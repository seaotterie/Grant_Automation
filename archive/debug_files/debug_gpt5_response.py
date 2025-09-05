#!/usr/bin/env python3
"""
Debug GPT-5 Response Issue
Test what's actually being returned from GPT-5 calls
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.openai_service import OpenAIService
from dotenv import load_dotenv

load_dotenv()

async def debug_gpt5_response():
    """Debug why GPT-5 responses are empty"""
    
    print("=" * 60)
    print("DEBUGGING GPT-5 RESPONSE ISSUE")
    print("=" * 60)
    
    service = OpenAIService()
    
    if not service.client:
        print("ERROR: OpenAI service not initialized")
        return False
    
    print("Testing simple GPT-5 request...")
    
    try:
        response = await service.create_completion(
            model="gpt-5-nano",
            messages=[
                {"role": "user", "content": "Say hello and confirm you are GPT-5"}
            ],
            max_tokens=50
        )
        
        print(f"Response object type: {type(response)}")
        print(f"Response content: '{response.content}'")
        print(f"Response content length: {len(response.content)}")
        print(f"Response content is None: {response.content is None}")
        print(f"Response content is empty string: {response.content == ''}")
        print(f"Response model: {response.model}")
        print(f"Response usage: {response.usage}")
        print(f"Response cost: {response.cost_estimate}")
        
        # Raw response inspection
        print(f"\nRaw response attributes:")
        for attr in dir(response):
            if not attr.startswith('_'):
                try:
                    value = getattr(response, attr)
                    if not callable(value):
                        print(f"  {attr}: {value}")
                except:
                    pass
        
        if response.content:
            print(f"\nSUCCESS: GPT-5 response received")
            print(f"Content: {response.content}")
        else:
            print(f"\nPROBLEM: GPT-5 response is empty")
            
        return response.content is not None and len(response.content) > 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await debug_gpt5_response()
    if success:
        print("\nGPT-5 response extraction working")
    else:
        print("\nGPT-5 response extraction needs fixing")
    return success

if __name__ == "__main__":
    result = asyncio.run(main())