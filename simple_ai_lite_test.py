#!/usr/bin/env python3
"""
Simple AI Lite API Test - Request/Response Analysis
Shows exactly what gets sent to OpenAI and what comes back

This script demonstrates:
1. Request structure sent to AI-Lite processor
2. Prompt generated for OpenAI API
3. Raw response from OpenAI 
4. Parsed structured results
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

# Configure logging to show detailed flow
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_ai_lite_flow():
    """Test the complete AI-Lite request/response flow"""
    
    print("=" * 60)
    print("AI-LITE API REQUEST/RESPONSE FLOW TEST")
    print("=" * 60)
    print()
    
    try:
        # Import AI-Lite processor
        from src.processors.analysis.ai_lite_scorer import (
            AILiteScorer, 
            AILiteRequest, 
            RequestMetadata, 
            ProfileContext, 
            CandidateData,
            FundingHistory
        )
        
        print("[OK] AI-Lite processor imported successfully")
        print()
        
        # Initialize the processor
        processor = AILiteScorer()
        print("[OK] AI-Lite processor initialized")
        print(f"   Model: {processor.model}")
        print(f"   Batch size: {processor.batch_size}")
        print(f"   Estimated cost per candidate: ${processor.estimated_cost_per_candidate}")
        print()
        
        # Create test profile context
        profile_context = ProfileContext(
            organization_name="Test Nonprofit Foundation",
            mission_statement="To improve healthcare access and outcomes for underserved communities through innovative programs and strategic partnerships.",
            focus_areas=["healthcare", "community health", "rural medicine", "health equity"],
            ntee_codes=["E32", "E42", "E86"],  # Health care, health services
            government_criteria=["501c3", "healthcare_focus", "rural_service"],
            keywords=["health", "medical", "community", "rural", "access"],
            geographic_scope="Virginia and surrounding states",
            funding_history=FundingHistory(
                typical_grant_size="$25000-150000",
                annual_budget="$3.2M", 
                grant_making_capacity="$800K"
            )
        )
        
        # Create test candidate data
        test_candidates = [
            CandidateData(
                opportunity_id="test_health_foundation_001",
                organization_name="Virginia Health Innovation Foundation",
                source_type="foundation",
                description="Rural Health Access Initiative - Supporting innovative healthcare delivery models in underserved rural communities across Virginia. Focus on telemedicine, mobile health units, and community health worker programs.",
                funding_amount=75000,
                application_deadline="2024-06-15",
                geographic_location="Virginia",
                current_score=0.82
            ),
            CandidateData(
                opportunity_id="test_government_grant_002", 
                organization_name="HRSA Rural Health Grants Program",
                source_type="government",
                description="Health Resources and Services Administration rural health grant program supporting community health centers and rural health clinics in expanding access to primary care services.",
                funding_amount=125000,
                application_deadline="2024-07-30",
                geographic_location="National",
                current_score=0.78
            ),
            CandidateData(
                opportunity_id="test_community_fund_003",
                organization_name="Community Health Equity Fund",
                source_type="foundation", 
                description="Supporting grassroots organizations addressing health disparities in minority and low-income communities through innovative outreach and education programs.",
                funding_amount=45000,
                application_deadline="2024-05-20",
                geographic_location="Southeast US",
                current_score=0.71
            )
        ]
        
        # Create test request metadata
        request_metadata = RequestMetadata(
            batch_id=f"test_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            profile_id="profile_test_ai_flow",
            analysis_type="compatibility_scoring",
            model_preference="gpt-3.5-turbo",  # Use reliable model
            cost_limit=0.05,
            priority="standard"
        )
        
        # Create complete AI-Lite request
        ai_lite_request = AILiteRequest(
            request_metadata=request_metadata,
            profile_context=profile_context,
            candidates=test_candidates
        )
        
        print("=" * 50)
        print("1. REQUEST DATA STRUCTURE")
        print("=" * 50)
        print()
        print("Profile Context:")
        print(f"  Organization: {profile_context.organization_name}")
        print(f"  Mission: {profile_context.mission_statement[:100]}...")
        print(f"  Focus Areas: {', '.join(profile_context.focus_areas)}")
        print(f"  NTEE Codes: {', '.join(profile_context.ntee_codes)}")
        print()
        
        print("Test Candidates:")
        for i, candidate in enumerate(test_candidates, 1):
            print(f"  {i}. {candidate.organization_name}")
            print(f"     ID: {candidate.opportunity_id}")
            print(f"     Type: {candidate.source_type}")
            print(f"     Funding: ${candidate.funding_amount:,}")
            print(f"     Current Score: {candidate.current_score:.2f}")
            print(f"     Description: {candidate.description[:80]}...")
            print()
        
        print("Request Metadata:")
        print(f"  Batch ID: {request_metadata.batch_id}")
        print(f"  Model: {request_metadata.model_preference}")
        print(f"  Cost Limit: ${request_metadata.cost_limit}")
        print()
        
        # Show what prompt will be generated (without making API call yet)
        print("=" * 50)
        print("2. GENERATED PROMPT FOR OPENAI")
        print("=" * 50)
        print()
        
        # Generate the prompt that would be sent to OpenAI
        batch_prompt = processor._create_enhanced_batch_prompt(ai_lite_request)
        
        print("PROMPT TO BE SENT TO OPENAI API:")
        print("-" * 40)
        print(batch_prompt)
        print("-" * 40)
        print()
        
        prompt_stats = {
            "total_characters": len(batch_prompt),
            "estimated_tokens": len(batch_prompt) // 4,  # Rough estimate
            "lines": batch_prompt.count('\n'),
            "candidates_included": len(test_candidates)
        }
        
        print("Prompt Statistics:")
        for key, value in prompt_stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        print()
        
        # Now execute the actual AI-Lite analysis
        print("=" * 50)
        print("3. EXECUTING AI-LITE ANALYSIS")
        print("=" * 50)
        print()
        
        print("Sending request to OpenAI API...")
        print(f"  Model: {request_metadata.model_preference}")
        print(f"  Max tokens: {processor.max_tokens}")
        print(f"  Temperature: {processor.temperature}")
        print()
        
        # Execute the analysis
        start_time = datetime.now()
        result = await processor.execute(ai_lite_request)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"[OK] Analysis completed in {processing_time:.2f} seconds")
        print()
        
        # Display results
        print("=" * 50)
        print("4. ANALYSIS RESULTS")
        print("=" * 50)
        print()
        
        print("Batch Results:")
        batch_results = result.batch_results
        print(f"  Batch ID: {batch_results.batch_id}")
        print(f"  Processed Count: {batch_results.processed_count}")
        print(f"  Processing Time: {batch_results.processing_time:.2f}s")
        print(f"  Total Cost: ${batch_results.total_cost:.4f}")
        print(f"  Model Used: {batch_results.model_used}")
        print(f"  Analysis Quality: {batch_results.analysis_quality}")
        print()
        
        print("Individual Analysis Results:")
        print()
        
        for opp_id, analysis in result.candidate_analysis.items():
            print(f"Opportunity: {opp_id}")
            print(f"  Compatibility Score: {analysis.compatibility_score:.3f}")
            print(f"  Strategic Value: {analysis.strategic_value}")
            print(f"  Funding Likelihood: {analysis.funding_likelihood:.3f}")
            print(f"  Priority Rank: {analysis.priority_rank}")
            print(f"  Action Priority: {analysis.action_priority}")
            print(f"  Confidence Level: {analysis.confidence_level:.3f}")
            print(f"  Strategic Rationale: {analysis.strategic_rationale}")
            print(f"  Risk Assessment: {', '.join(analysis.risk_assessment)}")
            
            if analysis.research_mode_enabled and analysis.research_report:
                print(f"  Research Mode: Enabled")
                print(f"  Executive Summary: {analysis.research_report.executive_summary[:100]}...")
            
            print()
        
        # Summary statistics
        print("=" * 50)
        print("5. SUMMARY STATISTICS")
        print("=" * 50)
        print()
        
        scores = [analysis.compatibility_score for analysis in result.candidate_analysis.values()]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        print(f"Total Candidates Analyzed: {len(result.candidate_analysis)}")
        print(f"Average Compatibility Score: {avg_score:.3f}")
        print(f"Highest Score: {max(scores):.3f}" if scores else "N/A")
        print(f"Lowest Score: {min(scores):.3f}" if scores else "N/A")
        print(f"Total Processing Time: {processing_time:.2f} seconds")
        print(f"Total Estimated Cost: ${batch_results.total_cost:.4f}")
        print(f"Cost per Candidate: ${batch_results.total_cost / len(test_candidates):.4f}")
        print()
        
        # Save detailed results to file
        output_file = f"ai_lite_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert result to JSON-serializable format
        result_data = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "processing_time_seconds": processing_time,
                "test_type": "AI-Lite Request/Response Flow"
            },
            "request_data": {
                "batch_id": request_metadata.batch_id,
                "profile_name": profile_context.organization_name,
                "candidates_count": len(test_candidates),
                "model_used": request_metadata.model_preference
            },
            "prompt_statistics": prompt_stats,
            "batch_results": {
                "batch_id": batch_results.batch_id,
                "processed_count": batch_results.processed_count,
                "processing_time": batch_results.processing_time,
                "total_cost": batch_results.total_cost,
                "model_used": batch_results.model_used
            },
            "analysis_results": {
                opp_id: {
                    "compatibility_score": analysis.compatibility_score,
                    "strategic_value": analysis.strategic_value,
                    "funding_likelihood": analysis.funding_likelihood,
                    "priority_rank": analysis.priority_rank,
                    "action_priority": analysis.action_priority,
                    "confidence_level": analysis.confidence_level,
                    "strategic_rationale": analysis.strategic_rationale,
                    "risk_assessment": analysis.risk_assessment,
                    "research_mode_enabled": analysis.research_mode_enabled
                }
                for opp_id, analysis in result.candidate_analysis.items()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        print(f"[SAVED] Detailed results saved to: {output_file}")
        print()
        
        print("=" * 60)
        print("AI-LITE API TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Error during AI-Lite test: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Starting AI-Lite API Request/Response Flow Test...")
    print()
    
    # Run the async test
    result = asyncio.run(test_ai_lite_flow())
    
    if result:
        print("\n[SUCCESS] Test completed successfully!")
        print("You can now see exactly how the AI-Lite system works:")
        print("  1. Request structure and data")
        print("  2. Generated prompt sent to OpenAI")
        print("  3. Processing and response handling")
        print("  4. Structured analysis results")
    else:
        print("\n[FAILED] Test failed. Check the error messages above.")