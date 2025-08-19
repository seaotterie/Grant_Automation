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
from .base_discoverer import DiscoveryResult, DiscoverySession


class UnifiedDiscoveryAdapter:
    """Adapter to bridge discovery results to unified architecture"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.unified_service = get_unified_profile_service()
    
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
                
                # Check for duplicates by organization name + EIN
                existing_opportunities = self.unified_service.get_profile_opportunities(profile_id)
                
                is_duplicate = False
                for existing in existing_opportunities:
                    if (existing.organization_name == opportunity.organization_name and 
                        existing.ein == opportunity.ein and 
                        existing.ein is not None):
                        duplicates_skipped.append({
                            "organization_name": opportunity.organization_name,
                            "ein": opportunity.ein,
                            "reason": "duplicate_by_ein_and_name"
                        })
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    # Save to unified service
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


# Singleton instance
_unified_discovery_adapter = None

def get_unified_discovery_adapter():
    """Get singleton unified discovery adapter instance"""
    global _unified_discovery_adapter
    if _unified_discovery_adapter is None:
        _unified_discovery_adapter = UnifiedDiscoveryAdapter()
    return _unified_discovery_adapter