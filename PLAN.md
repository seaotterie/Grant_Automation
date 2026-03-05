# Stage-by-Stage Pipeline Review & Optimization Plan

## Executive Summary

After a thorough code review, the core problem is clear: **the AI screening pipeline was never actually connected to AI**. Every scoring function is a placeholder returning hard-coded values or doing simple keyword matching. The BAML prompts are well-designed but never called. This means opportunities have been filtered by crude keyword/geographic checks masquerading as intelligent analysis.

The migration to Claude API is an opportunity to not just fix this, but fundamentally improve the pipeline quality.

---

## Stage-by-Stage Review

### Stage 0: Discovery / Data Sourcing
**Files**: `src/scoring/discovery_scorer.py`, `tools/bmf_filter_tool/`
**What happens**: Opportunities are sourced from Grants.gov, USASpending, foundations, state grants.

**Current problems**:
- Discovery scoring uses base 0.5 score + small increments from NTEE keyword matching
- Score distribution is compressed (everything scores 0.5-0.8) making ranking meaningless
- No semantic understanding of opportunity descriptions vs. org mission
- Geographic matching is exact-string only ("Virginia" won't match "VA")

**Recommendation**:
- Add Claude API call at discovery to do lightweight semantic matching of opportunity descriptions against org mission/programs
- Use `claude-haiku-4-5` here for cost efficiency (~$0.0002/opportunity)
- Return a 1-sentence relevance rationale with each score so humans can see *why*

---

### Stage 1: Fast Screening (200 → ~50)
**File**: `tools/opportunity_screening_tool/app/screening_tool.py` lines 165-215
**BAML prompt**: `tools/opportunity_screening_tool/baml_src/screening.baml` lines 129-174

**Current problems (CRITICAL)**:
- Line 175: `# TODO: Replace with actual BAML AI call` — **AI was never connected**
- `_calculate_strategic_fit_fast()` (line 305-315): Binary keyword match. Returns 0.5 or 0.8, nothing in between
- `_calculate_eligibility_fast()` (line 326-337): Starts at 0.7, subtracts 0.2 for geographic mismatch. That's it.
- `_calculate_timing_score()` (line 347-350): Always returns 0.8. Never checks actual deadlines.
- With these placeholders, every opportunity scores ~0.68-0.75 unless it fails a keyword check
- Proceed gate: `overall >= 0.55 AND eligibility >= 0.70` — the eligibility gate does all the filtering based solely on geography

**What's actually filtering**: Only geographic restrictions. An opportunity in a state not in your `geographic_focus` list gets eligibility 0.5, fails the 0.70 gate, and is rejected regardless of how perfect the strategic fit is.

**Recommendation**:
- Replace placeholder with actual Claude API call using the existing BAML prompt structure
- Use `claude-haiku-4-5` for fast screening (~$0.001/opportunity for ~500 tokens in + ~200 out)
- 200 opportunities × $0.001 = ~$0.20 total (cheaper than current $0.08 estimate)
- The prompt already exists in screening.baml — it's well-designed, just never called
- **Key change**: Lower eligibility gate to 0.50 (let AI nuance handle it, not a binary check)
- Add `reasoning` field to output so you can see why each opportunity scored as it did

---

### Stage 2: Thorough Screening (50 → 10-15)
**File**: `tools/opportunity_screening_tool/app/screening_tool.py` lines 245-301
**BAML prompt**: `tools/opportunity_screening_tool/baml_src/screening.baml` lines 176-273

**Current problems (CRITICAL)**:
- Line 255: `# TODO: Replace with actual BAML AI call` — also never connected
- ALL five scoring functions return hard-coded values:
  - `_calculate_strategic_fit_thorough()` → always 0.75
  - `_calculate_eligibility_thorough()` → always 0.85
  - `_calculate_timing_score()` → always 0.80
  - `_calculate_financial_score()` → always 0.70
  - `_calculate_competition_score()` → always 0.60
- With these constants, EVERY opportunity gets the same score: 0.755
- Proceed gate: `overall >= 0.60 AND eligibility >= 0.75` — every opportunity passes (0.755 > 0.60, 0.85 > 0.75)
- Since all score 0.755, the "top 15" is arbitrary (first 15 encountered)

**The contradiction**: Fast screening filters aggressively by geography. Thorough screening accepts everything that reaches it. The pipeline is: geographic filter → pass everything → done. No intelligence at all.

**Recommendation**:
- Use `claude-sonnet-4-6` for thorough screening (~$0.01/opportunity)
- 50 opportunities × $0.01 = ~$0.50 total
- **Critical addition**: Send the actual opportunity description/RFP text, not just metadata
- Use Anthropic's PDF skill to extract text from RFP PDFs when available
- Add funder research context (past recipients, typical grants) from your 990/Schedule I data
- This is where Claude's longer context window and reasoning shine over simple scoring

---

### Stage 3: Human Gateway (Currently Missing)
**Spec**: `src/workflows/HUMAN_GATEWAY_SPEC.md`

**Current status**: Designed but not implemented. The 10-15 recommendations from Stage 2 have nowhere to go except manual JSON file review.

**This is your highest-impact gap**. Even with perfect AI scoring, a human review step is essential because:
- AI can't know your current organizational priorities, board preferences, or political context
- Some opportunities are worth pursuing despite low scores (relationship building, strategic positioning)
- Some high-scoring opportunities are wrong for reasons AI can't see (bad history with funder, mission drift)

**Recommendation**:
- Build a simple review UI (or even a CLI tool) that presents the 10-15 with scores, rationale, and a pass/reject/maybe interface
- For "maybe" items, allow the user to request a quick Claude analysis of a specific concern
- This doesn't need to be fancy — even a well-formatted terminal output with y/n prompts would work

---

### Stage 4: Deep Intelligence (10 → Final Recommendations)
**File**: `tools/deep_intelligence_tool/app/depth_handlers.py`
**BAML prompt**: `tools/deep_intelligence_tool/baml_src/intelligence.baml`

**Current problems**:
- Depth handlers have placeholder analysis with fallback values when BAML fails
- BAML client is a stub (`NotImplementedError`)
- The multi-step workflow (validate → parse 990 → financial intel → network intel → deep analysis → risk → package) is well-architected but the central AI step is hollow
- Proceed gate: `overall >= 0.65 AND risk != CRITICAL` — threshold is *higher* than screening, meaning the deep analysis can reject opportunities that screening approved

**What works well**:
- The workflow YAML (`deep_intelligence.yaml`) is excellent architecture
- Supporting tools (financial, network, risk, Schedule I) are operational with real logic
- The multi-tool orchestration concept is sound

**Recommendation**:
- Use `claude-sonnet-4-6` for deep intelligence (best reasoning/cost balance)
- Feed the supporting tool outputs (financial metrics, network data, 990 data) as context to the Claude call
- Use Anthropic PDF skill to ingest actual RFP/NOFO documents — this is a game-changer
- For Premium tier, use `claude-opus-4-6` for the strategic consulting analysis
- **Remove the proceed gate at this stage** — by the time you've paid for deep analysis, let the human decide whether to proceed. Present the analysis with honest scores, don't auto-reject.

---

## Cross-Cutting Issues

### 1. Threshold Creep (Opportunities dying by a thousand cuts)
Current thresholds compound across stages:
```
Discovery:  base 0.5 + increments → must be "interesting enough" to surface
Fast:       overall >= 0.55 AND eligibility >= 0.70
Thorough:   overall >= 0.60 AND eligibility >= 0.75  (STRICTER)
Deep:       overall >= 0.65 AND risk != CRITICAL      (EVEN STRICTER)
```

Each stage raises the bar. An opportunity scoring 0.54 in fast screening is gone forever, even though with proper analysis it might score 0.85.

**Fix**: Invert the logic. Early stages should be PERMISSIVE (cast a wide net). Later stages should be INFORMATIVE (give you data to decide), not RESTRICTIVE (auto-reject).

Proposed:
```
Fast:       overall >= 0.40 (broad net, let AI sort it)
Thorough:   overall >= 0.50 (refinement, not rejection)
Deep:       NO auto-reject (present findings, human decides)
```

### 2. No Semantic Understanding
The current system matches keywords and NTEE codes. "Youth development" won't match "adolescent empowerment programs." "Community health" won't match "public wellness initiatives." Claude solves this inherently.

### 3. Missing RFP/NOFO Document Analysis
Grant opportunities are defined by their Request for Proposals. Your system only looks at metadata (title, funder, amount, deadline). The actual requirements, priorities, and evaluation criteria are in the documents.

**This is where Anthropic's PDF capability is transformative**: Feed the actual NOFO PDF to Claude and ask "Given this organization's profile, analyze the fit."

### 4. No Learning Loop
The system doesn't track which opportunities were pursued, which resulted in awards, and which were rejected. This means scoring can never improve.

---

## Implementation Plan

### Phase A: Claude API Integration (Foundation)
1. Create `src/core/anthropic_service.py` — async Claude API client (mirror structure of openai_service.py)
2. Update `.env` with `ANTHROPIC_API_KEY`
3. Update cost tracker to use Claude model pricing
4. Create a model routing config: haiku for fast, sonnet for thorough/deep, opus for premium

### Phase B: Activate Fast Screening AI (Biggest Bang for Buck)
1. Replace placeholder in `_screen_fast_single()` with Claude haiku call
2. Use the existing BAML prompt structure (screening.baml lines 134-173) as the prompt template
3. Parse structured JSON response into OpportunityScore
4. Lower the proceed threshold to 0.40
5. Add `reasoning` field to output

### Phase C: Activate Thorough Screening AI
1. Replace placeholder in `_screen_thorough_single()` with Claude sonnet call
2. Enrich context: pull 990 data and Schedule I data for the funder before calling AI
3. Add PDF ingestion for opportunities that have NOFO documents
4. Lower proceed threshold to 0.50
5. Add funder intelligence from your existing foundation/990-PF data

### Phase D: Activate Deep Intelligence AI
1. Connect Claude sonnet to the deep analysis handlers
2. Feed all supporting tool outputs as structured context
3. Add PDF skill for full NOFO analysis
4. Remove auto-reject threshold — present analysis for human decision
5. For Premium tier, use Claude opus

### Phase E: Human Gateway (Simple First Version)
1. Build a CLI or simple web view that shows screened opportunities with scores and rationale
2. Allow pass/reject/investigate actions
3. "Investigate" triggers a targeted Claude query about a specific concern
4. Track decisions for future learning

### Phase F: Quality & Learning Loop
1. Add outcome tracking (pursued, awarded, rejected, why)
2. Use historical outcomes to calibrate scoring weights
3. Generate periodic "what did we miss" reports comparing rejected opportunities against outcomes

---

## Cost Projections (Claude API)

| Stage | Model | Per-Opp Cost | Batch Cost (200 opps) |
|-------|-------|-------------|----------------------|
| Fast Screening | claude-haiku-4-5 | ~$0.001 | ~$0.20 |
| Thorough Screening | claude-sonnet-4-6 | ~$0.01 | ~$0.50 (50 opps) |
| Deep Intelligence (Essentials) | claude-sonnet-4-6 | ~$0.05 | ~$0.50 (10 opps) |
| Deep Intelligence (Premium) | claude-opus-4-6 | ~$0.20 | ~$2.00 (10 opps) |
| **Total Pipeline** | | | **~$1.20 - $3.20** |

This is significantly cheaper than the original GPT-5 estimates and delivers much better reasoning quality.

---

## Priority Order

1. **Phase A** — Claude API integration (unblocks everything)
2. **Phase B** — Fast screening AI (fixes the biggest quality gap)
3. **Phase C** — Thorough screening with PDF ingestion (the differentiator)
4. **Phase E** — Human gateway (even a simple version changes everything)
5. **Phase D** — Deep intelligence AI (builds on C)
6. **Phase F** — Learning loop (long-term improvement)
