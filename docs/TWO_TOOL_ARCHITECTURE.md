# Two-Tool Architecture - Catalynx Grant Intelligence

**Architecture Version**: 2.0
**Date**: 2025-09-30
**Status**: Operational (21/22 tools complete)

---

## Executive Summary

The Catalynx platform uses a **two-tool pipeline** with human-in-the-loop decision making to efficiently process grant opportunities from discovery through deep analysis.

### Core Principle

```
MASS SCREENING → HUMAN JUDGMENT → DEEP ANALYSIS
    Tool 1    →   Human Gateway  →    Tool 2
```

### Why Two Tools?

**Traditional Approach** (inefficient):
- Analyze all 200 opportunities deeply at $42 each = $8,400
- Most opportunities are poor fits
- Wasted time and money on non-viable options

**Two-Tool Approach** (efficient):
- Screen 200 opportunities at $0.02 each = $4.00
- Human selects 10 promising opportunities
- Deep analyze 10 at $7.50-$42.00 each = $75-$420
- **Total: $79-$424 vs. $8,400** (95%+ savings)

---

## Architecture Overview

### Tool 1: Opportunity Screening Tool
**Purpose**: Fast, cost-effective screening of large opportunity sets
**Input**: 100s-1000s of opportunities
**Output**: Scored and ranked shortlist (~10 opportunities)
**Cost**: $0.02 per opportunity (~$4 for 200)
**Time**: ~5 seconds per opportunity

**Modes**:
1. **Fast Mode** ($0.0004/opportunity, ~2 sec)
   - Basic eligibility and fit assessment
   - Equivalent to legacy PLAN tab
   - For initial discovery

2. **Thorough Mode** ($0.02/opportunity, ~5 sec)
   - Comprehensive screening with success scoring
   - Equivalent to legacy ANALYZE tab
   - For final shortlist creation

**Replaces**:
- `ai_lite_unified_processor.py` (PLAN tab)
- `ai_heavy_light_analyzer.py` (ANALYZE tab)

### Human Gateway (Manual Review)
**Purpose**: Strategic judgment and research augmentation
**Activities**:
- Review screening results and scores
- Conduct manual web research
- Evaluate strategic fit and priorities
- Select ~10 opportunities for deep analysis
- Add contextual notes and insights

**Why Human-in-the-Loop**:
- Humans excel at strategic judgment
- Context and nuance matter
- Prevents wasted AI costs on poor fits
- Enables research augmentation

### Tool 2: Deep Intelligence Tool
**Purpose**: Comprehensive analysis of selected opportunities
**Input**: ~10 pre-screened opportunities
**Output**: Detailed intelligence reports with recommendations
**Cost**: $0.75-$42.00 per opportunity (depth-dependent)
**Time**: 5-60 minutes per opportunity

**Depth Levels**:
1. **Quick** ($0.75, 5-10 min)
   - 4-stage AI analysis (PLAN → ANALYZE → EXAMINE → APPROACH)
   - Multi-dimensional scoring
   - Strategic recommendations
   - Equivalent to legacy CURRENT tier

2. **Standard** ($7.50, 15-20 min)
   - + Historical funding analysis
   - + Geographic distribution patterns
   - + Temporal trends
   - Equivalent to legacy STANDARD tier

3. **Enhanced** ($22.00, 30-45 min)
   - + Document analysis (RFPs, guidelines)
   - + Network intelligence (board connections)
   - + Decision maker profiling
   - Equivalent to legacy ENHANCED tier

4. **Complete** ($42.00, 45-60 min)
   - + Policy analysis and alignment
   - + Real-time monitoring setup
   - + 26+ page comprehensive reports
   - + Strategic consulting insights
   - Equivalent to legacy COMPLETE tier

**Replaces**:
- `ai_heavy_deep_researcher.py` (EXAMINE tab)
- `ai_heavy_researcher.py` (APPROACH tab)
- `current_tier_processor.py` ($0.75 tier)
- `standard_tier_processor.py` ($7.50 tier)
- `enhanced_tier_processor.py` ($22.00 tier)
- `complete_tier_processor.py` ($42.00 tier)

---

## Workflow Example

### Scenario: Heroes Bridge seeks health grants

**Step 1: Discovery** (Tool 1 - Fast Mode)
```python
# Screen 200 opportunities
from tools.opportunity_screening_tool import screen_opportunities

results = await screen_opportunities(
    opportunities=opportunity_list,  # 200 items
    organization_profile=heroes_bridge_profile,
    mode="fast"  # $0.0004 each = $0.08 total
)

# Results: 200 opportunities scored, ranked, and filtered
# Top 50 meet basic eligibility
```

**Cost**: $0.08
**Time**: ~7 minutes
**Output**: Ranked list of 200 opportunities with eligibility scores

---

**Step 2: Refinement** (Tool 1 - Thorough Mode)
```python
# Deep screen top 50
refined_results = await screen_opportunities(
    opportunities=top_50_opportunities,
    organization_profile=heroes_bridge_profile,
    mode="thorough"  # $0.02 each = $1.00 total
)

# Results: 50 opportunities with success probability scores
# Top 20 show strong potential
```

**Cost**: $1.00
**Time**: ~4 minutes
**Output**: 20 opportunities with detailed scoring and success probability

---

**Step 3: Human Review** (Manual Gateway)
- Review top 20 opportunities
- Conduct web research on grantors
- Check organizational priorities
- Read RFP requirements
- **Select 10 for deep analysis**

**Cost**: $0 (staff time)
**Time**: 30-60 minutes
**Output**: Curated list of 10 high-priority opportunities

---

**Step 4: Deep Analysis** (Tool 2 - Configurable Depth)
```python
# Analyze selected 10 opportunities
from tools.deep_intelligence_tool import analyze_opportunity

for opportunity in selected_10:
    # Choose depth based on importance
    depth = "standard" if opportunity.priority == "medium" else "enhanced"

    intelligence = await analyze_opportunity(
        opportunity_id=opportunity.id,
        organization_profile=heroes_bridge_profile,
        depth=depth,  # $7.50 or $22.00 per opportunity
        include_scoring=True,
        include_network=True,
        include_report=True
    )

# Results: Comprehensive intelligence packages for each opportunity
```

**Cost**: $75-$220 (mix of standard/enhanced)
**Time**: 2-5 hours total
**Output**: 10 comprehensive intelligence reports with recommendations

---

**Total Pipeline Economics**:
- **Fast Screening**: $0.08 (200 opportunities)
- **Thorough Screening**: $1.00 (50 opportunities)
- **Deep Analysis**: $75-$220 (10 opportunities)
- **TOTAL**: ~$76-$221 vs. $8,400 traditional approach
- **SAVINGS**: 97%+ cost reduction

---

## Supporting Tools (20 Additional Tools)

The two main tools are supported by 20 specialized tools:

### Data Acquisition (9 tools)
1. **XML 990 Parser** - Parse nonprofit 990 filings
2. **XML 990-PF Parser** - Parse foundation 990-PF filings
3. **XML 990-EZ Parser** - Parse small nonprofit 990-EZ filings
4. **BMF Filter Tool** - IRS Business Master File filtering
5. **Form 990 Analysis** - Financial metrics extraction
6. **Form 990 ProPublica** - ProPublica API enrichment
7. **Foundation Grant Intelligence** - Grant-making analysis
8. **ProPublica API Enrichment** - Additional data enrichment
9. **XML Schedule Parser** - Schedule extraction

### Intelligence & Scoring (4 tools)
10. **Financial Intelligence** - Comprehensive financial analysis ($0.03)
11. **Risk Intelligence** - Multi-dimensional risk assessment ($0.02)
12. **Network Intelligence** - Board network and relationships ($0.04)
13. **Schedule I Grant Analyzer** - Foundation patterns ($0.03)

### Data Quality & Validation (2 tools)
14. **Data Validator** - Quality and completeness validation ($0.00)
15. **EIN Validator** - EIN format validation and lookup ($0.00)

### Discovery & Research (1 tool)
17. **BMF Discovery** - Multi-criteria nonprofit discovery ($0.00)

### Output & Delivery (3 tools)
18. **Data Export** - Multi-format export (JSON, CSV, Excel, PDF) ($0.00)
19. **Grant Package Generator** - Application package assembly ($0.00)
21. **Report Generator** - Professional report templates ($0.00)

### Analysis Foundation (2 tools)
20. **Multi-Dimensional Scorer** - 5-stage dimensional scoring ($0.00)
22. **Historical Funding Analyzer** - Funding pattern detection (planned)

---

## Integration Architecture

### API Layer
```python
# Unified tool execution
POST /api/v1/tools/{tool_name}/execute

# Workflow orchestration
POST /api/v1/workflows/{workflow_name}/execute

# Real-time progress
WebSocket /api/v1/ws/workflows/{session_id}
```

### Workflow Definition (YAML)
```yaml
name: grant_discovery_workflow
version: 1.0

steps:
  - id: fast_screen
    tool: opportunity-screening-tool
    params:
      mode: fast
      opportunities: ${context.opportunity_list}

  - id: thorough_screen
    tool: opportunity-screening-tool
    depends_on: [fast_screen]
    params:
      mode: thorough
      opportunities: ${steps.fast_screen.top_50}

  - id: human_review
    type: human_gateway
    depends_on: [thorough_screen]
    prompt: "Review and select 10 opportunities"

  - id: deep_analysis
    tool: deep-intelligence-tool
    depends_on: [human_review]
    params:
      opportunities: ${steps.human_review.selected}
      depth: ${context.depth_preference}

  - id: generate_reports
    tool: report-generator-tool
    depends_on: [deep_analysis]
    params:
      template: comprehensive
      intelligence_data: ${steps.deep_analysis.output}
```

---

## Technical Implementation

### Tool Framework (12-Factor Compliant)
```python
from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext

class OpportunityScreeningTool(BaseTool[ScreeningOutput]):
    """
    12-Factor Compliant Screening Tool

    Factor 4: Structured outputs (ScreeningOutput dataclass)
    Factor 6: Stateless execution (no persistent state)
    Factor 10: Single responsibility (screening only)
    """

    async def _execute(
        self,
        context: ToolExecutionContext,
        opportunities: List[Dict],
        organization_profile: Dict,
        mode: str = "fast"
    ) -> ScreeningOutput:
        # Implementation
        pass
```

### Structured Outputs (BAML Validation)
```python
@dataclass
class ScreeningOutput:
    """Structured screening results"""
    opportunities_screened: int
    opportunities_qualified: int
    top_opportunities: List[ScoredOpportunity]
    screening_time_seconds: float
    total_cost: float
    recommendations: List[str]
```

### Configuration (12factors.toml)
```toml
[tool]
name = "Opportunity Screening Tool"
version = "1.0.0"
status = "operational"

[tool.metadata]
description = "Fast, cost-effective opportunity screening"
cost_per_operation_fast = 0.0004
cost_per_operation_thorough = 0.02
replaces = ["ai_lite_unified", "ai_heavy_light"]

[tool.modes]
fast = "Basic eligibility and fit assessment"
thorough = "Comprehensive screening with success scoring"
```

---

## Performance Characteristics

### Tool 1: Opportunity Screening
- **Throughput**: 720 opportunities/hour (fast), 720 opportunities/hour (thorough)
- **Latency**: 2-5 seconds per opportunity
- **Cost**: $0.0004-$0.02 per opportunity
- **Scalability**: Parallel execution, 10+ concurrent screens

### Tool 2: Deep Intelligence
- **Throughput**: 1-12 opportunities/hour (depth-dependent)
- **Latency**: 5-60 minutes per opportunity
- **Cost**: $0.75-$42.00 per opportunity
- **Quality**: Masters thesis-level analysis (complete depth)

### Supporting Tools
- **Zero-cost tools** (14 tools): <100ms execution, $0.00 cost
- **Low-cost intelligence** (4 tools): ~1s execution, $0.02-$0.04 cost
- **Scoring** (Tool 20): <0.05ms execution, $0.00 cost
- **Reporting** (Tool 21): 1-2s execution, $0.00 cost

---

## Comparison to Legacy System

### Before (Tier System)
```
Every opportunity → $42.00 complete tier analysis
200 opportunities = $8,400 total cost
No screening, all opportunities analyzed deeply
High waste on poor-fit opportunities
```

**Problems**:
- Expensive ($8,400 for 200 opportunities)
- Time-consuming (100+ hours)
- No prioritization mechanism
- Poor ROI on low-fit opportunities

### After (Two-Tool System)
```
200 opportunities → $0.02 screening = $4.00
Human selects 10 → $7.50-$42.00 deep analysis = $75-$420
Total: $79-$424 for 200 opportunities
```

**Benefits**:
- Cost-effective (95%+ savings)
- Time-efficient (2-5 hours vs. 100 hours)
- Human judgment integrated
- High ROI on selected opportunities

---

## Future Enhancements

### Phase 9: Workflow UI (Deferred)
- Visual workflow builder
- Real-time progress visualization
- Human gateway interface improvements
- Batch operation support

### Phase 10: Government Tools
- Grants.gov opportunity processor
- USASpending awards processor
- State grants discovery tool

### Advanced Features
- Machine learning scoring models
- Automated opportunity monitoring
- Predictive success analytics
- Real-time funder tracking

---

## See Also

- [Migration History](MIGRATION_HISTORY.md) - Complete transformation timeline
- [Tier System](TIER_SYSTEM.md) - Legacy tier system documentation
- [Scoring Algorithms](../SCORING_ALGORITHMS.md) - Multi-dimensional scoring details
- [Transformation Plan](12-factor-transformation/TRANSFORMATION_PLAN_V3_FINAL.md) - Detailed implementation plan
- [Tool Inventory](../tools/TOOLS_INVENTORY.md) - Complete tool catalog

---

**Last Updated**: 2025-09-30
**Architecture Status**: Operational (95% complete)
**Next Milestone**: Phase 6 (Web Integration + Testing)
