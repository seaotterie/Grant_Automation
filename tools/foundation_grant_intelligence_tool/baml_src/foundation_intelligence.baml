// Foundation Grant Intelligence Tool - BAML Schema
// Human Layer 12-Factor Agents Framework - Factor 4: Tools as Structured Outputs

// Input: Criteria for foundation grant intelligence analysis
class FoundationAnalysisCriteria {
    target_eins string[]                  // List of EINs to analyze (pre-filtered to 990-PF forms)
    years_to_analyze int                  // Number of years to analyze for trends
    include_investment_analysis bool      // Whether to analyze investment portfolios
    include_payout_requirements bool      // Whether to calculate payout requirements
    include_grant_capacity_scoring bool   // Whether to score grant-making capacity
    min_grant_amount float               // Minimum grant amount to consider significant
}

// Grant-making profile for a foundation
class GrantMakingProfile {
    ein string
    foundation_name string
    foundation_type string               // "Private Non-Operating", "Private Operating", etc.
    total_grants_paid float             // Total grants paid in latest year
    number_of_grants int                // Number of grants made
    average_grant_size float            // Average grant amount
    largest_grant_amount float          // Largest single grant
    smallest_grant_amount float         // Smallest grant (above minimum)
    grant_focus_areas string[]          // Identified focus areas from grant descriptions
    geographic_focus string[]           // States/regions where grants are concentrated
    recurring_recipients string[]       // Organizations that receive grants multiple years
    grant_making_consistency_score float // 0.0-1.0 score of consistent grant-making
}

// Payout requirement analysis for foundations
class PayoutAnalysis {
    ein string
    foundation_name string
    tax_year int
    total_assets float                   // Total foundation assets
    required_payout_percentage float     // Required payout percentage (typically 5%)
    required_payout_amount float         // Calculated required payout amount
    actual_grants_paid float            // Actual grants paid
    payout_compliance_status string     // "Compliant", "Over-Payout", "Under-Payout"
    excess_payout_amount float?          // Amount paid above requirement (if any)
    payout_deficit_amount float?         // Amount short of requirement (if any)
    administrative_expenses float        // Foundation administrative costs
    investment_income float              // Investment income for the year
    payout_ratio float                  // Actual payout as percentage of assets
}

// Foundation capacity scoring for grant research
class CapacityScore {
    ein string
    foundation_name string
    overall_capacity_score float         // 0.0-1.0 overall grant-making capacity
    financial_strength_score float       // Based on assets and stability
    grant_activity_score float          // Based on consistent grant-making
    grant_size_score float              // Based on average grant sizes
    accessibility_score float           // Based on application process and requirements
    alignment_likelihood_score float    // Likelihood of funding similar organizations
    capacity_category string            // "Major", "Significant", "Moderate", "Limited"
    annual_grant_budget_estimate float  // Estimated annual grant budget
    recommended_ask_range string        // Suggested grant request range
    best_application_timing string      // Recommended timing for applications
    capacity_trend string               // "Increasing", "Stable", "Decreasing"
}

// Investment portfolio analysis for foundations
class InvestmentProfile {
    ein string
    foundation_name string
    tax_year int
    total_investment_assets float        // Total investment portfolio value
    investment_income float              // Income generated from investments
    investment_return_rate float         // Return rate as percentage
    portfolio_growth_rate float          // Year-over-year portfolio growth
    investment_strategy_indicators string[] // Indicators of investment strategy
    liquidity_ratio float               // Ratio of liquid to total assets
    investment_risk_profile string      // "Conservative", "Moderate", "Aggressive"
    endowment_stability_score float     // 0.0-1.0 score of endowment stability
}

// Foundation intelligence execution metadata
class FoundationExecutionMetadata {
    execution_time_ms float
    foundations_analyzed int
    payout_analyses_completed int
    capacity_scores_generated int
    investment_profiles_created int
    high_value_foundations_identified int
    data_completeness_average float
    analysis_depth_score float
    trend_analysis_years int
    calculation_accuracy_score float
}

// Quality assessment for foundation intelligence
class FoundationQualityAssessment {
    overall_analysis_quality float       // 0.0-1.0 overall quality of analysis
    payout_calculation_accuracy float    // Accuracy of payout requirement calculations
    capacity_scoring_reliability float   // Reliability of capacity scoring methodology
    investment_analysis_depth float      // Depth of investment portfolio analysis
    grant_pattern_detection_score float  // Accuracy of grant pattern detection
    foundation_classification_accuracy float // Accuracy of foundation type classification
    limitation_notes string[]            // Any limitations or data quality issues
}

// Output: Complete foundation grant intelligence result
class FoundationIntelligenceResult {
    grant_making_profiles GrantMakingProfile[]
    payout_requirements PayoutAnalysis[]
    foundation_capacity_scores CapacityScore[]
    investment_analysis InvestmentProfile[]
    high_value_foundations string[]      // EINs of foundations with highest grant potential
    execution_metadata FoundationExecutionMetadata
    quality_assessment FoundationQualityAssessment
    tool_name string                     // "Foundation Grant Intelligence Tool"
    framework_compliance string          // "Human Layer 12-Factor Agents"
    factor_4_implementation string       // "Tools as Structured Outputs - eliminates foundation analysis errors"
    foundations_processed int
    major_grant_makers int               // Number of foundations classified as major grant makers
    total_grant_capacity_estimated float // Total estimated annual grant capacity
}