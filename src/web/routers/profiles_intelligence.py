"""
Profiles Intelligence Pipeline Router

Two endpoints:
  POST /{profile_id}/run-pipeline            → start 5-step background pipeline, return job_id
  GET  /{profile_id}/pipeline-status/{job_id} → poll current job state

Five pipeline steps:
  1. web           - Tool 25 Haiku web research
  2. 990_history   - ProPublica filing history
  3. 990_pdf       - PDFNarrativeExtractor on most-recent filing
  4. fast_screen   - Tool 1 fast mode
  5. thorough_screen - Tool 1 thorough mode

Shared cache: ein_intelligence table (web_data, filing_history, pdf_analyses)
  → SCREENING tab picks these up automatically for the same EIN.

Profile storage: processing_history["pipeline_results"] (scores summary)
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict, Optional, Any, List
import asyncio
import json
import logging
import uuid
from datetime import datetime

from src.database.database_manager import DatabaseManager
from src.config.database_config import get_catalynx_db
from src.core.anthropic_service import get_anthropic_service, PipelineStage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/profiles", tags=["profiles-intelligence"])

database_manager = DatabaseManager(get_catalynx_db())

# In-memory job store (single-user app — no persistence needed)
_pipeline_jobs: Dict[str, Dict] = {}

_STEPS = ["web", "990_history", "990_pdf", "fast_screen", "thorough_screen"]
_WEB_DATA_TTL_DAYS = 30


def _update_job(job_id: str, **kwargs):
    if job_id in _pipeline_jobs:
        _pipeline_jobs[job_id].update(kwargs)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/{profile_id}/run-pipeline")
async def run_intelligence_pipeline(profile_id: str, background_tasks: BackgroundTasks):
    """
    Start the 5-step intelligence pipeline for a profile's EIN.
    Returns job_id immediately; poll /pipeline-status/{job_id} for progress.
    """
    conn = database_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, ein, name, website_url FROM profiles WHERE id = ?", (profile_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

    _id, ein, org_name, website_url = row[0], row[1], row[2], row[3]

    if not ein:
        raise HTTPException(
            status_code=400,
            detail="Profile does not have an EIN. Intelligence pipeline requires an EIN.",
        )

    job_id = str(uuid.uuid4())
    _pipeline_jobs[job_id] = {
        "job_id": job_id,
        "profile_id": profile_id,
        "ein": ein,
        "status": "running",
        "step": "web",
        "step_index": 0,
        "total_steps": len(_STEPS),
        "error": None,
        "result": {},
    }

    background_tasks.add_task(
        _run_intelligence_pipeline,
        job_id, profile_id, ein, org_name or "", website_url or "",
    )

    return {"job_id": job_id, "profile_id": profile_id, "ein": ein, "status": "running"}


@router.get("/{profile_id}/pipeline-status/{job_id}")
async def get_pipeline_status(profile_id: str, job_id: str):
    """Poll pipeline job status."""
    job = _pipeline_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Pipeline job {job_id} not found")
    return job


# ---------------------------------------------------------------------------
# Background Orchestrator
# ---------------------------------------------------------------------------

async def _run_intelligence_pipeline(
    job_id: str, profile_id: str, ein: str, org_name: str, website_url: str,
):
    """Run all 5 pipeline steps sequentially, updating job state after each."""
    try:
        result: Dict[str, Any] = {}

        # ── Step 1: Web Research ─────────────────────────────────────────
        _update_job(job_id, step="web", step_index=0)
        web_quality = 0.0
        try:
            web_data = await _run_web_research(ein, org_name, website_url)
            if web_data:
                web_quality = web_data.get("data_quality_score", 0.0)
                result["web_quality"] = web_quality
                result["web_summary"] = {
                    "data_quality_score": web_quality,
                    "accepts_applications": web_data.get("accepts_applications"),
                    "grant_size_range": web_data.get("grant_size_range"),
                    "funding_priorities": web_data.get("key_facts") or [],
                    "geographic_limitations": web_data.get("geographic_limitations"),
                    "execution_time": web_data.get("execution_time"),
                    "ai_interpreted": web_data.get("ai_interpreted", True),
                }
        except Exception as e:
            logger.warning(f"[Pipeline {job_id}] Step 1 (web) failed: {e}")
            result["web_error"] = str(e)

        # ── Step 2: 990 Filing History ───────────────────────────────────
        _update_job(job_id, step="990_history", step_index=1)
        pdf_url: Optional[str] = None
        tax_year: Optional[int] = None
        try:
            from src.web.routers.opportunities import _fetch_and_cache_filing_history
            filing_history = await _fetch_and_cache_filing_history(ein, org_name)
            result["filing_count"] = len(filing_history)
            for filing in filing_history:
                if filing.get("pdf_url"):
                    pdf_url = filing["pdf_url"]
                    tax_year = filing.get("tax_year")
                    break
        except Exception as e:
            logger.warning(f"[Pipeline {job_id}] Step 2 (990_history) failed: {e}")
            result["history_error"] = str(e)

        # ── Step 3: 990 PDF Analysis ─────────────────────────────────────
        _update_job(job_id, step="990_pdf", step_index=2)
        pdf_confidence = 0.0
        if pdf_url:
            try:
                from src.web.routers.opportunities import _analyze_990_pdf_for_ein
                pdf_result = await _analyze_990_pdf_for_ein(
                    ein=ein, pdf_url=pdf_url, tax_year=tax_year
                )
                extraction = pdf_result.get("extraction", {})
                pdf_confidence = extraction.get("extraction_confidence", 0.0)
                result["pdf_confidence"] = pdf_confidence
                result["pdf_tax_year"] = tax_year
                result["pdf_summary"] = {
                    "extraction_confidence": pdf_confidence,
                    "accepts_applications": extraction.get("accepts_applications"),
                    "stated_priorities": extraction.get("stated_priorities") or [],
                    "population_focus": extraction.get("population_focus"),
                    "geographic_limitations": extraction.get("geographic_limitations"),
                    "tax_year": tax_year,
                }
            except Exception as e:
                logger.warning(f"[Pipeline {job_id}] Step 3 (990_pdf) failed: {e}")
                result["pdf_error"] = str(e)
        else:
            result["pdf_skipped"] = True
            logger.info(f"[Pipeline {job_id}] Step 3 skipped — no PDF URL found")

        # ── Sync profile people from gathered web/990 data ───────────────
        try:
            profile_people = _sync_profile_people(profile_id, ein)
            result["profile_people"] = profile_people
            result["profile_people_count"] = len(profile_people)
        except Exception as e:
            logger.warning(f"[Pipeline {job_id}] People sync failed: {e}")
            result["profile_people"] = []

        # ── Step 4a: Fast Profile Analysis ───────────────────────────────
        _update_job(job_id, step="fast_screen", step_index=3)
        fast_analysis: Optional[Dict] = None
        try:
            fast_analysis = await _run_profile_analysis(ein, profile_id, mode="fast")
            result["fast_analysis"] = fast_analysis
        except Exception as e:
            logger.warning(f"[Pipeline {job_id}] Step 4a (fast_screen) failed: {e}")
            result["fast_screen_error"] = str(e)

        # ── Step 4b: Thorough Profile Analysis ───────────────────────────
        _update_job(job_id, step="thorough_screen", step_index=4)
        thorough_analysis: Optional[Dict] = None
        try:
            thorough_analysis = await _run_profile_analysis(ein, profile_id, mode="thorough")
            result["thorough_analysis"] = thorough_analysis
        except Exception as e:
            logger.warning(f"[Pipeline {job_id}] Step 4b (thorough_screen) failed: {e}")
            result["thorough_screen_error"] = str(e)

        # ── Save to profile.processing_history ───────────────────────────
        try:
            conn = database_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT processing_history FROM profiles WHERE id = ?", (profile_id,))
            row = cursor.fetchone()
            if row:
                raw = row[0]
                ph = json.loads(raw) if isinstance(raw, str) and raw else {}
                ph["pipeline_results"] = {
                    "fast_analysis": fast_analysis,
                    "thorough_analysis": thorough_analysis,
                    "profile_people": result.get("profile_people", []),
                    "web_quality": web_quality,
                    "pdf_confidence": pdf_confidence,
                    "ran_at": datetime.now().isoformat(),
                }
                cursor.execute(
                    "UPDATE profiles SET processing_history = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (json.dumps(ph), profile_id),
                )
                conn.commit()
            conn.close()
        except Exception as db_err:
            logger.warning(f"[Pipeline {job_id}] Failed to save pipeline_results to profile: {db_err}")

        # Rough cost estimate
        result["estimated_cost_usd"] = round(
            0.01   # web (Tool 25 Haiku)
            + 0.02  # 990 PDF (PDFNarrativeExtractor Haiku)
            + 0.003 # fast profile analysis (Haiku)
            + 0.01  # thorough profile analysis (Sonnet)
        , 3)

        _update_job(job_id, step="done", step_index=len(_STEPS), status="complete", result=result)
        logger.info(f"[Pipeline {job_id}] Complete for EIN {ein}")

    except Exception as e:
        logger.error(f"[Pipeline {job_id}] Fatal error: {e}", exc_info=True)
        _update_job(job_id, status="error", error=str(e))


# ---------------------------------------------------------------------------
# Helper: Step 1 - Web Research
# ---------------------------------------------------------------------------

async def _run_web_research(ein: str, org_name: str, website_url: str) -> Optional[dict]:
    """
    Run Tool 25 Haiku web intelligence for the org.
    Returns web_data dict or None.  Cache TTL = 30 days.
    """
    # Check cache first
    cached = database_manager.get_ein_intelligence(ein)
    if cached and cached.get("web_data") and cached.get("web_data_fetched_at"):
        try:
            fetched_dt = datetime.fromisoformat(cached["web_data_fetched_at"])
            age_days = (datetime.now() - fetched_dt).days
            if age_days < _WEB_DATA_TTL_DAYS:
                logger.info(f"[WebResearch] Cache hit for EIN {ein} (age {age_days}d)")
                return cached["web_data"]
        except Exception:
            pass

    from tools.web_intelligence_tool.app.web_intelligence_tool import (
        WebIntelligenceTool, WebIntelligenceRequest, UseCase,
    )
    from tools.shared_schemas.grant_funder_intelligence import GrantFunderIntelligence as GFI

    tool = WebIntelligenceTool()
    params: Dict[str, Any] = {
        "ein": ein,
        "organization_name": org_name,
        "use_case": UseCase.PROFILE_BUILDER,
    }
    if website_url:
        params["user_provided_url"] = website_url

    result = await tool.execute(WebIntelligenceRequest(**params))

    if not result.success:
        if result.errors and "no_url_found" in result.errors:
            logger.info(f"[WebResearch] No URL found for EIN {ein}")
        return None

    intelligence = result.intelligence_data
    if not isinstance(intelligence, GFI):
        logger.warning(f"[WebResearch] Unexpected intelligence type: {type(intelligence)}")
        return None

    contact_obj = None
    if intelligence.contact_information:
        contact_obj = {"email": None, "phone": None, "address": intelligence.contact_information}

    web_data = {
        "website": intelligence.source_url,
        "website_verified": intelligence.confidence_score > 0.6,
        "mission": intelligence.mission_statement,
        "leadership": [
            {"name": m, "title": "", "email": None, "confidence": "medium"}
            for m in (intelligence.board_members or [])
        ],
        "contact": contact_obj,
        "social_media": {},
        "programs": [
            {"name": "", "description": d, "target_population": intelligence.population_focus}
            for d in (intelligence.program_descriptions or [])
        ],
        "key_facts": intelligence.funding_priorities or [],
        "data_quality_score": intelligence.confidence_score,
        "pages_scraped": result.pages_scraped,
        "execution_time": result.execution_time_seconds,
        "ai_interpreted": True,
        "accepts_applications": intelligence.accepts_applications,
        "application_deadlines": intelligence.application_deadlines,
        "application_process": intelligence.application_process,
        "required_documents": intelligence.required_documents,
        "geographic_limitations": intelligence.geographic_limitations,
        "grant_size_range": intelligence.grant_size_range,
        "grant_funder_intelligence": intelligence.to_dict(),
    }

    database_manager.upsert_ein_intelligence(
        ein=ein,
        org_name=org_name,
        web_data=web_data,
        web_data_fetched_at=datetime.now().isoformat(),
        web_data_source="tool25_haiku",
    )
    return web_data


# ---------------------------------------------------------------------------
# Helper: People Sync (profile side)
# ---------------------------------------------------------------------------

def _sync_profile_people(profile_id: str, ein: str) -> list:
    """
    Build a unified structured people list from ein_intelligence (web + 990)
    for the profile org itself.  Format: [{name, title, source, email?, compensation?}]
    — identical to GrantFunderIntelligence.people so both sides can be compared.

    Writes back to profiles.board_members if the new list is non-empty and
    richer (longer) than whatever is currently stored.

    Returns the merged people list.
    """
    intel = database_manager.get_ein_intelligence(ein) or {}
    web_data = intel.get("web_data") or {}
    pdf_analyses = intel.get("pdf_analyses") or {}

    def _name_key(raw: str) -> str:
        """Normalize a name for dedup: strip honorifics, collapse whitespace, lowercase."""
        import re
        s = raw.strip()
        s = re.sub(r'^(Dr|Mr|Mrs|Ms|Miss|Prof|Rev|Hon|Cpt|Sgt|Lt|Col|Gen)\.?\s+', '', s, flags=re.IGNORECASE)
        return ' '.join(s.lower().split())

    seen: set = set()
    people: list = []

    # ── Web source: leadership[] ─────────────────────────────────────────
    for ldr in (web_data.get("leadership") or []):
        name = (ldr.get("name") or "").strip()
        if not name:
            continue
        key = _name_key(name)
        if key in seen:
            continue
        seen.add(key)
        entry: dict = {"name": name, "source": "web"}
        title = ldr.get("title") or ldr.get("role") or ""
        if title:
            entry["title"] = title
        email = ldr.get("email") or ""
        if email:
            entry["email"] = email
        people.append(entry)

    # ── PDF source: officers[] from first extraction ─────────────────────
    first_extraction: dict = {}
    if isinstance(pdf_analyses, dict):
        for val in pdf_analyses.values():
            if isinstance(val, dict):
                # May be stored as {"extraction": {...}} or flat
                first_extraction = val.get("extraction") or val
                break

    for off in (first_extraction.get("officers") or []):
        if not isinstance(off, dict):
            continue
        name = (off.get("name") or "").strip()
        if not name:
            continue
        key = _name_key(name)
        if key in seen:
            continue
        seen.add(key)
        entry = {"name": name, "source": "990_pdf"}
        title = off.get("title") or off.get("position") or ""
        if title:
            entry["title"] = title
        comp = off.get("compensation")
        if comp is not None:
            entry["compensation"] = comp
        people.append(entry)

    if not people:
        return []

    # ── Write back to profiles.board_members if richer than existing ─────
    try:
        conn = database_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT board_members FROM profiles WHERE id = ?", (profile_id,))
        row = cursor.fetchone()
        existing: list = []
        if row and row[0]:
            try:
                existing = json.loads(row[0]) if isinstance(row[0], str) else (row[0] or [])
            except Exception:
                existing = []
        if len(people) > len(existing):
            cursor.execute(
                "UPDATE profiles SET board_members = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(people), profile_id),
            )
            conn.commit()
            logger.info(f"[SyncPeople] Updated board_members for profile {profile_id}: {len(people)} people")
        conn.close()
    except Exception as e:
        logger.warning(f"[SyncPeople] Failed to write board_members for profile {profile_id}: {e}")

    return people


# ---------------------------------------------------------------------------
# Helper: Steps 4a/4b - Screening
# ---------------------------------------------------------------------------

async def _run_screening(ein: str, profile_id: str, mode: str) -> Optional[dict]:
    """
    Run Tool 1 treating the profile org as the entity being analyzed.
    The ScreeningOpportunity is built from profile fields; injected with
    any funder intelligence already gathered in ein_intelligence.
    """
    from tools.opportunity_screening_tool.app.screening_tool import OpportunityScreeningTool
    from tools.opportunity_screening_tool.app.screening_models import (
        ScreeningInput, ScreeningMode,
        Opportunity as ScreeningOpportunity,
        OrganizationProfile as ScreeningOrgProfile,
    )
    from tools.shared_schemas.grant_funder_intelligence import build_from_ein_intelligence

    conn = database_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None

    profile_dict = dict(row)

    def _parse_json_list(val) -> list:
        try:
            return json.loads(val) if val else []
        except Exception:
            return []

    ntee_codes = _parse_json_list(profile_dict.get("ntee_codes"))
    service_areas = _parse_json_list(profile_dict.get("service_areas"))
    focus_areas = _parse_json_list(profile_dict.get("focus_areas"))
    program_areas = _parse_json_list(profile_dict.get("program_areas"))

    org_profile = ScreeningOrgProfile(
        ein=profile_dict.get("ein") or "",
        name=profile_dict.get("name") or "Unknown",
        mission=profile_dict.get("mission_statement") or "",
        ntee_codes=ntee_codes,
        geographic_focus=service_areas or [profile_dict.get("location") or ""],
        program_areas=program_areas or focus_areas,
        annual_revenue=profile_dict.get("annual_revenue"),
    )

    org_name = profile_dict.get("name") or "Unknown"
    mission = profile_dict.get("mission_statement") or ""
    location = profile_dict.get("location") or ""
    revenue = profile_dict.get("annual_revenue") or 0

    screening_opp = ScreeningOpportunity(
        opportunity_id=f"profile_{profile_id}",
        title=org_name,
        funder=org_name,
        funder_type="nonprofit",
        description=(
            f"Organization: {org_name}. "
            f"Mission: {mission[:200]}. "
            f"Location: {location}. "
            f"Annual Revenue: ${revenue:,.0f}."
        ),
        geographic_restrictions=[],
    )

    # Inject funder intelligence gathered in Steps 1-3
    intel = database_manager.get_ein_intelligence(ein)
    if intel:
        funder_intel = build_from_ein_intelligence(
            web_data=intel.get("web_data"),
            pdf_analyses=intel.get("pdf_analyses"),
            ein=ein,
        )
        if funder_intel:
            screening_opp.funder_intelligence = funder_intel

    mode_enum = ScreeningMode.FAST if mode == "fast" else ScreeningMode.THOROUGH
    tool = OpportunityScreeningTool()
    screening_input = ScreeningInput(
        opportunities=[screening_opp],
        organization_profile=org_profile,
        screening_mode=mode_enum,
        minimum_threshold=0.0,
        max_recommendations=1,
    )

    result = await tool.execute(screening_input=screening_input)
    if result.is_success and result.data and result.data.opportunity_scores:
        s = result.data.opportunity_scores[0]
        return {
            "overall_score": s.overall_score,
            "strategic_fit_score": s.strategic_fit_score,
            "eligibility_score": s.eligibility_score,
            "timing_score": s.timing_score,
            "confidence_level": s.confidence_level,
            "one_sentence_summary": s.one_sentence_summary,
            "key_strengths": s.key_strengths,
            "key_concerns": s.key_concerns,
            "mode": mode,
            "scored_at": datetime.now().isoformat(),
        }
    return None


# ---------------------------------------------------------------------------
# Helper: Steps 4a/4b - Profile Intelligence Analysis
# ---------------------------------------------------------------------------

async def _run_profile_analysis(ein: str, profile_id: str, mode: str) -> Optional[dict]:
    """
    Run a purpose-built profile intelligence analysis for a grant-seeking org.
    POV: Grantee — "What does this org do, who do they serve, what keywords help find grants?"
    Fast mode → Haiku; Thorough mode → Sonnet.
    """
    try:
        # ── Fetch profile row ────────────────────────────────────────────
        conn = database_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None

        profile_dict = dict(row)

        def _parse_json_field(val) -> list:
            try:
                return json.loads(val) if val else []
            except Exception:
                return []

        focus_areas = _parse_json_field(profile_dict.get("focus_areas"))
        program_areas = _parse_json_field(profile_dict.get("program_areas"))
        ntee_codes = _parse_json_field(profile_dict.get("ntee_codes"))
        service_areas = _parse_json_field(profile_dict.get("service_areas"))
        target_populations = _parse_json_field(profile_dict.get("target_populations"))
        board_members = _parse_json_field(profile_dict.get("board_members"))

        revenue = profile_dict.get("annual_revenue") or 0
        if revenue <= 0:
            capacity_tier = "unknown"
        elif revenue < 500_000:
            capacity_tier = "small"
        elif revenue < 5_000_000:
            capacity_tier = "medium"
        else:
            capacity_tier = "large"

        # ── Fetch ein_intelligence ───────────────────────────────────────
        intel = database_manager.get_ein_intelligence(ein) or {}
        web_data = intel.get("web_data") or {}
        pdf_analyses = intel.get("pdf_analyses") or {}

        # Pull first PDF analysis entry
        first_pdf: dict = {}
        if isinstance(pdf_analyses, dict) and pdf_analyses:
            first_pdf = next(iter(pdf_analyses.values()), {})
            if isinstance(first_pdf, dict) and "extraction" in first_pdf:
                first_pdf = first_pdf["extraction"]

        # ── Build context block ──────────────────────────────────────────
        context_parts = ["## Organization Data"]
        context_parts.append(f"Name: {profile_dict.get('name') or 'Unknown'}")
        context_parts.append(f"EIN: {ein}")
        context_parts.append(f"Location: {profile_dict.get('location') or 'Unknown'}")
        if revenue > 0:
            context_parts.append(f"Annual Revenue: ${revenue:,.0f} (capacity: {capacity_tier})")
        else:
            context_parts.append(f"Annual Revenue: Unknown (capacity: {capacity_tier})")
        mission = profile_dict.get("mission_statement") or ""
        if mission:
            context_parts.append(f"Mission: {mission[:300]}")
        if ntee_codes:
            context_parts.append(f"NTEE Codes: {', '.join(ntee_codes)}")
        if focus_areas:
            context_parts.append(f"Focus Areas: {', '.join(focus_areas)}")
        if program_areas:
            context_parts.append(f"Program Areas: {', '.join(program_areas)}")
        if target_populations:
            context_parts.append(f"Target Populations: {', '.join(target_populations)}")
        if service_areas:
            context_parts.append(f"Service Areas: {', '.join(service_areas)}")
        geo_scope = profile_dict.get("geographic_scope") or ""
        if geo_scope:
            context_parts.append(f"Geographic Scope: {geo_scope}")
        if board_members:
            bm_names = [
                b.get("name") if isinstance(b, dict) else str(b)
                for b in board_members[:5]
            ]
            context_parts.append(f"Board Members: {', '.join(filter(None, bm_names))}")

        if web_data:
            context_parts.append("\n## Website Intelligence (confidence: "
                                  f"{round((web_data.get('data_quality_score') or 0) * 100)}%)")
            web_mission = web_data.get("mission") or ""
            if web_mission:
                context_parts.append(f"Mission (from web): {web_mission[:200]}")
            programs = web_data.get("programs") or []
            if programs:
                prog_descs = [
                    p.get("description") if isinstance(p, dict) else str(p)
                    for p in programs[:3]
                ]
                context_parts.append(f"Programs: {'; '.join(filter(None, prog_descs))}")
            key_facts = web_data.get("key_facts") or []
            if key_facts:
                context_parts.append(f"Key facts: {'; '.join(str(f) for f in key_facts[:4])}")

        if first_pdf:
            tax_year = first_pdf.get("tax_year") or profile_dict.get("tax_year") or "unknown"
            context_parts.append(f"\n## 990 Tax Filing Data (tax year: {tax_year})")
            pdf_mission = first_pdf.get("mission_statement") or ""
            if pdf_mission:
                context_parts.append(f"Mission: {pdf_mission[:200]}")
            stated_priorities = first_pdf.get("stated_priorities") or []
            if stated_priorities:
                context_parts.append(f"Stated priorities: {'; '.join(str(p) for p in stated_priorities[:3])}")
            pop_focus = first_pdf.get("population_focus") or ""
            if pop_focus:
                context_parts.append(f"Population focus: {pop_focus}")
            program_descs = first_pdf.get("program_descriptions") or []
            if program_descs:
                context_parts.append(f"Program descriptions: {'; '.join(str(d) for d in program_descs[:2])}")

        context = "\n".join(context_parts)

        # ── Prompts ──────────────────────────────────────────────────────
        system_prompt = (
            "You are a grant research analyst building a structured profile of a nonprofit "
            "grant-seeking organization. Extract factual information about what they do, "
            "who they serve, and where they operate. "
            "Do NOT evaluate whether this org is a good funding opportunity — "
            "this org is a GRANT SEEKER, not a grantor. "
            "Respond with valid JSON only."
        )

        if mode == "fast":
            user_prompt = (
                f"{context}\n\n"
                "Return a JSON object with these exact keys:\n"
                '{\n'
                '  "one_sentence_summary": "string",\n'
                '  "mission_summary": "string or null",\n'
                '  "programs": ["string — max 5"],\n'
                '  "target_populations": ["string"],\n'
                '  "geographic_scope": "string",\n'
                '  "capacity_tier": "small|medium|large|unknown",\n'
                '  "grant_keywords": ["string — 5-8 keywords for finding matching grants"],\n'
                '  "confidence_level": "high|medium|low",\n'
                '  "data_sources_used": ["string"]\n'
                '}'
            )
            stage = PipelineStage.FAST_SCREENING
            max_tokens = 800
        else:
            user_prompt = (
                f"{context}\n\n"
                "Be comprehensive and actionable. "
                "Return a JSON object with these exact keys:\n"
                '{\n'
                '  "one_sentence_summary": "string",\n'
                '  "mission_summary": "string or null",\n'
                '  "programs": ["string — max 5"],\n'
                '  "target_populations": ["string"],\n'
                '  "geographic_scope": "string",\n'
                '  "capacity_tier": "small|medium|large|unknown",\n'
                '  "grant_keywords": ["string — 5-8 keywords for finding matching grants"],\n'
                '  "confidence_level": "high|medium|low",\n'
                '  "data_sources_used": ["string"],\n'
                '  "key_strengths": ["string — 3-5 specific strengths as a grant applicant"],\n'
                '  "leadership": [{"name": "string", "title": "string"}],\n'
                '  "previous_grants_hint": "string or null",\n'
                '  "search_tips": ["string — 3-5 specific grant search recommendations"]\n'
                '}'
            )
            stage = PipelineStage.THOROUGH_SCREENING
            max_tokens = 1400

        # ── Call Claude ──────────────────────────────────────────────────
        service = get_anthropic_service()
        result = await service.create_json_completion(
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
            stage=stage,
            max_tokens=max_tokens,
            temperature=0.0,
        )
        result["analyzed_at"] = datetime.now().isoformat()
        result["mode"] = mode
        return result

    except Exception as e:
        logger.warning(f"[ProfileAnalysis] {mode} analysis for EIN {ein} failed: {e}")
        return {
            "one_sentence_summary": "Analysis unavailable.",
            "confidence_level": "low",
            "mode": mode,
            "analyzed_at": datetime.now().isoformat(),
            "error": str(e),
        }
