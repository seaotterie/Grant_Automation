#!/usr/bin/env python3
"""
Test script to directly test profile saving with NTEE codes and government criteria
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from profiles.service import ProfileService
from profiles.models import OrganizationProfile
import json

def test_profile_save():
    """Test saving a profile with NTEE codes and government criteria"""
    
    print("Testing Profile Save Functionality")
    print("=" * 40)
    
    # Initialize profile service
    profile_service = ProfileService()
    
    # Test data with NTEE codes and government criteria
    test_profile_data = {
        "name": "Test Nonprofit",
        "organization_type": "nonprofit",
        "ein": "12-3456789",
        "mission_statement": "Test mission for debugging profile persistence",
        "keywords": "test, debugging, persistence",
        "focus_areas": ["Education", "Health"],
        "target_populations": ["Children", "Adults"],
        "geographic_scope": {
            "states": ["VA"],
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
        "ntee_codes": ["B25", "E32", "P20"],
        "government_criteria": ["Federal Grants", "State Programs", "Local Funding"]
    }
    
    try:
        # Step 1: Create profile
        print("Step 1: Creating profile...")
        created_profile = profile_service.create_profile(test_profile_data)
        
        print(f"Profile created with ID: {created_profile.profile_id}")
        print(f"NTEE codes in created profile: {created_profile.ntee_codes}")
        print(f"Government criteria in created profile: {created_profile.government_criteria}")
        print(f"Keywords in created profile: {created_profile.keywords}")
        
        # Step 2: Retrieve the profile
        print("\nStep 2: Retrieving profile...")
        retrieved_profile = profile_service.get_profile(created_profile.profile_id)
        
        if retrieved_profile:
            print(f"Profile retrieved successfully")
            print(f"NTEE codes in retrieved profile: {retrieved_profile.ntee_codes}")
            print(f"Government criteria in retrieved profile: {retrieved_profile.government_criteria}")
            print(f"Keywords in retrieved profile: {retrieved_profile.keywords}")
        else:
            print("Failed to retrieve profile")
            return
        
        # Step 3: Update the profile
        print("\nStep 3: Updating profile...")
        update_data = {
            "ntee_codes": ["A20", "B40", "C50"],
            "government_criteria": ["Federal Only", "State Only"],
            "keywords": "updated, test, keywords"
        }
        
        updated_profile = profile_service.update_profile(created_profile.profile_id, update_data)
        
        if updated_profile:
            print(f"Profile updated successfully")
            print(f"NTEE codes after update: {updated_profile.ntee_codes}")
            print(f"Government criteria after update: {updated_profile.government_criteria}")
            print(f"Keywords after update: {updated_profile.keywords}")
        else:
            print("Failed to update profile")
            return
        
        # Step 4: Retrieve again
        print("\nStep 4: Final verification...")
        final_profile = profile_service.get_profile(created_profile.profile_id)
        
        if final_profile:
            print(f"Final verification successful")
            print(f"Final NTEE codes: {final_profile.ntee_codes}")
            print(f"Final government criteria: {final_profile.government_criteria}")
            print(f"Final keywords: {final_profile.keywords}")
            
            # Check if data persisted
            expected_ntee = ["A20", "B40", "C50"]
            expected_govt = ["Federal Only", "State Only"]
            expected_keywords = "updated, test, keywords"
            
            if final_profile.ntee_codes == expected_ntee:
                print("SUCCESS: NTEE codes persisted correctly!")
            else:
                print(f"ERROR: NTEE codes not persisted. Expected: {expected_ntee}, Got: {final_profile.ntee_codes}")
            
            if final_profile.government_criteria == expected_govt:
                print("SUCCESS: Government criteria persisted correctly!")
            else:
                print(f"ERROR: Government criteria not persisted. Expected: {expected_govt}, Got: {final_profile.government_criteria}")
            
            if final_profile.keywords == expected_keywords:
                print("SUCCESS: Keywords persisted correctly!")
            else:
                print(f"ERROR: Keywords not persisted. Expected: {expected_keywords}, Got: {final_profile.keywords}")
        else:
            print("Failed final verification")
        
        # Cleanup
        print("\nCleaning up...")
        profile_service.delete_profile(created_profile.profile_id)
        print("Test profile deleted")
        
        # Show the actual saved file
        print(f"\nChecking saved file at: data/profiles/profiles/{created_profile.profile_id}.json")
        try:
            with open(f"data/profiles/profiles/{created_profile.profile_id}.json", 'r') as f:
                saved_data = json.load(f)
                print("Saved file contents:")
                print(f"  ntee_codes: {saved_data.get('ntee_codes', 'MISSING')}")
                print(f"  government_criteria: {saved_data.get('government_criteria', 'MISSING')}")
                print(f"  keywords: {saved_data.get('keywords', 'MISSING')}")
        except Exception as e:
            print(f"Could not read saved file: {e}")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_profile_save()