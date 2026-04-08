-- =====================================================================================
-- FOUNDATION GRANTS TABLE
-- Individual grant records extracted from 990 Schedule I and 990-PF Part XV XML
-- Run once before first bulk load:
--   python -c "
--   import sqlite3
--   db = sqlite3.connect('data/nonprofit_intelligence.db')
--   db.executescript(open('tools/irs_990_bulk_loader/migration_foundation_grants.sql').read())
--   db.close(); print('Done')
--   "
-- =====================================================================================

CREATE TABLE IF NOT EXISTS foundation_grants (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Grantor (the filing organization)
    grantor_ein       TEXT NOT NULL,
    tax_year          INTEGER NOT NULL,
    form_type         TEXT NOT NULL,        -- '990', '990-PF'

    -- Recipient
    recipient_name    TEXT NOT NULL,
    recipient_ein     TEXT,                 -- NULL if not disclosed
    recipient_city    TEXT,
    recipient_state   TEXT,

    -- Grant details
    grant_amount      REAL NOT NULL DEFAULT 0.0,
    grant_purpose     TEXT,
    assistance_type   TEXT,                 -- 'cash', 'non-cash', etc. (990 Schedule I)
    relationship_desc TEXT,                 -- Relationship to grantor

    -- Provenance
    source_zip_file   TEXT,                 -- e.g. '2025_TEOS_XML_01A.zip'
    loaded_at         TEXT DEFAULT (datetime('now')),

    -- Idempotent: same grant in same filing = same row
    UNIQUE(grantor_ein, tax_year, recipient_name, grant_amount)
);

CREATE INDEX IF NOT EXISTS idx_fg_grantor    ON foundation_grants(grantor_ein, tax_year DESC);
CREATE INDEX IF NOT EXISTS idx_fg_recip_ein  ON foundation_grants(recipient_ein)
    WHERE recipient_ein IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_fg_amount     ON foundation_grants(grant_amount DESC);
CREATE INDEX IF NOT EXISTS idx_fg_state      ON foundation_grants(recipient_state, tax_year DESC);
CREATE INDEX IF NOT EXISTS idx_fg_year       ON foundation_grants(tax_year DESC);
