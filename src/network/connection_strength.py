"""
ConnectionStrengthScorer — multi-factor connection strength scoring engine.

Calculates how strong a connection is between two organizations through a
shared person, based on concurrent service, recency, duration overlap,
role proximity, and interaction frequency.  All data comes from the SQLite
tables: people, organization_roles, board_connections, person_influence_metrics.

Pure SQLite operations, no external APIs or AI calls.
"""

import logging
import sqlite3
from datetime import date, datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Factor weights (sum to 1.0)
# ---------------------------------------------------------------------------
WEIGHT_CONCURRENT_SERVICE = 0.30
WEIGHT_RECENCY = 0.25
WEIGHT_DURATION_OVERLAP = 0.15
WEIGHT_ROLE_PROXIMITY = 0.15
WEIGHT_INTERACTION_FREQUENCY = 0.15

# Recency decay: score = max(0, 1 - DECAY_RATE * years_since_end)
RECENCY_DECAY_RATE = 0.15

# Duration overlap cap (years of concurrent service)
DURATION_OVERLAP_CAP = 5.0

# Board-size thresholds for interaction-frequency proxy
SMALL_BOARD_MAX = 7
MEDIUM_BOARD_MAX = 15


class ConnectionStrengthScorer:
    """Score connections between organizations through shared people and
    compute per-person influence metrics."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @staticmethod
    def _parse_date(value) -> Optional[date]:
        """Safely parse a date from various storage formats."""
        if value is None:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        try:
            return date.fromisoformat(str(value)[:10])
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _today() -> date:
        return datetime.now(timezone.utc).date()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # Individual factor calculations
    # ------------------------------------------------------------------

    def _factor_concurrent_service(
        self,
        role1_is_current: bool,
        role1_end_date: Optional[date],
        role2_is_current: bool,
        role2_end_date: Optional[date],
    ) -> float:
        """Both active = 1.0; one ended within 2 years = 0.6; both ended = 0.2."""
        if role1_is_current and role2_is_current:
            return 1.0

        today = self._today()

        if role1_is_current or role2_is_current:
            # One is current, check how recently the other ended
            ended_date = role1_end_date if not role1_is_current else role2_end_date
            if ended_date is not None:
                years_since = (today - ended_date).days / 365.25
                if years_since <= 2.0:
                    return 0.6
            else:
                # No end date recorded but marked not current — treat as recent
                return 0.6
            return 0.2

        # Both ended
        return 0.2

    def _factor_recency(
        self,
        role1_is_current: bool,
        role1_end_date: Optional[date],
        role2_is_current: bool,
        role2_end_date: Optional[date],
    ) -> float:
        """Exponential decay from most recent shared service.
        Current = 1.0; each year past decays by 0.15."""
        if role1_is_current or role2_is_current:
            return 1.0

        today = self._today()
        end_dates = [d for d in (role1_end_date, role2_end_date) if d is not None]
        if not end_dates:
            return 0.5  # no date info — moderate default

        most_recent = max(end_dates)
        years_since = (today - most_recent).days / 365.25
        return max(0.0, 1.0 - RECENCY_DECAY_RATE * years_since)

    @staticmethod
    def _factor_duration_overlap(
        role1_start: Optional[date],
        role1_end: Optional[date],
        role1_is_current: bool,
        role2_start: Optional[date],
        role2_end: Optional[date],
        role2_is_current: bool,
    ) -> float:
        """Years of concurrent service / 5.0, capped at 1.0.
        If no dates available, default 0.5."""
        if role1_start is None or role2_start is None:
            return 0.5

        today = date.today()
        end1 = today if role1_is_current else (role1_end or today)
        end2 = today if role2_is_current else (role2_end or today)

        overlap_start = max(role1_start, role2_start)
        overlap_end = min(end1, end2)

        if overlap_end <= overlap_start:
            return 0.0

        overlap_years = (overlap_end - overlap_start).days / 365.25
        return min(1.0, overlap_years / DURATION_OVERLAP_CAP)

    @staticmethod
    def _factor_role_proximity(position_type1: str, position_type2: str) -> float:
        """Score based on how closely the two role types interact.

        Both executive = 1.0, both board = 0.8, exec+board = 0.6,
        one advisory = 0.4, one staff = 0.3.
        """
        p1 = (position_type1 or "").lower().strip()
        p2 = (position_type2 or "").lower().strip()
        pair = frozenset([p1, p2])

        if p1 == "executive" and p2 == "executive":
            return 1.0
        if p1 == "board" and p2 == "board":
            return 0.8
        if pair == frozenset(["executive", "board"]):
            return 0.6
        if "advisory" in pair:
            return 0.4
        if "staff" in pair:
            return 0.3
        # Unknown or unrecognised types — conservative default
        return 0.3

    def _factor_interaction_frequency(
        self, conn: sqlite3.Connection, org1_ein: str, org2_ein: str
    ) -> float:
        """Proxy via board size — smaller boards imply more interaction."""
        scores = []
        for ein in (org1_ein, org2_ein):
            row = conn.execute(
                "SELECT COUNT(DISTINCT person_id) AS cnt "
                "FROM organization_roles WHERE organization_ein = ?",
                (ein,),
            ).fetchone()
            count = row["cnt"] if row else 0
            if count <= SMALL_BOARD_MAX:
                scores.append(1.0)
            elif count <= MEDIUM_BOARD_MAX:
                scores.append(0.7)
            else:
                scores.append(0.4)
        return sum(scores) / len(scores) if scores else 0.5

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_connection(
        self, person_id: int, org1_ein: str, org2_ein: str
    ) -> dict:
        """Calculate a multi-factor strength score for a connection between
        two organisations through a person.

        Returns::

            {
                total_score: float (0-1),
                factors: {
                    concurrent_service: float,
                    recency: float,
                    duration_overlap: float,
                    role_proximity: float,
                    interaction_frequency: float,
                },
                is_current: bool,
                details: str,
            }
        """
        with self._conn() as conn:
            role1 = conn.execute(
                "SELECT position_type, start_date, end_date, is_current, title "
                "FROM organization_roles "
                "WHERE person_id = ? AND organization_ein = ? "
                "ORDER BY is_current DESC, start_date DESC LIMIT 1",
                (person_id, org1_ein),
            ).fetchone()

            role2 = conn.execute(
                "SELECT position_type, start_date, end_date, is_current, title "
                "FROM organization_roles "
                "WHERE person_id = ? AND organization_ein = ? "
                "ORDER BY is_current DESC, start_date DESC LIMIT 1",
                (person_id, org2_ein),
            ).fetchone()

            if not role1 or not role2:
                logger.warning(
                    "Missing role data for person_id=%d org1=%s org2=%s",
                    person_id, org1_ein, org2_ein,
                )
                return {
                    "total_score": 0.0,
                    "factors": {
                        "concurrent_service": 0.0,
                        "recency": 0.0,
                        "duration_overlap": 0.0,
                        "role_proximity": 0.0,
                        "interaction_frequency": 0.0,
                    },
                    "is_current": False,
                    "details": "Insufficient role data to score connection.",
                }

            r1_current = bool(role1["is_current"])
            r2_current = bool(role2["is_current"])
            r1_start = self._parse_date(role1["start_date"])
            r1_end = self._parse_date(role1["end_date"])
            r2_start = self._parse_date(role2["start_date"])
            r2_end = self._parse_date(role2["end_date"])
            r1_type = role1["position_type"] or ""
            r2_type = role2["position_type"] or ""

            f_concurrent = self._factor_concurrent_service(
                r1_current, r1_end, r2_current, r2_end
            )
            f_recency = self._factor_recency(
                r1_current, r1_end, r2_current, r2_end
            )
            f_duration = self._factor_duration_overlap(
                r1_start, r1_end, r1_current, r2_start, r2_end, r2_current
            )
            f_role = self._factor_role_proximity(r1_type, r2_type)
            f_interaction = self._factor_interaction_frequency(
                conn, org1_ein, org2_ein
            )

            total = (
                WEIGHT_CONCURRENT_SERVICE * f_concurrent
                + WEIGHT_RECENCY * f_recency
                + WEIGHT_DURATION_OVERLAP * f_duration
                + WEIGHT_ROLE_PROXIMITY * f_role
                + WEIGHT_INTERACTION_FREQUENCY * f_interaction
            )

            is_current = r1_current and r2_current

            # Build human-readable details
            parts = []
            if is_current:
                parts.append("Both roles currently active.")
            if r1_start and r2_start:
                overlap_years = (
                    self._factor_duration_overlap(
                        r1_start, r1_end, r1_current,
                        r2_start, r2_end, r2_current,
                    )
                    * DURATION_OVERLAP_CAP
                )
                parts.append(f"Overlap: ~{overlap_years:.1f} yr.")
            parts.append(
                f"Roles: {r1_type or 'unknown'} / {r2_type or 'unknown'}."
            )

            return {
                "total_score": round(total, 4),
                "factors": {
                    "concurrent_service": round(f_concurrent, 4),
                    "recency": round(f_recency, 4),
                    "duration_overlap": round(f_duration, 4),
                    "role_proximity": round(f_role, 4),
                    "interaction_frequency": round(f_interaction, 4),
                },
                "is_current": is_current,
                "details": " ".join(parts),
            }

    def rebuild_board_connections(
        self, profile_id: Optional[str] = None
    ) -> dict:
        """Scan people + organization_roles to find all org pairs connected
        through shared people.  For each pair, calculate the connection
        strength using ``score_connection`` and upsert into board_connections.

        Args:
            profile_id: If given, only process people who have a role at an
                organisation whose name contains this value (substring match).

        Returns::

            {connections_created, connections_updated, total_connections}
        """
        created = 0
        updated = 0
        now = self._now_iso()

        with self._conn() as conn:
            # Find people who serve at 2+ organisations
            if profile_id:
                people_rows = conn.execute(
                    """
                    SELECT DISTINCT r.person_id
                    FROM organization_roles r
                    WHERE r.person_id IN (
                        SELECT person_id
                        FROM organization_roles
                        GROUP BY person_id
                        HAVING COUNT(DISTINCT organization_ein) >= 2
                    )
                    AND EXISTS (
                        SELECT 1 FROM organization_roles r2
                        WHERE r2.person_id = r.person_id
                          AND r2.organization_name LIKE '%' || ? || '%'
                    )
                    """,
                    (profile_id,),
                ).fetchall()
            else:
                people_rows = conn.execute(
                    """
                    SELECT person_id
                    FROM organization_roles
                    GROUP BY person_id
                    HAVING COUNT(DISTINCT organization_ein) >= 2
                    """
                ).fetchall()

            person_ids = [row["person_id"] for row in people_rows]
            logger.info(
                "rebuild_board_connections: %d people with multi-org roles",
                len(person_ids),
            )

            for pid in person_ids:
                orgs = conn.execute(
                    "SELECT DISTINCT organization_ein, organization_name "
                    "FROM organization_roles "
                    "WHERE person_id = ? AND organization_ein IS NOT NULL",
                    (pid,),
                ).fetchall()

                org_list = [
                    (r["organization_ein"], r["organization_name"]) for r in orgs
                ]

                for i in range(len(org_list)):
                    for j in range(i + 1, len(org_list)):
                        ein1, name1 = org_list[i]
                        ein2, name2 = org_list[j]

                        # Normalise ordering so org1_ein < org2_ein
                        if ein1 > ein2:
                            ein1, name1, ein2, name2 = ein2, name2, ein1, name1

                        score_result = self.score_connection(pid, ein1, ein2)

                        existing = conn.execute(
                            "SELECT id FROM board_connections "
                            "WHERE person_id = ? AND org1_ein = ? AND org2_ein = ?",
                            (pid, ein1, ein2),
                        ).fetchone()

                        if existing:
                            conn.execute(
                                """
                                UPDATE board_connections
                                SET connection_strength = ?,
                                    connection_type = ?,
                                    is_current_connection = ?,
                                    connection_end_date = CASE
                                        WHEN ? THEN NULL
                                        ELSE connection_end_date
                                    END,
                                    updated_at = ?
                                WHERE id = ?
                                """,
                                (
                                    score_result["total_score"],
                                    score_result["details"],
                                    score_result["is_current"],
                                    score_result["is_current"],
                                    now,
                                    existing["id"],
                                ),
                            )
                            updated += 1
                        else:
                            conn.execute(
                                """
                                INSERT INTO board_connections
                                    (person_id, org1_ein, org1_name,
                                     org2_ein, org2_name,
                                     connection_strength, connection_type,
                                     is_current_connection,
                                     created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    pid, ein1, name1, ein2, name2,
                                    score_result["total_score"],
                                    score_result["details"],
                                    score_result["is_current"],
                                    now, now,
                                ),
                            )
                            created += 1

            conn.commit()

        total = created + updated
        logger.info(
            "rebuild_board_connections complete: created=%d updated=%d total=%d",
            created, updated, total,
        )
        return {
            "connections_created": created,
            "connections_updated": updated,
            "total_connections": total,
        }

    def compute_person_influence(self, person_id: int) -> dict:
        """Calculate influence metrics for a person and upsert into
        person_influence_metrics.

        Scoring components:

        * **position_influence_score** — weighted sum of executive roles (0.3),
          chair roles (0.25), and total board positions (0.05), capped at 1.0.
        * **network_influence_score** — weighted sum of network reach (0.02),
          bridge connections (0.03), and cluster spanning (0.05), capped at 1.0.
        * **total_influence_score** — 50/50 blend of the two.

        Returns:
            The computed metrics dict.
        """
        with self._conn() as conn:
            roles = conn.execute(
                "SELECT organization_ein, organization_name, position_type, "
                "       title, is_current "
                "FROM organization_roles WHERE person_id = ?",
                (person_id,),
            ).fetchall()

            person_row = conn.execute(
                "SELECT normalized_name FROM people WHERE id = ?",
                (person_id,),
            ).fetchone()
            person_name = person_row["normalized_name"] if person_row else "Unknown"

            total_board_positions = sum(
                1
                for r in roles
                if (r["position_type"] or "").lower()
                in ("board", "executive", "advisory")
            )
            org_eins = set(
                r["organization_ein"] for r in roles if r["organization_ein"]
            )
            total_organizations = len(org_eins)

            executive_positions = sum(
                1 for r in roles
                if (r["position_type"] or "").lower() == "executive"
            )

            _chair_titles = {
                "chair", "chairman", "chairwoman", "chairperson",
                "board chair", "president",
            }
            board_chair_positions = sum(
                1 for r in roles
                if (r["title"] or "").lower().strip() in _chair_titles
            )

            # Network reach: unique orgs reachable through co-serving people
            my_eins = list(org_eins)
            if my_eins:
                ph = ",".join("?" * len(my_eins))
                reach_row = conn.execute(
                    f"""
                    SELECT COUNT(DISTINCT r2.organization_ein) AS reach
                    FROM organization_roles r1
                    JOIN organization_roles r2
                      ON r1.person_id = r2.person_id
                     AND r1.organization_ein != r2.organization_ein
                    WHERE r1.organization_ein IN ({ph})
                      AND r2.organization_ein NOT IN ({ph})
                      AND r1.person_id != ?
                    """,
                    my_eins + my_eins + [person_id],
                ).fetchone()
                network_reach = reach_row["reach"] if reach_row else 0
            else:
                network_reach = 0

            # Bridge connections: distinct people sharing at least one org
            if my_eins:
                ph = ",".join("?" * len(my_eins))
                bridge_row = conn.execute(
                    f"""
                    SELECT COUNT(DISTINCT person_id) AS bridges
                    FROM organization_roles
                    WHERE organization_ein IN ({ph}) AND person_id != ?
                    """,
                    my_eins + [person_id],
                ).fetchone()
                bridge_connections = bridge_row["bridges"] if bridge_row else 0
            else:
                bridge_connections = 0

            # Cluster spanning: number of distinct org pairs bridged
            cluster_spanning = max(
                0, len(my_eins) * (len(my_eins) - 1) // 2
            )

            # Sector diversity (rough proxy from distinct org names)
            unique_names = set(
                r["organization_name"] for r in roles if r["organization_name"]
            )
            sector_diversity = (
                round(min(1.0, len(unique_names) / 10.0), 4)
                if unique_names
                else 0.0
            )

            # Composite scores (all capped at 1.0)
            position_influence_score = round(
                min(
                    1.0,
                    executive_positions * 0.3
                    + board_chair_positions * 0.25
                    + total_board_positions * 0.05,
                ),
                4,
            )
            network_influence_score = round(
                min(
                    1.0,
                    network_reach * 0.02
                    + bridge_connections * 0.03
                    + cluster_spanning * 0.05,
                ),
                4,
            )
            total_influence_score = round(
                0.5 * position_influence_score + 0.5 * network_influence_score,
                4,
            )

            now = self._now_iso()

            existing = conn.execute(
                "SELECT id FROM person_influence_metrics WHERE person_id = ?",
                (person_id,),
            ).fetchone()

            metrics = {
                "person_id": person_id,
                "person_name": person_name,
                "total_board_positions": total_board_positions,
                "total_organizations": total_organizations,
                "executive_positions": executive_positions,
                "board_chair_positions": board_chair_positions,
                "network_reach": network_reach,
                "bridge_connections": bridge_connections,
                "cluster_spanning": cluster_spanning,
                "position_influence_score": position_influence_score,
                "network_influence_score": network_influence_score,
                "total_influence_score": total_influence_score,
                "sector_diversity": sector_diversity,
                "geographic_reach": total_organizations,
            }

            if existing:
                conn.execute(
                    """
                    UPDATE person_influence_metrics
                    SET person_name = ?,
                        total_board_positions = ?,
                        total_organizations = ?,
                        executive_positions = ?,
                        board_chair_positions = ?,
                        network_reach = ?,
                        bridge_connections = ?,
                        cluster_spanning = ?,
                        position_influence_score = ?,
                        network_influence_score = ?,
                        total_influence_score = ?,
                        sector_diversity = ?,
                        geographic_reach = ?,
                        updated_at = ?
                    WHERE person_id = ?
                    """,
                    (
                        person_name,
                        total_board_positions,
                        total_organizations,
                        executive_positions,
                        board_chair_positions,
                        network_reach,
                        bridge_connections,
                        cluster_spanning,
                        position_influence_score,
                        network_influence_score,
                        total_influence_score,
                        sector_diversity,
                        total_organizations,
                        now,
                        person_id,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO person_influence_metrics
                        (person_id, person_name, total_board_positions,
                         total_organizations, executive_positions,
                         board_chair_positions, network_reach,
                         bridge_connections, cluster_spanning,
                         position_influence_score, network_influence_score,
                         total_influence_score, sector_diversity,
                         geographic_reach, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        person_id, person_name,
                        total_board_positions, total_organizations,
                        executive_positions, board_chair_positions,
                        network_reach, bridge_connections, cluster_spanning,
                        position_influence_score, network_influence_score,
                        total_influence_score, sector_diversity,
                        total_organizations,
                        now, now,
                    ),
                )

            conn.commit()

        logger.info(
            "compute_person_influence: person_id=%d influence=%.4f",
            person_id, total_influence_score,
        )
        return metrics

    def rebuild_all_influence_scores(self) -> dict:
        """Recompute influence for all people.

        Returns::

            {people_scored, avg_influence}
        """
        with self._conn() as conn:
            rows = conn.execute("SELECT id FROM people").fetchall()

        person_ids = [r["id"] for r in rows]
        logger.info(
            "rebuild_all_influence_scores: scoring %d people", len(person_ids)
        )

        total_score = 0.0
        scored = 0

        for pid in person_ids:
            try:
                metrics = self.compute_person_influence(pid)
                total_score += metrics["total_influence_score"]
                scored += 1
            except Exception:
                logger.exception(
                    "Failed to compute influence for person_id=%d", pid
                )

        avg = round(total_score / scored, 4) if scored else 0.0
        logger.info(
            "rebuild_all_influence_scores complete: scored=%d avg=%.4f",
            scored, avg,
        )
        return {"people_scored": scored, "avg_influence": avg}

    def get_strongest_connections(
        self, org_ein: str, limit: int = 20
    ) -> list[dict]:
        """Return the strongest connections for an org, sorted by
        connection_strength descending.

        Each dict::

            {
                connected_org_ein, connected_org_name, strength,
                shared_people: [{name, title, role_proximity}],
                is_current,
            }
        """
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT
                    bc.person_id,
                    bc.org1_ein, bc.org1_name,
                    bc.org2_ein, bc.org2_name,
                    bc.connection_strength,
                    bc.is_current_connection
                FROM board_connections bc
                WHERE bc.org1_ein = ? OR bc.org2_ein = ?
                ORDER BY bc.connection_strength DESC
                """,
                (org_ein, org_ein),
            ).fetchall()

            # Aggregate by connected organisation
            org_groups: dict[str, dict] = {}

            for row in rows:
                if row["org1_ein"] == org_ein:
                    connected_ein = row["org2_ein"]
                    connected_name = row["org2_name"]
                else:
                    connected_ein = row["org1_ein"]
                    connected_name = row["org1_name"]

                if connected_ein not in org_groups:
                    org_groups[connected_ein] = {
                        "connected_org_ein": connected_ein,
                        "connected_org_name": connected_name,
                        "strength": row["connection_strength"],
                        "shared_people": [],
                        "is_current": bool(row["is_current_connection"]),
                    }
                else:
                    entry = org_groups[connected_ein]
                    if row["connection_strength"] > entry["strength"]:
                        entry["strength"] = row["connection_strength"]
                    if row["is_current_connection"]:
                        entry["is_current"] = True

                # Look up person details for the bridging person
                person = conn.execute(
                    """
                    SELECT p.normalized_name,
                           r.title,
                           r.position_type
                    FROM people p
                    LEFT JOIN organization_roles r
                      ON r.person_id = p.id AND r.organization_ein = ?
                    WHERE p.id = ?
                    ORDER BY r.is_current DESC
                    LIMIT 1
                    """,
                    (org_ein, row["person_id"]),
                ).fetchone()

                if person:
                    other_role = conn.execute(
                        "SELECT position_type FROM organization_roles "
                        "WHERE person_id = ? AND organization_ein = ? "
                        "ORDER BY is_current DESC LIMIT 1",
                        (row["person_id"], connected_ein),
                    ).fetchone()

                    rp = self._factor_role_proximity(
                        person["position_type"] or "",
                        (other_role["position_type"] if other_role else "") or "",
                    )

                    org_groups[connected_ein]["shared_people"].append({
                        "name": person["normalized_name"],
                        "title": person["title"] or "",
                        "role_proximity": rp,
                    })

            results = sorted(
                org_groups.values(),
                key=lambda x: x["strength"],
                reverse=True,
            )
            return results[:limit]
