#!/usr/bin/env python3
"""
Test script to validate the new interface features are working
"""

import requests
import json

def test_interface_features():
    """Test that all new interface features are working"""
    base_url = "http://localhost:8000"
    
    print("Testing Catalynx Interface Features...")
    print("=" * 50)
    
    # Test 1: Main page loads
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            print("[OK] Main interface loads successfully")
        else:
            print(f"[ERROR] Main interface failed to load: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to connect to server: {e}")
        return False
    
    # Test 2: API returns discovery fields
    try:
        response = requests.get(f"{base_url}/api/profiles?limit=1")
        if response.status_code == 200:
            data = response.json()
            if data.get("profiles") and len(data["profiles"]) > 0:
                profile = data["profiles"][0]
                required_fields = [
                    'discovery_status', 'last_discovery_date', 'discovery_count',
                    'opportunities_count', 'next_recommended_discovery'
                ]
                
                missing_fields = [field for field in required_fields if field not in profile]
                
                if not missing_fields:
                    print("[OK] API returns all discovery tracking fields")
                    print(f"   - Discovery Status: {profile.get('discovery_status')}")
                    print(f"   - Discovery Count: {profile.get('discovery_count')}")
                    print(f"   - Opportunities Count: {profile.get('opportunities_count')}")
                else:
                    print(f"[ERROR] API missing discovery fields: {missing_fields}")
                    return False
            else:
                print("[ERROR] No profiles returned by API")
                return False
        else:
            print(f"[ERROR] API request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] API test failed: {e}")
        return False
    
    # Test 3: Interface contains expected elements
    try:
        response = requests.get(base_url)
        html_content = response.text
        
        expected_elements = [
            'getDiscoveryStatusClass',  # Discovery status styling function
            'getDiscoveryStatusText',   # Discovery status text function  
            'getDiscoveryButtonText',   # Context-aware button text
            'selectedDiscoveryProfile', # Profile selection variable
            'type="radio"',             # Radio button selection
            'Discovery</th>',           # Discovery column header
            'Selected Profile for Discovery'  # Discovery page section
        ]
        
        missing_elements = []
        for element in expected_elements:
            if element not in html_content:
                missing_elements.append(element)
        
        if not missing_elements:
            print("[OK] Interface contains all expected discovery elements")
        else:
            print(f"[ERROR] Interface missing elements: {missing_elements}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Interface content test failed: {e}")
        return False
    
    print("\n[SUCCESS] ALL TESTS PASSED!")
    print("\nNew Features Available:")
    print("• Discovery status badges in profile tables")
    print("• Radio button selection for discovery profiles") 
    print("• Context-aware discovery buttons")
    print("• Selected profile information on discovery page")
    print("• Discovery history tracking")
    
    return True

if __name__ == "__main__":
    test_interface_features()