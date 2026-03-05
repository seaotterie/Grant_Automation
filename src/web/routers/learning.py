"""
Learning Loop API Router
REST API endpoints for outcome tracking, scoring calibration, and missed opportunity analysis.

Phase F: Quality & Learning Loop
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from dataclasses import asdict
import logging
import os

router = APIRouter(prefix="/api/learning", tags=["learning"])
logger = logging.getLogger(__name__)


def _db_path() -> str:
    """Resolve the database path."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    return os.path.join(project_root, "data", "catalynx.db")


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class RecordOutcomeRequest(BaseModel):
    """Record an outcome for an opportunity."""
    profile_id: str = Field(..., description="Profile that owns this opportunity")
    award_status: str = Field(..., description="pending | awarded | rejected | withdrawn | not_pursued")
    award_amount: Optional[float] = Field(None, description="Actual award amount if awarded")
    award_date: Optional[str] = Field(None, description="Date of award (ISO format)")
    application_submitted: bool = Field(False, description="Whether an application was submitted")
    application_submitted_date: Optional[str] = Field(None, description="Date application was submitted")
    award_notification_source: Optional[str] = Field(None, description="How the outcome was learned")
    outcome_notes: Optional[str] = Field(None, description="Notes about the outcome")
    key_success_factors: Optional[List[str]] = Field(None, description="Factors that led to success")
    key_failure_factors: Optional[List[str]] = Field(None, description="Factors that led to failure")


class UpdateOutcomeRequest(BaseModel):
    """Update an existing outcome."""
    award_status: Optional[str] = None
    award_amount: Optional[float] = None
    award_date: Optional[str] = None
    outcome_notes: Optional[str] = None
    key_success_factors: Optional[List[str]] = None
    key_failure_factors: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Outcome Tracking Endpoints
# ---------------------------------------------------------------------------

@router.post("/outcomes/{opportunity_id}")
async def record_outcome(opportunity_id: str, request: RecordOutcomeRequest):
    """Record or update an outcome for an opportunity."""
    from src.learning.outcome_tracker import OutcomeTracker
    try:
        tracker = OutcomeTracker(_db_path())
        outcome = tracker.record_outcome(
            opportunity_id=opportunity_id,
            profile_id=request.profile_id,
            award_status=request.award_status,
            award_amount=request.award_amount,
            award_date=request.award_date,
            application_submitted=request.application_submitted,
            application_submitted_date=request.application_submitted_date,
            award_notification_source=request.award_notification_source,
            outcome_notes=request.outcome_notes,
            key_success_factors=request.key_success_factors,
            key_failure_factors=request.key_failure_factors,
        )
        return {"status": "ok", "outcome": asdict(outcome)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to record outcome: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outcomes/{opportunity_id}")
async def get_outcome(opportunity_id: str):
    """Get the outcome record for an opportunity."""
    from src.learning.outcome_tracker import OutcomeTracker
    tracker = OutcomeTracker(_db_path())
    outcome = tracker.get_outcome(opportunity_id)
    if not outcome:
        raise HTTPException(status_code=404, detail="No outcome recorded for this opportunity")
    return {"outcome": asdict(outcome)}


@router.get("/outcomes")
async def list_outcomes(
    profile_id: Optional[str] = Query(None, description="Filter by profile"),
    status: Optional[str] = Query(None, description="Filter by award status"),
):
    """List outcomes, optionally filtered by profile and/or status."""
    from src.learning.outcome_tracker import OutcomeTracker
    tracker = OutcomeTracker(_db_path())
    if profile_id:
        outcomes = tracker.get_outcomes_for_profile(profile_id, status_filter=status)
    else:
        outcomes = tracker.get_confirmed_outcomes()
    return {
        "count": len(outcomes),
        "outcomes": [asdict(o) for o in outcomes],
    }


@router.get("/outcomes/summary")
async def outcome_summary(
    profile_id: Optional[str] = Query(None, description="Filter by profile"),
):
    """Get summary statistics of all tracked outcomes."""
    from src.learning.outcome_tracker import OutcomeTracker
    tracker = OutcomeTracker(_db_path())
    return tracker.get_outcome_summary(profile_id)


# ---------------------------------------------------------------------------
# Scoring Calibration Endpoints
# ---------------------------------------------------------------------------

@router.get("/calibration")
async def get_calibration_report(
    profile_id: Optional[str] = Query(None, description="Filter by profile"),
):
    """
    Generate a scoring calibration report.

    Analyzes prediction accuracy by comparing screening scores to actual
    outcomes. Returns dimension-level analysis and weight adjustment
    recommendations.
    """
    from src.learning.calibration_engine import ScoringCalibrationEngine
    engine = ScoringCalibrationEngine(_db_path())
    report = engine.generate_calibration_report(profile_id)
    return _calibration_to_dict(report)


# ---------------------------------------------------------------------------
# Missed Opportunity Endpoints
# ---------------------------------------------------------------------------

@router.get("/missed-opportunities")
async def get_missed_opportunities(
    profile_id: Optional[str] = Query(None, description="Filter by profile"),
    min_score: Optional[float] = Query(None, description="Minimum screening score"),
    max_score: Optional[float] = Query(None, description="Maximum screening score"),
):
    """
    Generate a "what did we miss" report.

    Identifies opportunities we rejected or didn't pursue that were
    actually funded. Analyzes patterns and recommends adjustments.
    """
    from src.learning.missed_opportunity_analyzer import MissedOpportunityAnalyzer
    analyzer = MissedOpportunityAnalyzer(_db_path())

    score_range = None
    if min_score is not None or max_score is not None:
        score_range = (min_score or 0.0, max_score or 1.0)

    report = analyzer.generate_report(
        profile_id=profile_id,
        score_range=score_range,
    )
    return _missed_report_to_dict(report)


# ---------------------------------------------------------------------------
# Combined Dashboard Endpoint
# ---------------------------------------------------------------------------

@router.get("/dashboard")
async def learning_dashboard(
    profile_id: Optional[str] = Query(None, description="Filter by profile"),
):
    """
    Combined learning loop dashboard data.

    Returns outcome summary, calibration highlights, and missed opportunity
    count in a single call for the performance analytics UI.
    """
    from src.learning.outcome_tracker import OutcomeTracker
    from src.learning.calibration_engine import ScoringCalibrationEngine
    from src.learning.missed_opportunity_analyzer import MissedOpportunityAnalyzer

    db = _db_path()
    tracker = OutcomeTracker(db)
    engine = ScoringCalibrationEngine(db)
    analyzer = MissedOpportunityAnalyzer(db)

    summary = tracker.get_outcome_summary(profile_id)
    calibration = engine.generate_calibration_report(profile_id)
    missed = analyzer.generate_report(profile_id=profile_id)

    return {
        "outcomes": summary,
        "calibration": {
            "sample_count": calibration.sample_count,
            "mean_absolute_error": calibration.mean_absolute_error,
            "overall_accuracy": calibration.overall_accuracy,
            "optimal_threshold": calibration.optimal_threshold,
            "weight_adjustments": calibration.weight_adjustments,
            "summary": calibration.summary,
        },
        "missed_opportunities": {
            "total_rejected": missed.total_rejected,
            "tracked_rejections": missed.tracked_rejections,
            "actually_awarded": missed.actually_awarded,
            "miss_rate": missed.miss_rate,
            "total_missed_amount": missed.total_missed_amount,
            "recommendations": missed.recommendations,
        },
    }


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _calibration_to_dict(report) -> Dict[str, Any]:
    return {
        "profile_id": report.profile_id,
        "sample_count": report.sample_count,
        "awarded_count": report.awarded_count,
        "rejected_count": report.rejected_count,
        "mean_absolute_error": report.mean_absolute_error,
        "overall_accuracy": report.overall_accuracy,
        "optimal_threshold": report.optimal_threshold,
        "dimensions": [
            {
                "dimension": d.dimension,
                "sample_count": d.sample_count,
                "mean_score_awarded": d.mean_score_awarded,
                "mean_score_rejected": d.mean_score_rejected,
                "separation": d.separation,
                "bias": d.bias,
                "prediction_power": d.prediction_power,
                "recommendation": d.recommendation,
            }
            for d in report.dimensions
        ],
        "score_bins": report.score_bins,
        "weight_adjustments": report.weight_adjustments,
        "threshold_adjustment": report.threshold_adjustment,
        "summary": report.summary,
        "generated_at": report.generated_at,
    }


def _missed_report_to_dict(report) -> Dict[str, Any]:
    return {
        "profile_id": report.profile_id,
        "analysis_period": report.analysis_period,
        "total_rejected": report.total_rejected,
        "tracked_rejections": report.tracked_rejections,
        "actually_awarded": report.actually_awarded,
        "miss_rate": report.miss_rate,
        "total_missed_amount": report.total_missed_amount,
        "missed_opportunities": [
            {
                "opportunity_id": m.opportunity_id,
                "organization_name": m.organization_name,
                "screening_score": m.screening_score,
                "screening_dimensions": m.screening_dimensions,
                "gateway_decision": m.gateway_decision,
                "gateway_reason": m.gateway_reason,
                "award_status": m.award_status,
                "award_amount": m.award_amount,
                "award_date": m.award_date,
                "score_gap": m.score_gap,
                "weakest_dimension": m.weakest_dimension,
                "dimension_errors": m.dimension_errors,
            }
            for m in report.missed_opportunities
        ],
        "common_weak_dimensions": report.common_weak_dimensions,
        "threshold_analysis": report.threshold_analysis,
        "recommendations": report.recommendations,
        "generated_at": report.generated_at,
    }
