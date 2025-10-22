# Tool 20: Multi-Dimensional Scorer Tool

**Version**: 1.0.0
**Status**: Operational
**Category**: Scoring
**Cost**: $0.00 per score (algorithmic, no AI calls)
**Replaces**: `discovery_scorer.py`, `success_scorer.py`, `composite_scorer_v2.py`

## Overview

Unified multi-dimensional scoring tool supporting both **stage-based** scoring (5 workflow stages) and **track-based** scoring (5 opportunity tracks including foundation-specific 990-PF scoring).

## Features

- **5 Workflow Stages**: DISCOVER → PLAN → ANALYZE → EXAMINE → APPROACH
- **5 Opportunity Tracks**: NONPROFIT, FEDERAL, STATE, COMMERCIAL, **FOUNDATION** (990-PF)
- **Dimensional Scoring**: 5 weighted dimensions per stage/track
- **Boost Factors**: Financial, network, historical, risk assessment enhancements
- **Confidence Calculation**: Data quality-based confidence scoring
- **12-Factor Compliant**: Stateless, structured outputs, single responsibility

## Architecture

### Stage-Based Scoring (Default)

Used for NONPROFIT, FEDERAL, STATE, COMMERCIAL tracks:

```
DISCOVER → PLAN → ANALYZE → EXAMINE → APPROACH
    ↓        ↓        ↓         ↓          ↓
  5 dims   5 dims   5 dims    5 dims     5 dims
```

Each stage has unique dimensional priorities optimized for funnel progression.

### Track-Based Scoring (Foundation Mode)

Used for FOUNDATION track (990-PF opportunities):

```
FOUNDATION Track
      ↓
 8 components → 5 dimensions
      ↓
  Single pass comprehensive scoring
```

See [FOUNDATION_MODE.md](./FOUNDATION_MODE.md) for detailed foundation scoring documentation.

## Usage

### Basic Scoring

```python
from tools.multi_dimensional_scorer_tool.app.scorer_tool import score_opportunity

# Stage-based scoring (default)
result = await score_opportunity(
    opportunity_data={...},
    organization_profile={...},
    workflow_stage="discover",  # or plan, analyze, examine, approach
    track_type="nonprofit"  # or federal, state, commercial
)

# Foundation mode (track-based)
result = await score_opportunity(
    opportunity_data=foundation_990pf_data,
    organization_profile=org_profile,
    workflow_stage="discover",  # Required but not used
    track_type="foundation"  # Activates foundation mode
)
```

### Tool Instance

```python
from tools.multi_dimensional_scorer_tool.app.scorer_tool import MultiDimensionalScorerTool
from tools.multi_dimensional_scorer_tool.app.scorer_models import ScoringInput, WorkflowStage, TrackType

tool = MultiDimensionalScorerTool(config={
    "stage_weights": {...},  # Optional custom weights
    "boost_factors": {...}   # Optional custom boosts
})

scoring_input = ScoringInput(
    opportunity_data={...},
    organization_profile={...},
    workflow_stage=WorkflowStage.DISCOVER,
    track_type=TrackType.NONPROFIT
)

result = await tool.execute(scoring_input=scoring_input)
```

## Output Structure

```python
MultiDimensionalScore(
    overall_score=0.75,  # 0.0-1.0 weighted sum
    confidence=0.85,  # 0.0-1.0 data quality
    dimensional_scores=[
        DimensionalScore(
            dimension_name="mission_alignment",
            raw_score=0.82,
            weight=0.30,
            weighted_score=0.246,
            boost_factor=1.0,
            data_quality=0.9,
            notes="..."
        ),
        # ... 4 more dimensions
    ],
    stage="discover",
    track_type="nonprofit",
    boost_factors_applied=["financial_data"],
    metadata=ScoringMetadata(...),
    proceed_recommendation=True,
    key_strengths=["Mission alignment: 82%", "..."],
    key_concerns=["Timing: 45%"],
    recommended_actions=["Proceed to next stage", "..."]
)
```

## Dimensional Weights

### DISCOVER Stage
- **mission_alignment**: 0.30
- **geographic_fit**: 0.25
- **financial_match**: 0.20
- **eligibility**: 0.15
- **timing**: 0.10

### PLAN Stage
- **success_probability**: 0.30
- **organizational_capacity**: 0.25
- **financial_viability**: 0.20
- **network_leverage**: 0.15
- **compliance**: 0.10

### ANALYZE Stage
- **competitive_position**: 0.30
- **strategic_alignment**: 0.25
- **risk_profile**: 0.20
- **implementation_feasibility**: 0.15
- **roi_potential**: 0.10

### EXAMINE Stage
- **deep_intelligence_quality**: 0.30
- **relationship_pathways**: 0.25
- **strategic_fit**: 0.20
- **partnership_potential**: 0.15
- **innovation_opportunity**: 0.10

### APPROACH Stage
- **overall_viability**: 0.30
- **success_probability**: 0.25
- **strategic_value**: 0.20
- **resource_requirements**: 0.15
- **timeline_feasibility**: 0.10

### FOUNDATION Track (990-PF)
- **mission_alignment**: 0.30 (NTEE alignment)
- **geographic_fit**: 0.20 (State matching)
- **financial_match**: 0.28 (Capacity + Grant size + Application policy)
- **strategic_alignment**: 0.12 (Recipient coherence)
- **timing**: 0.10 (Filing recency + Foundation type)

## Boost Factors

Optional enhancements based on available enriched data:

- **financial_data**: +10% to financial dimensions
- **network_data**: +15% to network/relationship dimensions
- **historical_data**: +12% to success probability
- **risk_assessment**: +8% to viability scores

## Confidence Calculation

Confidence in the overall score (0.0-1.0) based on:

1. **Data Quality Average**: Mean data_quality across dimensions
2. **Enhancement Bonus**: +5% per available enhancement (max +20%)

```python
confidence = data_quality_avg + (enhancement_count * 0.05)
```

## Performance

- **Speed**: < 10ms per score
- **Cost**: $0.00 (no AI calls)
- **Memory**: < 512MB per instance
- **Concurrency**: Async-ready for parallel execution

## 12-Factor Compliance

- ✅ **Factor 4**: Structured outputs (MultiDimensionalScore dataclass)
- ✅ **Factor 6**: Stateless execution (no persistent state)
- ✅ **Factor 10**: Single responsibility (scoring only)
- ✅ **Factor 12**: API-first design (function interface)

See [12factors.toml](./12factors.toml) for complete compliance details.

## Files

- **[scorer_tool.py](./app/scorer_tool.py)**: Main tool implementation
- **[scorer_models.py](./app/scorer_models.py)**: Data models and enums
- **[stage_scorers.py](./app/stage_scorers.py)**: Stage-specific scoring logic
- **[foundation_scorer.py](./app/foundation_scorer.py)**: Foundation-specific (990-PF) scoring
- **[12factors.toml](./12factors.toml)**: Tool configuration and compliance
- **[FOUNDATION_MODE.md](./FOUNDATION_MODE.md)**: Foundation scoring documentation

## Integration

### Workflow Engine

```yaml
# opportunity_screening.yaml
steps:
  - name: "score_opportunities"
    tool: "multi-dimensional-scorer-tool"
    inputs:
      scoring_input:
        opportunity_data: "${context.opportunity}"
        organization_profile: "${context.profile}"
        workflow_stage: "discover"
        track_type: "nonprofit"
```

### REST API

```python
# POST /api/tools/multi-dimensional-scorer-tool/execute
{
  "scoring_input": {
    "opportunity_data": {...},
    "organization_profile": {...},
    "workflow_stage": "discover",
    "track_type": "nonprofit"
  }
}
```

## See Also

- **Foundation Mode**: [FOUNDATION_MODE.md](./FOUNDATION_MODE.md) - 990-PF scoring documentation
- **Tool Registry**: [src/core/tool_registry.py](../../src/core/tool_registry.py)
- **12-Factor Framework**: [src/core/tool_framework/](../../src/core/tool_framework/)
- **System Architecture**: [CLAUDE.md](../../CLAUDE.md)
