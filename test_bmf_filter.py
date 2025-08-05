#!/usr/bin/env python3
"""
Test BMF Filter Processor
Simple test script to verify the BMF filter processor works.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.data_models import WorkflowConfig, ProcessorConfig
from src.processors.filtering.bmf_filter import BMFFilterProcessor


async def test_bmf_filter():
    """Test the BMF filter processor."""
    print("Testing BMF Filter Processor...")
    print("=" * 50)
    
    # Create test workflow config
    workflow_config = WorkflowConfig(
        workflow_id="test_bmf_filter",
        target_ein="131624868",
        ntee_codes=["P81", "E31"],  # Health organizations
        states=["VA"],  # Virginia only
        min_revenue=50000,  # $50K minimum
        max_results=5,  # Small test
        name="BMF Filter Test"
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
    print("Note: This test will download the IRS Business Master File (~several MB)")
    print("The first run may take a few minutes to download and process the file.")
    print()
    
    try:
        result = await processor.run(processor_config)
        
        print("Processor Result:")
        print(f"  Success: {result.success}")
        print(f"  Processor: {result.processor_name}")
        print(f"  Execution time: {result.execution_time:.2f}s" if result.execution_time else "N/A")
        
        if result.errors:
            print("  Errors:")
            for error in result.errors:
                print(f"    - {error}")
        
        if result.warnings:
            print("  Warnings:")
            for warning in result.warnings:
                print(f"    - {warning}")
        
        if result.data:
            print("  Data:")
            orgs_count = result.data.get('organizations_count', 0)
            print(f"    Organizations found: {orgs_count}")
            
            if 'organizations' in result.data and result.data['organizations']:
                print("    Sample organizations:")
                for i, org in enumerate(result.data['organizations'][:3]):  # Show first 3
                    print(f"      {i+1}. {org['name']} ({org['state']}) - NTEE: {org['ntee_code']}")
                    if org.get('revenue'):
                        print(f"         Revenue: ${org['revenue']:,.0f}")
        
        if result.metadata:
            print("  Metadata:")
            for key, value in result.metadata.items():
                if key == 'filter_criteria':
                    print(f"    {key}: {value}")
                else:
                    print(f"    {key}: {value}")
        
        print()
        if result.success:
            print("PASS: BMF Filter Processor test PASSED!")
        else:
            print("INFO: BMF Filter Processor test failed")
    
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_bmf_filter())