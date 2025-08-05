#!/usr/bin/env python3
"""
Test Workflow without API Dependencies
Test the workflow starting from BMF filter (no ProPublica API required)
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.data_models import WorkflowConfig, ProcessorConfig
from src.core.workflow_engine import WorkflowEngine
from src.processors import get_processor


async def test_workflow_no_api():
    """Test workflow components that don't require external APIs."""
    print("Testing Workflow Components (No API Required)")
    print("=" * 60)
    
    # Test BMF Filter independently
    print("\n1. Testing BMF Filter...")
    print("-" * 30)
    
    try:
        # Create workflow config for BMF filter
        workflow_config = WorkflowConfig(
            workflow_id="test_bmf_only",
            ntee_codes=["P81", "E31", "W70"],  # Health, medical, welfare
            states=["VA"],  # Virginia only
            min_revenue=50000,  # $50K minimum
            max_results=10,  # Small test set
            name="BMF Filter Test"
        )
        
        # Get BMF filter processor
        bmf_processor = get_processor("bmf_filter")
        if not bmf_processor:
            print("ERROR: BMF filter processor not found")
            return False
        
        # Create processor config
        processor_config = ProcessorConfig(
            workflow_id=workflow_config.workflow_id,
            processor_name="bmf_filter",
            workflow_config=workflow_config
        )
        
        start_time = time.time()
        result = await bmf_processor.run(processor_config)
        execution_time = time.time() - start_time
        
        print(f"BMF Filter Result:")
        print(f"  Success: {result.success}")
        print(f"  Execution Time: {execution_time:.2f}s")
        
        if result.success and result.data:
            orgs = result.data.get("organizations", [])
            print(f"  Organizations Found: {len(orgs)}")
            
            if orgs:
                print(f"  Sample Organizations:")
                for i, org in enumerate(orgs[:3], 1):
                    print(f"    {i}. {org.get('name', 'Unknown')}")
                    print(f"       EIN: {org.get('ein', 'Unknown')}")
                    print(f"       State: {org.get('state', 'Unknown')}")
                    print(f"       NTEE: {org.get('ntee_code', 'Unknown')}")
                    if org.get('revenue'):
                        print(f"       Revenue: ${org.get('revenue'):,.0f}")
                    print()
        
        if result.errors:
            print(f"  Errors:")
            for error in result.errors:
                print(f"    - {error}")
        
        if result.warnings:
            print(f"  Warnings:")
            for warning in result.warnings:
                print(f"    - {warning}")
        
        if not result.success:
            print("BMF Filter test failed!")
            return False
        
        print("BMF Filter test PASSED!")
        
    except Exception as e:
        print(f"BMF Filter test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test Financial Scorer with BMF results
    print("\n2. Testing Financial Scorer...")
    print("-" * 30)
    
    try:
        # Use BMF results as input for financial scorer
        # Note: This would normally get data from previous step
        # For now, we'll test with mock data
        
        financial_processor = get_processor("financial_scorer")
        if not financial_processor:
            print("ERROR: Financial scorer processor not found")
            return False
        
        print("Financial Scorer processor found but requires ProPublica data.")
        print("Skipping financial scorer test (needs API integration).")
        
    except Exception as e:
        print(f"Financial scorer test failed: {e}")
    
    print("\n3. Testing XML Downloader...")
    print("-" * 30)
    
    try:
        xml_processor = get_processor("xml_downloader")
        if xml_processor:
            print("XML Downloader processor found but requires financial scorer results.")
            print("Skipping XML downloader test (needs previous steps).")
        else:
            print("ERROR: XML downloader processor not found")
    
    except Exception as e:
        print(f"XML downloader test failed: {e}")
    
    print("\n4. Testing Processor Registration...")
    print("-" * 30)
    
    try:
        from src.processors import list_processors, get_all_processors
        
        all_processors = list_processors()
        print(f"Registered Processors ({len(all_processors)}):")
        for proc_name in all_processors:
            processor = get_processor(proc_name)
            if processor:
                print(f"  - {proc_name}: {processor.metadata.description}")
        
        print("\nProcessor registration test PASSED!")
        
    except Exception as e:
        print(f"Processor registration test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("Workflow Component Tests Complete!")
    print("\nNext Steps:")
    print("1. Set up ProPublica API access")
    print("2. Test EIN lookup processor")
    print("3. Test complete workflow end-to-end")
    print("4. Test fallback PDF/OCR logic")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_workflow_no_api())
    sys.exit(0 if success else 1)