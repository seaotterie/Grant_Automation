# Two-Tool AI Architecture: Design Decision Record
**12-Factor Agent Framework Implementation**

**Date**: 2025-09-29
**Status**: APPROVED ✅
**Decision**: Implement two unified AI tools instead of one or eight

---

## EXECUTIVE SUMMARY

**Architecture Decision**: Two unified AI tools with human-in-the-loop gateway

```
TOOL 1: Opportunity Screening Tool
├── Purpose: Narrow 100s of opportunities → 10s
├── Speed: Fast screening (seconds per opportunity)
├── Cost: Low ($0.0004 - $0.04 per opportunity)
└── Output: Scored, ranked shortlist

        ↓
    HUMAN GATEWAY (User interaction point)
    • Manual review and filtering
    • Web scraping for additional context
    • Internal analysis and research
    • User feedback and adjustments
    • Final selection of opportunities to analyze deeply
        ↓

TOOL 2: Deep Intelligence Tool
├── Purpose: Comprehensive analysis of selected 10s
├── Depth: Configurable (quick/standard/enhanced/complete)
├── Cost: Higher ($0.75 - $42.00 per opportunity)
└── Output: Complete intelligence package
```

**Rationale**: Real-world workflow requires human-in-the-loop between mass screening and deep analysis.

---

## CURRENT STATE MAPPING

### Current Processors → Two Tools

#### TOOL 1: Opportunity Screening Tool (Replaces 2 processors)
```
Consolidates:
├── ai_lite_unified_processor.py (PLAN tab) - Quick screening
└── ai_heavy_light_analyzer.py (ANALYZE tab) - Enhanced screening

Current Function:
• PLAN: Fast compatibility scoring, initial filtering ($0.0004)
• ANALYZE: Multi-dimensional scoring, preliminary intelligence ($0.02-0.04)

New Function:
• Single tool with two internal modes: "fast" and "thorough"
• Processes 100s of opportunities efficiently
• Outputs shortlist for human review
```

#### HUMAN GATEWAY (Not a tool - manual process)
```
Activities Between Tools:
├── User reviews screening results
├── Manual filtering and prioritization
├── Web scraping for additional context
├── Internal research and analysis
├── Stakeholder discussions
├── Final selection (reduces to ~10 opportunities)
└── Triggers deep analysis for selected opportunities
```

#### TOOL 2: Deep Intelligence Tool (Replaces 6 processors)
```
Consolidates:
├── ai_heavy_deep_researcher.py (EXAMINE tab)
├── ai_heavy_researcher.py (APPROACH tab)
├── current_tier_processor.py ($0.75 tier)
├── standard_tier_processor.py ($7.50 tier)
├── enhanced_tier_processor.py ($22.00 tier)
└── complete_tier_processor.py ($42.00 tier)

Current Function:
• EXAMINE: Strategic intelligence, competitive analysis
• APPROACH: Implementation planning, resource allocation
• Tiers: Business packaging with increasing depth

New Function:
• Single tool with depth parameter (quick/standard/enhanced/complete)
• Comprehensive analysis for pre-selected opportunities
• Business-ready deliverables
```

---

## TOOL 1: OPPORTUNITY SCREENING TOOL

### Tool Specification

```python
# tools/opportunity-screening-tool/

class OpportunityScreeningTool:
    """
    12-Factor compliant mass screening tool

    Purpose: Efficiently screen large volumes of opportunities (100s → 10s)
    Replaces: ai_lite_unified_processor + ai_heavy_light_analyzer
    """

    metadata = ToolMetadata(
        name="opportunity-screening-tool",
        version="1.0.0",
        description="Mass screening of opportunities with fast AI-powered scoring",
        estimated_duration=5,  # seconds per opportunity
        estimated_cost=0.02,   # $0.02 average per opportunity
    )

class ScreeningMode(str, Enum):
    FAST = "fast"           # Quick screening, $0.0004 (PLAN equivalent)
    THOROUGH = "thorough"   # Enhanced screening, $0.02-0.04 (ANALYZE equivalent)

class ScreeningInput(BaseModel):
    """Input for screening tool"""
    opportunities: List[Dict[str, Any]]  # Can process batch of opportunities
    organization_profile: Dict[str, Any]
    screening_mode: ScreeningMode = ScreeningMode.THOROUGH
    minimum_threshold: float = 0.5  # Filter out opportunities below this score

class ScreeningOutput(BaseModel):
    """BAML-defined output schema"""

    # Per-opportunity results
    opportunity_scores: List[OpportunityScore]

    # Aggregate analysis
    total_screened: int
    passed_threshold: int
    top_opportunities: List[str]  # IDs of top-ranked opportunities

    # Recommendations
    recommended_for_deep_analysis: List[str]  # Top 10-20 opportunity IDs
    auto_reject_reasons: Dict[str, List[str]]  # Why opportunities were filtered out

    # Metadata
    processing_time: float
    total_cost: float
    screening_mode_used: str

class OpportunityScore(BaseModel):
    """Individual opportunity screening result"""
    opportunity_id: str
    opportunity_name: str

    # Core screening scores
    overall_score: float = Field(..., ge=0.0, le=1.0)
    strategic_fit_score: float = Field(..., ge=0.0, le=1.0)
    eligibility_score: float = Field(..., ge=0.0, le=1.0)
    feasibility_score: float = Field(..., ge=0.0, le=1.0)

    # Quick assessment
    proceed_to_deep_analysis: bool
    priority_rank: Optional[int]  # Rank among all screened opportunities

    # Brief rationale
    key_strengths: List[str] = Field(max_items=3)
    key_concerns: List[str] = Field(max_items=3)
    one_sentence_summary: str
```

### Usage Pattern

```python
# Screen 200 opportunities
screening_tool = OpportunityScreeningTool()

result = await screening_tool.execute(
    ScreeningInput(
        opportunities=all_opportunities,  # 200 opportunities
        organization_profile=org_profile,
        screening_mode=ScreeningMode.THOROUGH,
        minimum_threshold=0.6  # Only show opportunities scoring 60%+
    )
)

# Result:
# - 200 opportunities scored
# - 45 passed threshold (60%+)
# - Top 15 recommended for deep analysis
# - Cost: $4-8 total (200 × $0.02-0.04)
# - Time: 16 minutes (200 × 5 seconds)

print(f"Recommended for deep analysis: {result.recommended_for_deep_analysis}")
# Output: [opp_123, opp_456, opp_789, ...]  # Top 15 opportunity IDs
```

### 12-Factor Compliance

**Factor 4 (Structured Outputs)**: ✅
- BAML-defined schema with consistent structure
- Easy to consume, parse, and display

**Factor 10 (Small, Focused Agents)**: ✅
- **Single Responsibility**: Mass opportunity screening
- **Clear Boundary**: Doesn't do deep analysis, just screening
- **Right Size**: Fast, efficient, focused on filtering

**Factor 11 (Autonomous Operation)**: ✅
- Can process batches independently
- Handles retries and errors internally
- No external dependencies beyond OpenAI

**Factor 12 (Stateless)**: ✅
- Stateless execution
- Can process opportunities in parallel

---

## HUMAN GATEWAY WORKFLOW

### Between Tools: Manual Activities

```yaml
# Not a tool - this is human workflow
human_gateway_activities:

  1_review_screening_results:
    - Review top-ranked opportunities
    - Read one-sentence summaries
    - Check scores and key strengths/concerns
    - Flag interesting opportunities

  2_web_research:
    - Scrape websites of top opportunities
    - Research funders via web search
    - Gather additional context
    - Validate information from screening

  3_internal_analysis:
    - Discuss with team members
    - Check against organizational priorities
    - Review capacity and resources
    - Consider strategic fit beyond scores

  4_manual_filtering:
    - Eliminate opportunities that don't fit
    - Adjust priorities based on new information
    - Consider timing and deadlines
    - Narrow down to ~10 opportunities

  5_feedback_capture:
    - Note why opportunities were rejected
    - Capture preferences and patterns
    - Document decision rationale
    - Feed back into system for learning

  6_trigger_deep_analysis:
    - Select final 10 opportunities
    - Choose depth tier for each (quick/standard/enhanced/complete)
    - Trigger Tool 2 for comprehensive analysis
```

### Web Interface Support

```javascript
// Frontend workflow
async function screeningWorkflow() {
  // Step 1: Screen opportunities
  const screeningResults = await api.post('/api/screening/execute', {
    opportunities: allOpportunities,
    profile: orgProfile,
    mode: 'thorough'
  });

  // Display results in UI
  displayScreeningResults(screeningResults);

  // Step 2: User reviews and selects (HUMAN GATEWAY)
  // - User interface shows scored opportunities
  // - User can sort, filter, mark for deep analysis
  // - User can trigger web scraping for specific opportunities
  // - User can add notes and adjust priorities

  const selectedForDeepAnalysis = await waitForUserSelection();
  // User manually selects ~10 opportunities

  // Step 3: Trigger deep analysis for selected
  for (const opportunity of selectedForDeepAnalysis) {
    await api.post('/api/intelligence/execute', {
      opportunity: opportunity,
      profile: orgProfile,
      depth: opportunity.selected_depth // User chooses tier
    });
  }
}
```

---

## TOOL 2: DEEP INTELLIGENCE TOOL

### Tool Specification

```python
# tools/deep-intelligence-tool/

class DeepIntelligenceTool:
    """
    12-Factor compliant deep analysis tool

    Purpose: Comprehensive intelligence for pre-selected opportunities
    Replaces: ai_heavy_deep + ai_heavy_researcher + all 4 tier processors
    """

    metadata = ToolMetadata(
        name="deep-intelligence-tool",
        version="1.0.0",
        description="Comprehensive intelligence analysis with configurable depth",
        estimated_duration=600,  # 10 minutes for quick tier
        estimated_cost=0.75,     # Varies by depth: $0.75 - $42.00
    )

class AnalysisDepth(str, Enum):
    QUICK = "quick"           # $0.75, 5-10 min (CURRENT tier)
    STANDARD = "standard"     # $7.50, 15-20 min (STANDARD tier)
    ENHANCED = "enhanced"     # $22.00, 30-45 min (ENHANCED tier)
    COMPLETE = "complete"     # $42.00, 45-60 min (COMPLETE tier)

class DeepIntelligenceInput(BaseModel):
    """Input for deep intelligence tool"""
    opportunity: Dict[str, Any]
    organization_profile: Dict[str, Any]
    depth: AnalysisDepth = AnalysisDepth.QUICK

    # Optional context from screening phase
    screening_score: Optional[float]
    screening_summary: Optional[str]
    user_notes: Optional[str]

    # Optional focus areas
    focus_areas: List[str] = ["all"]  # Or specific: ["strategic", "financial", ...]

class DeepIntelligenceOutput(BaseModel):
    """BAML-defined comprehensive output schema"""

    # Strategic Analysis (All depths)
    strategic_fit_score: float = Field(..., ge=0.0, le=1.0)
    strategic_rationale: str
    strategic_recommendations: List[str]
    competitive_positioning: str

    # Financial Analysis (All depths)
    financial_viability_score: float = Field(..., ge=0.0, le=1.0)
    funding_strategy: str
    budget_recommendations: List[str]
    resource_requirements: Dict[str, Any]

    # Operational Analysis (All depths)
    operational_readiness_score: float = Field(..., ge=0.0, le=1.0)
    implementation_plan: Dict[str, Any]
    timeline: Dict[str, str]
    capacity_assessment: str

    # Risk Analysis (All depths)
    risk_assessment: Dict[str, float]
    risk_mitigation_strategies: List[str]
    success_probability: float

    # Decision Support (All depths)
    proceed_recommendation: bool
    confidence_level: float
    next_steps: List[str]

    # Enhanced features (standard+ depths)
    historical_intelligence: Optional[Dict[str, Any]]  # Standard+
    geographic_analysis: Optional[Dict[str, Any]]      # Standard+

    # Advanced features (enhanced+ depths)
    network_intelligence: Optional[Dict[str, Any]]     # Enhanced+
    relationship_mapping: Optional[Dict[str, Any]]     # Enhanced+
    decision_maker_profiles: Optional[List[Dict]]      # Enhanced+

    # Premium features (complete depth)
    policy_analysis: Optional[Dict[str, Any]]          # Complete
    market_positioning: Optional[Dict[str, Any]]       # Complete
    strategic_consulting_insights: Optional[str]       # Complete

    # Metadata
    depth_executed: str
    processing_time: float
    api_cost: float
    tokens_used: int
    report_url: Optional[str]  # Link to generated report
```

### Internal Implementation

```python
class DeepIntelligenceTool:

    async def execute(self, inputs: DeepIntelligenceInput) -> DeepIntelligenceOutput:
        """
        Execute deep analysis based on selected depth

        Internally handles what used to be:
        - EXAMINE stage (ai_heavy_deep_researcher)
        - APPROACH stage (ai_heavy_researcher)
        - Tier orchestration (current/standard/enhanced/complete)
        """

        # Route to appropriate depth handler
        if inputs.depth == AnalysisDepth.QUICK:
            return await self._quick_depth_analysis(inputs)
        elif inputs.depth == AnalysisDepth.STANDARD:
            return await self._standard_depth_analysis(inputs)
        elif inputs.depth == AnalysisDepth.ENHANCED:
            return await self._enhanced_depth_analysis(inputs)
        else:  # COMPLETE
            return await self._complete_depth_analysis(inputs)

    async def _quick_depth_analysis(self, inputs):
        """
        Quick depth: Core intelligence only

        Replaces:
        - Current tier processor ($0.75)
        - Partial EXAMINE + partial APPROACH stages

        Includes:
        - Strategic fit assessment
        - Financial viability analysis
        - Operational readiness check
        - Basic risk assessment
        - Proceed/no-go recommendation
        """
        # Single comprehensive AI call covering all core areas
        prompt = self._build_quick_analysis_prompt(inputs)
        result = await self._execute_ai_call(prompt, max_tokens=3000)
        return self._parse_to_output(result, inputs.depth)

    async def _standard_depth_analysis(self, inputs):
        """
        Standard depth: + Historical intelligence

        Replaces:
        - Standard tier processor ($7.50)
        - Full EXAMINE stage

        Adds:
        - Historical funding patterns
        - Geographic analysis
        - Temporal trends
        """
        # Core analysis + historical context
        core_analysis = await self._quick_depth_analysis(inputs)

        # Enhanced with historical intelligence
        historical_prompt = self._build_historical_analysis_prompt(inputs, core_analysis)
        historical_result = await self._execute_ai_call(historical_prompt, max_tokens=2000)

        # Merge results
        return self._merge_results(core_analysis, historical_result, inputs.depth)

    async def _enhanced_depth_analysis(self, inputs):
        """
        Enhanced depth: + Network & relationship intelligence

        Replaces:
        - Enhanced tier processor ($22.00)
        - Full EXAMINE + partial APPROACH

        Adds:
        - Network intelligence
        - Relationship mapping
        - Decision maker profiling
        """
        # Standard analysis as base
        standard_analysis = await self._standard_depth_analysis(inputs)

        # Add network intelligence (can run in parallel with standard)
        network_task = self._analyze_network_intelligence(inputs)
        relationship_task = self._analyze_relationships(inputs)

        network_result, relationship_result = await asyncio.gather(
            network_task, relationship_task
        )

        # Merge all results
        return self._merge_enhanced_results(
            standard_analysis, network_result, relationship_result, inputs.depth
        )

    async def _complete_depth_analysis(self, inputs):
        """
        Complete depth: Masters thesis level

        Replaces:
        - Complete tier processor ($42.00)
        - Full APPROACH stage

        Adds:
        - Policy analysis
        - Market positioning
        - Strategic consulting insights
        - Premium reporting
        """
        # Enhanced analysis as base
        enhanced_analysis = await self._enhanced_depth_analysis(inputs)

        # Add premium features
        policy_task = self._analyze_policy_context(inputs)
        market_task = self._analyze_market_positioning(inputs)
        strategic_task = self._generate_strategic_insights(inputs, enhanced_analysis)

        policy_result, market_result, strategic_result = await asyncio.gather(
            policy_task, market_task, strategic_task
        )

        # Generate premium report
        report_url = await self._generate_premium_report(
            enhanced_analysis, policy_result, market_result, strategic_result
        )

        # Merge all results
        return self._merge_complete_results(
            enhanced_analysis,
            policy_result,
            market_result,
            strategic_result,
            report_url,
            inputs.depth
        )
```

### Usage Pattern

```python
# After user selects 10 opportunities from screening results

deep_intelligence_tool = DeepIntelligenceTool()

# Analyze selected opportunities with chosen depth
for opportunity in selected_opportunities:
    result = await deep_intelligence_tool.execute(
        DeepIntelligenceInput(
            opportunity=opportunity,
            organization_profile=org_profile,
            depth=AnalysisDepth.STANDARD,  # User chose $7.50 tier
            screening_score=opportunity.screening_score,
            user_notes=opportunity.user_notes
        )
    )

    # Display comprehensive intelligence
    display_intelligence_report(result)

# Cost: 10 opportunities × $7.50 = $75 total
# Time: 10 opportunities × 15-20 min = 2.5-3.3 hours
```

### 12-Factor Compliance

**Factor 4 (Structured Outputs)**: ✅
- Comprehensive BAML schema
- Consistent output across all depths
- Easy to consume and display

**Factor 10 (Small, Focused Agents)**: ✅
- **Single Responsibility**: Deep intelligence analysis
- **Clear Boundary**: Doesn't do screening, only deep analysis
- **Right Size**: Comprehensive but focused on pre-selected opportunities

**Factor 11 (Autonomous Operation)**: ✅
- Self-contained analysis
- Handles own retries and errors
- Manages internal stage orchestration

**Factor 12 (Stateless)**: ✅
- Stateless execution
- All context in inputs
- Reproducible results

---

## WORKFLOW INTEGRATION

### Complete Two-Tool Workflow

```yaml
# workflows/opportunity_pipeline.yaml

workflow: opportunity_pipeline
description: "Complete pipeline: screening → human review → deep intelligence"

inputs:
  all_opportunities: array[object]
  organization_profile: object
  screening_mode: enum[fast, thorough]
  minimum_threshold: float

stages:

  # STAGE 1: Mass Screening
  - name: screen_opportunities
    tool: opportunity-screening-tool
    inputs:
      opportunities: "{{ all_opportunities }}"
      organization_profile: "{{ organization_profile }}"
      screening_mode: "{{ screening_mode }}"
      minimum_threshold: "{{ minimum_threshold }}"
    outputs:
      screening_results: screening

  # STAGE 2: Human Gateway (Web Interface)
  - name: await_human_selection
    type: human_input
    interface: web_ui
    display:
      component: "screening_review_interface"
      data: "{{ screening_results }}"
    capabilities:
      - review_scores
      - web_scraping
      - manual_filtering
      - note_taking
      - priority_adjustment
    outputs:
      selected_opportunities: selections
      depth_selections: depths

  # STAGE 3: Deep Intelligence Analysis (for selected opportunities)
  - name: deep_intelligence_analysis
    tool: deep-intelligence-tool
    for_each: "{{ selected_opportunities }}"
    inputs:
      opportunity: "{{ item }}"
      organization_profile: "{{ organization_profile }}"
      depth: "{{ depths[item.id] }}"  # User-selected depth per opportunity
      screening_score: "{{ item.screening_score }}"
      user_notes: "{{ item.user_notes }}"
    outputs:
      intelligence_reports: reports

  # STAGE 4: Generate Final Package
  - name: generate_final_package
    tool: report-generator-tool
    inputs:
      intelligence_reports: "{{ intelligence_reports }}"
      output_format: "executive_package"
    outputs:
      final_package: package
```

---

## ARCHITECTURE BENEFITS

### Why Two Tools is Optimal

#### 1. **Matches Real-World Usage** ⭐⭐⭐⭐⭐
```
Reality: Users don't deep-analyze 200 opportunities
Process: Screen many → Select few → Analyze deeply
Two tools: Perfectly matches this workflow
```

#### 2. **Cost Efficiency** ⭐⭐⭐⭐⭐
```
Screening: 200 opportunities × $0.02 = $4
Deep Analysis: 10 opportunities × $7.50 = $75
Total: $79

vs. Deep analyzing 200: 200 × $7.50 = $1,500 ❌
Savings: 94% cost reduction
```

#### 3. **Human-in-the-Loop Gateway** ⭐⭐⭐⭐⭐
```
Natural breakpoint: Between screening and deep analysis
Activities: Web scraping, research, team discussion
Flexibility: Users control what gets deep analysis
Quality: Human judgment improves selection
```

#### 4. **12-Factor Compliance** ⭐⭐⭐⭐⭐
```
Each tool: Clear, focused responsibility
Tool 1: Mass screening
Tool 2: Deep intelligence
No overlap, clear boundaries
```

#### 5. **Performance Optimization** ⭐⭐⭐⭐⭐
```
Tool 1: Fast, parallelizable, batch-friendly
Tool 2: Thorough, comprehensive, quality-focused
Each optimized for its purpose
```

#### 6. **Flexibility** ⭐⭐⭐⭐⭐
```
Tool 1: Can adjust screening sensitivity
Tool 2: Can choose depth per opportunity
Mix and match: Different depths for different opportunities
```

#### 7. **Pricing Clarity** ⭐⭐⭐⭐⭐
```
Tool 1: Low cost per opportunity (pennies)
Tool 2: Tiered pricing ($0.75 - $42.00)
Clear cost structure for users
```

---

## MIGRATION STRATEGY

### Phase 1: Tool 1 - Opportunity Screening (Week 2)
```
Build: opportunity-screening-tool
├── Consolidate ai_lite_unified + ai_heavy_light
├── Implement fast and thorough modes
├── BAML schema for screening output
├── Batch processing capability
└── Test with 200 opportunity dataset

Deprecate:
├── ai_lite_unified_processor.py
└── ai_heavy_light_analyzer.py
```

### Phase 2: Tool 2 - Deep Intelligence (Week 3)
```
Build: deep-intelligence-tool
├── Consolidate ai_heavy_deep + ai_heavy_researcher + 4 tier processors
├── Implement all 4 depth levels (quick/standard/enhanced/complete)
├── BAML schema for comprehensive output
├── Internal stage orchestration
└── Test each depth tier

Deprecate:
├── ai_heavy_deep_researcher.py
├── ai_heavy_researcher.py
├── current_tier_processor.py
├── standard_tier_processor.py
├── enhanced_tier_processor.py
└── complete_tier_processor.py
```

### Phase 3: Workflow Integration (Week 4-5)
```
Build: opportunity_pipeline workflow
├── Integrate both tools
├── Implement human gateway interface
├── Web scraping integration
├── Note-taking and selection UI
└── End-to-end testing

Result:
• Complete pipeline operational
• All 8 processors deprecated
• Human-in-loop workflow functional
```

---

## SUMMARY TABLE

| Aspect | Tool 1: Screening | Tool 2: Deep Intelligence |
|--------|------------------|--------------------------|
| **Purpose** | Narrow 100s → 10s | Comprehensive analysis of 10s |
| **Replaces** | 2 processors (PLAN, ANALYZE) | 6 processors (EXAMINE, APPROACH, 4 tiers) |
| **Speed** | ~5 seconds/opportunity | 5-60 minutes/opportunity |
| **Cost** | $0.0004 - $0.04/opportunity | $0.75 - $42.00/opportunity |
| **Modes** | fast, thorough | quick, standard, enhanced, complete |
| **Output** | Scored shortlist | Comprehensive intelligence |
| **Use Case** | Mass filtering | Selected deep-dive |
| **Parallelization** | Yes, highly parallel | Less critical (small batch) |
| **12-Factor** | ✅ Small, focused | ✅ Small, focused |

---

## FINAL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TWO-TOOL ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────────────────────────────────┐             │
│  │  TOOL 1: Opportunity Screening Tool                │             │
│  │  • Input: 100s of opportunities                    │             │
│  │  • Output: Scored shortlist (~45 pass threshold)   │             │
│  │  • Cost: $4-8 for 200 opportunities                │             │
│  │  • Time: 16 minutes for 200 opportunities          │             │
│  └────────────────────────────────────────────────────┘             │
│                          ↓                                          │
│  ┌────────────────────────────────────────────────────┐             │
│  │         HUMAN GATEWAY (Web Interface)              │             │
│  │  • Review screening results                        │             │
│  │  • Web scraping & research                         │             │
│  │  • Manual filtering & prioritization               │             │
│  │  • Select ~10 opportunities for deep analysis      │             │
│  │  • Choose depth tier for each                      │             │
│  └────────────────────────────────────────────────────┘             │
│                          ↓                                          │
│  ┌────────────────────────────────────────────────────┐             │
│  │  TOOL 2: Deep Intelligence Tool                    │             │
│  │  • Input: Selected 10 opportunities                │             │
│  │  • Depth: User-chosen per opportunity              │             │
│  │  • Output: Comprehensive intelligence package      │             │
│  │  • Cost: $0.75-$42 per opportunity × 10            │             │
│  │  • Time: 5-60 minutes per opportunity              │             │
│  └────────────────────────────────────────────────────┘             │
│                                                                     │
│  Result: 8 processors → 2 tools + human gateway                    │
└─────────────────────────────────────────────────────────────────────┘
```

**Decision Approved**: ✅ Two unified tools with human-in-the-loop gateway