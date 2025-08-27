#!/usr/bin/env python3
"""
AI-Lite Validator - Stage 1 of Optimized 5-Call Architecture
Fast validation and triage processor for opportunity verification

This processor:
1. Validates that opportunities are real funding sources (not information sites)
2. Performs basic eligibility and geographic screening
3. Assigns opportunities to appropriate discovery tracks
4. Provides go/no-go recommendations for further analysis
5. Optimized for speed and cost-effectiveness (~$0.0001 per candidate)
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

logger = logging.getLogger(__name__)


class ValidationResult(str, Enum):
    """Validation results for opportunities"""
    VALID_FUNDING = "valid_funding"           # Confirmed funding opportunity
    INVALID_NOT_FUNDING = "invalid_not_funding"  # Not a funding source
    UNCERTAIN_NEEDS_RESEARCH = "uncertain_needs_research"  # Requires deeper investigation
    EXPIRED_INACTIVE = "expired_inactive"     # Program no longer active


class DiscoveryTrack(str, Enum):
    """Discovery track assignments"""
    GOVERNMENT = "government"
    COMMERCIAL = "commercial" 
    STATE = "state"
    NONPROFIT = "nonprofit"
    FOUNDATION = "foundation"


class EligibilityStatus(str, Enum):
    """Basic eligibility assessment"""
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    CONDITIONAL = "conditional"
    UNKNOWN = "unknown"


class ValidationAnalysis(BaseModel):
    """Results from AI-Lite validation analysis"""
    opportunity_id: str
    
    # Validation Results
    validation_result: ValidationResult
    eligibility_status: EligibilityStatus
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    
    # Triage Results
    discovery_track: DiscoveryTrack
    priority_level: str = Field(..., pattern="^(low|medium|high|urgent)$")
    go_no_go: str = Field(..., pattern="^(go|no_go|investigate)$")
    
    # Brief Analysis
    validation_reasoning: str = Field(..., max_length=200, description="Brief explanation of validation decision")
    key_flags: List[str] = Field(default_factory=list, description="Important flags or concerns")
    next_actions: List[str] = Field(default_factory=list, description="Recommended next steps")
    
    # Metadata
    analysis_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ValidationRequest(BaseModel):
    """Request structure for validation analysis"""
    batch_id: str
    profile_context: Dict[str, Any]
    candidates: List[Dict[str, Any]]
    analysis_priority: str = "standard"


class ValidationBatchResult(BaseModel):
    """Complete results from validation batch"""
    batch_id: str
    processed_count: int
    processing_time: float
    total_cost: float
    validations: Dict[str, ValidationAnalysis]  # opportunity_id -> analysis


class AILiteValidator(BaseProcessor):
    """AI-Lite Stage 1: Fast validation and triage processor"""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="ai_lite_validator",
            description="Stage 1: Fast opportunity validation and triage for 5-call architecture",
            version="1.0.0",
            dependencies=[],
            estimated_duration=30,  # 30 seconds - optimized for speed
            requires_network=True,
            requires_api_key=True,
            can_run_parallel=True,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Optimization settings for validation (Updated for GPT-5-nano)
        self.batch_size = 20  # Higher batch size for simple validation
        self.model = "gpt-5-nano"  # Most cost-effective GPT-5 model with higher accuracy
        self.max_tokens = 100  # Minimal tokens for fast validation
        self.temperature = 0.1  # Very low temperature for consistent validation
        
        # Cost tracking (Updated GPT-5-nano pricing: $0.05/1M input, $0.40/1M output)
        self.estimated_cost_per_candidate = 0.000025  # Even more cost-effective with GPT-5-nano
        
        # Initialize OpenAI service
        self.openai_service = get_openai_service()
        
    async def execute(self, request_data: ValidationRequest) -> ValidationBatchResult:
        """Execute fast validation and triage analysis"""
        start_time = datetime.now()
        batch_id = request_data.batch_id
        
        logger.info(f"Starting AI-Lite validation for {len(request_data.candidates)} candidates (batch: {batch_id})")
        
        try:
            # Create validation prompt
            validation_prompt = self._create_validation_prompt(request_data)
            
            # Call OpenAI API
            response = await self._call_openai_api(validation_prompt)
            
            # Parse validation results
            validations = self._parse_validation_response(response, request_data.candidates)
            
            # Calculate metrics
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            estimated_cost = len(request_data.candidates) * self.estimated_cost_per_candidate
            
            result = ValidationBatchResult(
                batch_id=batch_id,
                processed_count=len(validations),
                processing_time=processing_time,
                total_cost=estimated_cost,
                validations=validations
            )
            
            logger.info(f"AI-Lite validation completed: {len(validations)} candidates, "
                       f"${estimated_cost:.4f} cost, {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"AI-Lite validation failed: {str(e)}")
            raise
    
    def _create_validation_prompt(self, request_data: ValidationRequest) -> str:
        """Create focused validation prompt"""
        
        profile = request_data.profile_context
        candidates = request_data.candidates
        
        # Build organization context
        org_context = f"""ORGANIZATION PROFILE:
Name: {profile.get('name', 'Unknown')}
Mission Focus: {', '.join(profile.get('focus_areas', []))}
Geographic Scope: {profile.get('geographic_scope', 'Not specified')}
Organization Type: {profile.get('organization_type', 'Nonprofit')}"""

        # Build candidate summaries for validation
        candidate_summaries = []
        for i, candidate in enumerate(candidates, 1):
            summary = f"""
{i}. {candidate.get('organization_name', 'Unknown')} ({candidate.get('opportunity_id', 'no_id')})
   Type: {candidate.get('source_type', 'Unknown')}
   Website: {candidate.get('website', 'Not available')}
   Basic Info: {candidate.get('description', 'No description')[:150]}..."""
            candidate_summaries.append(summary)

        # Create focused validation prompt
        prompt = f"""OPPORTUNITY VALIDATION SPECIALIST

{org_context}

VALIDATION MISSION: Quickly assess if these are legitimate funding opportunities worth pursuing.

CANDIDATES FOR VALIDATION:
{''.join(candidate_summaries)}

For each candidate, provide validation analysis in EXACT JSON format:
{{
  "opportunity_id": {{
    "validation_result": "valid_funding",
    "eligibility_status": "eligible",
    "confidence_level": 0.85,
    "discovery_track": "foundation",
    "priority_level": "medium",
    "go_no_go": "go",
    "validation_reasoning": "Confirmed active foundation with technology grants matching our mission",
    "key_flags": ["application_deadline_approaching", "high_competition"],
    "next_actions": ["detailed_research", "contact_program_officer"]
  }}
}}

VALIDATION CRITERIA:
1. FUNDING VERIFICATION: Is this a real funding source or just information/services?
2. ACTIVE STATUS: Are they currently accepting applications?
3. BASIC ELIGIBILITY: Do we meet fundamental requirements (nonprofit status, geography)?
4. TRACK ASSIGNMENT: Which discovery track does this belong to?
5. PRIORITY ASSESSMENT: How urgently should this be researched?

VALIDATION RESULTS:
- "valid_funding": Confirmed funding opportunity
- "invalid_not_funding": Not a funding source
- "uncertain_needs_research": Requires investigation
- "expired_inactive": Program inactive

ELIGIBILITY STATUS:
- "eligible": We meet basic requirements
- "ineligible": We don't qualify
- "conditional": Requirements unclear
- "unknown": Cannot determine from available info

GO/NO-GO DECISIONS:
- "go": Proceed to strategic scoring
- "no_go": Stop processing this candidate
- "investigate": Needs research before decision

Focus on fast, accurate validation to eliminate non-opportunities early.

RESPONSE (JSON only):"""
        
        return prompt
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API for validation analysis"""
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
    
    def _parse_validation_response(self, response: str, candidates: List[Dict]) -> Dict[str, ValidationAnalysis]:
        """Parse and validate API response"""
        validations = {}
        
        try:
            # Parse JSON response
            response_data = json.loads(response)
            
            # Process each validation
            for opportunity_id, analysis_data in response_data.items():
                try:
                    # Create validation analysis with proper validation
                    validation = ValidationAnalysis(
                        opportunity_id=opportunity_id,
                        **analysis_data
                    )
                    validations[opportunity_id] = validation
                    
                except Exception as e:
                    logger.warning(f"Failed to parse validation for {opportunity_id}: {str(e)}")
                    # Create fallback validation
                    validations[opportunity_id] = ValidationAnalysis(
                        opportunity_id=opportunity_id,
                        validation_result=ValidationResult.UNCERTAIN_NEEDS_RESEARCH,
                        eligibility_status=EligibilityStatus.UNKNOWN,
                        confidence_level=0.1,
                        discovery_track=DiscoveryTrack.FOUNDATION,
                        priority_level="medium",
                        go_no_go="investigate",
                        validation_reasoning="Failed to parse validation response",
                        key_flags=["parsing_error"],
                        next_actions=["manual_review"]
                    )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            # Create fallback validations for all candidates
            for candidate in candidates:
                opportunity_id = candidate.get('opportunity_id', 'unknown')
                validations[opportunity_id] = ValidationAnalysis(
                    opportunity_id=opportunity_id,
                    validation_result=ValidationResult.UNCERTAIN_NEEDS_RESEARCH,
                    eligibility_status=EligibilityStatus.UNKNOWN,
                    confidence_level=0.1,
                    discovery_track=DiscoveryTrack.FOUNDATION,
                    priority_level="medium", 
                    go_no_go="investigate",
                    validation_reasoning="API response parsing failed",
                    key_flags=["api_error"],
                    next_actions=["retry_analysis"]
                )
        
        return validations
    
    def get_processor_stats(self) -> Dict[str, Any]:
        """Get processor statistics and configuration"""
        return {
            "processor_name": "ai_lite_validator",
            "stage": "validation_triage",
            "model": self.model,
            "max_tokens": self.max_tokens,
            "estimated_cost_per_candidate": self.estimated_cost_per_candidate,
            "batch_size": self.batch_size,
            "processing_focus": "opportunity_validation",
            "optimization_target": "speed_and_cost"
        }