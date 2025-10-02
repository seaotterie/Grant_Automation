#!/usr/bin/env python3
"""
Single GPT URL Discovery Test
Quick test to debug GPT response parsing.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import system components
from src.processors.analysis.gpt_url_discovery import GPTURLDiscoveryProcessor
from src.core.data_models import ProcessorConfig, WorkflowConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Test single URL discovery"""
    logger.info("Testing single GPT URL Discovery")
    
    # Verify OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OpenAI API key found")
        return
    
    processor = GPTURLDiscoveryProcessor()
    
    # Test with Heroes Bridge
    org_data = {
        'organization_name': 'Heroes Bridge',
        'ein': '812827604',
        'city': 'Warrenton',
        'state': 'VA',
        'organization_type': 'Veterans Services'
    }
    
    config = ProcessorConfig(
        workflow_id="test_single_url",
        processor_name="gpt_url_discovery",
        workflow_config=WorkflowConfig(),
        processor_specific_config={
            'organization_data': org_data,
            'force_refresh': True
        }
    )
    
    result = await processor.execute(config)
    
    logger.info(f"Success: {result.success}")
    if result.success:
        logger.info(f"URLs found: {result.data.get('urls', [])}")
        logger.info(f"Predictions: {result.data.get('predictions', [])}")
    else:
        logger.error(f"Errors: {result.errors}")

if __name__ == "__main__":
    asyncio.run(main())