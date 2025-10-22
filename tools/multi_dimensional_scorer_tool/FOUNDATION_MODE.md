# Foundation Mode - 990-PF Composite Scoring

**Tool 20 Extension**: Foundation-specific scoring for private foundation (990-PF) opportunities
**Migration Date**: 2025-10-21
**Replaces**: `src/scoring/composite_scorer_v2.py`
**Track Type**: `TrackType.FOUNDATION`

## Overview

Foundation Mode integrates the 8-component Composite Scorer V2 functionality into Tool 20's unified scoring architecture. This specialized track provides sophisticated 990-PF foundation-nonprofit matching analysis while maintaining Tool 20's 12-factor compliance and dimensional scoring framework.

## Architecture Design

### **Track-Based vs Stage-Based Scoring**

Tool 20 supports two scoring paradigms:

1. **Stage-Based Scoring** (Default)
   - Used for: NONPROFIT, FEDERAL, STATE, COMMERCIAL tracks
   - 5 workflow stages: DISCOVER → PLAN → ANALYZE → EXAMINE → APPROACH
   - Each stage has unique dimensional priorities
   - Progressive refinement through funnel

2. **Track-Based Scoring** (Foundation Mode)
   - Used for: FOUNDATION track (990-PF opportunities)
   - Single comprehensive scoring pass
   - 8-component composite analysis
   - Specialized for foundation-nonprofit alignment

### **8 Components → 5 Dimensions Mapping**

Foundation Mode maps Composite Scorer V2's 8 components to Tool 20's 5-dimensional framework:

#### **Dimension 1: Mission Alignment (30%)**
- **Component**: NTEE Alignment (30%)
- **Scorer**: `NTEEScorer` (Phase 2 Week 3)
- **Method**: Two-part scoring (major code + leaf code)
- **Cap**: 30% maximum contribution (prevents over-weighting)
- **Data Sources**: BMF, Schedule I recipients, website scraping

#### **Dimension 2: Geographic Fit (20%)**
- **Component**: Geographic Match (20%)
- **Method**: State-level matching with national fallback
- **Scoring**:
  - 100% - Exact state match
  - 75% - Adjacent state (future enhancement)
  - 50% - National focus (no restrictions)
  - 0% - Geographic mismatch
- **Data Sources**: 990-PF geographic focus states, organization profile

#### **Dimension 3: Financial Match (28%)**
- **Components** (3 combined):
  1. **Financial Capacity** (10/28): Foundation asset size analysis
  2. **Grant Size Fit** (10/28): Grant-to-revenue ratio using `GrantSizeScorer` (Phase 2 Week 4-5)
  3. **Application Policy** (8/28): Accepts applications preference
- **Method**: Weighted average of 3 sub-components
- **Data Sources**: 990-PF financial data, Schedule I grant amounts

#### **Dimension 4: Strategic Alignment (12%)**
- **Component**: Recipient Coherence (12%)
- **Scorer**: `ScheduleIVotingSystem` (Phase 2 Week 4-5)
- **Method**: Schedule I recipient voting with coherence analysis
- **Boost**: Coherent foundations get 0.0-0.15 boost factor
- **Data Sources**: Schedule I grantees, EIN resolution

#### **Dimension 5: Timing (10%)**
- **Components** (2 combined):
  1. **Filing Recency** (5/10): Time-decay analysis using `TimeDecayCalculator` (Phase 1)
  2. **Foundation Type** (5/10): Operating vs non-operating preference
- **Method**: Time-based penalty/boost for data staleness
- **Data Sources**: 990-PF filing metadata

## Usage

### **Basic Foundation Scoring**

```python
from tools.multi_dimensional_scorer_tool.app.scorer_tool import MultiDimensionalScorerTool, score_opportunity
from tools.multi_dimensional_scorer_tool.app.scorer_models import TrackType, WorkflowStage

# Method 1: Direct tool usage
tool = MultiDimensionalScorerTool()

scoring_input = ScoringInput(
    opportunity_data={
        'foundation_ein': '541026365',
        'foundation_name': 'Example Foundation',
        'ntee_codes': ['B25', 'E20'],
        'ntee_code_sources': {'B25': 'bmf', 'E20': 'schedule_i'},
        'geographic_focus_states': ['VA', 'MD', 'DC'],
        'total_assets': 5000000,
        'typical_grant_amount': 25000,
        'accepts_applications': True,
        'most_recent_filing_year': 2024,
        'schedule_i_grantees': [...]  # List of ScheduleIGrantee objects
    },
    organization_profile={
        'ein': '123456789',
        'ntee_codes': ['B25'],
        'state': 'VA',
        'revenue': 500000
    },
    workflow_stage=WorkflowStage.DISCOVER,  # Required but not used for foundation track
    track_type=TrackType.FOUNDATION  # KEY: Activates foundation mode
)

result = await tool.execute(scoring_input=scoring_input)

# Method 2: Convenience function
result = await score_opportunity(
    opportunity_data=foundation_data,
    organization_profile=org_profile,
    workflow_stage="discover",
    track_type="foundation"  # Foundation mode
)
```

### **Foundation-Specific Data Requirements**

**Opportunity Data (Foundation 990-PF)**:
```python
{
    # Core identification
    'foundation_ein': str,
    'foundation_name': str,

    # NTEE analysis
    'ntee_codes': List[str],  # ['B25', 'E20']
    'ntee_code_sources': Dict[str, str],  # {'B25': 'bmf'}
    'ntee_code_dates': Optional[Dict[str, datetime]],

    # Geographic data
    'geographic_focus_states': List[str],  # ['VA', 'MD', 'DC']

    # Financial data
    'total_assets': float,
    'grants_paid_total': float,
    'typical_grant_amount': float,
    'grant_amount_min': Optional[float],
    'grant_amount_max': Optional[float],

    # Application policy
    'accepts_applications': Optional[bool],

    # Schedule I data (critical for coherence)
    'schedule_i_grantees': List[ScheduleIGrantee],

    # Filing metadata
    'most_recent_filing_year': int
}
```

**Organization Profile**:
```python
{
    'ein': str,
    'ntee_codes': List[str],
    'state': str,
    'revenue': float
}
```

## Output Structure

Foundation Mode returns a standard `MultiDimensionalScore` with 5 dimensional scores:

```python
MultiDimensionalScore(
    overall_score=0.78,  # 0.0-1.0 (or 78/100)
    confidence=0.85,
    dimensional_scores=[
        DimensionalScore(
            dimension_name="mission_alignment",
            raw_score=0.82,
            weight=0.30,
            weighted_score=0.246,
            boost_factor=1.0,
            data_quality=0.9,
            notes="NTEE exact match: B25 (Education)"
        ),
        DimensionalScore(
            dimension_name="geographic_fit",
            raw_score=1.0,
            weight=0.20,
            weighted_score=0.20,
            boost_factor=1.0,
            data_quality=1.0,
            notes="Exact state match: VA"
        ),
        DimensionalScore(
            dimension_name="financial_match",
            raw_score=0.75,
            weight=0.28,
            weighted_score=0.21,
            boost_factor=1.0,
            data_quality=0.8,
            notes="Capacity: 0.85, Grant size: 0.78, Application: 1.00. Optimal grant-to-revenue ratio (5%)"
        ),
        DimensionalScore(
            dimension_name="strategic_alignment",
            raw_score=0.68,
            weight=0.12,
            weighted_score=0.0816,
            boost_factor=1.12,  # Coherence boost applied
            data_quality=0.9,
            notes="Coherence: 0.68 | Entropy: 0.42 | Recipients: 25 | Coherent: True | Top NTEE: B25, E20, P20"
        ),
        DimensionalScore(
            dimension_name="timing",
            raw_score=0.95,
            weight=0.10,
            weighted_score=0.095,
            boost_factor=0.95,  # Time-decay penalty
            data_quality=0.8,
            notes="Filing year: 2024, Decay: 0.95, Type score: 0.75"
        )
    ],
    stage="discover",  # Informational only
    track_type="foundation",
    boost_factors_applied=["coherence_boost", "time_decay"],
    metadata=ScoringMetadata(...)
)
```

## Decision Thresholds

Foundation Mode uses Composite Scorer V2's three-tier decision system:

- **PASS**: overall_score ≥ 0.58 (58/100)
- **ABSTAIN**: 0.45 ≤ overall_score < 0.58 (45-58/100) - Manual review queue
- **FAIL**: overall_score < 0.45 (45/100) - Clear mismatch

### **Abstain Triggers** (Force ABSTAIN regardless of score):
- Missing NTEE codes
- Very low NTEE alignment (< 20%)
- Geographic mismatch (foundation focuses on other states)
- Borderline scores (45-58 range)

## Performance Characteristics

- **Cost**: $0.00 per score (no AI calls - algorithmic only)
- **Speed**: < 10ms per foundation-nonprofit pair
- **Accuracy**: 70-90% improvement vs V1 (Phase 3 Week 6 baseline)
- **Confidence**: 0.5-1.0 based on data quality and recency

## Dependencies

Foundation Mode reuses existing Phase 1-3 scoring components:

```python
from src.scoring.ntee_scorer import NTEEScorer
from src.scoring.schedule_i_voting import ScheduleIVotingSystem
from src.scoring.grant_size_scoring import GrantSizeScorer
from src.scoring.time_decay_utils import TimeDecayCalculator
```

These components remain in `src/scoring/` as shared services (not migrated to tools/).

## Migration from Composite Scorer V2

### **Before (Composite Scorer V2)**:
```python
from src.scoring.composite_scorer_v2 import CompositeScoreV2, FoundationOpportunityData

scorer = CompositeScoreV2()
result = scorer.score_foundation_match(
    profile=org_profile,
    foundation=foundation_data
)

# Result: CompositeScoreResult
print(result.final_score)  # 0-100 scale
print(result.recommendation)  # PASS/ABSTAIN/FAIL
```

### **After (Tool 20 Foundation Mode)**:
```python
from tools.multi_dimensional_scorer_tool.app.scorer_tool import score_opportunity

result = await score_opportunity(
    opportunity_data=foundation_data,
    organization_profile=org_profile,
    workflow_stage="discover",
    track_type="foundation"
)

# Result: MultiDimensionalScore
print(result.overall_score)  # 0.0-1.0 scale (multiply by 100 for 0-100)
print(result.proceed_recommendation)  # True/False
```

### **Key Differences**:
1. **Async**: Tool 20 uses async execution
2. **Score Scale**: 0.0-1.0 (Tool 20) vs 0-100 (Composite V2)
3. **Output Structure**: MultiDimensionalScore vs CompositeScoreResult
4. **Track Selection**: Automatic via `track_type=TrackType.FOUNDATION`
5. **12-Factor Compliance**: Tool 20 is fully compliant

## Backward Compatibility

Composite Scorer V2 remains available in `src/scoring/` during migration period:

```python
# Legacy code continues to work
from src.scoring.composite_scorer_v2 import CompositeScoreV2
scorer = CompositeScoreV2()
result = scorer.score_foundation_match(profile, foundation)
```

**Deprecation Timeline**:
- Week 9 (Current): Both systems operational
- Week 10: Composite Scorer V2 marked deprecated
- Week 11: Migration complete, Composite Scorer V2 removed

## Testing Foundation Mode

```python
import pytest
from tools.multi_dimensional_scorer_tool.app.scorer_tool import MultiDimensionalScorerTool
from tools.multi_dimensional_scorer_tool.app.scorer_models import ScoringInput, WorkflowStage, TrackType

@pytest.mark.asyncio
async def test_foundation_mode_basic():
    """Test basic foundation scoring"""
    tool = MultiDimensionalScorerTool()

    scoring_input = ScoringInput(
        opportunity_data={
            'foundation_ein': '541026365',
            'foundation_name': 'Test Foundation',
            'ntee_codes': ['B25'],
            'ntee_code_sources': {'B25': 'bmf'},
            'geographic_focus_states': ['VA'],
            'total_assets': 5000000,
            'typical_grant_amount': 25000,
            'accepts_applications': True,
            'most_recent_filing_year': 2024,
            'schedule_i_grantees': []
        },
        organization_profile={
            'ein': '123456789',
            'ntee_codes': ['B25'],
            'state': 'VA',
            'revenue': 500000
        },
        workflow_stage=WorkflowStage.DISCOVER,
        track_type=TrackType.FOUNDATION
    )

    result = await tool.execute(scoring_input=scoring_input)

    assert result.track_type == "foundation"
    assert len(result.dimensional_scores) == 5
    assert 0.0 <= result.overall_score <= 1.0
    assert 0.0 <= result.confidence <= 1.0

@pytest.mark.asyncio
async def test_foundation_mode_dimensions():
    """Test foundation mode returns correct dimensions"""
    tool = MultiDimensionalScorerTool()

    scoring_input = ScoringInput(
        opportunity_data=foundation_data,
        organization_profile=org_profile,
        workflow_stage=WorkflowStage.DISCOVER,
        track_type=TrackType.FOUNDATION
    )

    result = await tool.execute(scoring_input=scoring_input)

    dimension_names = [ds.dimension_name for ds in result.dimensional_scores]
    assert "mission_alignment" in dimension_names
    assert "geographic_fit" in dimension_names
    assert "financial_match" in dimension_names
    assert "strategic_alignment" in dimension_names
    assert "timing" in dimension_names
```

## See Also

- [12factors.toml](./12factors.toml) - Tool configuration with foundation track details
- [foundation_scorer.py](./app/foundation_scorer.py) - Foundation scorer implementation
- [scorer_models.py](./app/scorer_models.py) - Data models with FOUNDATION track type
- [Composite Scorer V2](../../src/scoring/composite_scorer_v2.py) - Legacy implementation (deprecated)
- [CLAUDE.md](../../CLAUDE.md) - System architecture documentation
