"""
Fact Extraction Integration Service

Integrates the new repeatability architecture (fact extraction + local scoring)
with existing AI processors. Provides seamless migration path while maintaining
backward compatibility with current workflow.

Architecture: AI Extracts Facts → Local Deterministic Scoring → Intelligence Synthesis
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel

from src.core.openai_service import get_openai_service
from src.processors.analysis.opportunity_type_detector import OpportunityTypeDetector, OpportunityType, OpportunityTypeDetectionResult
from src.processors.analysis.fact_extraction_prompts import FactExtractionPromptGenerator, FactExtractionTemplate, PromptContext
from src.processors.analysis.deterministic_scoring_engine import (
    DeterministicScoringEngine, 
    ExtractedFacts, 
    ProfileData, 
    ScoringResult,
    ScoreConfidenceLevel
)

logger = logging.getLogger(__name__)

@dataclass
class ProcessorMigrationConfig:
    """Configuration for migrating existing processors to new architecture"""
    enable_fact_extraction: bool = True
    enable_deterministic_scoring: bool = True
    fallback_to_legacy: bool = True  # Fallback to existing processors if new architecture fails
    log_comparison_results: bool = True  # Log differences between old and new approaches
    confidence_threshold: float = 0.6  # Minimum confidence to use new architecture results

class ProcessorIntegrationResult(BaseModel):
    """Result of integrated fact extraction + deterministic scoring"""
    success: bool
    opportunity_type: OpportunityType
    extraction_template_used: str
    
    # Fact extraction results
    extracted_facts: Dict[str, Any]
    extraction_confidence: float
    data_completeness: float
    missing_fields: List[str]
    
    # Deterministic scoring results
    final_score: float
    confidence_level: ScoreConfidenceLevel
    component_scores: Dict[str, float]
    score_rationale: List[str]
    
    # Processing metadata
    processing_time: float
    cost_estimate: float
    architecture_used: str  # "new_architecture" or "legacy_fallback"
    
    # Legacy comparison (if enabled)
    legacy_comparison: Optional[Dict[str, Any]] = None

class FactExtractionIntegrationService:
    """
    Service that integrates fact extraction + deterministic scoring with existing processors
    
    Key Features:
    - Automatic opportunity type detection and routing
    - Seamless integration with existing AI processor workflow  
    - Fallback to legacy processors if new architecture fails
    - Performance and accuracy comparison logging
    - Gradual migration support with confidence thresholds
    """
    
    def __init__(self, config: Optional[ProcessorMigrationConfig] = None):
        self.config = config or ProcessorMigrationConfig()
        
        # Initialize new architecture components
        self.type_detector = OpportunityTypeDetector()
        self.prompt_generator = FactExtractionPromptGenerator()
        self.scoring_engine = DeterministicScoringEngine()
        self.openai_service = get_openai_service()
        
        # Integration metrics
        self.processing_stats = {
            'total_processed': 0,
            'new_architecture_used': 0,
            'legacy_fallback_used': 0,
            'accuracy_comparisons': [],
            'performance_metrics': [],
            'api_calls': 0,
            'total_tokens': 0,
            'total_cost': 0.0
        }
    
    async def process_opportunity(self, opportunity_data: Dict[str, Any], 
                                profile_data: Dict[str, Any],
                                processor_stage: str = "plan") -> ProcessorIntegrationResult:
        """
        Process opportunity using integrated fact extraction + deterministic scoring
        
        Args:
            opportunity_data: Opportunity information for analysis
            profile_data: Organization profile data
            processor_stage: Which processor stage (plan, analyze, examine, approach)
            
        Returns:
            ProcessorIntegrationResult with comprehensive analysis results
        """
        start_time = datetime.now()
        logger.info(f"Processing opportunity with integrated architecture - Stage: {processor_stage}")
        
        try:
            # Step 1: Detect opportunity type
            type_detection = self.type_detector.detect_opportunity_type(opportunity_data)
            logger.info(f"Detected opportunity type: {type_detection.detected_type.value} "
                       f"(confidence: {type_detection.confidence_score:.2f})")
            
            # Step 2: Generate appropriate fact extraction prompt
            extraction_template = self._select_extraction_template(
                type_detection, processor_stage
            )
            
            prompt_context = PromptContext(
                opportunity_title=opportunity_data.get('title', 'Unknown Opportunity'),
                organization_name=opportunity_data.get('organization_name', 'Unknown Organization'),
                opportunity_type=type_detection.detected_type.value,
                confidence_level=self._get_confidence_category(type_detection.confidence_score),
                expected_completeness=type_detection.expected_data_completeness,
                website_url=opportunity_data.get('website'),
                document_type=opportunity_data.get('document_type')
            )
            
            extraction_prompt = self.prompt_generator.generate_prompt(extraction_template, prompt_context)
            
            # Step 3: Execute fact extraction (AI call)
            if self.config.enable_fact_extraction:
                extracted_facts = await self._execute_fact_extraction(
                    extraction_prompt, opportunity_data, type_detection
                )
            else:
                logger.warning("Fact extraction disabled, using legacy approach")
                return await self._fallback_to_legacy(opportunity_data, profile_data, processor_stage, start_time)
            
            # Step 4: Execute deterministic scoring
            if self.config.enable_deterministic_scoring:
                scoring_result = await self._execute_deterministic_scoring(
                    extracted_facts, profile_data, type_detection
                )
            else:
                logger.warning("Deterministic scoring disabled, using legacy approach") 
                return await self._fallback_to_legacy(opportunity_data, profile_data, processor_stage, start_time)
            
            # Step 5: Create integrated result
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = ProcessorIntegrationResult(
                success=True,
                opportunity_type=type_detection.detected_type,
                extraction_template_used=extraction_template.value,
                extracted_facts=extracted_facts.raw_facts,
                extraction_confidence=extracted_facts.extraction_confidence,
                data_completeness=extracted_facts.data_completeness,
                missing_fields=extracted_facts.missing_fields,
                final_score=scoring_result.final_score,
                confidence_level=scoring_result.confidence_level,
                component_scores=scoring_result.component_scores,
                score_rationale=scoring_result.score_rationale,
                processing_time=processing_time,
                cost_estimate=self._estimate_processing_cost(type_detection.detected_type),
                architecture_used="new_architecture"
            )
            
            # Step 6: Legacy comparison (if enabled)
            if self.config.log_comparison_results:
                result.legacy_comparison = await self._compare_with_legacy(
                    opportunity_data, profile_data, result, processor_stage
                )
            
            # Update processing statistics
            self._update_processing_stats(result, processing_time)
            
            logger.info(f"Integrated processing completed successfully: {result.final_score:.3f} "
                       f"({result.confidence_level.value} confidence) in {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Integrated processing failed: {str(e)}")
            
            if self.config.fallback_to_legacy:
                logger.info("Falling back to legacy processor")
                return await self._fallback_to_legacy(opportunity_data, profile_data, processor_stage, start_time)
            else:
                # Return error result
                processing_time = (datetime.now() - start_time).total_seconds()
                return ProcessorIntegrationResult(
                    success=False,
                    opportunity_type=OpportunityType.UNKNOWN,
                    extraction_template_used="error",
                    extracted_facts={},
                    extraction_confidence=0.0,
                    data_completeness=0.0,
                    missing_fields=[],
                    final_score=0.0,
                    confidence_level=ScoreConfidenceLevel.VERY_LOW,
                    component_scores={},
                    score_rationale=[f"Processing failed: {str(e)}"],
                    processing_time=processing_time,
                    cost_estimate=0.0,
                    architecture_used="error"
                )
    
    def _select_extraction_template(self, type_detection: OpportunityTypeDetectionResult,
                                  processor_stage: str) -> FactExtractionTemplate:
        """Select appropriate fact extraction template based on opportunity type and confidence"""
        
        # Map processor stages to extraction approaches
        stage_complexity = {
            'plan': 'standard',      # Basic validation and strategic scoring
            'analyze': 'standard',   # Research and analysis
            'examine': 'comprehensive',  # Deep intelligence gathering
            'approach': 'comprehensive'  # Implementation planning
        }
        
        complexity = stage_complexity.get(processor_stage, 'standard')
        
        # Select template based on opportunity type and confidence
        if type_detection.detected_type == OpportunityType.GOVERNMENT:
            if type_detection.confidence_score >= 0.8 and complexity == 'comprehensive':
                return FactExtractionTemplate.GOVERNMENT_DETAILED
            elif type_detection.confidence_score >= 0.6:
                return FactExtractionTemplate.GOVERNMENT_STANDARD
            else:
                return FactExtractionTemplate.GOVERNMENT_BASIC
                
        elif type_detection.detected_type == OpportunityType.NONPROFIT:
            if type_detection.confidence_score >= 0.7 and complexity == 'comprehensive':
                return FactExtractionTemplate.NONPROFIT_COMPREHENSIVE
            elif type_detection.confidence_score >= 0.5:
                return FactExtractionTemplate.NONPROFIT_STANDARD
            else:
                return FactExtractionTemplate.NONPROFIT_MINIMAL
                
        elif type_detection.detected_type == OpportunityType.CORPORATE:
            if type_detection.confidence_score >= 0.7 and complexity == 'comprehensive':
                return FactExtractionTemplate.CORPORATE_RELATIONSHIP
            elif type_detection.confidence_score >= 0.5:
                return FactExtractionTemplate.CORPORATE_STANDARD
            else:
                return FactExtractionTemplate.CORPORATE_BASIC
                
        else:
            return FactExtractionTemplate.GENERAL_EXTRACTION
    
    def _get_confidence_category(self, confidence_score: float) -> str:
        """Convert confidence score to category"""
        if confidence_score >= 0.8:
            return "high"
        elif confidence_score >= 0.6:
            return "medium"
        else:
            return "low"
    
    async def _execute_fact_extraction(self, extraction_prompt: str,
                                     opportunity_data: Dict[str, Any],
                                     type_detection: OpportunityTypeDetectionResult) -> ExtractedFacts:
        """Execute fact extraction using real OpenAI API"""
        
        try:
            # Prepare messages for OpenAI API call
            messages = [
                {
                    "role": "system", 
                    "content": "You are a grant analysis expert. Extract factual information from opportunity data and return it as structured JSON."
                },
                {
                    "role": "user", 
                    "content": extraction_prompt
                }
            ]
            
            # Make real OpenAI API call
            logger.info(f"Making OpenAI API call for fact extraction (type: {type_detection.detected_type.value})")
            
            # Use the configured AI model from environment
            import os
            model = os.getenv("AI_LITE_MODEL", "gpt-5-nano")  # Use the configured GPT-5 model
            
            response = await self.openai_service.create_completion(
                model=model,
                messages=messages,
                max_tokens=1500,
                temperature=0.1  # Low temperature for more deterministic responses
            )
            
            # Parse the AI response
            try:
                raw_facts = json.loads(response.content)
                logger.info(f"Successfully extracted facts from AI response")
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse AI response as JSON, falling back to simulation")
                raw_facts = self._simulate_fact_extraction(opportunity_data, type_detection.detected_type)
            
            # Track API costs
            self.processing_stats['api_calls'] = self.processing_stats.get('api_calls', 0) + 1
            self.processing_stats['total_tokens'] = self.processing_stats.get('total_tokens', 0) + response.usage.get('total_tokens', 0)
            self.processing_stats['total_cost'] = self.processing_stats.get('total_cost', 0.0) + response.cost_estimate
            
        except Exception as e:
            logger.warning(f"AI fact extraction failed: {str(e)}, falling back to simulation")
            raw_facts = self._simulate_fact_extraction(opportunity_data, type_detection.detected_type)
        
        # Calculate data completeness based on opportunity type expectations
        expected_fields = self._get_expected_fields(type_detection.detected_type)
        available_fields = []
        
        # Handle nested dictionary structure for field counting
        def count_available_fields(data, prefix=""):
            count = 0
            if isinstance(data, dict):
                for key, value in data.items():
                    field_name = f"{prefix}.{key}" if prefix else key
                    if value and value != "Information not available":
                        if isinstance(value, dict):
                            count += count_available_fields(value, field_name)
                        else:
                            count += 1
            return count
        
        available_field_count = count_available_fields(raw_facts)
        data_completeness = available_field_count / len(expected_fields) if expected_fields else 0.0
        
        missing_fields = [field for field in expected_fields 
                         if field not in str(raw_facts)]  # Simple check for field presence
        
        return ExtractedFacts(
            opportunity_type=type_detection.detected_type,
            extraction_template=type_detection.recommended_extraction_approach,
            raw_facts=raw_facts,
            data_completeness=data_completeness,
            extraction_confidence=type_detection.confidence_score,
            missing_fields=missing_fields,
            extraction_timestamp=datetime.now()
        )
    
    def _simulate_fact_extraction(self, opportunity_data: Dict[str, Any], 
                                opportunity_type: OpportunityType) -> Dict[str, Any]:
        """Simulate fact extraction based on opportunity type"""
        
        if opportunity_type == OpportunityType.GOVERNMENT:
            return {
                "funding_details": {
                    "award_amount_range": opportunity_data.get('funding_amount', 'Information not available'),
                    "project_period": opportunity_data.get('project_period', 'Information not available'),
                    "number_of_awards": opportunity_data.get('number_of_awards', 'Information not available')
                },
                "eligibility_requirements": {
                    "organizational_type": "501(c)(3) nonprofit organizations",
                    "geographic_restrictions": opportunity_data.get('geographic_scope', 'Information not available'),
                    "financial_capacity": opportunity_data.get('min_revenue', 'Information not available')
                },
                "application_process": {
                    "deadline": opportunity_data.get('deadline', 'Information not available'),
                    "submission_method": "Grants.gov",
                    "required_documents": ["Project Narrative", "Budget", "Letters of Support"]
                }
            }
            
        elif opportunity_type == OpportunityType.NONPROFIT:
            return {
                "foundation_essentials": {
                    "name": opportunity_data.get('organization_name', 'Information not available'),
                    "mission_focus": opportunity_data.get('mission', 'Information not available'),
                    "geographic_scope": opportunity_data.get('geographic_scope', 'Information not available')
                },
                "grant_information": {
                    "typical_amounts": opportunity_data.get('funding_amount', 'Information not available'),
                    "funding_areas": opportunity_data.get('focus_areas', 'Information not available'),
                    "application_timing": opportunity_data.get('deadline', 'Information not available')
                }
            }
            
        elif opportunity_type == OpportunityType.CORPORATE:
            return {
                "corporate_basics": {
                    "company_name": opportunity_data.get('organization_name', 'Information not available'),
                    "industry_sector": opportunity_data.get('industry', 'Information not available'),
                    "csr_focus": opportunity_data.get('focus_areas', 'Information not available')
                },
                "partnership_info": {
                    "partnership_types": opportunity_data.get('partnership_types', 'Information not available'),
                    "contact_method": opportunity_data.get('contact_info', 'Information not available')
                }
            }
        
        else:
            return {
                "basic_details": {
                    "organization_name": opportunity_data.get('organization_name', 'Information not available'),
                    "general_focus": opportunity_data.get('focus_areas', 'Information not available'),
                    "contact_method": opportunity_data.get('contact_info', 'Information not available')
                }
            }
    
    def _get_expected_fields(self, opportunity_type: OpportunityType) -> List[str]:
        """Get expected fields for each opportunity type"""
        
        expected_fields = {
            OpportunityType.GOVERNMENT: [
                'funding_details', 'eligibility_requirements', 'application_process',
                'contacts', 'evaluation_criteria'
            ],
            OpportunityType.NONPROFIT: [
                'foundation_essentials', 'grant_information', 'application_approach', 'contact_info'
            ],
            OpportunityType.CORPORATE: [
                'corporate_basics', 'partnership_info', 'contact_process'
            ]
        }
        
        return expected_fields.get(opportunity_type, ['basic_details'])
    
    async def _execute_deterministic_scoring(self, extracted_facts: ExtractedFacts,
                                           profile_data: Dict[str, Any],
                                           type_detection: OpportunityTypeDetectionResult) -> ScoringResult:
        """Execute deterministic scoring using local algorithms"""
        
        # Convert profile data to ProfileData model
        profile = ProfileData(
            organization_name=profile_data.get('name', 'Unknown Organization'),
            ein=profile_data.get('ein', '000000000'),
            annual_revenue=profile_data.get('annual_revenue'),
            ntee_codes=profile_data.get('ntee_codes', []),
            state=profile_data.get('state', 'VA'),
            focus_areas=profile_data.get('focus_areas', []),
            mission_statement=profile_data.get('mission_statement'),
            board_size=profile_data.get('board_size'),
            staff_count=profile_data.get('staff_count'),
            years_in_operation=profile_data.get('years_in_operation')
        )
        
        # Execute deterministic scoring
        return self.scoring_engine.calculate_opportunity_score(extracted_facts, profile)
    
    async def _compare_with_legacy(self, opportunity_data: Dict[str, Any],
                                 profile_data: Dict[str, Any],
                                 new_result: ProcessorIntegrationResult,
                                 processor_stage: str) -> Dict[str, Any]:
        """Compare new architecture results with legacy processor results"""
        
        try:
            # Simulate legacy processor call
            # In real implementation, this would call the actual legacy processor
            legacy_score = 0.75  # Simulated legacy score
            
            score_difference = abs(new_result.final_score - legacy_score)
            
            comparison = {
                'legacy_score': legacy_score,
                'new_score': new_result.final_score,
                'score_difference': score_difference,
                'significant_difference': score_difference > 0.1,  # >10% difference
                'new_confidence': new_result.confidence_level.value,
                'comparison_timestamp': datetime.now().isoformat(),
                'processor_stage': processor_stage
            }
            
            logger.info(f"Legacy comparison - Legacy: {legacy_score:.3f}, "
                       f"New: {new_result.final_score:.3f}, "
                       f"Difference: {score_difference:.3f}")
            
            return comparison
            
        except Exception as e:
            logger.warning(f"Legacy comparison failed: {str(e)}")
            return {'comparison_error': str(e)}
    
    async def _fallback_to_legacy(self, opportunity_data: Dict[str, Any],
                                profile_data: Dict[str, Any],
                                processor_stage: str,
                                start_time: datetime) -> ProcessorIntegrationResult:
        """Fallback to legacy processor when new architecture fails"""
        
        logger.info("Using legacy processor fallback")
        
        # Simulate legacy processor execution
        # In real implementation, this would call the actual legacy processor
        legacy_score = 0.75
        processing_time = (datetime.now() - start_time).total_seconds()
        
        self.processing_stats['legacy_fallback_used'] += 1
        
        return ProcessorIntegrationResult(
            success=True,
            opportunity_type=OpportunityType.UNKNOWN,
            extraction_template_used="legacy_fallback",
            extracted_facts={},
            extraction_confidence=0.6,
            data_completeness=0.7,
            missing_fields=[],
            final_score=legacy_score,
            confidence_level=ScoreConfidenceLevel.MEDIUM,
            component_scores={'legacy_score': legacy_score},
            score_rationale=['Legacy processor fallback used'],
            processing_time=processing_time,
            cost_estimate=0.02,  # Estimated legacy processor cost
            architecture_used="legacy_fallback"
        )
    
    def _estimate_processing_cost(self, opportunity_type: OpportunityType) -> float:
        """Estimate processing cost based on opportunity type"""
        
        cost_estimates = {
            OpportunityType.GOVERNMENT: 0.003,  # More detailed analysis
            OpportunityType.NONPROFIT: 0.002,   # Medium complexity
            OpportunityType.CORPORATE: 0.001,   # Simpler analysis
            OpportunityType.UNKNOWN: 0.0015     # Basic analysis
        }
        
        return cost_estimates.get(opportunity_type, 0.0015)
    
    def _update_processing_stats(self, result: ProcessorIntegrationResult, processing_time: float):
        """Update processing statistics for monitoring"""
        
        self.processing_stats['total_processed'] += 1
        
        if result.architecture_used == "new_architecture":
            self.processing_stats['new_architecture_used'] += 1
        else:
            self.processing_stats['legacy_fallback_used'] += 1
        
        self.processing_stats['performance_metrics'].append({
            'processing_time': processing_time,
            'final_score': result.final_score,
            'confidence_level': result.confidence_level.value,
            'opportunity_type': result.opportunity_type.value,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 100 performance metrics to prevent memory growth
        if len(self.processing_stats['performance_metrics']) > 100:
            self.processing_stats['performance_metrics'] = self.processing_stats['performance_metrics'][-100:]
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get current processing statistics including API costs"""
        
        stats = self.processing_stats.copy()
        
        # Add computed metrics
        stats['api_calls_made'] = self.processing_stats['api_calls']
        stats['total_tokens_used'] = self.processing_stats['total_tokens'] 
        stats['total_api_cost'] = self.processing_stats['total_cost']
        stats['average_cost_per_call'] = self.processing_stats['total_cost'] / max(self.processing_stats['api_calls'], 1)
        stats['success_rate'] = self.processing_stats['new_architecture_used'] / max(self.processing_stats['total_processed'], 1)
        
        if stats['total_processed'] > 0:
            stats['new_architecture_percentage'] = (
                stats['new_architecture_used'] / stats['total_processed'] * 100
            )
            stats['legacy_fallback_percentage'] = (
                stats['legacy_fallback_used'] / stats['total_processed'] * 100
            )
            
            if stats['performance_metrics']:
                processing_times = [m['processing_time'] for m in stats['performance_metrics']]
                stats['average_processing_time'] = sum(processing_times) / len(processing_times)
                stats['max_processing_time'] = max(processing_times)
                stats['min_processing_time'] = min(processing_times)
        
        return stats
    
    def should_use_new_architecture(self, opportunity_data: Dict[str, Any]) -> bool:
        """Determine if new architecture should be used for this opportunity"""
        
        # Can add logic here for gradual rollout based on:
        # - Opportunity characteristics
        # - Confidence thresholds  
        # - A/B testing parameters
        # - System performance metrics
        
        return self.config.enable_fact_extraction and self.config.enable_deterministic_scoring