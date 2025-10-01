#!/usr/bin/env python3
"""
Pydantic Models for Catalynx Data Transformation Pipeline
Comprehensive models for converting scraped JSON data into normalized database records

Handles:
- Web scraping data from frontend
- Database JSON fields (board_members, web_enhanced_data, verification_data)
- Name parsing and normalization
- Cross-source deduplication
- Data validation and quality scoring
"""

from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional, Dict, Any, Union, Literal
from datetime import datetime, date
from enum import Enum
import re
import json
from decimal import Decimal


# =====================================================================================
# ENUMS AND CONSTANTS
# =====================================================================================

class DataSource(str, Enum):
    """Data source enumeration"""
    WEB_SCRAPING = "web_scraping"
    BOARD_MEMBERS = "board_members"
    VERIFICATION_DATA = "verification_data"
    TAX_FILING = "tax_filing"
    MANUAL_ENTRY = "manual_entry"
    API_IMPORT = "api_import"

class ContactType(str, Enum):
    """Contact information types"""
    EMAIL = "email"
    PHONE = "phone"
    WEBSITE = "website"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    ADDRESS = "address"
    FAX = "fax"

class ProgramType(str, Enum):
    """Program/service types"""
    DIRECT_SERVICE = "direct_service"
    ADVOCACY = "advocacy"
    RESEARCH = "research"
    EDUCATION = "education"
    FUNDRAISING = "fundraising"
    CAPACITY_BUILDING = "capacity_building"
    GRANTMAKING = "grantmaking"
    OTHER = "other"

class ValidationStatus(str, Enum):
    """Data validation status"""
    VALID = "valid"
    INVALID = "invalid"
    NEEDS_REVIEW = "needs_review"
    PENDING = "pending"


# =====================================================================================
# INPUT DATA MODELS - Raw scraped/source data
# =====================================================================================

class ScrapedLeadership(BaseModel):
    """Individual leadership/board member from web scraping"""
    name: str = Field(..., min_length=1, description="Full name")
    title: Optional[str] = Field(None, description="Position/title")
    biography: Optional[str] = Field(None, description="Biography text")
    quality_score: float = Field(0.0, ge=0.0, le=100.0, description="Scraping quality score")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Name cannot be empty")
        return v.strip()

class ScrapedProgram(BaseModel):
    """Program information from web scraping"""
    name: str = Field(..., min_length=1, description="Program name")
    description: Optional[str] = Field(None, description="Program description")
    type: Optional[str] = Field(None, description="Program type/category")
    quality_score: float = Field(0.0, ge=0.0, le=100.0, description="Scraping quality score")
    
class ScrapedContact(BaseModel):
    """Contact information from web scraping"""
    type: ContactType = Field(..., description="Contact type")
    value: str = Field(..., min_length=1, description="Contact value (email, phone, etc.)")
    label: Optional[str] = Field(None, description="Contact label/description")
    quality_score: float = Field(0.0, ge=0.0, le=100.0, description="Scraping quality score")
    
    @validator('value')
    def validate_contact_value(cls, v, values):
        contact_type = values.get('type')
        v = v.strip()
        
        if contact_type == ContactType.EMAIL:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError(f"Invalid email format: {v}")
        elif contact_type == ContactType.PHONE:
            # Clean and validate phone number
            cleaned = re.sub(r'[^0-9]', '', v)
            if len(cleaned) not in [10, 11]:
                raise ValueError(f"Invalid phone number: {v}")
        elif contact_type == ContactType.WEBSITE:
            if not (v.startswith('http://') or v.startswith('https://') or v.startswith('www.')):
                v = f"https://{v}"
        
        return v

class ScrapedExtractedInfo(BaseModel):
    """Extracted information from web scraping"""
    leadership: List[ScrapedLeadership] = Field(default_factory=list)
    programs: List[ScrapedProgram] = Field(default_factory=list)
    mission_statements: List[str] = Field(default_factory=list)
    contact_info: List[ScrapedContact] = Field(default_factory=list)
    
class WebScrapingResults(BaseModel):
    """Complete web scraping results structure"""
    extracted_info: ScrapedExtractedInfo = Field(default_factory=ScrapedExtractedInfo)
    successful_scrapes: List[str] = Field(default_factory=list, description="Successfully scraped URLs")
    source_attribution: Dict[str, Any] = Field(default_factory=dict, description="Source attribution data")
    scraping_timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    total_quality_score: float = Field(0.0, ge=0.0, le=100.0, description="Overall scraping quality")

class BoardMemberData(BaseModel):
    """Board member from database JSON field"""
    name: str = Field(..., min_length=1)
    title: Optional[str] = None
    tenure: Optional[str] = None
    background: Optional[str] = None
    compensation: Optional[Union[int, float]] = None
    committees: Optional[List[str]] = None
    
class DatabaseJSONFields(BaseModel):
    """Raw JSON data from database fields"""
    board_members: Optional[List[BoardMemberData]] = None
    web_enhanced_data: Optional[WebScrapingResults] = None
    verification_data: Optional[Dict[str, Any]] = None


# =====================================================================================
# NORMALIZED OUTPUT MODELS - Clean, validated data for database
# =====================================================================================

class ParsedName(BaseModel):
    """Parsed and normalized name components"""
    full_name: str = Field(..., description="Complete original name")
    first_name: Optional[str] = Field(None, description="First name")
    middle_name: Optional[str] = Field(None, description="Middle name/initial")
    last_name: Optional[str] = Field(None, description="Last name")
    suffix: Optional[str] = Field(None, description="Suffix (Jr, Sr, III, etc.)")
    prefix: Optional[str] = Field(None, description="Prefix (Dr, Prof, etc.)")
    normalized_name: str = Field(..., description="Normalized version for matching")
    
    @validator('normalized_name', always=True)
    def generate_normalized_name(cls, v, values):
        if v:
            return v
        
        # Generate normalized name from components
        first = values.get('first_name', '').strip()
        last = values.get('last_name', '').strip()
        
        if first and last:
            return f"{first} {last}".strip()
        else:
            # Fallback to full name without titles/suffixes
            full_name = values.get('full_name', '').strip()
            # Remove common titles and suffixes
            name_clean = re.sub(r'^(Dr|Prof|Mr|Ms|Mrs|Miss)\.?\s+', '', full_name, flags=re.IGNORECASE)
            name_clean = re.sub(r'\s+(Jr|Sr|III|IV|V|PhD|MD|JD|MBA)\.?$', '', name_clean, flags=re.IGNORECASE)
            return name_clean.strip()

class Person(BaseModel):
    """Normalized person record"""
    parsed_name: ParsedName
    primary_title: Optional[str] = Field(None, description="Primary/most recent title")
    all_titles: List[str] = Field(default_factory=list, description="All known titles")
    biography: Optional[str] = Field(None, description="Biography/background information")
    
    # Data quality and source tracking
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in person data")
    data_sources: List[DataSource] = Field(default_factory=list, description="Sources of data")
    quality_flags: List[str] = Field(default_factory=list, description="Quality issues or notes")
    
    # Deduplication support
    match_key: str = Field(..., description="Generated key for matching duplicates")
    
    @validator('match_key', always=True)
    def generate_match_key(cls, v, values):
        if v:
            return v
        
        parsed_name = values.get('parsed_name')
        if parsed_name:
            # Generate a key for deduplication
            name = parsed_name.normalized_name.lower()
            # Remove punctuation and extra spaces
            key = re.sub(r'[^a-z0-9\s]', '', name)
            key = re.sub(r'\s+', ' ', key).strip()
            return key
        return ""

class OrganizationRole(BaseModel):
    """Person-organization relationship record"""
    person_match_key: str = Field(..., description="Reference to person record")
    organization_ein: str = Field(..., description="Organization EIN")
    position_title: str = Field(..., description="Position/role title")
    
    # Role details
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = Field(True, description="Whether role is current")
    is_board_member: bool = Field(False, description="Whether position is board role")
    is_executive: bool = Field(False, description="Whether position is executive role")
    compensation: Optional[Decimal] = Field(None, description="Annual compensation if available")
    
    # Source and quality
    data_source: DataSource = Field(..., description="Source of this role data")
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in role data")
    
    # Committees and additional details
    committees: List[str] = Field(default_factory=list, description="Committee memberships")
    notes: Optional[str] = Field(None, description="Additional notes")

class Program(BaseModel):
    """Normalized program/service record"""
    name: str = Field(..., min_length=1, description="Program name")
    description: Optional[str] = Field(None, description="Program description")
    program_type: Optional[ProgramType] = Field(None, description="Categorized program type")
    
    # Classification and quality
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    data_source: DataSource = Field(..., description="Source of program data")
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in program data")
    
    # Deduplication
    match_key: str = Field(..., description="Generated key for matching duplicates")
    
    @validator('match_key', always=True)
    def generate_match_key(cls, v, values):
        if v:
            return v
        
        name = values.get('name', '').lower().strip()
        # Generate key for deduplication
        key = re.sub(r'[^a-z0-9\s]', '', name)
        key = re.sub(r'\s+', ' ', key).strip()
        return key

class Contact(BaseModel):
    """Normalized contact information record"""
    contact_type: ContactType = Field(..., description="Type of contact")
    value: str = Field(..., description="Contact value")
    label: Optional[str] = Field(None, description="Contact label/description")
    
    # Validation and verification
    is_verified: bool = Field(False, description="Whether contact has been verified")
    validation_status: ValidationStatus = Field(ValidationStatus.PENDING)
    last_verified: Optional[datetime] = None
    
    # Quality and source
    data_source: DataSource = Field(..., description="Source of contact data")
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in contact data")
    
    # Privacy and preferences
    is_public: bool = Field(True, description="Whether contact is publicly listed")
    contact_preferences: Optional[Dict[str, Any]] = None

class BoardConnection(BaseModel):
    """Network connection between organizations through board members"""
    source_ein: str = Field(..., description="Source organization EIN")
    target_ein: str = Field(..., description="Target organization EIN")
    connection_person: str = Field(..., description="Person creating connection (match_key)")
    
    # Connection strength
    connection_strength: float = Field(1.0, ge=0.0, le=1.0, description="Strength of connection")
    connection_type: str = Field("board_overlap", description="Type of connection")
    
    # Temporal information
    connection_start: Optional[date] = None
    connection_end: Optional[date] = None
    is_current: bool = Field(True, description="Whether connection is current")
    
    # Source tracking
    data_source: DataSource = Field(..., description="Source of connection data")
    discovered_at: datetime = Field(default_factory=datetime.now)


# =====================================================================================
# TRANSFORMATION RESULT MODELS
# =====================================================================================

class ValidationError(BaseModel):
    """Individual validation error"""
    field: str = Field(..., description="Field with error")
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    severity: Literal["warning", "error", "critical"] = Field("error")
    
class DuplicationMatch(BaseModel):
    """Duplicate record match information"""
    match_type: str = Field(..., description="Type of match (exact, fuzzy, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Match confidence")
    matched_record: str = Field(..., description="ID of matched record")
    conflicting_fields: List[str] = Field(default_factory=list, description="Fields with conflicts")
    
class TransformationStats(BaseModel):
    """Statistics from transformation process"""
    total_records_processed: int = 0
    successful_transformations: int = 0
    validation_errors: int = 0
    duplicates_found: int = 0
    duplicates_merged: int = 0
    data_quality_score: float = 0.0
    processing_time_seconds: float = 0.0
    
    # Detailed counts by type
    people_processed: int = 0
    roles_created: int = 0
    programs_processed: int = 0
    contacts_processed: int = 0
    connections_discovered: int = 0

class TransformationResult(BaseModel):
    """Complete transformation result"""
    success: bool = Field(..., description="Whether transformation succeeded")
    
    # Transformed data
    people: List[Person] = Field(default_factory=list)
    roles: List[OrganizationRole] = Field(default_factory=list)
    programs: List[Program] = Field(default_factory=list)
    contacts: List[Contact] = Field(default_factory=list)
    connections: List[BoardConnection] = Field(default_factory=list)
    
    # Quality and validation
    validation_errors: List[ValidationError] = Field(default_factory=list)
    duplicate_matches: List[DuplicationMatch] = Field(default_factory=list)
    statistics: TransformationStats = Field(default_factory=TransformationStats)
    
    # Processing metadata
    transformation_id: str = Field(..., description="Unique transformation ID")
    profile_id: str = Field(..., description="Associated profile ID")
    processed_at: datetime = Field(default_factory=datetime.now)
    processing_version: str = Field("1.0.0", description="Transformation engine version")
    
    # Source data fingerprint for change detection
    source_data_hash: Optional[str] = Field(None, description="Hash of source data")
    

# =====================================================================================
# CONFIGURATION AND SETTINGS MODELS
# =====================================================================================

class NameParsingConfig(BaseModel):
    """Configuration for name parsing"""
    strip_titles: bool = Field(True, description="Remove titles from normalized names")
    strip_suffixes: bool = Field(True, description="Remove suffixes from normalized names")
    handle_nicknames: bool = Field(True, description="Attempt to handle nickname matching")
    min_name_length: int = Field(2, description="Minimum length for valid names")

class DeduplicationConfig(BaseModel):
    """Configuration for deduplication logic"""
    fuzzy_match_threshold: float = Field(0.85, ge=0.0, le=1.0, description="Fuzzy match threshold")
    exact_match_required_fields: List[str] = Field(
        default=["normalized_name"], 
        description="Fields requiring exact match"
    )
    merge_strategy: Literal["newest", "highest_quality", "manual"] = Field(
        "highest_quality", 
        description="Strategy for merging duplicates"
    )
    
class ValidationConfig(BaseModel):
    """Configuration for data validation"""
    strict_email_validation: bool = Field(True, description="Strict email format validation")
    phone_number_formats: List[str] = Field(
        default=["US"], 
        description="Accepted phone number formats"
    )
    require_names: bool = Field(True, description="Require valid names for people")
    min_quality_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum quality score")

class TransformationConfig(BaseModel):
    """Complete transformation configuration"""
    name_parsing: NameParsingConfig = Field(default_factory=NameParsingConfig)
    deduplication: DeduplicationConfig = Field(default_factory=DeduplicationConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    
    # Processing options
    enable_fuzzy_matching: bool = Field(True, description="Enable fuzzy matching for deduplication")
    preserve_all_sources: bool = Field(True, description="Preserve all source attributions")
    auto_merge_duplicates: bool = Field(False, description="Automatically merge obvious duplicates")
    
    # Performance settings
    batch_size: int = Field(100, ge=1, description="Processing batch size")
    max_processing_time: int = Field(300, ge=30, description="Maximum processing time in seconds")
