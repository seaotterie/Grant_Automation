#!/usr/bin/env python3
"""
Test Dashboard Connectivity
Check if Streamlit dashboards can be accessed and diagnose connectivity issues.
"""

import requests
import subprocess
import time
import sys
import socket
from pathlib import Path

def test_port_availability(port):
    """Test if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0  # 0 means connection successful (port is in use)
    except Exception as e:
        print(f"Error testing port {port}: {e}")
        return False

def test_http_connectivity(port):
    """Test HTTP connectivity to a Streamlit port."""
    try:
        url = f"http://127.0.0.1:{port}"
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"HTTP test failed for port {port}: {e}")
        return False

def main():
    print("CATALYNX DASHBOARD CONNECTIVITY TEST")
    print("=" * 50)
    
    # Test common Streamlit ports
    test_ports = [8501, 8502, 8503]
    
    print("1. Testing port availability...")
    for port in test_ports:
        is_in_use = test_port_availability(port)
        status = "IN USE" if is_in_use else "AVAILABLE"
        print(f"   Port {port}: {status}")
    
    # Find an available port
    available_port = None
    for port in test_ports:
        if not test_port_availability(port):
            available_port = port
            break
    
    if not available_port:
        print("All test ports are in use. Using port 8504...")
        available_port = 8504
    
    print(f"\n2. Testing Streamlit startup on port {available_port}...")
    
    # Start the analytics dashboard
    dashboard_path = Path("src/dashboard/analytics_dashboard.py")
    if not dashboard_path.exists():
        print(f"ERROR: Dashboard file not found: {dashboard_path}")
        return
    
    streamlit_cmd = [
        "grant-research-env/Scripts/streamlit.exe",
        "run",
        str(dashboard_path),
        "--server.address", "127.0.0.1",
        "--server.port", str(available_port),
        "--server.headless", "true",
        "--server.runOnSave", "false"
    ]
    
    print(f"Starting: {' '.join(streamlit_cmd)}")
    
    try:
        # Start Streamlit process
        process = subprocess.Popen(
            streamlit_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for startup
        print("Waiting for Streamlit to start...")
        time.sleep(8)
        
        # Check if process is running
        if process.poll() is None:
            print("✅ Streamlit process is running")
            
            # Test HTTP connectivity
            print(f"3. Testing HTTP connectivity to http://127.0.0.1:{available_port}...")
            
            max_attempts = 5
            for attempt in range(max_attempts):
                if test_http_connectivity(available_port):
                    print(f"✅ HTTP connectivity successful on attempt {attempt + 1}")
                    print(f"\n🎉 SUCCESS! Dashboard is accessible at:")
                    print(f"   http://127.0.0.1:{available_port}")
                    print(f"   http://localhost:{available_port}")
                    
                    # Keep it running for a bit so user can test
                    print(f"\nDashboard will run for 30 seconds for testing...")
                    time.sleep(30)
                    break
                else:
                    print(f"⏳ HTTP test {attempt + 1}/{max_attempts} failed, retrying...")
                    time.sleep(3)
            else:
                print("❌ HTTP connectivity failed after all attempts")
                print("Dashboard started but is not accessible via HTTP")
        else:
            print("❌ Streamlit process failed to start")
            stdout, stderr = process.communicate()
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
        
        # Clean up
        if process.poll() is None:
            print("Stopping Streamlit process...")
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    
    print("\n" + "=" * 50)
    print("CONNECTIVITY TEST COMPLETE")

if __name__ == "__main__":
    main()