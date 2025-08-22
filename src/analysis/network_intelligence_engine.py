"""
Network Intelligence Engine - Phase 2 Enhanced Network Analysis

Implements multi-degree connection analysis, POC-board integration, and strategic pathway identification.
This expands upon the existing board network analyzer with deep intelligence capabilities.

Features:
- 1st/2nd/3rd degree connection analysis with weighted scoring
- POC (Point of Contact) and board member integration framework
- Network strength scoring algorithms
- Connection pathway analysis and introduction strategies
- Strategic network intelligence for PLAN stage decision-making
"""

import asyncio
import logging
import networkx as nx
import pandas as pd
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile

logger = logging.getLogger(__name__)


class ConnectionDegree(Enum):
    """Connection degree levels with strategic importance."""
    FIRST = "first_degree"      # Direct board overlap, shared leadership
    SECOND = "second_degree"    # Board-to-board connections, organizational partnerships  
    THIRD = "third_degree"      # Extended network, industry connections


class ConnectionType(Enum):
    """Types of organizational connections."""
    DIRECT_BOARD_OVERLAP = "direct_board_overlap"
    SHARED_LEADERSHIP = "shared_leadership"
    BOARD_TO_BOARD = "board_to_board"
    ORGANIZATIONAL_PARTNERSHIP = "organizational_partnership"
    EXTENDED_NETWORK = "extended_network"
    INDUSTRY_CONNECTION = "industry_connection"
    POC_RELATIONSHIP = "poc_relationship"


@dataclass
class NetworkContact:
    """Enhanced contact representation combining POC and board member data."""
    name: str
    normalized_name: str
    organizations: List[Dict[str, str]] = field(default_factory=list)  # EIN, name, position
    contact_info: Dict[str, str] = field(default_factory=dict)  # email, phone, etc.
    linkedin_profile: Optional[str] = None
    board_positions: List[Dict[str, str]] = field(default_factory=list)
    poc_roles: List[Dict[str, str]] = field(default_factory=list)
    influence_score: float = 0.0
    connection_strength: float = 0.0
    
    def get_total_positions(self) -> int:
        """Get total number of positions across all organizations."""
        return len(self.board_positions) + len(self.poc_roles)
    
    def get_organization_eins(self) -> Set[str]:
        """Get all organization EINs this contact is associated with."""
        eins = set()
        for org in self.organizations:
            if org.get('ein'):
                eins.add(org['ein'])
        return eins


@dataclass 
class ConnectionPath:
    """Represents a pathway between organizations through shared contacts."""
    source_org: str  # Source organization EIN
    target_org: str  # Target organization EIN
    degree: ConnectionDegree
    connection_type: ConnectionType
    intermediary_contacts: List[NetworkContact] = field(default_factory=list)
    path_strength: float = 0.0
    access_probability: float = 0.0
    introduction_difficulty: str = "unknown"
    strategic_value: float = 0.0
    pathway_description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'source_org': self.source_org,
            'target_org': self.target_org, 
            'degree': self.degree.value,
            'connection_type': self.connection_type.value,
            'intermediary_contacts': [
                {
                    'name': contact.name,
                    'organizations': contact.organizations,
                    'influence_score': contact.influence_score
                } for contact in self.intermediary_contacts
            ],
            'path_strength': self.path_strength,
            'access_probability': self.access_probability,
            'introduction_difficulty': self.introduction_difficulty,
            'strategic_value': self.strategic_value,
            'pathway_description': self.pathway_description
        }


class NetworkIntelligenceEngine(BaseProcessor):
    """
    Enhanced Network Intelligence Engine for multi-degree connection analysis.
    
    Implements Phase 2 Week 7-8 requirements:
    - 1st/2nd/3rd degree connection analysis
    - POC-board member integration framework  
    - Network strength scoring algorithms
    - Connection pathway analysis
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="network_intelligence_engine",
            description="Multi-degree network analysis with POC integration and pathway identification",
            version="2.0.0",
            dependencies=["board_network_analyzer"],
            estimated_duration=120,  # 2 minutes for comprehensive analysis
            requires_network=False,
            requires_api_key=False,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Connection degree weights and characteristics
        self.connection_degrees = {
            ConnectionDegree.FIRST: {
                'weight': 0.5,
                'access_probability': 0.8,
                'introduction_difficulty': 'low',
                'base_strategic_value': 0.9
            },
            ConnectionDegree.SECOND: {
                'weight': 0.3,
                'access_probability': 0.6, 
                'introduction_difficulty': 'medium',
                'base_strategic_value': 0.6
            },
            ConnectionDegree.THIRD: {
                'weight': 0.2,
                'access_probability': 0.4,
                'introduction_difficulty': 'high',
                'base_strategic_value': 0.3
            }
        }
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute enhanced network intelligence analysis."""
        start_time = datetime.now()
        
        try:
            self.logger.info("Starting Network Intelligence Engine analysis")
            
            # Get organizations and existing network data
            organizations = await self._get_input_organizations(config, workflow_state)
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No organizations found for network analysis"]
                )
            
            # Phase 1: Extract and consolidate contact data (POC + Board members)
            all_contacts = await self._extract_and_integrate_contacts(organizations)
            self.logger.info(f"Integrated {len(all_contacts)} unique contacts from POC and board data")
            
            # Phase 2: Build multi-degree network graph
            network_graph = self._build_enhanced_network_graph(all_contacts, organizations)
            
            # Phase 3: Analyze connection pathways
            connection_pathways = await self._analyze_connection_pathways(
                organizations, all_contacts, network_graph
            )
            
            # Phase 4: Calculate network strength scores
            network_strength_scores = self._calculate_network_strength_scores(
                connection_pathways, all_contacts
            )
            
            # Phase 5: Generate strategic insights and recommendations
            strategic_insights = self._generate_strategic_network_insights(
                connection_pathways, network_strength_scores, organizations
            )
            
            # Prepare enhanced results
            result_data = {
                "network_intelligence": {
                    "total_contacts": len(all_contacts),
                    "organizations_analyzed": len(organizations),
                    "connection_pathways": len(connection_pathways),
                    "network_density": nx.density(network_graph) if network_graph.number_of_nodes() > 1 else 0.0,
                    "analysis_timestamp": start_time.isoformat()
                },
                "connection_pathways": [pathway.to_dict() for pathway in connection_pathways],
                "network_strength_scores": network_strength_scores,
                "strategic_insights": strategic_insights,
                "contact_profiles": [self._contact_to_dict(contact) for contact in all_contacts[:50]]  # Top 50 for size
            }
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                start_time=start_time,
                end_time=datetime.now(),
                data=result_data
            )
            
        except Exception as e:
            self.logger.error(f"Network Intelligence Engine failed: {str(e)}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                start_time=start_time,
                end_time=datetime.now(),
                errors=[f"Network analysis error: {str(e)}"]
            )
    
    async def _extract_and_integrate_contacts(self, organizations: List[OrganizationProfile]) -> List[NetworkContact]:
        """
        Phase 2 Requirement: POC-board member integration framework.
        
        Extracts and consolidates contacts from both POC and board member data,
        creating unified contact profiles with comprehensive organization associations.
        """
        contact_map = defaultdict(lambda: NetworkContact(name="", normalized_name=""))
        
        for org in organizations:
            org_info = {
                'ein': getattr(org, 'ein', ''),
                'name': getattr(org, 'name', ''),
                'org_type': 'target_organization'
            }
            
            # Extract board members
            board_members = getattr(org, 'board_members', [])
            for member in board_members:
                if isinstance(member, dict):
                    name = member.get('name', '')
                    position = member.get('position', 'Board Member')
                else:
                    name = str(member) if member else ''
                    position = 'Board Member'
                
                if name:
                    normalized_name = self._normalize_contact_name(name)
                    contact = contact_map[normalized_name]
                    contact.name = contact.name or name
                    contact.normalized_name = normalized_name
                    
                    # Add organization and board position
                    if org_info not in contact.organizations:
                        contact.organizations.append(org_info)
                    
                    board_position = {
                        'ein': org_info['ein'],
                        'organization': org_info['name'],
                        'position': position
                    }
                    if board_position not in contact.board_positions:
                        contact.board_positions.append(board_position)
            
            # Extract POC data (key personnel, contacts)
            key_personnel = getattr(org, 'key_personnel', [])
            for person in key_personnel:
                if isinstance(person, dict):
                    name = person.get('name', '')
                    role = person.get('role', 'Key Personnel')
                    contact_info = person.get('contact_info', {})
                else:
                    name = str(person) if person else ''
                    role = 'Key Personnel'
                    contact_info = {}
                
                if name:
                    normalized_name = self._normalize_contact_name(name)
                    contact = contact_map[normalized_name]
                    contact.name = contact.name or name
                    contact.normalized_name = normalized_name
                    
                    # Add organization
                    if org_info not in contact.organizations:
                        contact.organizations.append(org_info)
                    
                    # Add POC role
                    poc_role = {
                        'ein': org_info['ein'],
                        'organization': org_info['name'],
                        'role': role
                    }
                    if poc_role not in contact.poc_roles:
                        contact.poc_roles.append(poc_role)
                    
                    # Integrate contact information
                    if contact_info:
                        contact.contact_info.update(contact_info)
        
        # Calculate influence scores based on total positions and organization diversity
        contacts = list(contact_map.values())
        for contact in contacts:
            contact.influence_score = self._calculate_contact_influence_score(contact)
        
        # Sort by influence score
        contacts.sort(key=lambda x: x.influence_score, reverse=True)
        
        return contacts
    
    def _normalize_contact_name(self, name: str) -> str:
        """Normalize contact names for better matching across POC and board data."""
        if not name:
            return ""
        
        import re
        
        # Remove titles and suffixes
        name = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|Rev|Hon|Esq)\.?\b', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\b(Jr|Sr|II|III|IV|Ph\.?D|MD|PhD)\.?\b', '', name, flags=re.IGNORECASE)
        
        # Clean up punctuation and whitespace
        name = re.sub(r'[^\w\s]', ' ', name)
        name = ' '.join(name.split())
        
        return name.strip().title()
    
    def _calculate_contact_influence_score(self, contact: NetworkContact) -> float:
        """Calculate influence score based on positions and organizational diversity."""
        if not contact.organizations:
            return 0.0
        
        # Base score from number of positions
        total_positions = contact.get_total_positions()
        position_score = min(total_positions * 0.2, 1.0)  # Cap at 1.0
        
        # Diversity bonus for multiple organizations
        org_diversity = len(contact.get_organization_eins())
        diversity_bonus = min(org_diversity * 0.15, 0.5)  # Cap at 0.5
        
        # Board vs POC role weighting
        board_weight = len(contact.board_positions) * 0.6
        poc_weight = len(contact.poc_roles) * 0.4
        role_score = min((board_weight + poc_weight) / max(total_positions, 1), 1.0)
        
        return min(position_score + diversity_bonus + role_score, 2.0)  # Cap at 2.0
    
    def _build_enhanced_network_graph(self, contacts: List[NetworkContact], organizations: List[OrganizationProfile]) -> nx.Graph:
        """Build enhanced network graph including both organizations and contacts."""
        G = nx.Graph()
        
        # Add organization nodes
        for org in organizations:
            org_ein = getattr(org, 'ein', '')
            if org_ein:
                G.add_node(f"org_{org_ein}", 
                          type="organization",
                          name=getattr(org, 'name', ''),
                          ein=org_ein)
        
        # Add contact nodes and edges
        for contact in contacts:
            contact_id = f"contact_{contact.normalized_name.replace(' ', '_')}"
            G.add_node(contact_id,
                      type="contact", 
                      name=contact.name,
                      influence_score=contact.influence_score)
            
            # Create edges between contact and organizations
            for org_ein in contact.get_organization_eins():
                org_node = f"org_{org_ein}"
                if G.has_node(org_node):
                    # Edge weight based on number of positions with this org
                    org_positions = sum(1 for pos in contact.board_positions + contact.poc_roles 
                                      if pos.get('ein') == org_ein)
                    weight = min(org_positions * 0.25, 1.0)
                    G.add_edge(contact_id, org_node, weight=weight)
        
        return G
    
    async def _analyze_connection_pathways(self, organizations: List[OrganizationProfile], 
                                         contacts: List[NetworkContact], 
                                         network_graph: nx.Graph) -> List[ConnectionPath]:
        """
        Phase 2 Requirement: Connection pathway analysis.
        
        Analyzes pathways between organizations through shared contacts,
        identifying 1st/2nd/3rd degree connections with strategic assessment.
        """
        pathways = []
        org_eins = [getattr(org, 'ein', '') for org in organizations if getattr(org, 'ein', '')]
        
        # Analyze pathways between all organization pairs
        for i, source_ein in enumerate(org_eins):
            for target_ein in org_eins[i+1:]:
                if source_ein == target_ein:
                    continue
                
                # Find pathways of different degrees
                pathways.extend(self._find_connection_pathways(
                    source_ein, target_ein, contacts, network_graph
                ))
        
        # Sort by strategic value
        pathways.sort(key=lambda x: x.strategic_value, reverse=True)
        
        return pathways
    
    def _find_connection_pathways(self, source_ein: str, target_ein: str, 
                                contacts: List[NetworkContact], 
                                network_graph: nx.Graph) -> List[ConnectionPath]:
        """Find all connection pathways between two organizations."""
        pathways = []
        source_node = f"org_{source_ein}"
        target_node = f"org_{target_ein}"
        
        if not (network_graph.has_node(source_node) and network_graph.has_node(target_node)):
            return pathways
        
        # 1st Degree: Direct shared contacts
        shared_contacts = self._find_shared_contacts(source_ein, target_ein, contacts)
        for contact in shared_contacts:
            pathway = ConnectionPath(
                source_org=source_ein,
                target_org=target_ein,
                degree=ConnectionDegree.FIRST,
                connection_type=self._determine_connection_type(contact, source_ein, target_ein),
                intermediary_contacts=[contact]
            )
            self._calculate_pathway_metrics(pathway)
            pathways.append(pathway)
        
        # 2nd Degree: One intermediary contact
        try:
            shortest_paths = list(nx.all_shortest_paths(network_graph, source_node, target_node))
            for path in shortest_paths[:5]:  # Limit to top 5 paths
                if len(path) == 3:  # org -> contact -> org
                    contact_node = path[1]
                    if contact_node.startswith('contact_'):
                        contact = self._find_contact_by_node_id(contact_node, contacts)
                        if contact:
                            pathway = ConnectionPath(
                                source_org=source_ein,
                                target_org=target_ein,
                                degree=ConnectionDegree.SECOND,
                                connection_type=ConnectionType.BOARD_TO_BOARD,
                                intermediary_contacts=[contact]
                            )
                            self._calculate_pathway_metrics(pathway)
                            pathways.append(pathway)
        except nx.NetworkXNoPath:
            pass
        
        # 3rd Degree: Multiple intermediary contacts (simplified for performance)
        try:
            all_paths = list(nx.all_simple_paths(network_graph, source_node, target_node, cutoff=5))
            for path in all_paths[:3]:  # Limit to top 3 complex paths
                if len(path) > 3:
                    intermediary_contacts = []
                    for node in path[1:-1]:
                        if node.startswith('contact_'):
                            contact = self._find_contact_by_node_id(node, contacts)
                            if contact:
                                intermediary_contacts.append(contact)
                    
                    if intermediary_contacts:
                        pathway = ConnectionPath(
                            source_org=source_ein,
                            target_org=target_ein,
                            degree=ConnectionDegree.THIRD,
                            connection_type=ConnectionType.EXTENDED_NETWORK,
                            intermediary_contacts=intermediary_contacts
                        )
                        self._calculate_pathway_metrics(pathway)
                        pathways.append(pathway)
        except (nx.NetworkXNoPath, nx.NetworkXError):
            pass
        
        return pathways
    
    def _find_shared_contacts(self, source_ein: str, target_ein: str, 
                            contacts: List[NetworkContact]) -> List[NetworkContact]:
        """Find contacts who have positions at both organizations."""
        shared = []
        for contact in contacts:
            org_eins = contact.get_organization_eins()
            if source_ein in org_eins and target_ein in org_eins:
                shared.append(contact)
        return shared
    
    def _determine_connection_type(self, contact: NetworkContact, source_ein: str, target_ein: str) -> ConnectionType:
        """Determine the type of connection based on contact's roles."""
        source_roles = [pos for pos in contact.board_positions + contact.poc_roles 
                       if pos.get('ein') == source_ein]
        target_roles = [pos for pos in contact.board_positions + contact.poc_roles 
                       if pos.get('ein') == target_ein]
        
        # Check for board overlap
        source_board = any('board' in pos.get('position', '').lower() or 
                          'board' in pos.get('role', '').lower() 
                          for pos in source_roles)
        target_board = any('board' in pos.get('position', '').lower() or 
                          'board' in pos.get('role', '').lower() 
                          for pos in target_roles)
        
        if source_board and target_board:
            return ConnectionType.DIRECT_BOARD_OVERLAP
        elif source_board or target_board:
            return ConnectionType.SHARED_LEADERSHIP
        else:
            return ConnectionType.POC_RELATIONSHIP
    
    def _find_contact_by_node_id(self, node_id: str, contacts: List[NetworkContact]) -> Optional[NetworkContact]:
        """Find contact by network node ID."""
        if not node_id.startswith('contact_'):
            return None
        
        normalized_name = node_id.replace('contact_', '').replace('_', ' ')
        for contact in contacts:
            if contact.normalized_name.lower() == normalized_name.lower():
                return contact
        return None
    
    def _calculate_pathway_metrics(self, pathway: ConnectionPath):
        """
        Phase 2 Requirement: Network strength scoring algorithms.
        
        Calculate comprehensive metrics for connection pathways including
        strength, access probability, and strategic value.
        """
        degree_config = self.connection_degrees[pathway.degree]
        
        # Base metrics from degree configuration
        pathway.access_probability = degree_config['access_probability']
        pathway.introduction_difficulty = degree_config['introduction_difficulty']
        
        # Calculate path strength based on contact influence
        if pathway.intermediary_contacts:
            avg_influence = sum(contact.influence_score for contact in pathway.intermediary_contacts) / len(pathway.intermediary_contacts)
            pathway.path_strength = avg_influence * degree_config['weight']
        else:
            pathway.path_strength = 0.0
        
        # Calculate strategic value
        base_value = degree_config['base_strategic_value']
        contact_bonus = min(len(pathway.intermediary_contacts) * 0.1, 0.3)
        influence_bonus = pathway.path_strength * 0.2
        
        pathway.strategic_value = min(base_value + contact_bonus + influence_bonus, 1.0)
        
        # Generate pathway description
        pathway.pathway_description = self._generate_pathway_description(pathway)
    
    def _generate_pathway_description(self, pathway: ConnectionPath) -> str:
        """Generate human-readable pathway description."""
        if not pathway.intermediary_contacts:
            return f"No direct connection found between organizations"
        
        if pathway.degree == ConnectionDegree.FIRST:
            contact = pathway.intermediary_contacts[0]
            return f"Direct connection through {contact.name} who has positions at both organizations"
        elif pathway.degree == ConnectionDegree.SECOND:
            contact = pathway.intermediary_contacts[0]
            return f"Second-degree connection through {contact.name} (introduction required)"
        else:
            contact_names = [c.name for c in pathway.intermediary_contacts[:2]]
            return f"Extended network connection through {', '.join(contact_names)} and others"
    
    def _calculate_network_strength_scores(self, pathways: List[ConnectionPath], 
                                         contacts: List[NetworkContact]) -> Dict[str, Any]:
        """Calculate overall network strength metrics."""
        if not pathways:
            return {
                "overall_network_strength": 0.0,
                "connection_density": 0.0,
                "avg_pathway_strength": 0.0,
                "top_influencers": []
            }
        
        # Overall network strength (weighted average of pathway strengths)
        total_weighted_strength = sum(p.path_strength * p.strategic_value for p in pathways)
        total_weights = sum(p.strategic_value for p in pathways)
        overall_strength = total_weighted_strength / total_weights if total_weights > 0 else 0.0
        
        # Connection density (ratio of existing connections to possible connections)
        first_degree_count = sum(1 for p in pathways if p.degree == ConnectionDegree.FIRST)
        second_degree_count = sum(1 for p in pathways if p.degree == ConnectionDegree.SECOND)
        total_possible = len(pathways) if pathways else 1
        connection_density = (first_degree_count * 1.0 + second_degree_count * 0.5) / total_possible
        
        # Average pathway strength
        avg_pathway_strength = sum(p.path_strength for p in pathways) / len(pathways)
        
        # Top influencers
        top_influencers = sorted(contacts, key=lambda x: x.influence_score, reverse=True)[:10]
        
        return {
            "overall_network_strength": round(overall_strength, 3),
            "connection_density": round(connection_density, 3), 
            "avg_pathway_strength": round(avg_pathway_strength, 3),
            "pathway_distribution": {
                "first_degree": first_degree_count,
                "second_degree": second_degree_count,
                "third_degree": len(pathways) - first_degree_count - second_degree_count
            },
            "top_influencers": [
                {
                    "name": contact.name,
                    "influence_score": round(contact.influence_score, 3),
                    "total_positions": contact.get_total_positions(),
                    "organization_count": len(contact.get_organization_eins())
                }
                for contact in top_influencers
            ]
        }
    
    def _generate_strategic_network_insights(self, pathways: List[ConnectionPath], 
                                           network_scores: Dict[str, Any],
                                           organizations: List[OrganizationProfile]) -> Dict[str, Any]:
        """Generate strategic insights and recommendations for network utilization."""
        insights = {
            "summary": {},
            "key_opportunities": [],
            "introduction_strategies": [],
            "network_gaps": [],
            "recommendations": []
        }
        
        # Summary insights
        total_pathways = len(pathways)
        strong_pathways = [p for p in pathways if p.strategic_value > 0.7]
        
        insights["summary"] = {
            "total_connection_pathways": total_pathways,
            "high_value_pathways": len(strong_pathways),
            "network_strength_rating": self._get_strength_rating(network_scores["overall_network_strength"]),
            "primary_connection_degree": self._get_primary_degree(pathways)
        }
        
        # Key opportunities (top strategic pathways)
        insights["key_opportunities"] = [
            {
                "target_organization": pathway.target_org,
                "connection_strength": pathway.path_strength,
                "strategic_value": pathway.strategic_value,
                "pathway_description": pathway.pathway_description,
                "recommended_action": self._get_recommended_action(pathway)
            }
            for pathway in sorted(pathways, key=lambda x: x.strategic_value, reverse=True)[:5]
        ]
        
        # Introduction strategies
        insights["introduction_strategies"] = self._generate_introduction_strategies(pathways)
        
        # Network gaps and recommendations
        insights["network_gaps"] = self._identify_network_gaps(organizations, pathways)
        insights["recommendations"] = self._generate_network_recommendations(network_scores, pathways)
        
        return insights
    
    def _get_strength_rating(self, strength_score: float) -> str:
        """Convert numeric strength to descriptive rating."""
        if strength_score >= 0.8:
            return "Excellent"
        elif strength_score >= 0.6:
            return "Strong" 
        elif strength_score >= 0.4:
            return "Moderate"
        elif strength_score >= 0.2:
            return "Weak"
        else:
            return "Minimal"
    
    def _get_primary_degree(self, pathways: List[ConnectionPath]) -> str:
        """Determine the primary connection degree in the network."""
        if not pathways:
            return "None"
        
        degree_counts = defaultdict(int)
        for pathway in pathways:
            degree_counts[pathway.degree] += 1
        
        primary_degree = max(degree_counts.keys(), key=lambda x: degree_counts[x])
        return primary_degree.value
    
    def _get_recommended_action(self, pathway: ConnectionPath) -> str:
        """Generate recommended action based on pathway characteristics."""
        if pathway.degree == ConnectionDegree.FIRST and pathway.strategic_value > 0.7:
            return "Direct outreach recommended - strong existing connection"
        elif pathway.degree == ConnectionDegree.SECOND and pathway.access_probability > 0.6:
            return "Request introduction through intermediary contact"
        elif pathway.strategic_value > 0.5:
            return "Develop relationship with intermediary contacts first"
        else:
            return "Consider alternative approaches or strengthen network connections"
    
    def _generate_introduction_strategies(self, pathways: List[ConnectionPath]) -> List[Dict[str, Any]]:
        """Generate specific introduction strategies for high-value pathways."""
        strategies = []
        
        for pathway in sorted(pathways, key=lambda x: x.strategic_value, reverse=True)[:3]:
            if pathway.intermediary_contacts:
                strategy = {
                    "target_organization": pathway.target_org,
                    "intermediary_contact": pathway.intermediary_contacts[0].name,
                    "approach_difficulty": pathway.introduction_difficulty,
                    "success_probability": pathway.access_probability,
                    "strategy_details": self._create_introduction_strategy(pathway)
                }
                strategies.append(strategy)
        
        return strategies
    
    def _create_introduction_strategy(self, pathway: ConnectionPath) -> str:
        """Create detailed introduction strategy."""
        contact = pathway.intermediary_contacts[0]
        
        if pathway.degree == ConnectionDegree.FIRST:
            return f"Direct approach: {contact.name} has active roles at both organizations and can facilitate direct introduction"
        elif pathway.degree == ConnectionDegree.SECOND:
            return f"Warm introduction: Build relationship with {contact.name} first, then request introduction to target organization"
        else:
            return f"Multi-step approach: Establish connection through {contact.name}, then navigate extended network"
    
    def _identify_network_gaps(self, organizations: List[OrganizationProfile], 
                             pathways: List[ConnectionPath]) -> List[Dict[str, Any]]:
        """Identify organizations with weak or no network connections."""
        gaps = []
        
        # Find organizations with no strong pathways
        org_connections = defaultdict(list)
        for pathway in pathways:
            org_connections[pathway.target_org].append(pathway)
        
        for org in organizations:
            org_ein = getattr(org, 'ein', '')
            if org_ein:
                strong_connections = [p for p in org_connections[org_ein] if p.strategic_value > 0.5]
                if len(strong_connections) < 2:  # Fewer than 2 strong connections
                    gaps.append({
                        "organization": getattr(org, 'name', ''),
                        "ein": org_ein,
                        "connection_strength": len(strong_connections),
                        "gap_severity": "High" if len(strong_connections) == 0 else "Moderate"
                    })
        
        return gaps
    
    def _generate_network_recommendations(self, network_scores: Dict[str, Any], 
                                        pathways: List[ConnectionPath]) -> List[str]:
        """Generate strategic recommendations for network enhancement."""
        recommendations = []
        
        overall_strength = network_scores["overall_network_strength"]
        
        if overall_strength < 0.3:
            recommendations.append("Network development critical: Focus on building foundational relationships")
            recommendations.append("Prioritize board member networking and industry event attendance")
        elif overall_strength < 0.6:
            recommendations.append("Strengthen existing connections: Regular engagement with key contacts")
            recommendations.append("Identify and cultivate second-degree connections")
        else:
            recommendations.append("Leverage strong network: Activate high-value pathways for strategic initiatives")
            recommendations.append("Maintain network health through regular relationship management")
        
        # Pathway-specific recommendations
        first_degree_count = sum(1 for p in pathways if p.degree == ConnectionDegree.FIRST)
        if first_degree_count < 3:
            recommendations.append("Develop more direct connections through board appointments or partnerships")
        
        return recommendations
    
    def _contact_to_dict(self, contact: NetworkContact) -> Dict[str, Any]:
        """Convert NetworkContact to dictionary for serialization."""
        return {
            "name": contact.name,
            "normalized_name": contact.normalized_name,
            "organizations": contact.organizations,
            "contact_info": contact.contact_info,
            "linkedin_profile": contact.linkedin_profile,
            "board_positions": contact.board_positions,
            "poc_roles": contact.poc_roles,
            "influence_score": round(contact.influence_score, 3),
            "total_positions": contact.get_total_positions(),
            "organization_count": len(contact.get_organization_eins())
        }
    
    async def _get_input_organizations(self, config: ProcessorConfig, workflow_state) -> List[OrganizationProfile]:
        """Get organizations from previous workflow steps or config."""
        # Try to get from workflow state first
        if workflow_state and hasattr(workflow_state, 'organizations'):
            return workflow_state.organizations
        
        # Try to get from config input data
        if config.input_data and 'organizations' in config.input_data:
            org_data = config.input_data['organizations']
            organizations = []
            for org_dict in org_data:
                if isinstance(org_dict, dict):
                    organizations.append(OrganizationProfile(**org_dict))
                elif hasattr(org_dict, 'dict'):
                    organizations.append(OrganizationProfile(**org_dict.dict()))
            return organizations
        
        return []


# Register the processor
def register_processor():
    """Register this processor with the workflow engine."""
    from src.core.workflow_engine import get_workflow_engine
    
    engine = get_workflow_engine()
    engine.register_processor(NetworkIntelligenceEngine)
    
    return NetworkIntelligenceEngine


# Factory function for processor registration
def get_processor():
    """Factory function for processor registration."""
    return NetworkIntelligenceEngine()