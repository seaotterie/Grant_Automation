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
PDF_OUTPUT_DIR = "/data/output/pdfs"
LOG_FILE = "/data/output/pdf_download_log.json"

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

# ─── MAIN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    update_status(STEP_KEY, "running")
    print("🚀 Starting PDF download step")

    os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

    # load scored nonprofits
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

    download_log = []
    for _, row in df.iterrows():
        ein = str(row["EIN"]).zfill(9)
        url = f"https://s3.amazonaws.com/irs-form-990/{ein}_2022_public.pdf"
        local_path = os.path.join(PDF_OUTPUT_DIR, f"{ein}.pdf")
        result = {"ein": ein}

        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200 and "application/pdf" in r.headers.get("Content-Type", ""):
                with open(local_path, "wb") as f:
                    f.write(r.content)
                result["status"] = "downloaded"
                print(f"✅ Downloaded: {ein}")
            else:
                result["status"] = "not_found"
                print(f"❌ Not found or invalid format: {ein}")
        except Exception as e:
            result["status"] = "error"
            result["message"] = str(e)
            print(f"⚠️ Error downloading {ein}: {e}")

        download_log.append(result)
        time.sleep(0.2)

    # write download log
    with open(LOG_FILE, "w") as f:
        json.dump(download_log, f, indent=2)
    print(f"✅ Wrote download log to {LOG_FILE}")

    # write legacy status
    status = {
        "status": "complete",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Step 4 complete: [Download PDFs]"
    }
    with open(LEGACY_STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)

    update_status(STEP_KEY, "complete")
    print("✅ Step 4 status updated to 'complete'")
