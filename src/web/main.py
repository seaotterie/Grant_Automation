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