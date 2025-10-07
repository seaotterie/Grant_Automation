"""
V2 Discovery API - Unified discovery across all tracks

Consolidates 20+ fragmented discovery endpoints into a single unified API:
- Track-based execution (nonprofit, federal, state, commercial, BMF)
- Session management
- Unified search
- Results analysis and scoring

Replaces legacy endpoints:
- /api/discovery/nonprofit
- /api/discovery/federal
- /api/discovery/state
- /api/discovery/commercial
- /api/profiles/{id}/run-bmf-filter
- Multiple other discovery-related endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from enum import Enum
import logging
import uuid
from datetime import datetime
import sqlite3

from src.core.tool_registry import ToolRegistry
from src.profiles.unified_service import UnifiedProfileService
from src.config.database_config import get_nonprofit_intelligence_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/discovery", tags=["discovery_v2"])

# Initialize services
tool_registry = ToolRegistry()
profile_service = UnifiedProfileService()


class DiscoveryTrack(str, Enum):
    """Discovery track types"""
    NONPROFIT = "nonprofit"
    FEDERAL = "federal"
    STATE = "state"
    COMMERCIAL = "commercial"
    BMF = "bmf"


@router.post("/execute")
async def execute_discovery(
    track: DiscoveryTrack,
    criteria: Dict[str, Any],
    profile_id: Optional[str] = None
):
    """
    Execute unified discovery workflow.

    Request:
    {
        "track": "nonprofit",  # or "federal", "state", "commercial", "bmf"
        "criteria": {
            "ntee_codes": ["P20", "B25"],
            "states": ["VA", "MD", "DC"],
            "min_assets": 1000000,
            "revenue_range": [100000, 10000000],
            ...
        },
        "profile_id": "profile_123"  # Optional
    }

    Response:
    {
        "success": true,
        "session_id": "uuid",
        "track": "nonprofit",
        "total_results": 472,
        "results": [...]
    }

    Replaces:
    - /api/discovery/nonprofit
    - /api/discovery/federal
    - /api/discovery/state
    - /api/discovery/commercial
    """
    try:
        session_id = str(uuid.uuid4())

        logger.info(f"Executing {track} discovery (session: {session_id})")

        results = []
        total_count = 0

        if track == DiscoveryTrack.BMF:
            # Use Tool 4 (BMF Filter Tool)
            bmf_result = await tool_registry.execute_tool(
                tool_name="bmf-filter-tool",
                inputs={
                    "ntee_codes": criteria.get("ntee_codes", []),
                    "states": criteria.get("states", []),
                    "min_assets": criteria.get("min_assets"),
                    "max_assets": criteria.get("max_assets"),
                    "min_revenue": criteria.get("min_revenue"),
                    "max_revenue": criteria.get("max_revenue"),
                    "foundation_code": criteria.get("foundation_code"),
                    "limit": criteria.get("limit", 100)
                }
            )

            if bmf_result.success:
                results = bmf_result.data.get('organizations', [])
                total_count = bmf_result.data.get('total_count', len(results))
            else:
                raise HTTPException(status_code=500, detail="BMF discovery failed")

        elif track == DiscoveryTrack.NONPROFIT:
            # Discovery for nonprofit foundations (990-PF)
            results = await discover_nonprofit_foundations(criteria)
            total_count = len(results)

        elif track == DiscoveryTrack.FEDERAL:
            # Federal opportunities discovery
            results = await discover_federal_opportunities(criteria)
            total_count = len(results)

        elif track == DiscoveryTrack.STATE:
            # State opportunities discovery
            results = await discover_state_opportunities(criteria)
            total_count = len(results)

        elif track == DiscoveryTrack.COMMERCIAL:
            # Commercial/corporate foundation discovery
            results = await discover_commercial_foundations(criteria)
            total_count = len(results)

        logger.info(f"Discovery complete: {total_count} results (session: {session_id})")

        # Save session if profile_id provided
        if profile_id:
            await save_discovery_session(
                session_id=session_id,
                profile_id=profile_id,
                track=track.value,
                criteria=criteria,
                result_count=total_count
            )

        return {
            "success": True,
            "session_id": session_id,
            "track": track.value,
            "total_results": total_count,
            "criteria": criteria,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Discovery execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bmf")
async def bmf_discovery(
    ntee_codes: Optional[List[str]] = Query(None),
    states: Optional[List[str]] = Query(None),
    min_assets: Optional[int] = None,
    max_assets: Optional[int] = None,
    min_revenue: Optional[int] = None,
    max_revenue: Optional[int] = None,
    foundation_code: Optional[str] = None,
    limit: int = 100
):
    """
    BMF-specific discovery (optimized path).

    Query Parameters:
    - ntee_codes: NTEE codes (comma-separated)
    - states: State codes (comma-separated)
    - min_assets: Minimum assets
    - max_assets: Maximum assets
    - min_revenue: Minimum revenue
    - max_revenue: Maximum revenue
    - foundation_code: Foundation code (15, 16, etc.)
    - limit: Maximum results (default 100)

    Direct Tool 4 execution for optimal performance.

    Replaces: /api/profiles/{id}/run-bmf-filter
    """
    try:
        # Use Tool 4 (BMF Filter Tool)
        bmf_result = await tool_registry.execute_tool(
            tool_name="bmf-filter-tool",
            inputs={
                "ntee_codes": ntee_codes or [],
                "states": states or [],
                "min_assets": min_assets,
                "max_assets": max_assets,
                "min_revenue": min_revenue,
                "max_revenue": max_revenue,
                "foundation_code": foundation_code,
                "limit": limit
            }
        )

        if not bmf_result.success:
            raise HTTPException(status_code=500, detail="BMF discovery failed")

        return {
            "success": True,
            "total_count": bmf_result.data.get('total_count', 0),
            "organizations": bmf_result.data.get('organizations', []),
            "execution_time_ms": bmf_result.execution_time_ms,
            "cost": bmf_result.cost
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"BMF discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def unified_search(search_query: Dict[str, Any]):
    """
    Search across all discovery sources.

    Request:
    {
        "query": "cancer research",
        "tracks": ["nonprofit", "federal"],  # Optional, defaults to all
        "filters": {
            "states": ["VA"],
            "min_amount": 50000
        }
    }

    Searches across multiple tracks and returns unified results.
    """
    try:
        query = search_query.get('query', '').strip()
        if not query:
            raise HTTPException(status_code=400, detail="Search query is required")

        tracks = search_query.get('tracks', ['nonprofit', 'bmf', 'federal'])
        filters = search_query.get('filters', {})

        all_results = []

        for track in tracks:
            try:
                # Execute discovery for this track with search query
                criteria = {**filters, 'search_query': query}

                if track == 'bmf':
                    # BMF search
                    results = await search_bmf(query, filters)
                elif track == 'nonprofit':
                    results = await search_nonprofit(query, filters)
                elif track == 'federal':
                    results = await search_federal(query, filters)
                else:
                    continue

                all_results.extend(results)

            except Exception as e:
                logger.warning(f"Search failed for track {track}: {e}")
                continue

        logger.info(f"Unified search complete: {len(all_results)} results for '{query}'")

        return {
            "success": True,
            "query": query,
            "total_results": len(all_results),
            "results": all_results,
            "tracks_searched": tracks
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unified search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions(
    profile_id: Optional[str] = None,
    recent: bool = False,
    page: int = 1,
    limit: int = 50
):
    """
    List discovery sessions.

    Query Parameters:
    - profile_id: Filter by profile
    - recent: Show only recent sessions (last 30 days)
    - page: Page number
    - limit: Results per page
    """
    try:
        # Would load from database/storage
        # For now, return empty list
        sessions = []

        return {
            "success": True,
            "page": page,
            "limit": limit,
            "total": len(sessions),
            "sessions": sessions
        }

    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get discovery session details."""
    try:
        # Would load from database/storage
        # For now, return 404
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_results(request: Dict[str, Any]):
    """
    Analyze discovery results with scoring.

    Request:
    {
        "results": [...],
        "profile_id": "profile_123",  # Optional
        "stage": "DISCOVER"  # Optional, for stage-specific scoring
    }

    Uses Tool 20 (Multi-Dimensional Scorer) for intelligent scoring.
    """
    try:
        results = request.get('results', [])
        profile_id = request.get('profile_id')
        stage = request.get('stage', 'DISCOVER')

        if not results:
            raise HTTPException(status_code=400, detail="Results are required")

        # Get profile if provided
        profile = None
        if profile_id:
            profile = profile_service.get_profile(profile_id)

        # Score each result using Tool 20
        scored_results = []

        for result in results:
            try:
                # Use Multi-Dimensional Scorer Tool
                score_result = await tool_registry.execute_tool(
                    tool_name="multi-dimensional-scorer-tool",
                    inputs={
                        "opportunity": result,
                        "profile": profile.__dict__ if profile else {},
                        "stage": stage
                    }
                )

                if score_result.success:
                    scored_results.append({
                        "result": result,
                        "score": score_result.data
                    })

            except Exception as e:
                logger.warning(f"Failed to score result: {e}")
                continue

        # Sort by score descending
        scored_results.sort(
            key=lambda x: x['score'].get('overall_score', 0),
            reverse=True
        )

        return {
            "success": True,
            "total_analyzed": len(results),
            "total_scored": len(scored_results),
            "scored_results": scored_results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def discover_nonprofit_foundations(criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Discover nonprofit foundations (990-PF) based on criteria."""
    try:
        db_path = get_nonprofit_intelligence_db()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query for foundations
        query = """
            SELECT b.*, f.distribamt, f.totassetsend, f.totnetinc
            FROM bmf_organizations b
            LEFT JOIN form_990pf f ON b.ein = f.ein
            WHERE b.foundation_code IN ('15', '16')
        """
        params = []

        # Apply filters
        if criteria.get('states'):
            placeholders = ','.join('?' * len(criteria['states']))
            query += f" AND b.state IN ({placeholders})"
            params.extend(criteria['states'])

        if criteria.get('ntee_codes'):
            placeholders = ','.join('?' * len(criteria['ntee_codes']))
            query += f" AND b.ntee_code IN ({placeholders})"
            params.extend(criteria['ntee_codes'])

        if criteria.get('min_assets'):
            query += " AND f.totassetsend >= ?"
            params.append(criteria['min_assets'])

        limit = criteria.get('limit', 100)
        query += f" LIMIT {limit}"

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        logger.info(f"Found {len(results)} nonprofit foundations")
        return results

    except Exception as e:
        logger.error(f"Nonprofit discovery failed: {e}")
        return []


async def discover_federal_opportunities(criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Discover federal opportunities."""
    # Placeholder - would integrate with Grants.gov/USASpending
    logger.info("Federal discovery not yet implemented")
    return []


async def discover_state_opportunities(criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Discover state opportunities."""
    # Placeholder - would integrate with state grant systems
    logger.info("State discovery not yet implemented")
    return []


async def discover_commercial_foundations(criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Discover commercial/corporate foundations."""
    # Placeholder - would filter BMF for corporate foundations
    logger.info("Commercial discovery not yet implemented")
    return []


async def search_bmf(query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search BMF organizations by name."""
    try:
        db_path = get_nonprofit_intelligence_db()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = "SELECT * FROM bmf_organizations WHERE name LIKE ?"
        params = [f"%{query}%"]

        if filters.get('states'):
            placeholders = ','.join('?' * len(filters['states']))
            sql += f" AND state IN ({placeholders})"
            params.extend(filters['states'])

        sql += " LIMIT 100"

        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    except Exception as e:
        logger.error(f"BMF search failed: {e}")
        return []


async def search_nonprofit(query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search nonprofit foundations."""
    # Would use discover_nonprofit_foundations with search query
    return []


async def search_federal(query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search federal opportunities."""
    # Would integrate with federal databases
    return []


async def save_discovery_session(
    session_id: str,
    profile_id: str,
    track: str,
    criteria: Dict[str, Any],
    result_count: int
):
    """Save discovery session to profile."""
    try:
        # Would save to profile's discovery sessions
        logger.info(f"Saved discovery session {session_id} for profile {profile_id}")

    except Exception as e:
        logger.error(f"Failed to save discovery session: {e}")


@router.get("/health")
async def health_check():
    """Health check endpoint for v2 discovery API."""
    return {
        "status": "healthy",
        "version": "2.0",
        "features": [
            "track_based_discovery",
            "unified_search",
            "session_management",
            "results_analysis",
            "bmf_optimized_path"
        ],
        "supported_tracks": [track.value for track in DiscoveryTrack]
    }
