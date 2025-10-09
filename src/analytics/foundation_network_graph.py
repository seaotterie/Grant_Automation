"""
Foundation Network Graph Module
Build and query bipartite network graphs connecting foundations and grantees.

Purpose: Network graph construction from Phase 1 bundling results
Integration: Phases 1-2 → Phase 3 network graph analytics
"""

import networkx as nx
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class NetworkNode:
    """Generic network node (foundation or grantee)"""
    node_id: str  # EIN
    node_type: str  # "foundation" or "grantee"
    name: str
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NetworkEdge:
    """Grant relationship edge"""
    from_node: str  # Foundation EIN
    to_node: str  # Grantee EIN
    edge_type: str = "grant"
    weight: float = 0  # Grant amount
    years: List[int] = field(default_factory=list)
    total_amount: float = 0
    grant_count: int = 0


@dataclass
class NetworkGraphOutput:
    """Complete network graph output"""
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    graph_statistics: Dict[str, Any]
    graph_object: Optional[nx.Graph] = None  # NetworkX graph
    graphml_export: Optional[str] = None  # GraphML string


class FoundationNetworkGraph:
    """
    Build and query foundation-grantee bipartite network graphs.

    Integration Points:
    - Phase 1: GranteeBundlingOutput provides bundled grantees
    - Phase 2: Co-funding similarity already computed
    - BMF Tool: Organization enrichment data
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.graph = nx.Graph()
        self.node_metadata: Dict[str, Dict[str, Any]] = {}

    def build_from_bundling_results(self, bundling_output) -> nx.Graph:
        """
        Construct bipartite graph from Phase 1 bundling data.

        Args:
            bundling_output: GranteeBundlingOutput from Phase 1

        Returns:
            NetworkX Graph with foundations and grantees as nodes
        """
        try:
            self.logger.info("Building foundation-grantee network graph...")

            # Extract foundation EINs from bundling output
            foundation_eins = set(bundling_output.foundation_eins)

            # Add foundation nodes
            for foundation_ein in foundation_eins:
                self._add_foundation_node(foundation_ein)

            # Add grantee nodes and grant edges
            for bundled_grantee in bundling_output.bundled_grantees:
                self._add_grantee_node(bundled_grantee)

                # Add edges from each funding source
                for funding_source in bundled_grantee.funding_sources:
                    self._add_grant_edge(
                        foundation_ein=funding_source.foundation_ein,
                        grantee_ein=bundled_grantee.grantee_ein,
                        amount=funding_source.grant_amount,
                        year=funding_source.grant_year
                    )

            self.logger.info(
                f"Graph built: {self.graph.number_of_nodes()} nodes, "
                f"{self.graph.number_of_edges()} edges"
            )

            return self.graph

        except Exception as e:
            self.logger.error(f"Error building network graph: {e}", exc_info=True)
            return nx.Graph()

    def _add_foundation_node(self, foundation_ein: str, foundation_name: str = None):
        """Add foundation node with BMF enrichment"""
        try:
            # Check if already exists
            if foundation_ein in self.graph:
                return

            # Look up in BMF for attributes (placeholder - integrate with BMF tool)
            bmf_data = self._lookup_bmf(foundation_ein)

            self.graph.add_node(
                foundation_ein,
                node_type='foundation',
                name=bmf_data.get('name', foundation_name or foundation_ein),
                state=bmf_data.get('state'),
                ntee=bmf_data.get('ntee'),
                assets=bmf_data.get('assets', 0),
                revenue=bmf_data.get('revenue', 0),
                subsection=bmf_data.get('subsection')
            )

            self.logger.debug(f"Added foundation node: {foundation_ein}")

        except Exception as e:
            self.logger.error(f"Error adding foundation node {foundation_ein}: {e}")

    def _add_grantee_node(self, bundled_grantee):
        """Add grantee node with financial metrics"""
        try:
            grantee_ein = bundled_grantee.grantee_ein

            # Check if already exists
            if grantee_ein in self.graph:
                return

            # Look up in BMF
            bmf_data = self._lookup_bmf(grantee_ein)

            self.graph.add_node(
                grantee_ein,
                node_type='grantee',
                name=bundled_grantee.grantee_name,
                funder_count=bundled_grantee.funder_count,
                total_funding=bundled_grantee.total_funding,
                average_grant_size=bundled_grantee.average_grant_size,
                funding_stability=bundled_grantee.funding_stability,
                first_grant_year=bundled_grantee.first_grant_year,
                last_grant_year=bundled_grantee.last_grant_year,
                state=bmf_data.get('state'),
                ntee=bmf_data.get('ntee'),
                assets=bmf_data.get('assets', 0)
            )

            self.logger.debug(f"Added grantee node: {grantee_ein} ({bundled_grantee.grantee_name})")

        except Exception as e:
            self.logger.error(f"Error adding grantee node: {e}")

    def _add_grant_edge(self, foundation_ein: str, grantee_ein: str, amount: float, year: int):
        """Add or update grant edge"""
        try:
            if self.graph.has_edge(foundation_ein, grantee_ein):
                # Update existing edge
                edge_data = self.graph[foundation_ein][grantee_ein]
                edge_data['weight'] += amount
                edge_data['total_amount'] += amount
                edge_data['grant_count'] += 1
                if year not in edge_data['years']:
                    edge_data['years'].append(year)
            else:
                # Create new edge
                self.graph.add_edge(
                    foundation_ein,
                    grantee_ein,
                    edge_type='grant',
                    weight=amount,
                    total_amount=amount,
                    grant_count=1,
                    years=[year]
                )

        except Exception as e:
            self.logger.error(f"Error adding grant edge: {e}")

    def _lookup_bmf(self, ein: str) -> Dict[str, Any]:
        """
        Look up organization in BMF database.

        TODO: Integrate with tools/bmf-filter-tool
        For now, returns empty dict (graceful degradation)
        """
        try:
            # Placeholder - will integrate with BMF tool
            # from tools.bmf_filter_tool import BMFFilterTool
            # bmf_tool = BMFFilterTool()
            # result = bmf_tool.lookup_by_ein(ein)
            return {}

        except Exception as e:
            self.logger.debug(f"BMF lookup failed for {ein}: {e}")
            return {}

    def export_to_graphml(self, output_path: str = None) -> str:
        """
        Export graph to GraphML format for Gephi/Cytoscape.

        Args:
            output_path: Optional file path to write GraphML

        Returns:
            GraphML string
        """
        try:
            import io

            # Create in-memory file
            output = io.StringIO()
            nx.write_graphml(self.graph, output)
            graphml_string = output.getvalue()
            output.close()

            # Write to file if path provided
            if output_path:
                nx.write_graphml(self.graph, output_path)
                self.logger.info(f"GraphML exported to {output_path}")

            return graphml_string

        except Exception as e:
            self.logger.error(f"Error exporting GraphML: {e}")
            return ""

    def export_to_json(self) -> Dict[str, Any]:
        """
        Export graph to JSON for web visualization (D3.js, vis.js).

        Returns:
            Dictionary with nodes and edges arrays
        """
        try:
            json_graph = {
                'nodes': [],
                'edges': [],
                'metadata': {
                    'node_count': self.graph.number_of_nodes(),
                    'edge_count': self.graph.number_of_edges(),
                    'generated_at': datetime.now().isoformat()
                }
            }

            # Add nodes
            for node, data in self.graph.nodes(data=True):
                node_dict = {
                    'id': node,
                    'type': data.get('node_type', 'unknown'),
                    'name': data.get('name', node)
                }
                # Add all other attributes
                for key, value in data.items():
                    if key not in ['node_type', 'name']:
                        node_dict[key] = value

                json_graph['nodes'].append(node_dict)

            # Add edges
            for u, v, data in self.graph.edges(data=True):
                edge_dict = {
                    'source': u,
                    'target': v,
                    'weight': data.get('weight', 1.0),
                    'years': data.get('years', []),
                    'total_amount': data.get('total_amount', 0),
                    'grant_count': data.get('grant_count', 0)
                }
                json_graph['edges'].append(edge_dict)

            return json_graph

        except Exception as e:
            self.logger.error(f"Error exporting JSON: {e}")
            return {'nodes': [], 'edges': [], 'error': str(e)}

    def get_network_statistics(self) -> Dict[str, Any]:
        """Compute comprehensive graph statistics"""
        try:
            foundation_nodes = [
                n for n, d in self.graph.nodes(data=True)
                if d.get('node_type') == 'foundation'
            ]
            grantee_nodes = [
                n for n, d in self.graph.nodes(data=True)
                if d.get('node_type') == 'grantee'
            ]

            stats = {
                'total_nodes': self.graph.number_of_nodes(),
                'total_edges': self.graph.number_of_edges(),
                'total_foundations': len(foundation_nodes),
                'total_grantees': len(grantee_nodes),
                'network_density': 0.0,
                'average_degree': 0.0,
                'average_grants_per_foundation': 0.0,
                'average_funders_per_grantee': 0.0,
                'most_connected_foundation': None,
                'most_connected_grantee': None,
                'total_grant_amount': 0.0,
                'average_grant_size': 0.0,
                'is_connected': False,
                'component_count': 0
            }

            if self.graph.number_of_nodes() > 0:
                # Density
                stats['network_density'] = nx.density(self.graph)

                # Average degree
                degrees = dict(self.graph.degree())
                stats['average_degree'] = sum(degrees.values()) / len(degrees)

                # Foundation metrics
                if foundation_nodes:
                    foundation_degrees = {n: degrees[n] for n in foundation_nodes}
                    stats['average_grants_per_foundation'] = sum(foundation_degrees.values()) / len(foundation_degrees)
                    stats['most_connected_foundation'] = max(foundation_degrees, key=foundation_degrees.get)

                # Grantee metrics
                if grantee_nodes:
                    grantee_degrees = {n: degrees[n] for n in grantee_nodes}
                    stats['average_funders_per_grantee'] = sum(grantee_degrees.values()) / len(grantee_degrees)
                    stats['most_connected_grantee'] = max(grantee_degrees, key=grantee_degrees.get)

                # Financial metrics
                total_amount = sum(d.get('total_amount', 0) for _, _, d in self.graph.edges(data=True))
                total_grants = sum(d.get('grant_count', 0) for _, _, d in self.graph.edges(data=True))
                stats['total_grant_amount'] = total_amount
                stats['average_grant_size'] = total_amount / total_grants if total_grants > 0 else 0

                # Connectivity
                stats['is_connected'] = nx.is_connected(self.graph)
                components = list(nx.connected_components(self.graph))
                stats['component_count'] = len(components)
                if components:
                    stats['largest_component_size'] = len(max(components, key=len))

            return stats

        except Exception as e:
            self.logger.error(f"Error computing network statistics: {e}")
            return {'error': str(e)}


class NetworkQueryEngine:
    """
    Query foundation network graph for strategic intelligence.
    """

    def __init__(self, graph: nx.Graph):
        self.graph = graph
        self.logger = logging.getLogger(__name__)

    def find_co_funders(self, grantee_ein: str) -> List[Dict[str, Any]]:
        """
        Find all foundations funding a specific grantee.

        Args:
            grantee_ein: Grantee organization EIN

        Returns:
            List of foundation dictionaries with grant details
        """
        try:
            if grantee_ein not in self.graph:
                return []

            co_funders = []
            for neighbor in self.graph.neighbors(grantee_ein):
                node_data = self.graph.nodes[neighbor]
                if node_data.get('node_type') == 'foundation':
                    edge_data = self.graph[neighbor][grantee_ein]

                    co_funders.append({
                        'foundation_ein': neighbor,
                        'foundation_name': node_data.get('name', neighbor),
                        'total_funding': edge_data.get('total_amount', 0),
                        'grant_count': edge_data.get('grant_count', 0),
                        'years': edge_data.get('years', []),
                        'average_grant': edge_data.get('total_amount', 0) / edge_data.get('grant_count', 1)
                    })

            # Sort by total funding descending
            co_funders.sort(key=lambda x: x['total_funding'], reverse=True)

            return co_funders

        except Exception as e:
            self.logger.error(f"Error finding co-funders for {grantee_ein}: {e}")
            return []

    def find_shared_grantees(self, foundation_ein_1: str, foundation_ein_2: str) -> List[Dict[str, Any]]:
        """
        Find grantees funded by both foundations.

        Args:
            foundation_ein_1: First foundation EIN
            foundation_ein_2: Second foundation EIN

        Returns:
            List of shared grantee dictionaries
        """
        try:
            if foundation_ein_1 not in self.graph or foundation_ein_2 not in self.graph:
                return []

            # Get neighbors (grantees) for each foundation
            grantees_1 = set(n for n in self.graph.neighbors(foundation_ein_1)
                           if self.graph.nodes[n].get('node_type') == 'grantee')
            grantees_2 = set(n for n in self.graph.neighbors(foundation_ein_2)
                           if self.graph.nodes[n].get('node_type') == 'grantee')

            # Find intersection
            shared_grantees = grantees_1 & grantees_2

            result = []
            for grantee_ein in shared_grantees:
                node_data = self.graph.nodes[grantee_ein]
                edge_data_1 = self.graph[foundation_ein_1][grantee_ein]
                edge_data_2 = self.graph[foundation_ein_2][grantee_ein]

                result.append({
                    'grantee_ein': grantee_ein,
                    'grantee_name': node_data.get('name', grantee_ein),
                    'foundation_1_funding': edge_data_1.get('total_amount', 0),
                    'foundation_2_funding': edge_data_2.get('total_amount', 0),
                    'total_co_funding': edge_data_1.get('total_amount', 0) + edge_data_2.get('total_amount', 0),
                    'foundation_1_years': edge_data_1.get('years', []),
                    'foundation_2_years': edge_data_2.get('years', [])
                })

            # Sort by total co-funding
            result.sort(key=lambda x: x['total_co_funding'], reverse=True)

            return result

        except Exception as e:
            self.logger.error(f"Error finding shared grantees: {e}")
            return []

    def get_funding_path(self, source_ein: str, target_ein: str, max_hops: int = 3) -> List[List[str]]:
        """
        Find funding pathways between two organizations.

        Args:
            source_ein: Source organization EIN
            target_ein: Target organization EIN
            max_hops: Maximum path length (default 3)

        Returns:
            List of paths (each path is a list of EINs)
        """
        try:
            if source_ein not in self.graph or target_ein not in self.graph:
                return []

            # Find all simple paths up to max_hops
            try:
                paths = list(nx.all_simple_paths(
                    self.graph, source_ein, target_ein, cutoff=max_hops
                ))
                # Limit to top 10 paths
                return paths[:10]
            except nx.NetworkXNoPath:
                return []

        except Exception as e:
            self.logger.error(f"Error finding funding path: {e}")
            return []

    def get_grantee_portfolio(self, foundation_ein: str) -> Dict[str, Any]:
        """
        Get complete grantee portfolio for a foundation.

        Args:
            foundation_ein: Foundation EIN

        Returns:
            Dictionary with portfolio analysis
        """
        try:
            if foundation_ein not in self.graph:
                return {'error': 'Foundation not found'}

            grantees = []
            total_funding = 0
            total_grants = 0

            for neighbor in self.graph.neighbors(foundation_ein):
                node_data = self.graph.nodes[neighbor]
                if node_data.get('node_type') == 'grantee':
                    edge_data = self.graph[foundation_ein][neighbor]

                    grant_info = {
                        'grantee_ein': neighbor,
                        'grantee_name': node_data.get('name', neighbor),
                        'total_funding': edge_data.get('total_amount', 0),
                        'grant_count': edge_data.get('grant_count', 0),
                        'years': edge_data.get('years', []),
                        'state': node_data.get('state'),
                        'ntee': node_data.get('ntee')
                    }

                    grantees.append(grant_info)
                    total_funding += edge_data.get('total_amount', 0)
                    total_grants += edge_data.get('grant_count', 0)

            # Sort by funding
            grantees.sort(key=lambda x: x['total_funding'], reverse=True)

            return {
                'foundation_ein': foundation_ein,
                'foundation_name': self.graph.nodes[foundation_ein].get('name', foundation_ein),
                'total_grantees': len(grantees),
                'total_funding': total_funding,
                'total_grants': total_grants,
                'average_grant_size': total_funding / total_grants if total_grants > 0 else 0,
                'grantees': grantees
            }

        except Exception as e:
            self.logger.error(f"Error getting grantee portfolio: {e}")
            return {'error': str(e)}


# Global instance
_foundation_network_graph: Optional[FoundationNetworkGraph] = None


def get_foundation_network_graph() -> FoundationNetworkGraph:
    """Get or create global foundation network graph instance"""
    global _foundation_network_graph
    if _foundation_network_graph is None:
        _foundation_network_graph = FoundationNetworkGraph()
    return _foundation_network_graph
