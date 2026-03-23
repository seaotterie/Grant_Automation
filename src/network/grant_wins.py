"""
GrantWinService — Ingest historical grant wins from multiple sources,
link them to contacts (people), and compute "proven pathway" scores
that identify high-probability contacts for future cultivation.

Data sources (all $0.00):
  - CSV/Excel import (POC-provided history)
  - Manual entry via API
  - Schedule I reverse lookup (990-PF grantee lists mentioning profile EIN)
  - Opportunity records promoted to "won" stage

Unified schema: every win goes into the same grant_wins table regardless
of source; contacts are linked via grant_win_contacts join table.
"""

import csv
import hashlib
import io
import json
import logging
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Data models
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class GrantWinRecord:
    """A single historical grant win ready for ingestion."""
    funder_name: str
    amount: Optional[float] = None
    award_date: Optional[str] = None          # ISO date or year string
    funder_ein: Optional[str] = None
    program_name: Optional[str] = None
    grant_purpose: Optional[str] = None
    grant_type: Optional[str] = None          # general, project, capacity, capital, etc.
    contact_names: list = field(default_factory=list)  # people involved
    notes: Optional[str] = None
    source: str = "manual"                    # manual, csv_import, schedule_i


@dataclass
class ImportResult:
    """Result from a CSV/Excel import."""
    total_rows: int = 0
    wins_created: int = 0
    wins_updated: int = 0
    contacts_linked: int = 0
    rows_skipped: int = 0
    errors: list = field(default_factory=list)
    column_mapping_used: dict = field(default_factory=dict)


@dataclass
class ProvenPathwayContact:
    """A contact scored by involvement in historical wins."""
    person_id: int
    person_name: str
    total_wins_involved: int = 0
    total_amount_involved: float = 0.0
    most_recent_win_date: Optional[str] = None
    oldest_win_date: Optional[str] = None
    funder_names: list = field(default_factory=list)
    roles_at_funders: list = field(default_factory=list)  # current roles
    proven_pathway_score: float = 0.0
    is_still_active: bool = False
    recommendation: str = ""


# ──────────────────────────────────────────────────────────────────────────────
# CSV column mapping
# ──────────────────────────────────────────────────────────────────────────────

# Fuzzy column name mapping — recognizes common header variations
_COLUMN_ALIASES = {
    "funder_name": [
        "funder", "funder_name", "foundation", "foundation_name",
        "grantor", "grantor_name", "donor", "donor_name",
        "organization", "org_name", "source_name", "awarding_org",
        "funding_source", "grant_source",
    ],
    "amount": [
        "amount", "grant_amount", "award_amount", "total_amount",
        "funding_amount", "dollars", "award", "grant_size",
        "award_value", "grant_value",
    ],
    "award_date": [
        "date", "award_date", "grant_date", "funding_date",
        "year", "award_year", "grant_year", "fiscal_year",
        "fy", "period", "start_date",
    ],
    "funder_ein": [
        "ein", "funder_ein", "tax_id", "employer_id",
        "federal_id", "fein",
    ],
    "program_name": [
        "program", "program_name", "grant_program",
        "funding_program", "initiative",
    ],
    "grant_purpose": [
        "purpose", "grant_purpose", "description",
        "project", "project_name", "use",
    ],
    "grant_type": [
        "type", "grant_type", "funding_type",
        "award_type", "category",
    ],
    "contact_names": [
        "contact", "contacts", "contact_name", "contact_names",
        "poc", "point_of_contact", "key_contact",
        "program_officer", "grant_officer",
    ],
    "notes": [
        "notes", "comments", "remarks", "memo",
    ],
}


def _normalize_header(header: str) -> str:
    """Lowercase, strip, replace spaces/dashes with underscores."""
    return re.sub(r"[\s\-]+", "_", header.strip().lower())


def _auto_map_columns(headers: list[str]) -> dict[str, str]:
    """
    Given CSV headers, return {our_field: csv_header} mapping.
    Uses fuzzy alias matching.
    """
    mapping = {}
    normalized_headers = {_normalize_header(h): h for h in headers}

    for our_field, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized_headers:
                mapping[our_field] = normalized_headers[alias]
                break
    return mapping


# ──────────────────────────────────────────────────────────────────────────────
# Service
# ──────────────────────────────────────────────────────────────────────────────

class GrantWinService:
    """Manages grant win ingestion, contact linking, and proven pathway scoring."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # DDL
    # ------------------------------------------------------------------

    def ensure_tables(self) -> None:
        """Create grant_wins and grant_win_contacts tables."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS grant_wins (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id      TEXT    NOT NULL,
                    funder_name     TEXT    NOT NULL,
                    funder_ein      TEXT,
                    amount          REAL,
                    award_date      TEXT,
                    award_year      INTEGER,
                    program_name    TEXT,
                    grant_purpose   TEXT,
                    grant_type      TEXT,
                    notes           TEXT,
                    source          TEXT    NOT NULL DEFAULT 'manual',
                    source_ref      TEXT,
                    win_hash        TEXT    UNIQUE,
                    created_at      TIMESTAMP,
                    updated_at      TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_grant_wins_profile
                    ON grant_wins(profile_id);
                CREATE INDEX IF NOT EXISTS idx_grant_wins_funder_ein
                    ON grant_wins(funder_ein);
                CREATE INDEX IF NOT EXISTS idx_grant_wins_year
                    ON grant_wins(award_year);

                CREATE TABLE IF NOT EXISTS grant_win_contacts (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    grant_win_id    INTEGER NOT NULL REFERENCES grant_wins(id) ON DELETE CASCADE,
                    person_id       INTEGER REFERENCES people(id),
                    contact_name    TEXT    NOT NULL,
                    contact_role    TEXT,
                    side            TEXT    NOT NULL DEFAULT 'funder',
                    linked_at       TIMESTAMP,
                    link_source     TEXT    DEFAULT 'auto',
                    UNIQUE(grant_win_id, contact_name, side)
                );

                CREATE INDEX IF NOT EXISTS idx_gwc_person
                    ON grant_win_contacts(person_id);
                CREATE INDEX IF NOT EXISTS idx_gwc_win
                    ON grant_win_contacts(grant_win_id);
            """)
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Win hash (dedup key)
    # ------------------------------------------------------------------

    @staticmethod
    def _win_hash(profile_id: str, funder_name: str, amount: Optional[float],
                  award_date: Optional[str]) -> str:
        """Deterministic hash for deduplication."""
        raw = f"{profile_id}|{funder_name.lower().strip()}|{amount or ''}|{award_date or ''}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    # ------------------------------------------------------------------
    # Single-win CRUD
    # ------------------------------------------------------------------

    def add_win(self, profile_id: str, record: GrantWinRecord) -> dict:
        """Insert or update a single grant win. Returns {win_id, created}."""
        self.ensure_tables()
        now = self._now()
        year = self._extract_year(record.award_date)
        h = self._win_hash(profile_id, record.funder_name, record.amount, record.award_date)

        with self._conn() as conn:
            existing = conn.execute(
                "SELECT id FROM grant_wins WHERE win_hash = ?", (h,)
            ).fetchone()

            if existing:
                conn.execute("""
                    UPDATE grant_wins SET
                        funder_ein=COALESCE(?, funder_ein),
                        amount=COALESCE(?, amount),
                        program_name=COALESCE(?, program_name),
                        grant_purpose=COALESCE(?, grant_purpose),
                        grant_type=COALESCE(?, grant_type),
                        notes=COALESCE(?, notes),
                        updated_at=?
                    WHERE id=?
                """, (
                    record.funder_ein, record.amount, record.program_name,
                    record.grant_purpose, record.grant_type, record.notes,
                    now, existing["id"],
                ))
                win_id = existing["id"]
                created = False
            else:
                cursor = conn.execute("""
                    INSERT INTO grant_wins
                        (profile_id, funder_name, funder_ein, amount, award_date,
                         award_year, program_name, grant_purpose, grant_type,
                         notes, source, win_hash, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    profile_id, record.funder_name, record.funder_ein,
                    record.amount, record.award_date, year,
                    record.program_name, record.grant_purpose, record.grant_type,
                    record.notes, record.source, h, now, now,
                ))
                win_id = cursor.lastrowid
                created = True

            # Link contacts if provided
            contacts_linked = 0
            for name in record.contact_names:
                if name and name.strip():
                    contacts_linked += self._link_contact(
                        conn, win_id, name.strip(), side="funder", source="import"
                    )
            conn.commit()

        return {"win_id": win_id, "created": created, "contacts_linked": contacts_linked}

    def get_wins(self, profile_id: str) -> list[dict]:
        """Return all grant wins for a profile with linked contacts."""
        self.ensure_tables()
        with self._conn() as conn:
            wins = conn.execute(
                "SELECT * FROM grant_wins WHERE profile_id = ? ORDER BY award_year DESC, funder_name",
                (profile_id,),
            ).fetchall()

            result = []
            for w in wins:
                win_dict = dict(w)
                contacts = conn.execute(
                    "SELECT contact_name, contact_role, side, person_id "
                    "FROM grant_win_contacts WHERE grant_win_id = ?",
                    (w["id"],),
                ).fetchall()
                win_dict["contacts"] = [dict(c) for c in contacts]
                result.append(win_dict)
        return result

    def delete_win(self, win_id: int) -> bool:
        """Delete a grant win and its contacts (CASCADE)."""
        with self._conn() as conn:
            cursor = conn.execute("DELETE FROM grant_wins WHERE id = ?", (win_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # CSV / Excel import
    # ------------------------------------------------------------------

    def import_from_csv(
        self,
        profile_id: str,
        file_content: str,
        column_mapping: Optional[dict] = None,
        delimiter: str = ",",
    ) -> ImportResult:
        """
        Parse a CSV string and ingest grant wins.

        If column_mapping is None, auto-detects columns from headers.
        Accepts both strict CSV and loose formats (handles $ signs, commas
        in numbers, date variations, etc.).

        Args:
            profile_id: Profile to attach wins to
            file_content: Raw CSV text content
            column_mapping: Optional {our_field: csv_column_name} override
            delimiter: CSV delimiter (default comma)

        Returns:
            ImportResult with counts and any errors
        """
        self.ensure_tables()
        result = ImportResult()

        # Parse CSV
        reader = csv.DictReader(io.StringIO(file_content), delimiter=delimiter)
        if not reader.fieldnames:
            result.errors.append("No headers found in CSV")
            return result

        # Auto-map or use provided mapping
        if column_mapping:
            mapping = column_mapping
        else:
            mapping = _auto_map_columns(reader.fieldnames)

        result.column_mapping_used = mapping

        if "funder_name" not in mapping:
            result.errors.append(
                f"Could not identify a funder/foundation name column. "
                f"Headers found: {reader.fieldnames}"
            )
            return result

        rows = list(reader)
        result.total_rows = len(rows)

        for i, row in enumerate(rows):
            try:
                record = self._row_to_record(row, mapping)
                if not record:
                    result.rows_skipped += 1
                    continue

                res = self.add_win(profile_id, record)
                if res["created"]:
                    result.wins_created += 1
                else:
                    result.wins_updated += 1
                result.contacts_linked += res["contacts_linked"]

            except Exception as e:
                result.errors.append(f"Row {i + 2}: {e}")
                result.rows_skipped += 1

        return result

    def preview_csv_mapping(self, file_content: str, delimiter: str = ",") -> dict:
        """
        Preview how CSV columns will be mapped without importing.
        Returns {headers, auto_mapping, sample_rows, unmapped_columns}.
        Useful for UI to show the user what will happen before committing.
        """
        reader = csv.DictReader(io.StringIO(file_content), delimiter=delimiter)
        headers = reader.fieldnames or []
        mapping = _auto_map_columns(headers)

        sample_rows = []
        for i, row in enumerate(reader):
            if i >= 3:
                break
            sample_rows.append(dict(row))

        mapped_headers = set(mapping.values())
        unmapped = [h for h in headers if h not in mapped_headers]

        return {
            "headers": headers,
            "auto_mapping": mapping,
            "sample_rows": sample_rows,
            "unmapped_columns": unmapped,
            "recognized_fields": list(mapping.keys()),
        }

    # ------------------------------------------------------------------
    # Auto-link contacts from existing people database
    # ------------------------------------------------------------------

    def auto_link_contacts(self, profile_id: str) -> dict:
        """
        For each grant win with a funder_ein, find people who were on that
        funder's board around the time of the award (from organization_roles)
        and link them as contacts.

        This is the key function that connects historical wins to the
        people database. Cost: $0.00 (pure DB operations).

        Returns {wins_processed, contacts_linked, wins_without_ein}.
        """
        self.ensure_tables()
        stats = {"wins_processed": 0, "contacts_linked": 0, "wins_without_ein": 0}

        with self._conn() as conn:
            wins = conn.execute(
                "SELECT id, funder_ein, award_year FROM grant_wins WHERE profile_id = ?",
                (profile_id,),
            ).fetchall()

            for win in wins:
                if not win["funder_ein"]:
                    stats["wins_without_ein"] += 1
                    continue

                stats["wins_processed"] += 1

                # Find people with roles at this funder org
                # If we have an award_year, prefer people active around that time
                award_year = win["award_year"]
                if award_year:
                    # People active at funder around the award year
                    people = conn.execute("""
                        SELECT p.id, p.normalized_name, r.title, r.is_current,
                               r.start_date, r.end_date, r.filing_year
                        FROM people p
                        JOIN organization_roles r ON p.id = r.person_id
                        WHERE r.organization_ein = ?
                          AND (
                              r.is_current = 1
                              OR r.filing_year >= ? - 2
                              OR r.end_date IS NULL
                              OR CAST(SUBSTR(r.end_date, 1, 4) AS INTEGER) >= ? - 1
                          )
                    """, (win["funder_ein"], award_year, award_year)).fetchall()
                else:
                    # No year info — get all people at this funder
                    people = conn.execute("""
                        SELECT p.id, p.normalized_name, r.title, r.is_current
                        FROM people p
                        JOIN organization_roles r ON p.id = r.person_id
                        WHERE r.organization_ein = ?
                    """, (win["funder_ein"],)).fetchall()

                for person in people:
                    linked = self._link_contact(
                        conn, win["id"], person["normalized_name"],
                        side="funder", source="auto_990",
                        person_id=person["id"],
                        role=person["title"],
                    )
                    stats["contacts_linked"] += linked

            conn.commit()

        return stats

    # ------------------------------------------------------------------
    # Proven pathway scoring
    # ------------------------------------------------------------------

    def compute_proven_pathways(self, profile_id: str) -> list[dict]:
        """
        Score all people linked to historical wins for this profile.
        Returns ranked list of ProvenPathwayContact dicts.

        Scoring formula:
          base = wins_involved × 0.4
               + recency_factor × 0.3
               + amount_factor × 0.15
               + still_active_bonus × 0.15

        Where:
          recency_factor = 1.0 if most recent win < 2 years ago,
                           decays 0.15/year after that
          amount_factor  = log10(total_amount) / 7 (capped at 1.0)
          still_active   = 1.0 if person is currently at any funder org

        Cost: $0.00 (pure DB).
        """
        self.ensure_tables()
        import math

        current_year = datetime.now().year
        results = []

        with self._conn() as conn:
            # Get all contacts linked to this profile's wins
            contacts = conn.execute("""
                SELECT
                    gwc.person_id,
                    gwc.contact_name,
                    gw.id AS win_id,
                    gw.funder_name,
                    gw.funder_ein,
                    gw.amount,
                    gw.award_year,
                    gw.award_date
                FROM grant_win_contacts gwc
                JOIN grant_wins gw ON gwc.grant_win_id = gw.id
                WHERE gw.profile_id = ?
                ORDER BY gwc.contact_name
            """, (profile_id,)).fetchall()

            # Group by person (use person_id if available, else contact_name)
            person_wins: dict[str, list] = {}
            for c in contacts:
                key = str(c["person_id"]) if c["person_id"] else c["contact_name"].lower()
                if key not in person_wins:
                    person_wins[key] = {
                        "person_id": c["person_id"],
                        "person_name": c["contact_name"],
                        "wins": [],
                    }
                person_wins[key]["wins"].append(dict(c))

            for key, data in person_wins.items():
                wins = data["wins"]
                person_id = data["person_id"]
                person_name = data["person_name"]

                # Aggregate
                total_wins = len(wins)
                total_amount = sum(w["amount"] or 0 for w in wins)
                years = [w["award_year"] for w in wins if w["award_year"]]
                funder_names = list({w["funder_name"] for w in wins})

                most_recent = max(years) if years else None
                oldest = min(years) if years else None

                # Check if person is still active at any funder
                is_active = False
                current_roles = []
                if person_id:
                    roles = conn.execute("""
                        SELECT organization_name, title, is_current
                        FROM organization_roles
                        WHERE person_id = ? AND is_current = 1
                    """, (person_id,)).fetchall()
                    is_active = len(roles) > 0
                    current_roles = [
                        {"org": r["organization_name"], "title": r["title"]}
                        for r in roles
                    ]

                # Score components
                win_factor = min(total_wins / 5.0, 1.0)  # 5+ wins = max

                recency_factor = 0.0
                if most_recent:
                    years_ago = current_year - most_recent
                    recency_factor = max(0.0, 1.0 - 0.15 * years_ago)

                amount_factor = 0.0
                if total_amount > 0:
                    amount_factor = min(math.log10(total_amount) / 7.0, 1.0)

                active_bonus = 1.0 if is_active else 0.0

                score = (
                    win_factor * 0.40
                    + recency_factor * 0.30
                    + amount_factor * 0.15
                    + active_bonus * 0.15
                )
                score = round(min(score, 1.0), 3)

                # Generate recommendation
                recommendation = self._generate_recommendation(
                    person_name, total_wins, most_recent, is_active,
                    funder_names, total_amount, score,
                )

                results.append({
                    "person_id": person_id,
                    "person_name": person_name,
                    "total_wins_involved": total_wins,
                    "total_amount_involved": total_amount,
                    "most_recent_win_year": most_recent,
                    "oldest_win_year": oldest,
                    "funder_names": funder_names,
                    "roles_at_funders": current_roles,
                    "proven_pathway_score": score,
                    "is_still_active": is_active,
                    "recommendation": recommendation,
                })

        # Sort by score descending
        results.sort(key=lambda r: r["proven_pathway_score"], reverse=True)
        return results

    # ------------------------------------------------------------------
    # Summary stats
    # ------------------------------------------------------------------

    def get_summary(self, profile_id: str) -> dict:
        """Return summary statistics for a profile's grant win history."""
        self.ensure_tables()
        with self._conn() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM grant_wins WHERE profile_id = ?",
                (profile_id,),
            ).fetchone()[0]

            total_amount = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM grant_wins WHERE profile_id = ?",
                (profile_id,),
            ).fetchone()[0]

            by_source = conn.execute(
                "SELECT source, COUNT(*) as cnt FROM grant_wins "
                "WHERE profile_id = ? GROUP BY source",
                (profile_id,),
            ).fetchall()

            year_range = conn.execute(
                "SELECT MIN(award_year), MAX(award_year) FROM grant_wins "
                "WHERE profile_id = ? AND award_year IS NOT NULL",
                (profile_id,),
            ).fetchone()

            contacts_linked = conn.execute(
                "SELECT COUNT(DISTINCT gwc.contact_name) "
                "FROM grant_win_contacts gwc "
                "JOIN grant_wins gw ON gwc.grant_win_id = gw.id "
                "WHERE gw.profile_id = ?",
                (profile_id,),
            ).fetchone()[0]

            unique_funders = conn.execute(
                "SELECT COUNT(DISTINCT funder_name) FROM grant_wins WHERE profile_id = ?",
                (profile_id,),
            ).fetchone()[0]

        return {
            "profile_id": profile_id,
            "total_wins": total,
            "total_amount": total_amount,
            "unique_funders": unique_funders,
            "contacts_linked": contacts_linked,
            "by_source": {r["source"]: r["cnt"] for r in by_source},
            "earliest_year": year_range[0] if year_range else None,
            "latest_year": year_range[1] if year_range else None,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _link_contact(
        self, conn: sqlite3.Connection, win_id: int, name: str,
        side: str = "funder", source: str = "auto",
        person_id: Optional[int] = None, role: Optional[str] = None,
    ) -> int:
        """Link a contact to a grant win. Returns 1 if created, 0 if exists."""
        try:
            # Try to resolve person_id from people table if not provided
            if person_id is None:
                from src.network.name_normalizer import NameNormalizer
                normalizer = NameNormalizer()
                name_hash = normalizer.person_hash(name)
                existing = conn.execute(
                    "SELECT id FROM people WHERE name_hash = ?", (name_hash,)
                ).fetchone()
                if existing:
                    person_id = existing["id"]

            conn.execute("""
                INSERT OR IGNORE INTO grant_win_contacts
                    (grant_win_id, person_id, contact_name, contact_role, side, linked_at, link_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (win_id, person_id, name, role, side, self._now(), source))
            return 1
        except sqlite3.IntegrityError:
            return 0

    def _row_to_record(self, row: dict, mapping: dict) -> Optional[GrantWinRecord]:
        """Convert a CSV row dict to a GrantWinRecord using column mapping."""
        funder_col = mapping.get("funder_name")
        if not funder_col or not row.get(funder_col, "").strip():
            return None

        funder_name = row[funder_col].strip()

        # Parse amount (handles $, commas, etc.)
        amount = None
        if "amount" in mapping:
            raw = row.get(mapping["amount"], "").strip()
            amount = self._parse_amount(raw)

        # Parse date
        award_date = None
        if "award_date" in mapping:
            raw = row.get(mapping["award_date"], "").strip()
            award_date = self._parse_date(raw)

        # Contact names (may be semicolon or comma separated)
        contact_names = []
        if "contact_names" in mapping:
            raw = row.get(mapping["contact_names"], "").strip()
            if raw:
                # Split on semicolons, or commas if no semicolons
                if ";" in raw:
                    contact_names = [n.strip() for n in raw.split(";") if n.strip()]
                else:
                    contact_names = [n.strip() for n in raw.split(",") if n.strip()]

        return GrantWinRecord(
            funder_name=funder_name,
            amount=amount,
            award_date=award_date,
            funder_ein=row.get(mapping.get("funder_ein", ""), "").strip() or None,
            program_name=row.get(mapping.get("program_name", ""), "").strip() or None,
            grant_purpose=row.get(mapping.get("grant_purpose", ""), "").strip() or None,
            grant_type=row.get(mapping.get("grant_type", ""), "").strip() or None,
            contact_names=contact_names,
            notes=row.get(mapping.get("notes", ""), "").strip() or None,
            source="csv_import",
        )

    @staticmethod
    def _parse_amount(raw: str) -> Optional[float]:
        """Parse dollar amounts: $1,234.56 → 1234.56"""
        if not raw:
            return None
        cleaned = re.sub(r"[^\d.]", "", raw)
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None

    @staticmethod
    def _parse_date(raw: str) -> Optional[str]:
        """Parse various date formats into ISO date string."""
        if not raw:
            return None
        # Pure year
        if re.match(r"^\d{4}$", raw):
            return raw
        # Try common formats
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d",
                     "%d-%b-%Y", "%b %d, %Y", "%B %d, %Y", "%m-%d-%Y"):
            try:
                dt = datetime.strptime(raw, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return raw  # Return as-is if unparseable

    @staticmethod
    def _extract_year(date_str: Optional[str]) -> Optional[int]:
        """Extract 4-digit year from a date string."""
        if not date_str:
            return None
        match = re.search(r"\b(19|20)\d{2}\b", date_str)
        return int(match.group(0)) if match else None

    @staticmethod
    def _generate_recommendation(
        name: str, wins: int, most_recent: Optional[int],
        is_active: bool, funders: list, amount: float, score: float,
    ) -> str:
        """Generate a human-readable cultivation recommendation."""
        current_year = datetime.now().year

        if score >= 0.8:
            priority = "HIGH PRIORITY"
        elif score >= 0.5:
            priority = "MEDIUM PRIORITY"
        else:
            priority = "LOW PRIORITY"

        parts = [f"{priority}:"]

        if is_active and most_recent and (current_year - most_recent) <= 2:
            parts.append(
                f"{name} was involved in {wins} successful grant(s) "
                f"(most recent: {most_recent}) and is still active."
            )
            parts.append("Re-engage for renewal or new application.")
        elif is_active:
            parts.append(
                f"{name} is still active at a funder organization "
                f"and was involved in {wins} past win(s)."
            )
            parts.append("Reconnect — relationship may have gone dormant.")
        elif most_recent and (current_year - most_recent) <= 3:
            parts.append(
                f"{name} was recently involved in {wins} win(s) "
                f"but may no longer be at the funder."
            )
            parts.append("Verify current position before outreach.")
        else:
            parts.append(
                f"{name} was involved in {wins} historical win(s). "
                f"Check current status and affiliations."
            )

        if amount > 0:
            parts.append(f"Total award value: ${amount:,.0f}.")

        return " ".join(parts)
