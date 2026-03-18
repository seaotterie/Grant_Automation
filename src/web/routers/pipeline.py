"""Pipeline, Commercial, State, Analytics, and Processor endpoints.

Extracted from main.py to reduce monolith size.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Pipeline & Processors"])


# ---------------------------------------------------------------------------
# Pipeline endpoints
# ---------------------------------------------------------------------------

@router.post("/profiles/{profile_id}/pipeline")
async def execute_full_pipeline(profile_id: str, pipeline_params: Dict[str, Any]):
    """Execute complete 4-stage processing pipeline for a profile."""
    try:
        from src.profiles.models import FundingType
        from src.pipeline.pipeline_engine import ProcessingPriority
        from src.profiles.workflow_integration import ProfileWorkflowIntegrator

        profile_integrator = ProfileWorkflowIntegrator()

        # Parse parameters
        funding_type_strings = pipeline_params.get("funding_types", ["grants"])
        funding_types = []

        for ft_str in funding_type_strings:
            try:
                funding_types.append(FundingType(ft_str))
            except ValueError:
                logger.warning(f"Invalid funding type: {ft_str}")

        if not funding_types:
            funding_types = [FundingType.GRANTS]

        priority_str = pipeline_params.get("priority", "standard")
        try:
            priority = ProcessingPriority(priority_str)
        except ValueError:
            priority = ProcessingPriority.STANDARD

        # Execute full pipeline
        pipeline_results = await profile_integrator.execute_full_pipeline(
            profile_id=profile_id,
            funding_types=funding_types,
            priority=priority,
            # WebSocket progress integration available through workflow state
            progress_callback=None  # WebSocket updates handled by workflow state
        )

        return {
            "message": f"Pipeline execution completed for profile {profile_id}",
            "pipeline_results": pipeline_results
        }

    except ValueError as e:
        logger.warning(f"Pipeline validation error for profile {profile_id}: {e}")
        raise HTTPException(status_code=404, detail="Resource not found")
    except Exception as e:
        logger.error(f"Failed to execute pipeline for profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pipeline/status")
async def get_pipeline_status():
    """Get overall pipeline system status and resource allocation."""
    try:
        from src.pipeline.resource_allocator import resource_allocator

        resource_status = resource_allocator.get_resource_status()
        optimization = resource_allocator.optimize_resource_allocation()

        return {
            "system_status": "operational",
            "resource_allocation": resource_status,
            "optimization_analysis": optimization,
            "last_check": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get pipeline status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Commercial Track API endpoints
# ---------------------------------------------------------------------------

@router.post("/commercial/discover")
async def discover_commercial_opportunities(request: Dict[str, Any]):
    """Start commercial opportunity discovery with filters."""
    try:
        from src.discovery.commercial_discoverer import CommercialDiscoverer

        discoverer = CommercialDiscoverer()

        # Mock search params based on request
        search_params = {
            'industries': request.get('industries', []),
            'company_sizes': request.get('company_sizes', []),
            'funding_range': request.get('funding_range', {}),
            'geographic_scope': request.get('geographic_scope', []),
            'partnership_types': request.get('partnership_types', [])
        }

        # For now, return mock results - in production this would call discoverer
        mock_opportunities = [
            {
                "id": "corp_001",
                "organization_name": "Microsoft Corporation Foundation",
                "program_name": "STEM Education Grant Program",
                "opportunity_type": "corporate_foundation",
                "funding_amount": 150000,
                "compatibility_score": 0.87,
                "description": "Supporting technology education initiatives in underserved communities",
                "application_deadline": "2025-06-30",
                "contact_info": {"email": "grants@microsoft.com", "type": "foundation"},
                "match_factors": {
                    "industry_alignment": True,
                    "csr_focus_match": True,
                    "geographic_presence": True,
                    "partnership_potential": True
                }
            }
        ]

        return {
            "status": "completed",
            "total_found": len(mock_opportunities),
            "opportunities": mock_opportunities,
            "search_params": search_params,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Commercial discovery failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/commercial/industries")
async def get_available_industries():
    """Get list of available industries for commercial discovery."""
    return {
        "industries": [
            {"value": "technology", "label": "Technology"},
            {"value": "healthcare", "label": "Healthcare"},
            {"value": "financial_services", "label": "Financial Services"},
            {"value": "retail", "label": "Retail"},
            {"value": "manufacturing", "label": "Manufacturing"},
            {"value": "energy", "label": "Energy"}
        ]
    }


# ---------------------------------------------------------------------------
# State Discovery API endpoints
# ---------------------------------------------------------------------------

@router.post("/states/discover")
async def discover_state_opportunities(request: Dict[str, Any]):
    """Start state-level opportunity discovery."""
    try:
        from src.discovery.state_discoverer import StateDiscoverer

        selected_states = request.get('states', ['VA'])

        # Mock results for now - in production would call state discoverer
        mock_opportunities = [
            {
                "id": "va_001",
                "agency_name": "Virginia Department of Health",
                "program_name": "Community Health Improvement Grants",
                "opportunity_type": "state_grant",
                "funding_amount": 125000,
                "priority_score": 0.89,
                "description": "Grants to support community-based health improvement initiatives",
                "application_deadline": "2025-05-15",
                "state": "VA",
                "focus_areas": ["public_health", "community_wellness"],
                "eligibility": "Virginia-based nonprofits"
            }
        ]

        return {
            "status": "completed",
            "total_found": len(mock_opportunities),
            "opportunities": mock_opportunities,
            "selected_states": selected_states,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"State discovery failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Analytics API endpoints
# ---------------------------------------------------------------------------

@router.get("/analytics/overview")
async def get_analytics_overview():
    """Get analytics overview data for dashboard."""
    try:
        # Mock analytics data - in production would calculate from real data
        return {
            "metrics": {
                "organizations_analyzed": 156,
                "avg_risk_score": 0.68,
                "low_risk_count": 89,
                "grant_ready_count": 124,
                "market_health": "good"
            },
            "trends": {
                "revenue_growth": [
                    {"year": 2020, "value": 2000000},
                    {"year": 2021, "value": 2200000},
                    {"year": 2022, "value": 2500000},
                    {"year": 2023, "value": 2800000}
                ],
                "success_rate": [
                    {"month": "Jan", "rate": 0.72},
                    {"month": "Feb", "rate": 0.75},
                    {"month": "Mar", "rate": 0.78},
                    {"month": "Apr", "rate": 0.81}
                ]
            },
            "risk_distribution": {
                "low": 45,
                "moderate": 32,
                "high": 18,
                "very_high": 5
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get analytics overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics/trends")
async def get_trend_analysis():
    """Get trend analysis data."""
    try:
        return {
            "financial_trends": [
                {
                    "organization": "Example Org 1",
                    "growth_rate": 0.12,
                    "stability_score": 0.85,
                    "classification": "accelerating"
                },
                {
                    "organization": "Example Org 2",
                    "growth_rate": 0.08,
                    "stability_score": 0.72,
                    "classification": "steady_growth"
                }
            ],
            "market_analysis": {
                "total_market_size": 25000000,
                "competitive_health": "good",
                "growth_potential": "high"
            }
        }
    except Exception as e:
        logger.error(f"Failed to get trend analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Processor Management API endpoints
# ---------------------------------------------------------------------------

@router.get("/processors")
async def list_processors():
    """List all available processors with status."""
    try:
        from src.processors.registry import get_processor_summary

        summary = get_processor_summary()
        return {
            "status": "success",
            "processors": summary["processors_info"],
            "total_count": summary["total_processors"],
            "by_type": summary["by_type"]
        }
    except Exception as e:
        logger.error(f"Failed to get processors: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/processors/architecture/overview")
async def get_processor_architecture_overview():
    """Get comprehensive overview of processor architecture and migration status."""
    try:
        from src.processors.registry import get_architecture_overview
        overview = get_architecture_overview()

        return {
            "status": "success",
            "architecture_overview": overview,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get architecture overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/processors/migration/status")
async def get_migration_status():
    """Get detailed migration status for client architecture integration."""
    try:
        from src.processors.registry import get_processor_summary
        summary = get_processor_summary()

        # Extract migration-specific information
        architecture_stats = summary.get('architecture_stats', {})
        migration_insights = summary.get('migration_insights', {})

        return {
            "status": "success",
            "migration_status": {
                "overall_completion": architecture_stats.get('migration_completion', 0),
                "processors_migrated": architecture_stats.get('client_integrated', 0),
                "total_processors": architecture_stats.get('total_processors', 0),
                "data_collection_progress": {
                    "total": migration_insights.get('data_collection_total', 0),
                    "migrated": migration_insights.get('data_collection_migrated', 0),
                    "completion_rate": migration_insights.get('data_collection_migration_rate', 0)
                },
                "priority_processors": migration_insights.get('priority_processors_status', {}),
                "architecture_benefits": migration_insights.get('architecture_benefits', [])
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get migration status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/processors/{processor_name}/status")
async def get_processor_status(processor_name: str):
    """Get detailed status for a specific processor."""
    try:
        from src.core.workflow_engine import get_workflow_engine

        engine = get_workflow_engine()
        info = engine.registry.get_processor_info(processor_name)
        if not info:
            raise HTTPException(status_code=404, detail="Processor not found")
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processor status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/processors/{processor_name}/execute")
async def execute_processor(processor_name: str, request: Dict[str, Any]):
    """Execute a specific processor with parameters."""
    try:
        from src.core.workflow_engine import get_workflow_engine
        from src.core.data_models import WorkflowConfig, ProcessorConfig

        engine = get_workflow_engine()

        # Get processor instance
        processor = engine.registry.get_processor(processor_name)
        if not processor:
            raise HTTPException(status_code=404, detail="Processor not found")

        # Extract parameters from request
        params = request.get("parameters", {})
        input_data = request.get("input_data", [])

        # Execute processor
        workflow_config = WorkflowConfig(
            workflow_id=f"api_execution_{processor_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        processor_config = ProcessorConfig(
            workflow_id=workflow_config.workflow_id,
            processor_name=processor_name,
            workflow_config=workflow_config,
            input_data={"data": input_data},
            processor_specific_config=params
        )

        processor_result = await processor.execute(processor_config)
        result = processor_result.data.get("results", processor_result.data)

        return {
            "status": "success",
            "processor": processor_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute processor {processor_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
