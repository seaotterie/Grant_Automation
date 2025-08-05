import pandas as pd
import os
import json
from datetime import datetime

# ---- CONFIG ----
STEP_KEY = "step1"
STATUS_FILE = "/data/output/workflow_status.json"
LEGACY_STATUS_FILE = "/data/output/status_step_01.json"
INPUT_PATH = '/data/input/eo_va.csv'
OUTPUT_PATH = '/data/output/filtered_nonprofits.csv'
FILTER_CONFIG_PATH = '/data/input/filter_config.json'

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

# ---- BEGIN SCRIPT ----
update_status(STEP_KEY, "running")

# Load IRS BMF file
try:
    bmf = pd.read_csv(INPUT_PATH, dtype=str)
except FileNotFoundError:
    print(f"❌ File not found: {INPUT_PATH}")
    update_status(STEP_KEY, "failed")
    exit(1)

# Load dynamic NTEE filters
target_ntee = ['E31', 'P81', 'W70']  # default fallback
try:
    with open(FILTER_CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
        if "ntee_minor" in config and config["ntee_minor"]:
            target_ntee = config["ntee_minor"]
            print(f"✅ Loaded filter_config.json with NTEE codes: {target_ntee}")
        else:
            print("⚠️ Warning: 'ntee_minor' missing or empty in filter_config.json")
except Exception as e:
    print(f"⚠️ Could not load filter_config.json — using fallback values. Error: {e}")

# Check if NTEE  Codes loaded
with open(FILTER_CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)
    target_ntee = config.get("ntee_codes", [])

# Apply filters
filtered = bmf[
    (bmf['SUBSECTION'] == '03') &
    (bmf['STATUS'] == '01') &
    (bmf['STATE'] == 'VA') &
    (bmf['NTEE_CD'].isin(target_ntee))
]

# Save result
os.makedirs('/data/output', exist_ok=True)
filtered.to_csv(OUTPUT_PATH, index=False)

print(f"✅ Filtered {len(filtered)} nonprofits to {OUTPUT_PATH}")

# ---- STATUS COMPLETE ----
status_log = {
    "status": "complete",
    "timestamp": datetime.utcnow().isoformat(),
    "message": "Step 1 complete: [Pull IRS BMF Records]"
}
with open(LEGACY_STATUS_FILE, "w") as f:
    json.dump(status_log, f, indent=2)

update_status(STEP_KEY, "complete")
