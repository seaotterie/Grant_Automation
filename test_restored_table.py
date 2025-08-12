#!/usr/bin/env python3
"""
Test the restored table with Discovery column
"""

import requests

def test_restored_table():
    """Test that table is working with Discovery column"""
    print('TESTING RESTORED TABLE WITH DISCOVERY COLUMN')
    print('=' * 50)

    # Test the interface
    response = requests.get('http://localhost:8000/')
    if response.status_code != 200:
        print(f'Server error: {response.status_code}')
        return False

    content = response.text

    # Check table structure
    table_headers = ['Select', 'Organization', 'Type', 'Focus Areas', 'Opportunities', 'Status', 'Discovery', 'Actions']

    print('TABLE HEADERS:')
    all_headers_found = True
    for header in table_headers:
        found = f'{header}</th>' in content
        print(f'{header}: {"FOUND" if found else "MISSING"}')
        if not found:
            all_headers_found = False

    # Check discovery features
    print()
    print('DISCOVERY FEATURES:')
    discovery_features = [
        ('Radio buttons', 'type="radio"'),
        ('Profile selection', 'selectedDiscoveryProfile'),
        ('Discovery status', 'getDiscoveryStatusClass'),
        ('Discovery buttons', 'getDiscoveryButtonText'),
        ('Table visibility condition', 'x-show="!profilesLoading && filteredProfiles.length > 0"')
    ]

    all_features_found = True
    for name, pattern in discovery_features:
        found = pattern in content
        print(f'{name}: {"PRESENT" if found else "MISSING"}')
        if not found:
            all_features_found = False

    # Check API data
    print()
    print('PROFILE DATA CHECK:')
    api_response = requests.get('http://localhost:8000/api/profiles?limit=1')
    if api_response.status_code == 200:
        data = api_response.json()
        if data.get('profiles') and len(data['profiles']) > 0:
            print(f'Profiles available: {len(data["profiles"])} profiles')
            profile = data['profiles'][0]
            print(f'Sample profile: {profile.get("name", "No name")}')
            print(f'Discovery status: {profile.get("discovery_status", "No status")}')
        else:
            print('No profiles found - table will show empty state')
    else:
        print(f'API error: {api_response.status_code}')

    print()
    if all_headers_found and all_features_found:
        print('SUCCESS: Table restored with Discovery column!')
    else:
        print('ISSUE: Some features still missing')
    
    print()
    print('NEXT STEPS FOR USER:')
    print('1. Clear browser cache (Ctrl+Shift+Delete)')
    print('2. Navigate to http://localhost:8000')  
    print('3. Go to PROFILER tab')
    print('4. You should see the table with Discovery column and radio buttons')
    
    return all_headers_found and all_features_found

if __name__ == "__main__":
    test_restored_table()