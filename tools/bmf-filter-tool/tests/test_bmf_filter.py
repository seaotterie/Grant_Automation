"""
BMF Filter Tool - Basic Tests
============================

Tests for the 12-factor BMF Filter Tool implementation.
Validates core functionality and 12-factor compliance.
"""

import os
import pytest
import tempfile
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.bmf_filter import BMFFilterTool
from app.generated import (
    BMFFilterIntent, BMFFilterCriteria, BMFSearchPriority,
    BMFSortOption
)

class TestBMFFilterTool:
    """Test cases for BMF Filter Tool"""

    @pytest.fixture
    def sample_csv_data(self):
        """Create sample BMF CSV data for testing"""
        data = {
            'EIN': ['123456789', '987654321', '111222333', '444555666', '777888999'],
            'NAME': ['Test Education Org', 'Sample Health Center', 'Virginia Arts Council', 'Child Development Center', 'Tech Training Institute'],
            'CITY': ['Richmond', 'Norfolk', 'Virginia Beach', 'Alexandria', 'Charlottesville'],
            'STATE': ['VA', 'VA', 'VA', 'VA', 'VA'],
            'ZIP': ['23220', '23510', '23450', '22301', '22901'],
            'NTEE_CD': ['P20', 'B25', 'A20', 'P99', 'P20'],
            'SUBSECTION': ['03', '03', '03', '03', '03'],
            'STATUS': ['01', '01', '01', '01', '01'],
            'INCOME_AMT': ['500000', '1200000', '75000', '800000', '300000'],
            'ASSET_AMT': ['1000000', '5000000', '200000', '2000000', '600000'],
            'FOUNDATION': ['', '', '', '', '']
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_csv_file(self, sample_csv_data):
        """Create temporary CSV file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_csv_data.to_csv(f.name, index=False)
            yield f.name
        os.unlink(f.name)

    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file for testing"""
        config = {
            "ntee_codes": ["P20", "B25", "A20"]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(config, f)
            yield f.name
        os.unlink(f.name)

    @pytest.fixture
    def bmf_tool(self, temp_csv_file, temp_config_file):
        """Create BMF Filter Tool with test data"""
        # Set environment variables for test
        os.environ['BMF_INPUT_PATH'] = temp_csv_file
        os.environ['BMF_FILTER_CONFIG_PATH'] = temp_config_file
        os.environ['BMF_CACHE_ENABLED'] = 'false'  # Disable cache for testing

        tool = BMFFilterTool()
        yield tool

        # Cleanup environment
        for key in ['BMF_INPUT_PATH', 'BMF_FILTER_CONFIG_PATH', 'BMF_CACHE_ENABLED']:
            os.environ.pop(key, None)

    @pytest.mark.asyncio
    async def test_basic_filtering(self, bmf_tool):
        """Test basic filtering functionality"""
        intent = BMFFilterIntent(
            criteria=BMFFilterCriteria(
                states=["VA"],
                ntee_codes=["P20"],  # Education
                limit=10
            ),
            what_youre_looking_for="Education organizations in Virginia"
        )

        result = await bmf_tool.execute(intent)

        assert result is not None
        assert len(result.organizations) == 2  # Should find 2 education orgs
        assert all(org.state == "VA" for org in result.organizations)
        assert all(org.ntee_code == "P20" for org in result.organizations)
        assert result.summary.total_found == 2

    @pytest.mark.asyncio
    async def test_revenue_filtering(self, bmf_tool):
        """Test revenue-based filtering"""
        intent = BMFFilterIntent(
            criteria=BMFFilterCriteria(
                states=["VA"],
                revenue_min=600000,  # Should filter to orgs with revenue >= 600K
                limit=10
            ),
            what_youre_looking_for="High-revenue Virginia organizations"
        )

        result = await bmf_tool.execute(intent)

        assert result is not None
        # Should find orgs with revenue >= 600K: 1200000, 800000
        assert len(result.organizations) == 2
        for org in result.organizations:
            assert org.revenue is None or org.revenue >= 600000

    @pytest.mark.asyncio
    async def test_name_filtering(self, bmf_tool):
        """Test organization name filtering"""
        intent = BMFFilterIntent(
            criteria=BMFFilterCriteria(
                states=["VA"],
                organization_name="child",  # Should match "Child Development Center"
                limit=10
            ),
            what_youre_looking_for="Organizations with 'child' in name"
        )

        result = await bmf_tool.execute(intent)

        assert result is not None
        assert len(result.organizations) == 1
        assert "child" in result.organizations[0].name.lower()

    @pytest.mark.asyncio
    async def test_stateless_behavior(self, bmf_tool):
        """Test that tool is stateless (Factor 6)"""
        intent = BMFFilterIntent(
            criteria=BMFFilterCriteria(
                states=["VA"],
                ntee_codes=["B25"],  # Health
                limit=5
            ),
            what_youre_looking_for="Health organizations for stateless test"
        )

        # Execute same intent twice
        result1 = await bmf_tool.execute(intent)
        result2 = await bmf_tool.execute(intent)

        # Results should be identical (same organizations)
        assert len(result1.organizations) == len(result2.organizations)
        eins1 = [org.ein for org in result1.organizations]
        eins2 = [org.ein for org in result2.organizations]
        assert eins1 == eins2

    @pytest.mark.asyncio
    async def test_structured_output(self, bmf_tool):
        """Test structured output compliance (Factor 4)"""
        intent = BMFFilterIntent(
            criteria=BMFFilterCriteria(
                states=["VA"],
                limit=3
            ),
            what_youre_looking_for="Test structured output"
        )

        result = await bmf_tool.execute(intent)

        # Verify structured output contains all required fields
        assert hasattr(result, 'organizations')
        assert hasattr(result, 'summary')
        assert hasattr(result, 'execution_metadata')
        assert hasattr(result, 'quality_assessment')

        # Verify summary structure
        assert hasattr(result.summary, 'total_found')
        assert hasattr(result.summary, 'criteria_summary')
        assert hasattr(result.summary, 'geographic_distribution')

        # Verify execution metadata
        assert hasattr(result.execution_metadata, 'execution_time_ms')
        assert hasattr(result.execution_metadata, 'cache_hit')
        assert hasattr(result.execution_metadata, 'query_complexity')

        # Verify organizations structure
        if result.organizations:
            org = result.organizations[0]
            assert hasattr(org, 'ein')
            assert hasattr(org, 'name')
            assert hasattr(org, 'state')
            assert hasattr(org, 'match_reasons')

    @pytest.mark.asyncio
    async def test_performance_metadata(self, bmf_tool):
        """Test that performance metadata is captured"""
        intent = BMFFilterIntent(
            criteria=BMFFilterCriteria(
                states=["VA"],
                limit=5
            ),
            what_youre_looking_for="Performance metadata test"
        )

        result = await bmf_tool.execute(intent)

        # Verify performance metadata
        assert result.execution_metadata.execution_time_ms > 0
        assert result.execution_metadata.database_query_time_ms >= 0
        assert result.execution_metadata.processing_time_ms >= 0
        assert result.execution_metadata.database_rows_scanned > 0

    @pytest.mark.asyncio
    async def test_sorting(self, bmf_tool):
        """Test sorting functionality"""
        intent = BMFFilterIntent(
            criteria=BMFFilterCriteria(
                states=["VA"],
                sort_by=BMFSortOption.revenue_desc,
                limit=5
            ),
            what_youre_looking_for="Test sorting by revenue"
        )

        result = await bmf_tool.execute(intent)

        # Verify sorting (revenues should be in descending order)
        revenues = [org.revenue for org in result.organizations if org.revenue]
        if len(revenues) > 1:
            assert revenues == sorted(revenues, reverse=True)

    @pytest.mark.asyncio
    async def test_config_from_environment(self, bmf_tool):
        """Test configuration from environment (Factor 3)"""
        # Tool should have loaded config from environment variables
        assert bmf_tool.input_path.endswith('.csv')
        assert bmf_tool.filter_config_path.endswith('.json')
        assert isinstance(bmf_tool.max_results, int)
        assert isinstance(bmf_tool.cache_enabled, bool)

        # Default NTEE codes should be loaded from config file
        assert isinstance(bmf_tool.default_ntee_codes, list)
        assert len(bmf_tool.default_ntee_codes) > 0

    @pytest.mark.asyncio
    async def test_error_handling(self, bmf_tool):
        """Test error handling for invalid inputs"""
        # Test with invalid state code
        intent = BMFFilterIntent(
            criteria=BMFFilterCriteria(
                states=["INVALID"],
                limit=5
            ),
            what_youre_looking_for="Test error handling"
        )

        with pytest.raises(ValueError):
            await bmf_tool.execute(intent)

        # Test with invalid revenue range
        intent = BMFFilterIntent(
            criteria=BMFFilterCriteria(
                revenue_min=1000000,
                revenue_max=500000,  # Max < Min
                limit=5
            ),
            what_youre_looking_for="Test invalid revenue range"
        )

        with pytest.raises(ValueError):
            await bmf_tool.execute(intent)

class TestTwelveFactorCompliance:
    """Test 12-Factor compliance specifically"""

    def test_factor_3_config_from_environment(self):
        """Factor 3: Config comes from environment"""
        # Set test environment variables
        test_env = {
            'BMF_INPUT_PATH': 'test_input.csv',
            'BMF_CACHE_ENABLED': 'false',
            'BMF_MAX_RESULTS': '500'
        }

        for key, value in test_env.items():
            os.environ[key] = value

        try:
            tool = BMFFilterTool()
            assert tool.input_path == 'test_input.csv'
            assert tool.cache_enabled == False
            assert tool.max_results == 500
        finally:
            for key in test_env.keys():
                os.environ.pop(key, None)

    @pytest.mark.asyncio
    async def test_factor_6_stateless_processes(self, sample_csv_data, temp_csv_file, temp_config_file):
        """Factor 6: Stateless processes"""
        os.environ['BMF_INPUT_PATH'] = temp_csv_file
        os.environ['BMF_FILTER_CONFIG_PATH'] = temp_config_file
        os.environ['BMF_CACHE_ENABLED'] = 'false'

        try:
            # Create two separate tool instances
            tool1 = BMFFilterTool()
            tool2 = BMFFilterTool()

            intent = BMFFilterIntent(
                criteria=BMFFilterCriteria(states=["VA"], limit=3),
                what_youre_looking_for="Stateless test"
            )

            # Both tools should produce identical results
            result1 = await tool1.execute(intent)
            result2 = await tool2.execute(intent)

            assert len(result1.organizations) == len(result2.organizations)

        finally:
            for key in ['BMF_INPUT_PATH', 'BMF_FILTER_CONFIG_PATH', 'BMF_CACHE_ENABLED']:
                os.environ.pop(key, None)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])