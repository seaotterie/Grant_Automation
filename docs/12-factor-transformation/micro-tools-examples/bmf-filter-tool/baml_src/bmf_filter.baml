// BMF Filter Tool BAML Schema
// Following 12-Factor Agents Pattern: Tools are structured outputs

// Tool Intent - What the LLM outputs to trigger this tool
class BMFFilterIntent {
    intent "bmf_filter"
    criteria BMFFilterCriteria
    what_youre_looking_for string @description("Human description of search goal")
}

// Search criteria structure
class BMFFilterCriteria {
    states string[]? @description("State codes like VA, MD, DC")
    revenue_min int? @description("Minimum annual revenue in dollars")
    revenue_max int? @description("Maximum annual revenue in dollars")
    ntee_codes string[]? @description("NTEE codes like P20=Education, B25=Health")
    asset_min int? @description("Minimum assets in dollars")
    asset_max int? @description("Maximum assets in dollars")
    organization_name string? @description("Partial name search")
    limit int? @default(100) @description("Maximum results to return")
}

// Tool Result - What the tool returns
class BMFFilterResult {
    intent "bmf_filter_result"
    organizations BMFOrganization[]
    summary BMFSearchSummary
    execution_metadata BMFExecutionData
}

// Individual organization record
class BMFOrganization {
    ein string @description("Employer ID Number - unique identifier")
    name string @description("Official organization name")
    city string? @description("City location")
    state string @description("State location (2-letter code)")
    ntee_code string @description("Nonprofit category code (e.g., P20=Education)")
    revenue int? @description("Annual revenue in dollars")
    assets int? @description("Total assets in dollars")
    match_reasons string[] @description("Why this organization matched search criteria")
}

// Search summary and insights
class BMFSearchSummary {
    total_found int @description("Number of organizations found")
    criteria_summary string @description("Human readable description of search criteria")
    top_matches_description string @description("Summary of the best matching organizations")
}

// Execution performance data
class BMFExecutionData {
    execution_time_ms float @description("Total execution time in milliseconds")
    cache_hit bool @description("Whether result came from cache")
    database_query_time_ms float @description("Time spent querying database")
    results_truncated bool @description("Whether results were limited by max_results")
}

// Natural language extraction function
function ExtractBMFFilterIntent(user_request: string) -> BMFFilterIntent {
    client OpenAI
    prompt #"
        The user wants to search for nonprofit organizations in the IRS Business Master File.
        Convert their natural language request into a structured search intent.

        User request: {{ user_request }}

        Guidelines for extraction:
        - States/locations → states array (use 2-letter codes: VA, MD, DC, etc.)
        - Revenue/budget/income mentions → revenue_min/max
        - Focus areas → ntee_codes:
          * Education = P20
          * Health/Medical = B25
          * Human Services = P99
          * Arts/Culture = A20
          * Environment = C20
          * Religion = X20
        - Size/assets mentions → asset_min/max
        - Specific organization names → organization_name
        - Number of results → limit

        Create a BMFFilterIntent with appropriate criteria and a clear description
        of what_youre_looking_for based on the user's intent.

        Examples:
        "Find education nonprofits in Virginia" →
        {
          "intent": "bmf_filter",
          "criteria": {
            "states": ["VA"],
            "ntee_codes": ["P20"]
          },
          "what_youre_looking_for": "Education-focused nonprofit organizations in Virginia"
        }

        "Large health organizations with revenue over $1M" →
        {
          "intent": "bmf_filter",
          "criteria": {
            "ntee_codes": ["B25"],
            "revenue_min": 1000000
          },
          "what_youre_looking_for": "Large health organizations with significant revenue"
        }
    "#
}