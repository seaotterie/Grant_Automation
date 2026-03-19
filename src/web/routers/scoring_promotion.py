"""
Scoring, Promotion & Enhanced Data API Router

Extracted from main.py - handles opportunity scoring, promotion (manual & automated),
and enhanced 990/990-PF data integration endpoints.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.web.services.scoring_service import (
    get_scoring_service, ScoreRequest, ScoreResponse,
    PromotionRequest, PromotionResponse, BulkPromotionRequest, BulkPromotionResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Scoring & Promotion"])

# ---------------------------------------------------------------------------
# Lazy-loaded service accessors
# ---------------------------------------------------------------------------

def _get_profile_service():
    from src.profiles.unified_service import get_unified_profile_service
    return get_unified_profile_service()

def _get_unified_service():
    from src.profiles.unified_service import get_unified_profile_service
    return get_unified_profile_service()

def _get_database_path() -> str:
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    return os.path.join(project_root, "data", "catalynx.db")

def _get_database_service():
    from src.database.database_manager import DatabaseManager
    return DatabaseManager(_get_database_path())


# =====================================
# SCORING & PROMOTION API ENDPOINTS
# =====================================

@router.post("/profiles/{profile_id}/opportunities/{opportunity_id}/score", response_model=ScoreResponse)
async def score_opportunity(profile_id: str, opportunity_id: str, request: ScoreRequest):
    """Score an opportunity against a profile"""
    scoring_service = get_scoring_service()
    return await scoring_service.score_opportunity(profile_id, opportunity_id, request)


@router.post("/profiles/{profile_id}/opportunities/{opportunity_id}/promote", response_model=PromotionResponse)
async def promote_opportunity(profile_id: str, opportunity_id: str, request: PromotionRequest):
    """Promote or demote an opportunity using unified service"""
    try:
        # Get database manager for direct access
        from src.database.database_manager import DatabaseManager
        database_path = _get_database_path()
        db_manager = DatabaseManager(database_path)

        # Get current opportunity from database directly
        logger.info(f"Looking for opportunity {opportunity_id} in profile {profile_id} via database")
        opportunity_data = db_manager.get_opportunity(profile_id, opportunity_id)
        logger.info(f"Database found opportunity: {opportunity_data is not None}")

        if opportunity_data:
            # SIMPLIFIED: Database now uses business terms directly
            stage_progression = {
                "prospects": "qualified",
                "qualified": "candidates",
                "candidates": "targets",
                "targets": "opportunities",
                "opportunities": "opportunities"  # Stay in final stage
            }

            # Get current stage from database (now in business terms)
            current_stage = opportunity_data.get('current_stage', 'prospects')
            logger.info(f"Current stage: {current_stage}")

            # Determine target stage based on action
            if request.action == "promote":
                target_stage = stage_progression.get(current_stage, current_stage)
            elif request.action == "demote":
                # Reverse progression for demotion
                stage_regression = {
                    "opportunities": "targets",
                    "targets": "candidates",
                    "candidates": "qualified",
                    "qualified": "prospects",
                    "prospects": "prospects"  # Stay at lowest stage
                }
                target_stage = stage_regression.get(current_stage, current_stage)
            else:
                raise HTTPException(status_code=400, detail="Action must be 'promote' or 'demote'")

            logger.info(f"Target stage: {target_stage}")

            if target_stage != current_stage:
                # Update database directly with business term
                logger.info(f"Updating stage: {current_stage} → {target_stage}")
                success = db_manager.update_opportunity_stage(
                    profile_id,
                    opportunity_id,
                    target_stage,
                    reason=f"Manual {request.action} via API - {current_stage} → {target_stage}",
                    promoted_by="web_user"
                )
                logger.info(f"Database update result: {success}")

                if success:
                    return PromotionResponse(
                        decision="approved",
                        reason=f"Manual {request.action} to {target_stage}",
                        current_score=opportunity_data.get('overall_score', 0.5),
                        target_stage=target_stage,
                        confidence_level=0.95,
                        requires_manual_review=False,
                        promotion_metadata={"source": "database_direct", "original_stage": current_stage, "action": request.action}
                    )
                else:
                    return PromotionResponse(
                        decision="failed",
                        reason="Failed to update stage in database",
                        current_score=opportunity_data.get('overall_score', 0.5),
                        target_stage=current_stage,
                        confidence_level=0.1,
                        requires_manual_review=True,
                        promotion_metadata={"error": "database_update_failed", "action": request.action}
                    )
            else:
                # Determine appropriate no-change message
                if request.action == "promote":
                    reason = f"Already at highest stage: {current_stage}"
                elif request.action == "demote":
                    reason = f"Already at lowest stage: {current_stage}"
                else:
                    reason = f"No stage change needed: {current_stage}"

                return PromotionResponse(
                    decision="no_change",
                    reason=reason,
                    current_score=opportunity_data.get('overall_score', 0.5),
                    target_stage=current_stage,
                    confidence_level=0.8,
                    requires_manual_review=False,
                    promotion_metadata={"status": "already_at_target", "action": request.action}
                )
        else:
            logger.warning(f"Opportunity {opportunity_id} not found in database for profile {profile_id}")
            return PromotionResponse(
                decision="error",
                reason=f"Opportunity not found: {opportunity_id}",
                current_score=0.0,
                target_stage="unknown",
                confidence_level=0.0,
                requires_manual_review=True,
                promotion_metadata={"error": "opportunity_not_found", "opportunity_id": opportunity_id}
            )

    except Exception as e:
        logger.error(f"Error promoting opportunity {opportunity_id}: {e}")
        return PromotionResponse(
            decision="error",
            reason=f"System error: {str(e)}",
            current_score=0.0,
            target_stage="unknown",
            confidence_level=0.0,
            requires_manual_review=True,
            promotion_metadata={"error": str(e), "error_type": type(e).__name__}
        )


@router.post("/profiles/{profile_id}/opportunities/{opportunity_id}/evaluate", response_model=PromotionResponse)
async def evaluate_promotion(profile_id: str, opportunity_id: str, request: PromotionRequest):
    """Evaluate promotion eligibility without applying changes"""
    scoring_service = get_scoring_service()
    return await scoring_service.evaluate_promotion(profile_id, opportunity_id, request)


@router.get("/profiles/{profile_id}/opportunities/{opportunity_id}/details")
async def get_opportunity_details(profile_id: str, opportunity_id: str):
    """Get detailed opportunity information using unified service"""
    try:
        # Try unified service first for complete data
        unified_service = _get_unified_service()
        opportunity = unified_service.get_opportunity(profile_id, opportunity_id)
        if opportunity:
            return {
                "opportunity": opportunity.model_dump(),
                "source": "unified_service"
            }

        # Fallback to scoring service
        scoring_service = get_scoring_service()

        # Get opportunity data (placeholder implementation)
        opportunity_data = await scoring_service._get_opportunity_data(profile_id, opportunity_id)
        if not opportunity_data:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        # Get current score if available
        current_score = await scoring_service._get_current_score(profile_id, opportunity_id, opportunity_data)

        # Get promotion evaluation
        promotion_request = PromotionRequest(action="evaluate")
        promotion_eval = await scoring_service.evaluate_promotion(profile_id, opportunity_id, promotion_request)

        return {
            "opportunity_data": opportunity_data,
            "current_score": scoring_service._format_score_response(current_score) if current_score else None,
            "promotion_evaluation": promotion_eval,
            "stage_progression": {
                "current": opportunity_data.get('funnel_stage', 'prospects'),
                "next": scoring_service._get_next_stage(opportunity_data.get('funnel_stage', 'prospects')),
                "previous": scoring_service._get_previous_stage(opportunity_data.get('funnel_stage', 'prospects'))
            }
        }

    except Exception as e:
        logger.error(f"Error getting opportunity details: {e}")
        logger.error(f"Failed to get opportunity details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/profiles/{profile_id}/opportunities/{opportunity_id}")
async def delete_opportunity(profile_id: str, opportunity_id: str):
    """Delete a specific opportunity from a profile"""
    try:
        logger.info(f"DELETE request: profile_id={profile_id}, opportunity_id={opportunity_id}")

        # Validate profile exists
        profile_service = _get_profile_service()
        profile = profile_service.get_profile(profile_id)
        if not profile:
            logger.warning(f"Profile not found: {profile_id}")
            return JSONResponse(
                status_code=404,
                content={"error": "Profile not found", "profile_id": profile_id}
            )

        logger.info(f"Profile found: {profile_id}")

        # Delete the opportunity using profile service
        success = profile_service.delete_lead(opportunity_id, profile_id)
        logger.info(f"Delete result: {success}")

        if not success:
            logger.warning(f"Opportunity not found for deletion: {opportunity_id}")
            return JSONResponse(
                status_code=404,
                content={"error": "Opportunity not found", "opportunity_id": opportunity_id}
            )

        logger.info(f"Successfully deleted opportunity {opportunity_id} from profile {profile_id}")

        response_data = {
            "success": True,
            "message": "Opportunity deleted successfully",
            "profile_id": profile_id,
            "opportunity_id": opportunity_id,
            "deleted_at": datetime.now().isoformat()
        }
        logger.info(f"Returning response: {response_data}")
        return response_data

    except Exception as e:
        logger.error(f"Error deleting opportunity {opportunity_id} from profile {profile_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "opportunity_id": opportunity_id}
        )


@router.post("/profiles/{profile_id}/opportunities/bulk-promote", response_model=BulkPromotionResponse)
async def bulk_promote_opportunities(profile_id: str, request: BulkPromotionRequest):
    """Bulk promote multiple opportunities"""
    scoring_service = get_scoring_service()
    return await scoring_service.bulk_promote(profile_id, request)


@router.get("/profiles/{profile_id}/promotion-candidates")
async def get_promotion_candidates(profile_id: str, stage: str = "prospects", limit: int = 50):
    """Get opportunities that are candidates for promotion"""
    scoring_service = get_scoring_service()
    return await scoring_service.get_promotion_candidates(profile_id, stage, limit)


@router.get("/profiles/{profile_id}/promotion-history")
async def get_promotion_history(profile_id: str, opportunity_id: Optional[str] = None, limit: int = 100):
    """Get promotion history for a profile or specific opportunity"""
    try:
        scoring_service = get_scoring_service()
        history = scoring_service.promotion_engine.get_promotion_history(opportunity_id, limit)

        # Convert to serializable format
        history_data = []
        for record in history:
            history_data.append({
                "opportunity_id": record.opportunity_id,
                "from_stage": record.from_stage,
                "to_stage": record.to_stage,
                "decision": record.decision.value,
                "reason": record.reason.value,
                "score_at_promotion": record.score_at_promotion,
                "promoted_by": record.promoted_by,
                "promoted_at": record.promoted_at.isoformat(),
                "metadata": record.metadata
            })

        return {
            "profile_id": profile_id,
            "history": history_data,
            "total_records": len(history_data)
        }

    except Exception as e:
        logger.error(f"Error getting promotion history: {e}")
        logger.error(f"Failed to get promotion history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ===============================================================================
# AUTOMATED PROMOTION ENGINE ENDPOINTS
# ===============================================================================

@router.post("/profiles/{profile_id}/automated-promotion/process")
async def process_automated_promotion(
    profile_id: str,
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """Process opportunities for automated scoring and promotion"""
    try:
        from src.web.services.automated_promotion_service import get_automated_promotion_service

        service = get_automated_promotion_service()

        opportunities = request.get("opportunities", [])
        discovery_source = request.get("discovery_source", "unknown")

        if not opportunities:
            raise HTTPException(status_code=400, detail="No opportunities provided")

        logger.info(f"Processing {len(opportunities)} opportunities for automated promotion")

        result = await service.process_discovery_results(profile_id, opportunities, discovery_source)

        return {
            "profile_id": profile_id,
            "discovery_source": discovery_source,
            "result": {
                "total_processed": result.total_processed,
                "promoted_count": result.promoted_count,
                "scored_count": result.scored_count,
                "error_count": result.error_count,
                "processing_time": result.processing_time,
                "promotion_details": result.promotion_details[:10],  # Limit to first 10 for response size
                "errors": result.errors[:5]  # Limit to first 5 errors
            },
            "success_rate": ((result.total_processed - result.error_count) / max(result.total_processed, 1)) * 100,
            "processed_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in automated promotion processing: {e}")
        logger.error(f"Automated promotion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/profiles/{profile_id}/automated-promotion/candidates")
async def get_automated_promotion_candidates(
    profile_id: str,
    stage: str = "prospects",
    limit: int = 50
) -> Dict[str, Any]:
    """Get opportunities that are candidates for automated promotion"""
    try:
        from src.web.services.automated_promotion_service import get_automated_promotion_service

        service = get_automated_promotion_service()
        candidates = await service.get_promotion_candidates(profile_id, stage, limit)

        return {
            "profile_id": profile_id,
            "stage": stage,
            "candidates": candidates,
            "total_candidates": len(candidates),
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting promotion candidates: {e}")
        logger.error(f"Failed to get candidates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/profiles/{profile_id}/automated-promotion/bulk-promote")
async def automated_bulk_promote_opportunities(
    profile_id: str,
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """Bulk promote multiple opportunities using automated scoring"""
    try:
        from src.web.services.automated_promotion_service import get_automated_promotion_service

        service = get_automated_promotion_service()

        opportunity_ids = request.get("opportunity_ids", [])
        user_id = request.get("user_id", "web_user")

        if not opportunity_ids:
            raise HTTPException(status_code=400, detail="No opportunity IDs provided")

        logger.info(f"Bulk promoting {len(opportunity_ids)} opportunities")

        result = await service.bulk_promote_candidates(profile_id, opportunity_ids, user_id)

        return {
            "profile_id": profile_id,
            "bulk_promotion_result": result,
            "processed_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in bulk promotion: {e}")
        logger.error(f"Bulk promotion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/automated-promotion/stats")
async def get_automated_promotion_stats() -> Dict[str, Any]:
    """Get automated promotion service statistics and configuration"""
    try:
        from src.web.services.automated_promotion_service import get_automated_promotion_service

        service = get_automated_promotion_service()
        stats = service.get_processing_stats()

        return {
            "service_stats": stats,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting automated promotion stats: {e}")
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/automated-promotion/config")
async def update_automated_promotion_config(request: Dict[str, Any]) -> Dict[str, Any]:
    """Update automated promotion service configuration"""
    try:
        from src.web.services.automated_promotion_service import get_automated_promotion_service

        service = get_automated_promotion_service()
        service.update_config(request)

        updated_stats = service.get_processing_stats()

        return {
            "message": "Configuration updated successfully",
            "updated_config": updated_stats["config"],
            "updated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error updating automated promotion config: {e}")
        logger.error(f"Failed to update config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ===============================================================================
# ENHANCED DATA SERVICE ENDPOINTS (990/990-PF Integration)
# ===============================================================================

@router.post("/profiles/{profile_id}/opportunities/{opportunity_id}/enhanced-data")
async def fetch_enhanced_data_for_opportunity(
    profile_id: str,
    opportunity_id: str,
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """Fetch enhanced 990/990-PF data for a specific opportunity"""
    try:
        from src.web.services.enhanced_data_service import get_enhanced_data_service

        service = get_enhanced_data_service()

        opportunity_data = request.get("opportunity_data", {})
        score = request.get("score", 0.0)

        if not opportunity_data:
            raise HTTPException(status_code=400, detail="Opportunity data required")

        logger.info(f"Fetching enhanced data for opportunity {opportunity_id}")

        enhanced_result = await service.fetch_enhanced_data_for_opportunity(opportunity_data, score)

        if enhanced_result:
            return {
                "profile_id": profile_id,
                "opportunity_id": opportunity_id,
                "enhanced_data": {
                    "has_990_data": enhanced_result.has_990_data,
                    "has_990_pf_data": enhanced_result.has_990_pf_data,
                    "financial_data": enhanced_result.financial_data,
                    "foundation_data": enhanced_result.foundation_data,
                    "board_data": enhanced_result.board_data,
                    "boost_factors": enhanced_result.boost_factors,
                    "data_completeness": enhanced_result.data_completeness,
                    "processing_time": enhanced_result.processing_time,
                    "fetched_at": enhanced_result.fetched_at.isoformat()
                },
                "success": True
            }
        else:
            return {
                "profile_id": profile_id,
                "opportunity_id": opportunity_id,
                "enhanced_data": None,
                "success": False,
                "message": "No enhanced data available or score below threshold"
            }

    except Exception as e:
        logger.error(f"Error fetching enhanced data: {e}")
        logger.error(f"Enhanced data fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/profiles/{profile_id}/opportunities/enhanced-data/batch")
async def fetch_enhanced_data_batch(
    profile_id: str,
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """Fetch enhanced data for a batch of opportunities"""
    try:
        from src.web.services.enhanced_data_service import get_enhanced_data_service

        service = get_enhanced_data_service()

        opportunities = request.get("opportunities", [])
        scores = request.get("scores", [])

        if not opportunities:
            raise HTTPException(status_code=400, detail="Opportunities list required")

        logger.info(f"Fetching enhanced data for batch of {len(opportunities)} opportunities")

        enhanced_results = await service.fetch_enhanced_data_batch(opportunities, scores)

        # Format results for API response
        formatted_results = []
        for result in enhanced_results:
            formatted_results.append({
                "opportunity_id": result.opportunity_id,
                "organization_name": result.organization_name,
                "ein": result.ein,
                "has_990_data": result.has_990_data,
                "has_990_pf_data": result.has_990_pf_data,
                "boost_factors": result.boost_factors,
                "data_completeness": result.data_completeness,
                "processing_time": result.processing_time,
                "error_message": result.error_message
            })

        return {
            "profile_id": profile_id,
            "batch_size": len(opportunities),
            "successful_results": len(enhanced_results),
            "results": formatted_results,
            "processed_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in batch enhanced data fetch: {e}")
        logger.error(f"Batch enhanced data fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/enhanced-data/stats")
async def get_enhanced_data_stats() -> Dict[str, Any]:
    """Get enhanced data service statistics"""
    try:
        from src.web.services.enhanced_data_service import get_enhanced_data_service

        service = get_enhanced_data_service()
        stats = service.get_statistics()

        return {
            "service_stats": stats,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting enhanced data stats: {e}")
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/enhanced-data/config")
async def update_enhanced_data_config(request: Dict[str, Any]) -> Dict[str, Any]:
    """Update enhanced data service configuration"""
    try:
        from src.web.services.enhanced_data_service import get_enhanced_data_service

        service = get_enhanced_data_service()
        service.update_config(request)

        updated_stats = service.get_statistics()

        return {
            "message": "Enhanced data configuration updated successfully",
            "updated_config": updated_stats["config"],
            "updated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error updating enhanced data config: {e}")
        logger.error(f"Failed to update config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/enhanced-data/cache")
async def clear_enhanced_data_cache() -> Dict[str, Any]:
    """Clear the enhanced data cache"""
    try:
        from src.web.services.enhanced_data_service import get_enhanced_data_service

        service = get_enhanced_data_service()
        cache_size = len(service.data_cache)
        service.clear_cache()

        return {
            "message": f"Enhanced data cache cleared ({cache_size} entries removed)",
            "cleared_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error clearing enhanced data cache: {e}")
        logger.error(f"Failed to clear cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
