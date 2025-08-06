#!/usr/bin/env python3
"""
Simple Catalynx Server Launcher
Minimal approach with maximum debugging
"""

import os
import sys
import time

def main():
    print("=" * 60)
    print("CATALYNX SIMPLE SERVER LAUNCHER")
    print("=" * 60)
    
    # Check current directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # Check if web directory exists
    web_dir = os.path.join(current_dir, "src", "web")
    if not os.path.exists(web_dir):
        print(f"ERROR: Web directory not found at {web_dir}")
        print("Please run this script from the Grant_Automation directory")
        return False
        
    print(f"Web directory found: {web_dir}")
    
    # Check if main.py exists
    main_py = os.path.join(web_dir, "main.py")
    if not os.path.exists(main_py):
        print(f"ERROR: main.py not found at {main_py}")
        return False
        
    print(f"main.py found: {main_py}")
    
    # Try to import required modules
    try:
        import uvicorn
        print("✓ uvicorn available")
    except ImportError:
        print("✗ uvicorn not available - run: pip install uvicorn")
        return False
        
    try:
        import fastapi
        print("✓ fastapi available")
    except ImportError:
        print("✗ fastapi not available - run: pip install fastapi")
        return False
    
    print("\nStarting server...")
    print("Server will be available at: http://127.0.0.1:8000")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Change to web directory
    os.chdir(web_dir)
    
    # Start the server using command line approach
    import subprocess
    
    try:
        # Use the python executable to run uvicorn
        python_exe = sys.executable
        cmd = [python_exe, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "info"]
        
        print(f"Running command: {' '.join(cmd)}")
        print("Starting...")
        
        # Run the server
        process = subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("Press Enter to exit...")