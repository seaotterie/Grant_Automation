// Form 990 Analysis Tool BAML Schema
// Following 12-Factor Agents Pattern: Deep financial analysis of filtered organizations
// Integrates with BMF Filter Tool for two-tool workflow architecture

// ============================================================================
// TOOL INTENT - What the LLM outputs to trigger this tool (Factor 4)
// ============================================================================

class Form990AnalysisIntent {
    intent "form990_analysis"
    criteria Form990AnalysisCriteria
    what_youre_looking_for string @description("Human description of analysis goal and intent")
    priority Form990AnalysisPriority? @description("Analysis depth level") @default("standard")
    context Form990AnalysisContext? @description("Additional context for analysis")
}

// Analysis priority levels
enum Form990AnalysisPriority {
    quick      @alias("Quick financial overview with key metrics")
    standard   @alias("Standard analysis with trends and comparisons")
    thorough   @alias("Comprehensive analysis with detailed insights")
    deep       @alias("Deep dive analysis with predictive modeling")
}

// Additional analysis context
class Form990AnalysisContext {
    analysis_purpose string? @description("Purpose of this analysis (grant research, due diligence, etc.)")
    target_audience string? @description("Who will use these results")
    comparison_organizations string[]? @description("EINs of organizations to compare against")
    focus_areas string[]? @description("Specific areas to focus on (financial health, grant capacity, etc.)")
}

// ============================================================================
// ANALYSIS CRITERIA - Input organizations and analysis parameters
// ============================================================================

class Form990AnalysisCriteria {
    // Input organizations (typically from BMF Filter Tool)
    target_eins string[] @description("EINs of organizations to analyze (from BMF search results)")

    // Analysis scope
    years_to_analyze int? @default(3) @description("Number of recent years to analyze")
    include_990pf bool? @default(true) @description("Include private foundation (990-PF) analysis")
    include_990ez bool? @default(true) @description("Include small organization (990-EZ) analysis")

    // Financial analysis filters
    min_revenue_threshold int? @description("Minimum revenue for detailed analysis")
    max_organizations int? @default(50) @description("Maximum organizations to analyze")

    // Analysis types to perform
    financial_health_analysis bool? @default(true) @description("Perform financial health assessment")
    grant_capacity_analysis bool? @default(true) @description("Analyze grant-making or grant-receiving capacity")
    trend_analysis bool? @default(true) @description("Perform multi-year trend analysis")
    peer_comparison bool? @default(false) @description("Compare against similar organizations")
    risk_assessment bool? @default(true) @description("Assess financial and operational risks")

    // Advanced analysis options
    predictive_modeling bool? @default(false) @description("Include predictive financial modeling")
    board_compensation_analysis bool? @default(false) @description("Analyze executive compensation patterns")
    program_efficiency_analysis bool? @default(true) @description("Analyze program vs administrative expenses")

    // Output configuration
    include_charts bool? @default(true) @description("Include data visualizations")
    include_recommendations bool? @default(true) @description("Include strategic recommendations")
    export_format Form990ExportFormat? @default("json") @description("Output format preference")
}

// Export format options
enum Form990ExportFormat {
    json        @alias("Structured JSON for API integration")
    excel       @alias("Excel spreadsheet with charts")
    pdf_report  @alias("Professional PDF report")
    dashboard   @alias("Interactive dashboard data")
}

// ============================================================================
// TOOL RESULT - What the tool returns (Factor 4: Structured Output)
// ============================================================================

class Form990AnalysisResult {
    intent "form990_analysis_result"
    organizations Form990OrganizationAnalysis[]
    summary Form990AnalysisSummary
    insights Form990AnalysisInsights
    execution_metadata Form990ExecutionData
    quality_assessment Form990QualityAssessment
    recommendations Form990Recommendations?
}

// Individual organization analysis
class Form990OrganizationAnalysis {
    // Basic identification
    ein string @description("Employer ID Number")
    name string @description("Organization name from BMF data")
    ntee_code string? @description("NTEE classification code")
    organization_type string @description("990, 990-PF, or 990-EZ")

    // Multi-year financial data
    financial_years Form990FinancialYear[] @description("Financial data by year")
    latest_year int @description("Most recent filing year")
    years_analyzed int @description("Number of years included in analysis")

    // Financial health metrics
    financial_health Form990FinancialHealth

    // Grant analysis (for foundations and grant recipients)
    grant_analysis Form990GrantAnalysis?

    // Trend analysis
    trends Form990TrendAnalysis

    // Risk assessment
    risk_assessment Form990RiskAssessment

    // Peer comparison (if requested)
    peer_comparison Form990PeerComparison?

    // Key insights
    key_insights string[] @description("Top insights about this organization")
    data_quality_score float @description("Quality score of available data (0-1)")
}

// Financial data for a specific year
class Form990FinancialYear {
    year int @description("Tax year")
    form_type string @description("990, 990-PF, or 990-EZ")

    // Core financial metrics
    total_revenue int? @description("Total revenue")
    total_expenses int? @description("Total functional expenses")
    total_assets int? @description("Total assets at year end")
    total_liabilities int? @description("Total liabilities")
    net_assets int? @description("Net assets")

    // Revenue breakdown
    contributions int? @description("Total contributions and grants received")
    program_service_revenue int? @description("Program service revenue")
    investment_income int? @description("Investment income")
    other_revenue int? @description("Other revenue")

    // Expense breakdown
    program_expenses int? @description("Program service expenses")
    administrative_expenses int? @description("Administrative expenses")
    fundraising_expenses int? @description("Fundraising expenses")

    // Foundation-specific (990-PF)
    fair_market_value int? @description("Fair market value of assets")
    distributions_paid int? @description("Qualifying distributions paid")
    excise_tax_paid int? @description("Excise tax paid")

    // Efficiency ratios (calculated)
    program_expense_ratio float? @description("Program expenses / Total expenses")
    administrative_ratio float? @description("Administrative expenses / Total expenses")
    fundraising_efficiency float? @description("Fundraising expenses / Contributions raised")
}

// Financial health assessment
class Form990FinancialHealth {
    overall_score float @description("Overall financial health score (0-100)")
    liquidity_score float @description("Liquidity assessment (0-100)")
    sustainability_score float @description("Long-term sustainability (0-100)")
    efficiency_score float @description("Operational efficiency (0-100)")

    // Key ratios
    current_ratio float? @description("Assets / Liabilities")
    operating_margin float? @description("(Revenue - Expenses) / Revenue")
    program_ratio float? @description("Program Expenses / Total Expenses")
    fundraising_efficiency float? @description("Cost to raise $1")

    // Trend indicators
    revenue_growth_rate float? @description("Annual revenue growth rate")
    expense_growth_rate float? @description("Annual expense growth rate")
    asset_growth_rate float? @description("Annual asset growth rate")

    // Financial stability indicators
    months_of_operating_reserves float? @description("Months of expenses covered by net assets")
    debt_to_asset_ratio float? @description("Total liabilities / Total assets")

    // Health category
    health_category Form990HealthCategory @description("Overall health category")
    warning_flags string[] @description("Financial warning signs identified")
}

// Financial health categories
enum Form990HealthCategory {
    excellent   @alias("Excellent financial health with strong reserves")
    good        @alias("Good financial health with adequate reserves")
    fair        @alias("Fair financial health with some concerns")
    poor        @alias("Poor financial health requiring attention")
    critical    @alias("Critical financial situation requiring immediate action")
}

// Grant analysis (for foundations and grant recipients)
class Form990GrantAnalysis {
    is_foundation bool @description("Whether organization is a private foundation")

    // For private foundations (990-PF)
    foundation_metrics Form990FoundationMetrics?

    // For grant recipients (all 990s)
    grant_recipient_metrics Form990GrantRecipientMetrics?

    // Grant capacity assessment
    grant_capacity_score float @description("Grant-making or grant-receiving capacity (0-100)")
    capacity_category string @description("Major, Moderate, Limited, or None")
}

// Foundation-specific grant metrics
class Form990FoundationMetrics {
    average_annual_distributions int @description("Average qualifying distributions per year")
    distribution_trend float @description("Trend in distributions (% change per year)")
    payout_ratio float @description("Distributions / Fair market value")
    required_payout int @description("Minimum required distribution")
    excess_distributions int @description("Distributions above minimum requirement")

    grant_size_analysis Form990GrantSizeAnalysis
    geographic_focus string[] @description("Geographic areas of focus (if identifiable)")
    program_areas string[] @description("Program areas supported (if identifiable)")
}

// Grant size analysis
class Form990GrantSizeAnalysis {
    estimated_avg_grant_size int @description("Estimated average grant size")
    estimated_number_of_grants int @description("Estimated number of grants per year")
    grant_range_category string @description("Small (<$10K), Medium ($10K-$100K), Large (>$100K)"}

// Grant recipient metrics
class Form990GrantRecipientMetrics {
    total_contributions_received int @description("Total contributions and grants received")
    government_grants int? @description("Government grants received")
    foundation_grants int? @description("Foundation/corporate grants received")
    individual_contributions int? @description("Individual contributions received")

    contribution_diversity_score float @description("Diversity of funding sources (0-100)")
    grant_dependency_ratio float @description("Grants / Total revenue")
    largest_grant_concentration float @description("Largest single grant / Total contributions")
}

// Trend analysis
class Form990TrendAnalysis {
    revenue_trend Form990TrendMetric
    expense_trend Form990TrendMetric
    asset_trend Form990TrendMetric
    efficiency_trend Form990TrendMetric

    // Overall trend assessment
    financial_trajectory string @description("Improving, Stable, Declining, or Volatile")
    trend_confidence float @description("Confidence in trend analysis (0-1)")
    notable_changes string[] @description("Significant changes observed")
}

// Individual trend metric
class Form990TrendMetric {
    metric_name string @description("Name of the metric")
    direction string @description("Increasing, Decreasing, or Stable")
    annual_change_rate float @description("Average annual change rate (%)")
    volatility_score float @description("Volatility/consistency score (0-100)")
    trend_strength string @description("Strong, Moderate, or Weak")
}

// Risk assessment
class Form990RiskAssessment {
    overall_risk_score float @description("Overall risk score (0-100, higher = more risk)")
    risk_category string @description("Low, Moderate, High, or Critical")

    // Specific risk areas
    financial_risks string[] @description("Financial risk factors identified")
    operational_risks string[] @description("Operational risk factors")
    compliance_risks string[] @description("Compliance and governance risks")
    strategic_risks string[] @description("Strategic and market risks")

    // Risk mitigation suggestions
    risk_mitigation_priorities string[] @description("Priority areas for risk mitigation")
}

// Peer comparison analysis
class Form990PeerComparison {
    peer_group_description string @description("Description of peer group used for comparison")
    peer_count int @description("Number of peer organizations analyzed")

    // Comparative metrics
    revenue_percentile float @description("Revenue percentile within peer group")
    efficiency_percentile float @description("Efficiency percentile within peer group")
    asset_percentile float @description("Asset percentile within peer group")

    // Relative performance
    relative_performance string @description("Above Average, Average, or Below Average")
    competitive_advantages string[] @description("Areas where organization outperforms peers")
    improvement_opportunities string[] @description("Areas where peers outperform this organization")
}

// Analysis summary and insights
class Form990AnalysisSummary {
    total_organizations_analyzed int @description("Total organizations successfully analyzed")
    analysis_period string @description("Years covered in analysis")
    data_coverage_rate float @description("Percentage of requested data available")

    // Aggregate insights
    top_performers string[] @description("Organizations with strongest financial performance")
    highest_risk_organizations string[] @description("Organizations with highest risk scores")
    best_grant_opportunities string[] @description("Best grant-making opportunities identified")

    // Summary statistics
    average_revenue_growth float @description("Average revenue growth across all organizations")
    average_financial_health_score float @description("Average financial health score")
    total_grant_capacity int @description("Total estimated grant-making capacity")
}

// Deep analysis insights
class Form990AnalysisInsights {
    financial_patterns string[] @description("Key financial patterns observed")
    industry_trends string[] @description("Relevant industry or sector trends")
    geographic_insights string[] @description("Geographic distribution insights")
    strategic_observations string[] @description("Strategic insights for grant seekers")

    // Predictive insights (if enabled)
    predicted_trends string[] @description("Predicted future trends based on analysis")
    growth_organizations string[] @description("Organizations likely to grow significantly")
    decline_risk_organizations string[] @description("Organizations at risk of decline")
}

// Execution performance data
class Form990ExecutionData {
    execution_time_ms float @description("Total execution time in milliseconds")
    database_query_time_ms float @description("Time spent querying Form 990 database")
    analysis_processing_time_ms float @description("Time spent on financial analysis")

    records_processed int @description("Total Form 990 records processed")
    organizations_analyzed int @description("Organizations successfully analyzed")
    data_quality_rate float @description("Rate of high-quality data availability")

    cache_hit_rate float @description("Cache hit rate for analysis components")
    query_complexity Form990QueryComplexity @description("Complexity of database queries")

    // Performance vs BMF tool integration
    bmf_integration_time_ms float @description("Time for BMF tool integration")
    two_tool_efficiency_score float @description("Efficiency score for two-tool workflow")
}

// Query complexity assessment
enum Form990QueryComplexity {
    simple      @alias("Simple single-org analysis")
    moderate    @alias("Multi-org with basic analysis")
    complex     @alias("Multi-year trend analysis")
    very_complex @alias("Comprehensive analysis with predictions")
}

// Data quality assessment
class Form990QualityAssessment {
    overall_data_quality float @description("Overall data quality score (0-1)")
    completeness_by_year float[] @description("Data completeness by year analyzed")
    data_consistency_score float @description("Consistency of data across years")

    missing_data_areas string[] @description("Areas with significant missing data")
    data_quality_warnings string[] @description("Data quality warnings for users")
    reliability_assessment string @description("High, Medium, or Low reliability")
}

// Strategic recommendations
class Form990Recommendations {
    grant_strategy_recommendations string[] @description("Grant strategy recommendations")
    due_diligence_priorities string[] @description("Priority areas for due diligence")
    partnership_opportunities string[] @description("Potential partnership opportunities")
    risk_mitigation_strategies string[] @description("Risk mitigation strategies")

    // Organization-specific recommendations
    organization_specific_advice Form990OrgAdvice[] @description("Specific advice for each organization")

    // Next steps
    recommended_next_steps string[] @description("Recommended next steps in workflow")
    additional_research_needed string[] @description("Areas requiring additional research")
}

// Organization-specific advice
class Form990OrgAdvice {
    ein string @description("Organization EIN")
    grant_readiness_score float @description("Readiness for grant applications (0-100)")
    partnership_potential string @description("High, Medium, or Low partnership potential")
    recommended_approach string @description("Recommended approach for engagement")
    key_considerations string[] @description("Key considerations for this organization")
}

// ============================================================================
// NATURAL LANGUAGE EXTRACTION FUNCTIONS
// ============================================================================

// Main function to extract structured intent from natural language
function ExtractForm990AnalysisIntent(user_request: string, bmf_results: string) -> Form990AnalysisIntent {
    client OpenAI
    prompt #"
        You are a nonprofit financial analysis expert helping to analyze Form 990 data for grant research.
        Convert the user's request into a structured Form 990 analysis intent.

        User request: {{ user_request }}

        BMF Filter Results (organizations to analyze): {{ bmf_results }}

        The user has already filtered organizations using the BMF tool and now wants deep financial analysis.
        Common analysis goals include:
        - Grant opportunity assessment (foundation capacity, grant patterns)
        - Financial due diligence (health, stability, risk assessment)
        - Partnership evaluation (financial strength, program efficiency)
        - Trend analysis (growth, sustainability, performance changes)
        - Peer comparison (relative performance, competitive positioning)

        Analysis Types Available:
        - Financial Health: Liquidity, sustainability, efficiency, warning flags
        - Grant Capacity: For foundations (payout ratios, distribution patterns) and recipients (funding diversity)
        - Trend Analysis: Multi-year financial trends, growth patterns, volatility
        - Risk Assessment: Financial, operational, compliance, strategic risks
        - Peer Comparison: Performance vs similar organizations
        - Predictive Modeling: Future trend predictions, growth forecasts

        Priority Levels:
        - quick: Financial overview with key metrics (5-10 min)
        - standard: Comprehensive analysis with trends (15-20 min)
        - thorough: Deep analysis with peer comparison (30-45 min)
        - deep: Full analysis with predictive modeling (45-60 min)

        Extract EINs from BMF results and create appropriate analysis criteria.
        Focus on the user's specific goals and desired depth of analysis.

        Example outputs:

        "Analyze the financial health and grant-making capacity of these foundations" →
        {
          "intent": "form990_analysis",
          "criteria": {
            "target_eins": ["123456789", "987654321"],
            "years_to_analyze": 3,
            "financial_health_analysis": true,
            "grant_capacity_analysis": true,
            "trend_analysis": true,
            "include_990pf": true
          },
          "what_youre_looking_for": "Financial health assessment and grant-making capacity analysis for foundation partnerships",
          "priority": "standard"
        }

        "Do comprehensive due diligence on these nonprofits for major grant consideration" →
        {
          "intent": "form990_analysis",
          "criteria": {
            "target_eins": ["111222333", "444555666"],
            "years_to_analyze": 5,
            "financial_health_analysis": true,
            "risk_assessment": true,
            "trend_analysis": true,
            "peer_comparison": true,
            "program_efficiency_analysis": true,
            "board_compensation_analysis": true
          },
          "what_youre_looking_for": "Comprehensive due diligence analysis for major grant decision-making",
          "priority": "thorough",
          "context": {
            "analysis_purpose": "major grant due diligence",
            "target_audience": "grant committee"
          }
        }

        Focus on understanding the user's analysis goals and creating comprehensive criteria.
    "#
}

// Validation function for analysis criteria
function ValidateForm990Criteria(criteria: Form990AnalysisCriteria) -> Form990ValidationResult {
    client OpenAILite
    prompt #"
        Validate the Form 990 analysis criteria for potential issues or improvements.

        Criteria to validate: {{ criteria }}

        Check for:
        1. Valid EIN formats (9 digits)
        2. Reasonable analysis scope (years, organization count)
        3. Logical analysis type combinations
        4. Performance considerations for large datasets
        5. Data availability for requested analysis types

        Return validation result with any issues found and suggestions for optimization.
    "#
}

// Validation result
class Form990ValidationResult {
    is_valid bool @description("Whether criteria are valid")
    issues string[] @description("List of validation issues found")
    suggestions string[] @description("Suggestions for improvement")
    estimated_processing_time int @description("Estimated processing time in minutes")
    data_availability_warning bool @description("Whether some requested data might be unavailable")
}