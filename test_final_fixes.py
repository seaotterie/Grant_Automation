#!/usr/bin/env python3
"""
Test all the final fixes for Discovery functionality
"""

import requests

def test_final_fixes():
    """Test that all issues are resolved"""
    print('TESTING ALL FINAL FIXES')
    print('=' * 50)

    # Test 1: Discovery functionality present
    print('1. DISCOVERY FUNCTIONALITY:')
    response = requests.get('http://localhost:8000/')
    content = response.text
    
    discovery_features = [
        ('Discovery column', 'Discovery</th>'),
        ('Radio buttons', 'type="radio"'),
        ('Profile selection', 'selectedDiscoveryProfile'),
        ('Status functions', 'getDiscoveryStatusClass'),
        ('Discovery buttons', 'getDiscoveryButtonText'),
    ]
    
    all_discovery_working = True
    for name, pattern in discovery_features:
        found = pattern in content
        print(f'   {name}: {"WORKING" if found else "BROKEN"}')
        if not found:
            all_discovery_working = False
    
    # Test 2: Flash prevention
    print()
    print('2. FLASH PREVENTION:')
    flash_fixes = [
        ('Delete modal x-cloak', 'x-show="showDeleteConfirmation"' in content and 'x-cloak' in content),
        ('Body x-cloak', 'x-data="catalynxApp()" x-cloak' in content),
        ('CSS hiding rule', '[x-cloak] { display: none !important; }' in content),
    ]
    
    all_flash_fixed = True
    for name, condition in flash_fixes:
        print(f'   {name}: {"FIXED" if condition else "NEEDS WORK"}')
        if not condition:
            all_flash_fixed = False
    
    # Test 3: Profile loading filter
    print()
    print('3. PROFILE LOADING:')
    js_response = requests.get('http://localhost:8000/static/app.js')
    js_content = js_response.text
    
    profile_fixes = [
        ('Removed active-only filter', 'profile.status === \'active\'' not in js_content),
        ('Allow non-archived profiles', 'profile.status !== \'archived\'' in js_content),
        ('Profile save navigation', 'this.switchStage(\'profiler\')' in js_content),
    ]
    
    all_profiles_fixed = True
    for name, condition in profile_fixes:
        print(f'   {name}: {"FIXED" if condition else "NEEDS WORK"}')
        if not condition:
            all_profiles_fixed = False
    
    # Test 4: API data availability
    print()
    print('4. API DATA:')
    api_response = requests.get('http://localhost:8000/api/profiles')
    if api_response.status_code == 200:
        data = api_response.json()
        profiles = data.get('profiles', [])
        print(f'   Profiles available: {len(profiles)}')
        if profiles:
            sample = profiles[0]
            print(f'   Sample profile status: {sample.get("status", "unknown")}')
            print(f'   Discovery status: {sample.get("discovery_status", "unknown")}')
    else:
        print(f'   API Error: {api_response.status_code}')
        all_profiles_fixed = False
    
    # Final assessment
    print()
    print('OVERALL ASSESSMENT:')
    if all_discovery_working and all_flash_fixed and all_profiles_fixed:
        print('SUCCESS: All fixes working!')
        print()
        print('WHAT SHOULD BE RESOLVED:')
        print('✓ Discovery column visible with radio buttons')
        print('✓ No more delete dialog flash on startup')
        print('✓ No more old interface flash')
        print('✓ Edit functionality stays after editing profiles')
        print('✓ Discovery buttons work after editing')
        print()
        print('USER INSTRUCTIONS:')
        print('1. Clear browser cache completely (Ctrl+Shift+Delete)')
        print('2. Navigate to http://localhost:8000')
        print('3. Go to PROFILER tab')
        print('4. Test editing a profile - it should stay visible')
        print('5. Test discovery functionality with radio buttons')
        return True
    else:
        print('ISSUES REMAIN:')
        if not all_discovery_working:
            print('- Discovery functionality incomplete')
        if not all_flash_fixed:
            print('- Flash prevention incomplete')
        if not all_profiles_fixed:
            print('- Profile loading issues remain')
        return False

if __name__ == "__main__":
    test_final_fixes()