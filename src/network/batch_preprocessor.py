"""
NetworkBatchPreprocessor — multi-stage pipeline to bulk-populate the people
database from free data sources before resorting to AI-powered enrichment.

Cost tiers:
  Stage 1  ($0.00) — Discover filing histories via ProPublica API
  Stage 2  ($0.00) — Fetch 990 XML + parse officers (no AI)
  Stage 3  ($0.00) — Migrate everything into people + organization_roles
  Stage 4  ($0.00) — Deduplicate and score connections
  Stage 5  ($$)    — Optional: AI web scraping for remaining gaps (Haiku)

All stages are idempotent and can be resumed safely.
"""

import asyncio
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class StageResult:
    """Result from a single pipeline stage."""
    stage: str
    status: str  # "completed", "skipped", "partial", "error"
    items_processed: int = 0
    items_added: int = 0
    items_skipped: int = 0
    errors: int = 0
    cost_usd: float = 0.0
    detail: str = ""
    duration_ms: float = 0.0


@dataclass
class BatchPreprocessResult:
    """Result from the full batch pipeline."""
    profile_id: str
    started_at: str = ""
    completed_at: str = ""
    stages: list = field(default_factory=list)
    total_people_before: int = 0
    total_people_after: int = 0
    total_roles_before: int = 0
    total_roles_after: int = 0
    total_cost_usd: float = 0.0
    funders_with_officers: int = 0
    funders_without_officers: int = 0


class NetworkBatchPreprocessor:
    """
    Orchestrates a multi-stage pipeline to populate the people network graph
    for a given profile, prioritizing free data sources.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_pipeline(
        self,
        profile_id: str,
        max_eins: int = 200,
        include_web_scraping: bool = False,
        web_scraping_limit: int = 10,
        concurrency: int = 3,
    ) -> BatchPreprocessResult:
        """
        Run the full preprocessing pipeline for a profile.

        Args:
            profile_id: Profile to process
            max_eins: Maximum funder EINs to process
            include_web_scraping: Whether to run Stage 5 (costs money)
            web_scraping_limit: Max orgs for web scraping (controls cost)
            concurrency: Max concurrent HTTP requests

        Returns:
            BatchPreprocessResult with per-stage details
        """
        result = BatchPreprocessResult(
            profile_id=profile_id,
            started_at=self._now(),
        )

        # Snapshot before counts
        result.total_people_before, result.total_roles_before = self._count_people_roles()

        # Get all funder EINs for this profile
        funder_eins = self._get_funder_eins(profile_id, max_eins)
        if not funder_eins:
            result.completed_at = self._now()
            result.stages.append(StageResult(
                stage="discovery",
                status="skipped",
                detail="No funder EINs found for this profile",
            ))
            return result

        logger.info(
            f"[BatchPreprocessor] Starting pipeline for profile {profile_id} "
            f"with {len(funder_eins)} funder EINs"
        )

        # Stage 1: Discover filing histories ($0.00)
        s1 = await self._stage_discover_filings(funder_eins, concurrency)
        result.stages.append(s1)

        # Stage 2: Fetch XML + parse officers ($0.00)
        s2 = await self._stage_xml_officer_extraction(funder_eins, concurrency)
        result.stages.append(s2)

        # Stage 3: Ingest into network_memberships, then ETL to people table ($0.00)
        s3 = self._stage_ingest_and_etl(profile_id, funder_eins)
        result.stages.append(s3)

        # Stage 4: Deduplicate + rebuild connections ($0.00)
        s4 = self._stage_dedup_and_score(profile_id)
        result.stages.append(s4)

        # Stage 5: Optional web scraping for gaps ($$)
        if include_web_scraping:
            s5 = await self._stage_web_enrichment(
                profile_id, funder_eins, web_scraping_limit, concurrency
            )
            result.stages.append(s5)

        # Final counts
        result.total_people_after, result.total_roles_after = self._count_people_roles()
        result.total_cost_usd = sum(s.cost_usd for s in result.stages)
        result.completed_at = self._now()

        # Coverage summary
        with_officers, without_officers = self._coverage_summary(funder_eins)
        result.funders_with_officers = with_officers
        result.funders_without_officers = without_officers

        logger.info(
            f"[BatchPreprocessor] Pipeline complete for profile {profile_id}: "
            f"people {result.total_people_before}→{result.total_people_after}, "
            f"roles {result.total_roles_before}→{result.total_roles_after}, "
            f"cost ${result.total_cost_usd:.4f}"
        )

        return result

    async def run_stage(
        self,
        profile_id: str,
        stage: str,
        max_eins: int = 200,
        concurrency: int = 3,
        web_scraping_limit: int = 10,
    ) -> StageResult:
        """Run a single stage of the pipeline (for granular control)."""

        if stage == "xml_officers":
            # Skip EINs already in graph so limit gives "next N unprocessed"
            funder_eins = self._get_funder_eins(profile_id, max_eins, skip_in_graph=True)
        else:
            funder_eins = self._get_funder_eins(profile_id, max_eins)

        if stage == "discover_filings":
            return await self._stage_discover_filings(funder_eins, concurrency)
        elif stage == "xml_officers":
            return await self._stage_xml_officer_extraction(funder_eins, concurrency, profile_id=profile_id)
        elif stage == "ingest_etl":
            return self._stage_ingest_and_etl(profile_id, funder_eins)
        elif stage == "dedup_score":
            return self._stage_dedup_and_score(profile_id)
        elif stage == "web_enrichment":
            return await self._stage_web_enrichment(
                profile_id, funder_eins, web_scraping_limit, concurrency
            )
        else:
            return StageResult(stage=stage, status="error", detail=f"Unknown stage: {stage}")

    def get_coverage_report(self, profile_id: str, max_eins: int = 200) -> dict:
        """
        Return a coverage report showing what data exists for each funder EIN.
        Helps users decide which stages to run. $0.00 cost.
        """
        funder_eins = self._get_funder_eins(profile_id, max_eins)
        if not funder_eins:
            return {"profile_id": profile_id, "funders": [], "summary": {}}

        report = []
        summary = {
            "total_funders": len(funder_eins),
            "has_filing_history": 0,
            "has_xml_officers": 0,
            "has_web_data": 0,
            "in_people_table": 0,
            "in_memberships_only": 0,
            "no_data": 0,
        }

        with self._conn() as conn:
            for item in funder_eins:
                ein = item["ein"]
                org_name = item["org_name"]

                # Check ein_intelligence
                ei = conn.execute(
                    "SELECT web_data, filing_history, pdf_analyses FROM ein_intelligence WHERE ein = ?",
                    (ein,),
                ).fetchone()

                has_filing = bool(ei and ei["filing_history"])
                has_web = bool(ei and ei["web_data"])
                has_pdf = bool(ei and ei["pdf_analyses"])

                # Check network_memberships
                membership_count = conn.execute(
                    "SELECT COUNT(*) FROM network_memberships "
                    "WHERE org_ein = ? AND org_type = 'funder'",
                    (ein,),
                ).fetchone()[0]

                # Check people/organization_roles
                people_count = 0
                try:
                    people_count = conn.execute(
                        "SELECT COUNT(DISTINCT p.id) FROM people p "
                        "JOIN organization_roles r ON p.id = r.person_id "
                        "WHERE r.organization_ein = ?",
                        (ein,),
                    ).fetchone()[0]
                except sqlite3.OperationalError:
                    pass  # tables may not exist yet

                # Determine recommended action
                if people_count > 0:
                    action = "complete"
                    summary["in_people_table"] += 1
                elif membership_count > 0:
                    action = "run_etl"
                    summary["in_memberships_only"] += 1
                elif has_filing or has_pdf:
                    action = "run_xml_parse"
                    summary["has_filing_history"] += 1
                elif has_web:
                    action = "run_ingest"
                    summary["has_web_data"] += 1
                else:
                    action = "needs_discovery"
                    summary["no_data"] += 1

                if has_filing:
                    summary["has_filing_history"] += 0  # already counted above
                if membership_count > 0 or people_count > 0:
                    summary["has_xml_officers"] += 1

                report.append({
                    "ein": ein,
                    "org_name": org_name,
                    "has_filing_history": has_filing,
                    "has_web_data": has_web,
                    "has_pdf_analysis": has_pdf,
                    "people_in_memberships": membership_count,
                    "people_in_normalized_table": people_count,
                    "recommended_action": action,
                })

        return {
            "profile_id": profile_id,
            "funders": report,
            "summary": summary,
        }

    # ------------------------------------------------------------------
    # Stage 1: Discover filing histories ($0.00)
    # ------------------------------------------------------------------

    async def _stage_discover_filings(
        self, funder_eins: list, concurrency: int
    ) -> StageResult:
        """
        For EINs missing filing_history, fetch from ProPublica API.
        Cost: $0.00 (free public API, 500 calls/hr).
        """
        import time
        start = time.time()

        # Filter to EINs that lack filing_history
        eins_needing_filings = []
        with self._conn() as conn:
            for item in funder_eins:
                ein = item["ein"]
                row = conn.execute(
                    "SELECT filing_history FROM ein_intelligence WHERE ein = ?",
                    (ein,),
                ).fetchone()
                if not row or not row["filing_history"]:
                    eins_needing_filings.append(item)

        if not eins_needing_filings:
            return StageResult(
                stage="discover_filings",
                status="skipped",
                detail="All funders already have filing histories",
                items_skipped=len(funder_eins),
                duration_ms=(time.time() - start) * 1000,
            )

        logger.info(
            f"[Stage 1] Discovering filings for {len(eins_needing_filings)} EINs "
            f"({len(funder_eins) - len(eins_needing_filings)} already cached)"
        )

        from src.clients.propublica_client import ProPublicaClient
        from src.database.database_manager import DatabaseManager

        db_mgr = DatabaseManager(self.db_path)
        sem = asyncio.Semaphore(concurrency)
        found = 0
        errors = 0

        async def fetch_one(item):
            nonlocal found, errors
            async with sem:
                try:
                    client = ProPublicaClient()
                    org_data = await client.get_organization_by_ein(item["ein"])
                    filings = []
                    if org_data:
                        for f in org_data.get("filings_with_data", [])[:10]:
                            filings.append({
                                "tax_year": f.get("tax_prd_yr"),
                                "pdf_url": f.get("pdf_url"),
                                "filing_date": f.get("updated"),
                                "source": "api",
                            })
                    if filings:
                        db_mgr.upsert_ein_intelligence(item["ein"], filing_history=filings)
                        found += 1
                    await asyncio.sleep(0.25)  # Respect rate limits
                except Exception as e:
                    logger.warning(f"[Stage 1] EIN {item['ein']}: {e}")
                    errors += 1

        await asyncio.gather(*[fetch_one(item) for item in eins_needing_filings])

        return StageResult(
            stage="discover_filings",
            status="completed",
            items_processed=len(eins_needing_filings),
            items_added=found,
            items_skipped=len(funder_eins) - len(eins_needing_filings),
            errors=errors,
            cost_usd=0.0,
            detail=f"Discovered filing histories for {found}/{len(eins_needing_filings)} EINs",
            duration_ms=(time.time() - start) * 1000,
        )

    # ------------------------------------------------------------------
    # Stage 2: XML officer extraction ($0.00)
    # ------------------------------------------------------------------

    async def _stage_xml_officer_extraction(
        self, funder_eins: list, concurrency: int, profile_id: str = None
    ) -> StageResult:
        """
        Fetch 990 XML from ProPublica and parse officers. No AI involved.
        Cost: $0.00.
        """
        import time
        import xml.etree.ElementTree as ET
        start = time.time()

        # Filter to EINs with 0 people in network_memberships (real or sentinel)
        targets = []
        with self._conn() as conn:
            for item in funder_eins:
                count = conn.execute(
                    "SELECT COUNT(*) FROM network_memberships "
                    "WHERE org_ein = ? AND org_type IN ('funder', 'funder_xml_no_data')",
                    (item["ein"],),
                ).fetchone()[0]
                if count == 0:
                    targets.append(item)

        if not targets:
            return StageResult(
                stage="xml_officers",
                status="skipped",
                detail="All funders already have officers in graph",
                items_skipped=len(funder_eins),
                duration_ms=(time.time() - start) * 1000,
            )

        logger.info(
            f"[Stage 2] Extracting XML officers for {len(targets)} EINs "
            f"({len(funder_eins) - len(targets)} already populated)"
        )

        from src.utils.xml_fetcher import XMLFetcher
        from src.network.graph_builder import NetworkGraphBuilder

        fetcher = XMLFetcher()
        builder = NetworkGraphBuilder(self.db_path)
        sem = asyncio.Semaphore(concurrency)

        officers_added = 0
        eins_with_officers = 0
        eins_no_xml = 0
        errors = 0

        async def process_one(item):
            nonlocal officers_added, eins_with_officers, eins_no_xml, errors
            async with sem:
                ein = item["ein"]
                org_name = item["org_name"]
                try:
                    xml_bytes = await fetcher.fetch_xml_by_ein(ein)
                    if not xml_bytes:
                        eins_no_xml += 1
                        self._mark_xml_no_data(ein, org_name)
                        return

                    officers = self._extract_officers_from_xml(xml_bytes, ein)
                    if not officers:
                        eins_no_xml += 1
                        self._mark_xml_no_data(ein, org_name)
                        return

                    # Ingest into network_memberships
                    ei = {"web_data": {"leadership": officers}}
                    added = builder.ingest_funder_ein(ein, org_name, ei)
                    officers_added += added
                    eins_with_officers += 1

                    logger.debug(
                        f"[Stage 2] EIN {ein}: {len(officers)} officers from XML"
                    )
                    await asyncio.sleep(0.3)  # Polite delay
                except Exception as e:
                    logger.warning(f"[Stage 2] EIN {ein}: {e}")
                    errors += 1

        await asyncio.gather(*[process_one(t) for t in targets])

        return StageResult(
            stage="xml_officers",
            status="completed",
            items_processed=len(targets),
            items_added=officers_added,
            items_skipped=eins_no_xml,
            errors=errors,
            cost_usd=0.0,
            detail=(
                f"Extracted officers from {eins_with_officers} EINs, "
                f"{officers_added} people added, "
                f"{eins_no_xml} EINs had no XML available"
            ),
            duration_ms=(time.time() - start) * 1000,
        )

    # ------------------------------------------------------------------
    # Stage 3: Ingest + ETL ($0.00)
    # ------------------------------------------------------------------

    def _stage_ingest_and_etl(
        self, profile_id: str, funder_eins: list
    ) -> StageResult:
        """
        1. Ingest all cached ein_intelligence into network_memberships
        2. Migrate network_memberships into people + organization_roles
        Cost: $0.00 (pure DB operations).
        """
        import time
        start = time.time()

        # Step 1: Ingest from ein_intelligence cache
        from src.network.graph_builder import NetworkGraphBuilder
        builder = NetworkGraphBuilder(self.db_path)
        ingest_stats = builder.ingest_all_funders_from_cache(profile_id)

        # Step 2: ETL from network_memberships → people + organization_roles
        from src.network.people_etl import PeopleETL
        etl = PeopleETL(self.db_path)
        etl.ensure_tables()
        etl_stats = etl.migrate_from_memberships()

        # Step 3: Also ingest 990 officer data for any EINs we fetched XML for
        # This adds richer data (compensation, hours, role flags) from the XML
        self._etl_xml_officers_to_people(funder_eins, etl)

        total_added = (
            ingest_stats.get("people_added", 0) +
            etl_stats.get("people_created", 0)
        )

        return StageResult(
            stage="ingest_etl",
            status="completed",
            items_processed=ingest_stats.get("eins_processed", 0),
            items_added=total_added,
            errors=etl_stats.get("errors", 0),
            cost_usd=0.0,
            detail=(
                f"Ingested {ingest_stats.get('people_added', 0)} from cache, "
                f"ETL created {etl_stats.get('people_created', 0)} people / "
                f"{etl_stats.get('roles_created', 0)} roles"
            ),
            duration_ms=(time.time() - start) * 1000,
        )

    # ------------------------------------------------------------------
    # Stage 4: Dedup + score ($0.00)
    # ------------------------------------------------------------------

    def _stage_dedup_and_score(self, profile_id: str) -> StageResult:
        """
        1. Auto-merge high-confidence duplicates
        2. Rebuild board connections with strength scoring
        3. Compute person influence metrics
        Cost: $0.00.
        """
        import time
        start = time.time()

        # Step 1: Deduplicate
        from src.network.person_deduplication import PersonDeduplicationService
        dedup = PersonDeduplicationService(self.db_path)
        merge_stats = dedup.auto_merge(min_confidence=0.92)

        # Step 2: Rebuild connections
        from src.network.connection_strength import ConnectionStrengthScorer
        scorer = ConnectionStrengthScorer(self.db_path)
        conn_stats = scorer.rebuild_board_connections(profile_id=profile_id)

        # Step 3: Influence scores
        influence_stats = scorer.rebuild_all_influence_scores()

        return StageResult(
            stage="dedup_score",
            status="completed",
            items_processed=merge_stats.get("pairs_found", 0) + influence_stats.get("people_scored", 0),
            items_added=conn_stats.get("connections_created", 0),
            cost_usd=0.0,
            detail=(
                f"Merged {merge_stats.get('pairs_merged', 0)} duplicates, "
                f"built {conn_stats.get('connections_created', 0)} connections, "
                f"scored {influence_stats.get('people_scored', 0)} people"
            ),
            duration_ms=(time.time() - start) * 1000,
        )

    # ------------------------------------------------------------------
    # Stage 5: Optional web enrichment ($$)
    # ------------------------------------------------------------------

    async def _stage_web_enrichment(
        self,
        profile_id: str,
        funder_eins: list,
        limit: int,
        concurrency: int,
    ) -> StageResult:
        """
        Use Tool 25 (Web Intelligence) to scrape leadership data for funders
        that still have 0 officers after free extraction.
        Cost: ~$0.003-$0.01 per org (Claude Haiku).
        """
        import time
        start = time.time()

        # Find funders still missing officers
        gaps = []
        with self._conn() as conn:
            for item in funder_eins:
                count = conn.execute(
                    "SELECT COUNT(*) FROM network_memberships "
                    "WHERE org_ein = ? AND org_type = 'funder'",
                    (item["ein"],),
                ).fetchone()[0]
                if count == 0:
                    # Check if we have a website URL to scrape
                    ei = conn.execute(
                        "SELECT web_data FROM ein_intelligence WHERE ein = ?",
                        (item["ein"],),
                    ).fetchone()
                    has_existing_web = bool(ei and ei["web_data"])
                    if not has_existing_web:
                        gaps.append(item)

        if not gaps:
            return StageResult(
                stage="web_enrichment",
                status="skipped",
                detail="No funders need web enrichment (all have officers or web data)",
                duration_ms=(time.time() - start) * 1000,
            )

        # Limit to control costs
        gaps = gaps[:limit]
        estimated_cost = len(gaps) * 0.007  # ~$0.007 avg per org

        logger.info(
            f"[Stage 5] Web enrichment for {len(gaps)} funders "
            f"(estimated cost: ${estimated_cost:.2f})"
        )

        try:
            from tools.web_intelligence_tool.app import WebIntelligenceTool
        except ImportError:
            return StageResult(
                stage="web_enrichment",
                status="error",
                detail="Web Intelligence Tool not available (import failed)",
                duration_ms=(time.time() - start) * 1000,
            )

        from src.network.graph_builder import NetworkGraphBuilder
        from src.database.database_manager import DatabaseManager

        builder = NetworkGraphBuilder(self.db_path)
        db_mgr = DatabaseManager(self.db_path)
        sem = asyncio.Semaphore(min(concurrency, 2))  # Conservative for AI calls
        enriched = 0
        officers_found = 0
        errors = 0

        async def enrich_one(item):
            nonlocal enriched, officers_found, errors
            async with sem:
                ein = item["ein"]
                try:
                    tool = WebIntelligenceTool()
                    result = await tool.execute(
                        ein=ein,
                        organization_name=item["org_name"],
                        use_case="FOUNDATION_RESEARCH",
                    )
                    if result.is_success() and result.data:
                        data = result.data
                        leadership = []
                        if hasattr(data, "leadership"):
                            leadership = data.leadership or []
                        elif isinstance(data, dict):
                            leadership = data.get("leadership", [])

                        if leadership:
                            # Store in ein_intelligence
                            web_data = {"leadership": leadership}
                            db_mgr.upsert_ein_intelligence(
                                ein, web_data=web_data, web_data_source="tool_25"
                            )
                            # Ingest into graph
                            added = builder.ingest_funder_ein(
                                ein, item["org_name"], {"web_data": web_data}
                            )
                            officers_found += added
                            enriched += 1
                except Exception as e:
                    logger.warning(f"[Stage 5] EIN {ein}: {e}")
                    errors += 1

        await asyncio.gather(*[enrich_one(g) for g in gaps])

        actual_cost = enriched * 0.007  # Approximate

        return StageResult(
            stage="web_enrichment",
            status="completed",
            items_processed=len(gaps),
            items_added=officers_found,
            errors=errors,
            cost_usd=actual_cost,
            detail=(
                f"Enriched {enriched}/{len(gaps)} funders via web scraping, "
                f"{officers_found} officers found"
            ),
            duration_ms=(time.time() - start) * 1000,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _mark_xml_no_data(self, ein: str, org_name: str) -> None:
        """Write a sentinel row so this EIN is skipped in future batch runs."""
        from src.network.name_normalizer import NameNormalizer
        normalizer = NameNormalizer()
        now = self._now()
        sentinel_id = normalizer.membership_id(f"__no_xml__{ein}", ein)
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO network_memberships
                    (id, person_hash, display_name, org_ein, org_name, org_type,
                     profile_id, source, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'funder_xml_no_data', NULL, 'xml_stage', NULL, ?, ?)
                ON CONFLICT(id) DO UPDATE SET updated_at = excluded.updated_at
                """,
                (sentinel_id, sentinel_id, "__no_xml__", ein, org_name or ein, now, now),
            )
            conn.commit()
        logger.debug(f"[Stage 2] Marked EIN {ein} as funder_xml_no_data (no XML or no officers)")

    def _get_funder_eins(self, profile_id: str, limit: int, skip_in_graph: bool = False) -> list:
        """Get distinct funder EINs linked to a profile's opportunities, ordered by score.

        Args:
            skip_in_graph: If True, exclude EINs already in network_memberships so that
                           limit gives "next N unprocessed" rather than "top N overall".
                           Also skips funder_xml_no_data sentinels (no XML available).
        """
        with self._conn() as conn:
            if skip_in_graph:
                rows = conn.execute(
                    "SELECT ein, organization_name FROM opportunities "
                    "WHERE profile_id = ? AND ein IS NOT NULL AND ein != '' "
                    "  AND ein NOT IN ("
                    "    SELECT DISTINCT org_ein FROM network_memberships "
                    "    WHERE org_type IN ('funder', 'funder_xml_no_data')"
                    "  ) "
                    "ORDER BY COALESCE(overall_score, 0) DESC "
                    "LIMIT ?",
                    (profile_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT ein, organization_name FROM opportunities "
                    "WHERE profile_id = ? AND ein IS NOT NULL AND ein != '' "
                    "ORDER BY COALESCE(overall_score, 0) DESC "
                    "LIMIT ?",
                    (profile_id, limit),
                ).fetchall()
        seen: set = set()
        result = []
        for r in rows:
            if r["ein"] not in seen:
                seen.add(r["ein"])
                result.append({"ein": r["ein"], "org_name": r["organization_name"] or r["ein"]})
        return result

    def _count_people_roles(self) -> tuple:
        """Return (people_count, roles_count) from normalized tables."""
        try:
            with self._conn() as conn:
                people = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
                roles = conn.execute("SELECT COUNT(*) FROM organization_roles").fetchone()[0]
                return people, roles
        except sqlite3.OperationalError:
            return 0, 0

    def _coverage_summary(self, funder_eins: list) -> tuple:
        """Return (funders_with_officers, funders_without_officers)."""
        with_officers = 0
        without_officers = 0
        with self._conn() as conn:
            for item in funder_eins:
                count = conn.execute(
                    "SELECT COUNT(*) FROM network_memberships "
                    "WHERE org_ein = ? AND org_type = 'funder'",
                    (item["ein"],),
                ).fetchone()[0]
                if count > 0:
                    with_officers += 1
                else:
                    without_officers += 1
        return with_officers, without_officers

    def _etl_xml_officers_to_people(self, funder_eins: list, etl) -> int:
        """
        For EINs where we have cached XML data, extract richer officer info
        (compensation, hours, role flags) and ingest into people table.
        """
        ingested = 0
        with self._conn() as conn:
            for item in funder_eins:
                ein = item["ein"]
                # Check if ein_intelligence has pdf_analyses with officers
                row = conn.execute(
                    "SELECT pdf_analyses FROM ein_intelligence WHERE ein = ?",
                    (ein,),
                ).fetchone()
                if not row or not row["pdf_analyses"]:
                    continue

                try:
                    pdf_data = json.loads(row["pdf_analyses"]) if isinstance(row["pdf_analyses"], str) else row["pdf_analyses"]
                    if not isinstance(pdf_data, dict):
                        continue
                    for year_key, analysis in pdf_data.items():
                        if not isinstance(analysis, dict):
                            continue
                        officers = analysis.get("officers_and_directors", [])
                        if officers:
                            filing_year = None
                            try:
                                filing_year = int(year_key)
                            except (ValueError, TypeError):
                                pass
                            stats = etl.ingest_from_990_officers(
                                ein, item["org_name"], officers, filing_year or 2024
                            )
                            ingested += stats.get("people_created", 0)
                except (json.JSONDecodeError, Exception) as e:
                    logger.debug(f"[ETL] Skipping pdf_analyses for EIN {ein}: {e}")

        return ingested

    @staticmethod
    def _extract_officers_from_xml(xml_bytes: bytes, ein: str) -> list:
        """
        Parse 990/990-PF/990-EZ XML and extract officers + directors.
        Returns list of {"name": str, "title": str} dicts.
        No AI involved — pure XML parsing.
        """
        import xml.etree.ElementTree as ET

        officers = []
        try:
            root = ET.fromstring(xml_bytes)
            ns = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
            pfx = f"{{{ns}}}" if ns else ""

            # Form 990 Part VII Section A
            for grp in root.iter(f"{pfx}Form990PartVIISectionAGrp"):
                name = (grp.findtext(f"{pfx}PersonNm") or grp.findtext("PersonNm") or "").strip()
                title = (grp.findtext(f"{pfx}TitleTxt") or grp.findtext("TitleTxt") or "").strip()
                if name:
                    officers.append({"name": name, "title": title or None})

            # Form 990-PF Part VIII
            for grp in root.iter(f"{pfx}OfficerDirTrstKeyEmplGrp"):
                name = (grp.findtext(f"{pfx}PersonNm") or grp.findtext("PersonNm") or "").strip()
                if not name:
                    name = (grp.findtext(f"{pfx}BusinessNameLine1Txt") or
                            grp.findtext("BusinessNameLine1Txt") or "").strip()
                title = (grp.findtext(f"{pfx}TitleTxt") or grp.findtext("TitleTxt") or "").strip()
                if name:
                    officers.append({"name": name, "title": title or None})

            # Form 990-EZ Part IV
            for grp in root.iter(f"{pfx}OfficerDirectorTrusteeKeyEmplGrp"):
                name = (grp.findtext(f"{pfx}PersonFullNm") or
                        grp.findtext("PersonFullNm") or "").strip()
                title = (grp.findtext(f"{pfx}TitleTxt") or grp.findtext("TitleTxt") or "").strip()
                if name:
                    officers.append({"name": name, "title": title or None})

        except Exception as e:
            logger.warning(f"[xml-parse] Error for EIN {ein}: {e}")

        # Deduplicate by name
        seen = set()
        unique = []
        for o in officers:
            key = o["name"].lower()
            if key not in seen:
                seen.add(key)
                unique.append(o)
        return unique
