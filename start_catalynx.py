#!/usr/bin/env python3
"""
Simple Catalynx Web Interface Launcher
Provides clear feedback about server status
"""

import os
import sys
import time
import webbrowser
from pathlib import Path

def main():
    print("=" * 60)
    print("CATALYNX - Grant Research Automation Web Interface")
    print("=" * 60)
    print()
    
    # Check if we're in the right directory
    if not Path("src/web/main.py").exists():
        print("ERROR: Please run this from the Grant_Automation directory")
        print("Current directory:", os.getcwd())
        input("Press Enter to exit...")
        return
    
    print("Starting Catalynx Web Server...")
    print("- Server will run on: http://127.0.0.1:8000")
    print("- Press Ctrl+C to stop the server")
    print("- Wait for 'Server Ready' message before opening browser")
    print()
    
    try:
        # Change to web directory
        os.chdir("src/web")
        
        # Import and start the server
        import uvicorn
        
        print("Server starting...")
        print("=" * 40)
        
        # Start server with clear output
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            log_level="info",
            access_log=True,
            reload=False
        )
        
    except KeyboardInterrupt:
        print()
        print("Server stopped by user")
    except Exception as e:
        print(f"ERROR starting server: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()