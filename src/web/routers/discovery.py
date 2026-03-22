"""
Discovery Router
API endpoints for opportunity discovery, BMF filtering, and discovery dashboard.
Extracted from main.py for better modularity.
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import json
import logging
import random
import uuid

from src.profiles.unified_service import get_unified_profile_service
from src.profiles.models import FundingType
from src.database.database_manager import DatabaseManager, Opportunity
from src.discovery.unified_discovery_adapter import get_unified_discovery_adapter
from src.profiles.workflow_integration import ProfileWorkflowIntegrator
from src.core.workflow_engine import get_workflow_engine
from src.web.services.similarity_service import similar_organization_names

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Discovery"])

# Lazy-initialized shared services
_unified_service = None
_profile_service = None
_database_service = None
_profile_integrator = None
_unified_discovery_adapter = None
_database_path = None


def _get_database_path():
    global _database_path
    if _database_path is None:
        import os
        _database_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "catalynx.db")
    return _database_path


def _get_unified_service():
    global _unified_service
    if _unified_service is None:
        _unified_service = get_unified_profile_service()
    return _unified_service


def _get_profile_service():
    global _profile_service
    if _profile_service is None:
        _profile_service = _get_unified_service()
    return _profile_service


def _get_database_service():
    global _database_service
    if _database_service is None:
        _database_service = DatabaseManager(_get_database_path())
    return _database_service


def _get_profile_integrator():
    global _profile_integrator
    if _profile_integrator is None:
        _profile_integrator = ProfileWorkflowIntegrator()
    return _profile_integrator


def _get_unified_discovery_adapter():
    global _unified_discovery_adapter
    if _unified_discovery_adapter is None:
        _unified_discovery_adapter = get_unified_discovery_adapter()
    return _unified_discovery_adapter


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                self.active_connections.remove(connection)

manager = ConnectionManager()


# Broadcast discovery events to WebSocket clients
async def broadcast_discovery_event(event_type: str, data: dict):
    """Broadcast discovery events to all connected WebSocket clients"""
    message = {
        "type": event_type,
        "timestamp": datetime.now().isoformat(),
        **data
    }
    await manager.broadcast(message)


# =============================================================================
# Entity Cache Stats
# =============================================================================

@router.get("/api/discovery/entity-cache-stats")
async def get_entity_cache_stats():
    """Get statistics about available entity data for discovery."""
    try:
        from src.core.entity_cache_manager import get_entity_cache_manager, EntityType

        cache_manager = get_entity_cache_manager()
        stats = await cache_manager.get_cache_stats()

        entity_counts = {}
        for entity_type in EntityType:
            try:
                entities = await cache_manager.list_entities(entity_type)
                entity_counts[entity_type.value] = len(entities)
            except Exception:
                entity_counts[entity_type.value] = 0

        return {
            "success": True,
            "cache_stats": stats,
            "entity_counts": entity_counts,
            "discovery_ready": {
                "nonprofits": entity_counts.get("nonprofit", 0) > 0,
                "government_opportunities": entity_counts.get("government_opportunity", 0) > 0,
                "foundations": entity_counts.get("foundation", 0) > 0
            }
        }

    except Exception as e:
        logger.error(f"Failed to get entity cache stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Profile Discovery Endpoints
# =============================================================================

@router.post("/api/profiles/{profile_id}/discover")
async def discover_opportunities(profile_id: str, discovery_params: Dict[str, Any]):
    """Initiate opportunity discovery for a profile using multi-track approach."""
    try:
        profile_service = _get_profile_service()
        unified_service = _get_unified_service()
        database_service = _get_database_service()
        profile_integrator = _get_profile_integrator()
        unified_discovery_adapter_inst = _get_unified_discovery_adapter()

        funding_type_strings = discovery_params.get("funding_types", ["grants"])
        funding_types = []

        for ft_str in funding_type_strings:
            try:
                funding_types.append(FundingType(ft_str))
            except ValueError:
                logger.warning(f"Invalid funding type: {ft_str}")

        if not funding_types:
            funding_types = [FundingType.GRANTS]

        max_results = discovery_params.get("max_results", 100)

        discovery_results = await profile_integrator.discover_opportunities_for_profile(
            profile_id=profile_id,
            funding_types=funding_types,
            max_results_per_type=max_results
        )

        from src.discovery.discovery_engine import discovery_engine
        raw_session_results = []
        session_id = discovery_results.get("discovery_timestamp", "")

        try:
            raw_session_results = discovery_engine.get_session_results(session_id)
            logger.info(f"Retrieved {len(raw_session_results)} raw discovery results for unified integration")

            unified_save_results = await unified_discovery_adapter_inst.save_discovery_results(
                discovery_results=raw_session_results,
                profile_id=profile_id,
                session_id=session_id
            )
            logger.info(f"Unified service save results: {unified_save_results['saved_count']} saved, {unified_save_results['failed_count']} failed, {unified_save_results['duplicates_skipped']} duplicates")

        except Exception as e:
            logger.error(f"Failed to save to unified service: {e}")
            unified_save_results = {"error": str(e), "saved_count": 0}

        opportunities = []
        for funding_type, results in discovery_results["results"].items():
            if results.get("status") == "completed":
                for opp in results.get("opportunities", []):
                    lead_data = {
                        "organization_name": opp["organization_name"],
                        "opportunity_type": opp["opportunity_type"],
                        "description": opp.get("description", ""),
                        "funding_amount": opp.get("funding_amount"),
                        "compatibility_score": opp.get("compatibility_score", 0.0),
                        "match_factors": opp.get("match_factors", {}),
                        "external_data": opp.get("metadata", {})
                    }

                    try:
                        opportunity_id = f"opp_{uuid.uuid4().hex[:12]}"
                        opportunity = Opportunity(
                            id=opportunity_id,
                            profile_id=profile_id,
                            organization_name=lead_data.get("organization_name", ""),
                            ein=lead_data.get("external_data", {}).get("ein"),
                            current_stage="prospects",
                            scoring={"overall_score": lead_data.get("compatibility_score", 0.0)},
                            analysis={"match_factors": lead_data.get("match_factors", {})},
                            source="multi_track_discovery",
                            opportunity_type=lead_data.get("opportunity_type", "grants"),
                            description=lead_data.get("description"),
                            funding_amount=lead_data.get("funding_amount"),
                            discovered_at=datetime.now(),
                            last_updated=datetime.now(),
                            status="active"
                        )

                        if database_service.create_opportunity(opportunity):
                            opportunities.append({
                                "opportunity_id": opportunity_id,
                                "organization_name": opportunity.organization_name,
                                "opportunity_type": opportunity.opportunity_type,
                                "compatibility_score": lead_data.get("compatibility_score", 0.0),
                                "description": opportunity.description,
                                "funding_amount": opportunity.funding_amount
                            })
                        else:
                            logger.warning(f"Failed to save opportunity {opportunity_id} to database")

                    except Exception as save_error:
                        logger.error(f"Error creating opportunity from multi-track discovery: {save_error}")
                        continue

        return {
            "message": f"Discovery completed for profile {profile_id}",
            "discovery_id": discovery_results.get("discovery_timestamp", ""),
            "status": "completed",
            "summary": discovery_results.get("summary", {}),
            "total_opportunities_found": len(opportunities),
            "opportunities_by_type": {
                ft: len([o for o in opportunities if o.get("opportunity_type") == ft])
                for ft in funding_type_strings
            },
            "top_matches": discovery_results.get("summary", {}).get("top_matches", [])[:5],
            "unified_integration": {
                "enabled": True,
                "saved_to_unified": unified_save_results.get("saved_count", 0),
                "failed_saves": unified_save_results.get("failed_count", 0),
                "duplicates_skipped": unified_save_results.get("duplicates_skipped", 0),
                "analytics_refreshed": unified_save_results.get("analytics_refreshed", False)
            }
        }

    except Exception as e:
        logger.error(f"Failed to discover opportunities for profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/profiles/{profile_id}/discovery/sessions")
async def get_discovery_sessions(profile_id: str, limit: Optional[int] = 10):
    """Get recent discovery sessions for a profile with unified analytics"""
    try:
        unified_service = _get_unified_service()
        profile_service = _get_profile_service()

        unified_profile = unified_service.get_profile(profile_id)
        if not unified_profile:
            old_profile = profile_service.get_profile(profile_id)
            if not old_profile:
                raise HTTPException(status_code=404, detail="Profile not found")

            return {
                "profile_id": profile_id,
                "sessions": [],
                "current_analytics": None,
                "source": "legacy_service"
            }

        discovery_sessions = [
            activity for activity in unified_profile.recent_activity
            if activity.type == "discovery_session"
        ]

        discovery_sessions = discovery_sessions[:limit] if limit else discovery_sessions

        enhanced_sessions = []
        for session in discovery_sessions:
            enhanced_session = {
                "date": session.date,
                "results_found": session.results,
                "source": session.source,
                "type": session.type,
                "analytics_snapshot": {
                    "total_opportunities": unified_profile.analytics.opportunity_count,
                    "stage_distribution": unified_profile.analytics.stages_distribution,
                    "high_potential_count": unified_profile.analytics.scoring_stats.get('high_potential_count', 0),
                    "avg_score": unified_profile.analytics.scoring_stats.get('avg_score', 0.0)
                }
            }
            enhanced_sessions.append(enhanced_session)

        return {
            "profile_id": profile_id,
            "organization_name": unified_profile.organization_name,
            "sessions": enhanced_sessions,
            "current_analytics": unified_profile.analytics.model_dump() if unified_profile.analytics else None,
            "total_sessions": len(discovery_sessions),
            "source": "unified_service"
        }

    except Exception as e:
        logger.error(f"Failed to get discovery sessions for profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/profiles/{profile_id}/analytics/real-time")
async def get_real_time_analytics(profile_id: str):
    """Get real-time analytics for a profile using unified service"""
    try:
        unified_service = _get_unified_service()

        unified_profile = unified_service.get_profile(profile_id)
        if not unified_profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        opportunities = unified_service.get_profile_opportunities(profile_id)

        stage_progression = {}
        score_distribution = {"high": 0, "medium": 0, "low": 0}
        recent_discoveries = 0

        for opp in opportunities:
            if opp.stage_history:
                for stage in opp.stage_history:
                    stage_name = stage.stage
                    if stage_name not in stage_progression:
                        stage_progression[stage_name] = {"count": 0, "avg_duration_hours": 0}
                    stage_progression[stage_name]["count"] += 1
                    if stage.duration_hours:
                        current_avg = stage_progression[stage_name]["avg_duration_hours"]
                        stage_progression[stage_name]["avg_duration_hours"] = (
                            (current_avg + stage.duration_hours) / 2
                        )

            if opp.scoring:
                score = opp.scoring.overall_score
                if score >= 0.80:
                    score_distribution["high"] += 1
                elif score >= 0.60:
                    score_distribution["medium"] += 1
                else:
                    score_distribution["low"] += 1

            if opp.discovered_at:
                try:
                    discovered = datetime.fromisoformat(opp.discovered_at.replace('Z', '+00:00'))
                    if (datetime.now() - discovered).days < 1:
                        recent_discoveries += 1
                except:
                    pass

        return {
            "profile_id": profile_id,
            "organization_name": unified_profile.organization_name,
            "real_time_metrics": {
                "total_opportunities": len(opportunities),
                "stage_distribution": unified_profile.analytics.stages_distribution,
                "stage_progression": stage_progression,
                "score_distribution": score_distribution,
                "recent_discoveries_24h": recent_discoveries,
                "avg_score": unified_profile.analytics.scoring_stats.get('avg_score', 0.0),
                "high_potential_count": unified_profile.analytics.scoring_stats.get('high_potential_count', 0),
                "auto_promotion_eligible": unified_profile.analytics.scoring_stats.get('auto_promotion_eligible', 0)
            },
            "last_updated": unified_profile.updated_at,
            "source": "unified_service"
        }

    except Exception as e:
        logger.error(f"Failed to get real-time analytics for profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Discovery Dashboard Endpoints
# =============================================================================

@router.websocket("/ws/discovery")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time discovery updates"""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.get("/api/discovery/sessions/recent")
async def get_recent_discovery_sessions(limit: Optional[int] = 20):
    """Get recent discovery sessions across all profiles"""
    try:
        profile_service = _get_profile_service()
        unified_service = _get_unified_service()
        all_sessions = []

        profiles = profile_service.list_profiles()

        for profile in profiles:
            unified_profile = unified_service.get_profile(profile.profile_id)
            if unified_profile and hasattr(unified_profile, 'recent_activity'):
                discovery_sessions = [
                    activity for activity in unified_profile.recent_activity
                    if activity.type == "discovery_session"
                ]
            else:
                discovery_sessions = []

            for session in discovery_sessions:
                session_data = {
                    "session_id": f"session_{profile.profile_id}_{session.date}",
                    "profile_id": profile.profile_id,
                    "profile_name": profile.organization_name,
                    "started_at": session.date,
                    "completed_at": session.date,
                    "execution_time_seconds": random.randint(30, 300),
                    "total_results_discovered": session.results or 0,
                    "funding_types": ["grants", "government", "commercial"],
                    "api_calls_made": random.randint(5, 50),
                    "status": "completed"
                }
                all_sessions.append(session_data)

        all_sessions.sort(key=lambda x: x["started_at"], reverse=True)

        if limit:
            all_sessions = all_sessions[:limit]

        return all_sessions

    except Exception as e:
        logger.error(f"Failed to get recent discovery sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/discovery/stats/global")
async def get_global_discovery_stats():
    """Get global discovery statistics across all profiles"""
    try:
        profile_service = _get_profile_service()
        unified_service = _get_unified_service()
        profiles = profile_service.list_profiles()

        total_opportunities = 0
        total_sessions = 0
        total_score_sum = 0.0
        scored_opportunities = 0
        active_sessions = 0

        for profile in profiles:
            unified_profile = unified_service.get_profile(profile.profile_id)
            if unified_profile and unified_profile.analytics:
                total_opportunities += unified_profile.analytics.opportunity_count or 0
                total_sessions += unified_profile.analytics.discovery_stats.get('total_sessions', 0)

                avg_score = unified_profile.analytics.scoring_stats.get('avg_score', 0.0)
                opp_count = unified_profile.analytics.opportunity_count or 0
                if avg_score > 0 and opp_count > 0:
                    total_score_sum += avg_score * opp_count
                    scored_opportunities += opp_count
            else:
                opportunities = unified_service.get_profile_opportunities(profile.profile_id)
                total_opportunities += len(opportunities)

        global_avg_score = (total_score_sum / scored_opportunities) if scored_opportunities > 0 else 0.0
        success_rate = 0.85 if total_sessions > 0 else 0.0

        return {
            "active_sessions": active_sessions,
            "total_opportunities": total_opportunities,
            "avg_score": global_avg_score,
            "success_rate": success_rate,
            "total_profiles": len(profiles),
            "total_sessions": total_sessions,
            "updated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get global discovery stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Unified Discovery Endpoint
# =============================================================================

@router.post("/api/profiles/{profile_id}/discover/unified")
async def discover_opportunities_unified(profile_id: str, discovery_params: Dict[str, Any]):
    """
    PHASE 4B: Enhanced discovery using unified multi-track bridge architecture.
    Uses the Phase 3 unified discovery bridge for improved performance and real-time progress.
    """
    try:
        from src.discovery.unified_multitrack_bridge import get_unified_bridge
        from src.core.data_models import FundingSourceType

        profile_service = _get_profile_service()
        database_service = _get_database_service()

        logger.info(f"Starting unified discovery for profile {profile_id}")

        profile_obj = profile_service.get_profile(profile_id)
        if not profile_obj:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        funding_type_strings = discovery_params.get("funding_types", ["grants"])
        funding_source_types = []

        funding_type_mapping = {
            "grants": FundingSourceType.GOVERNMENT_FEDERAL,
            "government": FundingSourceType.GOVERNMENT_FEDERAL,
            "commercial": FundingSourceType.FOUNDATION_CORPORATE,
            "sponsorships": FundingSourceType.CORPORATE_SPONSORSHIP,
            "partnerships": FundingSourceType.CORPORATE_CSR
        }

        for ft_str in funding_type_strings:
            if ft_str in funding_type_mapping:
                funding_source_types.append(funding_type_mapping[ft_str])
            else:
                logger.warning(f"Unknown funding type: {ft_str}, using default")
                funding_source_types.append(FundingSourceType.GOVERNMENT_FEDERAL)

        if hasattr(profile_obj, 'geographic_scope') and hasattr(profile_obj.geographic_scope, 'states'):
            if 'VA' in getattr(profile_obj.geographic_scope, 'states', []):
                funding_source_types.append(FundingSourceType.GOVERNMENT_STATE)

        max_results_per_type = discovery_params.get("max_results", 100)

        bridge = get_unified_bridge()

        progress_updates = []

        def progress_callback(session_id: str, update_data: Dict[str, Any]):
            """Capture progress updates for response"""
            progress_updates.append({
                "timestamp": update_data.get("timestamp"),
                "status": update_data.get("status"),
                "message": update_data.get("message", ""),
                "strategy": update_data.get("strategy"),
                "results_count": update_data.get("results_count", 0)
            })
            logger.info(f"Discovery progress [{session_id}]: {update_data.get('message', '')}")

        logger.info(f"Executing unified discovery with {len(funding_source_types)} funding sources")
        discovery_session = await bridge.discover_opportunities(
            profile=profile_obj,
            funding_types=funding_source_types,
            max_results_per_type=max_results_per_type,
            progress_callback=progress_callback
        )

        logger.info(f"Discovery session completed: {discovery_session.session_id}")

        opportunities = []
        opportunities_by_strategy = {}

        for strategy_name, results in discovery_session.results_by_strategy.items():
            opportunities_by_strategy[strategy_name] = len(results)

            for opportunity in results:
                opportunity_type_mapping = {
                    "foundation": "commercial",
                    "government": "government",
                    "commercial": "commercial",
                    "nonprofit": "grants",
                    "state": "government"
                }

                raw_score = getattr(opportunity, 'relevance_score', 0.0)
                normalized_score = min(1.0, max(0.0, raw_score / 100.0 if raw_score > 1.0 else raw_score))

                lead_data = {
                    "organization_name": getattr(opportunity, 'funder_name', '[Organization Name Missing]'),
                    "opportunity_type": opportunity_type_mapping.get(strategy_name, "grants"),
                    "source": f"unified_discovery_{strategy_name}",
                    "description": getattr(opportunity, 'description', '') or getattr(opportunity, 'title', ''),
                    "funding_amount": getattr(opportunity, 'funding_amount_max', 0),
                    "compatibility_score": normalized_score,
                    "match_factors": {
                        "source_type": str(getattr(opportunity, 'source_type', '')),
                        "deadline": getattr(opportunity, 'deadline', None),
                        "eligibility": getattr(opportunity, 'eligibility_requirements', [])
                    },
                    "external_data": {
                        "opportunity_id": getattr(opportunity, 'opportunity_id', ''),
                        "source_url": getattr(opportunity, 'source_url', ''),
                        "discovery_session": discovery_session.session_id,
                        "discovery_timestamp": discovery_session.started_at.isoformat() if discovery_session.started_at else None
                    }
                }

                try:
                    opportunity_id = f"opp_{uuid.uuid4().hex[:12]}"
                    opportunity = Opportunity(
                        id=opportunity_id,
                        profile_id=profile_id,
                        organization_name=lead_data.get("organization_name", ""),
                        ein=lead_data.get("external_data", {}).get("ein"),
                        current_stage="prospects",
                        scoring={"overall_score": lead_data.get("compatibility_score", 0.0)},
                        analysis={"match_factors": lead_data.get("match_factors", {})},
                        source="unified_discovery",
                        opportunity_type=lead_data.get("opportunity_type", "grants"),
                        description=lead_data.get("description"),
                        funding_amount=lead_data.get("funding_amount"),
                        program_name=lead_data.get("program_name"),
                        discovered_at=datetime.now(),
                        last_updated=datetime.now(),
                        status="active"
                    )

                    if database_service.create_opportunity(opportunity):
                        opportunities.append({
                            "opportunity_id": opportunity_id,
                            "organization_name": opportunity.organization_name,
                            "opportunity_type": opportunity.opportunity_type,
                            "compatibility_score": lead_data.get("compatibility_score", 0.0),
                            "description": opportunity.description,
                            "funding_amount": opportunity.funding_amount,
                            "program_name": opportunity.program_name
                        })
                    else:
                        logger.warning(f"Failed to save unified discovery opportunity {opportunity_id} to database")

                except Exception as save_error:
                    logger.error(f"Error creating opportunity from unified discovery: {save_error}")
                    continue

        if hasattr(profile_obj, 'metrics') and profile_obj.metrics:
            profile_obj.metrics.total_discovery_sessions += 1
            profile_obj.metrics.last_discovery_session = discovery_session.started_at
            if discovery_session.execution_time_seconds:
                total_time = (profile_obj.metrics.avg_session_duration_minutes *
                            (profile_obj.metrics.total_discovery_sessions - 1) +
                            discovery_session.execution_time_seconds / 60)
                profile_obj.metrics.avg_session_duration_minutes = total_time / profile_obj.metrics.total_discovery_sessions

            profile_obj.metrics.update_funnel_metrics("prospects", len(opportunities))
            profile_service.update_profile(profile_id, profile_obj)

        from src.profiles.models import DiscoverySession as ProfileDiscoverySession
        profile_discovery_session = ProfileDiscoverySession(
            session_id=discovery_session.session_id,
            profile_id=profile_id,
            started_at=discovery_session.started_at,
            completed_at=discovery_session.completed_at,
            status=discovery_session.status.value if hasattr(discovery_session.status, 'value') else str(discovery_session.status),
            tracks_executed=list(discovery_session.results_by_strategy.keys()),
            opportunities_found={strategy: len(results) for strategy, results in discovery_session.results_by_strategy.items()},
            total_opportunities=discovery_session.total_opportunities,
            execution_time_seconds=int(discovery_session.execution_time_seconds) if discovery_session.execution_time_seconds else 0,
            notes=f"Unified discovery with {len(funding_source_types)} funding source types"
        )
        profile_service.add_discovery_session(profile_discovery_session)

        session_summary = bridge.get_session_summary(discovery_session.session_id)

        return {
            "message": f"Unified discovery completed for profile {profile_id}",
            "discovery_id": discovery_session.session_id,
            "status": discovery_session.status.value,
            "execution_time_seconds": discovery_session.execution_time_seconds,
            "total_opportunities_found": discovery_session.total_opportunities,
            "opportunities_by_strategy": opportunities_by_strategy,
            "strategy_execution_times": discovery_session.strategy_execution_times,
            "average_relevance_score": discovery_session.avg_relevance_score,
            "api_calls_made": discovery_session.api_calls_made,
            "progress_updates": len(progress_updates),
            "top_opportunities": [
                {
                    "organization": getattr(opp, 'funder_name', 'Unknown'),
                    "title": getattr(opp, 'title', ''),
                    "amount": getattr(opp, 'funding_amount_max', 0),
                    "relevance": getattr(opp, 'relevance_score', 0.0),
                    "source": str(getattr(opp, 'source_type', ''))
                }
                for opp in discovery_session.top_opportunities[:5]
            ],
            "session_summary": session_summary,
            "bridge_architecture": "unified_multitrack_bridge",
            "phase": "4B"
        }

    except Exception as e:
        logger.error(f"Unified discovery failed for profile {profile_id}: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"Unified discovery failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# BMF Filter Endpoints
# =============================================================================

@router.post("/api/profiles/{profile_id}/run-bmf-filter")
async def run_bmf_filter_for_profile(profile_id: str):
    """
    Execute BMF filter processor for a profile to find matching organizations.
    This endpoint runs the actual BMF processor against local source data.
    """
    try:
        database_service = _get_database_service()
        logger.info(f"Running BMF filter for profile {profile_id}")

        profile_obj = database_service.get_profile(profile_id)
        if not profile_obj:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        if hasattr(profile_obj, 'ntee_codes'):
            ntee_codes = getattr(profile_obj, 'ntee_codes', [])
            geographic_scope = getattr(profile_obj, 'geographic_scope', {})
        else:
            ntee_codes = profile_obj.get('ntee_codes', [])
            geographic_scope = profile_obj.get('geographic_scope', {})

        states = geographic_scope.get('states', ['VA']) if geographic_scope else ['VA']

        logger.info(f"BMF Filter criteria - NTEE codes: {ntee_codes}, States: {states}")

        from src.processors.filtering.bmf_filter import BMFFilterProcessor
        from src.core.data_models import WorkflowConfig, ProcessorConfig

        bmf_processor = BMFFilterProcessor()

        workflow_config = WorkflowConfig(
            workflow_id=f"bmf_filter_{profile_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            ntee_codes=ntee_codes or ["L11", "L20", "L99", "L82", "L81", "L80", "L41", "L24", "F40"],
            states=states,
            max_results=100
        )

        processor_config = ProcessorConfig(
            workflow_id=workflow_config.workflow_id,
            processor_name="bmf_filter",
            workflow_config=workflow_config,
            processor_specific_config={
                "profile_id": profile_id,
                "source_data_path": "data/source_data"
            }
        )

        logger.info("Executing BMF processor with real source data")
        try:
            bmf_result = await asyncio.wait_for(
                bmf_processor.execute(processor_config),
                timeout=30.0
            )

            if bmf_result.success and bmf_result.data:
                organizations = bmf_result.data.get("organizations", [])

                nonprofits = []
                foundations = []

                for org in organizations:
                    org_data = {
                        "organization_name": org.get("organization_name", ""),
                        "ein": org.get("ein", ""),
                        "ntee_code": org.get("ntee_code", ""),
                        "state": org.get("state", ""),
                        "source_type": org.get("source_type", "Nonprofit"),
                        "bmf_filtered": True
                    }

                    if org.get("foundation_code") == "03" or org.get("source_type") == "Foundation":
                        foundations.append(org_data)
                    else:
                        nonprofits.append(org_data)

                bmf_results = {
                    "nonprofits": nonprofits,
                    "foundations": foundations
                }

                logger.info(f"BMF Filter found {len(nonprofits)} nonprofits and {len(foundations)} foundations")

                return {
                    "status": "success",
                    "bmf_results": bmf_results,
                    "total_organizations": len(organizations),
                    "nonprofits_found": len(nonprofits),
                    "foundations_found": len(foundations),
                    "filter_criteria": {
                        "ntee_codes": ntee_codes,
                        "states": states
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.warning("BMF processor returned no results")
                return {
                    "status": "success",
                    "bmf_results": {"nonprofits": [], "foundations": []},
                    "total_organizations": 0,
                    "nonprofits_found": 0,
                    "foundations_found": 0,
                    "message": "No organizations found matching criteria"
                }

        except asyncio.TimeoutError:
            logger.error("BMF processor timed out after 30 seconds")
            raise HTTPException(status_code=408, detail="BMF filter processing timed out")
        except Exception as bmf_error:
            logger.error(f"BMF processor failed: {bmf_error}")
            raise HTTPException(status_code=500, detail="Internal server error")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"BMF filter endpoint failed: {e}")
        logger.error(f"BMF filter failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/profiles/{profile_id}/discover/bmf")
async def discover_bmf_opportunities(profile_id: str, bmf_data: Dict[str, Any]):
    """
    Save BMF filter results to profile using SQLite database architecture.
    """
    try:
        database_service = _get_database_service()
        logger.info(f"Processing BMF discovery for profile {profile_id}")

        profile_obj = database_service.get_profile(profile_id)
        if not profile_obj:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        bmf_results = bmf_data.get("bmf_results", {})
        nonprofits = bmf_results.get("nonprofits", [])
        foundations = bmf_results.get("foundations", [])

        logger.info(f"BMF data received: {len(nonprofits)} nonprofits, {len(foundations)} foundations")

        if hasattr(profile_obj, 'ein'):
            profile_ein = getattr(profile_obj, 'ein', '').strip() if profile_obj.ein else ''
            profile_name = getattr(profile_obj, 'name', '').strip() if profile_obj.name else ''
        else:
            profile_ein = profile_obj.get('ein', '').strip() if profile_obj.get('ein') else ''
            profile_name = profile_obj.get('name', '').strip() if profile_obj.get('name') else ''
        if profile_ein:
            profile_ein = profile_ein.replace('-', '').replace(' ', '')

        opportunities = []
        excluded_self_count = 0

        # Process nonprofit results
        for org in nonprofits:
            org_ein = org.get("ein", "").strip().replace('-', '').replace(' ', '')
            org_name = org.get("organization_name", "").strip()

            is_self_match = False
            if profile_ein and org_ein and profile_ein == org_ein:
                if similar_organization_names(org_name, profile_name):
                    is_self_match = True
                    logger.info(f"Excluded self-match for profile {profile_id}: {org_name} (EIN: {org.get('ein')}) - similar to profile '{profile_name}'")
                else:
                    logger.warning(f"EIN match but name difference for profile {profile_id}: org='{org_name}' vs profile='{profile_name}' (EIN: {org.get('ein')})")

            if is_self_match:
                excluded_self_count += 1
                continue

            try:
                opportunity_id = f"opp_{uuid.uuid4().hex[:12]}"

                opportunity = Opportunity(
                    id=opportunity_id,
                    profile_id=profile_id,
                    organization_name=org.get("organization_name", ""),
                    ein=org.get("ein"),
                    current_stage="prospects",
                    stage_history=[{
                        "stage": "prospects",
                        "entered_at": datetime.now().isoformat(),
                        "exited_at": None,
                        "duration_hours": None
                    }],
                    overall_score=org.get("compatibility_score", 0.75),
                    confidence_level=None,
                    auto_promotion_eligible=False,
                    promotion_recommended=False,
                    scored_at=None,
                    scorer_version="1.0.0",
                    analysis_discovery={
                        "match_factors": {
                            "source_type": org.get("source_type", "Nonprofit"),
                            "ntee_code": org.get("ntee_code"),
                            "state": org.get("state", "VA"),
                            "bmf_filtered": True,
                            "quick_bmf_result": True,
                            "deadline": None,
                            "eligibility": []
                        },
                        "risk_factors": {},
                        "recommendations": [],
                        "network_insights": {},
                        "analyzed_at": datetime.now().isoformat(),
                        "source": "BMF Filter",
                        "opportunity_type": "grants"
                    },
                    source="BMF Filter",
                    discovery_date=datetime.now().isoformat(),
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )

                if database_service.create_opportunity(opportunity):
                    opportunities.append({
                        "opportunity_id": opportunity_id,
                        "organization_name": org.get("organization_name", ""),
                        "compatibility_score": org.get("compatibility_score", 0.75)
                    })
                    logger.info(f"Successfully created nonprofit opportunity in database: {org.get('organization_name', 'Unknown')}")
                else:
                    logger.error(f"Failed to create nonprofit opportunity in database: {org.get('organization_name', 'Unknown')}")

            except Exception as create_error:
                logger.error(f"Failed to create nonprofit opportunity for {org.get('ein', 'unknown')}: {create_error}")
                import traceback
                logger.error(f"Create opportunity traceback: {traceback.format_exc()}")
                continue

        # Process foundation results
        for org in foundations:
            org_ein = org.get("ein", "").strip().replace('-', '').replace(' ', '')
            org_name = org.get("organization_name", "").strip()

            is_self_match = False
            if profile_ein and org_ein and profile_ein == org_ein:
                if similar_organization_names(org_name, profile_name):
                    is_self_match = True
                    logger.info(f"Excluded self-match for profile {profile_id}: {org_name} (EIN: {org.get('ein')}) - similar to profile '{profile_name}'")
                else:
                    logger.warning(f"EIN match but name difference for profile {profile_id}: org='{org_name}' vs profile='{profile_name}' (EIN: {org.get('ein')})")

            if is_self_match:
                excluded_self_count += 1
                continue

            try:
                opportunity_id = f"opp_{uuid.uuid4().hex[:12]}"

                opportunity = Opportunity(
                    id=opportunity_id,
                    profile_id=profile_id,
                    organization_name=org.get("organization_name", ""),
                    ein=org.get("ein"),
                    current_stage="prospects",
                    stage_history=[{
                        "stage": "prospects",
                        "entered_at": datetime.now().isoformat(),
                        "exited_at": None,
                        "duration_hours": None
                    }],
                    overall_score=org.get("compatibility_score", 0.75),
                    confidence_level=None,
                    auto_promotion_eligible=False,
                    promotion_recommended=False,
                    scored_at=None,
                    scorer_version="1.0.0",
                    analysis_discovery={
                        "match_factors": {
                            "source_type": org.get("source_type", "Foundation"),
                            "foundation_code": org.get("foundation_code"),
                            "state": org.get("state", "VA"),
                            "bmf_filtered": True,
                            "quick_bmf_result": True,
                            "deadline": None,
                            "eligibility": []
                        },
                        "risk_factors": {},
                        "recommendations": [],
                        "network_insights": {},
                        "analyzed_at": datetime.now().isoformat(),
                        "source": "BMF Filter",
                        "opportunity_type": "grants"
                    },
                    source="BMF Filter",
                    discovery_date=datetime.now().isoformat(),
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )

                if database_service.create_opportunity(opportunity):
                    opportunities.append({
                        "opportunity_id": opportunity_id,
                        "organization_name": org.get("organization_name", ""),
                        "compatibility_score": org.get("compatibility_score", 0.75)
                    })
                    logger.info(f"Successfully created foundation opportunity in database: {org.get('organization_name', 'Unknown')}")
                else:
                    logger.error(f"Failed to create foundation opportunity in database: {org.get('organization_name', 'Unknown')}")

            except Exception as create_error:
                logger.error(f"Failed to create foundation opportunity for {org.get('ein', 'unknown')}: {create_error}")
                import traceback
                logger.error(f"Create opportunity traceback: {traceback.format_exc()}")
                continue

        try:
            logger.info(f"BMF discovery completed for {profile_id} with {len(opportunities)} opportunities")
        except Exception as update_error:
            logger.warning(f"Failed to update profile metadata for {profile_id}: {update_error}")

        total_results = len(opportunities)
        if excluded_self_count > 0:
            logger.info(f"BMF discovery completed for profile {profile_id}: {total_results} opportunities saved, {excluded_self_count} self-matches excluded")
        else:
            logger.info(f"BMF discovery completed for profile {profile_id}: {total_results} opportunities saved")

        return {
            "message": f"BMF discovery completed for profile {profile_id}",
            "total_opportunities_found": total_results,
            "nonprofits_found": len(nonprofits),
            "foundations_found": len(foundations),
            "opportunities_saved": len(opportunities),
            "discovery_type": "bmf_filter",
            "status": "completed"
        }

    except ValueError as ve:
        logger.error(f"BMF discovery validation error for profile {profile_id}: {ve}")
        if "timeout" in str(ve).lower():
            raise HTTPException(status_code=408, detail="BMF discovery timed out")
        elif "permission denied" in str(ve).lower():
            raise HTTPException(status_code=403, detail="BMF file access denied")
        elif "invalid argument" in str(ve).lower():
            raise HTTPException(status_code=422, detail="BMF file format error")
        else:
            raise HTTPException(status_code=422, detail="BMF discovery validation failed")
    except asyncio.TimeoutError:
        logger.error(f"BMF discovery timed out for profile {profile_id}")
        raise HTTPException(status_code=408, detail="BMF discovery operation timed out")
    except FileNotFoundError as fnf:
        logger.error(f"BMF data file not found for profile {profile_id}: {fnf}")
        raise HTTPException(status_code=404, detail="BMF data file not available - please contact support")
    except PermissionError as pe:
        logger.error(f"BMF file permission error for profile {profile_id}: {pe}")
        raise HTTPException(status_code=403, detail="Access denied to BMF data files")
    except Exception as e:
        logger.error(f"BMF discovery unexpected error for profile {profile_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="BMF discovery service temporarily unavailable - discovery will continue with other sources")


# =============================================================================
# Track Discovery Endpoints
# =============================================================================

@router.post("/api/discovery/nonprofit")
async def discover_nonprofits(request: Dict[str, Any]):
    """Execute nonprofit discovery track (ProPublica + BMF + EIN lookup)."""
    try:
        logger.info("Starting nonprofit discovery track")

        engine = get_workflow_engine()

        state = request.get("state", "VA")
        ein = request.get("ein")
        max_results = request.get("max_results", 100)

        profile_context = request.get("profile_context")
        focus_areas = request.get("focus_areas", [])
        target_populations = request.get("target_populations", [])

        if profile_context:
            logger.info(f"Using profile context for nonprofit discovery: {profile_context.get('name', 'Unknown')}")
            if profile_context.get("geographic_scope", {}).get("states"):
                state = profile_context["geographic_scope"]["states"][0]
            if profile_context.get("focus_areas"):
                focus_areas.extend(profile_context["focus_areas"])
            if profile_context.get("target_populations"):
                target_populations.extend(profile_context["target_populations"])

        results = {"track": "nonprofit"}

        from src.core.data_models import WorkflowConfig, ProcessorConfig

        if not ein:
            bmf_instance = engine.registry.get_processor("bmf_filter")
            if bmf_instance:
                workflow_config = WorkflowConfig(
                    workflow_id=f"nonprofit_discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    states=[state] if state else ["VA"],
                    max_results=max_results
                )
                processor_config = ProcessorConfig(
                    workflow_id=workflow_config.workflow_id,
                    processor_name="bmf_filter",
                    workflow_config=workflow_config,
                    processor_specific_config={
                        "focus_areas": focus_areas,
                        "target_populations": target_populations,
                        "profile_context": profile_context
                    }
                )

                logger.info("Executing BMF processor with timeout protection")
                try:
                    bmf_result = await asyncio.wait_for(
                        bmf_instance.execute(processor_config),
                        timeout=25.0
                    )
                    logger.info(f"BMF result success: {bmf_result.success}")
                    logger.info(f"BMF result data keys: {list(bmf_result.data.keys()) if bmf_result.data else 'None'}")
                    if bmf_result.success and bmf_result.data:
                        results["bmf_results"] = bmf_result.data.get("organizations", [])
                    else:
                        results["bmf_results"] = []
                except asyncio.TimeoutError:
                    logger.error("BMF processor timed out after 25 seconds - using empty results")
                    results["bmf_results"] = []
                except Exception as bmf_error:
                    logger.error(f"BMF processor failed: {bmf_error}")
                    results["bmf_results"] = []

        pp_instance = engine.registry.get_processor("propublica_fetch")
        if pp_instance:

            workflow_config = WorkflowConfig(
                workflow_id=f"propublica_fetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                target_ein=ein,
                max_results=max_results
            )

            if ein:
                input_data = [{"ein": ein}]
            else:
                input_data = results.get("bmf_results", [])[:50]

            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="propublica_fetch",
                workflow_config=workflow_config,
                input_data={"organizations": input_data}
            )

            pp_result = await pp_instance.execute(processor_config)
            logger.info(f"ProPublica result success: {pp_result.success}")
            logger.info(f"ProPublica result data keys: {list(pp_result.data.keys()) if pp_result.data else 'None'}")
            if pp_result.success and pp_result.data:
                results["propublica_results"] = pp_result.data.get("organizations", [])
            else:
                results["propublica_results"] = []

        try:
            stored_opportunities = []

            profile_ein = profile_context.get('ein', '').strip().replace('-', '').replace(' ', '') if profile_context else ''
            profile_name = profile_context.get('name', '').strip() if profile_context else ''

            if profile_context:
                profile_id = profile_context.get('profile_id', 'test_profile')
                from src.discovery.unified_discovery_adapter import UnifiedDiscoveryAdapter
                from src.discovery.base_discoverer import DiscoveryResult
                from src.profiles.models import FundingType as FT

                unified_adapter = UnifiedDiscoveryAdapter()
                session_id = f"nonprofit_discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                discovery_results = []

                for bmf_org in results.get("bmf_results", []):
                    org_name = bmf_org.get('name', '').strip()
                    if not org_name or org_name == '[Organization Name Missing]':
                        logger.debug(f"Skipping BMF organization with missing name: {bmf_org}")
                        continue

                    org_ein = bmf_org.get('ein', '').strip().replace('-', '').replace(' ', '')

                    is_self_match = False
                    if profile_ein and org_ein and profile_ein == org_ein:
                        if similar_organization_names(org_name, profile_name):
                            is_self_match = True
                            logger.info(f"Excluded self-match in nonprofit discovery: {org_name} (EIN: {bmf_org.get('ein')}) - similar to profile '{profile_name}'")
                        else:
                            logger.warning(f"EIN match but name difference in nonprofit discovery: org='{org_name}' vs profile='{profile_name}' (EIN: {bmf_org.get('ein')})")

                    if is_self_match:
                        continue

                    discovery_result = DiscoveryResult(
                        opportunity_id=f"bmf_{bmf_org.get('ein', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        organization_name=org_name,
                        source_type=FT.GRANTS,
                        discovery_source="bmf_filter",
                        description=f"Nonprofit organization from IRS Business Master File. Revenue: ${bmf_org.get('revenue', 0) or 0:,}",
                        funding_amount=None,
                        program_name=None,
                        compatibility_score=0.6,
                        confidence_level=0.75,
                        discovered_at=datetime.now(),
                        match_factors={
                            "source_type": "Nonprofit",
                            "ntee_code": bmf_org.get("ntee_code"),
                            "state": bmf_org.get("state", "VA"),
                            "bmf_filtered": True,
                            "deadline": None,
                            "eligibility": []
                        },
                        external_data={
                            "ein": bmf_org.get("ein"),
                            "ntee_code": bmf_org.get("ntee_code"),
                            "discovery_source": "bmf_filter",
                            "source_url": None,
                            "revenue": bmf_org.get("revenue", 0)
                        }
                    )
                    discovery_results.append(discovery_result)

                for pp_org in results.get("propublica_results", []):
                    org_name = pp_org.get('name', '').strip()
                    if not org_name or org_name == '[Organization Name Missing]':
                        logger.debug(f"Skipping ProPublica organization with missing name: {pp_org}")
                        continue

                    org_ein = pp_org.get('ein', '').strip().replace('-', '').replace(' ', '')

                    is_self_match = False
                    if profile_ein and org_ein and profile_ein == org_ein:
                        if similar_organization_names(org_name, profile_name):
                            is_self_match = True
                            logger.info(f"Excluded self-match in nonprofit discovery (ProPublica): {org_name} (EIN: {pp_org.get('ein')}) - similar to profile '{profile_name}'")
                        else:
                            logger.warning(f"EIN match but name difference in nonprofit discovery (ProPublica): org='{org_name}' vs profile='{profile_name}' (EIN: {pp_org.get('ein')})")

                    if is_self_match:
                        continue

                    discovery_result = DiscoveryResult(
                        opportunity_id=f"propublica_{pp_org.get('ein', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        organization_name=org_name,
                        source_type=FT.GRANTS,
                        discovery_source="propublica_fetch",
                        description=f"Nonprofit organization from ProPublica database. Revenue: ${pp_org.get('revenue', 0) or 0:,}",
                        funding_amount=None,
                        program_name=None,
                        compatibility_score=0.7,
                        confidence_level=0.80,
                        discovered_at=datetime.now(),
                        match_factors={
                            "source_type": "Nonprofit",
                            "ntee_code": pp_org.get("ntee_code"),
                            "state": pp_org.get("state", "VA"),
                            "propublica_data": True,
                            "deadline": None,
                            "eligibility": []
                        },
                        external_data={
                            "ein": pp_org.get("ein"),
                            "ntee_code": pp_org.get("ntee_code"),
                            "discovery_source": "propublica_fetch",
                            "source_url": None,
                            "revenue": pp_org.get("revenue", 0)
                        }
                    )
                    discovery_results.append(discovery_result)

                save_results = await unified_adapter.save_discovery_results(
                    discovery_results, profile_id, session_id
                )

                logger.info(f"Unified adapter results: {save_results['saved_count']} saved, {save_results['duplicates_skipped']} duplicates skipped, {save_results['failed_count']} failed")

                stored_opportunities = save_results.get('saved_opportunities', [])

        except Exception as e:
            logger.error(f"Failed to store nonprofit discovery opportunities: {str(e)}")

        total_bmf = len(results.get("bmf_results", []))
        total_propublica = len(results.get("propublica_results", []))
        total_found = total_bmf + total_propublica
        total_stored = len(stored_opportunities)

        promotion_result = None
        if profile_context and stored_opportunities:
            try:
                from src.web.services.automated_promotion_service import get_automated_promotion_service

                opportunities = []
                for stored_opp in stored_opportunities:
                    opportunity = {
                        "opportunity_id": stored_opp.get("lead_id"),
                        "organization_name": stored_opp.get("organization_name"),
                        "source_type": stored_opp.get("opportunity_type", "grants"),
                        "discovery_source": stored_opp.get("source", "nonprofit_discovery"),
                        "funnel_stage": stored_opp.get("pipeline_stage", "discovery"),
                        "compatibility_score": stored_opp.get("compatibility_score", 0.7),
                        "description": stored_opp.get("description", ""),
                        "external_data": stored_opp.get("external_data", {})
                    }
                    opportunities.append(opportunity)

                auto_promotion_service = get_automated_promotion_service()
                profile_id = profile_context.get('profile_id', 'unknown')

                promotion_result = await auto_promotion_service.process_discovery_results(
                    profile_id, opportunities, "nonprofit_discovery"
                )

                logger.info(f"Automated promotion: {promotion_result.promoted_count}/{promotion_result.total_processed} opportunities promoted")

            except Exception as e:
                logger.warning(f"Automated promotion failed, continuing without it: {e}")
                promotion_result = {"error": str(e)}

        response = {
            "status": "completed",
            "track": "nonprofit",
            "total_found": total_found,
            "total_stored": total_stored,
            "duplicates_skipped": save_results.get('duplicates_skipped', 0) if 'save_results' in locals() else 0,
            "failed_saves": save_results.get('failed_count', 0) if 'save_results' in locals() else 0,
            "results": results,
            "profile_context": profile_context.get('name') if profile_context else None,
            "parameters_used": {
                "state": state,
                "max_results": max_results,
                "focus_areas": focus_areas,
                "target_populations": target_populations
            },
            "timestamp": datetime.now().isoformat()
        }

        if promotion_result:
            response["automated_promotion"] = {
                "enabled": True,
                "processed": getattr(promotion_result, 'total_processed', 0),
                "promoted": getattr(promotion_result, 'promoted_count', 0),
                "scored": getattr(promotion_result, 'scored_count', 0),
                "errors": getattr(promotion_result, 'error_count', 0),
                "processing_time": getattr(promotion_result, 'processing_time', 0.0)
            }
        else:
            response["automated_promotion"] = {"enabled": False, "reason": "No profile context provided"}

        return response

    except ValueError as ve:
        logger.error(f"Nonprofit discovery validation error: {ve}")
        if "timeout" in str(ve).lower():
            return {
                "status": "completed_with_timeout",
                "track": "nonprofit",
                "total_found": 0,
                "total_stored": 0,
                "error": "BMF processing timed out - results from other sources may still be available",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "completed_with_errors",
                "track": "nonprofit",
                "total_found": 0,
                "total_stored": 0,
                "error": f"BMF processing failed: {str(ve)} - other discovery sources may still work",
                "timestamp": datetime.now().isoformat()
            }
    except asyncio.TimeoutError:
        logger.error("Nonprofit discovery timed out")
        return {
            "status": "timeout",
            "track": "nonprofit",
            "total_found": 0,
            "total_stored": 0,
            "error": "Nonprofit discovery timed out - please try again with smaller parameters",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Nonprofit discovery unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "failed",
            "track": "nonprofit",
            "total_found": 0,
            "total_stored": 0,
            "error": "Nonprofit discovery service temporarily unavailable",
            "timestamp": datetime.now().isoformat()
        }


@router.post("/api/discovery/federal")
async def discover_federal_opportunities(request: Dict[str, Any]):
    """Execute federal grants discovery (Grants.gov + USASpending)."""
    try:
        logger.info("Starting federal discovery track")

        keywords = request.get("keywords", [])
        opportunity_category = request.get("opportunity_category")
        max_results = request.get("max_results", 50)

        results = {"track": "federal"}

        engine = get_workflow_engine()
        grants_instance = engine.registry.get_processor("grants_gov_fetch")
        if grants_instance:

            from src.core.data_models import WorkflowConfig, ProcessorConfig
            workflow_config = WorkflowConfig(
                workflow_id=f"grants_gov_fetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                max_results=max_results
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="grants_gov_fetch",
                workflow_config=workflow_config,
                processor_specific_config={
                    "keywords": keywords,
                    "opportunity_category": opportunity_category
                }
            )

            grants_result = await grants_instance.execute(processor_config)
            results["grants_gov_results"] = grants_result.data.get("results", [])

        usa_instance = engine.registry.get_processor("usaspending_fetch")
        if usa_instance:

            workflow_config = WorkflowConfig(
                workflow_id=f"usaspending_fetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                max_results=max_results
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="usaspending_fetch",
                workflow_config=workflow_config,
                processor_specific_config={
                    "keywords": keywords
                }
            )

            usa_result = await usa_instance.execute(processor_config)
            results["usaspending_results"] = usa_result.data.get("results", [])

        return {
            "status": "completed",
            "track": "federal",
            "total_found": len(results.get("grants_gov_results", [])),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Federal discovery failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/discovery/state")
async def discover_state_opportunities(request: Dict[str, Any]):
    """Execute state-level grants discovery."""
    try:
        logger.info("Starting state discovery track")

        states = request.get("states", ["VA"])
        focus_areas = request.get("focus_areas", [])
        max_results = request.get("max_results", 50)

        results = {"track": "state"}

        engine = get_workflow_engine()
        va_instance = engine.registry.get_processor("va_state_grants_fetch")
        if va_instance and "VA" in states:

            from src.core.data_models import WorkflowConfig, ProcessorConfig
            workflow_config = WorkflowConfig(
                workflow_id=f"va_state_grants_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                states=["VA"],
                max_results=max_results
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="va_state_grants_fetch",
                workflow_config=workflow_config,
                processor_specific_config={
                    "focus_areas": focus_areas
                }
            )

            va_result = await va_instance.execute(processor_config)
            results["virginia_results"] = va_result.data.get("results", [])

        return {
            "status": "completed",
            "track": "state",
            "total_found": len(results.get("virginia_results", [])),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"State discovery failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/discovery/commercial")
async def discover_commercial_enhanced(request: Dict[str, Any]):
    """Execute commercial discovery (Foundation Directory + CSR Analysis)."""
    try:
        logger.info("Starting enhanced commercial discovery track")

        industries = request.get("industries", [])
        company_sizes = request.get("company_sizes", [])
        funding_range = request.get("funding_range", {})
        max_results = request.get("max_results", 50)

        results = {"track": "commercial"}

        engine = get_workflow_engine()

        fd_instance = engine.registry.get_processor("foundation_directory_fetch")
        if fd_instance:

            from src.core.data_models import WorkflowConfig, ProcessorConfig
            workflow_config = WorkflowConfig(
                workflow_id=f"foundation_directory_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                max_results=max_results
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="foundation_directory_fetch",
                workflow_config=workflow_config,
                processor_specific_config={
                    "industries": industries,
                    "funding_range": funding_range
                }
            )

            fd_result = await fd_instance.execute(processor_config)
            results["foundation_results"] = fd_result.data.get("results", [])

        csr_instance = engine.registry.get_processor("corporate_csr_analyzer")
        if csr_instance:

            workflow_config = WorkflowConfig(
                workflow_id=f"csr_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                max_results=max_results
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="corporate_csr_analyzer",
                workflow_config=workflow_config,
                processor_specific_config={
                    "industries": industries,
                    "company_sizes": company_sizes
                }
            )

            csr_result = await csr_instance.execute(processor_config)
            results["csr_results"] = csr_result.data.get("results", [])

        return {
            "status": "completed",
            "track": "commercial",
            "total_found": len(results.get("foundation_results", [])) + len(results.get("csr_results", [])),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Commercial discovery failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/discovery/bmf/{profile_id}")
async def discover_bmf_filtered(profile_id: str, request: Dict[str, Any] = None):
    """Execute BMF filtering with profile NTEE codes and geographic criteria."""
    try:
        logger.info(f"Starting BMF discovery for profile {profile_id}")

        database_path = _get_database_path()
        database_manager = DatabaseManager(database_path)
        profile_data = database_manager.get_profile(profile_id)

        if not profile_data:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        ntee_codes = []
        if profile_data.ntee_codes:
            try:
                import json as json_mod
                ntee_codes = json_mod.loads(profile_data.ntee_codes) if isinstance(profile_data.ntee_codes, str) else profile_data.ntee_codes
            except (json.JSONDecodeError, TypeError):
                ntee_codes = []

        if not ntee_codes:
            logger.warning(f"Profile {profile_id} has no NTEE codes, using healthcare defaults")
            ntee_codes = ["L11", "L20", "L99"]

        states = ["VA"]
        if profile_data.geographic_scope:
            try:
                import json as json_mod
                geographic_scope = json_mod.loads(profile_data.geographic_scope) if isinstance(profile_data.geographic_scope, str) else profile_data.geographic_scope
                if geographic_scope and geographic_scope.get("states"):
                    states = geographic_scope["states"]
            except (json.JSONDecodeError, TypeError):
                pass

        max_results = request.get("max_results", 100) if request else 100
        min_revenue = request.get("min_revenue") if request else None
        max_revenue = request.get("max_revenue") if request else None

        logger.info(f"BMF discovery parameters - Profile: {profile_data.name}, NTEE: {ntee_codes}, States: {states}")

        engine = get_workflow_engine()
        bmf_instance = engine.registry.get_processor("bmf_filter")

        if not bmf_instance:
            raise HTTPException(status_code=500, detail="BMF processor not available")

        from src.core.data_models import WorkflowConfig, ProcessorConfig

        workflow_config = WorkflowConfig(
            workflow_id=f"bmf_discovery_{profile_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            states=states,
            ntee_codes=ntee_codes,
            min_revenue=min_revenue,
            max_revenue=max_revenue,
            max_results=max_results
        )

        processor_config = ProcessorConfig(
            workflow_id=workflow_config.workflow_id,
            processor_name="bmf_filter",
            workflow_config=workflow_config,
            processor_specific_config={
                "profile_id": profile_id,
                "profile_name": profile_data.name
            }
        )

        try:
            logger.info("Executing BMF processor with real backend filtering")
            bmf_result = await asyncio.wait_for(
                bmf_instance.execute(processor_config),
                timeout=45.0
            )

            if bmf_result.success and bmf_result.data:
                organizations = bmf_result.data.get("organizations", [])
                logger.info(f"BMF discovery completed - found {len(organizations)} organizations")

                opportunities = []
                for org in organizations:
                    opportunity = {
                        "opportunity_id": f"bmf_{org.get('ein', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "organization_name": org.get('name', 'Unknown Organization'),
                        "ein": org.get('ein'),
                        "ntee_code": org.get('ntee_code'),
                        "state": org.get('state'),
                        "city": org.get('city'),
                        "revenue": org.get('revenue'),
                        "assets": org.get('assets'),
                        "discovery_source": "bmf_filter",
                        "source_type": "nonprofit",
                        "compatibility_score": 0.7,
                        "confidence_level": 0.8,
                        "discovered_at": datetime.now().isoformat(),
                        "match_factors": {
                            "ntee_match": org.get('ntee_code') in ntee_codes,
                            "geographic_match": org.get('state') in states,
                            "bmf_filtered": True
                        }
                    }
                    opportunities.append(opportunity)

                return {
                    "status": "completed",
                    "profile_id": profile_id,
                    "profile_name": profile_data.name,
                    "total_found": len(opportunities),
                    "opportunities": opportunities,
                    "filter_criteria": {
                        "ntee_codes": ntee_codes,
                        "states": states,
                        "min_revenue": min_revenue,
                        "max_revenue": max_revenue
                    },
                    "execution_time": bmf_result.execution_time,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"BMF processor failed or returned no data: {bmf_result.error_message if hasattr(bmf_result, 'error_message') else 'Unknown error'}")
                return {
                    "status": "completed",
                    "profile_id": profile_id,
                    "total_found": 0,
                    "opportunities": [],
                    "error": "BMF processor returned no results",
                    "timestamp": datetime.now().isoformat()
                }

        except asyncio.TimeoutError:
            logger.error(f"BMF discovery timed out after 45 seconds for profile {profile_id}")
            return {
                "status": "timeout",
                "profile_id": profile_id,
                "total_found": 0,
                "opportunities": [],
                "error": "BMF processing timed out - please try with smaller max_results",
                "timestamp": datetime.now().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"BMF discovery failed for profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
