#!/usr/bin/env python3
"""
Complete AI-Lite Processors Test
Tests all three AI-lite processors showing frontend requests and backend results
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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_all_ai_lite_processors():
    """Test all three AI-lite processors with complete request/response flow"""
    
    print("=" * 90)
    print("COMPLETE AI-LITE PROCESSORS TEST - ALL THREE PROCESSORS")
    print("=" * 90)
    print()
    
    # Test data for all processors
    test_opportunity = {
        "opportunity_id": "ai_test_rural_health_001",
        "organization_name": "HRSA Rural Health Technology Initiative",
        "source_type": "government",
        "description": "Federal program supporting rural healthcare organizations in implementing innovative technology solutions including telehealth platforms, electronic health records, and remote patient monitoring systems to improve healthcare access and outcomes in underserved rural communities.",
        "funding_amount": 250000,
        "application_deadline": "2024-10-15",
        "geographic_location": "Rural areas nationwide",
        "website_url": "https://hrsa.gov/rural-health/technology",
        "current_score": 0.82
    }
    
    test_profile = {
        "organization_name": "Digital Health Innovation Foundation",
        "mission_statement": "Advancing healthcare equity through innovative digital health technologies and strategic partnerships with rural healthcare providers.",
        "focus_areas": ["digital health", "rural healthcare", "health technology", "telehealth", "health equity"],
        "ntee_codes": ["E32", "E42", "U41"],
        "government_criteria": ["501c3", "healthcare_focus", "technology_focus"],
        "keywords": ["health", "technology", "digital", "rural", "innovation", "equity"],
        "geographic_scope": "National with rural focus",
        "annual_budget": "$4.2M",
        "grant_making_capacity": "$1.2M"
    }
    
    print("SHARED TEST DATA:")
    print(f"  Profile: {test_profile['organization_name']}")
    print(f"  Mission: {test_profile['mission_statement'][:80]}...")
    print(f"  Opportunity: {test_opportunity['organization_name']}")
    print(f"  Funding: ${test_opportunity['funding_amount']:,}")
    print(f"  Description: {test_opportunity['description'][:100]}...")
    print()
    
    # Test each processor
    results = {}
    
    # Test 1: AI-Lite Scorer (Standard compatibility scoring)
    print("1. AI-LITE SCORER - Standard Compatibility Analysis")
    print("=" * 60)
    
    try:
        from src.processors.analysis.ai_lite_scorer import (
            AILiteScorer, AILiteRequest, RequestMetadata, ProfileContext, 
            CandidateData, FundingHistory
        )
        
        # Create processor
        scorer = AILiteScorer()
        print(f"Purpose: {scorer.metadata.description}")
        print(f"Model: {scorer.model}")
        print(f"Cost per candidate: ${scorer.estimated_cost_per_candidate}")
        print()
        
        # Create request data
        profile_context = ProfileContext(
            organization_name=test_profile["organization_name"],
            mission_statement=test_profile["mission_statement"],
            focus_areas=test_profile["focus_areas"],
            ntee_codes=test_profile["ntee_codes"],
            government_criteria=test_profile["government_criteria"],
            keywords=test_profile["keywords"],
            geographic_scope=test_profile["geographic_scope"],
            funding_history=FundingHistory(
                typical_grant_size="$50000-300000",
                annual_budget=test_profile["annual_budget"],
                grant_making_capacity=test_profile["grant_making_capacity"]
            )
        )
        
        candidate = CandidateData(
            opportunity_id=test_opportunity["opportunity_id"],
            organization_name=test_opportunity["organization_name"],
            source_type=test_opportunity["source_type"],
            description=test_opportunity["description"],
            funding_amount=test_opportunity["funding_amount"],
            application_deadline=test_opportunity["application_deadline"],
            geographic_location=test_opportunity["geographic_location"],
            current_score=test_opportunity["current_score"]
        )
        
        request = AILiteRequest(
            request_metadata=RequestMetadata(
                batch_id=f"scorer_test_{datetime.now().strftime('%H%M%S')}",
                profile_id="test_profile_scorer",
                analysis_type="compatibility_scoring",
                model_preference="gpt-3.5-turbo",
                cost_limit=0.01,
                priority="standard"
            ),
            profile_context=profile_context,
            candidates=[candidate]
        )
        
        print("FRONTEND REQUEST TO AI-LITE SCORER:")
        print("-" * 40)
        print(f"  Request Type: {request.request_metadata.analysis_type}")
        print(f"  Profile: {profile_context.organization_name}")
        print(f"  Candidate: {candidate.organization_name}")
        print(f"  Model: {request.request_metadata.model_preference}")
        print(f"  Priority: {request.request_metadata.priority}")
        print()
        
        # Show generated prompt
        prompt = scorer._create_enhanced_batch_prompt(request)
        print("GENERATED OPENAI PROMPT:")
        print("-" * 25)
        print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
        print(f"\nPrompt length: {len(prompt)} characters")
        print()
        
        # Execute
        print("Executing AI-Lite Scorer...")
        start_time = datetime.now()
        result = await scorer.execute(request)
        end_time = datetime.now()
        
        print("BACKEND RESULTS FROM AI-LITE SCORER:")
        print("-" * 40)
        print(f"  Processing time: {(end_time - start_time).total_seconds():.2f}s")
        print(f"  Model used: {result.batch_results.model_used}")
        print(f"  Total cost: ${result.batch_results.total_cost:.6f}")
        
        analysis = list(result.candidate_analysis.values())[0]
        print(f"  Compatibility score: {analysis.compatibility_score:.3f}")
        print(f"  Strategic value: {analysis.strategic_value}")
        print(f"  Funding likelihood: {analysis.funding_likelihood:.3f}")
        print(f"  Strategic rationale: {analysis.strategic_rationale}")
        print(f"  Risk assessment: {', '.join(analysis.risk_assessment)}")
        print(f"  Action priority: {analysis.action_priority}")
        print(f"  Confidence level: {analysis.confidence_level:.3f}")
        
        results["scorer"] = {
            "processor": "AI-Lite Scorer",
            "purpose": "Standard compatibility scoring",
            "cost": result.batch_results.total_cost,
            "processing_time": (end_time - start_time).total_seconds(),
            "compatibility_score": analysis.compatibility_score,
            "confidence": analysis.confidence_level,
            "status": "Real API" if analysis.confidence_level > 0.5 else "Simulation"
        }
        
    except Exception as e:
        print(f"[ERROR] AI-Lite Scorer test failed: {e}")
        results["scorer"] = {"status": "failed", "error": str(e)}
    
    print("\n" + "=" * 90 + "\n")
    
    # Test 2: AI-Lite Validator (Data validation and triage)
    print("2. AI-LITE VALIDATOR - Data Validation & Triage")
    print("=" * 55)
    
    try:
        from src.processors.analysis.ai_lite_validator import (
            AILiteValidator, ValidationRequest, CandidateValidation, 
            ValidationBatchResult
        )
        
        validator = AILiteValidator()
        print(f"Purpose: {validator.metadata.description}")
        print(f"Model: {validator.model}")
        print(f"Cost per candidate: ${validator.estimated_cost_per_candidate}")
        print()
        
        # Create validation request
        validation_candidates = [CandidateValidation(
            opportunity_id=test_opportunity["opportunity_id"],
            organization_name=test_opportunity["organization_name"],
            source_type=test_opportunity["source_type"],
            description=test_opportunity["description"],
            funding_amount=test_opportunity["funding_amount"],
            application_deadline=test_opportunity["application_deadline"],
            website_url=test_opportunity.get("website_url"),
            preliminary_score=test_opportunity["current_score"]
        )]
        
        validation_request = ValidationRequest(
            batch_id=f"validator_test_{datetime.now().strftime('%H%M%S')}",
            profile_id="test_profile_validator",
            validation_type="fast_triage",
            model_preference="gpt-3.5-turbo",
            candidates=validation_candidates,
            profile_context=test_profile
        )
        
        print("FRONTEND REQUEST TO AI-LITE VALIDATOR:")
        print("-" * 45)
        print(f"  Validation Type: {validation_request.validation_type}")
        print(f"  Profile: {test_profile['organization_name']}")
        print(f"  Candidate: {validation_candidates[0].organization_name}")
        print(f"  Model: {validation_request.model_preference}")
        print(f"  Purpose: Fast opportunity validation and triage")
        print()
        
        # Show validation prompt
        validation_prompt = validator._create_validation_prompt(validation_request)
        print("GENERATED VALIDATION PROMPT:")
        print("-" * 30)
        print(validation_prompt[:300] + "..." if len(validation_prompt) > 300 else validation_prompt)
        print(f"\nPrompt length: {len(validation_prompt)} characters")
        print()
        
        # Execute validator
        print("Executing AI-Lite Validator...")
        start_time = datetime.now()
        validation_result = await validator.execute(validation_request)
        end_time = datetime.now()
        
        print("BACKEND RESULTS FROM AI-LITE VALIDATOR:")
        print("-" * 45)
        print(f"  Processing time: {(end_time - start_time).total_seconds():.2f}s")
        print(f"  Model used: {validation_result.batch_results.model_used}")
        print(f"  Total cost: ${validation_result.batch_results.total_cost:.6f}")
        
        validation = list(validation_result.validations.values())[0]
        print(f"  Validation result: {validation.validation_result}")
        print(f"  Confidence score: {validation.confidence_score:.3f}")
        print(f"  Eligibility status: {validation.eligibility_status}")
        print(f"  Data quality score: {validation.data_quality_score:.3f}")
        print(f"  Validation flags: {', '.join(validation.validation_flags)}")
        print(f"  Quick assessment: {validation.quick_assessment}")
        
        results["validator"] = {
            "processor": "AI-Lite Validator",
            "purpose": "Data validation and triage",
            "cost": validation_result.batch_results.total_cost,
            "processing_time": (end_time - start_time).total_seconds(),
            "validation_result": validation.validation_result,
            "confidence": validation.confidence_score,
            "status": "Real API" if validation.confidence_score > 0.5 else "Simulation"
        }
        
    except Exception as e:
        print(f"[ERROR] AI-Lite Validator test failed: {e}")
        results["validator"] = {"status": "failed", "error": str(e)}
        
    print("\n" + "=" * 90 + "\n")
    
    # Test 3: AI-Lite Strategic Scorer (Strategic analysis and scoring)
    print("3. AI-LITE STRATEGIC SCORER - Strategic Analysis")
    print("=" * 55)
    
    try:
        from src.processors.analysis.ai_lite_strategic_scorer import (
            AILiteStrategicScorer, StrategicScoringRequest, StrategicCandidate,
            StrategicScoringResult
        )
        
        strategic = AILiteStrategicScorer()
        print(f"Purpose: {strategic.metadata.description}")
        print(f"Model: {strategic.model}")
        print(f"Cost per candidate: ${strategic.estimated_cost_per_candidate}")
        print()
        
        # Create strategic scoring request
        strategic_candidates = [StrategicCandidate(
            opportunity_id=test_opportunity["opportunity_id"],
            organization_name=test_opportunity["organization_name"],
            source_type=test_opportunity["source_type"],
            description=test_opportunity["description"],
            funding_amount=test_opportunity["funding_amount"],
            strategic_context="High-priority rural health technology initiative aligned with federal priorities",
            competition_level="high",
            implementation_complexity="medium",
            baseline_score=test_opportunity["current_score"]
        )]
        
        strategic_request = StrategicScoringRequest(
            batch_id=f"strategic_test_{datetime.now().strftime('%H%M%S')}",
            profile_id="test_profile_strategic",
            analysis_type="comprehensive_strategic",
            model_preference="gpt-3.5-turbo",
            candidates=strategic_candidates,
            profile_context=test_profile,
            strategic_priorities=["rural health access", "technology innovation", "health equity"]
        )
        
        print("FRONTEND REQUEST TO AI-LITE STRATEGIC SCORER:")
        print("-" * 50)
        print(f"  Analysis Type: {strategic_request.analysis_type}")
        print(f"  Profile: {test_profile['organization_name']}")
        print(f"  Candidate: {strategic_candidates[0].organization_name}")
        print(f"  Strategic Context: {strategic_candidates[0].strategic_context}")
        print(f"  Competition Level: {strategic_candidates[0].competition_level}")
        print(f"  Strategic Priorities: {', '.join(strategic_request.strategic_priorities)}")
        print()
        
        # Show strategic prompt
        strategic_prompt = strategic._create_strategic_scoring_prompt(strategic_request)
        print("GENERATED STRATEGIC PROMPT:")
        print("-" * 30)
        print(strategic_prompt[:300] + "..." if len(strategic_prompt) > 300 else strategic_prompt)
        print(f"\nPrompt length: {len(strategic_prompt)} characters")
        print()
        
        # Execute strategic scorer
        print("Executing AI-Lite Strategic Scorer...")
        start_time = datetime.now()
        strategic_result = await strategic.execute(strategic_request)
        end_time = datetime.now()
        
        print("BACKEND RESULTS FROM AI-LITE STRATEGIC SCORER:")
        print("-" * 50)
        print(f"  Processing time: {(end_time - start_time).total_seconds():.2f}s")
        print(f"  Model used: {strategic_result.batch_results.model_used}")
        print(f"  Total cost: ${strategic_result.batch_results.total_cost:.6f}")
        
        strategic_analysis = list(strategic_result.strategic_analyses.values())[0]
        print(f"  Strategic score: {strategic_analysis.strategic_score:.3f}")
        print(f"  Strategic value: {strategic_analysis.strategic_value}")
        print(f"  Alignment score: {strategic_analysis.alignment_score:.3f}")
        print(f"  Competitive position: {strategic_analysis.competitive_position}")
        print(f"  Implementation risk: {strategic_analysis.implementation_risk}")
        print(f"  Strategic rationale: {strategic_analysis.strategic_rationale}")
        print(f"  Priority ranking: {strategic_analysis.priority_ranking}")
        
        results["strategic"] = {
            "processor": "AI-Lite Strategic Scorer",
            "purpose": "Strategic analysis and scoring",
            "cost": strategic_result.batch_results.total_cost,
            "processing_time": (end_time - start_time).total_seconds(),
            "strategic_score": strategic_analysis.strategic_score,
            "confidence": strategic_analysis.confidence_level,
            "status": "Real API" if strategic_analysis.confidence_level > 0.5 else "Simulation"
        }
        
    except Exception as e:
        print(f"[ERROR] AI-Lite Strategic Scorer test failed: {e}")
        results["strategic"] = {"status": "failed", "error": str(e)}
    
    # Summary comparison
    print("\n" + "=" * 90)
    print("COMPLETE PROCESSORS COMPARISON")
    print("=" * 90)
    
    total_cost = 0
    total_time = 0
    
    for name, result in results.items():
        if result.get("status") != "failed":
            print(f"\n{result['processor'].upper()}:")
            print(f"  Purpose: {result['purpose']}")
            print(f"  Status: {result['status']}")
            print(f"  Cost: ${result['cost']:.6f}")
            print(f"  Processing Time: {result['processing_time']:.2f}s")
            print(f"  Confidence: {result['confidence']:.3f}")
            
            if name == "scorer":
                print(f"  Compatibility Score: {result['compatibility_score']:.3f}")
            elif name == "validator":
                print(f"  Validation Result: {result['validation_result']}")
            elif name == "strategic":
                print(f"  Strategic Score: {result['strategic_score']:.3f}")
                
            total_cost += result['cost']
            total_time += result['processing_time']
        else:
            print(f"\n{name.upper()}: FAILED - {result['error']}")
    
    print(f"\nTOTAL COST: ${total_cost:.6f}")
    print(f"TOTAL TIME: {total_time:.2f} seconds")
    
    working_processors = [r for r in results.values() if r.get("status") != "failed"]
    real_api_count = sum(1 for r in working_processors if r.get("status") == "Real API")
    
    print(f"WORKING PROCESSORS: {len(working_processors)}/3")
    print(f"REAL API CALLS: {real_api_count}/{len(working_processors)}")
    
    return results

if __name__ == "__main__":
    print("Testing all three AI-lite processors...")
    result = asyncio.run(test_all_ai_lite_processors())
    
    success_count = sum(1 for r in result.values() if r.get("status") != "failed")
    print(f"\nTest completed: {success_count}/3 processors working")
    
    if success_count > 0:
        print("Check your OpenAI usage dashboard for actual API calls made!")