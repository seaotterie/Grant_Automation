"""
PathFinder — BFS on network_memberships to find connection paths between
seeker profile and a funder EIN.  Also discovers funder-to-funder connections
and grant-win warm paths.  Pure Python, no external graph library.
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


@dataclass
class FunderConnection:
    """A connection between two funder organisations through a shared person."""
    funder1_ein: str
    funder1_name: str
    funder2_ein: str
    funder2_name: str
    shared_people: list             # [{name, title_at_f1, title_at_f2}, ...]
    connection_count: int           # number of shared people
    strength: str                   # "strong" (3+), "moderate" (2), "weak" (1)


@dataclass
class WarmPath:
    """A warm path to a funder via a previous grant win."""
    funder_ein: str
    funder_name: str
    source: str                     # "grant_win" | "grant_win_contact"
    win_details: dict               # {amount, award_year, program_name}
    contact: Optional[dict] = None  # {name, role, side} if via contact
    connected_funder_ein: Optional[str] = None  # if contact bridges to another funder
    connected_funder_name: Optional[str] = None
    warmth_score: float = 0.0


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

    # ------------------------------------------------------------------
    # Funder-to-funder connections
    # ------------------------------------------------------------------

    def find_funder_connections(
        self,
        profile_id: str,
        min_shared: int = 1,
        limit: int = 100,
    ) -> list[FunderConnection]:
        """
        Discover connections between funders linked to this profile's
        opportunities.  Two funders are connected when they share at least
        one person_hash in network_memberships.

        Cost: $0.00 — pure DB reads.

        Returns a list of FunderConnection sorted by connection_count desc.
        """
        with self._conn() as conn:
            # All funder EINs for this profile
            ein_rows = conn.execute(
                "SELECT DISTINCT ein, organization_name FROM opportunities "
                "WHERE profile_id = ? AND ein IS NOT NULL AND ein != ''",
                (profile_id,),
            ).fetchall()

            if not ein_rows:
                return []

            ein_to_name = {r["ein"]: r["organization_name"] or r["ein"] for r in ein_rows}
            eins = list(ein_to_name.keys())

            # Build ein → set(person_hash) map from network_memberships
            ph = ",".join("?" * len(eins))
            membership_rows = conn.execute(
                f"SELECT org_ein, person_hash, display_name, title "
                f"FROM network_memberships "
                f"WHERE org_type = 'funder' AND org_ein IN ({ph})",
                eins,
            ).fetchall()

            ein_people: dict[str, dict[str, dict]] = {}  # ein → {hash → {name, title}}
            for r in membership_rows:
                ein_people.setdefault(r["org_ein"], {})[r["person_hash"]] = {
                    "name": r["display_name"],
                    "title": r["title"] or "",
                }

            # Find all pairs with shared people
            connections: list[FunderConnection] = []
            ein_list = [e for e in eins if e in ein_people]

            for i in range(len(ein_list)):
                for j in range(i + 1, len(ein_list)):
                    e1, e2 = ein_list[i], ein_list[j]
                    shared_hashes = set(ein_people[e1].keys()) & set(ein_people[e2].keys())

                    if len(shared_hashes) < min_shared:
                        continue

                    shared_people = []
                    for sh in list(shared_hashes)[:10]:  # cap detail at 10
                        p1 = ein_people[e1][sh]
                        p2 = ein_people[e2][sh]
                        shared_people.append({
                            "name": p1["name"],
                            "title_at_f1": p1["title"],
                            "title_at_f2": p2["title"],
                        })

                    count = len(shared_hashes)
                    if count >= 3:
                        strength = "strong"
                    elif count == 2:
                        strength = "moderate"
                    else:
                        strength = "weak"

                    connections.append(FunderConnection(
                        funder1_ein=e1,
                        funder1_name=ein_to_name.get(e1, e1),
                        funder2_ein=e2,
                        funder2_name=ein_to_name.get(e2, e2),
                        shared_people=shared_people,
                        connection_count=count,
                        strength=strength,
                    ))

            connections.sort(key=lambda c: c.connection_count, reverse=True)
            return connections[:limit]

    def find_funder_clusters(
        self,
        profile_id: str,
        min_shared: int = 1,
    ) -> list[dict]:
        """
        Group connected funders into clusters using union-find on shared
        board members.  Returns clusters sorted by size descending.

        Each cluster: {cluster_id, funders: [{ein, name}], size,
                       internal_connections, shared_people_count}
        """
        connections = self.find_funder_connections(profile_id, min_shared=min_shared, limit=500)
        if not connections:
            return []

        # Collect all EINs
        all_eins: set[str] = set()
        ein_names: dict[str, str] = {}
        for c in connections:
            all_eins.add(c.funder1_ein)
            all_eins.add(c.funder2_ein)
            ein_names[c.funder1_ein] = c.funder1_name
            ein_names[c.funder2_ein] = c.funder2_name

        # Union-Find
        parent: dict[str, str] = {e: e for e in all_eins}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: str, b: str):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        for c in connections:
            union(c.funder1_ein, c.funder2_ein)

        # Group by root
        clusters_map: dict[str, list[str]] = {}
        for ein in all_eins:
            root = find(ein)
            clusters_map.setdefault(root, []).append(ein)

        # Build cluster objects with connection counts
        result = []
        for idx, (root, members) in enumerate(
            sorted(clusters_map.items(), key=lambda x: len(x[1]), reverse=True)
        ):
            member_set = set(members)
            internal = [
                c for c in connections
                if c.funder1_ein in member_set and c.funder2_ein in member_set
            ]
            shared_count = sum(c.connection_count for c in internal)

            result.append({
                "cluster_id": f"cluster_{idx + 1}",
                "funders": [
                    {"ein": e, "name": ein_names.get(e, e)} for e in members
                ],
                "size": len(members),
                "internal_connections": len(internal),
                "shared_people_count": shared_count,
            })

        return result

    # ------------------------------------------------------------------
    # Grant-win warm paths
    # ------------------------------------------------------------------

    def find_warm_paths(
        self,
        profile_id: str,
        limit: int = 50,
    ) -> list[WarmPath]:
        """
        Discover warm paths to funders through historical grant wins.

        Three types of warm paths:
        1. Direct: You previously won a grant from this funder.
        2. Contact bridge: A contact from a past win also appears at another funder.
        3. Funder bridge: A past funder shares board members with a target funder.

        Cost: $0.00 — pure DB reads.
        """
        paths: list[WarmPath] = []

        with self._conn() as conn:
            # Get all opportunity funder EINs for this profile
            opp_rows = conn.execute(
                "SELECT DISTINCT ein, organization_name FROM opportunities "
                "WHERE profile_id = ? AND ein IS NOT NULL AND ein != ''",
                (profile_id,),
            ).fetchall()
            target_eins = {r["ein"]: r["organization_name"] or r["ein"] for r in opp_rows}

            if not target_eins:
                return []

            # Load grant wins
            try:
                wins = conn.execute(
                    "SELECT id, funder_name, funder_ein, amount, award_year, "
                    "       program_name, grant_purpose "
                    "FROM grant_wins WHERE profile_id = ?",
                    (profile_id,),
                ).fetchall()
            except sqlite3.OperationalError:
                # grant_wins table may not exist yet
                return []

            if not wins:
                return []

            # --- Type 1: Direct repeat funder ---
            for win in wins:
                win_ein = win["funder_ein"]
                if win_ein and win_ein in target_eins:
                    paths.append(WarmPath(
                        funder_ein=win_ein,
                        funder_name=target_eins[win_ein],
                        source="grant_win_direct",
                        win_details={
                            "amount": win["amount"],
                            "award_year": win["award_year"],
                            "program_name": win["program_name"],
                        },
                        warmth_score=0.9,
                    ))

            # --- Type 2: Contact bridge ---
            # Contacts from past wins who also appear at target funders
            for win in wins:
                try:
                    contacts = conn.execute(
                        "SELECT gwc.contact_name, gwc.contact_role, gwc.side, gwc.person_id "
                        "FROM grant_win_contacts gwc "
                        "WHERE gwc.grant_win_id = ?",
                        (win["id"],),
                    ).fetchall()
                except sqlite3.OperationalError:
                    continue

                for contact in contacts:
                    if not contact["person_id"]:
                        continue

                    # Find what other funder orgs this contact serves at
                    contact_orgs = conn.execute(
                        "SELECT DISTINCT nm.org_ein, nm.org_name "
                        "FROM network_memberships nm "
                        "JOIN people p ON nm.person_hash = p.name_hash "
                        "WHERE p.id = ? AND nm.org_type = 'funder' "
                        "  AND nm.org_ein IS NOT NULL",
                        (contact["person_id"],),
                    ).fetchall()

                    for org in contact_orgs:
                        if org["org_ein"] in target_eins and org["org_ein"] != win["funder_ein"]:
                            paths.append(WarmPath(
                                funder_ein=org["org_ein"],
                                funder_name=target_eins[org["org_ein"]],
                                source="grant_win_contact_bridge",
                                win_details={
                                    "amount": win["amount"],
                                    "award_year": win["award_year"],
                                    "program_name": win["program_name"],
                                    "original_funder": win["funder_name"],
                                },
                                contact={
                                    "name": contact["contact_name"],
                                    "role": contact["contact_role"],
                                    "side": contact["side"],
                                },
                                connected_funder_ein=win["funder_ein"],
                                connected_funder_name=win["funder_name"],
                                warmth_score=0.6,
                            ))

            # --- Type 3: Funder bridge ---
            # Past funder shares board members with target funders
            won_eins = {w["funder_ein"] for w in wins if w["funder_ein"]}
            won_ein_to_win = {w["funder_ein"]: w for w in wins if w["funder_ein"]}

            for won_ein in won_eins:
                if won_ein in target_eins:
                    continue  # already covered by Type 1

                # Get people at past funder
                won_hashes = conn.execute(
                    "SELECT person_hash, display_name FROM network_memberships "
                    "WHERE org_ein = ? AND org_type = 'funder'",
                    (won_ein,),
                ).fetchall()

                if not won_hashes:
                    continue

                won_hash_set = {r["person_hash"] for r in won_hashes}

                # Check which target funders share people with this past funder
                for target_ein, target_name in target_eins.items():
                    target_hashes = conn.execute(
                        "SELECT person_hash FROM network_memberships "
                        "WHERE org_ein = ? AND org_type = 'funder'",
                        (target_ein,),
                    ).fetchall()
                    target_hash_set = {r["person_hash"] for r in target_hashes}

                    shared = won_hash_set & target_hash_set
                    if shared:
                        win = won_ein_to_win.get(won_ein)
                        paths.append(WarmPath(
                            funder_ein=target_ein,
                            funder_name=target_name,
                            source="grant_win_funder_bridge",
                            win_details={
                                "amount": win["amount"] if win else None,
                                "award_year": win["award_year"] if win else None,
                                "program_name": win["program_name"] if win else None,
                                "original_funder": win["funder_name"] if win else None,
                            },
                            connected_funder_ein=won_ein,
                            connected_funder_name=win["funder_name"] if win else won_ein,
                            warmth_score=0.4,
                        ))

        # Deduplicate: keep highest warmth per target funder
        best: dict[str, WarmPath] = {}
        for p in paths:
            existing = best.get(p.funder_ein)
            if not existing or p.warmth_score > existing.warmth_score:
                best[p.funder_ein] = p
            elif p.warmth_score == existing.warmth_score and p.source != existing.source:
                # Keep both distinct path types — boost score slightly
                existing.warmth_score = min(1.0, existing.warmth_score + 0.1)

        result = sorted(best.values(), key=lambda p: p.warmth_score, reverse=True)
        return result[:limit]


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
