#!/usr/bin/env python3
"""
Test workflow output and scoring data
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.data_models import WorkflowConfig
from src.core.workflow_engine import get_workflow_engine


async def test_score_output():
    """Test workflow scoring output and data generation."""
    print("Testing Workflow Score Output")
    print("=" * 40)
    
    # Create test workflow config
    workflow_config = WorkflowConfig(
        workflow_id="score_output_test",
        target_ein="541669652",
        ntee_codes=["P81", "E31", "W70"],
        states=["VA"],
        min_revenue=50000,
        max_results=5,
        name="Score Output Test"
    )
    
    print(f"Workflow Config:")
    print(f"  ID: {workflow_config.workflow_id}")
    print(f"  Target EIN: {workflow_config.target_ein}")
    print(f"  Max Results: {workflow_config.max_results}")
    
    # Initialize workflow engine
    workflow_engine = get_workflow_engine()
    
    print(f"\nRunning workflow...")
    
    try:
        workflow_state = await workflow_engine.run_workflow(workflow_config)
        
        print(f"\nWorkflow Results:")
        print(f"  Status: {workflow_state.status}")
        print(f"  Organizations Found: {workflow_state.organizations_found}")
        print(f"  Organizations Processed: {workflow_state.organizations_processed}")
        print(f"  Organizations Scored: {workflow_state.organizations_scored}")
        print(f"  Completed Processors: {len(workflow_state.completed_processors)}")
        print(f"  Failed Processors: {len(workflow_state.failed_processors)}")
        
        if workflow_state.processor_results:
            print(f"\nProcessor Results Detail:")
            for name, result in workflow_state.processor_results.items():
                print(f"  {name}:")
                print(f"    Success: {result.success}")
                exec_time = result.execution_time or 0.0
                print(f"    Execution Time: {exec_time:.2f}s")
                if result.data and isinstance(result.data, dict):
                    print(f"    Data Keys: {list(result.data.keys())}")
                    
                    # Check for organizations data
                    if 'organizations' in result.data:
                        orgs = result.data['organizations']
                        print(f"    Organizations Count: {len(orgs) if isinstance(orgs, list) else 'N/A'}")
                        
                        # Show first organization if available
                        if isinstance(orgs, list) and len(orgs) > 0:
                            first_org = orgs[0]
                            print(f"    Sample Organization:")
                            if isinstance(first_org, dict):
                                if 'ein' in first_org:
                                    print(f"      EIN: {first_org.get('ein')}")
                                if 'name' in first_org:
                                    print(f"      Name: {first_org.get('name')}")
                                if 'composite_score' in first_org:
                                    print(f"      Score: {first_org.get('composite_score')}")
                                if 'revenue' in first_org:
                                    print(f"      Revenue: ${first_org.get('revenue'):,}")
                    
                    # Check for scoring stats
                    if 'scoring_stats' in result.data:
                        stats = result.data['scoring_stats']
                        print(f"    Scoring Stats: {stats}")
                
                if result.errors:
                    print(f"    Errors: {result.errors}")
                print()
        
        return True
        
    except Exception as e:
        print(f"Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_score_output())
    print(f"\nScore output test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)