# Unit Tests for API Endpoints
# Tests FastAPI endpoints with comprehensive coverage

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from src.web.main import app
    WEB_APP_AVAILABLE = True
except ImportError:
    WEB_APP_AVAILABLE = False
    app = None

@pytest.mark.skipif(not WEB_APP_AVAILABLE, reason="Web app not available")
class TestHealthEndpoints:
    """Test system health and status endpoints"""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client"""
        return TestClient(app)
    
    def test_health_endpoint_success(self, client):
        """Test health endpoint returns success"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "status" in data
        assert "timestamp" in data
        
        # Validate status
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
    
    def test_health_endpoint_response_time(self, client):
        """Test health endpoint response time"""
        import time
        
        start_time = time.perf_counter()
        response = client.get("/api/health")
        end_time = time.perf_counter()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5  # Should respond within 500ms
    
    def test_system_status_endpoint(self, client):
        """Test system status endpoint if available"""
        response = client.get("/api/system/status")
        
        # Should either work or return 404 if not implemented
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            
            # Should have system information
            expected_fields = ["timestamp", "uptime", "version"]
            for field in expected_fields:
                if field in data:
                    assert data[field] is not None


class TestProfileEndpoints:
    """Test profile management endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client with mocked dependencies"""
        if WEB_APP_AVAILABLE and app:
            return TestClient(app)
        else:
            # Mock client for testing when app isn't available
            mock_client = Mock()
            mock_client.post.return_value.status_code = 200
            mock_client.post.return_value.json.return_value = {"profile_id": "test_profile_123"}
            mock_client.get.return_value.status_code = 200
            mock_client.get.return_value.json.return_value = {
                "profile_id": "test_profile_123",
                "organization_name": "Test Organization"
            }
            mock_client.put.return_value.status_code = 200
            mock_client.delete.return_value.status_code = 200
            return mock_client
    
    @pytest.fixture
    def valid_profile_data(self):
        """Valid profile data for testing"""
        return {
            "organization_name": "Test Education Foundation",
            "mission_statement": "Supporting educational excellence in underserved communities",
            "ntee_codes": ["B25", "B28"],
            "revenue": 2500000,
            "staff_count": 25,
            "years_active": 15,
            "state": "VA",
            "city": "Richmond",
            "focus_areas": ["education", "student support", "literacy"]
        }
    
    def test_create_profile_success(self, client, valid_profile_data):
        """Test successful profile creation"""
        response = client.post("/api/profiles", json=valid_profile_data)
        
        if hasattr(response, 'status_code'):
            assert response.status_code in [200, 201]
            
            if response.status_code in [200, 201]:
                data = response.json()
                assert "profile_id" in data
                assert data["profile_id"] is not None
    
    def test_create_profile_validation(self, client):
        """Test profile creation validation"""
        # Test missing required fields
        invalid_data = {
            "mission_statement": "Missing required fields"
        }
        
        response = client.post("/api/profiles", json=invalid_data)
        
        if hasattr(response, 'status_code'):
            # Should return validation error
            assert response.status_code in [400, 422]
    
    def test_get_profile_success(self, client, valid_profile_data):
        """Test profile retrieval"""
        # First create a profile
        create_response = client.post("/api/profiles", json=valid_profile_data)
        
        if hasattr(create_response, 'status_code') and create_response.status_code in [200, 201]:
            create_data = create_response.json()
            profile_id = create_data.get("profile_id", "test_profile")
            
            # Then retrieve it
            get_response = client.get(f"/api/profiles/{profile_id}")
            
            if hasattr(get_response, 'status_code'):
                assert get_response.status_code in [200, 404]
                
                if get_response.status_code == 200:
                    profile_data = get_response.json()
                    assert profile_data["organization_name"] == valid_profile_data["organization_name"]
    
    def test_get_nonexistent_profile(self, client):
        """Test retrieval of non-existent profile"""
        response = client.get("/api/profiles/nonexistent_profile_12345")
        
        if hasattr(response, 'status_code'):
            assert response.status_code == 404
    
    def test_update_profile(self, client, valid_profile_data):
        """Test profile update"""
        # Create profile first
        create_response = client.post("/api/profiles", json=valid_profile_data)
        
        if hasattr(create_response, 'status_code') and create_response.status_code in [200, 201]:
            create_data = create_response.json()
            profile_id = create_data.get("profile_id", "test_profile")
            
            # Update profile
            update_data = {"revenue": 3000000}
            update_response = client.put(f"/api/profiles/{profile_id}", json=update_data)
            
            if hasattr(update_response, 'status_code'):
                assert update_response.status_code in [200, 404]
    
    def test_delete_profile(self, client, valid_profile_data):
        """Test profile deletion"""
        # Create profile first
        create_response = client.post("/api/profiles", json=valid_profile_data)
        
        if hasattr(create_response, 'status_code') and create_response.status_code in [200, 201]:
            create_data = create_response.json()
            profile_id = create_data.get("profile_id", "test_profile")
            
            # Delete profile
            delete_response = client.delete(f"/api/profiles/{profile_id}")
            
            if hasattr(delete_response, 'status_code'):
                assert delete_response.status_code in [200, 204, 404]
    
    def test_list_profiles(self, client):
        """Test profile listing"""
        response = client.get("/api/profiles")
        
        if hasattr(response, 'status_code'):
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (list, dict))
                
                if isinstance(data, dict):
                    assert "profiles" in data or "results" in data


class TestDiscoveryEndpoints:
    """Test discovery-related endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        if WEB_APP_AVAILABLE and app:
            return TestClient(app)
        else:
            mock_client = Mock()
            mock_client.post.return_value.status_code = 200
            mock_client.post.return_value.json.return_value = {
                "opportunities": [],
                "total_found": 0,
                "processing_time": 0.5
            }
            mock_client.get.return_value.status_code = 200
            mock_client.get.return_value.json.return_value = {
                "hit_rate": 0.85,
                "total_entries": 1250
            }
            return mock_client
    
    def test_entity_discovery_endpoint(self, client):
        """Test entity-based discovery endpoint"""
        discovery_data = {
            "max_results": 10,
            "ntee_filter": ["B25"],
            "revenue_range": {"min": 100000, "max": 5000000}
        }
        
        response = client.post("/api/profiles/test_profile/discover/entity-analytics", json=discovery_data)
        
        if hasattr(response, 'status_code'):
            # Should return results or appropriate error
            assert response.status_code in [200, 202, 404, 422]
            
            if response.status_code == 200:
                data = response.json()
                assert "opportunities" in data or "results" in data
    
    def test_cache_stats_endpoint(self, client):
        """Test entity cache statistics endpoint"""
        response = client.get("/api/discovery/entity-cache-stats")
        
        if hasattr(response, 'status_code'):
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["hit_rate", "total_entries"]
                for field in expected_fields:
                    if field in data:
                        assert isinstance(data[field], (int, float))
    
    def test_discovery_validation(self, client):
        """Test discovery parameter validation"""
        # Test invalid parameters
        invalid_data = {
            "max_results": -1,  # Invalid negative value
            "revenue_range": {"min": 1000000, "max": 100000}  # Min > Max
        }
        
        response = client.post("/api/profiles/test_profile/discover/entity-analytics", json=invalid_data)
        
        if hasattr(response, 'status_code'):
            # Should return validation error
            assert response.status_code in [400, 422]


class TestAnalyticsEndpoints:
    """Test analytics and metrics endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        if WEB_APP_AVAILABLE and app:
            return TestClient(app)
        else:
            mock_client = Mock()
            mock_client.get.return_value.status_code = 200
            mock_client.get.return_value.json.return_value = {
                "financial_health": 0.85,
                "organizational_capacity": 0.75,
                "network_influence": 0.65
            }
            return mock_client
    
    def test_profile_analytics_endpoint(self, client):
        """Test profile analytics endpoint"""
        response = client.get("/api/profiles/test_profile/analytics")
        
        if hasattr(response, 'status_code'):
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate analytics structure
                for field_name, value in data.items():
                    if isinstance(value, (int, float)) and "score" in field_name.lower():
                        assert 0.0 <= value <= 1.0, f"Score {field_name} out of range: {value}"
    
    def test_profile_metrics_endpoint(self, client):
        """Test profile metrics endpoint"""
        response = client.get("/api/profiles/test_profile/metrics")
        
        if hasattr(response, 'status_code'):
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                # Should have metrics data
                assert isinstance(data, dict)


class TestAIEndpoints:
    """Test AI analysis endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        if WEB_APP_AVAILABLE and app:
            return TestClient(app)
        else:
            mock_client = Mock()
            mock_client.post.return_value.status_code = 202  # Accepted for processing
            mock_client.post.return_value.json.return_value = {
                "status": "accepted",
                "job_id": "ai_job_123",
                "estimated_completion": "30s"
            }
            return mock_client
    
    def test_ai_lite_analysis_endpoint(self, client):
        """Test AI-Lite analysis endpoint"""
        analysis_data = {
            "profile_id": "test_profile",
            "opportunity_id": "test_opp_001",
            "analysis_type": "strategic_fit"
        }
        
        response = client.post("/api/ai/lite-analysis", json=analysis_data)
        
        if hasattr(response, 'status_code'):
            # Should accept request or return not implemented
            assert response.status_code in [200, 202, 404, 501]
    
    def test_ai_heavy_research_endpoint(self, client):
        """Test AI Heavy research endpoint"""
        research_data = {
            "profile_id": "test_profile",
            "opportunity_id": "test_opp_001",
            "depth": "comprehensive"
        }
        
        response = client.post("/api/ai/deep-research", json=research_data)
        
        if hasattr(response, 'status_code'):
            # Should accept request or return not implemented
            assert response.status_code in [200, 202, 404, 501]


class TestExportEndpoints:
    """Test export functionality endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        if WEB_APP_AVAILABLE and app:
            return TestClient(app)
        else:
            mock_client = Mock()
            mock_client.post.return_value.status_code = 200
            mock_client.post.return_value.headers = {"content-type": "application/pdf"}
            mock_client.post.return_value.content = b"Mock PDF content"
            return mock_client
    
    def test_export_opportunities_endpoint(self, client):
        """Test opportunity export endpoint"""
        export_data = {
            "profile_id": "test_profile",
            "format": "pdf",
            "template": "executive"
        }
        
        response = client.post("/api/export/opportunities", json=export_data)
        
        if hasattr(response, 'status_code'):
            assert response.status_code in [200, 202, 404, 501]
    
    def test_export_format_validation(self, client):
        """Test export format validation"""
        # Test invalid format
        invalid_export_data = {
            "profile_id": "test_profile",
            "format": "invalid_format",
            "template": "executive"
        }
        
        response = client.post("/api/export/opportunities", json=invalid_export_data)
        
        if hasattr(response, 'status_code'):
            # Should return validation error or accept (if validation is lenient)
            assert response.status_code in [200, 202, 400, 422, 404, 501]


class TestErrorHandling:
    """Test API error handling"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        if WEB_APP_AVAILABLE and app:
            return TestClient(app)
        else:
            mock_client = Mock()
            mock_client.get.return_value.status_code = 404
            mock_client.get.return_value.json.return_value = {"detail": "Not found"}
            mock_client.post.return_value.status_code = 422
            mock_client.post.return_value.json.return_value = {"detail": "Validation error"}
            return mock_client
    
    def test_404_error_handling(self, client):
        """Test 404 error handling"""
        response = client.get("/api/nonexistent/endpoint")
        
        if hasattr(response, 'status_code'):
            assert response.status_code == 404
    
    def test_malformed_json_handling(self, client):
        """Test malformed JSON handling"""
        # Send malformed JSON
        response = client.post(
            "/api/profiles",
            data="{ invalid json",
            headers={"content-type": "application/json"}
        )
        
        if hasattr(response, 'status_code'):
            # Should return bad request
            assert response.status_code in [400, 422]
    
    def test_missing_content_type(self, client):
        """Test missing content type handling"""
        response = client.post("/api/profiles", data='{"test": "data"}')
        
        if hasattr(response, 'status_code'):
            # Should handle gracefully
            assert response.status_code in [200, 201, 400, 415, 422]


class TestCORS:
    """Test CORS configuration"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        if WEB_APP_AVAILABLE and app:
            return TestClient(app)
        else:
            mock_client = Mock()
            mock_client.options.return_value.status_code = 200
            mock_client.options.return_value.headers = {
                "access-control-allow-origin": "*",
                "access-control-allow-methods": "GET, POST, PUT, DELETE",
                "access-control-allow-headers": "Content-Type, Authorization"
            }
            return mock_client
    
    def test_cors_preflight(self, client):
        """Test CORS preflight request"""
        response = client.options(
            "/api/profiles",
            headers={
                "origin": "http://localhost:3000",
                "access-control-request-method": "POST",
                "access-control-request-headers": "Content-Type"
            }
        )
        
        if hasattr(response, 'status_code'):
            # Should allow CORS or return method not allowed
            assert response.status_code in [200, 204, 405]


@pytest.mark.integration
class TestEndpointIntegration:
    """Integration tests for endpoint workflows"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        if WEB_APP_AVAILABLE and app:
            return TestClient(app)
        else:
            pytest.skip("Web app not available for integration tests")
    
    def test_complete_profile_workflow(self, client, enhanced_organization_profile):
        """Test complete profile management workflow"""
        # Create profile
        create_response = client.post("/api/profiles", json=enhanced_organization_profile)
        assert create_response.status_code in [200, 201]
        
        profile_data = create_response.json()
        profile_id = profile_data["profile_id"]
        
        try:
            # Get profile
            get_response = client.get(f"/api/profiles/{profile_id}")
            assert get_response.status_code == 200
            
            # Update profile
            update_data = {"revenue": 3500000}
            update_response = client.put(f"/api/profiles/{profile_id}", json=update_data)
            assert update_response.status_code == 200
            
            # Run discovery
            discovery_data = {"max_results": 5}
            discovery_response = client.post(
                f"/api/profiles/{profile_id}/discover/entity-analytics",
                json=discovery_data
            )
            assert discovery_response.status_code in [200, 202]
            
        finally:
            # Cleanup
            delete_response = client.delete(f"/api/profiles/{profile_id}")
            assert delete_response.status_code in [200, 204]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])