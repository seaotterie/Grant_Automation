#!/usr/bin/env python3
"""
Quick demo script to test Catalynx functionality
"""
import subprocess
import webbrowser
import time
import requests
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_profile_system():
    """Quick test of profile system"""
    from src.profiles.service import ProfileService
    
    profile_service = ProfileService()
    profiles = profile_service.list_profiles()
    
    print(f"Profile System Status:")
    print(f"  - Total profiles: {len(profiles)}")
    
    if profiles:
        print("  - Sample profiles:")
        for i, profile in enumerate(profiles[:3], 1):
            revenue = f"${profile.annual_revenue:,}" if profile.annual_revenue else "N/A"
            print(f"    {i}. {profile.name} - {revenue}")
    
    return len(profiles) > 0

def start_server():
    """Start server and wait for it to be ready"""
    print("Starting Catalynx server...")
    
    # Start server process
    process = subprocess.Popen([
        "grant-research-env/Scripts/python.exe", 
        "src/web/main.py"
    ], 
    stdout=subprocess.PIPE, 
    stderr=subprocess.PIPE, 
    text=True
    )
    
    # Wait for server to start
    for i in range(10):
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=2)
            if response.status_code == 200:
                print("✓ Server ready at http://localhost:8000")
                return process
        except:
            pass
        time.sleep(1)
        print(f"  Waiting for server... ({i+1}/10)")
    
    print("✗ Server failed to start")
    return None

def main():
    print("Catalynx Quick Demo - 15 Minute Test")
    print("=" * 40)
    
    # Test 1: Profile system
    print("1. Testing profile system...")
    profiles_ok = test_profile_system()
    
    if not profiles_ok:
        print("✗ No profiles found - run test_profile_creation.py first")
        return
    
    # Test 2: Start server
    print("\n2. Starting web server...")
    server_process = start_server()
    
    if not server_process:
        print("✗ Server failed to start")
        return
    
    # Test 3: Open browser
    print("\n3. Opening web interface...")
    try:
        webbrowser.open("http://localhost:8000")
        print("✓ Browser opened")
    except Exception as e:
        print(f"✗ Browser error: {e}")
    
    print("\n" + "=" * 40)
    print("DEMO READY!")
    print("=" * 40)
    print("Test Steps:")
    print("1. Check READIFIER -> Profiler shows 5 sample organizations")
    print("2. Try creating a new profile")
    print("3. Click 'Discover Opportunities' on any profile")
    print("4. Watch auto-navigation to DISCOMBOBULATOR")
    print("\nPress Ctrl+C to stop server...")
    
    try:
        # Keep server running
        server_process.wait()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server_process.terminate()

if __name__ == "__main__":
    main()