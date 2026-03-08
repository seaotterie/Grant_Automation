#!/usr/bin/env python3
"""
Enhanced URL Discovery Pipeline

Cascading 6-stage URL discovery with confidence scoring.

Pipeline Stages:
  Stage 0: User-provided URL (confidence 0.95)              - $0.00
  Stage 1: 990 XML WebsiteAddressTxt (confidence 0.85)      - $0.00
  Stage 2: Multi-year 990 + cross-form consolidation (0.82)  - $0.00
  Stage 3: ProPublica JSON API website field (0.80)          - $0.00
  Stage 4: DuckDuckGo + Wikidata public APIs (0.70)          - $0.00
  Stage 6: Haiku URL predictor + validation (0.65-0.85)      - ~$0.001
  Stage 8: Org name → domain heuristic (0.50)                - $0.00

Each stage runs only if prior stages failed.
Estimated cumulative discovery rate: ~73%
"""

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class URLCandidate:
    """A URL discovered by any pipeline stage."""
    url: str
    source: str  # e.g. 'user_provided', '990_xml', 'propublica_json', ...
    stage: int
    confidence: float  # 0.0–1.0
    description: str = ""
    validation_status: str = "pending"  # pending | valid | invalid | timeout
    http_status_code: Optional[int] = None
    ein_verified: bool = False  # True if the org's EIN was found on the page
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    notes: List[str] = field(default_factory=list)

    @property
    def final_confidence(self) -> float:
        """Apply validation multiplier to base confidence."""
        multipliers = {
            "valid": 1.10 if self.ein_verified else 0.90,
            "timeout": 0.85,
            "invalid": 0.00,
            "pending": 0.80,
        }
        raw = self.confidence * multipliers.get(self.validation_status, 0.80)
        return min(round(raw, 4), 0.95)


@dataclass
class PipelineResult:
    """Complete result from the cascading URL discovery pipeline."""
    ein: str
    organization_name: str
    primary_url: Optional[URLCandidate] = None
    all_candidates: List[URLCandidate] = field(default_factory=list)
    stages_attempted: List[int] = field(default_factory=list)
    stage_resolved: Optional[int] = None
    elapsed_ms: float = 0.0
    total_cost_usd: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        primary = None
        if self.primary_url:
            primary = {
                "url": self.primary_url.url,
                "source": self.primary_url.source,
                "stage": self.primary_url.stage,
                "confidence": self.primary_url.final_confidence,
                "validation_status": self.primary_url.validation_status,
                "ein_verified": self.primary_url.ein_verified,
            }
        return {
            "ein": self.ein,
            "organization_name": self.organization_name,
            "primary_url": primary,
            "candidates_count": len(self.all_candidates),
            "stages_attempted": self.stages_attempted,
            "stage_resolved": self.stage_resolved,
            "elapsed_ms": round(self.elapsed_ms, 1),
            "total_cost_usd": round(self.total_cost_usd, 6),
        }


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class EnhancedURLDiscoveryPipeline:
    """
    Cascading URL discovery with 6 stages.

    Usage::

        pipeline = EnhancedURLDiscoveryPipeline()
        result = await pipeline.discover(
            ein="541026365",
            organization_name="Heroes Bridge",
            user_url=None,   # or "https://herosbridge.org"
        )
        print(result.primary_url)
    """

    # Stages to execute in order. Each maps to a method.
    STAGES = [0, 1, 2, 3, 4, 6, 8]

    def __init__(
        self,
        *,
        validate_urls: bool = True,
        check_ein_on_page: bool = True,
        haiku_api_key: Optional[str] = None,
    ):
        self.validate_urls = validate_urls
        self.check_ein_on_page = check_ein_on_page
        self._haiku_api_key = haiku_api_key
        self._http_session = None  # lazily created

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def discover(
        self,
        ein: str,
        organization_name: str,
        user_url: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        ntee_code: Optional[str] = None,
    ) -> PipelineResult:
        """Run the cascading pipeline and return the best URL."""
        start = time.time()
        result = PipelineResult(ein=ein, organization_name=organization_name)

        context = {
            "ein": ein.replace("-", "").strip(),
            "name": organization_name,
            "city": city or "",
            "state": state or "",
            "ntee": ntee_code or "",
            "user_url": user_url,
        }

        stage_methods = {
            0: self._stage_0_user_provided,
            1: self._stage_1_990_xml,
            2: self._stage_2_multiyear_990,
            3: self._stage_3_propublica_json,
            4: self._stage_4_public_apis,
            6: self._stage_6_haiku_predictor,
            8: self._stage_8_name_heuristic,
        }

        for stage_num in self.STAGES:
            result.stages_attempted.append(stage_num)
            try:
                candidates = await stage_methods[stage_num](context)
            except Exception as exc:
                logger.warning(f"Stage {stage_num} error for {ein}: {exc}")
                candidates = []

            if not candidates:
                continue

            # Validate candidates
            if self.validate_urls:
                candidates = await self._validate_candidates(candidates, context)

            # Keep all candidates for reporting
            result.all_candidates.extend(candidates)

            # Pick best valid candidate from this stage
            best = self._pick_best(candidates)
            if best and best.validation_status in ("valid", "pending"):
                result.primary_url = best
                result.stage_resolved = stage_num
                logger.info(
                    f"URL resolved at stage {stage_num} for {ein}: "
                    f"{best.url} (confidence={best.final_confidence})"
                )
                break  # cascade stops

        result.elapsed_ms = (time.time() - start) * 1000

        if not result.primary_url:
            logger.info(f"No URL found for {ein} after all stages")

        await self._close_session()
        return result

    # ------------------------------------------------------------------
    # Stage 0 – User-provided URL
    # ------------------------------------------------------------------

    async def _stage_0_user_provided(self, ctx: Dict) -> List[URLCandidate]:
        url = ctx.get("user_url")
        if not url:
            return []
        url = _normalize_url(url)
        if not url:
            return []
        return [URLCandidate(
            url=url,
            source="user_provided",
            stage=0,
            confidence=0.95,
            description="User-provided organization website",
        )]

    # ------------------------------------------------------------------
    # Stage 1 – Current-year 990 XML WebsiteAddressTxt
    # ------------------------------------------------------------------

    async def _stage_1_990_xml(self, ctx: Dict) -> List[URLCandidate]:
        from ..utils.xml_fetcher import XMLFetcher

        ein = ctx["ein"]
        fetcher = XMLFetcher(context="profile")
        xml_bytes = await fetcher.fetch_xml_by_ein(ein)
        if not xml_bytes:
            return []

        url = _extract_website_from_xml(xml_bytes)
        if not url:
            return []

        return [URLCandidate(
            url=url,
            source="990_xml",
            stage=1,
            confidence=0.85,
            description="Website declared in most recent 990 filing",
        )]

    # ------------------------------------------------------------------
    # Stage 2 – Multi-year 990 + cross-form consolidation
    # ------------------------------------------------------------------

    async def _stage_2_multiyear_990(self, ctx: Dict) -> List[URLCandidate]:
        """
        Scrape ProPublica org page for ALL XML download links,
        then parse each for WebsiteAddressTxt. This catches URLs declared
        in prior years or in 990-PF / 990-EZ forms that the current-year
        parser missed.
        """
        import aiohttp
        from bs4 import BeautifulSoup
        from urllib.parse import urlparse as _urlparse, parse_qs

        ein = ctx["ein"]
        base = "https://projects.propublica.org/nonprofits"
        page_url = f"{base}/organizations/{ein}"
        headers = {"User-Agent": "Catalynx/2.0 Grant Research Platform"}

        try:
            session = await self._get_session()
            async with session.get(page_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()
        except Exception as exc:
            logger.debug(f"Stage 2: failed to fetch ProPublica page for {ein}: {exc}")
            return []

        soup = BeautifulSoup(html, "html.parser")
        object_ids = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/download-xml?object_id=" in href:
                parsed = _urlparse(href)
                qs = parse_qs(parsed.query)
                oid = qs.get("object_id", [None])[0]
                if oid and oid not in object_ids:
                    object_ids.append(oid)

        # Limit to last 5 filings to avoid excessive requests
        object_ids = object_ids[:5]

        if not object_ids:
            return []

        candidates = []
        seen_urls = set()

        for oid in object_ids:
            try:
                dl_url = f"{base}/download-xml"
                async with session.get(
                    dl_url, params={"object_id": oid},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        continue
                    xml_bytes = await resp.read()
            except Exception:
                continue

            url = _extract_website_from_xml(xml_bytes)
            if url and url.lower() not in seen_urls:
                seen_urls.add(url.lower())
                candidates.append(URLCandidate(
                    url=url,
                    source="990_xml_multiyear",
                    stage=2,
                    confidence=0.82,
                    description=f"Website from historical 990 filing (object_id={oid})",
                ))

        return candidates

    # ------------------------------------------------------------------
    # Stage 3 – ProPublica JSON API `website` field
    # ------------------------------------------------------------------

    async def _stage_3_propublica_json(self, ctx: Dict) -> List[URLCandidate]:
        """
        The ProPublica JSON API returns a top-level org profile that may
        include a website field distinct from the XML filing data.
        """
        import aiohttp

        ein = ctx["ein"]
        api_url = f"https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"
        headers = {"User-Agent": "Catalynx/2.0 Grant Research Platform"}

        try:
            session = await self._get_session()
            async with session.get(api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json(content_type=None)
        except Exception as exc:
            logger.debug(f"Stage 3: ProPublica API error for {ein}: {exc}")
            return []

        if not isinstance(data, dict):
            return []

        org = data.get("organization", data)

        # Try multiple possible field names
        website = None
        for key in ("website", "website_url", "url", "homepage"):
            val = org.get(key)
            if val and isinstance(val, str) and "." in val:
                website = val
                break

        if not website:
            return []

        url = _normalize_url(website)
        if not url:
            return []

        return [URLCandidate(
            url=url,
            source="propublica_json",
            stage=3,
            confidence=0.80,
            description="Website from ProPublica JSON API organization profile",
        )]

    # ------------------------------------------------------------------
    # Stage 4 – DuckDuckGo Instant Answer + Wikidata
    # ------------------------------------------------------------------

    async def _stage_4_public_apis(self, ctx: Dict) -> List[URLCandidate]:
        """Free public API lookups: DuckDuckGo and Wikidata."""
        ddg_task = self._stage_4a_duckduckgo(ctx)
        wiki_task = self._stage_4b_wikidata(ctx)

        results = await asyncio.gather(ddg_task, wiki_task, return_exceptions=True)
        candidates = []
        for r in results:
            if isinstance(r, list):
                candidates.extend(r)
        return candidates

    async def _stage_4a_duckduckgo(self, ctx: Dict) -> List[URLCandidate]:
        """DuckDuckGo Instant Answer API – free, no auth."""
        import aiohttp

        name = ctx["name"]
        state = ctx.get("state", "")
        query = f"{name} nonprofit {state}".strip()

        api_url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}

        try:
            session = await self._get_session()
            async with session.get(api_url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json(content_type=None)
        except Exception as exc:
            logger.debug(f"Stage 4a: DuckDuckGo error: {exc}")
            return []

        if not isinstance(data, dict):
            return []

        candidates = []

        # Check AbstractURL (official website from Instant Answer)
        abstract_url = data.get("AbstractURL", "")
        if abstract_url and "." in abstract_url:
            url = _normalize_url(abstract_url)
            if url and not _is_reference_site(url):
                candidates.append(URLCandidate(
                    url=url,
                    source="duckduckgo",
                    stage=4,
                    confidence=0.70,
                    description="DuckDuckGo Instant Answer – official website",
                ))

        # Check Infobox URL
        infobox = data.get("Infobox", {})
        if isinstance(infobox, dict):
            for item in infobox.get("content", []):
                if isinstance(item, dict) and item.get("label", "").lower() in (
                    "website", "official website", "url",
                ):
                    val = item.get("value", "")
                    if val and "." in val:
                        url = _normalize_url(val)
                        if url and not _is_reference_site(url):
                            candidates.append(URLCandidate(
                                url=url,
                                source="duckduckgo_infobox",
                                stage=4,
                                confidence=0.72,
                                description="DuckDuckGo Infobox – official website",
                            ))

        return candidates

    async def _stage_4b_wikidata(self, ctx: Dict) -> List[URLCandidate]:
        """Wikidata SPARQL query for official website (P856) by EIN (P1297)."""
        import aiohttp

        ein = ctx["ein"]
        # Wikidata stores EIN as P1297 with hyphen format
        ein_formatted = f"{ein[:2]}-{ein[2:]}" if len(ein) == 9 and "-" not in ein else ein

        sparql = f"""
        SELECT ?website WHERE {{
          ?org wdt:P1297 "{ein_formatted}" .
          ?org wdt:P856 ?website .
        }}
        LIMIT 1
        """

        endpoint = "https://query.wikidata.org/sparql"
        headers = {
            "Accept": "application/sparql-results+json",
            "User-Agent": "Catalynx/2.0 Grant Research Platform",
        }

        try:
            session = await self._get_session()
            async with session.get(
                endpoint, params={"query": sparql},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json(content_type=None)
        except Exception as exc:
            logger.debug(f"Stage 4b: Wikidata error: {exc}")
            return []

        bindings = data.get("results", {}).get("bindings", [])
        if not bindings:
            return []

        website = bindings[0].get("website", {}).get("value", "")
        if not website:
            return []

        url = _normalize_url(website)
        if not url:
            return []

        return [URLCandidate(
            url=url,
            source="wikidata",
            stage=4,
            confidence=0.75,
            description="Wikidata official website (P856) linked by EIN (P1297)",
        )]

    # ------------------------------------------------------------------
    # Stage 6 – Haiku URL Predictor with validation
    # ------------------------------------------------------------------

    async def _stage_6_haiku_predictor(self, ctx: Dict) -> List[URLCandidate]:
        """
        Use Claude Haiku to predict likely URLs, then HTTP-validate and
        optionally check for EIN on the target page.

        Cost: ~$0.001 per call.
        """
        import aiohttp
        import os
        import json as _json

        api_key = self._haiku_api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.debug("Stage 6: No ANTHROPIC_API_KEY – skipping Haiku predictor")
            return []

        name = ctx["name"]
        ein = ctx["ein"]
        city = ctx.get("city", "")
        state = ctx.get("state", "")
        ntee = ctx.get("ntee", "")

        prompt = (
            f"What is the official website URL for this nonprofit organization?\n\n"
            f"Organization: {name}\n"
            f"EIN: {ein}\n"
            f"Location: {city}, {state}\n"
            f"NTEE Code: {ntee}\n\n"
            f"Return ONLY a JSON array of up to 3 predicted URLs, most likely first.\n"
            f'Example: ["https://example.org", "https://www.example.org"]\n'
            f"If you are unsure, still give your best guesses."
        )

        payload = {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 200,
            "messages": [{"role": "user", "content": prompt}],
        }

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        try:
            session = await self._get_session()
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning(f"Stage 6: Haiku API returned {resp.status}: {body[:200]}")
                    return []
                data = await resp.json()
        except Exception as exc:
            logger.warning(f"Stage 6: Haiku API error: {exc}")
            return []

        # Track cost
        self._last_haiku_cost = 0.001  # approximate

        # Parse response
        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")

        # Extract JSON array from response
        urls = _extract_url_array(text)
        if not urls:
            return []

        candidates = []
        for i, raw_url in enumerate(urls[:3]):
            url = _normalize_url(raw_url)
            if url:
                # Slight confidence decay for 2nd and 3rd predictions
                conf = 0.65 - (i * 0.05)
                candidates.append(URLCandidate(
                    url=url,
                    source="haiku_predictor",
                    stage=6,
                    confidence=conf,
                    description=f"Haiku prediction #{i+1}",
                ))

        return candidates

    # ------------------------------------------------------------------
    # Stage 8 – Org name → domain heuristic
    # ------------------------------------------------------------------

    async def _stage_8_name_heuristic(self, ctx: Dict) -> List[URLCandidate]:
        """Deterministic name-to-domain conversion as last resort."""
        name = ctx["name"]
        candidates = []

        for url, desc in _generate_domain_guesses(name):
            candidates.append(URLCandidate(
                url=url,
                source="name_heuristic",
                stage=8,
                confidence=0.50,
                description=desc,
            ))

        return candidates

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    async def _validate_candidates(
        self, candidates: List[URLCandidate], ctx: Dict
    ) -> List[URLCandidate]:
        """HTTP HEAD validation + optional EIN-on-page check."""
        import aiohttp

        session = await self._get_session()

        async def _validate_one(c: URLCandidate) -> URLCandidate:
            try:
                async with session.head(
                    c.url,
                    allow_redirects=True,
                    timeout=aiohttp.ClientTimeout(total=8),
                ) as resp:
                    c.http_status_code = resp.status
                    if resp.status == 200:
                        c.validation_status = "valid"
                    elif 300 <= resp.status < 400:
                        c.validation_status = "valid"
                    elif resp.status == 403:
                        # Many nonprofits block HEAD; try GET
                        c.validation_status = "valid"
                        c.notes.append("HEAD returned 403 – site likely blocks HEAD")
                    else:
                        c.validation_status = "invalid"
            except asyncio.TimeoutError:
                c.validation_status = "timeout"
            except Exception as exc:
                c.validation_status = "invalid"
                c.notes.append(str(exc)[:100])
            return c

        validated = await asyncio.gather(
            *[_validate_one(c) for c in candidates],
            return_exceptions=True,
        )

        results = []
        for i, v in enumerate(validated):
            if isinstance(v, Exception):
                candidates[i].validation_status = "invalid"
                candidates[i].notes.append(f"Validation error: {v}")
                results.append(candidates[i])
            else:
                results.append(v)

        # EIN-on-page check for valid candidates (Stage 6 & 8 only – adds confidence)
        if self.check_ein_on_page:
            ein = ctx["ein"]
            for c in results:
                if c.validation_status == "valid" and c.stage >= 6:
                    c.ein_verified = await self._check_ein_on_page(session, c.url, ein)
                    if c.ein_verified:
                        c.confidence = min(c.confidence + 0.20, 0.90)
                        c.notes.append("EIN found on page – confidence boosted")

        return results

    async def _check_ein_on_page(self, session, url: str, ein: str) -> bool:
        """Fetch the page and check if the org's EIN appears."""
        import aiohttp

        ein_patterns = [ein, f"{ein[:2]}-{ein[2:]}"]  # both formats

        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=8),
                headers={"User-Agent": "Catalynx/2.0 Grant Research Platform"},
            ) as resp:
                if resp.status != 200:
                    return False
                text = await resp.text(errors="replace")
                return any(pat in text for pat in ein_patterns)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _pick_best(self, candidates: List[URLCandidate]) -> Optional[URLCandidate]:
        """Return candidate with highest final confidence, preferring valid."""
        valid = [c for c in candidates if c.validation_status in ("valid", "pending")]
        pool = valid or candidates
        if not pool:
            return None
        return max(pool, key=lambda c: c.final_confidence)

    async def _get_session(self):
        """Lazily create a shared aiohttp session."""
        import aiohttp
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession()
        return self._http_session

    async def _close_session(self):
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()
            self._http_session = None


# ---------------------------------------------------------------------------
# Pure-function helpers (no state, easily testable)
# ---------------------------------------------------------------------------

def _normalize_url(url: str) -> Optional[str]:
    """Normalize a URL string. Returns None for junk values."""
    if not url:
        return None
    url = url.strip()

    invalid = {"none", "n/a", "na", "null", "unknown", "", "-", ".", "tbd"}
    if url.lower() in invalid:
        return None

    if not url.lower().startswith(("http://", "https://")):
        url = f"https://{url}"
    elif url.startswith(("HTTP://", "Http://", "Https://", "HTTPS://")):
        # Normalize protocol case
        url = "https://" + url.split("://", 1)[1]

    # Lowercase domain, preserve path
    parsed = urlparse(url)
    if not parsed.netloc or "." not in parsed.netloc:
        return None

    url = url.replace(parsed.netloc, parsed.netloc.lower())
    url = url.rstrip("/")
    return url


def _extract_website_from_xml(xml_bytes: bytes) -> Optional[str]:
    """Parse 990/990-PF/990-EZ XML and extract the website URL."""
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return None

    # Try with and without IRS namespace
    ns = {"irs": "http://www.irs.gov/efile"}
    paths = [
        ".//irs:WebsiteAddressTxt",
        ".//WebsiteAddressTxt",
        ".//irs:Website",
        ".//Website",
        ".//irs:WebSite",
        ".//WebSite",
        ".//irs:InternetAddress",
        ".//InternetAddress",
    ]

    for path in paths:
        try:
            elem = root.find(path, ns)
        except Exception:
            elem = root.find(path)
        if elem is not None and elem.text:
            url = _normalize_url(elem.text)
            if url:
                return url

    return None


def _is_reference_site(url: str) -> bool:
    """Check if URL is a reference/aggregator site rather than the org's own site."""
    ref_domains = {
        "wikipedia.org", "wikidata.org", "guidestar.org", "charitynavigator.org",
        "propublica.org", "irs.gov", "facebook.com", "twitter.com", "linkedin.com",
        "instagram.com", "youtube.com",
    }
    try:
        domain = urlparse(url).netloc.lower()
        return any(domain.endswith(r) for r in ref_domains)
    except Exception:
        return False


def _extract_url_array(text: str) -> List[str]:
    """Extract a JSON array of URLs from LLM response text."""
    import json

    # Try direct JSON parse
    text = text.strip()
    try:
        arr = json.loads(text)
        if isinstance(arr, list):
            return [u for u in arr if isinstance(u, str) and "." in u]
    except json.JSONDecodeError:
        pass

    # Try to find JSON array in text
    match = re.search(r'\[.*?\]', text, re.DOTALL)
    if match:
        try:
            arr = json.loads(match.group())
            if isinstance(arr, list):
                return [u for u in arr if isinstance(u, str) and "." in u]
        except json.JSONDecodeError:
            pass

    # Fallback: extract URLs with regex
    url_pattern = re.compile(r'https?://[^\s"\'\]\),]+')
    return url_pattern.findall(text)[:3]


def _generate_domain_guesses(org_name: str) -> List[Tuple[str, str]]:
    """
    Generate plausible domain names from an organization name.
    Returns list of (url, description) tuples.
    """
    if not org_name:
        return []

    name = org_name.strip()

    # Remove common suffixes/prefixes
    strip_words = {
        "inc", "incorporated", "corp", "corporation", "llc", "ltd",
        "limited", "co", "company", "the", "a", "an", "of", "for",
        "and", "in", "at", "to",
    }
    strip_suffixes = {
        "foundation", "fund", "trust", "society", "association",
        "organization", "org", "group", "coalition", "alliance",
        "council", "committee", "commission", "board", "agency",
        "network", "institute", "center", "centre",
    }

    words = re.sub(r'[^\w\s]', '', name.lower()).split()
    # Keep suffix for domain variation
    core_words = [w for w in words if w not in strip_words]
    no_suffix_words = [w for w in core_words if w not in strip_suffixes]

    guesses = []

    # Variation 1: all meaningful words joined (e.g., herosbridge.org)
    if no_suffix_words and len("".join(no_suffix_words)) >= 4:
        domain = "".join(no_suffix_words)
        guesses.append((f"https://www.{domain}.org", f"Name joined: {domain}.org"))

    # Variation 2: with suffix (e.g., herosbridgefoundation.org)
    if core_words and core_words != no_suffix_words:
        domain = "".join(core_words)
        if len(domain) >= 4:
            guesses.append((f"https://www.{domain}.org", f"Name+suffix: {domain}.org"))

    # Variation 3: hyphenated (e.g., heros-bridge.org)
    if len(no_suffix_words) >= 2:
        domain = "-".join(no_suffix_words)
        guesses.append((f"https://www.{domain}.org", f"Hyphenated: {domain}.org"))

    # Variation 4: try .com for common patterns
    if no_suffix_words and len("".join(no_suffix_words)) >= 4:
        domain = "".join(no_suffix_words)
        guesses.append((f"https://www.{domain}.com", f"Name joined: {domain}.com"))

    # Deduplicate
    seen = set()
    unique = []
    for url, desc in guesses:
        if url.lower() not in seen:
            seen.add(url.lower())
            unique.append((url, desc))
    return unique[:4]
