"""
Schedule I Grant Analyzer Tool
12-Factor compliant tool for foundation grant pattern analysis.

Purpose: Analyze 990-PF Schedule I grants for funding intelligence
Cost: $0.03 per analysis
Replaces: schedule_i_processor.py, funnel_schedule_i_analyzer.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Optional
import time
from datetime import datetime
from collections import Counter

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext
from .schedule_i_models import (
    ScheduleIGrantAnalyzerInput,
    ScheduleIGrantAnalyzerOutput,
    GrantRecord,
    GrantCategory,
    GrantTier,
    GrantingPatterns,
    GrantSizeAnalysis,
    RecipientProfile,
    FoundationIntelligence,
    MatchAnalysis,
    SCHEDULE_I_ANALYZER_COST
)


class ScheduleIGrantAnalyzerTool(BaseTool[ScheduleIGrantAnalyzerOutput]):
    """
    12-Factor Schedule I Grant Analyzer Tool

    Factor 4: Returns structured ScheduleIGrantAnalyzerOutput
    Factor 6: Stateless - no persistence between runs
    Factor 10: Single responsibility - Schedule I analysis only
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize Schedule I analyzer tool."""
        super().__init__(config)
        self.openai_api_key = config.get("openai_api_key") if config else None

    def get_tool_name(self) -> str:
        return "Schedule I Grant Analyzer Tool"

    def get_tool_version(self) -> str:
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        return "Foundation grant-making pattern analysis from 990-PF Schedule I data"

    async def _execute(
        self,
        context: ToolExecutionContext,
        analyzer_input: ScheduleIGrantAnalyzerInput
    ) -> ScheduleIGrantAnalyzerOutput:
        """Execute Schedule I grant analysis."""
        start_time = time.time()

        self.logger.info(
            f"Starting Schedule I analysis: {analyzer_input.foundation_name} "
            f"with {len(analyzer_input.grants)} grants"
        )

        # Process grant records
        processed_grants = self._process_grants(analyzer_input.grants)

        # Analyze granting patterns
        patterns = self._analyze_granting_patterns(processed_grants)

        # Grant size analysis
        size_analysis = self._analyze_grant_sizes(processed_grants)

        # Recipient profile
        recipient_profile = self._profile_recipients(processed_grants)

        # Foundation intelligence
        foundation_intel = self._analyze_foundation_intelligence(
            processed_grants, patterns, size_analysis
        )

        # Match analysis (if organization provided)
        match_analysis = None
        if analyzer_input.analyzing_organization_ein:
            match_analysis = self._analyze_match(
                analyzer_input, processed_grants, patterns, size_analysis
            )

        # Data quality
        quality_score = self._assess_data_quality(analyzer_input.grants)

        processing_time = time.time() - start_time

        output = ScheduleIGrantAnalyzerOutput(
            foundation_ein=analyzer_input.foundation_ein,
            foundation_name=analyzer_input.foundation_name,
            tax_year=analyzer_input.tax_year,
            processed_grants=processed_grants,
            granting_patterns=patterns,
            grant_size_analysis=size_analysis,
            recipient_profile=recipient_profile,
            foundation_intelligence=foundation_intel,
            match_analysis=match_analysis,
            analysis_date=datetime.now().isoformat(),
            data_quality_score=quality_score,
            confidence_level=0.85,
            processing_time_seconds=processing_time,
            api_cost_usd=SCHEDULE_I_ANALYZER_COST
        )

        self.logger.info(
            f"Completed Schedule I analysis: {len(processed_grants)} grants, "
            f"${patterns.total_amount:,.0f} total"
        )

        return output

    def _process_grants(self, grants: list[dict]) -> list[GrantRecord]:
        """Process raw grant data into structured records"""
        processed = []

        # Calculate tiers
        amounts = [g.get("amount", 0) for g in grants if g.get("amount")]
        amounts.sort()

        if len(amounts) >= 5:
            major_threshold = amounts[int(len(amounts) * 0.8)]
            significant_threshold = amounts[int(len(amounts) * 0.5)]
            moderate_threshold = amounts[int(len(amounts) * 0.2)]
        else:
            major_threshold = max(amounts) if amounts else 0
            significant_threshold = major_threshold * 0.6
            moderate_threshold = major_threshold * 0.3

        for grant in grants:
            amount = grant.get("amount", 0)
            purpose = grant.get("purpose", "")

            # Determine tier
            if amount >= major_threshold:
                tier = GrantTier.MAJOR
            elif amount >= significant_threshold:
                tier = GrantTier.SIGNIFICANT
            elif amount >= moderate_threshold:
                tier = GrantTier.MODERATE
            else:
                tier = GrantTier.SMALL

            # Determine category (simple keyword matching)
            category = self._categorize_grant(purpose)

            processed.append(GrantRecord(
                recipient_name=grant.get("recipient_name", "Unknown"),
                recipient_ein=grant.get("ein"),
                grant_amount=amount,
                grant_purpose=purpose,
                recipient_city=grant.get("city"),
                recipient_state=grant.get("state"),
                grant_category=category,
                grant_tier=tier
            ))

        return processed

    def _categorize_grant(self, purpose: str) -> GrantCategory:
        """Categorize grant based on purpose"""
        purpose_lower = purpose.lower()

        if any(word in purpose_lower for word in ["education", "school", "scholarship", "student"]):
            return GrantCategory.EDUCATION
        elif any(word in purpose_lower for word in ["health", "medical", "hospital", "clinic"]):
            return GrantCategory.HEALTH
        elif any(word in purpose_lower for word in ["arts", "culture", "museum", "theater"]):
            return GrantCategory.ARTS_CULTURE
        elif any(word in purpose_lower for word in ["environment", "conservation", "climate"]):
            return GrantCategory.ENVIRONMENT
        elif any(word in purpose_lower for word in ["human services", "homeless", "food", "shelter"]):
            return GrantCategory.HUMAN_SERVICES
        elif any(word in purpose_lower for word in ["international", "global", "overseas"]):
            return GrantCategory.INTERNATIONAL
        elif any(word in purpose_lower for word in ["research", "study", "investigation"]):
            return GrantCategory.RESEARCH
        else:
            return GrantCategory.OTHER

    def _analyze_granting_patterns(self, grants: list[GrantRecord]) -> GrantingPatterns:
        """Analyze overall granting patterns"""

        amounts = [g.grant_amount for g in grants]
        amounts.sort()

        total_grants = len(grants)
        total_amount = sum(amounts)
        average_grant = total_amount / total_grants if total_grants > 0 else 0
        median_grant = amounts[len(amounts) // 2] if amounts else 0

        # By tier
        major_grants = [g for g in grants if g.grant_tier == GrantTier.MAJOR]
        significant_grants = [g for g in grants if g.grant_tier == GrantTier.SIGNIFICANT]
        moderate_grants = [g for g in grants if g.grant_tier == GrantTier.MODERATE]
        small_grants = [g for g in grants if g.grant_tier == GrantTier.SMALL]

        # By category
        category_counter = Counter(g.grant_category for g in grants)
        category_amounts = {}
        for category in GrantCategory:
            category_grants = [g for g in grants if g.grant_category == category]
            category_amounts[category.value] = sum(g.grant_amount for g in category_grants)

        # By geography
        state_counter = Counter(g.recipient_state for g in grants if g.recipient_state)
        top_states = [state for state, _ in state_counter.most_common(5)]

        # Focus areas (top categories)
        top_categories = [cat for cat, _ in category_counter.most_common()]
        primary = top_categories[:2] if len(top_categories) >= 2 else top_categories
        secondary = top_categories[2:5] if len(top_categories) > 2 else []

        return GrantingPatterns(
            total_grants=total_grants,
            total_amount=total_amount,
            average_grant=average_grant,
            median_grant=median_grant,
            largest_grant=max(amounts) if amounts else 0,
            smallest_grant=min(amounts) if amounts else 0,
            major_grants_count=len(major_grants),
            major_grants_total=sum(g.grant_amount for g in major_grants),
            significant_grants_count=len(significant_grants),
            significant_grants_total=sum(g.grant_amount for g in significant_grants),
            moderate_grants_count=len(moderate_grants),
            moderate_grants_total=sum(g.grant_amount for g in moderate_grants),
            small_grants_count=len(small_grants),
            small_grants_total=sum(g.grant_amount for g in small_grants),
            category_distribution={cat: count for cat, count in category_counter.items()},
            category_amounts=category_amounts,
            geographic_distribution={state: count for state, count in state_counter.items()},
            geographic_focus=top_states,
            primary_focus_areas=[cat.value for cat in primary],
            secondary_focus_areas=[cat.value for cat in secondary]
        )

    def _analyze_grant_sizes(self, grants: list[GrantRecord]) -> GrantSizeAnalysis:
        """Analyze grant size patterns"""

        tiers_info = {}
        for tier in GrantTier:
            tier_grants = [g for g in grants if g.grant_tier == tier]
            if tier_grants:
                amounts = [g.grant_amount for g in tier_grants]
                tiers_info[tier.value] = {
                    "min": min(amounts),
                    "max": max(amounts),
                    "avg": sum(amounts) / len(amounts),
                    "count": len(tier_grants)
                }

        # Typical range (25th to 75th percentile)
        amounts = sorted([g.grant_amount for g in grants])
        if len(amounts) >= 4:
            q1 = amounts[len(amounts) // 4]
            q3 = amounts[3 * len(amounts) // 4]
            typical_range = f"${q1:,.0f} - ${q3:,.0f}"
        else:
            typical_range = f"${amounts[0]:,.0f} - ${amounts[-1]:,.0f}" if amounts else "N/A"

        # Competitive grant size (median of significant/major)
        competitive_grants = [g for g in grants if g.grant_tier in [GrantTier.MAJOR, GrantTier.SIGNIFICANT]]
        if competitive_grants:
            competitive_amounts = sorted([g.grant_amount for g in competitive_grants])
            competitive_size = competitive_amounts[len(competitive_amounts) // 2]
        else:
            competitive_size = sum(g.grant_amount for g in grants) / len(grants) if grants else 0

        recommendation = f"Request ${competitive_size:,.0f} to be competitive (median of significant/major grants)"

        return GrantSizeAnalysis(
            grant_size_tiers=tiers_info,
            typical_grant_range=typical_range,
            grant_size_recommendation=recommendation,
            competitive_grant_size=competitive_size
        )

    def _profile_recipients(self, grants: list[GrantRecord]) -> RecipientProfile:
        """Profile typical grant recipients"""

        # Organization types (from names/purposes)
        org_types = []
        for grant in grants:
            name_lower = grant.recipient_name.lower()
            if "university" in name_lower or "college" in name_lower:
                org_types.append("Higher Education")
            elif "school" in name_lower:
                org_types.append("K-12 Education")
            elif "hospital" in name_lower or "medical" in name_lower:
                org_types.append("Healthcare")
            elif "museum" in name_lower or "theater" in name_lower:
                org_types.append("Arts & Culture")
            else:
                org_types.append("Nonprofit Organization")

        org_type_counter = Counter(org_types)
        top_types = [t for t, _ in org_type_counter.most_common(5)]

        # Geographic preferences
        state_counter = Counter(g.recipient_state for g in grants if g.recipient_state)
        top_states = [state for state, _ in state_counter.most_common(3)]

        characteristics = [
            f"Typical grant size: {self._analyze_grant_sizes(grants).typical_grant_range}",
            f"Primary focus: {', '.join(self._analyze_granting_patterns(grants).primary_focus_areas)}",
            f"Geographic focus: {', '.join(top_states) if top_states else 'National'}"
        ]

        return RecipientProfile(
            typical_recipient_characteristics=characteristics,
            organization_types=top_types,
            geographic_preferences=top_states,
            excluded_types=[]  # Would need more data to determine
        )

    def _analyze_foundation_intelligence(
        self,
        grants: list[GrantRecord],
        patterns: GrantingPatterns,
        size_analysis: GrantSizeAnalysis
    ) -> FoundationIntelligence:
        """Analyze foundation intelligence"""

        # Granting style
        if len(patterns.primary_focus_areas) <= 2:
            style = "Focused"
        elif len(patterns.primary_focus_areas) <= 4:
            style = "Diverse"
        else:
            style = "Opportunistic"

        # Decision-making indicators
        indicators = [
            f"Makes {patterns.total_grants} grants per year totaling ${patterns.total_amount:,.0f}",
            f"Average grant: ${patterns.average_grant:,.0f}, Median: ${patterns.median_grant:,.0f}",
            f"{style} funding approach"
        ]

        # Priorities
        stated_priorities = patterns.primary_focus_areas  # Would come from foundation website
        revealed_priorities = patterns.primary_focus_areas  # From actual grants

        # Accessibility
        if patterns.total_grants > 100:
            accessibility = "Accessible - makes many grants annually"
            barriers = ["High competition due to large applicant pool"]
        elif patterns.total_grants > 50:
            accessibility = "Moderately accessible"
            barriers = ["Moderate competition", "May require relationships"]
        else:
            accessibility = "Selective - small number of grants"
            barriers = ["Limited grant opportunities", "Likely requires strong relationships"]

        success_factors = [
            "Alignment with primary focus areas",
            f"Request within typical range ({size_analysis.typical_grant_range})",
            "Demonstrate organizational capacity"
        ]

        insights = [
            f"{style} grant-making approach indicates {'broad' if style == 'Opportunistic' else 'targeted'} funding interests",
            f"Geographic focus on {', '.join(patterns.geographic_focus[:3])} suggests regional priorities",
            f"Grant size distribution shows preference for {patterns.major_grants_count + patterns.significant_grants_count} substantial grants vs {patterns.small_grants_count} small grants"
        ]

        cultivation = f"{'Build relationships through' if patterns.total_grants < 50 else 'Apply directly with'} strong alignment to {', '.join(patterns.primary_focus_areas[:2])}"

        return FoundationIntelligence(
            granting_style=style,
            decision_making_indicators=indicators,
            stated_priorities=stated_priorities,
            revealed_priorities=revealed_priorities,
            priority_alignment="Strong alignment" if stated_priorities == revealed_priorities else "Review priorities",
            accessibility_assessment=accessibility,
            barriers_to_entry=barriers,
            success_factors=success_factors,
            strategic_insights=insights,
            cultivation_strategy=cultivation
        )

    def _analyze_match(
        self,
        inp: ScheduleIGrantAnalyzerInput,
        grants: list[GrantRecord],
        patterns: GrantingPatterns,
        size_analysis: GrantSizeAnalysis
    ) -> MatchAnalysis:
        """Analyze match for analyzing organization"""

        # Mission alignment (simplified - would use NLP in production)
        org_mission = inp.analyzing_organization_mission or ""
        mission_keywords = org_mission.lower().split()

        mission_score = 0.0
        for category in patterns.primary_focus_areas:
            if any(keyword in category.lower() for keyword in mission_keywords):
                mission_score += 0.3
        mission_score = min(1.0, mission_score)

        # Geographic match
        org_state = inp.analyzing_organization_location
        geo_score = 1.0 if org_state in patterns.geographic_focus else 0.5

        # Grant size match (can they give meaningful amount?)
        # Assume org wants at least $25k
        desired_amount = 25000
        grant_size_score = 1.0 if size_analysis.competitive_grant_size >= desired_amount else 0.5

        # Recipient type match
        recipient_score = 0.7  # Default moderate match

        # Overall match
        overall_score = (mission_score * 0.4 + geo_score * 0.2 + grant_size_score * 0.3 + recipient_score * 0.1)

        # Find similar grants
        similar = []
        for grant in grants:
            if grant.grant_category.value in [cat.lower() for cat in patterns.primary_focus_areas]:
                similar.append(grant)
        similar = similar[:5]  # Top 5

        # Strengths and concerns
        strengths = []
        concerns = []

        if mission_score > 0.6:
            strengths.append("Strong mission alignment with foundation priorities")
        else:
            concerns.append("Limited mission alignment - may need stronger positioning")

        if geo_score > 0.8:
            strengths.append("Geographic alignment with foundation focus areas")

        if grant_size_score > 0.8:
            strengths.append("Foundation grants at appropriate scale for organization")
        else:
            concerns.append("Foundation typical grants may be too small/large")

        # Application strategy
        if overall_score > 0.7:
            strategy = f"Strong match - apply with confidence emphasizing {', '.join(patterns.primary_focus_areas[:2])} alignment"
        elif overall_score > 0.5:
            strategy = f"Moderate match - strengthen application by emphasizing {', '.join(strengths[:2]) if strengths else 'alignment areas'}"
        else:
            strategy = "Weak match - reconsider or significantly strengthen alignment demonstration"

        # Recommended ask
        recommended_ask = size_analysis.competitive_grant_size

        # Positioning
        positioning = [
            f"Emphasize {patterns.primary_focus_areas[0] if patterns.primary_focus_areas else 'mission'} alignment",
            "Highlight relevant outcomes and impact",
            "Demonstrate organizational capacity"
        ]

        assessment = f"{'Strong' if overall_score > 0.7 else 'Moderate' if overall_score > 0.5 else 'Weak'} match with foundation priorities"

        return MatchAnalysis(
            overall_match_score=overall_score,
            match_assessment=assessment,
            mission_alignment_score=mission_score,
            geographic_match_score=geo_score,
            grant_size_match_score=grant_size_score,
            recipient_type_match_score=recipient_score,
            similar_past_grants=similar,
            match_strengths=strengths,
            match_concerns=concerns,
            application_strategy=strategy,
            recommended_ask_amount=recommended_ask,
            positioning_recommendations=positioning
        )

    def _assess_data_quality(self, grants: list[dict]) -> float:
        """Assess quality of grant data"""
        if not grants:
            return 0.0

        score = 0.0
        for grant in grants:
            if grant.get("recipient_name"):
                score += 0.3
            if grant.get("amount") and grant.get("amount") > 0:
                score += 0.4
            if grant.get("purpose"):
                score += 0.2
            if grant.get("state"):
                score += 0.1

        return min(1.0, score / len(grants))

    def get_cost_estimate(self) -> Optional[float]:
        return SCHEDULE_I_ANALYZER_COST

    def validate_inputs(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate tool inputs."""
        analyzer_input = kwargs.get("analyzer_input")

        if not analyzer_input:
            return False, "analyzer_input is required"

        if not isinstance(analyzer_input, ScheduleIGrantAnalyzerInput):
            return False, "analyzer_input must be ScheduleIGrantAnalyzerInput instance"

        if not analyzer_input.foundation_ein:
            return False, "foundation_ein is required"

        if not analyzer_input.grants:
            return False, "grants list is required"

        return True, None


# Convenience function
async def analyze_schedule_i_grants(
    foundation_ein: str,
    foundation_name: str,
    grants: list[dict],
    tax_year: int,
    analyzing_organization_ein: Optional[str] = None,
    analyzing_organization_name: Optional[str] = None,
    analyzing_organization_mission: Optional[str] = None,
    analyzing_organization_location: Optional[str] = None,
    config: Optional[dict] = None
) -> ToolResult[ScheduleIGrantAnalyzerOutput]:
    """Analyze Schedule I grants."""

    tool = ScheduleIGrantAnalyzerTool(config)

    analyzer_input = ScheduleIGrantAnalyzerInput(
        foundation_ein=foundation_ein,
        foundation_name=foundation_name,
        grants=grants,
        tax_year=tax_year,
        analyzing_organization_ein=analyzing_organization_ein,
        analyzing_organization_name=analyzing_organization_name,
        analyzing_organization_mission=analyzing_organization_mission,
        analyzing_organization_location=analyzing_organization_location
    )

    return await tool.execute(analyzer_input=analyzer_input)
