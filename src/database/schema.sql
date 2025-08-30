-- Catalynx Grant Research Platform - SQLite Database Schema
-- Optimized for single-user system with 50 profiles, ~7,500 opportunities
-- Created: August 29, 2025

-- =====================================================================================
-- CORE ENTITIES TABLES
-- =====================================================================================

-- Profiles table - Core organization profiles (target: 50 profiles)
CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,                    -- profile_f3adef3b653c format
    name TEXT NOT NULL,                     -- Organization name
    organization_type TEXT NOT NULL,       -- nonprofit, foundation, government, corporate
    ein TEXT,                              -- Employer Identification Number
    mission_statement TEXT,                -- Organization mission
    status TEXT DEFAULT 'active',          -- active, draft, archived, template
    
    -- Profile Configuration
    keywords TEXT,                         -- Comma-separated search keywords
    focus_areas TEXT,                      -- JSON array of focus areas
    program_areas TEXT,                    -- JSON array of program areas
    target_populations TEXT,               -- JSON array of target populations
    ntee_codes TEXT,                       -- JSON array of NTEE codes
    government_criteria TEXT,              -- JSON array of government criteria
    
    -- Geographic Configuration
    geographic_scope TEXT,                 -- JSON object: {states, regions, nationwide, international}
    service_areas TEXT,                    -- JSON array of service areas
    
    -- Financial Configuration
    funding_preferences TEXT,              -- JSON object: funding types, amounts, etc.
    annual_revenue INTEGER,                -- Annual revenue amount
    
    -- Foundation-Specific Fields
    form_type TEXT,                        -- 990, 990-PF for foundations
    foundation_grants TEXT,                -- JSON array of past grants
    board_members TEXT,                    -- JSON array of board member data
    
    -- Metrics and Analytics
    discovery_count INTEGER DEFAULT 0,     -- Total discoveries run
    opportunities_count INTEGER DEFAULT 0,  -- Total opportunities found
    last_discovery_date TIMESTAMP,        -- Last discovery run date
    performance_metrics TEXT,              -- JSON object with analytics
    
    -- Audit Fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_history TEXT               -- JSON array of processing events
);

-- Opportunities table - Grant opportunities for each profile (target: ~7,500 opportunities)
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,                   -- opp_lead_04293743dd92 format
    profile_id TEXT NOT NULL,             -- Foreign key to profiles.id
    organization_name TEXT NOT NULL,       -- Target organization name
    ein TEXT,                             -- Target organization EIN
    
    -- Pipeline Management
    current_stage TEXT NOT NULL DEFAULT 'discovery', -- prospects, qualified_prospects, candidates, targets, opportunities
    stage_history TEXT,                   -- JSON array of stage transitions with timestamps
    
    -- Scoring and Analysis
    overall_score REAL DEFAULT 0.0,      -- Primary opportunity score
    confidence_level REAL,               -- AI confidence in analysis
    auto_promotion_eligible BOOLEAN DEFAULT FALSE,
    promotion_recommended BOOLEAN DEFAULT FALSE,
    scored_at TIMESTAMP,
    scorer_version TEXT DEFAULT '1.0.0',
    
    -- Analysis Results Storage
    analysis_discovery TEXT,              -- JSON object: discovery stage analysis
    analysis_plan TEXT,                   -- JSON object: planning stage analysis
    analysis_analyze TEXT,                -- JSON object: analyze stage analysis  
    analysis_examine TEXT,                -- JSON object: examine stage analysis
    analysis_approach TEXT,               -- JSON object: approach stage analysis
    
    -- User Assessment
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5), -- 1-5 star rating
    priority_level TEXT CHECK (priority_level IN ('low', 'medium', 'high', 'urgent')),
    tags TEXT,                           -- JSON array of user-defined tags
    notes TEXT,                          -- User notes and comments
    
    -- Processing Tracking
    promotion_history TEXT,              -- JSON array of stage promotions
    legacy_mappings TEXT,                -- JSON object for backward compatibility
    processing_status TEXT DEFAULT 'pending', -- pending, processing, completed, error
    processing_errors TEXT,              -- JSON array of processing errors if any
    
    -- Source and Discovery
    source TEXT,                         -- discovery track: commercial, government, state, nonprofit
    discovery_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_analysis_date TIMESTAMP,
    
    -- Audit Fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraint
    FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE
);

-- =====================================================================================
-- ANALYSIS AND SCORING TABLES
-- =====================================================================================

-- AI Processing Results - Detailed AI analysis storage
CREATE TABLE IF NOT EXISTS ai_processing_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id TEXT NOT NULL,
    processor_type TEXT NOT NULL,         -- ai_lite_unified, ai_heavy_light, ai_heavy_deep, ai_heavy_implementation
    processing_stage TEXT NOT NULL,      -- plan, analyze, examine, approach
    
    -- Processing Details
    input_data TEXT,                      -- JSON: input provided to AI processor
    output_data TEXT,                     -- JSON: complete AI processor output
    processing_cost REAL,                 -- Actual cost of processing ($0.0004 to $0.20)
    processing_time INTEGER,              -- Processing time in seconds
    token_usage INTEGER,                  -- Tokens consumed
    model_used TEXT,                      -- GPT model version used
    
    -- Quality Metrics
    confidence_score REAL,               -- AI confidence in results
    quality_score REAL,                  -- Analysis quality assessment
    success_indicator BOOLEAN DEFAULT TRUE, -- Processing success/failure
    error_details TEXT,                   -- JSON: error information if failed
    
    -- Timestamps
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key
    FOREIGN KEY (opportunity_id) REFERENCES opportunities (id) ON DELETE CASCADE
);

-- Cost Tracking - OpenAI API usage monitoring
CREATE TABLE IF NOT EXISTS cost_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,                   -- Daily cost tracking
    profile_id TEXT,                      -- Optional: cost by profile
    
    -- Usage Metrics
    total_cost REAL DEFAULT 0.0,         -- Daily total cost
    api_calls_count INTEGER DEFAULT 0,    -- Number of API calls
    tokens_used INTEGER DEFAULT 0,        -- Total tokens consumed
    
    -- Cost Breakdown by Processor
    cost_ai_lite REAL DEFAULT 0.0,       -- AI-Lite processing costs ($0.0004 each)
    cost_ai_heavy_light REAL DEFAULT 0.0, -- AI-Heavy Light costs ($0.02-0.04)
    cost_ai_heavy_deep REAL DEFAULT 0.0,  -- AI-Heavy Deep costs ($0.08-0.15)  
    cost_ai_heavy_impl REAL DEFAULT 0.0,  -- AI-Heavy Implementation ($0.12-0.20)
    
    -- Budget Tracking
    daily_budget REAL DEFAULT 10.0,       -- Daily spending limit
    monthly_budget REAL DEFAULT 300.0,    -- Monthly spending limit
    budget_alert_sent BOOLEAN DEFAULT FALSE, -- Alert notification status
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================================
-- EXPORT AND BACKUP TABLES  
-- =====================================================================================

-- Export History - Track PDF/Excel exports
CREATE TABLE IF NOT EXISTS export_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    export_type TEXT NOT NULL,            -- pdf_report, excel_workbook, data_backup
    export_format TEXT NOT NULL,          -- pdf, xlsx, json
    
    -- Export Details
    filename TEXT NOT NULL,               -- Generated filename
    file_path TEXT NOT NULL,              -- Full file path
    file_size INTEGER,                    -- File size in bytes
    opportunities_count INTEGER,          -- Number of opportunities included
    
    -- Export Configuration
    export_config TEXT,                  -- JSON: export parameters used
    stage_filter TEXT,                   -- Which stages were included
    date_range_start DATE,               -- Export date range
    date_range_end DATE,
    
    -- Status
    export_status TEXT DEFAULT 'pending', -- pending, completed, failed
    export_duration INTEGER,             -- Time taken in seconds
    error_message TEXT,                   -- Error details if failed
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE
);

-- Backup History - Simple backup tracking
CREATE TABLE IF NOT EXISTS backup_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_type TEXT NOT NULL,           -- full_database, profile_data, opportunity_data
    backup_filename TEXT NOT NULL,       -- Backup filename
    backup_path TEXT NOT NULL,           -- Full backup file path
    
    -- Backup Metrics
    file_size INTEGER,                   -- Backup file size
    records_count INTEGER,               -- Number of records backed up
    compression_used BOOLEAN DEFAULT FALSE,
    
    -- Status
    backup_status TEXT DEFAULT 'pending', -- pending, completed, failed
    backup_duration INTEGER,             -- Time taken in seconds
    error_message TEXT,
    
    -- Verification
    verification_hash TEXT,              -- File integrity hash
    restore_tested BOOLEAN DEFAULT FALSE, -- Whether restore was tested
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================================
-- PERFORMANCE AND SYSTEM TABLES
-- =====================================================================================

-- System Metrics - Performance monitoring
CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_date DATE NOT NULL,
    
    -- Database Metrics
    database_size INTEGER,               -- Database file size in bytes
    total_profiles INTEGER,              -- Current profile count
    total_opportunities INTEGER,         -- Current opportunity count
    
    -- Performance Metrics
    avg_query_time REAL,                -- Average query response time (ms)
    slow_queries_count INTEGER DEFAULT 0, -- Queries > 1 second
    cache_hit_rate REAL,                -- Cache efficiency percentage
    
    -- AI Processing Metrics
    daily_ai_calls INTEGER DEFAULT 0,    -- AI API calls per day
    avg_processing_time REAL,           -- Average AI processing time
    success_rate REAL,                  -- AI processing success percentage
    
    -- System Health
    disk_space_used INTEGER,            -- Disk space used (bytes)
    memory_usage INTEGER,               -- Memory usage (bytes)
    uptime_hours INTEGER,               -- System uptime
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(metric_date)                  -- One entry per date
);

-- =====================================================================================
-- SEARCH AND INDEXING SUPPORT
-- =====================================================================================

-- Full-Text Search Index for Opportunities
CREATE VIRTUAL TABLE IF NOT EXISTS opportunities_fts USING fts5(
    opportunity_id,
    organization_name,
    profile_id,
    tags,
    notes,
    analysis_content,                    -- Combined analysis text for search
    content='opportunities',
    content_rowid='rowid'
);

-- Search trigger to keep FTS index updated
CREATE TRIGGER IF NOT EXISTS opportunities_fts_insert AFTER INSERT ON opportunities
BEGIN
    INSERT INTO opportunities_fts(
        rowid, opportunity_id, organization_name, profile_id, tags, notes, analysis_content
    ) VALUES (
        new.rowid, new.id, new.organization_name, new.profile_id, 
        new.tags, new.notes, 
        COALESCE(new.analysis_discovery, '') || ' ' || 
        COALESCE(new.analysis_plan, '') || ' ' ||
        COALESCE(new.analysis_analyze, '') || ' ' ||
        COALESCE(new.analysis_examine, '') || ' ' ||
        COALESCE(new.analysis_approach, '')
    );
END;

CREATE TRIGGER IF NOT EXISTS opportunities_fts_update AFTER UPDATE ON opportunities
BEGIN
    UPDATE opportunities_fts SET
        organization_name = new.organization_name,
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

CREATE TRIGGER IF NOT EXISTS opportunities_fts_delete AFTER DELETE ON opportunities
BEGIN
    DELETE FROM opportunities_fts WHERE rowid = old.rowid;
END;

-- =====================================================================================
-- USEFUL INDEXES FOR SINGLE-USER PERFORMANCE
-- =====================================================================================

-- Primary query patterns for 50 profiles, 7500 opportunities
CREATE INDEX IF NOT EXISTS idx_opportunities_profile_id ON opportunities (profile_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_stage ON opportunities (current_stage);
CREATE INDEX IF NOT EXISTS idx_opportunities_score ON opportunities (overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_discovery_date ON opportunities (discovery_date DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_profile_stage ON opportunities (profile_id, current_stage);
CREATE INDEX IF NOT EXISTS idx_opportunities_profile_score ON opportunities (profile_id, overall_score DESC);

-- AI Processing and cost tracking indexes
CREATE INDEX IF NOT EXISTS idx_ai_processing_opportunity ON ai_processing_results (opportunity_id);
CREATE INDEX IF NOT EXISTS idx_ai_processing_stage ON ai_processing_results (processing_stage);
CREATE INDEX IF NOT EXISTS idx_cost_tracking_date ON cost_tracking (date DESC);
CREATE INDEX IF NOT EXISTS idx_cost_tracking_profile ON cost_tracking (profile_id, date DESC);

-- Export and backup indexes  
CREATE INDEX IF NOT EXISTS idx_export_profile_date ON export_history (profile_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_backup_type_date ON backup_history (backup_type, created_at DESC);

-- System metrics index
CREATE INDEX IF NOT EXISTS idx_system_metrics_date ON system_metrics (metric_date DESC);

-- =====================================================================================
-- DATABASE INITIALIZATION DATA
-- =====================================================================================

-- Insert default system metrics row
INSERT OR IGNORE INTO system_metrics (
    metric_date, total_profiles, total_opportunities, 
    avg_query_time, cache_hit_rate, success_rate,
    daily_ai_calls, avg_processing_time
) VALUES (
    DATE('now'), 0, 0, 0.0, 85.0, 95.0, 0, 0.0
);

-- Insert default cost tracking for current date
INSERT OR IGNORE INTO cost_tracking (
    date, total_cost, daily_budget, monthly_budget
) VALUES (
    DATE('now'), 0.0, 10.0, 300.0  
);

-- =====================================================================================
-- USEFUL VIEWS FOR COMMON QUERIES
-- =====================================================================================

-- Profile Summary View - Quick overview of each profile
CREATE VIEW IF NOT EXISTS profile_summary AS
SELECT 
    p.id,
    p.name,
    p.organization_type,
    p.status,
    COUNT(o.id) AS total_opportunities,
    COUNT(CASE WHEN o.current_stage = 'opportunities' THEN 1 END) AS final_opportunities,
    AVG(o.overall_score) AS avg_score,
    MAX(o.discovery_date) AS last_discovery,
    p.created_at
FROM profiles p
LEFT JOIN opportunities o ON p.id = o.profile_id
GROUP BY p.id, p.name, p.organization_type, p.status, p.created_at;

-- Stage Funnel View - Opportunity progression by stage
CREATE VIEW IF NOT EXISTS stage_funnel AS
SELECT 
    profile_id,
    COUNT(CASE WHEN current_stage = 'prospects' THEN 1 END) AS prospects,
    COUNT(CASE WHEN current_stage = 'qualified_prospects' THEN 1 END) AS qualified_prospects,
    COUNT(CASE WHEN current_stage = 'candidates' THEN 1 END) AS candidates,
    COUNT(CASE WHEN current_stage = 'targets' THEN 1 END) AS targets,
    COUNT(CASE WHEN current_stage = 'opportunities' THEN 1 END) AS opportunities
FROM opportunities
GROUP BY profile_id;

-- Cost Summary View - Daily and monthly cost tracking
CREATE VIEW IF NOT EXISTS cost_summary AS
SELECT 
    date,
    total_cost,
    daily_budget,
    (total_cost / daily_budget * 100) AS daily_budget_used_pct,
    SUM(total_cost) OVER (
        ORDER BY date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS monthly_total,
    monthly_budget,
    api_calls_count,
    tokens_used
FROM cost_tracking
ORDER BY date DESC;

-- Recent Activity View - Latest processing activity
CREATE VIEW IF NOT EXISTS recent_activity AS
SELECT 
    'opportunity' AS activity_type,
    o.id AS item_id,
    p.name AS profile_name,
    o.organization_name AS item_name,
    o.current_stage AS status,
    o.updated_at AS activity_time
FROM opportunities o
JOIN profiles p ON o.profile_id = p.id
WHERE o.updated_at >= datetime('now', '-7 days')

UNION ALL

SELECT 
    'ai_processing' AS activity_type,
    a.opportunity_id AS item_id,
    p.name AS profile_name,
    a.processor_type AS item_name,
    CASE WHEN a.success_indicator THEN 'completed' ELSE 'failed' END AS status,
    a.processed_at AS activity_time
FROM ai_processing_results a
JOIN opportunities o ON a.opportunity_id = o.id  
JOIN profiles p ON o.profile_id = p.id
WHERE a.processed_at >= datetime('now', '-7 days')

ORDER BY activity_time DESC
LIMIT 50;

-- Performance Dashboard View - Key metrics for monitoring
CREATE VIEW IF NOT EXISTS performance_dashboard AS
SELECT 
    'profiles' AS metric_name,
    COUNT(*) AS current_value,
    50 AS target_value,
    'count' AS unit
FROM profiles
WHERE status = 'active'

UNION ALL

SELECT 
    'opportunities' AS metric_name,
    COUNT(*) AS current_value,
    7500 AS target_value,
    'count' AS unit  
FROM opportunities

UNION ALL

SELECT 
    'avg_query_time' AS metric_name,
    ROUND(avg_query_time, 2) AS current_value,
    5000 AS target_value,
    'ms' AS unit
FROM system_metrics
WHERE metric_date = DATE('now')

UNION ALL

SELECT 
    'daily_cost' AS metric_name,
    ROUND(total_cost, 4) AS current_value,
    10.0 AS target_value,
    '$' AS unit
FROM cost_tracking
WHERE date = DATE('now');

-- =====================================================================================
-- SCHEMA VERSION TRACKING
-- =====================================================================================

-- Schema version table for future migrations
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT OR REPLACE INTO schema_version (version, description) VALUES 
('1.0.0', 'Initial database schema for single-user grant research platform');

-- =====================================================================================
-- END OF SCHEMA
-- =====================================================================================

-- Database optimization settings for single-user performance
PRAGMA journal_mode = WAL;           -- Better concurrency and performance
PRAGMA synchronous = NORMAL;         -- Good balance of safety and speed
PRAGMA cache_size = 10000;          -- 10MB cache for better query performance
PRAGMA temp_store = MEMORY;          -- Store temporary data in memory
PRAGMA mmap_size = 268435456;        -- 256MB memory-mapped I/O for large databases

-- Analyze database to optimize query planner
ANALYZE;