# 12-Factor Data Models
*Comprehensive schema specification for 12-factor agent systems*

## Data Architecture Overview

This specification defines comprehensive data models for 12-factor agent systems, including entity schemas, BAML type definitions, database structures, and event models. All schemas support horizontal scaling, stateless processing, and environment-agnostic deployment.

## Core Principles

### 12-Factor Alignment
- **Factor IV (Backing Services)**: Database-agnostic schema design
- **Factor VI (Processes)**: Stateless data processing with immutable events
- **Factor III (Config)**: Environment-driven connection strings
- **Factor XI (Logs)**: Event sourcing for audit trails
- **Factor IX (Disposability)**: Resumable operations through event reconstruction

### Schema Standards
- **Type Safety**: Comprehensive type definitions with validation
- **Immutability**: Event-sourced models with append-only patterns
- **Versioning**: Schema evolution with backward compatibility
- **Validation**: Pydantic models with automatic validation
- **Serialization**: JSON-first with BAML type safety

## BAML Type System

### Core Entity Types

```baml
// baml/schemas/core.baml

// Base entity interface
interface Entity {
    id string
    created_at string
    updated_at string
    version int
    metadata map<string, string>?
}

// Organization entities
class Nonprofit {
    ein string @description("Employer Identification Number")
    name string @description("Official organization name")
    city string?
    state string
    zip_code string?
    ntee_code string @description("National Taxonomy of Exempt Entities")
    classification string @description("Tax classification")
    revenue int? @description("Annual revenue in dollars")
    assets int? @description("Total assets in dollars")
    employees int? @description("Number of employees")
    founded_year int?
    website string?
    mission_statement string?
    board_members BoardMember[]?
    programs Program[]?
    grants_received Grant[]?
    financial_data FinancialData[]?
}

class Foundation {
    ein string
    name string
    city string?
    state string
    foundation_type string @description("Private, Corporate, Community, etc.")
    assets int
    annual_giving int @description("Total annual grant distributions")
    focus_areas string[]
    geographic_focus string[]
    grant_size_range GrantRange?
    application_deadlines string[]?
    grants_awarded Grant[]?
    investment_data InvestmentData?
}

class Government {
    agency_name string
    agency_code string?
    department string
    opportunity_id string
    opportunity_title string
    funding_amount int
    application_deadline string?
    eligibility_criteria string[]
    geographic_restrictions string[]?
    program_areas string[]
    contact_info ContactInfo?
}

// Supporting types
class BoardMember {
    name string
    title string
    tenure_years int?
    other_affiliations string[]?
    compensation int?
}

class Program {
    name string
    description string
    budget int?
    participants_served int?
    outcomes string[]?
}

class Grant {
    id string
    grantor_name string
    grantor_ein string?
    amount int
    year int
    purpose string?
    duration_months int?
    reporting_requirements string[]?
}

class GrantRange {
    min_amount int
    max_amount int
    typical_amount int?
}

class FinancialData {
    year int
    revenue int
    expenses int
    net_assets int
    program_expense_ratio float? @description("Percentage spent on programs")
    administrative_expense_ratio float?
    fundraising_expense_ratio float?
    revenue_sources RevenueSource[]?
    expense_categories ExpenseCategory[]?
}

class RevenueSource {
    category string @description("Government grants, individual donations, etc.")
    amount int
    percentage float
}

class ExpenseCategory {
    category string @description("Program services, administration, fundraising")
    amount int
    percentage float
}

class ContactInfo {
    name string?
    title string?
    email string?
    phone string?
    address Address?
}

class Address {
    street string
    city string
    state string
    zip_code string
    country string @default("USA")
}
```

### Agent Execution Models

```baml
// baml/schemas/agents.baml

enum AgentStatus {
    IDLE
    BUSY
    DEGRADED
    UNHEALTHY
    MAINTENANCE
}

enum TaskPriority {
    LOW
    NORMAL
    HIGH
    CRITICAL
}

enum TaskStatus {
    QUEUED
    RUNNING
    COMPLETED
    FAILED
    CANCELLED
    TIMEOUT
}

class AgentConfig {
    id string @description("Unique agent identifier")
    name string @description("Human-readable name")
    capabilities string[] @description("List of supported actions")
    endpoint string @description("HTTP endpoint for agent")
    version string @regex("^\d+\.\d+\.\d+$") @description("Semantic version")
    health_check_url string
    max_concurrent_tasks int @default(10)
    timeout_seconds int @default(300)
    retry_attempts int @default(3)
    retry_delay_seconds int @default(30)
    metadata map<string, string>?
}

class AgentRequest {
    agent_id string
    action string @description("Action to execute")
    input map<string, string> @description("Action input parameters")
    timeout_seconds int? @description("Override default timeout")
    priority TaskPriority @default(NORMAL)
    correlation_id string? @description("Request tracing ID")
    user_id string? @description("Requesting user")
    context map<string, string>? @description("Additional context")
}

class AgentResponse {
    execution_id string
    agent_id string
    action string
    status TaskStatus
    started_at string @description("ISO 8601 timestamp")
    completed_at string? @description("ISO 8601 timestamp")
    duration_seconds float?
    result map<string, string>? @description("Execution results")
    error ErrorDetails? @description("Error information if failed")
    cost_dollars float? @description("Execution cost")
    tokens_used int? @description("AI tokens consumed")
    cache_hit bool @default(false)
}

class ErrorDetails {
    code string @description("Error code")
    message string @description("Human-readable error message")
    details map<string, string>? @description("Additional error context")
    stack_trace string? @description("Technical stack trace")
    retry_after_seconds int? @description("Suggested retry delay")
}
```

### Workflow Orchestration Models

```baml
// baml/schemas/workflows.baml

enum WorkflowStatus {
    INITIATED
    RUNNING
    PAUSED
    COMPLETED
    FAILED
    CANCELLED
    TIMEOUT
}

enum StepStatus {
    PENDING
    RUNNING
    COMPLETED
    FAILED
    SKIPPED
    COMPENSATED
}

class WorkflowDefinition {
    id string
    name string @description("Human-readable workflow name")
    description string?
    version string @regex("^\d+\.\d+\.\d+$")
    steps WorkflowStep[]
    input_schema map<string, string> @description("Required input parameters")
    output_schema map<string, string> @description("Expected output format")
    timeout_minutes int @default(60)
    retry_policy RetryPolicy?
    compensation_steps CompensationStep[]? @description("Rollback steps")
}

class WorkflowStep {
    step_id string
    name string
    agent_id string
    action string
    input_mapping map<string, string> @description("Map workflow input to agent input")
    output_mapping map<string, string> @description("Map agent output to workflow context")
    depends_on string[]? @description("Previous step dependencies")
    parallel_group string? @description("Steps that can run in parallel")
    timeout_seconds int?
    retry_attempts int @default(1)
    optional bool @default(false) @description("Workflow continues if this step fails")
    condition string? @description("Condition for step execution")
}

class CompensationStep {
    step_id string
    name string
    agent_id string
    action string
    input_mapping map<string, string>
    triggers_on string[] @description("Which steps trigger this compensation")
}

class WorkflowExecution {
    workflow_id string
    definition_id string
    definition_version string
    status WorkflowStatus
    input map<string, string>
    output map<string, string>?
    context map<string, string> @description("Shared state between steps")
    started_at string
    completed_at string?
    duration_seconds float?
    current_step string?
    progress_percentage int @default(0)
    step_executions StepExecution[]
    error_details ErrorDetails?
    cost_breakdown CostBreakdown?
    user_id string?
    correlation_id string?
}

class StepExecution {
    step_id string
    execution_id string
    agent_id string
    action string
    status StepStatus
    input map<string, string>
    output map<string, string>?
    started_at string?
    completed_at string?
    duration_seconds float?
    error_details ErrorDetails?
    retry_count int @default(0)
    cost_dollars float?
}

class RetryPolicy {
    max_attempts int @default(3)
    initial_delay_seconds int @default(30)
    max_delay_seconds int @default(300)
    backoff_multiplier float @default(2.0)
    retry_on_errors string[] @description("Error codes that trigger retry")
}

class CostBreakdown {
    total_cost_dollars float
    agent_costs map<string, float> @description("Cost per agent")
    token_costs float? @description("AI token costs")
    compute_costs float? @description("Infrastructure costs")
    storage_costs float? @description("Data storage costs")
}
```

### Event Sourcing Models

```baml
// baml/schemas/events.baml

enum EventType {
    PROFILE_CREATED
    PROFILE_UPDATED
    PROFILE_DELETED
    OPPORTUNITY_DISCOVERED
    ANALYSIS_STARTED
    ANALYSIS_COMPLETED
    WORKFLOW_INITIATED
    WORKFLOW_STEP_COMPLETED
    WORKFLOW_FAILED
    AGENT_REGISTERED
    AGENT_HEALTH_CHANGED
    SYSTEM_ALERT
    USER_ACTION
}

class Event {
    id string @description("Unique event identifier")
    event_type EventType
    aggregate_id string @description("ID of the entity this event affects")
    aggregate_type string @description("Type of entity (profile, workflow, etc.)")
    timestamp string @description("ISO 8601 timestamp")
    version int @description("Event version for ordering")
    data map<string, string> @description("Event-specific data")
    metadata EventMetadata?
    user_id string? @description("User who triggered the event")
    correlation_id string? @description("Request correlation ID")
}

class EventMetadata {
    source string @description("System component that generated event")
    ip_address string?
    user_agent string?
    session_id string?
    additional_context map<string, string>?
}

// Specific event data schemas
class ProfileCreatedEvent {
    profile_id string
    name string
    organization string
    created_by string
    initial_data map<string, string>?
}

class AnalysisCompletedEvent {
    profile_id string
    analysis_type string
    agent_id string
    execution_id string
    results_summary string
    cost_dollars float
    duration_seconds float
    quality_score float?
}

class WorkflowStepCompletedEvent {
    workflow_id string
    step_id string
    agent_id string
    execution_id string
    status StepStatus
    output map<string, string>?
    next_step string?
    progress_percentage int
}

class OpportunityDiscoveredEvent {
    profile_id string
    opportunity_id string
    source string @description("BMF, Grants.gov, etc.")
    organization_name string
    funding_amount int?
    deadline string?
    match_score float
    discovery_agent string
}
```

## Database Schema (SQL)

### Core Tables

```sql
-- profiles table
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    organization VARCHAR(255) NOT NULL,
    description TEXT,
    focus_areas JSONB,
    geographic_scope JSONB,
    funding_range JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    metadata JSONB,
    version INTEGER DEFAULT 1
);

-- opportunities table
CREATE TABLE opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES profiles(id),
    external_id VARCHAR(255), -- BMF EIN, Grant.gov ID, etc.
    source VARCHAR(100) NOT NULL, -- 'bmf', 'grants_gov', 'foundation'
    organization_name VARCHAR(255) NOT NULL,
    opportunity_type VARCHAR(100), -- 'grant', 'partnership', 'contract'
    funding_amount BIGINT,
    deadline TIMESTAMP,
    status VARCHAR(50) DEFAULT 'discovered',
    match_score FLOAT,
    analysis_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- agent_registry table
CREATE TABLE agent_registry (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    capabilities JSONB NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    version VARCHAR(20) NOT NULL,
    status VARCHAR(50) DEFAULT 'healthy',
    health_check_url VARCHAR(500),
    max_concurrent_tasks INTEGER DEFAULT 10,
    timeout_seconds INTEGER DEFAULT 300,
    last_health_check TIMESTAMP,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- workflow_executions table
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_type VARCHAR(100) NOT NULL,
    definition_version VARCHAR(20),
    profile_id UUID REFERENCES profiles(id),
    status VARCHAR(50) DEFAULT 'initiated',
    input_data JSONB NOT NULL,
    output_data JSONB,
    context_data JSONB DEFAULT '{}',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    current_step VARCHAR(100),
    progress_percentage INTEGER DEFAULT 0,
    total_cost_dollars DECIMAL(10,2),
    user_id UUID REFERENCES users(id),
    correlation_id VARCHAR(100),
    error_details JSONB
);

-- step_executions table
CREATE TABLE step_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflow_executions(id),
    step_id VARCHAR(100) NOT NULL,
    agent_id VARCHAR(100) REFERENCES agent_registry(id),
    action VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    input_data JSONB NOT NULL,
    output_data JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds DECIMAL(10,3),
    retry_count INTEGER DEFAULT 0,
    cost_dollars DECIMAL(10,4),
    error_details JSONB
);

-- events table (event sourcing)
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    aggregate_id VARCHAR(255) NOT NULL,
    aggregate_type VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL,
    data JSONB NOT NULL,
    metadata JSONB,
    user_id UUID REFERENCES users(id),
    correlation_id VARCHAR(100)
);

-- Create indexes for performance
CREATE INDEX idx_profiles_created_by ON profiles(created_by);
CREATE INDEX idx_profiles_created_at ON profiles(created_at);
CREATE INDEX idx_opportunities_profile_id ON opportunities(profile_id);
CREATE INDEX idx_opportunities_source ON opportunities(source);
CREATE INDEX idx_opportunities_deadline ON opportunities(deadline);
CREATE INDEX idx_workflow_executions_profile_id ON workflow_executions(profile_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_step_executions_workflow_id ON step_executions(workflow_id);
CREATE INDEX idx_events_aggregate_id ON events(aggregate_id);
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_correlation_id ON events(correlation_id);
```

### Intelligence Database Schema

```sql
-- BMF Organizations (Business Master File)
CREATE TABLE bmf_organizations (
    ein VARCHAR(9) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    ntee_code VARCHAR(10),
    classification VARCHAR(100),
    ruling_date DATE,
    deductibility_code VARCHAR(10),
    foundation_code VARCHAR(10),
    activity_codes JSONB,
    organization_code VARCHAR(10),
    exempt_organization_status_code VARCHAR(10),
    tax_period VARCHAR(6),
    asset_code VARCHAR(10),
    income_code VARCHAR(10),
    filing_requirement_code VARCHAR(10),
    pf_filing_requirement_code VARCHAR(10),
    accounting_period INTEGER,
    asset_amount BIGINT,
    income_amount BIGINT,
    revenue_amount BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(50) DEFAULT 'bmf'
);

-- Form 990 (Large nonprofits)
CREATE TABLE form_990 (
    ein VARCHAR(9) NOT NULL,
    tax_year INTEGER NOT NULL,
    organization_name VARCHAR(255),
    total_revenue BIGINT,
    total_expenses BIGINT,
    net_assets BIGINT,
    total_assets BIGINT,
    total_liabilities BIGINT,
    program_service_revenue BIGINT,
    investment_income BIGINT,
    other_revenue BIGINT,
    government_grants BIGINT,
    total_program_service_expenses BIGINT,
    total_management_expenses BIGINT,
    total_fundraising_expenses BIGINT,
    compensation_current_officers BIGINT,
    other_salaries_wages BIGINT,
    pension_employee_benefits BIGINT,
    professional_fundraising_fees BIGINT,
    accounting_fees BIGINT,
    legal_fees BIGINT,
    supplies BIGINT,
    telephone BIGINT,
    postage_shipping BIGINT,
    occupancy BIGINT,
    equipment_rental_maintenance BIGINT,
    printing_publications BIGINT,
    travel BIGINT,
    conferences_conventions_meetings BIGINT,
    interest BIGINT,
    payments_affiliates BIGINT,
    depreciation_depletion BIGINT,
    insurance BIGINT,
    other_expenses BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ein, tax_year),
    FOREIGN KEY (ein) REFERENCES bmf_organizations(ein)
);

-- Form 990-PF (Private foundations)
CREATE TABLE form_990pf (
    ein VARCHAR(9) NOT NULL,
    tax_year INTEGER NOT NULL,
    foundation_name VARCHAR(255),
    total_revenue BIGINT,
    total_expenses BIGINT,
    net_assets BIGINT,
    total_assets BIGINT,
    fair_market_value_assets BIGINT,
    cash_savings_checking BIGINT,
    corporate_stock BIGINT,
    corporate_bonds BIGINT,
    government_obligations BIGINT,
    land_buildings_equipment BIGINT,
    other_investments BIGINT,
    total_charitable_distributions BIGINT,
    distributions_to_donor_advised_funds BIGINT,
    undistributed_income BIGINT,
    distributable_amount BIGINT,
    minimum_investment_return BIGINT,
    adjusted_net_income BIGINT,
    analysis_income_producing_activities JSONB,
    officer_compensation BIGINT,
    accounting_fees BIGINT,
    legal_fees BIGINT,
    investment_management_fees BIGINT,
    other_professional_fees BIGINT,
    interest_expense BIGINT,
    taxes BIGINT,
    other_expenses BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ein, tax_year),
    FOREIGN KEY (ein) REFERENCES bmf_organizations(ein)
);

-- Government opportunities (Grants.gov, USASpending)
CREATE TABLE government_opportunities (
    opportunity_id VARCHAR(100) PRIMARY KEY,
    opportunity_number VARCHAR(100),
    title VARCHAR(500) NOT NULL,
    agency_code VARCHAR(10),
    agency_name VARCHAR(255),
    posted_date DATE,
    close_date DATE,
    last_updated_date DATE,
    opportunity_type VARCHAR(100),
    funding_instrument_type VARCHAR(100),
    category_code VARCHAR(10),
    category_name VARCHAR(255),
    cfda_numbers JSONB,
    eligible_applicants JSONB,
    additional_info_eligibility TEXT,
    funding_amount_min BIGINT,
    funding_amount_max BIGINT,
    expected_awards INTEGER,
    cost_sharing BOOLEAN,
    description TEXT,
    contact_info JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for intelligence database
CREATE INDEX idx_bmf_state ON bmf_organizations(state);
CREATE INDEX idx_bmf_ntee_code ON bmf_organizations(ntee_code);
CREATE INDEX idx_bmf_foundation_code ON bmf_organizations(foundation_code);
CREATE INDEX idx_bmf_asset_amount ON bmf_organizations(asset_amount);
CREATE INDEX idx_form_990_tax_year ON form_990(tax_year);
CREATE INDEX idx_form_990_total_revenue ON form_990(total_revenue);
CREATE INDEX idx_form_990pf_tax_year ON form_990pf(tax_year);
CREATE INDEX idx_form_990pf_total_assets ON form_990pf(total_assets);
CREATE INDEX idx_gov_opp_agency ON government_opportunities(agency_code);
CREATE INDEX idx_gov_opp_close_date ON government_opportunities(close_date);
```

## Pydantic Models (Python)

### Core Entity Models

```python
# src/models/entities.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid

class EntityBase(BaseModel):
    """Base class for all entities"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1)
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Address(BaseModel):
    street: str
    city: str
    state: str = Field(regex=r'^[A-Z]{2}$')
    zip_code: str = Field(regex=r'^\d{5}(-\d{4})?$')
    country: str = Field(default='USA')

class ContactInfo(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = None
    address: Optional[Address] = None

class FinancialData(BaseModel):
    year: int = Field(ge=1990, le=2030)
    revenue: int = Field(ge=0)
    expenses: int = Field(ge=0)
    net_assets: int
    program_expense_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)
    administrative_expense_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)
    fundraising_expense_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)

    @validator('program_expense_ratio', 'administrative_expense_ratio', 'fundraising_expense_ratio')
    def validate_ratios(cls, v, values):
        """Ensure expense ratios sum to <= 1.0"""
        if v is not None:
            total_ratio = sum(filter(None, [
                v,
                values.get('program_expense_ratio'),
                values.get('administrative_expense_ratio'),
                values.get('fundraising_expense_ratio')
            ]))
            if total_ratio > 1.0:
                raise ValueError('Expense ratios cannot sum to more than 1.0')
        return v

class Grant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    grantor_name: str
    grantor_ein: Optional[str] = Field(None, regex=r'^\d{9}$')
    amount: int = Field(ge=0)
    year: int = Field(ge=1990, le=2030)
    purpose: Optional[str] = None
    duration_months: Optional[int] = Field(None, ge=1, le=120)

class Nonprofit(EntityBase):
    ein: str = Field(regex=r'^\d{9}$')
    name: str = Field(min_length=1, max_length=255)
    city: Optional[str] = None
    state: str = Field(regex=r'^[A-Z]{2}$')
    zip_code: Optional[str] = Field(None, regex=r'^\d{5}(-\d{4})?$')
    ntee_code: str = Field(regex=r'^[A-Z]\d{2}$')
    classification: str
    revenue: Optional[int] = Field(None, ge=0)
    assets: Optional[int] = Field(None, ge=0)
    employees: Optional[int] = Field(None, ge=0)
    founded_year: Optional[int] = Field(None, ge=1800, le=2030)
    website: Optional[str] = None
    mission_statement: Optional[str] = None
    financial_data: List[FinancialData] = Field(default_factory=list)
    grants_received: List[Grant] = Field(default_factory=list)

class Foundation(EntityBase):
    ein: str = Field(regex=r'^\d{9}$')
    name: str = Field(min_length=1, max_length=255)
    city: Optional[str] = None
    state: str = Field(regex=r'^[A-Z]{2}$')
    foundation_type: str
    assets: int = Field(ge=0)
    annual_giving: int = Field(ge=0)
    focus_areas: List[str] = Field(default_factory=list)
    geographic_focus: List[str] = Field(default_factory=list)
    application_deadlines: List[str] = Field(default_factory=list)
```

### Agent and Workflow Models

```python
# src/models/agents.py
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"

class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class AgentConfig(BaseModel):
    id: str = Field(regex=r'^[a-z0-9_]+$')
    name: str
    capabilities: List[str] = Field(min_items=1)
    endpoint: str = Field(regex=r'^https?://.+')
    version: str = Field(regex=r'^\d+\.\d+\.\d+$')
    health_check_url: str
    max_concurrent_tasks: int = Field(default=10, ge=1, le=100)
    timeout_seconds: int = Field(default=300, ge=30, le=3600)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=30, ge=5, le=300)
    metadata: Optional[Dict[str, Any]] = None

class AgentRequest(BaseModel):
    agent_id: str
    action: str
    input: Dict[str, Any]
    timeout_seconds: Optional[int] = None
    priority: TaskPriority = TaskPriority.NORMAL
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ErrorDetails(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    retry_after_seconds: Optional[int] = None

class AgentResponse(BaseModel):
    execution_id: str
    agent_id: str
    action: str
    status: TaskStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[ErrorDetails] = None
    cost_dollars: Optional[float] = Field(None, ge=0)
    tokens_used: Optional[int] = Field(None, ge=0)
    cache_hit: bool = False
```

### Event Sourcing Models

```python
# src/models/events.py
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class EventType(str, Enum):
    PROFILE_CREATED = "profile_created"
    PROFILE_UPDATED = "profile_updated"
    PROFILE_DELETED = "profile_deleted"
    OPPORTUNITY_DISCOVERED = "opportunity_discovered"
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    WORKFLOW_INITIATED = "workflow_initiated"
    WORKFLOW_STEP_COMPLETED = "workflow_step_completed"
    WORKFLOW_FAILED = "workflow_failed"
    AGENT_REGISTERED = "agent_registered"
    AGENT_HEALTH_CHANGED = "agent_health_changed"
    SYSTEM_ALERT = "system_alert"
    USER_ACTION = "user_action"

class EventMetadata(BaseModel):
    source: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    additional_context: Optional[Dict[str, Any]] = None

class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    aggregate_id: str
    aggregate_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(ge=1)
    data: Dict[str, Any]
    metadata: Optional[EventMetadata] = None
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Specific event data models
class ProfileCreatedEventData(BaseModel):
    profile_id: str
    name: str
    organization: str
    created_by: str
    initial_data: Optional[Dict[str, Any]] = None

class AnalysisCompletedEventData(BaseModel):
    profile_id: str
    analysis_type: str
    agent_id: str
    execution_id: str
    results_summary: str
    cost_dollars: float = Field(ge=0)
    duration_seconds: float = Field(ge=0)
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)

class OpportunityDiscoveredEventData(BaseModel):
    profile_id: str
    opportunity_id: str
    source: str
    organization_name: str
    funding_amount: Optional[int] = Field(None, ge=0)
    deadline: Optional[datetime] = None
    match_score: float = Field(ge=0.0, le=1.0)
    discovery_agent: str
```

## MongoDB Schema (NoSQL Alternative)

### Document Structures

```javascript
// profiles collection
{
  "_id": ObjectId(),
  "name": "Virginia Community Foundation",
  "organization": "Virginia Community Foundation",
  "description": "Community foundation serving Virginia",
  "focus_areas": ["education", "health", "environment"],
  "geographic_scope": ["Virginia", "Washington DC"],
  "funding_range": {
    "min": 100000,
    "max": 5000000,
    "preferred": 500000
  },
  "created_at": ISODate(),
  "updated_at": ISODate(),
  "created_by": ObjectId(),
  "metadata": {
    "tier": "enhanced",
    "last_analysis": ISODate(),
    "analysis_count": 5
  },
  "version": 1
}

// opportunities collection
{
  "_id": ObjectId(),
  "profile_id": ObjectId(),
  "external_id": "541234567",
  "source": "bmf",
  "organization_name": "Virginia Education Foundation",
  "opportunity_type": "partnership",
  "funding_amount": 2500000,
  "deadline": ISODate(),
  "status": "analyzed",
  "match_score": 0.85,
  "analysis_summary": "High alignment with education focus",
  "created_at": ISODate(),
  "updated_at": ISODate(),
  "financial_data": {
    "revenue": 2500000,
    "assets": 15000000,
    "program_expense_ratio": 0.78
  },
  "contact_info": {
    "name": "John Smith",
    "title": "Program Director",
    "email": "jsmith@ved.org",
    "phone": "555-123-4567"
  },
  "tags": ["education", "K-12", "Virginia", "high-match"],
  "metadata": {
    "discovery_date": ISODate(),
    "last_contact": ISODate(),
    "priority": "high"
  }
}

// workflow_executions collection
{
  "_id": ObjectId(),
  "workflow_type": "intelligence_tier",
  "tier": "enhanced",
  "profile_id": ObjectId(),
  "status": "completed",
  "input_data": {
    "organization_name": "Virginia Community Foundation",
    "focus_areas": ["education", "health"]
  },
  "output_data": {
    "opportunities_found": 47,
    "total_funding": 125000000,
    "recommendations": [...],
    "analysis_report": "..."
  },
  "context": {
    "bmf_results": {...},
    "ai_analysis": {...},
    "network_analysis": {...}
  },
  "started_at": ISODate(),
  "completed_at": ISODate(),
  "duration_seconds": 1847,
  "progress_percentage": 100,
  "step_executions": [
    {
      "step_id": "bmf_filter",
      "agent_id": "bmf_filter_agent",
      "status": "completed",
      "duration_seconds": 135,
      "cost_dollars": 0.75,
      "output": {...}
    },
    {
      "step_id": "ai_analysis",
      "agent_id": "ai_heavy_agent",
      "status": "completed",
      "duration_seconds": 1200,
      "cost_dollars": 18.50,
      "output": {...}
    }
  ],
  "cost_breakdown": {
    "total_cost_dollars": 22.50,
    "agent_costs": {
      "bmf_filter_agent": 0.75,
      "ai_heavy_agent": 18.50,
      "network_analyzer": 3.25
    }
  },
  "user_id": ObjectId(),
  "correlation_id": "req_12345"
}

// events collection (event sourcing)
{
  "_id": ObjectId(),
  "event_type": "workflow_completed",
  "aggregate_id": "wf_67890",
  "aggregate_type": "workflow",
  "timestamp": ISODate(),
  "version": 15,
  "data": {
    "workflow_id": "wf_67890",
    "status": "completed",
    "duration_seconds": 1847,
    "total_cost": 22.50,
    "opportunities_found": 47
  },
  "metadata": {
    "source": "workflow_orchestrator",
    "ip_address": "192.168.1.100",
    "session_id": "sess_abc123"
  },
  "user_id": ObjectId(),
  "correlation_id": "req_12345"
}
```

## Validation and Serialization

### Input Validation

```python
# src/validation/validators.py
from pydantic import validator, root_validator
from typing import Any, Dict

class ProfileValidator(BaseModel):
    """Profile validation with business rules"""

    @validator('funding_range')
    def validate_funding_range(cls, v):
        """Ensure funding range is logical"""
        if v and 'min' in v and 'max' in v:
            if v['min'] > v['max']:
                raise ValueError('Minimum funding cannot exceed maximum')
            if v['min'] < 0:
                raise ValueError('Minimum funding must be positive')
        return v

    @validator('focus_areas')
    def validate_focus_areas(cls, v):
        """Validate focus areas against known categories"""
        valid_areas = {
            'education', 'health', 'environment', 'arts', 'social_services',
            'religion', 'international', 'public_benefit', 'research'
        }
        if v:
            invalid_areas = set(v) - valid_areas
            if invalid_areas:
                raise ValueError(f'Invalid focus areas: {invalid_areas}')
        return v

    @root_validator
    def validate_geographic_scope(cls, values):
        """Ensure geographic scope is consistent"""
        scope = values.get('geographic_scope', [])
        if scope:
            # Validate state codes
            state_pattern = re.compile(r'^[A-Z]{2}$')
            for location in scope:
                if len(location) == 2 and not state_pattern.match(location):
                    raise ValueError(f'Invalid state code: {location}')
        return values

class AgentRequestValidator(BaseModel):
    """Agent request validation"""

    @validator('timeout_seconds')
    def validate_timeout(cls, v, values):
        """Ensure timeout is reasonable for action type"""
        action = values.get('action')
        if action and v:
            # Different actions have different timeout limits
            limits = {
                'bmf_filter': 600,      # 10 minutes max
                'ai_heavy': 3600,       # 1 hour max
                'ai_lite': 300,         # 5 minutes max
                'network_analysis': 1800 # 30 minutes max
            }
            if action in limits and v > limits[action]:
                raise ValueError(f'Timeout {v}s exceeds limit for {action}')
        return v

    @validator('input')
    def validate_input_schema(cls, v, values):
        """Validate input matches expected schema for action"""
        action = values.get('action')
        if action and v:
            # Define required fields per action
            required_fields = {
                'bmf_filter': ['state'],
                'ai_heavy': ['profile_data'],
                'network_analysis': ['organization_name']
            }
            if action in required_fields:
                missing_fields = set(required_fields[action]) - set(v.keys())
                if missing_fields:
                    raise ValueError(f'Missing required fields for {action}: {missing_fields}')
        return v
```

### Schema Evolution

```python
# src/models/migrations.py
from typing import Dict, Any, Type
from pydantic import BaseModel

class SchemaMigration:
    """Handle schema evolution and backward compatibility"""

    def __init__(self):
        self.migrations = {
            'profile': {
                '1.0.0': self.migrate_profile_v1_to_v2,
                '2.0.0': self.migrate_profile_v2_to_v3
            },
            'workflow': {
                '1.0.0': self.migrate_workflow_v1_to_v2
            }
        }

    def migrate_data(self, data: Dict[str, Any], schema_type: str,
                    from_version: str, to_version: str) -> Dict[str, Any]:
        """Migrate data from one schema version to another"""
        current_data = data.copy()
        current_version = from_version

        # Apply migrations sequentially
        while current_version != to_version:
            migration_key = f"{schema_type}.{current_version}"
            if migration_key not in self.migrations:
                raise ValueError(f"No migration available for {migration_key}")

            migration_func = self.migrations[schema_type][current_version]
            current_data = migration_func(current_data)
            current_version = self._get_next_version(current_version)

        return current_data

    def migrate_profile_v1_to_v2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate profile from v1.0.0 to v2.0.0"""
        # v2.0.0 adds funding_range as nested object
        if 'min_funding' in data or 'max_funding' in data:
            data['funding_range'] = {
                'min': data.pop('min_funding', 0),
                'max': data.pop('max_funding', 1000000)
            }

        # Add version field
        data['schema_version'] = '2.0.0'
        return data

    def migrate_workflow_v1_to_v2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate workflow from v1.0.0 to v2.0.0"""
        # v2.0.0 adds cost tracking
        if 'cost_breakdown' not in data:
            data['cost_breakdown'] = {
                'total_cost_dollars': 0.0,
                'agent_costs': {}
            }

        data['schema_version'] = '2.0.0'
        return data
```

---

This comprehensive data model specification provides type-safe, validated, and evolvable schemas for building scalable 12-factor agent systems. All models support horizontal scaling, event sourcing, and cross-environment deployment while maintaining data integrity and business rule compliance.