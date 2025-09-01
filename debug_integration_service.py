#!/usr/bin/env python3
"""
Debug script to isolate the integration service issue
"""

import asyncio
import sys
import os
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging to see details
logging.basicConfig(level=logging.DEBUG)

from src.processors.analysis.fact_extraction_integration_service import FactExtractionIntegrationService, ProcessorMigrationConfig

async def debug_integration():
    """Debug the integration service step by step"""
    
    print("Debugging Integration Service...")
    
    # Create integration service with debug config
    config = ProcessorMigrationConfig(
        enable_fact_extraction=True,
        enable_deterministic_scoring=True,
        fallback_to_legacy=False
    )
    
    service = FactExtractionIntegrationService(config=config)
    
    # Simple test data
    opportunity_data = {
        'title': 'Test Government Grant',
        'organization_name': 'Department of Health',
        'funding_amount': 500000,
        'focus_areas': ['health', 'research']
    }
    
    profile_data = {
        'name': 'Test Nonprofit',
        'ein': '123456789',
        'annual_revenue': 1000000,
        'ntee_codes': ['P20']
    }
    
    print("Input data prepared...")
    
    try:
        # Test the main processing method
        result = await service.process_opportunity(
            opportunity_data=opportunity_data,
            profile_data=profile_data,
            processor_stage="plan"
        )
        
        print(f"SUCCESS! Result type: {type(result)}")
        print(f"Success: {result.success}")
        print(f"Final score: {result.final_score}")
        print(f"Architecture used: {result.architecture_used}")
        
        if not result.success:
            print(f"Rationale: {result.score_rationale}")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_integration())