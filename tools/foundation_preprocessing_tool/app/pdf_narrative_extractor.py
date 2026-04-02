#!/usr/bin/env python3
"""
PDF Narrative Extractor - Extract foundation intelligence from 990-PF PDFs

Uses Anthropic's Claude API with PDF document support to extract narrative
content from IRS Form 990-PF filings that isn't available in structured
SOI extract data.

Extracts:
  - Foundation mission statement (Part I)
  - Application acceptance status (Part XV)
  - Application deadlines and process
  - Program area descriptions (Part XVI)
  - Geographic giving limitations
  - Contact information for applications

Cost: ~$0.01-0.03 per PDF (using Claude Haiku)
Strategy: Extract once per foundation, cache in foundation_narratives table
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class NarrativeExtractionResult:
    """Structured output from PDF narrative extraction."""
    ein: str
    mission_statement: Optional[str] = None
    mission_keywords: List[str] = field(default_factory=list)
    accepts_applications: str = "unknown"  # yes, no, invitation_only, unknown
    application_deadlines: Optional[str] = None
    application_process: Optional[str] = None
    required_documents: List[str] = field(default_factory=list)
    contact_information: Optional[str] = None
    program_descriptions: List[str] = field(default_factory=list)
    stated_priorities: List[str] = field(default_factory=list)
    geographic_limitations: Optional[str] = None
    population_focus: Optional[str] = None
    grant_size_range: Optional[str] = None
    officers: List[Dict[str, Any]] = field(default_factory=list)  # [{name, title, compensation}]
    extraction_confidence: float = 0.0
    pdf_pages_note: Optional[str] = None  # set when PDF was truncated
    source_tax_year: Optional[int] = None
    source_pdf_url: Optional[str] = None


@dataclass
class BatchExtractionStats:
    """Statistics from a batch extraction run."""
    total_attempted: int = 0
    successful: int = 0
    failed: int = 0
    skipped_cached: int = 0
    total_cost_estimate: float = 0.0
    execution_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)


class PDFNarrativeExtractor:
    """
    Extract foundation narrative content from 990-PF PDF filings.

    Uses Anthropic's document understanding to parse IRS forms and extract
    structured intelligence that feeds into the foundation_narratives table.
    """

    PDF_PAGE_LIMIT = 10  # Officers/directors (Part VII) are in first ~10 pages; 35 was excessive and triggered rate limits

    EXTRACTION_PROMPT = """Analyze this IRS nonprofit tax filing (Form 990, 990-EZ, or 990-PF) and extract grant-making intelligence.

Return a JSON object with exactly these fields:

{
  "mission_statement": "The organization's stated mission or purpose. null if not found.",
  "mission_keywords": ["keyword1", "keyword2"],
  "accepts_applications": "yes" or "no" or "invitation_only" or "unknown",
  "application_deadlines": "Deadline information if stated. null if not found.",
  "application_process": "How to apply — letter of inquiry, online portal, full proposal, etc. null if not found.",
  "required_documents": ["document1", "document2"],
  "contact_information": "Contact person/address/email for grant applications. null if not found.",
  "program_descriptions": ["Description of each program area or grant focus"],
  "stated_priorities": ["Each stated funding priority, preference, or restriction"],
  "geographic_limitations": "Geographic restrictions on giving. null if not found.",
  "population_focus": "Target populations served or funded. null if not found.",
  "grant_size_range": "Typical grant range if mentioned (e.g. '$5,000-$50,000'). null if not found.",
  "officers": [{"name": "Full Name", "title": "Title/Role", "compensation": null}],
  "confidence": 0.0
}

Where to look depending on form type:
- Form 990-PF: Part XV (Application Information), Part I (Overview), Part XV-A (Grant Application), Schedule of Distributions, Part VIII (Officers, Directors, Trustees, Foundation Managers)
- Form 990: Part III (Program Service Accomplishments), Part IX (Grants column), Schedule I (Grants to Organizations), any narrative sections, Part VII (Compensation of Officers, Directors, Trustees)
- Form 990-EZ: Part III (Program Service Accomplishments), Schedule O (Supplemental Information), Part IV (Officers, Directors, Trustees, and Key Employees)
- All forms: Any supplemental narrative, mission statements, program descriptions

For officers: list all officers, directors, trustees, and key employees found in Part VII (Form 990), Part VIII (Form 990-PF), or Part IV (Form 990-EZ). Include name, title, and compensation (integer dollars or null if not listed/zero).

Set "confidence" based on how much useful grant-making data you found:
- 0.8-1.0: Rich data — application process, priorities, and geographic info all found
- 0.5-0.79: Partial data — some priorities or contact info found
- 0.2-0.49: Sparse data — only mission or basic info found
- 0.0-0.19: Little to no grant-making information in this filing

If a field has no data in the filing, use null for strings and empty arrays for lists.
Return ONLY the JSON object, no other text."""

    def __init__(
        self,
        intelligence_db_path: str,
        anthropic_api_key: Optional[str] = None,
        model: str = "claude-haiku-4-5-20251001",
    ):
        self.intelligence_db_path = intelligence_db_path
        self.model = model
        self._client = None

        # API key from param or environment
        self.api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")

    def _fetch_and_truncate_pdf(self, pdf_url: str) -> tuple[bytes, int, int]:
        """
        Download PDF and truncate to PDF_PAGE_LIMIT pages if needed.

        Returns:
            (pdf_bytes, total_pages, pages_sent)
        """
        import io
        import urllib.request

        req = urllib.request.Request(pdf_url, headers={"User-Agent": "Catalynx/1.0 Grant Research"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()

        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(raw))
            total_pages = len(reader.pages)

            if total_pages <= self.PDF_PAGE_LIMIT:
                return raw, total_pages, total_pages

            # Truncate: write first PDF_PAGE_LIMIT pages to a new buffer
            writer = pypdf.PdfWriter()
            for i in range(self.PDF_PAGE_LIMIT):
                writer.add_page(reader.pages[i])
            buf = io.BytesIO()
            writer.write(buf)
            return buf.getvalue(), total_pages, self.PDF_PAGE_LIMIT
        except ImportError:
            logger.warning("pypdf not available — sending full PDF without truncation. Install pypdf to enable page limiting.")
            return raw, 0, 0

    def _get_client(self):
        """Lazy-initialize Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package required. Install with: pip install anthropic"
                )
        return self._client

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.intelligence_db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def extract_from_pdf_url(
        self, ein: str, pdf_url: str, tax_year: Optional[int] = None
    ) -> NarrativeExtractionResult:
        """
        Extract narrative content from a 990 PDF via URL.

        Downloads the PDF, truncates to PDF_PAGE_LIMIT pages if needed (grant info
        is in early sections; later pages are schedules/lists that inflate page count),
        then sends as base64 to Claude.

        Args:
            ein: Organization EIN
            pdf_url: URL to the PDF filing
            tax_year: Tax year of the filing

        Returns:
            NarrativeExtractionResult with extracted data
        """
        import base64

        result = NarrativeExtractionResult(
            ein=ein,
            source_pdf_url=pdf_url,
            source_tax_year=tax_year,
        )

        try:
            client = self._get_client()

            # Download and truncate if needed
            pdf_bytes, total_pages, pages_sent = self._fetch_and_truncate_pdf(pdf_url)
            if total_pages > pages_sent:
                result.pdf_pages_note = f"PDF truncated: analyzed first {pages_sent} of {total_pages} pages (grant info is in early sections)"
                logger.info(f"PDF truncated for {ein}: {total_pages} pages -> sending first {pages_sent}")

            pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

            message = client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": self.EXTRACTION_PROMPT,
                        },
                    ],
                }],
            )

            # Parse the JSON response
            response_text = message.content[0].text.strip()
            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

            data = json.loads(response_text)

            result.mission_statement = data.get("mission_statement")
            result.mission_keywords = data.get("mission_keywords", [])
            result.accepts_applications = data.get("accepts_applications", "unknown")
            result.application_deadlines = data.get("application_deadlines")
            result.application_process = data.get("application_process")
            result.required_documents = data.get("required_documents", [])
            result.contact_information = data.get("contact_information")
            result.program_descriptions = data.get("program_descriptions", [])
            result.stated_priorities = data.get("stated_priorities", [])
            result.geographic_limitations = data.get("geographic_limitations")
            result.population_focus = data.get("population_focus")
            result.grant_size_range = data.get("grant_size_range")
            result.officers = data.get("officers", [])
            result.extraction_confidence = data.get("confidence", 0.5)

            logger.info(f"Extracted narrative for {ein}: mission={'yes' if result.mission_statement else 'no'}, "
                       f"accepts_apps={result.accepts_applications}, officers={len(result.officers)}, conf={result.extraction_confidence}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response for {ein}: {e}")
            result.extraction_confidence = 0.0
        except Exception as e:
            logger.error(f"PDF extraction failed for {ein}: {e}")
            result.extraction_confidence = 0.0

        return result

    async def extract_from_pdf_file(
        self, ein: str, pdf_path: str, tax_year: Optional[int] = None
    ) -> NarrativeExtractionResult:
        """
        Extract narrative content from a local 990-PF PDF file.

        Args:
            ein: Foundation EIN
            pdf_path: Local path to the 990-PF PDF filing
            tax_year: Tax year of the filing

        Returns:
            NarrativeExtractionResult with extracted data
        """
        import base64

        result = NarrativeExtractionResult(
            ein=ein,
            source_pdf_url=f"file://{pdf_path}",
            source_tax_year=tax_year,
        )

        try:
            client = self._get_client()

            with open(pdf_path, "rb") as f:
                pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

            message = client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": self.EXTRACTION_PROMPT,
                        },
                    ],
                }],
            )

            response_text = message.content[0].text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

            data = json.loads(response_text)

            result.mission_statement = data.get("mission_statement")
            result.mission_keywords = data.get("mission_keywords", [])
            result.accepts_applications = data.get("accepts_applications", "unknown")
            result.application_deadlines = data.get("application_deadlines")
            result.application_process = data.get("application_process")
            result.required_documents = data.get("required_documents", [])
            result.contact_information = data.get("contact_information")
            result.program_descriptions = data.get("program_descriptions", [])
            result.stated_priorities = data.get("stated_priorities", [])
            result.geographic_limitations = data.get("geographic_limitations")
            result.population_focus = data.get("population_focus")
            result.grant_size_range = data.get("grant_size_range")
            result.extraction_confidence = data.get("confidence", 0.5)

        except Exception as e:
            logger.error(f"PDF file extraction failed for {ein}: {e}")
            result.extraction_confidence = 0.0

        return result

    def cache_narrative(self, result: NarrativeExtractionResult):
        """Store extraction result in foundation_narratives table."""
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO foundation_narratives (
                    ein, mission_statement, mission_keywords,
                    accepts_applications, application_deadlines,
                    application_process, required_documents,
                    contact_information, program_descriptions,
                    stated_priorities, geographic_limitations,
                    population_focus, source_pdf_url, source_tax_year,
                    extraction_model, extraction_confidence, extracted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.ein,
                result.mission_statement,
                json.dumps(result.mission_keywords),
                result.accepts_applications,
                result.application_deadlines,
                result.application_process,
                json.dumps(result.required_documents),
                result.contact_information,
                json.dumps(result.program_descriptions),
                json.dumps(result.stated_priorities),
                result.geographic_limitations,
                result.population_focus,
                result.source_pdf_url,
                result.source_tax_year,
                self.model,
                result.extraction_confidence,
                datetime.now().isoformat(),
            ))
            conn.commit()
        finally:
            conn.close()

    def get_cached_narrative(self, ein: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached narrative for a foundation."""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM foundation_narratives WHERE ein = ?", (ein,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    async def batch_extract(
        self,
        ein_pdf_pairs: List[Dict[str, str]],
        skip_cached: bool = True,
        concurrency: int = 5,
    ) -> BatchExtractionStats:
        """
        Batch extract narratives from multiple 990-PF PDFs.

        Args:
            ein_pdf_pairs: List of {"ein": "...", "pdf_url": "...", "tax_year": ...}
            skip_cached: Skip EINs that already have cached narratives
            concurrency: Max concurrent extractions

        Returns:
            BatchExtractionStats with results summary
        """
        start_time = time.time()
        stats = BatchExtractionStats(total_attempted=len(ein_pdf_pairs))

        # Filter already-cached
        to_process = []
        if skip_cached:
            conn = self._get_connection()
            try:
                for pair in ein_pdf_pairs:
                    cached = conn.execute(
                        "SELECT ein FROM foundation_narratives WHERE ein = ?",
                        (pair["ein"],)
                    ).fetchone()
                    if cached:
                        stats.skipped_cached += 1
                    else:
                        to_process.append(pair)
            finally:
                conn.close()
        else:
            to_process = ein_pdf_pairs

        # Process with concurrency limit
        semaphore = asyncio.Semaphore(concurrency)

        async def process_one(pair: Dict[str, str]):
            async with semaphore:
                try:
                    result = await self.extract_from_pdf_url(
                        ein=pair["ein"],
                        pdf_url=pair["pdf_url"],
                        tax_year=pair.get("tax_year"),
                    )
                    if result.extraction_confidence > 0:
                        self.cache_narrative(result)
                        stats.successful += 1
                        stats.total_cost_estimate += 0.01  # ~$0.01 per Haiku call
                    else:
                        stats.failed += 1
                except Exception as e:
                    stats.failed += 1
                    stats.errors.append(f"{pair['ein']}: {str(e)}")

        # Run extractions
        tasks = [process_one(pair) for pair in to_process]
        await asyncio.gather(*tasks)

        stats.execution_time_ms = (time.time() - start_time) * 1000
        return stats

    def update_intelligence_index(self):
        """
        Push accepts_applications data from narratives into foundation_intelligence_index.
        Call after batch extraction to update the main index.
        """
        conn = self._get_connection()
        try:
            conn.execute("""
                UPDATE foundation_intelligence_index
                SET accepts_applications = fn.accepts_applications
                FROM foundation_narratives fn
                WHERE foundation_intelligence_index.ein = fn.ein
                  AND fn.accepts_applications != 'unknown'
            """)
            conn.commit()
            logger.info("Updated intelligence index with narrative application data")
        except sqlite3.OperationalError as e:
            logger.error(f"Failed to update intelligence index: {e}")
        finally:
            conn.close()


# =============================================================================
# IRS E-FILE PDF URL BUILDER
# =============================================================================

def build_irs_pdf_url(ein: str, tax_year: int = 2023) -> str:
    """
    Build URL for IRS e-file PDF.

    The IRS publishes 990-PF filings as XML on their e-file system.
    PDF versions are available through ProPublica's nonprofit explorer.
    """
    # ProPublica hosts rendered PDFs of 990 filings
    ein_clean = ein.replace("-", "")
    return f"https://projects.propublica.org/nonprofits/download-filing/{ein_clean}"


def get_priority_foundations_for_extraction(
    intelligence_db_path: str,
    limit: int = 100,
    min_capacity_tier: str = "significant",
) -> List[Dict[str, str]]:
    """
    Get the highest-priority foundations that need PDF narrative extraction.

    Priority: high-capacity foundations without cached narratives.
    """
    conn = sqlite3.connect(intelligence_db_path)
    conn.row_factory = sqlite3.Row
    try:
        tier_order = {"mega": 1, "major": 2, "significant": 3, "modest": 4, "minimal": 5}
        max_tier_rank = tier_order.get(min_capacity_tier, 3)

        eligible_tiers = [t for t, r in tier_order.items() if r <= max_tier_rank]
        placeholders = ",".join("?" * len(eligible_tiers))

        query = f"""
            SELECT fi.ein, fi.grants_paid_latest, fi.capacity_tier, fi.source_tax_year
            FROM foundation_intelligence_index fi
            LEFT JOIN foundation_narratives fn ON fi.ein = fn.ein
            WHERE fi.is_eligible_grantmaker = 1
              AND fi.capacity_tier IN ({placeholders})
              AND fn.ein IS NULL
            ORDER BY fi.grants_paid_latest DESC
            LIMIT ?
        """
        cursor = conn.execute(query, eligible_tiers + [limit])

        results = []
        for row in cursor:
            results.append({
                "ein": row["ein"],
                "pdf_url": build_irs_pdf_url(row["ein"], row["source_tax_year"] or 2023),
                "tax_year": row["source_tax_year"],
            })
        return results
    finally:
        conn.close()
