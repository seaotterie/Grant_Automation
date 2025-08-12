#!/usr/bin/env python3
import subprocess
import sys
import time

def start_server():
    print("Starting web server on port 8001...")
    
    # Start the server
    cmd = [
        sys.executable, 
        "src/web/main.py",
        "--port", "8001"
    ]
    
    try:
        process = subprocess.Popen(cmd)
        print(f"Server started with PID: {process.pid}")
        print("Server should be available at: http://localhost:8001")
        
        # Keep it running
        process.wait()
        
    except KeyboardInterrupt:
        print("\nShutting down server...")
        process.terminate()
        process.wait()
        print("Server stopped.")

if __name__ == "__main__":
    start_server()