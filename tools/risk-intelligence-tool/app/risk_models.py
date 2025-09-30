"""
Risk Intelligence Tool Data Models
Multi-dimensional risk assessment with mitigation strategies
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict


class RiskLevel(str, Enum):
    """Risk level indicator"""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(str, Enum):
    """Risk category types"""
    ELIGIBILITY = "eligibility"
    COMPETITION = "competition"
    CAPACITY = "capacity"
    TIMELINE = "timeline"
    FINANCIAL = "financial"
    COMPLIANCE = "compliance"
    REPUTATIONAL = "reputational"
    OPERATIONAL = "operational"


class MitigationPriority(str, Enum):
    """Mitigation priority level"""
    IMMEDIATE = "immediate"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RiskIntelligenceInput:
    """Input for risk intelligence analysis"""

    # Opportunity identification
    opportunity_id: str
    opportunity_title: str
    opportunity_description: str
    funder_name: str
    funder_type: str  # foundation, government, corporate

    # Organization context
    organization_ein: str
    organization_name: str
    organization_mission: str
    years_of_operation: Optional[int] = None

    # Opportunity details
    grant_amount: Optional[float] = None
    application_deadline: Optional[str] = None
    project_duration_months: Optional[int] = None
    match_required: Optional[bool] = None
    match_percentage: Optional[float] = None

    # Eligibility criteria
    geographic_restrictions: Optional[List[str]] = None
    organization_type_requirements: Optional[List[str]] = None
    budget_size_requirements: Optional[Dict[str, float]] = None

    # Organization capabilities
    total_revenue: Optional[float] = None
    total_expenses: Optional[float] = None
    net_assets: Optional[float] = None
    program_expense_ratio: Optional[float] = None
    staff_count: Optional[int] = None
    has_grant_manager: Optional[bool] = None
    prior_grants_with_funder: Optional[int] = None

    # Competitive context
    estimated_applicants: Optional[int] = None
    typical_award_rate: Optional[float] = None

    # User notes
    concerns: Optional[List[str]] = None


@dataclass
class RiskFactor:
    """Individual risk factor"""

    category: RiskCategory
    risk_level: RiskLevel
    description: str
    likelihood: float  # 0-1
    impact: float  # 0-1
    risk_score: float  # likelihood × impact
    evidence: List[str]
    related_factors: Optional[List[str]] = None


@dataclass
class MitigationStrategy:
    """Risk mitigation strategy"""

    risk_category: RiskCategory
    strategy: str
    priority: MitigationPriority
    timeline: str  # e.g., "Before application", "During project", "Ongoing"
    resources_required: List[str]
    success_indicators: List[str]
    estimated_cost: Optional[float] = None
    estimated_time_days: Optional[int] = None


@dataclass
class EligibilityRiskAssessment:
    """Detailed eligibility risk analysis"""

    overall_eligibility_score: float  # 0-1
    risk_level: RiskLevel

    # Geographic eligibility
    geographic_match: bool
    geographic_concerns: List[str]

    # Organization type eligibility
    type_match: bool
    type_concerns: List[str]

    # Budget/size eligibility
    budget_match: bool
    budget_concerns: List[str]

    # Other eligibility factors
    other_requirements_met: bool
    other_concerns: List[str]

    # Overall assessment
    proceed_recommendation: bool
    recommendation_reasoning: str


@dataclass
class CompetitionRiskAssessment:
    """Competition and success probability analysis"""

    competition_level: RiskLevel
    estimated_competition_score: float  # 0-1, higher = more competitive

    # Competition factors
    estimated_applicant_pool: str  # e.g., "50-100 applicants"
    typical_success_rate: Optional[float]
    organization_competitive_position: str

    # Competitive advantages
    competitive_strengths: List[str]
    competitive_weaknesses: List[str]

    # Success probability
    estimated_success_probability: float  # 0-1
    success_probability_reasoning: str


@dataclass
class CapacityRiskAssessment:
    """Organizational capacity risk analysis"""

    capacity_risk_level: RiskLevel
    overall_capacity_score: float  # 0-1

    # Staff capacity
    staff_capacity_adequate: bool
    staff_concerns: List[str]

    # Infrastructure capacity
    infrastructure_adequate: bool
    infrastructure_concerns: List[str]

    # Management capacity
    management_capacity_adequate: bool
    management_concerns: List[str]

    # Grant management experience
    grant_experience_adequate: bool
    experience_concerns: List[str]

    # Capacity gaps
    critical_gaps: List[str]
    moderate_gaps: List[str]


@dataclass
class TimelineRiskAssessment:
    """Timeline and deadline risk analysis"""

    timeline_risk_level: RiskLevel
    timeline_feasibility_score: float  # 0-1

    # Application timeline
    days_until_deadline: Optional[int]
    application_time_required: int
    timeline_adequate: bool
    deadline_concerns: List[str]

    # Project timeline
    project_timeline_feasible: bool
    project_concerns: List[str]

    # Critical dates
    critical_milestones: List[Dict[str, str]]


@dataclass
class FinancialRiskAssessment:
    """Financial risk analysis"""

    financial_risk_level: RiskLevel
    financial_risk_score: float  # 0-1

    # Budget risk
    can_manage_budget: bool
    budget_concerns: List[str]

    # Match requirement risk
    can_provide_match: bool
    match_concerns: List[str]

    # Cash flow risk
    cash_flow_adequate: bool
    cash_flow_concerns: List[str]

    # Sustainability risk
    sustainability_concerns: List[str]


@dataclass
class ComplianceRiskAssessment:
    """Compliance and regulatory risk analysis"""

    compliance_risk_level: RiskLevel
    compliance_risk_score: float  # 0-1

    # Regulatory compliance
    regulatory_requirements: List[str]
    regulatory_concerns: List[str]

    # Reporting requirements
    reporting_requirements: List[str]
    reporting_concerns: List[str]

    # Audit requirements
    audit_requirements: List[str]
    audit_concerns: List[str]


@dataclass
class AIRiskInsights:
    """AI-generated risk insights"""

    # Executive summary
    risk_executive_summary: str

    # Critical risks
    top_3_risks: List[str]
    deal_breaker_risks: List[str]

    # Hidden risks
    overlooked_risks: List[str]

    # Strategic considerations
    strategic_risk_factors: List[str]

    # Recommendations
    go_no_go_recommendation: bool
    recommendation_confidence: float  # 0-1
    recommendation_reasoning: str

    # Alternative approaches
    risk_reduction_suggestions: List[str]


@dataclass
class RiskIntelligenceOutput:
    """Complete risk intelligence output"""

    # Overall risk assessment
    overall_risk_level: RiskLevel
    overall_risk_score: float  # 0-1
    proceed_recommendation: bool

    # Risk factors
    all_risk_factors: List[RiskFactor]
    critical_risks: List[RiskFactor]
    high_risks: List[RiskFactor]
    manageable_risks: List[RiskFactor]

    # Dimensional assessments
    eligibility_assessment: EligibilityRiskAssessment
    competition_assessment: CompetitionRiskAssessment
    capacity_assessment: CapacityRiskAssessment
    timeline_assessment: TimelineRiskAssessment
    financial_assessment: FinancialRiskAssessment
    compliance_assessment: ComplianceRiskAssessment

    # Mitigation strategies
    mitigation_strategies: List[MitigationStrategy]
    immediate_actions: List[str]

    # AI insights
    ai_insights: AIRiskInsights

    # Risk summary
    risk_summary: str
    key_decision_factors: List[str]

    # Metadata
    analysis_date: str
    confidence_level: float  # 0-1
    processing_time_seconds: float
    api_cost_usd: float


# Cost configuration
RISK_INTELLIGENCE_COST = 0.02  # $0.02 per analysis
