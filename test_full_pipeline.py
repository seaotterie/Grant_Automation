#!/usr/bin/env python3
"""
Test Full Multi-Track Pipeline
Simple test of the complete government-integrated pipeline.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.workflow_engine import get_workflow_engine
from src.core.data_models import WorkflowConfig
from src.processors.registry import register_all_processors


async def test_full_pipeline():
    """Test the complete multi-track pipeline."""
    
    print("=== CATALYNX PHASE 2 PIPELINE TEST ===")
    print("Testing: Organizations + Government Opportunities + Awards\n")
    
    # Register processors
    registered_count = register_all_processors()
    print(f"Registered {registered_count} processors\n")
    
    # Create test configuration
    config = WorkflowConfig(
        workflow_id=f'pipeline_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        name='Phase 2 Multi-Track Pipeline Test',
        max_results=5,  # Small test
        states=['VA'],
        ntee_codes=['P81'],  # Health focus
        min_revenue=50000
    )
    
    print(f"Workflow ID: {config.workflow_id}")
    print(f"Configuration: {config.states[0]}, {config.ntee_codes[0]}, ${config.min_revenue:,}+\n")
    
    # Run workflow
    engine = get_workflow_engine()
    
    def progress_callback(workflow_id: str, progress: float, message: str):
        print(f"[{progress:5.1f}%] {message}")
    
    engine.add_progress_callback(progress_callback)
    
    try:
        print("Starting workflow execution...\n")
        state = await engine.run_workflow(config)
        
        print(f"\n=== RESULTS ===")
        print(f"Status: {state.status.value}")
        print(f"Execution Time: {state.get_execution_time():.2f} seconds")
        print(f"Organizations Processed: {state.organizations_processed}")
        print(f"Completed Processors: {len(state.completed_processors)}")
        print(f"Failed Processors: {len(state.failed_processors)}")
        
        # Show processor results
        print(f"\n=== PROCESSOR RESULTS ===")
        for proc_name in state.completed_processors:
            if proc_name in state.processor_results:
                result = state.processor_results[proc_name]
                if result.data:
                    data_info = {}
                    for key, value in result.data.items():
                        if isinstance(value, list):
                            data_info[key] = f"{len(value)} items"
                        else:
                            data_info[key] = str(value)[:50]
                    print(f"[OK] {proc_name}: {data_info}")
                else:
                    print(f"[OK] {proc_name}: (no data)")
            else:
                print(f"[OK] {proc_name}: (completed)")
        
        if state.failed_processors:
            print(f"\n=== FAILED PROCESSORS ===")
            for proc_name in state.failed_processors:
                if proc_name in state.processor_results:
                    result = state.processor_results[proc_name]
                    print(f"[FAIL] {proc_name}: {result.errors}")
                else:
                    print(f"[FAIL] {proc_name}: (unknown error)")
        
        # Check for government track results
        print(f"\n=== GOVERNMENT TRACK RESULTS ===")
        
        if state.has_processor_succeeded('grants_gov_fetch'):
            grants_data = state.get_processor_data('grants_gov_fetch')
            if grants_data:
                opps = grants_data.get('opportunities', [])
                print(f"Federal Opportunities Found: {len(opps)}")
        else:
            print("Grants.gov fetch: Not completed or failed")
        
        if state.has_processor_succeeded('usaspending_fetch'):
            usa_data = state.get_processor_data('usaspending_fetch')
            if usa_data:
                awards_total = usa_data.get('total_awards_found', 0)
                funding_total = usa_data.get('total_funding_found', 0)
                print(f"Historical Awards Found: {awards_total}")
                print(f"Historical Funding Total: ${funding_total:,.2f}")
        else:
            print("USASpending fetch: Not completed or failed")
        
        if state.has_processor_succeeded('government_opportunity_scorer'):
            scorer_data = state.get_processor_data('government_opportunity_scorer')
            if scorer_data:
                matches = scorer_data.get('opportunity_matches', [])
                print(f"Opportunity Matches Generated: {len(matches)}")
                
                if matches:
                    high_matches = len([m for m in matches if m.get('recommendation_level') == 'high'])
                    medium_matches = len([m for m in matches if m.get('recommendation_level') == 'medium'])
                    print(f"  - High Priority: {high_matches}")
                    print(f"  - Medium Priority: {medium_matches}")
        else:
            print("Government Opportunity Scorer: Not completed or failed")
        
        # Overall assessment
        print(f"\n=== ASSESSMENT ===")
        if state.status.value == "completed":
            print("SUCCESS: Multi-track pipeline completed successfully!")
            
            # Check if government track worked
            gov_success = (
                state.has_processor_succeeded('grants_gov_fetch') and
                state.has_processor_succeeded('usaspending_fetch') and 
                state.has_processor_succeeded('government_opportunity_scorer')
            )
            
            if gov_success:
                print("SUCCESS: Government track fully operational!")
                print("Phase 2 Multi-Track Discovery: COMPLETE")
            else:
                print("WARNING: Government track partially operational")
                print("Check API keys and network connectivity")
        else:
            print(f"FAILURE: Pipeline failed with status {state.status.value}")
        
    except Exception as e:
        print(f"ERROR: Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())