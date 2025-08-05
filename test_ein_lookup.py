#!/usr/bin/env python3
"""
Test EIN Lookup Processor
Simple test script to verify the EIN lookup processor works.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.data_models import WorkflowConfig, ProcessorConfig
from src.processors.lookup.ein_lookup import EINLookupProcessor


async def test_ein_lookup():
    """Test the EIN lookup processor with a sample EIN."""
    print("Testing EIN Lookup Processor...")
    print("=" * 50)
    
    # Create test workflow config
    workflow_config = WorkflowConfig(
        workflow_id="test_ein_lookup",
        target_ein="131624868",  # Sample EIN - you can change this to test with a real one
        name="EIN Lookup Test"
    )
    
    # Create processor config
    processor_config = ProcessorConfig(
        workflow_id=workflow_config.workflow_id,
        processor_name="ein_lookup",
        workflow_config=workflow_config
    )
    
    # Create and run processor
    processor = EINLookupProcessor()
    
    print(f"Testing EIN: {workflow_config.target_ein}")
    print("Note: This test requires a ProPublica API key to work fully.")
    print("Without an API key, it will test validation and fail gracefully.")
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
            print("  Data keys:", list(result.data.keys()))
            if 'organization_name' in result.data:
                print(f"  Organization: {result.data['organization_name']}")
            if 'state' in result.data:
                print(f"  State: {result.data['state']}")
        
        if result.metadata:
            print("  Metadata:")
            for key, value in result.metadata.items():
                print(f"    {key}: {value}")
        
        print()
        if result.success:
            print("PASS: EIN Lookup Processor test PASSED!")
        else:
            print("INFO: EIN Lookup Processor test failed (expected if no API key)")
    
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_ein_lookup())