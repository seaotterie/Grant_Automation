"""
Opportunity Screening Tool
12-Factor compliant tool for mass screening of grant opportunities.

Purpose: Screen 100s of opportunities → shortlist of ~10 for deep analysis
Cost: $0.0004-$0.04 per opportunity depending on mode
Replaces: ai_lite_unified, ai_heavy_light processors
"""

import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import List, Optional
import asyncio
import time
from datetime import datetime

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext
from .screening_models import (
    ScreeningInput,
    ScreeningOutput,
    ScreeningMode,
    Opportunity,
    OrganizationProfile,
    OpportunityScore
)


class OpportunityScreeningTool(BaseTool[ScreeningOutput]):
    """
    12-Factor Opportunity Screening Tool

    Factor 4: Returns structured ScreeningOutput
    Factor 6: Stateless - no persistence between runs
    Factor 10: Single responsibility - opportunity screening only
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize screening tool.

        Args:
            config: Optional configuration
                - openai_api_key: OpenAI API key
                - default_mode: "fast" or "thorough"
                - default_threshold: float (0.0-1.0)
        """
        super().__init__(config)

        # Configuration
        self.openai_api_key = config.get("openai_api_key") if config else None
        self.default_mode = config.get("default_mode", "fast")
        self.default_threshold = config.get("default_threshold", 0.55)

    def get_tool_name(self) -> str:
        """Tool name."""
        return "Opportunity Screening Tool"

    def get_tool_version(self) -> str:
        """Tool version."""
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        """Tool's single responsibility."""
        return "Mass screening of grant opportunities to identify high-potential matches"

    async def _execute(
        self,
        context: ToolExecutionContext,
        screening_input: ScreeningInput
    ) -> ScreeningOutput:
        """
        Execute opportunity screening.

        Args:
            context: Execution context
            screening_input: Screening input data

        Returns:
            ScreeningOutput with scored opportunities
        """
        start_time = time.time()

        # Screen opportunities based on mode
        if screening_input.screening_mode == ScreeningMode.FAST:
            opportunity_scores = await self._screen_fast_batch(
                screening_input.opportunities,
                screening_input.organization_profile
            )
        else:
            opportunity_scores = await self._screen_thorough_batch(
                screening_input.opportunities,
                screening_input.organization_profile
            )

        # Filter by threshold
        passed_threshold = [
            score for score in opportunity_scores
            if score.overall_score >= screening_input.minimum_threshold
        ]

        # Sort by score and limit recommendations
        passed_threshold.sort(key=lambda s: s.overall_score, reverse=True)
        recommended = passed_threshold[:screening_input.max_recommendations]

        # Calculate processing time and cost
        processing_time = time.time() - start_time
        total_cost = self._calculate_cost(
            len(screening_input.opportunities),
            screening_input.screening_mode
        )

        # Calculate quality metrics
        high_confidence = sum(
            1 for score in opportunity_scores
            if score.confidence_level == "high"
        )

        # Create output
        output = ScreeningOutput(
            total_screened=len(screening_input.opportunities),
            passed_threshold=len(passed_threshold),
            recommended_for_deep_analysis=[s.opportunity_id for s in recommended],
            opportunity_scores=opportunity_scores,
            screening_mode=screening_input.screening_mode.value,
            threshold_used=screening_input.minimum_threshold,
            processing_time_seconds=processing_time,
            total_cost_usd=total_cost,
            high_confidence_count=high_confidence
        )

        return output

    async def _screen_fast_batch(
        self,
        opportunities: List[Opportunity],
        organization: OrganizationProfile
    ) -> List[OpportunityScore]:
        """
        Fast screening mode (PLAN tab equivalent).

        Cost: ~$0.0004 per opportunity
        Time: ~2 seconds per opportunity
        Focus: Basic strategic fit and eligibility
        """
        self.logger.info(f"Fast screening {len(opportunities)} opportunities")

        # Screen opportunities in parallel (batches of 10)
        scores = []
        batch_size = 10

        for i in range(0, len(opportunities), batch_size):
            batch = opportunities[i:i + batch_size]
            batch_scores = await asyncio.gather(*[
                self._screen_fast_single(opp, organization)
                for opp in batch
            ])
            scores.extend(batch_scores)

        return scores

    async def _screen_fast_single(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile
    ) -> OpportunityScore:
        """
        Fast screening of single opportunity.

        Simple rule-based + lightweight AI scoring.
        """
        # TODO: Replace with actual BAML AI call
        # For now, using rule-based scoring as placeholder

        # Strategic fit (mission/program alignment)
        strategic_fit = self._calculate_strategic_fit_fast(opportunity, organization)

        # Eligibility (basic requirements)
        eligibility = self._calculate_eligibility_fast(opportunity, organization)

        # Timing (deadline feasibility)
        timing = self._calculate_timing_score(opportunity)

        # Overall score (weighted average)
        overall_score = (
            strategic_fit * 0.50 +
            eligibility * 0.30 +
            timing * 0.20
        )

        # Determine if should proceed
        proceed = overall_score >= 0.55 and eligibility >= 0.70

        # Generate summary (placeholder)
        summary = self._generate_fast_summary(opportunity, overall_score, proceed)

        return OpportunityScore(
            opportunity_id=opportunity.opportunity_id,
            opportunity_title=opportunity.title,
            overall_score=overall_score,
            proceed_to_deep_analysis=proceed,
            confidence_level="medium",  # Fast mode = medium confidence
            strategic_fit_score=strategic_fit,
            eligibility_score=eligibility,
            timing_score=timing,
            financial_score=0.0,  # Not assessed in fast mode
            competition_score=0.0,  # Not assessed in fast mode
            one_sentence_summary=summary,
            key_strengths=["Strategic alignment (placeholder)"],
            key_concerns=["Detailed analysis needed (placeholder)"],
            analysis_depth="fast"
        )

    async def _screen_thorough_batch(
        self,
        opportunities: List[Opportunity],
        organization: OrganizationProfile
    ) -> List[OpportunityScore]:
        """
        Thorough screening mode (ANALYZE tab equivalent).

        Cost: ~$0.02-$0.04 per opportunity
        Time: ~5 seconds per opportunity
        Focus: Comprehensive multi-dimensional analysis
        """
        self.logger.info(f"Thorough screening {len(opportunities)} opportunities")

        # Screen opportunities in parallel (batches of 5)
        scores = []
        batch_size = 5

        for i in range(0, len(opportunities), batch_size):
            batch = opportunities[i:i + batch_size]
            batch_scores = await asyncio.gather(*[
                self._screen_thorough_single(opp, organization)
                for opp in batch
            ])
            scores.extend(batch_scores)

        return scores

    async def _screen_thorough_single(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile
    ) -> OpportunityScore:
        """
        Thorough screening of single opportunity.

        Comprehensive AI-powered multi-dimensional analysis.
        """
        # TODO: Replace with actual BAML AI call
        # For now, using enhanced rule-based scoring

        # All dimensional scores
        strategic_fit = self._calculate_strategic_fit_thorough(opportunity, organization)
        eligibility = self._calculate_eligibility_thorough(opportunity, organization)
        timing = self._calculate_timing_score(opportunity)
        financial = self._calculate_financial_score(opportunity, organization)
        competition = self._calculate_competition_score(opportunity)

        # Overall score (weighted average)
        overall_score = (
            strategic_fit * 0.35 +
            eligibility * 0.25 +
            timing * 0.15 +
            financial * 0.15 +
            competition * 0.10
        )

        # Determine if should proceed
        proceed = overall_score >= 0.60 and eligibility >= 0.75

        # Confidence level
        confidence = self._calculate_confidence(overall_score, eligibility)

        # Generate detailed summary
        summary = self._generate_thorough_summary(opportunity, overall_score, proceed)

        return OpportunityScore(
            opportunity_id=opportunity.opportunity_id,
            opportunity_title=opportunity.title,
            overall_score=overall_score,
            proceed_to_deep_analysis=proceed,
            confidence_level=confidence,
            strategic_fit_score=strategic_fit,
            eligibility_score=eligibility,
            timing_score=timing,
            financial_score=financial,
            competition_score=competition,
            one_sentence_summary=summary,
            key_strengths=["Comprehensive analysis (placeholder)"],
            key_concerns=["Deep dive recommended (placeholder)"],
            risk_factors=["Limited competitive analysis (placeholder)"],
            recommended_actions=["Review full RFP", "Assess capacity"],
            estimated_effort_hours=20,
            analysis_depth="thorough"
        )

    # Helper methods (placeholder implementations)

    def _calculate_strategic_fit_fast(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile
    ) -> float:
        """Quick strategic fit calculation."""
        # Simple keyword matching (placeholder)
        score = 0.5
        if any(area in opportunity.focus_areas for area in organization.program_areas):
            score += 0.3
        return min(score, 1.0)

    def _calculate_strategic_fit_thorough(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile
    ) -> float:
        """Detailed strategic fit calculation."""
        # Enhanced analysis (placeholder)
        return 0.75

    def _calculate_eligibility_fast(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile
    ) -> float:
        """Basic eligibility check."""
        score = 0.7  # Assume eligible by default
        # Check geographic restrictions
        if opportunity.geographic_restrictions:
            if not any(geo in organization.geographic_focus for geo in opportunity.geographic_restrictions):
                score -= 0.2
        return max(score, 0.0)

    def _calculate_eligibility_thorough(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile
    ) -> float:
        """Detailed eligibility analysis."""
        return 0.85

    def _calculate_timing_score(self, opportunity: Opportunity) -> float:
        """Calculate timing feasibility."""
        # Placeholder: assume deadline is workable
        return 0.8

    def _calculate_financial_score(
        self,
        opportunity: Opportunity,
        organization: OrganizationProfile
    ) -> float:
        """Calculate financial fit."""
        # Placeholder
        return 0.7

    def _calculate_competition_score(self, opportunity: Opportunity) -> float:
        """Calculate competitive positioning."""
        # Placeholder
        return 0.6

    def _calculate_confidence(self, overall_score: float, eligibility: float) -> str:
        """Determine confidence level."""
        if overall_score >= 0.75 and eligibility >= 0.85:
            return "high"
        elif overall_score >= 0.60 and eligibility >= 0.70:
            return "medium"
        else:
            return "low"

    def _generate_fast_summary(
        self,
        opportunity: Opportunity,
        score: float,
        proceed: bool
    ) -> str:
        """Generate fast mode summary."""
        if proceed:
            return f"{opportunity.title} shows promising alignment and should be considered further."
        else:
            return f"{opportunity.title} has limited fit based on initial screening."

    def _generate_thorough_summary(
        self,
        opportunity: Opportunity,
        score: float,
        proceed: bool
    ) -> str:
        """Generate thorough mode summary."""
        if proceed:
            return f"{opportunity.title} demonstrates strong multi-dimensional fit with high strategic value."
        else:
            return f"{opportunity.title} presents challenges across multiple dimensions requiring careful consideration."

    def _calculate_cost(self, opportunity_count: int, mode: ScreeningMode) -> float:
        """Calculate total cost for screening."""
        if mode == ScreeningMode.FAST:
            cost_per_opp = 0.0004
        else:
            cost_per_opp = 0.02

        return opportunity_count * cost_per_opp

    def get_cost_estimate(
        self,
        opportunity_count: int,
        mode: str = "fast"
    ) -> Optional[float]:
        """
        Estimate execution cost.

        Args:
            opportunity_count: Number of opportunities to screen
            mode: "fast" or "thorough"

        Returns:
            Estimated cost in USD
        """
        mode_enum = ScreeningMode.FAST if mode == "fast" else ScreeningMode.THOROUGH
        return self._calculate_cost(opportunity_count, mode_enum)


# Convenience function for direct usage
async def screen_opportunities(
    opportunities: List[Opportunity],
    organization: OrganizationProfile,
    mode: str = "fast",
    threshold: float = 0.55,
    max_recommendations: int = 10,
    config: Optional[dict] = None
) -> ToolResult[ScreeningOutput]:
    """
    Screen opportunities with the tool.

    Args:
        opportunities: List of opportunities to screen
        organization: Organization profile
        mode: "fast" or "thorough"
        threshold: Minimum score threshold
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
        max_recommendations=max_recommendations
    )

    return await tool.execute(screening_input=screening_input)
