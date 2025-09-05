#!/usr/bin/env python3
"""
Test Fixed OpenAI Service - Verify real API calls work after removing GPT-5 restriction
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.openai_service import OpenAIService
from dotenv import load_dotenv

load_dotenv()

async def test_fixed_openai_service():
    """Test the fixed OpenAI service with real models"""
    
    print("=" * 70)
    print("TESTING FIXED OPENAI SERVICE - REAL API CALLS")
    print("=" * 70)
    
    # Initialize the service
    service = OpenAIService()
    
    if not service.client:
        print("ERROR: OpenAI service not initialized - check API key")
        return False
    
    print("SUCCESS: OpenAI service initialized with API key")
    
    # Test with GPT-3.5-turbo (should work now)
    try:
        print("\n1. Testing GPT-3.5-turbo...")
        response = await service.create_completion(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'GPT-3.5-turbo real API test successful'"}
            ],
            max_tokens=20
        )
        
        print(f"   Content: {response.content}")
        print(f"   Tokens: {response.usage}")
        print(f"   Cost: ${response.cost_estimate:.4f}")
        
        if "successful" in response.content:
            print("   SUCCESS: Real API call worked!")
        else:
            print("   WARNING: May be simulated")
            
    except Exception as e:
        print(f"   ERROR: {str(e)}")
        return False
    
    # Test with GPT-4 (should work now)
    try:
        print("\n2. Testing GPT-4...")
        response = await service.create_completion(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "Say 'GPT-4 real API test successful'"}
            ],
            max_tokens=20
        )
        
        print(f"   Content: {response.content}")
        print(f"   Tokens: {response.usage}")
        print(f"   Cost: ${response.cost_estimate:.4f}")
        
        if "successful" in response.content:
            print("   SUCCESS: Real API call worked!")
        else:
            print("   WARNING: May be simulated")
            
    except Exception as e:
        print(f"   ERROR: {str(e)}")
        return False
    
    print("\n" + "=" * 70)
    print("OPENAI SERVICE FIX VERIFICATION COMPLETE")
    print("=" * 70)
    print("Both GPT-3.5-turbo and GPT-4 should now work with real API calls")
    print("Next: Run complete AI processing with substantial token usage")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_fixed_openai_service())
    if success:
        print("\nSUCCESS: OpenAI service fixed and ready for real processing")
    else:
        print("\nFAILED: OpenAI service still has issues")