"""
Reliability Safeguards (V2.0)

Three-part safeguard system to prevent recommending unreliable foundations:
1. **Filing Recency**: Penalty for old 990-PF filings (potential inactivity)
2. **Mirage Guard**: Penalty for insufficient grant history (unproven grantmakers)
3. **Geographic Border Bonus**: Boost for foundations near state borders

Key Concepts:
- **Filing Recency Penalty**: 0.0 (current year) → -0.15 (5+ years old)
- **Mirage Guard**: Requires 3+ years of grant history, penalty for < 3 years
- **Border Bonus**: +0.03 to +0.08 for foundations within 50mi of state borders
- **Data Quality Score**: Composite reliability score (0-100)

Phase 3, Week 7 Implementation
Expected Impact: 8-12% reduction in recommendations of inactive/unreliable foundations
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
import math


logger = logging.getLogger(__name__)


class FilingRecencyLevel(str, Enum):
    """Filing recency categorization"""
    CURRENT = "current"          # 0-1 years old
    RECENT = "recent"            # 1-2 years old
    MODERATE = "moderate"        # 2-3 years old
    OLD = "old"                  # 3-4 years old
    VERY_OLD = "very_old"        # 4-5 years old
    STALE = "stale"              # 5+ years old


class GrantHistoryStatus(str, Enum):
    """Grant-making history status"""
    ESTABLISHED = "established"   # 5+ years of grants
    PROVEN = "proven"            # 3-5 years of grants
    EMERGING = "emerging"        # 1-3 years of grants
    MINIMAL = "minimal"          # <1 year of grants
    UNKNOWN = "unknown"          # No grant history data


class BorderProximity(str, Enum):
    """Distance to state border"""
    ADJACENT = "adjacent"        # <10 miles
    NEAR = "near"                # 10-25 miles
    MODERATE = "moderate"        # 25-50 miles
    FAR = "far"                  # 50-100 miles
    DISTANT = "distant"          # 100+ miles


@dataclass
class FilingRecencyAnalysis:
    """Analysis of 990-PF filing recency"""
    tax_year: int
    years_ago: int
    recency_level: FilingRecencyLevel
    recency_score: float  # 0.0-100.0
    penalty: float        # 0.0-0.15
    explanation: str
    warning: Optional[str] = None


@dataclass
class GrantHistoryAnalysis:
    """Analysis of foundation grant-making history"""
    years_of_grants: int
    total_grants: int
    avg_grants_per_year: float
    history_status: GrantHistoryStatus
    history_score: float  # 0.0-100.0
    penalty: float        # 0.0-0.12
    is_mirage: bool
    explanation: str
    recommendation: str


@dataclass
class BorderProximityAnalysis:
    """Analysis of geographic border proximity"""
    distance_to_border_miles: float
    nearest_border_state: Optional[str]
    proximity_level: BorderProximity
    proximity_score: float  # 0.0-100.0
    boost: float           # 0.0-0.08
    explanation: str
    cross_border_eligible: bool


@dataclass
class ReliabilitySafeguardsResult:
    """Combined reliability safeguards analysis"""
    # Component analyses
    filing_recency: FilingRecencyAnalysis
    grant_history: GrantHistoryAnalysis
    border_proximity: BorderProximityAnalysis

    # Composite metrics
    reliability_score: float      # 0.0-100.0
    total_penalty: float          # 0.0-0.27 (0.15 + 0.12)
    total_boost: float            # 0.0-0.08
    net_adjustment: float         # Combined penalty + boost

    # Flags
    has_reliability_concerns: bool
    concerns: List[str]

    # Recommendation
    overall_assessment: str
    recommendation: str


class ReliabilitySafeguards:
    """
    Three-part reliability safeguard system

    Safeguard 1: Filing Recency Penalty
    - Current year (0-1y): 0.00 penalty, 100 score
    - Recent (1-2y): -0.02 penalty, 85 score
    - Moderate (2-3y): -0.05 penalty, 70 score
    - Old (3-4y): -0.08 penalty, 50 score
    - Very old (4-5y): -0.12 penalty, 30 score
    - Stale (5+y): -0.15 penalty, 10 score

    Safeguard 2: Mirage Guard (Grant History)
    - Established (5+y): 0.00 penalty, 100 score
    - Proven (3-5y): 0.00 penalty, 85 score
    - Emerging (1-3y): -0.05 penalty, 60 score
    - Minimal (<1y): -0.10 penalty, 30 score
    - Unknown (no data): -0.12 penalty, 20 score

    Safeguard 3: Border Proximity Bonus
    - Adjacent (<10mi): +0.08 boost, 100 score
    - Near (10-25mi): +0.05 boost, 75 score
    - Moderate (25-50mi): +0.03 boost, 50 score
    - Far (50-100mi): 0.00 boost, 25 score
    - Distant (100+mi): 0.00 boost, 0 score

    Use Cases:
    - Prevent recommending inactive foundations (old filings)
    - Avoid "mirage" foundations with no proven grant history
    - Boost foundations near borders (cross-state grant opportunities)
    """

    # Minimum grant history requirements
    MIN_YEARS_PROVEN = 3
    MIN_GRANTS_PER_YEAR = 5
    MIN_TOTAL_GRANTS = 10

    # Border proximity thresholds (miles)
    BORDER_ADJACENT = 10
    BORDER_NEAR = 25
    BORDER_MODERATE = 50
    BORDER_FAR = 100

    def __init__(self):
        """Initialize reliability safeguards system"""
        self.logger = logging.getLogger(f"{__name__}.ReliabilitySafeguards")
        self.current_year = datetime.now().year

    def analyze_reliability(self,
                           foundation_ein: str,
                           tax_year: int,
                           grant_history: Optional[List[Dict]] = None,
                           foundation_lat: Optional[float] = None,
                           foundation_lon: Optional[float] = None,
                           state_borders: Optional[Dict[str, List[Tuple[float, float]]]] = None) -> ReliabilitySafeguardsResult:
        """
        Comprehensive reliability analysis with three safeguards

        Args:
            foundation_ein: Foundation EIN
            tax_year: Tax year of most recent 990-PF filing
            grant_history: List of grant records with year/amount
            foundation_lat: Foundation latitude
            foundation_lon: Foundation longitude
            state_borders: Dictionary of state border coordinates

        Returns:
            ReliabilitySafeguardsResult with all three safeguard analyses
        """
        # Safeguard 1: Filing recency
        filing_recency = self.analyze_filing_recency(tax_year)

        # Safeguard 2: Grant history (mirage guard)
        grant_history_analysis = self.analyze_grant_history(grant_history)

        # Safeguard 3: Border proximity
        border_proximity = self.analyze_border_proximity(
            foundation_lat, foundation_lon, state_borders
        )

        # Calculate composite metrics
        reliability_score = self._calculate_reliability_score(
            filing_recency, grant_history_analysis, border_proximity
        )

        total_penalty = filing_recency.penalty + grant_history_analysis.penalty
        total_boost = border_proximity.boost
        net_adjustment = total_boost - total_penalty

        # Identify concerns
        concerns = []
        has_concerns = False

        if filing_recency.recency_level in [FilingRecencyLevel.OLD,
                                            FilingRecencyLevel.VERY_OLD,
                                            FilingRecencyLevel.STALE]:
            concerns.append(f"Old 990-PF filing ({filing_recency.years_ago}y old)")
            has_concerns = True

        if grant_history_analysis.is_mirage:
            concerns.append(f"Insufficient grant history ({grant_history_analysis.years_of_grants}y)")
            has_concerns = True

        # Generate overall assessment
        overall_assessment = self._generate_overall_assessment(
            filing_recency, grant_history_analysis, border_proximity, has_concerns
        )

        recommendation = self._generate_recommendation(
            filing_recency, grant_history_analysis, has_concerns
        )

        return ReliabilitySafeguardsResult(
            filing_recency=filing_recency,
            grant_history=grant_history_analysis,
            border_proximity=border_proximity,
            reliability_score=reliability_score,
            total_penalty=total_penalty,
            total_boost=total_boost,
            net_adjustment=net_adjustment,
            has_reliability_concerns=has_concerns,
            concerns=concerns,
            overall_assessment=overall_assessment,
            recommendation=recommendation,
        )

    def analyze_filing_recency(self, tax_year: int) -> FilingRecencyAnalysis:
        """
        Analyze 990-PF filing recency and calculate penalty

        Piece-wise linear penalty:
        - 0-1 years: 0.00 penalty
        - 1-2 years: -0.02 penalty
        - 2-3 years: -0.05 penalty
        - 3-4 years: -0.08 penalty
        - 4-5 years: -0.12 penalty
        - 5+ years: -0.15 penalty
        """
        years_ago = self.current_year - tax_year

        # Categorize recency level
        if years_ago <= 1:
            recency_level = FilingRecencyLevel.CURRENT
            penalty = 0.00
            recency_score = 100.0
        elif years_ago <= 2:
            recency_level = FilingRecencyLevel.RECENT
            penalty = 0.02
            recency_score = 85.0
        elif years_ago <= 3:
            recency_level = FilingRecencyLevel.MODERATE
            penalty = 0.05
            recency_score = 70.0
        elif years_ago <= 4:
            recency_level = FilingRecencyLevel.OLD
            penalty = 0.08
            recency_score = 50.0
        elif years_ago <= 5:
            recency_level = FilingRecencyLevel.VERY_OLD
            penalty = 0.12
            recency_score = 30.0
        else:
            recency_level = FilingRecencyLevel.STALE
            penalty = 0.15
            recency_score = 10.0

        # Generate explanation
        if years_ago == 0:
            explanation = f"Current tax year - filing is up to date"
        elif years_ago == 1:
            explanation = f"Recent filing ({years_ago} year old) - good currency"
        elif years_ago <= 2:
            explanation = f"Moderately recent filing ({years_ago} years old)"
        elif years_ago <= 3:
            explanation = f"Filing is {years_ago} years old - may be outdated"
        else:
            explanation = f"Filing is {years_ago} years old - significant staleness concern"

        # Warning for very old filings
        warning = None
        if years_ago >= 4:
            warning = f"⚠️ Foundation may be inactive - {years_ago}y old filing"

        return FilingRecencyAnalysis(
            tax_year=tax_year,
            years_ago=years_ago,
            recency_level=recency_level,
            recency_score=recency_score,
            penalty=penalty,
            explanation=explanation,
            warning=warning,
        )

    def analyze_grant_history(self,
                             grant_history: Optional[List[Dict]]) -> GrantHistoryAnalysis:
        """
        Analyze grant-making history (Mirage Guard)

        Mirage Definition: Foundation with <3 years of grant history or
        <5 grants per year on average. These foundations may not be
        reliable/established grantmakers.

        Penalty Structure:
        - Established (5+y, 5+/y): 0.00 penalty, 100 score
        - Proven (3-5y, 5+/y): 0.00 penalty, 85 score
        - Emerging (1-3y): -0.05 penalty, 60 score
        - Minimal (<1y): -0.10 penalty, 30 score
        - Unknown (no data): -0.12 penalty, 20 score
        """
        if not grant_history:
            return GrantHistoryAnalysis(
                years_of_grants=0,
                total_grants=0,
                avg_grants_per_year=0.0,
                history_status=GrantHistoryStatus.UNKNOWN,
                history_score=20.0,
                penalty=0.12,
                is_mirage=True,
                explanation="No grant history data available",
                recommendation="Exercise caution - unable to verify grant-making track record",
            )

        # Calculate grant metrics
        total_grants = len(grant_history)

        # Extract years with grants
        years_with_grants = set()
        for grant in grant_history:
            if 'year' in grant:
                years_with_grants.add(grant['year'])

        years_of_grants = len(years_with_grants)

        # Calculate average grants per year
        avg_grants_per_year = total_grants / years_of_grants if years_of_grants > 0 else 0.0

        # Categorize history status
        if years_of_grants >= 5 and avg_grants_per_year >= self.MIN_GRANTS_PER_YEAR:
            history_status = GrantHistoryStatus.ESTABLISHED
            history_score = 100.0
            penalty = 0.00
            is_mirage = False
        elif years_of_grants >= 3 and avg_grants_per_year >= self.MIN_GRANTS_PER_YEAR:
            history_status = GrantHistoryStatus.PROVEN
            history_score = 85.0
            penalty = 0.00
            is_mirage = False
        elif years_of_grants >= 1 and years_of_grants < 3:
            history_status = GrantHistoryStatus.EMERGING
            history_score = 60.0
            penalty = 0.05
            is_mirage = True
        else:  # <1 year
            history_status = GrantHistoryStatus.MINIMAL
            history_score = 30.0
            penalty = 0.10
            is_mirage = True

        # Generate explanation
        if is_mirage:
            explanation = (
                f"⚠️ MIRAGE ALERT: Only {years_of_grants} years of grant history "
                f"({total_grants} total grants, {avg_grants_per_year:.1f}/year). "
                f"Foundation may not be established grantmaker."
            )
        else:
            explanation = (
                f"Established grant history: {years_of_grants} years, "
                f"{total_grants} total grants ({avg_grants_per_year:.1f}/year)"
            )

        # Generate recommendation
        if history_status == GrantHistoryStatus.ESTABLISHED:
            recommendation = "Excellent - Established grant-making track record. Reliable foundation."
        elif history_status == GrantHistoryStatus.PROVEN:
            recommendation = "Good - Proven grant-making history. Proceed with confidence."
        elif history_status == GrantHistoryStatus.EMERGING:
            recommendation = "Caution - Emerging foundation with limited history. Verify current status."
        else:
            recommendation = "High Risk - Minimal grant history. Research thoroughly before applying."

        return GrantHistoryAnalysis(
            years_of_grants=years_of_grants,
            total_grants=total_grants,
            avg_grants_per_year=avg_grants_per_year,
            history_status=history_status,
            history_score=history_score,
            penalty=penalty,
            is_mirage=is_mirage,
            explanation=explanation,
            recommendation=recommendation,
        )

    def analyze_border_proximity(self,
                                foundation_lat: Optional[float],
                                foundation_lon: Optional[float],
                                state_borders: Optional[Dict[str, List[Tuple[float, float]]]]) -> BorderProximityAnalysis:
        """
        Analyze proximity to state borders for cross-state opportunities

        Border Proximity Boost:
        - Adjacent (<10mi): +0.08 boost, 100 score
        - Near (10-25mi): +0.05 boost, 75 score
        - Moderate (25-50mi): +0.03 boost, 50 score
        - Far (50-100mi): 0.00 boost, 25 score
        - Distant (100+mi): 0.00 boost, 0 score

        Rationale: Foundations near state borders often fund cross-state
        projects, making them valuable for nonprofits in adjacent states.
        """
        # If no location data, return neutral result
        if foundation_lat is None or foundation_lon is None or not state_borders:
            return BorderProximityAnalysis(
                distance_to_border_miles=float('inf'),
                nearest_border_state=None,
                proximity_level=BorderProximity.DISTANT,
                proximity_score=0.0,
                boost=0.00,
                explanation="No geographic data available for border analysis",
                cross_border_eligible=False,
            )

        # Calculate distance to nearest border
        min_distance = float('inf')
        nearest_state = None

        for state, border_points in state_borders.items():
            for border_lat, border_lon in border_points:
                distance = self._haversine_distance(
                    foundation_lat, foundation_lon,
                    border_lat, border_lon
                )
                if distance < min_distance:
                    min_distance = distance
                    nearest_state = state

        # Categorize proximity
        if min_distance < self.BORDER_ADJACENT:
            proximity_level = BorderProximity.ADJACENT
            proximity_score = 100.0
            boost = 0.08
        elif min_distance < self.BORDER_NEAR:
            proximity_level = BorderProximity.NEAR
            proximity_score = 75.0
            boost = 0.05
        elif min_distance < self.BORDER_MODERATE:
            proximity_level = BorderProximity.MODERATE
            proximity_score = 50.0
            boost = 0.03
        elif min_distance < self.BORDER_FAR:
            proximity_level = BorderProximity.FAR
            proximity_score = 25.0
            boost = 0.00
        else:
            proximity_level = BorderProximity.DISTANT
            proximity_score = 0.0
            boost = 0.00

        cross_border_eligible = min_distance < self.BORDER_MODERATE

        # Generate explanation
        if cross_border_eligible:
            explanation = (
                f"Foundation is {min_distance:.1f} miles from {nearest_state} border. "
                f"Cross-state grant opportunities likely."
            )
        else:
            explanation = (
                f"Foundation is {min_distance:.1f} miles from nearest border. "
                f"Cross-state funding less likely."
            )

        return BorderProximityAnalysis(
            distance_to_border_miles=min_distance,
            nearest_border_state=nearest_state,
            proximity_level=proximity_level,
            proximity_score=proximity_score,
            boost=boost,
            explanation=explanation,
            cross_border_eligible=cross_border_eligible,
        )

    def _haversine_distance(self,
                           lat1: float, lon1: float,
                           lat2: float, lon2: float) -> float:
        """
        Calculate distance between two lat/lon points in miles

        Uses Haversine formula for great-circle distance
        """
        # Earth radius in miles
        R = 3959.0

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def _calculate_reliability_score(self,
                                    filing: FilingRecencyAnalysis,
                                    history: GrantHistoryAnalysis,
                                    border: BorderProximityAnalysis) -> float:
        """
        Calculate composite reliability score

        Weighted average:
        - Filing recency: 40%
        - Grant history: 50%
        - Border proximity: 10%
        """
        reliability_score = (
            filing.recency_score * 0.40 +
            history.history_score * 0.50 +
            border.proximity_score * 0.10
        )

        return round(reliability_score, 2)

    def _generate_overall_assessment(self,
                                    filing: FilingRecencyAnalysis,
                                    history: GrantHistoryAnalysis,
                                    border: BorderProximityAnalysis,
                                    has_concerns: bool) -> str:
        """Generate overall reliability assessment"""
        if not has_concerns:
            if border.cross_border_eligible:
                return "EXCELLENT: Current filing, proven grant history, near state border - highly reliable"
            else:
                return "GOOD: Current filing and proven grant history - reliable foundation"
        else:
            concerns_list = []
            if filing.recency_level in [FilingRecencyLevel.OLD, FilingRecencyLevel.VERY_OLD, FilingRecencyLevel.STALE]:
                concerns_list.append(f"{filing.years_ago}y old filing")
            if history.is_mirage:
                concerns_list.append(f"{history.years_of_grants}y grant history")

            concerns_str = ", ".join(concerns_list)
            return f"⚠️ CONCERNS: {concerns_str} - verify foundation is still active"

    def _generate_recommendation(self,
                                filing: FilingRecencyAnalysis,
                                history: GrantHistoryAnalysis,
                                has_concerns: bool) -> str:
        """Generate strategic recommendation"""
        if not has_concerns:
            return "Proceed - Foundation passes all reliability safeguards"

        if filing.years_ago >= 4 or history.is_mirage:
            return "CAUTION: Research foundation's current status before applying. May be inactive."

        return "Verify foundation is currently accepting applications before investing time"


def analyze_reliability_safeguards(foundation_ein: str,
                                  tax_year: int,
                                  grant_history: Optional[List[Dict]] = None,
                                  foundation_lat: Optional[float] = None,
                                  foundation_lon: Optional[float] = None,
                                  state_borders: Optional[Dict[str, List[Tuple[float, float]]]] = None) -> ReliabilitySafeguardsResult:
    """
    Convenience function for reliability safeguards analysis

    Args:
        foundation_ein: Foundation EIN
        tax_year: Tax year of most recent 990-PF filing
        grant_history: List of grant records with year/amount
        foundation_lat: Foundation latitude
        foundation_lon: Foundation longitude
        state_borders: Dictionary of state border coordinates

    Returns:
        ReliabilitySafeguardsResult with all three safeguard analyses
    """
    safeguards = ReliabilitySafeguards()
    return safeguards.analyze_reliability(
        foundation_ein,
        tax_year,
        grant_history,
        foundation_lat,
        foundation_lon,
        state_borders,
    )
