#!/usr/bin/env python3
"""
Test GUI integration with real profiles and nonprofit discovery
"""
import asyncio
import webbrowser
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.web.main import app
import uvicorn
import threading
import time

def start_server_background():
    """Start the FastAPI server in background"""
    config = uvicorn.Config(
        app, 
        host="127.0.0.1", 
        port=8000, 
        log_level="info",
        reload=False
    )
    server = uvicorn.Server(config)
    
    # Run server in background thread
    def run_server():
        asyncio.run(server.serve())
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give server time to start
    time.sleep(3)
    
    return server

def main():
    print("Starting Catalynx GUI Integration Test")
    print("=" * 40)
    
    # Start server
    print("1. Starting web server on http://localhost:8000...")
    server = start_server_background()
    
    # Test API accessibility
    print("2. Testing API endpoints...")
    import requests
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/api/health")
        if response.status_code == 200:
            print("   API Health: OK")
        
        # Test profiles endpoint
        response = requests.get("http://localhost:8000/api/profiles")
        if response.status_code == 200:
            data = response.json()
            profiles = data.get('profiles', [])
            print(f"   Profiles Available: {len(profiles)}")
            
            if profiles:
                print("   Sample Profiles:")
                for i, profile in enumerate(profiles[:3], 1):
                    print(f"     {i}. {profile['name']} ({profile.get('opportunities_count', 0)} opportunities)")
        
        # Test system status
        response = requests.get("http://localhost:8000/api/system/status")
        if response.status_code == 200:
            data = response.json()
            print(f"   System Status: {data.get('status', 'unknown')}")
            print(f"   Processors Available: {data.get('processors_available', 0)}")
    
    except Exception as e:
        print(f"   API Test Error: {e}")
    
    print("\n3. Opening web interface...")
    print("   URL: http://localhost:8000")
    print("   Navigate to READIFIER -> Profiler to see the 5 sample profiles")
    print("   Click 'Discover Opportunities' to test nonprofit discovery integration")
    
    # Open browser
    try:
        webbrowser.open("http://localhost:8000")
        print("   Browser opened successfully")
    except Exception as e:
        print(f"   Browser open error: {e}")
    
    print("\nGUI Integration Test Complete!")
    print("=" * 40)
    print("\nTesting Instructions:")
    print("1. Check that profiles load in the READIFIER section")
    print("2. Try creating a new profile using the form")
    print("3. Test the 'Discover Opportunities' button on existing profiles")
    print("4. Verify WebSocket connection status indicator")
    print("\nPress Ctrl+C to stop server when done testing...")
    
    try:
        # Keep server running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down server...")

if __name__ == "__main__":
    main()