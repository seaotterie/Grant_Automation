#!/usr/bin/env python3
"""
Catalynx Scoring System
Advanced multi-dimensional scoring for opportunity evaluation and promotion

Version 2.0: 990-PF Screening Enhancement
Added: Time-decay, two-part NTEE, recipient voting, and composite scoring v2

Version 2.1: Two-Part NTEE Scoring Implementation (Phase 2, Week 3)
Version 2.2: Schedule I Recipient Voting System (Phase 2, Week 4-5)
Version 2.3: Grant-Size Realism Bands (Phase 2, Week 4-5)
Version 2.4: Composite Scorer V2 with Rebalanced Weights (Phase 3, Week 6)
Version 2.5: Abstain/Triage Queue for Manual Review (Phase 3, Week 6)
Version 2.6: Payout Sufficiency (5% Rule) Scoring (Phase 3, Week 7)
"""

# Legacy scoring (V1)
from .discovery_scorer import DiscoveryScorer, ScoringDimensions, ScoringResult
from .promotion_engine import PromotionEngine, PromotionDecision, PromotionReason

# V2 Enhanced Scoring Infrastructure (990-PF Screening Enhancement)
from .time_decay_utils import (
    TimeDecayCalculator,
    DecayType,
    apply_schedule_i_decay,
    apply_filing_decay,
    apply_ntee_decay,
    get_decay_weight,
)

from .scoring_config import (
    COMPOSITE_WEIGHTS_V2,
    THRESHOLD_DEFAULT,
    THRESHOLD_ABSTAIN_LOWER,
    THRESHOLD_ABSTAIN_UPPER,
    CONFIDENCE_HIGH_MIN,
    CONFIDENCE_MEDIUM_MIN,
    NTEE_MAJOR_WEIGHT,
    NTEE_LEAF_WEIGHT,
    NTEE_MAX_CONTRIBUTION,
    RECIPIENT_COHERENCE_BONUS,
    RECIPIENT_ENTROPY_PENALTY,
    GRANT_SIZE_BANDS,
    FILING_RECENCY_BANDS,
    APPLICATION_POLICY_PENALTIES,
    PAYOUT_RATIO_BANDS,
    GEOGRAPHIC_SCORES,
    EIN_CONFIDENCE_WEIGHTS,
    FeatureFlags,
    ScoringVersion,
    get_scoring_version_info,
)

# V2.1 Two-Part NTEE Scoring (Phase 2, Week 3)
from .ntee_scorer import (
    NTEEScorer,
    NTEECode,
    NTEEScoreResult,
    NTEEDataSource,
    NTEEMatchLevel,
    score_ntee_alignment,
    get_ntee_major_description,
)

# V2.2 Schedule I Recipient Voting (Phase 2, Week 4-5)
from .schedule_i_voting import (
    ScheduleIVotingSystem,
    ScheduleIAnalysis,
    RecipientVote,
    NTEEVoteResult,
    get_foundation_ntee_codes,
)

# V2.3 Grant-Size Realism Bands (Phase 2, Week 4-5)
from .grant_size_scoring import (
    GrantSizeScorer,
    GrantSizeAnalysis,
    GrantSizeBand,
    CapacityLevel,
    GrantSizeFit,
    score_grant_size_fit,
    get_recommended_grant_range,
)

# V2.4 Composite Scorer V2 (Phase 3, Week 6)
from .composite_scorer_v2 import (
    CompositeScoreV2,
    CompositeScoreResult,
    FoundationOpportunityData,
)

# V2.5 Abstain/Triage Queue (Phase 3, Week 6)
from .triage_queue import (
    TriageQueue,
    TriageItem,
    TriageStatus,
    TriagePriority,
    ExpertDecision,
    TriageQueueStats,
    get_triage_queue,
)

# V2.6 Payout Sufficiency (Phase 3, Week 7)
from .payout_sufficiency import (
    PayoutSufficiencyScorer,
    PayoutAnalysis,
    PayoutCompliance,
    GrantActivity,
    score_payout_sufficiency,
)

__all__ = [
    # Legacy V1 scoring
    'DiscoveryScorer',
    'ScoringDimensions',
    'ScoringResult',
    'PromotionEngine',
    'PromotionDecision',
    'PromotionReason',

    # V2 Time decay
    "TimeDecayCalculator",
    "DecayType",
    "apply_schedule_i_decay",
    "apply_filing_decay",
    "apply_ntee_decay",
    "get_decay_weight",

    # V2 Configuration
    "COMPOSITE_WEIGHTS_V2",
    "THRESHOLD_DEFAULT",
    "THRESHOLD_ABSTAIN_LOWER",
    "THRESHOLD_ABSTAIN_UPPER",
    "CONFIDENCE_HIGH_MIN",
    "CONFIDENCE_MEDIUM_MIN",
    "NTEE_MAJOR_WEIGHT",
    "NTEE_LEAF_WEIGHT",
    "NTEE_MAX_CONTRIBUTION",
    "RECIPIENT_COHERENCE_BONUS",
    "RECIPIENT_ENTROPY_PENALTY",
    "GRANT_SIZE_BANDS",
    "FILING_RECENCY_BANDS",
    "APPLICATION_POLICY_PENALTIES",
    "PAYOUT_RATIO_BANDS",
    "GEOGRAPHIC_SCORES",
    "EIN_CONFIDENCE_WEIGHTS",
    "FeatureFlags",
    "ScoringVersion",
    "get_scoring_version_info",

    # V2.1 NTEE Two-Part Scoring
    "NTEEScorer",
    "NTEECode",
    "NTEEScoreResult",
    "NTEEDataSource",
    "NTEEMatchLevel",
    "score_ntee_alignment",
    "get_ntee_major_description",

    # V2.2 Schedule I Recipient Voting
    "ScheduleIVotingSystem",
    "ScheduleIAnalysis",
    "RecipientVote",
    "NTEEVoteResult",
    "get_foundation_ntee_codes",

    # V2.3 Grant-Size Realism Bands
    "GrantSizeScorer",
    "GrantSizeAnalysis",
    "GrantSizeBand",
    "CapacityLevel",
    "GrantSizeFit",
    "score_grant_size_fit",
    "get_recommended_grant_range",

    # V2.4 Composite Scorer V2
    "CompositeScoreV2",
    "CompositeScoreResult",
    "FoundationOpportunityData",

    # V2.5 Abstain/Triage Queue
    "TriageQueue",
    "TriageItem",
    "TriageStatus",
    "TriagePriority",
    "ExpertDecision",
    "TriageQueueStats",
    "get_triage_queue",

    # V2.6 Payout Sufficiency
    "PayoutSufficiencyScorer",
    "PayoutAnalysis",
    "PayoutCompliance",
    "GrantActivity",
    "score_payout_sufficiency",
]

__version__ = "2.6.0"