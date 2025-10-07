"""
Grant Application Package Generator - Complete Grant Application Intelligence

Purpose: Generate comprehensive grant application packages that get teams 60-80% ready to apply
Features:
- Application requirement analysis and documentation templates
- Effort estimation and timeline planning
- Checklist generation and milestone tracking
- Strategic positioning and competitive advantage analysis
- APPROACH tab preparation and pursuit recommendations
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)

# Grant Package Generation Models

class DocumentTemplate(BaseModel):
    """Document template with preparation guidance"""
    document_type: str
    template_outline: List[str] = Field(default_factory=list)
    writing_guidance: List[str] = Field(default_factory=list)
    common_pitfalls: List[str] = Field(default_factory=list)
    success_examples: List[str] = Field(default_factory=list)
    review_checklist: List[str] = Field(default_factory=list)

class ApplicationChecklist(BaseModel):
    """Complete application checklist with status tracking"""
    checklist_category: str
    checklist_items: List[Dict[str, str]] = Field(default_factory=list)
    completion_percentage: float = 0.0
    critical_items: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)

class PreparationPhase(BaseModel):
    """Detailed preparation phase with tasks and timeline"""
    phase_name: str
    duration_weeks: int
    effort_hours: int
    key_activities: List[str] = Field(default_factory=list)
    deliverables: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)

class ApplicationPackage(BaseModel):
    """Complete grant application package"""
    package_id: str
    target_organization: str
    grant_opportunity_title: str
    application_deadline: str
    generated_date: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # Core package components
    document_templates: List[DocumentTemplate] = Field(default_factory=list)
    application_checklists: List[ApplicationChecklist] = Field(default_factory=list)
    preparation_phases: List[PreparationPhase] = Field(default_factory=list)
    
    # Strategic guidance
    positioning_strategy: str = ""
    competitive_advantages: List[str] = Field(default_factory=list)
    risk_mitigation_plan: List[str] = Field(default_factory=list)
    
    # Project management
    critical_path: List[str] = Field(default_factory=list)
    resource_requirements: List[str] = Field(default_factory=list)
    quality_assurance_plan: List[str] = Field(default_factory=list)

class GrantPackageGenerator:
    """Generate comprehensive grant application packages"""
    
    def __init__(self):
        self.package_templates = self._load_package_templates()
        self.document_templates = self._load_document_templates()
        self.checklist_templates = self._load_checklist_templates()
    
    def generate_application_package(self, grant_intelligence: Dict[str, Any], organization_profile: Dict[str, Any]) -> ApplicationPackage:
        """Generate complete grant application package from AI intelligence"""
        try:
            target_org = grant_intelligence.get("target_organization", "Unknown")
            package_id = f"grant_package_{int(datetime.now().timestamp())}"
            
            # Extract key information
            app_requirements = grant_intelligence.get("application_requirements", [])
            grant_timeline = grant_intelligence.get("grant_timeline", {})
            effort_estimation = grant_intelligence.get("effort_estimation", {})
            recommended_approach = grant_intelligence.get("recommended_approach", {})
            
            # Generate document templates
            document_templates = self._generate_document_templates(app_requirements, organization_profile)
            
            # Generate application checklists
            checklists = self._generate_application_checklists(app_requirements, effort_estimation)
            
            # Generate preparation phases
            prep_phases = self._generate_preparation_phases(effort_estimation, grant_timeline)
            
            # Extract strategic positioning
            positioning = recommended_approach.get("positioning_strategy", "Standard competitive positioning")
            competitive_advantages = grant_intelligence.get("competitive_advantages", [])
            
            # Generate critical path
            critical_path = self._generate_critical_path(prep_phases, grant_timeline)
            
            package = ApplicationPackage(
                package_id=package_id,
                target_organization=target_org,
                grant_opportunity_title=f"{target_org} Grant Opportunity",
                application_deadline=grant_timeline.get("application_deadline", "TBD"),
                document_templates=document_templates,
                application_checklists=checklists,
                preparation_phases=prep_phases,
                positioning_strategy=positioning,
                competitive_advantages=competitive_advantages,
                risk_mitigation_plan=self._generate_risk_mitigation_plan(grant_intelligence),
                critical_path=critical_path,
                resource_requirements=self._generate_resource_requirements(effort_estimation),
                quality_assurance_plan=self._generate_qa_plan()
            )
            
            logger.info(f"Generated comprehensive grant package for {target_org}")
            return package
            
        except Exception as e:
            logger.error(f"Failed to generate grant package: {str(e)}")
            raise
    
    def _generate_document_templates(self, app_requirements: List[Dict], org_profile: Dict) -> List[DocumentTemplate]:
        """Generate document templates based on application requirements"""
        templates = []
        
        for req in app_requirements:
            doc_type = req.get("document_type", "Unknown Document")
            description = req.get("description", "")
            
            if "narrative" in doc_type.lower() or "proposal" in doc_type.lower():
                template = DocumentTemplate(
                    document_type=doc_type,
                    template_outline=[
                        "Executive Summary (1 page)",
                        "Statement of Need (2-3 pages)",
                        "Project Description (3-4 pages)", 
                        "Goals, Objectives, and Expected Outcomes (2 pages)",
                        "Methodology and Implementation Plan (2-3 pages)",
                        "Evaluation Plan (1-2 pages)",
                        "Organizational Capacity and Experience (1-2 pages)",
                        "Sustainability Plan (1 page)",
                        "Budget Narrative (1-2 pages)"
                    ],
                    writing_guidance=[
                        "Use clear, concise language and avoid jargon",
                        "Include specific, measurable outcomes and timelines",
                        "Provide evidence-based justification for all claims",
                        "Connect all activities to stated goals and objectives",
                        "Demonstrate organizational capacity with concrete examples"
                    ],
                    common_pitfalls=[
                        "Vague or unmeasurable objectives",
                        "Insufficient evidence of organizational capacity",
                        "Weak or missing evaluation plan",
                        "Budget that doesn't align with proposed activities",
                        "Failure to address sustainability"
                    ],
                    success_examples=[
                        "Clear logic model connecting activities to outcomes",
                        "Strong needs assessment with local data",
                        "Detailed implementation timeline with milestones",
                        "Comprehensive evaluation with both process and outcome measures",
                        "Evidence of stakeholder support and community buy-in"
                    ],
                    review_checklist=[
                        "All requirements addressed completely",
                        "Page limits and formatting requirements met",
                        "Grammar and spelling error-free",
                        "Consistent tone and messaging throughout",
                        "Supporting documents referenced and attached"
                    ]
                )
                templates.append(template)
            
            elif "budget" in doc_type.lower():
                template = DocumentTemplate(
                    document_type=doc_type,
                    template_outline=[
                        "Personnel Costs (salaries, benefits, consultants)",
                        "Direct Program Costs (materials, supplies, equipment)",
                        "Administrative/Indirect Costs (utilities, rent, admin)",
                        "Travel and Transportation",
                        "Other Direct Costs",
                        "Cost-Share/Match Requirements (if applicable)"
                    ],
                    writing_guidance=[
                        "Ensure all costs are allowable, allocable, and reasonable",
                        "Provide detailed justification for all major budget items",
                        "Include sufficient detail for reviewers to understand costs",
                        "Show clear connection between budget and project activities",
                        "Account for inflation and cost escalation over project period"
                    ],
                    common_pitfalls=[
                        "Underestimating personnel time requirements",
                        "Including unallowable costs",
                        "Insufficient budget detail or justification",
                        "Math errors or inconsistencies",
                        "Failure to include required cost-sharing"
                    ],
                    review_checklist=[
                        "All calculations verified and accurate",
                        "Budget aligns with project narrative",
                        "Cost-share requirements met",
                        "All budget categories properly justified",
                        "Indirect cost rate documentation included"
                    ]
                )
                templates.append(template)
            
            else:
                # Generic template for other document types
                template = DocumentTemplate(
                    document_type=doc_type,
                    template_outline=[
                        "Document introduction and purpose",
                        "Main content sections as required",
                        "Supporting evidence and documentation",
                        "Conclusion and next steps"
                    ],
                    writing_guidance=[
                        "Follow all specified formatting requirements",
                        "Address all required elements completely",
                        "Provide clear, well-organized content",
                        "Use professional tone and language"
                    ],
                    common_pitfalls=[
                        "Missing required elements",
                        "Formatting errors",
                        "Insufficient detail or explanation",
                        "Late submission or missed deadlines"
                    ],
                    review_checklist=[
                        "All requirements addressed",
                        "Formatting and length requirements met",
                        "Content is clear and well-organized",
                        "Supporting documents included"
                    ]
                )
                templates.append(template)
        
        return templates
    
    def _generate_application_checklists(self, app_requirements: List[Dict], effort_estimation: Dict) -> List[ApplicationChecklist]:
        """Generate comprehensive application checklists"""
        checklists = []
        
        # Pre-Application Checklist
        pre_app_checklist = ApplicationChecklist(
            checklist_category="Pre-Application Preparation",
            checklist_items=[
                {"item": "Review full grant guidelines and requirements", "status": "pending", "notes": "Critical first step"},
                {"item": "Confirm organizational eligibility", "status": "pending", "notes": "Must meet all eligibility criteria"},
                {"item": "Assess organizational capacity for project", "status": "pending", "notes": "Realistic capacity assessment"},
                {"item": "Identify potential project partners", "status": "pending", "notes": "Strategic partnership development"},
                {"item": "Develop preliminary project concept", "status": "pending", "notes": "Clear project vision"},
                {"item": "Estimate full project costs", "status": "pending", "notes": "Comprehensive budget planning"},
                {"item": "Secure board/leadership approval to proceed", "status": "pending", "notes": "Organizational commitment"}
            ],
            critical_items=["Confirm eligibility", "Board approval", "Capacity assessment"],
            dependencies=["Grant guidelines review"]
        )
        checklists.append(pre_app_checklist)
        
        # Documentation Checklist
        doc_checklist = ApplicationChecklist(
            checklist_category="Required Documentation",
            checklist_items=[
                {"item": "IRS determination letter", "status": "pending", "notes": "501(c)(3) proof"},
                {"item": "Current organizational chart", "status": "pending", "notes": "Staff structure"},
                {"item": "Board of directors list", "status": "pending", "notes": "Governance documentation"},
                {"item": "Audited financial statements (2 years)", "status": "pending", "notes": "Financial transparency"},
                {"item": "Letters of support from key partners", "status": "pending", "notes": "Community endorsement"},
                {"item": "Project evaluation plan", "status": "pending", "notes": "Outcome measurement"},
                {"item": "Organizational policies (as required)", "status": "pending", "notes": "Compliance documentation"}
            ],
            critical_items=["IRS letter", "Financial statements", "Board list"],
            dependencies=["Eligibility confirmation"]
        )
        checklists.append(doc_checklist)
        
        # Application Development Checklist
        dev_checklist = ApplicationChecklist(
            checklist_category="Application Development",
            checklist_items=[
                {"item": "Complete project narrative", "status": "pending", "notes": "Core application document"},
                {"item": "Detailed project budget", "status": "pending", "notes": "Financial planning"},
                {"item": "Budget justification narrative", "status": "pending", "notes": "Cost explanation"},
                {"item": "Timeline and milestones", "status": "pending", "notes": "Project scheduling"},
                {"item": "Evaluation methodology", "status": "pending", "notes": "Impact measurement"},
                {"item": "Sustainability plan", "status": "pending", "notes": "Long-term viability"},
                {"item": "Risk management strategy", "status": "pending", "notes": "Contingency planning"}
            ],
            critical_items=["Project narrative", "Budget", "Timeline"],
            dependencies=["Pre-application completion"]
        )
        checklists.append(dev_checklist)
        
        # Quality Assurance Checklist
        qa_checklist = ApplicationChecklist(
            checklist_category="Quality Assurance and Submission",
            checklist_items=[
                {"item": "Internal review by subject matter experts", "status": "pending", "notes": "Content validation"},
                {"item": "External review by grant writing professional", "status": "pending", "notes": "Professional assessment"},
                {"item": "Financial review by accounting/finance", "status": "pending", "notes": "Budget accuracy"},
                {"item": "Legal review (if required)", "status": "pending", "notes": "Compliance check"},
                {"item": "Final formatting and document assembly", "status": "pending", "notes": "Presentation quality"},
                {"item": "Submission system testing", "status": "pending", "notes": "Technical preparation"},
                {"item": "Application submission with confirmation", "status": "pending", "notes": "Final delivery"}
            ],
            critical_items=["External review", "Submission confirmation"],
            dependencies=["Application development completion"]
        )
        checklists.append(qa_checklist)
        
        return checklists
    
    def _generate_preparation_phases(self, effort_estimation: Dict, grant_timeline: Dict) -> List[PreparationPhase]:
        """Generate detailed preparation phases with timelines"""
        phases = []
        
        # Phase 1: Research and Planning
        phase1 = PreparationPhase(
            phase_name="Research and Planning",
            duration_weeks=2,
            effort_hours=40,
            key_activities=[
                "Comprehensive grant guidelines analysis",
                "Organizational capacity assessment",
                "Stakeholder identification and engagement",
                "Project concept development",
                "Preliminary budget estimation",
                "Risk assessment and mitigation planning"
            ],
            deliverables=[
                "Project concept document",
                "Stakeholder mapping",
                "Preliminary budget",
                "Risk assessment matrix",
                "Go/no-go recommendation"
            ],
            dependencies=["Grant opportunity identification"],
            risks=["Insufficient time for thorough research", "Key stakeholders unavailable"],
            success_criteria=["Clear project concept", "Stakeholder buy-in", "Realistic budget estimate"]
        )
        phases.append(phase1)
        
        # Phase 2: Application Development
        phase2 = PreparationPhase(
            phase_name="Application Development",
            duration_weeks=4,
            effort_hours=80,
            key_activities=[
                "Project narrative writing",
                "Detailed budget development", 
                "Supporting documentation collection",
                "Letters of support solicitation",
                "Evaluation plan development",
                "Timeline and milestone planning"
            ],
            deliverables=[
                "Complete project narrative",
                "Detailed budget with justification",
                "Supporting documents package",
                "Letters of support",
                "Evaluation framework"
            ],
            dependencies=["Phase 1 completion", "Board approval"],
            risks=["Writer availability", "Partner responsiveness", "Scope creep"],
            success_criteria=["Complete first draft", "Partner commitments secured", "Budget validated"]
        )
        phases.append(phase2)
        
        # Phase 3: Review and Refinement
        phase3 = PreparationPhase(
            phase_name="Review and Refinement",
            duration_weeks=2,
            effort_hours=30,
            key_activities=[
                "Internal expert review",
                "External professional review",
                "Financial accuracy validation",
                "Compliance verification",
                "Document formatting and assembly",
                "Final quality assurance"
            ],
            deliverables=[
                "Reviewed and refined application",
                "Professional assessment report",
                "Final budget validation",
                "Formatted final documents",
                "Submission-ready package"
            ],
            dependencies=["Phase 2 completion", "Reviewer availability"],
            risks=["Major revisions required", "Review timeline delays", "Technical issues"],
            success_criteria=["Professional approval", "No major gaps identified", "Submission ready"]
        )
        phases.append(phase3)
        
        # Phase 4: Submission and Follow-up
        phase4 = PreparationPhase(
            phase_name="Submission and Follow-up",
            duration_weeks=1,
            effort_hours=10,
            key_activities=[
                "Final document compilation",
                "Submission system preparation",
                "Application submission",
                "Submission confirmation",
                "Post-submission follow-up plan"
            ],
            deliverables=[
                "Submitted application",
                "Submission confirmation",
                "Follow-up timeline",
                "Next steps plan"
            ],
            dependencies=["Phase 3 completion", "System access"],
            risks=["Technical submission issues", "Last-minute changes", "System downtime"],
            success_criteria=["Successful submission", "Confirmation received", "Follow-up planned"]
        )
        phases.append(phase4)
        
        return phases
    
    def _generate_critical_path(self, prep_phases: List[PreparationPhase], grant_timeline: Dict) -> List[str]:
        """Generate critical path activities for project management"""
        critical_path = [
            "Grant guidelines review and eligibility confirmation",
            "Board/leadership approval to proceed",
            "Project team assembly and role assignments",
            "Stakeholder engagement and partnership development", 
            "Project narrative first draft completion",
            "Budget development and financial validation",
            "Letters of support collection",
            "External professional review engagement",
            "Final document assembly and formatting",
            "Submission system testing and preparation",
            "Application submission with confirmation"
        ]
        return critical_path
    
    def _generate_resource_requirements(self, effort_estimation: Dict) -> List[str]:
        """Generate comprehensive resource requirements"""
        return [
            "Project Director/Manager (20-30 hours/week)",
            "Grant Writer (professional, 40-60 hours total)",
            "Financial Analyst (budget development, 10-15 hours)",
            "Subject Matter Expert (technical review, 5-10 hours)",
            "Administrative Support (document management, 15-20 hours)",
            "External Review Consultant (professional assessment, 8-12 hours)",
            "Legal Review (if required, 3-5 hours)",
            "Board Member Champion (advocacy and approval, 5-8 hours)"
        ]
    
    def _generate_risk_mitigation_plan(self, grant_intelligence: Dict) -> List[str]:
        """Generate risk mitigation strategies"""
        return [
            "Start application process early to allow for delays",
            "Engage backup reviewers in case primary contacts unavailable", 
            "Maintain regular communication with all team members",
            "Create templates and standardized processes for efficiency",
            "Build in buffer time for unexpected revisions",
            "Establish clear roles and responsibilities upfront",
            "Implement version control for all documents",
            "Plan submission strategy to avoid last-minute technical issues"
        ]
    
    def _generate_qa_plan(self) -> List[str]:
        """Generate quality assurance plan"""
        return [
            "Multi-stage review process with internal and external reviewers",
            "Dedicated grammar and formatting review",
            "Technical compliance verification against all requirements",
            "Financial accuracy validation by accounting professional",
            "Legal review for compliance and risk assessment",
            "Final stakeholder sign-off before submission",
            "Technical submission testing with backup plans",
            "Post-submission quality assurance and follow-up planning"
        ]
    
    def _load_package_templates(self) -> Dict:
        """Load standard package templates"""
        return {}
    
    def _load_document_templates(self) -> Dict:
        """Load document templates"""
        return {}
    
    def _load_checklist_templates(self) -> Dict:
        """Load checklist templates"""
        return {}
    
    def export_package_to_formats(self, package: ApplicationPackage) -> Dict[str, str]:
        """Export package to multiple formats (JSON, PDF, Excel)"""
        try:
            # JSON export (structured data)
            json_content = package.json(indent=2)
            
            # Generate executive summary for reports
            summary = self._generate_executive_summary(package)
            
            # Generate checklist export
            checklist_export = self._generate_checklist_export(package)
            
            # Generate timeline export  
            timeline_export = self._generate_timeline_export(package)
            
            return {
                "json": json_content,
                "executive_summary": summary,
                "checklist": checklist_export,
                "timeline": timeline_export
            }
            
        except Exception as e:
            logger.error(f"Failed to export package: {str(e)}")
            raise
    
    def _generate_executive_summary(self, package: ApplicationPackage) -> str:
        """Generate executive summary of grant package"""
        summary = f"""
GRANT APPLICATION PACKAGE SUMMARY

Target Organization: {package.target_organization}
Application Deadline: {package.application_deadline}
Generated: {package.generated_date}

PREPARATION OVERVIEW:
- Total Phases: {len(package.preparation_phases)}
- Total Effort: {sum([phase.effort_hours for phase in package.preparation_phases])} hours
- Timeline: {sum([phase.duration_weeks for phase in package.preparation_phases])} weeks

CRITICAL SUCCESS FACTORS:
{chr(10).join([f"- {advantage}" for advantage in package.competitive_advantages[:5]])}

KEY DELIVERABLES:
{chr(10).join([f"- {template.document_type}" for template in package.document_templates])}

CRITICAL PATH HIGHLIGHTS:
{chr(10).join([f"- {item}" for item in package.critical_path[:5]])}

This package provides comprehensive guidance to get your grant team 60-80% ready for application submission.
"""
        return summary
    
    def _generate_checklist_export(self, package: ApplicationPackage) -> str:
        """Generate checklist export format"""
        checklist_content = "GRANT APPLICATION CHECKLIST\n\n"
        
        for checklist in package.application_checklists:
            checklist_content += f"{checklist.checklist_category.upper()}:\n"
            for item in checklist.checklist_items:
                checklist_content += f"☐ {item['item']}\n"
                if item.get('notes'):
                    checklist_content += f"   Notes: {item['notes']}\n"
            checklist_content += "\n"
        
        return checklist_content
    
    def _generate_timeline_export(self, package: ApplicationPackage) -> str:
        """Generate timeline export format"""
        timeline_content = "GRANT APPLICATION TIMELINE\n\n"
        
        for i, phase in enumerate(package.preparation_phases, 1):
            timeline_content += f"PHASE {i}: {phase.phase_name}\n"
            timeline_content += f"Duration: {phase.duration_weeks} weeks ({phase.effort_hours} hours)\n"
            timeline_content += "Key Activities:\n"
            for activity in phase.key_activities:
                timeline_content += f"- {activity}\n"
            timeline_content += "Deliverables:\n"
            for deliverable in phase.deliverables:
                timeline_content += f"- {deliverable}\n"
            timeline_content += "\n"
        
        return timeline_content

# Export the package generator and models
__all__ = [
    "GrantPackageGenerator",
    "ApplicationPackage",
    "DocumentTemplate",
    "ApplicationChecklist", 
    "PreparationPhase"
]