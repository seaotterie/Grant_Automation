#!/usr/bin/env python3
import os
import pandas as pd
import requests
import time
import json
from datetime import datetime

# ─── CONFIG ────────────────────────────────────────────────────────────────────
STEP_KEY = "step4"
STATUS_FILE = "/data/output/workflow_status.json"
LEGACY_STATUS_FILE = "/data/output/status_step_04.json"
CSV_PATH = "/data/output/scored_nonprofits.csv"
OUTPUT_DIR = "/data/output/filings"
LOG_FILE = "/data/output/filing_download_log.json"

# ─── UTILITIES ─────────────────────────────────────────────────────────────────
def update_status(step, status):
    try:
        with open(STATUS_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    data[step] = status
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def download_filing(ein, return_id, output_dir):
    xml_url = f"https://pp-990-xml.s3.us-east-1.amazonaws.com/{return_id}_public.xml"
    pdf_url = f"https://s3.amazonaws.com/irs-form-990/{return_id}_public.pdf"

    xml_path = os.path.join(output_dir, f"{ein}.xml")
    pdf_path = os.path.join(output_dir, f"{ein}.pdf")

    try:
        r = requests.get(xml_url, timeout=10)
        if r.status_code == 200:
            with open(xml_path, "wb") as f:
                f.write(r.content)
            return {"ein": ein, "format": "xml", "status": "downloaded"}
    except Exception as e:
        print(f"[XML] Error for {ein}: {e}")

    try:
        r = requests.get(pdf_url, timeout=10)
        if r.status_code == 200 and "application/pdf" in r.headers.get("Content-Type", ""):
            with open(pdf_path, "wb") as f:
                f.write(r.content)
            return {"ein": ein, "format": "pdf", "status": "downloaded"}
    except Exception as e:
        return {"ein": ein, "format": "pdf", "status": "error", "message": str(e)}

    return {"ein": ein, "status": "not_found"}

# ─── MAIN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    update_status(STEP_KEY, "running")
    print("🚀 Starting filing download step")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        df = pd.read_csv(CSV_PATH, dtype=str)
        df = df[df["COMPOSITE_SCORE"].astype(float) >= 0.70]
    except Exception as e:
        print(f"❌ Failed to load CSV: {e}")
        err = {"status": "error", "message": str(e)}
        with open(LEGACY_STATUS_FILE, "w") as f:
            json.dump(err, f, indent=2)
        update_status(STEP_KEY, "failed")
        exit(1)

    log = []
    for _, row in df.iterrows():
        ein = str(row["EIN"]).zfill(9)
        return_id = str(row.get("OBJECT_ID", "")).strip()  # Expect OBJECT_ID column
        if not return_id:
            print(f"⚠️ Missing OBJECT_ID for EIN {ein}, skipping.")
            log.append({"ein": ein, "status": "missing_return_id"})
            continue

        result = download_filing(ein, return_id, OUTPUT_DIR)
        log.append(result)
        print(f"{result.get('status', 'unknown')} — {ein} ({result.get('format', 'none')})")
        time.sleep(0.2)

    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)
    print(f"✅ Wrote filing download log to {LOG_FILE}")

    status = {
        "status": "complete",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Step 4 complete: [Download XML or PDF Filings]"
    }
    with open(LEGACY_STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)

    update_status(STEP_KEY, "complete")
    print("✅ Step 4 status updated to 'complete'")
