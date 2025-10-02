"""
Task 19: Modernized Profile API Endpoints

Updated profile endpoints using tools instead of processors:
- ProfileEnhancementOrchestrator for profile building
- ProfileQualityScorer for quality assessment
- UnifiedProfileService for profile management
- Direct BMF/990 database queries

Replaces legacy processor-based endpoints with tool-based architecture.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
import logging
import sqlite3
from datetime import datetime

from src.profiles.unified_service import UnifiedProfileService
from src.profiles.orchestration import ProfileEnhancementOrchestrator, WorkflowResult
from src.profiles.quality_scoring import (
    ProfileQualityScorer,
    OpportunityQualityScorer,
    DataCompletenessValidator,
    QualityScore
)
from src.profiles.models import UnifiedProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/profiles", tags=["profiles_v2"])

# Initialize services
profile_service = UnifiedProfileService()
orchestrator = ProfileEnhancementOrchestrator()
profile_scorer = ProfileQualityScorer()
opportunity_scorer = OpportunityQualityScorer()
completeness_validator = DataCompletenessValidator()


@router.post("/build")
async def build_profile_with_orchestration(request: Dict[str, Any]):
    """
    Build a comprehensive profile using the orchestration workflow.

    Request:
    {
        "ein": "123456789",
        "enable_tool25": true,  # Optional, default true
        "enable_tool2": false,  # Optional, default false (costs $0.75)
        "quality_threshold": 0.70  # Optional, default 0.70
    }

    Response:
    {
        "profile": {...},  # Profile data
        "workflow_result": {...},  # Workflow execution details
        "quality_score": {...},  # Quality assessment
        "completeness": {...}  # Data completeness metrics
    }
    """
    try:
        ein = request.get('ein', '').strip()
        if not ein:
            raise HTTPException(status_code=400, detail="EIN is required")

        enable_tool25 = request.get('enable_tool25', True)
        enable_tool2 = request.get('enable_tool2', False)
        quality_threshold = request.get('quality_threshold', 0.70)

        logger.info(f"Building profile for EIN {ein} (Tool25={enable_tool25}, Tool2={enable_tool2})")

        # Execute orchestrated profile building workflow
        workflow_result: WorkflowResult = orchestrator.execute_profile_building(
            ein=ein,
            enable_tool25=enable_tool25,
            enable_tool2=enable_tool2,
            quality_threshold=quality_threshold
        )

        if not workflow_result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Profile building failed: {', '.join(workflow_result.errors)}"
            )

        # Extract profile data from workflow result
        profile_data = workflow_result.profile_data

        # Calculate quality score
        quality_score = profile_scorer.calculate_profile_quality(
            bmf_data=workflow_result.steps_completed.get('bmf_discovery', {}).get('data'),
            form_990=workflow_result.steps_completed.get('form_990', {}).get('data'),
            tool25_data=workflow_result.steps_completed.get('tool_25', {}).get('data'),
            tool2_data=workflow_result.steps_completed.get('tool_2', {}).get('data')
        )

        # Calculate completeness
        completeness = completeness_validator.validate_profile_completeness(
            bmf_data=workflow_result.steps_completed.get('bmf_discovery', {}).get('data'),
            form_990=workflow_result.steps_completed.get('form_990', {}).get('data'),
            tool25_data=workflow_result.steps_completed.get('tool_25', {}).get('data'),
            tool2_data=workflow_result.steps_completed.get('tool_2', {}).get('data')
        )

        # Create UnifiedProfile and save to database
        try:
            unified_profile = UnifiedProfile(**profile_data)
            profile_service.create_profile(unified_profile)
            logger.info(f"Profile saved to database for EIN {ein}")
        except Exception as save_error:
            logger.warning(f"Failed to save profile to database: {save_error}")
            # Continue anyway - return the data even if save fails

        return {
            "success": True,
            "profile": profile_data,
            "workflow_result": {
                "success": workflow_result.success,
                "steps_completed": list(workflow_result.steps_completed.keys()),
                "total_cost": workflow_result.total_cost,
                "total_duration": workflow_result.total_duration,
                "quality_score": workflow_result.quality_score,
                "errors": workflow_result.errors,
                "recommendations": workflow_result.recommendations
            },
            "quality_assessment": {
                "overall_score": quality_score.overall_score,
                "rating": quality_score.rating.value,
                "component_scores": quality_score.component_scores,
                "missing_fields": quality_score.missing_fields[:10],  # First 10
                "recommendations": quality_score.recommendations
            },
            "completeness": completeness
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to build profile for EIN {ein}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profile_id}/quality")
async def get_profile_quality(profile_id: str):
    """
    Get quality assessment for an existing profile.

    Returns:
    {
        "quality_score": {...},
        "completeness": {...},
        "recommendations": [...]
    }
    """
    try:
        # Load profile from database
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        # Load associated data from intelligence database
        bmf_data = None
        form_990 = None

        if profile.ein:
            # Query BMF data
            db_path = "data/nonprofit_intelligence.db"
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get BMF data
            cursor.execute(
                "SELECT * FROM bmf_organizations WHERE ein = ?",
                (profile.ein,)
            )
            bmf_row = cursor.fetchone()
            if bmf_row:
                bmf_data = dict(bmf_row)

            # Get Form 990 data (most recent)
            cursor.execute(
                """
                SELECT * FROM form_990
                WHERE ein = ?
                ORDER BY tax_year DESC
                LIMIT 1
                """,
                (profile.ein,)
            )
            form_990_row = cursor.fetchone()
            if form_990_row:
                form_990 = dict(form_990_row)

            conn.close()

        # Calculate quality score
        quality_score = profile_scorer.calculate_profile_quality(
            bmf_data=bmf_data,
            form_990=form_990,
            tool25_data=None,  # Would need to load from profile data
            tool2_data=None
        )

        # Calculate completeness
        completeness = completeness_validator.validate_profile_completeness(
            bmf_data=bmf_data,
            form_990=form_990,
            tool25_data=None,
            tool2_data=None
        )

        return {
            "profile_id": profile_id,
            "quality_score": {
                "overall_score": quality_score.overall_score,
                "rating": quality_score.rating.value,
                "component_scores": quality_score.component_scores,
                "missing_fields": quality_score.missing_fields,
                "recommendations": quality_score.recommendations
            },
            "completeness": completeness
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{profile_id}/opportunities/score")
async def score_opportunity(profile_id: str, request: Dict[str, Any]):
    """
    Score an opportunity match for a profile.

    Request:
    {
        "opportunity_type": "funding",  # or "networking"
        "opportunity_data": {
            "ein": "987654321",
            "name": "Example Foundation",
            ...
        }
    }

    Returns:
    {
        "score": {...}
    }
    """
    try:
        # Load profile
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        opportunity_type = request.get('opportunity_type', 'funding')
        opportunity_data = request.get('opportunity_data', {})

        if not opportunity_data:
            raise HTTPException(status_code=400, detail="opportunity_data is required")

        # Convert profile to dict for scoring
        profile_dict = {
            'ntee_codes': profile.ntee_codes or [],
            'geographic_scope': profile.geographic_scope or {},
            'annual_budget': getattr(profile, 'annual_budget', 0)
        }

        # Score based on type
        if opportunity_type == 'funding':
            score = opportunity_scorer.score_funding_opportunity(
                profile=profile_dict,
                foundation=opportunity_data
            )
        elif opportunity_type == 'networking':
            score = opportunity_scorer.score_networking_opportunity(
                profile=profile_dict,
                peer_org=opportunity_data
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid opportunity_type: {opportunity_type}. Must be 'funding' or 'networking'"
            )

        return {
            "profile_id": profile_id,
            "opportunity_type": opportunity_type,
            "score": {
                "overall_score": score.overall_score,
                "rating": score.rating.value,
                "component_scores": score.component_scores,
                "recommendations": score.recommendations
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to score opportunity for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profile_id}/opportunities/funding")
async def discover_funding_opportunities(
    profile_id: str,
    state: Optional[str] = None,
    min_score: float = 0.50,
    limit: int = 100
):
    """
    Discover funding opportunities (foundations) for a profile.

    Query Parameters:
    - state: Filter by state (optional)
    - min_score: Minimum quality score (default 0.50)
    - limit: Maximum results (default 100)

    Returns list of scored funding opportunities.
    """
    try:
        # Load profile
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        # Query BMF for foundations
        db_path = "data/nonprofit_intelligence.db"
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

        if state:
            query += " AND b.state = ?"
            params.append(state)

        if profile.ntee_codes:
            # Filter by NTEE codes if available
            ntee_placeholders = ','.join('?' * len(profile.ntee_codes))
            query += f" AND b.ntee_code IN ({ntee_placeholders})"
            params.extend(profile.ntee_codes)

        query += f" LIMIT {limit * 2}"  # Get more, then filter by score

        cursor.execute(query, params)
        foundations = cursor.fetchall()
        conn.close()

        logger.info(f"Found {len(foundations)} foundations for profile {profile_id}")

        # Convert profile to dict for scoring
        profile_dict = {
            'ntee_codes': profile.ntee_codes or [],
            'geographic_scope': {'states': profile.geographic_scope.get('states', []) if profile.geographic_scope else []},
            'annual_budget': getattr(profile, 'annual_budget', 0)
        }

        # Score each foundation
        scored_opportunities = []
        for foundation_row in foundations:
            foundation_dict = dict(foundation_row)

            # Prepare foundation data for scoring
            opportunity = {
                'ein': foundation_dict.get('ein'),
                'name': foundation_dict.get('name'),
                'state': foundation_dict.get('state'),
                'funded_ntee_codes': [foundation_dict.get('ntee_code')] if foundation_dict.get('ntee_code') else [],
                'avg_grant_size': foundation_dict.get('distribamt', 0) / 10 if foundation_dict.get('distribamt') else 0,  # Rough estimate
                'similar_recipient_count': 0,  # Would need Schedule I analysis
                'accepts_applications': True,  # Default assumption
                'nationwide_scope': False
            }

            # Score this funding opportunity
            score = opportunity_scorer.score_funding_opportunity(
                profile=profile_dict,
                foundation=opportunity
            )

            if score.overall_score >= min_score:
                scored_opportunities.append({
                    'foundation': foundation_dict,
                    'score': {
                        'overall_score': score.overall_score,
                        'rating': score.rating.value,
                        'component_scores': score.component_scores,
                        'recommendations': score.recommendations
                    }
                })

        # Sort by score descending
        scored_opportunities.sort(key=lambda x: x['score']['overall_score'], reverse=True)

        # Limit to requested number
        scored_opportunities = scored_opportunities[:limit]

        logger.info(f"Returning {len(scored_opportunities)} scored opportunities (min_score={min_score})")

        return {
            "profile_id": profile_id,
            "total_found": len(foundations),
            "total_scored_above_threshold": len(scored_opportunities),
            "min_score": min_score,
            "opportunities": scored_opportunities
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to discover funding opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profile_id}/opportunities/networking")
async def discover_networking_opportunities(
    profile_id: str,
    state: Optional[str] = None,
    min_score: float = 0.50,
    limit: int = 100
):
    """
    Discover networking opportunities (peer nonprofits) for a profile.

    Query Parameters:
    - state: Filter by state (optional)
    - min_score: Minimum quality score (default 0.50)
    - limit: Maximum results (default 100)

    Returns list of scored networking opportunities.
    """
    try:
        # Load profile
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        # Query BMF for peer nonprofits
        db_path = "data/nonprofit_intelligence.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query for peer nonprofits (exclude foundations)
        query = """
            SELECT b.*, f.totrevenue, f.totfuncexpns, f.totassetsend
            FROM bmf_organizations b
            LEFT JOIN form_990 f ON b.ein = f.ein
            WHERE (b.foundation_code NOT IN ('15', '16') OR b.foundation_code IS NULL)
        """
        params = []

        if state:
            query += " AND b.state = ?"
            params.append(state)

        if profile.ntee_codes:
            # Filter by NTEE codes if available
            ntee_placeholders = ','.join('?' * len(profile.ntee_codes))
            query += f" AND b.ntee_code IN ({ntee_placeholders})"
            params.extend(profile.ntee_codes)

        query += f" LIMIT {limit * 2}"  # Get more, then filter by score

        cursor.execute(query, params)
        peer_orgs = cursor.fetchall()
        conn.close()

        logger.info(f"Found {len(peer_orgs)} peer organizations for profile {profile_id}")

        # Convert profile to dict for scoring
        profile_dict = {
            'ntee_codes': profile.ntee_codes or [],
            'geographic_scope': {'states': profile.geographic_scope.get('states', []) if profile.geographic_scope else []},
            'annual_budget': getattr(profile, 'annual_budget', 0)
        }

        # Score each peer org
        scored_opportunities = []
        for peer_row in peer_orgs:
            peer_dict = dict(peer_row)

            # Prepare peer data for scoring
            peer_opportunity = {
                'ein': peer_dict.get('ein'),
                'name': peer_dict.get('name'),
                'ntee_codes': [peer_dict.get('ntee_code')] if peer_dict.get('ntee_code') else [],
                'state': peer_dict.get('state'),
                'annual_budget': peer_dict.get('totrevenue', 0),
                'shared_board_members': 0,  # Would need board analysis
                'shared_funders': 0  # Would need Schedule I cross-analysis
            }

            # Score this networking opportunity
            score = opportunity_scorer.score_networking_opportunity(
                profile=profile_dict,
                peer_org=peer_opportunity
            )

            if score.overall_score >= min_score:
                scored_opportunities.append({
                    'peer_organization': peer_dict,
                    'score': {
                        'overall_score': score.overall_score,
                        'rating': score.rating.value,
                        'component_scores': score.component_scores,
                        'recommendations': score.recommendations
                    }
                })

        # Sort by score descending
        scored_opportunities.sort(key=lambda x: x['score']['overall_score'], reverse=True)

        # Limit to requested number
        scored_opportunities = scored_opportunities[:limit]

        logger.info(f"Returning {len(scored_opportunities)} scored networking opportunities (min_score={min_score})")

        return {
            "profile_id": profile_id,
            "total_found": len(peer_orgs),
            "total_scored_above_threshold": len(scored_opportunities),
            "min_score": min_score,
            "opportunities": scored_opportunities
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to discover networking opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for v2 profile API."""
    return {
        "status": "healthy",
        "version": "2.0",
        "features": [
            "orchestrated_profile_building",
            "quality_scoring",
            "funding_opportunity_discovery",
            "networking_opportunity_discovery"
        ],
        "tools": [
            "ProfileEnhancementOrchestrator",
            "ProfileQualityScorer",
            "OpportunityQualityScorer",
            "DataCompletenessValidator"
        ]
    }
