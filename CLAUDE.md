# Catalynx - Grant Research Intelligence Platform

## SYSTEM STATUS: PHASE 2 COMPLETE - TWO-TOOL ARCHITECTURE OPERATIONAL ✅

**Production-ready grant intelligence platform** with 4-tier business packages ($0.75-$42.00), entity-based data architecture, modern web interface, and **12-factor tool transformation in progress**. Phase 2 milestone achieved: **Two unified AI tools replace 8 processors** (87.5% consolidation).

### 12-Factor Transformation Status (Week 3 of 9)
- **Progress**: Phase 2 Complete - Two-Tool Architecture Operational
- **Completed Tools**: 11/19 operational (58% of MVP)
- **Architecture**: Screening Tool + Deep Intelligence Tool (replaces 8 AI processors)
- **Timeline**: 9 weeks total, on track for production completion

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
- Quick depth: $0.75, 5-10 min (CURRENT tier equivalent)
- Standard depth: $7.50, 15-20 min (STANDARD tier equivalent)
- Enhanced depth: $22.00, 30-45 min (ENHANCED tier equivalent)
- Complete depth: $42.00, 45-60 min (COMPLETE tier equivalent)
- Comprehensive analysis: ~10 selected opportunities
- Replaces: 6 processors (ai_heavy_deep, ai_heavy_researcher, 4 tier processors)

**Pipeline Economics**:
- Stage 1: $0.68 for 200 opportunities
- Stage 2: $50-100 typical (variable depth)
- Total: ~$50-100 vs. manual research
- Result: 87.5% processor reduction with better architecture

**Completed Phases**:
- ✅ Phase 1 (Week 1): Foundation infrastructure, tool framework, workflow engine
- ✅ Phase 2 (Week 2-3): Two unified AI tools operational

**Next**: Phase 3 (Week 4) - Supporting Tools Development

## CRITICAL: GPT-5 MODEL CONFIGURATION

**MANDATORY REQUIREMENT**: System uses GPT-5 models exclusively - DO NOT change to GPT-4.

**Configuration Files**:
- `.env`: AI_LITE_MODEL, AI_HEAVY_MODEL, AI_RESEARCH_MODEL (all GPT-5 variants)
- `src/core/openai_service.py`: GPT-5 validation and cost tracking
- All processors: Optimized for GPT-5 architecture and token limits

**Why GPT-5**: Better performance, cost-effectiveness, and system optimization vs GPT-4 alternatives.

## CORE SYSTEM CAPABILITIES

### 4-Tier Intelligence System (Business Packages)
- **CURRENT ($0.75)**: 4-stage AI analysis, strategic recommendations (5-10 min)
- **STANDARD ($7.50)**: + Historical funding analysis, geographic patterns (15-20 min)  
- **ENHANCED ($22.00)**: + Document analysis, network intelligence, decision maker profiles (30-45 min)
- **COMPLETE ($42.00)**: + Policy analysis, monitoring, strategic consulting (45-60 min)

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
**Goal**: Modernize 43 processors → 19 12-factor compliant tools
**Timeline**: 9 weeks (Started: 2025-09-30)
**Status**: Phase 1 Foundation Infrastructure (Week 1) - IN PROGRESS

### Tool Infrastructure (NEW - Phase 1)

#### Tool Registry System (`src/core/tool_registry.py`)
- Auto-discovery of tools via `12factors.toml` files
- Tool metadata management and version tracking
- Status management (operational, deprecated, in_development)
- Inventory reporting and tool lifecycle management

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

### Operational Tools (11 of 19 Complete - 58%)
1. ✅ XML 990 Parser Tool - Regular nonprofit 990 parsing
2. ✅ XML 990-PF Parser Tool - Private foundation 990-PF parsing
3. ✅ XML 990-EZ Parser Tool - Small nonprofit 990-EZ parsing
4. ✅ BMF Filter Tool - IRS Business Master File filtering
5. ✅ Form 990 Analysis Tool - Financial metrics and analytics
6. ✅ Form 990 ProPublica Tool - ProPublica API enrichment
7. ✅ Foundation Grant Intelligence Tool - Grant-making analysis
8. ✅ ProPublica API Enrichment Tool - Additional data enrichment
9. ✅ XML Schedule Parser Tool - Schedule extraction and parsing
10. ✅ **Opportunity Screening Tool** - Mass screening with fast/thorough modes (NEW - Phase 2)
11. ✅ **Deep Intelligence Tool** - 4-depth comprehensive analysis (NEW - Phase 2)

### Remaining Tools (8 tools, Weeks 4-6)
- Government opportunity tools (3 tools - deferred to Phase 9)
- Additional data enrichment tools (5 tools)
- Export and reporting tools (2 tools)

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