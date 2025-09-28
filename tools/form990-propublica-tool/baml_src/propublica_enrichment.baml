// BAML Schema for Form 990 ProPublica Enrichment Tool
// 12-Factor Factor 4: Structured input/output contracts

// =====================================================================================
// ENUMS AND TYPES
// =====================================================================================

enum EnrichmentDepth {
    basic
    standard
    comprehensive
}

enum OrganizationType {
    public_charity
    private_foundation
    private_operating_foundation
    public_foundation
    supporting_organization
    other
}

enum PeerSimilarityBasis {
    ntee_code
    revenue_size
    geographic_proximity
    program_focus
    combined
}

// =====================================================================================
// INPUT CONTRACTS
// =====================================================================================

class ProPublicaEnrichmentCriteria {
    // Target organizations (from previous tools)
    target_eins string[] @description("EINs to enrich from BMF/990 analysis tools")

    // Enrichment configuration
    enrichment_depth EnrichmentDepth @description("Level of detail for enrichment: basic, standard, comprehensive")
    max_organizations int? @description("Maximum organizations to process (default: 25)")

    // API data inclusion flags
    include_filing_history bool @description("Include complete ProPublica filing history")
    include_peer_analysis bool @description("Find and analyze similar organizations")
    include_leadership_details bool @description("Extract board and leadership information")
    include_program_details bool @description("Detailed program service descriptions")
    include_geographic_expansion bool @description("Multi-location and service area analysis")

    // Peer analysis configuration
    peer_search_radius int? @description("Geographic radius in miles for peer search (default: 50)")
    max_peer_organizations int? @description("Maximum similar organizations to find (default: 10)")
    peer_similarity_basis PeerSimilarityBasis? @description("Basis for determining organizational similarity")

    // Filing history configuration
    filing_years_limit int? @description("Years of filing history to include (default: 5)")
    include_document_links bool? @description("Include links to original PDF documents")

    // Quality and performance controls
    require_recent_filing bool? @description("Only include organizations with recent filings")
    min_data_quality_score float? @description("Minimum data completeness score (0.0-1.0)")
    enable_caching bool? @description("Enable aggressive caching for repeated queries")
}

class ProPublicaEnrichmentIntent {
    what_youre_enriching string @description("Human-readable description of enrichment goals")
    criteria ProPublicaEnrichmentCriteria @description("Structured enrichment criteria")
    priority_focus string? @description("Specific aspect to prioritize (leadership, programs, peers, etc.)")
}

// =====================================================================================
// OUTPUT CONTRACTS - ORGANIZATION PROFILES
// =====================================================================================

class ProPublicaFilingRecord {
    tax_year int @description("Tax year of the filing")
    form_type string @description("Type of form filed (990, 990-EZ, 990-PF)")
    pdf_url string? @description("URL to original PDF document")
    filing_date string? @description("Date the form was filed")
    total_revenue int? @description("Total revenue reported")
    total_expenses int? @description("Total expenses reported")
    total_assets int? @description("Total assets reported")
    has_form_data bool @description("Whether detailed form data is available")
}

class ProPublicaLeadershipMember {
    name string @description("Name of board member or officer")
    title string? @description("Position title or role")
    compensation int? @description("Total compensation if available")
    hours_per_week float? @description("Hours per week if available")
    is_key_employee bool? @description("Whether this is a key employee")
    is_officer bool? @description("Whether this person is an officer")
    is_director bool? @description("Whether this person is a director")
}

class ProPublicaProgramService {
    description string @description("Program service description")
    expenses int? @description("Program service expenses")
    revenue int? @description("Program service revenue")
    accomplishments string? @description("Program accomplishments description")
    beneficiaries string? @description("Primary beneficiaries served")
}

class ProPublicaPeerOrganization {
    ein string @description("EIN of similar organization")
    name string @description("Organization name")
    ntee_code string? @description("NTEE classification code")
    state string? @description("State where located")
    total_revenue int? @description("Total revenue for comparison")
    similarity_score float @description("Similarity score (0.0-1.0)")
    similarity_reasons string[] @description("Reasons for similarity match")
}

class ProPublicaGeographicInfo {
    primary_address string @description("Primary organizational address")
    service_states string[]? @description("States where services are provided")
    international_activities bool? @description("Whether organization has international activities")
    website_url string? @description("Organization website URL")
}

class ProPublicaOrganizationProfile {
    // Basic identification
    ein string @description("Employer Identification Number")
    name string @description("Organization name from ProPublica")
    organization_type OrganizationType @description("Type of tax-exempt organization")
    ntee_code string? @description("NTEE classification code")

    // Geographic and contact information
    geographic_info ProPublicaGeographicInfo @description("Location and service area details")

    // Filing history and documents
    filing_records ProPublicaFilingRecord[] @description("Complete filing history from ProPublica")
    latest_filing_year int? @description("Most recent filing year available")
    filing_data_quality float @description("Quality score for filing data (0.0-1.0)")

    // Leadership and governance
    leadership_members ProPublicaLeadershipMember[] @description("Board members and key officers")
    leadership_data_quality float @description("Quality score for leadership data (0.0-1.0)")

    // Program activities and services
    program_services ProPublicaProgramService[] @description("Detailed program service descriptions")
    mission_description string? @description("Organizational mission statement")
    program_data_quality float @description("Quality score for program data (0.0-1.0)")

    // Peer and network analysis
    peer_organizations ProPublicaPeerOrganization[] @description("Similar organizations found")
    peer_analysis_summary string? @description("Summary of peer organization landscape")
    network_centrality_score float? @description("Organization's position in nonprofit network")

    // API metadata
    api_last_updated string? @description("When ProPublica data was last updated")
    data_completeness_score float @description("Overall data completeness (0.0-1.0)")
    enrichment_timestamp string @description("When this enrichment was performed")
    api_response_time_ms float @description("Time taken for API calls")
}

// =====================================================================================
// OUTPUT CONTRACTS - EXECUTION RESULTS
// =====================================================================================

class ProPublicaExecutionMetadata {
    execution_time_ms float @description("Total execution time in milliseconds")
    api_calls_made int @description("Number of ProPublica API calls made")
    cache_hits int @description("Number of cache hits during execution")
    cache_hit_rate float @description("Percentage of requests served from cache")
    organizations_processed int @description("Number of organizations successfully processed")
    organizations_failed int @description("Number of organizations that failed processing")
    rate_limit_delays_ms float @description("Total time spent in rate limiting delays")

    // Performance tracking
    avg_api_response_time_ms float @description("Average API response time")
    peer_organizations_discovered int @description("Total peer organizations discovered")
    filing_documents_accessed int @description("Total filing documents accessed")

    // Quality metrics
    avg_data_completeness float @description("Average data completeness across organizations")
    enrichment_success_rate float @description("Percentage of successful enrichments")
}

class ProPublicaQualityAssessment {
    overall_quality_score float @description("Overall quality of enriched data (0.0-1.0)")
    api_data_freshness float @description("How recent the ProPublica data is (0.0-1.0)")
    cross_validation_score float @description("Consistency with BMF/990 database data")

    // Quality insights
    high_quality_profiles int @description("Number of profiles with >80% completeness")
    data_gaps_identified string[] @description("Common data gaps found")
    enrichment_recommendations string[] @description("Recommendations for improving data quality")
}

class ProPublicaEnrichmentSummary {
    total_organizations_enriched int @description("Total organizations successfully enriched")
    enrichment_depth_achieved EnrichmentDepth @description("Actual depth of enrichment achieved")
    peer_analysis_summary string @description("Summary of peer organization analysis")
    leadership_insights_summary string @description("Key insights about organizational leadership")
    program_analysis_summary string @description("Summary of program activities analysis")

    // Coverage statistics
    filing_coverage_years int @description("Average years of filing history obtained")
    leadership_coverage_rate float @description("Percentage of orgs with leadership data")
    program_coverage_rate float @description("Percentage of orgs with program details")
    peer_coverage_rate float @description("Percentage of orgs with peer analysis")

    // Value-added insights
    key_findings string[] @description("Key findings from the enrichment process")
    comparative_insights string[] @description("Insights from peer organization comparisons")
    strategic_recommendations string[] @description("Strategic recommendations based on enriched data")
}

// =====================================================================================
// FINAL RESULT CONTRACT
// =====================================================================================

class ProPublicaEnrichmentResult {
    // Core results
    enriched_organizations ProPublicaOrganizationProfile[] @description("Fully enriched organization profiles")

    // Execution and performance data
    execution_metadata ProPublicaExecutionMetadata @description("Execution performance and API usage metrics")

    // Quality assessment
    quality_assessment ProPublicaQualityAssessment @description("Data quality and reliability assessment")

    // Summary and insights
    enrichment_summary ProPublicaEnrichmentSummary @description("High-level summary and strategic insights")

    // Integration metadata
    source_tool_chain string @description("Tools used in sequence (e.g., 'BMF→990→ProPublica')")
    workflow_integration_data string? @description("Data for workflow orchestration and persistence")
}