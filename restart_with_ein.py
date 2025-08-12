#!/usr/bin/env python3
"""
Restart server with EIN creation functionality
"""
import subprocess
import time
import webbrowser
import sys
from pathlib import Path

print("Restarting Catalynx server with EIN functionality...")
print("=" * 50)

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Import and run server directly with new code
from src.web.main import app
import uvicorn

print("Starting server with updated EIN profile creation...")
print("New features:")
print("+ EIN-only profile creation form")
print("+ Auto-population from ProPublica/IRS data") 
print("+ Enhanced error handling and validation")
print()
print("Server will start on http://127.0.0.1:8000")
print("Navigate to READIFIER -> Profiler")
print("Click 'Create from EIN' to test the new functionality")
print()
print("Press Ctrl+C to stop")
print("=" * 50)

try:
    uvicorn.run(
        app,
        host="127.0.0.1", 
        port=8000,
        log_level="info",
        reload=False
    )
except KeyboardInterrupt:
    print("\nServer stopped")
except Exception as e:
    if "address already in use" in str(e).lower():
        print("\nPort 8000 is in use. The server is already running!")
        print("Navigate to http://localhost:8000 to test EIN functionality")
        print("The new code should be active after a browser refresh")
    else:
        print(f"\nServer error: {e}")