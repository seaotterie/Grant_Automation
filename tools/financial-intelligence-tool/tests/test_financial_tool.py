"""
Tests for Financial Intelligence Tool
"""

import pytest
import asyncio
from app import (
    FinancialIntelligenceTool,
    analyze_financial_intelligence,
    FinancialIntelligenceInput,
    FinancialHealthRating,
    FINANCIAL_INTELLIGENCE_COST
)


def test_tool_metadata():
    """Test tool metadata"""
    tool = FinancialIntelligenceTool()

    assert tool.get_tool_name() == "Financial Intelligence Tool"
    assert tool.get_tool_version() == "1.0.0"
    assert "financial" in tool.get_single_responsibility().lower()


def test_cost_estimation():
    """Test cost estimation"""
    tool = FinancialIntelligenceTool()
    assert tool.get_cost_estimate() == FINANCIAL_INTELLIGENCE_COST


@pytest.mark.asyncio
async def test_excellent_health_organization():
    """Test organization with excellent financial health"""
    tool = FinancialIntelligenceTool()

    financial_input = FinancialIntelligenceInput(
        organization_ein="12-3456789",
        organization_name="Excellent Nonprofit",
        total_revenue=2000000,
        total_expenses=1800000,
        total_assets=3000000,
        total_liabilities=500000,
        net_assets=2500000,
        contributions_grants=800000,
        program_service_revenue=900000,
        investment_income=200000,
        other_revenue=100000,
        program_expenses=1500000,  # 83% program ratio
        admin_expenses=200000,
        fundraising_expenses=100000,
        prior_year_revenue=1900000,
        prior_year_expenses=1750000,
        prior_year_net_assets=2400000,
        organization_mission="Education and youth development",
        ntee_code="B25",
        years_of_operation=15
    )

    result = await tool.execute(financial_input=financial_input)

    assert result.is_success()
    assert result.data is not None

    intelligence = result.data

    # Should have excellent or good rating
    assert intelligence.overall_health_rating in [FinancialHealthRating.EXCELLENT, FinancialHealthRating.GOOD]
    assert intelligence.overall_health_score >= 0.65

    # Should have high program expense ratio
    assert intelligence.metrics.program_expense_ratio >= 0.75

    # Should have good liquidity
    assert intelligence.metrics.months_of_expenses >= 6

    # Should identify strengths
    assert len(intelligence.strengths) > 0

    # Grant capacity should be substantial
    assert intelligence.grant_capacity.can_handle_budget > 500000
    assert intelligence.grant_capacity.budget_capacity_score > 0.7


@pytest.mark.asyncio
async def test_concerning_health_organization():
    """Test organization with concerning financial health"""
    tool = FinancialIntelligenceTool()

    financial_input = FinancialIntelligenceInput(
        organization_ein="98-7654321",
        organization_name="Struggling Nonprofit",
        total_revenue=500000,
        total_expenses=520000,  # Deficit
        total_assets=150000,
        total_liabilities=100000,
        net_assets=50000,
        contributions_grants=450000,  # 90% concentration
        program_service_revenue=40000,
        investment_income=5000,
        other_revenue=5000,
        program_expenses=300000,  # Only 58% program ratio
        admin_expenses=150000,
        fundraising_expenses=70000,
        prior_year_revenue=550000,  # Declining revenue
        prior_year_expenses=500000,
        prior_year_net_assets=70000  # Declining net assets
    )

    result = await tool.execute(financial_input=financial_input)

    assert result.is_success()
    intelligence = result.data

    # Should have concerning or critical rating
    assert intelligence.overall_health_rating in [
        FinancialHealthRating.CONCERNING,
        FinancialHealthRating.CRITICAL,
        FinancialHealthRating.FAIR
    ]

    # Should identify multiple concerns
    assert len(intelligence.concerns) >= 2

    # Should have low months of expenses
    assert intelligence.metrics.months_of_expenses < 3

    # Should have high revenue concentration
    assert intelligence.metrics.revenue_concentration_score > 0.6

    # Grant capacity should be limited
    assert intelligence.grant_capacity.budget_capacity_score < 0.7


@pytest.mark.asyncio
async def test_trend_analysis_with_historical_data():
    """Test trend analysis when historical data provided"""
    tool = FinancialIntelligenceTool()

    financial_input = FinancialIntelligenceInput(
        organization_ein="12-3456789",
        organization_name="Growing Nonprofit",
        total_revenue=1500000,
        total_expenses=1300000,
        total_assets=2000000,
        total_liabilities=500000,
        net_assets=1500000,
        contributions_grants=800000,
        program_service_revenue=600000,
        investment_income=80000,
        other_revenue=20000,
        program_expenses=1000000,
        admin_expenses=200000,
        fundraising_expenses=100000,
        # Historical data showing growth
        prior_year_revenue=1300000,
        prior_year_expenses=1200000,
        prior_year_net_assets=1400000
    )

    result = await tool.execute(financial_input=financial_input)

    assert result.is_success()
    intelligence = result.data

    # Should have trend analysis
    assert len(intelligence.trends) > 0

    # Should identify revenue growth
    revenue_trend = next((t for t in intelligence.trends if t.metric_name == "Total Revenue"), None)
    assert revenue_trend is not None
    assert revenue_trend.percentage_change > 0  # Growing


@pytest.mark.asyncio
async def test_trend_analysis_without_historical_data():
    """Test that tool works without historical data"""
    tool = FinancialIntelligenceTool()

    financial_input = FinancialIntelligenceInput(
        organization_ein="12-3456789",
        organization_name="New Nonprofit",
        total_revenue=500000,
        total_expenses=450000,
        total_assets=300000,
        total_liabilities=50000,
        net_assets=250000,
        contributions_grants=300000,
        program_service_revenue=200000,
        investment_income=0,
        other_revenue=0,
        program_expenses=350000,
        admin_expenses=70000,
        fundraising_expenses=30000
    )

    result = await tool.execute(financial_input=financial_input)

    assert result.is_success()
    intelligence = result.data

    # Should have no trends (no historical data)
    assert len(intelligence.trends) == 0

    # But should still have other analysis
    assert intelligence.metrics is not None
    assert intelligence.overall_health_rating is not None


@pytest.mark.asyncio
async def test_grant_capacity_assessment():
    """Test grant capacity assessment logic"""
    tool = FinancialIntelligenceTool()

    financial_input = FinancialIntelligenceInput(
        organization_ein="12-3456789",
        organization_name="Capacity Test Nonprofit",
        total_revenue=1000000,
        total_expenses=900000,
        total_assets=1500000,
        total_liabilities=300000,
        net_assets=1200000,
        contributions_grants=400000,
        program_service_revenue=500000,
        investment_income=80000,
        other_revenue=20000,
        program_expenses=700000,
        admin_expenses=150000,
        fundraising_expenses=50000
    )

    result = await tool.execute(financial_input=financial_input)

    assert result.is_success()
    intelligence = result.data

    # Should assess grant capacity
    assert intelligence.grant_capacity is not None
    assert intelligence.grant_capacity.can_handle_budget > 0
    assert 0 <= intelligence.grant_capacity.budget_capacity_score <= 1
    assert 0 <= intelligence.grant_capacity.sustainability_score <= 1

    # Should identify match sources if diversified
    if intelligence.metrics.revenue_concentration_score < 0.7:
        assert len(intelligence.grant_capacity.match_source_suggestions) > 0


@pytest.mark.asyncio
async def test_ai_insights_generation():
    """Test AI insights generation"""
    tool = FinancialIntelligenceTool()

    financial_input = FinancialIntelligenceInput(
        organization_ein="12-3456789",
        organization_name="Test Nonprofit",
        total_revenue=1000000,
        total_expenses=900000,
        total_assets=1500000,
        total_liabilities=300000,
        net_assets=1200000,
        contributions_grants=500000,
        program_service_revenue=400000,
        investment_income=80000,
        other_revenue=20000,
        program_expenses=700000,
        admin_expenses=150000,
        fundraising_expenses=50000,
        organization_mission="Education and youth development"
    )

    result = await tool.execute(financial_input=financial_input)

    assert result.is_success()
    intelligence = result.data

    # Should have AI insights
    assert intelligence.ai_insights is not None
    assert len(intelligence.ai_insights.executive_summary) > 50
    assert len(intelligence.ai_insights.strategic_opportunities) > 0
    assert len(intelligence.ai_insights.financial_management_recommendations) > 0
    assert len(intelligence.ai_insights.grant_strategy_recommendations) > 0


def test_input_validation():
    """Test input validation"""
    tool = FinancialIntelligenceTool()

    # Missing financial_input
    is_valid, error = tool.validate_inputs()
    assert not is_valid
    assert "financial_input is required" in error

    # Invalid type
    is_valid, error = tool.validate_inputs(financial_input="not a valid input")
    assert not is_valid
    assert "must be FinancialIntelligenceInput instance" in error

    # Valid input
    financial_input = FinancialIntelligenceInput(
        organization_ein="12-3456789",
        organization_name="Test",
        total_revenue=1000000,
        total_expenses=900000,
        total_assets=1500000,
        total_liabilities=300000,
        net_assets=1200000,
        contributions_grants=500000,
        program_service_revenue=400000,
        investment_income=80000,
        other_revenue=20000,
        program_expenses=700000,
        admin_expenses=150000,
        fundraising_expenses=50000
    )

    is_valid, error = tool.validate_inputs(financial_input=financial_input)
    assert is_valid
    assert error is None


@pytest.mark.asyncio
async def test_convenience_function():
    """Test convenience analyze_financial_intelligence function"""
    result = await analyze_financial_intelligence(
        organization_ein="12-3456789",
        organization_name="Convenience Test",
        total_revenue=1000000,
        total_expenses=900000,
        total_assets=1500000,
        total_liabilities=300000,
        net_assets=1200000,
        contributions_grants=500000,
        program_service_revenue=400000,
        investment_income=80000,
        other_revenue=20000,
        program_expenses=700000,
        admin_expenses=150000,
        fundraising_expenses=50000
    )

    assert result.is_success()
    assert result.data.organization_ein == "12-3456789"
    assert result.data.api_cost_usd == FINANCIAL_INTELLIGENCE_COST


def test_financial_metrics_calculations():
    """Test accuracy of financial metrics calculations"""
    tool = FinancialIntelligenceTool()

    financial_input = FinancialIntelligenceInput(
        organization_ein="12-3456789",
        organization_name="Metrics Test",
        total_revenue=1000000,
        total_expenses=900000,
        total_assets=1500000,
        total_liabilities=300000,
        net_assets=1200000,
        contributions_grants=500000,
        program_service_revenue=400000,
        investment_income=80000,
        other_revenue=20000,
        program_expenses=720000,  # 80% of expenses
        admin_expenses=135000,    # 15% of expenses
        fundraising_expenses=45000  # 5% of expenses
    )

    metrics = tool._calculate_metrics(financial_input)

    # Test liquidity metrics
    assert metrics.current_ratio == pytest.approx(1500000 / 300000, rel=0.01)
    assert metrics.months_of_expenses == pytest.approx((1200000 / (900000 / 12)), rel=0.01)

    # Test efficiency metrics
    assert metrics.program_expense_ratio == pytest.approx(0.80, rel=0.01)
    assert metrics.admin_expense_ratio == pytest.approx(0.15, rel=0.01)
    assert metrics.fundraising_expense_ratio == pytest.approx(0.05, rel=0.01)

    # Test sustainability metrics
    assert metrics.operating_margin == pytest.approx(0.10, rel=0.01)

    # Test capacity metrics
    assert metrics.asset_to_revenue_ratio == pytest.approx(1.5, rel=0.01)
    assert metrics.debt_to_asset_ratio == pytest.approx(0.2, rel=0.01)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
