#!/usr/bin/env python3
"""
Enhanced Network Analysis Tool
Combines real-time data with network analysis for strategic opportunity identification.

Features:
1. Live data integration with intelligent classification
2. Network-based opportunity scoring  
3. Relationship pathway analysis
4. Strategic approach recommendations
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.workflow_engine import WorkflowEngine
from src.core.data_models import WorkflowConfig, ProcessorConfig
from src.processors.analysis.board_network_analyzer import BoardNetworkAnalyzerProcessor
from src.processors.analysis.intelligent_classifier import IntelligentClassifierProcessor
from src.processors.visualization.network_visualizer import InteractiveNetworkVisualizer


class EnhancedNetworkAnalysis:
    """Enhanced network analysis with strategic insights."""
    
    def __init__(self):
        self.workflow_engine = WorkflowEngine()
        self.board_analyzer = BoardNetworkAnalyzerProcessor()
        self.classifier = IntelligentClassifierProcessor()
        self.visualizer = InteractiveNetworkVisualizer()
        
    async def analyze_opportunity_network(self, 
                                        target_organizations: List[Dict[str, Any]],
                                        classification_threshold: float = 0.6) -> Dict[str, Any]:
        """Analyze network opportunities for a set of organizations."""
        
        print("ENHANCED NETWORK ANALYSIS - OPPORTUNITY IDENTIFICATION")
        print("=" * 60)
        
        # Step 1: Get network data for target organizations
        print("Step 1: Analyzing board member networks...")
        
        config = ProcessorConfig(
            workflow_id=f"network_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            target_ein=None,
            max_results=50,
            states=['VA'],
            ntee_codes=['E21', 'E30', 'E32', 'E60', 'F30'],
            min_revenue=50000
        )
        
        # Run board network analysis
        network_result = await self.board_analyzer.process(config, {'organizations': target_organizations})
        
        if not network_result.success:
            print("FAILED: Board network analysis failed")
            return {'success': False, 'error': 'Network analysis failed'}
            
        network_data = network_result.data
        print(f"SUCCESS: Found {len(network_data.get('connections', []))} board connections")
        
        # Step 2: Identify high-value network opportunities
        print("\\nStep 2: Identifying network-based opportunities...")
        
        opportunities = await self._identify_network_opportunities(network_data, classification_threshold)
        
        # Step 3: Calculate relationship pathways
        print("\\nStep 3: Analyzing relationship pathways...")
        
        pathways = self._analyze_relationship_pathways(network_data, opportunities)
        
        # Step 4: Generate strategic recommendations
        print("\\nStep 4: Generating strategic recommendations...")
        
        recommendations = self._generate_strategic_recommendations(network_data, opportunities, pathways)
        
        # Step 5: Create enhanced visualizations
        print("\\nStep 5: Creating enhanced network visualizations...")
        
        viz_data = await self._create_enhanced_visualizations(network_data, opportunities, pathways)
        
        results = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'network_data': network_data,
            'opportunities': opportunities,
            'relationship_pathways': pathways,
            'strategic_recommendations': recommendations,
            'visualizations': viz_data,
            'summary': {
                'total_organizations': len(target_organizations),
                'network_connections': len(network_data.get('connections', [])),
                'identified_opportunities': len(opportunities),
                'strategic_pathways': len(pathways),
                'recommendations_generated': len(recommendations)
            }
        }
        
        return results
    
    async def _identify_network_opportunities(self, network_data: Dict[str, Any], threshold: float) -> List[Dict[str, Any]]:
        """Identify high-value opportunities based on network analysis."""
        
        opportunities = []
        connections = network_data.get('connections', [])
        influence_scores = network_data.get('influence_scores', {}).get('individual_influence', {})
        
        # Find organizations connected to high-influence board members
        high_influence_orgs = set()
        for person, score in influence_scores.items():
            if score >= threshold:
                # Find organizations this person is connected to
                for conn in connections:
                    if conn.get('shared_members', []):
                        for member in conn['shared_members']:
                            if member.get('name', '') == person:
                                high_influence_orgs.add(conn.get('organization_1_ein', ''))
                                high_influence_orgs.add(conn.get('organization_2_ein', ''))
        
        # Create opportunity records
        organizations = network_data.get('organizations', [])
        for org in organizations:
            if org.get('ein') in high_influence_orgs:
                opportunity_score = self._calculate_opportunity_score(org, network_data)
                
                if opportunity_score >= 0.5:  # Minimum opportunity threshold
                    opportunities.append({
                        'ein': org.get('ein'),
                        'name': org.get('organization_name', 'Unknown'),
                        'opportunity_score': opportunity_score,
                        'opportunity_type': self._classify_opportunity_type(org, network_data),
                        'key_connections': self._get_key_connections(org, network_data),
                        'strategic_value': self._assess_strategic_value(org, network_data)
                    })
        
        # Sort by opportunity score
        opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        return opportunities
    
    def _calculate_opportunity_score(self, org: Dict[str, Any], network_data: Dict[str, Any]) -> float:
        """Calculate opportunity score based on network position and influence."""
        
        base_score = 0.3  # Base opportunity value
        
        # Network centrality bonus
        network_metrics = network_data.get('network_metrics', {}).get('organization_metrics', {})
        org_metrics = network_metrics.get(org.get('ein', ''), {})
        centrality_score = org_metrics.get('betweenness_centrality', 0) * 0.3
        
        # Financial health bonus (if available)
        financial_score = org.get('composite_score', 0) * 0.2
        
        # Board influence bonus
        influence_bonus = 0
        connections = network_data.get('connections', [])
        for conn in connections:
            if conn.get('organization_1_ein') == org.get('ein') or conn.get('organization_2_ein') == org.get('ein'):
                influence_bonus += len(conn.get('shared_members', [])) * 0.05
        
        opportunity_score = min(1.0, base_score + centrality_score + financial_score + influence_bonus)
        return round(opportunity_score, 3)
    
    def _classify_opportunity_type(self, org: Dict[str, Any], network_data: Dict[str, Any]) -> str:
        """Classify the type of opportunity this organization represents."""
        
        ntee_code = org.get('ntee_code', '')
        
        if ntee_code.startswith('E'):
            return 'Healthcare Partnership'
        elif ntee_code.startswith('F'):
            return 'Nutrition/Food Security'
        elif ntee_code.startswith('T'):
            return 'Foundation/Funding'
        else:
            return 'Strategic Partnership'
    
    def _get_key_connections(self, org: Dict[str, Any], network_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get key board member connections for this organization."""
        
        key_connections = []
        connections = network_data.get('connections', [])
        ein = org.get('ein')
        
        for conn in connections:
            if conn.get('organization_1_ein') == ein or conn.get('organization_2_ein') == ein:
                for member in conn.get('shared_members', []):
                    key_connections.append({
                        'name': member.get('name', 'Unknown'),
                        'position': member.get('position', 'Board Member'),
                        'other_organization': (conn.get('organization_2_name') if conn.get('organization_1_ein') == ein 
                                             else conn.get('organization_1_name'))
                    })
        
        return key_connections[:5]  # Top 5 connections
    
    def _assess_strategic_value(self, org: Dict[str, Any], network_data: Dict[str, Any]) -> str:
        """Assess the strategic value of this opportunity."""
        
        opportunity_score = self._calculate_opportunity_score(org, network_data)
        
        if opportunity_score >= 0.8:
            return 'High - Key strategic partner with strong network position'
        elif opportunity_score >= 0.6:
            return 'Medium - Good partnership potential with network benefits'
        elif opportunity_score >= 0.4:
            return 'Low - Limited strategic value but worth monitoring'
        else:
            return 'Minimal - Low priority for partnership development'
    
    def _analyze_relationship_pathways(self, network_data: Dict[str, Any], opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze optimal relationship pathways to reach target organizations."""
        
        pathways = []
        connections = network_data.get('connections', [])
        
        for opp in opportunities[:10]:  # Top 10 opportunities
            ein = opp['ein']
            
            # Find all pathways to this organization
            org_pathways = []
            
            for conn in connections:
                if conn.get('organization_1_ein') == ein or conn.get('organization_2_ein') == ein:
                    for member in conn.get('shared_members', []):
                        pathway = {
                            'target_organization': opp['name'],
                            'target_ein': ein,
                            'connection_name': member.get('name', 'Unknown'),
                            'connection_position': member.get('position', 'Board Member'),
                            'bridge_organization': (conn.get('organization_2_name') if conn.get('organization_1_ein') == ein 
                                                  else conn.get('organization_1_name')),
                            'approach_strategy': self._generate_approach_strategy(member, conn),
                            'pathway_strength': self._calculate_pathway_strength(member, conn)
                        }
                        org_pathways.append(pathway)
            
            # Sort by pathway strength
            org_pathways.sort(key=lambda x: x['pathway_strength'], reverse=True)
            pathways.extend(org_pathways[:3])  # Top 3 pathways per opportunity
        
        return pathways
    
    def _generate_approach_strategy(self, member: Dict[str, Any], connection: Dict[str, Any]) -> str:
        """Generate approach strategy for a specific connection."""
        
        position = member.get('position', 'Board Member')
        
        if 'Chair' in position or 'President' in position:
            return 'Direct executive approach - High-level strategic discussion'
        elif 'Director' in position or 'Executive' in position:
            return 'Senior leadership engagement - Program collaboration focus'
        else:
            return 'Board member introduction - Informal networking approach'
    
    def _calculate_pathway_strength(self, member: Dict[str, Any], connection: Dict[str, Any]) -> float:
        """Calculate the strength of a relationship pathway."""
        
        base_strength = 0.5
        
        # Position influence bonus
        position = member.get('position', 'Board Member')
        if 'Chair' in position or 'President' in position:
            position_bonus = 0.3
        elif 'Director' in position or 'Executive' in position:
            position_bonus = 0.2
        else:
            position_bonus = 0.1
        
        # Connection strength bonus (based on number of shared members)
        shared_count = len(connection.get('shared_members', []))
        connection_bonus = min(0.2, shared_count * 0.05)
        
        pathway_strength = min(1.0, base_strength + position_bonus + connection_bonus)
        return round(pathway_strength, 3)
    
    def _generate_strategic_recommendations(self, network_data: Dict[str, Any], 
                                          opportunities: List[Dict[str, Any]], 
                                          pathways: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate strategic recommendations based on network analysis."""
        
        recommendations = []
        
        # Top opportunity recommendations
        if opportunities:
            top_opp = opportunities[0]
            recommendations.append({
                'type': 'Priority Partnership',
                'title': f'Prioritize partnership with {top_opp["name"]}',
                'description': f'Highest opportunity score ({top_opp["opportunity_score"]}) with {top_opp["opportunity_type"]} potential',
                'action_items': [
                    'Research organization leadership and mission alignment',
                    'Identify specific collaboration opportunities',
                    'Prepare partnership proposal focusing on shared board connections'
                ],
                'timeline': '2-4 weeks',
                'priority': 'High'
            })
        
        # Network expansion recommendations
        high_influence_members = []
        influence_scores = network_data.get('influence_scores', {}).get('individual_influence', {})
        for person, score in influence_scores.items():
            if score >= 5.0:  # High influence threshold
                high_influence_members.append({'name': person, 'score': score})
        
        if high_influence_members:
            recommendations.append({
                'type': 'Network Development',
                'title': 'Cultivate relationships with key network influencers',
                'description': f'Focus on {len(high_influence_members)} high-influence board members',
                'action_items': [
                    f'Engage with {high_influence_members[0]["name"]} (influence score: {high_influence_members[0]["score"]})',
                    'Attend events where these influencers are likely to participate',
                    'Consider board member recruitment from this network'
                ],
                'timeline': '3-6 months',
                'priority': 'Medium'
            })
        
        # Pathway optimization recommendations
        strong_pathways = [p for p in pathways if p['pathway_strength'] >= 0.7]
        if strong_pathways:
            recommendations.append({
                'type': 'Relationship Strategy',
                'title': 'Execute high-strength relationship pathways',
                'description': f'Leverage {len(strong_pathways)} strong pathways for strategic introductions',
                'action_items': [
                    f'Approach {strong_pathways[0]["connection_name"]} at {strong_pathways[0]["bridge_organization"]}',
                    'Request warm introduction to target organization leadership',
                    'Prepare value proposition highlighting mutual board connections'
                ],
                'timeline': '1-2 weeks',
                'priority': 'High'
            })
        
        return recommendations
    
    async def _create_enhanced_visualizations(self, network_data: Dict[str, Any], 
                                            opportunities: List[Dict[str, Any]], 
                                            pathways: List[Dict[str, Any]]) -> Dict[str, str]:
        """Create enhanced visualizations with opportunity overlays."""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create standard network visualization
        network_fig = self.visualizer.create_interactive_network(
            network_data, 
            title="Enhanced Network Analysis - Strategic Opportunities"
        )
        
        # Create opportunity-focused visualization
        opportunity_fig = self.visualizer.create_influence_network(
            network_data, 
            title="Opportunity Network - Partnership Potential"
        )
        
        # Export HTML files
        network_file = f"enhanced_network_analysis_{timestamp}.html"
        opportunity_file = f"strategic_opportunities_{timestamp}.html"
        
        network_fig.write_html(network_file)
        opportunity_fig.write_html(opportunity_file)
        
        return {
            'network_visualization': network_file,
            'opportunity_visualization': opportunity_file,
            'timestamp': timestamp
        }
    
    async def export_enhanced_analysis(self, results: Dict[str, Any], filename_prefix: str = "enhanced_network"):
        """Export enhanced analysis results to CSV and JSON."""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export opportunities
        if results.get('opportunities'):
            opportunities_df = pd.DataFrame(results['opportunities'])
            opportunities_file = f"{filename_prefix}_opportunities_{timestamp}.csv"
            opportunities_df.to_csv(opportunities_file, index=False)
            print(f"EXPORTED: Opportunities analysis → {opportunities_file}")
        
        # Export pathways
        if results.get('relationship_pathways'):
            pathways_df = pd.DataFrame(results['relationship_pathways'])
            pathways_file = f"{filename_prefix}_pathways_{timestamp}.csv"
            pathways_df.to_csv(pathways_file, index=False)
            print(f"EXPORTED: Relationship pathways → {pathways_file}")
        
        # Export recommendations
        if results.get('strategic_recommendations'):
            recommendations_df = pd.DataFrame(results['strategic_recommendations'])
            recommendations_file = f"{filename_prefix}_recommendations_{timestamp}.csv"
            recommendations_df.to_csv(recommendations_file, index=False)
            print(f"EXPORTED: Strategic recommendations → {recommendations_file}")
        
        # Export complete results as JSON
        json_file = f"{filename_prefix}_complete_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"EXPORTED: Complete analysis → {json_file}")
        
        return {
            'opportunities_file': opportunities_file if results.get('opportunities') else None,
            'pathways_file': pathways_file if results.get('relationship_pathways') else None,
            'recommendations_file': recommendations_file if results.get('strategic_recommendations') else None,
            'json_file': json_file,
            'timestamp': timestamp
        }


async def main():
    """Test enhanced network analysis."""
    
    print("ENHANCED NETWORK ANALYSIS - STRATEGIC OPPORTUNITY INTELLIGENCE")
    print("=" * 70)
    
    # Create analyzer
    analyzer = EnhancedNetworkAnalysis()
    
    # Test with sample organizations (in real use, these would come from workflow results)
    test_organizations = [
        {
            'ein': '541669652',
            'organization_name': 'Test Health Foundation',
            'ntee_code': 'E60',
            'composite_score': 0.75
        },
        {
            'ein': '123456789',
            'organization_name': 'Community Wellness Center',
            'ntee_code': 'E32',
            'composite_score': 0.68
        },
        {
            'ein': '987654321',
            'organization_name': 'Virginia Nutrition Alliance',
            'ntee_code': 'F30',
            'composite_score': 0.72
        }
    ]
    
    try:
        # Run enhanced analysis
        results = await analyzer.analyze_opportunity_network(test_organizations, classification_threshold=0.6)
        
        if results['success']:
            print("\\nENHANCED ANALYSIS RESULTS:")
            print("=" * 40)
            
            summary = results['summary']
            print(f"Organizations Analyzed: {summary['total_organizations']}")
            print(f"Network Connections: {summary['network_connections']}")
            print(f"Opportunities Identified: {summary['identified_opportunities']}")
            print(f"Strategic Pathways: {summary['strategic_pathways']}")
            print(f"Recommendations: {summary['recommendations_generated']}")
            
            # Display top opportunities
            opportunities = results.get('opportunities', [])
            if opportunities:
                print("\\nTOP STRATEGIC OPPORTUNITIES:")
                print("-" * 40)
                for i, opp in enumerate(opportunities[:5], 1):
                    print(f"{i}. {opp['name']}")
                    print(f"   Opportunity Score: {opp['opportunity_score']}")
                    print(f"   Type: {opp['opportunity_type']}")
                    print(f"   Strategic Value: {opp['strategic_value']}")
                    print()
            
            # Display top recommendations
            recommendations = results.get('strategic_recommendations', [])
            if recommendations:
                print("STRATEGIC RECOMMENDATIONS:")
                print("-" * 40)
                for i, rec in enumerate(recommendations, 1):
                    print(f"{i}. {rec['title']}")
                    print(f"   Type: {rec['type']}")
                    print(f"   Priority: {rec['priority']}")
                    print(f"   Timeline: {rec['timeline']}")
                    print(f"   Description: {rec['description']}")
                    print()
            
            # Export results
            print("\\nExporting enhanced analysis results...")
            export_results = await analyzer.export_enhanced_analysis(results, "catalynx_enhanced_network")
            
            print("\\nSUCCESS: Enhanced network analysis completed!")
            print("\\nNEXT STEPS:")
            print("1. Review opportunity analysis and strategic recommendations")
            print("2. Open interactive visualizations in web browser")
            print("3. Execute high-priority relationship pathways")
            print("4. Monitor network evolution and partnership development")
            
        else:
            print(f"FAILED: Enhanced analysis failed - {results.get('error')}")
            
    except Exception as e:
        print(f"ERROR: Enhanced network analysis failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())