"""
Tests for Opportunity Screening Tool
"""

import pytest
import asyncio
from tools.opportunity_screening_tool.app import (
    OpportunityScreeningTool,
    screen_opportunities,
    ScreeningMode,
    ScreeningInput,
    Opportunity,
    OrganizationProfile
)


def test_tool_metadata():
    """Test tool metadata"""
    tool = OpportunityScreeningTool()

    assert tool.get_tool_name() == "Opportunity Screening Tool"
    assert tool.get_tool_version() == "1.0.0"
    assert "screening" in tool.get_single_responsibility().lower()


def test_cost_estimation():
    """Test cost estimation"""
    tool = OpportunityScreeningTool()

    # Fast mode cost
    fast_cost = tool.get_cost_estimate(opportunity_count=200, mode="fast")
    assert fast_cost == pytest.approx(0.08, abs=0.01)

    # Thorough mode cost
    thorough_cost = tool.get_cost_estimate(opportunity_count=200, mode="thorough")
    assert thorough_cost == pytest.approx(4.0, abs=0.1)


@pytest.mark.asyncio
async def test_fast_screening():
    """Test fast screening mode"""
    tool = OpportunityScreeningTool()

    # Create test data
    organization = OrganizationProfile(
        ein="12-3456789",
        name="Test Nonprofit",
        mission="Education and youth development",
        ntee_codes=["B25"],
        geographic_focus=["Virginia"],
        program_areas=["Education"]
    )

    opportunities = [
        Opportunity(
            opportunity_id="opp-001",
            title="Education Innovation Grant",
            funder="Smith Foundation",
            funder_type="foundation",
            description="Supporting innovative education programs",
            amount_min=50000,
            amount_max=150000,
            focus_areas=["Education"]
        ),
        Opportunity(
            opportunity_id="opp-002",
            title="Healthcare Research Grant",
            funder="Health Foundation",
            funder_type="foundation",
            description="Supporting healthcare research",
            amount_min=100000,
            amount_max=200000,
            focus_areas=["Healthcare"]
        )
    ]

    screening_input = ScreeningInput(
        opportunities=opportunities,
        organization_profile=organization,
        screening_mode=ScreeningMode.FAST,
        minimum_threshold=0.50,
        max_recommendations=10
    )

    # Execute screening
    result = await tool.execute(screening_input=screening_input)

    # Verify result
    assert result.is_success()
    assert result.data is not None

    output = result.data
    assert output.total_screened == 2
    assert len(output.opportunity_scores) == 2
    assert output.screening_mode == "fast"
    assert output.total_cost_usd == pytest.approx(0.0008, abs=0.0001)


@pytest.mark.asyncio
async def test_thorough_screening():
    """Test thorough screening mode"""
    tool = OpportunityScreeningTool()

    organization = OrganizationProfile(
        ein="12-3456789",
        name="Test Nonprofit",
        mission="Education",
        ntee_codes=["B25"],
        geographic_focus=["Virginia"],
        program_areas=["Education"]
    )

    opportunities = [
        Opportunity(
            opportunity_id="opp-001",
            title="Test Grant",
            funder="Test Foundation",
            funder_type="foundation",
            description="Test description",
            focus_areas=["Education"]
        )
    ]

    screening_input = ScreeningInput(
        opportunities=opportunities,
        organization_profile=organization,
        screening_mode=ScreeningMode.THOROUGH,
        minimum_threshold=0.55
    )

    result = await tool.execute(screening_input=screening_input)

    assert result.is_success()
    output = result.data
    assert output.total_screened == 1
    assert output.screening_mode == "thorough"


def test_screening_output_structure():
    """Test that screening output has all required fields"""
    from tools.opportunity_screening_tool.app.screening_models import (
        ScreeningOutput,
        OpportunityScore
    )

    score = OpportunityScore(
        opportunity_id="test",
        opportunity_title="Test Opportunity",
        overall_score=0.75,
        proceed_to_deep_analysis=True,
        confidence_level="high",
        strategic_fit_score=0.8,
        eligibility_score=0.9,
        timing_score=0.7,
        financial_score=0.6,
        competition_score=0.5,
        one_sentence_summary="Test summary",
        analysis_depth="fast"
    )

    assert score.opportunity_id == "test"
    assert score.overall_score == 0.75
    assert score.proceed_to_deep_analysis is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
