#!/usr/bin/env python3
"""
Unified Scorer Interface
Standardized interface for all scoring components in the grant research platform

This module provides:
1. Common scoring interface with standardized methods
2. Scorer factory pattern for dynamic scorer selection
3. Cross-scorer validation and consistency checking
4. Performance monitoring and metrics collection
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
import hashlib

logger = logging.getLogger(__name__)


class ScorerType(Enum):
    """Types of scorers in the system"""
    DISCOVERY = "discovery"
    SUCCESS = "success" 
    GOVERNMENT = "government"
    AI_LITE = "ai_lite"
    AI_HEAVY = "ai_heavy"
    FINANCIAL = "financial"
    NETWORK = "network"


class WorkflowStage(Enum):
    """Workflow stages where scorers operate"""
    DISCOVER = "discover"
    PLAN = "plan"
    ANALYZE = "analyze"
    EXAMINE = "examine"
    APPROACH = "approach"


@dataclass
class ScoringDimension:
    """Standard scoring dimension with weight and calculation method"""
    name: str
    weight: float
    description: str
    calculation_method: str
    data_requirements: List[str]


@dataclass 
class ScoringResult:
    """Standardized scoring result across all scorer types"""
    overall_score: float  # Always 0.0-1.0 range
    dimension_scores: Dict[str, float]  # Individual dimension scores
    confidence_level: float  # 0.0-1.0 confidence in the score
    metadata: Dict[str, Any]  # Additional scoring metadata
    scorer_type: ScorerType  # Which scorer generated this result
    workflow_stage: WorkflowStage  # Which stage this applies to
    scoring_timestamp: datetime  # When the score was calculated
    processing_time_ms: float  # How long scoring took
    data_quality_score: float  # Quality of input data (0.0-1.0)
    
    @property
    def is_high_confidence(self) -> bool:
        """Whether this is a high-confidence result"""
        return self.confidence_level >= 0.8
    
    @property
    def requires_validation(self) -> bool:
        """Whether this result requires additional validation"""
        return self.confidence_level < 0.6 or self.data_quality_score < 0.5


@dataclass
class ScoringContext:
    """Context information for scoring operations"""
    profile_id: str
    opportunity_id: str
    entity_type: str  # nonprofit, government, foundation, etc.
    workflow_stage: WorkflowStage
    enhanced_data: Optional[Dict[str, Any]] = None
    cache_key: Optional[str] = None
    priority_level: str = "standard"  # standard, high, critical


class UnifiedScorerInterface(ABC):
    """Abstract base class for all scorers in the platform"""
    
    def __init__(self):
        self.scorer_type: ScorerType = None
        self.supported_stages: List[WorkflowStage] = []
        self.scoring_dimensions: List[ScoringDimension] = []
        self.performance_metrics: Dict[str, Any] = {
            'total_scores': 0,
            'avg_processing_time': 0.0,
            'cache_hit_rate': 0.0,
            'error_rate': 0.0
        }
        
        # Enhanced caching integration
        self._cache_enabled = True
        self._cache_ttl_hours = 24  # Default TTL for this scorer type
    
    @abstractmethod
    async def score(self, 
                   opportunity_data: Dict[str, Any],
                   profile_data: Dict[str, Any], 
                   context: ScoringContext) -> ScoringResult:
        """
        Score an opportunity against a profile
        
        Args:
            opportunity_data: Opportunity information to score
            profile_data: Organization profile to score against
            context: Scoring context and metadata
            
        Returns:
            ScoringResult with standardized 0-1 score and metadata
        """
        pass
    
    @abstractmethod
    def get_scoring_dimensions(self) -> List[ScoringDimension]:
        """Get the scoring dimensions used by this scorer"""
        pass
    
    @abstractmethod 
    def validate_input_data(self, 
                          opportunity_data: Dict[str, Any],
                          profile_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that required data is present for scoring
        
        Returns:
            (is_valid, list_of_missing_fields)
        """
        pass
    
    async def batch_score(self,
                         opportunities: List[Dict[str, Any]],
                         profile_data: Dict[str, Any],
                         context: ScoringContext) -> List[ScoringResult]:
        """
        Score multiple opportunities in batch for efficiency
        
        Args:
            opportunities: List of opportunities to score
            profile_data: Organization profile
            context: Scoring context
            
        Returns:
            List of ScoringResult objects
        """
        results = []
        for opportunity in opportunities:
            try:
                result = await self.score(opportunity, profile_data, context)
                results.append(result)
            except Exception as e:
                logger.error(f"Error scoring opportunity {opportunity.get('id', 'unknown')}: {e}")
                # Create error result
                error_result = ScoringResult(
                    overall_score=0.0,
                    dimension_scores={},
                    confidence_level=0.0,
                    metadata={'error': str(e)},
                    scorer_type=self.scorer_type,
                    workflow_stage=context.workflow_stage,
                    scoring_timestamp=datetime.now(),
                    processing_time_ms=0.0,
                    data_quality_score=0.0
                )
                results.append(error_result)
        return results
    
    def calculate_confidence(self,
                           dimension_scores: Dict[str, float],
                           data_quality: float,
                           score_consistency: float = 1.0) -> float:
        """
        Calculate confidence level based on multiple factors
        
        Args:
            dimension_scores: Scores for individual dimensions
            data_quality: Quality of input data (0-1)
            score_consistency: Consistency across dimensions (0-1)
            
        Returns:
            Confidence level (0-1)
        """
        # Base confidence from data quality
        base_confidence = data_quality * 0.5
        
        # Confidence from score consistency (low variance = high confidence)
        if dimension_scores:
            score_variance = 0.0
            if len(dimension_scores) > 1:
                scores = list(dimension_scores.values())
                mean_score = sum(scores) / len(scores)
                score_variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            
            consistency_confidence = max(0.0, 1.0 - score_variance * 2) * 0.3
        else:
            consistency_confidence = 0.0
        
        # Confidence from score consistency parameter
        external_confidence = score_consistency * 0.2
        
        return min(1.0, base_confidence + consistency_confidence + external_confidence)
    
    def update_performance_metrics(self, processing_time: float, cache_hit: bool, error: bool = False):
        """Update performance tracking metrics"""
        self.performance_metrics['total_scores'] += 1
        
        # Update average processing time
        current_avg = self.performance_metrics['avg_processing_time']
        total_scores = self.performance_metrics['total_scores']
        new_avg = ((current_avg * (total_scores - 1)) + processing_time) / total_scores
        self.performance_metrics['avg_processing_time'] = new_avg
        
        # Update cache hit rate
        cache_hits = self.performance_metrics.get('cache_hits', 0)
        if cache_hit:
            cache_hits += 1
        self.performance_metrics['cache_hits'] = cache_hits
        self.performance_metrics['cache_hit_rate'] = cache_hits / total_scores
        
        # Update error rate
        errors = self.performance_metrics.get('errors', 0)
        if error:
            errors += 1
        self.performance_metrics['errors'] = errors
        self.performance_metrics['error_rate'] = errors / total_scores
    
    def generate_cache_key(self, 
                          opportunity_data: Dict[str, Any],
                          profile_data: Dict[str, Any],
                          context: ScoringContext) -> str:
        """Generate intelligent cache key for enhanced caching"""
        
        # Core components for cache key
        key_components = [
            self.scorer_type.value,
            context.workflow_stage.value,
            context.entity_type,
            context.opportunity_id,
            context.profile_id
        ]
        
        # Add opportunity-specific components
        if isinstance(opportunity_data, dict):
            opp_components = []
            # Include key opportunity characteristics that affect scoring
            for key in ['funding_amount', 'deadline', 'location', 'ntee_codes', 'focus_areas']:
                if key in opportunity_data:
                    opp_components.append(f"{key}:{opportunity_data[key]}")
            
            if opp_components:
                opp_hash = hashlib.md5("|".join(opp_components).encode()).hexdigest()[:8]
                key_components.append(f"opp:{opp_hash}")
        
        # Add profile-specific components
        if isinstance(profile_data, dict):
            profile_components = []
            for key in ['revenue', 'state', 'ntee_codes', 'focus_areas']:
                if key in profile_data:
                    profile_components.append(f"{key}:{profile_data[key]}")
            
            if profile_components:
                profile_hash = hashlib.md5("|".join(profile_components).encode()).hexdigest()[:8]
                key_components.append(f"profile:{profile_hash}")
        
        return "|".join(key_components)
    
    async def get_cached_score(self,
                              opportunity_data: Dict[str, Any],
                              profile_data: Dict[str, Any], 
                              context: ScoringContext) -> Optional[ScoringResult]:
        """Get cached scoring result if available"""
        
        if not self._cache_enabled:
            return None
        
        try:
            from .enhanced_cache_system import enhanced_cache_system, DataType
            
            # Map scorer type to cache data type
            data_type_mapping = {
                ScorerType.DISCOVERY: DataType.DISCOVERY_RESULTS,
                ScorerType.SUCCESS: DataType.FINANCIAL_ANALYTICS,
                ScorerType.GOVERNMENT: DataType.GOVERNMENT_SCORES,
                ScorerType.AI_LITE: DataType.AI_LITE_RESULTS,
                ScorerType.AI_HEAVY: DataType.AI_HEAVY_RESULTS,
                ScorerType.NETWORK: DataType.NETWORK_ANALYTICS
            }
            
            data_type = data_type_mapping.get(self.scorer_type, DataType.DISCOVERY_RESULTS)
            
            # Generate cache context
            cache_context = {
                'scorer_type': self.scorer_type.value,
                'workflow_stage': context.workflow_stage.value,
                'entity_type': context.entity_type,
                'priority_level': context.priority_level
            }
            
            # Try to get from cache
            cached_result = await enhanced_cache_system.get(
                data_type=data_type,
                entity_id=f"{context.profile_id}:{context.opportunity_id}",
                context=cache_context
            )
            
            if cached_result:
                # Verify cached result is still valid format
                if isinstance(cached_result, dict) and 'overall_score' in cached_result:
                    logger.debug(f"Cache hit for {self.scorer_type.value} scorer")
                    return cached_result
            
            return None
            
        except Exception as e:
            logger.warning(f"Cache retrieval failed for {self.scorer_type.value}: {e}")
            return None
    
    async def cache_score(self,
                         opportunity_data: Dict[str, Any],
                         profile_data: Dict[str, Any],
                         context: ScoringContext,
                         result: ScoringResult) -> bool:
        """Cache scoring result for future use"""
        
        if not self._cache_enabled:
            return False
        
        try:
            from .enhanced_cache_system import enhanced_cache_system, DataType
            
            # Map scorer type to cache data type
            data_type_mapping = {
                ScorerType.DISCOVERY: DataType.DISCOVERY_RESULTS,
                ScorerType.SUCCESS: DataType.FINANCIAL_ANALYTICS,
                ScorerType.GOVERNMENT: DataType.GOVERNMENT_SCORES,
                ScorerType.AI_LITE: DataType.AI_LITE_RESULTS,
                ScorerType.AI_HEAVY: DataType.AI_HEAVY_RESULTS,
                ScorerType.NETWORK: DataType.NETWORK_ANALYTICS
            }
            
            data_type = data_type_mapping.get(self.scorer_type, DataType.DISCOVERY_RESULTS)
            
            # Generate cache context
            cache_context = {
                'scorer_type': self.scorer_type.value,
                'workflow_stage': context.workflow_stage.value,
                'entity_type': context.entity_type,
                'priority_level': context.priority_level
            }
            
            # Convert result to cacheable format
            cacheable_result = {
                'overall_score': result.overall_score,
                'dimension_scores': result.dimension_scores,
                'confidence_level': result.confidence_level,
                'metadata': result.metadata,
                'scorer_type': result.scorer_type.value,
                'workflow_stage': result.workflow_stage.value,
                'scoring_timestamp': result.scoring_timestamp.isoformat(),
                'processing_time_ms': result.processing_time_ms,
                'data_quality_score': result.data_quality_score
            }
            
            # Cache the result
            success = await enhanced_cache_system.put(
                data_type=data_type,
                entity_id=f"{context.profile_id}:{context.opportunity_id}",
                data=cacheable_result,
                context=cache_context,
                custom_ttl=self._cache_ttl_hours
            )
            
            if success:
                logger.debug(f"Cached result for {self.scorer_type.value} scorer")
            
            return success
            
        except Exception as e:
            logger.warning(f"Cache storage failed for {self.scorer_type.value}: {e}")
            return False


class ScorerFactory:
    """Factory for creating and managing scorer instances"""
    
    def __init__(self):
        self._scorers: Dict[ScorerType, UnifiedScorerInterface] = {}
        self._scorer_classes: Dict[ScorerType, type] = {}
    
    def register_scorer(self, scorer_type: ScorerType, scorer_class: type):
        """Register a scorer class for factory creation"""
        self._scorer_classes[scorer_type] = scorer_class
    
    def create_scorer(self, scorer_type: ScorerType) -> UnifiedScorerInterface:
        """Create a new scorer instance"""
        if scorer_type not in self._scorer_classes:
            raise ValueError(f"Unknown scorer type: {scorer_type}")
        
        scorer_class = self._scorer_classes[scorer_type]
        return scorer_class()
    
    def get_scorer(self, scorer_type: ScorerType) -> UnifiedScorerInterface:
        """Get or create a scorer instance (singleton pattern)"""
        if scorer_type not in self._scorers:
            self._scorers[scorer_type] = self.create_scorer(scorer_type)
        return self._scorers[scorer_type]
    
    def get_scorers_for_stage(self, stage: WorkflowStage) -> List[UnifiedScorerInterface]:
        """Get all scorers that support a specific workflow stage"""
        applicable_scorers = []
        for scorer_type, scorer_class in self._scorer_classes.items():
            scorer = self.get_scorer(scorer_type)
            if stage in scorer.supported_stages:
                applicable_scorers.append(scorer)
        return applicable_scorers


class CrossScorerValidator:
    """Validates consistency across different scorer results"""
    
    def __init__(self):
        self.validation_thresholds = {
            'max_score_difference': 0.3,  # Maximum acceptable difference between scorer results
            'min_confidence_agreement': 0.6,  # Minimum confidence when scores agree
            'outlier_threshold': 0.4  # Threshold for detecting outlier scores
        }
    
    def validate_scorer_consistency(self, 
                                  results: List[ScoringResult],
                                  context: ScoringContext) -> Dict[str, Any]:
        """
        Validate consistency across multiple scorer results
        
        Args:
            results: List of scoring results from different scorers
            context: Scoring context
            
        Returns:
            Validation report with warnings and recommendations
        """
        if len(results) < 2:
            return {'status': 'insufficient_data', 'message': 'Need at least 2 scorers for validation'}
        
        scores = [r.overall_score for r in results]
        confidences = [r.confidence_level for r in results]
        
        # Check score variance
        mean_score = sum(scores) / len(scores)
        max_difference = max(abs(s - mean_score) for s in scores)
        
        validation_report = {
            'status': 'valid',
            'mean_score': mean_score,
            'max_difference': max_difference,
            'mean_confidence': sum(confidences) / len(confidences),
            'warnings': [],
            'recommendations': []
        }
        
        # Check for high variance
        if max_difference > self.validation_thresholds['max_score_difference']:
            validation_report['status'] = 'warning'
            validation_report['warnings'].append(
                f"High score variance detected: {max_difference:.2f} > {self.validation_thresholds['max_score_difference']}"
            )
            validation_report['recommendations'].append("Manual review recommended due to scorer disagreement")
        
        # Check for low confidence agreement
        if validation_report['mean_confidence'] < self.validation_thresholds['min_confidence_agreement']:
            validation_report['warnings'].append(
                f"Low confidence agreement: {validation_report['mean_confidence']:.2f}"
            )
            validation_report['recommendations'].append("Consider additional data collection")
        
        # Identify outlier scorers
        outlier_scorers = []
        for i, score in enumerate(scores):
            if abs(score - mean_score) > self.validation_thresholds['outlier_threshold']:
                outlier_scorers.append(results[i].scorer_type.value)
        
        if outlier_scorers:
            validation_report['warnings'].append(f"Outlier scorers detected: {outlier_scorers}")
            validation_report['recommendations'].append("Review outlier scorer configurations")
        
        return validation_report


# Global scorer factory instance
scorer_factory = ScorerFactory()

# Global cross-scorer validator
cross_scorer_validator = CrossScorerValidator()