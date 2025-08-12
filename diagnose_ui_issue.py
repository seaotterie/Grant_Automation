#!/usr/bin/env python3
"""
Diagnostic script to identify why UI changes aren't visible to user
"""

import requests
import re
from pathlib import Path

def diagnose_ui_issue():
    """Comprehensive diagnosis of UI visibility issues"""
    base_url = "http://localhost:8000"
    
    print("CATALYNX UI DIAGNOSTIC")
    print("=" * 60)
    
    # Test 1: Check if server is serving the correct HTML file
    try:
        response = requests.get(base_url)
        html_content = response.text
        
        print("1. HTML FILE ANALYSIS")
        print("-" * 30)
        
        # Check for key discovery features
        discovery_indicators = {
            'Discovery Column': 'Discovery</th>',
            'Radio Buttons': 'type="radio"',
            'Selected Profile Check': 'selectedDiscoveryProfile?.profile_id === profile.profile_id',
            'Discovery Status Function': 'getDiscoveryStatusClass',
            'Profile Selection Method': 'selectProfileForDiscovery'
        }
        
        for feature, indicator in discovery_indicators.items():
            if indicator in html_content:
                print(f"[FOUND] {feature}")
            else:
                print(f"[MISSING] {feature}")
        
        # Check for the profile editing fix
        if "this.switchStage('profiler')" in html_content:
            print("[FOUND] Profile editing navigation fix")
        else:
            print("[MISSING] Profile editing navigation fix")
            
    except Exception as e:
        print(f"[ERROR] HTML analysis failed: {e}")
        return
    
    print("\n2. DELETE PROFILE DIALOG INVESTIGATION")
    print("-" * 30)
    
    # Look for delete profile dialog issues
    delete_patterns = [
        r'showDeleteDialog\s*=\s*true',
        r'deleteProfile',
        r'confirmDelete',
        r'x-show="showDeleteDialog"'
    ]
    
    for pattern in delete_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            print(f"[FOUND] Delete dialog pattern: {pattern} - {len(matches)} matches")
    
    # Check Alpine.js initialization
    if 'x-data=' in html_content:
        print("[FOUND] Alpine.js x-data attributes")
        # Count x-data occurrences
        x_data_count = len(re.findall(r'x-data=', html_content))
        print(f"         Total x-data attributes: {x_data_count}")
    else:
        print("[MISSING] Alpine.js x-data attributes")
    
    print("\n3. JAVASCRIPT FUNCTION VERIFICATION")
    print("-" * 30)
    
    try:
        # Check app.js content
        js_response = requests.get(f"{base_url}/static/app.js")
        js_content = js_response.text
        
        required_functions = [
            'getDiscoveryStatusClass',
            'getDiscoveryStatusText', 
            'getDiscoveryButtonText',
            'selectProfileForDiscovery',
            'saveProfile'
        ]
        
        for func in required_functions:
            if func in js_content:
                print(f"[FOUND] {func}()")
            else:
                print(f"[MISSING] {func}()")
                
        # Check for showDeleteDialog initialization
        if 'showDeleteDialog' in js_content:
            print("[FOUND] showDeleteDialog variable")
            # Check how it's initialized
            delete_init_patterns = [
                r'showDeleteDialog:\s*false',
                r'showDeleteDialog:\s*true', 
                r'showDeleteDialog\s*=\s*false',
                r'showDeleteDialog\s*=\s*true'
            ]
            
            for pattern in delete_init_patterns:
                matches = re.findall(pattern, js_content, re.IGNORECASE)
                if matches:
                    print(f"         Initialization: {matches[0]}")
                    
    except Exception as e:
        print(f"[ERROR] JavaScript analysis failed: {e}")
    
    print("\n4. CACHE AND HEADERS CHECK")
    print("-" * 30)
    
    try:
        response = requests.get(base_url)
        headers = response.headers
        
        print(f"Cache-Control: {headers.get('cache-control', 'NOT SET')}")
        print(f"Pragma: {headers.get('pragma', 'NOT SET')}")
        print(f"Expires: {headers.get('expires', 'NOT SET')}")
        print(f"ETag: {headers.get('etag', 'NOT SET')}")
        print(f"Last-Modified: {headers.get('last-modified', 'NOT SET')}")
        
    except Exception as e:
        print(f"[ERROR] Headers check failed: {e}")
    
    print("\n5. FILE TIMESTAMP CHECK")
    print("-" * 30)
    
    # Check when files were last modified
    files_to_check = [
        "src/web/static/index.html",
        "src/web/static/app.js", 
        "src/web/main.py"
    ]
    
    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            mtime = path.stat().st_mtime
            import time
            readable_time = time.ctime(mtime)
            print(f"{file_path}: {readable_time}")
        else:
            print(f"{file_path}: FILE NOT FOUND")
    
    print("\n6. PROFILE DATA CHECK")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/api/profiles?limit=1")
        if response.status_code == 200:
            data = response.json()
            if data.get("profiles"):
                profile = data["profiles"][0]
                print(f"Sample profile discovery_status: {profile.get('discovery_status', 'MISSING')}")
                print(f"Sample profile discovery_count: {profile.get('discovery_count', 'MISSING')}")
            else:
                print("No profiles returned")
        else:
            print(f"API call failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Profile API test failed: {e}")
    
    print("\n7. RECOMMENDATIONS")
    print("-" * 30)
    print("Based on this analysis:")
    print("• If discovery features are MISSING from HTML: Template not updated")
    print("• If DELETE dialog shows true initialization: Alpine.js state issue") 
    print("• If functions are MISSING from JS: JavaScript not updated")
    print("• Check browser developer console for JavaScript errors")
    print("• Try hard refresh (Ctrl+F5) or incognito mode")

if __name__ == "__main__":
    diagnose_ui_issue()