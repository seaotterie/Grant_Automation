# Test Configuration and Fixtures for Catalynx Testing Framework
# Enhanced configuration providing comprehensive test setup, fixtures, and utilities

import pytest
import asyncio
import os
import tempfile
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import existing components
from src.core.http_client import get_http_client, cleanup_http_client
from src.profiles.models import OrganizationProfile
from src.core.data_models import BaseOpportunity, GovernmentOpportunity

# Import FastAPI app for testing
try:
    from src.web.main import app
except ImportError:
    app = None

# Test configuration
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_catalynx.db")
TEST_CACHE_URL = os.getenv("TEST_CACHE_URL", "memory://")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    
    yield loop
    
    if not loop.is_closed():
        loop.close()

@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI application"""
    if app:
        with TestClient(app) as client:
            yield client
    else:
        # Mock client if app is not available
        yield Mock()

@pytest.fixture
async def http_client():
    """Provide HTTP client for testing"""
    client = get_http_client()
    yield client
    await cleanup_http_client()

@pytest.fixture
def temp_directory():
    """Provide temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_dir():
    """Alternative temporary directory fixture name"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_organization_profile():
    """Enhanced sample organization profile for testing"""
    return OrganizationProfile(
        ein="123456789",
        name="Test Education Foundation",
        state="VA",
        ntee_code="B25",
        ntee_description="Educational Support Services",
        revenue=2500000.0,
        assets=1500000.0,
        expenses=2200000.0
    )

@pytest.fixture
def enhanced_organization_profile():
    """Comprehensive organization profile with all fields"""
    return {
        "profile_id": "test_profile_001",
        "organization_name": "Comprehensive Test Foundation",
        "mission_statement": "Supporting educational initiatives and community development",
        "ntee_codes": ["B25", "B28"],
        "revenue": 2500000,
        "staff_count": 25,
        "years_active": 15,
        "state": "VA",
        "city": "Richmond",
        "focus_areas": ["education", "student support", "literacy"],
        "funding_history": [
            {
                "funder": "Education Grant Foundation",
                "amount": 150000,
                "year": 2023,
                "program": "Literacy Initiative"
            }
        ]
    }

@pytest.fixture
def sample_government_opportunity():
    """Enhanced sample government opportunity for testing"""
    return GovernmentOpportunity(
        id="test_gov_opp_001",
        title="Community Education Enhancement Grant",
        description="Federal funding for community-based education programs",
        funder_name="Department of Education",
        agency_code="ED",
        funding_amount_max=275000.0,
        funding_amount_min=50000.0,
        focus_areas=["education", "community", "literacy"],
        relevance_score=88.5
    )

@pytest.fixture
def sample_opportunity():
    """General opportunity fixture for testing"""
    return {
        "opportunity_id": "opp_test_001",
        "organization_name": "Educational Excellence Foundation",
        "source_type": "Foundation",
        "discovery_source": "ProPublica",
        "program_name": "STEM Education Grant",
        "description": "Supporting STEM education programs in underserved communities",
        "funding_amount": 250000,
        "application_deadline": (datetime.now() + timedelta(days=60)).isoformat(),
        "ntee_codes": ["B25"],
        "external_data": {
            "state": "VA",
            "geographic_scope": "Regional"
        },
        "raw_score": 0.75,
        "compatibility_score": 0.80,
        "confidence_level": 0.85,
        "funnel_stage": "prospects"
    }

@pytest.fixture
def sample_opportunities_batch():
    """Batch of opportunities for testing batch operations"""
    opportunities = []
    
    for i in range(10):
        opp = {
            "opportunity_id": f"batch_opp_{i:03d}",
            "organization_name": f"Test Foundation {i}",
            "source_type": ["Foundation", "Government", "Corporate"][i % 3],
            "discovery_source": "Test Source",
            "funding_amount": 100000 + (i * 50000),
            "raw_score": 0.5 + (i * 0.05),
            "compatibility_score": 0.6 + (i * 0.04),
            "confidence_level": 0.7 + (i * 0.03),
            "funnel_stage": ["prospects", "qualified_prospects", "candidates"][i % 3]
        }
        opportunities.append(opp)
    
    return opportunities

@pytest.fixture
def mock_entity_cache():
    """Mock entity cache manager for testing"""
    cache_mock = Mock()
    
    # Mock cached entity data
    cache_mock.get_entity_data.return_value = {
        "ein": "12-3456789",
        "organization_name": "Cached Test Organization",
        "revenue": 1500000,
        "ntee_codes": ["B25"],
        "board_members": [
            {"name": "John Smith", "title": "Board Chair"},
            {"name": "Jane Doe", "title": "Treasurer"}
        ]
    }
    
    cache_mock.get_cache_stats.return_value = {
        "hit_rate": 0.85,
        "total_entries": 1250,
        "cache_size_mb": 45.2
    }
    
    cache_mock.store_entity_data.return_value = True
    
    return cache_mock

@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing AI-powered components"""
    ai_mock = AsyncMock()
    
    # Mock AI-Lite responses
    ai_mock.analyze_lite.return_value = {
        "compatibility_score": 0.82,
        "strategic_value": "high",
        "risk_assessment": ["timeline_pressure", "capacity_concerns"],
        "priority_rank": 2,
        "funding_likelihood": 0.75,
        "strategic_rationale": "Strong mission alignment with proven track record in education sector.",
        "action_priority": "immediate",
        "confidence_level": 0.88
    }
    
    # Mock AI-Heavy responses
    ai_mock.analyze_heavy.return_value = {
        "partnership_assessment": {
            "mission_alignment_score": 85,
            "strategic_value": "exceptional",
            "mutual_benefits": ["program expansion", "knowledge sharing"],
            "partnership_potential": "long_term_strategic"
        },
        "funding_strategy": {
            "optimal_request_amount": 275000,
            "timing_strategy": "Q2 application cycle",
            "positioning_strategy": "Lead with proven outcomes"
        },
        "comprehensive_analysis": {
            "relationship_mapping": ["shared board member: Sarah Johnson"],
            "competitive_advantages": ["local presence", "demonstrated impact"],
            "implementation_timeline": "6-month preparation recommended"
        }
    }
    
    return ai_mock

@pytest.fixture
def mock_api_response():
    """Enhanced mock API response data"""
    return {
        "results": [
            {
                "id": "test_001",
                "name": "Test Organization",
                "ein": "123456789",
                "state": "VA",
                "revenue": 1000000,
                "ntee_code": "B25"
            }
        ],
        "total": 1,
        "page": 1,
        "total_pages": 1
    }

@pytest.fixture
def mock_grants_gov_response():
    """Enhanced mock Grants.gov API response"""
    return {
        "oppHits": [
            {
                "opportunityId": "ED-Test-001",
                "opportunityTitle": "Education Innovation Grant",
                "agencyName": "Department of Education",
                "agencyCode": "ED",
                "description": "Federal funding for innovative education programs",
                "awardCeiling": 275000,
                "awardFloor": 50000,
                "closeDate": "2025-06-30",
                "postDate": "2025-01-15",
                "eligibilityCategories": ["Nonprofits"],
                "fundingActivity": ["Education"]
            }
        ],
        "hitCountTotal": 1,
        "startRecordNum": 0
    }

@pytest.fixture
def performance_test_data():
    """Generate large dataset for performance testing"""
    profiles = []
    opportunities = []
    
    # Generate 100 test profiles
    for i in range(100):
        profile = {
            "profile_id": f"perf_profile_{i:03d}",
            "organization_name": f"Performance Test Org {i}",
            "revenue": 500000 + (i * 100000),
            "ntee_codes": [["B25", "P20", "T30"][i % 3]],
            "state": ["VA", "MD", "NC", "DC"][i % 4]
        }
        profiles.append(profile)
    
    # Generate 1000 test opportunities
    for i in range(1000):
        opportunity = {
            "opportunity_id": f"perf_opp_{i:04d}",
            "organization_name": f"Perf Test Foundation {i}",
            "funding_amount": 50000 + (i * 1000),
            "raw_score": 0.3 + (i % 70) * 0.01,  # Spread across score range
            "source_type": ["Foundation", "Government", "Corporate"][i % 3]
        }
        opportunities.append(opportunity)
    
    return {
        "profiles": profiles,
        "opportunities": opportunities
    }

@pytest.fixture
def edge_case_data():
    """Provide edge case data for robust testing"""
    return {
        "invalid_profiles": [
            {"organization_name": None},  # Missing required field
            {"revenue": -1000},           # Invalid negative revenue
            {"ntee_codes": "invalid"},    # Wrong data type
            {"state": "INVALID"}          # Invalid state code
        ],
        "invalid_opportunities": [
            {"opportunity_id": ""},       # Empty ID
            {"raw_score": 1.5},          # Score out of range
            {"funding_amount": "invalid"}, # Wrong data type
            {}                           # Empty object
        ],
        "malicious_inputs": [
            {"organization_name": "<script>alert('xss')</script>"},
            {"mission_statement": "'; DROP TABLE profiles; --"},
            {"description": "javascript:alert('xss')"}
        ]
    }

@pytest.fixture
def test_environment_config():
    """Provide test environment configuration"""
    return {
        "database_url": TEST_DATABASE_URL,
        "cache_url": TEST_CACHE_URL,
        "log_level": "DEBUG",
        "testing": True,
        "ai_service_enabled": False,  # Disable real AI calls in tests
        "cache_enabled": True,
        "rate_limiting_enabled": False,  # Disable for testing
        "external_apis_enabled": False   # Mock external API calls
    }

# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Enhanced mock environment variables for testing"""
    monkeypatch.setenv("CATALYNX_ENV", "test")
    monkeypatch.setenv("API_KEY_GRANTS_GOV", "test_key")
    monkeypatch.setenv("API_KEY_PROPUBLICA", "test_key")
    monkeypatch.setenv("API_KEY_FOUNDATION_DIRECTORY", "test_key")
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("CACHE_URL", TEST_CACHE_URL)
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("TESTING", "true")

# Utility functions for tests
def assert_valid_score(score: float, field_name: str = "score"):
    """Assert that a score is in valid range [0.0, 1.0]"""
    assert isinstance(score, (int, float)), f"{field_name} must be numeric"
    assert 0.0 <= score <= 1.0, f"{field_name} must be between 0.0 and 1.0, got {score}"

def assert_valid_profile(profile: Dict[str, Any]):
    """Assert that a profile contains required fields"""
    required_fields = ["organization_name"]
    
    for field in required_fields:
        assert field in profile, f"Profile missing required field: {field}"
        assert profile[field], f"Profile field {field} cannot be empty"

def assert_valid_opportunity(opportunity: Dict[str, Any]):
    """Assert that an opportunity contains required fields"""
    required_fields = ["opportunity_id", "organization_name", "source_type"]
    
    for field in required_fields:
        assert field in opportunity, f"Opportunity missing required field: {field}"
        assert opportunity[field], f"Opportunity field {field} cannot be empty"

def assert_api_response_structure(response_data: Dict[str, Any], expected_fields: List[str]):
    """Assert that API response has expected structure"""
    for field in expected_fields:
        assert field in response_data, f"API response missing field: {field}"

def create_test_file(temp_dir: Path, filename: str, content: str) -> Path:
    """Create a test file with specified content"""
    file_path = temp_dir / filename
    file_path.write_text(content)
    return file_path

def create_test_json_file(temp_dir: Path, filename: str, data: Dict[str, Any]) -> Path:
    """Create a test JSON file with specified data"""
    file_path = temp_dir / filename
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    return file_path

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
    config.addinivalue_line(
        "markers", "phase6: mark test as Phase 6 system test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "external: mark test as requiring external services"
    )

def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on path"""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Mark performance tests
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        
        # Mark security tests
        if "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        
        # Mark phase6 tests
        if "phase6" in str(item.fspath):
            item.add_marker(pytest.mark.phase6)