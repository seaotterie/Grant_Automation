#!/usr/bin/env python3
"""
Government-Specific Research Integration - Phase 5 Cross-System Integration
Enhanced research capabilities specifically designed for government opportunities.

This system provides specialized research and analysis for government grants, agencies,
compliance requirements, and strategic positioning for federal funding success.
"""

import asyncio
import time
import json
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.core.government_models import GovernmentOpportunity, GovernmentOpportunityMatch
from src.analysis.ai_lite_researcher import AILiteResearcher
from src.analysis.ai_heavy_dossier_builder import AIHeavyDossierBuilder


class GovernmentAgencyType(Enum):
    """Types of government agencies for specialized research."""
    CABINET_LEVEL = "cabinet_level"       # DOE, DOD, HHS, etc.
    INDEPENDENT = "independent"           # NSF, EPA, etc.
    SUB_AGENCY = "sub_agency"            # NIH, CDC, etc.
    COMMISSION = "commission"            # FCC, SEC, etc.
    ADMINISTRATION = "administration"    # SBA, GSA, etc.


class ComplianceComplexity(Enum):
    """Complexity levels for compliance requirements."""
    LOW = "low"           # Standard nonprofit eligibility
    MEDIUM = "medium"     # Additional documentation required
    HIGH = "high"         # Complex regulatory compliance
    CRITICAL = "critical" # Specialized regulatory expertise required


@dataclass
class AgencyIntelligence:
    """Comprehensive intelligence about a government agency."""
    agency_code: str
    agency_name: str
    agency_type: GovernmentAgencyType
    
    # Funding characteristics
    total_opportunities: int = 0
    average_award_size: float = 0.0
    funding_focus_areas: List[str] = field(default_factory=list)
    geographic_preferences: List[str] = field(default_factory=list)
    
    # Historical patterns
    funding_trends: Dict[str, Any] = field(default_factory=dict)
    success_factors: List[str] = field(default_factory=list)
    common_rejection_reasons: List[str] = field(default_factory=list)
    
    # Strategic insights
    key_personnel: List[Dict[str, str]] = field(default_factory=list)
    preferred_partnerships: List[str] = field(default_factory=list)
    strategic_priorities: List[str] = field(default_factory=list)
    
    # Compliance requirements
    compliance_complexity: ComplianceComplexity = ComplianceComplexity.MEDIUM
    required_certifications: List[str] = field(default_factory=list)
    documentation_requirements: List[str] = field(default_factory=list)


@dataclass
class ComplianceRoadmap:
    """Roadmap for meeting government compliance requirements."""
    opportunity_id: str
    agency_code: str
    complexity_level: ComplianceComplexity
    
    # Compliance checklist
    required_documents: List[Dict[str, str]] = field(default_factory=list)  # doc_type, description, deadline
    certifications_needed: List[Dict[str, str]] = field(default_factory=list)  # cert_type, description, timeline
    registration_requirements: List[Dict[str, str]] = field(default_factory=list)  # system, description, timeline
    
    # Timeline and milestones
    preparation_timeline: Dict[str, str] = field(default_factory=dict)  # milestone: deadline
    critical_deadlines: List[Dict[str, Any]] = field(default_factory=list)
    recommended_start_date: Optional[datetime] = None
    
    # Risk assessment
    compliance_risks: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)
    success_probability: float = 0.0


@dataclass
class GovernmentResearchInsights:
    """Comprehensive research insights for government opportunities."""
    opportunity_id: str
    agency_intelligence: AgencyIntelligence
    compliance_roadmap: ComplianceRoadmap
    
    # Strategic analysis
    competitive_landscape: Dict[str, Any] = field(default_factory=dict)
    positioning_strategy: List[str] = field(default_factory=list)
    partnership_recommendations: List[str] = field(default_factory=list)
    
    # Implementation guidance
    technical_requirements: List[str] = field(default_factory=list)
    resource_allocation_plan: Dict[str, Any] = field(default_factory=dict)
    success_metrics: List[str] = field(default_factory=list)
    
    # Risk analysis
    funding_risks: List[str] = field(default_factory=list)
    implementation_risks: List[str] = field(default_factory=list)
    mitigation_plan: List[str] = field(default_factory=list)


class GovernmentResearchIntegration(BaseProcessor):
    """
    Government-Specific Research Integration Processor
    
    Phase 5 Cross-System Integration Features:
    
    ## Government Agency Intelligence
    - Comprehensive agency profiling and analysis
    - Funding pattern recognition and trend analysis
    - Key personnel and contact intelligence
    - Strategic priority identification
    
    ## Compliance Roadmap Generation
    - Automated compliance requirement analysis
    - Timeline and milestone planning
    - Risk assessment and mitigation strategies
    - Documentation and certification tracking
    
    ## Strategic Positioning Intelligence
    - Competitive landscape analysis
    - Partnership opportunity identification
    - Technical requirement assessment
    - Success factor optimization
    
    ## Cross-System Research Integration
    - Integration with AI Lite and AI Heavy research
    - Entity-based government data organization
    - Historical success pattern analysis
    - Real-time intelligence updates
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="government_research_integration",
            description="Government-specific research and compliance intelligence",
            version="1.0.0",
            dependencies=["ai_lite_researcher", "workflow_aware_government_scorer"],
            estimated_duration=180,  # 3 minutes for comprehensive government research
            requires_network=True,   # For agency intelligence updates
            requires_api_key=True,   # For enhanced research capabilities
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Initialize research components
        self.ai_lite_researcher = AILiteResearcher()
        self.ai_heavy_dossier = AIHeavyDossierBuilder()
        
        # Government agency database
        self.agency_database = self._initialize_agency_database()
        
        # Compliance frameworks
        self.compliance_frameworks = self._initialize_compliance_frameworks()
        
        # Government-specific research weights
        self.research_weights = {
            "agency_intelligence": 0.25,      # Agency-specific insights
            "compliance_analysis": 0.30,      # Compliance and regulatory
            "strategic_positioning": 0.25,    # Competitive positioning
            "implementation_feasibility": 0.20 # Practical implementation
        }
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute government-specific research integration."""
        start_time = time.time()
        
        try:
            # Get government opportunities for research
            opportunities = await self._get_government_opportunities_for_research(workflow_state)
            organizations = await self._get_organizations(workflow_state)
            
            if not opportunities:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No government opportunities found for research integration"]
                )
            
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No organizations found for research integration"]
                )
            
            self.logger.info(f"Conducting government research for {len(opportunities)} opportunities and {len(organizations)} organizations")
            
            # Generate comprehensive research insights
            research_results = []
            total_combinations = len(opportunities) * len(organizations)
            processed = 0
            
            for opportunity in opportunities:
                for organization in organizations:
                    processed += 1
                    self._update_progress(
                        processed,
                        total_combinations,
                        f"Researching {opportunity.title[:40]}... for {organization.name[:25]}..."
                    )
                    
                    # Generate comprehensive research insights
                    research_insights = await self._generate_government_research_insights(
                        opportunity, organization, config
                    )
                    
                    if research_insights:
                        research_results.append({
                            "opportunity_id": opportunity.opportunity_id,
                            "organization_ein": organization.ein,
                            "research_insights": research_insights.__dict__
                        })
            
            # Generate cross-agency intelligence
            agency_intelligence_summary = await self._generate_agency_intelligence_summary(
                opportunities, research_results
            )
            
            # Generate compliance landscape analysis
            compliance_landscape = await self._generate_compliance_landscape_analysis(
                research_results
            )
            
            # Calculate government research performance metrics
            performance_metrics = await self._calculate_government_research_metrics(
                research_results, opportunities, organizations
            )
            
            # Prepare comprehensive results
            result_data = {
                "government_research_insights": research_results,
                "agency_intelligence_summary": agency_intelligence_summary,
                "compliance_landscape_analysis": compliance_landscape,
                "performance_metrics": performance_metrics,
                "total_research_combinations": len(research_results),
                "unique_agencies_analyzed": len(set(r["research_insights"]["agency_intelligence"]["agency_code"] 
                                                  for r in research_results)),
                "compliance_complexity_distribution": self._analyze_compliance_distribution(research_results)
            }
            
            execution_time = time.time() - start_time
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "research_scope": "government_specific",
                    "agency_intelligence_enabled": True,
                    "compliance_roadmaps_generated": len(research_results)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Government research integration failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"Government research integration failed: {str(e)}"]
            )
    
    async def _generate_government_research_insights(
        self,
        opportunity: GovernmentOpportunity,
        organization: OrganizationProfile,
        config: ProcessorConfig
    ) -> Optional[GovernmentResearchInsights]:
        """Generate comprehensive government research insights."""
        
        try:
            # Get agency intelligence
            agency_intelligence = await self._analyze_agency_intelligence(
                opportunity.agency_code, opportunity
            )
            
            # Generate compliance roadmap
            compliance_roadmap = await self._generate_compliance_roadmap(
                opportunity, organization, agency_intelligence
            )
            
            # Create comprehensive research insights
            research_insights = GovernmentResearchInsights(
                opportunity_id=opportunity.opportunity_id,
                agency_intelligence=agency_intelligence,
                compliance_roadmap=compliance_roadmap
            )
            
            # Analyze competitive landscape
            research_insights.competitive_landscape = await self._analyze_competitive_landscape(
                opportunity, organization, agency_intelligence
            )
            
            # Generate positioning strategy
            research_insights.positioning_strategy = await self._generate_positioning_strategy(
                opportunity, organization, agency_intelligence
            )
            
            # Generate partnership recommendations
            research_insights.partnership_recommendations = await self._generate_partnership_recommendations(
                opportunity, organization, agency_intelligence
            )
            
            # Analyze technical requirements
            research_insights.technical_requirements = await self._analyze_technical_requirements(
                opportunity, organization
            )
            
            # Create resource allocation plan
            research_insights.resource_allocation_plan = await self._create_resource_allocation_plan(
                opportunity, organization, compliance_roadmap
            )
            
            # Define success metrics
            research_insights.success_metrics = await self._define_success_metrics(
                opportunity, organization, agency_intelligence
            )
            
            # Conduct risk analysis
            research_insights.funding_risks = await self._analyze_funding_risks(
                opportunity, agency_intelligence
            )
            
            research_insights.implementation_risks = await self._analyze_implementation_risks(
                opportunity, organization
            )
            
            research_insights.mitigation_plan = await self._create_mitigation_plan(
                research_insights.funding_risks + research_insights.implementation_risks,
                opportunity, organization
            )
            
            return research_insights
            
        except Exception as e:
            self.logger.warning(f"Failed to generate research insights for {opportunity.opportunity_id}: {e}")
            return None
    
    async def _analyze_agency_intelligence(
        self, agency_code: str, opportunity: GovernmentOpportunity
    ) -> AgencyIntelligence:
        """Analyze comprehensive intelligence about a government agency."""
        
        # Get base agency information
        base_agency_info = self.agency_database.get(agency_code, {})
        
        # Create agency intelligence
        agency_intelligence = AgencyIntelligence(
            agency_code=agency_code,
            agency_name=base_agency_info.get("name", f"Agency {agency_code}"),
            agency_type=GovernmentAgencyType(base_agency_info.get("type", "independent"))
        )
        
        # Analyze funding characteristics
        agency_intelligence.total_opportunities = base_agency_info.get("total_opportunities", 0)
        agency_intelligence.average_award_size = base_agency_info.get("average_award_size", 0.0)
        agency_intelligence.funding_focus_areas = base_agency_info.get("focus_areas", [])
        agency_intelligence.geographic_preferences = base_agency_info.get("geographic_preferences", [])
        
        # Historical patterns
        agency_intelligence.funding_trends = base_agency_info.get("funding_trends", {})
        agency_intelligence.success_factors = base_agency_info.get("success_factors", [])
        agency_intelligence.common_rejection_reasons = base_agency_info.get("rejection_reasons", [])
        
        # Strategic insights
        agency_intelligence.key_personnel = base_agency_info.get("key_personnel", [])
        agency_intelligence.preferred_partnerships = base_agency_info.get("preferred_partnerships", [])
        agency_intelligence.strategic_priorities = base_agency_info.get("strategic_priorities", [])
        
        # Compliance requirements
        complexity_mapping = {
            "DOD": ComplianceComplexity.CRITICAL,
            "DOE": ComplianceComplexity.HIGH,
            "HHS": ComplianceComplexity.HIGH,
            "NSF": ComplianceComplexity.MEDIUM,
            "EPA": ComplianceComplexity.HIGH,
            "ED": ComplianceComplexity.MEDIUM
        }
        
        agency_intelligence.compliance_complexity = complexity_mapping.get(
            agency_code, ComplianceComplexity.MEDIUM
        )
        
        agency_intelligence.required_certifications = base_agency_info.get("required_certifications", [])
        agency_intelligence.documentation_requirements = base_agency_info.get("documentation_requirements", [])
        
        return agency_intelligence
    
    async def _generate_compliance_roadmap(
        self,
        opportunity: GovernmentOpportunity,
        organization: OrganizationProfile,
        agency_intelligence: AgencyIntelligence
    ) -> ComplianceRoadmap:
        """Generate comprehensive compliance roadmap."""
        
        compliance_roadmap = ComplianceRoadmap(
            opportunity_id=opportunity.opportunity_id,
            agency_code=agency_intelligence.agency_code,
            complexity_level=agency_intelligence.compliance_complexity
        )
        
        # Generate required documents based on agency and opportunity
        compliance_roadmap.required_documents = self._generate_required_documents(
            opportunity, organization, agency_intelligence
        )
        
        # Generate certification requirements
        compliance_roadmap.certifications_needed = self._generate_certification_requirements(
            opportunity, organization, agency_intelligence
        )
        
        # Generate registration requirements
        compliance_roadmap.registration_requirements = self._generate_registration_requirements(
            opportunity, organization, agency_intelligence
        )
        
        # Create preparation timeline
        compliance_roadmap.preparation_timeline = self._create_preparation_timeline(
            opportunity, compliance_roadmap
        )
        
        # Identify critical deadlines
        compliance_roadmap.critical_deadlines = self._identify_critical_deadlines(
            opportunity, compliance_roadmap
        )
        
        # Calculate recommended start date
        compliance_roadmap.recommended_start_date = self._calculate_recommended_start_date(
            opportunity, compliance_roadmap
        )
        
        # Assess compliance risks
        compliance_roadmap.compliance_risks = self._assess_compliance_risks(
            opportunity, organization, agency_intelligence
        )
        
        # Generate mitigation strategies
        compliance_roadmap.mitigation_strategies = self._generate_compliance_mitigation_strategies(
            compliance_roadmap.compliance_risks
        )
        
        # Calculate success probability
        compliance_roadmap.success_probability = self._calculate_compliance_success_probability(
            organization, compliance_roadmap, agency_intelligence
        )
        
        return compliance_roadmap
    
    # Government agency database initialization
    
    def _initialize_agency_database(self) -> Dict[str, Dict[str, Any]]:
        """Initialize comprehensive government agency database."""
        
        return {
            "DOD": {
                "name": "Department of Defense",
                "type": "cabinet_level",
                "total_opportunities": 1250,
                "average_award_size": 2500000,
                "focus_areas": ["defense technology", "cybersecurity", "advanced materials", "AI/ML"],
                "geographic_preferences": ["nationwide", "defense corridors"],
                "success_factors": ["proven track record", "security clearance", "technical excellence"],
                "rejection_reasons": ["lack security clearance", "insufficient technical depth", "cost overruns"],
                "strategic_priorities": ["technological superiority", "innovation acceleration", "small business"],
                "required_certifications": ["DCAA compliance", "security clearance"],
                "documentation_requirements": ["technical proposal", "cost proposal", "past performance"]
            },
            "HHS": {
                "name": "Department of Health and Human Services",
                "type": "cabinet_level",
                "total_opportunities": 850,
                "average_award_size": 750000,
                "focus_areas": ["health research", "social services", "public health", "healthcare innovation"],
                "geographic_preferences": ["underserved areas", "health professional shortage areas"],
                "success_factors": ["community partnerships", "evidence-based approaches", "measurable outcomes"],
                "rejection_reasons": ["weak evaluation plan", "insufficient community engagement", "budget issues"],
                "strategic_priorities": ["health equity", "evidence-based practice", "innovation"],
                "required_certifications": ["nonprofit status", "audit compliance"],
                "documentation_requirements": ["logic model", "evaluation plan", "budget narrative"]
            },
            "NSF": {
                "name": "National Science Foundation",
                "type": "independent",
                "total_opportunities": 450,
                "average_award_size": 450000,
                "focus_areas": ["STEM education", "basic research", "workforce development", "broadening participation"],
                "geographic_preferences": ["EPSCoR states", "underrepresented communities"],
                "success_factors": ["research excellence", "broader impacts", "collaboration"],
                "rejection_reasons": ["weak methodology", "insufficient broader impacts", "budget misalignment"],
                "strategic_priorities": ["diversity and inclusion", "research infrastructure", "education"],
                "required_certifications": ["research compliance", "IRB approval"],
                "documentation_requirements": ["research plan", "broader impacts", "budget justification"]
            },
            "DOE": {
                "name": "Department of Energy",
                "type": "cabinet_level",
                "total_opportunities": 350,
                "average_award_size": 1800000,
                "focus_areas": ["clean energy", "nuclear technology", "grid modernization", "energy efficiency"],
                "geographic_preferences": ["energy communities", "disadvantaged communities"],
                "success_factors": ["technical innovation", "commercialization potential", "partnerships"],
                "rejection_reasons": ["technology readiness", "market viability", "safety concerns"],
                "strategic_priorities": ["clean energy transition", "energy justice", "innovation"],
                "required_certifications": ["environmental compliance", "safety protocols"],
                "documentation_requirements": ["technical approach", "commercialization plan", "risk assessment"]
            },
            "EPA": {
                "name": "Environmental Protection Agency",
                "type": "independent",
                "total_opportunities": 280,
                "average_award_size": 425000,
                "focus_areas": ["environmental protection", "pollution prevention", "climate resilience", "environmental justice"],
                "geographic_preferences": ["disadvantaged communities", "tribal lands", "pollution hotspots"],
                "success_factors": ["community engagement", "environmental impact", "sustainable solutions"],
                "rejection_reasons": ["weak community component", "insufficient environmental benefit", "compliance issues"],
                "strategic_priorities": ["environmental justice", "climate action", "pollution reduction"],
                "required_certifications": ["environmental compliance", "community partnerships"],
                "documentation_requirements": ["environmental plan", "community engagement", "monitoring plan"]
            },
            "ED": {
                "name": "Department of Education",
                "type": "cabinet_level",
                "total_opportunities": 650,
                "average_award_size": 325000,
                "focus_areas": ["education innovation", "student success", "equity in education", "workforce preparation"],
                "geographic_preferences": ["high-need districts", "rural communities", "underserved populations"],
                "success_factors": ["evidence-based practices", "stakeholder engagement", "measurable outcomes"],
                "rejection_reasons": ["weak evaluation", "insufficient evidence base", "poor partnerships"],
                "strategic_priorities": ["equity", "evidence-based practice", "innovation"],
                "required_certifications": ["education compliance", "audit requirements"],
                "documentation_requirements": ["logic model", "evaluation plan", "sustainability plan"]
            }
        }
    
    def _initialize_compliance_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Initialize compliance frameworks for different agency types."""
        
        return {
            "cabinet_level": {
                "base_requirements": ["SAM registration", "DUNS number", "nonprofit status verification"],
                "documentation": ["audited financials", "organizational chart", "board resolution"],
                "timeline_weeks": 8
            },
            "independent": {
                "base_requirements": ["SAM registration", "DUNS number", "research compliance"],
                "documentation": ["research plan", "IRB approval", "conflict of interest"],
                "timeline_weeks": 6
            },
            "sub_agency": {
                "base_requirements": ["SAM registration", "DUNS number", "parent agency compliance"],
                "documentation": ["specialized certifications", "technical qualifications"],
                "timeline_weeks": 10
            }
        }
    
    # Helper methods for government research
    
    async def _get_government_opportunities_for_research(self, workflow_state) -> List[GovernmentOpportunity]:
        """Get government opportunities prioritized for research."""
        # This would integrate with the workflow state to get high-priority opportunities
        # For now, simulate getting opportunities from workflow
        if not workflow_state or not workflow_state.has_processor_succeeded('grants_gov_fetch'):
            return []
        
        opportunities_data = workflow_state.get_processor_data('grants_gov_fetch')
        if not opportunities_data:
            return []
        
        opportunities = []
        for opp_dict in opportunities_data.get('opportunities', [])[:10]:  # Limit for research
            try:
                opportunity = GovernmentOpportunity(**opp_dict)
                opportunities.append(opportunity)
            except Exception as e:
                self.logger.warning(f"Failed to parse opportunity for research: {e}")
                continue
        
        return opportunities
    
    async def _get_organizations(self, workflow_state) -> List[OrganizationProfile]:
        """Get organizations for government research."""
        # Similar to workflow_aware_scorer but focused on research-ready organizations
        organizations = []
        
        for processor_name in ['usaspending_fetch', 'propublica_fetch', 'bmf_filter']:
            if workflow_state and workflow_state.has_processor_succeeded(processor_name):
                org_dicts = workflow_state.get_organizations_from_processor(processor_name)
                if org_dicts:
                    for org_dict in org_dicts[:5]:  # Limit for research focus
                        try:
                            if isinstance(org_dict, dict):
                                org = OrganizationProfile(**org_dict)
                            else:
                                org = org_dict
                            organizations.append(org)
                        except Exception as e:
                            self.logger.warning(f"Failed to parse organization for research: {e}")
                            continue
                    break
        
        return organizations
    
    def _generate_required_documents(
        self, opportunity, organization, agency_intelligence
    ) -> List[Dict[str, str]]:
        """Generate list of required documents."""
        
        base_docs = [
            {"doc_type": "SF-424", "description": "Application for Federal Assistance", "deadline": "submission"},
            {"doc_type": "Budget Narrative", "description": "Detailed budget justification", "deadline": "submission"},
            {"doc_type": "Project Description", "description": "Technical/program narrative", "deadline": "submission"}
        ]
        
        # Agency-specific documents
        agency_docs = {
            "DOD": [
                {"doc_type": "DD-1414", "description": "Technical Data Package", "deadline": "submission"},
                {"doc_type": "Security Plan", "description": "Information security plan", "deadline": "pre-award"}
            ],
            "HHS": [
                {"doc_type": "Logic Model", "description": "Program theory and outcomes", "deadline": "submission"},
                {"doc_type": "Evaluation Plan", "description": "Performance measurement plan", "deadline": "submission"}
            ],
            "NSF": [
                {"doc_type": "Broader Impacts", "description": "Societal benefit statement", "deadline": "submission"},
                {"doc_type": "Data Management", "description": "Data sharing and management plan", "deadline": "submission"}
            ]
        }
        
        required_docs = base_docs + agency_docs.get(agency_intelligence.agency_code, [])
        
        return required_docs
    
    def _generate_certification_requirements(
        self, opportunity, organization, agency_intelligence
    ) -> List[Dict[str, str]]:
        """Generate certification requirements."""
        
        base_certs = [
            {"cert_type": "SAM Registration", "description": "System for Award Management", "timeline": "30 days"},
            {"cert_type": "DUNS Number", "description": "Data Universal Numbering System", "timeline": "5 days"}
        ]
        
        # Agency-specific certifications
        if agency_intelligence.agency_code == "DOD":
            base_certs.append({
                "cert_type": "DCAA Compliance", "description": "Defense Contract Audit Agency", "timeline": "90 days"
            })
        elif agency_intelligence.agency_code == "HHS":
            base_certs.append({
                "cert_type": "Grants.gov Registration", "description": "Federal grants portal", "timeline": "14 days"
            })
        
        return base_certs
    
    def _generate_registration_requirements(
        self, opportunity, organization, agency_intelligence
    ) -> List[Dict[str, str]]:
        """Generate system registration requirements."""
        
        registrations = [
            {"system": "Grants.gov", "description": "Federal grants portal", "timeline": "14 days"},
            {"system": "SAM.gov", "description": "System for Award Management", "timeline": "30 days"}
        ]
        
        # Agency-specific registrations
        if agency_intelligence.agency_code in ["DOD", "DOE"]:
            registrations.append({
                "system": "eMASS", "description": "Enterprise Mission Assurance Support Service", "timeline": "45 days"
            })
        
        return registrations
    
    def _create_preparation_timeline(self, opportunity, compliance_roadmap) -> Dict[str, str]:
        """Create detailed preparation timeline."""
        
        days_until_deadline = opportunity.calculate_days_until_deadline() or 60
        
        timeline = {}
        
        if days_until_deadline > 30:
            timeline["Initial Planning"] = f"{days_until_deadline - 21} days before deadline"
            timeline["Document Preparation"] = f"{days_until_deadline - 14} days before deadline"
            timeline["Review & Refinement"] = f"{days_until_deadline - 7} days before deadline"
            timeline["Final Submission"] = "Deadline day"
        else:
            timeline["Immediate Action Required"] = "Start immediately"
            timeline["Document Preparation"] = f"{max(1, days_until_deadline - 7)} days remaining"
            timeline["Final Submission"] = "Deadline day"
        
        return timeline
    
    def _identify_critical_deadlines(self, opportunity, compliance_roadmap) -> List[Dict[str, Any]]:
        """Identify critical deadlines in the compliance process."""
        
        deadlines = []
        
        # Registration deadlines
        for reg in compliance_roadmap.registration_requirements:
            deadlines.append({
                "type": "registration",
                "description": f"{reg['system']} registration",
                "deadline": f"{reg['timeline']} before submission",
                "criticality": "high"
            })
        
        # Certification deadlines  
        for cert in compliance_roadmap.certifications_needed:
            deadlines.append({
                "type": "certification",
                "description": f"{cert['cert_type']} completion",
                "deadline": f"{cert['timeline']} before submission",
                "criticality": "high"
            })
        
        # Application deadline
        deadlines.append({
            "type": "application",
            "description": "Grant application submission",
            "deadline": opportunity.close_date.strftime("%Y-%m-%d") if opportunity.close_date else "TBD",
            "criticality": "critical"
        })
        
        return deadlines
    
    def _calculate_recommended_start_date(self, opportunity, compliance_roadmap) -> Optional[datetime]:
        """Calculate recommended project start date."""
        
        if not opportunity.close_date:
            return None
        
        # Calculate preparation time needed
        max_prep_time = 0
        
        for reg in compliance_roadmap.registration_requirements:
            timeline_str = reg['timeline']
            if 'days' in timeline_str:
                days = int(timeline_str.split()[0])
                max_prep_time = max(max_prep_time, days)
        
        for cert in compliance_roadmap.certifications_needed:
            timeline_str = cert['timeline']
            if 'days' in timeline_str:
                days = int(timeline_str.split()[0])
                max_prep_time = max(max_prep_time, days)
        
        # Add buffer time based on complexity
        buffer_days = {
            ComplianceComplexity.LOW: 7,
            ComplianceComplexity.MEDIUM: 14,
            ComplianceComplexity.HIGH: 21,
            ComplianceComplexity.CRITICAL: 30
        }
        
        total_prep_time = max_prep_time + buffer_days[compliance_roadmap.complexity_level]
        
        recommended_start = opportunity.close_date - timedelta(days=total_prep_time)
        
        return recommended_start
    
    def _assess_compliance_risks(self, opportunity, organization, agency_intelligence) -> List[str]:
        """Assess compliance risks for the opportunity."""
        
        risks = []
        
        # Timeline risks
        days_until_deadline = opportunity.calculate_days_until_deadline() or 60
        if days_until_deadline < 30:
            risks.append("Insufficient preparation time for complete compliance")
        
        # Complexity risks
        if agency_intelligence.compliance_complexity in [ComplianceComplexity.HIGH, ComplianceComplexity.CRITICAL]:
            risks.append("High regulatory compliance complexity")
        
        # Organization capacity risks
        if not organization.revenue or organization.revenue < 500000:
            risks.append("Limited organizational capacity for complex compliance requirements")
        
        # Documentation risks
        required_docs = len(agency_intelligence.documentation_requirements)
        if required_docs > 5:
            risks.append("Extensive documentation requirements")
        
        # Agency-specific risks
        if agency_intelligence.agency_code == "DOD":
            risks.append("Security clearance and DCAA compliance requirements")
        elif agency_intelligence.agency_code == "DOE":
            risks.append("Technical safety and environmental compliance requirements")
        
        return risks
    
    def _generate_compliance_mitigation_strategies(self, compliance_risks: List[str]) -> List[str]:
        """Generate strategies to mitigate compliance risks."""
        
        strategies = []
        
        for risk in compliance_risks:
            if "preparation time" in risk:
                strategies.append("Prioritize critical compliance items and consider expedited processing")
            elif "complexity" in risk:
                strategies.append("Engage compliance consultant or experienced partner organization")
            elif "capacity" in risk:
                strategies.append("Partner with larger organization or hire temporary compliance support")
            elif "documentation" in risk:
                strategies.append("Create document checklist and assign dedicated documentation team")
            elif "security clearance" in risk:
                strategies.append("Begin security clearance process immediately or partner with cleared organization")
            elif "safety" in risk:
                strategies.append("Engage certified safety professionals and conduct compliance audit")
        
        # General strategies
        strategies.extend([
            "Establish regular compliance checkpoint meetings",
            "Maintain detailed audit trail of all compliance activities",
            "Build relationships with agency compliance officers"
        ])
        
        return list(set(strategies))  # Remove duplicates
    
    def _calculate_compliance_success_probability(
        self, organization, compliance_roadmap, agency_intelligence
    ) -> float:
        """Calculate probability of successful compliance."""
        
        base_probability = 0.7  # Base 70% for standard compliance
        
        # Organization factors
        if organization.revenue and organization.revenue > 1000000:
            base_probability += 0.1  # Larger organizations have more capacity
        
        # Timeline factors
        if compliance_roadmap.recommended_start_date and compliance_roadmap.recommended_start_date > datetime.now():
            base_probability += 0.15  # Adequate preparation time
        else:
            base_probability -= 0.2  # Time pressure
        
        # Complexity factors
        complexity_adjustments = {
            ComplianceComplexity.LOW: 0.2,
            ComplianceComplexity.MEDIUM: 0.0,
            ComplianceComplexity.HIGH: -0.15,
            ComplianceComplexity.CRITICAL: -0.25
        }
        base_probability += complexity_adjustments[compliance_roadmap.complexity_level]
        
        # Risk factors
        risk_penalty = len(compliance_roadmap.compliance_risks) * 0.05
        base_probability -= risk_penalty
        
        return max(0.1, min(1.0, base_probability))
    
    # Additional helper methods for competitive analysis, positioning, etc.
    
    async def _analyze_competitive_landscape(self, opportunity, organization, agency_intelligence) -> Dict[str, Any]:
        """Analyze competitive landscape for the opportunity."""
        
        return {
            "competition_level": self._assess_competition_level(opportunity, agency_intelligence),
            "typical_winners": self._identify_typical_winners(agency_intelligence),
            "competitive_advantages": self._identify_competitive_advantages(organization, opportunity),
            "competitive_weaknesses": self._identify_competitive_weaknesses(organization, opportunity),
            "differentiation_opportunities": self._identify_differentiation_opportunities(organization, opportunity)
        }
    
    async def _generate_positioning_strategy(self, opportunity, organization, agency_intelligence) -> List[str]:
        """Generate strategic positioning recommendations."""
        
        strategies = []
        
        # Organization strengths-based positioning
        if organization.revenue and organization.revenue > 1000000:
            strategies.append("Position as established, reliable implementation partner")
        else:
            strategies.append("Position as nimble, innovative solution provider")
        
        # Agency-specific positioning
        if agency_intelligence.agency_code == "NSF":
            strategies.append("Emphasize broader impacts and research excellence")
        elif agency_intelligence.agency_code == "HHS":
            strategies.append("Highlight community partnerships and evidence-based approaches")
        elif agency_intelligence.agency_code == "DOD":
            strategies.append("Focus on technical innovation and security compliance")
        
        # Opportunity-specific positioning
        if "innovation" in opportunity.description.lower():
            strategies.append("Emphasize innovative approach and cutting-edge methodology")
        if "partnership" in opportunity.description.lower():
            strategies.append("Highlight collaborative partnerships and stakeholder engagement")
        
        return strategies
    
    async def _generate_partnership_recommendations(self, opportunity, organization, agency_intelligence) -> List[str]:
        """Generate partnership recommendations."""
        
        recommendations = []
        
        # Based on organization capacity
        if not organization.revenue or organization.revenue < 500000:
            recommendations.append("Partner with larger organization for administrative capacity")
        
        # Based on agency preferences
        for preferred_partnership in agency_intelligence.preferred_partnerships:
            recommendations.append(f"Consider partnership with {preferred_partnership}")
        
        # Based on opportunity requirements
        if "research" in opportunity.description.lower():
            recommendations.append("Partner with academic institution for research credibility")
        if "community" in opportunity.description.lower():
            recommendations.append("Partner with community-based organizations for local engagement")
        
        return recommendations
    
    async def _analyze_technical_requirements(self, opportunity, organization) -> List[str]:
        """Analyze technical requirements for the opportunity."""
        
        requirements = []
        
        # Extract technical terms from opportunity description
        technical_keywords = ["software", "data", "system", "technology", "platform", "infrastructure", 
                             "security", "compliance", "integration", "analytics", "AI", "machine learning"]
        
        description_lower = opportunity.description.lower()
        for keyword in technical_keywords:
            if keyword in description_lower:
                requirements.append(f"Technical expertise in {keyword}")
        
        # Add compliance and regulatory requirements
        requirements.extend([
            "Federal grant management systems integration",
            "Audit trail and compliance reporting capabilities",
            "Data security and privacy protection measures"
        ])
        
        return requirements
    
    async def _create_resource_allocation_plan(self, opportunity, organization, compliance_roadmap) -> Dict[str, Any]:
        """Create resource allocation plan."""
        
        return {
            "preparation_phase": {
                "compliance_specialist": "0.5 FTE for compliance activities",
                "project_manager": "0.25 FTE for coordination",
                "technical_staff": "Variable based on requirements"
            },
            "implementation_phase": {
                "project_director": "0.5 FTE for overall management",
                "program_staff": "Variable based on project scope",
                "administrative_support": "0.25 FTE for reporting"
            },
            "budget_allocation": {
                "personnel": "65-75% of total budget",
                "compliance_costs": "5-10% of total budget",
                "administrative": "10-15% of total budget",
                "indirect_costs": f"{organization.component_scores.get('indirect_rate', 15)}%"
            }
        }
    
    async def _define_success_metrics(self, opportunity, organization, agency_intelligence) -> List[str]:
        """Define success metrics for the opportunity."""
        
        metrics = [
            "Successful grant application submission",
            "Compliance with all federal reporting requirements",
            "Achievement of stated project outcomes"
        ]
        
        # Agency-specific metrics
        if agency_intelligence.agency_code == "NSF":
            metrics.extend([
                "Publications in peer-reviewed journals",
                "Broader impacts achievement metrics",
                "Student/researcher training outcomes"
            ])
        elif agency_intelligence.agency_code == "HHS":
            metrics.extend([
                "Community engagement and participation rates",
                "Health outcome improvements",
                "Sustainability plan implementation"
            ])
        elif agency_intelligence.agency_code == "DOD":
            metrics.extend([
                "Technical milestone achievement",
                "Technology readiness level advancement",
                "Security compliance maintenance"
            ])
        
        return metrics
    
    async def _analyze_funding_risks(self, opportunity, agency_intelligence) -> List[str]:
        """Analyze funding-specific risks."""
        
        risks = [
            "Budget cuts or appropriation changes",
            "Policy priority shifts",
            "Increased competition for limited funds"
        ]
        
        # Agency-specific funding risks
        if agency_intelligence.agency_code == "DOD":
            risks.append("Defense spending policy changes")
        elif agency_intelligence.agency_code == "EPA":
            risks.append("Environmental policy and regulatory changes")
        elif agency_intelligence.agency_code == "ED":
            risks.append("Education policy and formula funding changes")
        
        return risks
    
    async def _analyze_implementation_risks(self, opportunity, organization) -> List[str]:
        """Analyze implementation-specific risks."""
        
        risks = [
            "Staff turnover during project implementation",
            "Technical challenges or scope creep",
            "Partnership coordination difficulties"
        ]
        
        # Organization-specific risks
        if not organization.revenue or organization.revenue < 1000000:
            risks.append("Limited organizational capacity for large projects")
        
        # Opportunity-specific risks
        if opportunity.award_ceiling and opportunity.award_ceiling > 1000000:
            risks.append("Complex project management for large award")
        
        return risks
    
    async def _create_mitigation_plan(self, all_risks: List[str], opportunity, organization) -> List[str]:
        """Create comprehensive risk mitigation plan."""
        
        mitigation_strategies = [
            "Develop detailed project management plan with clear milestones",
            "Establish regular communication with agency program officers",
            "Maintain detailed documentation and audit trails",
            "Build contingency plans for key risks",
            "Establish strong partnership agreements with clear roles"
        ]
        
        # Risk-specific mitigation
        risk_mitigation_map = {
            "capacity": "Partner with experienced organizations or hire temporary staff",
            "technical": "Engage technical consultants or build strategic partnerships",
            "compliance": "Hire compliance specialists or use experienced consultants",
            "funding": "Diversify funding sources and maintain strong agency relationships",
            "timeline": "Build buffer time into project schedule and use agile methodology"
        }
        
        for risk in all_risks:
            for risk_type, mitigation in risk_mitigation_map.items():
                if risk_type in risk.lower():
                    mitigation_strategies.append(mitigation)
                    break
        
        return list(set(mitigation_strategies))  # Remove duplicates
    
    # Analysis and summary methods
    
    async def _generate_agency_intelligence_summary(
        self, opportunities: List[GovernmentOpportunity], research_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary of agency intelligence across all opportunities."""
        
        agency_summary = {}
        
        for result in research_results:
            agency_code = result["research_insights"]["agency_intelligence"]["agency_code"]
            
            if agency_code not in agency_summary:
                agency_summary[agency_code] = {
                    "agency_name": result["research_insights"]["agency_intelligence"]["agency_name"],
                    "opportunities_analyzed": 0,
                    "avg_compliance_complexity": [],
                    "common_success_factors": [],
                    "total_funding_potential": 0
                }
            
            agency_data = agency_summary[agency_code]
            agency_data["opportunities_analyzed"] += 1
            
            # Track compliance complexity
            complexity = result["research_insights"]["compliance_roadmap"]["complexity_level"]
            agency_data["avg_compliance_complexity"].append(complexity)
            
        return agency_summary
    
    async def _generate_compliance_landscape_analysis(
        self, research_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate analysis of compliance landscape across opportunities."""
        
        complexity_distribution = {}
        common_requirements = {}
        avg_prep_time = []
        
        for result in research_results:
            compliance = result["research_insights"]["compliance_roadmap"]
            
            # Track complexity distribution
            complexity = compliance["complexity_level"]
            complexity_distribution[complexity] = complexity_distribution.get(complexity, 0) + 1
            
            # Track common requirements
            for doc in compliance["required_documents"]:
                doc_type = doc["doc_type"]
                common_requirements[doc_type] = common_requirements.get(doc_type, 0) + 1
            
            # Track preparation time
            if compliance["recommended_start_date"]:
                # Calculate days from now to recommended start
                start_date = datetime.fromisoformat(compliance["recommended_start_date"].replace('Z', '+00:00'))
                prep_days = (start_date - datetime.now()).days if start_date > datetime.now() else 0
                avg_prep_time.append(prep_days)
        
        return {
            "complexity_distribution": complexity_distribution,
            "most_common_requirements": sorted(common_requirements.items(), key=lambda x: x[1], reverse=True)[:10],
            "average_preparation_time_days": sum(avg_prep_time) / len(avg_prep_time) if avg_prep_time else 0,
            "total_opportunities_analyzed": len(research_results)
        }
    
    async def _calculate_government_research_metrics(
        self, research_results: List[Dict[str, Any]], opportunities: List[GovernmentOpportunity], 
        organizations: List[OrganizationProfile]
    ) -> Dict[str, Any]:
        """Calculate government research performance metrics."""
        
        total_research = len(research_results)
        if total_research == 0:
            return {"total_research_insights": 0}
        
        # Success probability distribution
        success_probs = [r["research_insights"]["compliance_roadmap"]["success_probability"] 
                        for r in research_results]
        
        # Compliance complexity distribution
        complexity_counts = {}
        for result in research_results:
            complexity = result["research_insights"]["compliance_roadmap"]["complexity_level"]
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
        
        # Agency coverage
        unique_agencies = len(set(r["research_insights"]["agency_intelligence"]["agency_code"] 
                                for r in research_results))
        
        return {
            "total_research_insights": total_research,
            "success_probability_stats": {
                "average": sum(success_probs) / len(success_probs) if success_probs else 0,
                "high_probability_count": len([p for p in success_probs if p > 0.7]),
                "low_probability_count": len([p for p in success_probs if p < 0.4])
            },
            "complexity_distribution": complexity_counts,
            "agency_coverage": unique_agencies,
            "research_depth_score": min(1.0, total_research / (len(opportunities) * len(organizations)))
        }
    
    def _analyze_compliance_distribution(self, research_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of compliance complexity levels."""
        
        distribution = {
            "low": 0,
            "medium": 0, 
            "high": 0,
            "critical": 0
        }
        
        for result in research_results:
            complexity = result["research_insights"]["compliance_roadmap"]["complexity_level"]
            distribution[complexity] += 1
        
        return distribution
    
    def _assess_competition_level(self, opportunity, agency_intelligence) -> str:
        """Assess competition level for opportunity."""
        
        # Simple heuristic based on award size and agency
        if opportunity.award_ceiling and opportunity.award_ceiling > 2000000:
            return "high"
        elif len(opportunity.eligible_applicants) > 5:
            return "high"
        elif agency_intelligence.agency_code in ["NSF", "NIH"]:
            return "high"
        elif opportunity.award_ceiling and opportunity.award_ceiling < 100000:
            return "low"
        else:
            return "medium"
    
    def _identify_typical_winners(self, agency_intelligence) -> List[str]:
        """Identify types of organizations that typically win from this agency."""
        
        typical_winners_map = {
            "DOD": ["Defense contractors", "Research universities", "Technology companies"],
            "HHS": ["Healthcare organizations", "Community health centers", "Research institutions"],
            "NSF": ["Universities", "Research institutions", "STEM education organizations"],
            "DOE": ["National laboratories", "Energy companies", "Research universities"],
            "EPA": ["Environmental organizations", "State/local agencies", "Research institutions"],
            "ED": ["Educational institutions", "State education agencies", "Community organizations"]
        }
        
        return typical_winners_map.get(agency_intelligence.agency_code, ["Nonprofit organizations", "Research institutions"])
    
    def _identify_competitive_advantages(self, organization, opportunity) -> List[str]:
        """Identify competitive advantages for the organization."""
        
        advantages = []
        
        # Revenue-based advantages
        if organization.revenue and organization.revenue > 2000000:
            advantages.append("Strong financial capacity and stability")
        elif organization.revenue and organization.revenue < 1000000:
            advantages.append("Nimble, cost-effective operations")
        
        # Experience-based advantages
        if organization.component_scores.get("award_history", {}).get("total_awards", 0) > 0:
            advantages.append("Proven federal grant management experience")
        
        # NTEE code-based advantages
        if organization.ntee_code:
            ntee_advantages = {
                "B": "Educational expertise and stakeholder relationships",
                "E": "Healthcare knowledge and community connections",
                "C": "Environmental expertise and conservation focus",
                "P": "Research and technical capabilities"
            }
            main_category = organization.ntee_code[0]
            if main_category in ntee_advantages:
                advantages.append(ntee_advantages[main_category])
        
        return advantages
    
    def _identify_competitive_weaknesses(self, organization, opportunity) -> List[str]:
        """Identify competitive weaknesses for the organization."""
        
        weaknesses = []
        
        # Capacity weaknesses
        if not organization.revenue or organization.revenue < 500000:
            weaknesses.append("Limited organizational capacity for large projects")
        
        # Experience weaknesses
        if organization.component_scores.get("award_history", {}).get("total_awards", 0) == 0:
            weaknesses.append("Limited federal grant management experience")
        
        # Geographic weaknesses
        if opportunity.eligible_states and organization.state not in opportunity.eligible_states:
            weaknesses.append("Geographic eligibility concerns")
        
        return weaknesses
    
    def _identify_differentiation_opportunities(self, organization, opportunity) -> List[str]:
        """Identify opportunities for differentiation."""
        
        opportunities_for_diff = [
            "Innovative approach to traditional challenges",
            "Strong community partnerships and stakeholder engagement",
            "Cost-effective implementation strategies",
            "Measurable outcomes and evaluation expertise"
        ]
        
        # Opportunity-specific differentiation
        if "innovation" in opportunity.description.lower():
            opportunities_for_diff.append("Cutting-edge technology or methodology")
        
        if "partnership" in opportunity.description.lower():
            opportunities_for_diff.append("Unique collaborative partnerships")
        
        return opportunities_for_diff


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return GovernmentResearchIntegration()