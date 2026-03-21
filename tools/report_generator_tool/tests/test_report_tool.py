"""
Tests for Report Generator Tool
"""

import pytest
import tempfile
from pathlib import Path
from app.report_tool import (
    ReportGeneratorTool,
    generate_report,
    REPORT_GENERATOR_COST,
)
from app.report_models import ReportTemplate, OutputFormat


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def opportunity_data():
    return {
        "title": "Community Education Enhancement Grant",
        "funder_name": "Department of Education",
        "funding_amount": 250_000,
        "description": "Federal funding for innovative community education programs",
        "application_deadline": "2026-06-30",
        "focus_areas": ["education", "community", "literacy"],
        "geographic_scope": "National",
    }


@pytest.fixture
def organization_data():
    return {
        "organization_name": "Education First Foundation",
        "ein": "12-3456789",
        "mission": "Supporting educational equity in underserved communities",
        "revenue": 2_000_000,
        "state": "VA",
        "ntee_codes": ["B25"],
        "years_active": 12,
    }


@pytest.fixture
def tmp_report_dir(tmp_path):
    """Temporary directory for report output to avoid polluting the repo."""
    return str(tmp_path)


# ---------------------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------------------

def test_tool_metadata():
    tool = ReportGeneratorTool()
    assert tool.get_tool_name() == "Report Generator Tool"
    assert tool.get_tool_version() == "1.0.0"
    assert "report" in tool.get_single_responsibility().lower()


def test_cost_is_zero():
    assert REPORT_GENERATOR_COST == 0.0
    assert ReportGeneratorTool().get_cost_estimate() == 0.0


# ---------------------------------------------------------------------------
# Core generation tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("template", [t.value for t in ReportTemplate])
async def test_all_templates_succeed(template, opportunity_data, organization_data, tmp_report_dir):
    result = await generate_report(
        template_type=template,
        opportunity_data=opportunity_data,
        organization_data=organization_data,
        config={"output_dir": tmp_report_dir},
    )
    assert result.is_success(), f"Template {template} failed: {result.errors}"
    report = result.data
    assert report.report_id
    assert report.template_used == template
    assert len(report.sections_generated) > 0


@pytest.mark.asyncio
@pytest.mark.parametrize("fmt", [OutputFormat.HTML.value, OutputFormat.MARKDOWN.value])
async def test_output_formats(fmt, opportunity_data, organization_data, tmp_report_dir):
    result = await generate_report(
        template_type="executive",
        opportunity_data=opportunity_data,
        organization_data=organization_data,
        output_format=fmt,
        config={"output_dir": tmp_report_dir},
    )
    assert result.is_success(), f"Format {fmt} failed: {result.errors}"
    assert result.data.format == fmt


@pytest.mark.asyncio
async def test_html_report_contains_org_name(opportunity_data, organization_data, tmp_report_dir):
    result = await generate_report(
        template_type="comprehensive",
        opportunity_data=opportunity_data,
        organization_data=organization_data,
        output_format="html",
        config={"output_dir": tmp_report_dir},
    )
    assert result.is_success()
    report = result.data
    # At least one section should contain the org name
    all_content = " ".join(s.content for s in report.sections_generated)
    assert "Education First Foundation" in all_content


@pytest.mark.asyncio
async def test_report_with_optional_data(opportunity_data, organization_data, tmp_report_dir):
    result = await generate_report(
        template_type="comprehensive",
        opportunity_data=opportunity_data,
        organization_data=organization_data,
        scoring_results=[{"stage": "plan", "overall_score": 0.82, "confidence": 0.75}],
        financial_data={"total_revenue": 2_000_000, "program_expense_ratio": 0.82},
        risk_data={"overall_risk": "low", "go_no_go": "go"},
        config={"output_dir": tmp_report_dir},
    )
    assert result.is_success()


# ---------------------------------------------------------------------------
# Output file tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_report_file_created(opportunity_data, organization_data, tmp_report_dir):
    result = await generate_report(
        template_type="executive",
        opportunity_data=opportunity_data,
        organization_data=organization_data,
        config={"output_dir": tmp_report_dir},
    )
    assert result.is_success()
    assert Path(result.data.file_path).exists()
    assert result.data.file_size_bytes > 0


@pytest.mark.asyncio
async def test_custom_output_path(opportunity_data, organization_data, tmp_path):
    output_file = str(tmp_path / "custom_report.html")
    result = await generate_report(
        template_type="executive",
        opportunity_data=opportunity_data,
        organization_data=organization_data,
        config={"output_dir": str(tmp_path)},
    )
    assert result.is_success()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_template_raises():
    with pytest.raises(ValueError):
        await generate_report(
            template_type="nonexistent_template",
            opportunity_data={},
            organization_data={},
        )


@pytest.mark.asyncio
async def test_minimal_data(tmp_report_dir):
    """Tool should not crash with minimal data."""
    result = await generate_report(
        template_type="executive",
        opportunity_data={"title": "Grant"},
        organization_data={"organization_name": "Org"},
        config={"output_dir": tmp_report_dir},
    )
    assert result.is_success()


@pytest.mark.asyncio
async def test_metadata_populated(opportunity_data, organization_data, tmp_report_dir):
    result = await generate_report(
        template_type="executive",
        opportunity_data=opportunity_data,
        organization_data=organization_data,
        config={"output_dir": tmp_report_dir},
    )
    assert result.is_success()
    meta = result.data.metadata
    assert meta.tool_version == "1.0.0"
    assert result.data.generation_time_seconds >= 0
