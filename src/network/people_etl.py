"""
PeopleETL — migrate network_memberships into normalized people + organization_roles tables.

Pure ETL: no AI calls, no external APIs. Reads from the legacy network_memberships
table and writes to the new people / organization_roles schema.
"""

import logging
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any

from src.network.name_normalizer import NameNormalizer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Position classification mappings
# ---------------------------------------------------------------------------

_BOARD_KEYWORDS: dict[str, str] = {
    "chairman": "chair",
    "chairwoman": "chair",
    "chairperson": "chair",
    "chair": "chair",
    "co-chair": "chair",
    "vice chair": "vice_chair",
    "vice-chair": "vice_chair",
    "vice chairman": "vice_chair",
    "vice chairwoman": "vice_chair",
    "treasurer": "treasurer",
    "secretary": "secretary",
    "trustee": "trustee",
    "board member": "member",
    "director": "member",
    "member": "member",
}

_EXECUTIVE_KEYWORDS: dict[str, str] = {
    "chief executive officer": "ceo",
    "ceo": "ceo",
    "executive director": "executive_director",
    "president": "president",
    "vice president": "vice_president",
    "vp": "vice_president",
    "chief financial officer": "cfo",
    "cfo": "cfo",
    "chief operating officer": "coo",
    "coo": "coo",
    "chief technology officer": "cto",
    "chief program officer": "cpo",
    "chief development officer": "cdo",
    "chief marketing officer": "cmo",
    "general counsel": "general_counsel",
}

_STAFF_KEYWORDS: dict[str, str] = {
    "manager": "manager",
    "coordinator": "coordinator",
    "analyst": "analyst",
    "specialist": "specialist",
    "associate": "associate",
    "assistant": "assistant",
    "officer": "officer",
    "accountant": "accountant",
    "controller": "controller",
}

_ADVISORY_KEYWORDS: dict[str, str] = {
    "advisor": "advisor",
    "adviser": "advisor",
    "advisory": "advisor",
    "consultant": "consultant",
    "emeritus": "emeritus",
    "honorary": "honorary",
}

# Source → base quality score
_SOURCE_QUALITY: dict[str, int] = {
    "990_filing": 85,
    "pdf_analysis": 75,
    "web_data": 60,
    "board_members": 50,
}
_DEFAULT_QUALITY = 40


class PeopleETL:
    """Extract people from network_memberships, transform names, load into
    the normalised people + organization_roles tables."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.normalizer = NameNormalizer()

    # ------------------------------------------------------------------
    # DDL
    # ------------------------------------------------------------------

    def ensure_tables(self) -> None:
        """Create the people and organization_roles tables if they do not exist."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS people (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    normalized_name TEXT    NOT NULL,
                    original_name   TEXT    NOT NULL,
                    name_hash       TEXT    UNIQUE,
                    first_name      TEXT,
                    last_name       TEXT,
                    middle_name     TEXT,
                    prefix          TEXT,
                    suffix          TEXT,
                    biography       TEXT,
                    linkedin_url    TEXT,
                    personal_website TEXT,
                    data_quality_score INTEGER DEFAULT 50,
                    confidence_level   REAL    DEFAULT 0.5,
                    source_count    INTEGER DEFAULT 1,
                    created_at      TIMESTAMP,
                    updated_at      TIMESTAMP,
                    last_verified_at TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS organization_roles (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id           INTEGER NOT NULL REFERENCES people(id),
                    organization_ein    TEXT    NOT NULL,
                    organization_name   TEXT    NOT NULL,
                    title               TEXT    NOT NULL,
                    position_type       TEXT    DEFAULT 'board',
                    position_category   TEXT,
                    start_date          DATE,
                    end_date            DATE,
                    is_current          BOOLEAN DEFAULT TRUE,
                    tenure_years        REAL,
                    data_source         TEXT    NOT NULL,
                    source_url          TEXT,
                    filing_year         INTEGER,
                    web_intelligence_id TEXT,
                    verification_status TEXT    DEFAULT 'unverified',
                    quality_score       INTEGER DEFAULT 50,
                    created_at          TIMESTAMP,
                    updated_at          TIMESTAMP,
                    UNIQUE(person_id, organization_ein, title, data_source)
                );
                """
            )
            conn.commit()
            logger.info("Ensured people and organization_roles tables exist.")
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Name parsing
    # ------------------------------------------------------------------

    def _parse_name_parts(self, name: str) -> dict[str, str | None]:
        """Parse a display name into component parts.

        Returns dict with keys: first_name, last_name, middle_name, prefix, suffix.
        """
        result: dict[str, str | None] = {
            "first_name": None,
            "last_name": None,
            "middle_name": None,
            "prefix": None,
            "suffix": None,
        }
        if not name or not name.strip():
            return result

        # Strip parenthetical content
        cleaned = re.sub(r"\(.*?\)", "", name).strip()
        # Remove punctuation except hyphens and apostrophes
        cleaned = re.sub(r"[^\w\s\-']", " ", cleaned)
        tokens = cleaned.split()

        if not tokens:
            return result

        # Extract prefix (honorific)
        if tokens[0].lower().rstrip(".") in NameNormalizer.HONORIFICS:
            result["prefix"] = tokens[0]
            tokens = tokens[1:]

        if not tokens:
            return result

        # Extract suffix from end
        if tokens[-1].lower().rstrip(".") in NameNormalizer.SUFFIXES:
            result["suffix"] = tokens[-1]
            tokens = tokens[:-1]

        if not tokens:
            return result

        # Assign first / middle / last
        if len(tokens) == 1:
            result["first_name"] = tokens[0]
        elif len(tokens) == 2:
            result["first_name"] = tokens[0]
            result["last_name"] = tokens[1]
        else:
            result["first_name"] = tokens[0]
            result["last_name"] = tokens[-1]
            result["middle_name"] = " ".join(tokens[1:-1])

        return result

    # ------------------------------------------------------------------
    # Position classification
    # ------------------------------------------------------------------

    def _classify_position(self, title: str) -> tuple[str, str]:
        """Return (position_type, position_category) for a given title string.

        position_type:     board | executive | staff | advisory
        position_category: specific role (chair, ceo, treasurer, …)
        """
        if not title:
            return ("board", "member")

        lower = title.lower().strip()

        # Check advisory first (least common, avoids false positives)
        for keyword, category in _ADVISORY_KEYWORDS.items():
            if keyword in lower:
                return ("advisory", category)

        # Executive
        for keyword, category in _EXECUTIVE_KEYWORDS.items():
            if keyword in lower:
                return ("executive", category)

        # Board
        for keyword, category in _BOARD_KEYWORDS.items():
            if keyword in lower:
                return ("board", category)

        # Staff
        for keyword, category in _STAFF_KEYWORDS.items():
            if keyword in lower:
                return ("staff", category)

        # Fallback
        return ("board", "member")

    # ------------------------------------------------------------------
    # Quality scoring
    # ------------------------------------------------------------------

    def _calculate_quality_score(
        self, source: str, has_title: bool, has_ein: bool
    ) -> int:
        """Return a quality score in 1–100 based on source and data completeness."""
        base = _SOURCE_QUALITY.get(source, _DEFAULT_QUALITY)
        if has_title:
            base += 10
        if has_ein:
            base += 5
        return min(max(base, 1), 100)

    # ------------------------------------------------------------------
    # Main migration
    # ------------------------------------------------------------------

    def migrate_from_memberships(self) -> dict[str, int]:
        """Read all rows from network_memberships and upsert into people + organization_roles.

        Returns:
            dict with keys: people_created, people_updated, roles_created,
            roles_updated, errors
        """
        stats: dict[str, int] = {
            "people_created": 0,
            "people_updated": 0,
            "roles_created": 0,
            "roles_updated": 0,
            "errors": 0,
        }

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            # Check that source table exists
            table_check = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='network_memberships'"
            ).fetchone()
            if not table_check:
                logger.warning("network_memberships table does not exist — nothing to migrate.")
                return stats

            rows = conn.execute(
                "SELECT id, person_hash, display_name, org_ein, org_name, "
                "org_type, profile_id, source, title, created_at, updated_at "
                "FROM network_memberships"
            ).fetchall()

            logger.info("Starting migration of %d network_memberships rows.", len(rows))

            now = datetime.now(timezone.utc).isoformat()

            for row in rows:
                try:
                    self._process_membership_row(conn, row, now, stats)
                except Exception:
                    logger.exception(
                        "Error processing membership id=%s name=%s",
                        row["id"],
                        row["display_name"],
                    )
                    stats["errors"] += 1

            conn.commit()
            logger.info(
                "Migration complete — people created=%d updated=%d, "
                "roles created=%d updated=%d, errors=%d",
                stats["people_created"],
                stats["people_updated"],
                stats["roles_created"],
                stats["roles_updated"],
                stats["errors"],
            )
        finally:
            conn.close()

        return stats

    def _process_membership_row(
        self,
        conn: sqlite3.Connection,
        row: sqlite3.Row,
        now: str,
        stats: dict[str, int],
    ) -> None:
        """Upsert a single network_memberships row into people + organization_roles."""
        display_name: str = row["display_name"] or ""
        if not display_name.strip():
            logger.debug("Skipping membership id=%s with empty display_name.", row["id"])
            stats["errors"] += 1
            return

        name_hash = self.normalizer.person_hash(display_name)
        normalized = self.normalizer.normalize(display_name)
        parts = self._parse_name_parts(display_name)
        source: str = row["source"] or "unknown"
        title: str = row["title"] or ""
        org_ein: str = row["org_ein"] or ""
        org_name: str = row["org_name"] or ""
        quality = self._calculate_quality_score(source, bool(title), bool(org_ein))

        # ---- Upsert into people ----
        existing = conn.execute(
            "SELECT id, source_count FROM people WHERE name_hash = ?", (name_hash,)
        ).fetchone()

        if existing:
            person_id = existing["id"]
            new_source_count = (existing["source_count"] or 1) + 1
            conn.execute(
                "UPDATE people SET source_count = ?, updated_at = ?, "
                "data_quality_score = MAX(data_quality_score, ?) WHERE id = ?",
                (new_source_count, now, quality, person_id),
            )
            stats["people_updated"] += 1
        else:
            cursor = conn.execute(
                "INSERT INTO people "
                "(normalized_name, original_name, name_hash, first_name, last_name, "
                "middle_name, prefix, suffix, data_quality_score, confidence_level, "
                "source_count, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    normalized,
                    display_name,
                    name_hash,
                    parts["first_name"],
                    parts["last_name"],
                    parts["middle_name"],
                    parts["prefix"],
                    parts["suffix"],
                    quality,
                    0.5,
                    1,
                    now,
                    now,
                ),
            )
            person_id = cursor.lastrowid
            stats["people_created"] += 1

        # ---- Upsert into organization_roles ----
        if not org_name:
            # Cannot create a role without an organisation name
            return

        position_type, position_category = self._classify_position(title)
        role_title = title if title else position_category

        existing_role = conn.execute(
            "SELECT id FROM organization_roles "
            "WHERE person_id = ? AND organization_ein = ? AND title = ? AND data_source = ?",
            (person_id, org_ein, role_title, source),
        ).fetchone()

        if existing_role:
            conn.execute(
                "UPDATE organization_roles SET organization_name = ?, position_type = ?, "
                "position_category = ?, quality_score = ?, updated_at = ? WHERE id = ?",
                (
                    org_name,
                    position_type,
                    position_category,
                    quality,
                    now,
                    existing_role["id"],
                ),
            )
            stats["roles_updated"] += 1
        else:
            conn.execute(
                "INSERT INTO organization_roles "
                "(person_id, organization_ein, organization_name, title, "
                "position_type, position_category, is_current, data_source, "
                "quality_score, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    person_id,
                    org_ein,
                    org_name,
                    role_title,
                    position_type,
                    position_category,
                    True,
                    source,
                    quality,
                    now,
                    now,
                ),
            )
            stats["roles_created"] += 1

    # ------------------------------------------------------------------
    # 990 officer ingestion
    # ------------------------------------------------------------------

    def ingest_from_990_officers(
        self,
        ein: str,
        org_name: str,
        officers: list[dict[str, Any]],
        filing_year: int,
    ) -> dict[str, int]:
        """Ingest officer/director data extracted from a 990 XML filing.

        Each officer dict is expected to contain:
            name, title, hours_per_week, compensation,
            is_officer, is_director, is_trustee, is_key_employee

        Returns:
            dict with keys: people_created, people_updated, roles_created,
            roles_updated, errors
        """
        stats: dict[str, int] = {
            "people_created": 0,
            "people_updated": 0,
            "roles_created": 0,
            "roles_updated": 0,
            "errors": 0,
        }

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        now = datetime.now(timezone.utc).isoformat()
        source = "990_filing"

        try:
            for officer in officers:
                try:
                    self._process_officer(conn, officer, ein, org_name, filing_year, source, now, stats)
                except Exception:
                    logger.exception(
                        "Error processing officer %s for EIN %s",
                        officer.get("name", "<unknown>"),
                        ein,
                    )
                    stats["errors"] += 1

            conn.commit()
            logger.info(
                "990 officer ingestion for EIN %s year %d — people created=%d "
                "updated=%d, roles created=%d updated=%d, errors=%d",
                ein,
                filing_year,
                stats["people_created"],
                stats["people_updated"],
                stats["roles_created"],
                stats["roles_updated"],
                stats["errors"],
            )
        finally:
            conn.close()

        return stats

    def _process_officer(
        self,
        conn: sqlite3.Connection,
        officer: dict[str, Any],
        ein: str,
        org_name: str,
        filing_year: int,
        source: str,
        now: str,
        stats: dict[str, int],
    ) -> None:
        """Upsert a single 990 officer into people + organization_roles."""
        name: str = officer.get("name", "")
        if not name or not name.strip():
            stats["errors"] += 1
            return

        title: str = officer.get("title", "")
        name_hash = self.normalizer.person_hash(name)
        normalized = self.normalizer.normalize(name)
        parts = self._parse_name_parts(name)
        quality = self._calculate_quality_score(source, bool(title), bool(ein))

        # Derive position type from 990 boolean flags
        position_type, position_category = self._classify_position_from_990(officer, title)

        # ---- Upsert people ----
        existing = conn.execute(
            "SELECT id, source_count FROM people WHERE name_hash = ?", (name_hash,)
        ).fetchone()

        if existing:
            person_id = existing["id"]
            new_source_count = (existing["source_count"] or 1) + 1
            conn.execute(
                "UPDATE people SET source_count = ?, updated_at = ?, "
                "data_quality_score = MAX(data_quality_score, ?) WHERE id = ?",
                (new_source_count, now, quality, person_id),
            )
            stats["people_updated"] += 1
        else:
            cursor = conn.execute(
                "INSERT INTO people "
                "(normalized_name, original_name, name_hash, first_name, last_name, "
                "middle_name, prefix, suffix, data_quality_score, confidence_level, "
                "source_count, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    normalized,
                    name,
                    name_hash,
                    parts["first_name"],
                    parts["last_name"],
                    parts["middle_name"],
                    parts["prefix"],
                    parts["suffix"],
                    quality,
                    0.7,  # higher confidence for 990 data
                    1,
                    now,
                    now,
                ),
            )
            person_id = cursor.lastrowid
            stats["people_created"] += 1

        # ---- Upsert organization_roles ----
        role_title = title if title else position_category

        existing_role = conn.execute(
            "SELECT id FROM organization_roles "
            "WHERE person_id = ? AND organization_ein = ? AND title = ? AND data_source = ?",
            (person_id, ein, role_title, source),
        ).fetchone()

        if existing_role:
            conn.execute(
                "UPDATE organization_roles SET organization_name = ?, position_type = ?, "
                "position_category = ?, filing_year = ?, quality_score = ?, updated_at = ? "
                "WHERE id = ?",
                (org_name, position_type, position_category, filing_year, quality, now, existing_role["id"]),
            )
            stats["roles_updated"] += 1
        else:
            conn.execute(
                "INSERT INTO organization_roles "
                "(person_id, organization_ein, organization_name, title, "
                "position_type, position_category, is_current, data_source, "
                "filing_year, quality_score, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    person_id,
                    ein,
                    org_name,
                    role_title,
                    position_type,
                    position_category,
                    True,
                    source,
                    filing_year,
                    quality,
                    now,
                    now,
                ),
            )
            stats["roles_created"] += 1

    @staticmethod
    def _classify_position_from_990(
        officer: dict[str, Any], title: str
    ) -> tuple[str, str]:
        """Derive position type/category using 990 boolean flags plus title text."""
        is_officer = officer.get("is_officer", False)
        is_director = officer.get("is_director", False)
        is_trustee = officer.get("is_trustee", False)
        is_key_employee = officer.get("is_key_employee", False)

        # Title-based classification takes priority when specific
        lower_title = (title or "").lower()
        for keyword, category in _EXECUTIVE_KEYWORDS.items():
            if keyword in lower_title:
                return ("executive", category)

        # Fall back to boolean flags
        if is_officer and not is_director and not is_trustee:
            # Try to classify from title, otherwise generic officer
            for keyword, category in _BOARD_KEYWORDS.items():
                if keyword in lower_title:
                    return ("board", category)
            return ("executive", "officer")

        if is_director or is_trustee:
            if is_trustee:
                return ("board", "trustee")
            return ("board", "member")

        if is_key_employee:
            return ("staff", "key_employee")

        # Final fallback: try title keywords
        for keyword, category in _BOARD_KEYWORDS.items():
            if keyword in lower_title:
                return ("board", category)

        return ("board", "member")

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        """Return aggregate counts from people and organization_roles tables.

        Returns dict with: total_people, total_roles, by_source, by_position_type
        """
        result: dict[str, Any] = {
            "total_people": 0,
            "total_roles": 0,
            "by_source": {},
            "by_position_type": {},
        }

        conn = sqlite3.connect(self.db_path)
        try:
            # Check tables exist before querying
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }

            if "people" in tables:
                row = conn.execute("SELECT COUNT(*) FROM people").fetchone()
                result["total_people"] = row[0] if row else 0

            if "organization_roles" in tables:
                row = conn.execute("SELECT COUNT(*) FROM organization_roles").fetchone()
                result["total_roles"] = row[0] if row else 0

                for source_row in conn.execute(
                    "SELECT data_source, COUNT(*) as cnt FROM organization_roles "
                    "GROUP BY data_source"
                ).fetchall():
                    result["by_source"][source_row[0]] = source_row[1]

                for pt_row in conn.execute(
                    "SELECT position_type, COUNT(*) as cnt FROM organization_roles "
                    "GROUP BY position_type"
                ).fetchall():
                    result["by_position_type"][pt_row[0]] = pt_row[1]
        finally:
            conn.close()

        return result
