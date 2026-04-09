# Grant Opportunity Pipeline: Redesign Plan
## 100 Top Candidates → Top 10 for a Profile

---

## 1. Current vs. Proposed — Step-by-Step Comparison

| Step | Current Process | Proposed Process | Status | Why It Changes |
|------|----------------|------------------|--------|----------------|
| **0. Profile signals** | *Not explicit — profile fields passed raw into discovery queries* | Extract keywords, NTEE neighbors, geo scope, ask range as structured signals | **NEW** | Cleaner signal generation used by both the DB query and AI prompts |
| **1. Foundation discovery** | `NonprofitDiscoverer`: BMF query by NTEE code + geography → orgs that *look like* funders | **Primary**: `BehavioralDiscovery` — `foundation_grants` query → orgs that *have actually funded* similar work. **Secondary (optional checkbox)**: existing BMF/NTEE geographic search as a supplemental source | **MODIFIED** | Behavioral evidence is the stronger signal; BMF search kept as a user-selectable supplement to catch funders not yet in the grants table |
| **2. Government discovery** | `GovernmentDiscoverer`: SAM.gov + grants.gov + federal DB queries | Placeholder — coming in a future phase | **PLANNED** | Federal grants are a separate track; will be built out separately |
| **3. Commercial/State discovery** | `CommercialDiscoverer` + `StateDiscoverer`: CSR programs, state portals | Placeholder — coming in a future phase | **PLANNED** | Corporate and state grant tracks will be built out separately |
| **4. Result pool** | ~200 orgs from all 4 tracks combined | 500–1,000 orgs from foundation_grants + public charity grants query | **EXPANDED** | Larger pre-AI pool is fine because Stage 5 scoring is free — no AI budget consumed yet |
| **5. Algorithmic pre-scoring** | *Does not exist* — all 200 go to AI with equal priority | Score 500–1,000 on grant amount alignment, recency, keyword density, payout health → cut to top 200 | **NEW** | Zero-cost ranking means AI only runs on the most promising 200 |
| **6. URL resolution** | 6-stage cascade (org_websites lookup → ProPublica → DuckDuckGo → Haiku predictor) | Same 6-stage cascade — no change | **UNCHANGED** | Pipeline is already optimized; 73% hit rate from fast-path DB lookup |
| **7. Fast Haiku screening** | Tool 1 fast mode on ~200 orgs; context = profile only | Tool 1 fast mode on top-200 pre-scored orgs; context = profile + grant history summary | **MODIFIED** | Same tool, better input — Haiku now sees actual past grants, not just org name/type |
| **8. Top 100 milestone** | *Not explicit* — ~50 survivors pass to thorough screen | Explicit output: ~100 candidates at score ≥ 0.55 | **FORMALIZED** | The 100→10 funnel becomes a tracked, reportable stage |
| **9. Batch 990 PDF enrichment** | Happens *after* human gateway (post-selection) | Moved to *before* thorough screen — runs on top 100 automatically | **MOVED EARLIER** | Thorough Sonnet screen is 50× more expensive; give it the full picture first |
| **10. Web intelligence enrichment** | Triggered manually per org from GUI | Runs automatically for top 100 orgs missing `web_data` in `ein_intelligence` cache | **MOVED EARLIER** | Same reason — Sonnet needs full context before evaluating |
| **11. Thorough Sonnet screening** | Tool 1 thorough mode on ~50 survivors; minimal context | Tool 1 thorough mode on 100 fully-enriched candidates; context = grants + 990 + website | **MODIFIED** | Bigger input pool, but now fully enriched — better quality decisions at same per-unit cost |
| **12. Top 10 output** | 10–15 candidates from thorough screen; no explicit ranking | Explicit top-10 ranked by thorough screen score + pre-score combined | **FORMALIZED** | Clear deliverable; scoring is transparent and auditable |
| **13. Human gateway** | Required step between thorough screen and Deep Intelligence | Optional review step after top 10 are identified (not a hard blocker) | **REPOSITIONED** | Human confirms the final 10 rather than manually selecting from 50 — less cognitive load |
| **14. Deep Intelligence** | Tool 2: $0.75–$42/org on human-selected ~10 | Tool 2: same tool, same tiers — no change | **UNCHANGED** | Already well-designed for this stage |

---

## 2. Cost Comparison (Per Profile Run)

| Stage | Current Cost | Proposed Cost | Delta |
|-------|-------------|---------------|-------|
| Discovery | $0.00 (SQL) | $0.00 (SQL) | — |
| Algorithmic scoring | $0.00 (none exists) | $0.00 | — |
| URL resolution | ~$0.05 | ~$0.10 (larger pool before cut to 200) | +$0.05 |
| Fast screening | $0.08 (200 × $0.0004) | $0.08 (200 × $0.0004) | — |
| 990 + web enrichment (before thorough) | $0.00 (done after human gate) | ~$1.50 (100 orgs, most cached) | +$1.50 |
| Thorough screening | $1.00 (50 × $0.02) | $2.00 (100 × $0.02) | +$1.00 |
| **Total to Top 10** | **~$1.13** | **~$3.68** | **+$2.55** |

The extra $2.55 buys: (1) Sonnet seeing full 990 + website context on 2× as many candidates, and (2) algorithmic pre-scoring eliminating random noise from the input pool. The top 10 output is substantially more reliable.

---

## 3. Core Insight: Lead with Behavioral Evidence

**Current approach:** "Which orgs match our profile characteristics?" → broad BMF search → AI filter

**Proposed approach:** "Which funders have already proven they fund things like us?" → `foundation_grants` query → algorithmic rank → AI confirm

The `foundation_grants` table (Schedule I + 990-PF Part XV, extracted from IRS bulk XML) is the key asset. A foundation that gave $50K to a youth education program in California last year is a near-certain match candidate for a California youth education nonprofit — no AI needed to recognize that signal.

The existing BMF/NTEE geographic search is kept as an **optional supplemental source** (user-selectable checkbox) to catch funders whose grants haven't yet been loaded into the database.

---

## 4. Proposed Funnel — Stage Detail

### Stage 0 — Profile Signal Extraction (Free, instant)
Parse the seeking org's profile into matching signals:
- Keyword list (from `focus_areas`, `program_areas`, `target_populations`, `mission_statement`)
- NTEE codes + neighboring codes (one level up/lateral)
- Geographic scope (states or national/international)
- Funding ask range (min/max grant size sought)
- Organization type and eligibility markers

---

### Stage 1 — Behavioral Discovery (Free, <1s) → 500–1,000 orgs

**Primary: foundation_grants query**
```sql
SELECT grantor_ein,
       COUNT(*)                              AS grant_count,
       AVG(grant_amount)                    AS avg_grant,
       MAX(tax_year)                         AS last_active,
       GROUP_CONCAT(DISTINCT grant_purpose)  AS purposes
FROM   foundation_grants
WHERE  grant_purpose LIKE '%{keyword}%'        -- profile keywords (OR across all keywords)
  AND  tax_year >= 2022                        -- active in last 3 years
  AND  grant_amount BETWEEN {min_ask} AND {max_ask * 3}
GROUP  BY grantor_ein
HAVING grant_count >= 1
```
JOIN `bmf_organizations` (name, state, status) + `form990_financials` (grants_paid, assets_fmv).

**Secondary (optional checkbox): existing BMF/NTEE geographic search**
- Runs `NonprofitDiscoverer` as before
- Results merged into the pool; duplicates deduplicated by EIN

**Public charity grants track:**
- `form990_financials WHERE grants_paid > threshold AND ntee proximity match`

---

### Stage 2 — Algorithmic Pre-Scoring (Free, <200ms) → Top 200

Score each candidate using zero-cost database signals:

| Signal | Weight | Source |
|--------|--------|--------|
| Grant amount alignment (% of grants in our ask range) | 25% | `foundation_grants` |
| Geographic alignment (local/state/national match) | 20% | `bmf_organizations` + `foundation_grants.recipient_state` |
| Keyword density (# of our keywords in grant purposes) | 15% | `foundation_grants.grant_purpose` |
| Recency (weighted: 2024 > 2023 > 2022) | 15% | `foundation_grants.tax_year` |
| Grant frequency (consistent annual vs one-time) | 15% | `foundation_grants` aggregates |
| Financial payout health (grants_paid / assets ratio) | 10% | `form990_financials` |

Sort descending, take top 200. **No AI, no network calls — pure database math.**

---

### Stage 3 — URL Resolution (Near-Free, <30s)

For the top 200 (existing 6-stage cascade, unchanged):
1. `organization_websites` table lookup (bulk-loaded, FREE — ~80% hit rate)
2. `ein_intelligence.web_data` cache check (FREE)
3. ProPublica JSON + multi-year 990 consolidation
4. DuckDuckGo + Wikidata public APIs
5. Haiku URL predictor (only for top-ranked orgs still missing URLs)

Expected cost: ~$0.05–0.15 total.

---

### Stage 4 — Fast Haiku Screening (Tool 1) → **Top 100** ($0.08)

- Tool 1 fast mode on 200 pre-scored candidates
- Context now includes: grant history summary (actual past grants, amounts, purposes)
- Haiku evaluates: strategic fit, eligibility, timing
- Threshold: score ≥ 0.55 AND eligibility ≥ 0.70
- Cost: 200 × $0.0004 = **$0.08**
- **Output: Top 100 candidates**

---

### Stage 5 — Batch 990 + Web Enrichment (Low Cost, batched)

For the 100 survivors — **run before thorough screen, not after:**
- Batch 990 PDF analysis (`PDFNarrativeExtractor`, `batch-analyze-990-pdfs`, Semaphore(3))
  — extracts: grant strategy, eligibility restrictions, deadlines, focus areas
- Haiku web intelligence (Tool 25) for any org missing `web_data` in `ein_intelligence` cache
- All results cached in `ein_intelligence` (`web_data` + `pdf_analyses`)

Cost: ~$0.50–2.00 (most will be cache hits after the first run per funder).

---

### Stage 6 — Thorough Sonnet Screening (Tool 1) → **Top 10** ($2.00)

Tool 1 thorough mode on the 100, now with full context:
- Actual grant history (Stage 1)
- Financial data (Stage 2)
- Website intelligence (Stage 5)
- 990 PDF narratives (Stage 5)

Sonnet evaluates 5 dimensions:
| Dimension | Weight |
|-----------|--------|
| Strategic fit | 35% |
| Eligibility | 25% |
| Timing | 15% |
| Financial | 15% |
| Competition | 10% |

Threshold: score ≥ 0.60 AND eligibility ≥ 0.75
Cost: 100 × $0.02 = **$2.00**
**Output: Top 10 candidates, explicitly ranked.**

---

### Stage 7 — Human Review (Optional)

Human confirms the top 10 rather than selecting from 50.
Not a hard blocker — can proceed to Deep Intelligence automatically if confidence is high.

---

### Stage 8 — Deep Intelligence (Tool 2, Unchanged)

$0.75–$7.50 per org (Quick → Standard tier) on the final 10.
Full dossier: financial intelligence, risk, network, historical funding, cultivation strategy.

---

## 5. What Needs to Be Built

### New: `BehavioralDiscoveryEngine`
- File: `src/discovery/behavioral_discoverer.py` (or `tools/behavioral_discovery_tool/`)
- Queries `foundation_grants` + `form990_financials` + `bmf_organizations`
- Returns `List[DiscoveredOpportunity]` with pre-computed signals attached
- Optional: merges with `NonprofitDiscoverer` results when BMF checkbox is enabled

### New: Algorithmic Pre-Scorer
- File: `src/discovery/pre_scorer.py` or inline in `BehavioralDiscoveryEngine`
- Pure SQL/Python; no AI calls
- Produces a `pre_score` float (0–1) stored on each `DiscoveredOpportunity`
- Runs in <200ms for 1,000 candidates

### Modified: `_run_batch_screen()` in `src/web/routers/opportunities.py`
- Accept pre-scored candidates as input
- Pass `grant_history_summary` as funder_intelligence context
  (hook already exists via `build_from_ein_intelligence()` in `tools/shared_schemas/grant_funder_intelligence.py`)

### Modified: Frontend Pipeline Card (`src/web/static/index.html`)
- Add "Find Funders" step (behavioral discovery) before "Find URLs"
- Show funnel counts at each stage (e.g., "847 found → 200 scored → 100 screened → 10 top")
- Optional checkbox: "Also search by NTEE/geography (BMF)"

---

## 6. What Already Exists (Reuse As-Is)

| Component | File | Notes |
|-----------|------|-------|
| Fast/Thorough screening | `tools/opportunity_screening_tool/` | No changes needed |
| Batch 990 PDF analysis | `src/web/routers/opportunities.py` (`batch-analyze-990-pdfs`) | No changes needed |
| Web intelligence (Haiku) | `tools/web_intelligence_tool/` | No changes needed |
| URL resolution cascade | `src/database/database_manager.py` | No changes needed |
| `build_from_ein_intelligence()` | `tools/shared_schemas/grant_funder_intelligence.py` | Context injection hook already wired |
| Multi-dimensional scorer | `tools/multi_dimensional_scorer_tool/` | Call for DISCOVER stage weights |
| `ein_intelligence` caching | `src/database/database_manager.py` | No changes needed |
| `foundation_grants` table | `data/nonprofit_intelligence.db` | Populated by bulk loader — ready to query |
| `form990_financials` table | `data/nonprofit_intelligence.db` | Populated by bulk loader — ready to query |
| `organization_websites` table | `data/nonprofit_intelligence.db` | Populated by bulk loader — ready to query |

---

## 7. Verification Checklist

- [ ] Run behavioral discovery against one test profile → confirm 500–1,000 results with plausible grant matches
- [ ] Run algorithmic scoring → confirm top 200 have meaningfully higher keyword/geo alignment than bottom 200
- [ ] Run fast screening → confirm ~100 survive at score ≥ 0.55
- [ ] Confirm batch 990 + web enrichment completes for 100 orgs before thorough screen begins
- [ ] Run thorough screening → confirm top 10 have eligibility ≥ 0.75 and represent credible matches
- [ ] Spot-check: manually review 5 of the top 10 — do their actual 990 grant histories confirm the match?
- [ ] Confirm cost per run ≤ $4.00 for stages 0–6
