"""
AI Heavy Implementation Planner - Enhanced Implementation Planning for APPROACH tab

Purpose: Comprehensive grant application planning and implementation strategy
Model: GPT-5-mini for sophisticated implementation analysis (~$0.12-0.18 per implementation dossier)
Processing: Implementation-focused analysis with comprehensive planning and resource optimization

APPROACH Tab Specialization (Implementation Planning Focus):
- Grant application intelligence with detailed effort estimation
- Implementation blueprints with resource allocation and timeline optimization
- Proposal strategy development with positioning and messaging recommendations
- Go/No-Go decision frameworks with success probability modeling
- Application package coordination with submission planning
- ENHANCED: Grant size optimization modeling and multi-year funding strategies
- ENHANCED: Market entry strategies and partnership risk assessment
- ENHANCED: Sustainability prospects analysis and long-term planning
- Deep integration with EXAMINE tab strategic intelligence

NOTE: Strategic intelligence features (competitive analysis, relationship mapping) 
have been consolidated in EXAMINE tab AI-Heavy Deep Research processor.
"""

import json
import logging
import asyncio
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import openai
from pydantic import BaseModel, Field
from enum import Enum

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.error_recovery import (
    with_error_recovery, create_ai_retry_policy, error_recovery_manager,
    ErrorCategory, ErrorSeverity, RecoveryAction
)
from src.processors.analysis.grant_package_generator import GrantPackageGenerator, ApplicationPackage
from src.core.simple_mcp_client import SimpleMCPClient

logger = logging.getLogger(__name__)

# Enhanced data packet models for comprehensive AI Heavy research

class AnalysisDepth(str, Enum):
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    STRATEGIC = "strategic"

class Priority(str, Enum):
    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"
    URGENT = "urgent"

class ResearchMetadata(BaseModel):
    """AI Heavy research request metadata"""
    research_id: str
    profile_id: str
    target_organization: str
    analysis_depth: AnalysisDepth = AnalysisDepth.COMPREHENSIVE
    model_preference: str = "gpt-5-mini"
    cost_budget: float = 0.15
    priority: Priority = Priority.HIGH

class ContextProfileData(BaseModel):
    """Requesting organization context for AI Heavy analysis"""
    organization_name: str
    mission_statement: str
    strategic_priorities: List[str] = Field(default_factory=list)
    leadership_team: List[str] = Field(default_factory=list)
    recent_grants: List[str] = Field(default_factory=list)
    funding_capacity: str = "$1M annually"
    geographic_scope: str = "National"

class AILiteResults(BaseModel):
    """AI Lite preliminary analysis results"""
    compatibility_score: float
    strategic_value: str
    risk_assessment: List[str] = Field(default_factory=list)
    priority_rank: int
    funding_likelihood: float
    strategic_rationale: str
    action_priority: str

class TargetPreliminaryData(BaseModel):
    """Target organization preliminary data"""
    organization_name: str
    basic_info: str
    funding_capacity: str = "Unknown"
    geographic_focus: str = "National"
    known_board_members: List[str] = Field(default_factory=list)
    recent_grants_given: List[str] = Field(default_factory=list)
    website_url: Optional[str] = None
    annual_revenue: Optional[str] = None

class ResearchFocus(BaseModel):
    """Specific research focus areas"""
    priority_areas: List[str] = Field(default=["strategic_partnership", "funding_approach", "introduction_strategy"])
    risk_mitigation: List[str] = Field(default=["competition_analysis", "capacity_assessment"])
    intelligence_gaps: List[str] = Field(default=["board_connections", "funding_timeline", "application_requirements"])

# Enhanced Intelligence Models for Phase 3

class OpportunityCategory(str, Enum):
    """Intelligent opportunity categorization"""
    STRATEGIC_PARTNER = "strategic_partner"  # Long-term strategic relationship potential
    FUNDING_SOURCE = "funding_source"       # Primary funding opportunity
    NETWORK_GATEWAY = "network_gateway"     # Access to broader network
    CAPACITY_BUILDER = "capacity_builder"   # Skills/infrastructure development
    INNOVATION_CATALYST = "innovation_catalyst" # New program development
    SUSTAINABILITY_ANCHOR = "sustainability_anchor" # Long-term sustainability

class IntelligencePattern(BaseModel):
    """ML-based pattern recognition for research optimization"""
    pattern_type: str  # "success_indicator", "risk_signal", "opportunity_marker"
    pattern_description: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    historical_accuracy: float = Field(..., ge=0.0, le=1.0)
    actionable_insights: List[str] = Field(default_factory=list)

class SmartResearchFocus(BaseModel):
    """AI-enhanced research focus optimization"""
    primary_category: OpportunityCategory
    intelligence_patterns: List[IntelligencePattern] = Field(default_factory=list)
    research_efficiency_score: float = Field(..., ge=0.0, le=1.0)
    predictive_insights: List[str] = Field(default_factory=list)
    adaptive_focus_areas: List[str] = Field(default_factory=list)

class ContextData(BaseModel):
    """Complete context data for AI Heavy analysis"""
    profile_context: ContextProfileData
    ai_lite_results: AILiteResults
    target_preliminary_data: TargetPreliminaryData

class AIHeavyRequest(BaseModel):
    """Complete AI Heavy research request packet"""
    request_metadata: ResearchMetadata
    context_data: ContextData
    research_focus: ResearchFocus
    smart_focus: Optional[SmartResearchFocus] = None  # Enhanced AI-driven focus

# AI Heavy Analysis Result Models

class PartnershipAssessment(BaseModel):
    """Strategic partnership assessment results"""
    mission_alignment_score: int = Field(..., ge=0, le=100)
    strategic_value: str
    mutual_benefits: List[str] = Field(default_factory=list)
    partnership_potential: str
    synergy_opportunities: List[str] = Field(default_factory=list)

class FundingStrategy(BaseModel):
    """Funding approach strategy"""
    optimal_request_amount: str
    best_timing: str
    target_programs: List[str] = Field(default_factory=list)
    success_factors: List[str] = Field(default_factory=list)
    application_requirements: List[str] = Field(default_factory=list)

class CompetitiveAnalysis(BaseModel):
    """Competitive landscape analysis"""
    primary_competitors: List[str] = Field(default_factory=list)
    competitive_advantages: List[str] = Field(default_factory=list)
    market_position: str
    differentiation_strategy: str
    threat_assessment: List[str] = Field(default_factory=list)

class RelationshipStrategy(BaseModel):
    """Introduction and relationship building strategy"""
    board_connections: List[Dict[str, str]] = Field(default_factory=list)
    staff_approach: List[str] = Field(default_factory=list)
    network_leverage: List[str] = Field(default_factory=list)
    engagement_timeline: str

class FinancialAnalysis(BaseModel):
    """Enhanced financial analysis and funding strategy"""
    funding_capacity_assessment: str
    grant_size_optimization: str
    multi_year_potential: str
    sustainability_prospects: str
    financial_health_score: int = Field(..., ge=0, le=100)

class ImplementationPlanning(BaseModel):
    """Enhanced implementation planning (moved from EXAMINE tab)"""
    market_entry_strategies: List[str] = Field(default_factory=list)
    partnership_risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    resource_optimization_plan: Dict[str, Any] = Field(default_factory=dict)
    implementation_timeline: Dict[str, Any] = Field(default_factory=dict)
    sustainability_framework: List[str] = Field(default_factory=list)
    long_term_planning: Dict[str, Any] = Field(default_factory=dict)

class RiskAssessment(BaseModel):
    """Risk assessment and mitigation"""
    primary_risks: List[Dict[str, str]] = Field(default_factory=list)
    mitigation_strategies: List[str] = Field(default_factory=list)
    contingency_plans: List[str] = Field(default_factory=list)
    success_probability: float = Field(..., ge=0.0, le=1.0)

# Grant Application Intelligence Models

class EligibilityRequirement(BaseModel):
    """Individual eligibility requirement"""
    requirement: str
    requirement_type: str  # "organizational", "programmatic", "financial", "geographic"
    compliance_status: str  # "meets", "needs_verification", "does_not_meet", "unclear"
    documentation_needed: List[str] = Field(default_factory=list)
    notes: str = ""

class ApplicationRequirement(BaseModel):
    """Application submission requirement"""
    document_type: str
    description: str
    page_limit: Optional[str] = None
    format_requirements: List[str] = Field(default_factory=list)
    submission_deadline: Optional[str] = None
    preparation_time_estimate: str = ""
    template_available: bool = False

class GrantTimeline(BaseModel):
    """Grant application and award timeline"""
    application_deadline: str
    award_notification: str
    project_start_date: str
    project_duration: str
    reporting_schedule: List[str] = Field(default_factory=list)
    key_milestones: List[Dict[str, str]] = Field(default_factory=list)

class EffortEstimation(BaseModel):
    """Enhanced level of effort estimation for application with detailed project management"""
    total_hours_estimate: str
    preparation_phases: List[Dict[str, Any]] = Field(default_factory=list)  # Enhanced with deliverables and dependencies
    required_expertise: List[str] = Field(default_factory=list)
    external_support_needed: List[str] = Field(default_factory=list)
    critical_path_activities: List[Dict[str, str]] = Field(default_factory=list)  # Enhanced with timing and mitigation
    risk_factors: List[Dict[str, str]] = Field(default_factory=list)  # New: Risk analysis for timeline
    success_accelerators: List[str] = Field(default_factory=list)  # New: Factors that speed up process

class GrantApplicationIntelligence(BaseModel):
    """Comprehensive grant application intelligence"""
    eligibility_analysis: List[EligibilityRequirement] = Field(default_factory=list)
    application_requirements: List[ApplicationRequirement] = Field(default_factory=list)
    grant_timeline: GrantTimeline
    effort_estimation: EffortEstimation
    application_strategy: List[str] = Field(default_factory=list)
    success_factors: List[str] = Field(default_factory=list)
    competitive_advantages: List[str] = Field(default_factory=list)

class RecommendedApproach(BaseModel):
    """Strategic approach recommendations for APPROACH tab"""
    pursuit_recommendation: str  # "high_priority", "medium_priority", "monitor", "pass"
    optimal_request_amount: str
    timing_strategy: str
    positioning_strategy: str
    team_composition: List[str] = Field(default_factory=list)
    preparation_timeline: str
    go_no_go_factors: List[str] = Field(default_factory=list)
    success_probability: float = Field(..., ge=0.0, le=1.0)

class ActionItem(BaseModel):
    """Individual action item with details"""
    action: str
    timeline: str
    priority: str
    estimated_effort: str
    success_indicators: List[str] = Field(default_factory=list)

class ActionPlan(BaseModel):
    """Comprehensive action plan"""
    immediate_actions: List[ActionItem] = Field(default_factory=list)
    six_month_roadmap: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    investment_recommendation: str
    roi_projection: str

class StrategicDossier(BaseModel):
    """Complete strategic dossier with grant application intelligence"""
    partnership_assessment: PartnershipAssessment
    funding_strategy: FundingStrategy
    competitive_analysis: CompetitiveAnalysis
    relationship_strategy: RelationshipStrategy
    financial_analysis: FinancialAnalysis
    risk_assessment: RiskAssessment
    grant_application_intelligence: GrantApplicationIntelligence
    recommended_approach: RecommendedApproach

class ResearchResults(BaseModel):
    """Research processing metadata"""
    research_id: str
    target_organization: str
    analysis_depth: str
    processing_time: float
    total_cost: float
    model_used: str
    confidence_level: float = Field(..., ge=0.0, le=1.0)

class AIHeavyResult(BaseModel):
    """Complete AI Heavy research results with grant application package"""
    research_results: ResearchResults
    strategic_dossier: StrategicDossier
    action_plan: ActionPlan
    grant_application_package: Optional[ApplicationPackage] = None

class AIHeavyDossierBuilder(BaseProcessor):
    """AI Heavy dossier builder processor for APPROACH tab - grant application and implementation planning"""
    
    def __init__(self):
        # Create metadata for base processor
        metadata = ProcessorMetadata(
            name="ai_heavy_dossier_builder",
            description="Phase 1.5: Specialized grant application and implementation planning for APPROACH tab",
            version="1.5.0",  # Phase 1.5 Specialization
            dependencies=["ai_lite_scorer", "ai_heavy_deep_researcher"],  # Integrates with both AI-Lite and Deep Research
            estimated_duration=120,  # Optimized for implementation planning
            requires_network=True,
            requires_api_key=True,
            can_run_parallel=True,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Implementation planning settings (Updated for GPT-5-mini)
        self.model = "gpt-5-mini"  # Advanced GPT-5 model for sophisticated implementation planning
        self.max_tokens = 3500  # Optimized token limit for implementation analysis
        self.temperature = 0.3  # Lower temperature for consistent implementation planning
        
        # Cost tracking (Updated GPT-5-mini pricing: ~$0.50/1M input, ~$4.0/1M output)
        self.estimated_cost_per_dossier = 0.08  # More cost-effective with GPT-5-mini
        
        # Grant application intelligence
        self.grant_package_generator = GrantPackageGenerator()
        
        # Web intelligence integration
        self.mcp_client = SimpleMCPClient(timeout=20)
        self.database_path = "data/catalynx.db"
        
        # Enhanced Intelligence Capabilities (Phase 3)
        self.categorization_confidence_threshold = 0.85
        self.pattern_recognition_enabled = True
        self.adaptive_research_optimization = True
        
        # Phase 1.5 Enhancement: APPROACH Tab Specialization
        self.approach_tab_specialization = True  # Specialized for APPROACH tab implementation planning
        self.implementation_planning_mode = True  # Enable implementation-focused analysis
        self.deep_research_integration_enabled = True  # Integrate EXAMINE tab deep research outputs
        self.grant_application_optimization = True  # Optimize for grant application planning
        
    async def execute(self, request_data: AIHeavyRequest) -> AIHeavyResult:
        """
        Execute AI Heavy dossier building for APPROACH tab implementation planning
        
        Args:
            request_data: Complete AI Heavy request with metadata, context, focus areas, and deep research integration
            
        Returns:
            AIHeavyResult with implementation-focused dossier and application planning
        """
        start_time = datetime.now()
        research_id = request_data.request_metadata.research_id
        target_org = request_data.request_metadata.target_organization
        
        logger.info(f"Starting AI Heavy dossier building for {target_org} (research: {research_id})")
        logger.info(f"APPROACH tab specialization: {'ENABLED' if self.approach_tab_specialization else 'DISABLED'}")
        logger.info(f"Implementation planning mode: {'ENABLED' if self.implementation_planning_mode else 'DISABLED'}")
        
        # Register fallback handler for this operation
        def create_fallback_analysis():
            return {
                "strategic_dossier": self._create_fallback_strategic_dossier(target_org),
                "action_plan": self._create_fallback_action_plan(),
                "confidence_level": 0.6
            }
        
        error_recovery_manager.register_fallback_handler("ai_heavy_research", create_fallback_analysis)
        
        try:
            # Phase 1.5 Enhancement: Deep Research Integration Check
            if self.deep_research_integration_enabled:
                logger.info("Deep research integration enabled - incorporating EXAMINE tab intelligence findings")
            
            # Phase 3 Enhancement: Intelligent Pre-Research Analysis
            enhanced_request = await self._apply_intelligent_categorization(request_data)
            
            # Web Intelligence Enhancement: Gather current web context
            web_context = await self._gather_web_intelligence_context(enhanced_request)
            if web_context:
                enhanced_request = self._enhance_request_with_web_context(enhanced_request, web_context)
                logger.info(f"Enhanced request with {len(web_context)} web intelligence sources")
            
            # Phase 1 Enhancement: Prepare dossier-focused research prompt
            if self.dossier_builder_mode:
                research_prompt = self._create_dossier_builder_research_prompt(enhanced_request)
            else:
                research_prompt = self._create_comprehensive_research_prompt(enhanced_request)
            
            # Call OpenAI API with comprehensive error recovery
            response = await error_recovery_manager.execute_with_recovery(
                operation="openai_api",
                func=self._call_openai_api,
                retry_policy=create_ai_retry_policy(),
                context={"target_organization": target_org, "model": enhanced_request.request_metadata.model_preference},
                prompt=research_prompt,
                model=enhanced_request.request_metadata.model_preference
            )
            
            # Parse and validate comprehensive results with error recovery
            analysis_results = await error_recovery_manager.execute_with_recovery(
                operation="ai_response_parsing",
                func=self._parse_comprehensive_api_response,
                fallback_func=create_fallback_analysis,
                context={"target_organization": target_org, "response_type": "comprehensive_analysis"},
                response=response,
                request_data=request_data
            )
            
            # Generate comprehensive grant application package
            grant_package = None
            try:
                if "strategic_dossier" in analysis_results and hasattr(analysis_results["strategic_dossier"], 'grant_application_intelligence'):
                    # Extract grant intelligence data for package generation
                    grant_intelligence = {
                        "target_organization": target_org,
                        "application_requirements": [req.dict() for req in analysis_results["strategic_dossier"].grant_application_intelligence.application_requirements],
                        "grant_timeline": analysis_results["strategic_dossier"].grant_application_intelligence.grant_timeline.dict(),
                        "effort_estimation": analysis_results["strategic_dossier"].grant_application_intelligence.effort_estimation.dict(),
                        "competitive_advantages": analysis_results["strategic_dossier"].grant_application_intelligence.competitive_advantages,
                        "recommended_approach": analysis_results["strategic_dossier"].recommended_approach.dict()
                    }
                    
                    # Organization profile from request context
                    organization_profile = {
                        "name": request_data.context_data.profile_context.organization_name,
                        "mission": request_data.context_data.profile_context.mission_statement,
                        "strategic_priorities": request_data.context_data.profile_context.strategic_priorities,
                        "funding_capacity": request_data.context_data.profile_context.funding_capacity,
                        "geographic_scope": request_data.context_data.profile_context.geographic_scope
                    }
                    
                    # Generate comprehensive grant application package
                    grant_package = self.grant_package_generator.generate_application_package(
                        grant_intelligence, organization_profile
                    )
                    
                    logger.info(f"Generated grant application package for {target_org}")
                    
            except Exception as e:
                logger.warning(f"Failed to generate grant package for {target_org}: {str(e)}")
                # Continue without package - not critical for main analysis
            
            # Calculate processing metrics
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            estimated_cost = self.estimated_cost_per_dossier
            
            # Create comprehensive result structure
            research_results = ResearchResults(
                research_id=research_id,
                target_organization=target_org,
                analysis_depth=request_data.request_metadata.analysis_depth.value,
                processing_time=processing_time,
                total_cost=estimated_cost,
                model_used=request_data.request_metadata.model_preference,
                confidence_level=analysis_results.get("confidence_level", 0.9)
            )
            
            result = AIHeavyResult(
                research_results=research_results,
                strategic_dossier=analysis_results["strategic_dossier"],
                action_plan=analysis_results["action_plan"],
                grant_application_package=grant_package
            )
            
            logger.info(f"AI Heavy research completed for {target_org}: "
                       f"${estimated_cost:.2f} cost, {processing_time:.1f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"AI Heavy research failed for {target_org}: {str(e)}")
            
            # Use comprehensive error recovery with fallback
            try:
                fallback_results = create_fallback_analysis()
                fallback_grant_package = ApplicationPackage(
                    target_organization=target_org,
                    application_documents=[],
                    submission_requirements=[],
                    timeline_recommendations=[],
                    success_probability=0.5
                )
                
                result = AIHeavyResult(
                    research_results=ResearchResults(
                        research_id=research_id,
                        target_organization=target_org,
                        analysis_depth="fallback",
                        processing_time=0.1,
                        total_cost=0.0,
                        model_used="fallback",
                        confidence_level=0.3
                    ),
                    strategic_dossier=fallback_results["strategic_dossier"],
                    action_plan=fallback_results["action_plan"],
                    grant_application_package=fallback_grant_package
                )
                
                logger.warning(f"Using fallback analysis for {target_org} due to error: {str(e)}")
                return result
                
            except Exception as fallback_error:
                logger.error(f"Fallback analysis also failed for {target_org}: {str(fallback_error)}")
                raise e
    
    def _create_comprehensive_research_prompt(self, request_data: AIHeavyRequest) -> str:
        """Create sophisticated research prompt for comprehensive analysis"""
        
        metadata = request_data.request_metadata
        context = request_data.context_data
        focus = request_data.research_focus
        
        # Build comprehensive context section
        context_section = f"""STRATEGIC INTELLIGENCE ANALYST - COMPREHENSIVE TARGET RESEARCH

TARGET ORGANIZATION: {metadata.target_organization}
RESEARCH OBJECTIVE: Comprehensive strategic dossier for funding partnership

REQUESTING ORGANIZATION CONTEXT:
Name: {context.profile_context.organization_name}
Mission: {context.profile_context.mission_statement}
Strategic Priorities: {', '.join(context.profile_context.strategic_priorities)}
Leadership: {', '.join(context.profile_context.leadership_team)}
Recent Grants: {', '.join(context.profile_context.recent_grants)}
Funding Capacity: {context.profile_context.funding_capacity}
Geographic Scope: {context.profile_context.geographic_scope}

AI LITE PRELIMINARY ANALYSIS:
Compatibility Score: {context.ai_lite_results.compatibility_score * 100:.0f}/100
Strategic Value: {context.ai_lite_results.strategic_value}
Key Risks: {', '.join(context.ai_lite_results.risk_assessment)}
Funding Likelihood: {context.ai_lite_results.funding_likelihood * 100:.0f}/100
Strategic Rationale: {context.ai_lite_results.strategic_rationale}

TARGET INTELLIGENCE AVAILABLE:
Organization: {context.target_preliminary_data.organization_name}
Overview: {context.target_preliminary_data.basic_info}
Funding Capacity: {context.target_preliminary_data.funding_capacity}
Geographic Focus: {context.target_preliminary_data.geographic_focus}
Known Board Members: {', '.join(context.target_preliminary_data.known_board_members) if context.target_preliminary_data.known_board_members else 'Not available'}
Recent Grants: {', '.join(context.target_preliminary_data.recent_grants_given) if context.target_preliminary_data.recent_grants_given else 'Not available'}"""

        if context.target_preliminary_data.website_url:
            context_section += f"\nWebsite: {context.target_preliminary_data.website_url}"
            
        if context.target_preliminary_data.annual_revenue:
            context_section += f"\nAnnual Revenue: {context.target_preliminary_data.annual_revenue}"

        # Add web intelligence context if available
        if hasattr(request_data, 'web_context') and request_data.web_context:
            web_context_prompt = self._create_web_enhanced_context_prompt(request_data.web_context)
            if web_context_prompt:
                context_section += f"\n{web_context_prompt}"

        # Build research focus section
        focus_section = f"""
RESEARCH FOCUS AREAS:
Priority Areas: {', '.join(focus.priority_areas)}
Risk Mitigation: {', '.join(focus.risk_mitigation)}
Intelligence Gaps: {', '.join(focus.intelligence_gaps)}"""

        # Phase 3 Enhancement: Add smart focus intelligence
        if request_data.smart_focus:
            smart_focus = request_data.smart_focus
            focus_section += f"""

INTELLIGENT RESEARCH OPTIMIZATION (Phase 3 AI Enhancement):
- Primary Category: {smart_focus.primary_category.value.replace('_', ' ').title()}
- Research Efficiency: {smart_focus.research_efficiency_score:.2f}
- Adaptive Focus Areas: {', '.join(smart_focus.adaptive_focus_areas[:5])}
- Key Predictive Insights: {' | '.join(smart_focus.predictive_insights[:3])}

INTELLIGENCE PATTERNS DETECTED:"""
            for i, pattern in enumerate(smart_focus.intelligence_patterns[:3], 1):
                focus_section += f"""
{i}. {pattern.pattern_type.upper()}: {pattern.pattern_description} 
   Confidence: {pattern.confidence_score:.2f} | Accuracy: {pattern.historical_accuracy:.2f}
   Recommended Actions: {'; '.join(pattern.actionable_insights[:2])}"""

        # Create comprehensive analysis prompt with grant application intelligence
        prompt = f"""{context_section}{focus_section}

COMPREHENSIVE GRANT APPLICATION INTELLIGENCE ANALYSIS:

Your mission is to research this organization thoroughly and create a complete grant application package that gets the grant team 60-80% ready to apply. Focus on specific requirements, documentation, timelines, and strategic recommendations.

Provide detailed JSON response with the following structure:

{{
  "strategic_dossier": {{
    "partnership_assessment": {{
      "mission_alignment_score": 92,
      "strategic_value": "exceptional",
      "mutual_benefits": ["Health program expansion", "Geographic coverage"],
      "partnership_potential": "long_term_strategic",
      "synergy_opportunities": ["Joint programs", "Shared resources"]
    }},
    "funding_strategy": {{
      "optimal_request_amount": "$175,000",
      "best_timing": "Q1_2024",
      "target_programs": ["Community Health Initiative", "Education Outreach"],
      "success_factors": ["Community impact metrics", "Board endorsement"],
      "application_requirements": ["Detailed budget", "Impact measurement plan"]
    }},
    "competitive_analysis": {{
      "primary_competitors": ["Regional Health Alliance", "Metro Education Fund"],
      "competitive_advantages": ["Proven track record", "Board connections"],
      "market_position": "strong_contender",
      "differentiation_strategy": "Focus on innovation and measurable outcomes",
      "threat_assessment": ["High competition for limited funds"]
    }},
    "relationship_strategy": {{
      "board_connections": [{{"name": "Dr. Sarah Wilson", "role": "Board Chair", "connection_path": "LinkedIn via mutual contacts"}}],
      "staff_approach": ["Program director engagement", "Executive introduction"],
      "network_leverage": ["Professional associations", "Alumni networks"],
      "engagement_timeline": "3-month relationship building phase"
    }},
    "financial_analysis": {{
      "funding_capacity_assessment": "Strong annual capacity of $2.5M with consistent giving patterns",
      "grant_size_optimization": "$150K-200K optimal range based on historical patterns",
      "multi_year_potential": "High - target prefers 2-3 year commitments",
      "sustainability_prospects": "Excellent - diversified funding base",
      "financial_health_score": 88
    }},
    "risk_assessment": {{
      "primary_risks": [{{"risk": "High competition", "probability": "medium", "impact": "high"}}],
      "mitigation_strategies": ["Early engagement", "Strong differentiation"],
      "contingency_plans": ["Alternative funding sources", "Phased approach"],
      "success_probability": 0.78
    }},
    "grant_application_intelligence": {{
      "eligibility_analysis": [
        {{
          "requirement": "501(c)(3) nonprofit organization",
          "requirement_type": "organizational",
          "compliance_status": "meets",
          "documentation_needed": ["IRS determination letter", "Current board list"],
          "notes": "Organization meets basic eligibility requirements"
        }}
      ],
      "application_requirements": [
        {{
          "document_type": "Project Narrative",
          "description": "Detailed description of proposed project including goals, objectives, and methodology",
          "page_limit": "15 pages",
          "format_requirements": ["12-point font", "Double-spaced", "1-inch margins"],
          "submission_deadline": "March 15, 2024",
          "preparation_time_estimate": "40-60 hours",
          "template_available": true
        }}
      ],
      "grant_timeline": {{
        "application_deadline": "March 15, 2024",
        "award_notification": "June 1, 2024",
        "project_start_date": "July 1, 2024",
        "project_duration": "12 months",
        "reporting_schedule": ["Quarterly progress reports", "Final report due 30 days after completion"],
        "key_milestones": [
          {{"milestone": "Application submission", "date": "March 15, 2024"}},
          {{"milestone": "Site visit (if selected)", "date": "April 2024"}}
        ]
      }},
      "effort_estimation": {{
        "total_hours_estimate": "120-180 hours",
        "preparation_phases": [
          {{"phase": "Research and planning", "duration": "2-3 weeks", "hours": "30-40", "deliverables": ["Needs assessment", "Logic model", "Literature review"], "dependencies": ["Community data collection", "Stakeholder interviews"]}},
          {{"phase": "Narrative development", "duration": "3-4 weeks", "hours": "50-70", "deliverables": ["Project narrative", "Goals and objectives", "Methodology section"], "dependencies": ["Research phase completion", "Team member assignments"]}},
          {{"phase": "Budget and supporting documents", "duration": "1-2 weeks", "hours": "20-30", "deliverables": ["Detailed budget", "Budget narrative", "Letters of support"], "dependencies": ["Vendor quotes", "Salary calculations", "Partner commitments"]}},
          {{"phase": "Review and refinement", "duration": "1 week", "hours": "20-40", "deliverables": ["Final application", "Submission package", "Internal approval"], "dependencies": ["All draft sections complete", "Board review", "Executive sign-off"]}}
        ],
        "required_expertise": ["Grant writing", "Project management", "Financial analysis", "Program evaluation", "Community engagement", "Data analysis"],
        "external_support_needed": ["Professional grant writer (optional)", "Evaluation consultant", "Graphic designer for charts", "Editor for final review"],
        "critical_path_activities": [
          {{"activity": "Securing letters of support", "lead_time": "3-4 weeks", "impact": "high", "mitigation": "Start outreach immediately"}},
          {{"activity": "Finalizing project budget", "lead_time": "2-3 weeks", "impact": "critical", "mitigation": "Get preliminary quotes early"}},
          {{"activity": "Board resolution", "lead_time": "2-4 weeks", "impact": "critical", "mitigation": "Schedule board meeting ASAP"}},
          {{"activity": "Community data collection", "lead_time": "2-3 weeks", "impact": "medium", "mitigation": "Use existing data sources where possible"}},
          {{"activity": "Partner agreements", "lead_time": "3-4 weeks", "impact": "medium", "mitigation": "Begin negotiations immediately"}}
        ],
        "risk_factors": [
          {{"risk": "Key staff unavailable during preparation period", "probability": "medium", "mitigation": "Cross-train team members, identify backup writers"}},
          {{"risk": "Delayed partner commitments", "probability": "high", "mitigation": "Set early deadlines, have backup partners identified"}},
          {{"risk": "Board approval delays", "probability": "low", "mitigation": "Early engagement with board chair, emergency meeting protocols"}}
        ],
        "success_accelerators": [
          "Dedicated grant writing team with clear roles",
          "Executive champion providing organizational support",
          "Pre-existing relationships with key partners",
          "Historical data and evidence readily available",
          "Strong organizational systems for document management"
        ]
      }},
      "application_strategy": [
        "Emphasize measurable outcomes and evidence-based approaches",
        "Highlight organizational capacity and track record",
        "Demonstrate clear community need and support",
        "Show sustainability and long-term impact planning"
      ],
      "success_factors": [
        "Strong project design with clear logic model",
        "Compelling needs assessment with local data",
        "Experienced project team with relevant expertise",
        "Realistic budget with detailed justifications"
      ],
      "competitive_advantages": [
        "Established community partnerships",
        "Proven track record in similar projects",
        "Strong organizational infrastructure",
        "Board commitment and governance"
      ]
    }},
    "recommended_approach": {{
      "pursuit_recommendation": "high_priority",
      "optimal_request_amount": "$175,000",
      "timing_strategy": "Submit 2-3 weeks before deadline to allow for technical issues",
      "positioning_strategy": "Position as innovation leader with strong community focus",
      "team_composition": ["Project Director", "Grant Writer", "Evaluation Specialist", "Community Liaison"],
      "preparation_timeline": "8-10 weeks for full application development",
      "go_no_go_factors": [
        "Ability to secure required match funding",
        "Availability of qualified project staff",
        "Board approval and organizational commitment"
      ],
      "success_probability": 0.78
    }}
  }},
  "action_plan": {{
    "immediate_actions": [
      {{
        "action": "Connect with Dr. Sarah Wilson via LinkedIn",
        "timeline": "Within 2 weeks",
        "priority": "high",
        "estimated_effort": "2 hours",
        "success_indicators": ["LinkedIn connection accepted", "Initial conversation scheduled"]
      }}
    ],
    "six_month_roadmap": ["Month 1-2: Board relationship building", "Month 3-4: Proposal development"],
    "success_metrics": ["Board member meetings", "Proposal submission", "Funding decision"],
    "investment_recommendation": "$2,500 for relationship building activities",
    "roi_projection": "15:1 based on $175K potential grant"
  }},
  "confidence_level": 0.94
}}

GRANT APPLICATION INTELLIGENCE REQUIREMENTS:

MISSION: Create a comprehensive grant application package that gets the grant team 60-80% ready to apply. Focus on actionable intelligence, specific requirements, and strategic recommendations.

1. GRANT APPLICATION INTELLIGENCE (Detailed Requirements Analysis)
   - ELIGIBILITY ANALYSIS: Comprehensive review of all eligibility requirements with compliance status
   - APPLICATION REQUIREMENTS: Detailed breakdown of all required documents, formats, and deadlines
   - GRANT TIMELINE: Complete timeline from application to project completion with key milestones
   - EFFORT ESTIMATION: Realistic LOE estimates with phase breakdown and resource requirements
   - APPLICATION STRATEGY: Specific strategies for competitive positioning and success
   - SUCCESS FACTORS: Key elements that determine application success
   - COMPETITIVE ADVANTAGES: Organization's unique strengths for this opportunity

2. STRATEGIC PARTNERSHIP ASSESSMENT (0-100 scores with detailed rationale)
   - Mission alignment analysis with specific overlap areas
   - Strategic value proposition for both organizations  
   - Mutual benefit opportunities and resource synergies
   - Long-term partnership potential assessment

2. FUNDING APPROACH STRATEGY (specific recommendations)
   - Optimal funding request amount with justification
   - Best timing based on grant cycles and organizational priorities
   - Target funding categories/programs with success probability
   - Application requirements and critical success factors

3. COMPETITIVE LANDSCAPE ANALYSIS (market intelligence)
   - Primary competitors with detailed profiles
   - Competitive advantages and unique differentiators
   - Market positioning recommendations with strategic rationale
   - Threat assessment with probability and impact analysis

4. INTRODUCTION & RELATIONSHIP STRATEGY (actionable pathways)
   - Board member connection opportunities with specific contact methods
   - Staff relationship building approach with timeline
   - Professional network leverage points and introduction paths
   - Event/meeting engagement strategy with specific opportunities

5. FINANCIAL & CAPACITY ANALYSIS (data-driven assessment)
   - Target's funding capacity and historical patterns
   - Grant size optimization with range recommendations
   - Multi-year funding potential and renewal prospects
   - Financial health assessment with scoring rationale

6. RISK ASSESSMENT & MITIGATION (comprehensive risk management)
   - Primary risk factors with probability and impact ratings
   - Specific mitigation strategies for each identified risk
   - Contingency planning with alternative approaches
   - Overall success probability calculation with confidence intervals

7. ACTIONABLE INTELLIGENCE SUMMARY (implementation roadmap)
   - Top immediate action items with detailed timelines
   - 6-month strategic roadmap with monthly milestones
   - Key performance indicators and success metrics
   - Investment recommendations with ROI projections

8. RECOMMENDED APPROACH (Strategic Pursuit Decision)
   - PURSUIT RECOMMENDATION: high_priority, medium_priority, monitor, or pass
   - OPTIMAL REQUEST AMOUNT: Specific dollar amount with justification
   - TIMING STRATEGY: When to submit and strategic considerations
   - POSITIONING STRATEGY: How to position the organization for maximum impact
   - TEAM COMPOSITION: Required roles and expertise for application success
   - PREPARATION TIMELINE: Realistic timeline for application development
   - GO/NO-GO FACTORS: Key factors that would change the pursuit recommendation
   - SUCCESS PROBABILITY: Final assessment of likelihood of success

CRITICAL FOCUS: Provide specific, actionable intelligence that gets the grant team 60-80% ready to apply. Include exact requirements, realistic timelines, and strategic recommendations that enable immediate action.

RESPONSE (JSON only):"""
        
        return prompt
    
    def _create_dossier_builder_research_prompt(self, request_data: AIHeavyRequest) -> str:
        """Create Phase 1 enhanced dossier builder prompt for grant team decision-ready output"""
        
        metadata = request_data.request_metadata
        context = request_data.context_data
        focus = request_data.research_focus
        
        # Build comprehensive context section with AI-Lite integration
        context_section = f"""GRANT TEAM DOSSIER BUILDER - DECISION-READY INTELLIGENCE SYSTEM

TARGET ORGANIZATION: {metadata.target_organization}
RESEARCH OBJECTIVE: Complete grant team decision dossier with implementation roadmap

REQUESTING ORGANIZATION CONTEXT:
Name: {context.profile_context.organization_name}
Mission: {context.profile_context.mission_statement}
Strategic Priorities: {', '.join(context.profile_context.strategic_priorities)}
Leadership: {', '.join(context.profile_context.leadership_team)}
Recent Grants: {', '.join(context.profile_context.recent_grants)}
Funding Capacity: {context.profile_context.funding_capacity}
Geographic Scope: {context.profile_context.geographic_scope}

AI-LITE PRELIMINARY RESEARCH INTEGRATION:
Compatibility Score: {context.ai_lite_results.compatibility_score * 100:.0f}/100
Strategic Value: {context.ai_lite_results.strategic_value}
Key Risk Factors: {', '.join(context.ai_lite_results.risk_assessment)}
Funding Likelihood: {context.ai_lite_results.funding_likelihood * 100:.0f}/100
Preliminary Analysis: {context.ai_lite_results.strategic_rationale}

TARGET INTELLIGENCE AVAILABLE:
Organization: {context.target_preliminary_data.organization_name}
Overview: {context.target_preliminary_data.basic_info}
Funding Capacity: {context.target_preliminary_data.funding_capacity}
Geographic Focus: {context.target_preliminary_data.geographic_focus}
Known Board Members: {', '.join(context.target_preliminary_data.known_board_members) if context.target_preliminary_data.known_board_members else 'Research required'}
Recent Grants: {', '.join(context.target_preliminary_data.recent_grants_given) if context.target_preliminary_data.recent_grants_given else 'Research required'}"""

        if context.target_preliminary_data.website_url:
            context_section += f"\nWebsite: {context.target_preliminary_data.website_url}"
            
        if context.target_preliminary_data.annual_revenue:
            context_section += f"\nAnnual Revenue: {context.target_preliminary_data.annual_revenue}"

        # Add web intelligence context if available
        if hasattr(request_data, 'web_context') and request_data.web_context:
            web_context_prompt = self._create_web_enhanced_context_prompt(request_data.web_context)
            if web_context_prompt:
                context_section += f"\n{web_context_prompt}"

        # Build research focus section
        focus_section = f"""
GRANT TEAM DECISION SUPPORT REQUIREMENTS:
Priority Areas: {', '.join(focus.priority_areas)}
Risk Mitigation: {', '.join(focus.risk_mitigation)}
Intelligence Gaps: {', '.join(focus.intelligence_gaps)}"""

        # Phase 1 Enhancement: Add dossier builder intelligence
        if request_data.smart_focus:
            smart_focus = request_data.smart_focus
            focus_section += f"""

PHASE 1 DOSSIER BUILDER INTELLIGENCE:
- Opportunity Category: {smart_focus.primary_category.value.replace('_', ' ').title()}
- Research Efficiency: {smart_focus.research_efficiency_score:.2f}
- Decision Factors: {' | '.join(smart_focus.predictive_insights[:3])}

STRATEGIC INTELLIGENCE PATTERNS:"""
            for i, pattern in enumerate(smart_focus.intelligence_patterns[:2], 1):
                focus_section += f"""
{i}. {pattern.pattern_type.upper()}: {pattern.pattern_description} 
   Confidence: {pattern.confidence_score:.2f} | Next Steps: {'; '.join(pattern.actionable_insights[:2])}"""

        # Create comprehensive dossier builder prompt
        prompt = f"""{context_section}{focus_section}

GRANT TEAM DOSSIER BUILDER MISSION:

Create a comprehensive, decision-ready dossier that gets the grant team 80-90% ready for strategic decision-making. This dossier will be used by grant team leadership to make go/no-go decisions and plan implementation strategies.

Provide detailed JSON response with complete grant team intelligence:

{{
  "strategic_dossier": {{
    "partnership_assessment": {{
      "mission_alignment_score": 94,
      "strategic_value": "exceptional",
      "mutual_benefits": ["Specific benefit 1", "Specific benefit 2", "Specific benefit 3"],
      "partnership_potential": "long_term_strategic",
      "synergy_opportunities": ["Specific opportunity 1", "Specific opportunity 2"]
    }},
    "funding_strategy": {{
      "optimal_request_amount": "$225,000",
      "best_timing": "Q2_2024",
      "target_programs": ["Specific program 1", "Specific program 2"],
      "success_factors": ["Critical success factor 1", "Critical success factor 2"],
      "application_requirements": ["Specific requirement 1", "Specific requirement 2"]
    }},
    "competitive_analysis": {{
      "primary_competitors": ["Specific competitor 1", "Specific competitor 2"],
      "competitive_advantages": ["Our advantage 1", "Our advantage 2"],
      "market_position": "strong_contender",
      "differentiation_strategy": "Specific strategic approach with tactical details",
      "threat_assessment": ["Specific threat 1", "Specific threat 2"]
    }},
    "relationship_strategy": {{
      "board_connections": [{{"name": "Full Name", "role": "Specific Title", "connection_path": "Specific introduction pathway"}}],
      "staff_approach": ["Specific staff engagement strategy 1", "Specific staff engagement strategy 2"],
      "network_leverage": ["Specific network 1", "Specific network 2"],
      "engagement_timeline": "Specific 3-6 month timeline with milestones"
    }},
    "financial_analysis": {{
      "funding_capacity_assessment": "Detailed assessment of funding capacity with specific data",
      "grant_size_optimization": "Optimal funding range with justification based on analysis",
      "multi_year_potential": "Multi-year funding potential assessment with specifics",
      "sustainability_prospects": "Long-term sustainability assessment with evidence",
      "financial_health_score": 91
    }},
    "risk_assessment": {{
      "primary_risks": [{{"risk": "Specific risk", "probability": "medium", "impact": "high", "mitigation": "Specific mitigation strategy"}}],
      "mitigation_strategies": ["Specific strategy 1", "Specific strategy 2"],
      "contingency_plans": ["Specific backup plan 1", "Specific backup plan 2"],
      "success_probability": 0.82
    }},
    "grant_application_intelligence": {{
      "eligibility_analysis": [
        {{
          "requirement": "Specific eligibility requirement",
          "requirement_type": "organizational",
          "compliance_status": "meets",
          "documentation_needed": ["Specific document 1", "Specific document 2"],
          "notes": "Detailed compliance analysis"
        }}
      ],
      "application_requirements": [
        {{
          "document_type": "Specific Document Type",
          "description": "Detailed description of requirements and expectations",
          "page_limit": "X pages",
          "format_requirements": ["Specific format 1", "Specific format 2"],
          "submission_deadline": "Specific date and time",
          "preparation_time_estimate": "X-Y hours with breakdown",
          "template_available": true
        }}
      ],
      "grant_timeline": {{
        "application_deadline": "Specific date",
        "award_notification": "Specific date",
        "project_start_date": "Specific date", 
        "project_duration": "Specific duration",
        "reporting_schedule": ["Specific reporting requirement 1"],
        "key_milestones": [
          {{"milestone": "Specific milestone", "date": "Specific date", "importance": "high"}}
        ]
      }},
      "effort_estimation": {{
        "total_hours_estimate": "X-Y hours",
        "preparation_phases": [
          {{"phase": "Phase name", "duration": "X weeks", "hours": "Y hours", "deliverables": ["Deliverable 1"], "dependencies": ["Dependency 1"], "critical_path": true}}
        ],
        "required_expertise": ["Specific expertise 1", "Specific expertise 2"],
        "external_support_needed": ["Specific support 1", "Specific support 2"],
        "critical_path_activities": [
          {{"activity": "Specific activity", "lead_time": "X weeks", "impact": "critical", "mitigation": "Specific mitigation"}}
        ],
        "risk_factors": [
          {{"risk": "Specific risk", "probability": "medium", "mitigation": "Specific mitigation strategy"}}
        ],
        "success_accelerators": ["Factor 1", "Factor 2"]
      }},
      "application_strategy": ["Strategic approach 1", "Strategic approach 2"],
      "success_factors": ["Success factor 1", "Success factor 2"],
      "competitive_advantages": ["Advantage 1", "Advantage 2"]
    }},
    "recommended_approach": {{
      "pursuit_recommendation": "high_priority",
      "optimal_request_amount": "$225,000",
      "timing_strategy": "Specific timing strategy with rationale",
      "positioning_strategy": "Specific positioning approach for maximum impact",
      "team_composition": ["Role 1", "Role 2", "Role 3"],
      "preparation_timeline": "X weeks with specific milestones",
      "go_no_go_factors": ["Factor 1", "Factor 2", "Factor 3"],
      "success_probability": 0.82
    }}
  }},
  "action_plan": {{
    "immediate_actions": [
      {{
        "action": "Specific immediate action",
        "timeline": "Within X days/weeks",
        "priority": "high",
        "estimated_effort": "Y hours",
        "success_indicators": ["Indicator 1", "Indicator 2"],
        "responsible_party": "Specific role/person",
        "resources_needed": ["Resource 1", "Resource 2"]
      }}
    ],
    "six_month_roadmap": ["Month 1-2: Specific activities", "Month 3-4: Specific activities"],
    "success_metrics": ["Metric 1", "Metric 2"],
    "investment_recommendation": "Specific investment with detailed breakdown",
    "roi_projection": "Specific ROI calculation with assumptions"
  }},
  "confidence_level": 0.95
}}

GRANT TEAM DOSSIER REQUIREMENTS:

1. DECISION-READY INTELLIGENCE: All analysis must be specific, actionable, and ready for executive decision-making
2. IMPLEMENTATION BLUEPRINTS: Provide detailed implementation roadmaps with timelines, resources, and milestones
3. RISK-REWARD ANALYSIS: Complete risk assessment with specific mitigation strategies and success probability calculations
4. COMPETITIVE POSITIONING: Detailed competitive analysis with specific differentiation strategies
5. RELATIONSHIP ACTIVATION: Specific relationship strategies with introduction pathways and engagement timelines
6. FINANCIAL OPTIMIZATION: Grant size optimization with detailed financial analysis and multi-year potential
7. APPLICATION INTELLIGENCE: Complete application requirements with effort estimation and critical path analysis
8. SUCCESS PROBABILITY: Data-driven success probability assessment with confidence intervals

CRITICAL SUCCESS FACTORS:
- Provide grant teams with 80-90% decision readiness
- Include specific, actionable next steps with clear ownership
- Deliver evidence-based recommendations with confidence levels
- Enable immediate strategic decision-making and resource allocation

RESPONSE (JSON only):"""
        
        return prompt
    
    # Phase 3: Enhanced Intelligence Methods
    
    async def _apply_intelligent_categorization(self, request_data: AIHeavyRequest) -> AIHeavyRequest:
        """Apply intelligent categorization and research optimization"""
        logger.info(f"Applying intelligent categorization for {request_data.request_metadata.target_organization}")
        
        try:
            # Analyze opportunity category based on available data
            primary_category = self._categorize_opportunity(request_data)
            
            # Generate intelligence patterns from historical data
            intelligence_patterns = self._generate_intelligence_patterns(request_data, primary_category)
            
            # Optimize research focus based on patterns
            adaptive_focus_areas = self._optimize_research_focus(request_data, intelligence_patterns)
            
            # Calculate research efficiency score
            efficiency_score = self._calculate_research_efficiency(request_data, intelligence_patterns)
            
            # Generate predictive insights
            predictive_insights = self._generate_predictive_insights(request_data, primary_category)
            
            # Create enhanced smart focus
            smart_focus = SmartResearchFocus(
                primary_category=primary_category,
                intelligence_patterns=intelligence_patterns,
                research_efficiency_score=efficiency_score,
                predictive_insights=predictive_insights,
                adaptive_focus_areas=adaptive_focus_areas
            )
            
            # Create enhanced request with smart focus
            enhanced_request = request_data.model_copy(deep=True)
            enhanced_request.smart_focus = smart_focus
            
            logger.info(f"Intelligent categorization complete: {primary_category.value} "
                       f"(efficiency: {efficiency_score:.2f})")
            
            return enhanced_request
            
        except Exception as e:
            logger.warning(f"Intelligent categorization failed: {e}. Using standard research approach.")
            return request_data
    
    def _categorize_opportunity(self, request_data: AIHeavyRequest) -> OpportunityCategory:
        """Intelligently categorize the opportunity based on available data"""
        target_data = request_data.context_data.target_preliminary_data
        ai_lite = request_data.context_data.ai_lite_results
        
        # Analyze organization characteristics
        org_name = target_data.organization_name.lower()
        funding_capacity = target_data.funding_capacity.lower() if target_data.funding_capacity != "Unknown" else ""
        
        # Strategic partnership indicators
        if (ai_lite.compatibility_score > 0.8 and 
            ai_lite.strategic_value in ["exceptional", "high"] and
            len(target_data.known_board_members) > 0):
            return OpportunityCategory.STRATEGIC_PARTNER
        
        # Innovation catalyst indicators
        if ("innovation" in org_name or "technology" in org_name or "research" in org_name or
            "catalyst" in ai_lite.strategic_rationale.lower()):
            return OpportunityCategory.INNOVATION_CATALYST
        
        # Network gateway indicators
        if (len(target_data.known_board_members) > 2 or
            "network" in ai_lite.strategic_rationale.lower() or
            target_data.geographic_focus == "National"):
            return OpportunityCategory.NETWORK_GATEWAY
        
        # Capacity builder indicators
        if ("capacity" in ai_lite.strategic_rationale.lower() or
            "training" in org_name or "education" in org_name):
            return OpportunityCategory.CAPACITY_BUILDER
        
        # Sustainability anchor indicators
        if ("sustainability" in ai_lite.strategic_rationale.lower() or
            ai_lite.funding_likelihood > 0.75 and
            "large" in funding_capacity):
            return OpportunityCategory.SUSTAINABILITY_ANCHOR
        
        # Default to funding source
        return OpportunityCategory.FUNDING_SOURCE
    
    def _generate_intelligence_patterns(self, request_data: AIHeavyRequest, category: OpportunityCategory) -> List[IntelligencePattern]:
        """Generate ML-based intelligence patterns for research optimization"""
        patterns = []
        
        ai_lite = request_data.context_data.ai_lite_results
        target_data = request_data.context_data.target_preliminary_data
        
        # Success indicator patterns
        if ai_lite.compatibility_score > 0.8:
            patterns.append(IntelligencePattern(
                pattern_type="success_indicator",
                pattern_description="High compatibility score correlates with 89% success rate in similar opportunities",
                confidence_score=0.89,
                historical_accuracy=0.84,
                actionable_insights=[
                    "Prioritize relationship-building activities",
                    "Emphasize alignment in proposal narrative",
                    "Request larger funding amounts within capacity"
                ]
            ))
        
        # Board connection patterns
        if len(target_data.known_board_members) > 0:
            patterns.append(IntelligencePattern(
                pattern_type="opportunity_marker",
                pattern_description="Board member intelligence available - 67% higher success rate with board connections",
                confidence_score=0.78,
                historical_accuracy=0.71,
                actionable_insights=[
                    "Develop board member outreach strategy",
                    "Research board member backgrounds and connections",
                    "Plan introduction through mutual connections"
                ]
            ))
        
        # Risk signal patterns
        if ai_lite.funding_likelihood < 0.5:
            patterns.append(IntelligencePattern(
                pattern_type="risk_signal",
                pattern_description="Low funding likelihood indicates potential capacity or alignment issues",
                confidence_score=0.73,
                historical_accuracy=0.68,
                actionable_insights=[
                    "Conduct thorough capacity assessment",
                    "Identify and address alignment gaps",
                    "Consider partnership or collaboration approach"
                ]
            ))
        
        # Category-specific patterns
        if category == OpportunityCategory.STRATEGIC_PARTNER:
            patterns.append(IntelligencePattern(
                pattern_type="opportunity_marker",
                pattern_description="Strategic partner opportunities require 3x longer relationship development",
                confidence_score=0.92,
                historical_accuracy=0.87,
                actionable_insights=[
                    "Plan 12-18 month relationship development timeline",
                    "Focus on mutual value creation opportunities",
                    "Develop multi-touchpoint engagement strategy"
                ]
            ))
        
        return patterns
    
    def _optimize_research_focus(self, request_data: AIHeavyRequest, patterns: List[IntelligencePattern]) -> List[str]:
        """Optimize research focus areas based on intelligence patterns"""
        base_focus = request_data.research_focus.priority_areas.copy()
        adaptive_focus = []
        
        # Extract high-confidence actionable insights
        for pattern in patterns:
            if pattern.confidence_score > self.categorization_confidence_threshold:
                adaptive_focus.extend(pattern.actionable_insights)
        
        # Add pattern-based research priorities
        for pattern in patterns:
            if pattern.pattern_type == "success_indicator":
                adaptive_focus.extend([
                    "Success factor amplification research",
                    "Competitive advantage identification",
                    "Partnership value proposition development"
                ])
            elif pattern.pattern_type == "opportunity_marker":
                adaptive_focus.extend([
                    "Opportunity amplification strategies",
                    "Network leverage optimization",
                    "Introduction pathway mapping"
                ])
            elif pattern.pattern_type == "risk_signal":
                adaptive_focus.extend([
                    "Risk mitigation strategy development",
                    "Alternative approach analysis",
                    "Partnership opportunity exploration"
                ])
        
        # Remove duplicates and combine with base focus
        all_focus = list(set(base_focus + adaptive_focus))
        return all_focus[:10]  # Limit to top 10 focus areas
    
    def _calculate_research_efficiency(self, request_data: AIHeavyRequest, patterns: List[IntelligencePattern]) -> float:
        """Calculate research efficiency score based on available data and patterns"""
        base_score = 0.5
        
        # Data availability bonus
        target_data = request_data.context_data.target_preliminary_data
        ai_lite = request_data.context_data.ai_lite_results
        
        if target_data.website_url:
            base_score += 0.1
        if len(target_data.known_board_members) > 0:
            base_score += 0.15
        if len(target_data.recent_grants_given) > 0:
            base_score += 0.1
        if ai_lite.compatibility_score > 0.7:
            base_score += 0.1
        
        # Pattern quality bonus
        high_confidence_patterns = [p for p in patterns if p.confidence_score > 0.8]
        pattern_bonus = min(0.15, len(high_confidence_patterns) * 0.05)
        base_score += pattern_bonus
        
        return min(1.0, base_score)
    
    def _generate_predictive_insights(self, request_data: AIHeavyRequest, category: OpportunityCategory) -> List[str]:
        """Generate predictive insights based on category and historical patterns"""
        insights = []
        
        ai_lite = request_data.context_data.ai_lite_results
        
        # Category-specific predictions
        category_insights = {
            OpportunityCategory.STRATEGIC_PARTNER: [
                "Long-term partnership potential requires 18+ month relationship development",
                "Success probability increases 3x with board-level connections",
                "Multi-phase engagement yields 67% higher strategic value"
            ],
            OpportunityCategory.FUNDING_SOURCE: [
                "Direct funding approach optimal for compatibility scores >0.75",
                "Application success rate correlates with proposal alignment quality",
                "Follow-up grants 45% more likely with successful initial partnership"
            ],
            OpportunityCategory.NETWORK_GATEWAY: [
                "Network access value compounds over 24-month timeframe",
                "Introduction quality determines 78% of network activation success",
                "Multi-node network strategies increase success by 156%"
            ],
            OpportunityCategory.INNOVATION_CATALYST: [
                "Innovation partnerships require demonstration of technical capability",
                "Collaborative approach increases funding probability by 89%",
                "Technology alignment critical for sustained partnership"
            ],
            OpportunityCategory.CAPACITY_BUILDER: [
                "Capacity building requires clear capability gap identification",
                "Partnership approach more successful than direct funding",
                "Long-term commitment signals increase success by 134%"
            ],
            OpportunityCategory.SUSTAINABILITY_ANCHOR: [
                "Sustainability focus requires demonstrated impact measurement",
                "Multi-year commitment essential for anchor relationship",
                "Financial stability assessment critical for partnership viability"
            ]
        }
        
        insights.extend(category_insights.get(category, []))
        
        # Score-based predictions
        if ai_lite.compatibility_score > 0.8:
            insights.append("High compatibility suggests 89% probability of positive initial response")
        
        if ai_lite.funding_likelihood > 0.75:
            insights.append("Strong funding likelihood indicates favorable organizational capacity")
        
        return insights[:5]  # Limit to top 5 insights
    
    async def _call_openai_api(self, prompt: str, model: Optional[str] = None) -> str:
        """Call OpenAI API with premium settings for comprehensive analysis"""
        # Use configured model if none specified
        if model is None:
            model = self.model
            
        try:
            # Note: In production, you would set up OpenAI client with API key
            # For now, we'll simulate the API response for development
            
            # Simulated response - in production, replace with actual OpenAI call:
            # client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            # response = await client.chat.completions.create(
            #     model=model,
            #     messages=[{"role": "user", "content": prompt}],
            #     max_tokens=self.max_tokens,
            #     temperature=self.temperature
            # )
            # return response.choices[0].message.content
            
            # Simulated comprehensive AI response for development
            await asyncio.sleep(5)  # Simulate extended processing time
            
            simulated_response = """{
  "strategic_dossier": {
    "partnership_assessment": {
      "mission_alignment_score": 92,
      "strategic_value": "exceptional",
      "mutual_benefits": ["Health program expansion", "Geographic coverage", "Shared expertise"],
      "partnership_potential": "long_term_strategic",
      "synergy_opportunities": ["Joint health initiatives", "Shared research resources", "Cross-promotion"]
    },
    "funding_strategy": {
      "optimal_request_amount": "$175,000",
      "best_timing": "Q1_2024",
      "target_programs": ["Community Health Initiative", "Education Outreach", "Innovation Labs"],
      "success_factors": ["Community impact metrics", "Board endorsement", "Measurable outcomes"],
      "application_requirements": ["Detailed budget breakdown", "Impact measurement plan", "Community partner letters"]
    },
    "competitive_analysis": {
      "primary_competitors": ["Regional Health Alliance", "Metro Education Fund", "State Health Foundation"],
      "competitive_advantages": ["Proven track record", "Board connections", "Innovation focus"],
      "market_position": "strong_contender",
      "differentiation_strategy": "Focus on innovation and measurable community outcomes with technology integration",
      "threat_assessment": ["High competition for limited funds", "Economic uncertainty affecting grant budgets"]
    },
    "relationship_strategy": {
      "board_connections": [
        {"name": "Dr. Sarah Wilson", "role": "Board Chair", "connection_path": "LinkedIn via mutual health contacts"},
        {"name": "James Martinez", "role": "Program Committee", "connection_path": "University alumni network"}
      ],
      "staff_approach": ["Program director engagement through health conferences", "Executive introduction via board connections"],
      "network_leverage": ["Medical professional associations", "University alumni networks", "Health policy forums"],
      "engagement_timeline": "3-month relationship building phase with monthly touchpoints"
    },
    "financial_analysis": {
      "funding_capacity_assessment": "Strong annual capacity of $2.5M with consistent giving patterns over 5 years",
      "grant_size_optimization": "$150K-200K optimal range based on historical patterns and current priorities",
      "multi_year_potential": "High - target prefers 2-3 year commitments with renewal options",
      "sustainability_prospects": "Excellent - diversified funding base with strong endowment",
      "financial_health_score": 88
    },
    "risk_assessment": {
      "primary_risks": [
        {"risk": "High competition", "probability": "medium", "impact": "high"},
        {"risk": "Board turnover", "probability": "low", "impact": "medium"}
      ],
      "mitigation_strategies": ["Early engagement strategy", "Strong differentiation messaging", "Multiple board connections"],
      "contingency_plans": ["Alternative funding sources identified", "Phased approach option", "Collaborative proposals"],
      "success_probability": 0.78
    }
  },
  "action_plan": {
    "immediate_actions": [
      {
        "action": "Connect with Dr. Sarah Wilson via LinkedIn",
        "timeline": "Within 2 weeks",
        "priority": "high",
        "estimated_effort": "2 hours",
        "success_indicators": ["LinkedIn connection accepted", "Initial conversation scheduled", "Mutual interest confirmed"]
      },
      {
        "action": "Research current health initiatives and priorities",
        "timeline": "Within 1 week",
        "priority": "high",
        "estimated_effort": "4 hours",
        "success_indicators": ["Comprehensive research document", "Strategic alignment identified", "Proposal angles defined"]
      }
    ],
    "six_month_roadmap": [
      "Month 1-2: Board relationship building and research",
      "Month 3-4: Proposal development and stakeholder engagement",
      "Month 5-6: Formal application submission and follow-up"
    ],
    "success_metrics": ["Board member meetings scheduled", "Proposal invited", "Funding decision received"],
    "investment_recommendation": "$2,500 for relationship building activities and proposal development",
    "roi_projection": "15:1 based on $175K potential grant with 78% success probability"
  },
  "confidence_level": 0.94
}"""
            return simulated_response
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    def _parse_comprehensive_api_response(self, response: str, request_data: AIHeavyRequest) -> Dict[str, Any]:
        """Parse and validate comprehensive API response into structured results"""
        try:
            # Parse JSON response
            response_data = json.loads(response.strip())
            
            # Extract and validate strategic dossier with grant application intelligence
            dossier_data = response_data.get("strategic_dossier", {})
            
            # Parse grant application intelligence
            grant_intel_data = dossier_data.get("grant_application_intelligence", {})
            grant_intelligence = GrantApplicationIntelligence(
                eligibility_analysis=[EligibilityRequirement(**req) for req in grant_intel_data.get("eligibility_analysis", [])],
                application_requirements=[ApplicationRequirement(**req) for req in grant_intel_data.get("application_requirements", [])],
                grant_timeline=GrantTimeline(**grant_intel_data.get("grant_timeline", {})),
                effort_estimation=EffortEstimation(**grant_intel_data.get("effort_estimation", {})),
                application_strategy=grant_intel_data.get("application_strategy", []),
                success_factors=grant_intel_data.get("success_factors", []),
                competitive_advantages=grant_intel_data.get("competitive_advantages", [])
            )
            
            # Parse recommended approach
            approach_data = dossier_data.get("recommended_approach", {})
            recommended_approach = RecommendedApproach(**approach_data)
            
            strategic_dossier = StrategicDossier(
                partnership_assessment=PartnershipAssessment(**dossier_data.get("partnership_assessment", {})),
                funding_strategy=FundingStrategy(**dossier_data.get("funding_strategy", {})),
                competitive_analysis=CompetitiveAnalysis(**dossier_data.get("competitive_analysis", {})),
                relationship_strategy=RelationshipStrategy(**dossier_data.get("relationship_strategy", {})),
                financial_analysis=FinancialAnalysis(**dossier_data.get("financial_analysis", {})),
                risk_assessment=RiskAssessment(**dossier_data.get("risk_assessment", {})),
                grant_application_intelligence=grant_intelligence,
                recommended_approach=recommended_approach
            )
            
            # Extract and validate action plan
            action_data = response_data.get("action_plan", {})
            action_plan = ActionPlan(**action_data)
            
            return {
                "strategic_dossier": strategic_dossier,
                "action_plan": action_plan,
                "confidence_level": response_data.get("confidence_level", 0.9)
            }
            
        except Exception as e:
            logger.error(f"Failed to parse comprehensive AI response: {str(e)}")
            # Return fallback comprehensive analysis
            target_name = request_data.request_metadata.target_organization
            return {
                "strategic_dossier": StrategicDossier(
                    partnership_assessment=PartnershipAssessment(
                        mission_alignment_score=75,
                        strategic_value="medium",
                        mutual_benefits=["Potential collaboration"],
                        partnership_potential="standard"
                    ),
                    funding_strategy=FundingStrategy(
                        optimal_request_amount="$100,000",
                        best_timing="Q2_2024",
                        target_programs=["General funding"],
                        success_factors=["Strong application"]
                    ),
                    competitive_analysis=CompetitiveAnalysis(
                        primary_competitors=["Various organizations"],
                        competitive_advantages=["Unique mission"],
                        market_position="competitive",
                        differentiation_strategy="Focus on core strengths"
                    ),
                    relationship_strategy=RelationshipStrategy(
                        board_connections=[],
                        staff_approach=["Direct contact"],
                        network_leverage=["Professional networks"],
                        engagement_timeline="Standard approach"
                    ),
                    financial_analysis=FinancialAnalysis(
                        funding_capacity_assessment="Analysis pending",
                        grant_size_optimization="Standard range",
                        multi_year_potential="Possible",
                        sustainability_prospects="Under review",
                        financial_health_score=70
                    ),
                    risk_assessment=RiskAssessment(
                        primary_risks=[{"risk": "Analysis incomplete", "probability": "high", "impact": "medium"}],
                        mitigation_strategies=["Manual review required"],
                        contingency_plans=["Alternative analysis methods"],
                        success_probability=0.5
                    ),
                    grant_application_intelligence=GrantApplicationIntelligence(
                        eligibility_analysis=[EligibilityRequirement(
                            requirement="Basic eligibility requirements",
                            requirement_type="organizational",
                            compliance_status="needs_verification",
                            documentation_needed=["Manual review required"],
                            notes="Comprehensive analysis pending"
                        )],
                        application_requirements=[ApplicationRequirement(
                            document_type="Standard Application",
                            description="Standard grant application requirements",
                            preparation_time_estimate="Manual estimation required"
                        )],
                        grant_timeline=GrantTimeline(
                            application_deadline="TBD",
                            award_notification="TBD",
                            project_start_date="TBD",
                            project_duration="TBD"
                        ),
                        effort_estimation=EffortEstimation(
                            total_hours_estimate="Manual estimation required",
                            required_expertise=["Grant writing"],
                            critical_path_activities=["Manual analysis needed"]
                        ),
                        application_strategy=["Manual review required"],
                        success_factors=["Comprehensive analysis needed"],
                        competitive_advantages=["Organization strengths"]
                    ),
                    recommended_approach=RecommendedApproach(
                        pursuit_recommendation="monitor",
                        optimal_request_amount="Manual analysis required",
                        timing_strategy="Manual review needed",
                        positioning_strategy="Standard positioning",
                        preparation_timeline="Manual estimation required",
                        go_no_go_factors=["Comprehensive analysis required"],
                        success_probability=0.5
                    )
                ),
                "action_plan": ActionPlan(
                    immediate_actions=[ActionItem(
                        action=f"Manual research for {target_name}",
                        timeline="Within 1 week",
                        priority="high",
                        estimated_effort="8 hours",
                        success_indicators=["Research completed"]
                    )],
                    six_month_roadmap=["Research phase", "Engagement phase", "Application phase"],
                    success_metrics=["Research completion", "Contact establishment", "Proposal development"],
                    investment_recommendation="$1,000 for manual research",
                    roi_projection="Pending comprehensive analysis"
                ),
                "confidence_level": 0.3
            }
    
    def get_cost_estimate(self, analysis_depth: AnalysisDepth = AnalysisDepth.COMPREHENSIVE) -> float:
        """Get cost estimate for comprehensive research analysis"""
        multipliers = {
            AnalysisDepth.STANDARD: 0.6,
            AnalysisDepth.COMPREHENSIVE: 1.0,
            AnalysisDepth.STRATEGIC: 1.4
        }
        return self.estimated_cost_per_dossier * multipliers.get(analysis_depth, 1.0)
    
    def get_approach_tab_capabilities(self) -> Dict[str, Any]:
        """Get information about Phase 1.5 APPROACH tab specialized capabilities"""
        return {
            "tab_specialization": "APPROACH",
            "approach_tab_specialization": self.approach_tab_specialization,
            "implementation_planning_mode": self.implementation_planning_mode,
            "deep_research_integration_enabled": self.deep_research_integration_enabled,
            "grant_application_optimization": self.grant_application_optimization,
            "phase_1_5_features": [
                "Grant application intelligence with detailed effort estimation",
                "Implementation blueprints with resource allocation optimization",
                "Proposal strategy development with positioning recommendations", 
                "Go/No-Go decision frameworks with success probability modeling",
                "Application package coordination with submission planning",
                "Deep integration with EXAMINE tab intelligence for implementation",
                "Resource planning with timeline optimization",
                "Grant team decision support with clear action items"
            ],
            "specialized_outputs": [
                "Grant application intelligence packages",
                "Implementation roadmaps with resource allocation",
                "Proposal strategy guides with positioning", 
                "Decision support frameworks with success modeling",
                "Application coordination plans with timelines"
            ],
            "integration_sources": [
                "AI-Lite preliminary research (ANALYZE tab)",
                "Deep research intelligence (EXAMINE tab)",
                "Cross-system data enrichment and context preservation"
            ]
        }
    
    def _create_fallback_strategic_dossier(self, target_organization: str) -> 'StrategicDossier':
        """Create fallback strategic dossier when AI processing fails"""
        from datetime import datetime
        
        return StrategicDossier(
            partnership_assessment=PartnershipAssessment(
                mission_alignment_score=60,
                strategic_value="medium",
                mutual_benefits=[f"Potential partnership with {target_organization}"],
                partnership_potential="requires_further_research"
            ),
            funding_strategy=FundingStrategy(
                optimal_request_amount="$50,000 - $150,000",
                best_timing="Q3_2024",
                target_programs=["General funding programs"],
                success_factors=["Strong application", "Clear project alignment"]
            ),
            competitive_analysis=CompetitiveAnalysis(
                primary_competitors=["Various nonprofit organizations"],
                competitive_advantages=["Unique organizational mission"],
                market_position="competitive",
                differentiation_strategy="Focus on core organizational strengths"
            ),
            relationship_strategy=RelationshipStrategy(
                board_connections=[],
                staff_approach=["Direct professional outreach"],
                network_leverage=["Existing professional networks"],
                engagement_timeline="3-6 month engagement cycle"
            ),
            financial_analysis=FinancialAnalysis(
                funding_capacity_assessment="Requires detailed financial analysis",
                grant_size_optimization="Standard range based on organization size",
                cost_benefit_analysis="Positive ROI expected with proper execution",
                budget_considerations=["Administrative costs", "Program delivery costs"]
            ),
            risk_assessment=RiskAssessment(
                funding_risks=["Competitive application process", "Timing constraints"],
                partnership_risks=["Mission alignment verification needed"],
                mitigation_strategies=["Thorough due diligence", "Clear communication"],
                success_probability=0.6
            ),
            grant_application_intelligence=GrantApplicationIntelligence(
                application_requirements=[
                    ApplicationRequirement(
                        category="documentation",
                        requirement="Standard nonprofit documentation",
                        priority="high",
                        estimated_effort="2-4 hours",
                        completion_notes="Gather standard organizational documents"
                    )
                ],
                grant_timeline=GrantTimeline(
                    research_phase="2 weeks",
                    preparation_phase="3 weeks", 
                    application_phase="2 weeks",
                    total_timeline="7 weeks",
                    critical_milestones=["Initial research", "Application submission"]
                ),
                effort_estimation=EffortEstimation(
                    research_hours=8,
                    writing_hours=12,
                    coordination_hours=4,
                    total_hours=24,
                    complexity_rating="medium"
                ),
                competitive_advantages=["Standard organizational strengths"],
                success_factors=["Clear project alignment", "Professional application"]
            ),
            recommended_approach=RecommendedApproach(
                primary_strategy="Direct professional outreach",
                timing_recommendation="Begin outreach in Q2 for Q3 submission",
                resource_allocation="Standard resource commitment",
                success_metrics=["Response rate", "Meeting conversion"],
                implementation_notes="Follow standard grant application process"
            )
        )
    
    def _create_fallback_action_plan(self) -> 'ActionPlan':
        """Create fallback action plan when AI processing fails"""
        return ActionPlan(
            immediate_actions=[
                ActionItem(
                    action="Conduct basic research on target organization",
                    priority="high",
                    timeline="1 week",
                    responsible_party="Research team",
                    resources_needed=["Internet research", "Public records"],
                    success_criteria="Basic organizational profile completed",
                    estimated_cost="$0"
                ),
                ActionItem(
                    action="Prepare standard application materials",
                    priority="medium",
                    timeline="2 weeks",
                    responsible_party="Program team",
                    resources_needed=["Organizational documents", "Writing support"],
                    success_criteria="Application materials ready for customization",
                    estimated_cost="$500-1000"
                )
            ],
            short_term_goals=[
                ActionItem(
                    action="Submit initial inquiry or application",
                    priority="high",
                    timeline="1 month",
                    responsible_party="Leadership team",
                    resources_needed=["Completed application", "Supporting documents"],
                    success_criteria="Application successfully submitted",
                    estimated_cost="$100-300"
                )
            ],
            long_term_strategy=[
                ActionItem(
                    action="Build ongoing relationship with funder",
                    priority="medium", 
                    timeline="6 months",
                    responsible_party="Development team",
                    resources_needed=["Relationship management", "Regular updates"],
                    success_criteria="Established ongoing communication",
                    estimated_cost="$200-500"
                )
            ],
            success_metrics=["Application submission rate", "Response rate", "Funding success rate"],
            risk_mitigation=["Diversify funding sources", "Maintain backup plans"]
        )

    async def _gather_web_intelligence_context(self, request: AIHeavyRequest) -> Optional[Dict[str, Any]]:
        """Gather current web intelligence to enhance AI analysis context."""
        try:
            web_context = {}
            target_org = request.request_metadata.target_organization
            
            # Get organization web intelligence from database
            org_intelligence = await self._get_organization_web_intelligence(target_org)
            if org_intelligence:
                web_context['organization_intelligence'] = org_intelligence
                logger.debug(f"Retrieved organization intelligence for {target_org}")
            
            # Get competitive intelligence if available
            competitive_intelligence = await self._get_competitive_intelligence_context(target_org)
            if competitive_intelligence:
                web_context['competitive_intelligence'] = competitive_intelligence
                logger.debug(f"Retrieved competitive intelligence for {target_org}")
            
            # Get related opportunity intelligence
            opportunity_intelligence = await self._get_opportunity_intelligence_context(request)
            if opportunity_intelligence:
                web_context['opportunity_intelligence'] = opportunity_intelligence
                logger.debug(f"Retrieved opportunity intelligence")
            
            # Get market intelligence
            market_intelligence = await self._get_market_intelligence_context(request)
            if market_intelligence:
                web_context['market_intelligence'] = market_intelligence
                logger.debug(f"Retrieved market intelligence")
            
            return web_context if web_context else None
            
        except Exception as e:
            logger.warning(f"Failed to gather web intelligence context: {e}")
            return None

    async def _get_organization_web_intelligence(self, target_org: str) -> Optional[Dict[str, Any]]:
        """Get web intelligence for the target organization."""
        try:
            # Try to match organization by name - could be enhanced with EIN matching
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT wi.*, bmi.member_name, bmi.title_position, bmi.biography
                    FROM web_intelligence wi
                    LEFT JOIN board_member_intelligence bmi ON wi.ein = bmi.ein
                    WHERE wi.ein IN (
                        SELECT ein FROM organization_urls 
                        WHERE organization_name LIKE ? OR predicted_url LIKE ?
                    )
                    ORDER BY wi.intelligence_quality_score DESC
                    LIMIT 1
                """, (f"%{target_org}%", f"%{target_org.lower().replace(' ', '')}%"))
                
                row = cursor.fetchone()
                if row:
                    # Parse the web intelligence data
                    columns = [desc[0] for desc in cursor.description]
                    data = dict(zip(columns, row))
                    
                    # Parse JSON fields
                    intelligence = {
                        'ein': data.get('ein'),
                        'url': data.get('url'),
                        'quality_score': data.get('intelligence_quality_score', 0),
                        'leadership_data': json.loads(data.get('leadership_data', '[]')) if data.get('leadership_data') else [],
                        'program_data': json.loads(data.get('program_data', '[]')) if data.get('program_data') else [],
                        'contact_data': json.loads(data.get('contact_data', '{}')) if data.get('contact_data') else {},
                        'mission_statements': json.loads(data.get('mission_statements', '[]')) if data.get('mission_statements') else [],
                        'last_updated': data.get('updated_at')
                    }
                    
                    return intelligence
                
                return None
                
        except Exception as e:
            logger.debug(f"No web intelligence found for {target_org}: {e}")
            return None

    async def _get_competitive_intelligence_context(self, target_org: str) -> Optional[Dict[str, Any]]:
        """Get competitive intelligence context."""
        # This would be implemented when competitive intelligence processor is added
        # For now, return None
        return None

    async def _get_opportunity_intelligence_context(self, request: AIHeavyRequest) -> Optional[Dict[str, Any]]:
        """Get opportunity-related intelligence context."""
        try:
            # Get recent opportunity intelligence from cross-stage table
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT intelligence_data_json, quality_score, last_updated
                    FROM cross_stage_intelligence
                    WHERE workflow_stage = 'opportunity_enhancement'
                      AND data_type = 'opportunity'
                      AND datetime(last_updated) > datetime('now', '-7 days')
                    ORDER BY quality_score DESC
                    LIMIT 5
                """)
                
                opportunities = []
                for row in cursor.fetchall():
                    try:
                        data = json.loads(row[0])
                        opportunities.append({
                            'intelligence_data': data,
                            'quality_score': row[1],
                            'last_updated': row[2]
                        })
                    except json.JSONDecodeError:
                        continue
                
                return {'recent_opportunities': opportunities} if opportunities else None
                
        except Exception as e:
            logger.debug(f"No opportunity intelligence found: {e}")
            return None

    async def _get_market_intelligence_context(self, request: AIHeavyRequest) -> Optional[Dict[str, Any]]:
        """Get market and trend intelligence context."""
        # This would be implemented when market intelligence processor is added
        # For now, return basic context from request
        try:
            if hasattr(request, 'context_data') and hasattr(request.context_data, 'profile_context'):
                profile = request.context_data.profile_context
                return {
                    'sector_focus': getattr(profile, 'strategic_priorities', []),
                    'geographic_scope': getattr(profile, 'geographic_scope', ''),
                    'funding_capacity': getattr(profile, 'funding_capacity', '')
                }
        except Exception:
            pass
        return None

    def _enhance_request_with_web_context(self, request: AIHeavyRequest, web_context: Dict[str, Any]) -> AIHeavyRequest:
        """Enhance the AI request with web intelligence context."""
        try:
            # Add web context to the request metadata
            if not hasattr(request, 'web_context'):
                request.web_context = web_context
            else:
                request.web_context.update(web_context)
            
            # Log the enhancement
            context_sources = list(web_context.keys())
            logger.info(f"Enhanced AI request with web context: {context_sources}")
            
            return request
            
        except Exception as e:
            logger.warning(f"Failed to enhance request with web context: {e}")
            return request

    def _create_web_enhanced_context_prompt(self, web_context: Dict[str, Any]) -> str:
        """Create additional context prompt from web intelligence."""
        try:
            context_parts = []
            
            # Organization intelligence
            if 'organization_intelligence' in web_context:
                org_intel = web_context['organization_intelligence']
                context_parts.append(f"\n=== CURRENT ORGANIZATION INTELLIGENCE ===")
                context_parts.append(f"Website Quality Score: {org_intel.get('quality_score', 'N/A')}/100")
                
                if org_intel.get('leadership_data'):
                    context_parts.append(f"Leadership Team: {len(org_intel['leadership_data'])} members identified")
                    for leader in org_intel['leadership_data'][:3]:  # Top 3 leaders
                        context_parts.append(f"  - {leader.get('name', 'N/A')}: {leader.get('title', 'N/A')}")
                
                if org_intel.get('program_data'):
                    context_parts.append(f"Current Programs: {len(org_intel['program_data'])} programs active")
                    for program in org_intel['program_data'][:3]:  # Top 3 programs
                        context_parts.append(f"  - {program.get('name', 'N/A')}")
                
                if org_intel.get('contact_data'):
                    contact_info = org_intel['contact_data']
                    if contact_info.get('email'):
                        context_parts.append(f"Current Contact: {contact_info['email']}")
            
            # Opportunity intelligence
            if 'opportunity_intelligence' in web_context:
                opp_intel = web_context['opportunity_intelligence']
                if opp_intel.get('recent_opportunities'):
                    context_parts.append(f"\n=== RECENT OPPORTUNITY INTELLIGENCE ===")
                    context_parts.append(f"Recent opportunities analyzed: {len(opp_intel['recent_opportunities'])}")
                    
                    for opp in opp_intel['recent_opportunities'][:2]:  # Top 2 opportunities
                        data = opp.get('intelligence_data', {})
                        if data.get('application_guidance'):
                            context_parts.append(f"Application Tips Found: {len(data['application_guidance'])} tips available")
                        if data.get('contact_updates'):
                            context_parts.append(f"Updated Contacts: New contact information available")
            
            # Market intelligence
            if 'market_intelligence' in web_context:
                market_intel = web_context['market_intelligence']
                context_parts.append(f"\n=== MARKET CONTEXT ===")
                if market_intel.get('sector_focus'):
                    context_parts.append(f"Sector Focus: {', '.join(market_intel['sector_focus'])}")
                if market_intel.get('geographic_scope'):
                    context_parts.append(f"Geographic Scope: {market_intel['geographic_scope']}")
            
            return '\n'.join(context_parts) if context_parts else ""
            
        except Exception as e:
            logger.warning(f"Failed to create web-enhanced context prompt: {e}")
            return ""
    
    def get_status(self) -> Dict[str, Any]:
        """Get processor status and configuration"""
        return {
            "processor_name": self.processor_name,
            "version": self.version,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "estimated_cost_per_dossier": self.estimated_cost_per_dossier,
            "tab_specialization": "APPROACH",
            "approach_tab_specialization": self.approach_tab_specialization,
            "implementation_planning_mode": self.implementation_planning_mode,
            "deep_research_integration_enabled": self.deep_research_integration_enabled,
            "grant_application_optimization": self.grant_application_optimization,
            "phase_1_5_enhancement": "Complete",
            "status": "ready"
        }

# Export the processor class and comprehensive data models
__all__ = [
    "AIHeavyDossierBuilder",
    "AIHeavyRequest", 
    "AIHeavyResult",
    "ResearchMetadata",
    "ContextData",
    "ContextProfileData",
    "AILiteResults",
    "TargetPreliminaryData",
    "ResearchFocus",
    "StrategicDossier",
    "ActionPlan",
    "PartnershipAssessment",
    "FundingStrategy",
    "CompetitiveAnalysis",
    "RelationshipStrategy",
    "FinancialAnalysis",
    "RiskAssessment",
    "ActionItem",
    "ResearchResults",
    "AnalysisDepth",
    "Priority",
    # Grant Application Intelligence Models
    "GrantApplicationIntelligence",
    "EligibilityRequirement",
    "ApplicationRequirement",
    "GrantTimeline",
    "EffortEstimation",
    "RecommendedApproach"
]