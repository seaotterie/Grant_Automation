# Risk Intelligence Tool

**12-Factor Compliant Multi-Dimensional Risk Assessment Tool**

## Purpose

Supporting tool for comprehensive risk analysis with AI-enhanced insights and actionable mitigation strategies. Performs 6-dimensional risk assessment to support grant opportunity decision-making.

**Pipeline Position**:
- Input: Opportunity data and organizational context
- Processing: Multi-dimensional risk analysis with AI insights
- Output: Structured risk intelligence with mitigation strategies
- Consumers: Opportunity Screening Tool, Deep Intelligence Tool, Decision Support Systems

## Features

### 6-Dimensional Risk Assessment

**1. Eligibility Risk Assessment**
- Geographic eligibility matching
- Organization type requirements
- Budget/size eligibility
- Other requirement verification
- Overall eligibility score and recommendation

**2. Competition Risk Assessment**
- Competition level analysis
- Estimated applicant pool
- Competitive strengths and weaknesses
- Success probability estimation
- Competitive positioning

**3. Capacity Risk Assessment**
- Staff capacity evaluation
- Infrastructure adequacy
- Management capacity
- Grant management experience
- Critical and moderate capacity gaps

**4. Timeline Risk Assessment**
- Application deadline feasibility
- Project timeline feasibility
- Critical milestones identification
- Time requirement analysis

**5. Financial Risk Assessment**
- Budget management capability
- Match requirement capability
- Cash flow adequacy
- Sustainability concerns

**6. Compliance Risk Assessment**
- Regulatory requirements
- Reporting requirements
- Audit requirements
- Compliance concerns

### Risk Categorization

All risks categorized by:
- **Level**: Minimal, Low, Medium, High, Critical
- **Category**: Eligibility, Competition, Capacity, Timeline, Financial, Compliance, Reputational, Operational
- **Likelihood**: 0-1 probability of occurrence
- **Impact**: 0-1 severity if occurs
- **Risk Score**: Likelihood × Impact

### Mitigation Strategies

Prioritized mitigation strategies including:
- Strategy description
- Priority level (Immediate, High, Medium, Low)
- Implementation timeline
- Required resources
- Success indicators
- Estimated cost and time

### AI-Enhanced Insights

- Executive risk summary
- Top 3 critical risks
- Deal-breaker risk identification
- Overlooked risk identification
- Go/no-go recommendation with confidence
- Risk reduction suggestions

## Usage

### Python API

```python
from tools.risk_intelligence_tool.app import analyze_risk_intelligence

result = await analyze_risk_intelligence(
    opportunity_id="opp-001",
    opportunity_title="Education Innovation Grant",
    opportunity_description="Supporting innovative education programs...",
    funder_name="Smith Foundation",
    funder_type="foundation",
    organization_ein="12-3456789",
    organization_name="Example Nonprofit",
    organization_mission="Improving education access",
    # Optional context
    grant_amount=500000,
    application_deadline="2025-12-31",
    project_duration_months=24,
    match_required=True,
    match_percentage=20,
    total_revenue=2000000,
    total_expenses=1800000,
    net_assets=1500000,
    program_expense_ratio=0.80,
    staff_count=15,
    has_grant_manager=True,
    prior_grants_with_funder=2,
    concerns=["Tight deadline", "Match requirement"]
)

if result.is_success():
    risk_analysis = result.data

    print(f"Overall Risk: {risk_analysis.overall_risk_level.value}")
    print(f"Risk Score: {risk_analysis.overall_risk_score:.2f}")
    print(f"Proceed Recommended: {risk_analysis.proceed_recommendation}")

    print(f"\nCritical Risks: {len(risk_analysis.critical_risks)}")
    for risk in risk_analysis.critical_risks:
        print(f"  - {risk.description}")
        print(f"    Evidence: {', '.join(risk.evidence)}")

    print(f"\nMitigation Strategies:")
    for strategy in risk_analysis.mitigation_strategies[:3]:
        print(f"  - [{strategy.priority.value}] {strategy.strategy}")
        print(f"    Timeline: {strategy.timeline}")

    print(f"\nAI Recommendation:")
    print(f"  Go/No-Go: {'GO' if risk_analysis.ai_insights.go_no_go_recommendation else 'NO-GO'}")
    print(f"  Confidence: {risk_analysis.ai_insights.recommendation_confidence:.0%}")
    print(f"  Reasoning: {risk_analysis.ai_insights.recommendation_reasoning}")
```

### Using BaseTool Interface

```python
from tools.risk_intelligence_tool.app import RiskIntelligenceTool, RiskIntelligenceInput

tool = RiskIntelligenceTool(config={
    "openai_api_key": "sk-..."
})

risk_input = RiskIntelligenceInput(
    opportunity_id="opp-001",
    opportunity_title="Grant Title",
    opportunity_description="Description",
    funder_name="Foundation",
    funder_type="foundation",
    organization_ein="12-3456789",
    organization_name="Nonprofit",
    organization_mission="Mission",
    grant_amount=500000,
    total_revenue=2000000
)

result = await tool.execute(risk_input=risk_input)
```

## Output Structure

```python
@dataclass
class RiskIntelligenceOutput:
    # Overall assessment
    overall_risk_level: RiskLevel
    overall_risk_score: float  # 0-1
    proceed_recommendation: bool

    # Risk factors
    all_risk_factors: List[RiskFactor]
    critical_risks: List[RiskFactor]
    high_risks: List[RiskFactor]
    manageable_risks: List[RiskFactor]

    # Dimensional assessments
    eligibility_assessment: EligibilityRiskAssessment
    competition_assessment: CompetitionRiskAssessment
    capacity_assessment: CapacityRiskAssessment
    timeline_assessment: TimelineRiskAssessment
    financial_assessment: FinancialRiskAssessment
    compliance_assessment: ComplianceRiskAssessment

    # Mitigation
    mitigation_strategies: List[MitigationStrategy]
    immediate_actions: List[str]

    # AI insights
    ai_insights: AIRiskInsights

    # Summary
    risk_summary: str
    key_decision_factors: List[str]

    # Metadata
    analysis_date: str
    confidence_level: float
    processing_time_seconds: float
    api_cost_usd: float  # $0.02
```

## Risk Level Criteria

### Minimal Risk
- No significant barriers
- High success probability
- Standard mitigation sufficient

### Low Risk
- Minor concerns easily addressed
- Good organizational fit
- Proceed with confidence

### Medium Risk
- Moderate concerns requiring attention
- Targeted mitigation needed
- Proceed with careful planning

### High Risk
- Significant concerns requiring resolution
- Substantial mitigation effort required
- Reconsider or delay if risks cannot be mitigated

### Critical Risk
- Major barriers to success
- Deal-breaker concerns present
- Not recommended to proceed unless risks fully resolved

## Common Risk Scenarios

### Eligibility Risks
- Geographic restrictions not met
- Organization type mismatch
- Budget size mismatch
- Missing required certifications

### Competition Risks
- High competition (100+ applicants)
- No competitive advantages
- Low historical success rates
- Crowded funding space

### Capacity Risks
- No grant manager
- Small staff (<5 people)
- No prior experience with funder
- Limited infrastructure

### Timeline Risks
- Deadline in <30 days
- Application requires >45 days
- Long project duration (>3 years)
- Critical milestones conflict

### Financial Risks
- Grant >50% of annual revenue
- Match >30% of net assets
- Negative cash flow
- High debt levels

### Compliance Risks
- Complex regulatory requirements
- Extensive reporting requirements
- Single Audit required
- New compliance areas

## 12-Factor Compliance

- ✅ **Factor 4**: Structured RiskIntelligenceOutput with 6 dimensional assessments
- ✅ **Factor 6**: Stateless - no persistent state between runs
- ✅ **Factor 10**: Single Responsibility - risk intelligence analysis only
- ✅ **Factor 8**: Batch processing capable

## Testing

```bash
cd tools/risk-intelligence-tool
python -m pytest tests/
```

## Configuration

Environment variables:
- `OPENAI_API_KEY`: Required for AI insights generation

## Cost

**$0.02 per analysis**

## Tool Registry

Auto-discovered by Tool Registry via `12factors.toml`.

## Replaced Processors

- ✅ `risk_assessor.py`

## Related Tools

- **Opportunity Screening Tool**: Consumer of risk intelligence
- **Deep Intelligence Tool**: Consumer of risk intelligence for comprehensive analysis
- **Financial Intelligence Tool**: Complementary financial analysis
- **Tool Registry**: Auto-discovery and metadata management
