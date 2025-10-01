// Use Case 2: Competitor/Peer Nonprofit Research Schema
// For analyzing competitive landscape and peer organizations

class GrantReceived {
    funder_name string
    grant_amount float?
    grant_year int?
    grant_purpose string?
    source string  // Where this was found (press release, annual report, etc.)
}

class FundingSource {
    source_name string
    source_type string  // "foundation", "corporate", "government", "individual", "earned_income"
    amount float?
    percentage_of_total float?
    relationship_type string?  // "major donor", "corporate sponsor", "grant", etc.
}

class PeerProgram {
    program_name string
    description string
    target_population string?
    service_overlap_score float?  // 0.0-1.0 how much it overlaps with our programs
    notable_features string[]?
}

class ImpactMetric {
    metric_name string
    metric_value string  // Could be number, percentage, or qualitative
    metric_year int?
    source string
}

class Partnership {
    partner_name string
    partner_type string  // "nonprofit", "corporate", "government", "academic"
    partnership_description string?
    partnership_value string?  // What they get from the partnership
}

class CompetitorStrength {
    strength_category string  // "funding", "programs", "reputation", "reach", etc.
    description string
    evidence string[]  // Supporting evidence from website
}

class CompetitorIntelligence {
    // Core identification
    ein string
    organization_name string
    website_url string

    // Competitive analysis
    grants_received GrantReceived[]
    funding_sources FundingSource[]
    programs PeerProgram[]
    impact_metrics ImpactMetric[]
    partnerships Partnership[]

    // Strategic insights
    competitive_strengths CompetitorStrength[]
    service_gaps string[]?  // Services they don't provide (opportunities for us)
    differentiation_points string[]?  // How they differentiate themselves

    // Additional context
    organizational_size string?  // "small", "medium", "large" based on staff/budget
    geographic_reach string[]?
    recent_news string[]?  // Recent press releases, awards, etc.

    // Metadata
    pages_scraped int
    scraping_duration_seconds float
    data_quality_score float
    scraping_timestamp string  // ISO format

    // Errors/warnings
    extraction_errors string[]?
}
