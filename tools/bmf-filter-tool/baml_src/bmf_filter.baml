// BMF Filter Tool BAML Schema
// Following 12-Factor Agents Pattern: Tools are structured outputs that trigger deterministic code
// Integrates with existing Catalynx nonprofit intelligence database

// ============================================================================
// TOOL INTENT - What the LLM outputs to trigger this tool (Factor 4)
// ============================================================================

class BMFFilterIntent {
    intent "bmf_filter"
    criteria BMFFilterCriteria
    what_youre_looking_for string @description("Human description of search goal and intent")
    priority BMFSearchPriority? @description("Search priority level") @default("standard")
    context BMFSearchContext? @description("Additional context for filtering")
}

// Search priority levels
enum BMFSearchPriority {
    quick      @alias("Quick search with basic criteria")
    standard   @alias("Standard search with full criteria")
    thorough   @alias("Thorough search with extensive analysis")
}

// Additional search context
class BMFSearchContext {
    use_case string? @description("What this search will be used for")
    target_audience string? @description("Who will use these results")
    follow_up_actions string[]? @description("What happens after this search")
}

// ============================================================================
// SEARCH CRITERIA - Integrates with Catalynx database schema
// ============================================================================

class BMFFilterCriteria {
    // Geographic filters
    states string[]? @description("State codes like VA, MD, DC (2-letter format)")
    cities string[]? @description("City names for additional geographic filtering")
    geographic_scope BMFGeographicScope? @description("Geographic scope preference")

    // Financial filters - aligned with Catalynx database fields
    revenue_min int? @description("Minimum annual revenue in dollars")
    revenue_max int? @description("Maximum annual revenue in dollars")
    asset_min int? @description("Minimum total assets in dollars")
    asset_max int? @description("Maximum total assets in dollars")

    // NTEE code filters - matches existing Catalynx categories
    ntee_codes string[]? @description("NTEE codes: P20=Education, B25=Health, P99=Human Services, A20=Arts, C20=Environment, X20=Religion")
    ntee_major_groups string[]? @description("Major NTEE groups like P=Education, B=Health")

    // Organization characteristics
    organization_name string? @description("Partial name search (case-insensitive)")
    foundation_type BMFFoundationType? @description("Type of foundation or nonprofit")

    // NEW: Enhanced filtering with imported fields from eo2.csv
    status_codes string[]? @description("Organization status codes: 01=Active, 02=Inactive, 12=Merged, 25=Terminated")
    filing_req_codes string[]? @description("Filing requirement codes: 01=990 Required, 02=990-EZ Eligible, 06=990-N Required")
    deductibility_codes string[]? @description("Deductibility codes: 1=Deductible, 2=Non-deductible, 0=Unknown")
    activity_codes string[]? @description("Activity classification codes from IRS")
    group_codes string[]? @description("Group classification codes")
    ruling_date_after string? @description("Organization ruling date after YYYYMM format (e.g., 200001 for 2000 or later)")
    ruling_date_before string? @description("Organization ruling date before YYYYMM format")

    // Data quality filters
    has_recent_990 bool? @description("Must have recent Form 990 filing")
    min_data_quality BMFDataQuality? @description("Minimum data quality requirement")
    active_orgs_only bool? @default(true) @description("Only include active organizations (status=01)")

    // Result configuration
    limit int? @default(100) @description("Maximum results to return (max 1000)")
    sort_by BMFSortOption? @default("revenue_desc") @description("How to sort results")
    include_metadata bool? @default(true) @description("Include execution metadata")
}

// Geographic scope options
enum BMFGeographicScope {
    local       @alias("Local/city level focus")
    regional    @alias("Regional/state level focus")
    national    @alias("National scope organizations")
    any         @alias("Any geographic scope")
}

// Foundation/nonprofit types aligned with BMF data
enum BMFFoundationType {
    public_charity          @alias("Public charity (501c3)")
    private_foundation      @alias("Private foundation (990-PF)")
    operating_foundation    @alias("Private operating foundation")
    community_foundation    @alias("Community foundation")
    corporate_foundation    @alias("Corporate foundation")
    any                     @alias("Any foundation type")
}

// Data quality levels
enum BMFDataQuality {
    basic       @alias("Basic BMF data only")
    standard    @alias("BMF + some 990 data")
    comprehensive @alias("BMF + complete 990 data")
}

// Sorting options
enum BMFSortOption {
    revenue_desc    @alias("Revenue (highest first)")
    revenue_asc     @alias("Revenue (lowest first)")
    assets_desc     @alias("Assets (highest first)")
    assets_asc      @alias("Assets (lowest first)")
    name_asc        @alias("Name (alphabetical)")
    recent_filing   @alias("Most recent 990 filing")
}

// ============================================================================
// TOOL RESULT - What the tool returns (Factor 4: Structured Output)
// ============================================================================

class BMFFilterResult {
    intent "bmf_filter_result"
    organizations BMFOrganization[]
    summary BMFSearchSummary
    execution_metadata BMFExecutionData
    quality_assessment BMFQualityAssessment
    recommendations BMFRecommendations?
}

// Individual organization record - enhanced with complete eo2.csv data
class BMFOrganization {
    // Primary identifiers
    ein string @description("Employer ID Number - unique identifier")
    name string @description("Official organization name")
    ico string? @description("In care of name")

    // Location information
    street string? @description("Street address")
    city string? @description("City location")
    state string @description("State location (2-letter code)")
    zip_code string? @description("ZIP code")

    // Classification and codes
    ntee_code string @description("NTEE code (e.g., P20=Education, B25=Health)")
    ntee_description string? @description("Human-readable NTEE description")
    foundation_code string? @description("Foundation classification code")
    organization_code string? @description("Organization type code")
    subsection string? @description("Tax code subsection (e.g., 03 for 501c3)")
    classification string? @description("Organization classification code")

    // NEW: Enhanced organizational metadata from eo2.csv
    status string? @description("Organization status: 01=Active, 02=Inactive, 12=Merged, 25=Terminated")
    filing_req_cd string? @description("Filing requirement: 01=990 Required, 02=990-EZ, 06=990-N")
    pf_filing_req_cd string? @description("Private foundation filing requirement")
    deductibility string? @description("Deductibility status: 1=Deductible, 2=Non-deductible")
    activity string? @description("Primary activity classification code")
    group_code string? @description("Group classification code")
    ruling_date string? @description("IRS ruling date (YYYYMM format)")
    affiliation string? @description("Affiliation code")
    acct_pd string? @description("Accounting period")

    // Financial data (from BMF and 990 filings)
    asset_amt int? @description("BMF asset amount")
    income_amt int? @description("BMF income amount")
    revenue_amt int? @description("BMF revenue amount")
    revenue int? @description("Form 990 annual revenue")
    assets int? @description("Form 990 total assets")
    expenses int? @description("Form 990 annual expenses")
    grants_paid int? @description("Grants paid (for foundations)")

    // Data quality indicators
    latest_990_year int? @description("Year of most recent 990 filing")
    data_completeness float? @description("Data completeness score (0-1)")
    tax_period string? @description("Tax period")

    // Why this organization matched
    match_reasons string[] @description("Specific reasons this organization matched criteria")
    match_score float? @description("Relevance score (0-1)")

    // Integration with existing Catalynx data
    catalynx_analyzed bool? @description("Whether this org has been analyzed by Catalynx")
    existing_opportunities int? @description("Number of existing opportunities identified")
}

// Search summary and insights
class BMFSearchSummary {
    total_found int @description("Total number of organizations found")
    total_in_database int @description("Total organizations checked in database")
    criteria_summary string @description("Human readable description of search criteria")
    top_matches_description string @description("Summary of the best matching organizations")
    geographic_distribution string @description("Distribution across states/regions")
    financial_summary string @description("Summary of financial characteristics")
    recommendations string[] @description("Suggestions for refining the search")
}

// Execution performance data (Factor 11: Logs as event streams)
class BMFExecutionData {
    execution_time_ms float @description("Total execution time in milliseconds")
    database_query_time_ms float @description("Time spent querying database")
    processing_time_ms float @description("Time spent processing results")

    cache_hit bool @description("Whether result came from cache")
    cache_key string? @description("Cache key used (if applicable)")

    results_truncated bool @description("Whether results were limited by max_results")
    query_complexity BMFQueryComplexity @description("Complexity of the executed query")

    // Performance metrics
    memory_used_mb float? @description("Memory used during execution")
    database_rows_scanned int? @description("Number of database rows examined")

    // Integration metrics
    compared_to_existing bool? @description("Whether compared to existing processor")
    performance_vs_existing float? @description("Performance ratio vs existing (>1 = faster)")
}

// Query complexity assessment
enum BMFQueryComplexity {
    simple      @alias("Simple criteria, fast execution")
    moderate    @alias("Multiple criteria, moderate complexity")
    complex     @alias("Complex criteria with multiple joins")
    very_complex @alias("Very complex multi-table analysis")
}

// Data quality assessment
class BMFQualityAssessment {
    overall_quality float @description("Overall data quality score (0-1)")
    completeness_rate float @description("Rate of complete records (0-1)")
    recent_data_rate float @description("Rate of recent 990 filings (0-1)")
    geographic_coverage string @description("Geographic coverage assessment")
    recommendations string[] @description("Data quality improvement suggestions")
}

// Recommendations for search refinement
class BMFRecommendations {
    refinement_suggestions string[] @description("Ways to refine the search criteria")
    expansion_suggestions string[] @description("Ways to expand the search if too narrow")
    next_steps string[] @description("Suggested next steps in the workflow")
    related_searches string[] @description("Related searches that might be useful")
}

// ============================================================================
// NATURAL LANGUAGE EXTRACTION FUNCTIONS
// ============================================================================

// Main function to extract structured intent from natural language
function ExtractBMFFilterIntent(user_request: string) -> BMFFilterIntent {
    client OpenAI
    prompt #"
        You are a nonprofit research expert helping to search the IRS Business Master File database.
        Convert the user's natural language request into a structured search intent.

        The database contains 2M+ nonprofit organizations with:
        - BMF data: EIN, name, location, NTEE codes, basic financial info
        - 990 filings: Detailed financial data, grants, activities
        - 990-PF filings: Foundation grant-making data

        User request: {{ user_request }}

        Guidelines for extraction:

        GEOGRAPHIC:
        - States/locations → states array (use 2-letter codes: VA, MD, DC, etc.)
        - Cities → cities array
        - Regional terms like "DC area" → ["VA", "MD", "DC"]

        FINANCIAL (in dollars):
        - Revenue/budget/income → revenue_min/max
        - Assets/endowment → asset_min/max
        - "Large" organizations → revenue_min: 1000000
        - "Small" organizations → revenue_max: 500000
        - "Major" foundations → asset_min: 10000000

        FOCUS AREAS → ntee_codes:
        - Education = P20
        - Health/Medical = B25
        - Human Services = P99
        - Arts/Culture = A20
        - Environment = C20
        - Religion = X20
        - Community Development = S20
        - Youth Development = O20

        ORGANIZATION TYPES:
        - "Foundations" → foundation_type: private_foundation
        - "Public charities" → foundation_type: public_charity
        - "Corporate foundations" → foundation_type: corporate_foundation

        DATA QUALITY:
        - "Recent data" → has_recent_990: true
        - "Complete information" → min_data_quality: comprehensive
        - "Active organizations" → status_codes: ["01"], active_orgs_only: true
        - "Filed recently" → filing_req_codes: ["01", "02"]

        NEW: ENHANCED FILTERING OPTIONS:
        - "Active only" → status_codes: ["01"]
        - "Inactive organizations" → status_codes: ["02", "12", "25"]
        - "Must file 990" → filing_req_codes: ["01"]
        - "990-EZ eligible" → filing_req_codes: ["02"]
        - "Tax-deductible donations" → deductibility_codes: ["1"]
        - "Established after 2000" → ruling_date_after: "200001"
        - "Recent organizations" → ruling_date_after: "201001"

        RESULT PREFERENCES:
        - Number mentioned → limit
        - "Top/best" → sort_by: revenue_desc
        - "Largest" → sort_by: assets_desc

        Create a BMFFilterIntent with:
        1. Appropriate criteria based on the request
        2. Clear what_youre_looking_for description
        3. Appropriate priority level
        4. Relevant context if available

        Examples:

        "Find large education nonprofits in Virginia" →
        {
          "intent": "bmf_filter",
          "criteria": {
            "states": ["VA"],
            "ntee_codes": ["P20"],
            "revenue_min": 1000000,
            "sort_by": "revenue_desc"
          },
          "what_youre_looking_for": "Large education-focused nonprofit organizations in Virginia for potential partnerships",
          "priority": "standard"
        }

        "Health foundations in DC area with assets over $5M for grant opportunities" →
        {
          "intent": "bmf_filter",
          "criteria": {
            "states": ["VA", "MD", "DC"],
            "ntee_codes": ["B25"],
            "asset_min": 5000000,
            "foundation_type": "private_foundation",
            "status_codes": ["01"],
            "filing_req_codes": ["01"],
            "deductibility_codes": ["1"],
            "sort_by": "assets_desc"
          },
          "what_youre_looking_for": "Active health-focused foundations in the DC metropolitan area with significant assets for grant partnership opportunities",
          "priority": "thorough",
          "context": {
            "use_case": "Grant opportunity identification",
            "target_audience": "Development team",
            "follow_up_actions": ["Contact research", "Grant application preparation"]
          }
        }

        "Find recent active education nonprofits in Virginia that accept tax-deductible donations" →
        {
          "intent": "bmf_filter",
          "criteria": {
            "states": ["VA"],
            "ntee_codes": ["P20"],
            "status_codes": ["01"],
            "deductibility_codes": ["1"],
            "ruling_date_after": "201001",
            "active_orgs_only": true,
            "sort_by": "ruling_date"
          },
          "what_youre_looking_for": "Recently established, active education nonprofits in Virginia that accept tax-deductible donations",
          "priority": "standard"
        }

        Focus on understanding the user's intent and creating comprehensive, accurate search criteria.
    "#
}

// Validation function to check search criteria
function ValidateBMFCriteria(criteria: BMFFilterCriteria) -> BMFValidationResult {
    client OpenAILite
    prompt #"
        Validate the BMF search criteria for potential issues or improvements.

        Criteria to validate: {{ criteria }}

        Check for:
        1. Valid state codes (2-letter format)
        2. Reasonable financial ranges
        3. Valid NTEE codes
        4. Logical combinations
        5. Performance considerations

        Return validation result with any issues found and suggestions for improvement.
    "#
}

// Validation result
class BMFValidationResult {
    is_valid bool @description("Whether criteria are valid")
    issues string[] @description("List of validation issues found")
    suggestions string[] @description("Suggestions for improvement")
    estimated_results int? @description("Estimated number of results")
    performance_warning bool @description("Whether query might be slow")
}