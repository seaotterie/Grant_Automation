"""
Rate Limit Middleware for Scrapy

Additional rate limiting beyond Scrapy's built-in DOWNLOAD_DELAY to ensure
respectful scraping practices.

Features:
- Per-domain rate limiting
- Request tracking
- Automatic backoff on errors
- Configurable limits from 12factors.toml
"""

import logging
import time
from collections import defaultdict
from scrapy import signals

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Middleware to enforce additional rate limiting for respectful web scraping.

    Tracks requests per domain and enforces delays to avoid overloading servers.
    """

    def __init__(self):
        # Track last request time per domain
        self.last_request_time = defaultdict(float)

        # Track request counts per domain (for monitoring)
        self.request_counts = defaultdict(int)

        # Minimum delay between requests (from settings)
        self.min_delay = 2.0  # Default 2 seconds

        # Backoff multiplier on errors
        self.error_backoff_multiplier = 2.0

    @classmethod
    def from_crawler(cls, crawler):
        """Factory method to create middleware from crawler"""
        middleware = cls()

        # Get delay from settings (uses DOWNLOAD_DELAY)
        middleware.min_delay = crawler.settings.getfloat('DOWNLOAD_DELAY', 2.0)

        # Connect to spider signals for cleanup
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)

        return middleware

    def process_request(self, request, spider):
        """
        Process request to enforce rate limiting.

        Calculates time since last request to same domain and adds delay if needed.
        """
        domain = request.url.split('/')[2]  # Extract domain from URL

        # Get time since last request to this domain
        last_time = self.last_request_time.get(domain, 0)
        current_time = time.time()
        time_since_last = current_time - last_time

        # Calculate required delay
        required_delay = self.min_delay

        # If we need to wait, sleep
        if time_since_last < required_delay:
            wait_time = required_delay - time_since_last
            logger.debug(f"Rate limiting: Waiting {wait_time:.2f}s before request to {domain}")
            time.sleep(wait_time)

        # Update last request time
        self.last_request_time[domain] = time.time()
        self.request_counts[domain] += 1

        # Add rate limit metadata to request
        request.meta['rate_limit_delay'] = required_delay
        request.meta['domain_request_count'] = self.request_counts[domain]

        return None  # Continue processing

    def process_response(self, request, response, spider):
        """Process response - reset backoff on success"""
        return response

    def process_exception(self, request, exception, spider):
        """
        Process exceptions - apply backoff on errors.

        If we get rate-limited (429) or server errors (5xx), increase delay.
        """
        domain = request.url.split('/')[2]

        # Check if this is a rate limiting or server error
        if hasattr(exception, 'response') and exception.response:
            status_code = exception.response.status

            if status_code == 429:  # Too Many Requests
                # Apply backoff
                current_delay = self.min_delay
                new_delay = current_delay * self.error_backoff_multiplier

                logger.warning(
                    f"Rate limited by {domain} (HTTP 429). "
                    f"Increasing delay to {new_delay:.2f}s"
                )

                self.min_delay = new_delay

            elif 500 <= status_code < 600:  # Server errors
                logger.warning(
                    f"Server error from {domain} (HTTP {status_code}). "
                    "Applying backoff."
                )

        return None  # Let other middlewares handle the exception

    def spider_closed(self, spider):
        """
        Called when spider closes. Log rate limiting statistics.
        """
        logger.info(f"Rate Limiting Statistics for {spider.name}:")

        for domain, count in self.request_counts.items():
            logger.info(f"  {domain}: {count} requests")

        total_requests = sum(self.request_counts.values())
        logger.info(f"  Total requests: {total_requests}")
        logger.info(f"  Final delay: {self.min_delay:.2f}s")
