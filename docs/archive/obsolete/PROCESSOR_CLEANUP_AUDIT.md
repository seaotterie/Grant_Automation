# Processor Cleanup Audit - 12-Factor Transformation

**Audit Date**: 2025-10-05
**Total Legacy Processors**: 45 files (excluding __init__.py)
**Status**: Cleanup Phase - Tools Complete, Processors Not Yet Deprecated

---

## Overview

The 12-factor transformation successfully created 24 operational tools. However, **45 legacy processor files remain** in `src/processors/` that should be deprecated or removed. This audit categorizes each processor by migration status.

---

## Category 1: ✅ READY TO DEPRECATE (Has Tool Equivalent)

### Analysis Processors (15 files)

| Processor File | Tool Equivalent | Status | Notes |
|---------------|-----------------|--------|-------|
| `ai_lite_unified_processor.py` | Tool 10 (Opportunity Screening - fast mode) | ✅ Replace | Mentioned in migration docs |
| `ai_heavy_light_analyzer.py` | Tool 10 (Opportunity Screening - thorough mode) | ✅ Replace | Mentioned in migration docs |
| `ai_heavy_deep_researcher.py` | Tool 11 (Deep Intelligence) | ✅ Replace | Mentioned in migration docs |
| `ai_heavy_researcher.py` | Tool 11 (Deep Intelligence) | ✅ Replace | Mentioned in migration docs |
| `financial_scorer.py` | Tool 12 (Financial Intelligence) | ✅ Replace | Mentioned in migration docs |
| `risk_assessor.py` | Tool 13 (Risk Intelligence) | ✅ Replace | Mentioned in migration docs |
| `board_network_analyzer.py` | Tool 14 (Network Intelligence) | ✅ Replace | Mentioned in migration docs |
| `enhanced_network_analyzer.py` | Tool 14 (Network Intelligence) | ✅ Replace | Features merged into tool |
| `schedule_i_processor.py` | Tool 15 (Schedule I Grant Analyzer) | ✅ Replace | Mentioned in migration docs |
| `funnel_schedule_i_analyzer.py` | Tool 15 (Schedule I Grant Analyzer) | ✅ Replace | Features merged into tool |
| `grant_package_generator.py` | Tool 19 (Grant Package Generator) | ✅ Replace | Mentioned in migration docs |
| `government_opportunity_scorer.py` | Tool 20 (Multi-Dimensional Scorer) | ✅ Replace | Discovery stage scoring |
| `deterministic_scoring_engine.py` | Tool 20 (Multi-Dimensional Scorer) | ✅ Replace | Algorithmic scoring logic |
| `fact_extraction_prompts.py` | Tool 11 (Deep Intelligence) | ✅ Replace | Prompts now in tool |
| `optimized_analysis_orchestrator.py` | Workflow Engine | ✅ Replace | Replaced by src/workflows/ |

**Subtotal**: 15 processors → Move to `_deprecated/`

### Filtering Processors (2 files)

| Processor File | Tool Equivalent | Status | Notes |
|---------------|-----------------|--------|-------|
| `bmf_filter.py` | Tool 4 (BMF Filter) | ✅ Replace | Mentioned in migration docs |
| `enhanced_bmf_filter.py` | Tool 4 (BMF Filter) | ✅ Replace | Enhanced version merged |

**Subtotal**: 2 processors → Move to `_deprecated/`

### Lookup Processors (1 file)

| Processor File | Tool Equivalent | Status | Notes |
|---------------|-----------------|--------|-------|
| `ein_lookup.py` | Tool 17 (EIN Validator) | ✅ Replace | Mentioned in migration docs |

**Subtotal**: 1 processor → Move to `_deprecated/`

### Export/Reports Processors (2 files)

| Processor File | Tool Equivalent | Status | Notes |
|---------------|-----------------|--------|-------|
| `export_processor.py` | Tool 18 (Data Export) | ✅ Replace | Multi-format export |
| `report_generator.py` | Tool 21 (Report Generator) | ✅ Replace | Professional templates |

**Subtotal**: 2 processors → Move to `_deprecated/`

### **Category 1 Total: 20 processors ready to deprecate**

---

## Category 2: 🔍 NEEDS INVESTIGATION (Uncertain Status)

### Analysis Processors (10 files)

| Processor File | Potential Tool | Status | Action Needed |
|---------------|----------------|--------|---------------|
| `ai_heavy_research_bridge.py` | Tool 11? | 🔍 Check | Bridge between old processors - likely deprecated |
| `ai_service_manager.py` | Core service | 🔍 Check | May be used by tools, or replaced by core/openai_service.py |
| `enhanced_ai_lite_processor.py` | Tool 10? | 🔍 Check | Enhanced version of ai_lite - check if used |
| `fact_extraction_integration_service.py` | Tool 11? | 🔍 Check | Integration service - check if used by tools |
| `research_integration_service.py` | Tool 11? | 🔍 Check | Integration service - check if used by tools |
| `competitive_intelligence.py` | No tool yet | 🔍 Check | Feature or future tool? |
| `competitive_intelligence_processor.py` | No tool yet | 🔍 Check | Duplicate of above? |
| `corporate_csr_analyzer.py` | No tool yet | 🔍 Check | Corporate CSR analysis - future tool? |
| `intelligent_classifier.py` | Tool 11? | 🔍 Check | Classification logic - merged into tools? |
| `opportunity_type_detector.py` | Tool 10? | 🔍 Check | Opportunity classification - merged? |

**Subtotal**: 10 processors → Need code review to determine status

### Data Collection Processors (1 file)

| Processor File | Potential Tool | Status | Action Needed |
|---------------|----------------|--------|---------------|
| `pf_data_extractor.py` | Tool 3 (XML 990-PF Parser)? | 🔍 Check | May be replaced by 990-PF parser tool |

**Subtotal**: 1 processor → Need code review

### Analysis Utilities (5 files)

| Processor File | Purpose | Status | Action Needed |
|---------------|---------|--------|---------------|
| `ein_cross_reference.py` | EIN validation | 🔍 Check | May be utility, not processor |
| `gpt_url_discovery.py` | URL discovery via GPT | 🔍 Check | Used by Tool 25 (Web Intelligence)? |
| `market_intelligence_monitor.py` | Market monitoring | 🔍 Check | Real-time monitoring - future feature? |
| `smart_duplicate_detector.py` | Deduplication | 🔍 Check | Utility used by multiple tools? |
| `trend_analyzer.py` | Trend analysis | 🔍 Check | Part of Tool 22 (Historical Funding)? |

**Subtotal**: 5 processors → Need code review

### **Category 2 Total: 16 processors need investigation**

---

## Category 3: ⏸️ DEFERRED (Government Opportunities)

### Data Collection Processors (3 files)

| Processor File | Future Tool | Status | Notes |
|---------------|-------------|--------|-------|
| `grants_gov_fetch.py` | Grants.gov Tool | ⏸️ Defer | Phase 9 - after nonprofit workflow |
| `usaspending_fetch.py` | USASpending Tool | ⏸️ Defer | Phase 9 - after nonprofit workflow |
| `va_state_grants_fetch.py` | State Grants Tool | ⏸️ Defer | Phase 9 - after nonprofit workflow |

**Subtotal**: 3 processors → Keep until government tools built

---

## Category 4: ❓ UNCLEAR PURPOSE (Need Review)

### Data Collection Processors (3 files)

| Processor File | Purpose | Status | Action Needed |
|---------------|---------|--------|---------------|
| `foundation_directory_fetch.py` | Foundation data | ❓ Check | Still used or replaced? |
| `propublica_fetch.py` | ProPublica API | ❓ Check | Tool 8 (ProPublica API Enrichment) exists |
| `xml_downloader.py` | XML download | ❓ Check | Utility or replaced by parsers? |

**Subtotal**: 3 processors → Need code review

### Utilities (4 files)

| Processor File | Purpose | Status | Action Needed |
|---------------|---------|--------|---------------|
| `pdf_downloader.py` | PDF download | ❓ Check | Utility or deprecated? |
| `pdf_ocr.py` | PDF OCR | ❓ Check | Future feature or unused? |
| `network_visualizer.py` | Network viz | ❓ Check | Part of visualization/ or deprecated? |
| `registry.py` | Processor registry | ❓ Check | Replaced by tool_registry.py? |

**Subtotal**: 4 processors → Need code review

### **Category 4 Total: 7 processors unclear**

---

## Summary Statistics

| Category | Count | Action |
|----------|-------|--------|
| ✅ Ready to Deprecate | 20 | Move to `_deprecated/` |
| 🔍 Needs Investigation | 16 | Code review required |
| ⏸️ Deferred (Gov Tools) | 3 | Keep for now |
| ❓ Unclear Purpose | 7 | Code review required |
| **TOTAL** | **46** | **20 immediate, 23 review, 3 defer** |

---

## Recommended Action Plan

### Phase 1: Quick Wins (2-3 hours)
1. **Move 20 confirmed deprecated processors** to `src/processors/_deprecated/`
2. **Move corresponding tests** to `tests/deprecated_processor_tests/`
3. **Search for imports** of these 20 files and update references

### Phase 2: Code Review (4-6 hours)
1. **Review 23 uncertain processors** (Categories 2 & 4)
2. **Check import usage** across codebase
3. **Determine**: Keep as utility, deprecate, or merge into tools
4. **Document findings** in this file

### Phase 3: Import Migration (2-3 hours)
1. **Find all imports** of deprecated processors
2. **Update to use new tools** via tool registry
3. **Test functionality** after migration
4. **Remove deprecated files** (optional - can keep for reference)

### Phase 4: Documentation (1 hour)
1. **Update MIGRATION_HISTORY.md** with cleanup completion
2. **Update CLAUDE.md** to reflect cleanup status
3. **Create deprecation guide** for any remaining edge cases

---

## Next Steps

**Immediate**: Start Phase 1 - Move 20 confirmed deprecated processors

**Question for Review**: Should we delete deprecated files entirely, or keep them in `_deprecated/` for reference?

---

**Status**: Audit Complete - Ready for Cleanup Phase 1
**Last Updated**: 2025-10-05
