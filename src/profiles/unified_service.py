"""
Unified Profile Service for Simplified Architecture

Handles the new unified architecture with:
- Profile directories: data/profiles/profile_id/
- Single profile.json with embedded analytics
- Individual opportunity files in opportunities/ subdirectory
- Single source of truth per opportunity with complete lifecycle data
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import (
    UnifiedProfile, UnifiedOpportunity, ProfileAnalytics, 
    PipelineStage, ScoringResult, StageAnalysis, UserAssessment,
    PromotionEvent, StageTransition, RecentActivity
)

logger = logging.getLogger(__name__)


class UnifiedProfileService:
    """Simplified profile service for unified architecture"""
    
    def __init__(self, data_dir: str = "data/profiles"):
        """Initialize with unified data directory structure"""
        self.data_dir = Path(data_dir)
        
        # Ensure base directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    # ============================================================================
    # PROFILE OPERATIONS
    # ============================================================================
    
    def get_profile(self, profile_id: str) -> Optional[UnifiedProfile]:
        """Get profile with real-time analytics"""
        profile_dir = self.data_dir / profile_id
        profile_file = profile_dir / "profile.json"
        
        if not profile_file.exists():
            logger.warning(f"Profile {profile_id} not found at {profile_file}")
            return None
        
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to UnifiedProfile model
            return UnifiedProfile(**data)
            
        except Exception as e:
            logger.error(f"Error loading profile {profile_id}: {e}")
            return None
    
    def save_profile(self, profile: UnifiedProfile) -> bool:
        """Save profile to storage"""
        try:
            profile_dir = self.data_dir / profile.profile_id
            profile_dir.mkdir(parents=True, exist_ok=True)
            
            profile_file = profile_dir / "profile.json"
            
            # Update timestamp
            profile.updated_at = datetime.now().isoformat()
            
            # Save profile
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile.model_dump(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Profile {profile.profile_id} saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving profile {profile.profile_id}: {e}")
            return False
    
    def list_profiles(self) -> List[str]:
        """List all available profile IDs"""
        profiles = []
        
        try:
            for profile_dir in self.data_dir.iterdir():
                if profile_dir.is_dir() and profile_dir.name.startswith('profile_'):
                    profile_file = profile_dir / "profile.json"
                    if profile_file.exists():
                        profiles.append(profile_dir.name)
            
            return sorted(profiles)
            
        except Exception as e:
            logger.error(f"Error listing profiles: {e}")
            return []
    
    # ============================================================================
    # OPPORTUNITY OPERATIONS
    # ============================================================================
    
    def get_opportunity(self, profile_id: str, opportunity_id: str) -> Optional[UnifiedOpportunity]:
        """Get single opportunity by ID"""
        opportunities_dir = self.data_dir / profile_id / "opportunities"
        
        # Try different possible filename formats to handle legacy naming
        clean_id = opportunity_id.replace('opp_', '').replace('lead_', '')
        possible_files = [
            opportunities_dir / f"{opportunity_id}.json",
            opportunities_dir / f"opportunity_{opportunity_id}.json",
            opportunities_dir / f"opportunity_{clean_id}.json",
            opportunities_dir / f"{clean_id}.json"
        ]
        
        for opp_file in possible_files:
            if opp_file.exists():
                try:
                    with open(opp_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    return UnifiedOpportunity(**data)
                    
                except Exception as e:
                    logger.error(f"Error loading opportunity {opportunity_id}: {e}")
                    continue
        
        logger.warning(f"Opportunity {opportunity_id} not found for profile {profile_id}")
        return None
    
    def save_opportunity(self, profile_id: str, opportunity: UnifiedOpportunity) -> bool:
        """Save opportunity to storage"""
        try:
            opportunities_dir = self.data_dir / profile_id / "opportunities"
            opportunities_dir.mkdir(parents=True, exist_ok=True)
            
            # Use consistent filename format
            opp_file = opportunities_dir / f"opportunity_{opportunity.opportunity_id.replace('opp_', '').replace('lead_', '')}.json"
            
            # Update timestamp
            opportunity.last_updated = datetime.now().isoformat()
            
            # Save opportunity
            with open(opp_file, 'w', encoding='utf-8') as f:
                json.dump(opportunity.model_dump(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Opportunity {opportunity.opportunity_id} saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving opportunity {opportunity.opportunity_id}: {e}")
            return False
    
    def get_profile_opportunities(self, profile_id: str, stage_filter: Optional[str] = None) -> List[UnifiedOpportunity]:
        """Get all opportunities for a profile, optionally filtered by stage"""
        opportunities_dir = self.data_dir / profile_id / "opportunities"
        
        if not opportunities_dir.exists():
            logger.info(f"No opportunities directory for profile {profile_id}")
            return []
        
        opportunities = []
        
        try:
            for opp_file in opportunities_dir.glob("opportunity_*.json"):
                try:
                    with open(opp_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    opportunity = UnifiedOpportunity(**data)
                    
                    # Apply stage filter if specified
                    if stage_filter is None or opportunity.current_stage == stage_filter:
                        opportunities.append(opportunity)
                        
                except Exception as e:
                    logger.error(f"Error loading {opp_file}: {e}")
                    continue
            
            # Sort by discovery date (newest first)
            opportunities.sort(
                key=lambda x: x.discovered_at or "1900-01-01", 
                reverse=True
            )
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error getting opportunities for {profile_id}: {e}")
            return []
    
    # ============================================================================
    # STAGE MANAGEMENT - SINGLE SOURCE OF TRUTH
    # ============================================================================
    
    def update_opportunity_stage(
        self, 
        profile_id: str, 
        opportunity_id: str, 
        new_stage: str,
        reason: str = "Stage update",
        promoted_by: str = "system"
    ) -> bool:
        """Update opportunity stage - atomic operation with history tracking"""
        
        try:
            # Get current opportunity
            opportunity = self.get_opportunity(profile_id, opportunity_id)
            if not opportunity:
                logger.error(f"Opportunity {opportunity_id} not found for stage update")
                return False
            
            old_stage = opportunity.current_stage
            
            # Don't update if already in target stage
            if old_stage == new_stage:
                logger.info(f"Opportunity {opportunity_id} already in stage {new_stage}")
                return True
            
            # Update current stage
            opportunity.current_stage = new_stage
            
            # Add stage transition to history
            now = datetime.now().isoformat()
            
            # Close previous stage if exists
            if opportunity.stage_history:
                last_stage = opportunity.stage_history[-1]
                if not last_stage.exited_at:
                    last_stage.exited_at = now
                    
                    # Calculate duration
                    if last_stage.entered_at:
                        try:
                            entered = datetime.fromisoformat(last_stage.entered_at.replace('Z', '+00:00'))
                            exited = datetime.fromisoformat(now.replace('Z', '+00:00'))
                            last_stage.duration_hours = (exited - entered).total_seconds() / 3600
                        except:
                            pass
            
            # Add new stage transition
            new_transition = StageTransition(
                stage=new_stage,
                entered_at=now,
                exited_at=None,
                duration_hours=None
            )
            opportunity.stage_history.append(new_transition)
            
            # Add to promotion history
            promotion_event = PromotionEvent(
                from_stage=old_stage,
                to_stage=new_stage,
                decision_type="stage_update",
                score_at_promotion=opportunity.scoring.overall_score if opportunity.scoring else 0.0,
                reason=reason,
                promoted_at=now,
                promoted_by=promoted_by
            )
            opportunity.promotion_history.append(promotion_event)
            
            # Save updated opportunity
            success = self.save_opportunity(profile_id, opportunity)
            
            if success:
                # Refresh profile analytics
                self.refresh_profile_analytics(profile_id)
                logger.info(f"Updated opportunity {opportunity_id}: {old_stage} → {new_stage}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating opportunity stage: {e}")
            return False
    
    # ============================================================================
    # SCORING OPERATIONS
    # ============================================================================
    
    def update_opportunity_score(
        self, 
        profile_id: str, 
        opportunity_id: str, 
        scoring_result: Dict[str, Any],
        force_rescore: bool = False
    ) -> bool:
        """Update opportunity scoring - cached unless forced"""
        
        try:
            opportunity = self.get_opportunity(profile_id, opportunity_id)
            if not opportunity:
                return False
            
            # Check if re-scoring is needed
            if not force_rescore and opportunity.scoring:
                logger.info(f"Using cached score for {opportunity_id}")
                return True
            
            # Create/update scoring result
            scoring = ScoringResult(
                overall_score=scoring_result.get('overall_score', 0.0),
                auto_promotion_eligible=scoring_result.get('auto_promotion_eligible', False),
                promotion_recommended=scoring_result.get('promotion_recommended', False),
                dimension_scores=scoring_result.get('dimension_scores', {}),
                confidence_level=scoring_result.get('confidence_level'),
                scored_at=datetime.now().isoformat(),
                scorer_version=scoring_result.get('scorer_version', '1.0.0')
            )
            
            opportunity.scoring = scoring
            
            # Save updated opportunity
            success = self.save_opportunity(profile_id, opportunity)
            
            if success:
                # Refresh profile analytics
                self.refresh_profile_analytics(profile_id)
                logger.info(f"Updated scoring for {opportunity_id}: {scoring.overall_score:.3f}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating opportunity score: {e}")
            return False
    
    def update_user_assessment(
        self,
        profile_id: str,
        opportunity_id: str,
        assessment: Dict[str, Any]
    ) -> bool:
        """Update user assessment - persistent across sessions"""
        
        try:
            opportunity = self.get_opportunity(profile_id, opportunity_id)
            if not opportunity:
                return False
            
            # Create/update user assessment
            user_assessment = UserAssessment(
                user_rating=assessment.get('user_rating'),
                priority_level=assessment.get('priority_level'),
                assessment_notes=assessment.get('assessment_notes'),
                tags=assessment.get('tags', []),
                last_assessed_at=datetime.now().isoformat()
            )
            
            opportunity.user_assessment = user_assessment
            
            # Save updated opportunity
            return self.save_opportunity(profile_id, opportunity)
            
        except Exception as e:
            logger.error(f"Error updating user assessment: {e}")
            return False
    
    # ============================================================================
    # ANALYTICS OPERATIONS
    # ============================================================================
    
    def refresh_profile_analytics(self, profile_id: str) -> bool:
        """Recompute profile analytics from current opportunities"""
        
        try:
            # Get all opportunities
            opportunities = self.get_profile_opportunities(profile_id)
            
            # Compute analytics
            analytics = self._compute_analytics(opportunities)
            
            # Get and update profile
            profile = self.get_profile(profile_id)
            if not profile:
                logger.error(f"Profile {profile_id} not found for analytics refresh")
                return False
            
            profile.analytics = analytics
            profile.recent_activity = self._generate_recent_activity(opportunities)
            
            # Save updated profile
            return self.save_profile(profile)
            
        except Exception as e:
            logger.error(f"Error refreshing analytics for {profile_id}: {e}")
            return False
    
    def _compute_analytics(self, opportunities: List[UnifiedOpportunity]) -> ProfileAnalytics:
        """Compute analytics from opportunities"""
        
        if not opportunities:
            return ProfileAnalytics()
        
        # Stage distribution
        stages_dist = {}
        for opp in opportunities:
            stage = opp.current_stage
            stages_dist[stage] = stages_dist.get(stage, 0) + 1
        
        # Scoring statistics
        scores = [opp.scoring.overall_score for opp in opportunities if opp.scoring]
        high_potential_count = len([s for s in scores if s >= 0.80])
        auto_promotion_eligible = len([opp for opp in opportunities 
                                     if opp.scoring and opp.scoring.auto_promotion_eligible])
        
        scoring_stats = {
            'avg_score': round(sum(scores) / len(scores), 3) if scores else 0.0,
            'high_potential_count': high_potential_count,
            'auto_promotion_eligible': auto_promotion_eligible,
            'last_scored': max((opp.scoring.scored_at for opp in opportunities 
                               if opp.scoring and opp.scoring.scored_at), default=None)
        }
        
        # Discovery statistics  
        discovery_dates = set()
        for opp in opportunities:
            if opp.discovered_at:
                date = opp.discovered_at[:10]  # Just date part
                discovery_dates.add(date)
        
        last_discovery = max((opp.discovered_at for opp in opportunities if opp.discovered_at), default=None)
        last_session_results = len([opp for opp in opportunities 
                                   if opp.discovered_at and opp.discovered_at.startswith(last_discovery[:10])]) if last_discovery else 0
        
        discovery_stats = {
            'total_sessions': len(discovery_dates),
            'last_discovery': last_discovery,
            'last_session_results': last_session_results,
            'avg_results_per_session': len(opportunities) / max(len(discovery_dates), 1)
        }
        
        # Promotion statistics
        total_promotions = sum(len(opp.promotion_history) for opp in opportunities)
        auto_promotions = sum(1 for opp in opportunities for promo in opp.promotion_history 
                             if promo.decision_type == 'auto_promote')
        
        promotion_stats = {
            'total_promotions': total_promotions,
            'auto_promotions': auto_promotions,
            'manual_promotions': total_promotions - auto_promotions,
            'promotion_rate': round(total_promotions / len(opportunities), 2) if opportunities else 0.0
        }
        
        return ProfileAnalytics(
            opportunity_count=len(opportunities),
            stages_distribution=stages_dist,
            scoring_stats=scoring_stats,
            discovery_stats=discovery_stats,
            promotion_stats=promotion_stats
        )
    
    def _generate_recent_activity(self, opportunities: List[UnifiedOpportunity]) -> List[RecentActivity]:
        """Generate recent activity from opportunities"""
        
        activities = []
        
        # Add discovery sessions
        discovery_by_date = {}
        for opp in opportunities:
            if opp.discovered_at:
                date = opp.discovered_at[:10]
                if date not in discovery_by_date:
                    discovery_by_date[date] = 0
                discovery_by_date[date] += 1
        
        # Recent discovery sessions
        for date, count in sorted(discovery_by_date.items(), reverse=True)[:3]:
            activities.append(RecentActivity(
                type='discovery_session',
                date=f"{date}T12:00:00",
                results=count,
                source='Multiple Sources'
            ))
        
        # Recent promotions
        recent_promotions = []
        for opp in opportunities:
            for promo in opp.promotion_history[-2:]:  # Last 2 promotions per opportunity
                recent_promotions.append((promo, opp.organization_name))
        
        # Sort by date and take most recent
        recent_promotions.sort(key=lambda x: x[0].promoted_at or '', reverse=True)
        
        for promo, org_name in recent_promotions[:3]:
            activities.append(RecentActivity(
                type='auto_promotion' if promo.decision_type == 'auto_promote' else 'manual_promotion',
                date=promo.promoted_at,
                opportunity=org_name,
                from_stage=promo.from_stage,
                to_stage=promo.to_stage
            ))
        
        # Sort all activities by date
        activities.sort(key=lambda x: x.date or '', reverse=True)
        
        return activities[:5]  # Return top 5 recent activities


def get_unified_profile_service() -> UnifiedProfileService:
    """Get singleton instance of unified profile service"""
    if not hasattr(get_unified_profile_service, '_instance'):
        get_unified_profile_service._instance = UnifiedProfileService()
    return get_unified_profile_service._instance