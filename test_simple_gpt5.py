#!/usr/bin/env python3
"""
Simple GPT-5 Test
Test basic GPT-5 functionality with a minimal prompt.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.core.openai_service import get_openai_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Test simple GPT-5 response"""
    logger.info("Testing simple GPT-5 response")
    
    openai_service = get_openai_service()
    
    try:
        response = await openai_service.create_completion(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=100
        )
        
        logger.info(f"Response: '{response.content}'")
        logger.info(f"Finish reason: {response.finish_reason}")
        logger.info(f"Usage: {response.usage}")
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())