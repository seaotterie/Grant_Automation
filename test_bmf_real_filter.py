#!/usr/bin/env python3
"""
Test the actual BMF filter processor to see how many records it returns.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.append('.')

from src.processors.filtering.bmf_filter import BMFFilterProcessor
from src.core.data_models import ProcessorConfig, WorkflowConfig

async def test_bmf_filter():
    """Test the BMF filter processor with your exact criteria."""
    print("Testing BMF Filter Processor...")
    
    # Create proper config
    config = ProcessorConfig(
        workflow_id="test_workflow",
        processor_name="bmf_filter",
        workflow_config=WorkflowConfig(
            target_ein='541669652',
            ntee_codes=['P81', 'E31', 'P30', 'W70'],
            state_filter='VA',
            max_results=100,  # Set high to see how many we get
            min_revenue=50000
        )
    )
    
    processor = BMFFilterProcessor()
    
    try:
        result = await processor.execute(config)
        
        print(f"Success: {result.success}")
        
        if result.success:
            orgs = result.data.get('organizations', [])
            print(f"Organizations found: {len(orgs)}")
            print(f"Max results limit: {config.workflow_config.max_results}")
            
            print(f"\nFirst 10 organizations:")
            for i, org in enumerate(orgs[:10]):
                revenue = org.get('revenue', 'N/A')
                print(f"  {i+1:2d}. {org['ein']} - {org['name'][:50]} - {org['ntee_code']} - Revenue: {revenue}")
            
            if len(orgs) > 10:
                print(f"  ... and {len(orgs) - 10} more")
            
            # Check criteria application
            print(f"\nCriteria Analysis:")
            print(f"NTEE codes: {config.workflow_config.ntee_codes}")
            print(f"State filter: {config.workflow_config.state_filter}")
            print(f"Min revenue: {config.workflow_config.min_revenue}")
            
            # Check revenue filtering
            orgs_with_revenue = [o for o in orgs if o.get('revenue') is not None]
            orgs_above_min = [o for o in orgs_with_revenue if o.get('revenue', 0) >= config.workflow_config.min_revenue]
            
            print(f"Organizations with revenue data: {len(orgs_with_revenue)}")
            print(f"Organizations above min revenue: {len(orgs_above_min)}")
            print(f"Organizations without revenue data: {len(orgs) - len(orgs_with_revenue)}")
            
        else:
            print(f"Errors: {result.errors}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bmf_filter())