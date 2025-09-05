#!/usr/bin/env python3
"""
Fetch real data for EIN 30-0219424 (Fauquier Health Foundation)
Real-world test of existing Catalynx system
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import aiohttp
import asyncio
import json
from pathlib import Path
from datetime import datetime

async def fetch_fauquier_health_foundation():
    """Fetch real data for Fauquier Health Foundation"""
    ein = '300219424'
    url = f'https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json'
    
    print(f"Fetching real data for EIN {ein}...")
    print(f"API URL: {url}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                # Create entity directory
                entity_dir = Path('data/source_data/nonprofits/300219424')
                entity_dir.mkdir(parents=True, exist_ok=True)
                
                # Save the raw data
                with open(entity_dir / 'propublica.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                # Extract key information
                org_data = data.get('organization', {})
                filings = data.get('filings_with_data', [])
                
                print("\n" + "="*60)
                print("REAL DATA ACQUIRED: FAUQUIER HEALTH FOUNDATION")
                print("="*60)
                print(f"Organization Name: {org_data.get('name')}")
                print(f"EIN: {org_data.get('ein')}")
                print(f"State: {org_data.get('state')}")
                print(f"City: {org_data.get('city')}")
                print(f"NTEE Code: {org_data.get('ntee_code')} (Health - General and Rehabilitative)")
                print(f"Ruling Date: {org_data.get('ruling_date')}")
                print(f"Deductibility Code: {org_data.get('deductibility_code')}")
                print(f"Foundation Code: {org_data.get('foundation_code')}")
                print(f"Classification: {org_data.get('classification')}")
                print(f"Available Filings: {len(filings)}")
                
                # Financial data from latest filing
                if filings:
                    latest = filings[0]
                    print(f"\nLatest Filing (Tax Year {latest.get('tax_prd_yr', 'Unknown')}):")
                    print(f"  Total Revenue: ${latest.get('totrevenue', 0):,}")
                    print(f"  Total Expenses: ${latest.get('totfuncexpns', 0):,}")
                    print(f"  Net Assets: ${latest.get('totnetassets', 0):,}")
                    print(f"  Contributions/Grants: ${latest.get('totcntrbs', 0):,}")
                    print(f"  Program Service Revenue: ${latest.get('totprgmrevnue', 0):,}")
                    print(f"  Investment Income: ${latest.get('invstmntinc', 0):,}")
                
                # Foundation/Grant-making indicators
                foundation_code = org_data.get('foundation_code')
                if foundation_code:
                    print(f"\nFoundation Classification: {foundation_code}")
                    if foundation_code in ['15', '16', '17']:  # Private foundation codes
                        print("  -> This is a PRIVATE FOUNDATION (potential funding source)")
                    elif foundation_code in ['09', '10', '11']:  # Public charity codes
                        print("  -> This is a PUBLIC CHARITY")
                
                print(f"\nData successfully saved to: {entity_dir / 'propublica.json'}")
                print("Entity ready for Catalynx processing pipeline")
                
                return {
                    'organization': org_data,
                    'filings': filings,
                    'entity_type': 'foundation' if foundation_code in ['15', '16', '17'] else 'nonprofit',
                    'data_file': str(entity_dir / 'propublica.json')
                }
                
            else:
                error_text = await response.text()
                print(f"API Error: {response.status}")
                print(f"Response: {error_text}")
                return None

async def check_heroes_bridge_data():
    """Check if Heroes Bridge data exists"""
    heroes_bridge_dir = Path('data/source_data/nonprofits/812827604')
    
    print("\n" + "="*60)
    print("CHECKING HEROES BRIDGE PROFILE DATA")
    print("="*60)
    
    if heroes_bridge_dir.exists():
        propublica_file = heroes_bridge_dir / 'propublica.json'
        if propublica_file.exists():
            with open(propublica_file, 'r') as f:
                data = json.load(f)
                org_data = data.get('organization', {})
                print(f"Heroes Bridge Data Found:")
                print(f"  Name: {org_data.get('name')}")
                print(f"  EIN: {org_data.get('ein')}")
                print(f"  State: {org_data.get('state')}")
                print(f"  NTEE Code: {org_data.get('ntee_code')}")
                return data
        else:
            print("Heroes Bridge directory exists but no propublica.json file found")
            return None
    else:
        print("Heroes Bridge data directory not found")
        print("Will need to fetch Heroes Bridge data as well")
        return None

async def main():
    """Main execution function"""
    print("STARTING REAL-WORLD CATALYNX TEST")
    print("Target: EIN 30-0219424 (Opportunity)")
    print("Profile: Heroes Bridge EIN 81-2827604 (Applying Organization)")
    print("-" * 60)
    
    # Fetch Fauquier Health Foundation data
    fauquier_data = await fetch_fauquier_health_foundation()
    
    # Check Heroes Bridge data
    heroes_data = await check_heroes_bridge_data()
    
    if fauquier_data and heroes_data:
        print("\n" + "="*60)
        print("DATA ACQUISITION COMPLETE - READY FOR AI PROCESSING")
        print("="*60)
        print("Next Steps:")
        print("1. PLAN Tab: Strategic opportunity assessment")
        print("2. ANALYZE Tab: Competitive landscape analysis") 
        print("3. EXAMINE Tab: Deep intelligence gathering")
        print("4. APPROACH Tab: Implementation planning")
        print("5. Complete Tier: $42.00 comprehensive intelligence")
        print("6. Masters Thesis Dossier Generation")
        
        return True
    else:
        print("\nData acquisition incomplete. Check errors above.")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    if result:
        print(f"\nSUCCESS: Ready to proceed with 4-stage AI processing")
    else:
        print(f"\nFAILED: Data acquisition incomplete")