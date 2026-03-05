"""
Tests for OpportunityScreeningTool v2 — Claude AI + rule-based fallback.

Tests cover:
- Rule-based fallback scoring (no API key)
- AI path with mocked Claude responses
- Threshold changes (fast: 0.40, thorough: 0.50)
- Prompt construction
- JSON response parsing
- Batch processing
- Graceful degradation on AI errors
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from tools.opportunity_screening_tool.app.screening_models import (
    Opportunity,
    OrganizationProfile,
    OpportunityScore,
    ScreeningInput,
    ScreeningMode,
)
from tools.opportunity_screening_tool.app.screening_tool import (
    OpportunityScreeningTool,
    _build_fast_screening_prompt,
    _build_thorough_screening_prompt,
    _parse_ai_score,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_org():
    return OrganizationProfile(
        ein="541234567",
        name="Youth Education Alliance",
        mission="Providing quality education and mentorship to underserved youth",
        ntee_codes=["B25", "P20"],
        geographic_focus=["Virginia", "VA", "Maryland"],
        program_areas=["youth development", "education", "mentorship"],
        annual_revenue=2_500_000,
        staff_count=25,
        years_established=12,
    )


@pytest.fixture
def sample_opps():
    return [
        Opportunity(
            opportunity_id="opp_001",
            title="Youth STEM Education Grant",
            funder="National Science Foundation",
            funder_type="government",
            description="Funding for STEM education programs targeting underserved youth in K-12 settings",
            amount_min=50000,
            amount_max=250000,
            deadline="2026-06-15",
            geographic_restrictions=["Virginia", "Maryland", "DC"],
            focus_areas=["education", "STEM", "youth development"],
        ),
        Opportunity(
            opportunity_id="opp_002",
            title="Agricultural Research Initiative",
            funder="USDA",
            funder_type="government",
            description="Research funding for agricultural innovation and crop science",
            amount_min=500000,
            amount_max=2000000,
            geographic_restrictions=["Iowa", "Nebraska"],
            focus_areas=["agriculture", "research"],
        ),
        Opportunity(
            opportunity_id="opp_003",
            title="Community Mentorship Program",
            funder="Local Foundation",
            funder_type="foundation",
            description="Supporting mentorship programs for at-risk youth in the mid-Atlantic region",
            amount_min=10000,
            amount_max=75000,
            geographic_restrictions=[],
            focus_areas=["mentorship", "youth development"],
        ),
    ]


@pytest.fixture
def tool_no_ai():
    """Screening tool without AI (rule-based fallback)."""
    with patch(
        "tools.opportunity_screening_tool.app.screening_tool.get_anthropic_service"
    ) as mock_get:
        mock_svc = MagicMock()
        mock_svc.is_available = False
        mock_get.return_value = mock_svc
        tool = OpportunityScreeningTool()
        return tool


@pytest.fixture
def tool_with_ai():
    """Screening tool with mocked AI service."""
    with patch(
        "tools.opportunity_screening_tool.app.screening_tool.get_anthropic_service"
    ) as mock_get:
        mock_svc = MagicMock()
        mock_svc.is_available = True
        mock_svc.create_json_completion = AsyncMock()
        mock_get.return_value = mock_svc
        tool = OpportunityScreeningTool()
        return tool


# ---------------------------------------------------------------------------
# Prompt Construction Tests
# ---------------------------------------------------------------------------

class TestPromptConstruction:

    def test_fast_prompt_includes_org_info(self, sample_org, sample_opps):
        system, user = _build_fast_screening_prompt(sample_opps[0], sample_org)
        assert "Youth Education Alliance" in user
        assert "underserved youth" in user
        assert "JSON" in system

    def test_fast_prompt_includes_opp_info(self, sample_org, sample_opps):
        _, user = _build_fast_screening_prompt(sample_opps[0], sample_org)
        assert "Youth STEM Education Grant" in user
        assert "National Science Foundation" in user

    def test_thorough_prompt_includes_dimensions(self, sample_org, sample_opps):
        system, user = _build_thorough_screening_prompt(sample_opps[0], sample_org)
        assert "financial_score" in system
        assert "competition_score" in system
        assert "Strategic Fit" in system

    def test_fast_prompt_scoring_weights(self, sample_org, sample_opps):
        system, _ = _build_fast_screening_prompt(sample_opps[0], sample_org)
        assert "strategic_fit*0.50" in system
        assert "eligibility*0.30" in system


# ---------------------------------------------------------------------------
# AI Response Parsing Tests
# ---------------------------------------------------------------------------

class TestResponseParsing:

    def test_parse_valid_fast_response(self, sample_opps):
        raw = {
            "strategic_fit_score": 0.82,
            "eligibility_score": 0.90,
            "timing_score": 0.75,
            "overall_score": 0.83,
            "confidence_level": "high",
            "one_sentence_summary": "Strong STEM education fit.",
            "key_strengths": ["Mission alignment", "Geographic match"],
            "key_concerns": ["Competition"],
            "reasoning": "Good fit overall.",
        }
        score = _parse_ai_score(raw, sample_opps[0], mode="fast")
        assert score.overall_score == 0.83
        assert score.proceed_to_deep_analysis is True  # 0.83 >= 0.40
        assert score.confidence_level == "high"
        assert len(score.key_strengths) == 2

    def test_parse_low_score_fast_no_proceed(self, sample_opps):
        raw = {
            "strategic_fit_score": 0.15,
            "eligibility_score": 0.20,
            "timing_score": 0.30,
            "overall_score": 0.18,
            "confidence_level": "medium",
            "one_sentence_summary": "Poor fit.",
            "key_strengths": [],
            "key_concerns": ["No alignment"],
        }
        score = _parse_ai_score(raw, sample_opps[1], mode="fast")
        assert score.overall_score == 0.18
        assert score.proceed_to_deep_analysis is False  # 0.18 < 0.40

    def test_parse_thorough_threshold(self, sample_opps):
        raw = {"overall_score": 0.49}
        score = _parse_ai_score(raw, sample_opps[0], mode="thorough")
        assert score.proceed_to_deep_analysis is False  # 0.49 < 0.50

        raw2 = {"overall_score": 0.51}
        score2 = _parse_ai_score(raw2, sample_opps[0], mode="thorough")
        assert score2.proceed_to_deep_analysis is True  # 0.51 >= 0.50

    def test_parse_clamps_scores(self, sample_opps):
        raw = {"strategic_fit_score": 1.5, "eligibility_score": -0.3}
        score = _parse_ai_score(raw, sample_opps[0], mode="fast")
        assert score.strategic_fit_score == 1.0
        assert score.eligibility_score == 0.0

    def test_parse_invalid_confidence_defaults_medium(self, sample_opps):
        raw = {"confidence_level": "super_high"}
        score = _parse_ai_score(raw, sample_opps[0], mode="fast")
        assert score.confidence_level == "medium"


# ---------------------------------------------------------------------------
# Rule-Based Fallback Tests
# ---------------------------------------------------------------------------

class TestRuleBasedFallback:

    def test_good_fit_scores_high(self, tool_no_ai, sample_org, sample_opps):
        """opp_001 (STEM education) should score well for an education org."""
        score = tool_no_ai._screen_fast_rules(sample_opps[0], sample_org)
        assert score.overall_score > 0.4
        assert score.proceed_to_deep_analysis is True
        assert score.analysis_depth == "fast"
        assert score.confidence_level == "low"  # Rule-based always low

    def test_poor_fit_scores_low(self, tool_no_ai, sample_org, sample_opps):
        """opp_002 (agriculture in Iowa) should score poorly for a VA education org."""
        score = tool_no_ai._screen_fast_rules(sample_opps[1], sample_org)
        assert score.overall_score < 0.5
        # Geographic mismatch + no program overlap

    def test_thorough_fallback_includes_all_dimensions(self, tool_no_ai, sample_org, sample_opps):
        score = tool_no_ai._screen_thorough_rules(sample_opps[0], sample_org)
        assert score.financial_score > 0
        assert score.competition_score > 0
        assert score.analysis_depth == "thorough"

    def test_timing_score_no_deadline(self, tool_no_ai):
        opp = Opportunity(
            opportunity_id="test", title="Test", funder="F",
            funder_type="government", description="desc",
            deadline=None,
        )
        score = tool_no_ai._calculate_timing_score(opp)
        assert score == 0.6  # Unknown deadline

    def test_timing_score_tight_deadline(self, tool_no_ai):
        from datetime import datetime, timedelta
        soon = (datetime.now() + timedelta(days=10)).isoformat()
        opp = Opportunity(
            opportunity_id="test", title="Test", funder="F",
            funder_type="government", description="desc",
            deadline=soon,
        )
        score = tool_no_ai._calculate_timing_score(opp)
        assert score == 0.3  # < 14 days = very tight


# ---------------------------------------------------------------------------
# AI Integration Tests (mocked)
# ---------------------------------------------------------------------------

class TestAIIntegration:

    @pytest.mark.asyncio
    async def test_fast_ai_called_when_available(self, tool_with_ai, sample_org, sample_opps):
        """When AI is available, fast screening calls Claude haiku."""
        tool_with_ai._anthropic.create_json_completion.return_value = {
            "strategic_fit_score": 0.85,
            "eligibility_score": 0.90,
            "timing_score": 0.80,
            "overall_score": 0.86,
            "confidence_level": "high",
            "one_sentence_summary": "Excellent fit.",
            "key_strengths": ["Strong alignment"],
            "key_concerns": [],
        }

        score = await tool_with_ai._screen_fast_ai(sample_opps[0], sample_org)

        assert score.overall_score == 0.86
        assert score.confidence_level == "high"
        tool_with_ai._anthropic.create_json_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_thorough_ai_called_when_available(self, tool_with_ai, sample_org, sample_opps):
        """When AI is available, thorough screening calls Claude sonnet."""
        tool_with_ai._anthropic.create_json_completion.return_value = {
            "strategic_fit_score": 0.75,
            "eligibility_score": 0.80,
            "timing_score": 0.70,
            "financial_score": 0.65,
            "competition_score": 0.55,
            "overall_score": 0.72,
            "confidence_level": "medium",
            "one_sentence_summary": "Good fit with moderate competition.",
            "key_strengths": ["Program match", "Geographic fit"],
            "key_concerns": ["Competition"],
            "risk_factors": [],
            "recommended_actions": ["Review RFP"],
            "estimated_effort_hours": 15,
        }

        score = await tool_with_ai._screen_thorough_ai(sample_opps[0], sample_org)

        assert score.overall_score == 0.72
        assert score.financial_score == 0.65
        assert score.analysis_depth == "thorough"

    @pytest.mark.asyncio
    async def test_ai_failure_falls_back_to_rules(self, tool_with_ai, sample_org, sample_opps):
        """If Claude call fails, should fall back to rule-based scoring."""
        tool_with_ai._anthropic.create_json_completion.side_effect = RuntimeError("API error")

        score = await tool_with_ai._screen_fast_ai(sample_opps[0], sample_org)

        # Should get a rule-based score, not an exception
        assert score.overall_score > 0
        assert score.confidence_level == "low"  # Rule-based = low


# ---------------------------------------------------------------------------
# Cost Estimation Tests
# ---------------------------------------------------------------------------

class TestCostEstimation:

    def test_ai_fast_cost(self, tool_with_ai):
        cost = tool_with_ai._calculate_cost(200, ScreeningMode.FAST)
        assert cost == pytest.approx(0.20)  # 200 * $0.001

    def test_ai_thorough_cost(self, tool_with_ai):
        cost = tool_with_ai._calculate_cost(50, ScreeningMode.THOROUGH)
        assert cost == pytest.approx(0.50)  # 50 * $0.01

    def test_no_ai_cost_is_zero(self, tool_no_ai):
        cost = tool_no_ai._calculate_cost(200, ScreeningMode.FAST)
        assert cost == 0.0

    def test_cost_estimate_convenience(self, tool_with_ai):
        estimate = tool_with_ai.get_cost_estimate(100, mode="fast")
        assert estimate == pytest.approx(0.10)
