"""
Tests for Deep Intelligence Tool
"""

import pytest
import asyncio
from tools.deep_intelligence_tool.app import (
    DeepIntelligenceTool,
    analyze_opportunity,
    DeepIntelligenceInput,
    AnalysisDepth,
    DEPTH_FEATURES
)


def test_tool_metadata():
    """Test tool metadata"""
    tool = DeepIntelligenceTool()

    assert tool.get_tool_name() == "Deep Intelligence Tool"
    assert tool.get_tool_version() == "1.0.0"
    assert "intelligence" in tool.get_single_responsibility().lower()


def test_cost_estimation():
    """Test cost estimation for each depth"""
    tool = DeepIntelligenceTool()

    assert tool.get_cost_estimate("quick") == 0.75
    assert tool.get_cost_estimate("standard") == 7.50
    assert tool.get_cost_estimate("enhanced") == 22.00
    assert tool.get_cost_estimate("complete") == 42.00


def test_depth_features():
    """Test depth features configuration"""
    quick_features = DEPTH_FEATURES[AnalysisDepth.QUICK]
    assert quick_features["cost"] == 0.75
    assert "strategic_fit" in quick_features["features"]

    complete_features = DEPTH_FEATURES[AnalysisDepth.COMPLETE]
    assert complete_features["cost"] == 42.00
    assert "policy_analysis" in complete_features["features"]
    assert "strategic_consulting" in complete_features["features"]


@pytest.mark.asyncio
async def test_quick_depth_analysis():
    """Test quick depth analysis"""
    tool = DeepIntelligenceTool()

    intelligence_input = DeepIntelligenceInput(
        opportunity_id="opp-test-001",
        opportunity_title="Test Grant",
        opportunity_description="Test grant for education programs",
        funder_name="Test Foundation",
        funder_type="foundation",
        organization_ein="12-3456789",
        organization_name="Test Nonprofit",
        organization_mission="Education and youth development",
        depth=AnalysisDepth.QUICK,
        screening_score=0.85
    )

    result = await tool.execute(intelligence_input=intelligence_input)

    assert result.is_success()
    assert result.data is not None

    intelligence = result.data
    assert intelligence.depth_executed == "quick"
    assert intelligence.api_cost_usd == 0.75
    assert 0.0 <= intelligence.overall_score <= 1.0
    assert isinstance(intelligence.proceed_recommendation, bool)

    # Core analyses present
    assert intelligence.strategic_fit is not None
    assert intelligence.financial_viability is not None
    assert intelligence.operational_readiness is not None
    assert intelligence.risk_assessment is not None

    # Enhanced features NOT present in quick depth
    assert intelligence.historical_intelligence is None
    assert intelligence.geographic_analysis is None
    assert intelligence.network_intelligence is None
    assert intelligence.policy_analysis is None


@pytest.mark.asyncio
async def test_standard_depth_analysis():
    """Test standard depth analysis"""
    tool = DeepIntelligenceTool()

    intelligence_input = DeepIntelligenceInput(
        opportunity_id="opp-test-002",
        opportunity_title="Standard Depth Test",
        opportunity_description="Testing standard depth features",
        funder_name="Test Foundation",
        funder_type="foundation",
        organization_ein="12-3456789",
        organization_name="Test Nonprofit",
        organization_mission="Community development",
        depth=AnalysisDepth.STANDARD
    )

    result = await tool.execute(intelligence_input=intelligence_input)

    assert result.is_success()
    intelligence = result.data

    assert intelligence.depth_executed == "standard"
    assert intelligence.api_cost_usd == 7.50

    # Core analyses present
    assert intelligence.strategic_fit is not None
    assert intelligence.financial_viability is not None

    # Enhanced features present in standard
    assert intelligence.historical_intelligence is not None
    assert intelligence.geographic_analysis is not None

    # Advanced features NOT present in standard
    assert intelligence.network_intelligence is None
    assert intelligence.policy_analysis is None


@pytest.mark.asyncio
async def test_enhanced_depth_analysis():
    """Test enhanced depth analysis"""
    tool = DeepIntelligenceTool()

    intelligence_input = DeepIntelligenceInput(
        opportunity_id="opp-test-003",
        opportunity_title="Enhanced Depth Test",
        opportunity_description="Testing enhanced depth features",
        funder_name="Test Foundation",
        funder_type="foundation",
        organization_ein="12-3456789",
        organization_name="Test Nonprofit",
        organization_mission="Healthcare access",
        depth=AnalysisDepth.ENHANCED
    )

    result = await tool.execute(intelligence_input=intelligence_input)

    assert result.is_success()
    intelligence = result.data

    assert intelligence.depth_executed == "enhanced"
    assert intelligence.api_cost_usd == 22.00

    # All enhanced features present
    assert intelligence.historical_intelligence is not None
    assert intelligence.geographic_analysis is not None
    assert intelligence.network_intelligence is not None
    assert intelligence.relationship_mapping is not None

    # Premium features NOT present in enhanced
    assert intelligence.policy_analysis is None
    assert intelligence.strategic_consulting is None


@pytest.mark.asyncio
async def test_complete_depth_analysis():
    """Test complete depth analysis"""
    tool = DeepIntelligenceTool()

    intelligence_input = DeepIntelligenceInput(
        opportunity_id="opp-test-004",
        opportunity_title="Complete Depth Test",
        opportunity_description="Testing complete depth features",
        funder_name="Test Foundation",
        funder_type="foundation",
        organization_ein="12-3456789",
        organization_name="Test Nonprofit",
        organization_mission="Environmental sustainability",
        depth=AnalysisDepth.COMPLETE
    )

    result = await tool.execute(intelligence_input=intelligence_input)

    assert result.is_success()
    intelligence = result.data

    assert intelligence.depth_executed == "complete"
    assert intelligence.api_cost_usd == 42.00

    # All features present
    assert intelligence.historical_intelligence is not None
    assert intelligence.network_intelligence is not None
    assert intelligence.policy_analysis is not None
    assert intelligence.strategic_consulting is not None

    # Strategic consulting has action plans
    consulting = intelligence.strategic_consulting
    assert len(consulting.immediate_actions) > 0
    assert len(consulting.medium_term_actions) > 0
    assert len(consulting.long_term_actions) > 0


def test_input_validation():
    """Test input validation"""
    tool = DeepIntelligenceTool()

    # Missing intelligence_input
    is_valid, error = tool.validate_inputs()
    assert not is_valid
    assert "intelligence_input is required" in error

    # Valid input
    intelligence_input = DeepIntelligenceInput(
        opportunity_id="test",
        opportunity_title="Test",
        opportunity_description="Test",
        funder_name="Test",
        funder_type="foundation",
        organization_ein="12-3456789",
        organization_name="Test",
        organization_mission="Test",
        depth=AnalysisDepth.QUICK
    )

    is_valid, error = tool.validate_inputs(intelligence_input=intelligence_input)
    assert is_valid
    assert error is None


@pytest.mark.asyncio
async def test_convenience_function():
    """Test convenience analyze_opportunity function"""
    result = await analyze_opportunity(
        opportunity_id="opp-convenience-test",
        opportunity_title="Convenience Test",
        opportunity_description="Testing convenience function",
        funder_name="Test Foundation",
        funder_type="foundation",
        organization_ein="12-3456789",
        organization_name="Test Nonprofit",
        organization_mission="Test mission",
        depth="quick",
        screening_score=0.75
    )

    assert result.is_success()
    assert result.data.depth_executed == "quick"
    assert result.data.screening_score == 0.75


def test_output_structure():
    """Test that output has all required fields"""
    from tools.deep_intelligence_tool.app.intelligence_models import (
        DeepIntelligenceOutput,
        StrategicFitAnalysis,
        FinancialViabilityAnalysis,
        OperationalReadinessAnalysis,
        RiskAssessment,
        RiskLevel,
        SuccessProbability
    )

    # Minimal valid output
    strategic_fit = StrategicFitAnalysis(
        fit_score=0.8,
        mission_alignment_score=0.8,
        program_alignment_score=0.8,
        geographic_alignment_score=0.8,
        alignment_strengths=[],
        alignment_concerns=[],
        strategic_rationale="Test",
        strategic_positioning="Test",
        key_differentiators=[]
    )

    financial = FinancialViabilityAnalysis(
        viability_score=0.7,
        budget_capacity_score=0.7,
        financial_health_score=0.7,
        sustainability_score=0.7,
        budget_implications="Test",
        resource_requirements={},
        financial_risks=[],
        financial_strategy="Test",
        budget_recommendations=[]
    )

    operational = OperationalReadinessAnalysis(
        readiness_score=0.6,
        capacity_score=0.6,
        timeline_feasibility_score=0.6,
        infrastructure_readiness_score=0.6,
        capacity_gaps=[],
        infrastructure_requirements=[],
        timeline_challenges=[],
        capacity_building_plan="Test",
        operational_recommendations=[],
        estimated_preparation_time_weeks=12
    )

    risk = RiskAssessment(
        overall_risk_level=RiskLevel.MEDIUM,
        overall_risk_score=0.5,
        risk_factors=[],
        critical_risks=[],
        manageable_risks=[],
        risk_mitigation_plan="Test"
    )

    output = DeepIntelligenceOutput(
        strategic_fit=strategic_fit,
        financial_viability=financial,
        operational_readiness=operational,
        risk_assessment=risk,
        proceed_recommendation=True,
        success_probability=SuccessProbability.HIGH,
        overall_score=0.75,
        executive_summary="Test summary",
        key_strengths=["Strength 1"],
        key_challenges=["Challenge 1"],
        recommended_next_steps=["Step 1"],
        depth_executed="quick",
        processing_time_seconds=5.0,
        api_cost_usd=0.75
    )

    assert output.overall_score == 0.75
    assert output.proceed_recommendation is True
    assert output.depth_executed == "quick"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
