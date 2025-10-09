"""
Test Suite for Foundation Network Graph (Phase 3)
Tests graph construction, queries, pathfinding, and influence scoring.
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import networkx as nx
from src.analytics.foundation_network_graph import (
    FoundationNetworkGraph,
    NetworkQueryEngine,
    NetworkNode,
    NetworkEdge
)
from src.analytics.network_pathfinder import (
    NetworkPathfinder,
    InfluenceAnalyzer,
    ConnectionPath,
    InfluenceScore
)


# ============================================================================
# MOCK DATA FIXTURES
# ============================================================================

@pytest.fixture
def mock_bundling_output():
    """Create mock bundling output for testing"""
    from dataclasses import dataclass, field
    from typing import List, Dict, Any

    @dataclass
    class MockFundingSource:
        foundation_ein: str
        foundation_name: str
        grant_amount: float
        grant_year: int

    @dataclass
    class MockBundledGrantee:
        grantee_ein: str
        grantee_name: str
        funder_count: int
        total_funding: float
        average_grant_size: float
        funding_stability: str
        first_grant_year: int
        last_grant_year: int
        funding_sources: List[MockFundingSource]
        common_purposes: List[str] = field(default_factory=list)

    @dataclass
    class MockBundlingOutput:
        foundation_eins: List[str]
        bundled_grantees: List[MockBundledGrantee]
        total_foundations_analyzed: int
        total_unique_grantees: int

    # Create test data: 3 foundations, 5 grantees
    # Foundation A funds: Grantee 1, 2, 3
    # Foundation B funds: Grantee 2, 3, 4
    # Foundation C funds: Grantee 3, 4, 5

    grantees = [
        MockBundledGrantee(
            grantee_ein="11-1111111",
            grantee_name="Nonprofit Alpha",
            funder_count=1,
            total_funding=100000,
            average_grant_size=100000,
            funding_stability="stable",
            first_grant_year=2023,
            last_grant_year=2023,
            funding_sources=[
                MockFundingSource("91-1111111", "Foundation A", 100000, 2023)
            ],
            common_purposes=["education"]
        ),
        MockBundledGrantee(
            grantee_ein="22-2222222",
            grantee_name="Nonprofit Beta",
            funder_count=2,
            total_funding=250000,
            average_grant_size=125000,
            funding_stability="stable",
            first_grant_year=2022,
            last_grant_year=2023,
            funding_sources=[
                MockFundingSource("91-1111111", "Foundation A", 150000, 2023),
                MockFundingSource("92-2222222", "Foundation B", 100000, 2022)
            ],
            common_purposes=["health", "education"]
        ),
        MockBundledGrantee(
            grantee_ein="33-3333333",
            grantee_name="Nonprofit Gamma",
            funder_count=3,
            total_funding=600000,
            average_grant_size=200000,
            funding_stability="growing",
            first_grant_year=2021,
            last_grant_year=2023,
            funding_sources=[
                MockFundingSource("91-1111111", "Foundation A", 200000, 2023),
                MockFundingSource("92-2222222", "Foundation B", 250000, 2022),
                MockFundingSource("93-3333333", "Foundation C", 150000, 2021)
            ],
            common_purposes=["environment", "conservation"]
        ),
        MockBundledGrantee(
            grantee_ein="44-4444444",
            grantee_name="Nonprofit Delta",
            funder_count=2,
            total_funding=300000,
            average_grant_size=150000,
            funding_stability="stable",
            first_grant_year=2022,
            last_grant_year=2023,
            funding_sources=[
                MockFundingSource("92-2222222", "Foundation B", 175000, 2023),
                MockFundingSource("93-3333333", "Foundation C", 125000, 2022)
            ],
            common_purposes=["arts", "culture"]
        ),
        MockBundledGrantee(
            grantee_ein="55-5555555",
            grantee_name="Nonprofit Epsilon",
            funder_count=1,
            total_funding=80000,
            average_grant_size=80000,
            funding_stability="new",
            first_grant_year=2023,
            last_grant_year=2023,
            funding_sources=[
                MockFundingSource("93-3333333", "Foundation C", 80000, 2023)
            ],
            common_purposes=["research"]
        )
    ]

    return MockBundlingOutput(
        foundation_eins=["91-1111111", "92-2222222", "93-3333333"],
        bundled_grantees=grantees,
        total_foundations_analyzed=3,
        total_unique_grantees=5
    )


@pytest.fixture
def sample_graph(mock_bundling_output):
    """Build sample graph from mock data"""
    graph_builder = FoundationNetworkGraph()
    graph = graph_builder.build_from_bundling_results(mock_bundling_output)
    return graph, graph_builder


# ============================================================================
# GRAPH CONSTRUCTION TESTS
# ============================================================================

def test_graph_construction_basic(sample_graph):
    """Test basic graph construction"""
    graph, builder = sample_graph

    # Should have 8 nodes: 3 foundations + 5 grantees
    assert graph.number_of_nodes() == 8

    # Should have 9 edges (based on funding sources)
    # Foundation A: 3 edges (to grantees 1, 2, 3)
    # Foundation B: 3 edges (to grantees 2, 3, 4)
    # Foundation C: 3 edges (to grantees 3, 4, 5)
    assert graph.number_of_edges() == 9


def test_graph_bipartite_structure(sample_graph):
    """Test that graph is properly bipartite (foundations only connect to grantees)"""
    graph, builder = sample_graph

    # Get foundation and grantee nodes
    foundation_nodes = [
        n for n, d in graph.nodes(data=True)
        if d.get('node_type') == 'foundation'
    ]
    grantee_nodes = [
        n for n, d in graph.nodes(data=True)
        if d.get('node_type') == 'grantee'
    ]

    assert len(foundation_nodes) == 3
    assert len(grantee_nodes) == 5

    # Verify bipartite structure: foundations should only connect to grantees
    for foundation in foundation_nodes:
        for neighbor in graph.neighbors(foundation):
            neighbor_type = graph.nodes[neighbor].get('node_type')
            assert neighbor_type == 'grantee', f"Foundation {foundation} connected to non-grantee {neighbor}"


def test_edge_weights(sample_graph):
    """Test that edge weights are correctly assigned"""
    graph, builder = sample_graph

    # Check specific edge: Foundation A → Grantee Gamma (should be $200,000)
    foundation_a = "91-1111111"
    grantee_gamma = "33-3333333"

    if graph.has_edge(foundation_a, grantee_gamma):
        edge_data = graph[foundation_a][grantee_gamma]
        assert edge_data['weight'] == 200000
        assert edge_data['total_amount'] == 200000
        assert edge_data['grant_count'] == 1
        assert 2023 in edge_data['years']


def test_node_attributes(sample_graph):
    """Test that nodes have correct attributes"""
    graph, builder = sample_graph

    # Check grantee node attributes
    grantee_gamma = "33-3333333"
    if grantee_gamma in graph:
        node_data = graph.nodes[grantee_gamma]
        assert node_data['node_type'] == 'grantee'
        assert node_data['name'] == "Nonprofit Gamma"
        assert node_data['funder_count'] == 3
        assert node_data['total_funding'] == 600000
        assert node_data['funding_stability'] == 'growing'


# ============================================================================
# NETWORK STATISTICS TESTS
# ============================================================================

def test_network_statistics(sample_graph):
    """Test network statistics computation"""
    graph, builder = sample_graph

    stats = builder.get_network_statistics()

    assert stats['total_nodes'] == 8
    assert stats['total_edges'] == 9
    assert stats['total_foundations'] == 3
    assert stats['total_grantees'] == 5
    assert stats['network_density'] > 0  # Should be connected
    assert stats['total_grant_amount'] == 1330000  # Sum of all grants


def test_most_connected_grantee(sample_graph):
    """Test identification of most connected grantee"""
    graph, builder = sample_graph

    stats = builder.get_network_statistics()

    # Nonprofit Gamma (33-3333333) has 3 funders - should be most connected
    assert stats['most_connected_grantee'] == "33-3333333"


# ============================================================================
# QUERY ENGINE TESTS
# ============================================================================

def test_find_co_funders(sample_graph):
    """Test finding co-funders for a grantee"""
    graph, builder = sample_graph

    query_engine = NetworkQueryEngine(graph)

    # Grantee Gamma has 3 co-funders
    co_funders = query_engine.find_co_funders("33-3333333")

    assert len(co_funders) == 3

    # Should be sorted by total funding (Foundation B gave most: $250K)
    assert co_funders[0]['foundation_ein'] == "92-2222222"
    assert co_funders[0]['total_funding'] == 250000


def test_find_shared_grantees(sample_graph):
    """Test finding shared grantees between two foundations"""
    graph, builder = sample_graph

    query_engine = NetworkQueryEngine(graph)

    # Foundation A and B share grantees 2 and 3
    shared = query_engine.find_shared_grantees("91-1111111", "92-2222222")

    assert len(shared) == 2

    # Check that we got the right grantees
    shared_eins = [g['grantee_ein'] for g in shared]
    assert "22-2222222" in shared_eins  # Nonprofit Beta
    assert "33-3333333" in shared_eins  # Nonprofit Gamma


def test_get_funding_path(sample_graph):
    """Test pathfinding between organizations"""
    graph, builder = sample_graph

    query_engine = NetworkQueryEngine(graph)

    # Find path from Foundation A to Foundation B
    # Should go through shared grantees
    paths = query_engine.get_funding_path("91-1111111", "92-2222222", max_hops=3)

    assert len(paths) > 0

    # Path should be length 3: Foundation A → Grantee → Foundation B
    for path in paths:
        assert len(path) == 3


def test_grantee_portfolio(sample_graph):
    """Test getting complete grantee portfolio for a foundation"""
    graph, builder = sample_graph

    query_engine = NetworkQueryEngine(graph)

    # Foundation A funds 3 grantees
    portfolio = query_engine.get_grantee_portfolio("91-1111111")

    assert portfolio['total_grantees'] == 3
    assert portfolio['total_funding'] == 450000  # 100K + 150K + 200K
    assert portfolio['total_grants'] == 3


# ============================================================================
# PATHFINDING TESTS
# ============================================================================

def test_pathfinder_construction(sample_graph):
    """Test NetworkPathfinder initialization"""
    graph, builder = sample_graph

    pathfinder = NetworkPathfinder(graph)
    assert pathfinder.graph is not None


def test_find_board_pathways(sample_graph):
    """Test finding strategic pathways"""
    graph, builder = sample_graph

    pathfinder = NetworkPathfinder(graph)

    # Find paths from Foundation A to Grantee Delta
    # Path: Foundation A → Grantee Gamma → Foundation B → Grantee Delta
    paths = pathfinder.find_board_pathways("91-1111111", "44-4444444")

    # Should find at least one path
    assert len(paths) > 0

    # Check first path properties
    first_path = paths[0]
    assert isinstance(first_path, ConnectionPath)
    assert len(first_path.path_nodes) >= 2
    assert first_path.path_strength > 0
    assert len(first_path.cultivation_strategy) > 0


def test_path_strength_calculation(sample_graph):
    """Test path strength scoring"""
    graph, builder = sample_graph

    pathfinder = NetworkPathfinder(graph)

    # Paths through high-value grants should have higher strength
    paths = pathfinder.find_board_pathways("91-1111111", "93-3333333")

    if paths:
        # Verify strength is positive
        for path in paths:
            assert path.path_strength > 0


def test_cultivation_strategy_generation(sample_graph):
    """Test cultivation strategy is generated"""
    graph, builder = sample_graph

    pathfinder = NetworkPathfinder(graph)

    paths = pathfinder.find_board_pathways("91-1111111", "55-5555555")

    if paths:
        for path in paths:
            # Strategy should be non-empty string
            assert isinstance(path.cultivation_strategy, str)
            assert len(path.cultivation_strategy) > 0

            # Should mention leveraging connection for longer paths
            if path.path_length > 1:
                assert any(keyword in path.cultivation_strategy.lower()
                          for keyword in ['leverage', 'connection', 'introduction', 'relationship'])


# ============================================================================
# INFLUENCE ANALYZER TESTS
# ============================================================================

def test_influence_analyzer_initialization(sample_graph):
    """Test InfluenceAnalyzer initialization"""
    graph, builder = sample_graph

    analyzer = InfluenceAnalyzer(graph)
    assert analyzer.graph is not None


def test_score_node_influence(sample_graph):
    """Test influence scoring for individual nodes"""
    graph, builder = sample_graph

    analyzer = InfluenceAnalyzer(graph)

    # Score the most connected grantee (Gamma with 3 funders)
    score = analyzer.score_node_influence("33-3333333")

    assert score is not None
    assert isinstance(score, InfluenceScore)
    assert score.node_id == "33-3333333"
    assert score.degree_centrality > 0
    assert score.pagerank_score > 0
    assert score.influence_tier in ['high', 'medium', 'low']


def test_degree_centrality_calculation(sample_graph):
    """Test degree centrality values"""
    graph, builder = sample_graph

    analyzer = InfluenceAnalyzer(graph)

    # Most connected grantee should have higher centrality
    gamma_score = analyzer.score_node_influence("33-3333333")  # 3 funders
    epsilon_score = analyzer.score_node_influence("55-5555555")  # 1 funder

    assert gamma_score.degree_centrality > epsilon_score.degree_centrality


def test_pagerank_scoring(sample_graph):
    """Test PageRank influence scoring"""
    graph, builder = sample_graph

    analyzer = InfluenceAnalyzer(graph)

    # Grantee with more funders should have higher PageRank
    gamma_score = analyzer.score_node_influence("33-3333333")

    assert gamma_score.pagerank_score > 0


def test_influence_tier_classification(sample_graph):
    """Test influence tier assignment"""
    graph, builder = sample_graph

    analyzer = InfluenceAnalyzer(graph)

    # Most connected node should be high influence
    gamma_score = analyzer.score_node_influence("33-3333333")

    # With 3 connections out of 8 nodes, should have decent centrality
    assert gamma_score.influence_tier in ['high', 'medium']


def test_top_influencers(sample_graph):
    """Test getting top influencers"""
    graph, builder = sample_graph

    analyzer = InfluenceAnalyzer(graph)

    # Get top 3 influencers
    top_influencers = analyzer.score_top_influencers(limit=3)

    assert len(top_influencers) <= 3

    # Should be sorted by PageRank (descending)
    if len(top_influencers) >= 2:
        assert top_influencers[0].pagerank_score >= top_influencers[1].pagerank_score


def test_influence_distribution(sample_graph):
    """Test influence distribution statistics"""
    graph, builder = sample_graph

    analyzer = InfluenceAnalyzer(graph)

    distribution = analyzer.get_influence_distribution()

    assert 'total_nodes' in distribution
    assert distribution['total_nodes'] == 8
    assert 'high_influence_count' in distribution
    assert 'medium_influence_count' in distribution
    assert 'low_influence_count' in distribution

    # Sum of tiers should equal total nodes
    total_by_tier = (
        distribution['high_influence_count'] +
        distribution['medium_influence_count'] +
        distribution['low_influence_count']
    )
    assert total_by_tier == 8


# ============================================================================
# EXPORT FUNCTIONALITY TESTS
# ============================================================================

def test_export_to_json(sample_graph):
    """Test JSON export functionality"""
    graph, builder = sample_graph

    json_graph = builder.export_to_json()

    assert 'nodes' in json_graph
    assert 'edges' in json_graph
    assert 'metadata' in json_graph

    # Should have correct counts
    assert len(json_graph['nodes']) == 8
    assert len(json_graph['edges']) == 9

    # Check node structure
    first_node = json_graph['nodes'][0]
    assert 'id' in first_node
    assert 'type' in first_node
    assert 'name' in first_node

    # Check edge structure
    first_edge = json_graph['edges'][0]
    assert 'source' in first_edge
    assert 'target' in first_edge
    assert 'weight' in first_edge


def test_export_to_graphml(sample_graph):
    """Test GraphML export functionality"""
    graph, builder = sample_graph

    graphml_string = builder.export_to_graphml()

    assert isinstance(graphml_string, str)
    assert len(graphml_string) > 0

    # Should contain GraphML XML markers
    assert '<?xml' in graphml_string or '<graphml' in graphml_string

    # Should contain node and edge definitions
    assert '<node' in graphml_string
    assert '<edge' in graphml_string


def test_graphml_reimport(sample_graph):
    """Test that exported GraphML can be re-imported"""
    graph, builder = sample_graph

    # Export to GraphML
    graphml_string = builder.export_to_graphml()

    # Re-import with NetworkX
    import io
    graphml_io = io.StringIO(graphml_string)
    reimported_graph = nx.read_graphml(graphml_io)

    # Should have same structure
    assert reimported_graph.number_of_nodes() == graph.number_of_nodes()
    assert reimported_graph.number_of_edges() == graph.number_of_edges()


# ============================================================================
# EDGE CASES & ERROR HANDLING
# ============================================================================

def test_query_nonexistent_node(sample_graph):
    """Test querying for non-existent node"""
    graph, builder = sample_graph

    query_engine = NetworkQueryEngine(graph)

    # Query for non-existent grantee
    co_funders = query_engine.find_co_funders("99-9999999")

    # Should return empty list, not error
    assert co_funders == []


def test_pathfinding_no_path(sample_graph):
    """Test pathfinding when no path exists"""
    graph, builder = sample_graph

    pathfinder = NetworkPathfinder(graph)

    # Try to find path to non-existent node
    paths = pathfinder.find_board_pathways("91-1111111", "99-9999999")

    # Should return empty list
    assert paths == []


def test_influence_nonexistent_node(sample_graph):
    """Test influence scoring for non-existent node"""
    graph, builder = sample_graph

    analyzer = InfluenceAnalyzer(graph)

    # Score non-existent node
    score = analyzer.score_node_influence("99-9999999")

    # Should return None
    assert score is None


def test_empty_graph():
    """Test operations on empty graph"""
    graph_builder = FoundationNetworkGraph()

    # Empty graph should have 0 nodes
    assert graph_builder.graph.number_of_nodes() == 0

    # Statistics should handle empty graph
    stats = graph_builder.get_network_statistics()
    assert stats['total_nodes'] == 0
    assert stats['total_edges'] == 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_workflow(mock_bundling_output):
    """Test complete workflow: build → query → analyze → export"""

    # Step 1: Build graph
    graph_builder = FoundationNetworkGraph()
    graph = graph_builder.build_from_bundling_results(mock_bundling_output)

    assert graph.number_of_nodes() > 0

    # Step 2: Query for co-funders
    query_engine = NetworkQueryEngine(graph)
    co_funders = query_engine.find_co_funders("33-3333333")

    assert len(co_funders) == 3

    # Step 3: Find pathways
    pathfinder = NetworkPathfinder(graph)
    paths = pathfinder.find_board_pathways("91-1111111", "44-4444444")

    assert len(paths) > 0

    # Step 4: Analyze influence
    analyzer = InfluenceAnalyzer(graph)
    top_influencers = analyzer.score_top_influencers(limit=5)

    assert len(top_influencers) > 0

    # Step 5: Export
    json_export = graph_builder.export_to_json()
    graphml_export = graph_builder.export_to_graphml()

    assert len(json_export['nodes']) > 0
    assert len(graphml_export) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
