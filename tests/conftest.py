"""
Pytest configuration and shared fixtures
"""
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.http_client import get_http_client, cleanup_http_client
from src.profiles.models import OrganizationProfile
from src.core.data_models import BaseOpportunity, GovernmentOpportunity


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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
def sample_organization_profile():
    """Sample organization profile for testing"""
    return OrganizationProfile(
        ein="123456789",
        name="Test Nonprofit Organization",
        state="VA",
        ntee_code="P81",
        ntee_description="Community Health Center",
        revenue=500000.0,
        assets=250000.0,
        expenses=450000.0
    )


@pytest.fixture
def sample_government_opportunity():
    """Sample government opportunity for testing"""
    return GovernmentOpportunity(
        id="test_opp_001",
        title="Community Health Grant Program",
        description="Funding for community health initiatives",
        funder_name="Department of Health and Human Services",
        agency_code="HHS",
        funding_amount_max=50000.0,
        funding_amount_min=10000.0,
        focus_areas=["health", "community"],
        relevance_score=85.0
    )


@pytest.fixture
def mock_api_response():
    """Mock API response data"""
    return {
        "results": [
            {
                "id": "test_001",
                "name": "Test Organization",
                "ein": "123456789",
                "state": "VA"
            }
        ],
        "total": 1,
        "page": 1
    }


@pytest.fixture
def mock_grants_gov_response():
    """Mock Grants.gov API response"""
    return {
        "oppHits": [
            {
                "opportunityId": "EPA-Test-001",
                "opportunityTitle": "Environmental Community Grant",
                "agencyName": "Environmental Protection Agency",
                "agencyCode": "EPA",
                "description": "Funding for environmental projects",
                "awardCeiling": 75000,
                "awardFloor": 15000,
                "closeDate": "2025-06-30",
                "postDate": "2025-01-15"
            }
        ],
        "hitCountTotal": 1,
        "startRecordNum": 0
    }


# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("CATALYNX_ENV", "test")
    monkeypatch.setenv("API_KEY_GRANTS_GOV", "test_key")
    monkeypatch.setenv("API_KEY_PROPUBLICA", "test_key")
    monkeypatch.setenv("API_KEY_FOUNDATION_DIRECTORY", "test_key")