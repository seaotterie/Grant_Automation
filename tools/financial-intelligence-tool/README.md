# Financial Intelligence Tool

**12-Factor Compliant Comprehensive Financial Analysis Tool**

## Purpose

Supporting tool for deep financial health assessment with AI-enhanced insights. Analyzes nonprofit 990 financial data to provide comprehensive metrics, trend analysis, grant capacity assessment, and strategic recommendations.

**Pipeline Position**:
- Input: 990 financial data from XML parsers or database
- Processing: Comprehensive financial analysis with AI insights
- Output: Structured financial intelligence for decision support
- Consumers: Deep Intelligence Tool, Decision Support Systems, Report Generators

## Features

### Core Financial Metrics (15+ metrics)

**Liquidity Analysis**:
- Current Ratio
- Months of Operating Expenses
- Liquid Assets Ratio

**Efficiency Analysis**:
- Program Expense Ratio
- Administrative Expense Ratio
- Fundraising Expense Ratio
- Fundraising Efficiency

**Sustainability Analysis**:
- Revenue Growth Rate
- Expense Growth Rate
- Net Assets Growth Rate
- Operating Margin

**Diversification Analysis**:
- Revenue Concentration Score
- Largest Revenue Source Percentage

**Capacity Analysis**:
- Asset to Revenue Ratio
- Debt to Asset Ratio

### Financial Health Assessment

- **Overall Rating**: Excellent, Good, Fair, Concerning, Critical
- **Health Score**: 0-1 comprehensive score
- **Strengths Identification**: 3-5 key financial strengths with metrics
- **Concerns Identification**: Key concerns with severity levels and recommendations

### Trend Analysis

- Multi-year financial trend analysis
- Revenue, expense, and net asset trends
- Trend interpretation and forecasting
- Historical pattern recognition

### Grant Capacity Assessment

- **Budget Capacity**: Maximum grant size organization can handle
- **Administrative Capacity**: Admin infrastructure assessment
- **Sustainability Assessment**: Long-term viability indicators
- **Match Capability**: Match funding capacity and sources

### AI-Enhanced Insights

- Executive summary of financial health
- Strategic opportunities and risks
- Competitive advantages and weaknesses
- Financial management recommendations
- Grant strategy recommendations
- Industry comparison (if NTEE code provided)
- Peer benchmarking insights

## Usage

### Python API

```python
from tools.financial_intelligence_tool.app import analyze_financial_intelligence

result = await analyze_financial_intelligence(
    organization_ein="12-3456789",
    organization_name="Example Nonprofit",
    total_revenue=1500000,
    total_expenses=1300000,
    total_assets=2000000,
    total_liabilities=500000,
    net_assets=1500000,
    contributions_grants=800000,
    program_service_revenue=600000,
    investment_income=80000,
    other_revenue=20000,
    program_expenses=1000000,
    admin_expenses=200000,
    fundraising_expenses=100000,
    # Optional historical data for trend analysis
    prior_year_revenue=1400000,
    prior_year_expenses=1250000,
    prior_year_net_assets=1400000,
    # Optional context
    organization_mission="Education and youth development",
    ntee_code="B25",
    years_of_operation=15
)

if result.is_success():
    intelligence = result.data

    print(f"Health Rating: {intelligence.overall_health_rating.value}")
    print(f"Health Score: {intelligence.overall_health_score:.2f}")
    print(f"\nProgram Expense Ratio: {intelligence.metrics.program_expense_ratio:.1%}")
    print(f"Months of Expenses: {intelligence.metrics.months_of_expenses:.1f}")

    print(f"\nGrant Capacity:")
    print(f"  Max Grant Size: ${intelligence.grant_capacity.can_handle_budget:,.0f}")
    print(f"  Can Provide Match: {intelligence.grant_capacity.can_provide_match}")
    print(f"  Max Match: {intelligence.grant_capacity.max_match_percentage:.0f}%")

    print(f"\nStrengths:")
    for strength in intelligence.strengths:
        print(f"  - {strength.description}")

    print(f"\nConcerns:")
    for concern in intelligence.concerns:
        print(f"  - [{concern.severity}] {concern.description}")
        print(f"    Recommendation: {concern.recommendation}")
```

### Using BaseTool Interface

```python
from tools.financial_intelligence_tool.app import FinancialIntelligenceTool, FinancialIntelligenceInput

tool = FinancialIntelligenceTool(config={
    "openai_api_key": "sk-..."
})

financial_input = FinancialIntelligenceInput(
    organization_ein="12-3456789",
    organization_name="Example Nonprofit",
    total_revenue=1500000,
    total_expenses=1300000,
    total_assets=2000000,
    total_liabilities=500000,
    net_assets=1500000,
    contributions_grants=800000,
    program_service_revenue=600000,
    investment_income=80000,
    other_revenue=20000,
    program_expenses=1000000,
    admin_expenses=200000,
    fundraising_expenses=100000
)

result = await tool.execute(financial_input=financial_input)
```

## Output Structure

```python
@dataclass
class FinancialIntelligenceOutput:
    # Core metrics
    metrics: FinancialMetrics

    # Overall assessment
    overall_health_rating: FinancialHealthRating
    overall_health_score: float  # 0-1

    # Strengths and concerns
    strengths: List[FinancialStrength]
    concerns: List[FinancialConcern]

    # Trend analysis
    trends: List[TrendAnalysis]

    # Grant capacity
    grant_capacity: GrantCapacityAssessment

    # AI insights
    ai_insights: AIFinancialInsights

    # Metadata
    analysis_date: str
    data_quality_score: float  # 0-1
    confidence_level: float  # 0-1
    processing_time_seconds: float
    api_cost_usd: float  # $0.03
```

## Financial Metrics Calculations

### Liquidity Metrics
- **Current Ratio** = Total Assets / Total Liabilities
- **Months of Expenses** = (Net Assets / Total Expenses) × 12
- **Liquid Assets Ratio** = Net Assets / Total Assets

### Efficiency Metrics
- **Program Expense Ratio** = Program Expenses / Total Expenses
- **Admin Expense Ratio** = Admin Expenses / Total Expenses
- **Fundraising Expense Ratio** = Fundraising Expenses / Total Expenses
- **Fundraising Efficiency** = Contributions / Fundraising Expenses

### Sustainability Metrics
- **Revenue Growth Rate** = (Current Revenue - Prior Revenue) / Prior Revenue
- **Operating Margin** = (Revenue - Expenses) / Revenue

### Diversification Metrics
- **Revenue Concentration** = Herfindahl Index of revenue sources
- Lower score = more diversified (better)

## Health Rating Criteria

### Excellent (0.80+)
- Strong liquidity (6+ months expenses)
- High program efficiency (75%+ program ratio)
- Diversified revenue
- Positive growth trends

### Good (0.65-0.79)
- Adequate liquidity (3-6 months)
- Good program efficiency (70-75%)
- Moderate diversification
- Stable or positive trends

### Fair (0.50-0.64)
- Limited liquidity (1-3 months)
- Acceptable efficiency (65-70%)
- Some concentration concerns
- Mixed trends

### Concerning (0.35-0.49)
- Low liquidity (<1 month)
- Below-standard efficiency (<65%)
- High concentration
- Negative trends

### Critical (<0.35)
- Severe liquidity issues
- Poor efficiency
- Critical sustainability concerns
- Multiple negative trends

## Grant Capacity Assessment

### Budget Capacity
- Organizations with health score >0.7 can typically handle grants up to 50% of annual revenue
- Organizations with health score <0.7 limited to 25% of annual revenue
- Considers admin infrastructure, debt levels, and reserves

### Match Capability
- Requires 3+ months operating reserves
- Requires positive operating margin
- Maximum match percentage = months of expenses × 5%
- Suggested match sources based on revenue composition

## 12-Factor Compliance

- ✅ **Factor 4**: Structured FinancialIntelligenceOutput with comprehensive modules
- ✅ **Factor 6**: Stateless - no persistent state between runs
- ✅ **Factor 10**: Single Responsibility - financial intelligence analysis only
- ✅ **Factor 8**: Batch processing capable

## Testing

```bash
cd tools/financial-intelligence-tool
python -m pytest tests/
```

## Configuration

Environment variables:
- `OPENAI_API_KEY`: Required for AI insights generation

## Cost

**$0.03 per analysis**

## Tool Registry

Auto-discovered by Tool Registry via `12factors.toml`.

```python
from src.core.tool_registry import get_registry

registry = get_registry()
tool_meta = registry.get_tool("Financial Intelligence Tool")
print(f"Version: {tool_meta.version}")
print(f"Cost: ${tool_meta.config['tool']['output_structure']['cost_per_analysis']}")
```

## Replaced Processors

- ✅ `financial_scorer.py`

## Roadmap

- [ ] Implement actual BAML AI calls (currently placeholder analysis)
- [ ] Add peer benchmarking data integration
- [ ] Implement industry-specific scoring models
- [ ] Add multi-year historical trend visualization
- [ ] Integrate with external financial databases for validation
- [ ] Add scenario modeling capabilities

## Related Tools

- **XML 990 Parser Tools**: Source of financial data
- **Form 990 Analysis Tool**: Additional financial analysis
- **Deep Intelligence Tool**: Consumer of financial intelligence
- **Tool Registry**: Auto-discovery and metadata management
