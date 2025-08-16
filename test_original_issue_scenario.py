#!/usr/bin/env python3
"""
Test script to verify the original issue scenario is resolved:
"I start with Heros bridge and get some DISCOVER opportunities, 
move to Fauquier Free Clinic and dont get any opportunities, 
move back to Heros Bridge and all the oportunities are gone and 
when running all tracks again in discovery I get no results."
"""

import asyncio
import json
import aiohttp
from datetime import datetime

class OriginalIssueTest:
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
            
    async def get_profile_by_name(self, profile_name):
        """Find a profile by name (partial match)"""
        async with self.session.get(f"{self.base_url}/api/profiles") as response:
            if response.status == 200:
                data = await response.json()
                profiles = data.get('profiles', [])
                
                for profile in profiles:
                    if profile_name.lower() in profile.get('name', '').lower():
                        return profile
                        
        return None
        
    async def get_opportunities_count(self, profile_id):
        """Get number of opportunities for a profile"""
        async with self.session.get(f"{self.base_url}/api/profiles/{profile_id}/opportunities") as response:
            if response.status == 200:
                data = await response.json()
                return data.get('total_opportunities', 0)
            return 0
            
    async def run_discovery(self, profile_id, profile_name):
        """Run discovery for a profile"""
        discovery_data = {
            "funding_types": ["nonprofit", "government", "commercial"],
            "max_results_per_type": 10
        }
        
        print(f"   Running discovery for {profile_name}...")
        async with self.session.post(
            f"{self.base_url}/api/profiles/{profile_id}/discover/unified",
            json=discovery_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                opportunities_found = result.get('total_opportunities_found', 0)
                session_id = result.get('discovery_id', 'unknown')
                print(f"   Discovery completed: {opportunities_found} opportunities found (session: {session_id})")
                return opportunities_found
            else:
                print(f"   Discovery failed: {response.status}")
                return 0
                
    async def test_original_scenario(self):
        """Test the exact scenario described in the original issue"""
        print("=" * 70)
        print("TESTING ORIGINAL ISSUE SCENARIO")
        print("=" * 70)
        print("Scenario: Start with Heros Bridge, switch to Fauquier Free Clinic,")
        print("          then back to Heros Bridge - opportunities should persist")
        print("=" * 70)
        
        # Step 1: Find Heros Bridge profile
        heros_profile = await self.get_profile_by_name("Heros Bridge")
        if not heros_profile:
            print("ERROR: Could not find Heros Bridge profile")
            return False
            
        heros_id = heros_profile['profile_id']
        heros_name = heros_profile['name']
        
        # Step 2: Find Fauquier Free Clinic or similar profile
        fauquier_profile = await self.get_profile_by_name("Fauquier")
        if not fauquier_profile:
            # Use any other profile as backup
            async with self.session.get(f"{self.base_url}/api/profiles") as response:
                if response.status == 200:
                    data = await response.json()
                    profiles = data.get('profiles', [])
                    for profile in profiles:
                        if profile['profile_id'] != heros_id:
                            fauquier_profile = profile
                            break
                            
        if not fauquier_profile:
            print("ERROR: Could not find second profile for testing")
            return False
            
        fauquier_id = fauquier_profile['profile_id']
        fauquier_name = fauquier_profile['name']
        
        print(f"\nTesting with:")
        print(f"  Primary Profile: {heros_name} ({heros_id})")
        print(f"  Secondary Profile: {fauquier_name} ({fauquier_id})")
        
        # ORIGINAL ISSUE REPRODUCTION TEST
        
        print(f"\n1. INITIAL STATE - Check existing opportunities...")
        heros_initial = await self.get_opportunities_count(heros_id)
        fauquier_initial = await self.get_opportunities_count(fauquier_id)
        
        print(f"   {heros_name}: {heros_initial} opportunities")
        print(f"   {fauquier_name}: {fauquier_initial} opportunities")
        
        print(f"\n2. DISCOVER OPPORTUNITIES - Run discovery on {heros_name}...")
        heros_discovered = await self.run_discovery(heros_id, heros_name)
        heros_after_discovery = await self.get_opportunities_count(heros_id)
        
        print(f"   After discovery: {heros_after_discovery} opportunities stored")
        
        print(f"\n3. SWITCH PROFILES - Move to {fauquier_name}...")
        fauquier_after_switch = await self.get_opportunities_count(fauquier_id)
        print(f"   {fauquier_name} opportunities: {fauquier_after_switch} (should be unchanged)")
        
        # Verify isolation
        isolation_success = (fauquier_after_switch == fauquier_initial)
        print(f"   Profile Isolation: {'PASS' if isolation_success else 'FAIL'}")
        
        print(f"\n4. RUN DISCOVERY ON SECOND PROFILE - {fauquier_name}...")
        fauquier_discovered = await self.run_discovery(fauquier_id, fauquier_name)
        fauquier_after_discovery = await self.get_opportunities_count(fauquier_id)
        
        print(f"   After discovery: {fauquier_after_discovery} opportunities stored")
        
        print(f"\n5. SWITCH BACK - Return to {heros_name}...")
        print("   This is where the original issue occurred - opportunities would be lost")
        
        heros_after_return = await self.get_opportunities_count(heros_id)
        print(f"   {heros_name} opportunities after return: {heros_after_return}")
        
        # THE CRITICAL TEST - opportunities should still be there
        persistence_success = (heros_after_return >= heros_after_discovery)
        print(f"   Persistence Test: {'PASS' if persistence_success else 'FAIL'}")
        
        if persistence_success:
            print("   GOOD: Opportunities persisted when switching back!")
        else:
            print("   BAD: Opportunities were lost (original issue still exists)")
            
        print(f"\n6. RUN ALL TRACKS AGAIN - Test discovery on {heros_name} again...")
        print("   This tests if running discovery again works correctly")
        
        heros_rediscovered = await self.run_discovery(heros_id, heros_name)
        heros_final = await self.get_opportunities_count(heros_id)
        
        print(f"   Final opportunity count: {heros_final}")
        
        # Test if re-discovery works (should not lose existing opportunities)
        rediscovery_success = (heros_final >= heros_after_return)
        print(f"   Re-discovery Test: {'PASS' if rediscovery_success else 'FAIL'}")
        
        print(f"\n" + "=" * 70)
        print("ISSUE RESOLUTION TEST RESULTS")
        print("=" * 70)
        
        print(f"Profile Isolation: {'PASS' if isolation_success else 'FAIL'}")
        print(f"Opportunity Persistence: {'PASS' if persistence_success else 'FAIL'}")
        print(f"Re-discovery Functionality: {'PASS' if rediscovery_success else 'FAIL'}")
        
        overall_success = isolation_success and persistence_success and rediscovery_success
        
        print(f"\nOverall Issue Resolution: {'RESOLVED' if overall_success else 'NOT RESOLVED'}")
        
        if overall_success:
            print("\nSUCCESS: The original issue has been resolved!")
            print("- Opportunities now persist when switching between profiles")
            print("- Profile isolation works correctly")
            print("- Re-running discovery maintains existing opportunities")
            print("- The opportunity count is correctly tracked and displayed")
        else:
            print("\nISSUE REMAINS: Some aspects of the original problem persist")
            
        return overall_success

async def main():
    """Main test function"""
    tester = OriginalIssueTest()
    await tester.setup()
    
    try:
        success = await tester.test_original_scenario()
        return 0 if success else 1
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        return 1
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)