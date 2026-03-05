"""
Opportunity Screening Tool
12-Factor compliant tool for mass screening of grant opportunities.

Purpose: Screen 100s of opportunities → shortlist of ~10 for deep analysis
Cost: ~$0.001/opp (fast, haiku) or ~$0.01/opp (thorough, sonnet)
Replaces: ai_lite_unified, ai_heavy_light processors

AI Integration:
  - Uses Claude API via AnthropicService when ANTHROPIC_API_KEY is set
  - Falls back to rule-based scoring when no key is available
  - Fast mode: claude-haiku-4-5 for cost-efficient screening
  - Thorough mode: claude-sonnet-4-6 for deep multi-dimensional analysis
"""

from src.core.tool_framework.path_helper import setup_tool_paths

# Setup paths for imports
project_root = setup_tool_paths(__file__)

from typing import List, Optional
import asyncio
import json
import logging
import time
from datetime import datetime

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext
from src.core.anthropic_service import (
    AnthropicService,
    PipelineStage,
    get_anthropic_service,
)
from .screening_models import (
    ScreeningInput,
    ScreeningOutput,
    ScreeningMode,
    Opportunity,
    OrganizationProfile,
    OpportunityScore,
)


# ---------------------------------------------------------------------------
# Prompt builders — convert BAML templates into plain-text Claude prompts
# ---------------------------------------------------------------------------

def _build_fast_screening_prompt(
    opportunity: Opportunity,
    organization: OrganizationProfile,
) -> str:
    """Build the system + user prompt for fast (haiku) screening."""
    system = (
        "You are an expert grant researcher analyzing opportunity fit for a nonprofit. "
        "Return ONLY valid JSON matching the schema below — no markdown, no commentary.\n\n"
        "JSON Schema:\n"
        "{\n"
        '  "strategic_fit_score": float 0.0-1.0,\n'
        '  "eligibility_score": float 0.0-1.0,\n'
        '  "timing_score": float 0.0-1.0,\n'
        '  "overall_score": float 0.0-1.0,\n'
        '  "confidence_level": "high" | "medium" | "low",\n'
        '  "one_sentence_summary": string,\n'
        '  "key_strengths": [string, string],\n'
        '  "key_concerns": [string, string],\n'
        '  "reasoning": string (1-2 sentences explaining the score)\n'
        "}\n\n"
        "Scoring weights: overall = strategic_fit*0.50 + eligibility*0.30 + timing*0.20\n"
        "Be honest — a poor fit should score below 0.4. A great fit above 0.8."
    )

    geo = ", ".join(opportunity.geographic_restrictions) if opportunity.geographic_restrictions else "None specified"
    focus = ", ".join(opportunity.focus_areas) if opportunity.focus_areas else "None specified"
    amount = ""
    if opportunity.amount_min or opportunity.amount_max:
        amount = f"${opportunity.amount_min or '?'} - ${opportunity.amount_max or '?'}"
    else:
        amount = "Not specified"

    user = (
        f"ORGANIZATION:\n"
        f"  Name: {organization.name}\n"
        f"  Mission: {organization.mission}\n"
        f"  NTEE: {', '.join(organization.ntee_codes)}\n"
        f"  Geography: {', '.join(organization.geographic_focus)}\n"
        f"  Programs: {', '.join(organization.program_areas)}\n\n"
        f"OPPORTUNITY:\n"
        f"  Title: {opportunity.title}\n"
        f"  Funder: {opportunity.funder} ({opportunity.funder_type})\n"
        f"  Description: {opportunity.description[:1500]}\n"
        f"  Amount: {amount}\n"
        f"  Deadline: {opportunity.deadline or 'Not specified'}\n"
        f"  Geographic Restrictions: {geo}\n"
        f"  Focus Areas: {focus}\n\n"
        f"Score this opportunity for the organization above."
    )

    return system, user


def _build_thorough_screening_prompt(
    opportunity: Opportunity,
    organization: OrganizationProfile,
) -> str:
    """Build the system + user prompt for thorough (sonnet) screening."""
    system = (
        "You are an expert grant researcher performing comprehensive opportunity analysis. "
        "Return ONLY valid JSON matching the schema below — no markdown, no commentary.\n\n"
        "JSON Schema:\n"
        "{\n"
        '  "strategic_fit_score": float 0.0-1.0,\n'
        '  "eligibility_score": float 0.0-1.0,\n'
        '  "timing_score": float 0.0-1.0,\n'
        '  "financial_score": float 0.0-1.0,\n'
        '  "competition_score": float 0.0-1.0,\n'
        '  "overall_score": float 0.0-1.0,\n'
        '  "confidence_level": "high" | "medium" | "low",\n'
        '  "one_sentence_summary": string,\n'
        '  "key_strengths": [string, ...] (3-5 items),\n'
        '  "key_concerns": [string, ...] (3-5 items),\n'
        '  "risk_factors": [string, ...],\n'
        '  "recommended_actions": [string, ...],\n'
        '  "estimated_effort_hours": int,\n'
        '  "reasoning": string (2-3 sentences)\n'
        "}\n\n"
        "Scoring weights: overall = strategic_fit*0.35 + eligibility*0.25 + "
        "timing*0.15 + financial*0.15 + competition*0.10\n\n"
        "Strategic Fit: Mission alignment, program match, geographic alignment, capacity fit.\n"
        "Eligibility: Hard requirements, NTEE match, revenue/size, geographic eligibility.\n"
        "Timing: Deadline feasibility, award timing, project duration.\n"
        "Financial: Award size vs org capacity, budget fit, ROI potential.\n"
        "Competition: Competitive positioning, past recipients, unique value proposition.\n\n"
        "Be honest and specific. Poor fits should score below 0.4."
    )

    geo = ", ".join(opportunity.geographic_restrictions) if opportunity.geographic_restrictions else "None specified"
    focus = ", ".join(opportunity.focus_areas) if opportunity.focus_areas else "None specified"
    past = ", ".join(opportunity.past_recipients[:5]) if opportunity.past_recipients else "Unknown"
    reqs = ", ".join(opportunity.application_requirements) if opportunity.application_requirements else "Not specified"

    amount = ""
    if opportunity.amount_min or opportunity.amount_max:
        amount = f"${opportunity.amount_min or '?'} - ${opportunity.amount_max or '?'}"
    elif opportunity.typical_award_size:
        amount = f"Typical: ${opportunity.typical_award_size}"
    else:
        amount = "Not specified"

    user = (
        f"ORGANIZATION:\n"
        f"  Name: {organization.name}\n"
        f"  Mission: {organization.mission}\n"
        f"  NTEE Codes: {', '.join(organization.ntee_codes)}\n"
        f"  Geography: {', '.join(organization.geographic_focus)}\n"
        f"  Programs: {', '.join(organization.program_areas)}\n"
        f"  Annual Revenue: ${organization.annual_revenue:,.0f}\n" if organization.annual_revenue else ""
        f"  Staff: {organization.staff_count}\n" if organization.staff_count else ""
        f"  Years Established: {organization.years_established}\n\n" if organization.years_established else "\n"
        f"OPPORTUNITY:\n"
        f"  Title: {opportunity.title}\n"
        f"  Funder: {opportunity.funder} ({opportunity.funder_type})\n"
        f"  Description: {opportunity.description[:3000]}\n\n"
        f"  Amount: {amount}\n"
        f"  Deadline: {opportunity.deadline or 'Not specified'}\n"
        f"  Award Date: {opportunity.award_date or 'Not specified'}\n"
        f"  Duration: {opportunity.project_duration_months or 'Not specified'} months\n\n"
        f"  Geographic Restrictions: {geo}\n"
        f"  NTEE Requirements: {', '.join(opportunity.ntee_requirements) if opportunity.ntee_requirements else 'None'}\n"
        f"  Revenue Requirements: {opportunity.revenue_requirements or 'None'}\n\n"
        f"  Focus Areas: {focus}\n"
        f"  Past Recipients: {past}\n"
        f"  Application Requirements: {reqs}\n\n"
        f"Provide comprehensive scoring for this opportunity."
    )

    return system, user


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------

def _parse_ai_score(
    raw_json: dict,
    opportunity: Opportunity,
    mode: str,
) -> OpportunityScore:
    """Parse Claude's JSON response into an OpportunityScore dataclass."""

    def _float(key: str, default: float = 0.0) -> float:
        val = raw_json.get(key, default)
        try:
            return max(0.0, min(1.0, float(val)))
        except (TypeError, ValueError):
            return default

    def _str_list(key: str) -> list:
        val = raw_json.get(key, [])
        if isinstance(val, list):
            return [str(v) for v in val]
        return []

    strategic = _float("strategic_fit_score")
    eligibility = _float("eligibility_score")
    timing = _float("timing_score")
    financial = _float("financial_score")
    competition = _float("competition_score")
    overall = _float("overall_score")

    confidence = raw_json.get("confidence_level", "medium")
    if confidence not in ("high", "medium", "low"):
        confidence = "medium"

    # Determine proceed recommendation using lowered thresholds
    if mode == "fast":
        proceed = overall >= 0.40
    else:
        proceed = overall >= 0.50

    return OpportunityScore(
        opportunity_id=opportunity.opportunity_id,
        opportunity_title=opportunity.title,
        overall_score=overall,
        proceed_to_deep_analysis=proceed,
        confidence_level=confidence,
        strategic_fit_score=strategic,
        eligibility_score=eligibility,
        timing_score=timing,
        financial_score=financial,
        competition_score=competition,
        one_sentence_summary=raw_json.get("one_sentence_summary", "AI analysis complete."),
        key_strengths=_str_list("key_strengths"),
        key_concerns=_str_list("key_concerns"),
        risk_factors=_str_list("risk_factors"),
        recommended_actions=_str_list("recommended_actions"),
        estimated_effort_hours=raw_json.get("estimated_effort_hours"),
        analysis_depth=mode,
    )


# ---------------------------------------------------------------------------
# Tool class
# ---------------------------------------------------------------------------

class OpportunityScreeningTool(BaseTool[ScreeningOutput]):
    """
    12-Factor Opportunity Screening Tool

    Factor 4: Returns structured ScreeningOutput
    Factor 6: Stateless - no persistence between runs
    Factor 10: Single responsibility - opportunity screening only

    Uses Claude API when available, falls back to rule-based scoring otherwise.
    """

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)

        config = config or {}
        self.default_mode = config.get("default_mode", "fast")
        self.default_threshold = config.get("default_threshold", 0.40)

        # Get Anthropic service (may not have an API key)
        self._anthropic: AnthropicService = get_anthropic_service()
        self._ai_available = self._anthropic.is_available

        if self._ai_available:
            self.logger.info("Screening tool initialized with Claude AI scoring")
        else:
            self.logger.warning(
                "Screening tool initialized WITHOUT AI — using rule-based fallback. "
                "Set ANTHROPIC_API_KEY to enable Claude scoring."
            )

    def get_tool_name(self) -> str:
        return "Opportunity Screening Tool"

    def get_tool_version(self) -> str:
        return "2.0.0"

    def get_single_responsibility(self) -> str:
        return "Mass screening of grant opportunities to identify high-potential matches"

    # ------------------------------------------------------------------
    # Main execution
    # ------------------------------------------------------------------

    async def _execute(
        self,
        context: ToolExecutionContext,
        screening_input: ScreeningInput,
    ) -> ScreeningOutput:
        start_time = time.time()

        if screening_input.screening_mode == ScreeningMode.FAST:
            opportunity_scores = await self._screen_fast_batch(
                screening_input.opportunities,
                screening_input.organization_profile,
            )
        else:
            opportunity_scores = await self._screen_thorough_batch(
                screening_input.opportunities,
                screening_input.organization_profile,
            )

        # Filter by threshold
        passed_threshold = [
            s for s in opportunity_scores
            if s.overall_score >= screening_input.minimum_threshold
        ]
        passed_threshold.sort(key=lambda s: s.overall_score, reverse=True)
        recommended = passed_threshold[:screening_input.max_recommendations]

        processing_time = time.time() - start_time
        total_cost = self._calculate_cost(
            len(screening_input.opportunities),
            screening_input.screening_mode,
        )

        high_confidence = sum(
            1 for s in opportunity_scores if s.confidence_level == "high"
        )

        return ScreeningOutput(
            total_screened=len(screening_input.opportunities),
            passed_threshold=len(passed_threshold),
            recommended_for_deep_analysis=[s.opportunity_id for s in recommended],
            opportunity_scores=opportunity_scores,
            screening_mode=screening_input.screening_mode.value,
            threshold_used=screening_input.minimum_threshold,
            processing_time_seconds=processing_time,
            total_cost_usd=total_cost,
            high_confidence_count=high_confidence,
        )

    # ------------------------------------------------------------------
    # Fast screening (haiku)
    # ------------------------------------------------------------------

    async def _screen_fast_batch(
        self,
        opportunities: List[Opportunity],
        organization: OrganizationProfile,
    ) -> List[OpportunityScore]:
        """Fast screening — parallel batches of 10."""
        self.logger.info(f"Fast screening {len(opportunities)} opportunities")
        scores = []
        batch_size = 10
        for i in range(0, len(opportunities), batch_size):
            batch = opportunities[i:i + batch_size]
            batch_scores = await asyncio.gather(*[
                self._screen_fast_single(opp, organization) for opp in batch
            ])
            scores.extend(batch_scores)
        return scores

    async def _screen_fast_single(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile,
    ) -> OpportunityScore:
        """Screen a single opportunity — Claude haiku or rule-based fallback."""
        if self._ai_available:
            return await self._screen_fast_ai(opportunity, organization)
        return self._screen_fast_rules(opportunity, organization)

    async def _screen_fast_ai(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile,
    ) -> OpportunityScore:
        """Fast screening via Claude haiku."""
        system, user = _build_fast_screening_prompt(opportunity, organization)
        try:
            result = await self._anthropic.create_json_completion(
                messages=[{"role": "user", "content": user}],
                system=system,
                stage=PipelineStage.FAST_SCREENING,
                max_tokens=512,
                temperature=0.0,
            )
            return _parse_ai_score(result, opportunity, mode="fast")
        except Exception as e:
            self.logger.warning(
                f"AI fast screening failed for {opportunity.opportunity_id}, "
                f"falling back to rules: {e}"
            )
            return self._screen_fast_rules(opportunity, organization)

    def _screen_fast_rules(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile,
    ) -> OpportunityScore:
        """Rule-based fast screening fallback (original placeholder logic, improved)."""
        strategic_fit = self._calculate_strategic_fit_fast(opportunity, organization)
        eligibility = self._calculate_eligibility_fast(opportunity, organization)
        timing = self._calculate_timing_score(opportunity)

        overall = strategic_fit * 0.50 + eligibility * 0.30 + timing * 0.20
        proceed = overall >= 0.40  # Lowered from 0.55

        if proceed:
            summary = f"{opportunity.title} shows promising alignment and should be considered further."
        else:
            summary = f"{opportunity.title} has limited fit based on initial screening."

        return OpportunityScore(
            opportunity_id=opportunity.opportunity_id,
            opportunity_title=opportunity.title,
            overall_score=overall,
            proceed_to_deep_analysis=proceed,
            confidence_level="low",  # Rule-based = low confidence
            strategic_fit_score=strategic_fit,
            eligibility_score=eligibility,
            timing_score=timing,
            financial_score=0.0,
            competition_score=0.0,
            one_sentence_summary=summary,
            key_strengths=[],
            key_concerns=["Rule-based scoring only — enable AI for better results"],
            analysis_depth="fast",
        )

    # ------------------------------------------------------------------
    # Thorough screening (sonnet)
    # ------------------------------------------------------------------

    async def _screen_thorough_batch(
        self,
        opportunities: List[Opportunity],
        organization: OrganizationProfile,
    ) -> List[OpportunityScore]:
        """Thorough screening — parallel batches of 5."""
        self.logger.info(f"Thorough screening {len(opportunities)} opportunities")
        scores = []
        batch_size = 5
        for i in range(0, len(opportunities), batch_size):
            batch = opportunities[i:i + batch_size]
            batch_scores = await asyncio.gather(*[
                self._screen_thorough_single(opp, organization) for opp in batch
            ])
            scores.extend(batch_scores)
        return scores

    async def _screen_thorough_single(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile,
    ) -> OpportunityScore:
        """Screen a single opportunity — Claude sonnet or rule-based fallback."""
        if self._ai_available:
            return await self._screen_thorough_ai(opportunity, organization)
        return self._screen_thorough_rules(opportunity, organization)

    async def _screen_thorough_ai(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile,
    ) -> OpportunityScore:
        """Thorough screening via Claude sonnet."""
        system, user = _build_thorough_screening_prompt(opportunity, organization)
        try:
            result = await self._anthropic.create_json_completion(
                messages=[{"role": "user", "content": user}],
                system=system,
                stage=PipelineStage.THOROUGH_SCREENING,
                max_tokens=1024,
                temperature=0.0,
            )
            return _parse_ai_score(result, opportunity, mode="thorough")
        except Exception as e:
            self.logger.warning(
                f"AI thorough screening failed for {opportunity.opportunity_id}, "
                f"falling back to rules: {e}"
            )
            return self._screen_thorough_rules(opportunity, organization)

    def _screen_thorough_rules(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile,
    ) -> OpportunityScore:
        """Rule-based thorough screening fallback."""
        strategic_fit = self._calculate_strategic_fit_fast(opportunity, organization)
        eligibility = self._calculate_eligibility_fast(opportunity, organization)
        timing = self._calculate_timing_score(opportunity)
        financial = self._calculate_financial_score(opportunity, organization)
        competition = self._calculate_competition_score(opportunity)

        overall = (
            strategic_fit * 0.35
            + eligibility * 0.25
            + timing * 0.15
            + financial * 0.15
            + competition * 0.10
        )
        proceed = overall >= 0.50  # Lowered from 0.60
        confidence = self._calculate_confidence(overall, eligibility)

        if proceed:
            summary = f"{opportunity.title} demonstrates multi-dimensional fit worth deeper analysis."
        else:
            summary = f"{opportunity.title} presents challenges across multiple dimensions."

        return OpportunityScore(
            opportunity_id=opportunity.opportunity_id,
            opportunity_title=opportunity.title,
            overall_score=overall,
            proceed_to_deep_analysis=proceed,
            confidence_level="low",  # Rule-based = low confidence
            strategic_fit_score=strategic_fit,
            eligibility_score=eligibility,
            timing_score=timing,
            financial_score=financial,
            competition_score=competition,
            one_sentence_summary=summary,
            key_strengths=[],
            key_concerns=["Rule-based scoring only — enable AI for better results"],
            risk_factors=[],
            recommended_actions=["Review full RFP", "Assess capacity"],
            estimated_effort_hours=20,
            analysis_depth="thorough",
        )

    # ------------------------------------------------------------------
    # Rule-based scoring helpers (used by fallback path)
    # ------------------------------------------------------------------

    def _calculate_strategic_fit_fast(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile,
    ) -> float:
        """Quick strategic fit via keyword + NTEE matching."""
        score = 0.3  # Base — lower than before to create more spread

        # Program area overlap
        if opportunity.focus_areas and organization.program_areas:
            org_lower = {a.lower() for a in organization.program_areas}
            opp_lower = {a.lower() for a in opportunity.focus_areas}
            overlap = org_lower & opp_lower
            if overlap:
                score += min(len(overlap) * 0.15, 0.4)

        # NTEE code match
        if opportunity.ntee_requirements and organization.ntee_codes:
            if any(n in organization.ntee_codes for n in opportunity.ntee_requirements):
                score += 0.2

        # Description keyword matching against mission
        if organization.mission and opportunity.description:
            mission_words = set(organization.mission.lower().split())
            desc_words = set(opportunity.description.lower().split()[:200])
            # Remove common stop words
            stop = {"the", "a", "an", "and", "or", "of", "to", "in", "for", "is", "are", "with", "that", "this", "on", "at", "by"}
            mission_words -= stop
            desc_words -= stop
            if mission_words and desc_words:
                overlap_pct = len(mission_words & desc_words) / max(len(mission_words), 1)
                score += min(overlap_pct * 0.3, 0.2)

        return min(score, 1.0)

    def _calculate_eligibility_fast(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile,
    ) -> float:
        """Basic eligibility check with geographic + requirements matching."""
        score = 0.6  # Lowered base from 0.7

        # Geographic check — case-insensitive, also checks state abbreviations
        if opportunity.geographic_restrictions:
            org_geo = {g.lower() for g in organization.geographic_focus}
            opp_geo = {g.lower() for g in opportunity.geographic_restrictions}
            if org_geo & opp_geo:
                score += 0.3
            elif "nationwide" in opp_geo or "national" in opp_geo:
                score += 0.2
            else:
                score -= 0.3  # Stronger penalty for geographic mismatch

        # Revenue requirements
        if opportunity.revenue_requirements and organization.annual_revenue:
            # Simple check — if they specify a revenue requirement, having one is good
            score += 0.1

        return max(0.0, min(score, 1.0))

    def _calculate_timing_score(self, opportunity: Opportunity) -> float:
        """Calculate timing feasibility based on deadline."""
        if not opportunity.deadline:
            return 0.6  # Unknown = moderate, not 0.8

        try:
            deadline_dt = datetime.fromisoformat(opportunity.deadline.replace("Z", "+00:00"))
            days_until = (deadline_dt - datetime.now(deadline_dt.tzinfo)).days
            if days_until < 0:
                return 0.1  # Past deadline
            elif days_until < 14:
                return 0.3  # Very tight
            elif days_until < 30:
                return 0.5  # Tight but possible
            elif days_until < 90:
                return 0.8  # Comfortable
            else:
                return 0.9  # Plenty of time
        except (ValueError, TypeError):
            return 0.6  # Unparseable date

    def _calculate_financial_score(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile,
    ) -> float:
        """Calculate financial fit based on award size vs org revenue."""
        if not opportunity.typical_award_size and not opportunity.amount_max:
            return 0.5  # Unknown

        award = opportunity.typical_award_size or opportunity.amount_max or 0
        if not organization.annual_revenue or award == 0:
            return 0.5

        # Award should be roughly 5-30% of annual revenue for good fit
        ratio = award / organization.annual_revenue
        if 0.05 <= ratio <= 0.30:
            return 0.8
        elif 0.01 <= ratio <= 0.50:
            return 0.6
        else:
            return 0.3  # Too small or too large relative to org size

    def _calculate_competition_score(self, opportunity: Opportunity) -> float:
        """Estimate competitive positioning."""
        if opportunity.past_recipients:
            # Having past recipient data gives some insight
            return 0.5  # Moderate — we know it's competitive
        return 0.5  # Unknown competition = moderate

    def _calculate_confidence(self, overall_score: float, eligibility: float) -> str:
        if overall_score >= 0.75 and eligibility >= 0.85:
            return "high"
        elif overall_score >= 0.55 and eligibility >= 0.60:
            return "medium"
        return "low"

    def _calculate_cost(self, opportunity_count: int, mode: ScreeningMode) -> float:
        """Calculate estimated total cost for screening run."""
        if self._ai_available:
            # Claude API costs
            if mode == ScreeningMode.FAST:
                cost_per_opp = 0.001  # Haiku
            else:
                cost_per_opp = 0.01   # Sonnet
        else:
            # Rule-based = free
            cost_per_opp = 0.0
        return opportunity_count * cost_per_opp

    def get_cost_estimate(
        self,
        opportunity_count: int,
        mode: str = "fast",
    ) -> Optional[float]:
        mode_enum = ScreeningMode.FAST if mode == "fast" else ScreeningMode.THOROUGH
        return self._calculate_cost(opportunity_count, mode_enum)


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

async def screen_opportunities(
    opportunities: List[Opportunity],
    organization: OrganizationProfile,
    mode: str = "fast",
    threshold: float = 0.40,
    max_recommendations: int = 10,
    config: Optional[dict] = None,
) -> ToolResult[ScreeningOutput]:
    """
    Screen opportunities with the tool.

    Args:
        opportunities: List of opportunities to screen
        organization: Organization profile
        mode: "fast" or "thorough"
        threshold: Minimum score threshold (default lowered to 0.40)
        max_recommendations: Maximum recommendations
        config: Optional tool configuration

    Returns:
        ToolResult with ScreeningOutput
    """
    tool = OpportunityScreeningTool(config)
    screening_input = ScreeningInput(
        opportunities=opportunities,
        organization_profile=organization,
        screening_mode=ScreeningMode.FAST if mode == "fast" else ScreeningMode.THOROUGH,
        minimum_threshold=threshold,
        max_recommendations=max_recommendations,
    )
    return await tool.execute(screening_input=screening_input)
