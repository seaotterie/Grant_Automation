#!/usr/bin/env python3
"""
Test what API routes are available
"""
import requests
import json

def check_api_routes():
    base_url = "http://localhost:8000"
    
    print("Checking available API routes...")
    
    # Test different profile endpoints
    endpoints_to_test = [
        ("GET", "/api/profiles"),
        ("POST", "/api/profiles"),
        ("POST", "/api/profiles/from-ein"),
        ("GET", "/api/system/status"),
        ("GET", "/api/health"),
    ]
    
    for method, endpoint in endpoints_to_test:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}")
            elif method == "POST":
                # Try with minimal data
                test_data = {"ein": "12-3456789"} if "ein" in endpoint else {"test": "data"}
                response = requests.post(f"{base_url}{endpoint}", json=test_data)
            
            print(f"{method} {endpoint}: {response.status_code}")
            
            if response.status_code == 405:
                print(f"   Method not allowed - endpoint exists but wrong method")
            elif response.status_code == 404:
                print(f"   Endpoint not found")
            elif response.status_code in [200, 400, 422]:
                print(f"   Endpoint available")
            
        except Exception as e:
            print(f"{method} {endpoint}: ERROR - {e}")
    
    # Try to access OpenAPI docs to see all available endpoints
    try:
        response = requests.get(f"{base_url}/openapi.json")
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get('paths', {})
            print(f"\nAll available API paths from OpenAPI:")
            for path, methods in paths.items():
                method_list = list(methods.keys())
                print(f"  {path}: {', '.join(method_list)}")
        else:
            print(f"\nCouldn't get OpenAPI spec: {response.status_code}")
    except Exception as e:
        print(f"\nOpenAPI check error: {e}")

if __name__ == "__main__":
    check_api_routes()