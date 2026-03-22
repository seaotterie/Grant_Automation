"""
Connection Pathway Tool
12-Factor compliant tool for discovering warm introduction pathways.

Purpose: Multi-hop connection pathway discovery between seeker and funder
Cost: $0.03 per analysis (when AI cultivation strategies enabled)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
import hashlib
import sqlite3
from typing import Optional, Dict, Any, List, Set, Tuple
from dataclasses import asdict
from datetime import datetime
from collections import defaultdict, deque

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext
from .pathway_models import (
    ConnectionPathwayInput,
    ConnectionPathwayOutput,
    IntroductionPathway,
    PathwayNode,
    PathwayStrength,
)

logger = logging.getLogger(__name__)

CONNECTION_PATHWAY_COST = 0.03


class ConnectionPathwayTool(BaseTool[ConnectionPathwayOutput]):
    """
    Discovers warm introduction pathways between a seeker and a target funder.
    Uses the people + organization_roles tables for multi-hop path discovery.
    Optionally generates AI cultivation strategies (costs $0.03 via Haiku).
    """

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)

    def get_tool_name(self) -> str:
        return "connection_pathway"

    def get_tool_version(self) -> str:
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        return "Multi-hop connection pathway discovery with cultivation strategies"

    def get_cost_estimate(self) -> Optional[float]:
        return CONNECTION_PATHWAY_COST

    def validate_inputs(self, **kwargs) -> tuple:
        input_data = kwargs.get("input_data")
        if not input_data:
            return False, "input_data (ConnectionPathwayInput) is required"
        if not isinstance(input_data, ConnectionPathwayInput):
            return False, "input_data must be a ConnectionPathwayInput instance"
        if not input_data.profile_id:
            return False, "profile_id is required"
        if not input_data.target_funder_ein:
            return False, "target_funder_ein is required"
        return True, None

    async def _execute(
        self, context: ToolExecutionContext, **kwargs
    ) -> ConnectionPathwayOutput:
        input_data: ConnectionPathwayInput = kwargs.get("input_data")
        if not input_data:
            raise ValueError("input_data (ConnectionPathwayInput) is required")

        db_path = kwargs.get("db_path")
        if not db_path:
            from src.config.database_config import get_catalynx_db
            db_path = get_catalynx_db()

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            # Resolve seeker EIN from profile
            seeker_ein = self._resolve_seeker_ein(conn, input_data)

            # Try normalized tables first (people + organization_roles)
            has_people_data = self._has_people_table(conn)

            if has_people_data:
                pathways = self._discover_pathways_normalized(
                    conn, input_data, seeker_ein
                )
            else:
                # Fallback to network_memberships
                logger.info(
                    "people/organization_roles tables empty; "
                    "falling back to network_memberships"
                )
                pathways = self._discover_pathways_memberships(
                    conn, input_data, seeker_ein
                )

            # Sort by aggregate_strength descending
            pathways.sort(key=lambda p: p.aggregate_strength, reverse=True)

            # Limit to reasonable number
            pathways = pathways[:50]

            # Generate AI cultivation strategies for top pathways
            if input_data.include_cultivation_strategy and pathways:
                await self._generate_cultivation_strategies(
                    pathways[:3], input_data
                )

            # Compute network proximity score
            proximity_score = self._compute_proximity_score(pathways)

            # Build coverage summary
            coverage_summary = self._build_coverage_summary(pathways)

            # Best pathway
            best_pathway = asdict(pathways[0]) if pathways else None

            # Strategic recommendations
            recommendations = self._generate_recommendations(
                pathways, input_data
            )

            return ConnectionPathwayOutput(
                profile_id=input_data.profile_id,
                target_funder_ein=input_data.target_funder_ein,
                target_funder_name=input_data.target_funder_name,
                pathways=pathways,
                best_pathway=best_pathway,
                network_proximity_score=proximity_score,
                total_pathways_found=len(pathways),
                coverage_summary=coverage_summary,
                recommendations=recommendations,
            )
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Seeker EIN resolution
    # ------------------------------------------------------------------

    def _resolve_seeker_ein(
        self, conn: sqlite3.Connection, input_data: ConnectionPathwayInput
    ) -> Optional[str]:
        """Resolve the seeker organization's EIN from the profiles table."""
        try:
            row = conn.execute(
                "SELECT ein FROM profiles WHERE id = ?",
                (input_data.profile_id,),
            ).fetchone()
            if row and row["ein"]:
                return row["ein"]
        except sqlite3.OperationalError:
            logger.debug("profiles table not found; skipping EIN resolution")
        return None

    # ------------------------------------------------------------------
    # Table availability check
    # ------------------------------------------------------------------

    def _has_people_table(self, conn: sqlite3.Connection) -> bool:
        """Check if people and organization_roles tables exist and have data."""
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM people"
            ).fetchone()
            return row["cnt"] > 0
        except sqlite3.OperationalError:
            return False

    # ------------------------------------------------------------------
    # Path discovery via normalized tables (people + organization_roles)
    # ------------------------------------------------------------------

    def _discover_pathways_normalized(
        self,
        conn: sqlite3.Connection,
        input_data: ConnectionPathwayInput,
        seeker_ein: Optional[str],
    ) -> List[IntroductionPathway]:
        """BFS path discovery using people and organization_roles tables."""

        # Build adjacency: person_id -> set of org_eins
        #                  org_ein   -> set of person_ids
        person_to_orgs: Dict[int, Set[str]] = defaultdict(set)
        org_to_persons: Dict[str, Set[int]] = defaultdict(set)

        # Also store metadata for node construction
        person_info: Dict[int, Dict[str, Any]] = {}
        role_info: Dict[Tuple[int, str], Dict[str, Any]] = {}

        rows = conn.execute(
            """
            SELECT p.id as person_id, p.normalized_name, p.original_name,
                   r.organization_ein, r.organization_name, r.title,
                   r.position_type, r.is_current
            FROM people p
            JOIN organization_roles r ON r.person_id = p.id
            """
        ).fetchall()

        for row in rows:
            pid = row["person_id"]
            oein = row["organization_ein"]
            person_to_orgs[pid].add(oein)
            org_to_persons[oein].add(pid)
            person_info[pid] = {
                "name": row["original_name"] or row["normalized_name"],
                "normalized_name": row["normalized_name"],
            }
            role_info[(pid, oein)] = {
                "title": row["title"],
                "position_type": row["position_type"] or "board",
                "org_name": row["organization_name"],
                "is_current": bool(row["is_current"]),
            }

        # Identify seeker person IDs
        seeker_person_ids: Set[int] = set()
        if seeker_ein:
            seeker_person_ids = org_to_persons.get(seeker_ein, set())

        # Also include board members provided in input
        for member in input_data.seeker_board_members:
            member_name = member.get("name", "").strip().lower()
            if not member_name:
                continue
            for pid, info in person_info.items():
                if info["normalized_name"].lower() == member_name:
                    seeker_person_ids.add(pid)

        # Identify funder person IDs
        funder_ein = input_data.target_funder_ein
        funder_person_ids: Set[int] = org_to_persons.get(funder_ein, set())

        if not seeker_person_ids or not funder_person_ids:
            return []

        # Degree-1 (direct): same person at both seeker and funder orgs
        pathways: List[IntroductionPathway] = []
        shared_person_ids = seeker_person_ids & funder_person_ids
        for pid in shared_person_ids:
            pathway = self._build_pathway_from_person_chain(
                person_chain=[pid],
                person_info=person_info,
                role_info=role_info,
                seeker_ein=seeker_ein,
                funder_ein=funder_ein,
                input_data=input_data,
                is_shared_person=True,
            )
            pathways.append(pathway)

        # BFS from each seeker person outward for multi-hop paths
        max_hops = min(input_data.max_hops, 4)

        for start_pid in seeker_person_ids:
            found = self._bfs_find_paths(
                start_pid=start_pid,
                target_pids=funder_person_ids,
                person_to_orgs=person_to_orgs,
                org_to_persons=org_to_persons,
                max_hops=max_hops,
            )
            for path in found:
                pathway = self._build_pathway_from_person_chain(
                    person_chain=path,
                    person_info=person_info,
                    role_info=role_info,
                    seeker_ein=seeker_ein,
                    funder_ein=funder_ein,
                    input_data=input_data,
                )
                pathways.append(pathway)

        # Deduplicate by pathway_id
        seen_ids: Set[str] = set()
        unique: List[IntroductionPathway] = []
        for pw in pathways:
            if pw.pathway_id not in seen_ids:
                seen_ids.add(pw.pathway_id)
                unique.append(pw)

        return unique

    def _bfs_find_paths(
        self,
        start_pid: int,
        target_pids: Set[int],
        person_to_orgs: Dict[int, Set[str]],
        org_to_persons: Dict[str, Set[int]],
        max_hops: int,
    ) -> List[List[int]]:
        """
        BFS that finds all paths from start_pid to any target_pid
        within max_hops. A hop is: person -> org -> person.
        Returns list of person_id chains.
        """
        # Each state in the queue: (current_person_id, path_so_far, visited_persons)
        results: List[List[int]] = []
        queue: deque = deque()
        queue.append((start_pid, [start_pid], {start_pid}))

        while queue:
            current_pid, path, visited = queue.popleft()
            hops = len(path) - 1  # number of person-to-person hops

            if current_pid in target_pids and hops > 0:
                results.append(list(path))
                continue  # don't extend past a target

            if hops >= max_hops:
                continue

            # Expand: current person's orgs -> other people at those orgs
            for oein in person_to_orgs.get(current_pid, set()):
                for next_pid in org_to_persons.get(oein, set()):
                    if next_pid not in visited:
                        new_visited = visited | {next_pid}
                        new_path = path + [next_pid]
                        queue.append((next_pid, new_path, new_visited))

        return results

    def _build_pathway_from_person_chain(
        self,
        person_chain: List[int],
        person_info: Dict[int, Dict[str, Any]],
        role_info: Dict[Tuple[int, str], Dict[str, Any]],
        seeker_ein: Optional[str],
        funder_ein: str,
        input_data: ConnectionPathwayInput,
        is_shared_person: bool = False,
    ) -> IntroductionPathway:
        """Convert a chain of person IDs into an IntroductionPathway."""
        if is_shared_person:
            degree = 1  # same person at both orgs counts as degree 1
        else:
            degree = len(person_chain) - 1
        strength = self._degree_to_strength(degree)

        # Build nodes
        nodes: List[dict] = []
        if is_shared_person and len(person_chain) == 1:
            # Same person at both orgs: build two nodes (seeker role + funder role)
            pid = person_chain[0]
            info = person_info.get(pid, {"name": "Unknown"})
            seeker_rinfo = role_info.get((pid, seeker_ein), {}) if seeker_ein else {}
            funder_rinfo = role_info.get((pid, funder_ein), {})

            seeker_node = PathwayNode(
                person_name=info.get("name", "Unknown"),
                title=seeker_rinfo.get("title"),
                organization_name=seeker_rinfo.get("org_name", input_data.seeker_org_name),
                organization_ein=seeker_ein,
                org_type="seeker",
                role_at_org=seeker_rinfo.get("position_type", "board"),
                influence_score=self._compute_person_influence(seeker_rinfo),
            )
            funder_node = PathwayNode(
                person_name=info.get("name", "Unknown"),
                title=funder_rinfo.get("title"),
                organization_name=funder_rinfo.get("org_name", input_data.target_funder_name),
                organization_ein=funder_ein,
                org_type="funder",
                role_at_org=funder_rinfo.get("position_type", "board"),
                influence_score=self._compute_person_influence(funder_rinfo),
            )
            nodes.append(asdict(seeker_node))
            nodes.append(asdict(funder_node))
        else:
            for i, pid in enumerate(person_chain):
                info = person_info.get(pid, {"name": "Unknown"})
                if i == 0:
                    org_type = "seeker"
                    ein = seeker_ein
                    rinfo = role_info.get((pid, seeker_ein), {}) if seeker_ein else {}
                elif i == len(person_chain) - 1:
                    org_type = "funder"
                    ein = funder_ein
                    rinfo = role_info.get((pid, funder_ein), {})
                else:
                    org_type = "intermediary"
                    # Find the shared org between this person and the next
                    ein = None
                    rinfo = {}
                    # Pick any org this person has a role at (prefer one connecting to neighbors)
                    for key, ri in role_info.items():
                        if key[0] == pid:
                            ein = key[1]
                            rinfo = ri
                            break

                node = PathwayNode(
                    person_name=info.get("name", "Unknown"),
                    title=rinfo.get("title"),
                    organization_name=rinfo.get("org_name", input_data.seeker_org_name if i == 0 else input_data.target_funder_name),
                    organization_ein=ein,
                    org_type=org_type,
                    role_at_org=rinfo.get("position_type", "board"),
                    influence_score=self._compute_person_influence(rinfo),
                )
                nodes.append(asdict(node))

        # Aggregate strength with boosts
        aggregate = self._compute_aggregate_strength(degree, nodes)

        # Connection basis
        names = [n["person_name"] for n in nodes]
        if degree == 1:
            basis = f"{names[0]} serves at both organizations"
        else:
            intermediaries = " -> ".join(names[1:-1])
            basis = f"{names[0]} connects to {names[-1]} via {intermediaries}"

        # Pathway ID from hash of person chain
        chain_str = "-".join(str(pid) for pid in person_chain)
        pathway_id = hashlib.md5(chain_str.encode()).hexdigest()[:12]

        # Estimated timeline
        timeline = self._estimate_timeline(degree)

        return IntroductionPathway(
            pathway_id=pathway_id,
            degree=degree,
            strength=strength,
            aggregate_strength=aggregate,
            nodes=nodes,
            connection_basis=basis,
            estimated_timeline=timeline,
            success_probability=min(1.0, aggregate * 0.8),
        )

    # ------------------------------------------------------------------
    # Fallback: network_memberships table
    # ------------------------------------------------------------------

    def _discover_pathways_memberships(
        self,
        conn: sqlite3.Connection,
        input_data: ConnectionPathwayInput,
        seeker_ein: Optional[str],
    ) -> List[IntroductionPathway]:
        """
        Fallback path discovery using the network_memberships table.
        This mirrors the normalized logic but queries a different schema.
        """
        person_to_orgs: Dict[str, Set[str]] = defaultdict(set)
        org_to_persons: Dict[str, Set[str]] = defaultdict(set)
        person_display: Dict[str, str] = {}
        membership_info: Dict[Tuple[str, str], Dict[str, Any]] = {}

        try:
            rows = conn.execute(
                """
                SELECT person_hash, display_name, org_ein, org_name,
                       org_type, title, profile_id
                FROM network_memberships
                """
            ).fetchall()
        except sqlite3.OperationalError:
            logger.warning("network_memberships table not found")
            return []

        for row in rows:
            phash = row["person_hash"]
            oein = row["org_ein"] or ""
            person_to_orgs[phash].add(oein)
            org_to_persons[oein].add(phash)
            person_display[phash] = row["display_name"]
            membership_info[(phash, oein)] = {
                "title": row["title"],
                "org_name": row["org_name"],
                "org_type": row["org_type"],
            }

        # Seeker people
        seeker_hashes: Set[str] = set()
        if seeker_ein:
            seeker_hashes = org_to_persons.get(seeker_ein, set())
        # Also check profile_id matches
        for row in rows:
            if row["profile_id"] == input_data.profile_id:
                seeker_hashes.add(row["person_hash"])

        # Funder people
        funder_hashes: Set[str] = org_to_persons.get(
            input_data.target_funder_ein, set()
        )

        if not seeker_hashes or not funder_hashes:
            return []

        pathways: List[IntroductionPathway] = []
        max_hops = min(input_data.max_hops, 4)

        for start_hash in seeker_hashes:
            found = self._bfs_find_paths_str(
                start=start_hash,
                targets=funder_hashes,
                person_to_orgs=person_to_orgs,
                org_to_persons=org_to_persons,
                max_hops=max_hops,
            )
            for chain in found:
                pathway = self._build_pathway_from_hash_chain(
                    chain=chain,
                    person_display=person_display,
                    membership_info=membership_info,
                    seeker_ein=seeker_ein,
                    funder_ein=input_data.target_funder_ein,
                    input_data=input_data,
                )
                pathways.append(pathway)

        # Deduplicate
        seen: Set[str] = set()
        unique: List[IntroductionPathway] = []
        for pw in pathways:
            if pw.pathway_id not in seen:
                seen.add(pw.pathway_id)
                unique.append(pw)
        return unique

    def _bfs_find_paths_str(
        self,
        start: str,
        targets: Set[str],
        person_to_orgs: Dict[str, Set[str]],
        org_to_persons: Dict[str, Set[str]],
        max_hops: int,
    ) -> List[List[str]]:
        """BFS for string-keyed person hashes."""
        results: List[List[str]] = []
        queue: deque = deque()
        queue.append((start, [start], {start}))

        while queue:
            current, path, visited = queue.popleft()
            hops = len(path) - 1

            if current in targets and hops > 0:
                results.append(list(path))
                continue

            if hops >= max_hops:
                continue

            for oein in person_to_orgs.get(current, set()):
                for next_p in org_to_persons.get(oein, set()):
                    if next_p not in visited:
                        queue.append(
                            (next_p, path + [next_p], visited | {next_p})
                        )

        return results

    def _build_pathway_from_hash_chain(
        self,
        chain: List[str],
        person_display: Dict[str, str],
        membership_info: Dict[Tuple[str, str], Dict[str, Any]],
        seeker_ein: Optional[str],
        funder_ein: str,
        input_data: ConnectionPathwayInput,
    ) -> IntroductionPathway:
        """Build pathway from a chain of person_hash values."""
        degree = len(chain) - 1
        strength = self._degree_to_strength(degree)

        nodes: List[dict] = []
        for i, phash in enumerate(chain):
            name = person_display.get(phash, "Unknown")
            if i == 0:
                org_type = "seeker"
                ein = seeker_ein
            elif i == len(chain) - 1:
                org_type = "funder"
                ein = funder_ein
            else:
                org_type = "intermediary"
                ein = None

            minfo = membership_info.get((phash, ein or ""), {})
            if not minfo:
                # Find any membership for this person
                for key, mi in membership_info.items():
                    if key[0] == phash:
                        minfo = mi
                        if not ein:
                            ein = key[1]
                        break

            node = PathwayNode(
                person_name=name,
                title=minfo.get("title"),
                organization_name=minfo.get("org_name", ""),
                organization_ein=ein,
                org_type=org_type,
                role_at_org=minfo.get("org_type", "board"),
                influence_score=0.5,
            )
            nodes.append(asdict(node))

        aggregate = self._compute_aggregate_strength(degree, nodes)
        names = [n["person_name"] for n in nodes]
        if degree == 1:
            basis = f"{names[0]} serves at both organizations"
        else:
            intermediaries = " -> ".join(names[1:-1])
            basis = f"{names[0]} connects to {names[-1]} via {intermediaries}"

        chain_str = "-".join(chain)
        pathway_id = hashlib.md5(chain_str.encode()).hexdigest()[:12]
        timeline = self._estimate_timeline(degree)

        return IntroductionPathway(
            pathway_id=pathway_id,
            degree=degree,
            strength=strength,
            aggregate_strength=aggregate,
            nodes=nodes,
            connection_basis=basis,
            estimated_timeline=timeline,
            success_probability=min(1.0, aggregate * 0.8),
        )

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _degree_to_strength(degree: int) -> PathwayStrength:
        return {
            1: PathwayStrength.DIRECT,
            2: PathwayStrength.STRONG,
            3: PathwayStrength.MODERATE,
            4: PathwayStrength.WEAK,
        }.get(degree, PathwayStrength.NONE)

    @staticmethod
    def _compute_person_influence(rinfo: Dict[str, Any]) -> float:
        """Compute influence score for a single person based on role info."""
        base = 0.5
        position = rinfo.get("position_type", "board")
        if position in ("executive", "officer", "ceo", "president"):
            base += 0.1
        if rinfo.get("is_current", True):
            base += 0.1
        return min(1.0, base)

    @staticmethod
    def _compute_aggregate_strength(
        degree: int, nodes: List[dict]
    ) -> float:
        """Compute aggregate pathway strength from degree and node info."""
        base_by_degree = {1: 1.0, 2: 0.7, 3: 0.4, 4: 0.2}
        base = base_by_degree.get(degree, 0.1)

        # Boost for executive roles along the path
        for node in nodes:
            role = node.get("role_at_org", "")
            if role in ("executive", "officer", "ceo", "president"):
                base = min(1.0, base + 0.1)
                break  # only one boost for executive

        # Boost for current connections (check influence_score as proxy)
        avg_influence = sum(n.get("influence_score", 0.5) for n in nodes) / max(len(nodes), 1)
        if avg_influence >= 0.7:
            base = min(1.0, base + 0.1)

        return round(base, 2)

    @staticmethod
    def _estimate_timeline(degree: int) -> str:
        return {
            1: "1-2 weeks",
            2: "2-4 weeks",
            3: "1-3 months",
            4: "3-6 months",
        }.get(degree, "6+ months")

    # ------------------------------------------------------------------
    # Network proximity score (0-100)
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_proximity_score(
        pathways: List[IntroductionPathway],
    ) -> float:
        """
        Compute a 0-100 network proximity score.

        Bands:
          - No pathways: 0-10 (base 5)
          - Best degree 4: 15-30
          - Best degree 3: 30-55
          - Best degree 2: 55-80
          - Best degree 1: 80-100
        Within each band: scale by pathway count and aggregate strength.
        """
        if not pathways:
            return 5.0

        best = pathways[0]  # already sorted by aggregate_strength desc

        # Band boundaries
        bands = {
            1: (80, 100),
            2: (55, 80),
            3: (30, 55),
            4: (15, 30),
        }
        low, high = bands.get(best.degree, (0, 15))

        # Scale within band based on:
        #   - number of pathways (more = better, diminishing returns)
        #   - best aggregate strength
        count_factor = min(1.0, len(pathways) / 10.0)
        strength_factor = best.aggregate_strength

        combined = (count_factor * 0.4 + strength_factor * 0.6)
        score = low + (high - low) * combined
        return round(min(100.0, max(0.0, score)), 1)

    # ------------------------------------------------------------------
    # Coverage summary
    # ------------------------------------------------------------------

    @staticmethod
    def _build_coverage_summary(
        pathways: List[IntroductionPathway],
    ) -> str:
        counts: Dict[int, int] = defaultdict(int)
        for pw in pathways:
            counts[pw.degree] += 1

        parts = []
        labels = {1: "direct connection", 2: "two-hop pathway", 3: "three-hop pathway", 4: "four-hop pathway"}
        for deg in sorted(counts.keys()):
            label = labels.get(deg, f"{deg}-hop pathway")
            n = counts[deg]
            if n != 1:
                label += "s"
            parts.append(f"{n} {label}")

        return ", ".join(parts) if parts else "No pathways found"

    # ------------------------------------------------------------------
    # AI cultivation strategy generation
    # ------------------------------------------------------------------

    async def _generate_cultivation_strategies(
        self,
        pathways: List[IntroductionPathway],
        input_data: ConnectionPathwayInput,
    ) -> None:
        """Generate AI cultivation strategies for the top pathways."""
        try:
            from src.core.anthropic_service import AnthropicService, ClaudeModel

            service = AnthropicService()
            if not service.is_available:
                logger.warning(
                    "Anthropic service not available; skipping cultivation strategies"
                )
                return

            for pathway in pathways:
                node_names = [n["person_name"] for n in pathway.nodes]
                prompt = (
                    f"You are an expert nonprofit fundraising advisor. "
                    f"A nonprofit organization ({input_data.seeker_org_name or 'the seeker'}) "
                    f"wants a warm introduction to {input_data.target_funder_name or input_data.target_funder_ein}. "
                    f"There is a {pathway.degree}-hop connection pathway: "
                    f"{' -> '.join(node_names)}. "
                    f"The connection basis is: {pathway.connection_basis}. "
                    f"Write a 2-3 sentence practical cultivation strategy for "
                    f"leveraging this pathway to secure an introduction. "
                    f"Be specific about concrete actions."
                )

                response = await service.create_completion(
                    messages=[{"role": "user", "content": prompt}],
                    model=ClaudeModel.HAIKU.value,
                    max_tokens=256,
                    temperature=0.7,
                )
                pathway.cultivation_strategy = response.content.strip()

        except Exception as e:
            logger.warning(
                "Failed to generate cultivation strategies: %s", str(e)
            )

    # ------------------------------------------------------------------
    # Strategic recommendations
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_recommendations(
        pathways: List[IntroductionPathway],
        input_data: ConnectionPathwayInput,
    ) -> List[str]:
        recommendations = []

        if not pathways:
            recommendations.append(
                "No warm introduction pathways found. Consider cold outreach "
                "or attending industry events where funder representatives "
                "may be present."
            )
            recommendations.append(
                "Recruit board members with connections to the target funder's network."
            )
            return recommendations

        best = pathways[0]
        if best.degree == 1:
            recommendations.append(
                f"Prioritize the direct connection through {best.nodes[0]['person_name']}. "
                f"Schedule a meeting to discuss the introduction within 1-2 weeks."
            )
        elif best.degree == 2:
            recommendations.append(
                f"Leverage the two-hop pathway via {best.nodes[1]['person_name']} "
                f"as your strongest introduction route."
            )
        else:
            recommendations.append(
                f"The best available pathway has {best.degree} hops. "
                f"Consider cultivating closer connections to shorten the path."
            )

        if len(pathways) > 1:
            recommendations.append(
                f"You have {len(pathways)} total pathways available. "
                f"Pursue multiple introduction routes in parallel for higher success probability."
            )

        return recommendations
