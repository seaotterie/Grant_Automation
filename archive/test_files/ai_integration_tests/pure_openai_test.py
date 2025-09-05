#!/usr/bin/env python3
"""
Pure OpenAI Test - Completely isolated from system components
Direct API call with no project imports or system interference
"""

import openai
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_pure_openai():
    """Test OpenAI API with minimal code - no system imports"""
    
    print("=" * 60)
    print("PURE OPENAI API TEST - NO SYSTEM COMPONENTS")
    print("=" * 60)
    
    # Get API key directly
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"API Key found: {api_key is not None}")
    print(f"API Key starts with sk-: {api_key.startswith('sk-') if api_key else False}")
    print(f"API Key length: {len(api_key) if api_key else 0}")
    
    if not api_key:
        raise ValueError("No OPENAI_API_KEY found")
    
    # Set the API key
    openai.api_key = api_key
    
    print(f"\nMaking direct OpenAI API call...")
    print(f"Using openai library version: {openai.__version__}")
    
    try:
        # Create OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Make the simplest possible API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use cheapest model
            messages=[
                {"role": "user", "content": "Say 'Hello, this is a real API call test. The current time is approximately 4:20 PM EST on September 2, 2025.'"}
            ],
            max_tokens=50
        )
        
        # Print the response
        content = response.choices[0].message.content
        usage = response.usage
        
        print(f"\n" + "=" * 60)
        print("API RESPONSE RECEIVED")
        print("=" * 60)
        print(f"Response: {content}")
        print(f"Model: {response.model}")
        print(f"Total tokens: {usage.total_tokens}")
        print(f"Prompt tokens: {usage.prompt_tokens}")
        print(f"Completion tokens: {usage.completion_tokens}")
        
        # Check if this looks like a real response
        if "real API call test" in content and "4:20 PM" in content:
            print(f"\n✅ REAL API CALL SUCCESS - Check your OpenAI dashboard!")
            return True
        else:
            print(f"\n⚠️ WARNING: Response may be simulated")
            return False
            
    except Exception as e:
        print(f"\n❌ API call failed: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pure_openai()
    if success:
        print("\nSUCCESS: Real OpenAI API call completed")
        print("Check https://platform.openai.com/usage for token usage")
    else:
        print("\nFAILED: API call did not complete successfully")