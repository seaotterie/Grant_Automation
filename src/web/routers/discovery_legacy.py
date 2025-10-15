"""
Legacy Discovery API - Backward Compatibility Aliases

Provides backward-compatible endpoints for tests expecting /api/discovery/ routes.
All endpoints delegate to the modern /api/v2/discovery/ endpoints.

Legacy Endpoints (for test compatibility):
- POST /api/discovery/bmf/search → /api/v2/discovery/execute (track=bmf)
- GET /api/discovery/bmf/stats → BMF database statistics
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import sqlite3

from src.config.database_config import get_nonprofit_intelligence_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/discovery", tags=["discovery_legacy"])


@router.post("/bmf/search")
async def bmf_search(request: Dict[str, Any]):
    """
    BMF discovery search (legacy endpoint for test compatibility).

    Maps to: /api/v2/discovery/execute with track=bmf

    Request:
    {
        "ntee_codes": ["P20", "B25"],
        "states": ["VA", "MD"],
        "min_revenue": 100000,
        "max_revenue": 10000000,
        "limit": 100
    }
    """
    try:
        logger.info(f"Legacy BMF search called with criteria: {request}")

        # Extract criteria
        ntee_codes = request.get('ntee_codes', [])
        states = request.get('states', [])
        min_revenue = request.get('min_revenue')
        max_revenue = request.get('max_revenue')
        limit = request.get('limit', 100)

        # Query BMF database directly
        db_path = get_nonprofit_intelligence_db()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build SQL query with filters (NOTE: revenue/assets in form_990 table, not bmf_organizations)
        # For now, just filter by state and NTEE code from BMF table
        query = """
            SELECT b.*, f.totrevenue as revenue, f.totassetsend as assets
            FROM bmf_organizations b
            LEFT JOIN form_990 f ON b.ein = f.ein
            WHERE 1=1
        """
        params = []

        if states:
            placeholders = ','.join('?' * len(states))
            query += f" AND b.state IN ({placeholders})"
            params.extend(states)

        if ntee_codes:
            placeholders = ','.join('?' * len(ntee_codes))
            query += f" AND b.ntee_code IN ({placeholders})"
            params.extend(ntee_codes)

        if min_revenue:
            query += " AND f.totrevenue >= ?"
            params.append(min_revenue)

        if max_revenue:
            query += " AND f.totrevenue <= ?"
            params.append(max_revenue)

        query += f" LIMIT {limit}"

        logger.info(f"Executing query: {query[:200]}... with params: {params}")
        cursor.execute(query, params)
        rows = cursor.fetchall()

        organizations = []
        for row in rows:
            organizations.append({
                'ein': row['ein'],
                'name': row['name'],
                'state': row['state'],
                'city': row['city'],
                'ntee_code': row['ntee_code'],
                'revenue': row['revenue'],
                'assets': row['assets'],
                'foundation_code': row['foundation_code']
            })

        conn.close()

        total_count = len(organizations)
        logger.info(f"BMF search found {total_count} organizations")

        return {
            "success": True,
            "results": organizations,
            "organizations": organizations,  # Alias for compatibility
            "count": total_count,
            "total_count": total_count,
            "criteria": request
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"BMF search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bmf/stats")
async def bmf_stats():
    """
    Get BMF database statistics (legacy endpoint for test compatibility).

    Returns:
    {
        "total_organizations": 700488,
        "database_version": "2024_q4",
        "last_updated": "..."
    }
    """
    try:
        db_path = get_nonprofit_intelligence_db()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get total organizations count
        cursor.execute("SELECT COUNT(*) FROM bmf_organizations")
        total_orgs = cursor.fetchone()[0]

        # Get foundation count
        cursor.execute("SELECT COUNT(*) FROM bmf_organizations WHERE foundation_code IN ('15', '16')")
        foundation_count = cursor.fetchone()[0]

        # Get state distribution
        cursor.execute("""
            SELECT state, COUNT(*) as count
            FROM bmf_organizations
            GROUP BY state
            ORDER BY count DESC
            LIMIT 10
        """)
        top_states = [{"state": row[0], "count": row[1]} for row in cursor.fetchall()]

        conn.close()

        logger.info(f"BMF stats: {total_orgs} total organizations")

        return {
            "success": True,
            "total_organizations": total_orgs,
            "total": total_orgs,  # Alias
            "count": total_orgs,  # Alias
            "foundation_count": foundation_count,
            "top_states": top_states,
            "database": "nonprofit_intelligence.db",
            "status": "operational"
        }

    except Exception as e:
        logger.error(f"Failed to get BMF stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bmf/enhanced-search")
@router.post("/bmf/enhanced-search")
async def bmf_enhanced_search(request: Dict[str, Any] = None):
    """
    Enhanced BMF discovery with financial intelligence filters (legacy endpoint).

    Request:
    {
        "criteria": {
            "ntee_codes": ["P20"],
            "states": ["VA"],
            "revenue_range": [500000, 5000000]
        },
        "financial_filters": {
            "foundation_grants_paid": true,
            "min_assets": 1000000,
            "grant_capacity": "Major"
        },
        "limit": 50
    }
    """
    try:
        if request is None:
            request = {}

        criteria = request.get('criteria', {})
        financial_filters = request.get('financial_filters', {})
        limit = request.get('limit', 50)

        # Extract filters
        ntee_codes = criteria.get('ntee_codes', [])
        states = criteria.get('states', [])
        revenue_range = criteria.get('revenue_range', [None, None])
        min_revenue = revenue_range[0] if len(revenue_range) > 0 else None
        max_revenue = revenue_range[1] if len(revenue_range) > 1 else None
        min_assets = financial_filters.get('min_assets')

        # Filter foundations if requested
        foundation_code = None
        if financial_filters.get('foundation_grants_paid'):
            foundation_code = '16'  # Private grantmaking foundations

        # Query BMF database directly (JOIN with form_990 for revenue/assets)
        db_path = get_nonprofit_intelligence_db()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build SQL query with filters
        query = """
            SELECT b.*, f.totrevenue as revenue, f.totassetsend as assets
            FROM bmf_organizations b
            LEFT JOIN form_990 f ON b.ein = f.ein
            WHERE 1=1
        """
        params = []

        if states:
            placeholders = ','.join('?' * len(states))
            query += f" AND b.state IN ({placeholders})"
            params.extend(states)

        if ntee_codes:
            placeholders = ','.join('?' * len(ntee_codes))
            query += f" AND b.ntee_code IN ({placeholders})"
            params.extend(ntee_codes)

        if min_revenue:
            query += " AND f.totrevenue >= ?"
            params.append(min_revenue)

        if max_revenue:
            query += " AND f.totrevenue <= ?"
            params.append(max_revenue)

        if min_assets:
            query += " AND f.totassetsend >= ?"
            params.append(min_assets)

        if foundation_code:
            query += " AND b.foundation_code = ?"
            params.append(foundation_code)

        query += f" LIMIT {limit}"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        organizations = []
        for row in rows:
            organizations.append({
                'ein': row['ein'],
                'name': row['name'],
                'state': row['state'],
                'city': row['city'],
                'ntee_code': row['ntee_code'],
                'revenue': row['revenue'],
                'assets': row['assets'],
                'foundation_code': row['foundation_code']
            })

        conn.close()

        logger.info(f"Enhanced BMF search found {len(organizations)} organizations")

        return {
            "success": True,
            "results": organizations,
            "count": len(organizations),
            "criteria": {
                "ntee_codes": ntee_codes,
                "states": states,
                "min_revenue": min_revenue,
                "max_revenue": max_revenue,
                "min_assets": min_assets,
                "foundation_code": foundation_code,
                "limit": limit
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced BMF search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
