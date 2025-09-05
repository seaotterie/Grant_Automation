#!/usr/bin/env python3
"""
Fetch Heroes Bridge data (EIN 81-2827604) for real-world test
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import aiohttp
import asyncio
import json
from pathlib import Path

async def fetch_heroes_bridge():
    """Fetch real data for Heroes Bridge (EIN 81-2827604)"""
    ein = '812827604'  # Heroes Bridge EIN
    url = f'https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json'
    
    print(f"Fetching Heroes Bridge data for EIN {ein}...")
    print(f"API URL: {url}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                # Create entity directory
                entity_dir = Path('data/source_data/nonprofits/812827604')
                entity_dir.mkdir(parents=True, exist_ok=True)
                
                # Save the raw data
                with open(entity_dir / 'propublica.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                # Extract key information
                org_data = data.get('organization', {})
                filings = data.get('filings_with_data', [])
                
                print("\n" + "="*60)
                print("REAL DATA ACQUIRED: HEROES BRIDGE")
                print("="*60)
                print(f"Organization Name: {org_data.get('name')}")
                print(f"EIN: {org_data.get('ein')}")
                print(f"State: {org_data.get('state')}")
                print(f"City: {org_data.get('city')}")
                print(f"NTEE Code: {org_data.get('ntee_code')}")
                print(f"Ruling Date: {org_data.get('ruling_date')}")
                print(f"Available Filings: {len(filings)}")
                
                # Financial data from latest filing
                if filings:
                    latest = filings[0]
                    print(f"\nLatest Filing (Tax Year {latest.get('tax_prd_yr', 'Unknown')}):")
                    print(f"  Total Revenue: ${latest.get('totrevenue', 0):,}")
                    print(f"  Total Expenses: ${latest.get('totfuncexpns', 0):,}")
                    print(f"  Net Assets: ${latest.get('totnetassets', 0):,}")
                    print(f"  Contributions/Grants Received: ${latest.get('totcntrbs', 0):,}")
                    print(f"  Program Service Revenue: ${latest.get('totprgmrevnue', 0):,}")
                
                print(f"\nData successfully saved to: {entity_dir / 'propublica.json'}")
                
                return {
                    'organization': org_data,
                    'filings': filings,
                    'data_file': str(entity_dir / 'propublica.json')
                }
                
            else:
                error_text = await response.text()
                print(f"API Error: {response.status}")
                print(f"Response: {error_text}")
                return None

async def verify_both_datasets():
    """Verify both organizations are ready"""
    print("\n" + "="*60)
    print("VERIFYING COMPLETE DATASET")
    print("="*60)
    
    # Check Fauquier Health Foundation
    fauquier_file = Path('data/source_data/nonprofits/300219424/propublica.json')
    heroes_file = Path('data/source_data/nonprofits/812827604/propublica.json')
    
    both_ready = True
    
    if fauquier_file.exists():
        with open(fauquier_file, 'r') as f:
            fauquier_data = json.load(f)
            fauquier_org = fauquier_data.get('organization', {})
            print(f"✓ OPPORTUNITY: {fauquier_org.get('name')} (EIN: {fauquier_org.get('ein')})")
            print(f"  Type: Health Foundation")
            print(f"  Location: {fauquier_org.get('city')}, {fauquier_org.get('state')}")
    else:
        print("✗ OPPORTUNITY: Fauquier Health Foundation data missing")
        both_ready = False
    
    if heroes_file.exists():
        with open(heroes_file, 'r') as f:
            heroes_data = json.load(f)
            heroes_org = heroes_data.get('organization', {})
            print(f"✓ PROFILE: {heroes_org.get('name')} (EIN: {heroes_org.get('ein')})")
            print(f"  Type: {heroes_org.get('ntee_code')} Organization")
            print(f"  Location: {heroes_org.get('city')}, {heroes_org.get('state')}")
    else:
        print("✗ PROFILE: Heroes Bridge data missing")
        both_ready = False
    
    return both_ready

async def main():
    """Main execution"""
    print("FETCHING HEROES BRIDGE DATA FOR REAL-WORLD TEST")
    print("-" * 60)
    
    # Fetch Heroes Bridge data
    heroes_data = await fetch_heroes_bridge()
    
    if heroes_data:
        # Verify both datasets are complete
        ready = await verify_both_datasets()
        
        if ready:
            print("\n" + "="*60)
            print("BOTH REAL DATASETS READY FOR AI PROCESSING")
            print("="*60)
            print("REAL-WORLD SCENARIO:")
            print("  Heroes Bridge (veteran services) seeking funding from")
            print("  Fauquier Health Foundation (health foundation)")
            print("\nNext: Execute 4-stage AI analysis pipeline")
            return True
        else:
            print("\nDataset verification failed")
            return False
    else:
        print("Failed to fetch Heroes Bridge data")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    if result:
        print(f"\nREADY: Proceeding to 4-stage AI processing with real data")
    else:
        print(f"\nFAILED: Data acquisition incomplete")