#!/usr/bin/env python3
"""
Interactive Network Visualizer
Creates beautiful interactive network graphs using Plotly.

This module:
1. Takes board network analysis data
2. Creates interactive spider web visualizations
3. Generates hoverable, zoomable network graphs
4. Exports to HTML for sharing and presentations
"""

import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
import colorsys
from datetime import datetime


class InteractiveNetworkVisualizer:
    """Creates interactive network visualizations from board member data."""
    
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
        self.ntee_colors = {
            'E21': '#FF6B6B',  # Health Care - Red
            'E30': '#4ECDC4',  # Ambulatory Health - Teal  
            'E32': '#45B7D1',  # Community Health - Blue
            'E60': '#96CEB4',  # Health Support - Green
            'E86': '#FFEAA7',  # Patient Services - Yellow
            'F30': '#DDA0DD',  # Food Services - Purple
            'F32': '#98D8C8',  # Nutrition - Mint
            'T31': '#F7DC6F',  # Foundations - Gold
            'P81': '#BB8FCE',  # Health General - Lavender
            'default': '#BDC3C7'  # Default gray
        }
    
    def create_interactive_network(self, network_data: Dict[str, Any], title: str = "Board Member Network") -> go.Figure:
        """Create an interactive network visualization."""
        
        # Extract data
        organizations = network_data.get('organizations', [])
        connections = network_data.get('connections', [])
        influence_data = network_data.get('influence_scores', {}).get('individual_influence', {})
        network_metrics = network_data.get('network_metrics', {}).get('organization_metrics', {})
        
        # Build NetworkX graph for layout calculation
        G = self._build_networkx_graph(organizations, connections)
        
        # Calculate layout positions
        pos = nx.spring_layout(G, k=3, iterations=50, seed=42)
        
        # Create the figure
        fig = go.Figure()
        
        # Add edges (connections between organizations)
        self._add_edges(fig, G, pos, connections)
        
        # Add nodes (organizations)
        self._add_organization_nodes(fig, organizations, pos, network_metrics, influence_data)
        
        # Add board member labels
        self._add_board_member_labels(fig, connections, pos, G)
        
        # Configure layout
        self._configure_layout(fig, title, len(organizations))
        
        return fig
    
    def _build_networkx_graph(self, organizations: List[Dict], connections: List[Dict]) -> nx.Graph:
        """Build NetworkX graph for layout calculation."""
        G = nx.Graph()
        
        # Add organization nodes
        for org in organizations:
            G.add_node(org['ein'], 
                      name=org['name'],
                      ntee=org.get('ntee_code', ''),
                      state=org.get('state', ''))
        
        # Add edges for connections
        for conn in connections:
            if conn['org1_ein'] != conn['org2_ein']:  # Avoid self-loops
                G.add_edge(conn['org1_ein'], conn['org2_ein'], 
                          weight=conn['connection_strength'],
                          shared_members=conn['shared_members'])
        
        return G
    
    def _add_edges(self, fig: go.Figure, G: nx.Graph, pos: Dict, connections: List[Dict]):
        """Add connection edges to the visualization."""
        
        edge_x = []
        edge_y = []
        edge_info = []
        
        for conn in connections:
            org1_ein = conn['org1_ein']
            org2_ein = conn['org2_ein']
            
            if org1_ein != org2_ein and org1_ein in pos and org2_ein in pos:
                x0, y0 = pos[org1_ein]
                x1, y1 = pos[org2_ein]
                
                # Add line coordinates
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                
                # Create hover info for this edge
                shared_members = ', '.join(conn['shared_members'][:3])
                if len(conn['shared_members']) > 3:
                    shared_members += f' + {len(conn["shared_members"]) - 3} more'
                
                edge_info.append(f"Connection: {conn['org1_name']} ↔ {conn['org2_name']}<br>"
                               f"Shared Members: {shared_members}<br>"
                               f"Strength: {conn['connection_strength']}")
        
        # Add edge trace
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='rgba(125, 125, 125, 0.5)'),
            hoverinfo='none',
            mode='lines',
            name='Connections',
            showlegend=False
        ))
    
    def _add_organization_nodes(self, fig: go.Figure, organizations: List[Dict], 
                              pos: Dict, network_metrics: Dict, influence_data: Dict):
        """Add organization nodes to the visualization."""
        
        for org in organizations:
            ein = org['ein']
            if ein not in pos:
                continue
                
            x, y = pos[ein]
            
            # Get organization info
            name = org['name']
            ntee_code = org.get('ntee_code', '')
            state = org.get('state', '')
            board_count = len(org.get('board_members', []))
            
            # Get network metrics
            metrics = network_metrics.get(ein, {})
            centrality = metrics.get('betweenness_centrality', 0)
            connections_count = metrics.get('total_connections', 0)
            
            # Determine node size based on board members and centrality
            base_size = 20 + (board_count * 3)
            centrality_bonus = centrality * 30
            node_size = min(base_size + centrality_bonus, 60)
            
            # Get color based on NTEE code
            color = self.ntee_colors.get(ntee_code[:3], self.ntee_colors.get(ntee_code, self.ntee_colors['default']))
            
            # Create hover text
            hover_text = (f"<b>{name}</b><br>"
                         f"EIN: {ein}<br>"
                         f"State: {state}<br>"
                         f"NTEE Code: {ntee_code}<br>"
                         f"Board Members: {board_count}<br>"
                         f"Network Connections: {connections_count}<br>"
                         f"Centrality Score: {centrality:.3f}")
            
            # Add board members to hover
            board_members = org.get('board_members', [])
            if board_members:
                member_list = ', '.join(board_members[:5])
                if len(board_members) > 5:
                    member_list += f' + {len(board_members) - 5} more'
                hover_text += f"<br><br>Board Members:<br>{member_list}"
            
            # Add the node
            fig.add_trace(go.Scatter(
                x=[x], y=[y],
                mode='markers+text',
                marker=dict(
                    size=node_size,
                    color=color,
                    line=dict(width=2, color='white'),
                    opacity=0.8
                ),
                text=name.split()[0] if len(name) > 20 else name,  # Abbreviated name
                textposition="middle center",
                textfont=dict(size=min(12, max(8, int(node_size/4))), color='white', family='Arial Black'),
                hovertext=hover_text,
                hoverinfo='text',
                name=f"{name} ({ntee_code})",
                showlegend=False
            ))
    
    def _add_board_member_labels(self, fig: go.Figure, connections: List[Dict], 
                                pos: Dict, G: nx.Graph):
        """Add board member names as labels on connections."""
        
        for conn in connections:
            org1_ein = conn['org1_ein']
            org2_ein = conn['org2_ein']
            
            if org1_ein != org2_ein and org1_ein in pos and org2_ein in pos:
                # Calculate midpoint of connection
                x0, y0 = pos[org1_ein]
                x1, y1 = pos[org2_ein]
                mid_x = (x0 + x1) / 2
                mid_y = (y0 + y1) / 2
                
                # Get shared members (limit to top 2 for readability)
                shared_members = conn['shared_members'][:2]
                if len(conn['shared_members']) > 2:
                    label_text = f"{', '.join(shared_members)}<br>+{len(conn['shared_members']) - 2} more"
                else:
                    label_text = ', '.join(shared_members)
                
                # Add label
                fig.add_trace(go.Scatter(
                    x=[mid_x], y=[mid_y],
                    mode='text',
                    text=label_text,
                    textfont=dict(size=10, color='rgba(0, 0, 0, 0.7)'),
                    textposition="middle center",
                    hoverinfo='skip',
                    showlegend=False
                ))
    
    def _configure_layout(self, fig: go.Figure, title: str, num_orgs: int):
        """Configure the overall layout of the visualization."""
        
        fig.update_layout(
            title={
                'text': f"<b>{title}</b><br><sub>Interactive Spider Web Network • Hover for Details • Zoom & Pan Enabled</sub>",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            showlegend=False,
            hovermode='closest',
            margin=dict(b=60, l=40, r=40, t=100),
            # Enhanced navigation controls
            dragmode='pan',
            annotations=[
                dict(
                    text="🔍 NAVIGATION: Mouse wheel = Zoom in/out • Click+drag = Pan around • Hover nodes = Details • Double-click = Reset zoom",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=-0.08,
                    xanchor='center', yanchor='bottom',
                    font=dict(color='#2C3E50', size=13, family='Arial')
                ),
                dict(
                    text="🎯 LEGEND: Node size = Influence/Centrality • Colors = NTEE codes • Lines = Shared board members",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=-0.12,
                    xanchor='center', yanchor='bottom',
                    font=dict(color='#7F8C8D', size=12)
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='#FAFAFA',
            width=1200,
            height=900,
            # Add toolbar with zoom controls
            modebar=dict(
                orientation='h',
                bgcolor='rgba(255,255,255,0.8)',
                color='#2C3E50',
                activecolor='#E74C3C'
            )
        )
    
    def create_influence_network(self, network_data: Dict[str, Any]) -> go.Figure:
        """Create a network focused on individual influence scores with connections."""
        
        influence_data = network_data.get('influence_scores', {}).get('individual_influence', {})
        organizations = network_data.get('organizations', [])
        connections = network_data.get('connections', [])
        
        # Create influence-based visualization
        fig = go.Figure()
        
        # Sort by influence score
        sorted_influence = sorted(influence_data.items(), 
                                key=lambda x: x[1]['total_influence_score'], 
                                reverse=True)
        
        # Create positions for top influencers
        n_influencers = min(len(sorted_influence), 15)  # Top 15
        positions = {}
        
        # Use force-directed layout for better connection visualization
        for i, (name, info) in enumerate(sorted_influence[:n_influencers]):
            influence_score = info['total_influence_score']
            
            # Create more dynamic positioning
            if influence_score >= 8:  # Super influencers in center
                radius = 0.2
                angle = i * (2 * np.pi / max(1, sum(1 for _, data in sorted_influence[:n_influencers] if data['total_influence_score'] >= 8)))
            elif influence_score >= 3:  # Medium influence in middle ring
                radius = 0.6
                angle = i * (2 * np.pi / max(1, sum(1 for _, data in sorted_influence[:n_influencers] if 3 <= data['total_influence_score'] < 8)))
            else:  # Lower influence in outer ring
                radius = 1.0
                angle = i * (2 * np.pi / max(1, sum(1 for _, data in sorted_influence[:n_influencers] if data['total_influence_score'] < 3)))
            
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            positions[name] = (x, y)
        
        # Add connection lines between people who serve on same boards
        self._add_influence_connections(fig, sorted_influence[:n_influencers], positions, organizations)
        
        # Add person nodes
        for i, (name, info) in enumerate(sorted_influence[:n_influencers]):
            if name not in positions:
                continue
                
            x, y = positions[name]
            influence_score = info['total_influence_score']
            
            # Node size based on influence
            node_size = min(max(influence_score * 4, 15), 50)
            
            # Color based on number of board positions
            positions_count = info['board_positions']
            if positions_count >= 4:
                color = '#E74C3C'  # Red for super-connectors
            elif positions_count >= 2:
                color = '#F39C12'  # Orange for multi-board
            else:
                color = '#3498DB'  # Blue for single board
            
            hover_text = (f"<b>{name}</b><br>"
                         f"Influence Score: {influence_score:.1f}<br>"
                         f"Board Positions: {positions_count}<br>"
                         f"Organizations: {', '.join(info['organizations'][:3])}")
            if len(info['organizations']) > 3:
                hover_text += f" + {len(info['organizations']) - 3} more"
            
            # Format name for display (two lines if needed)
            name_parts = name.split()
            if len(name_parts) >= 2:
                display_name = f"{name_parts[0]}<br>{name_parts[1]}"
            else:
                display_name = name_parts[0] if name_parts else name
            
            fig.add_trace(go.Scatter(
                x=[x], y=[y],
                mode='markers+text',
                marker=dict(size=node_size, color=color, opacity=0.9,
                           line=dict(width=2, color='white')),
                text=display_name,
                textposition="bottom center",  # Position text outside and below the circle
                textfont=dict(size=11, color='black', family='Arial Bold'),
                hovertext=hover_text,
                hoverinfo='text',
                showlegend=False
            ))
        
        # Enhanced layout with navigation controls
        fig.update_layout(
            title={
                'text': "<b>Board Member Influence Network</b><br><sub>Size = Influence Score • Color = Board Positions • Lines = Shared Organizations</sub>",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.4, 1.4]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.5, 1.3]),  # Extra space at bottom for text labels
            plot_bgcolor='white',
            width=900,
            height=900,
            showlegend=False,
            # Enhanced navigation controls
            dragmode='pan',
            annotations=[
                dict(
                    text="🔍 CONTROLS: Scroll wheel = Zoom • Click+drag = Pan • Hover = Details • Double-click = Reset zoom",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=-0.05,
                    xanchor='center', yanchor='bottom',
                    font=dict(color='gray', size=12)
                )
            ]
        )
        
        return fig
    
    def _add_influence_connections(self, fig: go.Figure, sorted_influence: List, positions: Dict, organizations: List):
        """Add connection lines only between people who actually share organizations."""
        
        edge_x = []
        edge_y = []
        connection_count = 0
        
        # Create person-to-organization mapping with exact organization names
        person_orgs = {}
        for name, info in sorted_influence:
            person_orgs[name] = set(info['organizations'])
        
        # Find actual shared organizations between people
        for i, (name1, info1) in enumerate(sorted_influence):
            if name1 not in positions:
                continue
            for j, (name2, info2) in enumerate(sorted_influence[i+1:], i+1):
                if name2 not in positions:
                    continue
                
                # Check if they share any organizations (must be exact matches)
                shared_orgs = person_orgs[name1].intersection(person_orgs[name2])
                if shared_orgs and len(shared_orgs) > 0:
                    # Only draw connection if they actually share organizations
                    x1, y1 = positions[name1]
                    x2, y2 = positions[name2]
                    
                    # Add connection line with variable thickness based on shared orgs
                    line_width = min(len(shared_orgs) + 1, 4)  # 1-4 width based on shared orgs
                    
                    # Add individual connection trace for better control
                    fig.add_trace(go.Scatter(
                        x=[x1, x2], y=[y1, y2],
                        line=dict(width=line_width, color='rgba(80, 80, 80, 0.4)'),
                        mode='lines',
                        hovertext=f"{name1} ↔ {name2}<br>Shared: {', '.join(list(shared_orgs)[:2])}{'...' if len(shared_orgs) > 2 else ''}",
                        hoverinfo='text',
                        showlegend=False
                    ))
                    connection_count += 1
        
        # Add annotation showing connection count
        print(f"Added {connection_count} actual board member connections to influence network")
    
    def export_visualizations(self, network_data: Dict[str, Any], base_filename: str = None) -> List[str]:
        """Export multiple network visualizations to HTML files."""
        
        if not base_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"network_viz_{timestamp}"
        
        exported_files = []
        
        # 1. Main network graph
        main_fig = self.create_interactive_network(network_data, "Board Member Network Analysis")
        main_file = f"{base_filename}_network.html"
        main_fig.write_html(main_file)
        exported_files.append(main_file)
        
        # 2. Influence network
        influence_fig = self.create_influence_network(network_data)
        influence_file = f"{base_filename}_influence.html"
        influence_fig.write_html(influence_file)
        exported_files.append(influence_file)
        
        return exported_files


# Factory function for easy import
def create_network_visualizer() -> InteractiveNetworkVisualizer:
    """Create and return a network visualizer instance."""
    return InteractiveNetworkVisualizer()