#!/usr/bin/env python3
"""
First Workflow Test
Test the complete grant research workflow with EIN 541669652
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.data_models import WorkflowConfig
from src.core.workflow_engine import WorkflowEngine


async def test_first_workflow():
    """Test the complete workflow with a real Virginia organization."""
    print("Starting First Workflow Test")
    print("=" * 60)
    
    # Create test workflow config
    workflow_config = WorkflowConfig(
        workflow_id="test_first_workflow_541669652",
        target_ein="541669652",  # Target EIN provided by user
        ntee_codes=["P81", "E31", "W70"],  # Health, medical, welfare
        states=["VA"],  # Virginia only
        min_revenue=50000,  # $50K minimum
        max_results=10,  # Small test set
        name="First Workflow Test - EIN 541669652"
    )
    
    print(f"Target EIN: {workflow_config.target_ein}")
    print(f"NTEE Codes: {workflow_config.ntee_codes}")
    print(f"State Filter: {workflow_config.states}")
    print(f"Min Revenue: ${workflow_config.min_revenue:,}")
    print(f"Max Results: {workflow_config.max_results}")
    print()
    
    # Initialize workflow engine
    workflow_engine = WorkflowEngine()
    
    try:
        print("Executing Complete Workflow...")
        print("-" * 40)
        
        # Run the complete workflow
        workflow_state = await workflow_engine.run_workflow(workflow_config)
        
        print(f"\nWorkflow Results:")
        print(f"Status: {workflow_state.status}")
        print(f"Start Time: {workflow_state.start_time}")
        print(f"End Time: {workflow_state.end_time}")
        if workflow_state.get_execution_time():
            print(f"Total Execution Time: {workflow_state.get_execution_time():.1f} seconds")
        
        print(f"\nCompleted Processors ({len(workflow_state.completed_processors)}):")
        for processor_name in workflow_state.completed_processors:
            result = workflow_state.processor_results[processor_name]
            print(f"  - {processor_name}: {result.execution_time:.2f}s" if result.execution_time else f"  - {processor_name}: completed")
        
        if workflow_state.failed_processors:
            print(f"\nFailed Processors ({len(workflow_state.failed_processors)}):")
            for processor_name in workflow_state.failed_processors:
                result = workflow_state.processor_results[processor_name]
                print(f"  - {processor_name}: {result.errors[0] if result.errors else 'Unknown error'}")
        
        if workflow_state.warnings:
            print(f"\nWarnings:")
            for warning in workflow_state.warnings:
                print(f"  - {warning}")
        
        # Show detailed results from key processors
        print(f"\nDetailed Results:")
        print("-" * 40)
        
        # EIN Lookup Results
        if "ein_lookup" in workflow_state.completed_processors:
            ein_result = workflow_state.processor_results["ein_lookup"]
            if ein_result.data and "organization" in ein_result.data:
                org = ein_result.data["organization"]
                print(f"Target Organization:")
                print(f"  Name: {org.get('name', 'Unknown')}")
                print(f"  EIN: {org.get('ein', 'Unknown')}")
                print(f"  State: {org.get('state', 'Unknown')}")
                print(f"  NTEE Code: {org.get('ntee_code', 'Unknown')}")
        
        # BMF Filter Results
        if "bmf_filter" in workflow_state.completed_processors:
            bmf_result = workflow_state.processor_results["bmf_filter"]
            if bmf_result.data and "organizations" in bmf_result.data:
                orgs = bmf_result.data["organizations"]
                print(f"\nBMF Filter Results:")
                print(f"  Organizations Found: {len(orgs)}")
                print(f"  Top 3 Organizations:")
                for i, org in enumerate(orgs[:3], 1):
                    print(f"    {i}. {org.get('name', 'Unknown')} (EIN: {org.get('ein', 'Unknown')})")
        
        # ProPublica Fetch Results
        if "propublica_fetch" in workflow_state.completed_processors:
            pp_result = workflow_state.processor_results["propublica_fetch"]
            if pp_result.data:
                stats = pp_result.data
                print(f"\nProPublica Fetch Results:")
                print(f"  Total Processed: {stats.get('total_processed', 0)}")
                print(f"  Successful Fetches: {stats.get('successful_fetches', 0)}")
                print(f"  Failed Fetches: {stats.get('failed_fetches', 0)}")
        
        # Financial Scorer Results
        if "financial_scorer" in workflow_state.completed_processors:
            scorer_result = workflow_state.processor_results["financial_scorer"]
            if scorer_result.data and "organizations" in scorer_result.data:
                scored_orgs = scorer_result.data["organizations"]
                print(f"\nFinancial Scoring Results:")
                print(f"  Organizations Scored: {len(scored_orgs)}")
                if scored_orgs:
                    # Show top 3 scored organizations
                    top_orgs = sorted(scored_orgs, key=lambda x: x.get('composite_score', 0), reverse=True)[:3]
                    print(f"  Top 3 Scored Organizations:")
                    for i, org in enumerate(top_orgs, 1):
                        score = org.get('composite_score', 0)
                        revenue = org.get('revenue', 0)
                        print(f"    {i}. {org.get('name', 'Unknown')}")
                        print(f"       Score: {score:.3f} | Revenue: ${revenue:,.0f}" if revenue else f"       Score: {score:.3f}")
        
        # XML Download Results
        if "xml_downloader" in workflow_state.completed_processors:
            xml_result = workflow_state.processor_results["xml_downloader"]
            if xml_result.data:
                stats = xml_result.data.get("download_stats", {})
                print(f"\nXML Download Results:")
                print(f"  Attempted Downloads: {stats.get('attempted_downloads', 0)}")
                print(f"  Successful Downloads: {stats.get('successful_downloads', 0)}")
                print(f"  Cached Files: {stats.get('cached_files', 0)}")
                print(f"  Failed Downloads: {stats.get('failed_downloads', 0)}")
        
        # Check for fallback processor results
        if "pdf_downloader" in workflow_state.completed_processors:
            print(f"\nPDF Fallback Results:")
            pdf_result = workflow_state.processor_results["pdf_downloader"]
            if pdf_result.data:
                stats = pdf_result.data.get("download_stats", {})
                print(f"  PDF Downloads: {stats.get('successful_pdf_downloads', 0)}")
        
        if "pdf_ocr" in workflow_state.completed_processors:
            print(f"\nOCR Fallback Results:")
            ocr_result = workflow_state.processor_results["pdf_ocr"]
            if ocr_result.data:
                stats = ocr_result.data.get("ocr_stats", {})
                print(f"  OCR Processing: {stats.get('successful_ocr', 0)} files")
                print(f"  Pages Processed: {stats.get('pages_processed', 0)}")
        
        print(f"\nFirst Workflow Test Complete!")
        print(f"Status: {workflow_state.status}")
        
        return workflow_state.status == "completed"
        
    except Exception as e:
        print(f"\nWorkflow Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_first_workflow())
    sys.exit(0 if success else 1)