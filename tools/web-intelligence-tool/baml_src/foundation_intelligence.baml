// Use Case 3: Foundation Grant Opportunity Research Schema
// For discovering and analyzing foundation grant opportunities

enum ApplicationStatus {
    OPEN               // Accepting applications
    CLOSED             // Not accepting applications
    INVITATION_ONLY    // By invitation only
    ROLLING            // Rolling deadlines
    SEASONAL           // Specific seasons
    UNKNOWN            // Status unclear
}

class ApplicationGuideline {
    guideline_category string  // "eligibility", "application_process", "required_documents", etc.
    guideline_text string
    requirements string[]?
    restrictions string[]?
}

class ApplicationDeadline {
    deadline_date string?  // ISO format if parseable
    deadline_description string  // "March 1st annually", "Rolling", etc.
    application_window string?  // "Open January-March"
    notification_timeline string?  // "Decisions by June 1st"
}

class FundingPriority {
    priority_area string
    description string
    geographic_focus string[]?
    population_focus string[]?
    funding_amount_range string?  // "$10,000-$50,000"
}

class FoundationTrustee {
    name string
    title string
    bio string?
    affiliations string[]?

    // 990-PF Verification
    verification_status VerificationStatus
    matches_990pf bool
    compensation_990pf float?
}

class RecentGrant {
    recipient_name string
    recipient_ein string?
    grant_amount float?
    grant_year int?
    grant_purpose string?
    geographic_location string?
}

class GrantOpportunity {
    opportunity_title string?
    opportunity_description string
    eligibility_criteria string[]
    funding_amount_range string?
    typical_grant_size float?

    // Application details
    application_process string?
    required_documents string[]?
    deadlines ApplicationDeadline?

    // Match analysis
    our_eligibility_score float?  // 0.0-1.0 how well we match
    match_reasoning string[]?
}

class FoundationIntelligence {
    // Core identification
    ein string
    foundation_name string
    website_url string
    foundation_type string?  // "private", "community", "corporate"

    // Grant opportunities
    grant_opportunities GrantOpportunity[]
    application_guidelines ApplicationGuideline[]
    funding_priorities FundingPriority[]

    // Leadership
    trustees FoundationTrustee[]
    staff_contacts string[]?  // Contact information for program officers

    // Grant-making patterns
    recent_grants RecentGrant[]
    total_grants_amount float?  // If stated on website
    grants_per_year int?
    average_grant_size float?

    // Strategic insights
    giving_focus string[]  // Primary areas of focus
    geographic_limitations string[]?
    application_status ApplicationStatus
    accepts_unsolicited bool?
    requires_letter_of_inquiry bool?

    // Additional context
    foundation_history string?
    mission_alignment_notes string[]?  // Notes on how well our mission aligns

    // Metadata
    pages_scraped int
    scraping_duration_seconds float
    data_quality_score float
    verification_confidence float  // Against 990-PF data
    scraping_timestamp string  // ISO format

    // Errors/warnings
    extraction_errors string[]?
    validation_warnings string[]?
}

// Enums referenced
enum VerificationStatus {
    VERIFIED_990PF  // Verified against 990-PF tax filing
    WEB_ONLY        // Found on website only
    CONFLICTING     // Web data conflicts with 990-PF
    UNKNOWN         // Unable to verify
}
