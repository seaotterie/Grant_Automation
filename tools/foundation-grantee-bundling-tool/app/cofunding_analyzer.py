"""
Co-Funding Analyzer
Phase 2: Funder similarity and peer group detection

Analyzes which foundations fund the same grantees to identify:
- Peer funders (high co-funding overlap)
- Funder similarity scores (Jaccard + recency weighted)
- Strategic recommendations for prospecting
"""

import logging
from typing import List, Dict, Set, Optional, Any
from collections import defaultdict
from datetime import datetime
import networkx as nx
from networkx.algorithms import community

from .bundling_models import (
    CoFundingAnalysisInput,
    CoFundingAnalysisOutput,
    FunderSimilarity,
    PeerFunderGroup,
    FunderRecommendation,
    GranteeBundlingOutput
)

logger = logging.getLogger(__name__)


class CoFundingAnalyzer:
    """
    Analyzes co-funding patterns between foundations.

    Phase 2: Identifies peer funders and generates strategic recommendations.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze(self, input: CoFundingAnalysisInput) -> CoFundingAnalysisOutput:
        """
        Execute co-funding analysis.

        Args:
            input: CoFundingAnalysisInput with bundling results

        Returns:
            CoFundingAnalysisOutput with similarity metrics and peer groups
        """
        start_time = datetime.now()

        bundling = input.bundling_results

        self.logger.info(
            f"Starting co-funding analysis for {bundling.total_foundations_analyzed} foundations"
        )

        # Step 1: Build foundation-grantee mapping
        foundation_grantees = self._build_foundation_grantee_map(bundling)

        # Step 2: Compute pairwise similarity
        similarity_pairs = self._compute_pairwise_similarity(
            foundation_grantees,
            bundling,
            input.similarity_threshold
        )

        # Step 3: Build funder similarity network
        funder_graph = None
        network_stats = {}
        if input.include_network_graph:
            funder_graph = self._build_funder_network(similarity_pairs, input.similarity_threshold)
            network_stats = self._compute_network_stats(funder_graph)

        # Step 4: Detect peer funder groups (Louvain clustering)
        peer_groups = self._detect_peer_groups(funder_graph) if funder_graph else []

        # Step 5: Generate strategic recommendations
        recommendations = self._generate_recommendations(
            similarity_pairs,
            peer_groups,
            bundling
        )

        # Step 6: Filter high similarity pairs
        highly_similar = [
            s for s in similarity_pairs
            if s.similarity_score >= input.similarity_threshold
        ]

        processing_time = (datetime.now() - start_time).total_seconds()

        output = CoFundingAnalysisOutput(
            funder_similarity_pairs=similarity_pairs,
            highly_similar_pairs=highly_similar,
            peer_funder_groups=peer_groups,
            foundation_network_graph=self._serialize_graph(funder_graph) if funder_graph else None,
            network_statistics=network_stats,
            recommendations=recommendations[:input.max_peer_funders],
            processing_time_seconds=processing_time,
            analysis_date=datetime.now().isoformat()
        )

        self.logger.info(
            f"Completed co-funding analysis: {len(highly_similar)} similar pairs, "
            f"{len(peer_groups)} peer groups"
        )

        return output

    def _build_foundation_grantee_map(
        self, bundling: GranteeBundlingOutput
    ) -> Dict[str, Set[str]]:
        """Build mapping of foundation EIN -> set of grantee EINs/names."""

        foundation_grantees = defaultdict(set)

        for grantee in bundling.bundled_grantees:
            grantee_key = grantee.grantee_ein or grantee.normalized_name

            for funding_source in grantee.funding_sources:
                foundation_grantees[funding_source.foundation_ein].add(grantee_key)

        self.logger.debug(f"Built grantee map for {len(foundation_grantees)} foundations")
        return foundation_grantees

    def _compute_pairwise_similarity(
        self,
        foundation_grantees: Dict[str, Set[str]],
        bundling: GranteeBundlingOutput,
        threshold: float
    ) -> List[FunderSimilarity]:
        """Compute Jaccard similarity for all foundation pairs."""

        similarities = []
        foundation_eins = list(foundation_grantees.keys())

        # Get foundation names (from bundling results)
        foundation_names = {}
        for grantee in bundling.bundled_grantees:
            for fs in grantee.funding_sources:
                if fs.foundation_ein not in foundation_names:
                    foundation_names[fs.foundation_ein] = fs.foundation_name

        # Compute pairwise similarity
        for i, ein1 in enumerate(foundation_eins):
            for ein2 in foundation_eins[i+1:]:
                grantees1 = foundation_grantees[ein1]
                grantees2 = foundation_grantees[ein2]

                intersection = grantees1 & grantees2
                union = grantees1 | grantees2

                if len(union) == 0:
                    continue

                # Jaccard similarity
                jaccard = len(intersection) / len(union)

                # Recency weighting (boost recent co-funding)
                recency_score = self._calculate_recency_score(
                    ein1, ein2, bundling
                )

                # Weighted similarity (Jaccard * recency boost)
                similarity_score = jaccard * (1 + recency_score * 0.2)

                # Calculate co-funding amount
                total_co_funding = self._calculate_co_funding_amount(
                    ein1, ein2, intersection, bundling
                )

                avg_co_grant = total_co_funding / len(intersection) if intersection else 0

                # Find common themes
                common_themes = self._find_common_themes(
                    ein1, ein2, intersection, bundling
                )

                # Find funding years overlap
                funding_years = self._find_funding_years_overlap(
                    ein1, ein2, bundling
                )

                similarity = FunderSimilarity(
                    foundation_ein_1=ein1,
                    foundation_name_1=foundation_names.get(ein1, "Unknown"),
                    foundation_ein_2=ein2,
                    foundation_name_2=foundation_names.get(ein2, "Unknown"),
                    similarity_score=similarity_score,
                    jaccard_similarity=jaccard,
                    shared_grantees_count=len(intersection),
                    total_co_funding_amount=total_co_funding,
                    average_co_grant_size=avg_co_grant,
                    recency_score=recency_score,
                    funding_years_overlap=funding_years,
                    shared_grantees=list(intersection),
                    common_geographic_focus=None,  # TODO: Implement
                    common_thematic_focus=common_themes
                )

                similarities.append(similarity)

        # Sort by similarity score
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)

        self.logger.debug(f"Computed {len(similarities)} similarity pairs")
        return similarities

    def _calculate_recency_score(
        self,
        ein1: str,
        ein2: str,
        bundling: GranteeBundlingOutput
    ) -> float:
        """Calculate recency score (0-1) based on recent co-funding."""

        current_year = datetime.now().year
        recent_years = [current_year - 1, current_year - 2]  # Last 2 years

        recent_co_funding_count = 0
        total_co_funding_count = 0

        for grantee in bundling.bundled_grantees:
            funder_eins = set(fs.foundation_ein for fs in grantee.funding_sources)

            if ein1 in funder_eins and ein2 in funder_eins:
                total_co_funding_count += 1

                # Check if any grants were recent
                for fs in grantee.funding_sources:
                    if fs.foundation_ein in [ein1, ein2] and fs.grant_year in recent_years:
                        recent_co_funding_count += 1
                        break

        if total_co_funding_count == 0:
            return 0.0

        return recent_co_funding_count / total_co_funding_count

    def _calculate_co_funding_amount(
        self,
        ein1: str,
        ein2: str,
        shared_grantees: Set[str],
        bundling: GranteeBundlingOutput
    ) -> float:
        """Calculate total amount co-funded to shared grantees."""

        total = 0.0

        for grantee in bundling.bundled_grantees:
            grantee_key = grantee.grantee_ein or grantee.normalized_name

            if grantee_key not in shared_grantees:
                continue

            # Sum grants from both foundations to this grantee
            for fs in grantee.funding_sources:
                if fs.foundation_ein in [ein1, ein2]:
                    total += fs.grant_amount

        return total

    def _find_common_themes(
        self,
        ein1: str,
        ein2: str,
        shared_grantees: Set[str],
        bundling: GranteeBundlingOutput
    ) -> List[str]:
        """Find common thematic focus areas."""

        all_purposes = []

        for grantee in bundling.bundled_grantees:
            grantee_key = grantee.grantee_ein or grantee.normalized_name

            if grantee_key in shared_grantees:
                all_purposes.extend(grantee.common_purposes)

        # Count frequency
        from collections import Counter
        purpose_counts = Counter(all_purposes)

        # Return top 5 themes
        return [purpose for purpose, count in purpose_counts.most_common(5)]

    def _find_funding_years_overlap(
        self,
        ein1: str,
        ein2: str,
        bundling: GranteeBundlingOutput
    ) -> List[int]:
        """Find years where both foundations were active."""

        years1 = set()
        years2 = set()

        for grantee in bundling.bundled_grantees:
            for fs in grantee.funding_sources:
                if fs.foundation_ein == ein1:
                    years1.add(fs.grant_year)
                elif fs.foundation_ein == ein2:
                    years2.add(fs.grant_year)

        overlap = sorted(years1 & years2)
        return overlap

    def _build_funder_network(
        self,
        similarities: List[FunderSimilarity],
        threshold: float
    ) -> nx.Graph:
        """Build NetworkX graph of funder relationships."""

        graph = nx.Graph()

        for sim in similarities:
            if sim.similarity_score >= threshold:
                # Add nodes
                if not graph.has_node(sim.foundation_ein_1):
                    graph.add_node(
                        sim.foundation_ein_1,
                        name=sim.foundation_name_1,
                        type='foundation'
                    )

                if not graph.has_node(sim.foundation_ein_2):
                    graph.add_node(
                        sim.foundation_ein_2,
                        name=sim.foundation_name_2,
                        type='foundation'
                    )

                # Add edge
                graph.add_edge(
                    sim.foundation_ein_1,
                    sim.foundation_ein_2,
                    weight=sim.similarity_score,
                    jaccard=sim.jaccard_similarity,
                    shared_grantees=sim.shared_grantees_count,
                    co_funding=sim.total_co_funding_amount
                )

        self.logger.debug(
            f"Built funder network: {graph.number_of_nodes()} nodes, "
            f"{graph.number_of_edges()} edges"
        )

        return graph

    def _detect_peer_groups(self, graph: nx.Graph) -> List[PeerFunderGroup]:
        """Detect peer funder groups using Louvain clustering."""

        if graph.number_of_nodes() < 2:
            return []

        try:
            # Louvain community detection
            communities = community.louvain_communities(graph, seed=42)

            peer_groups = []

            for i, community_set in enumerate(communities):
                if len(community_set) < 2:
                    continue  # Skip single-node communities

                community_list = list(community_set)

                # Get community characteristics
                member_names = [graph.nodes[node]['name'] for node in community_list]

                # Calculate total funding in cluster
                total_funding = 0.0
                edge_count = 0

                for u, v in graph.edges(community_list):
                    if u in community_set and v in community_set:
                        total_funding += graph[u][v].get('co_funding', 0)
                        edge_count += 1

                # Cluster density
                max_edges = len(community_list) * (len(community_list) - 1) / 2
                density = edge_count / max_edges if max_edges > 0 else 0

                # Find bridge foundations (high betweenness)
                try:
                    betweenness = nx.betweenness_centrality(graph)
                    bridges = [
                        node for node in community_list
                        if betweenness.get(node, 0) > 0.5
                    ]
                except:
                    bridges = []

                peer_group = PeerFunderGroup(
                    cluster_id=f"peer_group_{i}",
                    cluster_name=f"Peer Group {i+1}",
                    member_foundations=community_list,
                    member_count=len(community_list),
                    shared_focus_areas=[],  # TODO: Extract from themes
                    geographic_concentration=None,  # TODO: Implement
                    average_grant_size=0,  # TODO: Calculate
                    total_cluster_funding=total_funding,
                    cluster_density=density,
                    bridge_foundations=bridges
                )

                peer_groups.append(peer_group)

            self.logger.debug(f"Detected {len(peer_groups)} peer groups")
            return peer_groups

        except Exception as e:
            self.logger.error(f"Error detecting peer groups: {e}")
            return []

    def _generate_recommendations(
        self,
        similarities: List[FunderSimilarity],
        peer_groups: List[PeerFunderGroup],
        bundling: GranteeBundlingOutput
    ) -> List[FunderRecommendation]:
        """Generate strategic funder recommendations."""

        recommendations = []

        # Recommendation 1: Top similar funders
        for sim in similarities[:10]:  # Top 10 most similar
            if sim.similarity_score >= 0.5:  # High similarity
                rec = FunderRecommendation(
                    recommended_foundation_ein=sim.foundation_ein_2,
                    recommended_foundation_name=sim.foundation_name_2,
                    recommendation_type='peer_funder',
                    rationale=f"High co-funding overlap ({sim.jaccard_similarity:.1%}) with {sim.shared_grantees_count} shared grantees",
                    confidence_score=sim.similarity_score,
                    supporting_evidence=[
                        f"Shared {sim.shared_grantees_count} grantees",
                        f"${sim.total_co_funding_amount:,.0f} in co-funding",
                        f"Common themes: {', '.join(sim.common_thematic_focus[:3])}"
                    ],
                    shared_funders=[sim.foundation_ein_1],
                    similarity_to_current_funders=sim.similarity_score,
                    estimated_grant_range="$25K-$100K",  # Placeholder
                    suggested_approach="Reference shared grantees and common funding priorities",
                    priority='high' if sim.similarity_score > 0.7 else 'medium'
                )

                recommendations.append(rec)

        # Recommendation 2: Peer group members
        for group in peer_groups:
            if group.member_count >= 3:
                for member_ein in group.member_foundations[:5]:  # Top 5 per group
                    # Get foundation name
                    foundation_name = None
                    for grantee in bundling.bundled_grantees:
                        for fs in grantee.funding_sources:
                            if fs.foundation_ein == member_ein:
                                foundation_name = fs.foundation_name
                                break
                        if foundation_name:
                            break

                    if not foundation_name:
                        continue

                    rec = FunderRecommendation(
                        recommended_foundation_ein=member_ein,
                        recommended_foundation_name=foundation_name,
                        recommendation_type='cluster_member',
                        rationale=f"Member of {group.cluster_name} with {group.member_count} peer funders",
                        confidence_score=group.cluster_density,
                        supporting_evidence=[
                            f"Part of {group.member_count}-funder peer group",
                            f"Cluster density: {group.cluster_density:.1%}",
                            f"Total cluster funding: ${group.total_cluster_funding:,.0f}"
                        ],
                        shared_funders=group.member_foundations,
                        similarity_to_current_funders=group.cluster_density,
                        estimated_grant_range="Varies by foundation",
                        suggested_approach="Emphasize peer group connections and shared priorities",
                        priority='medium'
                    )

                    recommendations.append(rec)

        # Sort by confidence and priority
        recommendations.sort(
            key=lambda x: (1 if x.priority == 'high' else 2, -x.confidence_score)
        )

        return recommendations

    def _compute_network_stats(self, graph: nx.Graph) -> Dict[str, Any]:
        """Compute network statistics."""

        if not graph or graph.number_of_nodes() == 0:
            return {}

        stats = {
            'total_foundations': graph.number_of_nodes(),
            'total_connections': graph.number_of_edges(),
            'network_density': nx.density(graph),
            'average_degree': sum(dict(graph.degree()).values()) / graph.number_of_nodes(),
            'is_connected': nx.is_connected(graph)
        }

        if nx.is_connected(graph):
            stats['diameter'] = nx.diameter(graph)
            stats['average_path_length'] = nx.average_shortest_path_length(graph)

        # Find most central foundations
        try:
            degree_centrality = nx.degree_centrality(graph)
            top_central = sorted(
                degree_centrality.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]

            stats['top_central_foundations'] = [
                {
                    'ein': ein,
                    'name': graph.nodes[ein].get('name', 'Unknown'),
                    'centrality': centrality
                }
                for ein, centrality in top_central
            ]
        except Exception as e:
            self.logger.warning(f"Could not compute centrality: {e}")

        return stats

    def _serialize_graph(self, graph: nx.Graph) -> Dict[str, Any]:
        """Serialize NetworkX graph to JSON-compatible dict."""

        if not graph:
            return None

        return {
            'nodes': [
                {
                    'id': node,
                    'name': graph.nodes[node].get('name', 'Unknown'),
                    'type': graph.nodes[node].get('type', 'foundation')
                }
                for node in graph.nodes()
            ],
            'edges': [
                {
                    'source': u,
                    'target': v,
                    'weight': graph[u][v].get('weight', 1.0),
                    'jaccard': graph[u][v].get('jaccard', 0),
                    'shared_grantees': graph[u][v].get('shared_grantees', 0),
                    'co_funding': graph[u][v].get('co_funding', 0)
                }
                for u, v in graph.edges()
            ]
        }


# Convenience function
async def analyze_cofunding(
    bundling_results: GranteeBundlingOutput,
    similarity_threshold: float = 0.3,
    max_peer_funders: int = 10,
    include_network_graph: bool = True
) -> CoFundingAnalysisOutput:
    """Analyze co-funding patterns."""

    analyzer = CoFundingAnalyzer()

    input_data = CoFundingAnalysisInput(
        bundling_results=bundling_results,
        similarity_threshold=similarity_threshold,
        max_peer_funders=max_peer_funders,
        include_network_graph=include_network_graph
    )

    return analyzer.analyze(input_data)
