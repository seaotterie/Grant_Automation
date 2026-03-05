-- =====================================================================================
-- FOUNDATION PREPROCESSING TABLES
-- Precomputed foundation intelligence for instant profile-to-foundation matching
-- Created: 2026-03-05
-- =====================================================================================
-- These tables store precomputed foundation features that are:
-- 1. Universal (same for all profiles, computed once monthly)
-- 2. Profile-independent (no per-profile data here)
-- 3. Instantly queryable (replaces runtime calculations)

-- =====================================================================================
-- FOUNDATION INTELLIGENCE INDEX (Core precomputed features)
-- =====================================================================================
-- Monthly batch job output: one row per foundation with all precomputed scores

CREATE TABLE IF NOT EXISTS foundation_intelligence_index (
    ein TEXT PRIMARY KEY,                          -- Links to bmf_organizations

    -- Capacity Tier (from 990-PF financials)
    capacity_tier TEXT,                            -- 'mega', 'major', 'significant', 'modest', 'minimal'
    grants_paid_latest INTEGER DEFAULT 0,          -- Most recent year grants paid
    assets_fmv_latest INTEGER DEFAULT 0,           -- Most recent fair market value
    avg_grant_size INTEGER DEFAULT 0,              -- Estimated average grant size
    annual_grant_budget_estimate INTEGER DEFAULT 0, -- Projected annual giving capacity

    -- Giving Trend (multi-year analysis)
    giving_trend TEXT DEFAULT 'unknown',           -- 'growing', 'stable', 'declining', 'erratic', 'new', 'unknown'
    giving_trend_pct REAL,                         -- Year-over-year change percentage
    years_of_data INTEGER DEFAULT 0,              -- How many years of 990-PF data available

    -- Compliance Pre-Filter Flags
    is_eligible_grantmaker INTEGER DEFAULT 1,      -- 0 = disqualified by compliance flags
    disqualification_reasons TEXT,                 -- JSON array of reasons if ineligible
    accepts_applications TEXT DEFAULT 'unknown',   -- 'yes', 'no', 'invitation_only', 'unknown'
    grants_to_individuals_only INTEGER DEFAULT 0,  -- grntindivcd flag
    is_operating_foundation INTEGER DEFAULT 0,     -- operatingcd flag
    non_charity_grants INTEGER DEFAULT 0,          -- nchrtygrntcd flag

    -- Financial Health Signals
    health_status TEXT DEFAULT 'unknown',          -- 'strong', 'stable', 'declining', 'distressed', 'unknown'
    payout_compliance TEXT DEFAULT 'unknown',      -- 'compliant', 'under_payout', 'over_payout', 'unknown'
    payout_ratio REAL,                             -- Actual payout ratio (grants/assets)
    undistributed_income INTEGER,                  -- Current undistributed income
    future_grants_approved INTEGER DEFAULT 0,      -- Grants approved for future payment

    -- Investment Portfolio Profile
    portfolio_type TEXT DEFAULT 'unknown',         -- 'conservative', 'balanced', 'growth', 'aggressive', 'unknown'
    portfolio_diversity_score REAL,                -- 0-1.0 diversity across asset types
    investment_return_rate REAL,                   -- Net investment income / assets

    -- Geographic Focus (from Schedule I grant patterns)
    primary_states TEXT,                           -- JSON array of top grant-receiving states
    geographic_concentration REAL,                 -- 0-1.0 (1.0 = all grants to one state)

    -- Grant Purpose Archetypes (from Schedule I text clustering)
    primary_archetype TEXT,                        -- Best-fit archetype label
    secondary_archetypes TEXT,                     -- JSON array of other matching archetypes
    archetype_confidence REAL,                     -- 0-1.0 confidence in archetype assignment

    -- NTEE Classification
    ntee_code TEXT,                                -- From BMF
    ntee_major_group TEXT,                         -- First letter of NTEE code (broad category)

    -- Metadata
    last_computed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    computation_version TEXT DEFAULT '1.0.0',
    data_quality_score REAL DEFAULT 0.0,           -- 0-1.0 completeness of source data
    source_tax_year INTEGER                        -- Most recent tax year used
);

-- Performance indexes for foundation intelligence queries
CREATE INDEX IF NOT EXISTS idx_fi_capacity ON foundation_intelligence_index(capacity_tier);
CREATE INDEX IF NOT EXISTS idx_fi_eligible ON foundation_intelligence_index(is_eligible_grantmaker);
CREATE INDEX IF NOT EXISTS idx_fi_trend ON foundation_intelligence_index(giving_trend);
CREATE INDEX IF NOT EXISTS idx_fi_health ON foundation_intelligence_index(health_status);
CREATE INDEX IF NOT EXISTS idx_fi_archetype ON foundation_intelligence_index(primary_archetype);
CREATE INDEX IF NOT EXISTS idx_fi_ntee ON foundation_intelligence_index(ntee_code);
CREATE INDEX IF NOT EXISTS idx_fi_ntee_major ON foundation_intelligence_index(ntee_major_group);
CREATE INDEX IF NOT EXISTS idx_fi_capacity_eligible ON foundation_intelligence_index(capacity_tier, is_eligible_grantmaker);
CREATE INDEX IF NOT EXISTS idx_fi_grants_paid ON foundation_intelligence_index(grants_paid_latest DESC);
CREATE INDEX IF NOT EXISTS idx_fi_quality ON foundation_intelligence_index(data_quality_score DESC);

-- =====================================================================================
-- FOUNDATION NARRATIVES (From PDF extraction)
-- =====================================================================================
-- Cached narrative content extracted from 990-PF PDFs using Claude

CREATE TABLE IF NOT EXISTS foundation_narratives (
    ein TEXT PRIMARY KEY,                          -- Links to bmf_organizations

    -- Mission & Purpose
    mission_statement TEXT,                        -- Foundation's stated mission
    mission_keywords TEXT,                         -- JSON array of extracted keywords

    -- Application Process
    accepts_applications TEXT DEFAULT 'unknown',   -- 'yes', 'no', 'invitation_only', 'unknown'
    application_deadlines TEXT,                    -- Free text: deadline info
    application_process TEXT,                      -- How to apply
    required_documents TEXT,                       -- JSON array of required docs
    contact_information TEXT,                      -- Contact details for applications

    -- Program Focus
    program_descriptions TEXT,                     -- JSON array of program area descriptions
    stated_priorities TEXT,                        -- JSON array of stated funding priorities
    geographic_limitations TEXT,                   -- Geographic restrictions text
    population_focus TEXT,                         -- Target populations text

    -- Extraction Metadata
    source_pdf_url TEXT,                           -- URL of source PDF
    source_tax_year INTEGER,                       -- Tax year of source filing
    extraction_model TEXT,                         -- Model used for extraction
    extraction_confidence REAL,                    -- 0-1.0 confidence in extraction
    extracted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_fn_accepts ON foundation_narratives(accepts_applications);
CREATE INDEX IF NOT EXISTS idx_fn_year ON foundation_narratives(source_tax_year);

-- =====================================================================================
-- GRANT ARCHETYPES (Semantic clusters from Schedule I purposes)
-- =====================================================================================
-- Reference table of grant-giving archetypes derived from clustering

CREATE TABLE IF NOT EXISTS grant_archetypes (
    archetype_id TEXT PRIMARY KEY,                 -- e.g., 'education_k12', 'health_clinical'
    archetype_label TEXT NOT NULL,                 -- Human-readable label
    archetype_description TEXT,                    -- What this archetype represents
    example_purposes TEXT,                         -- JSON array of example grant purpose texts
    related_ntee_codes TEXT,                       -- JSON array of related NTEE codes
    keyword_patterns TEXT,                         -- JSON array of matching keywords
    foundation_count INTEGER DEFAULT 0,            -- How many foundations match this archetype
    total_grant_volume INTEGER DEFAULT 0,          -- Total $ across all matching foundations
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================================
-- PROFILE MATCH CACHE (Per-profile precomputed matches)
-- =====================================================================================
-- Cached profile-to-foundation match scores, invalidated on profile update

CREATE TABLE IF NOT EXISTS profile_foundation_matches (
    profile_id TEXT NOT NULL,
    foundation_ein TEXT NOT NULL,

    -- Match Scores (0-1.0)
    overall_match_score REAL NOT NULL,             -- Weighted composite score
    ntee_alignment_score REAL DEFAULT 0.0,         -- NTEE code overlap
    geographic_alignment_score REAL DEFAULT 0.0,   -- Geographic overlap
    grant_size_fit_score REAL DEFAULT 0.0,         -- Grant size vs profile capacity
    archetype_match_score REAL DEFAULT 0.0,        -- Mission archetype alignment
    giving_trend_score REAL DEFAULT 0.0,           -- Bonus for growing foundations
    board_connection_score REAL DEFAULT 0.0,       -- Board member connections

    -- Match Details
    matching_ntee_codes TEXT,                      -- JSON array of overlapping NTEE codes
    matching_states TEXT,                          -- JSON array of overlapping states
    matching_archetypes TEXT,                      -- JSON array of matching archetypes
    recommended_ask_range TEXT,                    -- Suggested grant amount range

    -- Cache Management
    computed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    profile_version TEXT,                          -- Profile hash/version when computed
    foundation_version TEXT,                       -- Foundation index version when computed
    is_stale INTEGER DEFAULT 0,                    -- 1 = needs recomputation

    PRIMARY KEY (profile_id, foundation_ein)
);

CREATE INDEX IF NOT EXISTS idx_pfm_profile ON profile_foundation_matches(profile_id, overall_match_score DESC);
CREATE INDEX IF NOT EXISTS idx_pfm_stale ON profile_foundation_matches(is_stale);
CREATE INDEX IF NOT EXISTS idx_pfm_score ON profile_foundation_matches(overall_match_score DESC);

-- =====================================================================================
-- BOARD NETWORK INDEX (Precomputed cross-foundation connections)
-- =====================================================================================
-- Maps board member names across foundations for network analysis

CREATE TABLE IF NOT EXISTS board_network_index (
    normalized_name TEXT NOT NULL,                 -- Normalized name for matching
    ein TEXT NOT NULL,                             -- Foundation EIN
    title TEXT,                                    -- Position title
    compensation INTEGER DEFAULT 0,               -- Compensation amount
    source_tax_year INTEGER,                       -- Tax year of data
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (normalized_name, ein)
);

CREATE INDEX IF NOT EXISTS idx_bni_ein ON board_network_index(ein);
CREATE INDEX IF NOT EXISTS idx_bni_name ON board_network_index(normalized_name);

-- Cross-foundation connection view
CREATE VIEW IF NOT EXISTS v_board_cross_connections AS
SELECT
    b1.normalized_name,
    b1.ein as foundation_1_ein,
    b2.ein as foundation_2_ein,
    b1.title as title_at_foundation_1,
    b2.title as title_at_foundation_2
FROM board_network_index b1
INNER JOIN board_network_index b2
    ON b1.normalized_name = b2.normalized_name
    AND b1.ein < b2.ein;
