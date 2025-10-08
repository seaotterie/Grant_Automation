"""
Schedule I Recipient Voting System (V2.0)

Analyzes foundation grant-making patterns from IRS Schedule I data to infer
funding interests and improve 990-PF screening accuracy.

Key Concepts:
- **Recipient Voting**: Each past grantee "votes" for their NTEE codes
- **Vote Weighting**: Larger grants = stronger votes, time-decay for old grants
- **Coherence Analysis**: Measures consistency of grant patterns
- **Entropy Scoring**: Low entropy = focused foundation, high = scattered

Phase 2, Week 4-5 Implementation
Expected Impact: 25-35% improvement in foundation matching accuracy
"""

import logging
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from ..profiles.models import ScheduleIGrantee
from ..utils.ein_resolution import EINResolver, EINConfidence
from .time_decay_utils import TimeDecayCalculator, DecayType
from .scoring_config import (
    RECIPIENT_COHERENCE_BONUS,
    RECIPIENT_ENTROPY_PENALTY,
    EIN_CONFIDENCE_WEIGHTS,
)


logger = logging.getLogger(__name__)


@dataclass
class RecipientVote:
    """A single recipient's vote for NTEE codes based on grant received"""
    recipient_name: str
    recipient_ein: Optional[str]
    grant_amount: float
    grant_year: int
    ntee_codes: List[str]  # NTEE codes for this recipient
    ein_confidence: EINConfidence  # Confidence in EIN resolution
    vote_weight: float  # Final weighted vote (amount × confidence × time-decay)


@dataclass
class NTEEVoteResult:
    """Aggregated votes for a single NTEE code"""
    ntee_code: str
    total_votes: float  # Sum of weighted votes
    vote_count: int  # Number of recipients voting for this code
    total_grant_amount: float  # Total $ awarded to orgs with this code
    avg_grant_amount: float  # Average grant size
    recipients: List[str]  # List of recipient names


@dataclass
class ScheduleIAnalysis:
    """Complete Schedule I analysis with voting and coherence metrics"""
    foundation_ein: str
    total_recipients: int
    total_grant_amount: float
    analysis_years: List[int]

    # Vote aggregations
    ntee_votes: Dict[str, NTEEVoteResult]  # NTEE code → vote results
    top_ntee_codes: List[str]  # Top voted NTEE codes (sorted by votes)

    # Coherence metrics
    coherence_score: float  # 0.0-1.0, higher = more consistent patterns
    entropy_score: float  # 0.0-∞, lower = more focused giving
    concentration_ratio: float  # % of $ to top 3 NTEE codes

    # Quality indicators
    ein_resolution_rate: float  # % of recipients successfully resolved
    high_confidence_rate: float  # % of recipients with HIGH confidence

    # Recommendations
    is_coherent: bool  # True if foundation has consistent patterns
    recommended_boost: float  # Boost factor for coherent foundations (0.0-0.15)


class ScheduleIVotingSystem:
    """
    Analyzes Schedule I grant recipients to infer foundation funding interests

    Process:
    1. Resolve recipient EINs with confidence scoring
    2. Lookup recipient NTEE codes from BMF
    3. Weight votes by grant amount, EIN confidence, and time-decay
    4. Aggregate votes and calculate coherence metrics
    5. Generate foundation NTEE code recommendations
    """

    def __init__(self,
                 ein_resolver: Optional[EINResolver] = None,
                 time_decay_calculator: Optional[TimeDecayCalculator] = None):
        """
        Initialize Schedule I voting system

        Args:
            ein_resolver: EIN resolution system (uses Phase 1 Week 2 implementation)
            time_decay_calculator: Time-decay calculator for aging grants
        """
        self.logger = logging.getLogger(f"{__name__}.ScheduleIVotingSystem")
        self.ein_resolver = ein_resolver or EINResolver()
        self.time_decay = time_decay_calculator or TimeDecayCalculator(DecayType.SCHEDULE_I_GRANTS)

    def analyze_foundation_patterns(self,
                                   foundation_ein: str,
                                   schedule_i_grantees: List[ScheduleIGrantee],
                                   current_year: Optional[int] = None) -> ScheduleIAnalysis:
        """
        Analyze foundation's Schedule I recipients to infer funding patterns

        Args:
            foundation_ein: Foundation's EIN
            schedule_i_grantees: List of Schedule I grantees from 990-PF
            current_year: Current year (defaults to now)

        Returns:
            ScheduleIAnalysis with vote results and coherence metrics
        """
        if not schedule_i_grantees:
            return self._create_empty_analysis(foundation_ein)

        current_year = current_year or datetime.now().year

        # Step 1: Resolve EINs and collect votes
        votes = self._collect_recipient_votes(schedule_i_grantees, current_year)

        if not votes:
            return self._create_empty_analysis(foundation_ein)

        # Step 2: Aggregate votes by NTEE code
        ntee_votes = self._aggregate_votes_by_ntee(votes)

        # Step 3: Calculate coherence metrics
        coherence_score = self._calculate_coherence(votes, ntee_votes)
        entropy_score = self._calculate_entropy(ntee_votes)
        concentration_ratio = self._calculate_concentration(ntee_votes)

        # Step 4: Calculate quality indicators
        ein_resolution_rate = sum(1 for v in votes if v.recipient_ein) / len(votes)
        high_confidence_rate = sum(
            1 for v in votes if v.ein_confidence == EINConfidence.HIGH
        ) / len(votes)

        # Step 5: Determine if foundation is "coherent" and calculate boost
        is_coherent = self._is_coherent(coherence_score, entropy_score, concentration_ratio)
        recommended_boost = self._calculate_coherence_boost(
            coherence_score, entropy_score, is_coherent
        )

        # Step 6: Sort NTEE codes by total votes
        top_ntee_codes = sorted(
            ntee_votes.keys(),
            key=lambda code: ntee_votes[code].total_votes,
            reverse=True
        )

        analysis_years = sorted(list(set(g.grant_year for g in schedule_i_grantees)))
        total_grant_amount = sum(g.grant_amount for g in schedule_i_grantees)

        return ScheduleIAnalysis(
            foundation_ein=foundation_ein,
            total_recipients=len(schedule_i_grantees),
            total_grant_amount=total_grant_amount,
            analysis_years=analysis_years,
            ntee_votes=ntee_votes,
            top_ntee_codes=top_ntee_codes,
            coherence_score=coherence_score,
            entropy_score=entropy_score,
            concentration_ratio=concentration_ratio,
            ein_resolution_rate=ein_resolution_rate,
            high_confidence_rate=high_confidence_rate,
            is_coherent=is_coherent,
            recommended_boost=recommended_boost,
        )

    def _collect_recipient_votes(self,
                                 grantees: List[ScheduleIGrantee],
                                 current_year: int) -> List[RecipientVote]:
        """
        Resolve recipient EINs and collect weighted votes

        Each recipient votes for their NTEE codes with weight based on:
        - Grant amount (larger grants = stronger signal)
        - EIN confidence (HIGH = 1.0, MEDIUM = 0.5, LOW = 0.0)
        - Time decay (recent grants weighted more heavily)
        """
        votes = []

        for grantee in grantees:
            # Resolve recipient EIN
            ein_result = self.ein_resolver.resolve_ein(
                ein=grantee.recipient_ein,
                name=grantee.recipient_name,
                state=None,  # Would need to extract from grantee address if available
                zip_code=None
            )

            if not ein_result or ein_result.confidence == EINConfidence.LOW:
                # Skip low-confidence matches (garbage-in-garbage-out prevention)
                self.logger.debug(
                    f"Skipping grantee '{grantee.recipient_name}' - low EIN confidence"
                )
                continue

            # Lookup NTEE codes from BMF
            ntee_codes = self._lookup_ntee_codes(ein_result.ein)

            if not ntee_codes:
                self.logger.debug(
                    f"No NTEE codes found for grantee '{grantee.recipient_name}' ({ein_result.ein})"
                )
                continue

            # Calculate time-decay weight
            years_old = current_year - grantee.grant_year
            months_old = years_old * 12
            time_decay_weight = self.time_decay.calculate_decay(months_old)

            # Calculate EIN confidence weight
            confidence_weight = EIN_CONFIDENCE_WEIGHTS[ein_result.confidence]

            # Calculate final vote weight
            # Formula: grant_amount × confidence_weight × time_decay_weight
            vote_weight = (
                grantee.grant_amount *
                confidence_weight *
                time_decay_weight
            )

            vote = RecipientVote(
                recipient_name=grantee.recipient_name,
                recipient_ein=ein_result.ein,
                grant_amount=grantee.grant_amount,
                grant_year=grantee.grant_year,
                ntee_codes=ntee_codes,
                ein_confidence=ein_result.confidence,
                vote_weight=vote_weight,
            )

            votes.append(vote)

        self.logger.info(
            f"Collected {len(votes)} valid votes from {len(grantees)} grantees "
            f"({len(votes)/len(grantees)*100:.1f}% success rate)"
        )

        return votes

    def _aggregate_votes_by_ntee(self,
                                votes: List[RecipientVote]) -> Dict[str, NTEEVoteResult]:
        """
        Aggregate votes by NTEE code

        Each recipient can vote for multiple NTEE codes (if they have multiple).
        Vote weight is split equally among all codes for that recipient.
        """
        ntee_aggregates = defaultdict(lambda: {
            'total_votes': 0.0,
            'vote_count': 0,
            'total_grant_amount': 0.0,
            'recipients': []
        })

        for vote in votes:
            # Split vote weight equally among all NTEE codes for this recipient
            vote_per_code = vote.vote_weight / len(vote.ntee_codes)

            for ntee_code in vote.ntee_codes:
                agg = ntee_aggregates[ntee_code]
                agg['total_votes'] += vote_per_code
                agg['vote_count'] += 1
                agg['total_grant_amount'] += vote.grant_amount
                agg['recipients'].append(vote.recipient_name)

        # Convert to NTEEVoteResult objects
        results = {}
        for ntee_code, agg in ntee_aggregates.items():
            results[ntee_code] = NTEEVoteResult(
                ntee_code=ntee_code,
                total_votes=agg['total_votes'],
                vote_count=agg['vote_count'],
                total_grant_amount=agg['total_grant_amount'],
                avg_grant_amount=agg['total_grant_amount'] / agg['vote_count'],
                recipients=agg['recipients'][:10]  # Limit to top 10 for storage
            )

        return results

    def _calculate_coherence(self,
                            votes: List[RecipientVote],
                            ntee_votes: Dict[str, NTEEVoteResult]) -> float:
        """
        Calculate coherence score (0.0-1.0)

        Coherence measures how consistent the foundation's grant patterns are.
        High coherence = foundation consistently funds similar organizations.

        Method: Calculate average pairwise similarity between recipients' NTEE codes
        """
        if len(votes) < 2:
            return 1.0  # Single recipient = perfectly coherent

        # Calculate pairwise NTEE code overlap
        similarities = []
        for i, vote1 in enumerate(votes):
            for vote2 in votes[i+1:]:
                codes1 = set(vote1.ntee_codes)
                codes2 = set(vote2.ntee_codes)

                if codes1 or codes2:
                    overlap = len(codes1 & codes2)
                    union = len(codes1 | codes2)
                    similarity = overlap / union if union > 0 else 0.0
                    similarities.append(similarity)

        if not similarities:
            return 0.0

        # Average pairwise similarity
        coherence = sum(similarities) / len(similarities)
        return coherence

    def _calculate_entropy(self,
                          ntee_votes: Dict[str, NTEEVoteResult]) -> float:
        """
        Calculate Shannon entropy of NTEE code distribution

        Entropy measures how "scattered" the foundation's giving is:
        - Low entropy (< 1.5): Focused foundation (few NTEE codes dominate)
        - Medium entropy (1.5-2.5): Balanced giving
        - High entropy (> 2.5): Scattered giving (many different areas)

        Formula: H = -Σ(p_i × log2(p_i))
        """
        if not ntee_votes:
            return 0.0

        # Calculate probability distribution
        total_votes = sum(result.total_votes for result in ntee_votes.values())

        if total_votes == 0:
            return 0.0

        entropy = 0.0
        for result in ntee_votes.values():
            p = result.total_votes / total_votes
            if p > 0:
                entropy -= p * math.log2(p)

        return entropy

    def _calculate_concentration(self,
                                ntee_votes: Dict[str, NTEEVoteResult]) -> float:
        """
        Calculate concentration ratio (% of votes going to top 3 NTEE codes)

        High concentration (> 0.7) = foundation focuses on few areas
        Low concentration (< 0.4) = foundation spreads giving widely
        """
        if not ntee_votes:
            return 0.0

        # Sort by votes and take top 3
        sorted_votes = sorted(
            ntee_votes.values(),
            key=lambda r: r.total_votes,
            reverse=True
        )

        top_3_votes = sum(r.total_votes for r in sorted_votes[:3])
        total_votes = sum(r.total_votes for r in ntee_votes.values())

        if total_votes == 0:
            return 0.0

        return top_3_votes / total_votes

    def _is_coherent(self,
                    coherence_score: float,
                    entropy_score: float,
                    concentration_ratio: float) -> bool:
        """
        Determine if foundation has coherent grant patterns

        A foundation is "coherent" if it meets 2 of 3 criteria:
        1. High coherence score (> 0.5)
        2. Low entropy (< 2.0)
        3. High concentration (> 0.6)
        """
        criteria_met = 0

        if coherence_score > 0.5:
            criteria_met += 1

        if entropy_score < 2.0:
            criteria_met += 1

        if concentration_ratio > 0.6:
            criteria_met += 1

        return criteria_met >= 2

    def _calculate_coherence_boost(self,
                                   coherence_score: float,
                                   entropy_score: float,
                                   is_coherent: bool) -> float:
        """
        Calculate score boost for coherent foundations (0.0-0.15)

        Coherent foundations are more predictable, so matches to their
        dominant NTEE codes should receive a boost.

        Formula:
        - Base boost: RECIPIENT_COHERENCE_BONUS (0.12)
        - Entropy penalty: -RECIPIENT_ENTROPY_PENALTY × (entropy / 3.0)
        - Minimum: 0.0, Maximum: 0.15
        """
        if not is_coherent:
            return 0.0

        # Start with base coherence bonus
        boost = RECIPIENT_COHERENCE_BONUS

        # Apply entropy penalty (higher entropy = lower boost)
        entropy_penalty = RECIPIENT_ENTROPY_PENALTY * (entropy_score / 3.0)
        boost -= entropy_penalty

        # Clamp to [0.0, 0.15]
        boost = max(0.0, min(0.15, boost))

        return boost

    def _lookup_ntee_codes(self, ein: str) -> List[str]:
        """
        Lookup NTEE codes for recipient from BMF database

        TODO: Implement BMF database query
        For now, returns empty list (placeholder)

        Args:
            ein: Recipient EIN

        Returns:
            List of NTEE codes for this organization
        """
        # TODO: Implement BMF lookup
        # This will query the nonprofit_intelligence.db BMF table
        # SELECT ntee_code FROM bmf_organizations WHERE ein = ?

        self.logger.debug(f"BMF NTEE lookup not yet implemented for EIN: {ein}")
        return []

    def _create_empty_analysis(self, foundation_ein: str) -> ScheduleIAnalysis:
        """Create empty analysis when no valid recipients"""
        return ScheduleIAnalysis(
            foundation_ein=foundation_ein,
            total_recipients=0,
            total_grant_amount=0.0,
            analysis_years=[],
            ntee_votes={},
            top_ntee_codes=[],
            coherence_score=0.0,
            entropy_score=0.0,
            concentration_ratio=0.0,
            ein_resolution_rate=0.0,
            high_confidence_rate=0.0,
            is_coherent=False,
            recommended_boost=0.0,
        )


def get_foundation_ntee_codes(schedule_i_analysis: ScheduleIAnalysis,
                             min_vote_threshold: float = 0.1) -> List[str]:
    """
    Extract foundation's inferred NTEE codes from Schedule I analysis

    Args:
        schedule_i_analysis: Completed Schedule I analysis
        min_vote_threshold: Minimum vote ratio to include code (0.0-1.0)
            Default 0.1 = code must have at least 10% of total votes

    Returns:
        List of NTEE codes ordered by vote strength
    """
    if not schedule_i_analysis.ntee_votes:
        return []

    total_votes = sum(r.total_votes for r in schedule_i_analysis.ntee_votes.values())

    if total_votes == 0:
        return []

    # Filter codes by minimum threshold
    qualified_codes = []
    for ntee_code in schedule_i_analysis.top_ntee_codes:
        vote_result = schedule_i_analysis.ntee_votes[ntee_code]
        vote_ratio = vote_result.total_votes / total_votes

        if vote_ratio >= min_vote_threshold:
            qualified_codes.append(ntee_code)

    return qualified_codes
