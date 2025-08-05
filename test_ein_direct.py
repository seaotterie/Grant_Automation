#!/usr/bin/env python3
"""
Direct test of EIN lookup with ProPublica public API
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.data_models import WorkflowConfig, ProcessorConfig
from src.processors import get_processor


async def test_ein_direct():
    """Test EIN lookup directly with ProPublica public API."""
    print("Testing EIN Lookup with ProPublica Public API")
    print("=" * 50)
    
    # Test EIN
    test_ein = "541669652"
    print(f"Testing EIN: {test_ein}")
    
    try:
        # Get EIN lookup processor
        ein_processor = get_processor("ein_lookup")
        if not ein_processor:
            print("ERROR: EIN lookup processor not found")
            return False
        
        print("EIN lookup processor found!")
        
        # Create workflow config
        workflow_config = WorkflowConfig(
            workflow_id="test_ein_direct",
            target_ein=test_ein,
            name="Direct EIN Test"
        )
        
        # Create processor config
        processor_config = ProcessorConfig(
            workflow_id=workflow_config.workflow_id,
            processor_name="ein_lookup",
            workflow_config=workflow_config
        )
        
        print("Making ProPublica API request...")
        
        # Run EIN lookup
        result = await ein_processor.run(processor_config)
        
        print(f"\nResults:")
        print(f"Success: {result.success}")
        print(f"Execution Time: {result.execution_time:.2f}s" if result.execution_time else "N/A")
        
        if result.success and result.data:
            org_data = result.data.get("organization")
            if org_data:
                print(f"\nOrganization Found:")
                print(f"  Name: {org_data.get('name', 'Unknown')}")
                print(f"  EIN: {org_data.get('ein', 'Unknown')}")
                print(f"  State: {org_data.get('state', 'Unknown')}")
                print(f"  NTEE Code: {org_data.get('ntee_code', 'Unknown')}")
                print(f"  City: {org_data.get('city', 'Unknown')}")
                
                if org_data.get('revenue'):
                    print(f"  Revenue: ${org_data.get('revenue'):,.0f}")
                if org_data.get('assets'):
                    print(f"  Assets: ${org_data.get('assets'):,.0f}")
                
                if org_data.get('filing_years'):
                    years = org_data.get('filing_years', [])
                    print(f"  Filing Years: {len(years)} years - {years}")
                
                if org_data.get('mission_description'):
                    mission = org_data.get('mission_description', '')
                    print(f"  Mission: {mission[:100]}..." if len(mission) > 100 else f"  Mission: {mission}")
        
        if result.errors:
            print(f"\nErrors:")
            for error in result.errors:
                print(f"  - {error}")
        
        if result.warnings:
            print(f"\nWarnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        if result.metadata:
            print(f"\nMetadata:")
            for key, value in result.metadata.items():
                print(f"  {key}: {value}")
        
        return result.success
        
    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_ein_direct())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)