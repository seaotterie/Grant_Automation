"""
Web Intelligence Tool - Main Entry Point

Tool 25 in the Catalynx 12-Factor Tool Architecture.

This is a Scrapy-powered web scraping tool for gathering nonprofit intelligence:
- Use Case 1: Profile Builder - Auto-populate org profiles from websites
- Use Case 2: Competitor Research - Analyze peer nonprofit websites
- Use Case 3: Foundation Research - Find grant opportunities and details

12-Factor Compliance:
- Factor 1: Codebase tracked in git
- Factor 3: Config from 12factors.toml
- Factor 4: Structured outputs (BAML schemas)
- Factor 6: Stateless execution
- Factor 10: Single responsibility (web intelligence gathering)
"""

import logging
import asyncio
import time
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum
import toml

# Scrapy imports
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import spider
from app.scrapy_spiders.organization_profile_spider import OrganizationProfileSpider

# Import structured output models
from app.scrapy_pipelines.structured_output_pipeline import OrganizationIntelligence

logger = logging.getLogger(__name__)


# ============================================================================
# INPUT/OUTPUT MODELS
# ============================================================================

class UseCase(str, Enum):
    """Use case selector"""
    PROFILE_BUILDER = "PROFILE_BUILDER"
    COMPETITOR_RESEARCH = "COMPETITOR_RESEARCH"
    FOUNDATION_RESEARCH = "FOUNDATION_RESEARCH"


class WebIntelligenceRequest:
    """
    Input request for web intelligence gathering.

    Attributes:
        ein: Organization EIN
        organization_name: Organization name
        use_case: Which use case to execute
        user_provided_url: Optional user URL (highest priority)
        max_depth: Override default crawl depth
        max_pages: Override default max pages
        require_990_verification: Require 990 tax filing verification
        min_confidence_score: Minimum confidence to accept data
    """

    def __init__(
            self,
            ein: str,
            organization_name: str,
            use_case: UseCase = UseCase.PROFILE_BUILDER,
            user_provided_url: Optional[str] = None,
            max_depth: Optional[int] = None,
            max_pages: Optional[int] = None,
            require_990_verification: bool = True,
            min_confidence_score: float = 0.7
    ):
        self.ein = ein
        self.organization_name = organization_name
        self.use_case = use_case
        self.user_provided_url = user_provided_url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.require_990_verification = require_990_verification
        self.min_confidence_score = min_confidence_score


class WebIntelligenceResponse:
    """
    Output response with structured intelligence data.

    Attributes:
        success: Whether scraping was successful
        intelligence_data: Structured intelligence (OrganizationIntelligence, etc.)
        execution_time_seconds: How long scraping took
        pages_scraped: Number of pages successfully scraped
        data_quality_score: Overall data quality (0.0-1.0)
        verification_confidence: 990 verification confidence (0.0-1.0)
        errors: List of errors encountered
    """

    def __init__(
            self,
            success: bool,
            intelligence_data: Optional[OrganizationIntelligence] = None,
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
# MAIN TOOL CLASS
# ============================================================================

class WebIntelligenceTool:
    """
    Main web intelligence tool class.

    Executes Scrapy spiders based on use case and returns structured intelligence.
    """

    def __init__(self):
        """Initialize tool and load configuration."""
        self.config = self._load_config()
        self.tool_dir = Path(__file__).parent.parent
        logger.info("WebIntelligenceTool initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from 12factors.toml."""
        config_path = Path(__file__).parent.parent / '12factors.toml'

        if not config_path.exists():
            logger.warning(f"12factors.toml not found at {config_path}. Using defaults.")
            return {}

        try:
            config = toml.load(config_path)
            logger.info("Loaded configuration from 12factors.toml")
            return config
        except Exception as e:
            logger.error(f"Error loading 12factors.toml: {e}")
            return {}

    async def execute(self, request: WebIntelligenceRequest) -> WebIntelligenceResponse:
        """
        Execute web intelligence gathering.

        Args:
            request: WebIntelligenceRequest with scraping parameters

        Returns:
            WebIntelligenceResponse with structured intelligence
        """
        start_time = time.time()

        logger.info(
            f"Executing Web Intelligence Tool:\n"
            f"  Organization: {request.organization_name}\n"
            f"  EIN: {request.ein}\n"
            f"  Use Case: {request.use_case.value}\n"
            f"  User URL: {request.user_provided_url or 'None (will auto-resolve)'}"
        )

        try:
            # Execute appropriate spider based on use case
            if request.use_case == UseCase.PROFILE_BUILDER:
                intelligence_data = await self._execute_profile_builder_spider(request)
            elif request.use_case == UseCase.COMPETITOR_RESEARCH:
                intelligence_data = await self._execute_competitor_spider(request)
            elif request.use_case == UseCase.FOUNDATION_RESEARCH:
                intelligence_data = await self._execute_foundation_spider(request)
            else:
                raise ValueError(f"Unknown use case: {request.use_case}")

            execution_time = time.time() - start_time

            # Extract metrics from intelligence data
            if intelligence_data:
                metadata = intelligence_data.scraping_metadata
                pages_scraped = metadata.pages_scraped
                data_quality_score = metadata.data_quality_score
                verification_confidence = metadata.verification_confidence
            else:
                pages_scraped = 0
                data_quality_score = 0.0
                verification_confidence = 0.0

            logger.info(
                f"Web intelligence complete:\n"
                f"  Execution time: {execution_time:.2f}s\n"
                f"  Pages scraped: {pages_scraped}\n"
                f"  Data quality: {data_quality_score:.2%}\n"
                f"  Verification confidence: {verification_confidence:.2%}"
            )

            return WebIntelligenceResponse(
                success=True,
                intelligence_data=intelligence_data,
                execution_time_seconds=execution_time,
                pages_scraped=pages_scraped,
                data_quality_score=data_quality_score,
                verification_confidence=verification_confidence
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Web intelligence failed: {str(e)}"
            logger.error(error_msg, exc_info=True)

            return WebIntelligenceResponse(
                success=False,
                execution_time_seconds=execution_time,
                errors=[error_msg]
            )

    async def _execute_profile_builder_spider(
            self,
            request: WebIntelligenceRequest
    ) -> Optional[OrganizationIntelligence]:
        """
        Execute Organization Profile Spider (Use Case 1).

        Args:
            request: WebIntelligenceRequest

        Returns:
            OrganizationIntelligence or None if failed
        """
        logger.info(f"Executing Profile Builder spider for {request.organization_name}")

        # Configure Scrapy settings
        settings = get_project_settings()

        # Override settings from request
        if request.max_depth:
            settings['DEPTH_LIMIT'] = request.max_depth

        # Create spider instance
        spider = OrganizationProfileSpider(
            ein=request.ein,
            organization_name=request.organization_name,
            user_provided_url=request.user_provided_url
        )

        # Run spider and collect results
        result = await self._run_spider(spider, settings)

        return result

    async def _execute_competitor_spider(
            self,
            request: WebIntelligenceRequest
    ) -> Optional[Any]:
        """
        Execute Competitor Research Spider (Use Case 2).

        TODO: Implement when spider is ready.
        """
        raise NotImplementedError("Competitor Research spider not yet implemented")

    async def _execute_foundation_spider(
            self,
            request: WebIntelligenceRequest
    ) -> Optional[Any]:
        """
        Execute Foundation Research Spider (Use Case 3).

        TODO: Implement when spider is ready.
        """
        raise NotImplementedError("Foundation Research spider not yet implemented")

    async def _run_spider(self, spider, settings) -> Optional[Any]:
        """
        Run a Scrapy spider and return the result.

        Args:
            spider: Spider instance
            settings: Scrapy settings

        Returns:
            Structured intelligence data or None
        """
        # This is a simplified synchronous approach
        # For production, you might want to use scrapyd or scrapy-playwright for async

        from scrapy.crawler import CrawlerRunner
        from twisted.internet import defer

        runner = CrawlerRunner(settings)

        @defer.inlineCallbacks
        def crawl():
            yield runner.crawl(spider)

        # Run the spider
        crawl()

        # Wait for completion (simplified)
        # In production, you'd want proper async handling

        # For now, return a placeholder
        # The actual implementation would need to properly integrate Scrapy's async
        logger.warning("Spider execution is a placeholder. Full integration pending.")

        return None


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def scrape_organization_profile(
        ein: str,
        organization_name: str,
        user_provided_url: Optional[str] = None
) -> WebIntelligenceResponse:
    """
    Convenience function to scrape organization profile.

    Args:
        ein: Organization EIN
        organization_name: Organization name
        user_provided_url: Optional user URL

    Returns:
        WebIntelligenceResponse with OrganizationIntelligence
    """
    tool = WebIntelligenceTool()

    request = WebIntelligenceRequest(
        ein=ein,
        organization_name=organization_name,
        use_case=UseCase.PROFILE_BUILDER,
        user_provided_url=user_provided_url
    )

    return await tool.execute(request)


# ============================================================================
# COMMAND-LINE INTERFACE (for testing)
# ============================================================================

async def main():
    """Command-line interface for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Web Intelligence Tool - Test CLI")
    parser.add_argument('--ein', required=True, help='Organization EIN')
    parser.add_argument('--name', required=True, help='Organization name')
    parser.add_argument('--url', help='Organization website URL (optional)')
    parser.add_argument('--use-case', default='PROFILE_BUILDER',
                        choices=['PROFILE_BUILDER', 'COMPETITOR_RESEARCH', 'FOUNDATION_RESEARCH'],
                        help='Use case to execute')

    args = parser.parse_args()

    # Create request
    request = WebIntelligenceRequest(
        ein=args.ein,
        organization_name=args.name,
        use_case=UseCase(args.use_case),
        user_provided_url=args.url
    )

    # Execute tool
    tool = WebIntelligenceTool()
    response = await tool.execute(request)

    # Print results
    print(f"\n{'='*60}")
    print(f"Web Intelligence Results")
    print(f"{'='*60}")
    print(f"Success: {response.success}")
    print(f"Execution Time: {response.execution_time_seconds:.2f}s")
    print(f"Pages Scraped: {response.pages_scraped}")
    print(f"Data Quality: {response.data_quality_score:.2%}")
    print(f"Verification Confidence: {response.verification_confidence:.2%}")

    if response.errors:
        print(f"\nErrors:")
        for error in response.errors:
            print(f"  - {error}")

    if response.intelligence_data:
        print(f"\nIntelligence Data:")
        print(f"  Mission: {response.intelligence_data.mission_statement[:100] if response.intelligence_data.mission_statement else 'N/A'}...")
        print(f"  Programs: {len(response.intelligence_data.programs)}")
        print(f"  Leadership: {len(response.intelligence_data.leadership)}")


if __name__ == '__main__':
    asyncio.run(main())
