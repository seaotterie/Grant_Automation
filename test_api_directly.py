#!/usr/bin/env python3
"""
Test the web API endpoints directly to see what they're returning
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    """Test the API endpoints to see what data they return"""
    
    print("Testing API Endpoints Directly")
    print("=" * 40)
    
    try:
        # Test 1: Check if server is running
        print("Step 1: Testing server connection...")
        response = requests.get(f"{BASE_URL}/api/profiles", timeout=5)
        print(f"Server response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Server not responding correctly: {response.text}")
            return
            
        # Test 2: Check existing profiles
        print("\nStep 2: Checking existing profiles...")
        data = response.json()
        profiles = data.get('profiles', data)
        
        print(f"Total profiles returned: {len(profiles)}")
        
        # Find any profile with our test data
        for profile in profiles[:5]:  # Check first 5 profiles
            print(f"\nProfile: {profile.get('name', 'Unknown')}")
            print(f"  Profile ID: {profile.get('profile_id', 'None')}")
            print(f"  NTEE codes: {profile.get('ntee_codes', 'MISSING')}")
            print(f"  Government criteria: {profile.get('government_criteria', 'MISSING')}")
            print(f"  Keywords: {profile.get('keywords', 'MISSING')}")
        
        # Test 3: Create a new profile via API
        print("\nStep 3: Creating profile via API...")
        test_profile = {
            "name": "API Test Nonprofit",
            "organization_type": "nonprofit",
            "ein": "99-8877665",
            "mission_statement": "API test mission statement for debugging",
            "keywords": "api, test, debugging",
            "focus_areas": ["Testing"],
            "target_populations": ["Developers"],
            "geographic_scope": {
                "states": ["VA"],
                "nationwide": False,
                "international": False
            },
            "funding_preferences": {
                "min_amount": 5000,
                "max_amount": 50000,
                "funding_types": ["grants"]
            },
            "ntee_codes": ["X01", "X02", "X03"],
            "government_criteria": ["API Test Criteria 1", "API Test Criteria 2"]
        }
        
        create_response = requests.post(f"{BASE_URL}/api/profiles", 
                                      json=test_profile,
                                      headers={'Content-Type': 'application/json'})
        
        if create_response.status_code == 200:
            created_data = create_response.json()
            print("Profile created successfully via API")
            print(f"Response structure: {list(created_data.keys())}")
            
            if 'profile' in created_data:
                profile = created_data['profile']
                print(f"Created profile NTEE codes: {profile.get('ntee_codes', 'MISSING')}")
                print(f"Created profile government criteria: {profile.get('government_criteria', 'MISSING')}")
                print(f"Created profile keywords: {profile.get('keywords', 'MISSING')}")
                
                # Test 4: Retrieve the specific profile
                profile_id = profile.get('profile_id')
                if profile_id:
                    print(f"\nStep 4: Retrieving specific profile {profile_id}...")
                    get_response = requests.get(f"{BASE_URL}/api/profiles/{profile_id}")
                    
                    if get_response.status_code == 200:
                        retrieved_data = get_response.json()
                        print(f"Retrieved profile response structure: {list(retrieved_data.keys())}")
                        
                        if 'profile' in retrieved_data:
                            retrieved_profile = retrieved_data['profile']
                            print(f"Retrieved NTEE codes: {retrieved_profile.get('ntee_codes', 'MISSING')}")
                            print(f"Retrieved government criteria: {retrieved_profile.get('government_criteria', 'MISSING')}")
                            print(f"Retrieved keywords: {retrieved_profile.get('keywords', 'MISSING')}")
                        else:
                            print("No 'profile' key in retrieved data")
                            print(f"Retrieved data: {retrieved_data}")
                    else:
                        print(f"Failed to retrieve profile: {get_response.status_code} - {get_response.text}")
                
                # Cleanup
                print(f"\nCleaning up profile {profile_id}...")
                delete_response = requests.delete(f"{BASE_URL}/api/profiles/{profile_id}")
                if delete_response.status_code == 200:
                    print("Profile deleted successfully")
                else:
                    print(f"Failed to delete profile: {delete_response.status_code}")
            else:
                print("No 'profile' key in creation response")
                print(f"Creation response: {created_data}")
        else:
            print(f"Failed to create profile: {create_response.status_code} - {create_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"ERROR: Test failed with: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_endpoints()