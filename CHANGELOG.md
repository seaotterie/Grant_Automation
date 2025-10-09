# Changelog - Catalynx Grant Intelligence Platform

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2025-10-09] - Phases 1-3 Complete: BAML Conversion & Testing Infrastructure

### Added

#### Phase 1: Foundation Scoring System BAML Conversion
- **25 BAML Schemas**: Complete foundation scoring system (14 classes + 11 enums)
  - NTEE Scoring: 4 schemas (NTEEScoreResult, NTEECode, NTEEDataSource, NTEEMatchLevel)
  - Schedule I Voting: 3 schemas (ScheduleIAnalysis, RecipientVote, NTEEVoteResult)
  - Grant Size Scoring: 4 schemas (GrantSizeAnalysis, GrantSizeBand, CapacityLevel, GrantSizeFit)
  - Composite Scorer V2: 2 schemas (CompositeScoreResult, FoundationOpportunityData)
  - Triage Queue: 5 schemas (TriageItem, TriageQueueStats, TriageStatus, TriagePriority, ExpertDecision)
  - Reliability Safeguards: 7 schemas (ReliabilitySafeguardsResult + 6 component schemas)

- **6 12-Factor Configuration Files**: `12factors.toml` for all scoring modules
  - src/scoring/ntee_scorer/12factors.toml (680 lines)
  - src/scoring/schedule_i_voting/12factors.toml (510 lines)
  - src/scoring/grant_size_scoring/12factors.toml (375 lines)
  - src/scoring/composite_scorer_v2/12factors.toml (485 lines)
  - src/scoring/triage_queue/12factors.toml (455 lines)
  - src/scoring/reliability_safeguards/12factors.toml (612 lines)

- **Python Client Generation**: 13 files in `baml_client/` with all 25 scoring schemas as Python types

#### Phase 2: Foundation Network Tool BAML Conversion
- **13 BAML Schemas**: Complete foundation network intelligence (11 classes + 2 enums)
  - Bundling Output: 5 schemas (GranteeBundlingOutput, BundledGrantee, FoundationOverlap, ThematicCluster, FundingSource)
  - Co-funding Output: 4 schemas (CoFundingAnalysisOutput, FunderSimilarity, PeerFunderGroup, FunderRecommendation)
  - Input Models: 2 schemas (GranteeBundlingInput, CoFundingAnalysisInput)
  - Enums: 2 schemas (FundingStability, RecommendationType)

- **Import Wrapper**: `tools/foundation_grantee_bundling_tool.py` for hyphenated directory support

#### Phase 3: Testing Harness Modernization
- **4 Test Templates** (1,960+ lines total):
  - `test_framework/12factor_tools/test_tool_template.py` (400+ lines) - 24 tools
  - `test_framework/scoring_systems/test_scoring_template.py` (480+ lines) - 6 modules
  - `test_framework/network_intelligence/test_network_template.py` (520+ lines) - Network tools
  - `test_framework/api_integration/test_api_template.py` (560+ lines) - 40+ endpoints

- **Test Organization**: 4 test category directories with package structure
- **Testing Guide**: `test_framework/README_MODERNIZED_TESTING.md` (480+ lines)

#### Documentation
- `docs/PHASE1_BAML_CONVERSION_COMPLETE.md` (278 lines)
- `docs/PHASE1_SCORING_COMPLIANCE_SUMMARY.md` (234 lines)
- `docs/PHASE3_TESTING_HARNESS_MODERNIZATION.md` (526 lines)
- `docs/PHASES_1-3_COMPLETE_SUMMARY.md` (544 lines)
- `README.md` - Project overview and quick links
- `QUICK_START.md` - 5-minute quick start guide
- `CHANGELOG.md` - This file

### Changed
- **Foundation Network Router**: Re-enabled in `src/web/main.py` (was temporarily disabled)
- **Router Imports**: Updated `src/web/routers/foundation_network.py` to use wrapper module

### Fixed
- **Python Import Issue**: Resolved hyphenated directory name incompatibility with Python imports via wrapper module
- **16 API Endpoints**: Foundation network endpoints now operational

### Removed
- **Legacy Tests**: Moved 10 files from `test_framework/essential_tests/` → `test_framework/deprecated_tests/`
  - test_processor_suite.py → replaced by tool tests
  - test_ai_processors.py → replaced by AI tool tests
  - test_intelligence_tiers.py → replaced by depth tests
  - test_modal_system.py → deprecated
  - 6 other legacy test files

### Statistics
- **BAML Schemas**: 38 total (25 scoring + 13 network)
- **12-Factor Components**: 30 (24 tools + 6 modules)
- **Lines Created**: 4,070+ (schemas, templates, docs, wrappers)
- **Generated Files**: 13 (baml_client/ Python types)
- **Factor 4 Compliance**: 100% (all outputs BAML-validated)

### Git Tags
- `phases-1-3-complete` - BAML conversion and testing infrastructure milestone

---

## [2025-10-05] - Phase 9 Foundation Network Intelligence Complete

### Added
- **Foundation Network Intelligence System** (Phase 9 Week 9-10)
  - Multi-foundation grant bundling and co-funding analysis
  - NetworkX-powered graph analysis with Louvain community detection
  - 16 REST API endpoints for foundation network analysis
  - Foundation grantee bundling tool with 990-PF Schedule I processing

- **11 Network Dataclasses + 2 Enums** (8,646 lines):
  - GranteeBundlingInput, CoFundingAnalysisInput
  - BundledGrantee, FoundationOverlap, ThematicCluster
  - FunderSimilarity, PeerFunderGroup, FunderRecommendation
  - GranteeBundlingOutput, CoFundingAnalysisOutput
  - FundingStability enum, RecommendationType enum

### Statistics
- 16 API endpoints operational
- 8,646 lines of network intelligence code
- NetworkX graph analysis with centrality metrics
- Louvain community detection for peer funder groups

---

## [2025-09-30] - Phase 8 Nonprofit Workflow Solidification Complete

### Added
- **Profile Service Consolidation**: UnifiedProfileService with no locking
- **Tool 25: Web Intelligence Tool**: Scrapy-powered web scraping with 990 verification
  - Profile Builder ($0.05-0.10)
  - Opportunity Research ($0.15-0.25)
  - Foundation Research ($0.10-0.20)
  - Smart URL resolution with confidence scoring
  - 990 verification pipeline

- **BMF/990 Intelligence Pipeline**: 626K+ Form 990, 220K+ Form 990-PF
- **Profile Enhancement Orchestration**: Multi-step workflow engine
- **Data Quality Scoring**: Profile + opportunity scoring
- **Modernized Profile API**: Tool-based architecture

### Changed
- Profile service architecture (removed locking mechanism)
- Comprehensive integration test suite
- Test organization and structure

### Statistics
- 20/20 tasks complete
- Profile v2 API operational
- 100% nonprofit workflow coverage

---

## [2025-09-22] - Phase 7 Validation & Compliance Audit Complete

### Added
- **12-Factor Compliance Matrix**: 100% compliant across all 22 tools
- **Git Safety Checkpoint**: `pre-processor-removal` tag
- **Processor Migration Documentation**: Backward compatibility strategy

### Changed
- All 22 tools validated for compliance
- Stateless execution verified
- Structured outputs validated

### Statistics
- 100% 12-factor compliance
- 22 operational tools
- Complete compliance audit

---

## [2025-09-15] - Phase 6 API Integration Complete

### Added
- **Unified Tool Execution API**: `/api/v1/tools/*`
- **Tool Metadata API**: List, filter, and discover tools
- **Health Check Endpoints**: Monitoring and status
- **API Test Suite**: Comprehensive integration tests
- **OpenAPI Documentation**: Complete Swagger docs at `/api/docs`

### Statistics
- 40+ REST endpoints
- Complete API test coverage
- OpenAPI/Swagger documentation

---

## [2025-09-08] - Phase 5 Historical Analysis & Documentation Complete

### Added
- **Tool 22: Historical Funding Analyzer**: USASpending.gov analysis
  - Geographic distribution (state-level)
  - Temporal trend analysis (year-over-year)
  - Award size categorization
  - Competitive positioning

- **Tool 25: Web Intelligence Tool**: Web scraping capabilities
  - Respectful scraping (2s delay, robots.txt)
  - BAML-validated outputs
  - 990 verification pipeline

- **Documentation Consolidation**:
  - Root MD files reduced from 20+ to 3 (85% reduction)
  - Created docs/MIGRATION_HISTORY.md
  - Created docs/TWO_TOOL_ARCHITECTURE.md
  - Created docs/TIER_SYSTEM.md
  - Archived 16+ legacy docs

### Statistics
- 22 tools total (100% nonprofit core)
- Documentation reduction: 85%
- Complete historical analysis pipeline

---

## [2025-09-01] - Phase 4 Scoring & Reporting Tools Complete

### Added
- **Tool 20: Multi-Dimensional Scorer**: 5-stage dimensional scoring
  - 5 workflow stages (DISCOVER → PLAN → ANALYZE → EXAMINE → APPROACH)
  - Stage-specific weights (sum to 1.0)
  - 4 boost factors (financial, network, historical, risk)

- **Tool 21: Report Generator**: Professional templates
  - 4 templates (comprehensive, executive, risk, implementation)
  - DOSSIER structure (masters thesis-level)
  - HTML output with responsive design
  - Jinja2 template rendering

### Statistics
- 21 tools total (95% MVP)
- <0.05ms scoring performance
- $0.00 cost (algorithmic)

---

## [2025-08-25] - Phase 3 Supporting Intelligence Tools Complete

### Added
- **Tool 10: Financial Intelligence**: 15+ comprehensive metrics
- **Tool 11: Risk Intelligence**: 6-dimensional risk assessment
- **Tool 12: Network Intelligence**: Board network analysis
- **Tool 13: Schedule I Grant Analyzer**: Foundation patterns
- **Tool 14: Data Validator**: Quality and completeness
- **Tool 15: EIN Validator**: Format validation
- **Tool 16: Data Validator**: Schema compliance
- **Tool 17: BMF Discovery**: IRS Business Master File filtering
- **Tool 18: Data Export**: Multi-format export (JSON, CSV, Excel, PDF)
- **Tool 19: Grant Package Generator**: Application assembly

### Statistics
- 19 tools total (86% MVP)
- All supporting intelligence operational
- Complete data validation pipeline

---

## [2025-08-18] - Phase 2 Two-Tool Pipeline Complete

### Added
- **Tool 1: Opportunity Screening**: Mass screening with fast/thorough modes
  - Fast mode: $0.0004/opp, ~2 sec
  - Thorough mode: $0.02/opp, ~5 sec
  - 200 → ~10 selection pipeline

- **Tool 2: Deep Intelligence**: Comprehensive analysis
  - Essentials: $2.00, 15-20 min (includes network)
  - Premium: $8.00, 30-40 min (enhanced + dossier)
  - 4-stage analysis (DISCOVER → PLAN → ANALYZE → APPROACH)

- **Human Gateway**: Manual review interface specification
- **Workflow Engine**: Multi-tool orchestration with YAML definitions

### Replaced
- 8 legacy processors with 2 unified AI tools
- 87.5% processor reduction
- 73-81% cost reduction for users

### Statistics
- 11 tools total
- $21-81 typical pipeline cost
- 97-99% savings vs manual research

---

## [2025-08-11] - Phase 1 Foundation Infrastructure Complete

### Added
- **Tool Registry System**: Auto-discovery via `12factors.toml`
- **Base Tool Framework**: BaseTool, SyncBaseTool, ToolResult[T]
- **BAML Validator**: Structured output validation
- **Workflow Engine**: YAML-based multi-tool orchestration
- **9 XML/Data Tools**: 990 parsers, BMF filter, ProPublica enrichment

### Architecture
- 12-factor compliance framework
- Factor 4: Tools as Structured Outputs
- Factor 6: Stateless execution
- Factor 10: Single responsibility

### Statistics
- 9 tools operational
- 12-factor foundation established
- Workflow orchestration ready

---

## [2025-06-15] - Database Architecture Complete

### Added
- **Dual Database Architecture**:
  - Catalynx.db: Application data (profiles, opportunities)
  - Nonprofit_Intelligence.db: BMF/SOI intelligence (2M+ records)

- **BMF/SOI Intelligence Database**:
  - 752,732 organizations (BMF)
  - 671,484 Form 990 records
  - 235,374 Form 990-PF records
  - 411,235 Form 990-EZ records

- **DatabaseManager**: Unified SQLite operations with performance monitoring

### Changed
- BMF Discovery: CSV → Comprehensive SQL database
- 47.2x improvement in discovery results (10 → 472 orgs)

### Statistics
- 2.07M+ comprehensive records
- Sub-second query performance
- 6-8GB database size

---

## [2025-05-01] - Entity-Based Data Architecture

### Added
- **Entity-Based Organization**: 42 entities
  - Nonprofits: EIN-organized
  - Government: Opportunity/award ID
  - Foundations: Foundation ID

- **Entity Cache Manager**: Multi-entity data organization
- **Shared Analytics**: Cross-entity reuse

### Changed
- 70% efficiency improvement
- 85% cache hit rate

---

## [2025-04-01] - Initial Web Interface

### Added
- **FastAPI Backend**: Async REST API
- **Alpine.js Frontend**: Reactive SPA
- **Tailwind CSS**: Mobile-first design
- **Chart.js Analytics**: Data visualization

### Features
- Real-time updates via WebSocket
- WCAG 2.1 AA compliance
- OpenAPI documentation at `/api/docs`

---

## [2025-03-01] - Tier System Architecture

### Added
- **4-Tier Intelligence System**:
  - CURRENT ($0.75): 4-stage AI analysis
  - STANDARD ($7.50): + Historical patterns
  - ENHANCED ($22.00): + Network intelligence
  - COMPLETE ($42.00): + Policy analysis + dossier

### Architecture
- Dual design: Tab processors + tier services
- Shared foundation for comprehensive analysis

---

## [2025-02-01] - Processor System

### Added
- **18 Granular Processors**:
  - Data Fetchers: BMF, ProPublica, Grants.gov, USASpending
  - Analysis: Opportunity scorer, success scorer, network analyzer
  - AI Processing: Heavy/lite variants

### Statistics
- Sub-millisecond processing
- 100% functional
- 85% cache integration

---

## Legend

- **Added**: New features, tools, or capabilities
- **Changed**: Modifications to existing functionality
- **Fixed**: Bug fixes and issue resolutions
- **Removed**: Deprecated features or code
- **Statistics**: Key metrics and performance data
- **Git Tags**: Version markers and milestones

---

**Current Version**: 2025-10-09 Baseline
**Status**: Production-ready with 12-factor architecture
**Next**: Phase 4 - Comprehensive Testing (38+ test files)
