"""
Screening Tool Data Models
Pydantic models for opportunity screening input/output.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class ScreeningMode(Enum):
    """Screening analysis depth"""
    FAST = "fast"          # Quick screening ($0.0004/opp) - PLAN tab equivalent
    THOROUGH = "thorough"  # Enhanced screening ($0.02-0.04/opp) - ANALYZE tab equivalent


@dataclass
class OrganizationProfile:
    """Organization profile for screening context"""
    ein: str
    name: str
    mission: str
    ntee_codes: List[str]
    geographic_focus: List[str]
    program_areas: List[str]
    annual_revenue: Optional[float] = None
    staff_count: Optional[int] = None
    years_established: Optional[int] = None


@dataclass
class Opportunity:
    """Grant opportunity to be screened"""
    opportunity_id: str
    title: str
    funder: str
    funder_type: str  # "foundation", "government", "corporate"
    description: str

    # Financial
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    typical_award_size: Optional[float] = None

    # Timing
    deadline: Optional[str] = None
    award_date: Optional[str] = None
    project_duration_months: Optional[int] = None

    # Eligibility
    geographic_restrictions: List[str] = field(default_factory=list)
    ntee_requirements: List[str] = field(default_factory=list)
    revenue_requirements: Optional[str] = None

    # Additional
    focus_areas: List[str] = field(default_factory=list)
    past_recipients: List[str] = field(default_factory=list)
    application_requirements: List[str] = field(default_factory=list)


@dataclass
class ScreeningInput:
    """Input for screening tool"""
    opportunities: List[Opportunity]
    organization_profile: OrganizationProfile
    screening_mode: ScreeningMode = ScreeningMode.FAST
    minimum_threshold: float = 0.55  # Default threshold
    max_recommendations: int = 10


@dataclass
class OpportunityScore:
    """Screening score for a single opportunity"""
    opportunity_id: str
    opportunity_title: str

    # Overall Assessment
    overall_score: float  # 0.0 - 1.0
    proceed_to_deep_analysis: bool
    confidence_level: str  # "high", "medium", "low"

    # Dimensional Scores
    strategic_fit_score: float  # Mission/program alignment
    eligibility_score: float    # Meets requirements
    timing_score: float         # Deadline feasibility
    financial_score: float      # Funding amount fit
    competition_score: float    # Competitive positioning

    # Summary
    one_sentence_summary: str
    key_strengths: List[str] = field(default_factory=list)
    key_concerns: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)

    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    estimated_effort_hours: Optional[int] = None

    # Metadata (fast mode only provides basics)
    analysis_depth: str = "fast"  # "fast" or "thorough"


@dataclass
class ScreeningOutput:
    """Output from screening tool"""
    # Summary Statistics
    total_screened: int
    passed_threshold: int
    recommended_for_deep_analysis: List[str]  # List of opportunity_ids

    # Detailed Scores
    opportunity_scores: List[OpportunityScore]

    # Analysis Metadata
    screening_mode: str
    threshold_used: float
    processing_time_seconds: float
    total_cost_usd: float

    # Execution Context
    timestamp: datetime = field(default_factory=datetime.now)
    tool_version: str = "1.0.0"

    # Quality Metrics
    avg_confidence_level: Optional[str] = None
    high_confidence_count: int = 0


@dataclass
class BatchScreeningResult:
    """Result from batch screening multiple opportunity sets"""
    batch_id: str
    outputs: List[ScreeningOutput]
    total_opportunities_screened: int
    total_cost_usd: float
    total_processing_time_seconds: float
    started_at: datetime
    completed_at: datetime


# Example Schemas for Reference
FAST_MODE_FEATURES = {
    "cost_per_opportunity": 0.0004,
    "processing_time_seconds": 2,
    "analysis_depth": "Quick strategic fit assessment",
    "dimensions_scored": ["strategic_fit", "eligibility_basic", "timing"],
    "equivalent_to": "PLAN tab processor"
}

THOROUGH_MODE_FEATURES = {
    "cost_per_opportunity": 0.02,  # Up to $0.04 with complex analysis
    "processing_time_seconds": 5,
    "analysis_depth": "Comprehensive multi-dimensional analysis",
    "dimensions_scored": ["strategic_fit", "eligibility_detailed", "timing", "financial", "competition"],
    "equivalent_to": "ANALYZE tab processor"
}
