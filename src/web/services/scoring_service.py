#!/usr/bin/env python3
"""
Scoring Service API Layer
Web service interface for opportunity scoring and promotion functionality

This service provides:
1. RESTful API endpoints for scoring operations
2. Integration with discovery scorer and promotion engine
3. 990/990-PF data integration for enhanced scoring
4. Bulk operations and batch processing
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from fastapi import HTTPException
from pydantic import BaseModel, Field

from src.scoring.discovery_scorer import DiscoveryScorer, ScoringResult, get_discovery_scorer
from src.scoring.promotion_engine import PromotionEngine, PromotionResult, PromotionDecision, get_promotion_engine
from src.profiles.unified_service import get_unified_profile_service
from src.profiles.models import OrganizationProfile

logger = logging.getLogger(__name__)


class ScoreRequest(BaseModel):
    """Request model for scoring an opportunity"""
    opportunity_data: Dict[str, Any] = Field(..., description="Opportunity data to score")
    enhanced_data: Optional[Dict[str, Any]] = Field(None, description="Optional 990/990-PF data")
    force_rescore: bool = Field(False, description="Force recalculation even if recent score exists")


class ScoreResponse(BaseModel):
    """Response model for scoring results"""
    overall_score: float = Field(..., description="Overall compatibility score (0-1)")
    dimension_scores: Dict[str, float] = Field(..., description="Breakdown by scoring dimensions")
    confidence_level: float = Field(..., description="Confidence in the score (0-1)")
    boost_factors: Dict[str, float] = Field(..., description="Applied boost factors")
    promotion_recommended: bool = Field(..., description="Whether promotion is recommended")
    auto_promotion_eligible: bool = Field(..., description="Whether auto-promotion threshold is met")
    scoring_metadata: Dict[str, Any] = Field(..., description="Additional scoring metadata")
    scored_at: datetime = Field(..., description="When the score was calculated")


class PromotionRequest(BaseModel):
    """Request model for promotion evaluation"""
    action: str = Field(..., description="Action: 'promote', 'demote', or 'evaluate'")
    reason: Optional[str] = Field(None, description="Reason for manual promotion/demotion")
    user_id: Optional[str] = Field(None, description="ID of user making manual change")


class PromotionResponse(BaseModel):
    """Response model for promotion results"""
    decision: str = Field(..., description="Promotion decision")
    reason: str = Field(..., description="Reason for decision")
    current_score: float = Field(..., description="Current opportunity score")
    target_stage: str = Field(..., description="Target funnel stage")
    confidence_level: float = Field(..., description="Confidence in decision")
    requires_manual_review: bool = Field(..., description="Whether manual review is needed")
    promotion_metadata: Dict[str, Any] = Field(..., description="Additional promotion metadata")


class BulkPromotionRequest(BaseModel):
    """Request model for bulk promotions"""
    opportunity_ids: List[str] = Field(..., description="List of opportunity IDs to promote")
    user_id: Optional[str] = Field(None, description="ID of user performing bulk action")


class BulkPromotionResponse(BaseModel):
    """Response model for bulk promotion results"""
    promoted_count: int = Field(..., description="Number of opportunities promoted")
    failed_count: int = Field(..., description="Number that failed to promote")
    results: List[Dict[str, Any]] = Field(..., description="Detailed results for each opportunity")


class ScoringService:
    """Service class for scoring and promotion operations"""
    
    def __init__(self):
        self.discovery_scorer = get_discovery_scorer()
        self.promotion_engine = get_promotion_engine()
        self.profile_service = get_unified_profile_service()
        
        # Cache for recent scores (in production, use Redis or similar)
        self.score_cache: Dict[str, Tuple[ScoringResult, datetime]] = {}
        self.cache_duration_minutes = 60  # Cache scores for 1 hour
    
    async def score_opportunity(
        self, profile_id: str, opportunity_id: str, request: ScoreRequest
    ) -> ScoreResponse:
        """Score an opportunity against a profile"""
        try:
            # Get the profile
            profile = self.profile_service.get_profile(profile_id)
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found")
            
            # Check cache unless forced rescore
            cache_key = f"{profile_id}:{opportunity_id}"
            if not request.force_rescore and cache_key in self.score_cache:
                cached_score, cached_at = self.score_cache[cache_key]
                if (datetime.now() - cached_at).total_seconds() < self.cache_duration_minutes * 60:
                    logger.info(f"Using cached score for {opportunity_id}")
                    return self._format_score_response(cached_score)
            
            # Score the opportunity
            scoring_result = await self.discovery_scorer.score_opportunity(
                request.opportunity_data, profile, request.enhanced_data
            )
            
            # Cache the result
            self.score_cache[cache_key] = (scoring_result, datetime.now())
            
            logger.info(f"Scored opportunity {opportunity_id} for profile {profile_id}: {scoring_result.overall_score:.3f}")
            
            return self._format_score_response(scoring_result)
            
        except Exception as e:
            logger.error(f"Error scoring opportunity {opportunity_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")
    
    async def evaluate_promotion(
        self, profile_id: str, opportunity_id: str, request: PromotionRequest
    ) -> PromotionResponse:
        """Evaluate promotion for an opportunity"""
        try:
            # Get opportunity data (this would come from database in production)
            opportunity_data = await self._get_opportunity_data(profile_id, opportunity_id)
            if not opportunity_data:
                raise HTTPException(status_code=404, detail="Opportunity not found")
            
            # Handle manual override if action is promote/demote
            manual_override = None
            if request.action in ['promote', 'demote']:
                manual_override = {
                    'action': request.action,
                    'reason': request.reason or f"Manual {request.action}",
                    'user_id': request.user_id
                }
            
            # Get current score if available
            current_score = await self._get_current_score(profile_id, opportunity_id, opportunity_data)
            
            # Evaluate promotion
            promotion_result = await self.promotion_engine.evaluate_promotion(
                opportunity_data, current_score, None, manual_override
            )
            
            logger.info(f"Evaluated promotion for {opportunity_id}: {promotion_result.decision.value}")
            
            return self._format_promotion_response(promotion_result)
            
        except Exception as e:
            logger.error(f"Error evaluating promotion for {opportunity_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Promotion evaluation failed: {str(e)}")
    
    async def promote_opportunity(
        self, profile_id: str, opportunity_id: str, request: PromotionRequest
    ) -> PromotionResponse:
        """Promote or demote an opportunity"""
        try:
            # Evaluate the promotion first
            promotion_response = await self.evaluate_promotion(profile_id, opportunity_id, request)
            
            # Get opportunity data
            opportunity_data = await self._get_opportunity_data(profile_id, opportunity_id)
            current_stage = opportunity_data.get('funnel_stage', 'prospects')
            
            # Apply the promotion/demotion
            if request.action == 'promote':
                new_stage = self._get_next_stage(current_stage)
                await self._update_opportunity_stage(profile_id, opportunity_id, new_stage)
                
            elif request.action == 'demote':
                new_stage = self._get_previous_stage(current_stage)
                await self._update_opportunity_stage(profile_id, opportunity_id, new_stage)
            
            # Record in promotion history
            promotion_result = PromotionResult(
                decision=PromotionDecision.MANUAL_OVERRIDE,
                reason=promotion_response.reason,
                current_score=promotion_response.current_score,
                target_stage=new_stage if request.action in ['promote', 'demote'] else current_stage,
                confidence_level=1.0,
                requires_manual_review=False,
                promotion_metadata={'manual_action': True, 'user_id': request.user_id},
                evaluated_at=datetime.now()
            )
            
            await self.promotion_engine.record_promotion(
                opportunity_id, current_stage, new_stage if request.action in ['promote', 'demote'] else current_stage,
                promotion_result, request.user_id
            )
            
            logger.info(f"Applied {request.action} to {opportunity_id}: {current_stage} -> {new_stage if request.action in ['promote', 'demote'] else current_stage}")
            
            return promotion_response
            
        except Exception as e:
            logger.error(f"Error promoting opportunity {opportunity_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Promotion failed: {str(e)}")
    
    async def bulk_promote(
        self, profile_id: str, request: BulkPromotionRequest
    ) -> BulkPromotionResponse:
        """Bulk promote multiple opportunities"""
        try:
            results = []
            promoted_count = 0
            failed_count = 0
            
            for opportunity_id in request.opportunity_ids:
                try:
                    # Get opportunity data
                    opportunity_data = await self._get_opportunity_data(profile_id, opportunity_id)
                    if not opportunity_data:
                        results.append({
                            'opportunity_id': opportunity_id,
                            'success': False,
                            'error': 'Opportunity not found'
                        })
                        failed_count += 1
                        continue
                    
                    # Evaluate promotion
                    promotion_result = await self.promotion_engine.evaluate_promotion(opportunity_data)
                    
                    if promotion_result.should_promote:
                        # Apply promotion
                        current_stage = opportunity_data.get('funnel_stage', 'prospects')
                        new_stage = promotion_result.target_stage
                        
                        await self._update_opportunity_stage(profile_id, opportunity_id, new_stage)
                        
                        # Record promotion
                        await self.promotion_engine.record_promotion(
                            opportunity_id, current_stage, new_stage, promotion_result, request.user_id
                        )
                        
                        results.append({
                            'opportunity_id': opportunity_id,
                            'success': True,
                            'from_stage': current_stage,
                            'to_stage': new_stage,
                            'score': promotion_result.current_score
                        })
                        promoted_count += 1
                    else:
                        results.append({
                            'opportunity_id': opportunity_id,
                            'success': False,
                            'error': 'Did not meet promotion criteria',
                            'score': promotion_result.current_score
                        })
                        failed_count += 1
                        
                except Exception as e:
                    results.append({
                        'opportunity_id': opportunity_id,
                        'success': False,
                        'error': str(e)
                    })
                    failed_count += 1
            
            logger.info(f"Bulk promotion completed: {promoted_count} promoted, {failed_count} failed")
            
            return BulkPromotionResponse(
                promoted_count=promoted_count,
                failed_count=failed_count,
                results=results
            )
            
        except Exception as e:
            logger.error(f"Error in bulk promotion: {e}")
            raise HTTPException(status_code=500, detail=f"Bulk promotion failed: {str(e)}")
    
    async def get_promotion_candidates(
        self, profile_id: str, stage: str = "prospects", limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get opportunities that are candidates for promotion"""
        try:
            # Get opportunities in the specified stage
            opportunities = await self._get_opportunities_by_stage(profile_id, stage)
            
            # Evaluate each for promotion
            candidates = []
            for opportunity in opportunities[:limit]:
                promotion_result = await self.promotion_engine.evaluate_promotion(opportunity)
                
                if promotion_result.should_promote:
                    candidates.append({
                        'opportunity_id': opportunity.get('opportunity_id'),
                        'organization_name': opportunity.get('organization_name'),
                        'current_stage': opportunity.get('funnel_stage'),
                        'target_stage': promotion_result.target_stage,
                        'score': promotion_result.current_score,
                        'decision': promotion_result.decision.value,
                        'requires_review': promotion_result.requires_manual_review
                    })
            
            # Sort by score descending
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"Found {len(candidates)} promotion candidates in {stage}")
            return candidates
            
        except Exception as e:
            logger.error(f"Error getting promotion candidates: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get candidates: {str(e)}")
    
    def _format_score_response(self, scoring_result: ScoringResult) -> ScoreResponse:
        """Format ScoringResult into ScoreResponse"""
        return ScoreResponse(
            overall_score=scoring_result.overall_score,
            dimension_scores={dim.value: score for dim, score in scoring_result.dimension_scores.items()},
            confidence_level=scoring_result.confidence_level,
            boost_factors=scoring_result.boost_factors,
            promotion_recommended=scoring_result.promotion_recommended,
            auto_promotion_eligible=(scoring_result.overall_score >= scoring_result.auto_promotion_threshold),
            scoring_metadata=scoring_result.scoring_metadata,
            scored_at=scoring_result.scored_at
        )
    
    def _format_promotion_response(self, promotion_result: PromotionResult) -> PromotionResponse:
        """Format PromotionResult into PromotionResponse"""
        return PromotionResponse(
            decision=promotion_result.decision.value,
            reason=promotion_result.reason.value,
            current_score=promotion_result.current_score,
            target_stage=promotion_result.target_stage,
            confidence_level=promotion_result.confidence_level,
            requires_manual_review=promotion_result.requires_manual_review,
            promotion_metadata=promotion_result.promotion_metadata
        )
    
    async def _get_opportunity_data(self, profile_id: str, opportunity_id: str) -> Optional[Dict[str, Any]]:
        """Get opportunity data from profile service"""
        try:
            profile_service = get_unified_profile_service()
            
            # Get all leads for the profile and find the one with matching ID
            leads = profile_service.get_profile_leads(profile_id)
            for lead in leads:
                if lead.lead_id == opportunity_id:
                    # Convert pipeline stage to funnel stage for scoring system
                    pipeline_to_funnel_mapping = {
                        'discovery': 'prospects',
                        'pre_scoring': 'qualified_prospects', 
                        'deep_analysis': 'candidates',
                        'recommendations': 'targets'
                    }
                    funnel_stage = pipeline_to_funnel_mapping.get(lead.pipeline_stage.value, 'prospects')
                    
                    # Convert lead to opportunity format expected by scoring system
                    return {
                        'opportunity_id': lead.lead_id,
                        'organization_name': lead.organization_name,
                        'funnel_stage': funnel_stage,
                        'compatibility_score': lead.compatibility_score or 0.5,
                        'source_type': lead.source or 'Nonprofit',
                        'external_data': lead.external_data or {},
                        'funding_amount': lead.funding_amount,
                        'location': getattr(lead, 'location', None),
                        'description': lead.description,
                        'discovered_at': lead.discovered_at.isoformat() if lead.discovered_at else None,
                        'last_analyzed': lead.last_analyzed.isoformat() if lead.last_analyzed else None
                    }
            
            logger.warning(f"Opportunity {opportunity_id} not found for profile {profile_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting opportunity data: {e}")
            return None
    
    async def _get_current_score(
        self, profile_id: str, opportunity_id: str, opportunity_data: Dict[str, Any]
    ) -> Optional[ScoringResult]:
        """Get current score for opportunity"""
        cache_key = f"{profile_id}:{opportunity_id}"
        if cache_key in self.score_cache:
            cached_score, cached_at = self.score_cache[cache_key]
            if (datetime.now() - cached_at).total_seconds() < self.cache_duration_minutes * 60:
                return cached_score
        return None
    
    async def _update_opportunity_stage(self, profile_id: str, opportunity_id: str, new_stage: str):
        """Update opportunity stage using profile service"""
        try:
            from src.profiles.models import PipelineStage

            profile_service = get_unified_profile_service()
            
            # Convert string stage to PipelineStage enum
            stage_mapping = {
                'prospects': PipelineStage.DISCOVERY,
                'qualified_prospects': PipelineStage.PRE_SCORING, 
                'candidates': PipelineStage.DEEP_ANALYSIS,
                'targets': PipelineStage.RECOMMENDATIONS,
                'opportunities': PipelineStage.RECOMMENDATIONS  # Final stage
            }
            
            pipeline_stage = stage_mapping.get(new_stage)
            if not pipeline_stage:
                logger.error(f"Invalid stage for update: {new_stage}")
                return
            
            # Update the lead stage in persistent storage
            success = profile_service.update_lead_stage(opportunity_id, pipeline_stage)
            if success:
                logger.info(f"Successfully updated opportunity {opportunity_id} to stage {new_stage}")
            else:
                logger.error(f"Failed to update opportunity {opportunity_id} to stage {new_stage}")
                
        except Exception as e:
            logger.error(f"Error updating opportunity stage: {e}")
    
    async def _get_opportunities_by_stage(self, profile_id: str, stage: str) -> List[Dict[str, Any]]:
        """Get opportunities by stage (placeholder - would query database)"""
        # In production, this would query the database
        return []
    
    def _get_next_stage(self, current_stage: str) -> str:
        """Get next stage in progression"""
        stage_progression = {
            'prospects': 'qualified_prospects',
            'qualified_prospects': 'candidates',
            'candidates': 'targets',
            'targets': 'opportunities'
        }
        return stage_progression.get(current_stage, current_stage)
    
    def _get_previous_stage(self, current_stage: str) -> str:
        """Get previous stage in progression"""
        stage_regression = {
            'qualified_prospects': 'prospects',
            'candidates': 'qualified_prospects',
            'targets': 'candidates',
            'opportunities': 'targets'
        }
        return stage_regression.get(current_stage, current_stage)


def get_scoring_service() -> ScoringService:
    """Get singleton instance of scoring service"""
    if not hasattr(get_scoring_service, '_instance'):
        get_scoring_service._instance = ScoringService()
    return get_scoring_service._instance