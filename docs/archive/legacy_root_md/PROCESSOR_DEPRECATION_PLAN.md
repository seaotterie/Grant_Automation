# Processor Deprecation Plan

**Date**: 2025-10-02
**Status**: Documentation Phase - Processors marked for deprecation but kept operational for legacy endpoints

## Overview

Phase 8 completed the tool-based architecture with 23 operational tools. Legacy processors are now superseded but remain active to support 50+ legacy API endpoints. This document tracks the deprecation roadmap.

## Processors Replaced by Tools

### Tool 1 & 2 Replacements (Opportunity Screening & Deep Intelligence)
**Status**: Replaced - Keep for legacy endpoint compatibility

- `ai_heavy_deep_researcher.py` → Tool 2 (Deep Intelligence - Complete depth)
- `ai_heavy_light_analyzer.py` → Tool 1 (Opportunity Screening - Fast mode)
- `ai_heavy_researcher.py` → Tool 2 (Deep Intelligence - Standard depth)
- `ai_heavy_research_bridge.py` → Tool 2 (Deep Intelligence)
- `ai_lite_unified_processor.py` → Tool 1 (Opportunity Screening)
- `enhanced_ai_lite_processor.py` → Tool 1 (Opportunity Screening - Thorough mode)

### Tool 11 Replacement (Risk Intelligence)
**Status**: Replaced - Keep for legacy endpoint compatibility

- `risk_assessor.py` → Tool 11 (Risk Intelligence Tool)

### Tool 12 Replacement (Network Intelligence)
**Status**: Replaced - Keep for legacy endpoint compatibility

- `board_network_analyzer.py` → Tool 12 (Network Intelligence Tool)
- `enhanced_network_analyzer.py` → Tool 12 (Network Intelligence Tool)

### Tool 13 Replacement (Schedule I Grant Analyzer)
**Status**: Replaced - Keep for legacy endpoint compatibility

- `schedule_i_processor.py` → Tool 13 (Schedule I Grant Analyzer Tool)
- `funnel_schedule_i_analyzer.py` → Tool 13 (Schedule I Grant Analyzer Tool)

### Tool 20 Replacement (Multi-Dimensional Scorer)
**Status**: Replaced - Keep for legacy endpoint compatibility

- `financial_scorer.py` → Tool 12 (Financial Intelligence Tool)
- `government_opportunity_scorer.py` → Tool 20 (Multi-Dimensional Scorer Tool)

### Tool 21 Replacement (Report Generator)
**Status**: Replaced - Keep for legacy endpoint compatibility

- `report_generator.py` → Tool 21 (Report Generator Tool)

### Tool 19 Replacement (Grant Package Generator)
**Status**: Replaced - Keep for legacy endpoint compatibility

- `grant_package_generator.py` → Tool 19 (Grant Package Generator Tool)

## Processors to Keep Active (Permanent)

These processors are used by both legacy endpoints and modern tools:

- ✅ `ein_lookup.py` - Used by legacy endpoints
- ✅ `bmf_filter.py` - Used by legacy endpoints
- ✅ `propublica_fetch.py` - Used by legacy endpoints
- ✅ `pf_data_extractor.py` - Used by legacy endpoints
- ✅ `gpt_url_discovery.py` - Used by Tool 25 (Web Intelligence)

## Other Legacy Processors

**Status**: To be evaluated in Phase 9-10

- `competitive_intelligence.py`
- `competitive_intelligence_processor.py`
- `corporate_csr_analyzer.py`
- `deterministic_scoring_engine.py`
- `ein_cross_reference.py`
- `fact_extraction_integration_service.py`
- `fact_extraction_prompts.py`
- `intelligent_classifier.py`
- `market_intelligence_monitor.py`
- `opportunity_type_detector.py`
- `optimized_analysis_orchestrator.py`
- `pdf_ocr.py`
- `research_integration_service.py`
- `smart_duplicate_detector.py`
- `trend_analyzer.py`
- `network_visualizer.py`
- `export_processor.py`
- `ai_service_manager.py`

## Data Collection Processors

**Status**: To be evaluated - May be needed for government opportunity tools (Phase 9)

- `foundation_directory_fetch.py`
- `grants_gov_fetch.py` - May be needed for Tool 23
- `pdf_downloader.py`
- `usaspending_fetch.py` - May be needed for Tool 24
- `va_state_grants_fetch.py` - May be needed for Tool 26
- `xml_downloader.py`
- `enhanced_bmf_filter.py`

## Deprecation Roadmap

### Phase 9 (Week 10 - Current)
- ✅ Document deprecation plan (this file)
- ⏳ Create `src/processors/_deprecated/` migration script
- ⏳ Maintain backward compatibility via import redirects

### Phase 10 (Week 11)
- Migrate legacy endpoints to v2 API (tool-based)
- Move deprecated processors to `src/processors/_deprecated/`
- Update all imports to new locations

### Phase 11 (Production Deployment)
- Complete processor removal
- Clean up import paths
- Final codebase optimization

## Import Usage Tracking

**Active imports in src/web/main.py**: 20+ legacy processor imports
**Active imports in other modules**: 26+ processor imports

All imports must be updated before physical file movement.

## Notes

- Legacy endpoints provide backward compatibility
- New v2 API uses tool-based architecture exclusively
- Processors marked as "Replaced" are fully superseded by tools
- No functionality will be lost in migration
