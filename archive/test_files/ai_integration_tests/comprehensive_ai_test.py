#!/usr/bin/env python3
"""
Comprehensive AI API Test - Fixed Service Layer
Shows exactly what's sent to OpenAI and what's received back
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

async def comprehensive_ai_test():
    """Test AI service with fixed parsing - show complete request/response flow"""
    
    print("=" * 80)
    print("COMPREHENSIVE AI API TEST - FIXED SERVICE LAYER")
    print("=" * 80)
    print()
    
    try:
        from src.core.openai_service import OpenAIService
        from src.processors.analysis.ai_lite_scorer import (
            AILiteScorer, AILiteRequest, RequestMetadata, ProfileContext, CandidateData
        )
        
        # Initialize service with API key
        api_key = os.getenv('OPENAI_API_KEY')
        service = OpenAIService(api_key=api_key)
        
        if service.client is None:
            print("[ERROR] OpenAI service client not initialized")
            return False
            
        print("1. OPENAI SERVICE TEST (Fixed Parsing)")
        print("-" * 45)
        
        # Test the fixed service directly
        test_messages = [
            {"role": "user", "content": "Respond with exactly: 'SERVICE_LAYER_FIXED'"}
        ]
        
        print("Request to OpenAI Service:")
        print(f"  Model: gpt-3.5-turbo")
        print(f"  Messages: {test_messages}")
        print(f"  Max tokens: 10")
        print()
        
        print("Making service call...")
        response = await service.create_completion(
            model="gpt-3.5-turbo",
            messages=test_messages,
            max_tokens=10,
            temperature=0
        )
        
        print("Service Response:")
        print(f"  Content: '{response.content}'")
        print(f"  Model: {response.model}")
        print(f"  Usage: {response.usage}")
        print(f"  Cost: ${response.cost_estimate:.6f}")
        print(f"  Finish reason: {response.finish_reason}")
        
        if "SERVICE_LAYER_FIXED" in response.content:
            print("[SUCCESS] Service layer is working with real API!")
            service_fixed = True
        else:
            print("[WARNING] Unexpected response from service")
            service_fixed = False
            
        print()
        
        if not service_fixed:
            return False
            
        # Test AI-Lite Processor with real API
        print("2. AI-LITE PROCESSOR TEST (Real API)")
        print("-" * 40)
        
        # Create test data
        profile_context = ProfileContext(
            organization_name="Healthcare Innovation Foundation",
            mission_statement="Advancing healthcare access through technology and community partnerships in underserved areas.",
            focus_areas=["healthcare technology", "rural health", "primary care access", "telehealth"],
            ntee_codes=["E32", "E42"],
            government_criteria=["501c3", "healthcare_focus"],
            keywords=["health", "technology", "rural", "access", "innovation"],
            geographic_scope="National with focus on rural areas"
        )
        
        test_candidate = CandidateData(
            opportunity_id="real_api_test_hrsa_001",
            organization_name="HRSA Telehealth Network Grant Program", 
            source_type="government",
            description="Federal grant supporting rural healthcare organizations in implementing comprehensive telehealth programs to improve access to specialty care, mental health services, and chronic disease management in underserved rural communities.",
            funding_amount=175000,
            application_deadline="2024-09-30",
            geographic_location="Rural areas nationwide",
            current_score=0.81
        )
        
        request_metadata = RequestMetadata(
            batch_id=f"comprehensive_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            profile_id="profile_comprehensive_test",
            analysis_type="compatibility_scoring_real_api",
            model_preference="gpt-3.5-turbo",
            cost_limit=0.02,
            priority="high"
        )
        
        ai_request = AILiteRequest(
            request_metadata=request_metadata,
            profile_context=profile_context,
            candidates=[test_candidate]
        )
        
        # Initialize processor
        processor = AILiteScorer()
        
        print("AI-Lite Request Data:")
        print(f"  Batch ID: {request_metadata.batch_id}")
        print(f"  Profile: {profile_context.organization_name}")
        print(f"  Mission: {profile_context.mission_statement[:80]}...")
        print(f"  Focus Areas: {', '.join(profile_context.focus_areas)}")
        print(f"  Candidate: {test_candidate.organization_name}")
        print(f"  Funding: ${test_candidate.funding_amount:,}")
        print(f"  Description: {test_candidate.description[:100]}...")
        print()
        
        # Generate the prompt that will be sent
        prompt = processor._create_enhanced_batch_prompt(ai_request)
        
        print("3. GENERATED PROMPT TO OPENAI")
        print("-" * 35)
        print("Prompt (first 500 chars):")
        print("-" * 25)
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        print("-" * 25)
        print(f"Full prompt length: {len(prompt)} characters")
        print(f"Estimated tokens: {len(prompt) // 4}")
        print()
        
        # Execute the processor
        print("4. EXECUTING AI-LITE PROCESSOR")
        print("-" * 35)
        print("Making AI-Lite analysis request...")
        
        start_time = datetime.now()
        result = await processor.execute(ai_request)
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"Processing completed in {processing_time:.2f} seconds")
        print()
        
        print("5. ANALYSIS RESULTS")
        print("-" * 20)
        
        batch_results = result.batch_results
        print("Batch Information:")
        print(f"  Batch ID: {batch_results.batch_id}")
        print(f"  Model Used: {batch_results.model_used}")
        print(f"  Processing Time: {batch_results.processing_time:.2f}s")
        print(f"  Total Cost: ${batch_results.total_cost:.6f}")
        print(f"  Candidates Processed: {batch_results.processed_count}")
        print()
        
        # Check if this is real API or simulation
        analysis = list(result.candidate_analysis.values())[0]
        
        if analysis.confidence_level == 0.1 and "not included" in analysis.strategic_rationale:
            print("[SIMULATION] Results appear to be from simulation fallback")
            api_status = "SIMULATION"
        else:
            print("[REAL API] Results appear to be from actual OpenAI analysis")
            api_status = "REAL API"
            
        print()
        print("Detailed Analysis Results:")
        print(f"  Opportunity ID: {test_candidate.opportunity_id}")
        print(f"  Compatibility Score: {analysis.compatibility_score:.3f}")
        print(f"  Strategic Value: {analysis.strategic_value}")
        print(f"  Funding Likelihood: {analysis.funding_likelihood:.3f}")
        print(f"  Priority Rank: {analysis.priority_rank}")
        print(f"  Action Priority: {analysis.action_priority}")
        print(f"  Confidence Level: {analysis.confidence_level:.3f}")
        print(f"  Risk Assessment: {', '.join(analysis.risk_assessment)}")
        print(f"  Strategic Rationale: {analysis.strategic_rationale}")
        print()
        
        if analysis.research_mode_enabled and analysis.research_report:
            print("Research Mode Results:")
            print(f"  Executive Summary: {analysis.research_report.executive_summary[:100]}...")
            print()
        
        # Test a simple direct service call to see raw response
        print("6. RAW API RESPONSE SAMPLE")
        print("-" * 30)
        
        simple_prompt = f"""Analyze this grant opportunity for {profile_context.organization_name}:

Grant: {test_candidate.organization_name}
Amount: ${test_candidate.funding_amount:,}
Description: {test_candidate.description[:200]}

Provide compatibility score 0.0-1.0 and brief rationale."""

        print("Sending simplified prompt...")
        raw_response = await service.create_completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": simple_prompt}],
            max_tokens=150,
            temperature=0.3
        )
        
        print("Raw OpenAI Response:")
        print(f"  Content: {raw_response.content}")
        print(f"  Tokens used: {raw_response.usage['total_tokens']}")
        print(f"  Cost: ${raw_response.cost_estimate:.6f}")
        print()
        
        print("=" * 80)
        print("COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        print(f"Service Layer: {'FIXED - Real API calls working' if service_fixed else 'Still has issues'}")
        print(f"AI-Lite Processor: {api_status}")
        print(f"Total Processing Time: {processing_time:.2f} seconds")
        print(f"Total Cost: ${batch_results.total_cost + raw_response.cost_estimate:.6f}")
        print(f"Prompt Length: {len(prompt)} characters")
        print(f"Analysis Quality: {'High-confidence real AI analysis' if api_status == 'REAL API' else 'Simulation fallback'}")
        
        return service_fixed and api_status == "REAL API"
        
    except Exception as e:
        print(f"[ERROR] Comprehensive test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting comprehensive AI API test with fixed service layer...")
    result = asyncio.run(comprehensive_ai_test())
    
    if result:
        print("\nSUCCESS: Complete AI integration working with real OpenAI API!")
    else:
        print("\nTest completed - check results above for details")