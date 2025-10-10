"""
E2E Test Configuration
=====================

Shared fixtures and utilities for end-to-end testing.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add tool paths
tools_dir = project_root / "tools"
sys.path.insert(0, str(tools_dir / "bmf-filter-tool" / "app"))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_data_dir(tmp_path):
    """Create temporary test data directory"""
    return tmp_path


@pytest.fixture(autouse=True)
def reset_test_environment():
    """Reset test environment before each test"""
    # Cleanup any test data
    yield
    # Teardown after test
