#!/usr/bin/env python3
"""
Debug OpenAI Quota Issues
Investigates the specific quota/billing issue
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append('.')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def debug_openai_quota():
    """Debug OpenAI API quota and billing status"""
    
    print("=" * 60)
    print("OPENAI QUOTA DEBUG ANALYSIS")
    print("=" * 60)
    print()
    
    # Check API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("[ERROR] No OPENAI_API_KEY found")
        return
    
    print("1. API KEY ANALYSIS")
    print("-" * 20)
    print(f"Key format: {openai_key[:12]}...{openai_key[-8:]}")
    print(f"Key length: {len(openai_key)} characters")
    
    # Analyze key format
    if openai_key.startswith("sk-proj-"):
        print("Key type: PROJECT KEY (newer format)")
        print("Note: Project keys may have different quota/billing rules")
    elif openai_key.startswith("sk-"):
        print("Key type: STANDARD API KEY (legacy format)")
    else:
        print("Key type: UNKNOWN FORMAT")
    
    print()
    
    # Test with minimal request
    print("2. MINIMAL API TEST")
    print("-" * 20)
    
    try:
        import openai
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=openai_key)
        
        # Try the smallest possible request
        print("Testing with minimal request (1 token max)...")
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1,
            temperature=0
        )
        
        print("[SUCCESS] Minimal API call worked!")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Usage: {response.usage}")
        
        # Calculate actual cost
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        
        # GPT-3.5-turbo pricing: $0.001/1K input, $0.002/1K output
        cost = (input_tokens * 0.001 / 1000) + (output_tokens * 0.002 / 1000)
        print(f"Calculated cost: ${cost:.6f}")
        
    except openai.RateLimitError as e:
        print(f"[RATE LIMIT ERROR] {e}")
        print("This suggests quota/billing limits")
        
        # Parse error details
        if hasattr(e, 'response') and e.response:
            print(f"Status code: {e.response.status_code}")
            if hasattr(e.response, 'json'):
                try:
                    error_data = e.response.json()
                    print(f"Error details: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Raw response: {e.response.text}")
        
    except openai.AuthenticationError as e:
        print(f"[AUTH ERROR] {e}")
        print("API key may be invalid or revoked")
        
    except Exception as e:
        print(f"[OTHER ERROR] {type(e).__name__}: {e}")
    
    print()
    
    # Test different models/approaches
    print("3. MODEL AVAILABILITY TEST")
    print("-" * 30)
    
    models_to_test = [
        ("gpt-3.5-turbo", "Standard model"),
        ("gpt-4o-mini", "Smaller GPT-4 variant"), 
        ("gpt-4", "Full GPT-4"),
    ]
    
    for model, description in models_to_test:
        print(f"Testing {model} ({description})...")
        
        try:
            client = AsyncOpenAI(api_key=openai_key)
            
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=1
            )
            
            print(f"  [SUCCESS] {model} works")
            
        except openai.NotFoundError:
            print(f"  [NOT FOUND] {model} not available for this API key")
        except openai.RateLimitError:
            print(f"  [QUOTA EXCEEDED] {model} blocked by quota limits")
        except Exception as e:
            print(f"  [ERROR] {model} failed: {type(e).__name__}")
    
    print()
    
    # Check quota information if possible
    print("4. QUOTA ANALYSIS")
    print("-" * 20)
    
    print("Common quota scenarios for $0.00 spend:")
    print("1. NEW ACCOUNT: Free tier with very low limits")
    print("2. PROJECT KEY: Different billing/quota rules")
    print("3. ORGANIZATION LIMITS: Org-level spending controls") 
    print("4. RATE LIMITS: Too many requests too quickly")
    print("5. MODEL ACCESS: Limited access to certain models")
    print()
    
    print("Recommendations:")
    print("1. Check OpenAI Dashboard > Billing for actual usage")
    print("2. Check OpenAI Dashboard > API Keys for key limits")
    print("3. Verify payment method is set up")
    print("4. Try different models (gpt-3.5-turbo vs gpt-4)")
    print("5. Check if using Organization vs Personal account")
    print()
    
    # Test our service's handling
    print("5. SYSTEM INTEGRATION TEST")
    print("-" * 30)
    
    try:
        from src.core.openai_service import OpenAIService
        
        service = OpenAIService(api_key=openai_key)
        print(f"Service initialized: {service.client is not None}")
        
        # Check cost tracking
        print("Cost tracking models:")
        for model, costs in service.cost_per_token.items():
            print(f"  {model}: ${costs['input']*1000:.4f}/1K input, ${costs['output']*1000:.4f}/1K output")
        
        print()
        print("Testing service with minimal request...")
        
        response = await service.create_completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1
        )
        
        print(f"Service response content: {response.content}")
        print(f"Service cost estimate: ${response.cost_estimate:.6f}")
        print(f"Service usage: {response.usage}")
        
        # Check if it was simulation
        if "analysis_result" in response.content or len(response.content) > 50:
            print("[DETECTED] Response appears to be simulation")
        else:
            print("[DETECTED] Response appears to be real API call")
        
    except Exception as e:
        print(f"Service test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("DEBUG COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    print("Starting OpenAI Quota Debug Analysis...")
    asyncio.run(debug_openai_quota())