#!/usr/bin/env python3
"""
Compliance Roadmap Generator - Phase 5 Cross-System Integration
Comprehensive system for generating detailed compliance roadmaps for government opportunities.

This system creates actionable compliance roadmaps with timelines, requirements,
risk assessments, and step-by-step guidance for successful grant applications.
"""

import asyncio
import time
import json
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta, date
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.core.government_models import GovernmentOpportunity


class ComplianceCategory(Enum):
    """Categories of compliance requirements."""
    ELIGIBILITY = "eligibility"           # Basic eligibility requirements
    REGISTRATION = "registration"         # System registrations (SAM, Grants.gov)
    DOCUMENTATION = "documentation"       # Required documents and forms
    CERTIFICATION = "certification"       # Certifications and licenses
    FINANCIAL = "financial"              # Financial and audit requirements
    TECHNICAL = "technical"              # Technical specifications
    REGULATORY = "regulatory"            # Regulatory compliance
    REPORTING = "reporting"              # Ongoing reporting requirements


class RiskLevel(Enum):
    """Risk levels for compliance requirements."""
    LOW = "low"           # Standard requirements, low failure risk
    MEDIUM = "medium"     # Moderate complexity, some failure risk
    HIGH = "high"         # Complex requirements, significant failure risk
    CRITICAL = "critical" # Mission-critical, high failure consequence


class ComplianceStatus(Enum):
    """Status of compliance requirements."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    EXPIRED = "expired"
    FAILED = "failed"


@dataclass
class ComplianceRequirement:
    """Individual compliance requirement with detailed information."""
    requirement_id: str
    title: str
    category: ComplianceCategory
    description: str
    
    # Requirement details
    mandatory: bool = True
    risk_level: RiskLevel = RiskLevel.MEDIUM
    estimated_effort_hours: int = 0
    estimated_cost: float = 0.0
    
    # Dependencies and prerequisites
    prerequisites: List[str] = field(default_factory=list)  # Other requirement IDs
    dependent_requirements: List[str] = field(default_factory=list)
    
    # Timeline information
    deadline: Optional[datetime] = None
    recommended_start_date: Optional[datetime] = None
    buffer_days: int = 7
    
    # Guidance and resources
    step_by_step_guide: List[str] = field(default_factory=list)
    required_documents: List[str] = field(default_factory=list)
    helpful_resources: List[str] = field(default_factory=list)
    contact_information: List[str] = field(default_factory=list)
    
    # Status tracking
    status: ComplianceStatus = ComplianceStatus.NOT_STARTED
    completion_percentage: float = 0.0
    notes: str = ""
    
    # Risk assessment
    failure_risks: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)
    success_factors: List[str] = field(default_factory=list)


@dataclass
class ComplianceTimeline:
    """Timeline for compliance roadmap with milestones."""
    opportunity_id: str
    submission_deadline: datetime
    recommended_start_date: datetime
    
    # Major milestones
    milestones: Dict[str, datetime] = field(default_factory=dict)  # milestone_name -> date
    critical_deadlines: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timeline analysis
    total_preparation_days: int = 0
    critical_path_requirements: List[str] = field(default_factory=list)
    timeline_risks: List[str] = field(default_factory=list)
    
    # Scheduling recommendations
    parallel_tasks: List[List[str]] = field(default_factory=list)  # Groups of tasks that can be done in parallel
    sequential_dependencies: List[Tuple[str, str]] = field(default_factory=list)  # (prerequisite, dependent)
    
    # Buffer and contingency planning
    recommended_buffers: Dict[str, int] = field(default_factory=dict)  # requirement_id -> buffer_days
    contingency_plans: List[str] = field(default_factory=list)


@dataclass
class OrganizationalReadiness:
    """Assessment of organization's readiness for compliance."""
    organization_ein: str
    overall_readiness_score: float = 0.0  # 0.0 to 1.0
    
    # Readiness by category
    category_readiness: Dict[ComplianceCategory, float] = field(default_factory=dict)
    
    # Strengths and gaps
    organizational_strengths: List[str] = field(default_factory=list)
    compliance_gaps: List[str] = field(default_factory=list)
    recommended_investments: List[str] = field(default_factory=list)
    
    # Resource requirements
    estimated_staff_hours: int = 0
    estimated_budget_required: float = 0.0
    external_expertise_needed: List[str] = field(default_factory=list)
    
    # Historical context
    previous_compliance_experience: List[str] = field(default_factory=list)
    compliance_track_record: str = "unknown"  # excellent, good, adequate, poor, unknown


@dataclass
class ComprehensiveComplianceRoadmap:
    """Complete compliance roadmap for an opportunity-organization pair."""
    opportunity_id: str
    organization_ein: str
    agency_code: str
    roadmap_id: str
    
    # Core components
    requirements: List[ComplianceRequirement] = field(default_factory=list)
    timeline: Optional[ComplianceTimeline] = None
    organizational_readiness: Optional[OrganizationalReadiness] = None
    
    # Success metrics and projections
    compliance_success_probability: float = 0.0  # 0.0 to 1.0
    estimated_completion_date: Optional[datetime] = None
    overall_risk_assessment: RiskLevel = RiskLevel.MEDIUM
    
    # Strategic guidance
    recommended_approach: str = ""
    success_strategies: List[str] = field(default_factory=list)
    risk_mitigation_plan: List[str] = field(default_factory=list)
    
    # Progress tracking
    overall_progress: float = 0.0  # 0.0 to 1.0
    completed_requirements: List[str] = field(default_factory=list)
    in_progress_requirements: List[str] = field(default_factory=list)
    
    # Metadata
    generated_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    confidence_level: float = 0.0  # 0.0 to 1.0


class ComplianceRoadmapGenerator(BaseProcessor):
    """
    Compliance Roadmap Generator - Phase 5 Cross-System Integration
    
    Comprehensive compliance roadmap generation providing:
    
    ## Detailed Requirement Analysis
    - Complete compliance requirement identification
    - Risk assessment and mitigation planning
    - Step-by-step guidance and resources
    - Timeline and dependency mapping
    
    ## Organizational Readiness Assessment
    - Capability gap analysis
    - Resource requirement estimation
    - Historical compliance performance
    - Readiness scoring and recommendations
    
    ## Timeline and Project Management
    - Critical path analysis
    - Milestone planning and scheduling
    - Buffer and contingency planning
    - Parallel task identification
    
    ## Risk Management and Success Planning
    - Comprehensive risk assessment
    - Mitigation strategy development
    - Success factor identification
    - Continuous monitoring and adaptation
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="compliance_roadmap_generator",
            description="Generate comprehensive compliance roadmaps for government opportunities",
            version="1.0.0",
            dependencies=["government_research_integration", "agency_intelligence_framework"],
            estimated_duration=300,  # 5 minutes for comprehensive roadmaps
            requires_network=False,  # Uses cached and analysis data
            requires_api_key=False,  # No external API calls required
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Initialize compliance knowledge base
        self.compliance_templates = self._initialize_compliance_templates()
        self.agency_specific_requirements = self._initialize_agency_requirements()
        self.risk_patterns = self._initialize_risk_patterns()
        
        # Roadmap generation weights
        self.roadmap_weights = {
            "requirement_completeness": 0.25,    # How complete the requirements are
            "timeline_feasibility": 0.25,       # Whether timeline is realistic
            "organizational_readiness": 0.20,    # Organization's capacity
            "risk_mitigation": 0.15,            # Risk management quality
            "resource_availability": 0.15       # Resource requirement alignment
        }
        
        # Risk assessment factors
        self.risk_factors = {
            "timeline_pressure": {"weight": 0.3, "threshold": 30},  # days until deadline
            "requirement_complexity": {"weight": 0.25, "threshold": 10},  # number of complex requirements
            "organizational_experience": {"weight": 0.2, "threshold": 0.7},  # readiness score
            "agency_complexity": {"weight": 0.15, "threshold": "tier_1"},  # agency tier
            "financial_requirements": {"weight": 0.1, "threshold": 50000}  # cost threshold
        }
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute comprehensive compliance roadmap generation."""
        start_time = time.time()
        
        try:
            # Get opportunities and organizations for roadmap generation
            opportunities = await self._get_target_opportunities(workflow_state)
            organizations = await self._get_target_organizations(workflow_state)
            
            if not opportunities:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No opportunities found for compliance roadmap generation"]
                )
            
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No organizations found for compliance roadmap generation"]
                )
            
            self.logger.info(f"Generating compliance roadmaps for {len(opportunities)} opportunities and {len(organizations)} organizations")
            
            # Generate comprehensive compliance roadmaps
            compliance_roadmaps = []
            total_combinations = len(opportunities) * len(organizations)
            processed = 0
            
            for opportunity in opportunities:
                for organization in organizations:
                    processed += 1
                    self._update_progress(
                        processed, total_combinations,
                        f"Generating compliance roadmap for {opportunity.title[:30]}... and {organization.name[:20]}..."
                    )
                    
                    # Generate comprehensive roadmap
                    roadmap = await self._generate_comprehensive_compliance_roadmap(
                        opportunity, organization, config
                    )
                    
                    if roadmap:
                        compliance_roadmaps.append(roadmap.__dict__)
            
            # Generate roadmap analytics and insights
            roadmap_analytics = await self._generate_roadmap_analytics(compliance_roadmaps)
            
            # Generate cross-roadmap insights
            cross_roadmap_insights = await self._generate_cross_roadmap_insights(compliance_roadmaps)
            
            # Calculate compliance performance metrics
            performance_metrics = await self._calculate_compliance_performance_metrics(
                compliance_roadmaps, opportunities, organizations
            )
            
            # Generate strategic recommendations
            strategic_recommendations = await self._generate_compliance_strategic_recommendations(
                compliance_roadmaps, roadmap_analytics
            )
            
            # Prepare comprehensive results
            result_data = {
                "comprehensive_compliance_roadmaps": compliance_roadmaps,
                "roadmap_analytics": roadmap_analytics,
                "cross_roadmap_insights": cross_roadmap_insights,
                "performance_metrics": performance_metrics,
                "strategic_recommendations": strategic_recommendations,
                "total_roadmaps_generated": len(compliance_roadmaps),
                "compliance_summary": {
                    "high_success_probability": len([r for r in compliance_roadmaps if r["compliance_success_probability"] > 0.7]),
                    "moderate_risk_roadmaps": len([r for r in compliance_roadmaps if r["overall_risk_assessment"] == "medium"]),
                    "high_risk_roadmaps": len([r for r in compliance_roadmaps if r["overall_risk_assessment"] in ["high", "critical"]]),
                    "avg_preparation_days": self._calculate_avg_preparation_days(compliance_roadmaps)
                }
            }
            
            execution_time = time.time() - start_time
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "roadmap_scope": "comprehensive",
                    "analysis_depth": "detailed",
                    "roadmap_confidence": self._calculate_overall_roadmap_confidence(compliance_roadmaps)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Compliance roadmap generation failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"Compliance roadmap generation failed: {str(e)}"]
            )
    
    async def _generate_comprehensive_compliance_roadmap(
        self,
        opportunity: GovernmentOpportunity,
        organization: OrganizationProfile,
        config: ProcessorConfig
    ) -> Optional[ComprehensiveComplianceRoadmap]:
        """Generate comprehensive compliance roadmap for opportunity-organization pair."""
        
        try:
            # Generate unique roadmap ID
            roadmap_id = self._generate_roadmap_id(opportunity.opportunity_id, organization.ein)
            
            # Create base roadmap
            roadmap = ComprehensiveComplianceRoadmap(
                opportunity_id=opportunity.opportunity_id,
                organization_ein=organization.ein,
                agency_code=opportunity.agency_code,
                roadmap_id=roadmap_id
            )
            
            # Generate compliance requirements
            roadmap.requirements = await self._generate_compliance_requirements(
                opportunity, organization
            )
            
            # Generate timeline
            roadmap.timeline = await self._generate_compliance_timeline(
                opportunity, organization, roadmap.requirements
            )
            
            # Assess organizational readiness
            roadmap.organizational_readiness = await self._assess_organizational_readiness(
                organization, roadmap.requirements
            )
            
            # Calculate success probability
            roadmap.compliance_success_probability = self._calculate_compliance_success_probability(
                roadmap.requirements, roadmap.timeline, roadmap.organizational_readiness
            )
            
            # Assess overall risk
            roadmap.overall_risk_assessment = self._assess_overall_risk(
                opportunity, organization, roadmap.requirements, roadmap.timeline
            )
            
            # Generate strategic guidance
            roadmap.recommended_approach = self._generate_recommended_approach(
                opportunity, organization, roadmap
            )
            
            roadmap.success_strategies = self._generate_success_strategies(
                opportunity, organization, roadmap
            )
            
            roadmap.risk_mitigation_plan = self._generate_risk_mitigation_plan(
                roadmap.requirements, roadmap.timeline, roadmap.organizational_readiness
            )
            
            # Calculate estimated completion date
            roadmap.estimated_completion_date = self._calculate_estimated_completion_date(
                roadmap.timeline, roadmap.requirements
            )
            
            # Set confidence level
            roadmap.confidence_level = self._calculate_roadmap_confidence(roadmap)
            
            return roadmap
            
        except Exception as e:
            self.logger.warning(f"Failed to generate roadmap for {opportunity.opportunity_id} and {organization.ein}: {e}")
            return None
    
    async def _generate_compliance_requirements(
        self,
        opportunity: GovernmentOpportunity,
        organization: OrganizationProfile
    ) -> List[ComplianceRequirement]:
        """Generate comprehensive list of compliance requirements."""
        
        requirements = []
        
        # Base federal requirements
        base_requirements = self._get_base_federal_requirements()
        requirements.extend(base_requirements)
        
        # Agency-specific requirements
        agency_requirements = self._get_agency_specific_requirements(opportunity.agency_code)
        requirements.extend(agency_requirements)
        
        # Opportunity-specific requirements
        opportunity_requirements = self._extract_opportunity_specific_requirements(opportunity)
        requirements.extend(opportunity_requirements)
        
        # Organization-specific adjustments
        org_adjusted_requirements = self._adjust_requirements_for_organization(
            requirements, organization
        )
        
        # Set deadlines and timelines
        requirements_with_timelines = self._set_requirement_timelines(
            org_adjusted_requirements, opportunity
        )
        
        # Validate and finalize requirements
        validated_requirements = self._validate_requirements(requirements_with_timelines)
        
        return validated_requirements
    
    def _get_base_federal_requirements(self) -> List[ComplianceRequirement]:
        """Get base federal grant requirements."""
        
        return [
            ComplianceRequirement(
                requirement_id="sam_registration",
                title="SAM.gov Registration",
                category=ComplianceCategory.REGISTRATION,
                description="Register organization in System for Award Management",
                mandatory=True,
                risk_level=RiskLevel.HIGH,
                estimated_effort_hours=8,
                estimated_cost=0.0,
                buffer_days=14,
                step_by_step_guide=[
                    "Gather required organizational information",
                    "Create SAM.gov account",
                    "Complete entity registration",
                    "Submit registration for processing",
                    "Monitor registration status",
                    "Maintain active registration"
                ],
                required_documents=[
                    "EIN/Tax ID number",
                    "DUNS number (if applicable)",
                    "Banking information",
                    "Point of contact information"
                ],
                helpful_resources=[
                    "SAM.gov Help Desk: 1-866-606-8220",
                    "SAM.gov User Guide",
                    "Federal Service Desk"
                ],
                failure_risks=[
                    "Application rejection without SAM registration",
                    "Delays in registration processing",
                    "Incomplete or incorrect information"
                ],
                mitigation_strategies=[
                    "Start registration process immediately",
                    "Verify all information before submission",
                    "Monitor registration status regularly"
                ]
            ),
            ComplianceRequirement(
                requirement_id="grants_gov_registration",
                title="Grants.gov Registration",
                category=ComplianceCategory.REGISTRATION,
                description="Register organization for federal grant applications",
                mandatory=True,
                risk_level=RiskLevel.MEDIUM,
                estimated_effort_hours=4,
                estimated_cost=0.0,
                prerequisites=["sam_registration"],
                buffer_days=7,
                step_by_step_guide=[
                    "Complete SAM.gov registration first",
                    "Create Grants.gov account",
                    "Register organization",
                    "Assign authorized organization representatives",
                    "Test application submission capability"
                ],
                required_documents=[
                    "SAM.gov registration confirmation",
                    "Authorized representative information"
                ],
                helpful_resources=[
                    "Grants.gov Customer Support: 1-800-518-4726",
                    "Organization Registration Guide"
                ]
            ),
            ComplianceRequirement(
                requirement_id="sf424_application",
                title="SF-424 Application Form",
                category=ComplianceCategory.DOCUMENTATION,
                description="Complete standard federal application form",
                mandatory=True,
                risk_level=RiskLevel.MEDIUM,
                estimated_effort_hours=6,
                estimated_cost=0.0,
                buffer_days=5,
                step_by_step_guide=[
                    "Download SF-424 form",
                    "Gather required organizational and project information",
                    "Complete all required fields",
                    "Review for accuracy and completeness",
                    "Obtain necessary signatures"
                ],
                required_documents=[
                    "Project description summary",
                    "Budget summary",
                    "Organizational information"
                ]
            ),
            ComplianceRequirement(
                requirement_id="budget_narrative",
                title="Budget Narrative and Justification",
                category=ComplianceCategory.FINANCIAL,
                description="Detailed budget breakdown and justification",
                mandatory=True,
                risk_level=RiskLevel.HIGH,
                estimated_effort_hours=16,
                estimated_cost=0.0,
                buffer_days=10,
                step_by_step_guide=[
                    "Review grant guidelines and allowable costs",
                    "Develop detailed budget by category",
                    "Write justification for each budget item",
                    "Ensure budget aligns with project activities",
                    "Review against federal cost principles"
                ],
                required_documents=[
                    "Cost breakdown by category",
                    "Personnel cost calculations",
                    "Indirect cost rate documentation"
                ],
                failure_risks=[
                    "Budget exceeds award limits",
                    "Unallowable costs included",
                    "Insufficient justification"
                ],
                mitigation_strategies=[
                    "Review 2 CFR 200 cost principles",
                    "Consult with grants management office",
                    "Have budget reviewed by experienced personnel"
                ]
            )
        ]
    
    def _get_agency_specific_requirements(self, agency_code: str) -> List[ComplianceRequirement]:
        """Get agency-specific requirements."""
        
        agency_requirements = {
            "DOD": [
                ComplianceRequirement(
                    requirement_id="dcaa_compliance",
                    title="DCAA Compliance System",
                    category=ComplianceCategory.REGULATORY,
                    description="Defense Contract Audit Agency compliance requirements",
                    mandatory=True,
                    risk_level=RiskLevel.CRITICAL,
                    estimated_effort_hours=40,
                    estimated_cost=5000.0,
                    buffer_days=30,
                    step_by_step_guide=[
                        "Assess current accounting system",
                        "Identify compliance gaps",
                        "Implement required accounting standards",
                        "Prepare for DCAA audit",
                        "Obtain compliance certification"
                    ],
                    external_expertise_needed=["DCAA compliance consultant", "Accounting system specialist"]
                ),
                ComplianceRequirement(
                    requirement_id="security_clearance",
                    title="Security Clearance Requirements",
                    category=ComplianceCategory.CERTIFICATION,
                    description="Personnel security clearance for classified projects",
                    mandatory=False,  # Depends on project
                    risk_level=RiskLevel.CRITICAL,
                    estimated_effort_hours=20,
                    estimated_cost=2000.0,
                    buffer_days=120,  # Can take months
                    step_by_step_guide=[
                        "Determine clearance level required",
                        "Identify personnel needing clearance",
                        "Initiate security clearance process",
                        "Complete SF-86 forms",
                        "Undergo background investigation"
                    ]
                )
            ],
            "HHS": [
                ComplianceRequirement(
                    requirement_id="human_subjects_irb",
                    title="Human Subjects IRB Approval",
                    category=ComplianceCategory.REGULATORY,
                    description="Institutional Review Board approval for human subjects research",
                    mandatory=False,  # Depends on project
                    risk_level=RiskLevel.HIGH,
                    estimated_effort_hours=20,
                    estimated_cost=1000.0,
                    buffer_days=45,
                    step_by_step_guide=[
                        "Determine if human subjects research is involved",
                        "Prepare IRB protocol",
                        "Submit to institutional IRB",
                        "Address IRB feedback and revisions",
                        "Obtain final IRB approval"
                    ]
                ),
                ComplianceRequirement(
                    requirement_id="logic_model",
                    title="Program Logic Model",
                    category=ComplianceCategory.DOCUMENTATION,
                    description="Detailed program theory and logic model",
                    mandatory=True,
                    risk_level=RiskLevel.MEDIUM,
                    estimated_effort_hours=12,
                    estimated_cost=0.0,
                    buffer_days=7,
                    step_by_step_guide=[
                        "Identify program inputs, activities, and outputs",
                        "Define short-term and long-term outcomes",
                        "Map causal relationships",
                        "Create visual logic model",
                        "Validate with stakeholders"
                    ]
                )
            ],
            "NSF": [
                ComplianceRequirement(
                    requirement_id="broader_impacts",
                    title="Broader Impacts Statement",
                    category=ComplianceCategory.DOCUMENTATION,
                    description="Description of broader impacts on society",
                    mandatory=True,
                    risk_level=RiskLevel.HIGH,
                    estimated_effort_hours=8,
                    estimated_cost=0.0,
                    buffer_days=5,
                    step_by_step_guide=[
                        "Review NSF broader impacts criteria",
                        "Identify societal benefits of research",
                        "Describe educational and outreach activities",
                        "Address diversity and inclusion",
                        "Quantify expected impacts"
                    ],
                    success_factors=[
                        "Clear connection to societal benefit",
                        "Specific, measurable outcomes",
                        "Innovative outreach approaches"
                    ]
                ),
                ComplianceRequirement(
                    requirement_id="data_management_plan",
                    title="Data Management Plan",
                    category=ComplianceCategory.DOCUMENTATION,
                    description="Plan for data sharing and management",
                    mandatory=True,
                    risk_level=RiskLevel.MEDIUM,
                    estimated_effort_hours=6,
                    estimated_cost=0.0,
                    buffer_days=5,
                    step_by_step_guide=[
                        "Identify data types to be generated",
                        "Describe data collection methods",
                        "Plan data storage and backup",
                        "Address data sharing requirements",
                        "Consider privacy and security issues"
                    ]
                )
            ]
        }
        
        return agency_requirements.get(agency_code, [])
    
    def _extract_opportunity_specific_requirements(
        self, opportunity: GovernmentOpportunity
    ) -> List[ComplianceRequirement]:
        """Extract requirements specific to the opportunity."""
        
        opportunity_requirements = []
        
        # Analyze opportunity description for specific requirements
        description = opportunity.description.lower()
        
        # Environmental requirements
        if "environmental" in description or "nepa" in description:
            opportunity_requirements.append(
                ComplianceRequirement(
                    requirement_id="environmental_compliance",
                    title="Environmental Compliance Assessment",
                    category=ComplianceCategory.REGULATORY,
                    description="Environmental impact assessment and compliance",
                    mandatory=True,
                    risk_level=RiskLevel.HIGH,
                    estimated_effort_hours=24,
                    estimated_cost=3000.0,
                    buffer_days=30
                )
            )
        
        # Cybersecurity requirements
        if "cyber" in description or "security" in description or "information" in description:
            opportunity_requirements.append(
                ComplianceRequirement(
                    requirement_id="cybersecurity_plan",
                    title="Cybersecurity Implementation Plan",
                    category=ComplianceCategory.TECHNICAL,
                    description="Cybersecurity controls and implementation plan",
                    mandatory=True,
                    risk_level=RiskLevel.HIGH,
                    estimated_effort_hours=20,
                    estimated_cost=2000.0,
                    buffer_days=14
                )
            )
        
        # Matching funds requirements
        if "match" in description or "cost share" in description or "cost sharing" in description:
            opportunity_requirements.append(
                ComplianceRequirement(
                    requirement_id="matching_funds",
                    title="Matching Funds Documentation",
                    category=ComplianceCategory.FINANCIAL,
                    description="Documentation of matching funds commitment",
                    mandatory=True,
                    risk_level=RiskLevel.HIGH,
                    estimated_effort_hours=8,
                    estimated_cost=0.0,
                    buffer_days=10
                )
            )
        
        return opportunity_requirements
    
    def _adjust_requirements_for_organization(
        self, requirements: List[ComplianceRequirement], organization: OrganizationProfile
    ) -> List[ComplianceRequirement]:
        """Adjust requirements based on organization characteristics."""
        
        adjusted_requirements = []
        
        for req in requirements:
            # Create a copy to avoid modifying original
            adjusted_req = ComplianceRequirement(
                requirement_id=req.requirement_id,
                title=req.title,
                category=req.category,
                description=req.description,
                mandatory=req.mandatory,
                risk_level=req.risk_level,
                estimated_effort_hours=req.estimated_effort_hours,
                estimated_cost=req.estimated_cost,
                prerequisites=req.prerequisites.copy(),
                buffer_days=req.buffer_days,
                step_by_step_guide=req.step_by_step_guide.copy(),
                required_documents=req.required_documents.copy(),
                helpful_resources=req.helpful_resources.copy(),
                failure_risks=req.failure_risks.copy(),
                mitigation_strategies=req.mitigation_strategies.copy()
            )
            
            # Adjust based on organization size
            if organization.revenue:
                if organization.revenue < 500000:  # Small organization
                    # Increase effort estimates and risks for small organizations
                    adjusted_req.estimated_effort_hours = int(adjusted_req.estimated_effort_hours * 1.3)
                    adjusted_req.buffer_days = int(adjusted_req.buffer_days * 1.5)
                    
                    # Add small organization specific guidance
                    if "Consider partnering with larger organization" not in adjusted_req.mitigation_strategies:
                        adjusted_req.mitigation_strategies.append("Consider partnering with larger organization for capacity")
                
                elif organization.revenue > 5000000:  # Large organization
                    # Reduce effort estimates for large organizations with more resources
                    adjusted_req.estimated_effort_hours = int(adjusted_req.estimated_effort_hours * 0.8)
            
            # Adjust based on federal award history
            award_history = organization.component_scores.get("award_history", {})
            if award_history.get("total_awards", 0) > 0:
                # Organization has federal experience, reduce risk and effort
                if adjusted_req.risk_level == RiskLevel.HIGH:
                    adjusted_req.risk_level = RiskLevel.MEDIUM
                elif adjusted_req.risk_level == RiskLevel.MEDIUM:
                    adjusted_req.risk_level = RiskLevel.LOW
                
                adjusted_req.estimated_effort_hours = int(adjusted_req.estimated_effort_hours * 0.9)
                adjusted_req.mitigation_strategies.append("Leverage previous federal grant experience")
            
            adjusted_requirements.append(adjusted_req)
        
        return adjusted_requirements
    
    def _set_requirement_timelines(
        self, requirements: List[ComplianceRequirement], opportunity: GovernmentOpportunity
    ) -> List[ComplianceRequirement]:
        """Set deadlines and recommended start dates for requirements."""
        
        submission_deadline = opportunity.close_date or (datetime.now() + timedelta(days=60))
        
        for req in requirements:
            # Calculate deadline based on buffer days
            req.deadline = submission_deadline - timedelta(days=req.buffer_days)
            
            # Calculate recommended start date based on effort estimate
            effort_days = max(1, req.estimated_effort_hours // 8)  # Convert hours to days
            req.recommended_start_date = req.deadline - timedelta(days=effort_days)
            
            # Adjust for prerequisites
            if req.prerequisites:
                # Find latest prerequisite deadline
                latest_prereq_deadline = req.recommended_start_date
                for prereq_id in req.prerequisites:
                    prereq = next((r for r in requirements if r.requirement_id == prereq_id), None)
                    if prereq and prereq.deadline:
                        if prereq.deadline > latest_prereq_deadline:
                            latest_prereq_deadline = prereq.deadline
                            req.recommended_start_date = latest_prereq_deadline + timedelta(days=1)
        
        return requirements
    
    def _validate_requirements(self, requirements: List[ComplianceRequirement]) -> List[ComplianceRequirement]:
        """Validate and finalize requirements list."""
        
        validated_requirements = []
        
        for req in requirements:
            # Ensure all required fields are present
            if not req.requirement_id or not req.title:
                continue
            
            # Ensure reasonable estimates
            if req.estimated_effort_hours <= 0:
                req.estimated_effort_hours = 4  # Minimum effort
            
            if req.buffer_days <= 0:
                req.buffer_days = 3  # Minimum buffer
            
            # Ensure step-by-step guide exists
            if not req.step_by_step_guide:
                req.step_by_step_guide = [
                    "Review requirement details",
                    "Gather necessary information and documents",
                    "Complete requirement tasks",
                    "Review and validate completion",
                    "Submit or finalize requirement"
                ]
            
            validated_requirements.append(req)
        
        return validated_requirements
    
    async def _generate_compliance_timeline(
        self,
        opportunity: GovernmentOpportunity,
        organization: OrganizationProfile,
        requirements: List[ComplianceRequirement]
    ) -> ComplianceTimeline:
        """Generate comprehensive compliance timeline."""
        
        submission_deadline = opportunity.close_date or (datetime.now() + timedelta(days=60))
        
        # Find earliest recommended start date
        earliest_start = min(req.recommended_start_date for req in requirements 
                           if req.recommended_start_date)
        
        timeline = ComplianceTimeline(
            opportunity_id=opportunity.opportunity_id,
            submission_deadline=submission_deadline,
            recommended_start_date=earliest_start,
            total_preparation_days=(submission_deadline - earliest_start).days
        )
        
        # Generate major milestones
        timeline.milestones = self._generate_timeline_milestones(
            requirements, earliest_start, submission_deadline
        )
        
        # Identify critical deadlines
        timeline.critical_deadlines = self._identify_critical_deadlines(requirements)
        
        # Find critical path
        timeline.critical_path_requirements = self._find_critical_path(requirements)
        
        # Assess timeline risks
        timeline.timeline_risks = self._assess_timeline_risks(
            requirements, timeline.total_preparation_days
        )
        
        # Identify parallel tasks
        timeline.parallel_tasks = self._identify_parallel_tasks(requirements)
        
        # Map sequential dependencies
        timeline.sequential_dependencies = self._map_sequential_dependencies(requirements)
        
        # Calculate recommended buffers
        timeline.recommended_buffers = self._calculate_recommended_buffers(
            requirements, timeline.total_preparation_days
        )
        
        # Generate contingency plans
        timeline.contingency_plans = self._generate_contingency_plans(
            requirements, timeline.timeline_risks
        )
        
        return timeline
    
    def _generate_timeline_milestones(
        self, requirements: List[ComplianceRequirement], start_date: datetime, end_date: datetime
    ) -> Dict[str, datetime]:
        """Generate major timeline milestones."""
        
        total_days = (end_date - start_date).days
        
        milestones = {}
        
        # Registration milestone (25% through timeline)
        reg_date = start_date + timedelta(days=int(total_days * 0.25))
        milestones["Registration Complete"] = reg_date
        
        # Documentation milestone (60% through timeline)
        doc_date = start_date + timedelta(days=int(total_days * 0.60))
        milestones["Documentation Complete"] = doc_date
        
        # Review milestone (80% through timeline)
        review_date = start_date + timedelta(days=int(total_days * 0.80))
        milestones["Internal Review Complete"] = review_date
        
        # Final submission milestone
        milestones["Final Submission"] = end_date
        
        return milestones
    
    def _identify_critical_deadlines(self, requirements: List[ComplianceRequirement]) -> List[Dict[str, Any]]:
        """Identify critical deadlines in the timeline."""
        
        critical_deadlines = []
        
        for req in requirements:
            if req.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] and req.deadline:
                critical_deadlines.append({
                    "requirement_id": req.requirement_id,
                    "title": req.title,
                    "deadline": req.deadline,
                    "risk_level": req.risk_level.value,
                    "buffer_days": req.buffer_days
                })
        
        return sorted(critical_deadlines, key=lambda x: x["deadline"])
    
    def _find_critical_path(self, requirements: List[ComplianceRequirement]) -> List[str]:
        """Find critical path through requirements."""
        
        # Simplified critical path - requirements with prerequisites that determine timeline
        critical_path = []
        
        # Start with requirements that have no prerequisites
        current_requirements = [req for req in requirements if not req.prerequisites]
        
        while current_requirements:
            # Find requirement with longest timeline impact
            longest_req = max(current_requirements, 
                            key=lambda x: x.estimated_effort_hours + x.buffer_days)
            critical_path.append(longest_req.requirement_id)
            
            # Find requirements that depend on this one
            current_requirements = [req for req in requirements 
                                  if longest_req.requirement_id in req.prerequisites]
        
        return critical_path
    
    def _assess_timeline_risks(self, requirements: List[ComplianceRequirement], total_days: int) -> List[str]:
        """Assess risks to the timeline."""
        
        risks = []
        
        # Time pressure risk
        if total_days < 30:
            risks.append("Insufficient preparation time - high risk of rushed compliance")
        elif total_days < 60:
            risks.append("Limited preparation time - requires focused effort")
        
        # Complex requirement risk
        complex_reqs = [req for req in requirements if req.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        if len(complex_reqs) > 3:
            risks.append("Multiple complex requirements create coordination challenges")
        
        # Dependency risk
        prereq_chains = [req for req in requirements if len(req.prerequisites) > 1]
        if len(prereq_chains) > 2:
            risks.append("Complex dependency chains create schedule risks")
        
        # External dependency risk
        external_reqs = [req for req in requirements if req.estimated_cost > 0]
        if len(external_reqs) > 0:
            risks.append("External dependencies (consultants, certifications) create schedule risks")
        
        return risks
    
    def _identify_parallel_tasks(self, requirements: List[ComplianceRequirement]) -> List[List[str]]:
        """Identify tasks that can be performed in parallel."""
        
        parallel_groups = []
        processed_reqs = set()
        
        for req in requirements:
            if req.requirement_id in processed_reqs:
                continue
            
            # Find requirements with no mutual dependencies
            parallel_group = [req.requirement_id]
            processed_reqs.add(req.requirement_id)
            
            for other_req in requirements:
                if (other_req.requirement_id not in processed_reqs and
                    req.requirement_id not in other_req.prerequisites and
                    other_req.requirement_id not in req.prerequisites):
                    parallel_group.append(other_req.requirement_id)
                    processed_reqs.add(other_req.requirement_id)
            
            if len(parallel_group) > 1:
                parallel_groups.append(parallel_group)
        
        return parallel_groups
    
    def _map_sequential_dependencies(self, requirements: List[ComplianceRequirement]) -> List[Tuple[str, str]]:
        """Map sequential dependencies between requirements."""
        
        dependencies = []
        
        for req in requirements:
            for prereq_id in req.prerequisites:
                dependencies.append((prereq_id, req.requirement_id))
        
        return dependencies
    
    def _calculate_recommended_buffers(
        self, requirements: List[ComplianceRequirement], total_days: int
    ) -> Dict[str, int]:
        """Calculate recommended buffer times for requirements."""
        
        buffers = {}
        
        # Base buffer calculation
        time_pressure_factor = 1.0
        if total_days < 30:
            time_pressure_factor = 0.5  # Reduce buffers when time is short
        elif total_days > 90:
            time_pressure_factor = 1.5  # Increase buffers when time allows
        
        for req in requirements:
            base_buffer = req.buffer_days
            
            # Adjust buffer based on risk level
            risk_multiplier = {
                RiskLevel.LOW: 0.8,
                RiskLevel.MEDIUM: 1.0,
                RiskLevel.HIGH: 1.3,
                RiskLevel.CRITICAL: 1.5
            }
            
            adjusted_buffer = int(base_buffer * risk_multiplier[req.risk_level] * time_pressure_factor)
            buffers[req.requirement_id] = max(1, adjusted_buffer)  # Minimum 1 day buffer
        
        return buffers
    
    def _generate_contingency_plans(
        self, requirements: List[ComplianceRequirement], timeline_risks: List[str]
    ) -> List[str]:
        """Generate contingency plans for timeline risks."""
        
        contingency_plans = []
        
        # General contingency strategies
        contingency_plans.extend([
            "Identify requirements that can be expedited with additional resources",
            "Prepare alternative approaches for complex requirements",
            "Establish relationships with external consultants for emergency support",
            "Create detailed daily task lists for final weeks"
        ])
        
        # Risk-specific contingencies
        for risk in timeline_risks:
            if "time pressure" in risk.lower():
                contingency_plans.append("Focus on mandatory requirements first, defer optional items")
            elif "complex requirements" in risk.lower():
                contingency_plans.append("Assign dedicated resources to each complex requirement")
            elif "dependency" in risk.lower():
                contingency_plans.append("Monitor prerequisite completion closely, have backup plans")
            elif "external" in risk.lower():
                contingency_plans.append("Have backup consultants/vendors identified and ready")
        
        return list(set(contingency_plans))  # Remove duplicates
    
    async def _assess_organizational_readiness(
        self, organization: OrganizationProfile, requirements: List[ComplianceRequirement]
    ) -> OrganizationalReadiness:
        """Assess organization's readiness for compliance requirements."""
        
        readiness = OrganizationalReadiness(organization_ein=organization.ein)
        
        # Assess readiness by category
        readiness.category_readiness = self._assess_category_readiness(
            organization, requirements
        )
        
        # Calculate overall readiness score
        if readiness.category_readiness:
            readiness.overall_readiness_score = sum(readiness.category_readiness.values()) / len(readiness.category_readiness)
        
        # Identify organizational strengths
        readiness.organizational_strengths = self._identify_organizational_strengths(organization)
        
        # Identify compliance gaps
        readiness.compliance_gaps = self._identify_compliance_gaps(
            organization, requirements, readiness.category_readiness
        )
        
        # Generate investment recommendations
        readiness.recommended_investments = self._generate_investment_recommendations(
            organization, requirements, readiness.compliance_gaps
        )
        
        # Calculate resource requirements
        readiness.estimated_staff_hours = sum(req.estimated_effort_hours for req in requirements)
        readiness.estimated_budget_required = sum(req.estimated_cost for req in requirements)
        
        # Identify external expertise needed
        readiness.external_expertise_needed = self._identify_external_expertise_needed(
            requirements, readiness.compliance_gaps
        )
        
        # Assess compliance track record
        readiness.previous_compliance_experience = self._assess_previous_experience(organization)
        readiness.compliance_track_record = self._assess_compliance_track_record(organization)
        
        return readiness
    
    def _assess_category_readiness(
        self, organization: OrganizationProfile, requirements: List[ComplianceRequirement]
    ) -> Dict[ComplianceCategory, float]:
        """Assess readiness by compliance category."""
        
        category_readiness = {}
        
        # Group requirements by category
        category_groups = {}
        for req in requirements:
            if req.category not in category_groups:
                category_groups[req.category] = []
            category_groups[req.category].append(req)
        
        # Assess each category
        for category, reqs in category_groups.items():
            if category == ComplianceCategory.REGISTRATION:
                # Registration readiness based on organization maturity
                if organization.revenue and organization.revenue > 1000000:
                    category_readiness[category] = 0.8
                elif organization.revenue and organization.revenue > 100000:
                    category_readiness[category] = 0.6
                else:
                    category_readiness[category] = 0.4
            
            elif category == ComplianceCategory.FINANCIAL:
                # Financial readiness based on revenue and award history
                base_score = 0.5
                if organization.revenue and organization.revenue > 500000:
                    base_score += 0.2
                
                award_history = organization.component_scores.get("award_history", {})
                if award_history.get("total_awards", 0) > 0:
                    base_score += 0.3
                
                category_readiness[category] = min(1.0, base_score)
            
            elif category == ComplianceCategory.DOCUMENTATION:
                # Documentation readiness based on organizational capacity
                base_score = 0.6
                if organization.revenue and organization.revenue > 2000000:
                    base_score += 0.2
                
                category_readiness[category] = min(1.0, base_score)
            
            elif category == ComplianceCategory.TECHNICAL:
                # Technical readiness - assumes moderate capability
                category_readiness[category] = 0.6
            
            else:
                # Default readiness for other categories
                category_readiness[category] = 0.5
        
        return category_readiness
    
    def _identify_organizational_strengths(self, organization: OrganizationProfile) -> List[str]:
        """Identify organizational strengths for compliance."""
        
        strengths = []
        
        # Revenue-based strengths
        if organization.revenue:
            if organization.revenue > 5000000:
                strengths.append("Large organizational capacity and resources")
            elif organization.revenue > 1000000:
                strengths.append("Established organization with adequate resources")
            else:
                strengths.append("Small, agile organization")
        
        # Experience-based strengths
        award_history = organization.component_scores.get("award_history", {})
        if award_history.get("total_awards", 0) > 0:
            strengths.append("Previous federal grant experience")
            
            if award_history.get("total_awards", 0) > 5:
                strengths.append("Extensive federal funding track record")
        
        # NTEE-based strengths
        if organization.ntee_code:
            strengths.append(f"Specialized expertise in {organization.ntee_code[0]} sector")
        
        return strengths
    
    def _identify_compliance_gaps(
        self, organization: OrganizationProfile, requirements: List[ComplianceRequirement],
        category_readiness: Dict[ComplianceCategory, float]
    ) -> List[str]:
        """Identify compliance gaps and weaknesses."""
        
        gaps = []
        
        # Identify low readiness categories
        for category, readiness_score in category_readiness.items():
            if readiness_score < 0.6:
                gaps.append(f"Low readiness in {category.value} requirements")
        
        # Organization-specific gaps
        if not organization.revenue or organization.revenue < 500000:
            gaps.append("Limited organizational capacity for complex compliance")
        
        award_history = organization.component_scores.get("award_history", {})
        if award_history.get("total_awards", 0) == 0:
            gaps.append("No previous federal grant compliance experience")
        
        # Requirement-specific gaps
        high_risk_reqs = [req for req in requirements if req.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        if len(high_risk_reqs) > 3:
            gaps.append("Multiple high-risk requirements requiring specialized expertise")
        
        expensive_reqs = [req for req in requirements if req.estimated_cost > 1000]
        if expensive_reqs:
            total_cost = sum(req.estimated_cost for req in expensive_reqs)
            gaps.append(f"Significant external costs required (${total_cost:,.0f})")
        
        return gaps
    
    def _generate_investment_recommendations(
        self, organization: OrganizationProfile, requirements: List[ComplianceRequirement],
        compliance_gaps: List[str]
    ) -> List[str]:
        """Generate investment recommendations to address gaps."""
        
        recommendations = []
        
        # Gap-specific recommendations
        for gap in compliance_gaps:
            if "capacity" in gap.lower():
                recommendations.append("Consider partnering with experienced organization")
            elif "experience" in gap.lower():
                recommendations.append("Hire experienced grants management consultant")
            elif "high-risk" in gap.lower():
                recommendations.append("Invest in specialized compliance expertise")
            elif "cost" in gap.lower():
                recommendations.append("Budget for external compliance support")
        
        # General recommendations
        total_cost = sum(req.estimated_cost for req in requirements)
        if total_cost > 10000:
            recommendations.append("Establish dedicated compliance budget")
        
        total_hours = sum(req.estimated_effort_hours for req in requirements)
        if total_hours > 100:
            recommendations.append("Assign dedicated compliance coordinator")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _identify_external_expertise_needed(
        self, requirements: List[ComplianceRequirement], compliance_gaps: List[str]
    ) -> List[str]:
        """Identify external expertise needed for compliance."""
        
        expertise_needed = []
        
        # Extract from requirements
        for req in requirements:
            if hasattr(req, 'external_expertise_needed'):
                expertise_needed.extend(req.external_expertise_needed)
        
        # Gap-based expertise
        for gap in compliance_gaps:
            if "financial" in gap.lower():
                expertise_needed.append("Grants financial management specialist")
            elif "regulatory" in gap.lower():
                expertise_needed.append("Regulatory compliance consultant")
            elif "technical" in gap.lower():
                expertise_needed.append("Technical compliance specialist")
        
        return list(set(expertise_needed))  # Remove duplicates
    
    def _assess_previous_experience(self, organization: OrganizationProfile) -> List[str]:
        """Assess previous compliance experience."""
        
        experience = []
        
        award_history = organization.component_scores.get("award_history", {})
        if award_history.get("total_awards", 0) > 0:
            experience.append(f"Federal grant management ({award_history.get('total_awards', 0)} awards)")
            
            agencies = award_history.get("unique_agencies", 0)
            if agencies > 0:
                experience.append(f"Multi-agency experience ({agencies} agencies)")
        
        # Add other experience indicators based on available data
        if organization.revenue and organization.revenue > 2000000:
            experience.append("Large organization financial management")
        
        return experience
    
    def _assess_compliance_track_record(self, organization: OrganizationProfile) -> str:
        """Assess overall compliance track record."""
        
        award_history = organization.component_scores.get("award_history", {})
        total_awards = award_history.get("total_awards", 0)
        
        if total_awards >= 10:
            return "excellent"
        elif total_awards >= 5:
            return "good"
        elif total_awards >= 1:
            return "adequate"
        elif organization.revenue and organization.revenue > 1000000:
            return "adequate"  # Large org likely has some compliance experience
        else:
            return "unknown"
    
    # Calculation and analysis methods
    
    def _calculate_compliance_success_probability(
        self, requirements: List[ComplianceRequirement], timeline: ComplianceTimeline,
        organizational_readiness: OrganizationalReadiness
    ) -> float:
        """Calculate probability of successful compliance."""
        
        base_probability = 0.7  # Base 70% success probability
        
        # Organizational readiness factor
        readiness_factor = organizational_readiness.overall_readiness_score * 0.3
        base_probability += readiness_factor
        
        # Timeline pressure factor
        if timeline.total_preparation_days < 30:
            base_probability -= 0.2
        elif timeline.total_preparation_days < 60:
            base_probability -= 0.1
        elif timeline.total_preparation_days > 120:
            base_probability += 0.1
        
        # Requirement complexity factor
        high_risk_reqs = len([req for req in requirements if req.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])
        complexity_penalty = min(0.3, high_risk_reqs * 0.05)
        base_probability -= complexity_penalty
        
        # Experience bonus
        if organizational_readiness.compliance_track_record == "excellent":
            base_probability += 0.15
        elif organizational_readiness.compliance_track_record == "good":
            base_probability += 0.1
        elif organizational_readiness.compliance_track_record == "adequate":
            base_probability += 0.05
        
        return max(0.1, min(1.0, base_probability))
    
    def _assess_overall_risk(
        self, opportunity: GovernmentOpportunity, organization: OrganizationProfile,
        requirements: List[ComplianceRequirement], timeline: ComplianceTimeline
    ) -> RiskLevel:
        """Assess overall risk level for compliance."""
        
        risk_score = 0
        
        # Timeline risk
        if timeline.total_preparation_days < 30:
            risk_score += 3
        elif timeline.total_preparation_days < 60:
            risk_score += 2
        elif timeline.total_preparation_days < 90:
            risk_score += 1
        
        # Requirement complexity risk
        critical_reqs = len([req for req in requirements if req.risk_level == RiskLevel.CRITICAL])
        high_reqs = len([req for req in requirements if req.risk_level == RiskLevel.HIGH])
        risk_score += critical_reqs * 2 + high_reqs
        
        # Organizational capacity risk
        if not organization.revenue or organization.revenue < 500000:
            risk_score += 2
        
        # Experience risk
        award_history = organization.component_scores.get("award_history", {})
        if award_history.get("total_awards", 0) == 0:
            risk_score += 2
        
        # Convert score to risk level
        if risk_score >= 8:
            return RiskLevel.CRITICAL
        elif risk_score >= 5:
            return RiskLevel.HIGH
        elif risk_score >= 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_recommended_approach(
        self, opportunity: GovernmentOpportunity, organization: OrganizationProfile,
        roadmap: ComprehensiveComplianceRoadmap
    ) -> str:
        """Generate recommended approach for compliance."""
        
        if roadmap.overall_risk_assessment == RiskLevel.CRITICAL:
            return ("CRITICAL RISK: Consider partnering with experienced organization or "
                   "deferring to future opportunity with more preparation time")
        elif roadmap.overall_risk_assessment == RiskLevel.HIGH:
            return ("HIGH RISK: Require dedicated compliance team and external expertise. "
                   "Consider if organizational capacity is sufficient")
        elif roadmap.overall_risk_assessment == RiskLevel.MEDIUM:
            return ("MODERATE RISK: Assign dedicated compliance coordinator and plan carefully. "
                   "Consider selective external support for complex requirements")
        else:
            return ("LOW RISK: Standard compliance approach with regular monitoring. "
                   "Organization appears well-positioned for success")
    
    def _generate_success_strategies(
        self, opportunity: GovernmentOpportunity, organization: OrganizationProfile,
        roadmap: ComprehensiveComplianceRoadmap
    ) -> List[str]:
        """Generate success strategies for compliance."""
        
        strategies = [
            "Start compliance activities immediately upon decision to apply",
            "Assign clear responsibility for each compliance requirement",
            "Establish regular progress monitoring and review meetings",
            "Maintain detailed documentation of all compliance activities"
        ]
        
        # Risk-specific strategies
        if roadmap.overall_risk_assessment in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            strategies.extend([
                "Engage external compliance expertise early in the process",
                "Build in extra buffer time for all requirements",
                "Have backup plans for critical requirements"
            ])
        
        # Timeline-specific strategies
        if roadmap.timeline and roadmap.timeline.total_preparation_days < 60:
            strategies.extend([
                "Focus on mandatory requirements first",
                "Work on parallel tasks simultaneously",
                "Have team members dedicated to compliance full-time"
            ])
        
        # Organization-specific strategies
        if roadmap.organizational_readiness and roadmap.organizational_readiness.overall_readiness_score < 0.6:
            strategies.extend([
                "Invest in capability building for future opportunities",
                "Partner with experienced organizations",
                "Consider hiring experienced compliance staff"
            ])
        
        return strategies
    
    def _generate_risk_mitigation_plan(
        self, requirements: List[ComplianceRequirement], timeline: ComplianceTimeline,
        organizational_readiness: OrganizationalReadiness
    ) -> List[str]:
        """Generate comprehensive risk mitigation plan."""
        
        mitigation_plan = []
        
        # Extract mitigation strategies from requirements
        for req in requirements:
            mitigation_plan.extend(req.mitigation_strategies)
        
        # Timeline-specific mitigation
        if timeline.total_preparation_days < 60:
            mitigation_plan.extend([
                "Create detailed daily task schedules",
                "Identify tasks that can be expedited with additional resources",
                "Have emergency consultant contacts ready"
            ])
        
        # Organizational capacity mitigation
        if organizational_readiness.overall_readiness_score < 0.6:
            mitigation_plan.extend([
                "Identify partner organizations for capacity support",
                "Pre-qualify external consultants and vendors",
                "Establish emergency budget for compliance support"
            ])
        
        # General mitigation strategies
        mitigation_plan.extend([
            "Monitor all requirement deadlines weekly",
            "Maintain backup documentation for all submissions",
            "Test all system registrations well before deadlines",
            "Have legal counsel review all compliance documentation"
        ])
        
        return list(set(mitigation_plan))  # Remove duplicates
    
    def _calculate_estimated_completion_date(
        self, timeline: ComplianceTimeline, requirements: List[ComplianceRequirement]
    ) -> Optional[datetime]:
        """Calculate estimated completion date for all requirements."""
        
        if not timeline or not requirements:
            return None
        
        # Find latest requirement deadline
        latest_deadline = max(req.deadline for req in requirements if req.deadline)
        
        # Add small buffer for final review and submission
        return latest_deadline + timedelta(days=2)
    
    def _calculate_roadmap_confidence(self, roadmap: ComprehensiveComplianceRoadmap) -> float:
        """Calculate confidence in the roadmap."""
        
        base_confidence = 0.7  # Base confidence
        
        # Data completeness factors
        if roadmap.requirements and len(roadmap.requirements) > 0:
            base_confidence += 0.1
        
        if roadmap.timeline:
            base_confidence += 0.1
        
        if roadmap.organizational_readiness:
            base_confidence += 0.1
        
        # Reduce confidence for high risk scenarios
        if roadmap.overall_risk_assessment == RiskLevel.CRITICAL:
            base_confidence -= 0.2
        elif roadmap.overall_risk_assessment == RiskLevel.HIGH:
            base_confidence -= 0.1
        
        return max(0.3, min(1.0, base_confidence))
    
    def _generate_roadmap_id(self, opportunity_id: str, organization_ein: str) -> str:
        """Generate unique roadmap ID."""
        
        combined = f"{opportunity_id}_{organization_ein}_{datetime.now().isoformat()}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]
    
    # Helper methods for data processing
    
    async def _get_target_opportunities(self, workflow_state) -> List[GovernmentOpportunity]:
        """Get opportunities for roadmap generation."""
        
        # Focus on high-priority opportunities for roadmap generation
        if not workflow_state or not workflow_state.has_processor_succeeded('grants_gov_fetch'):
            return []
        
        opportunities_data = workflow_state.get_processor_data('grants_gov_fetch')
        if not opportunities_data:
            return []
        
        opportunities = []
        for opp_dict in opportunities_data.get('opportunities', [])[:5]:  # Limit to top 5 for detailed analysis
            try:
                opportunity = GovernmentOpportunity(**opp_dict)
                opportunities.append(opportunity)
            except Exception as e:
                self.logger.warning(f"Failed to parse opportunity for roadmap: {e}")
                continue
        
        return opportunities
    
    async def _get_target_organizations(self, workflow_state) -> List[OrganizationProfile]:
        """Get organizations for roadmap generation."""
        
        organizations = []
        
        for processor_name in ['usaspending_fetch', 'propublica_fetch', 'bmf_filter']:
            if workflow_state and workflow_state.has_processor_succeeded(processor_name):
                org_dicts = workflow_state.get_organizations_from_processor(processor_name)
                if org_dicts:
                    for org_dict in org_dicts[:3]:  # Limit to top 3 for detailed analysis
                        try:
                            if isinstance(org_dict, dict):
                                org = OrganizationProfile(**org_dict)
                            else:
                                org = org_dict
                            organizations.append(org)
                        except Exception as e:
                            self.logger.warning(f"Failed to parse organization for roadmap: {e}")
                            continue
                    break
        
        return organizations
    
    # Analysis and summary methods
    
    async def _generate_roadmap_analytics(self, compliance_roadmaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate analytics across all roadmaps."""
        
        if not compliance_roadmaps:
            return {"total_roadmaps": 0}
        
        analytics = {
            "roadmap_overview": {
                "total_roadmaps": len(compliance_roadmaps),
                "avg_success_probability": sum(r["compliance_success_probability"] for r in compliance_roadmaps) / len(compliance_roadmaps),
                "risk_distribution": self._analyze_risk_distribution(compliance_roadmaps),
                "avg_requirements_per_roadmap": sum(len(r["requirements"]) for r in compliance_roadmaps) / len(compliance_roadmaps)
            },
            "timeline_analysis": {
                "avg_preparation_days": self._calculate_avg_preparation_days(compliance_roadmaps),
                "timeline_risk_patterns": self._analyze_timeline_risk_patterns(compliance_roadmaps),
                "critical_path_analysis": self._analyze_critical_paths(compliance_roadmaps)
            },
            "resource_requirements": {
                "total_estimated_hours": sum(r["organizational_readiness"]["estimated_staff_hours"] 
                                           for r in compliance_roadmaps if r["organizational_readiness"]),
                "total_estimated_costs": sum(r["organizational_readiness"]["estimated_budget_required"] 
                                           for r in compliance_roadmaps if r["organizational_readiness"]),
                "common_expertise_needs": self._analyze_common_expertise_needs(compliance_roadmaps)
            }
        }
        
        return analytics
    
    async def _generate_cross_roadmap_insights(self, compliance_roadmaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights across multiple roadmaps."""
        
        insights = {
            "success_patterns": {
                "high_success_factors": self._identify_high_success_factors(compliance_roadmaps),
                "common_risk_factors": self._identify_common_risk_factors(compliance_roadmaps),
                "best_practices": self._identify_best_practices(compliance_roadmaps)
            },
            "efficiency_opportunities": {
                "shared_requirements": self._identify_shared_requirements(compliance_roadmaps),
                "parallel_processing": self._identify_parallel_processing_opportunities(compliance_roadmaps),
                "resource_optimization": self._identify_resource_optimization_opportunities(compliance_roadmaps)
            },
            "strategic_insights": {
                "portfolio_risk_assessment": self._assess_portfolio_risk(compliance_roadmaps),
                "capacity_planning": self._analyze_capacity_planning_needs(compliance_roadmaps),
                "investment_priorities": self._identify_investment_priorities(compliance_roadmaps)
            }
        }
        
        return insights
    
    async def _calculate_compliance_performance_metrics(
        self, compliance_roadmaps: List[Dict[str, Any]], opportunities: List[GovernmentOpportunity],
        organizations: List[OrganizationProfile]
    ) -> Dict[str, Any]:
        """Calculate performance metrics for compliance system."""
        
        if not compliance_roadmaps:
            return {"total_roadmaps": 0}
        
        metrics = {
            "coverage_metrics": {
                "opportunities_covered": len(set(r["opportunity_id"] for r in compliance_roadmaps)),
                "organizations_covered": len(set(r["organization_ein"] for r in compliance_roadmaps)),
                "roadmap_completion_rate": 1.0  # All requested roadmaps were generated
            },
            "quality_metrics": {
                "avg_roadmap_confidence": sum(r["confidence_level"] for r in compliance_roadmaps) / len(compliance_roadmaps),
                "high_confidence_roadmaps": len([r for r in compliance_roadmaps if r["confidence_level"] > 0.8]),
                "comprehensive_roadmaps": len([r for r in compliance_roadmaps if len(r["requirements"]) > 5])
            },
            "feasibility_metrics": {
                "feasible_roadmaps": len([r for r in compliance_roadmaps if r["compliance_success_probability"] > 0.6]),
                "high_risk_roadmaps": len([r for r in compliance_roadmaps if r["overall_risk_assessment"] in ["high", "critical"]]),
                "timeline_feasible": len([r for r in compliance_roadmaps 
                                        if r["timeline"] and r["timeline"]["total_preparation_days"] > 30])
            },
            "resource_metrics": {
                "total_effort_estimated": sum(r["organizational_readiness"]["estimated_staff_hours"] 
                                            for r in compliance_roadmaps if r["organizational_readiness"]),
                "total_costs_estimated": sum(r["organizational_readiness"]["estimated_budget_required"] 
                                           for r in compliance_roadmaps if r["organizational_readiness"]),
                "external_expertise_frequency": self._calculate_external_expertise_frequency(compliance_roadmaps)
            }
        }
        
        return metrics
    
    async def _generate_compliance_strategic_recommendations(
        self, compliance_roadmaps: List[Dict[str, Any]], roadmap_analytics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate strategic recommendations based on compliance analysis."""
        
        recommendations = {
            "immediate_actions": [
                "Focus resources on roadmaps with highest success probability",
                "Address common compliance gaps across multiple opportunities",
                "Establish relationships with key external experts",
                "Implement standardized compliance tracking system"
            ],
            "capability_development": [
                "Invest in internal compliance expertise for frequently needed skills",
                "Develop templates and processes for common requirements",
                "Build relationships with preferred external consultants",
                "Create compliance knowledge base from successful projects"
            ],
            "risk_management": [
                "Establish emergency compliance support budget",
                "Develop contingency plans for high-risk requirements",
                "Create early warning system for timeline pressures",
                "Build buffer time into all compliance schedules"
            ],
            "portfolio_optimization": [
                "Balance high-risk/high-reward with lower-risk opportunities",
                "Sequence applications to build compliance capabilities over time",
                "Consider partnerships to address capacity constraints",
                "Focus on agencies where organization has strongest compliance fit"
            ]
        }
        
        # Analytics-driven recommendations
        if roadmap_analytics.get("roadmap_overview", {}).get("avg_success_probability", 0) < 0.6:
            recommendations["immediate_actions"].append(
                "Reconsider opportunity selection - current portfolio shows low success probability"
            )
        
        avg_prep_days = roadmap_analytics.get("timeline_analysis", {}).get("avg_preparation_days", 0)
        if avg_prep_days < 45:
            recommendations["risk_management"].append(
                "Timeline pressure identified - consider deferring some opportunities for better preparation"
            )
        
        return recommendations
    
    # Analytics helper methods
    
    def _analyze_risk_distribution(self, compliance_roadmaps: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of risk levels."""
        
        distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        for roadmap in compliance_roadmaps:
            risk_level = roadmap["overall_risk_assessment"]
            distribution[risk_level] += 1
        
        return distribution
    
    def _calculate_avg_preparation_days(self, compliance_roadmaps: List[Dict[str, Any]]) -> float:
        """Calculate average preparation days across roadmaps."""
        
        prep_days = []
        
        for roadmap in compliance_roadmaps:
            if roadmap["timeline"] and roadmap["timeline"]["total_preparation_days"]:
                prep_days.append(roadmap["timeline"]["total_preparation_days"])
        
        return sum(prep_days) / len(prep_days) if prep_days else 0
    
    def _analyze_timeline_risk_patterns(self, compliance_roadmaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in timeline risks."""
        
        risk_patterns = {
            "short_timeline_count": 0,
            "complex_dependency_count": 0,
            "external_dependency_count": 0
        }
        
        for roadmap in compliance_roadmaps:
            if roadmap["timeline"]:
                timeline = roadmap["timeline"]
                if timeline["total_preparation_days"] < 45:
                    risk_patterns["short_timeline_count"] += 1
                
                timeline_risks = timeline.get("timeline_risks", [])
                if any("dependency" in risk.lower() for risk in timeline_risks):
                    risk_patterns["complex_dependency_count"] += 1
                if any("external" in risk.lower() for risk in timeline_risks):
                    risk_patterns["external_dependency_count"] += 1
        
        return risk_patterns
    
    def _analyze_critical_paths(self, compliance_roadmaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze critical paths across roadmaps."""
        
        critical_path_analysis = {
            "avg_critical_path_length": 0,
            "common_critical_requirements": {},
            "bottleneck_requirements": []
        }
        
        critical_paths = []
        requirement_counts = {}
        
        for roadmap in compliance_roadmaps:
            if roadmap["timeline"] and roadmap["timeline"]["critical_path_requirements"]:
                critical_path = roadmap["timeline"]["critical_path_requirements"]
                critical_paths.append(len(critical_path))
                
                for req_id in critical_path:
                    requirement_counts[req_id] = requirement_counts.get(req_id, 0) + 1
        
        if critical_paths:
            critical_path_analysis["avg_critical_path_length"] = sum(critical_paths) / len(critical_paths)
        
        # Identify most common critical requirements
        if requirement_counts:
            sorted_reqs = sorted(requirement_counts.items(), key=lambda x: x[1], reverse=True)
            critical_path_analysis["common_critical_requirements"] = dict(sorted_reqs[:5])
            critical_path_analysis["bottleneck_requirements"] = [req for req, count in sorted_reqs if count > 1]
        
        return critical_path_analysis
    
    def _analyze_common_expertise_needs(self, compliance_roadmaps: List[Dict[str, Any]]) -> List[str]:
        """Analyze common external expertise needs."""
        
        expertise_counts = {}
        
        for roadmap in compliance_roadmaps:
            if roadmap["organizational_readiness"] and roadmap["organizational_readiness"]["external_expertise_needed"]:
                for expertise in roadmap["organizational_readiness"]["external_expertise_needed"]:
                    expertise_counts[expertise] = expertise_counts.get(expertise, 0) + 1
        
        # Return expertise needed by multiple roadmaps
        common_expertise = [expertise for expertise, count in expertise_counts.items() if count > 1]
        return sorted(common_expertise, key=lambda x: expertise_counts[x], reverse=True)
    
    def _identify_high_success_factors(self, compliance_roadmaps: List[Dict[str, Any]]) -> List[str]:
        """Identify factors associated with high success probability."""
        
        high_success_roadmaps = [r for r in compliance_roadmaps if r["compliance_success_probability"] > 0.75]
        
        success_factors = []
        
        for roadmap in high_success_roadmaps:
            if roadmap["organizational_readiness"]:
                readiness = roadmap["organizational_readiness"]
                if readiness["overall_readiness_score"] > 0.7:
                    success_factors.append("High organizational readiness")
                if readiness["compliance_track_record"] in ["excellent", "good"]:
                    success_factors.append("Strong compliance track record")
            
            if roadmap["timeline"] and roadmap["timeline"]["total_preparation_days"] > 60:
                success_factors.append("Adequate preparation time")
            
            if roadmap["overall_risk_assessment"] in ["low", "medium"]:
                success_factors.append("Manageable risk level")
        
        # Count frequency and return most common
        factor_counts = {}
        for factor in success_factors:
            factor_counts[factor] = factor_counts.get(factor, 0) + 1
        
        return sorted(factor_counts.keys(), key=lambda x: factor_counts[x], reverse=True)[:5]
    
    def _identify_common_risk_factors(self, compliance_roadmaps: List[Dict[str, Any]]) -> List[str]:
        """Identify common risk factors across roadmaps."""
        
        risk_factors = []
        
        for roadmap in compliance_roadmaps:
            if roadmap["overall_risk_assessment"] in ["high", "critical"]:
                if roadmap["timeline"] and roadmap["timeline"]["total_preparation_days"] < 45:
                    risk_factors.append("Insufficient preparation time")
                
                if roadmap["organizational_readiness"] and roadmap["organizational_readiness"]["overall_readiness_score"] < 0.6:
                    risk_factors.append("Low organizational readiness")
                
                high_risk_reqs = len([req for req in roadmap["requirements"] 
                                    if req["risk_level"] in ["high", "critical"]])
                if high_risk_reqs > 3:
                    risk_factors.append("Multiple high-risk requirements")
        
        # Count frequency and return most common
        factor_counts = {}
        for factor in risk_factors:
            factor_counts[factor] = factor_counts.get(factor, 0) + 1
        
        return sorted(factor_counts.keys(), key=lambda x: factor_counts[x], reverse=True)[:5]
    
    def _identify_best_practices(self, compliance_roadmaps: List[Dict[str, Any]]) -> List[str]:
        """Identify best practices from successful roadmaps."""
        
        return [
            "Start compliance activities at least 60 days before deadline",
            "Assign dedicated compliance coordinator for complex opportunities",
            "Engage external expertise early for specialized requirements",
            "Build in 20% buffer time for all requirement estimates",
            "Maintain detailed documentation throughout the process",
            "Test all system registrations and submissions before deadlines",
            "Establish regular progress review meetings",
            "Have contingency plans for critical requirements"
        ]
    
    def _identify_shared_requirements(self, compliance_roadmaps: List[Dict[str, Any]]) -> List[str]:
        """Identify requirements that appear across multiple roadmaps."""
        
        requirement_counts = {}
        
        for roadmap in compliance_roadmaps:
            for req in roadmap["requirements"]:
                req_id = req["requirement_id"]
                requirement_counts[req_id] = requirement_counts.get(req_id, 0) + 1
        
        # Return requirements that appear in multiple roadmaps
        shared_requirements = [req_id for req_id, count in requirement_counts.items() if count > 1]
        return sorted(shared_requirements, key=lambda x: requirement_counts[x], reverse=True)
    
    def _identify_parallel_processing_opportunities(self, compliance_roadmaps: List[Dict[str, Any]]) -> List[str]:
        """Identify opportunities for parallel processing."""
        
        opportunities = [
            "Process SAM.gov and Grants.gov registrations can be done for all opportunities simultaneously",
            "Base documentation templates can be developed once and reused",
            "External consultant relationships can serve multiple opportunities",
            "Internal compliance training can benefit all application teams"
        ]
        
        return opportunities
    
    def _identify_resource_optimization_opportunities(self, compliance_roadmaps: List[Dict[str, Any]]) -> List[str]:
        """Identify opportunities for resource optimization."""
        
        return [
            "Establish preferred consultant relationships for volume pricing",
            "Develop internal compliance capabilities to reduce external costs",
            "Create standardized templates and processes to reduce effort",
            "Implement compliance tracking system to improve efficiency",
            "Schedule applications to balance workload over time"
        ]
    
    def _assess_portfolio_risk(self, compliance_roadmaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess risk across the entire portfolio of roadmaps."""
        
        risk_assessment = {
            "overall_portfolio_risk": "medium",
            "risk_concentration": self._analyze_risk_distribution(compliance_roadmaps),
            "capacity_overload_risk": "low",
            "timeline_conflict_risk": "low"
        }
        
        # Assess overall portfolio risk
        high_risk_count = risk_assessment["risk_concentration"].get("high", 0) + risk_assessment["risk_concentration"].get("critical", 0)
        total_roadmaps = len(compliance_roadmaps)
        
        if high_risk_count / total_roadmaps > 0.5:
            risk_assessment["overall_portfolio_risk"] = "high"
        elif high_risk_count / total_roadmaps > 0.3:
            risk_assessment["overall_portfolio_risk"] = "medium"
        else:
            risk_assessment["overall_portfolio_risk"] = "low"
        
        # Assess capacity overload risk
        total_hours = sum(r["organizational_readiness"]["estimated_staff_hours"] 
                         for r in compliance_roadmaps if r["organizational_readiness"])
        if total_hours > 500:  # Rough threshold for capacity concerns
            risk_assessment["capacity_overload_risk"] = "high"
        elif total_hours > 200:
            risk_assessment["capacity_overload_risk"] = "medium"
        
        return risk_assessment
    
    def _analyze_capacity_planning_needs(self, compliance_roadmaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze capacity planning needs."""
        
        return {
            "total_staff_hours_needed": sum(r["organizational_readiness"]["estimated_staff_hours"] 
                                          for r in compliance_roadmaps if r["organizational_readiness"]),
            "peak_period_analysis": "Detailed timeline analysis would identify peak resource periods",
            "skill_requirements": self._analyze_common_expertise_needs(compliance_roadmaps),
            "external_budget_needed": sum(r["organizational_readiness"]["estimated_budget_required"] 
                                        for r in compliance_roadmaps if r["organizational_readiness"])
        }
    
    def _identify_investment_priorities(self, compliance_roadmaps: List[Dict[str, Any]]) -> List[str]:
        """Identify investment priorities based on roadmap analysis."""
        
        priorities = [
            "Compliance project management system and tracking tools",
            "Internal grants management training and certification",
            "Preferred vendor relationships for common external expertise",
            "Template library for standard compliance requirements"
        ]
        
        # Add priorities based on analysis
        common_expertise = self._analyze_common_expertise_needs(compliance_roadmaps)
        if common_expertise:
            priorities.append(f"Internal capability development in: {', '.join(common_expertise[:3])}")
        
        return priorities
    
    def _calculate_external_expertise_frequency(self, compliance_roadmaps: List[Dict[str, Any]]) -> float:
        """Calculate frequency of external expertise requirements."""
        
        roadmaps_needing_external = len([r for r in compliance_roadmaps 
                                       if r["organizational_readiness"] and 
                                       r["organizational_readiness"]["external_expertise_needed"]])
        
        return roadmaps_needing_external / len(compliance_roadmaps) if compliance_roadmaps else 0
    
    def _calculate_overall_roadmap_confidence(self, compliance_roadmaps: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence across all roadmaps."""
        
        if not compliance_roadmaps:
            return 0.0
        
        confidence_scores = [r["confidence_level"] for r in compliance_roadmaps]
        return sum(confidence_scores) / len(confidence_scores)
    
    # Initialize compliance templates and knowledge base
    
    def _initialize_compliance_templates(self) -> Dict[str, Any]:
        """Initialize compliance templates and patterns."""
        
        return {
            "base_federal": {
                "registrations": ["sam_gov", "grants_gov"],
                "documentation": ["sf424", "budget_narrative", "project_description"],
                "certifications": ["nonprofit_status", "audit_compliance"]
            },
            "agency_specific": {
                "DOD": {
                    "additional_reqs": ["dcaa_compliance", "security_clearance"],
                    "specialized_docs": ["technical_proposal", "cost_proposal"]
                },
                "HHS": {
                    "additional_reqs": ["human_subjects_irb", "logic_model"],
                    "specialized_docs": ["evaluation_plan", "sustainability_plan"]
                },
                "NSF": {
                    "additional_reqs": ["broader_impacts", "data_management_plan"],
                    "specialized_docs": ["research_plan", "facilities_equipment"]
                }
            }
        }
    
    def _initialize_agency_requirements(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize agency-specific requirement patterns."""
        
        return {
            "tier_1_agencies": {
                "base_complexity": "high",
                "typical_requirements": 8,
                "specialized_compliance": True
            },
            "tier_2_agencies": {
                "base_complexity": "medium",
                "typical_requirements": 6,
                "specialized_compliance": True
            },
            "tier_3_agencies": {
                "base_complexity": "medium",
                "typical_requirements": 5,
                "specialized_compliance": False
            }
        }
    
    def _initialize_risk_patterns(self) -> Dict[str, Any]:
        """Initialize risk assessment patterns."""
        
        return {
            "timeline_risks": {
                "critical": {"days": 15, "multiplier": 2.0},
                "high": {"days": 30, "multiplier": 1.5},
                "medium": {"days": 60, "multiplier": 1.2},
                "low": {"days": 90, "multiplier": 1.0}
            },
            "complexity_risks": {
                "critical_req_count": {"threshold": 3, "multiplier": 1.8},
                "high_req_count": {"threshold": 5, "multiplier": 1.4},
                "total_req_count": {"threshold": 10, "multiplier": 1.2}
            },
            "organizational_risks": {
                "no_experience": {"multiplier": 1.6},
                "limited_capacity": {"multiplier": 1.4},
                "adequate_capacity": {"multiplier": 1.0},
                "high_capacity": {"multiplier": 0.8}
            }
        }


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return ComplianceRoadmapGenerator()