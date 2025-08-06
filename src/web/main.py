#!/usr/bin/env python3
"""
Catalynx - Modern Web Interface
FastAPI backend with real-time progress monitoring
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import uvicorn

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.workflow_engine import get_workflow_engine
from src.core.data_models import WorkflowConfig
from src.web.services.workflow_service import WorkflowService
from src.web.services.progress_service import ProgressService
from src.web.models.requests import ClassificationRequest, WorkflowRequest
from src.web.models.responses import DashboardStats, WorkflowResponse, SystemStatus
from src.profiles.service import ProfileService
from src.profiles.models import OrganizationProfile, FundingType
from src.profiles.workflow_integration import ProfileWorkflowIntegrator
from src.pipeline.pipeline_engine import ProcessingPriority
from src.pipeline.resource_allocator import resource_allocator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Catalynx - Grant Research Automation",
    description="Modern web interface for intelligent grant research and classification",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
workflow_service = WorkflowService()
progress_service = ProgressService()
profile_service = ProfileService()
profile_integrator = ProfileWorkflowIntegrator()

# Serve static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Root endpoint - serve main interface
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard interface."""
    html_file = Path(__file__).parent / "static" / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    else:
        return HTMLResponse("""
        <html>
            <head><title>Catalynx - Loading...</title></head>
            <body>
                <h1>Catalynx Dashboard</h1>
                <p>Setting up the modern interface...</p>
                <p>Static files will be served from /static/</p>
            </body>
        </html>
        """)

# Dashboard API endpoints
@app.get("/api/dashboard/overview")
async def dashboard_overview() -> DashboardStats:
    """Get dashboard overview statistics."""
    try:
        engine = get_workflow_engine()
        stats = engine.get_workflow_statistics()
        
        return DashboardStats(
            active_workflows=stats.get('active_workflows', 0),
            total_processed=stats.get('total_processed', 0),
            success_rate=stats.get('success_rate', 0.0),
            recent_workflows=stats.get('recent_workflows', [])
        )
    except Exception as e:
        logger.error(f"Failed to get dashboard overview: {e}")
        # Return safe defaults instead of throwing error
        return DashboardStats(
            active_workflows=0,
            total_processed=0,
            success_rate=0.0,
            recent_workflows=[]
        )

@app.get("/api/system/status")
async def system_status() -> SystemStatus:
    """Get system health status."""
    try:
        engine = get_workflow_engine()
        processors = engine.registry.list_processors()
        
        return SystemStatus(
            status="healthy",
            processors_available=len(processors),
            uptime=datetime.now().isoformat(),
            version="2.0.0"
        )
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return SystemStatus(
            status="degraded",
            processors_available=0,
            uptime=datetime.now().isoformat(),
            version="2.0.0",
            error=str(e)
        )

# Classification API endpoints
@app.post("/api/classification/start")
async def start_classification(request: ClassificationRequest) -> WorkflowResponse:
    """Start intelligent classification with real-time progress."""
    try:
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
        logger.error(f"Failed to start classification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/classification/{workflow_id}/results")
async def get_classification_results(workflow_id: str, limit: Optional[int] = 100):
    """Get classification results for a workflow."""
    try:
        results = await workflow_service.get_classification_results(workflow_id, limit)
        return results
    except Exception as e:
        logger.error(f"Failed to get classification results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Workflow API endpoints
@app.post("/api/workflows/start")
async def start_workflow(request: WorkflowRequest) -> WorkflowResponse:
    """Start a complete workflow with real-time progress."""
    try:
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
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workflows")
async def list_workflows():
    """List all workflows."""
    try:
        engine = get_workflow_engine()
        workflows = engine.list_workflows()
        return {"workflows": workflows}
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        # Return empty list instead of error to prevent frontend crashes
        return {"workflows": []}

@app.get("/api/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get detailed workflow status."""
    try:
        status = await workflow_service.get_workflow_status(workflow_id)
        return status
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time progress
@app.websocket("/api/live/progress/{workflow_id}")
async def websocket_progress(websocket: WebSocket, workflow_id: str):
    """WebSocket endpoint for real-time progress updates."""
    await websocket.accept()
    
    try:
        # Add connection to progress service
        await progress_service.connect(workflow_id, websocket)
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages (ping/pong, etc.)
                data = await websocket.receive_text()
                
                # Handle ping requests
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        logger.error(f"WebSocket error for {workflow_id}: {e}")
    finally:
        # Remove connection
        await progress_service.disconnect(workflow_id, websocket)

# Export endpoints
@app.get("/api/exports/classification/{workflow_id}")
async def export_classification(workflow_id: str, format: str = "csv"):
    """Export classification results."""
    try:
        file_path = await workflow_service.export_classification_results(workflow_id, format)
        return FileResponse(
            path=file_path,
            filename=f"classification_{workflow_id}.{format}",
            media_type="application/octet-stream"
        )
    except Exception as e:
        logger.error(f"Failed to export classification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/exports/workflow/{workflow_id}")
async def export_workflow(workflow_id: str, format: str = "csv"):
    """Export workflow results."""
    try:
        file_path = await workflow_service.export_workflow_results(workflow_id, format)
        return FileResponse(
            path=file_path,
            filename=f"workflow_{workflow_id}.{format}",
            media_type="application/octet-stream"
        )
    except Exception as e:
        logger.error(f"Failed to export workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Profile Management API endpoints
@app.get("/api/profiles")
async def list_profiles(status: Optional[str] = None, limit: Optional[int] = None):
    """List all organization profiles."""
    try:
        profiles = profile_service.list_profiles(
            status=status,
            limit=limit
        )
        
        # Add opportunity counts (placeholder for now)
        for profile in profiles:
            profile.opportunities_count = 0  # TODO: Get actual count from leads
        
        return {"profiles": [p.dict() for p in profiles]}
        
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profiles")
async def create_profile(profile_data: Dict[str, Any]):
    """Create a new organization profile."""
    try:
        profile = profile_service.create_profile(profile_data)
        return {"profile": profile.dict(), "message": "Profile created successfully"}
        
    except Exception as e:
        logger.error(f"Failed to create profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/{profile_id}")
async def get_profile(profile_id: str):
    """Get a specific organization profile."""
    try:
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {"profile": profile.dict()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/profiles/{profile_id}")
async def update_profile(profile_id: str, update_data: Dict[str, Any]):
    """Update an existing organization profile."""
    try:
        profile = profile_service.update_profile(profile_id, update_data)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {"profile": profile.dict(), "message": "Profile updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    """Delete (archive) an organization profile."""
    try:
        success = profile_service.delete_profile(profile_id)
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {"message": "Profile archived successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profiles/templates")
async def create_profile_template(template_request: Dict[str, Any]):
    """Create a profile template."""
    try:
        template_name = template_request.get("template_name")
        template_data = template_request.get("template_data")
        
        if not template_name or not template_data:
            raise HTTPException(status_code=400, detail="template_name and template_data required")
        
        template = profile_service.create_template(template_data, template_name)
        return {"template": template.dict(), "message": "Template created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/{profile_id}/analytics")
async def get_profile_analytics(profile_id: str):
    """Get analytics for a specific profile."""
    try:
        analytics = profile_service.get_profile_analytics(profile_id)
        if not analytics:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {"analytics": analytics}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile analytics {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/{profile_id}/leads")
async def get_profile_leads(profile_id: str, stage: Optional[str] = None, min_score: Optional[float] = None):
    """Get opportunity leads for a profile."""
    try:
        from src.profiles.models import PipelineStage
        
        # Convert stage parameter if provided
        pipeline_stage = None
        if stage:
            try:
                pipeline_stage = PipelineStage(stage)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")
        
        leads = profile_service.get_profile_leads(
            profile_id=profile_id,
            stage=pipeline_stage,
            min_score=min_score
        )
        
        return {
            "profile_id": profile_id,
            "total_leads": len(leads),
            "leads": [lead.dict() for lead in leads],
            "filters_applied": {
                "stage": stage,
                "min_score": min_score
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get leads for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profiles/{profile_id}/discover")
async def discover_opportunities(profile_id: str, discovery_params: Dict[str, Any]):
    """Initiate opportunity discovery for a profile using multi-track approach."""
    try:
        # Parse funding types from request
        funding_type_strings = discovery_params.get("funding_types", ["grants"])
        funding_types = []
        
        for ft_str in funding_type_strings:
            try:
                funding_types.append(FundingType(ft_str))
            except ValueError:
                logger.warning(f"Invalid funding type: {ft_str}")
        
        if not funding_types:
            funding_types = [FundingType.GRANTS]  # Default fallback
        
        max_results = discovery_params.get("max_results", 100)
        
        # Execute profile-driven discovery
        discovery_results = await profile_integrator.discover_opportunities_for_profile(
            profile_id=profile_id,
            funding_types=funding_types,
            max_results_per_type=max_results
        )
        
        # Store results as opportunity leads
        opportunities = []
        for funding_type, results in discovery_results["results"].items():
            if results.get("status") == "completed":
                for opp in results.get("opportunities", []):
                    # Convert to opportunity lead and store
                    lead_data = {
                        "organization_name": opp["organization_name"],
                        "opportunity_type": opp["opportunity_type"],
                        "description": opp.get("description", ""),
                        "funding_amount": opp.get("funding_amount"),
                        "compatibility_score": opp.get("compatibility_score", 0.0),
                        "match_factors": opp.get("match_factors", {}),
                        "external_data": opp.get("metadata", {})
                    }
                    
                    # Add lead to profile
                    lead = profile_service.add_opportunity_lead(profile_id, lead_data)
                    if lead:
                        opportunities.append(lead.dict())
        
        return {
            "message": f"Discovery completed for profile {profile_id}",
            "discovery_id": discovery_results.get("discovery_timestamp", ""),
            "status": "completed",
            "summary": discovery_results.get("summary", {}),
            "total_opportunities_found": len(opportunities),
            "opportunities_by_type": {
                ft: len([o for o in opportunities if o.get("opportunity_type") == ft])
                for ft in funding_type_strings
            },
            "top_matches": discovery_results.get("summary", {}).get("top_matches", [])[:5]
        }
        
    except Exception as e:
        logger.error(f"Failed to discover opportunities for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profiles/{profile_id}/pipeline")
async def execute_full_pipeline(profile_id: str, pipeline_params: Dict[str, Any]):
    """Execute complete 4-stage processing pipeline for a profile."""
    try:
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
            progress_callback=None  # TODO: WebSocket progress integration
        )
        
        return {
            "message": f"Pipeline execution completed for profile {profile_id}",
            "pipeline_results": pipeline_results
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute pipeline for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pipeline/status")
async def get_pipeline_status():
    """Get overall pipeline system status and resource allocation."""
    try:
        resource_status = resource_allocator.get_resource_status()
        optimization = resource_allocator.optimize_resource_allocation()
        
        return {
            "system_status": "operational",
            "resource_allocation": resource_status,
            "optimization_analysis": optimization,
            "last_check": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get pipeline status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Catalynx API",
        "version": "2.0.0"
    }

# Simple test endpoint for debugging
@app.get("/api/test")
async def api_test():
    """Simple test endpoint to verify API connectivity."""
    return {
        "message": "API is working correctly",
        "timestamp": datetime.now().isoformat(),
        "endpoints_available": [
            "/api/health",
            "/api/system/status", 
            "/api/dashboard/overview",
            "/api/workflows",
            "/api/test"
        ]
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Catalynx Web Interface...")
    logger.info("Registering processors...")
    
    # Auto-register processors
    try:
        from src.processors.registry import register_all_processors
        registered_count = register_all_processors()
        logger.info(f"Registered {registered_count} processors")
    except Exception as e:
        logger.warning(f"Failed to auto-register processors: {e}")
    
    logger.info("Catalynx API ready!")

if __name__ == "__main__":
    # Run the application
    import uvicorn
    print("Starting Catalynx Web Interface on http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )