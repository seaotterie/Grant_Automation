#!/usr/bin/env python3
"""
Verify Billing Test - Make a trackable API call to confirm billing
"""

import openai
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def verify_openai_billing():
    """Make a trackable API call to verify billing"""
    
    print("=" * 60)
    print("OPENAI BILLING VERIFICATION TEST")
    print("=" * 60)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: No API key found")
        return False
    
    print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
    
    # Create unique identifier for this test
    test_id = f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Make a more expensive call to ensure it shows up in billing
        prompt = f"""
        BILLING VERIFICATION TEST - ID: {test_id}
        
        Please respond with exactly this format:
        
        CONFIRMATION: This is a real OpenAI API call
        TEST ID: {test_id}
        TIMESTAMP: {datetime.now().isoformat()}
        TOKENS: This response should consume approximately 100-150 tokens
        BILLING: This call should appear in your OpenAI usage dashboard
        STATUS: Real API call completed successfully
        
        Please include some additional text to ensure we consume enough tokens for clear billing visibility. This is a verification that the API key is working and charges are being applied to the correct account. The user wants to confirm that real API calls are being made and billed appropriately.
        """
        
        print(f"Making API call with test ID: {test_id}")
        print(f"Prompt length: {len(prompt)} characters")
        
        response = client.chat.completions.create(
            model="gpt-4",  # More expensive model to ensure visibility
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        
        content = response.choices[0].message.content
        usage = response.usage
        
        # Calculate cost
        prompt_cost = usage.prompt_tokens * 0.00003  # GPT-4 input cost
        completion_cost = usage.completion_tokens * 0.00006  # GPT-4 output cost
        total_cost = prompt_cost + completion_cost
        
        print(f"\nAPI CALL COMPLETED")
        print(f"==================")
        print(f"Test ID: {test_id}")
        print(f"Model: {response.model}")
        print(f"Total Tokens: {usage.total_tokens}")
        print(f"Prompt Tokens: {usage.prompt_tokens}")
        print(f"Completion Tokens: {usage.completion_tokens}")
        print(f"Estimated Cost: ${total_cost:.4f}")
        
        print(f"\nRESPONSE CONTENT:")
        print(f"-" * 40)
        print(content)
        print(f"-" * 40)
        
        # Check if response contains our test ID
        if test_id in content:
            print(f"\nSUCCESS: Response contains test ID {test_id}")
            print(f"This confirms the API call went to OpenAI servers")
            print(f"\nTo verify billing:")
            print(f"1. Go to https://platform.openai.com/usage")
            print(f"2. Look for usage around {datetime.now().strftime('%H:%M')} today")
            print(f"3. Should see {usage.total_tokens} tokens for GPT-4 model")
            print(f"4. Cost should be approximately ${total_cost:.4f}")
            return True
        else:
            print(f"\nWARNING: Response doesn't contain test ID - may be simulated")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    verify_openai_billing()