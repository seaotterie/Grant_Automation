#!/usr/bin/env python3
"""
Test ProPublica API with large, well-known nonprofits that should definitely have 990 data.
"""

import asyncio
import aiohttp

async def test_large_nonprofits():
    print('Testing large nonprofits that should have 990 filing data...')
    
    # Large nonprofits that definitely file 990s
    test_nonprofits = [
        # Format: (EIN, Expected Name)
        ('131624187', 'United Way'),
        ('530196605', 'American Red Cross'),
        ('363544947', 'Feeding America'),
        ('521594842', 'Goodwill Industries'),
        ('362167407', 'Goodwill example'),
        ('237067881', 'Another example'),
        ('366104572', 'Boys and Girls Clubs'),
        ('953242021', 'Doctors Without Borders'),
        ('436097903', 'World Vision'),
        ('132635427', 'Save the Children'),
    ]
    
    found_data = []
    
    async with aiohttp.ClientSession() as session:
        for ein, expected_name in test_nonprofits:
            url = f'https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json'
            
            try:
                print(f'\nTesting EIN {ein} ({expected_name})...')
                async with session.get(url, timeout=15) as response:
                    print(f'  Status: {response.status}')
                    
                    if response.status == 200:
                        data = await response.json()
                        org = data.get('organization', {})
                        filings = data.get('filings', [])
                        
                        actual_name = org.get('name', 'Unknown')
                        print(f'  Actual name: {actual_name}')
                        print(f'  Filings: {len(filings)}')
                        
                        if filings:
                            # Show detailed filing info
                            print(f'  SUCCESS - Found {len(filings)} filings!')
                            
                            recent = filings[0]
                            print(f'  Most recent filing:')
                            print(f'    Tax year: {recent.get("tax_prd_yr", "N/A")}')
                            print(f'    Revenue: ${recent.get("totrevenue", 0):,}')
                            print(f'    Assets: ${recent.get("totassetsend", 0):,}')
                            print(f'    Program expenses: ${recent.get("totfuncexpns", 0):,}')
                            print(f'    Total expenses: ${recent.get("totexpns", 0):,}')
                            
                            # Show multiple years
                            if len(filings) > 1:
                                years = [f.get("tax_prd_yr") for f in filings[:5]]
                                print(f'    Available years: {years}')
                            
                            found_data.append({
                                'ein': ein,
                                'name': actual_name,
                                'filings': len(filings),
                                'recent_year': recent.get('tax_prd_yr', 0),
                                'revenue': recent.get('totrevenue', 0)
                            })
                        else:
                            print(f'  No filing data for {actual_name}')
                    
                    elif response.status == 404:
                        print(f'  Organization not found in ProPublica database')
                    else:
                        print(f'  API error: {response.status}')
                        text = await response.text()
                        print(f'  Response: {text[:100]}')
                        
                await asyncio.sleep(1.0)  # Slower rate limiting for testing
                        
            except Exception as e:
                print(f'  Error: {e}')
    
    print('\n' + '='*70)
    print('RESULTS SUMMARY')
    print('='*70)
    
    if found_data:
        print('Organizations WITH filing data:')
        for org in found_data:
            print(f'  EIN {org["ein"]}: {org["name"]}')
            print(f'    {org["filings"]} filings, recent: {org["recent_year"]}, revenue: ${org["revenue"]:,}')
        
        # Best candidate for testing
        best = max(found_data, key=lambda x: (x['filings'], x['revenue']))
        print(f'\nBEST TEST CANDIDATE:')
        print(f'  EIN: {best["ein"]}')
        print(f'  Name: {best["name"]}')
        print(f'  Filings: {best["filings"]}')
        print(f'  Recent revenue: ${best["revenue"]:,}')
        
    else:
        print('NO organizations found with filing data!')
        print('This suggests an issue with:')
        print('  1. ProPublica API structure changes')
        print('  2. Database availability')
        print('  3. Our API request format')

if __name__ == "__main__":
    asyncio.run(test_large_nonprofits())