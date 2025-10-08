"""
Payout Sufficiency Scoring (5% Rule Analysis)

Scores private foundations based on IRS 5% payout requirement compliance.
Foundations must distribute ≥5% of average net investment assets annually for
charitable purposes. Higher payout ratios indicate more active grant-making.

Key Concepts:
- **5% Rule**: IRS requirement for private non-operating foundations
- **Payout Ratio**: Qualifying distributions ÷ Minimum investment return
- **Distribution Score**: How much foundation gives relative to requirements
- **Grant Capacity**: Available funding based on historical payout patterns

Phase 3, Week 7 Implementation
Expected Impact: 10-15% improvement in identifying active grantmakers
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional


logger = logging.getLogger(__name__)


class PayoutCompliance(str, Enum):
    """Foundation payout compliance level"""
    EXCESSIVE = "excessive"        # >10% payout (very generous)
    HIGH = "high"                  # 7-10% payout (generous)
    COMPLIANT = "compliant"        # 5-7% payout (meets requirement)
    MINIMAL = "minimal"            # 4-5% payout (barely meets/below)
    NONCOMPLIANT = "noncompliant"  # <4% payout (concerning)
    UNKNOWN = "unknown"            # Missing data


class GrantActivity(str, Enum):
    """Foundation grant-making activity level"""
    VERY_ACTIVE = "very_active"    # High payout, frequent grants
    ACTIVE = "active"              # Good payout, regular grants
    MODERATE = "moderate"          # Meets requirements
    LIMITED = "limited"            # Minimal activity
    INACTIVE = "inactive"          # Below requirements or no recent grants
    UNKNOWN = "unknown"            # Insufficient data


@dataclass
class PayoutAnalysis:
    """Analysis of foundation payout compliance"""
    foundation_ein: str

    # Financial data (from 990-PF Part XIII)
    minimum_investment_return: Optional[float]  # Min return required for payout calc
    qualifying_distributions: Optional[float]   # Actual charitable distributions
    distributable_amount: Optional[float]       # Required minimum distribution
    undistributed_income: Optional[float]       # Income not yet distributed

    # Calculated metrics
    payout_ratio: Optional[float]               # Distributions ÷ Min investment return
    payout_percentage: Optional[float]          # As percentage (e.g., 6.5%)
    excess_distribution: Optional[float]        # Amount above 5% requirement

    # Compliance assessment
    compliance_level: PayoutCompliance
    activity_level: GrantActivity

    # Scoring
    payout_score: float  # 0.0-100.0
    capacity_multiplier: float  # 0.5-1.5x adjustment for composite score

    # Explanation
    explanation: str
    recommendation: str


class PayoutSufficiencyScorer:
    """
    5% Rule compliance and payout sufficiency scorer

    Scoring Logic:
    1. Calculate payout ratio (qualifying distributions ÷ min investment return)
    2. Assess compliance level (excessive → noncompliant)
    3. Determine grant activity level
    4. Score based on payout percentage (higher = better)
    5. Apply capacity multiplier for composite scoring

    Payout Ratio Interpretation:
    - >10%: Exceptional generosity (100 points, 1.5x multiplier)
    - 7-10%: Very generous (85-95 points, 1.3x multiplier)
    - 5-7%: Compliant, good activity (70-85 points, 1.0x multiplier)
    - 4-5%: Minimal/borderline (50-70 points, 0.8x multiplier)
    - <4%: Noncompliant, concerning (0-50 points, 0.5x multiplier)

    Data Source: IRS Form 990-PF Part XIII (Undistributed Income)
    """

    def __init__(self):
        """Initialize payout sufficiency scorer"""
        self.logger = logging.getLogger(f"{__name__}.PayoutSufficiencyScorer")

    def analyze_payout(self,
                      foundation_ein: str,
                      minimum_investment_return: Optional[float] = None,
                      qualifying_distributions: Optional[float] = None,
                      distributable_amount: Optional[float] = None,
                      undistributed_income: Optional[float] = None,
                      total_assets: Optional[float] = None) -> PayoutAnalysis:
        """
        Analyze foundation payout compliance and grant-making capacity

        Args:
            foundation_ein: Foundation EIN
            minimum_investment_return: Min return for payout calc (990-PF Part XIII Line 6)
            qualifying_distributions: Charitable distributions (Part XIII Line 1)
            distributable_amount: Required minimum distribution (Part XIII Line 7)
            undistributed_income: Income not yet distributed (Part XIII Line 8)
            total_assets: Total assets (for capacity estimation)

        Returns:
            PayoutAnalysis with compliance assessment and scoring
        """

        # Calculate payout ratio
        payout_ratio = None
        payout_percentage = None

        if minimum_investment_return and qualifying_distributions:
            if minimum_investment_return > 0:
                payout_ratio = qualifying_distributions / minimum_investment_return
                payout_percentage = payout_ratio * 100.0
            else:
                # No investment return = can't calculate ratio
                payout_ratio = None
                payout_percentage = None

        # Calculate excess distribution
        excess_distribution = None
        if qualifying_distributions and distributable_amount:
            excess_distribution = qualifying_distributions - distributable_amount

        # Assess compliance level
        compliance_level = self._assess_compliance(payout_percentage)

        # Assess activity level
        activity_level = self._assess_activity(
            payout_percentage, qualifying_distributions, undistributed_income
        )

        # Calculate score
        payout_score = self._calculate_score(payout_percentage, compliance_level)

        # Calculate capacity multiplier
        capacity_multiplier = self._calculate_multiplier(
            compliance_level, activity_level
        )

        # Generate explanation and recommendation
        explanation = self._generate_explanation(
            payout_percentage, compliance_level, excess_distribution
        )
        recommendation = self._generate_recommendation(
            compliance_level, activity_level, payout_percentage
        )

        return PayoutAnalysis(
            foundation_ein=foundation_ein,
            minimum_investment_return=minimum_investment_return,
            qualifying_distributions=qualifying_distributions,
            distributable_amount=distributable_amount,
            undistributed_income=undistributed_income,
            payout_ratio=payout_ratio,
            payout_percentage=payout_percentage,
            excess_distribution=excess_distribution,
            compliance_level=compliance_level,
            activity_level=activity_level,
            payout_score=payout_score,
            capacity_multiplier=capacity_multiplier,
            explanation=explanation,
            recommendation=recommendation,
        )

    def _assess_compliance(self, payout_percentage: Optional[float]) -> PayoutCompliance:
        """Assess compliance level based on payout percentage"""
        if payout_percentage is None:
            return PayoutCompliance.UNKNOWN

        if payout_percentage >= 10.0:
            return PayoutCompliance.EXCESSIVE
        elif payout_percentage >= 7.0:
            return PayoutCompliance.HIGH
        elif payout_percentage >= 5.0:
            return PayoutCompliance.COMPLIANT
        elif payout_percentage >= 4.0:
            return PayoutCompliance.MINIMAL
        else:
            return PayoutCompliance.NONCOMPLIANT

    def _assess_activity(self,
                        payout_percentage: Optional[float],
                        qualifying_distributions: Optional[float],
                        undistributed_income: Optional[float]) -> GrantActivity:
        """Assess grant-making activity level"""

        if payout_percentage is None:
            return GrantActivity.UNKNOWN

        # High payout = very active
        if payout_percentage >= 8.0:
            return GrantActivity.VERY_ACTIVE

        # Good payout + low undistributed income = active
        if payout_percentage >= 6.0:
            if undistributed_income is None or undistributed_income <= 0:
                return GrantActivity.ACTIVE
            else:
                return GrantActivity.MODERATE

        # Compliant range = moderate
        if payout_percentage >= 5.0:
            return GrantActivity.MODERATE

        # Minimal/borderline = limited
        if payout_percentage >= 4.0:
            return GrantActivity.LIMITED

        # Below requirement = inactive
        return GrantActivity.INACTIVE

    def _calculate_score(self,
                        payout_percentage: Optional[float],
                        compliance_level: PayoutCompliance) -> float:
        """
        Calculate payout score (0-100)

        Uses piece-wise linear scoring:
        - 0-4%: 0-50 points (linear)
        - 4-5%: 50-70 points (linear)
        - 5-7%: 70-85 points (linear)
        - 7-10%: 85-95 points (linear)
        - 10%+: 95-100 points (capped)
        """
        if payout_percentage is None:
            return 50.0  # Neutral score for missing data

        if payout_percentage < 4.0:
            # 0-4%: 0-50 points
            return (payout_percentage / 4.0) * 50.0

        elif payout_percentage < 5.0:
            # 4-5%: 50-70 points
            progress = (payout_percentage - 4.0) / 1.0
            return 50.0 + (progress * 20.0)

        elif payout_percentage < 7.0:
            # 5-7%: 70-85 points
            progress = (payout_percentage - 5.0) / 2.0
            return 70.0 + (progress * 15.0)

        elif payout_percentage < 10.0:
            # 7-10%: 85-95 points
            progress = (payout_percentage - 7.0) / 3.0
            return 85.0 + (progress * 10.0)

        else:
            # 10%+: 95-100 points
            return min(100.0, 95.0 + (payout_percentage - 10.0))

    def _calculate_multiplier(self,
                             compliance_level: PayoutCompliance,
                             activity_level: GrantActivity) -> float:
        """
        Calculate capacity multiplier (0.5-1.5x) for composite scoring

        Higher payout = more grant capacity = boost to overall score
        Lower payout = limited capacity = penalty to overall score
        """
        # Base multiplier from compliance
        if compliance_level == PayoutCompliance.EXCESSIVE:
            base = 1.5
        elif compliance_level == PayoutCompliance.HIGH:
            base = 1.3
        elif compliance_level == PayoutCompliance.COMPLIANT:
            base = 1.0
        elif compliance_level == PayoutCompliance.MINIMAL:
            base = 0.8
        elif compliance_level == PayoutCompliance.NONCOMPLIANT:
            base = 0.5
        else:  # UNKNOWN
            base = 0.9  # Small penalty for missing data

        # Adjust based on activity level
        if activity_level == GrantActivity.VERY_ACTIVE:
            return min(1.5, base + 0.1)
        elif activity_level == GrantActivity.INACTIVE:
            return max(0.5, base - 0.1)
        else:
            return base

    def _generate_explanation(self,
                             payout_percentage: Optional[float],
                             compliance_level: PayoutCompliance,
                             excess_distribution: Optional[float]) -> str:
        """Generate human-readable explanation"""

        if payout_percentage is None:
            return "Payout data not available - cannot assess grant-making activity"

        payout_str = f"{payout_percentage:.1f}%"

        if compliance_level == PayoutCompliance.EXCESSIVE:
            excess_str = f"${excess_distribution:,.0f}" if excess_distribution else "substantial amount"
            return (
                f"Exceptional payout ratio ({payout_str}) - {excess_str} above 5% requirement. "
                f"Foundation is very generous and actively grant-making."
            )

        elif compliance_level == PayoutCompliance.HIGH:
            return (
                f"High payout ratio ({payout_str}) - significantly exceeds 5% requirement. "
                f"Foundation shows strong commitment to grant-making."
            )

        elif compliance_level == PayoutCompliance.COMPLIANT:
            return (
                f"Compliant payout ratio ({payout_str}) - meets 5% requirement with margin. "
                f"Foundation is actively distributing funds as required."
            )

        elif compliance_level == PayoutCompliance.MINIMAL:
            return (
                f"Minimal payout ratio ({payout_str}) - barely meets or slightly below 5% requirement. "
                f"Foundation may have limited grant-making capacity."
            )

        else:  # NONCOMPLIANT
            return (
                f"Low payout ratio ({payout_str}) - below 5% requirement. "
                f"Foundation may be inactive or have compliance issues. Proceed with caution."
            )

    def _generate_recommendation(self,
                                compliance_level: PayoutCompliance,
                                activity_level: GrantActivity,
                                payout_percentage: Optional[float]) -> str:
        """Generate strategic recommendation"""

        if compliance_level == PayoutCompliance.EXCESSIVE:
            return (
                "Excellent opportunity - foundation has strong grant-making capacity. "
                "Prioritize this foundation in your outreach."
            )

        elif compliance_level == PayoutCompliance.HIGH:
            return (
                "Good opportunity - foundation is actively distributing funds. "
                "Strong candidate for grant applications."
            )

        elif compliance_level == PayoutCompliance.COMPLIANT:
            return (
                "Solid opportunity - foundation meets requirements and shows regular activity. "
                "Proceed with standard application process."
            )

        elif compliance_level == PayoutCompliance.MINIMAL:
            return (
                "Borderline opportunity - foundation has limited distribution history. "
                "Verify recent grant-making activity before investing significant effort."
            )

        elif compliance_level == PayoutCompliance.NONCOMPLIANT:
            return (
                "Risky opportunity - foundation below payout requirements. "
                "May be inactive, in transition, or facing compliance issues. "
                "Consider deprioritizing unless other strong indicators exist."
            )

        else:  # UNKNOWN
            return (
                "Data incomplete - cannot assess payout compliance. "
                "Request 990-PF Part XIII data or deprioritize if unavailable."
            )


def score_payout_sufficiency(minimum_investment_return: Optional[float],
                            qualifying_distributions: Optional[float]) -> tuple[float, float]:
    """
    Convenience function for payout scoring

    Args:
        minimum_investment_return: Min return for payout calc
        qualifying_distributions: Actual charitable distributions

    Returns:
        Tuple of (score 0-100, multiplier 0.5-1.5x)
    """
    scorer = PayoutSufficiencyScorer()
    analysis = scorer.analyze_payout(
        foundation_ein="UNKNOWN",
        minimum_investment_return=minimum_investment_return,
        qualifying_distributions=qualifying_distributions,
    )
    return analysis.payout_score, analysis.capacity_multiplier
