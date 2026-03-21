# TODO / FIXME Triage (Phase E5)

Triage performed: 2026-03-21
Total markers found: 39

---

## Category A — Future work (keep, no immediate action)

These are valid future-work markers. They should stay as reminders but don't block any current functionality.

| File | Line | Note |
|------|------|------|
| `src/analytics/foundation_network_graph.py` | 197 | Integrate with BMF filter tool — future sprint |
| `src/auth/jwt_auth.py` | 246 | API key DB validation — depends on D1 (JWT re-enable) |
| `src/scoring/ntee_scorer.py` | 443 | Enhance with Tool 25 web intelligence — future sprint |
| `src/scoring/schedule_i_voting.py` | 445, 454 | BMF DB query — already works via CSV fallback |
| `src/scoring/triage_queue.py` | 126 | DB persistence for history — future sprint |
| `src/utils/ein_resolution.py` | 387, 410, 420 | Replace CSV BMF lookup with SQL — future sprint |
| `src/web/routers/workflows.py` | 23 | Persist in-memory workflow state to DB — future sprint |
| `tools/deep_intelligence_tool/app/depth_handlers.py` | 62, 263, 316, 365, 517, 603, 822 | Replace stubs with BAML AI calls — intentional placeholders |
| `tools/financial_intelligence_tool/app/financial_tool.py` | 105, 494 | BAML AI call placeholder — works without AI enhancement |
| `tools/foundation_grantee_bundling_tool/app/bundling_tool.py` | 154, 288, 354 | XML 990-PF auto-fetch and data enrichment — future sprint |
| `tools/foundation_grantee_bundling_tool/app/cofunding_analyzer.py` | 198, 402, 403, 404 | Geographic/funding enrichment — future sprint |
| `tools/foundation_preprocessing_tool/app/foundation_preprocessor.py` | 837 | Board member cross-reference — future sprint |
| `tools/risk_intelligence_tool/app/risk_tool.py` | 597 | BAML AI call placeholder — functions without it |
| `tools/web_intelligence_tool/app/scrapy_pipelines/structured_output_pipeline.py` | 176, 180 | OpportunityIntelligence / FoundationIntelligence conversion — future sprint |

## Category B — Endpoint Stubs (exposed as 501, implement in a future sprint)

These represent unfinished endpoints. They currently return HTTP 501 or use placeholder data.
They are **known** and should not be silently removed — they mark where real implementation is needed.

| File | Lines | Endpoint | Status |
|------|-------|----------|--------|
| `src/web/routers/opportunities.py` | 721–724 | `POST /{opportunity_id}/batch-web-research` (single-opp path) | Returns 501 — Scrapy integration pending |
| `src/web/routers/intelligence.py` | 339 | Deep intelligence analysis route | Uses placeholder org/opportunity data |
| `src/web/routers/profiles_v2.py` | 1623 | BMF discovery + Web Intelligence step 4 | Web Intelligence step omitted (comment explains why) |

**Future action**: Implement the Scrapy web research step in the single-opportunity endpoint using the existing `Web Intelligence Tool` (Tool 25), matching the batch implementation in `batch-web-research`.

## Summary

| Category | Count | Action |
|----------|-------|--------|
| A — Future work, keep | 30 | No change needed |
| B — Endpoint stubs | 9 | Implement in a future sprint |

No TODO/FIXME markers were found to be incorrect, misleading, or hiding bugs.
The `opportunities.py` 501 endpoint is the highest-priority item as it is user-visible.
