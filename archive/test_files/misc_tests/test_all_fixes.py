#!/usr/bin/env python3
"""
Test All AI-Lite Processor Fixes
Comprehensive test to verify all fixes work with real API calls
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
logging.basicConfig(level=logging.INFO)

async def test_all_fixes():
    """Test all AI-lite processor fixes with real API calls"""
    
    print("=" * 90)
    print("COMPREHENSIVE AI-LITE FIXES TEST - ALL THREE PROCESSORS")
    print("=" * 90)
    print()
    
    results = {}
    
    # Test 1: AI-Lite Scorer (with fixed JSON parsing)
    print("1. AI-LITE SCORER - Testing Fixed JSON Parsing")
    print("=" * 55)
    
    try:
        from src.processors.analysis.ai_lite_scorer import (
            AILiteScorer, AILiteRequest, RequestMetadata, ProfileContext, CandidateData
        )
        
        scorer = AILiteScorer()
        
        # Create test request
        profile = ProfileContext(
            organization_name="Health Tech Innovation Center",
            mission_statement="Transforming healthcare delivery through cutting-edge technology solutions.",
            focus_areas=["health technology", "digital health", "AI in healthcare"],
            ntee_codes=["E32", "U41"],
            government_criteria=["501c3", "technology_focus"],
            keywords=["health", "technology", "AI", "innovation"],
            geographic_scope="National"
        )
        
        candidate = CandidateData(
            opportunity_id="fix_test_001",
            organization_name="NIH AI in Healthcare Grant",
            source_type="government",
            description="National Institutes of Health grant program supporting the development and implementation of artificial intelligence technologies in healthcare settings to improve patient outcomes and reduce costs.",
            funding_amount=400000,
            application_deadline="2024-12-01",
            geographic_location="National",
            current_score=0.88
        )
        
        request = AILiteRequest(
            request_metadata=RequestMetadata(
                batch_id=f"fix_test_scorer_{datetime.now().strftime('%H%M%S')}",
                profile_id="fix_test_profile",
                analysis_type="compatibility_scoring",
                model_preference="gpt-3.5-turbo",  # Use reliable model first
                cost_limit=0.01,
                priority="standard"
            ),
            profile_context=profile,
            candidates=[candidate]
        )
        
        print(f"Testing with profile: {profile.organization_name}")
        print(f"Opportunity: {candidate.organization_name} (${candidate.funding_amount:,})")
        print(f"Model: {request.request_metadata.model_preference}")
        print()
        
        print("Executing AI-Lite Scorer with fixes...")
        start_time = datetime.now()
        result = await scorer.execute(request)
        end_time = datetime.now()
        
        analysis = list(result.candidate_analysis.values())[0]
        
        print("RESULTS:")
        print(f"  Processing time: {(end_time - start_time).total_seconds():.2f}s")
        print(f"  Model used: {result.batch_results.model_used}")
        print(f"  Total cost: ${result.batch_results.total_cost:.6f}")
        print(f"  Compatibility score: {analysis.compatibility_score:.3f}")
        print(f"  Confidence level: {analysis.confidence_level:.3f}")
        print(f"  Strategic rationale: {analysis.strategic_rationale}")
        
        status = "REAL API" if analysis.confidence_level > 0.5 else "SIMULATION"
        print(f"  STATUS: {status}")
        
        results["scorer"] = {
            "status": "success",
            "api_status": status,
            "confidence": analysis.confidence_level,
            "cost": result.batch_results.total_cost
        }
        
    except Exception as e:
        print(f"[ERROR] AI-Lite Scorer failed: {e}")
        results["scorer"] = {"status": "failed", "error": str(e)}
    
    print("\\n" + "=" * 90 + "\\n")
    
    # Test 2: AI-Lite Validator (with fixed response handling + GPT-5 compatibility)
    print("2. AI-LITE VALIDATOR - Testing Fixed Response Handling + GPT-5")
    print("=" * 65)
    
    try:
        from src.processors.analysis.ai_lite_validator import (
            AILiteValidator, ValidationRequest
        )
        
        validator = AILiteValidator()
        
        validation_request = ValidationRequest(
            batch_id=f"fix_test_validator_{datetime.now().strftime('%H%M%S')}",
            profile_context={
                "organization_name": "Health Tech Innovation Center",
                "mission_statement": "Transforming healthcare through technology",
                "focus_areas": ["health technology", "AI in healthcare"]
            },
            candidates=[{
                "opportunity_id": "fix_test_validation_001",
                "organization_name": "CDC Health Innovation Challenge",
                "source_type": "government",
                "description": "Centers for Disease Control innovation challenge for health technology solutions",
                "funding_amount": 150000,
                "website_url": "https://cdc.gov/innovation"
            }],
            analysis_priority="standard"
        )
        
        print(f"Testing validator with model: {validator.model}")
        print(f"Opportunity: CDC Health Innovation Challenge ($150,000)")
        print()
        
        print("Executing AI-Lite Validator with fixes...")
        start_time = datetime.now()
        result = await validator.execute(validation_request)
        end_time = datetime.now()
        
        validation = list(result.validations.values())[0]
        
        print("RESULTS:")
        print(f"  Processing time: {(end_time - start_time).total_seconds():.2f}s")
        print(f"  Model used: {result.batch_results.model_used}")
        print(f"  Total cost: ${result.batch_results.total_cost:.6f}")
        print(f"  Validation result: {validation.validation_result}")
        print(f"  Eligibility status: {validation.eligibility_status}")
        print(f"  Confidence score: {validation.confidence_level:.3f}")
        print(f"  Discovery track: {validation.discovery_track}")
        print(f"  Quick assessment: {validation.quick_assessment}")
        
        status = "REAL API" if validation.confidence_level > 0.5 else "SIMULATION"
        print(f"  STATUS: {status}")
        
        results["validator"] = {
            "status": "success",
            "api_status": status,
            "confidence": validation.confidence_level,
            "cost": result.batch_results.total_cost
        }
        
    except Exception as e:
        print(f"[ERROR] AI-Lite Validator failed: {e}")
        import traceback
        traceback.print_exc()
        results["validator"] = {"status": "failed", "error": str(e)}
    
    print("\\n" + "=" * 90 + "\\n")
    
    # Test 3: AI-Lite Strategic Scorer (with all fixes)
    print("3. AI-LITE STRATEGIC SCORER - Testing All Fixes")
    print("=" * 50)
    
    try:
        from src.processors.analysis.ai_lite_strategic_scorer import (
            AILiteStrategicScorer, StrategicScoringRequest
        )
        
        strategic = AILiteStrategicScorer()
        
        strategic_request = StrategicScoringRequest(
            batch_id=f"fix_test_strategic_{datetime.now().strftime('%H%M%S')}",
            profile_context={
                "organization_name": "Health Tech Innovation Center",
                "mission_statement": "Transforming healthcare through technology",
                "focus_areas": ["health technology", "AI in healthcare"],
                "strategic_priorities": ["healthcare innovation", "technology adoption", "patient outcomes"]
            },
            validated_candidates=[{
                "opportunity_id": "fix_test_strategic_001",
                "organization_name": "DARPA Biological Technologies Office Grant",
                "source_type": "government",
                "description": "DARPA strategic funding for revolutionary biological technologies with healthcare applications",
                "funding_amount": 1000000,
                "strategic_context": "High-impact transformative healthcare technology initiative"
            }],
            validation_results={},
            analysis_priority="high"
        )
        
        print(f"Testing strategic scorer with model: {strategic.model}")
        print(f"Opportunity: DARPA Bio Tech Grant ($1,000,000)")
        print()
        
        print("Executing AI-Lite Strategic Scorer with fixes...")
        start_time = datetime.now()
        result = await strategic.execute(strategic_request)
        end_time = datetime.now()
        
        analysis = list(result.strategic_analyses.values())[0]
        
        print("RESULTS:")
        print(f"  Processing time: {(end_time - start_time).total_seconds():.2f}s")
        print(f"  Model used: {result.batch_results.model_used}")
        print(f"  Total cost: ${result.batch_results.total_cost:.6f}")
        print(f"  Strategic score: {analysis.strategic_score:.3f}")
        print(f"  Strategic value: {analysis.strategic_value}")
        print(f"  Alignment score: {analysis.alignment_score:.3f}")
        print(f"  Competitive position: {analysis.competitive_position}")
        print(f"  Priority ranking: {analysis.priority_ranking}")
        print(f"  Strategic rationale: {analysis.strategic_rationale}")
        
        status = "REAL API" if analysis.confidence_level > 0.5 else "SIMULATION"
        print(f"  STATUS: {status}")
        
        results["strategic"] = {
            "status": "success",
            "api_status": status,
            "confidence": analysis.confidence_level,
            "cost": result.batch_results.total_cost
        }
        
    except Exception as e:
        print(f"[ERROR] AI-Lite Strategic Scorer failed: {e}")
        import traceback
        traceback.print_exc()
        results["strategic"] = {"status": "failed", "error": str(e)}
    
    # Final Summary
    print("\\n" + "=" * 90)
    print("FIXES TEST SUMMARY")
    print("=" * 90)
    
    successful = sum(1 for r in results.values() if r.get("status") == "success")
    real_api_calls = sum(1 for r in results.values() if r.get("api_status") == "REAL API")
    total_cost = sum(r.get("cost", 0) for r in results.values() if r.get("status") == "success")
    
    print(f"\\nProcessors working: {successful}/3")
    print(f"Real API calls: {real_api_calls}/{successful}")
    print(f"Total cost: ${total_cost:.6f}")
    
    print("\\nDetailed Results:")
    for name, result in results.items():
        if result["status"] == "success":
            print(f"  {name.upper()}: ✅ {result['api_status']} (confidence: {result['confidence']:.3f})")
        else:
            print(f"  {name.upper()}: ❌ FAILED - {result['error']}")
    
    if successful == 3:
        print("\\n🎉 ALL FIXES SUCCESSFUL!")
    elif successful > 0:
        print(f"\\n✅ {successful}/3 processors working after fixes")
    else:
        print("\\n❌ All processors still have issues")
        
    print("\\nCheck your OpenAI dashboard for API usage!")
    
    return results

if __name__ == "__main__":
    print("Testing all AI-lite processor fixes...")
    result = asyncio.run(test_all_fixes())
    
    successful = sum(1 for r in result.values() if r.get("status") == "success")
    print(f"\\nFinal status: {successful}/3 processors working")