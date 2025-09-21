#!/usr/bin/env python3
"""
Network Analytics Module
Entity-independent network analysis functions for board member connections.
"""

import networkx as nx
import pandas as pd
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class BoardMember:
    """Represents a board member with normalized name and positions"""
    original_name: str
    normalized_name: str
    organization_ein: str
    organization_name: str
    position: str = "Board Member"
    
    @classmethod
    def create(cls, name: str, organization_ein: str, organization_name: str, position: str = "Board Member"):
        """Create a BoardMember with normalized name"""
        normalized = cls._normalize_name(name)
        return cls(
            original_name=name,
            normalized_name=normalized,
            organization_ein=organization_ein,
            organization_name=organization_name,
            position=position
        )
    
    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize name for better matching"""
        if not name:
            return ""
        
        # Remove common titles and suffixes
        name = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|Rev|Hon|Esq)\.?\b', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\b(Jr|Sr|II|III|IV)\.?\b', '', name, flags=re.IGNORECASE)
        
        # Clean up whitespace and punctuation
        name = re.sub(r'[^\w\s]', ' ', name)
        name = ' '.join(name.split())
        
        return name.strip().title()


@dataclass
class NetworkConnection:
    """Represents a connection between two organizations through a shared board member"""
    organization1_ein: str
    organization1_name: str
    organization2_ein: str
    organization2_name: str
    shared_member_name: str
    connection_strength: float = 1.0
    member_positions: List[str] = field(default_factory=list)


@dataclass
class NetworkMetrics:
    """Network analysis metrics for an organization"""
    ein: str
    organization_name: str
    connection_count: int = 0
    centrality_score: float = 0.0
    betweenness_centrality: float = 0.0
    clustering_coefficient: float = 0.0
    network_influence_score: float = 0.0
    shared_members: List[str] = field(default_factory=list)
    connections: List[NetworkConnection] = field(default_factory=list)
    computed_at: datetime = field(default_factory=datetime.now)


class NetworkAnalytics:
    """
    Entity-independent network analysis engine.
    Analyzes board member connections and organizational networks.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.board_members: List[BoardMember] = []
        self.network_graph: Optional[nx.Graph] = None
        
    def extract_board_members_from_data(self, filing_data: Dict[str, Any], 
                                       ein: str, 
                                       organization_name: str) -> List[BoardMember]:
        """
        Extract board members from organization filing data.
        
        Args:
            filing_data: Raw filing data (990, etc.)
            ein: Organization EIN
            organization_name: Organization name
            
        Returns:
            List of BoardMember objects
        """
        try:
            members = []
            
            # Try different data structures for board member info
            board_data = self._find_board_data(filing_data)
            
            if board_data:
                for member_info in board_data:
                    member = self._parse_member_info(member_info, ein, organization_name)
                    if member:
                        members.append(member)
            
            self.logger.debug(f"Extracted {len(members)} board members from {ein}")
            return members
            
        except Exception as e:
            self.logger.error(f"Error extracting board members from {ein}: {e}")
            return []
    
    def _find_board_data(self, filing_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Find board member data in various filing formats"""
        
        # Common paths for board member data (ProPublica 990 formats)
        board_paths = [
            'board_members',
            'officers', 
            'key_employees',
            'compensation',
            'form_990_part_vii_section_a',
            'part_vii_section_a',
            'part_vii_comp_officers',  # Added ProPublica specific paths
            'officer_compensation',
            'governance',
            'board_governance'
        ]
        
        for path in board_paths:
            if path in filing_data and filing_data[path]:
                return filing_data[path]
        
        # Try nested structures in filings_with_data
        if 'filings_with_data' in filing_data:
            for filing in filing_data['filings_with_data']:
                for path in board_paths:
                    if path in filing and filing[path]:
                        return filing[path]
        
        # Check for organization-level data structure
        if 'organization' in filing_data:
            org_data = filing_data['organization']
            for path in board_paths:
                if path in org_data and org_data[path]:
                    return org_data[path]
        
        # No board member data found in any expected locations
        return None
    
    def _parse_member_info(self, member_info: Dict[str, Any], 
                          ein: str, 
                          organization_name: str) -> Optional[BoardMember]:
        """Parse individual board member information"""
        try:
            # Try different name fields
            name_fields = ['name', 'person_name', 'business_name', 'officer_name']
            name = None
            
            for field in name_fields:
                if field in member_info and member_info[field]:
                    name = str(member_info[field]).strip()
                    break
            
            if not name:
                return None
            
            # Try to get position/title
            position_fields = ['title', 'position', 'officer_title', 'business_name']
            position = "Board Member"
            
            for field in position_fields:
                if field in member_info and member_info[field]:
                    position = str(member_info[field]).strip()
                    break
            
            return BoardMember.create(
                name=name,
                organization_ein=ein,
                organization_name=organization_name,
                position=position
            )
            
        except Exception as e:
            self.logger.debug(f"Error parsing member info: {e}")
            return None
    
    def build_network_graph(self, all_board_members: List[BoardMember]) -> nx.Graph:
        """
        Build a network graph from board member data.
        
        Args:
            all_board_members: List of all board members across organizations
            
        Returns:
            NetworkX graph with organizations as nodes and shared members as edges
        """
        try:
            graph = nx.Graph()
            
            # Group members by normalized name to find shared members
            members_by_name = defaultdict(list)
            for member in all_board_members:
                if member.normalized_name:
                    members_by_name[member.normalized_name].append(member)
            
            # Add organizations as nodes
            organizations = set()
            for member in all_board_members:
                organizations.add((member.organization_ein, member.organization_name))
            
            for ein, name in organizations:
                graph.add_node(ein, name=name)
            
            # Add edges for shared board members
            for member_name, member_list in members_by_name.items():
                if len(member_list) > 1:  # Shared member
                    # Create connections between all pairs of organizations
                    for i in range(len(member_list)):
                        for j in range(i + 1, len(member_list)):
                            member1 = member_list[i]
                            member2 = member_list[j]
                            
                            if member1.organization_ein != member2.organization_ein:
                                # Add or strengthen edge
                                if graph.has_edge(member1.organization_ein, member2.organization_ein):
                                    graph[member1.organization_ein][member2.organization_ein]['weight'] += 1
                                    graph[member1.organization_ein][member2.organization_ein]['shared_members'].append(member_name)
                                else:
                                    graph.add_edge(
                                        member1.organization_ein,
                                        member2.organization_ein,
                                        weight=1,
                                        shared_members=[member_name]
                                    )
            
            self.network_graph = graph
            self.logger.info(f"Built network graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
            return graph
            
        except Exception as e:
            self.logger.error(f"Error building network graph: {e}")
            return nx.Graph()
    
    def calculate_network_metrics(self, ein: str, graph: Optional[nx.Graph] = None) -> NetworkMetrics:
        """
        Calculate network metrics for a specific organization.
        
        Args:
            ein: Organization EIN
            graph: Optional network graph (uses stored graph if None)
            
        Returns:
            NetworkMetrics object with calculated metrics
        """
        try:
            if graph is None:
                graph = self.network_graph
            
            if not graph or ein not in graph:
                return NetworkMetrics(
                    ein=ein,
                    organization_name="Unknown"
                )
            
            organization_name = graph.nodes[ein].get('name', 'Unknown')
            metrics = NetworkMetrics(ein=ein, organization_name=organization_name)
            
            # Basic connection metrics
            metrics.connection_count = graph.degree(ein)
            
            # Centrality measures
            if graph.number_of_nodes() > 1:
                centrality = nx.degree_centrality(graph)
                metrics.centrality_score = centrality.get(ein, 0.0)
                
                if graph.number_of_edges() > 0:
                    betweenness = nx.betweenness_centrality(graph)
                    metrics.betweenness_centrality = betweenness.get(ein, 0.0)
                    
                    clustering = nx.clustering(graph)
                    metrics.clustering_coefficient = clustering.get(ein, 0.0)
            
            # Get shared members and connections
            connections = []
            shared_members = set()
            
            for neighbor in graph.neighbors(ein):
                edge_data = graph[ein][neighbor]
                shared_member_names = edge_data.get('shared_members', [])
                
                for member_name in shared_member_names:
                    shared_members.add(member_name)
                
                connection = NetworkConnection(
                    organization1_ein=ein,
                    organization1_name=organization_name,
                    organization2_ein=neighbor,
                    organization2_name=graph.nodes[neighbor].get('name', 'Unknown'),
                    shared_member_name=', '.join(shared_member_names),
                    connection_strength=edge_data.get('weight', 1.0)
                )
                connections.append(connection)
            
            metrics.shared_members = list(shared_members)
            metrics.connections = connections
            
            # Calculate overall network influence score
            metrics.network_influence_score = self._calculate_influence_score(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating network metrics for {ein}: {e}")
            return NetworkMetrics(ein=ein, organization_name="Unknown")
    
    def _calculate_influence_score(self, metrics: NetworkMetrics) -> float:
        """Calculate overall network influence score (0-1)"""
        try:
            # Weighted combination of network metrics
            weights = {
                'connections': 0.4,      # Number of connections
                'centrality': 0.3,       # Position in network
                'betweenness': 0.2,      # Bridging role
                'clustering': 0.1        # Local network density
            }
            
            score = 0.0
            
            # Normalize connection count (cap at 20 for scoring)
            if metrics.connection_count > 0:
                connection_score = min(metrics.connection_count / 20.0, 1.0)
                score += connection_score * weights['connections']
            
            # Add centrality scores
            score += metrics.centrality_score * weights['centrality']
            score += metrics.betweenness_centrality * weights['betweenness']
            score += metrics.clustering_coefficient * weights['clustering']
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            self.logger.debug(f"Error calculating influence score: {e}")
            return 0.0
    
    def find_network_paths(self, source_ein: str, target_ein: str, 
                          graph: Optional[nx.Graph] = None) -> List[List[str]]:
        """
        Find connection paths between two organizations.
        
        Args:
            source_ein: Source organization EIN
            target_ein: Target organization EIN
            graph: Optional network graph
            
        Returns:
            List of paths (each path is a list of EINs)
        """
        try:
            if graph is None:
                graph = self.network_graph
            
            if not graph or source_ein not in graph or target_ein not in graph:
                return []
            
            # Find shortest paths (up to length 3)
            try:
                paths = list(nx.all_shortest_paths(graph, source_ein, target_ein))
                # Limit to reasonable number of paths
                return paths[:10]
            except nx.NetworkXNoPath:
                return []
            
        except Exception as e:
            self.logger.error(f"Error finding network paths: {e}")
            return []
    
    def get_network_summary(self, graph: Optional[nx.Graph] = None) -> Dict[str, Any]:
        """
        Get summary statistics for the entire network.
        
        Args:
            graph: Optional network graph
            
        Returns:
            Dictionary with network summary statistics
        """
        try:
            if graph is None:
                graph = self.network_graph
            
            if not graph:
                return {"error": "No network graph available"}
            
            summary = {
                "total_organizations": graph.number_of_nodes(),
                "total_connections": graph.number_of_edges(),
                "average_connections": 0.0,
                "network_density": 0.0,
                "largest_component_size": 0,
                "total_shared_members": 0
            }
            
            if graph.number_of_nodes() > 0:
                summary["average_connections"] = sum(dict(graph.degree()).values()) / graph.number_of_nodes()
                summary["network_density"] = nx.density(graph)
                
                # Largest connected component
                if graph.number_of_nodes() > 1:
                    components = list(nx.connected_components(graph))
                    if components:
                        summary["largest_component_size"] = len(max(components, key=len))
                
                # Count total shared members
                shared_members = set()
                for _, _, edge_data in graph.edges(data=True):
                    shared_members.update(edge_data.get('shared_members', []))
                summary["total_shared_members"] = len(shared_members)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating network summary: {e}")
            return {"error": str(e)}


# Global analytics instance
_network_analytics: Optional[NetworkAnalytics] = None


def get_network_analytics() -> NetworkAnalytics:
    """Get or create global network analytics instance"""
    global _network_analytics
    if _network_analytics is None:
        _network_analytics = NetworkAnalytics()
    return _network_analytics