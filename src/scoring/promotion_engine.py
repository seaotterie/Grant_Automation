#!/usr/bin/env python3
"""
Promotion Engine
Automated promotion/demotion system based on scoring thresholds

This engine handles:
1. Automated promotion from Discovery to Qualified Prospects
2. Score-based demotion triggers  
3. Manual promotion with override capabilities
4. Promotion history and audit trails
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

from .discovery_scorer import ScoringResult, DiscoveryScorer

logger = logging.getLogger(__name__)


class PromotionDecision(Enum):
    """Promotion decision types"""
    AUTO_PROMOTE = "auto_promote"          # Score ≥ 0.80 with high confidence
    REVIEW_PROMOTE = "review_promote"      # Score 0.65-0.79, manual review recommended
    STAY_DISCOVERY = "stay_discovery"     # Score < 0.65, remain in discovery
    DEMOTE = "demote"                     # Score dropped below threshold
    MANUAL_OVERRIDE = "manual_override"    # Manual promotion/demotion


class PromotionReason(Enum):
    """Reasons for promotion decisions"""
    HIGH_SCORE = "high_score"                    # Exceeded auto-promotion threshold
    SCORE_WITH_990_DATA = "score_with_990_data"  # Good score plus enhanced data
    MANUAL_REVIEW_PASSED = "manual_review_passed" # Manual review approved
    DEADLINE_URGENCY = "deadline_urgency"        # Urgent deadline requires promotion
    STRATEGIC_PRIORITY = "strategic_priority"    # Strategic importance override
    SCORE_DECLINED = "score_declined"            # Score dropped below threshold
    DEADLINE_PASSED = "deadline_passed"          # Opportunity deadline expired
    ELIGIBILITY_LOST = "eligibility_lost"        # No longer meets criteria
    MANUAL_DECISION = "manual_decision"          # Manual override by user


@dataclass
class PromotionResult:
    """Result of promotion evaluation"""
    decision: PromotionDecision
    reason: PromotionReason
    current_score: float
    target_stage: str
    confidence_level: float
    requires_manual_review: bool
    promotion_metadata: Dict[str, Any]
    evaluated_at: datetime
    
    @property
    def should_promote(self) -> bool:
        """Whether the opportunity should be promoted"""
        return self.decision in [PromotionDecision.AUTO_PROMOTE, PromotionDecision.REVIEW_PROMOTE]
    
    @property
    def should_demote(self) -> bool:
        """Whether the opportunity should be demoted"""
        return self.decision == PromotionDecision.DEMOTE


@dataclass
class PromotionHistory:
    """Historical promotion record"""
    opportunity_id: str
    from_stage: str
    to_stage: str
    decision: PromotionDecision
    reason: PromotionReason
    score_at_promotion: float
    promoted_by: Optional[str]  # User ID if manual
    promoted_at: datetime
    metadata: Dict[str, Any]


class PromotionEngine:
    """Engine for automated and manual promotion decisions"""
    
    def __init__(self, discovery_scorer: Optional[DiscoveryScorer] = None):
        self.discovery_scorer = discovery_scorer or DiscoveryScorer()
        
        # Promotion thresholds based on scoring analysis
        self.promotion_thresholds = {
            "auto_promote": 0.80,        # Automatic promotion threshold
            "review_promote": 0.65,      # Manual review recommended
            "stay_discovery": 0.45,      # Minimum to stay in discovery
            "demote_threshold": 0.35     # Below this = demote
        }
        
        # Stage progression mapping
        self.stage_progression = {
            "prospects": "qualified_prospects",
            "qualified_prospects": "candidates", 
            "candidates": "targets",
            "targets": "opportunities"
        }
        
        self.stage_regression = {
            "opportunities": "targets",
            "targets": "candidates",
            "candidates": "qualified_prospects",
            "qualified_prospects": "prospects"
        }
        
        # Promotion history storage (in production, this would be database)
        self.promotion_history: List[PromotionHistory] = []
    
    async def evaluate_promotion(
        self,
        opportunity: Dict[str, Any],
        current_score: Optional[ScoringResult] = None,
        enhanced_data: Optional[Dict[str, Any]] = None,
        manual_override: Optional[Dict[str, Any]] = None
    ) -> PromotionResult:
        """
        Evaluate whether an opportunity should be promoted
        
        Args:
            opportunity: Opportunity data
            current_score: Current scoring result
            enhanced_data: 990/990-PF data if available
            manual_override: Manual promotion/demotion request
            
        Returns:
            PromotionResult with decision and reasoning
        """
        try:
            current_stage = opportunity.get('funnel_stage', 'prospects')
            opportunity_id = opportunity.get('opportunity_id', '')
            
            logger.info(f"Evaluating promotion for {opportunity.get('organization_name')} (stage: {current_stage})")
            
            # Handle manual override first
            if manual_override:
                return await self._handle_manual_override(opportunity, manual_override)
            
            # Use provided score or calculate new one
            if not current_score:
                # Would need profile data here - simplified for now
                score_value = opportunity.get('compatibility_score', 0.5)
                confidence = 0.7
            else:
                score_value = current_score.overall_score
                confidence = current_score.confidence_level
            
            # Determine promotion decision based on score and stage
            decision, reason, target_stage = await self._determine_promotion_decision(
                current_stage, score_value, enhanced_data, confidence
            )
            
            # Create promotion metadata
            metadata = {
                "current_stage": current_stage,
                "score_value": score_value,
                "confidence_level": confidence,
                "has_enhanced_data": enhanced_data is not None,
                "thresholds_used": self.promotion_thresholds,
                "evaluation_version": "1.0.0"
            }
            
            # Check if manual review is required
            requires_review = self._requires_manual_review(decision, score_value, confidence)
            
            return PromotionResult(
                decision=decision,
                reason=reason,
                current_score=score_value,
                target_stage=target_stage,
                confidence_level=confidence,
                requires_manual_review=requires_review,
                promotion_metadata=metadata,
                evaluated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error evaluating promotion: {e}")
            return PromotionResult(
                decision=PromotionDecision.STAY_DISCOVERY,
                reason=PromotionReason.MANUAL_DECISION,
                current_score=0.1,
                target_stage=current_stage,
                confidence_level=0.0,
                requires_manual_review=True,
                promotion_metadata={"error": str(e)},
                evaluated_at=datetime.now()
            )
    
    async def _determine_promotion_decision(
        self,
        current_stage: str,
        score: float,
        enhanced_data: Optional[Dict[str, Any]],
        confidence: float
    ) -> Tuple[PromotionDecision, PromotionReason, str]:
        """Determine promotion decision based on score and context"""
        
        # Special handling for Discovery stage (prospects)
        if current_stage == "prospects":
            
            # Auto-promote: High score with good confidence
            if score >= self.promotion_thresholds["auto_promote"] and confidence >= 0.7:
                if enhanced_data and 'financial_data' in enhanced_data:
                    return (PromotionDecision.AUTO_PROMOTE, PromotionReason.SCORE_WITH_990_DATA, "qualified_prospects")
                else:
                    return (PromotionDecision.AUTO_PROMOTE, PromotionReason.HIGH_SCORE, "qualified_prospects")
            
            # Review promote: Good score, may need manual review
            elif score >= self.promotion_thresholds["review_promote"]:
                return (PromotionDecision.REVIEW_PROMOTE, PromotionReason.HIGH_SCORE, "qualified_prospects")
            
            # Stay in discovery: Adequate score
            elif score >= self.promotion_thresholds["stay_discovery"]:
                return (PromotionDecision.STAY_DISCOVERY, PromotionReason.HIGH_SCORE, "prospects")
            
            # Consider demotion: Very low score
            else:
                return (PromotionDecision.DEMOTE, PromotionReason.SCORE_DECLINED, "prospects")
        
        # For other stages, different logic applies
        else:
            # Check if score has declined significantly
            if score < self.promotion_thresholds["demote_threshold"]:
                prev_stage = self.stage_regression.get(current_stage, current_stage)
                return (PromotionDecision.DEMOTE, PromotionReason.SCORE_DECLINED, prev_stage)
            
            # Check for promotion to next stage
            elif score >= self.promotion_thresholds["auto_promote"] and current_stage != "opportunities":
                next_stage = self.stage_progression.get(current_stage, current_stage)
                return (PromotionDecision.AUTO_PROMOTE, PromotionReason.HIGH_SCORE, next_stage)
            
            # Stay in current stage
            else:
                return (PromotionDecision.STAY_DISCOVERY, PromotionReason.HIGH_SCORE, current_stage)
    
    async def _handle_manual_override(
        self, opportunity: Dict[str, Any], override: Dict[str, Any]
    ) -> PromotionResult:
        """Handle manual promotion/demotion override"""
        
        action = override.get('action', 'promote')  # 'promote' or 'demote'
        reason = override.get('reason', 'Manual decision')
        user_id = override.get('user_id')
        
        current_stage = opportunity.get('funnel_stage', 'prospects')
        
        if action == 'promote':
            target_stage = self.stage_progression.get(current_stage, current_stage)
            decision = PromotionDecision.MANUAL_OVERRIDE
            reason_enum = PromotionReason.MANUAL_DECISION
        else:  # demote
            target_stage = self.stage_regression.get(current_stage, current_stage)
            decision = PromotionDecision.MANUAL_OVERRIDE
            reason_enum = PromotionReason.MANUAL_DECISION
        
        metadata = {
            "manual_override": True,
            "user_id": user_id,
            "override_reason": reason,
            "action": action
        }
        
        return PromotionResult(
            decision=decision,
            reason=reason_enum,
            current_score=opportunity.get('compatibility_score', 0.5),
            target_stage=target_stage,
            confidence_level=1.0,  # Manual decisions have full confidence
            requires_manual_review=False,
            promotion_metadata=metadata,
            evaluated_at=datetime.now()
        )
    
    def _requires_manual_review(
        self, decision: PromotionDecision, score: float, confidence: float
    ) -> bool:
        """Determine if manual review is required"""
        
        # Review promote decisions always need review
        if decision == PromotionDecision.REVIEW_PROMOTE:
            return True
        
        # Low confidence auto-promotes need review
        if decision == PromotionDecision.AUTO_PROMOTE and confidence < 0.8:
            return True
        
        # Edge case scores need review
        if 0.75 <= score <= 0.85:  # Close to threshold
            return True
        
        return False
    
    async def record_promotion(
        self,
        opportunity_id: str,
        from_stage: str,
        to_stage: str,
        promotion_result: PromotionResult,
        promoted_by: Optional[str] = None
    ) -> PromotionHistory:
        """Record a promotion in history"""
        
        history_record = PromotionHistory(
            opportunity_id=opportunity_id,
            from_stage=from_stage,
            to_stage=to_stage,
            decision=promotion_result.decision,
            reason=promotion_result.reason,
            score_at_promotion=promotion_result.current_score,
            promoted_by=promoted_by,
            promoted_at=datetime.now(),
            metadata=promotion_result.promotion_metadata
        )
        
        self.promotion_history.append(history_record)
        logger.info(f"Recorded promotion: {opportunity_id} from {from_stage} to {to_stage}")
        
        return history_record
    
    async def get_promotion_candidates(
        self, opportunities: List[Dict[str, Any]], stage: str = "prospects"
    ) -> List[Tuple[Dict[str, Any], PromotionResult]]:
        """Get opportunities that are candidates for promotion"""
        
        candidates = []
        
        for opportunity in opportunities:
            if opportunity.get('funnel_stage') == stage:
                promotion_result = await self.evaluate_promotion(opportunity)
                
                if promotion_result.should_promote:
                    candidates.append((opportunity, promotion_result))
        
        # Sort by score descending
        candidates.sort(key=lambda x: x[1].current_score, reverse=True)
        
        return candidates
    
    async def bulk_promote(
        self,
        opportunities: List[Dict[str, Any]],
        user_id: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], PromotionResult]]:
        """Bulk promote multiple opportunities"""
        
        results = []
        
        for opportunity in opportunities:
            promotion_result = await self.evaluate_promotion(opportunity)
            
            if promotion_result.should_promote:
                # Record the promotion
                await self.record_promotion(
                    opportunity.get('opportunity_id', ''),
                    opportunity.get('funnel_stage', 'prospects'),
                    promotion_result.target_stage,
                    promotion_result,
                    user_id
                )
                
                results.append((opportunity, promotion_result))
        
        logger.info(f"Bulk promoted {len(results)} opportunities")
        return results
    
    def get_promotion_history(
        self, opportunity_id: Optional[str] = None, limit: int = 100
    ) -> List[PromotionHistory]:
        """Get promotion history"""
        
        if opportunity_id:
            history = [h for h in self.promotion_history if h.opportunity_id == opportunity_id]
        else:
            history = self.promotion_history
        
        # Sort by promotion date descending
        history.sort(key=lambda x: x.promoted_at, reverse=True)
        
        return history[:limit]


def get_promotion_engine() -> PromotionEngine:
    """Get singleton instance of promotion engine"""
    if not hasattr(get_promotion_engine, '_instance'):
        get_promotion_engine._instance = PromotionEngine()
    return get_promotion_engine._instance