"""
990 Filings API Endpoints

Extracted from opportunities.py as part of the Phase C router refactor.
Owns the IRS 990 filing lifecycle: filing-history lookup, per-EIN cache,
and PDF narrative extraction via the foundation preprocessing tool.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from src.config.database_config import get_catalynx_db, get_nonprofit_intelligence_db
from src.database.database_manager import DatabaseManager
from src.web.routers.opportunities_common import (
    Analyze990PDFRequest,
    BatchAnalyze990PDFsRequest,
    FILING_HISTORY_TTL_DAYS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/opportunities", tags=["opportunities-990"])

database_manager = DatabaseManager(get_catalynx_db())


def _lookup_local_financials(ein: str) -> List[Dict[str, Any]]:
    """
    Query form990_financials in nonprofit_intelligence.db for up to 5 most recent
    years. Returns a list in the same shape as filing_history entries so the
    rest of the pipeline is unchanged. Returns [] if table missing or no rows.
    """
    try:
        intel_db = Path(get_nonprofit_intelligence_db())
        if not intel_db.exists():
            return []
        conn = sqlite3.connect(str(intel_db), timeout=5)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT tax_year, form_type, total_revenue, total_expenses, total_assets
               FROM form990_financials WHERE ein = ?
               ORDER BY tax_year DESC LIMIT 5""",
            (ein,),
        ).fetchall()
        conn.close()
        return [
            {
                "tax_year":  r["tax_year"],
                "form_type": r["form_type"],
                "revenue":   r["total_revenue"],
                "expenses":  r["total_expenses"],
                "assets":    r["total_assets"],
                "pdf_url":   None,       # not available from bulk XML
                "source":    "bulk_xml",
            }
            for r in rows
        ]
    except Exception:
        return []


async def fetch_and_cache_filing_history(ein: str, org_name: str) -> List[Dict[str, Any]]:
    """
    Fetch filing history for an EIN. Fast-path: checks local form990_financials
    table first (populated by IRS bulk XML loader). Falls back to ProPublica API
    + PDF scraping when no local data exists.
    Returns the list of filing dicts (may be empty).
    """
    # Fast-path: local bulk-loaded financials (no ProPublica call needed)
    local_filings = _lookup_local_financials(ein)
    if local_filings:
        try:
            database_manager.upsert_ein_intelligence(
                ein=ein,
                org_name=org_name,
                filing_history=local_filings,
                filing_history_fetched_at=datetime.now().isoformat(),
            )
            logger.info(f"Filing history for EIN {ein} served from local bulk DB ({len(local_filings)} years)")
        except Exception as cache_err:
            logger.warning(f"Failed to cache local filing_history for EIN {ein}: {cache_err}")
        return local_filings

    filings: List[Dict[str, Any]] = []

    # 1. ProPublica API filings (structured data + pdf_url)
    try:
        from src.clients.propublica_client import ProPublicaClient
        client = ProPublicaClient()
        org_data = await client.get_organization_by_ein(ein)
        if org_data:
            for f in org_data.get("filings_with_data", [])[:10]:
                filings.append({
                    "tax_year": f.get("tax_prd_yr") or f.get("tax_year"),
                    "form_type": f.get("formtype") or f.get("form_type", "990"),
                    "pdf_url": f.get("pdf_url"),
                    "revenue": f.get("totrevenue"),
                    "expenses": f.get("totfuncexpns"),
                    "assets": f.get("totassetsend"),
                    "filing_date": f.get("updated"),
                    "source": "api",
                })
    except Exception as e:
        logger.warning(f"ProPublica API call failed for EIN {ein}: {e}")

    # 2. Scraped PDF links from ProPublica org page (catches links API misses)
    try:
        from src.utils.xml_fetcher import XMLFetcher
        fetcher = XMLFetcher()
        scraped_links = await fetcher.find_filing_pdf_links(ein)
        api_years = {f["tax_year"] for f in filings if f.get("tax_year")}
        for link in scraped_links:
            year = link.get("year")
            if year not in api_years or link.get("form_type", "").startswith("Schedule"):
                filings.append({
                    "tax_year": year,
                    "form_type": link.get("form_type", "990"),
                    "pdf_url": link.get("pdf_url"),
                    "revenue": None, "expenses": None, "assets": None,
                    "filing_date": None,
                    "link_text": link.get("link_text"),
                    "source": "scraped",
                })
    except Exception as e:
        logger.warning(f"PDF link scraping failed for EIN {ein}: {e}")

    filings.sort(key=lambda x: (x.get("tax_year") or 0), reverse=True)

    if filings:
        try:
            database_manager.upsert_ein_intelligence(
                ein=ein,
                org_name=org_name,
                filing_history=filings,
                filing_history_fetched_at=datetime.now().isoformat(),
            )
            logger.info(f"Cached filing_history for EIN {ein} ({len(filings)} filings)")
        except Exception as cache_err:
            logger.warning(f"Failed to cache filing_history for EIN {ein}: {cache_err}")

    return filings


async def analyze_990_pdf_for_ein(
    ein: str,
    pdf_url: str,
    tax_year: Optional[int],
    force_refresh: bool = False,
) -> dict:
    """
    Shared logic for 990 PDF analysis used by both single-opp and batch endpoints.

    Returns the extraction dict (same shape as stored in pdf_analyses cache).
    Raises on hard errors; returns cached result when available.
    """
    cache_key = str(tax_year) if tax_year else pdf_url[-40:]

    if not force_refresh:
        cached = database_manager.get_ein_intelligence(ein)
        if cached and isinstance(cached.get("pdf_analyses"), dict):
            cached_extraction = cached["pdf_analyses"].get(cache_key)
            if cached_extraction:
                # Skip cache if previous extraction had zero confidence (retry with improved prompt)
                if (cached_extraction.get("extraction_confidence") or 0.0) > 0.0:
                    logger.info(f"Cache hit: pdf_analyses[{cache_key}] for EIN {ein}")
                    return {"extraction": cached_extraction, "cache_hit": True}
                else:
                    logger.info(f"Skipping zero-confidence cache for EIN {ein}, re-extracting")

    from tools.foundation_preprocessing_tool.app.pdf_narrative_extractor import PDFNarrativeExtractor

    extractor = PDFNarrativeExtractor(intelligence_db_path=get_nonprofit_intelligence_db())
    result = await extractor.extract_from_pdf_url(
        ein=ein,
        pdf_url=pdf_url,
        tax_year=tax_year,
    )

    extraction = {
        "mission_statement": result.mission_statement,
        "accepts_applications": result.accepts_applications,
        "application_deadlines": result.application_deadlines,
        "application_process": result.application_process,
        "required_documents": result.required_documents,
        "stated_priorities": result.stated_priorities,
        "geographic_limitations": result.geographic_limitations,
        "population_focus": result.population_focus,
        "grant_size_range": result.grant_size_range,
        "program_descriptions": result.program_descriptions,
        "contact_information": result.contact_information,
        "officers": getattr(result, "officers", []),
        "extraction_confidence": result.extraction_confidence,
        "pdf_pages_note": result.pdf_pages_note,
    }

    # Store in EIN intelligence cache
    try:
        existing = database_manager.get_ein_intelligence(ein)
        existing_analyses = {}
        if existing and isinstance(existing.get("pdf_analyses"), dict):
            existing_analyses = existing["pdf_analyses"]
        existing_analyses[cache_key] = extraction
        database_manager.upsert_ein_intelligence(
            ein=ein,
            pdf_analyses=existing_analyses,
        )
        logger.info(f"Cached pdf_analyses[{cache_key}] for EIN {ein}")
    except Exception as cache_err:
        logger.warning(f"Failed to cache pdf_analyses for EIN {ein}: {cache_err}")

    return {"extraction": extraction, "cache_hit": False}


@router.get("/{opportunity_id}/990-filings", summary="List available 990 filings (ProPublica + scraped) for the funder")
async def get_990_filings(opportunity_id: str):
    """
    Return 990 filing history with PDF links for an opportunity.

    Merges ProPublica API filings (with pdf_url) and scraped PDF links
    from the ProPublica org page.
    """
    try:
        conn = database_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ein, organization_name FROM opportunities WHERE id = ?", (opportunity_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")

        ein, org_name = row[0], row[1]
        if not ein:
            raise HTTPException(status_code=400, detail="Opportunity has no EIN")

        # --- EIN Intelligence Cache check ---
        cached = database_manager.get_ein_intelligence(ein)
        if cached and cached.get("filing_history") and cached.get("filing_history_fetched_at"):
            try:
                fetched_dt = datetime.fromisoformat(cached["filing_history_fetched_at"])
                age_days = (datetime.now() - fetched_dt).days
                if age_days < FILING_HISTORY_TTL_DAYS:
                    logger.info(f"Cache hit: filing_history for EIN {ein} (age {age_days}d)")
                    return {
                        "success": True,
                        "opportunity_id": opportunity_id,
                        "ein": ein,
                        "organization_name": org_name,
                        "filings": cached["filing_history"],
                        "cache_hit": True,
                    }
            except Exception as cache_err:
                logger.warning(f"Cache read error for EIN {ein}: {cache_err}")

        filings = await fetch_and_cache_filing_history(ein, org_name)

        return {
            "success": True,
            "opportunity_id": opportunity_id,
            "ein": ein,
            "organization_name": org_name,
            "filings": filings,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get 990 filings for {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{opportunity_id}/990-extraction")
async def get_990_extraction(opportunity_id: str):
    """
    Return cached PDF extraction data for this opportunity's EIN.
    Returns the most recent pdf_analyses entry from ein_intelligence.
    """
    try:
        conn = database_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ein, organization_name FROM opportunities WHERE id = ?", (opportunity_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")

        ein, org_name = row[0], row[1]
        if not ein:
            raise HTTPException(status_code=400, detail="Opportunity has no EIN")

        cached = database_manager.get_ein_intelligence(ein)
        if not cached or not isinstance(cached.get("pdf_analyses"), dict) or not cached["pdf_analyses"]:
            return {"extraction": None, "tax_year": None, "cache_hit": False}

        pdf_analyses = cached["pdf_analyses"]

        # Pick the entry with the highest numeric key (most recent tax year) or last inserted
        best_key = None
        best_year = None
        for key in pdf_analyses.keys():
            try:
                year = int(key)
                if best_year is None or year > best_year:
                    best_year = year
                    best_key = key
            except (ValueError, TypeError):
                if best_key is None:
                    best_key = key

        extraction = pdf_analyses[best_key]
        return {
            "extraction": extraction,
            "tax_year": best_year,
            "cache_hit": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get 990 extraction for {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/batch-analyze-990-pdfs", summary="Batch-extract narrative data from 990 PDFs for multiple opportunities (max 50)")
async def batch_analyze_990_pdfs(body: BatchAnalyze990PDFsRequest):
    """
    Batch analyze 990 PDFs for multiple opportunities.

    For each EIN: uses most recent filing from cached filing_history.
    Cost: ~$0.01-0.03 per PDF (Claude Haiku), cached across calls.

    Returns per-EIN results with extraction data and cache/error status.
    """
    if not body.opportunity_ids:
        raise HTTPException(status_code=400, detail="opportunity_ids must not be empty")

    if len(body.opportunity_ids) > 50:
        raise HTTPException(status_code=400, detail="Batch size cannot exceed 50 opportunities")

    results: List[Dict[str, Any]] = []
    semaphore = asyncio.Semaphore(1)  # Sequential — PDFs are large; 3 concurrent exceeded 50k token/min rate limit

    async def analyze_one(opp_id: str):
        async with semaphore:
            try:
                conn = database_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ein, organization_name FROM opportunities WHERE id = ?", (opp_id,)
                )
                row = cursor.fetchone()
                conn.close()

                if not row or not row[0]:
                    results.append({"opportunity_id": opp_id, "status": "skipped", "reason": "no EIN"})
                    return

                ein, org_name = row[0], row[1]

                # Get most recent filing PDF URL — fetch from ProPublica if not cached
                intel = database_manager.get_ein_intelligence(ein)
                filing_history = intel.get("filing_history") if intel else None

                if not filing_history:
                    logger.info(f"Fetching filing history for EIN {ein} ({org_name})")
                    filing_history = await fetch_and_cache_filing_history(ein, org_name)

                pdf_url = None
                tax_year = None
                if isinstance(filing_history, list):
                    # Sorted descending by tax_year; pick first with a pdf_url
                    for filing in filing_history:
                        if filing.get("pdf_url"):
                            pdf_url = filing["pdf_url"]
                            tax_year = filing.get("tax_year")
                            break

                if not pdf_url:
                    results.append({
                        "opportunity_id": opp_id,
                        "ein": ein,
                        "organization_name": org_name,
                        "status": "skipped",
                        "reason": "no pdf_url found in ProPublica filing history",
                    })
                    return

                result = await analyze_990_pdf_for_ein(
                    ein=ein,
                    pdf_url=pdf_url,
                    tax_year=tax_year,
                    force_refresh=body.force_refresh,
                )

                # Write pdf_analyzed flag back to analysis_discovery
                try:
                    conn2 = database_manager.get_connection()
                    cur2 = conn2.cursor()
                    cur2.execute("SELECT analysis_discovery FROM opportunities WHERE id = ?", (opp_id,))
                    ad_row = cur2.fetchone()
                    if ad_row and ad_row[0]:
                        ad = json.loads(ad_row[0]) if isinstance(ad_row[0], str) else ad_row[0]
                        ad["pdf_analyzed"] = True
                        cur2.execute(
                            "UPDATE opportunities SET analysis_discovery = ?, updated_at = ? WHERE id = ?",
                            (json.dumps(ad), datetime.now().isoformat(), opp_id),
                        )
                        conn2.commit()
                except Exception as db_err:
                    logger.warning(f"Failed to write pdf_analyzed flag for {opp_id}: {db_err}")

                results.append({
                    "opportunity_id": opp_id,
                    "ein": ein,
                    "organization_name": org_name,
                    "pdf_url": pdf_url,
                    "tax_year": tax_year,
                    "status": "ok",
                    "cache_hit": result.get("cache_hit", False),
                    "extraction": result.get("extraction", {}),
                })

                # Pace requests to stay within 50k tokens/min rate limit
                if not result.get("cache_hit"):
                    await asyncio.sleep(3)

            except Exception as e:
                logger.warning(f"Batch 990 analysis failed for {opp_id}: {e}")
                results.append({"opportunity_id": opp_id, "status": "error", "error": str(e)})

    await asyncio.gather(*[analyze_one(opp_id) for opp_id in body.opportunity_ids])

    successful = [r for r in results if r.get("status") == "ok"]
    cached = [r for r in successful if r.get("cache_hit")]
    cost_estimate = (len(successful) - len(cached)) * 0.02  # ~$0.02 per Haiku PDF call

    return {
        "success": True,
        "total": len(body.opportunity_ids),
        "analyzed": len(successful),
        "cached": len(cached),
        "skipped": len([r for r in results if r.get("status") == "skipped"]),
        "errors": len([r for r in results if r.get("status") == "error"]),
        "estimated_cost_usd": cost_estimate,
        "results": results,
    }


@router.post("/{opportunity_id}/analyze-990-pdf", summary="Extract mission/grant data from a single 990 PDF URL")
async def analyze_990_pdf(opportunity_id: str, body: Analyze990PDFRequest):
    """
    Send a 990 PDF URL to Claude for grant-intelligence extraction.
    Cost: ~$0.01-0.03 per PDF (Claude Haiku), cached per EIN.
    """
    try:
        conn = database_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ein FROM opportunities WHERE id = ?", (opportunity_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")
        ein = row[0] or ""

        if not body.pdf_url or not body.pdf_url.startswith("http"):
            raise HTTPException(status_code=400, detail="Valid pdf_url required")

        logger.info(f"Analyzing 990 PDF for {opportunity_id} (EIN: {ein}): {body.pdf_url}")

        result = await analyze_990_pdf_for_ein(
            ein=ein,
            pdf_url=body.pdf_url,
            tax_year=body.tax_year,
        )

        # Persist pdf_analyzed flag to analysis_discovery so icon/section survive reload
        try:
            conn2 = database_manager.get_connection()
            cur2 = conn2.cursor()
            cur2.execute("SELECT analysis_discovery FROM opportunities WHERE id = ?", (opportunity_id,))
            ad_row = cur2.fetchone()
            if ad_row and ad_row[0]:
                ad = json.loads(ad_row[0]) if isinstance(ad_row[0], str) else ad_row[0]
                ad["pdf_analyzed"] = True
                cur2.execute(
                    "UPDATE opportunities SET analysis_discovery = ?, updated_at = ? WHERE id = ?",
                    (json.dumps(ad), datetime.now().isoformat(), opportunity_id),
                )
                conn2.commit()
            conn2.close()
        except Exception as db_err:
            logger.warning(f"Failed to write pdf_analyzed flag for {opportunity_id}: {db_err}")

        return {
            "success": True,
            "opportunity_id": opportunity_id,
            "ein": ein,
            "pdf_url": body.pdf_url,
            "tax_year": body.tax_year,
            "extraction": result["extraction"],
            "cache_hit": result.get("cache_hit", False),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze 990 PDF for {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
