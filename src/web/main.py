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
import uuid
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
from src.processors.lookup.ein_lookup import EINLookupProcessor

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

# Custom static file handler with cache control
@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    """Serve static files with cache control headers."""
    static_path = Path(__file__).parent / "static"
    full_path = static_path / file_path
    
    if full_path.exists() and full_path.is_file():
        # Add cache-busting headers for CSS and JS files
        if file_path.endswith(('.css', '.js')):
            headers = {
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        else:
            # Allow caching for images and other assets
            headers = {"Cache-Control": "public, max-age=3600"}
        
        return FileResponse(full_path, headers=headers)
    else:
        raise HTTPException(status_code=404, detail="File not found")

# Serve static files (fallback for non-cached files)
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Root endpoint - serve main interface
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard interface."""
    html_file = Path(__file__).parent / "static" / "index.html"
    if html_file.exists():
        # Add cache-busting headers to ensure latest version
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        return FileResponse(html_file, headers=headers)
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

@app.websocket("/api/live/system-monitor")
async def websocket_system_monitor(websocket: WebSocket):
    """WebSocket endpoint for real-time system monitoring."""
    await websocket.accept()
    logger.info("System monitoring WebSocket connected")
    
    try:
        # Send initial status
        initial_status = await get_all_processor_status()
        await websocket.send_text(json.dumps({
            "type": "processor_status",
            "data": initial_status
        }))
        
        # Keep connection alive and periodically send updates
        while True:
            try:
                # Wait for messages or timeout
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    
                    # Handle different message types
                    if data == "ping":
                        await websocket.send_text("pong")
                    elif data == "get_processor_status":
                        status = await get_all_processor_status()
                        await websocket.send_text(json.dumps({
                            "type": "processor_status",
                            "data": status
                        }))
                    elif data == "get_system_logs":
                        logs = await get_system_logs(50)
                        await websocket.send_text(json.dumps({
                            "type": "system_logs",
                            "data": logs
                        }))
                        
                except asyncio.TimeoutError:
                    # Send periodic status update
                    status = await get_all_processor_status()
                    await websocket.send_text(json.dumps({
                        "type": "processor_status",
                        "data": status
                    }))
                    
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        logger.error(f"System monitor WebSocket error: {e}")
    finally:
        logger.info("System monitoring WebSocket disconnected")

@app.post("/api/testing/export-results")
async def export_test_results(request: Dict[str, Any]):
    """Export test results in various formats."""
    try:
        results_data = request.get("results", [])
        export_format = request.get("format", "json")
        filename = request.get("filename", f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        if not results_data:
            raise HTTPException(status_code=400, detail="No results data provided")
        
        # Create temporary file for export
        import tempfile
        import csv
        from pathlib import Path
        
        temp_dir = Path(tempfile.gettempdir()) / "catalynx_exports"
        temp_dir.mkdir(exist_ok=True)
        
        if export_format.lower() == "csv":
            file_path = temp_dir / f"{filename}.csv"
            
            # Write CSV file
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                if results_data and isinstance(results_data[0], dict):
                    fieldnames = results_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(results_data)
                else:
                    writer = csv.writer(csvfile)
                    for row in results_data:
                        writer.writerow([row] if not isinstance(row, (list, tuple)) else row)
            
            return FileResponse(
                path=file_path,
                filename=f"{filename}.csv",
                media_type="text/csv"
            )
            
        elif export_format.lower() == "json":
            file_path = temp_dir / f"{filename}.json"
            
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump({
                    "export_timestamp": datetime.now().isoformat(),
                    "total_records": len(results_data),
                    "results": results_data
                }, jsonfile, indent=2)
            
            return FileResponse(
                path=file_path,
                filename=f"{filename}.json",
                media_type="application/json"
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format. Use 'csv' or 'json'")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export test results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
@app.post("/api/profiles/fetch-ein")
async def fetch_ein_data(request: dict):
    """
    Fetch organization data by EIN using ProPublica API.
    """
    try:
        ein = request.get('ein', '').strip()
        if not ein:
            raise HTTPException(status_code=400, detail="EIN is required")
        
        # Initialize EIN lookup processor
        ein_processor = EINLookupProcessor()
        
        # Create workflow config with EIN
        from src.core.data_models import WorkflowConfig, ProcessorConfig
        
        workflow_config = WorkflowConfig(
            target_ein=ein,
            target_state=None,
            target_tags=[],
            max_results=1
        )
        
        config = ProcessorConfig(
            workflow_id=str(uuid.uuid4()),
            processor_name="ein_lookup",
            workflow_config=workflow_config,
            processor_specific_config={}
        )
        
        # Execute EIN lookup
        result = await ein_processor.execute(config)
        logger.info(f"EIN lookup result: success={result.success}, data_keys={list(result.data.keys()) if result.data else 'None'}")
        
        if result.success and result.data:
            logger.info(f"Result data structure: {result.data}")
            org_data = result.data.get('target_organization', {})
            return {
                "success": True,
                "data": {
                    "name": org_data.get('name', ''),
                    "ein": org_data.get('ein', ein),
                    "mission_statement": org_data.get('mission_description', '') or org_data.get('activity_description', ''),
                    "organization_type": str(org_data.get('organization_type', 'nonprofit')).replace('OrganizationType.', '').lower(),
                    "ntee_code": org_data.get('ntee_code', ''),
                    "city": org_data.get('city', ''),
                    "state": org_data.get('state', ''),
                    "website": org_data.get('website', ''),
                    "revenue": org_data.get('revenue', 0),
                    "assets": org_data.get('assets', 0),
                    "expenses": org_data.get('expenses', 0),
                    "most_recent_filing_year": org_data.get('most_recent_filing_year', ''),
                    "filing_years": org_data.get('filing_years', [])
                }
            }
        else:
            return {
                "success": False,
                "message": "Organization not found or API error",
                "error": result.error_message if hasattr(result, 'error_message') else "Unknown error"
            }
            
    except Exception as e:
        logger.error(f"EIN fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch EIN data: {str(e)}")

@app.get("/api/profiles")
async def list_profiles(status: Optional[str] = None, limit: Optional[int] = None):
    """List all organization profiles."""
    try:
        profiles = profile_service.list_profiles(
            status=status,
            limit=limit
        )
        
        # Convert profiles to dict format and add opportunity counts
        profile_dicts = []
        for profile in profiles:
            profile_dict = profile.model_dump()
            profile_dict["opportunities_count"] = 0  # TODO: Get actual count from leads
            profile_dicts.append(profile_dict)
        
        return {"profiles": profile_dicts}
        
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profiles")
async def create_profile(profile_data: Dict[str, Any]):
    """Create a new organization profile."""
    try:
        profile = profile_service.create_profile(profile_data)
        return {"profile": profile.model_dump(), "message": "Profile created successfully"}
        
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
        
        return {"profile": profile.model_dump()}
        
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
        
        return {"profile": profile.model_dump(), "message": "Profile updated successfully"}
        
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
        return {"template": template.model_dump(), "message": "Template created successfully"}
        
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
            "leads": [lead.model_dump() for lead in leads],
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
                        opportunities.append(lead.model_dump())
        
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
        processor = engine.registry.get_processor(processor_name)
        if not processor:
            raise HTTPException(status_code=404, detail="Processor not found")
        
        # Extract parameters from request
        params = request.get("parameters", {})
        input_data = request.get("input_data", [])
        
        # Execute processor
        from src.core.data_models import WorkflowConfig, ProcessorConfig
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
            bmf_instance = engine.registry.get_processor("bmf_filter")
            if bmf_instance:
                
                # Create proper configuration objects
                from src.core.data_models import WorkflowConfig, ProcessorConfig
                workflow_config = WorkflowConfig(
                    workflow_id=f"nonprofit_discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    states=[state] if state else ["VA"],
                    max_results=max_results
                )
                processor_config = ProcessorConfig(
                    workflow_id=workflow_config.workflow_id,
                    processor_name="bmf_filter",
                    workflow_config=workflow_config,
                    processor_specific_config={
                        "focus_areas": focus_areas,
                        "target_populations": target_populations,
                        "profile_context": profile_context
                    }
                )
                
                bmf_result = await bmf_instance.execute(processor_config)
                results["bmf_results"] = bmf_result.data.get("results", [])
        
        # Execute ProPublica fetch
        pp_instance = engine.registry.get_processor("propublica_fetch")
        if pp_instance:
            
            workflow_config = WorkflowConfig(
                workflow_id=f"propublica_fetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                target_ein=ein,
                max_results=max_results
            )
            
            if ein:
                input_data = [{"ein": ein}]
            else:
                input_data = results.get("bmf_results", [])[:50]
            
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="propublica_fetch",
                workflow_config=workflow_config,
                input_data={"organizations": input_data}
            )
            
            pp_result = await pp_instance.execute(processor_config)
            results["propublica_results"] = pp_result.data.get("results", [])
        
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
        grants_instance = engine.registry.get_processor("grants_gov_fetch")
        if grants_instance:
            
            from src.core.data_models import WorkflowConfig, ProcessorConfig
            workflow_config = WorkflowConfig(
                workflow_id=f"grants_gov_fetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                max_results=max_results
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="grants_gov_fetch",
                workflow_config=workflow_config,
                processor_specific_config={
                    "keywords": keywords,
                    "opportunity_category": opportunity_category
                }
            )
            
            grants_result = await grants_instance.execute(processor_config)
            results["grants_gov_results"] = grants_result.data.get("results", [])
        
        # Execute USASpending fetch for historical context
        usa_instance = engine.registry.get_processor("usaspending_fetch")
        if usa_instance:
            
            workflow_config = WorkflowConfig(
                workflow_id=f"usaspending_fetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                max_results=max_results
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="usaspending_fetch",
                workflow_config=workflow_config,
                processor_specific_config={
                    "keywords": keywords
                }
            )
            
            usa_result = await usa_instance.execute(processor_config)
            results["usaspending_results"] = usa_result.data.get("results", [])
        
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
        va_instance = engine.registry.get_processor("va_state_grants_fetch")
        if va_instance and "VA" in states:
            
            from src.core.data_models import WorkflowConfig, ProcessorConfig
            workflow_config = WorkflowConfig(
                workflow_id=f"va_state_grants_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                states=["VA"],
                max_results=max_results
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="va_state_grants_fetch",
                workflow_config=workflow_config,
                processor_specific_config={
                    "focus_areas": focus_areas
                }
            )
            
            va_result = await va_instance.execute(processor_config)
            results["virginia_results"] = va_result.data.get("results", [])
        
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
        fd_instance = engine.registry.get_processor("foundation_directory_fetch")
        if fd_instance:
            
            from src.core.data_models import WorkflowConfig, ProcessorConfig
            workflow_config = WorkflowConfig(
                workflow_id=f"foundation_directory_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                max_results=max_results
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="foundation_directory_fetch",
                workflow_config=workflow_config,
                processor_specific_config={
                    "industries": industries,
                    "funding_range": funding_range
                }
            )
            
            fd_result = await fd_instance.execute(processor_config)
            results["foundation_results"] = fd_result.data.get("results", [])
        
        # Execute CSR Analysis
        csr_instance = engine.registry.get_processor("corporate_csr_analyzer")
        if csr_instance:
            
            workflow_config = WorkflowConfig(
                workflow_id=f"csr_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                max_results=max_results
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="corporate_csr_analyzer",
                workflow_config=workflow_config,
                processor_specific_config={
                    "industries": industries,
                    "company_sizes": company_sizes
                }
            )
            
            csr_result = await csr_instance.execute(processor_config)
            results["csr_results"] = csr_result.data.get("results", [])
        
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
        fs_instance = engine.registry.get_processor("financial_scorer")
        if fs_instance:
            
            from src.core.data_models import WorkflowConfig, ProcessorConfig
            workflow_config = WorkflowConfig(
                workflow_id=f"financial_scoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="financial_scorer",
                workflow_config=workflow_config,
                input_data={"organizations": organizations}
            )
            
            financial_result = await fs_instance.execute(processor_config)
            results["results"]["financial_scores"] = financial_result.data.get("results", [])
        
        # Execute Risk Assessment
        risk_instance = engine.registry.get_processor("risk_assessor")
        if risk_instance:
            
            workflow_config = WorkflowConfig(
                workflow_id=f"risk_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="risk_assessor",
                workflow_config=workflow_config,
                input_data={"organizations": organizations}
            )
            
            risk_result = await risk_instance.execute(processor_config)
            results["results"]["risk_assessments"] = risk_result.data.get("results", [])
        
        # Execute Government Opportunity Scoring
        gov_instance = engine.registry.get_processor("government_opportunity_scorer")
        if gov_instance:
            
            workflow_config = WorkflowConfig(
                workflow_id=f"gov_opportunity_scoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="government_opportunity_scorer",
                workflow_config=workflow_config,
                input_data={"organizations": organizations}
            )
            
            gov_result = await gov_instance.execute(processor_config)
            results["results"]["government_scores"] = gov_result.data.get("results", [])
        
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
        board_instance = engine.registry.get_processor("board_network_analyzer")
        if board_instance:
            
            from src.core.data_models import WorkflowConfig, ProcessorConfig
            workflow_config = WorkflowConfig(
                workflow_id=f"board_network_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="board_network_analyzer",
                workflow_config=workflow_config,
                input_data={"organizations": organizations}
            )
            
            board_result = await board_instance.execute(processor_config)
            results["results"]["board_networks"] = board_result.data.get("results", [])
        
        # Execute Enhanced Network Analysis
        enhanced_instance = engine.registry.get_processor("enhanced_network_analyzer")
        if enhanced_instance:
            
            workflow_config = WorkflowConfig(
                workflow_id=f"enhanced_network_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="enhanced_network_analyzer",
                workflow_config=workflow_config,
                input_data={"organizations": organizations}
            )
            
            enhanced_result = await enhanced_instance.execute(processor_config)
            results["results"]["enhanced_networks"] = enhanced_result.data.get("results", [])
        
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
        classifier_instance = engine.registry.get_processor("intelligent_classifier")
        if classifier_instance:
            
            from src.core.data_models import WorkflowConfig, ProcessorConfig
            workflow_config = WorkflowConfig(
                workflow_id=f"intelligent_classification_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                states=[state] if state else ["VA"]
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="intelligent_classifier",
                workflow_config=workflow_config,
                input_data={"organizations": organizations or []},
                processor_specific_config={
                    "min_score": min_score
                }
            )
            
            classification_result = await classifier_instance.execute(processor_config)
            results["results"]["classifications"] = classification_result.data.get("results", [])
        
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

# Testing Interface API endpoints
@app.get("/api/testing/processors/status")
async def get_all_processor_status():
    """Get detailed status for all processors with health indicators."""
    try:
        engine = get_workflow_engine()
        processors = engine.registry.list_processors()
        
        processor_statuses = []
        for processor_name in processors:
            try:
                # Get processor info
                processor_instance = engine.registry.get_processor(processor_name)
                info = engine.registry.get_processor_info(processor_name) or {}
                
                # Determine health status
                health_status = "healthy" if processor_instance else "error"
                health_details = "Processor ready" if processor_instance else "Processor not available"
                
                processor_status = {
                    "name": processor_name,
                    "health_status": health_status,
                    "health_details": health_details,
                    "type": info.get("type", "unknown"),
                    "description": info.get("description", "No description available"),
                    "last_check": datetime.now().isoformat(),
                    "available": processor_instance is not None
                }
                
                processor_statuses.append(processor_status)
                
            except Exception as e:
                processor_statuses.append({
                    "name": processor_name,
                    "health_status": "error",
                    "health_details": f"Status check failed: {str(e)[:100]}",
                    "type": "unknown",
                    "description": "Error retrieving processor information",
                    "last_check": datetime.now().isoformat(),
                    "available": False
                })
        
        # Calculate overall system health
        healthy_count = sum(1 for p in processor_statuses if p["health_status"] == "healthy")
        total_count = len(processor_statuses)
        overall_health = "healthy" if healthy_count == total_count else "degraded" if healthy_count > total_count * 0.5 else "critical"
        
        return {
            "overall_health": overall_health,
            "healthy_processors": healthy_count,
            "total_processors": total_count,
            "processors": processor_statuses,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get processor status: {e}")
        return {
            "overall_health": "error",
            "healthy_processors": 0,
            "total_processors": 0,
            "processors": [],
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/testing/processors/{processor_name}/test")
async def test_processor(processor_name: str, request: Dict[str, Any]):
    """Test execute a processor with sample data."""
    try:
        engine = get_workflow_engine()
        processor = engine.registry.get_processor(processor_name)
        
        if not processor:
            raise HTTPException(status_code=404, detail="Processor not found")
        
        # Use sample data or provided test data
        test_data = request.get("test_data", [])
        test_params = request.get("parameters", {})
        
        # Add test mode parameter
        test_params["test_mode"] = True
        test_params["max_results"] = min(test_params.get("max_results", 5), 10)  # Limit test results
        
        start_time = datetime.now()
        
        # Execute processor
        try:
            from src.core.data_models import WorkflowConfig, ProcessorConfig
            workflow_config = WorkflowConfig(
                workflow_id=f"test_{processor_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                max_results=test_params.get("max_results", 10)
            )
            processor_config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name=processor_name,
                workflow_config=workflow_config,
                input_data={"test_data": test_data},
                processor_specific_config=test_params
            )
            
            processor_result = await processor.execute(processor_config)
            result = processor_result.data.get("results", processor_result.data)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Processor execution failed: {str(e)}")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "status": "success",
            "processor": processor_name,
            "execution_time_seconds": execution_time,
            "test_data_count": len(test_data) if isinstance(test_data, list) else 1,
            "result_count": len(result) if isinstance(result, list) else 1,
            "result": result,
            "parameters_used": test_params,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test processor {processor_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/testing/processors/{processor_name}/logs")
async def get_processor_logs(processor_name: str, lines: int = 100):
    """Get recent log entries for a specific processor."""
    try:
        # For now, return mock logs - in production this would read actual log files
        mock_logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": f"Processor {processor_name} initialized successfully",
                "source": processor_name
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "DEBUG",
                "message": f"Processing request for {processor_name}",
                "source": processor_name
            }
        ]
        
        return {
            "processor": processor_name,
            "log_entries": mock_logs[-lines:],
            "total_entries": len(mock_logs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get logs for processor {processor_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/testing/system/logs")
async def get_system_logs(lines: int = 200):
    """Get recent system log entries."""
    try:
        # Mock system logs - in production would read actual log files
        mock_system_logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": "Catalynx system started successfully",
                "source": "system"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": f"Registered {len(get_processor_summary()['processors_info'])} processors",
                "source": "registry"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "DEBUG",
                "message": "WebSocket connections established",
                "source": "websocket"
            }
        ]
        
        return {
            "log_entries": mock_system_logs[-lines:],
            "total_entries": len(mock_system_logs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Welcome Stage API endpoints
@app.get("/api/welcome/status")
async def get_welcome_status():
    """Get welcome stage status and system overview."""
    try:
        processor_summary = get_processor_summary()
        
        return {
            "status": "ready",
            "system_health": "operational",
            "processors_available": processor_summary["total_processors"],
            "capabilities": [
                "Multi-track opportunity discovery",
                "AI-powered organization analysis", 
                "Strategic network insights",
                "Comprehensive export system"
            ],
            "quick_start_available": True,
            "sample_data_ready": True,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get welcome status: {e}")
        return {
            "status": "error",
            "system_health": "degraded",
            "processors_available": 0,
            "capabilities": [],
            "quick_start_available": False,
            "sample_data_ready": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/welcome/sample-profile")
async def create_sample_profile():
    """Create a sample organization profile for demonstration."""
    try:
        sample_profile_data = {
            "name": "Sample Technology Nonprofit",
            "description": "A sample organization focused on digital education and community technology access",
            "mission_statement": "To bridge the digital divide and empower communities through accessible technology education and resources",
            "organization_type": "nonprofit",
            "geographic_scope": {
                "states": ["VA", "MD", "DC"],
                "regions": ["Mid-Atlantic"]
            },
            "focus_areas": [
                "digital_literacy",
                "stem_education", 
                "community_development"
            ],
            "target_populations": [
                "underserved_youth",
                "seniors",
                "low_income_families"
            ],
            "funding_history": {
                "previous_grants": ["Federal STEM Grant", "Community Foundation Grant"],
                "funding_ranges": ["$10000-50000", "$50000-100000"]
            },
            "capabilities": [
                "Program delivery",
                "Community partnerships",
                "Technology integration"
            ],
            "is_sample": True
        }
        
        profile = profile_service.create_profile(sample_profile_data)
        
        return {
            "status": "success",
            "message": "Sample profile created successfully",
            "profile": profile.model_dump(),
            "next_steps": [
                "Review profile details in PROFILER stage",
                "Run multi-track discovery in DISCOVER stage",
                "Analyze results in ANALYZE stage"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to create sample profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/welcome/quick-start")
async def quick_start_demo():
    """Execute a quick demonstration of the platform capabilities."""
    try:
        # Create sample profile
        sample_response = await create_sample_profile()
        profile_data = sample_response["profile"]
        profile_id = profile_data.get("id") or "sample_profile_demo"
        
        # Generate mock discovery results for demonstration
        mock_discovery_data = {
            "nonprofit_track": [
                {
                    "organization_name": "Tech for Good Foundation",
                    "opportunity_type": "nonprofit_partnership",
                    "funding_amount": 75000,
                    "compatibility_score": 0.89,
                    "description": "Collaborative technology education initiative"
                }
            ],
            "federal_track": [
                {
                    "agency": "Department of Education",
                    "program": "Community Learning Centers",
                    "funding_amount": 150000,
                    "compatibility_score": 0.82,
                    "deadline": "2025-06-15"
                }
            ],
            "state_track": [
                {
                    "agency": "Virginia Department of Social Services",
                    "program": "Community Technology Access Grant",
                    "funding_amount": 85000,
                    "compatibility_score": 0.78,
                    "deadline": "2025-05-30"
                }
            ],
            "commercial_track": [
                {
                    "organization_name": "Microsoft Corporate Foundation", 
                    "program": "Digital Skills Initiative",
                    "funding_amount": 100000,
                    "compatibility_score": 0.85,
                    "opportunity_type": "corporate_grant"
                }
            ]
        }
        
        return {
            "status": "completed",
            "message": "Quick start demonstration completed successfully",
            "profile_created": sample_response["profile"],
            "mock_opportunities": mock_discovery_data,
            "total_opportunities": sum(len(track) for track in mock_discovery_data.values()),
            "recommendations": [
                "This demo shows potential opportunities across all 4 funding tracks",
                "Real discovery would analyze thousands of actual funding sources", 
                "Navigate to PROFILER to customize your organization profile",
                "Use DISCOVER to run actual multi-track opportunity discovery"
            ],
            "next_actions": {
                "customize_profile": "Edit profile details in PROFILER stage",
                "run_discovery": "Execute real discovery in DISCOVER stage", 
                "analyze_results": "Deep dive analysis in ANALYZE stage"
            }
        }
        
    except Exception as e:
        logger.error(f"Quick start demo failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
            "/api/welcome/status",
            "/api/welcome/sample-profile",
            "/api/welcome/quick-start",
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