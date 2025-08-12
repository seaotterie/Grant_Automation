#!/usr/bin/env python3
"""
Test ProPublica API with multiple EINs to find organizations with filing data.
"""

import asyncio
import aiohttp

async def test_multiple_eins():
    print('Testing multiple EINs for filing data...')
    
    # Test multiple EINs to find ones with filing data
    test_eins = [
        '541669652',  # Family Forward Foundation
        '134014982',  # Grantmakers In Aging Inc (from test results)
        '521382983',  # Try another random one
        '131624187',  # United Way example
        '530196605',  # Red Cross example
        '237067881',  # Feeding America
        '362167407',  # Goodwill
    ]
    
    organizations_with_data = []
    
    async with aiohttp.ClientSession() as session:
        for ein in test_eins:
            url = f'https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json'
            
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        org = data.get('organization', {})
                        filings = data.get('filings', [])
                        
                        print(f'\nEIN {ein}: {org.get("name", "Unknown")}')
                        print(f'  Filings: {len(filings)}')
                        
                        if filings:
                            recent = filings[0]
                            print(f'  Most recent: {recent.get("tax_prd_yr", "N/A")}')
                            print(f'  Revenue: ${recent.get("totrevenue", 0):,}')
                            print(f'  Assets: ${recent.get("totassetsend", 0):,}')
                            
                            if len(filings) > 1:
                                filing_years = [f.get("tax_prd_yr") for f in filings[:5]]
                                print(f'  Filing years: {filing_years}')
                            
                            organizations_with_data.append({
                                'ein': ein,
                                'name': org.get('name', 'Unknown'),
                                'filing_count': len(filings),
                                'recent_year': recent.get('tax_prd_yr', 0),
                                'revenue': recent.get('totrevenue', 0)
                            })
                        else:
                            print('  No filing data available')
                    else:
                        print(f'\nEIN {ein}: API error {response.status}')
                        
                await asyncio.sleep(0.5)  # Rate limiting
                        
            except Exception as e:
                print(f'\nEIN {ein}: Error - {e}')
    
    print('\n' + '='*60)
    print('SUMMARY - Organizations with filing data:')
    print('='*60)
    
    if organizations_with_data:
        for org in organizations_with_data:
            print(f"EIN {org['ein']}: {org['name']}")
            print(f"  {org['filing_count']} filings, recent: {org['recent_year']}, revenue: ${org['revenue']:,}")
        
        # Recommend best test EIN
        best_org = max(organizations_with_data, key=lambda x: x['filing_count'])
        print(f'\nRECOMMENDED TEST EIN: {best_org["ein"]} ({best_org["name"]})')
        print(f'Has {best_org["filing_count"]} filings - good for testing!')
    else:
        print('No organizations found with filing data.')

if __name__ == "__main__":
    asyncio.run(test_multiple_eins())