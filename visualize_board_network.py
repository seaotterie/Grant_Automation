#!/usr/bin/env python3
"""
Board Network Visualization
Creates ASCII and text-based visualizations of the board network.
"""

import asyncio
from src.processors.analysis.board_network_analyzer import BoardNetworkAnalyzerProcessor
from src.core.data_models import ProcessorConfig, WorkflowConfig

def create_ascii_network_diagram(data):
    """Create an ASCII representation of the network."""
    
    print("\n" + "="*80)
    print("BOARD MEMBER NETWORK VISUALIZATION")
    print("="*80)
    
    # Extract organizations and connections
    organizations = data['organizations']
    connections = data.get('connections', [])
    influence_data = data.get('influence_scores', {}).get('individual_influence', {})
    
    print("\nNETWORK STRUCTURE:")
    print("-" * 40)
    
    # Show organizations as nodes
    for i, org in enumerate(organizations):
        print(f"\n[{i+1}] {org['name']}")
        print(f"    EIN: {org['ein']}")
        print(f"    State: {org.get('state', 'N/A')}")
        print(f"    NTEE: {org.get('ntee_code', 'N/A')}")
        print(f"    Board Members: {len(org.get('board_members', []))}")
        
        # List board members
        members = org.get('board_members', []) + [p.get('name', '') for p in org.get('key_personnel', []) if isinstance(p, dict) and p.get('name')]
        unique_members = list(set(members))
        for member in unique_members[:5]:  # Show first 5
            influence_score = influence_data.get(member, {}).get('total_influence_score', 0)
            star = " *" if influence_score > 3 else ""
            print(f"      - {member}{star}")
        if len(unique_members) > 5:
            print(f"      - ... and {len(unique_members) - 5} more")
    
    print("\nNETWORK CONNECTIONS:")
    print("-" * 40)
    
    if connections:
        for i, conn in enumerate(connections, 1):
            print(f"\n{i}. {conn['org1_name']}")
            print("   |")
            print("   +-- Shared Members:")
            for member in conn['shared_members'][:3]:  # Show first 3
                print(f"   |   - {member}")
            if len(conn['shared_members']) > 3:
                print(f"   |   - ... and {len(conn['shared_members']) - 3} more")
            print("   |")
            print(f"   +-- {conn['org2_name']}")
            print(f"       Connection Strength: {conn['connection_strength']}")
    else:
        print("No direct connections found in this network.")
    
    print("\nTOP INFLUENCERS:")
    print("-" * 40)
    
    # Sort by influence score
    sorted_influence = sorted(influence_data.items(), key=lambda x: x[1]['total_influence_score'], reverse=True)
    
    for i, (name, info) in enumerate(sorted_influence[:5], 1):
        orgs = info['organizations'][:2]  # Show first 2 orgs
        org_display = ', '.join(orgs)
        if len(info['organizations']) > 2:
            org_display += f" + {len(info['organizations']) - 2} more"
            
        print(f"{i}. {name}")
        print(f"   Influence Score: {info['total_influence_score']:.1f}")
        print(f"   Board Positions: {info['board_positions']}")
        print(f"   Organizations: {org_display}")
        print()

def create_network_graph_description(data):
    """Describe what the network would look like as a graph."""
    
    print("\n" + "="*80)
    print("NETWORK GRAPH DESCRIPTION")
    print("="*80)
    
    network_stats = data.get('network_analysis', {}).get('network_graph_stats', {})
    
    print(f"""
WHAT THE NETWORK GRAPH WOULD SHOW:

NODES (Organizations): {network_stats.get('nodes', 0)} circles
   Each circle represents an organization, sized by number of board members
   Colors could represent NTEE codes (E32=blue for health, F30=green for food)

EDGES (Connections): {network_stats.get('edges', 0)} lines  
   Lines connect organizations that share board members
   Thickness represents connection strength (number of shared members)

NETWORK DENSITY: {network_stats.get('density', 0):.3f}
   (0.0 = no connections, 1.0 = everyone connected to everyone)
   
CENTRAL NODES: Organizations with highest betweenness centrality
   These act as "bridges" connecting different parts of the network
   
BOARD MEMBER LABELS: Names floating near connected organizations
   Shared members would appear as labels on the connecting lines

VISUAL INSIGHTS:
   - Clustered organizations suggest collaboration opportunities
   - Bridge organizations are key strategic partners
   - Isolated nodes may need relationship building
   - High-influence members could be approached for introductions
""")

async def visualize_board_network():
    """Run the board network analysis and create visualizations."""
    
    print("GENERATING BOARD NETWORK VISUALIZATIONS...")
    
    # Create processor and run analysis
    processor = BoardNetworkAnalyzerProcessor()
    config = ProcessorConfig(
        workflow_id='network_viz',
        processor_name='board_network_analyzer',
        workflow_config=WorkflowConfig(
            workflow_id='network_viz',
            target_ein='123456789',
            max_results=5
        )
    )
    
    result = await processor.execute(config, workflow_state=None)
    
    if result.success:
        data = result.data
        
        # Create ASCII visualization
        create_ascii_network_diagram(data)
        
        # Describe the network graph
        create_network_graph_description(data)
        
        print("\n" + "="*80)
        print("STRATEGIC INTELLIGENCE SUMMARY")
        print("="*80)
        
        insights = data.get('insights', {})
        findings = insights.get('key_findings', [])
        recommendations = insights.get('strategic_recommendations', [])
        
        if findings:
            print("\nKEY FINDINGS:")
            for finding in findings:
                print(f"   - {finding}")
        
        if recommendations:
            print("\nSTRATEGIC RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"   - {rec}")
        
        print(f"\nBOTTOM LINE:")
        print(f"   This network analysis reveals relationship patterns that can guide")
        print(f"   grant strategy, partnership development, and stakeholder engagement.")
        
    else:
        print("Visualization failed:")
        for error in result.errors:
            print(f"   {error}")

if __name__ == "__main__":
    asyncio.run(visualize_board_network())