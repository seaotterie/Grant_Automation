#!/usr/bin/env python3
"""
Test Repeatability Architecture

Validation script to test the new fact-extraction + deterministic scoring architecture
and demonstrate improved repeatability compared to legacy AI-based scoring.

This script validates the core user concern: "getting 10 different answers for the same opportunity"
"""

import asyncio
import json
import logging
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.processors.analysis.repeatability_testing_framework import RepeatabilityTestingFramework
from src.processors.analysis.enhanced_ai_lite_processor import EnhancedAILiteProcessor, ProcessingMode
from src.processors.analysis.fact_extraction_integration_service import ProcessorMigrationConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main test execution"""
    
    print("="*80)
    print("REPEATABILITY ARCHITECTURE VALIDATION TEST")
    print("="*80)
    print("Purpose: Validate that new architecture produces identical results for identical inputs")
    print("Issue: Addressing user concern about getting '10 different answers for the same opportunity'")
    print("="*80)
    
    # Initialize testing framework
    testing_framework = RepeatabilityTestingFramework()
    
    print(f"Initialized testing framework with {len(testing_framework.test_cases)} test cases")
    
    # Phase 1: Quick repeatability demonstration
    print("\n" + "="*60)
    print("PHASE 1: QUICK REPEATABILITY DEMONSTRATION")
    print("="*60)
    print("Testing same input 5 times with new architecture...")
    
    quick_result = await testing_framework.run_quick_repeatability_check(test_runs=5)
    
    print(f"\nQuick Test Results:")
    print(f"  Test Case: {quick_result.get('test_case', 'unknown')}")
    print(f"  Repeatability Quality: {quick_result.get('repeatability_quality', 'unknown').upper()}")
    print(f"  Perfect Repeatability: {quick_result.get('is_perfectly_repeatable', False)}")
    print(f"  Max Score Difference: {quick_result.get('max_difference', 0.0):.6f}")
    print(f"  Mean Score: {quick_result.get('mean_score', 0.0):.3f}")
    print(f"  Score Variance: {quick_result.get('score_variance', 0.0):.8f}")
    
    if quick_result.get('is_perfectly_repeatable', False):
        print("  [SUCCESS] PERFECT REPEATABILITY ACHIEVED - Identical results every time!")
    elif quick_result.get('max_difference', 1.0) < 0.01:
        print("  [SUCCESS] EXCELLENT REPEATABILITY - Less than 1% variation")
    else:
        print("  [WARNING] Some variation detected - may need architecture tuning")
    
    # Phase 2: Architecture comparison demonstration  
    print("\n" + "="*60)
    print("PHASE 2: ARCHITECTURE COMPARISON DEMONSTRATION")
    print("="*60)
    print("Comparing repeatability: New Architecture vs Legacy Architecture")
    
    # Test same opportunity with both architectures
    test_case = testing_framework.test_cases[0]  # Use first comprehensive test case
    
    print(f"\nTesting with: {test_case.description}")
    print(f"Organization: {test_case.profile_data['name']}")
    print(f"Opportunity: {test_case.opportunity_data['title']}")
    
    # Initialize processors
    new_processor = EnhancedAILiteProcessor(
        processing_mode=ProcessingMode.NEW_ARCHITECTURE,
        migration_config=ProcessorMigrationConfig(
            enable_fact_extraction=True,
            enable_deterministic_scoring=True,
            fallback_to_legacy=False
        )
    )
    
    legacy_processor = EnhancedAILiteProcessor(
        processing_mode=ProcessingMode.LEGACY_ARCHITECTURE
    )
    
    print(f"\nRunning NEW ARCHITECTURE 5 times...")
    new_scores = []
    for i in range(5):
        result = await new_processor.execute({
            'opportunity': test_case.opportunity_data,
            'profile': test_case.profile_data
        })
        new_scores.append(result.final_score)
        print(f"  Run {i+1}: {result.final_score:.6f} (confidence: {result.confidence_level})")
    
    print(f"\nRunning LEGACY ARCHITECTURE 5 times...")
    legacy_scores = []
    for i in range(5):
        result = await legacy_processor.execute({
            'opportunity': test_case.opportunity_data,
            'profile': test_case.profile_data
        })
        legacy_scores.append(result.final_score)
        print(f"  Run {i+1}: {result.final_score:.6f} (confidence: {result.confidence_level})")
    
    # Analyze comparison
    new_variance = max(new_scores) - min(new_scores) if new_scores else 0.0
    legacy_variance = max(legacy_scores) - min(legacy_scores) if legacy_scores else 0.0
    
    print(f"\n[ARCHITECTURE COMPARISON RESULTS]:")
    print(f"  New Architecture:")
    print(f"    Score Range: {min(new_scores):.6f} - {max(new_scores):.6f}")
    print(f"    Variance: {new_variance:.6f}")
    print(f"    Identical Results: {'[YES]' if new_variance == 0.0 else '[NO]'}")
    
    print(f"  Legacy Architecture:")
    print(f"    Score Range: {min(legacy_scores):.6f} - {max(legacy_scores):.6f}")
    print(f"    Variance: {legacy_variance:.6f}")
    print(f"    Identical Results: {'[YES]' if legacy_variance == 0.0 else '[NO]'}")
    
    improvement_ratio = (legacy_variance / new_variance) if new_variance > 0 else float('inf')
    
    print(f"\n[REPEATABILITY IMPROVEMENT]:")
    if new_variance == 0.0 and legacy_variance > 0.0:
        print(f"  [SUCCESS] PERFECT IMPROVEMENT: New architecture eliminates ALL variation")
        print(f"  Legacy had {legacy_variance:.6f} variance, New has ZERO variance")
    elif new_variance < legacy_variance:
        print(f"  [SUCCESS] SIGNIFICANT IMPROVEMENT: {improvement_ratio:.1f}x more consistent")
        print(f"  Variance reduced from {legacy_variance:.6f} to {new_variance:.6f}")
    else:
        print(f"  [WARNING] No improvement detected - architecture may need tuning")
    
    # Phase 3: Comprehensive test suite (optional)
    user_input = input(f"\n{'='*60}\nRun comprehensive test suite? (5 test cases, cross-architecture) [y/N]: ")
    
    if user_input.lower().startswith('y'):
        print(f"\n{'='*60}")
        print("PHASE 3: COMPREHENSIVE TEST SUITE")
        print("="*60)
        print("Running full repeatability test suite...")
        print("This may take 2-3 minutes...")
        
        suite_results = await testing_framework.run_repeatability_test_suite(
            test_runs=3,
            include_cross_architecture=True
        )
        
        print(f"\n[COMPREHENSIVE TEST RESULTS]:")
        print(f"  Total Test Cases: {suite_results.total_test_cases}")
        print(f"  Successful Tests: {suite_results.successful_tests}")
        print(f"  Failed Tests: {suite_results.failed_tests}")
        print(f"  Overall Repeatability Score: {suite_results.overall_repeatability_score:.3f}/1.0")
        print(f"  Perfect Repeatability Count: {suite_results.perfectly_repeatable_count}")
        
        print(f"\n[QUALITY DISTRIBUTION]:")
        for quality, count in suite_results.repeatability_quality_distribution.items():
            if count > 0:
                print(f"    {quality.title()}: {count} tests")
        
        if suite_results.new_architecture_performance:
            new_perf = suite_results.new_architecture_performance
            print(f"\n[NEW ARCHITECTURE PERFORMANCE]:")
            print(f"    Mean Repeatability Score: {new_perf.get('mean_repeatability_score', 0):.3f}")
            print(f"    Perfect Repeatability Rate: {new_perf.get('perfect_repeatability_rate', 0)*100:.1f}%")
            print(f"    Mean Processing Time: {new_perf.get('mean_processing_time', 0):.3f}s")
        
        if suite_results.legacy_architecture_performance:
            legacy_perf = suite_results.legacy_architecture_performance
            print(f"\n[LEGACY ARCHITECTURE PERFORMANCE]:")
            print(f"    Mean Repeatability Score: {legacy_perf.get('mean_repeatability_score', 0):.3f}")
            print(f"    Perfect Repeatability Rate: {legacy_perf.get('perfect_repeatability_rate', 0)*100:.1f}%")
            print(f"    Mean Processing Time: {legacy_perf.get('mean_processing_time', 0):.3f}s")
        
        if suite_results.architecture_difference_stats:
            diff_stats = suite_results.architecture_difference_stats
            print(f"\n[CROSS-ARCHITECTURE DIFFERENCES]:")
            print(f"    Mean Difference: {diff_stats.get('mean_difference', 0):.4f}")
            print(f"    Max Difference: {diff_stats.get('max_difference', 0):.4f}")
            print(f"    Significant Differences: {diff_stats.get('significant_differences', 0)}")
        
        # Save detailed results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"repeatability_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(suite_results.dict(), f, indent=2, default=str)
        
        print(f"\n[FILE SAVED] Detailed results saved to: {results_file}")
    
    # Final summary
    print(f"\n{'='*80}")
    print("REPEATABILITY ARCHITECTURE VALIDATION COMPLETE")
    print("="*80)
    
    if new_variance == 0.0:
        print("[SUCCESS] New architecture achieves PERFECT repeatability!")
        print("   [SUCCESS] Same input -> Same output every time")
        print("   [SUCCESS] Eliminates the '10 different answers' problem")
        print("   [SUCCESS] Ready for production deployment")
    elif new_variance < 0.01:
        print("[SUCCESS] New architecture achieves excellent repeatability!")
        print(f"   [INFO] Variance reduced to <1%: {new_variance:.6f}")
        print("   [SUCCESS] Significantly more reliable than legacy architecture")
    else:
        print("[WARNING] PARTIAL SUCCESS: Some improvement achieved")
        print(f"   [INFO] Variance: {new_variance:.6f}")
        print("   [WARNING] May need architecture parameter tuning")
    
    print(f"\n[NEXT STEPS]:")
    print("   1. Deploy new architecture to production")
    print("   2. Monitor repeatability in real-world usage")
    print("   3. Fine-tune scoring weights based on user feedback")
    print("   4. Update web interface to use new architecture")
    
    print(f"\n[ARCHITECTURE BENEFITS]:")
    print("   • Fact extraction (AI) + Deterministic scoring (local)")
    print("   • Opportunity-type aware prompts (government/nonprofit/corporate)")
    print("   • Confidence scoring based on data availability")
    print("   • Audit trails showing how scores were calculated")
    print("   • Backward compatibility with existing systems")
    
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Test failed with error: {str(e)}")
        logger.exception("Test execution failed")
    
    print(f"\nTest completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")