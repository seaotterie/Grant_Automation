"""
Schedule I Grant Analyzer Tool Data Models
Foundation grant-making pattern analysis from 990-PF Schedule I
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict


class GrantCategory(str, Enum):
    """Grant category types"""
    EDUCATION = "education"
    HEALTH = "health"
    ARTS_CULTURE = "arts_culture"
    ENVIRONMENT = "environment"
    HUMAN_SERVICES = "human_services"
    INTERNATIONAL = "international"
    RESEARCH = "research"
    OTHER = "other"


class GrantTier(str, Enum):
    """Grant size tier"""
    MAJOR = "major"  # Top 20% of grants
    SIGNIFICANT = "significant"  # 20-50%
    MODERATE = "moderate"  # 50-80%
    SMALL = "small"  # Bottom 20%


@dataclass
class ScheduleIGrantAnalyzerInput:
    """Input for Schedule I grant analysis"""

    # Foundation identification
    foundation_ein: str
    foundation_name: str

    # Schedule I grant data (list of grants from 990-PF)
    grants: List[Dict[str, any]]  # Each grant: {recipient_name, ein, amount, purpose, city, state}

    # Tax year
    tax_year: int

    # Optional: Organization context for match analysis
    analyzing_organization_ein: Optional[str] = None
    analyzing_organization_name: Optional[str] = None
    analyzing_organization_mission: Optional[str] = None
    analyzing_organization_location: Optional[str] = None


@dataclass
class GrantRecord:
    """Individual grant record"""

    recipient_name: str
    recipient_ein: Optional[str]
    grant_amount: float
    grant_purpose: str
    recipient_city: Optional[str]
    recipient_state: Optional[str]

    # Derived fields
    grant_category: GrantCategory
    grant_tier: GrantTier


@dataclass
class GrantingPatterns:
    """Foundation grant-making patterns"""

    # Volume metrics
    total_grants: int
    total_amount: float
    average_grant: float
    median_grant: float
    largest_grant: float
    smallest_grant: float

    # Distribution by tier
    major_grants_count: int
    major_grants_total: float
    significant_grants_count: int
    significant_grants_total: float
    moderate_grants_count: int
    moderate_grants_total: float
    small_grants_count: int
    small_grants_total: float

    # Category distribution
    category_distribution: Dict[str, int]  # Category -> count
    category_amounts: Dict[str, float]  # Category -> total amount

    # Geographic distribution
    geographic_distribution: Dict[str, int]  # State -> count
    geographic_focus: List[str]  # Top 5 states

    # Focus areas
    primary_focus_areas: List[str]
    secondary_focus_areas: List[str]


@dataclass
class GrantSizeAnalysis:
    """Analysis of grant size patterns"""

    grant_size_tiers: Dict[str, Dict[str, float]]  # Tier -> {min, max, avg, count}
    typical_grant_range: str  # e.g., "$25,000 - $100,000"
    grant_size_recommendation: str
    competitive_grant_size: float


@dataclass
class RecipientProfile:
    """Profile of typical grant recipients"""

    typical_recipient_characteristics: List[str]
    organization_types: List[str]
    geographic_preferences: List[str]
    excluded_types: List[str]


@dataclass
class MatchAnalysis:
    """Match analysis for analyzing organization"""

    # Overall match
    overall_match_score: float  # 0-1
    match_assessment: str

    # Dimensional matches
    mission_alignment_score: float  # 0-1
    geographic_match_score: float  # 0-1
    grant_size_match_score: float  # 0-1
    recipient_type_match_score: float  # 0-1

    # Evidence
    similar_past_grants: List[GrantRecord]
    match_strengths: List[str]
    match_concerns: List[str]

    # Recommendations
    application_strategy: str
    recommended_ask_amount: float
    positioning_recommendations: List[str]


@dataclass
class FoundationIntelligence:
    """Strategic intelligence about foundation"""

    # Grant-making style
    granting_style: str  # "Focused", "Diverse", "Opportunistic"
    decision_making_indicators: List[str]

    # Funding priorities
    stated_priorities: List[str]
    revealed_priorities: List[str]  # From actual grants
    priority_alignment: str

    # Accessibility
    accessibility_assessment: str
    barriers_to_entry: List[str]
    success_factors: List[str]

    # Strategic insights
    strategic_insights: List[str]
    cultivation_strategy: str


@dataclass
class ScheduleIGrantAnalyzerOutput:
    """Complete Schedule I grant analysis output"""

    # Foundation info
    foundation_ein: str
    foundation_name: str
    tax_year: int

    # Grant records
    processed_grants: List[GrantRecord]

    # Patterns
    granting_patterns: GrantingPatterns

    # Size analysis
    grant_size_analysis: GrantSizeAnalysis

    # Recipient profile
    recipient_profile: RecipientProfile

    # Foundation intelligence
    foundation_intelligence: FoundationIntelligence

    # Match analysis (if analyzing_organization provided)
    match_analysis: Optional[MatchAnalysis]

    # Metadata
    analysis_date: str
    data_quality_score: float  # 0-1
    confidence_level: float  # 0-1
    processing_time_seconds: float
    api_cost_usd: float


# Cost configuration
SCHEDULE_I_ANALYZER_COST = 0.03  # $0.03 per analysis
