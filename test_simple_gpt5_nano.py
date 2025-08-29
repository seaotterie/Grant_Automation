#!/usr/bin/env python3
"""
Simple GPT-5-nano Test - Debug the response extraction issue
"""

import asyncio
import sys
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

sys.path.append('.')

import logging
logging.basicConfig(level=logging.INFO)

async def test_simple_gpt5_nano():
    """Test simple GPT-5-nano interaction"""
    
    print("=" * 60)
    print("SIMPLE GPT-5-NANO TEST")
    print("=" * 60)
    
    try:
        from src.core.openai_service import get_openai_service
        
        service = get_openai_service()
        
        # Simple test prompt
        simple_prompt = """Please respond with exactly this JSON format:
{
  "test_id": {
    "result": "success",
    "message": "GPT-5-nano is working"
  }
}

RESPONSE (JSON only):"""
        
        print("Testing GPT-5-nano with simple JSON request...")
        print(f"Model: gpt-5-nano (GPT-5 model test)")
        print()
        
        # Make API call
        start_time = datetime.now()
        # Test with known working model first
        response = await service.create_completion(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": simple_prompt}],
            max_tokens=200,
            temperature=0.7
        )
        end_time = datetime.now()
        
        print("RESULTS:")
        print(f"Processing time: {(end_time - start_time).total_seconds():.2f}s")
        print(f"Total tokens: {response.usage.get('total_tokens', 'unknown')}")
        print(f"Cost: ${response.cost_estimate:.6f}")
        print(f"Model used: {response.model}")
        print(f"Finish reason: {response.finish_reason}")
        print()
        print("RESPONSE CONTENT:")
        print(f"Content length: {len(response.content)}")
        if response.content:
            print(f"Content: {repr(response.content[:200])}")
            print(f"Raw content: {response.content}")
        else:
            print("EMPTY CONTENT!")
            
        return {
            "status": "success" if response.content else "empty_response",
            "has_content": bool(response.content),
            "content_length": len(response.content),
            "tokens": response.usage.get('total_tokens', 0),
            "cost": response.cost_estimate
        }
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    print("Testing simple GPT-5-nano interaction...")
    result = asyncio.run(test_simple_gpt5_nano())
    
    if result.get("status") == "success":
        print(f"\nSUCCESS! GPT-5-nano returned {result['content_length']} characters")
    elif result.get("status") == "empty_response":
        print(f"\nAPI WORKING but empty response - {result['tokens']} tokens used")
    else:
        print(f"\nFAILED: {result.get('error', 'Unknown error')}")