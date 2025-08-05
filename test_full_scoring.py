#!/usr/bin/env python3
"""
Test Complete Scoring Workflow
Comprehensive test to verify end-to-end scoring functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.data_models import WorkflowConfig
from src.core.workflow_engine import get_workflow_engine


async def test_full_scoring():
    """Test complete scoring workflow with real EIN 541669652."""
    print("TESTING COMPLETE SCORING WORKFLOW")
    print("=" * 50)
    
    # Create test workflow config
    workflow_config = WorkflowConfig(
        workflow_id="full_scoring_test",
        target_ein="541669652",
        ntee_codes=["P81", "E31", "W70"],
        states=["VA"],
        min_revenue=50000,
        max_results=5,
        name="Full Scoring Test"
    )
    
    print(f"Workflow Configuration:")
    print(f"   ID: {workflow_config.workflow_id}")
    print(f"   Target EIN: {workflow_config.target_ein}")
    print(f"   Max Results: {workflow_config.max_results}")
    print()
    
    # Initialize workflow engine
    workflow_engine = get_workflow_engine()
    
    print(f"Starting Complete Workflow...")
    print()
    
    try:
        workflow_state = await workflow_engine.run_workflow(workflow_config)
        
        print(f"WORKFLOW RESULTS:")
        print(f"   Status: {workflow_state.status.value}")
        print(f"   Organizations Found: {workflow_state.organizations_found}")
        print(f"   Organizations Processed: {workflow_state.organizations_processed}")
        print(f"   Organizations Scored: {workflow_state.organizations_scored}")
        print(f"   Execution Time: {workflow_state.get_execution_time():.2f}s")
        print()
        
        print(f"PROCESSOR STATUS:")
        print(f"   Completed: {len(workflow_state.completed_processors)}")
        print(f"   Failed: {len(workflow_state.failed_processors)}")
        print(f"   Completed Processors: {workflow_state.completed_processors}")
        print(f"   Failed Processors: {workflow_state.failed_processors}")
        print()
        
        # Check for scoring output
        has_scores = False
        if workflow_state.processor_results:
            print(f"DETAILED PROCESSOR RESULTS:")
            for name, result in workflow_state.processor_results.items():
                success_icon = "[PASS]" if result.success else "[FAIL]"
                print(f"   {success_icon} {name}:")
                print(f"      Success: {result.success}")
                
                if result.execution_time:
                    print(f"      Time: {result.execution_time:.2f}s")
                
                if result.data and isinstance(result.data, dict):
                    print(f"      Data Keys: {list(result.data.keys())}")
                    
                    # Check for organizations with scores
                    if 'organizations' in result.data:
                        orgs = result.data['organizations']
                        if isinstance(orgs, list) and len(orgs) > 0:
                            print(f"      Organizations: {len(orgs)}")
                            
                            # Show sample organization if scored
                            sample_org = orgs[0]
                            if isinstance(sample_org, dict):
                                print(f"      Sample Organization:")
                                print(f"         EIN: {sample_org.get('ein', 'N/A')}")
                                print(f"         Name: {sample_org.get('name', 'N/A')}")
                                
                                # Check for scoring data
                                if 'composite_score' in sample_org:
                                    score = sample_org['composite_score']
                                    print(f"         *** COMPOSITE SCORE: {score:.3f} ***")
                                    has_scores = True
                                    
                                    if 'scoring_components' in sample_org:
                                        components = sample_org['scoring_components']
                                        print(f"         Score Breakdown:")
                                        for component, value in components.items():
                                            if isinstance(value, (int, float)):
                                                print(f"            {component}: {value:.3f}")
                    
                    # Show scoring stats
                    if 'scoring_stats' in result.data:
                        stats = result.data['scoring_stats']
                        print(f"      Scoring Stats: {stats}")
                
                if result.errors:
                    print(f"      ERRORS: {result.errors}")
                
                if result.warnings:
                    print(f"      WARNINGS: {result.warnings}")
                    
                print()
        
        # Final output check skipped for now
        
        # Final assessment
        if has_scores:
            print("*** SUCCESS: Scoring workflow is working! Organizations have composite scores. ***")
        elif workflow_state.organizations_processed > 0:
            print("PARTIAL: Workflow processed organizations but no scores generated.")
        else:
            print("ISSUE: No organizations were processed or scored.")
            
        return has_scores
        
    except Exception as e:
        print(f"Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_full_scoring())
    print()
    print("=" * 50)
    if success:
        print("SCORING TEST: PASSED - Composite scores are being generated!")
    else:
        print("SCORING TEST: FAILED - No scoring output detected")
    print("=" * 50)
    sys.exit(0 if success else 1)