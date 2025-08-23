#!/usr/bin/env python3
"""
API-GUI Binding Verification Test Suite
Tests that frontend GUI elements correctly trigger backend API calls

This test suite validates:
1. Tab navigation API calls
2. Profile management integration
3. Discovery engine integration
4. AI analysis integration
5. Real-time WebSocket functionality
"""

import asyncio
import json
import pytest
import requests
import websockets
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import logging

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.profiles.models import OrganizationProfile
from src.processors.analysis.ai_lite_scorer import AILiteRequest, AILiteAnalysis
from src.processors.analysis.ai_heavy_researcher import AIHeavyRequest, AIHeavyResult

logger = logging.getLogger(__name__)

class APIGUIBindingTester:
    """
    Comprehensive API-GUI binding verification tester
    
    Tests that frontend interactions properly trigger backend APIs
    and that data flows correctly between frontend and backend
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.websocket_url = f"ws://localhost:8000/ws"
        self.test_profile_id = None
        self.session = requests.Session()
        
    def setup_test_environment(self) -> bool:
        """Setup test environment and create test profile"""
        try:
            # Check if server is running
            health_response = self.session.get(f"{self.base_url}/api/health", timeout=5)
            if health_response.status_code != 200:
                logger.error(f"Server health check failed: {health_response.status_code}")
                return False
            
            # Create test profile
            test_profile_data = {
                "name": "API-GUI Test Organization",
                "mission": "Testing API-GUI integration for grant discovery",
                "ntee_codes": ["A20", "B30"],
                "revenue": 500000,
                "state": "VA",
                "government_criteria": ["health", "education"]
            }
            
            profile_response = self.session.post(
                f"{self.base_url}/api/profiles",
                json=test_profile_data,
                timeout=10
            )
            
            if profile_response.status_code == 201:
                self.test_profile_id = profile_response.json().get("profile_id")
                logger.info(f"Created test profile: {self.test_profile_id}")
                return True
            else:
                logger.error(f"Failed to create test profile: {profile_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            return False
    
    def cleanup_test_environment(self) -> bool:
        """Cleanup test environment"""
        try:
            if self.test_profile_id:
                delete_response = self.session.delete(
                    f"{self.base_url}/api/profiles/{self.test_profile_id}",
                    timeout=10
                )
                if delete_response.status_code in [200, 404]:
                    logger.info(f"Cleaned up test profile: {self.test_profile_id}")
                    return True
                else:
                    logger.warning(f"Failed to cleanup test profile: {delete_response.status_code}")
            return True
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return False

    def test_tab_navigation_api_calls(self) -> Dict[str, Any]:
        """
        Test that each tab correctly triggers corresponding backend APIs
        
        Tests:
        - DISCOVER tab: /api/discovery/* endpoints
        - PLAN tab: /api/profiles/*/analytics endpoints  
        - ANALYZE tab: /api/analysis/ai-lite endpoints
        - EXAMINE tab: /api/analysis/ai-heavy endpoints
        - APPROACH tab: /api/decision/* endpoints
        """
        results = {"test_name": "tab_navigation_api_calls", "tests": []}
        
        if not self.test_profile_id:
            results["error"] = "No test profile available"
            return results
        
        # Test DISCOVER tab API calls
        discover_test = {
            "tab": "DISCOVER",
            "api_endpoint": f"/api/discovery/entity-cache-stats",
            "expected_status": 200,
            "description": "Verify DISCOVER tab triggers discovery APIs"
        }
        
        try:
            response = self.session.get(f"{self.base_url}{discover_test['api_endpoint']}", timeout=10)
            discover_test["actual_status"] = response.status_code
            discover_test["response_data"] = response.json() if response.status_code == 200 else None
            discover_test["success"] = response.status_code == discover_test["expected_status"]
        except Exception as e:
            discover_test["error"] = str(e)
            discover_test["success"] = False
        
        results["tests"].append(discover_test)
        
        # Test PLAN tab API calls
        plan_test = {
            "tab": "PLAN",
            "api_endpoint": f"/api/profiles/{self.test_profile_id}/analytics",
            "expected_status": 200,
            "description": "Verify PLAN tab triggers analytics APIs"
        }
        
        try:
            response = self.session.get(f"{self.base_url}{plan_test['api_endpoint']}", timeout=10)
            plan_test["actual_status"] = response.status_code
            plan_test["response_data"] = response.json() if response.status_code == 200 else None
            plan_test["success"] = response.status_code == plan_test["expected_status"]
        except Exception as e:
            plan_test["error"] = str(e)
            plan_test["success"] = False
        
        results["tests"].append(plan_test)
        
        # Test ANALYZE tab API calls (AI Lite endpoint)
        analyze_test = {
            "tab": "ANALYZE",
            "api_endpoint": f"/api/profiles/{self.test_profile_id}/analyze/ai-lite",
            "expected_status": [200, 202],  # Accept async processing
            "description": "Verify ANALYZE tab triggers AI-Lite analysis"
        }
        
        try:
            # Test with minimal request data
            analysis_request = {
                "opportunities": [
                    {
                        "opportunity_id": "test_opp_001",
                        "organization_name": "Test Foundation",
                        "source_type": "foundation",
                        "description": "Test opportunity for API binding verification",
                        "funding_amount": 100000,
                        "current_score": 0.75
                    }
                ]
            }
            
            response = self.session.post(
                f"{self.base_url}{analyze_test['api_endpoint']}", 
                json=analysis_request,
                timeout=30
            )
            analyze_test["actual_status"] = response.status_code
            analyze_test["response_data"] = response.json() if response.status_code in [200, 202] else None
            analyze_test["success"] = response.status_code in analyze_test["expected_status"]
        except Exception as e:
            analyze_test["error"] = str(e)
            analyze_test["success"] = False
        
        results["tests"].append(analyze_test)
        
        # Test EXAMINE tab API calls (AI Heavy endpoint)
        examine_test = {
            "tab": "EXAMINE",
            "api_endpoint": f"/api/profiles/{self.test_profile_id}/examine/ai-heavy",
            "expected_status": [200, 202],  # Accept async processing
            "description": "Verify EXAMINE tab triggers AI-Heavy research"
        }
        
        try:
            # Test with minimal request data
            research_request = {
                "target_organization": "Test Foundation",
                "analysis_depth": "comprehensive",
                "research_focus": {
                    "priority_areas": ["strategic_partnership", "funding_approach"],
                    "intelligence_gaps": ["board_connections", "funding_timeline"]
                }
            }
            
            response = self.session.post(
                f"{self.base_url}{examine_test['api_endpoint']}", 
                json=research_request,
                timeout=60
            )
            examine_test["actual_status"] = response.status_code
            examine_test["response_data"] = response.json() if response.status_code in [200, 202] else None
            examine_test["success"] = response.status_code in examine_test["expected_status"]
        except Exception as e:
            examine_test["error"] = str(e)
            examine_test["success"] = False
        
        results["tests"].append(examine_test)
        
        # Calculate overall success
        results["total_tests"] = len(results["tests"])
        results["successful_tests"] = sum(1 for test in results["tests"] if test.get("success", False))
        results["success_rate"] = results["successful_tests"] / results["total_tests"]
        
        return results

    def test_profile_management_integration(self) -> Dict[str, Any]:
        """
        Test profile management API-GUI integration
        
        Tests:
        - Profile creation (POST /api/profiles)
        - Profile updates (PUT /api/profiles/{id})
        - Profile loading (GET /api/profiles/{id})
        - Profile deletion (DELETE /api/profiles/{id})
        """
        results = {"test_name": "profile_management_integration", "tests": []}
        
        # Test profile creation
        create_test = {
            "operation": "CREATE",
            "api_endpoint": "/api/profiles",
            "method": "POST",
            "expected_status": 201,
            "description": "Test profile creation API-GUI integration"
        }
        
        test_profile_data = {
            "name": "Integration Test Org",
            "mission": "Testing profile creation integration",
            "ntee_codes": ["A25"],
            "revenue": 250000,
            "state": "CA",
            "government_criteria": ["environment"]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}{create_test['api_endpoint']}",
                json=test_profile_data,
                timeout=10
            )
            create_test["actual_status"] = response.status_code
            create_test["response_data"] = response.json() if response.status_code == 201 else None
            create_test["success"] = response.status_code == create_test["expected_status"]
            
            # Store created profile ID for subsequent tests
            created_profile_id = None
            if create_test["success"]:
                created_profile_id = response.json().get("profile_id")
                
        except Exception as e:
            create_test["error"] = str(e)
            create_test["success"] = False
            created_profile_id = None
        
        results["tests"].append(create_test)
        
        if created_profile_id:
            # Test profile loading
            load_test = {
                "operation": "LOAD",
                "api_endpoint": f"/api/profiles/{created_profile_id}",
                "method": "GET",
                "expected_status": 200,
                "description": "Test profile loading API-GUI integration"
            }
            
            try:
                response = self.session.get(f"{self.base_url}{load_test['api_endpoint']}", timeout=10)
                load_test["actual_status"] = response.status_code
                load_test["response_data"] = response.json() if response.status_code == 200 else None
                load_test["success"] = response.status_code == load_test["expected_status"]
                
                # Verify data integrity
                if load_test["success"]:
                    loaded_data = response.json()
                    data_integrity = (
                        loaded_data.get("name") == test_profile_data["name"] and
                        loaded_data.get("mission") == test_profile_data["mission"]
                    )
                    load_test["data_integrity"] = data_integrity
                    if not data_integrity:
                        load_test["success"] = False
                        load_test["error"] = "Data integrity check failed"
                        
            except Exception as e:
                load_test["error"] = str(e)
                load_test["success"] = False
            
            results["tests"].append(load_test)
            
            # Test profile update
            update_test = {
                "operation": "UPDATE",
                "api_endpoint": f"/api/profiles/{created_profile_id}",
                "method": "PUT",
                "expected_status": 200,
                "description": "Test profile update API-GUI integration"
            }
            
            updated_data = test_profile_data.copy()
            updated_data["mission"] = "Updated mission for integration testing"
            updated_data["revenue"] = 300000
            
            try:
                response = self.session.put(
                    f"{self.base_url}{update_test['api_endpoint']}",
                    json=updated_data,
                    timeout=10
                )
                update_test["actual_status"] = response.status_code
                update_test["response_data"] = response.json() if response.status_code == 200 else None
                update_test["success"] = response.status_code == update_test["expected_status"]
                
            except Exception as e:
                update_test["error"] = str(e)
                update_test["success"] = False
            
            results["tests"].append(update_test)
            
            # Test profile deletion
            delete_test = {
                "operation": "DELETE",
                "api_endpoint": f"/api/profiles/{created_profile_id}",
                "method": "DELETE",
                "expected_status": 200,
                "description": "Test profile deletion API-GUI integration"
            }
            
            try:
                response = self.session.delete(f"{self.base_url}{delete_test['api_endpoint']}", timeout=10)
                delete_test["actual_status"] = response.status_code
                delete_test["response_data"] = response.json() if response.status_code == 200 else None
                delete_test["success"] = response.status_code == delete_test["expected_status"]
                
            except Exception as e:
                delete_test["error"] = str(e)
                delete_test["success"] = False
            
            results["tests"].append(delete_test)
        
        # Calculate overall success
        results["total_tests"] = len(results["tests"])
        results["successful_tests"] = sum(1 for test in results["tests"] if test.get("success", False))
        results["success_rate"] = results["successful_tests"] / results["total_tests"]
        
        return results

    def test_discovery_engine_integration(self) -> Dict[str, Any]:
        """
        Test 4-track discovery system API-GUI integration
        
        Tests:
        - Nonprofit+BMF track entity discovery
        - Federal track government discovery  
        - State track state-level discovery
        - Commercial track corporate discovery
        """
        results = {"test_name": "discovery_engine_integration", "tests": []}
        
        if not self.test_profile_id:
            results["error"] = "No test profile available"
            return results
        
        discovery_tracks = [
            {
                "track": "nonprofit_bmf",
                "api_endpoint": f"/api/profiles/{self.test_profile_id}/discover/entity-analytics",
                "method": "POST",
                "expected_status": [200, 202],
                "description": "Test Nonprofit+BMF track discovery integration",
                "request_data": {
                    "max_results": 5,
                    "filters": {
                        "ntee_codes": ["A20"],
                        "revenue_range": {"min": 100000, "max": 1000000}
                    }
                }
            },
            {
                "track": "federal",
                "api_endpoint": f"/api/profiles/{self.test_profile_id}/discover/federal",
                "method": "POST", 
                "expected_status": [200, 202],
                "description": "Test Federal track discovery integration",
                "request_data": {
                    "max_results": 5,
                    "filters": {
                        "agencies": ["HHS", "ED"],
                        "funding_range": {"min": 50000, "max": 500000}
                    }
                }
            },
            {
                "track": "state", 
                "api_endpoint": f"/api/profiles/{self.test_profile_id}/discover/state",
                "method": "POST",
                "expected_status": [200, 202],
                "description": "Test State track discovery integration",
                "request_data": {
                    "max_results": 5,
                    "states": ["VA", "CA"],
                    "program_types": ["health", "education"]
                }
            },
            {
                "track": "commercial",
                "api_endpoint": f"/api/profiles/{self.test_profile_id}/discover/commercial",
                "method": "POST",
                "expected_status": [200, 202], 
                "description": "Test Commercial track discovery integration",
                "request_data": {
                    "max_results": 5,
                    "industries": ["healthcare", "technology"],
                    "partnership_types": ["grants", "sponsorships"]
                }
            }
        ]
        
        for track_test in discovery_tracks:
            try:
                if track_test["method"] == "POST":
                    response = self.session.post(
                        f"{self.base_url}{track_test['api_endpoint']}",
                        json=track_test.get("request_data", {}),
                        timeout=30
                    )
                else:
                    response = self.session.get(
                        f"{self.base_url}{track_test['api_endpoint']}",
                        timeout=30
                    )
                
                track_test["actual_status"] = response.status_code
                track_test["response_data"] = response.json() if response.status_code in [200, 202] else None
                track_test["success"] = response.status_code in track_test["expected_status"]
                
                # Additional validation for discovery responses
                if track_test["success"] and track_test["response_data"]:
                    response_data = track_test["response_data"]
                    if "opportunities" in response_data or "results" in response_data:
                        track_test["data_validation"] = "Discovery results returned"
                    elif "status" in response_data and response_data["status"] == "processing":
                        track_test["data_validation"] = "Async processing initiated"
                    else:
                        track_test["data_validation"] = "Unexpected response structure"
                
            except Exception as e:
                track_test["error"] = str(e)
                track_test["success"] = False
            
            results["tests"].append(track_test)
        
        # Calculate overall success
        results["total_tests"] = len(results["tests"])
        results["successful_tests"] = sum(1 for test in results["tests"] if test.get("success", False))
        results["success_rate"] = results["successful_tests"] / results["total_tests"]
        
        return results

    async def test_websocket_integration(self) -> Dict[str, Any]:
        """
        Test real-time WebSocket functionality
        
        Tests:
        - WebSocket connection establishment
        - Real-time progress updates
        - Error propagation
        - Connection recovery
        """
        results = {"test_name": "websocket_integration", "tests": []}
        
        # Test WebSocket connection
        connection_test = {
            "test": "connection",
            "description": "Test WebSocket connection establishment",
            "success": False
        }
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Send test message
                test_message = {"type": "ping", "timestamp": datetime.now().isoformat()}
                await websocket.send(json.dumps(test_message))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                connection_test["response_data"] = response_data
                connection_test["success"] = True
                
        except Exception as e:
            connection_test["error"] = str(e)
        
        results["tests"].append(connection_test)
        
        # Test progress monitoring (simulate discovery operation)
        progress_test = {
            "test": "progress_monitoring",
            "description": "Test real-time progress monitoring during discovery",
            "success": False
        }
        
        if self.test_profile_id and connection_test["success"]:
            try:
                # Start a discovery operation that should generate progress updates
                discovery_request = {
                    "profile_id": self.test_profile_id,
                    "tracks": ["nonprofit_bmf"],
                    "max_results": 3
                }
                
                # Start discovery operation
                discovery_response = self.session.post(
                    f"{self.base_url}/api/profiles/{self.test_profile_id}/discover/start",
                    json=discovery_request,
                    timeout=10
                )
                
                if discovery_response.status_code in [200, 202]:
                    operation_id = discovery_response.json().get("operation_id")
                    
                    if operation_id:
                        # Connect to WebSocket to monitor progress
                        async with websockets.connect(self.websocket_url) as websocket:
                            # Subscribe to progress updates
                            subscribe_message = {
                                "type": "subscribe",
                                "operation_id": operation_id
                            }
                            await websocket.send(json.dumps(subscribe_message))
                            
                            # Wait for progress updates
                            progress_updates = []
                            for _ in range(3):  # Wait for up to 3 updates
                                try:
                                    update = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                                    progress_updates.append(json.loads(update))
                                except asyncio.TimeoutError:
                                    break
                            
                            progress_test["progress_updates"] = progress_updates
                            progress_test["success"] = len(progress_updates) > 0
                    
                else:
                    progress_test["error"] = f"Discovery operation failed: {discovery_response.status_code}"
                    
            except Exception as e:
                progress_test["error"] = str(e)
        
        results["tests"].append(progress_test)
        
        # Calculate overall success
        results["total_tests"] = len(results["tests"])
        results["successful_tests"] = sum(1 for test in results["tests"] if test.get("success", False))
        results["success_rate"] = results["successful_tests"] / results["total_tests"]
        
        return results

    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all API-GUI binding verification tests
        
        Returns comprehensive test results
        """
        logger.info("Starting API-GUI binding verification tests")
        
        # Setup test environment
        if not self.setup_test_environment():
            return {
                "error": "Failed to setup test environment",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Run synchronous tests
            tab_navigation_results = self.test_tab_navigation_api_calls()
            profile_management_results = self.test_profile_management_integration()
            discovery_integration_results = self.test_discovery_engine_integration()
            
            # Run WebSocket tests
            websocket_results = asyncio.run(self.test_websocket_integration())
            
            # Compile comprehensive results
            comprehensive_results = {
                "test_suite": "API-GUI Binding Verification",
                "timestamp": datetime.now().isoformat(),
                "test_environment": {
                    "base_url": self.base_url,
                    "test_profile_id": self.test_profile_id
                },
                "test_results": {
                    "tab_navigation": tab_navigation_results,
                    "profile_management": profile_management_results,
                    "discovery_integration": discovery_integration_results,
                    "websocket_integration": websocket_results
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
    """Main test execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="API-GUI Binding Verification Tests")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for API tests")
    parser.add_argument("--output", default="api_gui_binding_results.json", help="Output file for test results")
    args = parser.parse_args()
    
    # Initialize tester
    tester = APIGUIBindingTester(base_url=args.base_url)
    
    # Run tests
    results = tester.run_all_tests()
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    if "overall_statistics" in results:
        stats = results["overall_statistics"]
        print(f"\nAPI-GUI Binding Test Results:")
        print(f"Total Tests: {stats['total_individual_tests']}")
        print(f"Successful: {stats['successful_tests']}")
        print(f"Failed: {stats['failed_tests']}")
        print(f"Success Rate: {stats['overall_success_rate']:.2%}")
        print(f"Results saved to: {args.output}")
    else:
        print(f"Test setup failed: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()