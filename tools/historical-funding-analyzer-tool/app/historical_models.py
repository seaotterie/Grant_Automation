"""
Historical Funding Analyzer Tool Data Models
Analysis of USASpending.gov and historical funding data
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class HistoricalAnalysisInput:
    """Input for historical funding analysis"""

    # Required fields
    organization_ein: str
    historical_data: List[Dict[str, Any]]  # List of historical awards

    # Optional analysis parameters
    analysis_years: Optional[int] = 5  # Default to 5 years
    include_geographic: bool = True
    include_temporal: bool = True
    include_patterns: bool = True
    include_competitive: bool = False

    # Filtering
    min_award_amount: Optional[float] = None
    award_categories: Optional[List[str]] = None


@dataclass
class FundingPattern:
    """Identified funding pattern"""

    pattern_type: str  # award_size, frequency, category, etc.
    pattern_name: str
    description: str
    frequency: int
    total_amount: float
    percentage_of_total: float
    examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class GeographicDistribution:
    """Geographic funding distribution"""

    state: str
    award_count: int
    total_funding: float
    percentage_of_total: float
    average_award_size: float
    agencies: List[str] = field(default_factory=list)


@dataclass
class TemporalTrend:
    """Temporal funding trend"""

    year: int
    award_count: int
    total_funding: float
    average_award_size: float
    year_over_year_change: Optional[float] = None
    trend_direction: Optional[str] = None  # increasing, decreasing, stable


@dataclass
class CompetitiveInsight:
    """Competitive analysis insight"""

    insight_type: str
    description: str
    metric_value: float
    comparison_to_peers: str
    recommendation: str


@dataclass
class HistoricalAnalysisMetadata:
    """Metadata about historical analysis"""

    analysis_timestamp: str
    years_analyzed: int
    total_awards_analyzed: int
    date_range_start: str
    date_range_end: str
    analysis_time_ms: float
    data_quality_score: float  # 0.0-1.0


@dataclass
class HistoricalAnalysis:
    """Complete historical funding analysis output"""

    # Summary metrics
    organization_ein: str
    total_awards: int
    total_funding: float
    average_award_size: float
    years_analyzed: int

    # Analysis results
    funding_patterns: List[FundingPattern]
    geographic_distribution: List[GeographicDistribution]
    temporal_trends: List[TemporalTrend]
    competitive_insights: List[CompetitiveInsight]

    # Metadata
    metadata: HistoricalAnalysisMetadata

    # Key insights
    key_insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# Award size categories
AWARD_SIZE_CATEGORIES = {
    "micro": (0, 10000),
    "small": (10000, 50000),
    "medium": (50000, 250000),
    "large": (250000, 1000000),
    "major": (1000000, float('inf'))
}

# Trend thresholds
TREND_THRESHOLD_INCREASE = 0.10  # 10% increase = increasing trend
TREND_THRESHOLD_DECREASE = -0.10  # 10% decrease = decreasing trend

# Cost configuration
HISTORICAL_FUNDING_ANALYZER_COST = 0.00  # No AI calls - data analysis only
