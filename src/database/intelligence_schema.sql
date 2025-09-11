-- =====================================================================================
-- DEEP INTELLIGENCE DATABASE SCHEMA
-- Enhanced Web Scraping & Intelligence Storage System
-- Created: September 11, 2025
-- =====================================================================================
-- This schema stores comprehensive intelligence data gathered from web scraping,
-- board member analysis, and organizational research activities.
-- Designed to avoid cross-contamination with existing BMF/SOI financial data.

-- =====================================================================================
-- ORGANIZATION URLs CACHE TABLE
-- =====================================================================================
-- Stores discovered URLs for organizations to avoid repeated GPT API calls
-- Links to BMF organizations via EIN for authoritative data consistency

CREATE TABLE IF NOT EXISTS organization_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,                         -- Links to bmf_organizations.ein
    organization_name TEXT NOT NULL,           -- Organization name from BMF
    predicted_url TEXT NOT NULL,               -- GPT-predicted URL
    url_status TEXT DEFAULT 'pending',         -- 'pending', 'verified', 'failed', 'error'
    http_status_code INTEGER,                  -- HTTP response code (200, 404, etc.)
    discovery_method TEXT DEFAULT 'gpt_api',   -- 'gpt_api', 'manual', 'crawled'
    discovery_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified TIMESTAMP,                   -- Last successful verification
    verification_attempts INTEGER DEFAULT 0,   -- Number of verification attempts
    notes TEXT,                               -- Additional discovery notes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(ein)                              -- One URL per organization
);

-- Organization URLs indexes
CREATE INDEX IF NOT EXISTS idx_org_urls_status ON organization_urls(url_status);
CREATE INDEX IF NOT EXISTS idx_org_urls_discovery_date ON organization_urls(discovery_date);

-- =====================================================================================
-- WEB INTELLIGENCE CACHE TABLE  
-- =====================================================================================
-- Stores structured intelligence data extracted from websites
-- Comprehensive data structure supporting leadership, programs, contacts, mission

CREATE TABLE IF NOT EXISTS web_intelligence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,                         -- Links to organization
    url TEXT NOT NULL,                         -- Source URL for this intelligence
    scrape_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Intelligence Quality Metrics
    intelligence_quality_score INTEGER,        -- 0-100 quality score
    content_richness_score REAL,              -- Content richness metric
    pages_scraped INTEGER DEFAULT 1,           -- Number of pages analyzed
    total_content_length INTEGER,              -- Total character count
    
    -- Structured Leadership Data (JSON)
    leadership_data TEXT,                      -- JSON: [{name, title, bio, contact}]
    leadership_count INTEGER DEFAULT 0,        -- Number of leadership entries
    
    -- Structured Program Data (JSON)  
    program_data TEXT,                         -- JSON: [{name, description, focus_area}]
    program_count INTEGER DEFAULT 0,           -- Number of programs identified
    
    -- Contact Information (JSON)
    contact_data TEXT,                         -- JSON: {phone, email, address, social}
    
    -- Mission and Strategic Information
    mission_statements TEXT,                   -- JSON: [mission_text_1, mission_text_2]
    mission_count INTEGER DEFAULT 0,           -- Number of mission statements
    
    -- Additional Intelligence Fields
    key_focus_areas TEXT,                      -- Comma-separated focus areas
    geographic_scope TEXT,                     -- Geographic service area
    target_populations TEXT,                   -- Target beneficiary populations
    partnership_mentions TEXT,                -- JSON: [partnership_description]
    
    -- Website Technical Data
    website_structure_quality TEXT,            -- 'excellent', 'good', 'poor', 'minimal'
    navigation_complexity TEXT,                -- 'simple', 'moderate', 'complex'
    content_freshness TEXT,                    -- 'current', 'recent', 'outdated'
    
    -- Processing Metadata
    processor_version TEXT DEFAULT '1.0',      -- Processing algorithm version
    processing_duration_ms INTEGER,            -- Processing time in milliseconds
    error_messages TEXT,                       -- Any errors encountered during scraping
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Web intelligence indexes
CREATE INDEX IF NOT EXISTS idx_web_intel_ein ON web_intelligence(ein);
CREATE INDEX IF NOT EXISTS idx_web_intel_scrape_date ON web_intelligence(scrape_date);
CREATE INDEX IF NOT EXISTS idx_web_intel_quality ON web_intelligence(intelligence_quality_score);
CREATE INDEX IF NOT EXISTS idx_web_intel_richness ON web_intelligence(leadership_count, program_count);

-- =====================================================================================
-- BOARD MEMBER INTELLIGENCE TABLE
-- =====================================================================================  
-- Stores comprehensive board member data from multiple sources:
-- 1. Web scraping results (from web_intelligence.leadership_data)
-- 2. 990/990PF filings via ProPublica API
-- 3. Board Network Analyzer results

CREATE TABLE IF NOT EXISTS board_member_intelligence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,                         -- Organization EIN
    
    -- Member Identification
    member_name TEXT NOT NULL,                 -- Full name as reported
    normalized_name TEXT NOT NULL,             -- Normalized for matching
    title_position TEXT,                       -- Board position/title
    
    -- Data Sources
    data_source TEXT NOT NULL,                 -- 'web_scraping', '990_filing', 'network_analysis'
    source_confidence TEXT DEFAULT 'medium',   -- 'high', 'medium', 'low'
    
    -- Member Details (from web scraping)
    biography TEXT,                           -- Biography/background information
    professional_background TEXT,            -- Career/professional details
    education_background TEXT,               -- Educational background
    other_affiliations TEXT,                 -- Other board memberships (JSON)
    
    -- Contact Information
    contact_email TEXT,                      -- Email if publicly available
    linkedin_profile TEXT,                  -- LinkedIn URL if found
    professional_website TEXT,              -- Personal/professional website
    
    -- Network Analysis Data
    network_centrality_score REAL,          -- Centrality in board network
    cross_board_connections INTEGER DEFAULT 0, -- Number of other boards served
    influence_score REAL,                   -- Calculated influence metric
    
    -- 990 Filing Data Integration
    compensation_amount INTEGER,             -- From 990 filings if available
    is_voting_member BOOLEAN,               -- Voting rights (990 data)
    hours_per_week REAL,                    -- Time commitment (990 data)
    
    -- Temporal Data
    start_date DATE,                        -- Start of service (if available)
    end_date DATE,                          -- End of service (if applicable)
    tenure_years INTEGER,                   -- Calculated tenure
    
    -- Quality and Verification
    data_quality_score INTEGER,            -- 0-100 data completeness score
    last_verified TIMESTAMP,               -- Last verification date
    verification_method TEXT,              -- How data was verified
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Board member intelligence indexes
CREATE INDEX IF NOT EXISTS idx_board_intel_ein ON board_member_intelligence(ein);
CREATE INDEX IF NOT EXISTS idx_board_intel_name ON board_member_intelligence(normalized_name);
CREATE INDEX IF NOT EXISTS idx_board_intel_source ON board_member_intelligence(data_source);
CREATE INDEX IF NOT EXISTS idx_board_intel_influence ON board_member_intelligence(network_centrality_score DESC);
CREATE INDEX IF NOT EXISTS idx_board_intel_connections ON board_member_intelligence(cross_board_connections DESC);
CREATE INDEX IF NOT EXISTS idx_board_intel_org_source ON board_member_intelligence(ein, data_source);
CREATE INDEX IF NOT EXISTS idx_board_intel_name_ein ON board_member_intelligence(normalized_name, ein);

-- =====================================================================================
-- INTELLIGENCE PROCESSING LOG TABLE
-- =====================================================================================
-- Tracks all intelligence gathering activities for audit and performance monitoring

CREATE TABLE IF NOT EXISTS intelligence_processing_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,                         -- Organization EIN
    processing_type TEXT NOT NULL,             -- 'url_discovery', 'web_scraping', 'board_analysis'
    
    -- Processing Details
    status TEXT NOT NULL,                      -- 'success', 'partial', 'failed', 'error'
    start_time TIMESTAMP NOT NULL,             -- Processing start
    end_time TIMESTAMP,                        -- Processing completion
    duration_ms INTEGER,                       -- Processing duration
    
    -- Results Summary
    data_points_extracted INTEGER DEFAULT 0,   -- Number of data points found
    quality_score INTEGER,                     -- Overall quality of results
    pages_processed INTEGER,                   -- Pages scraped/analyzed
    
    -- Cost and Resource Usage
    api_calls_made INTEGER DEFAULT 0,          -- API calls (GPT, ProPublica)
    api_cost_cents INTEGER DEFAULT 0,          -- Cost in cents
    network_requests INTEGER DEFAULT 0,        -- HTTP requests made
    
    -- Error Handling
    error_type TEXT,                           -- Error category if failed
    error_message TEXT,                        -- Detailed error message
    retry_count INTEGER DEFAULT 0,             -- Number of retries attempted
    
    -- Configuration Used
    processor_config TEXT,                     -- JSON of processing configuration
    model_version TEXT,                        -- AI model version used
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Processing log indexes
CREATE INDEX IF NOT EXISTS idx_processing_log_ein_type ON intelligence_processing_log(ein, processing_type);
CREATE INDEX IF NOT EXISTS idx_processing_log_status ON intelligence_processing_log(status);
CREATE INDEX IF NOT EXISTS idx_processing_log_time ON intelligence_processing_log(start_time);
CREATE INDEX IF NOT EXISTS idx_processing_log_cost ON intelligence_processing_log(api_cost_cents);

-- =====================================================================================
-- INTELLIGENT DISCOVERY RESULTS TABLE
-- =====================================================================================
-- Stores enhanced discovery results that combine BMF data with web intelligence
-- Links discovered organizations with their intelligence quality metrics

CREATE TABLE IF NOT EXISTS intelligent_discovery_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discovery_session_id TEXT NOT NULL,       -- Session identifier for batch discovery
    ein TEXT NOT NULL,                        -- Organization EIN
    
    -- Discovery Context
    profile_id TEXT,                          -- Source profile ID that triggered discovery
    discovery_criteria TEXT,                 -- JSON of search criteria used
    discovery_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Organization Match Data
    bmf_match_confidence REAL,               -- Confidence in BMF match (0-1)
    web_presence_found BOOLEAN DEFAULT FALSE, -- Whether website was found
    intelligence_gathered BOOLEAN DEFAULT FALSE, -- Whether scraping succeeded
    
    -- Intelligence Quality Summary
    overall_intelligence_score INTEGER,       -- Combined intelligence score 0-100
    leadership_intelligence_score INTEGER,    -- Leadership data quality 0-100
    program_intelligence_score INTEGER,       -- Program data quality 0-100
    contact_intelligence_score INTEGER,       -- Contact data quality 0-100
    
    -- Strategic Value Assessment
    strategic_alignment_score REAL,          -- Alignment with discovery criteria
    partnership_potential TEXT,              -- 'high', 'medium', 'low', 'unknown'
    grant_opportunity_indicators INTEGER,     -- Number of grant-related signals
    
    -- Financial Intelligence Integration
    latest_revenue INTEGER,                   -- From BMF/990 data
    assets_value INTEGER,                     -- From BMF/990 data
    grant_making_capacity INTEGER,            -- From 990-PF data if foundation
    
    -- Geographic and Operational Scope
    service_area_overlap BOOLEAN,            -- Geographic overlap with profile
    program_area_matches INTEGER,            -- Number of program area matches
    target_population_overlap TEXT,          -- Population overlap assessment
    
    -- Recommendation Flags
    recommended_for_outreach BOOLEAN DEFAULT FALSE,
    priority_level TEXT DEFAULT 'medium',    -- 'high', 'medium', 'low'
    next_action_recommended TEXT,            -- Suggested follow-up action
    
    -- Audit and Performance
    processing_duration_ms INTEGER,          -- Total processing time
    api_costs_cents INTEGER DEFAULT 0,       -- Total API costs for this result
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Discovery results indexes
CREATE INDEX IF NOT EXISTS idx_discovery_session ON intelligent_discovery_results(discovery_session_id);
CREATE INDEX IF NOT EXISTS idx_discovery_profile ON intelligent_discovery_results(profile_id);
CREATE INDEX IF NOT EXISTS idx_discovery_intelligence ON intelligent_discovery_results(overall_intelligence_score DESC);
CREATE INDEX IF NOT EXISTS idx_discovery_alignment ON intelligent_discovery_results(strategic_alignment_score DESC);
CREATE INDEX IF NOT EXISTS idx_discovery_recommendations ON intelligent_discovery_results(recommended_for_outreach);
CREATE INDEX IF NOT EXISTS idx_discovery_priority ON intelligent_discovery_results(priority_level, discovery_date);
CREATE INDEX IF NOT EXISTS idx_discovery_ein_session ON intelligent_discovery_results(ein, discovery_session_id);
CREATE INDEX IF NOT EXISTS idx_discovery_profile_rec ON intelligent_discovery_results(profile_id, recommended_for_outreach);

-- =====================================================================================
-- VIEWS FOR COMMON INTELLIGENCE QUERIES
-- =====================================================================================

-- Comprehensive organization intelligence view
CREATE VIEW IF NOT EXISTS v_organization_intelligence AS
SELECT 
    u.ein,
    u.organization_name,
    u.predicted_url,
    u.url_status,
    
    -- Web intelligence summary
    wi.intelligence_quality_score,
    wi.leadership_count,
    wi.program_count,
    wi.pages_scraped,
    wi.scrape_date,
    
    -- Board member summary
    COUNT(DISTINCT bmi.id) as board_members_identified,
    AVG(bmi.network_centrality_score) as avg_board_influence,
    MAX(bmi.cross_board_connections) as max_cross_connections,
    
    -- Processing summary
    COUNT(DISTINCT ipl.id) as processing_attempts,
    MAX(ipl.start_time) as last_processing_attempt,
    SUM(ipl.api_cost_cents) as total_api_costs
    
FROM organization_urls u
LEFT JOIN web_intelligence wi ON u.ein = wi.ein
LEFT JOIN board_member_intelligence bmi ON u.ein = bmi.ein
LEFT JOIN intelligence_processing_log ipl ON u.ein = ipl.ein
GROUP BY u.ein, u.organization_name, u.predicted_url, u.url_status,
         wi.intelligence_quality_score, wi.leadership_count, wi.program_count, 
         wi.pages_scraped, wi.scrape_date;

-- High-value intelligence targets view
CREATE VIEW IF NOT EXISTS v_high_value_intelligence AS
SELECT 
    oi.*,
    bmf.ntee_code,
    bmf.state,
    bmf.revenue_amt,
    
    -- Intelligence completeness indicators
    CASE 
        WHEN oi.intelligence_quality_score >= 80 THEN 'Excellent'
        WHEN oi.intelligence_quality_score >= 60 THEN 'Good' 
        WHEN oi.intelligence_quality_score >= 40 THEN 'Moderate'
        ELSE 'Limited'
    END as intelligence_tier,
    
    -- Strategic value indicators
    (oi.leadership_count * 10 + oi.program_count * 5 + 
     COALESCE(oi.board_members_identified, 0) * 3) as strategic_value_score
     
FROM v_organization_intelligence oi
LEFT JOIN bmf_organizations bmf ON oi.ein = bmf.ein
WHERE oi.url_status = 'verified' 
  AND oi.intelligence_quality_score > 30;

-- =====================================================================================
-- PERFORMANCE INDEXES FOR INTELLIGENCE QUERIES
-- =====================================================================================

-- Cross-table relationship indexes
CREATE INDEX IF NOT EXISTS idx_web_intel_quality_date ON web_intelligence(intelligence_quality_score DESC, scrape_date DESC);
CREATE INDEX IF NOT EXISTS idx_board_member_influence ON board_member_intelligence(network_centrality_score DESC, cross_board_connections DESC);
CREATE INDEX IF NOT EXISTS idx_discovery_strategic_value ON intelligent_discovery_results(strategic_alignment_score DESC, overall_intelligence_score DESC);

-- Processing performance indexes  
CREATE INDEX IF NOT EXISTS idx_processing_log_performance ON intelligence_processing_log(duration_ms, api_calls_made, api_cost_cents);
CREATE INDEX IF NOT EXISTS idx_url_cache_performance ON organization_urls(url_status, last_verified, verification_attempts);

-- Multi-column indexes for complex discovery queries
CREATE INDEX IF NOT EXISTS idx_discovery_recommendations ON intelligent_discovery_results(
    recommended_for_outreach, 
    priority_level, 
    overall_intelligence_score DESC,
    discovery_date DESC
);

-- =====================================================================================
-- TRIGGERS FOR DATA CONSISTENCY AND AUDIT
-- =====================================================================================

-- Update timestamp trigger for organization_urls
CREATE TRIGGER IF NOT EXISTS trg_update_org_urls_timestamp 
    AFTER UPDATE ON organization_urls
    FOR EACH ROW
BEGIN
    UPDATE organization_urls 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Update timestamp trigger for web_intelligence
CREATE TRIGGER IF NOT EXISTS trg_update_web_intel_timestamp 
    AFTER UPDATE ON web_intelligence
    FOR EACH ROW  
BEGIN
    UPDATE web_intelligence 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Update timestamp trigger for board_member_intelligence
CREATE TRIGGER IF NOT EXISTS trg_update_board_member_timestamp 
    AFTER UPDATE ON board_member_intelligence
    FOR EACH ROW
BEGIN
    UPDATE board_member_intelligence 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- =====================================================================================
-- DATA MIGRATION AND COMPATIBILITY FUNCTIONS
-- =====================================================================================

-- Function to migrate existing URL cache data (if any)
-- Note: This would be implemented in Python migration scripts

-- Sample data quality check queries for validation:
/*
-- Validate data consistency
SELECT 'URL Cache Status' as check_type, url_status, COUNT(*) as count
FROM organization_urls GROUP BY url_status;

SELECT 'Intelligence Quality Distribution' as check_type, 
       CASE 
           WHEN intelligence_quality_score >= 80 THEN '80-100'
           WHEN intelligence_quality_score >= 60 THEN '60-79'
           WHEN intelligence_quality_score >= 40 THEN '40-59'
           WHEN intelligence_quality_score >= 20 THEN '20-39'
           ELSE '0-19'
       END as quality_range,
       COUNT(*) as count
FROM web_intelligence GROUP BY quality_range;

SELECT 'Board Member Data Sources' as check_type, data_source, COUNT(*) as count
FROM board_member_intelligence GROUP BY data_source;
*/

-- =====================================================================================
-- SUMMARY
-- =====================================================================================
-- This intelligence schema provides:
-- 
-- 1. **URL Discovery Cache**: Stores GPT-predicted URLs with verification status
-- 2. **Web Intelligence Storage**: Comprehensive scraped data with quality scoring  
-- 3. **Board Member Intelligence**: Multi-source board data with network analysis
-- 4. **Processing Audit Trail**: Complete logging of all intelligence operations
-- 5. **Discovery Results**: Enhanced discovery with intelligence quality metrics
-- 6. **Performance Views**: Optimized views for common intelligence queries
-- 7. **Data Consistency**: Triggers and constraints for data integrity
-- 
-- **Integration Points**:
-- - Links to existing BMF database via EIN foreign keys
-- - Compatible with current BoardNetworkAnalyzer processor
-- - Supports existing web scraping and GPT discovery workflows
-- - Maintains separation from BMF/SOI financial data to avoid cross-contamination
--
-- **Expected Performance**: 
-- - Sub-second queries with strategic indexing
-- - Scalable to 100K+ organizations with full intelligence data
-- - Efficient storage of JSON data for flexible structured information