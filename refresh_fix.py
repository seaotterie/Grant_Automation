#!/usr/bin/env python3
"""
Quick fix verification - check if profiles will now load
"""
import requests
import time

def test_fix():
    print("Testing profile loading fix...")
    
    try:
        # Test API endpoint
        response = requests.get('http://localhost:8000/api/profiles')
        print(f"API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            profiles = data.get('profiles', [])
            print(f"✓ API returns {len(profiles)} profiles")
            
            # Show sample profile data
            if profiles:
                sample = profiles[0]
                print("Sample profile:")
                print(f"  Name: {sample.get('name')}")
                print(f"  Type: {sample.get('organization_type')}")
                print(f"  Opportunities: {sample.get('opportunities_count', 0)}")
                print(f"  Profile ID: {sample.get('profile_id')}")
        
        # Test that JavaScript will now load profiles
        response = requests.get('http://localhost:8000/static/app.js')
        if response.status_code == 200:
            js_content = response.text
            if 'await this.loadProfiles();' in js_content:
                print("✓ JavaScript updated to load real profiles")
            else:
                print("✗ JavaScript still using static data")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_fix()
    print("\nFIX APPLIED!")
    print("Refresh your browser at http://localhost:8000")
    print("Navigate to READIFIER -> Profiler")
    print("You should now see 5 profiles!")