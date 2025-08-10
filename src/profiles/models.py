"""
Profile data models for organization profiles and opportunity tracking
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FundingType(str, Enum):
    """Types of funding opportunities"""
    GRANTS = "grants"
    GOVERNMENT = "government" 
    COMMERCIAL = "commercial"
    SPONSORSHIPS = "sponsorships"
    PARTNERSHIPS = "partnerships"


class OrganizationType(str, Enum):
    """Organization types for profile classification"""
    NONPROFIT = "nonprofit"
    FOR_PROFIT = "for_profit"
    GOVERNMENT = "government"
    ACADEMIC = "academic"
    HEALTHCARE = "healthcare"
    FOUNDATION = "foundation"


class PipelineStage(str, Enum):
    """Processing pipeline stages"""
    DISCOVERY = "discovery"
    PRE_SCORING = "pre_scoring"
    DEEP_ANALYSIS = "deep_analysis"
    RECOMMENDATIONS = "recommendations"


class ProfileStatus(str, Enum):
    """Profile status options"""
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"
    TEMPLATE = "template"


class GeographicScope(BaseModel):
    """Geographic targeting configuration"""
    states: Optional[List[str]] = Field(default=[], description="Target states (2-letter codes)")
    regions: Optional[List[str]] = Field(default=[], description="Geographic regions")
    nationwide: bool = Field(default=False, description="Nationwide scope")
    international: bool = Field(default=False, description="International scope")


class FundingPreferences(BaseModel):
    """Funding preferences and requirements"""
    min_amount: Optional[int] = Field(default=None, description="Minimum funding amount")
    max_amount: Optional[int] = Field(default=None, description="Maximum funding amount") 
    funding_types: List[FundingType] = Field(default=[FundingType.GRANTS], description="Preferred funding types")
    recurring: bool = Field(default=False, description="Seeks recurring funding")
    multi_year: bool = Field(default=False, description="Multi-year funding acceptable")


class OrganizationProfile(BaseModel):
    """Complete organization profile for opportunity discovery"""
    
    # Basic Information
    profile_id: str = Field(..., description="Unique profile identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Organization name")
    organization_type: OrganizationType = Field(..., description="Organization type")
    ein: Optional[str] = Field(default=None, pattern=r'^\d{2}-?\d{7}$', description="EIN (if applicable)")
    
    # Mission and Focus
    mission_statement: str = Field(..., min_length=10, max_length=1000, description="Organization mission")
    focus_areas: List[str] = Field(..., min_items=1, description="Primary focus areas/keywords")
    program_areas: List[str] = Field(default=[], description="Specific program areas")
    target_populations: List[str] = Field(default=[], description="Populations served")
    
    # Geographic and Scope
    geographic_scope: GeographicScope = Field(default_factory=GeographicScope)
    service_areas: List[str] = Field(default=[], description="Areas where services are provided")
    
    # Funding Information
    funding_preferences: FundingPreferences = Field(default_factory=FundingPreferences)
    current_funders: List[str] = Field(default=[], description="Current funding sources")
    past_grants: List[str] = Field(default=[], description="Previous grant awards")
    
    # Organizational Capacity
    annual_revenue: Optional[int] = Field(default=None, description="Annual revenue/budget")
    staff_size: Optional[int] = Field(default=None, description="Number of staff")
    volunteer_count: Optional[int] = Field(default=None, description="Number of volunteers")
    board_size: Optional[int] = Field(default=None, description="Board of directors size")
    
    # Strategic Information
    strategic_priorities: List[str] = Field(default=[], description="Current strategic priorities")
    growth_goals: List[str] = Field(default=[], description="Growth and expansion goals")
    partnership_interests: List[str] = Field(default=[], description="Partnership opportunities of interest")
    
    # Compliance and Requirements
    certifications: List[str] = Field(default=[], description="Relevant certifications")
    compliance_requirements: List[str] = Field(default=[], description="Compliance needs")
    reporting_capabilities: List[str] = Field(default=[], description="Reporting and evaluation capabilities")
    
    # Profile Management
    status: ProfileStatus = Field(default=ProfileStatus.ACTIVE, description="Profile status")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    created_by: Optional[str] = Field(default=None, description="Profile creator")
    tags: List[str] = Field(default=[], description="Profile tags for organization")
    notes: Optional[str] = Field(default=None, max_length=2000, description="Additional notes")
    
    # Discovery Tracking
    last_discovery_date: Optional[datetime] = Field(default=None, description="Date of most recent discovery run")
    discovery_count: int = Field(default=0, description="Total number of discovery sessions conducted")
    discovery_status: str = Field(default="never_run", description="Current discovery status (never_run, in_progress, completed, needs_update)")
    next_recommended_discovery: Optional[datetime] = Field(default=None, description="Suggested date for next discovery update")
    opportunities_count: int = Field(default=0, description="Total opportunities discovered")

    @validator('focus_areas', 'program_areas', 'target_populations')
    def validate_string_lists(cls, v):
        """Ensure string lists contain non-empty strings"""
        return [item.strip() for item in v if item and item.strip()]

    @validator('updated_at', always=True)
    def set_updated_at(cls, v):
        """Always update timestamp on save"""
        return datetime.now()

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DiscoverySession(BaseModel):
    """Individual discovery session record"""
    
    session_id: str = Field(..., description="Unique session identifier")
    profile_id: str = Field(..., description="Associated profile ID")
    started_at: datetime = Field(default_factory=datetime.now, description="Session start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Session completion timestamp")
    status: str = Field(default="in_progress", description="Session status (in_progress, completed, failed)")
    
    # Track execution details
    tracks_executed: List[str] = Field(default=[], description="Discovery tracks run (nonprofit, government, commercial, state)")
    opportunities_found: Dict[str, int] = Field(default_factory=dict, description="Opportunities found per track")
    total_opportunities: int = Field(default=0, description="Total opportunities discovered in session")
    
    # Session metadata
    execution_time_seconds: Optional[int] = Field(default=None, description="Total execution time")
    error_messages: List[str] = Field(default=[], description="Any errors encountered")
    notes: Optional[str] = Field(default=None, description="Session notes")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OpportunityLead(BaseModel):
    """Individual opportunity discovered for a profile"""
    
    # Basic Information
    lead_id: str = Field(..., description="Unique lead identifier")
    profile_id: str = Field(..., description="Associated profile ID")
    source: str = Field(..., description="Discovery source (ProPublica, Grants.gov, etc.)")
    opportunity_type: FundingType = Field(..., description="Type of opportunity")
    
    # Opportunity Details
    organization_name: str = Field(..., description="Funding organization name")
    program_name: Optional[str] = Field(default=None, description="Specific program/grant name")
    description: Optional[str] = Field(default=None, description="Opportunity description")
    funding_amount: Optional[int] = Field(default=None, description="Available funding amount")
    
    # Compatibility and Scoring
    pipeline_stage: PipelineStage = Field(default=PipelineStage.DISCOVERY, description="Current pipeline stage")
    compatibility_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Compatibility score")
    success_probability: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Success probability estimate")
    
    # Analysis Results
    match_factors: Dict[str, Any] = Field(default_factory=dict, description="Factors contributing to match")
    risk_factors: Dict[str, Any] = Field(default_factory=dict, description="Identified risk factors")
    recommendations: List[str] = Field(default=[], description="Strategic recommendations")
    
    # Relationship Intelligence
    board_connections: List[Dict[str, str]] = Field(default=[], description="Board member connections")
    network_insights: Dict[str, Any] = Field(default_factory=dict, description="Network analysis results")
    approach_strategy: Optional[str] = Field(default=None, description="Recommended approach strategy")
    
    # Processing Metadata
    discovered_at: datetime = Field(default_factory=datetime.now, description="Discovery timestamp")
    last_analyzed: Optional[datetime] = Field(default=None, description="Last analysis timestamp")
    status: str = Field(default="active", description="Lead status")
    assigned_to: Optional[str] = Field(default=None, description="Assigned researcher")
    
    # External Data
    external_data: Dict[str, Any] = Field(default_factory=dict, description="Additional data from sources")

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProfileSearchParams(BaseModel):
    """Parameters for profile-driven opportunity search"""
    
    profile_id: str = Field(..., description="Target profile ID")
    funding_types: List[FundingType] = Field(default=[FundingType.GRANTS], description="Types to search")
    max_results_per_type: int = Field(default=100, ge=1, le=1000, description="Max results per funding type")
    min_compatibility_threshold: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum compatibility score")
    
    # Geographic filters
    geographic_expansion: bool = Field(default=False, description="Search beyond profile geography")
    
    # Stage-specific parameters  
    discovery_filters: Dict[str, Any] = Field(default_factory=dict, description="Discovery stage filters")
    pre_scoring_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Pre-scoring threshold")
    deep_analysis_limit: int = Field(default=20, ge=1, le=100, description="Deep analysis candidate limit")
    
    # Resource allocation
    max_processing_time: Optional[int] = Field(default=None, description="Max processing time in minutes")
    priority_level: str = Field(default="standard", description="Processing priority level")

    class Config:
        """Pydantic configuration"""
        schema_extra = {
            "example": {
                "profile_id": "health_nonprofit_001",
                "funding_types": ["grants", "government"],
                "max_results_per_type": 100,
                "min_compatibility_threshold": 0.4,
                "geographic_expansion": True,
                "pre_scoring_threshold": 0.6,
                "deep_analysis_limit": 15,
                "priority_level": "high"
            }
        }