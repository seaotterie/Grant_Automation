#!/usr/bin/env python3
import pandas as pd
import requests
import os
import json
from datetime import datetime

# ---- CONFIG ----
STEP_KEY = "step2"
STATUS_FILE = "/data/output/workflow_status.json"
LEGACY_STATUS_FILE = "/data/output/status_step_02.json"
FILTERED_CSV = "/data/output/filtered_nonprofits.csv"
OUTPUT_DIR = "/data/990s_propublica"

# ---- UTILITIES ----
def update_status(step, status):
    try:
        with open(STATUS_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    data[step] = status
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_result(output_dir, ein, result):
    filename = os.path.join(output_dir, f"{ein}.json")
    try:
        with open(filename, "w") as f:
            json.dump(result, f, indent=2)
        print(f"✅ Saved result for {ein}: {result.get('status')}")
    except Exception as e:
        print(f"⚠️ Failed to write result for {ein}: {e}")

# ---- MAIN ----
def main():
    update_status(STEP_KEY, "running")
    print("🚀 Starting ProPublica VA downloader")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load filtered nonprofits and EIN list
    try:
        df = pd.read_csv(FILTERED_CSV, dtype=str)
        eins = set(df['EIN'].str.zfill(9))
        print(f"🔢 EINs to process: {eins}")
    except Exception as e:
        print(f"❌ Failed to read filtered CSV: {e}")
        update_status(STEP_KEY, "failed")
        return

    for ein in eins:
        json_path = os.path.join(OUTPUT_DIR, f"{ein}.json")
        if os.path.exists(json_path):
            print(f"⏭️ Skipping existing JSON for {ein}")
            continue

        result = {"ein": ein}
        org_url = f"https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"

        try:
            resp = requests.get(org_url, headers={"User-Agent": "Mozilla/5.0"})
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Request failed: {e}"
            save_result(OUTPUT_DIR, ein, result)
            continue

        if resp.status_code == 404:
            result["status"] = "not_found"
            result["message"] = "No record found for this EIN"
            save_result(OUTPUT_DIR, ein, result)
            continue
        elif resp.status_code != 200:
            result["status"] = "error"
            result["message"] = f"HTTP {resp.status_code}"
            save_result(OUTPUT_DIR, ein, result)
            continue

        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            result["status"] = "error"
            result["message"] = f"Invalid JSON: {e}"
            save_result(OUTPUT_DIR, ein, result)
            continue

        filings_with_data = data.get("filings_with_data", [])
        filings_without_data = data.get("filings_without_data", [])
        filings = filings_with_data + filings_without_data

        if not filings:
            result["status"] = "no_filings"
            result["filings"] = []
            save_result(OUTPUT_DIR, ein, result)
            continue

        result["status"] = "success"
        result["filings"] = filings

        save_result(OUTPUT_DIR, ein, result)

    # WRITE STATUS
    status = {
        "status": "complete",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Step 2 complete: [Pull ProPublica Records]"
    }
    with open(LEGACY_STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)

    update_status(STEP_KEY, "complete")
    print("✅ Step 2 status updated to 'complete'")

# ---- RUN ----
if __name__ == "__main__":
    main()
