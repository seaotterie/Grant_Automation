#!/usr/bin/env python3
"""
Debug workflow execution to see why processors aren't running
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.data_models import WorkflowConfig
from src.core.workflow_engine import WorkflowEngine


async def debug_workflow():
    """Debug why the workflow isn't executing processors."""
    print("Debugging Workflow Execution")
    print("=" * 40)
    
    # Create test workflow config
    workflow_config = WorkflowConfig(
        workflow_id="debug_workflow",
        target_ein="541669652",
        ntee_codes=["P81", "E31", "W70"],
        states=["VA"],
        min_revenue=50000,
        max_results=10,
        name="Debug Workflow Test"
    )
    
    print(f"Workflow Config:")
    print(f"  ID: {workflow_config.workflow_id}")
    print(f"  Target EIN: {workflow_config.target_ein}")
    print(f"  Processors to run: {workflow_config.processors_to_run}")
    
    # Initialize workflow engine
    workflow_engine = WorkflowEngine()
    
    print(f"\nWorkflow Engine Info:")
    print(f"  Registered processors: {len(workflow_engine.registry.list_processors())}")
    
    # Check processor registration
    from src.processors import list_processors, get_processor
    all_processors = list_processors()
    print(f"  Available processors: {all_processors}")
    
    # Check dependency resolution
    try:
        execution_order = workflow_engine.dependency_resolver.get_standard_execution_order()
        print(f"  Standard execution order: {execution_order}")
    except Exception as e:
        print(f"  Error getting execution order: {e}")
    
    # Try to run the workflow with debug info
    print(f"\nStarting workflow execution...")
    
    try:
        workflow_state = await workflow_engine.run_workflow(workflow_config)
        
        print(f"\nWorkflow completed:")
        print(f"  Status: {workflow_state.status}")
        print(f"  Completed processors: {len(workflow_state.completed_processors)}")
        print(f"  Failed processors: {len(workflow_state.failed_processors)}")
        print(f"  Errors: {workflow_state.errors}")
        print(f"  Warnings: {workflow_state.warnings}")
        
        if workflow_state.processor_results:
            print(f"\nProcessor Results:")
            for name, result in workflow_state.processor_results.items():
                print(f"  {name}: Success={result.success}, Errors={len(result.errors)}")
        
        return True
        
    except Exception as e:
        print(f"Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(debug_workflow())
    print(f"\nDebug test {'completed' if success else 'failed'}")
    sys.exit(0 if success else 1)