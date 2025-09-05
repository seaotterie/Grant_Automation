#!/usr/bin/env python3
"""
Simple AI-Lite Unified Processor Test
Focused testing to validate core functionality and performance
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any

from ai_lite_unified_processor import AILiteUnifiedProcessor, UnifiedRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_opportunities(count: int = 10) -> List[Dict[str, Any]]:
    """Create realistic test opportunities"""
    
    opportunities = []
    
    org_types = [
        {"name": "Foundation", "funding_range": [50000, 250000]},
        {"name": "Government Agency", "funding_range": [100000, 500000]},  
        {"name": "Corporate Foundation", "funding_range": [25000, 150000]},
        {"name": "State Agency", "funding_range": [75000, 300000]}
    ]
    
    for i in range(count):
        org_type = org_types[i % len(org_types)]
        funding_amount = org_type["funding_range"][0] + (i * 15000)
        
        opportunity = {
            "opportunity_id": f"test_unified_{i+1:03d}",
            "organization_name": f"Test {org_type['name']} {i+1}",
            "source_type": org_type["name"].lower().replace(" ", "_"),
            "description": f"Test opportunity {i+1} focusing on digital equity and community development with strategic alignment potential.",
            "funding_amount": funding_amount,
            "website": f"https://test-org-{i+1}.org/grants",
            "geographic_location": ["National", "Regional", "State", "Local"][i % 4],
            "application_deadline": ["2025-03-15", "2025-04-30", "2025-06-01", "Rolling"][i % 4]
        }
        
        opportunities.append(opportunity)
    
    return opportunities


def create_test_profile() -> Dict[str, Any]:
    """Create test organization profile"""
    
    return {
        "name": "Test Digital Equity Organization",
        "mission_statement": "Advancing digital equity and educational opportunities in underserved communities through innovative programs and strategic partnerships.",
        "focus_areas": ["digital equity", "education", "community development", "workforce training"],
        "ntee_codes": ["P20", "P30", "S20"],
        "geographic_scope": "Regional (Mid-Atlantic)",
        "organization_type": "Nonprofit",
        "typical_grant_size": "$50,000 - $200,000"
    }


async def test_unified_processor():
    """Test the unified AI-Lite processor"""
    
    print("UNIFIED AI-LITE PROCESSOR TEST")
    print("=" * 50)
    
    # Initialize processor
    processor = AILiteUnifiedProcessor()
    
    # Create test data
    test_opportunities = create_test_opportunities(5)  # Small test set
    test_profile = create_test_profile()
    
    print(f"\nTest Configuration:")
    print(f"  Opportunities: {len(test_opportunities)}")
    print(f"  Organization: {test_profile['name']}")
    print(f"  Processor Model: {processor.model}")
    print(f"  Max Tokens: {processor.max_tokens}")
    print(f"  Estimated Cost: ${processor.estimated_cost_per_candidate:.6f}/candidate")
    
    # Create request
    request = UnifiedRequest(
        batch_id=f"test_{int(time.time())}",
        profile_context=test_profile,
        candidates=test_opportunities,
        analysis_mode="comprehensive",
        enable_web_scraping=True,
        cost_budget=0.001,
        priority_level="high"
    )
    
    # Execute analysis
    print(f"\nExecuting unified analysis...")
    start_time = time.time()
    
    try:
        result = await processor.execute(request)
        end_time = time.time()
        
        print(f"\nRESULTS:")
        print(f"  Processing Time: {end_time - start_time:.2f} seconds")
        print(f"  Processed Count: {result.processed_count}")
        print(f"  Total Cost: ${result.total_cost:.4f}")
        print(f"  Cost per Candidate: ${result.cost_per_candidate:.6f}")
        print(f"  Web Scraping Attempts: {result.web_scraping_stats.get('total_web_attempts', 0)}")
        print(f"  Web Success Rate: {result.web_scraping_stats.get('success_rate', 0)*100:.1f}%")
        
        # Show sample analyses
        if result.analyses:
            print(f"\nSAMPLE ANALYSES:")
            for i, (opp_id, analysis) in enumerate(list(result.analyses.items())[:3]):
                print(f"\n  {i+1}. {opp_id}:")
                print(f"     Validation: {analysis.validation_result.value}")
                print(f"     Strategic Value: {analysis.strategic_value.value}")
                print(f"     Compatibility: {analysis.compatibility_score:.3f}")
                print(f"     Confidence: {analysis.confidence_level:.3f}")
                print(f"     Action Priority: {analysis.action_priority.value}")
                
                if analysis.web_intelligence:
                    print(f"     Web Intelligence: Available (confidence: {analysis.web_intelligence.extraction_confidence:.2f})")
                else:
                    print(f"     Web Intelligence: Not available")
        
        # Performance analysis
        print(f"\nPERFORMANCE ANALYSIS:")
        avg_confidence = sum(a.confidence_level for a in result.analyses.values()) / len(result.analyses)
        avg_compatibility = sum(a.compatibility_score for a in result.analyses.values()) / len(result.analyses)
        
        print(f"  Average Confidence: {avg_confidence:.3f}")
        print(f"  Average Compatibility: {avg_compatibility:.3f}")
        
        immediate_actions = sum(1 for a in result.analyses.values() 
                              if a.action_priority.value == "immediate")
        print(f"  Immediate Action Opportunities: {immediate_actions}/{len(result.analyses)}")
        
        # Cost comparison with 3-stage approach
        current_3stage_cost = len(test_opportunities) * 0.000205  # Current 3-stage cost
        savings = ((current_3stage_cost - result.total_cost) / current_3stage_cost) * 100
        
        print(f"\nCOST COMPARISON:")
        print(f"  Current 3-Stage Cost: ${current_3stage_cost:.6f}")
        print(f"  Unified Processor Cost: ${result.total_cost:.6f}")
        print(f"  Cost Savings: {savings:.1f}%")
        
        return {
            "success": True,
            "processing_time": end_time - start_time,
            "total_cost": result.total_cost,
            "processed_count": result.processed_count,
            "avg_confidence": avg_confidence,
            "avg_compatibility": avg_compatibility,
            "cost_savings_percent": savings,
            "web_success_rate": result.web_scraping_stats.get('success_rate', 0)
        }
        
    except Exception as e:
        end_time = time.time()
        print(f"\nTEST FAILED:")
        print(f"  Error: {str(e)}")
        print(f"  Processing Time: {end_time - start_time:.2f} seconds")
        
        return {
            "success": False,
            "error": str(e),
            "processing_time": end_time - start_time
        }


async def run_performance_tests():
    """Run performance tests with different batch sizes"""
    
    print(f"\n" + "=" * 50)
    print("PERFORMANCE SCALING TESTS")
    print("=" * 50)
    
    processor = AILiteUnifiedProcessor()
    test_profile = create_test_profile()
    
    batch_sizes = [5, 10, 20]
    results = {}
    
    for batch_size in batch_sizes:
        print(f"\nTesting batch size: {batch_size}")
        
        test_opportunities = create_test_opportunities(batch_size)
        
        request = UnifiedRequest(
            batch_id=f"perf_test_{batch_size}_{int(time.time())}",
            profile_context=test_profile,
            candidates=test_opportunities,
            analysis_mode="comprehensive",
            enable_web_scraping=True,
            cost_budget=0.001 * batch_size,  # Scale budget with batch size
            priority_level="standard"
        )
        
        start_time = time.time()
        
        try:
            result = await processor.execute(request)
            end_time = time.time()
            
            processing_time = end_time - start_time
            cost_per_candidate = result.total_cost / batch_size
            time_per_candidate = processing_time / batch_size
            
            results[batch_size] = {
                "success": True,
                "batch_size": batch_size,
                "processing_time": processing_time,
                "time_per_candidate": time_per_candidate,
                "total_cost": result.total_cost,
                "cost_per_candidate": cost_per_candidate,
                "processed_count": result.processed_count
            }
            
            print(f"  Processing Time: {processing_time:.2f}s ({time_per_candidate:.3f}s/candidate)")
            print(f"  Total Cost: ${result.total_cost:.6f} (${cost_per_candidate:.6f}/candidate)")
            print(f"  Success Rate: {result.processed_count}/{batch_size}")
            
        except Exception as e:
            end_time = time.time()
            results[batch_size] = {
                "success": False,
                "error": str(e),
                "processing_time": end_time - start_time
            }
            print(f"  FAILED: {str(e)}")
    
    # Performance analysis
    print(f"\nPERFORMANCE SUMMARY:")
    successful_tests = [r for r in results.values() if r.get("success")]
    
    if successful_tests:
        avg_time_per_candidate = sum(r["time_per_candidate"] for r in successful_tests) / len(successful_tests)
        avg_cost_per_candidate = sum(r["cost_per_candidate"] for r in successful_tests) / len(successful_tests)
        
        print(f"  Average Time per Candidate: {avg_time_per_candidate:.3f} seconds")
        print(f"  Average Cost per Candidate: ${avg_cost_per_candidate:.6f}")
        
        # Scalability assessment
        if len(successful_tests) > 1:
            min_batch = min(r["batch_size"] for r in successful_tests)
            max_batch = max(r["batch_size"] for r in successful_tests)
            
            min_result = next(r for r in successful_tests if r["batch_size"] == min_batch)
            max_result = next(r for r in successful_tests if r["batch_size"] == max_batch)
            
            scaling_factor = max_result["processing_time"] / min_result["processing_time"]
            batch_factor = max_batch / min_batch
            
            efficiency = batch_factor / scaling_factor
            print(f"  Scaling Efficiency: {efficiency:.2f} (1.0 = perfect linear scaling)")
    
    return results


async def main():
    """Main test execution"""
    
    print("AI-LITE UNIFIED PROCESSOR TESTING SUITE")
    print("=" * 60)
    print(f"Test Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Basic functionality test
    basic_result = await test_unified_processor()
    
    # Performance scaling tests
    performance_results = await run_performance_tests()
    
    # Summary
    print(f"\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    
    if basic_result["success"]:
        print(f"BASIC TEST: PASSED")
        print(f"  Cost Savings vs 3-Stage: {basic_result['cost_savings_percent']:.1f}%")
        print(f"  Average Confidence: {basic_result['avg_confidence']:.3f}")
        print(f"  Processing Speed: {basic_result['processing_time']:.2f}s for {basic_result['processed_count']} candidates")
    else:
        print(f"BASIC TEST: FAILED - {basic_result.get('error', 'Unknown error')}")
    
    successful_perf_tests = sum(1 for r in performance_results.values() if r.get("success"))
    total_perf_tests = len(performance_results)
    
    print(f"PERFORMANCE TESTS: {successful_perf_tests}/{total_perf_tests} PASSED")
    
    # Recommendations
    print(f"\nRECOMMENDATIONS:")
    
    if basic_result["success"] and basic_result["cost_savings_percent"] > 70:
        print("  * PROCEED WITH IMPLEMENTATION - Significant cost savings demonstrated")
    else:
        print("  * REVIEW ARCHITECTURE - Cost savings not meeting targets")
    
    if basic_result.get("avg_confidence", 0) >= 0.8:
        print("  * ANALYSIS QUALITY - Meets quality standards")
    else:
        print("  * IMPROVE ANALYSIS QUALITY - Below target confidence levels")
    
    if successful_perf_tests == total_perf_tests:
        print("  * SCALABILITY CONFIRMED - Ready for production testing")
    else:
        print("  * ADDRESS SCALABILITY ISSUES - Some batch sizes failing")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_data = {
        "basic_test": basic_result,
        "performance_tests": performance_results,
        "test_timestamp": timestamp,
        "summary": {
            "basic_test_passed": basic_result["success"],
            "performance_tests_passed": f"{successful_perf_tests}/{total_perf_tests}",
            "cost_savings_achieved": basic_result.get("cost_savings_percent", 0),
            "quality_level": basic_result.get("avg_confidence", 0)
        }
    }
    
    with open(f"unified_processor_test_results_{timestamp}.json", "w") as f:
        json.dump(results_data, f, indent=2, default=str)
    
    print(f"\nResults saved to: unified_processor_test_results_{timestamp}.json")


if __name__ == "__main__":
    asyncio.run(main())