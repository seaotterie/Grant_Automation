#!/usr/bin/env python3
"""
Discovery Router
Handles discovery workflow, entity cache, and search operations
Extracted from monolithic main.py for better modularity
"""

from fastapi import APIRouter, HTTPException, Query
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

# Import discovery services
from src.discovery.discovery_engine import discovery_engine
from src.discovery.unified_discovery_adapter import get_unified_discovery_adapter
from src.discovery.entity_discovery_service import get_entity_discovery_service
from src.core.entity_cache_manager import get_entity_cache_manager
from src.processors.registry import get_processor_summary
from src.processors.filtering.bmf_filter import BMFFilterProcessor
from src.profiles.unified_service import get_unified_profile_service

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/api/discovery", tags=["discovery"])

# Initialize services
discovery_adapter = get_unified_discovery_adapter()
entity_discovery = get_entity_discovery_service()
entity_cache = get_entity_cache_manager()
unified_service = get_unified_profile_service()


# Discovery Track Information

@router.get("/tracks")
async def get_discovery_tracks() -> Dict[str, Any]:
    """Get information about available discovery tracks."""
    try:
        tracks = {
            "nonprofit": {
                "name": "Nonprofit Organizations",
                "description": "Discover nonprofit organizations using IRS data and ProPublica 990 filings",
                "processors": ["bmf_filter", "propublica_fetch"],
                "data_sources": ["IRS BMF", "ProPublica Nonprofit Explorer"]
            },
            "government": {
                "name": "Government Opportunities", 
                "description": "Discover federal and state government funding opportunities",
                "processors": ["grants_gov_fetch", "usaspending_fetch"],
                "data_sources": ["Grants.gov", "USASpending.gov"]
            },
            "commercial": {
                "name": "Commercial Foundations",
                "description": "Discover corporate and private foundation opportunities",
                "processors": ["foundation_directory_fetch"],
                "data_sources": ["Foundation Directory Online"]
            },
            "state": {
                "name": "State and Local",
                "description": "Discover state and local funding opportunities",
                "processors": ["va_state_grants_fetch"],
                "data_sources": ["State Agency Websites"]
            }
        }
        
        return {
            "tracks": tracks,
            "total_tracks": len(tracks),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get discovery tracks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Entity Cache Operations

@router.get("/entity-cache-stats")
async def get_entity_cache_stats() -> Dict[str, Any]:
    """Get entity cache performance statistics."""
    try:
        stats = await entity_cache.get_cache_stats()
        return {
            "cache_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get entity cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}/data")
async def get_entity_data(entity_id: str) -> Dict[str, Any]:
    """Get cached data for a specific entity."""
    try:
        entity_data = entity_cache.get_entity_data(entity_id)
        if not entity_data:
            raise HTTPException(status_code=404, detail="Entity not found in cache")
        
        return {
            "entity_id": entity_id,
            "data": entity_data,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity data for {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entities/{entity_id}/data")
async def update_entity_data(
    entity_id: str,
    entity_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Update cached data for a specific entity."""
    try:
        entity_cache.set_entity_data(entity_id, entity_data)
        return {
            "entity_id": entity_id,
            "message": "Entity data updated successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to update entity data for {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# BMF (Business Master File) Discovery

@router.post("/bmf/search")
async def search_bmf(search_params: Dict[str, Any]) -> Dict[str, Any]:
    """Search the IRS Business Master File."""
    try:
        bmf_filter = BMFFilterProcessor()
        
        # Create configuration for BMF search
        config = {
            "search_criteria": search_params,
            "max_results": search_params.get("max_results", 100)
        }
        
        results = bmf_filter.execute(config)
        
        return {
            "bmf_results": results.get("results", []) if results else [],
            "search_params": search_params,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed BMF search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Discovery Execution

@router.post("/execute")
async def execute_discovery(
    discovery_request: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a discovery workflow."""
    try:
        profile_id = discovery_request.get("profile_id")
        tracks = discovery_request.get("tracks", ["nonprofit"])
        options = discovery_request.get("options", {})
        
        if not profile_id:
            raise HTTPException(status_code=400, detail="Profile ID is required")
        
        # Get profile for discovery
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Execute discovery using entity discovery service
        results = []
        for track in tracks:
            try:
                track_results = entity_discovery.discover_by_track(
                    profile, track, options
                )
                results.extend(track_results)
            except Exception as e:
                logger.warning(f"Failed discovery for track {track}: {e}")
        
        return {
            "discovery_results": results,
            "profile_id": profile_id,
            "tracks": tracks,
            "total_results": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Search and Filter Operations

@router.get("/search")
async def search_opportunities(
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=50, le=500),
    track: Optional[str] = Query(default=None),
    filters: Optional[str] = Query(default=None)
) -> Dict[str, Any]:
    """Search for opportunities across all tracks."""
    try:
        search_params = {
            "query": q,
            "limit": limit,
            "track": track,
            "filters": filters
        }
        
        # Basic search implementation using entity cache
        all_entities = entity_cache.get_all_entities()
        
        # Simple text-based filtering
        matching_entities = []
        search_terms = q.lower().split()
        
        for entity_id, entity_data in all_entities.items():
            if isinstance(entity_data, dict):
                # Search in organization name and description
                text_to_search = ""
                if "organization_name" in entity_data:
                    text_to_search += entity_data["organization_name"].lower()
                if "description" in entity_data:
                    text_to_search += " " + entity_data["description"].lower()
                
                # Check if any search terms match
                if any(term in text_to_search for term in search_terms):
                    matching_entities.append({
                        "entity_id": entity_id,
                        **entity_data
                    })
        
        # Apply limit
        matching_entities = matching_entities[:limit]
        
        return {
            "search_results": matching_entities,
            "search_params": search_params,
            "total_results": len(matching_entities),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to search opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filters")
async def get_discovery_filters() -> Dict[str, Any]:
    """Get available filters for discovery operations."""
    try:
        filters = {
            "ntee_codes": {
                "description": "NTEE classification codes",
                "type": "multiselect",
                "common_values": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
            },
            "revenue_range": {
                "description": "Annual revenue range",
                "type": "select",
                "options": ["<100K", "100K-500K", "500K-1M", "1M-5M", "5M-10M", "10M+"]
            },
            "geographic_area": {
                "description": "Geographic focus area",
                "type": "multiselect",
                "common_values": ["Virginia", "Maryland", "North Carolina", "District of Columbia", "National"]
            },
            "funding_type": {
                "description": "Type of funding opportunity",
                "type": "multiselect",
                "options": ["grant", "contract", "cooperative_agreement", "loan", "tax_credit"]
            }
        }
        
        return {
            "available_filters": filters,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get discovery filters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Processor Information

@router.get("/processors")
async def get_discovery_processors() -> Dict[str, Any]:
    """Get information about available discovery processors."""
    try:
        processor_summary = get_processor_summary()
        
        # Filter for discovery-related processors
        discovery_processors = {}
        discovery_keywords = ["bmf", "propublica", "grants", "usaspending", "foundation", "discovery", "fetch"]
        
        for proc_name, proc_info in processor_summary.items():
            if any(keyword in proc_name.lower() for keyword in discovery_keywords):
                discovery_processors[proc_name] = proc_info
        
        return {
            "discovery_processors": discovery_processors,
            "total_processors": len(discovery_processors),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get discovery processors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/processors/summary")
async def get_processors_summary() -> Dict[str, Any]:
    """Get summary of all available processors."""
    try:
        processor_summary = get_processor_summary()
        return {
            "processors": processor_summary,
            "total_count": len(processor_summary),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get processor summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Discovery Sessions and History

@router.get("/sessions")
async def get_discovery_sessions(
    limit: int = Query(default=20, le=100)
) -> Dict[str, Any]:
    """Get recent discovery sessions."""
    try:
        # In a real implementation, this would fetch from a sessions store
        # For now, return mock data
        sessions = []
        for i in range(min(limit, 5)):  # Mock data
            sessions.append({
                "session_id": f"session_{i+1}",
                "profile_id": f"profile_{i+1}",
                "tracks": ["nonprofit", "government"],
                "results_count": 25 + i * 10,
                "created_at": datetime.now().isoformat(),
                "status": "completed"
            })
        
        return {
            "discovery_sessions": sessions,
            "total_sessions": len(sessions),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get discovery sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_discovery_session(session_id: str) -> Dict[str, Any]:
    """Get details of a specific discovery session."""
    try:
        # Mock session data
        session = {
            "session_id": session_id,
            "profile_id": "profile_1",
            "tracks": ["nonprofit", "government"],
            "parameters": {
                "max_results": 100,
                "include_entity_cache": True
            },
            "results_count": 45,
            "status": "completed",
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        }
        
        return {
            "session": session,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get discovery session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))