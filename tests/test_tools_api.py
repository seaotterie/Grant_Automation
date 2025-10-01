"""
Comprehensive API Testing for Unified Tool Execution
Tests all 22 tools via REST API endpoints
"""

import pytest
from httpx import AsyncClient
import asyncio


@pytest.mark.asyncio
async def test_list_tools():
    """Test GET /api/v1/tools endpoint"""
    from src.web.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/tools")

        assert response.status_code == 200
        data = response.json()

        assert "tools" in data
        assert "total_count" in data
        assert "operational_count" in data
        assert data["operational_count"] >= 22  # At least 22 operational tools


@pytest.mark.asyncio
async def test_list_tools_by_category():
    """Test filtering tools by category"""
    from src.web.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/tools?category=scoring")

        assert response.status_code == 200
        data = response.json()

        # Should have at least Tool 20 (Multi-Dimensional Scorer)
        assert data["total_count"] >= 1


@pytest.mark.asyncio
async def test_get_tool_metadata():
    """Test GET /api/v1/tools/{tool_name} endpoint"""
    from src.web.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/tools/multi-dimensional-scorer-tool")

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Multi-Dimensional Scorer Tool"
        assert data["status"] == "operational"
        assert data["cost_per_operation"] == 0.0


@pytest.mark.asyncio
async def test_get_nonexistent_tool():
    """Test 404 for nonexistent tool"""
    from src.web.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/tools/nonexistent-tool")

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_execute_scorer_tool():
    """Test executing Multi-Dimensional Scorer via API"""
    from src.web.main import app

    request_data = {
        "inputs": {
            "scoring_input": {
                "opportunity_data": {
                    "opportunity_id": "TEST-001",
                    "title": "Test Grant",
                    "award_amount": 50000,
                    "location": "VA"
                },
                "organization_profile": {
                    "ein": "12-3456789",
                    "name": "Test Org",
                    "revenue": 500000
                },
                "workflow_stage": "discover",
                "track_type": "nonprofit"
            }
        }
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/tools/multi-dimensional-scorer-tool/execute",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["cost"] == 0.0
        assert "data" in data
        assert "overall_score" in data["data"]


@pytest.mark.asyncio
async def test_health_check():
    """Test tool API health check"""
    from src.web.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/tools/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["operational_tools"] >= 22


@pytest.mark.asyncio
async def test_list_categories():
    """Test listing tool categories"""
    from src.web.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/tools/categories/list")

        assert response.status_code == 200
        data = response.json()

        assert "categories" in data
        assert isinstance(data["categories"], list)
        assert len(data["categories"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
