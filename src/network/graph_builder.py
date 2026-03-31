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
                    ON CONFLICT(id) DO UPDATE SET
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
                    ON CONFLICT(id) DO UPDATE SET
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
    # Bulk harvest from cache
    # ------------------------------------------------------------------

    def ingest_all_funders_from_cache(self, profile_id: str, opportunity_limit: int | None = None) -> dict:
        """
        Batch-ingest all funder leadership data from ein_intelligence into
        network_memberships for every funder EIN linked to this profile's
        opportunities.  Also ingests the seeker profile's board_members.
        Cost: $0.00 — pure DB reads.
        Returns: {eins_processed, people_added, people_already_known, graph_total_size,
                  seeker_people_ingested, funders_with_data, funders_without_data}
        """
        import json as _json

        with self._conn() as conn:
            # 1. Distinct EINs + org names for this profile (top-N by score if limited)
            if opportunity_limit:
                raw = conn.execute(
                    "SELECT ein, organization_name FROM opportunities "
                    "WHERE profile_id = ? AND ein IS NOT NULL AND ein != '' "
                    "ORDER BY COALESCE(overall_score, 0) DESC "
                    "LIMIT ?",
                    (profile_id, opportunity_limit),
                ).fetchall()
                seen: set = set()
                rows = []
                for r in raw:
                    if r["ein"] not in seen:
                        seen.add(r["ein"])
                        rows.append(r)
            else:
                rows = conn.execute(
                    "SELECT DISTINCT ein, organization_name FROM opportunities "
                    "WHERE profile_id = ? AND ein IS NOT NULL AND ein != ''",
                    (profile_id,),
                ).fetchall()

            # 2. Seeker board members
            profile_row = conn.execute(
                "SELECT board_members, name FROM profiles WHERE id = ?",
                (profile_id,),
            ).fetchone()

        seeker_people_ingested = 0
        if profile_row:
            bm_raw = profile_row["board_members"] if profile_row else None
            org_name = profile_row["name"] if profile_row else "Seeker Organization"
            board_members = []
            if bm_raw:
                try:
                    board_members = _json.loads(bm_raw) if isinstance(bm_raw, str) else bm_raw
                except Exception:
                    board_members = []
            if board_members:
                seeker_people_ingested = self.ingest_profile_board_members(
                    profile_id, board_members, org_name
                )

        eins_processed = 0
        people_added = 0
        funders_with_data: list[dict] = []
        funders_without_data: list[dict] = []

        with self._conn() as conn:
            # Build a map: org_ein → max(updated_at) of rows already in graph
            existing_rows = conn.execute(
                "SELECT org_ein, MAX(updated_at) as last_ingested "
                "FROM network_memberships WHERE org_ein IS NOT NULL GROUP BY org_ein"
            ).fetchall()
            already_ingested: dict[str, str] = {
                r["org_ein"]: r["last_ingested"] for r in existing_rows
            }

            for row in rows:
                ein = row["ein"]
                org_name = row["organization_name"] or ein

                # Load ein_intelligence (only updated_at + data columns)
                ei_row = conn.execute(
                    "SELECT web_data, pdf_analyses, updated_at FROM ein_intelligence WHERE ein = ?",
                    (ein,),
                ).fetchone()

                if not ei_row:
                    funders_without_data.append({"ein": ein, "org_name": org_name})
                    continue

                # Skip if already ingested AND ein_intelligence hasn't been updated since
                last_ingested = already_ingested.get(ein)
                ei_updated = ei_row["updated_at"] or ""
                if last_ingested and ei_updated and ei_updated <= last_ingested:
                    # Data hasn't changed — nothing new to ingest
                    logger.debug(
                        f"[GraphBuilder] Skipping EIN {ein} — already ingested "
                        f"(graph={last_ingested}, intel={ei_updated})"
                    )
                    funders_with_data.append({"ein": ein, "org_name": org_name})
                    eins_processed += 1
                    continue

                ei: dict = {}
                for field in ("web_data", "pdf_analyses"):
                    raw = ei_row[field]
                    if raw and isinstance(raw, str):
                        try:
                            ei[field] = _json.loads(raw)
                        except Exception:
                            ei[field] = {}
                    else:
                        ei[field] = raw or {}

                has_data = bool(
                    (ei.get("web_data") or {}).get("leadership") or
                    (ei.get("web_data") or {}).get("grant_funder_intelligence") or
                    ei.get("pdf_analyses")
                )

                if has_data:
                    added = self.ingest_funder_ein(ein, org_name, ei)
                    people_added += added
                    funders_with_data.append({"ein": ein, "org_name": org_name})
                else:
                    funders_without_data.append({"ein": ein, "org_name": org_name})

                eins_processed += 1

        # Graph total size
        with self._conn() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM network_memberships"
            ).fetchone()[0]

        logger.info(
            f"[GraphBuilder] ingest_all_funders_from_cache profile={profile_id}: "
            f"eins={eins_processed}, added={people_added}, seeker={seeker_people_ingested}, "
            f"total={total}"
        )

        return {
            "eins_processed": eins_processed,
            "people_added": people_added,
            "people_already_known": max(0, eins_processed - people_added),
            "graph_total_size": total,
            "seeker_people_ingested": seeker_people_ingested,
            "funders_with_data": len(funders_with_data),
            "funders_without_data": funders_without_data,
        }

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
