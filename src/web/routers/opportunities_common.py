"""
Shared helpers for opportunities sub-routers.

Extracted from opportunities.py during the Phase C router refactor so that
per-domain sub-routers (research, promotion, 990, screening) can share
request models, SSRF validation, and the Claude website-interpretation
helper without importing from the top-level opportunities module.
"""

from __future__ import annotations

import ipaddress
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiohttp
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


# Cache TTL constants (in days)
WEB_DATA_TTL_DAYS = 30
FILING_HISTORY_TTL_DAYS = 7


# Claude web interpretation system prompt
INTERPRET_SYSTEM_PROMPT = """You are extracting structured data from scraped nonprofit website pages.
Return JSON with this exact structure:
{
  "mission": string or null,
  "leadership": [{"name": string, "title": string, "email": string or null, "confidence": "high" or "medium" or "low"}, ...],
  "programs": [{"name": string, "description": string}, ...],
  "contact": {"email": string or null, "phone": string or null, "address": string or null},
  "key_facts": [string, ...],
  "interpretation_notes": string
}
Only include data you actually see in the text. Use confidence="low" for anything uncertain.
Return ONLY the JSON object, no markdown or other text."""


# ---------------------------------------------------------------------------
# SSRF protection helpers
# ---------------------------------------------------------------------------

# Domains that legitimately host IRS 990 PDF filings
ALLOWED_PDF_DOMAINS = {
    "s3.amazonaws.com",       # AWS S3 (IRS bulk data)
    "s3.us-east-1.amazonaws.com",
    "apps.irs.gov",
    "www.irs.gov",
    "irs.gov",
    "projects.propublica.org",
    "www.propublica.org",
    "propublica.org",
    "990s.foundationcenter.org",
    "candid.org",
    "www.candid.org",
    "efts.irs.gov",
}

PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # link-local
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def validate_pdf_url(url: str) -> str:
    """Raise ValueError if *url* is not a safe, allowed 990 PDF URL."""
    if not url or not isinstance(url, str):
        raise ValueError("pdf_url is required")

    url = url.strip()
    if len(url) > 2048:
        raise ValueError("pdf_url exceeds maximum length")

    try:
        parsed = urlparse(url)
    except Exception:
        raise ValueError("pdf_url is not a valid URL")

    if parsed.scheme not in ("http", "https"):
        raise ValueError("pdf_url must use http or https")

    hostname = parsed.hostname or ""
    if not hostname:
        raise ValueError("pdf_url has no hostname")

    # Block bare IP addresses (SSRF via IP literal)
    try:
        ip = ipaddress.ip_address(hostname)
        for net in PRIVATE_RANGES:
            if ip in net:
                raise ValueError("pdf_url hostname resolves to a private/reserved address")
        # Public IPs are technically OK but not expected — reject them anyway
        raise ValueError("pdf_url must use a named host from an allowed domain")
    except ValueError as exc:
        # Re-raise our own errors; ignore "does not appear to be an IPv4 or IPv6 address"
        if "pdf_url" in str(exc):
            raise

    # Allowlist check — hostname must match or be a subdomain of an allowed domain
    def _matches(host: str) -> bool:
        for allowed in ALLOWED_PDF_DOMAINS:
            if host == allowed or host.endswith("." + allowed):
                return True
        return False

    if not _matches(hostname):
        raise ValueError(
            f"pdf_url hostname '{hostname}' is not in the allowed domain list"
        )

    return url


# ---------------------------------------------------------------------------
# Shared pydantic request models
# ---------------------------------------------------------------------------


class WebResearchRequest(BaseModel):
    """Request body for web research endpoint."""
    website_url: Optional[str] = None


class Analyze990PDFRequest(BaseModel):
    """Request body for 990 PDF analysis endpoint."""
    pdf_url: str
    tax_year: Optional[int] = None

    @field_validator("pdf_url")
    @classmethod
    def _validate(cls, v: str) -> str:
        return validate_pdf_url(v)


class BatchAnalyze990PDFsRequest(BaseModel):
    """Request body for batch 990 PDF analysis endpoint."""
    opportunity_ids: List[str]
    force_refresh: bool = False


class BatchWebResearchRequest(BaseModel):
    """Request body for batch web research endpoint."""
    opportunity_ids: List[str]
    profile_id: Optional[str] = None
    force_refresh: bool = False


class WebsiteUrlUpdate(BaseModel):
    """Request body for PATCH website-url endpoint."""
    url: Optional[str] = None


# ---------------------------------------------------------------------------
# Claude-backed website interpretation
# ---------------------------------------------------------------------------


async def interpret_with_claude(
    scraped_urls: List[str],
    org_name: str,
    ein: str,
) -> Optional[Dict[str, Any]]:
    """
    Fetch raw page text from scraped URLs and use Claude Sonnet for intelligent extraction.
    Returns parsed dict matching INTERPRET_SYSTEM_PROMPT schema, or None on failure.
    """
    from bs4 import BeautifulSoup
    from src.core.anthropic_service import get_anthropic_service, PipelineStage

    page_texts = []
    headers = {"User-Agent": "CatalynxResearch/1.0"}

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as client:
        for url in scraped_urls[:5]:
            try:
                async with client.get(url, headers=headers, allow_redirects=True) as resp:
                    if resp.status == 200:
                        html = await resp.text(errors="replace")
                        text = BeautifulSoup(html, "html.parser").get_text(
                            separator="\n", strip=True
                        )
                        page_texts.append(f"--- PAGE: {url} ---\n{text[:3000]}")
            except Exception:
                pass

    if not page_texts:
        return None

    combined = "\n\n".join(page_texts)
    try:
        svc = get_anthropic_service()
        result = await svc.create_json_completion(
            system=INTERPRET_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Organization: {org_name} (EIN: {ein})\n\n{combined}"
            }],
            stage=PipelineStage.THOROUGH_SCREENING,
            max_tokens=2048,
            temperature=0.0,
        )
        return result
    except Exception as e:
        logger.warning(f"Claude web interpretation failed for EIN {ein}: {e}")
        return None


__all__ = [
    "WEB_DATA_TTL_DAYS",
    "FILING_HISTORY_TTL_DAYS",
    "INTERPRET_SYSTEM_PROMPT",
    "ALLOWED_PDF_DOMAINS",
    "PRIVATE_RANGES",
    "validate_pdf_url",
    "WebResearchRequest",
    "Analyze990PDFRequest",
    "BatchAnalyze990PDFsRequest",
    "BatchWebResearchRequest",
    "WebsiteUrlUpdate",
    "interpret_with_claude",
]
