"""
Government Opportunity Data Models
Data models for Grants.gov and USASpending.gov API integration.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
from enum import Enum
import re


class OpportunityStatus(str, Enum):
    """Grant opportunity status."""
    FORECASTED = "forecasted"
    POSTED = "posted"
    CLOSED = "closed"
    AWARDED = "awarded"
    ARCHIVED = "archived"


class FundingInstrumentType(str, Enum):
    """Type of funding instrument."""
    GRANT = "grant"
    COOPERATIVE_AGREEMENT = "cooperative_agreement"
    CONTRACT = "contract"
    OTHER = "other"


class EligibilityCategory(str, Enum):
    """Applicant eligibility categories."""
    NONPROFIT = "nonprofit"
    STATE_GOVERNMENT = "state_government" 
    LOCAL_GOVERNMENT = "local_government"
    TRIBAL_GOVERNMENT = "tribal_government"
    UNIVERSITY = "university"
    FOR_PROFIT = "for_profit"
    INDIVIDUAL = "individual"
    OTHER = "other"


class GovernmentOpportunity(BaseModel):
    """Standardized model for federal grant opportunities from Grants.gov."""
    # Core Identification
    opportunity_id: str = Field(..., description="Unique opportunity identifier")
    opportunity_number: str = Field(..., description="Official opportunity number")
    title: str = Field(..., description="Opportunity title")
    description: str = Field("", description="Opportunity description")
    
    # Agency Information
    agency_code: str = Field(..., description="Federal agency code")
    agency_name: str = Field(..., description="Federal agency name")
    sub_agency: Optional[str] = Field(None, description="Sub-agency or office")
    
    # Opportunity Details
    status: OpportunityStatus = Field(..., description="Current opportunity status")
    funding_instrument_type: FundingInstrumentType = Field(..., description="Type of funding")
    category_of_funding_activity: Optional[str] = Field(None, description="CFDA category")
    cfda_numbers: List[str] = Field(default_factory=list, description="CFDA program numbers")
    
    # Financial Information
    estimated_total_funding: Optional[float] = Field(None, description="Estimated total program funding")
    award_ceiling: Optional[float] = Field(None, description="Maximum individual award amount")
    award_floor: Optional[float] = Field(None, description="Minimum individual award amount")
    expected_number_of_awards: Optional[int] = Field(None, description="Expected number of awards")
    
    # Dates
    posted_date: Optional[datetime] = Field(None, description="Date opportunity was posted")
    application_due_date: Optional[datetime] = Field(None, description="Application deadline")
    archive_date: Optional[datetime] = Field(None, description="Archive date")
    last_updated_date: Optional[datetime] = Field(None, description="Last modification date")
    
    # Eligibility
    eligible_applicants: List[EligibilityCategory] = Field(default_factory=list, description="Eligible applicant types")
    unrestricted_submission: bool = Field(True, description="Whether submission is unrestricted")
    
    # Geographic Scope
    eligible_states: List[str] = Field(default_factory=list, description="Eligible states (empty = all states)")
    eligible_counties: List[str] = Field(default_factory=list, description="Eligible counties")
    
    # Application Information
    grants_gov_url: Optional[str] = Field(None, description="Grants.gov opportunity URL")
    application_procedures: Optional[str] = Field(None, description="Application procedures")
    
    # Contact Information
    contact_email: Optional[str] = Field(None, description="Program contact email")
    contact_phone: Optional[str] = Field(None, description="Program contact phone")
    contact_name: Optional[str] = Field(None, description="Program contact name")
    
    # Analysis Fields
    relevance_score: float = Field(0.0, description="Calculated relevance score")
    match_reasons: List[str] = Field(default_factory=list, description="Reasons for matching")
    competition_level: str = Field("unknown", description="Estimated competition level")
    
    # Metadata
    source: str = Field("grants_gov", description="Data source")
    retrieved_at: datetime = Field(default_factory=datetime.now, description="Data retrieval timestamp")
    processing_notes: List[str] = Field(default_factory=list, description="Processing notes")
    
    @validator('opportunity_id', 'opportunity_number')
    def validate_not_empty(cls, v):
        """Ensure required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('agency_code')
    def validate_agency_code(cls, v):
        """Validate agency code format."""
        if not re.match(r'^[A-Z0-9-]{2,10}$', v):
            raise ValueError('Agency code must be 2-10 uppercase alphanumeric characters')
        return v
    
    def add_processing_note(self, note: str) -> None:
        """Add a processing note with timestamp."""
        self.processing_notes.append(f"{datetime.now().isoformat()}: {note}")
    
    def calculate_days_until_deadline(self) -> Optional[int]:
        """Calculate days until application deadline."""
        if not self.application_due_date:
            return None
        delta = self.application_due_date - datetime.now()
        return max(0, delta.days)
    
    def is_eligible_for_nonprofits(self) -> bool:
        """Check if nonprofits are eligible to apply."""
        return EligibilityCategory.NONPROFIT in self.eligible_applicants
    
    def is_active(self) -> bool:
        """Check if opportunity is currently active."""
        return self.status == OpportunityStatus.POSTED
    
    def matches_state(self, state_code: str) -> bool:
        """Check if opportunity is available in specified state."""
        if not self.eligible_states:  # Empty list means all states eligible
            return True
        return state_code.upper() in [s.upper() for s in self.eligible_states]


class HistoricalAward(BaseModel):
    """Historical award data from USASpending.gov."""
    # Award Identification
    award_id: str = Field(..., description="Unique award identifier")
    award_number: Optional[str] = Field(None, description="Award number")
    award_title: Optional[str] = Field(None, description="Award title")
    award_description: Optional[str] = Field(None, description="Award description")
    
    # Financial Information
    award_amount: float = Field(..., description="Total award amount")
    federal_award_amount: Optional[float] = Field(None, description="Federal portion of award")
    non_federal_funding: Optional[float] = Field(None, description="Non-federal funding amount")
    
    # Award Details
    award_type: str = Field(..., description="Type of award (grant, contract, etc.)")
    cfda_number: Optional[str] = Field(None, description="CFDA program number")
    cfda_title: Optional[str] = Field(None, description="CFDA program title")
    
    # Dates
    start_date: Optional[date] = Field(None, description="Award start date")
    end_date: Optional[date] = Field(None, description="Award end date")
    action_date: Optional[date] = Field(None, description="Award action date")
    
    # Recipient Information
    recipient_name: str = Field(..., description="Recipient organization name")
    recipient_ein: Optional[str] = Field(None, description="Recipient EIN")
    recipient_duns: Optional[str] = Field(None, description="Recipient DUNS number")
    recipient_uei: Optional[str] = Field(None, description="Recipient UEI")
    
    # Geographic Information
    recipient_state: Optional[str] = Field(None, description="Recipient state")
    recipient_city: Optional[str] = Field(None, description="Recipient city")
    recipient_county: Optional[str] = Field(None, description="Recipient county")
    recipient_zip: Optional[str] = Field(None, description="Recipient ZIP code")
    
    # Agency Information
    awarding_agency_code: str = Field(..., description="Awarding agency code")
    awarding_agency_name: str = Field(..., description="Awarding agency name")
    awarding_sub_agency: Optional[str] = Field(None, description="Awarding sub-agency")
    funding_agency_code: Optional[str] = Field(None, description="Funding agency code")
    funding_agency_name: Optional[str] = Field(None, description="Funding agency name")
    
    # Program Information
    object_class: Optional[str] = Field(None, description="Object class code")
    program_activity: Optional[str] = Field(None, description="Program activity")
    
    # Metadata
    source: str = Field("usaspending", description="Data source")
    retrieved_at: datetime = Field(default_factory=datetime.now, description="Data retrieval timestamp")
    
    @validator('recipient_ein')
    def validate_ein(cls, v):
        """Validate EIN format if provided."""
        if v and not re.match(r'^\d{9}$', v):
            raise ValueError('EIN must be exactly 9 digits')
        return v
    
    def calculate_award_duration_days(self) -> Optional[int]:
        """Calculate award duration in days."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None
    
    def is_current_award(self) -> bool:
        """Check if award is currently active."""
        if not self.end_date:
            return True  # No end date means ongoing
        return self.end_date >= date.today()


class OrganizationAwardHistory(BaseModel):
    """Collection of historical awards for an organization."""
    ein: str = Field(..., description="Organization EIN")
    name: str = Field(..., description="Organization name")
    awards: List[HistoricalAward] = Field(default_factory=list, description="Historical awards")
    
    # Calculated Statistics
    total_award_amount: float = Field(0.0, description="Total amount across all awards")
    award_count: int = Field(0, description="Number of awards received")
    unique_agencies: List[str] = Field(default_factory=list, description="Unique funding agencies")
    award_date_range: Optional[Dict[str, date]] = Field(None, description="Date range of awards")
    average_award_amount: float = Field(0.0, description="Average award amount")
    
    # Success Metrics
    funding_track_record_score: float = Field(0.0, description="Track record score based on awards")
    funding_diversity_score: float = Field(0.0, description="Diversity of funding sources score")
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    @validator('ein')
    def validate_ein(cls, v):
        """Validate EIN format."""
        if not re.match(r'^\d{9}$', v):
            raise ValueError('EIN must be exactly 9 digits')
        return v
    
    def calculate_statistics(self) -> None:
        """Calculate summary statistics from awards."""
        if not self.awards:
            return
        
        self.award_count = len(self.awards)
        self.total_award_amount = sum(award.award_amount for award in self.awards)
        self.average_award_amount = self.total_award_amount / self.award_count
        
        # Calculate unique agencies
        agencies = set()
        for award in self.awards:
            if award.awarding_agency_name:
                agencies.add(award.awarding_agency_name)
        self.unique_agencies = sorted(list(agencies))
        
        # Calculate date range
        dates = [award.action_date for award in self.awards if award.action_date]
        if dates:
            self.award_date_range = {
                "earliest": min(dates),
                "latest": max(dates)
            }
        
        # Calculate scores
        self._calculate_track_record_score()
        self._calculate_diversity_score()
    
    def _calculate_track_record_score(self) -> None:
        """Calculate funding track record score (0-1)."""
        if not self.awards:
            self.funding_track_record_score = 0.0
            return
        
        # Base score on number of awards and total funding
        award_count_score = min(1.0, self.award_count / 10.0)  # Max at 10 awards
        funding_score = min(1.0, self.total_award_amount / 10_000_000)  # Max at $10M
        
        # Recent activity bonus
        recent_awards = [a for a in self.awards if a.action_date and 
                        (date.today() - a.action_date).days <= 1095]  # 3 years
        recency_score = min(1.0, len(recent_awards) / max(1, self.award_count))
        
        self.funding_track_record_score = (
            award_count_score * 0.4 + 
            funding_score * 0.4 + 
            recency_score * 0.2
        )
    
    def _calculate_diversity_score(self) -> None:
        """Calculate funding diversity score (0-1)."""
        if len(self.unique_agencies) <= 1:
            self.funding_diversity_score = 0.0
        else:
            # Score based on number of different agencies
            self.funding_diversity_score = min(1.0, len(self.unique_agencies) / 5.0)  # Max at 5 agencies
    
    def get_awards_by_agency(self, agency_name: str) -> List[HistoricalAward]:
        """Get all awards from a specific agency."""
        return [award for award in self.awards if award.awarding_agency_name == agency_name]
    
    def get_recent_awards(self, days: int = 1095) -> List[HistoricalAward]:
        """Get awards from the last N days (default 3 years)."""
        cutoff_date = date.today() - datetime.timedelta(days=days)
        return [award for award in self.awards if award.action_date and award.action_date >= cutoff_date]


class GovernmentOpportunityMatch(BaseModel):
    """Represents a matched government opportunity with scoring."""
    opportunity: GovernmentOpportunity = Field(..., description="The matched opportunity")
    organization: Optional[str] = Field(None, description="Organization EIN being matched")
    
    # Matching Scores
    relevance_score: float = Field(0.0, description="Overall relevance score")
    eligibility_score: float = Field(0.0, description="Eligibility match score")
    geographic_score: float = Field(0.0, description="Geographic eligibility score")
    timing_score: float = Field(0.0, description="Timing/deadline score")
    financial_fit_score: float = Field(0.0, description="Financial size fit score")
    
    # Historical Performance
    historical_success_score: float = Field(0.0, description="Historical success with similar opportunities")
    competition_assessment: str = Field("unknown", description="Competition level assessment")
    
    # Recommendations
    recommendation_level: str = Field("review", description="Recommendation level (high/medium/low/review)")
    action_items: List[str] = Field(default_factory=list, description="Recommended action items")
    preparation_time_needed: Optional[int] = Field(None, description="Estimated prep time in days")
    
    # Metadata
    match_date: datetime = Field(default_factory=datetime.now, description="When match was created")
    match_version: str = Field("1.0", description="Matching algorithm version")
    
    def calculate_overall_score(self) -> None:
        """Calculate weighted overall relevance score."""
        weights = {
            'eligibility': 0.25,
            'geographic': 0.15,
            'timing': 0.20,
            'financial_fit': 0.20,
            'historical_success': 0.20
        }
        
        self.relevance_score = (
            self.eligibility_score * weights['eligibility'] +
            self.geographic_score * weights['geographic'] +
            self.timing_score * weights['timing'] +
            self.financial_fit_score * weights['financial_fit'] +
            self.historical_success_score * weights['historical_success']
        )
        
        # Update recommendation level based on score
        if self.relevance_score >= 0.8:
            self.recommendation_level = "high"
        elif self.relevance_score >= 0.6:
            self.recommendation_level = "medium"
        elif self.relevance_score >= 0.4:
            self.recommendation_level = "low"
        else:
            self.recommendation_level = "review"