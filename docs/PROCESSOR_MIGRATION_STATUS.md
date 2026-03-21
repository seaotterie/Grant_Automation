# Processor → Tool Migration Status

**Last updated**: 2026-03-21
**Reference**: `docs/TOOL_ARCHITECTURE_MAPPING.md` for full detail

---

## Summary

| Category | Count | Status |
|----------|-------|--------|
| Legacy processors fully replaced by tools | ~35 | ✅ Replaced |
| Processors still active (data collection) | 6 | ⚠️ Keep (no tool equivalent yet) |
| Processors still active (analysis) | 2 | ⚠️ Keep (no tool equivalent yet) |
| Processors removed (dead code) | ~6 | ✅ Removed |

---

## ✅ Replaced — processor functionality now in a tool

| Old processor(s) | Replacement tool | Notes |
|-----------------|-----------------|-------|
| `ai_lite_unified.py`, `ai_heavy_light.py` | Tool 1: `opportunity_screening_tool` | Fast ($0.0004) and thorough ($0.02) modes |
| `ai_heavy_deep.py`, `ai_heavy_researcher.py`, `tier_*.py` (×4) | Tool 2: `deep_intelligence_tool` | Essentials $2 / Premium $8 |
| `financial_scorer.py` | Tool 10: `financial_intelligence_tool` | 15+ metrics, Claude Haiku |
| `risk_assessor.py` | Tool 11: `risk_intelligence_tool` | 6-dimensional risk |
| `board_network_analyzer.py`, `enhanced_network_analyzer.py`, `optimized_network_analyzer.py` | Tool 12: `network_intelligence_tool` | Board network + pathways |
| `schedule_i_processor.py`, `funnel_schedule_i_analyzer.py` | Tool 13: `schedule_i_grant_analyzer_tool` | Foundation grant patterns |
| `data_validator.py` | Tool 16: `data_validator_tool` | Schema + completeness |
| `ein_lookup.py` | Tool 17: `ein_validator_tool` | EIN format + BMF lookup |
| `export_manager.py` | Tool 18: `data_export_tool` | JSON / CSV / Excel / PDF |
| `grant_package_generator.py` | Tool 19: `grant_package_generator_tool` | Application assembly |
| `discovery_scorer.py`, `success_scorer.py` | Tool 20: `multi_dimensional_scorer_tool` | 5-stage dimensional scoring |
| `bmf_filter.py` | Tool 4: `bmf_filter_tool` | IRS BMF filtering |
| `propublica_fetch.py` (legacy) | Tool 7: `form990_propublica_tool` | ProPublica API enrichment |
| Historical analysis portions of tier processors | Tool 22: `historical_funding_analyzer_tool` | USASpending pattern analysis |
| `verification_enhanced_scraper.py` | Tool 25: `web_intelligence_tool` | Scrapy web intelligence |

---

## ⚠️ Still Active — no tool equivalent yet (Phase 9)

These processors remain in `src/processors/` and are still imported by the service layer.
**Do not delete** until replacement tools are built.

### Data Collection (`src/processors/data_collection/`)

| Processor | Purpose | Planned replacement |
|-----------|---------|-------------------|
| `grants_gov_fetch.py` | Grants.gov API pull | Phase 9: Government opportunity tool |
| `usaspending_fetch.py` | USASpending.gov awards | Phase 9: USASpending tool |
| `va_state_grants_fetch.py` | Virginia state grants | Phase 9: State grants tool |
| `propublica_fetch.py` | ProPublica 990 API | Partial: Tool 7 covers enrichment; fetch path still used |
| `foundation_directory_fetch.py` | Foundation Directory API | Phase 9: Foundation directory tool |
| `pdf_downloader.py` | PDF download helper | Shared utility; keep as-is |

### Analysis (`src/processors/analysis/`)

| Processor | Purpose | Planned replacement |
|-----------|---------|-------------------|
| `intelligent_classifier.py` | Opportunity classification | Phase 9: Classification tool |
| `corporate_csr_analyzer.py` | Corporate CSR analysis | Phase 9: Corporate opportunity tool |

---

## ✅ Removed — dead code cleaned up

The following were removed in Phase C of the code review (no live callers):

- `src/_deprecated/` directory (README only, code already gone)
- `src/profiles/_deprecated/` directory
- `src/web/routers/ai_processing.py` (duplicate of ai_endpoints.py)
- ~6 empty modules in `src/web/routers/` and `src/analysis/`

---

## AI Service Migration

| Before | After | Status |
|--------|-------|--------|
| `src/core/openai_service.py` (OpenAI GPT) | `src/core/anthropic_service.py` (Claude) | ⚠️ Both present |
| `openai` SDK | `anthropic` SDK | ✅ New code uses Anthropic |
| GPT-5 models | Haiku (fast) / Sonnet (heavy) / Opus (future) | ✅ Configured |

**Action for Phase 9**: Remove all callers of `openai_service.py`, then delete the file.
Current callers: check with `grep -rn "openai_service\|get_openai_service" src/ --include="*.py"`.

---

## How to migrate a remaining processor to a tool

1. Create `tools/<name>_tool/` with `12factors.toml`, `app/`, `tests/`
2. Inherit from `BaseTool` in `src/core/tool_framework/`
3. Use `get_anthropic_service()` for any AI calls
4. Write tests covering happy path + edge cases
5. Update this document and `docs/TOOL_ARCHITECTURE_MAPPING.md`
6. Remove the processor from `src/processors/` once all callers are updated
