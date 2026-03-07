# Plan: Screening Filter for AI Pipeline Down-Selection

## Problem
The SCREENING tab currently shows 560 opportunities for the Free Clinic profile. Running all 560 through the AI enrichment pipeline (web research, 990 analysis, Tool 1 screening) is inefficient and costly. We need a smart filtering mechanism to select a manageable subset before AI processing.

## Current State
- **560 opportunities** loaded with algorithmic scores (overall_score 0-1.0)
- **4 category buckets**: qualified (≥0.75), review (0.65-0.75), consider (0.50-0.65), low_priority (<0.50)
- **AI Pipeline steps**: ① URL Search ($0) → ② Web Research ($0.01/ea) → ③ 990 Search ($0) → ④ AI Screen ($0.001-0.01/ea)
- **Existing filters**: category tabs, "skip low priority" checkbox, score threshold for batch screening
- **Missing**: No way to strategically select a subset for the AI pipeline; currently all-or-nothing

## Proposed Solution: "Plan Screening Filter" — A Multi-Strategy Selection Panel

Add a **Plan Screening Filter** panel between the discovery results and the AI Enrichment Pipeline. This panel provides 3 complementary strategies to down-select opportunities before committing to AI processing.

### Strategy 1: Score-Based Tier Filter (Default)
**What**: Filter by algorithmic score tiers with a configurable threshold slider.
- Slider from 0.0 to 1.0 (default: 0.65) showing live count of opportunities that pass
- Quick presets: "Top 25" / "Top 50" / "Qualified Only" / "All Above Review"
- Shows estimated cost for the filtered set

**Implementation**:
- Add `planScreeningThreshold` state (default 0.65) and `planScreeningMaxCount` state (default 50)
- Add `getPlanFilteredOpportunities()` computed that returns opportunities above threshold, capped at maxCount
- Live count badge: "42 of 560 selected — Est. $0.42"

### Strategy 2: Score + Data Enrichment Priority
**What**: Prioritize opportunities that have the most/least existing data, so AI budget is spent wisely.
- "Score highest, least data" — high-scoring opps that lack web data, 990 analysis (best ROI)
- "Score highest, most data" — high-scoring opps already enriched (cheapest to complete)
- Shows data completeness indicators per opportunity

**Implementation**:
- Add `planScreeningSortStrategy` state: 'score_desc' | 'score_data_gap' | 'score_data_rich'
- `score_data_gap` sorts by: score DESC, then by missing data fields ASC (URL missing, web data missing, 990 missing)
- Helps users target AI budget where it creates the most value

### Strategy 3: Batch Size Limiter
**What**: Hard cap on how many opportunities proceed to AI processing.
- Dropdown/input: 10 / 25 / 50 / 100 / Custom
- Combined with score threshold: "Top 50 above 0.60"
- Cost estimator updates in real-time

**Implementation**:
- Add `planScreeningBatchSize` state (default 50)
- Cost calculator: `batchSize × costPerStep` for each pipeline step
- Warning when batch size > 100: "Large batch — consider using Score filter first"

---

## Implementation Plan

### Step 1: Add State & Logic to `screening-module.js`
Add new state variables and filtering methods:
```
planScreeningEnabled: false,
planScreeningThreshold: 0.65,
planScreeningBatchSize: 50,
planScreeningSortStrategy: 'score_desc',
```

Add methods:
- `getPlanFilteredCount()` — returns count of opps passing current filter
- `getPlanFilteredIds()` — returns IDs of filtered opportunities
- `getPlanEstimatedCost()` — calculates cost for filtered set across pipeline steps
- `applyPlanFilter()` — applies the filter, updating which opportunities the AI pipeline buttons act on

### Step 2: Add Filter Panel UI to `index.html`
Insert a collapsible "Plan Screening Filter" card between the summary counts row and the AI Enrichment Pipeline card. Contains:
- Score threshold slider with live count
- Batch size selector
- Sort strategy toggle
- Cost estimate display
- "Apply Filter" button that constrains AI pipeline scope

### Step 3: Wire AI Pipeline Buttons to Use Filtered Set
Modify `discoverAllUrls()`, `searchAll990s()`, `screenAllUnscreened()` to operate on the filtered subset rather than all `discoveryResults`:
- Add `getAIPipelineTargets()` method that returns `planScreeningEnabled ? getPlanFilteredIds() : allIds`
- Each pipeline step uses this method instead of iterating all results

### Step 4: Add Visual Indicators
- Badge on each opportunity card showing if it's "in plan" or "filtered out"
- Summary bar: "Showing 42 of 560 | Est. AI cost: $0.42 | Score ≥ 0.65"
- Dim/grey out filtered-out opportunities in the grid (still visible, just de-emphasized)

---

## Files Modified

1. **`src/web/static/modules/screening-module.js`** — New state, filtering logic, cost estimator, modified pipeline methods
2. **`src/web/static/index.html`** — New filter panel UI between summary and AI pipeline card
3. **`src/web/routers/opportunities.py`** — No backend changes needed (filtering is client-side on already-loaded data)

## Cost Impact
- **Before**: 560 × $0.01 = $5.60 per pipeline step (web research + AI screen)
- **After (Top 50)**: 50 × $0.01 = $0.50 per step — **90% cost reduction**
- **After (Qualified only, ~80)**: 80 × $0.01 = $0.80 per step — **86% cost reduction**

## No Backend Changes Required
All filtering happens client-side on the already-loaded `discoveryResults` array. The existing batch endpoints already accept an array of `opportunity_ids`, so we just pass fewer IDs.
