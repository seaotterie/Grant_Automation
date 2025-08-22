"""
PHASE 6: Advanced Visualization Framework  
Enhanced visualization system for APPROACH tab with interactive charts,
decision support visualizations, and advanced analytics dashboards.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
import numpy as np
from collections import defaultdict

from src.core.base_processor import BaseProcessor
from src.decision.decision_synthesis_framework import DecisionRecommendation, DecisionConfidence, RecommendationType

logger = logging.getLogger(__name__)

class ChartType(Enum):
    """Supported chart types for visualizations"""
    BAR_CHART = "bar"
    LINE_CHART = "line" 
    PIE_CHART = "pie"
    SCATTER_PLOT = "scatter"
    RADAR_CHART = "radar"
    HEATMAP = "heatmap"
    SANKEY_DIAGRAM = "sankey"
    NETWORK_GRAPH = "network"
    DECISION_TREE = "decision_tree"
    FUNNEL_CHART = "funnel"

class InteractionType(Enum):
    """Types of interactive features"""
    HOVER_TOOLTIP = "hover"
    CLICK_DRILL_DOWN = "click_drill"
    ZOOM_PAN = "zoom_pan"
    FILTER_CONTROLS = "filter"
    BRUSH_SELECT = "brush"
    CROSSFILTER = "crossfilter"

class VisualizationTheme(Enum):
    """Visualization themes for consistent styling"""
    PROFESSIONAL = "professional"
    MODERN = "modern"
    HIGH_CONTRAST = "high_contrast"
    COLORBLIND_FRIENDLY = "colorblind"
    DARK_MODE = "dark"
    LIGHT_MODE = "light"

@dataclass
class ChartConfiguration:
    """Configuration for individual chart components"""
    chart_id: str
    chart_type: ChartType
    title: str
    description: str
    
    # Data configuration
    data_source: str                    # Data source identifier
    x_axis: str                        # X-axis field
    y_axis: str                        # Y-axis field
    color_field: Optional[str] = None   # Field for color coding
    size_field: Optional[str] = None    # Field for size variation
    
    # Styling and theming
    theme: VisualizationTheme = VisualizationTheme.PROFESSIONAL
    color_palette: List[str] = field(default_factory=lambda: [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ])
    
    # Interactive features
    interactions: List[InteractionType] = field(default_factory=list)
    tooltip_fields: List[str] = field(default_factory=list)
    
    # Layout and dimensions
    width: int = 600
    height: int = 400
    margin: Dict[str, int] = field(default_factory=lambda: {'top': 40, 'right': 30, 'bottom': 60, 'left': 70})
    
    # Chart-specific options
    options: Dict[str, Any] = field(default_factory=dict)
    
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DashboardLayout:
    """Layout configuration for visualization dashboard"""
    dashboard_id: str
    title: str
    description: str
    
    # Grid layout configuration
    grid_columns: int = 12              # Bootstrap-style 12-column grid
    grid_rows: int = 8                  # Number of grid rows
    
    # Chart placements
    chart_placements: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # {chart_id: {row, col, width, height}}
    
    # Responsive breakpoints
    breakpoints: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        'desktop': {'min_width': 1200},
        'tablet': {'min_width': 768, 'max_width': 1199},
        'mobile': {'max_width': 767}
    })
    
    # Dashboard-level interactivity
    cross_filters: List[str] = field(default_factory=list)    # Charts that participate in cross-filtering
    linked_interactions: List[List[str]] = field(default_factory=list)  # Groups of linked charts
    
    theme: VisualizationTheme = VisualizationTheme.PROFESSIONAL
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecisionSupportVisualization:
    """Specialized visualization for decision support"""
    opportunity_id: str
    recommendation: DecisionRecommendation
    
    # Key visualization components
    score_breakdown_chart: ChartConfiguration
    feasibility_radar_chart: ChartConfiguration
    resource_allocation_pie: ChartConfiguration
    timeline_gantt: ChartConfiguration
    risk_heatmap: ChartConfiguration
    
    # Interactive decision elements
    decision_tree: Dict[str, Any]
    scenario_selector: Dict[str, Any]
    sensitivity_analysis: Dict[str, Any]
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class ScoreVisualizationGenerator:
    """Generator for score-based visualizations"""
    
    def __init__(self):
        self.default_colors = {
            'excellent': '#2ecc71',      # Green
            'good': '#f39c12',           # Orange  
            'fair': '#e67e22',           # Dark orange
            'poor': '#e74c3c',           # Red
            'unknown': '#95a5a6'         # Gray
        }
    
    def generate_score_breakdown_chart(self, recommendation: DecisionRecommendation) -> ChartConfiguration:
        """Generate score breakdown bar chart"""
        
        # Prepare data for score components
        component_data = []
        for component in recommendation.integrated_score.components:
            component_data.append({
                'source': component.source,
                'raw_score': component.raw_score,
                'weighted_score': component.weighted_score,
                'confidence': component.confidence,
                'color': self._get_score_color(component.weighted_score)
            })
        
        return ChartConfiguration(
            chart_id=f"score_breakdown_{recommendation.opportunity_id}",
            chart_type=ChartType.BAR_CHART,
            title="Score Component Breakdown",
            description="Individual scoring components contributing to final recommendation",
            data_source="score_components",
            x_axis="source",
            y_axis="weighted_score",
            color_field="color",
            interactions=[InteractionType.HOVER_TOOLTIP, InteractionType.CLICK_DRILL_DOWN],
            tooltip_fields=["source", "raw_score", "weighted_score", "confidence"],
            options={
                'horizontal': False,
                'show_values': True,
                'max_value': 1.0,
                'score_thresholds': {'high': 0.75, 'medium': 0.5, 'low': 0.25}
            },
            metadata={'data': component_data}
        )
    
    def generate_feasibility_radar_chart(self, recommendation: DecisionRecommendation) -> ChartConfiguration:
        """Generate feasibility assessment radar chart"""
        
        feasibility_data = [
            {'dimension': 'Technical', 'score': recommendation.feasibility_assessment.technical_feasibility},
            {'dimension': 'Resource', 'score': recommendation.feasibility_assessment.resource_feasibility},
            {'dimension': 'Timeline', 'score': recommendation.feasibility_assessment.timeline_feasibility},
            {'dimension': 'Compliance', 'score': recommendation.feasibility_assessment.compliance_feasibility},
            {'dimension': 'Strategic', 'score': recommendation.feasibility_assessment.strategic_alignment}
        ]
        
        return ChartConfiguration(
            chart_id=f"feasibility_radar_{recommendation.opportunity_id}",
            chart_type=ChartType.RADAR_CHART,
            title="Feasibility Assessment",
            description="Multi-dimensional feasibility analysis across key factors",
            data_source="feasibility_dimensions",
            x_axis="dimension",
            y_axis="score",
            color_field=None,
            interactions=[InteractionType.HOVER_TOOLTIP],
            tooltip_fields=["dimension", "score"],
            options={
                'scale_min': 0,
                'scale_max': 1,
                'show_scale_labels': True,
                'fill_opacity': 0.2,
                'point_radius': 5
            },
            metadata={'data': feasibility_data}
        )
    
    def generate_priority_matrix_scatter(self, recommendations: List[DecisionRecommendation]) -> ChartConfiguration:
        """Generate priority matrix scatter plot"""
        
        scatter_data = []
        for rec in recommendations:
            scatter_data.append({
                'opportunity_id': rec.opportunity_id,
                'feasibility': rec.feasibility_assessment.overall_feasibility,
                'score': rec.integrated_score.final_score,
                'priority': rec.priority_score,
                'recommendation': rec.recommendation.value,
                'confidence': rec.confidence.value,
                'size': rec.resource_allocation.strategic_value * 100  # Scale for visualization
            })
        
        return ChartConfiguration(
            chart_id="priority_matrix_scatter",
            chart_type=ChartType.SCATTER_PLOT,
            title="Opportunity Priority Matrix",
            description="Feasibility vs Score analysis with recommendation categories",
            data_source="priority_matrix",
            x_axis="feasibility",
            y_axis="score", 
            color_field="recommendation",
            size_field="size",
            interactions=[InteractionType.HOVER_TOOLTIP, InteractionType.CLICK_DRILL_DOWN, InteractionType.BRUSH_SELECT],
            tooltip_fields=["opportunity_id", "feasibility", "score", "recommendation", "confidence"],
            options={
                'quadrant_lines': {'x': 0.5, 'y': 0.5},
                'quadrant_labels': {
                    'top_right': 'High Priority',
                    'top_left': 'High Score, Low Feasibility',
                    'bottom_right': 'High Feasibility, Low Score',
                    'bottom_left': 'Low Priority'
                }
            },
            metadata={'data': scatter_data}
        )
    
    def _get_score_color(self, score: float) -> str:
        """Get color based on score value"""
        if score >= 0.8:
            return self.default_colors['excellent']
        elif score >= 0.6:
            return self.default_colors['good']
        elif score >= 0.4:
            return self.default_colors['fair']
        else:
            return self.default_colors['poor']

class ResourceVisualizationGenerator:
    """Generator for resource allocation visualizations"""
    
    def generate_resource_allocation_pie(self, recommendation: DecisionRecommendation) -> ChartConfiguration:
        """Generate resource allocation pie chart"""
        
        allocation_data = []
        for resource_type, allocation in recommendation.resource_allocation.recommended_allocation.items():
            allocation_data.append({
                'resource_type': resource_type.value.replace('_', ' ').title(),
                'allocation': allocation,
                'percentage': allocation * 100
            })
        
        return ChartConfiguration(
            chart_id=f"resource_allocation_{recommendation.opportunity_id}",
            chart_type=ChartType.PIE_CHART,
            title="Recommended Resource Allocation",
            description="Distribution of resources across different categories",
            data_source="resource_allocation",
            x_axis="resource_type",
            y_axis="allocation",
            interactions=[InteractionType.HOVER_TOOLTIP],
            tooltip_fields=["resource_type", "percentage"],
            options={
                'show_percentages': True,
                'show_labels': True,
                'donut': False,
                'legend_position': 'right'
            },
            metadata={'data': allocation_data}
        )
    
    def generate_timeline_gantt(self, recommendation: DecisionRecommendation) -> ChartConfiguration:
        """Generate timeline Gantt chart"""
        
        timeline = recommendation.resource_allocation.recommended_timeline
        gantt_data = []
        
        if 'phases' in timeline:
            current_date = datetime.now()
            for phase_name, phase_info in timeline['phases'].items():
                duration_weeks = phase_info.get('duration_weeks', 4)
                end_date = current_date + timedelta(weeks=duration_weeks)
                
                gantt_data.append({
                    'phase': phase_name.replace('_', ' ').title(),
                    'start_date': current_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'duration_weeks': duration_weeks,
                    'description': phase_info.get('description', '')
                })
                
                current_date = end_date
        
        return ChartConfiguration(
            chart_id=f"timeline_gantt_{recommendation.opportunity_id}",
            chart_type=ChartType.BAR_CHART,  # Horizontal bar chart for Gantt
            title="Project Timeline",
            description="Recommended timeline phases and milestones",
            data_source="timeline_phases",
            x_axis="duration_weeks",
            y_axis="phase",
            interactions=[InteractionType.HOVER_TOOLTIP],
            tooltip_fields=["phase", "start_date", "end_date", "description"],
            options={
                'horizontal': True,
                'time_scale': True,
                'show_milestones': True,
                'critical_path': recommendation.resource_allocation.critical_path
            },
            metadata={'data': gantt_data}
        )
    
    def generate_resource_conflicts_heatmap(self, recommendations: List[DecisionRecommendation]) -> ChartConfiguration:
        """Generate resource conflicts heatmap"""
        
        # Prepare conflict matrix data
        heatmap_data = []
        resource_types = ['staff_time', 'budget', 'expertise', 'partnerships', 'infrastructure']
        
        for i, rec1 in enumerate(recommendations):
            for j, rec2 in enumerate(recommendations):
                if i != j:  # Don't compare with self
                    conflict_score = self._calculate_conflict_score(rec1, rec2)
                    heatmap_data.append({
                        'opportunity_1': rec1.opportunity_id,
                        'opportunity_2': rec2.opportunity_id,
                        'conflict_score': conflict_score,
                        'row': i,
                        'col': j
                    })
        
        return ChartConfiguration(
            chart_id="resource_conflicts_heatmap",
            chart_type=ChartType.HEATMAP,
            title="Resource Conflict Analysis",
            description="Potential resource conflicts between opportunities",
            data_source="resource_conflicts",
            x_axis="opportunity_2",
            y_axis="opportunity_1",
            color_field="conflict_score",
            interactions=[InteractionType.HOVER_TOOLTIP],
            tooltip_fields=["opportunity_1", "opportunity_2", "conflict_score"],
            options={
                'color_scale': 'RdYlGn_r',  # Red-Yellow-Green reversed
                'scale_min': 0,
                'scale_max': 1,
                'show_values': True
            },
            metadata={'data': heatmap_data}
        )
    
    def _calculate_conflict_score(self, rec1: DecisionRecommendation, rec2: DecisionRecommendation) -> float:
        """Calculate resource conflict score between two recommendations"""
        
        # Simple overlap calculation based on resource allocation
        alloc1 = rec1.resource_allocation.recommended_allocation
        alloc2 = rec2.resource_allocation.recommended_allocation
        
        overlap_score = 0.0
        for resource_type in alloc1.keys():
            if resource_type in alloc2:
                # Higher allocations in both create higher conflict
                conflict = min(alloc1[resource_type], alloc2[resource_type])
                overlap_score += conflict
        
        return min(1.0, overlap_score)

class InteractiveVisualizationEngine:
    """Engine for creating interactive visualization experiences"""
    
    def __init__(self):
        self.supported_interactions = {
            InteractionType.HOVER_TOOLTIP: self._generate_tooltip_config,
            InteractionType.CLICK_DRILL_DOWN: self._generate_drill_down_config,
            InteractionType.FILTER_CONTROLS: self._generate_filter_config,
            InteractionType.CROSSFILTER: self._generate_crossfilter_config
        }
    
    def enhance_chart_interactivity(self, chart_config: ChartConfiguration) -> Dict[str, Any]:
        """Enhance chart configuration with interactive features"""
        
        interactive_config = {
            'base_config': chart_config,
            'interactions': {}
        }
        
        for interaction_type in chart_config.interactions:
            if interaction_type in self.supported_interactions:
                handler = self.supported_interactions[interaction_type]
                interactive_config['interactions'][interaction_type.value] = handler(chart_config)
        
        return interactive_config
    
    def _generate_tooltip_config(self, chart_config: ChartConfiguration) -> Dict[str, Any]:
        """Generate tooltip configuration"""
        
        return {
            'enabled': True,
            'fields': chart_config.tooltip_fields,
            'format': {
                field: self._get_field_format(field) for field in chart_config.tooltip_fields
            },
            'style': {
                'background': 'rgba(0, 0, 0, 0.8)',
                'color': 'white',
                'border_radius': '4px',
                'padding': '8px',
                'font_size': '12px'
            },
            'position': 'cursor'  # Follow cursor or 'fixed'
        }
    
    def _generate_drill_down_config(self, chart_config: ChartConfiguration) -> Dict[str, Any]:
        """Generate drill-down interaction configuration"""
        
        return {
            'enabled': True,
            'trigger': 'click',
            'action': 'navigate',  # or 'modal', 'expand_inline'
            'target_route': f"/opportunities/{{{chart_config.x_axis}}}",  # Dynamic routing
            'data_context': chart_config.tooltip_fields,
            'animation': {
                'type': 'slide',
                'duration': 300
            }
        }
    
    def _generate_filter_config(self, chart_config: ChartConfiguration) -> Dict[str, Any]:
        """Generate filter controls configuration"""
        
        return {
            'enabled': True,
            'filter_types': {
                'range': [chart_config.y_axis] if chart_config.y_axis else [],
                'categorical': [chart_config.color_field] if chart_config.color_field else [],
                'search': [chart_config.x_axis] if chart_config.x_axis else []
            },
            'position': 'top',  # 'top', 'bottom', 'left', 'right'
            'style': 'compact'  # 'compact', 'expanded'
        }
    
    def _generate_crossfilter_config(self, chart_config: ChartConfiguration) -> Dict[str, Any]:
        """Generate cross-filter configuration"""
        
        return {
            'enabled': True,
            'dimensions': [chart_config.x_axis, chart_config.y_axis],
            'groups': ['main_dashboard'],  # Cross-filter groups
            'brush_selection': True,
            'auto_update': True
        }
    
    def _get_field_format(self, field: str) -> str:
        """Get appropriate format for field in tooltips"""
        
        format_mapping = {
            'score': '.2f',
            'percentage': '.1%',
            'currency': '$,.0f',
            'date': '%Y-%m-%d',
            'integer': ',d'
        }
        
        # Simple heuristic based on field name
        if 'score' in field.lower() or 'feasibility' in field.lower():
            return '.2f'
        elif 'percentage' in field.lower() or field.endswith('_pct'):
            return '.1%'
        elif 'budget' in field.lower() or 'cost' in field.lower():
            return '$,.0f'
        elif 'date' in field.lower():
            return '%Y-%m-%d'
        else:
            return 's'  # String format

class DashboardLayoutEngine:
    """Engine for creating responsive dashboard layouts"""
    
    def __init__(self):
        self.layout_templates = {
            'decision_support': self._create_decision_support_layout,
            'portfolio_overview': self._create_portfolio_layout,
            'comparative_analysis': self._create_comparative_layout,
            'executive_summary': self._create_executive_layout
        }
    
    def create_dashboard_layout(self, 
                               layout_type: str,
                               charts: List[ChartConfiguration],
                               **kwargs) -> DashboardLayout:
        """Create dashboard layout based on type and charts"""
        
        if layout_type in self.layout_templates:
            layout_func = self.layout_templates[layout_type]
            return layout_func(charts, **kwargs)
        else:
            return self._create_default_layout(charts, **kwargs)
    
    def _create_decision_support_layout(self, charts: List[ChartConfiguration], **kwargs) -> DashboardLayout:
        """Create layout optimized for decision support"""
        
        # Organize charts by type for optimal placement
        chart_placements = {}
        
        # Primary score chart - full width at top
        score_charts = [c for c in charts if 'score' in c.chart_id]
        if score_charts:
            chart_placements[score_charts[0].chart_id] = {
                'row': 1, 'col': 1, 'width': 12, 'height': 2
            }
        
        # Feasibility radar - left half of second row
        radar_charts = [c for c in charts if c.chart_type == ChartType.RADAR_CHART]
        if radar_charts:
            chart_placements[radar_charts[0].chart_id] = {
                'row': 3, 'col': 1, 'width': 6, 'height': 2
            }
        
        # Resource allocation - right half of second row
        pie_charts = [c for c in charts if c.chart_type == ChartType.PIE_CHART]
        if pie_charts:
            chart_placements[pie_charts[0].chart_id] = {
                'row': 3, 'col': 7, 'width': 6, 'height': 2
            }
        
        # Timeline - full width at bottom
        timeline_charts = [c for c in charts if 'timeline' in c.chart_id or 'gantt' in c.chart_id]
        if timeline_charts:
            chart_placements[timeline_charts[0].chart_id] = {
                'row': 5, 'col': 1, 'width': 12, 'height': 2
            }
        
        return DashboardLayout(
            dashboard_id=f"decision_support_{kwargs.get('opportunity_id', 'default')}",
            title="Decision Support Dashboard",
            description="Comprehensive analysis for informed decision making",
            chart_placements=chart_placements,
            cross_filters=[c.chart_id for c in charts if InteractionType.CROSSFILTER in c.interactions],
            theme=VisualizationTheme.PROFESSIONAL
        )
    
    def _create_portfolio_layout(self, charts: List[ChartConfiguration], **kwargs) -> DashboardLayout:
        """Create layout for portfolio overview"""
        
        chart_placements = {}
        
        # Priority matrix - prominent position
        scatter_charts = [c for c in charts if c.chart_type == ChartType.SCATTER_PLOT]
        if scatter_charts:
            chart_placements[scatter_charts[0].chart_id] = {
                'row': 1, 'col': 1, 'width': 8, 'height': 3
            }
        
        # Summary stats - right sidebar
        summary_charts = [c for c in charts if 'summary' in c.chart_id]
        if summary_charts:
            chart_placements[summary_charts[0].chart_id] = {
                'row': 1, 'col': 9, 'width': 4, 'height': 3
            }
        
        # Resource conflicts heatmap - bottom section
        heatmap_charts = [c for c in charts if c.chart_type == ChartType.HEATMAP]
        if heatmap_charts:
            chart_placements[heatmap_charts[0].chart_id] = {
                'row': 4, 'col': 1, 'width': 12, 'height': 2
            }
        
        return DashboardLayout(
            dashboard_id="portfolio_overview",
            title="Portfolio Overview Dashboard", 
            description="High-level view of all opportunities and their relationships",
            chart_placements=chart_placements,
            cross_filters=[c.chart_id for c in charts],  # Enable cross-filtering for all charts
            theme=VisualizationTheme.MODERN
        )
    
    def _create_default_layout(self, charts: List[ChartConfiguration], **kwargs) -> DashboardLayout:
        """Create default grid layout"""
        
        chart_placements = {}
        charts_per_row = 2
        current_row = 1
        current_col = 1
        
        for i, chart in enumerate(charts):
            chart_placements[chart.chart_id] = {
                'row': current_row,
                'col': current_col,
                'width': 12 // charts_per_row,
                'height': 2
            }
            
            current_col += 12 // charts_per_row
            if current_col > 12:
                current_col = 1
                current_row += 2
        
        return DashboardLayout(
            dashboard_id="default_dashboard",
            title="Analysis Dashboard",
            description="Standard dashboard layout",
            chart_placements=chart_placements
        )

class AdvancedVisualizationFramework(BaseProcessor):
    """Main framework for advanced visualization generation and management"""
    
    def __init__(self):
        super().__init__()
        self.score_generator = ScoreVisualizationGenerator()
        self.resource_generator = ResourceVisualizationGenerator()
        self.interaction_engine = InteractiveVisualizationEngine()
        self.layout_engine = DashboardLayoutEngine()
    
    async def process(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Process visualization generation for profile"""
        try:
            logger.info(f"Generating advanced visualizations for profile {profile_id}")
            
            # Get recommendations data
            recommendations = kwargs.get('recommendations', [])
            if not recommendations:
                return {
                    'profile_id': profile_id,
                    'visualizations': [],
                    'dashboards': [],
                    'message': 'No recommendations available for visualization'
                }
            
            # Generate visualizations
            all_charts = []
            decision_support_viz = []
            
            # Generate charts for each recommendation
            for rec in recommendations:
                if isinstance(rec, DecisionRecommendation):
                    viz_set = await self.generate_decision_support_visualizations(rec)
                    all_charts.extend(viz_set['charts'])
                    decision_support_viz.append(viz_set)
            
            # Generate portfolio-level visualizations
            portfolio_charts = await self.generate_portfolio_visualizations(recommendations)
            all_charts.extend(portfolio_charts)
            
            # Create dashboard layouts
            dashboards = await self.create_visualization_dashboards(all_charts, recommendations)
            
            # Generate export configurations
            export_configs = await self.generate_export_configurations(all_charts, dashboards)
            
            return {
                'profile_id': profile_id,
                'visualizations': [self._serialize_chart(chart) for chart in all_charts],
                'dashboards': [self._serialize_dashboard(dashboard) for dashboard in dashboards],
                'decision_support': decision_support_viz,
                'export_configurations': export_configs,
                'summary': {
                    'total_charts': len(all_charts),
                    'total_dashboards': len(dashboards),
                    'interactive_features': sum(len(c.interactions) for c in all_charts)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in advanced visualization framework: {e}")
            return {
                'profile_id': profile_id,
                'visualizations': [],
                'dashboards': [],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def generate_decision_support_visualizations(self, recommendation: DecisionRecommendation) -> Dict[str, Any]:
        """Generate comprehensive decision support visualizations for a recommendation"""
        
        charts = []
        
        # Score breakdown chart
        score_chart = self.score_generator.generate_score_breakdown_chart(recommendation)
        charts.append(score_chart)
        
        # Feasibility radar chart
        feasibility_chart = self.score_generator.generate_feasibility_radar_chart(recommendation)
        charts.append(feasibility_chart)
        
        # Resource allocation pie chart
        resource_pie = self.resource_generator.generate_resource_allocation_pie(recommendation)
        charts.append(resource_pie)
        
        # Timeline Gantt chart
        timeline_chart = self.resource_generator.generate_timeline_gantt(recommendation)
        charts.append(timeline_chart)
        
        # Add interactivity to all charts
        interactive_charts = []
        for chart in charts:
            enhanced_chart = self.interaction_engine.enhance_chart_interactivity(chart)
            interactive_charts.append(enhanced_chart)
        
        # Create decision support layout
        layout = self.layout_engine.create_dashboard_layout(
            'decision_support', charts, opportunity_id=recommendation.opportunity_id
        )
        
        return {
            'recommendation_id': recommendation.opportunity_id,
            'charts': charts,
            'interactive_charts': interactive_charts,
            'layout': layout,
            'decision_summary': {
                'recommendation': recommendation.recommendation.value,
                'confidence': recommendation.confidence.value,
                'priority_score': recommendation.priority_score
            }
        }
    
    async def generate_portfolio_visualizations(self, recommendations: List[DecisionRecommendation]) -> List[ChartConfiguration]:
        """Generate portfolio-level visualizations"""
        
        portfolio_charts = []
        
        # Priority matrix scatter plot
        priority_matrix = self.score_generator.generate_priority_matrix_scatter(recommendations)
        portfolio_charts.append(priority_matrix)
        
        # Resource conflicts heatmap
        if len(recommendations) > 1:
            conflicts_heatmap = self.resource_generator.generate_resource_conflicts_heatmap(recommendations)
            portfolio_charts.append(conflicts_heatmap)
        
        # Recommendation distribution pie chart
        rec_distribution = self._generate_recommendation_distribution_chart(recommendations)
        portfolio_charts.append(rec_distribution)
        
        # Confidence vs Priority scatter
        confidence_scatter = self._generate_confidence_priority_scatter(recommendations)
        portfolio_charts.append(confidence_scatter)
        
        return portfolio_charts
    
    def _generate_recommendation_distribution_chart(self, recommendations: List[DecisionRecommendation]) -> ChartConfiguration:
        """Generate recommendation type distribution chart"""
        
        # Count recommendations by type
        rec_counts = defaultdict(int)
        for rec in recommendations:
            rec_counts[rec.recommendation.value] += 1
        
        distribution_data = [
            {'recommendation_type': rec_type, 'count': count}
            for rec_type, count in rec_counts.items()
        ]
        
        return ChartConfiguration(
            chart_id="recommendation_distribution",
            chart_type=ChartType.PIE_CHART,
            title="Recommendation Distribution",
            description="Distribution of recommendation types across all opportunities",
            data_source="recommendation_counts",
            x_axis="recommendation_type",
            y_axis="count",
            interactions=[InteractionType.HOVER_TOOLTIP, InteractionType.CLICK_DRILL_DOWN],
            tooltip_fields=["recommendation_type", "count"],
            options={
                'show_percentages': True,
                'show_labels': True,
                'legend_position': 'bottom'
            },
            metadata={'data': distribution_data}
        )
    
    def _generate_confidence_priority_scatter(self, recommendations: List[DecisionRecommendation]) -> ChartConfiguration:
        """Generate confidence vs priority scatter plot"""
        
        confidence_mapping = {
            DecisionConfidence.VERY_HIGH: 1.0,
            DecisionConfidence.HIGH: 0.8,
            DecisionConfidence.MEDIUM: 0.6,
            DecisionConfidence.LOW: 0.4,
            DecisionConfidence.VERY_LOW: 0.2
        }
        
        scatter_data = [
            {
                'opportunity_id': rec.opportunity_id,
                'confidence': confidence_mapping[rec.confidence],
                'priority_score': rec.priority_score,
                'recommendation': rec.recommendation.value,
                'strategic_value': rec.resource_allocation.strategic_value
            }
            for rec in recommendations
        ]
        
        return ChartConfiguration(
            chart_id="confidence_priority_scatter",
            chart_type=ChartType.SCATTER_PLOT,
            title="Confidence vs Priority Analysis",
            description="Relationship between decision confidence and priority scores",
            data_source="confidence_priority",
            x_axis="confidence",
            y_axis="priority_score",
            color_field="recommendation",
            size_field="strategic_value",
            interactions=[InteractionType.HOVER_TOOLTIP, InteractionType.BRUSH_SELECT],
            tooltip_fields=["opportunity_id", "confidence", "priority_score", "recommendation"],
            options={
                'x_axis_label': 'Decision Confidence',
                'y_axis_label': 'Priority Score',
                'size_range': [50, 200]
            },
            metadata={'data': scatter_data}
        )
    
    async def create_visualization_dashboards(self, 
                                            charts: List[ChartConfiguration],
                                            recommendations: List[DecisionRecommendation]) -> List[DashboardLayout]:
        """Create multiple dashboard layouts for different use cases"""
        
        dashboards = []
        
        # Decision support dashboards (one per high-priority recommendation)
        high_priority_recs = [r for r in recommendations if r.priority_score > 0.7]
        for rec in high_priority_recs[:3]:  # Limit to top 3
            decision_charts = [c for c in charts if rec.opportunity_id in c.chart_id]
            if decision_charts:
                dashboard = self.layout_engine.create_dashboard_layout(
                    'decision_support', decision_charts, opportunity_id=rec.opportunity_id
                )
                dashboards.append(dashboard)
        
        # Portfolio overview dashboard
        portfolio_charts = [c for c in charts if not any(r.opportunity_id in c.chart_id for r in recommendations)]
        if portfolio_charts:
            portfolio_dashboard = self.layout_engine.create_dashboard_layout(
                'portfolio_overview', portfolio_charts
            )
            dashboards.append(portfolio_dashboard)
        
        # Executive summary dashboard
        summary_charts = self._select_executive_summary_charts(charts, recommendations)
        executive_dashboard = self.layout_engine.create_dashboard_layout(
            'executive_summary', summary_charts
        )
        dashboards.append(executive_dashboard)
        
        return dashboards
    
    def _select_executive_summary_charts(self, 
                                       charts: List[ChartConfiguration],
                                       recommendations: List[DecisionRecommendation]) -> List[ChartConfiguration]:
        """Select charts for executive summary dashboard"""
        
        # Key charts for executive overview
        priority_charts = []
        
        # Priority matrix - most important for executives
        priority_matrix = next((c for c in charts if c.chart_id == "priority_matrix_scatter"), None)
        if priority_matrix:
            priority_charts.append(priority_matrix)
        
        # Recommendation distribution
        rec_dist = next((c for c in charts if c.chart_id == "recommendation_distribution"), None)
        if rec_dist:
            priority_charts.append(rec_dist)
        
        # Top recommendation's score breakdown
        if recommendations:
            top_rec = max(recommendations, key=lambda r: r.priority_score)
            top_score_chart = next((c for c in charts if f"score_breakdown_{top_rec.opportunity_id}" == c.chart_id), None)
            if top_score_chart:
                priority_charts.append(top_score_chart)
        
        return priority_charts
    
    async def generate_export_configurations(self, 
                                           charts: List[ChartConfiguration],
                                           dashboards: List[DashboardLayout]) -> Dict[str, Any]:
        """Generate export configurations for reports and presentations"""
        
        return {
            'formats': {
                'pdf_report': {
                    'format': 'pdf',
                    'layout': 'portrait',
                    'charts_per_page': 2,
                    'include_data_tables': True,
                    'include_methodology': True
                },
                'powerpoint': {
                    'format': 'pptx',
                    'slide_layout': 'title_content',
                    'one_chart_per_slide': True,
                    'include_speaker_notes': True
                },
                'excel_workbook': {
                    'format': 'xlsx',
                    'include_raw_data': True,
                    'include_charts': True,
                    'separate_worksheets': True
                },
                'web_export': {
                    'format': 'html',
                    'interactive': True,
                    'responsive': True,
                    'offline_capable': True
                }
            },
            'chart_export_settings': {
                chart.chart_id: {
                    'high_res': True,
                    'vector_format': True,
                    'include_legend': True,
                    'transparent_background': False
                }
                for chart in charts
            },
            'dashboard_export_settings': {
                dashboard.dashboard_id: {
                    'full_page': True,
                    'preserve_interactivity': True,
                    'include_filters': True
                }
                for dashboard in dashboards
            }
        }
    
    def _serialize_chart(self, chart: ChartConfiguration) -> Dict[str, Any]:
        """Serialize chart configuration for JSON output"""
        return {
            'chart_id': chart.chart_id,
            'chart_type': chart.chart_type.value,
            'title': chart.title,
            'description': chart.description,
            'data_source': chart.data_source,
            'axes': {
                'x_axis': chart.x_axis,
                'y_axis': chart.y_axis,
                'color_field': chart.color_field,
                'size_field': chart.size_field
            },
            'styling': {
                'theme': chart.theme.value,
                'color_palette': chart.color_palette,
                'dimensions': {'width': chart.width, 'height': chart.height},
                'margin': chart.margin
            },
            'interactions': [interaction.value for interaction in chart.interactions],
            'tooltip_fields': chart.tooltip_fields,
            'options': chart.options,
            'data_preview': chart.metadata.get('data', [])[:5] if 'data' in chart.metadata else []
        }
    
    def _serialize_dashboard(self, dashboard: DashboardLayout) -> Dict[str, Any]:
        """Serialize dashboard layout for JSON output"""
        return {
            'dashboard_id': dashboard.dashboard_id,
            'title': dashboard.title,
            'description': dashboard.description,
            'grid_config': {
                'columns': dashboard.grid_columns,
                'rows': dashboard.grid_rows
            },
            'chart_placements': dashboard.chart_placements,
            'responsive_config': {
                'breakpoints': dashboard.breakpoints
            },
            'interactivity': {
                'cross_filters': dashboard.cross_filters,
                'linked_interactions': dashboard.linked_interactions
            },
            'theme': dashboard.theme.value
        }

# Export main components
__all__ = [
    'AdvancedVisualizationFramework',
    'ChartConfiguration',
    'DashboardLayout', 
    'DecisionSupportVisualization',
    'ChartType',
    'InteractionType',
    'VisualizationTheme'
]