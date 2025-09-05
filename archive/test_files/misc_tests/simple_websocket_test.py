#!/usr/bin/env python3
"""
Simple WebSocket Connection Test
Tests basic WebSocket connectivity and message handling
"""

import asyncio
import json
import websockets
import logging
from datetime import datetime

async def test_websocket_connection():
    """Test basic WebSocket connection"""
    websocket_url = "ws://localhost:8000/ws/discovery"
    
    try:
        print(f"Connecting to WebSocket: {websocket_url}")
        async with websockets.connect(websocket_url) as websocket:
            print("SUCCESS: WebSocket connection established successfully")
            
            # Test basic message sending
            test_message = {
                "type": "test",
                "message": "Hello from integration test",
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(test_message))
            print(f"SUCCESS: Sent test message: {test_message}")
            
            # Try to receive response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"SUCCESS: Received response: {response}")
                
                try:
                    response_data = json.loads(response)
                    print(f"SUCCESS: Response parsed as JSON: {response_data}")
                except json.JSONDecodeError:
                    print(f"WARNING: Response is not JSON: {response}")
                
            except asyncio.TimeoutError:
                print("WARNING: No response received within 5 seconds (this may be normal)")
            
            # Test ping/pong
            try:
                pong = await websocket.ping()
                await pong
                print("SUCCESS: Ping/pong successful")
            except Exception as e:
                print(f"WARNING: Ping failed: {e}")
            
            print("SUCCESS: WebSocket connection test completed successfully")
            return True
            
    except Exception as e:
        print(f"ERROR: WebSocket connection failed: {e}")
        return False

async def main():
    print("Starting WebSocket Integration Test")
    print("="*50)
    
    success = await test_websocket_connection()
    
    print("="*50)
    if success:
        print("WebSocket integration test PASSED")
    else:
        print("WebSocket integration test FAILED")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)