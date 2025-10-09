# Tools and Endpoints Comprehensive Analysis

**Date**: 2025-10-02
**Analysis Scope**: 23 operational tools, 162 legacy API endpoints, modernization opportunities
**Purpose**: Understand system architecture and identify consolidation opportunities

---

## Executive Summary

### Current Architecture State

**Tools (23 operational - 12-factor compliant)**
- 9 Data Collection/Parsing Tools (Forms 990, BMF, ProPublica)
- 2 AI Intelligence Tools (Screening & Deep Analysis)
- 4 Specialized Analysis Tools (Financial, Risk, Network, Grants)
- 3 Data Quality Tools (Validators, Export)
- 3 Output Generation Tools (Scorer, Reporter, Package Generator)
- 2 Discovery & Enhancement Tools (Historical, Web Intelligence)

**APIs (162+ legacy endpoints + 11 modern endpoints)**
- **Legacy APIs (162)**: Processor-based, monolithic, high duplication
- **Modern V2 Profile API (6)**: Tool-based, orchestrated workflows
- **Tool Execution API (5)**: Unified tool access, RESTful

**Key Finding**: **80-90% endpoint redundancy** - Tools fully replicate processor functionality but legacy endpoints remain for backward compatibility

---

## Part 1: The 23 Operational Tools

### Category 1: Data Collection & Parsing (9 tools)

#### Tool 1: XML 990 Parser Tool
- **Purpose**: Parse IRS Form 990 XML files for regular nonprofits
- **Cost**: $0.00 (parsing only)
- **Performance**: ~100ms per form
- **Replaces**: Internal parsing logic
- **Status**: ✅ Operational

#### Tool 2: XML 990-PF Parser Tool
- **Purpose**: Parse IRS Form 990-PF XML files for private foundations
- **Cost**: $0.00 (parsing only)
- **Performance**: ~100ms per form
- **Replaces**: Internal parsing logic
- **Status**: ✅ Operational

#### Tool 3: XML 990-EZ Parser Tool
- **Purpose**: Parse IRS Form 990-EZ XML files for small nonprofits
- **Cost**: $0.00 (parsing only)
- **Performance**: ~50ms per form
- **Replaces**: Internal parsing logic
- **Status**: ✅ Operational

#### Tool 4: BMF Filter Tool
- **Purpose**: IRS Business Master File filtering and nonprofit discovery
- **Cost**: $0.00 (database queries)
- **Performance**: <1s for most queries
- **Data**: 700K+ organizations
- **Replaces**: `bmf_filter.py` processor
- **Status**: ✅ Operational

#### Tool 5: Form 990 Analysis Tool
- **Purpose**: Financial metrics and analytics from parsed 990 data
- **Cost**: $0.00 (algorithmic analysis)
- **Performance**: <100ms per analysis
- **Data**: 626K+ Form 990 records
- **Replaces**: Internal analysis logic
- **Status**: ✅ Operational

#### Tool 6: Form 990 ProPublica Tool
- **Purpose**: ProPublica API integration for 990 data enrichment
- **Cost**: $0.00 (free API)
- **Performance**: 1-3s per organization
- **Replaces**: `propublica_fetch.py` processor
- **Status**: ✅ Operational

#### Tool 7: Foundation Grant Intelligence Tool
- **Purpose**: Private foundation grant-making pattern analysis
- **Cost**: $0.00 (database analysis)
- **Performance**: <200ms per foundation
- **Data**: 220K+ Form 990-PF records
- **Replaces**: Foundation analysis logic
- **Status**: ✅ Operational

#### Tool 8: ProPublica API Enrichment Tool
- **Purpose**: Additional ProPublica data enrichment
- **Cost**: $0.00 (free API)
- **Performance**: 1-2s per organization
- **Replaces**: Enrichment logic
- **Status**: ✅ Operational

#### Tool 9: XML Schedule Parser Tool
- **Purpose**: Extract and parse IRS form schedules (A, B, C, I, etc.)
- **Cost**: $0.00 (parsing only)
- **Performance**: 50-200ms per schedule
- **Replaces**: Schedule parsing logic
- **Status**: ✅ Operational

---

### Category 2: AI Intelligence Tools (2 tools)

#### Tool 10: Opportunity Screening Tool
- **Purpose**: Mass screening of 100s of opportunities → 10-15 high-potential matches
- **Cost**:
  - Fast mode: $0.0004/opp (~2s each)
  - Thorough mode: $0.02/opp (~5s each)
- **Performance**: 200 opportunities → $0.08-$4.00, 7-17 minutes
- **Replaces**:
  - `ai_lite_unified_processor.py`
  - `ai_heavy_light_analyzer.py`
  - `enhanced_ai_lite_processor.py`
- **Status**: ✅ Operational
- **Integration**: Stage 1 of two-tool pipeline (screening → human gateway → deep analysis)

#### Tool 11: Deep Intelligence Tool
- **Purpose**: Comprehensive analysis of selected opportunities
- **Cost**:
  - Quick: $0.75 (5-10 min)
  - Standard: $7.50 (15-20 min)
  - Enhanced: $22.00 (30-45 min)
  - Complete: $42.00 (45-60 min)
- **Performance**: 4 depth levels for different analysis needs
- **Replaces**:
  - `ai_heavy_deep_researcher.py`
  - `ai_heavy_researcher.py`
  - `ai_heavy_research_bridge.py`
  - All 4 tier processors (CURRENT, STANDARD, ENHANCED, COMPLETE)
- **Status**: ✅ Operational
- **Integration**: Stage 2 of two-tool pipeline (after screening + human review)

---

### Category 3: Specialized Analysis Tools (4 tools)

#### Tool 12: Financial Intelligence Tool
- **Purpose**: Comprehensive financial metrics and health assessment
- **Cost**: $0.03 per analysis
- **Performance**: <200ms per organization
- **Analysis**: 15+ financial metrics, health rating, grant capacity
- **Replaces**: `financial_scorer.py` processor
- **Status**: ✅ Operational

#### Tool 13: Risk Intelligence Tool
- **Purpose**: Multi-dimensional risk assessment (6 dimensions)
- **Cost**: $0.02 per analysis
- **Performance**: <150ms per opportunity
- **Dimensions**: Eligibility, competition, capacity, timeline, financial, compliance
- **Replaces**: `risk_assessor.py` processor
- **Status**: ✅ Operational

#### Tool 14: Network Intelligence Tool
- **Purpose**: Board member profiling, network analysis, relationship mapping
- **Cost**: $0.04 per analysis
- **Performance**: <300ms per organization
- **Features**: Centrality metrics, cluster identification, pathway mapping
- **Replaces**:
  - `board_network_analyzer.py`
  - `enhanced_network_analyzer.py`
- **Status**: ✅ Operational

#### Tool 15: Schedule I Grant Analyzer Tool
- **Purpose**: Foundation grant-making pattern analysis
- **Cost**: $0.03 per analysis
- **Performance**: <200ms per foundation
- **Analysis**: Grant categories, geographic distribution, size analysis, recipient profiling
- **Replaces**:
  - `schedule_i_processor.py`
  - `funnel_schedule_i_analyzer.py`
- **Status**: ✅ Operational

---

### Category 4: Data Quality & Validation Tools (3 tools)

#### Tool 16: Data Validator Tool
- **Purpose**: Data quality validation and completeness scoring
- **Cost**: $0.00 (algorithmic)
- **Performance**: <50ms per validation
- **Features**: Required field validation, type checking, quality scoring
- **Replaces**: `data_validator.py` processor
- **Status**: ✅ Operational

#### Tool 17: EIN Validator Tool
- **Purpose**: EIN format validation and organization lookup
- **Cost**: $0.00 (validation logic)
- **Performance**: <10ms per EIN
- **Features**: Format validation, invalid prefix detection, lookup capability
- **Replaces**: `ein_lookup.py` processor (validation portion)
- **Status**: ✅ Operational

#### Tool 18: Data Export Tool
- **Purpose**: Multi-format data export (JSON, CSV, Excel, PDF)
- **Cost**: $0.00 (formatting)
- **Performance**: 100ms-2s depending on format and size
- **Features**: Template-based formatting, batch export, custom field selection
- **Replaces**: `export_processor.py` processor
- **Status**: ✅ Operational

---

### Category 5: Output Generation Tools (3 tools)

#### Tool 19: Grant Package Generator Tool
- **Purpose**: Application package assembly and management
- **Cost**: $0.00 (assembly)
- **Performance**: 500ms-2s per package
- **Features**: Document checklist, timeline planning, package tracking
- **Replaces**: `grant_package_generator.py` processor
- **Status**: ✅ Operational

#### Tool 20: Multi-Dimensional Scorer Tool
- **Purpose**: 5-stage workflow scoring with dimensional weights
- **Cost**: $0.00 (algorithmic)
- **Performance**: <50ms per score
- **Stages**: DISCOVER → PLAN → ANALYZE → EXAMINE → APPROACH
- **Features**: Dimensional weights, boost factors, confidence calculation
- **Replaces**:
  - `discovery_scorer.py`
  - `success_scorer.py`
  - `government_opportunity_scorer.py`
- **Status**: ✅ Operational

#### Tool 21: Report Generator Tool
- **Purpose**: Professional report generation with multiple templates
- **Cost**: $0.00 (template rendering)
- **Performance**: 1-2s per report
- **Templates**: Comprehensive, executive, risk, implementation
- **Features**: DOSSIER structure, HTML output, responsive design
- **Replaces**: `report_generator.py` processor
- **Status**: ✅ Operational

---

### Category 6: Discovery & Enhancement Tools (2 tools)

#### Tool 22: Historical Funding Analyzer Tool
- **Purpose**: USASpending.gov data analysis with funding pattern detection
- **Cost**: $0.00 (data analysis)
- **Performance**: 4-5ms per analysis
- **Analysis**: Geographic distribution, temporal trends, award sizing, competitive positioning
- **Replaces**: Historical analysis portions of tier processors
- **Status**: ✅ Operational

#### Tool 25: Web Intelligence Tool
- **Purpose**: Scrapy-powered web scraping for nonprofit intelligence
- **Cost**: $0.05-$0.25 per use case
- **Performance**: 10-60s execution time
- **Use Cases**:
  - Profile Builder ($0.05-0.10)
  - Opportunity Research ($0.15-0.25)
  - Foundation Research ($0.10-0.20)
- **Features**: Smart URL resolution, 990 verification pipeline, respectful scraping
- **Replaces**: `verification_enhanced_scraper.py` (enhanced)
- **Status**: ✅ Operational

---

## Part 2: The 162 Legacy API Endpoints

### Endpoint Categories & Redundancy Analysis

#### Category A: Profile Management (40+ endpoints)
**Primary Functions**: Create, read, update, delete profiles; fetch EIN data; analytics

**Legacy Endpoints** (uses processors):
- `/api/profiles` (GET, POST, PUT, DELETE)
- `/api/profiles/{profile_id}` (GET, PUT, DELETE)
- `/api/profiles/fetch-ein` (POST) - Uses `ein_lookup.py` + `gpt_url_discovery.py`
- `/api/profiles/{profile_id}/analytics` (GET)
- `/api/profiles/{profile_id}/metrics` (GET, POST)
- `/api/profiles/{profile_id}/enhanced-intelligence` (GET)
- `/api/profiles/{profile_id}/verified-intelligence` (GET)
- `/api/profiles/{profile_id}/web-intelligence` (GET)
- `/api/profiles/templates` (POST)
- `/api/profiles/metrics/summary` (GET)
- ~30+ additional profile-related endpoints

**Modern V2 Endpoints** (uses tools):
- `/api/v2/profiles/build` (POST) - Uses ProfileEnhancementOrchestrator + Tools
- `/api/v2/profiles/{profile_id}/quality` (GET) - Uses ProfileQualityScorer
- `/api/v2/profiles/{profile_id}/opportunities/score` (POST)
- `/api/v2/profiles/{profile_id}/opportunities/funding` (GET)
- `/api/v2/profiles/{profile_id}/opportunities/networking` (GET)
- `/api/v2/profiles/health` (GET)

**Redundancy**: 85% - Most legacy endpoints can be replaced by 6 modern endpoints

---

#### Category B: Discovery & Search (20+ endpoints)
**Primary Functions**: Discover opportunities, search organizations, BMF filtering

**Legacy Endpoints**:
- `/api/discovery/nonprofit` (GET)
- `/api/discovery/federal` (GET)
- `/api/discovery/state` (GET)
- `/api/discovery/commercial` (GET)
- `/api/discovery/bmf/{profile_id}` (GET)
- `/api/profiles/{profile_id}/discover` (POST)
- `/api/profiles/{profile_id}/discover/bmf` (POST)
- `/api/profiles/{profile_id}/discover/entity-analytics` (POST)
- `/api/profiles/{profile_id}/discover/entity-preview` (GET)
- `/api/profiles/{profile_id}/discover/unified` (POST)
- `/api/search/opportunities` (GET)
- `/api/search/fields` (GET)
- ~10+ additional discovery endpoints

**Tool-Based Alternative**:
- Tool 4 (BMF Filter) via `/api/v1/tools/bmf-filter-tool/execute`
- Tool 22 (Historical Funding) via `/api/v1/tools/historical-funding-analyzer-tool/execute`

**Redundancy**: 70% - Can consolidate to 5-6 unified discovery endpoints

---

#### Category C: AI Analysis (30+ endpoints)
**Primary Functions**: AI-powered opportunity analysis, research, scoring

**Legacy Endpoints** (uses processors):
- `/api/ai/lite-analysis` (POST) - Uses `ai_lite_unified_processor.py`
- `/api/ai/heavy-light/analyze` (POST) - Uses `ai_heavy_light_analyzer.py`
- `/api/ai/heavy-1/research-bridge` (POST) - Uses `ai_heavy_researcher.py`
- `/api/ai/deep-research` (POST) - Uses `ai_heavy_deep_researcher.py`
- `/api/ai/lite-1/validate` (POST)
- `/api/ai/lite-2/strategic-score` (POST)
- `/api/ai/batch-analysis` (POST)
- `/api/ai/orchestrated-pipeline` (POST)
- `/api/research/ai-lite/analyze` (POST)
- `/api/research/capabilities` (GET)
- `/api/profiles/{profile_id}/analyze/ai-lite` (POST)
- `/api/profiles/{profile_id}/research/analyze-integrated` (POST)
- `/api/profiles/{profile_id}/research/batch-analyze` (POST)
- ~20+ additional AI/research endpoints

**Tool-Based Alternative**:
- Tool 10 (Opportunity Screening) via `/api/v1/tools/opportunity-screening-tool/execute`
- Tool 11 (Deep Intelligence) via `/api/v1/tools/deep-intelligence-tool/execute`
- OR via Workflow API: `/api/v1/workflows/execute` with workflow names

**Redundancy**: 95% - All functionality available via 2 tool endpoints + workflow API

---

#### Category D: Scoring & Analysis (15+ endpoints)
**Primary Functions**: Opportunity scoring, risk assessment, financial analysis

**Legacy Endpoints** (uses processors):
- `/api/analysis/scoring` (POST) - Uses various scorer processors
- `/api/analysis/network` (POST) - Uses `board_network_analyzer.py`
- `/api/analysis/enhanced-scoring` (POST)
- `/api/profiles/{profile_id}/opportunity-scores` (POST)
- `/api/profiles/{profile_id}/opportunities/{opp_id}/score` (POST)
- `/api/profiles/{profile_id}/opportunities/{opp_id}/scoring-rationale` (GET)
- `/api/scoring/government` (POST) - Uses `government_opportunity_scorer.py`
- `/api/scoring/financial` (POST) - Uses `financial_scorer.py`
- `/api/scoring/network` (POST)
- `/api/scoring/ai-lite` (POST)
- `/api/scoring/comprehensive` (POST)
- ~5+ additional scoring endpoints

**Tool-Based Alternative**:
- Tool 12 (Financial Intelligence) via tool execution API
- Tool 13 (Risk Intelligence) via tool execution API
- Tool 14 (Network Intelligence) via tool execution API
- Tool 20 (Multi-Dimensional Scorer) via tool execution API

**Redundancy**: 90% - All functionality available via 4 tool endpoints

---

#### Category E: Workflow & Funnel (15+ endpoints)
**Primary Functions**: Workflow management, opportunity funnel, stage transitions

**Legacy Endpoints**:
- `/api/workflows/start` (POST)
- `/api/workflows/{workflow_id}/status` (GET)
- `/api/funnel/{profile_id}/opportunities` (GET)
- `/api/funnel/{profile_id}/opportunities/{opp_id}/promote` (POST)
- `/api/funnel/{profile_id}/opportunities/{opp_id}/demote` (POST)
- `/api/funnel/{profile_id}/opportunities/{opp_id}/stage` (GET)
- `/api/funnel/{profile_id}/bulk-transition` (POST)
- `/api/funnel/{profile_id}/metrics` (GET)
- `/api/funnel/{profile_id}/recommendations` (GET)
- `/api/automated-promotion/process` (POST)
- `/api/automated-promotion/candidates` (GET)
- ~5+ additional workflow endpoints

**Modern Workflow API**:
- `/api/v1/workflows/execute` (POST)
- `/api/v1/workflows/status/{execution_id}` (GET)
- `/api/v1/workflows/results/{execution_id}` (GET)
- `/api/v1/workflows/list` (GET)
- `/api/v1/workflows/executions` (GET)
- `/api/v1/workflows/screen-opportunities` (POST)
- `/api/v1/workflows/deep-intelligence` (POST)

**Redundancy**: 60% - Many funnel endpoints are unique but can be streamlined

---

#### Category F: Export & Reporting (10+ endpoints)
**Primary Functions**: Data export, report generation, document creation

**Legacy Endpoints** (uses processors):
- `/api/analysis/reports` (POST) - Uses `report_generator.py`
- `/api/export/opportunities` (POST) - Uses `export_processor.py`
- `/api/exports/{export_filename}` (GET)
- `/api/exports/classification/{workflow_id}` (GET)
- `/api/exports/workflow/{workflow_id}` (GET)
- `/api/dossier/{dossier_id}/generate-document` (POST)
- `/api/dossier/templates` (GET)
- `/api/profiles/{profile_id}/dossier/generate` (POST)
- `/api/profiles/{profile_id}/dossier/batch-generate` (POST)
- ~3+ additional export endpoints

**Tool-Based Alternative**:
- Tool 18 (Data Export) via tool execution API
- Tool 21 (Report Generator) via tool execution API
- Tool 19 (Grant Package Generator) via tool execution API

**Redundancy**: 80% - All functionality available via 3 tool endpoints

---

#### Category G: System & Monitoring (12+ endpoints)
**Primary Functions**: Health checks, system status, monitoring, analytics

**Endpoints**:
- `/api/system/health` (GET)
- `/api/system/status` (GET)
- `/api/dashboard/overview` (GET)
- `/api/analytics/overview` (GET)
- `/api/analytics/trends` (GET)
- `/api/processors` (GET)
- `/api/processors/architecture/overview` (GET)
- `/api/pipeline/status` (GET)
- `/api/live/system-monitor` (GET)
- `/api/health` (GET)
- ~5+ additional system endpoints

**Redundancy**: 30% - Most are unique monitoring endpoints, minimal consolidation

---

#### Category H: Opportunity Management (20+ endpoints)
**Primary Functions**: Opportunity CRUD, enhanced data, evaluation

**Legacy Endpoints**:
- `/api/opportunities` (GET)
- `/api/profiles/{profile_id}/opportunities` (GET)
- `/api/profiles/{profile_id}/opportunities/{opp_id}` (GET, PUT, DELETE)
- `/api/profiles/{profile_id}/opportunities/{opp_id}/details` (GET)
- `/api/profiles/{profile_id}/opportunities/{opp_id}/evaluate` (POST)
- `/api/profiles/{profile_id}/opportunities/{opp_id}/enhanced-data` (GET)
- `/api/profiles/{profile_id}/opportunities/enhanced-data/batch` (POST)
- `/api/profiles/{profile_id}/opportunities/bulk-promote` (POST)
- `/api/profiles/{profile_id}/leads` (GET)
- `/api/profiles/{profile_id}/add-entity-lead` (POST)
- ~10+ additional opportunity endpoints

**Redundancy**: 50% - Many unique but can be consolidated

---

## Part 3: Processor-Tool-Endpoint Mapping

### Direct Replacement Mapping

| Processor | Tool | Legacy Endpoints Using It | Status |
|-----------|------|--------------------------|--------|
| `ai_lite_unified_processor.py` | Tool 10 (Screening) | `/api/ai/lite-analysis`, `/api/research/ai-lite/analyze` | ✅ Replaced |
| `ai_heavy_light_analyzer.py` | Tool 10 (Screening) | `/api/ai/heavy-light/analyze` | ✅ Replaced |
| `enhanced_ai_lite_processor.py` | Tool 10 (Screening) | N/A | ✅ Replaced |
| `ai_heavy_deep_researcher.py` | Tool 11 (Deep Intel) | `/api/ai/deep-research` | ✅ Replaced |
| `ai_heavy_researcher.py` | Tool 11 (Deep Intel) | `/api/ai/heavy-1/research-bridge` | ✅ Replaced |
| `ai_heavy_research_bridge.py` | Tool 11 (Deep Intel) | N/A | ✅ Replaced |
| `financial_scorer.py` | Tool 12 (Financial) | `/api/scoring/financial` | ✅ Replaced |
| `risk_assessor.py` | Tool 13 (Risk) | Multiple scoring endpoints | ✅ Replaced |
| `board_network_analyzer.py` | Tool 14 (Network) | `/api/analysis/network`, `/api/scoring/network` | ✅ Replaced |
| `enhanced_network_analyzer.py` | Tool 14 (Network) | N/A | ✅ Replaced |
| `schedule_i_processor.py` | Tool 15 (Schedule I) | N/A | ✅ Replaced |
| `funnel_schedule_i_analyzer.py` | Tool 15 (Schedule I) | N/A | ✅ Replaced |
| `data_validator.py` | Tool 16 (Validator) | Various validation endpoints | ✅ Replaced |
| `ein_lookup.py` | Tool 17 (EIN Validator) | `/api/profiles/fetch-ein` (partial) | ⚠️ Still in use |
| `export_processor.py` | Tool 18 (Export) | `/api/export/opportunities` | ✅ Replaced |
| `grant_package_generator.py` | Tool 19 (Package Gen) | N/A | ✅ Replaced |
| `discovery_scorer.py` | Tool 20 (Scorer) | `/api/analysis/scoring` | ✅ Replaced |
| `success_scorer.py` | Tool 20 (Scorer) | `/api/analysis/enhanced-scoring` | ✅ Replaced |
| `government_opportunity_scorer.py` | Tool 20 (Scorer) | `/api/scoring/government` | ✅ Replaced |
| `report_generator.py` | Tool 21 (Reporter) | `/api/analysis/reports`, `/api/dossier/*` | ✅ Replaced |
| `verification_enhanced_scraper.py` | Tool 25 (Web Intel) | `/api/profiles/fetch-ein` (partial) | ✅ Replaced |

### Processors Still Required (5)
These are used by legacy endpoints and cannot be removed yet:
1. `ein_lookup.py` - Used by `/api/profiles/fetch-ein`
2. `bmf_filter.py` - Used by multiple discovery endpoints
3. `propublica_fetch.py` - Used by profile building endpoints
4. `pf_data_extractor.py` - Used by foundation data endpoints
5. `gpt_url_discovery.py` - Used by Tool 25 internally

---

## Part 4: Duplication & Consolidation Opportunities

### High-Impact Consolidation (60+ endpoints → 15 endpoints)

#### 1. Profile Management Consolidation
**Current**: 40+ endpoints
**Target**: 8 endpoints

**Proposed Structure**:
- `/api/v2/profiles` (GET, POST) - List/create profiles
- `/api/v2/profiles/{id}` (GET, PUT, DELETE) - Manage profile
- `/api/v2/profiles/build` (POST) - Orchestrated profile building
- `/api/v2/profiles/{id}/quality` (GET) - Quality assessment
- `/api/v2/profiles/{id}/opportunities` (GET) - List opportunities
- `/api/v2/profiles/{id}/opportunities/discover` (POST) - Discover new
- `/api/v2/profiles/{id}/analytics` (GET) - Analytics summary
- `/api/v2/profiles/{id}/export` (POST) - Export data

**Elimination**: 32 endpoints removed

---

#### 2. AI Analysis Consolidation
**Current**: 30+ endpoints
**Target**: 3 endpoints (via Tool Execution API)

**Proposed Structure**:
- `/api/v1/tools/opportunity-screening-tool/execute` (POST) - All screening
- `/api/v1/tools/deep-intelligence-tool/execute` (POST) - All deep analysis
- `/api/v1/workflows/execute` (POST) - Orchestrated workflows

**Elimination**: 27 endpoints removed

---

#### 3. Scoring & Analysis Consolidation
**Current**: 15+ endpoints
**Target**: 4 endpoints (via Tool Execution API)

**Proposed Structure**:
- `/api/v1/tools/financial-intelligence-tool/execute` (POST)
- `/api/v1/tools/risk-intelligence-tool/execute` (POST)
- `/api/v1/tools/network-intelligence-tool/execute` (POST)
- `/api/v1/tools/multi-dimensional-scorer-tool/execute` (POST)

**Elimination**: 11 endpoints removed

---

#### 4. Export & Reporting Consolidation
**Current**: 10+ endpoints
**Target**: 3 endpoints (via Tool Execution API)

**Proposed Structure**:
- `/api/v1/tools/data-export-tool/execute` (POST)
- `/api/v1/tools/report-generator-tool/execute` (POST)
- `/api/v1/tools/grant-package-generator-tool/execute` (POST)

**Elimination**: 7 endpoints removed

---

### Total Consolidation Impact

**Before Consolidation**:
- 162 legacy endpoints
- 40+ processor imports in main.py
- High maintenance burden
- Difficult to understand/document

**After Consolidation** (Proposed):
- ~35 core endpoints:
  - 10 Profile V2 endpoints
  - 5 Tool Execution endpoints
  - 7 Workflow endpoints
  - 5 Intelligence endpoints
  - 8 System/monitoring endpoints
- 5 processor imports (minimum required)
- Reduced maintenance
- Clear, RESTful architecture

**Reduction**: 127 endpoints (78% reduction)

---

## Part 5: Migration Complexity Assessment

### Low Risk Migrations (Can do immediately)
1. **AI Analysis endpoints** → Tool 10 & 11
   - Impact: ~30 endpoints
   - Risk: Low (tools proven operational)
   - Effort: 1-2 days

2. **Scoring endpoints** → Tools 12, 13, 14, 20
   - Impact: ~15 endpoints
   - Risk: Low (tools operational)
   - Effort: 1 day

3. **Export/Report endpoints** → Tools 18, 19, 21
   - Impact: ~10 endpoints
   - Risk: Low (tools operational)
   - Effort: 1 day

### Medium Risk Migrations (Need testing)
4. **Discovery endpoints** → Tool 4 + consolidation
   - Impact: ~20 endpoints
   - Risk: Medium (complex query patterns)
   - Effort: 2-3 days

5. **Profile endpoints** → V2 Profile API
   - Impact: ~40 endpoints
   - Risk: Medium (frontend dependencies)
   - Effort: 3-5 days

### High Risk Migrations (Phase 10-11)
6. **Workflow/Funnel endpoints** → New workflow API
   - Impact: ~15 endpoints
   - Risk: High (complex state management)
   - Effort: 1 week

7. **System/Monitoring endpoints** → Streamline
   - Impact: ~12 endpoints
   - Risk: Medium (operational visibility)
   - Effort: 2-3 days

---

## Key Recommendations

### Immediate Actions (Phase 9)
1. ✅ Mark legacy AI endpoints as deprecated (add warnings)
2. ✅ Update frontend to use Tool Execution API for AI analysis
3. ✅ Create endpoint migration guide for API consumers
4. ✅ Implement endpoint redirect layer for graceful deprecation

### Short-term Actions (Phase 10)
5. Migrate profile endpoints to V2 API
6. Consolidate discovery endpoints
7. Remove deprecated processors after endpoint migration
8. Update all documentation

### Long-term Actions (Phase 11)
9. Complete workflow API migration
10. Final processor removal
11. Codebase optimization
12. Performance benchmarking

---

## Appendix: Complete Endpoint Inventory

### All 162 Legacy Endpoints
```
/api/ai/analysis-status/{request_id}
/api/ai/batch-analysis
/api/ai/cost-estimates
/api/ai/deep-research
/api/ai/heavy-1/research-bridge
/api/ai/heavy-light/analyze
/api/ai/lite-1/validate
/api/ai/lite-2/strategic-score
/api/ai/lite-analysis
/api/ai/orchestrated-pipeline
/api/ai/session-summary
/api/analysis/enhanced-scoring
/api/analysis/export
/api/analysis/network
/api/analysis/reports
/api/analysis/scoring
/api/analysis/strategic-plan
/api/analytics/overview
/api/analytics/trends
/api/analyze/network-data/{profile_id}
/api/automated-promotion/config
/api/automated-promotion/stats
/api/classification/{workflow_id}/results
/api/classification/start
/api/commercial/discover
/api/commercial/industries
/api/dashboard/overview
/api/debug/funnel-status
/api/discovery/bmf/{profile_id}
/api/discovery/commercial
/api/discovery/entity-cache-stats
/api/discovery/federal
/api/discovery/nonprofit
/api/discovery/sessions/recent
/api/discovery/state
/api/discovery/stats/global
/api/docs
/api/docs/api-documentation
/api/docs/help-index
/api/docs/help-search
/api/docs/processor-guide
/api/docs/user-guide
/api/dossier/{dossier_id}/generate-document
/api/dossier/performance-summary
/api/dossier/templates
/api/enhanced-data/cache
/api/enhanced-data/config
/api/enhanced-data/stats
/api/export/opportunities
/api/exports/{export_filename}
/api/exports/charts/{export_filename}
/api/exports/classification/{workflow_id}
/api/exports/workflow/{workflow_id}
/api/funnel/{profile_id}/bulk-transition
/api/funnel/{profile_id}/metrics
/api/funnel/{profile_id}/opportunities
/api/funnel/{profile_id}/opportunities/{opportunity_id}/demote
/api/funnel/{profile_id}/opportunities/{opportunity_id}/promote
/api/funnel/{profile_id}/opportunities/{opportunity_id}/stage
/api/funnel/{profile_id}/recommendations
/api/funnel/stages
/api/health
/api/intelligence/classify
/api/live/discovery/{session_id}
/api/live/progress/{workflow_id}
/api/live/system-monitor
/api/opportunities
/api/pipeline/full-summary
/api/pipeline/status
/api/plan/{profile_id}/prospects
/api/processors
/api/processors/{processor_name}/execute
/api/processors/{processor_name}/status
/api/processors/architecture/overview
/api/processors/migration/status
/api/profiles
/api/profiles/{ein}/web-intelligence
/api/profiles/{profile_id}
/api/profiles/{profile_id}/add-entity-lead
/api/profiles/{profile_id}/analytics
/api/profiles/{profile_id}/analytics/real-time
/api/profiles/{profile_id}/analyze/ai-lite
/api/profiles/{profile_id}/approach/decision-history
/api/profiles/{profile_id}/approach/export-decision
/api/profiles/{profile_id}/approach/synthesize-decision
/api/profiles/{profile_id}/automated-promotion/bulk-promote
/api/profiles/{profile_id}/automated-promotion/candidates
/api/profiles/{profile_id}/automated-promotion/process
/api/profiles/{profile_id}/discover
/api/profiles/{profile_id}/discover/bmf
/api/profiles/{profile_id}/discover/entity-analytics
/api/profiles/{profile_id}/discover/entity-preview
/api/profiles/{profile_id}/discover/unified
/api/profiles/{profile_id}/discovery/sessions
/api/profiles/{profile_id}/dossier/batch-generate
/api/profiles/{profile_id}/dossier/generate
/api/profiles/{profile_id}/enhanced-intelligence
/api/profiles/{profile_id}/entity-analysis
/api/profiles/{profile_id}/entity-discovery
/api/profiles/{profile_id}/leads
/api/profiles/{profile_id}/metrics
/api/profiles/{profile_id}/metrics/funnel
/api/profiles/{profile_id}/metrics/session
/api/profiles/{profile_id}/opportunities
/api/profiles/{profile_id}/opportunities/{opportunity_id}
/api/profiles/{profile_id}/opportunities/{opportunity_id}/details
/api/profiles/{profile_id}/opportunities/{opportunity_id}/enhanced-data
/api/profiles/{profile_id}/opportunities/{opportunity_id}/evaluate
/api/profiles/{profile_id}/opportunities/{opportunity_id}/promote
/api/profiles/{profile_id}/opportunities/{opportunity_id}/score
/api/profiles/{profile_id}/opportunities/{opportunity_id}/scoring-rationale
/api/profiles/{profile_id}/opportunities/bulk-promote
/api/profiles/{profile_id}/opportunities/enhanced-data/batch
/api/profiles/{profile_id}/opportunity-scores
/api/profiles/{profile_id}/pipeline
/api/profiles/{profile_id}/plan-results
/api/profiles/{profile_id}/promotion-candidates
/api/profiles/{profile_id}/promotion-history
/api/profiles/{profile_id}/research/analyze-integrated
/api/profiles/{profile_id}/research/batch-analyze
/api/profiles/{profile_id}/research/decision-package/{opportunity_id}
/api/profiles/{profile_id}/run-bmf-filter
/api/profiles/{profile_id}/verified-intelligence
/api/profiles/fetch-ein
/api/profiles/leads/{lead_id}/entity-analysis
/api/profiles/metrics/summary
/api/profiles/simple/{profile_id}
/api/profiles/templates
/api/profiles-new
/api/redoc
/api/research/ai-lite/analyze
/api/research/capabilities
/api/research/export-results
/api/research/integration-status/{opportunity_id}
/api/research/performance-summary
/api/research/split-capabilities
/api/research/status/{profile_id}
/api/research/website-intelligence
/api/search/fields
/api/search/opportunities
/api/search/stats
/api/states/discover
/api/system/health
/api/system/status
/api/test
/api/test-fix
/api/testing/export-results
/api/testing/processors/{processor_name}/logs
/api/testing/processors/{processor_name}/test
/api/testing/processors/status
/api/testing/system/logs
/api/visualizations/{chart_id}/export/{format}
/api/visualizations/chart-types
/api/visualizations/decision-dashboard
/api/visualizations/generate-chart
/api/welcome/quick-start
/api/welcome/sample-profile
/api/welcome/status
/api/workflows
/api/workflows/{workflow_id}/status
/api/workflows/start
```

### Modern API Endpoints (11 total)

**V2 Profile API (6)**:
```
/api/v2/profiles/build
/api/v2/profiles/{profile_id}/quality
/api/v2/profiles/{profile_id}/opportunities/score
/api/v2/profiles/{profile_id}/opportunities/funding
/api/v2/profiles/{profile_id}/opportunities/networking
/api/v2/profiles/health
```

**Tool Execution API (5)**:
```
/api/v1/tools (GET)
/api/v1/tools/{tool_name} (GET)
/api/v1/tools/{tool_name}/execute (POST)
/api/v1/tools/categories/list (GET)
/api/v1/tools/health (GET)
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-02
**Next Review**: After Phase 9 consolidation
