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
from src.database.database_manager import DatabaseManager, Opportunity
from src.config.database_config import get_nonprofit_intelligence_db, get_catalynx_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/profiles", tags=["profiles_v2"])

# Initialize services
profile_service = UnifiedProfileService()
orchestrator = ProfileEnhancementOrchestrator()
profile_scorer = ProfileQualityScorer()
opportunity_scorer = OpportunityQualityScorer()
completeness_validator = DataCompletenessValidator()
database_manager = DatabaseManager(get_catalynx_db())


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
    db_path = get_nonprofit_intelligence_db()

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

        # Join with foundation data to get grant-making info (use most recent filing)
        sql = f"""
            SELECT
                b.ein,
                b.name,
                b.state,
                b.city,
                b.ntee_code,
                b.income_amt,
                b.asset_amt,
                b.subsection,
                b.ruling_date,
                b.foundation_code,
                MAX(pf.distribamt) as grants_distributed
            FROM bmf_organizations b
            LEFT JOIN form_990pf pf ON b.ein = pf.ein
            WHERE ({where_clause})
            AND b.subsection IN ('03', '04')  -- 501(c)(3) and 501(c)(4) only
            GROUP BY b.ein, b.name, b.state, b.city, b.ntee_code, b.income_amt, b.asset_amt, b.subsection, b.ruling_date, b.foundation_code
            ORDER BY b.income_amt DESC
        """

        # Remove LIMIT - score all matching orgs, filter by threshold later

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
    db_path = get_nonprofit_intelligence_db()

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
                    prgmservrevnue, totcntrbgfts, invstmntinc,
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
                        totrcptperbks as totrevenue,
                        totexpnspbks as totexpns,
                        totassetsend,
                        totliabend,
                        distribamt as contributions_paid,
                        grscontrgifts as contributions_received,
                        tax_year
                    FROM form_990pf
                    WHERE ein = ?
                    ORDER BY tax_year DESC
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
                        totrevnue as totrevenue,
                        totexpns,
                        totassetsend,
                        totliabltend as totliabend,
                        totcntrbs as contributions,
                        prgmservrev as program_revenue,
                        tax_year
                    FROM form_990ez
                    WHERE ein = ?
                    ORDER BY tax_year DESC
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
    Calculate multi-dimensional scores for DISCOVER stage with Grant-Making focus.

    6 Dimensions for DISCOVER stage:
    1. Mission Alignment (25%) - NTEE code match
    2. Geographic Fit (20%) - State/region matching
    3. Financial Match (15%) - Revenue/assets compatibility
    4. Grant-Making Capacity (25%) - Foundation type + grants distributed
    5. Eligibility (10%) - 501(c)(3) status
    6. Timing (5%) - Placeholder (grant cycles unknown)

    Grant-Making Capacity Tiers (small nonprofit friendly):
    - Tier 1: $10K-$25K → +0.15 (active small grantor)
    - Tier 2: $25K-$100K → +0.25 (solid grantor)
    - Tier 3: $100K-$500K → +0.35 (strong grantor)
    - Tier 4: $500K+ → +0.45 (major grantor)
    - Foundation code 16 → +0.40 (private grantmaking foundation)
    - Foundation code 15 → +0.20 (operating foundation)

    Args:
        enriched_orgs: Organizations with 990 data and foundation info
        profile: User's profile with Target NTEE Codes, location preferences

    Returns:
        Organizations with overall_score, confidence, dimensional_scores, stage_category
    """
    scored_orgs = []

    # Get profile criteria
    target_ntee_codes = profile.ntee_codes or []
    target_states = profile.government_criteria.get('states', ['VA']) if hasattr(profile, 'government_criteria') and profile.government_criteria else ['VA']

    for org in enriched_orgs:
        # Calculate 6 dimensional scores
        dimensions = {}

        # 1. Mission Alignment (23%) - NTEE code match
        # Monte Carlo optimized weight: 0.230
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
            'weight': 0.230,
            'weighted_score': ntee_score * 0.230,
            'data_quality': 1.0 if org_ntee else 0.5
        }

        # 2. Geographic Fit (11%) - State match
        # Monte Carlo optimized weight: 0.108
        geo_score = 0.5  # Default
        org_state = org.get('state', '')
        if org_state in target_states:
            geo_score = 1.0
        dimensions['geographic_fit'] = {
            'raw_score': geo_score,
            'weight': 0.108,
            'weighted_score': geo_score * 0.108,
            'data_quality': 1.0 if org_state else 0.3
        }

        # 3. Financial Match (15%) - Revenue compatibility
        fin_score = 0.5  # Default
        org_revenue = org.get('990_data', {}).get('revenue', 0) if org.get('990_data') else org.get('income_amt', 0)

        # Handle None values
        if org_revenue is None:
            org_revenue = 0
        else:
            org_revenue = float(org_revenue)

        if org_revenue > 0:
            # Simple revenue band scoring
            if 100000 <= org_revenue <= 10000000:  # $100K - $10M sweet spot
                fin_score = 0.9
            elif 10000 <= org_revenue < 100000:  # Small
                fin_score = 0.6
            elif org_revenue > 10000000:  # Large
                fin_score = 0.7
        dimensions['financial_match'] = {
            'raw_score': fin_score,
            'weight': 0.156,
            'weighted_score': fin_score * 0.156,
            'data_quality': 1.0 if org_revenue > 0 else 0.3
        }

        # 4. Grant-Making Capacity (36%) - EVIDENCE-BASED scoring
        # Monte Carlo optimization determined this should be highest weight (35.8%)
        grant_score = 0.0  # Default (no evidence of grant-making)
        foundation_code = org.get('foundation_code')
        grants_distributed = org.get('grants_distributed')

        # Handle None values
        if grants_distributed is None:
            grants_distributed = 0
        else:
            grants_distributed = float(grants_distributed)

        # Grants distributed tiers (EVIDENCE-BASED - small nonprofit friendly)
        if grants_distributed >= 500000:  # Tier 4: Major grantor ($500K+)
            grant_score = 0.90
        elif grants_distributed >= 100000:  # Tier 3: Strong grantor ($100K-$500K)
            grant_score = 0.70
        elif grants_distributed >= 25000:  # Tier 2: Solid grantor ($25K-$100K)
            grant_score = 0.50
        elif grants_distributed >= 10000:  # Tier 1: Active small grantor ($10K-$25K)
            grant_score = 0.30
        elif grants_distributed > 0:  # Under $10K - minimal but active
            grant_score = 0.15
        # Foundation code ONLY adds points if there's grant evidence
        elif foundation_code == '16':  # Grantmaking foundation but NO grants data
            grant_score = 0.10  # Low score - classified but no evidence
        elif foundation_code == '15':  # Operating foundation, no grants
            grant_score = 0.05  # Minimal - may give grants but no data
        # Grant-seekers (no foundation code, no grants) = 0.0 (default)

        dimensions['grant_making_capacity'] = {
            'raw_score': grant_score,
            'weight': 0.358,
            'weighted_score': grant_score * 0.358,
            'data_quality': 1.0 if (foundation_code or grants_distributed > 0) else 0.2,
            'foundation_code': foundation_code,
            'grants_distributed': grants_distributed
        }

        # 5. Eligibility (7%) - 501(c)(3) status
        # Monte Carlo optimized weight: 0.069
        elig_score = 1.0 if org.get('subsection') in ['03', '04'] else 0.5
        dimensions['eligibility'] = {
            'raw_score': elig_score,
            'weight': 0.069,
            'weighted_score': elig_score * 0.069,
            'data_quality': 1.0
        }

        # 6. Timing (8%) - Placeholder (unknown grant cycles)
        # Monte Carlo optimized weight: 0.078
        dimensions['timing'] = {
            'raw_score': 0.7,  # Neutral score
            'weight': 0.078,
            'weighted_score': 0.7 * 0.078,
            'data_quality': 0.3  # Low quality (no data)
        }

        # Calculate overall score (sum of weighted scores)
        overall_score = sum(d['weighted_score'] for d in dimensions.values())

        # Calculate confidence (average data quality)
        avg_quality = sum(d['data_quality'] for d in dimensions.values()) / len(dimensions)
        confidence_level = "high" if avg_quality >= 0.8 else "medium" if avg_quality >= 0.5 else "low"

        # Categorize by score (percentile-based thresholds)
        # Based on observed score distribution: min=0.533, max=0.745, mean=0.621
        if overall_score >= 0.74:  # ~99.5th percentile - best matches
            category_level = "qualified"
        elif overall_score >= 0.71:  # ~97th percentile - strong candidates
            category_level = "review"
        elif overall_score >= 0.68:  # ~90th percentile - worth deeper look
            category_level = "consider"
        else:
            category_level = "low_priority"

        # Add scoring data to org
        scored_org = org.copy()
        scored_org['overall_score'] = round(overall_score, 3)
        scored_org['confidence'] = confidence_level
        scored_org['category_level'] = category_level
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
            db_path = get_nonprofit_intelligence_db()
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
        db_path = get_nonprofit_intelligence_db()
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
        logger.info(f"[ENDPOINT] List profiles called with limit={limit}, offset={offset}, search={search}")

        # Get all profiles (UnifiedProfileService doesn't have list method, so query directly)
        logger.info(f"[ENDPOINT] Calling profile_service.list_profiles()")
        profiles = profile_service.list_profiles(limit=limit, offset=offset, search=search)
        logger.info(f"[ENDPOINT] Retrieved {len(profiles) if profiles else 0} profiles")

        # Sort profiles
        reverse = (order == "desc")
        if sort == "name":
            profiles.sort(key=lambda p: p.get('organization_name', ''), reverse=reverse)
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
        logger.error(f"[ENDPOINT] Failed to list profiles: {e}", exc_info=True)
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
                "category_level": "qualified",  # qualified, review, consider, low_priority
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

        # Scoring parameters
        min_score_threshold = request.get('min_score_threshold', 0.62)  # 50th percentile - baseline qualification
        max_return_limit = request.get('max_return_limit', 500)  # Safety cap for UI performance
        auto_scrapy_count = request.get('auto_scrapy_count', 20)

        logger.info(f"Starting discovery for profile {profile_id} with NTEE codes: {target_ntee_codes}")
        logger.info(f"Parameters: min_score={min_score_threshold}, max_return={max_return_limit}")

        # Step 1: BMF Filter - Query nonprofit_intelligence.db (NO LIMIT - score all)
        bmf_start = time.time()
        bmf_results = _query_bmf_database(target_ntee_codes, None)  # None = no limit
        bmf_time = time.time() - bmf_start
        logger.info(f"BMF Filter found {len(bmf_results)} organizations in {bmf_time:.2f}s")

        # Step 2: 990 Data Enrichment - Add financial data from 990/990-PF/990-EZ filings
        enrichment_start = time.time()
        enriched_results = _enrich_with_990_data(bmf_results)
        enrichment_time = time.time() - enrichment_start
        logger.info(f"990 enrichment completed for {len(enriched_results)} organizations in {enrichment_time:.2f}s")

        # Step 3: Multi-Dimensional Scoring - Calculate compatibility scores
        scoring_start = time.time()
        scored_results = _calculate_multi_dimensional_scores(enriched_results, profile)
        scoring_time = time.time() - scoring_start
        logger.info(f"Multi-dimensional scoring completed for {len(scored_results)} organizations in {scoring_time:.2f}s")

        # Step 4: Filter by score threshold and apply safety cap
        qualified_results = [org for org in scored_results if org['overall_score'] >= min_score_threshold]
        qualified_results = qualified_results[:max_return_limit]  # Safety cap
        logger.info(f"After score filter (≥{min_score_threshold}): {len(qualified_results)} qualified organizations")

        # TODO: Step 4 - Web Intelligence Tool Scrapy (integrate in next task)

        # Convert qualified results to opportunities
        opportunities = []
        for org in qualified_results:
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
                "category_level": org.get("category_level", "low_priority"),
                "dimensional_scores": org.get("dimensional_scores", {}),
                "web_search_complete": False,
                "990_data": org.get("990_data"),
                "grant_history": org.get("grant_history")
            })

        # Calculate summary statistics
        summary_counts = {"qualified": 0, "review": 0, "consider": 0, "low_priority": 0}
        for opp in opportunities:
            category = opp["category_level"]
            summary_counts[category] = summary_counts.get(category, 0) + 1

        summary = {
            "total_found": len(opportunities),  # Total opportunities returned to UI
            "total_bmf_matches": len(bmf_results),
            "total_scored": len(scored_results),
            "total_qualified": len(qualified_results),
            "total_returned": len(opportunities),
            "qualified": summary_counts.get("qualified", 0),
            "review": summary_counts.get("review", 0),
            "consider": summary_counts.get("consider", 0),
            "low_priority": summary_counts.get("low_priority", 0),
            "min_score_threshold": min_score_threshold,
            "scrapy_completed": 0
        }

        execution_time = time.time() - start_time

        # Performance breakdown
        performance = {
            "total_time": execution_time,
            "bmf_query_time": bmf_time,
            "enrichment_time": enrichment_time,
            "scoring_time": scoring_time,
            "orgs_per_second": int(len(scored_results) / execution_time) if execution_time > 0 else 0
        }

        logger.info(f"Discovery complete: {len(bmf_results)} BMF → {len(scored_results)} scored → {len(qualified_results)} qualified in {execution_time:.2f}s ({performance['orgs_per_second']} orgs/sec)")

        # Step 4: Save discovered opportunities to database
        saved_count = 0
        import hashlib
        import time as time_module

        for opp_data in opportunities:
            try:
                # Generate unique opportunity ID: opp_discovery_{timestamp}_{ein_hash}
                timestamp_ms = int(time_module.time() * 1000)
                ein_hash = hashlib.md5((opp_data.get('ein', '') or '').encode()).hexdigest()[:8]
                opportunity_id = f"opp_discovery_{timestamp_ms}_{ein_hash}"

                # Create Opportunity object
                opportunity = Opportunity(
                    id=opportunity_id,
                    profile_id=profile_id,
                    organization_name=opp_data['organization_name'],
                    ein=opp_data.get('ein'),
                    current_stage='discovery',  # Initial stage for discovered opportunities
                    overall_score=opp_data.get('overall_score', 0.0),
                    confidence_level=0.8 if opp_data.get('confidence') == 'high' else 0.6,
                    scored_at=datetime.now(),
                    scorer_version='multi_dimensional_v1.0',
                    analysis_discovery={
                        'dimensional_scores': opp_data.get('dimensional_scores', {}),
                        'category_level': opp_data.get('category_level'),
                        '990_data': opp_data.get('990_data'),
                        'grant_history': opp_data.get('grant_history'),
                        'location': opp_data.get('location')
                    },
                    source='nonprofit',  # Discovery source
                    discovery_date=datetime.now(),
                    processing_status='discovered',
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

                # Save to database
                success = database_manager.create_opportunity(opportunity)
                if success:
                    saved_count += 1
                    # Add ID to response for frontend reference
                    opp_data['opportunity_id'] = opportunity_id
                else:
                    logger.warning(f"Failed to save opportunity {opportunity_id}")

            except Exception as e:
                logger.error(f"Error saving opportunity {opp_data.get('organization_name')}: {e}")

        logger.info(f"Saved {saved_count}/{len(opportunities)} opportunities to database")
        summary['saved_to_database'] = saved_count

        return {
            "status": "success",
            "profile_id": profile_id,
            "opportunities": opportunities,
            "summary": summary,
            "performance": performance,
            "execution_time": execution_time
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Discovery failed for profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profile_id}/opportunities")
async def get_profile_opportunities(profile_id: str, stage: Optional[str] = None):
    """
    Get all saved opportunities for a profile from the database.

    Query params:
    - stage: Optional filter by current_stage (discovery, screening, intelligence, etc.)

    Returns:
    {
        "status": "success",
        "profile_id": "...",
        "opportunities": [...],
        "total_count": 42,
        "summary": {
            "auto_qualified": 18,
            "review": 22,
            ...
        }
    }
    """
    try:
        from src.database.query_interface import DatabaseQueryInterface, QueryFilter

        db_query = DatabaseQueryInterface()

        # Build filter
        query_filter = QueryFilter(profile_ids=[profile_id])

        # Get all opportunities for this profile
        opportunities_raw, total_count = db_query.filter_opportunities(query_filter)

        # Filter by stage if specified
        if stage:
            opportunities_raw = [opp for opp in opportunities_raw if opp.get('current_stage') == stage]

        # Convert to frontend format
        opportunities = []
        summary_counts = {"qualified": 0, "review": 0, "consider": 0, "low_priority": 0}

        for opp_raw in opportunities_raw:
            # Extract analysis_discovery data
            discovery_data = opp_raw.get('analysis_discovery', {})
            if isinstance(discovery_data, str):
                import json
                discovery_data = json.loads(discovery_data)

            category_level = discovery_data.get('category_level', 'low_priority')
            summary_counts[category_level] = summary_counts.get(category_level, 0) + 1

            opportunities.append({
                "opportunity_id": opp_raw.get('id'),
                "organization_name": opp_raw.get('organization_name'),
                "ein": opp_raw.get('ein'),
                "location": discovery_data.get('location', {}),
                "overall_score": opp_raw.get('overall_score', 0.0),
                "confidence": "high" if opp_raw.get('confidence_level', 0) >= 0.75 else "medium",
                "category_level": category_level,
                "dimensional_scores": discovery_data.get('dimensional_scores', {}),
                "990_data": discovery_data.get('990_data'),
                "grant_history": discovery_data.get('grant_history'),
                "current_stage": opp_raw.get('current_stage'),
                "discovery_date": opp_raw.get('discovery_date')
            })

        summary = {
            "total_found": len(opportunities),
            "qualified": summary_counts.get("qualified", 0),
            "review": summary_counts.get("review", 0),
            "consider": summary_counts.get("consider", 0),
            "low_priority": summary_counts.get("low_priority", 0),
            "scrapy_completed": 0
        }

        logger.info(f"Retrieved {len(opportunities)} opportunities for profile {profile_id}")

        return {
            "status": "success",
            "profile_id": profile_id,
            "opportunities": opportunities,
            "total_count": len(opportunities),
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Failed to retrieve opportunities for profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
