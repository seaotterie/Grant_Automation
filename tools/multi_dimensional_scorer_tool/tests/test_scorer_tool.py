"""
Tests for Multi-Dimensional Scorer Tool
"""

import pytest
from app.scorer_tool import (
    MultiDimensionalScorerTool,
    score_opportunity,
    MULTI_DIMENSIONAL_SCORER_COST,
)
from app.scorer_models import (
    ScoringInput,
    WorkflowStage,
    TrackType,
    EnhancedData,
    STAGE_WEIGHTS,
    FOUNDATION_WEIGHTS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def basic_opportunity():
    return {
        "title": "Community Education Grant",
        "description": "Federal funding for community-based education programs",
        "funder_name": "Department of Education",
        "funding_amount": 250_000,
        "application_deadline": "2026-06-30",
        "focus_areas": ["education", "community"],
        "geographic_scope": "National",
        "eligibility_types": ["Nonprofit 501(c)(3)"],
        "agency_code": "ED",
    }


@pytest.fixture
def basic_organization():
    return {
        "organization_name": "Education First Nonprofit",
        "ein": "12-3456789",
        "mission": "Supporting education in underserved communities",
        "ntee_codes": ["B25"],
        "revenue": 2_000_000,
        "assets": 1_500_000,
        "state": "VA",
        "years_active": 10,
        "focus_areas": ["education", "youth development"],
    }


# ---------------------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------------------

def test_tool_metadata():
    tool = MultiDimensionalScorerTool()
    assert tool.get_tool_name() == "Multi-Dimensional Scorer Tool"
    assert tool.get_tool_version() == "1.0.0"
    assert "scor" in tool.get_single_responsibility().lower()


def test_cost_is_zero():
    tool = MultiDimensionalScorerTool()
    assert tool.get_cost_estimate() == MULTI_DIMENSIONAL_SCORER_COST
    assert MULTI_DIMENSIONAL_SCORER_COST == 0.0


# ---------------------------------------------------------------------------
# Scoring across all workflow stages
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("stage", [s.value for s in WorkflowStage])
async def test_score_all_stages(stage, basic_opportunity, basic_organization):
    result = await score_opportunity(
        opportunity_data=basic_opportunity,
        organization_profile=basic_organization,
        workflow_stage=stage,
    )
    assert result.is_success(), f"Failed for stage {stage}: {result.errors}"
    score = result.data
    assert 0.0 <= score.overall_score <= 1.0
    assert 0.0 <= score.confidence <= 1.0
    assert score.stage == stage
    assert len(score.dimensional_scores) == 5


@pytest.mark.asyncio
async def test_discover_stage_returns_expected_dimensions(basic_opportunity, basic_organization):
    result = await score_opportunity(
        opportunity_data=basic_opportunity,
        organization_profile=basic_organization,
        workflow_stage="discover",
    )
    assert result.is_success()
    dimension_names = {ds.dimension for ds in result.data.dimensional_scores}
    expected = set(STAGE_WEIGHTS["discover"].keys())
    assert dimension_names == expected


@pytest.mark.asyncio
async def test_foundation_track(basic_opportunity, basic_organization):
    result = await score_opportunity(
        opportunity_data=basic_opportunity,
        organization_profile=basic_organization,
        workflow_stage="discover",
        track_type="foundation",
    )
    assert result.is_success()
    assert result.data.track_type == "foundation"
    dimension_names = {ds.dimension for ds in result.data.dimensional_scores}
    expected = set(FOUNDATION_WEIGHTS.keys())
    assert dimension_names == expected


# ---------------------------------------------------------------------------
# Boost factors
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enhanced_data_boosts_score(basic_opportunity, basic_organization):
    base = await score_opportunity(
        opportunity_data=basic_opportunity,
        organization_profile=basic_organization,
        workflow_stage="analyze",
    )
    boosted = await score_opportunity(
        opportunity_data=basic_opportunity,
        organization_profile=basic_organization,
        workflow_stage="analyze",
        enhanced_data={
            "has_financial_data": True,
            "has_network_data": True,
            "has_historical_data": True,
            "has_risk_data": False,
        },
    )
    assert base.is_success()
    assert boosted.is_success()
    # Boosted score should be >= base score (boosts only add)
    assert boosted.data.overall_score >= base.data.overall_score
    assert len(boosted.data.boost_factors_applied) > 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_minimal_opportunity_data():
    """Tool should not crash on sparse data."""
    result = await score_opportunity(
        opportunity_data={"title": "Sparse Grant"},
        organization_profile={"organization_name": "Minimal Org"},
        workflow_stage="discover",
    )
    assert result.is_success()
    assert 0.0 <= result.data.overall_score <= 1.0


@pytest.mark.asyncio
async def test_invalid_stage_raises():
    with pytest.raises(ValueError):
        await score_opportunity(
            opportunity_data={},
            organization_profile={},
            workflow_stage="invalid_stage",
        )


@pytest.mark.asyncio
async def test_metadata_populated(basic_opportunity, basic_organization):
    result = await score_opportunity(
        opportunity_data=basic_opportunity,
        organization_profile=basic_organization,
        workflow_stage="plan",
    )
    assert result.is_success()
    meta = result.data.metadata
    assert meta.execution_time_ms >= 0
    assert meta.tool_version == "1.0.0"
