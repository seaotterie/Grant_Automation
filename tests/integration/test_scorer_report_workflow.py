"""
Integration test: Multi-Dimensional Scorer → Report Generator pipeline

Verifies that the output of the scorer can be fed directly into the report
generator, simulating the real workflow a user would follow.
"""

import pytest
import sys
from pathlib import Path

# Add tool directories to path so imports work without installation
project_root = Path(__file__).parent.parent.parent
for tool_dir in [
    project_root / "tools" / "multi_dimensional_scorer_tool",
    project_root / "tools" / "report_generator_tool",
]:
    sys.path.insert(0, str(tool_dir))

from app.scorer_tool import score_opportunity
from app.report_tool import generate_report


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def opportunity():
    return {
        "title": "Community STEM Education Grant",
        "funder_name": "National Science Foundation",
        "funding_amount": 350_000,
        "description": "Supporting STEM education in underserved communities",
        "application_deadline": "2026-09-30",
        "focus_areas": ["education", "STEM", "youth"],
        "geographic_scope": "National",
        "eligibility_types": ["Nonprofit 501(c)(3)"],
        "agency_code": "NSF",
    }


@pytest.fixture
def organization():
    return {
        "organization_name": "STEM Access Nonprofit",
        "ein": "55-1234567",
        "mission": "Advancing STEM education equity",
        "ntee_codes": ["B25"],
        "revenue": 1_800_000,
        "assets": 2_200_000,
        "state": "VA",
        "years_active": 8,
        "focus_areas": ["education", "STEM", "youth"],
        "staff_count": 18,
    }


# ---------------------------------------------------------------------------
# Pipeline test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.integration
async def test_scorer_output_feeds_report(opportunity, organization, tmp_path):
    """Score an opportunity then generate a report using those scores."""

    # Step 1: Score the opportunity at PLAN stage
    score_result = await score_opportunity(
        opportunity_data=opportunity,
        organization_profile=organization,
        workflow_stage="plan",
        enhanced_data={"has_financial_data": True, "has_network_data": False,
                       "has_historical_data": False, "has_risk_data": False},
    )
    assert score_result.is_success(), f"Scoring failed: {score_result.errors}"

    score = score_result.data
    assert 0.0 <= score.overall_score <= 1.0

    # Step 2: Pass scorer output into report generator
    scoring_payload = [
        {
            "stage": score.stage,
            "overall_score": score.overall_score,
            "confidence": score.confidence,
            "dimensional_scores": [
                {"dimension": ds.dimension, "score": ds.score, "weight": ds.weight}
                for ds in score.dimensional_scores
            ],
            "boost_factors_applied": score.boost_factors_applied,
        }
    ]

    report_result = await generate_report(
        template_type="executive",
        opportunity_data=opportunity,
        organization_data=organization,
        scoring_results=scoring_payload,
        output_format="html",
        config={"output_dir": str(tmp_path)},
    )
    assert report_result.is_success(), f"Report generation failed: {report_result.errors}"

    report = report_result.data
    assert report.report_id
    assert len(report.sections_generated) > 0
    assert Path(report.file_path).exists()

    # The report content should reference the organization
    all_content = " ".join(s.content for s in report.sections_generated)
    assert "STEM Access Nonprofit" in all_content


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multi_stage_scoring_then_comprehensive_report(opportunity, organization, tmp_path):
    """Score at multiple stages then produce a comprehensive report."""
    stages = ["discover", "plan", "analyze"]
    all_scores = []

    for stage in stages:
        result = await score_opportunity(
            opportunity_data=opportunity,
            organization_profile=organization,
            workflow_stage=stage,
        )
        assert result.is_success(), f"Scoring failed at stage {stage}"
        s = result.data
        all_scores.append({
            "stage": s.stage,
            "overall_score": s.overall_score,
            "confidence": s.confidence,
        })

    # Scores should be valid across all stages
    assert all(0.0 <= s["overall_score"] <= 1.0 for s in all_scores)

    # Generate comprehensive report with all stage scores
    report_result = await generate_report(
        template_type="comprehensive",
        opportunity_data=opportunity,
        organization_data=organization,
        scoring_results=all_scores,
        config={"output_dir": str(tmp_path)},
    )
    assert report_result.is_success()
    assert len(report_result.data.sections_generated) >= 3
