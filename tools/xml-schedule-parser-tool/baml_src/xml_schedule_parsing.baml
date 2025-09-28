// XML Schedule Parser Tool - BAML Schema
// Human Layer 12-Factor Agents Framework - Factor 4: Tools as Structured Outputs

// Input: Criteria for XML schedule parsing
class XMLScheduleCriteria {
    target_eins string[]                  // List of EINs to parse XML schedules for
    schedules_to_extract string[]        // Schedules to extract ["I", "J", "K", "A", "B"]
    cache_enabled bool                    // Whether to use cached XML files
    max_years_back int                    // Maximum years to look back for XML files
    download_if_missing bool              // Whether to download XML if not cached
}

// Schedule I: Grants and assistance made to organizations
class GrantRecord {
    ein string                           // EIN of the organization making the grant
    recipient_name string                // Name of grant recipient
    recipient_ein string?                // EIN of recipient (if available)
    grant_amount float                   // Amount of grant
    grant_purpose string?                // Purpose of the grant
    recipient_address string?            // Address of recipient
    relationship_description string?     // Relationship to grantmaker
    tax_year int                        // Year of the grant
    schedule_part string                // "I" for Schedule I
}

// Schedule J: Board member compensation and relationships
class BoardMember {
    ein string                           // EIN of the organization
    person_name string                   // Name of board member/officer
    title string                        // Title or position
    compensation float?                  // Total compensation received
    benefits float?                      // Benefits and other compensation
    expense_account float?               // Expense account allowances
    hours_per_week float?               // Average hours per week
    relationship_description string?     // Relationship to organization
    tax_year int                        // Year of the data
    schedule_part string                // "J" for Schedule J
}

// Schedule K: Supplemental financial information
class SupplementalFinancialData {
    ein string                           // EIN of the organization
    tax_year int                        // Tax year
    supplemental_data map<string, string> // Key-value pairs of supplemental data
    financial_metrics map<string, float>  // Numeric financial metrics
    compliance_indicators map<string, bool> // Yes/No compliance indicators
    schedule_part string                 // "K" for Schedule K
}

// XML file processing metadata
class XMLFileMetadata {
    ein string                           // EIN of the organization
    object_id string                     // ProPublica object_id for the file
    file_path string                     // Local path to cached XML file
    file_size_bytes int                  // Size of the XML file
    download_timestamp string            // When the file was downloaded
    tax_year int                        // Tax year of the filing
    form_type string                    // Type of form (990, 990-PF, 990-EZ)
    xml_namespaces string[]             // XML namespaces found in the file
    parsing_success bool                // Whether parsing was successful
    parsing_errors string[]             // Any errors encountered during parsing
}

// XML download and parsing execution metadata
class XMLExecutionMetadata {
    execution_time_ms float
    organizations_processed int
    xml_files_found int
    xml_files_downloaded int
    xml_files_parsed int
    cache_hits int
    cache_misses int
    cache_hit_rate float
    total_schedules_extracted int
    parsing_errors int
    download_errors int
    object_id_discovery_time_ms float
    xml_download_time_ms float
    schedule_parsing_time_ms float
}

// Quality assessment for XML schedule parsing
class XMLQualityAssessment {
    overall_success_rate float           // Percentage of successful extractions
    schedule_coverage_rate float         // Percentage of requested schedules found
    data_completeness_average float      // Average completeness of extracted data
    xml_file_freshness_score float       // How recent the XML files are
    parsing_reliability_score float      // Reliability of the parsing process
    limitation_notes string[]            // Any limitations or issues encountered
}

// Output: Complete XML schedule parsing result
class XMLScheduleResult {
    schedule_i_grants GrantRecord[]      // Grants made (Schedule I)
    schedule_j_board BoardMember[]       // Board member data (Schedule J)
    schedule_k_supplemental SupplementalFinancialData[] // Supplemental data (Schedule K)
    xml_files_processed XMLFileMetadata[]
    execution_metadata XMLExecutionMetadata
    quality_assessment XMLQualityAssessment
    tool_name string                     // "XML Schedule Parser Tool"
    framework_compliance string          // "Human Layer 12-Factor Agents"
    factor_4_implementation string       // "Tools as Structured Outputs - eliminates XML parsing errors"
    organizations_processed int
    schedules_extracted int
    extraction_failures int
}