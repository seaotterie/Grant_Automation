/**
 * Government Funding Criteria Data
 * Federal/State/Local opportunity filtering criteria
 *
 * Structure: 6 categories with multiple criteria options
 * Usage: Profile configuration, government opportunity discovery
 */

const GOVERNMENT_CRITERIA = {
    'funding_instruments': {
        category: 'Funding Instruments',
        description: 'Types of federal funding mechanisms',
        criteria: [
            { id: 'grant', name: 'Grants', description: 'Direct financial assistance for specific projects', sources: ['Federal', 'State', 'Local'] },
            { id: 'cooperative_agreement', name: 'Cooperative Agreements', description: 'Partnerships with substantial federal involvement', sources: ['Federal'] },
            { id: 'contract', name: 'Contracts', description: 'Procurement contracts for goods/services', sources: ['Federal', 'State', 'Local'] },
            { id: 'other', name: 'Other Instruments', description: 'Alternative funding mechanisms', sources: ['Federal', 'State'] }
        ]
    },
    'eligibility': {
        category: 'Applicant Eligibility',
        description: 'Types of organizations eligible to apply',
        criteria: [
            { id: 'nonprofit', name: 'Nonprofit Organizations', description: '501(c)(3) and other nonprofits', sources: ['Federal', 'State', 'Local'] },
            { id: 'state_government', name: 'State Governments', description: 'State-level government entities', sources: ['Federal'] },
            { id: 'local_government', name: 'Local Governments', description: 'Cities, counties, municipalities', sources: ['Federal', 'State'] },
            { id: 'tribal_government', name: 'Tribal Governments', description: 'Native American tribal organizations', sources: ['Federal'] },
            { id: 'university', name: 'Universities', description: 'Higher education institutions', sources: ['Federal', 'State'] },
            { id: 'for_profit', name: 'For-Profit Companies', description: 'Commercial businesses', sources: ['Federal', 'State', 'Local'] },
            { id: 'individual', name: 'Individuals', description: 'Individual applicants', sources: ['Federal', 'State'] }
        ]
    },
    'agencies': {
        category: 'Federal Agencies',
        description: 'Preferred federal funding agencies',
        criteria: [
            { id: 'HHS', name: 'Health & Human Services', description: 'CDC, NIH, HRSA, ACF, etc.', sources: ['Federal'] },
            { id: 'ED', name: 'Department of Education', description: 'Education programs and research', sources: ['Federal'] },
            { id: 'USDA', name: 'Agriculture Department', description: 'Rural development, nutrition programs', sources: ['Federal'] },
            { id: 'DOL', name: 'Department of Labor', description: 'Workforce development programs', sources: ['Federal'] },
            { id: 'HUD', name: 'Housing & Urban Development', description: 'Community development, housing', sources: ['Federal'] },
            { id: 'EPA', name: 'Environmental Protection Agency', description: 'Environmental programs', sources: ['Federal'] },
            { id: 'NSF', name: 'National Science Foundation', description: 'Scientific research funding', sources: ['Federal'] },
            { id: 'DOD', name: 'Department of Defense', description: 'Defense-related research', sources: ['Federal'] },
            { id: 'DHS', name: 'Homeland Security', description: 'Security and emergency programs', sources: ['Federal'] },
            { id: 'DOT', name: 'Transportation', description: 'Transportation infrastructure', sources: ['Federal'] }
        ]
    },
    'award_amounts': {
        category: 'Award Amount Ranges',
        description: 'Preferred funding amount ranges',
        criteria: [
            { id: 'small', name: 'Small Awards ($1K - $25K)', description: 'Small project funding', sources: ['Federal', 'State', 'Local'] },
            { id: 'medium', name: 'Medium Awards ($25K - $100K)', description: 'Standard program funding', sources: ['Federal', 'State', 'Local'] },
            { id: 'large', name: 'Large Awards ($100K - $500K)', description: 'Major initiative funding', sources: ['Federal', 'State'] },
            { id: 'very_large', name: 'Very Large Awards ($500K+)', description: 'Large-scale programs', sources: ['Federal'] }
        ]
    },
    'geographic_scope': {
        category: 'Geographic Eligibility',
        description: 'Geographic limitations and preferences',
        criteria: [
            { id: 'national', name: 'National Eligibility', description: 'Open to all US organizations', sources: ['Federal'] },
            { id: 'regional', name: 'Regional Programs', description: 'Multi-state regional initiatives', sources: ['Federal', 'State'] },
            { id: 'state_specific', name: 'State-Specific', description: 'Limited to specific states', sources: ['State'] },
            { id: 'local_focus', name: 'Local Focus', description: 'Community-level programs', sources: ['Local', 'State'] },
            { id: 'rural_priority', name: 'Rural Priority', description: 'Preference for rural areas', sources: ['Federal', 'State'] },
            { id: 'urban_priority', name: 'Urban Priority', description: 'Focus on urban communities', sources: ['Federal', 'State', 'Local'] }
        ]
    },
    'program_categories': {
        category: 'Program Categories',
        description: 'CFDA and program focus areas',
        criteria: [
            { id: 'health', name: 'Health Programs', description: 'Public health, medical research', sources: ['Federal', 'State', 'Local'] },
            { id: 'education', name: 'Education', description: 'K-12, higher education, training', sources: ['Federal', 'State', 'Local'] },
            { id: 'social_services', name: 'Social Services', description: 'Human services, community support', sources: ['Federal', 'State', 'Local'] },
            { id: 'environment', name: 'Environmental', description: 'Conservation, sustainability', sources: ['Federal', 'State', 'Local'] },
            { id: 'economic_development', name: 'Economic Development', description: 'Job creation, business support', sources: ['Federal', 'State', 'Local'] },
            { id: 'research', name: 'Research & Development', description: 'Scientific research programs', sources: ['Federal'] },
            { id: 'infrastructure', name: 'Infrastructure', description: 'Transportation, utilities, facilities', sources: ['Federal', 'State', 'Local'] },
            { id: 'technology', name: 'Technology', description: 'IT, innovation, digital programs', sources: ['Federal', 'State'] },
            { id: 'arts_culture', name: 'Arts & Culture', description: 'Cultural programs, humanities', sources: ['Federal', 'State', 'Local'] },
            { id: 'disaster_relief', name: 'Disaster Relief', description: 'Emergency response, recovery', sources: ['Federal', 'State', 'Local'] }
        ]
    }
};

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { GOVERNMENT_CRITERIA };
}
