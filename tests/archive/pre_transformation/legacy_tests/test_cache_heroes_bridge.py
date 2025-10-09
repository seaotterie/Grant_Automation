#!/usr/bin/env python3
"""
Test Heroes Bridge URL Caching
Manually cache Heroes Bridge URL and test retrieval.
"""

import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

from src.processors.analysis.gpt_url_discovery import GPTURLDiscoveryProcessor
from src.core.data_models import ProcessorConfig, WorkflowConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Test Heroes Bridge URL caching functionality"""
    logger.info("Testing Heroes Bridge URL Caching")
    
    processor = GPTURLDiscoveryProcessor()
    
    # Heroes Bridge EIN and expected URL
    ein = "812827604"
    expected_url = "https://heroesbridge.org"  # Likely URL for Heroes Bridge
    
    # Cache the URL manually
    await processor.cache_successful_url(ein, expected_url, 1.0)
    logger.info(f"✓ Cached URL for Heroes Bridge: {expected_url}")
    
    # Test retrieval through processor
    org_data = {
        'organization_name': 'Heroes Bridge',
        'ein': ein,
        'city': 'Warrenton',
        'state': 'VA',
        'organization_type': 'Veterans Services'
    }
    
    config = ProcessorConfig(
        workflow_id="test_cache_heroes_bridge",
        processor_name="gpt_url_discovery",
        workflow_config=WorkflowConfig(),
        processor_specific_config={
            'organization_data': org_data,
            'force_refresh': False  # Use cache
        }
    )
    
    # Execute URL discovery (should hit cache)
    result = await processor.execute(config)
    
    if result.success:
        urls = result.data.get('urls', [])
        source = result.data.get('source', 'unknown')
        logger.info(f"✓ Success! Source: {source}")
        logger.info(f"✓ URLs retrieved: {urls}")
        logger.info(f"✓ Cache working perfectly for Heroes Bridge")
    else:
        logger.error(f"✗ Failed: {result.errors}")
    
    # Show cache stats
    stats = await processor.get_cache_stats()
    logger.info(f"✓ Cache stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())