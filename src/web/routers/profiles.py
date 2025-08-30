#!/usr/bin/env python3
"""
Profiles Router
Handles all profile-related API endpoints including CRUD, analytics, discovery, and opportunity management
Extracted from monolithic main.py for better modularity
"""

from fastapi import APIRouter, HTTPException, Depends, Query
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

# Import essential services only
from src.database.query_interface import DatabaseQueryInterface, QueryFilter

# Try to import optional services (with fallbacks)
try:
    from src.profiles.service import ProfileService
    PROFILE_SERVICE_AVAILABLE = True
except ImportError:
    PROFILE_SERVICE_AVAILABLE = False

try:
    from src.auth.jwt_auth import get_current_user_dependency, User
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/api/profiles", tags=["profiles"])

# Initialize essential services
db_query_interface = DatabaseQueryInterface()

# Initialize optional services with fallbacks
profile_service = None
if PROFILE_SERVICE_AVAILABLE:
    try:
        profile_service = ProfileService()
    except Exception as e:
        logger.warning(f"Could not initialize ProfileService: {e}")
        PROFILE_SERVICE_AVAILABLE = False


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
        # Fallback to old method if database fails and service is available
        if PROFILE_SERVICE_AVAILABLE and profile_service:
            try:
                old_profiles = profile_service.list_profiles(status=status, limit=limit)
                profile_dicts = []
                for profile in old_profiles:
                    profile_dict = profile.model_dump()
                    profile_dict["opportunities_count"] = len(profile.associated_opportunities)
                    profile_dicts.append(profile_dict)
                
                logger.info(f"Fallback: Returned {len(profile_dicts)} profiles from file system")
                return {"profiles": profile_dicts}
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
        
        # Return empty result if all methods fail
        logger.error("All profile retrieval methods failed, returning empty result")
        return {"profiles": [], "error": "Unable to retrieve profiles"}


@router.post("")
async def create_profile(
    profile_data: Dict[str, Any],
    current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Create a new organization profile."""
    try:
        # Debug: Log the profile data received
        logger.info(f"Creating profile with data: ntee_codes={profile_data.get('ntee_codes')}, government_criteria={profile_data.get('government_criteria')}, keywords={profile_data.get('keywords')}")
        
        profile = profile_service.create_profile(profile_data)
        
        # Debug: Log the profile after creation
        logger.info(f"Profile after creation: ntee_codes={profile.ntee_codes}, government_criteria={profile.government_criteria}, keywords={profile.keywords}")
        
        return {"profile": profile.model_dump(), "message": "Profile created successfully"}
        
    except Exception as e:
        logger.error(f"Failed to create profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profile_id}")
async def get_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Get a specific organization profile with unified analytics."""
    try:
        # Try unified service first for enhanced analytics
        unified_profile = unified_service.get_profile(profile_id)
        if unified_profile:
            return {"profile": unified_profile.model_dump()}
        
        # Fallback to old service
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {"profile": profile.model_dump()}
        
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
        logger.info(f"Updating profile {profile_id} with data: ntee_codes={update_data.get('ntee_codes')}, government_criteria={update_data.get('government_criteria')}, keywords={update_data.get('keywords')}")
        
        profile = profile_service.update_profile(profile_id, update_data)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Debug: Log the profile after update
        logger.info(f"Profile after update: ntee_codes={profile.ntee_codes}, government_criteria={profile.government_criteria}, keywords={profile.keywords}")
        
        return {"profile": profile.model_dump(), "message": "Profile updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Delete an organization profile."""
    try:
        success = profile_service.delete_profile(profile_id)
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Also clean up from unified service
        try:
            unified_service.delete_profile(profile_id)
        except Exception as e:
            logger.warning(f"Failed to delete from unified service: {e}")
        
        logger.info(f"Profile {profile_id} deleted by user {current_user.username}")
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
        # Try unified service first
        unified_profile = unified_service.get_profile(profile_id)
        if unified_profile and unified_profile.analytics:
            return {"analytics": unified_profile.analytics.model_dump()}
        
        # Fallback to basic analytics
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Basic analytics
        analytics = {
            "opportunities_count": len(profile.associated_opportunities),
            "created_date": profile.created_at.isoformat() if profile.created_at else None,
            "last_updated": profile.updated_at.isoformat() if profile.updated_at else None,
            "focus_areas_count": len(profile.focus_areas) if profile.focus_areas else 0
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
        # Try unified service first
        unified_profile = unified_service.get_profile(profile_id)
        if unified_profile:
            opportunities = unified_profile.associated_opportunities[:limit] if limit else unified_profile.associated_opportunities
            return {
                "opportunities": opportunities,
                "total_count": len(unified_profile.associated_opportunities),
                "profile_id": profile_id
            }
        
        # Fallback to old service
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        opportunities = profile.associated_opportunities[:limit] if limit else profile.associated_opportunities
        return {
            "opportunities": opportunities,
            "total_count": len(profile.associated_opportunities),
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
    """Fetch organization data by EIN."""
    try:
        ein = request_data.get("ein")
        if not ein:
            raise HTTPException(status_code=400, detail="EIN is required")
        
        # Use EIN lookup processor
        from src.processors.lookup.ein_lookup import EINLookupProcessor
        ein_processor = EINLookupProcessor()
        
        # Create minimal config for lookup
        config = {"ein": ein}
        result = ein_processor.execute(config)
        
        if result and result.get("success"):
            return {
                "organization_data": result.get("data", {}),
                "ein": ein,
                "source": "irs_bmf"
            }
        else:
            return {
                "organization_data": None,
                "ein": ein,
                "error": "No data found for EIN"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch EIN data: {e}")
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