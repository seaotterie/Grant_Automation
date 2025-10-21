# 12-Factor Tool Architecture - Complete Mapping

**Document Version**: 2.0
**Last Updated**: 2025-10-21
**Status**: 24 Tools Operational in `tools/` directory

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Complete Tool Inventory](#complete-tool-inventory)
3. [3-Tab Workflow Mapping](#3-tab-workflow-mapping)
4. [Tool-to-Workflow Execution Order](#tool-to-workflow-execution-order)
5. [Legacy Processor Deprecation](#legacy-processor-deprecation)
6. [API Integration Guide](#api-integration-guide)
7. [Migration Roadmap](#migration-roadmap)

---

## Executive Summary

### Architecture Location
**CRITICAL**: All 12-factor tools are located in `tools/` directory at project root, NOT in `src/`.

```
Grant_Automation/
├── tools/                    ← 24 operational 12-factor tools HERE
│   ├── opportunity_screening_tool/
│   ├── deep_intelligence_tool/
│   ├── financial_intelligence_tool/
│   └── ... (21 more tools)
├── src/                     ← Service layer, legacy processors, API routers
│   ├── profiles/            ← Service layer (keep)
│   ├── discovery/           ← Service layer (keep)
│   ├── scoring/             ← Legacy processors (migrate/deprecate)
│   ├── analysis/            ← Legacy processors (migrate/deprecate)
│   └── processors/          ← Legacy processors (deprecate)
└── docs/                    ← Documentation
```

### Status Summary
- **24 Tools Operational**: All have `12factors.toml`, full Python implementation, BAML schemas, and tests
- **3-Tab Architecture**: Profiles → Screening → Intelligence
- **Dual System**: Tools (new) + Service Layer (keep) + Legacy Processors (deprecate)

---

## Complete Tool Inventory

### 1. XML Parser Tools (4 tools) - Foundation Data Layer

| # | Tool Name | Location | Purpose | Status |
|---|-----------|----------|---------|--------|
| - | **XML 990 Parser Tool** | `tools/xml-990-parser-tool/` | Regular nonprofits (≥$200K revenue) | ✅ Operational |
| - | **XML 990-PF Parser Tool** | `tools/xml-990pf-parser-tool/` | Private foundations + network analysis | ✅ Operational |
| - | **XML 990-EZ Parser Tool** | `tools/xml-990ez-parser-tool/` | Small nonprofits (<$200K revenue) | ✅ Operational |
| - | **XML Schedule Parser Tool** | `tools/xml-schedule-parser-tool/` | Schedule-specific parsing (A, B, I, etc.) | ✅ Operational |

**Extracts**: Board members, financial data, grants paid, governance indicators, investment portfolios

---

### 2. Core Workflow Tools (2 tools) - MAIN PIPELINE

| # | Tool Name | Location | Purpose | Cost | Time | Status |
|---|-----------|----------|---------|------|------|--------|
| 1 | **Opportunity Screening Tool** | `tools/opportunity_screening_tool/` | Mass screening (200 → 10-15) | Fast: $0.0004/opp<br>Thorough: $0.02/opp | Fast: 2s<br>Thorough: 5s | ✅ Operational |
| 2 | **Deep Intelligence Tool** | `tools/deep_intelligence_tool/` | Comprehensive analysis orchestrator | Essentials: $2.00<br>Premium: $8.00 | 15-40 min | ✅ Operational |

**Replaces**: 8 legacy processors (ai_lite_unified, ai_heavy_light, ai_heavy_deep, ai_heavy_researcher, 4 tier processors)

---

### 3. Intelligence Analysis Tools (5 tools) - Deep Analysis Layer

| # | Tool Name | Location | Purpose | Cost | Status |
|---|-----------|----------|---------|------|--------|
| 10 | **Financial Intelligence Tool** | `tools/financial_intelligence_tool/` | 15+ financial metrics, health rating, grant capacity | $0.03 | ✅ Operational |
| 11 | **Risk Intelligence Tool** | `tools/risk_intelligence_tool/` | 6-dimensional risk assessment | $0.02 | ✅ Operational |
| 12 | **Network Intelligence Tool** | `tools/network_intelligence_tool/` | Board network analysis, relationship mapping | $0.04 | ✅ Operational |
| 13 | **Schedule I Grant Analyzer Tool** | `tools/schedule_i_grant_analyzer_tool/` | Foundation grant-making patterns | $0.03 | ✅ Operational |
| 22 | **Historical Funding Analyzer Tool** | `tools/historical_funding_analyzer_tool/` | USASpending.gov pattern analysis, trends | $0.00 | ✅ Operational |

**Replaces**: Form990DataMiningEngine, NetworkIntelligenceEngine, FoundationIntelligenceEngine, board_network_analyzer.py, schedule_i_processor.py

---

### 4. Scoring & Reporting Tools (2 tools)

| # | Tool Name | Location | Purpose | Cost | Status |
|---|-----------|----------|---------|------|--------|
| 20 | **Multi-Dimensional Scorer Tool** | `tools/multi_dimensional_scorer_tool/` | 5-stage dimensional scoring (DISCOVER → PLAN → ANALYZE → EXAMINE → APPROACH) | $0.00 | ✅ Operational |
| 21 | **Report Generator Tool** | `tools/report_generator_tool/` | 4 professional templates (comprehensive, executive, risk, implementation) | $0.00 | ✅ Operational |

**Replaces**: discovery_scorer.py, success_scorer.py, ai_heavy_dossier_builder.py

---

### 5. Data Collection & Enrichment Tools (4 tools)

| # | Tool Name | Location | Purpose | Cost | Status |
|---|-----------|----------|---------|------|--------|
| 4 | **BMF Discovery Tool** | `tools/bmf_filter_tool/` | IRS Business Master File filtering and discovery | $0.00 | ✅ Operational |
| 5 | **Form 990 Analysis Tool** | `tools/form990_analysis_tool/` | Deep financial analysis of 990 data | $0.00 | ✅ Operational |
| 6 | **Form 990 ProPublica Tool** | `tools/form990_propublica_tool/` | ProPublica API data enrichment | $0.00 | ✅ Operational |
| 8 | **ProPublica API Enrichment Tool** | `tools/propublica_api_enrichment_tool/` | Additional ProPublica enrichment | $0.00 | ✅ Operational |

---

### 6. Support & Foundation Tools (6 tools)

| # | Tool Name | Location | Purpose | Cost | Status |
|---|-----------|----------|---------|------|--------|
| 7 | **Foundation Grant Intelligence Tool** | `tools/foundation_grant_intelligence_tool/` | Foundation grant-making intelligence analysis | $0.00 | ✅ Operational |
| 14 | **Foundation Grantee Bundling Tool** | `tools/foundation_grantee_bundling_tool/` | Co-funding analysis and grantee clustering | $0.00 | ✅ Operational |
| 16 | **Data Validator Tool** | `tools/data_validator_tool/` | Data quality and completeness validation | $0.00 | ✅ Operational |
| 17 | **EIN Validator Tool** | `tools/ein_validator_tool/` | EIN format validation and lookup | $0.00 | ✅ Operational |
| 18 | **Data Export Tool** | `tools/data_export_tool/` | Multi-format export (JSON, CSV, Excel, PDF) | $0.00 | ✅ Operational |
| 19 | **Grant Package Generator Tool** | `tools/grant_package_generator_tool/` | Application package assembly and timeline planning | $0.00 | ✅ Operational |

---

### 7. Web Intelligence Tools (1 tool)

| # | Tool Name | Location | Purpose | Cost | Status |
|---|-----------|----------|---------|------|--------|
| 25 | **Web Intelligence Tool** | `tools/web_intelligence_tool/` | Scrapy-powered web scraping (3 use cases: Profile Builder, Opportunity Research, Foundation Research) | $0.05-0.25 | ✅ Operational |

**3 Use Cases**:
1. Profile Builder: Scrape YOUR org's website ($0.05-0.10)
2. Opportunity Research: Scrape grantmaking nonprofits ($0.15-0.25)
3. Foundation Research: Scrape private foundations ($0.10-0.20)

---

## 3-Tab Workflow Mapping

### TAB 1: PROFILES (Profile Management & Enhancement)

**Purpose**: Create and enhance organization profiles

**Architecture**: Hybrid approach - 12-factor tools for generic tasks + service layer for profile-specific logic

#### Tools Used

##### Integrated 12-Factor Tools
- ✅ **Tool 17: EIN Validator Tool** (INTEGRATED)
  - EIN format validation before profile creation
  - Integration: `ProfileEnhancementOrchestrator._step_ein_validation()`
  - Validates format, detects invalid prefixes
  - Cost: $0.00 (no AI)
  - Status: **Active in workflow** (Step 0)

- ✅ **Tool 25: Web Intelligence Tool** (INTEGRATED)
  - Scrape YOUR organization's website for profile data
  - Integration: `POST /api/v2/profiles/{id}/enhance`
  - Cost: $0.05-0.10 per profile
  - Status: **Active in workflow** (Step 3)

##### Available But Not Used
- 🟡 **Tool 16: Data Validator Tool** (NOT USED)
  - Generic data validation tool
  - **Why not used**: Profile-specific validation requires deep nonprofit domain knowledge
  - **Alternative**: `ProfileQualityScorer` service layer (weighted scoring, confidence analysis, financial health checks)
  - Available for other use cases (opportunity validation, foundation data, etc.)

##### Supporting Services (Not Tools - Keep Active)
- `UnifiedProfileService` - Profile database CRUD operations
- `ProfileEnhancementOrchestrator` - Multi-step workflow coordination
- `ProfileQualityScorer` - **Profile-specific quality scoring** (replaces Tool 16 for profiles)
  - Weighted scoring: BMF (20%), 990 (35%), Tool25 (25%), Tool2 (20%)
  - Confidence-aware Tool 25 validation
  - Financial health analysis (margins, sustainability)
  - Contextual recommendations
- `DataCompletenessValidator` - **Multi-source completeness validation**

#### API Endpoints
- `POST /api/v2/profiles/create` - Create new profile
- `POST /api/v2/profiles/{id}/enhance` - Run Tool 25 (Profile Builder)
- `GET /api/v2/profiles/{id}/quality` - Get quality score
- `GET /api/v2/profiles` - List all profiles
- `GET /api/v2/profiles/{id}` - Get profile details

#### Workflow Execution Order
```
1. Create Profile
   └─→ UnifiedProfileService.create_profile()

2. Validate EIN Format (STEP 0 in orchestrator)
   └─→ Tool 17: EIN Validator Tool ✅ INTEGRATED
   └─→ Validates format, detects invalid prefixes
   └─→ Returns clean EIN or error

3. BMF Discovery (STEP 1)
   └─→ Query nonprofit_intelligence.db for organization data

4. Form 990 Query (STEP 2)
   └─→ Get financial data from 990 filings

5. Scrape Website (STEP 3)
   └─→ Tool 25: Web Intelligence Tool ✅ INTEGRATED
   └─→ Profile Builder use case

6. Quality Scoring & Validation
   └─→ ProfileQualityScorer.calculate_profile_quality()
   └─→ DataCompletenessValidator.validate_profile_completeness()
   └─→ Uses weighted scoring with domain knowledge
```

---

### TAB 2: SCREENING (Discovery & Opportunity Screening)

**Purpose**: Discover opportunities and screen 200 → 10-15 high-potential matches

#### Phase 1: Discovery

##### Tools Used
- ✅ **Tool 4: BMF Discovery Tool**
  - IRS Business Master File queries
  - Returns: 200-500 organizations
  - Cost: $0.00 (database query)

- ✅ **XML Parser Tools** (990, 990-PF, 990-EZ, Schedule)
  - Parse 990 data for discovered organizations
  - Extract: Financial data, NTEE codes, grant history, board members
  - Cost: $0.00 (parsing only)

##### Integration
- `POST /api/v2/profiles/{id}/discover` - BMF + 990 discovery

#### Phase 2: Scoring

##### Tools Used
- ✅ **Tool 20: Multi-Dimensional Scorer Tool**
  - 5-stage dimensional scoring
  - Stages: DISCOVER → PLAN → ANALYZE → EXAMINE → APPROACH
  - Cost: $0.00 (algorithmic)

- 🟡 **Composite Scorer V2** (in `src/scoring/` - needs migration)
  - 8-component foundation-nonprofit alignment
  - Used for: Foundation-specific matching only
  - Status: Operational but needs migration to `tools/`

#### Phase 3: Screening

##### Tools Used
- ✅ **Tool 1: Opportunity Screening Tool**
  - **Fast Mode**: 200 → 50 candidates ($0.0004/opp, 2 sec, $0.08 total)
  - **Thorough Mode**: 50 → 10-15 finalists ($0.02/opp, 5 sec, $1.00 total)
  - **Total Cost**: ~$1.08 for full 200 → 10-15 funnel

##### Integration
- `POST /api/workflows/screen-opportunities` - Tool 1 execution
- Request body:
  ```json
  {
    "opportunities": [...],
    "organization_profile": {...},
    "screening_mode": "fast" | "thorough",
    "minimum_threshold": 0.55,
    "max_recommendations": 15
  }
  ```

#### Phase 4: Web Research (Optional)

##### Tools Used
- ✅ **Tool 25: Web Intelligence Tool** (Opportunity Research use case)
  - Scrape GRANTMAKING nonprofits for grant opportunities
  - Enrich top candidates with additional intelligence
  - Cost: $0.15-0.25 per opportunity research

##### Integration
- `POST /api/v2/opportunities/{id}/research` - Tool 25 web research

#### API Endpoints
- `POST /api/v2/profiles/{id}/discover` - BMF + 990 discovery
- `POST /api/workflows/screen-opportunities` - Tool 1 screening
- `POST /api/v2/opportunities/{id}/research` - Tool 25 web research
- `PATCH /api/v2/opportunities/{id}/notes` - Save screening notes
- `POST /api/v2/opportunities/{id}/promote` - Promote to Intelligence tab

#### Workflow Execution Order
```
1. BMF Discovery
   └─→ Tool 4: BMF Discovery Tool
   └─→ Returns 200-500 organizations

2. 990 Data Enrichment
   └─→ XML Parser Tools (990, 990-PF, 990-EZ, Schedule)
   └─→ Adds financial data, NTEE codes, grant history

3. Initial Scoring
   └─→ Tool 20: Multi-Dimensional Scorer Tool
   └─→ 5-stage dimensional scores

4. Foundation Matching (foundations only)
   └─→ Composite Scorer V2
   └─→ 8-component alignment scores

5. Fast Screening
   └─→ Tool 1: Opportunity Screening Tool (Fast mode)
   └─→ 200 → 50 candidates ($0.08 total)

6. Thorough Screening
   └─→ Tool 1: Opportunity Screening Tool (Thorough mode)
   └─→ 50 → 10-15 finalists ($1.00 total)

7. Web Research (Optional)
   └─→ Tool 25: Web Intelligence Tool
   └─→ Enrich top 5-10 candidates

8. Human Gateway
   └─→ Manual review and selection
   └─→ Select ~10 opportunities for deep analysis
```

---

### TAB 3: INTELLIGENCE (Deep Analysis & Reports)

**Purpose**: Comprehensive deep analysis of ~10 selected opportunities

#### Phase 1: Deep Intelligence Analysis

##### Core Orchestrator
- ✅ **Tool 2: Deep Intelligence Tool**
  - Orchestrates comprehensive analysis
  - **Essentials Depth**: $2.00 user ($0.05 AI), 15-20 min
  - **Premium Depth**: $8.00 user ($0.10 AI), 30-40 min
  - Integrates: Tools 10, 11, 12, 13, 22

##### Component Analysis Tools
- ✅ **Tool 10: Financial Intelligence Tool**
  - 15+ comprehensive financial metrics
  - Financial health rating and scoring
  - Grant capacity assessment with match capability
  - Cost: $0.03 per analysis

- ✅ **Tool 11: Risk Intelligence Tool**
  - 6-dimensional risk assessment
  - Dimensions: Eligibility, competition, capacity, timeline, financial, compliance
  - Multi-level risk categorization (minimal → critical)
  - Go/no-go recommendations with confidence
  - Cost: $0.02 per analysis

- ✅ **Tool 12: Network Intelligence Tool**
  - Board member profiling with centrality metrics
  - Network cluster identification
  - Relationship pathway mapping (direct and indirect)
  - Target funder connection analysis
  - Strategic cultivation strategies
  - Cost: $0.04 per analysis

- ✅ **Tool 13: Schedule I Grant Analyzer Tool**
  - Foundation grant-making pattern analysis
  - Category and geographic distribution
  - Grant size analysis with competitive sizing
  - Recipient profiling
  - Organization match analysis
  - Cost: $0.03 per analysis

- ✅ **Tool 22: Historical Funding Analyzer Tool**
  - USASpending.gov data analysis
  - Geographic distribution (state-level funding breakdown)
  - Temporal trend analysis with YoY growth
  - Award size categorization (micro → major)
  - Competitive position insights
  - Cost: $0.00 (data analysis only)

#### Phase 2: Reporting & Package Generation

##### Reporting Tools
- ✅ **Tool 21: Report Generator Tool**
  - 4 professional templates:
    - Comprehensive Report (DOSSIER structure, 20+ pages)
    - Executive Summary (2-3 pages)
    - Risk Assessment Report (focused risk analysis)
    - Implementation Plan (tactical roadmap)
  - HTML output with responsive design
  - Template-based rendering with Jinja2
  - Cost: $0.00 (no AI calls)

- ✅ **Tool 19: Grant Package Generator Tool**
  - Application package assembly
  - Document checklist management
  - Submission timeline planning
  - Package status tracking
  - Cost: $0.00 (no AI calls)

#### API Endpoints
- `POST /api/workflows/deep-intelligence` - Tool 2 orchestration
- `POST /api/intelligence/financial` - Tool 10 direct call
- `POST /api/intelligence/risk` - Tool 11 direct call
- `POST /api/intelligence/network` - Tool 12 direct call
- `POST /api/intelligence/schedule-i` - Tool 13 direct call
- `POST /api/intelligence/historical` - Tool 22 direct call
- `POST /api/reports/generate` - Tool 21 report generation
- `POST /api/packages/create` - Tool 19 package assembly

#### Workflow Execution Order
```
1. Deep Intelligence Orchestration
   └─→ Tool 2: Deep Intelligence Tool
   └─→ Depth selection: Essentials ($2) or Premium ($8)

2. Parallel Analysis Execution
   ├─→ Tool 10: Financial Intelligence
   │   └─→ Financial metrics, health rating, grant capacity
   │
   ├─→ Tool 11: Risk Intelligence
   │   └─→ 6-dimensional risk assessment, go/no-go
   │
   ├─→ Tool 12: Network Intelligence
   │   └─→ Board network analysis, relationship pathways
   │
   ├─→ Tool 13: Schedule I Grant Analyzer
   │   └─→ Foundation grant patterns, recipient analysis
   │
   └─→ Tool 22: Historical Funding Analyzer
       └─→ USASpending.gov trends, competitive positioning

3. Report Generation
   └─→ Tool 21: Report Generator Tool
   └─→ Comprehensive DOSSIER output (20+ pages)

4. Package Assembly
   └─→ Tool 19: Grant Package Generator Tool
   └─→ Application materials, timeline, checklist

5. Human Decision
   └─→ Review comprehensive intelligence
   └─→ Go/No-Go decision
   └─→ Proposal development
```

---

## Tool-to-Workflow Execution Order

### Complete End-to-End Flow

```
═══════════════════════════════════════════════════════════════════
                    PROFILES TAB
═══════════════════════════════════════════════════════════════════
1. Create Profile → UnifiedProfileService
2. Validate EIN → Tool 17 (EIN Validator)
3. Scrape Website → Tool 25 (Profile Builder)
4. Validate Data → Tool 16 (Data Validator)
5. Quality Check → ProfileQualityScorer
                              ↓
═══════════════════════════════════════════════════════════════════
                    SCREENING TAB
═══════════════════════════════════════════════════════════════════
6. BMF Discovery → Tool 4 (BMF Discovery)
   └─→ Returns: 200-500 organizations

7. 990 Parsing → XML Parsers (990, 990-PF, 990-EZ, Schedule)
   └─→ Adds: Financial data, NTEE, grants, board members

8. Initial Scoring → Tool 20 (Multi-Dimensional Scorer)
   └─→ 5-stage dimensional scores

9. Foundation Matching → Composite Scorer V2 (foundations only)
   └─→ 8-component alignment scores

10. Fast Screening → Tool 1 (Fast mode)
    └─→ 200 → 50 candidates ($0.08 total, 2s each)

11. Thorough Screening → Tool 1 (Thorough mode)
    └─→ 50 → 10-15 finalists ($1.00 total, 5s each)

12. Web Research → Tool 25 (Opportunity Research, optional)
    └─→ Enrich top 5-10 candidates

13. Human Gateway → Manual review and selection
    └─→ Select ~10 opportunities for deep analysis
                              ↓
═══════════════════════════════════════════════════════════════════
                  INTELLIGENCE TAB
═══════════════════════════════════════════════════════════════════
14. Deep Intelligence Orchestration → Tool 2
    └─→ Depth: Essentials ($2) or Premium ($8)

15. Parallel Analysis (5 tools run concurrently):
    ├─→ Tool 10: Financial Intelligence ($0.03)
    ├─→ Tool 11: Risk Intelligence ($0.02)
    ├─→ Tool 12: Network Intelligence ($0.04)
    ├─→ Tool 13: Schedule I Grant Analyzer ($0.03)
    └─→ Tool 22: Historical Funding Analyzer ($0.00)

16. Report Generation → Tool 21
    └─→ Comprehensive DOSSIER (20+ pages)

17. Package Assembly → Tool 19
    └─→ Application materials, timeline, checklist

18. Human Decision → Go/No-Go → Proposal Development
```

---

## Legacy Processor Deprecation

### Category 1: Can Deprecate NOW (Tools Replace Them)

| Legacy Processor | Replaced By | Location | Action |
|-----------------|-------------|----------|--------|
| `discovery_scorer.py` | Tool 20 (Multi-Dimensional Scorer) | `src/scoring/` | ❌ Move to `_deprecated/` |
| `track_specific_scorer.py` | Tool 1 (Opportunity Screening) | `src/scoring/` | ❌ Move to `_deprecated/` |
| `form_990_data_mining_engine.py` | Tool 10 (Financial Intelligence) | `src/analysis/` | ❌ Move to `_deprecated/` |
| `network_intelligence_engine.py` | Tool 12 (Network Intelligence) | `src/analysis/` | ❌ Move to `_deprecated/` |
| `foundation_intelligence_engine.py` | Tool 13 (Schedule I Analyzer) | `src/analysis/` | ❌ Move to `_deprecated/` |
| `ai_heavy_dossier_builder.py` | Tool 21 (Report Generator) | `src/analysis/` | ❌ Move to `_deprecated/` |
| `financial_scorer.py` | Tool 10 (Financial Intelligence) | `src/scoring/` | ❌ Move to `_deprecated/` |
| `board_network_analyzer.py` | Tool 12 (Network Intelligence) | `src/scoring/` | ❌ Move to `_deprecated/` |
| `schedule_i_processor.py` | Tool 13 (Schedule I Analyzer) | `src/scoring/` | ❌ Move to `_deprecated/` |

**Timeline**: Move to `src/processors/_deprecated/` in Week 3

### Category 2: Migration Needed (Partial 12-Factor)

| Component | Has 12factors.toml? | Action | Priority |
|-----------|-------------------|--------|----------|
| `src/scoring/composite_scorer_v2/` | ✅ Yes | Migrate to `tools/composite_scorer_tool/` | 🔴 HIGH |
| `src/scoring/ntee_scorer/` | ✅ Yes | Integrate into Tool 20 or Tool 1 | 🟡 MEDIUM |
| `src/scoring/schedule_i_voting/` | ✅ Yes | Integrate into Tool 13 | 🟡 MEDIUM |
| `src/scoring/grant_size_scoring/` | ✅ Yes | Integrate into Tool 10 | 🟡 MEDIUM |
| `src/scoring/reliability_safeguards/` | ✅ Yes | Integrate into Tool 11 | 🟡 MEDIUM |
| `src/scoring/triage_queue/` | ✅ Yes | Build as Tool 23 (Triage Queue Tool) | 🟢 LOW |

**Timeline**: Complete migration in Week 2

### Category 3: Keep Active (Service Layer - NOT Tools)

| Service | Location | Purpose | Status |
|---------|----------|---------|--------|
| `UnifiedProfileService` | `src/profiles/unified_service.py` | Profile database CRUD | ✅ Keep |
| `ProfileEnhancementOrchestrator` | `src/profiles/orchestration.py` | Workflow coordination | ✅ Keep |
| `ProfileQualityScorer` | `src/profiles/quality_scoring.py` | Quality assessment | ✅ Keep |
| BMF/990 Database Queries | `src/discovery/` | Data source access | ✅ Keep |
| Data Collection Processors | `src/processors/data_collection/` | Grants.gov, USASpending fetchers | ✅ Keep |

**Rationale**: These are service layer components, not tools. They provide infrastructure and coordination.

### Category 4: Already Deprecated

| Processor | Status | Location |
|-----------|--------|----------|
| Old AI processors | ✅ Moved | `src/processors/_deprecated/analysis/` |
| Legacy export managers | ✅ Moved | `src/processors/_deprecated/export/` |
| Old visualization code | ✅ Moved | `src/processors/_deprecated/visualization/` |

---

## API Integration Guide

### Tool Loading Pattern

```python
from src.workflows.tool_loader import ToolLoader

# Initialize tool loader
tool_loader = ToolLoader(tools_directory="tools/")

# Load a tool
screening_tool = tool_loader.load_tool("opportunity-screening-tool")

# Execute tool
result = await screening_tool.execute({
    "opportunities": opportunities,
    "organization_profile": profile,
    "screening_mode": "thorough"
})
```

### FastAPI Router Integration

```python
from fastapi import APIRouter
from src.workflows.tool_loader import ToolLoader

router = APIRouter(prefix="/api/tools")
tool_loader = ToolLoader()

@router.post("/screen")
async def screen_opportunities(request: ScreeningRequest):
    tool = tool_loader.load_tool("opportunity-screening-tool")
    result = await tool.execute(request.dict())
    return result
```

### Available API Endpoints

#### Profile APIs
- `POST /api/v2/profiles/create`
- `POST /api/v2/profiles/{id}/enhance` - Tool 25 (Profile Builder)
- `GET /api/v2/profiles/{id}/quality` - Quality scoring

#### Discovery & Screening APIs
- `POST /api/v2/profiles/{id}/discover` - Tool 4 (BMF Discovery) + XML Parsers
- `POST /api/workflows/screen-opportunities` - Tool 1 (Screening)
- `POST /api/v2/opportunities/{id}/research` - Tool 25 (Web Research)

#### Intelligence APIs
- `POST /api/workflows/deep-intelligence` - Tool 2 (Orchestrator)
- `POST /api/intelligence/financial` - Tool 10
- `POST /api/intelligence/risk` - Tool 11
- `POST /api/intelligence/network` - Tool 12
- `POST /api/intelligence/schedule-i` - Tool 13
- `POST /api/intelligence/historical` - Tool 22

#### Reporting APIs
- `POST /api/reports/generate` - Tool 21 (Report Generator)
- `POST /api/packages/create` - Tool 19 (Package Generator)

---

## Migration Roadmap

### Week 1: Navigation & Integration (Current)
- ✅ Create this comprehensive mapping document
- 🔲 Fix all `switchStage()` button references in `index.html`
- 🔲 Add profile context display to Screening tab
- 🔲 Wire screening-module.js to Tool 1 API endpoint
- 🔲 Test end-to-end: Profiles → Screening → Intelligence

### Week 2: Tool Integration & Migration
- 🔲 Migrate Composite Scorer V2 to `tools/composite_scorer_tool/`
- 🔲 Integrate NTEE Scorer into Tool 20 or Tool 1
- 🔲 Integrate Schedule I Voting into Tool 13
- 🔲 Integrate Grant Size Scoring into Tool 10
- 🔲 Integrate Reliability Safeguards into Tool 11
- 🔲 Test Tool 1 + Tool 2 end-to-end pipeline
- 🔲 Verify all 24 tools callable via API

### Week 3: Processor Deprecation
- 🔲 Move 9 legacy processors to `src/processors/_deprecated/`
- 🔲 Update all imports to use tools instead of processors
- 🔲 Update API routers to call tools directly
- 🔲 Run comprehensive regression test suite
- 🔲 Document migration in CHANGELOG

### Week 4: Documentation & Production Prep
- 🔲 Update `CLAUDE.md` to reflect `tools/` directory structure
- 🔲 Update `tools/TOOLS_INVENTORY.md` (9 → 24 tools)
- 🔲 Create migration guide for future tool development
- 🔲 Production deployment preparation
- 🔲 Performance benchmarking
- 🔲 Security audit

---

## Appendix

### Tool Naming Convention
- Directory: `{tool_name}_tool/` (snake_case with `_tool` suffix)
- Python module: `{tool_name}_tool.py` (matches directory name)
- Class: `{ToolName}Tool` (PascalCase with `Tool` suffix)

### File Structure Standard
```
tool_name_tool/
├── 12factors.toml          # 12-factor compliance configuration
├── README.md               # Tool-specific documentation
├── app/
│   ├── __init__.py
│   ├── {tool_name}_tool.py # Main tool implementation
│   └── models.py           # Pydantic models (optional)
├── baml_src/               # BAML schemas for structured outputs
│   └── {tool_name}.baml
└── tests/
    ├── __init__.py
    └── test_{tool_name}_tool.py
```

### Quality Standards
All 24 operational tools meet these standards:
- ✅ 12-factor compliance (documented in `12factors.toml`)
- ✅ Structured outputs (BAML schemas)
- ✅ Stateless execution
- ✅ Fast startup (<100ms target)
- ✅ Comprehensive tests
- ✅ Type hints (Python 3.10+)
- ✅ Async support where applicable

---

**Document Maintainer**: Catalynx Development Team
**Review Cycle**: Weekly during Phase 9
**Next Review**: 2025-10-28
