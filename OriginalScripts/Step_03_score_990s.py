#!/usr/bin/env python3
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

# Test Print file has been moded
print("🟢 RUNNING UPDATED SCRIPT: v2 with NaN check after df assignment")


# ─── CONFIG ────────────────────────────────────────────────────────────────────
STEP_KEY         = "step3"
STATUS_FILE      = "/data/output/workflow_status.json"
LEGACY_STATUS_FILE = "/data/output/status_step_03.json"
BMF_CSV_PATH     = "/data/output/filtered_nonprofits.csv"
JSON_DIR         = "/data/990s_propublica/"
OUTPUT_PATH      = "/data/output/scored_nonprofits.csv"

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def update_status(step, status):
    try:
        with open(STATUS_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    data[step] = status
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def safe_divide(n, d): return n/d if d else 0.0
def scale_log(x):      return np.log1p(x)/15.0
def extract_num(f, keys):
    for k in keys:
        if k in f:
            try: return float(f[k])
            except: return 0.0
    return 0.0

# ─── START STATUS ─────────────────────────────────────────────────────────────
update_status(STEP_KEY, "running")

# ─── LOAD & NORMALIZE BMF METADATA ───────────────────────────────────────────────
try:
    bmf = pd.read_csv(BMF_CSV_PATH, dtype=str)
except Exception as e:
    print(f"❌ Failed to load BMF CSV: {e}")
    update_status(STEP_KEY, "failed")
    exit(1)

bmf = bmf.rename(columns={
    "NTEE_CD":           "NTEE_CODE",
    "SUBSECTION":        "SUBSECTION_CODE",
    "ASSET_CD":          "ASSET_CODE",
    "INCOME_CD":         "INCOME_CODE",
    "PF_FILING_REQ_CD":  "PF_F"
})
bmf["EIN"] = bmf["EIN"].str.zfill(9)

scored, skipped = [], []

# ─── SCORING LOOP ──────────────────────────────────────────────────────────────
for _, row in bmf.iterrows():
    ein, name = row["EIN"], row.get("NAME","")
    state, ntee, pf = row.get("STATE",""), row.get("NTEE_CODE",""), row.get("PF_F","")
    jsn = os.path.join(JSON_DIR, f"{ein}.json")
    if not os.path.exists(jsn):
        skipped.append(ein); continue
    try:
        data = json.load(open(jsn))
        filings = [f for f in data.get("filings",[]) if isinstance(f.get("tax_prd_yr"),int)]
    except:
        skipped.append(ein); continue
    if not filings:
        skipped.append(ein); continue

    filings.sort(key=lambda x: x["tax_prd_yr"], reverse=True)
    latest, recent5 = filings[0], filings[:5]
    pdf_url = next((f.get("pdf_url","") for f in filings if f.get("pdf_url")), "")

    revs  = [extract_num(f,["totrevenue","totrevnue"]) for f in recent5]
    asts  = [extract_num(f,["totassetsend","totnetassetend"]) for f in recent5]
    pexp  = [extract_num(f,["totfuncexpns","totexpns"]) for f in recent5]
    texp  = pexp
    if not any(revs) or not any(asts):
        skipped.append(ein); continue

    avg_rev = np.mean(revs)
    avg_ast = np.mean(asts)
    avg_prog_ratio = np.mean([safe_divide(p,t) for p,t in zip(pexp,texp)])
    cons = len({f["tax_prd_yr"] for f in recent5})/5.0
    rec  = max(0.0, 1.0 - 0.2 * (2024 - latest["tax_prd_yr"]))
    pf_score = 1 if pf!="1" else 0
    state_score = 1 if state=="VA" else 0
    ntee_score = 1 if str(ntee).startswith("P") else 0
    fin_score = np.mean([scale_log(avg_rev),scale_log(avg_ast)])

    comp = (
        0.10*rec +
        0.10*cons +
        0.20*fin_score +
        0.15*avg_prog_ratio +
        0.10*pf_score +
        0.10*state_score +
        0.15*ntee_score
    )

    scored.append({
        "EIN": ein,
        "NAME": name,
        "NTEE_CODE": ntee,
        "STATE": state,
        "MOST_RECENT_YEAR": latest["tax_prd_yr"],
        "AVG_REVENUE": avg_rev,
        "AVG_ASSETS": avg_ast,
        "AVG_PROGRAM_RATIO": avg_prog_ratio,
        "FILING_CONSISTENCY_SCORE": cons,
        "FILING_RECENCY_SCORE": rec,
        "EFFICIENCY_SCORE": avg_prog_ratio,
        "FINANCIAL_SCORE": fin_score,
        "PF_SCORE": pf_score,
        "STATE_SCORE": state_score,
        "NTEE_SCORE": ntee_score,
        "COMPOSITE_SCORE": comp,
        "PDF_URL": pdf_url
    })

# ─── PARTIAL SCORES FOR SKIPPED ─────────────────────────────────────────────────
partials = []
for ein in skipped:
    row = bmf[bmf["EIN"]==ein].iloc[0]
    state_score = 1 if row["STATE"]=="VA" else 0
    ntee_score  = 1 if str(row["NTEE_CODE"]).startswith("P") else 0
    pf_score    = 1 if row["PF_F"]!="1" else 0
    comp = 0.10*pf_score + 0.10*state_score + 0.15*ntee_score
    partials.append({
        "EIN": ein,
        "NAME": row.get("NAME",""),
        "NTEE_CODE": row["NTEE_CODE"],
        "STATE": row["STATE"],
        "MOST_RECENT_YEAR": "",
        "AVG_REVENUE": 0,
        "AVG_ASSETS": 0,
        "AVG_PROGRAM_RATIO": 0,
        "FILING_CONSISTENCY_SCORE": 0,
        "FILING_RECENCY_SCORE": 0,
        "EFFICIENCY_SCORE": 0,
        "FINANCIAL_SCORE": 0,
        "PF_SCORE": pf_score,
        "STATE_SCORE": state_score,
        "NTEE_SCORE": ntee_score,
        "COMPOSITE_SCORE": comp,
        "PDF_URL": ""
    })

# ─── COMBINE, RANK & SAVE ────────────────────────────────────────────────────────
df = pd.DataFrame(scored + partials)

# Check for NaNs in COMPOSITE_SCORE
nan_rows = df[df["COMPOSITE_SCORE"].isna()]
if not nan_rows.empty:
    print("🚨 Found NaNs in COMPOSITE_SCORE:")
    print(nan_rows[["EIN", "NAME", "COMPOSITE_SCORE"]])
    print(f"Total NaN rows: {len(nan_rows)}")
    nan_rows.to_csv("/data/output/debug_nan_scores.csv", index=False)

# Remove rows with missing scores to avoid rank error
df = df[df["COMPOSITE_SCORE"].notna()]
df["SCORE_RANK"] = df["COMPOSITE_SCORE"].rank(method="dense", ascending=False).astype(int)
df.sort_values("COMPOSITE_SCORE", ascending=False, inplace=True)

# Save to output
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False)
print(f"✅ Scored {len(scored)} + {len(partials)} partial → {OUTPUT_PATH}")


# ─── COMBINE, RANK & SAVE ────────────────────────────────────────────────────────
df = pd.DataFrame(scored + partials)

# Check for NaNs in COMPOSITE_SCORE
nan_rows = df[df["COMPOSITE_SCORE"].isna()]
if not nan_rows.empty:
    print("🚨 Found NaNs in COMPOSITE_SCORE:")
    print(nan_rows[["EIN", "NAME", "COMPOSITE_SCORE"]])
    print(f"Total NaN rows: {len(nan_rows)}")
    nan_rows.to_csv("/data/output/debug_nan_scores.csv", index=False)

# Remove rows with missing scores to avoid rank error
df = df[df["COMPOSITE_SCORE"].notna()]
df["SCORE_RANK"] = df["COMPOSITE_SCORE"].rank(method="dense",ascending=False).astype(int)
df.sort_values("COMPOSITE_SCORE", ascending=False, inplace=True)

# Save to output
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False)
print(f"✅ Scored {len(scored)} + {len(partials)} partial → {OUTPUT_PATH}")

# ─── FINAL STATUS WRITE ─────────────────────────────────────────────────────────
status = {
    "status": "complete",
    "timestamp": datetime.utcnow().isoformat(),
    "message": "Step 3 complete: [Score for Initial Down Select]"
}
with open(LEGACY_STATUS_FILE, "w") as f:
    json.dump(status, f, indent=2)

update_status(STEP_KEY, "complete")
