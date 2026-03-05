"""
Outcome Tracker - Records and queries grant outcomes for the learning loop.

Phase F component 1: Track what happens after screening/analysis.
Records whether opportunities were pursued, awarded, or rejected,
and why — enabling scoring calibration over time.
"""

import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OutcomeRecord:
    """A recorded grant outcome."""
    id: str
    opportunity_id: str
    profile_id: str
    award_status: str = "pending"  # pending, awarded, rejected, withdrawn, not_pursued
    application_submitted: bool = False
    application_submitted_date: Optional[str] = None
    award_date: Optional[str] = None
    award_amount: Optional[float] = None
    award_notification_source: Optional[str] = None
    screening_score: Optional[float] = None
    screening_confidence: Optional[str] = None
    screening_strategic_fit: Optional[float] = None
    screening_eligibility: Optional[float] = None
    screening_timing: Optional[float] = None
    screening_financial: Optional[float] = None
    screening_competition: Optional[float] = None
    deep_intelligence_score: Optional[float] = None
    multidimensional_score: Optional[float] = None
    gateway_decision: Optional[str] = None
    gateway_decision_reason: Optional[str] = None
    outcome_notes: Optional[str] = None
    key_success_factors: Optional[List[str]] = None
    key_failure_factors: Optional[List[str]] = None
    recorded_at: Optional[str] = None
    updated_at: Optional[str] = None


class OutcomeTracker:
    """
    Service for recording and querying grant outcomes.

    Connects outcome data to screening scores so the calibration
    engine can learn which scoring dimensions predict success.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self):
        """Run the learning loop migration if tables don't exist."""
        migration_path = Path(__file__).parent.parent / "database" / "migrations" / "002_learning_loop.sql"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='grant_outcomes'"
            )
            if not cursor.fetchone():
                if migration_path.exists():
                    conn.executescript(migration_path.read_text())
                    logger.info("Learning loop tables created")
                else:
                    logger.error(f"Migration file not found: {migration_path}")

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Record outcomes
    # ------------------------------------------------------------------

    def record_outcome(
        self,
        opportunity_id: str,
        profile_id: str,
        award_status: str,
        award_amount: Optional[float] = None,
        award_date: Optional[str] = None,
        application_submitted: bool = False,
        application_submitted_date: Optional[str] = None,
        award_notification_source: Optional[str] = None,
        outcome_notes: Optional[str] = None,
        key_success_factors: Optional[List[str]] = None,
        key_failure_factors: Optional[List[str]] = None,
    ) -> OutcomeRecord:
        """Record or update an outcome for an opportunity."""
        valid_statuses = {"pending", "awarded", "rejected", "withdrawn", "not_pursued"}
        if award_status not in valid_statuses:
            raise ValueError(f"award_status must be one of {valid_statuses}")

        now = datetime.utcnow().isoformat()

        # Fetch screening scores from the opportunity record
        scores = self._fetch_opportunity_scores(opportunity_id)

        # Fetch gateway decision if available
        gw = self._fetch_gateway_decision(opportunity_id)

        with self._conn() as conn:
            # Check for existing outcome
            existing = conn.execute(
                "SELECT id FROM grant_outcomes WHERE opportunity_id = ?",
                (opportunity_id,),
            ).fetchone()

            if existing:
                outcome_id = existing["id"]
                conn.execute(
                    """UPDATE grant_outcomes SET
                        award_status = ?, award_amount = ?, award_date = ?,
                        application_submitted = ?, application_submitted_date = ?,
                        award_notification_source = ?, outcome_notes = ?,
                        key_success_factors = ?, key_failure_factors = ?,
                        updated_at = ?
                    WHERE id = ?""",
                    (
                        award_status, award_amount, award_date,
                        int(application_submitted), application_submitted_date,
                        award_notification_source, outcome_notes,
                        json.dumps(key_success_factors) if key_success_factors else None,
                        json.dumps(key_failure_factors) if key_failure_factors else None,
                        now, outcome_id,
                    ),
                )
                logger.info(f"Updated outcome {outcome_id} for opportunity {opportunity_id}")
            else:
                outcome_id = f"outcome_{uuid.uuid4().hex[:12]}"
                conn.execute(
                    """INSERT INTO grant_outcomes (
                        id, opportunity_id, profile_id,
                        application_submitted, application_submitted_date,
                        award_status, award_date, award_amount, award_notification_source,
                        screening_score, screening_confidence,
                        screening_strategic_fit, screening_eligibility,
                        screening_timing, screening_financial, screening_competition,
                        deep_intelligence_score, multidimensional_score,
                        gateway_decision, gateway_decision_reason,
                        outcome_notes, key_success_factors, key_failure_factors,
                        recorded_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        outcome_id, opportunity_id, profile_id,
                        int(application_submitted), application_submitted_date,
                        award_status, award_date, award_amount, award_notification_source,
                        scores.get("overall_score"),
                        scores.get("confidence_level"),
                        scores.get("strategic_fit"),
                        scores.get("eligibility"),
                        scores.get("timing"),
                        scores.get("financial"),
                        scores.get("competition"),
                        scores.get("deep_intelligence_score"),
                        scores.get("multidimensional_score"),
                        gw.get("decision") if gw else None,
                        gw.get("decision_reason") if gw else None,
                        outcome_notes,
                        json.dumps(key_success_factors) if key_success_factors else None,
                        json.dumps(key_failure_factors) if key_failure_factors else None,
                        now, now,
                    ),
                )
                logger.info(f"Created outcome {outcome_id} for opportunity {opportunity_id}")

                # Write calibration log entry for confirmed outcomes
                if award_status in ("awarded", "rejected"):
                    self._write_calibration_entry(
                        conn, opportunity_id, profile_id,
                        scores, award_status, award_amount,
                    )

            conn.commit()

        return self.get_outcome(opportunity_id)

    def get_outcome(self, opportunity_id: str) -> Optional[OutcomeRecord]:
        """Get the outcome record for an opportunity."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM grant_outcomes WHERE opportunity_id = ?",
                (opportunity_id,),
            ).fetchone()
            if not row:
                return None
            return self._row_to_record(row)

    def get_outcomes_for_profile(
        self, profile_id: str, status_filter: Optional[str] = None
    ) -> List[OutcomeRecord]:
        """Get all outcomes for a profile, optionally filtered by status."""
        query = "SELECT * FROM grant_outcomes WHERE profile_id = ?"
        params: list = [profile_id]
        if status_filter:
            query += " AND award_status = ?"
            params.append(status_filter)
        query += " ORDER BY recorded_at DESC"

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_record(r) for r in rows]

    def get_confirmed_outcomes(self, profile_id: Optional[str] = None) -> List[OutcomeRecord]:
        """Get outcomes with confirmed results (awarded or rejected)."""
        query = "SELECT * FROM grant_outcomes WHERE award_status IN ('awarded', 'rejected')"
        params: list = []
        if profile_id:
            query += " AND profile_id = ?"
            params.append(profile_id)
        query += " ORDER BY recorded_at DESC"

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_record(r) for r in rows]

    def get_outcome_summary(self, profile_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary statistics of all outcomes."""
        base = "SELECT * FROM grant_outcomes"
        params: list = []
        if profile_id:
            base += " WHERE profile_id = ?"
            params.append(profile_id)

        with self._conn() as conn:
            rows = conn.execute(base, params).fetchall()

        if not rows:
            return {
                "total_tracked": 0,
                "by_status": {},
                "success_rate": None,
                "total_awarded_amount": 0,
                "avg_awarded_amount": None,
            }

        by_status: Dict[str, int] = {}
        total_awarded = 0.0
        award_count = 0
        for r in rows:
            s = r["award_status"]
            by_status[s] = by_status.get(s, 0) + 1
            if s == "awarded" and r["award_amount"]:
                total_awarded += r["award_amount"]
                award_count += 1

        confirmed = by_status.get("awarded", 0) + by_status.get("rejected", 0)
        success_rate = by_status.get("awarded", 0) / confirmed if confirmed > 0 else None

        return {
            "total_tracked": len(rows),
            "by_status": by_status,
            "success_rate": round(success_rate, 3) if success_rate is not None else None,
            "total_awarded_amount": total_awarded,
            "avg_awarded_amount": round(total_awarded / award_count, 2) if award_count > 0 else None,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_opportunity_scores(self, opportunity_id: str) -> Dict[str, Any]:
        """Pull screening scores from the opportunities table."""
        with self._conn() as conn:
            row = conn.execute(
                """SELECT overall_score, confidence_level,
                          analysis_discovery, analysis_plan
                   FROM opportunities WHERE id = ?""",
                (opportunity_id,),
            ).fetchone()
            if not row:
                return {}

        scores: Dict[str, Any] = {
            "overall_score": row["overall_score"],
            "confidence_level": str(row["confidence_level"]) if row["confidence_level"] else None,
        }

        # Try to extract dimensional scores from analysis JSON
        for field_name in ("analysis_discovery", "analysis_plan"):
            raw = row[field_name]
            if raw:
                try:
                    data = json.loads(raw) if isinstance(raw, str) else raw
                    for dim in ("strategic_fit", "eligibility", "timing", "financial", "competition"):
                        key = f"{dim}_score"
                        if key in data and dim not in scores:
                            scores[dim] = data[key]
                        elif dim in data and dim not in scores:
                            scores[dim] = data[dim]
                except (json.JSONDecodeError, TypeError):
                    pass

        return scores

    def _fetch_gateway_decision(self, opportunity_id: str) -> Optional[Dict[str, Any]]:
        """Fetch the most recent gateway decision for an opportunity."""
        with self._conn() as conn:
            row = conn.execute(
                """SELECT decision, decision_reason
                   FROM gateway_decisions WHERE opportunity_id = ?
                   ORDER BY decided_at DESC LIMIT 1""",
                (opportunity_id,),
            ).fetchone()
            if row:
                return dict(row)
        return None

    def _write_calibration_entry(
        self,
        conn: sqlite3.Connection,
        opportunity_id: str,
        profile_id: str,
        scores: Dict[str, Any],
        actual_outcome: str,
        award_amount: Optional[float],
    ):
        """Write a calibration log entry for a confirmed outcome."""
        screening_score = scores.get("overall_score")
        actual_val = 1.0 if actual_outcome == "awarded" else 0.0
        prediction_error = abs(screening_score - actual_val) if screening_score is not None else None

        dimension_scores = {}
        for dim in ("strategic_fit", "eligibility", "timing", "financial", "competition"):
            if dim in scores:
                dimension_scores[dim] = {"score": scores[dim]}

        conn.execute(
            """INSERT INTO scoring_calibration_log (
                id, opportunity_id, profile_id,
                screening_score, deep_score, multidimensional_score,
                dimension_scores, actual_outcome, award_amount,
                prediction_error, stage_at_prediction, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                f"cal_{uuid.uuid4().hex[:12]}",
                opportunity_id, profile_id,
                screening_score,
                scores.get("deep_intelligence_score"),
                scores.get("multidimensional_score"),
                json.dumps(dimension_scores) if dimension_scores else None,
                actual_outcome, award_amount,
                prediction_error, "screening",
                datetime.utcnow().isoformat(),
            ),
        )

    def _row_to_record(self, row: sqlite3.Row) -> OutcomeRecord:
        d = dict(row)
        for list_field in ("key_success_factors", "key_failure_factors"):
            if d.get(list_field):
                try:
                    d[list_field] = json.loads(d[list_field])
                except (json.JSONDecodeError, TypeError):
                    d[list_field] = None
        d["application_submitted"] = bool(d.get("application_submitted", 0))
        return OutcomeRecord(**{k: v for k, v in d.items() if k in OutcomeRecord.__dataclass_fields__})
