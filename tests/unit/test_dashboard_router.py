#!/usr/bin/env python3
"""
Unit Tests for Dashboard Router
Tests the modularized dashboard API endpoints
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.web.routers.dashboard import router
from src.web.models.responses import DashboardStats, SystemStatus


# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestDashboardRouter:
    """Test dashboard router functionality"""
    
    @patch('src.web.routers.dashboard.get_workflow_engine')
    def test_dashboard_overview_success(self, mock_get_engine):
        """Test successful dashboard overview"""
        # Mock workflow engine
        mock_engine = Mock()
        mock_engine.get_workflow_statistics.return_value = {
            'active_workflows': 5,
            'total_processed': 100,
            'success_rate': 0.95,
            'recent_workflows': ['workflow1', 'workflow2']
        }
        mock_get_engine.return_value = mock_engine
        
        # Test endpoint
        response = client.get("/api/dashboard/overview")
        
        assert response.status_code == 200
        data = response.json()
        assert data['active_workflows'] == 5
        assert data['total_processed'] == 100
        assert data['success_rate'] == 0.95
        assert data['recent_workflows'] == ['workflow1', 'workflow2']
    
    @patch('src.web.routers.dashboard.get_workflow_engine')
    def test_dashboard_overview_error_handling(self, mock_get_engine):
        """Test dashboard overview error handling"""
        # Mock workflow engine to raise exception
        mock_get_engine.side_effect = Exception("Engine failed")
        
        # Test endpoint
        response = client.get("/api/dashboard/overview")
        
        # Should return defaults instead of error
        assert response.status_code == 200
        data = response.json()
        assert data['active_workflows'] == 0
        assert data['total_processed'] == 0
        assert data['success_rate'] == 0.0
        assert data['recent_workflows'] == []
    
    @patch('src.web.routers.dashboard.get_workflow_engine')
    def test_system_status_success(self, mock_get_engine):
        """Test successful system status"""
        # Mock workflow engine
        mock_engine = Mock()
        mock_engine.registry.list_processors.return_value = ['processor1', 'processor2', 'processor3']
        mock_get_engine.return_value = mock_engine
        
        # Test endpoint
        response = client.get("/api/system/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['processors_available'] == 3
        assert data['version'] == '2.0.0'
        assert 'uptime' in data
    
    @patch('src.web.routers.dashboard.get_workflow_engine')
    def test_system_status_error_handling(self, mock_get_engine):
        """Test system status error handling"""
        # Mock workflow engine to raise exception
        mock_get_engine.side_effect = Exception("Engine failed")
        
        # Test endpoint
        response = client.get("/api/system/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'degraded'
        assert data['processors_available'] == 0
        assert 'error' in data
    
    @patch('src.web.routers.dashboard.get_workflow_engine')
    def test_system_health_success(self, mock_get_engine):
        """Test successful system health check"""
        # Mock workflow engine
        mock_engine = Mock()
        mock_engine.registry.list_processors.return_value = ['processor1', 'processor2']
        mock_get_engine.return_value = mock_engine
        
        # Test endpoint
        response = client.get("/api/system/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['processors_available'] == 2
        assert data['services']['api'] == 'operational'
        assert data['services']['database'] == 'operational'
        assert data['services']['processors'] == 'operational'
        assert 'timestamp' in data
        assert 'uptime' in data
    
    @patch('src.web.routers.dashboard.get_workflow_engine')
    def test_system_metrics_success(self, mock_get_engine):
        """Test system metrics endpoint"""
        # Mock workflow engine
        mock_engine = Mock()
        mock_engine.registry.list_processors.return_value = ['proc1', 'proc2', 'proc3']
        mock_get_engine.return_value = mock_engine
        
        # Test endpoint
        response = client.get("/api/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert data['processors']['total'] == 3
        assert data['processors']['active'] == 3
        assert data['processors']['failed'] == 0
        assert 'performance' in data
        assert 'timestamp' in data
    
    @patch('src.web.routers.dashboard.get_workflow_engine')  
    def test_system_processors_success(self, mock_get_engine):
        """Test system processors endpoint"""
        # Mock workflow engine
        mock_engine = Mock()
        mock_engine.registry.list_processors.return_value = ['processor1', 'processor2']
        
        # Mock processor info
        def mock_get_processor_info(name):
            if name == 'processor1':
                return {
                    'description': 'Test processor 1',
                    'version': '1.0.0'
                }
            elif name == 'processor2':
                return {
                    'description': 'Test processor 2', 
                    'version': '2.0.0'
                }
            return None
            
        mock_engine.registry.get_processor_info.side_effect = mock_get_processor_info
        mock_get_engine.return_value = mock_engine
        
        # Test endpoint
        response = client.get("/api/system/processors")
        
        assert response.status_code == 200
        data = response.json()
        assert data['total_processors'] == 2
        assert len(data['processors']) == 2
        
        # Check processor details
        processors = {p['name']: p for p in data['processors']}
        assert processors['processor1']['description'] == 'Test processor 1'
        assert processors['processor1']['version'] == '1.0.0'
        assert processors['processor1']['status'] == 'available'
        assert processors['processor2']['description'] == 'Test processor 2'
        assert processors['processor2']['version'] == '2.0.0'
        assert processors['processor2']['status'] == 'available'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])