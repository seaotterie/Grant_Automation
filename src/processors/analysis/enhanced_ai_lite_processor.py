"""
Enhanced AI-Lite Processor with Repeatability Architecture

Updated version of the AI-Lite processor that integrates with the new fact-extraction
+ deterministic scoring architecture for improved repeatability while maintaining
backward compatibility with existing systems.

Architecture: Fact Extraction (AI) → Deterministic Scoring (Local) → Intelligence Synthesis
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.processors.analysis.fact_extraction_integration_service import (
    FactExtractionIntegrationService, 
    ProcessorMigrationConfig,
    ProcessorIntegrationResult
)
from src.processors.analysis.opportunity_type_detector import OpportunityType
from src.processors.analysis.deterministic_scoring_engine import ScoreConfidenceLevel

logger = logging.getLogger(__name__)

class ProcessingMode(str, Enum):
    """Processing mode selection"""
    NEW_ARCHITECTURE = "new_architecture"      # Fact extraction + deterministic scoring
    LEGACY_ARCHITECTURE = "legacy_architecture"  # Original AI-based scoring
    HYBRID_COMPARISON = "hybrid_comparison"    # Run both and compare results

class EnhancedAILiteResult(BaseModel):
    """Enhanced result model that supports both architectures"""
    
    # Core results (compatible with both architectures)
    success: bool
    opportunity_id: str
    final_score: float = Field(..., ge=0.0, le=1.0)
    confidence_level: str
    processing_time: float
    cost_estimate: float
    
    # Strategic components
    mission_alignment_score: float = Field(..., ge=0.0, le=1.0)
    strategic_value: str
    strategic_rationale: str
    eligibility_status: str
    discovery_track: str
    
    # Risk assessment
    risk_factors: List[str] = Field(default_factory=list)
    risk_mitigation: List[str] = Field(default_factory=list)
    competitive_pressure: str = "unknown"
    
    # New architecture specific (when using fact extraction)
    architecture_used: str = "legacy_architecture"
    opportunity_type: Optional[str] = None
    extraction_template: Optional[str] = None
    data_completeness: Optional[float] = None
    component_scores: Dict[str, float] = Field(default_factory=dict)
    score_rationale: List[str] = Field(default_factory=list)
    
    # Legacy comparison (when enabled)
    architecture_comparison: Optional[Dict[str, Any]] = None

class EnhancedAILiteProcessor(BaseProcessor):
    """
    Enhanced AI-Lite processor with repeatability architecture integration
    
    Key Features:
    - Seamless integration between new and legacy architectures
    - Automatic opportunity type detection and routing
    - Deterministic scoring with fact extraction for improved repeatability
    - Backward compatibility with existing systems
    - Performance comparison and gradual migration support
    """
    
    def __init__(self, processing_mode: ProcessingMode = ProcessingMode.NEW_ARCHITECTURE,
                 migration_config: Optional[ProcessorMigrationConfig] = None):
        
        # Initialize base processor
        metadata = ProcessorMetadata(
            name="enhanced_ai_lite_processor",
            description="AI-Lite processor with repeatability architecture integration",
            version="2.0.0",
            dependencies=["openai_service", "fact_extraction_integration_service"],
            estimated_duration=30,
            requires_network=True,
            requires_api_key=True,
            can_run_parallel=True,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        self.processing_mode = processing_mode
        self.migration_config = migration_config or ProcessorMigrationConfig()
        
        # Initialize integration service for new architecture
        if processing_mode in [ProcessingMode.NEW_ARCHITECTURE, ProcessingMode.HYBRID_COMPARISON]:
            self.integration_service = FactExtractionIntegrationService(self.migration_config)
        else:
            self.integration_service = None
        
        # Processing statistics
        self.processing_stats = {
            'total_requests': 0,
            'new_architecture_used': 0,
            'legacy_architecture_used': 0,
            'hybrid_comparisons': 0,
            'significant_differences': 0
        }
    
    async def execute(self, request_data: Dict[str, Any]) -> EnhancedAILiteResult:
        """
        Execute enhanced AI-Lite processing with architecture selection
        
        Args:
            request_data: Processing request with opportunity and profile data
            
        Returns:
            EnhancedAILiteResult with comprehensive analysis results
        """
        start_time = datetime.now()
        opportunity_data = request_data.get('opportunity', {})
        profile_data = request_data.get('profile', {})
        
        opportunity_id = opportunity_data.get('opportunity_id', 'unknown')
        logger.info(f"Enhanced AI-Lite processing: {opportunity_id} (mode: {self.processing_mode.value})")
        
        self.processing_stats['total_requests'] += 1
        
        try:
            if self.processing_mode == ProcessingMode.NEW_ARCHITECTURE:
                return await self._process_new_architecture(opportunity_data, profile_data, start_time)
                
            elif self.processing_mode == ProcessingMode.LEGACY_ARCHITECTURE:
                return await self._process_legacy_architecture(opportunity_data, profile_data, start_time)
                
            elif self.processing_mode == ProcessingMode.HYBRID_COMPARISON:
                return await self._process_hybrid_comparison(opportunity_data, profile_data, start_time)
                
            else:
                raise ValueError(f"Unknown processing mode: {self.processing_mode}")
                
        except Exception as e:
            logger.error(f"Enhanced AI-Lite processing failed: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return EnhancedAILiteResult(
                success=False,
                opportunity_id=opportunity_id,
                final_score=0.0,
                confidence_level="very_low",
                processing_time=processing_time,
                cost_estimate=0.0,
                mission_alignment_score=0.0,
                strategic_value="minimal",
                strategic_rationale=f"Processing failed: {str(e)}",
                eligibility_status="unknown",
                discovery_track="unknown",
                architecture_used="error"
            )
    
    async def _process_new_architecture(self, opportunity_data: Dict[str, Any],
                                      profile_data: Dict[str, Any],
                                      start_time: datetime) -> EnhancedAILiteResult:
        """Process using new fact extraction + deterministic scoring architecture"""
        
        logger.info("Using new repeatability architecture (fact extraction + deterministic scoring)")
        self.processing_stats['new_architecture_used'] += 1
        
        # Execute integrated processing
        integration_result = await self.integration_service.process_opportunity(
            opportunity_data, profile_data, "plan"  # AI-Lite is typically used in PLAN stage
        )
        
        # Convert integration result to enhanced AI-Lite result format
        result = await self._convert_integration_result(integration_result, start_time)
        result.architecture_used = "new_architecture"
        
        logger.info(f"New architecture processing completed: {result.final_score:.3f} "
                   f"({result.confidence_level} confidence)")
        
        return result
    
    async def _process_legacy_architecture(self, opportunity_data: Dict[str, Any],
                                         profile_data: Dict[str, Any],
                                         start_time: datetime) -> EnhancedAILiteResult:
        """Process using legacy AI-based scoring architecture"""
        
        logger.info("Using legacy AI-based scoring architecture")
        self.processing_stats['legacy_architecture_used'] += 1
        
        # Simulate legacy AI-Lite processing
        # In real implementation, this would call the original AI-Lite processor
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Simulate legacy scoring results
        legacy_score = 0.75  # Typical AI-generated score
        
        return EnhancedAILiteResult(
            success=True,
            opportunity_id=opportunity_data.get('opportunity_id', 'unknown'),
            final_score=legacy_score,
            confidence_level="medium",
            processing_time=processing_time,
            cost_estimate=0.004,  # Legacy AI-Lite cost
            mission_alignment_score=0.8,
            strategic_value="high",
            strategic_rationale="Strategic alignment and mission compatibility identified through AI analysis",
            eligibility_status="eligible",
            discovery_track="government",
            risk_factors=["Competition risk: medium", "Technical requirements: low"],
            competitive_pressure="medium",
            architecture_used="legacy_architecture"
        )
    
    async def _process_hybrid_comparison(self, opportunity_data: Dict[str, Any],
                                       profile_data: Dict[str, Any],
                                       start_time: datetime) -> EnhancedAILiteResult:
        """Process using both architectures and compare results"""
        
        logger.info("Using hybrid comparison mode (both architectures)")
        self.processing_stats['hybrid_comparisons'] += 1
        
        # Process with new architecture
        new_result = await self._process_new_architecture(opportunity_data, profile_data, start_time)
        
        # Process with legacy architecture  
        legacy_result = await self._process_legacy_architecture(opportunity_data, profile_data, start_time)
        
        # Compare results
        score_difference = abs(new_result.final_score - legacy_result.final_score)
        significant_difference = score_difference > 0.1  # >10% difference
        
        if significant_difference:
            self.processing_stats['significant_differences'] += 1
            logger.warning(f"Significant scoring difference detected: "
                          f"New: {new_result.final_score:.3f}, "
                          f"Legacy: {legacy_result.final_score:.3f}, "
                          f"Difference: {score_difference:.3f}")
        
        # Create comparison data
        comparison_data = {
            'new_architecture': {
                'score': new_result.final_score,
                'confidence': new_result.confidence_level,
                'processing_time': new_result.processing_time,
                'opportunity_type': new_result.opportunity_type,
                'data_completeness': new_result.data_completeness
            },
            'legacy_architecture': {
                'score': legacy_result.final_score,
                'confidence': legacy_result.confidence_level,
                'processing_time': legacy_result.processing_time
            },
            'comparison': {
                'score_difference': score_difference,
                'significant_difference': significant_difference,
                'recommended_architecture': 'new' if new_result.confidence_level != 'very_low' else 'legacy'
            }
        }
        
        # Return new architecture result with comparison data
        new_result.architecture_used = "hybrid_comparison"
        new_result.architecture_comparison = comparison_data
        
        return new_result
    
    async def _convert_integration_result(self, integration_result: ProcessorIntegrationResult,
                                        start_time: datetime) -> EnhancedAILiteResult:
        """Convert integration service result to enhanced AI-Lite result format"""
        
        # Map confidence levels
        confidence_mapping = {
            ScoreConfidenceLevel.HIGH: "high",
            ScoreConfidenceLevel.MEDIUM: "medium", 
            ScoreConfidenceLevel.LOW: "low",
            ScoreConfidenceLevel.VERY_LOW: "very_low"
        }
        
        # Map opportunity types to discovery tracks
        track_mapping = {
            OpportunityType.GOVERNMENT: "government",
            OpportunityType.NONPROFIT: "nonprofit",
            OpportunityType.CORPORATE: "commercial",
            OpportunityType.UNKNOWN: "unknown"
        }
        
        # Extract strategic components from scoring rationale
        strategic_value = self._determine_strategic_value(integration_result.final_score)
        eligibility_status = self._determine_eligibility_status(integration_result.score_rationale)
        
        return EnhancedAILiteResult(
            success=integration_result.success,
            opportunity_id=integration_result.extracted_facts.get('opportunity_id', 'unknown'),
            final_score=integration_result.final_score,
            confidence_level=confidence_mapping.get(integration_result.confidence_level, "low"),
            processing_time=integration_result.processing_time,
            cost_estimate=integration_result.cost_estimate,
            mission_alignment_score=integration_result.component_scores.get('strategic_alignment', 0.5),
            strategic_value=strategic_value,
            strategic_rationale=" | ".join(integration_result.score_rationale[:3]),  # First 3 rationale items
            eligibility_status=eligibility_status,
            discovery_track=track_mapping.get(integration_result.opportunity_type, "unknown"),
            risk_factors=self._extract_risk_factors(integration_result.score_rationale),
            competitive_pressure=self._assess_competitive_pressure(integration_result.component_scores),
            opportunity_type=integration_result.opportunity_type.value,
            extraction_template=integration_result.extraction_template_used,
            data_completeness=integration_result.data_completeness,
            component_scores=integration_result.component_scores,
            score_rationale=integration_result.score_rationale
        )
    
    def _determine_strategic_value(self, final_score: float) -> str:
        """Determine strategic value category based on final score"""
        if final_score >= 0.85:
            return "exceptional"
        elif final_score >= 0.70:
            return "high"
        elif final_score >= 0.55:
            return "medium"
        elif final_score >= 0.40:
            return "low"
        else:
            return "minimal"
    
    def _determine_eligibility_status(self, score_rationale: List[str]) -> str:
        """Determine eligibility status from scoring rationale"""
        rationale_text = " ".join(score_rationale).lower()
        
        if "eligible" in rationale_text or "compliance" in rationale_text:
            return "eligible"
        elif "ineligible" in rationale_text or "not eligible" in rationale_text:
            return "ineligible"
        elif "conditional" in rationale_text:
            return "conditional"
        else:
            return "unknown"
    
    def _extract_risk_factors(self, score_rationale: List[str]) -> List[str]:
        """Extract risk factors from scoring rationale"""
        risk_keywords = ['competition', 'technical', 'geographic', 'capacity', 'timeline', 'compliance']
        risk_factors = []
        
        for rationale in score_rationale:
            for keyword in risk_keywords:
                if keyword in rationale.lower():
                    risk_factors.append(f"{keyword.title()} risk identified")
        
        return risk_factors[:3]  # Limit to top 3 risk factors
    
    def _assess_competitive_pressure(self, component_scores: Dict[str, float]) -> str:
        """Assess competitive pressure based on component scores"""
        # Use geographic and strategic alignment scores as proxy for competition
        geo_score = component_scores.get('geographic_advantage', 0.5)
        strategic_score = component_scores.get('strategic_alignment', 0.5)
        
        avg_advantage = (geo_score + strategic_score) / 2
        
        if avg_advantage >= 0.8:
            return "low"      # High advantage = low competition
        elif avg_advantage >= 0.6:
            return "medium"
        else:
            return "high"     # Low advantage = high competition
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        
        stats = self.processing_stats.copy()
        
        if stats['total_requests'] > 0:
            stats['new_architecture_percentage'] = (
                stats['new_architecture_used'] / stats['total_requests'] * 100
            )
            stats['legacy_architecture_percentage'] = (
                stats['legacy_architecture_used'] / stats['total_requests'] * 100
            )
            stats['hybrid_comparison_percentage'] = (
                stats['hybrid_comparisons'] / stats['total_requests'] * 100
            )
            
            if stats['hybrid_comparisons'] > 0:
                stats['significant_difference_rate'] = (
                    stats['significant_differences'] / stats['hybrid_comparisons'] * 100
                )
        
        # Add integration service stats if available
        if self.integration_service:
            integration_stats = self.integration_service.get_processing_statistics()
            stats['integration_service_stats'] = integration_stats
        
        return stats
    
    def set_processing_mode(self, mode: ProcessingMode):
        """Dynamically change processing mode"""
        old_mode = self.processing_mode
        self.processing_mode = mode
        
        logger.info(f"Processing mode changed from {old_mode.value} to {mode.value}")
        
        # Initialize integration service if switching to new architecture modes
        if mode in [ProcessingMode.NEW_ARCHITECTURE, ProcessingMode.HYBRID_COMPARISON] and not self.integration_service:
            self.integration_service = FactExtractionIntegrationService(self.migration_config)
    
    async def validate_repeatability(self, opportunity_data: Dict[str, Any], 
                                   profile_data: Dict[str, Any],
                                   test_runs: int = 3) -> Dict[str, Any]:
        """
        Validate repeatability by running the same analysis multiple times
        
        Args:
            opportunity_data: Opportunity to test
            profile_data: Profile to test with
            test_runs: Number of test runs to perform
            
        Returns:
            Repeatability validation results
        """
        logger.info(f"Starting repeatability validation with {test_runs} test runs")
        
        if self.processing_mode == ProcessingMode.LEGACY_ARCHITECTURE:
            logger.warning("Legacy architecture may show variability due to AI non-determinism")
        
        results = []
        for run in range(test_runs):
            logger.info(f"Repeatability test run {run + 1}/{test_runs}")
            result = await self.execute({'opportunity': opportunity_data, 'profile': profile_data})
            results.append({
                'run': run + 1,
                'final_score': result.final_score,
                'confidence_level': result.confidence_level,
                'processing_time': result.processing_time,
                'architecture_used': result.architecture_used
            })
        
        # Analyze repeatability
        scores = [r['final_score'] for r in results]
        score_variance = self._calculate_variance(scores)
        max_difference = max(scores) - min(scores)
        
        repeatability_analysis = {
            'test_runs': test_runs,
            'results': results,
            'score_statistics': {
                'mean_score': sum(scores) / len(scores),
                'min_score': min(scores),
                'max_score': max(scores),
                'score_variance': score_variance,
                'max_difference': max_difference
            },
            'repeatability_assessment': {
                'is_repeatable': max_difference < 0.05,  # <5% variation
                'repeatability_quality': self._assess_repeatability_quality(max_difference),
                'architecture_consistent': len(set(r['architecture_used'] for r in results)) == 1
            },
            'processing_mode': self.processing_mode.value
        }
        
        logger.info(f"Repeatability validation completed: "
                   f"Max difference: {max_difference:.3f}, "
                   f"Quality: {repeatability_analysis['repeatability_assessment']['repeatability_quality']}")
        
        return repeatability_analysis
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values"""
        if len(values) <= 1:
            return 0.0
        
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)
    
    def _assess_repeatability_quality(self, max_difference: float) -> str:
        """Assess repeatability quality based on maximum difference"""
        if max_difference < 0.01:  # <1% difference
            return "excellent"
        elif max_difference < 0.05:  # <5% difference  
            return "good"
        elif max_difference < 0.10:  # <10% difference
            return "fair"
        else:
            return "poor"