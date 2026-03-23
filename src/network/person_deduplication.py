"""
PersonDeduplicationService — find and merge duplicate person records using
fuzzy name matching and shared-organization signals.

All matching runs against the local SQLite `people` and `organization_roles`
tables.  No external libraries are required beyond the Python standard library
and the project's own NameNormalizer.
"""

import logging
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from src.network.name_normalizer import NameNormalizer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _similarity(a: str, b: str) -> float:
    """Character-level similarity ratio (0.0–1.0) inspired by SequenceMatcher.

    Uses a simple longest-common-subsequence approach to avoid pulling in any
    external dependency.  Adequate for short strings such as person names.
    """
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0

    # Build the LCS length via dynamic programming (space-optimised to two
    # rows since we only need the final length).
    len_a, len_b = len(a), len(b)
    prev = [0] * (len_b + 1)
    curr = [0] * (len_b + 1)
    for i in range(1, len_a + 1):
        for j in range(1, len_b + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, [0] * (len_b + 1)

    lcs_len = prev[len_b]
    # Dice-style coefficient: 2 * |LCS| / (|a| + |b|)
    return (2.0 * lcs_len) / (len_a + len_b)


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------

class PersonDeduplicationService:
    """Find and merge duplicate person records in the people table."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._normalizer = NameNormalizer()

    # -- connection helper ---------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # -- public API ----------------------------------------------------------

    def find_duplicates(
        self,
        min_confidence: float = 0.6,
        limit: int = 100,
    ) -> list[dict]:
        """Return potential duplicate pairs sorted by confidence descending.

        Each entry:
            {person_a_id, person_a_name, person_b_id, person_b_name,
             confidence, match_reasons: list[str], shared_orgs: list[str]}
        """
        conn = self._connect()
        try:
            candidates: dict[tuple[int, int], dict] = {}

            self._find_exact_normalized(conn, candidates)
            self._find_last_name_first_initial(conn, candidates)
            self._find_fuzzy_similar(conn, candidates)
            self._apply_shared_org_boost(conn, candidates)

            results = [
                v for v in candidates.values()
                if v["confidence"] >= min_confidence
            ]
            results.sort(key=lambda r: r["confidence"], reverse=True)
            return results[:limit]
        finally:
            conn.close()

    def merge_people(
        self,
        keep_id: int,
        merge_id: int,
        merged_by: str = "system",
    ) -> dict:
        """Merge *merge_id* into *keep_id* and delete the merged person.

        Returns ``{success, roles_transferred, conflicts_resolved}``.
        """
        conn = self._connect()
        try:
            self._ensure_merge_history_table(conn)

            kept = conn.execute(
                "SELECT * FROM people WHERE id = ?", (keep_id,)
            ).fetchone()
            merged = conn.execute(
                "SELECT * FROM people WHERE id = ?", (merge_id,)
            ).fetchone()

            if not kept or not merged:
                logger.warning(
                    "Merge aborted: one or both person IDs do not exist "
                    "(keep=%s, merge=%s)", keep_id, merge_id,
                )
                return {
                    "success": False,
                    "roles_transferred": 0,
                    "conflicts_resolved": 0,
                }

            roles_transferred = 0
            conflicts_resolved = 0

            # Fetch roles belonging to the merged person
            merge_roles = conn.execute(
                "SELECT * FROM organization_roles WHERE person_id = ?",
                (merge_id,),
            ).fetchall()

            for role in merge_roles:
                # Check for a conflicting role on the kept person at the same
                # org + title combination (UNIQUE constraint proxy).
                conflict = conn.execute(
                    """
                    SELECT id, quality_score FROM organization_roles
                    WHERE person_id = ? AND organization_ein = ? AND title = ?
                    """,
                    (keep_id, role["organization_ein"], role["title"]),
                ).fetchone()

                if conflict:
                    # Keep whichever row has the higher quality_score.
                    merge_quality = role["quality_score"] if role["quality_score"] is not None else 0.0
                    kept_quality = conflict["quality_score"] if conflict["quality_score"] is not None else 0.0

                    if merge_quality > kept_quality:
                        conn.execute(
                            "DELETE FROM organization_roles WHERE id = ?",
                            (conflict["id"],),
                        )
                        conn.execute(
                            "UPDATE organization_roles SET person_id = ? WHERE id = ?",
                            (keep_id, role["id"]),
                        )
                    else:
                        conn.execute(
                            "DELETE FROM organization_roles WHERE id = ?",
                            (role["id"],),
                        )
                    conflicts_resolved += 1
                else:
                    conn.execute(
                        "UPDATE organization_roles SET person_id = ? WHERE id = ?",
                        (keep_id, role["id"]),
                    )
                    roles_transferred += 1

            # Update aggregated fields on the kept person
            new_source_count = (kept["source_count"] or 0) + (merged["source_count"] or 0)
            new_quality = max(
                kept["data_quality_score"] or 0.0,
                merged["data_quality_score"] or 0.0,
            )
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                UPDATE people
                SET source_count = ?,
                    data_quality_score = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (new_source_count, new_quality, now, keep_id),
            )

            # Record merge in history
            conn.execute(
                """
                INSERT INTO person_merge_history
                    (kept_person_id, merged_person_id, merged_person_name,
                     confidence_score, merge_reason, merged_by, merged_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    keep_id,
                    merge_id,
                    merged["original_name"] or merged["normalized_name"],
                    None,
                    f"Manual merge by {merged_by}",
                    merged_by,
                    now,
                ),
            )

            # Delete the merged person
            conn.execute("DELETE FROM people WHERE id = ?", (merge_id,))

            conn.commit()
            logger.info(
                "Merged person %s into %s — %d roles transferred, %d conflicts resolved",
                merge_id, keep_id, roles_transferred, conflicts_resolved,
            )
            return {
                "success": True,
                "roles_transferred": roles_transferred,
                "conflicts_resolved": conflicts_resolved,
            }
        except Exception:
            conn.rollback()
            logger.exception("Failed to merge person %s into %s", merge_id, keep_id)
            return {
                "success": False,
                "roles_transferred": 0,
                "conflicts_resolved": 0,
            }
        finally:
            conn.close()

    def auto_merge(self, min_confidence: float = 0.90) -> dict:
        """Automatically merge all pairs above *min_confidence*.

        Returns ``{pairs_found, pairs_merged, errors}``.
        """
        pairs = self.find_duplicates(min_confidence=min_confidence, limit=500)
        pairs_merged = 0
        errors: list[str] = []
        # Track IDs that have already been merged away so we don't attempt to
        # merge a record that no longer exists.
        merged_away: set[int] = set()

        for pair in pairs:
            a_id = pair["person_a_id"]
            b_id = pair["person_b_id"]

            if a_id in merged_away or b_id in merged_away:
                continue

            result = self.merge_people(keep_id=a_id, merge_id=b_id, merged_by="auto_merge")
            if result["success"]:
                pairs_merged += 1
                merged_away.add(b_id)
            else:
                errors.append(f"Failed to merge {b_id} into {a_id}")

        logger.info(
            "Auto-merge complete: %d pairs found, %d merged, %d errors",
            len(pairs), pairs_merged, len(errors),
        )
        return {
            "pairs_found": len(pairs),
            "pairs_merged": pairs_merged,
            "errors": errors,
        }

    def get_merge_history(self, limit: int = 50) -> list[dict]:
        """Return recent merge-history rows, newest first."""
        conn = self._connect()
        try:
            self._ensure_merge_history_table(conn)
            rows = conn.execute(
                """
                SELECT * FROM person_merge_history
                ORDER BY merged_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # -- private matching strategies -----------------------------------------

    def _find_exact_normalized(
        self,
        conn: sqlite3.Connection,
        candidates: dict[tuple[int, int], dict],
    ) -> None:
        """Strategy: identical normalized_name but different id."""
        rows = conn.execute(
            """
            SELECT a.id   AS a_id, a.original_name AS a_name,
                   b.id   AS b_id, b.original_name AS b_name,
                   a.normalized_name
            FROM people a
            JOIN people b
              ON a.normalized_name = b.normalized_name
             AND a.id < b.id
            """
        ).fetchall()

        for r in rows:
            key = (r["a_id"], r["b_id"])
            entry = candidates.setdefault(key, self._empty_pair(r))
            entry["confidence"] = max(entry["confidence"], 0.95)
            entry["match_reasons"].append("exact_normalized_name")

    def _find_last_name_first_initial(
        self,
        conn: sqlite3.Connection,
        candidates: dict[tuple[int, int], dict],
    ) -> None:
        """Strategy: same last_name and first letter of first_name."""
        rows = conn.execute(
            """
            SELECT a.id   AS a_id, a.original_name AS a_name,
                   b.id   AS b_id, b.original_name AS b_name
            FROM people a
            JOIN people b
              ON a.last_name = b.last_name
             AND a.last_name IS NOT NULL
             AND a.last_name != ''
             AND a.first_name IS NOT NULL
             AND b.first_name IS NOT NULL
             AND a.first_name != ''
             AND b.first_name != ''
             AND SUBSTR(a.first_name, 1, 1) = SUBSTR(b.first_name, 1, 1)
             AND a.id < b.id
            """
        ).fetchall()

        for r in rows:
            key = (r["a_id"], r["b_id"])
            entry = candidates.setdefault(key, self._empty_pair(r))
            # Only set 0.7 if nothing higher is already recorded
            entry["confidence"] = max(entry["confidence"], 0.70)
            entry["match_reasons"].append("last_name_first_initial")

    def _find_fuzzy_similar(
        self,
        conn: sqlite3.Connection,
        candidates: dict[tuple[int, int], dict],
    ) -> None:
        """Strategy: character-level similarity on normalized names > 0.85.

        To keep the query set manageable we restrict to pairs sharing the same
        first two characters of last_name (a blocking key).
        """
        rows = conn.execute(
            """
            SELECT a.id AS a_id, a.original_name AS a_name,
                   a.normalized_name AS a_norm,
                   b.id AS b_id, b.original_name AS b_name,
                   b.normalized_name AS b_norm
            FROM people a
            JOIN people b
              ON a.id < b.id
             AND a.last_name IS NOT NULL
             AND b.last_name IS NOT NULL
             AND a.last_name != ''
             AND b.last_name != ''
             AND SUBSTR(a.last_name, 1, 2) = SUBSTR(b.last_name, 1, 2)
            """
        ).fetchall()

        for r in rows:
            sim = _similarity(r["a_norm"], r["b_norm"])
            if sim > 0.85:
                key = (r["a_id"], r["b_id"])
                entry = candidates.setdefault(key, self._empty_pair(r))
                entry["confidence"] = max(entry["confidence"], 0.65)
                entry["match_reasons"].append(
                    f"fuzzy_similarity({sim:.2f})"
                )

    def _apply_shared_org_boost(
        self,
        conn: sqlite3.Connection,
        candidates: dict[tuple[int, int], dict],
    ) -> None:
        """Boost confidence by +0.15 for pairs sharing an organization."""
        if not candidates:
            return

        for key, entry in candidates.items():
            a_id, b_id = key
            shared = conn.execute(
                """
                SELECT DISTINCT ra.organization_ein, ra.organization_name
                FROM organization_roles ra
                JOIN organization_roles rb
                  ON ra.organization_ein = rb.organization_ein
                WHERE ra.person_id = ? AND rb.person_id = ?
                """,
                (a_id, b_id),
            ).fetchall()

            if shared:
                entry["confidence"] = min(entry["confidence"] + 0.15, 1.0)
                entry["match_reasons"].append("shared_organization")
                entry["shared_orgs"] = [
                    r["organization_name"] or r["organization_ein"]
                    for r in shared
                ]

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _empty_pair(row: sqlite3.Row) -> dict:
        return {
            "person_a_id": row["a_id"],
            "person_a_name": row["a_name"],
            "person_b_id": row["b_id"],
            "person_b_name": row["b_name"],
            "confidence": 0.0,
            "match_reasons": [],
            "shared_orgs": [],
        }

    @staticmethod
    def _ensure_merge_history_table(conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS person_merge_history (
                merge_id_pk       INTEGER PRIMARY KEY AUTOINCREMENT,
                kept_person_id    INTEGER NOT NULL,
                merged_person_id  INTEGER NOT NULL,
                merged_person_name TEXT,
                confidence_score  REAL,
                merge_reason      TEXT,
                merged_by         TEXT NOT NULL DEFAULT 'system',
                merged_at         TEXT NOT NULL
            )
            """
        )
