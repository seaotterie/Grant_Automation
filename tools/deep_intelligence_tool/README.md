# Deep Intelligence Tool

**12-Factor Compliant Comprehensive Grant Intelligence Analysis Tool**

## Purpose

Stage 2 of two-tool architecture: Deep intelligence analysis of ~10 selected opportunities with configurable depth levels matching 4-tier business packages.

**Pipeline Position**:
1. Screening Tool: 200 opportunities → ~10 selected
2. Human Gateway: Manual review and selection
3. **Deep Intelligence Tool**: Comprehensive analysis at chosen depth
4. Decision: Go/no-go on proposal development

## Depth Levels

### Quick Depth ($0.75, 5-10 min)
**Equivalent**: CURRENT tier
**Features**:
- ✅ Strategic Fit Analysis (PLAN stage)
- ✅ Financial Viability Analysis (ANALYZE stage)
- ✅ Operational Readiness Analysis (EXAMINE stage)
- ✅ Risk Assessment (APPROACH stage)
- ✅ Overall score and proceed recommendation
- ✅ Executive summary

### Standard Depth ($7.50, 15-20 min)
**Equivalent**: STANDARD tier
**Features**: Quick depth +
- ✅ Historical Intelligence (past grants, patterns, success factors)
- ✅ Geographic Analysis (alignment, competition, location advantages)

### Enhanced Depth ($22.00, 30-45 min)
**Equivalent**: ENHANCED tier
**Features**: Standard depth +
- ✅ Network Intelligence (board connections, relationships, influence)
- ✅ Relationship Mapping (direct/indirect relationships, cultivation strategy)

### Complete Depth ($42.00, 45-60 min)
**Equivalent**: COMPLETE tier
**Features**: Enhanced depth +
- ✅ Policy Analysis (federal/state alignment, opportunities, advocacy)
- ✅ Strategic Consulting (multi-year strategy, action plans, 26+ page report)

## Usage

### Python API

```python
from tools.deep_intelligence_tool.app import analyze_opportunity

result = await analyze_opportunity(
    opportunity_id="opp-001",
    opportunity_title="Education Innovation Grant",
    opportunity_description="Supporting innovative education programs...",
    funder_name="Smith Foundation",
    funder_type="foundation",
    organization_ein="12-3456789",
    organization_name="Example Nonprofit",
    organization_mission="Improving education access",
    depth="quick",  # or "standard", "enhanced", "complete"
    screening_score=0.85,  # Optional from screening tool
    user_notes="High priority opportunity"  # Optional
)

if result.is_success():
    intelligence = result.data

    print(f"Overall Score: {intelligence.overall_score:.2f}")
    print(f"Proceed: {intelligence.proceed_recommendation}")
    print(f"Success Probability: {intelligence.success_probability.value}")
    print(f"\nExecutive Summary:")
    print(intelligence.executive_summary)

    print(f"\nStrategic Fit: {intelligence.strategic_fit.fit_score:.2f}")
    print(f"Financial Viability: {intelligence.financial_viability.viability_score:.2f}")
    print(f"Operational Readiness: {intelligence.operational_readiness.readiness_score:.2f}")
    print(f"Risk Level: {intelligence.risk_assessment.overall_risk_level.value}")
```

### Batch Analysis

```python
from tools.deep_intelligence_tool.app import analyze_opportunities_batch

opportunities = [
    {
        "id": "opp-001",
        "title": "Grant A",
        "description": "...",
        "funder": "Foundation A",
        "funder_type": "foundation",
        "screening_score": 0.85
    },
    # ... more opportunities
]

results = await analyze_opportunities_batch(
    opportunities=opportunities,
    organization_ein="12-3456789",
    organization_name="Example Nonprofit",
    organization_mission="Improving education",
    depth="standard"
)

for result in results:
    if result.is_success():
        print(f"{result.data.executive_summary}\n")
```

### Using BaseTool Interface

```python
from tools.deep_intelligence_tool.app import DeepIntelligenceTool, DeepIntelligenceInput, AnalysisDepth

tool = DeepIntelligenceTool(config={
    "openai_api_key": "sk-...",
    "default_depth": "quick"
})

intelligence_input = DeepIntelligenceInput(
    opportunity_id="opp-001",
    opportunity_title="Education Grant",
    opportunity_description="...",
    funder_name="Foundation",
    funder_type="foundation",
    organization_ein="12-3456789",
    organization_name="Nonprofit",
    organization_mission="Education",
    depth=AnalysisDepth.QUICK
)

result = await tool.execute(intelligence_input=intelligence_input)
```

## Output Structure

```python
@dataclass
class DeepIntelligenceOutput:
    # Core Analysis (All Depths)
    strategic_fit: StrategicFitAnalysis
    financial_viability: FinancialViabilityAnalysis
    operational_readiness: OperationalReadinessAnalysis
    risk_assessment: RiskAssessment

    # Overall Assessment
    proceed_recommendation: bool
    success_probability: SuccessProbability
    overall_score: float

    # Summary
    executive_summary: str
    key_strengths: List[str]
    key_challenges: List[str]
    recommended_next_steps: List[str]

    # Enhanced Features (Standard+ only)
    historical_intelligence: Optional[HistoricalAnalysis]
    geographic_analysis: Optional[GeographicAnalysis]

    # Advanced Features (Enhanced+ only)
    network_intelligence: Optional[NetworkAnalysis]
    relationship_mapping: Optional[RelationshipMap]

    # Premium Features (Complete only)
    policy_analysis: Optional[PolicyAnalysis]
    strategic_consulting: Optional[StrategicConsultingInsights]

    # Metadata
    depth_executed: str
    processing_time_seconds: float
    api_cost_usd: float
```

## 4-Stage Analysis Framework

All depth levels execute 4-stage AI analysis:

1. **PLAN** - Strategic Fit Analysis
   - Mission, program, geographic alignment
   - Strategic positioning and differentiators

2. **ANALYZE** - Financial Viability Analysis
   - Budget capacity, financial health
   - Resource requirements and strategy

3. **EXAMINE** - Operational Readiness Analysis
   - Capacity, timeline feasibility, infrastructure
   - Capacity gaps and preparation needs

4. **APPROACH** - Risk Assessment
   - Multi-dimensional risk analysis
   - Mitigation strategies and risk management

## Typical Workflow

### Quick Depth ($0.75 each × 10 = $7.50)
- Fast go/no-go decisions
- Initial feasibility assessment
- Identify 2-3 top priorities

### Standard Depth ($7.50 each × 3 = $22.50)
- Top priorities get deeper analysis
- Historical and geographic intelligence
- Final selection for proposals

### Enhanced Depth ($22.00 each × 1 = $22.00)
- High-priority opportunity with network complexity
- Relationship leverage needed
- Strategic positioning required

### Complete Depth ($42.00 each × 1 = $42.00)
- Transformational opportunity
- Multi-year strategic importance
- Executive-level decision support

**Total Pipeline Cost**: $0.68 (screening) + variable (intelligence) = ~$50-100 typical

## 12-Factor Compliance

- ✅ **Factor 4**: Structured DeepIntelligenceOutput with depth-specific modules
- ✅ **Factor 6**: Stateless - no persistent state between runs
- ✅ **Factor 10**: Single Responsibility - deep intelligence analysis only
- ✅ **Factor 8**: Batch processing with concurrent execution

## Testing

```bash
cd tools/deep-intelligence-tool
python -m pytest tests/
```

## Configuration

Environment variables:
- `OPENAI_API_KEY`: Required for AI analysis
- `INTELLIGENCE_DEFAULT_DEPTH`: Optional ("quick", "standard", "enhanced", "complete")

## Tool Registry

Auto-discovered by Tool Registry via `12factors.toml`.

```python
from src.core.tool_registry import get_registry

registry = get_registry()
tool_meta = registry.get_tool("Deep Intelligence Tool")
print(f"Version: {tool_meta.version}")
print(f"Depth Features: {tool_meta.config['tool']['depths']}")
```

## Architecture

```
tools/deep-intelligence-tool/
├── app/
│   ├── intelligence_tool.py     # Main tool (BaseTool)
│   ├── intelligence_models.py   # Comprehensive data models
│   ├── depth_handlers.py        # 4 depth-specific handlers
│   └── __init__.py
├── baml_src/
│   └── intelligence.baml        # BAML schema for all depths
├── tests/
│   ├── test_quick_depth.py
│   ├── test_standard_depth.py
│   ├── test_enhanced_depth.py
│   └── test_complete_depth.py
├── 12factors.toml               # 12-factor configuration
└── README.md                    # This file
```

## Replaced Processors (7 total)

- ✅ `ai_heavy_deep_researcher.py`
- ✅ `ai_heavy_researcher.py`
- ✅ `current_tier_processor.py`
- ✅ `standard_tier_processor.py`
- ✅ `enhanced_tier_processor.py`
- ✅ `complete_tier_processor.py`
- ✅ `enhanced_ai_lite_processor.py`

## Roadmap

- [ ] Implement actual BAML AI calls (currently placeholder analysis)
- [ ] Add caching for repeated opportunity analysis
- [ ] Implement retry logic for AI failures
- [ ] Add performance benchmarking
- [ ] Create integration tests with real opportunities
- [ ] Add PDF report generation for Complete depth

## Related Tools

- **Opportunity Screening Tool**: Stage 1 mass screening
- **Workflow Engine**: Orchestrates screening → intelligence pipeline
- **Tool Registry**: Auto-discovery and metadata management
