#!/usr/bin/env python3
"""
Catalynx Server Service Manager
Runs the server as a background service with proper lifecycle management
"""

import sys
import os
import subprocess
import signal
import time
import json
from pathlib import Path

def get_pid_file():
    """Get the PID file path."""
    return Path(__file__).parent / "catalynx_server.pid"

def get_log_file():
    """Get the log file path."""
    return Path(__file__).parent / "logs" / "catalynx_server.log"

def is_server_running():
    """Check if server is already running."""
    pid_file = get_pid_file()
    if not pid_file.exists():
        return False, None
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Check if process is still running
        os.kill(pid, 0)  # This doesn't kill, just checks if process exists
        return True, pid
    except (OSError, ValueError, ProcessLookupError):
        # Process not running, clean up stale PID file
        pid_file.unlink(missing_ok=True)
        return False, None

def start_server():
    """Start the server as a background process."""
    running, pid = is_server_running()
    if running:
        print(f"Server is already running (PID: {pid})")
        print(f"Access at: http://localhost:8000")
        return pid
    
    print("Starting Catalynx server in background...")
    
    # Ensure logs directory exists
    log_file = get_log_file()
    log_file.parent.mkdir(exist_ok=True)
    
    # Start server process
    cmd = [
        sys.executable, "src/web/main.py"
    ]
    
    with open(log_file, 'w') as log:
        process = subprocess.Popen(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # Detach from parent
            cwd=os.getcwd()
        )
    
    # Save PID
    with open(get_pid_file(), 'w') as f:
        f.write(str(process.pid))
    
    # Wait a moment to check if server started successfully
    time.sleep(3)
    
    if process.poll() is None:  # Still running
        print(f"SUCCESS: Server started successfully (PID: {process.pid})")
        print(f"SUCCESS: Access at: http://localhost:8000")
        print(f"SUCCESS: Logs: {log_file}")
        print(f"SUCCESS: Use 'python start_catalynx_service.py stop' to stop")
        return process.pid
    else:
        print("FAILED: Server failed to start. Check logs:")
        with open(log_file, 'r') as f:
            print(f.read())
        return None

def stop_server():
    """Stop the running server."""
    running, pid = is_server_running()
    if not running:
        print("Server is not running")
        return
    
    try:
        print(f"Stopping server (PID: {pid})...")
        os.kill(pid, signal.SIGTERM)
        
        # Wait for graceful shutdown
        for _ in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(0.5)
            except ProcessLookupError:
                break
        else:
            # Force kill if still running
            print("Force killing server...")
            os.kill(pid, signal.SIGKILL)
        
        # Clean up PID file
        get_pid_file().unlink(missing_ok=True)
        print("SUCCESS: Server stopped")
        
    except Exception as e:
        print(f"Error stopping server: {e}")

def status_server():
    """Check server status."""
    running, pid = is_server_running()
    if running:
        print(f"SUCCESS: Server is running (PID: {pid})")
        print(f"SUCCESS: Access at: http://localhost:8000")
        print(f"SUCCESS: Logs: {get_log_file()}")
    else:
        print("STOPPED: Server is not running")
    
    return running

def restart_server():
    """Restart the server."""
    print("Restarting server...")
    stop_server()
    time.sleep(2)
    start_server()

def main():
    """Main service manager."""
    if len(sys.argv) < 2:
        command = "start"
    else:
        command = sys.argv[1].lower()
    
    if command == "start":
        start_server()
    elif command == "stop":
        stop_server()
    elif command == "restart":
        restart_server()
    elif command == "status":
        status_server()
    elif command == "logs":
        log_file = get_log_file()
        if log_file.exists():
            with open(log_file, 'r') as f:
                print(f.read())
        else:
            print("No log file found")
    else:
        print("Usage: python start_catalynx_service.py [start|stop|restart|status|logs]")
        print("Commands:")
        print("  start   - Start the server in background")
        print("  stop    - Stop the running server") 
        print("  restart - Restart the server")
        print("  status  - Check if server is running")
        print("  logs    - Show server logs")

if __name__ == "__main__":
    main()