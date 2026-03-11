"""
NetworkGraphBuilder — ingest board/leadership people into network_memberships.
Side-effect only; no AI calls.
"""

import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional

from .name_normalizer import NameNormalizer

logger = logging.getLogger(__name__)


class NetworkGraphBuilder:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.normalizer = NameNormalizer()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # Seeker (profile board members)
    # ------------------------------------------------------------------

    def ingest_profile_board_members(
        self,
        profile_id: str,
        board_members: list,
        org_name: str = "Seeker Organization",
    ) -> int:
        """
        Upsert seeker people from profiles.board_members into network_memberships.
        org_ein = None, org_type = 'seeker', source = 'board_members'.
        Returns count of new rows inserted.
        """
        if not board_members:
            return 0

        inserted = 0
        now = self._now()

        with self._conn() as conn:
            cursor = conn.cursor()
            for member in board_members:
                name = self._extract_name(member)
                if not name:
                    continue
                title = self._extract_title(member)
                ph = self.normalizer.person_hash(name)
                mem_id = self.normalizer.membership_id(name, f"seeker_{profile_id}")
                display = self._best_display(name)

                cursor.execute(
                    """
                    INSERT INTO network_memberships
                        (id, person_hash, display_name, org_ein, org_name, org_type,
                         profile_id, source, title, created_at, updated_at)
                    VALUES (?, ?, ?, NULL, ?, 'seeker', ?, 'board_members', ?, ?, ?)
                    ON CONFLICT(person_hash, org_ein) DO UPDATE SET
                        display_name = excluded.display_name,
                        title = excluded.title,
                        updated_at = excluded.updated_at
                    """,
                    (mem_id, ph, display, org_name, profile_id, title, now, now),
                )
                if cursor.rowcount and cursor.lastrowid:
                    inserted += 1

            conn.commit()

        logger.info(
            f"[GraphBuilder] Ingested seeker board for profile {profile_id}: "
            f"{len(board_members)} members, {inserted} new rows"
        )
        return inserted

    # ------------------------------------------------------------------
    # Funder (ein_intelligence)
    # ------------------------------------------------------------------

    def ingest_funder_ein(
        self,
        ein: str,
        org_name: str,
        ein_intelligence: dict,
    ) -> int:
        """
        Upsert funder people from ein_intelligence into network_memberships.
        Reads web_data.leadership + pdf_analyses[*].officers_and_directors.
        Returns count of new rows inserted.
        """
        if not ein or not ein_intelligence:
            return 0

        people: list[dict] = []

        # Web data leadership
        web_data = ein_intelligence.get("web_data") or {}
        if isinstance(web_data, dict):
            # Direct leadership key
            for ldr in (web_data.get("leadership") or []):
                if isinstance(ldr, dict):
                    people.append({**ldr, "_source": "web_data"})
            # Nested under grant_funder_intelligence key
            gfi = web_data.get("grant_funder_intelligence") or {}
            if isinstance(gfi, dict):
                for ldr in (gfi.get("leadership") or []):
                    if isinstance(ldr, dict):
                        people.append({**ldr, "_source": "web_data"})

        # PDF analyses — officers_and_directors
        pdf_analyses = ein_intelligence.get("pdf_analyses") or {}
        if isinstance(pdf_analyses, dict):
            for _key, analysis in pdf_analyses.items():
                if not isinstance(analysis, dict):
                    continue
                for officer in (analysis.get("officers_and_directors") or []):
                    if isinstance(officer, dict):
                        people.append({**officer, "_source": "pdf_analysis"})

        if not people:
            return 0

        inserted = 0
        now = self._now()

        with self._conn() as conn:
            cursor = conn.cursor()
            for person in people:
                name = self._extract_name(person)
                if not name:
                    continue
                source = person.get("_source", "web_data")
                title = self._extract_title(person)
                ph = self.normalizer.person_hash(name)
                mem_id = self.normalizer.membership_id(name, ein)
                display = self._best_display(name)

                cursor.execute(
                    """
                    INSERT INTO network_memberships
                        (id, person_hash, display_name, org_ein, org_name, org_type,
                         profile_id, source, title, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 'funder', NULL, ?, ?, ?, ?)
                    ON CONFLICT(person_hash, org_ein) DO UPDATE SET
                        display_name = excluded.display_name,
                        title = excluded.title,
                        source = excluded.source,
                        updated_at = excluded.updated_at
                    """,
                    (mem_id, ph, display, ein, org_name, source, title, now, now),
                )
                if cursor.rowcount:
                    inserted += 1

            conn.commit()

        logger.info(
            f"[GraphBuilder] Ingested funder EIN {ein} ({org_name}): "
            f"{len(people)} people, {inserted} new/updated rows"
        )
        return inserted

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_name(self, obj) -> str:
        if isinstance(obj, str):
            return obj.strip()
        if isinstance(obj, dict):
            for key in ("name", "person_name", "full_name", "officer_name"):
                if obj.get(key):
                    return str(obj[key]).strip()
        return ""

    def _extract_title(self, obj) -> Optional[str]:
        if isinstance(obj, dict):
            for key in ("title", "role", "position", "officer_title"):
                if obj.get(key):
                    return str(obj[key]).strip()
        return None

    def _best_display(self, name: str) -> str:
        """Title-case the raw name for display."""
        return " ".join(w.capitalize() for w in name.split())
