"""
Report Generation Processor
Creates comprehensive reports from analysis data.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.workflow_engine import get_workflow_engine


class ReportGenerator(BaseProcessor):
    """
    Processor for generating comprehensive reports.
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="report_generator",
            description="Generate comprehensive analysis reports in multiple formats",
            processor_type="analysis",
            dependencies=["financial_scorer", "risk_assessor", "board_network_analyzer"],
            version="1.0.0",
            estimated_duration=60,
            requires_network=False,
            can_run_parallel=True
        )
        super().__init__(metadata)
        self.logger = logging.getLogger(__name__)
    
    async def execute(self, config) -> Dict[str, Any]:
        """
        Generate comprehensive reports based on analysis data.
        
        Args:
            config: Processing config with report parameters
            
        Returns:
            Dictionary containing generated reports and file paths
        """
        context = config.parameters if hasattr(config, 'parameters') else config
        report_type = context.get('report_type', 'comprehensive')
        
        try:
            if report_type == 'comprehensive':
                return await self._generate_comprehensive_report(context)
            elif report_type == 'executive_summary':
                return await self._generate_executive_summary(context)
            elif report_type == 'financial_analysis':
                return await self._generate_financial_report(context)
            elif report_type == 'network_analysis':
                return await self._generate_network_report(context)
            else:
                raise ValueError(f"Unknown report type: {report_type}")
                
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'report_type': report_type
            }
    
    async def _generate_comprehensive_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_data = {
                'title': 'Catalynx Comprehensive Analysis Report',
                'generated': datetime.now().isoformat(),
                'sections': []
            }
            
            # Add financial analysis section
            financial_section = await self._get_financial_analysis()
            if financial_section:
                report_data['sections'].append(financial_section)
            
            # Add risk assessment section
            risk_section = await self._get_risk_analysis()
            if risk_section:
                report_data['sections'].append(risk_section)
            
            # Add network analysis section
            network_section = await self._get_network_analysis()
            if network_section:
                report_data['sections'].append(network_section)
            
            # Add recommendations section
            recommendations = await self._generate_recommendations(context)
            if recommendations:
                report_data['sections'].append(recommendations)
            
            # Save report
            report_filename = f"catalynx_comprehensive_report_{timestamp}.json"
            report_path = Path(report_filename)
            
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            # Generate text summary
            summary_filename = f"catalynx_report_summary_{timestamp}.txt"
            await self._generate_text_summary(report_data, summary_filename)
            
            return {
                'success': True,
                'report_type': 'comprehensive',
                'report_file': str(report_path),
                'summary_file': summary_filename,
                'sections_count': len(report_data['sections']),
                'timestamp': timestamp
            }
            
        except Exception as e:
            self.logger.error(f"Comprehensive report generation failed: {e}")
            raise
    
    async def _generate_executive_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary report."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            summary_data = {
                'title': 'Catalynx Executive Summary',
                'generated': datetime.now().isoformat(),
                'key_metrics': await self._get_key_metrics(),
                'recommendations': await self._get_top_recommendations(),
                'risk_assessment': await self._get_risk_summary(),
                'next_steps': await self._get_next_steps()
            }
            
            # Save summary
            summary_filename = f"catalynx_executive_summary_{timestamp}.json"
            with open(summary_filename, 'w') as f:
                json.dump(summary_data, f, indent=2)
            
            return {
                'success': True,
                'report_type': 'executive_summary',
                'report_file': summary_filename,
                'timestamp': timestamp
            }
            
        except Exception as e:
            self.logger.error(f"Executive summary generation failed: {e}")
            raise
    
    async def _generate_financial_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financial analysis report."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Run financial scorer if needed
            engine = get_workflow_engine()
            financial_context = {'analysis_type': 'comprehensive'}
            financial_results = await engine.process('financial_scorer', financial_context)
            
            report_filename = f"catalynx_financial_report_{timestamp}.json"
            with open(report_filename, 'w') as f:
                json.dump(financial_results, f, indent=2)
            
            return {
                'success': True,
                'report_type': 'financial_analysis',
                'report_file': report_filename,
                'timestamp': timestamp
            }
            
        except Exception as e:
            self.logger.error(f"Financial report generation failed: {e}")
            raise
    
    async def _generate_network_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate network analysis report."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Run board network analyzer if needed
            engine = get_workflow_engine()
            network_context = {'analysis_type': 'comprehensive'}
            network_results = await engine.process('board_network_analyzer', network_context)
            
            report_filename = f"catalynx_network_report_{timestamp}.json"
            with open(report_filename, 'w') as f:
                json.dump(network_results, f, indent=2)
            
            return {
                'success': True,
                'report_type': 'network_analysis',
                'report_file': report_filename,
                'timestamp': timestamp
            }
            
        except Exception as e:
            self.logger.error(f"Network report generation failed: {e}")
            raise
    
    async def _get_financial_analysis(self) -> Dict[str, Any]:
        """Get financial analysis section data."""
        try:
            engine = get_workflow_engine()
            context = {'analysis_type': 'summary'}
            result = await engine.process('financial_scorer', context)
            
            return {
                'title': 'Financial Analysis',
                'type': 'financial',
                'data': result
            }
        except Exception as e:
            self.logger.warning(f"Could not get financial analysis: {e}")
            return None
    
    async def _get_risk_analysis(self) -> Dict[str, Any]:
        """Get risk analysis section data."""
        try:
            engine = get_workflow_engine()
            context = {'analysis_type': 'summary'}
            result = await engine.process('risk_assessor', context)
            
            return {
                'title': 'Risk Assessment',
                'type': 'risk',
                'data': result
            }
        except Exception as e:
            self.logger.warning(f"Could not get risk analysis: {e}")
            return None
    
    async def _get_network_analysis(self) -> Dict[str, Any]:
        """Get network analysis section data."""
        try:
            engine = get_workflow_engine()
            context = {'analysis_type': 'summary'}
            result = await engine.process('board_network_analyzer', context)
            
            return {
                'title': 'Network Analysis',
                'type': 'network',
                'data': result
            }
        except Exception as e:
            self.logger.warning(f"Could not get network analysis: {e}")
            return None
    
    async def _generate_recommendations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic recommendations."""
        return {
            'title': 'Strategic Recommendations',
            'type': 'recommendations',
            'data': {
                'priority_actions': [
                    'Focus on highest-scoring opportunities',
                    'Leverage network connections for introductions',
                    'Address identified risk factors'
                ],
                'timeline': '30-90 days',
                'expected_outcomes': 'Improved funding success rate'
            }
        }
    
    async def _get_key_metrics(self) -> Dict[str, Any]:
        """Get key performance metrics."""
        return {
            'total_opportunities': 'TBD',
            'success_probability': 'TBD',
            'risk_score': 'TBD',
            'network_strength': 'TBD'
        }
    
    async def _get_top_recommendations(self) -> List[str]:
        """Get top strategic recommendations."""
        return [
            'Focus on highest probability opportunities',
            'Strengthen network connections',
            'Address risk mitigation priorities'
        ]
    
    async def _get_risk_summary(self) -> str:
        """Get risk assessment summary."""
        return "Overall risk level within acceptable parameters"
    
    async def _get_next_steps(self) -> List[str]:
        """Get recommended next steps."""
        return [
            'Review detailed analysis sections',
            'Prioritize recommended opportunities',
            'Develop action plan timeline'
        ]
    
    async def _generate_text_summary(self, report_data: Dict[str, Any], filename: str):
        """Generate readable text summary of report."""
        try:
            with open(filename, 'w') as f:
                f.write(f"{report_data['title']}\n")
                f.write("=" * len(report_data['title']) + "\n\n")
                f.write(f"Generated: {report_data['generated']}\n\n")
                
                for section in report_data.get('sections', []):
                    f.write(f"{section['title']}\n")
                    f.write("-" * len(section['title']) + "\n")
                    f.write(f"Type: {section['type']}\n")
                    f.write(f"Data: {json.dumps(section['data'], indent=2)}\n\n")
                    
        except Exception as e:
            self.logger.error(f"Text summary generation failed: {e}")


def register_processor():
    """Register the report generator processor."""
    engine = get_workflow_engine()
    engine.register_processor(ReportGenerator)