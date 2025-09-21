-- Fetch Operation Performance Optimization Indexes
-- Adds missing indexes specifically for data fetching operations
-- Created: September 2025

-- =====================================================================================
-- EIN-based Lookup Indexes (Critical for ProPublica and BMF fetch operations)
-- =====================================================================================

-- EIN lookups are frequent in verified intelligence and BMF operations
CREATE INDEX IF NOT EXISTS idx_profiles_ein ON profiles (ein);
CREATE INDEX IF NOT EXISTS idx_opportunities_ein ON opportunities (ein);

-- Combined profile lookups by EIN and name (for organization resolution)
CREATE INDEX IF NOT EXISTS idx_profiles_ein_name ON profiles (ein, name);
CREATE INDEX IF NOT EXISTS idx_opportunities_ein_name ON opportunities (ein, organization_name);

-- =====================================================================================
-- Organization Name Search Indexes (Web scraping and data consolidation)
-- =====================================================================================

-- Organization name lookups for data source matching
CREATE INDEX IF NOT EXISTS idx_profiles_name ON profiles (name);
CREATE INDEX IF NOT EXISTS idx_opportunities_org_name ON opportunities (organization_name);

-- Case-insensitive organization name lookups (for fuzzy matching)
CREATE INDEX IF NOT EXISTS idx_profiles_name_collate ON profiles (name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_opportunities_org_name_collate ON opportunities (organization_name COLLATE NOCASE);

-- =====================================================================================
-- Processing Status Indexes (For fetch queue management)
-- =====================================================================================

-- Processing status tracking for fetch operations
CREATE INDEX IF NOT EXISTS idx_opportunities_processing_status ON opportunities (processing_status);
CREATE INDEX IF NOT EXISTS idx_opportunities_status_date ON opportunities (processing_status, updated_at);

-- Profile status for active fetch targets
CREATE INDEX IF NOT EXISTS idx_profiles_status ON profiles (status);
CREATE INDEX IF NOT EXISTS idx_profiles_status_updated ON profiles (status, updated_at);

-- =====================================================================================
-- Source Tracking Indexes (Data source attribution)
-- =====================================================================================

-- Source tracking for data provenance (discovery track)
CREATE INDEX IF NOT EXISTS idx_opportunities_source ON opportunities (source);
CREATE INDEX IF NOT EXISTS idx_opportunities_profile_source ON opportunities (profile_id, source);

-- =====================================================================================
-- AI Processing Optimization Indexes
-- =====================================================================================

-- AI processing lookup optimization
CREATE INDEX IF NOT EXISTS idx_ai_processing_type_stage ON ai_processing_results (processor_type, processing_stage);
CREATE INDEX IF NOT EXISTS idx_ai_processing_success ON ai_processing_results (success_indicator, processed_at);

-- Cost tracking for fetch operations
CREATE INDEX IF NOT EXISTS idx_cost_tracking_profile_date ON cost_tracking (profile_id, date);

-- =====================================================================================
-- Composite Indexes for Common Fetch Patterns
-- =====================================================================================

-- Profile lookup with status and last discovery (for fetch prioritization)
CREATE INDEX IF NOT EXISTS idx_profiles_status_discovery ON profiles (status, last_discovery_date);

-- Opportunity lookup by profile and processing status (for batch fetch operations)
CREATE INDEX IF NOT EXISTS idx_opportunities_profile_processing ON opportunities (profile_id, processing_status, updated_at);

-- Opportunity lookup by stage and score (for quality-based fetch prioritization)
CREATE INDEX IF NOT EXISTS idx_opportunities_stage_score_date ON opportunities (current_stage, overall_score DESC, discovery_date DESC);

-- =====================================================================================
-- Full-Text Search Enhancement for Fetch Operations
-- =====================================================================================

-- Ensure FTS index covers EIN for comprehensive search
-- Note: FTS index already exists, this adds EIN coverage
DROP TRIGGER IF EXISTS opportunities_fts_insert;
DROP TRIGGER IF EXISTS opportunities_fts_update;

-- Enhanced FTS triggers with EIN support
CREATE TRIGGER opportunities_fts_insert AFTER INSERT ON opportunities
BEGIN
    INSERT INTO opportunities_fts(
        rowid, opportunity_id, organization_name, profile_id, tags, notes, analysis_content
    ) VALUES (
        new.rowid,
        new.id,
        new.organization_name || ' ' || COALESCE(new.ein, ''), -- Include EIN in searchable content
        new.profile_id,
        new.tags,
        new.notes,
        COALESCE(new.analysis_discovery, '') || ' ' ||
        COALESCE(new.analysis_plan, '') || ' ' ||
        COALESCE(new.analysis_analyze, '') || ' ' ||
        COALESCE(new.analysis_examine, '') || ' ' ||
        COALESCE(new.analysis_approach, '')
    );
END;

CREATE TRIGGER opportunities_fts_update AFTER UPDATE ON opportunities
BEGIN
    UPDATE opportunities_fts SET
        organization_name = new.organization_name || ' ' || COALESCE(new.ein, ''),
        tags = new.tags,
        notes = new.notes,
        analysis_content =
            COALESCE(new.analysis_discovery, '') || ' ' ||
            COALESCE(new.analysis_plan, '') || ' ' ||
            COALESCE(new.analysis_analyze, '') || ' ' ||
            COALESCE(new.analysis_examine, '') || ' ' ||
            COALESCE(new.analysis_approach, '')
    WHERE rowid = new.rowid;
END;

-- =====================================================================================
-- Analyze Tables for Query Planner Optimization
-- =====================================================================================

-- Update statistics for query planner optimization
ANALYZE profiles;
ANALYZE opportunities;
ANALYZE ai_processing_results;
ANALYZE cost_tracking;

-- =====================================================================================
-- Index Usage Statistics View
-- =====================================================================================

-- Create view to monitor index effectiveness
CREATE VIEW IF NOT EXISTS fetch_index_stats AS
SELECT
    'profiles_ein' AS index_name,
    COUNT(*) AS total_rows,
    COUNT(CASE WHEN ein IS NOT NULL THEN 1 END) AS indexed_rows,
    ROUND(COUNT(CASE WHEN ein IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2) AS coverage_pct
FROM profiles

UNION ALL

SELECT
    'opportunities_ein' AS index_name,
    COUNT(*) AS total_rows,
    COUNT(CASE WHEN ein IS NOT NULL THEN 1 END) AS indexed_rows,
    ROUND(COUNT(CASE WHEN ein IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2) AS coverage_pct
FROM opportunities

UNION ALL

SELECT
    'processing_status' AS index_name,
    COUNT(*) AS total_rows,
    COUNT(CASE WHEN processing_status IS NOT NULL THEN 1 END) AS indexed_rows,
    ROUND(COUNT(CASE WHEN processing_status IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2) AS coverage_pct
FROM opportunities;

-- =====================================================================================
-- Performance Monitoring
-- =====================================================================================

-- Add performance tracking for fetch operations
INSERT OR IGNORE INTO system_metrics (
    metric_date,
    avg_query_time,
    cache_hit_rate,
    daily_ai_calls,
    success_rate
) VALUES (
    DATE('now'),
    0.0,  -- Will be updated by actual measurements
    85.0, -- Target cache hit rate
    0,    -- Will be updated by actual usage
    95.0  -- Target success rate
);

-- Record index creation in schema version
INSERT OR REPLACE INTO schema_version (version, description) VALUES
('1.1.0', 'Added fetch operation optimization indexes for EIN, organization names, and processing status');