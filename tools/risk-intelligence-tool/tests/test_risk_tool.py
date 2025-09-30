"""
Tests for Risk Intelligence Tool
"""

import pytest
from tools.risk_intelligence_tool.app import (
    RiskIntelligenceTool,
    analyze_risk_intelligence,
    RiskIntelligenceInput,
    RiskLevel,
    RISK_INTELLIGENCE_COST
)


def test_tool_metadata():
    """Test tool metadata"""
    tool = RiskIntelligenceTool()
    assert tool.get_tool_name() == "Risk Intelligence Tool"
    assert tool.get_tool_version() == "1.0.0"
    assert "risk" in tool.get_single_responsibility().lower()


def test_cost_estimation():
    """Test cost estimation"""
    tool = RiskIntelligenceTool()
    assert tool.get_cost_estimate() == RISK_INTELLIGENCE_COST


@pytest.mark.asyncio
async def test_low_risk_opportunity():
    """Test opportunity with low overall risk"""
    tool = RiskIntelligenceTool()

    risk_input = RiskIntelligenceInput(
        opportunity_id="opp-lowrisk",
        opportunity_title="Low Risk Grant",
        opportunity_description="Well-matched grant opportunity",
        funder_name="Friendly Foundation",
        funder_type="foundation",
        organization_ein="12-3456789",
        organization_name="Strong Nonprofit",
        organization_mission="Education",
        grant_amount=250000,
        total_revenue=2000000,
        total_expenses=1800000,
        net_assets=1500000,
        program_expense_ratio=0.80,
        staff_count=20,
        has_grant_manager=True,
        prior_grants_with_funder=3,
        application_deadline="2026-06-30"
    )

    result = await tool.execute(risk_input=risk_input)

    assert result.is_success()
    intelligence = result.data

    # Should have low or medium risk
    assert intelligence.overall_risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.MINIMAL]
    assert intelligence.proceed_recommendation is True

    # Should have manageable risks
    assert len(intelligence.manageable_risks) >= 0

    # Should have mitigation strategies
    assert isinstance(intelligence.mitigation_strategies, list)


@pytest.mark.asyncio
async def test_high_risk_opportunity():
    """Test opportunity with high overall risk"""
    tool = RiskIntelligenceTool()

    risk_input = RiskIntelligenceInput(
        opportunity_id="opp-highrisk",
        opportunity_title="High Risk Grant",
        opportunity_description="Challenging grant opportunity",
        funder_name="Competitive Foundation",
        funder_type="government",
        organization_ein="98-7654321",
        organization_name="Small Nonprofit",
        organization_mission="Community Development",
        grant_amount=1000000,  # Large relative to revenue
        total_revenue=500000,
        total_expenses=520000,  # Deficit
        net_assets=50000,
        program_expense_ratio=0.60,
        staff_count=3,  # Small staff
        has_grant_manager=False,  # No grant manager
        prior_grants_with_funder=0,  # No prior relationship
        match_required=True,
        match_percentage=50,  # High match
        application_deadline="2025-11-15"  # Tight timeline
    )

    result = await tool.execute(risk_input=risk_input)

    assert result.is_success()
    intelligence = result.data

    # Should identify multiple risks
    assert len(intelligence.all_risk_factors) > 0

    # Should have capacity concerns
    assert not intelligence.capacity_assessment.staff_capacity_adequate
    assert not intelligence.capacity_assessment.management_capacity_adequate

    # Financial concerns
    assert len(intelligence.financial_assessment.budget_concerns) > 0


@pytest.mark.asyncio
async def test_eligibility_assessment():
    """Test eligibility risk assessment"""
    tool = RiskIntelligenceTool()

    risk_input = RiskIntelligenceInput(
        opportunity_id="opp-elig",
        opportunity_title="Eligibility Test",
        opportunity_description="Test eligibility",
        funder_name="Foundation",
        funder_type="foundation",
        organization_ein="12-3456789",
        organization_name="Nonprofit",
        organization_mission="Test",
        grant_amount=100000,
        total_revenue=1000000
    )

    result = await tool.execute(risk_input=risk_input)

    assert result.is_success()
    intelligence = result.data

    # Should have eligibility assessment
    assert intelligence.eligibility_assessment is not None
    assert 0 <= intelligence.eligibility_assessment.overall_eligibility_score <= 1
    assert intelligence.eligibility_assessment.risk_level is not None


@pytest.mark.asyncio
async def test_competition_assessment():
    """Test competition risk assessment"""
    tool = RiskIntelligenceTool()

    risk_input = RiskIntelligenceInput(
        opportunity_id="opp-comp",
        opportunity_title="Competition Test",
        opportunity_description="Test competition",
        funder_name="Foundation",
        funder_type="government",  # Higher competition
        organization_ein="12-3456789",
        organization_name="Nonprofit",
        organization_mission="Test",
        prior_grants_with_funder=0  # No relationship
    )

    result = await tool.execute(risk_input=risk_input)

    assert result.is_success()
    intelligence = result.data

    # Should assess competition
    assert intelligence.competition_assessment is not None
    assert intelligence.competition_assessment.competition_level is not None
    assert 0 <= intelligence.competition_assessment.estimated_success_probability <= 1


@pytest.mark.asyncio
async def test_mitigation_strategies():
    """Test mitigation strategy generation"""
    tool = RiskIntelligenceTool()

    risk_input = RiskIntelligenceInput(
        opportunity_id="opp-mitigate",
        opportunity_title="Mitigation Test",
        opportunity_description="Test mitigation",
        funder_name="Foundation",
        funder_type="foundation",
        organization_ein="12-3456789",
        organization_name="Nonprofit",
        organization_mission="Test",
        has_grant_manager=False,  # Creates capacity risk
        staff_count=2  # Small staff
    )

    result = await tool.execute(risk_input=risk_input)

    assert result.is_success()
    intelligence = result.data

    # Should generate mitigation strategies
    if len(intelligence.all_risk_factors) > 0:
        assert len(intelligence.mitigation_strategies) > 0


def test_input_validation():
    """Test input validation"""
    tool = RiskIntelligenceTool()

    # Missing risk_input
    is_valid, error = tool.validate_inputs()
    assert not is_valid
    assert "risk_input is required" in error

    # Valid input
    risk_input = RiskIntelligenceInput(
        opportunity_id="test",
        opportunity_title="Test",
        opportunity_description="Test",
        funder_name="Test",
        funder_type="foundation",
        organization_ein="12-3456789",
        organization_name="Test",
        organization_mission="Test"
    )

    is_valid, error = tool.validate_inputs(risk_input=risk_input)
    assert is_valid
    assert error is None


@pytest.mark.asyncio
async def test_convenience_function():
    """Test convenience analyze_risk_intelligence function"""
    result = await analyze_risk_intelligence(
        opportunity_id="opp-convenience",
        opportunity_title="Convenience Test",
        opportunity_description="Testing convenience function",
        funder_name="Foundation",
        funder_type="foundation",
        organization_ein="12-3456789",
        organization_name="Nonprofit",
        organization_mission="Test"
    )

    assert result.is_success()
    assert result.data.api_cost_usd == RISK_INTELLIGENCE_COST


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
