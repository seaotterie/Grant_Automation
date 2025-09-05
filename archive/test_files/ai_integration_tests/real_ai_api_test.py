#!/usr/bin/env python3
"""
REAL AI API Test - No Simulation Mode
Tests actual OpenAI API calls and clearly identifies simulation fallbacks

This script:
1. Forces real API calls (no simulation)
2. Shows all AI-lite processor types
3. Tracks actual API usage
4. Clearly marks if simulation is used
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any
import logging

# Add project root to path
sys.path.append('.')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_real_openai_api():
    """Test with REAL OpenAI API calls - no simulation"""
    
    print("=" * 70)
    print("REAL OPENAI API TEST - NO SIMULATION")
    print("=" * 70)
    print()
    
    # First, let's check API key availability
    print("1. API KEY STATUS CHECK")
    print("-" * 30)
    
    # Check environment variable
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print(f"[OK] Environment OPENAI_API_KEY found: {openai_key[:12]}...{openai_key[-8:]}")
        print(f"     Key length: {len(openai_key)} characters")
    else:
        print("[ERROR] No OPENAI_API_KEY environment variable found")
        return False
    
    # Test OpenAI service directly
    try:
        from src.core.openai_service import OpenAIService
        
        service = OpenAIService(api_key=openai_key)
        
        if service.client is None:
            print("[ERROR] OpenAI service failed to initialize client")
            return False
        else:
            print("[OK] OpenAI service client initialized successfully")
        
        # Test direct API call
        print("\n2. DIRECT API TEST")
        print("-" * 20)
        
        test_messages = [
            {"role": "user", "content": "Respond with exactly: 'API_TEST_SUCCESS'"}
        ]
        
        print("Making direct OpenAI API call...")
        start_time = datetime.now()
        
        response = await service.create_completion(
            model="gpt-3.5-turbo",
            messages=test_messages,
            max_tokens=10,
            temperature=0
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"Response content: '{response.content}'")
        print(f"Model used: {response.model}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Usage: {response.usage}")
        print(f"Cost estimate: ${response.cost_estimate:.6f}")
        
        if "API_TEST_SUCCESS" in response.content:
            print("[SUCCESS] Real API call confirmed!")
            api_working = True
        else:
            print("[WARNING] Unexpected response - might be simulation")
            api_working = False
            
    except Exception as e:
        print(f"[ERROR] Direct API test failed: {e}")
        api_working = False
    
    print()
    
    # Now test the different AI-lite processors
    print("3. AI-LITE PROCESSOR TYPES")
    print("-" * 30)
    
    processor_tests = []
    
    # Test 1: Standard AI-Lite Scorer
    try:
        from src.processors.analysis.ai_lite_scorer import AILiteScorer, AILiteRequest, RequestMetadata, ProfileContext, CandidateData
        
        print("[1] ai_lite_scorer.py - Standard compatibility scoring")
        scorer = AILiteScorer()
        print(f"    Purpose: {scorer.metadata.description}")
        print(f"    Model: {scorer.model}")
        print(f"    Cost per candidate: ${scorer.estimated_cost_per_candidate}")
        
        processor_tests.append(("ai_lite_scorer", scorer, "Standard compatibility analysis"))
        
    except Exception as e:
        print(f"[1] ai_lite_scorer.py - FAILED TO LOAD: {e}")
    
    # Test 2: AI-Lite Validator
    try:
        from src.processors.analysis.ai_lite_validator import AILiteValidator
        
        print("[2] ai_lite_validator.py - Data validation and verification")
        validator = AILiteValidator()
        print(f"    Purpose: {validator.metadata.description}")
        print(f"    Model: {validator.model}")
        print(f"    Cost per candidate: ${validator.estimated_cost_per_candidate}")
        
        processor_tests.append(("ai_lite_validator", validator, "Data validation"))
        
    except Exception as e:
        print(f"[2] ai_lite_validator.py - FAILED TO LOAD: {e}")
    
    # Test 3: AI-Lite Strategic Scorer
    try:
        from src.processors.analysis.ai_lite_strategic_scorer import AILiteStrategicScorer
        
        print("[3] ai_lite_strategic_scorer.py - Strategic analysis and scoring")
        strategic = AILiteStrategicScorer()
        print(f"    Purpose: {strategic.metadata.description}")
        print(f"    Model: {strategic.model}")
        print(f"    Cost per candidate: ${strategic.estimated_cost_per_candidate}")
        
        processor_tests.append(("ai_lite_strategic", strategic, "Strategic analysis"))
        
    except Exception as e:
        print(f"[3] ai_lite_strategic_scorer.py - FAILED TO LOAD: {e}")
    
    print()
    
    if not api_working:
        print("[WARNING] Since direct API test failed, all processor tests will likely use simulation")
        print("This means your API key might not be properly configured with the processors")
        print()
    
    # Test each processor with a simple candidate
    print("4. PROCESSOR API TESTS")
    print("-" * 25)
    
    # Create test data
    test_profile = ProfileContext(
        organization_name="Test Health Foundation",
        mission_statement="Improving healthcare access in rural communities",
        focus_areas=["healthcare", "rural medicine"],
        ntee_codes=["E32"],
        government_criteria=["501c3"],
        keywords=["health", "rural"],
        geographic_scope="Virginia"
    )
    
    test_candidate = CandidateData(
        opportunity_id="real_api_test_001",
        organization_name="Rural Health Grant Program",
        source_type="government",
        description="Federal grant supporting rural health initiatives with focus on primary care access.",
        funding_amount=100000,
        application_deadline="2024-12-31",
        geographic_location="National",
        current_score=0.75
    )
    
    for processor_name, processor, description in processor_tests:
        print(f"\nTesting {processor_name} ({description})...")
        
        try:
            # Force real API usage check
            if hasattr(processor, '_call_openai_api'):
                print("  Checking for simulation code...")
                # Check if it has hardcoded simulation responses
                import inspect
                source = inspect.getsource(processor._call_openai_api)
                if "simulated_response" in source or "await asyncio.sleep" in source:
                    print("  [WARNING] This processor contains simulation code!")
                    print("  [INFO] Will test anyway to see if it uses real API...")
            
            # Create appropriate request based on processor type
            if processor_name == "ai_lite_scorer":
                request_metadata = RequestMetadata(
                    batch_id=f"real_test_{processor_name}_{datetime.now().strftime('%H%M%S')}",
                    profile_id="profile_real_test",
                    analysis_type="compatibility_scoring",
                    model_preference="gpt-3.5-turbo",
                    cost_limit=0.01,
                    priority="high"  # Force real API
                )
                
                request = AILiteRequest(
                    request_metadata=request_metadata,
                    profile_context=test_profile,
                    candidates=[test_candidate]
                )
                
                print("  Making AI-Lite Scorer API call...")
                start_time = datetime.now()
                result = await processor.execute(request)
                end_time = datetime.now()
                
                print(f"  Processing time: {(end_time - start_time).total_seconds():.2f}s")
                print(f"  Batch results: {result.batch_results.model_used}")
                print(f"  Total cost: ${result.batch_results.total_cost:.6f}")
                
                # Check if results look real or simulated
                analysis = list(result.candidate_analysis.values())[0]
                if analysis.confidence_level == 0.1 and "not included in" in analysis.strategic_rationale:
                    print("  [SIMULATION] Results appear to be from fallback simulation")
                else:
                    print("  [REAL API] Results appear to be from actual OpenAI API")
                    
                print(f"  Compatibility Score: {analysis.compatibility_score}")
                print(f"  Strategic Rationale: {analysis.strategic_rationale}")
                
            else:
                print(f"  [SKIP] {processor_name} - Need to implement test for this processor type")
                
        except Exception as e:
            print(f"  [ERROR] {processor_name} test failed: {e}")
    
    print()
    print("=" * 70)
    print("REAL API TEST SUMMARY")
    print("=" * 70)
    
    if api_working:
        print("[SUCCESS] OpenAI API is working with real calls")
        print("API usage should appear in your OpenAI dashboard")
    else:
        print("[WARNING] API calls appear to be using simulation")
        print("Check your API key configuration")
    
    print(f"Found {len(processor_tests)} AI-lite processors:")
    for name, _, desc in processor_tests:
        print(f"  - {name}: {desc}")
    
    return api_working

if __name__ == "__main__":
    print("Starting REAL OpenAI API Test (No Simulation)...")
    print("This will make actual API calls and cost real money if API key is configured correctly")
    print()
    
    # Run the test
    result = asyncio.run(test_real_openai_api())
    
    if result:
        print("\n[SUCCESS] Real API integration confirmed!")
        print("Check your OpenAI API usage dashboard to see the actual calls.")
    else:
        print("\n[FAILED] API integration using simulation or not working properly.")
        print("Your OpenAI API key may need proper configuration.")