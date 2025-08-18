#!/usr/bin/env python3
"""
Automated Promotion Service
Background service for automatic opportunity scoring and promotion based on thresholds

This service provides:
1. Batch processing of new opportunities from discovery
2. Automatic scoring using the discovery scorer
3. Threshold-based promotion decisions
4. Background task management for large-scale processing
5. Promotion history tracking and analytics
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from .scoring_service import get_scoring_service
from src.scoring.promotion_engine import get_promotion_engine
from src.profiles.service import get_profile_service

logger = logging.getLogger(__name__)


@dataclass
class AutoPromotionResult:
    """Result of automated promotion batch processing"""
    total_processed: int
    promoted_count: int
    scored_count: int
    error_count: int
    processing_time: float
    promotion_details: List[Dict[str, Any]]
    errors: List[Dict[str, str]]


@dataclass
class AutoPromotionConfig:
    """Configuration for automated promotion"""
    enable_auto_promotion: bool = True
    auto_promotion_threshold: float = 0.75  # Lowered from 0.80 to catch more high-scoring opportunities
    review_promotion_threshold: float = 0.60  # Lowered from 0.65 for better opportunity capture
    batch_size: int = 50
    max_concurrent_scores: int = 10
    enable_990_fetching: bool = True
    score_cache_duration: int = 3600  # 1 hour in seconds


class AutomatedPromotionService:
    """Service for automated opportunity scoring and promotion"""
    
    def __init__(self):
        self.scoring_service = get_scoring_service()
        self.promotion_engine = get_promotion_engine()
        self.profile_service = get_profile_service()
        
        # Default configuration
        self.config = AutoPromotionConfig()
        
        # Processing state
        self.is_processing = False
        self.current_batch_id = None
        self.processing_stats = {
            'last_run': None,
            'total_processed': 0,
            'total_promoted': 0,
            'success_rate': 100.0
        }
    
    async def process_discovery_results(
        self, 
        profile_id: str, 
        opportunities: List[Dict[str, Any]],
        discovery_source: str = "unknown"
    ) -> AutoPromotionResult:
        """
        Process newly discovered opportunities for automatic scoring and promotion
        
        Args:
            profile_id: Profile ID for context
            opportunities: List of opportunity dictionaries from discovery
            discovery_source: Source of the discovery (nonprofit, government, etc.)
            
        Returns:
            AutoPromotionResult with processing statistics and details
        """
        start_time = datetime.now()
        batch_id = f"auto_promote_{profile_id}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting automated promotion for {len(opportunities)} opportunities from {discovery_source}")
        
        if self.is_processing:
            logger.warning("Automated promotion already in progress, skipping batch")
            return AutoPromotionResult(
                total_processed=0,
                promoted_count=0,
                scored_count=0,
                error_count=0,
                processing_time=0.0,
                promotion_details=[],
                errors=[{"error": "Service busy - promotion already in progress"}]
            )
        
        self.is_processing = True
        self.current_batch_id = batch_id
        
        try:
            # Get profile for context
            profile = self.profile_service.get_profile(profile_id)
            if not profile:
                raise ValueError(f"Profile {profile_id} not found")
            
            # Process opportunities in batches
            result = await self._process_opportunity_batch(
                profile, opportunities, discovery_source, batch_id
            )
            
            # Update processing statistics
            self._update_processing_stats(result)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            
            logger.info(f"Automated promotion completed: {result.promoted_count}/{result.total_processed} promoted in {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in automated promotion batch {batch_id}: {e}")
            return AutoPromotionResult(
                total_processed=0,
                promoted_count=0,
                scored_count=0,
                error_count=1,
                processing_time=(datetime.now() - start_time).total_seconds(),
                promotion_details=[],
                errors=[{"error": str(e), "batch_id": batch_id}]
            )
        finally:
            self.is_processing = False
            self.current_batch_id = None
    
    async def _process_opportunity_batch(
        self,
        profile,
        opportunities: List[Dict[str, Any]],
        discovery_source: str,
        batch_id: str
    ) -> AutoPromotionResult:
        """Process a batch of opportunities for scoring and promotion"""
        
        total_processed = 0
        promoted_count = 0
        scored_count = 0
        error_count = 0
        promotion_details = []
        errors = []
        
        # Process opportunities in smaller batches to avoid overwhelming the system
        for i in range(0, len(opportunities), self.config.batch_size):
            batch = opportunities[i:i + self.config.batch_size]
            
            # Create semaphore to limit concurrent scoring operations
            semaphore = asyncio.Semaphore(self.config.max_concurrent_scores)
            
            # Process batch concurrently
            tasks = [
                self._process_single_opportunity(semaphore, profile, opp, discovery_source, batch_id)
                for opp in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for j, result in enumerate(batch_results):
                total_processed += 1
                
                if isinstance(result, Exception):
                    error_count += 1
                    errors.append({
                        "opportunity_id": batch[j].get('opportunity_id', 'unknown'),
                        "error": str(result),
                        "batch_id": batch_id
                    })
                else:
                    scored_count += 1
                    
                    if result.get('promoted', False):
                        promoted_count += 1
                        promotion_details.append(result)
            
            # Small delay between batches to avoid overwhelming the system
            if i + self.config.batch_size < len(opportunities):
                await asyncio.sleep(0.1)
        
        return AutoPromotionResult(
            total_processed=total_processed,
            promoted_count=promoted_count,
            scored_count=scored_count,
            error_count=error_count,
            processing_time=0.0,  # Will be set by caller
            promotion_details=promotion_details,
            errors=errors
        )
    
    async def _process_single_opportunity(
        self,
        semaphore: asyncio.Semaphore,
        profile,
        opportunity: Dict[str, Any],
        discovery_source: str,
        batch_id: str
    ) -> Dict[str, Any]:
        """Process a single opportunity for scoring and potential promotion"""
        
        async with semaphore:
            opportunity_id = opportunity.get('opportunity_id', f"unknown_{datetime.now().timestamp()}")
            
            try:
                # Score the opportunity (initial scoring without enhanced data for threshold check)
                initial_score_request = {
                    "opportunity_data": opportunity,
                    "enhanced_data": None,
                    "force_rescore": False
                }
                
                initial_score_result = await self.scoring_service.score_opportunity(
                    profile.profile_id, opportunity_id, type('ScoreRequest', (), initial_score_request)()
                )
                
                # Fetch enhanced data if score is high enough and 990 fetching is enabled
                enhanced_data = None
                if self.config.enable_990_fetching and initial_score_result.overall_score >= 0.65:
                    enhanced_data = await self._fetch_enhanced_data(opportunity, initial_score_result.overall_score)
                
                # Re-score with enhanced data if available
                if enhanced_data:
                    final_score_request = {
                        "opportunity_data": opportunity,
                        "enhanced_data": enhanced_data,
                        "force_rescore": True
                    }
                    
                    score_result = await self.scoring_service.score_opportunity(
                        profile.profile_id, opportunity_id, type('ScoreRequest', (), final_score_request)()
                    )
                    logger.info(f"Enhanced scoring for {opportunity.get('organization_name')}: "
                              f"{initial_score_result.overall_score:.3f} → {score_result.overall_score:.3f}")
                else:
                    score_result = initial_score_result
                
                # Evaluate for promotion
                promotion_request = {
                    "action": "evaluate",
                    "reason": f"Automated evaluation from {discovery_source}",
                    "user_id": "automated_system"
                }
                
                promotion_result = await self.scoring_service.evaluate_promotion(
                    profile.profile_id, opportunity_id, type('PromotionRequest', (), promotion_request)()
                )
                
                # Apply automatic promotion if threshold is met
                promoted = False
                target_stage = opportunity.get('funnel_stage', 'prospects')
                
                if self.config.enable_auto_promotion and score_result.auto_promotion_eligible:
                    # Automatically promote high-scoring opportunities
                    promote_request = {
                        "action": "promote",
                        "reason": f"Automatic promotion (score: {score_result.overall_score:.3f})",
                        "user_id": "automated_system"
                    }
                    
                    await self.scoring_service.promote_opportunity(
                        profile.profile_id, opportunity_id, type('PromotionRequest', (), promote_request)()
                    )
                    
                    promoted = True
                    target_stage = promotion_result.target_stage
                
                return {
                    "opportunity_id": opportunity_id,
                    "organization_name": opportunity.get('organization_name', 'Unknown'),
                    "score": score_result.overall_score,
                    "promoted": promoted,
                    "from_stage": opportunity.get('funnel_stage', 'prospects'),
                    "to_stage": target_stage,
                    "promotion_recommended": score_result.promotion_recommended,
                    "auto_promotion_eligible": score_result.auto_promotion_eligible,
                    "discovery_source": discovery_source,
                    "batch_id": batch_id,
                    "processed_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error processing opportunity {opportunity_id}: {e}")
                raise e
    
    async def _fetch_enhanced_data(self, opportunity: Dict[str, Any], score: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Fetch enhanced 990 data for high-potential opportunities"""
        try:
            from .enhanced_data_service import get_enhanced_data_service
            
            enhanced_service = get_enhanced_data_service()
            enhanced_result = await enhanced_service.fetch_enhanced_data_for_opportunity(opportunity, score)
            
            if enhanced_result and not enhanced_result.error_message:
                # Format the enhanced data for scoring service consumption
                enhanced_data = {
                    'financial_data': enhanced_result.financial_data,
                    'foundation_data': enhanced_result.foundation_data,
                    'board_data': enhanced_result.board_data,
                    'has_990_data': enhanced_result.has_990_data,
                    'has_990_pf_data': enhanced_result.has_990_pf_data,
                    'data_completeness': enhanced_result.data_completeness,
                    'boost_factors': enhanced_result.boost_factors,
                    'source': 'enhanced_data_service'
                }
                
                logger.info(f"Enhanced data fetched for {enhanced_result.organization_name}: "
                          f"990={enhanced_result.has_990_data}, 990-PF={enhanced_result.has_990_pf_data}, "
                          f"completeness={enhanced_result.data_completeness:.2f}")
                
                return enhanced_data
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to fetch enhanced data: {e}")
            return None
    
    def _update_processing_stats(self, result: AutoPromotionResult):
        """Update service processing statistics"""
        self.processing_stats['last_run'] = datetime.now().isoformat()
        self.processing_stats['total_processed'] += result.total_processed
        self.processing_stats['total_promoted'] += result.promoted_count
        
        if result.total_processed > 0:
            success_rate = ((result.total_processed - result.error_count) / result.total_processed) * 100
            # Use weighted average for overall success rate
            current_weight = min(result.total_processed, 100)  # Cap weight at 100
            total_weight = self.processing_stats['total_processed']
            
            if total_weight > 0:
                self.processing_stats['success_rate'] = (
                    (self.processing_stats['success_rate'] * (total_weight - current_weight) + 
                     success_rate * current_weight) / total_weight
                )
            else:
                self.processing_stats['success_rate'] = success_rate
    
    async def get_promotion_candidates(
        self, profile_id: str, stage: str = "prospects", limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get opportunities that are candidates for promotion"""
        return await self.scoring_service.get_promotion_candidates(profile_id, stage, limit)
    
    async def bulk_promote_candidates(
        self, profile_id: str, opportunity_ids: List[str], user_id: str = "automated_system"
    ) -> Dict[str, Any]:
        """Bulk promote a list of opportunity candidates"""
        bulk_request = type('BulkPromotionRequest', (), {
            'opportunity_ids': opportunity_ids,
            'user_id': user_id
        })()
        
        return await self.scoring_service.bulk_promote(profile_id, bulk_request)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return {
            **self.processing_stats,
            'is_processing': self.is_processing,
            'current_batch_id': self.current_batch_id,
            'config': {
                'auto_promotion_enabled': self.config.enable_auto_promotion,
                'auto_promotion_threshold': self.config.auto_promotion_threshold,
                'review_promotion_threshold': self.config.review_promotion_threshold,
                'batch_size': self.config.batch_size
            }
        }
    
    def update_config(self, config_updates: Dict[str, Any]):
        """Update service configuration"""
        for key, value in config_updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated automated promotion config: {key} = {value}")


def get_automated_promotion_service() -> AutomatedPromotionService:
    """Get singleton instance of automated promotion service"""
    if not hasattr(get_automated_promotion_service, '_instance'):
        get_automated_promotion_service._instance = AutomatedPromotionService()
    return get_automated_promotion_service._instance