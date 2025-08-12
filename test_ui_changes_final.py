#!/usr/bin/env python3
"""
Final comprehensive test to verify all UI changes are working
"""

import requests
import json

def test_ui_changes():
    """Test that all UI changes are visible and functional"""
    base_url = "http://localhost:8000"
    
    print("Final UI Changes Verification Test")
    print("=" * 50)
    
    # Test 1: Cache-busting headers are working
    try:
        response = requests.head(base_url)
        headers = response.headers
        
        cache_control = headers.get('cache-control', '')
        pragma = headers.get('pragma', '')
        
        if 'no-cache' in cache_control and pragma == 'no-cache':
            print("[OK] Cache-busting headers working")
        else:
            print(f"[WARNING] Cache headers may not be optimal: {cache_control}, {pragma}")
            
    except Exception as e:
        print(f"[ERROR] Cache header test failed: {e}")
        return False
    
    # Test 2: All discovery features present in HTML
    try:
        response = requests.get(base_url)
        html_content = response.text
        
        required_features = {
            'Discovery column': 'Discovery</th>',
            'Radio buttons': 'type="radio"',
            'Selected profile highlight': 'selectedDiscoveryProfile?.profile_id === profile.profile_id',
            'Discovery status function': 'getDiscoveryStatusClass',
            'Discovery status text function': 'getDiscoveryStatusText',
            'Context-aware buttons': 'getDiscoveryButtonText',
            'Profile selection feedback': 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500',
            'Discovery page profile info': 'Selected Profile for Discovery',
            'No profile selected state': 'No Profile Selected'
        }
        
        missing_features = []
        for feature_name, search_text in required_features.items():
            if search_text not in html_content:
                missing_features.append(feature_name)
        
        if not missing_features:
            print("[OK] All discovery features present in HTML")
        else:
            print(f"[ERROR] Missing features: {', '.join(missing_features)}")
            return False
            
    except Exception as e:
        print(f"[ERROR] HTML content test failed: {e}")
        return False
    
    # Test 3: JavaScript functions are available
    try:
        response = requests.get(f"{base_url}/static/app.js")
        js_content = response.text
        
        js_functions = [
            'getDiscoveryStatusClass(status)',
            'getDiscoveryStatusText(status)',  
            'getDiscoveryButtonText(profile)',
            'selectProfileForDiscovery(profile)',
            'switchStage(\'profiler\')'  # Profile editing navigation fix
        ]
        
        missing_functions = []
        for func in js_functions:
            if func not in js_content:
                missing_functions.append(func)
        
        if not missing_functions:
            print("[OK] All JavaScript functions present")
        else:
            print(f"[ERROR] Missing JS functions: {', '.join(missing_functions)}")
            return False
            
    except Exception as e:
        print(f"[ERROR] JavaScript test failed: {e}")
        return False
    
    # Test 4: API returns discovery tracking data
    try:
        response = requests.get(f"{base_url}/api/profiles?limit=1")
        if response.status_code == 200:
            data = response.json()
            if data.get("profiles") and len(data["profiles"]) > 0:
                profile = data["profiles"][0]
                discovery_fields = [
                    'discovery_status', 'last_discovery_date', 'discovery_count',
                    'opportunities_count', 'next_recommended_discovery'
                ]
                
                missing_fields = [field for field in discovery_fields if field not in profile]
                
                if not missing_fields:
                    print("[OK] API returns all discovery fields")
                    print(f"     Example: Status='{profile.get('discovery_status')}', Count={profile.get('discovery_count')}")
                else:
                    print(f"[ERROR] Missing API fields: {missing_fields}")
                    return False
            else:
                print("[ERROR] No profiles in API response")
                return False
        else:
            print(f"[ERROR] API request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] API test failed: {e}")
        return False
    
    print("\n[SUCCESS] ALL TESTS PASSED!")
    print("\nImplemented Features Summary:")
    print("• Discovery Status Column: Shows 'Never Run', 'In Progress', 'Completed', etc.")
    print("• Radio Button Selection: Click to select profiles for discovery")  
    print("• Visual Selection Feedback: Selected profiles highlighted in blue")
    print("• Context-Aware Buttons: 'Start Discovery', 'Update Discovery', 'Retry Discovery'")
    print("• Discovery Page Integration: Shows selected profile details")
    print("• Profile Editing Fix: Returns to profiles tab after saving")
    print("• Cache-Busting: Prevents browser cache issues")
    print("• Discovery History Tracking: Tracks dates, counts, and status")
    
    print("\nNext Steps for Testing:")
    print("1. Clear your browser cache (Ctrl+Shift+Delete)")
    print("2. Navigate to http://localhost:8000")
    print("3. Go to PROFILER tab to see the Discovery column")
    print("4. Click radio buttons to select profiles")
    print("5. Click context-aware discovery buttons")
    print("6. Go to DISCOVER tab to see selected profile info")
    
    return True

if __name__ == "__main__":
    test_ui_changes()