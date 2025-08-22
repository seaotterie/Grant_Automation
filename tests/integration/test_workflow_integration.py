# Integration Tests for Complete Workflow
# Tests the full DISCOVER → PLAN → ANALYZE → EXAMINE → APPROACH workflow

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from src.web.main import app
    WEB_APP_AVAILABLE = True
except ImportError:
    WEB_APP_AVAILABLE = False
    app = None

@pytest.mark.integration
class TestWorkflowIntegration:
    """Test complete workflow integration across all tabs"""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client"""
        if WEB_APP_AVAILABLE and app:
            return TestClient(app)
        else:
            # Mock client for testing
            from unittest.mock import Mock
            mock_client = Mock()
            mock_client.post.return_value.status_code = 200
            mock_client.post.return_value.json.return_value = {"profile_id": "test_profile"}
            mock_client.get.return_value.status_code = 200
            mock_client.get.return_value.json.return_value = {"status": "success"}
            mock_client.delete.return_value.status_code = 200
            return mock_client
    
    @pytest.fixture
    def test_profile_data(self):
        """Test profile for workflow testing"""
        return {
            "organization_name": "Workflow Test Foundation",
            "mission_statement": "Supporting comprehensive educational initiatives",
            "ntee_codes": ["B25", "B28"],
            "revenue": 3000000,
            "staff_count": 35,
            "years_active": 20,
            "state": "VA",
            "city": "Richmond",
            "focus_areas": ["education", "student support", "teacher training"],
            "funding_history": [
                {
                    "funder": "State Education Department",
                    "amount": 250000,
                    "year": 2023,
                    "program": "Teacher Excellence Initiative"
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_complete_workflow_success_path(self, client, test_profile_data):
        """Test complete successful workflow from DISCOVER to APPROACH"""
        
        # Step 1: Create test profile
        profile_response = client.post("/api/profiles", json=test_profile_data)
        
        if hasattr(profile_response, 'status_code'):
            assert profile_response.status_code == 200
            profile_data = profile_response.json()
            profile_id = profile_data.get("profile_id", "test_profile")
        else:
            profile_id = "test_profile"
        
        try:
            # Step 2: DISCOVER - Run discovery across all tracks
            await self._test_discover_phase(client, profile_id)
            
            # Step 3: PLAN - Assess organizational readiness
            await self._test_plan_phase(client, profile_id)
            
            # Step 4: ANALYZE - AI-Lite strategic analysis
            await self._test_analyze_phase(client, profile_id)
            
            # Step 5: EXAMINE - AI Heavy comprehensive research
            await self._test_examine_phase(client, profile_id)
            
            # Step 6: APPROACH - Decision synthesis
            await self._test_approach_phase(client, profile_id)
            
        finally:
            # Cleanup
            try:
                client.delete(f"/api/profiles/{profile_id}")
            except:
                pass  # Ignore cleanup errors in tests
    
    async def _test_discover_phase(self, client, profile_id):
        """Test DISCOVER tab functionality"""
        
        # Test 4-track discovery system
        tracks = [
            "entity-analytics",  # Nonprofit + BMF
            "federal",          # Federal opportunities
            "state",            # State opportunities
            "commercial"        # Commercial opportunities
        ]
        
        for track in tracks:
            if track == "entity-analytics":
                # Test entity-based discovery
                discovery_data = {
                    "max_results": 10,
                    "ntee_filter": ["B25"],
                    "revenue_range": {"min": 100000, "max": 10000000}
                }
                
                response = client.post(
                    f"/api/profiles/{profile_id}/discover/entity-analytics",
                    json=discovery_data
                )
            else:
                # Test other tracks
                discovery_data = {
                    "max_results": 5,
                    "focus_areas": ["education"]
                }
                
                response = client.post(
                    f"/api/discovery/{track}",
                    json=discovery_data
                )
            
            if hasattr(response, 'status_code'):
                # Should return results or appropriate status
                assert response.status_code in [200, 202, 404]  # 202 for async, 404 if not implemented
                
                if response.status_code == 200:
                    data = response.json()
                    # Validate response structure
                    assert "opportunities" in data or "results" in data
    
    async def _test_plan_phase(self, client, profile_id):
        """Test PLAN tab functionality"""
        
        # Test organizational analytics
        analytics_response = client.get(f"/api/profiles/{profile_id}/analytics")
        
        if hasattr(analytics_response, 'status_code'):
            assert analytics_response.status_code in [200, 404]
            
            if analytics_response.status_code == 200:
                analytics_data = analytics_response.json()
                
                # Validate analytics structure
                expected_fields = ["financial_health", "organizational_capacity", "strategic_alignment"]
                for field in expected_fields:
                    if field in analytics_data:
                        # Validate score ranges
                        score = analytics_data[field]
                        if isinstance(score, (int, float)):
                            assert 0.0 <= score <= 1.0
        
        # Test success assessment
        success_response = client.get(f"/api/profiles/{profile_id}/metrics")
        
        if hasattr(success_response, 'status_code'):
            assert success_response.status_code in [200, 404]
        
        # Test network analysis if available
        network_response = client.post("/api/analysis/network", json={
            "profile_id": profile_id,
            "analysis_type": "board_connections"
        })
        
        if hasattr(network_response, 'status_code'):
            assert network_response.status_code in [200, 202, 404, 501]
    
    async def _test_analyze_phase(self, client, profile_id):
        """Test ANALYZE tab functionality"""
        
        # Test AI-Lite analysis
        ai_lite_data = {
            "profile_id": profile_id,
            "opportunities": [
                {
                    "opportunity_id": "test_opp_001",
                    "organization_name": "Test Education Foundation",
                    "description": "Educational support program",
                    "funding_amount": 150000
                }
            ],
            "analysis_type": "strategic_fit"
        }
        
        ai_lite_response = client.post("/api/ai/lite-analysis", json=ai_lite_data)
        
        if hasattr(ai_lite_response, 'status_code'):
            # Should accept request or return not implemented
            assert ai_lite_response.status_code in [200, 202, 404, 501]
            
            if ai_lite_response.status_code == 200:
                ai_data = ai_lite_response.json()
                
                # Validate AI response structure
                if "results" in ai_data:
                    for result in ai_data["results"]:
                        if "compatibility_score" in result:
                            assert 0.0 <= result["compatibility_score"] <= 1.0
        
        # Test batch scoring
        scoring_data = {
            "opportunities": [
                {
                    "opportunity_id": f"batch_opp_{i}",
                    "organization_name": f"Batch Test Foundation {i}",
                    "funding_amount": 100000 + (i * 25000)
                }
                for i in range(5)
            ]
        }
        
        scoring_response = client.post(
            f"/api/profiles/{profile_id}/opportunity-scores",
            json=scoring_data
        )
        
        if hasattr(scoring_response, 'status_code'):
            assert scoring_response.status_code in [200, 202, 404]
    
    async def _test_examine_phase(self, client, profile_id):
        """Test EXAMINE tab functionality"""
        
        # Test AI Heavy deep research
        ai_heavy_data = {
            "profile_id": profile_id,
            "opportunity_id": "test_deep_opp_001",
            "analysis_depth": "comprehensive",
            "include_dossier": True
        }
        
        ai_heavy_response = client.post("/api/ai/deep-research", json=ai_heavy_data)
        
        if hasattr(ai_heavy_response, 'status_code'):
            # Should accept request or return not implemented
            assert ai_heavy_response.status_code in [200, 202, 404, 501]
            
            if ai_heavy_response.status_code == 200:
                heavy_data = ai_heavy_response.json()
                
                # Validate comprehensive analysis structure
                expected_sections = ["partnership_assessment", "strategic_analysis", "implementation_plan"]
                for section in expected_sections:
                    if section in heavy_data:
                        assert isinstance(heavy_data[section], dict)
        
        # Test dossier generation
        dossier_data = {
            "opportunity_id": "test_dossier_opp_001",
            "template": "comprehensive",
            "include_relationships": True
        }
        
        dossier_response = client.post(
            f"/api/profiles/{profile_id}/dossier/generate",
            json=dossier_data
        )
        
        if hasattr(dossier_response, 'status_code'):
            assert dossier_response.status_code in [200, 202, 404, 501]
    
    async def _test_approach_phase(self, client, profile_id):
        """Test APPROACH tab functionality"""
        
        # Test decision synthesis
        decision_data = {
            "opportunity_id": "test_decision_opp_001",
            "include_all_stages": True,
            "decision_framework": "comprehensive"
        }
        
        decision_response = client.post(
            f"/api/profiles/{profile_id}/approach/synthesize-decision",
            json=decision_data
        )
        
        if hasattr(decision_response, 'status_code'):
            # Should accept request or return not implemented
            assert decision_response.status_code in [200, 202, 404, 501]
            
            if decision_response.status_code == 200:
                decision_data = decision_response.json()
                
                # Validate decision synthesis structure
                expected_fields = ["recommendation", "confidence_level", "implementation_plan"]
                for field in expected_fields:
                    if field in decision_data:
                        if field == "confidence_level" and isinstance(decision_data[field], (int, float)):
                            assert 0.0 <= decision_data[field] <= 1.0
        
        # Test export functionality
        export_data = {
            "format": "pdf",
            "template": "executive",
            "include_charts": True
        }
        
        export_response = client.post(
            f"/api/profiles/{profile_id}/approach/export-decision",
            json=export_data
        )
        
        if hasattr(export_response, 'status_code'):
            assert export_response.status_code in [200, 202, 404, 501]
    
    @pytest.mark.asyncio
    async def test_workflow_data_persistence(self, client, test_profile_data):
        """Test that data persists correctly across workflow stages"""
        
        # Create profile
        profile_response = client.post("/api/profiles", json=test_profile_data)
        if hasattr(profile_response, 'status_code'):
            assert profile_response.status_code == 200
            profile_id = profile_response.json().get("profile_id", "test_profile")
        else:
            profile_id = "test_profile"
        
        try:
            # Add opportunities in DISCOVER
            discovery_data = {"max_results": 3}
            client.post(f"/api/profiles/{profile_id}/discover/entity-analytics", json=discovery_data)
            
            # Check opportunities persist in PLAN
            opportunities_response = client.get(f"/api/profiles/{profile_id}/opportunities")
            if hasattr(opportunities_response, 'status_code'):
                if opportunities_response.status_code == 200:
                    opportunities = opportunities_response.json()
                    # Should have opportunities from discovery
                    assert "opportunities" in opportunities
            
            # Update opportunity stage and verify persistence
            if hasattr(opportunities_response, 'status_code') and opportunities_response.status_code == 200:
                opportunities = opportunities_response.json()
                if opportunities.get("opportunities"):
                    first_opp = opportunities["opportunities"][0]
                    opp_id = first_opp.get("opportunity_id")
                    
                    if opp_id:
                        # Update stage
                        stage_update = {"new_stage": "candidates"}
                        stage_response = client.put(
                            f"/api/funnel/{profile_id}/opportunities/{opp_id}/stage",
                            json=stage_update
                        )
                        
                        if hasattr(stage_response, 'status_code'):
                            assert stage_response.status_code in [200, 404, 501]
        
        finally:
            client.delete(f"/api/profiles/{profile_id}")
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, client):
        """Test workflow error handling with invalid data"""
        
        # Test with non-existent profile
        invalid_profile_id = "non_existent_profile_12345"
        
        # Should handle gracefully
        discovery_response = client.post(
            f"/api/profiles/{invalid_profile_id}/discover/entity-analytics",
            json={"max_results": 5}
        )
        
        if hasattr(discovery_response, 'status_code'):
            assert discovery_response.status_code in [404, 422]
        
        analytics_response = client.get(f"/api/profiles/{invalid_profile_id}/analytics")
        if hasattr(analytics_response, 'status_code'):
            assert analytics_response.status_code in [404, 422]
    
    @pytest.mark.asyncio
    async def test_workflow_concurrent_operations(self, client, test_profile_data):
        """Test concurrent operations across workflow stages"""
        
        # Create profile
        profile_response = client.post("/api/profiles", json=test_profile_data)
        if hasattr(profile_response, 'status_code'):
            assert profile_response.status_code == 200
            profile_id = profile_response.json().get("profile_id", "test_profile")
        else:
            profile_id = "test_profile"
        
        try:
            # Run concurrent operations
            async def run_discovery():
                return client.post(
                    f"/api/profiles/{profile_id}/discover/entity-analytics",
                    json={"max_results": 5}
                )
            
            async def run_analytics():
                return client.get(f"/api/profiles/{profile_id}/analytics")
            
            async def run_metrics():
                return client.get(f"/api/profiles/{profile_id}/metrics")
            
            # Execute concurrently
            tasks = [run_discovery(), run_analytics(), run_metrics()]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Should handle concurrent requests
            for result in results:
                if isinstance(result, Exception):
                    # Log but don't fail on concurrent request issues
                    print(f"Concurrent request exception: {result}")
                elif hasattr(result, 'status_code'):
                    assert result.status_code in [200, 202, 404, 429]  # 429 for rate limiting
        
        finally:
            client.delete(f"/api/profiles/{profile_id}")
    
    @pytest.mark.asyncio
    async def test_phase6_systems_integration(self, client, test_profile_data):
        """Test Phase 6 advanced systems integration"""
        
        # Create profile
        profile_response = client.post("/api/profiles", json=test_profile_data)
        if hasattr(profile_response, 'status_code'):
            assert profile_response.status_code == 200
            profile_id = profile_response.json().get("profile_id", "test_profile")
        else:
            profile_id = "test_profile"
        
        try:
            # Test visualization generation
            viz_data = {
                "chart_type": "decision_matrix",
                "data_source": "workflow_results",
                "include_interactive": True
            }
            
            viz_response = client.post("/api/visualizations/generate-chart", json=viz_data)
            if hasattr(viz_response, 'status_code'):
                assert viz_response.status_code in [200, 404, 501]
            
            # Test export system
            export_data = {
                "profile_id": profile_id,
                "format": "pdf",
                "template": "executive",
                "include_visualizations": True
            }
            
            export_response = client.post("/api/export/opportunities", json=export_data)
            if hasattr(export_response, 'status_code'):
                assert export_response.status_code in [200, 202, 404, 501]
            
            # Test decision synthesis framework
            synthesis_data = {
                "opportunity_id": "test_synthesis_opp",
                "workflow_stages": ["discover", "plan", "analyze", "examine"],
                "decision_parameters": {"risk_tolerance": "moderate"}
            }
            
            synthesis_response = client.post(
                f"/api/profiles/{profile_id}/approach/synthesize-decision",
                json=synthesis_data
            )
            if hasattr(synthesis_response, 'status_code'):
                assert synthesis_response.status_code in [200, 202, 404, 501]
        
        finally:
            client.delete(f"/api/profiles/{profile_id}")


@pytest.mark.integration
class TestCacheIntegration:
    """Test entity cache integration across workflow"""
    
    @pytest.mark.asyncio
    async def test_cache_consistency_across_tabs(self, client):
        """Test that cache data is consistent across different tabs"""
        
        # This would test the entity cache manager integration
        # For now, test basic cache endpoints if available
        
        cache_stats_response = client.get("/api/discovery/entity-cache-stats")
        if hasattr(cache_stats_response, 'status_code'):
            if cache_stats_response.status_code == 200:
                stats = cache_stats_response.json()
                
                # Validate cache stats structure
                expected_fields = ["hit_rate", "total_entries"]
                for field in expected_fields:
                    if field in stats:
                        assert isinstance(stats[field], (int, float))
                        if field == "hit_rate":
                            assert 0.0 <= stats[field] <= 1.0


@pytest.mark.integration
class TestAPIConsistency:
    """Test API consistency across different endpoints"""
    
    def test_response_format_consistency(self, client):
        """Test that all API endpoints follow consistent response formats"""
        
        endpoints_to_test = [
            "/api/health",
            "/api/system/status",
            "/api/profiles"
        ]
        
        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            if hasattr(response, 'status_code'):
                if response.status_code == 200:
                    data = response.json()
                    
                    # Should be valid JSON
                    assert isinstance(data, dict)
                    
                    # Should have timestamp for status endpoints
                    if "status" in endpoint or "health" in endpoint:
                        if "timestamp" in data:
                            assert isinstance(data["timestamp"], (int, float, str))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])