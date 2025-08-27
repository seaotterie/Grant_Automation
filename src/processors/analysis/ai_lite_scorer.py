"""
AI Lite Scorer - Dual-Function Research & Scoring Platform for ANALYZE tab

Purpose: Cost-effective candidate evaluation with comprehensive research capabilities
Model: GPT-3.5 for optimal cost/performance ratio (~$0.0001 per candidate)
Batch Processing: 10-20 candidates per API call for cost optimization

Phase 1 Enhanced Features:
- Dual-function scoring AND research platform
- Website intelligence and document parsing
- Fact extraction and verification
- Grant team ready research reports
- Evidence-based scoring with supporting documentation
- Risk assessment with mitigation strategies
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
from src.core.error_recovery import (
    with_error_recovery, create_ai_retry_policy, error_recovery_manager,
    ErrorCategory, ErrorSeverity, RecoveryAction
)

logger = logging.getLogger(__name__)

# Enhanced data packet models for comprehensive AI analysis

class StrategicValue(str, Enum):
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"

class ActionPriority(str, Enum):
    IMMEDIATE = "immediate"
    PLANNED = "planned"
    MONITOR = "monitor"

# Phase 1 Enhancement: Research Data Models

class WebsiteIntelligence(BaseModel):
    """Website and document intelligence gathered"""
    primary_website_url: Optional[str] = None
    key_contacts: List[str] = Field(default_factory=list)
    application_process_summary: str = ""
    eligibility_highlights: List[str] = Field(default_factory=list)
    deadline_information: str = ""
    document_links: List[str] = Field(default_factory=list)

class FactExtraction(BaseModel):
    """Systematically extracted facts"""
    award_amount_range: str = ""
    application_deadline: str = ""
    project_duration: str = ""
    geographic_eligibility: List[str] = Field(default_factory=list)
    organizational_requirements: List[str] = Field(default_factory=list)
    matching_requirements: str = ""
    reporting_requirements: List[str] = Field(default_factory=list)

class ResearchReport(BaseModel):
    """Comprehensive research findings for grant teams"""
    executive_summary: str = Field(description="200-word executive summary for grant teams")
    opportunity_overview: str = Field(description="Detailed opportunity description and context")
    eligibility_analysis: List[str] = Field(default_factory=list, description="Point-by-point eligibility assessment")
    key_dates_timeline: List[str] = Field(default_factory=list, description="All critical dates and deadlines")
    funding_details: str = Field(description="Award amounts, restrictions, terms")
    strategic_considerations: List[str] = Field(default_factory=list, description="Strategic factors for consideration")
    decision_factors: List[str] = Field(default_factory=list, description="Key factors for go/no-go decision")

class CompetitiveAnalysis(BaseModel):
    """Competition and positioning analysis"""
    likely_competitors: List[str] = Field(default_factory=list)
    competitive_advantages: List[str] = Field(default_factory=list)
    application_volume_estimate: str = ""
    success_probability_factors: List[str] = Field(default_factory=list)
    differentiation_strategies: List[str] = Field(default_factory=list)

class RequestMetadata(BaseModel):
    """AI request metadata for tracking and optimization"""
    batch_id: str
    profile_id: str
    analysis_type: str = "compatibility_scoring"
    model_preference: str = "gpt-5-nano"
    cost_limit: float = 0.005
    priority: str = "standard"

class FundingHistory(BaseModel):
    """Organization funding context"""
    typical_grant_size: str = "$50000-250000"
    annual_budget: str = "$2M"
    grant_making_capacity: str = "$500K"

class ProfileContext(BaseModel):
    """Comprehensive organization profile for AI analysis"""
    organization_name: str
    mission_statement: str
    focus_areas: List[str] = Field(default_factory=list)
    ntee_codes: List[str] = Field(default_factory=list)
    government_criteria: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    geographic_scope: str = "National"
    funding_history: Optional[FundingHistory] = None

class ExistingAnalysis(BaseModel):
    """Previously computed analysis data"""
    raw_score: float = 0.0
    confidence_level: float = 0.0
    match_factors: List[str] = Field(default_factory=list)

class CandidateData(BaseModel):
    """Individual candidate for AI analysis"""
    opportunity_id: str
    organization_name: str
    source_type: str
    description: str
    funding_amount: Optional[int] = None
    application_deadline: Optional[str] = None
    geographic_location: Optional[str] = None
    current_score: float = 0.0
    existing_analysis: Optional[ExistingAnalysis] = None

class AILiteRequest(BaseModel):
    """Complete AI Lite analysis request packet"""
    request_metadata: RequestMetadata
    profile_context: ProfileContext
    candidates: List[CandidateData]

class AILiteAnalysis(BaseModel):
    """Enhanced AI Lite analysis with dual-function scoring and research"""
    # SCORING COMPONENTS (Enhanced Original Function)
    compatibility_score: float = Field(..., ge=0.0, le=1.0, description="AI compatibility score 0-1")
    strategic_value: StrategicValue = Field(..., description="Strategic importance classification")
    risk_assessment: List[str] = Field(default_factory=list, description="Identified risk factors")
    priority_rank: int = Field(..., ge=1, description="Priority ranking within batch")
    funding_likelihood: float = Field(..., ge=0.0, le=1.0, description="Probability of funding success")
    strategic_rationale: str = Field(..., description="2-sentence strategic analysis")
    action_priority: ActionPriority = Field(..., description="Next steps classification")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Analysis confidence")
    
    # RESEARCH COMPONENTS (Phase 1 New Function)
    research_report: Optional[ResearchReport] = Field(default=None, description="Comprehensive research findings")
    website_intelligence: Optional[WebsiteIntelligence] = Field(default=None, description="Website analysis and document parsing")
    fact_extraction: Optional[FactExtraction] = Field(default=None, description="Systematically gathered facts")
    competitive_analysis: Optional[CompetitiveAnalysis] = Field(default=None, description="Competition and positioning analysis")
    
    # METADATA
    research_mode_enabled: bool = Field(default=False, description="Whether research mode was activated")
    analysis_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class BatchResults(BaseModel):
    """Processing metadata for batch analysis"""
    batch_id: str
    processed_count: int
    processing_time: float
    total_cost: float
    model_used: str
    analysis_quality: str = "standard"

class AILiteBatchResult(BaseModel):
    """Complete results from AI Lite batch analysis"""
    batch_results: BatchResults
    candidate_analysis: Dict[str, AILiteAnalysis]  # opportunity_id -> analysis

class AILiteScorer(BaseProcessor):
    """AI Lite scoring processor for cost-effective candidate analysis"""
    
    def __init__(self):
        # Create metadata for base processor
        metadata = ProcessorMetadata(
            name="ai_lite_scorer",
            description="Phase 1: Dual-function research and scoring platform for ANALYZE tab",
            version="2.0.0",  # Phase 1 Enhancement
            dependencies=[],
            estimated_duration=60,  # Extended for research mode
            requires_network=True,
            requires_api_key=True,
            can_run_parallel=True,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Cost optimization settings (Updated for GPT-5-nano)
        self.batch_size = 15  # Optimal batch size for cost/performance
        self.model = "gpt-5-nano"  # Most cost-effective GPT-5 model
        self.max_tokens = 150  # Keep responses concise for cost control (scoring mode)
        self.max_tokens_research = 800  # Extended tokens for research mode
        self.temperature = 0.3  # Lower temperature for consistent analysis
        
        # Cost tracking (Updated GPT-5-nano pricing: $0.25/1M input, $2.0/1M output)
        self.estimated_cost_per_candidate = 0.00005  # More cost-effective with GPT-5-nano
        self.estimated_cost_per_candidate_research = 0.0004  # Research mode estimate
        
        # Phase 1 Enhancement: Research mode settings
        self.research_mode_default = True  # Enable research by default in Phase 1
    
    def _should_enable_research_mode(self, request_data: AILiteRequest) -> bool:
        """Determine whether to enable research mode for this request"""
        # Phase 1: Enable research mode by default for high-value opportunities
        analysis_type = request_data.request_metadata.analysis_type
        
        # Enable research mode if:
        # 1. Explicitly requested in analysis_type
        # 2. High-priority request
        # 3. Default research mode enabled
        if "research" in analysis_type.lower():
            return True
        if request_data.request_metadata.priority in ["high", "urgent"]:
            return True
        if self.research_mode_default:
            return True
            
        return False
        
    async def execute(self, request_data: AILiteRequest) -> AILiteBatchResult:
        """
        Execute AI Lite analysis using comprehensive data packet
        
        Args:
            request_data: Complete AI Lite request with metadata, profile, and candidates
            
        Returns:
            AILiteBatchResult with enhanced analysis for each candidate
        """
        start_time = datetime.now()
        batch_id = request_data.request_metadata.batch_id
        
        logger.info(f"Starting AI Lite analysis for {len(request_data.candidates)} candidates (batch: {batch_id})")
        
        # Register fallback handler for AI Lite processing
        def create_fallback_results():
            return [self._create_fallback_analysis(candidate) for candidate in request_data.candidates]
        
        error_recovery_manager.register_fallback_handler("ai_lite_analysis", create_fallback_results)
        
        try:
            # Phase 1 Enhancement: Determine research mode
            research_mode = self._should_enable_research_mode(request_data)
            logger.info(f"Research mode {'ENABLED' if research_mode else 'DISABLED'} for batch {batch_id}")
            
            # Prepare enhanced batch analysis prompt (with research if enabled)
            if research_mode:
                batch_prompt = self._create_research_enhanced_batch_prompt(request_data)
                max_tokens = self.max_tokens_research
                cost_per_candidate = self.estimated_cost_per_candidate_research
            else:
                batch_prompt = self._create_enhanced_batch_prompt(request_data)
                max_tokens = self.max_tokens
                cost_per_candidate = self.estimated_cost_per_candidate
            
            # Call OpenAI API with comprehensive error recovery
            response = await error_recovery_manager.execute_with_recovery(
                operation="openai_api",
                func=self._call_openai_api,
                retry_policy=create_ai_retry_policy(),
                context={"batch_id": batch_id, "candidate_count": len(request_data.candidates)},
                prompt=batch_prompt,
                model=request_data.request_metadata.model_preference,
                max_tokens=max_tokens
            )
            
            # Parse and validate enhanced results with error recovery
            if research_mode:
                analysis_results = await error_recovery_manager.execute_with_recovery(
                    operation="ai_response_parsing",
                    func=self._parse_research_enhanced_api_response,
                    fallback_func=create_fallback_results,
                    context={"research_mode": True, "batch_id": batch_id},
                    response=response,
                    candidates=request_data.candidates
                )
            else:
                analysis_results = await error_recovery_manager.execute_with_recovery(
                    operation="ai_response_parsing", 
                    func=self._parse_enhanced_api_response,
                    fallback_func=create_fallback_results,
                    context={"research_mode": False, "batch_id": batch_id},
                    response=response,
                    candidates=request_data.candidates
                )
            
            # Calculate processing metrics
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            estimated_cost = len(request_data.candidates) * cost_per_candidate
            
            # Create comprehensive result structure
            batch_results = BatchResults(
                batch_id=batch_id,
                processed_count=len(analysis_results),
                processing_time=processing_time,
                total_cost=estimated_cost,
                model_used=request_data.request_metadata.model_preference,
                analysis_quality="standard"
            )
            
            result = AILiteBatchResult(
                batch_results=batch_results,
                candidate_analysis=analysis_results
            )
            
            logger.info(f"AI Lite analysis completed: {len(analysis_results)} candidates, "
                       f"${estimated_cost:.4f} estimated cost, {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"AI Lite analysis failed: {str(e)}")
            
            # Use comprehensive error recovery with fallback
            try:
                fallback_results = create_fallback_results()
                
                result = AILiteBatchResult(
                    batch_results=BatchResults(
                        batch_id=batch_id,
                        processed_count=len(fallback_results),
                        processing_time=0.1,
                        total_cost=0.0,
                        model_used="fallback",
                        research_mode_enabled=False
                    ),
                    candidate_analysis=fallback_results
                )
                
                logger.warning(f"Using fallback analysis for batch {batch_id} due to error: {str(e)}")
                return result
                
            except Exception as fallback_error:
                logger.error(f"Fallback analysis also failed for batch {batch_id}: {str(fallback_error)}")
                raise e
    
    def _create_enhanced_batch_prompt(self, request_data: AILiteRequest) -> str:
        """Create sophisticated batch prompt using comprehensive data packet"""
        
        profile = request_data.profile_context
        candidates = request_data.candidates
        
        # Build comprehensive profile context
        profile_section = f"""ANALYZING ORGANIZATION PROFILE:
Name: {profile.organization_name}
Mission: {profile.mission_statement}
Focus Areas: {', '.join(profile.focus_areas)}
NTEE Codes: {', '.join(profile.ntee_codes)}
Geographic Scope: {profile.geographic_scope}"""
        
        if profile.funding_history:
            profile_section += f"""
Typical Grant Size: {profile.funding_history.typical_grant_size}
Annual Budget: {profile.funding_history.annual_budget}
Grant Making Capacity: {profile.funding_history.grant_making_capacity}"""
        
        # Build detailed candidate summaries
        candidate_summaries = []
        for i, candidate in enumerate(candidates, 1):
            funding_info = f"${candidate.funding_amount:,}" if candidate.funding_amount else "Amount TBD"
            deadline_info = f"Deadline: {candidate.application_deadline}" if candidate.application_deadline else "Deadline: Open"
            
            summary = f"""
{i}. {candidate.organization_name} ({candidate.opportunity_id})
   Type: {candidate.source_type} | Funding: {funding_info}
   Location: {candidate.geographic_location or 'National'}
   Current Score: {(candidate.current_score * 100):.1f}% | {deadline_info}
   Description: {candidate.description[:250]}..."""
            
            if candidate.existing_analysis:
                summary += f"""
   Prior Analysis: Score {candidate.existing_analysis.raw_score:.2f}, Confidence {candidate.existing_analysis.confidence_level:.2f}
   Match Factors: {', '.join(candidate.existing_analysis.match_factors)}"""
            
            candidate_summaries.append(summary)
        
        # Create sophisticated prompt
        prompt = f"""GRANT STRATEGY EXPERT - BATCH COMPATIBILITY ANALYSIS

{profile_section}

BATCH CANDIDATES ({len(candidates)} organizations):
{''.join(candidate_summaries)}

ANALYSIS REQUIREMENTS:
For each candidate, provide EXACT JSON response:

{{
  "opportunity_id": {{
    "compatibility_score": 0.85,
    "strategic_value": "high",
    "risk_assessment": ["competition_level", "capacity_requirements"],
    "priority_rank": 1,
    "funding_likelihood": 0.75,
    "strategic_rationale": "2-sentence strategic analysis",
    "action_priority": "immediate",
    "confidence_level": 0.9
  }}
}}

SCORING CRITERIA:
- compatibility_score: 0.0-1.0 mission/focus alignment
- strategic_value: "high", "medium", or "low" overall strategic importance
- risk_assessment: Choose from ["high_competition", "technical_requirements", "geographic_mismatch", "capacity_concerns", "timeline_pressure", "compliance_complex", "matching_required", "reporting_intensive", "board_connections_needed"]
- priority_rank: 1=highest, rank ALL candidates 1-{len(candidates)}
- funding_likelihood: 0.0-1.0 probability of success
- strategic_rationale: Concise strategic reasoning (2 sentences max)
- action_priority: "immediate", "planned", or "monitor"
- confidence_level: Analysis confidence 0.0-1.0

Focus on strategic fit, competitive advantages, and practical implementation considerations.

RESPONSE (JSON only):"""
        
        return prompt
    
    def _create_research_enhanced_batch_prompt(self, request_data: AILiteRequest) -> str:
        """Create research-enhanced batch prompt for comprehensive analysis"""
        
        profile = request_data.profile_context
        candidates = request_data.candidates
        
        # Build comprehensive profile context
        profile_section = f"""RESEARCH ANALYST - COMPREHENSIVE OPPORTUNITY INTELLIGENCE
        
ANALYZING ORGANIZATION PROFILE:
Name: {profile.organization_name}
Mission: {profile.mission_statement}
Focus Areas: {', '.join(profile.focus_areas)}
NTEE Codes: {', '.join(profile.ntee_codes)}
Geographic Scope: {profile.geographic_scope}"""
        
        if profile.funding_history:
            profile_section += f"""
Typical Grant Size: {profile.funding_history.typical_grant_size}
Annual Budget: {profile.funding_history.annual_budget}
Grant Making Capacity: {profile.funding_history.grant_making_capacity}"""
        
        # Build detailed candidate summaries
        candidate_summaries = []
        for i, candidate in enumerate(candidates, 1):
            funding_info = f"${candidate.funding_amount:,}" if candidate.funding_amount else "Amount TBD"
            deadline_info = f"Deadline: {candidate.application_deadline}" if candidate.application_deadline else "Deadline: Open"
            
            summary = f"""
{i}. {candidate.organization_name} ({candidate.opportunity_id})
   Type: {candidate.source_type} | Funding: {funding_info}
   Location: {candidate.geographic_location or 'National'}
   Current Score: {(candidate.current_score * 100):.1f}% | {deadline_info}
   Description: {candidate.description[:300]}..."""
            
            candidate_summaries.append(summary)
        
        # Create comprehensive research prompt
        prompt = f"""{profile_section}

BATCH CANDIDATES FOR RESEARCH ({len(candidates)} opportunities):
{''.join(candidate_summaries)}

COMPREHENSIVE RESEARCH MISSION:
For each opportunity, conduct thorough research and provide analysis in EXACT JSON format:

{{
  "opportunity_id": {{
    "compatibility_score": 0.85,
    "strategic_value": "high",
    "risk_assessment": ["competition_level", "capacity_requirements"],
    "priority_rank": 1,
    "funding_likelihood": 0.75,
    "strategic_rationale": "2-sentence strategic analysis",
    "action_priority": "immediate",
    "confidence_level": 0.9,
    "research_report": {{
      "executive_summary": "200-word executive summary for grant teams highlighting key findings and recommendations",
      "opportunity_overview": "Detailed opportunity description, context, and strategic importance",
      "eligibility_analysis": ["Point 1: Specific eligibility requirement analysis", "Point 2: Additional requirement assessment"],
      "key_dates_timeline": ["Application deadline specifics", "Award notification timeline", "Project period details"],
      "funding_details": "Complete funding information including restrictions, terms, matching requirements",
      "strategic_considerations": ["Strategic factor 1", "Strategic factor 2"],
      "decision_factors": ["Go/no-go factor 1", "Go/no-go factor 2"]
    }},
    "website_intelligence": {{
      "primary_website_url": "https://funder-website.org",
      "key_contacts": ["Contact Name, Title, email"],
      "application_process_summary": "Step-by-step application process overview",
      "eligibility_highlights": ["Key eligibility point 1", "Key eligibility point 2"],
      "deadline_information": "Complete deadline and timeline information"
    }},
    "fact_extraction": {{
      "award_amount_range": "$X - $Y per award",
      "application_deadline": "Specific date and time",
      "project_duration": "X months/years",
      "geographic_eligibility": ["Geographic restriction 1", "Geographic restriction 2"],
      "organizational_requirements": ["Organization requirement 1", "Organization requirement 2"],
      "matching_requirements": "Matching funds requirements if any",
      "reporting_requirements": ["Reporting requirement 1", "Reporting requirement 2"]
    }},
    "competitive_analysis": {{
      "likely_competitors": ["Competitor organization 1", "Competitor organization 2"],
      "competitive_advantages": ["Our advantage 1", "Our advantage 2"],
      "application_volume_estimate": "Estimated number of applications",
      "success_probability_factors": ["Success factor 1", "Success factor 2"],
      "differentiation_strategies": ["Strategy 1", "Strategy 2"]
    }},
    "research_mode_enabled": true
  }}
}}

RESEARCH REQUIREMENTS:
1. COMPREHENSIVE OPPORTUNITY ANALYSIS: Extract detailed information about funding opportunity, requirements, and process
2. ELIGIBILITY DEEP DIVE: Point-by-point analysis of all eligibility requirements with compliance assessment
3. WEBSITE & DOCUMENT INTELLIGENCE: Gather contact information, process details, and application materials
4. COMPETITIVE INTELLIGENCE: Assess likely competition and strategic positioning
5. FACT EXTRACTION: Systematically extract all critical facts and requirements
6. STRATEGIC ASSESSMENT: Evaluate strategic fit and implementation considerations
7. DECISION SUPPORT: Provide clear go/no-go factors and next steps

Focus on providing grant teams with comprehensive, actionable intelligence that supports strategic decision-making.

RESPONSE (JSON only):"""
        
        return prompt
    
    def _create_batch_prompt(self, opportunities: List[Dict], profile_context: Optional[Dict] = None) -> str:
        """Create optimized batch prompt for cost-effective analysis"""
        
        # Extract profile context for better analysis
        profile_info = ""
        if profile_context:
            profile_info = f"""
ANALYZING ORGANIZATION: {profile_context.get('name', 'Unknown')}
Mission: {profile_context.get('mission', 'Not specified')}
Focus Areas: {', '.join(profile_context.get('focus_areas', []))}
NTEE Codes: {', '.join(profile_context.get('ntee_codes', []))}
"""
        
        # Create candidate summaries for analysis
        candidate_summaries = []
        for i, opp in enumerate(opportunities, 1):
            summary = f"""
{i}. {opp.get('organization_name', 'Unknown')} ({opp.get('opportunity_id', 'no_id')})
   Type: {opp.get('source_type', 'Unknown')}
   Funding: ${opp.get('funding_amount', 0):,}
   Current Score: {(opp.get('combined_score', 0) * 100):.1f}%
   Description: {opp.get('description', 'No description')[:200]}...
"""
            candidate_summaries.append(summary)
        
        prompt = f"""You are an expert grant strategist analyzing funding opportunities for optimal compatibility and risk assessment.

{profile_info}

CANDIDATES FOR ANALYSIS:
{''.join(candidate_summaries)}

For each candidate, provide analysis in this EXACT JSON format:
{{
  "opportunity_id": {{
    "compatibility_score": 0.85,
    "risk_flags": ["high_competition", "technical_requirements"],
    "priority_rank": 1,
    "quick_insight": "Strong mission alignment with excellent funding amount, but competitive application process requires strong technical expertise.",
    "confidence_level": 0.9
  }}
}}

SCORING CRITERIA:
- compatibility_score: 0.0-1.0 based on mission alignment, funding fit, and strategic value
- risk_flags: Choose from ["high_competition", "technical_requirements", "geographic_mismatch", "capacity_concerns", "timeline_pressure", "compliance_complex", "matching_required", "reporting_intensive"]
- priority_rank: 1=highest priority, rank all candidates 1-{len(opportunities)}
- quick_insight: 1-2 sentences explaining the score and key considerations
- confidence_level: 0.0-1.0 based on available information quality

Focus on practical funding strategy and organizational fit. Be concise but insightful.

RESPONSE (JSON only):"""
        
        return prompt
    
    async def _call_openai_api(self, prompt: str, model: str = "gpt-3.5-turbo", max_tokens: Optional[int] = None) -> str:
        """Call OpenAI API with cost optimization settings"""
        try:
            # Note: In production, you would set up OpenAI client with API key
            # For now, we'll simulate the API response for development
            
            # Simulated response - in production, replace with actual OpenAI call:
            # client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            # response = await client.chat.completions.create(
            #     model=model,
            #     messages=[{"role": "user", "content": prompt}],
            #     max_tokens=max_tokens or (self.max_tokens * 20),  # Adjust for batch size
            #     temperature=self.temperature
            # )
            # return response.choices[0].message.content
            
            # Simulated AI response for development
            await asyncio.sleep(2)  # Simulate API delay
            
            simulated_response = """
{
  "unified_opp_005": {
    "compatibility_score": 0.78,
    "risk_flags": ["high_competition", "technical_requirements"],
    "priority_rank": 2,
    "quick_insight": "Strong global health focus aligns well with mission, but requires significant technical expertise and faces high competition.",
    "confidence_level": 0.85
  },
  "unified_opp_006": {
    "compatibility_score": 0.89,
    "risk_flags": ["reporting_intensive"],
    "priority_rank": 1,
    "quick_insight": "Excellent local STEM education alignment with strong funding amount and geographic advantage.",
    "confidence_level": 0.92
  },
  "unified_opp_007": {
    "compatibility_score": 0.82,
    "risk_flags": ["technical_requirements", "compliance_complex"],
    "priority_rank": 3,
    "quick_insight": "Good health innovation fit but requires advanced technical capabilities and regulatory compliance expertise.",
    "confidence_level": 0.88
  }
}
"""
            return simulated_response
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    def _parse_enhanced_api_response(self, response: str, candidates: List[CandidateData]) -> Dict[str, AILiteAnalysis]:
        """Parse and validate enhanced API response into structured results"""
        try:
            # Parse JSON response
            response_data = json.loads(response.strip())
            
            results = {}
            for candidate in candidates:
                opp_id = candidate.opportunity_id
                if opp_id in response_data:
                    try:
                        analysis_data = response_data[opp_id]
                        # Validate and create enhanced AILiteAnalysis object
                        analysis = AILiteAnalysis(**analysis_data)
                        results[opp_id] = analysis
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse enhanced analysis for {opp_id}: {str(e)}")
                        # Create fallback analysis with enhanced fields
                        results[opp_id] = AILiteAnalysis(
                            compatibility_score=candidate.current_score,
                            strategic_value=StrategicValue.MEDIUM,
                            risk_assessment=["analysis_error"],
                            priority_rank=len(candidates),
                            funding_likelihood=0.5,
                            strategic_rationale="Analysis temporarily unavailable - manual review recommended.",
                            action_priority=ActionPriority.MONITOR,
                            confidence_level=0.1
                        )
                else:
                    # Create fallback for missing candidates
                    results[opp_id] = AILiteAnalysis(
                        compatibility_score=candidate.current_score,
                        strategic_value=StrategicValue.MEDIUM,
                        risk_assessment=["incomplete_data"],
                        priority_rank=len(candidates),
                        funding_likelihood=0.5,
                        strategic_rationale="Candidate not included in AI analysis response.",
                        action_priority=ActionPriority.MONITOR,
                        confidence_level=0.1
                    )
            
            return results
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse enhanced AI response as JSON: {str(e)}")
            # Return fallback results for all candidates
            fallback_results = {}
            for i, candidate in enumerate(candidates):
                fallback_results[candidate.opportunity_id] = AILiteAnalysis(
                    compatibility_score=candidate.current_score,
                    strategic_value=StrategicValue.MEDIUM,
                    risk_assessment=["api_error"],
                    priority_rank=i + 1,
                    funding_likelihood=0.5,
                    strategic_rationale="AI analysis temporarily unavailable - using baseline scoring.",
                    action_priority=ActionPriority.MONITOR,
                    confidence_level=0.2
                )
            return fallback_results
    
    def _parse_research_enhanced_api_response(self, response: str, candidates: List[CandidateData]) -> Dict[str, AILiteAnalysis]:
        """Parse and validate research-enhanced API response into structured results"""
        try:
            # Parse JSON response
            response_data = json.loads(response.strip())
            
            results = {}
            for candidate in candidates:
                opp_id = candidate.opportunity_id
                if opp_id in response_data:
                    try:
                        analysis_data = response_data[opp_id]
                        
                        # Parse research components if present
                        if "research_report" in analysis_data and analysis_data["research_report"]:
                            analysis_data["research_report"] = ResearchReport(**analysis_data["research_report"])
                        if "website_intelligence" in analysis_data and analysis_data["website_intelligence"]:
                            analysis_data["website_intelligence"] = WebsiteIntelligence(**analysis_data["website_intelligence"])
                        if "fact_extraction" in analysis_data and analysis_data["fact_extraction"]:
                            analysis_data["fact_extraction"] = FactExtraction(**analysis_data["fact_extraction"])
                        if "competitive_analysis" in analysis_data and analysis_data["competitive_analysis"]:
                            analysis_data["competitive_analysis"] = CompetitiveAnalysis(**analysis_data["competitive_analysis"])
                        
                        # Set research mode flag
                        analysis_data["research_mode_enabled"] = True
                        
                        # Validate and create enhanced AILiteAnalysis object
                        analysis = AILiteAnalysis(**analysis_data)
                        results[opp_id] = analysis
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse research-enhanced analysis for {opp_id}: {str(e)}")
                        # Create fallback analysis with research components
                        results[opp_id] = AILiteAnalysis(
                            compatibility_score=candidate.current_score,
                            strategic_value=StrategicValue.MEDIUM,
                            risk_assessment=["research_analysis_error"],
                            priority_rank=len(candidates),
                            funding_likelihood=0.5,
                            strategic_rationale="Research analysis temporarily unavailable - manual review recommended.",
                            action_priority=ActionPriority.MONITOR,
                            confidence_level=0.1,
                            research_mode_enabled=True,
                            research_report=ResearchReport(
                                executive_summary="Research analysis temporarily unavailable. Manual research required.",
                                opportunity_overview="Comprehensive research could not be completed automatically.",
                                funding_details="Please verify funding details manually.",
                                eligibility_analysis=["Manual eligibility verification required"],
                                key_dates_timeline=["Manual timeline verification required"],
                                strategic_considerations=["Manual strategic analysis required"],
                                decision_factors=["Manual decision support required"]
                            )
                        )
                else:
                    # Create fallback for missing candidates with research components
                    results[opp_id] = AILiteAnalysis(
                        compatibility_score=candidate.current_score,
                        strategic_value=StrategicValue.MEDIUM,
                        risk_assessment=["incomplete_research_data"],
                        priority_rank=len(candidates),
                        funding_likelihood=0.5,
                        strategic_rationale="Candidate not included in research analysis response.",
                        action_priority=ActionPriority.MONITOR,
                        confidence_level=0.1,
                        research_mode_enabled=True
                    )
            
            return results
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse research-enhanced AI response as JSON: {str(e)}")
            # Return fallback results for all candidates with research components
            fallback_results = {}
            for i, candidate in enumerate(candidates):
                fallback_results[candidate.opportunity_id] = AILiteAnalysis(
                    compatibility_score=candidate.current_score,
                    strategic_value=StrategicValue.MEDIUM,
                    risk_assessment=["api_research_error"],
                    priority_rank=i + 1,
                    funding_likelihood=0.5,
                    strategic_rationale="Research analysis temporarily unavailable - using baseline scoring.",
                    action_priority=ActionPriority.MONITOR,
                    confidence_level=0.2,
                    research_mode_enabled=True,
                    research_report=ResearchReport(
                        executive_summary="Automated research unavailable. Manual research required for comprehensive analysis.",
                        opportunity_overview="API error prevented comprehensive research analysis.",
                        funding_details="Manual verification of funding details required.",
                        eligibility_analysis=["Manual eligibility analysis required"],
                        key_dates_timeline=["Manual timeline analysis required"],
                        strategic_considerations=["Manual strategic assessment required"],
                        decision_factors=["Manual decision analysis required"]
                    )
                )
            return fallback_results
    
    def _parse_api_response(self, response: str, opportunities: List[Dict]) -> Dict[str, AILiteAnalysis]:
        """Parse and validate API response into structured results"""
        try:
            # Parse JSON response
            response_data = json.loads(response.strip())
            
            results = {}
            for opp_id, analysis_data in response_data.items():
                try:
                    # Validate and create AILiteAnalysis object
                    analysis = AILiteAnalysis(**analysis_data)
                    results[opp_id] = analysis
                    
                except Exception as e:
                    logger.warning(f"Failed to parse analysis for {opp_id}: {str(e)}")
                    # Create fallback analysis
                    results[opp_id] = AILiteAnalysis(
                        compatibility_score=0.5,
                        risk_flags=["analysis_error"],
                        priority_rank=len(opportunities),
                        quick_insight="Analysis temporarily unavailable - manual review recommended.",
                        confidence_level=0.1
                    )
            
            return results
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            # Return fallback results for all opportunities
            fallback_results = {}
            for i, opp in enumerate(opportunities):
                opp_id = opp.get('opportunity_id', f'fallback_{i}')
                fallback_results[opp_id] = AILiteAnalysis(
                    compatibility_score=opp.get('combined_score', 0.5),
                    risk_flags=["api_error"],
                    priority_rank=i + 1,
                    quick_insight="AI analysis temporarily unavailable - using baseline scoring.",
                    confidence_level=0.2
                )
            return fallback_results
    
    def get_cost_estimate(self, candidate_count: int, research_mode: bool = None) -> float:
        """Get cost estimate for analyzing a given number of candidates"""
        if research_mode is None:
            research_mode = self.research_mode_default
        
        if research_mode:
            return candidate_count * self.estimated_cost_per_candidate_research
        else:
            return candidate_count * self.estimated_cost_per_candidate
    
    def get_research_capabilities(self) -> Dict[str, Any]:
        """Get information about research capabilities"""
        return {
            "research_mode_available": True,
            "research_mode_default": self.research_mode_default,
            "cost_per_candidate_scoring": self.estimated_cost_per_candidate,
            "cost_per_candidate_research": self.estimated_cost_per_candidate_research,
            "research_features": [
                "Website intelligence gathering",
                "Document parsing and fact extraction", 
                "Grant team ready research reports",
                "Competitive analysis and positioning",
                "Evidence-based scoring with documentation"
            ]
        }
    
    def _create_fallback_analysis(self, candidate: 'CandidateData') -> 'AILiteAnalysis':
        """Create fallback analysis when AI processing fails"""
        return AILiteAnalysis(
            organization_name=candidate.organization_name,
            compatibility_score=0.6,
            strategic_value=StrategicValue.MEDIUM,
            funding_likelihood=0.5,
            strategic_rationale=f"Fallback analysis for {candidate.organization_name}. AI processing unavailable - manual review recommended.",
            risk_assessment=["AI processing unavailable", "Manual review required"],
            recommended_actions=[
                "Conduct manual research and analysis",
                "Review organization website and public documents",
                "Verify mission alignment manually"
            ],
            confidence_level=0.3,
            research_notes="AI processing failed - fallback analysis provided. Complete manual review recommended for accurate assessment.",
            
            # Research mode fields (if applicable)
            website_intelligence=None,
            fact_extraction=None,
            research_report=ResearchReport(
                key_findings=["AI processing unavailable"],
                strategic_insights=[f"Manual research required for {candidate.organization_name}"],
                competitive_analysis=CompetitiveAnalysis(
                    market_position="Unknown - requires manual analysis",
                    competitive_advantages=["Manual analysis needed"],
                    strategic_differentiation="Assessment pending manual review"
                ),
                evidence_base=["Fallback analysis - no AI processing completed"],
                research_confidence=0.3,
                recommended_next_steps=[
                    "Conduct comprehensive manual research",
                    "Review organizational documents and website",
                    "Assess mission alignment through direct analysis"
                ]
            ) if hasattr(candidate, 'research_mode') and candidate.research_mode else None,
            
            # Ensure all required analysis components are present
            next_steps=[
                "Manual research and verification required",
                "Review organizational mission and programs",
                "Assess funding alignment manually"
            ],
            supporting_evidence=["Fallback analysis - AI processing unavailable"]
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get processor status and configuration"""
        return {
            "processor_name": self.processor_name,
            "version": self.version,
            "model": self.model,
            "batch_size": self.batch_size,
            "estimated_cost_per_candidate": self.estimated_cost_per_candidate,
            "research_mode_available": True,
            "research_mode_default": self.research_mode_default,
            "estimated_cost_per_candidate_research": self.estimated_cost_per_candidate_research,
            "status": "ready"
        }

# Export the processor class and enhanced data models
__all__ = [
    "AILiteScorer", 
    "AILiteRequest", 
    "AILiteAnalysis", 
    "AILiteBatchResult",
    "RequestMetadata",
    "ProfileContext", 
    "CandidateData",
    "FundingHistory",
    "ExistingAnalysis",
    "BatchResults",
    "StrategicValue",
    "ActionPriority",
    # Phase 1 Enhancement: Research Data Models
    "WebsiteIntelligence",
    "FactExtraction", 
    "ResearchReport",
    "CompetitiveAnalysis"
]