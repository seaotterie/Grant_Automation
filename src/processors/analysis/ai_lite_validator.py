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
    """Results from AI-Lite validation analysis with enhanced intelligence"""
    opportunity_id: str
    
    # Core Validation Results
    validation_result: ValidationResult
    eligibility_status: EligibilityStatus
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    
    # Triage Results
    discovery_track: DiscoveryTrack
    priority_level: str = Field(..., pattern="^(low|medium|high|urgent)$")
    go_no_go: str = Field(..., pattern="^(go|no_go|investigate)$")
    
    # Enhanced Validation Intelligence (Phase 2A)
    funding_provider_type: str = Field(default="unknown", description="Actual funder vs aggregator vs information site")
    program_status: str = Field(default="unknown", description="Active, archived, seasonal, or unclear")
    application_pathway: str = Field(default="unknown", description="Clear process, vague inquiry, or no pathway")
    
    # Competition & Complexity Pre-Screening
    competition_level: str = Field(default="unknown", pattern="^(low|moderate|high|extreme|unknown)$")
    application_complexity: str = Field(default="unknown", pattern="^(simple|moderate|complex|extreme|unknown)$")
    success_probability: float = Field(default=0.5, ge=0.0, le=1.0, description="Early success probability assessment")
    
    # Website Intelligence
    deadline_indicators: List[str] = Field(default_factory=list, description="Application deadlines found")
    contact_quality: str = Field(default="unknown", pattern="^(program_officer|direct|generic|none|unknown)$")
    recent_activity: List[str] = Field(default_factory=list, description="Recent awards, announcements, updates")
    
    # Original Analysis Fields
    validation_reasoning: str = Field(..., max_length=300, description="Enhanced validation reasoning")
    key_flags: List[str] = Field(default_factory=list, description="Important flags or concerns")
    next_actions: List[str] = Field(default_factory=list, description="Recommended next steps")
    
    # Metadata
    analysis_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    enhancement_level: str = Field(default="enhanced_2a", description="Validation enhancement version")


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
        
        # Optimization settings for enhanced validation (GPT-5-nano for cost-effective reliability)
        self.batch_size = 20  # Higher batch size for simple validation
        self.model = "gpt-5-nano"  # Most cost-effective GPT-5 model with superior reasoning
        self.max_tokens = 800  # Sufficient tokens for enhanced multi-opportunity analysis
        self.temperature = 0.2  # Low temperature for consistent validation
        
        # Cost tracking (GPT-5-nano pricing: $0.25/1M input, $2.0/1M output)
        self.estimated_cost_per_candidate = 0.00008  # More cost-effective with GPT-5-nano enhanced intelligence
        
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

        # Create enhanced validation prompt with GPT-5 intelligence
        prompt = f"""ENHANCED OPPORTUNITY VALIDATION SPECIALIST (GPT-5 Phase 2A)

{org_context}

VALIDATION MISSION: Perform comprehensive validation with enhanced intelligence to optimize downstream processing efficiency.

CANDIDATES FOR ENHANCED VALIDATION:
{''.join(candidate_summaries)}

For each candidate, provide enhanced validation analysis in EXACT JSON format:
{{
  "opportunity_id": {{
    "validation_result": "valid_funding",
    "eligibility_status": "eligible", 
    "confidence_level": 0.85,
    "discovery_track": "foundation",
    "priority_level": "medium",
    "go_no_go": "go",
    
    "funding_provider_type": "actual_funder",
    "program_status": "active",
    "application_pathway": "clear_process",
    
    "competition_level": "moderate",
    "application_complexity": "moderate",
    "success_probability": 0.75,
    
    "deadline_indicators": ["March 15, 2025", "Annual cycle"],
    "contact_quality": "program_officer",
    "recent_activity": ["2024 awards announced", "Program guidelines updated"],
    
    "validation_reasoning": "Confirmed active foundation with clear application process, moderate competition, strong mission alignment indicators",
    "key_flags": ["application_deadline_approaching", "moderate_competition"],
    "next_actions": ["detailed_strategic_analysis", "contact_program_officer"]
  }}
}}

ENHANCED VALIDATION CRITERIA (GPT-5 Intelligence):

1. FUNDING PROVIDER VERIFICATION:
   - "actual_funder": Direct grant-making organization with funding capacity
   - "fiscal_sponsor": Intermediary managing funds for others  
   - "aggregator": Information site listing multiple opportunities
   - "service_provider": Consulting or application assistance (not funding)
   - "unknown": Cannot determine funding capacity

2. PROGRAM STATUS ASSESSMENT:
   - "active": Currently accepting applications with recent activity
   - "seasonal": Regular cycle, currently open or opening soon
   - "archived": Program exists but not currently active
   - "unclear": Status ambiguous, requires investigation
   - "unknown": Cannot determine program status

3. APPLICATION PATHWAY ANALYSIS:
   - "clear_process": Detailed guidelines, application forms, submission process
   - "inquiry_based": Letter of inquiry or initial contact required
   - "vague_process": General interest but unclear application method
   - "no_pathway": No clear application mechanism identified
   - "unknown": Cannot determine application process

4. COMPETITION & COMPLEXITY PRE-SCREENING:
   - Competition: "low" (niche/specialized), "moderate" (typical), "high" (national/prestigious), "extreme" (ultra-competitive)
   - Complexity: "simple" (basic application), "moderate" (standard requirements), "complex" (extensive documentation), "extreme" (multi-stage process)
   - Success Probability: 0.0-1.0 based on organizational fit, competition level, and requirement match

5. WEBSITE INTELLIGENCE EXTRACTION:
   - Deadline Indicators: Application deadlines, funding cycles, key dates
   - Contact Quality: "program_officer" (named contact), "direct" (department), "generic" (general inquiry), "none" (no contact info)
   - Recent Activity: Award announcements, program updates, news, guidelines changes

STRATEGIC FILTERING OBJECTIVES:
- Eliminate non-funding sources before expensive AI-heavy processing
- Identify high-probability opportunities for priority processing
- Extract actionable intelligence for strategic decision-making
- Optimize resource allocation through enhanced early-stage intelligence

Focus on maximizing downstream processing efficiency through superior early-stage intelligence.

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
            
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    def _parse_validation_response(self, response: str, candidates: List[Dict]) -> Dict[str, ValidationAnalysis]:
        """Parse and validate API response with enhanced debugging"""
        validations = {}
        
        try:
            # Debug: Log the raw response for troubleshooting
            logger.info(f"Raw API response length: {len(response)}")
            if len(response) > 0:
                logger.info(f"Raw API response (first 200 chars): {repr(response[:200])}")
            else:
                logger.error("Empty response received from API")
                raise ValueError("Empty response from OpenAI API")
            
            # Clean the response - remove any markdown formatting or extra text
            cleaned_response = response.strip()
            
            # Remove markdown json blocks
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
                
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
                
            cleaned_response = cleaned_response.strip()
            
            # Find JSON content between first { and last }
            start_idx = cleaned_response.find('{')
            end_idx = cleaned_response.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                cleaned_response = cleaned_response[start_idx:end_idx+1]
                
            logger.info(f"Cleaned response length: {len(cleaned_response)}")
            logger.info(f"Cleaned response preview: {cleaned_response[:100]}...")
            
            # Parse JSON response
            response_data = json.loads(cleaned_response)
            
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
            logger.error(f"Problematic JSON content: {cleaned_response}")
            
            # Try to save the malformed JSON for debugging
            with open("debug_malformed_json.txt", "w") as f:
                f.write(f"Original response:\n{response}\n\nCleaned response:\n{cleaned_response}")
            
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