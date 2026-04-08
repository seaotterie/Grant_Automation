"""
IRS 990 XML Offline Bulk Loader

Downloads full IRS monthly ZIP archives, extracts XML files locally, parses
officers, grants, website URLs, and financial data, then writes to
nonprofit_intelligence.db and catalynx.db. ZIP is deleted after processing.

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

    # Custom temp directory for downloaded ZIPs
    python tools/irs_990_bulk_loader/bulk_loader.py --temp-dir D:/tmp

Resume is on by default — interrupted runs can be restarted safely.
"""

import argparse
import asyncio
import logging
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import aiohttp

# ---------------------------------------------------------------------------
# Bootstrap project root on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

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

DOWNLOAD_CHUNK_SIZE = 4 * 1024 * 1024   # 4 MB chunks
LOG_DOWNLOAD_EVERY  = 10                 # log download progress every N %

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
# Download helper
# ---------------------------------------------------------------------------

async def _download_zip(
    url: str,
    zip_filename: str,
    session: aiohttp.ClientSession,
    temp_dir: Path,
) -> Path:
    """
    Download a ZIP file to temp_dir with progress logging.
    Returns the local path. Raises on HTTP error.
    """
    zip_path = temp_dir / zip_filename
    dl_start = time.time()
    last_pct_logged = -1

    async with session.get(url) as resp:
        resp.raise_for_status()
        total_bytes = int(resp.headers.get("Content-Length", 0))
        downloaded  = 0

        if total_bytes:
            logger.info(
                f"Downloading {zip_filename} ({total_bytes / 1e6:.0f} MB) → {zip_path}"
            )
        else:
            logger.info(f"Downloading {zip_filename} (size unknown) → {zip_path}")

        with open(zip_path, "wb") as fh:
            async for chunk in resp.content.iter_chunked(DOWNLOAD_CHUNK_SIZE):
                fh.write(chunk)
                downloaded += len(chunk)

                if total_bytes:
                    pct = int(downloaded / total_bytes * 100)
                    bucket = (pct // LOG_DOWNLOAD_EVERY) * LOG_DOWNLOAD_EVERY
                    if bucket > last_pct_logged:
                        elapsed = time.time() - dl_start
                        rate_mb = downloaded / 1e6 / elapsed if elapsed > 0 else 0
                        logger.info(
                            f"  {zip_filename}: {pct}%  "
                            f"({downloaded/1e6:.0f}/{total_bytes/1e6:.0f} MB  "
                            f"{rate_mb:.1f} MB/s)"
                        )
                        last_pct_logged = bucket

    elapsed = time.time() - dl_start
    size_mb = zip_path.stat().st_size / 1e6
    logger.info(
        f"Download complete: {zip_filename}  {size_mb:.0f} MB  "
        f"in {elapsed:.1f}s  ({size_mb/elapsed:.1f} MB/s)"
    )
    return zip_path


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
    Download, extract, and process one monthly ZIP. Returns stats dict.
    The ZIP file is deleted from disk after processing.
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

    temp_dir = Path(args.temp_dir) if args.temp_dir else Path(tempfile.gettempdir()) / "irs_bulk_loader"
    temp_dir.mkdir(parents=True, exist_ok=True)
    zip_path = None

    try:
        # ------------------------------------------------------------------
        # 1. Download ZIP
        # ------------------------------------------------------------------
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=None, connect=30, sock_read=120),
            headers={"User-Agent": "Catalynx Grant Research / IRS 990 Bulk Loader"},
        ) as session:

            # HEAD check first (fast 404 detection)
            try:
                async with session.head(url) as resp:
                    if resp.status == 404:
                        logger.warning(f"ZIP not found (404): {zip_filename} — skipping")
                        return stats
                    if resp.status not in (200, 405):   # 405 = HEAD not allowed, try GET anyway
                        logger.warning(f"ZIP HEAD returned {resp.status}: {zip_filename} — skipping")
                        return stats
            except Exception as e:
                logger.warning(f"ZIP HEAD failed {zip_filename}: {e} — skipping")
                return stats

            zip_path = await _download_zip(url, zip_filename, session, temp_dir)

        # ------------------------------------------------------------------
        # 2. Process extracted XML entries (synchronous, local I/O)
        # ------------------------------------------------------------------
        with zipfile.ZipFile(zip_path, "r") as zf:
            xml_entries = [e for e in zf.infolist() if e.filename.lower().endswith(".xml")]
            total_in_zip = len(xml_entries)
            logger.info(f"Extracted {total_in_zip:,} XML entries from {zip_filename}")

            for entry in xml_entries:
                filename = entry.filename
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
                    xml_bytes = zf.read(entry)
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

                    ein       = parsed["ein"] or ""
                    tax_year  = parsed["tax_year"]
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
                                    "grantor_ein":     ein,
                                    "tax_year":        tax_year,
                                    "form_type":       form_type,
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
                            writer.flush_board_network(board_batch);   board_batch = []
                        if len(grant_batch) >= args.batch_size:
                            writer.flush_grants(grant_batch);           grant_batch = []
                        if len(fi_batch) >= args.batch_size:
                            writer.flush_foundation_intelligence(fi_batch); fi_batch = []
                        if len(fn_batch) >= args.batch_size:
                            writer.flush_foundation_narratives(fn_batch);   fn_batch = []
                        if len(ei_batch) >= args.batch_size:
                            writer.flush_ein_intelligence(ei_batch);    ei_batch = []
                        if len(website_batch) >= args.batch_size:
                            writer.flush_organization_websites(website_batch); website_batch = []

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

    finally:
        # ------------------------------------------------------------------
        # 3. Delete ZIP regardless of success/failure
        # ------------------------------------------------------------------
        if zip_path and zip_path.exists():
            try:
                zip_path.unlink()
                logger.info(f"Deleted {zip_path.name} ({zip_path.stat().st_size / 1e6:.0f} MB freed)" if zip_path.exists() else f"Deleted {zip_path.name}")
            except Exception as e:
                logger.warning(f"Could not delete {zip_path}: {e}")

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
        "--temp-dir", default=None,
        dest="temp_dir",
        metavar="DIR",
        help="Directory for temporary ZIP downloads (default: system temp)",
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
        "--log-interval", type=int, default=500,
        dest="log_interval",
        help="Log progress every N files (default: 500)",
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
        help="Stop gracefully after N minutes (completes current ZIP before exiting)",
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
    logger.info(f"Batch size:  {args.batch_size}")
    logger.info(f"Dry run:     {args.dry_run}")
    logger.info(f"Resume:      {args.resume}")
    temp_display = args.temp_dir or f"{tempfile.gettempdir()}/irs_bulk_loader"
    logger.info(f"Temp dir:    {temp_display}")
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
