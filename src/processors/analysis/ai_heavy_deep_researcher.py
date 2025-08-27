"""
AI Heavy Deep Research Tool - Specialized Intelligence Gathering for EXAMINE tab

Purpose: Comprehensive strategic intelligence and research analysis
Model: GPT-4 for sophisticated research analysis (~$0.08-0.15 per deep research)
Processing: Deep intelligence gathering with multi-thousand token research output

Phase 1.5 Specialized Features:
- Deep relationship intelligence and network mapping
- Comprehensive competitive landscape analysis  
- Financial deep-dive with multi-year funding potential
- Strategic partnership assessment with synergy identification
- Market intelligence and positioning analysis
- Risk assessment with sophisticated mitigation strategies
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import openai
from pydantic import BaseModel, Field
from enum import Enum

from src.core.base_processor import BaseProcessor, ProcessorMetadata

logger = logging.getLogger(__name__)

# Deep Research Specialized Data Models

class ResearchDepth(str, Enum):
    FOCUSED = "focused"
    COMPREHENSIVE = "comprehensive"
    STRATEGIC = "strategic"

class IntelligenceType(str, Enum):
    RELATIONSHIP = "relationship"
    COMPETITIVE = "competitive"
    FINANCIAL = "financial"
    STRATEGIC = "strategic"
    MARKET = "market"
    RISK = "risk"

class DeepResearchMetadata(BaseModel):
    """Deep research request metadata"""
    research_id: str
    profile_id: str
    target_organization: str
    research_depth: ResearchDepth = ResearchDepth.COMPREHENSIVE
    intelligence_types: List[IntelligenceType] = Field(default_factory=list)
    model_preference: str = "gpt-5-mini"
    research_budget: float = 0.10
    priority: str = "standard"

class OrganizationIntelligence(BaseModel):
    """Organization intelligence from AI-Lite"""
    organization_name: str
    mission_statement: str
    strategic_priorities: List[str] = Field(default_factory=list)
    leadership_team: List[str] = Field(default_factory=list)
    recent_grants: List[str] = Field(default_factory=list)
    funding_capacity: str = ""
    geographic_scope: str = ""

class AILiteResearchResults(BaseModel):
    """AI-Lite research results integration"""
    compatibility_score: float
    strategic_value: str
    risk_assessment: List[str]
    funding_likelihood: float
    strategic_rationale: str
    research_evidence: Optional[Dict[str, Any]] = None

class TargetIntelligenceData(BaseModel):
    """Target organization intelligence"""
    organization_name: str
    basic_info: str = ""
    funding_capacity: str = ""
    geographic_focus: str = ""
    known_board_members: List[str] = Field(default_factory=list)
    recent_grants_given: List[str] = Field(default_factory=list)
    website_url: Optional[str] = None
    annual_revenue: Optional[str] = None

class ResearchFocusAreas(BaseModel):
    """Research focus areas for intelligence gathering"""
    priority_areas: List[str] = Field(default_factory=list)
    intelligence_gaps: List[str] = Field(default_factory=list)
    specific_questions: List[str] = Field(default_factory=list)
    research_objectives: List[str] = Field(default_factory=list)

class DeepResearchContext(BaseModel):
    """Complete context for deep research"""
    organization_intelligence: OrganizationIntelligence
    ai_lite_research_results: AILiteResearchResults
    target_intelligence_data: TargetIntelligenceData
    research_focus_areas: ResearchFocusAreas

class DeepResearchRequest(BaseModel):
    """Complete deep research request"""
    request_metadata: DeepResearchMetadata
    research_context: DeepResearchContext

# Deep Research Output Models

class RelationshipIntelligence(BaseModel):
    """Deep relationship intelligence and network mapping"""
    board_network_analysis: List[Dict[str, Any]] = Field(default_factory=list)
    key_decision_makers: List[Dict[str, Any]] = Field(default_factory=list)
    introduction_pathways: List[Dict[str, Any]] = Field(default_factory=list)
    relationship_strength_assessment: Dict[str, float] = Field(default_factory=dict)
    network_influence_mapping: Dict[str, Any] = Field(default_factory=dict)
    engagement_timeline_recommendations: List[str] = Field(default_factory=list)

class CompetitiveIntelligence(BaseModel):
    """Comprehensive competitive landscape analysis"""
    primary_competitors: List[Dict[str, Any]] = Field(default_factory=list)
    competitive_positioning_matrix: Dict[str, Any] = Field(default_factory=dict)
    market_share_analysis: Dict[str, Any] = Field(default_factory=dict)
    competitive_advantages_assessment: List[str] = Field(default_factory=list)
    threat_analysis: List[Dict[str, Any]] = Field(default_factory=list)
    differentiation_opportunities: List[str] = Field(default_factory=list)

class FinancialIntelligence(BaseModel):
    """Financial deep-dive analysis"""
    funding_capacity_assessment: Dict[str, Any] = Field(default_factory=dict)
    historical_giving_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    financial_health_indicators: Dict[str, float] = Field(default_factory=dict)
    grant_size_optimization: Dict[str, Any] = Field(default_factory=dict)
    multi_year_funding_potential: Dict[str, Any] = Field(default_factory=dict)
    sustainability_prospects: List[str] = Field(default_factory=list)

class StrategicPartnershipIntelligence(BaseModel):
    """Strategic partnership assessment"""
    partnership_potential_score: float = 0.0
    mission_alignment_analysis: Dict[str, Any] = Field(default_factory=dict)
    synergy_opportunities: List[Dict[str, Any]] = Field(default_factory=list)
    collaboration_history: List[Dict[str, Any]] = Field(default_factory=list)
    strategic_value_proposition: List[str] = Field(default_factory=list)
    partnership_risks: List[Dict[str, Any]] = Field(default_factory=list)

class MarketIntelligence(BaseModel):
    """Market intelligence and positioning"""
    market_landscape_analysis: Dict[str, Any] = Field(default_factory=dict)
    funding_trend_analysis: List[Dict[str, Any]] = Field(default_factory=list)
    opportunity_market_size: Dict[str, Any] = Field(default_factory=dict)
    positioning_recommendations: List[str] = Field(default_factory=list)
    market_entry_strategies: List[str] = Field(default_factory=list)
    timing_optimization: Dict[str, Any] = Field(default_factory=dict)

class RiskIntelligence(BaseModel):
    """Sophisticated risk assessment"""
    primary_risk_factors: List[Dict[str, Any]] = Field(default_factory=list)
    risk_probability_modeling: Dict[str, float] = Field(default_factory=dict)
    mitigation_strategies: List[Dict[str, Any]] = Field(default_factory=list)
    contingency_planning: List[str] = Field(default_factory=list)
    success_probability_analysis: Dict[str, Any] = Field(default_factory=dict)
    scenario_planning: List[Dict[str, Any]] = Field(default_factory=list)

class DeepResearchIntelligenceReport(BaseModel):
    """Comprehensive deep research intelligence report"""
    executive_intelligence_summary: str = Field(description="Executive summary of all intelligence findings")
    relationship_intelligence: Optional[RelationshipIntelligence] = None
    competitive_intelligence: Optional[CompetitiveIntelligence] = None
    financial_intelligence: Optional[FinancialIntelligence] = None
    strategic_partnership_intelligence: Optional[StrategicPartnershipIntelligence] = None
    market_intelligence: Optional[MarketIntelligence] = None
    risk_intelligence: Optional[RiskIntelligence] = None
    
    # Research Quality Indicators
    intelligence_confidence_score: float = Field(ge=0.0, le=1.0)
    research_completeness_score: float = Field(ge=0.0, le=1.0)
    actionable_insights_count: int = 0
    
    # Next Steps for APPROACH tab
    approach_tab_handoff_data: Dict[str, Any] = Field(default_factory=dict)
    dossier_builder_preparation: List[str] = Field(default_factory=list)

class DeepResearchProcessingMetadata(BaseModel):
    """Processing metadata for deep research"""
    research_id: str
    processing_time: float
    intelligence_types_analyzed: List[str]
    research_cost: float
    model_used: str
    research_quality_score: float

class DeepResearchResult(BaseModel):
    """Complete deep research analysis result"""
    processing_metadata: DeepResearchProcessingMetadata
    intelligence_report: DeepResearchIntelligenceReport

class AIHeavyDeepResearcher(BaseProcessor):
    """AI Heavy deep research processor for comprehensive strategic intelligence"""
    
    def __init__(self):
        # Create metadata for base processor
        metadata = ProcessorMetadata(
            name="ai_heavy_deep_researcher",
            description="Phase 1.5: Specialized deep research tool for EXAMINE tab - strategic intelligence gathering",
            version="1.0.0",  # New specialized processor
            dependencies=["ai_lite_scorer"],  # Integrates with AI-Lite research outputs
            estimated_duration=180,  # Extended for deep research
            requires_network=True,
            requires_api_key=True,
            can_run_parallel=True,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Deep research settings (Updated for GPT-5-mini)
        self.model = "gpt-5-mini"  # Advanced GPT-5 model for sophisticated intelligence
        self.max_tokens = 4500  # Extended token limit for deep research
        self.temperature = 0.3  # Lower temperature for consistent intelligence gathering
        
        # Cost tracking (Updated GPT-5-mini pricing)
        self.estimated_cost_per_research = 0.06  # More cost-effective with GPT-5-mini
        self.research_depth_multipliers = {
            ResearchDepth.FOCUSED: 0.6,
            ResearchDepth.COMPREHENSIVE: 1.0,
            ResearchDepth.STRATEGIC: 1.4
        }
        
        # Deep research specialization
        self.intelligence_specialization_enabled = True
        self.examine_tab_optimization = True
        self.approach_tab_handoff_enabled = True
        
    async def execute(self, request_data: DeepResearchRequest) -> DeepResearchResult:
        """
        Execute deep research analysis for EXAMINE tab
        
        Args:
            request_data: Complete deep research request with context and focus areas
            
        Returns:
            DeepResearchResult with comprehensive intelligence report
        """
        start_time = datetime.now()
        research_id = request_data.request_metadata.research_id
        target_org = request_data.request_metadata.target_organization
        
        logger.info(f"Starting AI Heavy deep research for {target_org} (research: {research_id})")
        logger.info(f"Intelligence types requested: {[t.value for t in request_data.request_metadata.intelligence_types]}")
        
        try:
            # Prepare comprehensive deep research prompt
            research_prompt = self._create_deep_research_prompt(request_data)
            
            # Call OpenAI API with premium settings
            response = await self._call_openai_api(
                research_prompt, 
                request_data.request_metadata.model_preference
            )
            
            # Parse and validate comprehensive intelligence results
            intelligence_report = self._parse_deep_research_response(response, request_data)
            
            # Calculate processing metrics
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            research_cost = self._calculate_research_cost(request_data.request_metadata.research_depth)
            
            # Create comprehensive result structure
            processing_metadata = DeepResearchProcessingMetadata(
                research_id=research_id,
                processing_time=processing_time,
                intelligence_types_analyzed=[t.value for t in request_data.request_metadata.intelligence_types],
                research_cost=research_cost,
                model_used=request_data.request_metadata.model_preference,
                research_quality_score=intelligence_report.intelligence_confidence_score
            )
            
            result = DeepResearchResult(
                processing_metadata=processing_metadata,
                intelligence_report=intelligence_report
            )
            
            logger.info(f"Deep research completed: {target_org}, "
                       f"${research_cost:.4f} cost, {processing_time:.2f}s, "
                       f"confidence: {intelligence_report.intelligence_confidence_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Deep research analysis failed: {str(e)}")
            raise
    
    def _create_deep_research_prompt(self, request_data: DeepResearchRequest) -> str:
        """Create comprehensive deep research prompt for intelligence gathering"""
        
        metadata = request_data.request_metadata
        context = request_data.research_context
        
        # Build comprehensive context section
        context_section = f"""STRATEGIC INTELLIGENCE ANALYST - DEEP RESEARCH SYSTEM

TARGET ORGANIZATION: {metadata.target_organization}
RESEARCH OBJECTIVE: Comprehensive strategic intelligence for EXAMINE tab decision-making

REQUESTING ORGANIZATION CONTEXT:
Name: {context.organization_intelligence.organization_name}
Mission: {context.organization_intelligence.mission_statement}
Strategic Priorities: {', '.join(context.organization_intelligence.strategic_priorities)}
Leadership: {', '.join(context.organization_intelligence.leadership_team)}
Recent Grants: {', '.join(context.organization_intelligence.recent_grants)}
Funding Capacity: {context.organization_intelligence.funding_capacity}
Geographic Scope: {context.organization_intelligence.geographic_scope}

AI-LITE PRELIMINARY RESEARCH INTEGRATION:
Compatibility Score: {context.ai_lite_research_results.compatibility_score * 100:.0f}/100
Strategic Value: {context.ai_lite_research_results.strategic_value}
Key Risk Factors: {', '.join(context.ai_lite_research_results.risk_assessment)}
Funding Likelihood: {context.ai_lite_research_results.funding_likelihood * 100:.0f}/100
Preliminary Analysis: {context.ai_lite_research_results.strategic_rationale}"""

        if context.ai_lite_research_results.research_evidence:
            context_section += f"\nPreliminary Research Evidence Available: {len(context.ai_lite_research_results.research_evidence)} components"

        context_section += f"""

TARGET INTELLIGENCE BASELINE:
Organization: {context.target_intelligence_data.organization_name}
Overview: {context.target_intelligence_data.basic_info}
Funding Capacity: {context.target_intelligence_data.funding_capacity}
Geographic Focus: {context.target_intelligence_data.geographic_focus}
Known Board Members: {', '.join(context.target_intelligence_data.known_board_members) if context.target_intelligence_data.known_board_members else 'Intelligence gathering required'}
Recent Grants: {', '.join(context.target_intelligence_data.recent_grants_given) if context.target_intelligence_data.recent_grants_given else 'Research required'}"""

        if context.target_intelligence_data.website_url:
            context_section += f"\nWebsite: {context.target_intelligence_data.website_url}"
            
        if context.target_intelligence_data.annual_revenue:
            context_section += f"\nAnnual Revenue: {context.target_intelligence_data.annual_revenue}"

        # Build research focus section
        focus_section = f"""

DEEP RESEARCH INTELLIGENCE REQUIREMENTS:
Priority Areas: {', '.join(context.research_focus_areas.priority_areas)}
Intelligence Gaps: {', '.join(context.research_focus_areas.intelligence_gaps)}
Specific Questions: {'; '.join(context.research_focus_areas.specific_questions)}
Research Objectives: {'; '.join(context.research_focus_areas.research_objectives)}

INTELLIGENCE TYPES REQUESTED: {', '.join([t.value.upper() for t in metadata.intelligence_types])}"""

        # Build intelligence-specific requirements
        intelligence_requirements = []
        
        if IntelligenceType.RELATIONSHIP in metadata.intelligence_types:
            intelligence_requirements.append("""
1. RELATIONSHIP INTELLIGENCE:
   - Complete board network analysis with connection mapping
   - Key decision maker identification with influence assessment
   - Introduction pathway analysis with relationship strength scoring
   - Engagement timeline recommendations with strategic milestones""")
        
        if IntelligenceType.COMPETITIVE in metadata.intelligence_types:
            intelligence_requirements.append("""
2. COMPETITIVE INTELLIGENCE:
   - Primary competitor identification with positioning matrix
   - Market share analysis with competitive advantage assessment
   - Threat analysis with differentiation opportunity identification
   - Competitive landscape evolution and strategic positioning""")
        
        if IntelligenceType.FINANCIAL in metadata.intelligence_types:
            intelligence_requirements.append("""
3. FINANCIAL INTELLIGENCE:
   - Funding capacity deep-dive with historical giving pattern analysis
   - Financial health indicators with grant size optimization modeling
   - Multi-year funding potential assessment with sustainability prospects
   - Investment strategy alignment with funding capacity optimization""")
        
        if IntelligenceType.STRATEGIC in metadata.intelligence_types:
            intelligence_requirements.append("""
4. STRATEGIC PARTNERSHIP INTELLIGENCE:
   - Partnership potential scoring with mission alignment analysis
   - Synergy opportunity identification with collaboration history review
   - Strategic value proposition development with partnership risk assessment
   - Long-term relationship building strategy with mutual benefit analysis""")
        
        if IntelligenceType.MARKET in metadata.intelligence_types:
            intelligence_requirements.append("""
5. MARKET INTELLIGENCE:
   - Market landscape analysis with funding trend identification
   - Opportunity market size assessment with positioning recommendations
   - Market entry strategy development with timing optimization
   - Competitive market dynamics with strategic positioning guidance""")
        
        if IntelligenceType.RISK in metadata.intelligence_types:
            intelligence_requirements.append("""
6. RISK INTELLIGENCE:
   - Primary risk factor identification with probability modeling
   - Mitigation strategy development with contingency planning
   - Success probability analysis with scenario planning
   - Risk-reward optimization with strategic risk management""")

        # Create comprehensive deep research prompt
        prompt = f"""{context_section}{focus_section}

DEEP RESEARCH INTELLIGENCE MISSION:

Conduct comprehensive strategic intelligence gathering that provides EXAMINE tab teams with sophisticated analysis for strategic decision-making. This research will feed into the APPROACH tab for implementation planning.

Provide detailed JSON response with comprehensive intelligence analysis:

{{
  "executive_intelligence_summary": "Comprehensive 300-word executive summary highlighting key intelligence findings, strategic implications, and critical insights for decision-making",
  "intelligence_confidence_score": 0.92,
  "research_completeness_score": 0.88,
  "actionable_insights_count": 15,
  "approach_tab_handoff_data": {{
    "key_implementation_factors": ["Factor 1", "Factor 2", "Factor 3"],
    "recommended_approach_focus": ["Focus area 1", "Focus area 2"],
    "critical_success_requirements": ["Requirement 1", "Requirement 2"],
    "resource_planning_insights": ["Insight 1", "Insight 2"]
  }},
  "dossier_builder_preparation": [
    "Specific preparation item 1 for APPROACH tab",
    "Specific preparation item 2 for APPROACH tab"
  ]"""

        # Add intelligence-specific sections based on requested types
        for intelligence_req in intelligence_requirements:
            if "RELATIONSHIP" in intelligence_req:
                prompt += """,
  "relationship_intelligence": {
    "board_network_analysis": [
      {"name": "Board Member Name", "role": "Position", "influence_score": 0.85, "connection_type": "direct", "engagement_strategy": "Specific approach"}
    ],
    "key_decision_makers": [
      {"name": "Decision Maker", "role": "Title", "decision_authority": "high", "contact_pathway": "Specific pathway", "engagement_timeline": "3-6 months"}
    ],
    "introduction_pathways": [
      {"target": "Person Name", "pathway": "Introduction method", "probability": 0.75, "timeline": "2-4 weeks", "preparation_required": "Specific prep"}
    ],
    "relationship_strength_assessment": {"existing_connections": 0.6, "potential_connections": 0.8},
    "network_influence_mapping": {"primary_influencers": ["Name 1", "Name 2"], "secondary_network": ["Name 3"]},
    "engagement_timeline_recommendations": ["Month 1-2: Specific activities", "Month 3-4: Specific activities"]
  }"""
            
            if "COMPETITIVE" in intelligence_req:
                prompt += """,
  "competitive_intelligence": {
    "primary_competitors": [
      {"name": "Competitor Org", "market_position": "strong", "competitive_advantages": ["Advantage 1"], "threat_level": "medium"}
    ],
    "competitive_positioning_matrix": {"our_position": "strong contender", "key_differentiators": ["Differentiator 1", "Differentiator 2"]},
    "market_share_analysis": {"total_market_size": "$10M annually", "our_addressable_market": "$2M", "competitive_density": "moderate"},
    "competitive_advantages_assessment": ["Our unique advantage 1", "Our unique advantage 2"],
    "threat_analysis": [
      {"threat": "Competitive threat", "probability": "medium", "impact": "high", "mitigation": "Specific mitigation"}
    ],
    "differentiation_opportunities": ["Differentiation strategy 1", "Differentiation strategy 2"]
  }"""
        
        # Add other intelligence sections as needed...
        
        prompt += f"""
}}

DEEP RESEARCH INTELLIGENCE REQUIREMENTS:
{''.join(intelligence_requirements)}

EXAMINE TAB DECISION SUPPORT FOCUS:
1. STRATEGIC INTELLIGENCE: Provide sophisticated intelligence that enables strategic decision-making
2. RELATIONSHIP MAPPING: Complete relationship intelligence with actionable engagement strategies  
3. COMPETITIVE POSITIONING: Comprehensive competitive analysis with differentiation strategies
4. RISK-REWARD ASSESSMENT: Sophisticated risk modeling with mitigation strategies
5. MARKET INTELLIGENCE: Deep market analysis with positioning and timing recommendations
6. APPROACH TAB PREPARATION: Prepare key intelligence for implementation planning phase

CRITICAL SUCCESS FACTORS:
- Provide EXAMINE tab teams with sophisticated strategic intelligence
- Enable evidence-based strategic decision-making with confidence levels
- Prepare comprehensive intelligence foundation for APPROACH tab implementation
- Deliver actionable insights with specific next steps and timelines

RESPONSE (JSON only):"""
        
        return prompt
    
    async def _call_openai_api(self, prompt: str, model: str = "gpt-4") -> str:
        """Call OpenAI API with deep research settings"""
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
            
            # Simulated deep research response for development
            await asyncio.sleep(3)  # Simulate deeper analysis delay
            
            return json.dumps({
                "executive_intelligence_summary": "Comprehensive strategic intelligence analysis reveals strong partnership potential with moderate competitive landscape. Key relationship pathways identified through board connections. Financial capacity assessment indicates substantial multi-year funding potential. Risk analysis shows manageable risk profile with clear mitigation strategies. Market positioning analysis suggests optimal timing for engagement with differentiation opportunities in healthcare innovation space.",
                "intelligence_confidence_score": 0.87,
                "research_completeness_score": 0.82,
                "actionable_insights_count": 12,
                "relationship_intelligence": {
                    "board_network_analysis": [
                        {"name": "Dr. Sarah Johnson", "role": "Board Chair", "influence_score": 0.92, "connection_type": "second_degree", "engagement_strategy": "Healthcare innovation focus approach"}
                    ],
                    "key_decision_makers": [
                        {"name": "Michael Chen", "role": "Program Director", "decision_authority": "high", "contact_pathway": "Professional association", "engagement_timeline": "2-3 months"}
                    ],
                    "introduction_pathways": [
                        {"target": "Dr. Sarah Johnson", "pathway": "Alumni network connection", "probability": 0.75, "timeline": "3-4 weeks", "preparation_required": "Healthcare innovation portfolio preparation"}
                    ],
                    "relationship_strength_assessment": {"existing_connections": 0.4, "potential_connections": 0.8},
                    "network_influence_mapping": {"primary_influencers": ["Dr. Sarah Johnson", "Michael Chen"], "secondary_network": ["Dr. Lisa Park"]},
                    "engagement_timeline_recommendations": ["Month 1-2: Initial relationship building through healthcare forums", "Month 3-4: Direct engagement with program team"]
                },
                "approach_tab_handoff_data": {
                    "key_implementation_factors": ["Board relationship leverage required", "Healthcare innovation focus essential", "Multi-year commitment preferred"],
                    "recommended_approach_focus": ["Innovation partnership angle", "Long-term strategic relationship"],
                    "critical_success_requirements": ["Healthcare expertise demonstration", "Multi-year project planning"],
                    "resource_planning_insights": ["Board engagement strategy needed", "Healthcare subject matter experts required"]
                },
                "dossier_builder_preparation": [
                    "Prepare healthcare innovation portfolio for board presentation",
                    "Develop multi-year partnership proposal framework",
                    "Create relationship engagement timeline with milestone tracking"
                ]
            })
            
        except Exception as e:
            logger.error(f"Deep research API call failed: {str(e)}")
            raise
    
    def _parse_deep_research_response(self, response: str, request_data: DeepResearchRequest) -> DeepResearchIntelligenceReport:
        """Parse and validate deep research API response"""
        try:
            # Parse JSON response
            response_data = json.loads(response.strip())
            
            # Create intelligence report with parsed components
            intelligence_report = DeepResearchIntelligenceReport(
                executive_intelligence_summary=response_data.get("executive_intelligence_summary", ""),
                intelligence_confidence_score=response_data.get("intelligence_confidence_score", 0.5),
                research_completeness_score=response_data.get("research_completeness_score", 0.5),
                actionable_insights_count=response_data.get("actionable_insights_count", 0),
                approach_tab_handoff_data=response_data.get("approach_tab_handoff_data", {}),
                dossier_builder_preparation=response_data.get("dossier_builder_preparation", [])
            )
            
            # Parse intelligence components based on requested types
            if IntelligenceType.RELATIONSHIP in request_data.request_metadata.intelligence_types:
                if "relationship_intelligence" in response_data:
                    intelligence_report.relationship_intelligence = RelationshipIntelligence(
                        **response_data["relationship_intelligence"]
                    )
            
            # Add other intelligence type parsing as needed...
            
            return intelligence_report
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse deep research response as JSON: {str(e)}")
            # Return fallback intelligence report
            return DeepResearchIntelligenceReport(
                executive_intelligence_summary="Deep research analysis temporarily unavailable. Manual intelligence gathering recommended.",
                intelligence_confidence_score=0.1,
                research_completeness_score=0.1,
                actionable_insights_count=0,
                approach_tab_handoff_data={"status": "manual_analysis_required"},
                dossier_builder_preparation=["Manual research required for APPROACH tab preparation"]
            )
        except Exception as e:
            logger.error(f"Failed to parse deep research response: {str(e)}")
            # Return fallback intelligence report
            return DeepResearchIntelligenceReport(
                executive_intelligence_summary="Deep research processing error. Manual intelligence review recommended.",
                intelligence_confidence_score=0.1,
                research_completeness_score=0.1,
                actionable_insights_count=0,
                approach_tab_handoff_data={"status": "processing_error"},
                dossier_builder_preparation=["Manual analysis required due to processing error"]
            )
    
    def _calculate_research_cost(self, research_depth: ResearchDepth) -> float:
        """Calculate research cost based on depth"""
        multiplier = self.research_depth_multipliers.get(research_depth, 1.0)
        return self.estimated_cost_per_research * multiplier
    
    def get_deep_research_capabilities(self) -> Dict[str, Any]:
        """Get deep research capabilities for EXAMINE tab"""
        return {
            "processor_name": "ai_heavy_deep_researcher",
            "tab_specialization": "EXAMINE",
            "intelligence_types_supported": [t.value for t in IntelligenceType],
            "research_depths_available": [d.value for d in ResearchDepth],
            "cost_per_research": self.estimated_cost_per_research,
            "specialized_capabilities": [
                "Deep relationship intelligence and network mapping",
                "Comprehensive competitive landscape analysis",
                "Financial deep-dive with multi-year funding potential",
                "Strategic partnership assessment with synergy identification",
                "Market intelligence and positioning analysis",
                "Risk assessment with sophisticated mitigation strategies"
            ],
            "approach_tab_integration": [
                "Comprehensive intelligence handoff to APPROACH tab",
                "Implementation-ready intelligence preparation",
                "Dossier builder foundation data provision"
            ],
            "phase_1_5_features": "Specialized EXAMINE tab intelligence gathering with APPROACH tab preparation"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get processor status and configuration"""
        return {
            "processor_name": self.processor_name,
            "version": self.version,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "estimated_cost_per_research": self.estimated_cost_per_research,
            "intelligence_specialization_enabled": self.intelligence_specialization_enabled,
            "examine_tab_optimization": self.examine_tab_optimization,
            "approach_tab_handoff_enabled": self.approach_tab_handoff_enabled,
            "status": "ready"
        }

# Export the processor class and specialized data models
__all__ = [
    "AIHeavyDeepResearcher",
    "DeepResearchRequest",
    "DeepResearchResult", 
    "DeepResearchMetadata",
    "DeepResearchContext",
    "OrganizationIntelligence",
    "AILiteResearchResults",
    "TargetIntelligenceData",
    "ResearchFocusAreas",
    "DeepResearchIntelligenceReport",
    "RelationshipIntelligence",
    "CompetitiveIntelligence",
    "FinancialIntelligence", 
    "StrategicPartnershipIntelligence",
    "MarketIntelligence",
    "RiskIntelligence",
    "ResearchDepth",
    "IntelligenceType"
]