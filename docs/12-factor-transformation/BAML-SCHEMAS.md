# BAML Schemas: Structured Output Specifications

## Overview

This document provides comprehensive BAML (Boundary AI Markup Language) schemas for all micro-tools in the 12-factor Catalynx transformation. These schemas ensure type-safe, structured outputs that enable reliable tool composition and workflow orchestration.

## BAML Framework Benefits

### Type Safety
- **Compile-time validation** of schema definitions
- **Runtime output validation** against declared types
- **Automatic client generation** for multiple languages

### Model Agnostic
- **Works across different LLM providers** (OpenAI, Anthropic, etc.)
- **Handles non-native structured output** models
- **Schema-aligned parsing** for flexible model responses

### Developer Experience
- **Syntax highlighting** and validation in editors
- **Auto-completion** for schema types
- **Version management** for schema evolution

---

## Core Data Types

### Base Types
```baml
// Common base types used across all schemas

class Organization {
  ein: string
  name: string
  ntee_code: string?
  state: string?
  city: string?
  zip_code: string?
  website: string?
  mission_statement: string?
}

class FinancialData {
  tax_year: int
  total_revenue: float
  total_expenses: float
  net_assets: float
  program_expenses: float?
  administrative_expenses: float?
  fundraising_expenses: float?
}

class ContactInfo {
  name: string
  title: string?
  email: string?
  phone: string?
}

class Address {
  street: string
  city: string
  state: string
  zip_code: string
  country: string
}

// Enums for standardized values
enum ConfidenceLevel {
  VERY_LOW    // 0.0 - 0.2
  LOW         // 0.2 - 0.4
  MEDIUM      // 0.4 - 0.6
  HIGH        // 0.6 - 0.8
  VERY_HIGH   // 0.8 - 1.0
}

enum RiskLevel {
  VERY_LOW
  LOW
  MEDIUM
  HIGH
  CRITICAL
}

enum PriorityLevel {
  LOW
  MEDIUM
  HIGH
  URGENT
}

enum DataQuality {
  EXCELLENT
  GOOD
  FAIR
  POOR
  MISSING
}
```

---

## Data Collection Schemas

### BMF Data Fetcher Schema
```baml
function fetch_bmf_data {
  client GPT4o
  prompt #"
    Extract and structure BMF data for organization:
    EIN: {{ ein }}
    Required fields: {{ required_fields }}
    Include historical data: {{ include_history }}

    Ensure all financial amounts are properly formatted and validated.
  "#

  response BMFData {
    // Core identification
    ein: string
    organization_name: string
    aka_names: string[]

    // Classification
    ntee_code: string?
    ntee_description: string?
    organization_type: OrganizationType
    subsection: string?

    // Location
    address: Address

    // Financial highlights
    revenue_amount: float?
    asset_amount: float?
    income_amount: float?

    // Status and dates
    ruling_date: string?
    tax_period: string?

    // Data quality
    data_completeness: float
    last_updated: string
    data_source: string
  }

  enum OrganizationType {
    PUBLIC_CHARITY
    PRIVATE_FOUNDATION
    PRIVATE_OPERATING_FOUNDATION
    OTHER_EXEMPT_ORGANIZATION
  }
}
```

### 990 Filing Fetcher Schema
```baml
function fetch_990_filing {
  client GPT4o
  prompt #"
    Retrieve and structure 990 filing data:
    EIN: {{ ein }}
    Tax year: {{ tax_year }}
    Include schedules: {{ requested_schedules }}

    Focus on accuracy of financial data and proper classification.
  "#

  response Form990Data {
    // Filing metadata
    ein: string
    tax_year: int
    filing_type: FilingType
    filing_date: string?
    pdf_url: string?

    // Financial summary
    total_revenue: float
    total_expenses: float
    net_assets_eoy: float
    net_assets_boy: float

    // Revenue breakdown
    contributions_grants: float?
    program_service_revenue: float?
    investment_income: float?
    other_revenue: float?

    // Expense breakdown
    program_expenses: float?
    management_expenses: float?
    fundraising_expenses: float?

    // Key ratios (auto-calculated)
    program_expense_ratio: float?
    administrative_ratio: float?
    fundraising_ratio: float?

    // Schedules and attachments
    schedules_included: ScheduleType[]
    schedule_data: ScheduleData[]

    // Data quality indicators
    data_quality: DataQuality
    completeness_score: float
    validation_notes: string[]
  }

  enum FilingType {
    FORM_990
    FORM_990EZ
    FORM_990PF
    FORM_990N
  }

  enum ScheduleType {
    SCHEDULE_A  // Public Charity Status
    SCHEDULE_B  // Contributors
    SCHEDULE_D  // Supplemental Financial Statements
    SCHEDULE_G  // Fundraising Activities
    SCHEDULE_I  // Grants and Assistance
    SCHEDULE_O  // Supplemental Information
  }

  class ScheduleData {
    schedule_type: ScheduleType
    data: object  // Flexible structure for different schedules
    completeness: float
  }
}
```

### Grant Opportunity Fetcher Schema
```baml
function fetch_federal_opportunities {
  client GPT4o
  prompt #"
    Search and structure federal grant opportunities:
    Search criteria: {{ search_criteria }}
    CFDA numbers: {{ cfda_numbers }}
    Keywords: {{ keywords }}
    Eligibility: {{ eligibility_filters }}
    Deadline range: {{ date_range }}

    Prioritize opportunities with clear eligibility and deadline information.
  "#

  response GrantOpportunities {
    // Search metadata
    search_criteria: SearchCriteria
    total_found: int
    search_date: string
    last_updated: string

    // Opportunities
    opportunities: Opportunity[]

    // Search quality
    search_quality: SearchQualityMetrics
  }

  class SearchCriteria {
    keywords: string[]
    cfda_numbers: string[]
    agencies: string[]
    eligibility_types: string[]
    funding_range: FundingRange?
    deadline_range: DateRange?
  }

  class Opportunity {
    // Identification
    opportunity_number: string
    title: string
    agency: string
    cfda_number: string?

    // Funding details
    total_funding: float?
    award_ceiling: float?
    award_floor: float?
    estimated_awards: int?

    // Timeline
    post_date: string?
    application_due_date: string?
    estimated_award_date: string?

    // Eligibility
    eligible_applicants: string[]
    ineligible_entities: string[]

    // Requirements
    cost_sharing: bool?
    matching_funds_required: bool?
    matching_percentage: float?

    // Content
    description: string
    program_description: string?
    award_description: string?

    // URLs and documents
    opportunity_url: string?
    application_package_url: string?

    // Quality indicators
    information_completeness: float
    eligibility_clarity: ConfidenceLevel
    deadline_certainty: ConfidenceLevel
  }

  class FundingRange {
    min_amount: float?
    max_amount: float?
  }

  class DateRange {
    start_date: string
    end_date: string
  }

  class SearchQualityMetrics {
    result_relevance: float
    data_completeness: float
    search_coverage: float
    update_recency: float
  }
}
```

---

## Analysis Schemas

### Financial Metrics Calculator Schema
```baml
function calculate_financial_metrics {
  client GPT4o
  prompt #"
    Calculate comprehensive financial health metrics:

    Organization: {{ organization_name }}
    Financial data: {{ financial_data }}
    Comparison period: {{ comparison_years }} years

    Calculate standard nonprofit financial ratios and provide interpretation
    of financial health, efficiency, and sustainability indicators.
  "#

  response FinancialMetrics {
    // Core efficiency ratios
    program_expense_ratio: float        // Program expenses / Total expenses
    administrative_ratio: float         // Admin expenses / Total expenses
    fundraising_ratio: float           // Fundraising expenses / Total expenses

    // Revenue ratios
    revenue_concentration_ratio: float  // Largest revenue source / Total revenue
    contribution_dependency: float     // Contributions / Total revenue
    earned_revenue_ratio: float        // Program revenue / Total revenue

    // Financial health indicators
    operating_margin: float            // (Revenue - Expenses) / Revenue
    net_asset_growth: float           // YoY net asset change %
    months_of_expenses: float         // Net assets / (Monthly expenses)
    debt_to_asset_ratio: float        // Total liabilities / Total assets

    // Liquidity measures
    current_ratio: float?             // Current assets / Current liabilities
    quick_ratio: float?               // Quick assets / Current liabilities
    cash_to_expenses_ratio: float     // Cash / Monthly expenses

    // Overall assessments
    financial_health_score: float     // 0.0 to 1.0 composite score
    sustainability_score: float      // 0.0 to 1.0 sustainability assessment
    efficiency_score: float          // 0.0 to 1.0 operational efficiency

    // Benchmarking context
    sector_percentile: float?         // Percentile rank within NTEE sector
    size_percentile: float?           // Percentile rank within size category

    // Qualitative assessments
    strengths: string[]
    concerns: string[]
    recommendations: string[]

    // Metadata
    calculation_date: string
    data_quality: DataQuality
    confidence_level: ConfidenceLevel
    benchmark_data_available: bool
  }
}
```

### Risk Assessment Schema
```baml
function calculate_risk_score {
  client GPT4o
  prompt #"
    Perform comprehensive risk assessment:

    Organization: {{ organization }}
    Financial metrics: {{ financial_metrics }}
    Historical data: {{ historical_data }}
    External factors: {{ external_factors }}

    Assess risks across financial, operational, compliance, and market dimensions.
    Provide specific risk factors and mitigation recommendations.
  "#

  response RiskAssessment {
    // Overall risk
    overall_risk_score: float          // 0.0 (low) to 1.0 (high)
    overall_risk_level: RiskLevel

    // Risk categories
    financial_risk: RiskCategory
    operational_risk: RiskCategory
    compliance_risk: RiskCategory
    market_risk: RiskCategory
    governance_risk: RiskCategory

    // Specific risk factors
    high_risk_factors: RiskFactor[]
    medium_risk_factors: RiskFactor[]

    // Risk trends
    risk_trend: TrendDirection
    risk_velocity: float              // Rate of risk change

    // Mitigation
    mitigation_strategies: MitigationStrategy[]
    monitoring_recommendations: string[]

    // Context
    risk_tolerance_assessment: string
    external_risk_factors: string[]

    // Metadata
    assessment_date: string
    confidence_level: ConfidenceLevel
    data_quality: DataQuality
  }

  class RiskCategory {
    category_name: string
    risk_score: float                 // 0.0 to 1.0
    risk_level: RiskLevel
    contributing_factors: string[]
    trend: TrendDirection
  }

  class RiskFactor {
    factor_name: string
    description: string
    impact_level: ImpactLevel
    likelihood: LikelihoodLevel
    mitigation_priority: PriorityLevel
    evidence: string[]
  }

  class MitigationStrategy {
    strategy_name: string
    description: string
    implementation_difficulty: DifficultyLevel
    expected_impact: ImpactLevel
    timeline: string
    resources_required: string[]
  }

  enum TrendDirection {
    IMPROVING
    STABLE
    DETERIORATING
    VOLATILE
  }

  enum ImpactLevel {
    MINIMAL
    LOW
    MODERATE
    HIGH
    SEVERE
  }

  enum LikelihoodLevel {
    VERY_UNLIKELY
    UNLIKELY
    POSSIBLE
    LIKELY
    VERY_LIKELY
  }

  enum DifficultyLevel {
    EASY
    MODERATE
    DIFFICULT
    VERY_DIFFICULT
  }
}
```

### Opportunity Scoring Schema
```baml
function score_opportunity_fit {
  client GPT4o
  prompt #"
    Score opportunity fit for organization:

    Organization profile: {{ organization_profile }}
    Opportunity details: {{ opportunity }}
    Scoring criteria: {{ scoring_weights }}

    Provide detailed scoring across all evaluation dimensions with
    specific justification for each score component.
  "#

  response OpportunityScore {
    // Overall assessment
    overall_score: float              // 0.0 to 1.0
    recommendation: RecommendationLevel

    // Detailed scoring
    eligibility_score: ScoreComponent
    mission_alignment_score: ScoreComponent
    capacity_score: ScoreComponent
    geographic_score: ScoreComponent
    timing_score: ScoreComponent
    competition_score: ScoreComponent
    financial_fit_score: ScoreComponent

    // Qualitative assessment
    strengths: OpportunityStrength[]
    concerns: OpportunityConcern[]
    requirements_analysis: RequirementAnalysis[]

    // Strategic considerations
    strategic_value: StrategicValue
    resource_requirements: ResourceRequirement[]
    success_probability: float        // 0.0 to 1.0

    // Recommendations
    application_recommendation: string
    preparation_timeline: string
    key_success_factors: string[]
    risk_mitigation_steps: string[]

    // Metadata
    scoring_date: string
    confidence_level: ConfidenceLevel
    data_completeness: float
  }

  class ScoreComponent {
    score: float                      // 0.0 to 1.0
    weight: float                     // Relative importance
    rationale: string
    supporting_evidence: string[]
    improvement_suggestions: string[]
  }

  class OpportunityStrength {
    strength_area: string
    description: string
    competitive_advantage: bool
    leverage_strategy: string
  }

  class OpportunityConcern {
    concern_area: string
    description: string
    severity: SeverityLevel
    mitigation_options: string[]
  }

  class RequirementAnalysis {
    requirement: string
    organization_capability: CapabilityLevel
    gap_analysis: string
    development_needed: string[]
  }

  class StrategicValue {
    mission_advancement: float        // 0.0 to 1.0
    capacity_building: float
    relationship_building: float
    visibility_enhancement: float
    long_term_sustainability: float
  }

  class ResourceRequirement {
    resource_type: ResourceType
    amount_needed: string
    current_availability: AvailabilityLevel
    acquisition_strategy: string
  }

  enum RecommendationLevel {
    HIGHLY_RECOMMENDED
    RECOMMENDED
    CONSIDER_WITH_CAUTION
    NOT_RECOMMENDED
  }

  enum SeverityLevel {
    MINOR
    MODERATE
    MAJOR
    CRITICAL
  }

  enum CapabilityLevel {
    EXCEEDS_REQUIREMENTS
    MEETS_REQUIREMENTS
    PARTIALLY_MEETS
    DOES_NOT_MEET
    UNKNOWN
  }

  enum ResourceType {
    FINANCIAL
    HUMAN_RESOURCES
    EXPERTISE
    INFRASTRUCTURE
    PARTNERSHIPS
    TIME
  }

  enum AvailabilityLevel {
    READILY_AVAILABLE
    AVAILABLE_WITH_EFFORT
    LIMITED_AVAILABILITY
    NOT_AVAILABLE
  }
}
```

---

## Intelligence Schemas

### AI Content Analysis Schema
```baml
function analyze_content_intelligence {
  client GPT4o
  prompt #"
    Analyze content for grant research intelligence:

    Content type: {{ content_type }}
    Content: {{ content }}
    Analysis objectives: {{ analysis_focus }}

    Extract actionable intelligence including themes, requirements,
    success factors, and strategic insights for grant applications.
  "#

  response ContentIntelligence {
    // Content summary
    content_summary: string
    key_themes: Theme[]

    // Funding intelligence
    funding_priorities: FundingPriority[]
    funding_preferences: FundingPreference[]
    award_patterns: AwardPattern[]

    // Requirements analysis
    application_requirements: Requirement[]
    evaluation_criteria: EvaluationCriterion[]
    success_factors: SuccessFactor[]

    // Risk and opportunity identification
    opportunity_indicators: OpportunityIndicator[]
    risk_flags: RiskFlag[]
    competitive_landscape: CompetitiveLandscape

    // Strategic insights
    strategic_recommendations: StrategyRecommendation[]
    timing_insights: TimingInsight[]
    partnership_opportunities: PartnershipOpportunity[]

    // Metadata
    analysis_confidence: ConfidenceLevel
    content_quality: DataQuality
    intelligence_value: IntelligenceValue
    analysis_date: string
  }

  class Theme {
    theme_name: string
    frequency: int
    importance_score: float           // 0.0 to 1.0
    related_keywords: string[]
    context_examples: string[]
  }

  class FundingPriority {
    priority_area: string
    priority_level: PriorityLevel
    funding_amount_range: FundingRange?
    geographic_focus: string[]
    target_populations: string[]
    evidence_strength: ConfidenceLevel
  }

  class FundingPreference {
    preference_type: PreferenceType
    description: string
    weight: float                     // Relative importance
    examples: string[]
  }

  class AwardPattern {
    pattern_type: PatternType
    description: string
    frequency: string
    typical_amount: FundingRange?
    duration: string?
    success_indicators: string[]
  }

  class Requirement {
    requirement_type: RequirementType
    description: string
    mandatory: bool
    complexity_level: ComplexityLevel
    common_challenges: string[]
    success_tips: string[]
  }

  class EvaluationCriterion {
    criterion_name: string
    weight: float                     // Relative importance in evaluation
    description: string
    scoring_approach: string
    optimization_strategies: string[]
  }

  class SuccessFactor {
    factor_name: string
    impact_level: ImpactLevel
    frequency_in_winners: float       // 0.0 to 1.0
    implementation_guidance: string
    measurement_approach: string
  }

  class OpportunityIndicator {
    indicator_type: string
    signal_strength: ConfidenceLevel
    description: string
    action_recommendations: string[]
  }

  class RiskFlag {
    risk_type: string
    severity: SeverityLevel
    description: string
    mitigation_strategies: string[]
  }

  class CompetitiveLandscape {
    competition_level: CompetitionLevel
    typical_competitors: string[]
    competitive_advantages: string[]
    differentiation_opportunities: string[]
  }

  class StrategyRecommendation {
    strategy_area: string
    recommendation: string
    implementation_steps: string[]
    expected_impact: ImpactLevel
    resource_requirements: string[]
  }

  class TimingInsight {
    timing_factor: string
    optimal_timing: string
    timing_rationale: string
    deadline_considerations: string[]
  }

  class PartnershipOpportunity {
    partner_type: string
    partnership_value: string
    identification_strategies: string[]
    engagement_approaches: string[]
  }

  enum PreferenceType {
    SECTOR_PREFERENCE
    GEOGRAPHIC_PREFERENCE
    ORGANIZATION_SIZE
    COLLABORATION_TYPE
    INNOVATION_LEVEL
    EVIDENCE_REQUIREMENTS
  }

  enum PatternType {
    AWARD_SIZE
    DURATION
    GEOGRAPHIC
    SECTOR
    COLLABORATION
    INNOVATION
  }

  enum RequirementType {
    ELIGIBILITY
    DOCUMENTATION
    MATCHING_FUNDS
    REPORTING
    COMPLIANCE
    COLLABORATION
  }

  enum ComplexityLevel {
    SIMPLE
    MODERATE
    COMPLEX
    VERY_COMPLEX
  }

  enum CompetitionLevel {
    LOW
    MODERATE
    HIGH
    VERY_HIGH
  }

  enum IntelligenceValue {
    LOW
    MODERATE
    HIGH
    CRITICAL
  }
}
```

### Pattern Detection Schema
```baml
function detect_funding_patterns {
  client GPT4o
  prompt #"
    Detect patterns and trends in funding data:

    Data scope: {{ data_scope }}
    Time period: {{ time_period }}
    Analysis dimensions: {{ analysis_dimensions }}
    Pattern types to detect: {{ pattern_types }}

    Identify significant patterns, trends, and anomalies that could
    inform funding strategy and timing decisions.
  "#

  response FundingPatterns {
    // Pattern summary
    pattern_summary: string
    significance_level: ConfidenceLevel

    // Temporal patterns
    seasonal_patterns: SeasonalPattern[]
    annual_trends: AnnualTrend[]
    cyclical_patterns: CyclicalPattern[]

    // Sector patterns
    sector_trends: SectorTrend[]
    emerging_sectors: EmergingSector[]
    declining_sectors: DecliningSector[]

    // Geographic patterns
    geographic_trends: GeographicTrend[]
    regional_preferences: RegionalPreference[]

    // Funding patterns
    amount_patterns: AmountPattern[]
    duration_patterns: DurationPattern[]
    success_rate_patterns: SuccessRatePattern[]

    // Competitive patterns
    competition_trends: CompetitionTrend[]
    applicant_patterns: ApplicantPattern[]

    // Predictive insights
    future_projections: FutureProjection[]
    opportunity_windows: OpportunityWindow[]

    // Recommendations
    strategic_implications: string[]
    timing_recommendations: TimingRecommendation[]

    // Metadata
    analysis_period: DateRange
    data_quality: DataQuality
    pattern_confidence: ConfidenceLevel
    update_frequency: string
  }

  class SeasonalPattern {
    season_name: string
    typical_activity_level: ActivityLevel
    funding_volume: float
    success_rates: float
    competitive_intensity: CompetitionLevel
    optimal_strategies: string[]
  }

  class AnnualTrend {
    trend_name: string
    trend_direction: TrendDirection
    magnitude: float                  // Percentage change
    duration: string
    drivers: string[]
    implications: string[]
  }

  class CyclicalPattern {
    cycle_name: string
    cycle_length: string
    phase_descriptions: CyclePhase[]
    current_phase: string
    next_phase_timing: string
  }

  class SectorTrend {
    sector: string
    trend_direction: TrendDirection
    growth_rate: float
    funding_volume_change: float
    key_drivers: string[]
    outlook: SectorOutlook
  }

  class EmergingSector {
    sector_name: string
    emergence_indicators: string[]
    growth_potential: float
    funding_availability: AvailabilityLevel
    entry_barriers: string[]
  }

  class AmountPattern {
    amount_category: string
    trend: TrendDirection
    typical_range: FundingRange
    growth_rate: float
    market_factors: string[]
  }

  class FutureProjection {
    projection_area: string
    timeframe: string
    projected_outcome: string
    confidence_level: ConfidenceLevel
    key_assumptions: string[]
    risk_factors: string[]
  }

  class OpportunityWindow {
    window_name: string
    start_timeframe: string
    duration: string
    opportunity_type: string
    preparation_requirements: string[]
    competitive_advantage_factors: string[]
  }

  class TimingRecommendation {
    recommendation_type: string
    optimal_timing: string
    rationale: string
    preparation_timeline: string
    success_probability: float
  }

  class CyclePhase {
    phase_name: string
    characteristics: string[]
    typical_duration: string
    strategic_recommendations: string[]
  }

  enum ActivityLevel {
    VERY_LOW
    LOW
    MODERATE
    HIGH
    VERY_HIGH
  }

  enum SectorOutlook {
    VERY_POSITIVE
    POSITIVE
    STABLE
    DECLINING
    UNCERTAIN
  }
}
```

---

## Human Interface Schemas

### Expert Validation Schema
```baml
function request_expert_validation {
  client Human
  prompt #"
    Expert validation required for grant research analysis:

    Organization: {{ organization_name }}
    Analysis type: {{ analysis_type }}

    ## Key Findings Requiring Validation
    {% for finding in key_findings %}
    **{{ finding.category }}**: {{ finding.description }}
    - AI Confidence: {{ finding.ai_confidence }}
    - Supporting evidence: {{ finding.evidence }}
    {% endfor %}

    ## Specific Questions for Expert Review
    {% for question in validation_questions %}
    {{ loop.index }}. {{ question.question }}
       Context: {{ question.context }}
    {% endfor %}

    ## Current AI Recommendation
    {{ ai_recommendation }}

    Please provide your expert assessment, corrections, and additional insights.
  "#

  response ExpertValidation {
    // Overall validation
    overall_approval: bool
    expert_confidence: float          // 0.0 to 1.0

    // Finding-by-finding validation
    finding_validations: FindingValidation[]

    // Corrections and improvements
    corrections: Correction[]
    additional_insights: AdditionalInsight[]

    // Recommendations
    revised_recommendation: string?
    implementation_guidance: string[]
    risk_mitigation_suggestions: string[]

    // Quality assessment
    analysis_quality_rating: QualityRating
    data_sufficiency: SufficiencyLevel
    methodology_appropriateness: AppropriateneLevel

    // Expert context
    expert_expertise_areas: string[]
    relevant_experience: string
    confidence_in_assessment: ConfidenceLevel

    // Follow-up
    requires_additional_analysis: bool
    suggested_next_steps: string[]
    consultation_recommendation: string?

    // Metadata
    validation_date: string
    review_duration_minutes: int
    validation_scope: string[]
  }

  class FindingValidation {
    finding_id: string
    finding_category: string
    validation_status: ValidationStatus
    accuracy_assessment: AccuracyLevel
    completeness_assessment: CompletenessLevel
    expert_notes: string
    suggested_revisions: string[]
  }

  class Correction {
    correction_type: CorrectionType
    field_or_section: string
    original_value: string
    corrected_value: string
    correction_rationale: string
    confidence_in_correction: ConfidenceLevel
    impact_on_overall_analysis: ImpactLevel
  }

  class AdditionalInsight {
    insight_category: string
    insight_description: string
    relevance_to_analysis: RelevanceLevel
    actionability: ActionabilityLevel
    source_of_insight: string
    implementation_suggestions: string[]
  }

  enum ValidationStatus {
    FULLY_VALIDATED
    PARTIALLY_VALIDATED
    REQUIRES_REVISION
    INCORRECT
    INSUFFICIENT_DATA
  }

  enum AccuracyLevel {
    HIGHLY_ACCURATE
    MOSTLY_ACCURATE
    PARTIALLY_ACCURATE
    INACCURATE
    CANNOT_ASSESS
  }

  enum CompletenessLevel {
    COMPREHENSIVE
    MOSTLY_COMPLETE
    PARTIALLY_COMPLETE
    INCOMPLETE
    MISSING_CRITICAL_ELEMENTS
  }

  enum CorrectionType {
    FACTUAL_ERROR
    ANALYTICAL_ERROR
    INTERPRETATION_ERROR
    OMISSION
    EMPHASIS_ADJUSTMENT
    METHODOLOGY_IMPROVEMENT
  }

  enum QualityRating {
    EXCELLENT
    GOOD
    SATISFACTORY
    NEEDS_IMPROVEMENT
    POOR
  }

  enum SufficiencyLevel {
    MORE_THAN_SUFFICIENT
    SUFFICIENT
    MARGINALLY_SUFFICIENT
    INSUFFICIENT
    CRITICALLY_INSUFFICIENT
  }

  enum AppropriateneLevel {
    HIGHLY_APPROPRIATE
    APPROPRIATE
    SOMEWHAT_APPROPRIATE
    INAPPROPRIATE
    CANNOT_ASSESS
  }

  enum RelevanceLevel {
    HIGHLY_RELEVANT
    RELEVANT
    SOMEWHAT_RELEVANT
    NOT_RELEVANT
  }

  enum ActionabilityLevel {
    IMMEDIATELY_ACTIONABLE
    ACTIONABLE_WITH_PLANNING
    REQUIRES_FURTHER_DEVELOPMENT
    NOT_ACTIONABLE
  }
}
```

---

## Output Generation Schemas

### Report Generation Schema
```baml
function generate_analysis_report {
  client GPT4o
  prompt #"
    Generate comprehensive analysis report:

    Report type: {{ report_type }}
    Target audience: {{ target_audience }}
    Organization: {{ organization }}
    Analysis results: {{ analysis_results }}

    Create a professional report with executive summary, detailed findings,
    recommendations, and supporting evidence. Tailor complexity and focus
    to the specified audience.
  "#

  response GeneratedReport {
    // Report metadata
    report_title: string
    report_type: ReportType
    organization_name: string
    report_date: string
    executive_summary: string

    // Main content sections
    sections: ReportSection[]

    // Key outcomes
    key_findings: KeyFinding[]
    recommendations: Recommendation[]

    // Supporting materials
    appendices: Appendix[]
    charts_and_tables: ChartReference[]

    // Quality and completeness
    completeness_score: float         // 0.0 to 1.0
    confidence_level: ConfidenceLevel
    data_quality_assessment: string

    // Usage guidance
    recommended_actions: ActionItem[]
    implementation_timeline: Timeline
    resource_requirements: string[]

    // Metadata
    word_count: int
    complexity_level: ComplexityLevel
    technical_depth: TechnicalDepth
    review_status: ReviewStatus
  }

  class ReportSection {
    section_number: int
    section_title: string
    section_content: string
    subsections: Subsection[]
    supporting_data: SupportingData[]
    key_takeaways: string[]
  }

  class KeyFinding {
    finding_number: int
    finding_title: string
    finding_description: string
    evidence: string[]
    implications: string[]
    confidence_level: ConfidenceLevel
    priority: PriorityLevel
  }

  class Recommendation {
    recommendation_id: string
    recommendation_title: string
    description: string
    rationale: string
    implementation_steps: string[]
    timeline: string
    resource_requirements: string[]
    expected_outcomes: string[]
    success_metrics: string[]
    priority: PriorityLevel
    difficulty: DifficultyLevel
  }

  class Appendix {
    appendix_letter: string
    title: string
    content_type: ContentType
    description: string
    content: string
  }

  class ChartReference {
    chart_id: string
    chart_title: string
    chart_type: ChartType
    data_source: string
    description: string
    insights: string[]
  }

  class ActionItem {
    action_description: string
    responsible_party: string
    deadline: string
    prerequisites: string[]
    deliverables: string[]
  }

  class Timeline {
    timeline_description: string
    phases: TimelinePhase[]
    critical_milestones: Milestone[]
    dependencies: string[]
  }

  class Subsection {
    subsection_title: string
    content: string
    data_references: string[]
  }

  class SupportingData {
    data_type: string
    description: string
    source: string
    reliability: ReliabilityLevel
  }

  class TimelinePhase {
    phase_name: string
    duration: string
    activities: string[]
    deliverables: string[]
  }

  class Milestone {
    milestone_name: string
    target_date: string
    success_criteria: string[]
    dependencies: string[]
  }

  enum ReportType {
    FINANCIAL_ANALYSIS
    RISK_ASSESSMENT
    COMPETITIVE_ANALYSIS
    OPPORTUNITY_ANALYSIS
    COMPREHENSIVE_ANALYSIS
    EXECUTIVE_BRIEFING
  }

  enum ContentType {
    TEXT
    TABLE
    CHART
    APPENDIX
    REFERENCE_MATERIAL
  }

  enum ChartType {
    BAR_CHART
    LINE_CHART
    PIE_CHART
    SCATTER_PLOT
    TABLE
    INFOGRAPHIC
  }

  enum TechnicalDepth {
    EXECUTIVE_LEVEL
    MANAGEMENT_LEVEL
    TECHNICAL_LEVEL
    DETAILED_ANALYSIS
  }

  enum ReviewStatus {
    DRAFT
    UNDER_REVIEW
    APPROVED
    FINAL
  }

  enum ReliabilityLevel {
    VERY_HIGH
    HIGH
    MODERATE
    LOW
    UNVERIFIED
  }
}
```

---

## Schema Composition Patterns

### Tool Chain Schemas
```baml
// Schema for chaining tool outputs
class ToolChainInput {
  previous_tool_output: object
  chain_context: ChainContext
  next_tool_requirements: string[]
}

class ChainContext {
  workflow_id: string
  current_step: int
  total_steps: int
  accumulated_confidence: float
  error_history: ChainError[]
}

class ChainError {
  step_number: int
  tool_name: string
  error_description: string
  recovery_action: string
  impact_on_chain: ImpactLevel
}
```

### Validation Schemas
```baml
// Schema for validating tool outputs
class OutputValidation {
  schema_compliance: bool
  data_quality_score: float
  completeness_percentage: float
  validation_errors: ValidationError[]
  recommendations: ValidationRecommendation[]
}

class ValidationError {
  field_name: string
  error_type: ValidationErrorType
  error_message: string
  suggested_fix: string
  severity: SeverityLevel
}

class ValidationRecommendation {
  recommendation_type: string
  description: string
  implementation_priority: PriorityLevel
  expected_improvement: float
}

enum ValidationErrorType {
  MISSING_REQUIRED_FIELD
  INVALID_DATA_TYPE
  OUT_OF_RANGE_VALUE
  INCONSISTENT_DATA
  MALFORMED_INPUT
}
```

## Schema Management

### Version Control
```baml
// Schema versioning pattern
class SchemaVersion {
  schema_name: string
  version: string          // Semantic versioning (e.g., "1.2.3")
  release_date: string
  changes: SchemaChange[]
  backward_compatible: bool
  migration_required: bool
}

class SchemaChange {
  change_type: ChangeType
  field_affected: string
  description: string
  impact_level: ImpactLevel
}

enum ChangeType {
  FIELD_ADDED
  FIELD_REMOVED
  FIELD_MODIFIED
  ENUM_VALUE_ADDED
  ENUM_VALUE_REMOVED
  TYPE_CHANGED
}
```

### Performance Optimization
```baml
// Schema optimization for token efficiency
class OptimizedSchema {
  base_schema: string
  optimizations: Optimization[]
  token_savings: int
  accuracy_impact: float
}

class Optimization {
  optimization_type: OptimizationType
  description: string
  token_reduction: int
  trade_off_description: string
}

enum OptimizationType {
  FIELD_CONSOLIDATION
  ENUM_SIMPLIFICATION
  DESCRIPTION_COMPRESSION
  CONDITIONAL_INCLUSION
  PRIORITY_BASED_FILTERING
}
```

---

## Implementation Guidelines

### Schema Development Process
1. **Requirements Analysis**: Define data needs and output requirements
2. **Schema Design**: Create initial BAML schema with comprehensive types
3. **Validation Testing**: Test schema with sample data and edge cases
4. **Performance Optimization**: Optimize for token efficiency while maintaining accuracy
5. **Documentation**: Document schema purpose, usage patterns, and examples
6. **Version Management**: Implement semantic versioning for schema evolution

### Best Practices
- **Consistent Naming**: Use clear, consistent naming conventions across all schemas
- **Comprehensive Enums**: Define enums for all categorical data to ensure consistency
- **Confidence Tracking**: Include confidence levels for all AI-generated assessments
- **Metadata Inclusion**: Always include relevant metadata for traceability
- **Error Handling**: Design schemas to capture and structure error information
- **Human Integration**: Include fields for human validation and feedback

### Testing Strategy
- **Schema Validation**: Ensure all schemas compile and validate correctly
- **Output Consistency**: Test that tools produce consistent outputs with same inputs
- **Edge Case Handling**: Test schemas with incomplete or unusual data
- **Performance Testing**: Measure token usage and response times
- **Integration Testing**: Validate schema compatibility across tool chains

---

**Next Steps**:
1. Review [WORKFLOWS.md](./WORKFLOWS.md) for tool composition and workflow patterns
2. Study [IMPLEMENTATION-PLAYBOOK.md](./IMPLEMENTATION-PLAYBOOK.md) for migration strategy
3. Examine [PROJECT-TEMPLATE.md](./PROJECT-TEMPLATE.md) for new project patterns