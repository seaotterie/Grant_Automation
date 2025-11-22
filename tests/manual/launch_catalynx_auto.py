#!/usr/bin/env python3
"""
Catalynx Auto Launcher
Automatically starts server if needed and opens browser
Best for development workflow
"""

import sys
import os
import subprocess
import time
import webbrowser
import requests
from pathlib import Path

def check_server_health(timeout=10):
    """Check if server is running and healthy."""
    for _ in range(timeout):
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=2)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False

def start_server_if_needed():
    """Start server only if it's not already running."""
    if check_server_health(timeout=2):
        print("SUCCESS: Server is already running")
        return True
    
    print("Starting Catalynx server...")
    
    # Use the service manager to start in background
    service_script = Path(__file__).parent / "start_catalynx_service.py"
    if service_script.exists():
        result = subprocess.run([sys.executable, str(service_script), "start"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("SUCCESS: Server started via service manager")
        else:
            print(f"Service manager output: {result.stdout}")
            print(f"Service manager error: {result.stderr}")
    else:
        # Fallback: start directly
        print("Starting server directly...")
        subprocess.Popen([
            sys.executable, "src/web/main.py"
        ], start_new_session=True)
    
    # Wait for server to be ready
    print("Waiting for server to be ready...")
    if check_server_health(timeout=15):
        print("SUCCESS: Server is ready")
        return True
    else:
        print("FAILED: Server failed to start or become ready")
        return False

def open_browser():
    """Open the default browser to the application."""
    url = "http://localhost:8000"
    print(f"Opening browser to: {url}")
    try:
        webbrowser.open(url)
        print("SUCCESS: Browser opened")
    except Exception as e:
        print(f"Could not open browser: {e}")
        print(f"Please manually navigate to: {url}")

def main():
    """Main launcher function."""
    print("Catalynx Auto Launcher")
    print("=" * 40)
    
    if start_server_if_needed():
        open_browser()
        print("\nServer is running in background.")
        print("You can close this terminal - the server will continue running.")
        print("To stop the server later, use: python start_catalynx_service.py stop")
    else:
        print("Failed to start server. Check the logs for details.")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()