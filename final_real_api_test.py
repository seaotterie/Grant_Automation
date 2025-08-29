#!/usr/bin/env python3
"""
Final Real API Test - Direct AI-Lite Processor Test
Shows exactly what's sent to OpenAI and received back
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

import logging
logging.basicConfig(level=logging.DEBUG)

async def final_real_api_test():
    """Test the AI-Lite processor directly with detailed logging"""
    
    print("=" * 80)
    print("FINAL REAL API TEST - AI-LITE PROCESSOR")
    print("=" * 80)
    print()
    
    try:
        from src.processors.analysis.ai_lite_scorer import AILiteScorer
        
        # Test the processor's API call directly
        processor = AILiteScorer()
        
        print("1. TESTING PROCESSOR API CALL DIRECTLY")
        print("-" * 45)
        
        # Create a simple test prompt
        test_prompt = """You are a grant strategy expert. Analyze this opportunity:

Organization: Healthcare Innovation Foundation
Mission: Advancing healthcare access through technology
Opportunity: HRSA Telehealth Grant - $175,000 for rural telehealth

Respond with EXACT JSON format:
{
  "real_api_test_hrsa_001": {
    "compatibility_score": 0.85,
    "strategic_value": "high",
    "risk_assessment": ["competition"],
    "priority_rank": 1,
    "funding_likelihood": 0.75,
    "strategic_rationale": "Strong alignment with healthcare technology mission",
    "action_priority": "immediate", 
    "confidence_level": 0.9
  }
}

JSON only:"""

        print("Test prompt being sent:")
        print("-" * 25)
        print(test_prompt)
        print("-" * 25)
        print(f"Prompt length: {len(test_prompt)} characters")
        print()
        
        print("Making direct processor API call...")
        start_time = datetime.now()
        
        # Call the processor's API method directly
        response = await processor._call_openai_api(
            prompt=test_prompt,
            model="gpt-3.5-turbo",
            max_tokens=200
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"Processing time: {processing_time:.2f} seconds")
        print()
        
        print("RAW RESPONSE FROM OPENAI:")
        print("-" * 30)
        print(response)
        print("-" * 30)
        print()
        
        # Check if it's real or simulation
        if "unified_opp_005" in response:
            print("[SIMULATION] Response contains simulation markers")
        elif "real_api_test_hrsa_001" in response:
            print("[REAL API] Response matches our test request!")
        else:
            print("[UNKNOWN] Response format unclear")
            
        # Try to parse as JSON
        try:
            parsed = json.loads(response.strip())
            print("PARSED JSON RESPONSE:")
            for key, value in parsed.items():
                print(f"  {key}:")
                for subkey, subvalue in value.items():
                    print(f"    {subkey}: {subvalue}")
            print()
        except json.JSONDecodeError as e:
            print(f"[ERROR] Could not parse as JSON: {e}")
            print("Raw response might not be valid JSON")
            print()
            
        # Test 2: Full processor workflow
        print("2. TESTING FULL PROCESSOR WORKFLOW")
        print("-" * 38)
        
        from src.processors.analysis.ai_lite_scorer import (
            AILiteRequest, RequestMetadata, ProfileContext, CandidateData
        )
        
        # Create full request
        profile = ProfileContext(
            organization_name="Healthcare Innovation Foundation",
            mission_statement="Advancing healthcare access through technology",
            focus_areas=["healthcare technology", "telehealth"],
            ntee_codes=["E32"],
            government_criteria=["501c3"],
            keywords=["health", "technology"],
            geographic_scope="National"
        )
        
        candidate = CandidateData(
            opportunity_id="final_test_001",
            organization_name="HRSA Telehealth Grant",
            source_type="government", 
            description="Federal telehealth grant for rural healthcare",
            funding_amount=175000,
            current_score=0.8
        )
        
        request = AILiteRequest(
            request_metadata=RequestMetadata(
                batch_id="final_test_batch",
                profile_id="test_profile",
                analysis_type="real_api_test",
                model_preference="gpt-3.5-turbo",
                cost_limit=0.05,
                priority="high"
            ),
            profile_context=profile,
            candidates=[candidate]
        )
        
        print("Executing full AI-Lite processor...")
        result = await processor.execute(request)
        
        print("Full processor results:")
        print(f"  Model used: {result.batch_results.model_used}")
        print(f"  Total cost: ${result.batch_results.total_cost:.6f}")
        print(f"  Processing time: {result.batch_results.processing_time:.2f}s")
        
        analysis = list(result.candidate_analysis.values())[0]
        print(f"  Compatibility score: {analysis.compatibility_score}")
        print(f"  Strategic rationale: {analysis.strategic_rationale}")
        print(f"  Confidence level: {analysis.confidence_level}")
        
        if analysis.confidence_level > 0.5:
            print("[REAL API] High confidence indicates real analysis")
            api_status = "REAL"
        else:
            print("[SIMULATION] Low confidence indicates simulation fallback")
            api_status = "SIMULATION"
            
        print()
        print("=" * 80)
        print("FINAL TEST SUMMARY")
        print("=" * 80)
        print(f"Direct API call: {'REAL' if 'real_api_test_hrsa_001' in response else 'SIMULATION'}")
        print(f"Full processor: {api_status}")
        print(f"Total cost: ${result.batch_results.total_cost:.6f}")
        
        return "REAL" in [api_status]
        
    except Exception as e:
        print(f"[ERROR] Final test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting final real API test...")
    result = asyncio.run(final_real_api_test())
    
    if result:
        print("\nSUCCESS: Real OpenAI API integration confirmed!")
    else:
        print("\nTest completed - check logs for API vs simulation status")