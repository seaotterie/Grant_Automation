"""
People Router — CRUD, search, deduplication, ETL, and network pathways
for the normalized people + organization_roles tables.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import sqlite3

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/people", tags=["people"])


# ── Request / Response models ─────────────────────────────────────────────────

class PersonResponse(BaseModel):
    id: int
    normalized_name: Optional[str] = None
    original_name: Optional[str] = None
    name_hash: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    biography: Optional[str] = None
    linkedin_url: Optional[str] = None
    personal_website: Optional[str] = None
    data_quality_score: Optional[int] = None
    confidence_level: Optional[float] = None
    source_count: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_verified_at: Optional[str] = None
    organization_roles: List[dict] = []


class PersonSearchResponse(BaseModel):
    query: str
    total: int
    offset: int
    limit: int
    results: List[PersonResponse]


class MergeRequest(BaseModel):
    keep_id: int
    merge_id: int


class AutoMergeRequest(BaseModel):
    min_confidence: float = Field(default=0.90, ge=0.0, le=1.0)


class PathwayRequest(BaseModel):
    profile_id: str
    target_funder_ein: str
    max_hops: int = Field(default=4, ge=1, le=10)
    include_cultivation_strategy: bool = False


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_db_path() -> str:
    from src.config.database_config import get_catalynx_db
    return get_catalynx_db()


def _conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _fetch_roles_for_person(conn: sqlite3.Connection, person_id: int) -> List[dict]:
    """Fetch all organization_roles for a given person_id."""
    rows = conn.execute(
        "SELECT * FROM organization_roles WHERE person_id = ? ORDER BY is_current DESC, filing_year DESC",
        (person_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def _fetch_roles_for_person_at_org(conn: sqlite3.Connection, person_id: int, org_ein: str) -> List[dict]:
    """Fetch organization_roles for a person at a specific organization."""
    rows = conn.execute(
        "SELECT * FROM organization_roles WHERE person_id = ? AND organization_ein = ? "
        "ORDER BY is_current DESC, filing_year DESC",
        (person_id, org_ein),
    ).fetchall()
    return [dict(r) for r in rows]


def _person_to_dict(row: sqlite3.Row, roles: List[dict]) -> dict:
    """Convert a people row + roles list into a response dict."""
    person = dict(row)
    person["organization_roles"] = roles
    return person


# ── 1. Search people by name ─────────────────────────────────────────────────

@router.get("/search", response_model=PersonSearchResponse)
async def search_people(
    q: str = Query(..., min_length=1, description="Search query for person name"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Search people by name using LIKE on normalized_name and original_name.
    Returns matching people with their organization_roles."""
    try:
        db_path = _get_db_path()
        conn = _conn(db_path)

        pattern = f"%{q}%"

        # Get total count
        total = conn.execute(
            "SELECT COUNT(*) FROM people WHERE normalized_name LIKE ? OR original_name LIKE ?",
            (pattern, pattern),
        ).fetchone()[0]

        # Fetch paginated results
        rows = conn.execute(
            "SELECT * FROM people WHERE normalized_name LIKE ? OR original_name LIKE ? "
            "ORDER BY data_quality_score DESC, source_count DESC "
            "LIMIT ? OFFSET ?",
            (pattern, pattern, limit, offset),
        ).fetchall()

        results = []
        for row in rows:
            roles = _fetch_roles_for_person(conn, row["id"])
            results.append(_person_to_dict(row, roles))

        conn.close()

        return {
            "query": q,
            "total": total,
            "offset": offset,
            "limit": limit,
            "results": results,
        }

    except Exception as e:
        logger.error(f"[people/search] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 5. People database statistics ─────────────────────────────────────────────
# NOTE: Fixed-path GET routes must be declared before /{person_id} to avoid
# being captured by the path parameter.

@router.get("/stats")
async def people_stats():
    """Return people database statistics via PeopleETL.get_stats(). Cost: $0.00."""
    try:
        from src.network.people_etl import PeopleETL

        db_path = _get_db_path()
        etl = PeopleETL(db_path)
        stats = etl.get_stats()

        return stats

    except Exception as e:
        logger.error(f"[people/stats] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 6. Find potential duplicates ──────────────────────────────────────────────

@router.get("/duplicates")
async def find_duplicates(
    min_confidence: float = Query(default=0.6, ge=0.0, le=1.0),
    limit: int = Query(default=50, ge=1, le=500),
):
    """Find potential duplicate people. Returns pairs with confidence scores."""
    try:
        from src.network.person_deduplication import PersonDeduplicationService

        db_path = _get_db_path()
        svc = PersonDeduplicationService(db_path)
        pairs = svc.find_duplicates(min_confidence=min_confidence, limit=limit)

        return {
            "total": len(pairs),
            "min_confidence": min_confidence,
            "duplicates": pairs,
        }

    except Exception as e:
        logger.error(f"[people/duplicates] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 9. Merge history ─────────────────────────────────────────────────────────

@router.get("/merge-history")
async def merge_history(
    limit: int = Query(default=50, ge=1, le=500),
):
    """Return merge history, newest first."""
    try:
        from src.network.person_deduplication import PersonDeduplicationService

        db_path = _get_db_path()
        svc = PersonDeduplicationService(db_path)
        history = svc.get_merge_history(limit=limit)

        return {
            "total": len(history),
            "history": history,
        }

    except Exception as e:
        logger.error(f"[people/merge-history] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 3. Get all people at an organization ──────────────────────────────────────

@router.get("/by-org/{org_ein}")
async def get_people_by_org(org_ein: str):
    """Get all people at an organization, with their roles there."""
    try:
        db_path = _get_db_path()
        conn = _conn(db_path)

        # Find distinct person_ids with roles at this org
        role_rows = conn.execute(
            "SELECT DISTINCT person_id FROM organization_roles WHERE organization_ein = ?",
            (org_ein,),
        ).fetchall()

        results = []
        for role_row in role_rows:
            pid = role_row["person_id"]
            person = conn.execute(
                "SELECT * FROM people WHERE id = ?", (pid,)
            ).fetchone()
            if person:
                roles = _fetch_roles_for_person_at_org(conn, pid, org_ein)
                results.append(_person_to_dict(person, roles))

        conn.close()

        return {
            "organization_ein": org_ein,
            "total": len(results),
            "people": results,
        }

    except Exception as e:
        logger.error(f"[people/by-org/{org_ein}] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 2. Get a single person by ID ─────────────────────────────────────────────
# NOTE: This catch-all path parameter route must come AFTER all fixed-path
# GET routes (/search, /stats, /duplicates, /merge-history, /by-org).

@router.get("/{person_id}")
async def get_person(person_id: int):
    """Get a single person with all their organization_roles."""
    try:
        db_path = _get_db_path()
        conn = _conn(db_path)

        row = conn.execute(
            "SELECT * FROM people WHERE id = ?", (person_id,)
        ).fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Person {person_id} not found")

        roles = _fetch_roles_for_person(conn, person_id)
        result = _person_to_dict(row, roles)
        conn.close()

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[people/{person_id}] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 4. Run ETL migration ─────────────────────────────────────────────────────

@router.post("/etl/migrate")
async def etl_migrate():
    """Run PeopleETL.migrate_from_memberships() to populate the people tables
    from network_memberships. Cost: $0.00."""
    try:
        from src.network.people_etl import PeopleETL

        db_path = _get_db_path()
        etl = PeopleETL(db_path)
        etl.ensure_tables()
        stats = etl.migrate_from_memberships()

        return {
            "success": True,
            **stats,
        }

    except Exception as e:
        logger.error(f"[people/etl/migrate] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 7. Merge two people ──────────────────────────────────────────────────────

@router.post("/merge")
async def merge_people(req: MergeRequest):
    """Merge two people. Transfers roles from merge_id to keep_id and deletes
    the merged person."""
    try:
        from src.network.person_deduplication import PersonDeduplicationService

        if req.keep_id == req.merge_id:
            raise HTTPException(status_code=400, detail="keep_id and merge_id must be different")

        db_path = _get_db_path()
        svc = PersonDeduplicationService(db_path)
        result = svc.merge_people(keep_id=req.keep_id, merge_id=req.merge_id, merged_by="api")

        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Merge failed — one or both person IDs not found (keep={req.keep_id}, merge={req.merge_id})",
            )

        return {
            "success": True,
            "keep_id": req.keep_id,
            "merge_id": req.merge_id,
            **result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[people/merge] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 8. Auto-merge high-confidence duplicates ──────────────────────────────────

@router.post("/auto-merge")
async def auto_merge(req: AutoMergeRequest):
    """Automatically merge all duplicate pairs above the confidence threshold."""
    try:
        from src.network.person_deduplication import PersonDeduplicationService

        db_path = _get_db_path()
        svc = PersonDeduplicationService(db_path)
        stats = svc.auto_merge(min_confidence=req.min_confidence)

        return {
            "success": True,
            "min_confidence": req.min_confidence,
            **stats,
        }

    except Exception as e:
        logger.error(f"[people/auto-merge] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 10. Batch preprocessing ───────────────────────────────────────────────────

class BatchPreprocessRequest(BaseModel):
    profile_id: str
    max_eins: int = Field(default=200, ge=1, le=1000)
    include_web_scraping: bool = Field(
        default=False,
        description="Enable Stage 5 AI web scraping (costs ~$0.007/org)"
    )
    web_scraping_limit: int = Field(
        default=10, ge=1, le=50,
        description="Max orgs for web scraping (controls cost)"
    )
    concurrency: int = Field(default=3, ge=1, le=5)


class BatchStageRequest(BaseModel):
    profile_id: str
    stage: str = Field(
        description="Stage to run: discover_filings, xml_officers, ingest_etl, dedup_score, web_enrichment"
    )
    max_eins: int = Field(default=200, ge=1, le=1000)
    concurrency: int = Field(default=3, ge=1, le=5)
    web_scraping_limit: int = Field(default=10, ge=1, le=50)


@router.post("/batch/preprocess")
async def batch_preprocess(req: BatchPreprocessRequest):
    """
    Run the full network batch preprocessing pipeline for a profile.

    Stages (in order):
      1. Discover filing histories via ProPublica API ($0.00)
      2. Fetch 990 XML + parse officers ($0.00)
      3. Ingest into people + organization_roles ($0.00)
      4. Deduplicate and score connections ($0.00)
      5. (Optional) AI web scraping for gaps (~$0.007/org)

    All free stages run automatically. Stage 5 only runs if
    include_web_scraping=true.
    """
    try:
        from src.network.batch_preprocessor import NetworkBatchPreprocessor
        from dataclasses import asdict

        db_path = _get_db_path()
        preprocessor = NetworkBatchPreprocessor(db_path)
        result = await preprocessor.run_pipeline(
            profile_id=req.profile_id,
            max_eins=req.max_eins,
            include_web_scraping=req.include_web_scraping,
            web_scraping_limit=req.web_scraping_limit,
            concurrency=req.concurrency,
        )
        return asdict(result)

    except Exception as e:
        logger.error(f"[people/batch/preprocess] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/batch/stage")
async def batch_run_stage(req: BatchStageRequest):
    """
    Run a single stage of the preprocessing pipeline.
    Useful for targeted re-processing or debugging.

    Valid stages: discover_filings, xml_officers, ingest_etl,
    dedup_score, web_enrichment
    """
    valid_stages = {
        "discover_filings", "xml_officers", "ingest_etl",
        "dedup_score", "web_enrichment",
    }
    if req.stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage '{req.stage}'. Valid: {sorted(valid_stages)}"
        )

    try:
        from src.network.batch_preprocessor import NetworkBatchPreprocessor
        from dataclasses import asdict

        db_path = _get_db_path()
        preprocessor = NetworkBatchPreprocessor(db_path)
        result = await preprocessor.run_stage(
            profile_id=req.profile_id,
            stage=req.stage,
            max_eins=req.max_eins,
            concurrency=req.concurrency,
            web_scraping_limit=req.web_scraping_limit,
        )
        return asdict(result)

    except Exception as e:
        logger.error(f"[people/batch/stage] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/batch/coverage")
async def batch_coverage_report(
    profile_id: str = Query(...),
    max_eins: int = Query(default=200, ge=1, le=1000),
):
    """
    Get a coverage report showing what data exists for each funder.
    Helps decide which stages to run. Cost: $0.00.
    """
    try:
        from src.network.batch_preprocessor import NetworkBatchPreprocessor

        db_path = _get_db_path()
        preprocessor = NetworkBatchPreprocessor(db_path)
        return preprocessor.get_coverage_report(profile_id, max_eins)

    except Exception as e:
        logger.error(f"[people/batch/coverage] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 11. Find connection pathways ──────────────────────────────────────────────

@router.post("/pathways")
async def find_pathways(req: PathwayRequest):
    """Find connection pathways between a profile and a target funder.
    Uses BFS on network_memberships via PathFinder. Cost: $0.00."""
    try:
        from src.network.path_finder import PathFinder

        db_path = _get_db_path()
        finder = PathFinder(db_path)
        paths = finder.find_paths(
            profile_id=req.profile_id,
            funder_ein=req.target_funder_ein,
            max_degree=req.max_hops,
        )

        # Compute network_proximity_score from path degrees
        if paths:
            network_proximity_score = min(1.0, sum(1.0 / p.degree for p in paths))
        else:
            network_proximity_score = 0.0

        pathway_results = []
        for p in paths:
            pathway_results.append({
                "degree": p.degree,
                "path_nodes": p.path_nodes,
                "connection_basis": p.connection_basis,
                "strength": p.strength,
            })

        result = {
            "profile_id": req.profile_id,
            "target_funder_ein": req.target_funder_ein,
            "pathways_found": len(pathway_results),
            "network_proximity_score": round(network_proximity_score, 3),
            "pathways": pathway_results,
        }

        # Optional cultivation strategy placeholder
        if req.include_cultivation_strategy and paths:
            best_degree = min(p.degree for p in paths)
            if best_degree == 1:
                strategy = "Direct connection exists. Leverage shared board membership for a warm introduction."
            elif best_degree == 2:
                strategy = "Second-degree connection. Request introduction through mutual contact."
            elif best_degree == 3:
                strategy = "Third-degree connection. Build relationship through intermediary network events."
            else:
                strategy = "Distant connection. Consider cultivating through industry conferences or shared interests."
            result["cultivation_strategy"] = strategy

        return result

    except Exception as e:
        logger.error(f"[people/pathways] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
