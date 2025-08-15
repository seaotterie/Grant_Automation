"""
AI Lite Scorer - Cost-effective candidate analysis for ANALYZE tab

Purpose: Fast, cost-effective candidate evaluation and prioritization
Model: GPT-3.5 for optimal cost/performance ratio (~$0.0001 per candidate)
Batch Processing: 10-20 candidates per API call for cost optimization

Features:
- Compatibility scoring with AI-enhanced analysis
- Risk flag identification
- Opportunity ranking and prioritization
- Basic insights (1-2 sentence summaries per candidate)
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import openai
from pydantic import BaseModel, Field
from enum import Enum

from ..base_processor import BaseProcessor

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

class RequestMetadata(BaseModel):
    """AI request metadata for tracking and optimization"""
    batch_id: str
    profile_id: str
    analysis_type: str = "compatibility_scoring"
    model_preference: str = "gpt-3.5-turbo"
    cost_limit: float = 0.01
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
    """Enhanced AI Lite analysis results for a single candidate"""
    compatibility_score: float = Field(..., ge=0.0, le=1.0, description="AI compatibility score 0-1")
    strategic_value: StrategicValue = Field(..., description="Strategic importance classification")
    risk_assessment: List[str] = Field(default_factory=list, description="Identified risk factors")
    priority_rank: int = Field(..., ge=1, description="Priority ranking within batch")
    funding_likelihood: float = Field(..., ge=0.0, le=1.0, description="Probability of funding success")
    strategic_rationale: str = Field(..., description="2-sentence strategic analysis")
    action_priority: ActionPriority = Field(..., description="Next steps classification")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Analysis confidence")
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
        super().__init__()
        self.processor_name = "AI Lite Scorer"
        self.description = "Cost-effective AI analysis for candidate prioritization"
        self.version = "1.0.0"
        
        # Cost optimization settings
        self.batch_size = 15  # Optimal batch size for cost/performance
        self.model = "gpt-3.5-turbo"  # Cost-effective model
        self.max_tokens = 150  # Keep responses concise for cost control
        self.temperature = 0.3  # Lower temperature for consistent analysis
        
        # Cost tracking
        self.estimated_cost_per_candidate = 0.0001  # Conservative estimate
        
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
        
        try:
            # Prepare enhanced batch analysis prompt
            batch_prompt = self._create_enhanced_batch_prompt(request_data)
            
            # Call OpenAI API with cost optimization
            response = await self._call_openai_api(batch_prompt, request_data.request_metadata.model_preference)
            
            # Parse and validate enhanced results
            analysis_results = self._parse_enhanced_api_response(response, request_data.candidates)
            
            # Calculate processing metrics
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            estimated_cost = len(request_data.candidates) * self.estimated_cost_per_candidate
            
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
            raise
    
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
    
    async def _call_openai_api(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
        """Call OpenAI API with cost optimization settings"""
        try:
            # Note: In production, you would set up OpenAI client with API key
            # For now, we'll simulate the API response for development
            
            # Simulated response - in production, replace with actual OpenAI call:
            # client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            # response = await client.chat.completions.create(
            #     model=self.model,
            #     messages=[{"role": "user", "content": prompt}],
            #     max_tokens=self.max_tokens * 20,  # Adjust for batch size
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
    
    def get_cost_estimate(self, candidate_count: int) -> float:
        """Get cost estimate for analyzing a given number of candidates"""
        return candidate_count * self.estimated_cost_per_candidate
    
    def get_status(self) -> Dict[str, Any]:
        """Get processor status and configuration"""
        return {
            "processor_name": self.processor_name,
            "version": self.version,
            "model": self.model,
            "batch_size": self.batch_size,
            "estimated_cost_per_candidate": self.estimated_cost_per_candidate,
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
    "ActionPriority"
]