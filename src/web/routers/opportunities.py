"""
Opportunities API Endpoints - SCREENING Stage Support

Endpoints for viewing opportunity details, running web research, and promoting
to INTELLIGENCE stage.

Phase C refactor: shared helpers, pydantic models, SSRF validation, and the
Claude web-interpretation helper live in opportunities_common.py. The 990
filings/PDF extraction endpoints moved to opportunities_990.py.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import asyncio
import aiohttp
import logging
import json
import re
import uuid
from datetime import datetime, timezone

from src.database.database_manager import DatabaseManager
from src.config.database_config import get_catalynx_db
from src.web.routers.opportunities_common import (
    WEB_DATA_TTL_DAYS as _WEB_DATA_TTL_DAYS,
    WebResearchRequest,
    BatchWebResearchRequest,
    WebsiteUrlUpdate,
    interpret_with_claude as _interpret_with_claude,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/opportunities", tags=["opportunities"])

# Initialize database manager
database_manager = DatabaseManager(get_catalynx_db())

# In-memory batch job store (single-user app — no persistence needed)
_batch_jobs: Dict[str, Dict] = {}


@router.get("/{opportunity_id}/details", summary="Get full opportunity details including all analysis data")
async def get_opportunity_details(opportunity_id: str, profile_id: Optional[str] = None):
    """
    Get full opportunity details for SCREENING stage modal.

    Returns complete opportunity data including:
    - Organization information
    - Dimensional scores
    - 990 financial data
    - Grant history (if foundation)
    - Web research data (if available)

    Query params:
    - profile_id: Optional profile ID for faster lookup
    """
    try:
        # If profile_id not provided, query by opportunity_id only
        if profile_id:
            opportunity = database_manager.get_opportunity(profile_id, opportunity_id)
        else:
            # Query without profile_id - find any opportunity with this ID
            conn = database_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Opportunity {opportunity_id} not found"
                )

            # Convert row to Opportunity object
            from src.database.database_manager import Opportunity
            import json

            opportunity = Opportunity(
                id=row[0],
                profile_id=row[1],
                organization_name=row[2],
                ein=row[3],
                current_stage=row[4],
                stage_history=json.loads(row[5]) if row[5] else None,
                overall_score=row[6],
                confidence_level=row[7],
                auto_promotion_eligible=row[8],
                promotion_recommended=row[9],
                scored_at=row[10],
                scorer_version=row[11],
                analysis_discovery=json.loads(row[12]) if row[12] else None,
                analysis_plan=json.loads(row[13]) if row[13] else None,
                analysis_analyze=json.loads(row[14]) if row[14] else None,
                analysis_examine=json.loads(row[15]) if row[15] else None,
                analysis_approach=json.loads(row[16]) if row[16] else None,
                user_rating=row[17],
                priority_level=row[18],
                tags=json.loads(row[19]) if row[19] else None,
                notes=row[20],
                promotion_history=json.loads(row[21]) if row[21] else None,
                legacy_mappings=json.loads(row[22]) if row[22] else None,
                processing_status=row[23],
                processing_errors=json.loads(row[24]) if row[24] else None,
                source=row[25],
                discovery_date=row[26],
                last_analysis_date=row[27],
                created_at=row[28],
                updated_at=row[29]
            )

        if not opportunity:
            raise HTTPException(
                status_code=404,
                detail=f"Opportunity {opportunity_id} not found"
            )

        # Extract discovery analysis data
        discovery_analysis = opportunity.analysis_discovery or {}
        dimensional_scores = discovery_analysis.get('dimensional_scores', {})
        location = discovery_analysis.get('location', {})

        # Determine confidence level
        confidence = "high" if opportunity.confidence_level and opportunity.confidence_level >= 0.75 else "medium"
        if opportunity.confidence_level and opportunity.confidence_level < 0.6:
            confidence = "low"

        # Build response
        # Convert discovery_date if it's a string
        discovery_date_iso = None
        if opportunity.discovery_date:
            if isinstance(opportunity.discovery_date, str):
                discovery_date_iso = opportunity.discovery_date
            else:
                discovery_date_iso = opportunity.discovery_date.isoformat()

        response = {
            "opportunity_id": opportunity.id,
            "organization_name": opportunity.organization_name,
            "ein": opportunity.ein,
            "location": location,
            "overall_score": opportunity.overall_score,
            "confidence": confidence,
            "stage_category": discovery_analysis.get('stage_category', 'low_priority'),
            "dimensional_scores": dimensional_scores,
            "990_data": discovery_analysis.get('990_data'),
            "grant_history": discovery_analysis.get('grant_history'),
            "web_search_complete": discovery_analysis.get('web_search_complete', False),
            "web_data": discovery_analysis.get('web_data'),  # Return stored web intelligence data
            "current_stage": opportunity.current_stage,
            "discovery_date": discovery_date_iso,
            "notes": opportunity.notes,
            "tags": opportunity.tags or []
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get opportunity details for {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{opportunity_id}/research", summary="Run Scrapy web intelligence on an opportunity's funder")
async def research_opportunity(
    opportunity_id: str,
    request_body: WebResearchRequest = WebResearchRequest(),
    profile_id: Optional[str] = None
):
    """
    Run on-demand Web Intelligence (Scrapy) for an opportunity.

    This endpoint triggers Tool 25 (Web Intelligence Tool) to gather:
    - Website URL and verification
    - Leadership team information
    - Recent news and updates
    - Contact information
    - Social media presence

    Args:
        opportunity_id: ID of the opportunity to research
        request_body: Optional website URL to use for scraping
        profile_id: Optional profile ID for database lookup

    Returns enriched opportunity data.
    """
    try:
        # Get opportunity from database (same logic as get_opportunity_details)
        if profile_id:
            opportunity = database_manager.get_opportunity(profile_id, opportunity_id)
        else:
            conn = database_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")

            # Extract just what we need for this endpoint
            opportunity = type('obj', (object,), {
                'id': row[0],
                'profile_id': row[1],
                'organization_name': row[2],
                'ein': row[3]
            })()

        if not opportunity:
            raise HTTPException(
                status_code=404,
                detail=f"Opportunity {opportunity_id} not found"
            )

        # Extract EIN for web intelligence gathering
        ein = opportunity.ein
        if not ein:
            raise HTTPException(
                status_code=400,
                detail="Opportunity does not have an EIN. Web research requires an EIN."
            )

        logger.info(f"Starting web research for opportunity {opportunity_id} (EIN: {ein})")

        # --- EIN Intelligence Cache check ---
        cached = database_manager.get_ein_intelligence(ein)
        if cached and cached.get("web_data") and cached.get("web_data_fetched_at"):
            try:
                fetched_dt = datetime.fromisoformat(cached["web_data_fetched_at"])
                age_days = (datetime.now() - fetched_dt).days
                if age_days < _WEB_DATA_TTL_DAYS:
                    logger.info(f"Cache hit: web_data for EIN {ein} (age {age_days}d) — skipping Tool 25")
                    web_data = cached["web_data"]
                    # Write back to this opportunity's analysis_discovery so the modal shows it
                    conn = database_manager.get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT analysis_discovery, website_url FROM opportunities WHERE id = ?", (opportunity_id,)
                    )
                    row = cursor.fetchone()
                    if row and row[0]:
                        ad = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                        ad["web_data"] = web_data
                        ad["web_search_complete"] = True
                        found_url = web_data.get("website") if isinstance(web_data, dict) else None
                        existing_url = row[1]
                        if found_url and not existing_url:
                            cursor.execute(
                                "UPDATE opportunities SET analysis_discovery = ?, website_url = ?, url_source = ?, url_discovered_at = ?, updated_at = ? WHERE id = ?",
                                (json.dumps(ad), found_url, "web_research", datetime.now().isoformat(), datetime.now().isoformat(), opportunity_id),
                            )
                        else:
                            cursor.execute(
                                "UPDATE opportunities SET analysis_discovery = ?, updated_at = ? WHERE id = ?",
                                (json.dumps(ad), datetime.now().isoformat(), opportunity_id),
                            )
                        conn.commit()
                    conn.close()
                    return {
                        "success": True,
                        "opportunity_id": opportunity_id,
                        "web_data": web_data,
                        "web_search_complete": True,
                        "execution_time": 0.0,
                        "pages_scraped": 0,
                        "data_quality_score": web_data.get("data_quality_score"),
                        "ein": ein,
                        "organization_name": opportunity.organization_name,
                        "cache_hit": True,
                    }
            except Exception as cache_err:
                logger.warning(f"Cache read error for EIN {ein}: {cache_err}")

        # Integrate Tool 25 Web Intelligence
        try:
            import sys
            from pathlib import Path

            # Add tools directory to path for imports
            tools_dir = Path(__file__).parent.parent.parent / 'tools' / 'web-intelligence-tool'
            sys.path.insert(0, str(tools_dir))

            logger.info(f"Tool 25 path: {tools_dir}")
            logger.info(f"Tool 25 exists: {tools_dir.exists()}")

            from tools.web_intelligence_tool.app.web_intelligence_tool import (
                WebIntelligenceTool,
                WebIntelligenceRequest,
                UseCase
            )

            # Create Tool 25 instance and request
            tool = WebIntelligenceTool()

            # Build request with optional user-provided URL
            tool_request_params = {
                'ein': ein,
                'organization_name': opportunity.organization_name,
                'use_case': UseCase.PROFILE_BUILDER  # Use Case 1: Profile Builder (implemented)
            }

            # Add user-provided URL if available
            if request_body.website_url:
                tool_request_params['user_provided_url'] = request_body.website_url
                logger.info(f"Using user-provided URL: {request_body.website_url}")

            request = WebIntelligenceRequest(**tool_request_params)

            logger.info(f"Executing Tool 25 for EIN {ein}")

            # Execute Tool 25 web scraping
            result = await tool.execute(request)

            logger.info(f"Tool 25 result: success={result.success}, errors={result.errors if hasattr(result, 'errors') else 'N/A'}")

            # Short-circuit: no URL found — return graceful 200 instead of 500
            if not result.success and result.errors and "no_url_found" in result.errors:
                logger.info(f"No URL found for opportunity {opportunity_id} (EIN: {ein}) — skipping web intelligence")
                return {
                    "success": False,
                    "reason": "no_url_found",
                    "web_search_complete": False,
                    "opportunity_id": opportunity_id,
                    "ein": ein,
                    "organization_name": opportunity.organization_name,
                }

            if result.success and result.intelligence_data:
                intelligence = result.intelligence_data

                # Check if result is new GrantFunderIntelligence (Haiku agent) or
                # legacy OrganizationIntelligence (Scrapy path, kept for compat)
                from tools.shared_schemas.grant_funder_intelligence import GrantFunderIntelligence as GFI
                if isinstance(intelligence, GFI):
                    # --- Haiku agent path ---
                    contact_obj = None
                    if intelligence.contact_information:
                        contact_obj = {"email": None, "phone": None, "address": intelligence.contact_information}
                    web_data = {
                        "website": intelligence.source_url,
                        "website_verified": intelligence.confidence_score > 0.6,
                        "mission": intelligence.mission_statement,
                        "leadership": [
                            {"name": m, "title": "", "email": None, "confidence": "medium"}
                            for m in (intelligence.board_members or [])
                        ],
                        "leadership_cross_validated": False,
                        "contact": contact_obj,
                        "social_media": {},
                        "programs": [
                            {"name": "", "description": d, "target_population": intelligence.population_focus}
                            for d in (intelligence.program_descriptions or [])
                        ],
                        "key_facts": intelligence.funding_priorities or [],
                        "grant_application_url": None,
                        "recent_news": [],
                        "data_quality_score": intelligence.confidence_score,
                        "pages_scraped": result.pages_scraped,
                        "execution_time": result.execution_time_seconds,
                        "ai_interpreted": True,
                        # Grant-specific fields stored alongside standard web_data
                        "accepts_applications": intelligence.accepts_applications,
                        "application_deadlines": intelligence.application_deadlines,
                        "application_process": intelligence.application_process,
                        "required_documents": intelligence.required_documents,
                        "geographic_limitations": intelligence.geographic_limitations,
                        "grant_size_range": intelligence.grant_size_range,
                        "grant_funder_intelligence": intelligence.to_dict(),
                    }
                    logger.info(f"Haiku web intelligence complete for {ein} (confidence={intelligence.confidence_score:.0%})")
                else:
                    # --- Legacy Scrapy path ---
                    scrapy_web_data = {
                        "website": intelligence.website_url,
                        "website_verified": intelligence.scraping_metadata.verification_confidence > 0.7,
                        "leadership": [
                            {
                                "name": leader.name,
                                "title": leader.title,
                                "email": leader.email,
                                "phone": leader.phone,
                                "bio": leader.bio,
                                "matches_990": leader.matches_990
                            }
                            for leader in intelligence.leadership
                        ],
                        "leadership_cross_validated": any(leader.matches_990 for leader in intelligence.leadership),
                        "contact": {
                            "email": intelligence.contact_info.email if intelligence.contact_info else None,
                            "phone": intelligence.contact_info.phone if intelligence.contact_info else None,
                            "address": intelligence.contact_info.mailing_address if intelligence.contact_info else None
                        } if intelligence.contact_info else None,
                        "social_media": intelligence.contact_info.social_media_links if intelligence.contact_info else {},
                        "mission": intelligence.mission_statement,
                        "programs": [
                            {"name": program.name, "description": program.description,
                             "target_population": program.target_population}
                            for program in intelligence.programs
                        ],
                        "grant_application_url": None,
                        "recent_news": [],
                        "data_quality_score": result.data_quality_score,
                        "pages_scraped": result.pages_scraped,
                        "execution_time": result.execution_time_seconds
                    }

                    scraped_urls = getattr(intelligence.scraping_metadata, "scraped_urls", []) or []
                    claude_result = None
                    if scraped_urls:
                        logger.info(f"Running Claude interpretation on {len(scraped_urls)} scraped URLs for {ein}")
                        claude_result = await _interpret_with_claude(scraped_urls, opportunity.organization_name, ein)

                    if claude_result:
                        web_data = {
                            "website": scrapy_web_data["website"],
                            "website_verified": scrapy_web_data["website_verified"],
                            "leadership": [
                                {"name": ldr.get("name", ""), "title": ldr.get("title", ""),
                                 "email": ldr.get("email"), "phone": None, "bio": None,
                                 "matches_990": False, "confidence": ldr.get("confidence", "medium")}
                                for ldr in (claude_result.get("leadership") or [])
                            ],
                            "leadership_cross_validated": scrapy_web_data["leadership_cross_validated"],
                            "contact": claude_result.get("contact") or scrapy_web_data["contact"],
                            "social_media": scrapy_web_data["social_media"],
                            "mission": claude_result.get("mission") or scrapy_web_data["mission"],
                            "programs": [
                                {"name": p.get("name", ""), "description": p.get("description", ""),
                                 "target_population": None}
                                for p in (claude_result.get("programs") or [])
                            ],
                            "key_facts": claude_result.get("key_facts") or [],
                            "interpretation_notes": claude_result.get("interpretation_notes"),
                            "grant_application_url": scrapy_web_data["grant_application_url"],
                            "recent_news": scrapy_web_data["recent_news"],
                            "data_quality_score": scrapy_web_data["data_quality_score"],
                            "pages_scraped": scrapy_web_data["pages_scraped"],
                            "execution_time": scrapy_web_data["execution_time"],
                            "ai_interpreted": True,
                            "web_data_scrapy_raw": scrapy_web_data,
                        }
                        logger.info(f"Claude web interpretation complete for {ein}")
                    else:
                        web_data = scrapy_web_data
                        web_data["ai_interpreted"] = False

                # Update opportunity in database with web data
                conn = database_manager.get_connection()
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT analysis_discovery, website_url FROM opportunities WHERE id = ?", (opportunity_id,)
                )
                row = cursor.fetchone()

                if row and row[0]:
                    import json
                    analysis_discovery = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    analysis_discovery['web_data'] = web_data
                    analysis_discovery['web_search_complete'] = True
                    found_url = web_data.get("website") if isinstance(web_data, dict) else None
                    existing_url = row[1]
                    if found_url and not existing_url:
                        cursor.execute(
                            "UPDATE opportunities SET analysis_discovery = ?, website_url = ?, url_source = ?, url_discovered_at = ?, updated_at = ? WHERE id = ?",
                            (json.dumps(analysis_discovery), found_url, "web_research", datetime.now().isoformat(), datetime.now().isoformat(), opportunity_id),
                        )
                    else:
                        cursor.execute(
                            "UPDATE opportunities SET analysis_discovery = ?, updated_at = ? WHERE id = ?",
                            (json.dumps(analysis_discovery), datetime.now().isoformat(), opportunity_id)
                        )
                    conn.commit()

                conn.close()

                logger.info(f"Web research completed successfully for {opportunity_id} - scraped {result.pages_scraped} pages in {result.execution_time_seconds:.2f}s")

                # --- Store in EIN intelligence cache ---
                try:
                    database_manager.upsert_ein_intelligence(
                        ein=ein,
                        org_name=opportunity.organization_name,
                        web_data=web_data,
                        web_data_fetched_at=datetime.now().isoformat(),
                        web_data_source="claude_interpreted" if web_data.get("ai_interpreted") else "scrapy_raw",
                    )
                    logger.info(f"Cached web_data for EIN {ein}")
                except Exception as cache_err:
                    logger.warning(f"Failed to cache web_data for EIN {ein}: {cache_err}")

                return {
                    "success": True,
                    "opportunity_id": opportunity_id,
                    "web_data": web_data,
                    "web_search_complete": True,
                    "execution_time": result.execution_time_seconds,
                    "pages_scraped": result.pages_scraped,
                    "data_quality_score": result.data_quality_score,
                    "ein": ein,
                    "organization_name": opportunity.organization_name
                }
            else:
                # Tool 25 failed - return error
                error_msg = "; ".join(result.errors) if result.errors else "Unknown error"
                logger.error(f"Tool 25 web research failed for {opportunity_id}: {error_msg}")
                raise HTTPException(status_code=500, detail="Web intelligence tool failed")

        except ImportError as e:
            logger.error(f"Failed to import Tool 25: {e}")
            logger.error(f"Tool 25 import error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")
        except Exception as e:
            logger.error(f"Tool 25 execution error for {opportunity_id}: {e}", exc_info=True)
            logger.error(f"Web research failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to research opportunity {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{opportunity_id}/research_placeholder")
async def research_opportunity_placeholder(opportunity_id: str):
    """
    PLACEHOLDER - Shows what web research would return.

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
        logger.error(f"Web research failed for {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{opportunity_id}/promote-with-notes", summary="Promote opportunity to Intelligence stage with reviewer notes")
async def promote_to_intelligence(opportunity_id: str, request: Dict[str, Any], profile_id: Optional[str] = None):
    """
    Promote opportunity from SCREENING to INTELLIGENCE stage.

    This marks the opportunity for deeper AI-powered analysis (4-tier intelligence system).

    Request:
    {
        "notes": "High priority foundation with strong mission alignment",
        "priority": "high"  # Optional: low, medium, high, urgent
    }

    Returns:
    {
        "success": true,
        "opportunity_id": "...",
        "promoted_to": "intelligence",
        "previous_stage": "discovery",
        "timestamp": "2024-03-15T10:30:00Z"
    }
    """
    try:
        # Get opportunity from database (same logic as get_opportunity_details)
        if profile_id:
            opportunity = database_manager.get_opportunity(profile_id, opportunity_id)
        else:
            conn = database_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")

            # Build full Opportunity object for update
            from src.database.database_manager import Opportunity
            import json

            opportunity = Opportunity(
                id=row[0],
                profile_id=row[1],
                organization_name=row[2],
                ein=row[3],
                current_stage=row[4],
                stage_history=json.loads(row[5]) if row[5] else None,
                overall_score=row[6],
                confidence_level=row[7],
                auto_promotion_eligible=row[8],
                promotion_recommended=row[9],
                scored_at=row[10],
                scorer_version=row[11],
                analysis_discovery=json.loads(row[12]) if row[12] else None,
                analysis_plan=json.loads(row[13]) if row[13] else None,
                analysis_analyze=json.loads(row[14]) if row[14] else None,
                analysis_examine=json.loads(row[15]) if row[15] else None,
                analysis_approach=json.loads(row[16]) if row[16] else None,
                user_rating=row[17],
                priority_level=row[18],
                tags=json.loads(row[19]) if row[19] else None,
                notes=row[20],
                promotion_history=json.loads(row[21]) if row[21] else None,
                legacy_mappings=json.loads(row[22]) if row[22] else None,
                processing_status=row[23],
                processing_errors=json.loads(row[24]) if row[24] else None,
                source=row[25],
                discovery_date=row[26],
                last_analysis_date=row[27],
                created_at=row[28],
                updated_at=row[29]
            )

        if not opportunity:
            raise HTTPException(
                status_code=404,
                detail=f"Opportunity {opportunity_id} not found"
            )

        # Extract request data
        notes = request.get('notes', '')
        priority = request.get('priority', 'medium')

        # Validate priority
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if priority not in valid_priorities:
            priority = 'medium'

        # Update opportunity stage and metadata
        previous_stage = opportunity.current_stage
        opportunity.current_stage = 'intelligence'  # Promoted to INTELLIGENCE stage
        opportunity.priority_level = priority

        # Append notes if provided
        if notes:
            existing_notes = opportunity.notes or ""
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            opportunity.notes = f"{existing_notes}\n\n[{timestamp_str}] Promoted to INTELLIGENCE:\n{notes}".strip()

        # Update promotion history
        promotion_history = opportunity.promotion_history or []
        promotion_history.append({
            "from_stage": previous_stage,
            "to_stage": "intelligence",
            "timestamp": datetime.now().isoformat(),
            "notes": notes,
            "priority": priority
        })
        opportunity.promotion_history = promotion_history

        # Update stage history
        stage_history = opportunity.stage_history or []
        stage_history.append({
            "stage": "intelligence",
            "timestamp": datetime.now().isoformat(),
            "action": "promoted_from_screening"
        })
        opportunity.stage_history = stage_history

        # Update timestamp
        opportunity.updated_at = datetime.now()

        # Save to database using SQL directly
        conn = database_manager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE opportunities
            SET current_stage = ?,
                stage_history = ?,
                priority_level = ?,
                notes = ?,
                promotion_history = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            opportunity.current_stage,
            json.dumps(opportunity.stage_history),
            opportunity.priority_level,
            opportunity.notes,
            json.dumps(opportunity.promotion_history),
            opportunity.updated_at.isoformat() if isinstance(opportunity.updated_at, datetime) else opportunity.updated_at,
            opportunity.id
        ))

        conn.commit()
        conn.close()

        logger.info(f"Promoted opportunity {opportunity_id} from {previous_stage} to intelligence stage")

        return {
            "success": True,
            "opportunity_id": opportunity_id,
            "promoted_to": "intelligence",
            "previous_stage": previous_stage,
            "timestamp": datetime.now().isoformat(),
            "priority": priority,
            "notes": notes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to promote opportunity {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{opportunity_id}/promote")
async def promote_category_level(opportunity_id: str):
    """
    Promote opportunity to next category_level or to intelligence stage.

    Promotion ladder:
    - low_priority → consider
    - consider → review
    - review → qualified
    - qualified → intelligence stage (workflow change)

    Returns updated opportunity with new category_level or current_stage.
    """
    try:
        # Get opportunity from database
        conn = database_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")

        # Parse current state
        opportunity_dict = dict(zip([col[0] for col in cursor.description], row))
        current_stage = opportunity_dict.get('current_stage', 'discovery')

        # Get category_level from analysis_discovery JSON field
        analysis_discovery = opportunity_dict.get('analysis_discovery', '{}')
        if isinstance(analysis_discovery, str):
            analysis_discovery = json.loads(analysis_discovery) if analysis_discovery else {}
        current_category = analysis_discovery.get('category_level', 'low_priority')

        # Determine promotion action
        new_category = current_category
        new_stage = current_stage
        action_taken = None

        if current_category == 'low_priority':
            new_category = 'consider'
            action_taken = 'promoted_to_consider'
        elif current_category == 'consider':
            new_category = 'review'
            action_taken = 'promoted_to_review'
        elif current_category == 'review':
            new_category = 'qualified'
            action_taken = 'promoted_to_qualified'
        elif current_category == 'qualified':
            # Already qualified - promote to intelligence stage
            new_stage = 'intelligence'
            action_taken = 'promoted_to_intelligence'
        else:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Cannot promote from {current_category}")

        # Update category_level in analysis_discovery JSON
        analysis_discovery['category_level'] = new_category

        # Update database
        timestamp = datetime.now().isoformat()
        cursor.execute("""
            UPDATE opportunities
            SET analysis_discovery = ?,
                current_stage = ?,
                updated_at = ?
            WHERE id = ?
        """, (json.dumps(analysis_discovery), new_stage, timestamp, opportunity_id))

        conn.commit()
        conn.close()

        logger.info(f"Promoted opportunity {opportunity_id}: {current_category} → {new_category}, stage: {current_stage} → {new_stage}")

        return {
            "success": True,
            "opportunity_id": opportunity_id,
            "action": action_taken,
            "previous_category": current_category,
            "new_category": new_category,
            "previous_stage": current_stage,
            "new_stage": new_stage,
            "message": f"Promoted from {current_category} to {new_category}" if new_category != current_category else f"Promoted to {new_stage} stage"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to promote opportunity {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{opportunity_id}/demote")
async def demote_category_level(opportunity_id: str):
    """
    Demote opportunity to previous category_level.

    Demotion ladder:
    - qualified → review
    - review → consider
    - consider → low_priority
    - low_priority → (cannot demote further)

    Cannot demote if current_stage != 'discovery' (already promoted to intelligence/approach).

    Returns updated opportunity with new category_level.
    """
    try:
        # Get opportunity from database
        conn = database_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")

        # Parse current state
        opportunity_dict = dict(zip([col[0] for col in cursor.description], row))
        current_stage = opportunity_dict.get('current_stage', 'discovery')

        # Get category_level from analysis_discovery JSON field
        analysis_discovery = opportunity_dict.get('analysis_discovery', '{}')
        if isinstance(analysis_discovery, str):
            analysis_discovery = json.loads(analysis_discovery) if analysis_discovery else {}
        current_category = analysis_discovery.get('category_level', 'low_priority')

        # Cannot demote if already moved past discovery
        if current_stage not in ['discovery', 'screening', 'prospects', 'qualified_prospects', 'candidates']:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"Cannot demote opportunity in {current_stage} stage. Only discovery/screening stage opportunities can be demoted."
            )

        # Determine demotion action
        new_category = current_category
        action_taken = None

        if current_category == 'qualified':
            new_category = 'review'
            action_taken = 'demoted_to_review'
        elif current_category == 'review':
            new_category = 'consider'
            action_taken = 'demoted_to_consider'
        elif current_category == 'consider':
            new_category = 'low_priority'
            action_taken = 'demoted_to_low_priority'
        elif current_category == 'low_priority':
            conn.close()
            raise HTTPException(status_code=400, detail="Cannot demote below low_priority")
        else:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Unknown category level: {current_category}")

        # Update category_level in analysis_discovery JSON
        analysis_discovery['category_level'] = new_category

        # Update database
        timestamp = datetime.now().isoformat()
        cursor.execute("""
            UPDATE opportunities
            SET analysis_discovery = ?,
                updated_at = ?
            WHERE id = ?
        """, (json.dumps(analysis_discovery), timestamp, opportunity_id))

        conn.commit()
        conn.close()

        logger.info(f"Demoted opportunity {opportunity_id}: {current_category} → {new_category}")

        return {
            "success": True,
            "opportunity_id": opportunity_id,
            "action": action_taken,
            "previous_category": current_category,
            "new_category": new_category,
            "message": f"Demoted from {current_category} to {new_category}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to demote opportunity {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{opportunity_id}/notes")
async def update_opportunity_notes(opportunity_id: str, request: Dict[str, Any]):
    """
    Update notes field for an opportunity.

    Request body:
    {
        "notes": "User notes text (max 2000 characters)"
    }

    Returns updated opportunity with new notes.
    """
    try:
        # Extract notes from request
        notes = request.get('notes', '')

        # Validate max 2000 characters
        if len(notes) > 2000:
            raise HTTPException(status_code=400, detail="Notes cannot exceed 2000 characters")

        # Get opportunity from database
        conn = database_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")

        # Update notes
        timestamp = datetime.now().isoformat()
        cursor.execute("""
            UPDATE opportunities
            SET notes = ?,
                updated_at = ?
            WHERE id = ?
        """, (notes, timestamp, opportunity_id))

        conn.commit()
        conn.close()

        logger.info(f"Updated notes for opportunity {opportunity_id} ({len(notes)} characters)")

        return {
            "success": True,
            "opportunity_id": opportunity_id,
            "notes": notes,
            "updated_at": timestamp,
            "character_count": len(notes)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update notes for opportunity {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{opportunity_id}/website-url", summary="Set or clear the website URL for an opportunity")
async def update_website_url(opportunity_id: str, body: WebsiteUrlUpdate):
    """
    Update (or clear) the website_url for an opportunity.

    Stores the URL in analysis_discovery.website_url with url_source='manual'.
    Also caches it in ein_intelligence so batch URL discovery can see it.

    Request body:
    {
        "url": "https://example.org"   # or null/empty to clear
    }
    """
    try:
        url = (body.url or "").strip()

        conn = database_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ein, organization_name, analysis_discovery FROM opportunities WHERE id = ?",
            (opportunity_id,)
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")

        ein, org_name, ad_raw = row[0], row[1], row[2]
        analysis_discovery = json.loads(ad_raw) if ad_raw else {}

        # Update URL fields
        analysis_discovery["website_url"] = url
        analysis_discovery["url_source"] = "manual" if url else None

        timestamp = datetime.now().isoformat()
        cursor.execute(
            "UPDATE opportunities SET analysis_discovery = ?, updated_at = ? WHERE id = ?",
            (json.dumps(analysis_discovery), timestamp, opportunity_id)
        )
        conn.commit()
        conn.close()

        logger.info(f"Updated website_url for {opportunity_id} (EIN: {ein}): {url!r}")

        return {
            "success": True,
            "opportunity_id": opportunity_id,
            "website_url": url or None,
            "url_source": "manual" if url else None,
            "updated_at": timestamp,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update website_url for {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")



# ---------------------------------------------------------------------------
# Batch Web Research Endpoint (Haiku web scraper fan-out)
# ---------------------------------------------------------------------------

@router.post("/batch-web-research", summary="Run Scrapy web intelligence on multiple opportunities in batch (max 50)")
async def batch_web_research(body: BatchWebResearchRequest):
    """
    Batch Haiku web intelligence for multiple opportunities.

    For each EIN: checks EIN intelligence cache, then runs Tool 25 (Haiku agent).
    Concurrency: 3 simultaneous web scrapes.
    Cost: ~$0.003-0.01 per org (Claude Haiku), cached per EIN.

    Returns { total, researched, cached, errors, estimated_cost_usd }
    """
    if not body.opportunity_ids:
        raise HTTPException(status_code=400, detail="opportunity_ids must not be empty")

    if len(body.opportunity_ids) > 50:
        raise HTTPException(status_code=400, detail="Batch size cannot exceed 50 opportunities")

    results = []
    semaphore = asyncio.Semaphore(3)

    async def research_one(opp_id: str):
        async with semaphore:
            try:
                conn = database_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ein, organization_name FROM opportunities WHERE id = ?", (opp_id,)
                )
                row = cursor.fetchone()
                conn.close()

                if not row or not row[0]:
                    results.append({"opportunity_id": opp_id, "status": "skipped", "reason": "no EIN"})
                    return

                ein, org_name = row[0], row[1]

                # EIN intelligence cache check
                if not body.force_refresh:
                    cached = database_manager.get_ein_intelligence(ein)
                    if cached and cached.get("web_data") and cached.get("web_data_fetched_at"):
                        try:
                            fetched_dt = datetime.fromisoformat(cached["web_data_fetched_at"])
                            age_days = (datetime.now() - fetched_dt).days
                            if age_days < _WEB_DATA_TTL_DAYS:
                                logger.info(f"Cache hit: web_data for EIN {ein} (batch)")
                                # Write back to this opportunity's analysis_discovery
                                web_data = cached["web_data"]
                                conn2 = database_manager.get_connection()
                                cur2 = conn2.cursor()
                                cur2.execute(
                                    "SELECT analysis_discovery, website_url FROM opportunities WHERE id = ?", (opp_id,)
                                )
                                ad_row = cur2.fetchone()
                                if ad_row and ad_row[0]:
                                    ad = json.loads(ad_row[0]) if isinstance(ad_row[0], str) else ad_row[0]
                                    ad["web_data"] = web_data
                                    ad["web_search_complete"] = True
                                    found_url = web_data.get("website") if isinstance(web_data, dict) else None
                                    existing_url = ad_row[1]
                                    if found_url and not existing_url:
                                        cur2.execute(
                                            "UPDATE opportunities SET analysis_discovery = ?, website_url = ?, url_source = ?, url_discovered_at = ?, updated_at = ? WHERE id = ?",
                                            (json.dumps(ad), found_url, "web_research", datetime.now().isoformat(), datetime.now().isoformat(), opp_id),
                                        )
                                    else:
                                        cur2.execute(
                                            "UPDATE opportunities SET analysis_discovery = ?, updated_at = ? WHERE id = ?",
                                            (json.dumps(ad), datetime.now().isoformat(), opp_id),
                                        )
                                    conn2.commit()
                                conn2.close()
                                results.append({"opportunity_id": opp_id, "ein": ein, "status": "cached"})
                                return
                        except Exception:
                            pass

                # Run Tool 25
                from tools.web_intelligence_tool.app.web_intelligence_tool import (
                    WebIntelligenceTool, WebIntelligenceRequest, UseCase
                )
                tool = WebIntelligenceTool()
                request = WebIntelligenceRequest(
                    ein=ein,
                    organization_name=org_name,
                    use_case=UseCase.PROFILE_BUILDER,
                )
                result = await tool.execute(request)

                if result.success and result.intelligence_data:
                    intelligence = result.intelligence_data
                    from tools.shared_schemas.grant_funder_intelligence import GrantFunderIntelligence as GFI

                    if isinstance(intelligence, GFI):
                        contact_obj = None
                        if intelligence.contact_information:
                            contact_obj = {"email": None, "phone": None, "address": intelligence.contact_information}
                        web_data = {
                            "website": intelligence.source_url,
                            "website_verified": intelligence.confidence_score > 0.6,
                            "mission": intelligence.mission_statement,
                            "leadership": [
                                {"name": m, "title": "", "email": None, "confidence": "medium"}
                                for m in (intelligence.board_members or [])
                            ],
                            "leadership_cross_validated": False,
                            "contact": contact_obj,
                            "social_media": {},
                            "programs": [
                                {"name": "", "description": d, "target_population": intelligence.population_focus}
                                for d in (intelligence.program_descriptions or [])
                            ],
                            "key_facts": intelligence.funding_priorities or [],
                            "grant_application_url": None,
                            "recent_news": [],
                            "data_quality_score": intelligence.confidence_score,
                            "pages_scraped": result.pages_scraped,
                            "execution_time": result.execution_time_seconds,
                            "ai_interpreted": True,
                            "accepts_applications": intelligence.accepts_applications,
                            "application_deadlines": intelligence.application_deadlines,
                            "application_process": intelligence.application_process,
                            "required_documents": intelligence.required_documents,
                            "geographic_limitations": intelligence.geographic_limitations,
                            "grant_size_range": intelligence.grant_size_range,
                            "grant_funder_intelligence": intelligence.to_dict(),
                        }
                    else:
                        web_data = {"ai_interpreted": False, "data_quality_score": 0.0}

                    # Update opportunity in DB
                    conn2 = database_manager.get_connection()
                    cur2 = conn2.cursor()
                    cur2.execute(
                        "SELECT analysis_discovery, website_url FROM opportunities WHERE id = ?", (opp_id,)
                    )
                    ad_row = cur2.fetchone()
                    if ad_row and ad_row[0]:
                        ad = json.loads(ad_row[0]) if isinstance(ad_row[0], str) else ad_row[0]
                        ad["web_data"] = web_data
                        ad["web_search_complete"] = True
                        # Back-fill website_url column if currently empty and web research found a URL
                        found_url = web_data.get("website") if isinstance(web_data, dict) else None
                        existing_url = ad_row[1]
                        if found_url and not existing_url:
                            cur2.execute(
                                "UPDATE opportunities SET analysis_discovery = ?, website_url = ?, url_source = ?, url_discovered_at = ?, updated_at = ? WHERE id = ?",
                                (json.dumps(ad), found_url, "web_research", datetime.now().isoformat(), datetime.now().isoformat(), opp_id),
                            )
                        else:
                            cur2.execute(
                                "UPDATE opportunities SET analysis_discovery = ?, updated_at = ? WHERE id = ?",
                                (json.dumps(ad), datetime.now().isoformat(), opp_id),
                            )
                        conn2.commit()
                    conn2.close()

                    # Cache in EIN intelligence
                    try:
                        database_manager.upsert_ein_intelligence(
                            ein=ein,
                            org_name=org_name,
                            web_data=web_data,
                            web_data_fetched_at=datetime.now().isoformat(),
                            web_data_source="claude_interpreted",
                        )
                    except Exception as ce:
                        logger.warning(f"Failed to cache web_data for EIN {ein}: {ce}")

                    results.append({
                        "opportunity_id": opp_id,
                        "ein": ein,
                        "status": "ok",
                        "data_quality_score": web_data.get("data_quality_score"),
                    })
                else:
                    error_msg = "; ".join(result.errors) if result.errors else "Unknown error"
                    results.append({"opportunity_id": opp_id, "ein": ein, "status": "error", "error": error_msg})

            except Exception as e:
                logger.warning(f"Batch web research failed for {opp_id}: {e}")
                results.append({"opportunity_id": opp_id, "status": "error", "error": str(e)})

    await asyncio.gather(*[research_one(opp_id) for opp_id in body.opportunity_ids])

    researched = [r for r in results if r.get("status") == "ok"]
    cached_list = [r for r in results if r.get("status") == "cached"]
    cost_estimate = len(researched) * 0.008  # ~$0.003-0.01 per Haiku call

    return {
        "success": True,
        "total": len(body.opportunity_ids),
        "researched": len(researched),
        "cached": len(cached_list),
        "errors": len([r for r in results if r.get("status") == "error"]),
        "estimated_cost_usd": round(cost_estimate, 4),
    }


# ---------------------------------------------------------------------------
# Batch Screen Endpoint (Tool 1 fast-mode fan-out)
# ---------------------------------------------------------------------------

class BatchScreenRequest(BaseModel):
    profile_id: str
    opportunity_ids: List[str]
    mode: str = "fast"         # "fast" | "thorough"
    threshold: float = 0.50    # Min score to keep after screening


async def _run_batch_screen(job_id: str, body: BatchScreenRequest) -> None:
    """Background task: run Tool 1 on each opportunity, update DB and job state."""
    job = _batch_jobs[job_id]
    semaphore = asyncio.Semaphore(10)

    # Load profile for OrganizationProfile context
    try:
        profile_conn = database_manager.get_connection()
        pcursor = profile_conn.cursor()
        pcursor.execute("SELECT * FROM profiles WHERE id = ?", (body.profile_id,))
        profile_row = pcursor.fetchone()
        profile_conn.close()
        if not profile_row:
            job["status"] = "failed"
            job["error"] = f"Profile {body.profile_id} not found"
            return
        profile_dict = dict(profile_row)
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        return

    # Import Tool 1
    try:
        from tools.opportunity_screening_tool.app.screening_tool import OpportunityScreeningTool
        from tools.opportunity_screening_tool.app.screening_models import (
            ScreeningInput, ScreeningMode, Opportunity as ScreeningOpportunity, OrganizationProfile
        )
        tool = OpportunityScreeningTool()
    except Exception as e:
        logger.error(f"Batch screen: Failed to import Tool 1: {e}")
        job["status"] = "failed"
        job["error"] = f"Tool 1 import error: {e}"
        return

    # Build OrganizationProfile from DB row
    try:
        focus_areas = json.loads(profile_dict.get("focus_areas") or "[]") or []
        program_areas = json.loads(profile_dict.get("program_areas") or "[]") or []
        ntee_codes = json.loads(profile_dict.get("ntee_codes") or "[]") or []
        service_areas = json.loads(profile_dict.get("service_areas") or "[]") or []
        org_profile = OrganizationProfile(
            ein=profile_dict.get("ein") or "",
            name=profile_dict.get("name") or "Unknown",
            mission=profile_dict.get("mission_statement") or "",
            ntee_codes=ntee_codes,
            geographic_focus=service_areas or [profile_dict.get("location") or ""],
            program_areas=program_areas or focus_areas,
            annual_revenue=profile_dict.get("annual_revenue"),
        )
    except Exception as e:
        job["status"] = "failed"
        job["error"] = f"Profile parse error: {e}"
        return

    mode_enum = ScreeningMode.FAST if body.mode == "fast" else ScreeningMode.THOROUGH
    results = []
    processed = 0

    async def screen_one(opp_id: str):
        nonlocal processed
        async with semaphore:
            try:
                opp_conn = database_manager.get_connection()
                ocursor = opp_conn.cursor()
                ocursor.execute(
                    "SELECT id, organization_name, ein, analysis_discovery FROM opportunities WHERE id = ?",
                    (opp_id,)
                )
                row = ocursor.fetchone()
                opp_conn.close()
                if not row:
                    return

                opp_id_db, org_name, ein, ad_raw = row[0], row[1], row[2], row[3]
                ad = json.loads(ad_raw) if isinstance(ad_raw, str) and ad_raw else {}
                data_990 = ad.get("990_data") or {}
                ntee = ad.get("ntee_code") or ""
                bsig = ad.get("behavioral_signals") or {}

                # Build description — include behavioral grant history when available
                desc_parts = [
                    f"Organization: {org_name}.",
                    f"NTEE: {ntee}." if ntee else "",
                    f"Revenue: ${data_990.get('revenue', 0):,.0f}." if data_990.get('revenue') else "",
                    f"Assets: ${data_990.get('assets', 0):,.0f}." if data_990.get('assets') else "",
                    (
                        f"Location: {ad.get('location', {}).get('city', '')}, "
                        f"{ad.get('location', {}).get('state', '')}."
                    ),
                ]
                if bsig:
                    desc_parts += [
                        f"IRS grant history: {bsig.get('grant_count', 0)} grants avg "
                        f"${bsig.get('avg_grant', 0):,.0f} (last active {bsig.get('last_active', 'N/A')}).",
                        f"Total grants paid: ${bsig.get('grants_paid', 0):,.0f}.",
                    ]
                    if bsig.get("grant_purposes_sample"):
                        desc_parts.append(
                            f"Sample grant purposes: {bsig['grant_purposes_sample'][:200]}."
                        )

                screening_opp = ScreeningOpportunity(
                    opportunity_id=opp_id_db,
                    title=org_name or "Unknown Organization",
                    funder=org_name or "Unknown",
                    funder_type="foundation" if ad.get("foundation_code") else "nonprofit",
                    description=" ".join(p for p in desc_parts if p),
                    geographic_restrictions=[],  # Don't assume local-only restriction; most nonprofits give broadly
                )

                # Inject W/9 funder intelligence if available in ein_intelligence
                if ein:
                    try:
                        from tools.shared_schemas.grant_funder_intelligence import build_from_ein_intelligence
                        intel = database_manager.get_ein_intelligence(ein)
                        if intel:
                            funder_intel = build_from_ein_intelligence(
                                web_data=intel.get("web_data"),
                                pdf_analyses=intel.get("pdf_analyses"),
                                ein=ein,
                            )
                            if funder_intel:
                                screening_opp.funder_intelligence = funder_intel
                                logger.debug(f"Injected funder intelligence for {ein} (source={funder_intel.source.value})")
                                # Backfill analysis_discovery['web_data']['leadership'] from
                                # funder_intel.people so the Officers tab shows data without
                                # requiring manual Steps 2/3 per opportunity.
                                if funder_intel.people and not ad.get("web_data", {}).get("leadership"):
                                    ad.setdefault("web_data", {})["leadership"] = [
                                        {
                                            "name": p["name"],
                                            "title": p.get("title", ""),
                                            "email": p.get("email", ""),
                                            "source": p.get("source", ""),
                                        }
                                        for p in funder_intel.people
                                    ]
                                    bf_conn = database_manager.get_connection()
                                    bf_cur = bf_conn.cursor()
                                    bf_cur.execute(
                                        "UPDATE opportunities SET analysis_discovery = ?, updated_at = ? WHERE id = ?",
                                        (json.dumps(ad), datetime.now().isoformat(), opp_id_db),
                                    )
                                    bf_conn.commit()
                                    bf_conn.close()
                    except Exception as fi_err:
                        logger.debug(f"Funder intelligence injection skipped for {ein}: {fi_err}")

                screening_input = ScreeningInput(
                    opportunities=[screening_opp],
                    organization_profile=org_profile,
                    screening_mode=mode_enum,
                    minimum_threshold=0.0,   # Don't filter here; we filter client-side
                    max_recommendations=1,
                )

                result = await tool.execute(screening_input=screening_input)

                if result.is_success and result.data and result.data.opportunity_scores:
                    score_obj = result.data.opportunity_scores[0]
                    tool1_result = {
                        "overall_score": score_obj.overall_score,
                        "strategic_fit_score": score_obj.strategic_fit_score,
                        "eligibility_score": score_obj.eligibility_score,
                        "timing_score": score_obj.timing_score,
                        "confidence_level": score_obj.confidence_level,
                        "one_sentence_summary": score_obj.one_sentence_summary,
                        "key_strengths": score_obj.key_strengths,
                        "key_concerns": score_obj.key_concerns,
                        "mode": body.mode,
                        "scored_at": datetime.now().isoformat(),
                    }
                    # Write back to analysis_discovery
                    upd_conn = database_manager.get_connection()
                    ucursor = upd_conn.cursor()
                    ucursor.execute(
                        "SELECT analysis_discovery FROM opportunities WHERE id = ?", (opp_id_db,)
                    )
                    upd_row = ucursor.fetchone()
                    if upd_row:
                        raw = upd_row[0]
                        upd_ad = json.loads(raw) if isinstance(raw, str) and raw else {}
                        upd_ad["tool1_score"] = tool1_result               # keep as "latest" for backward compat
                        upd_ad[f"tool1_score_{body.mode}"] = tool1_result  # "tool1_score_fast" or "tool1_score_thorough"
                        ucursor.execute(
                            "UPDATE opportunities SET analysis_discovery = ?, updated_at = ? WHERE id = ?",
                            (json.dumps(upd_ad), datetime.now().isoformat(), opp_id_db),
                        )
                        upd_conn.commit()
                    upd_conn.close()

                    results.append({
                        "opportunity_id": opp_id_db,
                        "organization_name": org_name,
                        "tool1_score": score_obj.overall_score,
                        "summary": score_obj.one_sentence_summary,
                    })
            except Exception as e:
                logger.warning(f"Batch screen error for {opp_id}: {e}")
            finally:
                processed += 1
                job["progress"] = processed
                job["processed"] = processed

    await asyncio.gather(*[screen_one(opp_id) for opp_id in body.opportunity_ids])

    job["status"] = "complete"
    job["results"] = results
    job["above_threshold"] = [r for r in results if r["tool1_score"] >= body.threshold]
    cost_per_opp = 0.001 if body.mode == "fast" else 0.01
    job["estimated_cost"] = len(body.opportunity_ids) * cost_per_opp

    # ── Auto-trigger: populate network graph from cached ein_intelligence ──
    # After screening completes, ingest any available funder leadership data
    # into network_memberships so relationship analysis is immediately available.
    # Cost: $0.00 — pure DB reads.
    try:
        from src.network.graph_builder import NetworkGraphBuilder
        db_path = database_manager.db_path
        builder = NetworkGraphBuilder(db_path)
        graph_stats = builder.ingest_all_funders_from_cache(body.profile_id)
        job["network_graph_populated"] = True
        job["network_stats"] = {
            "people_added": graph_stats.get("people_added", 0),
            "graph_total_size": graph_stats.get("graph_total_size", 0),
            "funders_with_data": graph_stats.get("funders_with_data", 0),
            "funders_without_data": len(graph_stats.get("funders_without_data", [])),
        }
        logger.info(
            f"[batch-screen] Auto-populated network graph for profile {body.profile_id}: "
            f"{graph_stats.get('people_added', 0)} people added, "
            f"graph size={graph_stats.get('graph_total_size', 0)}"
        )
    except Exception as graph_err:
        logger.warning(f"[batch-screen] Network graph auto-populate failed (non-fatal): {graph_err}")
        job["network_graph_populated"] = False


@router.post("/batch-screen", summary="Screen up to 500 opportunities using Claude Haiku (async background job)")
async def start_batch_screen(body: BatchScreenRequest, background_tasks: BackgroundTasks):
    """
    Start a background batch screening job using Tool 1 (fast or thorough).

    Returns a job_id. Poll GET /batch-screen/{job_id} for status and results.
    Cost estimate: fast=$0.001/opp, thorough=$0.01/opp.
    """
    if not body.opportunity_ids:
        raise HTTPException(status_code=400, detail="opportunity_ids must not be empty")

    if len(body.opportunity_ids) > 500:
        raise HTTPException(status_code=400, detail="Batch size cannot exceed 500 opportunities")

    cost_per_opp = 0.001 if body.mode == "fast" else 0.01
    estimated_cost = len(body.opportunity_ids) * cost_per_opp

    job_id = str(uuid.uuid4())[:8]
    _batch_jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "processed": 0,
        "total": len(body.opportunity_ids),
        "mode": body.mode,
        "threshold": body.threshold,
        "estimated_cost": estimated_cost,
        "results": [],
        "above_threshold": [],
        "error": None,
    }

    background_tasks.add_task(_run_batch_screen, job_id, body)

    return {
        "job_id": job_id,
        "total": len(body.opportunity_ids),
        "mode": body.mode,
        "estimated_cost": estimated_cost,
        "status_url": f"/api/v2/opportunities/batch-screen/{job_id}",
    }


@router.get("/batch-screen/{job_id}")
async def get_batch_screen_status(job_id: str):
    """Poll batch screening job status and results."""
    job = _batch_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Batch job {job_id} not found")
    return job


@router.post("/{opportunity_id}/screen")
async def screen_single_opportunity(opportunity_id: str, mode: str = "fast"):
    """
    Screen a single opportunity with Tool 1 (fast or thorough mode).

    Reuses the same helpers as _run_batch_screen:
      - Loads opportunity + profile from DB
      - Injects funder_intelligence from ein_intelligence cache
      - Runs OpportunityScreeningTool
      - Persists tool1_score in analysis_discovery

    Returns:
      { tool1_score, category_level, overall_score, organization_name }
    """
    try:
        # 1. Load opportunity
        conn = database_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,))
        row = cursor.fetchone()
        col_names = [col[0] for col in cursor.description] if cursor.description else []
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")

        opp_dict = dict(zip(col_names, row))
        opp_id_db = opp_dict["id"]
        org_name = opp_dict["organization_name"]
        ein = opp_dict.get("ein") or ""
        profile_id = opp_dict.get("profile_id") or ""
        ad_raw = opp_dict.get("analysis_discovery")
        ad = json.loads(ad_raw) if isinstance(ad_raw, str) and ad_raw else {}

        # 2. Load profile
        if not profile_id:
            raise HTTPException(status_code=400, detail="Opportunity has no profile_id")

        p_conn = database_manager.get_connection()
        p_cursor = p_conn.cursor()
        p_cursor.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
        p_row = p_cursor.fetchone()
        p_conn.close()

        if not p_row:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        profile_dict = dict(p_row)

        # 3. Import Tool 1
        try:
            from tools.opportunity_screening_tool.app.screening_tool import OpportunityScreeningTool
            from tools.opportunity_screening_tool.app.screening_models import (
                ScreeningInput, ScreeningMode, Opportunity as ScreeningOpportunity, OrganizationProfile
            )
            tool = OpportunityScreeningTool()
        except Exception as e:
            logger.error(f"Tool 1 import error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

        # 4. Build OrganizationProfile
        focus_areas = json.loads(profile_dict.get("focus_areas") or "[]") or []
        program_areas = json.loads(profile_dict.get("program_areas") or "[]") or []
        ntee_codes = json.loads(profile_dict.get("ntee_codes") or "[]") or []
        service_areas = json.loads(profile_dict.get("service_areas") or "[]") or []
        org_profile = OrganizationProfile(
            ein=profile_dict.get("ein") or "",
            name=profile_dict.get("name") or "Unknown",
            mission=profile_dict.get("mission_statement") or "",
            ntee_codes=ntee_codes,
            geographic_focus=service_areas or [profile_dict.get("location") or ""],
            program_areas=program_areas or focus_areas,
            annual_revenue=profile_dict.get("annual_revenue"),
        )

        # 5. Build ScreeningOpportunity
        data_990 = ad.get("990_data") or {}
        ntee = ad.get("ntee_code") or ""
        screening_opp = ScreeningOpportunity(
            opportunity_id=opp_id_db,
            title=org_name or "Unknown Organization",
            funder=org_name or "Unknown",
            funder_type="foundation" if ad.get("foundation_code") else "nonprofit",
            description=(
                f"Organization: {org_name}. "
                f"NTEE: {ntee}. "
                f"Revenue: ${data_990.get('revenue', 0):,.0f}. "
                f"Assets: ${data_990.get('assets', 0):,.0f}. "
                f"Location: {ad.get('location', {}).get('city', '')}, "
                f"{ad.get('location', {}).get('state', '')}."
            ),
            geographic_restrictions=[],
        )

        # 6. Inject funder intelligence if available
        if ein:
            try:
                from tools.shared_schemas.grant_funder_intelligence import build_from_ein_intelligence
                intel = database_manager.get_ein_intelligence(ein)
                if intel:
                    funder_intel = build_from_ein_intelligence(
                        web_data=intel.get("web_data"),
                        pdf_analyses=intel.get("pdf_analyses"),
                        ein=ein,
                    )
                    if funder_intel:
                        screening_opp.funder_intelligence = funder_intel
            except Exception as fi_err:
                logger.debug(f"Funder intelligence skipped for {ein}: {fi_err}")

        # 7. Run screening
        mode_enum = ScreeningMode.FAST if mode == "fast" else ScreeningMode.THOROUGH
        screening_input = ScreeningInput(
            opportunities=[screening_opp],
            organization_profile=org_profile,
            screening_mode=mode_enum,
            minimum_threshold=0.0,
            max_recommendations=1,
        )

        result = await tool.execute(screening_input=screening_input)

        if not (result.is_success and result.data and result.data.opportunity_scores):
            raise HTTPException(status_code=500, detail="Screening returned no results")

        score_obj = result.data.opportunity_scores[0]
        tool1_result = {
            "overall_score": score_obj.overall_score,
            "strategic_fit_score": score_obj.strategic_fit_score,
            "eligibility_score": score_obj.eligibility_score,
            "timing_score": score_obj.timing_score,
            "confidence_level": score_obj.confidence_level,
            "one_sentence_summary": score_obj.one_sentence_summary,
            "key_strengths": score_obj.key_strengths,
            "key_concerns": score_obj.key_concerns,
            "mode": mode,
            "scored_at": datetime.now().isoformat(),
        }

        # 8. Persist to DB
        upd_conn = database_manager.get_connection()
        ucursor = upd_conn.cursor()
        ucursor.execute("SELECT analysis_discovery FROM opportunities WHERE id = ?", (opp_id_db,))
        upd_row = ucursor.fetchone()
        if upd_row:
            raw = upd_row[0]
            upd_ad = json.loads(raw) if isinstance(raw, str) and raw else {}
            upd_ad["tool1_score"] = tool1_result
            upd_ad[f"tool1_score_{mode}"] = tool1_result
            ucursor.execute(
                "UPDATE opportunities SET analysis_discovery = ?, updated_at = ? WHERE id = ?",
                (json.dumps(upd_ad), datetime.now().isoformat(), opp_id_db),
            )
            upd_conn.commit()
        upd_conn.close()

        logger.info(f"Single screen ({mode}) for {opportunity_id}: {score_obj.overall_score:.2f}")

        return {
            "success": True,
            "opportunity_id": opportunity_id,
            "organization_name": org_name,
            "mode": mode,
            "tool1_score": tool1_result,
            "overall_score": score_obj.overall_score,
            "category_level": ad.get("category_level"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Single screen failed for {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{opportunity_id}/run-connections")
async def run_opportunity_connections(opportunity_id: str):
    """
    Six Degrees connection analysis for a specific Intelligence-stage opportunity.
    Reads seeker people from profiles.board_members and funder people from ein_intelligence.
    Stores result in analysis_discovery['connection_analysis'].
    Called automatically after Essentials AI completes.
    """
    from src.web.routers.profiles_intelligence import _analyze_opportunity_connections

    # ── Fetch opportunity ─────────────────────────────────────────────────
    conn = database_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, profile_id, organization_name, ein, analysis_discovery FROM opportunities WHERE id = ?",
        (opportunity_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")

    opp_id, profile_id, org_name, funder_ein, ad_raw = row[0], row[1], row[2], row[3], row[4]

    if not funder_ein:
        raise HTTPException(
            status_code=400,
            detail="Opportunity does not have an EIN — cannot run Six Degrees analysis.",
        )

    if not profile_id:
        raise HTTPException(
            status_code=400,
            detail="Opportunity is not linked to a profile — cannot run Six Degrees analysis.",
        )

    # ── Populate network graph (side-effect, no AI calls) ────────────────
    try:
        from src.network.graph_builder import NetworkGraphBuilder
        from src.config.database_config import get_catalynx_db
        _gb = NetworkGraphBuilder(get_catalynx_db())

        # Ingest seeker board members
        _gc = database_manager.get_connection()
        _gcur = _gc.cursor()
        _gcur.execute("SELECT board_members, name FROM profiles WHERE id = ?", (profile_id,))
        _profile_row = _gcur.fetchone()
        _gc.close()

        if _profile_row and _profile_row[0]:
            try:
                _board = json.loads(_profile_row[0]) if isinstance(_profile_row[0], str) else _profile_row[0]
                _gb.ingest_profile_board_members(str(profile_id), _board, _profile_row[1] or "Seeker Organization")
            except Exception as _e:
                logger.debug(f"[RunConnections] Board member ingest skipped: {_e}")

        # Ingest funder people from ein_intelligence
        _ei = database_manager.get_ein_intelligence(str(funder_ein))
        if _ei:
            _gb.ingest_funder_ein(str(funder_ein), org_name or "", _ei)

    except Exception as _graph_err:
        logger.debug(f"[RunConnections] Graph population skipped: {_graph_err}")

    # ── Run connection analysis ───────────────────────────────────────────
    connection_result = await _analyze_opportunity_connections(
        profile_id=str(profile_id),
        funder_ein=str(funder_ein),
        funder_name=org_name or "",
    )

    # ── Persist result in analysis_discovery ─────────────────────────────
    try:
        ad = json.loads(ad_raw) if isinstance(ad_raw, str) and ad_raw else {}
        ad["connection_analysis"] = connection_result

        conn = database_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE opportunities SET analysis_discovery = ?, updated_at = ? WHERE id = ?",
            (json.dumps(ad), datetime.now(timezone.utc).isoformat(), opp_id),
        )
        conn.commit()
        conn.close()
        logger.info(f"[RunConnections] Saved connection_analysis for opportunity {opp_id}")
    except Exception as e:
        logger.warning(f"[RunConnections] Failed to persist connection_analysis for {opp_id}: {e}")

    return {"success": True, "connection_analysis": connection_result}


@router.post("/{opportunity_id}/run-networking")
async def run_opportunity_networking(opportunity_id: str):
    """
    Networking tier: BFS graph paths + Sonnet narration. $4.00.
    Discovers 1st/2nd/3rd degree connections between seeker board and funder leadership
    using the persistent network_memberships graph.
    """
    from src.web.routers.intelligence import _run_networking_analysis

    try:
        result = await _run_networking_analysis(opportunity_id)
        return result
    except ValueError as e:
        logger.warning(f"[RunNetworking] Not found for {opportunity_id}: {e}")
        raise HTTPException(status_code=404, detail="Resource not found")
    except Exception as e:
        logger.error(f"[RunNetworking] Failed for {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """Health check for opportunities API."""
    return {
        "status": "healthy",
        "version": "1.1",
        "endpoints": [
            "GET /api/v2/opportunities/{id}/details",
            "POST /api/v2/opportunities/{id}/research",
            "POST /api/v2/opportunities/{id}/screen",
            "POST /api/v2/opportunities/{id}/run-connections",
            "POST /api/v2/opportunities/{id}/run-networking",
            "POST /api/v2/opportunities/{id}/promote",
            "POST /api/v2/opportunities/{id}/demote",
            "PATCH /api/v2/opportunities/{id}/notes",
            "POST /api/v2/opportunities/batch-screen",
            "GET /api/v2/opportunities/batch-screen/{job_id}",
            # 990 filings live in opportunities_990.py:
            "GET /api/v2/opportunities/{id}/990-filings",
            "GET /api/v2/opportunities/{id}/990-extraction",
            "POST /api/v2/opportunities/{id}/analyze-990-pdf",
            "POST /api/v2/opportunities/batch-analyze-990-pdfs",
        ]
    }
