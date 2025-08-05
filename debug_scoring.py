#!/usr/bin/env python3
"""
Debug Scoring Issues
Investigate why organizations are getting low scores and what filing data is available.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.workflow_engine import WorkflowEngine
from src.core.data_models import WorkflowConfig
import json

async def debug_scoring():
    """Debug the scoring pipeline to understand why scores are low."""
    print("DEBUG: Catalynx Scoring Analysis")
    print("=" * 50)
    
    # Run a small test workflow
    workflow_engine = WorkflowEngine()
    
    config = WorkflowConfig(
        workflow_id="debug_scoring",
        name="Debug Scoring Test",
        target_ein="541669652",
        ntee_codes=["E21", "E30", "E31", "E32", "F30", "F32", "P81"],
        states=["VA"],
        min_revenue=50000,
        max_results=3  # Small sample for debugging
    )
    
    # Run just the core processors
    processors = ["ein_lookup", "bmf_filter", "propublica_fetch", "financial_scorer"]
    
    print("Running processors:", processors)
    
    # Create workflow and run it
    workflow_state = workflow_engine.create_workflow(config)
    result = await workflow_engine.run_workflow(config)
    
    if not result.success:
        print("Workflow failed!")
        for error in result.errors:
            print(f"ERROR: {error}")
        return
    
    print("\nDEBUGGING RESULTS:")
    print("-" * 30)
    
    # Examine each processor's output
    for processor_name in processors:
        if processor_name in result.processor_results:
            processor_result = result.processor_results[processor_name]
            print(f"\n{processor_name.upper()}:")
            print(f"  Success: {processor_result.success}")
            print(f"  Execution Time: {processor_result.execution_time:.2f}s")
            
            if processor_result.data:
                data = processor_result.data
                
                if processor_name == "propublica_fetch":
                    organizations = data.get("organizations", [])
                    print(f"  Organizations returned: {len(organizations)}")
                    
                    if organizations:
                        org = organizations[0]
                        print(f"  Sample organization: {org.get('name', 'Unknown')}")
                        print(f"  Has filing_data: {'filing_data' in org}")
                        
                        if 'filing_data' in org:
                            filing_data = org['filing_data']
                            filings = filing_data.get('filings', [])
                            print(f"  Number of filings: {len(filings)}")
                            
                            if filings:
                                sample_filing = filings[0]
                                print(f"  Sample filing keys: {list(sample_filing.keys())}")
                                print(f"  Tax year: {sample_filing.get('tax_prd_yr', 'N/A')}")
                                print(f"  Revenue: {sample_filing.get('totrevenue', 'N/A')}")
                                print(f"  Assets: {sample_filing.get('totassetsend', 'N/A')}")
                
                elif processor_name == "financial_scorer":
                    organizations = data.get("organizations", [])
                    scoring_stats = data.get("scoring_stats", {})
                    
                    print(f"  Organizations scored: {len(organizations)}")
                    print(f"  Fully scored: {scoring_stats.get('fully_scored', 0)}")
                    print(f"  Partially scored: {scoring_stats.get('partially_scored', 0)}")
                    
                    if organizations:
                        org = organizations[0]
                        print(f"  Sample organization: {org.get('name', 'Unknown')}")
                        print(f"  Composite score: {org.get('composite_score', 'N/A')}")
                        
                        scoring_components = org.get('scoring_components', {})
                        if scoring_components:
                            print("  Score breakdown:")
                            for component, score in scoring_components.items():
                                print(f"    {component}: {score}")
    
    # Now let's look at specific issues
    print("\n" + "=" * 50)
    print("SPECIFIC ISSUE ANALYSIS:")
    
    if "propublica_fetch" in result.processor_results:
        pp_result = result.processor_results["propublica_fetch"]
        if pp_result.success and pp_result.data:
            organizations = pp_result.data.get("organizations", [])
            
            print(f"\nProPublica Fetch Analysis:")
            print(f"Organizations processed: {len(organizations)}")
            
            for i, org in enumerate(organizations):
                print(f"\nOrganization {i+1}: {org.get('name', 'Unknown')}")
                print(f"  EIN: {org.get('ein', 'N/A')}")
                
                # Check filing data
                has_filing_data = 'filing_data' in org
                print(f"  Has filing_data attribute: {has_filing_data}")
                
                if has_filing_data:
                    filing_data = org['filing_data']
                    filings = filing_data.get('filings', [])
                    print(f"  Number of filings: {len(filings)}")
                    
                    if filings:
                        for j, filing in enumerate(filings[:2]):  # Show first 2 filings
                            print(f"    Filing {j+1}:")
                            print(f"      Tax year: {filing.get('tax_prd_yr', 'N/A')}")
                            print(f"      Revenue: {filing.get('totrevenue', 'N/A')}")
                            print(f"      Assets: {filing.get('totassetsend', 'N/A')}")
                            print(f"      Program expenses: {filing.get('totfuncexpns', 'N/A')}")
                            print(f"      Total expenses: {filing.get('totexpns', 'N/A')}")
    
    # Save debug results
    debug_dir = Path("debug_results")
    debug_dir.mkdir(exist_ok=True)
    
    debug_file = debug_dir / "scoring_debug.json"
    with open(debug_file, 'w') as f:
        debug_data = {}
        for processor_name, processor_result in result.processor_results.items():
            debug_data[processor_name] = {
                "success": processor_result.success,
                "execution_time": processor_result.execution_time,
                "data": processor_result.data,
                "errors": processor_result.errors
            }
        json.dump(debug_data, f, indent=2, default=str)
    
    print(f"\nDebug data saved to: {debug_file}")

if __name__ == "__main__":
    asyncio.run(debug_scoring())