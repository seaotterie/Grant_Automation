#!/usr/bin/env python3
"""
Test web connection to Catalynx interface
"""

import requests
import time
import sys

def test_connection():
    urls_to_test = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:8000/api/health",
        "http://127.0.0.1:8000/api/system/status"
    ]
    
    print("Testing Catalynx web interface connection...")
    print("=" * 50)
    
    for url in urls_to_test:
        try:
            print(f"Testing: {url}")
            response = requests.get(url, timeout=5)
            print(f"SUCCESS: {response.status_code} - {url}")
            
            if "api" in url:
                try:
                    data = response.json()
                    print(f"   Response: {data}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"   Content length: {len(response.text)} bytes")
            
        except requests.exceptions.ConnectionError:
            print(f"X CONNECTION ERROR: Cannot connect to {url}")
            print("   Make sure the server is running!")
        except requests.exceptions.Timeout:
            print(f"TIMEOUT: {url} took too long to respond")
        except Exception as e:
            print(f"ERROR: {url} - {e}")
        
        print()
    
    print("Connection test completed.")
    print()
    print("If all tests failed, start the server with:")
    print("  launch_catalynx_web.bat")
    print()
    print("If the server is running but connections fail, try:")
    print("  - Check Windows Firewall settings")
    print("  - Try http://127.0.0.1:8000 instead of localhost")
    print("  - Check if another application is using port 8000")

if __name__ == "__main__":
    test_connection()