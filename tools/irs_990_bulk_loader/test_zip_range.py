"""
Test: IRS TEOS XML ZIP range-request extraction

Validates the full pipeline:
  1. Fetch ZIP central directory via HTTP range (no full download)
  2. Stream individual XML files via range request
  3. Parse officer data (Part VII / 990-PF / 990-EZ)
  4. Insert into board_network_index in nonprofit_intelligence.db

Run from project root:
    python tools/irs_990_bulk_loader/test_zip_range.py
"""

import asyncio
import sqlite3
import struct
import xml.etree.ElementTree as ET
import zlib
from datetime import datetime, timezone
from pathlib import Path

import aiohttp

# ── Config ────────────────────────────────────────────────────────────────────

# One monthly ZIP as the test target (~99MB, but we download <2MB total)
TEST_ZIP_URL = "https://apps.irs.gov/pub/epostcard/990/xml/2024/2024_TEOS_XML_01A.zip"

# How many XML files to sample from the ZIP
SAMPLE_SIZE = 10

DB_PATH = Path(__file__).parent.parent.parent / "data" / "nonprofit_intelligence.db"


# ── ZIP range helpers ─────────────────────────────────────────────────────────

async def get_file_size(session: aiohttp.ClientSession, url: str) -> int:
    async with session.head(url) as resp:
        return int(resp.headers["Content-Length"])


async def fetch_range(session: aiohttp.ClientSession, url: str, start: int, end: int) -> bytes:
    headers = {"Range": f"bytes={start}-{end}"}
    async with session.get(url, headers=headers) as resp:
        return await resp.read()


async def read_central_directory(session: aiohttp.ClientSession, url: str, total_size: int):
    """
    Read the ZIP central directory via two range requests:
      1. Last 65KB to find the End-of-Central-Directory record
      2. The central directory itself
    Returns list of file entry dicts.
    """
    # 1. Fetch tail to find EOCD
    tail_size = min(65536 + 22, total_size)
    tail = await fetch_range(session, url, total_size - tail_size, total_size - 1)

    eocd_pos = tail.rfind(b"PK\x05\x06")
    if eocd_pos == -1:
        raise ValueError("EOCD signature not found — not a valid ZIP?")
    eocd = tail[eocd_pos:]

    cd_size   = struct.unpack_from("<I", eocd, 12)[0]
    cd_offset = struct.unpack_from("<I", eocd, 16)[0]

    print(f"  Central directory: {cd_size:,} bytes at offset {cd_offset:,}")

    # 2. Fetch central directory
    cd_data = await fetch_range(session, url, cd_offset, cd_offset + cd_size - 1)

    # 3. Parse entries
    entries = []
    pos = 0
    while pos < len(cd_data):
        if cd_data[pos : pos + 4] != b"PK\x01\x02":
            break
        compress_method    = struct.unpack_from("<H", cd_data, pos + 10)[0]
        compressed_size    = struct.unpack_from("<I", cd_data, pos + 20)[0]
        uncompressed_size  = struct.unpack_from("<I", cd_data, pos + 24)[0]
        fname_len          = struct.unpack_from("<H", cd_data, pos + 28)[0]
        extra_len          = struct.unpack_from("<H", cd_data, pos + 30)[0]
        comment_len        = struct.unpack_from("<H", cd_data, pos + 32)[0]
        local_hdr_offset   = struct.unpack_from("<I", cd_data, pos + 42)[0]
        fname = cd_data[pos + 46 : pos + 46 + fname_len].decode("utf-8", errors="replace")

        if fname.lower().endswith(".xml"):
            entries.append({
                "name": fname,
                "compress_method": compress_method,
                "compressed_size": compressed_size,
                "uncompressed_size": uncompressed_size,
                "local_hdr_offset": local_hdr_offset,
            })

        pos += 46 + fname_len + extra_len + comment_len

    return entries


async def download_xml_from_zip(
    session: aiohttp.ClientSession, url: str, entry: dict
) -> bytes:
    """Range-request a single XML file out of the ZIP."""
    # Read local file header to get actual data offset
    lh_start = entry["local_hdr_offset"]
    lh_header = await fetch_range(session, url, lh_start, lh_start + 29)

    fname_len = struct.unpack_from("<H", lh_header, 26)[0]
    extra_len = struct.unpack_from("<H", lh_header, 28)[0]
    data_start = lh_start + 30 + fname_len + extra_len
    data_end   = data_start + entry["compressed_size"] - 1

    compressed = await fetch_range(session, url, data_start, data_end)

    if entry["compress_method"] == 8:   # deflate
        return zlib.decompress(compressed, -15)
    return compressed                   # stored (method 0)


# ── XML parsing ───────────────────────────────────────────────────────────────

def extract_from_xml(xml_bytes: bytes) -> dict:
    """
    Parse a 990 XML file and return:
      { "ein": str, "tax_year": int|None, "officers": [{"name", "title"}] }
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        return {"ein": None, "tax_year": None, "officers": [], "error": str(e)}

    ns  = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
    pfx = f"{{{ns}}}" if ns else ""

    # EIN
    ein = (
        root.findtext(f".//{pfx}EIN")
        or root.findtext(".//EIN")
        or ""
    ).strip().replace("-", "")

    # Tax year (TaxPeriodEndDt or TaxYear)
    tax_year = None
    for tag in (f"{pfx}TaxPeriodEndDt", "TaxPeriodEndDt", f"{pfx}TaxYr", "TaxYr"):
        val = root.findtext(f".//{tag}", "").strip()
        if val:
            try:
                tax_year = int(val[:4])
            except ValueError:
                pass
            break

    officers = []
    seen = set()

    def add(name, title):
        name = name.strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            officers.append({"name": name, "title": (title or "").strip() or None})

    # 990 Part VII-A
    for grp in root.iter(f"{pfx}Form990PartVIISectionAGrp"):
        add(
            grp.findtext(f"{pfx}PersonNm") or grp.findtext("PersonNm") or "",
            grp.findtext(f"{pfx}TitleTxt") or grp.findtext("TitleTxt") or "",
        )

    # 990-PF Part VIII
    for grp in root.iter(f"{pfx}OfficerDirTrstKeyEmplGrp"):
        name = (
            grp.findtext(f"{pfx}PersonNm")
            or grp.findtext("PersonNm")
            or grp.findtext(f"{pfx}BusinessNameLine1Txt")
            or grp.findtext("BusinessNameLine1Txt")
            or ""
        )
        add(name, grp.findtext(f"{pfx}TitleTxt") or grp.findtext("TitleTxt") or "")

    # 990-EZ Part IV
    for grp in root.iter(f"{pfx}OfficerDirectorTrusteeKeyEmplGrp"):
        add(
            grp.findtext(f"{pfx}PersonFullNm") or grp.findtext("PersonFullNm") or "",
            grp.findtext(f"{pfx}TitleTxt") or grp.findtext("TitleTxt") or "",
        )

    return {"ein": ein or None, "tax_year": tax_year, "officers": officers}


# ── DB helpers ────────────────────────────────────────────────────────────────

def ensure_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS board_network_index (
            normalized_name  TEXT NOT NULL,
            ein              TEXT NOT NULL,
            title            TEXT,
            compensation     REAL,
            source_tax_year  INTEGER,
            created_at       TEXT NOT NULL,
            PRIMARY KEY (normalized_name, ein)
        )
    """)
    conn.commit()


def insert_officers(conn: sqlite3.Connection, ein: str, tax_year, officers: list) -> int:
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    for o in officers:
        normalized = o["name"].lower().strip()
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO board_network_index
                    (normalized_name, ein, title, compensation, source_tax_year, created_at)
                VALUES (?, ?, ?, NULL, ?, ?)
                """,
                (normalized, ein, o["title"], tax_year, now),
            )
            inserted += conn.execute(
                "SELECT changes()"
            ).fetchone()[0]
        except sqlite3.Error:
            pass
    conn.commit()
    return inserted


# ── Main test ─────────────────────────────────────────────────────────────────

async def main():
    print(f"\n{'='*60}")
    print("IRS ZIP Range-Request Test")
    print(f"{'='*60}")
    print(f"URL:     {TEST_ZIP_URL}")
    print(f"Sample:  {SAMPLE_SIZE} XML files")
    print(f"DB:      {DB_PATH}\n")

    conn = sqlite3.connect(DB_PATH)
    ensure_table(conn)
    rows_before = conn.execute("SELECT COUNT(*) FROM board_network_index").fetchone()[0]

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=60),
        headers={"User-Agent": "Grant Research Automation Tool"},
    ) as session:

        # Step 1: File size
        total_size = await get_file_size(session, TEST_ZIP_URL)
        print(f"Step 1: ZIP size = {total_size/1e6:.1f} MB")

        # Step 2: Central directory
        print("Step 2: Reading central directory...")
        entries = await read_central_directory(session, TEST_ZIP_URL, total_size)
        print(f"  Found {len(entries):,} XML files in ZIP")

        if not entries:
            print("ERROR: No XML files found in central directory.")
            return

        # Step 3: Sample + download
        sample = entries[:SAMPLE_SIZE]
        print(f"\nStep 3: Downloading {len(sample)} sample XML files...")

        total_downloaded = 0
        total_officers   = 0
        total_inserted   = 0
        eins_seen        = set()
        parse_errors     = 0

        for i, entry in enumerate(sample, 1):
            try:
                xml_bytes = await download_xml_from_zip(session, TEST_ZIP_URL, entry)
                total_downloaded += len(xml_bytes)

                result = extract_from_xml(xml_bytes)

                if result.get("error"):
                    parse_errors += 1
                    print(f"  [{i:2}] PARSE ERROR: {entry['name']}: {result['error']}")
                    continue

                ein      = result["ein"] or "unknown"
                tax_year = result["tax_year"]
                officers = result["officers"]

                if ein not in eins_seen:
                    eins_seen.add(ein)

                n_inserted = 0
                if ein != "unknown" and officers:
                    n_inserted = insert_officers(conn, ein, tax_year, officers)
                    total_inserted += n_inserted

                total_officers += len(officers)

                print(
                    f"  [{i:2}] {entry['name'][:40]:<40} "
                    f"EIN={ein}  year={tax_year}  "
                    f"officers={len(officers)}  inserted={n_inserted}"
                )

            except Exception as e:
                parse_errors += 1
                print(f"  [{i:2}] ERROR {entry['name']}: {e}")

    # Step 4: Summary
    rows_after = conn.execute("SELECT COUNT(*) FROM board_network_index").fetchone()[0]
    conn.close()

    print(f"\n{'='*60}")
    print("Results")
    print(f"{'='*60}")
    print(f"XML files processed : {len(sample)}")
    print(f"Parse errors        : {parse_errors}")
    print(f"Total downloaded    : {total_downloaded/1e3:.1f} KB")
    print(f"Unique EINs         : {len(eins_seen)}")
    print(f"Total officers found: {total_officers}")
    print(f"Rows inserted (new) : {total_inserted}")
    print(f"board_network_index : {rows_before} -> {rows_after} rows")

    # Step 5: Sample query — show what Stage 2 would see
    if rows_after > 0:
        conn2 = sqlite3.connect(DB_PATH)
        conn2.row_factory = sqlite3.Row
        sample_ein = conn2.execute(
            "SELECT DISTINCT ein FROM board_network_index LIMIT 1"
        ).fetchone()["ein"]
        officers_for_ein = conn2.execute(
            "SELECT normalized_name, title FROM board_network_index WHERE ein = ?",
            (sample_ein,),
        ).fetchall()
        conn2.close()

        print(f"\nStage 2 query test — EIN {sample_ein}:")
        for row in officers_for_ein:
            print(f"  {row['normalized_name']:<30}  {row['title']}")

    print("\nTest complete.")


if __name__ == "__main__":
    asyncio.run(main())
