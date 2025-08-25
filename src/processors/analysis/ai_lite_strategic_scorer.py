#!/usr/bin/env python3
"""
AI-Lite Strategic Scorer - Stage 2 of Optimized 5-Call Architecture
Strategic assessment and scoring processor for validated opportunities

This processor:
1. Performs semantic mission alignment analysis (requires AI)
2. Provides strategic value judgments (requires business reasoning) 
3. Generates strategic rationale explanations (requires NLP)
4. Prioritizes opportunities for resource allocation
5. Works with validated opportunities from AI-Lite-1
6. Optimized for strategic intelligence (~$0.0003 per candidate)
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.openai_service import get_openai_service
from src.processors.analysis.ai_lite_validator import ValidationAnalysis

logger = logging.getLogger(__name__)


class StrategicValue(str, Enum):
    """Strategic value assessment levels"""
    EXCEPTIONAL = "exceptional"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class ActionPriority(str, Enum):
    """Action priority classifications"""
    IMMEDIATE = "immediate"    # Apply ASAP
    PLANNED = "planned"        # Include in pipeline
    MONITOR = "monitor"        # Watch for changes
    DEFER = "defer"           # Low priority


class StrategicAnalysis(BaseModel):
    """Results from strategic scoring analysis"""
    opportunity_id: str
    
    # Strategic Scoring (AI-required components)
    mission_alignment_score: float = Field(..., ge=0.0, le=1.0, description="Semantic mission alignment")
    strategic_value: StrategicValue = Field(..., description="Strategic importance assessment")
    strategic_rationale: str = Field(..., max_length=300, description="Strategic reasoning explanation")
    
    # Priority and Action Planning
    priority_rank: int = Field(..., ge=1, description="Priority ranking within batch")
    action_priority: ActionPriority = Field(..., description="Next steps classification")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Analysis confidence")
    
    # Strategic Considerations
    key_advantages: List[str] = Field(default_factory=list, description="Strategic advantages")
    potential_concerns: List[str] = Field(default_factory=list, description="Strategic concerns")
    resource_requirements: List[str] = Field(default_factory=list, description="Resource needs")
    
    # Integration with Local Scoring
    local_scores_available: bool = Field(default=False, description="Whether local scoring data is available")
    combined_compatibility_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Combined AI+Local score")
    
    # Metadata
    analysis_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class StrategicScoringRequest(BaseModel):
    """Request structure for strategic scoring"""
    batch_id: str
    profile_context: Dict[str, Any]
    validated_candidates: List[Dict[str, Any]]  # Only validated opportunities
    validation_results: Dict[str, ValidationAnalysis]  # From AI-Lite-1
    local_scoring_data: Optional[Dict[str, Any]] = None  # From local scorers
    analysis_priority: str = "standard"


class StrategicScoringBatchResult(BaseModel):
    """Complete results from strategic scoring batch"""
    batch_id: str
    processed_count: int
    processing_time: float
    total_cost: float
    strategic_analyses: Dict[str, StrategicAnalysis]  # opportunity_id -> analysis


class AILiteStrategicScorer(BaseProcessor):
    """AI-Lite Stage 2: Strategic assessment and scoring processor"""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="ai_lite_strategic_scorer",
            description="Stage 2: Strategic assessment and scoring for validated opportunities",
            version="1.0.0",
            dependencies=["ai_lite_validator"],
            estimated_duration=45,  # 45 seconds for strategic analysis
            requires_network=True,
            requires_api_key=True,
            can_run_parallel=True,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Strategic analysis settings
        self.batch_size = 15  # Optimal batch for strategic analysis
        self.model = "gpt-4o-mini"  # Cost-effective but capable model
        self.max_tokens = 200  # Moderate tokens for strategic reasoning
        self.temperature = 0.3  # Balanced temperature for strategic judgment
        
        # Cost tracking
        self.estimated_cost_per_candidate = 0.0003  # Strategic analysis cost
        
        # Initialize OpenAI service
        self.openai_service = get_openai_service()
        
    async def execute(self, request_data: StrategicScoringRequest) -> StrategicScoringBatchResult:
        """Execute strategic scoring analysis for validated opportunities"""
        start_time = datetime.now()
        batch_id = request_data.batch_id
        
        logger.info(f"Starting AI-Lite strategic scoring for {len(request_data.validated_candidates)} candidates (batch: {batch_id})")
        
        try:
            # Create strategic scoring prompt
            scoring_prompt = self._create_strategic_scoring_prompt(request_data)
            
            # Call OpenAI API
            response = await self._call_openai_api(scoring_prompt)
            
            # Parse strategic analyses
            analyses = self._parse_strategic_response(response, request_data)
            
            # Integrate with local scoring data if available
            if request_data.local_scoring_data:
                analyses = self._integrate_local_scores(analyses, request_data.local_scoring_data)
            
            # Calculate metrics
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            estimated_cost = len(request_data.validated_candidates) * self.estimated_cost_per_candidate
            
            result = StrategicScoringBatchResult(
                batch_id=batch_id,
                processed_count=len(analyses),
                processing_time=processing_time,
                total_cost=estimated_cost,
                strategic_analyses=analyses
            )
            
            logger.info(f"AI-Lite strategic scoring completed: {len(analyses)} candidates, "
                       f"${estimated_cost:.4f} cost, {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"AI-Lite strategic scoring failed: {str(e)}")
            raise
    
    def _create_strategic_scoring_prompt(self, request_data: StrategicScoringRequest) -> str:
        """Create strategic scoring prompt focused on AI-required tasks"""
        
        profile = request_data.profile_context
        candidates = request_data.validated_candidates
        validations = request_data.validation_results
        
        # Build enhanced organization context
        org_context = f"""ORGANIZATION STRATEGIC PROFILE:
Name: {profile.get('name', 'Unknown')}
Mission: {profile.get('mission_statement', 'Not specified')}
Strategic Focus Areas: {', '.join(profile.get('focus_areas', []))}
Geographic Scope: {profile.get('geographic_scope', 'Not specified')}
Funding Capacity: {profile.get('typical_grant_size', 'Not specified')}
Strategic Priorities: {', '.join(profile.get('strategic_priorities', []))}"""

        # Build validated candidate summaries with validation context
        candidate_summaries = []
        for i, candidate in enumerate(candidates, 1):
            opp_id = candidate.get('opportunity_id', 'no_id')
            validation = validations.get(opp_id)
            
            validation_info = ""
            if validation:
                validation_info = f"""
   Validation: {validation.validation_result.value} (Confidence: {validation.confidence_level:.1f})
   Track: {validation.discovery_track.value} | Priority: {validation.priority_level}"""
            
            summary = f"""
{i}. {candidate.get('organization_name', 'Unknown')} ({opp_id})
   Type: {candidate.get('source_type', 'Unknown')}
   Focus: {candidate.get('program_focus', 'Not specified')}
   Description: {candidate.get('description', 'No description')[:200]}...{validation_info}"""
            candidate_summaries.append(summary)

        # Create strategic analysis prompt
        prompt = f"""STRATEGIC GRANT ANALYST

{org_context}

STRATEGIC MISSION: Perform strategic assessment and scoring for validated funding opportunities.

VALIDATED CANDIDATES (passed initial screening):
{''.join(candidate_summaries)}

For each candidate, provide strategic analysis in EXACT JSON format:
{{
  "opportunity_id": {{
    "mission_alignment_score": 0.85,
    "strategic_value": "high",
    "strategic_rationale": "Excellent mission alignment with digital equity goals, strong potential for long-term partnership, aligns with our geographic focus and capacity",
    "priority_rank": 2,
    "action_priority": "immediate",
    "confidence_level": 0.90,
    "key_advantages": ["Strong mission fit", "Geographic alignment", "Funding size appropriate"],
    "potential_concerns": ["High competition", "Complex application process"],
    "resource_requirements": ["Grant writer time", "Partnership development", "Board approval"]
  }}
}}

STRATEGIC ANALYSIS FOCUS (AI-Required Tasks):
1. MISSION ALIGNMENT: Semantic analysis of mission compatibility (requires NLP)
2. STRATEGIC VALUE: Business reasoning about opportunity importance (requires strategic thinking)
3. STRATEGIC RATIONALE: Clear explanation of strategic reasoning (requires language generation)
4. PRIORITY RANKING: Comparative assessment across opportunities (requires judgment)
5. RESOURCE ASSESSMENT: Understanding of organizational capacity needs (requires context)

STRATEGIC VALUE LEVELS:
- "exceptional": Transformational opportunity with high strategic impact
- "high": Strong strategic value with clear benefits
- "medium": Good fit with moderate strategic importance
- "low": Limited strategic value but potential benefits
- "minimal": Very limited strategic importance

ACTION PRIORITIES:
- "immediate": Apply as soon as possible
- "planned": Include in funding pipeline
- "monitor": Watch for changes or future opportunities
- "defer": Low priority, consider later

MISSION ALIGNMENT SCORING:
- 0.9-1.0: Exceptional alignment with core mission
- 0.7-0.89: Strong alignment with strategic priorities
- 0.5-0.69: Good alignment with some mission areas
- 0.3-0.49: Limited alignment, marginal fit
- 0.0-0.29: Poor alignment with mission

Focus on strategic intelligence that guides resource allocation decisions.

RESPONSE (JSON only):"""
        
        return prompt
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API for strategic analysis"""
        try:
            response = await self.openai_service.create_completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    def _parse_strategic_response(self, response: str, request_data: StrategicScoringRequest) -> Dict[str, StrategicAnalysis]:
        """Parse and validate strategic analysis response"""
        analyses = {}
        
        try:
            # Parse JSON response
            response_data = json.loads(response)
            
            # Process each strategic analysis
            for opportunity_id, analysis_data in response_data.items():
                try:
                    # Create strategic analysis with proper validation
                    analysis = StrategicAnalysis(
                        opportunity_id=opportunity_id,
                        **analysis_data
                    )
                    analyses[opportunity_id] = analysis
                    
                except Exception as e:
                    logger.warning(f"Failed to parse strategic analysis for {opportunity_id}: {str(e)}")
                    # Create fallback analysis
                    analyses[opportunity_id] = StrategicAnalysis(
                        opportunity_id=opportunity_id,
                        mission_alignment_score=0.5,
                        strategic_value=StrategicValue.MEDIUM,
                        strategic_rationale="Failed to parse strategic response - requires manual review",
                        priority_rank=99,
                        action_priority=ActionPriority.MONITOR,
                        confidence_level=0.1,
                        key_advantages=["parsing_error"],
                        potential_concerns=["analysis_failed"],
                        resource_requirements=["manual_review"]
                    )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            # Create fallback analyses for all candidates
            for candidate in request_data.validated_candidates:
                opportunity_id = candidate.get('opportunity_id', 'unknown')
                analyses[opportunity_id] = StrategicAnalysis(
                    opportunity_id=opportunity_id,
                    mission_alignment_score=0.5,
                    strategic_value=StrategicValue.MEDIUM,
                    strategic_rationale="API response parsing failed - requires manual analysis",
                    priority_rank=99,
                    action_priority=ActionPriority.MONITOR,
                    confidence_level=0.1,
                    key_advantages=["unknown"],
                    potential_concerns=["api_error"],
                    resource_requirements=["retry_analysis"]
                )
        
        return analyses
    
    def _integrate_local_scores(self, analyses: Dict[str, StrategicAnalysis], local_data: Dict[str, Any]) -> Dict[str, StrategicAnalysis]:
        """Integrate AI strategic analysis with local scoring data"""
        for opportunity_id, analysis in analyses.items():
            if opportunity_id in local_data:
                local_score = local_data[opportunity_id]
                
                # Combine AI mission alignment with local scoring
                if 'combined_score' in local_score:
                    # Weight: 60% AI strategic, 40% local algorithmic
                    combined_score = (0.6 * analysis.mission_alignment_score) + (0.4 * local_score['combined_score'])
                    analysis.combined_compatibility_score = combined_score
                    analysis.local_scores_available = True
                    
                    # Update strategic rationale with local insights
                    if 'risk_score' in local_score:
                        risk_info = f" Local risk assessment: {local_score['risk_score']:.2f}."
                        analysis.strategic_rationale += risk_info
        
        return analyses
    
    def get_processor_stats(self) -> Dict[str, Any]:
        """Get processor statistics and configuration"""
        return {
            "processor_name": "ai_lite_strategic_scorer",
            "stage": "strategic_scoring",
            "model": self.model,
            "max_tokens": self.max_tokens,
            "estimated_cost_per_candidate": self.estimated_cost_per_candidate,
            "batch_size": self.batch_size,
            "processing_focus": "strategic_intelligence",
            "ai_tasks": [
                "mission_alignment_analysis",
                "strategic_value_assessment", 
                "strategic_rationale_generation",
                "priority_ranking",
                "resource_requirement_assessment"
            ],
            "optimization_target": "strategic_accuracy"
        }