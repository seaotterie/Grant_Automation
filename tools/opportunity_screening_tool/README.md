# Opportunity Screening Tool

**12-Factor Compliant Grant Opportunity Screening Tool**

## Purpose

Mass screening of grant opportunities to identify high-potential matches for deep analysis.

**Pipeline Position**: Stage 1 of Two-Tool Architecture
- **Input**: 100s of opportunities from discovery tools
- **Output**: Shortlist of ~10 high-scoring opportunities
- **Next Stage**: Human gateway → Deep Intelligence Tool

## Modes

### Fast Mode
- **Cost**: $0.0004 per opportunity (~$0.08 for 200)
- **Time**: ~2 seconds per opportunity
- **Analysis**: Basic strategic fit and eligibility
- **Replaces**: PLAN tab processor
- **Dimensions**: Strategic Fit, Eligibility, Timing

### Thorough Mode
- **Cost**: $0.02 per opportunity (~$4.00 for 200)
- **Time**: ~5 seconds per opportunity
- **Analysis**: Comprehensive multi-dimensional analysis
- **Replaces**: ANALYZE tab processor
- **Dimensions**: Strategic Fit, Eligibility, Timing, Financial, Competition

## Usage

### Python API

```python
from tools.opportunity_screening_tool.app import screen_opportunities
from tools.opportunity_screening_tool.app.screening_models import (
    Opportunity,
    OrganizationProfile
)

# Define organization
organization = OrganizationProfile(
    ein="12-3456789",
    name="Example Nonprofit",
    mission="Improving education access",
    ntee_codes=["B25"],
    geographic_focus=["Virginia", "Maryland"],
    program_areas=["Education", "Youth Development"]
)

# Define opportunities
opportunities = [
    Opportunity(
        opportunity_id="opp-001",
        title="Education Innovation Grant",
        funder="Smith Foundation",
        funder_type="foundation",
        description="Supporting innovative education programs...",
        amount_min=50000,
        amount_max=150000,
        focus_areas=["Education", "Innovation"]
    ),
    # ... more opportunities
]

# Screen opportunities
result = await screen_opportunities(
    opportunities=opportunities,
    organization=organization,
    mode="fast",  # or "thorough"
    threshold=0.55,
    max_recommendations=10
)

# Access results
if result.is_success():
    output = result.data
    print(f"Screened: {output.total_screened}")
    print(f"Passed threshold: {output.passed_threshold}")
    print(f"Recommended: {output.recommended_for_deep_analysis}")

    for score in output.opportunity_scores:
        if score.proceed_to_deep_analysis:
            print(f"\n{score.opportunity_title}")
            print(f"Overall Score: {score.overall_score:.2f}")
            print(f"Summary: {score.one_sentence_summary}")
```

### Using BaseTool Interface

```python
from tools.opportunity_screening_tool.app.screening_tool import OpportunityScreeningTool
from tools.opportunity_screening_tool.app.screening_models import ScreeningInput, ScreeningMode

tool = OpportunityScreeningTool(config={
    "openai_api_key": "sk-...",
    "default_mode": "fast",
    "default_threshold": 0.55
})

screening_input = ScreeningInput(
    opportunities=opportunities,
    organization_profile=organization,
    screening_mode=ScreeningMode.FAST,
    minimum_threshold=0.55,
    max_recommendations=10
)

result = await tool.execute(screening_input=screening_input)
```

## Output Structure

```python
@dataclass
class ScreeningOutput:
    # Summary Statistics
    total_screened: int
    passed_threshold: int
    recommended_for_deep_analysis: List[str]  # opportunity_ids

    # Detailed Scores
    opportunity_scores: List[OpportunityScore]

    # Metadata
    screening_mode: str
    threshold_used: float
    processing_time_seconds: float
    total_cost_usd: float
    high_confidence_count: int

@dataclass
class OpportunityScore:
    opportunity_id: str
    opportunity_title: str

    # Overall Assessment
    overall_score: float  # 0.0 - 1.0
    proceed_to_deep_analysis: bool
    confidence_level: str  # "high", "medium", "low"

    # Dimensional Scores
    strategic_fit_score: float
    eligibility_score: float
    timing_score: float
    financial_score: float  # Thorough mode only
    competition_score: float  # Thorough mode only

    # Analysis
    one_sentence_summary: str
    key_strengths: List[str]
    key_concerns: List[str]
    recommended_actions: List[str]
```

## Scoring Logic

### Fast Mode
```
overall_score = (strategic_fit * 0.50) +
                (eligibility * 0.30) +
                (timing * 0.20)

proceed_to_deep_analysis = (overall_score >= 0.55) AND
                            (eligibility >= 0.70)
```

### Thorough Mode
```
overall_score = (strategic_fit * 0.35) +
                (eligibility * 0.25) +
                (timing * 0.15) +
                (financial * 0.15) +
                (competition * 0.10)

proceed_to_deep_analysis = (overall_score >= 0.60) AND
                            (eligibility >= 0.75)
```

## 12-Factor Compliance

- ✅ **Factor 4**: Tools as Structured Outputs - Returns `ScreeningOutput` dataclass
- ✅ **Factor 6**: Stateless - No persistent state between runs
- ✅ **Factor 10**: Single Responsibility - Opportunity screening only
- ✅ **Factor 8**: Concurrent batch processing (10 fast, 5 thorough)

## Typical Workflow

1. **Discovery**: 200 opportunities identified by discovery tools
2. **Fast Screening**: Initial pass at $0.0004 each (~$0.08 total)
3. **Filtering**: ~30 opportunities pass threshold (0.55)
4. **Thorough Screening**: Second pass on 30 at $0.02 each (~$0.60)
5. **Human Gateway**: Manual review and selection
6. **Deep Analysis**: ~10 selected for Deep Intelligence Tool ($0.75-$42 each)

**Total Stage 1 Cost**: ~$0.68 to screen 200 opportunities
**Time**: ~7 minutes (400 seconds fast + 150 seconds thorough)

## Testing

```bash
cd tools/opportunity-screening-tool
python -m pytest tests/
```

## Configuration

Environment variables:
- `OPENAI_API_KEY`: Required for AI screening
- `SCREENING_DEFAULT_MODE`: Optional ("fast" or "thorough")
- `SCREENING_DEFAULT_THRESHOLD`: Optional (0.0-1.0)

## Tool Registry

Auto-discovered by Tool Registry via `12factors.toml`.

```python
from src.core.tool_registry import get_registry

registry = get_registry()
tool_meta = registry.get_tool("Opportunity Screening Tool")
print(f"Version: {tool_meta.version}")
print(f"Status: {tool_meta.status}")
```

## Architecture

```
tools/opportunity-screening-tool/
├── app/
│   ├── screening_tool.py        # Main tool implementation (BaseTool)
│   ├── screening_models.py      # Pydantic data models
│   └── screening_prompts.py     # AI prompt templates
├── baml_src/
│   └── screening.baml           # BAML schema definitions
├── tests/
│   ├── test_screening_tool.py
│   └── test_screening_batch.py
├── 12factors.toml               # 12-factor configuration
└── README.md                    # This file
```

## Roadmap

- [ ] Implement actual BAML AI calls (currently placeholder scoring)
- [ ] Add caching for repeated opportunity screening
- [ ] Implement retry logic for AI failures
- [ ] Add performance benchmarking suite
- [ ] Create integration tests with real opportunities
- [ ] Add support for custom scoring weights

## Related Tools

- **Discovery Tools**: BMF Filter, Grants.gov Search, Foundation Directory
- **Deep Intelligence Tool**: Stage 2 comprehensive analysis
- **Workflow Engine**: Orchestrates multi-tool pipelines
