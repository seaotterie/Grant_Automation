"""
Custom Scoring Criteria Data Models
Defines flexible, user-configurable scoring criteria for opportunity analysis.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import re


class CriteriaType(str, Enum):
    """Types of custom scoring criteria."""
    KEYWORD = "keyword"           # Keyword matching in descriptions
    FINANCIAL = "financial"       # Financial thresholds (amount, percentage)
    GEOGRAPHIC = "geographic"     # Geographic preferences/requirements
    TIMING = "timing"            # Deadline and timing preferences
    ELIGIBILITY = "eligibility"   # Custom eligibility requirements
    AGENCY = "agency"            # Agency preferences
    CATEGORY = "category"        # Program category preferences
    CUSTOM_RULE = "custom_rule"  # Custom logical rules


class OperatorType(str, Enum):
    """Comparison operators for criteria."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    REGEX_MATCH = "regex_match"
    BETWEEN = "between"


class CriterionValue(BaseModel):
    """Flexible value container for criteria."""
    text_value: Optional[str] = None
    numeric_value: Optional[float] = None
    list_value: Optional[List[str]] = None
    range_value: Optional[Dict[str, float]] = None  # {"min": 1000, "max": 5000}
    boolean_value: Optional[bool] = None
    
    def get_value(self) -> Any:
        """Get the appropriate value based on what's set."""
        if self.text_value is not None:
            return self.text_value
        elif self.numeric_value is not None:
            return self.numeric_value
        elif self.list_value is not None:
            return self.list_value
        elif self.range_value is not None:
            return self.range_value
        elif self.boolean_value is not None:
            return self.boolean_value
        return None


class CustomScoringCriterion(BaseModel):
    """Individual custom scoring criterion."""
    # Core Properties
    criterion_id: str = Field(..., description="Unique identifier for this criterion")
    name: str = Field(..., description="Human-readable name")
    description: str = Field("", description="Description of what this criterion evaluates")
    
    # Criteria Definition
    criteria_type: CriteriaType = Field(..., description="Type of criteria")
    target_field: str = Field(..., description="Field to evaluate (e.g., 'description', 'award_ceiling')")
    operator: OperatorType = Field(..., description="Comparison operator")
    value: CriterionValue = Field(..., description="Value to compare against")
    
    # Scoring Impact
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight in overall score (0-1)")
    positive_impact: bool = Field(True, description="Whether meeting this criterion increases score")
    score_boost: float = Field(0.1, ge=0.0, le=1.0, description="Score increase when criterion is met")
    score_penalty: float = Field(0.0, ge=0.0, le=1.0, description="Score decrease when criterion is not met")
    
    # Configuration
    is_required: bool = Field(False, description="Whether this is a hard requirement")
    is_active: bool = Field(True, description="Whether this criterion is currently active")
    priority: int = Field(1, ge=1, le=10, description="Priority level (1=highest)")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="User who created this criterion")
    tags: List[str] = Field(default_factory=list, description="Tags for organization")
    
    @validator('criterion_id')
    def validate_criterion_id(cls, v):
        """Validate criterion ID format."""
        if not re.match(r'^[a-z0-9_]+$', v):
            raise ValueError('Criterion ID must contain only lowercase letters, numbers, and underscores')
        return v
    
    @validator('target_field')
    def validate_target_field(cls, v):
        """Validate target field is supported."""
        valid_fields = [
            'title', 'description', 'agency_name', 'category_code',
            'award_ceiling', 'award_floor', 'estimated_total_funding',
            'application_due_date', 'eligible_applicants', 'eligible_states',
            'cfda_numbers', 'funding_instrument_type'
        ]
        if v not in valid_fields:
            raise ValueError(f'Target field must be one of: {", ".join(valid_fields)}')
        return v
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()


class CustomScoringProfile(BaseModel):
    """Collection of custom scoring criteria for a specific profile/use case."""
    # Core Properties
    profile_id: str = Field(..., description="Unique identifier for this scoring profile")
    name: str = Field(..., description="Human-readable name")
    description: str = Field("", description="Description of this scoring profile")
    
    # Criteria
    criteria: List[CustomScoringCriterion] = Field(default_factory=list, description="List of scoring criteria")
    
    # Configuration
    base_scoring_enabled: bool = Field(True, description="Whether to use base system scoring")
    custom_weight_total: float = Field(0.3, ge=0.0, le=1.0, description="Total weight for custom criteria")
    base_weight_total: float = Field(0.7, ge=0.0, le=1.0, description="Total weight for base scoring")
    
    # Thresholds
    custom_high_threshold: float = Field(0.8, ge=0.0, le=1.0)
    custom_medium_threshold: float = Field(0.6, ge=0.0, le=1.0)
    custom_low_threshold: float = Field(0.4, ge=0.0, le=1.0)
    
    # Metadata
    is_active: bool = Field(True, description="Whether this profile is active")
    is_default: bool = Field(False, description="Whether this is the default profile")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="User who created this profile")
    
    @validator('base_weight_total', always=True)
    def validate_weights_sum(cls, v, values):
        """Ensure custom and base weights sum to 1.0."""
        custom_weight = values.get('custom_weight_total', 0.0)
        if abs(custom_weight + v - 1.0) > 0.001:  # Allow small floating point errors
            raise ValueError('custom_weight_total and base_weight_total must sum to 1.0')
        return v
    
    def add_criterion(self, criterion: CustomScoringCriterion) -> None:
        """Add a new scoring criterion."""
        # Check for duplicate IDs
        existing_ids = {c.criterion_id for c in self.criteria}
        if criterion.criterion_id in existing_ids:
            raise ValueError(f"Criterion with ID '{criterion.criterion_id}' already exists")
        
        self.criteria.append(criterion)
        self.update_timestamp()
    
    def remove_criterion(self, criterion_id: str) -> bool:
        """Remove a scoring criterion by ID."""
        initial_count = len(self.criteria)
        self.criteria = [c for c in self.criteria if c.criterion_id != criterion_id]
        
        if len(self.criteria) < initial_count:
            self.update_timestamp()
            return True
        return False
    
    def get_criterion(self, criterion_id: str) -> Optional[CustomScoringCriterion]:
        """Get a criterion by ID."""
        for criterion in self.criteria:
            if criterion.criterion_id == criterion_id:
                return criterion
        return None
    
    def get_active_criteria(self) -> List[CustomScoringCriterion]:
        """Get only active criteria, sorted by priority."""
        active_criteria = [c for c in self.criteria if c.is_active]
        return sorted(active_criteria, key=lambda x: x.priority)
    
    def get_required_criteria(self) -> List[CustomScoringCriterion]:
        """Get required criteria that must be met."""
        return [c for c in self.criteria if c.is_required and c.is_active]
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()


class CustomScoringResult(BaseModel):
    """Result of applying custom scoring criteria to an opportunity."""
    # Core Properties
    opportunity_id: str = Field(..., description="ID of the scored opportunity")
    profile_id: str = Field(..., description="ID of the scoring profile used")
    
    # Scoring Results
    base_score: float = Field(0.0, ge=0.0, le=1.0, description="Original base scoring result")
    custom_score: float = Field(0.0, ge=0.0, le=1.0, description="Custom criteria score")
    final_score: float = Field(0.0, ge=0.0, le=1.0, description="Weighted final score")
    
    # Criteria Results
    criteria_results: List[Dict[str, Any]] = Field(default_factory=list, description="Results for each criterion")
    met_criteria_count: int = Field(0, description="Number of criteria that were met")
    total_criteria_count: int = Field(0, description="Total number of active criteria")
    required_criteria_met: bool = Field(True, description="Whether all required criteria were met")
    
    # Analysis
    score_breakdown: Dict[str, float] = Field(default_factory=dict, description="Breakdown of score components")
    improvement_suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    
    # Metadata
    scoring_timestamp: datetime = Field(default_factory=datetime.now)
    processing_time_ms: Optional[float] = Field(None, description="Time taken to score in milliseconds")
    
    @property
    def criteria_success_rate(self) -> float:
        """Calculate the percentage of criteria that were met."""
        if self.total_criteria_count == 0:
            return 1.0
        return self.met_criteria_count / self.total_criteria_count


class ScoringProfileManager(BaseModel):
    """Manager for multiple scoring profiles."""
    profiles: Dict[str, CustomScoringProfile] = Field(default_factory=dict)
    default_profile_id: Optional[str] = Field(None)
    
    def add_profile(self, profile: CustomScoringProfile) -> None:
        """Add a new scoring profile."""
        self.profiles[profile.profile_id] = profile
        
        # Set as default if it's the first profile or explicitly marked as default
        if profile.is_default or not self.default_profile_id:
            self.default_profile_id = profile.profile_id
    
    def get_profile(self, profile_id: str) -> Optional[CustomScoringProfile]:
        """Get a profile by ID."""
        return self.profiles.get(profile_id)
    
    def get_default_profile(self) -> Optional[CustomScoringProfile]:
        """Get the default scoring profile."""
        if self.default_profile_id:
            return self.profiles.get(self.default_profile_id)
        return None
    
    def get_active_profiles(self) -> List[CustomScoringProfile]:
        """Get all active profiles."""
        return [p for p in self.profiles.values() if p.is_active]
    
    def set_default_profile(self, profile_id: str) -> bool:
        """Set a profile as the default."""
        if profile_id in self.profiles:
            # Unmark previous default
            if self.default_profile_id:
                old_default = self.profiles[self.default_profile_id]
                old_default.is_default = False
            
            # Set new default
            self.profiles[profile_id].is_default = True
            self.default_profile_id = profile_id
            return True
        return False
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete a scoring profile."""
        if profile_id in self.profiles:
            del self.profiles[profile_id]
            
            # Clear default if it was deleted
            if self.default_profile_id == profile_id:
                self.default_profile_id = None
                # Set first available profile as default
                active_profiles = self.get_active_profiles()
                if active_profiles:
                    self.set_default_profile(active_profiles[0].profile_id)
            
            return True
        return False


# Export models
__all__ = [
    "CriteriaType",
    "OperatorType", 
    "CriterionValue",
    "CustomScoringCriterion",
    "CustomScoringProfile",
    "CustomScoringResult",
    "ScoringProfileManager"
]