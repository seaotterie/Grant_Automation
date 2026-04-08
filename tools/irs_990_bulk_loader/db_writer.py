"""
BulkLoaderDBWriter — all database writes for the IRS 990 offline bulk loader.

Writes to two databases:
  - nonprofit_intelligence.db: board_network_index, foundation_grants,
                               foundation_intelligence_index, foundation_narratives,
                               data_import_log
  - catalynx.db:               ein_intelligence.pdf_analyses (officer data for Stage 3 ETL)

All flushes use executemany() with a single transaction per batch.
INSERT OR IGNORE keeps loads idempotent.
"""

import json
import logging
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Capacity tier thresholds (assets_fmv)
_TIER_THRESHOLDS = [
    (100_000_000, "mega"),
    ( 10_000_000, "major"),
    (  1_000_000, "significant"),
  (    100_000, "modest"),
]

_LOADER_VERSION = "bulk_loader_v1"


def _capacity_tier(assets_fmv: Optional[float]) -> str:
    if not assets_fmv:
        return "unknown"
    for threshold, label in _TIER_THRESHOLDS:
        if assets_fmv >= threshold:
            return label
    return "minimal"


def _payout_compliance(qualifying: Optional[float], distributable: Optional[float]) -> str:
    if qualifying is None or distributable is None or distributable <= 0:
        return "unknown"
    ratio = qualifying / distributable
    if ratio >= 0.95:
        return "compliant"
    if ratio >= 0.50:
        return "under_payout"
    return "distressed"


def _health_status(payout: str, assets_fmv: Optional[float]) -> str:
    if payout == "compliant":
        return "strong" if (assets_fmv or 0) > 1_000_000 else "stable"
    if payout == "under_payout":
        return "declining"
    if payout == "distressed":
        return "distressed"
    return "unknown"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _data_quality(financials: dict, officers: list) -> float:
    """Simple 0-1 completeness score."""
    expected = ["total_assets", "grants_paid_total", "distributable_amount",
                "qualifying_distributions"]
    filled = sum(1 for k in expected if financials.get(k) is not None)
    officer_score = 1.0 if officers else 0.0
    return round((filled / len(expected) * 0.7 + officer_score * 0.3), 3)


class BulkLoaderDBWriter:
    """
    Manages DB connections and batch writes for the bulk loader.

    Usage:
        writer = BulkLoaderDBWriter(intel_db, catalynx_db)
        writer.ensure_tables()
        writer.flush_board_network(batch)
        ...
        writer.close()
    """

    def __init__(self, intel_db_path: str, catalynx_db_path: str):
        self.intel_db_path    = intel_db_path
        self.catalynx_db_path = catalynx_db_path
        self._intel_conn: Optional[sqlite3.Connection] = None
        self._cat_conn:   Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _intel(self) -> sqlite3.Connection:
        if self._intel_conn is None:
            conn = sqlite3.connect(self.intel_db_path, timeout=30)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = 10000")
            self._intel_conn = conn
        return self._intel_conn

    def _cat(self) -> sqlite3.Connection:
        if self._cat_conn is None:
            conn = sqlite3.connect(self.catalynx_db_path, timeout=30)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            self._cat_conn = conn
        return self._cat_conn

    def close(self):
        if self._intel_conn:
            self._intel_conn.close()
            self._intel_conn = None
        if self._cat_conn:
            self._cat_conn.close()
            self._cat_conn = None

    # ------------------------------------------------------------------
    # Schema setup
    # ------------------------------------------------------------------

    def ensure_tables(self):
        """Run migration SQL if foundation_grants doesn't exist yet."""
        migration = (
            Path(__file__).parent / "migration_foundation_grants.sql"
        )
        conn = self._intel()
        with open(migration) as f:
            conn.executescript(f.read())
        conn.commit()
        logger.info("foundation_grants table ensured")

    # ------------------------------------------------------------------
    # Resume support
    # ------------------------------------------------------------------

    def is_zip_already_processed(self, zip_filename: str) -> bool:
        """
        Return True if data_import_log has a successful entry for this ZIP.
        A ZIP with >10% error rate is considered incomplete and will reprocess.
        """
        try:
            row = self._intel().execute(
                """
                SELECT records_processed, records_error, notes
                FROM data_import_log
                WHERE file_name = ?
                ORDER BY import_date DESC LIMIT 1
                """,
                (zip_filename,),
            ).fetchone()
            if row is None:
                return False
            processed = row["records_processed"] or 1
            errors    = row["records_error"] or 0
            notes     = row["notes"] or ""
            if _LOADER_VERSION not in notes:
                return False
            return (errors / processed) < 0.10
        except Exception:
            return False

    # ------------------------------------------------------------------
    # board_network_index
    # ------------------------------------------------------------------

    def flush_board_network(self, batch: list) -> int:
        """
        Insert officer records into board_network_index.
        batch items: parsed["officers"] entries with extra "ein" and "source_tax_year".
        Returns number of rows actually inserted.
        """
        if not batch:
            return 0
        rows = [
            (
                r["normalized_name"],
                r["ein"],
                r.get("title"),
                int(r["compensation"]) if r.get("compensation") else 0,
                r.get("source_tax_year"),
                _now(),
            )
            for r in batch
            if r.get("normalized_name") and r.get("ein")
        ]
        if not rows:
            return 0
        conn = self._intel()
        cur  = conn.cursor()
        cur.executemany(
            """
            INSERT OR IGNORE INTO board_network_index
                (normalized_name, ein, title, compensation, source_tax_year, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        inserted = cur.rowcount if cur.rowcount >= 0 else len(rows)
        logger.debug(f"board_network_index: {len(rows)} attempted, {inserted} inserted")
        return inserted

    # ------------------------------------------------------------------
    # foundation_grants
    # ------------------------------------------------------------------

    def flush_grants(self, batch: list) -> int:
        """
        Insert grant records into foundation_grants.
        batch items: parsed["grants"] entries with extra "grantor_ein",
        "tax_year", "form_type", "source_zip_file".
        """
        if not batch:
            return 0
        rows = [
            (
                r["grantor_ein"],
                r["tax_year"],
                r["form_type"],
                r["recipient_name"][:500],
                r.get("recipient_ein"),
                r.get("recipient_city"),
                r.get("recipient_state"),
                float(r.get("grant_amount") or 0),
                r.get("grant_purpose"),
                r.get("assistance_type"),
                r.get("relationship_desc"),
                r.get("source_zip_file"),
            )
            for r in batch
            if r.get("grantor_ein") and r.get("recipient_name")
        ]
        if not rows:
            return 0
        conn = self._intel()
        cur  = conn.cursor()
        cur.executemany(
            """
            INSERT OR IGNORE INTO foundation_grants
                (grantor_ein, tax_year, form_type, recipient_name, recipient_ein,
                 recipient_city, recipient_state, grant_amount, grant_purpose,
                 assistance_type, relationship_desc, source_zip_file)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        inserted = cur.rowcount if cur.rowcount >= 0 else len(rows)
        logger.debug(f"foundation_grants: {len(rows)} attempted, {inserted} inserted")
        return inserted

    # ------------------------------------------------------------------
    # foundation_intelligence_index  (990-PF only)
    # ------------------------------------------------------------------

    def flush_foundation_intelligence(self, batch: list) -> int:
        """
        Upsert (INSERT OR REPLACE) foundation_intelligence_index rows.
        batch items: full parsed dicts for 990-PF filings.
        """
        if not batch:
            return 0

        rows = []
        for r in batch:
            fin   = r.get("financials", {})
            offs  = r.get("officers", [])
            narr  = r.get("narrative", {})
            assets_fmv = fin.get("assets_fmv") or fin.get("total_assets")
            grants_paid = fin.get("grants_paid_total")
            avg_grant = None
            if grants_paid and r.get("grant_count", 0) > 0:
                avg_grant = int(grants_paid / r["grant_count"])

            qual  = fin.get("qualifying_distributions")
            distr = fin.get("distributable_amount")
            payout = _payout_compliance(qual, distr)
            health = _health_status(payout, assets_fmv)
            tier   = _capacity_tier(assets_fmv)
            dq     = _data_quality(fin, offs)

            accepts = narr.get("accepts_applications", "unknown") or "unknown"

            rows.append((
                r["ein"],
                tier,
                int(grants_paid) if grants_paid else 0,
                int(assets_fmv)  if assets_fmv  else 0,
                int(avg_grant)   if avg_grant   else 0,
                int(grants_paid) if grants_paid else 0,  # budget estimate = grants_paid
                "unknown",        # giving_trend (needs multi-year, set later)
                None,             # giving_trend_pct
                1,                # years_of_data (at least 1 — this filing)
                1,                # is_eligible_grantmaker (default)
                accepts,
                1 if r.get("is_operating_foundation") else 0,
                health,
                payout,
                (qual / distr) if qual and distr and distr > 0 else None,
                None,             # undistributed_income
                0,                # future_grants_approved
                "unknown",        # portfolio_type
                dq,
                r["tax_year"],
                _now(),
                _LOADER_VERSION,
                dq,
            ))

        conn = self._intel()
        cur  = conn.cursor()
        cur.executemany(
            """
            INSERT OR REPLACE INTO foundation_intelligence_index (
                ein,
                capacity_tier,
                grants_paid_latest,
                assets_fmv_latest,
                avg_grant_size,
                annual_grant_budget_estimate,
                giving_trend,
                giving_trend_pct,
                years_of_data,
                is_eligible_grantmaker,
                accepts_applications,
                is_operating_foundation,
                health_status,
                payout_compliance,
                payout_ratio,
                undistributed_income,
                future_grants_approved,
                portfolio_type,
                portfolio_diversity_score,
                source_tax_year,
                last_computed_at,
                computation_version,
                data_quality_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        inserted = len(rows)
        logger.debug(f"foundation_intelligence_index: {inserted} upserted")
        return inserted

    # ------------------------------------------------------------------
    # foundation_narratives  (990-PF only)
    # ------------------------------------------------------------------

    def flush_foundation_narratives(self, batch: list) -> int:
        """
        INSERT OR IGNORE narrative rows (don't overwrite AI-extracted data).
        batch items: full parsed dicts for 990-PF filings.
        """
        if not batch:
            return 0
        rows = [
            (
                r["ein"],
                r.get("narrative", {}).get("mission_statement"),
                r.get("narrative", {}).get("accepts_applications", "unknown"),
                r.get("narrative", {}).get("geographic_limitations"),
                r["tax_year"],
                "xml_bulk_loader",
                0.70,           # extraction_confidence (structured XML, high but not perfect)
                _now(),
            )
            for r in batch
            if r.get("ein")
        ]
        if not rows:
            return 0
        conn = self._intel()
        cur  = conn.cursor()
        cur.executemany(
            """
            INSERT OR IGNORE INTO foundation_narratives
                (ein, mission_statement, accepts_applications, geographic_limitations,
                 source_tax_year, extraction_model, extraction_confidence, extracted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        inserted = cur.rowcount if cur.rowcount >= 0 else len(rows)
        logger.debug(f"foundation_narratives: {len(rows)} attempted, {inserted} inserted")
        return inserted

    # ------------------------------------------------------------------
    # organization_websites
    # ------------------------------------------------------------------

    def flush_organization_websites(self, batch: list) -> int:
        """
        INSERT OR IGNORE website URLs extracted from 990 XML WebsiteAddressTxt.
        Does not overwrite existing rows — first loaded year wins.
        Caller filters out entries without website_url before calling.
        """
        rows = [
            (r["ein"], r["website_url"], r.get("tax_year"), _now())
            for r in batch
            if r.get("ein") and r.get("website_url")
        ]
        if not rows:
            return 0
        conn = self._intel()
        cur  = conn.cursor()
        cur.executemany(
            """
            INSERT OR IGNORE INTO organization_websites (ein, website_url, tax_year, loaded_at)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        inserted = cur.rowcount if cur.rowcount >= 0 else len(rows)
        logger.debug(f"organization_websites: {len(rows)} attempted, {inserted} inserted")
        return inserted

    # ------------------------------------------------------------------
    # ein_intelligence.pdf_analyses  (catalynx.db)
    # ------------------------------------------------------------------

    def flush_ein_intelligence(self, batch: list) -> int:
        """
        Merge officer data into ein_intelligence.pdf_analyses in catalynx.db.
        batch items: full parsed dicts.

        The pdf_analyses format expected by Stage 3 ETL:
        {
          "2024": {
            "officers_and_directors": [
              {"name": str, "title": str, "is_officer": bool, "is_director": bool,
               "compensation": int}
            ]
          }
        }
        """
        if not batch:
            return 0

        conn = self._cat()
        updated = 0
        for r in batch:
            ein = r.get("ein")
            if not ein or not r.get("officers"):
                continue
            year = str(r.get("tax_year", ""))
            if not year:
                continue

            officers_list = [
                {
                    "name":        o["raw_name"],
                    "title":       o.get("title") or "",
                    "is_officer":  True,
                    "is_director": False,
                    "compensation": int(o["compensation"]) if o.get("compensation") else 0,
                }
                for o in r["officers"]
            ]

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    row = conn.execute(
                        "SELECT pdf_analyses FROM ein_intelligence WHERE ein = ?", (ein,)
                    ).fetchone()

                    if row:
                        existing = {}
                        try:
                            existing = json.loads(row["pdf_analyses"] or "{}")
                        except (json.JSONDecodeError, TypeError):
                            pass
                        existing[year] = {"officers_and_directors": officers_list}
                        conn.execute(
                            "UPDATE ein_intelligence SET pdf_analyses = ?, updated_at = ? WHERE ein = ?",
                            (json.dumps(existing), _now(), ein),
                        )
                    else:
                        pdf_analyses = json.dumps({year: {"officers_and_directors": officers_list}})
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO ein_intelligence
                                (ein, pdf_analyses, created_at, updated_at)
                            VALUES (?, ?, ?, ?)
                            """,
                            (ein, pdf_analyses, _now(), _now()),
                        )
                    conn.commit()
                    updated += 1
                    break
                except sqlite3.OperationalError as e:
                    if "locked" in str(e).lower() and attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                    else:
                        logger.debug(f"ein_intelligence write failed EIN {ein}: {e}")
                        break

        logger.debug(f"ein_intelligence: {updated} EINs updated in catalynx.db")
        return updated

    # ------------------------------------------------------------------
    # data_import_log
    # ------------------------------------------------------------------

    def log_import(
        self,
        zip_filename: str,
        file_type: str,
        tax_year: int,
        processed: int,
        success: int,
        errors: int,
        elapsed_seconds: float,
        notes: str = "",
    ) -> None:
        """Record a completed ZIP in data_import_log."""
        try:
            self._intel().execute(
                """
                INSERT INTO data_import_log
                    (import_date, file_name, file_type, tax_year,
                     records_processed, records_success, records_error,
                     processing_time_seconds, notes)
                VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    zip_filename,
                    file_type,
                    tax_year,
                    processed,
                    success,
                    errors,
                    round(elapsed_seconds, 1),
                    notes or f"{_LOADER_VERSION} complete",
                ),
            )
            self._intel().commit()
        except Exception as e:
            logger.warning(f"data_import_log write failed: {e}")
