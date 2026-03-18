#!/usr/bin/env python3
"""
Funnel Management Router - Opportunity funnel stage management endpoints.

Extracted from main.py funnel endpoints (lines ~6108-6363).
Handles opportunity stage transitions, promotions, demotions,
metrics, recommendations, and bulk transitions.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/funnel", tags=["Funnel Management"])


@router.get("/{profile_id}/opportunities")
async def get_profile_opportunities(profile_id: str, stage: Optional[str] = None):
    """Get opportunities by funnel stage for a profile."""
    try:
        from src.discovery.funnel_manager import FunnelManager
        from src.discovery.base_discoverer import FunnelStage

        # Use a module-level funnel manager via lazy init
        if not hasattr(get_profile_opportunities, '_funnel_manager'):
            get_profile_opportunities._funnel_manager = FunnelManager()
        funnel_manager = get_profile_opportunities._funnel_manager

        if stage:
            try:
                stage_enum = FunnelStage(stage)
                opportunities = funnel_manager.get_opportunities_by_stage(profile_id, stage_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")
        else:
            opportunities = funnel_manager.get_all_opportunities(profile_id)

        return {
            "profile_id": profile_id,
            "stage_filter": stage,
            "total_opportunities": len(opportunities),
            "opportunities": [{
                # Core opportunity fields (standardized schema)
                "opportunity_id": opp.opportunity_id,
                "organization_name": opp.organization_name,
                "funnel_stage": opp.funnel_stage.value,
                "source_type": opp.source_type.value,
                "discovery_source": opp.discovery_source,

                # Opportunity details
                "program_name": getattr(opp, 'program_name', None),
                "description": getattr(opp, 'description', None),
                "funding_amount": opp.funding_amount,
                "application_deadline": getattr(opp, 'application_deadline', None),

                # Scoring fields (standardized)
                "raw_score": getattr(opp, 'raw_score', 0.0),
                "compatibility_score": opp.compatibility_score,
                "confidence_level": getattr(opp, 'confidence_level', 0.0),

                # Advanced scoring (for candidates/targets/opportunities)
                "xml_990_score": getattr(opp, 'xml_990_score', None),
                "network_score": getattr(opp, 'network_score', None),
                "enhanced_score": getattr(opp, 'enhanced_score', None),
                "combined_score": getattr(opp, 'combined_score', None),

                # Metadata
                "is_schedule_i_grantee": getattr(opp, 'is_schedule_i_grantee', False),
                "discovered_at": opp.discovered_at.isoformat() if hasattr(opp, 'discovered_at') and opp.discovered_at else None,
                "stage_updated_at": opp.stage_updated_at.isoformat() if opp.stage_updated_at else None,
                "stage_notes": opp.stage_notes,

                # Contact and location info
                "contact_info": getattr(opp, 'contact_info', {}),
                "geographic_info": getattr(opp, 'geographic_info', {}),

                # Analysis factors
                "match_factors": getattr(opp, 'match_factors', {}),
                "risk_factors": getattr(opp, 'risk_factors', {}),

                # Analysis status
                "analysis_status": getattr(opp, 'analysis_status', {}),
                "strategic_analysis": getattr(opp, 'strategic_analysis', {}),
                "ai_analyzed": getattr(opp, 'ai_analyzed', False),
                "ai_processing": getattr(opp, 'ai_processing', False),
                "ai_error": getattr(opp, 'ai_error', False),
                "ai_summary": getattr(opp, 'ai_summary', None),
                "action_plan": getattr(opp, 'action_plan', None),

                # Legacy support
                "stage_color": opp.get_stage_color() if hasattr(opp, 'get_stage_color') else None
            } for opp in opportunities]
        }

    except Exception as e:
        logger.error(f"Failed to get profile opportunities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{profile_id}/opportunities/{opportunity_id}/stage")
async def update_opportunity_stage(
    profile_id: str,
    opportunity_id: str,
    stage_data: dict
):
    """Update opportunity funnel stage."""
    try:
        from src.discovery.funnel_manager import funnel_manager
        from src.discovery.base_discoverer import FunnelStage

        new_stage = stage_data.get("stage")
        notes = stage_data.get("notes")

        if not new_stage:
            raise HTTPException(status_code=400, detail="Stage is required")

        try:
            stage_enum = FunnelStage(new_stage)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid stage: {new_stage}")

        success = funnel_manager.set_opportunity_stage(
            profile_id, opportunity_id, stage_enum, notes
        )

        if not success:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        return {
            "success": True,
            "profile_id": profile_id,
            "opportunity_id": opportunity_id,
            "new_stage": new_stage,
            "notes": notes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update opportunity stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{profile_id}/opportunities/{opportunity_id}/promote")
async def promote_opportunity(profile_id: str, opportunity_id: str, notes_data: dict = None):
    """Promote opportunity to next funnel stage."""
    try:
        from src.discovery.funnel_manager import funnel_manager

        notes = notes_data.get("notes") if notes_data else None
        success = funnel_manager.promote_opportunity(profile_id, opportunity_id, notes)

        if not success:
            raise HTTPException(status_code=400, detail="Cannot promote opportunity (already at highest stage or not found)")

        return {
            "success": True,
            "profile_id": profile_id,
            "opportunity_id": opportunity_id,
            "action": "promoted",
            "notes": notes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to promote opportunity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{profile_id}/opportunities/{opportunity_id}/demote")
async def demote_opportunity(profile_id: str, opportunity_id: str, notes_data: dict = None):
    """Demote opportunity to previous funnel stage."""
    try:
        from src.discovery.funnel_manager import funnel_manager

        notes = notes_data.get("notes") if notes_data else None
        success = funnel_manager.demote_opportunity(profile_id, opportunity_id, notes)

        if not success:
            raise HTTPException(status_code=400, detail="Cannot demote opportunity (already at lowest stage or not found)")

        return {
            "success": True,
            "profile_id": profile_id,
            "opportunity_id": opportunity_id,
            "action": "demoted",
            "notes": notes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to demote opportunity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{profile_id}/metrics")
async def get_funnel_metrics(profile_id: str):
    """Get funnel conversion analytics for a profile."""
    try:
        from src.discovery.funnel_manager import FunnelManager

        if not hasattr(get_funnel_metrics, '_funnel_manager'):
            get_funnel_metrics._funnel_manager = FunnelManager()
        funnel_manager = get_funnel_metrics._funnel_manager

        metrics = funnel_manager.get_funnel_metrics(profile_id)
        return metrics

    except Exception as e:
        logger.error(f"Failed to get funnel metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{profile_id}/recommendations")
async def get_stage_recommendations(profile_id: str):
    """Get recommendations for stage transitions."""
    try:
        from src.discovery.funnel_manager import FunnelManager

        if not hasattr(get_stage_recommendations, '_funnel_manager'):
            get_stage_recommendations._funnel_manager = FunnelManager()
        funnel_manager = get_stage_recommendations._funnel_manager

        recommendations = funnel_manager.get_stage_recommendations(profile_id)
        return {
            "profile_id": profile_id,
            "recommendations": recommendations
        }

    except Exception as e:
        logger.error(f"Failed to get stage recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{profile_id}/bulk-transition")
async def bulk_stage_transition(profile_id: str, transition_data: dict):
    """Bulk transition multiple opportunities to target stage."""
    try:
        from src.discovery.funnel_manager import funnel_manager
        from src.discovery.base_discoverer import FunnelStage

        opportunity_ids = transition_data.get("opportunity_ids", [])
        target_stage = transition_data.get("target_stage")
        notes = transition_data.get("notes")

        if not opportunity_ids:
            raise HTTPException(status_code=400, detail="opportunity_ids is required")

        if not target_stage:
            raise HTTPException(status_code=400, detail="target_stage is required")

        try:
            stage_enum = FunnelStage(target_stage)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid stage: {target_stage}")

        results = funnel_manager.bulk_stage_transition(
            profile_id, opportunity_ids, stage_enum, notes
        )

        return {
            "profile_id": profile_id,
            "target_stage": target_stage,
            "results": results,
            "successful_transitions": sum(1 for success in results.values() if success),
            "total_opportunities": len(opportunity_ids)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform bulk stage transition: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
