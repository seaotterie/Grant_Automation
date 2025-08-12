#!/usr/bin/env python3
"""
Test profile loading to see if discovery fields are properly loaded
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from profiles.service import ProfileService

def test_profile_loading():
    """Test that profiles load with new discovery fields"""
    service = ProfileService()
    
    # Get all profiles
    profiles = service.list_profiles(limit=3)
    
    print(f"Found {len(profiles)} profiles")
    
    for profile in profiles:
        print(f"\nProfile: {profile.name}")
        print(f"  Discovery Status: {profile.discovery_status}")
        print(f"  Last Discovery: {profile.last_discovery_date}")
        print(f"  Discovery Count: {profile.discovery_count}")
        print(f"  Opportunities Count: {profile.opportunities_count}")
        print(f"  Next Recommended: {profile.next_recommended_discovery}")
        
        # Test the model_dump method
        profile_dict = profile.model_dump()
        discovery_fields = [
            'discovery_status', 'last_discovery_date', 'discovery_count', 
            'opportunities_count', 'next_recommended_discovery'
        ]
        
        print("  Fields in model_dump:")
        for field in discovery_fields:
            print(f"    {field}: {profile_dict.get(field, 'MISSING')}")

if __name__ == "__main__":
    test_profile_loading()