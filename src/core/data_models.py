"""
Core Data Models for Grant Research Automation
Comprehensive data models using Pydantic for validation and serialization.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import re


class FundingSourceType(str, Enum):
    """Types of funding sources"""
    GOVERNMENT_FEDERAL = "government_federal"
    GOVERNMENT_STATE = "government_state" 
    GOVERNMENT_LOCAL = "government_local"
    FOUNDATION_PRIVATE = "foundation_private"
    FOUNDATION_CORPORATE = "foundation_corporate"
    FOUNDATION_COMMUNITY = "foundation_community"
    CORPORATE_CSR = "corporate_csr"
    CORPORATE_SPONSORSHIP = "corporate_sponsorship"
    NONPROFIT_INTERMEDIARY = "nonprofit_intermediary"
    INTERNATIONAL = "international"
    OTHER = "other"


class OpportunityStatus(str, Enum):
    """Universal opportunity status"""
    DISCOVERY = "discovery"          # Just discovered
    ACTIVE = "active"               # Open for applications
    FORECASTED = "forecasted"       # Announced but not yet open
    POSTED = "posted"               # Government terminology
    CLOSING_SOON = "closing_soon"   # Less than 30 days to deadline
    CLOSED = "closed"               # Past deadline
    AWARDED = "awarded"             # Awards made
    CANCELLED = "cancelled"         # Cancelled/withdrawn
    ARCHIVED = "archived"           # Historical


class EligibilityType(str, Enum):
    """Universal eligibility categories"""
    NONPROFIT_501C3 = "nonprofit_501c3"
    NONPROFIT_OTHER = "nonprofit_other"
    GOVERNMENT_STATE = "government_state"
    GOVERNMENT_LOCAL = "government_local"
    GOVERNMENT_TRIBAL = "government_tribal"
    UNIVERSITY_PUBLIC = "university_public"
    UNIVERSITY_PRIVATE = "university_private"
    FOR_PROFIT_SMALL = "for_profit_small"
    FOR_PROFIT_LARGE = "for_profit_large"
    INDIVIDUAL = "individual"
    FISCAL_SPONSOR = "fiscal_sponsor"
    COLLABORATIVE = "collaborative"
    OTHER = "other"


class BaseOpportunity(BaseModel):
    """
    Universal base class for all funding opportunities.
    
    This provides common fields across government, foundation,
    corporate, and other funding sources.
    """
    # Core Identity
    id: str = Field(..., description="Unique opportunity identifier")
    title: str = Field(..., description="Opportunity title")
    description: str = Field("", description="Detailed description")
    source_type: FundingSourceType = Field(..., description="Type of funding source")
    
    # Funder Information
    funder_name: str = Field(..., description="Name of funding organization")
    funder_id: Optional[str] = Field(None, description="Unique funder identifier (EIN, etc.)")
    program_name: Optional[str] = Field(None, description="Specific program or initiative name")
    contact_info: Dict[str, str] = Field(default_factory=dict, description="Contact information")
    
    # Opportunity Status
    status: OpportunityStatus = Field(..., description="Current opportunity status")
    source_url: Optional[str] = Field(None, description="URL to opportunity details")
    application_url: Optional[str] = Field(None, description="URL to apply")
    
    # Financial Details
    funding_amount_min: Optional[float] = Field(None, description="Minimum funding amount")
    funding_amount_max: Optional[float] = Field(None, description="Maximum funding amount")
    total_available: Optional[float] = Field(None, description="Total available funding")
    expected_awards: Optional[int] = Field(None, description="Expected number of awards")
    matching_required: bool = Field(False, description="Matching funds required")
    matching_percentage: Optional[float] = Field(None, description="Required matching percentage")
    
    # Timeline
    posted_date: Optional[datetime] = Field(None, description="Date posted/announced")
    application_deadline: Optional[datetime] = Field(None, description="Application deadline")
    award_date: Optional[datetime] = Field(None, description="Expected award date")
    project_start_date: Optional[datetime] = Field(None, description="Project start date")
    project_end_date: Optional[datetime] = Field(None, description="Project end date")
    
    # Eligibility
    eligible_applicants: List[EligibilityType] = Field(default_factory=list, description="Eligible applicant types")
    geographic_restrictions: List[str] = Field(default_factory=list, description="Geographic limitations")
    sector_restrictions: List[str] = Field(default_factory=list, description="Sector/industry restrictions")
    organization_size_limits: Dict[str, Any] = Field(default_factory=dict, description="Size limitations")
    
    # Focus Areas
    focus_areas: List[str] = Field(default_factory=list, description="Primary focus areas")
    keywords: List[str] = Field(default_factory=list, description="Relevant keywords")
    subject_areas: List[str] = Field(default_factory=list, description="Subject matter areas")
    
    # Analysis & Scoring
    relevance_score: float = Field(0.0, description="Calculated relevance score (0-100)")
    competition_level: str = Field("unknown", description="Estimated competition level")
    success_probability: Optional[float] = Field(None, description="Estimated success probability")
    match_reasons: List[str] = Field(default_factory=list, description="Reasons for match")
    
    # Metadata
    discovered_at: datetime = Field(default_factory=datetime.now, description="Discovery timestamp")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    data_quality_score: float = Field(0.0, description="Data completeness/quality score")
    processing_notes: List[str] = Field(default_factory=list, description="Processing notes")
    
    def calculate_days_until_deadline(self) -> Optional[int]:
        """Calculate days until application deadline"""
        if not self.application_deadline:
            return None
        
        delta = self.application_deadline - datetime.now()
        return max(0, delta.days)
    
    def is_eligible_for(self, applicant_type: EligibilityType) -> bool:
        """Check if applicant type is eligible"""
        return applicant_type in self.eligible_applicants
    
    def add_match_reason(self, reason: str) -> None:
        """Add a reason for matching this opportunity"""
        if reason not in self.match_reasons:
            self.match_reasons.append(reason)
    
    def update_score(self, score: float, reason: Optional[str] = None) -> None:
        """Update relevance score with optional reason"""
        self.relevance_score = max(0.0, min(100.0, score))
        if reason:
            self.add_match_reason(reason)


class GovernmentOpportunity(BaseOpportunity):
    """
    Government funding opportunity (Federal, State, Local)
    Extends BaseOpportunity with government-specific fields.
    """
    # Government-specific fields
    agency_code: str = Field(..., description="Government agency code")
    sub_agency: Optional[str] = Field(None, description="Sub-agency or office")
    cfda_numbers: List[str] = Field(default_factory=list, description="CFDA program numbers")
    funding_instrument: str = Field("grant", description="Type of funding instrument")
    opportunity_category: Optional[str] = Field(None, description="Opportunity category")
    
    # Compliance
    compliance_requirements: List[str] = Field(default_factory=list, description="Compliance requirements")
    reporting_requirements: List[str] = Field(default_factory=list, description="Reporting requirements")
    
    # Source tracking
    grants_gov_id: Optional[str] = Field(None, description="Grants.gov opportunity ID")
    usaspending_data: Dict[str, Any] = Field(default_factory=dict, description="USASpending historical data")
    
    def __init__(self, **kwargs):
        # Set default source_type for government opportunities
        if 'source_type' not in kwargs:
            kwargs['source_type'] = FundingSourceType.GOVERNMENT_FEDERAL
        super().__init__(**kwargs)


class FoundationOpportunity(BaseOpportunity):
    """
    Foundation funding opportunity (Private, Corporate, Community)
    Extends BaseOpportunity with foundation-specific fields.
    """
    # Foundation-specific fields
    foundation_type: str = Field(..., description="Type of foundation")
    assets_range: Optional[str] = Field(None, description="Foundation asset range")
    giving_history: List[Dict[str, Any]] = Field(default_factory=list, description="Historical giving data")
    board_connections: List[str] = Field(default_factory=list, description="Board member connections")
    
    # Corporate foundation specific
    parent_company: Optional[str] = Field(None, description="Parent company if corporate foundation")
    industry_focus: List[str] = Field(default_factory=list, description="Industry focus areas")
    
    # Application process
    application_process: str = Field("standard", description="Application process type")
    requires_loi: bool = Field(False, description="Requires letter of inquiry")
    invitation_only: bool = Field(False, description="Invitation only application")
    
    def __init__(self, **kwargs):
        # Set appropriate default source_type
        if 'source_type' not in kwargs:
            if kwargs.get('foundation_type') == 'corporate':
                kwargs['source_type'] = FundingSourceType.FOUNDATION_CORPORATE
            elif kwargs.get('foundation_type') == 'community':
                kwargs['source_type'] = FundingSourceType.FOUNDATION_COMMUNITY
            else:
                kwargs['source_type'] = FundingSourceType.FOUNDATION_PRIVATE
        super().__init__(**kwargs)


class CorporateOpportunity(BaseOpportunity):
    """
    Corporate funding opportunity (CSR, Sponsorship, Partnerships)
    Extends BaseOpportunity with corporate-specific fields.
    """
    # Corporate-specific fields
    company_name: str = Field(..., description="Corporation name")
    industry: str = Field(..., description="Corporate industry")
    company_size: Optional[str] = Field(None, description="Company size category")
    
    # CSR Program details
    csr_focus_areas: List[str] = Field(default_factory=list, description="CSR focus areas")
    partnership_types: List[str] = Field(default_factory=list, description="Types of partnerships offered")
    employee_engagement: bool = Field(False, description="Includes employee engagement component")
    
    # Corporate giving pattern
    annual_giving: Optional[float] = Field(None, description="Annual corporate giving amount")
    giving_priorities: List[str] = Field(default_factory=list, description="Corporate giving priorities")
    
    def __init__(self, **kwargs):
        # Set appropriate default source_type
        if 'source_type' not in kwargs:
            partnership_types = kwargs.get('partnership_types', [])
            if 'sponsorship' in partnership_types:
                kwargs['source_type'] = FundingSourceType.CORPORATE_SPONSORSHIP
            else:
                kwargs['source_type'] = FundingSourceType.CORPORATE_CSR
        super().__init__(**kwargs)


class OpportunityCollection(BaseModel):
    """
    Collection of opportunities with metadata and analysis
    """
    collection_id: str = Field(..., description="Unique collection identifier")
    name: str = Field(..., description="Collection name")
    description: Optional[str] = Field(None, description="Collection description")
    
    # Opportunities by type
    government_opportunities: List[GovernmentOpportunity] = Field(default_factory=list)
    foundation_opportunities: List[FoundationOpportunity] = Field(default_factory=list)
    corporate_opportunities: List[CorporateOpportunity] = Field(default_factory=list)
    
    # Collection metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    total_count: int = Field(0, description="Total opportunities in collection")
    source_breakdown: Dict[str, int] = Field(default_factory=dict)
    
    # Search/filter criteria used
    search_criteria: Dict[str, Any] = Field(default_factory=dict)
    profile_used: Optional[str] = Field(None, description="Organization profile used for matching")
    
    def add_opportunity(self, opportunity: BaseOpportunity) -> None:
        """Add opportunity to appropriate collection"""
        if isinstance(opportunity, GovernmentOpportunity):
            self.government_opportunities.append(opportunity)
        elif isinstance(opportunity, FoundationOpportunity):
            self.foundation_opportunities.append(opportunity)
        elif isinstance(opportunity, CorporateOpportunity):
            self.corporate_opportunities.append(opportunity)
        
        self._update_metadata()
    
    def get_all_opportunities(self) -> List[BaseOpportunity]:
        """Get all opportunities regardless of type"""
        return (self.government_opportunities + 
                self.foundation_opportunities + 
                self.corporate_opportunities)
    
    def get_top_opportunities(self, limit: int = 10) -> List[BaseOpportunity]:
        """Get top opportunities by relevance score"""
        all_opps = self.get_all_opportunities()
        return sorted(all_opps, key=lambda x: x.relevance_score, reverse=True)[:limit]
    
    def _update_metadata(self) -> None:
        """Update collection metadata"""
        self.total_count = (len(self.government_opportunities) + 
                           len(self.foundation_opportunities) + 
                           len(self.corporate_opportunities))
        
        self.source_breakdown = {
            'government': len(self.government_opportunities),
            'foundation': len(self.foundation_opportunities),
            'corporate': len(self.corporate_opportunities)
        }
        
        self.last_updated = datetime.now()


class WorkflowStatus(str, Enum):
    """Enumeration of possible workflow states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ProcessorStatus(str, Enum):
    """Enumeration of processor execution states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class OrganizationType(str, Enum):
    """Types of organizations we analyze."""
    NONPROFIT = "nonprofit"
    FOUNDATION = "foundation"
    CHARITY = "charity"
    UNKNOWN = "unknown"


class ProcessorResult(BaseModel):
    """Standard result format for all processors."""
    success: bool
    processor_name: str
    execution_time: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def add_data(self, key: str, value: Any) -> None:
        """Add data to the result."""
        self.data[key] = value
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the result."""
        self.metadata[key] = value


class OrganizationProfile(BaseModel):
    """Comprehensive organization data model."""
    # Basic Information
    ein: str = Field(..., description="9-digit EIN")
    name: str = Field(..., description="Organization name")
    ntee_code: Optional[str] = Field(None, description="NTEE classification code")
    ntee_description: Optional[str] = Field(None, description="NTEE classification description")
    state: str = Field(..., description="State abbreviation")
    city: Optional[str] = Field(None, description="City")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    organization_type: OrganizationType = Field(default=OrganizationType.NONPROFIT)
    subsection_code: Optional[str] = Field(None, description="IRS subsection code (1=private foundation)")
    asset_code: Optional[str] = Field(None, description="IRS asset amount code")
    income_code: Optional[str] = Field(None, description="IRS income amount code")
    
    # Financial Data (Most Recent Year)
    revenue: Optional[float] = Field(None, description="Total revenue")
    assets: Optional[float] = Field(None, description="Total assets")
    expenses: Optional[float] = Field(None, description="Total expenses")
    net_assets: Optional[float] = Field(None, description="Net assets")
    program_expenses: Optional[float] = Field(None, description="Program service expenses")
    
    # Calculated Financial Ratios
    program_expense_ratio: Optional[float] = Field(None, description="Program expenses / Total expenses")
    fundraising_efficiency: Optional[float] = Field(None, description="Fundraising expenses / Total revenue")
    administrative_ratio: Optional[float] = Field(None, description="Admin expenses / Total expenses")
    revenue_growth_rate: Optional[float] = Field(None, description="Year-over-year revenue growth")
    
    # Historical Financial Data (Multi-year)
    financial_history: List[Dict[str, Any]] = Field(default_factory=list, description="Historical financial data")
    
    # Organizational Data
    mission_description: Optional[str] = Field(None, description="Mission statement")
    activity_description: Optional[str] = Field(None, description="Primary activities")
    website: Optional[str] = Field(None, description="Website URL")
    
    # Leadership and Governance
    board_members: List[str] = Field(default_factory=list, description="Board member names")
    key_personnel: List[Dict[str, Any]] = Field(default_factory=list, description="Key staff information")
    board_size: Optional[int] = Field(None, description="Number of board members")
    
    # Filing Information
    most_recent_filing_year: Optional[int] = Field(None, description="Most recent 990 filing year")
    filing_years: List[int] = Field(default_factory=list, description="All available filing years")
    filing_consistency_score: Optional[float] = Field(None, description="Consistency of filings score")
    has_990_filing: bool = Field(default=False, description="Has 990 filing available")
    has_schedule_i: bool = Field(default=False, description="Has Schedule I (grants) filing")
    
    # Grant-making Information (if applicable)
    total_grants_made: Optional[float] = Field(None, description="Total grants made (if grantmaker)")
    num_grants_made: Optional[int] = Field(None, description="Number of grants made")
    grant_recipients: List[Dict[str, Any]] = Field(default_factory=list, description="Grant recipient information")
    
    # Scoring and Analysis
    composite_score: Optional[float] = Field(None, description="Overall composite score")
    component_scores: Dict[str, Any] = Field(default_factory=dict, description="Individual component scores")
    scoring_components: Dict[str, float] = Field(default_factory=dict, description="Detailed scoring components")
    score_rank: Optional[int] = Field(None, description="Rank among analyzed organizations")
    score_percentile: Optional[float] = Field(None, description="Percentile ranking")
    
    # Individual Scoring Components
    filing_consistency_score: Optional[float] = Field(None, description="Filing consistency score")
    filing_recency_score: Optional[float] = Field(None, description="Filing recency score")
    financial_health_score: Optional[float] = Field(None, description="Financial health score")
    
    # Analysis Flags
    is_potential_funder: bool = Field(default=False, description="Identified as potential funder")
    has_similar_mission: bool = Field(default=False, description="Has similar mission to target")
    financial_health_status: Optional[str] = Field(None, description="Financial health assessment")
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    data_sources: List[str] = Field(default_factory=list, description="Sources of data")
    processing_notes: List[str] = Field(default_factory=list, description="Processing notes and warnings")
    
    @validator('ein')
    def validate_ein_format(cls, v):
        """Ensure EIN is properly formatted."""
        if not re.match(r'^\d{9}$', v):
            raise ValueError('EIN must be exactly 9 digits')
        return v
    
    @validator('program_expense_ratio', 'fundraising_efficiency', 'administrative_ratio')
    def validate_ratio_range(cls, v):
        """Ensure ratios are between 0 and 1."""
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Ratio must be between 0 and 1')
        return v
    
    @validator('state')
    def validate_state_code(cls, v):
        """Ensure state is a valid 2-letter code."""
        if not re.match(r'^[A-Z]{2}$', v):
            raise ValueError('State must be a 2-letter uppercase code')
        return v
    
    def calculate_financial_ratios(self) -> None:
        """Calculate financial ratios from available data."""
        if self.expenses and self.expenses > 0:
            if self.program_expenses:
                self.program_expense_ratio = self.program_expenses / self.expenses
        
        # Additional ratio calculations can be added here
    
    def add_processing_note(self, note: str) -> None:
        """Add a processing note."""
        self.processing_notes.append(f"{datetime.now().isoformat()}: {note}")
    
    def add_data_source(self, source: str) -> None:
        """Add a data source."""
        if source not in self.data_sources:
            self.data_sources.append(source)


class WorkflowConfig(BaseModel):
    """Configuration for a complete workflow run."""
    workflow_id: str = Field(default_factory=lambda: f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    name: Optional[str] = Field(None, description="Human-readable workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    
    # Target Configuration
    target_ein: Optional[str] = Field(None, description="Target organization EIN for similarity analysis")
    target_organization_name: Optional[str] = Field(None, description="Target organization name")
    
    # Filtering Criteria
    ntee_codes: List[str] = Field(default_factory=lambda: ["P81", "E31", "W70"], description="NTEE codes to include")
    state_filter: Optional[str] = Field("VA", description="State to filter by")
    states: List[str] = Field(default_factory=list, description="Multiple states to include")
    
    # Financial Filters
    min_revenue: Optional[int] = Field(100000, description="Minimum revenue threshold")
    max_revenue: Optional[int] = Field(None, description="Maximum revenue threshold")
    min_assets: Optional[int] = Field(None, description="Minimum assets threshold")
    max_assets: Optional[int] = Field(None, description="Maximum assets threshold")
    
    # Processing Options
    max_results: int = Field(100, description="Maximum number of results to process")
    scoring_profile: str = Field("default", description="Scoring profile to use")
    processors_to_run: List[str] = Field(default_factory=list, description="Specific processors to run (empty = all)")
    processors_to_skip: List[str] = Field(default_factory=list, description="Processors to skip")
    
    # Output Options
    generate_excel_dossier: bool = Field(True, description="Generate Excel dossier report")
    generate_pdf_report: bool = Field(False, description="Generate PDF summary report")
    generate_csv_export: bool = Field(True, description="Generate CSV export")
    
    # Analysis Options
    include_board_analysis: bool = Field(True, description="Analyze board members")
    include_financial_trends: bool = Field(True, description="Analyze multi-year financial trends")
    include_grant_analysis: bool = Field(True, description="Analyze grant-making patterns")
    similarity_analysis: bool = Field(True, description="Perform mission similarity analysis")
    
    # Intelligent Classification Options
    include_classified_organizations: bool = Field(False, description="Include organizations classified by intelligent classifier")
    classification_score_threshold: float = Field(0.5, description="Minimum classification score for inclusion")
    classification_categories: List[str] = Field(default_factory=lambda: ["health", "nutrition", "safety", "education"], 
                                               description="Categories to include from classification")
    
    # Performance Settings
    max_concurrent_downloads: int = Field(3, description="Maximum concurrent downloads")
    max_concurrent_processors: int = Field(2, description="Maximum concurrent processors")
    enable_caching: bool = Field(True, description="Enable caching of results")
    cache_expiry_hours: int = Field(24, description="Cache expiry time in hours")
    
    # Retry and Error Handling
    max_retries: int = Field(3, description="Maximum retry attempts for failed operations")
    retry_delay: float = Field(1.0, description="Delay between retries in seconds")
    continue_on_error: bool = Field(True, description="Continue processing on non-critical errors")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="User who created the workflow")
    
    @validator('workflow_id')
    def validate_workflow_id(cls, v):
        """Ensure workflow ID is valid."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Workflow ID must contain only letters, numbers, underscores, and hyphens')
        return v
    
    @validator('state_filter')
    def validate_state_filter(cls, v):
        """Validate state filter."""
        if v and not re.match(r'^[A-Z]{2}$', v):
            raise ValueError('State filter must be a 2-letter uppercase code')
        return v
    
    def get_all_states(self) -> List[str]:
        """Get all states to process (combination of state_filter and states)."""
        all_states = []
        if self.state_filter:
            all_states.append(self.state_filter)
        all_states.extend(self.states)
        return list(set(all_states))  # Remove duplicates


class WorkflowState(BaseModel):
    """Tracks the state of a workflow execution."""
    workflow_id: str
    config: WorkflowConfig
    status: WorkflowStatus = WorkflowStatus.PENDING
    
    # Execution tracking
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_processor: Optional[str] = None
    completed_processors: List[str] = Field(default_factory=list)
    failed_processors: List[str] = Field(default_factory=list)
    
    # Results tracking
    processor_results: Dict[str, ProcessorResult] = Field(default_factory=dict)
    organizations_found: int = 0
    organizations_processed: int = 0
    organizations_scored: int = 0
    
    # Error tracking
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Progress tracking
    progress_percentage: float = 0.0
    progress_message: str = "Initializing..."
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def mark_processor_started(self, processor_name: str) -> None:
        """Mark a processor as started."""
        self.current_processor = processor_name
        self.last_updated = datetime.now()
    
    def mark_processor_completed(self, processor_name: str, result: ProcessorResult) -> None:
        """Mark a processor as completed."""
        self.completed_processors.append(processor_name)
        self.processor_results[processor_name] = result
        if processor_name == self.current_processor:
            self.current_processor = None
        
        # Update organization counts from result data
        if result.success and result.data and isinstance(result.data, dict):
            if 'organizations' in result.data:
                orgs = result.data['organizations']
                if isinstance(orgs, list):
                    if processor_name == 'bmf_filter':
                        self.organizations_found = len(orgs)
                    elif processor_name == 'financial_scorer':
                        self.organizations_scored = len(orgs)
                    self.organizations_processed = len(orgs)
        
        self.last_updated = datetime.now()
    
    def mark_processor_failed(self, processor_name: str, result: ProcessorResult) -> None:
        """Mark a processor as failed."""
        self.failed_processors.append(processor_name)
        self.processor_results[processor_name] = result
        if processor_name == self.current_processor:
            self.current_processor = None
        self.last_updated = datetime.now()
    
    def update_progress(self, percentage: float, message: str = "") -> None:
        """Update progress information."""
        self.progress_percentage = max(0, min(100, percentage))
        if message:
            self.progress_message = message
        self.last_updated = datetime.now()
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(f"{datetime.now().isoformat()}: {error}")
        self.last_updated = datetime.now()
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(f"{datetime.now().isoformat()}: {warning}")
        self.last_updated = datetime.now()
    
    def get_execution_time(self) -> Optional[float]:
        """Get total execution time in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return None
    
    def get_processor_data(self, processor_name: str) -> Optional[Dict[str, Any]]:
        """Get data from a completed processor."""
        if processor_name in self.processor_results:
            result = self.processor_results[processor_name]
            if result.success and result.data:
                return result.data
        return None
    
    def get_organizations_from_processor(self, processor_name: str) -> List[Dict[str, Any]]:
        """Get organizations list from a specific processor."""
        data = self.get_processor_data(processor_name)
        if data and 'organizations' in data:
            organizations = data['organizations']
            if isinstance(organizations, list):
                return organizations
        return []
    
    def has_processor_succeeded(self, processor_name: str) -> bool:
        """Check if a processor has completed successfully."""
        return (processor_name in self.processor_results and 
                self.processor_results[processor_name].success)


class ProcessorConfig(BaseModel):
    """Configuration passed to individual processors."""
    workflow_id: str
    processor_name: str
    workflow_config: WorkflowConfig
    input_data: Dict[str, Any] = Field(default_factory=dict)
    processor_specific_config: Dict[str, Any] = Field(default_factory=dict)
    
    def get_input(self, key: str, default: Any = None) -> Any:
        """Get input data value."""
        return self.input_data.get(key, default)
    
    def set_input(self, key: str, value: Any) -> None:
        """Set input data value."""
        self.input_data[key] = value
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get processor-specific configuration value."""
        return self.processor_specific_config.get(key, default)