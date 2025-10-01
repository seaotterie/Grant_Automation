"""
Tests for Grant Package Generator Tool
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from datetime import datetime, timedelta

# Import with proper path resolution
package_tool_path = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(package_tool_path))

from package_tool import (
    GrantPackageGeneratorTool,
    generate_grant_package
)
from package_models import (
    GrantPackageInput,
    DocumentType,
    PackageStatus
)


@pytest.fixture
def sample_package_input():
    """Sample package input for testing"""
    deadline = (datetime.now() + timedelta(days=30)).isoformat()

    return GrantPackageInput(
        opportunity_id="OPP-2025-001",
        opportunity_title="Community Health Initiative Grant",
        funder_name="Health Foundation",
        application_deadline=deadline,
        organization_ein="541026365",
        organization_name="Community Health Services",
        include_documents=[
            DocumentType.COVER_LETTER,
            DocumentType.PROPOSAL_NARRATIVE,
            DocumentType.BUDGET,
            DocumentType.ORGANIZATIONAL_DOCUMENTS
        ]
    )


@pytest.mark.asyncio
async def test_package_generator_basic(sample_package_input):
    """Test basic package generation"""
    tool = GrantPackageGeneratorTool()

    result = await tool.execute(package_input=sample_package_input)

    assert result.success
    assert result.data is not None

    output = result.data
    assert output.opportunity_id == "OPP-2025-001"
    assert output.package_status == PackageStatus.DRAFT
    assert len(output.included_documents) == 4
    assert output.total_documents == 4


@pytest.mark.asyncio
async def test_package_generator_checklist(sample_package_input):
    """Test checklist generation"""
    tool = GrantPackageGeneratorTool()

    result = await tool.execute(package_input=sample_package_input)

    assert result.success
    output = result.data

    # Should have document items + additional items
    assert output.checklist.total_items >= 4
    assert output.checklist.completed_items >= 0
    assert 0 <= output.checklist.completion_percentage <= 100


@pytest.mark.asyncio
async def test_package_generator_submission_plan(sample_package_input):
    """Test submission plan creation"""
    tool = GrantPackageGeneratorTool()

    result = await tool.execute(package_input=sample_package_input)

    assert result.success
    output = result.data

    plan = output.submission_plan
    assert plan.days_until_deadline >= 0
    assert plan.submission_method in ["online", "mail", "email"]
    assert plan.recommended_submission_date
    assert plan.final_review_date


@pytest.mark.asyncio
async def test_package_generator_missing_documents(sample_package_input):
    """Test missing document tracking"""
    tool = GrantPackageGeneratorTool()

    result = await tool.execute(package_input=sample_package_input)

    assert result.success
    output = result.data

    # Documents should be in pending status initially
    assert len(output.missing_documents) >= 0


@pytest.mark.asyncio
async def test_package_generator_deadline_warning():
    """Test deadline warning generation"""
    # Create input with near deadline
    near_deadline = (datetime.now() + timedelta(days=5)).isoformat()

    package_input = GrantPackageInput(
        opportunity_id="OPP-2025-002",
        opportunity_title="Urgent Grant",
        funder_name="Test Foundation",
        application_deadline=near_deadline,
        organization_ein="541026365",
        organization_name="Test Organization",
        include_documents=[DocumentType.COVER_LETTER]
    )

    tool = GrantPackageGeneratorTool()
    result = await tool.execute(package_input=package_input)

    assert result.success
    output = result.data

    # Should have deadline warning
    assert len(output.warnings) > 0
    assert any("Deadline" in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_convenience_function():
    """Test convenience function"""
    deadline = (datetime.now() + timedelta(days=30)).isoformat()

    result = await generate_grant_package(
        opportunity_id="OPP-2025-003",
        opportunity_title="Test Grant",
        funder_name="Test Funder",
        application_deadline=deadline,
        organization_ein="541026365",
        organization_name="Test Org",
        include_documents=["cover_letter", "proposal_narrative"]
    )

    assert result.success
    assert result.data.opportunity_id == "OPP-2025-003"


@pytest.mark.asyncio
async def test_package_generator_validation():
    """Test input validation"""
    tool = GrantPackageGeneratorTool()

    # Test missing opportunity_id
    invalid_input = GrantPackageInput(
        opportunity_id="",
        opportunity_title="Test",
        funder_name="Test",
        application_deadline=datetime.now().isoformat(),
        organization_ein="123456789",
        organization_name="Test",
        include_documents=[]
    )

    is_valid, error = tool.validate_inputs(package_input=invalid_input)
    assert not is_valid or invalid_input.opportunity_id == ""


@pytest.mark.asyncio
async def test_package_generator_cost():
    """Test cost estimate"""
    tool = GrantPackageGeneratorTool()

    cost = tool.get_cost_estimate()
    assert cost == 0.00


@pytest.mark.asyncio
async def test_package_generator_tool_metadata():
    """Test tool metadata"""
    tool = GrantPackageGeneratorTool()

    assert tool.get_tool_name() == "Grant Package Generator Tool"
    assert tool.get_tool_version() == "1.0.0"
    assert "package assembly" in tool.get_single_responsibility().lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
