// BAML Schema for Deep Intelligence Tool
// Factor 4: Structured outputs for comprehensive grant intelligence

enum AnalysisDepth {
  QUICK
  STANDARD
  ENHANCED
  COMPLETE
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
