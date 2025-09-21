#!/usr/bin/env python3
"""
Direct GPT-5 Test - Bypass OpenAI service to test raw GPT-5 API
"""

import openai
import os
import sys
# Configure UTF-8 encoding for Windows
if os.name == 'nt':
    import codecs
    try:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except AttributeError:
        # stdout/stderr may already be wrapped or redirected
        pass

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

    # List of GPT-5 models only (no fallback allowed)
    models_to_try = [
        os.getenv('AI_LITE_MODEL', 'gpt-5-nano'),
        os.getenv('AI_HEAVY_MODEL', 'gpt-5-mini'),
        os.getenv('AI_RESEARCH_MODEL', 'gpt-5'),
        "gpt-5-nano",
        "gpt-5-mini",
        "gpt-5"
    ]

    client = openai.OpenAI(api_key=api_key)

    for model in models_to_try:
        print(f"Trying model: {model}")
        try:
            # Try with max_completion_tokens first (for newer models like GPT-5)
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": "Analyze Heroes Bridge seeking funding from Fauquier Health Foundation. Provide strategic score and recommendation."}
                    ],
                    max_completion_tokens=200
                )
            except Exception as completion_tokens_error:
                # Fallback to max_tokens for older models
                if "max_completion_tokens" in str(completion_tokens_error):
                    print(f"  Using max_tokens parameter for {model}")
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "user", "content": "Analyze Heroes Bridge seeking funding from Fauquier Health Foundation. Provide strategic score and recommendation."}
                        ],
                        max_tokens=200
                    )
                else:
                    raise completion_tokens_error

            print(f"Model: {response.model}")
            print(f"Tokens: {response.usage.total_tokens}")
            print(f"Finish reason: {response.choices[0].finish_reason}")
            print(f"Content length: {len(response.choices[0].message.content or '')}")
            print(f"\nContent:")
            print(f"'{response.choices[0].message.content}'")

            content = response.choices[0].message.content
            if content and len(content.strip()) > 0:
                print(f"\nSUCCESS: Model {model} working with content")
                return True, content
            else:
                print(f"\nPROBLEM: Model {model} returning empty content, trying next model...")
                continue

        except Exception as e:
            print(f"ERROR with model {model}: {str(e)}")
            print("Trying next model...")
            continue

    print("\nFAILED: All models failed or returned empty content")
    return False, ""

if __name__ == "__main__":
    success, content = direct_gpt5_test()
    if success:
        print(f"\nDirect GPT-5 working - content received: {len(content)} chars")
    else:
        print(f"\nDirect GPT-5 also has content issues")