#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Step_04_download_xmls.py:
--------------------------
- Reads EINs and existing 'COMPOSITE_SCORE' values from your scored_nonprofits.csv
- Filters only rows with score >= 0.70
- Skips records whose XML has already been downloaded
- For each remaining EIN, attempts to scrape ProPublica's site to find the latest XML filing via its 'object_id'.
- If successful, downloads the XML via ProPublica's download-xml endpoint and saves it locally (filename prefix: {EIN}_{object_id}.xml).
- Logs XML status in a CSV, allowing your n8n workflow to choose XML first (fallback to PDF if missing or failed).

Assumes the input CSV has headers: EIN, COMPOSITE_SCORE, etc.
"""

import csv
import os
import glob
import requests
from bs4 import BeautifulSoup  # pip install beautifulsoup4
from urllib.parse import urlparse, parse_qs

# ─── Configuration ────────────────────────────────────────────────────────────
INPUT_CSV      = "/data/output/scored_nonprofits.csv"
OUTPUT_CSV     = "/data/output/step4_xml_results.csv"
XML_OUTPUT_DIR = "/data/output/step4_xml"
USER_AGENT     = "python-requests/2.x (+your-email@example.com)"
PROPUBLICA_BASE= "https://projects.propublica.org/nonprofits"

# ensure output directory exists
os.makedirs(XML_OUTPUT_DIR, exist_ok=True)


def find_latest_object_id(ein: str) -> str:
    """
    Scrape the ProPublica org page for the given EIN:
    https://projects.propublica.org/nonprofits/organizations/{EIN}
    Return the first object_id found in an anchor to /download-xml.
    """
    url = f"{PROPUBLICA_BASE}/organizations/{ein}"
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.find_all("a", href=True):
        if "/download-xml?object_id=" in a["href"]:
            query = urlparse(a["href"]).query
            params = parse_qs(query)
            oid = params.get("object_id", [None])[0]
            if oid:
                return oid
    return None


def download_xml(object_id: str) -> bytes:
    """
    Download the raw XML content for the object_id using ProPublica's endpoint.
    Returns XML bytes or raises on failure.
    """
    url = f"{PROPUBLICA_BASE}/download-xml"
    headers = {"User-Agent": USER_AGENT, "Referer": PROPUBLICA_BASE}
    params = {"object_id": object_id}
    resp = requests.get(url, headers=headers, params=params, allow_redirects=True, timeout=30)
    resp.raise_for_status()
    ct = resp.headers.get("Content-Type", "").lower()
    if "xml" not in ct:
        raise RuntimeError(f"Unexpected Content-Type: {ct}")
    return resp.content


def main():
    results = []
    with open(INPUT_CSV, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ein = row.get("EIN", "").strip()
            # parse composite score and filter
            try:
                score = float(row.get("COMPOSITE_SCORE", 0))
            except ValueError:
                score = 0.0
            if score < 0.70:
                print(f"[SKIP] EIN {ein} score {score:.2f} < 0.70")
                row["xml_status"] = "skipped_low_score"
                results.append(row)
                continue

            if not ein:
                row["xml_status"] = "no_ein"
                results.append(row)
                continue

            # Check if any XML already exists for this EIN
            existing_files = glob.glob(os.path.join(XML_OUTPUT_DIR, f"{ein}_*.xml"))
            if existing_files:
                # Use the first match
                fname = os.path.basename(existing_files[0])
                print(f"[SKIP] XML already exists for {ein} -> {fname}")
                row["xml_status"] = "exists"
                row["object_id"] = fname.split("_")[1].rsplit(".xml", 1)[0]
                row["xml_file"] = fname
                results.append(row)
                continue

            try:
                print(f"[INFO] Processing EIN: {ein} (score={score:.2f})")
                oid = find_latest_object_id(ein)
                if not oid:
                    print(f"  → No XML link found for {ein}")
                    row["xml_status"] = "missing"
                    row["object_id"] = ""
                    row["xml_file"] = ""
                else:
                    print(f"  → Found object_id: {oid}")
                    xml_bytes = download_xml(oid)
                    fname = f"{ein}_{oid}.xml"
                    fpath = os.path.join(XML_OUTPUT_DIR, fname)
                    with open(fpath, "wb") as f:
                        f.write(xml_bytes)
                    print(f"  → Saved {len(xml_bytes):,} bytes → {fpath}")
                    row["xml_status"] = "success"
                    row["object_id"] = oid
                    row["xml_file"] = fname
            except Exception as e:
                print(f"  ❌ ERROR ({ein}): {e}")
                row["xml_status"] = "error"
                row["object_id"] = row.get("object_id", "")
                row["xml_file"] = ""

            results.append(row)

    # write results to output CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print(f"[DONE] XML download step complete. Processed {len(results)} rows.")


if __name__ == "__main__":
    main()
