// ProPublica API Enrichment Tool - BAML Schema
// Human Layer 12-Factor Agents Framework - Factor 4: Tools as Structured Outputs

// Input: Criteria for ProPublica API enrichment
class ProPublicaAPIEnrichmentCriteria {
    target_eins string[]                  // List of EINs to enrich from previous tools
    include_filing_history bool           // Whether to fetch detailed filing history
    years_to_include int                  // Number of years of filing data to include
    include_mission_data bool             // Whether to fetch mission and activity descriptions
    include_leadership_summary bool       // Whether to extract basic leadership compensation data
    include_similar_orgs bool             // Whether to find similar organizations
    max_similar_orgs int                  // Maximum number of similar organizations to find
}

// Core organization profile from ProPublica API
class ProPublicaOrganizationProfile {
    ein string
    name string
    organization_type string              // "public_charity", "private_foundation", etc.
    state string?
    city string?
    zip_code string?
    ntee_code string?
    ntee_description string?
    mission_description string?
    activity_description string?
    website_url string?
    ruling_date string?
    classification string?
    api_data_freshness float             // 0.0-1.0 score of how recent the API data is
    data_completeness_score float        // 0.0-1.0 score of how complete the profile is
}

// Filing summary from ProPublica API
class FilingSummary {
    ein string
    tax_year int
    form_type string                     // "990", "990-PF", "990-EZ"
    total_revenue float?
    total_expenses float?
    total_assets float?
    total_liabilities float?
    net_assets float?
    filing_date string?
    pdf_url string?
    data_source string                   // Always "ProPublica API"
}

// Basic leadership compensation data from ProPublica API
class APILeadershipSummary {
    ein string
    tax_year int
    total_compensation float?            // Total compensation paid to officers/directors
    highest_compensation float?          // Highest individual compensation
    number_of_officers int?              // Count of officers/directors (if available)
    compensation_data_quality string     // "Limited - API only provides totals, use XML tools for detailed rosters"
    data_source string                   // "ProPublica API"
}

// Similar organization found through API search
class SimilarOrganization {
    ein string
    name string
    state string?
    ntee_code string?
    revenue_amount float?
    similarity_score float               // 0.0-1.0 based on matching criteria
    similarity_reasons string[]          // Reasons for similarity (sector, location, size)
}

// API execution metadata
class APIExecutionMetadata {
    execution_time_ms float
    api_calls_made int
    rate_limit_delays_ms float
    cache_hits int
    cache_hit_rate float
    failed_requests int
    success_rate float
    api_limitations string[]             // Any limitations encountered
}

// Output: Complete ProPublica API enrichment result
class ProPublicaAPIResult {
    enriched_organizations ProPublicaOrganizationProfile[]
    filing_summaries FilingSummary[]
    leadership_summaries APILeadershipSummary[]
    similar_organizations SimilarOrganization[]
    execution_metadata APIExecutionMetadata
    tool_name string                     // "ProPublica API Enrichment Tool"
    framework_compliance string          // "Human Layer 12-Factor Agents"
    factor_4_implementation string       // "Tools as Structured Outputs - eliminates API parsing errors"
    leadership_data_note string          // "Limited API data - use XML 990/990-PF/990-EZ tools for complete leadership rosters"
    total_organizations_processed int
    organizations_enriched int
    organizations_failed int
    quality_assessment QualityAssessment
}

// Data quality assessment
class QualityAssessment {
    overall_quality_score float          // 0.0-1.0 average quality across all organizations
    api_data_freshness float             // How recent the API data is
    completeness_distribution float[]    // Distribution of completeness scores
    enrichment_success_rate float        // Percentage of organizations successfully enriched
    limitation_notes string[]            // Any data quality limitations found
}