// Use Case 1: Organization Profile Intelligence Schema
// For building and enriching nonprofit organization profiles

enum VerificationStatus {
    VERIFIED_990    // Verified against 990 tax filing
    WEB_ONLY        // Found on website only, not in 990
    CONFLICTING     // Web data conflicts with 990
    UNKNOWN         // Unable to verify
}

enum DataQuality {
    EXCELLENT  // 0.9-1.0
    GOOD       // 0.7-0.89
    FAIR       // 0.5-0.69
    POOR       // <0.5
}

class ProgramArea {
    name string
    description string
    target_population string?
    geographic_scope string[]?
    budget_estimate float?  // If available on website
    outcomes string[]?      // Stated outcomes/impact
}

class LeadershipEntry {
    name string
    title string
    bio string?
    email string?
    phone string?
    linkedin_url string?

    // 990 Verification
    verification_status VerificationStatus
    matches_990 bool

    // If from 990
    compensation_990 float?
    average_hours_per_week float?
}

class ContactInformation {
    mailing_address string?
    physical_address string?
    city string?
    state string?
    zip_code string?
    phone string?
    email string?
    social_media_links map<string, string>?  // platform -> URL
}

class FinancialSummary {
    annual_budget float?
    revenue_sources string[]?
    recent_fiscal_year int?

    // Verification against 990
    budget_matches_990 bool?
    budget_990_value float?
    fiscal_year_990 int?
}

class ScrapingMetadata {
    pages_scraped int
    pages_attempted int
    scraping_duration_seconds float
    scraping_timestamp string  // ISO format

    // Quality metrics
    data_quality_score float  // 0.0-1.0
    data_quality DataQuality
    verification_confidence float  // 0.0-1.0 (how well web data matches 990)

    // URL resolution
    url_scraped string
    url_source string  // "user_provided", "990_declared", "gpt_predicted"
    url_confidence float

    // Extraction success rates
    mission_extracted bool
    programs_extracted bool
    leadership_extracted bool
    contact_extracted bool
    financial_extracted bool
}

class OrganizationIntelligence {
    // Core identification
    ein string
    organization_name string
    website_url string

    // Profile data
    mission_statement string?
    vision_statement string?
    programs ProgramArea[]
    leadership LeadershipEntry[]
    contact_info ContactInformation?
    financial_info FinancialSummary?

    // Additional enrichment
    founded_year int?
    service_area string[]?
    target_populations string[]?
    key_achievements string[]?
    current_initiatives string[]?

    // Metadata
    scraping_metadata ScrapingMetadata

    // Errors/warnings
    extraction_errors string[]?
    validation_warnings string[]?
}
