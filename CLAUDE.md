# Catalynx - Grant Research Intelligence Platform

## SYSTEM STATUS: PHASE 7 COMPLETE - VALIDATION & COMPLIANCE AUDIT ✅

**Production-ready grant intelligence platform** with 4-tier business packages ($0.75-$42.00), entity-based data architecture, modern web interface, and **12-factor tool transformation complete**. Phase 7 milestone: **ALL 22 TOOLS VALIDATED, COMPLIANCE AUDIT COMPLETE**.

### 12-Factor Transformation Status (Week 8 of 11 - Revised Plan V3.1)
- **Progress**: Phase 7 Complete - Validation & Compliance Audit
- **Completed Tools**: 22/22 operational (100% of nonprofit core)
- **Compliance**: 100% 12-factor compliant across all tools
- **Architecture**: Complete intelligence pipeline with REST API layer
- **Timeline**: 11 weeks total, on track for production completion

**Phase 7 Achievement - Validation & Compliance**:
- ✅ 12-Factor Compliance Matrix (100% compliant)
- ✅ All 22 tools have 12factors.toml files
- ✅ Stateless execution verified
- ✅ Structured outputs validated
- ✅ Git safety checkpoint (`pre-processor-removal` tag)
- ✅ Processor migration status documented
- ✅ Backward compatibility strategy defined

**Phase 6 Achievement - API Integration**:
- ✅ Unified Tool Execution API (`/api/v1/tools/*`)
- ✅ List tools with filtering (category, status)
- ✅ Get tool metadata and schemas
- ✅ Execute any tool via REST API
- ✅ Health check and monitoring endpoints
- ✅ Comprehensive API test suite
- ✅ Complete API documentation (OpenAPI/Swagger)

**Phase 5 Achievement - Historical Analysis & Documentation**:

**Tool 22: Historical Funding Analyzer Tool** ✅
- USASpending.gov data analysis with funding pattern detection
- Geographic distribution analysis (state-level funding breakdown)
- Temporal trend analysis with year-over-year growth calculations
- Award size categorization (micro → small → medium → large → major)
- Competitive position insights and recommendations
- Performance: 4-5ms per analysis, $0.00 cost (data analysis only)
- Replaces: Historical analysis portions of tier processors

**Tool 25: Web Intelligence Tool** ✅
- **Scrapy-powered web scraping** for nonprofit intelligence gathering
- **3 Use Cases**: Profile Builder ($0.05-0.10), Opportunity Research ($0.15-0.25), Foundation Research ($0.10-0.20)
- **Use Case 1**: Profile Builder - Scrape YOUR organization's website for profile data
- **Use Case 2**: Opportunity Research - Scrape grantmaking nonprofits (United Way, community foundations) for grant opportunities
- **Use Case 3**: Foundation Research - Scrape private foundations (990-PF) for grant opportunities
- **Smart URL Resolution**: User → 990 → GPT priority with confidence scoring
- **990 Verification Pipeline**: Cross-validates web data against IRS tax filings
- **Respectful Scraping**: 2s delay, robots.txt compliance, user-agent identification
- **Structured Outputs**: BAML schemas with Pydantic validation
- Integration: Profile Builder (POST /api/profiles/fetch-ein), Tool 2 (Deep Intelligence), Tool 13 (Schedule I)
- Performance: 10-60s execution, 85-95% accuracy with 990 verification
- Replaces: verification_enhanced_scraper.py (enhanced with Scrapy framework)

**Documentation Consolidation** ✅
- Root MD files reduced from 20+ to 3 (85% reduction)
- Created docs/MIGRATION_HISTORY.md (complete transformation timeline)
- Created docs/TWO_TOOL_ARCHITECTURE.md (architecture overview)
- Created docs/TIER_SYSTEM.md (consolidated tier documentation)
- Archived 16+ legacy documentation files

**Phase 4 Achievement - Scoring & Reporting Tools**:

**Tool 20: Multi-Dimensional Scorer Tool** ✅
- 5 workflow stages (DISCOVER → PLAN → ANALYZE → EXAMINE → APPROACH)
- Stage-specific dimensional weights (5 dimensions per stage, weights sum to 1.0)
- 4 boost factors (financial +10%, network +15%, historical +12%, risk +8%)
- Confidence calculation based on data quality + enhancements
- Performance: <0.05ms per score, $0.00 cost (algorithmic)
- Replaces: discovery_scorer.py, success_scorer.py

**Tool 21: Report Generator Tool** ✅
- 4 professional templates (comprehensive, executive, risk, implementation)
- DOSSIER structure (masters thesis-level comprehensive analysis)
- HTML output with responsive design and professional styling
- Template-based rendering with Jinja2
- Performance: 1-2s per report, $0.00 cost (no AI calls)
- Replaces: N/A (new capability)

**Completed Phases**:
- ✅ Phase 1 (Week 1): Foundation infrastructure, tool framework, workflow engine
- ✅ Phase 2 (Week 2-3): Two unified AI tools operational (11 tools total)
- ✅ Phase 3 (Week 4): All supporting tools operational (19 tools total, 86% MVP)
- ✅ Phase 4 (Week 5): Scoring & reporting foundation (21 tools total, 95% MVP)
- ✅ Phase 5 (Week 6): Historical analysis & documentation (22 tools total, 100% nonprofit core)
- ✅ Phase 6 (Week 7): API Integration & Testing (Unified Tool Execution API)
- ✅ Phase 7 (Week 8): Validation & Compliance Audit (100% 12-factor compliant)
- ✅ Phase 8 (Week 9): Nonprofit Workflow Solidification (20/20 tasks complete, profile v2 API operational)

**Phase 8 Achievement - Nonprofit Workflow Solidification**:
- ✅ Profile service consolidation (UnifiedProfileService, no locking)
- ✅ Tool 25 integration (Scrapy-powered web intelligence)
- ✅ BMF/990 intelligence pipeline (626K+ Form 990, 220K+ Form 990-PF)
- ✅ Profile enhancement orchestration (multi-step workflow engine)
- ✅ Data quality scoring system (profile + opportunity scoring)
- ✅ Modernized profile API endpoints (tool-based architecture)
- ✅ Comprehensive test suite (integration tests + test organization)

**Current**: Phase 8 Complete - All 20 tasks operational
**Next**: Phase 9 - Desktop UI modernization, government opportunity tools, production deployment

**Phase 2 Achievement - Two-Tool Pipeline**:

**Tool 1: Opportunity Screening Tool** ✅
- Fast mode: $0.0004/opportunity, ~2 sec (PLAN equivalent)
- Thorough mode: $0.02/opportunity, ~5 sec (ANALYZE equivalent)
- Mass screening: 200 opportunities → ~10 selected
- Replaces: 2 processors (ai_lite_unified, ai_heavy_light)

**Human Gateway**:
- Manual review and strategic selection
- Web scraping for additional context
- Priority ranking and focus area selection

**Tool 2: Deep Intelligence Tool** ✅
- Essentials depth: $2.00 user ($0.05 AI), 15-20 min - **includes network intelligence**
- Premium depth: $8.00 user ($0.10 AI), 30-40 min - enhanced features + dossier
- Network analysis included in base tier (was $6.50 add-on)
- Comprehensive analysis: ~10 selected opportunities
- Replaces: 6 processors (ai_heavy_deep, ai_heavy_researcher, 4 tier processors)
- **New**: True AI cost transparency with 40-80x platform value markup

**Pipeline Economics** (NEW TRUE-COST PRICING):
- Stage 1: $0.68 for 200 opportunities (screening)
- Stage 2: $20-80 typical (10 opportunities × $2-8/each)
- Total: ~$21-81 vs. $800-1,600 manual research
- **Savings**: 97-99% vs consultant rates
- Result: 87.5% processor reduction + 73-81% cost reduction for users

**Phase 3 Achievement - Supporting Intelligence Tools**:

**Tool 10: Financial Intelligence Tool** ✅
- 15+ comprehensive financial metrics (liquidity, efficiency, sustainability)
- Financial health rating and scoring
- Grant capacity assessment with match capability
- AI-enhanced strategic insights
- Cost: $0.03 per analysis
- Replaces: financial_scorer.py

**Tool 11: Risk Intelligence Tool** ✅
- 6 dimensional risk assessments (eligibility, competition, capacity, timeline, financial, compliance)
- Multi-level risk categorization (minimal to critical)
- Prioritized mitigation strategies
- Go/no-go recommendations with confidence levels
- Cost: $0.02 per analysis
- Replaces: risk_assessor.py

**Tool 12: Network Intelligence Tool** ✅
- Board member profiling with centrality metrics
- Network cluster identification
- Relationship pathway mapping (direct and indirect)
- Target funder connection analysis
- Strategic cultivation strategies
- Cost: $0.04 per analysis
- Replaces: board_network_analyzer.py, enhanced_network_analyzer.py, optimized_network_analyzer.py

**Tool 13: Schedule I Grant Analyzer Tool** ✅
- Foundation grant-making pattern analysis
- Category and geographic distribution
- Grant size analysis with competitive sizing
- Recipient profiling
- Organization match analysis
- Cost: $0.03 per analysis
- Replaces: schedule_i_processor.py, funnel_schedule_i_analyzer.py

**Tool 14: Data Validator Tool** ✅
- Required field validation
- Type checking
- Completeness and quality scoring
- Cost: $0.00 (no AI calls)

**Tool 16: Data Validator Tool** ✅
- Required field validation
- Type checking and validation
- Completeness and quality scoring
- Schema compliance verification
- Cost: $0.00 (no AI calls)
- Replaces: data_validator.py
- **Note**: Available but not used in PROFILES workflow (ProfileQualityScorer provides profile-specific domain intelligence instead)

**Tool 17: EIN Validator Tool** ✅ **[INTEGRATED IN PROFILES]**
- **EIN format validation (Step 0 in profile building workflow)**
- Invalid prefix detection
- Organization lookup capability
- Cost: $0.00 (no AI calls)
- Replaces: ein_lookup.py
- **Integration**: ProfileEnhancementOrchestrator._step_ein_validation()

**Tool 4: BMF Discovery Tool** ✅
- IRS Business Master File filtering
- Multi-criteria nonprofit discovery
- Geographic and NTEE code filtering
- Financial threshold filtering
- Cost: $0.00 (no AI calls)
- Replaces: bmf_filter.py

**Tool 18: Data Export Tool** ✅
- Multi-format export (JSON, CSV, Excel, PDF)
- Template-based formatting
- Batch export capabilities
- Custom field selection
- Cost: $0.00 (no AI calls)
- Replaces: export_manager.py

**Tool 19: Grant Package Generator Tool** ✅
- Application package assembly
- Document checklist management
- Submission timeline planning
- Package status tracking
- Cost: $0.00 (no AI calls)
- Replaces: grant_package_generator.py

**Phase 4 Achievement - Workflow Integration** ⚙️:

**Workflow Engine Infrastructure**:
- YAML-based workflow definitions with dependency management
- Dynamic tool loader with instance caching
- Parallel execution of independent steps
- Context variable substitution (${context.var}, ${steps.step.output})
- Comprehensive error handling and retry logic

**Workflow Definitions**:
1. **opportunity_screening.yaml** - Two-stage screening funnel
   - Fast screening (200 opps → 50 candidates)
   - Thorough screening (50 → 10-15 recommended)
   - Cost: ~$1-2 for full pipeline

2. **deep_intelligence.yaml** - Comprehensive analysis workflow
   - Multi-tool orchestration (9 steps)
   - Depth-configurable (quick → complete)
   - Financial, network, risk intelligence
   - Package outline generation
   - Cost: $0.75-$42.00 per opportunity

**API Endpoints** (`/api/workflows/`):
- `POST /execute` - Execute any workflow by name
- `GET /status/{execution_id}` - Monitor workflow progress
- `GET /results/{execution_id}` - Retrieve completed results
- `GET /list` - List available workflows
- `POST /screen-opportunities` - Convenience endpoint for screening
- `POST /deep-intelligence` - Convenience endpoint for deep analysis

**Human Gateway Specification**:
- Screening results dashboard with sortable/filterable views
- Web research enhancement panel
- Strategic selection interface with cost calculator
- Batch depth configuration
- Comparison and decision support tools
- Real-time workflow execution monitoring

**Technical Implementation**:
- Tool loader: `src/workflows/tool_loader.py` - Dynamic tool loading and execution
- Workflow engine: `src/workflows/workflow_engine.py` - Multi-tool orchestration
- API router: `src/web/routers/workflows.py` - FastAPI endpoints
- Gateway spec: `src/workflows/HUMAN_GATEWAY_SPEC.md` - Interface specification

**Completed Phases**:
- ✅ Phase 1 (Week 1): Foundation infrastructure, tool framework, workflow engine
- ✅ Phase 2 (Week 2-3): Two unified AI tools operational (11 tools total)
- ✅ Phase 3 (Week 4): All supporting tools operational (19 tools total, 100% MVP complete)
- ⚙️ Phase 4 (Week 5): Workflow integration - Engine, API, and gateway spec complete

**Next**: Complete human gateway web interface and end-to-end testing

## CRITICAL: GPT-5 MODEL CONFIGURATION

**MANDATORY REQUIREMENT**: System uses GPT-5 models exclusively - DO NOT change to GPT-4.

**Configuration Files**:
- `.env`: AI_LITE_MODEL, AI_HEAVY_MODEL, AI_RESEARCH_MODEL (all GPT-5 variants)
- `src/core/openai_service.py`: GPT-5 validation and cost tracking
- All processors: Optimized for GPT-5 architecture and token limits

**Why GPT-5**: Better performance, cost-effectiveness, and system optimization vs GPT-4 alternatives.

## CORE SYSTEM CAPABILITIES

### 2-Tier Intelligence System (TRUE COST PRICING)
- **ESSENTIALS ($2.00)**: Complete 4-stage AI analysis + **network intelligence** + historical/geographic insights (15-20 min) | AI Cost: $0.05
- **PREMIUM ($8.00)**: + Enhanced network pathways + policy analysis + strategic consulting + comprehensive dossier (30-40 min) | AI Cost: $0.10

**Why 2 Tiers?** Previous 4-tier system ($0.75 → $7.50 → $22 → $42) based on consultant rates, not AI costs. New pricing reflects true AI API costs ($0.05-0.10) with transparent platform value markup (40-80x). Network intelligence now INCLUDED in base tier (was $6.50 add-on). See [TIER_CONSOLIDATION_RATIONALE.md](docs/TIER_CONSOLIDATION_RATIONALE.md) for full analysis.

### Dual Architecture Design
- **Tab Processors**: 18 granular components for custom workflows ($0.0004-$0.20 each)
- **Tier Services**: Complete business packages utilizing tab processors internally
- **Entity-Based Data**: EIN/ID organization achieving 70% efficiency improvement
- **Performance**: Sub-millisecond processing, 85% cache hit rate, 0 critical errors

## DATA ARCHITECTURE

### Entity-Based Organization (42 Entities)
- **Nonprofits**: EIN-organized with 990 filings, board data, NTEE codes (`data/source_data/nonprofits/{EIN}/`)
- **Government**: Opportunity/award ID structure with Grants.gov and USASpending data (`data/source_data/government/`)
- **Foundations**: Foundation ID organization with 990-PF structure (`data/source_data/foundations/`)

### Core Components
- **Entity Cache Manager** (`src/core/entity_cache_manager.py`) - Multi-entity data organization
- **Shared Analytics** (`src/analytics/`) - Financial and network analysis with cross-entity reuse
- **Entity Services** (`src/discovery/`, `src/profiles/`) - Discovery and profile analysis using shared data

## DATABASE ARCHITECTURE (PHASE 8 COMPLETE - BMF/SOI INTELLIGENCE) ✅

### Dual Database Architecture - Application + Intelligence
**Status**: **PRODUCTION READY** - Complete nonprofit financial intelligence platform

### 1. Application Database (Catalynx.db)
- **DatabaseManager** (`src/database/database_manager.py`) - Unified SQLite operations with performance monitoring
- **Schema**: Profiles, Opportunities, AI Processing Costs, Export Records, System Metrics
- **Performance**: Sub-second operations with millisecond precision tracking
- **Monitoring**: Duration logging, error tracking, operation metrics

### 2. Intelligence Database (Nonprofit_Intelligence.db) - NEW ✨
**Source Data**: IRS Business Master File (BMF) + Statistics of Income (SOI) Extracts
**Coverage**: 2M+ organizations across 4 comprehensive tables
**Purpose**: Advanced nonprofit financial intelligence and grant research capabilities

#### BMF/SOI Database Schema
```sql
-- Master organizational index
bmf_organizations      -- 752,732 records (all tax-exempt orgs)
├── Primary: EIN, name, NTEE code, location, classification
├── Financial: Asset/income amounts, revenue data
└── Indexes: State, NTEE, foundation code for fast discovery

-- Multi-year SOI financial data (2022-2024)
form_990              -- 671,484 records (large nonprofits ≥$200K revenue)
├── Revenue/Expenses: 190+ detailed financial fields
├── Grants: Government/individual grant distributions
├── Assets/Liabilities: Complete balance sheet data
└── Operational: Program activities, compliance flags

form_990pf            -- 235,374 records (private foundations)
├── Grant Making: Distribution amounts, future grants
├── Investments: Portfolio composition, fair market values
├── Requirements: Distribution requirements, payout ratios
└── Foundation Intelligence: Grant capacity analysis

form_990ez            -- 411,235 records (smaller nonprofits <$200K)
├── Simplified: Core financial data for smaller orgs
├── Revenue/Expenses: Essential financial metrics
└── Public Support: Community foundation analysis
```

#### Performance Statistics
- **Total Records**: 2.07M+ comprehensive nonprofit intelligence
- **Query Performance**: Sub-second with strategic indexing
- **Database Size**: 6-8GB with full coverage
- **Financial Intelligence**: 47.2x improvement in discovery results (10 → 472 orgs)
- **Grant Research**: Foundation payout analysis and capacity scoring

#### Advanced Discovery Capabilities
```python
# Enhanced BMF discovery with financial intelligence
bmf_results = bmf_processor.discover_with_financial_intelligence(
    profile_criteria={
        'ntee_codes': ['P20', 'B25'],
        'states': ['VA', 'MD', 'DC'],
        'revenue_range': [100000, 10000000]
    },
    financial_filters={
        'foundation_grants_paid': True,
        'min_assets': 1000000,
        'grant_capacity': 'Major'  # Based on 990-PF distribution data
    }
)
```

### Migration Achievement (September 2025)
- **Phase 7**: BMF Discovery 500 Internal Server Errors → 200 OK responses
- **Phase 8**: CSV-based BMF processing → Comprehensive SQL intelligence database
- **Performance**: 47.2x improvement in organizational discovery results
- **Intelligence**: Foundation grant-making analysis and capacity scoring
- **Coverage**: Multi-state BMF data + 3 years of SOI financial intelligence

### Database Operations
```python
# Application database (profiles, opportunities)
database_service = DatabaseManager("data/catalynx.db")
opportunity = Opportunity(id=..., profile_id=..., organization_name=...)
success = database_service.create_opportunity(opportunity)

# Intelligence database (nonprofit financial data)
intelligence_db = BMFSOIIntelligenceService("data/nonprofit_intelligence.db")
financial_data = intelligence_db.get_organization_intelligence(ein="541026365")
foundation_capacity = intelligence_db.analyze_foundation_grants(ein="541026365")
```

### System Status
- **BMF Discovery**: ✅ **Enhanced Intelligence** (was basic CSV → now comprehensive SQL)
- **Financial Analysis**: ✅ **Multi-Year SOI Data** (2022-2024 with 190+ fields)
- **Foundation Intelligence**: ✅ **Grant-Making Analysis** (payout ratios, capacity scoring)
- **Performance**: ✅ **47.2x Improvement** (10 → 472 organizations discovered)
- **Legacy Compatibility**: ✅ **Maintained** (ProfileService deprecated but functional)

## WEB INTERFACE

### Modern Stack
- **Backend**: FastAPI (`src/web/main.py`) with async REST API, WebSocket support
- **Frontend**: Alpine.js + Tailwind CSS reactive SPA (`src/web/static/`)
- **Features**: Mobile-first design, real-time updates, Chart.js analytics, WCAG 2.1 AA compliance

### Key APIs
- `POST /api/profiles/{profile_id}/discover/entity-analytics` - Enhanced discovery
- `GET /api/profiles/{profile_id}/entity-analysis` - Profile analysis  
- `GET /api/entities/{entity_id}/financial-metrics` - Shared analytics
- **Documentation**: `/api/docs` - OpenAPI specification

### Launch
- **Primary**: `launch_catalynx_web.bat` → http://localhost:8000
- **Dev Mode**: `python src/web/main.py`

## DISCOVERY & ANALYTICS

### Government Opportunity Scorer (Optimized Weights)
- **Eligibility**: 0.30, **Geographic**: 0.20, **Timing**: 0.20, **Financial**: 0.15, **Historical**: 0.15
- **Thresholds**: High (0.75), Medium (0.55), Low (0.35) - data-driven adjustments

### Network Analysis
- **Board Network Analyzer**: Strategic relationship mapping with centrality metrics
- **Partnership Intelligence**: AI-powered opportunity identification through network analysis

## PROCESSOR SYSTEM (18 PROCESSORS - 100% OPERATIONAL)

### Data Fetchers
- **BMF Filter**: IRS Business Master File with entity integration
- **ProPublica Fetch**: 990 filing data with shared analytics  
- **Grants.gov/USASpending**: Federal opportunities and awards with entity structure
- **VA State Grants**: Virginia opportunities with priority scoring
- **Foundation Directory**: Corporate foundation opportunities

### Analysis Processors  
- **Government Opportunity Scorer**: Data-driven weights with comprehensive documentation
- **Success Scorer**: Historical pattern analysis with error handling
- **Board Network Analyzer**: Relationship mapping with shared analytics
- **AI Heavy/Lite**: Comprehensive and cost-effective AI analysis with GPT-5 optimization

### Performance
- **Processing**: Sub-millisecond per entity-organization pair
- **Success Rate**: 100% functional with enhanced error handling
- **Cache Integration**: 85% hit rate, async optimization

## 4-TIER INTELLIGENCE SYSTEM (BUSINESS PACKAGES)

### Service Tiers
1. **CURRENT ($0.75, 5-10 min)**: 4-stage AI analysis (PLAN→ANALYZE→EXAMINE→APPROACH), multi-dimensional scoring, risk assessment, strategic recommendations
2. **STANDARD ($7.50, 15-20 min)**: + Historical funding analysis, geographic patterns, temporal trends, success factors
3. **ENHANCED ($22.00, 30-45 min)**: + Document analysis, network intelligence, decision maker profiling, competitive analysis
4. **COMPLETE ($42.00, 45-60 min)**: + Policy analysis, real-time monitoring, 26+ page reports, strategic consulting

### Architecture Benefits
- **Dual Design**: Tab processors ($0.0004-$0.20) for granular control + tier services for complete packages
- **Shared Foundation**: Tier services utilize processors internally for comprehensive analysis
- **Professional Output**: Executive summaries, implementation plans, strategic recommendations

## PHASE 6 ADVANCED FEATURES (COMPLETE)

### Decision Support System (`src/decision/`)
- **Multi-Score Integration**: Combines government, AI, network, compliance scoring
- **Feasibility Assessment**: Technical, resource, timeline, compliance evaluation
- **Interactive Tools**: Parameter adjustment, scenario analysis, sensitivity testing
- **Collaborative Features**: Multi-user sessions, voting, consensus tracking

### Visualization & Export (`src/visualization/`, `src/export/`)
- **Chart Types**: 10+ interactive charts (bar, line, pie, scatter, radar, heatmap, sankey, network)
- **Export Formats**: PDF, Excel, PowerPoint, HTML, JSON with professional templates
- **Mobile Accessibility**: WCAG 2.1 AA compliance, responsive design, touch optimization

### Analytics & Reporting (`src/analytics/`, `src/reporting/`)
- **Real-Time Metrics**: Performance monitoring, predictive insights, KPI tracking
- **Automated Reports**: Executive, technical, performance templates with scheduling
- **Report Analytics**: Usage tracking, optimization suggestions, delivery systems

## DEVELOPMENT GUIDELINES

### Core Principles
- Maintain entity-based architecture patterns
- Follow GPT-5 model configuration requirements
- Use shared analytics for cross-entity analysis
- Implement comprehensive logging and error handling

### Launch Commands
- **Primary**: `launch_catalynx_web.bat` → http://localhost:8000
- **Development**: `python src/web/main.py`
- **Network Analysis**: `launch_strategic_analysis.bat`

---

## 12-FACTOR TOOL ARCHITECTURE (PHASE 1-9 TRANSFORMATION)

### Transformation Overview
**Goal**: Modernize 43 processors → 24 12-factor compliant tools
**Timeline**: 11 weeks (Started: 2025-09-30)
**Status**: ✅ **PHASE 8 COMPLETE** - 24 operational tools, Week 9 UI modernization

**CRITICAL LOCATION**: All 12-factor tools are in `tools/` directory at project root, NOT in `src/`

```
Grant_Automation/
├── tools/                    ← 24 OPERATIONAL 12-FACTOR TOOLS HERE
│   ├── opportunity_screening_tool/     # Tool 1
│   ├── deep_intelligence_tool/         # Tool 2
│   ├── bmf_filter_tool/                # Tool 4
│   ├── financial_intelligence_tool/    # Tool 10
│   ├── risk_intelligence_tool/         # Tool 11
│   ├── network_intelligence_tool/      # Tool 12
│   ├── schedule_i_grant_analyzer_tool/ # Tool 13
│   ├── multi_dimensional_scorer_tool/  # Tool 20
│   ├── report_generator_tool/          # Tool 21
│   ├── historical_funding_analyzer_tool/ # Tool 22
│   ├── web_intelligence_tool/          # Tool 25
│   └── ... (13 more tools)
├── src/                     ← Service layer, legacy processors, API routers
│   ├── core/tool_framework/ ← Base classes for tools
│   ├── workflows/           ← Workflow engine & tool loader
│   ├── profiles/            ← Service layer (keep)
│   ├── discovery/           ← Service layer (keep)
│   ├── scoring/             ← Legacy processors (deprecate Week 3)
│   ├── analysis/            ← Legacy processors (deprecate Week 3)
│   └── processors/          ← Legacy processors (deprecated)
└── docs/                    ← Documentation
    └── TOOL_ARCHITECTURE_MAPPING.md ← Complete 3-tab workflow mapping
```

### Tool Infrastructure

#### Tool Registry System (`src/core/tool_registry.py`)
- Auto-discovery of tools via `12factors.toml` files in `tools/` directory
- Tool metadata management and version tracking
- Status management (operational, deprecated, in_development)
- Inventory reporting and tool lifecycle management
- **Default Directory**: `tools/` (project root)

#### Base Tool Framework (`src/core/tool_framework/`)
- **BaseTool**: Abstract base class for async tools
- **SyncBaseTool**: Base class for synchronous tools
- **ToolResult[T]**: Generic structured output container
- **ToolExecutionContext**: Execution metadata and configuration
- **Factor 4**: Tools as Structured Outputs - eliminates parsing errors
- **Factor 6**: Stateless execution - no persistent state between runs
- **Factor 10**: Single Responsibility - each tool does one thing well

#### BAML Validator (`src/core/tool_framework/baml_validator.py`)
- Structured output validation (dataclasses, schemas, enums)
- Type checking and field validation
- Required field enforcement
- Range validation for numbers
- Example schemas: NONPROFIT_PROFILE_SCHEMA, OPPORTUNITY_SCHEMA

#### Workflow Engine (`src/workflows/`)
- **WorkflowParser**: YAML workflow definition parser
- **WorkflowEngine**: Multi-tool orchestration with dependency management
- Parallel execution of independent steps
- Context variable substitution (${context.var}, ${steps.step.output})
- Error handling and retry logic

### Two-Tool Architecture (Weeks 2-3)

#### Tool 1: Opportunity Screening Tool
- **Purpose**: Screen 100s of opportunities → shortlist of ~10
- **Cost**: $0.02/opportunity (~$4-8 for 200 opportunities)
- **Speed**: ~5 seconds per opportunity
- **Replaces**: 2 processors (ai_lite_unified, ai_heavy_light)

#### Human Gateway
- Manual review and filtering of screened opportunities
- Web scraping for additional context
- Selection of ~10 opportunities for deep analysis

#### Tool 2: Deep Intelligence Tool
- **Purpose**: Comprehensive analysis of selected opportunities
- **Cost**: $0.75-$42.00 per opportunity (depth-dependent)
- **Speed**: 5-60 minutes per opportunity
- **Depths**: quick ($0.75), standard ($7.50), enhanced ($22.00), complete ($42.00)
- **Replaces**: 6 processors (ai_heavy_deep, ai_heavy_researcher, 4 tier processors)

### Operational Tools (24 of 24 Complete - 100% Nonprofit Core + Web Intelligence)

**Location**: All tools in `tools/` directory at project root

**Categories**:
1. **XML Parser Tools** (4 tools) - Foundation data layer
2. **Core Workflow Tools** (2 tools) - Main pipeline
3. **Intelligence Analysis Tools** (5 tools) - Deep analysis
4. **Scoring & Reporting Tools** (2 tools) - Results generation
5. **Data Collection & Enrichment** (4 tools) - Data sources
6. **Support & Foundation Tools** (6 tools) - Utilities
7. **Web Intelligence Tools** (1 tool) - Web scraping

**Complete Tool List**:
1. ✅ **XML 990 Parser Tool** - Regular nonprofit 990 parsing (`xml-990-parser-tool/`)
2. ✅ **XML 990-PF Parser Tool** - Private foundation 990-PF parsing (`xml-990pf-parser-tool/`)
3. ✅ **XML 990-EZ Parser Tool** - Small nonprofit 990-EZ parsing (`xml-990ez-parser-tool/`)
4. ✅ **XML Schedule Parser Tool** - Schedule extraction and parsing (`xml-schedule-parser-tool/`)
5. ✅ **BMF Filter Tool** - IRS Business Master File filtering (`bmf_filter_tool/`)
6. ✅ **Form 990 Analysis Tool** - Financial metrics and analytics (`form990_analysis_tool/`)
7. ✅ **Form 990 ProPublica Tool** - ProPublica API enrichment (`form990_propublica_tool/`)
8. ✅ **ProPublica API Enrichment Tool** - Additional data enrichment (`propublica_api_enrichment_tool/`)
9. ✅ **Foundation Grant Intelligence Tool** - Grant-making analysis (`foundation_grant_intelligence_tool/`)
10. ✅ **Tool 1: Opportunity Screening Tool** - Mass screening with fast/thorough modes (`opportunity_screening_tool/`)
11. ✅ **Tool 2: Deep Intelligence Tool** - 2-tier comprehensive analysis (Essentials $2, Premium $8) (`deep_intelligence_tool/`)
12. ✅ **Tool 10: Financial Intelligence Tool** - Comprehensive financial metrics and scoring (`financial_intelligence_tool/`)
13. ✅ **Tool 11: Risk Intelligence Tool** - Multi-dimensional risk assessment (`risk_intelligence_tool/`)
14. ✅ **Tool 12: Network Intelligence Tool** - Board network and relationship analysis (`network_intelligence_tool/`)
15. ✅ **Tool 13: Schedule I Grant Analyzer Tool** - Foundation grant-making patterns (`schedule_i_grant_analyzer_tool/`)
16. ✅ **Tool 14: Foundation Grantee Bundling Tool** - Co-funding analysis (`foundation_grantee_bundling_tool/`)
17. ✅ **Tool 16: Data Validator Tool** - Data quality and completeness validation (`data_validator_tool/`)
18. ✅ **Tool 17: EIN Validator Tool** - EIN format validation and lookup (`ein_validator_tool/`)
19. ✅ **Tool 18: Data Export Tool** - Multi-format export capabilities (`data_export_tool/`)
20. ✅ **Tool 19: Grant Package Generator Tool** - Application package assembly (`grant_package_generator_tool/`)
21. ✅ **Tool 20: Multi-Dimensional Scorer Tool** - 5-stage dimensional scoring (`multi_dimensional_scorer_tool/`)
22. ✅ **Tool 21: Report Generator Tool** - Professional report templates with DOSSIER structure (`report_generator_tool/`)
23. ✅ **Tool 22: Historical Funding Analyzer Tool** - USASpending.gov pattern analysis (`historical_funding_analyzer_tool/`)
24. ✅ **Tool 25: Web Intelligence Tool** - Scrapy-powered web scraping with 990 verification (`web_intelligence_tool/`)

**Documentation**:
- **Complete Inventory**: `tools/TOOLS_INVENTORY.md` (24 tools with full descriptions)
- **Architecture Mapping**: `docs/TOOL_ARCHITECTURE_MAPPING.md` (3-tab workflow, execution order)
- **Tool-Specific Docs**: Each tool has `README.md` in its directory

### Future Enhancements (Optional - Phase 9)
- Government opportunity tools (3 tools - Grants.gov, USASpending, State grants)
- Additional specialized analysis tools

### Processor Deprecation Strategy
- Progressive deprecation as tools come online
- Legacy processors moved to `src/processors/_deprecated/`
- Tests moved to `tests/deprecated_processor_tests/`
- Major cleanup in Phase 7 (Week 7)
- Full removal in Phase 9 (Week 9)

### 12-Factor Compliance Tracking
All tools comply with 12 factors via `12factors.toml` configuration:
1. ✅ One codebase tracked in revision control
2. ✅ Explicitly declare and isolate dependencies
3. ✅ Store config in the environment
4. ✅ **Tools as Structured Outputs (CORE)** - Predictable data interfaces
5. ✅ Strictly separate build and run stages
6. ✅ Execute as stateless processes
7. ✅ Export services via port binding (or function calls)
8. ✅ Scale out via the process model
9. ✅ Maximize robustness with fast startup
10. ✅ **Small, Focused Agents (CORE)** - Single responsibility per tool
11. ✅ Autonomous operation
12. ✅ API First design

---

**STATUS: PHASE 1 IN PROGRESS** - Foundation infrastructure complete. Ready for unified AI tools development (Weeks 2-3).