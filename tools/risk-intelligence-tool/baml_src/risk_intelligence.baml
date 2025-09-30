// BAML Schema for Risk Intelligence Tool
// Multi-dimensional risk assessment with mitigation strategies

enum RiskLevel {
  minimal
  low
  medium
  high
  critical
}

enum RiskCategory {
  eligibility
  competition
  capacity
  timeline
  financial
  compliance
  reputational
  operational
}

enum MitigationPriority {
  immediate
  high
  medium
  low
}

class RiskIntelligenceInput {
  // Opportunity identification
  opportunity_id string
  opportunity_title string
  opportunity_description string
  funder_name string
  funder_type string

  // Organization context
  organization_ein string
  organization_name string
  organization_mission string
  years_of_operation int?

  // Opportunity details
  grant_amount float?
  application_deadline string?
  project_duration_months int?
  match_required bool?
  match_percentage float?

  // Eligibility criteria
  geographic_restrictions string[]?
  organization_type_requirements string[]?

  // Organization capabilities
  total_revenue float?
  total_expenses float?
  net_assets float?
  program_expense_ratio float?
  staff_count int?
  has_grant_manager bool?
  prior_grants_with_funder int?

  // Competitive context
  estimated_applicants int?
  typical_award_rate float?

  // User concerns
  concerns string[]?
}

class RiskFactor {
  category RiskCategory
  risk_level RiskLevel
  description string @description("Detailed description of this risk")
  likelihood float @description("Probability this risk materializes (0-1)")
  impact float @description("Severity if risk occurs (0-1)")
  risk_score float @description("likelihood × impact")
  evidence string[] @description("Specific evidence supporting this risk")
  related_factors string[]? @description("Other related risk factors")
}

class EligibilityRiskAssessment {
  overall_eligibility_score float @description("Score 0-1 indicating eligibility match")
  risk_level RiskLevel

  // Geographic
  geographic_match bool
  geographic_concerns string[]

  // Organization type
  type_match bool
  type_concerns string[]

  // Budget/size
  budget_match bool
  budget_concerns string[]

  // Other
  other_requirements_met bool
  other_concerns string[]

  // Recommendation
  proceed_recommendation bool
  recommendation_reasoning string
}

class CompetitionRiskAssessment {
  competition_level RiskLevel
  estimated_competition_score float @description("0-1, higher = more competitive")

  estimated_applicant_pool string @description("E.g., '50-100 applicants'")
  typical_success_rate float?
  organization_competitive_position string

  competitive_strengths string[]
  competitive_weaknesses string[]

  estimated_success_probability float @description("0-1 probability of winning")
  success_probability_reasoning string
}

class CapacityRiskAssessment {
  capacity_risk_level RiskLevel
  overall_capacity_score float @description("0-1 capacity adequacy score")

  staff_capacity_adequate bool
  staff_concerns string[]

  infrastructure_adequate bool
  infrastructure_concerns string[]

  management_capacity_adequate bool
  management_concerns string[]

  grant_experience_adequate bool
  experience_concerns string[]

  critical_gaps string[]
  moderate_gaps string[]
}

class TimelineRiskAssessment {
  timeline_risk_level RiskLevel
  timeline_feasibility_score float @description("0-1 timeline feasibility")

  days_until_deadline int?
  application_time_required int
  timeline_adequate bool
  deadline_concerns string[]

  project_timeline_feasible bool
  project_concerns string[]

  critical_milestones map<string, string>[]
}

class FinancialRiskAssessment {
  financial_risk_level RiskLevel
  financial_risk_score float @description("0-1 financial risk score")

  can_manage_budget bool
  budget_concerns string[]

  can_provide_match bool
  match_concerns string[]

  cash_flow_adequate bool
  cash_flow_concerns string[]

  sustainability_concerns string[]
}

class ComplianceRiskAssessment {
  compliance_risk_level RiskLevel
  compliance_risk_score float @description("0-1 compliance risk score")

  regulatory_requirements string[]
  regulatory_concerns string[]

  reporting_requirements string[]
  reporting_concerns string[]

  audit_requirements string[]
  audit_concerns string[]
}

class MitigationStrategy {
  risk_category RiskCategory
  strategy string @description("Specific mitigation strategy")
  priority MitigationPriority
  timeline string @description("When to implement (e.g., 'Before application', 'During project')")
  resources_required string[] @description("Resources needed to implement")
  success_indicators string[] @description("How to measure success")
  estimated_cost float?
  estimated_time_days int?
}

class AIRiskInsights {
  // Executive summary
  risk_executive_summary string @description("2-3 paragraph executive summary of risk analysis")

  // Critical risks
  top_3_risks string[] @description("Top 3 most critical risks")
  deal_breaker_risks string[] @description("Risks that should prevent proceeding")

  // Hidden risks
  overlooked_risks string[] @description("Risks that might be overlooked but are important")

  // Strategic considerations
  strategic_risk_factors string[] @description("Strategic risk considerations")

  // Recommendations
  go_no_go_recommendation bool @description("Should organization proceed?")
  recommendation_confidence float @description("Confidence in recommendation (0-1)")
  recommendation_reasoning string @description("Reasoning for go/no-go recommendation")

  // Alternatives
  risk_reduction_suggestions string[] @description("Ways to reduce risk before proceeding")
}

class RiskIntelligenceOutput {
  // Overall risk assessment
  overall_risk_level RiskLevel
  overall_risk_score float @description("Overall risk score 0-1")
  proceed_recommendation bool

  // Risk factors
  all_risk_factors RiskFactor[] @description("All identified risk factors")
  critical_risks RiskFactor[] @description("Critical/high risk factors")
  high_risks RiskFactor[] @description("High risk factors")
  manageable_risks RiskFactor[] @description("Medium/low risk factors")

  // Dimensional assessments
  eligibility_assessment EligibilityRiskAssessment
  competition_assessment CompetitionRiskAssessment
  capacity_assessment CapacityRiskAssessment
  timeline_assessment TimelineRiskAssessment
  financial_assessment FinancialRiskAssessment
  compliance_assessment ComplianceRiskAssessment

  // Mitigation strategies
  mitigation_strategies MitigationStrategy[] @description("Prioritized mitigation strategies")
  immediate_actions string[] @description("Actions to take immediately")

  // AI insights
  ai_insights AIRiskInsights

  // Summary
  risk_summary string @description("Concise risk summary")
  key_decision_factors string[] @description("Key factors for go/no-go decision")

  // Metadata
  confidence_level float @description("Confidence in analysis (0-1)")
}

// AI function for comprehensive risk analysis
function AnalyzeRiskIntelligence(input: RiskIntelligenceInput) -> RiskIntelligenceOutput {
  client GPT4o

  prompt #"
    You are an expert risk analyst specializing in grant opportunity assessment.

    Analyze the risks for the following grant opportunity:

    OPPORTUNITY:
    - Title: {{ input.opportunity_title }}
    - Funder: {{ input.funder_name }} ({{ input.funder_type }})
    - Description: {{ input.opportunity_description }}
    {% if input.grant_amount %}- Grant Amount: ${{ input.grant_amount }}{% endif %}
    {% if input.application_deadline %}- Deadline: {{ input.application_deadline }}{% endif %}
    {% if input.match_required %}- Match Required: {{ input.match_percentage }}%{% endif %}

    ORGANIZATION:
    - Name: {{ input.organization_name }} (EIN: {{ input.organization_ein }})
    - Mission: {{ input.organization_mission }}
    {% if input.years_of_operation %}- Years Operating: {{ input.years_of_operation }}{% endif %}
    {% if input.total_revenue %}- Annual Revenue: ${{ input.total_revenue }}{% endif %}
    {% if input.staff_count %}- Staff Count: {{ input.staff_count }}{% endif %}
    {% if input.prior_grants_with_funder %}- Prior Grants with Funder: {{ input.prior_grants_with_funder }}{% endif %}

    {% if input.concerns %}
    USER CONCERNS:
    {% for concern in input.concerns %}
    - {{ concern }}
    {% endfor %}
    {% endif %}

    Provide a comprehensive multi-dimensional risk analysis including:

    1. RISK FACTORS:
       - Identify ALL significant risks across all categories
       - For each risk: category, level, likelihood, impact, evidence
       - Prioritize critical and high risks

    2. ELIGIBILITY ASSESSMENT:
       - Geographic match and concerns
       - Organization type match and concerns
       - Budget/size match and concerns
       - Other eligibility factors
       - Clear proceed/don't proceed recommendation

    3. COMPETITION ASSESSMENT:
       - Competition level and estimated applicant pool
       - Organization's competitive position
       - Competitive strengths and weaknesses
       - Success probability estimate with reasoning

    4. CAPACITY ASSESSMENT:
       - Staff capacity adequacy
       - Infrastructure adequacy
       - Management capacity
       - Grant management experience
       - Critical vs. moderate capacity gaps

    5. TIMELINE ASSESSMENT:
       - Application timeline feasibility
       - Project timeline feasibility
       - Critical milestones and dates
       - Deadline concerns

    6. FINANCIAL ASSESSMENT:
       - Budget management capability
       - Match requirement capability
       - Cash flow adequacy
       - Sustainability concerns

    7. COMPLIANCE ASSESSMENT:
       - Regulatory requirements and concerns
       - Reporting requirements and concerns
       - Audit requirements and concerns

    8. MITIGATION STRATEGIES:
       - Prioritized strategies for each major risk
       - Timeline for implementation (before application, during project, etc.)
       - Resources required and success indicators
       - Immediate actions needed

    9. AI INSIGHTS:
       - Executive summary of risk landscape
       - Top 3 most critical risks
       - Deal-breaker risks (if any)
       - Hidden/overlooked risks
       - Go/no-go recommendation with confidence level and reasoning
       - Risk reduction suggestions

    10. DECISION SUPPORT:
        - Risk summary
        - Key decision factors
        - Clear overall recommendation

    Be thorough, objective, and provide actionable insights. Consider both obvious and subtle risks.
  "#
}
