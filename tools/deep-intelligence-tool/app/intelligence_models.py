"""
Deep Intelligence Tool Data Models
Comprehensive intelligence analysis with configurable depth levels.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class AnalysisDepth(Enum):
    """Analysis depth levels matching 4-tier business packages"""
    QUICK = "quick"          # $0.75, 5-10 min - CURRENT tier
    STANDARD = "standard"    # $7.50, 15-20 min - STANDARD tier
    ENHANCED = "enhanced"    # $22.00, 30-45 min - ENHANCED tier
    COMPLETE = "complete"    # $42.00, 45-60 min - COMPLETE tier


class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SuccessProbability(Enum):
    """Success probability categories"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


# Input Models

@dataclass
class DeepIntelligenceInput:
    """Input for deep intelligence analysis"""
    # From screening tool
    opportunity_id: str
    opportunity_title: str
    opportunity_description: str
    funder_name: str
    funder_type: str

    # Organization context
    organization_ein: str
    organization_name: str
    organization_mission: str
    organization_revenue: Optional[float] = None

    # Analysis configuration
    depth: AnalysisDepth = AnalysisDepth.QUICK
    screening_score: Optional[float] = None
    user_notes: Optional[str] = None
    focus_areas: List[str] = field(default_factory=list)

    # Additional opportunity data
    opportunity_amount_min: Optional[float] = None
    opportunity_amount_max: Optional[float] = None
    opportunity_deadline: Optional[str] = None
    opportunity_focus_areas: List[str] = field(default_factory=list)


# Core Analysis Models (All Depths)

@dataclass
class StrategicFitAnalysis:
    """Strategic fit assessment"""
    fit_score: float  # 0.0 - 1.0
    mission_alignment_score: float
    program_alignment_score: float
    geographic_alignment_score: float

    # Detailed rationale
    alignment_strengths: List[str]
    alignment_concerns: List[str]
    strategic_rationale: str

    # Recommendations
    strategic_positioning: str
    key_differentiators: List[str]


@dataclass
class FinancialViabilityAnalysis:
    """Financial viability assessment"""
    viability_score: float  # 0.0 - 1.0
    budget_capacity_score: float
    financial_health_score: float
    sustainability_score: float

    # Analysis
    budget_implications: str
    resource_requirements: Dict[str, Any]
    financial_risks: List[str]

    # Recommendations
    financial_strategy: str
    budget_recommendations: List[str]


@dataclass
class OperationalReadinessAnalysis:
    """Operational readiness assessment"""
    readiness_score: float  # 0.0 - 1.0
    capacity_score: float
    timeline_feasibility_score: float
    infrastructure_readiness_score: float

    # Analysis
    capacity_gaps: List[str]
    infrastructure_requirements: List[str]
    timeline_challenges: List[str]

    # Recommendations
    capacity_building_plan: str
    operational_recommendations: List[str]
    estimated_preparation_time_weeks: int


@dataclass
class RiskFactor:
    """Individual risk factor"""
    category: str  # "eligibility", "competition", "capacity", "timeline", "financial"
    risk_level: RiskLevel
    description: str
    impact: str
    mitigation_strategy: str
    probability: float  # 0.0 - 1.0


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment"""
    overall_risk_level: RiskLevel
    overall_risk_score: float  # 0.0 - 1.0
    risk_factors: List[RiskFactor]

    # Summary
    critical_risks: List[str]
    manageable_risks: List[str]
    risk_mitigation_plan: str


# Enhanced Features (Standard+ Depths)

@dataclass
class HistoricalGrant:
    """Historical grant record"""
    recipient_name: str
    grant_amount: float
    grant_year: int
    purpose: str
    geographic_location: Optional[str] = None


@dataclass
class HistoricalAnalysis:
    """Historical funding intelligence (Standard+ depths)"""
    historical_grants: List[HistoricalGrant]
    total_grants_analyzed: int
    total_funding_amount: float

    # Patterns
    average_grant_size: float
    typical_grant_range: str
    funding_trends: str
    geographic_patterns: str

    # Insights
    similar_recipient_profiles: List[str]
    success_factors: List[str]
    competitive_intelligence: str


@dataclass
class GeographicAnalysis:
    """Geographic analysis (Standard+ depths)"""
    primary_service_area: str
    funder_geographic_focus: str
    geographic_alignment_score: float

    # Analysis
    geographic_fit_assessment: str
    regional_competition_analysis: str
    location_advantages: List[str]
    location_challenges: List[str]


# Advanced Features (Enhanced+ Depths)

@dataclass
class BoardMember:
    """Board member information"""
    name: str
    title: Optional[str] = None
    affiliations: List[str] = field(default_factory=list)
    influence_score: Optional[float] = None


@dataclass
class NetworkConnection:
    """Network relationship"""
    connection_type: str  # "board_overlap", "partnership", "funding"
    connected_entity: str
    strength: float  # 0.0 - 1.0
    description: str


@dataclass
class NetworkAnalysis:
    """Network intelligence (Enhanced+ depths)"""
    board_connections: List[BoardMember]
    network_connections: List[NetworkConnection]

    # Metrics
    network_strength_score: float
    relationship_advantages: List[str]

    # Strategy
    relationship_leverage_strategy: str
    key_contacts_to_cultivate: List[str]


@dataclass
class RelationshipMap:
    """Relationship mapping (Enhanced+ depths)"""
    direct_relationships: List[str]
    indirect_relationships: List[str]
    partnership_opportunities: List[str]

    # Intelligence
    relationship_insights: str
    cultivation_strategy: str


# Premium Features (Complete Depth Only)

@dataclass
class PolicyAlignment:
    """Policy alignment analysis"""
    relevant_policies: List[str]
    alignment_score: float
    policy_opportunities: List[str]
    policy_risks: List[str]


@dataclass
class PolicyAnalysis:
    """Policy analysis (Complete depth only)"""
    federal_policy_alignment: PolicyAlignment
    state_policy_alignment: Optional[PolicyAlignment]

    # Strategic insights
    policy_landscape_summary: str
    policy_opportunities: List[str]
    advocacy_recommendations: List[str]


@dataclass
class StrategicConsultingInsights:
    """Strategic consulting insights (Complete depth only)"""
    executive_summary: str
    competitive_positioning: str
    differentiation_strategy: str

    # Long-term strategy
    multi_year_funding_strategy: str
    partnership_development_strategy: str
    capacity_building_roadmap: str

    # Action plan
    immediate_actions: List[str]
    medium_term_actions: List[str]
    long_term_actions: List[str]


# Output Model

@dataclass
class DeepIntelligenceOutput:
    """Comprehensive intelligence analysis output"""
    # Core Analysis (All Depths)
    strategic_fit: StrategicFitAnalysis
    financial_viability: FinancialViabilityAnalysis
    operational_readiness: OperationalReadinessAnalysis
    risk_assessment: RiskAssessment

    # Overall Assessment
    proceed_recommendation: bool
    success_probability: SuccessProbability
    overall_score: float  # 0.0 - 1.0

    # Executive Summary
    executive_summary: str
    key_strengths: List[str]
    key_challenges: List[str]
    recommended_next_steps: List[str]

    # Enhanced Features (Standard+ depths only)
    historical_intelligence: Optional[HistoricalAnalysis] = None
    geographic_analysis: Optional[GeographicAnalysis] = None

    # Advanced Features (Enhanced+ depths only)
    network_intelligence: Optional[NetworkAnalysis] = None
    relationship_mapping: Optional[RelationshipMap] = None

    # Premium Features (Complete depth only)
    policy_analysis: Optional[PolicyAnalysis] = None
    strategic_consulting: Optional[StrategicConsultingInsights] = None

    # Metadata
    depth_executed: str
    processing_time_seconds: float
    api_cost_usd: float
    timestamp: datetime = field(default_factory=datetime.now)
    tool_version: str = "1.0.0"


# Depth Configuration

DEPTH_FEATURES = {
    AnalysisDepth.QUICK: {
        "cost": 0.75,
        "time_minutes": (5, 10),
        "features": [
            "strategic_fit",
            "financial_viability",
            "operational_readiness",
            "risk_assessment"
        ],
        "equivalent_to": "CURRENT tier ($0.75)"
    },
    AnalysisDepth.STANDARD: {
        "cost": 7.50,
        "time_minutes": (15, 20),
        "features": [
            "strategic_fit",
            "financial_viability",
            "operational_readiness",
            "risk_assessment",
            "historical_intelligence",
            "geographic_analysis"
        ],
        "equivalent_to": "STANDARD tier ($7.50)"
    },
    AnalysisDepth.ENHANCED: {
        "cost": 22.00,
        "time_minutes": (30, 45),
        "features": [
            "strategic_fit",
            "financial_viability",
            "operational_readiness",
            "risk_assessment",
            "historical_intelligence",
            "geographic_analysis",
            "network_intelligence",
            "relationship_mapping"
        ],
        "equivalent_to": "ENHANCED tier ($22.00)"
    },
    AnalysisDepth.COMPLETE: {
        "cost": 42.00,
        "time_minutes": (45, 60),
        "features": [
            "strategic_fit",
            "financial_viability",
            "operational_readiness",
            "risk_assessment",
            "historical_intelligence",
            "geographic_analysis",
            "network_intelligence",
            "relationship_mapping",
            "policy_analysis",
            "strategic_consulting"
        ],
        "equivalent_to": "COMPLETE tier ($42.00)"
    }
}
