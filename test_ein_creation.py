#!/usr/bin/env python3
"""
Test EIN-based profile creation functionality
"""
import requests
import json
import sys
from pathlib import Path

def test_ein_creation():
    """Test the EIN-based profile creation endpoint"""
    
    print("Testing EIN-Based Profile Creation")
    print("=" * 40)
    
    # Test EINs - using well-known nonprofits
    test_eins = [
        "13-1628593",  # American Red Cross
        "31-4617866",  # Goodwill Industries International
        "23-7083797",  # United Way Worldwide
    ]
    
    base_url = "http://localhost:8000"
    
    for i, ein in enumerate(test_eins, 1):
        print(f"\n{i}. Testing EIN: {ein}")
        
        try:
            response = requests.post(
                f"{base_url}/api/profiles/from-ein",
                json={"ein": ein},
                headers={"Content-Type": "application/json"},
                timeout=30  # EIN lookup can take time
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    profile = data.get('profile', {})
                    print(f"   SUCCESS: {profile.get('name', 'Unknown')}")
                    print(f"   Revenue: ${profile.get('annual_revenue', 0):,}" if profile.get('annual_revenue') else "   Revenue: Unknown")
                    print(f"   Address: {profile.get('address', 'Unknown')}")
                    print(f"   Auto-populated fields: {len(data.get('auto_populated_fields', []))}")
                    
                    # Show some key fields
                    focus_areas = profile.get('focus_areas', [])
                    if focus_areas:
                        print(f"   Focus Areas: {', '.join(focus_areas[:2])}...")
                else:
                    print(f"   FAILED: {data.get('message', 'Unknown error')}")
            else:
                print(f"   ERROR: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print("   TIMEOUT: EIN lookup took too long (expected for external API)")
        except Exception as e:
            print(f"   ERROR: {e}")
    
    # Test current profile count
    try:
        response = requests.get(f"{base_url}/api/profiles")
        if response.status_code == 200:
            profiles = response.json().get('profiles', [])
            print(f"\n" + "=" * 40)
            print(f"Total profiles now: {len(profiles)}")
            
            # Show EIN-created profiles
            auto_profiles = [p for p in profiles if p.get('source') == 'ProPublica/IRS lookup']
            print(f"EIN-created profiles: {len(auto_profiles)}")
            
            for profile in auto_profiles[-3:]:  # Show last 3
                revenue_str = f"${profile.get('annual_revenue', 0):,}" if profile.get('annual_revenue') else "Unknown"
                print(f"  - {profile.get('name', 'Unknown')} ({revenue_str})")
                
    except Exception as e:
        print(f"Error checking profiles: {e}")

def main():
    print("EIN Profile Creation Test")
    print("Ensure the server is running at http://localhost:8000")
    print()
    
    # Quick server check
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("Server is running!")
            test_ein_creation()
        else:
            print(f"Server issue: {response.status_code}")
    except Exception as e:
        print(f"Server not accessible: {e}")
        print("\nPlease start the server first:")
        print("python src/web/main.py")

if __name__ == "__main__":
    main()