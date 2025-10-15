"""
Financial Intelligence Tool Data Models
Comprehensive financial analysis with AI-enhanced insights
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict


class FinancialHealthRating(str, Enum):
    """Overall financial health rating"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    CONCERNING = "concerning"
    CRITICAL = "critical"


class TrendDirection(str, Enum):
    """Trend direction indicator"""
    STRONGLY_POSITIVE = "strongly_positive"
    POSITIVE = "positive"
    STABLE = "stable"
    NEGATIVE = "negative"
    STRONGLY_NEGATIVE = "strongly_negative"


@dataclass
class FinancialIntelligenceInput:
    """Input for financial intelligence analysis"""

    # Organization identification
    organization_ein: str
    organization_name: str

    # Financial data (from 990)
    total_revenue: float
    total_expenses: float
    total_assets: float
    total_liabilities: float
    net_assets: float

    # Revenue breakdown
    contributions_grants: float
    program_service_revenue: float
    investment_income: float
    other_revenue: float

    # Expense breakdown
    program_expenses: float
    admin_expenses: float
    fundraising_expenses: float

    # Historical data (optional, for trend analysis)
    prior_year_revenue: Optional[float] = None
    prior_year_expenses: Optional[float] = None
    prior_year_net_assets: Optional[float] = None

    # Context for AI analysis
    organization_mission: Optional[str] = None
    ntee_code: Optional[str] = None
    years_of_operation: Optional[int] = None


@dataclass
class FinancialMetrics:
    """Calculated financial metrics"""

    # Liquidity metrics
    current_ratio: float
    months_of_expenses: float
    liquid_assets_ratio: float

    # Efficiency metrics
    program_expense_ratio: float
    admin_expense_ratio: float
    fundraising_expense_ratio: float
    fundraising_efficiency: float

    # Sustainability metrics
    revenue_growth_rate: Optional[float]
    expense_growth_rate: Optional[float]
    net_assets_growth_rate: Optional[float]
    operating_margin: float

    # Diversification metrics
    revenue_concentration_score: float  # 0-1, lower is more diversified
    largest_revenue_source_pct: float

    # Capacity metrics
    asset_to_revenue_ratio: float
    debt_to_asset_ratio: float


@dataclass
class FinancialStrength:
    """Assessment of financial strengths"""

    strength_category: str  # e.g., "Liquidity", "Efficiency", "Growth"
    description: str
    metric_value: float
    metric_name: str
    percentile: Optional[float]  # Compared to peers if available


@dataclass
class FinancialConcern:
    """Assessment of financial concerns"""

    concern_category: str  # e.g., "Liquidity", "Efficiency", "Sustainability"
    description: str
    severity: str  # "low", "medium", "high", "critical"
    metric_value: float
    metric_name: str
    recommendation: str


@dataclass
class TrendAnalysis:
    """Multi-year trend analysis"""

    metric_name: str
    direction: TrendDirection
    percentage_change: float
    interpretation: str
    forecast: Optional[str]  # AI-generated forecast


@dataclass
class GrantCapacityAssessment:
    """Assessment of grant management capacity"""

    # Financial capacity
    can_handle_budget: float  # Maximum grant size recommended
    budget_capacity_score: float  # 0-1
    budget_capacity_reasoning: str

    # Administrative capacity
    admin_capacity_score: float  # 0-1
    admin_capacity_concerns: List[str]

    # Sustainability indicators
    sustainability_score: float  # 0-1
    sustainability_concerns: List[str]

    # Match requirement capability
    can_provide_match: bool
    max_match_percentage: float
    match_source_suggestions: List[str]


@dataclass
class AIFinancialInsights:
    """AI-generated financial insights"""

    # Executive summary
    executive_summary: str

    # Strategic insights
    strategic_opportunities: List[str]
    strategic_risks: List[str]

    # Competitive positioning
    competitive_advantages: List[str]
    competitive_weaknesses: List[str]

    # Recommendations
    financial_management_recommendations: List[str]
    grant_strategy_recommendations: List[str]

    # Industry context
    industry_comparison: Optional[str]
    peer_benchmarking_insights: Optional[str]


@dataclass
class FinancialIntelligenceOutput:
    """Complete financial intelligence output"""

    # Core metrics
    metrics: FinancialMetrics

    # Overall assessment
    overall_health_rating: FinancialHealthRating
    overall_health_score: float  # 0-1

    # Strengths and concerns
    strengths: List[FinancialStrength]
    concerns: List[FinancialConcern]

    # Trend analysis
    trends: List[TrendAnalysis]

    # Grant capacity
    grant_capacity: GrantCapacityAssessment

    # AI insights
    ai_insights: AIFinancialInsights

    # Metadata
    analysis_date: str
    data_quality_score: float  # 0-1, based on completeness
    confidence_level: float  # 0-1, AI confidence in analysis
    processing_time_seconds: float
    api_cost_usd: float


# Cost configuration
FINANCIAL_INTELLIGENCE_COST = 0.03  # $0.03 per analysis
