"""
Smart URL Middleware for Scrapy

Integrates SmartURLResolutionService with Scrapy to:
1. Resolve best URL before scraping (user → 990 → GPT priority)
2. Add URL source attribution to requests
3. Set confidence metadata for downstream validation
4. Skip scraping if no valid URL found

This middleware runs BEFORE the spider starts, ensuring we scrape
the most authoritative URL available.
"""

import logging
import asyncio
from typing import Optional
from scrapy import signals
from scrapy.http import Request

# Import Catalynx services
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.smart_url_resolution_service import SmartURLResolutionService, URLResolutionResult

logger = logging.getLogger(__name__)


class SmartURLMiddleware:
    """
    Scrapy middleware that resolves the best URL to scrape using
    SmartURLResolutionService before the spider starts crawling.

    Lifecycle:
    1. Spider opens → check if EIN + org name available
    2. Call SmartURLResolutionService.resolve_organization_url()
    3. Update spider.start_urls with resolved URL
    4. Add metadata to all requests (url_source, url_confidence)
    """

    def __init__(self):
        self.url_service = SmartURLResolutionService()
        self._resolution_cache = {}  # Cache per-spider

    @classmethod
    def from_crawler(cls, crawler):
        """Factory method to create middleware from crawler"""
        middleware = cls()

        # Connect to spider signals
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)

        return middleware

    def spider_opened(self, spider):
        """
        Called when spider opens. Resolve URL before crawling starts.

        Spider must have these attributes:
        - ein: Organization EIN (required)
        - organization_name: Organization name (required)
        - user_provided_url: Optional user URL (optional)
        """
        logger.info(f"SmartURLMiddleware: Spider opened - {spider.name}")

        # NEW: Skip if spider already has start_urls (URL was pre-resolved)
        if hasattr(spider, 'start_urls') and spider.start_urls:
            logger.info(
                f"SmartURLMiddleware: Spider already has start_urls ({spider.start_urls[0]}). "
                "Skipping URL resolution."
            )
            return

        # Check if spider has required attributes
        if not hasattr(spider, 'ein') or not hasattr(spider, 'organization_name'):
            logger.warning(
                f"Spider {spider.name} missing 'ein' or 'organization_name' attributes. "
                "Smart URL resolution skipped."
            )
            return

        # Resolve URL synchronously (Scrapy spider_opened is not async)
        # Create event loop if none exists
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run URL resolution
        resolution_result = loop.run_until_complete(
            self._resolve_url_for_spider(spider)
        )

        if resolution_result and resolution_result.primary_url:
            # Update spider's start URLs
            resolved_url = resolution_result.primary_url.url
            spider.start_urls = [resolved_url]

            # Store resolution result on spider for access in spider methods
            spider.url_resolution = resolution_result

            # Cache for middleware
            self._resolution_cache[spider.name] = resolution_result

            logger.info(
                f"SmartURLMiddleware: Resolved URL for {spider.organization_name} ({spider.ein})\n"
                f"  URL: {resolved_url}\n"
                f"  Source: {resolution_result.primary_url.source}\n"
                f"  Confidence: {resolution_result.primary_url.confidence_score:.2f}\n"
                f"  Strategy: {resolution_result.resolution_strategy}"
            )
        else:
            logger.error(
                f"SmartURLMiddleware: Failed to resolve URL for {spider.organization_name} ({spider.ein}). "
                "Spider may not have valid start URLs."
            )

    async def _resolve_url_for_spider(self, spider) -> Optional[URLResolutionResult]:
        """
        Resolve organization URL using SmartURLResolutionService

        Args:
            spider: Scrapy spider with ein, organization_name, and optionally user_provided_url

        Returns:
            URLResolutionResult or None if resolution failed
        """
        try:
            ein = spider.ein
            org_name = spider.organization_name
            user_url = getattr(spider, 'user_provided_url', None)

            logger.info(
                f"Resolving URL for {org_name} (EIN: {ein})\n"
                f"  User-provided URL: {user_url if user_url else 'None'}"
            )

            # Call URL resolution service
            resolution = await self.url_service.resolve_organization_url(
                ein=ein,
                organization_name=org_name,
                user_provided_url=user_url
            )

            return resolution

        except Exception as e:
            logger.error(f"Error resolving URL for {spider.organization_name}: {e}", exc_info=True)
            return None

    def process_request(self, request: Request, spider):
        """
        Process each request to add URL metadata.

        This adds metadata from URL resolution to each request:
        - url_source: Where the URL came from (user_provided, 990_declared, gpt_predicted)
        - url_confidence: Confidence score (0.0-1.0)
        - url_resolution_strategy: Human-readable resolution strategy
        """
        # Get cached resolution for this spider
        resolution = self._resolution_cache.get(spider.name)

        if resolution and resolution.primary_url:
            # Add metadata to request
            request.meta['url_source'] = resolution.primary_url.source
            request.meta['url_confidence'] = resolution.primary_url.confidence_score
            request.meta['url_resolution_strategy'] = resolution.resolution_strategy

            # Add confidence assessment
            request.meta['url_overall_confidence'] = resolution.confidence_assessment.get('overall_confidence', 0.0)
            request.meta['url_data_quality'] = resolution.confidence_assessment.get('data_quality', 'unknown')

        return None  # Continue processing request
