#!/usr/bin/env python3
"""
Test GPT-5 Model Availability - Direct API calls to confirm GPT-5 is available
"""

import openai
import os
from dotenv import load_dotenv

load_dotenv()

def test_gpt5_models():
    """Test GPT-5 model availability with direct OpenAI API calls"""
    
    print("=" * 70)
    print("GPT-5 MODEL AVAILABILITY TEST")
    print("=" * 70)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: No API key found")
        return False
    
    print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=api_key)
    
    # Test GPT-5 models
    gpt5_models = ["gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-preview"]
    
    for model in gpt5_models:
        print(f"\nTesting {model}...")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": f"Say 'GPT-5 model {model} is working correctly'"}
                ],
                max_completion_tokens=20
            )
            
            content = response.choices[0].message.content
            usage = response.usage
            
            print(f"  SUCCESS: {content}")
            print(f"  Tokens: {usage.total_tokens}")
            print(f"  Model confirmed: {response.model}")
            
        except openai.NotFoundError as e:
            print(f"  NOT AVAILABLE: {model} - {str(e)}")
        except Exception as e:
            print(f"  ERROR: {model} - {str(e)}")
    
    return True

if __name__ == "__main__":
    test_gpt5_models()