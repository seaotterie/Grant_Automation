#!/usr/bin/env python3
"""
Detailed test of BMF Filter Processor
Shows detailed results from processing the Virginia BMF data.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.data_models import WorkflowConfig, ProcessorConfig
from src.processors.filtering.bmf_filter import BMFFilterProcessor


async def test_bmf_detailed():
    """Test the BMF filter processor with detailed output."""
    print("Detailed BMF Filter Test")
    print("=" * 50)
    
    # Create test workflow config
    workflow_config = WorkflowConfig(
        workflow_id="test_bmf_detailed",
        target_ein="131624868",
        ntee_codes=["P81", "E31", "W70"],  # Health, medical, welfare
        states=["VA"],  # Virginia only
        min_revenue=10000,  # Lower threshold to catch more orgs
        max_results=10,  # Show more results
        name="Detailed BMF Test"
    )
    
    # Create processor config
    processor_config = ProcessorConfig(
        workflow_id=workflow_config.workflow_id,
        processor_name="bmf_filter",
        workflow_config=workflow_config
    )
    
    # Create and run processor
    processor = BMFFilterProcessor()
    
    print(f"Testing with criteria:")
    print(f"  NTEE Codes: {workflow_config.ntee_codes}")
    print(f"  States: {workflow_config.states}")
    print(f"  Min Revenue: ${workflow_config.min_revenue:,}")
    print(f"  Max Results: {workflow_config.max_results}")
    print()
    
    try:
        result = await processor.run(processor_config)
        
        print(f"Success: {result.success}")
        print(f"Execution time: {result.execution_time:.2f}s" if result.execution_time else "N/A")
        print()
        
        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")
            print()
        
        if result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
            print()
        
        if result.data and 'organizations' in result.data:
            orgs = result.data['organizations']
            print(f"Found {len(orgs)} organizations:")
            print()
            
            for i, org in enumerate(orgs, 1):
                print(f"{i}. {org['name']}")
                print(f"   EIN: {org['ein']}")
                print(f"   Location: {org.get('city', 'Unknown')}, {org['state']}")
                print(f"   NTEE Code: {org['ntee_code']}")
                if org.get('revenue'):
                    print(f"   Revenue: ${org['revenue']:,.0f}")
                if org.get('assets'):
                    print(f"   Assets: ${org['assets']:,.0f}")
                
                # Show processing notes
                if org.get('processing_notes'):
                    print(f"   Notes: {len(org['processing_notes'])} processing notes")
                    for note in org['processing_notes'][:3]:  # Show first 3 notes
                        print(f"     - {note}")
                print()
        else:
            print("No organizations found")
        
        if result.metadata:
            print("Metadata:")
            for key, value in result.metadata.items():
                print(f"  {key}: {value}")
    
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_bmf_detailed())