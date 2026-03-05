"""
Tests for deep intelligence depth handlers — Claude API integration,
prompt building, response parsing, and fallback behavior.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import logging

from tools.deep_intelligence_tool.app.depth_handlers import (
    EssentialsDepthHandler,
    PremiumDepthHandler,
    QuickDepthHandler,
    _build_deep_analysis_prompt,
    _parse_deep_analysis_response,
    get_depth_handler,
)
from tools.deep_intelligence_tool.app.intelligence_models import (
    AnalysisDepth,
    DeepIntelligenceInput,
    DeepIntelligenceOutput,
    RiskLevel,
    SuccessProbability,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_input():
    return DeepIntelligenceInput(
        opportunity_id="opp-001",
        opportunity_title="Youth Education Innovation Grant",
        opportunity_description="This grant supports innovative K-12 education programs in underserved communities.",
        funder_name="Smith Education Foundation",
        funder_type="foundation",
        organization_ein="541234567",
        organization_name="Youth Education Alliance",
        organization_mission="Quality education for underserved youth in Virginia",
        organization_revenue=2_500_000,
        depth=AnalysisDepth.ESSENTIALS,
        screening_score=0.82,
        focus_areas=["education", "youth development"],
        opportunity_amount_min=50_000,
        opportunity_amount_max=200_000,
        opportunity_deadline="2026-06-15",
        user_notes="Board member has connection to program officer.",
    )


@pytest.fixture
def sample_ai_response():
    """A realistic Claude JSON response for deep analysis."""
    return {
        "strategic_fit": {
            "fit_score": 0.85,
            "mission_alignment_score": 0.90,
            "program_alignment_score": 0.82,
            "geographic_alignment_score": 0.78,
            "alignment_strengths": [
                "Direct mission alignment with K-12 education focus",
                "Established presence in target communities",
            ],
            "alignment_concerns": [
                "Innovation component may require new program design",
            ],
            "strategic_rationale": "Strong alignment with core mission and existing programs.",
            "strategic_positioning": "Position as experienced community partner with innovation capacity.",
            "key_differentiators": ["10-year track record", "Community trust"],
        },
        "financial_viability": {
            "viability_score": 0.72,
            "budget_capacity_score": 0.70,
            "financial_health_score": 0.75,
            "sustainability_score": 0.68,
            "budget_implications": "Grant represents 8% of annual revenue — manageable.",
            "resource_requirements": {"staff": "0.5 FTE program coordinator", "evaluation": "External consultant"},
            "financial_risks": ["Match funding requirement", "Sustainability post-grant"],
            "financial_strategy": "Leverage existing infrastructure to minimize overhead.",
            "budget_recommendations": ["Identify match sources early", "Build sustainability plan"],
        },
        "operational_readiness": {
            "readiness_score": 0.68,
            "capacity_score": 0.65,
            "timeline_feasibility_score": 0.72,
            "infrastructure_readiness_score": 0.67,
            "capacity_gaps": ["Evaluation expertise", "Data management"],
            "infrastructure_requirements": ["Learning management system"],
            "timeline_challenges": ["Staff hiring timeline"],
            "capacity_building_plan": "Phased 3-month ramp-up with consultant support.",
            "operational_recommendations": ["Partner with evaluation firm", "Hire early"],
            "estimated_preparation_time_weeks": 10,
        },
        "risk_assessment": {
            "overall_risk_level": "medium",
            "overall_risk_score": 0.45,
            "risk_factors": [
                {
                    "category": "competition",
                    "risk_level": "medium",
                    "description": "3-4 comparable organizations in region",
                    "impact": "Moderate impact on selection probability",
                    "mitigation_strategy": "Emphasize unique community relationships",
                    "probability": 0.5,
                },
            ],
            "critical_risks": [],
            "manageable_risks": ["Competition", "Evaluation capacity"],
            "risk_mitigation_plan": "Address capacity gaps through partnerships.",
        },
        "overall_score": 0.76,
        "success_probability": "high",
        "executive_summary": "This opportunity presents a strong fit for Youth Education Alliance.",
        "key_strengths": ["Mission alignment", "Community trust", "Track record"],
        "key_challenges": ["Evaluation capacity", "Innovation requirement"],
        "recommended_next_steps": [
            "Review full RFP requirements",
            "Identify evaluation partner",
            "Develop preliminary budget",
        ],
    }


@pytest.fixture
def sample_premium_response(sample_ai_response):
    """Premium response includes extra fields."""
    resp = dict(sample_ai_response)
    resp["relationship_mapping"] = {
        "direct_relationships": ["Partner Org A"],
        "indirect_relationships": ["Funder board member via Partner A"],
        "partnership_opportunities": ["Joint programming"],
        "relationship_insights": "Strong network position",
        "cultivation_strategy": "Use board connection for warm intro",
    }
    resp["policy_analysis"] = {
        "federal_alignment_score": 0.80,
        "federal_policies": ["Education Reform Act"],
        "policy_opportunities": ["Federal priority alignment"],
        "policy_risks": ["Administration change"],
        "policy_landscape_summary": "Favorable policy environment.",
        "advocacy_recommendations": ["Join education coalition"],
    }
    resp["strategic_consulting"] = {
        "executive_summary": "Strong strategic opportunity.",
        "competitive_positioning": "Regional leader",
        "differentiation_strategy": "Community-based innovation",
        "multi_year_funding_strategy": "Build for multi-year support",
        "partnership_development_strategy": "Deepen partner network",
        "capacity_building_roadmap": "Phase 1: Foundation. Phase 2: Scale.",
        "immediate_actions": ["Submit LOI"],
        "medium_term_actions": ["Build evaluation capacity"],
        "long_term_actions": ["Seek multi-year funding"],
    }
    return resp


# ---------------------------------------------------------------------------
# Prompt Building Tests
# ---------------------------------------------------------------------------

class TestPromptBuilding:

    def test_essentials_prompt_includes_context(self, sample_input):
        system, user = _build_deep_analysis_prompt(sample_input, depth="essentials")
        assert "grant research analyst" in system
        assert "strategic_fit" in system
        assert "Youth Education Alliance" in user
        assert "Youth Education Innovation Grant" in user
        assert "Smith Education Foundation" in user
        assert "$2,500,000" in user
        assert "0.82" in user  # screening score

    def test_premium_prompt_includes_extra_fields(self, sample_input):
        system, user = _build_deep_analysis_prompt(sample_input, depth="premium")
        assert "relationship_mapping" in system
        assert "policy_analysis" in system
        assert "strategic_consulting" in system

    def test_essentials_prompt_excludes_premium_fields(self, sample_input):
        system, user = _build_deep_analysis_prompt(sample_input, depth="essentials")
        assert "relationship_mapping" not in system
        assert "strategic_consulting" not in system

    def test_user_notes_included(self, sample_input):
        system, user = _build_deep_analysis_prompt(sample_input)
        assert "Board member has connection" in user

    def test_focus_areas_included(self, sample_input):
        system, user = _build_deep_analysis_prompt(sample_input)
        assert "education" in user
        assert "youth development" in user


# ---------------------------------------------------------------------------
# Response Parsing Tests
# ---------------------------------------------------------------------------

class TestResponseParsing:

    def test_parse_essentials_response(self, sample_ai_response, sample_input):
        output = _parse_deep_analysis_response(sample_ai_response, sample_input)
        assert isinstance(output, DeepIntelligenceOutput)
        assert output.overall_score == 0.76
        assert output.strategic_fit.fit_score == 0.85
        assert output.financial_viability.viability_score == 0.72
        assert output.operational_readiness.readiness_score == 0.68
        assert output.risk_assessment.overall_risk_level == RiskLevel.MEDIUM
        assert output.success_probability == SuccessProbability.HIGH
        assert len(output.key_strengths) == 3
        assert output.proceed_recommendation is True  # 0.76 >= 0.50

    def test_parse_premium_response(self, sample_premium_response, sample_input):
        output = _parse_deep_analysis_response(sample_premium_response, sample_input, premium=True)
        assert output.relationship_mapping is not None
        assert "Partner Org A" in output.relationship_mapping.direct_relationships
        assert output.policy_analysis is not None
        assert output.policy_analysis.federal_policy_alignment.alignment_score == 0.80
        assert output.strategic_consulting is not None
        assert "Submit LOI" in output.strategic_consulting.immediate_actions

    def test_no_auto_reject_low_score(self, sample_ai_response, sample_input):
        """Scores below 0.65 should NOT be auto-rejected anymore."""
        sample_ai_response["overall_score"] = 0.55
        output = _parse_deep_analysis_response(sample_ai_response, sample_input)
        assert output.overall_score == 0.55
        assert output.proceed_recommendation is True  # 0.55 >= 0.50

    def test_very_low_score_marked_no_proceed(self, sample_ai_response, sample_input):
        """Only very low scores (< 0.50) get proceed=False."""
        sample_ai_response["overall_score"] = 0.35
        output = _parse_deep_analysis_response(sample_ai_response, sample_input)
        assert output.proceed_recommendation is False

    def test_parse_handles_missing_fields(self, sample_input):
        """Parser should not crash on minimal response."""
        output = _parse_deep_analysis_response({}, sample_input)
        assert output.overall_score == 0.5  # default
        assert output.strategic_fit.fit_score == 0.5
        assert output.risk_assessment.overall_risk_level == RiskLevel.MEDIUM

    def test_parse_handles_invalid_enums(self, sample_ai_response, sample_input):
        """Invalid enum values should fall back to defaults."""
        sample_ai_response["success_probability"] = "extremely_high"
        sample_ai_response["risk_assessment"]["overall_risk_level"] = "catastrophic"
        output = _parse_deep_analysis_response(sample_ai_response, sample_input)
        assert output.success_probability == SuccessProbability.MODERATE
        assert output.risk_assessment.overall_risk_level == RiskLevel.MEDIUM


# ---------------------------------------------------------------------------
# Handler Integration Tests
# ---------------------------------------------------------------------------

class TestEssentialsHandler:

    @pytest.mark.asyncio
    async def test_essentials_with_ai(self, sample_input, sample_ai_response):
        """When Claude is available, uses AI for analysis."""
        mock_anthropic = MagicMock()
        mock_anthropic.is_available = True
        mock_anthropic.create_json_completion = AsyncMock(return_value=sample_ai_response)

        with patch(
            "src.core.anthropic_service.get_anthropic_service",
            return_value=mock_anthropic,
        ):
            handler = EssentialsDepthHandler(logging.getLogger("test"))
            output = await handler.analyze(sample_input)

            assert output.overall_score == 0.76
            assert output.depth_executed == "essentials"
            assert output.api_cost_usd == 0.05
            assert output.historical_intelligence is not None  # Algorithmic enrichment
            assert output.geographic_analysis is not None
            mock_anthropic.create_json_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_essentials_fallback_on_error(self, sample_input):
        """When Claude fails, falls back to rule-based analysis."""
        mock_anthropic = MagicMock()
        mock_anthropic.is_available = True
        mock_anthropic.create_json_completion = AsyncMock(side_effect=RuntimeError("API down"))

        with patch(
            "src.core.anthropic_service.get_anthropic_service",
            return_value=mock_anthropic,
        ):
            handler = EssentialsDepthHandler(logging.getLogger("test"))
            output = await handler.analyze(sample_input)

            # Should still return a valid output from fallback
            assert isinstance(output, DeepIntelligenceOutput)
            assert output.depth_executed == "essentials"

    @pytest.mark.asyncio
    async def test_essentials_fallback_no_api_key(self, sample_input):
        """When no API key, falls back to rule-based analysis."""
        mock_anthropic = MagicMock()
        mock_anthropic.is_available = False

        with patch(
            "src.core.anthropic_service.get_anthropic_service",
            return_value=mock_anthropic,
        ):
            handler = EssentialsDepthHandler(logging.getLogger("test"))
            output = await handler.analyze(sample_input)

            assert isinstance(output, DeepIntelligenceOutput)


class TestPremiumHandler:

    @pytest.mark.asyncio
    async def test_premium_with_ai(self, sample_input, sample_premium_response):
        """Premium handler uses Claude Opus and includes extra analysis."""
        sample_input.depth = AnalysisDepth.PREMIUM

        mock_anthropic = MagicMock()
        mock_anthropic.is_available = True
        mock_anthropic.create_json_completion = AsyncMock(return_value=sample_premium_response)

        with patch(
            "src.core.anthropic_service.get_anthropic_service",
            return_value=mock_anthropic,
        ):
            handler = PremiumDepthHandler(logging.getLogger("test"))
            output = await handler.analyze(sample_input)

            assert output.depth_executed == "premium"
            assert output.api_cost_usd == 0.10
            assert output.relationship_mapping is not None
            assert output.policy_analysis is not None
            assert output.strategic_consulting is not None

            # Verify Opus model was used (PREMIUM_INTELLIGENCE stage)
            call_kwargs = mock_anthropic.create_json_completion.call_args
            from src.core.anthropic_service import PipelineStage
            assert call_kwargs.kwargs.get("stage") == PipelineStage.PREMIUM_INTELLIGENCE

    @pytest.mark.asyncio
    async def test_premium_fallback(self, sample_input):
        """Premium fallback still produces relationship/policy/consulting output."""
        mock_anthropic = MagicMock()
        mock_anthropic.is_available = False

        with patch(
            "src.core.anthropic_service.get_anthropic_service",
            return_value=mock_anthropic,
        ):
            handler = PremiumDepthHandler(logging.getLogger("test"))
            output = await handler.analyze(sample_input)

            assert output.depth_executed == "premium"
            assert output.relationship_mapping is not None
            assert output.policy_analysis is not None
            assert output.strategic_consulting is not None


# ---------------------------------------------------------------------------
# Depth Migration Tests
# ---------------------------------------------------------------------------

class TestDepthMigration:

    def test_quick_maps_to_essentials(self):
        handler = get_depth_handler(AnalysisDepth.QUICK, logging.getLogger("test"))
        assert isinstance(handler, EssentialsDepthHandler)

    def test_standard_maps_to_essentials(self):
        handler = get_depth_handler(AnalysisDepth.STANDARD, logging.getLogger("test"))
        assert isinstance(handler, EssentialsDepthHandler)

    def test_enhanced_maps_to_premium(self):
        handler = get_depth_handler(AnalysisDepth.ENHANCED, logging.getLogger("test"))
        assert isinstance(handler, PremiumDepthHandler)

    def test_complete_maps_to_premium(self):
        handler = get_depth_handler(AnalysisDepth.COMPLETE, logging.getLogger("test"))
        assert isinstance(handler, PremiumDepthHandler)

    def test_essentials_returns_essentials(self):
        handler = get_depth_handler(AnalysisDepth.ESSENTIALS, logging.getLogger("test"))
        assert isinstance(handler, EssentialsDepthHandler)

    def test_premium_returns_premium(self):
        handler = get_depth_handler(AnalysisDepth.PREMIUM, logging.getLogger("test"))
        assert isinstance(handler, PremiumDepthHandler)
