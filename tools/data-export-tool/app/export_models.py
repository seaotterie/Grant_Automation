"""
Data Export Tool Data Models
Multi-format export with professional templates
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class ExportFormat(str, Enum):
    """Export format types"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


class ExportTemplate(str, Enum):
    """Export template styles"""
    EXECUTIVE = "executive"
    DETAILED = "detailed"
    TECHNICAL = "technical"
    SUMMARY = "summary"
    CUSTOM = "custom"


@dataclass
class DataExportInput:
    """Input for data export"""

    # Data to export
    data: Dict[str, Any]

    # Export configuration
    export_format: ExportFormat
    template: ExportTemplate = ExportTemplate.DETAILED

    # Output configuration
    output_filename: str = "export"
    include_metadata: bool = True
    include_charts: bool = False

    # Template customization
    title: Optional[str] = None
    subtitle: Optional[str] = None
    organization_name: Optional[str] = None
    custom_sections: Optional[List[Dict[str, Any]]] = None


@dataclass
class ExportMetadata:
    """Export metadata"""

    export_date: str
    export_format: str
    template_used: str
    record_count: int
    file_size_bytes: Optional[int] = None
    generator: str = "Catalynx Data Export Tool"


@dataclass
class ExportSection:
    """Individual export section"""

    section_name: str
    section_data: Dict[str, Any]
    include_in_export: bool = True
    page_break_before: bool = False


@dataclass
class DataExportOutput:
    """Complete data export output"""

    # Export success
    export_successful: bool

    # Output file information
    output_filepath: str
    output_format: ExportFormat

    # Export metadata
    metadata: ExportMetadata

    # Export statistics
    records_exported: int
    sections_included: List[str]

    # File information
    file_size_bytes: int
    download_url: Optional[str] = None

    # Processing info
    processing_time_seconds: float
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


# Cost configuration (no AI calls, so free)
DATA_EXPORT_COST = 0.00
