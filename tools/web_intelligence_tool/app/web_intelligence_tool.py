"""
Web Intelligence Tool - Main Entry Point

Tool 25 in the Catalynx 12-Factor Tool Architecture.

Uses an agentic Claude Haiku approach to gather nonprofit intelligence:
- Use Case 1: PROFILE_BUILDER - Auto-populate org profiles from websites
- Use Case 2: OPPORTUNITY_RESEARCH - Discover grants from grantmaking nonprofits
- Use Case 3: FOUNDATION_RESEARCH - Find grant opportunities and details

Replaces the previous Scrapy subprocess approach with semantic navigation:
  Step 1: Fetch homepage via httpx
  Step 2: Haiku identifies grant-relevant navigation links
  Step 3: Fetch up to 5 targeted pages
  Step 4: Haiku structures all content into GrantFunderIntelligence

Cost: ~3-6 Haiku calls per org ≈ $0.003-0.01
Scrapy spider files are kept in place but no longer called by this tool.

12-Factor Compliance:
- Factor 4: Structured outputs (GrantFunderIntelligence schema)
- Factor 6: Stateless execution
- Factor 10: Single responsibility (web intelligence gathering)
"""

import asyncio
import logging
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum
from urllib.parse import urljoin, urlparse
import toml

logger = logging.getLogger(__name__)

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.shared_schemas.grant_funder_intelligence import GrantFunderIntelligence, IntelligenceSource


# ============================================================================
# INPUT/OUTPUT MODELS
# ============================================================================

class UseCase(str, Enum):
    """Use case selector"""
    PROFILE_BUILDER = "PROFILE_BUILDER"
    OPPORTUNITY_RESEARCH = "OPPORTUNITY_RESEARCH"
    FOUNDATION_RESEARCH = "FOUNDATION_RESEARCH"


class WebIntelligenceRequest:
    """
    Input request for web intelligence gathering.

    Attributes:
        ein: Organization EIN
        organization_name: Organization name
        use_case: Which use case to execute
        user_provided_url: Optional user URL (highest priority)
        timeout: Optional timeout in seconds
        require_990_verification: (kept for API compat, not used in Haiku path)
        min_confidence_score: Minimum confidence to accept data
    """

    def __init__(
            self,
            ein: str,
            organization_name: str,
            use_case: UseCase = UseCase.PROFILE_BUILDER,
            user_provided_url: Optional[str] = None,
            timeout: Optional[int] = None,
            require_990_verification: bool = True,
            min_confidence_score: float = 0.7,
            # Legacy Scrapy params — ignored
            max_depth: Optional[int] = None,
            max_pages: Optional[int] = None,
    ):
        self.ein = ein
        self.organization_name = organization_name
        self.use_case = use_case
        self.user_provided_url = user_provided_url
        self.timeout = timeout
        self.require_990_verification = require_990_verification
        self.min_confidence_score = min_confidence_score


class WebIntelligenceResponse:
    """
    Output response with structured intelligence data.

    Attributes:
        success: Whether fetching was successful
        intelligence_data: GrantFunderIntelligence structured output
        execution_time_seconds: How long it took
        pages_scraped: Number of pages fetched
        data_quality_score: Overall data quality (0.0-1.0)
        verification_confidence: Confidence score
        errors: List of errors encountered
    """

    def __init__(
            self,
            success: bool,
            intelligence_data: Optional[GrantFunderIntelligence] = None,
            execution_time_seconds: float = 0.0,
            pages_scraped: int = 0,
            data_quality_score: float = 0.0,
            verification_confidence: float = 0.0,
            errors: Optional[list] = None
    ):
        self.success = success
        self.intelligence_data = intelligence_data
        self.execution_time_seconds = execution_time_seconds
        self.pages_scraped = pages_scraped
        self.data_quality_score = data_quality_score
        self.verification_confidence = verification_confidence
        self.errors = errors or []


# ============================================================================
# HTML UTILITY
# ============================================================================

def _strip_html(html_text: str) -> str:
    """Extract readable text from HTML, removing scripts, styles, and tags."""
    # Remove script and style blocks
    html_text = re.sub(r'<script[^>]*>.*?</script>', ' ', html_text, flags=re.DOTALL | re.IGNORECASE)
    html_text = re.sub(r'<style[^>]*>.*?</style>', ' ', html_text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    html_text = re.sub(r'<[^>]+>', ' ', html_text)
    # Decode common HTML entities
    html_text = html_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') \
                         .replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"')
    # Collapse whitespace
    html_text = re.sub(r'\s+', ' ', html_text).strip()
    return html_text


def _is_same_domain(base_url: str, link_url: str) -> bool:
    """Return True if link_url is on the same domain as base_url."""
    try:
        base_host = urlparse(base_url).netloc.lower().lstrip("www.")
        link_host = urlparse(link_url).netloc.lower().lstrip("www.")
        return not link_host or link_host == base_host
    except Exception:
        return True


# ============================================================================
# MAIN TOOL CLASS
# ============================================================================

class WebIntelligenceTool:
    """
    Main web intelligence tool class.

    Uses an agentic Claude Haiku pipeline (fetch → navigate → structure)
    instead of Scrapy spider subprocesses.
    """

    def __init__(self):
        """Initialize tool and load configuration."""
        self.config = self._load_config()
        self.tool_dir = Path(__file__).parent.parent
        logger.info("WebIntelligenceTool initialized (Haiku agent mode)")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from 12factors.toml."""
        config_path = Path(__file__).parent.parent / '12factors.toml'
        if not config_path.exists():
            return {}
        try:
            return toml.load(config_path)
        except Exception as e:
            logger.error(f"Error loading 12factors.toml: {e}")
            return {}

    async def execute(self, request: WebIntelligenceRequest) -> WebIntelligenceResponse:
        """
        Execute web intelligence gathering via agentic Haiku pipeline.

        All three use cases go through the same Haiku agent path;
        only the URL resolution differs.
        """
        start_time = time.time()

        logger.info(
            f"WebIntelligenceTool (Haiku) | org={request.organization_name} "
            f"| ein={request.ein} | use_case={request.use_case.value}"
        )

        try:
            url = await self._resolve_url(request)
            if not url:
                return WebIntelligenceResponse(
                    success=False,
                    errors=["no_url_found", f"Could not resolve URL for {request.organization_name}"]
                )

            intelligence = await self._fetch_with_haiku_agent(
                url=url,
                use_case=request.use_case,
                ein=request.ein,
                org_name=request.organization_name,
                timeout=request.timeout or 90,
            )

            execution_time = time.time() - start_time
            logger.info(
                f"WebIntelligenceTool complete | time={execution_time:.1f}s "
                f"| confidence={intelligence.confidence_score:.0%}"
            )

            return WebIntelligenceResponse(
                success=True,
                intelligence_data=intelligence,
                execution_time_seconds=execution_time,
                pages_scraped=intelligence._pages_fetched if hasattr(intelligence, '_pages_fetched') else 1,
                data_quality_score=intelligence.confidence_score,
                verification_confidence=intelligence.confidence_score,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Web intelligence failed: {e}"
            logger.error(error_msg, exc_info=True)
            return WebIntelligenceResponse(
                success=False,
                execution_time_seconds=execution_time,
                errors=[error_msg]
            )

    # ------------------------------------------------------------------
    # URL resolution
    # ------------------------------------------------------------------

    async def _resolve_url(self, request: WebIntelligenceRequest) -> Optional[str]:
        """Resolve the starting URL for the given request."""
        # Highest priority: user-provided
        if request.user_provided_url:
            return request.user_provided_url

        # For PROFILE_BUILDER: use SmartURLResolutionService (990 → GPT priority)
        if request.use_case == UseCase.PROFILE_BUILDER:
            try:
                from src.core.smart_url_resolution_service import SmartURLResolutionService
                service = SmartURLResolutionService()
                resolution = await service.resolve_organization_url(
                    ein=request.ein,
                    organization_name=request.organization_name,
                    user_provided_url=None,
                )
                if resolution and resolution.primary_url:
                    url = resolution.primary_url.url
                    logger.info(f"URL resolved: {url} (confidence {resolution.primary_url.confidence_score:.2f})")
                    return url
            except Exception as e:
                logger.warning(f"SmartURLResolutionService failed: {e}")

        # OPPORTUNITY_RESEARCH / FOUNDATION_RESEARCH: user_provided_url is expected
        logger.warning(f"No URL available for {request.organization_name} ({request.use_case.value})")
        return None

    # ------------------------------------------------------------------
    # Haiku agent pipeline
    # ------------------------------------------------------------------

    async def _fetch_with_haiku_agent(
        self,
        url: str,
        use_case: UseCase,
        ein: str,
        org_name: str,
        timeout: int = 90,
    ) -> GrantFunderIntelligence:
        """
        Four-step Haiku agent pipeline:
          1. Fetch homepage HTML via httpx
          2. Haiku identifies grant-relevant navigation links
          3. Fetch up to 5 targeted pages
          4. Haiku structures combined content into GrantFunderIntelligence
        """
        import httpx
        from src.core.anthropic_service import get_anthropic_service, PipelineStage

        service = get_anthropic_service()
        headers = {"User-Agent": "Catalynx Grant Research Bot (grant research platform)"}

        # Step 1: Fetch homepage
        homepage_text = ""
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                homepage_text = _strip_html(resp.text)
                logger.info(f"Fetched homepage: {url} ({len(homepage_text)} chars)")
        except Exception as e:
            logger.warning(f"Homepage fetch failed for {url}: {e}")
            if not homepage_text:
                # Return minimal result with just the URL
                return GrantFunderIntelligence(
                    ein=ein,
                    organization_name=org_name,
                    source=IntelligenceSource.WEB,
                    source_url=url,
                    confidence_score=0.1,
                )

        # Step 2: Haiku identifies grant-relevant links
        relevant_links = []
        if service.is_available:
            nav_system = (
                "You extract grant-relevant navigation links from nonprofit/foundation websites. "
                "Return ONLY a JSON object: {\"links\": [{\"url\": \"...\", \"label\": \"...\", "
                "\"relevance_reason\": \"...\"}]}. No markdown, no other text."
            )
            nav_user = (
                f"Homepage URL: {url}\n\n"
                f"Page text (first 6000 chars):\n{homepage_text[:6000]}\n\n"
                "Extract up to 8 navigation links most likely to contain: grants, funding, apply, "
                "programs, about us, board, leadership, contact, news, partners. "
                "Include absolute URLs or relative paths as they appear in the text."
            )
            try:
                links_result = await service.create_json_completion(
                    messages=[{"role": "user", "content": nav_user}],
                    system=nav_system,
                    stage=PipelineStage.FAST_SCREENING,
                    max_tokens=800,
                    temperature=0.0,
                )
                raw_links = links_result.get("links", [])
                relevant_links = [lnk for lnk in raw_links if lnk.get("url")][:5]
                logger.info(f"Haiku identified {len(relevant_links)} relevant links")
            except Exception as e:
                logger.warning(f"Link identification failed: {e}")

        # Step 3: Fetch targeted pages
        page_texts = [("Homepage", homepage_text[:12000])]
        pages_fetched = 1

        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            for link in relevant_links:
                raw_href = link.get("url", "").strip()
                if not raw_href:
                    continue

                # Resolve relative URLs
                if raw_href.startswith("//"):
                    link_url = "https:" + raw_href
                elif raw_href.startswith("/"):
                    link_url = urljoin(url, raw_href)
                elif raw_href.startswith("http"):
                    link_url = raw_href
                else:
                    link_url = urljoin(url, raw_href)

                # Stay on same domain
                if not _is_same_domain(url, link_url):
                    continue

                try:
                    await asyncio.sleep(1.5)  # Respectful crawl delay
                    page_resp = await client.get(link_url, headers=headers)
                    page_resp.raise_for_status()
                    page_text = _strip_html(page_resp.text)[:10000]
                    page_texts.append((link.get("label", "Page"), page_text))
                    pages_fetched += 1
                    logger.info(f"Fetched: {link_url} ({len(page_text)} chars)")
                except Exception as e:
                    logger.debug(f"Skipped {link_url}: {e}")

        # Step 4: Haiku structures all content into GrantFunderIntelligence
        combined_text = "\n\n--- PAGE BREAK ---\n\n".join(
            [f"[{label}]\n{text}" for label, text in page_texts]
        )

        structure_system = (
            "You are extracting grant-intelligence from nonprofit/foundation website pages. "
            "Return ONLY a JSON object with exactly these fields — no markdown, no other text:\n"
            "{\n"
            '  "accepts_applications": "yes" or "no" or "invitation_only" or "unknown",\n'
            '  "application_deadlines": "deadline info or null",\n'
            '  "application_process": "how to apply or null",\n'
            '  "required_documents": ["doc1", "doc2"],\n'
            '  "funding_priorities": ["priority1", "priority2"],\n'
            '  "geographic_limitations": "limitations or null",\n'
            '  "grant_size_range": "range like \'$5,000-$50,000\' or null",\n'
            '  "population_focus": "who they serve/fund or null",\n'
            '  "mission_statement": "mission or null",\n'
            '  "program_descriptions": ["program 1 description", "program 2"],\n'
            '  "contact_information": "contact info or null",\n'
            '  "board_members": ["Full Name", "Full Name"],\n'
            '  "past_grantees": ["Org name", "Org name"],\n'
            '  "confidence_score": 0.0\n'
            "}\n"
            "Only include what you actually see in the text. "
            "Set confidence_score based on how much grant-relevant data you found (0.0-1.0)."
        )
        structure_user = (
            f"Organization: {org_name} (EIN: {ein})\n"
            f"Website: {url}\n\n"
            f"Scraped pages:\n{combined_text[:18000]}\n\n"
            "Extract grant-relevant intelligence."
        )

        if service.is_available:
            try:
                intel = await service.create_json_completion(
                    messages=[{"role": "user", "content": structure_user}],
                    system=structure_system,
                    stage=PipelineStage.FAST_SCREENING,
                    max_tokens=2048,
                    temperature=0.0,
                )

                result = GrantFunderIntelligence(
                    ein=ein,
                    organization_name=org_name,
                    source=IntelligenceSource.WEB,
                    accepts_applications=intel.get("accepts_applications", "unknown"),
                    application_deadlines=intel.get("application_deadlines"),
                    application_process=intel.get("application_process"),
                    required_documents=intel.get("required_documents") or [],
                    funding_priorities=intel.get("funding_priorities") or [],
                    geographic_limitations=intel.get("geographic_limitations"),
                    grant_size_range=intel.get("grant_size_range"),
                    population_focus=intel.get("population_focus"),
                    mission_statement=intel.get("mission_statement"),
                    program_descriptions=intel.get("program_descriptions") or [],
                    contact_information=intel.get("contact_information"),
                    board_members=intel.get("board_members") or [],
                    past_grantees=intel.get("past_grantees") or [],
                    confidence_score=float(intel.get("confidence_score", 0.7)),
                    source_url=url,
                )
                logger.info(
                    f"Intelligence structured | confidence={result.confidence_score:.0%} "
                    f"| pages={pages_fetched}"
                )
                return result

            except Exception as e:
                logger.error(f"Intelligence structuring failed: {e}")

        # Fallback: return minimal result with what we know from homepage text
        return GrantFunderIntelligence(
            ein=ein,
            organization_name=org_name,
            source=IntelligenceSource.WEB,
            source_url=url,
            confidence_score=0.3,
            mission_statement=homepage_text[:300] if homepage_text else None,
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def scrape_organization_profile(
        ein: str,
        organization_name: str,
        user_provided_url: Optional[str] = None,
        timeout: Optional[int] = None,
        # Legacy params ignored
        max_pages: Optional[int] = None,
        max_depth: Optional[int] = None,
) -> WebIntelligenceResponse:
    """
    Convenience function to gather organization intelligence via Haiku agent.
    """
    tool = WebIntelligenceTool()
    request = WebIntelligenceRequest(
        ein=ein,
        organization_name=organization_name,
        use_case=UseCase.PROFILE_BUILDER,
        user_provided_url=user_provided_url,
        timeout=timeout,
    )
    return await tool.execute(request)


# ============================================================================
# COMMAND-LINE INTERFACE (for testing)
# ============================================================================

async def main():
    """Command-line interface for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Web Intelligence Tool (Haiku Agent) - Test CLI")
    parser.add_argument('--ein', required=True, help='Organization EIN')
    parser.add_argument('--name', required=True, help='Organization name')
    parser.add_argument('--url', help='Organization website URL (optional)')
    parser.add_argument('--use-case', default='PROFILE_BUILDER',
                        choices=['PROFILE_BUILDER', 'OPPORTUNITY_RESEARCH', 'FOUNDATION_RESEARCH'],
                        help='Use case to execute')

    args = parser.parse_args()

    request = WebIntelligenceRequest(
        ein=args.ein,
        organization_name=args.name,
        use_case=UseCase(args.use_case),
        user_provided_url=args.url,
    )

    tool = WebIntelligenceTool()
    response = await tool.execute(request)

    print(f"\n{'='*60}")
    print("Web Intelligence Results (Haiku Agent)")
    print(f"{'='*60}")
    print(f"Success: {response.success}")
    print(f"Execution Time: {response.execution_time_seconds:.2f}s")
    print(f"Data Quality: {response.data_quality_score:.2%}")

    if response.errors:
        print(f"\nErrors:")
        for error in response.errors:
            print(f"  - {error}")

    if response.intelligence_data:
        intel = response.intelligence_data
        print(f"\nIntelligence Data:")
        print(f"  Mission: {intel.mission_statement[:100] if intel.mission_statement else 'N/A'}")
        print(f"  Accepts Apps: {intel.accepts_applications}")
        print(f"  Priorities: {intel.funding_priorities[:3]}")
        print(f"  Board Members: {len(intel.board_members)}")


if __name__ == '__main__':
    asyncio.run(main())
