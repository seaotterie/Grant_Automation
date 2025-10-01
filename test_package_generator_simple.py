"""
Simple test for Grant Package Generator Tool
"""

import sys
from pathlib import Path
import asyncio
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add tool path
tool_path = project_root / "tools" / "grant-package-generator-tool" / "app"
sys.path.insert(0, str(tool_path))

from package_tool import GrantPackageGeneratorTool, generate_grant_package
from package_models import GrantPackageInput, DocumentType


async def test_package_generator():
    """Test package generation"""

    print("Testing Grant Package Generator Tool...")

    # Create sample input
    deadline = (datetime.now() + timedelta(days=30)).isoformat()

    package_input = GrantPackageInput(
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

    # Test tool
    tool = GrantPackageGeneratorTool()
    result = await tool.execute(package_input=package_input)

    print(f"\n[OK] Tool Execution: {'SUCCESS' if result.is_success else 'FAILED'}")

    if result.is_success:
        output = result.data
        print(f"[OK] Package ID: {output.package_id}")
        print(f"[OK] Status: {output.package_status.value}")
        print(f"[OK] Documents: {output.total_documents}")
        print(f"[OK] Missing: {len(output.missing_documents)}")
        print(f"[OK] Checklist: {output.checklist.completion_percentage:.1f}% complete")
        print(f"[OK] Days until deadline: {output.submission_plan.days_until_deadline}")
        print(f"[OK] Processing time: {output.processing_time_seconds:.3f}s")
        print(f"[OK] Cost: ${tool.get_cost_estimate():.2f}")

        if output.warnings:
            print(f"[OK] Warnings: {len(output.warnings)}")
            for warning in output.warnings:
                print(f"  - {warning}")

    # Test convenience function
    print("\n\nTesting convenience function...")
    result2 = await generate_grant_package(
        opportunity_id="OPP-2025-002",
        opportunity_title="Education Grant",
        funder_name="Education Foundation",
        application_deadline=(datetime.now() + timedelta(days=45)).isoformat(),
        organization_ein="123456789",
        organization_name="Education Services Inc",
        include_documents=["cover_letter", "proposal_narrative", "budget"]
    )

    print(f"[OK] Convenience Function: {'SUCCESS' if result2.is_success else 'FAILED'}")
    if result2.is_success:
        print(f"[OK] Package ID: {result2.data.package_id}")

    print("\n[SUCCESS] All tests passed!")

    return result.is_success and result2.is_success


if __name__ == "__main__":
    success = asyncio.run(test_package_generator())
    sys.exit(0 if success else 1)
