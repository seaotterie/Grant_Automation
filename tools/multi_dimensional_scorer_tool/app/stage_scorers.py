"""
Stage-Specific Scoring Logic
Each workflow stage has different dimensional calculations.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

try:
    from .scorer_models import DimensionalScore, TrackType
except ImportError:
    from scorer_models import DimensionalScore, TrackType


class BaseStageScorer:
    """Base class for stage-specific scoring."""

    def calculate_dimensions(
        self,
        opportunity: Dict[str, Any],
        organization: Dict[str, Any],
        weights: Dict[str, float],
        track_type: Optional[TrackType]
    ) -> List[DimensionalScore]:
        """Calculate dimensional scores for this stage."""
        raise NotImplementedError

    def _create_dimensional_score(
        self,
        dimension_name: str,
        raw_score: float,
        weight: float,
        data_quality: float = 0.8,
        calculation_method: Optional[str] = None,
        data_sources: List[str] = None,
        notes: Optional[str] = None
    ) -> DimensionalScore:
        """Helper to create a dimensional score."""
        return DimensionalScore(
            dimension_name=dimension_name,
            raw_score=min(1.0, max(0.0, raw_score)),  # Clamp 0-1
            weight=weight,
            weighted_score=min(1.0, max(0.0, raw_score)) * weight,
            boost_factor=1.0,  # Will be updated by boost logic
            data_quality=data_quality,
            calculation_method=calculation_method,
            data_sources=data_sources or [],
            notes=notes
        )

    def _safe_get(self, data: Dict, key: str, default=None):
        """Safely get nested dict values."""
        keys = key.split('.')
        value = data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value if value is not None else default


class DiscoverStageScorer(BaseStageScorer):
    """DISCOVER stage scoring - initial opportunity identification."""

    def calculate_dimensions(
        self,
        opportunity: Dict[str, Any],
        organization: Dict[str, Any],
        weights: Dict[str, float],
        track_type: Optional[TrackType]
    ) -> List[DimensionalScore]:
        """Calculate DISCOVER dimensions."""

        dimensions = []

        # Mission Alignment (0.30)
        mission_score = self._calculate_mission_alignment(opportunity, organization)
        dimensions.append(self._create_dimensional_score(
            "mission_alignment",
            mission_score,
            weights.get("mission_alignment", 0.30),
            data_quality=0.75,
            calculation_method="keyword_matching + category_alignment",
            data_sources=["opportunity_description", "organization_mission"]
        ))

        # Geographic Fit (0.25)
        geo_score = self._calculate_geographic_fit(opportunity, organization)
        dimensions.append(self._create_dimensional_score(
            "geographic_fit",
            geo_score,
            weights.get("geographic_fit", 0.25),
            data_quality=0.9,
            calculation_method="location_matching",
            data_sources=["opportunity_location", "organization_location"]
        ))

        # Financial Match (0.20)
        financial_score = self._calculate_financial_match(opportunity, organization)
        dimensions.append(self._create_dimensional_score(
            "financial_match",
            financial_score,
            weights.get("financial_match", 0.20),
            data_quality=0.85,
            calculation_method="award_size_vs_org_revenue",
            data_sources=["opportunity_award_amount", "organization_revenue"]
        ))

        # Eligibility (0.15)
        eligibility_score = self._calculate_eligibility(opportunity, organization, track_type)
        dimensions.append(self._create_dimensional_score(
            "eligibility",
            eligibility_score,
            weights.get("eligibility", 0.15),
            data_quality=0.7,
            calculation_method="basic_eligibility_check",
            data_sources=["opportunity_eligibility", "organization_type"]
        ))

        # Timing (0.10)
        timing_score = self._calculate_timing(opportunity)
        dimensions.append(self._create_dimensional_score(
            "timing",
            timing_score,
            weights.get("timing", 0.10),
            data_quality=1.0,
            calculation_method="days_until_deadline",
            data_sources=["opportunity_deadline"]
        ))

        return dimensions

    def _calculate_mission_alignment(self, opp: Dict, org: Dict) -> float:
        """Calculate mission alignment score."""
        # Simplified - would use NLP/embedding similarity in production
        opp_desc = str(self._safe_get(opp, 'description', '')).lower()
        org_mission = str(self._safe_get(org, 'mission', '')).lower()

        # Basic keyword matching
        opp_keywords = set(opp_desc.split())
        org_keywords = set(org_mission.split())

        if not opp_keywords or not org_keywords:
            return 0.5  # Neutral if no data

        overlap = len(opp_keywords & org_keywords)
        union = len(opp_keywords | org_keywords)

        return overlap / union if union > 0 else 0.5

    def _calculate_geographic_fit(self, opp: Dict, org: Dict) -> float:
        """Calculate geographic fit score."""
        opp_location = str(self._safe_get(opp, 'location', '')).lower()
        org_location = str(self._safe_get(org, 'location', '')).lower()

        if not opp_location or opp_location == "national" or opp_location == "any":
            return 1.0  # National opportunities match all

        if not org_location:
            return 0.5  # Unknown location

        # Simple state/city matching
        if opp_location in org_location or org_location in opp_location:
            return 1.0

        return 0.3  # Different locations

    def _calculate_financial_match(self, opp: Dict, org: Dict) -> float:
        """Calculate financial match score."""
        award_amount = self._safe_get(opp, 'award_amount', 0)
        org_revenue = self._safe_get(org, 'revenue', 0)

        if not award_amount or not org_revenue:
            return 0.5  # Neutral if no data

        # Award should be 5-30% of org revenue for good match
        ratio = award_amount / org_revenue

        if 0.05 <= ratio <= 0.30:
            return 1.0  # Ideal range
        elif ratio < 0.05:
            return 0.7  # Small but manageable
        elif ratio <= 0.50:
            return 0.8  # Larger but still good
        else:
            return 0.4  # Too large, may be risky

    def _calculate_eligibility(self, opp: Dict, org: Dict, track: Optional[TrackType]) -> float:
        """Calculate basic eligibility score."""
        # Simplified - would check detailed eligibility criteria
        org_type = self._safe_get(org, 'organization_type', '').lower()

        if '501(c)(3)' in org_type or 'nonprofit' in org_type:
            return 0.9  # Most opportunities accept nonprofits

        return 0.6  # Other org types have limited eligibility

    def _calculate_timing(self, opp: Dict) -> float:
        """Calculate timing score based on deadline."""
        days_until_deadline = self._safe_get(opp, 'days_until_deadline', 60)

        if days_until_deadline >= 60:
            return 1.0  # Ample time
        elif days_until_deadline >= 30:
            return 0.8  # Good time
        elif days_until_deadline >= 14:
            return 0.6  # Tight but doable
        else:
            return 0.3  # Very tight


class PlanStageScorer(BaseStageScorer):
    """PLAN stage scoring - success probability assessment."""

    def calculate_dimensions(
        self,
        opportunity: Dict[str, Any],
        organization: Dict[str, Any],
        weights: Dict[str, float],
        track_type: Optional[TrackType]
    ) -> List[DimensionalScore]:
        """Calculate PLAN dimensions."""

        dimensions = []

        # Success Probability (0.30)
        dimensions.append(self._create_dimensional_score(
            "success_probability",
            self._calculate_success_probability(opportunity, organization),
            weights.get("success_probability", 0.30),
            data_quality=0.7
        ))

        # Organizational Capacity (0.25)
        dimensions.append(self._create_dimensional_score(
            "organizational_capacity",
            self._calculate_org_capacity(organization),
            weights.get("organizational_capacity", 0.25),
            data_quality=0.8
        ))

        # Financial Viability (0.20)
        dimensions.append(self._create_dimensional_score(
            "financial_viability",
            self._calculate_financial_viability(organization),
            weights.get("financial_viability", 0.20),
            data_quality=0.85
        ))

        # Network Leverage (0.15)
        dimensions.append(self._create_dimensional_score(
            "network_leverage",
            self._calculate_network_leverage(organization),
            weights.get("network_leverage", 0.15),
            data_quality=0.6
        ))

        # Compliance (0.10)
        dimensions.append(self._create_dimensional_score(
            "compliance",
            self._calculate_compliance(organization),
            weights.get("compliance", 0.10),
            data_quality=0.9
        ))

        return dimensions

    def _calculate_success_probability(self, opp: Dict, org: Dict) -> float:
        """Estimate overall success probability."""
        # Simplified - would use ML model in production
        track_record = self._safe_get(org, 'past_grants_won', 0)
        experience_years = self._safe_get(org, 'years_operating', 0)

        score = 0.5  # Base probability

        # Boost for track record
        if track_record > 10:
            score += 0.2
        elif track_record > 5:
            score += 0.1

        # Boost for experience
        if experience_years > 10:
            score += 0.15
        elif experience_years > 5:
            score += 0.1

        return min(1.0, score)

    def _calculate_org_capacity(self, org: Dict) -> float:
        """Assess organizational capacity."""
        staff_count = self._safe_get(org, 'staff_count', 0)
        revenue = self._safe_get(org, 'revenue', 0)

        score = 0.5

        # Staff capacity
        if staff_count > 20:
            score += 0.2
        elif staff_count > 10:
            score += 0.1

        # Financial capacity
        if revenue > 1000000:
            score += 0.2
        elif revenue > 500000:
            score += 0.15

        return min(1.0, score)

    def _calculate_financial_viability(self, org: Dict) -> float:
        """Assess financial health."""
        revenue = self._safe_get(org, 'revenue', 0)
        expenses = self._safe_get(org, 'expenses', 0)

        if not revenue or not expenses:
            return 0.6

        # Check if expenses exceed revenue significantly
        if expenses > revenue * 1.5:
            return 0.4  # Financial stress
        elif expenses > revenue * 1.1:
            return 0.6  # Slight deficit
        else:
            return 0.9  # Healthy

    def _calculate_network_leverage(self, org: Dict) -> float:
        """Assess network strength."""
        board_size = self._safe_get(org, 'board_size', 0)
        partnerships = self._safe_get(org, 'partnerships_count', 0)

        score = 0.5

        if board_size > 12:
            score += 0.2
        elif board_size > 7:
            score += 0.1

        if partnerships > 5:
            score += 0.2
        elif partnerships > 2:
            score += 0.1

        return min(1.0, score)

    def _calculate_compliance(self, org: Dict) -> float:
        """Check compliance status."""
        has_501c3 = self._safe_get(org, 'has_501c3', False)
        audit_current = self._safe_get(org, 'audit_current', False)

        score = 0.7

        if has_501c3:
            score += 0.2

        if audit_current:
            score += 0.1

        return min(1.0, score)


class AnalyzeStageScorer(BaseStageScorer):
    """ANALYZE stage scoring - competitive analysis."""

    def calculate_dimensions(
        self,
        opportunity: Dict[str, Any],
        organization: Dict[str, Any],
        weights: Dict[str, float],
        track_type: Optional[TrackType]
    ) -> List[DimensionalScore]:
        """Calculate ANALYZE dimensions."""

        dimensions = []

        # Competitive Position (0.30)
        dimensions.append(self._create_dimensional_score(
            "competitive_position",
            0.7,  # Placeholder
            weights.get("competitive_position", 0.30),
            data_quality=0.6
        ))

        # Strategic Alignment (0.25)
        dimensions.append(self._create_dimensional_score(
            "strategic_alignment",
            0.75,  # Placeholder
            weights.get("strategic_alignment", 0.25),
            data_quality=0.75
        ))

        # Risk Profile (0.20)
        dimensions.append(self._create_dimensional_score(
            "risk_profile",
            0.65,  # Placeholder
            weights.get("risk_profile", 0.20),
            data_quality=0.7
        ))

        # Implementation Feasibility (0.15)
        dimensions.append(self._create_dimensional_score(
            "implementation_feasibility",
            0.7,  # Placeholder
            weights.get("implementation_feasibility", 0.15),
            data_quality=0.65
        ))

        # ROI Potential (0.10)
        dimensions.append(self._create_dimensional_score(
            "roi_potential",
            0.8,  # Placeholder
            weights.get("roi_potential", 0.10),
            data_quality=0.7
        ))

        return dimensions


class ExamineStageScorer(BaseStageScorer):
    """EXAMINE stage scoring - deep intelligence quality."""

    def calculate_dimensions(
        self,
        opportunity: Dict[str, Any],
        organization: Dict[str, Any],
        weights: Dict[str, float],
        track_type: Optional[TrackType]
    ) -> List[DimensionalScore]:
        """Calculate EXAMINE dimensions."""

        dimensions = []

        # Deep Intelligence Quality (0.30)
        dimensions.append(self._create_dimensional_score(
            "deep_intelligence_quality",
            0.8,  # Placeholder
            weights.get("deep_intelligence_quality", 0.30),
            data_quality=0.85
        ))

        # Relationship Pathways (0.25)
        dimensions.append(self._create_dimensional_score(
            "relationship_pathways",
            0.7,  # Placeholder
            weights.get("relationship_pathways", 0.25),
            data_quality=0.7
        ))

        # Strategic Fit (0.20)
        dimensions.append(self._create_dimensional_score(
            "strategic_fit",
            0.85,  # Placeholder
            weights.get("strategic_fit", 0.20),
            data_quality=0.8
        ))

        # Partnership Potential (0.15)
        dimensions.append(self._create_dimensional_score(
            "partnership_potential",
            0.75,  # Placeholder
            weights.get("partnership_potential", 0.15),
            data_quality=0.65
        ))

        # Innovation Opportunity (0.10)
        dimensions.append(self._create_dimensional_score(
            "innovation_opportunity",
            0.7,  # Placeholder
            weights.get("innovation_opportunity", 0.10),
            data_quality=0.6
        ))

        return dimensions


class ApproachStageScorer(BaseStageScorer):
    """APPROACH stage scoring - final decision synthesis."""

    def calculate_dimensions(
        self,
        opportunity: Dict[str, Any],
        organization: Dict[str, Any],
        weights: Dict[str, float],
        track_type: Optional[TrackType]
    ) -> List[DimensionalScore]:
        """Calculate APPROACH dimensions."""

        dimensions = []

        # Overall Viability (0.30)
        dimensions.append(self._create_dimensional_score(
            "overall_viability",
            0.75,  # Placeholder
            weights.get("overall_viability", 0.30),
            data_quality=0.85
        ))

        # Success Probability (0.25)
        dimensions.append(self._create_dimensional_score(
            "success_probability",
            0.8,  # Placeholder
            weights.get("success_probability", 0.25),
            data_quality=0.8
        ))

        # Strategic Value (0.20)
        dimensions.append(self._create_dimensional_score(
            "strategic_value",
            0.85,  # Placeholder
            weights.get("strategic_value", 0.20),
            data_quality=0.75
        ))

        # Resource Requirements (0.15)
        dimensions.append(self._create_dimensional_score(
            "resource_requirements",
            0.7,  # Placeholder
            weights.get("resource_requirements", 0.15),
            data_quality=0.7
        ))

        # Timeline Feasibility (0.10)
        dimensions.append(self._create_dimensional_score(
            "timeline_feasibility",
            0.75,  # Placeholder
            weights.get("timeline_feasibility", 0.10),
            data_quality=0.9
        ))

        return dimensions
