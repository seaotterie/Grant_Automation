"""
Scrapy Settings for Web Intelligence Tool

Settings derived from 12factors.toml for consistent configuration management.
These settings prioritize:
1. Respectful scraping (rate limiting, robots.txt compliance)
2. Data quality (validation pipelines)
3. 12-factor compliance (stateless, config-driven)
"""

import os
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# ============================================================================
# BASIC SCRAPY SETTINGS
# ============================================================================

BOT_NAME = 'catalynx_web_intelligence'

SPIDER_MODULES = ['app.scrapy_spiders']
NEWSPIDER_MODULE = 'app.scrapy_spiders'

# ============================================================================
# RESPECTFUL SCRAPING CONFIGURATION (from 12factors.toml)
# ============================================================================

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 2  # Low concurrency for respectful scraping

# Configure a delay for requests for the same website (default: 0)
DOWNLOAD_DELAY = 2.0  # 2 seconds between requests

# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'User-Agent': 'CatalynxBot/1.0 (+https://catalynx.io/bot)',
}

# ============================================================================
# SPIDER MIDDLEWARES
# ============================================================================

SPIDER_MIDDLEWARES = {
    'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware': 50,
    'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': 500,
    'scrapy.spidermiddlewares.referer.RefererMiddleware': 700,
    'scrapy.spidermiddlewares.urllength.UrlLengthMiddleware': 800,
    'scrapy.spidermiddlewares.depth.DepthMiddleware': 900,
}

# ============================================================================
# DOWNLOADER MIDDLEWARES
# ============================================================================

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': 100,
    'scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware': 300,
    'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
    'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': 400,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 500,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
    'scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware': 580,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 590,
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 600,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750,
    'scrapy.downloadermiddlewares.stats.DownloaderStats': 850,
    'scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware': 900,

    # Custom middlewares
    'app.scrapy_middlewares.smart_url_middleware.SmartURLMiddleware': 950,
    'app.scrapy_middlewares.rate_limit_middleware.RateLimitMiddleware': 960,
}

# ============================================================================
# ITEM PIPELINES
# ============================================================================

ITEM_PIPELINES = {
    # Validation pipeline - verify against 990 data
    'app.scrapy_pipelines.validation_pipeline.NinetyValidationPipeline': 100,

    # Deduplication pipeline - remove duplicate entries
    'app.scrapy_pipelines.deduplication_pipeline.DeduplicationPipeline': 200,

    # Structured output pipeline - convert to BAML models
    'app.scrapy_pipelines.structured_output_pipeline.StructuredOutputPipeline': 300,
}

# ============================================================================
# EXTENSIONS
# ============================================================================

EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,  # Disable telnet console
    'scrapy.extensions.corestats.CoreStats': 10,
    'scrapy.extensions.memusage.MemoryUsage': 20,
}

# ============================================================================
# AUTOTHROTTLE (ADAPTIVE THROTTLING)
# ============================================================================

# Enable and configure the AutoThrottle extension (disabled by default)
AUTOTHROTTLE_ENABLED = True

# The initial download delay
AUTOTHROTTLE_START_DELAY = 2

# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 10

# The average number of requests Scrapy should be sending in parallel to each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Enable showing throttling stats for every response received
AUTOTHROTTLE_DEBUG = False

# ============================================================================
# HTTP CACHING
# ============================================================================

# Enable and configure HTTP caching (disabled by default)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 604800  # 7 days (from 12factors.toml cache_expiry_hours)
HTTPCACHE_DIR = 'data/scrapy_cache'
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 400, 403, 404, 408]
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# ============================================================================
# DEPTH & CRAWLING LIMITS
# ============================================================================

# Maximum crawl depth (from 12factors.toml)
DEPTH_LIMIT = 3

# Download timeout
DOWNLOAD_TIMEOUT = 30  # seconds (from 12factors.toml)

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 2  # Maximum number of retries
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# ============================================================================
# LOGGING
# ============================================================================

# Log level
LOG_LEVEL = 'INFO'

# Log format (JSON structured logging for 12-factor compliance)
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# Disable log stats
LOG_ENABLED = True
LOG_ENCODING = 'utf-8'

# ============================================================================
# CUSTOM SETTINGS FROM 12FACTORS.TOML
# ============================================================================

# These can be overridden per-spider or per-request
CUSTOM_SETTINGS = {
    # Profile Builder (Use Case 1)
    'profile_builder': {
        'max_pages': 10,
        'target_pages': ['about', 'mission', 'programs', 'board', 'staff', 'contact', 'team', 'leadership'],
        'verification_required': True,
    },

    # Opportunity Research (Use Case 2) - Grantmaking nonprofits
    'opportunity_research': {
        'max_pages': 15,
        'target_pages': ['grants', 'funding', 'apply', 'giving', 'how-to-apply', 'grant-programs', 'application'],
        'verification_required': True,  # Verify against 990 Schedule I
    },

    # Foundation Research (Use Case 3)
    'foundation_research': {
        'max_pages': 12,
        'target_pages': ['apply', 'guidelines', 'grants', 'priorities', 'trustees', 'how-to-apply', 'funding'],
        'verification_required': True,
    },
}

# ============================================================================
# REQUEST FINGERPRINTER
# ============================================================================

# Use custom request fingerprinter to handle dynamic parameters
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'

# ============================================================================
# FEED EXPORT SETTINGS
# ============================================================================

# Disable feed export (we use structured output pipeline instead)
FEEDS = {}
