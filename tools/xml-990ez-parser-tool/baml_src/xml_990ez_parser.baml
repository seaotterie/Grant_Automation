// XML 990-EZ Parser Tool - BAML Schema
// Human Layer 12-Factor Agents Framework - Factor 4: Tools as Structured Outputs
// Single Responsibility: XML download and 990-EZ form schedule parsing (Small Organizations Only)

// Input: Criteria for XML 990-EZ parsing
class XML990EZParseCriteria {
    target_eins string[]                      // List of EINs to parse (must be small organizations)
    schedules_to_extract string[]            // Schedules to extract: ["officers", "revenue", "expenses", "balance_sheet", "public_support"]
    cache_enabled bool                       // Whether to use cached XML files
    max_years_back int                       // Maximum years of historical data
    download_if_missing bool                 // Download XML if not cached
    validate_990ez_schema bool               // Strict validation that forms are 990-EZ (not 990 or 990-PF)
}

// Officer/director from Form 990-EZ Part V
class SmallOrgOfficer {
    ein string
    person_name string
    title string                             // President, Secretary, Treasurer, Director, etc.
    average_hours_per_week float?
    compensation float?                      // Compensation from organization
    is_officer bool                          // Officer designation
    is_director bool                         // Director designation
    is_trustee bool                          // Trustee designation
    is_key_employee bool                     // Key employee designation
    tax_year int
    data_source string                       // "Form 990-EZ XML"
}

// Revenue breakdown from Form 990-EZ Part I
class Form990EZRevenue {
    ein string
    tax_year int

    // Revenue sources (Part I)
    contributions_gifts_grants float?        // Contributions, gifts, grants received
    program_service_revenue float?           // Program service revenue
    membership_dues_assessments float?       // Membership dues and assessments
    investment_income float?                 // Investment income
    gross_amount_from_sale_assets float?     // Gross amount from sale of assets
    special_events_gross_revenue float?      // Special events gross revenue
    special_events_direct_expenses float?    // Special events direct expenses
    special_events_net_income float?         // Special events net income
    gross_sales_inventory float?             // Gross sales of inventory
    cost_goods_sold float?                   // Cost of goods sold
    gross_profit_loss_inventory float?       // Gross profit or loss from inventory
    other_revenue float?                     // Other revenue
    total_revenue float?                     // Total revenue
}

// Expenses from Form 990-EZ Part I
class Form990EZExpenses {
    ein string
    tax_year int

    // Expense categories
    grants_similar_amounts_paid float?       // Grants and similar amounts paid
    benefits_paid_members float?             // Benefits paid to or for members
    salaries_wages_benefits float?           // Salaries, other compensation, employee benefits
    professional_fees float?                 // Professional fees and other payments
    occupancy_rent_utilities float?          // Occupancy, rent, utilities, and maintenance
    printing_publications_postage float?     // Printing, publications, postage, and shipping
    other_expenses float?                    // Other expenses
    total_expenses float?                    // Total expenses
    excess_deficit_current_year float?       // Excess or deficit for the year
}

// Balance sheet from Form 990-EZ Part II
class Form990EZBalanceSheet {
    ein string
    tax_year int

    // Assets (Beginning of Year and End of Year)
    cash_savings_investments_boy float?      // Cash, savings, and investments (BOY)
    cash_savings_investments_eoy float?      // Cash, savings, and investments (EOY)
    land_buildings_boy float?                // Land and buildings (BOY)
    land_buildings_eoy float?                // Land and buildings (EOY)
    other_assets_boy float?                  // Other assets (BOY)
    other_assets_eoy float?                  // Other assets (EOY)
    total_assets_boy float?                  // Total assets (BOY)
    total_assets_eoy float?                  // Total assets (EOY)

    // Liabilities (Beginning of Year and End of Year)
    total_liabilities_boy float?             // Total liabilities (BOY)
    total_liabilities_eoy float?             // Total liabilities (EOY)

    // Net Assets
    net_assets_boy float?                    // Net assets or fund balances (BOY)
    net_assets_eoy float?                    // Net assets or fund balances (EOY)
}

// Public support test data from Form 990-EZ Part VI
class PublicSupportData {
    ein string
    tax_year int

    // Public support test (for public charity status)
    total_support float?                     // Total support
    gross_receipts_related_activities float? // Gross receipts from related activities
    first_five_years_support float?          // First 5 years support for new organizations
    public_support_percentage float?         // Public support percentage
    public_charity_status bool?              // Meets public charity requirements

    // Support sources
    gifts_grants_contributions float?        // Gifts, grants, contributions received
    membership_fees_received float?          // Membership fees received
    gross_receipts_admissions float?         // Gross receipts from admissions
    gross_receipts_merchandise float?        // Gross receipts from merchandise
    gross_receipts_other float?              // Gross receipts from other sources
}

// Program accomplishments from Form 990-EZ Part III
class ProgramAccomplishment {
    ein string
    tax_year int
    accomplishment_number int                // 1, 2, 3, 4a, 4b, 4c, 4d
    description string?                      // Description of accomplishment
    expense_amount float?                    // Expenses for this accomplishment
}

// Small organization operations summary
class SmallOrgOperations {
    ein string
    tax_year int

    // Basic operational data
    organization_type string?                // Corporation, trust, association, etc.
    formation_year int?                      // Year of formation
    activity_codes string[]                  // NTEE activity codes

    // Operational indicators
    significant_change_activities bool?      // Significant change in activities
    unrelated_business_income bool?          // Unrelated business income
    organization_dissolved bool?             // Organization dissolved during year

    // Financial thresholds
    gross_receipts_normally_not_more_50k bool? // Gross receipts normally ≤ $50k
    total_assets_less_than_25k bool?         // Total assets < $25k at end of year
}

// XML file processing metadata for 990-EZ
class XML990EZFileMetadata {
    ein string
    object_id string
    file_path string
    file_size_bytes int
    download_timestamp string
    tax_year int
    form_type string                         // Should be "990-EZ"
    xml_namespaces string[]
    parsing_success bool
    parsing_errors string[]
    schema_validation_passed bool            // True if confirmed to be 990-EZ form
}

// Execution metadata for 990-EZ processing
class XML990EZExecutionMetadata {
    execution_time_ms float
    organizations_processed int
    xml_files_found int
    xml_files_downloaded int
    xml_files_parsed int
    schema_validation_failures int           // Files that were not 990-EZ forms
    cache_hits int
    cache_misses int
    cache_hit_rate float
    total_officers_extracted int
    total_accomplishments_extracted int
    parsing_errors int
    download_errors int
}

// Quality assessment for 990-EZ parsing
class XML990EZQualityAssessment {
    overall_success_rate float
    schema_validation_rate float             // Percentage of files that were valid 990-EZ forms
    officer_data_completeness float
    revenue_data_completeness float
    expense_data_completeness float
    balance_sheet_completeness float
    data_freshness_score float
    limitation_notes string[]
}

// Complete XML 990-EZ parsing result - Factor 4 structured output
class XML990EZResult {
    officers: SmallOrgOfficer[]
    revenue_data: Form990EZRevenue[]
    expense_data: Form990EZExpenses[]
    balance_sheets: Form990EZBalanceSheet[]
    public_support_data: PublicSupportData[]
    program_accomplishments: ProgramAccomplishment[]
    operations_data: SmallOrgOperations[]
    xml_files_processed: XML990EZFileMetadata[]
    execution_metadata: XML990EZExecutionMetadata
    quality_assessment: XML990EZQualityAssessment
    tool_name string                         // "XML 990-EZ Parser Tool"
    framework_compliance string              // "Human Layer 12-Factor Agents"
    factor_4_implementation string           // "Tools as Structured Outputs - eliminates XML parsing errors"
    form_type_specialization string          // "990-EZ Forms Only - Small Organizations"
    organizations_processed int
    officers_extracted int
    accomplishments_extracted int
    extraction_failures int
}