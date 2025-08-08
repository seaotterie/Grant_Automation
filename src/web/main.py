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
from src.processors.registry import get_processor_summary

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

# Commercial Track API endpoints
@app.post("/api/commercial/discover")
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
        logger.error(f"Commercial discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/commercial/industries")
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

# State Discovery API endpoints  
@app.post("/api/states/discover")
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
        logger.error(f"State discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics API endpoints
@app.get("/api/analytics/overview")
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
        logger.error(f"Failed to get analytics overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/trends")
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
        logger.error(f"Failed to get trend analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Processor Management API endpoints
@app.get("/api/processors")
async def list_processors():
    """List all available processors with status."""
    try:
        summary = get_processor_summary()
        return {
            "status": "success",
            "processors": summary["processors_info"],
            "total_count": summary["total_processors"],
            "by_type": summary["by_type"]
        }
    except Exception as e:
        logger.error(f"Failed to get processors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/processors/{processor_name}/status")
async def get_processor_status(processor_name: str):
    """Get detailed status for a specific processor."""
    try:
        engine = get_workflow_engine()
        info = engine.registry.get_processor_info(processor_name)
        if not info:
            raise HTTPException(status_code=404, detail="Processor not found")
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processor status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/processors/{processor_name}/execute")
async def execute_processor(processor_name: str, request: Dict[str, Any]):
    """Execute a specific processor with parameters."""
    try:
        engine = get_workflow_engine()
        
        # Get processor instance
        processor_class = engine.registry.get_processor(processor_name)
        if not processor_class:
            raise HTTPException(status_code=404, detail="Processor not found")
        
        processor = processor_class()
        
        # Extract parameters from request
        params = request.get("parameters", {})
        input_data = request.get("input_data", [])
        
        # Execute processor
        result = await processor.process_async(input_data, **params)
        
        return {
            "status": "success",
            "processor": processor_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute processor {processor_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# DISCOMBOBULATOR Track Endpoints
@app.post("/api/discovery/nonprofit")
async def discover_nonprofits(request: Dict[str, Any]):
    """Execute nonprofit discovery track (ProPublica + BMF + EIN lookup)."""
    try:
        logger.info("Starting nonprofit discovery track")
        
        # Execute nonprofit track processors
        engine = get_workflow_engine()
        
        # Get parameters
        state = request.get("state", "VA")
        ein = request.get("ein")
        max_results = request.get("max_results", 100)
        
        # Phase 1.3: Profile context integration
        profile_context = request.get("profile_context")
        focus_areas = request.get("focus_areas", [])
        target_populations = request.get("target_populations", [])
        
        if profile_context:
            logger.info(f"Using profile context for nonprofit discovery: {profile_context.get('name', 'Unknown')}")
            # Override parameters with profile-specific values
            if profile_context.get("geographic_scope", {}).get("states"):
                state = profile_context["geographic_scope"]["states"][0]
            if profile_context.get("focus_areas"):
                focus_areas.extend(profile_context["focus_areas"])
            if profile_context.get("target_populations"):
                target_populations.extend(profile_context["target_populations"])
        
        results = {"track": "nonprofit", "results": []}
        
        # Execute BMF filtering if no specific EIN
        if not ein:
            bmf_processor = engine.registry.get_processor("bmf_filter")
            if bmf_processor:
                bmf_instance = bmf_processor()
                bmf_results = await bmf_instance.process_async(
                    [], 
                    state=state, 
                    max_results=max_results,
                    focus_areas=focus_areas,
                    target_populations=target_populations,
                    profile_context=profile_context
                )
                results["bmf_results"] = bmf_results
        
        # Execute ProPublica fetch
        propublica_processor = engine.registry.get_processor("propublica_fetch")
        if propublica_processor:
            pp_instance = propublica_processor()
            if ein:
                pp_results = await pp_instance.process_async([{"ein": ein}])
            else:
                pp_results = await pp_instance.process_async(results.get("bmf_results", [])[:50])
            results["propublica_results"] = pp_results
        
        return {
            "status": "completed",
            "track": "nonprofit",
            "total_found": len(results.get("propublica_results", [])),
            "results": results,
            "profile_context": profile_context.get('name') if profile_context else None,
            "parameters_used": {
                "state": state,
                "max_results": max_results,
                "focus_areas": focus_areas,
                "target_populations": target_populations
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Nonprofit discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/discovery/federal")
async def discover_federal_opportunities(request: Dict[str, Any]):
    """Execute federal grants discovery (Grants.gov + USASpending)."""
    try:
        logger.info("Starting federal discovery track")
        
        # Get parameters
        keywords = request.get("keywords", [])
        opportunity_category = request.get("opportunity_category")
        max_results = request.get("max_results", 50)
        
        results = {"track": "federal", "results": []}
        
        # Execute Grants.gov fetch
        engine = get_workflow_engine()
        grants_processor = engine.registry.get_processor("grants_gov_fetch")
        if grants_processor:
            grants_instance = grants_processor()
            grants_results = await grants_instance.process_async(
                [], 
                keywords=keywords,
                opportunity_category=opportunity_category,
                max_results=max_results
            )
            results["grants_gov_results"] = grants_results
        
        # Execute USASpending fetch for historical context
        usaspending_processor = engine.registry.get_processor("usaspending_fetch")
        if usaspending_processor:
            usa_instance = usaspending_processor()
            usa_results = await usa_instance.process_async([], keywords=keywords)
            results["usaspending_results"] = usa_results
        
        return {
            "status": "completed",
            "track": "federal",
            "total_found": len(results.get("grants_gov_results", [])),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Federal discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/discovery/state")
async def discover_state_opportunities(request: Dict[str, Any]):
    """Execute state-level grants discovery."""
    try:
        logger.info("Starting state discovery track")
        
        # Get parameters
        states = request.get("states", ["VA"])
        focus_areas = request.get("focus_areas", [])
        max_results = request.get("max_results", 50)
        
        results = {"track": "state", "results": []}
        
        # Execute Virginia state grants fetch
        engine = get_workflow_engine()
        va_processor = engine.registry.get_processor("va_state_grants_fetch")
        if va_processor and "VA" in states:
            va_instance = va_processor()
            va_results = await va_instance.process_async(
                [], 
                focus_areas=focus_areas,
                max_results=max_results
            )
            results["virginia_results"] = va_results
        
        return {
            "status": "completed", 
            "track": "state",
            "total_found": len(results.get("virginia_results", [])),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"State discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/discovery/commercial")
async def discover_commercial_enhanced(request: Dict[str, Any]):
    """Execute commercial discovery (Foundation Directory + CSR Analysis)."""
    try:
        logger.info("Starting enhanced commercial discovery track")
        
        # Get parameters
        industries = request.get("industries", [])
        company_sizes = request.get("company_sizes", [])
        funding_range = request.get("funding_range", {})
        max_results = request.get("max_results", 50)
        
        results = {"track": "commercial", "results": []}
        
        engine = get_workflow_engine()
        
        # Execute Foundation Directory fetch
        foundation_processor = engine.registry.get_processor("foundation_directory_fetch")
        if foundation_processor:
            fd_instance = foundation_processor()
            fd_results = await fd_instance.process_async(
                [],
                industries=industries,
                funding_range=funding_range,
                max_results=max_results
            )
            results["foundation_results"] = fd_results
        
        # Execute CSR Analysis
        csr_processor = engine.registry.get_processor("corporate_csr_analyzer")
        if csr_processor:
            csr_instance = csr_processor()
            csr_results = await csr_instance.process_async(
                [],
                industries=industries,
                company_sizes=company_sizes
            )
            results["csr_results"] = csr_results
        
        return {
            "status": "completed",
            "track": "commercial", 
            "total_found": len(results.get("foundation_results", [])) + len(results.get("csr_results", [])),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Commercial discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AMPLINATOR Track Endpoints
@app.post("/api/analysis/scoring")
async def run_scoring_analysis(request: Dict[str, Any]):
    """Execute scoring analysis (Financial + Risk + Government Opportunity scoring)."""
    try:
        logger.info("Starting scoring analysis")
        
        # Get input organizations
        organizations = request.get("organizations", [])
        if not organizations:
            raise HTTPException(status_code=400, detail="Organizations required for scoring")
        
        results = {"track": "scoring", "results": {}}
        
        engine = get_workflow_engine()
        
        # Execute Financial Scoring
        financial_processor = engine.registry.get_processor("financial_scorer")
        if financial_processor:
            fs_instance = financial_processor()
            financial_results = await fs_instance.process_async(organizations)
            results["results"]["financial_scores"] = financial_results
        
        # Execute Risk Assessment
        risk_processor = engine.registry.get_processor("risk_assessor")
        if risk_processor:
            risk_instance = risk_processor()
            risk_results = await risk_instance.process_async(organizations)
            results["results"]["risk_assessments"] = risk_results
        
        # Execute Government Opportunity Scoring
        gov_scorer = engine.registry.get_processor("government_opportunity_scorer")
        if gov_scorer:
            gov_instance = gov_scorer()
            gov_results = await gov_instance.process_async(organizations)
            results["results"]["government_scores"] = gov_results
        
        return {
            "status": "completed",
            "track": "scoring",
            "organizations_analyzed": len(organizations),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scoring analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/network")
async def run_network_analysis(request: Dict[str, Any]):
    """Execute network analysis (Board connections + Strategic intelligence)."""
    try:
        logger.info("Starting network analysis")
        
        # Get input organizations
        organizations = request.get("organizations", [])
        if not organizations:
            raise HTTPException(status_code=400, detail="Organizations required for network analysis")
        
        results = {"track": "network", "results": {}}
        
        engine = get_workflow_engine()
        
        # Execute Board Network Analysis
        board_processor = engine.registry.get_processor("board_network_analyzer")
        if board_processor:
            board_instance = board_processor()
            board_results = await board_instance.process_async(organizations)
            results["results"]["board_networks"] = board_results
        
        # Execute Enhanced Network Analysis
        enhanced_processor = engine.registry.get_processor("enhanced_network_analyzer")
        if enhanced_processor:
            enhanced_instance = enhanced_processor()
            enhanced_results = await enhanced_instance.process_async(organizations)
            results["results"]["enhanced_networks"] = enhanced_results
        
        return {
            "status": "completed",
            "track": "network",
            "organizations_analyzed": len(organizations),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Network analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/export")
async def run_export_functions(request: Dict[str, Any]):
    """Execute export functions (All export/download processors)."""
    try:
        logger.info("Starting export functions")
        
        export_type = request.get("export_type", "results")
        export_params = request.get("parameters", {})
        
        engine = get_workflow_engine()
        
        # Execute Export Processor
        export_processor = engine.registry.get_processor("export_processor")
        if not export_processor:
            raise HTTPException(status_code=500, detail="Export processor not available")
        
        export_instance = export_processor()
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
        logger.error(f"Export functions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/reports")
async def run_report_generation(request: Dict[str, Any]):
    """Execute report generation processors."""
    try:
        logger.info("Starting report generation")
        
        report_type = request.get("report_type", "comprehensive")
        report_params = request.get("parameters", {})
        
        engine = get_workflow_engine()
        
        # Execute Report Generator
        report_processor = engine.registry.get_processor("report_generator")
        if not report_processor:
            raise HTTPException(status_code=500, detail="Report generator not available")
        
        report_instance = report_processor()
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
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/intelligence/classify")
async def run_intelligent_classification(request: Dict[str, Any]):
    """Execute intelligent classification analysis."""
    try:
        logger.info("Starting intelligent classification")
        
        # Get input organizations  
        organizations = request.get("organizations", [])
        state = request.get("state", "VA")
        min_score = request.get("min_score", 0.3)
        
        results = {"track": "classification", "results": {}}
        
        engine = get_workflow_engine()
        
        # Execute Intelligent Classification
        classifier = engine.registry.get_processor("intelligent_classifier")
        if classifier:
            classifier_instance = classifier()
            classification_results = await classifier_instance.process_async(
                organizations or [],
                state=state,
                min_score=min_score
            )
            results["results"]["classifications"] = classification_results
        
        return {
            "status": "completed",
            "track": "classification",
            "organizations_analyzed": len(organizations) if organizations else "discovery_mode",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Intelligent classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Multi-Track Pipeline Endpoint
@app.post("/api/pipeline/full-summary")
async def run_full_pipeline_summary(request: Dict[str, Any]):
    """Execute complete pipeline status overview across all tracks."""
    try:
        logger.info("Generating full pipeline summary")
        
        engine = get_workflow_engine()
        processor_summary = get_processor_summary()
        workflow_stats = engine.get_workflow_statistics()
        resource_status = resource_allocator.get_resource_status()
        
        return {
            "status": "completed",
            "summary_type": "full_pipeline",
            "system_overview": {
                "processors": processor_summary,
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
        logger.error(f"Full pipeline summary failed: {e}")
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