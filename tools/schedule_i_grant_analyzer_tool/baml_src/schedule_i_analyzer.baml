// BAML Schema for Schedule I Grant Analyzer Tool
// Foundation grant-making pattern analysis

enum GrantCategory {
  education
  health
  arts_culture
  environment
  human_services
  international
  research
  other
}

class ScheduleIGrantAnalyzerInput {
  foundation_ein string
  foundation_name string
  grants map<string, any>[] @description("List of grants from Schedule I")
  tax_year int
  analyzing_organization_ein string?
  analyzing_organization_name string?
  analyzing_organization_mission string?
  analyzing_organization_location string?
}

class ScheduleIGrantAnalyzerOutput {
  foundation_ein string
  foundation_name string
  tax_year int
  total_grants int
  total_amount float
  granting_patterns string @description("Summary of grant-making patterns")
  foundation_intelligence string @description("Strategic intelligence about foundation")
  match_analysis string? @description("Match analysis if organization provided")
  data_quality_score float
  confidence_level float
}

function AnalyzeScheduleIGrants(input: ScheduleIGrantAnalyzerInput) -> ScheduleIGrantAnalyzerOutput {
  client GPT4o

  prompt #"
    Analyze the grant-making patterns for {{ input.foundation_name }}.

    Total grants provided: {{ input.grants | length }}

    Provide comprehensive analysis of granting patterns, foundation intelligence, and strategic insights.
  "#
}
