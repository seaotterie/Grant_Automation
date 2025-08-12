#!/usr/bin/env python3
"""
Test Board Member Network Analysis
Demonstrates the board member network analysis functionality.
"""

import asyncio
import json
from datetime import datetime
from src.core.workflow_engine import WorkflowEngine
from src.core.data_models import WorkflowConfig

async def test_board_network_analysis():
    """Test the board member network analysis with real workflow data."""
    
    print("TESTING BOARD MEMBER NETWORK ANALYSIS")
    print("="*60)
    
    # Create workflow with board network analysis
    engine = WorkflowEngine()
    config = WorkflowConfig(
        workflow_id=f'board_network_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        target_ein='541669652',
        max_results=5,
        states=['VA'],
        ntee_codes=['E21','E30','E32','E60','E86','F30','F32'],
        processors=['ein_lookup', 'bmf_filter', 'propublica_fetch', 'financial_scorer', 'board_network_analyzer']
    )
    
    # Execute workflow
    print("Running workflow with board network analysis...")
    state = await engine.run_workflow(config)
    
    # Check if board network analysis completed
    if state.has_processor_succeeded('board_network_analyzer'):
        result = state.get_processor_result('board_network_analyzer')
        data = result.data
        
        print("\nBOARD NETWORK ANALYSIS RESULTS:")
        print("="*60)
        
        # Network statistics
        network_analysis = data.get('network_analysis', {})
        print(f"Network Statistics:")
        print(f"   Total board member positions: {network_analysis.get('total_board_members', 0)}")
        print(f"   Unique individuals: {network_analysis.get('unique_individuals', 0)}")
        print(f"   Network connections: {network_analysis.get('network_connections', 0)}")
        
        graph_stats = network_analysis.get('network_graph_stats', {})
        print(f"   Network nodes: {graph_stats.get('nodes', 0)}")
        print(f"   Network edges: {graph_stats.get('edges', 0)}")
        print(f"   Network density: {graph_stats.get('density', 0):.3f}")
        
        # Connections found
        connections = data.get('connections', [])
        if connections:
            print(f"\nORGANIZATIONAL CONNECTIONS:")
            for i, conn in enumerate(connections[:5], 1):  # Show top 5
                print(f"   {i}. {conn['org1_name']} <-> {conn['org2_name']}")
                print(f"      Shared members: {', '.join(conn['shared_members'])}")
                print(f"      Connection strength: {conn['connection_strength']}")
                print()
        else:
            print("\nNo direct board connections found in this dataset")
        
        # Influence scores
        influence_data = data.get('influence_scores', {})
        top_influencers = influence_data.get('top_influencers', {})
        if top_influencers:
            print(f"TOP INFLUENTIAL BOARD MEMBERS:")
            for i, (name, info) in enumerate(list(top_influencers.items())[:5], 1):
                print(f"   {i}. {name}")
                print(f"      Board positions: {info['board_positions']}")
                print(f"      Organizations: {', '.join(info['organizations'][:2])}{'...' if len(info['organizations']) > 2 else ''}")
                print(f"      Influence score: {info['total_influence_score']:.2f}")
                print()
        
        # Network metrics for organizations
        network_metrics = data.get('network_metrics', {})
        org_metrics = network_metrics.get('organization_metrics', {})
        if org_metrics:
            print(f"ORGANIZATION NETWORK METRICS:")
            # Sort by betweenness centrality (bridge organizations)
            sorted_orgs = sorted(org_metrics.items(), key=lambda x: x[1].get('betweenness_centrality', 0), reverse=True)
            for ein, metrics in sorted_orgs[:3]:  # Top 3
                print(f"   - {metrics['organization_name']}")
                print(f"     Betweenness centrality: {metrics['betweenness_centrality']:.3f}")
                print(f"     Degree centrality: {metrics['degree_centrality']:.3f}")
                print(f"     Total connections: {metrics['total_connections']}")
                print()
        
        # Strategic insights
        insights = data.get('insights', {})
        key_findings = insights.get('key_findings', [])
        if key_findings:
            print(f"KEY INSIGHTS:")
            for finding in key_findings:
                print(f"   - {finding}")
            print()
        
        recommendations = insights.get('strategic_recommendations', [])
        if recommendations:
            print(f"STRATEGIC RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"   - {rec}")
            print()
        
        # Export network data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        network_file = f"board_network_analysis_{timestamp}.json"
        
        with open(network_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"Network analysis exported to: {network_file}")
        
    else:
        print("Board network analysis failed or not completed")
        if state.processor_results.get('board_network_analyzer'):
            result = state.processor_results['board_network_analyzer']
            print(f"Errors: {result.errors}")

if __name__ == "__main__":
    asyncio.run(test_board_network_analysis())