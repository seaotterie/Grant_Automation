#!/usr/bin/env python3
"""
Competitive Intelligence Processor
Advanced market analysis processor that identifies peer organizations and analyzes competitive landscape.

This processor:
1. Takes risk-assessed organizations from previous steps
2. Identifies peer organizations and competitive clusters
3. Performs market positioning and competitive analysis
4. Generates strategic intelligence for grant decision-making
"""

import asyncio
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from statistics import mean, median, stdev
from collections import defaultdict
import re

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile


class CompetitiveIntelligenceProcessor(BaseProcessor):
    """Advanced competitive intelligence and market analysis processor."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="competitive_intelligence",
            description="Peer organization identification and competitive market analysis",
            version="1.0.0",
            dependencies=["risk_assessor"],
            estimated_duration=120,  # 2 minutes
            requires_network=False,
            requires_api_key=False
        )
        super().__init__(metadata)
        
        # Competitive analysis parameters
        self.similarity_weights = {
            "ntee_similarity": 0.25,      # NTEE code similarity
            "size_similarity": 0.20,      # Revenue/asset similarity
            "geographic_proximity": 0.15,  # Geographic closeness
            "program_alignment": 0.15,     # Program expense patterns
            "operational_similarity": 0.15, # Operational characteristics
            "mission_alignment": 0.10      # Mission/activity alignment
        }
        
        # Market analysis thresholds
        self.market_thresholds = {
            "peer_similarity_min": 0.60,    # Minimum similarity for peer classification
            "market_leader_revenue": 2000000, # Revenue threshold for market leadership
            "niche_player_max": 500000,     # Maximum revenue for niche classification
            "crowded_market_min": 5,        # Minimum orgs for crowded market
            "competitive_radius_miles": 50   # Geographic competition radius
        }
        
        # NTEE code groups for competitive analysis
        self.ntee_groups = {
            "health_general": ["E20", "E21", "E22", "E30", "E31", "E32"],
            "health_support": ["E60", "E61", "E62", "E86", "E87"],
            "nutrition_food": ["F30", "F31", "F32", "F40", "F41"],
            "human_services": ["P20", "P21", "P22", "P30", "P31", "P32"],
            "education": ["B20", "B21", "B22", "B30", "B40", "B41"],
            "community_development": ["S20", "S21", "S22", "S30", "S31"]
        }
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute competitive intelligence analysis."""
        start_time = time.time()
        
        try:
            # Get risk-assessed organizations
            organizations = await self._get_risk_assessed_organizations(config, workflow_state)
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No risk-assessed organizations found for competitive analysis"]
                )
            
            self.logger.info(f"Performing competitive analysis for {len(organizations)} organizations")
            
            # Identify peer clusters and competitive relationships
            peer_analysis = await self._identify_peer_organizations(organizations)
            
            # Analyze market positioning
            market_analysis = self._analyze_market_positioning(organizations, peer_analysis)
            
            # Generate competitive insights
            competitive_insights = self._generate_competitive_insights(organizations, peer_analysis, market_analysis)
            
            # Create funding opportunity analysis
            funding_opportunities = self._analyze_funding_opportunities(organizations, market_analysis)
            
            execution_time = time.time() - start_time
            
            # Prepare results
            result_data = {
                "organizations": [org.dict() for org in organizations],
                "peer_analysis": peer_analysis,
                "market_analysis": market_analysis,
                "competitive_insights": competitive_insights,
                "funding_opportunities": funding_opportunities,
                "analysis_stats": {
                    "total_organizations": len(organizations),
                    "peer_clusters_identified": len(peer_analysis.get("clusters", [])),
                    "market_segments": len(market_analysis.get("segments", [])),
                    "competitive_gaps": len(funding_opportunities.get("market_gaps", []))
                }
            }
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "analysis_type": "competitive_intelligence",
                    "similarity_weights": self.similarity_weights,
                    "market_thresholds": self.market_thresholds
                }
            )
            
        except Exception as e:
            self.logger.error(f"Competitive intelligence analysis failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"Competitive intelligence analysis failed: {str(e)}"]
            )
    
    async def _get_risk_assessed_organizations(self, config: ProcessorConfig, workflow_state=None) -> List[OrganizationProfile]:
        """Get organizations from risk assessor step."""
        try:
            if workflow_state and workflow_state.has_processor_succeeded('risk_assessor'):
                org_dicts = workflow_state.get_organizations_from_processor('risk_assessor')
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
            
            # Fallback to earlier processors
            for processor in ['trend_analyzer', 'financial_scorer']:
                if workflow_state and workflow_state.has_processor_succeeded(processor):
                    org_dicts = workflow_state.get_organizations_from_processor(processor)
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
            
            self.logger.warning("No suitable organizations found for competitive analysis")
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get organizations for competitive analysis: {e}")
            return []
    
    async def _identify_peer_organizations(self, organizations: List[OrganizationProfile]) -> Dict[str, Any]:
        """Identify peer organizations and competitive clusters."""
        try:
            # Calculate similarity matrix between all organizations
            similarity_matrix = self._calculate_similarity_matrix(organizations)
            
            # Identify peer relationships
            peer_relationships = self._identify_peer_relationships(organizations, similarity_matrix)
            
            # Create competitive clusters
            clusters = self._create_competitive_clusters(organizations, peer_relationships)
            
            # Analyze cluster characteristics
            cluster_analysis = self._analyze_clusters(organizations, clusters)
            
            return {
                "similarity_matrix": similarity_matrix,
                "peer_relationships": peer_relationships,
                "clusters": clusters,
                "cluster_analysis": cluster_analysis,
                "peer_count_distribution": self._calculate_peer_distribution(peer_relationships)
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to identify peer organizations: {e}")
            return {}
    
    def _calculate_similarity_matrix(self, organizations: List[OrganizationProfile]) -> Dict[str, Dict[str, float]]:
        """Calculate similarity scores between all pairs of organizations."""
        similarity_matrix = {}
        
        for i, org1 in enumerate(organizations):
            similarity_matrix[org1.ein] = {}
            
            for j, org2 in enumerate(organizations):
                if i == j:
                    similarity_matrix[org1.ein][org2.ein] = 1.0
                else:
                    similarity = self._calculate_organization_similarity(org1, org2)
                    similarity_matrix[org1.ein][org2.ein] = similarity
        
        return similarity_matrix
    
    def _calculate_organization_similarity(self, org1: OrganizationProfile, org2: OrganizationProfile) -> float:
        """Calculate similarity score between two organizations."""
        similarity_components = []
        
        # NTEE code similarity
        ntee_sim = self._calculate_ntee_similarity(org1.ntee_code, org2.ntee_code)
        similarity_components.append(("ntee_similarity", ntee_sim))
        
        # Size similarity (revenue and assets)
        size_sim = self._calculate_size_similarity(org1, org2)
        similarity_components.append(("size_similarity", size_sim))
        
        # Geographic proximity
        geo_sim = self._calculate_geographic_similarity(org1.state, org2.state)
        similarity_components.append(("geographic_proximity", geo_sim))
        
        # Program alignment (expense ratios)
        program_sim = self._calculate_program_similarity(org1, org2)
        similarity_components.append(("program_alignment", program_sim))
        
        # Operational similarity
        operational_sim = self._calculate_operational_similarity(org1, org2)
        similarity_components.append(("operational_similarity", operational_sim))
        
        # Mission alignment (basic text similarity if available)
        mission_sim = self._calculate_mission_similarity(org1, org2)
        similarity_components.append(("mission_alignment", mission_sim))
        
        # Calculate weighted similarity
        weighted_similarity = sum(
            self.similarity_weights[component] * score 
            for component, score in similarity_components
        )
        
        return weighted_similarity
    
    def _calculate_ntee_similarity(self, ntee1: Optional[str], ntee2: Optional[str]) -> float:
        """Calculate NTEE code similarity."""
        if not ntee1 or not ntee2:
            return 0.0
        
        if ntee1 == ntee2:
            return 1.0
        
        # Check if they're in the same group
        group1 = self._get_ntee_group(ntee1)
        group2 = self._get_ntee_group(ntee2)
        
        if group1 and group2 and group1 == group2:
            return 0.8
        
        # Check if same category (first letter)
        if ntee1[0] == ntee2[0]:
            return 0.6
        
        # Check for related categories
        related_categories = {
            'E': ['F', 'P'],  # Health related to Food/Nutrition and Human Services
            'F': ['E', 'P'],  # Food related to Health and Human Services  
            'P': ['E', 'F'],  # Human Services related to Health and Food
            'B': ['C'],       # Education related to Environment
            'C': ['B']        # Environment related to Education
        }
        
        if ntee1[0] in related_categories.get(ntee2[0], []):
            return 0.4
        
        return 0.0
    
    def _get_ntee_group(self, ntee_code: str) -> Optional[str]:
        """Get NTEE group for a given code."""
        for group, codes in self.ntee_groups.items():
            if ntee_code in codes:
                return group
        return None
    
    def _calculate_size_similarity(self, org1: OrganizationProfile, org2: OrganizationProfile) -> float:
        """Calculate size similarity based on revenue and assets."""
        similarities = []
        
        # Revenue similarity
        if org1.revenue and org2.revenue:
            rev_ratio = min(org1.revenue, org2.revenue) / max(org1.revenue, org2.revenue)
            similarities.append(rev_ratio)
        
        # Asset similarity
        if org1.assets and org2.assets:
            asset_ratio = min(org1.assets, org2.assets) / max(org1.assets, org2.assets)
            similarities.append(asset_ratio)
        
        return mean(similarities) if similarities else 0.5
    
    def _calculate_geographic_similarity(self, state1: str, state2: str) -> float:
        """Calculate geographic similarity."""
        if state1 == state2:
            return 1.0
        
        # Regional groupings
        regions = {
            'northeast': ['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA'],
            'southeast': ['DE', 'MD', 'DC', 'VA', 'WV', 'KY', 'TN', 'NC', 'SC', 'GA', 'FL', 'AL', 'MS', 'AR', 'LA'],
            'midwest': ['OH', 'MI', 'IN', 'WI', 'IL', 'MN', 'IA', 'MO', 'ND', 'SD', 'NE', 'KS'],
            'southwest': ['TX', 'OK', 'NM', 'AZ'],
            'west': ['MT', 'WY', 'CO', 'UT', 'ID', 'WA', 'OR', 'NV', 'CA', 'AK', 'HI']
        }
        
        # Find regions for both states
        region1 = None
        region2 = None
        
        for region, states in regions.items():
            if state1 in states:
                region1 = region
            if state2 in states:
                region2 = region
        
        if region1 and region2 and region1 == region2:
            return 0.6
        
        return 0.2  # Different regions
    
    def _calculate_program_similarity(self, org1: OrganizationProfile, org2: OrganizationProfile) -> float:
        """Calculate program focus similarity."""
        if not org1.program_expense_ratio or not org2.program_expense_ratio:
            return 0.5
        
        # Similar program expense ratios indicate similar operational focus
        ratio_diff = abs(org1.program_expense_ratio - org2.program_expense_ratio)
        similarity = max(0, 1 - (ratio_diff * 2))  # Scale difference
        
        return similarity
    
    def _calculate_operational_similarity(self, org1: OrganizationProfile, org2: OrganizationProfile) -> float:
        """Calculate operational characteristics similarity."""
        similarities = []
        
        # Filing recency similarity
        if org1.most_recent_filing_year and org2.most_recent_filing_year:
            year_diff = abs(org1.most_recent_filing_year - org2.most_recent_filing_year)
            filing_sim = max(0, 1 - (year_diff * 0.2))
            similarities.append(filing_sim)
        
        # Organization type similarity (subsection code)
        if org1.subsection_code == org2.subsection_code:
            similarities.append(1.0)
        else:
            similarities.append(0.3)
        
        # Risk profile similarity (if available)
        if (hasattr(org1, 'risk_classification') and hasattr(org2, 'risk_classification') and
            org1.risk_classification and org2.risk_classification):
            if org1.risk_classification == org2.risk_classification:
                similarities.append(0.8)
            else:
                similarities.append(0.4)
        
        return mean(similarities) if similarities else 0.5
    
    def _calculate_mission_similarity(self, org1: OrganizationProfile, org2: OrganizationProfile) -> float:
        """Calculate mission/activity similarity."""
        # Basic implementation - could be enhanced with NLP
        if (hasattr(org1, 'mission_description') and hasattr(org2, 'mission_description') and
            org1.mission_description and org2.mission_description):
            
            # Simple keyword matching
            words1 = set(re.findall(r'\w+', org1.mission_description.lower()))
            words2 = set(re.findall(r'\w+', org2.mission_description.lower()))
            
            if words1 and words2:
                intersection = len(words1 & words2)
                union = len(words1 | words2)
                return intersection / union if union > 0 else 0
        
        # Fallback to name similarity
        if org1.name and org2.name:
            name_words1 = set(re.findall(r'\w+', org1.name.lower()))
            name_words2 = set(re.findall(r'\w+', org2.name.lower()))
            
            if name_words1 and name_words2:
                intersection = len(name_words1 & name_words2)
                union = len(name_words1 | name_words2)
                return intersection / union if union > 0 else 0
        
        return 0.3  # Default similarity
    
    def _identify_peer_relationships(self, organizations: List[OrganizationProfile], 
                                   similarity_matrix: Dict[str, Dict[str, float]]) -> Dict[str, List[Dict[str, Any]]]:
        """Identify peer relationships based on similarity scores."""
        peer_relationships = {}
        
        for org in organizations:
            peers = []
            org_similarities = similarity_matrix.get(org.ein, {})
            
            for other_ein, similarity in org_similarities.items():
                if other_ein != org.ein and similarity >= self.market_thresholds["peer_similarity_min"]:
                    # Find the other organization
                    other_org = next((o for o in organizations if o.ein == other_ein), None)
                    if other_org:
                        peers.append({
                            "ein": other_ein,
                            "name": other_org.name,
                            "similarity_score": similarity,
                            "relationship_type": self._classify_peer_relationship(similarity),
                            "competitive_position": self._determine_competitive_position(org, other_org)
                        })
            
            # Sort peers by similarity score
            peers.sort(key=lambda x: x["similarity_score"], reverse=True)
            peer_relationships[org.ein] = peers
        
        return peer_relationships
    
    def _classify_peer_relationship(self, similarity: float) -> str:
        """Classify the type of peer relationship."""
        if similarity >= 0.85:
            return "direct_competitor"
        elif similarity >= 0.75:
            return "close_peer"
        elif similarity >= 0.65:
            return "market_peer"
        else:
            return "distant_peer"
    
    def _determine_competitive_position(self, org1: OrganizationProfile, org2: OrganizationProfile) -> str:
        """Determine competitive position between two organizations."""
        if not org1.revenue or not org2.revenue:
            return "comparable"
        
        ratio = org1.revenue / org2.revenue
        
        if ratio >= 2.0:
            return "larger"
        elif ratio <= 0.5:
            return "smaller"
        else:
            return "comparable"
    
    def _create_competitive_clusters(self, organizations: List[OrganizationProfile], 
                                   peer_relationships: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Create competitive clusters based on peer relationships."""
        clusters = []
        processed_orgs = set()
        
        for org in organizations:
            if org.ein in processed_orgs:
                continue
            
            # Create cluster starting with this organization
            cluster_members = {org.ein}
            cluster_queue = [org.ein]
            
            # Add strongly connected peers
            while cluster_queue:
                current_ein = cluster_queue.pop(0)
                current_peers = peer_relationships.get(current_ein, [])
                
                for peer in current_peers:
                    if (peer["similarity_score"] >= 0.75 and 
                        peer["ein"] not in cluster_members):
                        cluster_members.add(peer["ein"])
                        cluster_queue.append(peer["ein"])
            
            # Create cluster information
            cluster_orgs = [o for o in organizations if o.ein in cluster_members]
            if len(cluster_orgs) >= 2:  # Only clusters with 2+ members
                cluster_info = self._analyze_cluster_characteristics(cluster_orgs)
                cluster_info["member_eins"] = list(cluster_members)
                cluster_info["cluster_id"] = f"cluster_{len(clusters) + 1}"
                clusters.append(cluster_info)
                
                processed_orgs.update(cluster_members)
        
        return clusters
    
    def _analyze_cluster_characteristics(self, cluster_orgs: List[OrganizationProfile]) -> Dict[str, Any]:
        """Analyze characteristics of a competitive cluster."""
        revenues = [org.revenue for org in cluster_orgs if org.revenue]
        assets = [org.assets for org in cluster_orgs if org.assets]
        
        # Geographic distribution
        states = [org.state for org in cluster_orgs]
        state_counts = defaultdict(int)
        for state in states:
            state_counts[state] += 1
        
        # NTEE distribution
        ntee_codes = [org.ntee_code for org in cluster_orgs if org.ntee_code]
        ntee_groups = [self._get_ntee_group(code) for code in ntee_codes if code]
        ntee_group_counts = defaultdict(int)
        for group in ntee_groups:
            if group:
                ntee_group_counts[group] += 1
        
        return {
            "size": len(cluster_orgs),
            "organizations": [{"ein": org.ein, "name": org.name} for org in cluster_orgs],
            "financial_profile": {
                "revenue_range": [min(revenues), max(revenues)] if revenues else [0, 0],
                "median_revenue": median(revenues) if revenues else 0,
                "total_revenue": sum(revenues) if revenues else 0,
                "median_assets": median(assets) if assets else 0
            },
            "geographic_spread": dict(state_counts),
            "sector_focus": dict(ntee_group_counts),
            "cluster_type": self._classify_cluster_type(cluster_orgs),
            "competitive_intensity": self._assess_competitive_intensity(cluster_orgs)
        }
    
    def _classify_cluster_type(self, cluster_orgs: List[OrganizationProfile]) -> str:
        """Classify the type of competitive cluster."""
        revenues = [org.revenue for org in cluster_orgs if org.revenue]
        
        if not revenues:
            return "unknown"
        
        avg_revenue = mean(revenues)
        revenue_std = stdev(revenues) if len(revenues) > 1 else 0
        
        # Size-based classification
        if avg_revenue > self.market_thresholds["market_leader_revenue"]:
            return "large_players"
        elif avg_revenue < self.market_thresholds["niche_player_max"]:
            return "niche_players"
        else:
            return "mid_market"
    
    def _assess_competitive_intensity(self, cluster_orgs: List[OrganizationProfile]) -> str:
        """Assess competitive intensity within a cluster."""
        if len(cluster_orgs) < 3:
            return "low"
        elif len(cluster_orgs) >= self.market_thresholds["crowded_market_min"]:
            return "high"
        else:
            return "moderate"
    
    def _analyze_clusters(self, organizations: List[OrganizationProfile], 
                         clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall cluster patterns and market structure."""
        total_orgs = len(organizations)
        clustered_orgs = sum(cluster["size"] for cluster in clusters)
        unclustered_orgs = total_orgs - clustered_orgs
        
        return {
            "total_clusters": len(clusters),
            "clustered_organizations": clustered_orgs,
            "unclustered_organizations": unclustered_orgs,
            "clustering_rate": clustered_orgs / total_orgs if total_orgs > 0 else 0,
            "average_cluster_size": mean([c["size"] for c in clusters]) if clusters else 0,
            "largest_cluster_size": max([c["size"] for c in clusters]) if clusters else 0,
            "market_fragmentation": "high" if len(clusters) / total_orgs > 0.3 else 
                                   "moderate" if len(clusters) / total_orgs > 0.15 else "low"
        }
    
    def _calculate_peer_distribution(self, peer_relationships: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        """Calculate distribution of peer counts."""
        peer_counts = [len(peers) for peers in peer_relationships.values()]
        
        distribution = {
            "no_peers": sum(1 for count in peer_counts if count == 0),
            "few_peers_1_3": sum(1 for count in peer_counts if 1 <= count <= 3),
            "moderate_peers_4_7": sum(1 for count in peer_counts if 4 <= count <= 7),
            "many_peers_8_plus": sum(1 for count in peer_counts if count >= 8)
        }
        
        return distribution
    
    def _analyze_market_positioning(self, organizations: List[OrganizationProfile], 
                                  peer_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market positioning and competitive landscape."""
        # Market segmentation analysis
        segments = self._identify_market_segments(organizations)
        
        # Competitive positioning
        positioning = self._analyze_competitive_positioning(organizations, peer_analysis)
        
        # Market concentration analysis
        concentration = self._analyze_market_concentration(organizations)
        
        # Geographic market analysis
        geographic_analysis = self._analyze_geographic_markets(organizations)
        
        return {
            "segments": segments,
            "competitive_positioning": positioning,
            "market_concentration": concentration,
            "geographic_markets": geographic_analysis,
            "market_leaders": self._identify_market_leaders(organizations),
            "market_opportunities": self._identify_market_opportunities(organizations, segments)
        }
    
    def _identify_market_segments(self, organizations: List[OrganizationProfile]) -> Dict[str, Any]:
        """Identify distinct market segments."""
        segments = defaultdict(list)
        
        for org in organizations:
            # Primary segmentation by NTEE group
            ntee_group = self._get_ntee_group(org.ntee_code) or "other"
            
            # Secondary segmentation by size
            if org.revenue:
                if org.revenue < 250000:
                    size_segment = "small"
                elif org.revenue < 1000000:
                    size_segment = "medium"
                else:
                    size_segment = "large"
            else:
                size_segment = "unknown"
            
            segment_key = f"{ntee_group}_{size_segment}"
            segments[segment_key].append(org)
        
        # Analyze segment characteristics
        segment_analysis = {}
        for segment_key, orgs in segments.items():
            if len(orgs) >= 2:  # Only analyze segments with multiple organizations
                revenues = [org.revenue for org in orgs if org.revenue]
                segment_analysis[segment_key] = {
                    "organization_count": len(orgs),
                    "total_revenue": sum(revenues) if revenues else 0,
                    "average_revenue": mean(revenues) if revenues else 0,
                    "organizations": [{"ein": org.ein, "name": org.name} for org in orgs],
                    "geographic_spread": len(set(org.state for org in orgs)),
                    "competitive_intensity": "high" if len(orgs) >= 5 else "moderate" if len(orgs) >= 3 else "low"
                }
        
        return segment_analysis
    
    def _analyze_competitive_positioning(self, organizations: List[OrganizationProfile], 
                                       peer_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competitive positioning of organizations."""
        positioning_analysis = {}
        
        for org in organizations:
            peers = peer_analysis.get("peer_relationships", {}).get(org.ein, [])
            
            # Determine market position
            market_position = self._determine_market_position(org, organizations)
            
            # Competitive advantages
            advantages = self._identify_competitive_advantages(org, peers)
            
            # Competitive threats
            threats = self._identify_competitive_threats(org, peers)
            
            positioning_analysis[org.ein] = {
                "organization_name": org.name,
                "market_position": market_position,
                "peer_count": len(peers),
                "competitive_advantages": advantages,
                "competitive_threats": threats,
                "market_share_proxy": self._calculate_market_share_proxy(org, organizations),
                "differentiation_factors": self._identify_differentiation_factors(org)
            }
        
        return positioning_analysis
    
    def _determine_market_position(self, org: OrganizationProfile, 
                                 all_organizations: List[OrganizationProfile]) -> str:
        """Determine organization's market position."""
        if not org.revenue:
            return "unknown"
        
        revenues = [o.revenue for o in all_organizations if o.revenue]
        if not revenues:
            return "unknown"
        
        percentile = sum(1 for r in revenues if r < org.revenue) / len(revenues)
        
        if percentile >= 0.90:
            return "market_leader"
        elif percentile >= 0.75:
            return "major_player"
        elif percentile >= 0.50:
            return "established_player"
        elif percentile >= 0.25:
            return "emerging_player"
        else:
            return "niche_player"
    
    def _identify_competitive_advantages(self, org: OrganizationProfile, 
                                       peers: List[Dict[str, Any]]) -> List[str]:
        """Identify competitive advantages."""
        advantages = []
        
        # Financial advantages
        if org.revenue:
            peer_revenues = [p.get("revenue", 0) for p in peers if "revenue" in p]
            if peer_revenues and org.revenue > mean(peer_revenues) * 1.2:
                advantages.append("superior_financial_resources")
        
        # Program efficiency advantage
        if org.program_expense_ratio and org.program_expense_ratio > 0.8:
            advantages.append("high_program_efficiency")
        
        # Financial stability advantage
        if hasattr(org, 'risk_classification') and org.risk_classification == "low":
            advantages.append("low_risk_profile")
        
        # Recent filing advantage
        if org.most_recent_filing_year and org.most_recent_filing_year >= 2023:
            advantages.append("current_compliance")
        
        return advantages
    
    def _identify_competitive_threats(self, org: OrganizationProfile, 
                                    peers: List[Dict[str, Any]]) -> List[str]:
        """Identify competitive threats."""
        threats = []
        
        # Size-based threats
        larger_competitors = [p for p in peers if p.get("competitive_position") == "larger"]
        if len(larger_competitors) >= 2:
            threats.append("multiple_larger_competitors")
        
        # Market crowding
        if len(peers) >= 5:
            threats.append("crowded_market")
        
        # Geographic overlap
        same_state_peers = len([p for p in peers if p.get("state") == org.state])
        if same_state_peers >= 3:
            threats.append("high_local_competition")
        
        return threats
    
    def _calculate_market_share_proxy(self, org: OrganizationProfile, 
                                    all_organizations: List[OrganizationProfile]) -> Optional[float]:
        """Calculate proxy for market share based on revenue."""
        if not org.revenue:
            return None
        
        # Find organizations in same sector
        same_sector_orgs = [
            o for o in all_organizations 
            if o.ntee_code and org.ntee_code and 
            self._get_ntee_group(o.ntee_code) == self._get_ntee_group(org.ntee_code)
        ]
        
        if len(same_sector_orgs) < 2:
            return None
        
        sector_revenues = [o.revenue for o in same_sector_orgs if o.revenue]
        if not sector_revenues:
            return None
        
        total_sector_revenue = sum(sector_revenues)
        return org.revenue / total_sector_revenue if total_sector_revenue > 0 else None
    
    def _identify_differentiation_factors(self, org: OrganizationProfile) -> List[str]:
        """Identify factors that differentiate the organization."""
        factors = []
        
        # Geographic differentiation
        if org.state not in ['CA', 'NY', 'TX', 'FL']:  # Not in major states
            factors.append("geographic_niche")
        
        # Size differentiation
        if org.revenue:
            if org.revenue < 100000:
                factors.append("grassroots_scale")
            elif org.revenue > 2000000:
                factors.append("large_scale_operations")
        
        # Focus differentiation
        if org.program_expense_ratio and org.program_expense_ratio > 0.85:
            factors.append("mission_focused")
        
        return factors
    
    def _analyze_market_concentration(self, organizations: List[OrganizationProfile]) -> Dict[str, Any]:
        """Analyze market concentration using revenue data."""
        revenues = [org.revenue for org in organizations if org.revenue]
        
        if len(revenues) < 4:
            return {"status": "insufficient_data"}
        
        # Sort revenues in descending order
        revenues.sort(reverse=True)
        total_revenue = sum(revenues)
        
        # Calculate concentration ratios
        cr4 = sum(revenues[:4]) / total_revenue if total_revenue > 0 else 0  # Top 4 concentration
        cr8 = sum(revenues[:8]) / total_revenue if len(revenues) >= 8 and total_revenue > 0 else cr4
        
        # Herfindahl-Hirschman Index (simplified)
        hhi = sum((revenue / total_revenue) ** 2 for revenue in revenues) if total_revenue > 0 else 0
        
        # Market structure classification
        if cr4 >= 0.6:
            market_structure = "concentrated"
        elif cr4 >= 0.4:
            market_structure = "moderately_concentrated"
        else:
            market_structure = "fragmented"
        
        return {
            "concentration_ratio_4": cr4,
            "concentration_ratio_8": cr8,
            "herfindahl_index": hhi,
            "market_structure": market_structure,
            "revenue_distribution": {
                "top_25_percent": sum(revenues[:len(revenues)//4]) / total_revenue if total_revenue > 0 else 0,
                "bottom_50_percent": sum(revenues[len(revenues)//2:]) / total_revenue if total_revenue > 0 else 0
            }
        }
    
    def _analyze_geographic_markets(self, organizations: List[OrganizationProfile]) -> Dict[str, Any]:
        """Analyze geographic distribution and market concentration."""
        state_counts = defaultdict(int)
        state_revenues = defaultdict(list)
        
        for org in organizations:
            state_counts[org.state] += 1
            if org.revenue:
                state_revenues[org.state].append(org.revenue)
        
        # Analyze each state market
        state_analysis = {}
        for state, count in state_counts.items():
            revenues = state_revenues[state]
            state_analysis[state] = {
                "organization_count": count,
                "total_revenue": sum(revenues) if revenues else 0,
                "average_revenue": mean(revenues) if revenues else 0,
                "market_concentration": "high" if count >= 5 else "moderate" if count >= 3 else "low"
            }
        
        return {
            "state_distribution": dict(state_counts),
            "state_analysis": state_analysis,
            "geographic_concentration": len([s for s, c in state_counts.items() if c >= 3]),
            "primary_markets": sorted(state_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def _identify_market_leaders(self, organizations: List[OrganizationProfile]) -> List[Dict[str, Any]]:
        """Identify market leaders by various criteria."""
        leaders = []
        
        # Revenue leaders
        revenue_orgs = [(org.revenue, org) for org in organizations if org.revenue]
        revenue_orgs.sort(reverse=True)
        
        for revenue, org in revenue_orgs[:3]:  # Top 3 by revenue
            leaders.append({
                "ein": org.ein,
                "name": org.name,
                "leadership_type": "revenue_leader",
                "metric_value": revenue,
                "market_position": self._determine_market_position(org, organizations)
            })
        
        # Efficiency leaders (high program expense ratio)
        efficiency_orgs = [(org.program_expense_ratio, org) for org in organizations 
                          if org.program_expense_ratio and org.revenue and org.revenue > 100000]
        efficiency_orgs.sort(reverse=True)
        
        for ratio, org in efficiency_orgs[:2]:  # Top 2 by efficiency
            if org.ein not in [l["ein"] for l in leaders]:  # Avoid duplicates
                leaders.append({
                    "ein": org.ein,
                    "name": org.name,
                    "leadership_type": "efficiency_leader",
                    "metric_value": ratio,
                    "market_position": self._determine_market_position(org, organizations)
                })
        
        return leaders
    
    def _identify_market_opportunities(self, organizations: List[OrganizationProfile], 
                                     segments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify market opportunities and gaps."""
        opportunities = []
        
        # Underserved segments (few organizations)
        for segment_key, segment_data in segments.items():
            if segment_data["organization_count"] <= 2:
                opportunities.append({
                    "type": "underserved_segment",
                    "segment": segment_key,
                    "opportunity_size": "high",
                    "current_players": segment_data["organization_count"],
                    "description": f"Only {segment_data['organization_count']} organizations in {segment_key}"
                })
        
        # Geographic gaps
        state_counts = defaultdict(int)
        for org in organizations:
            state_counts[org.state] += 1
        
        for state, count in state_counts.items():
            if count == 1:
                opportunities.append({
                    "type": "geographic_gap",
                    "location": state,
                    "opportunity_size": "medium",
                    "current_players": count,
                    "description": f"Only one organization in {state}"
                })
        
        return opportunities
    
    def _generate_competitive_insights(self, organizations: List[OrganizationProfile], 
                                     peer_analysis: Dict[str, Any], 
                                     market_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic competitive insights."""
        
        # Market dynamics
        market_dynamics = {
            "market_maturity": self._assess_market_maturity(organizations),
            "competitive_intensity": self._assess_overall_competitive_intensity(peer_analysis),
            "market_growth_potential": self._assess_market_growth_potential(organizations),
            "consolidation_potential": self._assess_consolidation_potential(market_analysis)
        }
        
        # Strategic recommendations
        strategic_recommendations = self._generate_strategic_recommendations(
            organizations, peer_analysis, market_analysis
        )
        
        # Key findings
        key_findings = self._extract_key_findings(peer_analysis, market_analysis)
        
        return {
            "market_dynamics": market_dynamics,
            "strategic_recommendations": strategic_recommendations,
            "key_findings": key_findings,
            "competitive_landscape_summary": self._create_landscape_summary(organizations, market_analysis)
        }
    
    def _assess_market_maturity(self, organizations: List[OrganizationProfile]) -> str:
        """Assess overall market maturity."""
        # Look at organization ages (filing history) and size distribution
        filing_histories = [len(self._get_filing_data(org)) for org in organizations]
        avg_history = mean(filing_histories) if filing_histories else 0
        
        revenues = [org.revenue for org in organizations if org.revenue]
        size_variation = stdev(revenues) / mean(revenues) if len(revenues) > 1 and mean(revenues) > 0 else 0
        
        if avg_history >= 5 and size_variation < 1.0:
            return "mature"
        elif avg_history >= 3:
            return "developing"
        else:
            return "emerging"
    
    def _get_filing_data(self, org: OrganizationProfile) -> List[Dict[str, Any]]:
        """Extract filing data from organization."""
        if hasattr(org, 'filing_data') and org.filing_data:
            return org.filing_data.get('filings', [])
        return []
    
    def _assess_overall_competitive_intensity(self, peer_analysis: Dict[str, Any]) -> str:
        """Assess overall competitive intensity in the market."""
        peer_distribution = peer_analysis.get("peer_count_distribution", {})
        
        high_competition_orgs = peer_distribution.get("many_peers_8_plus", 0)
        total_orgs = sum(peer_distribution.values())
        
        if total_orgs == 0:
            return "unknown"
        
        high_competition_ratio = high_competition_orgs / total_orgs
        
        if high_competition_ratio > 0.3:
            return "high"
        elif high_competition_ratio > 0.15:
            return "moderate"
        else:
            return "low"
    
    def _assess_market_growth_potential(self, organizations: List[OrganizationProfile]) -> str:
        """Assess market growth potential based on organization trends."""
        if not organizations:
            return "unknown"
        
        # Look at recent revenue trends if available
        growing_orgs = 0
        total_with_trends = 0
        
        for org in organizations:
            if hasattr(org, 'trend_analysis') and org.trend_analysis:
                total_with_trends += 1
                growth_class = org.trend_analysis.get("growth_classification", "unknown")
                if growth_class in ["accelerating", "steady_growth"]:
                    growing_orgs += 1
        
        if total_with_trends == 0:
            return "unknown"
        
        growth_ratio = growing_orgs / total_with_trends
        
        if growth_ratio > 0.6:
            return "high"
        elif growth_ratio > 0.4:
            return "moderate"
        else:
            return "low"
    
    def _assess_consolidation_potential(self, market_analysis: Dict[str, Any]) -> str:
        """Assess potential for market consolidation."""
        concentration = market_analysis.get("market_concentration", {})
        market_structure = concentration.get("market_structure", "unknown")
        
        if market_structure == "fragmented":
            return "high"
        elif market_structure == "moderately_concentrated":
            return "moderate"
        else:
            return "low"
    
    def _generate_strategic_recommendations(self, organizations: List[OrganizationProfile], 
                                          peer_analysis: Dict[str, Any], 
                                          market_analysis: Dict[str, Any]) -> List[str]:
        """Generate strategic recommendations based on competitive analysis."""
        recommendations = []
        
        # Market structure recommendations
        market_structure = market_analysis.get("market_concentration", {}).get("market_structure", "unknown")
        
        if market_structure == "fragmented":
            recommendations.append("Consider supporting market consolidation through strategic partnerships")
            recommendations.append("Focus on building market leaders with sustainable competitive advantages")
        
        elif market_structure == "concentrated":
            recommendations.append("Support innovative smaller players to increase market competition")
            recommendations.append("Focus on niche segments with less competitive pressure")
        
        # Geographic recommendations
        geographic_analysis = market_analysis.get("geographic_markets", {})
        state_distribution = geographic_analysis.get("state_distribution", {})
        
        if len(state_distribution) > 5:
            recommendations.append("Leverage geographic diversification for risk mitigation")
        else:
            recommendations.append("Consider expanding geographic reach for portfolio diversification")
        
        # Segment recommendations
        segments = market_analysis.get("segments", {})
        underserved_segments = [s for s, data in segments.items() if data["organization_count"] <= 2]
        
        if underserved_segments:
            recommendations.append(f"Opportunity to develop {len(underserved_segments)} underserved market segments")
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _extract_key_findings(self, peer_analysis: Dict[str, Any], 
                            market_analysis: Dict[str, Any]) -> List[str]:
        """Extract key findings from competitive analysis."""
        findings = []
        
        # Clustering findings
        cluster_analysis = peer_analysis.get("cluster_analysis", {}) 
        total_clusters = cluster_analysis.get("total_clusters", 0)
        clustering_rate = cluster_analysis.get("clustering_rate", 0)
        
        if clustering_rate > 0.7:
            findings.append(f"High market clustering: {int(clustering_rate*100)}% of organizations in {total_clusters} competitive clusters")
        elif clustering_rate > 0.4:
            findings.append(f"Moderate clustering: {total_clusters} distinct competitive clusters identified")
        else:
            findings.append("Fragmented market with limited competitive clustering")
        
        # Market concentration findings
        concentration = market_analysis.get("market_concentration", {})
        cr4 = concentration.get("concentration_ratio_4", 0)
        
        if cr4 > 0.6:
            findings.append(f"Concentrated market: Top 4 organizations control {int(cr4*100)}% of revenue")
        elif cr4 > 0.4:
            findings.append(f"Moderately concentrated: Top 4 organizations represent {int(cr4*100)}% of revenue")
        
        # Geographic findings
        geographic_markets = market_analysis.get("geographic_markets", {})
        primary_markets = geographic_markets.get("primary_markets", [])
        
        if primary_markets:
            top_state, org_count = primary_markets[0]
            findings.append(f"Geographic concentration in {top_state} with {org_count} organizations")
        
        return findings[:4]  # Top 4 findings
    
    def _create_landscape_summary(self, organizations: List[OrganizationProfile], 
                                market_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive summary of competitive landscape."""
        revenues = [org.revenue for org in organizations if org.revenue]
        
        return {
            "total_organizations": len(organizations),
            "total_market_size": sum(revenues) if revenues else 0,
            "average_organization_size": mean(revenues) if revenues else 0,
            "market_structure": market_analysis.get("market_concentration", {}).get("market_structure", "unknown"),
            "geographic_reach": len(set(org.state for org in organizations)),
            "sector_diversity": len(set(self._get_ntee_group(org.ntee_code) for org in organizations if org.ntee_code)),
            "competitive_health": self._assess_competitive_health(organizations, market_analysis)
        }
    
    def _assess_competitive_health(self, organizations: List[OrganizationProfile], 
                                 market_analysis: Dict[str, Any]) -> str:
        """Assess overall competitive health of the market."""
        # Consider multiple factors
        factors = []
        
        # Market structure factor
        market_structure = market_analysis.get("market_concentration", {}).get("market_structure", "unknown")
        if market_structure == "moderately_concentrated":
            factors.append(0.8)  # Optimal balance
        elif market_structure in ["fragmented", "concentrated"]:
            factors.append(0.6)
        
        # Geographic diversity factor
        geographic_reach = len(set(org.state for org in organizations))
        if geographic_reach >= 5:
            factors.append(0.8)
        elif geographic_reach >= 3:
            factors.append(0.6)
        else:
            factors.append(0.4)
        
        # Size diversity factor
        revenues = [org.revenue for org in organizations if org.revenue]
        if len(revenues) > 1:
            size_cv = stdev(revenues) / mean(revenues)
            if 0.5 <= size_cv <= 1.5:  # Good diversity
                factors.append(0.8)
            else:
                factors.append(0.6)
        
        health_score = mean(factors) if factors else 0.5
        
        if health_score > 0.75:
            return "excellent"
        elif health_score > 0.6:
            return "good"
        elif health_score > 0.45:
            return "fair"
        else:
            return "poor"
    
    def _analyze_funding_opportunities(self, organizations: List[OrganizationProfile], 
                                     market_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze funding opportunities based on competitive intelligence."""
        
        # Market gaps and opportunities
        market_gaps = market_analysis.get("market_opportunities", [])
        
        # Strategic funding priorities
        funding_priorities = self._identify_funding_priorities(organizations, market_analysis)
        
        # Portfolio optimization recommendations
        portfolio_recommendations = self._generate_portfolio_recommendations(organizations, market_analysis)
        
        # Risk-adjusted opportunities
        risk_adjusted_opportunities = self._identify_risk_adjusted_opportunities(organizations)
        
        return {
            "market_gaps": market_gaps,
            "funding_priorities": funding_priorities,
            "portfolio_recommendations": portfolio_recommendations,
            "risk_adjusted_opportunities": risk_adjusted_opportunities,
            "strategic_funding_themes": self._identify_strategic_themes(organizations, market_analysis)
        }
    
    def _identify_funding_priorities(self, organizations: List[OrganizationProfile], 
                                   market_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify strategic funding priorities."""
        priorities = []
        
        # Market leaders with growth potential
        leaders = market_analysis.get("market_leaders", [])
        for leader in leaders:
            org = next((o for o in organizations if o.ein == leader["ein"]), None)
            if org and hasattr(org, 'risk_classification') and org.risk_classification in ["low", "moderate"]:
                priorities.append({
                    "type": "scale_market_leader",
                    "organization": leader["name"],
                    "rationale": f"Proven {leader['leadership_type']} with growth potential",
                    "priority_level": "high"
                })
        
        # Underserved market segments
        segments = market_analysis.get("segments", {})
        for segment, data in segments.items():
            if data["organization_count"] <= 2:
                priorities.append({
                    "type": "develop_underserved_segment",
                    "segment": segment,
                    "rationale": f"Only {data['organization_count']} organizations serving this market",
                    "priority_level": "medium"
                })
        
        return priorities[:5]  # Top 5 priorities
    
    def _generate_portfolio_recommendations(self, organizations: List[OrganizationProfile], 
                                          market_analysis: Dict[str, Any]) -> List[str]:
        """Generate portfolio-level recommendations."""
        recommendations = []
        
        # Diversification recommendations
        geographic_reach = len(set(org.state for org in organizations))
        if geographic_reach < 3:
            recommendations.append("Increase geographic diversification to reduce regional risk")
        
        # Size diversification
        revenues = [org.revenue for org in organizations if org.revenue]
        if revenues:
            large_orgs = sum(1 for r in revenues if r > 1000000)
            small_orgs = sum(1 for r in revenues if r < 250000)
            
            if large_orgs / len(revenues) > 0.7:
                recommendations.append("Balance portfolio with smaller, innovative organizations")
            elif small_orgs / len(revenues) > 0.7:
                recommendations.append("Include larger organizations for greater impact scale")
        
        # Risk diversification
        low_risk_orgs = sum(1 for org in organizations 
                           if hasattr(org, 'risk_classification') and org.risk_classification == "low")
        
        if low_risk_orgs / len(organizations) < 0.3:
            recommendations.append("Increase allocation to low-risk, stable organizations")
        
        return recommendations
    
    def _identify_risk_adjusted_opportunities(self, organizations: List[OrganizationProfile]) -> List[Dict[str, Any]]:
        """Identify opportunities adjusted for risk levels."""
        opportunities = []
        
        for org in organizations:
            # High-impact, low-risk opportunities
            if (hasattr(org, 'risk_classification') and org.risk_classification == "low" and
                hasattr(org, 'grant_readiness_score') and org.grant_readiness_score > 0.7):
                
                opportunities.append({
                    "ein": org.ein,
                    "name": org.name,
                    "opportunity_type": "high_confidence_investment",
                    "risk_level": "low",
                    "expected_impact": "high",
                    "rationale": "Low risk with high grant readiness"
                })
            
            # High-potential, moderate-risk opportunities
            elif (hasattr(org, 'growth_classification') and 
                  org.growth_classification in ["accelerating", "steady_growth"] and
                  hasattr(org, 'risk_classification') and org.risk_classification == "moderate"):
                
                opportunities.append({
                    "ein": org.ein,
                    "name": org.name,
                    "opportunity_type": "growth_investment",
                    "risk_level": "moderate",
                    "expected_impact": "high",
                    "rationale": "Strong growth trajectory with manageable risk"
                })
        
        return opportunities
    
    def _identify_strategic_themes(self, organizations: List[OrganizationProfile], 
                                 market_analysis: Dict[str, Any]) -> List[str]:
        """Identify strategic funding themes."""
        themes = []
        
        # Market development themes
        if market_analysis.get("market_concentration", {}).get("market_structure") == "fragmented":
            themes.append("market_consolidation_and_leadership_development")
        
        # Geographic themes
        geographic_markets = market_analysis.get("geographic_markets", {})
        if geographic_markets.get("geographic_concentration", 0) >= 3:
            themes.append("geographic_expansion_and_diversification")
        
        # Sector themes
        ntee_groups = set(self._get_ntee_group(org.ntee_code) for org in organizations if org.ntee_code)
        if "health_general" in ntee_groups and "nutrition_food" in ntee_groups:
            themes.append("integrated_health_and_nutrition_approach")
        
        return themes
    
    def validate_inputs(self, config: ProcessorConfig) -> List[str]:
        """Validate inputs for competitive intelligence analysis."""
        errors = []
        
        if not config.workflow_id:
            errors.append("Workflow ID is required")
        
        return errors


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return CompetitiveIntelligenceProcessor()