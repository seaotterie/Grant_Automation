"""
Data Export Tool
12-Factor compliant tool for multi-format data export.

Purpose: Export intelligence data to multiple formats
Cost: $0.00 per export (no AI calls)
Replaces: export_processor.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Optional
import time
from datetime import datetime
import json
import csv
from io import StringIO

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext
from .export_models import (
    DataExportInput,
    DataExportOutput,
    ExportFormat,
    ExportTemplate,
    ExportMetadata,
    ExportSection,
    DATA_EXPORT_COST
)


class DataExportTool(BaseTool[DataExportOutput]):
    """
    12-Factor Data Export Tool

    Factor 4: Returns structured DataExportOutput
    Factor 6: Stateless - no persistence between runs
    Factor 10: Single responsibility - data export only
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize data export tool."""
        super().__init__(config)
        self.output_directory = config.get("output_directory", "exports") if config else "exports"

    def get_tool_name(self) -> str:
        return "Data Export Tool"

    def get_tool_version(self) -> str:
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        return "Multi-format data export with professional templates"

    async def _execute(
        self,
        context: ToolExecutionContext,
        export_input: DataExportInput
    ) -> DataExportOutput:
        """Execute data export."""
        start_time = time.time()

        self.logger.info(
            f"Starting data export: format={export_input.export_format.value}, "
            f"template={export_input.template.value}"
        )

        warnings = []
        errors = []

        try:
            # Route to appropriate export handler
            if export_input.export_format == ExportFormat.JSON:
                output_filepath, file_size = self._export_json(export_input)
            elif export_input.export_format == ExportFormat.CSV:
                output_filepath, file_size = self._export_csv(export_input)
            elif export_input.export_format == ExportFormat.EXCEL:
                output_filepath, file_size = self._export_excel(export_input)
            elif export_input.export_format == ExportFormat.PDF:
                output_filepath, file_size = self._export_pdf(export_input)
            elif export_input.export_format == ExportFormat.HTML:
                output_filepath, file_size = self._export_html(export_input)
            else:
                raise ValueError(f"Unsupported export format: {export_input.export_format}")

            export_successful = True

        except Exception as e:
            self.logger.error(f"Export failed: {str(e)}")
            errors.append(str(e))
            export_successful = False
            output_filepath = ""
            file_size = 0

        # Create metadata
        metadata = ExportMetadata(
            export_date=datetime.now().isoformat(),
            export_format=export_input.export_format.value,
            template_used=export_input.template.value,
            record_count=self._count_records(export_input.data),
            file_size_bytes=file_size
        )

        # Determine sections
        sections = list(export_input.data.keys()) if isinstance(export_input.data, dict) else ["data"]

        processing_time = time.time() - start_time

        output = DataExportOutput(
            export_successful=export_successful,
            output_filepath=output_filepath,
            output_format=export_input.export_format,
            metadata=metadata,
            records_exported=metadata.record_count,
            sections_included=sections,
            file_size_bytes=file_size,
            processing_time_seconds=processing_time,
            warnings=warnings,
            errors=errors
        )

        self.logger.info(
            f"Completed export: successful={export_successful}, "
            f"file_size={file_size} bytes, time={processing_time:.2f}s"
        )

        return output

    def _export_json(self, export_input: DataExportInput) -> tuple[str, int]:
        """Export to JSON format"""

        # Create export data structure
        export_data = {
            "metadata": {
                "title": export_input.title or "Data Export",
                "organization": export_input.organization_name,
                "export_date": datetime.now().isoformat(),
                "template": export_input.template.value
            },
            "data": export_input.data
        }

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{export_input.output_filename}_{timestamp}.json"
        filepath = Path(self.output_directory) / filename

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON
        json_str = json.dumps(export_data, indent=2, default=str)
        filepath.write_text(json_str)

        file_size = len(json_str.encode('utf-8'))

        return str(filepath), file_size

    def _export_csv(self, export_input: DataExportInput) -> tuple[str, int]:
        """Export to CSV format"""

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{export_input.output_filename}_{timestamp}.csv"
        filepath = Path(self.output_directory) / filename

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Convert data to CSV
        output = StringIO()

        # Flatten data if nested
        flat_data = self._flatten_data(export_input.data)

        if flat_data:
            # Get headers
            headers = list(flat_data[0].keys()) if isinstance(flat_data[0], dict) else []

            if headers:
                writer = csv.DictWriter(output, fieldnames=headers)
                writer.writeheader()
                writer.writerows(flat_data)
            else:
                # Simple list
                writer = csv.writer(output)
                for row in flat_data:
                    writer.writerow([row] if not isinstance(row, (list, tuple)) else row)

        csv_str = output.getvalue()
        filepath.write_text(csv_str)

        file_size = len(csv_str.encode('utf-8'))

        return str(filepath), file_size

    def _export_excel(self, export_input: DataExportInput) -> tuple[str, int]:
        """Export to Excel format"""

        # Note: Would use openpyxl or xlsxwriter in production
        # For now, export as CSV with .xlsx extension (placeholder)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{export_input.output_filename}_{timestamp}.xlsx"
        filepath = Path(self.output_directory) / filename

        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Placeholder: Export as CSV-like format
        content = "Excel export would be generated here using openpyxl\n"
        content += f"Data: {json.dumps(export_input.data, default=str)}\n"

        filepath.write_text(content)
        file_size = len(content.encode('utf-8'))

        return str(filepath), file_size

    def _export_pdf(self, export_input: DataExportInput) -> tuple[str, int]:
        """Export to PDF format"""

        # Note: Would use reportlab or weasyprint in production

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{export_input.output_filename}_{timestamp}.pdf"
        filepath = Path(self.output_directory) / filename

        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Placeholder: Generate HTML-like content that would be converted to PDF
        html_content = self._generate_html_content(export_input)
        content = f"PDF would be generated from HTML using reportlab\n\n{html_content}"

        filepath.write_text(content)
        file_size = len(content.encode('utf-8'))

        return str(filepath), file_size

    def _export_html(self, export_input: DataExportInput) -> tuple[str, int]:
        """Export to HTML format"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{export_input.output_filename}_{timestamp}.html"
        filepath = Path(self.output_directory) / filename

        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Generate HTML
        html_content = self._generate_html_content(export_input)

        filepath.write_text(html_content)
        file_size = len(html_content.encode('utf-8'))

        return str(filepath), file_size

    def _generate_html_content(self, export_input: DataExportInput) -> str:
        """Generate HTML content from data"""

        title = export_input.title or "Data Export"
        org_name = export_input.organization_name or ""

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        .metadata {{ color: #888; font-size: 0.9em; margin-bottom: 30px; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="metadata">
        {f'<p><strong>Organization:</strong> {org_name}</p>' if org_name else ''}
        <p><strong>Export Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Template:</strong> {export_input.template.value.title()}</p>
    </div>
"""

        # Add data sections
        if isinstance(export_input.data, dict):
            for section_name, section_data in export_input.data.items():
                html += f"    <h2>{section_name.replace('_', ' ').title()}</h2>\n"
                html += self._format_data_as_html(section_data)
        else:
            html += self._format_data_as_html(export_input.data)

        html += """
</body>
</html>
"""

        return html

    def _format_data_as_html(self, data: any) -> str:
        """Format data as HTML table or list"""

        if isinstance(data, list) and data and isinstance(data[0], dict):
            # Table format
            headers = list(data[0].keys())
            html = "    <table>\n"
            html += "        <tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>\n"
            for row in data:
                html += "        <tr>" + "".join(f"<td>{row.get(h, '')}</td>" for h in headers) + "</tr>\n"
            html += "    </table>\n"
            return html
        elif isinstance(data, dict):
            # Key-value list
            html = "    <table>\n"
            for key, value in data.items():
                html += f"        <tr><th>{key}</th><td>{value}</td></tr>\n"
            html += "    </table>\n"
            return html
        else:
            # Simple paragraph
            return f"    <p>{data}</p>\n"

    def _flatten_data(self, data: any) -> list:
        """Flatten nested data structures for CSV export"""

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Convert dict to list of dicts
            return [data]
        else:
            return [{"value": data}]

    def _count_records(self, data: any) -> int:
        """Count number of records in data"""

        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            # Count total items in all values
            return sum(len(v) if isinstance(v, list) else 1 for v in data.values())
        else:
            return 1

    def get_cost_estimate(self) -> Optional[float]:
        return DATA_EXPORT_COST

    def validate_inputs(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate tool inputs."""
        export_input = kwargs.get("export_input")

        if not export_input:
            return False, "export_input is required"

        if not isinstance(export_input, DataExportInput):
            return False, "export_input must be DataExportInput instance"

        if not export_input.data:
            return False, "data is required for export"

        return True, None


# Convenience function
async def export_data(
    data: dict,
    export_format: str = "json",
    output_filename: str = "export",
    template: str = "detailed",
    title: Optional[str] = None,
    organization_name: Optional[str] = None,
    include_metadata: bool = True,
    config: Optional[dict] = None
) -> ToolResult[DataExportOutput]:
    """Export data to specified format."""

    tool = DataExportTool(config)

    export_input = DataExportInput(
        data=data,
        export_format=ExportFormat(export_format),
        template=ExportTemplate(template),
        output_filename=output_filename,
        title=title,
        organization_name=organization_name,
        include_metadata=include_metadata
    )

    return await tool.execute(export_input=export_input)
