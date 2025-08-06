#!/usr/bin/env python3
"""
Check if Catalynx server is accessible
"""

import socket
import time
import sys

def check_port(host, port):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Socket error: {e}")
        return False

def check_http_response():
    """Try to get a simple HTTP response"""
    try:
        import urllib.request
        import urllib.error
        
        url = "http://127.0.0.1:8000"
        print(f"Testing HTTP request to {url}...")
        
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            print(f"HTTP Response: {status}")
            
            if status == 200:
                content_length = len(response.read())
                print(f"Content length: {content_length} bytes")
                return True
            else:
                print(f"Unexpected status code: {status}")
                return False
                
    except urllib.error.URLError as e:
        print(f"URL Error: {e}")
        return False
    except Exception as e:
        print(f"HTTP Error: {e}")
        return False

def main():
    print("=" * 50)
    print("CATALYNX CONNECTION TEST")
    print("=" * 50)
    
    host = "127.0.0.1"
    port = 8000
    
    print(f"Testing connection to {host}:{port}")
    print()
    
    # Test 1: Check if port is open
    print("1. Testing port connectivity...")
    if check_port(host, port):
        print("   ✓ Port 8000 is open and accepting connections")
    else:
        print("   ✗ Port 8000 is not accessible")
        print("   → Make sure the server is running")
        print("   → Run: python simple_server.py")
        return
    
    # Test 2: Try HTTP request
    print("\n2. Testing HTTP response...")
    if check_http_response():
        print("   ✓ HTTP server is responding correctly")
        print("   ✓ Website should be accessible!")
        print()
        print("SUCCESS: Server is working!")
        print("Open your browser and go to: http://127.0.0.1:8000")
    else:
        print("   ✗ HTTP server is not responding properly")
        print("   → Server might be starting up - wait a moment and try again")
        print("   → Check for error messages in the server console")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()