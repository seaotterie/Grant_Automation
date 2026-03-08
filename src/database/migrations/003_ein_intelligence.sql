-- Migration 003: EIN-keyed shared intelligence cache
-- Enables cross-profile reuse of web research and 990 PDF analysis
-- TTL policy: web_data 30 days, filing_history 7 days, pdf_analyses never expire

CREATE TABLE IF NOT EXISTS ein_intelligence (
    ein TEXT PRIMARY KEY,
    org_name TEXT,
    -- Web intelligence (Tool 25 + Claude interpretation)
    web_data TEXT,                   -- JSON blob: mission, leadership, programs, key_facts, contact
    web_data_fetched_at TEXT,        -- ISO timestamp
    web_data_source TEXT,            -- 'claude_interpreted' | 'scrapy_raw'
    -- 990 filing history (ProPublica API + scraping)
    filing_history TEXT,             -- JSON array: [{tax_year, form_type, pdf_url, revenue, expenses}]
    filing_history_fetched_at TEXT,  -- ISO timestamp
    -- Per-filing PDF analysis results (keyed by tax_year)
    pdf_analyses TEXT,               -- JSON object: {"2023": NarrativeExtractionResult, ...}
    -- Timestamps
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
