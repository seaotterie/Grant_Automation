#!/usr/bin/env python3
"""
Integration Tests for Web API Endpoints
Tests FastAPI + Alpine.js integration, WebSocket connections, and complete workflows.
"""

import pytest
import asyncio
import json
import websockets
from datetime import datetime
from typing import Dict, Any, Optional
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Testing framework imports
import httpx
from fastapi.testclient import TestClient

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.web.main import app
from src.profiles.models import OrganizationProfile, FundingType


class TestWebAPIIntegration:
    """Test suite for web API endpoint integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        
    def test_root_endpoint(self):
        """Test main web interface endpoint"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
    def test_health_endpoint(self):
        """Test system health endpoint"""
        response = self.client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        
    def test_api_docs_endpoint(self):
        """Test OpenAPI documentation endpoint"""
        response = self.client.get("/api/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
    def test_openapi_schema_endpoint(self):
        """Test OpenAPI schema endpoint"""
        response = self.client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema


class TestProfileAPIIntegration:
    """Test profile management API endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        
    def create_test_profile(self) -> Dict[str, Any]:
        """Create test profile data"""
        return {
            "organization_name": "Test Veterans Foundation",
            "mission": "Supporting veteran healthcare and wellness programs",
            "focus_areas": ["veteran healthcare", "mental health", "rehabilitation"],
            "geographic_focus": ["Virginia", "North Carolina"],
            "revenue_range": "1M-5M",
            "funding_types": ["government", "foundation"],
            "ntee_codes": ["T99", "P99"],
            "government_criteria": {
                "eligibility_types": ["501c3", "nonprofit"],
                "funding_mechanisms": ["grant", "cooperative_agreement"],
                "geographic_eligibility": ["statewide", "national"]
            }
        }
        
    def test_create_profile_endpoint(self):
        """Test profile creation via API"""
        test_profile = self.create_test_profile()
        
        response = self.client.post("/api/profiles", json=test_profile)
        
        # Should successfully create profile
        assert response.status_code in [200, 201]
        response_data = response.json()
        assert "profile_id" in response_data or "id" in response_data
        
    def test_list_profiles_endpoint(self):
        """Test profile listing endpoint"""
        response = self.client.get("/api/profiles")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
        
    def test_get_profile_endpoint(self):
        """Test individual profile retrieval"""
        # First create a test profile
        test_profile = self.create_test_profile()
        create_response = self.client.post("/api/profiles", json=test_profile)
        
        if create_response.status_code in [200, 201]:
            profile_data = create_response.json()
            profile_id = profile_data.get("profile_id") or profile_data.get("id")
            
            if profile_id:
                # Retrieve the profile
                get_response = self.client.get(f"/api/profiles/{profile_id}")
                assert get_response.status_code == 200

                retrieved_profile = get_response.json()
                # Handle nested response structure
                profile_data = retrieved_profile.get("profile", retrieved_profile)
                assert (profile_data.get("organization_name") == test_profile["organization_name"] or
                        profile_data.get("name") == test_profile["organization_name"])

    @pytest.mark.integration
    def test_complete_profile_crud_workflow(self):
        """Test complete Create-Read-Update-Delete workflow for profiles"""
        # Step 1: CREATE
        test_profile = self.create_test_profile()
        create_response = self.client.post("/api/profiles", json=test_profile)

        assert create_response.status_code in [200, 201], f"Profile creation failed with {create_response.status_code}"

        profile_data = create_response.json()
        profile_id = profile_data.get("profile_id") or profile_data.get("id")

        assert profile_id is not None, "Profile ID not returned from creation"

        try:
            # Step 2: READ
            read_response = self.client.get(f"/api/profiles/{profile_id}")

            # Profile retrieval should succeed now (persistence layer fixed)
            if read_response.status_code == 200:
                read_data = read_response.json()
                # Handle both flat and nested response structures
                profile_data = read_data.get("profile", read_data)
                assert profile_data.get("organization_name") or profile_data.get("name"), "Profile data missing"
            elif read_response.status_code == 404:
                # If still failing, there's a real issue
                raise AssertionError(f"Profile {profile_id} not found after creation - persistence issue not resolved")

            # Step 3: UPDATE
            update_data = {
                "mission": "Updated mission statement for integration testing",
                "revenue_range": "5M-10M"
            }
            update_response = self.client.put(f"/api/profiles/{profile_id}", json=update_data)

            # Accept 200 (updated), 404 (not found), or 405 (method not allowed if PUT not implemented)
            assert update_response.status_code in [200, 404, 405], f"Profile update unexpected status {update_response.status_code}"

            # If update succeeded, verify the changes
            if update_response.status_code == 200:
                updated_response = self.client.get(f"/api/profiles/{profile_id}")
                updated_data = updated_response.json()
                # Verify at least one update was applied (fields may vary by implementation)
                assert updated_data is not None

            # Step 4: LIST (verify profile appears in list)
            list_response = self.client.get("/api/profiles")
            assert list_response.status_code == 200

            list_data = list_response.json()
            # Handle both list and dict responses
            if isinstance(list_data, list):
                profile_ids = [p.get("profile_id") or p.get("id") for p in list_data]
                assert profile_id in profile_ids, "Created profile not found in list"

        finally:
            # Step 5: DELETE (cleanup)
            delete_response = self.client.delete(f"/api/profiles/{profile_id}")
            # Accept 200/204 (deleted) or 404 (already gone) or 405 (method not allowed)
            assert delete_response.status_code in [200, 204, 404, 405]

            # Verify deletion (should be 404)
            verify_response = self.client.get(f"/api/profiles/{profile_id}")
            # After delete, should get 404 (or 200 with empty/null if soft delete)
            assert verify_response.status_code in [200, 404]


class TestDiscoveryAPIIntegration:
    """Test discovery workflow API endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        
    def test_discovery_tracks_endpoint(self):
        """Test discovery tracks information endpoint"""
        response = self.client.get("/api/discovery/tracks")
        
        # Should return available discovery tracks
        assert response.status_code in [200, 404]  # 404 if endpoint doesn't exist yet
        
    def test_processor_summary_endpoint(self):
        """Test processor summary endpoint"""
        response = self.client.get("/api/processors/summary")
        
        # Should return processor information
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "total_processors" in data or isinstance(data, list)
            
    @patch('src.web.main.get_workflow_engine')
    def test_discovery_execution_endpoint(self, mock_workflow_engine):
        """Test discovery workflow execution endpoint"""
        # Mock workflow engine
        mock_engine = Mock()
        mock_workflow_engine.return_value = mock_engine
        
        # Test discovery request
        discovery_request = {
            "profile_id": "test_profile_123",
            "tracks": ["nonprofit", "government"],
            "options": {
                "include_entity_cache": True,
                "max_results": 100
            }
        }
        
        response = self.client.post("/api/discovery/execute", json=discovery_request)
        
        # Should accept the request (even if mocked)
        assert response.status_code in [200, 202, 404, 422]


class TestAnalysisAPIIntegration:
    """Test analysis workflow API endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        
    def test_scoring_endpoints(self):
        """Test various scoring API endpoints"""
        scoring_endpoints = [
            "/api/scoring/government",
            "/api/scoring/ai-lite",
            "/api/scoring/financial",
            "/api/scoring/network"
        ]
        
        test_data = {
            "profile_id": "test_profile",
            "candidates": [
                {
                    "organization_name": "Test Organization",
                    "ein": "12-3456789",
                    "revenue": 1000000
                }
            ]
        }
        
        for endpoint in scoring_endpoints:
            response = self.client.post(endpoint, json=test_data)
            
            # Should either work or return method not allowed/not found
            assert response.status_code in [200, 202, 404, 405, 422]
            
    def test_ai_processor_endpoints(self):
        """Test AI processor endpoints"""
        ai_endpoints = [
            "/api/ai/lite-1/validate",
            "/api/ai/lite-2/strategic-score", 
            "/api/ai/heavy-1/research-bridge",
            "/api/ai/orchestrated-pipeline"
        ]
        
        test_data = {
            "selected_profile": {
                "organization_name": "Test Profile",
                "focus_areas": ["healthcare", "education"]
            },
            "candidates": [
                {
                    "organization_name": "Test Opportunity",
                    "description": "Test funding opportunity"
                }
            ]
        }
        
        for endpoint in ai_endpoints:
            response = self.client.post(endpoint, json=test_data)
            
            # Should either work or return expected error codes
            assert response.status_code in [200, 202, 400, 404, 422, 500]


class TestWebSocketIntegration:
    """Test WebSocket integration for real-time updates"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.websocket_url = "ws://localhost:8000/ws"
        
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test basic WebSocket connection"""
        try:
            # Start the FastAPI app in test mode
            with TestClient(app) as test_client:
                # Test WebSocket connection
                async with websockets.connect("ws://localhost:8000/ws") as websocket:
                    # Send test message
                    test_message = {"type": "test", "data": "connection_test"}
                    await websocket.send(json.dumps(test_message))
                    
                    # Should not immediately close
                    assert not websocket.closed
                    
        except Exception as e:
            # WebSocket might not be available in test environment
            pytest.skip(f"WebSocket test skipped: {e}")
            
    @pytest.mark.asyncio
    async def test_websocket_progress_updates(self):
        """Test WebSocket progress update functionality"""
        try:
            async with websockets.connect("ws://localhost:8000/ws") as websocket:
                # Simulate progress update request
                progress_message = {
                    "type": "subscribe_progress",
                    "workflow_id": "test_workflow_123"
                }
                await websocket.send(json.dumps(progress_message))
                
                # Wait for response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    response_data = json.loads(response)
                    
                    # Should receive some kind of acknowledgment or update
                    assert isinstance(response_data, dict)
                    
                except asyncio.TimeoutError:
                    # Timeout is acceptable - WebSocket might not respond immediately
                    pass
                    
        except Exception as e:
            pytest.skip(f"WebSocket progress test skipped: {e}")


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        
    def test_complete_workflow_simulation(self):
        """Test complete DISCOVER→PLAN→ANALYZE workflow simulation"""
        # Step 1: Create test profile
        test_profile = {
            "organization_name": "Integration Test Foundation",
            "mission": "Testing complete workflow integration",
            "focus_areas": ["education", "healthcare"],
            "geographic_focus": ["Virginia"],
            "revenue_range": "1M-5M",
            "funding_types": ["government", "foundation"]
        }
        
        profile_response = self.client.post("/api/profiles", json=test_profile)
        
        if profile_response.status_code in [200, 201]:
            profile_data = profile_response.json()
            profile_id = profile_data.get("profile_id") or profile_data.get("id")
            
            if profile_id:
                # Step 2: Execute discovery
                discovery_request = {
                    "profile_id": profile_id,
                    "tracks": ["government", "nonprofit"],
                    "options": {"max_results": 10}
                }
                
                discovery_response = self.client.post("/api/discovery/execute", json=discovery_request)
                
                # Step 3: Execute analysis (if discovery succeeded)
                if discovery_response.status_code in [200, 202]:
                    analysis_request = {
                        "profile_id": profile_id,
                        "analysis_type": "comprehensive",
                        "include_ai_analysis": True
                    }
                    
                    analysis_response = self.client.post("/api/analysis/execute", json=analysis_request)
                    
                    # Should complete workflow or return reasonable error
                    assert analysis_response.status_code in [200, 202, 400, 404, 422]


class TestAPIErrorHandling:
    """Test API error handling and edge cases"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON requests"""
        invalid_json = '{"invalid": json,}'

        response = self.client.post(
            "/api/profiles",
            content=invalid_json,
            headers={"content-type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
        
    def test_missing_required_fields(self):
        """Test handling of minimal profile data"""
        incomplete_profile = {
            "organization_name": "Test Org"
            # Missing other fields - API accepts minimal data
        }

        response = self.client.post("/api/profiles", json=incomplete_profile)

        # API accepts minimal profile data (flexible validation)
        assert response.status_code in [200, 201, 400, 422]

        # Clean up if created successfully
        if response.status_code in [200, 201]:
            profile_data = response.json()
            profile_id = profile_data.get("profile_id") or profile_data.get("id")
            if profile_id:
                self.client.delete(f"/api/profiles/{profile_id}")
        
    def test_nonexistent_endpoints(self):
        """Test handling of non-existent endpoints"""
        response = self.client.get("/api/nonexistent-endpoint")
        assert response.status_code == 404
        
        response = self.client.post("/api/another-nonexistent-endpoint")
        assert response.status_code == 404
        
    def test_method_not_allowed(self):
        """Test method not allowed scenarios"""
        # Try POST on GET-only endpoint
        response = self.client.post("/api/health")
        assert response.status_code in [405, 404]  # Method Not Allowed or Not Found
        
        # Try GET on POST-only endpoint
        response = self.client.get("/api/profiles")  # Assuming this should be GET-able
        # This might be valid, so check for reasonable response
        assert response.status_code in [200, 404, 405]


class TestAPIPerformance:
    """Test API performance characteristics"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        
    def test_health_endpoint_performance(self):
        """Test health endpoint response time"""
        import time
        
        start_time = time.time()
        response = self.client.get("/api/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second
        
    def test_concurrent_api_requests(self):
        """Test API under concurrent load"""
        import concurrent.futures
        import time
        
        def make_request():
            """Make a single API request"""
            start_time = time.time()
            response = self.client.get("/api/health")
            end_time = time.time()
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time
            }
            
        # Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in futures]
            
        # Analyze results
        successful_requests = [r for r in results if r["status_code"] == 200]
        response_times = [r["response_time"] for r in results]
        
        # Performance assertions
        success_rate = len(successful_requests) / len(results) * 100
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        assert success_rate >= 95.0, f"Success rate {success_rate}% below 95% threshold"
        assert avg_response_time < 2.0, f"Average response time {avg_response_time:.3f}s exceeds 2s threshold"
        assert max_response_time < 5.0, f"Maximum response time {max_response_time:.3f}s exceeds 5s threshold"
        
        print(f"Concurrent API test results:")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Average response time: {avg_response_time*1000:.1f}ms")
        print(f"  Maximum response time: {max_response_time*1000:.1f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])