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


# Helper Functions for SCREENING Stage

def _query_bmf_database(ntee_codes: List[str], max_results: int = 200) -> List[Dict[str, Any]]:
    """
    Query nonprofit_intelligence.db for organizations matching NTEE codes.

    Args:
        ntee_codes: List of NTEE codes from Profile's Target NTEE Codes
        max_results: Maximum number of results to return

    Returns:
        List of organization dictionaries with EIN, name, state, city, revenue, assets
    """
    db_path = "data/nonprofit_intelligence.db"

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()

        # Build query with NTEE code filtering
        # Match on major code (first letter) OR full code
        # Example: If Profile has ["P20", "E31"], match orgs with NTEE starting with P or E, or exact match
        ntee_conditions = []
        params = []

        for code in ntee_codes:
            if len(code) >= 1:
                major_code = code[0]  # First letter (e.g., 'P' from 'P20')
                ntee_conditions.append("(ntee_code LIKE ? OR ntee_code = ?)")
                params.extend([f"{major_code}%", code])

        where_clause = " OR ".join(ntee_conditions) if ntee_conditions else "1=1"

        sql = f"""
            SELECT
                ein,
                name,
                state,
                city,
                ntee_code,
                income_amt,
                asset_amt,
                subsection,
                ruling_date
            FROM bmf_organizations
            WHERE ({where_clause})
            AND subsection IN ('03', '04')  -- 501(c)(3) and 501(c)(4) only
            ORDER BY income_amt DESC
            LIMIT ?
        """

        params.append(max_results)

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # Convert to list of dicts
        results = [dict(row) for row in rows]

        conn.close()

        logger.info(f"BMF query returned {len(results)} organizations")
        return results

    except Exception as e:
        logger.error(f"BMF database query failed: {e}", exc_info=True)
        return []


def _enrich_with_990_data(bmf_orgs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich BMF organizations with 990 financial data.

    Args:
        bmf_orgs: List of organizations from BMF query

    Returns:
        List of organizations enriched with 990 data (revenue, expenses, program ratios, etc.)
    """
    db_path = "data/nonprofit_intelligence.db"

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        enriched_orgs = []

        for org in bmf_orgs:
            ein = org.get('ein')
            if not ein:
                enriched_orgs.append(org)
                continue

            # Try to find 990 data - check all three form types
            form_990_data = None
            form_type = None

            # Check Form 990 (regular nonprofits)
            cursor.execute("""
                SELECT
                    totrevenue, totfuncexpns, totassetsend, totliabend,
                    totprgmrevnue, totcntrbgfts, invstmntinc,
                    compnsatncurrofcr, othrsalwages, profndraising,
                    tax_pd as tax_year
                FROM form_990
                WHERE ein = ?
                ORDER BY tax_pd DESC
                LIMIT 1
            """, (ein,))
            row = cursor.fetchone()
            if row:
                form_990_data = dict(row)
                form_type = "990"

            # Check Form 990-PF (private foundations)
            if not form_990_data:
                cursor.execute("""
                    SELECT
                        totrevenue, totexpns, totassetsend, totliabend,
                        contrpdduringyr as contributions_paid,
                        totcntrbrcvd as contributions_received,
                        grntspaidtoindiv as grants_to_individuals,
                        grntstotorgspaid as grants_to_orgs,
                        tax_pd as tax_year
                    FROM form_990pf
                    WHERE ein = ?
                    ORDER BY tax_pd DESC
                    LIMIT 1
                """, (ein,))
                row = cursor.fetchone()
                if row:
                    form_990_data = dict(row)
                    form_type = "990-PF"

            # Check Form 990-EZ (smaller nonprofits)
            if not form_990_data:
                cursor.execute("""
                    SELECT
                        totrevenue, totexpns, totassetsend, totliabend,
                        totcntrbs as contributions,
                        prgmservrev as program_revenue,
                        tax_pd as tax_year
                    FROM form_990ez
                    WHERE ein = ?
                    ORDER BY tax_pd DESC
                    LIMIT 1
                """, (ein,))
                row = cursor.fetchone()
                if row:
                    form_990_data = dict(row)
                    form_type = "990-EZ"

            # Merge 990 data into org
            enriched_org = org.copy()

            if form_990_data:
                # Calculate program expense ratio for 990 (if available)
                program_ratio = None
                if form_type == "990" and form_990_data.get('totfuncexpns'):
                    total_expenses = form_990_data['totfuncexpns'] or 0
                    program_expenses = form_990_data.get('totprgmrevnue') or 0
                    if total_expenses > 0:
                        program_ratio = (program_expenses / total_expenses) * 100

                enriched_org['990_data'] = {
                    'form_type': form_type,
                    'tax_year': form_990_data.get('tax_year'),
                    'revenue': form_990_data.get('totrevenue') or 0,
                    'expenses': form_990_data.get('totfuncexpns') or form_990_data.get('totexpns') or 0,
                    'assets': form_990_data.get('totassetsend') or 0,
                    'liabilities': form_990_data.get('totliabend') or 0,
                    'program_ratio': program_ratio,
                    'raw_data': form_990_data
                }

                # For 990-PF, add grant-making data
                if form_type == "990-PF":
                    enriched_org['grant_history'] = {
                        'grants_paid': form_990_data.get('contributions_paid') or 0,
                        'grants_to_individuals': form_990_data.get('grants_to_individuals') or 0,
                        'grants_to_orgs': form_990_data.get('grants_to_orgs') or 0,
                        'tax_year': form_990_data.get('tax_year')
                    }
            else:
                enriched_org['990_data'] = None
                enriched_org['grant_history'] = None

            enriched_orgs.append(enriched_org)

        conn.close()

        logger.info(f"Enriched {len(enriched_orgs)} organizations with 990 data")
        return enriched_orgs

    except Exception as e:
        logger.error(f"990 enrichment failed: {e}", exc_info=True)
        return bmf_orgs  # Return original data if enrichment fails


def _calculate_multi_dimensional_scores(
    enriched_orgs: List[Dict[str, Any]],
    profile: UnifiedProfile
) -> List[Dict[str, Any]]:
    """
    Calculate multi-dimensional scores for DISCOVER stage using simplified algorithm.

    5 Dimensions for DISCOVER stage:
    1. Mission Alignment (30%) - NTEE code match
    2. Geographic Fit (25%) - State/region matching
    3. Financial Match (20%) - Revenue/assets compatibility
    4. Eligibility (15%) - 501(c)(3) status
    5. Timing (10%) - Placeholder (grant cycles unknown)

    Args:
        enriched_orgs: Organizations with 990 data
        profile: User's profile with Target NTEE Codes, location preferences

    Returns:
        Organizations with overall_score, confidence, dimensional_scores, stage_category
    """
    scored_orgs = []

    # Get profile criteria
    target_ntee_codes = profile.ntee_codes or []
    target_states = profile.government_criteria.get('states', ['VA']) if hasattr(profile, 'government_criteria') and profile.government_criteria else ['VA']

    for org in enriched_orgs:
        # Calculate 5 dimensional scores
        dimensions = {}

        # 1. Mission Alignment (30%) - NTEE code match
        ntee_score = 0.5  # Default medium score
        org_ntee = org.get('ntee_code', '')
        if org_ntee:
            for target_code in target_ntee_codes:
                if org_ntee.startswith(target_code[0]):  # Major category match
                    ntee_score = 0.7
                if org_ntee == target_code:  # Exact match
                    ntee_score = 1.0
                    break
        dimensions['mission_alignment'] = {
            'raw_score': ntee_score,
            'weight': 0.30,
            'weighted_score': ntee_score * 0.30,
            'data_quality': 1.0 if org_ntee else 0.5
        }

        # 2. Geographic Fit (25%) - State match
        geo_score = 0.5  # Default
        org_state = org.get('state', '')
        if org_state in target_states:
            geo_score = 1.0
        dimensions['geographic_fit'] = {
            'raw_score': geo_score,
            'weight': 0.25,
            'weighted_score': geo_score * 0.25,
            'data_quality': 1.0 if org_state else 0.3
        }

        # 3. Financial Match (20%) - Revenue compatibility
        fin_score = 0.5  # Default
        org_revenue = org.get('990_data', {}).get('revenue', 0) if org.get('990_data') else org.get('income_amt', 0)
        if org_revenue:
            # Simple revenue band scoring
            if 100000 <= org_revenue <= 10000000:  # $100K - $10M sweet spot
                fin_score = 0.9
            elif 10000 <= org_revenue < 100000:  # Small
                fin_score = 0.6
            elif org_revenue > 10000000:  # Large
                fin_score = 0.7
        dimensions['financial_match'] = {
            'raw_score': fin_score,
            'weight': 0.20,
            'weighted_score': fin_score * 0.20,
            'data_quality': 1.0 if org_revenue > 0 else 0.3
        }

        # 4. Eligibility (15%) - 501(c)(3) status
        elig_score = 1.0 if org.get('subsection') in ['03', '04'] else 0.5
        dimensions['eligibility'] = {
            'raw_score': elig_score,
            'weight': 0.15,
            'weighted_score': elig_score * 0.15,
            'data_quality': 1.0
        }

        # 5. Timing (10%) - Placeholder (unknown grant cycles)
        dimensions['timing'] = {
            'raw_score': 0.7,  # Neutral score
            'weight': 0.10,
            'weighted_score': 0.7 * 0.10,
            'data_quality': 0.3  # Low quality (no data)
        }

        # Calculate overall score (sum of weighted scores)
        overall_score = sum(d['weighted_score'] for d in dimensions.values())

        # Calculate confidence (average data quality)
        avg_quality = sum(d['data_quality'] for d in dimensions.values()) / len(dimensions)
        confidence_level = "high" if avg_quality >= 0.8 else "medium" if avg_quality >= 0.5 else "low"

        # Categorize by score
        if overall_score >= 0.85:
            stage_category = "auto_qualified"
        elif overall_score >= 0.70:
            stage_category = "review"
        elif overall_score >= 0.55:
            stage_category = "consider"
        else:
            stage_category = "low_priority"

        # Add scoring data to org
        scored_org = org.copy()
        scored_org['overall_score'] = round(overall_score, 3)
        scored_org['confidence'] = confidence_level
        scored_org['stage_category'] = stage_category
        scored_org['dimensional_scores'] = dimensions

        scored_orgs.append(scored_org)

    # Sort by overall score descending
    scored_orgs.sort(key=lambda x: x['overall_score'], reverse=True)

    logger.info(f"Scored {len(scored_orgs)} organizations")
    return scored_orgs


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


@router.post("", status_code=201)
async def create_profile(request: Dict[str, Any]):
    """
    Create a new profile manually (without EIN-based building).

    Request:
    {
        "name": "Organization Name",
        "ein": "123456789",  # Optional
        "description": "...",
        "ntee_codes": ["P20"],
        "geographic_scope": {"states": ["VA"]},
        ...
    }
    """
    try:
        name = request.get('name', '').strip()
        if not name:
            raise HTTPException(status_code=400, detail="Organization name is required")

        # Create UnifiedProfile
        profile = UnifiedProfile(
            ein=request.get('ein'),
            name=name,
            description=request.get('description'),
            ntee_codes=request.get('ntee_codes', []),
            geographic_scope=request.get('geographic_scope', {}),
            contact_info=request.get('contact_info', {}),
            mission_statement=request.get('mission_statement'),
            programs=request.get('programs', []),
            board_members=request.get('board_members', []),
            created_at=datetime.utcnow().isoformat()
        )

        # Save to database
        success = profile_service.create_profile(profile)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to create profile")

        logger.info(f"Created profile: {profile.profile_id}")

        return {
            "success": True,
            "profile_id": profile.profile_id,
            "profile": profile.__dict__
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_profiles(
    page: int = 1,
    limit: int = 50,
    sort: str = "name",
    order: str = "asc",
    search: Optional[str] = None
):
    """
    List all profiles with pagination and filtering.

    Query Parameters:
    - page: Page number (default 1)
    - limit: Results per page (default 50, max 200)
    - sort: Sort field (name, created_at, updated_at)
    - order: Sort order (asc, desc)
    - search: Search term for name/EIN
    """
    try:
        limit = min(limit, 200)  # Cap at 200
        offset = (page - 1) * limit

        # Get all profiles (UnifiedProfileService doesn't have list method, so query directly)
        profiles = profile_service.list_profiles(limit=limit, offset=offset, search=search)

        # Sort profiles
        reverse = (order == "desc")
        if sort == "name":
            profiles.sort(key=lambda p: p.get('name', ''), reverse=reverse)
        elif sort == "created_at":
            profiles.sort(key=lambda p: p.get('created_at', ''), reverse=reverse)
        elif sort == "updated_at":
            profiles.sort(key=lambda p: p.get('updated_at', ''), reverse=reverse)

        return {
            "success": True,
            "page": page,
            "limit": limit,
            "total": len(profiles),
            "profiles": profiles
        }

    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profile_id}")
async def get_profile_details(profile_id: str):
    """Get detailed profile information."""
    try:
        profile = profile_service.get_profile(profile_id)

        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        return {
            "success": True,
            "profile": profile.__dict__ if hasattr(profile, '__dict__') else profile
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{profile_id}")
async def update_profile(profile_id: str, updates: Dict[str, Any]):
    """
    Update profile fields.

    Request:
    {
        "name": "New Name",
        "description": "Updated description",
        ...
    }
    """
    try:
        # Get existing profile
        existing_profile = profile_service.get_profile(profile_id)
        if not existing_profile:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        # Update fields
        for key, value in updates.items():
            if hasattr(existing_profile, key) and key not in ['profile_id', 'created_at']:
                setattr(existing_profile, key, value)

        # Update timestamp
        existing_profile.updated_at = datetime.utcnow().isoformat()

        # Save
        success = profile_service.update_profile(existing_profile)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update profile")

        logger.info(f"Updated profile: {profile_id}")

        return {
            "success": True,
            "profile_id": profile_id,
            "profile": existing_profile.__dict__
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{profile_id}")
async def delete_profile(profile_id: str):
    """Delete a profile."""
    try:
        success = profile_service.delete_profile(profile_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        logger.info(f"Deleted profile: {profile_id}")

        return {
            "success": True,
            "profile_id": profile_id,
            "message": "Profile deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profile_id}/analytics")
async def get_profile_analytics(profile_id: str):
    """
    Get consolidated analytics for a profile.

    Combines metrics, funnel data, and session information.
    """
    try:
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        # Get analytics from profile service
        analytics = profile_service.get_profile_analytics(profile_id)

        return {
            "success": True,
            "profile_id": profile_id,
            "analytics": analytics
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{profile_id}/export")
async def export_profile_data(profile_id: str, export_config: Dict[str, Any]):
    """
    Export profile data in various formats.

    Request:
    {
        "format": "json",  # or "csv", "excel", "pdf"
        "fields": ["name", "ein", "revenue"],  # Optional
        "include_opportunities": true
    }

    Uses Tool 18 (Data Export Tool)
    """
    try:
        from src.core.tool_registry import ToolRegistry

        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        # Prepare data for export
        export_data = profile.__dict__ if hasattr(profile, '__dict__') else profile

        # Get opportunities if requested
        if export_config.get('include_opportunities', False):
            # Would query opportunities from database
            export_data['opportunities'] = []

        # Filter fields if specified
        if 'fields' in export_config:
            export_data = {k: v for k, v in export_data.items() if k in export_config['fields']}

        # Use Tool 18 (Data Export Tool)
        tool_registry = ToolRegistry()
        export_result = await tool_registry.execute_tool(
            tool_name="data-export-tool",
            inputs={
                "data": export_data,
                "format": export_config.get('format', 'json'),
                "filename": f"profile_{profile_id}"
            }
        )

        if not export_result.success:
            raise HTTPException(status_code=500, detail="Export failed")

        return {
            "success": True,
            "profile_id": profile_id,
            "format": export_config.get('format', 'json'),
            "export_result": export_result.data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{profile_id}/discover")
async def discover_nonprofit_opportunities(profile_id: str, request: Dict[str, Any]):
    """
    SCREENING Stage: Discover nonprofit opportunities using BMF + 990 + Scoring + Scrapy.

    Workflow:
    1. BMF Filter Tool → Find orgs matching Profile's Target NTEE Codes
    2. 990 Parser Tools → Enrich with financial data
    3. Multi-Dimensional Scorer Tool → Calculate compatibility scores
    4. Web Intelligence Tool → Scrapy top 20 Auto-Qualified orgs

    Request:
    {
        "max_results": 200,  # Optional, default 200
        "auto_scrapy_count": 20  # Optional, run Scrapy on top N scored orgs
    }

    Response:
    {
        "status": "success",
        "profile_id": "...",
        "opportunities": [
            {
                "organization_name": "...",
                "ein": "...",
                "location": {"state": "...", "city": "..."},
                "revenue": 0,
                "overall_score": 0.89,
                "confidence": "high",
                "stage_category": "auto_qualified",  # auto_qualified, review, consider, low_priority
                "dimensional_scores": {...},
                "web_search_complete": true,
                "990_data": {...},
                "grant_history": {...}  # For 990-PF only
            }
        ],
        "summary": {
            "total_found": 200,
            "auto_qualified": 18,
            "review": 42,
            "consider": 38,
            "low_priority": 102,
            "scrapy_completed": 18
        },
        "execution_time": 12.5
    }
    """
    try:
        import time
        start_time = time.time()

        # Get profile to extract Target NTEE Codes
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        # Extract NTEE Codes from profile
        target_ntee_codes = profile.ntee_codes or []
        if not target_ntee_codes:
            raise HTTPException(
                status_code=400,
                detail="Profile has no NTEE Codes. Please configure in Profile modal."
            )

        max_results = request.get('max_results', 200)
        auto_scrapy_count = request.get('auto_scrapy_count', 20)

        logger.info(f"Starting discovery for profile {profile_id} with NTEE codes: {target_ntee_codes}")

        # Step 1: BMF Filter - Query nonprofit_intelligence.db
        bmf_results = _query_bmf_database(target_ntee_codes, max_results)
        logger.info(f"BMF Filter found {len(bmf_results)} organizations")

        # Step 2: 990 Data Enrichment - Add financial data from 990/990-PF/990-EZ filings
        enriched_results = _enrich_with_990_data(bmf_results)
        logger.info(f"990 enrichment completed for {len(enriched_results)} organizations")

        # Step 3: Multi-Dimensional Scoring - Calculate compatibility scores
        scored_results = _calculate_multi_dimensional_scores(enriched_results, profile)
        logger.info(f"Multi-dimensional scoring completed for {len(scored_results)} organizations")

        # TODO: Step 4 - Web Intelligence Tool Scrapy (integrate in next task)

        # Convert scored results to opportunities
        opportunities = []
        for org in scored_results:
            # Use 990 revenue if available, otherwise BMF estimate
            revenue = 0
            if org.get('990_data') and org['990_data'].get('revenue'):
                revenue = org['990_data']['revenue']
            else:
                revenue = org.get("income_amt", 0)

            opportunities.append({
                "organization_name": org.get("name", ""),
                "ein": org.get("ein", ""),
                "location": {
                    "state": org.get("state", ""),
                    "city": org.get("city", "")
                },
                "revenue": revenue,
                "overall_score": org.get("overall_score", 0.0),
                "confidence": org.get("confidence", "low"),
                "stage_category": org.get("stage_category", "low_priority"),
                "dimensional_scores": org.get("dimensional_scores", {}),
                "web_search_complete": False,
                "990_data": org.get("990_data"),
                "grant_history": org.get("grant_history")
            })

        # Calculate summary statistics
        summary_counts = {"auto_qualified": 0, "review": 0, "consider": 0, "low_priority": 0}
        for opp in opportunities:
            category = opp["stage_category"]
            summary_counts[category] = summary_counts.get(category, 0) + 1

        summary = {
            "total_found": len(opportunities),
            "auto_qualified": summary_counts.get("auto_qualified", 0),
            "review": summary_counts.get("review", 0),
            "consider": summary_counts.get("consider", 0),
            "low_priority": summary_counts.get("low_priority", 0),
            "scrapy_completed": 0
        }

        execution_time = time.time() - start_time

        return {
            "status": "success",
            "profile_id": profile_id,
            "opportunities": opportunities,
            "summary": summary,
            "execution_time": execution_time
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Discovery failed for profile {profile_id}: {e}", exc_info=True)
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
            "networking_opportunity_discovery",
            "crud_operations",
            "analytics",
            "export"
        ],
        "tools": [
            "ProfileEnhancementOrchestrator",
            "ProfileQualityScorer",
            "OpportunityQualityScorer",
            "DataCompletenessValidator"
        ]
    }
