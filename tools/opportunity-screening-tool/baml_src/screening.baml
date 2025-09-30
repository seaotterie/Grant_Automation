// BAML Schema for Opportunity Screening Tool
// Factor 4: Structured outputs eliminate parsing errors

enum ScreeningMode {
  FAST
  THOROUGH
}

enum ConfidenceLevel {
  HIGH
  MEDIUM
  LOW
}

enum FunderType {
  FOUNDATION
  GOVERNMENT
  CORPORATE
}

// Input Types

class OrganizationProfile {
  ein string
  name string
  mission string
  ntee_codes string[]
  geographic_focus string[]
  program_areas string[]
  annual_revenue float?
  staff_count int?
  years_established int?
}

class Opportunity {
  opportunity_id string
  title string
  funder string
  funder_type FunderType
  description string

  // Financial
  amount_min float?
  amount_max float?
  typical_award_size float?

  // Timing
  deadline string?
  award_date string?
  project_duration_months int?

  // Eligibility
  geographic_restrictions string[]
  ntee_requirements string[]
  revenue_requirements string?

  // Additional
  focus_areas string[]
  past_recipients string[]
  application_requirements string[]
}

class ScreeningInput {
  opportunities Opportunity[]
  organization_profile OrganizationProfile
  screening_mode ScreeningMode
  minimum_threshold float
  max_recommendations int
}

// Output Types

class OpportunityScore {
  opportunity_id string
  opportunity_title string

  // Overall Assessment
  overall_score float
  proceed_to_deep_analysis bool
  confidence_level ConfidenceLevel

  // Dimensional Scores (0.0 - 1.0)
  strategic_fit_score float
  eligibility_score float
  timing_score float
  financial_score float
  competition_score float

  // Analysis
  one_sentence_summary string
  key_strengths string[]
  key_concerns string[]
  risk_factors string[]

  // Recommendations
  recommended_actions string[]
  estimated_effort_hours int?

  // Metadata
  analysis_depth string
}

class ScreeningOutput {
  // Summary Statistics
  total_screened int
  passed_threshold int
  recommended_for_deep_analysis string[]

  // Detailed Scores
  opportunity_scores OpportunityScore[]

  // Analysis Metadata
  screening_mode string
  threshold_used float
  processing_time_seconds float
  total_cost_usd float

  // Execution Context
  timestamp string
  tool_version string

  // Quality Metrics
  avg_confidence_level string?
  high_confidence_count int
}

// AI Functions for Screening

function ScreenOpportunityFast(
  opportunity: Opportunity,
  organization: OrganizationProfile
) -> OpportunityScore {
  client GPT4o
  prompt #"
    You are an expert grant researcher analyzing opportunity fit.

    SCREENING MODE: FAST (Quick Assessment)
    - Focus: Strategic fit and basic eligibility
    - Analysis Depth: High-level match assessment
    - Time Budget: 2 seconds

    ORGANIZATION PROFILE:
    Name: {{ organization.name }}
    Mission: {{ organization.mission }}
    NTEE Codes: {{ organization.ntee_codes }}
    Geographic Focus: {{ organization.geographic_focus }}
    Program Areas: {{ organization.program_areas }}

    OPPORTUNITY TO SCREEN:
    Title: {{ opportunity.title }}
    Funder: {{ opportunity.funder }}
    Description: {{ opportunity.description }}
    Amount: ${{ opportunity.amount_min }} - ${{ opportunity.amount_max }}
    Deadline: {{ opportunity.deadline }}
    Geographic Restrictions: {{ opportunity.geographic_restrictions }}
    Focus Areas: {{ opportunity.focus_areas }}

    SCORING INSTRUCTIONS:
    1. Strategic Fit (0.0-1.0): How well does this align with mission/programs?
    2. Eligibility (0.0-1.0): Does organization meet basic requirements?
    3. Timing (0.0-1.0): Is deadline feasible?

    Overall Score = (strategic_fit * 0.50) + (eligibility * 0.30) + (timing * 0.20)

    Proceed to deep analysis if overall_score >= 0.55 AND eligibility >= 0.70

    Provide:
    - Dimensional scores
    - One sentence summary of fit
    - 2-3 key strengths
    - 2-3 key concerns
    - Recommended actions if pursuing
  "#
}

function ScreenOpportunityThorough(
  opportunity: Opportunity,
  organization: OrganizationProfile
) -> OpportunityScore {
  client GPT4o
  prompt #"
    You are an expert grant researcher performing comprehensive opportunity analysis.

    SCREENING MODE: THOROUGH (Comprehensive Assessment)
    - Focus: Multi-dimensional strategic analysis
    - Analysis Depth: Detailed evaluation across all dimensions
    - Time Budget: 5 seconds

    ORGANIZATION PROFILE:
    Name: {{ organization.name }}
    Mission: {{ organization.mission }}
    NTEE Codes: {{ organization.ntee_codes }}
    Geographic Focus: {{ organization.geographic_focus }}
    Program Areas: {{ organization.program_areas }}
    Annual Revenue: ${{ organization.annual_revenue }}
    Staff Count: {{ organization.staff_count }}
    Years Established: {{ organization.years_established }}

    OPPORTUNITY TO SCREEN:
    Title: {{ opportunity.title }}
    Funder: {{ opportunity.funder }} ({{ opportunity.funder_type }})
    Description: {{ opportunity.description }}

    FINANCIAL:
    Amount Range: ${{ opportunity.amount_min }} - ${{ opportunity.amount_max }}
    Typical Award: ${{ opportunity.typical_award_size }}

    TIMING:
    Deadline: {{ opportunity.deadline }}
    Award Date: {{ opportunity.award_date }}
    Project Duration: {{ opportunity.project_duration_months }} months

    ELIGIBILITY:
    Geographic: {{ opportunity.geographic_restrictions }}
    NTEE Requirements: {{ opportunity.ntee_requirements }}
    Revenue Requirements: {{ opportunity.revenue_requirements }}

    CONTEXT:
    Focus Areas: {{ opportunity.focus_areas }}
    Past Recipients: {{ opportunity.past_recipients }}
    Application Requirements: {{ opportunity.application_requirements }}

    COMPREHENSIVE SCORING INSTRUCTIONS:

    1. Strategic Fit (0.0-1.0):
       - Mission alignment
       - Program area match
       - Geographic alignment
       - Organizational capacity fit

    2. Eligibility (0.0-1.0):
       - Hard requirements compliance
       - NTEE code match
       - Revenue/size requirements
       - Geographic eligibility

    3. Timing (0.0-1.0):
       - Deadline feasibility
       - Award timing fit
       - Project duration alignment

    4. Financial (0.0-1.0):
       - Award size appropriateness
       - Budget capacity match
       - ROI potential

    5. Competition (0.0-1.0):
       - Competitive positioning
       - Past recipient analysis
       - Unique value proposition

    Overall Score = (strategic_fit * 0.35) + (eligibility * 0.25) +
                    (timing * 0.15) + (financial * 0.15) + (competition * 0.10)

    Proceed to deep analysis if:
    - overall_score >= 0.60
    - eligibility >= 0.75
    - No critical risk factors

    Confidence Level:
    - HIGH: Strong fit, clear eligibility, minimal concerns
    - MEDIUM: Good fit with some questions or moderate concerns
    - LOW: Marginal fit, significant concerns, or insufficient data

    Provide comprehensive analysis:
    - All dimensional scores with reasoning
    - Detailed one-sentence summary
    - 3-5 key strengths (be specific)
    - 3-5 key concerns (identify risks)
    - Risk factors (deal-breakers or major obstacles)
    - Recommended actions with estimated effort
  "#
}

function BatchScreenOpportunities(
  input: ScreeningInput
) -> ScreeningOutput {
  client GPT4o
  prompt #"
    You are screening {{ input.opportunities.length }} opportunities for {{ input.organization_profile.name }}.

    Mode: {{ input.screening_mode }}
    Threshold: {{ input.minimum_threshold }}
    Max Recommendations: {{ input.max_recommendations }}

    For each opportunity, perform screening analysis and return structured results.
    Rank by overall_score and recommend top opportunities above threshold.
  "#
}
