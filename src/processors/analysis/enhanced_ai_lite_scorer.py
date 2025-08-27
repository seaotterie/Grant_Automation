"""
Enhanced AI Lite Scorer - Production-Ready Error Recovery System
Improved version of AI Lite Scorer with comprehensive error handling,
retry logic, circuit breakers, and graceful degradation.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import openai

from .ai_lite_scorer import (
    AILiteScorer, AILiteRequest, AILiteAnalysis, AILiteBatchResult,
    CandidateData, StrategicValue, ActionPriority
)
from src.core.error_recovery import get_recovery_manager, ErrorCategory

logger = logging.getLogger(__name__)

class EnhancedAILiteScorer(AILiteScorer):
    """Enhanced AI Lite Scorer with comprehensive error recovery"""
    
    def __init__(self):
        super().__init__()
        self.recovery_manager = get_recovery_manager()
        self.openai_client = None
        self._initialize_openai_client()
    
    def _initialize_openai_client(self):
        """Initialize OpenAI client with proper error handling"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = openai.AsyncOpenAI(api_key=api_key)
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("OpenAI API key not found, using simulation mode")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    async def execute(self, request_data: AILiteRequest) -> AILiteBatchResult:
        """Execute AI Lite analysis with enhanced error recovery"""
        operation_id = f"ai_lite_{request_data.request_metadata.batch_id}"
        
        # Create operation context for recovery
        context = {
            "batch_id": request_data.request_metadata.batch_id,
            "candidates": [candidate.dict() for candidate in request_data.candidates],
            "model_preference": request_data.request_metadata.model_preference,
            "profile_context": request_data.profile_context.dict(),
            "operation_type": "ai_lite_analysis"
        }
        
        # Execute with comprehensive retry and recovery
        result = await self.recovery_manager.execute_with_retry(
            operation=lambda: self._execute_with_recovery(request_data, context),
            operation_id=operation_id,
            context=context
        )
        
        return result
    
    async def _execute_with_recovery(self, request_data: AILiteRequest, context: Dict[str, Any]) -> AILiteBatchResult:
        """Internal execution method with recovery context"""
        start_time = datetime.now()
        batch_id = request_data.request_metadata.batch_id
        
        logger.info(f"Starting enhanced AI Lite analysis for {len(request_data.candidates)} candidates (batch: {batch_id})")
        
        # Determine research mode
        research_mode = self._should_enable_research_mode(request_data)
        context["research_mode"] = research_mode
        
        # Prepare enhanced batch analysis prompt
        if research_mode:
            batch_prompt = self._create_research_enhanced_batch_prompt(request_data)
            max_tokens = self.max_tokens_research
            cost_per_candidate = self.estimated_cost_per_candidate_research
        else:
            batch_prompt = self._create_enhanced_batch_prompt(request_data)
            max_tokens = self.max_tokens
            cost_per_candidate = self.estimated_cost_per_candidate
        
        context["batch_prompt"] = batch_prompt
        context["max_tokens"] = max_tokens
        
        # Call OpenAI API with enhanced error handling
        response = await self._call_openai_api_with_recovery(
            batch_prompt, 
            request_data.request_metadata.model_preference,
            max_tokens=max_tokens,
            context=context
        )
        
        context["raw_response"] = response
        
        # Parse and validate results with recovery
        if research_mode:
            analysis_results = await self._parse_research_response_with_recovery(response, request_data.candidates, context)
        else:
            analysis_results = await self._parse_enhanced_response_with_recovery(response, request_data.candidates, context)
        
        # Calculate processing metrics
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        estimated_cost = len(request_data.candidates) * cost_per_candidate
        
        # Create comprehensive result structure
        from .ai_lite_scorer import BatchResults
        batch_results = BatchResults(
            batch_id=batch_id,
            processed_count=len(analysis_results),
            processing_time=processing_time,
            total_cost=estimated_cost,
            model_used=request_data.request_metadata.model_preference,
            analysis_quality="enhanced" if research_mode else "standard"
        )
        
        result = AILiteBatchResult(
            batch_results=batch_results,
            candidate_analysis=analysis_results
        )
        
        logger.info(f"Enhanced AI Lite analysis completed: {len(analysis_results)} candidates, "
                   f"${estimated_cost:.4f} estimated cost, {processing_time:.2f}s")
        
        return result
    
    async def _call_openai_api_with_recovery(
        self, 
        prompt: str, 
        model: str = "gpt-3.5-turbo", 
        max_tokens: Optional[int] = None,
        context: Dict[str, Any] = None
    ) -> str:
        """Call OpenAI API with comprehensive error recovery"""
        
        async def api_operation():
            if self.openai_client is None:
                # Fallback to simulation in development
                logger.warning("Using simulated OpenAI response - no API key configured")
                return await self._simulate_openai_response(context)
            
            try:
                response = await self.openai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens or (self.max_tokens * 20),
                    temperature=self.temperature,
                    timeout=30  # 30 second timeout
                )
                return response.choices[0].message.content
                
            except openai.RateLimitError as e:
                # Specific handling for rate limits
                error_context = self.recovery_manager.classify_error(e, context)
                error_context.category = ErrorCategory.API_RATE_LIMIT
                raise e
            
            except openai.APITimeoutError as e:
                # Specific handling for timeouts
                error_context = self.recovery_manager.classify_error(e, context)
                error_context.category = ErrorCategory.API_TIMEOUT
                raise e
            
            except openai.AuthenticationError as e:
                # Authentication errors are not recoverable
                error_context = self.recovery_manager.classify_error(e, context)
                error_context.category = ErrorCategory.API_AUTH_ERROR
                logger.critical("OpenAI authentication failed - check API key")
                raise e
            
            except openai.APIError as e:
                # General API errors
                logger.error(f"OpenAI API error: {e}")
                raise e
        
        # Execute with recovery
        operation_id = f"openai_api_{model}"
        return await self.recovery_manager.execute_with_retry(
            operation=api_operation,
            operation_id=operation_id,
            context=context
        )
    
    async def _simulate_openai_response(self, context: Dict[str, Any]) -> str:
        """Improved simulation with more realistic error scenarios"""
        import random
        
        # Simulate various error scenarios for testing
        error_chance = random.random()
        
        if error_chance < 0.1:  # 10% chance of timeout
            await asyncio.sleep(3)
            raise Exception("Request timeout - simulated for testing")
        elif error_chance < 0.15:  # 5% chance of rate limit
            raise Exception("Rate limit exceeded - simulated for testing")
        elif error_chance < 0.18:  # 3% chance of parsing error
            return '{"incomplete": "response with missing data'
        
        # Normal simulation with realistic delay
        await asyncio.sleep(random.uniform(1.0, 3.0))
        
        # Generate dynamic response based on candidates
        candidates = context.get("candidates", [])
        research_mode = context.get("research_mode", False)
        
        response_data = {}
        for i, candidate in enumerate(candidates):
            candidate_id = candidate.get("opportunity_id", f"sim_opp_{i}")
            
            if research_mode:
                response_data[candidate_id] = {
                    "compatibility_score": round(random.uniform(0.4, 0.95), 2),
                    "strategic_value": random.choice(["high", "medium", "low"]),
                    "risk_assessment": random.sample([
                        "high_competition", "technical_requirements", "geographic_mismatch",
                        "capacity_concerns", "timeline_pressure", "compliance_complex"
                    ], k=random.randint(1, 3)),
                    "priority_rank": i + 1,
                    "funding_likelihood": round(random.uniform(0.3, 0.9), 2),
                    "strategic_rationale": f"Simulated analysis for {candidate.get('organization_name', 'Unknown Organization')} with detailed research components.",
                    "action_priority": random.choice(["immediate", "planned", "monitor"]),
                    "confidence_level": round(random.uniform(0.7, 0.95), 2),
                    "research_mode_enabled": True,
                    "research_report": {
                        "executive_summary": f"Comprehensive research summary for {candidate.get('organization_name', 'organization')} highlighting strategic fit and implementation considerations.",
                        "opportunity_overview": "Detailed opportunity analysis with strategic context and competitive positioning.",
                        "eligibility_analysis": ["Primary eligibility requirements met", "Secondary criteria need verification"],
                        "key_dates_timeline": ["Application deadline analysis", "Award notification schedule"],
                        "funding_details": "Comprehensive funding structure and requirements analysis",
                        "strategic_considerations": ["Market positioning factors", "Implementation complexity"],
                        "decision_factors": ["Go/no-go decision criteria", "Risk mitigation strategies"]
                    }
                }
            else:
                response_data[candidate_id] = {
                    "compatibility_score": round(random.uniform(0.4, 0.95), 2),
                    "strategic_value": random.choice(["high", "medium", "low"]),
                    "risk_assessment": random.sample([
                        "high_competition", "technical_requirements", "capacity_concerns"
                    ], k=random.randint(1, 2)),
                    "priority_rank": i + 1,
                    "funding_likelihood": round(random.uniform(0.3, 0.9), 2),
                    "strategic_rationale": f"Strategic analysis for {candidate.get('organization_name', 'Unknown Organization')} with compatibility assessment.",
                    "action_priority": random.choice(["immediate", "planned", "monitor"]),
                    "confidence_level": round(random.uniform(0.7, 0.95), 2)
                }
        
        return json.dumps(response_data, indent=2)
    
    async def _parse_enhanced_response_with_recovery(
        self, 
        response: str, 
        candidates: List[CandidateData], 
        context: Dict[str, Any]
    ) -> Dict[str, AILiteAnalysis]:
        """Parse enhanced API response with recovery capabilities"""
        
        async def parsing_operation():
            return self._parse_enhanced_api_response(response, candidates)
        
        try:
            return await self.recovery_manager.execute_with_retry(
                operation=parsing_operation,
                operation_id="parse_enhanced_response",
                context={**context, "raw_response": response}
            )
        except Exception as e:
            # Final fallback - create basic analysis for all candidates
            logger.warning(f"All parsing recovery attempts failed: {e}")
            return self._create_fallback_analysis(candidates, "Enhanced parsing failed")
    
    async def _parse_research_response_with_recovery(
        self, 
        response: str, 
        candidates: List[CandidateData], 
        context: Dict[str, Any]
    ) -> Dict[str, AILiteAnalysis]:
        """Parse research-enhanced API response with recovery capabilities"""
        
        async def parsing_operation():
            return self._parse_research_enhanced_api_response(response, candidates)
        
        try:
            return await self.recovery_manager.execute_with_retry(
                operation=parsing_operation,
                operation_id="parse_research_response",
                context={**context, "raw_response": response}
            )
        except Exception as e:
            # Final fallback - create basic research analysis for all candidates
            logger.warning(f"All research parsing recovery attempts failed: {e}")
            return self._create_fallback_research_analysis(candidates, "Research parsing failed")
    
    def _create_fallback_analysis(self, candidates: List[CandidateData], reason: str) -> Dict[str, AILiteAnalysis]:
        """Create fallback analysis when all recovery attempts fail"""
        results = {}
        
        for i, candidate in enumerate(candidates):
            # Use existing score or calculate basic score
            basic_score = candidate.current_score if candidate.current_score > 0 else 0.5
            
            results[candidate.opportunity_id] = AILiteAnalysis(
                compatibility_score=basic_score,
                strategic_value=StrategicValue.MEDIUM if basic_score > 0.6 else StrategicValue.LOW,
                risk_assessment=["ai_processing_unavailable", "manual_review_required"],
                priority_rank=i + 1,
                funding_likelihood=basic_score * 0.8,
                strategic_rationale=f"Fallback analysis used due to: {reason}. Manual review recommended for comprehensive assessment.",
                action_priority=ActionPriority.MONITOR,
                confidence_level=0.2,
                research_mode_enabled=False
            )
        
        logger.info(f"Created fallback analysis for {len(candidates)} candidates")
        return results
    
    def _create_fallback_research_analysis(self, candidates: List[CandidateData], reason: str) -> Dict[str, AILiteAnalysis]:
        """Create fallback research analysis when all recovery attempts fail"""
        results = {}
        
        from .ai_lite_scorer import ResearchReport
        
        for i, candidate in enumerate(candidates):
            basic_score = candidate.current_score if candidate.current_score > 0 else 0.5
            
            # Create minimal research report
            research_report = ResearchReport(
                executive_summary=f"Automated research analysis unavailable for {candidate.organization_name}. Manual research recommended for comprehensive intelligence gathering.",
                opportunity_overview=f"Basic opportunity profile for {candidate.organization_name}. Comprehensive analysis requires manual review due to system limitations.",
                funding_details="Funding details require manual verification due to processing limitations.",
                eligibility_analysis=["Automated eligibility analysis unavailable", "Manual verification required"],
                key_dates_timeline=["Timeline analysis requires manual review"],
                strategic_considerations=["Manual strategic analysis recommended"],
                decision_factors=[f"Manual decision framework needed for {candidate.organization_name}"]
            )
            
            results[candidate.opportunity_id] = AILiteAnalysis(
                compatibility_score=basic_score,
                strategic_value=StrategicValue.MEDIUM if basic_score > 0.6 else StrategicValue.LOW,
                risk_assessment=["ai_research_unavailable", "manual_research_required"],
                priority_rank=i + 1,
                funding_likelihood=basic_score * 0.8,
                strategic_rationale=f"Fallback research analysis due to: {reason}. Comprehensive manual research strongly recommended.",
                action_priority=ActionPriority.MONITOR,
                confidence_level=0.1,
                research_mode_enabled=True,
                research_report=research_report
            )
        
        logger.info(f"Created fallback research analysis for {len(candidates)} candidates")
        return results
    
    async def get_enhanced_status(self) -> Dict[str, Any]:
        """Get enhanced status including error recovery statistics"""
        base_status = self.get_status()
        
        # Add recovery manager statistics
        error_summary = self.recovery_manager.get_error_summary()
        
        enhanced_status = {
            **base_status,
            "error_recovery": {
                "total_errors_handled": error_summary.get("total_errors", 0),
                "recent_errors": error_summary.get("recent_errors", 0),
                "error_categories": error_summary.get("category_breakdown", {}),
                "circuit_breakers": error_summary.get("circuit_breaker_states", {}),
                "recovery_enabled": True
            },
            "api_client": {
                "openai_configured": self.openai_client is not None,
                "simulation_mode": self.openai_client is None
            }
        }
        
        return enhanced_status

# Export enhanced processor
__all__ = ["EnhancedAILiteScorer"]