#!/usr/bin/env python3
"""
Board Network Analysis Export Utility
Generates CSV reports of board member networks and connections.
"""

import asyncio
import pandas as pd
from datetime import datetime
from src.processors.analysis.board_network_analyzer import BoardNetworkAnalyzerProcessor
from src.core.data_models import ProcessorConfig, WorkflowConfig

async def export_board_network_analysis():
    """Generate and export board network analysis to CSV files."""
    
    print("BOARD MEMBER NETWORK ANALYSIS & EXPORT")
    print("="*60)
    
    # Create the processor
    processor = BoardNetworkAnalyzerProcessor()
    
    # Create config
    config = ProcessorConfig(
        workflow_id='board_network_export',
        processor_name='board_network_analyzer',
        workflow_config=WorkflowConfig(
            workflow_id='board_network_export',
            target_ein='123456789',
            max_results=10
        )
    )
    
    # Execute analysis
    result = await processor.execute(config, workflow_state=None)
    
    if result.success:
        data = result.data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"Analysis completed successfully!")
        print(f"Found {data['network_analysis']['total_board_members']} board positions")
        print(f"Across {data['network_analysis']['unique_individuals']} unique individuals")
        print(f"With {data['network_analysis']['network_connections']} organizational connections")
        print()
        
        # 1. Export Board Member Directory
        board_data = []
        for org in data['organizations']:
            for member in org.get('board_members', []):
                board_data.append({
                    'Board_Member': member,
                    'Organization_EIN': org['ein'],
                    'Organization_Name': org['name'],
                    'State': org.get('state', ''),
                    'NTEE_Code': org.get('ntee_code', ''),
                    'Position': 'Board Member'
                })
            
            # Add key personnel
            for person in org.get('key_personnel', []):
                if isinstance(person, dict):
                    board_data.append({
                        'Board_Member': person.get('name', ''),
                        'Organization_EIN': org['ein'],
                        'Organization_Name': org['name'],
                        'State': org.get('state', ''),
                        'NTEE_Code': org.get('ntee_code', ''),
                        'Position': person.get('title', 'Key Personnel')
                    })
        
        board_df = pd.DataFrame(board_data)
        board_file = f"board_member_directory_{timestamp}.csv"
        board_df.to_csv(board_file, index=False)
        print(f"Board Member Directory exported to: {board_file}")
        
        # 2. Export Organizational Connections
        if data.get('connections'):
            connections_data = []
            for conn in data['connections']:
                connections_data.append({
                    'Organization_1_EIN': conn['org1_ein'],
                    'Organization_1_Name': conn['org1_name'],
                    'Organization_2_EIN': conn['org2_ein'],
                    'Organization_2_Name': conn['org2_name'],
                    'Shared_Members': '; '.join(conn['shared_members']),
                    'Number_Shared_Members': conn['num_shared_members'],
                    'Connection_Strength': conn['connection_strength']
                })
            
            connections_df = pd.DataFrame(connections_data)
            connections_file = f"organizational_connections_{timestamp}.csv"
            connections_df.to_csv(connections_file, index=False)
            print(f"Organizational Connections exported to: {connections_file}")
        
        # 3. Export Influence Scores
        influence_data = data.get('influence_scores', {}).get('individual_influence', {})
        if influence_data:
            influence_list = []
            for name, info in influence_data.items():
                influence_list.append({
                    'Board_Member': name,
                    'Board_Positions': info['board_positions'],
                    'Organizations': '; '.join(info['organizations']),
                    'Network_Connections': info['network_connections'],
                    'Total_Influence_Score': info['total_influence_score']
                })
            
            influence_df = pd.DataFrame(influence_list)
            influence_df = influence_df.sort_values('Total_Influence_Score', ascending=False)
            influence_file = f"board_member_influence_{timestamp}.csv"
            influence_df.to_csv(influence_file, index=False)
            print(f"Board Member Influence Scores exported to: {influence_file}")
        
        # 4. Export Network Metrics for Organizations
        org_metrics = data.get('network_metrics', {}).get('organization_metrics', {})
        if org_metrics:
            metrics_list = []
            for ein, metrics in org_metrics.items():
                metrics_list.append({
                    'EIN': ein,
                    'Organization_Name': metrics['organization_name'],
                    'Betweenness_Centrality': metrics['betweenness_centrality'],
                    'Closeness_Centrality': metrics['closeness_centrality'],
                    'Degree_Centrality': metrics['degree_centrality'],
                    'Eigenvector_Centrality': metrics['eigenvector_centrality'],
                    'Total_Connections': metrics['total_connections'],
                    'Network_Degree': metrics['degree']
                })
            
            metrics_df = pd.DataFrame(metrics_list)
            metrics_df = metrics_df.sort_values('Betweenness_Centrality', ascending=False)
            metrics_file = f"organization_network_metrics_{timestamp}.csv"
            metrics_df.to_csv(metrics_file, index=False)
            print(f"Organization Network Metrics exported to: {metrics_file}")
        
        # 5. Export Strategic Insights Summary
        insights = data.get('insights', {})
        insights_data = []
        
        for finding in insights.get('key_findings', []):
            insights_data.append({'Type': 'Key Finding', 'Insight': finding})
        
        for rec in insights.get('strategic_recommendations', []):
            insights_data.append({'Type': 'Strategic Recommendation', 'Insight': rec})
        
        for opp in insights.get('potential_opportunities', []):
            insights_data.append({'Type': 'Potential Opportunity', 'Insight': opp})
        
        if insights_data:
            insights_df = pd.DataFrame(insights_data)
            insights_file = f"strategic_insights_{timestamp}.csv"
            insights_df.to_csv(insights_file, index=False)
            print(f"Strategic Insights exported to: {insights_file}")
        
        print()
        print("BOARD NETWORK ANALYSIS SUMMARY:")
        print("="*40)
        
        # Show top influencers
        if influence_data:
            print("Top 3 Most Influential Board Members:")
            sorted_influence = sorted(influence_data.items(), key=lambda x: x[1]['total_influence_score'], reverse=True)
            for i, (name, info) in enumerate(sorted_influence[:3], 1):
                print(f"  {i}. {name} (Score: {info['total_influence_score']:.1f})")
                print(f"     Serves on {info['board_positions']} boards")
        
        # Show strongest connections
        connections = data.get('connections', [])
        if connections:
            strongest = max(connections, key=lambda x: x['connection_strength'])
            print(f"\nStrongest Organizational Connection:")
            print(f"  {strongest['org1_name']} <-> {strongest['org2_name']}")
            print(f"  {int(strongest['connection_strength'])} shared board members")
        
        print(f"\nAll network analysis files exported with timestamp: {timestamp}")
        
    else:
        print("Board network analysis failed:")
        for error in result.errors:
            print(f"  - {error}")

if __name__ == "__main__":
    asyncio.run(export_board_network_analysis())