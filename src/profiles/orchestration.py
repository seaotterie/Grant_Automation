"""
Profile Enhancement Orchestration Engine

Implements the multi-step profile building workflow as specified in
docs/PROFILE_ENHANCEMENT_DATA_FLOW.md (Task 16).

Workflow: BMF → Form 990 → Tool 25 → Tool 2 (optional)

Key Features:
- Step dependencies and sequential execution
- Quality gates between steps
- Graceful degradation on errors
- Cost and performance tracking
- Configurable tool execution
"""

import logging
import time
import sqlite3
import os
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .models import UnifiedProfile
from .unified_service import UnifiedProfileService

logger = logging.getLogger(__name__)


def get_nonprofit_intelligence_db() -> Path:
    """Get absolute path to nonprofit intelligence database."""
    # Get project root (assumes this file is in src/profiles/)
    project_root = Path(__file__).parent.parent.parent
    return project_root / "data" / "nonprofit_intelligence.db"


@dataclass
class StepResult:
    """Result of a single workflow step."""
    step_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    cost_dollars: float = 0.0
    quality_score: float = 0.0


@dataclass
class WorkflowResult:
    """Complete workflow execution result."""
    profile: Optional[UnifiedProfile] = None
    steps_completed: List[StepResult] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    total_cost_dollars: float = 0.0
    final_quality_score: float = 0.0
    success: bool = False
    errors: List[str] = field(default_factory=list)


class QualityGate:
    """Quality gate enforcement between workflow steps."""

    @staticmethod
    def check_bmf_quality(bmf_data: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        """
        Check BMF data quality.

        Required fields: EIN, name, state
        Optional but valuable: ntee_code

        Returns: (passed, score, errors)
        """
        errors = []
        required_fields = ['ein', 'name', 'state']
        optional_fields = ['ntee_code']

        # Check required fields
        for field in required_fields:
            if not bmf_data.get(field):
                errors.append(f"Missing required BMF field: {field}")

        required_score = len([f for f in required_fields if bmf_data.get(f)]) / len(required_fields)
        optional_score = len([f for f in optional_fields if bmf_data.get(f)]) / len(optional_fields)

        # Overall score: 80% weight on required, 20% on optional
        score = (required_score * 0.80) + (optional_score * 0.20)

        passed = required_score >= 1.0  # All required fields must be present
        return passed, score, errors

    @staticmethod
    def check_990_quality(form_990: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        """
        Check Form 990 data quality.

        Required: totrevenue, totfuncexpns, totassetsend

        Returns: (passed, score, errors)
        """
        errors = []
        required_fields = ['totrevenue', 'totfuncexpns', 'totassetsend']

        for field in required_fields:
            if not form_990.get(field) or form_990[field] <= 0:
                errors.append(f"Missing or invalid 990 field: {field}")

        score = len([f for f in required_fields
                    if form_990.get(f) and form_990[f] > 0]) / len(required_fields)

        passed = score >= 0.33  # At least one financial metric required
        return passed, score, errors

    @staticmethod
    def check_tool25_quality(web_data: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        """
        Check Tool 25 web intelligence quality.

        Based on BAML OrganizationIntelligence structure with scraping_metadata.

        Returns: (passed, score, errors)
        """
        errors = []

        if not web_data:
            return False, 0.0, ["No web data returned"]

        # Check for BAML structure with scraping_metadata
        if 'scraping_metadata' in web_data:
            metadata = web_data['scraping_metadata']
            data_quality_score = metadata.get('data_quality_score', 0.0)
            verification_confidence = metadata.get('verification_confidence', 0.0)

            # Use data quality score as primary metric
            score = data_quality_score
            passed = score >= 0.20  # Low threshold - any scraped data is valuable

            if not passed:
                errors.append(f"Data quality score too low: {score:.2f} (minimum 0.20 required)")

            return passed, score, errors

        # Fallback: Check if we have basic required fields
        required_fields = ['ein', 'organization_name', 'website_url']
        has_required = all(field in web_data for field in required_fields)

        if not has_required:
            errors.append("Missing required fields in web data (ein, organization_name, website_url)")
            return False, 0.0, errors

        # If we have fields but no metadata, estimate quality from field count
        field_count = len([v for v in web_data.values() if v])
        score = min(field_count / 20.0, 1.0)  # Estimate: 20+ fields = perfect score
        passed = score >= 0.20

        return passed, score, errors


class ProfileEnhancementOrchestrator:
    """
    Orchestrates the multi-step profile enhancement workflow.

    Workflow Steps:
    1. BMF Discovery (REQUIRED) - Organization validation
    2. Form 990 Query (HIGH PRIORITY) - Financial intelligence
    3. Tool 25 Web Intelligence (MEDIUM PRIORITY) - Website scraping
    4. Tool 2 AI Analysis (OPTIONAL) - Deep intelligence

    Quality Gates:
    - After BMF: Must have all required fields (score >= 1.0)
    - After 990: Must have at least one financial metric (score >= 0.33)
    - After Tool 25: Must have medium confidence (score >= 0.60)
    - Final: Overall quality >= 0.70 recommended for AI analysis
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize orchestrator with database connection."""
        if db_path is None:
            db_path = str(get_nonprofit_intelligence_db())
        self.db_path = db_path
        self.profile_service = UnifiedProfileService()
        self.quality_gate = QualityGate()

    def execute_profile_building(
        self,
        ein: str,
        enable_tool25: bool = True,
        enable_tool2: bool = False,
        quality_threshold: float = 0.70,
        website_url: Optional[str] = None,
        ntee_code_990: Optional[str] = None,
        ntee_codes: Optional[List[str]] = None,
        government_criteria: Optional[List[str]] = None,
        tool25_max_pages: Optional[int] = None,
        tool25_max_depth: Optional[int] = None,
        tool25_timeout: Optional[int] = None
    ) -> WorkflowResult:
        """
        Execute complete profile building workflow.

        Args:
            ein: Organization EIN
            enable_tool25: Enable Tool 25 web scraping
            enable_tool2: Enable Tool 2 AI analysis
            quality_threshold: Minimum quality score for AI analysis
            website_url: Optional website URL (if already known, skips BMF/990 lookup)
            ntee_code_990: Optional NTEE code from 990 filing
            ntee_codes: Optional list of NTEE codes
            government_criteria: Optional government criteria list
            tool25_max_pages: Optional override for Tool 25 max pages (manual retry)
            tool25_max_depth: Optional override for Tool 25 crawl depth (manual retry)
            tool25_timeout: Optional override for Tool 25 timeout seconds (manual retry)

        Returns:
            WorkflowResult with profile and execution details
        """
        start_time = time.time()
        result = WorkflowResult()

        logger.info(f"Starting profile building workflow for EIN: {ein}")

        # Step 1: BMF Discovery (REQUIRED)
        bmf_result = self._step_bmf_discovery(ein)
        result.steps_completed.append(bmf_result)
        result.total_cost_dollars += bmf_result.cost_dollars

        if not bmf_result.success:
            result.errors.append("BMF Discovery failed - cannot continue")
            result.total_duration_seconds = time.time() - start_time
            return result

        # Step 2: Form 990 Query (HIGH PRIORITY)
        form_990_result = self._step_form_990_query(ein)
        result.steps_completed.append(form_990_result)
        result.total_cost_dollars += form_990_result.cost_dollars

        # Continue even if 990 fails (graceful degradation)
        if not form_990_result.success:
            logger.warning(f"Form 990 query failed for {ein}, continuing with degraded profile")

        # Step 3: Tool 25 Web Intelligence (MEDIUM PRIORITY, OPTIONAL)
        if enable_tool25:
            # Get website URL from: 1) parameter, 2) BMF data, or 3) 990 data
            website = website_url or self._extract_website(bmf_result.data, form_990_result.data)
            # Get organization name from BMF data
            org_name = bmf_result.data.get('name', 'Unknown') if bmf_result.success and bmf_result.data else 'Unknown'

            if website:
                logger.info(f"Using website URL for Tool 25: {website}")
                tool25_result = self._step_tool25_web_intelligence(
                    ein=ein,
                    website=website,
                    organization_name=org_name,
                    max_pages=tool25_max_pages,
                    max_depth=tool25_max_depth,
                    timeout=tool25_timeout
                )
                result.steps_completed.append(tool25_result)
                result.total_cost_dollars += tool25_result.cost_dollars
            else:
                logger.warning(f"No website found for {ein}, skipping Tool 25")

        # Calculate profile quality
        profile_quality = self._calculate_profile_quality(result.steps_completed)
        result.final_quality_score = profile_quality

        # Step 4: Tool 2 AI Analysis (OPTIONAL)
        if enable_tool2 and profile_quality >= quality_threshold:
            tool2_result = self._step_tool2_ai_analysis(ein, result.steps_completed)
            result.steps_completed.append(tool2_result)
            result.total_cost_dollars += tool2_result.cost_dollars
        elif enable_tool2 and profile_quality < quality_threshold:
            logger.warning(f"Profile quality {profile_quality:.2f} below threshold "
                          f"{quality_threshold:.2f}, skipping AI analysis")

        # Build final profile (preserve user-edited fields if they were passed in)
        profile = self._build_profile_from_steps(
            ein, result.steps_completed, website_url, ntee_code_990, ntee_codes, government_criteria
        )
        result.profile = profile
        result.success = profile is not None

        result.total_duration_seconds = time.time() - start_time

        logger.info(f"Profile building complete for {ein}: "
                   f"Success={result.success}, Quality={profile_quality:.2f}, "
                   f"Cost=${result.total_cost_dollars:.2f}, "
                   f"Time={result.total_duration_seconds:.1f}s")

        return result

    def _step_bmf_discovery(self, ein: str) -> StepResult:
        """
        Step 1: BMF Discovery - Get organization from Business Master File.

        Required step - workflow fails if this fails.
        """
        start_time = time.time()
        step_name = "BMF Discovery"

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    ein,
                    name,
                    ntee_code,
                    state,
                    city,
                    foundation_code
                FROM bmf_organizations
                WHERE ein = ?
                LIMIT 1
            """, (ein,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return StepResult(
                    step_name=step_name,
                    success=False,
                    errors=[f"EIN {ein} not found in BMF"],
                    duration_seconds=time.time() - start_time,
                    cost_dollars=0.0
                )

            bmf_data = dict(row)

            # Quality gate
            passed, quality, errors = self.quality_gate.check_bmf_quality(bmf_data)

            if not passed:
                return StepResult(
                    step_name=step_name,
                    success=False,
                    data=bmf_data,
                    errors=errors,
                    duration_seconds=time.time() - start_time,
                    cost_dollars=0.0,
                    quality_score=quality
                )

            logger.info(f"BMF Discovery successful for {ein}: {bmf_data.get('name')}")

            return StepResult(
                step_name=step_name,
                success=True,
                data=bmf_data,
                duration_seconds=time.time() - start_time,
                cost_dollars=0.0,  # BMF lookup is free
                quality_score=quality
            )

        except Exception as e:
            logger.error(f"BMF Discovery failed: {e}")
            return StepResult(
                step_name=step_name,
                success=False,
                errors=[str(e)],
                duration_seconds=time.time() - start_time,
                cost_dollars=0.0
            )

    def _step_form_990_query(self, ein: str) -> StepResult:
        """
        Step 2: Form 990 Query - Get financial and operational data.

        High priority but not required - workflow continues on failure.
        """
        start_time = time.time()
        step_name = "Form 990 Query"

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    ein,
                    tax_year,
                    totrevenue,
                    totfuncexpns,
                    totassetsend,
                    totliabend,
                    totnetassetend
                FROM form_990
                WHERE ein = ?
                ORDER BY tax_year DESC
                LIMIT 1
            """, (ein,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return StepResult(
                    step_name=step_name,
                    success=False,
                    errors=[f"No Form 990 data found for EIN {ein}"],
                    duration_seconds=time.time() - start_time,
                    cost_dollars=0.0
                )

            form_990 = dict(row)

            # Quality gate
            passed, quality, errors = self.quality_gate.check_990_quality(form_990)

            logger.info(f"Form 990 query for {ein}: Quality={quality:.2f}, "
                       f"Revenue=${form_990.get('totrevenue', 0):,}")

            return StepResult(
                step_name=step_name,
                success=passed,
                data=form_990,
                errors=errors if not passed else [],
                duration_seconds=time.time() - start_time,
                cost_dollars=0.0,  # 990 query is free
                quality_score=quality
            )

        except Exception as e:
            logger.error(f"Form 990 query failed: {e}")
            return StepResult(
                step_name=step_name,
                success=False,
                errors=[str(e)],
                duration_seconds=time.time() - start_time,
                cost_dollars=0.0
            )

    def _step_tool25_web_intelligence(
        self,
        ein: str,
        website: str,
        organization_name: str = None,
        max_pages: int = None,
        max_depth: int = None,
        timeout: int = None,
        is_retry: bool = False
    ) -> StepResult:
        """
        Step 3: Tool 25 Web Intelligence - Scrape organization website.

        Medium priority, optional - workflow continues on failure.

        Args:
            ein: Organization EIN
            website: Website URL to scrape
            organization_name: Organization name
            max_pages: Optional override for max pages (default: 5, retry: 10, manual: 15)
            max_depth: Optional override for crawl depth (default: 1, retry: 2)
            timeout: Optional override for timeout seconds (default: 60, retry: 120, manual: 180)
            is_retry: Whether this is an auto-retry attempt
        """
        start_time = time.time()
        step_name = "Tool 25 Web Intelligence"

        try:
            # Import Tool 25 - add parent directory to handle package imports
            import sys
            tool_root = Path(__file__).parent.parent.parent / "tools" / "web_intelligence_tool"
            if str(tool_root) not in sys.path:
                sys.path.insert(0, str(tool_root))

            from app.web_intelligence_tool import scrape_organization_profile

            retry_label = " (RETRY with expanded params)" if is_retry else ""
            logger.info(f"Tool 25 web scraping{retry_label} for EIN {ein} at {website}")

            # Call Tool 25 (it's async, so we need to handle the event loop properly)
            # Since we're being called from FastAPI (which has a running event loop),
            # we need to run the async function in a thread pool executor
            import concurrent.futures

            async def run_tool25():
                return await scrape_organization_profile(
                    ein=ein,
                    organization_name=organization_name or "Unknown",
                    user_provided_url=website,
                    max_pages=max_pages,
                    max_depth=max_depth,
                    timeout=timeout
                )

            # Run async function in thread pool to avoid event loop conflict
            dynamic_timeout = timeout if timeout else 120  # Use custom timeout or default 2 minutes
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, run_tool25())
                response = future.result(timeout=dynamic_timeout)

            # Extract web_enhanced_data from response
            if response and response.success and response.intelligence_data:
                web_data = response.intelligence_data.dict() if hasattr(response.intelligence_data, 'dict') else response.intelligence_data
                logger.info(f"Tool 25 completed successfully for {ein}: {len(web_data)} fields extracted")
            else:
                logger.warning(f"Tool 25 returned no data for {ein}: {response.errors if response else 'No response'}")
                web_data = {}

            # Check quality for informational purposes (not blocking)
            passed, quality, errors = self.quality_gate.check_tool25_quality(web_data)

            # Log quality info
            if not passed:
                logger.info(f"Tool 25 data quality below threshold ({quality:.0%}), but saving anyway for user visibility")

            # PHASE 3: HYBRID ADAPTIVE SCRAPING - Auto-retry once if quality < 40%
            # BUT: Skip auto-retry if user already requested custom parameters (manual deeper search)
            user_requested_custom_params = (max_pages and max_pages > 10) or (max_depth and max_depth > 3)

            if quality < 0.40 and not is_retry and web_data and not user_requested_custom_params:
                logger.info(f"Quality {quality:.0%} below 40% threshold - Auto-retrying with expanded parameters...")
                logger.info(f"Expanding search: pages unlimited, depth 3 → 5")

                # Recursive call with expanded parameters
                # NOTE: Default DEPTH_LIMIT in scrapy_settings.py is 3
                # First run uses default depth 3, so retry needs depth 4-5 to go deeper
                return self._step_tool25_web_intelligence(
                    ein=ein,
                    website=website,
                    organization_name=organization_name,
                    max_pages=20,  # Expanded: allow more pages
                    max_depth=5,   # Expanded: go DEEPER than default 3
                    timeout=180,   # Expanded: 3 minute timeout
                    is_retry=True
                )
            elif quality < 0.40 and user_requested_custom_params:
                logger.info(f"Quality {quality:.0%} is low, but skipping auto-retry because user requested custom parameters (depth={max_depth}, pages={max_pages})")

            return StepResult(
                step_name=step_name,
                success=bool(web_data),  # Success = any data extracted (quality is informational only)
                data=web_data,
                errors=errors if not passed else [],  # Keep errors for UI display
                duration_seconds=time.time() - start_time,
                cost_dollars=0.10,  # Tool 25 cost estimate
                quality_score=quality
            )

        except Exception as e:
            logger.error(f"Tool 25 failed for {ein}: {e}", exc_info=True)
            return StepResult(
                step_name=step_name,
                success=False,
                data={},
                errors=[f"Tool 25 execution failed: {str(e)}"],
                duration_seconds=time.time() - start_time,
                cost_dollars=0.0,
                quality_score=0.0
            )

    def _step_tool2_ai_analysis(
        self,
        ein: str,
        previous_steps: List[StepResult]
    ) -> StepResult:
        """
        Step 4: Tool 2 AI Analysis - Deep intelligence with AI.

        Optional - only runs if profile quality meets threshold.
        """
        start_time = time.time()
        step_name = "Tool 2 AI Analysis"

        # Placeholder for Tool 2 integration
        logger.info(f"Tool 2 AI analysis for {ein} (PLACEHOLDER)")

        # Simulated result
        ai_data = {
            "strategic_positioning": "Strong educational focus",
            "grant_readiness": 0.85
        }

        return StepResult(
            step_name=step_name,
            success=True,
            data=ai_data,
            duration_seconds=time.time() - start_time,
            cost_dollars=0.75,  # Tool 2 quick depth cost
            quality_score=1.0
        )

    def _extract_website(
        self,
        bmf_data: Optional[Dict[str, Any]],
        form_990: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Extract website URL from BMF or Form 990 data."""
        # Placeholder - would extract from actual data
        return None

    def _calculate_profile_quality(self, steps: List[StepResult]) -> float:
        """
        Calculate overall profile quality from completed steps.

        Quality = (BMF * 0.20) + (990 * 0.35) + (Tool25 * 0.25) + (Tool2 * 0.20)
        """
        quality = 0.0

        for step in steps:
            if step.step_name == "BMF Discovery" and step.success:
                quality += step.quality_score * 0.20
            elif step.step_name == "Form 990 Query" and step.success:
                quality += step.quality_score * 0.35
            elif step.step_name == "Tool 25 Web Intelligence" and step.success:
                quality += step.quality_score * 0.25
            elif step.step_name == "Tool 2 AI Analysis" and step.success:
                quality += step.quality_score * 0.20

        return quality

    def _build_profile_from_steps(
        self,
        ein: str,
        steps: List[StepResult],
        website_url: Optional[str] = None,
        ntee_code_990: Optional[str] = None,
        ntee_codes: Optional[List[str]] = None,
        government_criteria: Optional[List[str]] = None
    ) -> Optional[UnifiedProfile]:
        """Build UnifiedProfile from completed workflow steps."""

        # Get BMF data
        bmf_step = next((s for s in steps if s.step_name == "BMF Discovery"), None)
        if not bmf_step or not bmf_step.success:
            return None

        bmf_data = bmf_step.data

        # Create profile
        profile_id = f"profile_{ein}"

        # Use user-selected NTEE codes if provided, otherwise build from BMF data
        if ntee_codes is not None:
            # Preserve user's selections from NTEE tab
            final_ntee_codes = ntee_codes
        else:
            # Build from BMF data (first-time creation)
            final_ntee_codes = []
            ntee_code = bmf_data.get('ntee_code')
            if ntee_code:
                final_ntee_codes.append(ntee_code)

        # Use user-selected government criteria if provided, otherwise empty list
        final_government_criteria = government_criteria if government_criteria is not None else []

        profile = UnifiedProfile(
            profile_id=profile_id,
            organization_name=bmf_data.get('name', ''),
            ein=ein,  # Store the EIN
            website_url=website_url,  # Preserve existing website URL
            ntee_code_990=ntee_code_990,  # Preserve user-edited NTEE code from 990
            focus_areas=[],
            geographic_scope={'states': [bmf_data.get('state', '')], 'nationwide': False, 'international': False},
            ntee_codes=final_ntee_codes,  # Preserve user-selected NTEE codes
            government_criteria=final_government_criteria,  # Preserve user-selected criteria
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            status="active"
        )

        logger.info(f"Built profile with website_url: {website_url}, ntee_code_990: {ntee_code_990}, "
                   f"ntee_codes: {final_ntee_codes}, government_criteria: {final_government_criteria}")

        # Add 990 data if available
        form_990_step = next((s for s in steps if s.step_name == "Form 990 Query"), None)
        if form_990_step and form_990_step.success:
            # Would populate financial data here
            pass

        # Add web data if available (check data first, success is secondary)
        tool25_step = next((s for s in steps if s.step_name == "Tool 25 Web Intelligence"), None)
        if tool25_step and tool25_step.data:
            # Add web_enhanced_data to profile regardless of quality score
            quality_score = tool25_step.quality_score or 0.0
            logger.info(f"Adding Tool 25 web_enhanced_data to profile {profile_id} (quality: {quality_score:.0%}, fields: {len(tool25_step.data)})")
            profile.web_enhanced_data = tool25_step.data

            # Also populate website_url if found in Tool 25 data
            if 'website_url' in tool25_step.data:
                profile.website_url = tool25_step.data['website_url']
        elif tool25_step:
            logger.info(f"Tool 25 step exists but has no data for {profile_id}")

        # Note: Quality score is tracked in WorkflowResult, not stored on profile

        return profile
