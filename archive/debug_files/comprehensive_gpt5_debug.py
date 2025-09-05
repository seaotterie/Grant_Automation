#!/usr/bin/env python3
"""
Comprehensive GPT-5 Debug - Test all GPT-5 models and response fields
"""

import openai
import os
from dotenv import load_dotenv
import json

load_dotenv()

def comprehensive_gpt5_debug():
    """Test all aspects of GPT-5 response"""
    
    print("=" * 70)
    print("COMPREHENSIVE GPT-5 DEBUG")
    print("=" * 70)
    
    api_key = os.getenv('OPENAI_API_KEY')
    client = openai.OpenAI(api_key=api_key)
    
    models = ["gpt-5", "gpt-5-mini", "gpt-5-nano"]
    
    for model in models:
        print(f"\nTesting {model}...")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "Provide a brief analysis of grant funding opportunity. Just say 'This is a test response from [MODEL_NAME].'"}
                ],
                max_completion_tokens=50
            )
            
            # Detailed response inspection
            print(f"  Model returned: {response.model}")
            print(f"  Tokens used: {response.usage.total_tokens}")
            print(f"  Finish reason: {response.choices[0].finish_reason}")
            
            # Check all possible content fields
            choice = response.choices[0]
            message = choice.message
            
            print(f"  Message content: '{message.content}'")
            print(f"  Message role: {message.role}")
            
            # Try to serialize entire response to see structure
            print(f"  Raw choice object keys: {list(vars(choice).keys())}")
            print(f"  Raw message object keys: {list(vars(message).keys())}")
            
            # Check if there's content in other places
            if hasattr(message, 'content') and message.content:
                print(f"  SUCCESS: Content found in message.content")
                print(f"  Content: '{message.content}'")
            elif hasattr(choice, 'text'):
                print(f"  Content in choice.text: '{choice.text}'")
            elif hasattr(response, 'text'):
                print(f"  Content in response.text: '{response.text}'")
            else:
                print(f"  NO CONTENT FOUND - but tokens consumed!")
                
                # Debug: Print entire response structure
                print(f"  Full response dump:")
                try:
                    print(f"    Response type: {type(response)}")
                    print(f"    Response model: {response.model}")
                    print(f"    Response usage: {response.usage}")
                    print(f"    Choice 0: {choice}")
                    print(f"    Message: {message}")
                except Exception as e:
                    print(f"    Error dumping response: {e}")
            
        except Exception as e:
            print(f"  ERROR with {model}: {str(e)}")
    
    # Try a different approach - streaming response
    print(f"\nTesting streaming response...")
    try:
        stream = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "user", "content": "Say hello"}
            ],
            max_completion_tokens=20,
            stream=True
        )
        
        content_chunks = []
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content_chunks.append(chunk.choices[0].delta.content)
        
        full_content = ''.join(content_chunks)
        print(f"  Streaming content: '{full_content}'")
        print(f"  Streaming content length: {len(full_content)}")
        
        if full_content:
            print(f"  SUCCESS: Streaming works!")
            return True, full_content
        else:
            print(f"  Streaming also empty")
            
    except Exception as e:
        print(f"  Streaming error: {str(e)}")
    
    return False, ""

if __name__ == "__main__":
    success, content = comprehensive_gpt5_debug()
    if success:
        print(f"\nFound working GPT-5 method: {len(content)} chars")
    else:
        print(f"\nGPT-5 content issue confirmed across all methods")