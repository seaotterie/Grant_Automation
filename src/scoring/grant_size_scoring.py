"""
Grant-Size Realism Bands (V2.0)

Revenue-proportional scoring to ensure grant recommendations match organizational
capacity. Prevents recommending $5M grants to $100K organizations and vice versa.

Key Concepts:
- **Realism Bands**: Grant size categories based on applicant revenue
- **Revenue Proportionality**: Typical grants should be 5-50% of annual budget
- **Capacity Scoring**: Penalize unrealistic grant sizes (too large or too small)
- **Match Multipliers**: Boost scores for optimal grant-to-revenue ratios

Phase 2, Week 4-5 Implementation
Expected Impact: 15-20% improvement in applicant success rates
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .scoring_config import GRANT_SIZE_BANDS


logger = logging.getLogger(__name__)


class GrantSizeBand(str, Enum):
    """Grant size categories based on award amount"""
    MICRO = "micro"          # < $5K
    SMALL = "small"          # $5K - $25K
    MEDIUM = "medium"        # $25K - $100K
    LARGE = "large"          # $100K - $500K
    MAJOR = "major"          # $500K - $2M
    TRANSFORMATIONAL = "transformational"  # > $2M


class CapacityLevel(str, Enum):
    """Organizational capacity levels based on revenue"""
    GRASSROOTS = "grassroots"        # < $100K revenue
    EMERGING = "emerging"            # $100K - $500K
    ESTABLISHED = "established"      # $500K - $2M
    MATURE = "mature"                # $2M - $10M
    MAJOR_INSTITUTION = "major"      # > $10M


class GrantSizeFit(str, Enum):
    """Quality of grant size fit for organization"""
    OPTIMAL = "optimal"              # Perfect fit (5-25% of budget)
    GOOD = "good"                    # Good fit (3-5% or 25-40% of budget)
    ACCEPTABLE = "acceptable"        # Acceptable (1-3% or 40-60% of budget)
    STRETCH = "stretch"              # Challenging but possible (60-100% of budget)
    UNREALISTIC_TOO_LARGE = "unrealistic_large"   # Grant > budget (very hard to manage)
    UNREALISTIC_TOO_SMALL = "unrealistic_small"   # Grant < 1% of budget (not worth effort)


@dataclass
class GrantSizeAnalysis:
    """Analysis of grant size fit for organization"""
    grant_amount: float
    org_revenue: float

    # Categorization
    grant_size_band: GrantSizeBand
    capacity_level: CapacityLevel

    # Fit analysis
    grant_to_revenue_ratio: float  # Grant as % of revenue
    fit_level: GrantSizeFit

    # Scoring
    fit_score: float  # 0.0-1.0, higher = better fit
    multiplier: float  # Score multiplier (0.5-1.5)

    # Explanation
    explanation: str
    recommendations: str


class GrantSizeScorer:
    """
    Revenue-proportional grant size scoring system

    Scoring Logic:
    1. Categorize grant into size bands (micro → transformational)
    2. Categorize organization into capacity levels (grassroots → major)
    3. Calculate grant-to-revenue ratio
    4. Determine fit level (optimal → unrealistic)
    5. Apply scoring multipliers based on fit

    Optimal Ratios:
    - Sweet spot: 5-25% of annual budget
    - Good fit: 3-5% or 25-40%
    - Acceptable: 1-3% or 40-60%
    - Stretch: 60-100% (challenging but possible)
    - Unrealistic: <1% (too small) or >100% (too large)
    """

    def __init__(self):
        """Initialize grant size scorer"""
        self.logger = logging.getLogger(f"{__name__}.GrantSizeScorer")

    def analyze_grant_fit(self,
                         grant_amount: float,
                         org_revenue: float) -> GrantSizeAnalysis:
        """
        Analyze how well grant size fits organization's capacity

        Args:
            grant_amount: Grant award amount ($)
            org_revenue: Organization's annual revenue ($)

        Returns:
            GrantSizeAnalysis with fit scoring and recommendations
        """
        # Categorize grant and organization
        grant_band = self._categorize_grant_size(grant_amount)
        capacity_level = self._categorize_capacity(org_revenue)

        # Calculate ratio
        ratio = grant_amount / org_revenue if org_revenue > 0 else float('inf')

        # Determine fit level
        fit_level = self._determine_fit_level(ratio)

        # Calculate scores
        fit_score = self._calculate_fit_score(ratio, fit_level)
        multiplier = self._calculate_multiplier(fit_level, ratio)

        # Generate explanation
        explanation = self._generate_explanation(
            grant_amount, org_revenue, ratio, fit_level
        )
        recommendations = self._generate_recommendations(
            grant_band, capacity_level, fit_level, ratio
        )

        return GrantSizeAnalysis(
            grant_amount=grant_amount,
            org_revenue=org_revenue,
            grant_size_band=grant_band,
            capacity_level=capacity_level,
            grant_to_revenue_ratio=ratio,
            fit_level=fit_level,
            fit_score=fit_score,
            multiplier=multiplier,
            explanation=explanation,
            recommendations=recommendations,
        )

    def _categorize_grant_size(self, amount: float) -> GrantSizeBand:
        """Categorize grant into size band"""
        if amount < 5_000:
            return GrantSizeBand.MICRO
        elif amount < 25_000:
            return GrantSizeBand.SMALL
        elif amount < 100_000:
            return GrantSizeBand.MEDIUM
        elif amount < 500_000:
            return GrantSizeBand.LARGE
        elif amount < 2_000_000:
            return GrantSizeBand.MAJOR
        else:
            return GrantSizeBand.TRANSFORMATIONAL

    def _categorize_capacity(self, revenue: float) -> CapacityLevel:
        """Categorize organization into capacity level"""
        if revenue < 100_000:
            return CapacityLevel.GRASSROOTS
        elif revenue < 500_000:
            return CapacityLevel.EMERGING
        elif revenue < 2_000_000:
            return CapacityLevel.ESTABLISHED
        elif revenue < 10_000_000:
            return CapacityLevel.MATURE
        else:
            return CapacityLevel.MAJOR_INSTITUTION

    def _determine_fit_level(self, ratio: float) -> GrantSizeFit:
        """
        Determine fit level based on grant-to-revenue ratio

        Optimal: 5-25% (sweet spot for most organizations)
        Good: 3-5% or 25-40% (slightly below/above optimal)
        Acceptable: 1-3% or 40-60% (manageable but not ideal)
        Stretch: 60-100% (challenging, requires significant capacity)
        Unrealistic Large: >100% (exceeds annual budget)
        Unrealistic Small: <1% (not worth administrative overhead)
        """
        if ratio > 1.0:  # Grant exceeds annual budget
            return GrantSizeFit.UNREALISTIC_TOO_LARGE
        elif ratio < 0.01:  # Grant is < 1% of budget
            return GrantSizeFit.UNREALISTIC_TOO_SMALL
        elif 0.05 <= ratio <= 0.25:  # 5-25% - optimal range
            return GrantSizeFit.OPTIMAL
        elif (0.03 <= ratio < 0.05) or (0.25 < ratio <= 0.40):  # Good but not perfect
            return GrantSizeFit.GOOD
        elif (0.01 <= ratio < 0.03) or (0.40 < ratio <= 0.60):  # Acceptable
            return GrantSizeFit.ACCEPTABLE
        elif 0.60 < ratio <= 1.0:  # Stretch goal
            return GrantSizeFit.STRETCH
        else:
            return GrantSizeFit.UNREALISTIC_TOO_SMALL

    def _calculate_fit_score(self, ratio: float, fit_level: GrantSizeFit) -> float:
        """
        Calculate fit score (0.0-1.0) based on ratio and fit level

        Uses Gaussian-like curve centered on 15% (optimal ratio)
        """
        if fit_level == GrantSizeFit.UNREALISTIC_TOO_LARGE:
            return 0.0
        elif fit_level == GrantSizeFit.UNREALISTIC_TOO_SMALL:
            return 0.1
        elif fit_level == GrantSizeFit.STRETCH:
            return 0.5
        elif fit_level == GrantSizeFit.ACCEPTABLE:
            return 0.7
        elif fit_level == GrantSizeFit.GOOD:
            return 0.85
        elif fit_level == GrantSizeFit.OPTIMAL:
            # Peak at 15% ratio
            optimal_ratio = 0.15
            distance = abs(ratio - optimal_ratio)
            # Gaussian curve: score decreases as distance from optimal increases
            score = 1.0 - (distance / 0.10)  # Normalize by 10% range
            return max(0.85, min(1.0, score))
        else:
            return 0.5

    def _calculate_multiplier(self, fit_level: GrantSizeFit, ratio: float) -> float:
        """
        Calculate score multiplier (0.5-1.5) based on fit level

        Multipliers:
        - Optimal: 1.3-1.5x (boost for perfect fit)
        - Good: 1.1-1.2x (small boost)
        - Acceptable: 1.0x (neutral)
        - Stretch: 0.85x (small penalty)
        - Unrealistic: 0.5-0.7x (significant penalty)
        """
        if fit_level == GrantSizeFit.OPTIMAL:
            # Higher boost for ratio closer to 15%
            optimal_ratio = 0.15
            distance = abs(ratio - optimal_ratio)
            multiplier = 1.5 - (distance * 2.0)  # Max 1.5x at 15%, decreases with distance
            return max(1.3, min(1.5, multiplier))
        elif fit_level == GrantSizeFit.GOOD:
            return 1.15
        elif fit_level == GrantSizeFit.ACCEPTABLE:
            return 1.0
        elif fit_level == GrantSizeFit.STRETCH:
            return 0.85
        elif fit_level == GrantSizeFit.UNREALISTIC_TOO_LARGE:
            return 0.5
        elif fit_level == GrantSizeFit.UNREALISTIC_TOO_SMALL:
            return 0.7
        else:
            return 1.0

    def _generate_explanation(self,
                             grant_amount: float,
                             org_revenue: float,
                             ratio: float,
                             fit_level: GrantSizeFit) -> str:
        """Generate human-readable explanation of fit"""
        grant_str = f"${grant_amount:,.0f}"
        revenue_str = f"${org_revenue:,.0f}"
        ratio_pct = f"{ratio * 100:.1f}%"

        if fit_level == GrantSizeFit.OPTIMAL:
            return (
                f"{grant_str} grant is {ratio_pct} of {revenue_str} budget - "
                f"OPTIMAL fit. This is the sweet spot for organizational capacity."
            )
        elif fit_level == GrantSizeFit.GOOD:
            return (
                f"{grant_str} grant is {ratio_pct} of {revenue_str} budget - "
                f"GOOD fit. Slightly outside optimal range but still manageable."
            )
        elif fit_level == GrantSizeFit.ACCEPTABLE:
            return (
                f"{grant_str} grant is {ratio_pct} of {revenue_str} budget - "
                f"ACCEPTABLE fit. Worth pursuing but may require planning."
            )
        elif fit_level == GrantSizeFit.STRETCH:
            return (
                f"{grant_str} grant is {ratio_pct} of {revenue_str} budget - "
                f"STRETCH goal. Challenging to manage; requires significant capacity."
            )
        elif fit_level == GrantSizeFit.UNREALISTIC_TOO_LARGE:
            return (
                f"{grant_str} grant EXCEEDS {revenue_str} annual budget - "
                f"UNREALISTIC. Organization likely cannot manage this award size."
            )
        else:  # UNREALISTIC_TOO_SMALL
            return (
                f"{grant_str} grant is only {ratio_pct} of {revenue_str} budget - "
                f"Too small. Administrative overhead may not justify pursuit."
            )

    def _generate_recommendations(self,
                                 grant_band: GrantSizeBand,
                                 capacity_level: CapacityLevel,
                                 fit_level: GrantSizeFit,
                                 ratio: float) -> str:
        """Generate strategic recommendations"""
        if fit_level == GrantSizeFit.OPTIMAL:
            return "Excellent match. Prioritize this opportunity - high success probability."

        elif fit_level == GrantSizeFit.GOOD:
            if ratio < 0.05:
                return "Consider bundling with other small grants or using as supplemental funding."
            else:
                return "Good opportunity. Ensure you have capacity for program expansion."

        elif fit_level == GrantSizeFit.ACCEPTABLE:
            if ratio < 0.03:
                return "May not be worth effort unless strategically important or very high win probability."
            else:
                return "Feasible but requires careful planning. Assess internal capacity before applying."

        elif fit_level == GrantSizeFit.STRETCH:
            return (
                "Very challenging. Only pursue if: (1) strategic priority, (2) willing to hire staff, "
                "(3) have fiscal sponsor support, or (4) partnering with larger organization."
            )

        elif fit_level == GrantSizeFit.UNREALISTIC_TOO_LARGE:
            return (
                "Not recommended. Consider: (1) requesting smaller amount, (2) multi-year award, "
                "(3) partnership with fiscal sponsor, or (4) skip this opportunity."
            )

        else:  # UNREALISTIC_TOO_SMALL
            return (
                "Low priority. Only pursue if: (1) no-narrative/simple application, "
                "(2) very high win probability, or (3) relationship-building opportunity."
            )


def score_grant_size_fit(grant_amount: float,
                        org_revenue: float) -> Tuple[float, float]:
    """
    Convenience function for grant size scoring

    Args:
        grant_amount: Grant award amount ($)
        org_revenue: Organization's annual revenue ($)

    Returns:
        Tuple of (fit_score, multiplier)
        - fit_score: 0.0-1.0 quality of fit
        - multiplier: 0.5-1.5 score adjustment factor
    """
    scorer = GrantSizeScorer()
    analysis = scorer.analyze_grant_fit(grant_amount, org_revenue)
    return analysis.fit_score, analysis.multiplier


def get_recommended_grant_range(org_revenue: float) -> Tuple[float, float]:
    """
    Get recommended grant range for organization

    Args:
        org_revenue: Organization's annual revenue ($)

    Returns:
        Tuple of (min_recommended, max_recommended) grant amounts
        Based on 5-25% of annual budget (optimal range)
    """
    min_grant = org_revenue * 0.05
    max_grant = org_revenue * 0.25

    return min_grant, max_grant
