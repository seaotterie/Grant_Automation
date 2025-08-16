#!/usr/bin/env python3
"""
Test script to verify multi-profile opportunity persistence.
Tests the scenario mentioned by the user: switching between profiles and ensuring
opportunities persist correctly.
"""

import asyncio
import json
import aiohttp
from datetime import datetime

class MultiProfileTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def setup(self):
        """Setup async HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Cleanup async HTTP session"""
        if self.session:
            await self.session.close()
            
    async def get_profiles(self):
        """Get list of available profiles"""
        async with self.session.get(f"{self.base_url}/api/profiles") as response:
            if response.status == 200:
                data = await response.json()
                profiles = data.get('profiles', [])
                print(f"Found {len(profiles)} profiles")
                return profiles
            else:
                print(f"Failed to get profiles: {response.status}")
                return []
                
    async def get_profile_opportunities(self, profile_id):
        """Get opportunities for a specific profile"""
        async with self.session.get(f"{self.base_url}/api/profiles/{profile_id}/opportunities") as response:
            if response.status == 200:
                data = await response.json()
                opportunities = data.get('opportunities', [])
                count = data.get('total_opportunities', 0)
                print(f"Profile {profile_id}: {count} opportunities found")
                return opportunities
            elif response.status == 404:
                print(f"Profile {profile_id}: No opportunities found (404)")
                return []
            else:
                print(f"Profile {profile_id}: Failed to get opportunities - {response.status}")
                return []
                
    async def run_discovery_for_profile(self, profile_id):
        """Run unified discovery for a profile"""
        discovery_data = {
            "funding_types": ["nonprofit", "government", "commercial", "state"],
            "max_results_per_type": 10,
            "discovery_mode": "test"
        }
        
        async with self.session.post(
            f"{self.base_url}/api/profiles/{profile_id}/discover/unified",
            json=discovery_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                opportunities_found = result.get('total_opportunities_found', 0)
                print(f"Discovery completed for {profile_id}: {opportunities_found} opportunities found")
                return result
            else:
                print(f"Discovery failed for {profile_id}: {response.status}")
                return None
                
    async def test_multi_profile_scenario(self):
        """Test the multi-profile persistence scenario"""
        print("=" * 60)
        print("MULTI-PROFILE OPPORTUNITY PERSISTENCE TEST")
        print("=" * 60)
        
        # Get available profiles
        profiles = await self.get_profiles()
        if len(profiles) < 2:
            print("ERROR: Need at least 2 profiles for testing")
            return False
            
        # Select first two profiles for testing
        profile1 = profiles[0]
        profile2 = profiles[1]
        
        profile1_id = profile1['profile_id']
        profile2_id = profile2['profile_id']
        profile1_name = profile1['name']
        profile2_name = profile2['name']
        
        print(f"\nTesting with:")
        print(f"  Profile 1: {profile1_name} ({profile1_id})")
        print(f"  Profile 2: {profile2_name} ({profile2_id})")
        
        # STEP 1: Check initial state
        print(f"\n1. Checking initial opportunities...")
        initial_opps_1 = await self.get_profile_opportunities(profile1_id)
        initial_opps_2 = await self.get_profile_opportunities(profile2_id)
        
        # STEP 2: Run discovery for Profile 1
        print(f"\n2. Running discovery for {profile1_name}...")
        discovery_result_1 = await self.run_discovery_for_profile(profile1_id)
        
        if discovery_result_1:
            # Check opportunities after discovery
            post_discovery_opps_1 = await self.get_profile_opportunities(profile1_id)
            print(f"   Before: {len(initial_opps_1)} opportunities")
            print(f"   After: {len(post_discovery_opps_1)} opportunities")
            
        # STEP 3: Switch to Profile 2 and check it doesn't have Profile 1's opportunities
        print(f"\n3. Checking {profile2_name} opportunities (should be unchanged)...")
        opps_2_after_1_discovery = await self.get_profile_opportunities(profile2_id)
        
        if len(opps_2_after_1_discovery) == len(initial_opps_2):
            print("   PASS: Profile 2 opportunities unchanged (good)")
        else:
            print("   FAIL: Profile 2 opportunities changed unexpectedly")
            
        # STEP 4: Run discovery for Profile 2
        print(f"\n4. Running discovery for {profile2_name}...")
        discovery_result_2 = await self.run_discovery_for_profile(profile2_id)
        
        if discovery_result_2:
            post_discovery_opps_2 = await self.get_profile_opportunities(profile2_id)
            print(f"   Before: {len(initial_opps_2)} opportunities")
            print(f"   After: {len(post_discovery_opps_2)} opportunities")
            
        # STEP 5: Switch back to Profile 1 and verify opportunities are still there
        print(f"\n5. Switching back to {profile1_name} - checking persistence...")
        final_opps_1 = await self.get_profile_opportunities(profile1_id)
        
        if discovery_result_1 and len(final_opps_1) >= len(post_discovery_opps_1):
            print("   PASS: Profile 1 opportunities persisted correctly")
            persistence_success = True
        else:
            print("   FAIL: Profile 1 opportunities were lost!")
            persistence_success = False
            
        # STEP 6: Final verification
        print(f"\n6. Final verification...")
        final_opps_2 = await self.get_profile_opportunities(profile2_id)
        
        print(f"Final state:")
        print(f"  {profile1_name}: {len(final_opps_1)} opportunities")
        print(f"  {profile2_name}: {len(final_opps_2)} opportunities")
        
        # Test results
        print(f"\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        
        if persistence_success:
            print("PASS: Opportunities persist correctly across profile switches")
        else:
            print("FAIL: Opportunities are lost when switching profiles")
            
        return persistence_success

async def main():
    """Main test function"""
    tester = MultiProfileTester()
    await tester.setup()
    
    try:
        success = await tester.test_multi_profile_scenario()
        if success:
            print("\nAll tests passed!")
            return 0
        else:
            print("\nSome tests failed!")
            return 1
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        return 1
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)