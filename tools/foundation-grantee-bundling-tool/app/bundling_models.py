"""
Foundation Grantee Bundling Tool Data Models
Multi-foundation grant aggregation and co-funding analysis models
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


# ============================================================================
# INPUT MODELS
# ============================================================================

@dataclass
class GranteeBundlingInput:
    """Input for multi-foundation bundling analysis"""

    # Required fields
    foundation_eins: List[str]  # Multiple foundation EINs to analyze

    # Optional filters
    tax_years: List[int] = field(default_factory=lambda: [2022, 2023, 2024])
    min_foundations: int = 2  # Minimum funders to flag as "bundled"
    include_grant_purposes: bool = True
    geographic_filter: Optional[List[str]] = None  # State codes (e.g., ['VA', 'MD', 'DC'])
    min_grant_amount: float = 0  # Filter out small grants

    # Advanced options
    normalize_recipient_names: bool = True
    fuzzy_matching_threshold: float = 0.85  # For name matching without EINs


# ============================================================================
# OUTPUT MODELS
# ============================================================================

@dataclass
class FundingSource:
    """Single grant from a foundation to a grantee"""

    foundation_ein: str
    foundation_name: str
    grant_amount: float
    grant_year: int
    grant_purpose: Optional[str] = None
    grant_tier: Optional[str] = None  # 'major', 'significant', 'moderate', 'small'


@dataclass
class BundledGrantee:
    """Organization funded by multiple foundations"""

    # Grantee identification
    grantee_ein: Optional[str]  # May be None if not available
    grantee_name: str
    normalized_name: str  # Standardized for matching

    # Funding summary
    funder_count: int
    total_funding: float
    average_grant_size: float

    # Detailed funding sources
    funding_sources: List[FundingSource]  # All grants to this grantee

    # Temporal data
    first_grant_year: int
    last_grant_year: int
    funding_consistency: float  # 0-1, based on year-over-year funding

    # Geographic and thematic
    geographic_location: Optional[str]  # State or city
    common_purposes: List[str]  # Thematic keywords across grants
    purpose_diversity_score: float  # 0-1, indicates focus vs. diverse funding

    # Strategic intelligence
    funding_stability: str  # 'stable', 'growing', 'declining', 'new'
    co_funding_strength: float  # 0-1, how often funders co-fund this org


@dataclass
class FoundationOverlap:
    """Overlap between two foundations"""

    foundation_ein_1: str
    foundation_name_1: str
    foundation_ein_2: str
    foundation_name_2: str

    shared_grantees_count: int
    shared_grantee_eins: List[str]
    total_overlap_funding: float

    jaccard_similarity: float  # 0-1, intersection/union
    overlap_percentage_1: float  # Shared grantees / total grantees of foundation 1
    overlap_percentage_2: float  # Shared grantees / total grantees of foundation 2


@dataclass
class ThematicCluster:
    """Group of grantees with similar purposes"""

    cluster_id: str
    cluster_name: str  # e.g., "Veterans Services", "Education K-12"
    grantee_count: int
    total_funding: float

    member_grantees: List[str]  # EINs or names
    common_keywords: List[str]
    funding_foundations: List[str]  # EINs of foundations supporting this cluster


@dataclass
class GranteeBundlingOutput:
    """Complete output from multi-foundation bundling analysis"""

    # Input summary
    total_foundations_analyzed: int
    foundation_eins: List[str]
    tax_years_analyzed: List[int]

    # Grantee analysis
    total_unique_grantees: int
    bundled_grantees: List[BundledGrantee]  # Funded by ≥ min_foundations
    single_funder_grantees_count: int

    # Co-funding patterns
    foundation_overlap_matrix: List[FoundationOverlap]  # All foundation pairs
    top_co_funded_orgs: List[BundledGrantee]  # Sorted by funder count

    # Thematic analysis
    thematic_clusters: List[ThematicCluster]

    # Aggregate statistics
    total_grants_analyzed: int
    total_funding_amount: float
    average_grants_per_foundation: float
    average_grantees_per_foundation: float

    # Data quality
    data_completeness_score: float  # 0-1, based on available EINs and purposes
    recipient_matching_confidence: float  # 0-1, average confidence in name matching

    # Processing metadata
    processing_time_seconds: float
    analysis_date: str
    api_cost_usd: float  # Should be 0.00 for this tool


# ============================================================================
# CO-FUNDING ANALYSIS MODELS (Phase 2)
# ============================================================================

@dataclass
class CoFundingAnalysisInput:
    """Input for co-funding and funder similarity analysis"""

    bundling_results: GranteeBundlingOutput  # From Phase 1
    similarity_threshold: float = 0.3  # Minimum Jaccard to consider "similar"
    max_peer_funders: int = 10
    include_network_graph: bool = True


@dataclass
class FunderSimilarity:
    """Similarity between two foundations"""

    foundation_ein_1: str
    foundation_name_1: str
    foundation_ein_2: str
    foundation_name_2: str

    # Similarity metrics
    similarity_score: float  # 0-1, weighted Jaccard with recency
    jaccard_similarity: float  # 0-1, pure set overlap
    shared_grantees_count: int

    # Financial overlap
    total_co_funding_amount: float
    average_co_grant_size: float

    # Temporal
    recency_score: float  # 0-1, weighted by recent grants
    funding_years_overlap: List[int]

    # Shared characteristics
    shared_grantees: List[str]  # EINs
    common_geographic_focus: Optional[str]
    common_thematic_focus: List[str]


@dataclass
class PeerFunderGroup:
    """Cluster of similar funders (detected via Louvain)"""

    cluster_id: str
    cluster_name: str  # Auto-generated or manual

    # Members
    member_foundations: List[str]  # EINs
    member_count: int

    # Shared characteristics
    shared_focus_areas: List[str]
    geographic_concentration: Optional[str]
    average_grant_size: float
    total_cluster_funding: float

    # Network metrics
    cluster_density: float  # How interconnected members are
    bridge_foundations: List[str]  # Foundations connecting to other clusters


@dataclass
class FunderRecommendation:
    """Strategic recommendation for prospecting"""

    recommended_foundation_ein: str
    recommended_foundation_name: str
    recommendation_type: str  # 'peer_funder', 'cluster_member', 'bridge'

    rationale: str
    confidence_score: float  # 0-1
    supporting_evidence: List[str]

    # Connection details
    shared_funders: List[str]  # EINs of foundations you both fund
    similarity_to_current_funders: float

    # Strategic notes
    estimated_grant_range: str  # e.g., "$25K-$100K"
    suggested_approach: str
    priority: str  # 'high', 'medium', 'low'


@dataclass
class CoFundingAnalysisOutput:
    """Output from co-funding and peer funder analysis"""

    # Funder similarity
    funder_similarity_pairs: List[FunderSimilarity]
    highly_similar_pairs: List[FunderSimilarity]  # Above threshold

    # Peer groups (Louvain clustering)
    peer_funder_groups: List[PeerFunderGroup]

    # Network graph (if requested)
    foundation_network_graph: Optional[Dict[str, Any]]  # NetworkX serialized
    network_statistics: Dict[str, Any]

    # Recommendations
    recommendations: List[FunderRecommendation]

    # Processing metadata
    processing_time_seconds: float
    analysis_date: str


# ============================================================================
# UTILITY MODELS
# ============================================================================

class FundingStability(str, Enum):
    """Funding pattern classification"""
    STABLE = "stable"  # Consistent funding over years
    GROWING = "growing"  # Increasing funding over time
    DECLINING = "declining"  # Decreasing funding
    NEW = "new"  # Recent grantee (< 2 years)
    SPORADIC = "sporadic"  # Inconsistent funding


class RecommendationType(str, Enum):
    """Types of funder recommendations"""
    PEER_FUNDER = "peer_funder"  # Similar to current funders
    CLUSTER_MEMBER = "cluster_member"  # In same peer group
    BRIDGE_FUNDER = "bridge_funder"  # Connects multiple clusters
    EMERGING_FUNDER = "emerging_funder"  # New entrant to issue area
    GEOGRAPHIC_MATCH = "geographic_match"  # Geographic alignment


# ============================================================================
# CONSTANTS
# ============================================================================

# Cost configuration
BUNDLING_TOOL_COST = 0.00  # No AI calls, pure data aggregation

# Matching thresholds
DEFAULT_FUZZY_THRESHOLD = 0.85
MIN_SIMILARITY_THRESHOLD = 0.3

# Grant size tiers (for classification)
GRANT_TIER_THRESHOLDS = {
    'major': 100000,      # >= $100K
    'significant': 25000,  # $25K - $99K
    'moderate': 5000,      # $5K - $24K
    'small': 0             # < $5K
}
