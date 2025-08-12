#!/usr/bin/env python3
"""
Simple Board Network Analysis Test
Tests the board network analysis with standalone data.
"""

import asyncio
from src.processors.analysis.board_network_analyzer import BoardNetworkAnalyzerProcessor
from src.core.data_models import ProcessorConfig, WorkflowConfig

async def test_board_network_simple():
    """Test board network analysis with built-in test data."""
    
    print("TESTING BOARD MEMBER NETWORK ANALYSIS (Standalone)")
    print("="*60)
    
    # Create the processor
    processor = BoardNetworkAnalyzerProcessor()
    
    # Create a simple config
    config = ProcessorConfig(
        workflow_id='test_board_network',
        processor_name='board_network_analyzer',
        workflow_config=WorkflowConfig(
            workflow_id='test_board_network',
            target_ein='123456789',
            max_results=5
        )
    )
    
    # Execute the processor (it will use test data since no workflow state)
    result = await processor.execute(config, workflow_state=None)
    
    if result.success:
        print("\nBOARD NETWORK ANALYSIS RESULTS:")
        print("="*60)
        
        data = result.data
        
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
        
        # Show connections
        connections = data.get('connections', [])
        if connections:
            print(f"\nORGANIZATIONAL CONNECTIONS:")
            for i, conn in enumerate(connections, 1):
                print(f"   {i}. {conn['org1_name']} <-> {conn['org2_name']}")
                print(f"      Shared members: {', '.join(conn['shared_members'])}")
                print(f"      Connection strength: {conn['connection_strength']}")
                print()
        
        # Show influence scores
        influence_data = data.get('influence_scores', {})
        top_influencers = influence_data.get('top_influencers', {})
        if top_influencers:
            print(f"TOP INFLUENTIAL BOARD MEMBERS:")
            for i, (name, info) in enumerate(top_influencers.items(), 1):
                print(f"   {i}. {name}")
                print(f"      Board positions: {info['board_positions']}")
                print(f"      Organizations: {', '.join(info['organizations'])}")
                print(f"      Influence score: {info['total_influence_score']:.2f}")
                print()
        
        # Show insights
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
        
        print("SUCCESS: Board network analysis working with test data!")
        
    else:
        print("FAILED: Board network analysis failed")
        print(f"Errors: {result.errors}")

if __name__ == "__main__":
    asyncio.run(test_board_network_simple())