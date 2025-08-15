#!/usr/bin/env python3
"""
Test EIN lookup integration with real IRS BMF data.
This script tests the EIN lookup functionality to ensure profiles
can be populated with real organization data.
"""

import asyncio
import json
import requests
import time

# Test EINs - real organizations
TEST_EINS = [
    "13-1684331",  # Ford Foundation (from existing profile)
    "81-2827604",  # Heros Bridge (from existing profile) 
    "13-1624296",  # American Red Cross
    "31-1611044",  # Salvation Army
    "52-1693387",  # United Way Worldwide
]

def test_ein_lookup_api():
    """Test EIN lookup via API endpoints"""
    print("=" * 60)
    print("TESTING EIN LOOKUP VIA API")
    print("=" * 60)
    
    results = []
    base_url = "http://127.0.0.1:8000"
    
    for ein in TEST_EINS:
        print(f"\n[INFO] Testing EIN: {ein}")
        
        try:
            # Test EIN lookup API endpoint
            response = requests.post(f"{base_url}/api/profiles/fetch-ein", json={"ein": ein}, timeout=30)
            
            if response.status_code == 200:
                api_response = response.json()
                if api_response.get('success', False):
                    org_data = api_response.get('data', {})
                    print(f"[SUCCESS] EIN Lookup Success: {org_data.get('name', 'Unknown')}")
                    print(f"   Revenue: ${org_data.get('revenue', 0):,}")
                    print(f"   State: {org_data.get('state', 'N/A')}")
                    print(f"   Organization Type: {org_data.get('organization_type', 'N/A')}")
                    print(f"   NTEE Code: {org_data.get('ntee_code', 'N/A')}")
                    print(f"   City: {org_data.get('city', 'N/A')}")
                else:
                    print(f"[ERROR] API returned success=false: {api_response.get('message', 'Unknown error')}")
                    org_data = {}
                
                results.append({
                    "ein": ein,
                    "success": api_response.get('success', False),
                    "organization": org_data
                })
                
            else:
                print(f"[ERROR] EIN Lookup Failed: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                results.append({
                    "ein": ein,
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text[:100]}"
                })
                
        except Exception as e:
            print(f"[ERROR] Exception during EIN lookup: {str(e)}")
            results.append({
                "ein": ein,
                "success": False,
                "error": str(e)
            })
        
        # Small delay between requests
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("EIN LOOKUP API TEST SUMMARY")
    print("=" * 60)
    
    successful_lookups = [r for r in results if r.get("success", False)]
    print(f"Total EINs tested: {len(results)}")
    print(f"Successful lookups: {len(successful_lookups)}")
    print(f"Success rate: {len(successful_lookups)/len(results)*100:.1f}%" if results else "No tests run")
    
    if successful_lookups:
        print("\n[SUMMARY] Successful Organizations:")
        for result in successful_lookups:
            org = result.get("organization", {})
            print(f"   - {org.get('name', 'Unknown')} ({result['ein']})")
            print(f"     Revenue: ${org.get('revenue', 0):,}")
            print(f"     Type: {org.get('organization_type', 'N/A')}")
            print(f"     State: {org.get('state', 'N/A')}")
    
    return results

def test_profile_creation_api():
    """Test profile creation with EIN auto-population"""
    print("\n" + "=" * 60)
    print("TESTING PROFILE CREATION WITH EIN AUTO-POPULATION")
    print("=" * 60)
    
    test_ein = "13-1624296"  # American Red Cross
    base_url = "http://127.0.0.1:8000"
    
    try:
        # First test EIN lookup
        print(f"[INFO] Testing EIN lookup for: {test_ein}")
        lookup_response = requests.post(f"{base_url}/api/profiles/fetch-ein", json={"ein": test_ein}, timeout=30)
        
        if lookup_response.status_code == 200:
            api_response = lookup_response.json()
            if api_response.get('success', False):
                ein_data = api_response.get('data', {})
                print(f"[SUCCESS] EIN Lookup Success: {ein_data.get('name', 'Unknown')}")
                print(f"   Revenue: ${ein_data.get('revenue', 0):,}")
                print(f"   State: {ein_data.get('state', 'N/A')}")
                
                # Create a profile with this data
                profile_data = {
                    "name": ein_data.get("name", "Test Organization"),
                    "organization_type": ein_data.get("organization_type", "nonprofit"),
                    "ein": test_ein,
                    "mission_statement": ein_data.get("mission_statement", "Test mission statement from EIN lookup integration"),
                    "focus_areas": ["education", "health"],
                    "geographic_scope": {
                        "states": [ein_data.get("state", "VA")],
                        "nationwide": False,
                        "international": False
                    },
                    "annual_revenue": ein_data.get("revenue", 0)
                }
            else:
                print(f"[ERROR] EIN Lookup returned success=false: {api_response.get('message', 'Unknown error')}")
                return None
            
            print(f"[INFO] Creating profile with EIN data...")
            create_response = requests.post(f"{base_url}/api/profiles", json=profile_data, timeout=30)
            
            if create_response.status_code == 200:
                created_profile = create_response.json()
                print(f"[SUCCESS] Profile Created Successfully!")
                print(f"   Profile ID: {created_profile.get('profile_id', 'Unknown')}")
                print(f"   Name: {created_profile.get('name', 'Unknown')}")
                print(f"   Revenue: ${created_profile.get('annual_revenue', 0):,}")
                print(f"   EIN: {created_profile.get('ein', 'N/A')}")
                print(f"   State: {created_profile.get('geographic_scope', {}).get('states', ['N/A'])[0] if created_profile.get('geographic_scope', {}).get('states') else 'N/A'}")
                return created_profile
            else:
                print(f"[ERROR] Profile Creation Failed: HTTP {create_response.status_code}")
                print(f"   Response: {create_response.text[:200]}...")
                return None
        else:
            print(f"[ERROR] EIN Lookup Failed: HTTP {lookup_response.status_code}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Exception during profile creation test: {str(e)}")
        return None

def main():
    """Run all EIN lookup integration tests"""
    print("[START] Starting EIN Lookup Integration Tests...")
    print("   Server should be running at: http://localhost:8000")
    
    # Wait for server to be ready
    print("[INFO] Waiting for server to be ready...")
    time.sleep(3)
    
    # Test basic EIN lookup functionality
    lookup_results = test_ein_lookup_api()
    
    # Test profile creation with EIN data
    profile_data = test_profile_creation_api()
    
    print(f"\n[COMPLETE] EIN Lookup Integration Testing Complete!")
    print(f"   Successful lookups: {len([r for r in lookup_results if r.get('success', False)])}/{len(lookup_results)}")
    print(f"   View the web interface at: http://localhost:8000")
    print(f"   Test profile creation with real EIN data in the PROFILER tab")

if __name__ == "__main__":
    main()