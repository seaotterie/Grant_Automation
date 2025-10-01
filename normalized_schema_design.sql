-- =====================================================================================
-- CATALYNX NORMALIZED ANALYTICS SCHEMA
-- Designed for efficient analytical operations and network analysis
-- =====================================================================================

-- =====================================================================================
-- PEOPLE AND LEADERSHIP TABLES
-- =====================================================================================

-- Normalized person table for board members and key personnel
CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    normalized_name TEXT NOT NULL,           -- Cleaned, standardized name
    original_name TEXT NOT NULL,             -- Original name as provided
    name_hash TEXT UNIQUE,                   -- Hash for deduplication

    -- Name parsing
    first_name TEXT,
    last_name TEXT,
    middle_name TEXT,
    prefix TEXT,                            -- Dr, Mr, Mrs, etc.
    suffix TEXT,                            -- Jr, Sr, III, etc.

    -- Biographical information
    biography TEXT,                         -- From web scraping
    linkedin_url TEXT,
    personal_website TEXT,

    -- Data quality and sources
    data_quality_score INTEGER DEFAULT 50,  -- 1-100 quality score
    confidence_level REAL DEFAULT 0.5,     -- AI confidence in data
    source_count INTEGER DEFAULT 1,        -- Number of confirming sources

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP,

    -- Unique constraint on normalized name hash
    UNIQUE(name_hash)
);

-- Organization roles and positions
CREATE TABLE IF NOT EXISTS organization_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    organization_ein TEXT NOT NULL,          -- Links to profiles.ein
    organization_name TEXT NOT NULL,

    -- Position details
    title TEXT NOT NULL,                     -- Board Chair, CEO, Director, etc.
    position_type TEXT DEFAULT 'board',     -- board, executive, staff, advisory
    position_category TEXT,                  -- chair, member, treasurer, etc.

    -- Tenure information
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    tenure_years REAL,                      -- Calculated tenure

    -- Source attribution
    data_source TEXT NOT NULL,              -- web_scraping, 990_filing, manual
    source_url TEXT,                        -- Source URL if web scraped
    filing_year INTEGER,                    -- For 990 filing sources
    web_intelligence_id TEXT,               -- Link to web intelligence source

    -- Data quality
    verification_status TEXT DEFAULT 'unverified', -- verified, unverified, disputed
    quality_score INTEGER DEFAULT 50,       -- Data quality assessment

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (person_id) REFERENCES people (id) ON DELETE CASCADE,
    FOREIGN KEY (organization_ein) REFERENCES profiles (ein) ON DELETE CASCADE,

    -- Unique constraint to prevent duplicates
    UNIQUE(person_id, organization_ein, title, data_source)
);

-- =====================================================================================
-- ORGANIZATIONAL PROGRAMS AND SERVICES
-- =====================================================================================

-- Normalized programs table
CREATE TABLE IF NOT EXISTS organization_programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_ein TEXT NOT NULL,
    organization_name TEXT NOT NULL,

    -- Program details
    program_name TEXT NOT NULL,
    program_description TEXT,
    program_type TEXT,                      -- service, grant, initiative, etc.
    focus_area TEXT,                        -- health, education, environment, etc.
    target_population TEXT,                 -- seniors, youth, families, etc.

    -- Program scope and scale
    geographic_scope TEXT,                  -- local, regional, national, international
    annual_budget REAL,
    participant_count INTEGER,
    duration_months INTEGER,

    -- Status and timing
    program_status TEXT DEFAULT 'active',   -- active, inactive, planned, completed
    start_date DATE,
    end_date DATE,

    -- Source attribution
    data_source TEXT NOT NULL,              -- web_scraping, 990_filing, manual
    source_url TEXT,
    extracted_at TIMESTAMP,

    -- Data quality
    quality_score INTEGER DEFAULT 50,
    confidence_level REAL DEFAULT 0.5,

    -- Keywords and categorization
    keywords TEXT,                          -- Comma-separated keywords
    ntee_alignment TEXT,                    -- Related NTEE codes

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (organization_ein) REFERENCES profiles (ein) ON DELETE CASCADE
);

-- =====================================================================================
-- CONTACT INFORMATION
-- =====================================================================================

-- Normalized contact information
CREATE TABLE IF NOT EXISTS organization_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_ein TEXT NOT NULL,
    organization_name TEXT NOT NULL,

    -- Contact details
    contact_type TEXT NOT NULL,             -- email, phone, address, website, social
    contact_value TEXT NOT NULL,            -- The actual contact info
    contact_label TEXT,                     -- main, grants, info, etc.

    -- Contact specifics
    department TEXT,                        -- grants, admin, programs, etc.
    contact_person TEXT,                    -- If specific person
    is_primary BOOLEAN DEFAULT FALSE,       -- Primary contact of this type
    is_public BOOLEAN DEFAULT TRUE,         -- Publicly available

    -- Verification and quality
    verification_status TEXT DEFAULT 'unverified',
    last_verified_at TIMESTAMP,
    response_rate REAL,                     -- Historical response tracking
    preferred_method BOOLEAN DEFAULT FALSE, -- Organization's preferred contact

    -- Source attribution
    data_source TEXT NOT NULL,
    source_url TEXT,
    extracted_at TIMESTAMP,
    quality_score INTEGER DEFAULT 50,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (organization_ein) REFERENCES profiles (ein) ON DELETE CASCADE
);

-- =====================================================================================
-- NETWORK ANALYSIS TABLES
-- =====================================================================================

-- Board member network connections
CREATE TABLE IF NOT EXISTS board_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    org1_ein TEXT NOT NULL,
    org1_name TEXT NOT NULL,
    org2_ein TEXT NOT NULL,
    org2_name TEXT NOT NULL,

    -- Connection strength and details
    connection_strength REAL DEFAULT 1.0,   -- Base 1.0 per shared member
    shared_positions INTEGER DEFAULT 1,      -- Number of shared positions
    connection_type TEXT DEFAULT 'board',    -- board, executive, advisory

    -- Network metrics
    betweenness_score REAL,                 -- Network betweenness centrality
    closeness_score REAL,                   -- Network closeness centrality
    influence_score REAL,                   -- Combined influence metric

    -- Temporal information
    connection_start_date DATE,
    connection_end_date DATE,
    is_current_connection BOOLEAN DEFAULT TRUE,

    -- Analysis metadata
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    algorithm_version TEXT DEFAULT '2.0.0',

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (person_id) REFERENCES people (id) ON DELETE CASCADE,
    FOREIGN KEY (org1_ein) REFERENCES profiles (ein) ON DELETE CASCADE,
    FOREIGN KEY (org2_ein) REFERENCES profiles (ein) ON DELETE CASCADE,

    -- Unique constraint (ensure ordered ein pairs)
    UNIQUE(person_id, org1_ein, org2_ein),

    -- Ensure org1_ein < org2_ein for consistent ordering
    CHECK(org1_ein < org2_ein)
);

-- Organization network metrics
CREATE TABLE IF NOT EXISTS organization_network_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_ein TEXT NOT NULL,
    organization_name TEXT NOT NULL,

    -- Centrality measures
    degree_centrality REAL,                -- Direct connections
    betweenness_centrality REAL,           -- Bridge position
    closeness_centrality REAL,             -- Average distance
    eigenvector_centrality REAL,           -- Connection to important nodes

    -- Network position
    total_connections INTEGER,              -- Number of connected orgs
    unique_shared_members INTEGER,          -- Unique people creating connections
    network_cluster_id TEXT,                -- Community detection result
    cluster_size INTEGER,                   -- Size of network cluster

    -- Influence metrics
    network_influence_score REAL,          -- Overall network influence
    bridge_score REAL,                     -- Ability to bridge communities
    connector_efficiency REAL,             -- Efficiency of connections

    -- Analysis metadata
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    algorithm_version TEXT DEFAULT '2.0.0',
    network_size INTEGER,                   -- Total network size during analysis

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (organization_ein) REFERENCES profiles (ein) ON DELETE CASCADE,

    -- One current metric per organization
    UNIQUE(organization_ein)
);

-- Individual influence scores
CREATE TABLE IF NOT EXISTS person_influence_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    person_name TEXT NOT NULL,

    -- Position influence
    total_board_positions INTEGER,          -- Number of board positions
    total_organizations INTEGER,            -- Number of organizations
    executive_positions INTEGER,            -- C-level or equivalent positions
    board_chair_positions INTEGER,          -- Board chair roles

    -- Network influence
    network_reach INTEGER,                  -- Total org connections through this person
    bridge_connections INTEGER,             -- Connections they uniquely enable
    cluster_spanning INTEGER,               -- Number of clusters they connect

    -- Calculated influence scores
    position_influence_score REAL,         -- Based on position types and count
    network_influence_score REAL,          -- Based on network position
    total_influence_score REAL,            -- Combined influence metric
    influence_rank INTEGER,                -- Rank among all people

    -- Sector analysis
    sector_diversity INTEGER,              -- Number of different NTEE sectors
    geographic_reach INTEGER,              -- Number of different states/regions

    -- Analysis metadata
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    algorithm_version TEXT DEFAULT '2.0.0',

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (person_id) REFERENCES people (id) ON DELETE CASCADE,

    -- One current metric per person
    UNIQUE(person_id)
);

-- =====================================================================================
-- STRATEGIC INDEXING FOR ANALYTICAL PERFORMANCE
-- =====================================================================================

-- People table indexes
CREATE INDEX IF NOT EXISTS idx_people_normalized_name ON people (normalized_name);
CREATE INDEX IF NOT EXISTS idx_people_name_hash ON people (name_hash);
CREATE INDEX IF NOT EXISTS idx_people_quality ON people (data_quality_score DESC);

-- Organization roles indexes for network analysis
CREATE INDEX IF NOT EXISTS idx_org_roles_person ON organization_roles (person_id);
CREATE INDEX IF NOT EXISTS idx_org_roles_org ON organization_roles (organization_ein);
CREATE INDEX IF NOT EXISTS idx_org_roles_person_org ON organization_roles (person_id, organization_ein);
CREATE INDEX IF NOT EXISTS idx_org_roles_current ON organization_roles (is_current);
CREATE INDEX IF NOT EXISTS idx_org_roles_position_type ON organization_roles (position_type);
CREATE INDEX IF NOT EXISTS idx_org_roles_source ON organization_roles (data_source);

-- Programs indexes for discovery
CREATE INDEX IF NOT EXISTS idx_programs_org ON organization_programs (organization_ein);
CREATE INDEX IF NOT EXISTS idx_programs_focus ON organization_programs (focus_area);
CREATE INDEX IF NOT EXISTS idx_programs_keywords ON organization_programs (keywords);
CREATE INDEX IF NOT EXISTS idx_programs_status ON organization_programs (program_status);
CREATE INDEX IF NOT EXISTS idx_programs_source ON organization_programs (data_source);

-- Contact indexes for outreach
CREATE INDEX IF NOT EXISTS idx_contacts_org ON organization_contacts (organization_ein);
CREATE INDEX IF NOT EXISTS idx_contacts_type ON organization_contacts (contact_type);
CREATE INDEX IF NOT EXISTS idx_contacts_primary ON organization_contacts (is_primary);
CREATE INDEX IF NOT EXISTS idx_contacts_verified ON organization_contacts (verification_status);

-- Network analysis indexes for performance
CREATE INDEX IF NOT EXISTS idx_board_conn_person ON board_connections (person_id);
CREATE INDEX IF NOT EXISTS idx_board_conn_orgs ON board_connections (org1_ein, org2_ein);
CREATE INDEX IF NOT EXISTS idx_board_conn_current ON board_connections (is_current_connection);
CREATE INDEX IF NOT EXISTS idx_board_conn_strength ON board_connections (connection_strength DESC);

-- Network metrics indexes
CREATE INDEX IF NOT EXISTS idx_org_metrics_centrality ON organization_network_metrics (betweenness_centrality DESC);
CREATE INDEX IF NOT EXISTS idx_org_metrics_influence ON organization_network_metrics (network_influence_score DESC);
CREATE INDEX IF NOT EXISTS idx_person_influence_score ON person_influence_metrics (total_influence_score DESC);
CREATE INDEX IF NOT EXISTS idx_person_influence_rank ON person_influence_metrics (influence_rank);

-- =====================================================================================
-- ANALYTICAL VIEWS FOR COMMON QUERIES
-- =====================================================================================

-- Board member network view
CREATE VIEW IF NOT EXISTS board_member_network AS
SELECT
    p.normalized_name,
    p.original_name,
    or1.organization_ein,
    or1.organization_name,
    or1.title,
    or1.position_type,
    or1.is_current,
    or1.data_source,
    p.data_quality_score,
    COUNT(or2.organization_ein) - 1 AS other_board_positions
FROM people p
JOIN organization_roles or1 ON p.id = or1.person_id
LEFT JOIN organization_roles or2 ON p.id = or2.person_id AND or2.organization_ein != or1.organization_ein
WHERE or1.position_type = 'board' AND or1.is_current = TRUE
GROUP BY p.id, or1.organization_ein
ORDER BY other_board_positions DESC, p.data_quality_score DESC;

-- Organization connection strength view
CREATE VIEW IF NOT EXISTS organization_connections AS
SELECT
    bc.org1_ein,
    bc.org1_name,
    bc.org2_ein,
    bc.org2_name,
    COUNT(DISTINCT bc.person_id) AS shared_members_count,
    SUM(bc.connection_strength) AS total_connection_strength,
    GROUP_CONCAT(p.normalized_name, '; ') AS shared_member_names,
    AVG(p.data_quality_score) AS avg_data_quality
FROM board_connections bc
JOIN people p ON bc.person_id = p.id
WHERE bc.is_current_connection = TRUE
GROUP BY bc.org1_ein, bc.org2_ein
ORDER BY total_connection_strength DESC;

-- Program analytics view
CREATE VIEW IF NOT EXISTS program_analytics AS
SELECT
    op.focus_area,
    COUNT(*) AS program_count,
    COUNT(DISTINCT op.organization_ein) AS organization_count,
    AVG(op.annual_budget) AS avg_budget,
    SUM(op.annual_budget) AS total_budget,
    AVG(op.quality_score) AS avg_quality_score
FROM organization_programs op
WHERE op.program_status = 'active'
GROUP BY op.focus_area
ORDER BY program_count DESC;

-- Contact availability view
CREATE VIEW IF NOT EXISTS contact_availability AS
SELECT
    oc.organization_ein,
    oc.organization_name,
    SUM(CASE WHEN oc.contact_type = 'email' THEN 1 ELSE 0 END) AS email_contacts,
    SUM(CASE WHEN oc.contact_type = 'phone' THEN 1 ELSE 0 END) AS phone_contacts,
    SUM(CASE WHEN oc.contact_type = 'website' THEN 1 ELSE 0 END) AS website_contacts,
    SUM(CASE WHEN oc.is_primary = TRUE THEN 1 ELSE 0 END) AS primary_contacts,
    AVG(oc.quality_score) AS avg_contact_quality
FROM organization_contacts oc
GROUP BY oc.organization_ein, oc.organization_name;

-- =====================================================================================
-- DATA INTEGRITY TRIGGERS
-- =====================================================================================

-- Update person metrics when roles change
CREATE TRIGGER IF NOT EXISTS update_person_metrics_on_role_change
AFTER INSERT ON organization_roles
BEGIN
    DELETE FROM person_influence_metrics WHERE person_id = NEW.person_id;
END;

-- Update connection strength when roles change
CREATE TRIGGER IF NOT EXISTS update_connections_on_role_change
AFTER INSERT ON organization_roles
BEGIN
    -- Trigger network analysis recalculation for affected organizations
    DELETE FROM organization_network_metrics
    WHERE organization_ein = NEW.organization_ein;
END;

-- Maintain name hash for deduplication
CREATE TRIGGER IF NOT EXISTS maintain_name_hash
BEFORE INSERT ON people
BEGIN
    UPDATE NEW SET name_hash = printf('%08X', abs(random() % 4294967296)) ||
                               printf('%08X', abs(random() % 4294967296));
END;