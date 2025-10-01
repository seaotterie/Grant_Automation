// Web Intelligence Tool - Input Schema
// Defines inputs for all 3 use cases

enum UseCase {
    PROFILE_BUILDER      // Use Case 1: Build YOUR organization profile
    OPPORTUNITY_RESEARCH // Use Case 2: Research grantmaking nonprofits (United Way, community foundations)
    FOUNDATION_RESEARCH  // Use Case 3: Research private foundations (990-PF filers)
}

class WebIntelligenceRequest {
    // Core identification
    ein string           // EIN of target organization
    organization_name string

    // Use case selector
    use_case UseCase

    // URL resolution (optional - will use SmartURLResolutionService if not provided)
    user_provided_url string?

    // Scraping configuration overrides
    max_depth int?       // Override default max_depth
    max_pages int?       // Override default max_pages_per_site

    // Verification flags
    require_990_verification bool @default(true)  // Require 990 tax filing verification
    min_confidence_score float @default(0.7)      // Minimum confidence to accept data
}
