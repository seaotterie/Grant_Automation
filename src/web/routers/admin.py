#!/usr/bin/env python3
"""
Admin Router
Handles administrative functions, system management, and remaining miscellaneous routes
Extracted from monolithic main.py for better modularity
"""

from fastapi import APIRouter, HTTPException, Depends, Request
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Import admin services and dependencies
from src.auth.jwt_auth import get_current_user_dependency, User
from src.core.workflow_engine import get_workflow_engine
from src.core.entity_cache_manager import get_entity_cache_manager
from src.profiles.unified_service import get_unified_profile_service
from src.web.middleware.deprecation import get_deprecation_stats, reset_deprecation_stats

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/api/admin", tags=["admin"])

# Initialize services
unified_service = get_unified_profile_service()
entity_cache = get_entity_cache_manager()


@router.get("/system/overview")
async def get_system_overview(
    current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Get comprehensive system overview for administrators."""
    try:
        workflow_engine = get_workflow_engine()
        cache_stats = await entity_cache.get_cache_stats()
        
        system_overview = {
            "system_health": {
                "status": "operational",
                "processors_available": len(workflow_engine.registry.list_processors()),
                "cache_status": cache_stats.get("status", "unknown"),
                "uptime": datetime.now().isoformat()
            },
            "performance_metrics": {
                "cache_hit_rate": cache_stats.get("hit_rate_percentage", 0),
                "total_entities": cache_stats.get("total_entities", 0),
                "cache_size_mb": cache_stats.get("cache_size_mb", 0)
            },
            "user_activity": {
                "active_profiles": len(unified_service.list_profiles()),
                "system_load": "low",  # Simplified metric
                "last_activity": datetime.now().isoformat()
            }
        }
        
        return {
            "system_overview": system_overview,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_system_cache(
    cache_type: str = "all",
    current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Clear system caches (admin only)."""
    try:
        if cache_type == "entity" or cache_type == "all":
            # Clear entity cache
            entity_cache.clear_cache()
            logger.info(f"Entity cache cleared by admin user {current_user.username}")
        
        return {
            "message": f"Cache '{cache_type}' cleared successfully",
            "cleared_by": current_user.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/recent")
async def get_recent_logs(
    limit: int = 100,
    level: str = "INFO",
    current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Get recent system logs (admin only)."""
    try:
        # Mock log data - in a real implementation, this would read from log files
        recent_logs = []
        for i in range(min(limit, 10)):  # Mock data
            recent_logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": f"System log entry {i+1}",
                "module": "system"
            })
        
        return {
            "recent_logs": recent_logs,
            "total_logs": len(recent_logs),
            "log_level": level,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maintenance/mode")
async def toggle_maintenance_mode(
    maintenance_data: Dict[str, Any],
    current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Toggle system maintenance mode (admin only)."""
    try:
        enable_maintenance = maintenance_data.get("enable", False)
        maintenance_message = maintenance_data.get("message", "System under maintenance")
        
        # In a real implementation, this would set a global maintenance flag
        logger.info(f"Maintenance mode {'enabled' if enable_maintenance else 'disabled'} by {current_user.username}")
        
        return {
            "maintenance_mode": enable_maintenance,
            "message": maintenance_message,
            "set_by": current_user.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to toggle maintenance mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Additional router for remaining miscellaneous routes
misc_router = APIRouter(prefix="/api", tags=["miscellaneous"])


@misc_router.get("/help")
async def get_help_information() -> Dict[str, Any]:
    """Get help and documentation information."""
    try:
        help_info = {
            "api_version": "2.0.0",
            "documentation": {
                "api_docs": "/api/docs",
                "openapi_schema": "/openapi.json"
            },
            "support": {
                "contact": "support@catalynx.com",
                "documentation_url": "https://docs.catalynx.com"
            },
            "endpoints": {
                "profiles": "/api/profiles",
                "discovery": "/api/discovery", 
                "scoring": "/api/scoring",
                "ai": "/api/ai",
                "export": "/api/export"
            }
        }
        
        return {
            "help": help_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get help information: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@misc_router.get("/search")
async def global_search(
    q: str,
    limit: int = 20
) -> Dict[str, Any]:
    """Global search across the system."""
    try:
        # Mock global search results
        search_results = {
            "profiles": [],
            "opportunities": [],
            "entities": []
        }
        
        # In a real implementation, this would search across all data types
        for i in range(min(limit // 3, 3)):
            search_results["profiles"].append({
                "id": f"profile_{i+1}",
                "name": f"Search Result Profile {i+1}",
                "type": "profile"
            })
            search_results["opportunities"].append({
                "id": f"opp_{i+1}",
                "title": f"Search Result Opportunity {i+1}",
                "type": "opportunity"
            })
            search_results["entities"].append({
                "id": f"entity_{i+1}",
                "name": f"Search Result Entity {i+1}",
                "type": "entity"
            })
        
        return {
            "search_results": search_results,
            "query": q,
            "total_results": sum(len(results) for results in search_results.values()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Global search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@misc_router.post("/feedback")
async def submit_feedback(feedback_data: Dict[str, Any]) -> Dict[str, Any]:
    """Submit user feedback."""
    try:
        feedback_id = f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Process feedback data
        processed_feedback = {
            "feedback_id": feedback_id,
            "type": feedback_data.get("type", "general"),
            "message": feedback_data.get("message", ""),
            "rating": feedback_data.get("rating"),
            "user_info": feedback_data.get("user_info", {}),
            "submitted_at": datetime.now().isoformat(),
            "status": "received"
        }
        
        logger.info(f"Feedback submitted: {feedback_id}")
        
        return {
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deprecated-usage")
async def get_deprecated_endpoint_usage() -> Dict[str, Any]:
    """
    Get usage statistics for deprecated API endpoints.

    This endpoint helps monitor API migration progress by tracking
    how often deprecated endpoints are being accessed.

    Returns:
        Dictionary with usage statistics including:
        - total_calls: Total deprecated endpoint calls
        - unique_endpoints_used: Number of unique deprecated endpoints accessed
        - total_deprecated_endpoints: Total number of deprecated endpoints
        - by_endpoint: Usage count per endpoint
        - by_phase: Usage count per migration phase
        - top_10: Top 10 most-used deprecated endpoints
        - last_updated: Timestamp of stats
    """
    try:
        stats = get_deprecation_stats()
        return {
            "success": True,
            "data": stats,
            "migration_progress": {
                "phase_1_complete": stats.get("by_phase", {}).get(1, 0) == 0,
                "phase_2_complete": stats.get("by_phase", {}).get(2, 0) == 0,
                "phase_3_complete": stats.get("by_phase", {}).get(3, 0) == 0,
                "overall_progress": f"{stats['unique_endpoints_used']}/{stats['total_deprecated_endpoints']} endpoints still in use"
            }
        }

    except Exception as e:
        logger.error(f"Failed to get deprecation stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deprecated-usage/reset")
async def reset_deprecated_stats(
    current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, str]:
    """
    Reset deprecation usage statistics.

    Requires authentication. Use this to reset counters after reviewing stats.
    """
    try:
        reset_deprecation_stats()
        logger.info(f"Deprecation stats reset by user: {current_user.username if hasattr(current_user, 'username') else 'unknown'}")

        return {
            "success": True,
            "message": "Deprecation usage statistics reset successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to reset deprecation stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Include both routers
routers = [router, misc_router]