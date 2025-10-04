"""
Opportunities API Endpoints - SCREENING Stage Support

Endpoints for viewing opportunity details, running web research, and promoting to INTELLIGENCE stage.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import logging
import sqlite3
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/opportunities", tags=["opportunities"])


# Helper function to get opportunity from temporary discovery results
# Note: In production, opportunities would be stored in database
# For now, we'll return mock data structure

@router.get("/{opportunity_id}/details")
async def get_opportunity_details(opportunity_id: str):
    """
    Get full opportunity details for SCREENING stage modal.

    Returns:
    {
        "organization_name": "United Way of Greater Richmond",
        "ein": "54-0505822",
        "location": {"state": "VA", "city": "Richmond"},
        "revenue": 2543891,
        "overall_score": 0.89,
        "confidence": "high",
        "stage_category": "auto_qualified",
        "dimensional_scores": {
            "mission_alignment": {
                "raw_score": 0.92,
                "weight": 0.30,
                "weighted_score": 0.276,
                "data_quality": 1.0
            },
            ... 4 more dimensions
        },
        "990_data": {
            "form_type": "990",
            "tax_year": 2023,
            "revenue": 2543891,
            "expenses": 2398102,
            "assets": 1187543,
            "liabilities": 543211,
            "program_ratio": 82.0,
            "raw_data": {...}
        },
        "grant_history": null,  # Only for 990-PF
        "web_search_complete": false,
        "web_data": null
    }
    """
    try:
        # TODO: In production, query from opportunities table
        # For now, return error indicating this should be called after discovery
        raise HTTPException(
            status_code=501,
            detail="Opportunity details endpoint not fully implemented. Use data from /discover response."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get opportunity details for {opportunity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{opportunity_id}/research")
async def research_opportunity(opportunity_id: str):
    """
    Run on-demand Web Intelligence (Scrapy) for an opportunity.

    This endpoint triggers Scrapy web scraping to gather:
    - Website URL
    - Leadership team
    - Recent news
    - Contact information
    - Social media links

    Returns:
    {
        "success": true,
        "opportunity_id": "...",
        "web_data": {
            "website": "www.unitedwayrichmond.org",
            "leadership": [
                {"name": "John Smith", "title": "CEO"},
                {"name": "Jane Doe", "title": "Board Chair"}
            ],
            "recent_news": [
                {"title": "...", "date": "2024-03-15"}
            ],
            "contact": {
                "email": "info@...",
                "phone": "(804) 555-1234",
                "address": "..."
            },
            "social_media": {
                "linkedin": "...",
                "twitter": "..."
            }
        },
        "execution_time": 32.5
    }
    """
    try:
        import time
        start_time = time.time()

        # TODO: Step 1 - Get opportunity EIN
        # TODO: Step 2 - Call Web Intelligence Tool (Scrapy)
        # TODO: Step 3 - Save results to database
        # TODO: Step 4 - Return web_data

        # Placeholder response
        raise HTTPException(
            status_code=501,
            detail="Web research endpoint not fully implemented. Scrapy integration pending."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web research failed for {opportunity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{opportunity_id}/promote")
async def promote_to_intelligence(opportunity_id: str, request: Dict[str, Any]):
    """
    Promote opportunity from SCREENING to INTELLIGENCE stage.

    This marks the opportunity for deeper AI-powered analysis.

    Request:
    {
        "notes": "High priority foundation with strong mission alignment"
    }

    Returns:
    {
        "success": true,
        "opportunity_id": "...",
        "promoted_to": "intelligence",
        "timestamp": "2024-03-15T10:30:00Z"
    }
    """
    try:
        notes = request.get('notes', '')

        # TODO: Update opportunity stage in database
        # TODO: Mark for INTELLIGENCE stage processing

        return {
            "success": True,
            "opportunity_id": opportunity_id,
            "promoted_to": "intelligence",
            "timestamp": "2024-03-15T10:30:00Z",
            "notes": notes
        }

    except Exception as e:
        logger.error(f"Failed to promote opportunity {opportunity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for opportunities API."""
    return {
        "status": "healthy",
        "version": "1.0",
        "endpoints": [
            "GET /api/v2/opportunities/{id}/details",
            "POST /api/v2/opportunities/{id}/research",
            "POST /api/v2/opportunities/{id}/promote"
        ]
    }
