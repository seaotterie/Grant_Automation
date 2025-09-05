  Catalynx Database Schema - Table Relationships & Data Elements

  ┌─────────────────────────────────────────────────────────────────────────────────────┐
  │                                PROFILES TABLE                                       │
  ├─────────────────────────────────────────────────────────────────────────────────────┤
  │ PRIMARY KEY: id (TEXT) - format: profile_f3adef3b653c                               │
  ├─────────────────────────────────────────────────────────────────────────────────────┤
  │ CORE IDENTITY:                                                                      │
  │ • name (TEXT) - Organization name                                                   │
  │ • organization_type (TEXT) - nonprofit/foundation/government/corporate              │
  │ • ein (TEXT) - 9-digit Employer Identification Number                              │
  │ • mission_statement (TEXT)                                                          │
  │ • status (TEXT) - active/draft/archived/template                                   │
  │                                                                                     │
  │ CONFIGURATION (JSON Fields):                                                       │
  │ • keywords (TEXT) - Comma-separated search terms                                   │
  │ • focus_areas (TEXT) - JSON array of focus areas                                  │
  │ • program_areas (TEXT) - JSON array of program areas                              │
  │ • target_populations (TEXT) - JSON array of target populations                    │
  │ • ntee_codes (TEXT) - JSON array of NTEE codes                                    │
  │ • government_criteria (TEXT) - JSON array of government criteria                  │
  │ • geographic_scope (TEXT) - JSON object: states/regions/nationwide                │
  │ • service_areas (TEXT) - JSON array of service areas                             │
  │ • funding_preferences (TEXT) - JSON object: types/amounts                         │
  │                                                                                     │
  │ FINANCIAL:                                                                          │
  │ • annual_revenue (INTEGER)                                                          │
  │                                                                                     │
  │ FOUNDATION-SPECIFIC:                                                                │
  │ • form_type (TEXT) - 990, 990-PF                                                  │
  │ • foundation_grants (TEXT) - JSON array of past grants                            │
  │ • board_members (TEXT) - JSON array of board member data                          │
  │                                                                                     │
  │ METRICS & ANALYTICS:                                                                │
  │ • discovery_count (INTEGER) - Total discoveries run                                │
  │ • opportunities_count (INTEGER) - Total opportunities found                        │
  │ • last_discovery_date (TIMESTAMP)                                                  │
  │ • performance_metrics (TEXT) - JSON object with analytics                         │
  │                                                                                     │
  │ AUDIT:                                                                              │
  │ • created_at (TIMESTAMP)                                                           │
  │ • updated_at (TIMESTAMP)                                                           │
  │ • processing_history (TEXT) - JSON array of processing events                     │
  └─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ 1:Many
                                        ▼
  ┌─────────────────────────────────────────────────────────────────────────────────────┐
  │                               OPPORTUNITIES TABLE                                    │
  ├─────────────────────────────────────────────────────────────────────────────────────┤
  │ PRIMARY KEY: id (TEXT) - format: opp_lead_04293743dd92                             │
  │ FOREIGN KEY: profile_id -> profiles.id (CASCADE DELETE)                            │
  ├─────────────────────────────────────────────────────────────────────────────────────┤
  │ CORE IDENTITY:                                                                      │
  │ • profile_id (TEXT) - Links to profiles.id                                        │
  │ • organization_name (TEXT) - Target organization (funder) name                    │
  │ • ein (TEXT) - Target organization EIN                                            │
  │                                                                                     │
  │ PIPELINE MANAGEMENT:                                                                │
  │ • current_stage (TEXT) - prospects/qualified_prospects/candidates/targets/opps    │
  │ • stage_history (TEXT) - JSON array of stage transitions with timestamps         │
  │                                                                                     │
  │ SCORING & ANALYSIS:                                                                 │
  │ • overall_score (REAL) - Primary opportunity score (0.0-1.0)                     │
  │ • confidence_level (REAL) - AI confidence in analysis                             │
  │ • auto_promotion_eligible (BOOLEAN)                                                │
  │ • promotion_recommended (BOOLEAN)                                                   │
  │ • scored_at (TIMESTAMP)                                                            │
  │ • scorer_version (TEXT)                                                            │
  │                                                                                     │
  │ AI ANALYSIS RESULTS (JSON Fields):                                                 │
  │ • analysis_discovery (TEXT) - JSON: DISCOVER tab results                          │
  │ • analysis_plan (TEXT) - JSON: PLAN tab results                                   │
  │ • analysis_analyze (TEXT) - JSON: ANALYZE tab results                             │
  │ • analysis_examine (TEXT) - JSON: EXAMINE tab results                             │
  │ • analysis_approach (TEXT) - JSON: APPROACH tab results                           │
  │                                                                                     │
  │ USER MANAGEMENT:                                                                    │
  │ • user_rating (INTEGER) - 1-5 star rating                                         │
  │ • priority_level (TEXT) - low/medium/high/urgent                                  │
  │ • tags (TEXT) - JSON array of user-defined tags                                   │
  │ • notes (TEXT) - User notes and comments                                          │
  │                                                                                     │
  │ PROCESSING & SOURCE:                                                                │
  │ • promotion_history (TEXT) - JSON array of stage promotions                       │
  │ • processing_status (TEXT) - pending/processing/completed/error                   │
  │ • processing_errors (TEXT) - JSON array of processing errors                      │
  │ • source (TEXT) - commercial/government/state/nonprofit                           │
  │ • discovery_date (TIMESTAMP)                                                       │
  │ • last_analysis_date (TIMESTAMP)                                                   │
  │                                                                                     │
  │ AUDIT:                                                                              │
  │ • created_at (TIMESTAMP)                                                           │
  │ • updated_at (TIMESTAMP)                                                           │
  └─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ 1:Many
                                        ▼
  ┌─────────────────────────────────────────────────────────────────────────────────────┐
  │                           AI_PROCESSING_RESULTS TABLE                               │
  ├─────────────────────────────────────────────────────────────────────────────────────┤
  │ PRIMARY KEY: id (INTEGER AUTOINCREMENT)                                            │
  │ FOREIGN KEY: opportunity_id -> opportunities.id (CASCADE DELETE)                   │
  ├─────────────────────────────────────────────────────────────────────────────────────┤
  │ • opportunity_id (TEXT) - Links to opportunities.id                                │
  │ • processor_type (TEXT) - ai_lite_unified/ai_heavy_light/ai_heavy_deep/impl       │
  │ • processing_stage (TEXT) - plan/analyze/examine/approach                          │
  │ • input_data (TEXT) - JSON: input provided to AI processor                        │
  │ • output_data (TEXT) - JSON: complete AI processor output                         │
  │ • processing_cost (REAL) - Actual cost ($0.0004 to $0.20)                        │
  │ • processing_time (INTEGER) - Processing time in seconds                           │
  │ • token_usage (INTEGER) - Tokens consumed                                          │
  │ • model_used (TEXT) - GPT model version                                           │
  │ • confidence_score (REAL) - AI confidence in results                              │
  │ • quality_score (REAL) - Analysis quality assessment                              │
  │ • success_indicator (BOOLEAN) - Processing success/failure                         │
  │ • error_details (TEXT) - JSON: error information if failed                        │
  │ • processed_at (TIMESTAMP)                                                         │
  └─────────────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────────────┐
  │                              COST_TRACKING TABLE                                    │
  ├─────────────────────────────────────────────────────────────────────────────────────┤
  │ PRIMARY KEY: id (INTEGER AUTOINCREMENT)                                            │
  ├─────────────────────────────────────────────────────────────────────────────────────┤
  │ • date (DATE) - Daily cost tracking                                                │
  │ • profile_id (TEXT) - Optional: cost by profile                                   │
  │ • total_cost (REAL) - Daily total cost                                            │
  │ • api_calls_count (INTEGER) - Number of API calls                                 │
  │ • tokens_used (INTEGER) - Total tokens consumed                                   │
  │                                                                                     │
  │ COST BREAKDOWN BY PROCESSOR:                                                       │
  │ • cost_ai_lite (REAL) - AI-Lite costs ($0.0004 each)                            │
  │ • cost_ai_heavy_light (REAL) - AI-Heavy Light costs ($0.02-0.04)                 │
  │ • cost_ai_heavy_deep (REAL) - AI-Heavy Deep costs ($0.08-0.15)                   │
  │ • cost_ai_heavy_impl (REAL) - AI-Heavy Implementation ($0.12-0.20)               │
  │                                                                                     │
  │ BUDGET TRACKING:                                                                    │
  │ • daily_budget (REAL) - Daily spending limit                                      │
  │ • monthly_budget (REAL) - Monthly spending limit                                  │
  │ • budget_alert_sent (BOOLEAN) - Alert notification status                         │
  │ • created_at (TIMESTAMP)                                                           │
  └─────────────────────────────────────────────────────────────────────────────────────┘

                ┌─────────────────────────────────────┐
                │         EXPORT_HISTORY TABLE        │
                │ FOREIGN KEY: profile_id -> profiles │
                ├─────────────────────────────────────┤
                │ • profile_id (TEXT)                 │
                │ • export_type (TEXT)                │
                │ • export_format (TEXT)              │
                │ • filename (TEXT)                   │
                │ • file_path (TEXT)                  │
                │ • file_size (INTEGER)               │
                │ • opportunities_count (INTEGER)     │
                │ • export_config (TEXT)              │
                │ • export_status (TEXT)              │
                │ • created_at (TIMESTAMP)            │
                └─────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────────────┐
  │                      OPPORTUNITIES_FTS (Full-Text Search)                          │
  ├─────────────────────────────────────────────────────────────────────────────────────┤
  │ VIRTUAL TABLE using FTS5 for fast text search across:                              │
  │ • opportunity_id, organization_name, profile_id, tags, notes, analysis_content     │
  │ • Auto-updated via triggers on opportunities table INSERT/UPDATE/DELETE           │
  └─────────────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────────────┐
  │                           SUPPORTING TABLES                                         │
  ├─────────────────────────────────────────────────────────────────────────────────────┤
  │ BACKUP_HISTORY: backup tracking and verification                                   │
  │ SYSTEM_METRICS: performance monitoring and database health                         │
  │ SCHEMA_VERSION: database migration tracking                                        │
  └─────────────────────────────────────────────────────────────────────────────────────┘

  ═══════════════════════════════════════════════════════════════════════════════════════
                                      USEFUL VIEWS
  ═══════════════════════════════════════════════════════════════════════════════════════

  PROFILE_SUMMARY: Profile overview with opportunity counts and scores
  STAGE_FUNNEL: Opportunity progression by stage (prospects → opportunities)
  COST_SUMMARY: Daily and monthly cost tracking with budget percentages
  RECENT_ACTIVITY: Latest 7 days of processing activity across all profiles
  PERFORMANCE_DASHBOARD: Key system metrics vs targets

  ═══════════════════════════════════════════════════════════════════════════════════════
                                 KEY RELATIONSHIPS
  ═══════════════════════════════════════════════════════════════════════════════════════

  profiles (1) ←→ (Many) opportunities (CASCADE DELETE)
  opportunities (1) ←→ (Many) ai_processing_results (CASCADE DELETE)  
  profiles (1) ←→ (Many) export_history (CASCADE DELETE)
  cost_tracking ←→ profiles (optional profile-specific tracking)

  Target Scale: 50 profiles, ~7,500 opportunities (~150 opportunities per profile)
  Database File: Single SQLite file at data/catalynx.db

  Key Design Principles

  1. Single Database: All data in one SQLite file with proper foreign key relationships
  2. JSON Storage: Complex configuration and analysis data stored as JSON in TEXT fields
  3. Audit Trail: Comprehensive timestamps and history tracking across all tables
  4. Performance Optimized: Indexes designed for common query patterns
  5. Cost Integration: Built-in OpenAI API cost monitoring with budget controls
  6. Full-Text Search: Virtual FTS5 table enables fast search across opportunity content
  7. Cascade Deletes: Deleting a profile removes all related opportunities and results

  This structure supports the dual architecture of tab-based processors and intelligence tiers while maintaining data integrity and performance for the target scale of 50 profiles with ~7,500    
   opportunities.