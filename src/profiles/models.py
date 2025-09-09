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


class GrantsGovCategory(str, Enum):
    """Grants.gov funding categories for opportunity matching"""
    DISCRETIONARY = "discretionary"
    MANDATORY = "mandatory"  
    EARMARK = "earmark"
    CONTINUATION = "continuation"
    OTHER = "other"


class PipelineStage(str, Enum):
    """Processing pipeline stages"""
    DISCOVERY = "discovery"
    PRE_SCORING = "pre_scoring"
    DEEP_ANALYSIS = "deep_analysis"
    RECOMMENDATIONS = "recommendations"


class FunnelStage(str, Enum):
    """Grant opportunity funnel stages"""
    PROSPECTS = "prospects"                    # Initial ProPublica/API broad filtering
    QUALIFIED_PROSPECTS = "qualified_prospects" # 990 XML/eligibility detailed analysis  
    CANDIDATES = "candidates"                  # Mission/eligibility matched
    TARGETS = "targets"                        # High-potential for deep research
    OPPORTUNITIES = "opportunities"            # Decision-ready final stage


class ProfileStatus(str, Enum):
    """Profile status options"""
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"
    TEMPLATE = "template"


class FormType(str, Enum):
    """IRS form type classification"""
    FORM_990 = "990"
    FORM_990_PF = "990-PF"
    FORM_990_EZ = "990-EZ"
    FORM_990_N = "990-N"
    UNKNOWN = "unknown"


class FoundationType(str, Enum):
    """Foundation type classification"""
    PRIVATE_NON_OPERATING = "private_non_operating"      # Foundation Code 03 - Primary target
    PRIVATE_OPERATING = "private_operating"              # Foundation Code 04
    PUBLIC_CHARITY = "public_charity"                    # Most nonprofits
    SUPPORTING_ORGANIZATION = "supporting_organization"   # Foundation Code 12
    DONOR_ADVISED_FUND = "donor_advised_fund"           # Foundation Code 15
    UNKNOWN = "unknown"


class ApplicationAcceptanceStatus(str, Enum):
    """Application acceptance status from 990-PF Part XV"""
    ACCEPTS_APPLICATIONS = "accepts_applications"
    NO_APPLICATIONS = "no_applications"
    INVITATION_ONLY = "invitation_only"
    UNKNOWN = "unknown"


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
    
    # Grants.gov Classifications
    grants_gov_categories: List[GrantsGovCategory] = Field(default=[], description="Preferred Grants.gov funding categories")


class ScheduleIGrantee(BaseModel):
    """Schedule I grantee information from 990 filings"""
    recipient_name: str = Field(..., description="Organization name of grant recipient")
    recipient_ein: Optional[str] = Field(default=None, description="EIN of recipient if available")
    grant_amount: float = Field(..., description="Grant amount provided")
    grant_year: int = Field(..., description="Tax year of the grant")
    grant_purpose: Optional[str] = Field(default=None, description="Purpose or description of grant")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FoundationBoardMember(BaseModel):
    """990-PF Part VIII - Officers, Directors, Trustees information"""
    name: str = Field(..., description="Board member full name")
    title: str = Field(..., description="Position/title")
    address: Optional[str] = Field(default=None, description="Full address if available")
    average_hours_per_week: Optional[float] = Field(default=None, description="Hours per week devoted to position")
    compensation: Optional[float] = Field(default=None, description="Compensation amount")
    is_officer: bool = Field(default=False, description="Whether this person is an officer")
    is_director: bool = Field(default=False, description="Whether this person is a director/trustee")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FoundationGrantRecord(BaseModel):
    """990-PF Part XV - Enhanced grant record with full details"""
    recipient_name: str = Field(..., description="Grantee organization name")
    recipient_ein: Optional[str] = Field(default=None, description="Recipient EIN if available")
    recipient_address: Optional[str] = Field(default=None, description="Full recipient address")
    grant_amount: float = Field(..., description="Grant amount")
    grant_year: int = Field(..., description="Tax year of grant")
    grant_purpose: Optional[str] = Field(default=None, description="Detailed purpose or project description")
    support_type: Optional[str] = Field(default=None, description="General support or project support")
    relationship_to_substantial_contributor: Optional[str] = Field(default=None, description="Any relationship notes")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FoundationApplicationProcess(BaseModel):
    """990-PF Part XV - Application process information"""
    accepts_applications: ApplicationAcceptanceStatus = Field(default=ApplicationAcceptanceStatus.UNKNOWN, description="Application acceptance status")
    application_deadlines: Optional[str] = Field(default=None, description="Application deadline information")
    application_process_description: Optional[str] = Field(default=None, description="How to apply - process description")
    contact_information: Optional[str] = Field(default=None, description="Contact person or information")
    application_restrictions: Optional[str] = Field(default=None, description="Any restrictions on applications")
    geographic_limitations: Optional[str] = Field(default=None, description="Geographic giving limitations")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FoundationFinancialData(BaseModel):
    """990-PF Part I - Financial summary and investment information"""
    investment_income: Optional[float] = Field(default=None, description="Total investment income")
    capital_gains: Optional[float] = Field(default=None, description="Net capital gains")
    total_revenue: Optional[float] = Field(default=None, description="Total revenue")
    total_assets_beginning: Optional[float] = Field(default=None, description="Total assets beginning of year")
    total_assets_end: Optional[float] = Field(default=None, description="Total assets end of year")
    grants_paid: Optional[float] = Field(default=None, description="Total grants and contributions paid")
    qualifying_distributions: Optional[float] = Field(default=None, description="Qualifying distributions")
    minimum_investment_return: Optional[float] = Field(default=None, description="Minimum investment return")
    distributable_amount: Optional[float] = Field(default=None, description="Distributable amount for year")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FoundationProgramAreas(BaseModel):
    """990-PF Part XVI - Program areas and funding priorities"""
    program_area_codes: Optional[List[str]] = Field(default=[], description="NTEE or other program area codes")
    program_descriptions: Optional[List[str]] = Field(default=[], description="Detailed program area descriptions")
    funding_priorities: Optional[List[str]] = Field(default=[], description="Stated funding priorities")
    population_served: Optional[List[str]] = Field(default=[], description="Target populations served")
    geographic_focus: Optional[List[str]] = Field(default=[], description="Geographic areas of focus")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProfileMetrics(BaseModel):
    """Comprehensive metrics tracking for profile-based processing"""
    
    # Basic Information
    profile_id: str = Field(..., description="Associated profile ID")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last metrics update")
    
    # Opportunity Funnel Metrics
    total_opportunities_discovered: int = Field(default=0, description="Total opportunities discovered")
    funnel_stage_counts: Dict[str, int] = Field(default_factory=lambda: {
        "prospects": 0,
        "qualified_prospects": 0, 
        "candidates": 0,
        "targets": 0,
        "opportunities": 0
    }, description="Count of opportunities at each funnel stage")
    
    # API Usage Tracking
    api_calls_made: Dict[str, int] = Field(default_factory=lambda: {
        "propublica_api": 0,
        "grants_gov_api": 0,
        "foundation_directory_api": 0,
        "va_state_api": 0,
        "usaspending_api": 0,
        "other_apis": 0
    }, description="API calls made by source")
    
    # AI Processing Metrics
    ai_lite_calls: int = Field(default=0, description="AI Lite scoring calls made")
    ai_heavy_calls: int = Field(default=0, description="AI Heavy research calls made")
    total_ai_cost_usd: float = Field(default=0.0, description="Total AI processing costs")
    
    # Processing Efficiency
    total_processing_time_minutes: float = Field(default=0.0, description="Total processing time")
    successful_processors: int = Field(default=0, description="Number of successful processor executions")
    failed_processors: int = Field(default=0, description="Number of failed processor executions")
    cache_hits: int = Field(default=0, description="Number of cache hits")
    cache_misses: int = Field(default=0, description="Number of cache misses")
    
    # FTE Time Savings Calculation
    estimated_manual_hours_saved: float = Field(default=0.0, description="Estimated manual research hours saved")
    automation_efficiency_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall automation efficiency")
    
    # Quality Metrics
    average_match_score: Optional[float] = Field(default=None, description="Average opportunity match score")
    success_rate_by_stage: Dict[str, float] = Field(default_factory=dict, description="Success rates for stage transitions")
    user_engagement_score: Optional[float] = Field(default=None, description="User interaction/engagement score")
    
    # Session Tracking
    total_discovery_sessions: int = Field(default=0, description="Number of discovery sessions run")
    last_discovery_session: Optional[datetime] = Field(default=None, description="Last discovery session timestamp")
    avg_session_duration_minutes: float = Field(default=0.0, description="Average session duration")
    
    # Cost Analysis
    cost_per_qualified_opportunity: Optional[float] = Field(default=None, description="Cost per qualified opportunity")
    roi_estimate: Optional[float] = Field(default=None, description="Estimated ROI based on time savings")
    
    # Export and Reporting
    reports_generated: int = Field(default=0, description="Number of reports generated for this profile")
    last_export_date: Optional[datetime] = Field(default=None, description="Last data export timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def calculate_fte_hours_saved(self) -> float:
        """Calculate estimated FTE hours saved based on automated tasks"""
        hours_saved = 0.0
        
        # Organization discovery: 2.5 hours per org (average)
        orgs_processed = sum(self.funnel_stage_counts.values())
        hours_saved += orgs_processed * 2.5
        
        # Financial analysis: 1.5 hours per detailed analysis
        deep_analyses = self.funnel_stage_counts.get("candidates", 0) + self.funnel_stage_counts.get("targets", 0)
        hours_saved += deep_analyses * 1.5
        
        # Grant opportunity research: 4 hours per final opportunity
        final_opportunities = self.funnel_stage_counts.get("opportunities", 0)
        hours_saved += final_opportunities * 4.0
        
        # Board network analysis: 5 hours per network analysis session
        if self.total_discovery_sessions > 0:
            hours_saved += self.total_discovery_sessions * 5.0
        
        self.estimated_manual_hours_saved = hours_saved
        return hours_saved
    
    def update_funnel_metrics(self, stage: str, increment: int = 1) -> None:
        """Update funnel stage counts"""
        if stage in self.funnel_stage_counts:
            self.funnel_stage_counts[stage] += increment
            self.last_updated = datetime.now()
    
    def add_api_call(self, api_source: str) -> None:
        """Track an API call"""
        if api_source in self.api_calls_made:
            self.api_calls_made[api_source] += 1
        else:
            self.api_calls_made["other_apis"] += 1
        self.last_updated = datetime.now()
    
    def add_processing_time(self, minutes: float) -> None:
        """Add to total processing time"""
        self.total_processing_time_minutes += minutes
        self.last_updated = datetime.now()
    
    def calculate_cost_efficiency(self) -> float:
        """Calculate cost per qualified opportunity"""
        qualified_opps = (
            self.funnel_stage_counts.get("candidates", 0) + 
            self.funnel_stage_counts.get("targets", 0) + 
            self.funnel_stage_counts.get("opportunities", 0)
        )
        
        if qualified_opps > 0 and self.total_ai_cost_usd > 0:
            self.cost_per_qualified_opportunity = self.total_ai_cost_usd / qualified_opps
            return self.cost_per_qualified_opportunity
        return 0.0


class OrganizationProfile(BaseModel):
    """Complete organization profile for opportunity discovery"""
    
    # Basic Information
    profile_id: str = Field(..., description="Unique profile identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Organization name")
    organization_type: OrganizationType = Field(..., description="Organization type")
    ein: Optional[str] = Field(default=None, pattern=r'^\d{2}-?\d{7}$', description="EIN (if applicable)")
    
    # Mission and Focus
    mission_statement: Optional[str] = Field(default=None, max_length=1000, description="Organization mission")
    keywords: Optional[str] = Field(default=None, max_length=500, description="Key terms and phrases describing the organization's work")
    focus_areas: List[str] = Field(..., min_items=1, description="Primary focus areas/keywords")
    program_areas: List[str] = Field(default=[], description="Specific program areas")
    target_populations: List[str] = Field(default=[], description="Populations served")
    ntee_codes: List[str] = Field(default=[], description="NTEE (National Taxonomy of Exempt Entities) classification codes")
    ntee_description: Optional[str] = Field(default=None, max_length=500, description="Human-readable description of NTEE classifications")
    government_criteria: List[str] = Field(default=[], description="Government funding criteria preferences (agencies, funding types, etc.)")
    
    # Geographic and Scope
    geographic_scope: GeographicScope = Field(default_factory=GeographicScope)
    service_areas: List[str] = Field(default=[], description="Areas where services are provided")
    
    # Funding Information
    funding_preferences: FundingPreferences = Field(default_factory=FundingPreferences)
    current_funders: List[str] = Field(default=[], description="Current funding sources")
    past_grants: List[str] = Field(default=[], description="Previous grant awards")
    schedule_i_grantees: List[ScheduleIGrantee] = Field(default=[], description="Organizations this profile has granted to (from Schedule I)")
    schedule_i_status: Optional[str] = Field(default=None, description="Status of Schedule I data: 'found', 'no_grantees', 'no_xml', 'not_checked'")
    
    # 990-PF Private Foundation Information
    form_type: FormType = Field(default=FormType.UNKNOWN, description="IRS form type (990, 990-PF, etc.)")
    foundation_type: FoundationType = Field(default=FoundationType.UNKNOWN, description="Foundation classification")
    foundation_code: Optional[str] = Field(default=None, description="IRS Foundation Code (03 for private non-operating)")
    
    # 990-PF Part XV - Grant Making and Applications
    foundation_grants: List[FoundationGrantRecord] = Field(default=[], description="Grants made by this foundation (990-PF Part XV)")
    application_process: Optional[FoundationApplicationProcess] = Field(default=None, description="Application process information")
    accepts_unsolicited_applications: bool = Field(default=False, description="Whether foundation accepts unsolicited applications")
    
    # 990-PF Part VIII - Board and Decision Makers  
    foundation_board_members: List[FoundationBoardMember] = Field(default=[], description="Board members and officers (990-PF Part VIII)")
    
    # 990-PF Part I - Financial Information
    foundation_financial_data: Optional[FoundationFinancialData] = Field(default=None, description="Foundation financial summary")
    
    # 990-PF Part XVI - Program Areas
    foundation_program_areas: Optional[FoundationProgramAreas] = Field(default=None, description="Foundation program areas and priorities")
    
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
    
    # Processing State Tracking
    associated_opportunities: List[str] = Field(default=[], description="List of opportunity IDs associated with this profile")
    processing_history: Dict[str, Any] = Field(default_factory=dict, description="History of processing operations and their status")
    ai_analysis_count: int = Field(default=0, description="Number of AI analyses performed for this profile")
    last_ai_analysis_date: Optional[datetime] = Field(default=None, description="Date of most recent AI analysis")
    cache_usage_stats: Dict[str, int] = Field(default_factory=dict, description="Statistics on cache usage for this profile")
    cost_tracking: Dict[str, Any] = Field(default_factory=dict, description="Cost tracking for expensive operations")
    
    # Comprehensive Metrics Tracking
    metrics: Optional[ProfileMetrics] = Field(default=None, description="Comprehensive metrics tracking for this profile")

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


# ============================================================================
# UNIFIED OPPORTUNITY ARCHITECTURE MODELS
# ============================================================================

class StageTransition(BaseModel):
    """Individual stage transition record"""
    stage: str = Field(..., description="Stage name (discovery, pre_scoring, etc.)")
    entered_at: Optional[str] = Field(default=None, description="ISO timestamp when stage entered")
    exited_at: Optional[str] = Field(default=None, description="ISO timestamp when stage exited")
    duration_hours: Optional[float] = Field(default=None, description="Time spent in this stage")


class ScoringResult(BaseModel):
    """Unified scoring result"""
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall compatibility score")
    auto_promotion_eligible: bool = Field(default=False, description="Eligible for automatic promotion")
    promotion_recommended: bool = Field(default=False, description="Manual promotion recommended")
    dimension_scores: Dict[str, float] = Field(default_factory=dict, description="Scoring breakdown by dimension")
    confidence_level: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence in scoring")
    scored_at: Optional[str] = Field(default=None, description="ISO timestamp when scored")
    scorer_version: str = Field(default="1.0.0", description="Scoring algorithm version")


class StageAnalysis(BaseModel):
    """Analysis data for a specific stage"""
    match_factors: Dict[str, Any] = Field(default_factory=dict, description="Factors contributing to match")
    risk_factors: Dict[str, Any] = Field(default_factory=dict, description="Identified risk factors")
    recommendations: List[str] = Field(default=[], description="Stage-specific recommendations")
    network_insights: Dict[str, Any] = Field(default_factory=dict, description="Network analysis results")
    analyzed_at: Optional[str] = Field(default=None, description="ISO timestamp when analyzed")
    
    # Stage-specific fields
    source: Optional[str] = Field(default=None, description="Discovery source (for discovery stage)")
    opportunity_type: Optional[str] = Field(default=None, description="Opportunity type (for discovery stage)")
    enhanced_data: Optional[Dict[str, Any]] = Field(default=None, description="Enhanced data (for pre_scoring+ stages)")


class UserAssessment(BaseModel):
    """User assessment and rating of opportunity"""
    user_rating: Optional[int] = Field(default=None, ge=1, le=5, description="User rating (1-5 stars)")
    priority_level: Optional[str] = Field(default=None, description="Priority level (high, medium, low)")
    assessment_notes: Optional[str] = Field(default=None, description="User notes and assessment")
    tags: List[str] = Field(default=[], description="User-assigned tags")
    last_assessed_at: Optional[str] = Field(default=None, description="ISO timestamp of last assessment")


class PromotionEvent(BaseModel):
    """Individual promotion/demotion event"""
    from_stage: str = Field(..., description="Source stage")
    to_stage: str = Field(..., description="Target stage")
    decision_type: str = Field(..., description="Type of promotion decision")
    score_at_promotion: float = Field(default=0.0, description="Score when promotion occurred")
    reason: str = Field(default="", description="Reason for promotion/demotion")
    promoted_at: Optional[str] = Field(default=None, description="ISO timestamp of promotion")
    promoted_by: str = Field(default="system", description="Who/what made the promotion")


class UnifiedOpportunity(BaseModel):
    """Unified opportunity record - single source of truth"""
    
    # Core Identity
    opportunity_id: str = Field(..., description="Unique opportunity identifier (opp_*)")
    profile_id: str = Field(..., description="Associated profile ID")
    organization_name: str = Field(..., description="Target organization name")
    ein: Optional[str] = Field(default=None, description="EIN if available")
    
    # Pipeline Status - Single Source of Truth
    current_stage: str = Field(default="prospects", description="Current pipeline stage")
    stage_history: List[StageTransition] = Field(default=[], description="Complete stage history")
    
    # Scoring - Computed Once, Referenced Forever
    scoring: Optional[ScoringResult] = Field(default=None, description="Latest scoring results")
    
    # Stage-Specific Analysis - Accumulated Knowledge
    analysis: Dict[str, StageAnalysis] = Field(default_factory=dict, description="Analysis by stage")
    
    # User Assessments - Persistent Across Sessions
    user_assessment: Optional[UserAssessment] = Field(default=None, description="User ratings and notes")
    
    # Promotion History - Complete Audit Trail
    promotion_history: List[PromotionEvent] = Field(default=[], description="Complete promotion history")
    
    # Metadata
    source: Optional[str] = Field(default=None, description="Original discovery source")
    opportunity_type: str = Field(default="grants", description="Type of opportunity")
    discovered_at: Optional[str] = Field(default=None, description="ISO timestamp of discovery")
    last_updated: Optional[str] = Field(default=None, description="ISO timestamp of last update")
    status: str = Field(default="active", description="Opportunity status")
    
    # Legacy Compatibility Fields
    legacy_lead_id: Optional[str] = Field(default=None, description="Original lead_id from migration")
    legacy_pipeline_stage: Optional[str] = Field(default=None, description="Original pipeline stage")
    description: Optional[str] = Field(default=None, description="Opportunity description")
    funding_amount: Optional[int] = Field(default=None, description="Funding amount if known")
    program_name: Optional[str] = Field(default=None, description="Program name if applicable")


class ProfileAnalytics(BaseModel):
    """Real-time analytics computed from opportunities"""
    
    # Basic Counts
    opportunity_count: int = Field(default=0, description="Total opportunities")
    stages_distribution: Dict[str, int] = Field(default_factory=dict, description="Count by stage")
    
    # Scoring Statistics
    scoring_stats: Dict[str, Any] = Field(default_factory=dict, description="Scoring analytics")
    
    # Discovery Statistics
    discovery_stats: Dict[str, Any] = Field(default_factory=dict, description="Discovery session analytics")
    
    # Promotion Statistics
    promotion_stats: Dict[str, Any] = Field(default_factory=dict, description="Promotion analytics")


class RecentActivity(BaseModel):
    """Recent activity item"""
    type: str = Field(..., description="Activity type")
    date: Optional[str] = Field(default=None, description="ISO timestamp")
    results: Optional[int] = Field(default=None, description="Results count for discovery sessions")
    source: Optional[str] = Field(default=None, description="Source for discovery sessions")
    opportunity: Optional[str] = Field(default=None, description="Opportunity name for promotions")
    from_stage: Optional[str] = Field(default=None, description="From stage for promotions")
    to_stage: Optional[str] = Field(default=None, description="To stage for promotions")


class UnifiedProfile(BaseModel):
    """Unified profile with embedded analytics"""
    
    # Core Profile Information
    profile_id: str = Field(..., description="Unique profile identifier")
    organization_name: str = Field(..., description="Organization name")
    focus_areas: List[str] = Field(default=[], description="Focus areas")
    geographic_scope: Optional[Any] = Field(default=None, description="Geographic scope")
    ntee_codes: List[str] = Field(default=[], description="NTEE codes")
    created_at: Optional[str] = Field(default=None, description="ISO timestamp of creation")
    updated_at: Optional[str] = Field(default=None, description="ISO timestamp of last update")
    
    # Embedded Analytics - Computed from Opportunities
    analytics: ProfileAnalytics = Field(default_factory=ProfileAnalytics, description="Real-time analytics")
    
    # Recent Activity Summary
    recent_activity: List[RecentActivity] = Field(default=[], description="Recent activity summary")
    
    # Legacy compatibility
    status: str = Field(default="active", description="Profile status")
    tags: List[str] = Field(default=[], description="Profile tags")
    notes: Optional[str] = Field(default=None, description="Profile notes")