// BAML Schema for Network Intelligence Tool
// Board network analysis and relationship mapping

enum NetworkStrength {
  very_strong
  strong
  moderate
  weak
  minimal
}

enum RelationshipType {
  board_member
  advisor
  donor
  partner
  vendor
  peer
}

class NetworkIntelligenceInput {
  organization_ein string
  organization_name string
  board_members map<string, string>[] @description("Board members with name, title, affiliations")
  target_funder_name string?
  target_funder_board string[]?
  key_donors string[]?
  partner_organizations string[]?
  advisory_board string[]?
}

class BoardMemberProfile {
  name string
  title string?
  current_affiliations string[]
  past_affiliations string[]
  centrality_score float @description("Network centrality 0-1")
  influence_score float @description("Influence within network 0-1")
  connection_count int
  direct_connections string[]
  indirect_connections string[]
  strategic_value_score float @description("Strategic value to organization 0-1")
  strategic_value_reasoning string
}

class NetworkConnection {
  from_entity string
  to_entity string
  connection_type RelationshipType
  strength NetworkStrength
  description string
  strategic_value string
}

class CentralityMetrics {
  degree_centrality float @description("Number of connections, 0-1")
  betweenness_centrality float @description("Bridge position, 0-1")
  closeness_centrality float @description("Distance to others, 0-1")
  eigenvector_centrality float @description("Connection to influential nodes, 0-1")
  overall_centrality float @description("Overall centrality score, 0-1")
  centrality_interpretation string
}

class NetworkCluster {
  cluster_id string
  cluster_name string
  member_count int
  members string[]
  cluster_focus string
  strategic_relevance string
}

class RelationshipPathway {
  target string
  pathway string[] @description("Entities forming path from org to target")
  pathway_strength NetworkStrength
  pathway_description string
  cultivation_strategy string
}

class StrategicConnection {
  target_entity string
  connection_type string
  priority string @description("high, medium, or low")
  rationale string
  cultivation_steps string[]
  estimated_timeline string
  success_probability float @description("0-1 probability of successful cultivation")
}

class NetworkIntelligenceAnalysis {
  network_executive_summary string @description("2-3 paragraph summary")
  network_size int
  network_density float @description("0-1 network connectivity")
  average_path_length float
  network_strengths string[]
  key_influencers string[]
  network_gaps string[]
  recommended_additions string[]
  strategic_opportunities string[]
  cultivation_priorities string[]
}

class FunderConnectionAnalysis {
  funder_name string
  direct_board_connections string[]
  direct_connection_count int
  indirect_pathways RelationshipPathway[]
  strongest_pathway RelationshipPathway?
  overall_connection_strength NetworkStrength
  connection_advantage string
  recommended_cultivation_strategy string
  immediate_actions string[]
  success_probability float @description("0-1 probability of success")
}

class NetworkIntelligenceOutput {
  board_member_profiles BoardMemberProfile[]
  all_connections NetworkConnection[]
  strategic_connections StrategicConnection[]
  network_centrality CentralityMetrics
  identified_clusters NetworkCluster[]
  network_analysis NetworkIntelligenceAnalysis
  funder_connection_analysis FunderConnectionAnalysis?
  network_quality_score float @description("Data completeness, 0-1")
  confidence_level float @description("Analysis confidence, 0-1")
}

function AnalyzeNetworkIntelligence(input: NetworkIntelligenceInput) -> NetworkIntelligenceOutput {
  client GPT4o

  prompt #"
    You are an expert in nonprofit board network analysis and relationship mapping.

    Analyze the board network for {{ input.organization_name }} (EIN: {{ input.organization_ein }}).

    BOARD MEMBERS:
    {% for member in input.board_members %}
    - {{ member.name }}{% if member.title %}, {{ member.title }}{% endif %}
      {% if member.affiliations %}Affiliations: {{ member.affiliations }}{% endif %}
    {% endfor %}

    {% if input.target_funder_name %}
    TARGET FUNDER ANALYSIS:
    - Funder: {{ input.target_funder_name }}
    {% if input.target_funder_board %}
    - Funder Board: {{ input.target_funder_board | join(', ') }}
    {% endif %}
    {% endif %}

    {% if input.key_donors %}
    KEY DONORS: {{ input.key_donors | join(', ') }}
    {% endif %}

    {% if input.partner_organizations %}
    PARTNER ORGANIZATIONS: {{ input.partner_organizations | join(', ') }}
    {% endif %}

    Provide comprehensive network intelligence including:

    1. BOARD MEMBER PROFILES:
       - For each board member: profile with affiliations, centrality, influence
       - Identify direct and indirect connections
       - Assess strategic value to organization

    2. NETWORK CONNECTIONS:
       - Map all connections between entities
       - Categorize by relationship type
       - Assess connection strength and strategic value

    3. CENTRALITY METRICS:
       - Calculate degree, betweenness, closeness, eigenvector centrality
       - Provide overall centrality assessment
       - Interpret what centrality means strategically

    4. NETWORK CLUSTERS:
       - Identify communities/clusters within network
       - Describe cluster focus and strategic relevance

    5. STRATEGIC CONNECTIONS:
       - Identify high-value connection opportunities
       - Provide cultivation strategies and timelines
       - Estimate success probability

    6. NETWORK ANALYSIS:
       - Executive summary of network characteristics
       - Network size, density, average path length
       - Key strengths, gaps, and opportunities
       - Recommended board additions
       - Cultivation priorities

    {% if input.target_funder_name %}
    7. FUNDER CONNECTION ANALYSIS:
       - Identify direct board connections to funder
       - Map indirect relationship pathways
       - Assess overall connection strength
       - Describe competitive advantage from connections
       - Provide cultivation strategy and immediate actions
       - Estimate success probability
    {% endif %}

    Be thorough and strategic. Focus on actionable insights for relationship cultivation.
  "#
}
