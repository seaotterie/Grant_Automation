#!/usr/bin/env python3
"""
Test Interactive Network Visualization
Demonstrates the interactive spider web network graphs.
"""

import asyncio
from src.processors.analysis.board_network_analyzer import BoardNetworkAnalyzerProcessor
from src.processors.visualization.network_visualizer import InteractiveNetworkVisualizer
from src.core.data_models import ProcessorConfig, WorkflowConfig

async def test_interactive_visualization():
    """Test the interactive network visualization system."""
    
    print("TESTING INTERACTIVE NETWORK VISUALIZATION")
    print("="*60)
    
    # 1. Generate network analysis data
    print("Step 1: Generating board network analysis data...")
    processor = BoardNetworkAnalyzerProcessor()
    config = ProcessorConfig(
        workflow_id='interactive_viz_test',
        processor_name='board_network_analyzer',
        workflow_config=WorkflowConfig(
            workflow_id='interactive_viz_test',
            target_ein='123456789',
            max_results=5
        )
    )
    
    result = await processor.execute(config, workflow_state=None)
    
    if not result.success:
        print("Failed to generate network data:")
        for error in result.errors:
            print(f"  - {error}")
        return
    
    network_data = result.data
    print(f"SUCCESS: Generated network data with {len(network_data['organizations'])} organizations")
    print(f"SUCCESS: Found {network_data['network_analysis']['network_connections']} connections")
    
    # 2. Create interactive visualizations
    print("\nStep 2: Creating interactive visualizations...")
    visualizer = InteractiveNetworkVisualizer()
    
    # Create main network graph
    main_network_fig = visualizer.create_interactive_network(
        network_data, 
        "Catalynx Board Member Network"
    )
    
    # Create influence network  
    influence_fig = visualizer.create_influence_network(network_data)
    
    print("SUCCESS: Created interactive network graphs")
    
    # 3. Export to HTML files
    print("\nStep 3: Exporting interactive HTML files...")
    exported_files = visualizer.export_visualizations(network_data, "catalynx_demo")
    
    for file in exported_files:
        print(f"SUCCESS: Exported: {file}")
    
    # 4. Display summary
    print(f"\nINTERACTIVE NETWORK VISUALIZATION COMPLETE!")
    print("="*60)
    
    network_stats = network_data['network_analysis']
    print(f"Network Statistics:")
    print(f"  - Organizations: {len(network_data['organizations'])}")
    print(f"  - Board Members: {network_stats['total_board_members']}")
    print(f"  - Unique Individuals: {network_stats['unique_individuals']}")
    print(f"  - Network Connections: {network_stats['network_connections']}")
    print(f"  - Network Density: {network_stats['network_graph_stats']['density']:.3f}")
    
    print(f"\nVisualization Features:")
    print(f"  - Interactive spider web network graph")
    print(f"  - Color-coded by NTEE codes")
    print(f"  - Node size reflects influence/centrality")
    print(f"  - Hover for detailed organization info")
    print(f"  - Draggable nodes for exploration")
    print(f"  - Board member labels on connections")
    print(f"  - Zoom and pan capabilities")
    
    print(f"\nGenerated Files:")
    for file in exported_files:
        print(f"  - {file} - Open in web browser")
    
    print(f"\nTo view the interactive networks:")
    print(f"  1. Open any web browser")
    print(f"  2. Open the HTML files above") 
    print(f"  3. Interact with the network:")
    print(f"     - Drag nodes around")
    print(f"     - Hover over organizations for details")
    print(f"     - Zoom in/out with mouse wheel")
    print(f"     - Pan by clicking and dragging empty space")
    
    print(f"\nThe visualizations show:")
    print(f"  - Board member connection patterns")
    print(f"  - Organizational relationship strength")
    print(f"  - Key influencers and bridge organizations")
    print(f"  - Strategic partnership opportunities")

if __name__ == "__main__":
    asyncio.run(test_interactive_visualization())