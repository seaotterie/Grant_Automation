// XML 990 Parser Tool - BAML Schema
// Human Layer 12-Factor Agents Framework - Factor 4: Tools as Structured Outputs
// Single Responsibility: XML download and 990 form schedule parsing (Regular Nonprofits Only)

// Input: Criteria for XML 990 parsing
class XML990ParseCriteria {
    target_eins string[]                      // List of EINs to parse (must be regular nonprofits)
    schedules_to_extract string[]            // Schedules to extract: ["officers", "governance", "programs", "financials"]
    cache_enabled bool                       // Whether to use cached XML files
    max_years_back int                       // Maximum years of historical data
    download_if_missing bool                 // Download XML if not cached
    validate_990_schema bool                 // Strict validation that forms are 990 (not 990-PF or 990-EZ)
}

// Core officer/board member from Form 990 Part VII Section A
class RegularNonprofitOfficer {
    ein string
    person_name string
    title string                             // President, VP, Secretary, Treasurer, Director, etc.
    average_hours_per_week float?
    is_individual_trustee bool               // IndividualTrusteeOrDirectorInd
    is_institutional_trustee bool            // InstitutionalTrusteeInd
    is_officer bool                          // OfficerInd
    is_key_employee bool                     // KeyEmployeeInd
    is_highest_compensated bool              // HighestCompensatedEmployeeInd
    is_former_officer bool                   // FormerOfcrDirectorTrusteeInd
    reportable_comp_from_org float?          // ReportableCompFromOrgAmt
    reportable_comp_from_related_org float?  // ReportableCompFromRltdOrgAmt
    other_compensation float?                // OtherCompensationAmt
    tax_year int
    data_source string                       // "Form 990 XML"
}

// Grant or assistance record from Schedule I
class Form990GrantRecord {
    ein string
    recipient_name string
    recipient_ein string?
    recipient_address string?
    grant_amount float
    grant_purpose string?
    assistance_type string?                  // Cash, non-cash, etc.
    relationship_description string?
    tax_year int
    schedule_part string                     // "Schedule I"
}

// Contact and organizational information
class OrganizationContactInfo {
    ein string
    tax_year int
    website_url string?                      // WebsiteAddressTxt
    primary_phone string?                    // PhoneNum (primary)
    alternate_phone string?                  // PhoneNum (alternate)
    email_address string?                    // EmailAddressTxt (if available)
    formation_year int?                      // FormationYr
    legal_domicile_state string?             // LegalDomicileStateCd
    activity_mission_desc string?            // ActivityOrMissionDesc
    organization_type string?                // TypeOfOrganization indicators
    multi_state_operations string[]?        // StatesWhereCopyOfReturnIsFldCd - Geographic operations
    operational_footprint string?           // Analysis of geographic scope for grant targeting
}

// Schedule A - Public Charity Classification (Grant Eligibility Intelligence)
class Schedule990APublicCharity {
    ein string
    tax_year int
    public_charity_status bool?              // PublicOrganization170Ind - true if public charity
    public_support_percentage float?         // PublicSupportCY170Pct - % of support from public
    support_test_passed bool?                // ThirtyThrPctSuprtTestsCY170Ind - passes 33⅓% test
    total_public_support float?              // PublicSupportTotal170Amt - total public support
    total_support_amount float?              // TotalSupportAmt - total support received
    grant_eligibility_classification string? // "Public Charity" or "Private Foundation"
    grant_eligibility_confidence string?     // "High", "Medium", "Low" based on support %
}

// Schedule B - Major Contributor Intelligence (Foundation Relationship Patterns)
class Schedule990BMajorContributors {
    ein string
    tax_year int
    contributor_data_available bool          // Whether contributor info exists (even if restricted)
    major_contributor_count int?             // Number of major contributors (if available)
    contributor_information_restricted bool  // True if contributor details are redacted
    foundation_relationship_indicator bool   // Suggests institutional funding relationships
}

// Governance and management data from various Form 990 sections
class GovernanceIndicators {
    ein string
    tax_year int
    voting_members_governing_body int?       // VotingMembersGoverningBodyCnt
    independent_voting_members int?          // VotingMembersIndependentCnt
    total_employees int?                     // TotalEmployeeCnt
    total_volunteers int?                    // TotalVolunteersCnt

    // Governance policies (Part VI)
    family_or_business_relationships bool?   // FamilyOrBusinessRlnInd
    delegation_of_management_duties bool?    // DelegationOfMgmtDutiesInd
    minutes_of_governing_body bool?          // MinutesOfGoverningBodyInd
    minutes_of_committees bool?              // MinutesOfCommitteesInd
    conflict_of_interest_policy bool?        // ConflictOfInterestPolicyInd
    annual_disclosure_covered_persons bool?  // AnnualDisclosureCoveredPrsnInd
    regular_monitoring_enforcement bool?     // RegularMonitoringEnfrcInd
    whistleblower_policy bool?               // WhistleblowerPolicyInd
    document_retention_policy bool?          // DocumentRetentionPolicyInd
    compensation_process_ceo bool?           // CompensationProcessCEOInd
    compensation_process_other bool?         // CompensationProcessOtherInd
}

// Program activity from Form 990 Part III
class ProgramActivity {
    ein string
    tax_year int
    activity_sequence int                    // 1, 2, 3, or "Other"
    expense_amount float?
    description string?
    program_service_accomplishments string?
    grants_and_allocations float?
    program_service_revenue float?
}

// Financial summary from various Form 990 sections
class Form990FinancialSummary {
    ein string
    tax_year int

    // Revenue (Part VIII)
    contributions_grants_current_year float?      // CYContributionsGrantsAmt
    contributions_grants_prior_year float?        // PYContributionsGrantsAmt
    program_service_revenue_current_year float?   // CYProgramServiceRevenueAmt
    investment_income_current_year float?         // CYInvestmentIncomeAmt
    other_revenue_current_year float?             // CYOtherRevenueAmt
    total_revenue_current_year float?             // CYTotalRevenueAmt

    // Expenses (Part IX)
    program_service_expenses float?               // TotalProgramServiceExpensesAmt
    management_general_expenses float?            // ManagementAndGeneralAmt
    fundraising_expenses float?                   // FundraisingAmt
    total_expenses_current_year float?            // CYTotalExpensesAmt

    // Balance Sheet (Part X)
    total_assets_end_of_year float?               // TotalAssetsEOYAmt
    total_liabilities_end_of_year float?          // TotalLiabilitiesEOYAmt
    net_assets_end_of_year float?                 // NetAssetsOrFundBalancesEOYAmt
}

// XML file processing metadata
class XML990FileMetadata {
    ein string
    object_id string
    file_path string
    file_size_bytes int
    download_timestamp string
    tax_year int
    form_type string                         // Should be "990"
    xml_namespaces string[]
    parsing_success bool
    parsing_errors string[]
    schema_validation_passed bool            // True if confirmed to be 990 form
}

// Execution metadata
class XML990ExecutionMetadata {
    execution_time_ms float
    organizations_processed int
    xml_files_found int
    xml_files_downloaded int
    xml_files_parsed int
    schema_validation_failures int           // Files that were not 990 forms
    cache_hits int
    cache_misses int
    cache_hit_rate float
    total_officers_extracted int
    total_grants_extracted int
    parsing_errors int
    download_errors int
}

// Quality assessment
class XML990QualityAssessment {
    overall_success_rate float
    schema_validation_rate float             // Percentage of files that were valid 990 forms
    officer_data_completeness float
    financial_data_completeness float
    governance_data_completeness float
    data_freshness_score float
    limitation_notes string[]
}

// Complete XML 990 parsing result - Factor 4 structured output
class XML990Result {
    officers: RegularNonprofitOfficer[]
    grants_made: Form990GrantRecord[]
    governance_indicators: GovernanceIndicators[]
    program_activities: ProgramActivity[]
    financial_summaries: Form990FinancialSummary[]
    contact_information: OrganizationContactInfo[]
    schedule_a_public_charity: Schedule990APublicCharity[]
    schedule_b_contributors: Schedule990BMajorContributors[]
    xml_files_processed: XML990FileMetadata[]
    execution_metadata: XML990ExecutionMetadata
    quality_assessment: XML990QualityAssessment
    tool_name string                         // "XML 990 Parser Tool"
    framework_compliance string              // "Human Layer 12-Factor Agents"
    factor_4_implementation string           // "Tools as Structured Outputs - eliminates XML parsing errors"
    form_type_specialization string          // "990 Forms Only - Regular Nonprofits"
    organizations_processed int
    officers_extracted int
    grants_extracted int
    extraction_failures int
}