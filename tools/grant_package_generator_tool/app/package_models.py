"""
Grant Package Generator Tool Data Models
Application package assembly and coordination
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class PackageStatus(str, Enum):
    """Package generation status"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    READY_FOR_REVIEW = "ready_for_review"
    COMPLETE = "complete"
    SUBMITTED = "submitted"


class DocumentType(str, Enum):
    """Document types in package"""
    COVER_LETTER = "cover_letter"
    PROPOSAL_NARRATIVE = "proposal_narrative"
    BUDGET = "budget"
    BUDGET_NARRATIVE = "budget_narrative"
    ORGANIZATIONAL_DOCUMENTS = "organizational_documents"
    FINANCIAL_STATEMENTS = "financial_statements"
    LETTERS_OF_SUPPORT = "letters_of_support"
    ADDITIONAL_MATERIALS = "additional_materials"


@dataclass
class GrantPackageInput:
    """Input for grant package generation"""

    # Opportunity information
    opportunity_id: str
    opportunity_title: str
    funder_name: str
    application_deadline: str

    # Organization information
    organization_ein: str
    organization_name: str

    # Package configuration
    include_documents: List[DocumentType]

    # Intelligence data (from prior analysis)
    intelligence_data: Optional[Dict[str, Any]] = None

    # Custom content
    custom_sections: Optional[Dict[str, str]] = None


@dataclass
class PackageDocument:
    """Individual document in package"""

    document_type: DocumentType
    document_name: str
    file_path: Optional[str] = None
    status: str = "pending"  # pending, complete, missing
    required: bool = True
    notes: Optional[str] = None


@dataclass
class PackageChecklist:
    """Package completion checklist"""

    checklist_items: List[Dict[str, Any]]
    completed_items: int
    total_items: int
    completion_percentage: float


@dataclass
class SubmissionPlan:
    """Plan for grant submission"""

    submission_method: str  # online, mail, email
    submission_deadline: str
    submission_instructions: str
    days_until_deadline: int
    recommended_submission_date: str
    final_review_date: str


@dataclass
class GrantPackageOutput:
    """Complete grant package output"""

    # Package information
    package_id: str
    opportunity_id: str
    opportunity_title: str
    funder_name: str

    # Package status
    package_status: PackageStatus
    package_directory: str

    # Documents
    included_documents: List[PackageDocument]
    missing_documents: List[str]

    # Completion tracking
    checklist: PackageChecklist

    # Submission planning
    submission_plan: SubmissionPlan

    # Package metadata
    created_date: str
    last_updated: str
    total_documents: int
    ready_for_submission: bool

    # Processing info
    processing_time_seconds: float
    warnings: List[str] = field(default_factory=list)


# Cost configuration
GRANT_PACKAGE_GENERATOR_COST = 0.00  # No AI calls
