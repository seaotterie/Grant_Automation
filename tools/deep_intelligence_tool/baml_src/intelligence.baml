// BAML Schema for Deep Intelligence Tool
// Factor 4: Structured outputs for comprehensive grant intelligence
// Version 2.0.0 - TRUE COST 2-Tier System (October 2025)

enum AnalysisDepth {
  // New 2-tier system (October 2025)
  ESSENTIALS  // $2.00 user, $0.05 AI, includes network intelligence
  PREMIUM     // $8.00 user, $0.10 AI, enhanced features + dossier

  // DEPRECATED (30-day sunset, auto-mapped to new tiers)
  QUICK       // → ESSENTIALS
  STANDARD    // → ESSENTIALS
  ENHANCED    // → PREMIUM
  COMPLETE    // → PREMIUM
}

enum RiskLevel {
  LOW
  MEDIUM
  HIGH
  CRITICAL
}

enum SuccessProbability {
  VERY_LOW
  LOW
  MODERATE
  HIGH
  VERY_HIGH
}

// Core Analysis Types (All Depths)

class StrategicFitAnalysis {
  fit_score float
  mission_alignment_score float
  program_alignment_score float
  geographic_alignment_score float

  alignment_strengths string[]
  alignment_concerns string[]
  strategic_rationale string

  strategic_positioning string
  key_differentiators string[]
}

class FinancialViabilityAnalysis {
  viability_score float
  budget_capacity_score float
  financial_health_score float
  sustainability_score float

  budget_implications string
  resource_requirements map<string, string>
  financial_risks string[]

  financial_strategy string
  budget_recommendations string[]
}

class OperationalReadinessAnalysis {
  readiness_score float
  capacity_score float
  timeline_feasibility_score float
  infrastructure_readiness_score float

  capacity_gaps string[]
  infrastructure_requirements string[]
  timeline_challenges string[]

  capacity_building_plan string
  operational_recommendations string[]
  estimated_preparation_time_weeks int
}

class RiskFactor {
  category string
  risk_level RiskLevel
  description string
  impact string
  mitigation_strategy string
  probability float
}

class RiskAssessment {
  overall_risk_level RiskLevel
  overall_risk_score float
  risk_factors RiskFactor[]

  critical_risks string[]
  manageable_risks string[]
  risk_mitigation_plan string
}

// Enhanced Features (Standard+ Depths)

class HistoricalGrant {
  recipient_name string
  grant_amount float
  grant_year int
  purpose string
  geographic_location string?
}

class HistoricalAnalysis {
  historical_grants HistoricalGrant[]
  total_grants_analyzed int
  total_funding_amount float

  average_grant_size float
  typical_grant_range string
  funding_trends string
  geographic_patterns string

  similar_recipient_profiles string[]
  success_factors string[]
  competitive_intelligence string
}

class GeographicAnalysis {
  primary_service_area string
  funder_geographic_focus string
  geographic_alignment_score float

  geographic_fit_assessment string
  regional_competition_analysis string
  location_advantages string[]
  location_challenges string[]
}

// Advanced Features (Enhanced+ Depths)

class BoardMember {
  name string
  title string?
  affiliations string[]
  influence_score float?
}

class NetworkConnection {
  connection_type string
  connected_entity string
  strength float
  description string
}

class NetworkAnalysis {
  board_connections BoardMember[]
  network_connections NetworkConnection[]

  network_strength_score float
  relationship_advantages string[]

  relationship_leverage_strategy string
  key_contacts_to_cultivate string[]
}

class RelationshipMap {
  direct_relationships string[]
  indirect_relationships string[]
  partnership_opportunities string[]

  relationship_insights string
  cultivation_strategy string
}

// Premium Features (Complete Depth)

class PolicyAlignment {
  relevant_policies string[]
  alignment_score float
  policy_opportunities string[]
  policy_risks string[]
}

class PolicyAnalysis {
  federal_policy_alignment PolicyAlignment
  state_policy_alignment PolicyAlignment?

  policy_landscape_summary string
  policy_opportunities string[]
  advocacy_recommendations string[]
}

class StrategicConsultingInsights {
  executive_summary string
  competitive_positioning string
  differentiation_strategy string

  multi_year_funding_strategy string
  partnership_development_strategy string
  capacity_building_roadmap string

  immediate_actions string[]
  medium_term_actions string[]
  long_term_actions string[]
}

// Main Output

class DeepIntelligenceOutput {
  // Core (all depths)
  strategic_fit StrategicFitAnalysis
  financial_viability FinancialViabilityAnalysis
  operational_readiness OperationalReadinessAnalysis
  risk_assessment RiskAssessment

  proceed_recommendation bool
  success_probability SuccessProbability
  overall_score float

  executive_summary string
  key_strengths string[]
  key_challenges string[]
  recommended_next_steps string[]

  // Enhanced (standard+)
  historical_intelligence HistoricalAnalysis?
  geographic_analysis GeographicAnalysis?

  // Advanced (enhanced+)
  network_intelligence NetworkAnalysis?
  relationship_mapping RelationshipMap?

  // Premium (complete only)
  policy_analysis PolicyAnalysis?
  strategic_consulting StrategicConsultingInsights?

  // Metadata
  depth_executed string
  processing_time_seconds float
  api_cost_usd float
  timestamp string
  tool_version string
}

// AI Functions

function AnalyzeQuickDepth(
  opportunity_title: string,
  opportunity_description: string,
  funder_name: string,
  organization_name: string,
  organization_mission: string,
  screening_score: float?
) -> DeepIntelligenceOutput {
  client GPT4o
  prompt #"
    DEEP INTELLIGENCE ANALYSIS - QUICK DEPTH
    Cost: $0.75 | Time: 5-10 minutes | Equivalent: CURRENT tier

    OPPORTUNITY:
    Title: {{ opportunity_title }}
    Funder: {{ funder_name }}
    Description: {{ opportunity_description }}

    ORGANIZATION:
    Name: {{ organization_name }}
    Mission: {{ organization_mission }}
    Screening Score: {{ screening_score }}

    ANALYSIS REQUIREMENTS (4-Stage AI Analysis):

    1. STRATEGIC FIT (PLAN stage):
       - Mission alignment (0.0-1.0)
       - Program alignment (0.0-1.0)
       - Geographic alignment (0.0-1.0)
       - Strategic positioning and key differentiators

    2. FINANCIAL VIABILITY (ANALYZE stage):
       - Budget capacity assessment
       - Financial health considerations
       - Sustainability implications
       - Resource requirements and budget strategy

    3. OPERATIONAL READINESS (EXAMINE stage):
       - Capacity assessment
       - Timeline feasibility
       - Infrastructure readiness
       - Capacity gaps and preparation requirements

    4. RISK ASSESSMENT (APPROACH stage):
       - Identify 3-5 risk factors (eligibility, competition, capacity, timeline, financial)
       - Assess overall risk level (LOW/MEDIUM/HIGH/CRITICAL)
       - Provide mitigation strategies

    OVERALL ASSESSMENT:
    - Proceed recommendation (true/false)
    - Success probability (VERY_LOW to VERY_HIGH)
    - Overall score (weighted average)
    - Executive summary (2-3 paragraphs)
    - Key strengths (3-5 items)
    - Key challenges (3-5 items)
    - Recommended next steps (3-5 actions)

    Return comprehensive DeepIntelligenceOutput with all core analyses.
    QUICK depth does NOT include: historical_intelligence, geographic_analysis,
    network_intelligence, policy_analysis, or strategic_consulting.
  "#
}

function AnalyzeStandardDepth(
  opportunity_title: string,
  opportunity_description: string,
  funder_name: string,
  organization_name: string,
  organization_mission: string,
  screening_score: float?
) -> DeepIntelligenceOutput {
  client GPT4o
  prompt #"
    DEEP INTELLIGENCE ANALYSIS - STANDARD DEPTH
    Cost: $7.50 | Time: 15-20 minutes | Equivalent: STANDARD tier

    [Same core analysis as QUICK depth, plus:]

    5. HISTORICAL INTELLIGENCE:
       - Research funder's past grants (3-5 examples)
       - Calculate average grant size and typical range
       - Identify funding trends and patterns
       - Analyze geographic distribution
       - Profile similar successful recipients
       - Extract success factors
       - Competitive intelligence insights

    6. GEOGRAPHIC ANALYSIS:
       - Service area alignment assessment
       - Funder geographic focus analysis
       - Geographic alignment score
       - Regional competition analysis
       - Location advantages and challenges

    Return DeepIntelligenceOutput with core + historical + geographic analyses.
  "#
}

function AnalyzeEnhancedDepth(
  opportunity_title: string,
  opportunity_description: string,
  funder_name: string,
  organization_name: string,
  organization_mission: string,
  screening_score: float?
) -> DeepIntelligenceOutput {
  client GPT4o
  prompt #"
    DEEP INTELLIGENCE ANALYSIS - ENHANCED DEPTH
    Cost: $22.00 | Time: 30-45 minutes | Equivalent: ENHANCED tier

    [Same analyses as STANDARD depth, plus:]

    7. NETWORK INTELLIGENCE:
       - Board member analysis (3-5 key members)
       - Identify board connections and affiliations
       - Map network connections (board overlap, partnerships, funding)
       - Calculate network strength score
       - Identify relationship advantages
       - Develop relationship leverage strategy
       - Identify key contacts to cultivate

    8. RELATIONSHIP MAPPING:
       - Direct relationships (existing connections)
       - Indirect relationships (2nd degree connections)
       - Partnership opportunities
       - Relationship insights and patterns
       - Cultivation strategy

    Return DeepIntelligenceOutput with core + enhanced + advanced analyses.
  "#
}

function AnalyzeCompleteDepth(
  opportunity_title: string,
  opportunity_description: string,
  funder_name: string,
  organization_name: string,
  organization_mission: string,
  screening_score: float?
) -> DeepIntelligenceOutput {
  client GPT4o
  prompt #"
    DEEP INTELLIGENCE ANALYSIS - COMPLETE DEPTH
    Cost: $42.00 | Time: 45-60 minutes | Equivalent: COMPLETE tier

    DEPRECATED: Use AnalyzePremiumDepth instead

    [Same analyses as ENHANCED depth, plus:]

    9. POLICY ANALYSIS:
       - Federal policy alignment (relevant policies, score, opportunities, risks)
       - State policy alignment (if applicable)
       - Policy landscape summary
       - Policy opportunities for strategic positioning
       - Advocacy recommendations

    10. STRATEGIC CONSULTING INSIGHTS:
        - Executive summary (comprehensive strategic overview)
        - Competitive positioning analysis
        - Differentiation strategy
        - Multi-year funding strategy
        - Partnership development strategy
        - Capacity building roadmap
        - Action plan:
          * Immediate actions (0-3 months)
          * Medium-term actions (3-12 months)
          * Long-term actions (1-3 years)

    Return complete DeepIntelligenceOutput with ALL analyses (26+ page report equivalent).
  "#
}

// ============================================================================
// NEW 2-TIER SYSTEM BAML FUNCTIONS (October 2025 - TRUE COST PRICING)
// ============================================================================

function AnalyzeEssentialsDepth(
  opportunity_title: string,
  opportunity_description: string,
  funder_name: string,
  funder_type: string,
  organization_name: string,
  organization_mission: string,
  organization_ein: string,
  screening_score: float?,
  opportunity_amount_min: float?,
  opportunity_amount_max: float?,
  opportunity_deadline: string?
) -> DeepIntelligenceOutput {
  client GPT4o
  prompt #"
    DEEP INTELLIGENCE ANALYSIS - ESSENTIALS TIER
    User Price: $2.00 | AI Cost: $0.05 | Time: 15-20 minutes

    ** INCLUDES NETWORK INTELLIGENCE IN BASE TIER! **

    OPPORTUNITY DETAILS:
    Title: {{ opportunity_title }}
    Funder: {{ funder_name }} ({{ funder_type }})
    Description: {{ opportunity_description }}
    Amount Range: ${{ opportunity_amount_min }} - ${{ opportunity_amount_max }}
    Deadline: {{ opportunity_deadline }}

    ORGANIZATION CONTEXT:
    Name: {{ organization_name }}
    EIN: {{ organization_ein }}
    Mission: {{ organization_mission }}
    Screening Score: {{ screening_score }}

    ANALYSIS REQUIREMENTS (Comprehensive 4-Stage AI Analysis):

    1. STRATEGIC FIT ANALYSIS (PLAN Stage):
       - Mission alignment score (0.0-1.0): How well does this opportunity align with the organization's mission?
       - Program alignment score (0.0-1.0): Does the organization have programs that fit?
       - Geographic alignment score (0.0-1.0): Service area match?
       - Alignment strengths (3-5 bullet points)
       - Alignment concerns (2-3 bullet points)
       - Strategic rationale (2-3 sentences)
       - Strategic positioning recommendation
       - Key differentiators (3-4 items)

    2. FINANCIAL VIABILITY ANALYSIS (ANALYZE Stage):
       - Viability score (0.0-1.0): Overall financial feasibility
       - Budget capacity score (0.0-1.0): Can organization manage this grant size?
       - Financial health score (0.0-1.0): Organization's financial stability
       - Sustainability score (0.0-1.0): Long-term sustainability potential
       - Budget implications (describe financial requirements)
       - Resource requirements (staff, infrastructure, etc.)
       - Financial risks (3-4 key risks)
       - Financial strategy recommendation
       - Budget recommendations (3-4 specific actions)

    3. OPERATIONAL READINESS ANALYSIS (EXAMINE Stage):
       - Readiness score (0.0-1.0): Overall operational preparedness
       - Capacity score (0.0-1.0): Current capacity to execute
       - Timeline feasibility score (0.0-1.0): Can meet deadlines?
       - Infrastructure readiness score (0.0-1.0): Systems and processes ready?
       - Capacity gaps (3-5 specific gaps)
       - Infrastructure requirements (3-4 items)
       - Timeline challenges (2-3 challenges)
       - Capacity building plan (2-3 sentences)
       - Operational recommendations (3-4 actions)
       - Estimated preparation time in weeks

    4. RISK ASSESSMENT (APPROACH Stage):
       - Overall risk level (LOW/MEDIUM/HIGH/CRITICAL)
       - Overall risk score (0.0-1.0)
       - Risk factors (4-6 specific risks):
         * Category: eligibility, competition, capacity, timeline, financial, compliance
         * Risk level for each
         * Description and impact
         * Mitigation strategy
         * Probability (0.0-1.0)
       - Critical risks (if any)
       - Manageable risks (list)
       - Risk mitigation plan (comprehensive strategy)

    NETWORK INTELLIGENCE (NEW IN ESSENTIALS - $0.01 AI cost):
    Analyze relationship opportunities:
    - Network strength score (0.0-1.0)
    - Relationship advantages (3-4 items)
    - Relationship leverage strategy
    - Key contacts to cultivate (2-3 contacts)

    Note: Network intelligence is included in ESSENTIALS tier - this is a competitive advantage!

    OVERALL ASSESSMENT:
    - Proceed recommendation (true/false): Should organization pursue this?
    - Success probability (VERY_LOW/LOW/MODERATE/HIGH/VERY_HIGH)
    - Overall score (0.0-1.0): Weighted composite score
    - Executive summary (3-4 paragraphs):
      * Opportunity overview and strategic fit
      * Key strengths and competitive advantages
      * Main challenges and considerations
      * Bottom-line recommendation with rationale
    - Key strengths (4-6 bullet points)
    - Key challenges (3-5 bullet points)
    - Recommended next steps (5-6 specific actions)

    IMPORTANT:
    - Be specific and actionable
    - Use data-driven scoring
    - Provide clear go/no-go guidance
    - Focus on practical implementation
    - Include network intelligence insights (NEW!)

    Return comprehensive DeepIntelligenceOutput with all ESSENTIALS analyses.
    Set depth_executed = "essentials"
  "#
}

function AnalyzePremiumDepth(
  opportunity_title: string,
  opportunity_description: string,
  funder_name: string,
  funder_type: string,
  organization_name: string,
  organization_mission: string,
  organization_ein: string,
  screening_score: float?,
  opportunity_amount_min: float?,
  opportunity_amount_max: float?,
  opportunity_deadline: string?,
  target_funder_board: string[]?
) -> DeepIntelligenceOutput {
  client GPT4o
  prompt #"
    DEEP INTELLIGENCE ANALYSIS - PREMIUM TIER
    User Price: $8.00 | AI Cost: $0.10 | Time: 30-40 minutes

    ** EVERYTHING IN ESSENTIALS + ENHANCED STRATEGIC FEATURES **

    OPPORTUNITY DETAILS:
    Title: {{ opportunity_title }}
    Funder: {{ funder_name }} ({{ funder_type }})
    Description: {{ opportunity_description }}
    Amount Range: ${{ opportunity_amount_min }} - ${{ opportunity_amount_max }}
    Deadline: {{ opportunity_deadline }}
    Target Funder Board: {{ target_funder_board }}

    ORGANIZATION CONTEXT:
    Name: {{ organization_name }}
    EIN: {{ organization_ein }}
    Mission: {{ organization_mission }}
    Screening Score: {{ screening_score }}

    PERFORM ALL ESSENTIALS ANALYSES FIRST:
    (See AnalyzeEssentialsDepth for core analysis requirements)

    PLUS PREMIUM ENHANCEMENTS:

    5. RELATIONSHIP MAPPING (PREMIUM Feature):
       - Direct relationships (3-5 existing connections)
       - Indirect relationships (2nd degree connections, pathways)
       - Partnership opportunities (3-4 strategic partnerships)
       - Relationship insights (2-3 key patterns/advantages)
       - Cultivation strategy (specific approach for warm introductions)

       Focus: How to leverage relationships for warm introductions to decision makers

    6. POLICY ANALYSIS (PREMIUM Feature):
       Federal Policy Alignment:
       - Relevant policies (4-6 policies)
       - Alignment score (0.0-1.0)
       - Policy opportunities (3-4 opportunities)
       - Policy risks (2-3 risks)

       State Policy Alignment (if applicable):
       - Relevant state policies
       - Alignment score
       - State-level opportunities
       - State-level risks

       Policy Landscape Summary (2-3 paragraphs)
       Policy opportunities for positioning (3-4 items)
       Advocacy recommendations (3-4 specific actions)

    7. STRATEGIC CONSULTING INSIGHTS (PREMIUM Feature):
       Executive Summary (3-4 paragraphs):
       - Comprehensive strategic overview
       - Success probability with network context
       - Connection strength to funder ecosystem
       - Strategic opportunity assessment

       Competitive Positioning:
       - Unique competitive advantages
       - Differentiation from likely competitors
       - Network and relationship strengths

       Differentiation Strategy:
       - Key differentiators to emphasize
       - Unique value proposition
       - Strategic positioning approach

       Multi-Year Funding Strategy:
       - Relationship building timeline
       - Sequential funding opportunities
       - Long-term funder engagement plan

       Partnership Development Strategy:
       - Strategic partner identification
       - Collaboration opportunities
       - Ecosystem positioning

       Capacity Building Roadmap:
       - Phase 1: Infrastructure (timeframe and focus)
       - Phase 2: Staff capacity (timeframe and focus)
       - Phase 3: Program scaling (timeframe and focus)

       Action Plan (specific and prioritized):
       * Immediate actions (0-3 months): 4-6 specific actions
       * Medium-term actions (3-12 months): 4-5 strategic initiatives
       * Long-term actions (1-3 years): 3-4 institutional positioning moves

    COMPREHENSIVE DOSSIER ELEMENTS:
    - 20+ page equivalent analysis
    - Decision-maker profiling insights
    - Warm introduction pathways
    - Enhanced network intelligence
    - Policy context and opportunities
    - Strategic consulting level insights
    - Complete implementation roadmap

    IMPORTANT PREMIUM GUIDANCE:
    - Provide strategic consulting-level insights
    - Focus on competitive advantage and differentiation
    - Emphasize relationship leverage and warm introductions
    - Include policy context for strategic positioning
    - Deliver actionable multi-year strategy
    - Executive-ready comprehensive analysis

    Return complete DeepIntelligenceOutput with ALL ESSENTIALS + PREMIUM analyses.
    Set depth_executed = "premium"
  "#
}
