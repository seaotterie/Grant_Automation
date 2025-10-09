// Foundation Scoring System BAML Schemas
// Phase 1: Foundation Scoring Compliance
// Converted from Python dataclasses (Oct 7-8, 2025)

// ============================================================================
// NTEE Two-Part Scoring System
// ============================================================================

enum NTEEDataSource {
  BMF                 // IRS Business Master File (most authoritative)
  SCHEDULE_I          // Inferred from Schedule I recipients
  WEBSITE             // Scraped from organization website
  USER_PROVIDED       // Manually entered by user
  UNKNOWN
}

enum NTEEMatchLevel {
  EXACT_FULL          // Exact major + leaf match (B25 = B25) - score 1.0
  EXACT_MAJOR         // Major match, different leaf (B25 = B30) - score 0.4
  RELATED_MAJOR       // Related major codes (B ~ E for education) - score 0.2
  NO_MATCH            // No alignment - score 0.0
}

class NTEECode {
  full_code string
  major string          // Single letter A-Z
  leaf string | null    // 2-3 digit subcategory (optional)
  source NTEEDataSource
  source_date string | null  // ISO datetime string
  confidence float      // 0.0-1.0 confidence in this code
}

class NTEEScoreResult {
  score float                    // 0.0-1.0 normalized score
  match_level NTEEMatchLevel
  profile_codes NTEECode[]
  foundation_codes NTEECode[]
  major_score float              // Raw major code contribution
  leaf_score float               // Raw leaf code contribution
  time_decay_factor float        // Applied time-decay weight
  confidence float               // Overall confidence in this score
  explanation string             // Human-readable explanation
  weighted_score float           // Final score with time-decay applied (score × time_decay_factor)
}

// ============================================================================
// Schedule I Recipient Voting System
// ============================================================================

class RecipientVote {
  recipient_name string
  recipient_ein string | null
  grant_amount float
  grant_year int
  ntee_codes string[]            // NTEE codes for this recipient
  ein_confidence string          // "HIGH" | "MEDIUM" | "LOW"
  vote_weight float              // Final weighted vote (amount × confidence × time-decay)
}

class NTEEVoteResult {
  ntee_code string
  total_votes float              // Sum of weighted votes
  vote_count int                 // Number of recipients voting for this code
  total_grant_amount float       // Total $ awarded to orgs with this code
  avg_grant_amount float         // Average grant size
  recipients string[]            // List of recipient names (max 10)
}

class ScheduleIAnalysis {
  foundation_ein string
  total_recipients int
  total_grant_amount float
  analysis_years int[]

  // Vote aggregations
  ntee_votes map<string, NTEEVoteResult>  // NTEE code → vote results
  top_ntee_codes string[]                  // Top voted NTEE codes (sorted by votes)

  // Coherence metrics
  coherence_score float          // 0.0-1.0, higher = more consistent patterns
  entropy_score float            // 0.0-∞, lower = more focused giving
  concentration_ratio float      // % of $ to top 3 NTEE codes

  // Quality indicators
  ein_resolution_rate float      // % of recipients successfully resolved
  high_confidence_rate float     // % of recipients with HIGH confidence

  // Recommendations
  is_coherent bool               // True if foundation has consistent patterns
  recommended_boost float        // Boost factor for coherent foundations (0.0-0.15)
}

// ============================================================================
// Grant-Size Realism Bands
// ============================================================================

enum GrantSizeBand {
  MICRO              // < $5K
  SMALL              // $5K - $25K
  MEDIUM             // $25K - $100K
  LARGE              // $100K - $500K
  MAJOR              // $500K - $2M
  TRANSFORMATIONAL   // > $2M
}

enum CapacityLevel {
  GRASSROOTS         // < $100K revenue
  EMERGING           // $100K - $500K
  ESTABLISHED        // $500K - $2M
  MATURE             // $2M - $10M
  MAJOR_INSTITUTION  // > $10M
}

enum GrantSizeFit {
  OPTIMAL                  // Perfect fit (5-25% of budget)
  GOOD                     // Good fit (3-5% or 25-40% of budget)
  ACCEPTABLE               // Acceptable (1-3% or 40-60% of budget)
  STRETCH                  // Challenging but possible (60-100% of budget)
  UNREALISTIC_TOO_LARGE    // Grant > budget (very hard to manage)
  UNREALISTIC_TOO_SMALL    // Grant < 1% of budget (not worth effort)
}

class GrantSizeAnalysis {
  grant_amount float
  org_revenue float

  // Categorization
  grant_size_band GrantSizeBand
  capacity_level CapacityLevel

  // Fit analysis
  grant_to_revenue_ratio float   // Grant as % of revenue
  fit_level GrantSizeFit

  // Scoring
  fit_score float                 // 0.0-1.0, higher = better fit
  multiplier float                // Score multiplier (0.5-1.5)

  // Explanation
  explanation string
  recommendations string
}

// ============================================================================
// 990-PF Composite Scorer V2
// ============================================================================

class FoundationOpportunityData {
  foundation_ein string
  foundation_name string

  // NTEE codes (from BMF, Schedule I, or website)
  ntee_codes string[]
  ntee_code_sources map<string, string>  // code → source name
  ntee_code_dates map<string, string> | null  // code → ISO datetime

  // Schedule I recipient data
  schedule_i_grantees string | null      // JSON serialized ScheduleIGrantee[]

  // Grant size data
  typical_grant_amount float | null
  grant_amount_min float | null
  grant_amount_max float | null

  // Geographic data
  geographic_focus_states string[]

  // Financial data
  total_assets float | null
  grants_paid_total float | null

  // Application data
  accepts_applications bool | null

  // Filing metadata
  most_recent_filing_year int | null
}

class CompositeScoreResult {
  final_score float              // 0.0-100.0
  recommendation string          // "PASS" | "ABSTAIN" | "FAIL"

  // Component scores (0.0-100.0 scale)
  ntee_alignment_score float
  geographic_match_score float
  recipient_coherence_score float
  financial_capacity_score float
  grant_size_fit_score float
  application_policy_score float
  filing_recency_score float
  foundation_type_score float

  // Boosts and penalties
  coherence_boost float          // 0.0-0.15
  time_decay_penalty float       // 0.0-1.0 (multiplier)

  // Detailed analysis
  ntee_explanation string

  // Decision support
  confidence float               // 0.0-1.0
  should_abstain bool

  // Optional fields
  schedule_i_analysis map<string, string> | null  // Serialized analysis
  grant_size_analysis map<string, string> | null  // Serialized analysis
  abstain_reason string | null
}

// ============================================================================
// Abstain/Triage Queue System
// ============================================================================

enum TriageStatus {
  PENDING      // Awaiting review
  IN_REVIEW    // Currently being reviewed
  APPROVED     // Expert decided PASS
  REJECTED     // Expert decided FAIL
  ESCALATED    // Needs senior review
  DEFERRED     // Postponed for later
}

enum TriagePriority {
  CRITICAL     // High confidence but critical data missing
  HIGH         // Borderline high score (55-58)
  MEDIUM       // True borderline (50-55)
  LOW          // Borderline low score (45-50)
}

enum ExpertDecision {
  PASS         // Recommend this foundation
  FAIL         // Do not recommend
  UNCERTAIN    // Still unclear, need more data
}

class TriageItem {
  // Identification
  item_id string
  profile_ein string
  profile_name string
  foundation_ein string
  foundation_name string

  // Scoring data
  composite_score float          // 45-58 range typically
  confidence float               // 0.0-1.0
  abstain_reason string

  // Component scores (for analyst context)
  ntee_score float
  geographic_score float
  coherence_score float
  grant_size_score float

  // Triage metadata
  status TriageStatus
  priority TriagePriority
  created_at string              // ISO datetime
  assigned_to string | null

  // Expert review
  expert_decision ExpertDecision | null
  expert_rationale string | null
  reviewed_at string | null      // ISO datetime
  reviewed_by string | null

  // Additional context
  notes string[]
  tags string[]
}

class TriageQueueStats {
  total_items int
  pending_count int
  in_review_count int
  approved_count int
  rejected_count int

  // Priority breakdown
  critical_count int
  high_count int
  medium_count int
  low_count int

  // Performance metrics
  avg_review_time_hours float
  approval_rate float            // % of reviewed items approved
  agreement_rate float           // % where expert agrees with borderline score
}

// ============================================================================
// Reliability Safeguards System
// ============================================================================

enum FilingRecencyLevel {
  CURRENT          // 0-1 years old
  RECENT           // 1-2 years old
  MODERATE         // 2-3 years old
  OLD              // 3-4 years old
  VERY_OLD         // 4-5 years old
  STALE            // 5+ years old
}

enum GrantHistoryStatus {
  ESTABLISHED      // 5+ years of grants
  PROVEN           // 3-5 years of grants
  EMERGING         // 1-3 years of grants
  MINIMAL          // <1 year of grants
  UNKNOWN          // No grant history data
}

enum BorderProximity {
  ADJACENT         // <10 miles
  NEAR             // 10-25 miles
  MODERATE         // 25-50 miles
  FAR              // 50-100 miles
  DISTANT          // 100+ miles
}

class FilingRecencyAnalysis {
  tax_year int
  years_ago int
  recency_level FilingRecencyLevel
  recency_score float            // 0.0-100.0
  penalty float                  // 0.0-0.15
  explanation string
  warning string | null
}

class GrantHistoryAnalysis {
  years_of_grants int
  total_grants int
  avg_grants_per_year float
  history_status GrantHistoryStatus
  history_score float            // 0.0-100.0
  penalty float                  // 0.0-0.12
  is_mirage bool
  explanation string
  recommendation string
}

class BorderProximityAnalysis {
  distance_to_border_miles float
  nearest_border_state string | null
  proximity_level BorderProximity
  proximity_score float          // 0.0-100.0
  boost float                    // 0.0-0.08
  explanation string
  cross_border_eligible bool
}

class ReliabilitySafeguardsResult {
  // Component analyses
  filing_recency FilingRecencyAnalysis
  grant_history GrantHistoryAnalysis
  border_proximity BorderProximityAnalysis

  // Composite metrics
  reliability_score float        // 0.0-100.0
  total_penalty float            // 0.0-0.27 (0.15 + 0.12)
  total_boost float              // 0.0-0.08
  net_adjustment float           // Combined penalty + boost

  // Flags
  has_reliability_concerns bool
  concerns string[]

  // Recommendation
  overall_assessment string
  recommendation string
}

// ============================================================================
// Foundation Network Intelligence System (Phase 9)
// Foundation Grantee Bundling Tool - Multi-Foundation Grant Aggregation
// ============================================================================

enum FundingStability {
  STABLE       // Consistent funding over years
  GROWING      // Increasing funding over time
  DECLINING    // Decreasing funding
  NEW          // Recent grantee (< 2 years)
  SPORADIC     // Inconsistent funding
}

enum RecommendationType {
  PEER_FUNDER        // Similar to current funders
  CLUSTER_MEMBER     // In same peer group
  BRIDGE_FUNDER      // Connects multiple clusters
  EMERGING_FUNDER    // New entrant to issue area
  GEOGRAPHIC_MATCH   // Geographic alignment
}

// Input Models

class GranteeBundlingInput {
  // Required fields
  foundation_eins string[]  // Multiple foundation EINs to analyze

  // Optional filters
  tax_years int[]           // Default: [2022, 2023, 2024]
  min_foundations int       // Minimum funders to flag as "bundled" (default: 2)
  include_grant_purposes bool
  geographic_filter string[] | null  // State codes (e.g., ['VA', 'MD', 'DC'])
  min_grant_amount float    // Filter out small grants (default: 0)

  // Advanced options
  normalize_recipient_names bool
  fuzzy_matching_threshold float  // For name matching without EINs (default: 0.85)
}

class CoFundingAnalysisInput {
  bundling_results string   // Serialized GranteeBundlingOutput from Phase 1
  similarity_threshold float  // Minimum Jaccard to consider "similar" (default: 0.3)
  max_peer_funders int      // Default: 10
  include_network_graph bool
}

// Output Models - Bundling Analysis

class FundingSource {
  foundation_ein string
  foundation_name string
  grant_amount float
  grant_year int
  grant_purpose string | null
  grant_tier string | null  // 'major', 'significant', 'moderate', 'small'
}

class BundledGrantee {
  // Grantee identification
  grantee_ein string | null  // May be None if not available
  grantee_name string
  normalized_name string     // Standardized for matching

  // Funding summary
  funder_count int
  total_funding float
  average_grant_size float

  // Detailed funding sources
  funding_sources FundingSource[]  // All grants to this grantee

  // Temporal data
  first_grant_year int
  last_grant_year int
  funding_consistency float  // 0-1, based on year-over-year funding

  // Geographic and thematic
  geographic_location string | null  // State or city
  common_purposes string[]   // Thematic keywords across grants
  purpose_diversity_score float  // 0-1, indicates focus vs. diverse funding

  // Strategic intelligence
  funding_stability FundingStability
  co_funding_strength float  // 0-1, how often funders co-fund this org
}

class FoundationOverlap {
  foundation_ein_1 string
  foundation_name_1 string
  foundation_ein_2 string
  foundation_name_2 string

  shared_grantees_count int
  shared_grantee_eins string[]
  total_overlap_funding float

  jaccard_similarity float  // 0-1, intersection/union
  overlap_percentage_1 float  // Shared grantees / total grantees of foundation 1
  overlap_percentage_2 float  // Shared grantees / total grantees of foundation 2
}

class ThematicCluster {
  cluster_id string
  cluster_name string        // e.g., "Veterans Services", "Education K-12"
  grantee_count int
  total_funding float

  member_grantees string[]   // EINs or names
  common_keywords string[]
  funding_foundations string[]  // EINs of foundations supporting this cluster
}

class GranteeBundlingOutput {
  // Input summary
  total_foundations_analyzed int
  foundation_eins string[]
  tax_years_analyzed int[]

  // Grantee analysis
  total_unique_grantees int
  bundled_grantees BundledGrantee[]  // Funded by ≥ min_foundations
  single_funder_grantees_count int

  // Co-funding patterns
  foundation_overlap_matrix FoundationOverlap[]  // All foundation pairs
  top_co_funded_orgs BundledGrantee[]  // Sorted by funder count

  // Thematic analysis
  thematic_clusters ThematicCluster[]

  // Aggregate statistics
  total_grants_analyzed int
  total_funding_amount float
  average_grants_per_foundation float
  average_grantees_per_foundation float

  // Data quality
  data_completeness_score float  // 0-1, based on available EINs and purposes
  recipient_matching_confidence float  // 0-1, average confidence in name matching

  // Processing metadata
  processing_time_seconds float
  analysis_date string       // ISO datetime
  api_cost_usd float         // Should be 0.00 for this tool
}

// Output Models - Co-Funding Analysis

class FunderSimilarity {
  foundation_ein_1 string
  foundation_name_1 string
  foundation_ein_2 string
  foundation_name_2 string

  // Similarity metrics
  similarity_score float     // 0-1, weighted Jaccard with recency
  jaccard_similarity float   // 0-1, pure set overlap
  shared_grantees_count int

  // Financial overlap
  total_co_funding_amount float
  average_co_grant_size float

  // Temporal
  recency_score float        // 0-1, weighted by recent grants
  funding_years_overlap int[]

  // Shared characteristics
  shared_grantees string[]   // EINs
  common_geographic_focus string | null
  common_thematic_focus string[]
}

class PeerFunderGroup {
  cluster_id string
  cluster_name string        // Auto-generated or manual

  // Members
  member_foundations string[]  // EINs
  member_count int

  // Shared characteristics
  shared_focus_areas string[]
  geographic_concentration string | null
  average_grant_size float
  total_cluster_funding float

  // Network metrics
  cluster_density float      // How interconnected members are
  bridge_foundations string[]  // Foundations connecting to other clusters
}

class FunderRecommendation {
  recommended_foundation_ein string
  recommended_foundation_name string
  recommendation_type RecommendationType

  rationale string
  confidence_score float     // 0-1
  supporting_evidence string[]

  // Connection details
  shared_funders string[]    // EINs of foundations you both fund
  similarity_to_current_funders float

  // Strategic notes
  estimated_grant_range string  // e.g., "$25K-$100K"
  suggested_approach string
  priority string            // 'high', 'medium', 'low'
}

class CoFundingAnalysisOutput {
  // Funder similarity
  funder_similarity_pairs FunderSimilarity[]
  highly_similar_pairs FunderSimilarity[]  // Above threshold

  // Peer groups (Louvain clustering)
  peer_funder_groups PeerFunderGroup[]

  // Network graph (if requested)
  foundation_network_graph map<string, string> | null  // NetworkX serialized
  network_statistics map<string, string>

  // Recommendations
  recommendations FunderRecommendation[]

  // Processing metadata
  processing_time_seconds float
  analysis_date string       // ISO datetime
}
