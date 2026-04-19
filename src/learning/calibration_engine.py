"""
Scoring Calibration Engine - Analyzes prediction accuracy and recommends weight adjustments.

Phase F component 2: Use historical outcomes to calibrate scoring weights.
Compares predicted scores against actual outcomes (awarded/rejected) to
identify which dimensions are strong/weak predictors.
"""

import json
import logging
import math
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

SCORING_DIMENSIONS = [
    "strategic_fit", "eligibility", "timing", "financial", "competition"
]


@dataclass
class DimensionCalibration:
    """Calibration metrics for a single scoring dimension."""
    dimension: str
    sample_count: int
    mean_score_awarded: Optional[float]   # Average score for awarded opps
    mean_score_rejected: Optional[float]   # Average score for rejected opps
    separation: Optional[float]            # How well this dim separates outcomes
    bias: Optional[float]                  # Positive = over-optimistic, negative = under-scoring
    prediction_power: Optional[float]      # 0-1, how well it correlates with outcomes
    current_weight: Optional[float] = None
    recommended_weight: Optional[float] = None
    recommendation: str = ""


@dataclass
class CalibrationReport:
    """Full calibration report across all dimensions."""
    profile_id: Optional[str]
    sample_count: int
    awarded_count: int
    rejected_count: int

    # Overall metrics
    mean_absolute_error: Optional[float]
    overall_accuracy: Optional[float]       # % of correct pass/reject at threshold
    optimal_threshold: Optional[float]

    # Dimension-level analysis
    dimensions: List[DimensionCalibration]

    # Score distribution
    score_bins: List[Dict[str, Any]]        # [{bin, awarded_count, rejected_count, success_rate}]

    # Recommendations
    weight_adjustments: Dict[str, float]    # {dimension: delta}
    threshold_adjustment: Optional[float]
    summary: str

    generated_at: str = ""


class ScoringCalibrationEngine:
    """
    Analyzes scoring accuracy by comparing predicted scores to actual outcomes.

    Uses the scoring_calibration_log and grant_outcomes tables to compute:
    - Overall prediction accuracy (MAE, threshold-based accuracy)
    - Dimension-level analysis (which dimensions predict success)
    - Weight adjustment recommendations
    - Optimal threshold suggestions
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def generate_calibration_report(
        self, profile_id: Optional[str] = None
    ) -> CalibrationReport:
        """Generate a full calibration report from confirmed outcomes."""
        outcomes = self._load_confirmed_outcomes(profile_id)

        if len(outcomes) < 3:
            return CalibrationReport(
                profile_id=profile_id,
                sample_count=len(outcomes),
                awarded_count=sum(1 for o in outcomes if o["award_status"] == "awarded"),
                rejected_count=sum(1 for o in outcomes if o["award_status"] == "rejected"),
                mean_absolute_error=None,
                overall_accuracy=None,
                optimal_threshold=None,
                dimensions=[],
                score_bins=[],
                weight_adjustments={},
                threshold_adjustment=None,
                summary=f"Insufficient data for calibration ({len(outcomes)} outcomes, need at least 3).",
                generated_at=datetime.now(timezone.utc).isoformat(),
            )

        awarded = [o for o in outcomes if o["award_status"] == "awarded"]
        rejected = [o for o in outcomes if o["award_status"] == "rejected"]

        # Overall prediction accuracy
        mae = self._compute_mae(outcomes)
        score_bins = self._compute_score_bins(outcomes)
        optimal_threshold = self._find_optimal_threshold(outcomes)
        accuracy = self._compute_accuracy(outcomes, optimal_threshold or 0.5)

        # Dimension-level calibration
        dimensions = self._calibrate_dimensions(outcomes)

        # Weight adjustment recommendations
        weight_adjustments = self._recommend_weight_adjustments(dimensions)
        current_threshold = 0.5  # Default screening threshold
        threshold_adjustment = (optimal_threshold - current_threshold) if optimal_threshold else None

        summary = self._generate_summary(
            len(outcomes), len(awarded), len(rejected),
            mae, accuracy, dimensions, weight_adjustments,
        )

        return CalibrationReport(
            profile_id=profile_id,
            sample_count=len(outcomes),
            awarded_count=len(awarded),
            rejected_count=len(rejected),
            mean_absolute_error=mae,
            overall_accuracy=accuracy,
            optimal_threshold=optimal_threshold,
            dimensions=dimensions,
            score_bins=score_bins,
            weight_adjustments=weight_adjustments,
            threshold_adjustment=threshold_adjustment,
            summary=summary,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Core analysis methods
    # ------------------------------------------------------------------

    def _load_confirmed_outcomes(self, profile_id: Optional[str]) -> List[Dict[str, Any]]:
        """Load outcomes with confirmed results and screening scores."""
        query = """
            SELECT go.*, o.overall_score, o.analysis_discovery, o.analysis_plan
            FROM grant_outcomes go
            JOIN opportunities o ON go.opportunity_id = o.id
            WHERE go.award_status IN ('awarded', 'rejected')
        """
        params: list = []
        if profile_id:
            query += " AND go.profile_id = ?"
            params.append(profile_id)

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def _compute_mae(self, outcomes: List[Dict]) -> Optional[float]:
        """Mean absolute error: avg(|score - actual|) where actual is 1 for awarded, 0 for rejected."""
        errors = []
        for o in outcomes:
            score = o.get("screening_score") or o.get("overall_score")
            if score is not None:
                actual = 1.0 if o["award_status"] == "awarded" else 0.0
                errors.append(abs(score - actual))
        return round(sum(errors) / len(errors), 4) if errors else None

    def _compute_accuracy(self, outcomes: List[Dict], threshold: float) -> Optional[float]:
        """Fraction of outcomes where score > threshold predicted awarded correctly."""
        correct = 0
        total = 0
        for o in outcomes:
            score = o.get("screening_score") or o.get("overall_score")
            if score is not None:
                predicted_pass = score >= threshold
                actual_pass = o["award_status"] == "awarded"
                if predicted_pass == actual_pass:
                    correct += 1
                total += 1
        return round(correct / total, 4) if total > 0 else None

    def _find_optimal_threshold(self, outcomes: List[Dict]) -> Optional[float]:
        """Find the threshold that maximizes accuracy."""
        best_threshold = 0.5
        best_accuracy = 0.0
        for t in [i / 20.0 for i in range(1, 20)]:
            acc = self._compute_accuracy(outcomes, t)
            if acc is not None and acc > best_accuracy:
                best_accuracy = acc
                best_threshold = t
        return best_threshold

    def _compute_score_bins(self, outcomes: List[Dict]) -> List[Dict[str, Any]]:
        """Group outcomes into score bins to show calibration curve."""
        bins: Dict[str, Dict] = {}
        for label in ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]:
            bins[label] = {"bin": label, "awarded": 0, "rejected": 0, "total": 0}

        for o in outcomes:
            score = o.get("screening_score") or o.get("overall_score") or 0
            if score < 0.2:
                b = "0.0-0.2"
            elif score < 0.4:
                b = "0.2-0.4"
            elif score < 0.6:
                b = "0.4-0.6"
            elif score < 0.8:
                b = "0.6-0.8"
            else:
                b = "0.8-1.0"
            bins[b]["total"] += 1
            if o["award_status"] == "awarded":
                bins[b]["awarded"] += 1
            else:
                bins[b]["rejected"] += 1

        result = []
        for b in bins.values():
            b["success_rate"] = round(b["awarded"] / b["total"], 3) if b["total"] > 0 else None
            result.append(b)
        return result

    def _calibrate_dimensions(self, outcomes: List[Dict]) -> List[DimensionCalibration]:
        """Analyze each scoring dimension's predictive power."""
        results = []
        for dim in SCORING_DIMENSIONS:
            awarded_scores = []
            rejected_scores = []

            for o in outcomes:
                score = self._extract_dimension_score(o, dim)
                if score is not None:
                    if o["award_status"] == "awarded":
                        awarded_scores.append(score)
                    else:
                        rejected_scores.append(score)

            total = len(awarded_scores) + len(rejected_scores)
            if total < 2:
                results.append(DimensionCalibration(
                    dimension=dim, sample_count=total,
                    mean_score_awarded=None, mean_score_rejected=None,
                    separation=None, bias=None, prediction_power=None,
                    recommendation=f"Insufficient data for {dim} ({total} samples)",
                ))
                continue

            mean_awarded = sum(awarded_scores) / len(awarded_scores) if awarded_scores else None
            mean_rejected = sum(rejected_scores) / len(rejected_scores) if rejected_scores else None

            # Separation: how much gap between awarded and rejected means
            separation = None
            if mean_awarded is not None and mean_rejected is not None:
                separation = round(mean_awarded - mean_rejected, 4)

            # Bias: positive = scores too high on average vs outcomes
            all_scores = awarded_scores + rejected_scores
            all_actuals = [1.0] * len(awarded_scores) + [0.0] * len(rejected_scores)
            bias = round(sum(all_scores) / len(all_scores) - sum(all_actuals) / len(all_actuals), 4)

            # Prediction power: normalized separation (0-1)
            prediction_power = None
            if separation is not None:
                prediction_power = round(min(max(separation, 0), 1.0), 4)

            recommendation = self._dimension_recommendation(dim, separation, bias, prediction_power)

            results.append(DimensionCalibration(
                dimension=dim,
                sample_count=total,
                mean_score_awarded=round(mean_awarded, 4) if mean_awarded else None,
                mean_score_rejected=round(mean_rejected, 4) if mean_rejected else None,
                separation=separation,
                bias=bias,
                prediction_power=prediction_power,
                recommendation=recommendation,
            ))

        return results

    def _extract_dimension_score(self, outcome: Dict, dimension: str) -> Optional[float]:
        """Extract a dimension score from an outcome record."""
        # Check snapshot columns first
        col = f"screening_{dimension}"
        if outcome.get(col) is not None:
            return outcome[col]

        # Fall back to analysis JSON
        for field_name in ("analysis_discovery", "analysis_plan"):
            raw = outcome.get(field_name)
            if raw:
                try:
                    data = json.loads(raw) if isinstance(raw, str) else raw
                    for key in (f"{dimension}_score", dimension):
                        if key in data:
                            return data[key]
                except (json.JSONDecodeError, TypeError):
                    pass
        return None

    def _recommend_weight_adjustments(
        self, dimensions: List[DimensionCalibration]
    ) -> Dict[str, float]:
        """Suggest weight deltas based on dimension calibration."""
        adjustments = {}
        for d in dimensions:
            if d.prediction_power is None or d.sample_count < 3:
                continue

            delta = 0.0
            if d.prediction_power >= 0.3:
                # Strong predictor — increase weight modestly
                delta = round(min(d.prediction_power * 0.05, 0.05), 3)
            elif d.prediction_power < 0.1:
                # Weak predictor — decrease weight
                delta = -0.03

            if abs(delta) > 0.001:
                adjustments[d.dimension] = delta

        return adjustments

    def _dimension_recommendation(
        self, dim: str, separation: Optional[float],
        bias: Optional[float], power: Optional[float],
    ) -> str:
        if power is None:
            return "Insufficient data"
        parts = []
        if power >= 0.3:
            parts.append(f"Strong predictor (power={power})")
        elif power >= 0.15:
            parts.append(f"Moderate predictor (power={power})")
        else:
            parts.append(f"Weak predictor (power={power})")

        if bias is not None:
            if bias > 0.15:
                parts.append("over-optimistic — consider lowering base scores")
            elif bias < -0.15:
                parts.append("under-scoring — consider raising base scores")

        return "; ".join(parts)

    def _generate_summary(
        self, total: int, awarded: int, rejected: int,
        mae: Optional[float], accuracy: Optional[float],
        dimensions: List[DimensionCalibration],
        adjustments: Dict[str, float],
    ) -> str:
        lines = [
            f"Calibration based on {total} confirmed outcomes ({awarded} awarded, {rejected} rejected).",
        ]
        if mae is not None:
            lines.append(f"Mean absolute error: {mae:.3f}")
        if accuracy is not None:
            lines.append(f"Overall accuracy at optimal threshold: {accuracy:.1%}")

        strong = [d.dimension for d in dimensions if d.prediction_power and d.prediction_power >= 0.3]
        weak = [d.dimension for d in dimensions if d.prediction_power is not None and d.prediction_power < 0.1]
        if strong:
            lines.append(f"Strongest predictors: {', '.join(strong)}")
        if weak:
            lines.append(f"Weakest predictors: {', '.join(weak)}")

        if adjustments:
            adj_str = ", ".join(f"{k}: {v:+.3f}" for k, v in adjustments.items())
            lines.append(f"Recommended weight adjustments: {adj_str}")

        return " | ".join(lines)
