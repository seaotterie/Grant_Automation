# Intelligence Module 12-Factor Migration Plan + 2-Tier Consolidation

**Created**: 2025-10-04
**Updated**: 2025-10-04 (Added 2-tier system)
**Status**: PLANNING PHASE
**Goal**: Migrate to 12-factor tools + consolidate to 2-tier TRUE COST pricing

---

## EXECUTIVE SUMMARY

### Current State Analysis
- **Intelligence Router**: `src/web/routers/intelligence.py` (503 lines) - References DELETED tier processors
- **Tier Pricing**: 4 tiers ($0.75 → $7.50 → $22 → $42) - Based on consultant rates, NOT AI costs
- **Actual AI Costs**: $0.0047 → $0.075 (15-560x markup!)
- **Legacy Module**: `src/intelligence/historical_funding_analyzer.py` (781 lines) - NOT 12-factor compliant
- **12-Factor Tool**: `tools/historical-funding-analyzer-tool/` - EXISTS but NOT integrated
- **API Endpoints**: Broken (reference deleted tier processors)

### Migration Strategy
**Three-Phase Approach**:
1. **Phase 1**: Consolidate to 2-tier TRUE COST system ($2 ESSENTIALS, $8 PREMIUM)
2. **Phase 2**: Create missing 12-factor tools (6 tools needed)
3. **Phase 3**: Migrate API endpoints + deprecate legacy code

### Key Changes
- **2-Tier System**: ESSENTIALS ($2.00, AI: $0.05) + PREMIUM ($8.00, AI: $0.10)
- **Network in Base**: Network intelligence included in ESSENTIALS (was $6.50 add-on)
- **73-81% Cost Reduction**: For users vs old 4-tier system
- **True Cost Transparency**: Show AI costs ($0.05-0.10) + platform value markup (40-80x)

---

## PART 1: COMPREHENSIVE INVENTORY

### A. Original Catalynx Intelligence (Legacy Processors)

#### 1. Tier Processors (DELETED - Phase 8)
| Processor | Status | Cost | Replacement |
|-----------|--------|------|-------------|
| `current_tier_processor.py` | ❌ DELETED | $0.75 | Tool 2 (quick depth) |
| `standard_tier_processor.py` | ❌ DELETED | $7.50 | Tool 2 (standard depth) |
| `enhanced_tier_processor.py` | ❌ DELETED | $22.00 | Tool 2 (enhanced depth) |
| `complete_tier_processor.py` | ❌ DELETED | $42.00 | Tool 2 (complete depth) |

**Functionality Lost**:
- ❌ Tier-based orchestration
- ❌ Add-on module integration
- ❌ Cost tracking by tier
- ❌ API endpoints broken

#### 2. Intelligence Router (`src/web/routers/intelligence.py`)
**Broken Endpoints**:
- `POST /api/intelligence/profiles/{profile_id}/analysis` - References deleted processors
- `GET /api/intelligence/analysis/{task_id}` - Task manager exists but no processors
- `POST /api/intelligence/cost-estimate` - Cost calculator exists (lines 88-169)
- `GET /api/intelligence/tiers` - Metadata exists (lines 371-448)

**What Still Works**:
- ✅ Cost calculator (TierCostCalculator class, lines 88-169)
- ✅ Task manager (TaskManager class, lines 172-223)
- ✅ Tier metadata (lines 371-448)

**What's Broken**:
- ❌ StandardTierProcessor (line 254)
- ❌ EnhancedTierProcessor (line 274)
- ❌ CompleteTierProcessor (line 304)

#### 3. Historical Funding Analyzer
**Legacy**: `src/intelligence/historical_funding_analyzer.py` (781 lines)
- ❌ NOT 12-factor compliant
- ❌ Direct processor, not a tool
- ❌ Missing BAML validation
- ❌ No ToolResult wrapper

**12-Factor Tool**: `tools/historical-funding-analyzer-tool/app/historical_tool.py` (559 lines)
- ✅ 12-factor compliant
- ✅ BAML schemas
- ✅ ToolResult wrapper
- ❌ NOT integrated with API

### B. Analysis Processors (src/processors/analysis/)

**Intelligence-Related Processors** (27 total):

| Processor | Lines | Function | 12-Factor Tool? |
|-----------|-------|----------|-----------------|
| `ai_heavy_deep_researcher.py` | 2,300+ | Deep research analysis | Tool 2 (Deep Intel) |
| `ai_heavy_researcher.py` | 2,100+ | Dossier building | Tool 2 (Deep Intel) |
| `ai_heavy_light_analyzer.py` | 1,200+ | Light AI analysis | Tool 1 (Screening) |
| `ai_lite_unified_processor.py` | 800+ | Fast screening | Tool 1 (Screening) |
| `board_network_analyzer.py` | 500+ | Network analysis | Tool 12 (Network) |
| `competitive_intelligence_processor.py` | 800+ | Competitive analysis | ❌ NO TOOL |
| `market_intelligence_monitor.py` | 600+ | Market monitoring | ❌ NO TOOL |
| `financial_scorer.py` | 400+ | Financial scoring | Tool 10 (Financial) |
| `risk_assessor.py` | 300+ | Risk assessment | Tool 11 (Risk) |
| `government_opportunity_scorer.py` | 1,100+ | Opportunity scoring | Tool 20 (Scorer) |
| `schedule_i_processor.py` | 400+ | Schedule I analysis | Tool 13 (Schedule I) |
| `trend_analyzer.py` | 300+ | Trend analysis | ❌ NO TOOL |
| `enhanced_network_analyzer.py` | 400+ | Enhanced network | Tool 12 (Network) |
| `intelligent_classifier.py` | 300+ | Classification | ❌ NO TOOL |
| `pdf_ocr.py` | 200+ | PDF OCR | ❌ NO TOOL |
| `corporate_csr_analyzer.py` | 400+ | CSR analysis | ❌ NO TOOL |
| `ein_cross_reference.py` | 200+ | EIN lookup | Tool 15 (EIN Validator) |

**CRITICAL GAP**: 7 processors have NO 12-factor tool equivalent!

### C. Web Intelligence Integration

**References Found** (16 occurrences):
1. `src/database/intelligence_schema.sql` - Web scraping results
2. `src/web/static/index.html` - UI references
3. `src/web/main.py` - Router import
4. `src/web/routers/intelligence.py` - Tier processors (BROKEN)
5. `src/web/routers/profiles_v2.py` - Intelligence database
6. `src/web/routers/opportunities.py` - Web intelligence tool
7. `src/processors/analysis/ai_heavy_researcher.py` - Web intelligence context
8. `src/processors/analysis/board_network_analyzer.py` - Board member extraction
9. `src/processors/analysis/competitive_intelligence_processor.py` - Strategic positioning
10. Tool 25 (Web Intelligence) - Scrapy-powered

**Tool 25 Integration**:
- ✅ Scrapy framework
- ✅ 990 verification pipeline
- ✅ BAML schemas
- ✅ Profile builder integration
- ❌ NOT integrated with intelligence tier system

---

## PART 2: GAP ANALYSIS

### Critical Missing Tools (7 Tools Needed)

#### 1. Competitive Intelligence Tool ❌
**Source**: `competitive_intelligence_processor.py` (800+ lines)
**Functionality**:
- Strategic positioning analysis
- Competitive landscape assessment
- Market share analysis
- Strength/weakness profiling

**12-Factor Requirements**:
- Input: Organization profile + competitor list
- Output: CompetitiveAnalysis dataclass
- Cost: ~$0.10 (AI-enhanced analysis)
- Factor 10: Single responsibility (competitive analysis only)

#### 2. Market Intelligence Monitor Tool ❌
**Source**: `market_intelligence_monitor.py` (600+ lines)
**Functionality**:
- Real-time market monitoring
- Funding trend tracking
- Policy change detection
- Strategic insights

**12-Factor Requirements**:
- Input: Market segment + monitoring criteria
- Output: MarketIntelligence dataclass
- Cost: ~$0.15 (continuous monitoring)
- Factor 6: Stateless (no persistent monitoring state)

#### 3. Trend Analyzer Tool ❌
**Source**: `trend_analyzer.py` (300+ lines)
**Functionality**:
- Temporal pattern detection
- Seasonal analysis
- Growth/decline trends
- Predictive insights

**12-Factor Requirements**:
- Input: Historical data array + analysis period
- Output: TrendAnalysis dataclass
- Cost: $0.00 (algorithmic)
- Factor 4: Structured output (trends + predictions)

#### 4. Document Intelligence Tool ❌
**Source**: `pdf_ocr.py` (200+ lines)
**Functionality**:
- PDF text extraction (OCR)
- Document structure analysis
- Key information extraction
- RFP/NOFO parsing

**12-Factor Requirements**:
- Input: PDF file path or bytes
- Output: DocumentIntelligence dataclass
- Cost: ~$0.05 (OCR processing)
- Factor 9: Fast startup (< 2s for typical PDF)

#### 5. Corporate CSR Analyzer Tool ❌
**Source**: `corporate_csr_analyzer.py` (400+ lines)
**Functionality**:
- Corporate social responsibility analysis
- Foundation giving patterns
- Corporate partnership opportunities
- Strategic alignment assessment

**12-Factor Requirements**:
- Input: Corporation data + CSR criteria
- Output: CSRAnalysis dataclass
- Cost: ~$0.08 (AI-enhanced)
- Factor 10: Single responsibility (CSR analysis only)

#### 6. Intelligent Classifier Tool ❌
**Source**: `intelligent_classifier.py` (300+ lines)
**Functionality**:
- Opportunity type classification
- Category detection
- Tag generation
- Priority assignment

**12-Factor Requirements**:
- Input: Opportunity text + classification rules
- Output: Classification dataclass
- Cost: ~$0.02 (AI classification)
- Factor 6: Stateless (no learning between runs)

#### 7. Enhanced Historical Funding Tool ✅ (EXISTS but NOT integrated)
**Source**: `tools/historical-funding-analyzer-tool/`
**Status**: Tool exists but not integrated with intelligence router
**Action Required**: API integration only

### Intelligence Router Migration

**Current State** (intelligence.py):
```python
# Lines 16-19: DELETED IMPORTS
# from src.intelligence.standard_tier_processor import StandardTierProcessor
# from src.intelligence.enhanced_tier_processor import EnhancedTierProcessor
# from src.intelligence.complete_tier_processor import CompleteTierProcessor

# Lines 254, 274, 304: BROKEN CALLS
result = await standard_tier_processor.process_opportunity(...)  # ❌ DELETED
result = await enhanced_tier_processor.process_opportunity(...)  # ❌ DELETED
result = await complete_tier_processor.process_opportunity(...)  # ❌ DELETED
```

**Required Migration**:
1. Replace tier processors with Tool 2 (Deep Intelligence Tool)
2. Map tier → depth parameter:
   - `CURRENT` → `quick` depth ($0.75, 5-10 min)
   - `STANDARD` → `standard` depth ($7.50, 15-20 min)
   - `ENHANCED` → `enhanced` depth ($22.00, 30-45 min)
   - `COMPLETE` → `complete` depth ($42.00, 45-60 min)
3. Integrate add-on modules with specialized tools
4. Update cost calculator to use tool costs

### Add-On Modules Mapping

**Current Add-Ons** (intelligence.py lines 30-36):
```python
class AddOnModule(str, Enum):
    BOARD_NETWORK = "board_network_analysis"           # Tool 12 ✅
    DECISION_MAKER = "decision_maker_intelligence"     # Tool 2 depth ✅
    RFP_ANALYSIS = "complete_rfp_analysis"             # Tool 4 (Document) ❌
    HISTORICAL_PATTERNS = "historical_success_patterns" # Tool 22 ✅
    WARM_INTRODUCTIONS = "warm_introduction_pathways"  # Tool 12 ✅
    COMPETITIVE_ANALYSIS = "competitive_deep_dive"     # Tool 1 (Competitive) ❌
```

**Tool Mapping**:
- ✅ Board Network → Tool 12 (Network Intelligence)
- ✅ Decision Maker → Tool 2 (Deep Intelligence - enhanced depth)
- ❌ RFP Analysis → Tool 4 (Document Intelligence) - NEEDED
- ✅ Historical Patterns → Tool 22 (Historical Funding Analyzer)
- ✅ Warm Introductions → Tool 12 (Network Intelligence)
- ❌ Competitive Analysis → Tool 1 (Competitive Intelligence) - NEEDED

---

## PART 3: MIGRATION EXECUTION PLAN

### Phase 1: Foundation (Week 1) - 8-12 hours

#### Task 1.1: Create Missing Tools (6-8 hours)
1. **Competitive Intelligence Tool**
   - Location: `tools/competitive-intelligence-tool/`
   - Source: `src/processors/analysis/competitive_intelligence_processor.py`
   - Files needed:
     - `12factors.toml`
     - `app/competitive_intelligence_tool.py`
     - `app/competitive_models.py`
   - Estimated: 2-3 hours

2. **Market Intelligence Monitor Tool**
   - Location: `tools/market-intelligence-monitor-tool/`
   - Source: `src/processors/analysis/market_intelligence_monitor.py`
   - Estimated: 2-3 hours

3. **Trend Analyzer Tool**
   - Location: `tools/trend-analyzer-tool/`
   - Source: `src/processors/analysis/trend_analyzer.py`
   - Estimated: 1-2 hours

4. **Document Intelligence Tool**
   - Location: `tools/document-intelligence-tool/`
   - Source: `src/processors/analysis/pdf_ocr.py`
   - Estimated: 1-2 hours

5. **Corporate CSR Analyzer Tool**
   - Location: `tools/corporate-csr-analyzer-tool/`
   - Source: `src/processors/analysis/corporate_csr_analyzer.py`
   - Estimated: 2-3 hours

6. **Intelligent Classifier Tool**
   - Location: `tools/intelligent-classifier-tool/`
   - Source: `src/processors/analysis/intelligent_classifier.py`
   - Estimated: 1-2 hours

#### Task 1.2: Update Tool Registry (30 min)
- Add 6 new tools to `src/core/tool_registry.py`
- Verify auto-discovery works
- Update tool count (23 → 29 operational tools)

#### Task 1.3: Create Intelligence Orchestrator (1-2 hours)
**New File**: `src/intelligence/intelligence_orchestrator.py`

**Purpose**: Replace tier processors with tool-based orchestration

**Responsibilities**:
- Map tier → tool depth configuration
- Orchestrate add-on modules
- Cost tracking
- Result aggregation

**Interface**:
```python
class IntelligenceOrchestrator:
    async def execute_tier_analysis(
        self,
        tier: ServiceTier,
        profile_id: str,
        opportunity_id: str,
        add_ons: List[AddOnModule]
    ) -> IntelligenceResult:
        # Tool 2 (Deep Intelligence) - base analysis
        # Tool 22 (Historical Funding) - if STANDARD+ tier
        # Tool 12 (Network) - if BOARD_NETWORK or WARM_INTRODUCTIONS
        # Tool 1 (Competitive) - if COMPETITIVE_ANALYSIS
        # Tool 4 (Document) - if RFP_ANALYSIS
        ...
```

### Phase 2: API Integration (Week 2) - 6-8 hours

#### Task 2.1: Update Intelligence Router (3-4 hours)
**File**: `src/web/routers/intelligence.py`

**Changes Required**:
```python
# Line 16-19: REPLACE deleted imports
from src.intelligence.intelligence_orchestrator import IntelligenceOrchestrator

# Line 228-231: REPLACE tier processor instances
orchestrator = IntelligenceOrchestrator()

# Line 254-267: REPLACE StandardTierProcessor call
result = await orchestrator.execute_tier_analysis(
    tier=ServiceTier.STANDARD,
    profile_id=profile_id,
    opportunity_id=request.opportunity_id,
    add_ons=request.add_ons
)

# Similar for ENHANCED (274-288), COMPLETE (301-319)
```

#### Task 2.2: Update Cost Calculator (1-2 hours)
**File**: `src/web/routers/intelligence.py` (lines 88-169)

**Changes Required**:
- Update base costs to match Tool 2 depths
- Update add-on costs to match new tool costs
- Add cost estimation for new tools

#### Task 2.3: Integration Testing (2-3 hours)
- Test all 4 tier endpoints
- Test all 6 add-on modules
- Test cost estimation
- Test task management
- Verify Tool 2 integration

### Phase 3: Deprecation & Cleanup (Week 3) - 4-6 hours

#### Task 3.1: Move Legacy Code (2-3 hours)
```bash
# Create deprecation directory
mkdir -p src/intelligence/_deprecated

# Move legacy module
mv src/intelligence/historical_funding_analyzer.py \
   src/intelligence/_deprecated/

# Move legacy processors (7 processors)
mv src/processors/analysis/competitive_intelligence_processor.py \
   src/processors/analysis/_deprecated/

# Repeat for all 7 gap-filled processors
```

#### Task 3.2: Update Documentation (1-2 hours)
**Files to Update**:
1. `CLAUDE.md` - Update tool count (23 → 29)
2. `tools/TOOLS_INVENTORY.md` - Add 6 new tools
3. `docs/12-factor-transformation/` - Update status
4. `PHASE_9_WEEK4_PROGRESS.md` - Mark intelligence complete

#### Task 3.3: Create Migration Summary (1 hour)
**New File**: `docs/INTELLIGENCE_MIGRATION_SUMMARY.md`

**Contents**:
- Before/after architecture comparison
- Tool mapping table
- API endpoint migration guide
- Cost structure changes
- Performance improvements

---

## PART 4: VALIDATION CHECKLIST

### Functional Validation
- [ ] All 4 tier endpoints work (CURRENT, STANDARD, ENHANCED, COMPLETE)
- [ ] All 6 add-on modules integrate correctly
- [ ] Cost estimation matches actual costs
- [ ] Task management tracks progress
- [ ] Tool 2 (Deep Intelligence) handles all depths
- [ ] Tool 22 (Historical Funding) integrates with STANDARD+ tiers
- [ ] Tool 12 (Network) provides board/warm intro analysis
- [ ] Tool 1 (Competitive) provides competitive analysis
- [ ] Tool 4 (Document) provides RFP/NOFO analysis
- [ ] All 29 tools registered and discoverable

### 12-Factor Compliance
- [ ] All 6 new tools have `12factors.toml` files
- [ ] All tools follow BaseTool framework
- [ ] All tools return ToolResult[T] with structured outputs
- [ ] All tools are stateless (Factor 6)
- [ ] All tools have single responsibility (Factor 10)
- [ ] All tools support async execution (Factor 8)
- [ ] All tools have cost estimation (Factor 3 - config)

### Performance Validation
- [ ] CURRENT tier: 5-10 min execution ✅
- [ ] STANDARD tier: 15-20 min execution ✅
- [ ] ENHANCED tier: 30-45 min execution ✅
- [ ] COMPLETE tier: 45-60 min execution ✅
- [ ] Add-on modules: +5-15 min each ✅
- [ ] API response time: < 500ms for sync endpoints ✅
- [ ] Background task initiation: < 100ms ✅

### Cost Validation
- [ ] CURRENT tier: $0.75 actual cost matches estimate
- [ ] STANDARD tier: $7.50 actual cost matches estimate
- [ ] ENHANCED tier: $22.00 actual cost matches estimate
- [ ] COMPLETE tier: $42.00 actual cost matches estimate
- [ ] Add-on costs match tool costs
- [ ] Total cost tracking accurate across all tools

---

## PART 5: EFFORT ESTIMATION

### Time Breakdown

**Phase 1: Foundation (Week 1)**
- Create 6 missing tools: 10-16 hours
- Update tool registry: 0.5 hour
- Create orchestrator: 1-2 hours
- **Total**: 11.5-18.5 hours

**Phase 2: API Integration (Week 2)**
- Update intelligence router: 3-4 hours
- Update cost calculator: 1-2 hours
- Integration testing: 2-3 hours
- **Total**: 6-9 hours

**Phase 3: Deprecation & Cleanup (Week 3)**
- Move legacy code: 2-3 hours
- Update documentation: 1-2 hours
- Create migration summary: 1 hour
- **Total**: 4-6 hours

**GRAND TOTAL**: 21.5-33.5 hours

**Recommended Schedule**: 3 weeks @ 8-12 hours/week

---

## PART 6: RISK MITIGATION

### Risk 1: Breaking Changes
**Mitigation**:
- Create `intelligence_router_v2.py` alongside existing
- Test thoroughly before switching
- Keep legacy code for 1 release cycle

### Risk 2: Cost Discrepancies
**Mitigation**:
- Add cost monitoring to orchestrator
- Log actual vs estimated costs
- Alert on >10% variance

### Risk 3: Performance Degradation
**Mitigation**:
- Benchmark current tier performance
- Monitor tool execution times
- Optimize slow paths

### Risk 4: Missing Functionality
**Mitigation**:
- Comprehensive gap analysis (this document)
- Create migration test suite
- User acceptance testing

---

## PART 7: SUCCESS CRITERIA

### Migration Complete When:
1. ✅ All 6 missing tools created and operational
2. ✅ Tool count: 29 operational tools (was 23)
3. ✅ Intelligence router fully migrated to orchestrator
4. ✅ All 4 tier endpoints functional
5. ✅ All 6 add-on modules integrated
6. ✅ Cost estimation accurate (< 5% variance)
7. ✅ Performance meets SLA (tier time windows)
8. ✅ Legacy code deprecated and documented
9. ✅ 100% 12-factor compliance
10. ✅ API documentation updated

### Measurable Outcomes:
- **Tool Coverage**: 23 → 29 tools (+26%)
- **12-Factor Compliance**: 100% (all tools)
- **API Uptime**: 99.9% (no broken endpoints)
- **Cost Accuracy**: ±5% (actual vs estimated)
- **Performance**: Meets tier SLA windows

---

## APPENDIX A: Tool Creation Template

**Example**: Competitive Intelligence Tool

### Directory Structure
```
tools/competitive-intelligence-tool/
├── 12factors.toml
├── app/
│   ├── __init__.py
│   ├── competitive_intelligence_tool.py
│   └── competitive_models.py
└── tests/
    └── test_competitive_intelligence.py
```

### 12factors.toml
```toml
[tool]
name = "Competitive Intelligence Tool"
version = "1.0.0"
status = "operational"
category = "analysis"

[tool.metadata]
description = "Competitive landscape analysis and strategic positioning"
purpose = "Analyze competitive environment, market share, and strategic advantages"
single_responsibility = "Competitive intelligence only - no market monitoring or trend analysis"
cost_per_operation = 0.10
replaces = ["competitive_intelligence_processor.py"]

[tool.factors]
factor_1_codebase = "Single tool in tools/competitive-intelligence-tool/"
factor_2_dependencies = "Core framework via src/core/tool_framework, OpenAI for AI analysis"
factor_3_config = "Analysis parameters configurable via config dict"
factor_4_structured_output = "Returns CompetitiveAnalysis dataclass with landscape, positioning, insights"
factor_5_build_run_separation = "Tool execution separate from analysis logic"
factor_6_stateless = "No state between executions - pure function analysis"
factor_7_port_binding = "Async function interface via execute() method"
factor_8_concurrency = "Async-ready for parallel analysis"
factor_9_disposability = "Fast startup (<500ms), immediate analysis"
factor_10_single_responsibility = "Competitive analysis only - no financial scoring, no risk assessment"
factor_11_autonomous = "Operates independently with competitor data inputs"
factor_12_api_first = "Function-based API with type-safe interfaces"

[tool.inputs]
type = "CompetitiveAnalysisInput"
required_fields = ["organization_ein", "competitor_list", "market_segment"]
optional_fields = ["analysis_depth", "include_swot", "include_market_share"]

[tool.outputs]
type = "CompetitiveAnalysis"
fields = ["landscape_overview", "competitive_position", "market_share_estimate", "swot_analysis", "strategic_insights", "recommendations"]

[tool.performance]
typical_duration_seconds = 8
ai_calls_per_execution = 1
cost_per_execution = 0.10

[tool.integration]
module_path = "tools.competitive-intelligence-tool.app.competitive_intelligence_tool"
class_name = "CompetitiveIntelligenceTool"
convenience_function = "analyze_competitive_landscape"
```

### competitive_intelligence_tool.py
```python
from typing import Optional, List
from dataclasses import dataclass
from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext

@dataclass
class CompetitiveAnalysisInput:
    organization_ein: str
    competitor_list: List[str]
    market_segment: str
    analysis_depth: str = "standard"
    include_swot: bool = True
    include_market_share: bool = True

@dataclass
class CompetitiveAnalysis:
    organization_ein: str
    landscape_overview: str
    competitive_position: str
    market_share_estimate: float
    swot_analysis: dict
    strategic_insights: List[str]
    recommendations: List[str]
    confidence_score: float

class CompetitiveIntelligenceTool(BaseTool[CompetitiveAnalysis]):
    """
    12-Factor Competitive Intelligence Tool

    Factor 4: Returns structured CompetitiveAnalysis
    Factor 6: Stateless - pure function analysis
    Factor 10: Single responsibility - competitive analysis only
    """

    def get_tool_name(self) -> str:
        return "Competitive Intelligence Tool"

    def get_tool_version(self) -> str:
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        return "Competitive landscape analysis and strategic positioning"

    async def _execute(
        self,
        context: ToolExecutionContext,
        analysis_input: CompetitiveAnalysisInput
    ) -> CompetitiveAnalysis:
        # Implementation here
        ...

# Convenience function
async def analyze_competitive_landscape(
    organization_ein: str,
    competitor_list: List[str],
    market_segment: str,
    config: Optional[dict] = None
) -> ToolResult[CompetitiveAnalysis]:
    tool = CompetitiveIntelligenceTool(config)
    analysis_input = CompetitiveAnalysisInput(
        organization_ein=organization_ein,
        competitor_list=competitor_list,
        market_segment=market_segment
    )
    return await tool.execute(analysis_input=analysis_input)
```

---

## APPENDIX B: Intelligence Orchestrator Interface

```python
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from src.core.tool_framework import ToolResult
from tools.deep_intelligence_tool.app.deep_intelligence_tool import DeepIntelligenceTool, AnalysisDepth
from tools.historical_funding_analyzer_tool.app.historical_tool import HistoricalFundingAnalyzerTool
from tools.network_intelligence_tool.app.network_intelligence_tool import NetworkIntelligenceTool
from tools.competitive_intelligence_tool.app.competitive_intelligence_tool import CompetitiveIntelligenceTool
from tools.document_intelligence_tool.app.document_intelligence_tool import DocumentIntelligenceTool

class ServiceTier(str, Enum):
    CURRENT = "current"
    STANDARD = "standard"
    ENHANCED = "enhanced"
    COMPLETE = "complete"

class AddOnModule(str, Enum):
    BOARD_NETWORK = "board_network_analysis"
    DECISION_MAKER = "decision_maker_intelligence"
    RFP_ANALYSIS = "complete_rfp_analysis"
    HISTORICAL_PATTERNS = "historical_success_patterns"
    WARM_INTRODUCTIONS = "warm_introduction_pathways"
    COMPETITIVE_ANALYSIS = "competitive_deep_dive"

@dataclass
class IntelligenceResult:
    tier: ServiceTier
    profile_id: str
    opportunity_id: str
    add_ons_executed: List[AddOnModule]

    # Core analysis (Tool 2)
    deep_intelligence: Dict[str, Any]

    # Optional add-on results
    historical_analysis: Optional[Dict[str, Any]] = None
    network_analysis: Optional[Dict[str, Any]] = None
    competitive_analysis: Optional[Dict[str, Any]] = None
    document_analysis: Optional[Dict[str, Any]] = None

    # Metadata
    total_processing_cost: float = 0.0
    processing_time_seconds: float = 0.0
    timestamp: str = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier": self.tier.value,
            "profile_id": self.profile_id,
            "opportunity_id": self.opportunity_id,
            "add_ons_executed": [a.value for a in self.add_ons_executed],
            "deep_intelligence": self.deep_intelligence,
            "historical_analysis": self.historical_analysis,
            "network_analysis": self.network_analysis,
            "competitive_analysis": self.competitive_analysis,
            "document_analysis": self.document_analysis,
            "total_processing_cost": self.total_processing_cost,
            "processing_time_seconds": self.processing_time_seconds,
            "timestamp": self.timestamp
        }

class IntelligenceOrchestrator:
    """
    Orchestrates intelligence analysis using 12-factor tools
    Replaces deleted tier processors
    """

    TIER_DEPTH_MAPPING = {
        ServiceTier.CURRENT: AnalysisDepth.QUICK,
        ServiceTier.STANDARD: AnalysisDepth.STANDARD,
        ServiceTier.ENHANCED: AnalysisDepth.ENHANCED,
        ServiceTier.COMPLETE: AnalysisDepth.COMPLETE
    }

    def __init__(self):
        self.deep_intelligence_tool = DeepIntelligenceTool()
        self.historical_tool = HistoricalFundingAnalyzerTool()
        self.network_tool = NetworkIntelligenceTool()
        self.competitive_tool = CompetitiveIntelligenceTool()
        self.document_tool = DocumentIntelligenceTool()

    async def execute_tier_analysis(
        self,
        tier: ServiceTier,
        profile_id: str,
        opportunity_id: str,
        add_ons: List[AddOnModule] = None
    ) -> IntelligenceResult:
        """Execute tiered intelligence analysis using tools"""

        start_time = time.time()
        total_cost = 0.0
        add_ons = add_ons or []

        # 1. Core Deep Intelligence (Tool 2) - ALL TIERS
        depth = self.TIER_DEPTH_MAPPING[tier]
        deep_result = await self.deep_intelligence_tool.execute(
            profile_id=profile_id,
            opportunity_id=opportunity_id,
            depth=depth
        )
        total_cost += deep_result.metadata.get("cost", 0)

        # 2. Historical Funding Analysis - STANDARD+ tiers
        historical_result = None
        if tier in [ServiceTier.STANDARD, ServiceTier.ENHANCED, ServiceTier.COMPLETE]:
            historical_result = await self.historical_tool.execute(
                organization_ein=profile_id,
                historical_data=...  # From USASpending
            )
            total_cost += historical_result.metadata.get("cost", 0)

        # 3. Add-On Modules
        network_result = None
        competitive_result = None
        document_result = None

        if AddOnModule.BOARD_NETWORK in add_ons or AddOnModule.WARM_INTRODUCTIONS in add_ons:
            network_result = await self.network_tool.execute(
                organization_ein=profile_id,
                analysis_type="board_network" if AddOnModule.BOARD_NETWORK in add_ons else "warm_introductions"
            )
            total_cost += network_result.metadata.get("cost", 0)

        if AddOnModule.COMPETITIVE_ANALYSIS in add_ons:
            competitive_result = await self.competitive_tool.execute(
                organization_ein=profile_id,
                competitor_list=...,  # From discovery
                market_segment=...
            )
            total_cost += competitive_result.metadata.get("cost", 0)

        if AddOnModule.RFP_ANALYSIS in add_ons:
            document_result = await self.document_tool.execute(
                document_path=...,  # From opportunity
                analysis_type="rfp"
            )
            total_cost += document_result.metadata.get("cost", 0)

        # 4. Aggregate Results
        processing_time = time.time() - start_time

        return IntelligenceResult(
            tier=tier,
            profile_id=profile_id,
            opportunity_id=opportunity_id,
            add_ons_executed=add_ons,
            deep_intelligence=deep_result.data.to_dict(),
            historical_analysis=historical_result.data.to_dict() if historical_result else None,
            network_analysis=network_result.data.to_dict() if network_result else None,
            competitive_analysis=competitive_result.data.to_dict() if competitive_result else None,
            document_analysis=document_result.data.to_dict() if document_result else None,
            total_processing_cost=total_cost,
            processing_time_seconds=processing_time,
            timestamp=datetime.now().isoformat()
        )
```

---

**END OF MIGRATION PLAN**

*Next Steps*:
1. Review and approve this plan
2. Begin Phase 1: Create 6 missing tools (10-16 hours)
3. Proceed to Phase 2: API integration (6-9 hours)
4. Complete Phase 3: Cleanup and documentation (4-6 hours)

*Total Effort*: 21.5-33.5 hours over 3 weeks
