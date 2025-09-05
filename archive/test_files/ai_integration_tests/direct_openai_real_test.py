#!/usr/bin/env python3
"""
Direct OpenAI API Test - Real API Calls Only
No system processors, no simulation - direct API calls with real data
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load environment
load_dotenv()

def make_real_openai_call():
    """Make direct OpenAI API call with real Heroes Bridge and Fauquier Health Foundation data"""
    
    print("=" * 80)
    print("DIRECT OPENAI API CALL - REAL DATA ANALYSIS")
    print("=" * 80)
    
    # Verify API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")
    
    print(f"SUCCESS: API Key loaded: {api_key[:15]}...{api_key[-10:]}")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Load real data
    print("\nLoading real organization data...")
    
    # Load Fauquier Health Foundation (Opportunity)
    fauquier_file = Path('data/source_data/nonprofits/300219424/propublica.json')
    with open(fauquier_file, 'r') as f:
        fauquier_data = json.load(f)
        
    # Load Heroes Bridge (Profile)  
    heroes_file = Path('data/source_data/nonprofits/812827604/propublica.json')
    with open(heroes_file, 'r') as f:
        heroes_data = json.load(f)
        
    # Extract organization info
    fauquier_org = fauquier_data.get('organization', {})
    heroes_org = heroes_data.get('organization', {})
    
    # Get latest financial data
    fauquier_filings = fauquier_data.get('filings_with_data', [])
    heroes_filings = heroes_data.get('filings_with_data', [])
    
    fauquier_latest = fauquier_filings[0] if fauquier_filings else {}
    heroes_latest = heroes_filings[0] if heroes_filings else {}
    
    print(f"SUCCESS: Fauquier Health Foundation: ${fauquier_latest.get('totrevenue', 0):,} revenue")
    print(f"SUCCESS: Heroes Bridge: ${heroes_latest.get('totrevenue', 0):,} revenue")
    print(f"SUCCESS: Both located in: {heroes_org.get('city')}, {heroes_org.get('state')}")
    
    # Create analysis prompt with real data
    prompt = f"""
    Analyze this real grant opportunity scenario:
    
    FUNDING SOURCE (Opportunity):
    - Organization: {fauquier_org.get('name')}
    - EIN: {fauquier_org.get('ein')}
    - Type: Health Foundation
    - Annual Revenue: ${fauquier_latest.get('totrevenue', 0):,}
    - Location: {fauquier_org.get('city')}, {fauquier_org.get('state')}
    - NTEE Code: {fauquier_org.get('ntee_code')}
    
    APPLYING ORGANIZATION (Profile):
    - Organization: {heroes_org.get('name')}
    - EIN: {heroes_org.get('ein')}
    - Type: Veteran Services Organization
    - Annual Revenue: ${heroes_latest.get('totrevenue', 0):,}
    - Location: {heroes_org.get('city')}, {heroes_org.get('state')}
    - NTEE Code: {heroes_org.get('ntee_code')}
    
    Please provide a strategic analysis including:
    1. Strategic alignment score (0-1.0)
    2. Geographic advantage assessment
    3. Financial compatibility analysis
    4. Success probability estimate
    5. Key recommendations
    6. Risk factors to consider
    
    Base your analysis on the real financial data and organizational characteristics provided.
    """
    
    print(f"\nMaking real OpenAI API call...")
    print(f"Model: gpt-4")
    print(f"Prompt length: {len(prompt)} characters")
    
    try:
        # Make the actual API call
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert grant research analyst. Provide detailed, data-driven analysis with specific numerical assessments based on the real organizational data provided."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        # Extract results
        analysis = response.choices[0].message.content
        usage = response.usage
        
        print(f"SUCCESS: API call successful!")
        print(f"Total tokens: {usage.total_tokens}")
        print(f"Prompt tokens: {usage.prompt_tokens}")
        print(f"Completion tokens: {usage.completion_tokens}")
        
        # Calculate approximate cost (GPT-4 pricing)
        prompt_cost = usage.prompt_tokens * 0.00003  # $0.03 per 1K tokens
        completion_cost = usage.completion_tokens * 0.00006  # $0.06 per 1K tokens
        total_cost = prompt_cost + completion_cost
        
        print(f"Estimated cost: ${total_cost:.4f}")
        
        print(f"\n" + "=" * 80)
        print("REAL AI ANALYSIS RESULTS")
        print("=" * 80)
        print(analysis)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_data = {
            'timestamp': timestamp,
            'api_call_type': 'DIRECT_OPENAI_REAL',
            'model_used': 'gpt-4',
            'organizations': {
                'funding_source': {
                    'name': fauquier_org.get('name'),
                    'ein': fauquier_org.get('ein'),
                    'revenue': fauquier_latest.get('totrevenue', 0),
                    'location': f"{fauquier_org.get('city')}, {fauquier_org.get('state')}"
                },
                'applicant': {
                    'name': heroes_org.get('name'),
                    'ein': heroes_org.get('ein'),
                    'revenue': heroes_latest.get('totrevenue', 0),
                    'location': f"{heroes_org.get('city')}, {heroes_org.get('state')}"
                }
            },
            'api_usage': {
                'total_tokens': usage.total_tokens,
                'prompt_tokens': usage.prompt_tokens,
                'completion_tokens': usage.completion_tokens,
                'estimated_cost_usd': total_cost,
                'model': 'gpt-4'
            },
            'ai_analysis': analysis,
            'simulation_mode': False
        }
        
        output_file = f'direct_openai_real_test_{timestamp}.json'
        with open(output_file, 'w') as f:
            json.dump(result_data, f, indent=2, default=str)
        
        print(f"\nResults saved to: {output_file}")
        print(f"\nSUCCESS: Real OpenAI API call completed - Check your OpenAI dashboard!")
        
        return result_data
        
    except Exception as e:
        print(f"ERROR: API call failed: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        result = make_real_openai_call()
        print(f"\nREAL API CALL COMPLETED SUCCESSFULLY")
        print(f"Tokens used: {result['api_usage']['total_tokens']}")
        print(f"Cost: ${result['api_usage']['estimated_cost_usd']:.4f}")
    except Exception as e:
        print(f"\nFAILED: {str(e)}")
        import traceback
        traceback.print_exc()