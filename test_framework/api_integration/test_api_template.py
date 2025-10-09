"""
API Integration Test Template
Template for testing REST API endpoints with tool execution

API Endpoints by Category:
1. Tool Execution API - /api/v1/tools/*
2. Profile API - /api/profiles/*
3. Opportunity API - /api/opportunities/*
4. Workflow API - /api/workflows/*
5. Foundation Network API - /api/foundation-network/*

Usage:
1. Copy this file and rename to test_{api_category}_api.py
2. Update API_BASE_URL, ENDPOINTS, and test cases
3. Run with pytest: pytest test_framework/api_integration/test_{api_category}_api.py
4. Requires running FastAPI server (launch_catalynx_web.bat)
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, List, Optional
import httpx
import asyncio
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# API configuration
API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 30.0  # seconds

# Test configuration - UPDATE FOR EACH API CATEGORY
API_CATEGORY = "example"  # e.g., "tools", "profiles", "workflows"
ENDPOINTS = {
    "list": "/api/v1/example/list",
    "get": "/api/v1/example/{id}",
    "create": "/api/v1/example",
    "execute": "/api/v1/example/{id}/execute"
}


class TestAPIAvailability:
    """Test API server availability and health"""

    @pytest.mark.asyncio
    async def test_server_is_running(self):
        """Verify FastAPI server is running"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{API_BASE_URL}/health",
                    timeout=5.0
                )
                assert response.status_code == 200, "Server health check failed"
            except httpx.ConnectError:
                pytest.fail(
                    "FastAPI server not running. "
                    "Start with: launch_catalynx_web.bat"
                )

    @pytest.mark.asyncio
    async def test_api_docs_accessible(self):
        """Verify OpenAPI documentation is accessible"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/docs",
                timeout=5.0
            )
            assert response.status_code == 200, "API docs not accessible"

    @pytest.mark.asyncio
    async def test_openapi_spec_valid(self):
        """Verify OpenAPI specification is valid"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/openapi.json",
                timeout=5.0
            )
            assert response.status_code == 200
            spec = response.json()
            assert "openapi" in spec
            assert "paths" in spec
            assert "components" in spec


class TestAPIEndpoints:
    """Test API endpoint functionality"""

    @pytest.mark.asyncio
    async def test_list_endpoint(self):
        """Test list/discovery endpoint"""
        if "list" not in ENDPOINTS:
            pytest.skip("No list endpoint defined")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}{ENDPOINTS['list']}",
                timeout=API_TIMEOUT
            )

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert isinstance(data, (list, dict))

            # UPDATE WITH EXPECTED RESPONSE FIELDS
            # if isinstance(data, dict):
            #     assert "items" in data
            #     assert "total" in data

    @pytest.mark.asyncio
    async def test_get_endpoint(self):
        """Test get by ID endpoint"""
        if "get" not in ENDPOINTS:
            pytest.skip("No get endpoint defined")

        # UPDATE WITH ACTUAL TEST ID
        test_id = "test_id"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}{ENDPOINTS['get'].format(id=test_id)}",
                timeout=API_TIMEOUT
            )

            # Should return 200 (found) or 404 (not found)
            assert response.status_code in [200, 404]

            if response.status_code == 200:
                data = response.json()
                assert data is not None
                # UPDATE WITH EXPECTED RESPONSE FIELDS
                # assert "id" in data

    @pytest.mark.asyncio
    async def test_create_endpoint(self):
        """Test create endpoint"""
        if "create" not in ENDPOINTS:
            pytest.skip("No create endpoint defined")

        # UPDATE WITH ACTUAL CREATE PAYLOAD
        create_payload = {
            "field1": "value1",
            "field2": "value2"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}{ENDPOINTS['create']}",
                json=create_payload,
                timeout=API_TIMEOUT
            )

            # Should return 200 (created) or 201 (created) or 400 (validation error)
            assert response.status_code in [200, 201, 400, 422]

            if response.status_code in [200, 201]:
                data = response.json()
                assert data is not None

    @pytest.mark.asyncio
    async def test_execute_endpoint(self):
        """Test execution endpoint"""
        if "execute" not in ENDPOINTS:
            pytest.skip("No execute endpoint defined")

        # UPDATE WITH ACTUAL TEST ID AND EXECUTION PAYLOAD
        test_id = "test_id"
        execute_payload = {
            "input_field": "value"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}{ENDPOINTS['execute'].format(id=test_id)}",
                json=execute_payload,
                timeout=API_TIMEOUT
            )

            # Should return 200 (success) or 404 (not found) or 400 (validation error)
            assert response.status_code in [200, 404, 400, 422]


class TestAPIValidation:
    """Test API input validation"""

    @pytest.mark.asyncio
    async def test_invalid_json_payload(self):
        """Test API handles invalid JSON gracefully"""
        if "create" not in ENDPOINTS:
            pytest.skip("No create endpoint defined")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}{ENDPOINTS['create']}",
                content="invalid json",
                headers={"Content-Type": "application/json"},
                timeout=API_TIMEOUT
            )

            # Should return 422 (validation error)
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_required_fields(self):
        """Test API validates required fields"""
        if "create" not in ENDPOINTS:
            pytest.skip("No create endpoint defined")

        # Empty payload - missing required fields
        empty_payload = {}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}{ENDPOINTS['create']}",
                json=empty_payload,
                timeout=API_TIMEOUT
            )

            # Should return 422 (validation error)
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_field_types(self):
        """Test API validates field types"""
        if "create" not in ENDPOINTS:
            pytest.skip("No create endpoint defined")

        # UPDATE WITH PAYLOAD CONTAINING INVALID TYPES
        invalid_payload = {
            "numeric_field": "not_a_number",
            "boolean_field": "not_a_boolean"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}{ENDPOINTS['create']}",
                json=invalid_payload,
                timeout=API_TIMEOUT
            )

            # Should return 422 (validation error)
            assert response.status_code == 422


class TestAPIPerformance:
    """Test API performance"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_endpoint_response_time(self):
        """Test API endpoint response time"""
        if "list" not in ENDPOINTS:
            pytest.skip("No list endpoint defined")

        import time

        async with httpx.AsyncClient() as client:
            start = time.time()
            response = await client.get(
                f"{API_BASE_URL}{ENDPOINTS['list']}",
                timeout=API_TIMEOUT
            )
            duration = time.time() - start

            assert response.status_code == 200

            # Most endpoints should respond in < 5 seconds
            max_duration = 5.0
            assert duration < max_duration, \
                f"Endpoint took {duration:.2f}s, expected < {max_duration}s"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_requests(self):
        """Test API handles concurrent requests"""
        if "list" not in ENDPOINTS:
            pytest.skip("No list endpoint defined")

        async def make_request(client):
            response = await client.get(
                f"{API_BASE_URL}{ENDPOINTS['list']}",
                timeout=API_TIMEOUT
            )
            return response.status_code

        async with httpx.AsyncClient() as client:
            # Make 10 concurrent requests
            tasks = [make_request(client) for _ in range(10)]
            results = await asyncio.gather(*tasks)

            # All requests should succeed
            assert all(status == 200 for status in results)


class TestAPIErrorHandling:
    """Test API error handling"""

    @pytest.mark.asyncio
    async def test_not_found_error(self):
        """Test API returns 404 for non-existent resources"""
        if "get" not in ENDPOINTS:
            pytest.skip("No get endpoint defined")

        # Use non-existent ID
        nonexistent_id = "nonexistent_id_12345"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}{ENDPOINTS['get'].format(id=nonexistent_id)}",
                timeout=API_TIMEOUT
            )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_method_not_allowed(self):
        """Test API returns 405 for invalid HTTP methods"""
        if "list" not in ENDPOINTS:
            pytest.skip("No list endpoint defined")

        async with httpx.AsyncClient() as client:
            # Try POST on list endpoint (should only accept GET)
            response = await client.post(
                f"{API_BASE_URL}{ENDPOINTS['list']}",
                timeout=API_TIMEOUT
            )

            # Should return 405 (method not allowed)
            assert response.status_code in [405, 422]

    @pytest.mark.asyncio
    async def test_internal_server_error_handling(self):
        """Test API handles internal errors gracefully"""
        # This test would need to trigger an internal error
        # Skip for now unless specific error scenario is known
        pytest.skip("No specific error scenario defined")


class TestAPIResponseStructure:
    """Test API response structure consistency"""

    @pytest.mark.asyncio
    async def test_response_has_expected_structure(self):
        """Test API responses follow consistent structure"""
        if "list" not in ENDPOINTS:
            pytest.skip("No list endpoint defined")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}{ENDPOINTS['list']}",
                timeout=API_TIMEOUT
            )

            assert response.status_code == 200
            data = response.json()

            # UPDATE WITH EXPECTED RESPONSE STRUCTURE
            # assert isinstance(data, dict)
            # assert "data" in data or "items" in data
            # assert "metadata" in data or "total" in data

    @pytest.mark.asyncio
    async def test_error_response_structure(self):
        """Test error responses follow consistent structure"""
        if "get" not in ENDPOINTS:
            pytest.skip("No get endpoint defined")

        # Trigger 404 error
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}{ENDPOINTS['get'].format(id='nonexistent')}",
                timeout=API_TIMEOUT
            )

            if response.status_code == 404:
                error_data = response.json()

                # Error responses should have consistent structure
                # UPDATE WITH EXPECTED ERROR STRUCTURE
                # assert "detail" in error_data or "error" in error_data


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for API integration tests"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "requires_server: marks tests requiring running server"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
