"""
Network Router — graph population, coverage stats, filing discovery, funder ranking.
All endpoints are $0.00 (pure DB reads + free ProPublica HTTP).
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import json
import logging
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/network", tags=["network"])


# ── Request / Response models ──────────────────────────────────────────────────

class PopulateGraphRequest(BaseModel):
    profile_id: str


class DiscoverFilingsRequest(BaseModel):
    profile_id: str
    limit: int = 2000


class RankFundersRequest(BaseModel):
    profile_id: str
    max_degree: int = 3


class XmlOfficerLookupRequest(BaseModel):
    profile_id: str
    limit: int = 2000


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_db_path() -> str:
    from src.config.database_config import get_catalynx_db
    return get_catalynx_db()


def _conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ── Endpoint A: Populate graph from cache ─────────────────────────────────────

@router.post("/populate-graph")
async def populate_graph(req: PopulateGraphRequest):
    """
    Batch-ingest all funder leadership data from ein_intelligence into
    network_memberships for every funder EIN linked to this profile.
    Cost: $0.00
    """
    try:
        from src.network.graph_builder import NetworkGraphBuilder
        db_path = _get_db_path()
        builder = NetworkGraphBuilder(db_path)
        stats = builder.ingest_all_funders_from_cache(req.profile_id)
        return {
            "success": True,
            "profile_id": req.profile_id,
            **stats,
        }
    except Exception as e:
        logger.error(f"[network/populate-graph] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── Endpoint B: Graph coverage stats ──────────────────────────────────────────

@router.get("/graph-stats")
async def graph_stats(profile_id: str = Query(...)):
    """
    Return graph coverage stats for all funders linked to this profile.
    Cost: $0.00
    """
    try:
        db_path = _get_db_path()
        conn = _conn(db_path)
        cur = conn.cursor()

        # Seeker people
        seeker_count = cur.execute(
            "SELECT COUNT(*) FROM network_memberships WHERE profile_id = ? AND org_type = 'seeker'",
            (profile_id,),
        ).fetchone()[0]

        # Funder EINs in graph
        funder_eins_in_graph = cur.execute(
            "SELECT COUNT(DISTINCT org_ein) FROM network_memberships "
            "WHERE org_type = 'funder' AND org_ein IN ("
            "  SELECT DISTINCT ein FROM opportunities WHERE profile_id = ? AND ein IS NOT NULL"
            ")",
            (profile_id,),
        ).fetchone()[0]

        # Funder people in graph
        funder_people_in_graph = cur.execute(
            "SELECT COUNT(*) FROM network_memberships "
            "WHERE org_type = 'funder' AND org_ein IN ("
            "  SELECT DISTINCT ein FROM opportunities WHERE profile_id = ? AND ein IS NOT NULL"
            ")",
            (profile_id,),
        ).fetchone()[0]

        # Total people
        total_people = cur.execute(
            "SELECT COUNT(*) FROM network_memberships WHERE "
            "(profile_id = ? AND org_type = 'seeker') OR org_ein IN ("
            "  SELECT DISTINCT ein FROM opportunities WHERE profile_id = ? AND ein IS NOT NULL"
            ")",
            (profile_id, profile_id),
        ).fetchone()[0]

        # Coverage per funder — include all opportunity IDs for this EIN
        opp_rows = cur.execute(
            "SELECT ein, organization_name, COUNT(*) as opp_count "
            "FROM opportunities WHERE profile_id = ? AND ein IS NOT NULL AND ein != '' "
            "GROUP BY ein",
            (profile_id,),
        ).fetchall()

        coverage = []
        for row in opp_rows:
            ein = row["ein"]
            org_name = row["organization_name"] or ein

            # Opportunity IDs for this EIN (needed to target batch-analyze-990-pdfs)
            opp_id_rows = cur.execute(
                "SELECT id FROM opportunities WHERE profile_id = ? AND ein = ?",
                (profile_id, ein),
            ).fetchall()
            opportunity_ids = [r["id"] for r in opp_id_rows]

            ei_row = cur.execute(
                "SELECT web_data, pdf_analyses, filing_history FROM ein_intelligence WHERE ein = ?",
                (ein,),
            ).fetchone()

            has_web = False
            has_pdf = False
            has_filing = False
            pdf_has_officers = False
            if ei_row:
                has_web = bool(ei_row["web_data"])
                has_filing = bool(ei_row["filing_history"])
                if ei_row["pdf_analyses"]:
                    has_pdf = True
                    # Check whether any analysis actually extracted officers
                    try:
                        pdf_data = json.loads(ei_row["pdf_analyses"]) if isinstance(ei_row["pdf_analyses"], str) else ei_row["pdf_analyses"]
                        if isinstance(pdf_data, dict):
                            pdf_has_officers = any(
                                len(v.get("officers_and_directors") or []) > 0
                                for v in pdf_data.values()
                                if isinstance(v, dict)
                            )
                    except Exception:
                        pass

            people_count = cur.execute(
                "SELECT COUNT(*) FROM network_memberships WHERE org_ein = ? AND org_type = 'funder'",
                (ein,),
            ).fetchone()[0]

            # Preflight status — what's needed to get officers into the graph
            if people_count > 0:
                preflight = "ok"
            elif has_pdf and not pdf_has_officers:
                preflight = "pdf_no_officers"   # PDF ran but no officers found — web scrape may help
            elif has_filing and not has_pdf:
                preflight = "needs_990_search"  # Has filing URL, needs PDF analysis
            elif not has_filing:
                preflight = "needs_url"         # No filing history — run Find URLs first
            else:
                preflight = "unknown"

            coverage.append({
                "ein": ein,
                "org_name": org_name,
                "has_web_data": has_web,
                "has_pdf_data": has_pdf,
                "has_filing_history": has_filing,
                "pdf_has_officers": pdf_has_officers,
                "people_in_graph": people_count,
                "opportunity_count": row["opp_count"],
                "opportunity_ids": opportunity_ids,
                "preflight": preflight,
            })

        conn.close()

        return {
            "profile_id": profile_id,
            "seeker_people": seeker_count,
            "funder_eins_in_graph": funder_eins_in_graph,
            "funder_people_in_graph": funder_people_in_graph,
            "total_people": total_people,
            "coverage": coverage,
        }

    except Exception as e:
        logger.error(f"[network/graph-stats] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── Endpoint C: Discover filing histories (free HTTP, no AI) ──────────────────

@router.post("/discover-filings")
async def discover_filings(req: DiscoverFilingsRequest, background_tasks: BackgroundTasks):
    """
    For EINs lacking filing_history in ein_intelligence, fetch from ProPublica.
    Returns immediately; ProPublica calls run in the background.
    Cost: $0.00 (ProPublica public API).
    """
    try:
        db_path = _get_db_path()
        conn = _conn(db_path)
        cur = conn.cursor()

        opp_rows = cur.execute(
            "SELECT DISTINCT o.ein, o.organization_name "
            "FROM opportunities o "
            "WHERE o.profile_id = ? AND o.ein IS NOT NULL AND o.ein != '' "
            "LIMIT ?",
            (req.profile_id, req.limit),
        ).fetchall()

        eins_to_fetch = []
        already_cached = 0
        for row in opp_rows:
            ein = row["ein"]
            ei_row = cur.execute(
                "SELECT filing_history FROM ein_intelligence WHERE ein = ?", (ein,)
            ).fetchone()
            if ei_row and ei_row["filing_history"]:
                already_cached += 1
            else:
                eins_to_fetch.append({"ein": ein, "org_name": row["organization_name"] or ein})

        conn.close()

        if not eins_to_fetch:
            return {
                "status": "complete",
                "eins_queried": 0,
                "filing_histories_found": 0,
                "already_cached": already_cached,
                "errors": 0,
            }

        async def _run_in_background(items: list, path: str):
            from src.clients.propublica_client import ProPublicaClient
            from src.database.database_manager import DatabaseManager
            db_manager = DatabaseManager(path)
            sem = asyncio.Semaphore(3)
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
                            db_manager.upsert_ein_intelligence(item["ein"], filing_history=filings)
                            found += 1
                        await asyncio.sleep(0.2)
                    except Exception as exc:
                        logger.warning(f"[discover-filings] EIN {item['ein']}: {exc}")
                        errors += 1

            await asyncio.gather(*[fetch_one(item) for item in items])
            logger.info(f"[discover-filings] background complete: {found}/{len(items)} found, {errors} errors")

        background_tasks.add_task(_run_in_background, eins_to_fetch, db_path)

        return {
            "status": "running",
            "eins_queried": len(eins_to_fetch),
            "filing_histories_found": 0,
            "already_cached": already_cached,
            "errors": 0,
            "message": f"Fetching filings for {len(eins_to_fetch)} funders in background — re-run Pre-process when complete",
        }

    except Exception as e:
        logger.error(f"[network/discover-filings] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── Endpoint D: Cross-funder warmth ranking ───────────────────────────────────

@router.post("/rank-funders")
async def rank_funders(req: RankFundersRequest):
    """
    Run BFS for every funder EIN linked to this profile and return a warmth
    ranking.  Cost: $0.00 — pure BFS on network_memberships.
    """
    try:
        from src.network.path_finder import PathFinder
        db_path = _get_db_path()

        conn = _conn(db_path)
        opp_rows = conn.execute(
            "SELECT DISTINCT ein, organization_name FROM opportunities "
            "WHERE profile_id = ? AND ein IS NOT NULL AND ein != ''",
            (req.profile_id,),
        ).fetchall()

        graph_size = conn.execute(
            "SELECT COUNT(*) FROM network_memberships"
        ).fetchone()[0]
        conn.close()

        finder = PathFinder(db_path)
        ranked = []

        for row in opp_rows:
            ein = row["ein"]
            org_name = row["organization_name"] or ein
            paths = finder.find_paths(req.profile_id, ein, max_degree=req.max_degree)

            if paths:
                best_degree = min(p.degree for p in paths)
                paths_found = len(paths)
                # warmth_score = sum(1/degree) capped at 1.0
                warmth_score = min(1.0, sum(1.0 / p.degree for p in paths))
            else:
                best_degree = None
                paths_found = 0
                warmth_score = 0.0

            if warmth_score >= 0.8:
                strength = "hot"
            elif warmth_score >= 0.3:
                strength = "warm"
            elif warmth_score > 0:
                strength = "cold"
            else:
                strength = "unknown"

            ranked.append({
                "ein": ein,
                "org_name": org_name,
                "best_degree": best_degree,
                "paths_found": paths_found,
                "warmth_score": round(warmth_score, 3),
                "strength": strength,
            })

        # Sort: hot first, then by warmth_score desc
        strength_order = {"hot": 0, "warm": 1, "cold": 2, "unknown": 3}
        ranked.sort(key=lambda r: (strength_order[r["strength"]], -r["warmth_score"]))

        return {
            "profile_id": req.profile_id,
            "graph_size": graph_size,
            "ranked_funders": ranked,
        }

    except Exception as e:
        logger.error(f"[network/rank-funders] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── Endpoint E: XML officer lookup (free, no AI) ──────────────────────────────

def _extract_officers_from_xml(xml_bytes: bytes, ein: str) -> list[dict]:
    """
    Parse 990 / 990-PF / 990-EZ XML and extract officers + directors.
    Returns list of {"name": str, "title": str} dicts.
    No AI involved — pure XML parsing.
    """
    officers = []
    try:
        root = ET.fromstring(xml_bytes)
        ns = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
        pfx = f"{{{ns}}}" if ns else ""

        # ── Form 990 Part VII Section A ──────────────────────────────────
        for grp in root.iter(f"{pfx}Form990PartVIISectionAGrp"):
            name = (grp.findtext(f"{pfx}PersonNm") or "").strip()
            if not name:
                name = (grp.findtext("PersonNm") or "").strip()
            title = (grp.findtext(f"{pfx}TitleTxt") or grp.findtext("TitleTxt") or "").strip()
            if name:
                officers.append({"name": name, "title": title or None})

        # ── Form 990-PF Part VIII ────────────────────────────────────────
        # Individual record element is OfficerDirTrstKeyEmplGrp (note: Trst not Trustee)
        for grp in root.iter(f"{pfx}OfficerDirTrstKeyEmplGrp"):
            name = (grp.findtext(f"{pfx}PersonNm") or
                    grp.findtext("PersonNm") or "").strip()
            if not name:
                name = (grp.findtext(f"{pfx}BusinessNameLine1Txt") or
                        grp.findtext("BusinessNameLine1Txt") or "").strip()
            title = (grp.findtext(f"{pfx}TitleTxt") or grp.findtext("TitleTxt") or "").strip()
            if name:
                officers.append({"name": name, "title": title or None})

        # ── Form 990-EZ Part IV ──────────────────────────────────────────
        for grp in root.iter(f"{pfx}OfficerDirectorTrusteeKeyEmplGrp"):
            name = (grp.findtext(f"{pfx}PersonFullNm") or
                    grp.findtext("PersonFullNm") or "").strip()
            title = (grp.findtext(f"{pfx}TitleTxt") or grp.findtext("TitleTxt") or "").strip()
            if name:
                officers.append({"name": name, "title": title or None})

    except Exception as exc:
        logger.warning(f"[xml-officer-lookup] XML parse error for EIN {ein}: {exc}")

    # Deduplicate by name
    seen = set()
    unique = []
    for o in officers:
        key = o["name"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(o)
    return unique


@router.post("/xml-officer-lookup")
async def xml_officer_lookup(req: XmlOfficerLookupRequest):
    """
    For funders missing officer data (any preflight status except 'ok'), fetch their
    990 XML from ProPublica and parse officers directly — no AI, no PDF, $0.00.

    Writes found officers straight into network_memberships via ingest_funder_ein().
    Also refreshes graph-stats preflight flags automatically.
    """
    try:
        from src.utils.xml_fetcher import XMLFetcher
        from src.network.graph_builder import NetworkGraphBuilder
        from src.database.database_manager import DatabaseManager

        db_path = _get_db_path()
        conn = _conn(db_path)

        # Fetch funders that need officer data
        opp_rows = conn.execute(
            "SELECT DISTINCT o.ein, o.organization_name "
            "FROM opportunities o "
            "WHERE o.profile_id = ? AND o.ein IS NOT NULL AND o.ein != '' "
            "LIMIT ?",
            (req.profile_id, req.limit),
        ).fetchall()
        conn.close()

        # Filter to those already in network_memberships with 0 people
        # (same logic as preflight != 'ok')
        conn2 = _conn(db_path)
        targets = []
        for row in opp_rows:
            ein = row["ein"]
            count = conn2.execute(
                "SELECT COUNT(*) FROM network_memberships WHERE org_ein = ? AND org_type = 'funder'",
                (ein,),
            ).fetchone()[0]
            if count == 0:
                targets.append({"ein": ein, "org_name": row["organization_name"] or ein})
        conn2.close()

        if not targets:
            return {
                "success": True,
                "message": "All funders already have officer data in graph",
                "eins_attempted": 0,
                "eins_with_officers": 0,
                "officers_added": 0,
                "eins_no_xml": 0,
            }

        fetcher = XMLFetcher()
        builder = NetworkGraphBuilder(db_path)
        db_mgr = DatabaseManager(db_path)
        sem = asyncio.Semaphore(3)

        eins_with_officers = 0
        officers_added = 0
        eins_no_xml = 0
        per_funder = []

        async def lookup_one(item):
            nonlocal eins_with_officers, officers_added, eins_no_xml
            async with sem:
                ein = item["ein"]
                org_name = item["org_name"]
                try:
                    xml_bytes = await fetcher.fetch_xml_by_ein(ein)
                    if not xml_bytes:
                        eins_no_xml += 1
                        per_funder.append({"ein": ein, "org_name": org_name, "status": "no_xml", "officers": 0})
                        return

                    officers = _extract_officers_from_xml(xml_bytes, ein)
                    if not officers:
                        eins_no_xml += 1
                        per_funder.append({"ein": ein, "org_name": org_name, "status": "xml_no_officers", "officers": 0})
                        return

                    # Ingest into network_memberships
                    ei = {"web_data": {"leadership": officers}}
                    added = builder.ingest_funder_ein(ein, org_name, ei)
                    officers_added += added
                    eins_with_officers += 1

                    # Touch ein_intelligence.updated_at so cache skip logic sees fresh data
                    db_mgr.upsert_ein_intelligence(ein, org_name=org_name)

                    per_funder.append({"ein": ein, "org_name": org_name, "status": "ok", "officers": len(officers)})
                    logger.info(f"[xml-officer-lookup] EIN {ein}: {len(officers)} officers from XML")

                    await asyncio.sleep(0.3)  # polite delay
                except Exception as exc:
                    logger.warning(f"[xml-officer-lookup] EIN {ein}: {exc}")
                    per_funder.append({"ein": ein, "org_name": org_name, "status": "error", "officers": 0})

        await asyncio.gather(*[lookup_one(t) for t in targets])

        return {
            "success": True,
            "eins_attempted": len(targets),
            "eins_with_officers": eins_with_officers,
            "officers_added": officers_added,
            "eins_no_xml": eins_no_xml,
            "per_funder": per_funder,
        }

    except Exception as e:
        logger.error(f"[network/xml-officer-lookup] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
