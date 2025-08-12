#!/usr/bin/env python3
"""
Test server accessibility
Run this while the server is running to check if it's accessible
"""

import requests
import time
import webbrowser

def test_server():
    print("=" * 50)
    print("TESTING CATALYNX SERVER ACCESSIBILITY")
    print("=" * 50)
    
    server_url = "http://127.0.0.1:8000"
    
    print(f"Testing connection to: {server_url}")
    print()
    
    try:
        # Test basic connection
        print("1. Testing basic connection...")
        response = requests.get(server_url, timeout=10)
        
        if response.status_code == 200:
            print(f"   SUCCESS: Server responded with status {response.status_code}")
            print(f"   Response length: {len(response.text)} characters")
        else:
            print(f"   WARNING: Server responded with status {response.status_code}")
        
        # Test API health endpoint
        print("2. Testing API health endpoint...")
        health_response = requests.get(f"{server_url}/api/health", timeout=5)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   SUCCESS: Health check passed")
            print(f"   Response: {health_data}")
        else:
            print(f"   WARNING: Health check failed with status {health_response.status_code}")
        
        # Test static files
        print("3. Testing static files...")
        static_response = requests.get(f"{server_url}/static/test.html", timeout=5)
        
        if static_response.status_code == 200:
            print(f"   SUCCESS: Static files accessible")
        else:
            print(f"   WARNING: Static files not accessible (status {static_response.status_code})")
        
        print()
        print("=" * 50)
        print("SERVER IS ACCESSIBLE!")
        print("=" * 50)
        print()
        print("You can now access:")
        print(f"- Main Interface: {server_url}")
        print(f"- API Test Page: {server_url}/static/test.html") 
        print(f"- API Docs: {server_url}/api/docs")
        print()
        
        # Ask if user wants to open browser
        open_browser = input("Open browser automatically? (y/n): ").lower().strip()
        if open_browser == 'y':
            print("Opening browser...")
            webbrowser.open(server_url)
        
    except requests.exceptions.ConnectionError:
        print("   ERROR: Cannot connect to server")
        print("   Make sure the server is running:")
        print("   1. Run: python start_catalynx.py")
        print("   2. Wait for 'Server Ready' message")
        print("   3. Then run this test again")
        
    except requests.exceptions.Timeout:
        print("   ERROR: Connection timed out")
        print("   Server might be starting up - wait a moment and try again")
        
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    test_server()