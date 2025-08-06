#!/usr/bin/env python3
"""
Strategic Network Analysis Tool
Combines existing network analysis with strategic opportunity identification.

Uses existing working components:
- Board network export functionality
- Interactive visualizations  
- Network metrics and analysis
"""

import asyncio
import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import json
from datetime import datetime


class StrategicNetworkAnalysis:
    """Strategic network analysis using existing system components."""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def run_complete_analysis(self) -> Dict[str, Any]:
        """Run complete strategic network analysis."""
        
        print("STRATEGIC NETWORK ANALYSIS - CATALYNX INTELLIGENCE")
        print("=" * 60)
        
        results = {
            'success': True,
            'timestamp': self.timestamp,
            'components': {},
            'insights': {},
            'files_generated': []
        }
        
        try:
            # Step 1: Generate board network analysis
            print("Step 1: Running board network analysis...")
            network_result = self._run_board_network_export()
            results['components']['board_network'] = network_result
            
            # Step 2: Create interactive visualizations
            print("\\nStep 2: Generating interactive network visualizations...")
            viz_result = self._run_interactive_visualizations()
            results['components']['visualizations'] = viz_result
            
            # Step 3: Run intelligent classification
            print("\\nStep 3: Running intelligent classification analysis...")
            classification_result = self._run_intelligent_classification()
            results['components']['classification'] = classification_result
            
            # Step 4: Generate strategic insights
            print("\\nStep 4: Analyzing strategic insights...")
            insights = self._analyze_strategic_insights()
            results['insights'] = insights
            
            # Step 5: Create comprehensive report
            print("\\nStep 5: Creating comprehensive strategic report...")
            report_file = self._create_strategic_report(results)
            results['strategic_report'] = report_file
            
            print("\\nSTRATEGIC ANALYSIS COMPLETE!")
            print("=" * 40)
            print("Generated Components:")
            for component, details in results['components'].items():
                if details.get('success'):
                    print(f"  [SUCCESS] {component}: {details.get('description', 'Completed')}")
                else:
                    print(f"  [FAILED]  {component}: {details.get('error', 'Unknown error')}")
            
            print(f"\\nStrategic Report: {report_file}")
            print("\\nNEXT STEPS:")
            print("1. Review strategic insights and recommendations")
            print("2. Open interactive network visualizations")
            print("3. Execute priority relationship pathways")
            print("4. Monitor network evolution over time")
            
            return results
            
        except Exception as e:
            print(f"ERROR: Strategic analysis failed: {e}")
            results['success'] = False
            results['error'] = str(e)
            return results
    
    def _run_board_network_export(self) -> Dict[str, Any]:
        """Run board network analysis and export."""
        
        try:
            result = subprocess.run([
                "grant-research-env/Scripts/python.exe", 
                "export_board_network.py"
            ], capture_output=True, text=True, cwd=".")
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'description': 'Board network analysis completed',
                    'output': result.stdout.strip(),
                    'files': self._extract_generated_files(result.stdout, 'board_member')
                }
            else:
                return {
                    'success': False,
                    'error': f"Board network export failed: {result.stderr}",
                    'output': result.stdout
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to run board network export: {e}"
            }
    
    def _run_interactive_visualizations(self) -> Dict[str, Any]:
        """Generate interactive network visualizations."""
        
        try:
            result = subprocess.run([
                "grant-research-env/Scripts/python.exe", 
                "test_interactive_network.py"
            ], capture_output=True, text=True, cwd=".")
            
            if result.returncode == 0:
                html_files = []
                if "catalynx_demo_network.html" in result.stdout:
                    html_files.append("catalynx_demo_network.html")
                if "catalynx_demo_influence.html" in result.stdout:
                    html_files.append("catalynx_demo_influence.html")
                
                return {
                    'success': True,
                    'description': f'Generated {len(html_files)} interactive visualizations',
                    'html_files': html_files,
                    'output': result.stdout.strip()
                }
            else:
                return {
                    'success': False,
                    'error': f"Visualization generation failed: {result.stderr}",
                    'output': result.stdout
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to generate visualizations: {e}"
            }
    
    def _run_intelligent_classification(self) -> Dict[str, Any]:
        """Run intelligent classification analysis."""
        
        try:
            result = subprocess.run([
                "grant-research-env/Scripts/python.exe", 
                "main.py", "classify-organizations", 
                "--max-results", "50",
                "--detailed"
            ], capture_output=True, text=True, cwd=".")
            
            if result.returncode == 0:
                # Extract key metrics from output
                output_lines = result.stdout.strip().split('\\n')
                metrics = {}
                
                for line in output_lines:
                    if "Total unclassified organizations:" in line:
                        metrics['total_unclassified'] = line.split(':')[1].strip()
                    elif "Promising candidates" in line:
                        metrics['promising_candidates'] = line.split(':')[1].strip()
                    elif "Success rate:" in line:
                        metrics['success_rate'] = line.split(':')[1].strip()
                
                return {
                    'success': True,
                    'description': 'Intelligent classification completed',
                    'metrics': metrics,
                    'output': result.stdout.strip()
                }
            else:
                return {
                    'success': False,
                    'error': f"Classification failed: {result.stderr}",
                    'output': result.stdout
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to run classification: {e}"
            }
    
    def _analyze_strategic_insights(self) -> Dict[str, Any]:
        """Analyze strategic insights from available data."""
        
        insights = {
            'network_opportunities': [],
            'strategic_recommendations': [],
            'priority_actions': [],
            'relationship_pathways': []
        }
        
        # Analyze CSV files if they exist
        csv_files = list(Path('.').glob('*network*.csv'))
        csv_files.extend(list(Path('.').glob('*board_member*.csv')))
        csv_files.extend(list(Path('.').glob('*influence*.csv')))
        
        if csv_files:
            latest_files = sorted(csv_files, key=os.path.getmtime, reverse=True)[:5]
            
            for csv_file in latest_files:
                try:
                    df = pd.read_csv(csv_file)
                    file_analysis = self._analyze_csv_file(csv_file, df)
                    
                    if 'influence' in csv_file.name.lower():
                        insights['network_opportunities'].extend(file_analysis.get('opportunities', []))
                    elif 'connection' in csv_file.name.lower():
                        insights['relationship_pathways'].extend(file_analysis.get('pathways', []))
                    
                except Exception as e:
                    print(f"Warning: Could not analyze {csv_file}: {e}")
        
        # Generate strategic recommendations
        insights['strategic_recommendations'] = self._generate_strategic_recommendations(insights)
        insights['priority_actions'] = self._generate_priority_actions(insights)
        
        return insights
    
    def _analyze_csv_file(self, file_path: Path, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze a CSV file for strategic insights."""
        
        analysis = {
            'file': str(file_path),
            'rows': len(df),
            'columns': list(df.columns),
            'opportunities': [],
            'pathways': []
        }
        
        # Analyze influence data
        if 'influence' in file_path.name.lower() and 'influence_score' in df.columns:
            high_influence = df[df['influence_score'] > 5.0] if 'influence_score' in df.columns else df.head(5)
            
            for _, row in high_influence.iterrows():
                analysis['opportunities'].append({
                    'type': 'High Influence Contact',
                    'name': row.get('name', 'Unknown'),
                    'score': row.get('influence_score', 0),
                    'organizations': row.get('board_positions', 'Unknown')
                })
        
        # Analyze connection data
        elif 'connection' in file_path.name.lower():
            for _, row in df.head(10).iterrows():  # Top 10 connections
                analysis['pathways'].append({
                    'type': 'Organizational Connection',
                    'org1': row.get('organization_1', 'Unknown'),
                    'org2': row.get('organization_2', 'Unknown'),
                    'strength': row.get('connection_strength', 'Unknown'),
                    'shared_members': row.get('shared_members_count', 0)
                })
        
        return analysis
    
    def _generate_strategic_recommendations(self, insights: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate strategic recommendations based on insights."""
        
        recommendations = []
        
        # Network opportunity recommendations
        opportunities = insights.get('network_opportunities', [])
        if opportunities:
            high_influence = [opp for opp in opportunities if isinstance(opp.get('score'), (int, float)) and opp['score'] > 5.0]
            if high_influence:
                recommendations.append({
                    'title': 'Engage High-Influence Network Contacts',
                    'description': f'Focus on {len(high_influence)} high-influence board members for strategic partnerships',
                    'priority': 'High',
                    'timeline': '2-4 weeks',
                    'action': f'Prioritize outreach to {high_influence[0]["name"]} and similar influencers'
                })
        
        # Relationship pathway recommendations
        pathways = insights.get('relationship_pathways', [])
        if pathways:
            strong_connections = [path for path in pathways if isinstance(path.get('shared_members'), int) and path['shared_members'] > 2]
            if strong_connections:
                recommendations.append({
                    'title': 'Leverage Strong Organizational Connections',
                    'description': f'Utilize {len(strong_connections)} multi-member board connections for warm introductions',
                    'priority': 'Medium',
                    'timeline': '1-3 weeks',
                    'action': 'Request introductions through shared board members'
                })
        
        # General networking recommendations
        recommendations.append({
            'title': 'Expand Network Analysis Coverage',
            'description': 'Increase data collection to identify additional strategic partnership opportunities',
            'priority': 'Medium',
            'timeline': '4-8 weeks',
            'action': 'Run analysis on larger organization dataset and track network evolution'
        })
        
        return recommendations
    
    def _generate_priority_actions(self, insights: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate specific priority actions."""
        
        actions = []
        
        actions.append({
            'action': 'Review Interactive Network Visualizations',
            'description': 'Open generated HTML files to explore network relationships visually',
            'timeline': 'Immediate',
            'tools': 'Web browser, catalynx_demo_*.html files'
        })
        
        actions.append({
            'action': 'Analyze Board Member Influence Data',
            'description': 'Review influence scores and identify top candidates for outreach',
            'timeline': '1-2 days',
            'tools': 'CSV files, spreadsheet software'
        })
        
        actions.append({
            'action': 'Develop Relationship Outreach Strategy',
            'description': 'Create specific outreach plan for high-value connections',
            'timeline': '1 week',
            'tools': 'Network analysis data, contact research'
        })
        
        return actions
    
    def _extract_generated_files(self, output: str, prefix: str) -> List[str]:
        """Extract generated file names from command output."""
        
        files = []
        lines = output.split('\\n')
        
        for line in lines:
            if 'exported to:' in line.lower() or 'saved to:' in line.lower():
                # Extract filename from line
                parts = line.split(':')
                if len(parts) > 1:
                    filename = parts[-1].strip()
                    if filename and prefix in filename:
                        files.append(filename)
        
        return files
    
    def _create_strategic_report(self, results: Dict[str, Any]) -> str:
        """Create comprehensive strategic analysis report."""
        
        report_file = f"catalynx_strategic_analysis_{self.timestamp}.json"
        
        # Enhance results with metadata
        enhanced_results = {
            **results,
            'analysis_metadata': {
                'generated_at': datetime.now().isoformat(),
                'analysis_type': 'Strategic Network Intelligence',
                'system_version': 'Catalynx 2.0',
                'components_analyzed': list(results.get('components', {}).keys())
            },
            'executive_summary': self._create_executive_summary(results)
        }
        
        # Export as JSON
        with open(report_file, 'w') as f:
            json.dump(enhanced_results, f, indent=2, default=str)
        
        # Also create a readable text summary
        txt_file = f"catalynx_strategic_summary_{self.timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("CATALYNX STRATEGIC NETWORK ANALYSIS\\n")
            f.write("=" * 50 + "\\n\\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
            
            # Executive summary
            f.write("EXECUTIVE SUMMARY:\\n")
            f.write("-" * 20 + "\\n")
            exec_summary = enhanced_results.get('executive_summary', {})
            for key, value in exec_summary.items():
                f.write(f"{key.replace('_', ' ').title()}: {value}\\n")
            
            # Strategic recommendations
            f.write("\\nSTRATEGIC RECOMMENDATIONS:\\n")
            f.write("-" * 30 + "\\n")
            recommendations = results.get('insights', {}).get('strategic_recommendations', [])
            for i, rec in enumerate(recommendations, 1):
                f.write(f"{i}. {rec.get('title', 'Unknown')}\\n")
                f.write(f"   Priority: {rec.get('priority', 'Unknown')}\\n")
                f.write(f"   Timeline: {rec.get('timeline', 'Unknown')}\\n")
                f.write(f"   Action: {rec.get('action', 'No action specified')}\\n\\n")
        
        print(f"EXPORTED: Strategic analysis report -> {report_file}")
        print(f"EXPORTED: Executive summary -> {txt_file}")
        
        return report_file
    
    def _create_executive_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive summary of analysis."""
        
        summary = {
            'analysis_status': 'Completed' if results.get('success') else 'Failed',
            'components_successful': len([c for c in results.get('components', {}).values() if c.get('success')]),
            'total_components': len(results.get('components', {})),
            'insights_generated': len(results.get('insights', {}).get('strategic_recommendations', [])),
            'priority_actions': len(results.get('insights', {}).get('priority_actions', [])),
            'network_opportunities': len(results.get('insights', {}).get('network_opportunities', [])),
            'relationship_pathways': len(results.get('insights', {}).get('relationship_pathways', []))
        }
        
        # Calculate success rate
        if summary['total_components'] > 0:
            success_rate = (summary['components_successful'] / summary['total_components']) * 100
            summary['success_rate'] = f"{success_rate:.1f}%"
        else:
            summary['success_rate'] = "0%"
        
        return summary


def main():
    """Run strategic network analysis."""
    
    analyzer = StrategicNetworkAnalysis()
    results = analyzer.run_complete_analysis()
    
    return results


if __name__ == "__main__":
    main()