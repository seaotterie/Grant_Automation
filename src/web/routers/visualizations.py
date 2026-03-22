#!/usr/bin/env python3
"""
Visualizations Router - Phase 6 Visualization Framework API Endpoints

Extracted from main.py to provide modular chart generation,
decision dashboards, chart export, and chart type listing.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Body

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/visualizations", tags=["Visualizations"])


@router.post("/generate-chart")
async def generate_chart(request_data: Dict[str, Any] = Body(...)):
    """
    Generate interactive charts using the advanced visualization framework

    Args:
        request_data: {
            "chart_type": "bar|line|pie|scatter|radar|heatmap|sankey|network|decision_tree",
            "data": dict,  # Chart data structure
            "config": dict (optional),  # Chart configuration
            "styling": dict (optional),  # Styling options
            "export_format": str (optional)  # "png"|"svg"|"html"|"json"
        }

    Returns:
        Chart data and configuration for frontend rendering
    """
    try:
        from src.visualization.advanced_visualization_framework import AdvancedVisualizationFramework

        logger.info(f"Generating chart: {request_data.get('chart_type', 'unknown')}")

        # Validate required fields
        if "chart_type" not in request_data or "data" not in request_data:
            raise HTTPException(status_code=400, detail="Missing required fields: chart_type, data")

        # Initialize visualization framework
        viz_framework = AdvancedVisualizationFramework()

        # Generate chart (this would use the actual visualization framework)
        chart_config = {
            'type': request_data['chart_type'],
            'data': request_data['data'],
            'options': request_data.get('config', {}),
            'styling': request_data.get('styling', {}),
            'responsive': True,
            'mobile_optimized': True
        }

        # Mock chart generation result
        chart_result = {
            "success": True,
            "chart_id": f"chart_{int(datetime.now().timestamp())}",
            "chart_type": request_data['chart_type'],
            "chart_config": chart_config,
            "data_points": len(request_data['data'].get('values', [])) if isinstance(request_data['data'], dict) else 0,
            "generated_timestamp": datetime.now().isoformat(),
            "export_formats": ["png", "svg", "html", "json"],
            "interactive_features": ["zoom", "pan", "hover", "click"],
            "mobile_optimized": True
        }

        # Add export URL if format specified
        if request_data.get('export_format'):
            export_format = request_data['export_format']
            chart_result['export_url'] = f"/api/visualizations/{chart_result['chart_id']}/export/{export_format}"

        return chart_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/decision-dashboard")
async def create_decision_dashboard(request_data: Dict[str, Any] = Body(...)):
    """
    Create interactive decision support dashboard

    Args:
        request_data: {
            "profile_id": str,
            "opportunity_id": str,
            "synthesis_data": dict,  # Decision synthesis results
            "dashboard_type": "overview|detailed|comparison",
            "customization": dict (optional)
        }

    Returns:
        Dashboard configuration with multiple visualizations
    """
    try:
        from src.visualization.advanced_visualization_framework import AdvancedVisualizationFramework

        logger.info(f"Creating decision dashboard for profile {request_data.get('profile_id')}")

        # Validate required fields
        required_fields = ["profile_id", "opportunity_id", "synthesis_data"]
        for field in required_fields:
            if field not in request_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Initialize visualization framework
        viz_framework = AdvancedVisualizationFramework()

        dashboard_type = request_data.get('dashboard_type', 'overview')
        synthesis_data = request_data['synthesis_data']

        # Generate dashboard components
        dashboard_components = []

        # 1. Decision Matrix Chart
        if 'synthesis_score' in synthesis_data and 'overall_confidence' in synthesis_data:
            dashboard_components.append({
                'component_id': 'decision_matrix',
                'chart_type': 'scatter',
                'title': 'Decision Matrix',
                'data': {
                    'x': [synthesis_data['synthesis_score']],
                    'y': [synthesis_data['overall_confidence']],
                    'labels': [request_data['opportunity_id']]
                },
                'layout': {'row': 1, 'col': 1, 'span': 1}
            })

        # 2. Stage Contributions Bar Chart
        if 'stage_contributions' in synthesis_data:
            stage_data = synthesis_data['stage_contributions']
            dashboard_components.append({
                'component_id': 'stage_contributions',
                'chart_type': 'bar',
                'title': 'Workflow Stage Contributions',
                'data': {
                    'labels': list(stage_data.keys()),
                    'values': list(stage_data.values())
                },
                'layout': {'row': 1, 'col': 2, 'span': 1}
            })

        # 3. Feasibility Radar Chart
        if 'feasibility_assessment' in synthesis_data:
            feasibility_data = synthesis_data['feasibility_assessment']
            dashboard_components.append({
                'component_id': 'feasibility_radar',
                'chart_type': 'radar',
                'title': 'Feasibility Assessment',
                'data': {
                    'dimensions': list(feasibility_data.keys()),
                    'scores': list(feasibility_data.values())
                },
                'layout': {'row': 2, 'col': 1, 'span': 2}
            })

        # 4. Risk Assessment Heatmap (if detailed dashboard)
        if dashboard_type == 'detailed' and 'risk_assessment' in synthesis_data:
            risks = synthesis_data['risk_assessment']
            dashboard_components.append({
                'component_id': 'risk_heatmap',
                'chart_type': 'heatmap',
                'title': 'Risk Assessment',
                'data': {
                    'risk_types': [r.get('risk_type', 'unknown') for r in risks],
                    'severities': [r.get('severity', 'low') for r in risks]
                },
                'layout': {'row': 3, 'col': 1, 'span': 2}
            })

        dashboard_result = {
            "success": True,
            "dashboard_id": f"dashboard_{request_data['profile_id']}_{int(datetime.now().timestamp())}",
            "profile_id": request_data['profile_id'],
            "opportunity_id": request_data['opportunity_id'],
            "dashboard_type": dashboard_type,
            "components": dashboard_components,
            "layout": {
                "grid_rows": 3 if dashboard_type == 'detailed' else 2,
                "grid_cols": 2,
                "responsive": True,
                "mobile_breakpoints": [768, 1024]
            },
            "interactive_features": [
                "drill_down", "cross_filtering", "real_time_updates",
                "export_charts", "parameter_adjustment"
            ],
            "generated_timestamp": datetime.now().isoformat(),
            "expires_in_hours": 24
        }

        return dashboard_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating decision dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{chart_id}/export/{format}")
async def export_chart(chart_id: str, format: str):
    """
    Export chart in specified format

    Args:
        chart_id: Unique chart identifier
        format: Export format (png, svg, html, json)

    Returns:
        File response or download information
    """
    try:
        # Validate format
        valid_formats = ['png', 'svg', 'html', 'json']
        if format not in valid_formats:
            raise HTTPException(status_code=400, detail=f"Invalid format. Must be one of: {valid_formats}")

        # Mock export generation
        export_filename = f"{chart_id}.{format}"

        return {
            "success": True,
            "chart_id": chart_id,
            "export_format": format,
            "filename": export_filename,
            "file_size": "245KB",  # Mock data
            "download_url": f"/api/exports/charts/{export_filename}",
            "generated_timestamp": datetime.now().isoformat(),
            "expires_in_hours": 2,
            "message": f"Chart exported successfully as {format.upper()}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting chart {chart_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/chart-types")
async def get_available_chart_types():
    """
    Get list of available chart types and their configurations

    Returns:
        Dictionary of chart types with their capabilities and requirements
    """
    try:
        chart_types = {
            "bar": {
                "name": "Bar Chart",
                "description": "Compare values across categories",
                "required_data": ["labels", "values"],
                "optional_data": ["colors", "groups"],
                "features": ["horizontal", "stacked", "grouped"],
                "best_for": ["categorical_data", "comparisons"]
            },
            "line": {
                "name": "Line Chart",
                "description": "Show trends over time or continuous data",
                "required_data": ["x_values", "y_values"],
                "optional_data": ["multiple_series", "confidence_intervals"],
                "features": ["interpolation", "markers", "area_fill"],
                "best_for": ["time_series", "trends", "continuous_data"]
            },
            "pie": {
                "name": "Pie Chart",
                "description": "Show proportions of a whole",
                "required_data": ["labels", "values"],
                "optional_data": ["colors", "explode"],
                "features": ["donut_mode", "percentage_labels"],
                "best_for": ["proportions", "percentages", "composition"]
            },
            "scatter": {
                "name": "Scatter Plot",
                "description": "Show relationships between two variables",
                "required_data": ["x_values", "y_values"],
                "optional_data": ["size", "color", "labels"],
                "features": ["trend_lines", "clusters", "size_mapping"],
                "best_for": ["correlations", "distributions", "relationships"]
            },
            "radar": {
                "name": "Radar Chart",
                "description": "Compare multiple dimensions simultaneously",
                "required_data": ["dimensions", "scores"],
                "optional_data": ["multiple_profiles", "fill_areas"],
                "features": ["multi_profile", "range_scaling"],
                "best_for": ["multi_dimensional_comparison", "profiles", "assessments"]
            },
            "heatmap": {
                "name": "Heatmap",
                "description": "Show intensity of values across two dimensions",
                "required_data": ["x_categories", "y_categories", "values"],
                "optional_data": ["color_scale", "annotations"],
                "features": ["color_scales", "clustering", "annotations"],
                "best_for": ["correlation_matrices", "density_visualization", "pattern_detection"]
            },
            "decision_tree": {
                "name": "Decision Tree",
                "description": "Visualize decision pathways and outcomes",
                "required_data": ["nodes", "edges", "outcomes"],
                "optional_data": ["probabilities", "costs"],
                "features": ["interactive_navigation", "outcome_highlighting"],
                "best_for": ["decision_analysis", "process_flows", "hierarchies"]
            }
        }

        return {
            "success": True,
            "chart_types": chart_types,
            "total_types": len(chart_types),
            "framework_version": "1.0.0_phase6",
            "capabilities": {
                "responsive_design": True,
                "mobile_optimization": True,
                "export_formats": ["png", "svg", "html", "json"],
                "interactive_features": ["zoom", "pan", "hover", "click", "drill_down"],
                "real_time_updates": True
            }
        }

    except Exception as e:
        logger.error(f"Error retrieving chart types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
