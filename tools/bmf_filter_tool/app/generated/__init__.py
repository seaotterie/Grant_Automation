"""
Generated BAML types for BMF Filter Tool

This module contains auto-generated Pydantic models from BAML schemas.
These types ensure type-safe interaction between LLM outputs and tool logic.

To regenerate these types:
1. Update schemas in baml_src/
2. Run: baml generate
3. Generated types will appear in this directory

Note: This file and types are auto-generated. Do not edit manually.
"""

# BAML generated types will be imported here
# For now, we'll create manual types matching the BAML schema
# In production, these would be auto-generated

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

# Enums
class BMFSearchPriority(str, Enum):
    quick = "quick"
    standard = "standard"
    thorough = "thorough"

class BMFGeographicScope(str, Enum):
    local = "local"
    regional = "regional"
    national = "national"
    any = "any"

class BMFFoundationType(str, Enum):
    public_charity = "public_charity"
    private_foundation = "private_foundation"
    operating_foundation = "operating_foundation"
    community_foundation = "community_foundation"
    corporate_foundation = "corporate_foundation"
    any = "any"

class BMFDataQuality(str, Enum):
    basic = "basic"
    standard = "standard"
    comprehensive = "comprehensive"

class BMFSortOption(str, Enum):
    revenue_desc = "revenue_desc"
    revenue_asc = "revenue_asc"
    assets_desc = "assets_desc"
    assets_asc = "assets_asc"
    name_asc = "name_asc"
    recent_filing = "recent_filing"

class BMFQueryComplexity(str, Enum):
    simple = "simple"
    moderate = "moderate"
    complex = "complex"
    very_complex = "very_complex"

# Context classes
class BMFSearchContext(BaseModel):
    use_case: Optional[str] = Field(None, description="What this search will be used for")
    target_audience: Optional[str] = Field(None, description="Who will use these results")
    follow_up_actions: Optional[List[str]] = Field(None, description="What happens after this search")

# Criteria classes
class BMFFilterCriteria(BaseModel):
    # Geographic filters
    states: Optional[List[str]] = Field(None, description="State codes like VA, MD, DC")
    cities: Optional[List[str]] = Field(None, description="City names for additional filtering")
    geographic_scope: Optional[BMFGeographicScope] = Field(None, description="Geographic scope preference")

    # Financial filters
    revenue_min: Optional[int] = Field(None, description="Minimum annual revenue in dollars")
    revenue_max: Optional[int] = Field(None, description="Maximum annual revenue in dollars")
    asset_min: Optional[int] = Field(None, description="Minimum total assets in dollars")
    asset_max: Optional[int] = Field(None, description="Maximum total assets in dollars")

    # NTEE code filters
    ntee_codes: Optional[List[str]] = Field(None, description="NTEE codes like P20, B25, etc.")
    ntee_major_groups: Optional[List[str]] = Field(None, description="Major NTEE groups like P, B")

    # Organization characteristics
    organization_name: Optional[str] = Field(None, description="Partial name search")
    foundation_type: Optional[BMFFoundationType] = Field(None, description="Type of foundation")

    # Data quality filters
    has_recent_990: Optional[bool] = Field(None, description="Must have recent Form 990")
    min_data_quality: Optional[BMFDataQuality] = Field(None, description="Minimum data quality")

    # Result configuration
    limit: Optional[int] = Field(100, description="Maximum results to return")
    sort_by: Optional[BMFSortOption] = Field(BMFSortOption.revenue_desc, description="Sort option")
    include_metadata: Optional[bool] = Field(True, description="Include execution metadata")

# Intent class
class BMFFilterIntent(BaseModel):
    intent: str = Field("bmf_filter", description="Tool intent identifier")
    criteria: BMFFilterCriteria = Field(..., description="Search criteria")
    what_youre_looking_for: str = Field(..., description="Human description of search goal")
    priority: Optional[BMFSearchPriority] = Field(BMFSearchPriority.standard, description="Search priority")
    context: Optional[BMFSearchContext] = Field(None, description="Additional context")

# Organization class
class BMFOrganization(BaseModel):
    # Primary identifiers
    ein: str = Field(..., description="Employer ID Number")
    name: str = Field(..., description="Official organization name")

    # Location
    city: Optional[str] = Field(None, description="City location")
    state: str = Field(..., description="State location (2-letter code)")
    zip_code: Optional[str] = Field(None, description="ZIP code")

    # Classification
    ntee_code: str = Field(..., description="NTEE code")
    ntee_description: Optional[str] = Field(None, description="NTEE description")
    foundation_code: Optional[str] = Field(None, description="Foundation classification")

    # Financial data
    revenue: Optional[int] = Field(None, description="Annual revenue")
    assets: Optional[int] = Field(None, description="Total assets")
    expenses: Optional[int] = Field(None, description="Annual expenses")
    grants_paid: Optional[int] = Field(None, description="Grants paid")

    # Data quality
    latest_990_year: Optional[int] = Field(None, description="Latest 990 filing year")
    data_completeness: Optional[float] = Field(None, description="Data completeness score")

    # Match information
    match_reasons: List[str] = Field(default_factory=list, description="Why this org matched")
    match_score: Optional[float] = Field(None, description="Relevance score")

    # Catalynx integration
    catalynx_analyzed: Optional[bool] = Field(None, description="Analyzed by Catalynx")
    existing_opportunities: Optional[int] = Field(None, description="Existing opportunities")

# Summary classes
class BMFSearchSummary(BaseModel):
    total_found: int = Field(..., description="Total organizations found")
    total_in_database: int = Field(..., description="Total organizations checked")
    criteria_summary: str = Field(..., description="Human readable criteria summary")
    top_matches_description: str = Field(..., description="Description of top matches")
    geographic_distribution: str = Field(..., description="Geographic distribution")
    financial_summary: str = Field(..., description="Financial characteristics summary")
    recommendations: List[str] = Field(default_factory=list, description="Search refinement suggestions")

class BMFExecutionData(BaseModel):
    execution_time_ms: float = Field(..., description="Total execution time")
    database_query_time_ms: float = Field(..., description="Database query time")
    processing_time_ms: float = Field(..., description="Processing time")

    cache_hit: bool = Field(..., description="Whether result came from cache")
    cache_key: Optional[str] = Field(None, description="Cache key used")

    results_truncated: bool = Field(..., description="Whether results were truncated")
    query_complexity: BMFQueryComplexity = Field(..., description="Query complexity")

    memory_used_mb: Optional[float] = Field(None, description="Memory used")
    database_rows_scanned: Optional[int] = Field(None, description="Rows scanned")

    compared_to_existing: Optional[bool] = Field(None, description="Compared to existing processor")
    performance_vs_existing: Optional[float] = Field(None, description="Performance ratio vs existing")

class BMFQualityAssessment(BaseModel):
    overall_quality: float = Field(..., description="Overall quality score")
    completeness_rate: float = Field(..., description="Completeness rate")
    recent_data_rate: float = Field(..., description="Recent data rate")
    geographic_coverage: str = Field(..., description="Geographic coverage assessment")
    recommendations: List[str] = Field(default_factory=list, description="Quality improvement suggestions")

class BMFRecommendations(BaseModel):
    refinement_suggestions: List[str] = Field(default_factory=list, description="Refinement suggestions")
    expansion_suggestions: List[str] = Field(default_factory=list, description="Expansion suggestions")
    next_steps: List[str] = Field(default_factory=list, description="Next steps")
    related_searches: List[str] = Field(default_factory=list, description="Related searches")

# Result class
class BMFFilterResult(BaseModel):
    intent: str = Field("bmf_filter_result", description="Result intent identifier")
    organizations: List[BMFOrganization] = Field(default_factory=list, description="Found organizations")
    summary: BMFSearchSummary = Field(..., description="Search summary")
    execution_metadata: BMFExecutionData = Field(..., description="Execution metadata")
    quality_assessment: BMFQualityAssessment = Field(..., description="Quality assessment")
    recommendations: Optional[BMFRecommendations] = Field(None, description="Recommendations")

# Validation result
class BMFValidationResult(BaseModel):
    is_valid: bool = Field(..., description="Whether criteria are valid")
    issues: List[str] = Field(default_factory=list, description="Validation issues")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions")
    estimated_results: Optional[int] = Field(None, description="Estimated result count")
    performance_warning: bool = Field(False, description="Performance warning")