# Deprecated Processors

**Status**: These processors have been replaced by 12-factor compliant tools
**Date Deprecated**: 2025-10-05
**Phase**: 12-Factor Transformation Cleanup

---

## Why Deprecated?

These processors were part of the legacy system before the 12-factor transformation. Each has been replaced by a modern, 12-factor compliant tool with improved:
- Structured outputs (BAML validation)
- Stateless execution
- Single responsibility design
- Better error handling
- Comprehensive testing

---

## Processor → Tool Migration Map

### Analysis Processors (15 files)

| Deprecated Processor | Replaced By | Tool Path |
|---------------------|-------------|-----------|
| `ai_lite_unified_processor.py` | Opportunity Screening Tool (fast mode) | `tools/opportunity-screening-tool/` |
| `ai_heavy_light_analyzer.py` | Opportunity Screening Tool (thorough mode) | `tools/opportunity-screening-tool/` |
| `ai_heavy_deep_researcher.py` | Deep Intelligence Tool | `tools/deep-intelligence-tool/` |
| `ai_heavy_researcher.py` | Deep Intelligence Tool | `tools/deep-intelligence-tool/` |
| `financial_scorer.py` | Financial Intelligence Tool | `tools/financial-intelligence-tool/` |
| `risk_assessor.py` | Risk Intelligence Tool | `tools/risk-intelligence-tool/` |
| `board_network_analyzer.py` | Network Intelligence Tool | `tools/network-intelligence-tool/` |
| `enhanced_network_analyzer.py` | Network Intelligence Tool | `tools/network-intelligence-tool/` |
| `schedule_i_processor.py` | Schedule I Grant Analyzer Tool | `tools/schedule-i-grant-analyzer-tool/` |
| `funnel_schedule_i_analyzer.py` | Schedule I Grant Analyzer Tool | `tools/schedule-i-grant-analyzer-tool/` |
| `grant_package_generator.py` | Grant Package Generator Tool | `tools/grant-package-generator-tool/` |
| `government_opportunity_scorer.py` | Multi-Dimensional Scorer Tool | `tools/multi-dimensional-scorer-tool/` |
| `deterministic_scoring_engine.py` | Multi-Dimensional Scorer Tool | `tools/multi-dimensional-scorer-tool/` |
| `fact_extraction_prompts.py` | Deep Intelligence Tool (prompts integrated) | `tools/deep-intelligence-tool/` |
| `optimized_analysis_orchestrator.py` | Workflow Engine | `src/workflows/workflow_engine.py` |

### Filtering Processors (2 files)

| Deprecated Processor | Replaced By | Tool Path |
|---------------------|-------------|-----------|
| `bmf_filter.py` | BMF Filter Tool | `tools/bmf-filter-tool/` |
| `enhanced_bmf_filter.py` | BMF Filter Tool (enhanced features merged) | `tools/bmf-filter-tool/` |

### Lookup Processors (1 file)

| Deprecated Processor | Replaced By | Tool Path |
|---------------------|-------------|-----------|
| `ein_lookup.py` | EIN Validator Tool | `tools/ein-validator-tool/` |

### Export Processors (1 file)

| Deprecated Processor | Replaced By | Tool Path |
|---------------------|-------------|-----------|
| `export_processor.py` | Data Export Tool | `tools/data-export-tool/` |

### Report Processors (1 file)

| Deprecated Processor | Replaced By | Tool Path |
|---------------------|-------------|-----------|
| `report_generator.py` | Report Generator Tool | `tools/report-generator-tool/` |

---

## How to Use New Tools

### Via Tool Registry (Recommended)
```python
from src.core.tool_registry import ToolRegistry

# Load tool
registry = ToolRegistry()
tool = registry.get_tool("opportunity-screening-tool")

# Execute
result = await tool.execute(context)
```

### Via Direct Import
```python
from tools.opportunity_screening_tool.app.screening_tool import OpportunityScreeningTool

tool = OpportunityScreeningTool()
result = await tool.execute(context)
```

### Via REST API
```bash
# List all tools
GET /api/v1/tools/

# Get tool metadata
GET /api/v1/tools/opportunity-screening-tool

# Execute tool
POST /api/v1/tools/opportunity-screening-tool/execute
```

---

## Migration Guide

If you have code that imports these deprecated processors:

1. **Find imports**: Search codebase for `from src.processors.analysis import ...`
2. **Replace with tool**: Use tool registry or direct tool import
3. **Update execution**: Tools use async `execute()` method with structured outputs
4. **Test thoroughly**: Verify functionality with new tool

---

## Can These Files Be Deleted?

**Not yet recommended**. Keep for reference during migration period. Once all imports are updated and tested:
- Archive to `docs/archive/deprecated_processors/`
- Or delete entirely if confident in migration

---

## Questions?

See documentation:
- `docs/PROCESSOR_CLEANUP_AUDIT.md` - Full deprecation audit
- `docs/MIGRATION_HISTORY.md` - Transformation timeline
- `docs/TWO_TOOL_ARCHITECTURE.md` - New architecture overview

---

## Phase 2 Additions (2025-10-05)

### Additional Analysis Processors (9 files)

| Deprecated Processor | Reason | Notes |
|---------------------|---------|-------|
| `ai_heavy_research_bridge.py` | Legacy AI architecture | Bridge processor for old 5-call system |
| `ai_service_manager.py` | Legacy AI architecture | Service manager for deprecated processors |
| `enhanced_ai_lite_processor.py` | Legacy AI architecture | Experimental enhancement of deprecated processor |
| `fact_extraction_integration_service.py` | Legacy AI architecture | Integration layer for deprecated processors |
| `research_integration_service.py` | Legacy AI architecture | Integration layer for deprecated workflows |
| `competitive_intelligence.py` | Duplicate/old version | Replaced by competitive_intelligence_processor.py |
| `competitive_intelligence_processor.py` | Not used | Orphaned - no active imports |
| `market_intelligence_monitor.py` | Future feature | Not implemented for production |
| `network_visualizer.py` | Wrong location | Visualization should be in src/visualization/ |

---

## Phase 3 Additions (2025-10-05)

### Final Analysis Processors (2 files)

| Deprecated Processor | Reason | Notes |
|---------------------|---------|-------|
| `ein_cross_reference.py` | Orphaned | No active imports, replaced by Schedule I Tool + EIN Validator Tool |
| `trend_analyzer.py` | Replaced by tool | Functionality in Historical Funding Analyzer Tool (Tool 22) |

---

## Phase 3C Additions (2025-10-05)

### Final Verification-Based Deprecations (4 files)

| Deprecated Processor | Reason | Notes |
|---------------------|---------|-------|
| `pf_data_extractor.py` | Fully replaced by XML 990-PF Parser Tool | Tool has ALL capabilities plus more (investments, excise tax, payout) |
| `gpt_url_discovery.py` | Unreliable and unnecessary | GPT URL guessing removed from SmartURLResolutionService (0.3 confidence) |
| `xml_downloader.py` | OBE - 990s in database | XML tools have built-in download capability, ProPublica scraping no longer needed |
| `smart_duplicate_detector.py` | Orphaned and unused | ML deduplication not currently needed, database is stable |

---

**Total Deprecated**: 35 processors (20 Phase 1 + 9 Phase 2 + 2 Phase 3 + 4 Phase 3C)
**Replacement Tools**: 24 modern 12-factor tools
**Active Processors Remaining**: 11 (76% reduction from original 46)
**Status**: Phase 3C complete - Final transformation successful ✅
