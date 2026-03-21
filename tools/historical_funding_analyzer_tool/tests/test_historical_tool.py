"""
Tests for Historical Funding Analyzer Tool
"""

import pytest
from app.historical_tool import (
    HistoricalFundingAnalyzerTool,
    analyze_historical_funding,
    HISTORICAL_FUNDING_ANALYZER_COST,
)
from app.historical_models import HistoricalAnalysisInput


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_awards():
    """Realistic USASpending-style award records."""
    return [
        {
            "award_id": "ED-2022-001",
            "amount": 250_000,
            "year": 2022,
            "awarding_agency": "Department of Education",
            "recipient_state": "VA",
            "description": "Community literacy program",
            "category": "Education",
        },
        {
            "award_id": "ED-2023-001",
            "amount": 300_000,
            "year": 2023,
            "awarding_agency": "Department of Education",
            "recipient_state": "VA",
            "description": "STEM support grant",
            "category": "Education",
        },
        {
            "award_id": "HHS-2023-001",
            "amount": 150_000,
            "year": 2023,
            "awarding_agency": "HHS",
            "recipient_state": "MD",
            "description": "Youth health initiative",
            "category": "Health",
        },
        {
            "award_id": "ED-2024-001",
            "amount": 400_000,
            "year": 2024,
            "awarding_agency": "Department of Education",
            "recipient_state": "VA",
            "description": "Digital learning expansion",
            "category": "Education",
        },
    ]


# ---------------------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------------------

def test_tool_metadata():
    tool = HistoricalFundingAnalyzerTool()
    assert tool.get_tool_name() == "Historical Funding Analyzer Tool"
    assert tool.get_tool_version() == "1.0.0"
    assert "historical" in tool.get_single_responsibility().lower()


def test_cost_is_zero():
    assert HISTORICAL_FUNDING_ANALYZER_COST == 0.0
    assert HistoricalFundingAnalyzerTool().get_cost_estimate() == 0.0


# ---------------------------------------------------------------------------
# Core analysis tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_basic_analysis(sample_awards):
    result = await analyze_historical_funding(
        organization_ein="12-3456789",
        historical_data=sample_awards,
    )
    assert result.is_success(), f"Analysis failed: {result.errors}"
    analysis = result.data

    assert analysis.organization_ein == "12-3456789"
    assert analysis.total_awards == 4
    assert analysis.total_funding == 1_100_000
    assert analysis.average_award_size == pytest.approx(275_000)
    assert analysis.years_analyzed >= 1


@pytest.mark.asyncio
async def test_geographic_distribution(sample_awards):
    result = await analyze_historical_funding(
        organization_ein="12-3456789",
        historical_data=sample_awards,
        include_geographic=True,
    )
    assert result.is_success()
    geo = result.data.geographic_distribution
    assert len(geo) > 0
    states = {g.state for g in geo}
    assert "VA" in states


@pytest.mark.asyncio
async def test_geographic_disabled(sample_awards):
    result = await analyze_historical_funding(
        organization_ein="12-3456789",
        historical_data=sample_awards,
        include_geographic=False,
    )
    assert result.is_success()
    assert result.data.geographic_distribution == []


@pytest.mark.asyncio
async def test_temporal_trends(sample_awards):
    result = await analyze_historical_funding(
        organization_ein="12-3456789",
        historical_data=sample_awards,
        include_temporal=True,
    )
    assert result.is_success()
    # Multi-year data should produce temporal trend entries
    assert len(result.data.temporal_trends) > 0


@pytest.mark.asyncio
async def test_funding_patterns(sample_awards):
    result = await analyze_historical_funding(
        organization_ein="12-3456789",
        historical_data=sample_awards,
        include_patterns=True,
    )
    assert result.is_success()
    assert len(result.data.funding_patterns) > 0


@pytest.mark.asyncio
async def test_competitive_insights(sample_awards):
    result = await analyze_historical_funding(
        organization_ein="12-3456789",
        historical_data=sample_awards,
        include_competitive=True,
    )
    assert result.is_success()
    # Should compute competitive position
    assert len(result.data.competitive_insights) > 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_empty_historical_data():
    result = await analyze_historical_funding(
        organization_ein="99-9999999",
        historical_data=[],
    )
    assert result.is_success()
    assert result.data.total_awards == 0
    assert result.data.total_funding == 0.0


@pytest.mark.asyncio
async def test_single_award():
    result = await analyze_historical_funding(
        organization_ein="11-1111111",
        historical_data=[{"amount": 100_000, "year": 2024, "recipient_state": "TX"}],
    )
    assert result.is_success()
    assert result.data.total_awards == 1
    assert result.data.average_award_size == 100_000


@pytest.mark.asyncio
async def test_metadata_populated(sample_awards):
    result = await analyze_historical_funding(
        organization_ein="12-3456789",
        historical_data=sample_awards,
    )
    assert result.is_success()
    meta = result.data.metadata
    assert meta.tool_version == "1.0.0"
    assert meta.execution_time_ms >= 0
