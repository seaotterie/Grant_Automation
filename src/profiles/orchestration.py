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
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .models import UnifiedProfile
from .unified_service import UnifiedProfileService

logger = logging.getLogger(__name__)


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

        Based on confidence scores of extracted data.

        Returns: (passed, score, errors)
        """
        errors = []

        if not web_data:
            return False, 0.0, ["No web data returned"]

        # Check for at least one high-confidence field
        confidence_scores = []

        for field, value in web_data.items():
            if isinstance(value, dict) and 'confidence' in value:
                confidence_scores.append(value['confidence'])

        if not confidence_scores:
            errors.append("No confidence scores in web data")
            return False, 0.0, errors

        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        passed = avg_confidence >= 0.60  # Medium confidence required

        return passed, avg_confidence, errors


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

    def __init__(self, db_path: str = "data/nonprofit_intelligence.db"):
        """Initialize orchestrator with database connection."""
        self.db_path = db_path
        self.profile_service = UnifiedProfileService()
        self.quality_gate = QualityGate()

    def execute_profile_building(
        self,
        ein: str,
        enable_tool25: bool = True,
        enable_tool2: bool = False,
        quality_threshold: float = 0.70
    ) -> WorkflowResult:
        """
        Execute complete profile building workflow.

        Args:
            ein: Organization EIN
            enable_tool25: Enable Tool 25 web scraping
            enable_tool2: Enable Tool 2 AI analysis
            quality_threshold: Minimum quality score for AI analysis

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
            # Get website URL from BMF or 990 data
            website = self._extract_website(bmf_result.data, form_990_result.data)

            if website:
                tool25_result = self._step_tool25_web_intelligence(ein, website)
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

        # Build final profile
        profile = self._build_profile_from_steps(ein, result.steps_completed)
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

    def _step_tool25_web_intelligence(self, ein: str, website: str) -> StepResult:
        """
        Step 3: Tool 25 Web Intelligence - Scrape organization website.

        Medium priority, optional - workflow continues on failure.
        """
        start_time = time.time()
        step_name = "Tool 25 Web Intelligence"

        # Placeholder for Tool 25 integration
        # In real implementation, would call Tool 25 Scrapy spider
        logger.info(f"Tool 25 web scraping for {ein} at {website} (PLACEHOLDER)")

        # Simulated result for now
        web_data = {
            "mission_statement": {"text": "Sample mission", "confidence": 0.85},
            "contact_info": {"phone": "555-1234", "confidence": 0.90}
        }

        passed, quality, errors = self.quality_gate.check_tool25_quality(web_data)

        return StepResult(
            step_name=step_name,
            success=passed,
            data=web_data,
            errors=errors if not passed else [],
            duration_seconds=time.time() - start_time,
            cost_dollars=0.10,  # Tool 25 cost estimate
            quality_score=quality
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
        steps: List[StepResult]
    ) -> Optional[UnifiedProfile]:
        """Build UnifiedProfile from completed workflow steps."""

        # Get BMF data
        bmf_step = next((s for s in steps if s.step_name == "BMF Discovery"), None)
        if not bmf_step or not bmf_step.success:
            return None

        bmf_data = bmf_step.data

        # Create profile
        profile_id = f"profile_{ein}"

        # Build NTEE codes list (filter out None/empty values)
        ntee_codes = []
        ntee_code = bmf_data.get('ntee_code')
        if ntee_code:
            ntee_codes.append(ntee_code)

        profile = UnifiedProfile(
            profile_id=profile_id,
            organization_name=bmf_data.get('name', ''),
            focus_areas=[],
            geographic_scope={'states': [bmf_data.get('state', '')], 'nationwide': False, 'international': False},
            ntee_codes=ntee_codes,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            status="active"
        )

        # Add 990 data if available
        form_990_step = next((s for s in steps if s.step_name == "Form 990 Query"), None)
        if form_990_step and form_990_step.success:
            # Would populate financial data here
            pass

        # Add web data if available
        tool25_step = next((s for s in steps if s.step_name == "Tool 25 Web Intelligence"), None)
        if tool25_step and tool25_step.success:
            # Would populate web intelligence here
            pass

        # Note: Quality score is tracked in WorkflowResult, not stored on profile

        return profile
