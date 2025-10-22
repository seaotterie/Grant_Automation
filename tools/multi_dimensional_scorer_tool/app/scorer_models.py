"""
Multi-Dimensional Scorer Tool Data Models
Sophisticated dimensional analysis with stage-specific weights
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class WorkflowStage(str, Enum):
    """Workflow stages for scoring"""
    DISCOVER = "discover"
    PLAN = "plan"
    ANALYZE = "analyze"
    EXAMINE = "examine"
    APPROACH = "approach"


class TrackType(str, Enum):
    """Opportunity track types"""
    NONPROFIT = "nonprofit"
    FEDERAL = "federal"
    STATE = "state"
    COMMERCIAL = "commercial"
    FOUNDATION = "foundation"  # 990-PF foundation opportunities (Composite Scorer V2)


@dataclass
class EnhancedData:
    """Enhanced data availability flags"""
    financial_data: bool = False
    network_data: bool = False
    historical_data: bool = False
    risk_assessment: bool = False

    # Optional actual data references
    financial_metrics: Optional[Dict[str, Any]] = None
    network_analysis: Optional[Dict[str, Any]] = None
    historical_analysis: Optional[Dict[str, Any]] = None
    risk_data: Optional[Dict[str, Any]] = None


@dataclass
class ScoringInput:
    """Input for multi-dimensional scoring"""

    # Core data
    opportunity_data: Dict[str, Any]
    organization_profile: Dict[str, Any]

    # Workflow context
    workflow_stage: WorkflowStage
    track_type: Optional[TrackType] = None

    # Enhanced data (boosts scores)
    enhanced_data: Optional[EnhancedData] = None

    # Custom overrides
    custom_weights: Optional[Dict[str, float]] = None
    custom_boost_factors: Optional[Dict[str, float]] = None


@dataclass
class DimensionalScore:
    """Individual dimension score"""

    dimension_name: str
    raw_score: float  # 0.0-1.0 before weighting
    weight: float  # 0.0-1.0, sum to 1.0 across dimensions
    weighted_score: float  # raw_score * weight
    boost_factor: float  # 1.0 = no boost, >1.0 = boosted
    data_quality: float  # 0.0-1.0, confidence in raw score

    # Metadata
    calculation_method: Optional[str] = None
    data_sources: List[str] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass
class ScoringMetadata:
    """Metadata about scoring execution"""

    scoring_timestamp: str
    stage: str
    track_type: Optional[str]
    dimensions_count: int
    boost_factors_count: int
    data_quality_average: float
    calculation_time_ms: float

    # Configuration used
    weights_used: Dict[str, float] = field(default_factory=dict)
    boost_config_used: Dict[str, float] = field(default_factory=dict)


@dataclass
class MultiDimensionalScore:
    """Complete multi-dimensional scoring output"""

    # Overall scoring
    overall_score: float  # 0.0-1.0, weighted sum of dimensional scores
    confidence: float  # 0.0-1.0, based on data quality and completeness

    # Dimensional breakdown
    dimensional_scores: List[DimensionalScore]

    # Context
    stage: str
    track_type: Optional[str]

    # Enhancements
    boost_factors_applied: List[str]  # Names of boost factors that were applied

    # Metadata
    metadata: ScoringMetadata

    # Optional recommendations
    proceed_recommendation: Optional[bool] = None
    key_strengths: List[str] = field(default_factory=list)
    key_concerns: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)


# Stage-specific dimensional weights (from SCORING_ALGORITHMS.md)

DISCOVER_WEIGHTS = {
    "mission_alignment": 0.30,
    "geographic_fit": 0.25,
    "financial_match": 0.20,
    "eligibility": 0.15,
    "timing": 0.10
}

PLAN_WEIGHTS = {
    "success_probability": 0.30,
    "organizational_capacity": 0.25,
    "financial_viability": 0.20,
    "network_leverage": 0.15,
    "compliance": 0.10
}

ANALYZE_WEIGHTS = {
    "competitive_position": 0.30,
    "strategic_alignment": 0.25,
    "risk_profile": 0.20,
    "implementation_feasibility": 0.15,
    "roi_potential": 0.10
}

EXAMINE_WEIGHTS = {
    "deep_intelligence_quality": 0.30,
    "relationship_pathways": 0.25,
    "strategic_fit": 0.20,
    "partnership_potential": 0.15,
    "innovation_opportunity": 0.10
}

APPROACH_WEIGHTS = {
    "overall_viability": 0.30,
    "success_probability": 0.25,
    "strategic_value": 0.20,
    "resource_requirements": 0.15,
    "timeline_feasibility": 0.10
}

# Foundation-specific weights (990-PF Composite Scorer V2 integration)
# 8 components mapped to 5 dimensions
FOUNDATION_WEIGHTS = {
    "mission_alignment": 0.30,  # NTEE alignment (30%)
    "geographic_fit": 0.20,  # Geographic match (20%)
    "financial_match": 0.28,  # Financial capacity (10%) + Grant size (10%) + Application policy (8%)
    "strategic_alignment": 0.12,  # Recipient coherence (12%)
    "timing": 0.10  # Filing recency (5%) + Foundation type (5%)
}

STAGE_WEIGHTS = {
    WorkflowStage.DISCOVER: DISCOVER_WEIGHTS,
    WorkflowStage.PLAN: PLAN_WEIGHTS,
    WorkflowStage.ANALYZE: ANALYZE_WEIGHTS,
    WorkflowStage.EXAMINE: EXAMINE_WEIGHTS,
    WorkflowStage.APPROACH: APPROACH_WEIGHTS
}

# Boost factors configuration

DEFAULT_BOOST_FACTORS = {
    "financial_data": 0.10,  # +10% to financial dimensions
    "network_data": 0.15,  # +15% to network/relationship dimensions
    "historical_data": 0.12,  # +12% to success probability
    "risk_assessment": 0.08  # +8% to viability scores
}

# Dimension boost mapping (which dimensions get boosted by which data)

DIMENSION_BOOST_MAP = {
    # Financial data boosts
    "financial_match": ["financial_data"],
    "financial_viability": ["financial_data"],
    "resource_requirements": ["financial_data"],

    # Network data boosts
    "network_leverage": ["network_data"],
    "relationship_pathways": ["network_data"],
    "partnership_potential": ["network_data"],

    # Historical data boosts
    "success_probability": ["historical_data"],

    # Risk assessment boosts
    "overall_viability": ["risk_assessment"],
    "risk_profile": ["risk_assessment"],

    # Strategic alignment gets boost from multiple sources
    "strategic_fit": ["financial_data", "network_data", "risk_assessment"]
}

# Cost configuration
MULTI_DIMENSIONAL_SCORER_COST = 0.00  # No AI calls - pure algorithmic
