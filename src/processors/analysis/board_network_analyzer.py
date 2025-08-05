#!/usr/bin/env python3
"""
Board Member Network Analysis Processor
Analyzes board member connections and organizational relationships.

This processor:
1. Extracts board member data from organizations
2. Identifies shared board members across organizations
3. Maps network connections and relationships
4. Calculates network metrics and influence scores
5. Generates relationship insights for grant strategy
"""

import asyncio
import time
import networkx as nx
import pandas as pd
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import re

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile


class BoardMember:
    """Represents a board member with normalized name and positions."""
    
    def __init__(self, name: str, organization_ein: str, organization_name: str, position: str = "Board Member"):
        self.original_name = name
        self.normalized_name = self._normalize_name(name)
        self.organization_ein = organization_ein
        self.organization_name = organization_name
        self.position = position
        
    def _normalize_name(self, name: str) -> str:
        """Normalize name for better matching."""
        if not name:
            return ""
        
        # Remove common titles and suffixes
        name = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|Rev|Hon|Esq)\.?\b', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\b(Jr|Sr|II|III|IV)\.?\b', '', name, flags=re.IGNORECASE)
        
        # Clean up whitespace and punctuation
        name = re.sub(r'[^\w\s]', ' ', name)
        name = ' '.join(name.split())
        
        return name.strip().title()
    
    def __str__(self):
        return f"{self.normalized_name} ({self.organization_name})"
    
    def __hash__(self):
        return hash((self.normalized_name, self.organization_ein))
    
    def __eq__(self, other):
        if not isinstance(other, BoardMember):
            return False
        return self.normalized_name == other.normalized_name


class NetworkConnection:
    """Represents a connection between two organizations through shared board members."""
    
    def __init__(self, org1_ein: str, org1_name: str, org2_ein: str, org2_name: str):
        self.org1_ein = org1_ein
        self.org1_name = org1_name
        self.org2_ein = org2_ein  
        self.org2_name = org2_name
        self.shared_members: List[BoardMember] = []
        self.connection_strength = 0.0
        
    def add_shared_member(self, member: BoardMember):
        """Add a shared board member to this connection."""
        self.shared_members.append(member)
        self.connection_strength += 1.0
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            'org1_ein': self.org1_ein,
            'org1_name': self.org1_name,
            'org2_ein': self.org2_ein,
            'org2_name': self.org2_name,
            'shared_members': [member.normalized_name for member in self.shared_members],
            'connection_strength': self.connection_strength,
            'num_shared_members': len(self.shared_members)
        }


class BoardNetworkAnalyzerProcessor(BaseProcessor):
    """Processor for analyzing board member networks and organizational relationships."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="board_network_analyzer",
            description="Analyze board member networks and organizational relationships",
            version="1.0.0",
            dependencies=["financial_scorer"],  # Run after scoring to get full org data
            estimated_duration=60,  # 1 minute
            requires_network=False,
            requires_api_key=False
        )
        super().__init__(metadata)
        
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute board member network analysis."""
        start_time = time.time()
        
        try:
            # Get organizations from previous step
            organizations = await self._get_input_organizations(config, workflow_state)
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No organizations found for network analysis"]
                )
            
            self.logger.info(f"Analyzing board network for {len(organizations)} organizations")
            
            # Extract board members from all organizations
            board_members = self._extract_board_members(organizations)
            self.logger.info(f"Found {len(board_members)} total board member positions")
            
            # Build network connections
            network_graph = self._build_network_graph(board_members)
            connections = self._identify_connections(board_members)
            
            # Calculate network metrics
            network_metrics = self._calculate_network_metrics(network_graph, organizations)
            influence_scores = self._calculate_influence_scores(board_members, connections)
            
            # Generate insights
            insights = self._generate_network_insights(connections, network_metrics, organizations)
            
            execution_time = time.time() - start_time
            
            # Prepare results
            result_data = {
                "organizations": [org.dict() for org in organizations],
                "network_analysis": {
                    "total_board_members": len(board_members),
                    "unique_individuals": len(set(member.normalized_name for member in board_members)),
                    "network_connections": len(connections),
                    "network_graph_stats": {
                        "nodes": network_graph.number_of_nodes(),
                        "edges": network_graph.number_of_edges(),
                        "density": nx.density(network_graph) if network_graph.number_of_nodes() > 1 else 0.0
                    }
                },
                "connections": [conn.to_dict() for conn in connections],
                "network_metrics": network_metrics,
                "influence_scores": influence_scores,
                "insights": insights
            }
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "analysis_type": "board_network_analysis",
                    "algorithms_used": ["networkx", "centrality_analysis", "community_detection"]
                }
            )
            
        except Exception as e:
            self.logger.error(f"Board network analysis failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"Network analysis failed: {str(e)}"]
            )
    
    async def _get_input_organizations(self, config: ProcessorConfig, workflow_state=None) -> List[OrganizationProfile]:
        """Get organizations from the financial scorer step."""
        try:
            if workflow_state and workflow_state.has_processor_succeeded('financial_scorer'):
                org_dicts = workflow_state.get_organizations_from_processor('financial_scorer')
                if org_dicts:
                    organizations = []
                    for org_dict in org_dicts:
                        try:
                            if isinstance(org_dict, dict):
                                org = OrganizationProfile(**org_dict)
                            else:
                                org = org_dict
                            organizations.append(org)
                        except Exception as e:
                            self.logger.warning(f"Failed to parse organization data: {e}")
                            continue
                    return organizations
            
            # Fallback: create test data with board members
            self.logger.warning("No organizations from financial scorer - using test data")
            return self._create_test_organizations()
            
        except Exception as e:
            self.logger.error(f"Failed to get organizations: {e}")
            return []
    
    def _create_test_organizations(self) -> List[OrganizationProfile]:
        """Create test organizations with board member data for testing."""
        return [
            OrganizationProfile(
                ein="123456789",
                name="Health Foundation of Virginia",
                state="VA",
                ntee_code="T31",
                board_members=[
                    "Dr. John Smith", "Mary Johnson", "Robert Davis", 
                    "Sarah Wilson", "Michael Brown"
                ],
                key_personnel=[
                    {"name": "Dr. John Smith", "title": "Board Chair"},
                    {"name": "Mary Johnson", "title": "CEO"}
                ]
            ),
            OrganizationProfile(
                ein="987654321",
                name="Community Health Alliance",
                state="VA",
                ntee_code="E32",
                board_members=[
                    "Mary Johnson", "David Miller", "Robert Davis",
                    "Lisa Anderson", "James Taylor"
                ],
                key_personnel=[
                    {"name": "David Miller", "title": "Executive Director"},
                    {"name": "Mary Johnson", "title": "Board Member"}
                ]
            ),
            OrganizationProfile(
                ein="456789123",
                name="Virginia Food Bank Network",
                state="VA",
                ntee_code="F30",
                board_members=[
                    "Sarah Wilson", "Michael Brown", "Jennifer Lee",
                    "Thomas Anderson", "Patricia Martinez"
                ]
            )
        ]
    
    def _extract_board_members(self, organizations: List[OrganizationProfile]) -> List[BoardMember]:
        """Extract and normalize board member data from organizations."""
        board_members = []
        
        for org in organizations:
            # Add board members
            for name in org.board_members:
                if name and name.strip():
                    member = BoardMember(
                        name=name.strip(),
                        organization_ein=org.ein,
                        organization_name=org.name,
                        position="Board Member"
                    )
                    board_members.append(member)
            
            # Add key personnel who might also be board members
            for person in org.key_personnel:
                if isinstance(person, dict) and 'name' in person:
                    name = person['name']
                    title = person.get('title', 'Key Personnel')
                    
                    if name and name.strip():
                        member = BoardMember(
                            name=name.strip(),
                            organization_ein=org.ein,
                            organization_name=org.name,
                            position=title
                        )
                        board_members.append(member)
        
        return board_members
    
    def _build_network_graph(self, board_members: List[BoardMember]) -> nx.Graph:
        """Build a NetworkX graph of organizational connections."""
        G = nx.Graph()
        
        # Add organizations as nodes
        orgs = {}
        for member in board_members:
            org_id = member.organization_ein
            if org_id not in orgs:
                orgs[org_id] = member.organization_name
                G.add_node(org_id, name=member.organization_name)
        
        # Group board members by name to find shared members
        members_by_name = defaultdict(list)
        for member in board_members:
            members_by_name[member.normalized_name].append(member)
        
        # Add edges for organizations that share board members
        for name, members in members_by_name.items():
            if len(members) > 1:  # Shared across multiple organizations
                org_eins = [member.organization_ein for member in members]
                # Add edges between all pairs of organizations sharing this member
                for i in range(len(org_eins)):
                    for j in range(i + 1, len(org_eins)):
                        org1, org2 = org_eins[i], org_eins[j]
                        if G.has_edge(org1, org2):
                            G[org1][org2]['weight'] += 1
                            G[org1][org2]['shared_members'].append(name)
                        else:
                            G.add_edge(org1, org2, weight=1, shared_members=[name])
        
        return G
    
    def _identify_connections(self, board_members: List[BoardMember]) -> List[NetworkConnection]:
        """Identify and analyze connections between organizations."""
        connections = []
        
        # Group board members by normalized name
        members_by_name = defaultdict(list)
        for member in board_members:
            members_by_name[member.normalized_name].append(member)
        
        # Find connections through shared board members
        connection_dict = {}
        
        for name, members in members_by_name.items():
            if len(members) > 1:  # Person serves on multiple boards
                # Create connections between all pairs of organizations
                for i in range(len(members)):
                    for j in range(i + 1, len(members)):
                        member1, member2 = members[i], members[j]
                        
                        # Create connection key (ensure consistent ordering)
                        org1_ein, org2_ein = sorted([member1.organization_ein, member2.organization_ein])
                        conn_key = (org1_ein, org2_ein)
                        
                        if conn_key not in connection_dict:
                            connection_dict[conn_key] = NetworkConnection(
                                org1_ein=org1_ein,
                                org1_name=member1.organization_name if member1.organization_ein == org1_ein else member2.organization_name,
                                org2_ein=org2_ein,
                                org2_name=member2.organization_name if member2.organization_ein == org2_ein else member1.organization_name
                            )
                        
                        connection_dict[conn_key].add_shared_member(member1)
        
        return list(connection_dict.values())
    
    def _calculate_network_metrics(self, graph: nx.Graph, organizations: List[OrganizationProfile]) -> Dict[str, Any]:
        """Calculate network centrality and other metrics for organizations."""
        metrics = {}
        
        if graph.number_of_nodes() == 0:
            return {"message": "No network connections found"}
        
        try:
            # Calculate centrality measures
            betweenness = nx.betweenness_centrality(graph)
            closeness = nx.closeness_centrality(graph)
            degree_centrality = nx.degree_centrality(graph)
            eigenvector = nx.eigenvector_centrality(graph, max_iter=1000)
            
            # Organize by organization
            org_metrics = {}
            for org in organizations:
                ein = org.ein
                if ein in graph.nodes():
                    org_metrics[ein] = {
                        "organization_name": org.name,
                        "betweenness_centrality": betweenness.get(ein, 0.0),
                        "closeness_centrality": closeness.get(ein, 0.0),
                        "degree_centrality": degree_centrality.get(ein, 0.0),
                        "eigenvector_centrality": eigenvector.get(ein, 0.0),
                        "degree": graph.degree(ein),
                        "total_connections": len(list(graph.neighbors(ein)))
                    }
            
            metrics = {
                "organization_metrics": org_metrics,
                "network_stats": {
                    "total_nodes": graph.number_of_nodes(),
                    "total_edges": graph.number_of_edges(),
                    "network_density": nx.density(graph),
                    "average_clustering": nx.average_clustering(graph),
                    "connected_components": nx.number_connected_components(graph)
                }
            }
            
        except Exception as e:
            self.logger.warning(f"Error calculating network metrics: {e}")
            metrics = {"error": f"Failed to calculate metrics: {str(e)}"}
        
        return metrics
    
    def _calculate_influence_scores(self, board_members: List[BoardMember], connections: List[NetworkConnection]) -> Dict[str, Any]:
        """Calculate influence scores for individual board members."""
        # Count board positions per person
        member_counts = Counter(member.normalized_name for member in board_members)
        
        # Calculate influence based on number of positions and connection strength
        influence_scores = {}
        for name, count in member_counts.items():
            # Find all organizations this person is connected to
            person_orgs = [member.organization_name for member in board_members if member.normalized_name == name]
            
            # Calculate influence based on board positions and network connections
            base_influence = count  # Number of board positions
            network_boost = 0
            
            # Add bonus for connecting organizations
            for conn in connections:
                shared_names = [member.normalized_name for member in conn.shared_members]
                if name in shared_names:
                    network_boost += conn.connection_strength
            
            influence_scores[name] = {
                "board_positions": count,
                "organizations": person_orgs,
                "network_connections": network_boost,
                "total_influence_score": base_influence + (network_boost * 0.5)
            }
        
        # Sort by influence score
        sorted_scores = dict(sorted(influence_scores.items(), key=lambda x: x[1]['total_influence_score'], reverse=True))
        
        return {
            "individual_influence": sorted_scores,
            "top_influencers": dict(list(sorted_scores.items())[:10]),  # Top 10
            "summary": {
                "total_unique_individuals": len(influence_scores),
                "multi_board_members": len([name for name, data in influence_scores.items() if data['board_positions'] > 1]),
                "average_positions_per_person": sum(data['board_positions'] for data in influence_scores.values()) / len(influence_scores) if influence_scores else 0
            }
        }
    
    def _generate_network_insights(self, connections: List[NetworkConnection], network_metrics: Dict[str, Any], organizations: List[OrganizationProfile]) -> Dict[str, Any]:
        """Generate strategic insights from network analysis."""
        insights = {
            "key_findings": [],
            "strategic_recommendations": [],
            "network_clusters": [],
            "potential_opportunities": []
        }
        
        # Key findings
        if connections:
            insights["key_findings"].append(f"Found {len(connections)} organizational connections through shared board members")
            
            strongest_connection = max(connections, key=lambda x: x.connection_strength)
            insights["key_findings"].append(f"Strongest connection: {strongest_connection.org1_name} ↔ {strongest_connection.org2_name} ({int(strongest_connection.connection_strength)} shared members)")
        
        # Analyze organization types in network
        ntee_codes = [org.ntee_code for org in organizations if org.ntee_code]
        if ntee_codes:
            ntee_counter = Counter(ntee_codes)
            most_common_ntee = ntee_counter.most_common(1)[0] if ntee_counter else None
            if most_common_ntee:
                insights["key_findings"].append(f"Most common NTEE code: {most_common_ntee[0]} ({most_common_ntee[1]} organizations)")
        
        # Strategic recommendations
        if len(connections) > 2:
            insights["strategic_recommendations"].append("Consider collaborative grant applications with connected organizations")
            insights["strategic_recommendations"].append("Leverage board member networks for introductions and partnerships")
        
        if network_metrics.get("organization_metrics"):
            # Find most central organizations
            central_orgs = sorted(
                network_metrics["organization_metrics"].items(),
                key=lambda x: x[1].get("betweenness_centrality", 0),
                reverse=True
            )[:3]
            
            if central_orgs:
                insights["strategic_recommendations"].append(f"Focus on central organizations like {central_orgs[0][1]['organization_name']} for maximum network reach")
        
        # Potential opportunities
        if connections:
            insights["potential_opportunities"].append("Shared board members can facilitate knowledge transfer and collaboration")
            insights["potential_opportunities"].append("Connected organizations may have complementary expertise or resources")
        
        return insights
    
    def validate_inputs(self, config: ProcessorConfig) -> List[str]:
        """Validate inputs for board network analysis."""
        errors = []
        
        if not config.workflow_id:
            errors.append("Workflow ID is required")
        
        return errors


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return BoardNetworkAnalyzerProcessor()