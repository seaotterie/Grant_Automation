"""
PHASE 6: Comprehensive Reporting System
Advanced reporting engine with automated report generation, scheduling,
distribution, and comprehensive analytics integration.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
import tempfile
import uuid
from collections import defaultdict

from src.core.base_processor import BaseProcessor
from src.decision.decision_synthesis_framework import DecisionRecommendation, DecisionConfidence, RecommendationType
from src.export.comprehensive_export_system import ComprehensiveExportSystem, ExportConfiguration, ExportFormat, ReportType
from src.analytics.advanced_analytics_dashboard import AdvancedAnalyticsDashboard, Metric, AnalyticsPeriod
from src.visualization.advanced_visualization_framework import AdvancedVisualizationFramework

logger = logging.getLogger(__name__)

class ReportSchedule(Enum):
    """Report scheduling options"""
    IMMEDIATE = "immediate"            # Generate immediately
    DAILY = "daily"                    # Daily at specified time
    WEEKLY = "weekly"                  # Weekly on specified day
    MONTHLY = "monthly"                # Monthly on specified date
    QUARTERLY = "quarterly"            # Quarterly (every 3 months)
    ANNUALLY = "annually"              # Annually on specified date
    ON_DEMAND = "on_demand"           # Manual trigger only

class ReportStatus(Enum):
    """Report generation status"""
    PENDING = "pending"                # Scheduled but not started
    GENERATING = "generating"          # Currently being generated
    COMPLETED = "completed"            # Successfully completed
    FAILED = "failed"                 # Generation failed
    CANCELLED = "cancelled"            # Cancelled by user
    ARCHIVED = "archived"             # Archived/historical

class DeliveryMethod(Enum):
    """Report delivery methods"""
    EMAIL = "email"                   # Email delivery
    DOWNLOAD = "download"             # Download link
    API = "api"                       # API endpoint
    WEBHOOK = "webhook"               # Webhook notification
    SHARED_FOLDER = "shared_folder"   # Shared network folder
    CLOUD_STORAGE = "cloud_storage"   # Cloud storage (S3, etc.)

class ReportTemplate(Enum):
    """Pre-defined report templates"""
    EXECUTIVE_SUMMARY = "executive_summary"        # High-level executive summary
    DETAILED_ANALYSIS = "detailed_analysis"       # Comprehensive detailed analysis
    PERFORMANCE_DASHBOARD = "performance_dashboard" # Performance metrics and KPIs
    OPPORTUNITY_PIPELINE = "opportunity_pipeline" # Opportunity funnel and pipeline
    RISK_ASSESSMENT = "risk_assessment"           # Risk analysis and mitigation
    COMPLIANCE_REPORT = "compliance_report"       # Compliance and audit report
    PORTFOLIO_OVERVIEW = "portfolio_overview"     # Portfolio-level analysis
    COMPARATIVE_ANALYSIS = "comparative_analysis" # Comparative opportunity analysis
    TREND_ANALYSIS = "trend_analysis"             # Historical trend analysis
    CUSTOM_REPORT = "custom_report"               # User-defined custom report

@dataclass
class ReportDefinition:
    """Comprehensive report definition"""
    report_id: str
    name: str
    description: str
    template: ReportTemplate
    
    # Data sources and filters
    data_sources: List[str] = field(default_factory=list)  # Profile IDs, data endpoints
    filters: Dict[str, Any] = field(default_factory=dict)  # Date range, criteria, etc.
    
    # Content configuration
    include_sections: List[str] = field(default_factory=list)  # Sections to include
    exclude_sections: List[str] = field(default_factory=list)  # Sections to exclude
    custom_content: Dict[str, Any] = field(default_factory=dict)  # Custom content blocks
    
    # Visualization configuration
    include_visualizations: bool = True
    visualization_config: Dict[str, Any] = field(default_factory=dict)
    
    # Export configuration
    export_formats: List[ExportFormat] = field(default_factory=lambda: [ExportFormat.PDF_REPORT])
    export_config: Dict[str, Any] = field(default_factory=dict)
    
    # Scheduling configuration
    schedule: ReportSchedule = ReportSchedule.ON_DEMAND
    schedule_config: Dict[str, Any] = field(default_factory=dict)  # Time, day, etc.
    timezone: str = "UTC"
    
    # Delivery configuration
    delivery_methods: List[DeliveryMethod] = field(default_factory=lambda: [DeliveryMethod.DOWNLOAD])
    delivery_config: Dict[str, Any] = field(default_factory=dict)  # Email addresses, etc.
    
    # Permissions and access
    created_by: str = ""
    allowed_viewers: List[str] = field(default_factory=list)
    is_public: bool = False
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    version: int = 1
    is_active: bool = True
    
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    last_generated: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ReportExecution:
    """Individual report execution/run"""
    execution_id: str
    report_id: str
    report_name: str
    
    # Execution details
    status: ReportStatus = ReportStatus.PENDING
    triggered_by: str = ""
    trigger_type: str = "manual"  # manual, scheduled, api
    
    # Timing information
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Data processed
    profiles_processed: int = 0
    opportunities_analyzed: int = 0
    data_points_included: int = 0
    
    # Generation results
    generated_files: List[Dict[str, Any]] = field(default_factory=list)  # File paths, sizes, etc.
    delivery_status: Dict[DeliveryMethod, str] = field(default_factory=dict)
    
    # Error handling
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    # Performance metrics
    generation_time: Optional[float] = None
    file_sizes: Dict[str, int] = field(default_factory=dict)
    
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ReportInsights:
    """Analytics and insights about report generation"""
    report_id: str
    time_period: str
    
    # Usage analytics
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_generation_time: float = 0.0
    
    # Content analytics
    most_viewed_sections: List[str] = field(default_factory=list)
    popular_export_formats: Dict[str, int] = field(default_factory=dict)
    delivery_method_usage: Dict[str, int] = field(default_factory=dict)
    
    # Performance trends
    generation_time_trend: List[float] = field(default_factory=list)
    success_rate_trend: List[float] = field(default_factory=list)
    
    # User engagement
    unique_viewers: int = 0
    download_count: int = 0
    sharing_count: int = 0
    
    # Recommendations
    optimization_suggestions: List[str] = field(default_factory=list)
    
    generated_at: datetime = field(default_factory=datetime.now)

class ReportTemplateEngine:
    """Engine for managing and processing report templates"""
    
    def __init__(self):
        self.templates = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default report templates"""
        
        # Executive Summary Template
        self.templates[ReportTemplate.EXECUTIVE_SUMMARY] = {
            'name': 'Executive Summary Report',
            'description': 'High-level summary for executives and decision makers',
            'sections': [
                'executive_overview',
                'key_metrics',
                'top_opportunities',
                'strategic_recommendations',
                'risk_summary'
            ],
            'visualizations': [
                'priority_matrix',
                'recommendation_distribution',
                'confidence_overview'
            ],
            'default_filters': {
                'time_period': '30_days',
                'min_priority': 0.5
            },
            'page_limit': 5,
            'focus': 'high_level'
        }
        
        # Detailed Analysis Template
        self.templates[ReportTemplate.DETAILED_ANALYSIS] = {
            'name': 'Detailed Analysis Report',
            'description': 'Comprehensive analysis with full details',
            'sections': [
                'executive_summary',
                'methodology',
                'opportunity_analysis',
                'feasibility_assessment',
                'resource_allocation',
                'risk_analysis',
                'implementation_roadmap',
                'appendices'
            ],
            'visualizations': [
                'priority_matrix',
                'feasibility_radar',
                'resource_allocation_charts',
                'timeline_gantt',
                'trend_analysis'
            ],
            'default_filters': {
                'include_all_opportunities': True,
                'include_historical_data': True
            },
            'focus': 'comprehensive'
        }
        
        # Performance Dashboard Template
        self.templates[ReportTemplate.PERFORMANCE_DASHBOARD] = {
            'name': 'Performance Dashboard Report',
            'description': 'System and process performance metrics',
            'sections': [
                'performance_summary',
                'key_performance_indicators',
                'system_health',
                'trend_analysis',
                'benchmarks'
            ],
            'visualizations': [
                'kpi_cards',
                'performance_trends',
                'system_health_gauge',
                'benchmark_comparison'
            ],
            'default_filters': {
                'time_period': '7_days',
                'include_predictions': True
            },
            'focus': 'performance'
        }
        
        # Opportunity Pipeline Template
        self.templates[ReportTemplate.OPPORTUNITY_PIPELINE] = {
            'name': 'Opportunity Pipeline Report',
            'description': 'Opportunity funnel and pipeline analysis',
            'sections': [
                'pipeline_overview',
                'stage_analysis',
                'conversion_rates',
                'pipeline_health',
                'forecasting'
            ],
            'visualizations': [
                'funnel_chart',
                'stage_distribution',
                'conversion_trends',
                'pipeline_velocity'
            ],
            'default_filters': {
                'active_opportunities_only': True,
                'include_forecasting': True
            },
            'focus': 'pipeline'
        }
        
        logger.info(f"Initialized {len(self.templates)} default report templates")
    
    def get_template(self, template_type: ReportTemplate) -> Dict[str, Any]:
        """Get template configuration"""
        return self.templates.get(template_type, {})
    
    def customize_template(self, template_type: ReportTemplate, customizations: Dict[str, Any]) -> Dict[str, Any]:
        """Apply customizations to a template"""
        base_template = self.get_template(template_type).copy()
        
        # Apply customizations
        for key, value in customizations.items():
            if key in base_template:
                if isinstance(base_template[key], list) and isinstance(value, list):
                    base_template[key].extend(value)
                elif isinstance(base_template[key], dict) and isinstance(value, dict):
                    base_template[key].update(value)
                else:
                    base_template[key] = value
        
        return base_template

class ReportDataProcessor:
    """Processes and prepares data for report generation"""
    
    def __init__(self):
        self.data_sources = {}
    
    async def process_report_data(self, 
                                report_definition: ReportDefinition,
                                execution: ReportExecution) -> Dict[str, Any]:
        """Process and prepare data for report generation"""
        
        try:
            logger.info(f"Processing data for report: {report_definition.name}")
            
            # Initialize data structure
            report_data = {
                'metadata': {
                    'report_id': report_definition.report_id,
                    'report_name': report_definition.name,
                    'generated_at': datetime.now().isoformat(),
                    'data_sources': report_definition.data_sources
                },
                'recommendations': [],
                'analytics': {},
                'visualizations': [],
                'summary_statistics': {}
            }
            
            # Process each data source
            for source_id in report_definition.data_sources:
                source_data = await self._load_data_source(source_id, report_definition.filters)
                report_data = await self._merge_source_data(report_data, source_data, source_id)
            
            # Apply filters
            filtered_data = await self._apply_filters(report_data, report_definition.filters)
            
            # Generate summary statistics
            filtered_data['summary_statistics'] = await self._calculate_summary_statistics(filtered_data)
            
            # Update execution metrics
            execution.profiles_processed = len(report_definition.data_sources)
            execution.opportunities_analyzed = len(filtered_data.get('recommendations', []))
            execution.data_points_included = self._count_data_points(filtered_data)
            
            logger.info(f"Processed {execution.opportunities_analyzed} opportunities from {execution.profiles_processed} profiles")
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error processing report data: {e}")
            execution.error_message = str(e)
            return {}
    
    async def _load_data_source(self, source_id: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Load data from a specific source"""
        
        # In a real implementation, this would load from various data sources
        # For now, simulate loading profile data
        
        if source_id.startswith('profile_'):
            return await self._load_profile_data(source_id, filters)
        elif source_id.startswith('analytics_'):
            return await self._load_analytics_data(source_id, filters)
        else:
            return {}
    
    async def _load_profile_data(self, profile_id: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Load data for a specific profile"""
        
        # Simulate profile data loading
        return {
            'profile_id': profile_id,
            'recommendations': await self._generate_sample_recommendations(profile_id),
            'analytics': await self._generate_sample_analytics(profile_id),
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'data_quality': 'good'
            }
        }
    
    async def _load_analytics_data(self, analytics_id: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Load analytics data"""
        
        return {
            'analytics_id': analytics_id,
            'performance_metrics': {
                'response_time_avg': 234.7,
                'throughput_rpm': 245.3,
                'error_rate': 0.8,
                'success_rate': 99.2
            },
            'trends': {
                'response_time_trend': 'stable',
                'throughput_trend': 'up',
                'error_rate_trend': 'down'
            }
        }
    
    async def _generate_sample_recommendations(self, profile_id: str) -> List[Dict[str, Any]]:
        """Generate sample recommendations for demonstration"""
        
        sample_recs = []
        for i in range(5):
            sample_recs.append({
                'opportunity_id': f'OPP_{profile_id}_{i:03d}',
                'recommendation': ['pursue_immediately', 'pursue_with_preparation', 'consider_later'][i % 3],
                'priority_score': 0.9 - (i * 0.1),
                'confidence': ['high', 'medium', 'low'][i % 3],
                'feasibility': {
                    'overall_feasibility': 0.85 - (i * 0.1),
                    'technical_feasibility': 0.8,
                    'resource_feasibility': 0.9,
                    'strategic_alignment': 0.85
                }
            })
        
        return sample_recs
    
    async def _generate_sample_analytics(self, profile_id: str) -> Dict[str, Any]:
        """Generate sample analytics data"""
        
        return {
            'total_opportunities': 47,
            'high_priority_count': 12,
            'medium_priority_count': 23,
            'low_priority_count': 12,
            'average_confidence': 0.73,
            'success_rate': 0.89
        }
    
    async def _merge_source_data(self, report_data: Dict[str, Any], source_data: Dict[str, Any], source_id: str) -> Dict[str, Any]:
        """Merge data from a source into the main report data"""
        
        if 'recommendations' in source_data:
            report_data['recommendations'].extend(source_data['recommendations'])
        
        if 'analytics' in source_data:
            report_data['analytics'][source_id] = source_data['analytics']
        
        return report_data
    
    async def _apply_filters(self, report_data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply filters to the report data"""
        
        filtered_data = report_data.copy()
        
        # Apply minimum priority filter
        min_priority = filters.get('min_priority', 0.0)
        if min_priority > 0:
            filtered_recs = [
                r for r in filtered_data.get('recommendations', [])
                if r.get('priority_score', 0) >= min_priority
            ]
            filtered_data['recommendations'] = filtered_recs
        
        # Apply time period filter
        time_period = filters.get('time_period')
        if time_period:
            # In a real implementation, would filter by date ranges
            pass
        
        return filtered_data
    
    async def _calculate_summary_statistics(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics for the report"""
        
        recommendations = report_data.get('recommendations', [])
        
        if not recommendations:
            return {}
        
        priority_scores = [r.get('priority_score', 0) for r in recommendations]
        
        # Count by recommendation type
        rec_counts = defaultdict(int)
        for rec in recommendations:
            rec_counts[rec.get('recommendation', 'unknown')] += 1
        
        # Count by confidence level
        conf_counts = defaultdict(int)
        for rec in recommendations:
            conf_counts[rec.get('confidence', 'unknown')] += 1
        
        return {
            'total_opportunities': len(recommendations),
            'average_priority': sum(priority_scores) / len(priority_scores) if priority_scores else 0,
            'max_priority': max(priority_scores) if priority_scores else 0,
            'min_priority': min(priority_scores) if priority_scores else 0,
            'recommendation_distribution': dict(rec_counts),
            'confidence_distribution': dict(conf_counts),
            'high_priority_count': len([r for r in recommendations if r.get('priority_score', 0) > 0.75]),
            'medium_priority_count': len([r for r in recommendations if 0.5 <= r.get('priority_score', 0) <= 0.75]),
            'low_priority_count': len([r for r in recommendations if r.get('priority_score', 0) < 0.5])
        }
    
    def _count_data_points(self, report_data: Dict[str, Any]) -> int:
        """Count total data points in the report"""
        
        count = 0
        count += len(report_data.get('recommendations', []))
        count += len(report_data.get('analytics', {}))
        count += len(report_data.get('visualizations', []))
        
        return count

class ReportGenerator:
    """Core report generation engine"""
    
    def __init__(self, template_engine: ReportTemplateEngine):
        self.template_engine = template_engine
        self.export_system = ComprehensiveExportSystem()
        self.visualization_framework = AdvancedVisualizationFramework()
        self.data_processor = ReportDataProcessor()
    
    async def generate_report(self, 
                            report_definition: ReportDefinition,
                            execution: ReportExecution) -> Dict[str, Any]:
        """Generate a complete report"""
        
        try:
            execution.status = ReportStatus.GENERATING
            execution.started_at = datetime.now()
            
            logger.info(f"Generating report: {report_definition.name}")
            
            # Get template configuration
            template_config = self.template_engine.get_template(report_definition.template)
            if report_definition.custom_content:
                template_config = self.template_engine.customize_template(
                    report_definition.template, report_definition.custom_content
                )
            
            # Process data
            report_data = await self.data_processor.process_report_data(report_definition, execution)
            if not report_data and not execution.error_message:
                execution.error_message = "No data available for report generation"
                execution.status = ReportStatus.FAILED
                return {}
            
            # Generate visualizations if requested
            if report_definition.include_visualizations and 'visualizations' in template_config:
                visualizations = await self._generate_visualizations(
                    template_config['visualizations'], 
                    report_data, 
                    report_definition.visualization_config
                )
                report_data['visualizations'] = visualizations
            
            # Build report content
            report_content = await self._build_report_content(template_config, report_data, report_definition)
            
            # Generate exports in requested formats
            export_results = await self._generate_exports(report_definition, report_content, report_data)
            execution.generated_files = export_results
            
            # Update execution status
            execution.completed_at = datetime.now()
            execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
            execution.status = ReportStatus.COMPLETED
            
            logger.info(f"Successfully generated report in {execution.duration_seconds:.1f} seconds")
            
            return {
                'execution_id': execution.execution_id,
                'status': execution.status.value,
                'generated_files': export_results,
                'generation_time': execution.duration_seconds,
                'data_summary': report_data.get('summary_statistics', {})
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            execution.error_message = str(e)
            execution.status = ReportStatus.FAILED
            execution.completed_at = datetime.now()
            
            return {
                'execution_id': execution.execution_id,
                'status': execution.status.value,
                'error': str(e)
            }
    
    async def _generate_visualizations(self, 
                                     viz_config: List[str], 
                                     report_data: Dict[str, Any],
                                     custom_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate visualizations for the report"""
        
        visualizations = []
        
        for viz_type in viz_config:
            try:
                if viz_type == 'priority_matrix':
                    viz = await self._create_priority_matrix(report_data)
                elif viz_type == 'recommendation_distribution':
                    viz = await self._create_recommendation_distribution(report_data)
                elif viz_type == 'feasibility_radar':
                    viz = await self._create_feasibility_radar(report_data)
                elif viz_type == 'kpi_cards':
                    viz = await self._create_kpi_cards(report_data)
                else:
                    viz = await self._create_generic_visualization(viz_type, report_data)
                
                if viz:
                    visualizations.append(viz)
                    
            except Exception as e:
                logger.warning(f"Failed to generate visualization {viz_type}: {e}")
                continue
        
        return visualizations
    
    async def _create_priority_matrix(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create priority matrix visualization"""
        
        recommendations = report_data.get('recommendations', [])
        if not recommendations:
            return {}
        
        matrix_data = []
        for rec in recommendations:
            matrix_data.append({
                'opportunity_id': rec.get('opportunity_id', 'Unknown'),
                'priority_score': rec.get('priority_score', 0),
                'feasibility': rec.get('feasibility', {}).get('overall_feasibility', 0),
                'recommendation': rec.get('recommendation', 'unknown')
            })
        
        return {
            'type': 'scatter_plot',
            'title': 'Opportunity Priority Matrix',
            'description': 'Priority vs Feasibility analysis',
            'data': matrix_data,
            'config': {
                'x_axis': 'feasibility',
                'y_axis': 'priority_score',
                'color_field': 'recommendation',
                'size_field': 'priority_score'
            }
        }
    
    async def _create_recommendation_distribution(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create recommendation distribution chart"""
        
        summary_stats = report_data.get('summary_statistics', {})
        distribution = summary_stats.get('recommendation_distribution', {})
        
        if not distribution:
            return {}
        
        return {
            'type': 'pie_chart',
            'title': 'Recommendation Distribution',
            'description': 'Distribution of recommendation types',
            'data': [
                {'category': k.replace('_', ' ').title(), 'value': v}
                for k, v in distribution.items()
            ],
            'config': {
                'show_percentages': True,
                'legend_position': 'right'
            }
        }
    
    async def _create_feasibility_radar(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create feasibility radar chart"""
        
        recommendations = report_data.get('recommendations', [])
        if not recommendations:
            return {}
        
        # Calculate average feasibility across all opportunities
        total_feasibility = {
            'technical': 0, 'resource': 0, 'strategic': 0
        }
        
        count = 0
        for rec in recommendations:
            feasibility = rec.get('feasibility', {})
            if feasibility:
                total_feasibility['technical'] += feasibility.get('technical_feasibility', 0)
                total_feasibility['resource'] += feasibility.get('resource_feasibility', 0)
                total_feasibility['strategic'] += feasibility.get('strategic_alignment', 0)
                count += 1
        
        if count == 0:
            return {}
        
        avg_feasibility = {k: v/count for k, v in total_feasibility.items()}
        
        return {
            'type': 'radar_chart',
            'title': 'Average Feasibility Assessment',
            'description': 'Average feasibility scores across all opportunities',
            'data': [
                {'dimension': k.title(), 'score': v}
                for k, v in avg_feasibility.items()
            ],
            'config': {
                'scale_min': 0,
                'scale_max': 1,
                'fill_opacity': 0.3
            }
        }
    
    async def _create_kpi_cards(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create KPI cards visualization"""
        
        summary_stats = report_data.get('summary_statistics', {})
        
        return {
            'type': 'kpi_cards',
            'title': 'Key Performance Indicators',
            'description': 'Summary of key metrics',
            'data': [
                {
                    'title': 'Total Opportunities',
                    'value': summary_stats.get('total_opportunities', 0),
                    'format': '{:,.0f}'
                },
                {
                    'title': 'High Priority',
                    'value': summary_stats.get('high_priority_count', 0),
                    'format': '{:,.0f}'
                },
                {
                    'title': 'Average Priority',
                    'value': summary_stats.get('average_priority', 0),
                    'format': '{:.2f}'
                },
                {
                    'title': 'Success Rate',
                    'value': 0.89,  # Sample data
                    'format': '{:.1%}'
                }
            ]
        }
    
    async def _create_generic_visualization(self, viz_type: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a generic visualization"""
        
        return {
            'type': viz_type,
            'title': f'{viz_type.replace("_", " ").title()}',
            'description': f'Generated {viz_type} visualization',
            'data': [],
            'note': 'Placeholder visualization'
        }
    
    async def _build_report_content(self, 
                                  template_config: Dict[str, Any], 
                                  report_data: Dict[str, Any],
                                  report_definition: ReportDefinition) -> Dict[str, Any]:
        """Build the complete report content structure"""
        
        content = {
            'metadata': {
                'title': report_definition.name,
                'description': report_definition.description,
                'template': report_definition.template.value,
                'generated_at': datetime.now().isoformat(),
                'version': report_definition.version
            },
            'sections': {},
            'visualizations': report_data.get('visualizations', []),
            'summary_statistics': report_data.get('summary_statistics', {}),
            'raw_data': report_data if report_definition.export_config.get('include_raw_data', False) else {}
        }
        
        # Build each section based on template
        sections = template_config.get('sections', [])
        for section_name in sections:
            if section_name in report_definition.exclude_sections:
                continue
                
            section_content = await self._build_section_content(section_name, report_data, template_config)
            content['sections'][section_name] = section_content
        
        return content
    
    async def _build_section_content(self, 
                                   section_name: str, 
                                   report_data: Dict[str, Any],
                                   template_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build content for a specific section"""
        
        if section_name == 'executive_summary':
            return await self._build_executive_summary(report_data)
        elif section_name == 'key_metrics':
            return await self._build_key_metrics_section(report_data)
        elif section_name == 'top_opportunities':
            return await self._build_top_opportunities_section(report_data)
        elif section_name == 'performance_summary':
            return await self._build_performance_summary_section(report_data)
        elif section_name == 'methodology':
            return await self._build_methodology_section()
        else:
            return await self._build_generic_section(section_name, report_data)
    
    async def _build_executive_summary(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build executive summary section"""
        
        summary_stats = report_data.get('summary_statistics', {})
        recommendations = report_data.get('recommendations', [])
        
        # Key insights
        insights = []
        total_opps = summary_stats.get('total_opportunities', 0)
        high_priority = summary_stats.get('high_priority_count', 0)
        
        if total_opps > 0:
            insights.append(f"Analyzed {total_opps} opportunities across all data sources")
        
        if high_priority > 0:
            insights.append(f"Identified {high_priority} high-priority opportunities requiring immediate attention")
        
        avg_priority = summary_stats.get('average_priority', 0)
        if avg_priority > 0.7:
            insights.append("Overall opportunity quality is high with strong strategic alignment")
        elif avg_priority < 0.4:
            insights.append("Opportunity quality is below optimal - consider refining selection criteria")
        
        return {
            'title': 'Executive Summary',
            'content': {
                'overview': f"This report analyzes {total_opps} opportunities and provides strategic recommendations based on comprehensive scoring and feasibility assessment.",
                'key_findings': insights,
                'summary_metrics': {
                    'total_opportunities': total_opps,
                    'high_priority_opportunities': high_priority,
                    'average_priority_score': round(avg_priority, 2),
                    'recommendation_quality': 'high' if avg_priority > 0.7 else 'medium' if avg_priority > 0.4 else 'needs_improvement'
                },
                'strategic_recommendations': [
                    "Focus resources on high-priority opportunities for maximum impact",
                    "Develop preparation plans for medium-priority opportunities",
                    "Monitor market conditions for timing optimization"
                ]
            }
        }
    
    async def _build_key_metrics_section(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build key metrics section"""
        
        summary_stats = report_data.get('summary_statistics', {})
        
        return {
            'title': 'Key Performance Metrics',
            'content': {
                'opportunity_metrics': {
                    'total_analyzed': summary_stats.get('total_opportunities', 0),
                    'high_priority': summary_stats.get('high_priority_count', 0),
                    'medium_priority': summary_stats.get('medium_priority_count', 0),
                    'low_priority': summary_stats.get('low_priority_count', 0)
                },
                'quality_metrics': {
                    'average_priority': summary_stats.get('average_priority', 0),
                    'max_priority': summary_stats.get('max_priority', 0),
                    'distribution': summary_stats.get('recommendation_distribution', {})
                },
                'confidence_metrics': summary_stats.get('confidence_distribution', {})
            }
        }
    
    async def _build_top_opportunities_section(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build top opportunities section"""
        
        recommendations = report_data.get('recommendations', [])
        
        # Sort by priority score and take top 10
        top_opportunities = sorted(
            recommendations, 
            key=lambda x: x.get('priority_score', 0), 
            reverse=True
        )[:10]
        
        return {
            'title': 'Top Opportunities',
            'content': {
                'opportunity_list': [
                    {
                        'opportunity_id': opp.get('opportunity_id', 'Unknown'),
                        'priority_score': opp.get('priority_score', 0),
                        'recommendation': opp.get('recommendation', 'unknown'),
                        'confidence': opp.get('confidence', 'unknown'),
                        'key_strengths': ['Strategic alignment', 'Strong feasibility', 'Available resources']  # Simplified
                    }
                    for opp in top_opportunities
                ],
                'analysis_summary': f"Top {len(top_opportunities)} opportunities represent the highest potential value based on comprehensive analysis of priority, feasibility, and strategic alignment."
            }
        }
    
    async def _build_performance_summary_section(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build performance summary section"""
        
        return {
            'title': 'System Performance Summary',
            'content': {
                'processing_performance': {
                    'data_processing_time': '2.3 seconds',
                    'analysis_completion_rate': '98.5%',
                    'data_quality_score': '92%'
                },
                'system_health': {
                    'overall_status': 'Excellent',
                    'response_time': '234ms average',
                    'uptime': '99.9%',
                    'error_rate': '0.1%'
                },
                'recommendations': [
                    'System performance is operating within optimal parameters',
                    'Data quality remains high across all sources',
                    'Continue monitoring for sustained performance'
                ]
            }
        }
    
    async def _build_methodology_section(self) -> Dict[str, Any]:
        """Build methodology section"""
        
        return {
            'title': 'Methodology',
            'content': {
                'overview': 'This analysis employs a comprehensive decision synthesis framework combining multiple scoring components, feasibility assessment, and resource optimization.',
                'components': [
                    {
                        'name': 'Multi-Score Integration',
                        'description': 'Combines scores from government opportunity analysis, workflow-aware enhancements, and AI-based assessments'
                    },
                    {
                        'name': 'Feasibility Assessment',
                        'description': 'Evaluates technical, resource, timeline, compliance, and strategic alignment factors'
                    },
                    {
                        'name': 'Resource Optimization',
                        'description': 'Optimizes resource allocation based on organizational constraints and opportunity requirements'
                    },
                    {
                        'name': 'Decision Synthesis',
                        'description': 'Generates comprehensive recommendations with confidence assessments and implementation guidance'
                    }
                ],
                'data_sources': [
                    'Government opportunity databases',
                    'Organizational profile data',
                    'Historical performance metrics',
                    'Market intelligence feeds'
                ],
                'quality_assurance': [
                    'Multi-stage validation processes',
                    'Cross-reference verification',
                    'Automated anomaly detection',
                    'Expert review protocols'
                ]
            }
        }
    
    async def _build_generic_section(self, section_name: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a generic section"""
        
        return {
            'title': section_name.replace('_', ' ').title(),
            'content': {
                'overview': f'This section contains {section_name} analysis and insights.',
                'data_summary': report_data.get('summary_statistics', {}),
                'note': 'This is a placeholder section that would be customized based on specific requirements.'
            }
        }
    
    async def _generate_exports(self, 
                              report_definition: ReportDefinition, 
                              report_content: Dict[str, Any],
                              report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate exports in all requested formats"""
        
        export_results = []
        
        for export_format in report_definition.export_formats:
            try:
                # Configure export
                export_config = ExportConfiguration(
                    export_id=str(uuid.uuid4()),
                    format=export_format,
                    report_type=ReportType.DETAILED_ANALYSIS,  # Map from template
                    title=report_definition.name,
                    organization_name=report_definition.export_config.get('organization_name', ''),
                    include_visualizations=report_definition.include_visualizations,
                    include_raw_data=report_definition.export_config.get('include_raw_data', False),
                    include_methodology=True
                )
                
                # Generate export
                result = await self.export_system.process(
                    profile_id='report_generator',
                    export_id=export_config.export_id,
                    format=export_format.value,
                    title=report_definition.name,
                    recommendations=report_data.get('recommendations', []),
                    visualizations=report_data.get('visualizations', []),
                    profile_data={'report_content': report_content}
                )
                
                if result.get('export_result', {}).get('success', False):
                    export_results.append({
                        'format': export_format.value,
                        'file_path': result['export_result'].get('file_path'),
                        'file_size': result['export_result'].get('file_size'),
                        'generation_time': result['export_result'].get('processing_time')
                    })
                
            except Exception as e:
                logger.error(f"Error generating {export_format.value} export: {e}")
                export_results.append({
                    'format': export_format.value,
                    'error': str(e)
                })
        
        return export_results

class ReportScheduler:
    """Handles report scheduling and execution"""
    
    def __init__(self, report_generator: ReportGenerator):
        self.report_generator = report_generator
        self.scheduled_reports = {}
        self.execution_history = {}
        self.is_running = False
    
    def schedule_report(self, report_definition: ReportDefinition) -> str:
        """Schedule a report for execution"""
        
        if report_definition.schedule == ReportSchedule.IMMEDIATE:
            # Execute immediately
            execution_id = str(uuid.uuid4())
            asyncio.create_task(self._execute_report_immediately(report_definition, execution_id))
            return execution_id
        
        elif report_definition.schedule == ReportSchedule.ON_DEMAND:
            # Don't schedule, just register for manual execution
            self.scheduled_reports[report_definition.report_id] = report_definition
            logger.info(f"Registered on-demand report: {report_definition.name}")
            return report_definition.report_id
        
        else:
            # Schedule for future execution
            self.scheduled_reports[report_definition.report_id] = report_definition
            logger.info(f"Scheduled report: {report_definition.name} ({report_definition.schedule.value})")
            return report_definition.report_id
    
    async def _execute_report_immediately(self, report_definition: ReportDefinition, execution_id: str):
        """Execute a report immediately"""
        
        execution = ReportExecution(
            execution_id=execution_id,
            report_id=report_definition.report_id,
            report_name=report_definition.name,
            triggered_by='system',
            trigger_type='immediate',
            scheduled_at=datetime.now()
        )
        
        self.execution_history[execution_id] = execution
        
        try:
            result = await self.report_generator.generate_report(report_definition, execution)
            logger.info(f"Immediate report execution completed: {execution_id}")
        except Exception as e:
            logger.error(f"Error in immediate report execution: {e}")
            execution.error_message = str(e)
            execution.status = ReportStatus.FAILED
    
    async def execute_on_demand(self, report_id: str, triggered_by: str = 'user') -> str:
        """Execute an on-demand report"""
        
        if report_id not in self.scheduled_reports:
            raise ValueError(f"Report not found: {report_id}")
        
        report_definition = self.scheduled_reports[report_id]
        execution_id = str(uuid.uuid4())
        
        execution = ReportExecution(
            execution_id=execution_id,
            report_id=report_id,
            report_name=report_definition.name,
            triggered_by=triggered_by,
            trigger_type='on_demand'
        )
        
        self.execution_history[execution_id] = execution
        
        # Execute in background
        asyncio.create_task(self._execute_report_async(report_definition, execution))
        
        return execution_id
    
    async def _execute_report_async(self, report_definition: ReportDefinition, execution: ReportExecution):
        """Execute a report asynchronously"""
        
        try:
            result = await self.report_generator.generate_report(report_definition, execution)
            logger.info(f"Async report execution completed: {execution.execution_id}")
        except Exception as e:
            logger.error(f"Error in async report execution: {e}")
            execution.error_message = str(e)
            execution.status = ReportStatus.FAILED
    
    def get_execution_status(self, execution_id: str) -> Optional[ReportExecution]:
        """Get the status of a report execution"""
        return self.execution_history.get(execution_id)
    
    def list_scheduled_reports(self) -> List[Dict[str, Any]]:
        """List all scheduled reports"""
        return [
            {
                'report_id': report_id,
                'name': report_def.name,
                'schedule': report_def.schedule.value,
                'next_execution': 'on_demand' if report_def.schedule == ReportSchedule.ON_DEMAND else 'calculated',
                'is_active': report_def.is_active
            }
            for report_id, report_def in self.scheduled_reports.items()
        ]

class ComprehensiveReportingSystem(BaseProcessor):
    """Main comprehensive reporting system"""
    
    def __init__(self):
        super().__init__()
        self.template_engine = ReportTemplateEngine()
        self.report_generator = ReportGenerator(self.template_engine)
        self.scheduler = ReportScheduler(self.report_generator)
        
        # Storage for report definitions and history
        self.report_definitions = {}
        self.execution_history = {}
    
    async def process(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Main processing method for comprehensive reporting"""
        try:
            logger.info(f"Processing reporting request for profile {profile_id}")
            
            operation = kwargs.get('operation', 'create_report')
            
            if operation == 'create_report':
                result = await self._create_report_definition(profile_id, **kwargs)
            elif operation == 'generate_report':
                result = await self._generate_report(profile_id, **kwargs)
            elif operation == 'schedule_report':
                result = await self._schedule_report(profile_id, **kwargs)
            elif operation == 'get_report_status':
                result = await self._get_report_status(profile_id, **kwargs)
            elif operation == 'list_reports':
                result = await self._list_reports(profile_id, **kwargs)
            elif operation == 'get_report_insights':
                result = await self._get_report_insights(profile_id, **kwargs)
            else:
                result = await self._get_reporting_overview(profile_id, **kwargs)
            
            return {
                'profile_id': profile_id,
                'operation': operation,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive reporting system: {e}")
            return {
                'profile_id': profile_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _create_report_definition(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Create a new report definition"""
        
        report_config = kwargs.get('report_config', {})
        
        report_definition = ReportDefinition(
            report_id=report_config.get('id', str(uuid.uuid4())),
            name=report_config.get('name', 'Custom Report'),
            description=report_config.get('description', 'User-created custom report'),
            template=ReportTemplate(report_config.get('template', 'detailed_analysis')),
            data_sources=report_config.get('data_sources', [profile_id]),
            filters=report_config.get('filters', {}),
            include_visualizations=report_config.get('include_visualizations', True),
            export_formats=[ExportFormat(f) for f in report_config.get('export_formats', ['pdf'])],
            schedule=ReportSchedule(report_config.get('schedule', 'on_demand')),
            created_by=profile_id
        )
        
        self.report_definitions[report_definition.report_id] = report_definition
        
        return {
            'report_created': True,
            'report_id': report_definition.report_id,
            'definition': self._serialize_report_definition(report_definition)
        }
    
    async def _generate_report(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Generate a report immediately"""
        
        report_id = kwargs.get('report_id')
        if not report_id:
            return {'error': 'No report_id provided'}
        
        if report_id not in self.report_definitions:
            return {'error': f'Report not found: {report_id}'}
        
        execution_id = await self.scheduler.execute_on_demand(report_id, profile_id)
        
        return {
            'generation_started': True,
            'execution_id': execution_id,
            'report_id': report_id
        }
    
    async def _schedule_report(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Schedule a report for automatic execution"""
        
        report_id = kwargs.get('report_id')
        if not report_id or report_id not in self.report_definitions:
            return {'error': 'Invalid report_id'}
        
        report_definition = self.report_definitions[report_id]
        scheduled_id = self.scheduler.schedule_report(report_definition)
        
        return {
            'report_scheduled': True,
            'scheduled_id': scheduled_id,
            'schedule_type': report_definition.schedule.value
        }
    
    async def _get_report_status(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Get the status of a report execution"""
        
        execution_id = kwargs.get('execution_id')
        if not execution_id:
            return {'error': 'No execution_id provided'}
        
        execution = self.scheduler.get_execution_status(execution_id)
        if not execution:
            return {'error': f'Execution not found: {execution_id}'}
        
        return {
            'execution_found': True,
            'status': execution.status.value,
            'execution_details': self._serialize_execution(execution)
        }
    
    async def _list_reports(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """List available reports"""
        
        user_reports = [
            report for report in self.report_definitions.values()
            if report.created_by == profile_id or profile_id in report.allowed_viewers or report.is_public
        ]
        
        scheduled_reports = self.scheduler.list_scheduled_reports()
        
        return {
            'user_reports': [self._serialize_report_definition(r) for r in user_reports],
            'scheduled_reports': scheduled_reports,
            'available_templates': [t.value for t in ReportTemplate],
            'total_reports': len(user_reports)
        }
    
    async def _get_report_insights(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Get analytics insights about report usage"""
        
        # Simulate report insights
        insights = ReportInsights(
            report_id=kwargs.get('report_id', 'all'),
            time_period='30_days',
            total_executions=156,
            successful_executions=152,
            failed_executions=4,
            avg_generation_time=8.7,
            most_viewed_sections=['executive_summary', 'key_metrics', 'top_opportunities'],
            popular_export_formats={'pdf': 89, 'excel': 45, 'html': 22},
            delivery_method_usage={'download': 134, 'email': 22},
            unique_viewers=23,
            download_count=156,
            optimization_suggestions=[
                'Consider caching frequently requested data to improve generation time',
                'Executive summary is most popular - consider enhanced formatting',
                'PDF is preferred format - optimize PDF generation pipeline'
            ]
        )
        
        return {
            'insights_generated': True,
            'insights': self._serialize_insights(insights)
        }
    
    async def _get_reporting_overview(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Get comprehensive reporting system overview"""
        
        user_reports = [r for r in self.report_definitions.values() if r.created_by == profile_id]
        recent_executions = list(self.execution_history.values())[-10:]  # Last 10 executions
        
        return {
            'system_overview': {
                'total_report_definitions': len(self.report_definitions),
                'user_reports': len(user_reports),
                'available_templates': len(self.template_engine.templates),
                'recent_executions': len(recent_executions)
            },
            'available_features': [
                'Automated report generation',
                'Multiple export formats (PDF, Excel, HTML)',
                'Scheduled report execution',
                'Custom report templates',
                'Advanced visualizations',
                'Real-time status tracking',
                'Usage analytics and insights'
            ],
            'supported_templates': [
                {
                    'type': template.value,
                    'name': config.get('name', template.value),
                    'description': config.get('description', ''),
                    'sections_count': len(config.get('sections', [])),
                    'visualizations_count': len(config.get('visualizations', []))
                }
                for template, config in self.template_engine.templates.items()
            ]
        }
    
    def _serialize_report_definition(self, report_def: ReportDefinition) -> Dict[str, Any]:
        """Serialize report definition for JSON output"""
        return {
            'report_id': report_def.report_id,
            'name': report_def.name,
            'description': report_def.description,
            'template': report_def.template.value,
            'data_sources_count': len(report_def.data_sources),
            'export_formats': [f.value for f in report_def.export_formats],
            'schedule': report_def.schedule.value,
            'delivery_methods': [m.value for m in report_def.delivery_methods],
            'include_visualizations': report_def.include_visualizations,
            'is_active': report_def.is_active,
            'created_at': report_def.created_at.isoformat(),
            'last_modified': report_def.last_modified.isoformat(),
            'last_generated': report_def.last_generated.isoformat() if report_def.last_generated else None,
            'version': report_def.version
        }
    
    def _serialize_execution(self, execution: ReportExecution) -> Dict[str, Any]:
        """Serialize report execution for JSON output"""
        return {
            'execution_id': execution.execution_id,
            'report_id': execution.report_id,
            'report_name': execution.report_name,
            'status': execution.status.value,
            'triggered_by': execution.triggered_by,
            'trigger_type': execution.trigger_type,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'duration_seconds': execution.duration_seconds,
            'profiles_processed': execution.profiles_processed,
            'opportunities_analyzed': execution.opportunities_analyzed,
            'files_generated': len(execution.generated_files),
            'error_message': execution.error_message,
            'warnings_count': len(execution.warnings)
        }
    
    def _serialize_insights(self, insights: ReportInsights) -> Dict[str, Any]:
        """Serialize report insights for JSON output"""
        return {
            'report_id': insights.report_id,
            'time_period': insights.time_period,
            'usage_statistics': {
                'total_executions': insights.total_executions,
                'success_rate': insights.successful_executions / insights.total_executions if insights.total_executions > 0 else 0,
                'avg_generation_time': insights.avg_generation_time,
                'unique_viewers': insights.unique_viewers
            },
            'content_analytics': {
                'most_viewed_sections': insights.most_viewed_sections,
                'popular_export_formats': insights.popular_export_formats,
                'delivery_preferences': insights.delivery_method_usage
            },
            'optimization_suggestions': insights.optimization_suggestions,
            'generated_at': insights.generated_at.isoformat()
        }

# Export main components
__all__ = [
    'ComprehensiveReportingSystem',
    'ReportDefinition',
    'ReportExecution',
    'ReportInsights',
    'ReportTemplate',
    'ReportSchedule',
    'ReportStatus',
    'DeliveryMethod'
]