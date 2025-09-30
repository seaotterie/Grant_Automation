"""
Network Intelligence Tool Data Models
Board network analysis and relationship mapping
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict


class NetworkStrength(str, Enum):
    """Network connection strength"""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    MINIMAL = "minimal"


class RelationshipType(str, Enum):
    """Type of relationship"""
    BOARD_MEMBER = "board_member"
    ADVISOR = "advisor"
    DONOR = "donor"
    PARTNER = "partner"
    VENDOR = "vendor"
    PEER = "peer"


@dataclass
class NetworkIntelligenceInput:
    """Input for network intelligence analysis"""

    # Organization identification
    organization_ein: str
    organization_name: str

    # Board members (name, title, affiliations)
    board_members: List[Dict[str, str]]  # [{"name": "...", "title": "...", "affiliations": "..."}]

    # Target analysis (optional - for opportunity-specific network analysis)
    target_funder_name: Optional[str] = None
    target_funder_board: Optional[List[str]] = None

    # Additional network data
    key_donors: Optional[List[str]] = None
    partner_organizations: Optional[List[str]] = None
    advisory_board: Optional[List[str]] = None


@dataclass
class BoardMemberProfile:
    """Individual board member profile"""

    name: str
    title: Optional[str]
    current_affiliations: List[str]
    past_affiliations: List[str]

    # Network metrics
    centrality_score: float  # 0-1
    influence_score: float  # 0-1
    connection_count: int

    # Connections
    direct_connections: List[str]
    indirect_connections: List[str]

    # Strategic value
    strategic_value_score: float  # 0-1
    strategic_value_reasoning: str


@dataclass
class NetworkConnection:
    """Connection between entities"""

    from_entity: str
    to_entity: str
    connection_type: RelationshipType
    strength: NetworkStrength
    description: str
    strategic_value: str


@dataclass
class CentralityMetrics:
    """Network centrality metrics"""

    # Degree centrality (number of connections)
    degree_centrality: float  # 0-1

    # Betweenness centrality (bridge between networks)
    betweenness_centrality: float  # 0-1

    # Closeness centrality (distance to all others)
    closeness_centrality: float  # 0-1

    # Eigenvector centrality (connections to influential nodes)
    eigenvector_centrality: float  # 0-1

    # Overall centrality score
    overall_centrality: float  # 0-1

    # Interpretation
    centrality_interpretation: str


@dataclass
class NetworkCluster:
    """Identified network cluster/community"""

    cluster_id: str
    cluster_name: str
    member_count: int
    members: List[str]
    cluster_focus: str
    strategic_relevance: str


@dataclass
class RelationshipPathway:
    """Pathway from organization to target"""

    target: str
    pathway: List[str]  # List of entities forming the path
    pathway_strength: NetworkStrength
    pathway_description: str
    cultivation_strategy: str


@dataclass
class StrategicConnection:
    """Strategic connection opportunity"""

    target_entity: str
    connection_type: str
    priority: str  # "high", "medium", "low"
    rationale: str
    cultivation_steps: List[str]
    estimated_timeline: str
    success_probability: float  # 0-1


@dataclass
class NetworkIntelligenceAnalysis:
    """Overall network analysis insights"""

    # Executive summary
    network_executive_summary: str

    # Network characteristics
    network_size: int
    network_density: float  # 0-1
    average_path_length: float

    # Network strengths
    network_strengths: List[str]
    key_influencers: List[str]

    # Network gaps
    network_gaps: List[str]
    recommended_additions: List[str]

    # Strategic opportunities
    strategic_opportunities: List[str]
    cultivation_priorities: List[str]


@dataclass
class FunderConnectionAnalysis:
    """Analysis of connections to target funder"""

    funder_name: str

    # Direct connections
    direct_board_connections: List[str]
    direct_connection_count: int

    # Indirect connections
    indirect_pathways: List[RelationshipPathway]
    strongest_pathway: Optional[RelationshipPathway]

    # Connection strength
    overall_connection_strength: NetworkStrength
    connection_advantage: str  # Description of competitive advantage

    # Cultivation strategy
    recommended_cultivation_strategy: str
    immediate_actions: List[str]
    success_probability: float  # 0-1


@dataclass
class NetworkIntelligenceOutput:
    """Complete network intelligence output"""

    # Board member profiles
    board_member_profiles: List[BoardMemberProfile]

    # Network connections
    all_connections: List[NetworkConnection]
    strategic_connections: List[StrategicConnection]

    # Centrality analysis
    network_centrality: CentralityMetrics

    # Clusters/communities
    identified_clusters: List[NetworkCluster]

    # Overall network analysis
    network_analysis: NetworkIntelligenceAnalysis

    # Target funder analysis (if provided)
    funder_connection_analysis: Optional[FunderConnectionAnalysis]

    # Metadata
    analysis_date: str
    network_quality_score: float  # 0-1, based on data completeness
    confidence_level: float  # 0-1
    processing_time_seconds: float
    api_cost_usd: float


# Cost configuration
NETWORK_INTELLIGENCE_COST = 0.04  # $0.04 per analysis
