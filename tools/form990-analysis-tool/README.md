# Form 990 Analysis Tool - 12-Factor Agents Implementation
*🟡 Intermediate Level - Deep Financial Analysis Following Human Layer Framework*

## What This Tool Does

The Form 990 Analysis Tool demonstrates **Factor 4: Tools as Structured Outputs** by performing deep financial analysis of nonprofit organizations using Form 990 database records. This is the **second tool** in the three-tool nonprofit grant research architecture.

**Think of it like**: A financial analyst that takes EINs from the BMF filter and produces structured financial health assessments, trend analysis, and grant capacity evaluations.

## Integration with Three-Tool Architecture

This tool fits into the complete workflow:
1. **BMF Filter Tool**: 700K organizations → 10 filtered organizations
2. **Form 990 Analysis Tool**: 10 organizations → deep financial analysis ← **(This Tool)**
3. **ProPublica Enrichment Tool**: Top organizations → comprehensive profiles

## 12-Factor Agents Principles (Human Layer Framework)

This tool implements the [Human Layer 12-Factor Agents Framework](https://github.com/humanlayer/12-factor-agents):

**Factor 1: Natural Language to Tool Calls** - Takes structured EINs from previous tools, not natural language
**Factor 2: Own Your Prompts** - Complete control over financial analysis algorithms and health scoring
**Factor 3: Own Your Context Window** - Database handles financial data, minimal context usage
**Factor 4: Tools as Structured Outputs** - Forces structured Form990AnalysisResult with guaranteed format
**Factor 5: Unify Execution and Business State** - Financial analysis unified with nonprofit database
**Factor 6: Launch/Pause/Resume with Simple APIs** - Single async execute() method for workflow integration
**Factor 7: Contact Humans with Tool Calls** - Provides human-readable financial insights and warnings
**Factor 8: Control Flow Management** - Explicit analysis flow: EINs → database → calculations → insights
**Factor 9: Compact Error Handling** - Analysis errors integrated into result structure
**Factor 10: Small, Focused Agents** - Single responsibility: multi-year financial analysis only
**Factor 12: Stateless Reducer Model** - Pure function: Form990AnalysisCriteria → Form990AnalysisResult

### Key Innovation: Factor 4 Implementation

This tool demonstrates **Factor 4: Tools as Structured Outputs** for financial analysis:
- Takes structured EIN list from BMF Filter Tool
- Executes deterministic database queries for Form 990 data
- Returns structured `Form990AnalysisResult` with guaranteed JSON format
- **Eliminates financial data parsing errors** in production environments

## Core Capabilities

### Multi-Year Financial Analysis
- **3-Year Trends**: Revenue, expenses, assets analysis across multiple years
- **Financial Health Scoring**: Liquidity, efficiency, program ratio assessment
- **Risk Assessment**: Warning flags for financial concerns
- **Grant Capacity**: Foundation grant-making capacity analysis (990-PF data)

### Structured Output Format

```typescript
Form990AnalysisResult {
    organizations: Form990OrganizationAnalysis[]  // Structured financial profiles
    execution_time_ms: float                      // Performance metadata
    total_organizations_analyzed: int             // Success metrics
    analysis_period: string                       // Data coverage period
}

Form990OrganizationAnalysis {
    ein: string                                   // Organization identifier
    name: string                                  // Organization name
    financial_years: Form990FinancialYear[]      // Multi-year data
    financial_health: Form990FinancialHealth     // Health assessment
    key_insights: string[]                       // Human-readable insights
    data_quality_score: float                   // Data completeness
}
```

## Integration with Catalynx Platform

This tool integrates with existing Catalynx infrastructure:
- **Database**: Uses `data/nonprofit_intelligence.db` (990/990-PF/990-EZ tables)
- **Performance**: Benchmarked against existing AI Heavy processors
- **Architecture**: Demonstrates 12-factor patterns alongside existing workflows
- **Environment**: Extends existing `.env` configuration

## Tool Structure

```
tools/form990-analysis-tool/
├── README.md                    # This file
├── 12factors.toml              # Human Layer 12-Factor Agents compliance
├── app/
│   ├── __init__.py
│   ├── form990_analyzer.py     # Core financial analysis logic
│   └── test_form990_tool.py    # Test implementation
└── baml_src/                   # BAML schemas (future enhancement)
    └── form990_analysis.baml   # Structured input/output definitions
```

## Quick Start

```python
from app.form990_analyzer import Form990AnalysisTool, Form990AnalysisCriteria

# Initialize tool
tool = Form990AnalysisTool()

# Analyze organizations (typically from BMF Filter Tool results)
criteria = Form990AnalysisCriteria(
    target_eins=["123456789", "987654321"],  # From BMF filter
    years_to_analyze=3,
    financial_health_analysis=True,
    grant_capacity_analysis=True
)

# Execute analysis
result = await tool.execute(criteria)

# Access structured results
for org in result.organizations:
    print(f"{org.name}: {org.financial_health.health_category}")
    print(f"  Health Score: {org.financial_health.overall_score}")
    print(f"  Key Insights: {org.key_insights}")
```

## Three-Tool Workflow Integration

This tool receives structured input from BMF Filter Tool and provides structured output to ProPublica Enrichment Tool:

```python
# Stage 1: BMF Filter
bmf_result = await bmf_tool.execute(bmf_criteria)

# Stage 2: Form 990 Analysis (This Tool)
target_eins = [org.ein for org in bmf_result.organizations]
form990_criteria = Form990AnalysisCriteria(target_eins=target_eins)
form990_result = await form990_tool.execute(form990_criteria)

# Stage 3: ProPublica Enrichment
high_scoring_eins = [org.ein for org in form990_result.organizations
                    if org.financial_health.overall_score > 70]
```

## Financial Analysis Features

### Health Assessment Algorithms
- **Liquidity Score**: Based on months of operating reserves
- **Efficiency Score**: Program expense ratio analysis
- **Operating Margin**: Revenue vs expense sustainability
- **Warning Flags**: Automated detection of financial concerns

### Multi-Year Trend Analysis
- **Revenue Growth**: Year-over-year change analysis
- **Expense Efficiency**: Program vs administrative cost trends
- **Asset Management**: Asset growth and utilization patterns
- **Financial Stability**: Multi-year consistency assessment

### Foundation Intelligence (990-PF)
- **Grant Distribution**: Analysis of foundation grant-making patterns
- **Asset Capacity**: Foundation asset-based grant capacity scoring
- **Distribution Requirements**: 5% minimum distribution compliance
- **Investment Performance**: Asset management effectiveness

## Performance Characteristics

- **Target Latency**: < 1000ms for analyzing 10 organizations
- **Database Efficiency**: Optimized queries for multi-year 990 data
- **Memory Usage**: < 1GB for typical analysis workloads
- **Scalability**: Stateless design enables horizontal scaling

## Factor 4 Benefits

By implementing **Factor 4: Tools as Structured Outputs**:
- ✅ **Eliminates JSON parsing errors** in financial data presentation
- ✅ **Guarantees consistent structure** for downstream tools
- ✅ **Enables reliable workflows** with predictable data formats
- ✅ **Supports production deployment** with error-free data exchange

## Environment Configuration

```bash
# Required
FORM990_DATABASE_PATH="data/nonprofit_intelligence.db"

# Optional
FORM990_CACHE_ENABLED=true
FORM990_MAX_ORGANIZATIONS=50
FORM990_DEFAULT_YEARS=3
FORM990_TIMEOUT_SECONDS=300
FORM990_LOG_PERFORMANCE=true
```

## Testing

```bash
# Test individual tool
cd tools/form990-analysis-tool
python app/test_form990_tool.py

# Test in three-tool workflow
cd tools
python three_tool_workflow_orchestrator.py
```

This tool demonstrates how **Factor 4: Tools as Structured Outputs** creates reliable financial analysis capabilities that eliminate common parsing errors while providing comprehensive nonprofit intelligence for grant research workflows.