#!/usr/bin/env python3
"""
Simple GPT-5 Test - Verify GPT-5 integration with OpenAI service
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.openai_service import OpenAIService
from dotenv import load_dotenv

load_dotenv()

async def test_gpt5_service():
    """Test GPT-5 models through our OpenAI service"""
    
    print("=" * 60)
    print("GPT-5 SERVICE INTEGRATION TEST")
    print("=" * 60)
    
    # Initialize service
    service = OpenAIService()
    
    if not service.client:
        print("ERROR: OpenAI service not initialized")
        return False
    
    print("SUCCESS: OpenAI service initialized")
    
    # Test GPT-5-nano (most cost-effective)
    try:
        print("\nTesting GPT-5-nano...")
        response = await service.create_completion(
            model="gpt-5-nano",
            messages=[
                {"role": "user", "content": "Analyze Heroes Bridge (EIN 81-2827604) seeking funding from Fauquier Health Foundation (EIN 30-0219424). Both in Warrenton, VA. Provide strategic fit score and key recommendation."}
            ],
            max_tokens=200
        )
        
        print(f"  Content: {response.content[:200]}...")
        print(f"  Tokens: {response.usage['total_tokens']}")
        print(f"  Cost: ${response.cost_estimate:.4f}")
        print(f"  Model: {response.model}")
        
        return True
        
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return False

async def main():
    success = await test_gpt5_service()
    if success:
        print("\nSUCCESS: GPT-5 service integration working")
    else:
        print("\nFAILED: GPT-5 service integration failed")
    return success

if __name__ == "__main__":
    result = asyncio.run(main())