"""
Centralized Scoring Configuration for 990-PF Screening Enhancement
Defines all weights, thresholds, and parameters for the scoring system.

Version: 2.0 (990-PF Enhancement Project)
Created: Phase 1, Week 1
"""

from typing import Dict
from enum import Enum


class ScoringVersion(str, Enum):
    """Scoring model versions for auditing and rollback"""
    V1_BASELINE = "1.0"        # Original system (pre-enhancement)
    V2_ENHANCED = "2.0"        # Post-enhancement system
    CURRENT = "2.0"


# ==============================================================================
# COMPOSITE SCORE WEIGHTS (Validated on Gold Set)
# ==============================================================================

# V2.0 Enhanced Weights (Empirically validated - Phase 3, Week 6)
COMPOSITE_WEIGHTS_V2 = {
    "ntee_alignment": 0.30,        # Two-part NTEE scoring (capped at 30%)
    "geographic_match": 0.20,      # State/regional alignment with border bonus
    "recipient_coherence": 0.12,   # Schedule I voting system
    "financial_capacity": 0.10,    # Payout ratio + asset sufficiency
    "grant_size_fit": 0.10,        # Revenue-proportional realism
    "application_policy": 0.08,    # Acceptance status with reconciliation
    "filing_recency": 0.05,        # Time-based quality signal
    "foundation_type": 0.05,       # Code 03 preference
}

# V1.0 Baseline Weights (for A/B comparison)
COMPOSITE_WEIGHTS_V1 = {
    "ntee_alignment": 0.30,
    "geographic_match": 0.20,
    "financial_capacity": 0.10,
    "eligibility_score": 0.15,
    "timing_score": 0.15,
    "competition_score": 0.10,
}

# Active weights (feature flag controlled)
ACTIVE_WEIGHTS = COMPOSITE_WEIGHTS_V2


# ==============================================================================
# SCORING THRESHOLDS
# ==============================================================================

# Composite score pass thresholds
THRESHOLD_DEFAULT = 0.58           # Standard threshold
THRESHOLD_HIGH_VOLUME = 0.62       # When >500 opportunities found
THRESHOLD_SPARSE_MARKET = 0.54     # When <50 opportunities found
THRESHOLD_ABSTAIN_LOWER = 0.54     # Lower bound of gray zone
THRESHOLD_ABSTAIN_UPPER = 0.62     # Upper bound of gray zone

# Confidence band thresholds
CONFIDENCE_HIGH_MIN = 0.70         # High confidence: strong match
CONFIDENCE_MEDIUM_MIN = 0.58       # Medium confidence: review details
CONFIDENCE_LOW_MAX = 0.58          # Low confidence: manual review needed

# Data quality thresholds
DATA_COMPLETENESS_MIN = 0.50       # Minimum completeness for scoring
DATA_COMPLETENESS_ABSTAIN = 0.60   # Below this triggers abstain


# ==============================================================================
# NTEE SCORING PARAMETERS
# ==============================================================================

# Two-part NTEE weights (Phase 2, Week 3)
NTEE_MAJOR_WEIGHT = 0.40           # Major code (A-Z) contribution
NTEE_LEAF_WEIGHT = 0.60            # Leaf code (3-digit) contribution
NTEE_MAX_CONTRIBUTION = 0.30       # Cap on NTEE's total contribution to composite

# NTEE validation source priorities
NTEE_SOURCE_PRIORITIES = {
    "bmf": 1,                      # BMF database baseline
    "schedule_i": 2,               # Schedule I recipient patterns
    "website": 3,                  # Scraped website data
}


# ==============================================================================
# SCHEDULE I RECIPIENT VOTING PARAMETERS
# ==============================================================================

# Coherence and entropy scoring (Phase 2, Week 4-5)
RECIPIENT_COHERENCE_BONUS = 10     # Bonus when top recipients share leaf NTEE
RECIPIENT_ENTROPY_PENALTY = -8     # Penalty when recipients span disparate causes
RECIPIENT_COHERENCE_THRESHOLD = 0.60  # 60% of grants to similar orgs
RECIPIENT_ENTROPY_THRESHOLD = 0.80    # Shannon entropy threshold

# Multi-year voting parameters
RECIPIENT_VOTING_WINDOW_YEARS = 3  # Rolling window for grant history
RECIPIENT_MIN_GRANTS = 3           # Minimum grants needed for voting
RECIPIENT_SPARSITY_PENALTY = {
    1: 0.30,  # Only 1 year: 70% penalty
    2: 0.80,  # 2 years: 20% penalty
    3: 1.00,  # 3+ years: no penalty
}


# ==============================================================================
# GRANT-SIZE REALISM BANDS (Revenue Proportional)
# ==============================================================================

# Scoring by grant size as % of recipient revenue (Phase 2, Week 5)
GRANT_SIZE_BANDS = {
    # (min%, max%): score_adjustment
    (1.0, 10.0): +12,      # Sweet spot: 1-10% of revenue
    (10.0, 25.0): +6,      # Stretch but reasonable: 10-25%
    (0.5, 1.0): +2,        # Small but useful: 0.5-1%
    (25.0, 50.0): 0,       # Neutral: user discretion for large grants
    (0.0, 0.5): -6,        # Too small: <0.5% of revenue
    (50.0, 100.0): -4,     # Unrealistic dependency: >50% of revenue
}


# ==============================================================================
# FILING RECENCY SCORING BANDS
# ==============================================================================

# Tiered scoring by filing age (Phase 1, Week 2)
FILING_RECENCY_BANDS = {
    # (min_months, max_months): score_adjustment
    (0, 18): +8,           # Recent: ≤18 months
    (19, 30): +5,          # Acceptable: 19-30 months
    (31, 42): +2,          # Aging: 31-42 months
    (43, 999): -6,         # Stale: >42 months
}

# IRS processing delay buffer (months)
IRS_PROCESSING_DELAY_BUFFER = 4


# ==============================================================================
# APPLICATION POLICY PENALTIES
# ==============================================================================

# Penalties for application restrictions (Phase 3, Week 7)
APPLICATION_POLICY_PENALTIES = {
    "no_applications": -12,         # 990 says no applications accepted
    "invitation_only": -18,         # Invitation-only policy
    "application_conflict": -8,     # Website vs 990 conflict detected
    "policy_unknown": -5,           # Missing policy data
}

# Multi-source confirmation requirement for full exclusion
POLICY_EXCLUSION_SOURCES_REQUIRED = 2  # Need 2+ sources to fully exclude
POLICY_EXCLUSION_YEARS_REQUIRED = 2    # Need 2+ consecutive years


# ==============================================================================
# PAYOUT SUFFICIENCY (5% Rule) SCORING
# ==============================================================================

# Scoring by payout ratio vs IRS 5% requirement (Phase 3, Week 7)
PAYOUT_RATIO_BANDS = {
    # Ratio thresholds: score_adjustment
    1.20: +12,             # Generous: ≥120% of requirement
    1.00: +8,              # Meeting requirement: ≥100%
    0.70: +3,              # Mostly compliant: ≥70%
    0.40: 0,               # Marginal: ≥40%
    0.00: -10,             # Under-distributing: <40%
}

PAYOUT_ROLLING_WINDOW_YEARS = 3    # 3-year average
PAYOUT_MIN_YEARS_REQUIRED = 2       # Need 2+ years for scoring


# ==============================================================================
# GEOGRAPHIC SCORING
# ==============================================================================

# Geographic alignment scoring (Phase 3, Week 7)
GEOGRAPHIC_SCORES = {
    "in_state": +20,               # Same state as profile
    "adjacent_state": +14,         # Bordering state
    "regional": +8,                # Same region (e.g., Mid-Atlantic)
    "national": +12,               # National scope foundation
    "out_of_region": 0,            # Outside region but not excluded
}

# Metro area bonuses (treat as single market)
METRO_AREAS = {
    "dmv": ["DC", "MD", "VA"],    # DC/Maryland/Virginia
    "tri_state": ["NY", "NJ", "CT"],  # Tri-State Area
}
METRO_AREA_BONUS = +18            # Apply if foundation covers entire metro


# ==============================================================================
# EIN RESOLUTION CONFIDENCE WEIGHTS
# ==============================================================================

# Confidence-based weighting for recipient voting (Phase 1, Week 2)
EIN_CONFIDENCE_WEIGHTS = {
    "high": 1.00,      # Exact EIN + name + state match
    "medium": 0.50,    # Fuzzy name + ZIP3 match
    "low": 0.00,       # Name-only match (excluded from voting)
}

# Fuzzy matching thresholds
EIN_FUZZY_NAME_THRESHOLD = 0.80    # Levenshtein similarity (80%+)


# ==============================================================================
# ABSTAIN/TRIAGE CRITERIA
# ==============================================================================

# Conditions that trigger abstain/manual review (Phase 3, Week 6)
ABSTAIN_CONDITIONS = {
    "gray_zone_score": True,           # Score in [0.54, 0.62]
    "high_conflicts": 2,               # ≥2 conflict flags
    "low_data_completeness": 0.50,    # <50% data available
    "high_entropy": 0.80,              # Recipient entropy >0.8
    "low_ein_confidence": True,        # Any low-confidence EIN matches
}

# Target abstain rate bounds
ABSTAIN_RATE_TARGET_MIN = 0.08    # 8%
ABSTAIN_RATE_TARGET_MAX = 0.12    # 12%


# ==============================================================================
# TIME-DECAY PARAMETERS (from time_decay_utils.py)
# ==============================================================================

# Lambda values for exponential decay
TIME_DECAY_LAMBDA = {
    "schedule_i_grants": 0.03,     # Half-life ~23 months
    "ntee_mission": 0.02,          # Half-life ~35 months (slower decay)
    "website_data": 0.04,          # Half-life ~17 months (faster decay)
    "filing_data": 0.025,          # Half-life ~28 months
}


# ==============================================================================
# FOUNDATION TYPE PREFERENCES
# ==============================================================================

# Foundation code scoring (Phase 1, Week 1)
FOUNDATION_CODE_SCORES = {
    "03": +8,     # Private non-operating (grantmaking) - PREFERRED
    "04": -5,     # Private operating (not typically grantmaking)
    "12": +3,     # Supporting organization
    "15": +2,     # Donor-advised fund
    "unknown": 0,
}


# ==============================================================================
# FEATURE FLAGS (A/B Testing & Rollout Control)
# ==============================================================================

class FeatureFlags:
    """Feature flags for phased rollout and A/B testing"""

    # Scoring model version (V1 baseline vs V2 enhanced)
    SCORING_VERSION = ScoringVersion.V2_ENHANCED

    # Enable/disable individual features
    ENABLE_TIME_DECAY = True
    ENABLE_TWO_PART_NTEE = True
    ENABLE_RECIPIENT_VOTING = True
    ENABLE_GRANT_SIZE_BANDS = True
    ENABLE_PAYOUT_SUFFICIENCY = True
    ENABLE_APPLICATION_PENALTIES = True
    ENABLE_ABSTAIN_TRIAGE = True
    ENABLE_EVIDENCE_CARDS = True

    # Rollout percentage (for phased deployment)
    ROLLOUT_PERCENTAGE = 100  # 0-100, start with 10%

    # A/B testing mode (runs both scorers in parallel)
    AB_TESTING_MODE = False

    # Shadow mode (new scorer runs but doesn't affect results)
    SHADOW_MODE = False


# ==============================================================================
# VALIDATION & MONITORING
# ==============================================================================

# Gold set evaluation targets (Phase 5, Week 9-10)
GOLD_SET_TARGETS = {
    "f1_score": 0.75,          # Macro-F1 ≥ 0.75
    "precision_at_10": 0.80,   # P@10 ≥ 0.80
    "precision_at_50": 0.70,   # P@50 ≥ 0.70
    "calibration_ece": 0.10,   # ECE ≤ 0.10
    "top_2_accuracy": 0.85,    # Top-2 accuracy ≥ 85%
}

# Drift monitoring thresholds (Phase 5, Week 10)
DRIFT_ALERT_THRESHOLDS = {
    "f1_drop_percent": 5,      # Alert if F1 drops >5%
    "ece_increase": 0.03,      # Alert if ECE increases >0.03
    "kl_divergence": 0.10,     # Alert if prediction KL divergence >0.10
}


# ==============================================================================
# VERSION STAMPING
# ==============================================================================

def get_scoring_version_info() -> Dict:
    """
    Get current scoring configuration version info.

    Returns:
        Dictionary with version metadata for auditing
    """
    return {
        "model_version": ScoringVersion.CURRENT.value,
        "weights_config": ACTIVE_WEIGHTS,
        "ntee_weights": {
            "major": NTEE_MAJOR_WEIGHT,
            "leaf": NTEE_LEAF_WEIGHT,
            "cap": NTEE_MAX_CONTRIBUTION,
        },
        "thresholds": {
            "default": THRESHOLD_DEFAULT,
            "abstain_range": [THRESHOLD_ABSTAIN_LOWER, THRESHOLD_ABSTAIN_UPPER],
            "confidence_bands": {
                "high": CONFIDENCE_HIGH_MIN,
                "medium": CONFIDENCE_MEDIUM_MIN,
            },
        },
        "time_decay_lambda": TIME_DECAY_LAMBDA,
        "feature_flags": {
            "scoring_version": FeatureFlags.SCORING_VERSION.value,
            "time_decay": FeatureFlags.ENABLE_TIME_DECAY,
            "two_part_ntee": FeatureFlags.ENABLE_TWO_PART_NTEE,
            "recipient_voting": FeatureFlags.ENABLE_RECIPIENT_VOTING,
            "rollout_percentage": FeatureFlags.ROLLOUT_PERCENTAGE,
        },
    }
