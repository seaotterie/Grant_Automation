"""
Classification & Workflows Router
API endpoints for classification, workflows, funnel stages, opportunities,
pipeline summary, analysis export, and report generation.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Optional, Any
from datetime import datetime
import asyncio
import logging

from src.web.models.requests import ClassificationRequest, WorkflowRequest
from src.web.models.responses import WorkflowResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Classification & Workflows"])


# === CLASSIFICATION ENDPOINTS ===

@router.post("/classification/start")
async def start_classification(request: ClassificationRequest) -> WorkflowResponse:
    """Start intelligent classification with real-time progress."""
    try:
        from src.web.services.workflow_service import WorkflowService
        from src.web.services.progress_service import ProgressService

        workflow_service = WorkflowService()
        progress_service = ProgressService()

        workflow_id = f"classification_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Start background task
        task = asyncio.create_task(
            workflow_service.run_classification_with_progress(
                workflow_id, request, progress_service.broadcast_progress
            )
        )

        return WorkflowResponse(
            workflow_id=workflow_id,
            status="started",
            message="Classification started successfully",
            started_at=datetime.now()
        )

    except Exception as e:
        logger.error(f"Failed to start classification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/classification/{workflow_id}/results")
async def get_classification_results(workflow_id: str, limit: Optional[int] = 100):
    """Get classification results for a workflow."""
    try:
        from src.web.services.workflow_service import WorkflowService

        workflow_service = WorkflowService()
        results = await workflow_service.get_classification_results(workflow_id, limit)
        return results
    except Exception as e:
        logger.error(f"Failed to get classification results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# === WORKFLOW ENDPOINTS ===

@router.post("/workflows/start")
async def start_workflow(request: WorkflowRequest) -> WorkflowResponse:
    """Start a complete workflow with real-time progress."""
    try:
        from src.core.data_models import WorkflowConfig
        from src.web.services.workflow_service import WorkflowService
        from src.web.services.progress_service import ProgressService

        workflow_service = WorkflowService()
        progress_service = ProgressService()

        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create workflow configuration
        config = WorkflowConfig(
            workflow_id=workflow_id,
            name=request.name or "API Workflow",
            target_ein=request.target_ein,
            states=request.states,
            ntee_codes=request.ntee_codes,
            min_revenue=request.min_revenue,
            max_results=request.max_results,
            include_classified_organizations=request.include_classified,
            classification_score_threshold=request.classification_threshold
        )

        # Start background workflow
        task = asyncio.create_task(
            workflow_service.run_workflow_with_progress(
                config, progress_service.broadcast_progress
            )
        )

        return WorkflowResponse(
            workflow_id=workflow_id,
            status="started",
            message="Workflow started successfully",
            started_at=datetime.now()
        )

    except Exception as e:
        logger.error(f"Failed to start workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/workflows")
async def list_workflows():
    """List all workflows."""
    try:
        from src.core.workflow_engine import get_workflow_engine

        engine = get_workflow_engine()
        workflows = engine.list_workflows()
        return {"workflows": workflows}
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        # Return empty list instead of error to prevent frontend crashes
        return {"workflows": []}


@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get detailed workflow status."""
    try:
        from src.web.services.workflow_service import WorkflowService

        workflow_service = WorkflowService()
        status = await workflow_service.get_workflow_status(workflow_id)
        return status
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# === FUNNEL & OPPORTUNITIES ENDPOINTS ===

@router.get("/funnel/stages")
async def get_funnel_stages():
    """Get all funnel stage definitions."""
    from src.discovery.base_discoverer import FunnelStage

    stages = []
    for stage in FunnelStage:
        stages.append({
            "value": stage.value,
            "name": stage.value.replace('_', ' ').title(),
            "color": {
                "prospects": "gray",
                "qualified_prospects": "yellow",
                "candidates": "orange",
                "targets": "blue",
                "opportunities": "green"
            }.get(stage.value, "gray")
        })

    return {"stages": stages}


@router.get("/opportunities")
async def get_opportunities(profile_id: Optional[str] = None, scope: Optional[str] = None, stage: Optional[str] = None):
    """Get opportunities with profile scoping and filtering for real data integration."""
    try:
        logger.info(f"Getting opportunities - profile_id: {profile_id}, scope: {scope}, stage: {stage}")

        # Enhanced mock opportunities with profile associations for development
        base_opportunities = [
            {
                "opportunity_id": "unified_opp_001",
                "organization_name": "Metropolitan Health Foundation",
                "source_type": "Nonprofit",
                "discovery_source": "nonprofit_discovery",
                "description": "Leading health advocacy organization focused on community wellness and preventive care programs.",
                "funnel_stage": "prospects",
                "raw_score": 0.72,
                "compatibility_score": 0.68,
                "confidence_level": 0.85,
                "xml_990_score": 0.0,
                "network_score": 0.0,
                "enhanced_score": 0.0,
                "combined_score": 0.68,
                "discovered_at": "2024-01-15T10:30:00Z",
                "discovered_for_profile": "demo_profile_001",
                "analysis_context": {
                    "profile_id": "demo_profile_001",
                    "discovery_mode": "nonprofit_track",
                    "ntee_matches": ["E", "P"],
                    "focus_area_matches": ["health", "community"]
                }
            },
            {
                "opportunity_id": "unified_opp_002",
                "organization_name": "Regional Education Alliance",
                "source_type": "Nonprofit",
                "discovery_source": "nonprofit_discovery",
                "description": "Consortium of educational institutions promoting STEM learning and digital literacy.",
                "funnel_stage": "qualified",
                "raw_score": 0.85,
                "compatibility_score": 0.82,
                "confidence_level": 0.90,
                "xml_990_score": 0.0,
                "network_score": 0.0,
                "enhanced_score": 0.0,
                "combined_score": 0.82,
                "discovered_at": "2024-01-15T11:45:00Z",
                "discovered_for_profile": "demo_profile_001",
                "analysis_context": {
                    "profile_id": "demo_profile_001",
                    "discovery_mode": "government_track",
                    "ntee_matches": ["B"],
                    "focus_area_matches": ["education", "STEM"]
                }
            },
            {
                "opportunity_id": "unified_opp_003",
                "organization_name": "Tech Innovation Fund",
                "source_type": "Commercial",
                "discovery_source": "foundation_directory",
                "description": "Corporate foundation supporting technology startups and digital innovation projects.",
                "funnel_stage": "candidates",
                "raw_score": 0.78,
                "compatibility_score": 0.75,
                "confidence_level": 0.88,
                "xml_990_score": 0.0,
                "network_score": 0.0,
                "enhanced_score": 0.0,
                "combined_score": 0.75,
                "discovered_at": "2024-01-15T14:20:00Z",
                "discovered_for_profile": "demo_profile_002",
                "analysis_context": {
                    "profile_id": "demo_profile_002",
                    "discovery_mode": "commercial_track",
                    "ntee_matches": ["M", "T"],
                    "focus_area_matches": ["technology", "innovation"]
                }
            }
        ]

        # Apply profile scoping if specified
        filtered_opportunities = base_opportunities
        if profile_id:
            filtered_opportunities = [
                opp for opp in filtered_opportunities
                if opp.get("discovered_for_profile") == profile_id or
                   opp.get("analysis_context", {}).get("profile_id") == profile_id
            ]

        # Apply stage filtering if specified
        if stage:
            stages = [s.strip() for s in stage.split(',')]
            filtered_opportunities = [opp for opp in filtered_opportunities if opp["funnel_stage"] in stages]

        # Apply scope filtering (all=return everything, focused=apply additional filtering)
        if scope == "focused" and profile_id:
            # In real implementation, this would apply advanced matching logic
            # For now, return profile-scoped results
            pass

        return {
            "profile_id": profile_id,
            "scope": scope,
            "stage_filter": stage,
            "total_count": len(filtered_opportunities),
            "opportunities": filtered_opportunities,
            "metadata": {
                "data_source": "mock_development",
                "profile_scoped": profile_id is not None,
                "filtered": stage is not None,
                "last_updated": datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Error getting opportunities: {str(e)}")
        logger.error(f"Internal server error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# === PIPELINE & ANALYSIS ENDPOINTS ===

@router.post("/pipeline/full-summary")
async def run_full_pipeline_summary(request: Dict[str, Any]):
    """Execute complete pipeline status overview across all tracks."""
    try:
        from src.core.workflow_engine import get_workflow_engine
        from src.core.tool_registry import get_tool_summary
        from src.pipeline.resource_allocator import resource_allocator

        logger.info("Generating full pipeline summary")

        engine = get_workflow_engine()
        tool_summary = get_tool_summary()
        workflow_stats = engine.get_workflow_statistics()
        resource_status = resource_allocator.get_resource_status()

        return {
            "status": "completed",
            "summary_type": "full_pipeline",
            "system_overview": {
                "tools": tool_summary,
                "workflows": workflow_stats,
                "resources": resource_status,
                "uptime": datetime.now().isoformat()
            },
            "track_status": {
                "nonprofit_track": "operational",
                "federal_track": "operational",
                "state_track": "operational",
                "commercial_track": "operational",
                "intelligence_track": "operational"
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Full pipeline summary failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analysis/export")
async def run_export_functions(request: Dict[str, Any]):
    """Execute export functions (All export/download processors)."""
    try:
        from src.core.workflow_engine import get_workflow_engine

        logger.info("Starting export functions")

        export_type = request.get("export_type", "results")
        export_params = request.get("parameters", {})

        engine = get_workflow_engine()

        # Execute Export Processor
        export_instance = engine.registry.get_processor("export_processor")
        if not export_instance:
            raise HTTPException(status_code=500, detail="Export processor not available")
        export_context = {
            "export_type": export_type,
            **export_params
        }

        export_results = await export_instance.execute(export_context)

        return {
            "status": "completed",
            "track": "export",
            "export_type": export_type,
            "results": export_results,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export functions failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analysis/reports")
async def run_report_generation(request: Dict[str, Any]):
    """Execute report generation processors."""
    try:
        from src.core.workflow_engine import get_workflow_engine

        logger.info("Starting report generation")

        report_type = request.get("report_type", "comprehensive")
        report_params = request.get("parameters", {})

        engine = get_workflow_engine()

        # Execute Report Generator
        report_instance = engine.registry.get_processor("report_generator")
        if not report_instance:
            raise HTTPException(status_code=500, detail="Report generator not available")
        report_context = {
            "report_type": report_type,
            **report_params
        }

        report_results = await report_instance.execute(report_context)

        return {
            "status": "completed",
            "track": "reports",
            "report_type": report_type,
            "results": report_results,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
