"""
Report Generator Tool Data Models
Professional report generation with structured outputs
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class ReportTemplate(str, Enum):
    """Report template types"""
    COMPREHENSIVE = "comprehensive"
    EXECUTIVE = "executive"
    RISK = "risk"
    IMPLEMENTATION = "implementation"


class OutputFormat(str, Enum):
    """Output format types"""
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"


class SectionType(str, Enum):
    """Report section content types"""
    TEXT = "text"
    TABLE = "table"
    CHART = "chart"
    MATRIX = "matrix"
    LIST = "list"


@dataclass
class ReportInput:
    """Input for report generation"""

    # Required fields
    template_type: ReportTemplate
    opportunity_data: Dict[str, Any]
    organization_data: Dict[str, Any]

    # Optional analysis results
    scoring_results: Optional[List[Dict[str, Any]]] = None  # Multi-dimensional scores
    intelligence_data: Optional[Dict[str, Any]] = None  # Deep intelligence output
    financial_data: Optional[Dict[str, Any]] = None  # Financial intelligence
    network_data: Optional[Dict[str, Any]] = None  # Network intelligence
    risk_data: Optional[Dict[str, Any]] = None  # Risk assessment

    # Output configuration
    output_format: OutputFormat = OutputFormat.HTML
    output_path: Optional[str] = None

    # Customization
    include_sections: Optional[List[str]] = None  # Override default sections
    custom_title: Optional[str] = None
    custom_subtitle: Optional[str] = None


@dataclass
class ReportSection:
    """Individual report section"""

    section_id: str
    section_title: str
    content_type: SectionType
    content: str  # HTML, markdown, or JSON string
    data_sources: List[str] = field(default_factory=list)
    subsections: List['ReportSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportMetadata:
    """Metadata about report generation"""

    generation_timestamp: str
    template_used: str
    output_format: str
    sections_count: int
    total_pages_estimated: int
    data_sources_used: List[str]
    generation_time_seconds: float

    # Quality metrics
    completeness_score: float  # 0.0-1.0
    data_quality_score: float  # 0.0-1.0


@dataclass
class ReportOutput:
    """Complete report generation output"""

    # Report identification
    report_id: str
    template_used: str
    file_path: str
    format: str

    # Sections generated
    sections_generated: List[ReportSection]

    # File metrics
    generation_time_seconds: float
    file_size_bytes: int

    # Metadata
    metadata: ReportMetadata

    # Optional summary
    executive_summary: Optional[str] = None
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# Template section configurations

COMPREHENSIVE_SECTIONS = [
    "executive_summary",
    "opportunity_overview",
    "organization_analysis",
    "grantor_intelligence",
    "strategic_fit",
    "opportunity_deep_dive",
    "funding_history",
    "strategic_approach",
    "network_intelligence",
    "scoring_analysis",
    "winning_strategy",
    "discover_tab",
    "plan_tab",
    "analyze_tab",
    "examine_tab",
    "approach_tab",
    "tier_analysis",
    "system_architecture",
    "data_sources",
    "quality_assurance"
]

EXECUTIVE_SECTIONS = [
    "executive_summary",
    "key_findings",
    "strategic_recommendation",
    "risk_summary",
    "next_steps"
]

RISK_SECTIONS = [
    "executive_summary",
    "risk_assessment_matrix",
    "risk_breakdown",
    "mitigation_strategies",
    "probability_analysis",
    "impact_analysis",
    "recommendations"
]

IMPLEMENTATION_SECTIONS = [
    "executive_summary",
    "implementation_timeline",
    "resource_requirements",
    "key_milestones",
    "success_metrics",
    "risk_mitigation",
    "action_plan"
]

TEMPLATE_SECTIONS = {
    ReportTemplate.COMPREHENSIVE: COMPREHENSIVE_SECTIONS,
    ReportTemplate.EXECUTIVE: EXECUTIVE_SECTIONS,
    ReportTemplate.RISK: RISK_SECTIONS,
    ReportTemplate.IMPLEMENTATION: IMPLEMENTATION_SECTIONS
}

# Cost configuration
REPORT_GENERATOR_COST = 0.00  # No AI calls - template-based
