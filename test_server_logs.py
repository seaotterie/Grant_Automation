#!/usr/bin/env python3
"""
Simple test to check if the server is running our updated code
"""

import requests
import json

def test_server_logs():
    """Test if server is running updated code by checking logs"""
    
    print("Testing if server has our debugging updates...")
    print("=" * 50)
    
    try:
        # This request should trigger our debug logging
        response = requests.get("http://localhost:8000/api/profiles?limit=1")
        
        if response.status_code == 200:
            data = response.json()
            profiles = data.get('profiles', [])
            
            if profiles:
                profile = profiles[0]
                print(f"First profile name: {profile.get('name')}")
                print(f"Has ntee_codes field: {'ntee_codes' in profile}")
                print(f"Has government_criteria field: {'government_criteria' in profile}")
                print(f"Has keywords field: {'keywords' in profile}")
                
                print("\nNow check the SERVER TERMINAL/CONSOLE for debug messages like:")
                print("INFO:__main__:ProfileService returned X profiles")
                print("INFO:__main__:Sample profile data: ntee_codes=...")
                print("INFO:__main__:Sample profile dict: ntee_codes=...")
                print("\nIf you don't see these messages, the server needs to be restarted!")
            else:
                print("No profiles returned")
        else:
            print(f"Server error: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_server_logs()