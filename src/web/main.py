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
import random
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
from src.profiles.entity_service import get_entity_profile_service
from src.profiles.models import OrganizationProfile, FundingType
from src.profiles.workflow_integration import ProfileWorkflowIntegrator
from src.profiles.metrics_tracker import get_metrics_tracker
from src.discovery.entity_discovery_service import get_entity_discovery_service
from src.discovery.discovery_engine import discovery_engine
from src.pipeline.pipeline_engine import ProcessingPriority
from src.pipeline.resource_allocator import resource_allocator
from src.processors.registry import get_processor_summary
from src.processors.lookup.ein_lookup import EINLookupProcessor
# from src.processors.analysis.ai_service_manager import get_ai_service_manager

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
entity_profile_service = get_entity_profile_service()  # Enhanced entity-based service
entity_discovery_service = get_entity_discovery_service()  # Enhanced discovery service
profile_integrator = ProfileWorkflowIntegrator()
metrics_tracker = get_metrics_tracker()

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

@app.get("/favicon.ico")
async def favicon():
    """Serve favicon to prevent 404 errors."""
    # Return a simple 1x1 transparent PNG to avoid 404 errors
    # This prevents favicon requests from showing up as errors in logs
    favicon_path = Path(__file__).parent / "static" / "CatalynxLogo.png" 
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/x-icon")
    else:
        # Return empty response to prevent 404
        from fastapi.responses import Response
        return Response(status_code=204)

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

@app.get("/api/system/health")
async def system_health():
    """Get detailed system health information."""
    try:
        engine = get_workflow_engine()
        processors = engine.registry.list_processors()
        
        return {
            "status": "healthy",
            "processors_available": len(processors),
            "services": {
                "api": "operational",
                "database": "operational", 
                "processors": "operational"
            },
            "uptime": datetime.now().isoformat(),
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        return {
            "status": "degraded",
            "processors_available": 0,
            "services": {
                "api": "operational",
                "database": "error",
                "processors": "error"
            },
            "error": str(e),
            "uptime": datetime.now().isoformat(),
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat()
        }

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

@app.websocket("/api/live/discovery/{session_id}")
async def websocket_unified_discovery(websocket: WebSocket, session_id: str):
    """
    PHASE 4B: WebSocket endpoint for real-time unified discovery progress monitoring.
    Provides live updates during unified multi-track discovery execution.
    """
    await websocket.accept()
    logger.info(f"Unified discovery WebSocket connected for session: {session_id}")
    
    try:
        from src.discovery.unified_multitrack_bridge import get_unified_bridge
        
        bridge = get_unified_bridge()
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "bridge_architecture": "unified_multitrack_bridge",
            "phase": "4B"
        }))
        
        # Store WebSocket connection for progress updates
        # This would be handled by a progress callback in the actual discovery call
        session = bridge.get_session(session_id)
        if session:
            # Send current session status
            await websocket.send_text(json.dumps({
                "type": "session_status",
                "session_id": session_id,
                "status": session.status.value,
                "progress_updates": len(session.progress_updates),
                "total_opportunities": session.total_opportunities,
                "execution_time": session.execution_time_seconds,
                "strategies_executed": list(session.results_by_strategy.keys()),
                "timestamp": datetime.now().isoformat()
            }))
            
            # Send recent progress updates
            for update in session.progress_updates[-10:]:  # Last 10 updates
                await websocket.send_text(json.dumps({
                    "type": "progress_update",
                    "session_id": session_id,
                    "update": update,
                    "timestamp": datetime.now().isoformat()
                }))
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                
                elif message.get("type") == "get_session_summary":
                    summary = bridge.get_session_summary(session_id)
                    await websocket.send_text(json.dumps({
                        "type": "session_summary",
                        "session_id": session_id,
                        "summary": summary,
                        "timestamp": datetime.now().isoformat()
                    }))
                
                elif message.get("type") == "get_bridge_status":
                    bridge_status = bridge.get_bridge_status()
                    await websocket.send_text(json.dumps({
                        "type": "bridge_status",
                        "status": bridge_status,
                        "timestamp": datetime.now().isoformat()
                    }))
                
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }))
                
            except WebSocketDisconnect:
                logger.info(f"Discovery WebSocket disconnected for session: {session_id}")
                break
                
    except Exception as e:
        logger.error(f"Discovery WebSocket error for session {session_id}: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:

            logger.warning(f"Unexpected error: {e}")

            pass
    finally:
        logger.info(f"Discovery WebSocket cleanup for session: {session_id}")

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
    Fetch organization data by EIN using ProPublica API (both JSON and XML data).
    Enhanced to extract Schedule I grantees for discovery fast-tracking.
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
        
        # Execute EIN lookup (gets JSON data)
        result = await ein_processor.execute(config)
        logger.info(f"EIN lookup result: success={result.success}, data_keys={list(result.data.keys()) if result.data else 'None'}")
        
        if result.success and result.data:
            logger.info(f"Result data structure: {result.data}")
            org_data = result.data.get('target_organization', {})
            
            # Prepare basic response data
            response_data = {
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
                "filing_years": org_data.get('filing_years', []),
                "schedule_i_grantees": [],  # Initialize empty list
                "schedule_i_status": "not_checked"  # Default status
            }
            
            # Attempt to fetch XML data and extract Schedule I grantees
            try:
                from src.utils.xml_fetcher import XMLFetcher
                from src.utils.schedule_i_extractor import ScheduleIExtractor
                
                logger.info(f"Attempting to fetch XML data for EIN {ein}")
                
                xml_fetcher = XMLFetcher()
                xml_content = await xml_fetcher.fetch_xml_by_ein(ein)
                
                logger.info(f"XML fetch completed for EIN {ein}, content: {xml_content is not None}, size: {len(xml_content) if xml_content else 0}")
                
                if xml_content:
                    logger.info(f"Successfully fetched XML data for EIN {ein} ({len(xml_content):,} bytes)")
                    
                    # Extract Schedule I grantees
                    extractor = ScheduleIExtractor()
                    most_recent_year = org_data.get('most_recent_filing_year')
                    grantees = extractor.extract_grantees_from_xml(xml_content, most_recent_year)
                    
                    if grantees:
                        logger.info(f"Extracted {len(grantees)} Schedule I grantees for EIN {ein}")
                        response_data["schedule_i_grantees"] = [grantee.dict() for grantee in grantees]
                        response_data["schedule_i_status"] = "found"
                    else:
                        logger.info(f"No Schedule I grantees found in XML for EIN {ein}")
                        response_data["schedule_i_status"] = "no_grantees"
                else:
                    logger.warning(f"No XML data available for EIN {ein}")
                    response_data["schedule_i_status"] = "no_xml"
                    
            except Exception as e:
                logger.warning(f"Error fetching/processing XML data for EIN {ein}: {e}")
                response_data["schedule_i_status"] = "no_xml"
                # Continue with basic data even if XML processing fails
            
            return {
                "success": True,
                "data": response_data
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
        
        # Debug: Log what profiles we got from the service
        logger.info(f"ProfileService returned {len(profiles)} profiles")
        if profiles:
            # Find a profile with actual data for debugging (not just the first one)
            sample_profile = profiles[0]  # Default to first
            for profile in profiles:
                if (profile.ntee_codes and len(profile.ntee_codes) > 0) or (profile.government_criteria and len(profile.government_criteria) > 0):
                    sample_profile = profile
                    break
            logger.info(f"Sample profile data ('{sample_profile.name}'): ntee_codes={getattr(sample_profile, 'ntee_codes', 'NOT_FOUND')}, government_criteria={getattr(sample_profile, 'government_criteria', 'NOT_FOUND')}, keywords={getattr(sample_profile, 'keywords', 'NOT_FOUND')}")
        
        # Convert profiles to dict format and add opportunity counts
        profile_dicts = []
        for profile in profiles:
            profile_dict = profile.model_dump()
            # Get actual opportunities count from associated leads
            profile_dict["opportunities_count"] = len(profile.associated_opportunities)
            profile_dicts.append(profile_dict)
        
        # Debug: Log what we're returning  
        if profile_dicts:
            # Find a profile dict with actual data for debugging
            sample_dict = profile_dicts[0]  # Default to first
            for profile_dict in profile_dicts:
                if (profile_dict.get('ntee_codes') and len(profile_dict.get('ntee_codes', [])) > 0) or (profile_dict.get('government_criteria') and len(profile_dict.get('government_criteria', [])) > 0):
                    sample_dict = profile_dict
                    break
            logger.info(f"Sample profile dict ('{sample_dict.get('name', 'UNKNOWN')}'): ntee_codes={sample_dict.get('ntee_codes', 'NOT_FOUND')}, government_criteria={sample_dict.get('government_criteria', 'NOT_FOUND')}, keywords={sample_dict.get('keywords', 'NOT_FOUND')}")
        
        return {"profiles": profile_dicts}
        
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profiles")
async def create_profile(profile_data: Dict[str, Any]):
    """Create a new organization profile."""
    try:
        # Debug: Log the profile data received
        logger.info(f"Creating profile with data: ntee_codes={profile_data.get('ntee_codes')}, government_criteria={profile_data.get('government_criteria')}, keywords={profile_data.get('keywords')}")
        
        profile = profile_service.create_profile(profile_data)
        
        # Debug: Log the profile after creation
        logger.info(f"Profile after creation: ntee_codes={profile.ntee_codes}, government_criteria={profile.government_criteria}, keywords={profile.keywords}")
        
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
        # Debug: Log the update data received
        logger.info(f"Updating profile {profile_id} with data: ntee_codes={update_data.get('ntee_codes')}, government_criteria={update_data.get('government_criteria')}, keywords={update_data.get('keywords')}")
        
        profile = profile_service.update_profile(profile_id, update_data)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Debug: Log the profile after update
        logger.info(f"Profile after update: ntee_codes={profile.ntee_codes}, government_criteria={profile.government_criteria}, keywords={profile.keywords}")
        
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

@app.get("/api/profiles/{profile_id}/metrics")
async def get_profile_metrics(profile_id: str):
    """Get comprehensive metrics for a specific profile."""
    try:
        # Verify profile exists
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Generate efficiency report
        metrics_report = await metrics_tracker.generate_efficiency_report(profile_id)
        
        return {
            "profile_id": profile_id,
            "profile_name": profile.name,
            "metrics": metrics_report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/metrics/summary")
async def get_all_profiles_metrics_summary():
    """Get metrics summary for all profiles."""
    try:
        summary = await metrics_tracker.get_all_profile_metrics_summary()
        
        return {
            "total_profiles": len(summary),
            "profiles": summary,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get profiles metrics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profiles/{profile_id}/metrics/funnel")
async def update_funnel_metrics(profile_id: str, request: Dict[str, Any]):
    """Update funnel stage metrics for a profile."""
    try:
        stage = request.get("stage")
        count = request.get("count", 1)
        
        if not stage:
            raise HTTPException(status_code=400, detail="Stage is required")
        
        await metrics_tracker.update_funnel_stage(profile_id, stage, count)
        
        return {"success": True, "message": f"Updated {stage} metrics for profile {profile_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update funnel metrics for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profiles/{profile_id}/metrics/session")
async def start_metrics_session(profile_id: str):
    """Start a new discovery session for metrics tracking."""
    try:
        await metrics_tracker.start_discovery_session(profile_id)
        
        return {
            "success": True, 
            "message": f"Started new discovery session for profile {profile_id}",
            "session_started_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start metrics session for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/{profile_id}/plan-results")
async def get_profile_plan_results(profile_id: str):
    """Get strategic planning results for a profile."""
    try:
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Extract plan results from processing history
        plan_results = profile.processing_history.get('plan_results', {})
        
        return {
            "profile_id": profile_id,
            "plan_results": plan_results,
            "last_updated": profile.processing_history.get('plan_last_updated'),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Failed to get plan results for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profiles/{profile_id}/plan-results")
async def save_profile_plan_results(profile_id: str, plan_data: Dict[str, Any]):
    """Save strategic planning results for a profile."""
    try:
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Store plan results in processing history
        if not profile.processing_history:
            profile.processing_history = {}
            
        profile.processing_history['plan_results'] = plan_data
        profile.processing_history['plan_last_updated'] = datetime.now().isoformat()
        
        # Update the profile
        updated_profile = profile_service.update_profile(profile_id, profile)
        
        return {
            "message": "Plan results saved successfully",
            "profile_id": profile_id,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Failed to save plan results for profile {profile_id}: {e}")
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

@app.get("/api/profiles/{profile_id}/opportunities")
async def get_profile_opportunities(profile_id: str, stage: Optional[str] = None, min_score: Optional[float] = None):
    """Get opportunities for a profile (alias for leads endpoint)."""
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
        
        # Convert leads to opportunities format for frontend
        opportunities = []
        for lead in leads:
            opportunity = {
                "id": lead.lead_id,
                "organization_name": lead.organization_name,
                "program_name": lead.program_name,
                "description": lead.description,
                "funding_amount": lead.funding_amount,
                "opportunity_type": lead.opportunity_type.value if hasattr(lead.opportunity_type, 'value') else str(lead.opportunity_type),
                "compatibility_score": lead.compatibility_score,
                "success_probability": lead.success_probability,
                "pipeline_stage": lead.pipeline_stage.value if hasattr(lead.pipeline_stage, 'value') else str(lead.pipeline_stage),
                "discovered_at": lead.discovered_at.isoformat() if lead.discovered_at else None,
                "last_analyzed": lead.last_analyzed.isoformat() if lead.last_analyzed else None,
                "match_factors": lead.match_factors,
                "recommendations": lead.recommendations,
                "approach_strategy": lead.approach_strategy,
                "external_data": lead.external_data
            }
            opportunities.append(opportunity)
        
        return {
            "profile_id": profile_id,
            "total_opportunities": len(opportunities),
            "opportunities": opportunities,
            "filters_applied": {
                "stage": stage,
                "min_score": min_score
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get opportunities for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Enhanced Entity-Based Profile Endpoints

@app.get("/api/profiles/{profile_id}/entity-analysis")
async def get_profile_entity_analysis(profile_id: str):
    """Get comprehensive entity-based analysis for a profile using shared analytics."""
    try:
        analysis = await entity_profile_service.analyze_profile_entities(profile_id)
        return analysis
    except Exception as e:
        logger.error(f"Failed to get entity analysis for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profiles/{profile_id}/add-entity-lead")
async def add_entity_lead(profile_id: str, lead_data: Dict[str, Any]):
    """Add opportunity lead using entity references (EIN, opportunity ID)."""
    try:
        organization_ein = lead_data.get("organization_ein")
        opportunity_id = lead_data.get("opportunity_id")
        
        if not organization_ein:
            raise HTTPException(status_code=400, detail="organization_ein is required")
        
        lead = await entity_profile_service.add_entity_lead(
            profile_id=profile_id,
            organization_ein=organization_ein,
            opportunity_id=opportunity_id,
            additional_data=lead_data.get("additional_data", {})
        )
        
        if lead:
            return {
                "success": True,
                "lead_id": lead.lead_id,
                "message": "Entity lead added successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to add entity lead")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add entity lead for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/leads/{lead_id}/entity-analysis")
async def get_lead_entity_analysis(lead_id: str):
    """Get comprehensive entity-based analysis for a specific lead."""
    try:
        analysis = await entity_profile_service.get_entity_lead_analysis(lead_id)
        return analysis
    except Exception as e:
        logger.error(f"Failed to get entity analysis for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profiles/{profile_id}/entity-discovery")
async def start_entity_discovery(profile_id: str, discovery_params: Dict[str, Any]):
    """Start discovery session using entity-based data sources."""
    try:
        entity_types = discovery_params.get("entity_types", ["nonprofits", "government_opportunities"])
        filters = discovery_params.get("filters", {})
        
        session = entity_profile_service.create_entity_discovery_session(
            profile_id=profile_id,
            entity_types=entity_types,
            filters=filters
        )
        
        if session:
            return {
                "success": True,
                "session_id": session.session_id,
                "message": "Entity discovery session started"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to start entity discovery session")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start entity discovery for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Enhanced Entity-Based Discovery Endpoints

@app.post("/api/profiles/{profile_id}/discover/entity-analytics")
async def discover_with_entity_analytics(profile_id: str, discovery_params: Dict[str, Any]):
    """Start discovery using entity-based architecture with shared analytics."""
    try:
        # Get profile
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        entity_types = discovery_params.get("entity_types", ["nonprofits", "government"])
        max_results = discovery_params.get("max_results", 50)
        filters = discovery_params.get("filters", {})
        
        # Start entity-based discovery
        session = await discovery_engine.discover_with_entity_analytics(
            profile=profile,
            entity_types=entity_types,
            max_results=max_results,
            filters=filters
        )
        
        return {
            "success": True,
            "session_id": session.session_id,
            "discovery_mode": "entity_analytics",
            "message": f"Entity-based discovery started with {len(entity_types)} entity types"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start entity analytics discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/{profile_id}/discover/entity-preview")
async def get_entity_discovery_preview(profile_id: str, entity_types: str = "nonprofits,government"):
    """Get a quick preview of entity-based discovery results."""
    try:
        # Get profile
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Parse entity types
        types_list = [t.strip() for t in entity_types.split(",")]
        
        # Get preview results
        preview_results = await discovery_engine.get_entity_discovery_preview(
            profile=profile,
            entity_types=types_list,
            limit=10
        )
        
        # Convert to serializable format
        results_data = []
        for result in preview_results:
            results_data.append({
                "organization_name": result.organization_name,
                "organization_ein": result.organization_ein,
                "opportunity_title": result.opportunity_title,
                "source_type": result.source_type.value,
                "discovery_source": result.discovery_source,
                "final_score": result.final_discovery_score,
                "funnel_stage": result.funnel_stage.value,
                "match_reasons": result.match_reasons,
                "financial_health_score": result.entity_health_score,
                "profile_compatibility_score": result.profile_compatibility_score
            })
        
        return {
            "success": True,
            "preview_results": results_data,
            "total_results": len(results_data),
            "entity_types": types_list,
            "avg_score": sum(r.final_discovery_score for r in preview_results) / len(preview_results) if preview_results else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity discovery preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/discovery/entity-cache-stats")
async def get_entity_cache_stats():
    """Get statistics about available entity data for discovery."""
    try:
        from src.core.entity_cache_manager import get_entity_cache_manager, EntityType
        
        cache_manager = get_entity_cache_manager()
        stats = await cache_manager.get_cache_stats()
        
        # Get entity counts by type
        entity_counts = {}
        for entity_type in EntityType:
            try:
                entities = await cache_manager.list_entities(entity_type)
                entity_counts[entity_type.value] = len(entities)
            except Exception:
                entity_counts[entity_type.value] = 0
        
        return {
            "success": True,
            "cache_stats": stats,
            "entity_counts": entity_counts,
            "discovery_ready": {
                "nonprofits": entity_counts.get("nonprofit", 0) > 0,
                "government_opportunities": entity_counts.get("government_opportunity", 0) > 0,
                "foundations": entity_counts.get("foundation", 0) > 0
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get entity cache stats: {e}")
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

@app.post("/api/profiles/{profile_id}/discover/unified")
async def discover_opportunities_unified(profile_id: str, discovery_params: Dict[str, Any]):
    """
    PHASE 4B: Enhanced discovery using unified multi-track bridge architecture.
    Uses the Phase 3 unified discovery bridge for improved performance and real-time progress.
    """
    try:
        # Import the unified discovery bridge
        from src.discovery.unified_multitrack_bridge import get_unified_bridge
        from src.core.data_models import FundingSourceType
        
        logger.info(f"Starting unified discovery for profile {profile_id}")
        
        # Get profile
        profile_obj = profile_service.get_profile(profile_id)
        if not profile_obj:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")
        
        # Parse funding types from request - convert from FundingType to FundingSourceType
        funding_type_strings = discovery_params.get("funding_types", ["grants"])
        funding_source_types = []
        
        # Map old FundingType to new FundingSourceType
        funding_type_mapping = {
            "grants": FundingSourceType.GOVERNMENT_FEDERAL,
            "government": FundingSourceType.GOVERNMENT_FEDERAL,
            "commercial": FundingSourceType.FOUNDATION_CORPORATE,
            "sponsorships": FundingSourceType.CORPORATE_SPONSORSHIP,
            "partnerships": FundingSourceType.CORPORATE_CSR
        }
        
        for ft_str in funding_type_strings:
            if ft_str in funding_type_mapping:
                funding_source_types.append(funding_type_mapping[ft_str])
            else:
                logger.warning(f"Unknown funding type: {ft_str}, using default")
                funding_source_types.append(FundingSourceType.GOVERNMENT_FEDERAL)
        
        # Add state funding if applicable
        if hasattr(profile_obj, 'geographic_scope') and hasattr(profile_obj.geographic_scope, 'states'):
            if 'VA' in getattr(profile_obj.geographic_scope, 'states', []):
                funding_source_types.append(FundingSourceType.GOVERNMENT_STATE)
        
        max_results_per_type = discovery_params.get("max_results", 100)
        
        # Initialize unified bridge
        bridge = get_unified_bridge()
        
        # Track progress updates
        progress_updates = []
        
        def progress_callback(session_id: str, update_data: Dict[str, Any]):
            """Capture progress updates for response"""
            progress_updates.append({
                "timestamp": update_data.get("timestamp"),
                "status": update_data.get("status"),
                "message": update_data.get("message", ""),
                "strategy": update_data.get("strategy"),
                "results_count": update_data.get("results_count", 0)
            })
            logger.info(f"Discovery progress [{session_id}]: {update_data.get('message', '')}")
        
        # Execute unified multi-track discovery
        logger.info(f"Executing unified discovery with {len(funding_source_types)} funding sources")
        discovery_session = await bridge.discover_opportunities(
            profile=profile_obj,
            funding_types=funding_source_types,
            max_results_per_type=max_results_per_type,
            progress_callback=progress_callback
        )
        
        logger.info(f"Discovery session completed: {discovery_session.session_id}")
        
        # Process and convert results to web interface format
        opportunities = []
        opportunities_by_strategy = {}
        
        for strategy_name, results in discovery_session.results_by_strategy.items():
            opportunities_by_strategy[strategy_name] = len(results)
            
            for opportunity in results:
                # Convert unified opportunity to web interface format
                # Map strategy names to valid opportunity types
                opportunity_type_mapping = {
                    "foundation": "commercial",
                    "government": "government", 
                    "commercial": "commercial",
                    "nonprofit": "grants",
                    "state": "government"
                }
                
                # Normalize compatibility score to 0-1 range
                raw_score = getattr(opportunity, 'relevance_score', 0.0)
                normalized_score = min(1.0, max(0.0, raw_score / 100.0 if raw_score > 1.0 else raw_score))
                
                lead_data = {
                    "organization_name": getattr(opportunity, 'funder_name', 'Unknown Organization'),
                    "opportunity_type": opportunity_type_mapping.get(strategy_name, "grants"),
                    "source": f"unified_discovery_{strategy_name}",  # Add required source field
                    "description": getattr(opportunity, 'description', '') or getattr(opportunity, 'title', ''),
                    "funding_amount": getattr(opportunity, 'funding_amount_max', 0),
                    "compatibility_score": normalized_score,
                    "match_factors": {
                        "source_type": str(getattr(opportunity, 'source_type', '')),
                        "deadline": getattr(opportunity, 'deadline', None),
                        "eligibility": getattr(opportunity, 'eligibility_requirements', [])
                    },
                    "external_data": {
                        "opportunity_id": getattr(opportunity, 'opportunity_id', ''),
                        "source_url": getattr(opportunity, 'source_url', ''),
                        "discovery_session": discovery_session.session_id,
                        "discovery_timestamp": discovery_session.started_at.isoformat() if discovery_session.started_at else None
                    }
                }
                
                # Add lead to profile using existing service
                lead = profile_service.add_opportunity_lead(profile_id, lead_data)
                if lead:
                    opportunities.append(lead.model_dump())
        
        # Update profile metrics
        if hasattr(profile_obj, 'metrics') and profile_obj.metrics:
            profile_obj.metrics.total_discovery_sessions += 1
            profile_obj.metrics.last_discovery_session = discovery_session.started_at
            if discovery_session.execution_time_seconds:
                # Update average session duration
                total_time = (profile_obj.metrics.avg_session_duration_minutes * 
                            (profile_obj.metrics.total_discovery_sessions - 1) + 
                            discovery_session.execution_time_seconds / 60)
                profile_obj.metrics.avg_session_duration_minutes = total_time / profile_obj.metrics.total_discovery_sessions
            
            # Update funnel metrics
            profile_obj.metrics.update_funnel_metrics("prospects", len(opportunities))
            
            # Save updated profile
            profile_service.update_profile(profile_id, profile_obj)
        
        # Save discovery session for tracking and linkage
        from src.profiles.models import DiscoverySession as ProfileDiscoverySession
        profile_discovery_session = ProfileDiscoverySession(
            session_id=discovery_session.session_id,
            profile_id=profile_id,
            started_at=discovery_session.started_at,
            completed_at=discovery_session.completed_at,
            status=discovery_session.status.value if hasattr(discovery_session.status, 'value') else str(discovery_session.status),
            tracks_executed=list(discovery_session.results_by_strategy.keys()),
            opportunities_found={strategy: len(results) for strategy, results in discovery_session.results_by_strategy.items()},
            total_opportunities=discovery_session.total_opportunities,
            execution_time_seconds=int(discovery_session.execution_time_seconds) if discovery_session.execution_time_seconds else 0,
            notes=f"Unified discovery with {len(funding_source_types)} funding source types"
        )
        profile_service.add_discovery_session(profile_discovery_session)
        
        # Get session summary for response
        session_summary = bridge.get_session_summary(discovery_session.session_id)
        
        return {
            "message": f"Unified discovery completed for profile {profile_id}",
            "discovery_id": discovery_session.session_id,
            "status": discovery_session.status.value,
            "execution_time_seconds": discovery_session.execution_time_seconds,
            "total_opportunities_found": discovery_session.total_opportunities,
            "opportunities_by_strategy": opportunities_by_strategy,
            "strategy_execution_times": discovery_session.strategy_execution_times,
            "average_relevance_score": discovery_session.avg_relevance_score,
            "api_calls_made": discovery_session.api_calls_made,
            "progress_updates": len(progress_updates),
            "top_opportunities": [
                {
                    "organization": getattr(opp, 'funder_name', 'Unknown'),
                    "title": getattr(opp, 'title', ''),
                    "amount": getattr(opp, 'funding_amount_max', 0),
                    "relevance": getattr(opp, 'relevance_score', 0.0),
                    "source": str(getattr(opp, 'source_type', ''))
                }
                for opp in discovery_session.top_opportunities[:5]
            ],
            "session_summary": session_summary,
            "bridge_architecture": "unified_multitrack_bridge",
            "phase": "4B"
        }
        
    except Exception as e:
        logger.error(f"Unified discovery failed for profile {profile_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unified discovery failed: {str(e)}")

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
            # WebSocket progress integration available through workflow state
            progress_callback=None  # WebSocket updates handled by workflow state
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

@app.get("/api/processors/architecture/overview")
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
        logger.error(f"Failed to get architecture overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/processors/migration/status")
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
        logger.error(f"Failed to get migration status: {e}")
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
        
        results = {"track": "nonprofit"}
        
        # Import configuration objects needed for both BMF and ProPublica
        from src.core.data_models import WorkflowConfig, ProcessorConfig
        
        # Execute BMF filtering if no specific EIN
        if not ein:
            bmf_instance = engine.registry.get_processor("bmf_filter")
            if bmf_instance:
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
                logger.info(f"BMF result success: {bmf_result.success}")
                logger.info(f"BMF result data keys: {list(bmf_result.data.keys()) if bmf_result.data else 'None'}")
                if bmf_result.success and bmf_result.data:
                    results["bmf_results"] = bmf_result.data.get("organizations", [])
                else:
                    results["bmf_results"] = []
        
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
            logger.info(f"ProPublica result success: {pp_result.success}")
            logger.info(f"ProPublica result data keys: {list(pp_result.data.keys()) if pp_result.data else 'None'}")
            if pp_result.success and pp_result.data:
                results["propublica_results"] = pp_result.data.get("organizations", [])
            else:
                results["propublica_results"] = []
        
        # Phase 3.1: Integrate with FunnelManager for web interface
        try:
            from src.discovery.funnel_manager import FunnelManager
            from src.discovery.base_discoverer import DiscoveryResult, FunnelStage, FundingType
            
            # Get or create funnel manager instance
            if not hasattr(app.state, 'funnel_manager'):
                app.state.funnel_manager = FunnelManager()
            funnel_manager = app.state.funnel_manager
            
            # Convert results to DiscoveryResult objects
            discovery_results = []
            
            # Convert BMF results
            for bmf_org in results.get("bmf_results", []):
                discovery_result = DiscoveryResult(
                    organization_name=bmf_org.get('name', 'Unknown Organization'),
                    source_type=FundingType.GRANTS,
                    discovery_source='bmf_filter',
                    opportunity_id=f"bmf_{bmf_org.get('ein', 'unknown')}_{int(datetime.now().timestamp())}",
                    description=f"Nonprofit organization from IRS Business Master File. Revenue: ${bmf_org.get('revenue', 0) or 0:,}",
                    raw_score=0.7,
                    compatibility_score=0.6,
                    confidence_level=0.8,
                    funnel_stage=FunnelStage.PROSPECTS
                )
                discovery_results.append(discovery_result)
            
            # Convert ProPublica results
            for pp_org in results.get("propublica_results", []):
                discovery_result = DiscoveryResult(
                    organization_name=pp_org.get('name', 'Unknown Organization'),
                    source_type=FundingType.GRANTS,
                    discovery_source='propublica_fetch',
                    opportunity_id=f"propublica_{pp_org.get('ein', 'unknown')}_{int(datetime.now().timestamp())}",
                    description=f"Nonprofit organization from ProPublica database. Revenue: ${pp_org.get('revenue', 0) or 0:,}",
                    raw_score=0.8,
                    compatibility_score=0.7,
                    confidence_level=0.9,
                    funnel_stage=FunnelStage.PROSPECTS
                )
                discovery_results.append(discovery_result)
            
            # Add to funnel manager if we have a profile context
            if profile_context and discovery_results:
                profile_id = profile_context.get('profile_id', 'test_profile')
                funnel_manager.add_opportunities(profile_id, discovery_results)
                logger.info(f"Added {len(discovery_results)} opportunities to funnel for profile {profile_id}")
            
        except Exception as e:
            logger.error(f"Failed to integrate with FunnelManager: {str(e)}")
        
        # Calculate total opportunities found from all sources
        total_bmf = len(results.get("bmf_results", []))
        total_propublica = len(results.get("propublica_results", []))
        total_found = total_bmf + total_propublica
        
        return {
            "status": "completed",
            "track": "nonprofit",
            "total_found": total_found,
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
        
        results = {"track": "federal"}
        
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
        
        results = {"track": "state"}
        
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
        
        results = {"track": "commercial"}
        
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

# Funnel Stage API endpoints
@app.get("/api/funnel/stages")
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

@app.get("/api/opportunities")
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
                "funnel_stage": "qualified_prospects",
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/funnel/{profile_id}/opportunities")
async def get_profile_opportunities(profile_id: str, stage: Optional[str] = None):
    """Get opportunities by funnel stage for a profile."""
    try:
        from src.discovery.funnel_manager import FunnelManager
        from src.discovery.base_discoverer import FunnelStage
        
        # Use the same funnel manager instance as discovery endpoints
        if not hasattr(app.state, 'funnel_manager'):
            app.state.funnel_manager = FunnelManager()
        funnel_manager = app.state.funnel_manager
        
        if stage:
            try:
                stage_enum = FunnelStage(stage)
                opportunities = funnel_manager.get_opportunities_by_stage(profile_id, stage_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")
        else:
            opportunities = funnel_manager.get_all_opportunities(profile_id)
        
        return {
            "profile_id": profile_id,
            "stage_filter": stage,
            "total_opportunities": len(opportunities),
            "opportunities": [{
                # Core opportunity fields (standardized schema)
                "opportunity_id": opp.opportunity_id,
                "organization_name": opp.organization_name,
                "funnel_stage": opp.funnel_stage.value,
                "source_type": opp.source_type.value,
                "discovery_source": opp.discovery_source,
                
                # Opportunity details
                "program_name": getattr(opp, 'program_name', None),
                "description": getattr(opp, 'description', None),
                "funding_amount": opp.funding_amount,
                "application_deadline": getattr(opp, 'application_deadline', None),
                
                # Scoring fields (standardized)
                "raw_score": getattr(opp, 'raw_score', 0.0),
                "compatibility_score": opp.compatibility_score,
                "confidence_level": getattr(opp, 'confidence_level', 0.0),
                
                # Advanced scoring (for candidates/targets/opportunities)
                "xml_990_score": getattr(opp, 'xml_990_score', None),
                "network_score": getattr(opp, 'network_score', None),
                "enhanced_score": getattr(opp, 'enhanced_score', None),
                "combined_score": getattr(opp, 'combined_score', None),
                
                # Metadata
                "is_schedule_i_grantee": getattr(opp, 'is_schedule_i_grantee', False),
                "discovered_at": opp.discovered_at.isoformat() if hasattr(opp, 'discovered_at') and opp.discovered_at else None,
                "stage_updated_at": opp.stage_updated_at.isoformat() if opp.stage_updated_at else None,
                "stage_notes": opp.stage_notes,
                
                # Contact and location info
                "contact_info": getattr(opp, 'contact_info', {}),
                "geographic_info": getattr(opp, 'geographic_info', {}),
                
                # Analysis factors
                "match_factors": getattr(opp, 'match_factors', {}),
                "risk_factors": getattr(opp, 'risk_factors', {}),
                
                # Analysis status
                "analysis_status": getattr(opp, 'analysis_status', {}),
                "strategic_analysis": getattr(opp, 'strategic_analysis', {}),
                "ai_analyzed": getattr(opp, 'ai_analyzed', False),
                "ai_processing": getattr(opp, 'ai_processing', False),
                "ai_error": getattr(opp, 'ai_error', False),
                "ai_summary": getattr(opp, 'ai_summary', None),
                "action_plan": getattr(opp, 'action_plan', None),
                
                # Legacy support
                "stage_color": opp.get_stage_color() if hasattr(opp, 'get_stage_color') else None
            } for opp in opportunities]
        }
        
    except Exception as e:
        logger.error(f"Failed to get profile opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/funnel/{profile_id}/opportunities/{opportunity_id}/stage")
async def update_opportunity_stage(
    profile_id: str, 
    opportunity_id: str, 
    stage_data: dict
):
    """Update opportunity funnel stage."""
    try:
        from src.discovery.funnel_manager import funnel_manager
        from src.discovery.base_discoverer import FunnelStage
        
        new_stage = stage_data.get("stage")
        notes = stage_data.get("notes")
        
        if not new_stage:
            raise HTTPException(status_code=400, detail="Stage is required")
        
        try:
            stage_enum = FunnelStage(new_stage)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid stage: {new_stage}")
        
        success = funnel_manager.set_opportunity_stage(
            profile_id, opportunity_id, stage_enum, notes
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        return {
            "success": True,
            "profile_id": profile_id,
            "opportunity_id": opportunity_id,
            "new_stage": new_stage,
            "notes": notes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update opportunity stage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/funnel/{profile_id}/opportunities/{opportunity_id}/promote")
async def promote_opportunity(profile_id: str, opportunity_id: str, notes_data: dict = None):
    """Promote opportunity to next funnel stage."""
    try:
        from src.discovery.funnel_manager import funnel_manager
        
        notes = notes_data.get("notes") if notes_data else None
        success = funnel_manager.promote_opportunity(profile_id, opportunity_id, notes)
        
        if not success:
            raise HTTPException(status_code=400, detail="Cannot promote opportunity (already at highest stage or not found)")
        
        return {
            "success": True,
            "profile_id": profile_id,
            "opportunity_id": opportunity_id,
            "action": "promoted",
            "notes": notes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to promote opportunity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/funnel/{profile_id}/opportunities/{opportunity_id}/demote")
async def demote_opportunity(profile_id: str, opportunity_id: str, notes_data: dict = None):
    """Demote opportunity to previous funnel stage."""
    try:
        from src.discovery.funnel_manager import funnel_manager
        
        notes = notes_data.get("notes") if notes_data else None
        success = funnel_manager.demote_opportunity(profile_id, opportunity_id, notes)
        
        if not success:
            raise HTTPException(status_code=400, detail="Cannot demote opportunity (already at lowest stage or not found)")
        
        return {
            "success": True,
            "profile_id": profile_id,
            "opportunity_id": opportunity_id,
            "action": "demoted",
            "notes": notes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to demote opportunity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/funnel/{profile_id}/metrics")
async def get_funnel_metrics(profile_id: str):
    """Get funnel conversion analytics for a profile."""
    try:
        from src.discovery.funnel_manager import FunnelManager
        
        # Use the same funnel manager instance as discovery endpoints
        if not hasattr(app.state, 'funnel_manager'):
            app.state.funnel_manager = FunnelManager()
        funnel_manager = app.state.funnel_manager
        
        metrics = funnel_manager.get_funnel_metrics(profile_id)
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get funnel metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/funnel/{profile_id}/recommendations")
async def get_stage_recommendations(profile_id: str):
    """Get recommendations for stage transitions."""
    try:
        from src.discovery.funnel_manager import FunnelManager
        
        # Use the same funnel manager instance as discovery endpoints
        if not hasattr(app.state, 'funnel_manager'):
            app.state.funnel_manager = FunnelManager()
        funnel_manager = app.state.funnel_manager
        
        recommendations = funnel_manager.get_stage_recommendations(profile_id)
        return {
            "profile_id": profile_id,
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Failed to get stage recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Debug endpoint to check funnel manager state
@app.get("/api/debug/funnel-status")
async def debug_funnel_status():
    """Debug endpoint to check funnel manager state."""
    try:
        from src.discovery.funnel_manager import FunnelManager
        
        # Check app.state instance
        if not hasattr(app.state, 'funnel_manager'):
            app.state.funnel_manager = FunnelManager()
        funnel_manager = app.state.funnel_manager
        
        all_profiles = list(funnel_manager.opportunities.keys())
        profile_counts = {
            profile_id: len(opportunities) 
            for profile_id, opportunities in funnel_manager.opportunities.items()
        }
        
        return {
            "app_state_instance": {
                "total_profiles": len(all_profiles),
                "profiles_with_opportunities": all_profiles,
                "opportunity_counts": profile_counts,
                "instance_id": id(funnel_manager)
            }
        }
        
    except Exception as e:
        logger.error(f"Debug funnel status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/funnel/{profile_id}/bulk-transition")
async def bulk_stage_transition(profile_id: str, transition_data: dict):
    """Bulk transition multiple opportunities to target stage."""
    try:
        from src.discovery.funnel_manager import funnel_manager
        from src.discovery.base_discoverer import FunnelStage
        
        opportunity_ids = transition_data.get("opportunity_ids", [])
        target_stage = transition_data.get("target_stage")
        notes = transition_data.get("notes")
        
        if not opportunity_ids:
            raise HTTPException(status_code=400, detail="opportunity_ids is required")
        
        if not target_stage:
            raise HTTPException(status_code=400, detail="target_stage is required")
        
        try:
            stage_enum = FunnelStage(target_stage)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid stage: {target_stage}")
        
        results = funnel_manager.bulk_stage_transition(
            profile_id, opportunity_ids, stage_enum, notes
        )
        
        return {
            "profile_id": profile_id,
            "target_stage": target_stage,
            "results": results,
            "successful_transitions": sum(1 for success in results.values() if success),
            "total_opportunities": len(opportunity_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform bulk stage transition: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# PLAN Tab API Endpoints - 990 XML Analysis and Strategic Intelligence
@app.post("/api/analysis/scoring")
async def run_financial_scoring(request: Dict[str, Any]):
    """Run 990 XML financial analysis on selected organizations."""
    try:
        logger.info(f"Received scoring request: {request}")
        organizations = request.get("organizations", [])
        if not organizations:
            logger.error(f"No organizations provided in request: {request}")
            raise HTTPException(status_code=400, detail="Organizations list is required")
        
        logger.info(f"Running financial scoring on {len(organizations)} organizations")
        
        # Simulate analysis delay
        await asyncio.sleep(2)
        
        # Mock financial analysis results - in production would use actual processors
        results = {
            "analysis_id": f"financial_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "completed",
            "analyzed_count": len(organizations),
            "financial_metrics": {
                "average_revenue_trend": (random.random() - 0.5) * 20,  # -10% to +10%
                "average_health_score": 0.7 + random.random() * 0.3,   # 0.7 to 1.0
                "risk_distribution": {
                    "Low": random.randint(40, 60),
                    "Medium": random.randint(20, 40), 
                    "High": random.randint(0, 20)
                },
                "990_availability": random.randint(70, 95)  # 70% to 95%
            },
            "organization_results": [
                {
                    "organization_name": org.get("organization_name", "Unknown"),
                    "ein": org.get("ein"),
                    "revenue_trend": (random.random() - 0.5) * 20,
                    "health_score": 0.7 + random.random() * 0.3,
                    "risk_level": random.choice(["Low", "Medium", "High"]),
                    "990_available": random.random() > 0.25
                }
                for org in organizations
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Financial scoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/network")
async def run_network_analysis(request: Dict[str, Any]):
    """Run network discovery and board connection analysis."""
    try:
        logger.info(f"Received network request: {request}")
        organizations = request.get("organizations", [])
        if not organizations:
            logger.error(f"No organizations provided in network request: {request}")
            raise HTTPException(status_code=400, detail="Organizations list is required")
        
        logger.info(f"Running network analysis on {len(organizations)} organizations")
        
        # Simulate analysis delay
        await asyncio.sleep(1.5)
        
        # Mock network analysis results - in production would use board_network_analyzer
        results = {
            "analysis_id": f"network_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "completed",
            "analyzed_count": len(organizations),
            "network_metrics": {
                "total_board_connections": random.randint(50, 200),
                "unique_board_members": random.randint(30, 100),
                "network_density": round(random.uniform(0.2, 0.8), 3),
                "average_influence_score": round(random.uniform(0.4, 0.9), 3)
            },
            "organization_results": [
                {
                    "organization_name": org.get("organization_name", "Unknown"),
                    "ein": org.get("ein"),
                    "board_connections": random.randint(3, 25),
                    "strategic_links": random.randint(1, 15),
                    "influence_score": round(random.uniform(0.3, 0.9), 3),
                    "network_position": random.choice(["Central", "Peripheral", "Bridge", "Isolated"])
                }
                for org in organizations
            ],
            "top_connections": [
                {"name": "John Smith", "organizations": random.randint(3, 8), "influence": round(random.uniform(0.6, 0.95), 2)},
                {"name": "Sarah Johnson", "organizations": random.randint(3, 7), "influence": round(random.uniform(0.5, 0.9), 2)},
                {"name": "Michael Davis", "organizations": random.randint(2, 6), "influence": round(random.uniform(0.4, 0.85), 2)},
                {"name": "Jennifer Wilson", "organizations": random.randint(2, 5), "influence": round(random.uniform(0.4, 0.8), 2)},
                {"name": "Robert Brown", "organizations": random.randint(2, 5), "influence": round(random.uniform(0.3, 0.75), 2)}
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Network analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/intelligence/classify")
async def run_intelligence_classification(request: Dict[str, Any]):
    """Run AI-powered intelligent classification and opportunity scoring."""
    try:
        organizations = request.get("organizations", [])
        min_score = request.get("min_score", 0.3)
        
        if not organizations:
            raise HTTPException(status_code=400, detail="Organizations list is required")
        
        logger.info(f"Running AI classification on {len(organizations)} organizations")
        
        # Simulate analysis delay
        await asyncio.sleep(1)
        
        # Mock intelligence classification results - in production would use intelligent_classifier
        results = {
            "analysis_id": f"intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "completed",
            "analyzed_count": len(organizations),
            "min_score_threshold": min_score,
            "classification_metrics": {
                "average_score": round(random.uniform(0.5, 0.9), 3),
                "average_confidence": round(random.uniform(0.7, 0.95), 3),
                "recommendations": {
                    "Promote": random.randint(40, 70),
                    "Review": random.randint(20, 40),
                    "Monitor": random.randint(10, 30)
                }
            },
            "organization_results": [
                {
                    "organization_name": org.get("organization_name", "Unknown"),
                    "ein": org.get("ein"),
                    "classification_score": round(random.uniform(0.4, 0.95), 3),
                    "confidence_level": round(random.uniform(0.6, 0.95), 2),
                    "recommendation": random.choice(["Promote", "Review", "Monitor"]),
                    "key_factors": random.sample([
                        "Strong financial performance",
                        "Expanding network influence", 
                        "Mission alignment",
                        "Geographic relevance",
                        "Program compatibility",
                        "Historical success patterns"
                    ], 3),
                    "risk_factors": random.sample([
                        "Limited financial transparency",
                        "Recent leadership changes",
                        "Narrow funding base",
                        "Geographic constraints"
                    ], random.randint(0, 2))
                }
                for org in organizations
            ],
            "insights": [
                "Organizations show strong potential for strategic partnership development",
                "Network influence appears to be a key differentiator in this cohort",
                "Financial health indicators suggest sustainable growth trajectories",
                "Mission alignment scores indicate high compatibility with funding priorities"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Intelligence classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/enhanced-scoring")
async def run_enhanced_scoring(request: Dict[str, Any]):
    """Run enhanced scoring analysis using local Python algorithms."""
    try:
        logger.info(f"Received enhanced scoring request: {request}")
        organizations = request.get("organizations", [])
        if not organizations:
            logger.error(f"No organizations provided in enhanced scoring request: {request}")
            raise HTTPException(status_code=400, detail="Organizations list is required")
        
        logger.info(f"Running enhanced scoring on {len(organizations)} organizations")
        
        # Simulate analysis delay
        await asyncio.sleep(1.8)
        
        # Mock enhanced scoring results using local Python analysis
        results = {
            "analysis_id": f"enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "completed",
            "analyzed_count": len(organizations),
            "enhanced_metrics": {
                "average_mission_alignment": round(random.uniform(0.6, 0.9), 3),
                "average_eligibility_match": round(random.uniform(0.65, 0.95), 3),
                "average_opportunity_fit": round(random.uniform(0.7, 0.92), 3),
                "geographic_distribution": {
                    "Virginia": random.randint(60, 85),
                    "Regional": random.randint(10, 25),
                    "National": random.randint(5, 15)
                }
            },
            "organization_results": [
                {
                    "organization_name": org.get("organization_name", "Unknown"),
                    "ein": org.get("ein"),
                    "mission_alignment_score": round(random.uniform(0.5, 0.95), 3),
                    "eligibility_match_score": round(random.uniform(0.6, 0.98), 3), 
                    "opportunity_fit_score": round(random.uniform(0.65, 0.92), 3),
                    "enhanced_score": round(random.uniform(0.65, 0.93), 3),
                    "qualification_factors": [
                        random.choice(["Financial Strength", "Geographic Match", "Mission Alignment", "Foundation Type"]),
                        random.choice(["Activity Pattern", "Network Position", "Grant History", "Organizational Size"])
                    ]
                }
                for org in organizations
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Enhanced scoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/strategic-plan")
async def generate_strategic_plan(request: Dict[str, Any]):
    """Generate strategic plan and recommendations for qualified prospects."""
    try:
        logger.info(f"Received strategic planning request: {request}")
        profile_id = request.get("profile_id")
        
        if not profile_id:
            logger.error("No profile_id provided in strategic planning request")
            raise HTTPException(status_code=400, detail="Profile ID is required")
        
        logger.info(f"Generating strategic plan for profile: {profile_id}")
        
        # Simulate strategic analysis delay
        await asyncio.sleep(3.0)
        
        # Mock strategic planning results
        high_scoring_count = random.randint(5, 15)
        results = {
            "analysis_id": f"strategic_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "completed",
            "profile_id": profile_id,
            "strategic_metrics": {
                "qualified_prospects_count": high_scoring_count,
                "promotion_candidates": random.randint(3, 8),
                "average_combined_score": round(random.uniform(0.75, 0.92), 3),
                "recommended_focus_areas": [
                    "High-value network connections",
                    "Strategic partnerships",
                    "Board-level introductions"
                ]
            },
            "recommendations": [
                {
                    "priority": "High",
                    "action": "Initiate contact with top 3 scoring organizations",
                    "timeline": "Within 2 weeks",
                    "expected_outcome": "Strategic partnership discussions"
                },
                {
                    "priority": "Medium", 
                    "action": "Network mapping for board connections",
                    "timeline": "Within 1 month",
                    "expected_outcome": "Warm introductions identified"
                },
                {
                    "priority": "Medium",
                    "action": "Develop partnership proposals for candidates",
                    "timeline": "Within 6 weeks", 
                    "expected_outcome": "Formal collaboration framework"
                }
            ],
            "next_steps": [
                "Review enhanced scoring results for top prospects",
                "Prioritize network connections based on influence scores", 
                "Prepare strategic outreach materials",
                "Schedule follow-up analysis in 30 days"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Strategic planning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/plan/{profile_id}/prospects")
async def get_plan_prospects(profile_id: str, stage: Optional[str] = None):
    """Get prospects for PLAN tab analysis - supports comma-separated stages."""
    try:
        from src.discovery.funnel_manager import funnel_manager
        from src.discovery.base_discoverer import FunnelStage
        
        # Handle comma-separated stages for filtering
        if stage:
            stage_values = [s.strip() for s in stage.split(',')]
            opportunities = []
            for stage_val in stage_values:
                try:
                    stage_enum = FunnelStage(stage_val)
                    stage_opportunities = funnel_manager.get_opportunities_by_stage(profile_id, stage_enum)
                    opportunities.extend(stage_opportunities)
                except ValueError:
                    logger.warning(f"Invalid stage in filter: {stage_val}")
        else:
            opportunities = funnel_manager.get_all_opportunities(profile_id)
        
        # Convert to serializable format
        prospects_data = []
        for opp in opportunities:
            prospect = {
                "opportunity_id": opp.opportunity_id,
                "organization_name": opp.organization_name,
                "source_type": opp.source_type.value if hasattr(opp.source_type, 'value') else str(opp.source_type),
                "funnel_stage": opp.funnel_stage.value if hasattr(opp.funnel_stage, 'value') else str(opp.funnel_stage),
                "compatibility_score": opp.compatibility_score,
                "confidence_level": opp.confidence_level,
                "ein": getattr(opp, 'ein', None) or opp.external_data.get('ein', None),
                "discovered_at": opp.discovered_at.isoformat() if opp.discovered_at else None,
                "stage_updated_at": opp.stage_updated_at.isoformat() if opp.stage_updated_at else None,
                "stage_notes": opp.stage_notes,
                "funding_amount": opp.funding_amount,
                "application_deadline": opp.application_deadline,
                "geographic_info": opp.geographic_info,
                "match_factors": opp.match_factors
            }
            prospects_data.append(prospect)
        
        return {
            "profile_id": profile_id,
            "stage_filter": stage,
            "total_prospects": len(prospects_data),
            "opportunities": prospects_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get PLAN prospects for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analyze/network-data/{profile_id}")
async def get_network_visualization_data(profile_id: str):
    """Get network data and generate visualizations for ANALYZE tab."""
    try:
        logger.info(f"Generating network visualizations for profile: {profile_id}")
        
        # Import the existing network visualizer processor
        from src.processors.visualization.network_visualizer import create_network_visualizer
        
        # Mock network data for demo - in production, this would come from actual network analysis
        mock_network_data = {
            "organizations": [
                {
                    "ein": "12-3456789",
                    "name": "Health Innovation Foundation",
                    "ntee_code": "E21",
                    "revenue": 1800000,
                    "assets": 2400000
                },
                {
                    "ein": "98-7654321", 
                    "name": "Community Development Partners",
                    "ntee_code": "F30",
                    "revenue": 1250000,
                    "assets": 950000
                },
                {
                    "ein": "55-1234567",
                    "name": "Rural Development Initiative", 
                    "ntee_code": "T31",
                    "revenue": 2500000,
                    "assets": 1800000
                }
            ],
            "connections": [
                {
                    "org1_ein": "12-3456789",
                    "org2_ein": "98-7654321",
                    "shared_members": ["Sarah Johnson", "Michael Davis"],
                    "connection_strength": 0.8
                },
                {
                    "org1_ein": "98-7654321", 
                    "org2_ein": "55-1234567",
                    "shared_members": ["Jennifer Wilson"],
                    "connection_strength": 0.6
                }
            ],
            "influence_scores": {
                "individual_influence": {
                    "Sarah Johnson": {
                        "total_influence_score": 8.5,
                        "organizations": 3,
                        "board_positions": ["Chair", "Member"]
                    },
                    "Michael Davis": {
                        "total_influence_score": 6.2,
                        "organizations": 2,
                        "board_positions": ["Vice Chair", "Treasurer"] 
                    },
                    "Jennifer Wilson": {
                        "total_influence_score": 4.8,
                        "organizations": 2,
                        "board_positions": ["Member", "Secretary"]
                    }
                }
            },
            "network_metrics": {
                "organization_metrics": {
                    "12-3456789": {"centrality": 0.75, "betweenness": 0.6},
                    "98-7654321": {"centrality": 0.85, "betweenness": 0.8},
                    "55-1234567": {"centrality": 0.65, "betweenness": 0.4}
                }
            }
        }
        
        # Create visualizer instance
        visualizer = create_network_visualizer()
        
        # Generate both network types
        try:
            network_fig = visualizer.create_interactive_network(mock_network_data, "Board Member Network")
            influence_fig = visualizer.create_influence_network(mock_network_data)
            
            # Convert to HTML for embedding
            board_network_html = network_fig.to_html(
                include_plotlyjs='cdn',
                div_id="board-network-plotly-div",
                config={'displayModeBar': True, 'responsive': True}
            )
            
            influence_network_html = influence_fig.to_html(
                include_plotlyjs='cdn',
                div_id="influence-network-plotly-div", 
                config={'displayModeBar': True, 'responsive': True}
            )
            
            return {
                "profile_id": profile_id,
                "board_network_html": board_network_html,
                "influence_network_html": influence_network_html,
                "network_metrics": mock_network_data.get('network_metrics', {}),
                "influence_scores": mock_network_data.get('influence_scores', {}),
                "total_organizations": len(mock_network_data['organizations']),
                "total_connections": len(mock_network_data['connections']),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as viz_error:
            logger.error(f"Network visualization generation failed: {viz_error}")
            # Return basic data without visualizations
            return {
                "profile_id": profile_id,
                "board_network_html": "<div class='text-center py-8'><h3>Network visualization temporarily unavailable</h3></div>",
                "influence_network_html": "<div class='text-center py-8'><h3>Influence network temporarily unavailable</h3></div>",
                "network_metrics": mock_network_data.get('network_metrics', {}),
                "influence_scores": mock_network_data.get('influence_scores', {}),
                "error": "Visualization generation failed",
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Network data retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate network visualizations: {str(e)}")

# ENHANCED AI ANALYSIS ENDPOINTS - Comprehensive AI Lite & AI Heavy Processing

@app.post("/api/ai/lite-analysis")
async def execute_ai_lite_analysis(request: Dict[str, Any]):
    """
    Execute AI Lite batch analysis using comprehensive data packets.
    
    Request format:
    {
        "selected_profile": {...},
        "candidates": [...],
        "model_preference": "gpt-3.5-turbo",
        "cost_limit": 0.01
    }
    """
    try:
        logger.info("Starting AI Lite batch analysis")
        
        # Get AI service manager
        ai_service = get_ai_service_manager()
        
        # Validate request data
        if not request.get("candidates"):
            raise HTTPException(status_code=400, detail="No candidates provided for analysis")
            
        if not request.get("selected_profile"):
            raise HTTPException(status_code=400, detail="Profile context required for AI analysis")
        
        # Execute AI Lite analysis
        result = await ai_service.execute_ai_lite_analysis(request)
        
        return {
            "status": "success",
            "analysis_type": "ai_lite",
            "result": result,
            "session_summary": ai_service.get_session_summary()
        }
        
    except Exception as e:
        logger.error(f"AI Lite analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI Lite analysis failed: {str(e)}")

@app.post("/api/ai/deep-research")
async def execute_ai_heavy_research(request: Dict[str, Any]):
    """
    Execute AI Heavy deep research using comprehensive data packets.
    
    Request format:
    {
        "target_opportunity": {...},
        "selected_profile": {...},
        "ai_lite_results": {...},
        "model_preference": "gpt-4",
        "cost_budget": 0.25,
        "research_priority_areas": [...],
        "research_risk_areas": [...],
        "research_intelligence_gaps": [...]
    }
    """
    try:
        logger.info("Starting AI Heavy deep research")
        
        # Get AI service manager
        ai_service = get_ai_service_manager()
        
        # Validate request data
        if not request.get("target_opportunity"):
            raise HTTPException(status_code=400, detail="Target opportunity required for deep research")
            
        if not request.get("selected_profile"):
            raise HTTPException(status_code=400, detail="Profile context required for AI research")
        
        # Execute AI Heavy research
        result = await ai_service.execute_ai_heavy_research(request)
        
        return {
            "status": "success",
            "analysis_type": "ai_heavy",
            "result": result,
            "session_summary": ai_service.get_session_summary()
        }
        
    except Exception as e:
        logger.error(f"AI Heavy research failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI Heavy research failed: {str(e)}")

@app.get("/api/ai/analysis-status/{request_id}")
async def get_ai_analysis_status(request_id: str):
    """Get status of a specific AI processing request."""
    try:
        ai_service = get_ai_service_manager()
        status = ai_service.get_processing_status(request_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
        
        return {
            "status": "success",
            "request_status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get AI analysis status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/session-summary")
async def get_ai_session_summary():
    """Get comprehensive AI session summary with cost tracking."""
    try:
        ai_service = get_ai_service_manager()
        summary = ai_service.get_session_summary()
        
        return {
            "status": "success",
            "session_summary": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI session summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/cost-estimates")
async def get_ai_cost_estimates(candidate_count: int = 1, research_count: int = 1):
    """Get cost estimates for AI processing."""
    try:
        ai_service = get_ai_service_manager()
        estimates = ai_service.get_cost_estimates(candidate_count, research_count)
        
        return {
            "status": "success",
            "cost_estimates": estimates,
            "pricing_info": {
                "ai_lite_per_candidate": "$0.0001 - $0.0015",
                "ai_heavy_per_research": "$0.10 - $0.25",
                "model_tiers": {
                    "ai_lite": "GPT-3.5 Turbo (cost-optimized)",
                    "ai_heavy": "GPT-4 (premium analysis)"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI cost estimates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/batch-analysis")
async def execute_batch_ai_analysis(request: Dict[str, Any]):
    """
    Execute combined AI Lite + AI Heavy analysis pipeline.
    
    First runs AI Lite on all candidates, then runs AI Heavy on top-ranked targets.
    """
    try:
        logger.info("Starting batch AI analysis pipeline")
        
        # Get AI service manager
        ai_service = get_ai_service_manager()
        
        # Validate request data
        if not request.get("candidates"):
            raise HTTPException(status_code=400, detail="No candidates provided for batch analysis")
            
        if not request.get("selected_profile"):
            raise HTTPException(status_code=400, detail="Profile context required for batch analysis")
        
        # Step 1: Execute AI Lite analysis
        logger.info("Phase 1: AI Lite batch analysis")
        ai_lite_result = await ai_service.execute_ai_lite_analysis(request)
        
        # Step 2: Identify top candidates for deep research
        top_candidates_count = request.get("deep_research_count", 3)
        candidates_data = request.get("candidates", [])
        
        # Sort by AI Lite priority ranking and select top candidates
        if "candidate_results" in ai_lite_result:
            top_candidates = []
            for candidate in candidates_data:
                opp_id = candidate.get("opportunity_id")
                if opp_id in ai_lite_result["candidate_results"]:
                    ai_analysis = ai_lite_result["candidate_results"][opp_id]["ai_analysis"]
                    candidate["ai_lite_results"] = ai_analysis
                    top_candidates.append((candidate, ai_analysis["priority_rank"]))
            
            # Sort by priority rank and take top N
            top_candidates.sort(key=lambda x: x[1])
            selected_candidates = [c[0] for c in top_candidates[:top_candidates_count]]
        else:
            selected_candidates = candidates_data[:top_candidates_count]
        
        # Step 3: Execute AI Heavy research on top candidates
        logger.info(f"Phase 2: AI Heavy research on {len(selected_candidates)} top candidates")
        deep_research_results = []
        
        for candidate in selected_candidates:
            try:
                research_request = {
                    "target_opportunity": candidate,
                    "selected_profile": request["selected_profile"],
                    "ai_lite_results": candidate.get("ai_lite_results", {}),
                    "model_preference": request.get("model_preference", "gpt-4"),
                    "cost_budget": request.get("cost_budget", 0.25)
                }
                
                research_result = await ai_service.execute_ai_heavy_research(research_request)
                deep_research_results.append({
                    "candidate": candidate,
                    "research_result": research_result
                })
                
            except Exception as e:
                logger.warning(f"Deep research failed for {candidate.get('organization_name', 'Unknown')}: {str(e)}")
                deep_research_results.append({
                    "candidate": candidate,
                    "research_result": {"error": str(e)}
                })
        
        # Compile comprehensive results
        return {
            "status": "success",
            "analysis_type": "batch_pipeline",
            "ai_lite_result": ai_lite_result,
            "deep_research_results": deep_research_results,
            "pipeline_summary": {
                "total_candidates_analyzed": len(candidates_data),
                "deep_research_conducted": len(selected_candidates),
                "successful_deep_research": len([r for r in deep_research_results if "error" not in r["research_result"]])
            },
            "session_summary": ai_service.get_session_summary()
        }
        
    except Exception as e:
        logger.error(f"Batch AI analysis pipeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

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
            "/api/funnel/stages",
            "/api/funnel/{profile_id}/opportunities",
            "/api/funnel/{profile_id}/metrics",
            "/api/analysis/scoring",
            "/api/analysis/network", 
            "/api/intelligence/classify",
            "/api/plan/{profile_id}/prospects",
            "/api/analyze/network-data/{profile_id}",
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
    logger.info(f"Starting Catalynx Web Interface on http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )