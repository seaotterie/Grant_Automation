#!/usr/bin/env python3
"""
Working AI-Lite Test - Real API Calls with Correct Data Models
Shows frontend requests and backend results for each working processor
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

async def test_working_ai_lite_processors():
    """Test working AI-lite processors with real API calls"""
    
    print("=" * 85)
    print("WORKING AI-LITE PROCESSORS TEST - REAL API CALLS")
    print("=" * 85)
    print()
    
    results = {}
    
    # Test 1: AI-Lite Scorer (We know this works)
    print("1. AI-LITE SCORER - Standard Compatibility Analysis")
    print("=" * 60)
    
    try:
        from src.processors.analysis.ai_lite_scorer import (
            AILiteScorer, AILiteRequest, RequestMetadata, ProfileContext, CandidateData
        )
        
        scorer = AILiteScorer()
        print(f"Purpose: {scorer.metadata.description}")
        print(f"Model: {scorer.model}")
        print(f"Cost per candidate: ${scorer.estimated_cost_per_candidate}")
        print()
        
        # Create test request
        profile = ProfileContext(
            organization_name="Rural Health Technology Institute",
            mission_statement="Advancing rural healthcare through innovative technology solutions and strategic partnerships.",
            focus_areas=["rural health", "health technology", "telehealth", "primary care"],
            ntee_codes=["E32", "U41"],
            government_criteria=["501c3", "healthcare_focus"],
            keywords=["health", "technology", "rural", "innovation"],
            geographic_scope="Rural areas nationwide"
        )
        
        candidate = CandidateData(
            opportunity_id="test_hrsa_tech_001",
            organization_name="HRSA Health Technology Innovation Grant",
            source_type="government",
            description="HRSA federal grant program supporting rural healthcare organizations in implementing cutting-edge health technology solutions including AI-powered diagnostic tools, telehealth platforms, and electronic health record systems to improve patient outcomes and reduce healthcare disparities in underserved rural communities.",
            funding_amount=300000,
            application_deadline="2024-11-30",
            geographic_location="Rural areas nationwide",
            current_score=0.85
        )
        
        request = AILiteRequest(
            request_metadata=RequestMetadata(
                batch_id=f"working_test_{datetime.now().strftime('%H%M%S')}",
                profile_id="test_profile_working",
                analysis_type="compatibility_scoring",
                model_preference="gpt-3.5-turbo",
                cost_limit=0.01,
                priority="standard"
            ),
            profile_context=profile,
            candidates=[candidate]
        )
        
        print("FRONTEND REQUEST TO AI-LITE SCORER:")
        print("-" * 40)
        print(f"  Profile: {profile.organization_name}")
        print(f"  Mission: {profile.mission_statement[:60]}...")
        print(f"  Focus Areas: {', '.join(profile.focus_areas)}")
        print(f"  Opportunity: {candidate.organization_name}")
        print(f"  Funding: ${candidate.funding_amount:,}")
        print(f"  Description: {candidate.description[:80]}...")
        print(f"  Model: {request.request_metadata.model_preference}")
        print()
        
        # Show the exact prompt being sent
        prompt = scorer._create_enhanced_batch_prompt(request)
        print("EXACT PROMPT SENT TO OPENAI:")
        print("-" * 35)
        print(prompt[:500] + "\\n..." if len(prompt) > 500 else prompt)
        print(f"\\nFull prompt length: {len(prompt)} characters")
        print(f"Estimated tokens: ~{len(prompt) // 4}")
        print()
        
        # Execute with logging
        print("Executing AI-Lite Scorer (watch for API calls)...")
        start_time = datetime.now()
        
        result = await scorer.execute(request)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print("\\nBACKEND RESULTS FROM AI-LITE SCORER:")
        print("-" * 40)
        batch_info = result.batch_results
        print(f"  Batch ID: {batch_info.batch_id}")
        print(f"  Model used: {batch_info.model_used}")
        print(f"  Processing time: {batch_info.processing_time:.2f}s")
        print(f"  Total cost: ${batch_info.total_cost:.6f}")
        print(f"  Candidates processed: {batch_info.processed_count}")
        
        # Analyze the result
        analysis = list(result.candidate_analysis.values())[0]
        print(f"\\n  ANALYSIS RESULTS:")
        print(f"  Opportunity ID: {candidate.opportunity_id}")
        print(f"  Compatibility Score: {analysis.compatibility_score:.3f}")
        print(f"  Strategic Value: {analysis.strategic_value}")
        print(f"  Funding Likelihood: {analysis.funding_likelihood:.3f}")
        print(f"  Priority Rank: {analysis.priority_rank}")
        print(f"  Action Priority: {analysis.action_priority}")
        print(f"  Confidence Level: {analysis.confidence_level:.3f}")
        print(f"  Risk Assessment: {', '.join(analysis.risk_assessment)}")
        print(f"  Strategic Rationale: {analysis.strategic_rationale}")
        
        # Determine if real API or simulation
        if analysis.confidence_level > 0.5:
            api_status = "REAL API"
            print(f"\\n  STATUS: REAL API CALL (confidence: {analysis.confidence_level:.3f})")
        else:
            api_status = "SIMULATION"
            print(f"\\n  STATUS: SIMULATION FALLBACK (confidence: {analysis.confidence_level:.3f})")
            
        results["scorer"] = {
            "name": "AI-Lite Scorer",
            "purpose": "Standard compatibility scoring",
            "cost": batch_info.total_cost,
            "processing_time": processing_time,
            "api_status": api_status,
            "confidence": analysis.confidence_level,
            "compatibility_score": analysis.compatibility_score
        }
        
    except Exception as e:
        print(f"[ERROR] AI-Lite Scorer failed: {e}")
        import traceback
        traceback.print_exc()
        results["scorer"] = {"status": "failed", "error": str(e)}
    
    print("\\n" + "=" * 85 + "\\n")
    
    # Test 2: AI-Lite Validator (with correct data model)
    print("2. AI-LITE VALIDATOR - Data Validation & Triage")
    print("=" * 55)
    
    try:
        from src.processors.analysis.ai_lite_validator import (
            AILiteValidator, ValidationRequest
        )
        
        validator = AILiteValidator()
        print(f"Purpose: {validator.metadata.description}")
        print(f"Model: {validator.model}")
        print(f"Cost per candidate: ${validator.estimated_cost_per_candidate}")
        print()
        
        # Create validation request with correct structure
        validation_request = ValidationRequest(
            batch_id=f"validator_test_{datetime.now().strftime('%H%M%S')}",
            profile_context={
                "organization_name": "Rural Health Technology Institute",
                "mission_statement": "Advancing rural healthcare through technology",
                "focus_areas": ["rural health", "health technology"]
            },
            candidates=[{
                "opportunity_id": "test_validation_001",
                "organization_name": "HRSA Rural Health Grant",
                "source_type": "government",
                "description": "Federal program for rural health technology implementation",
                "funding_amount": 200000,
                "website_url": "https://hrsa.gov/rural-health"
            }],
            analysis_priority="standard"
        )
        
        print("FRONTEND REQUEST TO AI-LITE VALIDATOR:")
        print("-" * 45)
        print(f"  Batch ID: {validation_request.batch_id}")
        print(f"  Profile: {validation_request.profile_context['organization_name']}")
        print(f"  Candidates: {len(validation_request.candidates)}")
        print(f"  Priority: {validation_request.analysis_priority}")
        print(f"  Purpose: Fast validation and triage of opportunities")
        print()
        
        # Show validation prompt
        validation_prompt = validator._create_validation_prompt(validation_request)
        print("VALIDATION PROMPT SENT TO OPENAI:")
        print("-" * 35)
        print(validation_prompt[:400] + "\\n..." if len(validation_prompt) > 400 else validation_prompt)
        print(f"\\nPrompt length: {len(validation_prompt)} characters")
        print()
        
        print("Executing AI-Lite Validator...")
        start_time = datetime.now()
        
        validation_result = await validator.execute(validation_request)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print("\\nBACKEND RESULTS FROM AI-LITE VALIDATOR:")
        print("-" * 45)
        batch_info = validation_result.batch_results
        print(f"  Model used: {batch_info.model_used}")
        print(f"  Processing time: {batch_info.processing_time:.2f}s")
        print(f"  Total cost: ${batch_info.total_cost:.6f}")
        print(f"  Validations processed: {batch_info.processed_count}")
        
        # Show validation results
        validation = list(validation_result.validations.values())[0]
        print(f"\\n  VALIDATION RESULTS:")
        print(f"  Opportunity ID: test_validation_001")
        print(f"  Validation Result: {validation.validation_result}")
        print(f"  Eligibility Status: {validation.eligibility_status}")
        print(f"  Confidence Score: {validation.confidence_level:.3f}")
        print(f"  Discovery Track: {validation.discovery_track}")
        print(f"  Data Quality Score: {validation.data_quality_score:.3f}")
        print(f"  Quick Assessment: {validation.quick_assessment}")
        
        api_status = "REAL API" if validation.confidence_level > 0.5 else "SIMULATION"
        print(f"\\n  STATUS: {api_status} (confidence: {validation.confidence_level:.3f})")
        
        results["validator"] = {
            "name": "AI-Lite Validator", 
            "purpose": "Data validation and triage",
            "cost": batch_info.total_cost,
            "processing_time": processing_time,
            "api_status": api_status,
            "confidence": validation.confidence_level,
            "validation_result": validation.validation_result
        }
        
    except Exception as e:
        print(f"[ERROR] AI-Lite Validator failed: {e}")
        import traceback
        traceback.print_exc()
        results["validator"] = {"status": "failed", "error": str(e)}
    
    print("\\n" + "=" * 85 + "\\n")
    
    # Test 3: AI-Lite Strategic Scorer
    print("3. AI-LITE STRATEGIC SCORER - Strategic Analysis")
    print("=" * 55)
    
    try:
        from src.processors.analysis.ai_lite_strategic_scorer import (
            AILiteStrategicScorer, StrategicScoringRequest
        )
        
        strategic = AILiteStrategicScorer()
        print(f"Purpose: {strategic.metadata.description}")
        print(f"Model: {strategic.model}")
        print(f"Cost per candidate: ${strategic.estimated_cost_per_candidate}")
        print()
        
        # Create strategic request with correct structure
        strategic_request = StrategicScoringRequest(
            batch_id=f"strategic_test_{datetime.now().strftime('%H%M%S')}",
            profile_context={
                "organization_name": "Rural Health Technology Institute",
                "mission_statement": "Advancing rural healthcare through technology",
                "focus_areas": ["rural health", "health technology"],
                "strategic_priorities": ["health equity", "technology innovation", "rural access"]
            },
            validated_candidates=[{
                "opportunity_id": "test_strategic_001",
                "organization_name": "HRSA Strategic Health Initiative",
                "source_type": "government",
                "description": "Strategic federal program for transformative rural health technology initiatives",
                "funding_amount": 500000,
                "strategic_context": "High-priority health equity initiative"
            }],
            validation_results={},  # Empty for direct test
            analysis_priority="high"
        )
        
        print("FRONTEND REQUEST TO AI-LITE STRATEGIC SCORER:")
        print("-" * 50)
        print(f"  Batch ID: {strategic_request.batch_id}")
        print(f"  Profile: {strategic_request.profile_context['organization_name']}")
        print(f"  Validated Candidates: {len(strategic_request.validated_candidates)}")
        print(f"  Analysis Priority: {strategic_request.analysis_priority}")
        print(f"  Purpose: Strategic assessment and priority scoring")
        print()
        
        # Show strategic prompt
        strategic_prompt = strategic._create_strategic_scoring_prompt(strategic_request)
        print("STRATEGIC PROMPT SENT TO OPENAI:")
        print("-" * 35)
        print(strategic_prompt[:400] + "\\n..." if len(strategic_prompt) > 400 else strategic_prompt)
        print(f"\\nPrompt length: {len(strategic_prompt)} characters")
        print()
        
        print("Executing AI-Lite Strategic Scorer...")
        start_time = datetime.now()
        
        strategic_result = await strategic.execute(strategic_request)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print("\\nBACKEND RESULTS FROM AI-LITE STRATEGIC SCORER:")
        print("-" * 50)
        batch_info = strategic_result.batch_results
        print(f"  Model used: {batch_info.model_used}")
        print(f"  Processing time: {batch_info.processing_time:.2f}s")
        print(f"  Total cost: ${batch_info.total_cost:.6f}")
        print(f"  Strategic analyses: {batch_info.processed_count}")
        
        # Show strategic results
        strategic_analysis = list(strategic_result.strategic_analyses.values())[0]
        print(f"\\n  STRATEGIC ANALYSIS RESULTS:")
        print(f"  Opportunity ID: test_strategic_001")
        print(f"  Strategic Score: {strategic_analysis.strategic_score:.3f}")
        print(f"  Strategic Value: {strategic_analysis.strategic_value}")
        print(f"  Alignment Score: {strategic_analysis.alignment_score:.3f}")
        print(f"  Competitive Position: {strategic_analysis.competitive_position}")
        print(f"  Implementation Risk: {strategic_analysis.implementation_risk}")
        print(f"  Priority Ranking: {strategic_analysis.priority_ranking}")
        print(f"  Strategic Rationale: {strategic_analysis.strategic_rationale}")
        
        api_status = "REAL API" if strategic_analysis.confidence_level > 0.5 else "SIMULATION"
        print(f"\\n  STATUS: {api_status} (confidence: {strategic_analysis.confidence_level:.3f})")
        
        results["strategic"] = {
            "name": "AI-Lite Strategic Scorer",
            "purpose": "Strategic analysis and scoring", 
            "cost": batch_info.total_cost,
            "processing_time": processing_time,
            "api_status": api_status,
            "confidence": strategic_analysis.confidence_level,
            "strategic_score": strategic_analysis.strategic_score
        }
        
    except Exception as e:
        print(f"[ERROR] AI-Lite Strategic Scorer failed: {e}")
        import traceback
        traceback.print_exc()
        results["strategic"] = {"status": "failed", "error": str(e)}
    
    # Final Summary
    print("\\n" + "=" * 85)
    print("COMPLETE AI-LITE PROCESSORS SUMMARY")
    print("=" * 85)
    
    total_cost = 0
    total_time = 0
    real_api_count = 0
    working_count = 0
    
    for name, result in results.items():
        if result.get("status") != "failed":
            working_count += 1
            print(f"\\n{result['name'].upper()}:")
            print(f"  Purpose: {result['purpose']}")
            print(f"  API Status: {result['api_status']}")
            print(f"  Cost: ${result['cost']:.6f}")
            print(f"  Processing Time: {result['processing_time']:.2f}s")
            print(f"  Confidence: {result['confidence']:.3f}")
            
            if name == "scorer":
                print(f"  Compatibility Score: {result['compatibility_score']:.3f}")
            elif name == "validator":
                print(f"  Validation: {result['validation_result']}")
            elif name == "strategic":
                print(f"  Strategic Score: {result['strategic_score']:.3f}")
                
            total_cost += result['cost']
            total_time += result['processing_time']
            
            if result['api_status'] == "REAL API":
                real_api_count += 1
        else:
            print(f"\\n{name.upper()}: FAILED")
            print(f"  Error: {result['error']}")
    
    print(f"\\nSUMMARY:")
    print(f"  Working Processors: {working_count}/3")
    print(f"  Real API Calls: {real_api_count}/{working_count}")
    print(f"  Total Cost: ${total_cost:.6f}")
    print(f"  Total Time: {total_time:.2f} seconds")
    print(f"  Average Cost per Processor: ${total_cost/working_count:.6f}" if working_count > 0 else "")
    
    print("\\nCheck your OpenAI usage dashboard to confirm API calls!")
    
    return results

if __name__ == "__main__":
    print("Testing all working AI-lite processors with real API calls...")
    result = asyncio.run(test_working_ai_lite_processors())
    
    working = sum(1 for r in result.values() if r.get("status") != "failed")
    real_api = sum(1 for r in result.values() if r.get("api_status") == "REAL API")
    
    print(f"\\n✅ {working}/3 processors working")
    print(f"🔥 {real_api}/{working} using real API calls")