"""
Application Policy Reconciler (V2.0)

Reconciles foundation application acceptance status from multiple sources
(990-PF Part XV vs website scraping via Tool 25). Applies penalties for
contradictory signals and boosts for consistent positive signals.

Key Concepts:
- **Multi-Source Reconciliation**: Combines 990-PF data with web intelligence
- **Conflict Detection**: Identifies contradictions between sources
- **Penalty System**: -0.10 penalty for contradictory signals
- **Confidence Scoring**: Rates reliability of application policy determination
- **Source Prioritization**: Website > Recent 990 > Old 990

Phase 3, Week 7 Implementation
Expected Impact: 12-18% reduction in false positives (closed foundations)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


logger = logging.getLogger(__name__)


class ApplicationStatus(str, Enum):
    """Application acceptance status"""
    ACCEPTS = "accepts"              # Foundation accepts applications
    DOES_NOT_ACCEPT = "does_not_accept"  # Foundation does not accept applications
    BY_INVITATION_ONLY = "invitation_only"  # Invitation-only applications
    TEMPORARILY_CLOSED = "temporarily_closed"  # Temporarily not accepting
    UNKNOWN = "unknown"              # Insufficient data


class DataSource(str, Enum):
    """Source of application policy data"""
    WEBSITE = "website"              # Scraped from foundation website (Tool 25)
    FORM_990PF = "form_990pf"        # From 990-PF Part XV
    GRANTS_GOV = "grants_gov"        # From Grants.gov listing
    FOUNDATION_DIRECTORY = "foundation_directory"  # From foundation directory
    UNKNOWN = "unknown"


class ConflictType(str, Enum):
    """Type of data conflict detected"""
    NO_CONFLICT = "no_conflict"                    # All sources agree
    WEBSITE_990_MISMATCH = "website_990_mismatch"  # Website contradicts 990
    CLOSED_BUT_HAS_FORM = "closed_but_has_form"    # Says closed but has app form
    ACCEPTS_BUT_NO_INFO = "accepts_but_no_info"    # Says accepts but no details
    STALE_DATA = "stale_data"                      # Data older than 3 years


class ReconciliationConfidence(str, Enum):
    """Confidence in reconciled application policy"""
    HIGH = "high"          # 90%+ confidence (recent website + 990 agree)
    MEDIUM = "medium"      # 70-90% confidence (one strong source)
    LOW = "low"            # 50-70% confidence (old data or minor conflicts)
    VERY_LOW = "very_low"  # <50% confidence (major conflicts or no data)


@dataclass
class ApplicationPolicyData:
    """Application policy data from a single source"""
    source: DataSource
    status: ApplicationStatus
    date_observed: datetime
    details: Optional[str] = None
    url: Optional[str] = None
    confidence: float = 1.0  # 0.0-1.0


@dataclass
class ReconciliationResult:
    """Result of application policy reconciliation"""
    # Final determination
    reconciled_status: ApplicationStatus
    confidence: ReconciliationConfidence
    confidence_score: float  # 0.0-1.0

    # Source data
    sources: List[ApplicationPolicyData]
    primary_source: DataSource

    # Conflict analysis
    has_conflict: bool
    conflict_type: Optional[ConflictType]
    conflict_explanation: Optional[str]

    # Scoring impact
    policy_score: float  # 0.0-100.0
    penalty: float       # 0.0-0.10 (applied to composite score)
    boost: float         # 0.0-0.05 (for strong positive signals)

    # Explanation
    explanation: str
    recommendation: str


class ApplicationPolicyReconciler:
    """
    Multi-source application policy reconciliation system

    Reconciliation Logic:
    1. Collect data from all available sources (990-PF, website, etc.)
    2. Prioritize sources: Recent Website > Recent 990 > Old data
    3. Detect conflicts between sources
    4. Apply conflict resolution rules
    5. Calculate confidence score
    6. Apply penalties/boosts to composite score

    Source Priority:
    - Website (Tool 25): Highest priority if < 1 year old
    - 990-PF Part XV: High priority if < 2 years old
    - Other sources: Medium priority

    Penalty System:
    - Major conflict (website says accepts, 990 says closed): -0.10
    - Minor conflict (stale data, minor inconsistencies): -0.05
    - No conflict + accepts applications: +0.05 boost
    - No conflict + clear policy: 0.00 (neutral)
    """

    def __init__(self):
        """Initialize application policy reconciler"""
        self.logger = logging.getLogger(f"{__name__}.ApplicationPolicyReconciler")

    def reconcile(self,
                 policy_data: List[ApplicationPolicyData]) -> ReconciliationResult:
        """
        Reconcile application policy from multiple sources

        Args:
            policy_data: List of ApplicationPolicyData from different sources

        Returns:
            ReconciliationResult with final determination and scoring impact
        """
        if not policy_data:
            return self._create_unknown_result()

        # Sort by priority (website > 990 > others) and date (recent > old)
        sorted_data = self._prioritize_sources(policy_data)

        # Detect conflicts
        has_conflict, conflict_type, conflict_explanation = self._detect_conflicts(
            sorted_data
        )

        # Determine reconciled status
        reconciled_status, primary_source = self._determine_status(
            sorted_data, has_conflict
        )

        # Calculate confidence
        confidence, confidence_score = self._calculate_confidence(
            sorted_data, has_conflict, reconciled_status
        )

        # Calculate scoring impact
        policy_score, penalty, boost = self._calculate_scoring_impact(
            reconciled_status, has_conflict, conflict_type, confidence
        )

        # Generate explanation and recommendation
        explanation = self._generate_explanation(
            reconciled_status, sorted_data, has_conflict, conflict_type
        )
        recommendation = self._generate_recommendation(
            reconciled_status, has_conflict, confidence
        )

        return ReconciliationResult(
            reconciled_status=reconciled_status,
            confidence=confidence,
            confidence_score=confidence_score,
            sources=sorted_data,
            primary_source=primary_source,
            has_conflict=has_conflict,
            conflict_type=conflict_type,
            conflict_explanation=conflict_explanation,
            policy_score=policy_score,
            penalty=penalty,
            boost=boost,
            explanation=explanation,
            recommendation=recommendation,
        )

    def _prioritize_sources(self,
                           data: List[ApplicationPolicyData]) -> List[ApplicationPolicyData]:
        """
        Sort sources by priority and recency

        Priority Order:
        1. Website (most current)
        2. 990-PF (official filing)
        3. Other sources

        Within each priority tier, sort by date (newest first)
        """
        priority_order = {
            DataSource.WEBSITE: 0,
            DataSource.FORM_990PF: 1,
            DataSource.GRANTS_GOV: 2,
            DataSource.FOUNDATION_DIRECTORY: 3,
            DataSource.UNKNOWN: 4,
        }

        return sorted(
            data,
            key=lambda x: (
                priority_order.get(x.source, 4),
                -x.date_observed.timestamp()  # Negative for descending
            )
        )

    def _detect_conflicts(self,
                         data: List[ApplicationPolicyData]) -> tuple[bool, Optional[ConflictType], Optional[str]]:
        """
        Detect conflicts between sources

        Major Conflicts:
        - Website says "accepts", 990 says "does not accept"
        - Foundation says "closed" but has active application form
        - Recent data contradicts older data

        Minor Conflicts:
        - Data older than 3 years (stale)
        - Says accepts but no application details/URL
        """
        if len(data) < 2:
            # No conflicts possible with single source
            return False, ConflictType.NO_CONFLICT, None

        # Get primary (highest priority) status
        primary = data[0]

        # Check for major contradictions
        for secondary in data[1:]:
            # Website vs 990 mismatch
            if (primary.source == DataSource.WEBSITE and
                secondary.source == DataSource.FORM_990PF):
                if (primary.status == ApplicationStatus.ACCEPTS and
                    secondary.status == ApplicationStatus.DOES_NOT_ACCEPT):
                    return (
                        True,
                        ConflictType.WEBSITE_990_MISMATCH,
                        f"Website shows applications accepted, but 990-PF says not accepting"
                    )
                elif (primary.status == ApplicationStatus.DOES_NOT_ACCEPT and
                      secondary.status == ApplicationStatus.ACCEPTS):
                    return (
                        True,
                        ConflictType.WEBSITE_990_MISMATCH,
                        f"Website shows no applications, but 990-PF says accepting"
                    )

        # Check for closed-but-has-form conflict
        for item in data:
            if (item.status in [ApplicationStatus.DOES_NOT_ACCEPT, ApplicationStatus.TEMPORARILY_CLOSED] and
                item.url is not None and "application" in item.url.lower()):
                return (
                    True,
                    ConflictType.CLOSED_BUT_HAS_FORM,
                    f"Foundation claims not accepting applications but has application form URL"
                )

        # Check for stale data
        current_year = datetime.now().year
        for item in data:
            years_old = current_year - item.date_observed.year
            if years_old > 3:
                return (
                    True,
                    ConflictType.STALE_DATA,
                    f"Data is {years_old} years old - may be outdated"
                )

        # Check for accepts-but-no-info
        if primary.status == ApplicationStatus.ACCEPTS:
            if not primary.details and not primary.url:
                return (
                    True,
                    ConflictType.ACCEPTS_BUT_NO_INFO,
                    f"Foundation claims to accept applications but provides no details or URL"
                )

        return False, ConflictType.NO_CONFLICT, None

    def _determine_status(self,
                         data: List[ApplicationPolicyData],
                         has_conflict: bool) -> tuple[ApplicationStatus, DataSource]:
        """
        Determine final reconciled status

        Logic:
        - If no conflict: Use highest priority source
        - If conflict: Use most recent and reliable source with penalty
        - If major conflict: Default to conservative (does not accept)
        """
        if not data:
            return ApplicationStatus.UNKNOWN, DataSource.UNKNOWN

        # Primary source (highest priority, most recent)
        primary = data[0]

        if not has_conflict:
            return primary.status, primary.source

        # With conflict, check for conservative fallback
        # If website says closed but 990 says open, trust website (more current)
        if primary.source == DataSource.WEBSITE:
            return primary.status, primary.source

        # If 990 is more recent, trust it
        if primary.source == DataSource.FORM_990PF:
            years_old = datetime.now().year - primary.date_observed.year
            if years_old <= 2:
                return primary.status, primary.source

        # Default to conservative (does not accept) if major conflict
        return ApplicationStatus.DOES_NOT_ACCEPT, primary.source

    def _calculate_confidence(self,
                             data: List[ApplicationPolicyData],
                             has_conflict: bool,
                             status: ApplicationStatus) -> tuple[ReconciliationConfidence, float]:
        """
        Calculate confidence in reconciled determination

        High Confidence (90%+):
        - Website < 1 year old + 990 agrees
        - Recent 990 (< 2 years) with clear statement

        Medium Confidence (70-90%):
        - Website or 990 alone, recent
        - Minor conflicts resolved

        Low Confidence (50-70%):
        - Older data (2-3 years)
        - Minor conflicts

        Very Low Confidence (<50%):
        - Major conflicts
        - Very old data (3+ years)
        - No clear data
        """
        if not data or status == ApplicationStatus.UNKNOWN:
            return ReconciliationConfidence.VERY_LOW, 0.0

        primary = data[0]
        years_old = datetime.now().year - primary.date_observed.year

        # Check for agreement between sources
        agreement_count = sum(1 for d in data if d.status == status)
        agreement_ratio = agreement_count / len(data)

        # Calculate base confidence
        confidence_score = 0.5  # Baseline

        # Boost for recent data
        if years_old == 0:
            confidence_score += 0.25
        elif years_old == 1:
            confidence_score += 0.15
        elif years_old == 2:
            confidence_score += 0.05

        # Boost for high-priority source
        if primary.source == DataSource.WEBSITE:
            confidence_score += 0.15
        elif primary.source == DataSource.FORM_990PF:
            confidence_score += 0.10

        # Boost for agreement
        confidence_score += (agreement_ratio - 0.5) * 0.2

        # Penalty for conflicts
        if has_conflict:
            confidence_score -= 0.25

        # Cap at 0.0-1.0
        confidence_score = max(0.0, min(1.0, confidence_score))

        # Categorize
        if confidence_score >= 0.90:
            confidence = ReconciliationConfidence.HIGH
        elif confidence_score >= 0.70:
            confidence = ReconciliationConfidence.MEDIUM
        elif confidence_score >= 0.50:
            confidence = ReconciliationConfidence.LOW
        else:
            confidence = ReconciliationConfidence.VERY_LOW

        return confidence, confidence_score

    def _calculate_scoring_impact(self,
                                 status: ApplicationStatus,
                                 has_conflict: bool,
                                 conflict_type: Optional[ConflictType],
                                 confidence: ReconciliationConfidence) -> tuple[float, float, float]:
        """
        Calculate impact on composite score

        Returns: (policy_score 0-100, penalty 0.0-0.10, boost 0.0-0.05)

        Policy Score:
        - Accepts applications: 100.0
        - Invitation only: 60.0
        - Temporarily closed: 40.0
        - Does not accept: 20.0
        - Unknown: 50.0 (neutral)

        Penalties:
        - Major conflict (website/990 mismatch): -0.10
        - Closed but has form: -0.10
        - Minor conflict (stale data): -0.05
        - Accepts but no info: -0.03

        Boosts:
        - High confidence + accepts: +0.05
        - Medium confidence + accepts: +0.03
        """
        # Base policy score
        if status == ApplicationStatus.ACCEPTS:
            policy_score = 100.0
        elif status == ApplicationStatus.BY_INVITATION_ONLY:
            policy_score = 60.0
        elif status == ApplicationStatus.TEMPORARILY_CLOSED:
            policy_score = 40.0
        elif status == ApplicationStatus.DOES_NOT_ACCEPT:
            policy_score = 20.0
        else:  # UNKNOWN
            policy_score = 50.0

        # Calculate penalty
        penalty = 0.0
        if has_conflict:
            if conflict_type in [ConflictType.WEBSITE_990_MISMATCH,
                                ConflictType.CLOSED_BUT_HAS_FORM]:
                penalty = 0.10  # Major conflict
            elif conflict_type == ConflictType.STALE_DATA:
                penalty = 0.05  # Minor conflict
            elif conflict_type == ConflictType.ACCEPTS_BUT_NO_INFO:
                penalty = 0.03  # Small penalty

        # Calculate boost
        boost = 0.0
        if status == ApplicationStatus.ACCEPTS and not has_conflict:
            if confidence == ReconciliationConfidence.HIGH:
                boost = 0.05
            elif confidence == ReconciliationConfidence.MEDIUM:
                boost = 0.03

        return policy_score, penalty, boost

    def _generate_explanation(self,
                             status: ApplicationStatus,
                             data: List[ApplicationPolicyData],
                             has_conflict: bool,
                             conflict_type: Optional[ConflictType]) -> str:
        """Generate human-readable explanation"""
        primary = data[0] if data else None

        if not primary:
            return "No application policy data available"

        status_str = status.value.replace('_', ' ').title()
        source_str = primary.source.value.replace('_', ' ').title()
        years_old = datetime.now().year - primary.date_observed.year

        base_msg = f"Application Status: {status_str} (Source: {source_str}, {years_old}y old)"

        if not has_conflict:
            if len(data) > 1:
                return f"{base_msg}. Multiple sources agree."
            else:
                return f"{base_msg}. Single source available."

        # With conflict
        conflict_str = conflict_type.value.replace('_', ' ').title()
        return f"{base_msg}. ⚠️ CONFLICT DETECTED: {conflict_str}. Use with caution."

    def _generate_recommendation(self,
                                status: ApplicationStatus,
                                has_conflict: bool,
                                confidence: ReconciliationConfidence) -> str:
        """Generate strategic recommendation"""
        if status == ApplicationStatus.ACCEPTS:
            if confidence == ReconciliationConfidence.HIGH and not has_conflict:
                return "Excellent - Foundation accepts applications with high confidence. Proceed with application."
            elif has_conflict:
                return "Caution - Foundation may accept applications but data conflicts exist. Verify directly before applying."
            else:
                return "Good - Foundation appears to accept applications. Confirm details on their website."

        elif status == ApplicationStatus.BY_INVITATION_ONLY:
            return "Invitation only - Do not apply directly. Focus on building relationship first."

        elif status == ApplicationStatus.TEMPORARILY_CLOSED:
            return "Currently closed - Monitor for reopening. Add to watchlist for future cycles."

        elif status == ApplicationStatus.DOES_NOT_ACCEPT:
            if has_conflict:
                return "Unclear - Data suggests not accepting, but conflicts exist. Research further before dismissing."
            else:
                return "Not recommended - Foundation does not accept unsolicited applications. Skip unless invited."

        else:  # UNKNOWN
            return "Insufficient data - Research application policy on foundation website before proceeding."

    def _create_unknown_result(self) -> ReconciliationResult:
        """Create result for cases with no data"""
        return ReconciliationResult(
            reconciled_status=ApplicationStatus.UNKNOWN,
            confidence=ReconciliationConfidence.VERY_LOW,
            confidence_score=0.0,
            sources=[],
            primary_source=DataSource.UNKNOWN,
            has_conflict=False,
            conflict_type=None,
            conflict_explanation=None,
            policy_score=50.0,
            penalty=0.05,  # Small penalty for missing data
            boost=0.0,
            explanation="No application policy data available",
            recommendation="Research application policy on foundation website before proceeding.",
        )


def reconcile_application_policy(policy_data: List[ApplicationPolicyData]) -> ReconciliationResult:
    """
    Convenience function for application policy reconciliation

    Args:
        policy_data: List of ApplicationPolicyData from different sources

    Returns:
        ReconciliationResult with final determination and scoring impact
    """
    reconciler = ApplicationPolicyReconciler()
    return reconciler.reconcile(policy_data)
