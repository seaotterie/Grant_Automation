"""
Funder Enrichment Module — Pulls intelligence about opportunity funders from
the nonprofit intelligence database to provide richer context for AI screening.

Data sources:
  - foundation_intelligence_index: Precomputed 990-PF features (capacity, trends, compliance)
  - form_990pf: Raw 990-PF financials (grants paid, assets, investments)
  - form_990: Regular 990 data for non-foundation funders
  - bmf_organizations: Basic org info (name, NTEE, location)

This module is stateless and read-only — it queries the database and returns
a structured dict of funder context that gets injected into the screening prompt.

Cost: $0 (pure SQL queries)
Latency: <50ms per funder lookup
"""

import json
import logging
import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _get_intelligence_db_path() -> str:
    """Get the path to nonprofit_intelligence.db."""
    # Check env var first
    db_path = os.getenv("INTELLIGENCE_DATABASE_PATH")
    if db_path and os.path.exists(db_path):
        return db_path

    # Default: project_root/data/nonprofit_intelligence.db
    project_root = Path(__file__).parent.parent.parent.parent
    default_path = project_root / "data" / "nonprofit_intelligence.db"
    return str(default_path)


@dataclass
class FunderIntelligence:
    """Structured funder context for screening prompt enrichment."""
    funder_name: str
    ein: Optional[str] = None
    funder_type: str = "unknown"  # "foundation", "government", "nonprofit", "unknown"

    # Basic identity
    ntee_code: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None

    # Financial profile (from 990-PF or 990)
    total_assets: Optional[int] = None
    total_revenue: Optional[int] = None
    grants_paid: Optional[int] = None
    avg_grant_size: Optional[int] = None
    annual_grant_budget: Optional[int] = None

    # Foundation-specific (from intelligence index)
    capacity_tier: Optional[str] = None
    giving_trend: Optional[str] = None
    giving_trend_pct: Optional[float] = None
    health_status: Optional[str] = None
    payout_compliance: Optional[str] = None
    accepts_applications: Optional[str] = None
    is_operating_foundation: bool = False

    # Geographic focus
    primary_grant_states: List[str] = field(default_factory=list)
    geographic_concentration: Optional[float] = None

    # Grant purpose
    primary_archetype: Optional[str] = None
    secondary_archetypes: List[str] = field(default_factory=list)

    # Data quality
    data_quality_score: float = 0.0
    source_tax_year: Optional[int] = None

    def to_prompt_context(self) -> str:
        """Format funder intelligence as text for injection into screening prompt."""
        lines = [f"FUNDER INTELLIGENCE ({self.funder_name}):"]

        if self.ein:
            lines.append(f"  EIN: {self.ein}")
        if self.ntee_code:
            lines.append(f"  NTEE Code: {self.ntee_code}")
        if self.state:
            location = f"{self.city}, {self.state}" if self.city else self.state
            lines.append(f"  Location: {location}")

        # Financial
        financials = []
        if self.total_assets:
            financials.append(f"Assets: ${self.total_assets:,}")
        if self.grants_paid:
            financials.append(f"Grants Paid: ${self.grants_paid:,}")
        if self.avg_grant_size:
            financials.append(f"Avg Grant: ${self.avg_grant_size:,}")
        if self.annual_grant_budget:
            financials.append(f"Annual Budget: ${self.annual_grant_budget:,}")
        if financials:
            lines.append(f"  Financials: {', '.join(financials)}")

        # Foundation intelligence
        if self.capacity_tier:
            lines.append(f"  Capacity: {self.capacity_tier}")
        if self.giving_trend and self.giving_trend != "unknown":
            trend = self.giving_trend
            if self.giving_trend_pct is not None:
                trend += f" ({self.giving_trend_pct:+.1f}% YoY)"
            lines.append(f"  Giving Trend: {trend}")
        if self.health_status and self.health_status != "unknown":
            lines.append(f"  Financial Health: {self.health_status}")
        if self.payout_compliance and self.payout_compliance != "unknown":
            lines.append(f"  Payout Status: {self.payout_compliance}")
        if self.accepts_applications and self.accepts_applications != "unknown":
            lines.append(f"  Accepts Applications: {self.accepts_applications}")
        if self.is_operating_foundation:
            lines.append("  WARNING: Operating foundation (may not make external grants)")

        # Geographic focus
        if self.primary_grant_states:
            lines.append(f"  Grant Geography: {', '.join(self.primary_grant_states)}")
            if self.geographic_concentration and self.geographic_concentration > 0.7:
                lines.append("  NOTE: Highly geographically concentrated funder")

        # Purpose
        if self.primary_archetype:
            archetypes = [self.primary_archetype] + self.secondary_archetypes
            lines.append(f"  Grant Focus: {', '.join(archetypes)}")

        if len(lines) == 1:
            lines.append("  No intelligence data available for this funder.")

        return "\n".join(lines)


def lookup_funder(
    funder_name: str,
    funder_ein: Optional[str] = None,
    funder_type: str = "unknown",
    db_path: Optional[str] = None,
) -> FunderIntelligence:
    """
    Look up funder intelligence from the nonprofit intelligence database.

    Tries multiple lookup strategies:
    1. Direct EIN match in foundation_intelligence_index (fastest)
    2. Direct EIN match in bmf_organizations
    3. Name-based fuzzy match in bmf_organizations (fallback)

    Args:
        funder_name: Funder organization name
        funder_ein: Funder EIN if known
        funder_type: "foundation", "government", "corporate", or "unknown"
        db_path: Override database path

    Returns:
        FunderIntelligence with whatever data was found
    """
    db = db_path or _get_intelligence_db_path()
    result = FunderIntelligence(funder_name=funder_name, funder_type=funder_type)

    if not os.path.exists(db):
        logger.debug(f"Intelligence database not found at {db}")
        return result

    try:
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row

        # Strategy 1: If we have an EIN, try foundation intelligence index
        if funder_ein:
            result.ein = funder_ein
            _enrich_from_foundation_index(conn, result)

            # If not in foundation index, try BMF + form_990
            if not result.capacity_tier:
                _enrich_from_bmf(conn, result)
                _enrich_from_form_990(conn, result)

        # Strategy 2: Name-based lookup in BMF
        if not result.ein or (not result.total_assets and not result.capacity_tier):
            _enrich_from_bmf_by_name(conn, result)

        conn.close()

    except Exception as e:
        logger.warning(f"Funder enrichment failed for {funder_name}: {e}")

    return result


def _enrich_from_foundation_index(conn: sqlite3.Connection, result: FunderIntelligence) -> None:
    """Pull precomputed features from foundation_intelligence_index."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                capacity_tier, grants_paid_latest, assets_fmv_latest,
                avg_grant_size, annual_grant_budget_estimate,
                giving_trend, giving_trend_pct, years_of_data,
                is_eligible_grantmaker, accepts_applications,
                is_operating_foundation, health_status, payout_compliance,
                primary_states, geographic_concentration,
                primary_archetype, secondary_archetypes,
                ntee_code, data_quality_score, source_tax_year
            FROM foundation_intelligence_index
            WHERE ein = ?
        """, (result.ein,))

        row = cursor.fetchone()
        if not row:
            return

        result.funder_type = "foundation"
        result.capacity_tier = row["capacity_tier"]
        result.grants_paid = row["grants_paid_latest"]
        result.total_assets = row["assets_fmv_latest"]
        result.avg_grant_size = row["avg_grant_size"]
        result.annual_grant_budget = row["annual_grant_budget_estimate"]
        result.giving_trend = row["giving_trend"]
        result.giving_trend_pct = row["giving_trend_pct"]
        result.health_status = row["health_status"]
        result.payout_compliance = row["payout_compliance"]
        result.accepts_applications = row["accepts_applications"]
        result.is_operating_foundation = bool(row["is_operating_foundation"])
        result.ntee_code = row["ntee_code"]
        result.data_quality_score = row["data_quality_score"] or 0.0
        result.source_tax_year = row["source_tax_year"]

        # Parse JSON fields
        if row["primary_states"]:
            try:
                result.primary_grant_states = json.loads(row["primary_states"])
            except (json.JSONDecodeError, TypeError):
                pass

        result.geographic_concentration = row["geographic_concentration"]

        result.primary_archetype = row["primary_archetype"]
        if row["secondary_archetypes"]:
            try:
                result.secondary_archetypes = json.loads(row["secondary_archetypes"])
            except (json.JSONDecodeError, TypeError):
                pass

        logger.debug(f"Foundation index enrichment for {result.ein}: capacity={result.capacity_tier}")

    except sqlite3.OperationalError as e:
        # Table may not exist yet
        logger.debug(f"Foundation index query failed (table may not exist): {e}")


def _enrich_from_bmf(conn: sqlite3.Connection, result: FunderIntelligence) -> None:
    """Pull basic org info from bmf_organizations."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, ntee_code, state, city, foundation_code
            FROM bmf_organizations
            WHERE ein = ?
            LIMIT 1
        """, (result.ein,))

        row = cursor.fetchone()
        if not row:
            return

        if not result.funder_name or result.funder_name == "Unknown":
            result.funder_name = row["name"]
        result.ntee_code = result.ntee_code or row["ntee_code"]
        result.state = row["state"]
        result.city = row["city"]

    except sqlite3.OperationalError as e:
        logger.debug(f"BMF query failed: {e}")


def _enrich_from_form_990(conn: sqlite3.Connection, result: FunderIntelligence) -> None:
    """Pull financial data from form_990 (regular nonprofits)."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                totrevenue, totfuncexpns, totassetsend, totliabend,
                tax_year
            FROM form_990
            WHERE ein = ?
            ORDER BY tax_year DESC
            LIMIT 1
        """, (result.ein,))

        row = cursor.fetchone()
        if not row:
            return

        result.total_revenue = row["totrevenue"]
        result.total_assets = row["totassetsend"]
        result.source_tax_year = row["tax_year"]

    except sqlite3.OperationalError as e:
        logger.debug(f"Form 990 query failed: {e}")


def _enrich_from_bmf_by_name(conn: sqlite3.Connection, result: FunderIntelligence) -> None:
    """Fuzzy name lookup in BMF as last resort."""
    if not result.funder_name:
        return

    try:
        cursor = conn.cursor()
        # Use LIKE for basic name matching (normalized to uppercase in BMF)
        name_pattern = f"%{result.funder_name.upper()}%"
        cursor.execute("""
            SELECT ein, name, ntee_code, state, city
            FROM bmf_organizations
            WHERE UPPER(name) LIKE ?
            LIMIT 1
        """, (name_pattern,))

        row = cursor.fetchone()
        if not row:
            return

        if not result.ein:
            result.ein = row["ein"]
        result.ntee_code = result.ntee_code or row["ntee_code"]
        result.state = result.state or row["state"]
        result.city = result.city or row["city"]

        # Now try to get financial data with the discovered EIN
        if result.ein:
            _enrich_from_foundation_index(conn, result)
            if not result.capacity_tier:
                _enrich_from_form_990(conn, result)

    except sqlite3.OperationalError as e:
        logger.debug(f"BMF name lookup failed: {e}")


def enrich_opportunities_batch(
    opportunities: list,
    db_path: Optional[str] = None,
) -> Dict[str, FunderIntelligence]:
    """
    Batch-enrich a list of opportunities with funder intelligence.

    Args:
        opportunities: List of Opportunity objects
        db_path: Override database path

    Returns:
        Dict mapping funder name to FunderIntelligence
    """
    cache: Dict[str, FunderIntelligence] = {}

    for opp in opportunities:
        funder_key = opp.funder
        if funder_key not in cache:
            # Extract EIN from opportunity if available
            funder_ein = getattr(opp, "funder_ein", None)
            cache[funder_key] = lookup_funder(
                funder_name=opp.funder,
                funder_ein=funder_ein,
                funder_type=opp.funder_type,
                db_path=db_path,
            )

    enriched = sum(1 for v in cache.values() if v.capacity_tier or v.total_assets)
    logger.info(
        f"Funder enrichment: {len(cache)} unique funders, "
        f"{enriched} enriched with intelligence data"
    )

    return cache
