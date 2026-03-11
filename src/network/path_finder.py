"""
PathFinder — BFS on network_memberships to find connection paths between
seeker profile and a funder EIN.  Pure Python, no external graph library.
"""

import sqlite3
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class NetworkPath:
    degree: int                     # 1, 2, or 3
    path_nodes: list                # [{name, org_name, org_type, title}, ...]
    connection_basis: str           # "direct board overlap" | "shared board at X"
    strength: str                   # "strong" | "moderate" | "weak"


class PathFinder:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def find_paths(
        self,
        profile_id: str,
        funder_ein: str,
        max_degree: int = 3,
    ) -> list[NetworkPath]:
        """
        BFS on network_memberships to find connection paths (degree 1-3).
        Returns a list of NetworkPath sorted by degree (ascending).
        """
        paths: list[NetworkPath] = []

        with self._conn() as conn:
            # ── Load seeker nodes ────────────────────────────────────────
            seeker_rows = conn.execute(
                "SELECT person_hash, display_name, org_name, title "
                "FROM network_memberships WHERE profile_id = ? AND org_type = 'seeker'",
                (profile_id,),
            ).fetchall()

            # ── Load funder nodes ────────────────────────────────────────
            funder_rows = conn.execute(
                "SELECT person_hash, display_name, org_name, title "
                "FROM network_memberships WHERE org_ein = ? AND org_type = 'funder'",
                (funder_ein,),
            ).fetchall()

            if not seeker_rows or not funder_rows:
                return []

            seeker_by_hash = {r["person_hash"]: dict(r) for r in seeker_rows}
            funder_by_hash = {r["person_hash"]: dict(r) for r in funder_rows}
            seeker_hashes = set(seeker_by_hash)
            funder_hashes = set(funder_by_hash)

            # ── Degree 1: direct overlap ─────────────────────────────────
            direct = seeker_hashes & funder_hashes
            for ph in direct:
                s = seeker_by_hash[ph]
                f = funder_by_hash[ph]
                paths.append(NetworkPath(
                    degree=1,
                    path_nodes=[
                        {
                            "name": s["display_name"],
                            "org_name": s["org_name"],
                            "org_type": "seeker",
                            "title": s["title"] or "",
                        },
                        {
                            "name": f["display_name"],
                            "org_name": f["org_name"],
                            "org_type": "funder",
                            "title": f["title"] or "",
                        },
                    ],
                    connection_basis="direct board overlap",
                    strength="strong",
                ))

            if max_degree < 2:
                return paths

            # ── Degree 2: seeker → shared org → funder ───────────────────
            # Find orgs where seeker people appear (excluding seeker org itself)
            seeker_hash_list = list(seeker_hashes - direct)
            if seeker_hash_list:
                placeholders = ",".join("?" * len(seeker_hash_list))
                shared_org_rows = conn.execute(
                    f"SELECT person_hash, display_name, org_ein, org_name, title "
                    f"FROM network_memberships "
                    f"WHERE person_hash IN ({placeholders}) "
                    f"  AND org_type = 'funder' AND org_ein != ?",
                    seeker_hash_list + [funder_ein],
                ).fetchall()

                # Group by org_ein
                shared_orgs: dict[str, list] = {}
                for row in shared_org_rows:
                    shared_orgs.setdefault(row["org_ein"], []).append(dict(row))

                for shared_ein, shared_members in shared_orgs.items():
                    # Who else is at funder AND at this shared org?
                    intermediary_hashes = {r["person_hash"] for r in shared_members}
                    # Find if any of these intermediary hashes appear at the funder
                    inter_at_funder = intermediary_hashes & funder_hashes
                    for inter_ph in inter_at_funder:
                        # Seeker person who is also at shared_ein
                        seeker_person = None
                        for sh in shared_members:
                            if sh["person_hash"] == inter_ph:
                                seeker_person = sh
                                break
                        if not seeker_person:
                            continue
                        f = funder_by_hash[inter_ph]
                        paths.append(NetworkPath(
                            degree=2,
                            path_nodes=[
                                {
                                    "name": seeker_person["display_name"],
                                    "org_name": seeker_person["org_name"],
                                    "org_type": "funder",
                                    "title": seeker_person["title"] or "",
                                },
                                {
                                    "name": f["display_name"],
                                    "org_name": f["org_name"],
                                    "org_type": "funder",
                                    "title": f["title"] or "",
                                },
                            ],
                            connection_basis=f"shared board at {seeker_person['org_name']}",
                            strength="moderate",
                        ))

            if max_degree < 3:
                return _deduplicate(paths)

            # ── Degree 3: seeker → org A → org B → funder ───────────────
            # Get all hashes from all funder-type orgs except target funder
            # that intersect with seeker hashes
            all_inter_rows = conn.execute(
                "SELECT DISTINCT person_hash, org_ein, org_name, display_name, title "
                "FROM network_memberships "
                "WHERE org_type = 'funder' AND org_ein != ?",
                (funder_ein,),
            ).fetchall()

            # Build: org_ein → set of person_hashes
            org_to_hashes: dict[str, set] = {}
            hash_to_info: dict[str, dict] = {}
            for r in all_inter_rows:
                org_to_hashes.setdefault(r["org_ein"], set()).add(r["person_hash"])
                hash_to_info[r["person_hash"]] = dict(r)

            # Seeker-reachable orgs (orgs where a seeker person also sits)
            seeker_reachable_orgs = set()
            for ph in seeker_hashes - direct:
                for ein_key, hashes in org_to_hashes.items():
                    if ph in hashes:
                        seeker_reachable_orgs.add(ein_key)

            # For each seeker-reachable org, find orgs that share a person with it
            # AND that share a person with the funder
            for org_a in seeker_reachable_orgs:
                hashes_a = org_to_hashes.get(org_a, set())
                for org_b, hashes_b in org_to_hashes.items():
                    if org_b == org_a:
                        continue
                    bridge = hashes_a & hashes_b
                    final = hashes_b & funder_hashes
                    if bridge and final:
                        bridge_ph = next(iter(bridge))
                        final_ph = next(iter(final))
                        bridge_info = hash_to_info.get(bridge_ph, {})
                        f = funder_by_hash[final_ph]
                        # Seeker person at org_a
                        seeker_ph = next(
                            (ph for ph in seeker_hashes if ph in org_to_hashes.get(org_a, set())),
                            None,
                        )
                        if not seeker_ph:
                            continue
                        s = seeker_by_hash.get(seeker_ph, {})
                        paths.append(NetworkPath(
                            degree=3,
                            path_nodes=[
                                {
                                    "name": s.get("display_name", ""),
                                    "org_name": s.get("org_name", ""),
                                    "org_type": "seeker",
                                    "title": s.get("title") or "",
                                },
                                {
                                    "name": bridge_info.get("display_name", ""),
                                    "org_name": bridge_info.get("org_name", ""),
                                    "org_type": "funder",
                                    "title": bridge_info.get("title") or "",
                                },
                                {
                                    "name": f["display_name"],
                                    "org_name": f["org_name"],
                                    "org_type": "funder",
                                    "title": f["title"] or "",
                                },
                            ],
                            connection_basis=f"via {bridge_info.get('org_name', org_b)}",
                            strength="weak",
                        ))

        return _deduplicate(paths)


def _deduplicate(paths: list[NetworkPath]) -> list[NetworkPath]:
    """Remove duplicate paths (same degree + first/last node name)."""
    seen = set()
    result = []
    for p in sorted(paths, key=lambda x: x.degree):
        key = (p.degree, p.path_nodes[0].get("name", ""), p.path_nodes[-1].get("name", ""))
        if key not in seen:
            seen.add(key)
            result.append(p)
    return result
