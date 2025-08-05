"""
Core Data Models for Grant Research Automation
Comprehensive data models using Pydantic for validation and serialization.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import re


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
    component_scores: Dict[str, float] = Field(default_factory=dict, description="Individual component scores")
    score_rank: Optional[int] = Field(None, description="Rank among analyzed organizations")
    score_percentile: Optional[float] = Field(None, description="Percentile ranking")
    
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