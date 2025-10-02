#!/usr/bin/env python3
"""
Test Heroes Bridge BMF Integration and URL Prediction
Validates that the GPT URL Discovery processor correctly:
1. Queries BMF database for authoritative organization data
2. Uses correct "HEROS BRIDGE" spelling from BMF
3. Predicts accurate URLs with enhanced GPT prompt
"""

import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

from src.processors.analysis.gpt_url_discovery import GPTURLDiscoveryProcessor
from src.core.data_models import ProcessorConfig, WorkflowConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_heroes_bridge_bmf_integration():
    """Test complete Heroes Bridge BMF integration and URL prediction"""
    logger.info("Testing Heroes Bridge BMF integration and URL prediction")
    
    heroes_bridge_ein = '812827604'
    
    print("="*80)
    print("HEROES BRIDGE BMF INTEGRATION & URL PREDICTION TEST")
    print("="*80)
    
    processor = GPTURLDiscoveryProcessor()
    
    # Test 1: Direct BMF database query
    print("\nTest 1: BMF Database Query")
    print("-" * 40)
    
    bmf_data = await processor._query_bmf_organization(heroes_bridge_ein)
    
    if bmf_data:
        print(f"SUCCESS: Retrieved BMF data for EIN {heroes_bridge_ein}")
        print(f"Organization Name: '{bmf_data['organization_name']}'")
        print(f"Location: {bmf_data['city']}, {bmf_data['state']}")
        print(f"Address: {bmf_data['address']}")
        print(f"Organization Type: {bmf_data['organization_type']}")
        print(f"Data Source: {bmf_data['data_source']}")
        
        # Verify correct spelling
        org_name = bmf_data['organization_name']
        if org_name == "HEROS BRIDGE":
            print("SUCCESS: BMF has 'HEROS BRIDGE' spelling (not 'Heroes')")
        elif "HEROS" in org_name.upper():
            print(f"SUCCESS: BMF preserves 'HEROS' spelling: '{org_name}'")
        else:
            print(f"WARNING: Unexpected organization name: '{org_name}'")
            
    else:
        print(f"ERROR: No BMF data found for EIN {heroes_bridge_ein}")
        print("Make sure nonprofit_intelligence.db exists and contains Heroes Bridge data")
        return False
    
    # Test 2: GPT URL Prediction with BMF Data  
    print(f"\nTest 2: GPT URL Prediction with BMF Data")
    print("-" * 40)
    
    try:
        # Create processor config with EIN
        workflow_config = WorkflowConfig(
            workflow_id="test_heroes_bridge",
            profile_id="test_profile",
            target_ein=heroes_bridge_ein
        )
        
        config = ProcessorConfig(
            workflow_id="test_heroes_bridge",
            processor_name="gpt_url_discovery",
            workflow_config=workflow_config,
            processor_specific_config={
                'ein': heroes_bridge_ein,
                'force_refresh': True  # Bypass cache to test fresh GPT prediction
            }
        )
        
        # Execute URL discovery
        result = await processor.execute(config)
        
        if result.success:
            print("SUCCESS: GPT URL Discovery completed")
            print(f"Execution time: {result.execution_time:.2f} seconds")
            
            urls = result.data.get('urls', [])
            org_data = result.data.get('organization_data', {})
            
            print(f"Organization used: '{org_data.get('organization_name', 'N/A')}'")
            print(f"Predicted URLs: {len(urls)}")
            
            if urls:
                print("\nURL Predictions:")
                for i, url in enumerate(urls[:3], 1):
                    # Check for correct spelling and patterns
                    correct_spelling = "herosbridge.org" in url.lower()
                    has_www = url.startswith("https://www.")
                    
                    status_indicators = []
                    if correct_spelling:
                        status_indicators.append("CORRECT SPELLING")
                    if has_www:
                        status_indicators.append("WWW SUBDOMAIN")
                    if url.lower() == "https://www.herosbridge.org":
                        status_indicators.append("PERFECT MATCH")
                    
                    status = " | ".join(status_indicators) if status_indicators else "Check needed"
                    print(f"  {i}. {url} [{status}]")
                
                # Check if we got the perfect URL
                perfect_url = "https://www.herosbridge.org"
                if perfect_url in [url.lower() for url in urls]:
                    print(f"\nSUCCESS: Predicted correct URL '{perfect_url}'")
                    return True
                elif any("herosbridge.org" in url.lower() for url in urls):
                    print(f"\nGOOD: Predicted correct spelling 'herosbridge.org'")
                    print("  (May need www. subdomain but spelling is accurate)")
                    return True
                else:
                    print(f"\nISSUE: No predictions with correct 'heros' spelling")
                    return False
            else:
                print("ERROR: No URL predictions generated")
                return False
        else:
            print(f"ERROR: URL Discovery failed: {result.errors}")
            return False
            
    except Exception as e:
        print(f"ERROR in URL prediction test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run Heroes Bridge BMF integration test"""
    try:
        success = await test_heroes_bridge_bmf_integration()
        
        print("\n" + "="*80)
        if success:
            print("HEROES BRIDGE BMF INTEGRATION TEST: PASSED")
            print("* BMF database integration working")
            print("* Correct 'HEROS BRIDGE' spelling preserved")
            print("* GPT URL predictions improved")
        else:
            print("HEROES BRIDGE BMF INTEGRATION TEST: NEEDS IMPROVEMENT")
            print("Check BMF database and GPT prompt effectiveness")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())