"""
GrantFunderIntelligence — shared schema for web (W) and 990-PDF (9) intelligence.

Both sources produce this same structured contract so downstream tools
(Opportunity Screening Tool prompts, batch endpoints) can consume them identically.

Sources are complementary, not duplicate:
  W (website) → board_members, application_process, required_documents
  9 (990-PF)  → grant_size_range, population_focus, financial acceptance data
  Both        → accepts_applications, deadlines, priorities, geographic limits

Adapters:
  from_narrative_extraction(result)  → from NarrativeExtractionResult (990 PDF)
  from_web_data(web_data, ein)       → from ein_intelligence.web_data dict
  merge(web, pdf)                    → combine both sources
  to_screening_context()             → formatted text block for Claude prompts
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class IntelligenceSource(str, Enum):
    WEB = "web"
    PDF_990 = "pdf_990"
    BOTH = "both"


@dataclass
class GrantFunderIntelligence:
    ein: str
    organization_name: str
    source: IntelligenceSource

    # Grant-relevant fields (primary purpose)
    accepts_applications: str = "unknown"   # yes / no / invitation_only / unknown
    application_deadlines: Optional[str] = None
    application_process: Optional[str] = None
    required_documents: List[str] = field(default_factory=list)
    funding_priorities: List[str] = field(default_factory=list)
    geographic_limitations: Optional[str] = None
    grant_size_range: Optional[str] = None
    population_focus: Optional[str] = None

    # Org intelligence fields
    mission_statement: Optional[str] = None
    program_descriptions: List[str] = field(default_factory=list)
    contact_information: Optional[str] = None
    past_grantees: List[str] = field(default_factory=list)

    # Leadership — names only (kept for backward compat with prompt injection)
    board_members: List[str] = field(default_factory=list)

    # Leadership — structured (name + title + source + optional email/compensation)
    # [{name: str, title: str, source: "web"|"990_pdf", email?: str, compensation?: int}]
    people: List[dict] = field(default_factory=list)

    # Quality
    confidence_score: float = 0.0
    source_url: Optional[str] = None       # website URL or 990 PDF URL
    source_tax_year: Optional[int] = None  # for PDF source

    # -----------------------------------------------------------------------
    # Output
    # -----------------------------------------------------------------------

    def to_screening_context(self, mode: str = "fast") -> str:
        """
        Return a formatted text block for injection into screening prompts.
        mode="fast"    → compact summary (key fields only)
        mode="thorough" → full block including programs, docs, board, contact
        """
        lines = ["FUNDER INTELLIGENCE (from website/990 filing):"]
        lines.append(f"  Source: {self.source.value} | Confidence: {self.confidence_score:.0%}")

        if self.accepts_applications != "unknown":
            lines.append(f"  Accepts Applications: {self.accepts_applications}")
        if self.application_deadlines:
            lines.append(f"  Deadlines: {self.application_deadlines}")
        if self.funding_priorities:
            lines.append(f"  Funding Priorities: {', '.join(self.funding_priorities[:5])}")
        if self.geographic_limitations:
            lines.append(f"  Geographic Limits: {self.geographic_limitations}")
        if self.grant_size_range:
            lines.append(f"  Typical Grant Size: {self.grant_size_range}")
        if self.population_focus:
            lines.append(f"  Population Focus: {self.population_focus}")

        if mode == "thorough":
            if self.application_process:
                lines.append(f"  Application Process: {self.application_process}")
            if self.required_documents:
                lines.append(f"  Required Documents: {', '.join(self.required_documents)}")
            if self.mission_statement:
                lines.append(f"  Mission: {self.mission_statement[:200]}")
            if self.program_descriptions:
                lines.append(f"  Programs: {'; '.join(self.program_descriptions[:3])}")
            if self.people:
                formatted = ", ".join(
                    f"{p['name']} ({p['title']})" if p.get("title") else p["name"]
                    for p in self.people[:8]
                )
                lines.append(f"  Board/Officers: {formatted}")
            elif self.board_members:
                lines.append(f"  Board Members: {', '.join(self.board_members[:5])}")
            if self.contact_information:
                lines.append(f"  Contact: {self.contact_information}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize to dict for storage in ein_intelligence."""
        return {
            "ein": self.ein,
            "organization_name": self.organization_name,
            "source": self.source.value,
            "accepts_applications": self.accepts_applications,
            "application_deadlines": self.application_deadlines,
            "application_process": self.application_process,
            "required_documents": self.required_documents,
            "funding_priorities": self.funding_priorities,
            "geographic_limitations": self.geographic_limitations,
            "grant_size_range": self.grant_size_range,
            "population_focus": self.population_focus,
            "mission_statement": self.mission_statement,
            "program_descriptions": self.program_descriptions,
            "contact_information": self.contact_information,
            "past_grantees": self.past_grantees,
            "board_members": self.board_members,
            "people": self.people,
            "confidence_score": self.confidence_score,
            "source_url": self.source_url,
            "source_tax_year": self.source_tax_year,
        }


# ---------------------------------------------------------------------------
# Adapter: NarrativeExtractionResult → GrantFunderIntelligence
# ---------------------------------------------------------------------------

def from_narrative_extraction(result, ein: Optional[str] = None) -> "GrantFunderIntelligence":
    """
    Convert a NarrativeExtractionResult (from PDFNarrativeExtractor) into
    GrantFunderIntelligence.  Accepts either the dataclass or a plain dict.
    """
    if isinstance(result, dict):
        d = result
    else:
        # Dataclass — convert to dict via attribute access
        d = {
            "ein": getattr(result, "ein", ein or ""),
            "mission_statement": getattr(result, "mission_statement", None),
            "accepts_applications": getattr(result, "accepts_applications", "unknown"),
            "application_deadlines": getattr(result, "application_deadlines", None),
            "application_process": getattr(result, "application_process", None),
            "required_documents": getattr(result, "required_documents", []),
            "stated_priorities": getattr(result, "stated_priorities", []),
            "geographic_limitations": getattr(result, "geographic_limitations", None),
            "population_focus": getattr(result, "population_focus", None),
            "program_descriptions": getattr(result, "program_descriptions", []),
            "contact_information": getattr(result, "contact_information", None),
            "extraction_confidence": getattr(result, "extraction_confidence", 0.0),
            "source_pdf_url": getattr(result, "source_pdf_url", None),
            "source_tax_year": getattr(result, "source_tax_year", None),
            "officers": getattr(result, "officers", []) or [],
        }

    # Build structured people list from officers array
    officers_raw = d.get("officers") or []
    board_from_pdf: List[str] = []
    people_from_pdf: List[dict] = []
    for off in officers_raw:
        if not isinstance(off, dict):
            continue
        name = (off.get("name") or "").strip()
        if not name:
            continue
        board_from_pdf.append(name)
        entry: dict = {"name": name, "source": "990_pdf"}
        title = off.get("title") or off.get("position") or ""
        if title:
            entry["title"] = title
        comp = off.get("compensation")
        if comp is not None:
            entry["compensation"] = comp
        people_from_pdf.append(entry)

    return GrantFunderIntelligence(
        ein=d.get("ein") or ein or "",
        organization_name="",
        source=IntelligenceSource.PDF_990,
        accepts_applications=d.get("accepts_applications", "unknown"),
        application_deadlines=d.get("application_deadlines"),
        application_process=d.get("application_process"),
        required_documents=d.get("required_documents") or [],
        funding_priorities=d.get("stated_priorities") or [],
        geographic_limitations=d.get("geographic_limitations"),
        population_focus=d.get("population_focus"),
        mission_statement=d.get("mission_statement"),
        program_descriptions=d.get("program_descriptions") or [],
        contact_information=d.get("contact_information"),
        board_members=board_from_pdf,
        people=people_from_pdf,
        confidence_score=d.get("extraction_confidence") or d.get("confidence_score", 0.0),
        source_url=d.get("source_pdf_url"),
        source_tax_year=d.get("source_tax_year"),
    )


# ---------------------------------------------------------------------------
# Adapter: ein_intelligence.web_data dict → GrantFunderIntelligence
# ---------------------------------------------------------------------------

def from_web_data(web_data: dict, ein: str) -> "GrantFunderIntelligence":
    """
    Convert the web_data dict stored in ein_intelligence (as produced by
    the Claude web interpretation step in the research endpoint) into
    GrantFunderIntelligence.
    """
    contact = web_data.get("contact") or {}
    contact_str = None
    if contact:
        parts = [v for v in [contact.get("email"), contact.get("phone"), contact.get("address")] if v]
        contact_str = " | ".join(parts) if parts else None

    board: List[str] = []
    people_from_web: List[dict] = []
    for ldr in (web_data.get("leadership") or []):
        name = (ldr.get("name") or "").strip()
        if not name:
            continue
        board.append(name)
        entry: dict = {"name": name, "source": "web"}
        title = ldr.get("title") or ldr.get("role") or ""
        if title:
            entry["title"] = title
        email = ldr.get("email") or ""
        if email:
            entry["email"] = email
        people_from_web.append(entry)

    programs = [
        p.get("description") or p.get("name", "")
        for p in (web_data.get("programs") or [])
        if p.get("description") or p.get("name")
    ]
    key_facts = web_data.get("key_facts") or []

    return GrantFunderIntelligence(
        ein=ein,
        organization_name="",
        source=IntelligenceSource.WEB,
        mission_statement=web_data.get("mission"),
        program_descriptions=programs,
        board_members=board,
        people=people_from_web,
        contact_information=contact_str,
        funding_priorities=key_facts[:5],
        confidence_score=web_data.get("data_quality_score") or 0.7,
        source_url=web_data.get("website"),
    )


# ---------------------------------------------------------------------------
# Merge: combine W and 9 sources into unified GrantFunderIntelligence
# ---------------------------------------------------------------------------

def merge(
    web: Optional["GrantFunderIntelligence"],
    pdf: Optional["GrantFunderIntelligence"],
) -> "GrantFunderIntelligence":
    """
    Combine web and PDF sources into a single GrantFunderIntelligence.

    Strategy:
    - String fields: prefer higher-confidence source; fall back to the other
    - List fields: union (deduplicate)
    - accepts_applications: prefer any non-"unknown" value; if both known, use PDF
    - confidence_score: boost when both sources agree on a field
    """
    if web is None and pdf is None:
        raise ValueError("At least one source required")
    if web is None:
        return pdf
    if pdf is None:
        return web

    # Determine overall source
    source = IntelligenceSource.BOTH

    # For string fields, pick whichever is non-None (PDF preferred for grant fields)
    def _pick(pdf_val, web_val):
        if pdf_val and web_val:
            return pdf_val  # PDF authoritative for grant-specific text
        return pdf_val or web_val

    # accepts_applications: PDF wins if known
    if pdf.accepts_applications != "unknown":
        accepts = pdf.accepts_applications
    elif web.accepts_applications != "unknown":
        accepts = web.accepts_applications
    else:
        accepts = "unknown"

    # Union of lists (deduplicate preserving order)
    def _union(a: list, b: list) -> list:
        seen = set()
        result = []
        for item in (a or []) + (b or []):
            if item and item not in seen:
                seen.add(item)
                result.append(item)
        return result

    # Boost confidence when both sources present
    base_confidence = max(web.confidence_score, pdf.confidence_score)
    combined_confidence = min(base_confidence + 0.08, 1.0)

    ein = web.ein or pdf.ein
    org_name = web.organization_name or pdf.organization_name

    # Merge people: web first (has email), then add 990 entries not already present
    seen_names: set = set()
    merged_people: list = []
    for p in (web.people or []) + (pdf.people or []):
        key = (p.get("name") or "").lower().strip()
        if key and key not in seen_names:
            seen_names.add(key)
            merged_people.append(p)

    return GrantFunderIntelligence(
        ein=ein,
        organization_name=org_name,
        source=source,
        accepts_applications=accepts,
        application_deadlines=_pick(pdf.application_deadlines, web.application_deadlines),
        application_process=_pick(pdf.application_process, web.application_process),
        required_documents=_union(pdf.required_documents, web.required_documents),
        funding_priorities=_union(pdf.funding_priorities, web.funding_priorities),
        geographic_limitations=_pick(pdf.geographic_limitations, web.geographic_limitations),
        grant_size_range=_pick(pdf.grant_size_range, web.grant_size_range),
        population_focus=_pick(pdf.population_focus, web.population_focus),
        mission_statement=_pick(pdf.mission_statement, web.mission_statement),
        program_descriptions=_union(pdf.program_descriptions, web.program_descriptions),
        contact_information=_pick(pdf.contact_information, web.contact_information),
        past_grantees=_union(pdf.past_grantees, web.past_grantees),
        board_members=_union(web.board_members, pdf.board_members),  # web first (more reliable)
        people=merged_people,
        confidence_score=combined_confidence,
        source_url=web.source_url or pdf.source_url,
        source_tax_year=pdf.source_tax_year,
    )


def build_from_ein_intelligence(
    web_data: Optional[dict],
    pdf_analyses: Optional[dict],
    ein: str,
) -> Optional["GrantFunderIntelligence"]:
    """
    Build GrantFunderIntelligence from raw ein_intelligence fields.
    Returns None if no usable data available.

    Args:
        web_data:     ein_intelligence.web_data (dict from Claude interpretation)
        pdf_analyses: ein_intelligence.pdf_analyses (dict of {cache_key: extraction})
        ein:          EIN string
    """
    web_intel = None
    pdf_intel = None

    if web_data and isinstance(web_data, dict):
        try:
            web_intel = from_web_data(web_data, ein)
        except Exception:
            pass

    if pdf_analyses and isinstance(pdf_analyses, dict):
        # Use the most recently cached extraction (first key found)
        for _cache_key, extraction in pdf_analyses.items():
            if isinstance(extraction, dict) and extraction.get("extraction_confidence", 0) > 0:
                try:
                    pdf_intel = from_narrative_extraction(extraction, ein)
                    break
                except Exception:
                    pass

    if web_intel is None and pdf_intel is None:
        return None

    return merge(web_intel, pdf_intel)
