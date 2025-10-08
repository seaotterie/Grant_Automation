#!/usr/bin/env python3
"""
Catalynx Scoring System
Advanced multi-dimensional scoring for opportunity evaluation and promotion

Version 2.0: 990-PF Screening Enhancement
Added: Time-decay, two-part NTEE, recipient voting, and composite scoring v2

Version 2.1: Two-Part NTEE Scoring Implementation (Phase 2, Week 3)
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
]

__version__ = "2.1.0"