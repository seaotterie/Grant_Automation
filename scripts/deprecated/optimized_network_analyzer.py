#!/usr/bin/env python3
"""
Optimized Board Network Analyzer
High-performance implementation using normalized database structure
"""

import sqlite3
import time
import networkx as nx
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class NetworkAnalysisResult:
    """Result of network analysis with performance metrics"""
    success: bool
    total_people: int
    total_organizations: int
    total_connections: int
    network_density: float
    largest_component_size: int
    analysis_time: float
    query_times: Dict[str, float]
    top_influencers: List[Dict[str, Any]]
    organization_metrics: Dict[str, Any]
    performance_notes: List[str]


class OptimizedNetworkAnalyzer:
    """High-performance network analyzer using normalized database structure"""

    def __init__(self, database_path: str):
        self.database_path = database_path

    def analyze_full_network(self, min_quality_score: int = 60) -> NetworkAnalysisResult:
        """
        Perform comprehensive network analysis with performance optimization

        Args:
            min_quality_score: Minimum data quality score to include records

        Returns:
            NetworkAnalysisResult with analysis and performance data
        """
        start_time = time.time()
        query_times = {}
        performance_notes = []

        try:
            with sqlite3.connect(self.database_path) as conn:
                # Enable query optimization
                conn.execute("PRAGMA optimize")
                conn.execute("PRAGMA cache_size = 20000")  # 20MB cache

                # Step 1: Load people and roles efficiently
                people_time = time.time()
                people_df, roles_df = self._load_people_and_roles(conn, min_quality_score)
                query_times['load_people_roles'] = time.time() - people_time

                if len(people_df) == 0:
                    return self._create_empty_result(query_times, start_time)

                # Step 2: Build network graph efficiently
                graph_time = time.time()
                graph, connections_df = self._build_optimized_network_graph(people_df, roles_df)
                query_times['build_graph'] = time.time() - graph_time

                # Step 3: Calculate network metrics efficiently
                metrics_time = time.time()
                org_metrics, person_metrics = self._calculate_optimized_metrics(
                    graph, people_df, roles_df, connections_df
                )
                query_times['calculate_metrics'] = time.time() - metrics_time

                # Step 4: Store results back to database
                storage_time = time.time()
                self._store_network_results(conn, org_metrics, person_metrics)
                query_times['store_results'] = time.time() - storage_time

                # Step 5: Generate analysis summary
                summary_time = time.time()
                top_influencers = self._get_top_influencers(person_metrics)
                query_times['generate_summary'] = time.time() - summary_time

                # Performance analysis
                total_time = time.time() - start_time
                performance_notes.extend([
                    f"Processed {len(people_df)} people in {total_time:.3f}s",
                    f"Graph density: {nx.density(graph):.4f}",
                    f"Largest component: {max(len(c) for c in nx.connected_components(graph)) if graph.number_of_nodes() > 0 else 0} nodes"
                ])

                return NetworkAnalysisResult(
                    success=True,
                    total_people=len(people_df),
                    total_organizations=len(roles_df['organization_ein'].unique()),
                    total_connections=graph.number_of_edges(),
                    network_density=nx.density(graph),
                    largest_component_size=max(len(c) for c in nx.connected_components(graph)) if graph.number_of_nodes() > 0 else 0,
                    analysis_time=total_time,
                    query_times=query_times,
                    top_influencers=top_influencers,
                    organization_metrics=org_metrics,
                    performance_notes=performance_notes
                )

        except Exception as e:
            logger.error(f"Network analysis failed: {e}", exc_info=True)
            return NetworkAnalysisResult(
                success=False,
                total_people=0,
                total_organizations=0,
                total_connections=0,
                network_density=0.0,
                largest_component_size=0,
                analysis_time=time.time() - start_time,
                query_times=query_times,
                top_influencers=[],
                organization_metrics={},
                performance_notes=[f"Analysis failed: {str(e)}"]
            )

    def _load_people_and_roles(self, conn: sqlite3.Connection, min_quality_score: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load people and roles data efficiently using optimized queries"""

        # Load people with quality filtering
        people_query = """
            SELECT id, normalized_name, original_name, first_name, last_name,
                   data_quality_score, source_count, created_at
            FROM people
            WHERE data_quality_score >= ?
            ORDER BY data_quality_score DESC, source_count DESC
        """
        people_df = pd.read_sql_query(people_query, conn, params=(min_quality_score,))

        if len(people_df) == 0:
            return people_df, pd.DataFrame()

        # Load current roles for these people
        people_ids = people_df['id'].tolist()
        placeholders = ','.join('?' * len(people_ids))

        roles_query = f"""
            SELECT person_id, organization_ein, organization_name, title,
                   position_type, is_current, data_source, quality_score,
                   start_date, end_date
            FROM organization_roles
            WHERE person_id IN ({placeholders})
              AND is_current = TRUE
              AND quality_score >= ?
            ORDER BY person_id, quality_score DESC
        """

        roles_df = pd.read_sql_query(
            roles_query, conn,
            params=people_ids + [min_quality_score]
        )

        return people_df, roles_df

    def _build_optimized_network_graph(self, people_df: pd.DataFrame,
                                     roles_df: pd.DataFrame) -> Tuple[nx.Graph, pd.DataFrame]:
        """Build network graph efficiently using pandas operations"""

        # Create organization pairs for each person
        connections_list = []

        # Group roles by person for efficient processing
        roles_by_person = roles_df.groupby('person_id')

        for person_id, person_roles in roles_by_person:
            if len(person_roles) > 1:  # Person serves on multiple boards
                orgs = person_roles[['organization_ein', 'organization_name']].drop_duplicates()
                org_list = orgs.values.tolist()

                # Create all pairs of organizations for this person
                for i in range(len(org_list)):
                    for j in range(i + 1, len(org_list)):
                        org1_ein, org1_name = org_list[i]
                        org2_ein, org2_name = org_list[j]

                        # Ensure consistent ordering
                        if org1_ein > org2_ein:
                            org1_ein, org1_name, org2_ein, org2_name = org2_ein, org2_name, org1_ein, org1_name

                        connections_list.append({
                            'person_id': person_id,
                            'person_name': people_df[people_df['id'] == person_id]['normalized_name'].iloc[0],
                            'org1_ein': org1_ein,
                            'org1_name': org1_name,
                            'org2_ein': org2_ein,
                            'org2_name': org2_name,
                            'connection_strength': 1.0
                        })

        # Create connections DataFrame
        if connections_list:
            connections_df = pd.DataFrame(connections_list)

            # Group by organization pairs to calculate total connection strength
            org_connections = connections_df.groupby(['org1_ein', 'org1_name', 'org2_ein', 'org2_name']).agg({
                'connection_strength': 'sum',
                'person_name': lambda x: list(x),
                'person_id': 'count'
            }).reset_index()

            # Build NetworkX graph
            graph = nx.Graph()

            # Add nodes (organizations)
            unique_orgs = set()
            for _, row in org_connections.iterrows():
                unique_orgs.add((row['org1_ein'], row['org1_name']))
                unique_orgs.add((row['org2_ein'], row['org2_name']))

            for ein, name in unique_orgs:
                graph.add_node(ein, name=name)

            # Add edges (connections)
            for _, row in org_connections.iterrows():
                graph.add_edge(
                    row['org1_ein'], row['org2_ein'],
                    weight=row['connection_strength'],
                    shared_members=row['person_name'],
                    member_count=row['person_id']
                )

        else:
            connections_df = pd.DataFrame()
            graph = nx.Graph()

        return graph, connections_df

    def _calculate_optimized_metrics(self, graph: nx.Graph, people_df: pd.DataFrame,
                                   roles_df: pd.DataFrame, connections_df: pd.DataFrame) -> Tuple[Dict, Dict]:
        """Calculate network metrics efficiently"""

        org_metrics = {}
        person_metrics = {}

        if graph.number_of_nodes() == 0:
            return org_metrics, person_metrics

        # Calculate centrality measures for organizations
        degree_centrality = nx.degree_centrality(graph)
        betweenness_centrality = nx.betweenness_centrality(graph)
        closeness_centrality = nx.closeness_centrality(graph)

        try:
            eigenvector_centrality = nx.eigenvector_centrality(graph, max_iter=1000)
        except nx.PowerIterationFailedConvergence:
            eigenvector_centrality = {node: 0.0 for node in graph.nodes()}

        # Prepare organization metrics
        for node in graph.nodes():
            org_metrics[node] = {
                'organization_ein': node,
                'organization_name': graph.nodes[node]['name'],
                'degree_centrality': degree_centrality.get(node, 0.0),
                'betweenness_centrality': betweenness_centrality.get(node, 0.0),
                'closeness_centrality': closeness_centrality.get(node, 0.0),
                'eigenvector_centrality': eigenvector_centrality.get(node, 0.0),
                'total_connections': graph.degree(node),
                'network_influence_score': (
                    degree_centrality.get(node, 0.0) * 0.3 +
                    betweenness_centrality.get(node, 0.0) * 0.4 +
                    eigenvector_centrality.get(node, 0.0) * 0.3
                )
            }

        # Calculate person influence metrics efficiently using pandas
        person_board_counts = roles_df[roles_df['position_type'] == 'board'].groupby('person_id').agg({
            'organization_ein': 'count',
            'organization_name': 'count'
        }).rename(columns={'organization_ein': 'board_positions', 'organization_name': 'total_organizations'})

        person_executive_counts = roles_df[roles_df['position_type'] == 'executive'].groupby('person_id').size()

        # Merge with people data
        person_stats = people_df.set_index('id').join([
            person_board_counts,
            person_executive_counts.rename('executive_positions')
        ], how='left').fillna(0)

        # Calculate network reach for each person
        if not connections_df.empty:
            person_network_reach = connections_df.groupby('person_id').agg({
                'org1_ein': 'nunique',
                'org2_ein': 'nunique'
            })
            person_network_reach['total_network_reach'] = (
                person_network_reach['org1_ein'] + person_network_reach['org2_ein']
            )
            person_stats = person_stats.join(person_network_reach['total_network_reach'], how='left').fillna(0)
        else:
            person_stats['total_network_reach'] = 0

        # Calculate influence scores
        person_stats['position_influence_score'] = (
            person_stats['board_positions'] * 1.0 +
            person_stats['executive_positions'] * 2.0
        )

        person_stats['network_influence_score'] = person_stats['total_network_reach'] * 0.5

        person_stats['total_influence_score'] = (
            person_stats['position_influence_score'] +
            person_stats['network_influence_score']
        )

        # Convert to dictionary
        for person_id, row in person_stats.iterrows():
            person_metrics[person_id] = {
                'person_id': person_id,
                'person_name': row['normalized_name'],
                'total_board_positions': int(row['board_positions']),
                'executive_positions': int(row['executive_positions']),
                'total_organizations': int(row['total_organizations']),
                'network_reach': int(row['total_network_reach']),
                'position_influence_score': row['position_influence_score'],
                'network_influence_score': row['network_influence_score'],
                'total_influence_score': row['total_influence_score'],
                'data_quality_score': row['data_quality_score']
            }

        return org_metrics, person_metrics

    def _store_network_results(self, conn: sqlite3.Connection,
                              org_metrics: Dict, person_metrics: Dict) -> None:
        """Store analysis results back to database efficiently"""

        # Clear existing metrics
        conn.execute("DELETE FROM organization_network_metrics")
        conn.execute("DELETE FROM person_influence_metrics")

        # Insert organization metrics
        if org_metrics:
            org_insert_data = []
            for metrics in org_metrics.values():
                org_insert_data.append((
                    metrics['organization_ein'],
                    metrics['organization_name'],
                    metrics['degree_centrality'],
                    metrics['betweenness_centrality'],
                    metrics['closeness_centrality'],
                    metrics['eigenvector_centrality'],
                    metrics['total_connections'],
                    metrics['network_influence_score'],
                    datetime.now().isoformat(),
                    '2.0.0'
                ))

            conn.executemany("""
                INSERT INTO organization_network_metrics
                (organization_ein, organization_name, degree_centrality, betweenness_centrality,
                 closeness_centrality, eigenvector_centrality, total_connections,
                 network_influence_score, analysis_date, algorithm_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, org_insert_data)

        # Insert person metrics
        if person_metrics:
            person_insert_data = []
            for metrics in person_metrics.values():
                person_insert_data.append((
                    metrics['person_id'],
                    metrics['person_name'],
                    metrics['total_board_positions'],
                    metrics['executive_positions'],
                    metrics['total_organizations'],
                    metrics['network_reach'],
                    metrics['position_influence_score'],
                    metrics['network_influence_score'],
                    metrics['total_influence_score'],
                    datetime.now().isoformat(),
                    '2.0.0'
                ))

            conn.executemany("""
                INSERT INTO person_influence_metrics
                (person_id, person_name, total_board_positions, executive_positions,
                 total_organizations, network_reach, position_influence_score,
                 network_influence_score, total_influence_score, analysis_date, algorithm_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, person_insert_data)

        conn.commit()

    def _get_top_influencers(self, person_metrics: Dict, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top influencers sorted by total influence score"""
        sorted_people = sorted(
            person_metrics.values(),
            key=lambda x: x['total_influence_score'],
            reverse=True
        )
        return sorted_people[:limit]

    def _create_empty_result(self, query_times: Dict[str, float], start_time: float) -> NetworkAnalysisResult:
        """Create empty result when no data is available"""
        return NetworkAnalysisResult(
            success=True,
            total_people=0,
            total_organizations=0,
            total_connections=0,
            network_density=0.0,
            largest_component_size=0,
            analysis_time=time.time() - start_time,
            query_times=query_times,
            top_influencers=[],
            organization_metrics={},
            performance_notes=["No qualified data found for network analysis"]
        )

    def get_organization_connections(self, organization_ein: str) -> Dict[str, Any]:
        """Get detailed connection information for a specific organization"""
        with sqlite3.connect(self.database_path) as conn:
            # Get direct connections
            query = """
                SELECT DISTINCT
                    CASE WHEN bc.org1_ein = ? THEN bc.org2_ein ELSE bc.org1_ein END as connected_ein,
                    CASE WHEN bc.org1_ein = ? THEN bc.org2_name ELSE bc.org1_name END as connected_name,
                    p.normalized_name as shared_member,
                    or1.title as member_title,
                    bc.connection_strength
                FROM board_connections bc
                JOIN people p ON bc.person_id = p.id
                JOIN organization_roles or1 ON p.id = or1.person_id AND or1.organization_ein = ?
                WHERE (bc.org1_ein = ? OR bc.org2_ein = ?)
                  AND bc.is_current_connection = TRUE
                ORDER BY bc.connection_strength DESC, p.normalized_name
            """

            results = conn.execute(query, (organization_ein, organization_ein,
                                         organization_ein, organization_ein, organization_ein)).fetchall()

            connections = {}
            for connected_ein, connected_name, shared_member, member_title, strength in results:
                if connected_ein not in connections:
                    connections[connected_ein] = {
                        'organization_name': connected_name,
                        'total_strength': 0,
                        'shared_members': []
                    }

                connections[connected_ein]['total_strength'] += strength
                connections[connected_ein]['shared_members'].append({
                    'name': shared_member,
                    'title': member_title
                })

            return connections

    def analyze_person_network(self, person_id: int) -> Dict[str, Any]:
        """Analyze network position and influence for a specific person"""
        with sqlite3.connect(self.database_path) as conn:
            # Get person's roles and connections
            query = """
                SELECT
                    p.normalized_name,
                    p.data_quality_score,
                    COUNT(DISTINCT or_roles.organization_ein) as total_organizations,
                    COUNT(DISTINCT bc.org1_ein || ',' || bc.org2_ein) as unique_connections,
                    pim.total_influence_score,
                    pim.influence_rank
                FROM people p
                LEFT JOIN organization_roles or_roles ON p.id = or_roles.person_id AND or_roles.is_current = TRUE
                LEFT JOIN board_connections bc ON p.id = bc.person_id AND bc.is_current_connection = TRUE
                LEFT JOIN person_influence_metrics pim ON p.id = pim.person_id
                WHERE p.id = ?
                GROUP BY p.id
            """

            result = conn.execute(query, (person_id,)).fetchone()

            if result:
                return {
                    'name': result[0],
                    'data_quality_score': result[1],
                    'total_organizations': result[2],
                    'unique_connections': result[3],
                    'influence_score': result[4] or 0,
                    'influence_rank': result[5] or 0
                }

            return {}


# Performance testing and benchmarking
class NetworkAnalysisPerformanceTester:
    """Test and benchmark network analysis performance"""

    def __init__(self, database_path: str):
        self.analyzer = OptimizedNetworkAnalyzer(database_path)

    def run_performance_test(self) -> Dict[str, Any]:
        """Run comprehensive performance test"""
        results = {}

        # Test different quality thresholds
        quality_thresholds = [30, 50, 70, 90]

        for threshold in quality_thresholds:
            print(f"Testing with quality threshold: {threshold}")
            result = self.analyzer.analyze_full_network(min_quality_score=threshold)

            results[f"quality_{threshold}"] = {
                'success': result.success,
                'total_people': result.total_people,
                'total_organizations': result.total_organizations,
                'analysis_time': result.analysis_time,
                'query_times': result.query_times,
                'performance_notes': result.performance_notes
            }

        return results


# Usage example
if __name__ == "__main__":
    analyzer = OptimizedNetworkAnalyzer("data/catalynx.db")
    result = analyzer.analyze_full_network(min_quality_score=60)

    print(f"Analysis {'succeeded' if result.success else 'failed'}")
    print(f"People: {result.total_people}")
    print(f"Organizations: {result.total_organizations}")
    print(f"Connections: {result.total_connections}")
    print(f"Density: {result.network_density:.4f}")
    print(f"Time: {result.analysis_time:.3f}s")

    print("\nQuery Performance:")
    for operation, time_taken in result.query_times.items():
        print(f"  {operation}: {time_taken:.3f}s")

    if result.top_influencers:
        print(f"\nTop Influencers:")
        for i, person in enumerate(result.top_influencers[:5], 1):
            print(f"  {i}. {person['person_name']} (Score: {person['total_influence_score']:.2f})")