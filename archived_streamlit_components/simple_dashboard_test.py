#!/usr/bin/env python3
"""
Simple Dashboard Test
Test dashboard accessibility without Unicode characters.
"""

import requests
import time
import sys

def test_dashboard_access():
    print("Testing dashboard accessibility...")
    
    # Test common ports
    ports_to_test = [8501, 8502, 8503]
    
    for port in ports_to_test:
        try:
            url = f"http://127.0.0.1:{port}"
            print(f"Testing {url}...")
            
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"SUCCESS: Dashboard accessible at {url}")
                print(f"Response length: {len(response.text)} characters")
                return True
            else:
                print(f"Port {port}: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"Port {port}: No service running")
        except requests.exceptions.Timeout:
            print(f"Port {port}: Timeout")
        except Exception as e:
            print(f"Port {port}: Error - {str(e)}")
    
    print("No accessible dashboard found on tested ports")
    return False

def start_dashboard_instructions():
    print("\nTo start the dashboard manually:")
    print("1. Open Command Prompt in this directory")
    print("2. Run one of these commands:")
    print('   "grant-research-env\\Scripts\\streamlit.exe" run src\\dashboard\\analytics_dashboard.py')
    print('   "grant-research-env\\Scripts\\streamlit.exe" run src\\dashboard\\app.py --server.port 8502')
    print("3. Open browser to http://localhost:8501 or http://localhost:8502")

if __name__ == "__main__":
    success = test_dashboard_access()
    
    if not success:
        start_dashboard_instructions()
    
    print("\n" + "="*50)
    print("Dashboard connectivity test complete")