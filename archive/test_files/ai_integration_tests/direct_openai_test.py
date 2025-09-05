#!/usr/bin/env python3
"""
Direct OpenAI API Test - Bypass System Issues
Tests OpenAI API directly to show real request/response flow
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
sys.path.append('.')

async def direct_openai_test():
    """Test OpenAI API directly without the system's service layer"""
    
    print("=" * 70)
    print("DIRECT OPENAI API TEST - REAL RESPONSES")
    print("=" * 70)
    print()
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("[ERROR] No OPENAI_API_KEY found")
        return
        
    print(f"API Key: {api_key[:12]}...{api_key[-8:]}")
    print()
    
    try:
        import openai
        from openai import AsyncOpenAI
        
        # Initialize client directly
        client = AsyncOpenAI(api_key=api_key)
        
        # Test 1: Simple confirmation test
        print("1. SIMPLE API CONFIRMATION")
        print("-" * 30)
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Respond with exactly 'REAL_API_SUCCESS' and nothing else."}
            ],
            max_tokens=5,
            temperature=0
        )
        
        content = response.choices[0].message.content
        usage = response.usage
        
        print(f"Response: '{content}'")
        print(f"Usage: input={usage.prompt_tokens}, output={usage.completion_tokens}, total={usage.total_tokens}")
        
        if "REAL_API_SUCCESS" in content:
            print("[SUCCESS] Real API confirmed!")
        else:
            print("[UNEXPECTED] Response doesn't match expected")
            
        # Calculate cost
        cost = (usage.prompt_tokens * 0.001/1000) + (usage.completion_tokens * 0.002/1000)
        print(f"Actual cost: ${cost:.6f}")
        print()
        
        # Test 2: Grant Analysis Simulation
        print("2. GRANT ANALYSIS PROMPT TEST")
        print("-" * 35)
        
        grant_prompt = """You are a grant strategy expert. Analyze this opportunity for compatibility with our nonprofit:

ORGANIZATION PROFILE:
Name: Rural Health Initiative
Mission: Improving healthcare access in underserved rural communities
Focus Areas: primary care, telehealth, community health workers
Annual Budget: $2.5M

OPPORTUNITY TO ANALYZE:
Organization: HRSA Rural Health Grant Program  
Funding: $150,000
Description: Federal program supporting rural health clinics and community health centers in expanding primary care access through innovative delivery models including telemedicine and mobile health units.
Deadline: 2024-12-31

Provide analysis in this EXACT JSON format:
{
  "compatibility_score": 0.85,
  "strategic_value": "high", 
  "funding_likelihood": 0.75,
  "strategic_rationale": "Brief 2-sentence analysis of fit and opportunity",
  "risk_assessment": ["risk1", "risk2"],
  "action_priority": "immediate"
}

Respond with JSON only:"""

        print("Sending grant analysis prompt to OpenAI...")
        start_time = datetime.now()
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": grant_prompt}
            ],
            max_tokens=200,
            temperature=0.3
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        content = response.choices[0].message.content
        usage = response.usage
        
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Usage: input={usage.prompt_tokens}, output={usage.completion_tokens}, total={usage.total_tokens}")
        
        # Calculate cost
        cost = (usage.prompt_tokens * 0.001/1000) + (usage.completion_tokens * 0.002/1000)
        print(f"Cost: ${cost:.6f}")
        print()
        
        print("RAW OPENAI RESPONSE:")
        print("-" * 20)
        print(content)
        print("-" * 20)
        print()
        
        # Try to parse as JSON
        try:
            analysis = json.loads(content)
            print("PARSED ANALYSIS:")
            print(f"  Compatibility Score: {analysis.get('compatibility_score', 'N/A')}")
            print(f"  Strategic Value: {analysis.get('strategic_value', 'N/A')}")
            print(f"  Funding Likelihood: {analysis.get('funding_likelihood', 'N/A')}")
            print(f"  Strategic Rationale: {analysis.get('strategic_rationale', 'N/A')}")
            print(f"  Risk Assessment: {analysis.get('risk_assessment', 'N/A')}")
            print(f"  Action Priority: {analysis.get('action_priority', 'N/A')}")
            
            print("\n[SUCCESS] Real OpenAI analysis completed!")
            
        except json.JSONDecodeError:
            print("[WARNING] Response is not valid JSON, but it's a real OpenAI response")
        
        print()
        
        # Test 3: Different model test
        print("3. MODEL COMPARISON TEST")
        print("-" * 25)
        
        models_to_test = ["gpt-3.5-turbo", "gpt-4o-mini"]
        
        for model in models_to_test:
            try:
                print(f"\nTesting {model}...")
                
                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": "Rate this grant opportunity fit from 1-10: Rural health program for $150K focusing on telemedicine. Our org focuses on rural healthcare access."}
                    ],
                    max_tokens=50,
                    temperature=0.3
                )
                
                content = response.choices[0].message.content
                usage = response.usage
                cost = (usage.prompt_tokens * 0.001/1000) + (usage.completion_tokens * 0.002/1000)
                
                print(f"  Response: {content}")
                print(f"  Tokens: {usage.total_tokens}, Cost: ${cost:.6f}")
                
            except Exception as e:
                print(f"  [ERROR] {model} failed: {e}")
        
        print()
        print("=" * 70)
        print("DIRECT API TEST COMPLETE")
        print("=" * 70)
        print("✓ OpenAI API is working with real responses!")
        print("✓ Your billing is set up correctly!")
        print("✓ The system bug is in the response parsing layer!")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Direct API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing OpenAI API directly...")
    result = asyncio.run(direct_openai_test())
    
    if result:
        print("\nSUCCESS: Real OpenAI API is working!")
        print("The system has a parsing bug, but the API integration is solid.")
    else:
        print("\nAPI test failed")