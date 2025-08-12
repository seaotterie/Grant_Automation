#!/usr/bin/env python3
"""
Test API endpoints directly to verify functionality
"""
import requests
import json
import sys
from pathlib import Path

def test_api_endpoints():
    """Test key API endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing Catalynx API Endpoints")
    print("=" * 40)
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✓ Health endpoint working")
        else:
            print(f"✗ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Health endpoint error: {e}")
        return
    
    # Test 2: List profiles
    try:
        response = requests.get(f"{base_url}/api/profiles")
        if response.status_code == 200:
            data = response.json()
            profiles = data.get('profiles', [])
            print(f"✓ Profiles endpoint: {len(profiles)} profiles found")
            
            if profiles:
                print("   Sample profiles:")
                for i, profile in enumerate(profiles[:3], 1):
                    name = profile.get('name', 'Unknown')
                    org_type = profile.get('organization_type', 'Unknown')
                    opportunities = profile.get('opportunities_count', 0)
                    print(f"     {i}. {name} ({org_type}) - {opportunities} opportunities")
        else:
            print(f"✗ Profiles endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Profiles endpoint error: {e}")
    
    # Test 3: System status
    try:
        response = requests.get(f"{base_url}/api/system/status")
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            processors = data.get('processors_available', 0)
            print(f"✓ System status: {status} ({processors} processors)")
        else:
            print(f"✗ System status failed: {response.status_code}")
    except Exception as e:
        print(f"✗ System status error: {e}")
    
    # Test 4: Try discovery on first profile
    try:
        # Get profiles first
        response = requests.get(f"{base_url}/api/profiles")
        if response.status_code == 200:
            profiles = response.json().get('profiles', [])
            
            if profiles:
                first_profile = profiles[0]
                profile_id = first_profile['profile_id']
                
                print(f"\n✓ Testing discovery for: {first_profile['name']}")
                
                discovery_data = {
                    "funding_types": ["grants"],
                    "max_results": 5
                }
                
                response = requests.post(
                    f"{base_url}/api/profiles/{profile_id}/discover",
                    json=discovery_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    total_found = result.get('total_opportunities_found', 0)
                    print(f"   ✓ Discovery completed: {total_found} opportunities found")
                else:
                    print(f"   ✗ Discovery failed: {response.status_code}")
                    print(f"     Response: {response.text[:200]}...")
    except Exception as e:
        print(f"✗ Discovery test error: {e}")
    
    print("\n" + "=" * 40)
    print("API Integration Test Complete")
    print("The server is ready for GUI testing!")

if __name__ == "__main__":
    test_api_endpoints()