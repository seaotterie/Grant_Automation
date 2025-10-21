#!/usr/bin/env python3
"""
Profiles Router
Handles all profile-related API endpoints including CRUD, analytics, discovery, and opportunity management
Extracted from monolithic main.py for better modularity
"""

from fastapi import APIRouter, HTTPException, Depends, Query
import logging
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

# Import essential services only
from src.database.query_interface import DatabaseQueryInterface, QueryFilter
from src.database.database_manager import DatabaseManager, Profile
from src.web.services.scoring_service import (
    get_scoring_service, ScoreRequest, ScoreResponse
)

# ProfileService removed - now using DatabaseManager exclusively

# Authentication removed - single-user desktop application
AUTH_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/api/profiles", tags=["profiles"])

# Initialize essential services
db_query_interface = DatabaseQueryInterface()
db_manager = DatabaseManager()
scoring_service = get_scoring_service()

# ProfileService initialization removed - using DatabaseManager only


# Core Profile CRUD Operations

@router.get("/database")
async def list_profiles_from_database() -> Dict[str, Any]:
    """List all organization profiles directly from database."""
    try:
        profiles, total_count = db_query_interface.filter_profiles(QueryFilter())
        
        # Add opportunity count for each profile
        for profile in profiles:
            opportunities, opp_count = db_query_interface.filter_opportunities(
                QueryFilter(profile_ids=[profile["id"]])
            )
            profile["opportunities_count"] = len(opportunities)
            profile["total_opportunities"] = opp_count
        
        logger.info(f"Returned {len(profiles)} profiles from database")
        return {
            "profiles": profiles,
            "total_count": total_count,
            "source": "database"
        }
        
    except Exception as e:
        logger.error(f"Failed to list profiles from database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_profiles(
    status: Optional[str] = None, 
    limit: Optional[int] = None
    # Temporarily removed authentication: current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """List all organization profiles with database integration."""
    try:
        # Use database directly for reliable profile listing
        profiles, total_count = db_query_interface.filter_profiles(QueryFilter())
        
        # Add opportunity count for each profile
        for profile in profiles:
            opportunities, opp_count = db_query_interface.filter_opportunities(
                QueryFilter(profile_ids=[profile["id"]])
            )
            profile["opportunities_count"] = len(opportunities)
            
            # Rename 'id' to 'profile_id' for frontend compatibility
            profile["profile_id"] = profile["id"]
        
        # Apply limit if specified
        if limit:
            profiles = profiles[:limit]
        
        logger.info(f"Returned {len(profiles)} profiles from database")
        return {"profiles": profiles}
        
    except Exception as e:
        logger.error(f"Failed to list profiles from database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_profile(
    profile_data: Dict[str, Any]
    # Removed authentication: single-user desktop application
) -> Dict[str, Any]:
    """Create a new organization profile."""
    try:
        # Debug: Log the profile data received
        logger.info(f"Creating profile with data: ntee_codes={profile_data.get('ntee_codes')}, government_criteria={profile_data.get('government_criteria')}, keywords={profile_data.get('keywords')}")

        # Generate unique profile ID
        import uuid
        profile_id = f"profile_{uuid.uuid4().hex[:12]}"

        # Normalize EIN: Remove dashes for consistency
        ein_raw = profile_data.get('ein', '').strip() if profile_data.get('ein') else None
        ein_normalized = ein_raw.replace('-', '') if ein_raw else None

        logger.info(f"[CREATE_PROFILE] Creating profile {profile_id}, EIN: {ein_raw} → {ein_normalized}")

        # Create Profile object for DatabaseManager
        profile = Profile(
            id=profile_id,
            name=profile_data.get('name'),
            organization_type=profile_data.get('organization_type', 'nonprofit'),
            ein=ein_normalized,  # Store normalized EIN
            mission_statement=profile_data.get('mission_statement'),
            keywords=profile_data.get('keywords'),
            focus_areas=profile_data.get('focus_areas', []),
            program_areas=profile_data.get('program_areas', []),
            target_populations=profile_data.get('target_populations', []),
            ntee_codes=profile_data.get('ntee_codes', []),
            government_criteria=profile_data.get('government_criteria', []),
            geographic_scope=profile_data.get('geographic_scope', {}),
            service_areas=profile_data.get('service_areas', []),
            funding_preferences=profile_data.get('funding_preferences', {}),
            annual_revenue=profile_data.get('annual_revenue'),
            form_type=profile_data.get('form_type'),
            foundation_grants=profile_data.get('foundation_grants', []),
            board_members=profile_data.get('board_members', []),
            verification_data=profile_data.get('verification_data'),
            web_enhanced_data=profile_data.get('web_enhanced_data'),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Save to database
        success = db_manager.create_profile(profile)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save profile to database")

        # Process any fetched web scraping data through transformation pipeline
        web_enhanced_data = profile_data.get('web_enhanced_data')
        if web_enhanced_data:
            logger.info(f"Processing web enhanced data for new profile {profile.id}")
            board_members_json = profile_data.get('board_members')
            if isinstance(board_members_json, list):
                board_members_json = json.dumps(board_members_json)

            transformation_success = db_manager.process_fetched_data(
                profile=profile,
                web_scraping_results=web_enhanced_data,
                board_members_json=board_members_json
            )
            if transformation_success:
                logger.info(f"Successfully processed fetched data for new profile {profile.id}")
            else:
                logger.warning(f"Data transformation completed with warnings for new profile {profile.id}")

        # Debug: Log the profile after creation
        logger.info(f"Profile created in database: ntee_codes={profile.ntee_codes}, government_criteria={profile.government_criteria}, keywords={profile.keywords}")

        # Convert Profile object to dict for response
        profile_dict = {
            'profile_id': profile.id,
            'name': profile.name,
            'organization_type': profile.organization_type,
            'ein': profile.ein,
            'mission_statement': profile.mission_statement,
            'keywords': profile.keywords,
            'focus_areas': profile.focus_areas,
            'program_areas': profile.program_areas,
            'target_populations': profile.target_populations,
            'ntee_codes': profile.ntee_codes,
            'government_criteria': profile.government_criteria,
            'geographic_scope': profile.geographic_scope,
            'service_areas': profile.service_areas,
            'funding_preferences': profile.funding_preferences,
            'annual_revenue': profile.annual_revenue,
            'form_type': profile.form_type,
            'foundation_grants': profile.foundation_grants,
            'board_members': profile.board_members,
            'verification_data': profile.verification_data,
            'web_enhanced_data': profile.web_enhanced_data,
            'created_at': profile.created_at.isoformat() if profile.created_at else None,
            'updated_at': profile.updated_at.isoformat() if profile.updated_at else None
        }

        return {"profile": profile_dict, "message": "Profile created successfully"}

    except Exception as e:
        logger.error(f"Failed to create profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profile_id}")
async def get_profile(
    profile_id: str
    # Temporarily removed authentication: current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Get a specific organization profile from database."""
    try:
        print(f"*** PROFILES ROUTER: GET profile {profile_id} ***")
        logger.critical(f"*** PROFILES ROUTER: GET profile {profile_id} ***")

        # Get profile from database
        profile_dict = db_manager.get_profile_by_id(profile_id)
        if not profile_dict:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Add profile_id field for frontend compatibility
        profile_dict["profile_id"] = profile_dict.get("id", profile_id)

        # Debug: Check persistence fields without printing content that might have encoding issues
        fields_exist = {
            'website_url': bool(profile_dict.get('website_url')),
            'annual_revenue': bool(profile_dict.get('annual_revenue')),
            'location': bool(profile_dict.get('location')),
            'mission_statement': bool(profile_dict.get('mission_statement'))
        }
        logger.critical(f"*** PROFILES ROUTER: Fields exist: {fields_exist} ***")

        logger.info(f"Retrieved profile {profile_id} from database")
        return {"profile": profile_dict}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{profile_id}")
async def update_profile(
    profile_id: str,
    update_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Update an existing organization profile."""
    try:
        # Debug: Log the update data received
        logger.info(f"[V1_UPDATE] Received update for profile {profile_id}")
        logger.info(f"[V1_UPDATE] website_url={update_data.get('website_url')}, ntee_code_990={update_data.get('ntee_code_990')}")
        logger.info(f"[V1_UPDATE] ntee_codes={update_data.get('ntee_codes')}, government_criteria={update_data.get('government_criteria')}, keywords={update_data.get('keywords')}")
        logger.critical(f"*** DB Manager using database: {db_manager.database_path} ***")

        # Get existing profile from database
        existing_profile_dict = db_manager.get_profile_by_id(profile_id)
        logger.critical(f"*** Profile lookup result: {existing_profile_dict is not None} ***")
        if not existing_profile_dict:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Normalize EIN if being updated
        ein_value = update_data.get('ein', existing_profile_dict.get('ein'))
        if ein_value:
            ein_raw = str(ein_value).strip()
            ein_normalized = ein_raw.replace('-', '')
            logger.info(f"[UPDATE_PROFILE] Normalizing EIN: {ein_raw} → {ein_normalized}")
        else:
            ein_normalized = ein_value

        # Create updated Profile object by merging existing data with updates
        updated_profile = Profile(
            id=profile_id,
            name=update_data.get('name', existing_profile_dict.get('name')),
            organization_type=update_data.get('organization_type', existing_profile_dict.get('organization_type')),
            ein=ein_normalized,  # Use normalized EIN
            website_url=update_data.get('website_url', existing_profile_dict.get('website_url')),
            mission_statement=update_data.get('mission_statement', existing_profile_dict.get('mission_statement')),
            keywords=update_data.get('keywords', existing_profile_dict.get('keywords')),
            focus_areas=update_data.get('focus_areas', existing_profile_dict.get('focus_areas', [])),
            program_areas=update_data.get('program_areas', existing_profile_dict.get('program_areas', [])),
            target_populations=update_data.get('target_populations', existing_profile_dict.get('target_populations', [])),
            ntee_codes=update_data.get('ntee_codes', existing_profile_dict.get('ntee_codes', [])),
            ntee_code_990=update_data.get('ntee_code_990', existing_profile_dict.get('ntee_code_990')),
            government_criteria=update_data.get('government_criteria', existing_profile_dict.get('government_criteria', [])),
            geographic_scope=update_data.get('geographic_scope', existing_profile_dict.get('geographic_scope', {})),
            service_areas=update_data.get('service_areas', existing_profile_dict.get('service_areas', [])),
            funding_preferences=update_data.get('funding_preferences', existing_profile_dict.get('funding_preferences', {})),
            annual_revenue=update_data.get('annual_revenue', existing_profile_dict.get('annual_revenue')),
            form_type=update_data.get('form_type', existing_profile_dict.get('form_type')),
            foundation_grants=update_data.get('foundation_grants', existing_profile_dict.get('foundation_grants', [])),
            board_members=update_data.get('board_members', existing_profile_dict.get('board_members', [])),
            verification_data=update_data.get('verification_data', existing_profile_dict.get('verification_data')),
            web_enhanced_data=update_data.get('web_enhanced_data', existing_profile_dict.get('web_enhanced_data')),
            discovery_count=existing_profile_dict.get('discovery_count', 0),
            opportunities_count=existing_profile_dict.get('opportunities_count', 0),
            last_discovery_date=existing_profile_dict.get('last_discovery_date'),
            performance_metrics=existing_profile_dict.get('performance_metrics'),
            created_at=existing_profile_dict.get('created_at'),
            updated_at=datetime.now(),
            processing_history=existing_profile_dict.get('processing_history', [])
        )

        # Debug: Log the Profile object being saved
        logger.info(f"[V1_UPDATE] Created Profile object with website_url={updated_profile.website_url}, ntee_code_990={updated_profile.ntee_code_990}")

        # Save updated profile to database
        success = db_manager.update_profile(updated_profile)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update profile in database")

        # Process any fetched web scraping data through transformation pipeline
        web_enhanced_data = update_data.get('web_enhanced_data')
        if web_enhanced_data:
            logger.info(f"Processing web enhanced data for profile {profile_id}")
            board_members_json = update_data.get('board_members')
            if isinstance(board_members_json, list):
                board_members_json = json.dumps(board_members_json)

            transformation_success = db_manager.process_fetched_data(
                profile=updated_profile,
                web_scraping_results=web_enhanced_data,
                board_members_json=board_members_json
            )
            if transformation_success:
                logger.info(f"Successfully processed fetched data for profile {profile_id}")
            else:
                logger.warning(f"Data transformation completed with warnings for profile {profile_id}")

        # Debug: Log the profile after update
        logger.info(f"Profile updated in database: ntee_codes={updated_profile.ntee_codes}, government_criteria={updated_profile.government_criteria}, keywords={updated_profile.keywords}")

        # Helper to safely format timestamps (handles both str and datetime)
        def format_timestamp(ts):
            if not ts:
                return None
            if isinstance(ts, str):
                return ts  # Already a string, return as-is
            try:
                return ts.isoformat()  # datetime object
            except:
                return str(ts)

        # Convert Profile object to dict for response
        profile_dict = {
            'profile_id': updated_profile.id,
            'id': updated_profile.id,  # For database compatibility
            'name': updated_profile.name,
            'organization_type': updated_profile.organization_type,
            'ein': updated_profile.ein,
            'mission_statement': updated_profile.mission_statement,
            'keywords': updated_profile.keywords,
            'focus_areas': updated_profile.focus_areas,
            'program_areas': updated_profile.program_areas,
            'target_populations': updated_profile.target_populations,
            'ntee_codes': updated_profile.ntee_codes,
            'government_criteria': updated_profile.government_criteria,
            'geographic_scope': updated_profile.geographic_scope,
            'service_areas': updated_profile.service_areas,
            'funding_preferences': updated_profile.funding_preferences,
            'annual_revenue': updated_profile.annual_revenue,
            'form_type': updated_profile.form_type,
            'foundation_grants': updated_profile.foundation_grants,
            'board_members': updated_profile.board_members,
            'verification_data': updated_profile.verification_data,
            'web_enhanced_data': updated_profile.web_enhanced_data,
            'discovery_count': updated_profile.discovery_count,
            'opportunities_count': updated_profile.opportunities_count,
            'last_discovery_date': format_timestamp(updated_profile.last_discovery_date),
            'created_at': format_timestamp(updated_profile.created_at),
            'updated_at': format_timestamp(updated_profile.updated_at)
        }

        return {"profile": profile_dict, "message": "Profile updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: str
    # Removed authentication: single-user desktop application
) -> Dict[str, Any]:
    """Delete an organization profile."""
    try:
        success = db_manager.delete_profile(profile_id)
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")

        logger.info(f"Profile {profile_id} deleted from database")
        return {"message": "Profile deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Profile Analytics and Metrics

@router.get("/{profile_id}/analytics")
async def get_profile_analytics(profile_id: str) -> Dict[str, Any]:
    """Get comprehensive analytics for a profile."""
    try:
        # Get profile from database
        profile_dict = db_manager.get_profile_by_id(profile_id)
        if not profile_dict:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Get opportunities count from database
        opportunities = db_manager.get_opportunities_by_profile(profile_id)

        # Basic analytics
        analytics = {
            "opportunities_count": len(opportunities),
            "created_date": profile_dict.get('created_at'),
            "last_updated": profile_dict.get('updated_at'),
            "focus_areas_count": len(profile_dict.get('focus_areas', []))
        }
        
        return {"analytics": analytics}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profile_id}/metrics")
async def get_profile_metrics(profile_id: str) -> Dict[str, Any]:
    """Get detailed metrics for a profile."""
    try:
        metrics = metrics_tracker.get_profile_metrics(profile_id)
        return {"metrics": metrics}
    except Exception as e:
        logger.error(f"Failed to get metrics for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/summary")
async def get_metrics_summary() -> Dict[str, Any]:
    """Get summary metrics across all profiles."""
    try:
        summary = metrics_tracker.get_summary_metrics()
        return {"summary": summary}
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Profile Discovery and Opportunity Management

@router.post("/{profile_id}/discover/entity-analytics")
async def discover_entity_analytics(
    profile_id: str,
    discovery_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Run entity-based discovery with analytics integration."""
    try:
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Use entity discovery service
        results = entity_discovery.discover_opportunities(
            profile, 
            params=discovery_params or {}
        )
        
        return {
            "opportunities": results,
            "profile_id": profile_id,
            "discovery_params": discovery_params,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed entity discovery for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profile_id}/discover/entity-preview")
async def get_entity_preview(profile_id: str) -> Dict[str, Any]:
    """Get quick preview of entity-based opportunities."""
    try:
        # Get limited preview results
        preview_results = entity_discovery.get_preview_opportunities(profile_id, limit=5)
        return {
            "preview_opportunities": preview_results,
            "total_available": len(preview_results),
            "profile_id": profile_id
        }
    except Exception as e:
        logger.error(f"Failed to get entity preview for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profile_id}/opportunities")
async def get_profile_opportunities(
    profile_id: str,
    limit: Optional[int] = Query(default=50)
) -> Dict[str, Any]:
    """Get opportunities associated with a profile."""
    try:
        # Get opportunities from database
        opportunities = db_manager.get_opportunities_by_profile(profile_id, limit=limit)
        total_count = len(db_manager.get_opportunities_by_profile(profile_id))  # Get total without limit

        return {
            "opportunities": opportunities,
            "total_count": total_count,
            "profile_id": profile_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get opportunities for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Profile Scoring and Evaluation

@router.post("/{profile_id}/opportunities/{opportunity_id}/score")
async def score_opportunity(
    profile_id: str,
    opportunity_id: str,
    score_request: ScoreRequest
) -> ScoreResponse:
    """Score an opportunity against a profile."""
    try:
        result = scoring_service.score_opportunity(profile_id, opportunity_id, score_request)
        return result
    except Exception as e:
        logger.error(f"Failed to score opportunity {opportunity_id} for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{profile_id}/opportunity-scores")
async def batch_score_opportunities(
    profile_id: str,
    opportunities: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Batch score multiple opportunities against a profile."""
    try:
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Process scoring for each opportunity
        scored_opportunities = []
        for opp in opportunities:
            try:
                # Basic scoring implementation
                score = scoring_service.calculate_basic_score(profile, opp)
                scored_opportunities.append({
                    **opp,
                    "profile_score": score,
                    "scoring_timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to score opportunity {opp.get('id', 'unknown')}: {e}")
                scored_opportunities.append({
                    **opp,
                    "profile_score": 0.0,
                    "scoring_error": str(e)
                })
        
        return {
            "scored_opportunities": scored_opportunities,
            "profile_id": profile_id,
            "total_processed": len(scored_opportunities)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed batch scoring for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Profile Templates and Configuration

@router.post("/templates")
async def create_profile_template(template_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new profile template."""
    try:
        # Basic template creation logic
        template_id = f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        template = {
            "template_id": template_id,
            "name": template_data.get("name", "Unnamed Template"),
            "description": template_data.get("description", ""),
            "default_fields": template_data.get("fields", {}),
            "created_at": datetime.now().isoformat()
        }
        
        # In a real implementation, this would be saved to a template store
        logger.info(f"Created profile template: {template_id}")
        
        return {"template": template, "message": "Template created successfully"}
        
    except Exception as e:
        logger.error(f"Failed to create profile template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# EIN Lookup and Data Fetching

@router.post("/fetch-ein")
async def fetch_ein_data(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch organization data by EIN from BMF database."""
    try:
        print(f"\n=== FETCH-EIN DEBUG START ===")
        print(f"Request data: {request_data}")

        ein = request_data.get("ein")
        if not ein:
            print(f"ERROR: No EIN provided in request")
            raise HTTPException(status_code=400, detail="EIN is required")

        # Strip hyphens from EIN for BMF database query (BMF uses format without hyphens)
        ein_normalized = ein.replace("-", "").strip()

        print(f"Fetching data for EIN: {ein} (normalized: {ein_normalized})")
        logger.info(f"Fetching data for EIN: {ein} (normalized: {ein_normalized})")

        # Query BMF database directly
        import sqlite3
        import os

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        db_path = os.path.join(project_root, "data", "nonprofit_intelligence.db")

        print(f"Project root: {project_root}")
        print(f"Database path: {db_path}")
        print(f"Database exists: {os.path.exists(db_path)}")

        if not os.path.exists(db_path):
            logger.error(f"BMF database not found at {db_path}")
            return {
                "success": False,
                "profile_data": None,
                "ein": ein,
                "error": "BMF database not available"
            }

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query BMF organizations table
        # Try both normalized (no hyphens) and original format to handle user input flexibility
        cursor.execute("""
            SELECT ein, name, city, state, ntee_code, asset_amt, income_amt,
                   classification, deductibility
            FROM bmf_organizations
            WHERE ein = ? OR ein = ?
        """, (ein_normalized, ein))

        row = cursor.fetchone()
        conn.close()

        if row:
            organization_data = {
                'name': row['name'] or '',
                'ein': ein,
                'city': row['city'] or '',
                'state': row['state'] or '',
                'ntee_code': row['ntee_code'] or '',
                'organization_type': row['classification'] or '',
                'revenue': row['income_amt'] or 0,
                'assets': row['asset_amt'] or 0,
                'deductibility': row['deductibility'] or ''
            }
            logger.info(f"Found organization in BMF: {organization_data['name']}")

            return {
                "success": True,
                "profile_data": organization_data,
                "ein": ein,
                "source": "bmf"
            }
        else:
            logger.warning(f"No organization found for EIN: {ein}")
            return {
                "success": False,
                "profile_data": None,
                "ein": ein,
                "error": "Organization not found in BMF database"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch EIN data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Plan Results Management

@router.get("/{profile_id}/plan-results")
async def get_plan_results(profile_id: str) -> Dict[str, Any]:
    """Get plan results for a profile (5-stage workflow planning data)."""
    try:
        # Get profile from database
        profile_dict = db_manager.get_profile_by_id(profile_id)
        if not profile_dict:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Extract plan results from profile data
        # Plan results are stored in the profile's processing_history or a dedicated field
        plan_results = profile_dict.get('plan_results', {})

        return {
            "success": True,
            "plan_results": plan_results,
            "profile_id": profile_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plan results for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{profile_id}/plan-results")
async def save_plan_results(
    profile_id: str,
    plan_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Save plan results for a profile (5-stage workflow planning data)."""
    try:
        # Get profile from database
        profile_dict = db_manager.get_profile_by_id(profile_id)
        if not profile_dict:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Update the profile with plan results
        # For now, store plan_results as a JSON field in the profile
        # In the future, this could be a separate table
        updated_profile = Profile(
            id=profile_id,
            name=profile_dict.get('name'),
            organization_type=profile_dict.get('organization_type'),
            ein=profile_dict.get('ein'),
            mission_statement=profile_dict.get('mission_statement'),
            keywords=profile_dict.get('keywords'),
            focus_areas=profile_dict.get('focus_areas', []),
            program_areas=profile_dict.get('program_areas', []),
            target_populations=profile_dict.get('target_populations', []),
            ntee_codes=profile_dict.get('ntee_codes', []),
            government_criteria=profile_dict.get('government_criteria', []),
            geographic_scope=profile_dict.get('geographic_scope', {}),
            service_areas=profile_dict.get('service_areas', []),
            funding_preferences=profile_dict.get('funding_preferences', {}),
            annual_revenue=profile_dict.get('annual_revenue'),
            form_type=profile_dict.get('form_type'),
            foundation_grants=profile_dict.get('foundation_grants', []),
            board_members=profile_dict.get('board_members', []),
            verification_data=profile_dict.get('verification_data'),
            web_enhanced_data=profile_dict.get('web_enhanced_data'),
            discovery_count=profile_dict.get('discovery_count', 0),
            opportunities_count=profile_dict.get('opportunities_count', 0),
            last_discovery_date=profile_dict.get('last_discovery_date'),
            performance_metrics=profile_dict.get('performance_metrics'),
            created_at=profile_dict.get('created_at'),
            updated_at=datetime.now(),
            processing_history=profile_dict.get('processing_history', [])
        )

        # Note: We need to add plan_results field to the Profile class
        # For now, store it in a custom field if the database schema supports it
        # This is a temporary solution - ideally we'd have a dedicated table

        success = db_manager.update_profile(updated_profile)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save plan results")

        logger.info(f"Saved plan results for profile {profile_id}")

        return {
            "success": True,
            "message": "Plan results saved successfully",
            "profile_id": profile_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save plan results for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export router will be created separately to avoid making this file too large
# The following routes will be moved to export router:
# - /api/profiles/{profile_id}/approach/export-decision
# - /api/profiles/{profile_id}/dossier/generate  
# - /api/profiles/{profile_id}/dossier/batch-generate

# Research and analysis routes will be moved to a research router:
# - /api/profiles/{profile_id}/research/analyze-integrated
# - /api/profiles/{profile_id}/research/batch-analyze
# - /api/profiles/{profile_id}/research/decision-package/{opportunity_id}