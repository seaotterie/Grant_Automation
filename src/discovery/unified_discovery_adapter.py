"""
Unified Discovery Adapter

Bridges discovery results to unified profile service, enabling automatic
opportunity creation with enhanced data persistence and real-time analytics.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from src.profiles.unified_service import get_unified_profile_service
from src.profiles.models import UnifiedOpportunity, ScoringResult, StageAnalysis
from src.scoring.promotion_engine import PromotionEngine, PromotionDecision
from .base_discoverer import DiscoveryResult, DiscoverySession


class UnifiedDiscoveryAdapter:
    """Adapter to bridge discovery results to unified architecture"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.unified_service = get_unified_profile_service()
        self.promotion_engine = PromotionEngine()
    
    def convert_discovery_result_to_opportunity(
        self, 
        discovery_result: DiscoveryResult, 
        profile_id: str,
        session_id: str
    ) -> UnifiedOpportunity:
        """Convert a discovery result to a unified opportunity"""
        
        # Generate unique opportunity ID
        opportunity_id = f"opp_{discovery_result.opportunity_id}"
        
        # Create scoring result from discovery data
        scoring = None
        if hasattr(discovery_result, 'compatibility_score') and discovery_result.compatibility_score:
            scoring = ScoringResult(
                overall_score=discovery_result.compatibility_score,
                auto_promotion_eligible=discovery_result.compatibility_score >= 0.75,
                promotion_recommended=discovery_result.compatibility_score >= 0.80,
                dimension_scores={},
                confidence_level=discovery_result.confidence_level if discovery_result.confidence_level else 0.75,
                scored_at=datetime.now().isoformat(),
                scorer_version="discovery_v1.0"
            )
        
        # Create discovery stage analysis
        discovery_analysis = StageAnalysis(
            match_factors=discovery_result.match_factors or {},
            risk_factors={},
            recommendations=[],
            network_insights={},
            analyzed_at=datetime.now().isoformat(),
            source=discovery_result.discovery_source or "discovery_engine",
            opportunity_type=discovery_result.source_type.value if discovery_result.source_type else "grants",
            enhanced_data=discovery_result.external_data
        )
        
        # Create unified opportunity
        opportunity = UnifiedOpportunity(
            opportunity_id=opportunity_id,
            profile_id=profile_id,
            organization_name=discovery_result.organization_name,
            ein=discovery_result.external_data.get('ein') if discovery_result.external_data else None,
            current_stage="discovery",
            stage_history=[],
            scoring=scoring,
            analysis={"discovery": discovery_analysis},
            user_assessment=None,
            promotion_history=[],
            source=discovery_result.discovery_source or "discovery_engine",
            opportunity_type=discovery_result.source_type.value if discovery_result.source_type else "grants",
            discovered_at=discovery_result.discovered_at.isoformat() if discovery_result.discovered_at else datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            status="active",
            legacy_lead_id=f"lead_{discovery_result.opportunity_id}",
            legacy_pipeline_stage="discovery",
            description=discovery_result.description or f"Opportunity discovered via {discovery_result.discovery_source}",
            funding_amount=discovery_result.funding_amount,
            program_name=discovery_result.program_name or (discovery_result.external_data.get('program_name') if discovery_result.external_data else None)
        )
        
        return opportunity
    
    async def save_discovery_results(
        self, 
        discovery_results: List[DiscoveryResult], 
        profile_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Save discovery results to unified service and return statistics"""
        
        saved_opportunities = []
        failed_saves = []
        duplicates_skipped = []
        
        for result in discovery_results:
            try:
                # Convert to unified opportunity
                opportunity = self.convert_discovery_result_to_opportunity(
                    result, profile_id, session_id
                )
                
                # Enhanced duplicate detection
                existing_opportunities = self.unified_service.get_profile_opportunities(profile_id)
                
                is_duplicate = False
                duplicate_reason = None
                
                for existing in existing_opportunities:
                    # Method 1: Exact EIN match (most reliable)
                    if (opportunity.ein and existing.ein and 
                        opportunity.ein == existing.ein):
                        duplicate_reason = "duplicate_by_ein"
                        is_duplicate = True
                        break
                    
                    # Method 2: Exact organization name match (case-insensitive)
                    if (opportunity.organization_name and existing.organization_name and
                        opportunity.organization_name.lower().strip() == existing.organization_name.lower().strip()):
                        duplicate_reason = "duplicate_by_name"
                        is_duplicate = True
                        break
                    
                    # Method 3: Fuzzy name matching for similar organizations
                    if (opportunity.organization_name and existing.organization_name):
                        name1 = opportunity.organization_name.lower().strip()
                        name2 = existing.organization_name.lower().strip()
                        
                        # Remove common suffixes/prefixes for comparison
                        name1_clean = self._clean_org_name(name1)
                        name2_clean = self._clean_org_name(name2)
                        
                        # Check for high similarity (>= 85% match)
                        similarity = self._calculate_name_similarity(name1_clean, name2_clean)
                        if similarity >= 0.85:
                            duplicate_reason = f"duplicate_by_fuzzy_name_similarity_{similarity:.2f}"
                            is_duplicate = True
                            break
                    
                    # Method 4: Cross-source duplicate detection
                    if (opportunity.organization_name and existing.organization_name and
                        opportunity.source != existing.source and
                        opportunity.organization_name.lower().strip() == existing.organization_name.lower().strip()):
                        duplicate_reason = "duplicate_cross_source"
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    duplicates_skipped.append({
                        "organization_name": opportunity.organization_name,
                        "ein": opportunity.ein,
                        "reason": duplicate_reason
                    })
                    self.logger.info(f"Skipping duplicate: {opportunity.organization_name} ({duplicate_reason})")
                
                if not is_duplicate:
                    # Check for auto-promotion before saving (to modify opportunity in-memory)
                    await self._check_auto_promotion(opportunity, profile_id)
                    
                    # Save to unified service (with updated stage if auto-promoted)
                    success = self.unified_service.save_opportunity(profile_id, opportunity)
                    
                    if success:
                        saved_opportunities.append({
                            "opportunity_id": opportunity.opportunity_id,
                            "organization_name": opportunity.organization_name,
                            "score": opportunity.scoring.overall_score if opportunity.scoring else 0.0,
                            "source": opportunity.source
                        })
                        self.logger.info(f"Saved opportunity: {opportunity.organization_name}")
                    else:
                        failed_saves.append({
                            "organization_name": opportunity.organization_name,
                            "reason": "save_failed"
                        })
                        
            except Exception as e:
                self.logger.error(f"Failed to save opportunity {result.organization_name}: {e}")
                failed_saves.append({
                    "organization_name": result.organization_name,
                    "reason": str(e)
                })
        
        # Refresh profile analytics after bulk save
        if saved_opportunities:
            self.unified_service.refresh_profile_analytics(profile_id)
            self.logger.info(f"Refreshed analytics for profile {profile_id} after saving {len(saved_opportunities)} opportunities")
        
        return {
            "saved_count": len(saved_opportunities),
            "failed_count": len(failed_saves),
            "duplicates_skipped": len(duplicates_skipped),
            "saved_opportunities": saved_opportunities,
            "failed_saves": failed_saves,
            "duplicates": duplicates_skipped,
            "analytics_refreshed": len(saved_opportunities) > 0
        }
    
    async def update_discovery_session_analytics(
        self, 
        session: DiscoverySession, 
        save_results: Dict[str, Any],
        profile_id: str
    ) -> Dict[str, Any]:
        """Update session analytics in profile with unified service data"""
        
        try:
            # Get updated profile with fresh analytics
            profile = self.unified_service.get_profile(profile_id)
            if not profile:
                return {"error": "Profile not found"}
            
            # Create discovery session record
            session_record = {
                "session_id": session.session_id,
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "execution_time_seconds": session.execution_time_seconds,
                "total_results_discovered": session.total_results,
                "opportunities_saved": save_results["saved_count"],
                "opportunities_failed": save_results["failed_count"],  
                "duplicates_skipped": save_results["duplicates_skipped"],
                "funding_types": [ft.value for ft in session.funding_types] if session.funding_types else [],
                "api_calls_made": session.api_calls_made,
                "status": session.status.value if session.status else "unknown"
            }
            
            return {
                "session_record": session_record,
                "updated_analytics": profile.analytics.model_dump() if profile.analytics else None,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update discovery session analytics: {e}")
            return {"error": str(e), "success": False}
    
    async def _check_auto_promotion(self, opportunity: UnifiedOpportunity, profile_id: str) -> None:
        """Check if opportunity qualifies for auto-promotion and advance through stages"""
        
        try:
            if not opportunity.scoring:
                self.logger.debug(f"No scoring data for opportunity {opportunity.opportunity_id}, skipping auto-promotion")
                return
            
            score = opportunity.scoring.overall_score
            
            # Check if opportunity qualifies for auto-promotion (score >= 0.80)
            if score >= 0.80:
                self.logger.info(f"Opportunity {opportunity.organization_name} ({score:.2f}) qualifies for auto-promotion")
                
                # Evaluate promotion using promotion engine
                opportunity_dict = {
                    "opportunity_id": opportunity.opportunity_id,
                    "organization_name": opportunity.organization_name,
                    "current_stage": opportunity.current_stage,
                    "score": score,
                    "ein": opportunity.ein
                }
                
                promotion_result = await self.promotion_engine.evaluate_promotion(
                    opportunity=opportunity_dict,
                    current_score=opportunity.scoring
                )
                
                # If auto-promotion recommended, advance through stages
                if promotion_result.decision == PromotionDecision.AUTO_PROMOTE:
                    # Auto-promote through discovery -> pre_scoring -> deep_analysis
                    final_stage = "deep_analysis"  # Target stage for high-scoring opportunities
                    
                    if opportunity.current_stage == "discovery":
                        final_stage = "deep_analysis"  # Skip intermediate stages for high scores
                    elif opportunity.current_stage == "pre_scoring":
                        final_stage = "deep_analysis"
                    
                    # Update opportunity in-memory (before saving)
                    old_stage = opportunity.current_stage
                    opportunity.current_stage = final_stage
                    
                    # Add stage transition to history
                    from src.profiles.models import StageTransition, PromotionEvent
                    now = datetime.now().isoformat()
                    
                    # Close current stage
                    if opportunity.stage_history:
                        last_stage = opportunity.stage_history[-1]
                        if not last_stage.exited_at:
                            last_stage.exited_at = now
                    
                    # Add new stage transition
                    new_transition = StageTransition(
                        stage=final_stage,
                        entered_at=now,
                        exited_at=None,
                        duration_hours=None
                    )
                    opportunity.stage_history.append(new_transition)
                    
                    # Add promotion event
                    promotion_event = PromotionEvent(
                        from_stage=old_stage,
                        to_stage=final_stage,
                        promoted_at=now,
                        promoted_by="auto_promotion_engine",
                        reason=f"Auto-promotion based on score {score:.2f}",
                        decision_type="auto_promote"
                    )
                    opportunity.promotion_history.append(promotion_event)
                    
                    # Update scoring result to reflect auto-promotion status
                    opportunity.scoring.auto_promotion_eligible = True
                    opportunity.scoring.promotion_recommended = True
                    
                    self.logger.info(f"Auto-promoted {opportunity.organization_name} from {old_stage} to {final_stage} (score: {score:.2f})")
                    
                else:
                    self.logger.info(f"Promotion engine did not recommend auto-promotion for {opportunity.organization_name}: {promotion_result.reasoning}")
                    
            elif score >= 0.65:
                self.logger.info(f"Opportunity {opportunity.organization_name} ({score:.2f}) qualifies for manual review")
                # Mark as eligible for manual review but don't auto-promote
                opportunity.scoring.promotion_recommended = True
                
        except Exception as e:
            self.logger.error(f"Failed to check auto-promotion for {opportunity.opportunity_id}: {e}")
    
    def _clean_org_name(self, name: str) -> str:
        """Clean organization name for better duplicate detection"""
        import re
        
        # Convert to lowercase and strip
        name = name.lower().strip()
        
        # Remove common organizational suffixes
        suffixes = [
            r'\b(inc\.?|incorporated)\b',
            r'\b(llc\.?|l\.l\.c\.?)\b',
            r'\b(corp\.?|corporation)\b',
            r'\b(ltd\.?|limited)\b',
            r'\b(foundation|fund)\b',
            r'\b(org\.?|organization)\b',
            r'\b(assoc\.?|association)\b',
            r'\b(inst\.?|institute)\b',
            r'\b(center|centre)\b',
            r'\b(society|soc\.?)\b',
            r'\b(trust|company|co\.?)\b'
        ]
        
        for suffix in suffixes:
            name = re.sub(suffix, '', name).strip()
        
        # Remove extra whitespace and punctuation
        name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
        name = re.sub(r'\s+', ' ', name)     # Normalize whitespace
        
        return name.strip()
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two organization names using Levenshtein distance"""
        if not name1 or not name2:
            return 0.0
        
        if name1 == name2:
            return 1.0
        
        # Simple character-based similarity calculation
        # Using a basic approach since we want to avoid external dependencies
        def levenshtein_distance(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        max_len = max(len(name1), len(name2))
        if max_len == 0:
            return 1.0
        
        distance = levenshtein_distance(name1, name2)
        similarity = 1.0 - (distance / max_len)
        
        return max(0.0, similarity)


# Singleton instance
_unified_discovery_adapter = None

def get_unified_discovery_adapter():
    """Get singleton unified discovery adapter instance"""
    global _unified_discovery_adapter
    if _unified_discovery_adapter is None:
        _unified_discovery_adapter = UnifiedDiscoveryAdapter()
    return _unified_discovery_adapter