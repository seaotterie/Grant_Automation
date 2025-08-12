#!/usr/bin/env python3
"""
Test script to debug profile persistence issues with NTEE codes and government criteria
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_profile_persistence():
    """Test creating and editing a profile with NTEE codes and government criteria"""
    
    print("Testing Profile Persistence")
    print("=" * 50)
    
    # Test data
    test_profile = {
        "name": "Test Nonprofit Organization",
        "organization_type": "nonprofit",
        "ein": "12-3456789",
        "mission_statement": "Test mission for persistence debugging",
        "keywords": "test, debugging, persistence",
        "focus_areas": ["Education", "Health"],
        "target_populations": ["Children", "Adults"],
        "geographic_scope": {
            "states": ["VA", "MD"],
            "nationwide": False,
            "international": False
        },
        "funding_preferences": {
            "min_amount": 10000,
            "max_amount": 100000,
            "funding_types": ["grants"]
        },
        "annual_revenue": 250000,
        "staff_size": 5,
        "volunteer_count": 20,
        "board_size": 7,
        "location": "Richmond, VA",
        "notes": "Test profile for debugging",
        "ntee_codes": ["B25", "E32", "P20"],
        "government_criteria": ["Federal Grants", "State Programs", "Local Funding"]
    }
    
    try:
        # Step 1: Create profile
        print("Step 1: Creating profile...")
        response = requests.post(f"{BASE_URL}/api/profiles", json=test_profile)
        
        if response.status_code == 200:
            created_profile = response.json()
            profile_id = created_profile.get('profile_id')
            print(f"Profile created with ID: {profile_id}")
            print(f"NTEE codes saved: {created_profile.get('ntee_codes', [])}")
            print(f"Gov criteria saved: {created_profile.get('government_criteria', [])}")
        else:
            print(f"Failed to create profile: {response.status_code} - {response.text}")
            return
        
        time.sleep(1)
        
        # Step 2: Retrieve the profile
        print("\nStep 2: Retrieving profile...")
        response = requests.get(f"{BASE_URL}/api/profiles/{profile_id}")
        
        if response.status_code == 200:
            retrieved_profile = response.json()
            print(f"Profile retrieved successfully")
            print(f"NTEE codes retrieved: {retrieved_profile.get('ntee_codes', [])}")
            print(f"Gov criteria retrieved: {retrieved_profile.get('government_criteria', [])}")
        else:
            print(f"Failed to retrieve profile: {response.status_code} - {response.text}")
            return
        
        time.sleep(1)
        
        # Step 3: Update the profile with new data
        print("\nStep 3: Updating profile...")
        updated_profile = retrieved_profile.copy()
        updated_profile['mission_statement'] = "Updated mission statement for testing"
        updated_profile['ntee_codes'] = ["A20", "B40", "C50"]  # Different codes
        updated_profile['government_criteria'] = ["Federal Only", "State Only"]  # Different criteria
        
        response = requests.put(f"{BASE_URL}/api/profiles/{profile_id}", json=updated_profile)
        
        if response.status_code == 200:
            updated_result = response.json()
            print(f"Profile updated successfully")
            print(f"NTEE codes after update: {updated_result.get('ntee_codes', [])}")
            print(f"Gov criteria after update: {updated_result.get('government_criteria', [])}")
        else:
            print(f"Failed to update profile: {response.status_code} - {response.text}")
            return
        
        time.sleep(1)
        
        # Step 4: Retrieve again to verify persistence
        print("\nStep 4: Final verification...")
        response = requests.get(f"{BASE_URL}/api/profiles/{profile_id}")
        
        if response.status_code == 200:
            final_profile = response.json()
            print(f"Final retrieval successful")
            print(f"Final NTEE codes: {final_profile.get('ntee_codes', [])}")
            print(f"Final gov criteria: {final_profile.get('government_criteria', [])}")
            
            # Check if data persisted correctly
            expected_ntee = ["A20", "B40", "C50"]
            expected_govt = ["Federal Only", "State Only"]
            
            if final_profile.get('ntee_codes', []) == expected_ntee:
                print("SUCCESS: NTEE codes persisted correctly!")
            else:
                print(f"ERROR: NTEE codes NOT persisted. Expected: {expected_ntee}, Got: {final_profile.get('ntee_codes', [])}")
            
            if final_profile.get('government_criteria', []) == expected_govt:
                print("SUCCESS: Government criteria persisted correctly!")
            else:
                print(f"ERROR: Government criteria NOT persisted. Expected: {expected_govt}, Got: {final_profile.get('government_criteria', [])}")
                
        else:
            print(f"Failed final verification: {response.status_code} - {response.text}")
        
        # Cleanup
        print("\nCleaning up...")
        requests.delete(f"{BASE_URL}/api/profiles/{profile_id}")
        print("Test profile deleted")
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server. Make sure the web server is running on localhost:8000")
    except Exception as e:
        print(f"ERROR: Test failed with error: {e}")

if __name__ == "__main__":
    test_profile_persistence()