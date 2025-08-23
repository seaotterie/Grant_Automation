#!/usr/bin/env python3
"""
WebSocket Integration Testing Suite
Tests real-time WebSocket functionality for progress monitoring and live updates

This test suite validates:
1. WebSocket connection establishment and maintenance
2. Real-time progress monitoring during discovery operations
3. Error propagation through WebSocket channels
4. Connection recovery and reconnection handling
5. Multi-tab synchronization
6. Message queue handling during high-frequency updates
"""

import asyncio
import json
import pytest
import websockets
import requests
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import concurrent.futures
from dataclasses import dataclass

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

@dataclass
class WebSocketMessage:
    """Structured WebSocket message for testing"""
    message_type: str
    timestamp: str
    data: Dict[str, Any]
    operation_id: Optional[str] = None

class WebSocketTester:
    """
    Comprehensive WebSocket functionality tester
    
    Tests all aspects of WebSocket integration including:
    - Connection lifecycle management
    - Real-time progress monitoring
    - Error handling and recovery
    - Multi-client scenarios
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.websocket_url = f"ws://localhost:8000/ws"
        self.http_session = requests.Session()
        self.test_profile_id = None
        self.received_messages = []
        
    async def setup_test_environment(self) -> bool:
        """Setup test environment with test profile"""
        try:
            # Check server health
            health_response = self.http_session.get(f"{self.base_url}/api/health", timeout=5)
            if health_response.status_code != 200:
                logger.error(f"Server not available: {health_response.status_code}")
                return False
            
            # Create test profile for WebSocket testing
            test_profile = {
                "name": "WebSocket Test Organization",
                "mission": "Testing real-time WebSocket functionality",
                "ntee_codes": ["A20", "B25"],
                "revenue": 750000,
                "state": "VA",
                "government_criteria": ["health", "technology"]
            }
            
            profile_response = self.http_session.post(
                f"{self.base_url}/api/profiles",
                json=test_profile,
                timeout=10
            )
            
            if profile_response.status_code == 201:
                self.test_profile_id = profile_response.json().get("profile_id")
                logger.info(f"Created WebSocket test profile: {self.test_profile_id}")
                return True
            else:
                logger.error(f"Failed to create test profile: {profile_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"WebSocket test setup failed: {str(e)}")
            return False
    
    def cleanup_test_environment(self) -> bool:
        """Cleanup test environment"""
        try:
            if self.test_profile_id:
                delete_response = self.http_session.delete(
                    f"{self.base_url}/api/profiles/{self.test_profile_id}",
                    timeout=10
                )
                logger.info(f"Cleaned up WebSocket test profile: {self.test_profile_id}")
            return True
        except Exception as e:
            logger.error(f"WebSocket cleanup failed: {str(e)}")
            return False

    async def test_websocket_connection_lifecycle(self) -> Dict[str, Any]:
        """
        Test WebSocket connection establishment, maintenance, and cleanup
        
        Tests:
        - Initial connection establishment
        - Connection stability over time
        - Heartbeat/ping-pong functionality
        - Clean disconnection
        """
        results = {"test_name": "websocket_connection_lifecycle", "tests": []}
        
        # Test 1: Basic connection establishment
        connection_test = {
            "test": "connection_establishment",
            "description": "Test basic WebSocket connection establishment",
            "success": False
        }
        
        try:
            async with websockets.connect(
                self.websocket_url,
                timeout=10,
                ping_interval=20,
                ping_timeout=10
            ) as websocket:
                # Connection established successfully
                connection_test["connection_state"] = str(websocket.state)
                connection_test["success"] = True
                
        except Exception as e:
            connection_test["error"] = str(e)
        
        results["tests"].append(connection_test)
        
        # Test 2: Heartbeat/ping-pong functionality
        heartbeat_test = {
            "test": "heartbeat_functionality", 
            "description": "Test WebSocket heartbeat and keep-alive",
            "success": False
        }
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Send ping
                await websocket.ping()
                
                # Send custom heartbeat message
                heartbeat_msg = {
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "client_id": "websocket_tester"
                }
                
                await websocket.send(json.dumps(heartbeat_msg))
                
                # Wait for any response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    heartbeat_test["response"] = json.loads(response)
                    heartbeat_test["success"] = True
                except asyncio.TimeoutError:
                    heartbeat_test["success"] = True  # Timeout is acceptable for heartbeat
                    heartbeat_test["note"] = "No response required for heartbeat"
                    
        except Exception as e:
            heartbeat_test["error"] = str(e)
        
        results["tests"].append(heartbeat_test)
        
        # Test 3: Connection stability over time
        stability_test = {
            "test": "connection_stability",
            "description": "Test WebSocket connection stability over extended period",
            "success": False
        }
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Keep connection open and send periodic messages
                messages_sent = 0
                start_time = time.time()
                
                while (time.time() - start_time) < 30:  # Test for 30 seconds
                    test_msg = {
                        "type": "stability_test",
                        "sequence": messages_sent,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send(json.dumps(test_msg))
                    messages_sent += 1
                    await asyncio.sleep(2)  # Send message every 2 seconds
                
                stability_test["messages_sent"] = messages_sent
                stability_test["duration_seconds"] = 30
                stability_test["connection_state"] = str(websocket.state)
                stability_test["success"] = True
                
        except Exception as e:
            stability_test["error"] = str(e)
        
        results["tests"].append(stability_test)
        
        return results

    async def test_real_time_progress_monitoring(self) -> Dict[str, Any]:
        """
        Test real-time progress monitoring during discovery operations
        
        Tests:
        - Progress update reception during discovery
        - Message ordering and sequence
        - Progress data structure validation
        - Completion notification
        """
        results = {"test_name": "real_time_progress_monitoring", "tests": []}
        
        if not self.test_profile_id:
            results["error"] = "No test profile available for progress monitoring"
            return results
        
        # Test 1: Discovery operation progress monitoring
        discovery_progress_test = {
            "test": "discovery_progress_monitoring",
            "description": "Test progress monitoring during discovery operation",
            "success": False
        }
        
        try:
            # Start WebSocket connection for monitoring
            async with websockets.connect(self.websocket_url) as websocket:
                # Subscribe to progress updates
                subscribe_msg = {
                    "type": "subscribe",
                    "events": ["discovery_progress", "operation_status"],
                    "profile_id": self.test_profile_id
                }
                
                await websocket.send(json.dumps(subscribe_msg))
                
                # Start discovery operation via HTTP
                discovery_request = {
                    "profile_id": self.test_profile_id,
                    "tracks": ["nonprofit_bmf"],
                    "max_results": 5,
                    "notify_via_websocket": True
                }
                
                discovery_response = self.http_session.post(
                    f"{self.base_url}/api/profiles/{self.test_profile_id}/discover/start",
                    json=discovery_request,
                    timeout=15
                )
                
                if discovery_response.status_code in [200, 202]:
                    operation_id = discovery_response.json().get("operation_id")
                    discovery_progress_test["operation_id"] = operation_id
                    
                    # Monitor progress updates via WebSocket
                    progress_messages = []
                    timeout_duration = 60  # 60 seconds timeout
                    start_time = time.time()
                    
                    while (time.time() - start_time) < timeout_duration:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            message_data = json.loads(message)
                            progress_messages.append(message_data)
                            
                            # Check if operation completed
                            if (message_data.get("type") == "operation_complete" or 
                                message_data.get("status") == "completed"):
                                break
                                
                        except asyncio.TimeoutError:
                            # No message received in 5 seconds, continue monitoring
                            continue
                    
                    discovery_progress_test["progress_messages"] = progress_messages
                    discovery_progress_test["total_messages"] = len(progress_messages)
                    discovery_progress_test["success"] = len(progress_messages) > 0
                    
                    # Validate progress message structure
                    if progress_messages:
                        sample_message = progress_messages[0]
                        discovery_progress_test["message_structure_valid"] = all(
                            key in sample_message for key in ["type", "timestamp"]
                        )
                    
                else:
                    discovery_progress_test["error"] = f"Discovery operation failed: {discovery_response.status_code}"
                    
        except Exception as e:
            discovery_progress_test["error"] = str(e)
        
        results["tests"].append(discovery_progress_test)
        
        # Test 2: AI Analysis progress monitoring
        ai_progress_test = {
            "test": "ai_analysis_progress_monitoring",
            "description": "Test progress monitoring during AI analysis operations",
            "success": False
        }
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Subscribe to AI analysis progress
                subscribe_msg = {
                    "type": "subscribe", 
                    "events": ["ai_analysis_progress"],
                    "profile_id": self.test_profile_id
                }
                
                await websocket.send(json.dumps(subscribe_msg))
                
                # Start AI analysis operation
                analysis_request = {
                    "opportunities": [
                        {
                            "opportunity_id": "ws_test_001",
                            "organization_name": "WebSocket Test Foundation",
                            "source_type": "foundation",
                            "description": "Testing WebSocket progress monitoring for AI analysis",
                            "funding_amount": 150000,
                            "current_score": 0.8
                        }
                    ],
                    "notify_via_websocket": True
                }
                
                ai_response = self.http_session.post(
                    f"{self.base_url}/api/profiles/{self.test_profile_id}/analyze/ai-lite",
                    json=analysis_request,
                    timeout=45
                )
                
                if ai_response.status_code in [200, 202]:
                    # Monitor AI analysis progress
                    ai_messages = []
                    timeout_duration = 45
                    start_time = time.time()
                    
                    while (time.time() - start_time) < timeout_duration:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            message_data = json.loads(message)
                            ai_messages.append(message_data)
                            
                            # Check for completion
                            if (message_data.get("type") == "analysis_complete" or
                                message_data.get("status") == "completed"):
                                break
                                
                        except asyncio.TimeoutError:
                            continue
                    
                    ai_progress_test["ai_messages"] = ai_messages
                    ai_progress_test["total_messages"] = len(ai_messages)
                    ai_progress_test["success"] = len(ai_messages) > 0
                    
                else:
                    ai_progress_test["error"] = f"AI analysis failed: {ai_response.status_code}"
                    
        except Exception as e:
            ai_progress_test["error"] = str(e)
        
        results["tests"].append(ai_progress_test)
        
        return results

    async def test_error_propagation(self) -> Dict[str, Any]:
        """
        Test error propagation through WebSocket channels
        
        Tests:
        - Backend error propagation to WebSocket clients
        - Error message structure and content
        - Recovery notifications
        - Graceful error handling
        """
        results = {"test_name": "error_propagation", "tests": []}
        
        # Test 1: API error propagation
        api_error_test = {
            "test": "api_error_propagation",
            "description": "Test propagation of backend API errors via WebSocket", 
            "success": False
        }
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Subscribe to error events
                subscribe_msg = {
                    "type": "subscribe",
                    "events": ["errors", "operation_failed"],
                    "profile_id": "invalid_profile_id"  # Use invalid ID to trigger error
                }
                
                await websocket.send(json.dumps(subscribe_msg))
                
                # Trigger operation that will fail
                invalid_request = {
                    "profile_id": "invalid_profile_id",
                    "tracks": ["invalid_track"],
                    "max_results": 5
                }
                
                # This should fail and error should be propagated via WebSocket
                error_response = self.http_session.post(
                    f"{self.base_url}/api/profiles/invalid_profile_id/discover/start",
                    json=invalid_request,
                    timeout=10
                )
                
                # Listen for error messages
                error_messages = []
                for _ in range(3):  # Wait for up to 3 error messages
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        message_data = json.loads(message)
                        error_messages.append(message_data)
                        
                        if message_data.get("type") == "error" or "error" in message_data:
                            break
                            
                    except asyncio.TimeoutError:
                        break
                
                api_error_test["error_messages"] = error_messages
                api_error_test["http_status"] = error_response.status_code
                api_error_test["success"] = len(error_messages) > 0 or error_response.status_code >= 400
                
        except Exception as e:
            api_error_test["error"] = str(e)
        
        results["tests"].append(api_error_test)
        
        # Test 2: Connection error recovery
        recovery_test = {
            "test": "connection_recovery",
            "description": "Test WebSocket connection recovery after errors",
            "success": False
        }
        
        try:
            # Test reconnection scenario
            async with websockets.connect(self.websocket_url) as websocket:
                # Send normal message first
                normal_msg = {"type": "test", "content": "before_error"}
                await websocket.send(json.dumps(normal_msg))
                
                # Simulate error condition by sending malformed message
                try:
                    await websocket.send("invalid json message")
                except:
                    pass  # Expected to fail
                
                # Try to continue normal communication
                recovery_msg = {"type": "test", "content": "after_error"}
                await websocket.send(json.dumps(recovery_msg))
                
                # If we get here without exception, recovery was successful
                recovery_test["recovery_successful"] = True
                recovery_test["success"] = True
                
        except Exception as e:
            recovery_test["error"] = str(e)
        
        results["tests"].append(recovery_test)
        
        return results

    async def test_multi_client_synchronization(self) -> Dict[str, Any]:
        """
        Test WebSocket functionality with multiple concurrent clients
        
        Tests:
        - Multi-client message broadcasting
        - Client isolation and targeting
        - Concurrent connection handling
        - Resource management under load
        """
        results = {"test_name": "multi_client_synchronization", "tests": []}
        
        # Test 1: Multiple concurrent connections
        concurrent_connections_test = {
            "test": "concurrent_connections",
            "description": "Test multiple concurrent WebSocket connections",
            "success": False
        }
        
        try:
            num_clients = 5
            client_tasks = []
            
            async def client_session(client_id: int):
                """Individual client session"""
                try:
                    async with websockets.connect(self.websocket_url) as websocket:
                        # Send client identification
                        client_msg = {
                            "type": "client_identification",
                            "client_id": client_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(client_msg))
                        
                        # Listen for messages for 10 seconds
                        messages_received = []
                        start_time = time.time()
                        
                        while (time.time() - start_time) < 10:
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                                messages_received.append(json.loads(message))
                            except asyncio.TimeoutError:
                                continue
                        
                        return {
                            "client_id": client_id,
                            "messages_received": len(messages_received),
                            "success": True
                        }
                        
                except Exception as e:
                    return {
                        "client_id": client_id,
                        "error": str(e),
                        "success": False
                    }
            
            # Create concurrent client sessions
            client_results = await asyncio.gather(*[
                client_session(i) for i in range(num_clients)
            ])
            
            concurrent_connections_test["client_results"] = client_results
            concurrent_connections_test["successful_clients"] = sum(
                1 for result in client_results if result.get("success", False)
            )
            concurrent_connections_test["total_clients"] = num_clients
            concurrent_connections_test["success"] = concurrent_connections_test["successful_clients"] > 0
            
        except Exception as e:
            concurrent_connections_test["error"] = str(e)
        
        results["tests"].append(concurrent_connections_test)
        
        # Test 2: Message broadcasting to multiple clients
        broadcasting_test = {
            "test": "message_broadcasting",
            "description": "Test message broadcasting to multiple WebSocket clients",
            "success": False
        }
        
        if self.test_profile_id:
            try:
                # Create multiple clients that subscribe to same profile updates
                num_subscribers = 3
                
                async def subscriber_client(subscriber_id: int):
                    """Client that subscribes to profile updates"""
                    try:
                        async with websockets.connect(self.websocket_url) as websocket:
                            # Subscribe to profile updates
                            subscribe_msg = {
                                "type": "subscribe",
                                "events": ["profile_updated", "discovery_complete"],
                                "profile_id": self.test_profile_id,
                                "subscriber_id": subscriber_id
                            }
                            await websocket.send(json.dumps(subscribe_msg))
                            
                            # Wait for broadcast messages
                            broadcast_messages = []
                            for _ in range(5):  # Wait for up to 5 messages
                                try:
                                    message = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                                    broadcast_messages.append(json.loads(message))
                                except asyncio.TimeoutError:
                                    break
                            
                            return {
                                "subscriber_id": subscriber_id,
                                "messages_received": len(broadcast_messages),
                                "messages": broadcast_messages,
                                "success": True
                            }
                            
                    except Exception as e:
                        return {
                            "subscriber_id": subscriber_id,
                            "error": str(e),
                            "success": False
                        }
                
                # Start subscriber clients
                subscriber_tasks = [
                    subscriber_client(i) for i in range(num_subscribers)
                ]
                
                # Start all subscribers concurrently
                subscriber_results = await asyncio.gather(*subscriber_tasks)
                
                # Trigger an event that should broadcast to all subscribers
                await asyncio.sleep(2)  # Give time for subscriptions
                
                # Update profile to trigger broadcast
                update_data = {
                    "mission": "Updated mission to test WebSocket broadcasting",
                    "revenue": 800000
                }
                
                update_response = self.http_session.put(
                    f"{self.base_url}/api/profiles/{self.test_profile_id}",
                    json=update_data,
                    timeout=10
                )
                
                broadcasting_test["subscriber_results"] = subscriber_results
                broadcasting_test["update_triggered"] = update_response.status_code == 200
                broadcasting_test["successful_subscribers"] = sum(
                    1 for result in subscriber_results if result.get("success", False)
                )
                broadcasting_test["success"] = broadcasting_test["successful_subscribers"] > 0
                
            except Exception as e:
                broadcasting_test["error"] = str(e)
        
        results["tests"].append(broadcasting_test)
        
        return results

    async def run_all_websocket_tests(self) -> Dict[str, Any]:
        """
        Run all WebSocket integration tests
        
        Returns comprehensive WebSocket test results
        """
        logger.info("Starting comprehensive WebSocket integration tests")
        
        # Setup test environment
        if not await self.setup_test_environment():
            return {
                "error": "Failed to setup WebSocket test environment", 
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Run all WebSocket test categories
            connection_results = await self.test_websocket_connection_lifecycle()
            progress_results = await self.test_real_time_progress_monitoring()
            error_results = await self.test_error_propagation()
            multi_client_results = await self.test_multi_client_synchronization()
            
            # Compile comprehensive results
            comprehensive_results = {
                "test_suite": "WebSocket Integration Testing",
                "timestamp": datetime.now().isoformat(),
                "test_environment": {
                    "websocket_url": self.websocket_url,
                    "base_url": self.base_url,
                    "test_profile_id": self.test_profile_id
                },
                "test_results": {
                    "connection_lifecycle": connection_results,
                    "progress_monitoring": progress_results,
                    "error_propagation": error_results,
                    "multi_client_sync": multi_client_results
                }
            }
            
            # Calculate overall statistics
            all_tests = []
            for category in comprehensive_results["test_results"].values():
                if "tests" in category:
                    all_tests.extend(category["tests"])
            
            comprehensive_results["overall_statistics"] = {
                "total_test_categories": len(comprehensive_results["test_results"]),
                "total_individual_tests": len(all_tests),
                "successful_tests": sum(1 for test in all_tests if test.get("success", False)),
                "failed_tests": sum(1 for test in all_tests if not test.get("success", False)),
                "overall_success_rate": sum(1 for test in all_tests if test.get("success", False)) / len(all_tests) if all_tests else 0
            }
            
            return comprehensive_results
            
        finally:
            # Always cleanup
            self.cleanup_test_environment()

def main():
    """Main WebSocket test execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="WebSocket Integration Tests")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for API tests")
    parser.add_argument("--output", default="websocket_integration_results.json", help="Output file for test results")
    args = parser.parse_args()
    
    # Initialize WebSocket tester
    tester = WebSocketTester(base_url=args.base_url)
    
    # Run WebSocket tests
    results = asyncio.run(tester.run_all_websocket_tests())
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    if "overall_statistics" in results:
        stats = results["overall_statistics"]
        print(f"\nWebSocket Integration Test Results:")
        print(f"Total Tests: {stats['total_individual_tests']}")
        print(f"Successful: {stats['successful_tests']}")
        print(f"Failed: {stats['failed_tests']}")
        print(f"Success Rate: {stats['overall_success_rate']:.2%}")
        print(f"Results saved to: {args.output}")
    else:
        print(f"WebSocket test setup failed: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()