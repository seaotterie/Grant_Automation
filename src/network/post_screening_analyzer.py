"""
PostScreeningAnalyzer — Automated network relationship discovery that runs
after opportunity screening completes.

Surfaces connections that exist in the data but weren't visible when looking
at opportunities individually:
  - Funder-to-funder board overlap clusters
  - Cross-opportunity funder frequency (same funder in many opps)
  - Grant-win warm paths to target funders
  - Network coverage diagnostics + actionable feedback

Cost: $0.00 — pure DB reads on existing data.
"""

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.network.path_finder import PathFinder, FunderConnection, WarmPath

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class FunderFrequency:
    """A funder that appears across multiple opportunities."""
    ein: str
    name: str
    opportunity_count: int
    total_award_potential: float  # sum of amount_max across opps
    program_areas: list[str]     # distinct focus areas
    people_in_graph: int


@dataclass
class NetworkDiagnostic:
    """Actionable feedback about network data completeness."""
    category: str       # "seeker_profile" | "funder_coverage" | "enrichment_gap"
    severity: str       # "critical" | "warning" | "info"
    message: str
    action: str         # what the user should do
    details: dict = field(default_factory=dict)


@dataclass
class PostScreeningReport:
    """Complete post-screening network analysis."""
    profile_id: str
    generated_at: str

    # Funder frequency analysis
    top_funders: list[FunderFrequency]
    total_unique_funders: int
    funders_appearing_3_plus: int

    # Funder-to-funder connections
    funder_connections: list[dict]   # serialised FunderConnection
    funder_clusters: list[dict]
    total_funder_connections: int

    # Warm paths from grant history
    warm_paths: list[dict]           # serialised WarmPath
    warm_funder_count: int

    # Network diagnostics
    diagnostics: list[dict]          # serialised NetworkDiagnostic

    # Summary stats
    people_in_graph: int
    funders_with_people: int
    funders_without_people: int
    seeker_board_size: int
    network_readiness_score: float   # 0.0–1.0


class PostScreeningAnalyzer:
    """
    Runs after opportunity screening to discover cross-opportunity
    relationships and produce actionable network intelligence.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._finder = PathFinder(db_path)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, profile_id: str) -> PostScreeningReport:
        """
        Run full post-screening analysis.  Cost: $0.00.

        Call this after:
          1. Opportunity screening is complete (Tool 1)
          2. Graph has been populated (populate-graph or batch preprocessor)
        """
        logger.info(f"[PostScreeningAnalyzer] Starting analysis for profile {profile_id}")

        # 1. Funder frequency
        top_funders, unique_count, freq3_count = self._analyze_funder_frequency(profile_id)

        # 2. Funder-to-funder connections
        funder_conns = self._finder.find_funder_connections(profile_id, min_shared=1, limit=100)
        funder_clusters = self._finder.find_funder_clusters(profile_id, min_shared=1)

        # 3. Warm paths
        warm_paths = self._finder.find_warm_paths(profile_id, limit=50)

        # 4. Diagnostics
        diagnostics = self._run_diagnostics(profile_id)

        # 5. Summary stats
        stats = self._compute_stats(profile_id)

        # 6. Network readiness score
        readiness = self._compute_readiness(
            seeker_board_size=stats["seeker_board_size"],
            funders_with_people=stats["funders_with_people"],
            total_funders=unique_count,
            funder_connection_count=len(funder_conns),
            warm_path_count=len(warm_paths),
        )

        report = PostScreeningReport(
            profile_id=profile_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            top_funders=top_funders,
            total_unique_funders=unique_count,
            funders_appearing_3_plus=freq3_count,
            funder_connections=[_serialise_funder_conn(c) for c in funder_conns],
            funder_clusters=funder_clusters,
            total_funder_connections=len(funder_conns),
            warm_paths=[_serialise_warm_path(p) for p in warm_paths],
            warm_funder_count=len(warm_paths),
            diagnostics=[_serialise_diagnostic(d) for d in diagnostics],
            people_in_graph=stats["people_in_graph"],
            funders_with_people=stats["funders_with_people"],
            funders_without_people=stats["funders_without_people"],
            seeker_board_size=stats["seeker_board_size"],
            network_readiness_score=readiness,
        )

        logger.info(
            f"[PostScreeningAnalyzer] Complete: {unique_count} funders, "
            f"{len(funder_conns)} funder-funder connections, "
            f"{len(funder_clusters)} clusters, {len(warm_paths)} warm paths, "
            f"readiness={readiness:.2f}"
        )
        return report

    # ------------------------------------------------------------------
    # Funder frequency analysis
    # ------------------------------------------------------------------

    def _analyze_funder_frequency(
        self, profile_id: str
    ) -> tuple[list[FunderFrequency], int, int]:
        """
        Which funders appear across the most opportunities?
        """
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT
                    ein,
                    organization_name,
                    COUNT(*) as opp_count,
                    SUM(CASE WHEN json_valid(analysis_discovery) THEN
                        json_extract(analysis_discovery, '$.amount_max')
                    ELSE 0 END) as total_potential,
                    GROUP_CONCAT(DISTINCT
                        CASE WHEN json_valid(analysis_discovery) THEN
                            json_extract(analysis_discovery, '$.focus_area')
                        ELSE NULL END
                    ) as focus_areas
                FROM opportunities
                WHERE profile_id = ? AND ein IS NOT NULL AND ein != ''
                GROUP BY ein
                ORDER BY opp_count DESC
                """,
                (profile_id,),
            ).fetchall()

            total_unique = len(rows)
            freq3 = sum(1 for r in rows if r["opp_count"] >= 3)

            top = []
            for r in rows[:25]:
                # Check people coverage
                people_count = conn.execute(
                    "SELECT COUNT(*) FROM network_memberships "
                    "WHERE org_ein = ? AND org_type = 'funder'",
                    (r["ein"],),
                ).fetchone()[0]

                areas = []
                if r["focus_areas"]:
                    areas = [a.strip() for a in r["focus_areas"].split(",") if a.strip()]

                top.append(FunderFrequency(
                    ein=r["ein"],
                    name=r["organization_name"] or r["ein"],
                    opportunity_count=r["opp_count"],
                    total_award_potential=r["total_potential"] or 0.0,
                    program_areas=areas[:5],
                    people_in_graph=people_count,
                ))

            return top, total_unique, freq3

    # ------------------------------------------------------------------
    # Network diagnostics
    # ------------------------------------------------------------------

    def _run_diagnostics(self, profile_id: str) -> list[NetworkDiagnostic]:
        """
        Generate actionable feedback about network data quality.
        """
        diagnostics: list[NetworkDiagnostic] = []

        with self._conn() as conn:
            # 1. Check seeker board members
            seeker_count = conn.execute(
                "SELECT COUNT(*) FROM network_memberships "
                "WHERE profile_id = ? AND org_type = 'seeker'",
                (profile_id,),
            ).fetchone()[0]

            profile_row = conn.execute(
                "SELECT board_members FROM profiles WHERE id = ?",
                (profile_id,),
            ).fetchone()

            if seeker_count == 0:
                if not profile_row or not profile_row["board_members"]:
                    diagnostics.append(NetworkDiagnostic(
                        category="seeker_profile",
                        severity="critical",
                        message="No board members in your profile. Network analysis cannot find connections without knowing your people.",
                        action="Add your board members and their affiliations in Profile Settings → Board Members.",
                        details={"board_count": 0},
                    ))
                else:
                    diagnostics.append(NetworkDiagnostic(
                        category="seeker_profile",
                        severity="warning",
                        message="Board members exist in profile but haven't been ingested into the network graph.",
                        action="Run 'Populate Graph' to load your board members into the network.",
                        details={"board_count": 0, "profile_has_data": True},
                    ))
            elif seeker_count < 5:
                diagnostics.append(NetworkDiagnostic(
                    category="seeker_profile",
                    severity="warning",
                    message=f"Only {seeker_count} board members in network. More members = more potential connections.",
                    action="Add advisory board members, key staff, and past board members to increase coverage.",
                    details={"board_count": seeker_count},
                ))

            # 2. Check funder people coverage
            opp_count = conn.execute(
                "SELECT COUNT(DISTINCT ein) FROM opportunities "
                "WHERE profile_id = ? AND ein IS NOT NULL AND ein != ''",
                (profile_id,),
            ).fetchone()[0]

            funders_with = conn.execute(
                """
                SELECT COUNT(DISTINCT nm.org_ein) FROM network_memberships nm
                WHERE nm.org_type = 'funder' AND nm.org_ein IN (
                    SELECT DISTINCT ein FROM opportunities
                    WHERE profile_id = ? AND ein IS NOT NULL
                )
                """,
                (profile_id,),
            ).fetchone()[0]

            funders_without = opp_count - funders_with

            if funders_without > opp_count * 0.5 and funders_without > 10:
                diagnostics.append(NetworkDiagnostic(
                    category="funder_coverage",
                    severity="warning",
                    message=f"{funders_without} of {opp_count} funders have no people data in the network graph.",
                    action="Run the Batch Preprocessor to extract officers from 990 filings (free) or web scrape leadership pages.",
                    details={"total_funders": opp_count, "with_data": funders_with, "without_data": funders_without},
                ))
            elif funders_without > 0:
                diagnostics.append(NetworkDiagnostic(
                    category="funder_coverage",
                    severity="info",
                    message=f"{funders_with}/{opp_count} funders have people in the network graph. {funders_without} remaining.",
                    action="Run XML Officer Lookup or Web Enrichment for remaining funders.",
                    details={"total_funders": opp_count, "with_data": funders_with, "without_data": funders_without},
                ))

            # 3. Check if graph population has been run
            total_memberships = conn.execute(
                "SELECT COUNT(*) FROM network_memberships"
            ).fetchone()[0]

            if total_memberships == 0 and opp_count > 0:
                diagnostics.append(NetworkDiagnostic(
                    category="enrichment_gap",
                    severity="critical",
                    message="Network graph is empty. No relationship analysis is possible.",
                    action="Run 'Populate Graph' first, then 'Batch Preprocessor' for comprehensive coverage.",
                    details={"graph_size": 0, "opportunities": opp_count},
                ))

            # 4. Check grant wins
            try:
                wins_count = conn.execute(
                    "SELECT COUNT(*) FROM grant_wins WHERE profile_id = ?",
                    (profile_id,),
                ).fetchone()[0]

                if wins_count == 0:
                    diagnostics.append(NetworkDiagnostic(
                        category="enrichment_gap",
                        severity="info",
                        message="No grant win history recorded. Past wins create warm paths to new funders.",
                        action="Import your grant history via Grant Wins → Import CSV to unlock warm path analysis.",
                        details={"wins_count": 0},
                    ))
            except sqlite3.OperationalError:
                diagnostics.append(NetworkDiagnostic(
                    category="enrichment_gap",
                    severity="info",
                    message="Grant wins tracking not yet initialized.",
                    action="Record past grant wins to enable warm path discovery to new funders.",
                    details={},
                ))

            # 5. Check for seeker board members missing affiliations
            if seeker_count > 0:
                seeker_with_affiliations = conn.execute(
                    """
                    SELECT COUNT(DISTINCT nm1.person_hash)
                    FROM network_memberships nm1
                    WHERE nm1.profile_id = ? AND nm1.org_type = 'seeker'
                    AND EXISTS (
                        SELECT 1 FROM network_memberships nm2
                        WHERE nm2.person_hash = nm1.person_hash
                        AND nm2.org_type = 'funder'
                    )
                    """,
                    (profile_id,),
                ).fetchone()[0]

                if seeker_with_affiliations == 0 and seeker_count > 0:
                    diagnostics.append(NetworkDiagnostic(
                        category="seeker_profile",
                        severity="info",
                        message="None of your board members appear in any funder's officer data. This is normal for most nonprofits.",
                        action="Focus on funder-to-funder connections and grant-win warm paths instead of direct board overlap.",
                        details={"seeker_people": seeker_count, "overlap": 0},
                    ))

        return diagnostics

    # ------------------------------------------------------------------
    # Stats and readiness
    # ------------------------------------------------------------------

    def _compute_stats(self, profile_id: str) -> dict:
        with self._conn() as conn:
            people_in_graph = conn.execute(
                "SELECT COUNT(*) FROM network_memberships"
            ).fetchone()[0]

            opp_eins = conn.execute(
                "SELECT DISTINCT ein FROM opportunities "
                "WHERE profile_id = ? AND ein IS NOT NULL AND ein != ''",
                (profile_id,),
            ).fetchall()
            opp_ein_set = {r["ein"] for r in opp_eins}

            funders_with = 0
            for ein in opp_ein_set:
                count = conn.execute(
                    "SELECT COUNT(*) FROM network_memberships "
                    "WHERE org_ein = ? AND org_type = 'funder'",
                    (ein,),
                ).fetchone()[0]
                if count > 0:
                    funders_with += 1

            seeker_count = conn.execute(
                "SELECT COUNT(*) FROM network_memberships "
                "WHERE profile_id = ? AND org_type = 'seeker'",
                (profile_id,),
            ).fetchone()[0]

            return {
                "people_in_graph": people_in_graph,
                "funders_with_people": funders_with,
                "funders_without_people": len(opp_ein_set) - funders_with,
                "seeker_board_size": seeker_count,
            }

    @staticmethod
    def _compute_readiness(
        seeker_board_size: int,
        funders_with_people: int,
        total_funders: int,
        funder_connection_count: int,
        warm_path_count: int,
    ) -> float:
        """
        Network readiness score (0.0–1.0) measuring how prepared
        the data is for meaningful relationship analysis.
        """
        score = 0.0

        # Seeker board (25%)
        if seeker_board_size >= 7:
            score += 0.25
        elif seeker_board_size >= 3:
            score += 0.15
        elif seeker_board_size >= 1:
            score += 0.05

        # Funder coverage (35%)
        if total_funders > 0:
            coverage = funders_with_people / total_funders
            score += 0.35 * min(1.0, coverage * 1.5)  # boost partial coverage

        # Funder connections discovered (25%)
        if funder_connection_count >= 20:
            score += 0.25
        elif funder_connection_count >= 5:
            score += 0.15
        elif funder_connection_count >= 1:
            score += 0.08

        # Warm paths (15%)
        if warm_path_count >= 5:
            score += 0.15
        elif warm_path_count >= 1:
            score += 0.08

        return round(min(1.0, score), 2)


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _serialise_funder_conn(c: FunderConnection) -> dict:
    return {
        "funder1_ein": c.funder1_ein,
        "funder1_name": c.funder1_name,
        "funder2_ein": c.funder2_ein,
        "funder2_name": c.funder2_name,
        "shared_people": c.shared_people,
        "connection_count": c.connection_count,
        "strength": c.strength,
    }


def _serialise_warm_path(p: WarmPath) -> dict:
    return {
        "funder_ein": p.funder_ein,
        "funder_name": p.funder_name,
        "source": p.source,
        "win_details": p.win_details,
        "contact": p.contact,
        "connected_funder_ein": p.connected_funder_ein,
        "connected_funder_name": p.connected_funder_name,
        "warmth_score": p.warmth_score,
    }


def _serialise_diagnostic(d: NetworkDiagnostic) -> dict:
    return {
        "category": d.category,
        "severity": d.severity,
        "message": d.message,
        "action": d.action,
        "details": d.details,
    }
