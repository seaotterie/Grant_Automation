-- Phase F: Quality & Learning Loop - Schema Migration
-- Adds outcome tracking, gateway decision persistence, and scoring calibration

-- =====================================================================================
-- OUTCOME TRACKING
-- =====================================================================================

-- Grant outcomes - tracks what happened after screening/analysis
CREATE TABLE IF NOT EXISTS grant_outcomes (
    id TEXT PRIMARY KEY,
    opportunity_id TEXT NOT NULL,
    profile_id TEXT NOT NULL,

    -- Application tracking
    application_submitted INTEGER DEFAULT 0,
    application_submitted_date TIMESTAMP,

    -- Award status
    award_status TEXT NOT NULL DEFAULT 'pending',  -- pending, awarded, rejected, withdrawn, not_pursued
    award_date TIMESTAMP,
    award_amount REAL,
    award_notification_source TEXT,  -- user_reported, grants_gov, funder_direct, research

    -- Scores at time of decision (snapshot for calibration)
    screening_score REAL,
    screening_confidence TEXT,
    screening_strategic_fit REAL,
    screening_eligibility REAL,
    screening_timing REAL,
    screening_financial REAL,
    screening_competition REAL,
    deep_intelligence_score REAL,
    multidimensional_score REAL,

    -- Human decision context
    gateway_decision TEXT,           -- pass, reject, investigate
    gateway_decision_reason TEXT,

    -- Outcome analysis
    outcome_notes TEXT,
    key_success_factors TEXT,        -- JSON array
    key_failure_factors TEXT,        -- JSON array

    -- Metadata
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (opportunity_id) REFERENCES opportunities (id) ON DELETE CASCADE,
    FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_outcomes_opportunity ON grant_outcomes (opportunity_id);
CREATE INDEX IF NOT EXISTS idx_outcomes_profile ON grant_outcomes (profile_id);
CREATE INDEX IF NOT EXISTS idx_outcomes_status ON grant_outcomes (award_status);
CREATE INDEX IF NOT EXISTS idx_outcomes_date ON grant_outcomes (recorded_at DESC);

-- =====================================================================================
-- GATEWAY DECISION PERSISTENCE
-- =====================================================================================

-- Persists human gateway decisions (currently in-memory only)
CREATE TABLE IF NOT EXISTS gateway_decisions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    opportunity_id TEXT NOT NULL,
    profile_id TEXT,

    -- AI scores at time of decision
    screening_overall_score REAL,
    screening_confidence TEXT,
    screening_dimensions TEXT,       -- JSON: {strategic_fit, eligibility, timing, ...}

    -- Human decision
    decision TEXT NOT NULL,          -- pass, reject, investigate
    decision_reason TEXT,
    selected_depth TEXT,             -- essentials or premium

    -- Investigation trail
    investigation_notes TEXT,        -- JSON array of {question, answer, timestamp}

    -- Metadata
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (opportunity_id) REFERENCES opportunities (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_gw_decisions_session ON gateway_decisions (session_id);
CREATE INDEX IF NOT EXISTS idx_gw_decisions_opportunity ON gateway_decisions (opportunity_id);
CREATE INDEX IF NOT EXISTS idx_gw_decisions_decision ON gateway_decisions (decision);

-- =====================================================================================
-- SCORING CALIBRATION LOG
-- =====================================================================================

-- Records predicted vs actual outcomes for calibration analysis
CREATE TABLE IF NOT EXISTS scoring_calibration_log (
    id TEXT PRIMARY KEY,
    opportunity_id TEXT NOT NULL,
    profile_id TEXT NOT NULL,

    -- Predicted scores
    screening_score REAL,
    deep_score REAL,
    multidimensional_score REAL,

    -- Dimension-level scores (JSON for flexible analysis)
    dimension_scores TEXT,           -- JSON: {dim_name: {score, weight, boost}}

    -- Actual outcome
    actual_outcome TEXT NOT NULL,    -- awarded, rejected, not_pursued, pending
    award_amount REAL,

    -- Error analysis
    prediction_error REAL,           -- abs(predicted_success - actual)

    -- Metadata
    stage_at_prediction TEXT,        -- Which stage was the prediction from?
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (opportunity_id) REFERENCES opportunities (id) ON DELETE CASCADE,
    FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_calibration_profile ON scoring_calibration_log (profile_id);
CREATE INDEX IF NOT EXISTS idx_calibration_outcome ON scoring_calibration_log (actual_outcome);

-- =====================================================================================
-- SCHEMA VERSION UPDATE
-- =====================================================================================

INSERT OR REPLACE INTO schema_version (version, description) VALUES
('2.0.0', 'Phase F: Learning loop - outcome tracking, gateway persistence, scoring calibration');
