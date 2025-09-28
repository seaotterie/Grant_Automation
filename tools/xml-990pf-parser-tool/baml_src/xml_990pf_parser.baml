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

// Foundation officer/director from 990-PF Part VIII
class FoundationOfficer {
    ein string
    person_name string
    title string                             // President, Secretary, Treasurer, Director, Trustee, etc.
    average_hours_per_week float?
    compensation float?                      // Total compensation from foundation
    employee_benefit_program bool?           // Participating in employee benefit programs
    expense_account_allowance float?         // Expense account or allowance
    is_officer bool                          // Officer designation
    is_director bool                         // Director/trustee designation
    tax_year int
    data_source string                       // "Form 990-PF XML"
}

// Grant paid by foundation from 990-PF Part XV
class FoundationGrant {
    ein string
    recipient_name string
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
    officers: FoundationOfficer[]
    grants_paid: FoundationGrant[]
    investment_holdings: InvestmentHolding[]
    excise_tax_data: ExciseTaxData[]
    payout_requirements: PayoutRequirement[]
    governance_indicators: FoundationGovernance[]
    financial_summaries: Foundation990PFFinancialSummary[]
    xml_files_processed: XML990PFFileMetadata[]
    execution_metadata: XML990PFExecutionMetadata
    quality_assessment: XML990PFQualityAssessment
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