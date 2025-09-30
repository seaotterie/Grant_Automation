"""
Network Intelligence Tool
12-Factor compliant tool for board network analysis.

Purpose: Board network and relationship mapping analysis
Cost: $0.04 per analysis
Replaces: board_network_analyzer.py, enhanced_network_analyzer.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Optional
import time
from datetime import datetime

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext
from .network_models import (
    NetworkIntelligenceInput,
    NetworkIntelligenceOutput,
    BoardMemberProfile,
    NetworkConnection,
    NetworkStrength,
    RelationshipType,
    CentralityMetrics,
    NetworkCluster,
    RelationshipPathway,
    StrategicConnection,
    NetworkIntelligenceAnalysis,
    FunderConnectionAnalysis,
    NETWORK_INTELLIGENCE_COST
)


class NetworkIntelligenceTool(BaseTool[NetworkIntelligenceOutput]):
    """
    12-Factor Network Intelligence Tool

    Factor 4: Returns structured NetworkIntelligenceOutput
    Factor 6: Stateless - no persistence between runs
    Factor 10: Single responsibility - network analysis only
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize network intelligence tool."""
        super().__init__(config)
        self.openai_api_key = config.get("openai_api_key") if config else None

    def get_tool_name(self) -> str:
        return "Network Intelligence Tool"

    def get_tool_version(self) -> str:
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        return "Board network analysis and relationship mapping for strategic cultivation"

    async def _execute(
        self,
        context: ToolExecutionContext,
        network_input: NetworkIntelligenceInput
    ) -> NetworkIntelligenceOutput:
        """Execute network intelligence analysis."""
        start_time = time.time()

        self.logger.info(
            f"Starting network intelligence analysis: {network_input.organization_name} "
            f"with {len(network_input.board_members)} board members"
        )

        # Board member profiling
        board_profiles = self._profile_board_members(network_input)

        # Network connections
        connections = self._map_connections(network_input, board_profiles)
        strategic_connections = self._identify_strategic_connections(network_input, board_profiles)

        # Centrality analysis
        centrality = self._calculate_centrality(board_profiles, connections)

        # Cluster identification
        clusters = self._identify_clusters(network_input, connections)

        # Overall network analysis
        network_analysis = self._analyze_network(network_input, board_profiles, connections, centrality)

        # Funder connection analysis (if target provided)
        funder_analysis = None
        if network_input.target_funder_name:
            funder_analysis = self._analyze_funder_connections(
                network_input, board_profiles, connections
            )

        # Network quality
        quality_score = self._assess_network_quality(network_input)

        processing_time = time.time() - start_time

        output = NetworkIntelligenceOutput(
            board_member_profiles=board_profiles,
            all_connections=connections,
            strategic_connections=strategic_connections,
            network_centrality=centrality,
            identified_clusters=clusters,
            network_analysis=network_analysis,
            funder_connection_analysis=funder_analysis,
            analysis_date=datetime.now().isoformat(),
            network_quality_score=quality_score,
            confidence_level=0.85,
            processing_time_seconds=processing_time,
            api_cost_usd=NETWORK_INTELLIGENCE_COST
        )

        self.logger.info(
            f"Completed network analysis: {len(board_profiles)} profiles, "
            f"{len(connections)} connections, quality={quality_score:.2f}"
        )

        return output

    def _profile_board_members(self, inp: NetworkIntelligenceInput) -> list[BoardMemberProfile]:
        """Profile each board member"""
        profiles = []

        for member in inp.board_members:
            name = member.get("name", "Unknown")
            title = member.get("title")
            affiliations_str = member.get("affiliations", "")

            # Parse affiliations
            current_affiliations = [a.strip() for a in affiliations_str.split(",") if a.strip()]
            past_affiliations = []  # Would need historical data

            # Calculate metrics (placeholder - would use real network analysis)
            centrality = min(1.0, len(current_affiliations) / 5.0)  # Simple heuristic
            influence = centrality * 0.9  # Simplified
            connection_count = len(current_affiliations)

            # Identify connections
            direct_connections = current_affiliations[:5]  # Top 5
            indirect_connections = []  # Would need broader network data

            # Strategic value
            strategic_value = centrality
            value_reasoning = f"Connected to {connection_count} organizations" if connection_count > 0 else "Limited network data available"

            profiles.append(BoardMemberProfile(
                name=name,
                title=title,
                current_affiliations=current_affiliations,
                past_affiliations=past_affiliations,
                centrality_score=centrality,
                influence_score=influence,
                connection_count=connection_count,
                direct_connections=direct_connections,
                indirect_connections=indirect_connections,
                strategic_value_score=strategic_value,
                strategic_value_reasoning=value_reasoning
            ))

        return profiles

    def _map_connections(
        self,
        inp: NetworkIntelligenceInput,
        profiles: list[BoardMemberProfile]
    ) -> list[NetworkConnection]:
        """Map network connections"""
        connections = []

        # Board member to affiliation connections
        for profile in profiles:
            for affiliation in profile.current_affiliations:
                connections.append(NetworkConnection(
                    from_entity=profile.name,
                    to_entity=affiliation,
                    connection_type=RelationshipType.BOARD_MEMBER,
                    strength=NetworkStrength.STRONG,
                    description=f"{profile.name} serves on board/leadership of {affiliation}",
                    strategic_value="High - direct board connection"
                ))

        # Partner organization connections
        if inp.partner_organizations:
            for partner in inp.partner_organizations:
                connections.append(NetworkConnection(
                    from_entity=inp.organization_name,
                    to_entity=partner,
                    connection_type=RelationshipType.PARTNER,
                    strength=NetworkStrength.MODERATE,
                    description=f"Partnership with {partner}",
                    strategic_value="Moderate - organizational partnership"
                ))

        return connections

    def _identify_strategic_connections(
        self,
        inp: NetworkIntelligenceInput,
        profiles: list[BoardMemberProfile]
    ) -> list[StrategicConnection]:
        """Identify strategic connection opportunities"""
        strategic = []

        # High-value profiles
        high_value_profiles = [p for p in profiles if p.strategic_value_score > 0.6]

        for profile in high_value_profiles[:3]:  # Top 3
            strategic.append(StrategicConnection(
                target_entity=profile.name,
                connection_type="Board Member Cultivation",
                priority="high",
                rationale=f"High centrality ({profile.centrality_score:.2f}) with {profile.connection_count} connections",
                cultivation_steps=[
                    "Schedule one-on-one meeting",
                    "Discuss strategic priorities",
                    "Identify shared interests",
                    "Develop action plan"
                ],
                estimated_timeline="3-6 months",
                success_probability=0.75
            ))

        return strategic

    def _calculate_centrality(
        self,
        profiles: list[BoardMemberProfile],
        connections: list[NetworkConnection]
    ) -> CentralityMetrics:
        """Calculate network centrality metrics"""

        # Simple calculations (would use proper network analysis library in production)
        avg_centrality = sum(p.centrality_score for p in profiles) / len(profiles) if profiles else 0

        return CentralityMetrics(
            degree_centrality=avg_centrality,
            betweenness_centrality=avg_centrality * 0.8,
            closeness_centrality=avg_centrality * 0.9,
            eigenvector_centrality=avg_centrality * 0.85,
            overall_centrality=avg_centrality,
            centrality_interpretation=f"{'Strong' if avg_centrality > 0.6 else 'Moderate' if avg_centrality > 0.3 else 'Limited'} network centrality with average connections across board"
        )

    def _identify_clusters(
        self,
        inp: NetworkIntelligenceInput,
        connections: list[NetworkConnection]
    ) -> list[NetworkCluster]:
        """Identify network clusters"""

        # Simplified clustering (would use proper community detection in production)
        clusters = []

        # Create a cluster for board connections
        board_entities = set()
        for conn in connections:
            if conn.connection_type == RelationshipType.BOARD_MEMBER:
                board_entities.add(conn.to_entity)

        if board_entities:
            clusters.append(NetworkCluster(
                cluster_id="board_network",
                cluster_name="Board Network Cluster",
                member_count=len(board_entities),
                members=list(board_entities)[:10],  # Top 10
                cluster_focus="Organizations with board/leadership connections",
                strategic_relevance="High - direct influence opportunities"
            ))

        return clusters

    def _analyze_network(
        self,
        inp: NetworkIntelligenceInput,
        profiles: list[BoardMemberProfile],
        connections: list[NetworkConnection],
        centrality: CentralityMetrics
    ) -> NetworkIntelligenceAnalysis:
        """Perform overall network analysis"""

        network_size = len(profiles) + len(set(c.to_entity for c in connections))
        total_possible_connections = network_size * (network_size - 1) / 2
        network_density = len(connections) / total_possible_connections if total_possible_connections > 0 else 0

        # Identify strengths
        strengths = []
        if len(profiles) >= 5:
            strengths.append(f"Substantial board size ({len(profiles)} members)")
        if centrality.overall_centrality > 0.5:
            strengths.append("Strong network centrality and connections")
        if network_density > 0.3:
            strengths.append("High network density indicating good connectivity")

        # Key influencers
        influencers = [p.name for p in sorted(profiles, key=lambda x: x.influence_score, reverse=True)[:3]]

        # Network gaps
        gaps = []
        if centrality.overall_centrality < 0.3:
            gaps.append("Limited network centrality - need better-connected board members")
        if network_density < 0.2:
            gaps.append("Low network density - board members not well connected")

        # Recommendations
        recommended_additions = [
            "Recruit board members with foundation connections",
            "Add members from corporate sector",
            "Seek board members with government relationships"
        ]

        # Strategic opportunities
        opportunities = [
            "Leverage existing board connections for introductions",
            "Develop board cultivation strategy",
            "Create board network mapping initiative"
        ]

        # Cultivation priorities
        priorities = [
            "Engage top 3 most connected board members",
            "Map pathways to target funders",
            "Develop board member activation plan"
        ]

        summary = f"""
{inp.organization_name} has a {'strong' if len(profiles) >= 7 else 'moderate' if len(profiles) >= 5 else 'developing'}
board network with {len(profiles)} members and {len(connections)} identified connections.
The network shows {'high' if centrality.overall_centrality > 0.6 else 'moderate' if centrality.overall_centrality > 0.3 else 'limited'}
centrality with {'strong' if network_density > 0.3 else 'moderate'} connectivity between board members and external organizations.
Key influencers include {', '.join(influencers[:2]) if influencers else 'board leadership'}.
Strategic opportunities exist to leverage these connections for fundraising and partnership development.
        """.strip()

        return NetworkIntelligenceAnalysis(
            network_executive_summary=summary,
            network_size=network_size,
            network_density=network_density,
            average_path_length=2.5,  # Placeholder
            network_strengths=strengths,
            key_influencers=influencers,
            network_gaps=gaps,
            recommended_additions=recommended_additions,
            strategic_opportunities=opportunities,
            cultivation_priorities=priorities
        )

    def _analyze_funder_connections(
        self,
        inp: NetworkIntelligenceInput,
        profiles: list[BoardMemberProfile],
        connections: list[NetworkConnection]
    ) -> FunderConnectionAnalysis:
        """Analyze connections to target funder"""

        funder_name = inp.target_funder_name
        funder_board = inp.target_funder_board or []

        # Find direct connections
        direct_connections = []
        for profile in profiles:
            for affiliation in profile.current_affiliations:
                if funder_name and funder_name.lower() in affiliation.lower():
                    direct_connections.append(profile.name)
                    break

        # Find indirect pathways
        indirect_pathways = []
        for profile in profiles:
            if profile.name not in direct_connections:
                # Check if any affiliations connect to funder board
                for affiliation in profile.current_affiliations:
                    for funder_board_member in funder_board:
                        if funder_board_member.lower() in affiliation.lower():
                            pathway = RelationshipPathway(
                                target=funder_name,
                                pathway=[inp.organization_name, profile.name, affiliation, funder_name],
                                pathway_strength=NetworkStrength.MODERATE,
                                pathway_description=f"Through {profile.name}'s connection to {affiliation}",
                                cultivation_strategy=f"Request {profile.name} to facilitate introduction through {affiliation}"
                            )
                            indirect_pathways.append(pathway)

        # Determine connection strength
        if len(direct_connections) >= 2:
            strength = NetworkStrength.VERY_STRONG
        elif len(direct_connections) == 1:
            strength = NetworkStrength.STRONG
        elif indirect_pathways:
            strength = NetworkStrength.MODERATE
        else:
            strength = NetworkStrength.WEAK

        # Connection advantage
        if direct_connections:
            advantage = f"Direct board connections through {', '.join(direct_connections)} provide significant competitive advantage"
        elif indirect_pathways:
            advantage = f"Indirect pathways available through {len(indirect_pathways)} board connections"
        else:
            advantage = "Limited existing connections - cold approach required"

        # Cultivation strategy
        if direct_connections:
            strategy = f"Engage {direct_connections[0]} to facilitate warm introduction and advocacy"
        elif indirect_pathways:
            strategy = f"Cultivate indirect pathways through {indirect_pathways[0].pathway[1]}"
        else:
            strategy = "Develop new connections through networking and research"

        # Immediate actions
        actions = []
        if direct_connections:
            actions.append(f"Schedule meeting with {direct_connections[0]} to discuss funder")
            actions.append("Request introduction or recommendation")
        else:
            actions.append("Research funder board composition")
            actions.append("Identify networking opportunities")

        # Success probability
        if strength in [NetworkStrength.VERY_STRONG, NetworkStrength.STRONG]:
            success_prob = 0.7
        elif strength == NetworkStrength.MODERATE:
            success_prob = 0.4
        else:
            success_prob = 0.2

        return FunderConnectionAnalysis(
            funder_name=funder_name,
            direct_board_connections=direct_connections,
            direct_connection_count=len(direct_connections),
            indirect_pathways=indirect_pathways,
            strongest_pathway=indirect_pathways[0] if indirect_pathways else None,
            overall_connection_strength=strength,
            connection_advantage=advantage,
            recommended_cultivation_strategy=strategy,
            immediate_actions=actions,
            success_probability=success_prob
        )

    def _assess_network_quality(self, inp: NetworkIntelligenceInput) -> float:
        """Assess quality/completeness of network data"""
        score = 0.0
        total = 0.0

        # Board members provided
        total += 1
        if len(inp.board_members) >= 5:
            score += 1
        elif len(inp.board_members) >= 3:
            score += 0.7

        # Affiliations data
        total += 1
        affiliation_count = sum(1 for m in inp.board_members if m.get("affiliations"))
        if affiliation_count >= len(inp.board_members) * 0.7:
            score += 1
        elif affiliation_count >= len(inp.board_members) * 0.5:
            score += 0.7

        # Additional data
        if inp.key_donors:
            score += 0.3
        if inp.partner_organizations:
            score += 0.3
        total += 0.6

        return min(1.0, score / total)

    def get_cost_estimate(self) -> Optional[float]:
        return NETWORK_INTELLIGENCE_COST

    def validate_inputs(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate tool inputs."""
        network_input = kwargs.get("network_input")

        if not network_input:
            return False, "network_input is required"

        if not isinstance(network_input, NetworkIntelligenceInput):
            return False, "network_input must be NetworkIntelligenceInput instance"

        if not network_input.organization_ein:
            return False, "organization_ein is required"

        if not network_input.board_members:
            return False, "board_members list is required"

        return True, None


# Convenience function
async def analyze_network_intelligence(
    organization_ein: str,
    organization_name: str,
    board_members: list[dict],
    target_funder_name: Optional[str] = None,
    target_funder_board: Optional[list] = None,
    key_donors: Optional[list] = None,
    partner_organizations: Optional[list] = None,
    advisory_board: Optional[list] = None,
    config: Optional[dict] = None
) -> ToolResult[NetworkIntelligenceOutput]:
    """Analyze network intelligence."""

    tool = NetworkIntelligenceTool(config)

    network_input = NetworkIntelligenceInput(
        organization_ein=organization_ein,
        organization_name=organization_name,
        board_members=board_members,
        target_funder_name=target_funder_name,
        target_funder_board=target_funder_board,
        key_donors=key_donors,
        partner_organizations=partner_organizations,
        advisory_board=advisory_board
    )

    return await tool.execute(network_input=network_input)
