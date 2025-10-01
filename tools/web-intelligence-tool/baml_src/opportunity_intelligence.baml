// Use Case 2: Opportunity Research Schema
// For researching grantmaking nonprofit organizations
// Examples: United Way chapters, community foundations, nonprofit grantmakers

class GrantProgram {
    program_name string
    description string
    funding_amount_range string?  // e.g., "$5,000-$25,000"
    typical_award_size float?
    eligibility_criteria string[]?
    application_process string?
    deadlines string?
    funding_priorities string[]?
    geographic_restrictions string[]?
}

class ApplicationRequirement {
    requirement_type string  // "document", "form", "eligibility", "deadline"
    description string
    mandatory bool
    submission_details string?
}

class FundingPriority {
    priority_area string
    description string
    examples string[]?
    preferred_population string[]?
    geographic_focus string[]?
}

class GrantAwarded {
    recipient_name string?
    grant_amount float?
    grant_year int?
    grant_purpose string?
    source string  // "annual report", "990 Schedule I", "website", etc.
}

class OpportunityIntelligence {
    // Core identification
    ein string
    organization_name string
    website_url string
    organization_type string  // "community_foundation", "united_way", "grantmaking_nonprofit"

    // Grant opportunity information
    grant_programs GrantProgram[]
    application_requirements ApplicationRequirement[]
    funding_priorities FundingPriority[]

    // Historical grant data
    grants_awarded GrantAwarded[]  // From website/annual reports
    total_grants_awarded float?
    average_grant_size float?
    grant_range_low float?
    grant_range_high float?

    // Application details
    application_deadline string?
    application_url string?
    contact_person string?
    contact_email string?
    contact_phone string?

    // Verification (990 Schedule I)
    schedule_i_verification bool?
    schedule_i_grants_count int?
    schedule_i_total_amount float?
    verification_confidence float?  // 0.0-1.0

    // Geographic scope
    service_area string[]?
    geographic_restrictions string[]?

    // Metadata
    pages_scraped int
    scraping_duration_seconds float
    data_quality_score float
    scraping_timestamp string  // ISO format

    // Errors/warnings
    extraction_errors string[]?
    validation_warnings string[]?
}
