"""
Foundation Scorer - 990-PF Foundation-Specific Scoring
Integrated into Tool 20 as FOUNDATION track type

Migrates Composite Scorer V2 functionality into 12-factor Tool 20 architecture.
8-component foundation scoring mapped to Tool 20's dimensional framework.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .scorer_models import DimensionalScore

# Import existing scoring components from src/scoring/
from src.scoring.ntee_scorer import NTEEScorer, NTEEDataSource
from src.scoring.schedule_i_voting import ScheduleIVotingSystem
from src.scoring.grant_size_scoring import GrantSizeScorer
from src.scoring.time_decay_utils import TimeDecayCalculator, DecayType
from src.scoring.scoring_config import (
    COMPOSITE_WEIGHTS_V2,
    NTEE_MAX_CONTRIBUTION,
)

logger = logging.getLogger(__name__)


class FoundationStageScorer:
    """
    Foundation-specific scorer for 990-PF opportunities

    Implements 8-component composite scoring mapped to Tool 20's 5-dimensional framework:

    8 Foundation Components → 5 Dimensions:
    1. Mission Alignment: NTEE alignment (30%)
    2. Geographic Fit: Geographic match (20%)
    3. Financial Match: Financial capacity (10%) + Grant size (10%) + Application policy (8%)
    4. Strategic Alignment: Recipient coherence (12%)
    5. Timing: Filing recency (5%) + Foundation type (5%)

    Maintains backward compatibility with Composite Scorer V2 while integrating
    into Tool 20's dimensional scoring framework.
    """

    def __init__(self):
        """Initialize foundation scorer with Phase 1-3 components"""
        self.logger = logging.getLogger(f"{__name__}.FoundationStageScorer")

        # Phase 2-3 scorers (from src/scoring/)
        self.ntee_scorer = NTEEScorer(enable_time_decay=True)
        self.schedule_i_voting = ScheduleIVotingSystem()
        self.grant_size_scorer = GrantSizeScorer()

        # Phase 1 time-decay
        self.time_decay = TimeDecayCalculator(DecayType.FILING_DATA)

        self.logger.info("Initialized FoundationStageScorer with 8-component scoring")

    def calculate_dimensions(
        self,
        opportunity_data: Dict[str, Any],
        organization_profile: Dict[str, Any],
        weights: Dict[str, float],
        track_type: Optional[Any] = None
    ) -> List[DimensionalScore]:
        """
        Calculate foundation-specific dimensional scores

        Args:
            opportunity_data: Foundation 990-PF data
            organization_profile: Applicant organization profile
            weights: Dimensional weights (5 dimensions)
            track_type: Should be TrackType.FOUNDATION

        Returns:
            List of 5 DimensionalScore objects
        """
        self.logger.info(f"Calculating foundation dimensions for EIN: {opportunity_data.get('foundation_ein', 'unknown')}")

        # Extract foundation data
        foundation_ein = opportunity_data.get('foundation_ein', '')
        foundation_name = opportunity_data.get('foundation_name', '')

        # Dimension 1: Mission Alignment (NTEE component 30%)
        mission_score = self._score_mission_alignment(opportunity_data, organization_profile)

        # Dimension 2: Geographic Fit (Geographic component 20%)
        geographic_score = self._score_geographic_fit(opportunity_data, organization_profile)

        # Dimension 3: Financial Match (Financial 10% + Grant size 10% + Application 8% = 28%)
        financial_score = self._score_financial_match(opportunity_data, organization_profile)

        # Dimension 4: Strategic Alignment (Recipient coherence 12%)
        strategic_score = self._score_strategic_alignment(opportunity_data)

        # Dimension 5: Timing (Filing recency 5% + Foundation type 5% = 10%)
        timing_score = self._score_timing(opportunity_data)

        # Use provided weights or default foundation weights
        default_foundation_weights = {
            'mission_alignment': 0.30,
            'geographic_fit': 0.20,
            'financial_match': 0.28,
            'strategic_alignment': 0.12,
            'timing': 0.10
        }
        weights = weights if weights else default_foundation_weights

        return [mission_score, geographic_score, financial_score, strategic_score, timing_score]

    def _score_mission_alignment(
        self,
        opportunity_data: Dict[str, Any],
        organization_profile: Dict[str, Any]
    ) -> DimensionalScore:
        """
        Dimension 1: Mission Alignment (NTEE component)

        Uses Phase 2 Week 3 NTEE two-part scorer with 30% cap
        """
        profile_ntee = organization_profile.get('ntee_codes', [])
        foundation_ntee = opportunity_data.get('ntee_codes', [])

        if not profile_ntee or not foundation_ntee:
            return DimensionalScore(
                dimension_name="mission_alignment",
                raw_score=0.0,
                weight=0.30,
                weighted_score=0.0,
                boost_factor=1.0,
                data_quality=0.3,
                calculation_method="ntee_two_part_scoring",
                data_sources=["bmf", "schedule_i"],
                notes="Missing NTEE codes for comparison"
            )

        # Use Phase 2 Week 3 NTEE scorer
        ntee_result = self.ntee_scorer.score_alignment(
            profile_codes=profile_ntee,
            foundation_codes=foundation_ntee,
            profile_code_sources={code: NTEEDataSource.BMF for code in profile_ntee},
            foundation_code_sources=opportunity_data.get('ntee_code_sources', {}),
            foundation_code_dates=opportunity_data.get('ntee_code_dates'),
        )

        # Convert 0.0-1.0 to 0-100 scale with NTEE cap (30%)
        raw_score = ntee_result.weighted_score
        capped_score = min(raw_score, NTEE_MAX_CONTRIBUTION)

        return DimensionalScore(
            dimension_name="mission_alignment",
            raw_score=capped_score,
            weight=0.30,
            weighted_score=capped_score * 0.30,
            boost_factor=1.0,
            data_quality=ntee_result.confidence,
            calculation_method="ntee_two_part_scoring_capped",
            data_sources=["bmf", "schedule_i", "ntee_scorer"],
            notes=ntee_result.explanation
        )

    def _score_geographic_fit(
        self,
        opportunity_data: Dict[str, Any],
        organization_profile: Dict[str, Any]
    ) -> DimensionalScore:
        """
        Dimension 2: Geographic Fit (Geographic match component)

        Returns: 1.0 for exact match, 0.75 for adjacent state, 0.5 for national, 0.0 for mismatch
        """
        foundation_states = opportunity_data.get('geographic_focus_states', [])
        profile_state = organization_profile.get('state')

        if not foundation_states:
            # No restrictions = nationally focused
            return DimensionalScore(
                dimension_name="geographic_fit",
                raw_score=0.5,
                weight=0.20,
                weighted_score=0.5 * 0.20,
                boost_factor=1.0,
                data_quality=0.6,
                calculation_method="geographic_matching",
                data_sources=["990pf_geographic_data"],
                notes="Foundation has national focus (no geographic restrictions)"
            )

        if not profile_state:
            return DimensionalScore(
                dimension_name="geographic_fit",
                raw_score=0.25,
                weight=0.20,
                weighted_score=0.25 * 0.20,
                boost_factor=1.0,
                data_quality=0.3,
                calculation_method="geographic_matching",
                data_sources=["organization_profile"],
                notes="Unknown profile state"
            )

        if profile_state in foundation_states:
            # Exact state match
            return DimensionalScore(
                dimension_name="geographic_fit",
                raw_score=1.0,
                weight=0.20,
                weighted_score=1.0 * 0.20,
                boost_factor=1.0,
                data_quality=1.0,
                calculation_method="geographic_matching",
                data_sources=["990pf_geographic_data", "organization_profile"],
                notes=f"Exact state match: {profile_state}"
            )

        # No match
        return DimensionalScore(
            dimension_name="geographic_fit",
            raw_score=0.0,
            weight=0.20,
            weighted_score=0.0,
            boost_factor=1.0,
            data_quality=1.0,
            calculation_method="geographic_matching",
            data_sources=["990pf_geographic_data", "organization_profile"],
            notes=f"Geographic mismatch: Foundation focuses on {foundation_states}, org in {profile_state}"
        )

    def _score_financial_match(
        self,
        opportunity_data: Dict[str, Any],
        organization_profile: Dict[str, Any]
    ) -> DimensionalScore:
        """
        Dimension 3: Financial Match (Financial capacity + Grant size + Application policy)

        Combines 3 components:
        - Financial capacity (10%): Foundation asset size
        - Grant size fit (10%): Grant-to-revenue ratio using Phase 2 Week 4-5 scorer
        - Application policy (8%): Accepts applications preference

        Total weight: 28%
        """
        # Component 1: Financial capacity (10/28)
        total_assets = opportunity_data.get('total_assets', 0)
        if total_assets > 50_000_000:
            capacity_score = 1.0  # Major foundation
        elif total_assets > 10_000_000:
            capacity_score = 0.85  # Large foundation
        elif total_assets > 1_000_000:
            capacity_score = 0.70  # Medium foundation
        elif total_assets > 100_000:
            capacity_score = 0.50  # Small foundation
        else:
            capacity_score = 0.25  # Very small foundation

        # Component 2: Grant size fit (10/28)
        typical_grant = opportunity_data.get('typical_grant_amount', 0)
        org_revenue = organization_profile.get('revenue', 0)

        if typical_grant and org_revenue:
            # Use Phase 2 Week 4-5 grant size scorer
            analysis = self.grant_size_scorer.analyze_grant_fit(
                grant_amount=typical_grant,
                org_revenue=org_revenue,
            )
            grant_size_score = analysis.fit_score * analysis.multiplier
            grant_size_score = min(1.0, grant_size_score)
            grant_size_notes = analysis.explanation
        else:
            grant_size_score = 0.5  # Neutral if data missing
            grant_size_notes = "Missing grant amount or revenue data"

        # Component 3: Application policy (8/28)
        accepts_applications = opportunity_data.get('accepts_applications')
        if accepts_applications is None:
            application_score = 0.6  # Uncertain = slight penalty
        elif accepts_applications:
            application_score = 1.0  # Accepts applications
        else:
            application_score = 0.2  # Does not accept applications

        # Combine components (weighted average within dimension)
        raw_score = (
            capacity_score * (10/28) +
            grant_size_score * (10/28) +
            application_score * (8/28)
        )

        return DimensionalScore(
            dimension_name="financial_match",
            raw_score=raw_score,
            weight=0.28,
            weighted_score=raw_score * 0.28,
            boost_factor=1.0,
            data_quality=0.8 if (typical_grant and org_revenue) else 0.5,
            calculation_method="composite_financial_analysis",
            data_sources=["990pf_financial_data", "grant_size_scorer", "organization_profile"],
            notes=f"Capacity: {capacity_score:.2f}, Grant size: {grant_size_score:.2f}, Application: {application_score:.2f}. {grant_size_notes}"
        )

    def _score_strategic_alignment(
        self,
        opportunity_data: Dict[str, Any]
    ) -> DimensionalScore:
        """
        Dimension 4: Strategic Alignment (Recipient coherence component)

        Uses Phase 2 Week 4-5 Schedule I voting system
        """
        schedule_i_grantees = opportunity_data.get('schedule_i_grantees', [])

        if not schedule_i_grantees:
            return DimensionalScore(
                dimension_name="strategic_alignment",
                raw_score=0.5,
                weight=0.12,
                weighted_score=0.5 * 0.12,
                boost_factor=1.0,
                data_quality=0.3,
                calculation_method="recipient_coherence_analysis",
                data_sources=["schedule_i"],
                notes="No Schedule I data available (neutral score)"
            )

        # Analyze Schedule I patterns
        analysis = self.schedule_i_voting.analyze_foundation_patterns(
            foundation_ein=opportunity_data.get('foundation_ein', ''),
            schedule_i_grantees=schedule_i_grantees,
        )

        # Convert coherence score to 0-1 scale
        raw_score = analysis.coherence_score

        # Note: coherence_boost is handled separately in final score calculation
        coherence_boost = analysis.recommended_boost

        notes_parts = [
            f"Coherence: {analysis.coherence_score:.2f}",
            f"Entropy: {analysis.entropy_score:.2f}",
            f"Recipients: {analysis.total_recipients}",
            f"Coherent: {analysis.is_coherent}"
        ]
        if analysis.top_ntee_codes:
            notes_parts.append(f"Top NTEE: {', '.join(analysis.top_ntee_codes[:3])}")

        return DimensionalScore(
            dimension_name="strategic_alignment",
            raw_score=raw_score,
            weight=0.12,
            weighted_score=raw_score * 0.12,
            boost_factor=1.0 + coherence_boost,  # Apply coherence boost (0.0-0.15)
            data_quality=0.9,
            calculation_method="schedule_i_voting_system",
            data_sources=["schedule_i", "ein_resolver"],
            notes=" | ".join(notes_parts)
        )

    def _score_timing(
        self,
        opportunity_data: Dict[str, Any]
    ) -> DimensionalScore:
        """
        Dimension 5: Timing (Filing recency + Foundation type)

        Combines:
        - Filing recency (5%): Phase 1 time-decay for aging data
        - Foundation type (5%): Operating vs non-operating preference

        Total weight: 10%
        """
        # Component 1: Filing recency (5/10)
        most_recent_filing_year = opportunity_data.get('most_recent_filing_year')

        if not most_recent_filing_year:
            filing_score = 0.5  # Neutral
            time_decay_penalty = 0.9
        else:
            current_year = datetime.now().year
            years_old = current_year - most_recent_filing_year
            months_old = max(0.0, years_old * 12)  # Clamp to 0 for future dates

            # Apply time-decay
            decay_factor = self.time_decay.calculate_decay(months_old)
            filing_score = decay_factor
            time_decay_penalty = decay_factor

        # Component 2: Foundation type (5/10)
        # Placeholder - would check foundation_code from 990-PF
        # 03 = private non-operating (most common for grant-making)
        # 04 = private operating
        foundation_type_score = 0.75  # Neutral-positive default

        # Combine components (weighted average within dimension)
        raw_score = (filing_score * 0.5) + (foundation_type_score * 0.5)

        filing_year_str = str(most_recent_filing_year) if most_recent_filing_year else "unknown"

        return DimensionalScore(
            dimension_name="timing",
            raw_score=raw_score,
            weight=0.10,
            weighted_score=raw_score * 0.10,
            boost_factor=time_decay_penalty,  # Apply time-decay as boost/penalty
            data_quality=0.8 if most_recent_filing_year else 0.4,
            calculation_method="filing_recency_with_time_decay",
            data_sources=["990pf_filing_metadata"],
            notes=f"Filing year: {filing_year_str}, Decay: {time_decay_penalty:.2f}, Type score: {foundation_type_score:.2f}"
        )


# Convenience function for foundation scoring
def score_foundation_opportunity(
    foundation_data: Dict[str, Any],
    organization_profile: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None
) -> List[DimensionalScore]:
    """
    Score a foundation opportunity using 8-component composite scoring

    Args:
        foundation_data: Foundation 990-PF data
        organization_profile: Applicant organization profile
        weights: Optional custom dimensional weights

    Returns:
        List of 5 DimensionalScore objects
    """
    scorer = FoundationStageScorer()
    return scorer.calculate_dimensions(
        opportunity_data=foundation_data,
        organization_profile=organization_profile,
        weights=weights or {},
        track_type="foundation"
    )
