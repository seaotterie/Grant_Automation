"""
IRS 990 XML Offline Bulk Loader

Streams individual 990 XML files from IRS monthly ZIP archives using HTTP
range requests (no full download required). Parses officers, grants, and
financial data, then writes to nonprofit_intelligence.db and catalynx.db.

Run from project root:

    # Dry run — parse only, no DB writes
    python tools/irs_990_bulk_loader/bulk_loader.py --years 2025 --months 1 --dry-run --max-files 200

    # Small live test
    python tools/irs_990_bulk_loader/bulk_loader.py --years 2025 --months 1 --max-files 500

    # Full recommended first load (2024+2025, most recent data)
    python tools/irs_990_bulk_loader/bulk_loader.py --years 2024 2025

    # Incremental new month
    python tools/irs_990_bulk_loader/bulk_loader.py --years 2025 --months 4

    # Full 4-year load (run overnight)
    python tools/irs_990_bulk_loader/bulk_loader.py

Resume is on by default — interrupted runs can be restarted safely.
"""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

import aiohttp

# ---------------------------------------------------------------------------
# Bootstrap project root on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools.irs_990_bulk_loader.zip_streamer import ZipStreamer
from tools.irs_990_bulk_loader.xml_dispatcher import parse_xml_bytes
from tools.irs_990_bulk_loader.db_writer import BulkLoaderDBWriter

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

IRS_ZIP_URL = "https://apps.irs.gov/pub/epostcard/990/xml/{year}/{year}_TEOS_XML_{month:02d}A.zip"

DEFAULT_INTEL_DB    = str(_PROJECT_ROOT / "data" / "nonprofit_intelligence.db")
DEFAULT_CATALYNX_DB = str(_PROJECT_ROOT / "data" / "catalynx.db")

FORM_FILTER_MAP = {
    "990":    {"990"},
    "990-PF": {"990-PF"},
    "990-EZ": {"990-EZ"},
    "all":    {"990", "990-PF", "990-EZ"},
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("bulk_loader")


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

async def process_zip(
    url: str,
    zip_filename: str,
    year: int,
    args,
    writer: BulkLoaderDBWriter,
    deadline: float = None,
    global_remaining: int = None,
) -> dict:
    """
    Stream and process one monthly ZIP. Returns stats dict.
    deadline: epoch time after which we stop (from --max-time).
    global_remaining: max files left from global cap (from --max-total).
    """
    logger.info(f"Starting {zip_filename}")
    start = time.time()

    form_filter = FORM_FILTER_MAP[args.forms]
    ein_filter  = set(args.ein) if args.ein else None

    # Per-batch accumulators
    board_batch   = []
    grant_batch   = []
    fi_batch      = []
    fn_batch      = []
    ei_batch      = []
    website_batch = []

    stats = {"processed": 0, "success": 0, "errors": 0, "skipped_form": 0,
             "officers": 0, "grants": 0, "fi_rows": 0, "websites": 0,
             "stopped_early": False}

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=120, connect=15),
        headers={"User-Agent": "Catalynx Grant Research / IRS 990 Bulk Loader"},
    ) as session:

        # Check URL exists before streaming
        try:
            async with session.head(url) as resp:
                if resp.status == 404:
                    logger.warning(f"ZIP not found (404): {zip_filename} — skipping")
                    return stats
                if resp.status != 200:
                    logger.warning(f"ZIP returned {resp.status}: {zip_filename} — skipping")
                    return stats
        except Exception as e:
            logger.warning(f"ZIP HEAD failed {zip_filename}: {e} — skipping")
            return stats

        streamer = ZipStreamer(url, session, concurrency=args.concurrency)
        total_in_zip = await streamer.get_entry_count()

        async for filename, xml_bytes in streamer.stream_xml_entries():
            stats["processed"] += 1

            # Per-ZIP file cap
            if args.max_files and stats["processed"] > args.max_files:
                stats["stopped_early"] = True
                break

            # Global file cap (across ZIPs)
            if global_remaining is not None and stats["processed"] > global_remaining:
                stats["stopped_early"] = True
                break

            # Time limit
            if deadline and time.time() >= deadline:
                stats["stopped_early"] = True
                break

            try:
                parsed = parse_xml_bytes(xml_bytes)
                if parsed is None:
                    stats["errors"] += 1
                    continue

                # Form type filter
                if parsed["form_type"] not in form_filter:
                    stats["skipped_form"] += 1
                    continue

                # EIN filter
                if ein_filter and parsed.get("ein") not in ein_filter:
                    continue

                ein      = parsed["ein"] or ""
                tax_year = parsed["tax_year"]
                form_type = parsed["form_type"]

                if not ein:
                    stats["errors"] += 1
                    continue

                stats["success"] += 1

                if not args.dry_run:
                    # Board network (all form types)
                    for o in parsed["officers"]:
                        board_batch.append({
                            **o,
                            "ein":             ein,
                            "source_tax_year": tax_year,
                        })
                        stats["officers"] += 1

                    # Grants (990 and 990-PF)
                    if form_type in ("990", "990-PF"):
                        for g in parsed["grants"]:
                            grant_batch.append({
                                **g,
                                "grantor_ein":    ein,
                                "tax_year":       tax_year,
                                "form_type":      form_type,
                                "source_zip_file": zip_filename,
                            })
                        stats["grants"] += len(parsed["grants"])

                    # Foundation intelligence + narratives (990-PF only)
                    if form_type == "990-PF":
                        parsed["grant_count"] = len(parsed["grants"])
                        fi_batch.append(parsed)
                        fn_batch.append(parsed)
                        stats["fi_rows"] += 1

                    # Mission statement for 990/990-EZ filers (INSERT OR IGNORE)
                    if form_type in ("990", "990-EZ") and parsed["narrative"].get("mission_statement"):
                        fn_batch.append(parsed)

                    # ein_intelligence officer merge (all types)
                    if parsed["officers"]:
                        ei_batch.append(parsed)

                    # Website URL (all form types)
                    if parsed.get("website_url"):
                        website_batch.append({
                            "ein":         ein,
                            "website_url": parsed["website_url"],
                            "tax_year":    tax_year,
                        })
                        stats["websites"] += 1

                    # Flush at batch-size threshold
                    if len(board_batch) >= args.batch_size:
                        writer.flush_board_network(board_batch)
                        board_batch = []
                    if len(grant_batch) >= args.batch_size:
                        writer.flush_grants(grant_batch)
                        grant_batch = []
                    if len(fi_batch) >= args.batch_size:
                        writer.flush_foundation_intelligence(fi_batch)
                        fi_batch = []
                    if len(fn_batch) >= args.batch_size:
                        writer.flush_foundation_narratives(fn_batch)
                        fn_batch = []
                    if len(ei_batch) >= args.batch_size:
                        writer.flush_ein_intelligence(ei_batch)
                        ei_batch = []
                    if len(website_batch) >= args.batch_size:
                        writer.flush_organization_websites(website_batch)
                        website_batch = []

            except Exception as e:
                stats["errors"] += 1
                logger.debug(f"Error processing {filename}: {e}")

            # Progress logging
            if stats["processed"] % args.log_interval == 0:
                elapsed = time.time() - start
                rate = stats["processed"] / elapsed if elapsed > 0 else 0
                cap = min(args.max_files, total_in_zip) if args.max_files else total_in_zip
                pct = (stats["processed"] / cap * 100) if cap else 0
                eta_s = ((cap - stats["processed"]) / rate) if rate > 0 and cap > stats["processed"] else 0
                eta_str = f"{eta_s/60:.0f}m" if eta_s > 0 else "—"
                logger.info(
                    f"[{zip_filename}] {stats['processed']:,}/{cap:,} ({pct:.1f}%) | "
                    f"ok={stats['success']:,} err={stats['errors']} | "
                    f"officers={stats['officers']:,} grants={stats['grants']:,} | "
                    f"{rate:.0f} files/s  ETA {eta_str}"
                )

    # Flush remaining batches
    if not args.dry_run:
        if board_batch:   writer.flush_board_network(board_batch)
        if grant_batch:   writer.flush_grants(grant_batch)
        if fi_batch:      writer.flush_foundation_intelligence(fi_batch)
        if fn_batch:      writer.flush_foundation_narratives(fn_batch)
        if ei_batch:      writer.flush_ein_intelligence(ei_batch)
        if website_batch: writer.flush_organization_websites(website_batch)

    elapsed = time.time() - start
    logger.info(
        f"[{zip_filename}] DONE | "
        f"processed={stats['processed']:,} ok={stats['success']:,} "
        f"errors={stats['errors']} | "
        f"officers={stats['officers']:,} grants={stats['grants']:,} "
        f"websites={stats['websites']:,} fi={stats['fi_rows']:,} | "
        f"{elapsed/60:.1f} min"
    )

    if not args.dry_run:
        writer.log_import(
            zip_filename=zip_filename,
            file_type=args.forms,
            tax_year=year,
            processed=stats["processed"],
            success=stats["success"],
            errors=stats["errors"],
            elapsed_seconds=elapsed,
        )

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="IRS 990 XML Offline Bulk Loader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--years", nargs="+", type=int,
        default=[2022, 2023, 2024, 2025],
        metavar="YEAR",
        help="Processing years to load (default: 2022 2023 2024 2025)",
    )
    p.add_argument(
        "--months", nargs="+", type=int,
        default=list(range(1, 13)),
        metavar="MONTH",
        help="Specific months 1-12 (default: all 12)",
    )
    p.add_argument(
        "--forms", choices=["990", "990-PF", "990-EZ", "all"],
        default="all",
        help="Form types to process (default: all)",
    )
    p.add_argument(
        "--concurrency", type=int, default=3,
        help="Simultaneous range requests per ZIP (default: 3)",
    )
    p.add_argument(
        "--batch-size", type=int, default=500,
        dest="batch_size",
        help="DB insert batch size (default: 500)",
    )
    p.add_argument(
        "--intel-db", default=DEFAULT_INTEL_DB,
        dest="intel_db",
        help=f"Path to nonprofit_intelligence.db (default: {DEFAULT_INTEL_DB})",
    )
    p.add_argument(
        "--catalynx-db", default=DEFAULT_CATALYNX_DB,
        dest="catalynx_db",
        help=f"Path to catalynx.db (default: {DEFAULT_CATALYNX_DB})",
    )
    p.add_argument(
        "--resume", action="store_true", default=True,
        help="Skip ZIPs already recorded in data_import_log (default: on)",
    )
    p.add_argument(
        "--no-resume", action="store_false", dest="resume",
        help="Reprocess all ZIPs even if previously logged",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        dest="dry_run",
        help="Parse XML but make no DB writes",
    )
    p.add_argument(
        "--max-files", type=int, default=None,
        dest="max_files",
        help="Stop after N XML files per ZIP (for testing)",
    )
    p.add_argument(
        "--ein", nargs="+",
        help="Only process XML files matching these EINs",
    )
    p.add_argument(
        "--log-interval", type=int, default=100,
        dest="log_interval",
        help="Log progress every N files (default: 100)",
    )
    p.add_argument(
        "--max-total", type=int, default=None,
        dest="max_total",
        help="Stop after N XML files total across all ZIPs (for timed/budgeted runs)",
    )
    p.add_argument(
        "--max-time", type=int, default=None,
        dest="max_time",
        metavar="MINUTES",
        help="Stop gracefully after N minutes (completes current batch before exiting)",
    )
    return p.parse_args()


async def main():
    args = parse_args()

    logger.info("=" * 60)
    logger.info("IRS 990 XML Offline Bulk Loader")
    logger.info("=" * 60)
    logger.info(f"Years:       {args.years}")
    logger.info(f"Months:      {args.months}")
    logger.info(f"Forms:       {args.forms}")
    logger.info(f"Concurrency: {args.concurrency}")
    logger.info(f"Batch size:  {args.batch_size}")
    logger.info(f"Dry run:     {args.dry_run}")
    logger.info(f"Resume:      {args.resume}")
    if args.max_files:
        logger.info(f"Max files:   {args.max_files} per ZIP")
    if args.max_total:
        logger.info(f"Max total:   {args.max_total} files across all ZIPs")
    if args.max_time:
        logger.info(f"Max time:    {args.max_time} minutes")
    if args.ein:
        logger.info(f"EIN filter:  {args.ein}")
    logger.info(f"Intel DB:    {args.intel_db}")
    logger.info(f"Catalynx DB: {args.catalynx_db}")
    logger.info("=" * 60)

    writer = BulkLoaderDBWriter(args.intel_db, args.catalynx_db)

    if not args.dry_run:
        writer.ensure_tables()

    total_stats = {"processed": 0, "success": 0, "errors": 0,
                   "officers": 0, "grants": 0, "fi_rows": 0, "websites": 0,
                   "zips_run": 0, "zips_skipped": 0}
    run_start = time.time()
    deadline  = (run_start + args.max_time * 60) if args.max_time else None
    stopped_early = False

    for year in sorted(args.years):
        if stopped_early:
            break
        for month in sorted(args.months):
            # Time limit check
            if deadline and time.time() >= deadline:
                logger.info(f"Time limit ({args.max_time} min) reached — stopping gracefully")
                stopped_early = True
                break

            # Global file cap check
            if args.max_total and total_stats["processed"] >= args.max_total:
                logger.info(f"Global file cap ({args.max_total}) reached — stopping")
                stopped_early = True
                break

            zip_filename = f"{year}_TEOS_XML_{month:02d}A.zip"
            url = IRS_ZIP_URL.format(year=year, month=month)

            if args.resume and not args.dry_run:
                if writer.is_zip_already_processed(zip_filename):
                    logger.info(f"Skipping {zip_filename} (already processed)")
                    total_stats["zips_skipped"] += 1
                    continue

            try:
                stats = await process_zip(url, zip_filename, year, args, writer,
                                          deadline=deadline,
                                          global_remaining=(args.max_total - total_stats["processed"])
                                          if args.max_total else None)
                for k in ("processed", "success", "errors", "officers", "grants", "fi_rows", "websites"):
                    total_stats[k] += stats.get(k, 0)
                total_stats["zips_run"] += 1
                if stats.get("stopped_early"):
                    stopped_early = True
                    break
            except KeyboardInterrupt:
                logger.info("Interrupted — progress saved, rerun to resume")
                stopped_early = True
                break
            except Exception as e:
                logger.error(f"ZIP processing failed {zip_filename}: {e}")
                total_stats["zips_run"] += 1

    writer.close()

    elapsed = time.time() - run_start
    logger.info("=" * 60)
    logger.info("BULK LOAD COMPLETE")
    logger.info("=" * 60)
    logger.info(f"ZIPs run:    {total_stats['zips_run']} (skipped: {total_stats['zips_skipped']})")
    logger.info(f"XML files:   {total_stats['processed']:,} processed, {total_stats['success']:,} ok, {total_stats['errors']} errors")
    logger.info(f"Officers:    {total_stats['officers']:,}")
    logger.info(f"Grants:      {total_stats['grants']:,}")
    logger.info(f"Websites:    {total_stats['websites']:,}")
    logger.info(f"Foundations: {total_stats['fi_rows']:,}")
    logger.info(f"Total time:  {elapsed/3600:.1f} hours")


if __name__ == "__main__":
    asyncio.run(main())
