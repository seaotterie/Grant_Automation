#!/usr/bin/env python3
"""
Test Enhanced AI-Lite Validator - Phase 2A Implementation
Testing enhanced funding provider verification, website intelligence, and competition pre-screening
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

async def test_enhanced_validator():
    """Test enhanced AI-Lite Validator with Phase 2A features"""
    
    print("=" * 80)
    print("ENHANCED AI-LITE VALIDATOR TEST - Phase 2A Features")
    print("=" * 80)
    print("Testing: Funding provider verification, website intelligence, competition pre-screening")
    print()
    
    try:
        from src.processors.analysis.ai_lite_validator import AILiteValidator, ValidationRequest
        
        validator = AILiteValidator()
        
        # Test with diverse opportunity types to test enhanced intelligence
        test_candidates = [
            {
                "opportunity_id": "enhanced_test_001",
                "organization_name": "National Science Foundation - AI Research Initiative", 
                "source_type": "government",
                "website": "https://nsf.gov/funding/ai-research",
                "description": "NSF seeks proposals for artificial intelligence research with potential for transformative impact. Applications due March 15, 2025. Contact: Dr. Sarah Johnson, Program Director."
            },
            {
                "opportunity_id": "enhanced_test_002",
                "organization_name": "GrantSpace.org - Funding Database",
                "source_type": "information",
                "website": "https://grantspace.org/find-funding",
                "description": "GrantSpace provides a comprehensive database of funding opportunities. Search thousands of grants and foundations. No application process - information service only."
            },
            {
                "opportunity_id": "enhanced_test_003", 
                "organization_name": "Gates Foundation - Global Health Innovation",
                "source_type": "foundation",
                "website": "https://gatesfoundation.org/grants",
                "description": "Private foundation supporting global health innovations. Highly competitive program with extensive requirements. Recent awards to Johns Hopkins, Stanford. Letter of inquiry required."
            }
        ]
        
        request = ValidationRequest(
            batch_id=f"enhanced_validator_{datetime.now().strftime('%H%M%S')}",
            profile_context={
                "organization_name": "Advanced Healthcare AI Research Institute",
                "focus_areas": ["AI in healthcare", "medical innovation", "global health"],
                "geographic_scope": "National/International",
                "organization_type": "501c3 Research Institute"
            },
            candidates=test_candidates
        )
        
        print(f"Testing with {len(test_candidates)} diverse opportunities:")
        for i, candidate in enumerate(test_candidates, 1):
            print(f"  {i}. {candidate['organization_name']} ({candidate['source_type']})")
        print()
        print(f"Model: {validator.model} (GPT-5-nano)")
        print("Enhanced Features: Funding provider verification, website intelligence, competition analysis")
        print()
        
        # Execute enhanced validation
        start_time = datetime.now()
        result = await validator.execute(request)
        end_time = datetime.now()
        
        print("ENHANCED VALIDATION RESULTS:")
        print(f"Processing time: {(end_time - start_time).total_seconds():.2f}s")
        print(f"Total cost: ${result.total_cost:.6f}")
        print(f"Processed count: {result.processed_count}")
        print()
        
        if result.validations:
            for i, (opp_id, validation) in enumerate(result.validations.items(), 1):
                print(f"--- OPPORTUNITY {i}: {opp_id} ---")
                print(f"  Validation: {validation.validation_result.value}")
                print(f"  Eligibility: {validation.eligibility_status.value}")
                print(f"  Confidence: {validation.confidence_level:.3f}")
                print(f"  Go/No-Go: {validation.go_no_go}")
                
                # Enhanced Phase 2A Features
                print(f"  [ENHANCED] Provider Type: {validation.funding_provider_type}")
                print(f"  [ENHANCED] Program Status: {validation.program_status}")
                print(f"  [ENHANCED] Application Pathway: {validation.application_pathway}")
                print(f"  [ENHANCED] Competition Level: {validation.competition_level}")
                print(f"  [ENHANCED] Application Complexity: {validation.application_complexity}")
                print(f"  [ENHANCED] Success Probability: {validation.success_probability:.3f}")
                print(f"  [ENHANCED] Contact Quality: {validation.contact_quality}")
                
                if validation.deadline_indicators:
                    print(f"  [ENHANCED] Deadlines: {', '.join(validation.deadline_indicators)}")
                if validation.recent_activity:
                    print(f"  [ENHANCED] Recent Activity: {', '.join(validation.recent_activity)}")
                    
                print(f"  Reasoning: {validation.validation_reasoning}")
                if validation.key_flags:
                    print(f"  Flags: {', '.join(validation.key_flags)}")
                print()
            
            # Analysis Summary
            actual_funders = sum(1 for v in result.validations.values() if v.funding_provider_type == "actual_funder")
            high_success = sum(1 for v in result.validations.values() if v.success_probability > 0.7)
            clear_pathways = sum(1 for v in result.validations.values() if v.application_pathway == "clear_process")
            
            print("ENHANCED INTELLIGENCE SUMMARY:")
            print(f"  Actual funders identified: {actual_funders}/{len(result.validations)}")
            print(f"  High success probability (>0.7): {high_success}/{len(result.validations)}")
            print(f"  Clear application pathways: {clear_pathways}/{len(result.validations)}")
            
            # Determine if enhanced features are working
            enhanced_working = any([
                any(v.funding_provider_type != "unknown" for v in result.validations.values()),
                any(v.program_status != "unknown" for v in result.validations.values()),
                any(v.deadline_indicators for v in result.validations.values()),
                any(v.recent_activity for v in result.validations.values())
            ])
            
            status = "ENHANCED FEATURES ACTIVE" if enhanced_working else "BASIC MODE"
            api_status = "REAL API" if validation.confidence_level > 0.5 else "SIMULATION"
            
            print(f"\nSTATUS: {status} | {api_status}")
            
            return {
                "status": "success",
                "enhanced_features": enhanced_working,
                "api_working": validation.confidence_level > 0.5,
                "cost": result.total_cost,
                "intelligence_extracted": {
                    "actual_funders": actual_funders,
                    "high_success_prob": high_success,
                    "clear_pathways": clear_pathways
                }
            }
        else:
            print("  No validation results returned")
            return {"status": "partial", "cost": result.total_cost}
            
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    print("Testing Enhanced AI-Lite Validator (Phase 2A)...")
    result = asyncio.run(test_enhanced_validator())
    
    if result.get("status") == "success":
        if result.get("enhanced_features"):
            print("\nENHANCED VALIDATION SUCCESS!")
            print(f"   Cost: ${result['cost']:.6f}")
            intel = result.get("intelligence_extracted", {})
            print(f"   Intelligence: {intel.get('actual_funders', 0)} funders, {intel.get('high_success_prob', 0)} high-probability")
        else:
            print("\nBasic validation working, enhanced features in simulation mode")
    elif result.get("status") == "partial":
        print("\nPartial success - validator working but limited results")
    else:
        print("\nTest failed")
        
    print("\nCheck your OpenAI dashboard for API usage confirmation!")