#!/usr/bin/env python3
"""
Simple test to run and check Catalynx server
"""

import subprocess
import time
import urllib.request
import threading
import sys
import os

def test_connection():
    """Test if server is responding"""
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            print(f"Attempt {attempt + 1}/{max_attempts}: Testing connection...")
            response = urllib.request.urlopen('http://127.0.0.1:8000/api/test', timeout=5)
            print(f"SUCCESS: Server responding with status {response.status}")
            content = response.read().decode()
            print("Server is working properly!")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            if attempt < max_attempts - 1:
                print("Waiting 2 seconds before retry...")
                time.sleep(2)
    
    return False

def main():
    print("=" * 60)
    print("CATALYNX SERVER TEST")
    print("=" * 60)
    
    # Change to web directory
    web_dir = os.path.join(os.getcwd(), "src", "web")
    if not os.path.exists(web_dir):
        print("ERROR: Web directory not found!")
        return False
    
    os.chdir(web_dir)
    print(f"Changed to directory: {web_dir}")
    
    # Start server in background
    python_exe = os.path.join("..", "..", "grant-research-env", "Scripts", "python.exe")
    
    print("Starting server...")
    server_process = subprocess.Popen(
        [python_exe, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print("Server started, waiting for it to be ready...")
    time.sleep(5)  # Give server time to start
    
    # Test connection
    success = test_connection()
    
    if success:
        print("\nSUCCESS: Server is running and accessible!")
        print("You can now open your browser and go to: http://127.0.0.1:8000")
        print("\nPress Enter to stop the server...")
        input()
    else:
        print("\nERROR: Could not connect to server")
        # Check server output
        try:
            stdout, stderr = server_process.communicate(timeout=1)
            if stdout:
                print("Server stdout:", stdout[:500])
            if stderr:
                print("Server stderr:", stderr[:500])
        except:
            pass
    
    # Stop server
    server_process.terminate()
    print("Server stopped.")

if __name__ == "__main__":
    main()