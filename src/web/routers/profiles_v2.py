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
from pydantic import BaseModel, Field, validator
import logging
import sqlite3
from datetime import datetime, timezone

from src.profiles.unified_service import UnifiedProfileService
from src.profiles.orchestration import ProfileEnhancementOrchestrator, WorkflowResult, StepResult
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


# Pydantic Request Models for Input Validation

class DiscoveryRequest(BaseModel):
    """Request model for nonprofit discovery endpoint."""
    min_score_threshold: float = Field(default=0.62, ge=0.0, le=1.0, description="Minimum score threshold (0.0-1.0)")
    max_return_limit: int = Field(default=500, ge=1, le=10000, description="Maximum results to return")
    auto_scrapy_count: int = Field(default=20, ge=0, le=100, description="Number of top orgs to auto-scrape")
    max_results: int = Field(default=200, ge=1, le=10000, description="Maximum orgs to query from BMF")

    @validator('min_score_threshold')
    def validate_score(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Score threshold must be between 0.0 and 1.0')
        return v


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

        # Validate NTEE codes to prevent SQL injection
        import re
        NTEE_PATTERN = re.compile(r'^[A-Z][0-9]{0,2}[A-Z]?$')  # e.g., P, P20, P20Z
        VALID_NTEE_MAJOR_CODES = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

        ntee_conditions = []
        params = []

        for code in ntee_codes:
            # Validate NTEE code format
            if not NTEE_PATTERN.match(code):
                logger.warning(f"Invalid NTEE code format rejected: {code}")
                continue

            if len(code) >= 1:
                major_code = code[0]  # First letter (e.g., 'P' from 'P20')

                # Validate major code is in allowed set
                if major_code not in VALID_NTEE_MAJOR_CODES:
                    logger.warning(f"Invalid NTEE major code rejected: {major_code}")
                    continue

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

        # Add safety limit to prevent OOM with broad filters
        MAX_QUERY_LIMIT = 10000  # Safety limit for memory protection
        sql += f" LIMIT {MAX_QUERY_LIMIT}"

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # Log if we hit the safety limit
        if len(rows) >= MAX_QUERY_LIMIT:
            logger.warning(f"BMF query hit safety limit ({MAX_QUERY_LIMIT} orgs) with NTEE codes {ntee_codes}. Results may be incomplete.")

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

        # Normalize EIN: accept both "123456789" and "12-3456789" formats
        # Store the clean version for database queries
        ein_clean = ein.replace('-', '')

        enable_tool25 = request.get('enable_tool25', True)
        enable_tool2 = request.get('enable_tool2', False)
        quality_threshold = request.get('quality_threshold', 0.70)

        # Phase 3: Extract retry parameters if provided (manual retry from UI)
        tool25_params = request.get('tool25_params', {})
        tool25_retry = request.get('tool25_retry', False)
        max_pages = tool25_params.get('max_pages')
        max_depth = tool25_params.get('depth')
        timeout = tool25_params.get('timeout')

        retry_label = " (MANUAL RETRY)" if tool25_retry else ""
        logger.info(f"[BUILD_PROFILE] Building profile{retry_label} for EIN {ein_clean} (Tool25={enable_tool25}, Tool2={enable_tool2})")
        if tool25_params:
            logger.info(f"[BUILD_PROFILE] Tool 25 custom params: max_pages={max_pages}, depth={max_depth}, timeout={timeout}")

        # Check if profile already exists by EIN (search by EIN value, not just profile ID)
        # This handles profiles created manually with random IDs
        existing_profile = None
        profile_id = f"profile_{ein_clean}"

        # First try to find by EIN-based profile ID
        existing_profile = profile_service.get_profile(profile_id)

        # If not found, search all profiles for matching EIN (with or without dash)
        if not existing_profile:
            logger.info(f"[BUILD_PROFILE] Profile {profile_id} not found, searching by EIN value...")
            all_profiles = profile_service.list_profiles(limit=1000)  # Get all profiles
            for p in all_profiles:
                p_ein = p.get('ein', '').replace('-', '')  # Normalize to compare
                if p_ein == ein_clean:
                    existing_profile_dict = p
                    profile_id = p.get('profile_id')  # Use existing profile ID!
                    logger.info(f"[BUILD_PROFILE] Found existing profile by EIN: {profile_id}")
                    # Convert dict to UnifiedProfile object
                    from src.profiles.models import UnifiedProfile
                    existing_profile = profile_service.get_profile(profile_id)
                    break
        existing_website = existing_profile.website_url if existing_profile and existing_profile.website_url else None
        existing_ntee = existing_profile.ntee_code_990 if existing_profile and existing_profile.ntee_code_990 else None
        existing_ntee_codes = existing_profile.ntee_codes if existing_profile and existing_profile.ntee_codes else None
        existing_gov_criteria = existing_profile.government_criteria if existing_profile and existing_profile.government_criteria else None

        if existing_website:
            logger.info(f"[BUILD_PROFILE] Using existing profile's website URL: {existing_website}")
        if existing_ntee:
            logger.info(f"[BUILD_PROFILE] Using existing profile's NTEE code: {existing_ntee}")
        if existing_ntee_codes:
            logger.info(f"[BUILD_PROFILE] Using existing profile's NTEE codes: {existing_ntee_codes}")
        if existing_gov_criteria:
            logger.info(f"[BUILD_PROFILE] Using existing profile's government criteria: {existing_gov_criteria}")

        # Execute orchestrated profile building workflow
        workflow_result: WorkflowResult = orchestrator.execute_profile_building(
            ein=ein_clean,
            enable_tool25=enable_tool25,
            enable_tool2=enable_tool2,
            quality_threshold=quality_threshold,
            website_url=existing_website,  # Pass existing website URL if available
            ntee_code_990=existing_ntee,  # Pass existing NTEE code if available
            ntee_codes=existing_ntee_codes,  # Pass existing NTEE codes list if available
            government_criteria=existing_gov_criteria,  # Pass existing government criteria if available
            tool25_max_pages=max_pages,  # Phase 3: Manual retry parameters
            tool25_max_depth=max_depth,
            tool25_timeout=timeout
        )

        logger.info(f"[BUILD_PROFILE] Workflow completed: success={workflow_result.success}, steps={len(workflow_result.steps_completed)}")
        for step in workflow_result.steps_completed:
            logger.info(f"[BUILD_PROFILE] Step: {step.step_name}, success={step.success}, has_data={bool(step.data)}")

        if not workflow_result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Profile building failed: {', '.join(workflow_result.errors)}"
            )

        # Extract profile data from workflow result
        profile_data = workflow_result.profile

        # Convert steps_completed list to dictionary for easier lookup
        steps_dict = {step.step_name.lower().replace(' ', '_'): step
                     for step in workflow_result.steps_completed}

        # Calculate quality score
        quality_score = profile_scorer.calculate_profile_quality(
            bmf_data=steps_dict.get('bmf_discovery', StepResult('', False)).data,
            form_990=steps_dict.get('form_990_query', StepResult('', False)).data,
            tool25_data=steps_dict.get('tool_25_web_intelligence', StepResult('', False)).data,
            tool2_data=steps_dict.get('tool_2_ai_analysis', StepResult('', False)).data
        )

        # Calculate completeness
        completeness = completeness_validator.validate_profile_completeness(
            bmf_data=steps_dict.get('bmf_discovery', StepResult('', False)).data,
            form_990=steps_dict.get('form_990_query', StepResult('', False)).data,
            tool25_data=steps_dict.get('tool_25_web_intelligence', StepResult('', False)).data,
            tool2_data=steps_dict.get('tool_2_ai_analysis', StepResult('', False)).data
        )

        # Save UnifiedProfile to database
        try:
            if isinstance(profile_data, UnifiedProfile):
                logger.info(f"[BUILD_PROFILE] Profile has web_enhanced_data: {bool(profile_data.web_enhanced_data)}")
                if profile_data.web_enhanced_data:
                    logger.info(f"[BUILD_PROFILE] web_enhanced_data keys: {list(profile_data.web_enhanced_data.keys())}")

                profile_service.create_profile(profile_data)
                logger.info(f"[BUILD_PROFILE] Profile saved to database for EIN {ein_clean}")
                # Convert to dict for JSON response
                profile_dict = profile_data.dict()
            else:
                logger.error(f"[BUILD_PROFILE] Profile data is not UnifiedProfile instance: {type(profile_data)}")
                profile_dict = profile_data if isinstance(profile_data, dict) else {}
        except Exception as save_error:
            logger.error(f"[BUILD_PROFILE] Failed to save profile to database for EIN {ein_clean}: {save_error}", exc_info=True)
            # Continue anyway - return the data even if save fails
            profile_dict = profile_data.dict() if hasattr(profile_data, 'dict') else {}

        # Add 'name' field for backward compatibility
        if isinstance(profile_dict, dict) and 'organization_name' in profile_dict:
            profile_dict['name'] = profile_dict['organization_name']

        return {
            "success": True,
            "profile": profile_dict,
            "workflow_result": {
                "success": workflow_result.success,
                "steps_completed": [step.step_name for step in workflow_result.steps_completed],
                "total_cost": workflow_result.total_cost_dollars,
                "total_duration": workflow_result.total_duration_seconds,
                "quality_score": workflow_result.final_quality_score,
                "errors": workflow_result.errors
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


@router.post("/enhance")
async def enhance_profile(request: Dict[str, Any]):
    """
    Enhance an existing profile with web intelligence and AI analysis.

    Alias for /build endpoint for backward compatibility with tests.

    Request:
    {
        "ein": "123456789",
        "enhancement_level": "basic"  # or "complete"
    }
    """
    # Map enhancement_level to tool flags
    enhancement_level = request.get('enhancement_level', 'basic')
    enable_tool25 = enhancement_level in ['basic', 'complete']
    enable_tool2 = enhancement_level == 'complete'

    # Call build endpoint with appropriate flags
    build_request = {
        'ein': request.get('ein'),
        'enable_tool25': enable_tool25,
        'enable_tool2': enable_tool2,
        'quality_threshold': request.get('quality_threshold', 0.70)
    }

    return await build_profile_with_orchestration(build_request)


@router.post("/orchestrate")
async def orchestrate_profile_workflow(request: Dict[str, Any]):
    """
    Execute orchestrated profile building workflow.

    Alias for /build endpoint for backward compatibility with tests.

    Request:
    {
        "ein": "123456789",
        "workflow": "comprehensive",  # or "basic"
        "steps": ["fetch_990", "analyze_financial", "assess_risk"]  # optional
    }
    """
    # Map workflow type to tool flags
    workflow = request.get('workflow', 'basic')
    enable_tool25 = workflow in ['basic', 'comprehensive']
    enable_tool2 = workflow == 'comprehensive'

    # Call build endpoint
    build_request = {
        'ein': request.get('ein'),
        'enable_tool25': enable_tool25,
        'enable_tool2': enable_tool2,
        'quality_threshold': request.get('quality_threshold', 0.70)
    }

    return await build_profile_with_orchestration(build_request)


async def _get_quality_internal(profile_id: str):
    """Internal function to get quality assessment - shared by both endpoints."""
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
        return await _get_quality_internal(profile_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profile_id}/quality-score")
async def get_profile_quality_score(profile_id: str):
    """
    Get quality assessment for an existing profile.

    Alias for /quality endpoint for backward compatibility with tests.

    Returns:
    {
        "quality_score": {...},
        "completeness": {...},
        "recommendations": [...]
    }
    """
    try:
        return await _get_quality_internal(profile_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality-score for profile {profile_id}: {e}")
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

        # Normalize EIN: Remove dashes for consistency
        ein_raw = request.get('ein', '').strip()
        ein_normalized = ein_raw.replace('-', '') if ein_raw else None

        logger.info(f"[CREATE_PROFILE] Creating profile for {name}, EIN: {ein_raw} → {ein_normalized}")

        # Generate unique profile_id
        import uuid
        profile_id = f"profile_{uuid.uuid4().hex[:12]}"

        # Create UnifiedProfile
        profile = UnifiedProfile(
            profile_id=profile_id,
            organization_name=name,
            ein=ein_normalized,  # Store normalized EIN
            ntee_codes=request.get('ntee_codes', []),
            geographic_scope=request.get('geographic_scope', {}),
            mission_statement=request.get('mission_statement'),
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

        # Convert to dict and add 'name' field for backward compatibility
        profile_dict = profile.__dict__ if hasattr(profile, '__dict__') else profile
        if isinstance(profile_dict, dict) and 'organization_name' in profile_dict:
            profile_dict['name'] = profile_dict['organization_name']

        return {
            "success": True,
            "profile": profile_dict
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

        # Normalize EIN if being updated
        if 'ein' in updates and updates['ein']:
            ein_raw = str(updates['ein']).strip()
            ein_normalized = ein_raw.replace('-', '')
            updates['ein'] = ein_normalized
            logger.info(f"[UPDATE_PROFILE] Normalizing EIN: {ein_raw} → {ein_normalized}")

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
async def discover_nonprofit_opportunities(profile_id: str, request: DiscoveryRequest):
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

        # Scoring parameters (now validated by Pydantic)
        min_score_threshold = request.min_score_threshold  # Validated 0.0-1.0
        max_return_limit = request.max_return_limit  # Validated 1-10000
        auto_scrapy_count = request.auto_scrapy_count  # Validated 0-100
        max_results = request.max_results  # Validated 1-10000

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
        failed_saves = []
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
                    scored_at=datetime.now(timezone.utc),
                    scorer_version='multi_dimensional_v1.0',
                    analysis_discovery={
                        'dimensional_scores': opp_data.get('dimensional_scores', {}),
                        'category_level': opp_data.get('category_level'),
                        '990_data': opp_data.get('990_data'),
                        'grant_history': opp_data.get('grant_history'),
                        'location': opp_data.get('location')
                    },
                    source='nonprofit',  # Discovery source
                    discovery_date=datetime.now(timezone.utc),
                    processing_status='discovered',
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )

                # Save to database
                success = database_manager.create_opportunity(opportunity)
                if success:
                    saved_count += 1
                    # Add ID to response for frontend reference
                    opp_data['opportunity_id'] = opportunity_id
                else:
                    failed_saves.append({
                        'organization': opp_data.get('organization_name'),
                        'ein': opp_data.get('ein'),
                        'reason': 'Database save failed'
                    })
                    logger.warning(f"Failed to save opportunity {opportunity_id}")

            except Exception as e:
                failed_saves.append({
                    'organization': opp_data.get('organization_name'),
                    'ein': opp_data.get('ein'),
                    'reason': str(e)
                })
                logger.error(f"Error saving opportunity {opp_data.get('organization_name')}: {e}", exc_info=True)

        logger.info(f"Saved {saved_count}/{len(opportunities)} opportunities to database")
        summary['saved_to_database'] = saved_count
        summary['failed_saves'] = failed_saves
        summary['save_success_rate'] = f"{saved_count}/{len(opportunities)} ({(saved_count/len(opportunities)*100):.1f}%)" if opportunities else "0/0"

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
                "compatibility_score": opp_raw.get('overall_score', 0.0),  # Frontend alias for overall_score
                "confidence": "high" if opp_raw.get('confidence_level', 0) >= 0.75 else "medium",
                "category_level": category_level,
                "dimensional_scores": discovery_data.get('dimensional_scores', {}),
                "990_data": discovery_data.get('990_data'),
                "grant_history": discovery_data.get('grant_history'),
                "current_stage": opp_raw.get('current_stage'),
                "funnel_stage": opp_raw.get('current_stage'),  # Frontend alias for current_stage
                "source_type": opp_raw.get('source', 'nonprofit'),  # Map source to source_type with default
                "discovery_source": opp_raw.get('source', 'nonprofit'),  # Frontend alias for source
                "discovery_date": opp_raw.get('discovery_date'),
                "discovered_at": opp_raw.get('discovery_date')  # Frontend alias for discovery_date
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
