"""
Network Pathfinder Module
Strategic pathfinding and influence scoring for foundation networks.

Purpose: Find connection paths and calculate influence metrics
Integration: Phase 3 network graph analytics
"""

import networkx as nx
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ConnectionPath:
    """A path from source to target in the network"""
    path_nodes: List[str]  # Sequence of EINs
    path_length: int  # Number of hops
    path_strength: float  # Based on grant amounts
    path_description: str  # Human-readable
    cultivation_strategy: str  # How to leverage this path
    path_details: List[Dict[str, Any]] = field(default_factory=list)  # Detailed step info


@dataclass
class InfluenceScore:
    """Influence metrics for a network node"""
    node_id: str
    node_name: str
    node_type: str  # foundation or grantee
    degree_centrality: float  # Connection count normalized
    pagerank_score: float  # PageRank influence
    closeness_centrality: float  # Access to network
    betweenness_centrality: float  # Bridge position (approximated)
    influence_tier: str  # high, medium, low
    influence_interpretation: str  # Human-readable assessment
    key_connections: List[str] = field(default_factory=list)  # Top connections


class NetworkPathfinder:
    """
    Find strategic pathways and calculate influence in foundation networks.

    Capabilities:
    - Board-based pathway detection
    - Path strength calculation
    - Cultivation strategy generation
    - Influence scoring (simplified for performance)
    """

    def __init__(self, graph: nx.Graph):
        self.graph = graph
        self.logger = logging.getLogger(__name__)

    def find_board_pathways(self, source: str, target: str) -> List[ConnectionPath]:
        """
        Find board-based pathways from source to target funder.

        Note: Currently finds all pathways. Board member filtering
        will be added when board nodes are integrated (Phase 2-deferred).

        Args:
            source: Source organization EIN
            target: Target foundation EIN

        Returns:
            List of ConnectionPath objects sorted by strength
        """
        try:
            if source not in self.graph or target not in self.graph:
                self.logger.warning(f"Source {source} or target {target} not in graph")
                return []

            # Find all simple paths up to 3 hops
            try:
                all_paths = list(nx.all_simple_paths(
                    self.graph, source, target, cutoff=3
                ))
            except nx.NetworkXNoPath:
                self.logger.info(f"No path found between {source} and {target}")
                return []

            # Convert to ConnectionPath objects
            connection_paths = []
            for path in all_paths[:20]:  # Limit to top 20 raw paths
                conn_path = self._create_connection_path(path)
                if conn_path:
                    connection_paths.append(conn_path)

            # Sort by path strength (descending)
            connection_paths.sort(key=lambda p: p.path_strength, reverse=True)

            # Return top 5 strongest paths
            return connection_paths[:5]

        except Exception as e:
            self.logger.error(f"Error finding board pathways: {e}", exc_info=True)
            return []

    def _create_connection_path(self, path: List[str]) -> Optional[ConnectionPath]:
        """Convert node path to ConnectionPath object with details"""
        try:
            # Build human-readable description
            description_parts = []
            path_details = []
            total_weight = 0
            min_weight = float('inf')

            for i in range(len(path) - 1):
                current_node = path[i]
                next_node = path[i + 1]

                current_data = self.graph.nodes[current_node]
                next_data = self.graph.nodes[next_node]
                edge_data = self.graph[current_node][next_node]

                current_name = current_data.get('name', current_node)
                next_name = next_data.get('name', next_node)
                edge_type = edge_data.get('edge_type', 'connection')
                weight = edge_data.get('weight', 0)

                total_weight += weight
                min_weight = min(min_weight, weight if weight > 0 else float('inf'))

                if edge_type == 'grant':
                    description_parts.append(
                        f"{current_name} funds {next_name} (${weight:,.0f})"
                    )
                else:
                    description_parts.append(
                        f"{current_name} connects to {next_name}"
                    )

                path_details.append({
                    'from_node': current_node,
                    'from_name': current_name,
                    'to_node': next_node,
                    'to_name': next_name,
                    'relationship_type': edge_type,
                    'weight': weight,
                    'years': edge_data.get('years', [])
                })

            # Calculate path strength (weighted average, favoring bottlenecks)
            num_edges = len(path) - 1
            avg_weight = total_weight / num_edges if num_edges > 0 else 0

            # Path strength: combination of average and minimum (bottleneck matters)
            path_strength = (avg_weight * 0.7 + min_weight * 0.3) if min_weight != float('inf') else avg_weight

            # Generate cultivation strategy
            strategy = self._generate_cultivation_strategy(path, path_details)

            # Create path description
            description = " -> ".join(description_parts)

            return ConnectionPath(
                path_nodes=path,
                path_length=len(path) - 1,
                path_strength=path_strength,
                path_description=description,
                cultivation_strategy=strategy,
                path_details=path_details
            )

        except Exception as e:
            self.logger.error(f"Error creating connection path: {e}")
            return None

    def _generate_cultivation_strategy(self, path: List[str], path_details: List[Dict]) -> str:
        """
        Generate strategic cultivation advice based on path.

        Args:
            path: List of node EINs
            path_details: Detailed information about each step

        Returns:
            Strategic cultivation recommendation
        """
        try:
            path_length = len(path) - 1

            if path_length == 1:
                # Direct connection
                return "Direct relationship - apply with confidence emphasizing shared interests"

            elif path_length == 2:
                # One intermediary
                intermediate = path[1]
                intermediate_name = self.graph.nodes[intermediate].get('name', intermediate)

                if self.graph.nodes[intermediate].get('node_type') == 'grantee':
                    return (
                        f"Leverage shared grantee connection through {intermediate_name}. "
                        f"Request introduction or reference from mutual contact."
                    )
                else:
                    return (
                        f"Build relationship with {intermediate_name} first, "
                        f"then seek warm introduction to target funder."
                    )

            else:
                # Multi-hop path (3+)
                return (
                    f"Complex pathway with {path_length} intermediaries. "
                    f"Focus on strengthening nearest connections first, "
                    f"then work systematically toward target funder."
                )

        except Exception as e:
            self.logger.error(f"Error generating cultivation strategy: {e}")
            return "Review relationship pathway and identify strongest connection points"

    def find_all_pathways(self, source: str, target: str, max_hops: int = 3) -> List[ConnectionPath]:
        """
        Find all pathways between source and target (alias for find_board_pathways).

        Args:
            source: Source organization EIN
            target: Target organization EIN
            max_hops: Maximum path length (default 3)

        Returns:
            List of ConnectionPath objects
        """
        return self.find_board_pathways(source, target)


class InfluenceAnalyzer:
    """
    Calculate influence metrics for network nodes.

    Simplified implementation focusing on:
    - Degree centrality (connection count)
    - PageRank (network influence)
    - Closeness centrality (network access)
    - Approximated betweenness (bridge position)
    """

    def __init__(self, graph: nx.Graph):
        self.graph = graph
        self.logger = logging.getLogger(__name__)

        # Pre-compute expensive metrics
        self._degree_centrality = None
        self._pagerank = None
        self._closeness_centrality = None

    def score_node_influence(self, node_id: str) -> Optional[InfluenceScore]:
        """
        Calculate comprehensive influence score for a node.

        Args:
            node_id: Organization EIN

        Returns:
            InfluenceScore object with all metrics
        """
        try:
            if node_id not in self.graph:
                self.logger.warning(f"Node {node_id} not in graph")
                return None

            node_data = self.graph.nodes[node_id]

            # Compute centrality metrics (lazy load)
            degree = self._get_degree_centrality()[node_id]
            pagerank = self._get_pagerank()[node_id]
            closeness = self._get_closeness_centrality()[node_id]

            # Approximate betweenness (use degree as proxy for performance)
            # True betweenness is O(n³) - too expensive for large graphs
            betweenness = degree * 0.5  # Rough approximation

            # Determine influence tier
            if degree > 0.7 or pagerank > 0.05:
                tier = "high"
                interpretation = "High influence - well-connected hub in the network"
            elif degree > 0.4 or pagerank > 0.02:
                tier = "medium"
                interpretation = "Medium influence - important connector in the network"
            else:
                tier = "low"
                interpretation = "Low influence - peripheral node with limited connections"

            # Get key connections (top neighbors by weight)
            key_connections = self._get_key_connections(node_id)

            return InfluenceScore(
                node_id=node_id,
                node_name=node_data.get('name', node_id),
                node_type=node_data.get('node_type', 'unknown'),
                degree_centrality=degree,
                pagerank_score=pagerank,
                closeness_centrality=closeness,
                betweenness_centrality=betweenness,
                influence_tier=tier,
                influence_interpretation=interpretation,
                key_connections=key_connections
            )

        except Exception as e:
            self.logger.error(f"Error scoring node influence for {node_id}: {e}")
            return None

    def score_top_influencers(self, limit: int = 20, node_type: str = None) -> List[InfluenceScore]:
        """
        Get top influencers in the network.

        Args:
            limit: Maximum results to return
            node_type: Filter by node type ('foundation' or 'grantee')

        Returns:
            List of InfluenceScore objects sorted by PageRank
        """
        try:
            pagerank_scores = self._get_pagerank()

            # Filter by node type if specified
            if node_type:
                filtered_nodes = [
                    n for n in self.graph.nodes()
                    if self.graph.nodes[n].get('node_type') == node_type
                ]
            else:
                filtered_nodes = list(self.graph.nodes())

            # Sort by PageRank
            sorted_nodes = sorted(
                filtered_nodes,
                key=lambda n: pagerank_scores.get(n, 0),
                reverse=True
            )[:limit]

            # Score each node
            influencers = []
            for node in sorted_nodes:
                score = self.score_node_influence(node)
                if score:
                    influencers.append(score)

            return influencers

        except Exception as e:
            self.logger.error(f"Error scoring top influencers: {e}")
            return []

    def _get_degree_centrality(self) -> Dict[str, float]:
        """Get or compute degree centrality (cached)"""
        if self._degree_centrality is None:
            self._degree_centrality = nx.degree_centrality(self.graph)
        return self._degree_centrality

    def _get_pagerank(self) -> Dict[str, float]:
        """Get or compute PageRank (cached)"""
        if self._pagerank is None:
            try:
                self._pagerank = nx.pagerank(self.graph, max_iter=100)
            except Exception as e:
                self.logger.warning(f"PageRank computation failed: {e}")
                # Fallback to degree centrality
                self._pagerank = self._get_degree_centrality()
        return self._pagerank

    def _get_closeness_centrality(self) -> Dict[str, float]:
        """Get or compute closeness centrality (cached)"""
        if self._closeness_centrality is None:
            try:
                # Only compute if graph is connected, otherwise use fallback
                if nx.is_connected(self.graph):
                    self._closeness_centrality = nx.closeness_centrality(self.graph)
                else:
                    # For disconnected graphs, compute per component
                    closeness = {}
                    for component in nx.connected_components(self.graph):
                        subgraph = self.graph.subgraph(component)
                        component_closeness = nx.closeness_centrality(subgraph)
                        closeness.update(component_closeness)
                    self._closeness_centrality = closeness
            except Exception as e:
                self.logger.warning(f"Closeness centrality computation failed: {e}")
                # Fallback
                self._closeness_centrality = {n: 0.0 for n in self.graph.nodes()}

        return self._closeness_centrality

    def _get_key_connections(self, node_id: str, limit: int = 5) -> List[str]:
        """Get top connected nodes by edge weight"""
        try:
            connections = []
            for neighbor in self.graph.neighbors(node_id):
                edge_data = self.graph[node_id][neighbor]
                weight = edge_data.get('weight', 0)
                connections.append((neighbor, weight))

            # Sort by weight and return top N
            connections.sort(key=lambda x: x[1], reverse=True)
            return [conn[0] for conn in connections[:limit]]

        except Exception as e:
            self.logger.error(f"Error getting key connections: {e}")
            return []

    def get_influence_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of influence across the network.

        Returns:
            Statistics about influence tiers and metrics
        """
        try:
            degree_centrality = self._get_degree_centrality()
            pagerank = self._get_pagerank()

            tiers = {'high': 0, 'medium': 0, 'low': 0}

            for node in self.graph.nodes():
                degree = degree_centrality.get(node, 0)
                pr = pagerank.get(node, 0)

                if degree > 0.7 or pr > 0.05:
                    tiers['high'] += 1
                elif degree > 0.4 or pr > 0.02:
                    tiers['medium'] += 1
                else:
                    tiers['low'] += 1

            return {
                'total_nodes': self.graph.number_of_nodes(),
                'high_influence_count': tiers['high'],
                'medium_influence_count': tiers['medium'],
                'low_influence_count': tiers['low'],
                'high_influence_percentage': (tiers['high'] / self.graph.number_of_nodes() * 100) if self.graph.number_of_nodes() > 0 else 0,
                'average_degree_centrality': sum(degree_centrality.values()) / len(degree_centrality) if degree_centrality else 0,
                'average_pagerank': sum(pagerank.values()) / len(pagerank) if pagerank else 0
            }

        except Exception as e:
            self.logger.error(f"Error computing influence distribution: {e}")
            return {'error': str(e)}


# Convenience functions
def analyze_network_influence(graph: nx.Graph, node_id: str = None) -> Dict[str, Any]:
    """
    Analyze influence for a specific node or entire network.

    Args:
        graph: NetworkX graph
        node_id: Optional specific node to analyze

    Returns:
        Influence analysis results
    """
    analyzer = InfluenceAnalyzer(graph)

    if node_id:
        score = analyzer.score_node_influence(node_id)
        return {
            'node_analysis': score.__dict__ if score else None
        }
    else:
        top_influencers = analyzer.score_top_influencers(limit=10)
        distribution = analyzer.get_influence_distribution()

        return {
            'top_influencers': [inf.__dict__ for inf in top_influencers],
            'influence_distribution': distribution
        }


def find_strategic_pathways(graph: nx.Graph, source: str, target: str) -> Dict[str, Any]:
    """
    Find strategic pathways between source and target.

    Args:
        graph: NetworkX graph
        source: Source organization EIN
        target: Target organization EIN

    Returns:
        Pathway analysis results
    """
    pathfinder = NetworkPathfinder(graph)
    paths = pathfinder.find_board_pathways(source, target)

    return {
        'source_ein': source,
        'target_ein': target,
        'paths_found': len(paths),
        'pathways': [
            {
                'path_nodes': p.path_nodes,
                'path_length': p.path_length,
                'path_strength': p.path_strength,
                'description': p.path_description,
                'cultivation_strategy': p.cultivation_strategy,
                'details': p.path_details
            }
            for p in paths
        ]
    }
