"""
URL Bulk Resolver — standalone CLI for resolving missing opportunity URLs.

Runs outside the web application against the same SQLite databases.
Two modes:

  --bulk-only   (default, fast)
      Queries organization_websites (bulk-loaded from IRS XML) and updates
      any opportunity whose EIN has a match. Pure SQLite, no network calls.
      Typical runtime: seconds for thousands of opportunities.

  --pipeline
      After the bulk-only pass, runs unresolved EINs through the full
      EnhancedURLDiscoveryPipeline (ProPublica API, Haiku predictor, etc).
      Requires ANTHROPIC_API_KEY. Can be slow (2-4s per org).

Usage:
    python tools/url_bulk_resolver/url_bulk_resolver.py
    python tools/url_bulk_resolver/url_bulk_resolver.py --profile profile_812827604
    python tools/url_bulk_resolver/url_bulk_resolver.py --pipeline --limit 100
    python tools/url_bulk_resolver/url_bulk_resolver.py --retry-not-found --bulk-only
    python tools/url_bulk_resolver/url_bulk_resolver.py --dry-run

Run from the project root directory.
"""

import argparse
import asyncio
import logging
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Path setup — allow running from project root without installing the package
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("url_bulk_resolver")

# ---------------------------------------------------------------------------
# Default DB paths (override with --catalynx-db / --intel-db)
# ---------------------------------------------------------------------------
DEFAULT_CATALYNX_DB = PROJECT_ROOT / "data" / "catalynx.db"
DEFAULT_INTEL_DB    = PROJECT_ROOT / "data" / "nonprofit_intelligence.db"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_unresolved_opportunities(
    catalynx_db: str,
    profile_id: Optional[str],
    retry_not_found: bool,
    limit: Optional[int],
) -> list[dict]:
    """
    Return opportunities that need URL resolution.

    Default: website_url IS NULL AND url_source IS NULL  (never attempted)
    With --retry-not-found: also includes url_source = 'not_found'
    """
    conn = sqlite3.connect(catalynx_db, timeout=10)
    conn.row_factory = sqlite3.Row

    if retry_not_found:
        where_url = "(website_url IS NULL AND (url_source IS NULL OR url_source = 'not_found'))"
    else:
        where_url = "(website_url IS NULL AND url_source IS NULL)"

    profile_clause = "AND profile_id = ?" if profile_id else ""
    limit_clause   = f"LIMIT {limit}" if limit else ""

    params = [profile_id] if profile_id else []

    rows = conn.execute(
        f"""
        SELECT id, profile_id, organization_name, ein, url_source
        FROM opportunities
        WHERE {where_url}
          {profile_clause}
        ORDER BY created_at DESC
        {limit_clause}
        """,
        params,
    ).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def bulk_db_lookup(intel_db: str, ein: str) -> Optional[str]:
    """Check organization_websites table for a pre-loaded URL."""
    try:
        conn = sqlite3.connect(intel_db, timeout=5)
        row = conn.execute(
            "SELECT website_url FROM organization_websites WHERE ein = ?", (ein,)
        ).fetchone()
        conn.close()
        return row[0] if row and row[0] else None
    except Exception:
        return None


def update_opportunity_url(
    catalynx_db: str,
    opp_id: str,
    url: Optional[str],
    source: str,
    verification_status: str,
    dry_run: bool,
) -> None:
    """Write URL (or not_found marker) back to the opportunity row."""
    if dry_run:
        return
    try:
        conn = sqlite3.connect(catalynx_db, timeout=10)
        now = _now()
        conn.execute(
            """
            UPDATE opportunities
            SET website_url = ?,
                url_source = ?,
                url_discovered_at = ?,
                url_verification_status = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (url, source, now, verification_status, now, opp_id),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB update failed for {opp_id}: {e}")


# ---------------------------------------------------------------------------
# Bulk-only pass (pure SQLite, no network)
# ---------------------------------------------------------------------------

def run_bulk_pass(
    opportunities: list[dict],
    intel_db: str,
    catalynx_db: str,
    dry_run: bool,
) -> tuple[list[dict], int]:
    """
    For each opportunity, check organization_websites. Update on hit.
    Returns (unresolved_remaining, bulk_hit_count).
    """
    unresolved = []
    hits = 0

    # Batch lookup: pull all EINs at once for speed
    eins = [o["ein"] for o in opportunities if o.get("ein")]
    if not eins:
        return opportunities, 0

    conn = sqlite3.connect(intel_db, timeout=10)
    placeholders = ",".join("?" * len(eins))
    rows = conn.execute(
        f"SELECT ein, website_url FROM organization_websites WHERE ein IN ({placeholders})",
        eins,
    ).fetchall()
    conn.close()

    bulk_map = {r[0]: r[1] for r in rows if r[1]}

    for opp in opportunities:
        ein = opp.get("ein")
        url = bulk_map.get(ein) if ein else None
        if url:
            logger.info(f"  Bulk DB: {opp['organization_name']} → {url}")
            update_opportunity_url(
                catalynx_db, opp["id"], url, "990_xml_bulk", "bulk_loaded", dry_run
            )
            hits += 1
        else:
            unresolved.append(opp)

    return unresolved, hits


# ---------------------------------------------------------------------------
# Pipeline pass (async, network calls)
# ---------------------------------------------------------------------------

async def run_pipeline_pass(
    opportunities: list[dict],
    catalynx_db: str,
    dry_run: bool,
    log_interval: int = 10,
) -> tuple[int, int]:
    """
    Run unresolved opportunities through EnhancedURLDiscoveryPipeline.
    Returns (pipeline_found, pipeline_not_found).
    """
    if not opportunities:
        return 0, 0

    try:
        from src.core.enhanced_url_discovery import EnhancedURLDiscoveryPipeline
    except ImportError as e:
        logger.error(f"Cannot import pipeline: {e}")
        logger.error("Ensure you're running from the project root with dependencies installed.")
        return 0, len(opportunities)

    pipeline = EnhancedURLDiscoveryPipeline()
    found = 0
    not_found = 0
    start = time.time()

    for idx, opp in enumerate(opportunities, 1):
        ein  = opp.get("ein")
        name = opp.get("organization_name", "Unknown")

        if not ein:
            not_found += 1
            update_opportunity_url(catalynx_db, opp["id"], None, "not_found", "not_found", dry_run)
            continue

        try:
            result = await pipeline.discover(ein=ein, organization_name=name)

            if result.primary_url:
                url        = result.primary_url.url
                source     = result.primary_url.source
                confidence = result.primary_url.final_confidence
                stage      = result.stage_resolved
                status     = "verified" if confidence >= 0.70 else "pending"

                logger.info(f"  Pipeline stage {stage}: {name} → {url} (conf={confidence:.2f})")
                update_opportunity_url(catalynx_db, opp["id"], url, source, status, dry_run)
                found += 1
            else:
                logger.debug(f"  No URL found: {name} (EIN {ein})")
                update_opportunity_url(catalynx_db, opp["id"], None, "not_found", "not_found", dry_run)
                not_found += 1

        except Exception as e:
            logger.warning(f"  Pipeline error for {name}: {e}")
            not_found += 1

        if idx % log_interval == 0:
            elapsed = time.time() - start
            rate = idx / elapsed if elapsed > 0 else 0
            remaining = len(opportunities) - idx
            eta = f"{remaining / rate / 60:.0f}m" if rate > 0 else "?"
            logger.info(
                f"  Progress: {idx}/{len(opportunities)} | "
                f"found={found} not_found={not_found} | "
                f"{rate:.1f}/s  ETA {eta}"
            )

    return found, not_found


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(
        description="Resolve missing opportunity URLs from bulk DB and/or pipeline."
    )
    parser.add_argument("--profile", metavar="PROFILE_ID",
                        help="Limit to a specific profile ID")
    parser.add_argument("--pipeline", action="store_true",
                        help="After bulk pass, run unresolved through full URL pipeline")
    parser.add_argument("--bulk-only", action="store_true", default=True,
                        help="Only use bulk DB lookup (default)")
    parser.add_argument("--retry-not-found", action="store_true",
                        help="Also retry opportunities previously marked not_found")
    parser.add_argument("--limit", type=int, metavar="N",
                        help="Max opportunities to process")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would be updated without writing to DB")
    parser.add_argument("--log-interval", type=int, default=50, metavar="N",
                        help="Log pipeline progress every N orgs (default: 50)")
    parser.add_argument("--catalynx-db", default=str(DEFAULT_CATALYNX_DB),
                        help="Path to catalynx.db")
    parser.add_argument("--intel-db", default=str(DEFAULT_INTEL_DB),
                        help="Path to nonprofit_intelligence.db")
    args = parser.parse_args()

    # If --pipeline is set, disable bulk-only default
    if args.pipeline:
        args.bulk_only = False

    logger.info("=" * 60)
    logger.info("URL Bulk Resolver")
    logger.info("=" * 60)
    logger.info(f"Profile:       {args.profile or 'all'}")
    logger.info(f"Mode:          {'bulk-only' if not args.pipeline else 'bulk + pipeline'}")
    logger.info(f"Retry 404s:    {args.retry_not_found}")
    logger.info(f"Limit:         {args.limit or 'none'}")
    logger.info(f"Dry run:       {args.dry_run}")
    logger.info(f"Catalynx DB:   {args.catalynx_db}")
    logger.info(f"Intel DB:      {args.intel_db}")
    logger.info("=" * 60)

    if not Path(args.catalynx_db).exists():
        logger.error(f"Catalynx DB not found: {args.catalynx_db}")
        sys.exit(1)
    if not Path(args.intel_db).exists():
        logger.error(f"Intel DB not found: {args.intel_db}")
        sys.exit(1)

    # Load opportunities
    opportunities = get_unresolved_opportunities(
        catalynx_db=args.catalynx_db,
        profile_id=args.profile,
        retry_not_found=args.retry_not_found,
        limit=args.limit,
    )

    logger.info(f"Unresolved opportunities to process: {len(opportunities):,}")
    if not opportunities:
        logger.info("Nothing to do.")
        return

    start = time.time()
    bulk_hits = 0
    pipeline_found = 0
    pipeline_not_found = 0

    # --- Bulk DB pass ---
    logger.info(f"\nBulk DB pass ({len(opportunities):,} opportunities)...")
    unresolved, bulk_hits = run_bulk_pass(
        opportunities, args.intel_db, args.catalynx_db, args.dry_run
    )
    logger.info(f"Bulk DB pass complete: {bulk_hits:,} resolved, {len(unresolved):,} remaining")

    # --- Pipeline pass (optional) ---
    if args.pipeline and unresolved:
        logger.info(f"\nPipeline pass ({len(unresolved):,} remaining)...")
        pipeline_found, pipeline_not_found = await run_pipeline_pass(
            unresolved, args.catalynx_db, args.dry_run, args.log_interval
        )

    elapsed = time.time() - start
    total_resolved = bulk_hits + pipeline_found

    logger.info("\n" + "=" * 60)
    logger.info("COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Processed:       {len(opportunities):,}")
    logger.info(f"Bulk DB hits:    {bulk_hits:,}")
    logger.info(f"Pipeline found:  {pipeline_found:,}")
    logger.info(f"Not found:       {pipeline_not_found:,}")
    logger.info(f"Total resolved:  {total_resolved:,}")
    logger.info(f"Time:            {elapsed:.1f}s")
    if args.dry_run:
        logger.info("(DRY RUN — no DB changes made)")


if __name__ == "__main__":
    asyncio.run(main())
