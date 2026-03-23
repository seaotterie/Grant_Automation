"""
Grant Wins Router — CRUD, CSV import, contact linking, and proven pathway scoring
for historical grant wins.
"""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/grant-wins", tags=["grant-wins"])


def _get_db_path() -> str:
    from src.config.database_config import get_catalynx_db
    return get_catalynx_db()


# ── Request / Response models ─────────────────────────────────────────────────

class GrantWinCreateRequest(BaseModel):
    profile_id: str
    funder_name: str
    amount: Optional[float] = None
    award_date: Optional[str] = None
    funder_ein: Optional[str] = None
    program_name: Optional[str] = None
    grant_purpose: Optional[str] = None
    grant_type: Optional[str] = None
    contact_names: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class GrantWinBulkRequest(BaseModel):
    """Add multiple wins at once (for UI form with multiple entries)."""
    profile_id: str
    wins: List[GrantWinCreateRequest]


class ColumnMappingOverride(BaseModel):
    """Optional column mapping for CSV import."""
    funder_name: Optional[str] = None
    amount: Optional[str] = None
    award_date: Optional[str] = None
    funder_ein: Optional[str] = None
    program_name: Optional[str] = None
    grant_purpose: Optional[str] = None
    grant_type: Optional[str] = None
    contact_names: Optional[str] = None
    notes: Optional[str] = None


# ── 1. Add a single grant win ────────────────────────────────────────────────

@router.post("")
async def add_grant_win(req: GrantWinCreateRequest):
    """Add a single historical grant win. Cost: $0.00."""
    try:
        from src.network.grant_wins import GrantWinService, GrantWinRecord

        svc = GrantWinService(_get_db_path())
        record = GrantWinRecord(
            funder_name=req.funder_name,
            amount=req.amount,
            award_date=req.award_date,
            funder_ein=req.funder_ein,
            program_name=req.program_name,
            grant_purpose=req.grant_purpose,
            grant_type=req.grant_type,
            contact_names=req.contact_names,
            notes=req.notes,
            source="manual",
        )
        result = svc.add_win(req.profile_id, record)
        return result
    except Exception as e:
        logger.error(f"[grant-wins/add] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 2. Add multiple wins at once ─────────────────────────────────────────────

@router.post("/bulk")
async def add_grant_wins_bulk(req: GrantWinBulkRequest):
    """Add multiple grant wins in one request. Cost: $0.00."""
    try:
        from src.network.grant_wins import GrantWinService, GrantWinRecord

        svc = GrantWinService(_get_db_path())
        results = {"created": 0, "updated": 0, "contacts_linked": 0, "errors": []}

        for i, win in enumerate(req.wins):
            try:
                record = GrantWinRecord(
                    funder_name=win.funder_name,
                    amount=win.amount,
                    award_date=win.award_date,
                    funder_ein=win.funder_ein,
                    program_name=win.program_name,
                    grant_purpose=win.grant_purpose,
                    grant_type=win.grant_type,
                    contact_names=win.contact_names,
                    notes=win.notes,
                    source="manual",
                )
                res = svc.add_win(req.profile_id, record)
                if res["created"]:
                    results["created"] += 1
                else:
                    results["updated"] += 1
                results["contacts_linked"] += res["contacts_linked"]
            except Exception as e:
                results["errors"].append(f"Win {i + 1}: {e}")

        return results
    except Exception as e:
        logger.error(f"[grant-wins/bulk] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 3. List all grant wins for a profile ─────────────────────────────────────

@router.get("")
async def list_grant_wins(profile_id: str = Query(...)):
    """Get all grant wins for a profile with linked contacts. Cost: $0.00."""
    try:
        from src.network.grant_wins import GrantWinService
        svc = GrantWinService(_get_db_path())
        return svc.get_wins(profile_id)
    except Exception as e:
        logger.error(f"[grant-wins/list] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 4. Delete a grant win ────────────────────────────────────────────────────

@router.delete("/{win_id}")
async def delete_grant_win(win_id: int):
    """Delete a grant win and its contact links. Cost: $0.00."""
    try:
        from src.network.grant_wins import GrantWinService
        svc = GrantWinService(_get_db_path())
        deleted = svc.delete_win(win_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Grant win not found")
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[grant-wins/delete] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 5. CSV import — preview mapping ──────────────────────────────────────────

@router.post("/import/preview")
async def preview_csv_import(file: UploadFile = File(...)):
    """
    Upload a CSV file and preview how columns will be mapped.
    Returns auto-detected mapping + sample rows so the user can
    confirm or override before committing. Cost: $0.00.
    """
    try:
        from src.network.grant_wins import GrantWinService

        content = await file.read()
        text = content.decode("utf-8-sig")  # Handle BOM from Excel exports

        svc = GrantWinService(_get_db_path())
        return svc.preview_csv_mapping(text)
    except Exception as e:
        logger.error(f"[grant-wins/import/preview] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 6. CSV import — commit ───────────────────────────────────────────────────

@router.post("/import")
async def import_csv(
    file: UploadFile = File(...),
    profile_id: str = Form(...),
    column_mapping: Optional[str] = Form(default=None),
):
    """
    Import grant wins from a CSV file.

    Accepts:
      - file: CSV file upload
      - profile_id: Profile to attach wins to
      - column_mapping: Optional JSON string of {our_field: csv_column} overrides

    Auto-detects columns if no mapping provided. Handles:
      - Dollar signs and commas in amounts ($1,234.56)
      - Various date formats (YYYY-MM-DD, MM/DD/YYYY, just year)
      - Semicolon or comma-separated contact names
      - Excel-exported CSVs with BOM

    Cost: $0.00.
    """
    try:
        from src.network.grant_wins import GrantWinService
        import json

        content = await file.read()
        text = content.decode("utf-8-sig")

        mapping = None
        if column_mapping:
            mapping = json.loads(column_mapping)

        svc = GrantWinService(_get_db_path())
        result = svc.import_from_csv(profile_id, text, column_mapping=mapping)

        return {
            "total_rows": result.total_rows,
            "wins_created": result.wins_created,
            "wins_updated": result.wins_updated,
            "contacts_linked": result.contacts_linked,
            "rows_skipped": result.rows_skipped,
            "errors": result.errors,
            "column_mapping_used": result.column_mapping_used,
        }
    except Exception as e:
        logger.error(f"[grant-wins/import] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 7. Ingest from existing opportunities ────────────────────────────────────

@router.post("/ingest-opportunities")
async def ingest_from_opportunities(profile_id: str = Query(...)):
    """
    Scan opportunities tagged/rated as 'won' and create grant_win records.
    Detects wins via user_rating=5 or notes/tags containing
    'won'/'awarded'/'funded'. Cost: $0.00.
    """
    try:
        from src.network.grant_wins import GrantWinService
        svc = GrantWinService(_get_db_path())
        return svc.ingest_from_opportunities(profile_id)
    except Exception as e:
        logger.error(f"[grant-wins/ingest-opportunities] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 8. Auto-link contacts from people database ──────────────────────────────

@router.post("/auto-link")
async def auto_link_contacts(profile_id: str = Query(...)):
    """
    For each grant win with a funder EIN, find people from the people
    database who served on the funder's board around the award date.
    Links them as proven pathway contacts. Cost: $0.00.
    """
    try:
        from src.network.grant_wins import GrantWinService
        svc = GrantWinService(_get_db_path())
        return svc.auto_link_contacts(profile_id)
    except Exception as e:
        logger.error(f"[grant-wins/auto-link] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 9. Proven pathway scoring ────────────────────────────────────────────────

@router.get("/proven-pathways")
async def get_proven_pathways(profile_id: str = Query(...)):
    """
    Score all contacts linked to historical wins. Returns ranked list
    of high-probability contacts with cultivation recommendations.

    Scoring: 40% win count + 30% recency + 15% amount + 15% still active.
    Cost: $0.00.
    """
    try:
        from src.network.grant_wins import GrantWinService
        svc = GrantWinService(_get_db_path())
        return svc.compute_proven_pathways(profile_id)
    except Exception as e:
        logger.error(f"[grant-wins/proven-pathways] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── 10. Summary stats ────────────────────────────────────────────────────────

@router.get("/summary")
async def get_grant_win_summary(profile_id: str = Query(...)):
    """Summary statistics for a profile's grant win history. Cost: $0.00."""
    try:
        from src.network.grant_wins import GrantWinService
        svc = GrantWinService(_get_db_path())
        return svc.get_summary(profile_id)
    except Exception as e:
        logger.error(f"[grant-wins/summary] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
