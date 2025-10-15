"""
Grant Package Generator Tool
12-Factor compliant tool for application package assembly.

Purpose: Coordinate and assemble grant application packages
Cost: $0.00 per package (no AI calls)
Replaces: grant_package_generator.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Optional, List
import time
from datetime import datetime, timedelta
import uuid

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext

try:
    from .package_models import (
        GrantPackageInput,
        GrantPackageOutput,
        PackageStatus,
        DocumentType,
        PackageDocument,
        PackageChecklist,
        SubmissionPlan,
        GRANT_PACKAGE_GENERATOR_COST
    )
except ImportError:
    from package_models import (
        GrantPackageInput,
        GrantPackageOutput,
        PackageStatus,
        DocumentType,
        PackageDocument,
        PackageChecklist,
        SubmissionPlan,
        GRANT_PACKAGE_GENERATOR_COST
    )


class GrantPackageGeneratorTool(BaseTool[GrantPackageOutput]):
    """
    12-Factor Grant Package Generator Tool

    Factor 4: Returns structured GrantPackageOutput
    Factor 6: Stateless - no persistence between runs
    Factor 10: Single responsibility - package assembly only
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize grant package generator tool."""
        super().__init__(config)
        self.packages_directory = config.get("packages_directory", "grant_packages") if config else "grant_packages"

    def get_tool_name(self) -> str:
        return "Grant Package Generator Tool"

    def get_tool_version(self) -> str:
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        return "Grant application package assembly and coordination"

    async def _execute(
        self,
        context: ToolExecutionContext,
        package_input: GrantPackageInput
    ) -> GrantPackageOutput:
        """Execute grant package generation."""
        start_time = time.time()

        self.logger.info(
            f"Starting grant package generation: {package_input.opportunity_title} "
            f"for {package_input.organization_name}"
        )

        warnings = []

        # Generate unique package ID
        package_id = f"pkg_{uuid.uuid4().hex[:8]}"

        # Create package directory
        package_dir = Path(self.packages_directory) / package_id
        package_dir.mkdir(parents=True, exist_ok=True)

        # Process documents
        documents = self._initialize_documents(package_input, package_dir)

        # Identify missing documents
        missing = [
            doc.document_name for doc in documents
            if doc.status == "missing" and doc.required
        ]

        # Create checklist
        checklist = self._create_checklist(package_input, documents)

        # Create submission plan
        submission_plan = self._create_submission_plan(package_input)

        # Determine package status
        if len(missing) == 0:
            package_status = PackageStatus.READY_FOR_REVIEW
            ready_for_submission = checklist.completion_percentage >= 90.0
        elif checklist.completion_percentage >= 50:
            package_status = PackageStatus.IN_PROGRESS
            ready_for_submission = False
        else:
            package_status = PackageStatus.DRAFT
            ready_for_submission = False

        # Check for warnings
        if submission_plan.days_until_deadline < 7:
            warnings.append(f"Deadline in {submission_plan.days_until_deadline} days - immediate action required")
        if len(missing) > 0:
            warnings.append(f"{len(missing)} required documents missing")

        processing_time = time.time() - start_time
        now = datetime.now().isoformat()

        output = GrantPackageOutput(
            package_id=package_id,
            opportunity_id=package_input.opportunity_id,
            opportunity_title=package_input.opportunity_title,
            funder_name=package_input.funder_name,
            package_status=package_status,
            package_directory=str(package_dir),
            included_documents=documents,
            missing_documents=missing,
            checklist=checklist,
            submission_plan=submission_plan,
            created_date=now,
            last_updated=now,
            total_documents=len(documents),
            ready_for_submission=ready_for_submission,
            processing_time_seconds=processing_time,
            warnings=warnings
        )

        self.logger.info(
            f"Completed package generation: status={package_status.value}, "
            f"documents={len(documents)}, missing={len(missing)}"
        )

        return output

    def _initialize_documents(
        self,
        package_input: GrantPackageInput,
        package_dir: Path
    ) -> List[PackageDocument]:
        """Initialize document list"""

        documents = []

        for doc_type in package_input.include_documents:
            # Determine document name
            doc_name = self._get_document_name(doc_type, package_input)

            # Check if document exists (placeholder - would check actual files)
            file_path = package_dir / doc_name
            status = "pending"  # Would check if file exists

            documents.append(PackageDocument(
                document_type=doc_type,
                document_name=doc_name,
                file_path=str(file_path),
                status=status,
                required=self._is_required_document(doc_type),
                notes=self._get_document_notes(doc_type)
            ))

        return documents

    def _get_document_name(self, doc_type: DocumentType, package_input: GrantPackageInput) -> str:
        """Get appropriate document name"""

        org_name = package_input.organization_name.replace(" ", "_")
        opp_title = package_input.opportunity_title[:30].replace(" ", "_")

        names = {
            DocumentType.COVER_LETTER: f"{org_name}_Cover_Letter.pdf",
            DocumentType.PROPOSAL_NARRATIVE: f"{org_name}_Proposal_{opp_title}.pdf",
            DocumentType.BUDGET: f"{org_name}_Budget.xlsx",
            DocumentType.BUDGET_NARRATIVE: f"{org_name}_Budget_Narrative.pdf",
            DocumentType.ORGANIZATIONAL_DOCUMENTS: f"{org_name}_Org_Documents.pdf",
            DocumentType.FINANCIAL_STATEMENTS: f"{org_name}_Financial_Statements.pdf",
            DocumentType.LETTERS_OF_SUPPORT: f"{org_name}_Support_Letters.pdf",
            DocumentType.ADDITIONAL_MATERIALS: f"{org_name}_Additional_Materials.pdf"
        }

        return names.get(doc_type, f"{org_name}_{doc_type.value}.pdf")

    def _is_required_document(self, doc_type: DocumentType) -> bool:
        """Determine if document is required"""

        # Most documents are required
        required_docs = {
            DocumentType.COVER_LETTER,
            DocumentType.PROPOSAL_NARRATIVE,
            DocumentType.BUDGET,
            DocumentType.ORGANIZATIONAL_DOCUMENTS
        }

        return doc_type in required_docs

    def _get_document_notes(self, doc_type: DocumentType) -> Optional[str]:
        """Get notes for document type"""

        notes = {
            DocumentType.COVER_LETTER: "Introduce organization and request",
            DocumentType.PROPOSAL_NARRATIVE: "Describe project and expected outcomes",
            DocumentType.BUDGET: "Detailed financial breakdown",
            DocumentType.BUDGET_NARRATIVE: "Explanation of budget line items",
            DocumentType.ORGANIZATIONAL_DOCUMENTS: "501(c)(3) letter, bylaws, board list",
            DocumentType.FINANCIAL_STATEMENTS: "Most recent audited financials or 990",
            DocumentType.LETTERS_OF_SUPPORT: "From partners and community members",
            DocumentType.ADDITIONAL_MATERIALS: "Supporting documentation as needed"
        }

        return notes.get(doc_type)

    def _create_checklist(
        self,
        package_input: GrantPackageInput,
        documents: List[PackageDocument]
    ) -> PackageChecklist:
        """Create package completion checklist"""

        checklist_items = []

        # Document checklist items
        for doc in documents:
            checklist_items.append({
                "item": f"Complete {doc.document_type.value.replace('_', ' ').title()}",
                "completed": doc.status == "complete",
                "required": doc.required
            })

        # Additional checklist items
        additional_items = [
            {"item": "Review funder guidelines", "completed": False, "required": True},
            {"item": "Obtain board approval", "completed": False, "required": True},
            {"item": "Final proofreading", "completed": False, "required": True},
            {"item": "Prepare submission method", "completed": False, "required": True}
        ]

        checklist_items.extend(additional_items)

        # Calculate completion
        completed = sum(1 for item in checklist_items if item["completed"])
        total = len(checklist_items)
        completion_pct = (completed / total * 100) if total > 0 else 0

        return PackageChecklist(
            checklist_items=checklist_items,
            completed_items=completed,
            total_items=total,
            completion_percentage=completion_pct
        )

    def _create_submission_plan(self, package_input: GrantPackageInput) -> SubmissionPlan:
        """Create submission plan"""

        # Parse deadline
        try:
            deadline = datetime.fromisoformat(package_input.application_deadline.replace('Z', '+00:00'))
        except:
            deadline = datetime.now() + timedelta(days=30)  # Default to 30 days

        now = datetime.now()
        days_until = (deadline - now).days

        # Recommend submission 2 days before deadline
        recommended_submission = deadline - timedelta(days=2)

        # Final review should be 5 days before deadline
        final_review = deadline - timedelta(days=5)

        # Determine submission method (would parse from funder requirements)
        submission_method = "online"

        instructions = f"Submit application through funder's online portal by {deadline.strftime('%Y-%m-%d %H:%M')}"

        return SubmissionPlan(
            submission_method=submission_method,
            submission_deadline=deadline.strftime('%Y-%m-%d'),
            submission_instructions=instructions,
            days_until_deadline=max(0, days_until),
            recommended_submission_date=recommended_submission.strftime('%Y-%m-%d'),
            final_review_date=final_review.strftime('%Y-%m-%d')
        )

    def get_cost_estimate(self) -> Optional[float]:
        return GRANT_PACKAGE_GENERATOR_COST

    def validate_inputs(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate tool inputs."""
        package_input = kwargs.get("package_input")

        if not package_input:
            return False, "package_input is required"

        if not isinstance(package_input, GrantPackageInput):
            return False, "package_input must be GrantPackageInput instance"

        if not package_input.opportunity_id:
            return False, "opportunity_id is required"

        if not package_input.include_documents:
            return False, "include_documents list is required"

        return True, None


# Convenience function
async def generate_grant_package(
    opportunity_id: str,
    opportunity_title: str,
    funder_name: str,
    application_deadline: str,
    organization_ein: str,
    organization_name: str,
    include_documents: List[str],
    intelligence_data: Optional[dict] = None,
    config: Optional[dict] = None
) -> ToolResult[GrantPackageOutput]:
    """Generate grant application package."""

    tool = GrantPackageGeneratorTool(config)

    # Convert string document types to enum
    doc_types = [DocumentType(doc) for doc in include_documents]

    package_input = GrantPackageInput(
        opportunity_id=opportunity_id,
        opportunity_title=opportunity_title,
        funder_name=funder_name,
        application_deadline=application_deadline,
        organization_ein=organization_ein,
        organization_name=organization_name,
        include_documents=doc_types,
        intelligence_data=intelligence_data
    )

    return await tool.execute(package_input=package_input)
