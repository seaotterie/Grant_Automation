"""
Missed Opportunity Analyzer - Identifies opportunities we rejected that were actually funded.

Phase F component 3: Generate periodic "what did we miss" reports comparing
rejected opportunities against outcomes.
"""

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MissedOpportunity:
    """An opportunity we rejected or skipped that was actually funded."""
    opportunity_id: str
    organization_name: str
    profile_id: str
    # What we scored it
    screening_score: Optional[float]
    screening_dimensions: Dict[str, float]
    # What we decided
    gateway_decision: Optional[str]
    gateway_reason: Optional[str]
    # What actually happened
    award_status: str
    award_amount: Optional[float]
    award_date: Optional[str]
    # Analysis
    score_gap: Optional[float]  # How far below threshold it was
    weakest_dimension: Optional[str]
    dimension_errors: Dict[str, float]  # {dimension: error}


@dataclass
class MissedOpportunityReport:
    """Full report of missed opportunities for a profile."""
    profile_id: Optional[str]
    analysis_period: str
    total_rejected: int
    tracked_rejections: int
    actually_awarded: int
    miss_rate: Optional[float]
    total_missed_amount: float
    missed_opportunities: List[MissedOpportunity]
    # Pattern analysis
    common_weak_dimensions: List[Dict[str, Any]]  # Which dims caused us to miss
    threshold_analysis: Dict[str, Any]
    recommendations: List[str]
    generated_at: str = ""


class MissedOpportunityAnalyzer:
    """
    Analyzes rejected opportunities that turned out to be funded.

    Identifies patterns in what we missed and recommends adjustments
    to prevent similar misses in the future.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def generate_report(
        self,
        profile_id: Optional[str] = None,
        score_range: Optional[tuple] = None,
        decision_filter: Optional[str] = None,
    ) -> MissedOpportunityReport:
        """
        Generate a "what did we miss" report.

        Args:
            profile_id: Limit to specific profile
            score_range: (min, max) score range to analyze
            decision_filter: Only look at specific decision type (reject, not_pursued)
        """
        # Get rejected opportunities that have tracked outcomes
        rejected_with_outcomes = self._load_rejected_with_outcomes(
            profile_id, score_range, decision_filter,
        )

        # Total rejected count (even those without outcome tracking)
        total_rejected = self._count_rejected(profile_id)

        # Filter to only those that were actually awarded
        missed = [r for r in rejected_with_outcomes if r["award_status"] == "awarded"]

        # Build MissedOpportunity objects
        missed_opps = [self._build_missed_opportunity(m) for m in missed]

        # Analyze patterns
        common_weak = self._analyze_weak_dimensions(missed_opps)
        threshold_analysis = self._analyze_thresholds(missed, total_rejected)
        recommendations = self._generate_recommendations(missed_opps, common_weak, threshold_analysis)

        total_missed_amount = sum(m.award_amount or 0 for m in missed_opps)
        tracked = len(rejected_with_outcomes)
        miss_rate = len(missed) / tracked if tracked > 0 else None

        return MissedOpportunityReport(
            profile_id=profile_id,
            analysis_period="all_time",
            total_rejected=total_rejected,
            tracked_rejections=tracked,
            actually_awarded=len(missed),
            miss_rate=round(miss_rate, 3) if miss_rate is not None else None,
            total_missed_amount=total_missed_amount,
            missed_opportunities=missed_opps,
            common_weak_dimensions=common_weak,
            threshold_analysis=threshold_analysis,
            recommendations=recommendations,
            generated_at=datetime.utcnow().isoformat(),
        )

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_rejected_with_outcomes(
        self,
        profile_id: Optional[str],
        score_range: Optional[tuple],
        decision_filter: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Load rejected/not-pursued opportunities that have outcome data."""
        query = """
            SELECT go.*, o.organization_name, o.overall_score,
                   o.analysis_discovery, o.analysis_plan,
                   gd.decision AS gw_decision, gd.decision_reason AS gw_reason
            FROM grant_outcomes go
            JOIN opportunities o ON go.opportunity_id = o.id
            LEFT JOIN gateway_decisions gd ON go.opportunity_id = gd.opportunity_id
            WHERE go.award_status IN ('awarded', 'rejected')
              AND (go.gateway_decision IN ('reject', 'not_pursued')
                   OR gd.decision = 'reject'
                   OR go.award_status = 'awarded')
        """
        params: list = []

        if profile_id:
            query += " AND go.profile_id = ?"
            params.append(profile_id)

        if score_range:
            query += " AND COALESCE(go.screening_score, o.overall_score) BETWEEN ? AND ?"
            params.extend(score_range)

        if decision_filter:
            query += " AND (go.gateway_decision = ? OR gd.decision = ?)"
            params.extend([decision_filter, decision_filter])

        query += " ORDER BY go.award_amount DESC NULLS LAST"

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def _count_rejected(self, profile_id: Optional[str]) -> int:
        """Count total rejected/not-pursued opportunities."""
        query = """
            SELECT COUNT(*) as cnt FROM gateway_decisions
            WHERE decision = 'reject'
        """
        params: list = []
        if profile_id:
            query += " AND profile_id = ?"
            params.append(profile_id)

        with self._conn() as conn:
            row = conn.execute(query, params).fetchone()
            return row["cnt"] if row else 0

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def _build_missed_opportunity(self, row: Dict[str, Any]) -> MissedOpportunity:
        """Build a MissedOpportunity from a database row."""
        dimensions: Dict[str, float] = {}
        dimension_errors: Dict[str, float] = {}
        weakest = None
        worst_error = 0.0

        for dim in ("strategic_fit", "eligibility", "timing", "financial", "competition"):
            score = self._extract_dim_score(row, dim)
            if score is not None:
                dimensions[dim] = score
                # For awarded opps, the "error" is 1.0 - score (we should have scored higher)
                error = 1.0 - score
                dimension_errors[dim] = round(error, 4)
                if error > worst_error:
                    worst_error = error
                    weakest = dim

        screening_score = row.get("screening_score") or row.get("overall_score")
        score_gap = (0.5 - screening_score) if screening_score is not None else None

        return MissedOpportunity(
            opportunity_id=row.get("opportunity_id", ""),
            organization_name=row.get("organization_name", "Unknown"),
            profile_id=row.get("profile_id", ""),
            screening_score=screening_score,
            screening_dimensions=dimensions,
            gateway_decision=row.get("gw_decision") or row.get("gateway_decision"),
            gateway_reason=row.get("gw_reason") or row.get("gateway_decision_reason"),
            award_status=row["award_status"],
            award_amount=row.get("award_amount"),
            award_date=row.get("award_date"),
            score_gap=round(score_gap, 4) if score_gap is not None else None,
            weakest_dimension=weakest,
            dimension_errors=dimension_errors,
        )

    def _extract_dim_score(self, row: Dict, dim: str) -> Optional[float]:
        col = f"screening_{dim}"
        if row.get(col) is not None:
            return row[col]
        for field_name in ("analysis_discovery", "analysis_plan"):
            raw = row.get(field_name)
            if raw:
                try:
                    data = json.loads(raw) if isinstance(raw, str) else raw
                    for key in (f"{dim}_score", dim):
                        if key in data:
                            return data[key]
                except (json.JSONDecodeError, TypeError):
                    pass
        return None

    def _analyze_weak_dimensions(
        self, missed: List[MissedOpportunity]
    ) -> List[Dict[str, Any]]:
        """Find which dimensions most frequently caused us to miss opportunities."""
        dim_miss_count: Dict[str, int] = {}
        dim_total_error: Dict[str, float] = {}

        for m in missed:
            for dim, error in m.dimension_errors.items():
                dim_miss_count[dim] = dim_miss_count.get(dim, 0) + 1
                dim_total_error[dim] = dim_total_error.get(dim, 0.0) + error

        result = []
        for dim in sorted(dim_miss_count, key=lambda d: dim_total_error.get(d, 0), reverse=True):
            count = dim_miss_count[dim]
            avg_error = dim_total_error[dim] / count if count > 0 else 0
            result.append({
                "dimension": dim,
                "miss_count": count,
                "avg_error": round(avg_error, 4),
                "total_error": round(dim_total_error[dim], 4),
            })
        return result

    def _analyze_thresholds(
        self, missed_rows: List[Dict], total_rejected: int,
    ) -> Dict[str, Any]:
        """Analyze what threshold adjustments would have caught more opportunities."""
        if not missed_rows:
            return {"analysis": "No missed opportunities to analyze."}

        scores = [
            r.get("screening_score") or r.get("overall_score") or 0
            for r in missed_rows
        ]
        if not scores:
            return {"analysis": "No screening scores available for missed opportunities."}

        max_missed_score = max(scores)
        avg_missed_score = sum(scores) / len(scores)

        # How many would we catch at different thresholds
        catches = {}
        for t in [0.3, 0.35, 0.4, 0.45, 0.5]:
            caught = sum(1 for s in scores if s >= t)
            catches[str(t)] = caught

        return {
            "missed_count": len(scores),
            "max_missed_score": round(max_missed_score, 4),
            "avg_missed_score": round(avg_missed_score, 4),
            "catches_at_threshold": catches,
            "recommendation": (
                f"Lowering threshold to {avg_missed_score:.2f} would catch "
                f"{sum(1 for s in scores if s >= avg_missed_score)} of {len(scores)} missed opportunities."
            ),
        }

    def _generate_recommendations(
        self,
        missed: List[MissedOpportunity],
        weak_dims: List[Dict[str, Any]],
        threshold_analysis: Dict[str, Any],
    ) -> List[str]:
        """Generate actionable recommendations from the analysis."""
        recs = []

        if not missed:
            recs.append("No missed opportunities detected. Screening appears well-calibrated.")
            return recs

        recs.append(
            f"Detected {len(missed)} missed opportunities "
            f"(total missed funding: ${sum(m.award_amount or 0 for m in missed):,.0f})."
        )

        # Weak dimension recommendations
        if weak_dims:
            worst = weak_dims[0]
            recs.append(
                f"Most problematic dimension: '{worst['dimension']}' "
                f"(caused {worst['miss_count']} misses, avg error {worst['avg_error']:.2f}). "
                f"Consider increasing its weight or adjusting base scores."
            )

        # Threshold recommendation
        avg_score = threshold_analysis.get("avg_missed_score")
        if avg_score is not None and avg_score < 0.5:
            recs.append(
                f"Average missed opportunity score was {avg_score:.2f}. "
                f"Consider lowering the pass threshold or flagging borderline cases for human review."
            )

        # Pattern: many high-score misses
        high_score_misses = [m for m in missed if m.screening_score and m.screening_score > 0.4]
        if len(high_score_misses) > len(missed) * 0.5:
            recs.append(
                "Most missed opportunities had moderate-to-high scores. "
                "The human gateway may be too aggressive in rejecting borderline opportunities."
            )

        return recs
