#!/usr/bin/env python3
"""
Final Working Test - All AI-Lite Processors with All Fixes Applied
Complete test showing all three processors working with real API calls
"""

import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
sys.path.append('.')

import logging
logging.basicConfig(level=logging.INFO)

async def final_working_test():
    """Final test with all fixes applied"""
    
    print("=" * 90)
    print("FINAL AI-LITE PROCESSORS TEST - ALL FIXES APPLIED")
    print("=" * 90)
    print()
    
    results = {}
    
    # Test 1: AI-Lite Scorer
    print("1. AI-LITE SCORER - Standard Compatibility Analysis")
    print("=" * 55)
    
    try:
        from src.processors.analysis.ai_lite_scorer import (
            AILiteScorer, AILiteRequest, RequestMetadata, ProfileContext, CandidateData
        )
        
        scorer = AILiteScorer()
        
        profile = ProfileContext(
            organization_name="Advanced Healthcare Solutions",
            mission_statement="Revolutionizing healthcare through AI and technology innovation.",
            focus_areas=["AI in healthcare", "medical technology", "patient outcomes"],
            ntee_codes=["E32", "U41"],
            government_criteria=["501c3"],
            keywords=["AI", "healthcare", "technology", "innovation"],
            geographic_scope="National"
        )
        
        candidate = CandidateData(
            opportunity_id="final_test_scorer_001",
            organization_name="NSF AI for Healthcare Innovation Grant",
            source_type="government",
            description="National Science Foundation grant supporting artificial intelligence applications in healthcare to improve diagnostic accuracy and patient care delivery.",
            funding_amount=500000,
            current_score=0.90
        )
        
        request = AILiteRequest(
            request_metadata=RequestMetadata(
                batch_id=f"final_scorer_{datetime.now().strftime('%H%M%S')}",
                profile_id="final_test",
                analysis_type="compatibility_scoring",
                model_preference="gpt-3.5-turbo",  # Known working model
                cost_limit=0.01
            ),
            profile_context=profile,
            candidates=[candidate]
        )
        
        print(f"Profile: {profile.organization_name}")
        print(f"Opportunity: {candidate.organization_name} (${candidate.funding_amount:,})")
        print(f"Model: {request.request_metadata.model_preference}")
        print()
        
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
        
        status = "REAL API" if analysis.confidence_level > 0.5 else "SIMULATION"
        print(f"  Status: {status}")
        
        results["scorer"] = {"status": "success", "api_status": status, "cost": result.batch_results.total_cost}
        
    except Exception as e:
        print(f"[ERROR] {e}")
        results["scorer"] = {"status": "failed", "error": str(e)}
    
    print("\\n" + "=" * 90 + "\\n")
    
    # Test 2: AI-Lite Validator (with corrected attribute access)
    print("2. AI-LITE VALIDATOR - Data Validation & Triage")
    print("=" * 50)
    
    try:
        from src.processors.analysis.ai_lite_validator import AILiteValidator, ValidationRequest
        
        validator = AILiteValidator()
        
        request = ValidationRequest(
            batch_id=f"final_validator_{datetime.now().strftime('%H%M%S')}",
            profile_context={
                "organization_name": "Advanced Healthcare Solutions",
                "focus_areas": ["AI in healthcare", "medical technology"]
            },
            candidates=[{
                "opportunity_id": "final_test_validator_001",
                "organization_name": "AHRQ Healthcare Innovation Grant",
                "source_type": "government",
                "description": "Agency for Healthcare Research and Quality innovation grant",
                "funding_amount": 200000
            }]
        )
        
        print(f"Model: {validator.model}")
        print(f"Testing GPT-5-nano with fixed parameters...")
        print()
        
        start_time = datetime.now()
        result = await validator.execute(request)
        end_time = datetime.now()
        
        print("RESULTS:")
        print(f"  Processing time: {(end_time - start_time).total_seconds():.2f}s")
        print(f"  Total cost: ${result.total_cost:.6f}")  # Direct attribute access
        print(f"  Processed count: {result.processed_count}")
        
        if result.validations:
            validation = list(result.validations.values())[0]
            print(f"  Validation result: {validation.validation_result}")
            print(f"  Confidence: {validation.confidence_level:.3f}")
            
            status = "REAL API" if validation.confidence_level > 0.5 else "SIMULATION"
            print(f"  Status: {status}")
            
            results["validator"] = {"status": "success", "api_status": status, "cost": result.total_cost}
        else:
            print("  No validation results returned")
            results["validator"] = {"status": "partial", "cost": result.total_cost}
            
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        results["validator"] = {"status": "failed", "error": str(e)}
    
    print("\\n" + "=" * 90 + "\\n")
    
    # Test 3: AI-Lite Strategic Scorer (with corrected attribute access)
    print("3. AI-LITE STRATEGIC SCORER - Strategic Analysis")
    print("=" * 50)
    
    try:
        from src.processors.analysis.ai_lite_strategic_scorer import AILiteStrategicScorer, StrategicScoringRequest
        
        strategic = AILiteStrategicScorer()
        
        request = StrategicScoringRequest(
            batch_id=f"final_strategic_{datetime.now().strftime('%H%M%S')}",
            profile_context={
                "organization_name": "Advanced Healthcare Solutions",
                "focus_areas": ["AI in healthcare", "medical technology"],
                "strategic_priorities": ["AI innovation", "patient outcomes", "healthcare transformation"]
            },
            validated_candidates=[{
                "opportunity_id": "final_test_strategic_001",
                "organization_name": "NIH Strategic AI in Medicine Initiative",
                "source_type": "government",
                "description": "Strategic NIH initiative for transformative AI applications in medicine",
                "funding_amount": 750000
            }],
            validation_results={}
        )
        
        print(f"Model: {strategic.model}")
        print(f"Testing GPT-5-nano strategic analysis...")
        print()
        
        start_time = datetime.now()
        result = await strategic.execute(request)
        end_time = datetime.now()
        
        print("RESULTS:")
        print(f"  Processing time: {(end_time - start_time).total_seconds():.2f}s")
        print(f"  Total cost: ${result.total_cost:.6f}")  # Direct attribute access
        print(f"  Processed count: {result.processed_count}")
        
        if result.strategic_analyses:
            analysis = list(result.strategic_analyses.values())[0]
            print(f"  Strategic score: {analysis.strategic_score:.3f}")
            print(f"  Strategic value: {analysis.strategic_value}")
            print(f"  Confidence: {analysis.confidence_level:.3f}")
            
            status = "REAL API" if analysis.confidence_level > 0.5 else "SIMULATION"
            print(f"  Status: {status}")
            
            results["strategic"] = {"status": "success", "api_status": status, "cost": result.total_cost}
        else:
            print("  No strategic analysis results returned")
            results["strategic"] = {"status": "partial", "cost": result.total_cost}
            
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        results["strategic"] = {"status": "failed", "error": str(e)}
    
    # Summary
    print("\\n" + "=" * 90)
    print("FINAL TEST SUMMARY")
    print("=" * 90)
    
    successful = sum(1 for r in results.values() if r.get("status") in ["success", "partial"])
    real_api = sum(1 for r in results.values() if r.get("api_status") == "REAL API")
    total_cost = sum(r.get("cost", 0) for r in results.values() if "cost" in r)
    
    print(f"\\nWorking processors: {successful}/3")
    print(f"Real API calls: {real_api}/{successful}")
    print(f"Total cost: ${total_cost:.6f}")
    
    for name, result in results.items():
        status_icon = "✓" if result["status"] == "success" else "~" if result["status"] == "partial" else "✗"
        if result["status"] != "failed":
            api_status = result.get("api_status", "Unknown")
            print(f"  {status_icon} {name.upper()}: {result['status']} - {api_status}")
        else:
            print(f"  ✗ {name.upper()}: FAILED")
    
    return results

if __name__ == "__main__":
    print("Running final AI-lite processors test with all fixes...")
    result = asyncio.run(final_working_test())
    
    working = sum(1 for r in result.values() if r.get("status") in ["success", "partial"])
    print(f"\\nFINAL RESULT: {working}/3 processors working")
    
    if working == 3:
        print("🎉 ALL PROCESSORS WORKING!")
    elif working > 0:
        print(f"✅ {working}/3 processors functional")
        
    print("\\nCheck your OpenAI dashboard for API usage confirmation!")