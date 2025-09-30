// BAML Schema for Financial Intelligence Tool
// Comprehensive financial analysis with AI-enhanced insights

class FinancialIntelligenceInput {
  // Organization identification
  organization_ein string
  organization_name string

  // Financial data (from 990)
  total_revenue float
  total_expenses float
  total_assets float
  total_liabilities float
  net_assets float

  // Revenue breakdown
  contributions_grants float
  program_service_revenue float
  investment_income float
  other_revenue float

  // Expense breakdown
  program_expenses float
  admin_expenses float
  fundraising_expenses float

  // Historical data (optional)
  prior_year_revenue float?
  prior_year_expenses float?
  prior_year_net_assets float?

  // Context for AI analysis
  organization_mission string?
  ntee_code string?
  years_of_operation int?
}

class FinancialMetrics {
  // Liquidity metrics
  current_ratio float
  months_of_expenses float
  liquid_assets_ratio float

  // Efficiency metrics
  program_expense_ratio float
  admin_expense_ratio float
  fundraising_expense_ratio float
  fundraising_efficiency float

  // Sustainability metrics
  revenue_growth_rate float?
  expense_growth_rate float?
  net_assets_growth_rate float?
  operating_margin float

  // Diversification metrics
  revenue_concentration_score float
  largest_revenue_source_pct float

  // Capacity metrics
  asset_to_revenue_ratio float
  debt_to_asset_ratio float
}

class FinancialStrength {
  strength_category string @description("Category: Liquidity, Efficiency, Growth, Stability")
  description string @description("Detailed explanation of this strength")
  metric_value float
  metric_name string
  percentile float? @description("Percentile rank compared to peers")
}

class FinancialConcern {
  concern_category string @description("Category: Liquidity, Efficiency, Sustainability, Risk")
  description string @description("Detailed explanation of this concern")
  severity string @description("Severity level: low, medium, high, critical")
  metric_value float
  metric_name string
  recommendation string @description("Specific recommendation to address this concern")
}

enum TrendDirection {
  strongly_positive
  positive
  stable
  negative
  strongly_negative
}

class TrendAnalysis {
  metric_name string
  direction TrendDirection
  percentage_change float
  interpretation string @description("Explanation of what this trend means")
  forecast string? @description("AI-generated forecast for this metric")
}

class GrantCapacityAssessment {
  // Financial capacity
  can_handle_budget float @description("Maximum grant size recommended in USD")
  budget_capacity_score float @description("Score 0-1 indicating budget management capacity")
  budget_capacity_reasoning string

  // Administrative capacity
  admin_capacity_score float @description("Score 0-1 indicating administrative capacity")
  admin_capacity_concerns string[] @description("List of administrative capacity concerns")

  // Sustainability indicators
  sustainability_score float @description("Score 0-1 indicating long-term sustainability")
  sustainability_concerns string[] @description("List of sustainability concerns")

  // Match requirement capability
  can_provide_match bool @description("Can organization provide matching funds?")
  max_match_percentage float @description("Maximum match percentage organization can handle")
  match_source_suggestions string[] @description("Suggested sources for match funding")
}

class AIFinancialInsights {
  // Executive summary
  executive_summary string @description("2-3 paragraph executive summary of financial health")

  // Strategic insights
  strategic_opportunities string[] @description("Financial opportunities to leverage")
  strategic_risks string[] @description("Financial risks to mitigate")

  // Competitive positioning
  competitive_advantages string[] @description("Financial advantages over peers")
  competitive_weaknesses string[] @description("Financial weaknesses vs peers")

  // Recommendations
  financial_management_recommendations string[] @description("Recommendations for financial management")
  grant_strategy_recommendations string[] @description("Recommendations for grant strategy")

  // Industry context
  industry_comparison string? @description("Comparison to industry standards")
  peer_benchmarking_insights string? @description("Insights from peer benchmarking")
}

enum FinancialHealthRating {
  excellent
  good
  fair
  concerning
  critical
}

class FinancialIntelligenceOutput {
  // Core metrics
  metrics FinancialMetrics

  // Overall assessment
  overall_health_rating FinancialHealthRating
  overall_health_score float @description("Score 0-1 indicating overall financial health")

  // Strengths and concerns
  strengths FinancialStrength[] @description("3-5 key financial strengths")
  concerns FinancialConcern[] @description("Key financial concerns to address")

  // Trend analysis
  trends TrendAnalysis[] @description("Analysis of financial trends over time")

  // Grant capacity
  grant_capacity GrantCapacityAssessment

  // AI insights
  ai_insights AIFinancialInsights

  // Metadata
  data_quality_score float @description("Score 0-1 based on data completeness")
  confidence_level float @description("Score 0-1 indicating AI confidence in analysis")
}

// AI function for comprehensive financial analysis
function AnalyzeFinancialIntelligence(input: FinancialIntelligenceInput) -> FinancialIntelligenceOutput {
  client GPT4o

  prompt #"
    You are an expert financial analyst specializing in nonprofit financial health assessment.

    Analyze the financial data for {{ input.organization_name }} (EIN: {{ input.organization_ein }}).

    FINANCIAL DATA:
    - Total Revenue: ${{ input.total_revenue }}
    - Total Expenses: ${{ input.total_expenses }}
    - Total Assets: ${{ input.total_assets }}
    - Total Liabilities: ${{ input.total_liabilities }}
    - Net Assets: ${{ input.net_assets }}

    REVENUE BREAKDOWN:
    - Contributions/Grants: ${{ input.contributions_grants }}
    - Program Service Revenue: ${{ input.program_service_revenue }}
    - Investment Income: ${{ input.investment_income }}
    - Other Revenue: ${{ input.other_revenue }}

    EXPENSE BREAKDOWN:
    - Program Expenses: ${{ input.program_expenses }}
    - Administrative Expenses: ${{ input.admin_expenses }}
    - Fundraising Expenses: ${{ input.fundraising_expenses }}

    {% if input.prior_year_revenue %}
    HISTORICAL DATA:
    - Prior Year Revenue: ${{ input.prior_year_revenue }}
    - Prior Year Expenses: ${{ input.prior_year_expenses }}
    - Prior Year Net Assets: ${{ input.prior_year_net_assets }}
    {% endif %}

    {% if input.organization_mission %}
    CONTEXT:
    - Mission: {{ input.organization_mission }}
    - NTEE Code: {{ input.ntee_code }}
    - Years of Operation: {{ input.years_of_operation }}
    {% endif %}

    Provide a comprehensive financial intelligence analysis including:

    1. FINANCIAL METRICS:
       - Calculate ALL metrics accurately based on the data provided
       - Use standard nonprofit financial ratio formulas
       - Include trend calculations if historical data available

    2. FINANCIAL HEALTH ASSESSMENT:
       - Rate overall health (excellent, good, fair, concerning, critical)
       - Provide health score (0-1) based on comprehensive analysis

    3. STRENGTHS & CONCERNS:
       - Identify 3-5 key financial strengths with specific metrics
       - List concerns with severity levels and recommendations

    4. TREND ANALYSIS (if historical data available):
       - Analyze revenue, expense, and net asset trends
       - Provide interpretation and forecasts

    5. GRANT CAPACITY ASSESSMENT:
       - Assess budget management capacity
       - Determine maximum grant size organization can handle
       - Evaluate match requirement capability
       - Identify sustainability concerns

    6. AI INSIGHTS:
       - Executive summary (2-3 paragraphs)
       - Strategic opportunities and risks
       - Competitive advantages and weaknesses
       - Financial management and grant strategy recommendations
       - Industry comparison if NTEE code provided

    Be thorough, data-driven, and provide actionable insights.
  "#
}
