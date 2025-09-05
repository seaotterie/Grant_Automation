#!/usr/bin/env python3
"""
Direct GPT-5 Test - Bypass OpenAI service to test raw GPT-5 API
"""

import openai
import os
from dotenv import load_dotenv

load_dotenv()

def direct_gpt5_test():
    """Test GPT-5 directly without our service wrapper"""
    
    print("=" * 60)
    print("DIRECT GPT-5 API TEST")
    print("=" * 60)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: No API key")
        return False
    
    print("Testing direct GPT-5 call...")
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "user", "content": "Analyze Heroes Bridge seeking funding from Fauquier Health Foundation. Provide strategic score and recommendation."}
            ],
            max_completion_tokens=200
        )
        
        print(f"Model: {response.model}")
        print(f"Tokens: {response.usage.total_tokens}")
        print(f"Finish reason: {response.choices[0].finish_reason}")
        print(f"Content length: {len(response.choices[0].message.content or '')}")
        print(f"\nContent:")
        print(f"'{response.choices[0].message.content}'")
        
        content = response.choices[0].message.content
        if content and len(content.strip()) > 0:
            print(f"\nSUCCESS: Direct GPT-5 working with content")
            return True, content
        else:
            print(f"\nPROBLEM: Direct GPT-5 also returning empty content")
            return False, ""
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False, ""

if __name__ == "__main__":
    success, content = direct_gpt5_test()
    if success:
        print(f"\nDirect GPT-5 working - content received: {len(content)} chars")
    else:
        print(f"\nDirect GPT-5 also has content issues")