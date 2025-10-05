"""
Opportunities API Endpoints - SCREENING Stage Support

Endpoints for viewing opportunity details, running web research, and promoting to INTELLIGENCE stage.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import logging
import sqlite3
import json
from datetime import datetime

from src.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/opportunities", tags=["opportunities"])

# Initialize database manager
database_manager = DatabaseManager("data/catalynx.db")


@router.get("/{opportunity_id}/details")
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
            "web_search_complete": False,  # Will be updated by research endpoint
            "web_data": None,  # Will be populated by research endpoint
            "current_stage": opportunity.current_stage,
            "discovery_date": discovery_date_iso,
            "notes": opportunity.notes,
            "tags": opportunity.tags or []
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get opportunity details for {opportunity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{opportunity_id}/research")
async def research_opportunity(opportunity_id: str, profile_id: Optional[str] = None):
    """
    Run on-demand Web Intelligence (Scrapy) for an opportunity.

    This endpoint triggers Tool 25 (Web Intelligence Tool) to gather:
    - Website URL and verification
    - Leadership team information
    - Recent news and updates
    - Contact information
    - Social media presence

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

        # Integrate Tool 25 Web Intelligence
        try:
            import sys
            from pathlib import Path

            # Add tools directory to path for imports
            tools_dir = Path(__file__).parent.parent.parent / 'tools' / 'web-intelligence-tool'
            sys.path.insert(0, str(tools_dir))

            logger.info(f"Tool 25 path: {tools_dir}")
            logger.info(f"Tool 25 exists: {tools_dir.exists()}")

            from app.web_intelligence_tool import WebIntelligenceTool, WebIntelligenceRequest, UseCase

            # Create Tool 25 instance and request
            tool = WebIntelligenceTool()
            request = WebIntelligenceRequest(
                ein=ein,
                organization_name=opportunity.organization_name,
                use_case=UseCase.OPPORTUNITY_RESEARCH  # Use Case 2: Opportunity Research
            )

            logger.info(f"Executing Tool 25 for EIN {ein}")

            # Execute Tool 25 web scraping
            result = await tool.execute(request)

            logger.info(f"Tool 25 result: success={result.success}, errors={result.errors if hasattr(result, 'errors') else 'N/A'}")

            if result.success and result.intelligence_data:
                # Convert OrganizationIntelligence to dict for storage
                intelligence = result.intelligence_data

                web_data = {
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
                        {
                            "name": program.name,
                            "description": program.description,
                            "target_population": program.target_population
                        }
                        for program in intelligence.programs
                    ],
                    "grant_application_url": None,  # Would need custom detection logic
                    "recent_news": [],  # Would need news extraction spider
                    "data_quality_score": result.data_quality_score,
                    "pages_scraped": result.pages_scraped,
                    "execution_time": result.execution_time_seconds
                }

                # Update opportunity in database with web data
                conn = database_manager.get_connection()
                cursor = conn.cursor()

                # Get current opportunity data
                cursor.execute("SELECT analysis_discovery FROM opportunities WHERE id = ?", (opportunity_id,))
                row = cursor.fetchone()

                if row and row[0]:
                    import json
                    analysis_discovery = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    analysis_discovery['web_data'] = web_data
                    analysis_discovery['web_search_complete'] = True

                    # Update database
                    cursor.execute(
                        "UPDATE opportunities SET analysis_discovery = ?, updated_at = ? WHERE id = ?",
                        (json.dumps(analysis_discovery), datetime.now().isoformat(), opportunity_id)
                    )
                    conn.commit()

                conn.close()

                logger.info(f"Web research completed successfully for {opportunity_id} - scraped {result.pages_scraped} pages in {result.execution_time_seconds:.2f}s")

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
                raise HTTPException(status_code=500, detail=f"Web intelligence tool failed: {error_msg}")

        except ImportError as e:
            logger.error(f"Failed to import Tool 25: {e}")
            raise HTTPException(status_code=500, detail=f"Tool 25 import error: {str(e)}")
        except Exception as e:
            logger.error(f"Tool 25 execution error for {opportunity_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Web research failed: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to research opportunity {opportunity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        logger.error(f"Web research failed for {opportunity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{opportunity_id}/promote")
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
        logger.error(f"Failed to promote opportunity {opportunity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        current_category = opportunity_dict.get('category_level', 'low_priority')
        current_stage = opportunity_dict.get('current_stage', 'discovery')

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

        # Update database
        timestamp = datetime.now().isoformat()
        cursor.execute("""
            UPDATE opportunities
            SET category_level = ?,
                current_stage = ?,
                updated_at = ?
            WHERE id = ?
        """, (new_category, new_stage, timestamp, opportunity_id))

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
        logger.error(f"Failed to promote opportunity {opportunity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        current_category = opportunity_dict.get('category_level', 'low_priority')
        current_stage = opportunity_dict.get('current_stage', 'discovery')

        # Cannot demote if already moved past discovery
        if current_stage not in ['discovery', 'screening']:
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

        # Update database
        timestamp = datetime.now().isoformat()
        cursor.execute("""
            UPDATE opportunities
            SET category_level = ?,
                updated_at = ?
            WHERE id = ?
        """, (new_category, timestamp, opportunity_id))

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
        logger.error(f"Failed to demote opportunity {opportunity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        logger.error(f"Failed to update notes for opportunity {opportunity_id}: {e}")
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
            "POST /api/v2/opportunities/{id}/promote",
            "POST /api/v2/opportunities/{id}/demote",
            "PATCH /api/v2/opportunities/{id}/notes"
        ]
    }
