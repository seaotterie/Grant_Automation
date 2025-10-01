// XML 990-PF Parser Tool - BAML Schema
// Human Layer 12-Factor Agents Framework - Factor 4: Tools as Structured Outputs
// Single Responsibility: XML download and 990-PF form schedule parsing (Private Foundations Only)

// Input: Criteria for XML 990-PF parsing
class XML990PFParseCriteria {
    target_eins string[]                      // List of EINs to parse (must be private foundations)
    schedules_to_extract string[]            // Schedules to extract: ["officers", "grants_paid", "investments", "excise_tax", "payout_requirements"]
    cache_enabled bool                       // Whether to use cached XML files
    max_years_back int                       // Maximum years of historical data
    download_if_missing bool                 // Download XML if not cached
    validate_990pf_schema bool               // Strict validation that forms are 990-PF (not 990 or 990-EZ)
}

// Foundation contact information from 990-PF header
class FoundationContactInfo {
    ein string
    foundation_name string
    address_line_1 string?
    address_line_2 string?
    city string?
    state string?
    zip_code string?
    country string?
    phone_number string?
    website string?
    email string?
    principal_officer_name string?           // Name of principal officer
    principal_officer_title string?         // Title of principal officer
    contact_person_name string?              // Contact person for grant inquiries
    contact_person_title string?
    tax_year int
    data_source string                       // "Form 990-PF XML Header"
}

// Foundation officer/director from 990-PF Part VIII
class FoundationOfficer {
    ein string
    person_name string
    normalized_person_name string            // Cleaned name for network matching (UPPERCASE, no punctuation)
    title string                             // President, Secretary, Treasurer, Director, Trustee, etc.
    role_category string                     // Executive, Board, Staff, Volunteer
    average_hours_per_week float?
    compensation float?                      // Total compensation from foundation
    employee_benefit_program bool?           // Participating in employee benefit programs
    expense_account_allowance float?         // Expense account or allowance
    is_officer bool                          // Officer designation
    is_director bool                         // Director/trustee designation
    influence_score float?                   // Calculated decision-making power score (0-1)
    tax_year int
    data_source string                       // "Form 990-PF XML"
}

// Grant paid by foundation from 990-PF Part XV
class FoundationGrant {
    ein string
    recipient_name string
    normalized_recipient_name string         // Cleaned org name for network matching
    recipient_ein string?                    // **CRITICAL** for org-to-org network mapping
    recipient_type string?                   // Individual, Organization, etc.
    recipient_address string?
    recipient_relationship string?           // Relationship to foundation
    grant_amount float
    grant_purpose string?
    foundation_status_of_recipient string?   // 501(c)(3) status, etc.
    grant_monitoring_procedures string?      // How foundation monitors use
    tax_year int
    schedule_part string                     // "Part XV - Grants"
}

// Foundation grant distribution analysis for strategic intelligence
class FoundationGrantAnalysis {
    ein string
    tax_year int
    total_grants_count int
    total_grants_amount float
    average_grant_size float
    largest_grant_amount float?
    smallest_grant_amount float?
    median_grant_amount float?

    // Grant recipient patterns
    individual_recipients_count int          // Grants to individuals
    organization_recipients_count int        // Grants to organizations
    geographic_concentration string?         // Primary geographic focus
    recipient_diversity_score float?        // 0-1 score of recipient diversity

    // Grant purpose analysis
    top_grant_purposes string[]             // Most common grant purposes
    funding_focus_areas string[]            // Key funding priority areas
    impact_grant_percentage float?          // % of grants labeled as "impact"
    flexible_funding_percentage float?      // % of grants for flexible funding

    // Grant size distribution
    large_grants_count int                  // Grants >= $100K
    medium_grants_count int                 // Grants $10K - $99K
    small_grants_count int                  // Grants < $10K
    grant_size_strategy string              // "Large Impact", "Broad Distribution", "Mixed Strategy"

    // Historical patterns
    grant_making_consistency string         // "Consistent", "Variable", "Seasonal"
    repeat_recipient_percentage float?      // % of grants to previous recipients
    new_recipient_percentage float?         // % of grants to new recipients

    data_source string                      // "Form 990-PF Grant Analysis"
}

// Foundation classification and grant-making approach analysis
class FoundationClassification {
    ein string
    tax_year int

    // Foundation type classification
    foundation_type string                   // "Private Foundation", "Operating Foundation", "Family Foundation", "Corporate Foundation"
    foundation_size_category string          // "Major", "Large", "Medium", "Small" based on assets
    grant_making_approach string             // "Strategic", "Responsive", "Mixed", "Emerging"

    // Grant-making characteristics
    funding_model string                     // "Proactive", "Reactive", "Invitation Only", "Open Application"
    geographic_scope string                  // "Local", "Regional", "National", "International"
    sector_focus string[]                    // Primary sectors based on grant analysis

    // Foundation maturity and sophistication
    operational_sophistication string       // "High", "Medium", "Basic" based on governance indicators
    grant_making_maturity string            // "Mature", "Developing", "Emerging" based on processes
    professional_management string          // "Professional", "Board-Managed", "Mixed" based on compensation

    // Grant strategy intelligence
    risk_tolerance string                    // "Conservative", "Moderate", "Aggressive" based on grant patterns
    innovation_focus string                  // "High", "Medium", "Low" based on grant purposes
    capacity_building_emphasis string       // "High", "Medium", "Low" based on grant types

    // Foundation accessibility for grant seekers
    grant_accessibility_score float         // 0-1 score for how accessible foundation is to new applicants
    application_complexity string           // "Simple", "Moderate", "Complex" based on procedures
    funding_predictability string           // "Predictable", "Variable", "Opportunistic"

    // Strategic positioning
    competitive_landscape_position string   // Position relative to similar foundations
    unique_value_proposition string?        // What makes this foundation distinctive
    grant_seeker_recommendations string[]  // Strategic advice for potential applicants

    data_source string                      // "Form 990-PF Classification Analysis"
}

// Investment holding from 990-PF Part II
class InvestmentHolding {
    ein string
    tax_year int
    investment_type string                   // Corporate stock, bonds, etc.
    book_value float?
    fair_market_value float?
    investment_description string?
    acquisition_date string?
    cost_basis float?
    investment_category string               // "Corporate Stock", "Corporate Bonds", "Government Securities", etc.
}

// Investment portfolio analysis for grant capacity assessment
class InvestmentAnalysis {
    ein string
    tax_year int

    // Portfolio composition
    total_investment_value float             // Total fair market value of investments
    total_investment_count int               // Number of investment holdings
    portfolio_diversification_score float   // 0-1 score of diversification

    // Asset allocation analysis
    equity_percentage float?                 // % in stocks/equity investments
    fixed_income_percentage float?           // % in bonds/fixed income
    alternative_investments_percentage float? // % in other investments
    cash_equivalent_percentage float?        // % in cash/cash equivalents

    // Investment performance indicators
    unrealized_gains_losses float?           // Difference between FMV and book value
    investment_return_estimate float?        // Estimated annual return rate
    investment_volatility_assessment string  // "Low", "Medium", "High" risk portfolio

    // Grant capacity analysis
    sustainable_grant_capacity float         // Estimated sustainable annual grant amount
    grant_funding_stability string           // "Very Stable", "Stable", "Variable", "Volatile"
    endowment_sustainability_years int?      // Years foundation could operate at current levels

    // Strategic investment insights
    investment_strategy_type string          // "Conservative", "Balanced", "Growth", "Income"
    liquidity_assessment string              // "High", "Medium", "Low" - ability to convert to cash
    professional_management_indicators bool  // Evidence of professional investment management

    // Grant-making implications
    grant_capacity_trend string              // "Growing", "Stable", "Declining"
    optimal_grant_timing string?             // Best times to apply based on portfolio performance
    multi_year_grant_feasibility string     // "High", "Medium", "Low" based on stability

    data_source string                       // "Form 990-PF Investment Analysis"
}

// Excise tax computation from 990-PF Part VI
class ExciseTaxData {
    ein string
    tax_year int
    net_investment_income float?             // Subject to excise tax
    excise_tax_rate float?                   // 1% or 2%
    excise_tax_owed float?
    prior_year_tax_underpayment float?
    total_excise_tax_and_underpayment float?
    qualifying_distributions_made float?     // For excise tax reduction
}

// Payout requirements and calculations from 990-PF Part XII
class PayoutRequirement {
    ein string
    tax_year int
    average_monthly_fair_market_value float? // Of foundation assets
    minimum_investment_return float?         // 5% of average monthly FMV
    distributable_amount float?              // Amount that must be distributed
    qualifying_distributions_made float?     // Actual distributions made
    excess_distributions float?              // Distributions above minimum
    underdistributions float?                // If distributions below minimum
    carryover_from_prior_years float?        // Excess from previous years
    remaining_underdistributions float?      // Carried to next year
}

// Foundation governance and operations from various 990-PF sections
class FoundationGovernance {
    ein string
    tax_year int

    // Foundation classification
    operating_foundation bool?               // Operating vs non-operating foundation
    private_foundation_status bool?          // Subject to 4940 excise tax
    section_4942_j_election bool?            // Election to be treated as operating foundation

    // Governance indicators
    board_meetings_held int?                 // Number of board meetings
    compensation_policy bool?                // Written compensation policy
    conflict_of_interest_policy bool?        // Conflict of interest policy
    minutes_of_governing_body bool?          // Minutes kept for meetings

    // Financial oversight
    independent_audit bool?                  // Independent audit performed
    audit_committee bool?                    // Audit committee exists
    investment_policy bool?                  // Written investment policy

    // Grant making procedures
    grant_making_procedures bool?            // Written grant making procedures
    grant_monitoring_procedures bool?        // Procedures to monitor grants
    website_grant_application_process bool?  // Website describes grant process
}

// Foundation financial summary from 990-PF Part I
class Foundation990PFFinancialSummary {
    ein string
    tax_year int

    // Revenue (Part I)
    contributions_received float?            // Contributions, gifts, grants received
    interest_dividends_received float?       // Interest and dividends
    gross_rents float?                       // Gross rents received
    net_rental_income float?                 // Net rental income
    net_gain_sales_assets float?             // Net gain from sale of assets
    gross_sales_price float?                 // Gross sales price of assets sold
    total_revenue float?                     // Total revenue

    // Expenses (Part I)
    compensation_officers_directors float?   // Compensation of officers/directors
    other_employee_salaries float?           // Other employee salaries and wages
    pension_plans_benefits float?            // Pension plans, employee benefits
    legal_fees float?                        // Legal fees
    accounting_fees float?                   // Accounting fees
    other_professional_fees float?           // Other professional fees
    interest_expense float?                  // Interest expense
    taxes float?                             // Taxes
    other_expenses float?                    // Other expenses
    total_operating_expenses float?          // Total operating and administrative expenses

    // Balance Sheet (Part II)
    cash_non_interest_bearing float?         // Cash - non-interest-bearing
    savings_temporary_investments float?     // Savings and temporary cash investments
    accounts_receivable float?               // Accounts receivable
    pledges_receivable float?                // Pledges receivable
    grants_receivable float?                 // Grants receivable
    investments_corporate_stock float?       // Investments - corporate stock
    investments_corporate_bonds float?       // Investments - corporate bonds
    total_assets float?                      // Total assets
    accounts_payable float?                  // Accounts payable and accrued expenses
    grants_payable float?                    // Grants payable
    total_liabilities float?                 // Total liabilities
    net_assets float?                        // Net assets or fund balances
}

// XML file processing metadata for 990-PF
class XML990PFFileMetadata {
    ein string
    object_id string
    file_path string
    file_size_bytes int
    download_timestamp string
    tax_year int
    form_type string                         // Should be "990-PF"
    xml_namespaces string[]
    parsing_success bool
    parsing_errors string[]
    schema_validation_passed bool            // True if confirmed to be 990-PF form
}

// Execution metadata for 990-PF processing
class XML990PFExecutionMetadata {
    execution_time_ms float
    organizations_processed int
    xml_files_found int
    xml_files_downloaded int
    xml_files_parsed int
    schema_validation_failures int           // Files that were not 990-PF forms
    cache_hits int
    cache_misses int
    cache_hit_rate float
    total_officers_extracted int
    total_grants_extracted int
    total_investments_extracted int
    parsing_errors int
    download_errors int
}

// Quality assessment for 990-PF parsing
class XML990PFQualityAssessment {
    overall_success_rate float
    schema_validation_rate float             // Percentage of files that were valid 990-PF forms
    officer_data_completeness float
    grant_data_completeness float
    investment_data_completeness float
    financial_data_completeness float
    governance_data_completeness float
    data_freshness_score float
    limitation_notes string[]
}

// Complete XML 990-PF parsing result - Factor 4 structured output
class XML990PFResult {
    contact_info FoundationContactInfo[]
    officers FoundationOfficer[]
    grants_paid FoundationGrant[]
    grant_analysis FoundationGrantAnalysis[]
    foundation_classification FoundationClassification[]
    investment_holdings InvestmentHolding[]
    investment_analysis InvestmentAnalysis[]
    excise_tax_data ExciseTaxData[]
    payout_requirements PayoutRequirement[]
    governance_indicators FoundationGovernance[]
    financial_summaries Foundation990PFFinancialSummary[]
    xml_files_processed XML990PFFileMetadata[]
    execution_metadata XML990PFExecutionMetadata
    quality_assessment XML990PFQualityAssessment
    tool_name string                         // "XML 990-PF Parser Tool"
    framework_compliance string              // "Human Layer 12-Factor Agents"
    factor_4_implementation string           // "Tools as Structured Outputs - eliminates XML parsing errors"
    form_type_specialization string          // "990-PF Forms Only - Private Foundations"
    organizations_processed int
    officers_extracted int
    grants_extracted int
    investments_extracted int
    extraction_failures int
}