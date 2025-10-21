# 12-Factor Agent Tools Inventory

**Last Updated**: 2025-10-21
**Tool Count**: 24 operational tools
**Status**: All production-ready with full 12-factor compliance

## Overview

Complete inventory of 24 specialized 12-factor agent tools implementing the Human Layer Framework for Catalynx Grant Research Intelligence Platform.

**Framework Principles**:
- **Factor 4**: Tools as Structured Outputs - eliminates parsing errors
- **Factor 10**: Small, Focused Agents - single responsibility per tool

**Location**: All tools in `tools/` directory at project root

---

## Tool Categories

### 1. XML Parser Tools (4 tools) - Foundation Data Layer
### 2. Core Workflow Tools (2 tools) - Main Pipeline
### 3. Intelligence Analysis Tools (5 tools) - Deep Analysis
### 4. Scoring & Reporting Tools (2 tools) - Results Generation
### 5. Data Collection & Enrichment Tools (4 tools) - Data Sources
### 6. Support & Foundation Tools (6 tools) - Utilities
### 7. Web Intelligence Tools (1 tool) - Web Scraping

---

## 1. XML Parser Tools (4 Tools - CORE ARCHITECTURE)

### xml-990-parser-tool
**Form**: IRS 990 (Regular Nonprofits)
**Organizations**: 501(c)(3) public charities, ≥$200K revenue or ≥$500K assets
**Size**: 1,472 lines
**Status**: ✅ Production Ready

**Extracts**:
- Officers & board members (Form990PartVIISectionAGrp)
- Governance indicators (conflict of interest policies, whistleblower, etc.)
- Program activities & accomplishments
- Financial summaries (revenue, expenses, assets)
- Grants paid (Schedule I)

**Documentation**: `tools/xml-990-parser-tool/README.md`

---

### xml-990pf-parser-tool ⭐ ENHANCED
**Form**: IRS 990-PF (Private Foundations)
**Organizations**: Private foundations only
**Size**: 2,310 lines
**Status**: ✅ Production Ready + Network Analysis (Phase 2 Complete)

**Extracts**:
- Foundation officers/directors (OfficerDirTrstKeyEmplInfoGrp) **WITH network analysis**
- Grants paid (Part XV) **WITH normalized names**
- Investment portfolios (Part II) with grant capacity analysis
- Payout requirements (5% distribution rule)
- Excise tax computation
- Governance & management indicators
- Foundation classification & intelligence

**Network Analysis Features** (NEW):
- `normalized_person_name`: "CHRISTINE M CONNOLLY" (fuzzy matching)
- `normalized_recipient_name`: "AFRO AMERICAN HISTORICAL ASSOC"
- `role_category`: Executive, Board, Staff, Volunteer
- `influence_score`: 0-1 decision-making power calculation
- `recipient_ein`: Direct org-to-org linking

**Documentation**: `tools/xml-990pf-parser-tool/README.md`

---

### xml-990ez-parser-tool
**Form**: IRS 990-EZ (Small Organizations)
**Organizations**: Small nonprofits, <$200K revenue, <$500K assets
**Size**: 821 lines
**Status**: ✅ Production Ready

**Extracts**:
- Officers & key employees (simplified structure)
- Basic financial summary (simplified reporting)
- Program service accomplishments
- Public support data
- Balance sheet (simplified)

**Documentation**: `tools/xml-990ez-parser-tool/README.md`

---

### xml-schedule-parser-tool
**Purpose**: Schedule-specific parsing (Schedule A, B, I, etc.)
**Organizations**: All 990 filers with schedules
**Status**: ✅ Production Ready

**Extracts**:
- Schedule I: Grants and other assistance
- Schedule A: Public charity status
- Schedule B: Contributors
- Other schedules as needed

**Documentation**: `tools/xml-schedule-parser-tool/README.md`

---

## 2. Core Workflow Tools (2 Tools - MAIN PIPELINE)

### Tool 1: opportunity-screening-tool 🎯
**Purpose**: Mass screening of grant opportunities (200 → 10-15)
**Status**: ✅ Production Ready

**Modes**:
- **Fast Mode**: $0.0004/opp, ~2 sec (basic strategic fit)
- **Thorough Mode**: $0.02/opp, ~5 sec (comprehensive analysis)

**Typical Pipeline**:
- Fast: 200 → 50 candidates ($0.08 total)
- Thorough: 50 → 10-15 finalists ($1.00 total)
- **Total Cost**: ~$1.08 for complete funnel

**Replaces**: ai_lite_unified, ai_heavy_light processors

**Documentation**: `tools/opportunity-screening-tool/README.md`

---

### Tool 2: deep-intelligence-tool 🎯
**Purpose**: Comprehensive deep intelligence analysis
**Status**: ✅ Production Ready

**Depths**:
- **Essentials**: $2.00 user ($0.05 AI), 15-20 min
  - 4-stage AI analysis + network intelligence + historical/geographic insights
- **Premium**: $8.00 user ($0.10 AI), 30-40 min
  - Enhanced network pathways + policy analysis + strategic consulting + comprehensive dossier

**Features**:
- Orchestrates Tools 10, 11, 12, 13, 22
- Network intelligence included in base tier
- 40-80x transparent platform value markup

**Replaces**: ai_heavy_deep, ai_heavy_researcher, current_tier, standard_tier, enhanced_tier, complete_tier processors

**Documentation**: `tools/deep-intelligence-tool/README.md`

---

## 3. Intelligence Analysis Tools (5 Tools - DEEP ANALYSIS)

### Tool 10: financial-intelligence-tool
**Purpose**: Comprehensive financial health assessment
**Status**: ✅ Production Ready
**Cost**: $0.03 per analysis

**Features**:
- 15+ comprehensive financial metrics
- Financial health rating and scoring
- Grant capacity assessment with match capability
- AI-enhanced strategic insights
- Liquidity, efficiency, sustainability analysis

**Replaces**: financial_scorer.py, Form990DataMiningEngine

**Documentation**: `tools/financial-intelligence-tool/README.md`

---

### Tool 11: risk-intelligence-tool
**Purpose**: Multi-dimensional risk assessment
**Status**: ✅ Production Ready
**Cost**: $0.02 per analysis

**Features**:
- 6-dimensional risk assessments
  - Eligibility, competition, capacity, timeline, financial, compliance
- Multi-level risk categorization (minimal → critical)
- Prioritized mitigation strategies
- Go/no-go recommendations with confidence levels

**Replaces**: risk_assessor.py

**Documentation**: `tools/risk-intelligence-tool/README.md`

---

### Tool 12: network-intelligence-tool
**Purpose**: Board network and relationship analysis
**Status**: ✅ Production Ready
**Cost**: $0.04 per analysis

**Features**:
- Board member profiling with centrality metrics
- Network cluster identification
- Relationship pathway mapping (direct and indirect)
- Target funder connection analysis
- Strategic cultivation strategies

**Replaces**: board_network_analyzer.py, enhanced_network_analyzer.py, optimized_network_analyzer.py, NetworkIntelligenceEngine

**Documentation**: `tools/network-intelligence-tool/README.md`

---

### Tool 13: schedule-i-grant-analyzer-tool
**Purpose**: Foundation grant-making pattern analysis
**Status**: ✅ Production Ready
**Cost**: $0.03 per analysis

**Features**:
- Foundation grant-making pattern analysis
- Category and geographic distribution
- Grant size analysis with competitive sizing
- Recipient profiling
- Organization match analysis

**Replaces**: schedule_i_processor.py, FoundationIntelligenceEngine

**Documentation**: `tools/schedule-i-grant-analyzer-tool/README.md`

---

### Tool 22: historical-funding-analyzer-tool
**Purpose**: USASpending.gov pattern analysis and trends
**Status**: ✅ Production Ready
**Cost**: $0.00 (data analysis only)

**Features**:
- USASpending.gov data analysis with funding pattern detection
- Geographic distribution analysis (state-level funding breakdown)
- Temporal trend analysis with year-over-year growth calculations
- Award size categorization (micro → small → medium → large → major)
- Competitive position insights and recommendations
- Performance: 4-5ms per analysis

**Replaces**: Historical analysis portions of tier processors

**Documentation**: `tools/historical-funding-analyzer-tool/README.md`

---

## 4. Scoring & Reporting Tools (2 Tools)

### Tool 20: multi-dimensional-scorer-tool
**Purpose**: 5-stage dimensional scoring with boost factors
**Status**: ✅ Production Ready
**Cost**: $0.00 (algorithmic)

**Features**:
- 5 workflow stages (DISCOVER → PLAN → ANALYZE → EXAMINE → APPROACH)
- Stage-specific dimensional weights (5 dimensions per stage, weights sum to 1.0)
- 4 boost factors (financial +10%, network +15%, historical +12%, risk +8%)
- Confidence calculation based on data quality + enhancements
- Performance: <0.05ms per score

**Replaces**: discovery_scorer.py, success_scorer.py

**Documentation**: `tools/multi-dimensional-scorer-tool/README.md`

---

### Tool 21: report-generator-tool
**Purpose**: Professional report templates with DOSSIER structure
**Status**: ✅ Production Ready
**Cost**: $0.00 (no AI calls)

**Features**:
- 4 professional templates (comprehensive, executive, risk, implementation)
- DOSSIER structure (masters thesis-level comprehensive analysis)
- HTML output with responsive design and professional styling
- Template-based rendering with Jinja2
- Performance: 1-2s per report

**Replaces**: ai_heavy_dossier_builder.py

**Documentation**: `tools/report-generator-tool/README.md`

---

## 5. Data Collection & Enrichment Tools (4 Tools)

### Tool 4: bmf-filter-tool
**Purpose**: IRS Business Master File filtering and discovery
**Status**: ✅ Production Ready
**Cost**: $0.00 (database query)

**Features**:
- Multi-criteria nonprofit discovery
- Geographic and NTEE code filtering
- Financial threshold filtering
- Returns: 200-500 organizations per query

**Replaces**: bmf_filter.py

**Documentation**: `tools/bmf-filter-tool/README.md`

---

### Tool 5: form990-analysis-tool
**Purpose**: Deep financial analysis of 990 data
**Status**: ✅ Production Ready
**Cost**: $0.00 (analysis only)

**Features**:
- Comprehensive financial metrics extraction
- Multi-year trend analysis
- Program service analysis
- Balance sheet analysis

**Documentation**: `tools/form990-analysis-tool/README.md`

---

### Tool 6: form990-propublica-tool
**Purpose**: ProPublica API data enrichment for 990 filings
**Status**: ✅ Production Ready
**Cost**: $0.00 (API calls only)

**Features**:
- ProPublica Nonprofit Explorer API integration
- Additional financial data enrichment
- Multi-year 990 filing history
- Organization profile enhancement

**Documentation**: `tools/form990-propublica-tool/README.md`

---

### Tool 8: propublica-api-enrichment-tool
**Purpose**: Additional ProPublica API integration and enrichment
**Status**: ✅ Production Ready
**Cost**: $0.00 (API calls only)

**Features**:
- Additional data enrichment beyond basic 990 data
- Supplementary organizational information
- Historical filing data

**Documentation**: `tools/propublica-api-enrichment-tool/README.md`

---

## 6. Support & Foundation Tools (6 Tools)

### Tool 7: foundation-grant-intelligence-tool
**Purpose**: Foundation grant-making intelligence analysis
**Status**: ✅ Production Ready
**Cost**: $0.00 (analysis only)

**Features**:
- Foundation 990-PF analysis
- Grant-making pattern detection
- Geographic and programmatic focus analysis
- Payout ratio calculations

**Documentation**: `tools/foundation-grant-intelligence-tool/README.md`

---

### Tool 14: foundation-grantee-bundling-tool
**Purpose**: Co-funding analysis and grantee clustering
**Status**: ✅ Production Ready
**Cost**: $0.00 (analysis only)

**Features**:
- Identify foundations that fund similar organizations
- Grantee clustering and pattern analysis
- Co-funding network mapping
- Strategic foundation bundling recommendations

**Documentation**: `tools/foundation-grantee-bundling-tool/README.md`

---

### Tool 16: data-validator-tool
**Purpose**: Data quality and completeness validation
**Status**: ✅ Production Ready
**Cost**: $0.00 (no AI calls)

**Features**:
- Required field validation
- Type checking and validation
- Completeness and quality scoring
- Schema compliance verification

**Replaces**: data_validator.py

**Documentation**: `tools/data-validator-tool/README.md`

---

### Tool 17: ein-validator-tool
**Purpose**: EIN format validation and lookup
**Status**: ✅ Production Ready
**Cost**: $0.00 (no AI calls)

**Features**:
- EIN format validation
- Invalid prefix detection
- Organization lookup capability

**Replaces**: ein_lookup.py

**Documentation**: `tools/ein-validator-tool/README.md`

---

### Tool 18: data-export-tool
**Purpose**: Multi-format export capabilities
**Status**: ✅ Production Ready
**Cost**: $0.00 (no AI calls)

**Features**:
- Multi-format export (JSON, CSV, Excel, PDF)
- Template-based formatting
- Batch export capabilities
- Custom field selection

**Replaces**: export_manager.py

**Documentation**: `tools/data-export-tool/README.md`

---

### Tool 19: grant-package-generator-tool
**Purpose**: Application package assembly and timeline planning
**Status**: ✅ Production Ready
**Cost**: $0.00 (no AI calls)

**Features**:
- Application package assembly
- Document checklist management
- Submission timeline planning
- Package status tracking

**Replaces**: grant_package_generator.py

**Documentation**: `tools/grant-package-generator-tool/README.md`

---

## 7. Web Intelligence Tools (1 Tool)

### Tool 25: web-intelligence-tool 🌐
**Purpose**: Scrapy-powered web scraping with 990 verification
**Status**: ✅ Production Ready

**3 Use Cases**:

1. **Profile Builder**: Scrape YOUR organization's website ($0.05-0.10)
   - Extract mission, programs, leadership, contact info
   - Build comprehensive nonprofit profile
   - 990 verification pipeline

2. **Opportunity Research**: Scrape grantmaking nonprofits ($0.15-0.25)
   - United Way chapters, community foundations
   - Extract grant opportunities, eligibility, deadlines
   - Cross-validate with 990 grant data

3. **Foundation Research**: Scrape private foundations ($0.10-0.20)
   - 990-PF foundations
   - Extract grant opportunities, application processes
   - Verify against Schedule I grant data

**Features**:
- Smart URL resolution (User → 990 → GPT priority with confidence scoring)
- 990 verification pipeline (cross-validates web data against IRS tax filings)
- Respectful scraping (2s delay, robots.txt compliance, user-agent identification)
- Structured outputs (BAML schemas with Pydantic validation)
- Performance: 10-60s execution, 85-95% accuracy with 990 verification

**Integration**:
- Profile Builder: `POST /api/v2/profiles/{id}/enhance`
- Opportunity Research: `POST /api/v2/opportunities/{id}/research`
- Foundation Research: `POST /api/v2/foundations/{id}/research`

**Replaces**: verification_enhanced_scraper.py (enhanced with Scrapy framework)

**Documentation**: `tools/web-intelligence-tool/README.md`

---

## Tool Selection Guide

### By Organization Type
| Organization Type | Revenue/Assets | Use Tool |
|------------------|----------------|----------|
| Private Foundation | Any | xml-990pf-parser-tool |
| Regular Nonprofit | ≥$200K or ≥$500K | xml-990-parser-tool |
| Small Nonprofit | <$200K and <$500K | xml-990ez-parser-tool |

### By Workflow Stage
| Stage | Purpose | Primary Tools |
|-------|---------|---------------|
| **Profiles** | Create & enhance profiles | Tool 25 (Profile Builder), Tool 16, Tool 17 |
| **Screening** | Find & screen opportunities | Tool 4 (BMF), Tool 1 (Screening), Tool 20 (Scorer) |
| **Intelligence** | Deep analysis | Tool 2 (orchestrator), Tools 10-13, Tool 22 |

### By Data Need
| Need | Use Tool |
|------|----------|
| Board member network analysis | Tool 12 (Network Intelligence) |
| Foundation grant patterns | Tool 13 (Schedule I Analyzer) |
| Financial health assessment | Tool 10 (Financial Intelligence) |
| Risk assessment | Tool 11 (Risk Intelligence) |
| Historical funding trends | Tool 22 (Historical Funding) |
| Mass opportunity screening | Tool 1 (Opportunity Screening) |
| Comprehensive analysis | Tool 2 (Deep Intelligence) |
| Professional reports | Tool 21 (Report Generator) |
| Web scraping | Tool 25 (Web Intelligence) |

---

## File Structure Standards

### Required Files
```
tool-name_tool/
├── 12factors.toml          # Framework compliance config
├── README.md               # Tool documentation
├── app/
│   ├── __init__.py
│   ├── {tool_name}_tool.py # Main implementation
│   └── models.py           # Pydantic models (optional)
├── baml_src/               # BAML schema (optional)
│   └── tool_schema.baml
└── tests/
    ├── __init__.py
    └── test_{tool_name}_tool.py
```

### Generated/Cache Files (Excluded)
- `__pycache__/` - Python bytecode (deleted)
- `baml_client/` - Auto-generated TypeScript (deleted from 990-PF)
- `cache/` - Cached XML files (gitignored)

---

## Performance Characteristics

### Typical Execution Times
- **Startup**: <50ms (all tools, Factor 9 compliance)
- **990-EZ parsing**: 8-15ms
- **990 parsing**: 10-20ms
- **990-PF parsing**: 10-20ms
- **Opportunity screening (fast)**: ~2 sec per opportunity
- **Opportunity screening (thorough)**: ~5 sec per opportunity
- **Deep intelligence (essentials)**: 15-20 min
- **Deep intelligence (premium)**: 30-40 min
- **Cache hit rate**: 85%+
- **Concurrent downloads**: 3 simultaneous (Factor 8 scaling)

### Quality Metrics
All 24 operational tools include comprehensive quality assessment:
- Overall success rate (0-1)
- Schema validation rate
- Data completeness scores by category
- Data freshness score
- Parsing error tracking

---

## Integration Example

```python
# Multi-tool workflow with Tool 1 & Tool 2
from src.workflows.tool_loader import ToolLoader

# Initialize tool loader
tool_loader = ToolLoader(tools_directory="tools/")

# Stage 1: Screen 200 opportunities → 10-15
screening_tool = tool_loader.load_tool("opportunity-screening-tool")
screening_result = await screening_tool.execute({
    "opportunities": opportunities,  # 200 opportunities
    "organization_profile": profile,
    "screening_mode": "thorough",
    "minimum_threshold": 0.55
})
# Returns: ~10-15 high-potential opportunities

# Stage 2: Deep intelligence on selected opportunities
intelligence_tool = tool_loader.load_tool("deep-intelligence-tool")
for opp in screening_result.recommended_opportunities[:10]:
    intelligence_result = await intelligence_tool.execute({
        "opportunity": opp,
        "organization_profile": profile,
        "depth": "essentials"  # or "premium"
    })
    # Returns: Comprehensive analysis with Tools 10-13, 22
```

---

## Documentation Map

### Core Documentation
- **Framework Overview**: `CLAUDE.md` (project root)
- **Tool Inventory**: This file (`tools/TOOLS_INVENTORY.md`)
- **Architecture Mapping**: `docs/TOOL_ARCHITECTURE_MAPPING.md` (comprehensive 3-tab workflow)
- **Network Analysis**: `docs/cross_990_field_standardization.md`

### Tool-Specific Documentation
Each tool has a README.md in its directory:
- `tools/{tool_name}_tool/README.md`

---

## Recent Enhancements

### Phase 8 (October 2025) ✅
- Added 15 new tools (9 → 24 total)
- Tool 1 (Opportunity Screening) operational
- Tool 2 (Deep Intelligence) operational with 2-tier pricing
- Tools 10-13 (Intelligence Analysis) operational
- Tool 20 (Multi-Dimensional Scorer) operational
- Tool 21 (Report Generator) operational
- Tool 22 (Historical Funding Analyzer) operational
- Tool 25 (Web Intelligence) enhanced with 3 use cases

### Phase 7 (September 2025) ✅
- Validation & compliance audit (100% 12-factor compliant)
- All 22 tools validated
- Git safety checkpoint (pre-processor-removal tag)

### Phase 6 (September 2025) ✅
- Unified Tool Execution API (`/api/v1/tools/*`)
- Complete API documentation (OpenAPI/Swagger)

### Phase 2 (September 2025) ✅
- Network analysis for xml-990pf-parser-tool
- Cross-990 field standardization
- Name normalization (person and organization)
- Role categorization and influence scoring

### Phase 1 (September 2025) ✅
- Complete array output (all items, not samples)
- Comprehensive README files
- 12factors.toml configuration files

---

**Status**: All 24 tools production ready
**Compliance**: 100% 12-factor compliant
**Next Phase**: Phase 9 - Desktop UI modernization, government opportunity tools, production deployment
**Last Updated**: 2025-10-21
