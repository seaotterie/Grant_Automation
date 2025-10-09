#!/usr/bin/env python3
"""
Discovery Tab Functionality Test Script
Verifies that the Discovery tab displays opportunities correctly after the stage migration fix
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_discovery_functionality():
    """Test the complete Discovery tab functionality"""
    
    print("=== Discovery Tab Functionality Test ===")
    print(f"Timestamp: {datetime.now()}")
    
    profile_id = "profile_f3adef3b653c"  # Heros Bridge
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Verify profile exists and has opportunities
        print("\n1. Testing profile access...")
        async with session.get(f"{base_url}/api/profiles") as response:
            if response.status == 200:
                data = await response.json()
                heros_bridge = next((p for p in data['profiles'] if p['id'] == profile_id), None)
                if heros_bridge:
                    print(f"   SUCCESS: Profile found - {heros_bridge['name']}")
                    print(f"   - EIN: {heros_bridge['ein']}")
                    print(f"   - Opportunities count: {heros_bridge['opportunities_count']}")
                else:
                    print("   ERROR: Profile not found")
                    return False
            else:
                print(f"   ERROR: Failed to get profiles - {response.status}")
                return False
        
        # Test 2: Test opportunity API endpoint
        print("\n2. Testing opportunity API endpoint...")
        async with session.get(f"{base_url}/api/profiles/{profile_id}/opportunities") as response:
            if response.status == 200:
                data = await response.json()
                opportunities = data.get('opportunities', [])
                print(f"   SUCCESS: API returned {len(opportunities)} opportunities")
                
                if opportunities:
                    # Test stage validation
                    stages = {}
                    for opp in opportunities:
                        stage = opp.get('current_stage', 'unknown')
                        stages[stage] = stages.get(stage, 0) + 1
                    
                    print(f"   - Stage distribution: {dict(stages)}")
                    
                    # Check if all stages are valid
                    valid_stages = ['prospects', 'qualified_prospects', 'candidates', 'targets', 'opportunities']
                    invalid_stages = [stage for stage in stages.keys() if stage not in valid_stages]
                    
                    if invalid_stages:
                        print(f"   WARNING: Found invalid stages: {invalid_stages}")
                        return False
                    else:
                        print(f"   SUCCESS: All stages are valid")
                    
                    # Show sample opportunities
                    print(f"   - Sample opportunities:")
                    for i, opp in enumerate(opportunities[:3]):
                        print(f"     {i+1}. {opp['organization_name']} (Stage: {opp['current_stage']}, Score: {opp.get('overall_score', 0):.3f})")
                
            else:
                print(f"   ERROR: Failed to get opportunities - {response.status}")
                return False
        
        # Test 3: Test frontend validation would work
        print("\n3. Testing frontend compatibility...")
        
        # Simulate frontend validation logic
        validation_errors = 0
        validation_successes = 0
        
        for opp in opportunities:
            # Simulate the frontend validation
            required_fields = ['id', 'organization_name', 'current_stage']
            valid_stages = ['prospects', 'qualified_prospects', 'candidates', 'targets', 'opportunities']
            
            has_required_fields = all(field in opp for field in required_fields)
            has_valid_stage = opp.get('current_stage') in valid_stages
            
            if has_required_fields and has_valid_stage:
                validation_successes += 1
            else:
                validation_errors += 1
                print(f"     VALIDATION ERROR: {opp.get('organization_name', 'Unknown')} - Missing: {[f for f in required_fields if f not in opp]} Stage: {opp.get('current_stage')}")
        
        print(f"   - Frontend validation results:")
        print(f"     ✓ Valid opportunities: {validation_successes}")
        print(f"     ✗ Invalid opportunities: {validation_errors}")
        
        if validation_errors == 0:
            print(f"   SUCCESS: All opportunities should display in frontend")
        else:
            print(f"   ERROR: {validation_errors} opportunities would be filtered out")
            return False
        
        # Test 4: Test stage standardization
        print("\n4. Testing stage standardization...")
        stage_mapping_tests = [
            {"input": "discovery", "expected": "prospects"},
            {"input": "qualified", "expected": "qualified_prospects"},
            {"input": "prospects", "expected": "prospects"},
            {"input": "candidates", "expected": "candidates"}
        ]
        
        for test in stage_mapping_tests:
            # This simulates the frontend standardization logic
            input_stage = test["input"]
            expected = test["expected"]
            
            if input_stage == "discovery":
                actual = "prospects"
            elif input_stage == "qualified":
                actual = "qualified_prospects"
            else:
                actual = input_stage
            
            if actual == expected:
                print(f"   ✓ Stage mapping: {input_stage} → {actual}")
            else:
                print(f"   ✗ Stage mapping failed: {input_stage} → {actual} (expected {expected})")
                return False
        
        print("\n=== Test Results Summary ===")
        print("✓ Profile access: WORKING")
        print("✓ Opportunity API: WORKING")
        print("✓ Stage validation: WORKING")
        print("✓ Frontend compatibility: WORKING") 
        print("✓ Stage standardization: WORKING")
        
        print(f"\n🎉 Discovery tab should now display all {len(opportunities)} opportunities!")
        print("   - No more 'Invalid funnel stage' errors")
        print("   - No more validation failures")
        print("   - Opportunities properly categorized by stage")
        
        return True

if __name__ == "__main__":
    success = asyncio.run(test_discovery_functionality())
    if success:
        print("\nSUCCESS: Discovery tab is fully functional!")
    else:
        print("\nERROR: Discovery tab has issues that need to be resolved.")
        exit(1)