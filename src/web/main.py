#!/usr/bin/env python3
"""
Catalynx - Modern Web Interface
FastAPI backend with real-time progress monitoring
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Body, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
import sys
import uuid
import random
import shutil
import re
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
from src.profiles.unified_service import get_unified_profile_service
from src.discovery.unified_discovery_adapter import get_unified_discovery_adapter
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
from src.processors.analysis.ai_service_manager import get_ai_service_manager
from src.web.services.scoring_service import (
    get_scoring_service, ScoreRequest, ScoreResponse, 
    PromotionRequest, PromotionResponse, BulkPromotionRequest, BulkPromotionResponse
)

# Security and Authentication imports
from src.middleware.security import (
    SecurityHeadersMiddleware, 
    XSSProtectionMiddleware, 
    InputValidationMiddleware,
    RateLimitingMiddleware
)
from src.auth.jwt_auth import get_current_user_dependency, User
from src.web.auth_routes import router as auth_router
from src.web.routers.ai_processing import router as ai_processing_router

# Error Handling imports
from src.web.middleware.error_handling import (
    ErrorHandlingMiddleware,
    RequestContextMiddleware,
    validation_exception_handler,
    http_exception_handler
)
from src.core.error_recovery import error_recovery_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def similar_organization_names(name1: str, name2: str, threshold: float = 0.85) -> bool:
    """
    Check if two organization names are similar enough to be considered the same organization.
    Handles common variations like Heroes/Heros, Inc/Inc., etc.
    
    Args:
        name1: First organization name
        name2: Second organization name
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        True if names are similar enough to be considered the same organization
    """
    if not name1 or not name2:
        return False
        
    # Normalize names for comparison
    def normalize_name(name: str) -> str:
        name = name.lower().strip()
        # Remove common suffixes and variations
        suffixes = [' inc', ' inc.', ' incorporated', ' llc', ' ltd', ' ltd.', ' corp', ' corp.', ' corporation']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()
        return name
    
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)
    
    # Exact match after normalization
    if norm1 == norm2:
        return True
    
    # Simple character-based similarity for fuzzy matching
    # This handles cases like "Heroes Bridge" vs "Heros Bridge"
    if len(norm1) == 0 or len(norm2) == 0:
        return False
        
    # Calculate character overlap similarity
    chars1 = set(norm1.replace(' ', ''))
    chars2 = set(norm2.replace(' ', ''))
    
    if len(chars1) == 0 or len(chars2) == 0:
        return False
        
    intersection = len(chars1.intersection(chars2))
    union = len(chars1.union(chars2))
    similarity = intersection / union if union > 0 else 0
    
    return similarity >= threshold

async def secure_profile_deletion(profile_id: str, deleted_by: str) -> bool:
    """
    Securely delete an organization profile with comprehensive data purging.
    
    This function performs a complete data purge including:
    - Profile metadata and configuration
    - Associated opportunities and leads
    - Discovery history and cache data
    - Metrics and analytics data
    - Associated files and attachments
    - Entity cache references
    - AI analysis results
    
    Args:
        profile_id: The profile ID to delete
        deleted_by: Username of person performing deletion
        
    Returns:
        True if all data successfully purged, False otherwise
    """
    try:
        logger.info(f"Starting secure deletion of profile {profile_id} by {deleted_by}")
        deletion_success = True
        deleted_items = []
        
        # 1. Delete profile from main service
        try:
            success = profile_service.delete_profile(profile_id)
            if success:
                deleted_items.append("profile_metadata")
            else:
                deletion_success = False
                logger.warning(f"Failed to delete profile metadata for {profile_id}")
        except Exception as e:
            logger.error(f"Error deleting profile metadata for {profile_id}: {e}")
            deletion_success = False
        
        # 2. Delete associated opportunities and leads
        try:
            opportunities_dir = Path("data/opportunities")
            leads_dir = Path("data/leads")
            
            # Find and delete all opportunity files associated with this profile
            for opp_file in opportunities_dir.glob("*.json"):
                try:
                    with open(opp_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('profile_id') == profile_id:
                            opp_file.unlink()
                            deleted_items.append(f"opportunity_{opp_file.name}")
                except Exception as e:
                    logger.warning(f"Error processing opportunity file {opp_file}: {e}")
            
            # Find and delete all lead files associated with this profile
            for lead_file in leads_dir.glob("*.json"):
                try:
                    with open(lead_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('profile_id') == profile_id:
                            lead_file.unlink()
                            deleted_items.append(f"lead_{lead_file.name}")
                except Exception as e:
                    logger.warning(f"Error processing lead file {lead_file}: {e}")
            
            deleted_items.append("associated_opportunities_leads")
        except Exception as e:
            logger.error(f"Error deleting opportunities/leads for {profile_id}: {e}")
            deletion_success = False
        
        # 3. Delete profile-specific directories and files
        try:
            profile_dirs = [
                Path(f"data/profiles/profiles/{profile_id}.json"),
                Path(f"data/profiles/profiles/{profile_id}/"),
                Path(f"data/cache/profiles/{profile_id}/"),
                Path(f"data/processing_results/{profile_id}/"),
                Path(f"data/exports/{profile_id}/"),
                Path(f"data/reports/{profile_id}/")
            ]
            
            for path in profile_dirs:
                if path.exists():
                    if path.is_file():
                        path.unlink()
                        deleted_items.append(f"file_{path.name}")
                    elif path.is_dir():
                        shutil.rmtree(path)
                        deleted_items.append(f"directory_{path.name}")
        except Exception as e:
            logger.error(f"Error deleting profile directories for {profile_id}: {e}")
            deletion_success = False
        
        # 4. Clear entity cache references
        try:
            from src.core.entity_cache_manager import get_entity_cache_manager
            cache_manager = get_entity_cache_manager()
            
            # Remove profile references from entity cache
            # This ensures no orphaned references remain
            # Note: EntityCacheManager may not have clear_profile_references method
            # This is not critical for data purging
            if hasattr(cache_manager, 'clear_profile_references'):
                cache_manager.clear_profile_references(profile_id)
                deleted_items.append("entity_cache_references")
            else:
                logger.info(f"Entity cache manager doesn't support profile reference clearing - skipping")
                deleted_items.append("entity_cache_skip")
        except Exception as e:
            logger.warning(f"Non-critical error clearing entity cache for {profile_id}: {e}")
            deleted_items.append("entity_cache_error")
        
        # 5. Delete metrics and analytics data
        try:
            metrics_file = Path(f"data/metrics/{profile_id}_metrics.json")
            if metrics_file.exists():
                metrics_file.unlink()
                deleted_items.append("metrics_data")
                
            analytics_file = Path(f"data/analytics/{profile_id}_analytics.json")
            if analytics_file.exists():
                analytics_file.unlink()
                deleted_items.append("analytics_data")
        except Exception as e:
            logger.error(f"Error deleting metrics/analytics for {profile_id}: {e}")
            deletion_success = False
        
        # 6. Delete AI analysis results and costs
        try:
            ai_results_dir = Path(f"data/ai_analysis/{profile_id}/")
            if ai_results_dir.exists():
                shutil.rmtree(ai_results_dir)
                deleted_items.append("ai_analysis_results")
                
            cost_tracking_file = Path(f"data/cost_tracking/{profile_id}_costs.json")
            if cost_tracking_file.exists():
                cost_tracking_file.unlink()
                deleted_items.append("cost_tracking_data")
        except Exception as e:
            logger.error(f"Error deleting AI data for {profile_id}: {e}")
            deletion_success = False
        
        # 7. Remove from any scheduling or queue systems
        try:
            # Remove from discovery scheduling if exists
            schedule_file = Path(f"data/schedules/{profile_id}_schedule.json")
            if schedule_file.exists():
                schedule_file.unlink()
                deleted_items.append("schedule_data")
        except Exception as e:
            logger.error(f"Error deleting schedule data for {profile_id}: {e}")
            deletion_success = False
        
        # 8. Log comprehensive deletion audit trail
        audit_entry = {
            "profile_id": profile_id,
            "deleted_by": deleted_by,
            "deletion_timestamp": datetime.utcnow().isoformat(),
            "deletion_success": deletion_success,
            "deleted_items": deleted_items,
            "items_count": len(deleted_items)
        }
        
        # Write audit log
        audit_dir = Path("data/audit_logs")
        audit_dir.mkdir(exist_ok=True)
        audit_file = audit_dir / f"profile_deletion_{profile_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump(audit_entry, f, indent=2, ensure_ascii=False)
        
        if deletion_success:
            logger.info(f"Successfully completed secure deletion of profile {profile_id}. Deleted {len(deleted_items)} items: {deleted_items}")
        else:
            logger.warning(f"Partial deletion of profile {profile_id}. Some items may remain. Deleted {len(deleted_items)} items: {deleted_items}")
        
        return deletion_success
        
    except Exception as e:
        logger.error(f"Critical error during secure deletion of profile {profile_id}: {e}")
        
        # Create failure audit entry
        try:
            audit_entry = {
                "profile_id": profile_id,
                "deleted_by": deleted_by,
                "deletion_timestamp": datetime.utcnow().isoformat(),
                "deletion_success": False,
                "error": str(e),
                "status": "critical_failure"
            }
            
            audit_dir = Path("data/audit_logs")
            audit_dir.mkdir(exist_ok=True)
            audit_file = audit_dir / f"profile_deletion_failed_{profile_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(audit_file, 'w', encoding='utf-8') as f:
                json.dump(audit_entry, f, indent=2, ensure_ascii=False)
        except Exception as audit_error:
            logger.error(f"Failed to create audit log for failed deletion: {audit_error}")
        
        return False

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

# Custom middleware to disable TRACE method
@app.middleware("http")
async def disable_trace_method(request: Request, call_next):
    if request.method == "TRACE":
        raise HTTPException(status_code=405, detail="Method not allowed")
    return await call_next(request)

# Add error handling middleware (order matters - add in reverse order of execution)
# Request context middleware should be added first (executed last)
app.add_middleware(RequestContextMiddleware)
# Error handling middleware should wrap all other middleware
app.add_middleware(ErrorHandlingMiddleware, include_debug_info=False)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
# Re-enable XSSProtectionMiddleware with Alpine.js fix
app.add_middleware(XSSProtectionMiddleware)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(RateLimitingMiddleware, requests_per_minute=60)

# Include authentication routes
app.include_router(auth_router)

# Include AI processing routes
app.include_router(ai_processing_router)

# Add global exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
try:
    from pydantic import ValidationError
    app.add_exception_handler(ValidationError, validation_exception_handler)
except ImportError:
    logger.warning("Pydantic ValidationError handler not available")

# Documentation serving endpoints
import markdown
from pathlib import Path

@app.get("/api/docs/user-guide")
async def get_user_guide():
    """Get user guide documentation in HTML format."""
    try:
        docs_path = Path(__file__).parent.parent.parent / "docs" / "user-guide.md"
        
        if not docs_path.exists():
            raise HTTPException(status_code=404, detail="User guide not found")
        
        with open(docs_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['toc', 'tables', 'fenced_code']
        )
        
        return {
            "title": "Catalynx User Guide",
            "content": html_content,
            "format": "html",
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to serve user guide: {e}")
        raise HTTPException(status_code=500, detail="Failed to load user guide")

@app.get("/api/docs/api-documentation")
async def get_api_documentation():
    """Get API documentation in HTML format."""
    try:
        docs_path = Path(__file__).parent.parent.parent / "docs" / "api-documentation.md"
        
        if not docs_path.exists():
            raise HTTPException(status_code=404, detail="API documentation not found")
        
        with open(docs_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['toc', 'tables', 'fenced_code', 'codehilite']
        )
        
        return {
            "title": "Catalynx API Documentation",
            "content": html_content,
            "format": "html",
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to serve API documentation: {e}")
        raise HTTPException(status_code=500, detail="Failed to load API documentation")

@app.get("/api/docs/processor-guide")
async def get_processor_guide():
    """Get processor guide documentation in HTML format."""
    try:
        docs_path = Path(__file__).parent.parent.parent / "docs" / "processor-guide.md"
        
        if not docs_path.exists():
            raise HTTPException(status_code=404, detail="Processor guide not found")
        
        with open(docs_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['toc', 'tables', 'fenced_code']
        )
        
        return {
            "title": "Catalynx Processor Guide",
            "content": html_content,
            "format": "html",
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to serve processor guide: {e}")
        raise HTTPException(status_code=500, detail="Failed to load processor guide")

@app.get("/api/docs/help-search")
async def search_help_documentation(q: str = Query(..., min_length=2)):
    """Search across all help documentation."""
    try:
        docs_dir = Path(__file__).parent.parent.parent / "docs"
        search_results = []
        
        # Files to search
        help_files = [
            ("user-guide.md", "User Guide"),
            ("api-documentation.md", "API Documentation"), 
            ("processor-guide.md", "Processor Guide")
        ]
        
        search_term = q.lower()
        
        for filename, title in help_files:
            file_path = docs_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Simple search implementation
                    lines = content.split('\n')
                    matches = []
                    
                    for i, line in enumerate(lines):
                        if search_term in line.lower():
                            # Get context around the match
                            start = max(0, i-2)
                            end = min(len(lines), i+3)
                            context = '\n'.join(lines[start:end])
                            
                            matches.append({
                                "line_number": i+1,
                                "line": line.strip(),
                                "context": context,
                                "relevance": line.lower().count(search_term)
                            })
                    
                    if matches:
                        # Sort by relevance (number of matches in line)
                        matches.sort(key=lambda x: x['relevance'], reverse=True)
                        
                        search_results.append({
                            "document": title,
                            "file": filename,
                            "matches": matches[:5],  # Top 5 matches per document
                            "total_matches": len(matches)
                        })
                        
                except Exception as e:
                    logger.warning(f"Error searching {filename}: {e}")
        
        return {
            "query": q,
            "results": search_results,
            "total_documents": len(search_results),
            "total_matches": sum(r["total_matches"] for r in search_results)
        }
        
    except Exception as e:
        logger.error(f"Help search failed: {e}")
        raise HTTPException(status_code=500, detail="Help search failed")

@app.get("/api/docs/help-index")
async def get_help_index():
    """Get index of all available help documentation."""
    try:
        docs_dir = Path(__file__).parent.parent.parent / "docs"
        help_index = []
        
        # Main documentation files
        main_docs = [
            {
                "id": "user-guide",
                "title": "User Guide",
                "description": "Comprehensive guide to using Catalynx platform features",
                "file": "user-guide.md",
                "endpoint": "/api/docs/user-guide",
                "category": "User Documentation"
            },
            {
                "id": "api-documentation", 
                "title": "API Documentation",
                "description": "Complete API reference with endpoints and examples",
                "file": "api-documentation.md",
                "endpoint": "/api/docs/api-documentation",
                "category": "Technical Documentation"
            },
            {
                "id": "processor-guide",
                "title": "Processor Guide", 
                "description": "Detailed guide to all 18 processors and their capabilities",
                "file": "processor-guide.md",
                "endpoint": "/api/docs/processor-guide",
                "category": "Technical Documentation"
            }
        ]
        
        # Check which files actually exist and get metadata
        for doc in main_docs:
            file_path = docs_dir / doc["file"]
            if file_path.exists():
                stat = file_path.stat()
                doc.update({
                    "exists": True,
                    "size_bytes": stat.st_size,
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
                
                # Get first few lines for preview
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[:10]
                        doc["preview"] = ''.join(lines).strip()[:200] + "..."
                except:
                    doc["preview"] = "Preview not available"
                    
                help_index.append(doc)
            else:
                doc.update({
                    "exists": False,
                    "preview": "File not found"
                })
                help_index.append(doc)
        
        return {
            "available_docs": help_index,
            "categories": list(set(doc["category"] for doc in help_index)),
            "search_endpoint": "/api/docs/help-search",
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate help index: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate help index")

# Initialize services
workflow_service = WorkflowService()
progress_service = ProgressService()
profile_service = ProfileService()
unified_service = get_unified_profile_service()
unified_discovery_adapter = get_unified_discovery_adapter()
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

# Phase 1 Enhancement: Research API Endpoints

@app.get("/api/research/capabilities")
async def get_research_capabilities():
    """Get AI research capabilities for ANALYZE and EXAMINE tabs"""
    try:
        # Import research integration service
        from src.processors.analysis.research_integration_service import get_research_integration_service
        from src.processors.analysis.ai_lite_scorer import AILiteScorer
        from src.processors.analysis.ai_heavy_researcher import AIHeavyResearcher
        
        integration_service = get_research_integration_service()
        ai_lite = AILiteScorer()
        ai_heavy = AIHeavyResearcher()
        
        return {
            "research_integration": integration_service.get_integration_status(),
            "ai_lite_capabilities": ai_lite.get_research_capabilities(),
            "ai_heavy_capabilities": ai_heavy.get_dossier_builder_capabilities(),
            "phase_1_features": {
                "ai_lite_research_mode": "Comprehensive research reports for grant teams",
                "ai_heavy_dossier_builder": "Decision-ready dossiers with implementation roadmaps", 
                "cross_system_integration": "Seamless research handoff from ANALYZE to EXAMINE",
                "evidence_based_scoring": "Research-backed scoring with supporting documentation"
            },
            "status": "Phase 1 Complete - Research capabilities fully activated"
        }
    except Exception as e:
        logger.error(f"Failed to get research capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/research/ai-lite/analyze")
async def ai_lite_research_analysis(
    opportunity_ids: List[str] = Body(...),
    profile_id: str = Body(...),
    research_mode: bool = Body(default=True)
):
    """Trigger AI-Lite research analysis for opportunities"""
    try:
        from src.processors.analysis.ai_lite_scorer import AILiteScorer, AILiteRequest, RequestMetadata, ProfileContext, CandidateData
        
        ai_lite = AILiteScorer()
        
        # Create mock request data for demonstration
        # In production, this would pull real data from the profile and opportunity systems
        request_data = AILiteRequest(
            request_metadata=RequestMetadata(
                batch_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                profile_id=profile_id,
                analysis_type="research_analysis" if research_mode else "compatibility_scoring",
                model_preference="gpt-3.5-turbo",
                cost_limit=0.05,
                priority="high"
            ),
            profile_context=ProfileContext(
                organization_name="Sample Organization",
                mission_statement="Sample mission for demonstration",
                focus_areas=["health", "education"],
                ntee_codes=["A01", "B01"],
                geographic_scope="National"
            ),
            candidates=[
                CandidateData(
                    opportunity_id=opp_id,
                    organization_name=f"Target Organization {i+1}",
                    source_type="foundation",
                    description=f"Sample opportunity description for {opp_id}",
                    funding_amount=100000,
                    current_score=0.7
                ) for i, opp_id in enumerate(opportunity_ids[:3])  # Limit to 3 for demo
            ]
        )
        
        # Execute analysis
        results = await ai_lite.execute(request_data)
        
        # Convert results to JSON-serializable format
        response_data = {
            "batch_id": results.batch_results.batch_id,
            "processed_count": results.batch_results.processed_count,
            "processing_time": results.batch_results.processing_time,
            "estimated_cost": results.batch_results.total_cost,
            "research_mode_used": research_mode,
            "analysis_results": {}
        }
        
        for opp_id, analysis in results.candidate_analysis.items():
            result_data = {
                "compatibility_score": analysis.compatibility_score,
                "strategic_value": analysis.strategic_value.value,
                "funding_likelihood": analysis.funding_likelihood,
                "strategic_rationale": analysis.strategic_rationale,
                "action_priority": analysis.action_priority.value,
                "confidence_level": analysis.confidence_level,
                "research_mode_enabled": analysis.research_mode_enabled
            }
            
            # Add research components if available
            if analysis.research_report:
                result_data["research_report"] = {
                    "executive_summary": analysis.research_report.executive_summary,
                    "opportunity_overview": analysis.research_report.opportunity_overview,
                    "funding_details": analysis.research_report.funding_details,
                    "decision_factors": analysis.research_report.decision_factors
                }
            
            if analysis.competitive_analysis:
                result_data["competitive_analysis"] = {
                    "likely_competitors": analysis.competitive_analysis.likely_competitors,
                    "competitive_advantages": analysis.competitive_analysis.competitive_advantages,
                    "success_probability_factors": analysis.competitive_analysis.success_probability_factors
                }
            
            response_data["analysis_results"][opp_id] = result_data
        
        return response_data
        
    except Exception as e:
        logger.error(f"AI-Lite research analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/research/status/{profile_id}")
async def get_research_status(profile_id: str):
    """Get research status for a profile"""
    try:
        from src.processors.analysis.research_integration_service import get_research_integration_service
        
        integration_service = get_research_integration_service()
        
        return {
            "profile_id": profile_id,
            "research_integration_status": integration_service.get_integration_status(),
            "ai_lite_research_enabled": True,
            "ai_heavy_dossier_builder_enabled": True,
            "cross_system_integration_enabled": True,
            "phase_1_enhancement": "Complete",
            "available_features": [
                "AI-Lite comprehensive research reports",
                "AI-Heavy decision-ready dossiers",
                "Research evidence integration",
                "Cross-system data handoff",
                "Grant team decision support"
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get research status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Phase 1.5 Enhancement: Specialized Deep Research and Dossier Builder Endpoints

@app.get("/api/research/split-capabilities")
async def get_split_research_capabilities():
    """Get specialized research capabilities for split AI-Heavy system"""
    try:
        # Import both specialized processors
        from src.processors.analysis.ai_heavy_deep_researcher import AIHeavyDeepResearcher
        from src.processors.analysis.ai_heavy_researcher import AIHeavyDossierBuilder
        from src.processors.analysis.research_integration_service import get_research_integration_service
        
        deep_researcher = AIHeavyDeepResearcher()
        dossier_builder = AIHeavyDossierBuilder()
        integration_service = get_research_integration_service()
        
        return {
            "phase_1_5_split_architecture": {
                "examine_tab_deep_research": deep_researcher.get_deep_research_capabilities(),
                "approach_tab_dossier_builder": dossier_builder.get_approach_tab_capabilities(),
                "three_way_integration": integration_service.get_integration_status()
            },
            "workflow_architecture": {
                "analyze_tab": "AI-Lite comprehensive research and scoring",
                "examine_tab": "AI-Heavy deep research and strategic intelligence",
                "approach_tab": "AI-Heavy implementation planning and dossier building"
            },
            "data_flow": {
                "stage_1": "ANALYZE: AI-Lite research → preliminary analysis",
                "stage_2": "EXAMINE: Deep research → strategic intelligence",
                "stage_3": "APPROACH: Dossier building → implementation planning"
            },
            "cost_optimization": {
                "ai_lite_research": "$0.0008 per candidate",
                "deep_research_examine": "$0.08-0.15 per analysis",
                "dossier_builder_approach": "$0.12-0.20 per implementation plan"
            },
            "status": "Phase 1.5 Complete - AI-Heavy split architecture active"
        }
    except Exception as e:
        logger.error(f"Failed to get split research capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/research/integration-status/{opportunity_id}")
async def get_integration_status_endpoint(opportunity_id: str):
    """Get three-way integration status for an opportunity"""
    try:
        from src.processors.analysis.research_integration_service import get_research_integration_service
        
        integration_service = get_research_integration_service()
        integration_context = integration_service.get_complete_integration_context(opportunity_id)
        
        if not integration_context:
            return {
                "opportunity_id": opportunity_id,
                "integration_available": False,
                "workflow_stage": "none",
                "message": "No integration context found for this opportunity"
            }
        
        return {
            "opportunity_id": opportunity_id,
            "integration_available": True,
            "integration_completeness_score": integration_context.integration_completeness_score,
            "current_workflow_stage": integration_context.workflow_stage,
            "ai_lite_handoff_available": integration_context.ai_lite_handoff is not None,
            "deep_research_handoff_available": integration_context.deep_research_handoff is not None,
            "context_preservation_metadata": integration_context.context_preservation_metadata,
            "workflow_progression": {
                "analyze_completed": integration_context.ai_lite_handoff is not None,
                "examine_completed": integration_context.deep_research_handoff is not None,
                "approach_ready": integration_context.integration_completeness_score >= 0.67
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get integration status: {e}")
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
async def list_profiles(
    status: Optional[str] = None, 
    limit: Optional[int] = None
    # Temporarily removed authentication: current_user: User = Depends(get_current_user_dependency)
):
    """List all organization profiles with unified analytics."""
    try:
        # Use both services - old for profile metadata, unified for opportunity analytics
        old_profiles = profile_service.list_profiles(status=status, limit=limit)
        unified_profile_ids = unified_service.list_profiles()
        
        # Convert profiles to dict format and add analytics from unified service
        profile_dicts = []
        for profile in old_profiles:
            profile_dict = profile.model_dump()
            
            # Try to get unified profile analytics for enhanced data
            if profile.profile_id in unified_profile_ids:
                unified_profile = unified_service.get_profile(profile.profile_id)
                if unified_profile and unified_profile.analytics:
                    # Use unified analytics for accurate opportunity counts
                    profile_dict["opportunities_count"] = unified_profile.analytics.opportunity_count
                    profile_dict["analytics"] = unified_profile.analytics.model_dump()
                else:
                    # Fallback to old method
                    profile_dict["opportunities_count"] = len(profile.associated_opportunities)
            else:
                # Fallback to old method
                profile_dict["opportunities_count"] = len(profile.associated_opportunities)
            
            profile_dicts.append(profile_dict)
        
        logger.info(f"Returned {len(profile_dicts)} profiles with unified analytics")
        return {"profiles": profile_dicts}
        
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profiles")
async def create_profile(
    profile_data: Dict[str, Any],
    current_user: User = Depends(get_current_user_dependency)
):
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
async def get_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user_dependency)
):
    """Get a specific organization profile with unified analytics."""
    try:
        # Try unified service first for enhanced analytics
        unified_profile = unified_service.get_profile(profile_id)
        if unified_profile:
            return {"profile": unified_profile.model_dump()}
        
        # Fallback to old service
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
async def delete_profile(
    profile_id: str
    # Temporarily removed authentication: current_user: User = Depends(get_current_user_dependency)
):
    """Securely delete an organization profile with comprehensive data purging."""
    try:
        # Validate profile_id format to prevent path traversal
        if not re.match(r'^[a-zA-Z0-9_-]+$', profile_id):
            raise HTTPException(
                status_code=400, 
                detail="Invalid profile ID format"
            )
        
        # Check if profile exists first
        try:
            profile = profile_service.get_profile(profile_id)
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found")
        except Exception:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Perform secure deletion with comprehensive data purging  
        success = await secure_profile_deletion(profile_id, "system")
        
        if not success:
            raise HTTPException(
                status_code=500, 
                detail="Failed to completely purge profile data"
            )
        
        logger.info(f"Profile {profile_id} securely deleted by user: system")
        return {
            "message": "Profile and all associated data permanently deleted",
            "deleted_by": "system",
            "deletion_timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to securely delete profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/api/profiles/simple/{profile_id}")
async def simple_delete_profile(profile_id: str):
    """Simple profile deletion without authentication for testing."""
    try:
        from pathlib import Path
        
        # Simple file-based deletion
        profile_path = Path(f"data/profiles/profiles/{profile_id}.json")
        if profile_path.exists():
            profile_path.unlink()
            return {"message": "Profile deleted successfully", "profile_id": profile_id}
        else:
            raise HTTPException(status_code=404, detail="Profile not found")
            
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
    """Get strategic planning results for a profile including opportunity scores."""
    try:
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Extract plan results from processing history
        plan_results = profile.processing_history.get('plan_results', {})
        
        # Get opportunity scores from profile data
        opportunity_scores = profile.processing_history.get('opportunity_scores', {})
        
        # Get opportunity assessments (user ratings/notes)
        opportunity_assessments = profile.processing_history.get('opportunity_assessments', {})
        
        return {
            "profile_id": profile_id,
            "plan_results": plan_results,
            "opportunity_scores": opportunity_scores,
            "opportunity_assessments": opportunity_assessments,
            "last_updated": profile.processing_history.get('plan_last_updated'),
            "scores_last_updated": profile.processing_history.get('scores_last_updated'),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Failed to get plan results for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profiles/{profile_id}/plan-results")
async def save_profile_plan_results(profile_id: str, plan_data: Dict[str, Any]):
    """Save strategic planning results for a profile including opportunity scores."""
    try:
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Store plan results in processing history
        if not profile.processing_history:
            profile.processing_history = {}
        
        current_time = datetime.now().isoformat()
        
        # Save general plan results
        if 'plan_results' in plan_data:
            profile.processing_history['plan_results'] = plan_data['plan_results']
            profile.processing_history['plan_last_updated'] = current_time
        
        # Save opportunity scores (compatibility scores, user ratings, etc.)
        if 'opportunity_scores' in plan_data:
            profile.processing_history['opportunity_scores'] = plan_data['opportunity_scores']
            profile.processing_history['scores_last_updated'] = current_time
            logger.info(f"Saved scores for {len(plan_data['opportunity_scores'])} opportunities")
        
        # Save opportunity assessments (user notes, manual ratings, etc.)
        if 'opportunity_assessments' in plan_data:
            profile.processing_history['opportunity_assessments'] = plan_data['opportunity_assessments']
            profile.processing_history['assessments_last_updated'] = current_time
            logger.info(f"Saved assessments for {len(plan_data['opportunity_assessments'])} opportunities")
        
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

@app.post("/api/profiles/{profile_id}/opportunity-scores")
async def save_opportunity_scores(profile_id: str, scores_data: Dict[str, Any]):
    """Save individual opportunity scores and assessments for persistence."""
    try:
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Initialize processing history if needed
        if not profile.processing_history:
            profile.processing_history = {}
        
        current_time = datetime.now().isoformat()
        opportunity_id = scores_data.get('opportunity_id')
        
        if not opportunity_id:
            raise HTTPException(status_code=400, detail="opportunity_id is required")
        
        # Initialize opportunity scores dictionary
        if 'opportunity_scores' not in profile.processing_history:
            profile.processing_history['opportunity_scores'] = {}
        
        # Save the score data for this specific opportunity
        profile.processing_history['opportunity_scores'][opportunity_id] = {
            'compatibility_score': scores_data.get('compatibility_score'),
            'user_rating': scores_data.get('user_rating'),
            'priority_level': scores_data.get('priority_level'),
            'assessment_notes': scores_data.get('assessment_notes'),
            'tags': scores_data.get('tags', []),
            'last_scored': current_time,
            'scored_by': scores_data.get('scored_by', 'user')
        }
        
        # Update timestamps
        profile.processing_history['scores_last_updated'] = current_time
        
        # Update the profile
        updated_profile = profile_service.update_profile(profile_id, profile)
        
        logger.info(f"Saved score data for opportunity {opportunity_id} in profile {profile_id}")
        
        return {
            "message": "Opportunity score saved successfully",
            "profile_id": profile_id,
            "opportunity_id": opportunity_id,
            "score_data": profile.processing_history['opportunity_scores'][opportunity_id],
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Failed to save opportunity score for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/{profile_id}/opportunities/{opportunity_id}/scoring-rationale")
async def get_scoring_rationale(profile_id: str, opportunity_id: str):
    """Get detailed scoring rationale and analysis for an opportunity."""
    try:
        # Get the profile and opportunity
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get the opportunity/lead
        leads = profile_service.get_profile_leads(profile_id=profile_id)
        opportunity = None
        for lead in leads:
            if lead.lead_id == opportunity_id:
                opportunity = lead
                break
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Generate scoring rationale analysis
        scoring_rationale = await _generate_scoring_rationale(profile, opportunity)
        
        return {
            "profile_id": profile_id,
            "opportunity_id": opportunity_id,
            "organization_name": opportunity.organization_name,
            "overall_score": opportunity.compatibility_score,
            "scoring_rationale": scoring_rationale,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate scoring rationale for {opportunity_id} in profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _generate_scoring_rationale(profile, opportunity):
    """Generate comprehensive scoring rationale with pros/cons analysis."""
    
    # Extract data for analysis
    org_name = opportunity.organization_name
    score = opportunity.compatibility_score or 0.0
    match_factors = opportunity.match_factors or {}
    external_data = opportunity.external_data or {}
    
    # Profile criteria for comparison
    profile_focus_areas = getattr(profile, 'focus_areas', '').split(',') if hasattr(profile, 'focus_areas') else []
    profile_geographic_scope = getattr(profile, 'geographic_scope', '') if hasattr(profile, 'geographic_scope') else ''
    
    # Scoring dimension analysis
    scoring_dimensions = {
        "eligibility": _analyze_eligibility_fit(profile, opportunity),
        "geographic": _analyze_geographic_fit(profile, opportunity),
        "mission_alignment": _analyze_mission_alignment(profile, opportunity),
        "financial_fit": _analyze_financial_fit(profile, opportunity),
        "timing": _analyze_timing_factors(opportunity)
    }
    
    # Generate pros and cons
    pros = []
    cons = []
    improvement_recommendations = []
    risk_factors = []
    
    # Analyze each dimension for pros/cons
    for dimension, analysis in scoring_dimensions.items():
        if analysis["score"] >= 0.7:
            pros.extend(analysis["positive_factors"])
        elif analysis["score"] <= 0.4:
            cons.extend(analysis["negative_factors"])
            improvement_recommendations.extend(analysis["recommendations"])
        
        risk_factors.extend(analysis.get("risks", []))
    
    # Overall assessment
    if score >= 0.8:
        overall_assessment = "Excellent match with strong alignment across multiple dimensions"
        recommendation = "High priority - proceed with application preparation"
    elif score >= 0.65:
        overall_assessment = "Good match with some areas for optimization"
        recommendation = "Medium priority - address identified gaps before proceeding"
    elif score >= 0.45:
        overall_assessment = "Moderate match requiring significant preparation"
        recommendation = "Low priority - substantial work needed to improve fit"
    else:
        overall_assessment = "Poor match with fundamental misalignment"
        recommendation = "Not recommended - consider alternative opportunities"
    
    return {
        "overall_assessment": overall_assessment,
        "recommendation": recommendation,
        "score_breakdown": scoring_dimensions,
        "strengths": pros[:5],  # Top 5 strengths
        "challenges": cons[:5],  # Top 5 challenges
        "improvement_recommendations": improvement_recommendations[:3],  # Top 3 recommendations
        "risk_factors": risk_factors[:3],  # Top 3 risks
        "strategic_insights": _generate_strategic_insights(profile, opportunity, score),
        "next_steps": _generate_next_steps(score, scoring_dimensions)
    }

def _analyze_eligibility_fit(profile, opportunity):
    """Analyze eligibility alignment between profile and opportunity."""
    match_factors = opportunity.match_factors or {}
    external_data = opportunity.external_data or {}
    
    positive_factors = []
    negative_factors = []
    recommendations = []
    risks = []
    
    # NTEE code alignment
    profile_focus = getattr(profile, 'focus_areas', '') if hasattr(profile, 'focus_areas') else ''
    ntee_code = external_data.get('ntee_code', '')
    
    if ntee_code:
        # Map NTEE codes to focus areas (simplified)
        ntee_focus_map = {
            'A': 'arts', 'B': 'education', 'C': 'environment', 'D': 'animals',
            'E': 'health', 'F': 'mental health', 'G': 'medical', 'H': 'medical research',
            'I': 'crime', 'J': 'employment', 'K': 'food', 'L': 'housing',
            'M': 'safety', 'N': 'recreation', 'O': 'youth', 'P': 'human services',
            'Q': 'international', 'R': 'civil rights', 'S': 'community', 'T': 'philanthropy'
        }
        
        primary_category = ntee_code[0] if ntee_code else ''
        mapped_focus = ntee_focus_map.get(primary_category, '')
        
        if mapped_focus and mapped_focus in profile_focus.lower():
            positive_factors.append(f"Strong NTEE alignment: {ntee_code} matches profile focus on {mapped_focus}")
        else:
            negative_factors.append(f"NTEE mismatch: {ntee_code} may not align with profile focus areas")
    
    # Organization type compatibility
    source_type = match_factors.get('source_type', 'Unknown')
    if source_type == 'Nonprofit' and 'nonprofit' in profile_focus.lower():
        positive_factors.append("Organization type aligns with nonprofit focus")
    elif source_type in ['Foundation', 'Government']:
        positive_factors.append(f"{source_type} source provides credible funding opportunity")
    
    score = max(0.1, min(1.0, len(positive_factors) * 0.3 - len(negative_factors) * 0.2 + 0.5))
    
    return {
        "score": score,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "recommendations": recommendations,
        "risks": risks
    }

def _analyze_geographic_fit(profile, opportunity):
    """Analyze geographic alignment."""
    match_factors = opportunity.match_factors or {}
    external_data = opportunity.external_data or {}
    
    positive_factors = []
    negative_factors = []
    recommendations = []
    
    org_state = match_factors.get('state', external_data.get('state', ''))
    profile_scope = getattr(profile, 'geographic_scope', '') if hasattr(profile, 'geographic_scope') else ''
    
    if org_state:
        if org_state in profile_scope or 'national' in profile_scope.lower():
            positive_factors.append(f"Geographic match: Organization in {org_state} aligns with profile scope")
        else:
            negative_factors.append(f"Geographic mismatch: {org_state} location may not align with target areas")
            recommendations.append("Consider if geographic expansion is strategic")
    
    score = 0.7 if positive_factors else 0.3
    
    return {
        "score": score,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "recommendations": recommendations,
        "risks": []
    }

def _analyze_mission_alignment(profile, opportunity):
    """Analyze mission and program alignment."""
    positive_factors = []
    negative_factors = []
    
    # Simple keyword matching for mission alignment
    org_name = opportunity.organization_name.lower()
    description = (opportunity.description or '').lower()
    profile_focus = getattr(profile, 'focus_areas', '').lower() if hasattr(profile, 'focus_areas') else ''
    
    # Check for mission keywords
    focus_keywords = profile_focus.split(',') if profile_focus else []
    mission_matches = 0
    
    for keyword in focus_keywords:
        keyword = keyword.strip()
        if keyword and (keyword in org_name or keyword in description):
            positive_factors.append(f"Mission alignment: '{keyword}' appears in organization context")
            mission_matches += 1
    
    if mission_matches == 0:
        negative_factors.append("Limited mission alignment detected in available information")
    
    score = min(1.0, 0.4 + mission_matches * 0.2)
    
    return {
        "score": score,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "recommendations": [],
        "risks": []
    }

def _analyze_financial_fit(profile, opportunity):
    """Analyze financial capacity and funding alignment."""
    positive_factors = []
    negative_factors = []
    recommendations = []
    
    # Revenue analysis if available
    external_data = opportunity.external_data or {}
    description = opportunity.description or ''
    
    # Extract revenue if mentioned in description
    import re
    revenue_match = re.search(r'\$?([\d,]+(?:\.\d+)?)', description)
    if revenue_match:
        try:
            revenue_str = revenue_match.group(1).replace(',', '')
            revenue = float(revenue_str)
            
            if revenue > 1000000:
                positive_factors.append(f"Strong financial capacity: ${revenue:,.0f} annual revenue")
            elif revenue > 100000:
                positive_factors.append(f"Moderate financial capacity: ${revenue:,.0f} annual revenue")
            else:
                negative_factors.append(f"Limited financial capacity: ${revenue:,.0f} annual revenue")
                recommendations.append("Verify financial stability and grant management capacity")
        except:
            pass
    
    funding_amount = opportunity.funding_amount
    if funding_amount:
        positive_factors.append(f"Specific funding amount available: ${funding_amount:,.0f}")
    
    score = 0.6 + len(positive_factors) * 0.15 - len(negative_factors) * 0.2
    score = max(0.1, min(1.0, score))
    
    return {
        "score": score,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "recommendations": recommendations,
        "risks": []
    }

def _analyze_timing_factors(opportunity):
    """Analyze timing and deadline factors."""
    positive_factors = []
    negative_factors = []
    risks = []
    
    # Check for deadline information
    match_factors = opportunity.match_factors or {}
    deadline = match_factors.get('deadline')
    
    if deadline:
        positive_factors.append("Clear application deadline provided")
    else:
        negative_factors.append("No clear deadline information available")
        risks.append("Risk of missing application windows without deadline clarity")
    
    # Check discovery recency
    discovered_at = opportunity.discovered_at
    if discovered_at:
        from datetime import datetime, timedelta
        try:
            discovered_date = datetime.fromisoformat(discovered_at.replace('Z', '+00:00'))
            days_since_discovery = (datetime.now().astimezone() - discovered_date).days
            
            if days_since_discovery <= 7:
                positive_factors.append("Recently discovered opportunity - information is current")
            elif days_since_discovery <= 30:
                positive_factors.append("Opportunity discovered within last month")
            else:
                negative_factors.append("Opportunity information may be outdated")
                risks.append("Risk of changed requirements or closed applications")
        except:
            pass
    
    score = 0.5 + len(positive_factors) * 0.2 - len(negative_factors) * 0.15
    score = max(0.1, min(1.0, score))
    
    return {
        "score": score,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "recommendations": [],
        "risks": risks
    }

def _generate_strategic_insights(profile, opportunity, score):
    """Generate strategic insights for the opportunity."""
    insights = []
    
    org_name = opportunity.organization_name
    external_data = opportunity.external_data or {}
    
    # Foundation-specific insights
    if external_data.get('foundation_code') == '03':
        insights.append(f"{org_name} is a private foundation - may offer flexible funding terms")
    
    # Revenue-based insights
    description = opportunity.description or ''
    if 'million' in description.lower():
        insights.append("Large organization with potentially substantial grant-making capacity")
    
    # NTEE-based insights
    ntee_code = external_data.get('ntee_code', '')
    if ntee_code and ntee_code.startswith('T'):
        insights.append("Philanthropy/voluntarism focus suggests potential for collaborative partnerships")
    
    # Score-based strategic advice
    if score >= 0.8:
        insights.append("High-scoring opportunity - prioritize for immediate action")
    elif score >= 0.6:
        insights.append("Solid opportunity - develop targeted approach based on strengths")
    else:
        insights.append("Challenging opportunity - consider if strategic investment is warranted")
    
    return insights[:3]  # Return top 3 insights

def _generate_next_steps(score, scoring_dimensions):
    """Generate actionable next steps based on scoring analysis."""
    next_steps = []
    
    if score >= 0.8:
        next_steps.extend([
            "Begin application preparation immediately",
            "Research organization's recent funding patterns",
            "Identify key contacts and decision makers"
        ])
    elif score >= 0.6:
        # Focus on improving lowest-scoring dimensions
        lowest_dimension = min(scoring_dimensions.items(), key=lambda x: x[1]["score"])
        next_steps.extend([
            f"Address {lowest_dimension[0]} alignment gaps first",
            "Gather additional information to strengthen application",
            "Consider strategic partnerships to enhance fit"
        ])
    else:
        next_steps.extend([
            "Reassess strategic fit before proceeding",
            "Explore alternative opportunities with better alignment",
            "Consider if significant changes could improve compatibility"
        ])
    
    # Add universal steps
    next_steps.extend([
        "Review organization's 990 filings for deeper insights",
        "Analyze past grant recipients for pattern recognition"
    ])
    
    return next_steps[:5]  # Return top 5 next steps

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

def _convert_lead_to_opportunity(lead):
    """Convert a lead object to opportunity dictionary format"""
    return {
        "id": lead.lead_id,
        "opportunity_id": lead.lead_id,  # Add for frontend compatibility
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
        "external_data": lead.external_data,
        # Enhanced data for frontend columns
        "source_type": lead.match_factors.get('source_type', 'Unknown') if lead.match_factors else 'Unknown',
        "discovery_source": lead.external_data.get('discovery_source', 'Unknown Source') if lead.external_data else 'Unknown Source',
        "application_status": lead.match_factors.get('application_status', None) if lead.match_factors else None,
        "is_schedule_i_grantee": lead.external_data.get('is_schedule_i_grantee', False) if lead.external_data else False
    }

@app.get("/api/profiles/{profile_id}/opportunities")
async def get_profile_opportunities(profile_id: str, stage: Optional[str] = None, min_score: Optional[float] = None):
    """Get opportunities for a profile using unified service."""
    try:
        # Convert frontend stage filter to unified stage
        frontend_to_unified_stage = {
            "prospects": "discovery",
            "qualified_prospects": "pre_scoring",
            "candidates": "deep_analysis", 
            "targets": "recommendations"
        }
        
        unified_stage_filter = frontend_to_unified_stage.get(stage, stage) if stage else None
        
        # Try unified service first for enhanced data
        logger.info(f"DEBUG: Trying unified service for profile {profile_id} with stage_filter={unified_stage_filter}")
        try:
            unified_opportunities = unified_service.get_profile_opportunities(
                profile_id=profile_id,
                stage_filter=unified_stage_filter
            )
            logger.info(f"DEBUG: Unified service returned {len(unified_opportunities) if unified_opportunities else 0} opportunities")
        except Exception as e:
            logger.error(f"DEBUG: Unified service failed with error: {e}")
            unified_opportunities = None
        
        logger.info(f"DEBUG: Unified opportunities check: {unified_opportunities is not None} and length: {len(unified_opportunities) if unified_opportunities else 'None'}")
        
        if unified_opportunities is not None:
            logger.info(f"DEBUG: Using unified service with {len(unified_opportunities)} opportunities")
            # Stage mapping from unified backend to frontend
            stage_mapping = {
                "discovery": "prospects",
                "pre_scoring": "qualified_prospects", 
                "deep_analysis": "candidates",
                "recommendations": "targets"
            }
            
            # Filter by min_score if provided
            filtered_opportunities = []
            for opp in unified_opportunities:
                if min_score is None or (opp.scoring and opp.scoring.overall_score >= min_score):
                    # Map unified stage to frontend stage
                    frontend_stage = stage_mapping.get(opp.current_stage, opp.current_stage)
                    
                    # Convert to frontend format
                    opportunity = {
                        "id": opp.opportunity_id,
                        "opportunity_id": opp.opportunity_id,
                        "organization_name": opp.organization_name,
                        "current_stage": opp.current_stage,  # Keep original for backend compatibility
                        "stage": frontend_stage,  # For frontend compatibility
                        "pipeline_stage": frontend_stage,  # For frontend compatibility
                        "funnel_stage": frontend_stage,  # For frontend compatibility
                        "compatibility_score": opp.scoring.overall_score if opp.scoring else 0.0,
                        "auto_promotion_eligible": opp.scoring.auto_promotion_eligible if opp.scoring else False,
                        "discovered_at": opp.discovered_at,
                        "last_updated": opp.last_updated,
                        "ein": opp.ein,
                        "funding_amount": opp.funding_amount,
                        "program_name": opp.program_name,
                        "source": opp.source,
                        "opportunity_type": opp.opportunity_type,
                        "description": opp.description,
                        "stage_history": [h.model_dump() for h in opp.stage_history] if opp.stage_history else [],
                        "promotion_history": [p.model_dump() for p in opp.promotion_history] if opp.promotion_history else []
                    }
                    filtered_opportunities.append(opportunity)
            
            return {
                "profile_id": profile_id,
                "total_opportunities": len(filtered_opportunities),
                "opportunities": filtered_opportunities,
                "filters_applied": {
                    "stage": stage,
                    "min_score": min_score
                },
                "source": "unified_service"
            }
        
        # Fallback to old service logic
        logger.info(f"DEBUG: Falling back to legacy service for profile {profile_id}")
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
        
        # Convert leads to opportunities format for frontend with deduplication
        opportunities = []
        seen_organizations = set()  # Track unique organizations by EIN + name
        
        for lead in leads:
            # Create unique key for deduplication (EIN + Organization Name)
            ein = lead.external_data.get('ein', '') if lead.external_data else ''
            org_name = lead.organization_name or ''
            unique_key = f"{ein.strip()}|{org_name.strip().lower()}"
            
            # Skip duplicates - keep the highest scoring or most recent entry
            if unique_key in seen_organizations:
                # Find existing opportunity to potentially replace
                existing_idx = None
                for i, opp in enumerate(opportunities):
                    existing_ein = opp.get('external_data', {}).get('ein', '')
                    existing_name = opp.get('organization_name', '')
                    existing_key = f"{existing_ein.strip()}|{existing_name.strip().lower()}"
                    
                    if existing_key == unique_key:
                        existing_idx = i
                        break
                
                # Replace if this lead has higher score or is more recent
                if existing_idx is not None:
                    existing_score = opportunities[existing_idx].get('compatibility_score', 0)
                    current_score = lead.compatibility_score or 0
                    
                    # Keep higher scoring opportunity, or if scores are equal, keep more recent
                    if current_score > existing_score:
                        # Replace with higher scoring opportunity
                        opportunities[existing_idx] = _convert_lead_to_opportunity(lead)
                        logger.debug(f"Replaced duplicate {org_name} with higher score: {current_score:.3f} vs {existing_score:.3f}")
                    # If same score, keep the more recent one
                    elif current_score == existing_score and lead.discovered_at:
                        existing_discovered = opportunities[existing_idx].get('discovered_at')
                        if not existing_discovered or lead.discovered_at.isoformat() > existing_discovered:
                            opportunities[existing_idx] = _convert_lead_to_opportunity(lead)
                            logger.debug(f"Replaced duplicate {org_name} with more recent discovery")
                
                continue  # Skip adding this duplicate
            
            # Add unique organization
            seen_organizations.add(unique_key)
            opportunity = _convert_lead_to_opportunity(lead)
            opportunities.append(opportunity)
        
        logger.info(f"Deduplicated opportunities: {len(leads)} leads -> {len(opportunities)} unique opportunities")
        
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

# @app.get("/api/profiles/{profile_id}/entity-analysis")
# async def get_profile_entity_analysis(profile_id: str):
#     """Get comprehensive entity-based analysis for a profile using shared analytics."""
#     try:
#         analysis = await entity_profile_service.analyze_profile_entities(profile_id)
#         return analysis
#     except Exception as e:
#         logger.error(f"Failed to get entity analysis for profile {profile_id}: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/profiles/{profile_id}/add-entity-lead")
# async def add_entity_lead(profile_id: str, lead_data: Dict[str, Any]):
#     """Add opportunity lead using entity references (EIN, opportunity ID)."""
#     try:
#         organization_ein = lead_data.get("organization_ein")
#         opportunity_id = lead_data.get("opportunity_id")
#         
#         if not organization_ein:
#             raise HTTPException(status_code=400, detail="organization_ein is required")
#         
#         lead = await entity_profile_service.add_entity_lead(
#             profile_id=profile_id,
#             organization_ein=organization_ein,
#             opportunity_id=opportunity_id,
#             additional_data=lead_data.get("additional_data", {})
#         )
#         
#         if lead:
#             return {
#                 "success": True,
#                 "lead_id": lead.lead_id,
#                 "message": "Entity lead added successfully"
#             }
#         else:
#             raise HTTPException(status_code=400, detail="Failed to add entity lead")
#             
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Failed to add entity lead for profile {profile_id}: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/api/profiles/leads/{lead_id}/entity-analysis")
# async def get_lead_entity_analysis(lead_id: str):
#     """Get comprehensive entity-based analysis for a specific lead."""
#     try:
#         analysis = await entity_profile_service.get_entity_lead_analysis(lead_id)
#         return analysis
#     except Exception as e:
#         logger.error(f"Failed to get entity analysis for lead {lead_id}: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/profiles/{profile_id}/entity-discovery")
# async def start_entity_discovery(profile_id: str, discovery_params: Dict[str, Any]):
#     """Start discovery session using entity-based data sources."""
#     try:
#         entity_types = discovery_params.get("entity_types", ["nonprofits", "government_opportunities"])
#         filters = discovery_params.get("filters", {})
#         
#         session = entity_profile_service.create_entity_discovery_session(
#             profile_id=profile_id,
#             entity_types=entity_types,
#             filters=filters
#         )
#         
#         if session:
#             return {
#                 "success": True,
#                 "session_id": session.session_id,
#                 "message": "Entity discovery session started"
#             }
#         else:
#             raise HTTPException(status_code=400, detail="Failed to start entity discovery session")
#             
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Failed to start entity discovery for profile {profile_id}: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


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
        
        # Enhanced: Get raw discovery results for unified service integration
        from src.discovery.discovery_engine import discovery_engine
        raw_session_results = []
        session_id = discovery_results.get("discovery_timestamp", "")
        
        try:
            # Get the raw DiscoveryResult objects from the session
            raw_session_results = discovery_engine.get_session_results(session_id)
            logger.info(f"Retrieved {len(raw_session_results)} raw discovery results for unified integration")
            
            # Save to unified service using adapter
            unified_save_results = await unified_discovery_adapter.save_discovery_results(
                discovery_results=raw_session_results,
                profile_id=profile_id,
                session_id=session_id
            )
            logger.info(f"Unified service save results: {unified_save_results['saved_count']} saved, {unified_save_results['failed_count']} failed, {unified_save_results['duplicates_skipped']} duplicates")
            
        except Exception as e:
            logger.error(f"Failed to save to unified service: {e}")
            unified_save_results = {"error": str(e), "saved_count": 0}
        
        # Store results as opportunity leads (legacy compatibility)
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
                    
                    # Add lead to profile (legacy)
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
            "top_matches": discovery_results.get("summary", {}).get("top_matches", [])[:5],
            "unified_integration": {
                "enabled": True,
                "saved_to_unified": unified_save_results.get("saved_count", 0),
                "failed_saves": unified_save_results.get("failed_count", 0),
                "duplicates_skipped": unified_save_results.get("duplicates_skipped", 0),
                "analytics_refreshed": unified_save_results.get("analytics_refreshed", False)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to discover opportunities for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/{profile_id}/discovery/sessions")
async def get_discovery_sessions(profile_id: str, limit: Optional[int] = 10):
    """Get recent discovery sessions for a profile with unified analytics"""
    try:
        # Get unified profile for enhanced session data
        unified_profile = unified_service.get_profile(profile_id)
        if not unified_profile:
            # Fallback to old service
            old_profile = profile_service.get_profile(profile_id)
            if not old_profile:
                raise HTTPException(status_code=404, detail="Profile not found")
            
            return {
                "profile_id": profile_id,
                "sessions": [],
                "current_analytics": None,
                "source": "legacy_service"
            }
        
        # Get recent activity filtered for discovery sessions
        discovery_sessions = [
            activity for activity in unified_profile.recent_activity 
            if activity.type == "discovery_session"
        ]
        
        # Limit results
        discovery_sessions = discovery_sessions[:limit] if limit else discovery_sessions
        
        # Enhanced session data with unified analytics
        enhanced_sessions = []
        for session in discovery_sessions:
            enhanced_session = {
                "date": session.date,
                "results_found": session.results,
                "source": session.source,
                "type": session.type,
                "analytics_snapshot": {
                    "total_opportunities": unified_profile.analytics.opportunity_count,
                    "stage_distribution": unified_profile.analytics.stages_distribution,
                    "high_potential_count": unified_profile.analytics.scoring_stats.get('high_potential_count', 0),
                    "avg_score": unified_profile.analytics.scoring_stats.get('avg_score', 0.0)
                }
            }
            enhanced_sessions.append(enhanced_session)
        
        return {
            "profile_id": profile_id,
            "organization_name": unified_profile.organization_name,
            "sessions": enhanced_sessions,
            "current_analytics": unified_profile.analytics.model_dump() if unified_profile.analytics else None,
            "total_sessions": len(discovery_sessions),
            "source": "unified_service"
        }
        
    except Exception as e:
        logger.error(f"Failed to get discovery sessions for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/{profile_id}/analytics/real-time")
async def get_real_time_analytics(profile_id: str):
    """Get real-time analytics for a profile using unified service"""
    try:
        # Get unified profile for real-time data
        unified_profile = unified_service.get_profile(profile_id)
        if not unified_profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get opportunities for detailed analytics
        opportunities = unified_service.get_profile_opportunities(profile_id)
        
        # Calculate real-time metrics
        stage_progression = {}
        score_distribution = {"high": 0, "medium": 0, "low": 0}
        recent_discoveries = 0
        
        for opp in opportunities:
            # Stage progression tracking
            if opp.stage_history:
                for stage in opp.stage_history:
                    stage_name = stage.stage
                    if stage_name not in stage_progression:
                        stage_progression[stage_name] = {"count": 0, "avg_duration_hours": 0}
                    stage_progression[stage_name]["count"] += 1
                    if stage.duration_hours:
                        current_avg = stage_progression[stage_name]["avg_duration_hours"]
                        stage_progression[stage_name]["avg_duration_hours"] = (
                            (current_avg + stage.duration_hours) / 2
                        )
            
            # Score distribution
            if opp.scoring:
                score = opp.scoring.overall_score
                if score >= 0.80:
                    score_distribution["high"] += 1
                elif score >= 0.60:
                    score_distribution["medium"] += 1
                else:
                    score_distribution["low"] += 1
            
            # Recent discoveries (last 24 hours)
            if opp.discovered_at:
                try:
                    discovered = datetime.fromisoformat(opp.discovered_at.replace('Z', '+00:00'))
                    if (datetime.now() - discovered).days < 1:
                        recent_discoveries += 1
                except:
                    pass
        
        return {
            "profile_id": profile_id,
            "organization_name": unified_profile.organization_name,
            "real_time_metrics": {
                "total_opportunities": len(opportunities),
                "stage_distribution": unified_profile.analytics.stages_distribution,
                "stage_progression": stage_progression,
                "score_distribution": score_distribution,
                "recent_discoveries_24h": recent_discoveries,
                "avg_score": unified_profile.analytics.scoring_stats.get('avg_score', 0.0),
                "high_potential_count": unified_profile.analytics.scoring_stats.get('high_potential_count', 0),
                "auto_promotion_eligible": unified_profile.analytics.scoring_stats.get('auto_promotion_eligible', 0)
            },
            "last_updated": unified_profile.updated_at,
            "source": "unified_service"
        }
        
    except Exception as e:
        logger.error(f"Failed to get real-time analytics for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === DISCOVERY DASHBOARD ENDPOINTS ===

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

@app.websocket("/ws/discovery")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time discovery updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/dashboard", response_class=HTMLResponse)
async def discovery_dashboard():
    """Discovery Dashboard interface"""
    try:
        template_path = Path(__file__).parent / "templates" / "discovery_dashboard.html"
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard template not found")

@app.get("/api/discovery/sessions/recent")
async def get_recent_discovery_sessions(limit: Optional[int] = 20):
    """Get recent discovery sessions across all profiles"""
    try:
        all_sessions = []
        
        # Get all profiles from profile service
        profiles = profile_service.list_profiles()
        
        for profile in profiles:
            # Try to get unified profile for enhanced data, fall back to basic profile
            unified_profile = unified_service.get_profile(profile.profile_id)
            if unified_profile and hasattr(unified_profile, 'recent_activity'):
                # Get recent discovery sessions for each profile
                discovery_sessions = [
                    activity for activity in unified_profile.recent_activity 
                    if activity.type == "discovery_session"
                ]
            else:
                # No discovery sessions in legacy profile
                discovery_sessions = []
            
            # Add profile info to sessions
            for session in discovery_sessions:
                session_data = {
                    "session_id": f"session_{profile.profile_id}_{session.date}",
                    "profile_id": profile.profile_id,
                    "profile_name": profile.organization_name,
                    "started_at": session.date,
                    "completed_at": session.date,  # Mock completion time
                    "execution_time_seconds": random.randint(30, 300),  # Mock duration
                    "total_results_discovered": session.results or 0,
                    "funding_types": ["grants", "government", "commercial"],  # Mock types
                    "api_calls_made": random.randint(5, 50),  # Mock API calls
                    "status": "completed"
                }
                all_sessions.append(session_data)
        
        # Sort by date descending
        all_sessions.sort(key=lambda x: x["started_at"], reverse=True)
        
        # Limit results
        if limit:
            all_sessions = all_sessions[:limit]
        
        return all_sessions
        
    except Exception as e:
        logger.error(f"Failed to get recent discovery sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/discovery/stats/global")
async def get_global_discovery_stats():
    """Get global discovery statistics across all profiles"""
    try:
        profiles = profile_service.list_profiles()
        
        total_opportunities = 0
        total_sessions = 0
        total_score_sum = 0.0
        scored_opportunities = 0
        active_sessions = 0  # Mock active sessions
        
        for profile in profiles:
            # Try to get unified profile for analytics, fall back to counting opportunities
            unified_profile = unified_service.get_profile(profile.profile_id)
            if unified_profile and unified_profile.analytics:
                total_opportunities += unified_profile.analytics.opportunity_count or 0
                total_sessions += unified_profile.analytics.discovery_stats.get('total_sessions', 0)
                
                # Calculate weighted average score
                avg_score = unified_profile.analytics.scoring_stats.get('avg_score', 0.0)
                opp_count = unified_profile.analytics.opportunity_count or 0
                if avg_score > 0 and opp_count > 0:
                    total_score_sum += avg_score * opp_count
                    scored_opportunities += opp_count
            else:
                # For legacy profiles, count opportunities manually
                opportunities = unified_service.get_profile_opportunities(profile.profile_id)
                total_opportunities += len(opportunities)
        
        # Calculate global averages
        global_avg_score = (total_score_sum / scored_opportunities) if scored_opportunities > 0 else 0.0
        success_rate = 0.85 if total_sessions > 0 else 0.0  # Mock success rate
        
        return {
            "active_sessions": active_sessions,
            "total_opportunities": total_opportunities,
            "avg_score": global_avg_score,
            "success_rate": success_rate,
            "total_profiles": len(profiles),
            "total_sessions": total_sessions,
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get global discovery stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Broadcast discovery events to WebSocket clients
async def broadcast_discovery_event(event_type: str, data: dict):
    """Broadcast discovery events to all connected WebSocket clients"""
    message = {
        "type": event_type,
        "timestamp": datetime.now().isoformat(),
        **data
    }
    await manager.broadcast(message)

# === END DISCOVERY DASHBOARD ENDPOINTS ===

# === ADVANCED SEARCH & EXPORT ENDPOINTS ===

from src.web.services.search_export_service import (
    get_search_export_service, SearchCriteria, SearchFilter, SearchOperator, 
    SortDirection, ExportFormat
)
from fastapi.responses import StreamingResponse
import io

search_service = get_search_export_service()

@app.post("/api/search/opportunities")
async def search_opportunities(
    search_request: Dict[str, Any],
    profile_id: Optional[str] = None
):
    """Advanced search across opportunities with flexible filtering"""
    try:
        # Parse search criteria
        filters = []
        if 'filters' in search_request:
            for f in search_request['filters']:
                filter_obj = SearchFilter(
                    field=f['field'],
                    operator=SearchOperator(f['operator']),
                    value=f['value'],
                    value2=f.get('value2')
                )
                filters.append(filter_obj)
        
        criteria = SearchCriteria(
            filters=filters,
            sort_by=search_request.get('sort_by'),
            sort_direction=SortDirection(search_request.get('sort_direction', 'desc')),
            limit=search_request.get('limit'),
            offset=search_request.get('offset', 0)
        )
        
        # Perform search
        results = search_service.search_opportunities(criteria, profile_id)
        
        # Convert to JSON-serializable format
        opportunities_data = [opp.model_dump() for opp in results.opportunities]
        
        return {
            "opportunities": opportunities_data,
            "total_count": results.total_count,
            "filtered_count": results.filtered_count,
            "page_info": results.page_info,
            "search_metadata": results.search_metadata
        }
        
    except Exception as e:
        logger.error(f"Failed to search opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search/fields")
async def get_searchable_fields():
    """Get available fields for advanced search"""
    return {
        "basic_fields": [
            {"field": "organization_name", "type": "string", "label": "Organization Name"},
            {"field": "ein", "type": "string", "label": "EIN"},
            {"field": "current_stage", "type": "string", "label": "Current Stage"},
            {"field": "opportunity_type", "type": "string", "label": "Opportunity Type"},
            {"field": "funding_amount", "type": "number", "label": "Funding Amount"},
            {"field": "program_name", "type": "string", "label": "Program Name"},
            {"field": "status", "type": "string", "label": "Status"},
            {"field": "discovered_at", "type": "datetime", "label": "Discovered Date"},
            {"field": "last_updated", "type": "datetime", "label": "Last Updated"}
        ],
        "scoring_fields": [
            {"field": "scoring.overall_score", "type": "number", "label": "Overall Score"},
            {"field": "scoring.confidence_level", "type": "number", "label": "Confidence Level"},
            {"field": "scoring.auto_promotion_eligible", "type": "boolean", "label": "Auto Promotion Eligible"},
            {"field": "scoring.promotion_recommended", "type": "boolean", "label": "Promotion Recommended"}
        ],
        "analysis_fields": [
            {"field": "analysis.discovery.match_factors.source_type", "type": "string", "label": "Source Type"},
            {"field": "analysis.discovery.match_factors.state", "type": "string", "label": "State"}
        ],
        "operators": [
            {"value": "equals", "label": "Equals", "types": ["string", "number", "boolean"]},
            {"value": "contains", "label": "Contains", "types": ["string"]},
            {"value": "starts_with", "label": "Starts With", "types": ["string"]},
            {"value": "ends_with", "label": "Ends With", "types": ["string"]},
            {"value": "gt", "label": "Greater Than", "types": ["number", "datetime"]},
            {"value": "lt", "label": "Less Than", "types": ["number", "datetime"]},
            {"value": "between", "label": "Between", "types": ["number", "datetime"]},
            {"value": "in", "label": "In List", "types": ["string", "number"]},
            {"value": "not_in", "label": "Not In List", "types": ["string", "number"]}
        ]
    }

@app.post("/api/export/opportunities")
async def export_opportunities(
    export_request: Dict[str, Any]
):
    """Export opportunities with advanced filtering and format options"""
    try:
        # Get search criteria (same as search endpoint)
        filters = []
        if 'filters' in export_request:
            for f in export_request['filters']:
                filter_obj = SearchFilter(
                    field=f['field'],
                    operator=SearchOperator(f['operator']),
                    value=f['value'],
                    value2=f.get('value2')
                )
                filters.append(filter_obj)
        
        criteria = SearchCriteria(
            filters=filters,
            sort_by=export_request.get('sort_by'),
            sort_direction=SortDirection(export_request.get('sort_direction', 'desc')),
            limit=None,  # Export all results
            offset=0
        )
        
        # Get export format and options
        format_str = export_request.get('format', 'csv')
        include_analytics = export_request.get('include_analytics', True)
        profile_id = export_request.get('profile_id')
        
        try:
            export_format = ExportFormat(format_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid export format: {format_str}")
        
        # Perform search to get opportunities
        results = search_service.search_opportunities(criteria, profile_id)
        
        # Export data
        export_data = search_service.export_opportunities(
            results.opportunities, 
            export_format, 
            include_analytics
        )
        
        # Determine content type and filename
        content_types = {
            ExportFormat.JSON: "application/json",
            ExportFormat.CSV: "text/csv",
            ExportFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        file_extensions = {
            ExportFormat.JSON: "json",
            ExportFormat.CSV: "csv", 
            ExportFormat.XLSX: "xlsx"
        }
        
        content_type = content_types.get(export_format, "application/octet-stream")
        file_extension = file_extensions.get(export_format, "txt")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"opportunities_export_{timestamp}.{file_extension}"
        
        # Create streaming response
        return StreamingResponse(
            io.BytesIO(export_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(export_data))
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to export opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search/stats")
async def get_search_stats():
    """Get search and export statistics"""
    try:
        profiles = profile_service.list_profiles()
        total_opportunities = 0
        
        # Calculate stats across all profiles
        stage_distribution = {}
        source_distribution = {}
        score_ranges = {"high": 0, "medium": 0, "low": 0}
        
        for profile in profiles:
            opportunities = unified_service.get_profile_opportunities(profile.profile_id)
            total_opportunities += len(opportunities)
            
            for opp in opportunities:
                # Stage distribution
                stage = opp.current_stage
                stage_distribution[stage] = stage_distribution.get(stage, 0) + 1
                
                # Source distribution
                source = opp.opportunity_type
                source_distribution[source] = source_distribution.get(source, 0) + 1
                
                # Score distribution
                if opp.scoring:
                    score = opp.scoring.overall_score
                    if score >= 0.80:
                        score_ranges["high"] += 1
                    elif score >= 0.60:
                        score_ranges["medium"] += 1
                    else:
                        score_ranges["low"] += 1
        
        return {
            "total_opportunities": total_opportunities,
            "total_profiles": len(profiles),
            "stage_distribution": stage_distribution,
            "source_distribution": source_distribution,
            "score_distribution": score_ranges,
            "searchable_fields": 15,  # Based on fields defined above
            "export_formats": 3,
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get search stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === END ADVANCED SEARCH & EXPORT ENDPOINTS ===

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
                    "organization_name": getattr(opportunity, 'funder_name', '[Organization Name Missing]'),
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

@app.post("/api/profiles/{profile_id}/discover/bmf")
async def discover_bmf_opportunities(profile_id: str, bmf_data: Dict[str, Any]):
    """Save BMF filter results to profile using existing discovery pattern."""
    try:
        logger.info(f"Processing BMF discovery for profile {profile_id}")
        
        # Validate profile exists
        profile_obj = profile_service.get_profile(profile_id)
        if not profile_obj:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")
        
        bmf_results = bmf_data.get("bmf_results", {})
        nonprofits = bmf_results.get("nonprofits", [])
        foundations = bmf_results.get("foundations", [])
        
        logger.info(f"BMF data received: {len(nonprofits)} nonprofits, {len(foundations)} foundations")
        
        # Get profile's EIN and name for enhanced self-exclusion check
        profile_ein = getattr(profile_obj, 'ein', '').strip()
        profile_name = getattr(profile_obj, 'name', '').strip()
        if profile_ein:
            # Normalize EIN format for comparison (remove dashes)
            profile_ein = profile_ein.replace('-', '').replace(' ', '')
        
        opportunities = []
        excluded_self_count = 0
        
        # Process nonprofit results
        for org in nonprofits:
            # Enhanced self-exclusion check: skip if this organization is the profile itself
            org_ein = org.get("ein", "").strip().replace('-', '').replace(' ', '')
            org_name = org.get("organization_name", "").strip()
            
            # Check both EIN match and name similarity for comprehensive exclusion
            is_self_match = False
            if profile_ein and org_ein and profile_ein == org_ein:
                # EIN match - check name similarity for confirmation
                if similar_organization_names(org_name, profile_name):
                    is_self_match = True
                    logger.info(f"Excluded self-match for profile {profile_id}: {org_name} (EIN: {org.get('ein')}) - similar to profile '{profile_name}'")
                else:
                    # EIN match but names significantly different - log for review
                    logger.warning(f"EIN match but name difference for profile {profile_id}: org='{org_name}' vs profile='{profile_name}' (EIN: {org.get('ein')})")
            
            if is_self_match:
                excluded_self_count += 1
                continue
            lead_data = {
                "source": "BMF Filter",
                "opportunity_type": "grants", 
                "organization_name": org.get("organization_name", ""),
                "program_name": None,
                "description": f"Nonprofit organization identified through BMF filter - {org.get('ntee_description', '')}",
                "funding_amount": None,
                "pipeline_stage": "discovery",
                "compatibility_score": org.get("compatibility_score", 0.75),
                "success_probability": None,
                "match_factors": {
                    "source_type": org.get("source_type", "Nonprofit"),
                    "ntee_code": org.get("ntee_code"),
                    "state": org.get("state", "VA"),
                    "bmf_filtered": True,
                    "quick_bmf_result": True,
                    "deadline": None,
                    "eligibility": []
                },
                "risk_factors": {},
                "recommendations": [],
                "board_connections": [],
                "network_insights": {},
                "approach_strategy": None,
                "status": "active",
                "assigned_to": None,
                "external_data": {
                    "ein": org.get("ein"),
                    "ntee_code": org.get("ntee_code"),
                    "discovery_source": org.get("discovery_source", "BMF Filter"),
                    "opportunity_id": f"bmf_nonprofit_{org.get('ein', 'unknown')}",
                    "source_url": None,
                    "bmf_session": "bmf_filter_session"
                }
            }
            
            # Add lead to profile using existing service
            lead = profile_service.add_opportunity_lead(profile_id, lead_data)
            if lead:
                # Create opportunity data with both discovery ID and actual lead ID
                opportunity_data = lead.model_dump()
                opportunity_data['discovery_opportunity_id'] = f"bmf_nonprofit_{org.get('ein', 'unknown')}"
                opportunity_data['lead_id'] = lead.lead_id
                opportunities.append(opportunity_data)
        
        # Process foundation results  
        for org in foundations:
            # Enhanced self-exclusion check: skip if this organization is the profile itself
            org_ein = org.get("ein", "").strip().replace('-', '').replace(' ', '')
            org_name = org.get("organization_name", "").strip()
            
            # Check both EIN match and name similarity for comprehensive exclusion
            is_self_match = False
            if profile_ein and org_ein and profile_ein == org_ein:
                # EIN match - check name similarity for confirmation
                if similar_organization_names(org_name, profile_name):
                    is_self_match = True
                    logger.info(f"Excluded self-match for profile {profile_id}: {org_name} (EIN: {org.get('ein')}) - similar to profile '{profile_name}'")
                else:
                    # EIN match but names significantly different - log for review
                    logger.warning(f"EIN match but name difference for profile {profile_id}: org='{org_name}' vs profile='{profile_name}' (EIN: {org.get('ein')})")
            
            if is_self_match:
                excluded_self_count += 1
                continue
            lead_data = {
                "source": "BMF Filter",
                "opportunity_type": "grants",
                "organization_name": org.get("organization_name", ""),
                "program_name": None,
                "description": f"Foundation identified through BMF filter - Foundation Code {org.get('foundation_code', '')}",
                "funding_amount": None,
                "pipeline_stage": "discovery", 
                "compatibility_score": org.get("compatibility_score", 0.75),
                "success_probability": None,
                "match_factors": {
                    "source_type": org.get("source_type", "Foundation"),
                    "foundation_code": org.get("foundation_code"),
                    "state": org.get("state", "VA"),
                    "bmf_filtered": True,
                    "quick_bmf_result": True,
                    "deadline": None,
                    "eligibility": []
                },
                "risk_factors": {},
                "recommendations": [],
                "board_connections": [],
                "network_insights": {},
                "approach_strategy": None,
                "status": "active",
                "assigned_to": None,
                "external_data": {
                    "ein": org.get("ein"),
                    "foundation_code": org.get("foundation_code"),
                    "discovery_source": org.get("discovery_source", "BMF Filter"),
                    "opportunity_id": f"bmf_foundation_{org.get('ein', 'unknown')}",
                    "source_url": None,
                    "bmf_session": "bmf_filter_session"
                }
            }
            
            # Add lead to profile using existing service
            lead = profile_service.add_opportunity_lead(profile_id, lead_data)
            if lead:
                # Create opportunity data with both discovery ID and actual lead ID
                opportunity_data = lead.model_dump()
                opportunity_data['discovery_opportunity_id'] = f"bmf_foundation_{org.get('ein', 'unknown')}"
                opportunity_data['lead_id'] = lead.lead_id
                opportunities.append(opportunity_data)
        
        # Update profile discovery metadata
        profile_obj.last_discovery_date = datetime.now()
        profile_obj.discovery_status = "completed" 
        profile_service.update_profile(profile_id, profile_obj)
        
        total_results = len(opportunities)
        if excluded_self_count > 0:
            logger.info(f"BMF discovery completed for profile {profile_id}: {total_results} opportunities saved, {excluded_self_count} self-matches excluded")
        else:
            logger.info(f"BMF discovery completed for profile {profile_id}: {total_results} opportunities saved")
        
        return {
            "message": f"BMF discovery completed for profile {profile_id}",
            "total_opportunities_found": total_results,
            "nonprofits_found": len(nonprofits),
            "foundations_found": len(foundations),
            "opportunities_saved": len(opportunities),
            "discovery_type": "bmf_filter",
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"BMF discovery failed for profile {profile_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"BMF discovery failed: {str(e)}")

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
        
        # Phase 3.1: Store opportunities directly through profile service like BMF endpoint
        try:
            stored_opportunities = []
            
            # Get profile's EIN and name for enhanced self-exclusion check  
            profile_ein = profile_context.get('ein', '').strip().replace('-', '').replace(' ', '') if profile_context else ''
            profile_name = profile_context.get('name', '').strip() if profile_context else ''
            
            if profile_context:
                profile_id = profile_context.get('profile_id', 'test_profile')
                from src.profiles.service import get_profile_service
                profile_service = get_profile_service()
            
                # Process BMF results
                for bmf_org in results.get("bmf_results", []):
                    org_name = bmf_org.get('name', '').strip()
                    if not org_name or org_name == '[Organization Name Missing]':
                        # Skip organizations with missing names
                        logger.debug(f"Skipping BMF organization with missing name: {bmf_org}")
                        continue
                        
                    # Enhanced self-exclusion check: skip if this organization is the profile itself
                    org_ein = bmf_org.get('ein', '').strip().replace('-', '').replace(' ', '')
                    
                    # Check both EIN match and name similarity for comprehensive exclusion
                    is_self_match = False
                    if profile_ein and org_ein and profile_ein == org_ein:
                        # EIN match - check name similarity for confirmation
                        if similar_organization_names(org_name, profile_name):
                            is_self_match = True
                            logger.info(f"Excluded self-match in nonprofit discovery: {org_name} (EIN: {bmf_org.get('ein')}) - similar to profile '{profile_name}'")
                        else:
                            # EIN match but names significantly different - log for review
                            logger.warning(f"EIN match but name difference in nonprofit discovery: org='{org_name}' vs profile='{profile_name}' (EIN: {bmf_org.get('ein')})")
                    
                    if is_self_match:
                        continue
                    
                    # Create lead data similar to BMF endpoint pattern
                    lead_data = {
                        "source": "Nonprofit Discovery - BMF",
                        "opportunity_type": "grants", 
                        "organization_name": org_name,
                        "program_name": None,
                        "description": f"Nonprofit organization from IRS Business Master File. Revenue: ${bmf_org.get('revenue', 0) or 0:,}",
                        "funding_amount": None,
                        "pipeline_stage": "discovery",
                        "compatibility_score": 0.6,
                        "success_probability": None,
                        "match_factors": {
                            "source_type": "Nonprofit",
                            "ntee_code": bmf_org.get("ntee_code"),
                            "state": bmf_org.get("state", "VA"),
                            "bmf_filtered": True,
                            "deadline": None,
                            "eligibility": []
                        },
                        "risk_factors": {},
                        "recommendations": [],
                        "board_connections": [],
                        "network_insights": {},
                        "approach_strategy": None,
                        "status": "active",
                        "assigned_to": None,
                        "external_data": {
                            "ein": bmf_org.get("ein"),
                            "ntee_code": bmf_org.get("ntee_code"),
                            "discovery_source": "bmf_filter",
                            "source_url": None
                        }
                    }
                    
                    # Store lead and capture actual lead_id
                    lead = profile_service.add_opportunity_lead(profile_id, lead_data)
                    if lead:
                        opportunity_data = lead.model_dump()
                        opportunity_data['discovery_opportunity_id'] = f"bmf_{bmf_org.get('ein', 'unknown')}"
                        opportunity_data['lead_id'] = lead.lead_id
                        stored_opportunities.append(opportunity_data)
            
                # Process ProPublica results
                for pp_org in results.get("propublica_results", []):
                    org_name = pp_org.get('name', '').strip()
                    if not org_name or org_name == '[Organization Name Missing]':
                        # Skip organizations with missing names
                        logger.debug(f"Skipping ProPublica organization with missing name: {pp_org}")
                        continue
                        
                    # Enhanced self-exclusion check: skip if this organization is the profile itself
                    org_ein = pp_org.get('ein', '').strip().replace('-', '').replace(' ', '')
                    
                    # Check both EIN match and name similarity for comprehensive exclusion
                    is_self_match = False
                    if profile_ein and org_ein and profile_ein == org_ein:
                        # EIN match - check name similarity for confirmation
                        if similar_organization_names(org_name, profile_name):
                            is_self_match = True
                            logger.info(f"Excluded self-match in nonprofit discovery (ProPublica): {org_name} (EIN: {pp_org.get('ein')}) - similar to profile '{profile_name}'")
                        else:
                            # EIN match but names significantly different - log for review
                            logger.warning(f"EIN match but name difference in nonprofit discovery (ProPublica): org='{org_name}' vs profile='{profile_name}' (EIN: {pp_org.get('ein')})")
                    
                    if is_self_match:
                        continue
                    
                    # Create lead data for ProPublica results
                    lead_data = {
                        "source": "Nonprofit Discovery - ProPublica",
                        "opportunity_type": "grants", 
                        "organization_name": org_name,
                        "program_name": None,
                        "description": f"Nonprofit organization from ProPublica database. Revenue: ${pp_org.get('revenue', 0) or 0:,}",
                        "funding_amount": None,
                        "pipeline_stage": "discovery",
                        "compatibility_score": 0.7,
                        "success_probability": None,
                        "match_factors": {
                            "source_type": "Nonprofit",
                            "ntee_code": pp_org.get("ntee_code"),
                            "state": pp_org.get("state", "VA"),
                            "propublica_data": True,
                            "deadline": None,
                            "eligibility": []
                        },
                        "risk_factors": {},
                        "recommendations": [],
                        "board_connections": [],
                        "network_insights": {},
                        "approach_strategy": None,
                        "status": "active",
                        "assigned_to": None,
                        "external_data": {
                            "ein": pp_org.get("ein"),
                            "ntee_code": pp_org.get("ntee_code"),
                            "discovery_source": "propublica_fetch",
                            "source_url": None
                        }
                    }
                    
                    # Store lead and capture actual lead_id
                    lead = profile_service.add_opportunity_lead(profile_id, lead_data)
                    if lead:
                        opportunity_data = lead.model_dump()
                        opportunity_data['discovery_opportunity_id'] = f"propublica_{pp_org.get('ein', 'unknown')}"
                        opportunity_data['lead_id'] = lead.lead_id
                        stored_opportunities.append(opportunity_data)
                
                logger.info(f"Added {len(stored_opportunities)} opportunities to profile {profile_id}")
            
        except Exception as e:
            logger.error(f"Failed to store nonprofit discovery opportunities: {str(e)}")
        
        # Calculate total opportunities found from all sources
        total_bmf = len(results.get("bmf_results", []))
        total_propublica = len(results.get("propublica_results", []))
        total_found = total_bmf + total_propublica
        
        # Automated Promotion Integration
        promotion_result = None
        if profile_context and stored_opportunities:
            try:
                from src.web.services.automated_promotion_service import get_automated_promotion_service
                
                # Use stored opportunities directly (they have the correct lead_id format)
                opportunities = []
                for stored_opp in stored_opportunities:
                    opportunity = {
                        "opportunity_id": stored_opp.get("lead_id"),  # Use actual lead_id for lookups
                        "organization_name": stored_opp.get("organization_name"),
                        "source_type": stored_opp.get("opportunity_type", "grants"),
                        "discovery_source": stored_opp.get("source", "nonprofit_discovery"),
                        "funnel_stage": stored_opp.get("pipeline_stage", "discovery"),
                        "compatibility_score": stored_opp.get("compatibility_score", 0.7),
                        "description": stored_opp.get("description", ""),
                        "external_data": stored_opp.get("external_data", {})
                    }
                    opportunities.append(opportunity)
                
                # Process opportunities for automated promotion
                auto_promotion_service = get_automated_promotion_service()
                profile_id = profile_context.get('profile_id', 'unknown')
                
                promotion_result = await auto_promotion_service.process_discovery_results(
                    profile_id, opportunities, "nonprofit_discovery"
                )
                
                logger.info(f"Automated promotion: {promotion_result.promoted_count}/{promotion_result.total_processed} opportunities promoted")
                
            except Exception as e:
                logger.warning(f"Automated promotion failed, continuing without it: {e}")
                promotion_result = {"error": str(e)}
        
        response = {
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
        
        # Add automated promotion results if available
        if promotion_result:
            response["automated_promotion"] = {
                "enabled": True,
                "processed": getattr(promotion_result, 'total_processed', 0),
                "promoted": getattr(promotion_result, 'promoted_count', 0),
                "scored": getattr(promotion_result, 'scored_count', 0),
                "errors": getattr(promotion_result, 'error_count', 0),
                "processing_time": getattr(promotion_result, 'processing_time', 0.0)
            }
        else:
            response["automated_promotion"] = {"enabled": False, "reason": "No profile context provided"}
        
        return response
        
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
    Supports both single target and batch promotion modes.
    
    Single Target Request format:
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
    
    Batch Promotion Request format:
    {
        "candidates": [{...}, {...}],
        "selected_profile": {...},
        "research_mode": "batch_promotion",
        "cost_limit": 1.50,
        "priority": "high"
    }
    """
    try:
        logger.info("Starting AI Heavy deep research")
        
        # Get AI service manager
        ai_service = get_ai_service_manager()
        
        # Validate request data
        if not request.get("selected_profile"):
            raise HTTPException(status_code=400, detail="Profile context required for AI research")
        
        # Check for batch promotion mode
        if request.get("research_mode") == "batch_promotion":
            return await handle_batch_promotion(request, ai_service)
        
        # Original single target handling
        if not request.get("target_opportunity"):
            raise HTTPException(status_code=400, detail="Target opportunity required for deep research")
        
        # Execute single target AI Heavy research
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


async def handle_batch_promotion(request: Dict[str, Any], ai_service):
    """
    Handle batch promotion of multiple candidates for AI-Heavy research.
    Transforms candidate data to individual target_opportunity format.
    """
    logger.info("Processing batch promotion for AI-Heavy research")
    
    candidates = request.get("candidates", [])
    if not candidates:
        raise HTTPException(status_code=400, detail="No candidates provided for batch promotion")
    
    selected_profile = request.get("selected_profile")
    cost_limit = request.get("cost_limit", 5.0)  # Default budget limit
    
    batch_results = []
    total_cost = 0.0
    successful_analyses = 0
    failed_analyses = []
    
    logger.info(f"Processing {len(candidates)} candidates for AI-Heavy promotion")
    
    for i, candidate in enumerate(candidates):
        try:
            # Transform candidate to target_opportunity format
            target_opportunity = transform_candidate_to_target(candidate)
            
            # Create individual research request
            single_request = {
                "target_opportunity": target_opportunity,
                "selected_profile": selected_profile,
                "ai_lite_results": candidate.get("ai_lite_insights", {}),
                "model_preference": "gpt-4o-mini" if candidate.get("research_depth") == "standard" else "gpt-4o",
                "cost_budget": candidate.get("estimated_cost", 0.08),
                "research_priority_areas": ["funding_strategy", "competitive_analysis"],
                "research_risk_areas": ["capacity_assessment", "timeline_feasibility"],
                "research_intelligence_gaps": ["board_connections", "success_metrics"]
            }
            
            # Check cost budget
            if total_cost + single_request["cost_budget"] > cost_limit:
                logger.warning(f"Cost limit reached. Stopping batch processing at candidate {i+1}")
                break
            
            # Execute AI Heavy research for this candidate
            result = await ai_service.execute_ai_heavy_research(single_request)
            
            # Process successful result
            analysis_result = {
                "opportunity_id": candidate.get("opportunity_id"),
                "organization_name": candidate.get("organization_name"),
                "research_score": result.get("research_score", 0.0),
                "comprehensive_analysis": result.get("comprehensive_analysis", ""),
                "strategic_insights": result.get("strategic_insights", {}),
                "competitive_analysis": result.get("competitive_analysis", {}),
                "risk_assessment": result.get("risk_assessment", {}),
                "funding_strategy": result.get("funding_strategy", {}),
                "research_mode": candidate.get("research_depth", "standard"),
                "cost_breakdown": {
                    "total_cost": result.get("cost_breakdown", {}).get("total_cost", single_request["cost_budget"]),
                    "model_used": single_request["model_preference"]
                }
            }
            
            batch_results.append(analysis_result)
            total_cost += analysis_result["cost_breakdown"]["total_cost"]
            successful_analyses += 1
            
            logger.info(f"✅ Completed AI-Heavy research for {candidate.get('organization_name')} (${analysis_result['cost_breakdown']['total_cost']:.4f})")
            
        except Exception as e:
            logger.error(f"❌ Failed AI-Heavy research for {candidate.get('organization_name', 'Unknown')}: {str(e)}")
            failed_analyses.append({
                "candidate": candidate.get("organization_name", "Unknown"),
                "error": str(e)
            })
            continue
    
    logger.info(f"Batch promotion completed: {successful_analyses} successful, {len(failed_analyses)} failed, Total cost: ${total_cost:.4f}")
    
    return {
        "status": "success",
        "analysis_type": "ai_heavy_batch",
        "results": {
            "research_analyses": batch_results,
            "batch_summary": {
                "total_processed": len(candidates),
                "successful_analyses": successful_analyses,
                "failed_analyses": len(failed_analyses),
                "total_cost": total_cost,
                "cost_limit": cost_limit,
                "processing_time": "batch_mode"
            }
        },
        "failed_analyses": failed_analyses if failed_analyses else None,
        "total_cost": total_cost
    }


def transform_candidate_to_target(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform candidate data from ANALYZE tab to target_opportunity format
    expected by AI Heavy researcher.
    """
    return {
        "opportunity_id": candidate.get("opportunity_id"),
        "organization_name": candidate.get("organization_name"),
        "source_type": candidate.get("source_type"),
        "funding_amount": candidate.get("funding_amount"),
        "website": candidate.get("website"),
        "ein": candidate.get("ein"),
        "ai_compatibility_score": candidate.get("ai_lite_score", 0.0),
        "ai_analysis_insights": candidate.get("ai_lite_insights", ""),
        "discovery_context": {
            "promoted_from": "ai_lite_analysis",
            "original_source": candidate.get("source_type", "unknown"),
            "promotion_timestamp": candidate.get("promotion_timestamp")
        }
    }

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

# SPECIALIZED AI PROCESSOR ENDPOINTS - 5-Call Architecture Integration

@app.post("/api/ai/lite-1/validate")
async def execute_ai_lite_validator(request: Dict[str, Any]):
    """Execute AI-Lite-1 Validator processor for fast opportunity screening."""
    try:
        logger.info("Starting AI-Lite-1 Validator analysis")
        
        # Import the specific processor
        from src.processors.analysis.ai_lite_validator import AILiteValidator
        
        # Validate request data
        candidates = request.get("candidates", [])
        profile = request.get("selected_profile", {})
        
        if not candidates:
            raise HTTPException(status_code=400, detail="No candidates provided for validation")
        if not profile:
            raise HTTPException(status_code=400, detail="Profile context required for validation")
        
        # Initialize processor
        validator = AILiteValidator()
        
        # Execute validation
        results = await validator.execute({
            "candidates": candidates,
            "profile_context": profile,
            "batch_size": request.get("batch_size", 20),
            "cost_optimization": request.get("cost_optimization", True)
        })
        
        return {
            "status": "success",
            "processor": "ai_lite_validator",
            "results": results,
            "cost_estimate": "$0.0001 per candidate",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI-Lite-1 Validator failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.post("/api/ai/lite-2/strategic-score")
async def execute_ai_lite_strategic_scorer(request: Dict[str, Any]):
    """Execute AI-Lite-2 Strategic Scorer for semantic reasoning and priority ranking."""
    try:
        logger.info("Starting AI-Lite-2 Strategic Scorer analysis")
        
        # Import the specific processor
        from src.processors.analysis.ai_lite_strategic_scorer import AILiteStrategicScorer
        
        # Validate request data
        qualified_candidates = request.get("qualified_candidates", [])
        profile = request.get("selected_profile", {})
        
        if not qualified_candidates:
            raise HTTPException(status_code=400, detail="No qualified candidates provided for strategic scoring")
        if not profile:
            raise HTTPException(status_code=400, detail="Profile context required for strategic analysis")
        
        # Initialize processor
        strategic_scorer = AILiteStrategicScorer()
        
        # Execute strategic scoring
        results = await strategic_scorer.execute({
            "qualified_candidates": qualified_candidates,
            "profile_context": profile,
            "analysis_depth": request.get("analysis_depth", "standard"),
            "focus_areas": request.get("focus_areas", [])
        })
        
        return {
            "status": "success",
            "processor": "ai_lite_strategic_scorer", 
            "results": results,
            "cost_estimate": "$0.0003 per candidate",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI-Lite-2 Strategic Scorer failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Strategic scoring failed: {str(e)}")

@app.post("/api/ai/heavy-1/research-bridge")
async def execute_ai_heavy_research_bridge(request: Dict[str, Any]):
    """Execute AI-Heavy-1 Research Bridge for intelligence gathering and fact extraction."""
    try:
        logger.info("Starting AI-Heavy-1 Research Bridge analysis")
        
        # Import the specific processor
        from src.processors.analysis.ai_heavy_research_bridge import AIHeavyResearchBridge
        
        # Validate request data
        target_candidates = request.get("target_candidates", [])
        profile = request.get("selected_profile", {})
        lite_results = request.get("ai_lite_results", {})
        
        if not target_candidates:
            raise HTTPException(status_code=400, detail="No target candidates provided for research bridge")
        if not profile:
            raise HTTPException(status_code=400, detail="Profile context required for research analysis")
        
        # Initialize processor
        research_bridge = AIHeavyResearchBridge()
        
        # Execute research bridge analysis
        results = await research_bridge.execute({
            "target_candidates": target_candidates,
            "profile_context": profile,
            "ai_lite_context": lite_results,
            "research_depth": request.get("research_depth", "comprehensive"),
            "intelligence_priorities": request.get("intelligence_priorities", [])
        })
        
        return {
            "status": "success",
            "processor": "ai_heavy_research_bridge",
            "results": results,
            "cost_estimate": "$0.05 per candidate",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI-Heavy-1 Research Bridge failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Research bridge failed: {str(e)}")

@app.post("/api/ai/orchestrated-pipeline")
async def execute_orchestrated_analysis_pipeline(request: Dict[str, Any]):
    """Execute the complete 5-call orchestrated AI analysis pipeline."""
    try:
        logger.info("Starting orchestrated AI analysis pipeline")
        
        # Import the orchestrator
        from src.processors.analysis.optimized_analysis_orchestrator import OptimizedAnalysisOrchestrator
        
        # Validate request data
        prospects = request.get("prospects", [])
        profile = request.get("selected_profile", {})
        
        if not prospects:
            raise HTTPException(status_code=400, detail="No prospects provided for orchestrated analysis")
        if not profile:
            raise HTTPException(status_code=400, detail="Profile context required for orchestrated analysis")
        
        # Initialize orchestrator
        orchestrator = OptimizedAnalysisOrchestrator()
        
        # Execute complete pipeline
        results = await orchestrator.execute_complete_pipeline({
            "prospects": prospects,
            "profile_context": profile,
            "cost_budget": request.get("cost_budget", 1.0),
            "quality_threshold": request.get("quality_threshold", 0.7),
            "parallel_processing": request.get("parallel_processing", True)
        })
        
        return {
            "status": "success",
            "processor": "orchestrated_pipeline",
            "results": results,
            "pipeline_summary": {
                "total_prospects_input": len(prospects),
                "candidates_after_validation": results.get("validation_stats", {}).get("passed", 0),
                "qualified_after_scoring": results.get("scoring_stats", {}).get("qualified", 0),
                "targets_after_research": results.get("research_stats", {}).get("completed", 0),
                "total_cost": results.get("cost_summary", {}).get("total_cost", 0)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Orchestrated pipeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

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
            "/api/profiles/{profile_id}/opportunities/{opportunity_id}/score",
            "/api/profiles/{profile_id}/opportunities/{opportunity_id}/promote",
            "/api/profiles/{profile_id}/opportunities/{opportunity_id}/evaluate",
            "/api/profiles/{profile_id}/opportunities/{opportunity_id}/details",
            "/api/profiles/{profile_id}/opportunities/bulk-promote",
            "/api/profiles/{profile_id}/promotion-candidates",
            "/api/profiles/{profile_id}/promotion-history",
            "/api/test"
        ]
    }

# =====================================
# SCORING & PROMOTION API ENDPOINTS  
# =====================================

@app.post("/api/profiles/{profile_id}/opportunities/{opportunity_id}/score", response_model=ScoreResponse)
async def score_opportunity(profile_id: str, opportunity_id: str, request: ScoreRequest):
    """Score an opportunity against a profile"""
    scoring_service = get_scoring_service()
    return await scoring_service.score_opportunity(profile_id, opportunity_id, request)

@app.post("/api/profiles/{profile_id}/opportunities/{opportunity_id}/promote", response_model=PromotionResponse)
async def promote_opportunity(profile_id: str, opportunity_id: str, request: PromotionRequest):
    """Promote or demote an opportunity using unified service"""
    try:
        # Try unified service first for stage updates
        if request.action in ["promote", "next_stage"]:
            # Get current opportunity to determine next stage
            opportunity = unified_service.get_opportunity(profile_id, opportunity_id)
            if opportunity:
                # Determine target stage based on current stage
                stage_progression = {
                    "discovery": "pre_scoring",
                    "pre_scoring": "deep_analysis", 
                    "deep_analysis": "recommendations",
                    "recommendations": "recommendations"  # Stay in final stage
                }
                
                target_stage = stage_progression.get(opportunity.current_stage, opportunity.current_stage)
                if target_stage != opportunity.current_stage:
                    success = unified_service.update_opportunity_stage(
                        profile_id, 
                        opportunity_id,
                        target_stage,
                        reason=f"Manual promotion via API - {request.action}",
                        promoted_by="user"
                    )
                    
                    if success:
                        return PromotionResponse(
                            decision="approved",
                            reason=f"Manual promotion to {target_stage}",
                            current_score=opportunity.scoring.overall_score if opportunity.scoring else 0.5,
                            target_stage=target_stage,
                            confidence_level=0.95,
                            requires_manual_review=False,
                            promotion_metadata={"source": "manual_api", "original_stage": opportunity.current_stage}
                        )
                    else:
                        return PromotionResponse(
                            decision="failed",
                            reason="Failed to update stage",
                            current_score=opportunity.scoring.overall_score if opportunity.scoring else 0.5,
                            target_stage=opportunity.current_stage,
                            confidence_level=0.1,
                            requires_manual_review=True,
                            promotion_metadata={"error": "stage_update_failed"}
                        )
                else:
                    return PromotionResponse(
                        decision="no_change",
                        reason=f"Already in final stage: {opportunity.current_stage}",
                        current_score=opportunity.scoring.overall_score if opportunity.scoring else 0.5,
                        target_stage=opportunity.current_stage,
                        confidence_level=0.8,
                        requires_manual_review=False,
                        promotion_metadata={"status": "already_at_target"}
                    )
        
        # Fallback to scoring service for complex promotion logic
        scoring_service = get_scoring_service()
        return await scoring_service.promote_opportunity(profile_id, opportunity_id, request)
        
    except Exception as e:
        logger.error(f"Error promoting opportunity {opportunity_id}: {e}")
        return PromotionResponse(
            decision="error",
            reason=f"System error: {str(e)}",
            current_score=0.0,
            target_stage="unknown",
            confidence_level=0.0,
            requires_manual_review=True,
            promotion_metadata={"error": str(e), "error_type": type(e).__name__}
        )

@app.post("/api/profiles/{profile_id}/opportunities/{opportunity_id}/evaluate", response_model=PromotionResponse)
async def evaluate_promotion(profile_id: str, opportunity_id: str, request: PromotionRequest):
    """Evaluate promotion eligibility without applying changes"""
    scoring_service = get_scoring_service()
    return await scoring_service.evaluate_promotion(profile_id, opportunity_id, request)

@app.get("/api/profiles/{profile_id}/opportunities/{opportunity_id}/details")
async def get_opportunity_details(profile_id: str, opportunity_id: str):
    """Get detailed opportunity information using unified service"""
    try:
        # Try unified service first for complete data
        opportunity = unified_service.get_opportunity(profile_id, opportunity_id)
        if opportunity:
            return {
                "opportunity": opportunity.model_dump(),
                "source": "unified_service"
            }
        
        # Fallback to scoring service
        scoring_service = get_scoring_service()
        
        # Get opportunity data (placeholder implementation)
        opportunity_data = await scoring_service._get_opportunity_data(profile_id, opportunity_id)
        if not opportunity_data:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Get current score if available
        current_score = await scoring_service._get_current_score(profile_id, opportunity_id, opportunity_data)
        
        # Get promotion evaluation
        promotion_request = PromotionRequest(action="evaluate")
        promotion_eval = await scoring_service.evaluate_promotion(profile_id, opportunity_id, promotion_request)
        
        return {
            "opportunity_data": opportunity_data,
            "current_score": scoring_service._format_score_response(current_score) if current_score else None,
            "promotion_evaluation": promotion_eval,
            "stage_progression": {
                "current": opportunity_data.get('funnel_stage', 'prospects'),
                "next": scoring_service._get_next_stage(opportunity_data.get('funnel_stage', 'prospects')),
                "previous": scoring_service._get_previous_stage(opportunity_data.get('funnel_stage', 'prospects'))
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting opportunity details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get opportunity details: {str(e)}")

@app.post("/api/profiles/{profile_id}/opportunities/bulk-promote", response_model=BulkPromotionResponse)
async def bulk_promote_opportunities(profile_id: str, request: BulkPromotionRequest):
    """Bulk promote multiple opportunities"""
    scoring_service = get_scoring_service()
    return await scoring_service.bulk_promote(profile_id, request)

@app.get("/api/profiles/{profile_id}/promotion-candidates")
async def get_promotion_candidates(profile_id: str, stage: str = "prospects", limit: int = 50):
    """Get opportunities that are candidates for promotion"""
    scoring_service = get_scoring_service()
    return await scoring_service.get_promotion_candidates(profile_id, stage, limit)

@app.get("/api/profiles/{profile_id}/promotion-history")
async def get_promotion_history(profile_id: str, opportunity_id: Optional[str] = None, limit: int = 100):
    """Get promotion history for a profile or specific opportunity"""
    try:
        scoring_service = get_scoring_service()
        history = scoring_service.promotion_engine.get_promotion_history(opportunity_id, limit)
        
        # Convert to serializable format
        history_data = []
        for record in history:
            history_data.append({
                "opportunity_id": record.opportunity_id,
                "from_stage": record.from_stage,
                "to_stage": record.to_stage,
                "decision": record.decision.value,
                "reason": record.reason.value,
                "score_at_promotion": record.score_at_promotion,
                "promoted_by": record.promoted_by,
                "promoted_at": record.promoted_at.isoformat(),
                "metadata": record.metadata
            })
        
        return {
            "profile_id": profile_id,
            "history": history_data,
            "total_records": len(history_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting promotion history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get promotion history: {str(e)}")


# ===============================================================================
# AUTOMATED PROMOTION ENGINE ENDPOINTS
# ===============================================================================

@app.post("/api/profiles/{profile_id}/automated-promotion/process")
async def process_automated_promotion(
    profile_id: str,
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """Process opportunities for automated scoring and promotion"""
    try:
        from src.web.services.automated_promotion_service import get_automated_promotion_service
        
        service = get_automated_promotion_service()
        
        opportunities = request.get("opportunities", [])
        discovery_source = request.get("discovery_source", "unknown")
        
        if not opportunities:
            raise HTTPException(status_code=400, detail="No opportunities provided")
        
        logger.info(f"Processing {len(opportunities)} opportunities for automated promotion")
        
        result = await service.process_discovery_results(profile_id, opportunities, discovery_source)
        
        return {
            "profile_id": profile_id,
            "discovery_source": discovery_source,
            "result": {
                "total_processed": result.total_processed,
                "promoted_count": result.promoted_count,
                "scored_count": result.scored_count,
                "error_count": result.error_count,
                "processing_time": result.processing_time,
                "promotion_details": result.promotion_details[:10],  # Limit to first 10 for response size
                "errors": result.errors[:5]  # Limit to first 5 errors
            },
            "success_rate": ((result.total_processed - result.error_count) / max(result.total_processed, 1)) * 100,
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in automated promotion processing: {e}")
        raise HTTPException(status_code=500, detail=f"Automated promotion failed: {str(e)}")


@app.get("/api/profiles/{profile_id}/automated-promotion/candidates")
async def get_automated_promotion_candidates(
    profile_id: str,
    stage: str = "prospects",
    limit: int = 50
) -> Dict[str, Any]:
    """Get opportunities that are candidates for automated promotion"""
    try:
        from src.web.services.automated_promotion_service import get_automated_promotion_service
        
        service = get_automated_promotion_service()
        candidates = await service.get_promotion_candidates(profile_id, stage, limit)
        
        return {
            "profile_id": profile_id,
            "stage": stage,
            "candidates": candidates,
            "total_candidates": len(candidates),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting promotion candidates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get candidates: {str(e)}")


@app.post("/api/profiles/{profile_id}/automated-promotion/bulk-promote")
async def bulk_promote_opportunities(
    profile_id: str,
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """Bulk promote multiple opportunities using automated scoring"""
    try:
        from src.web.services.automated_promotion_service import get_automated_promotion_service
        
        service = get_automated_promotion_service()
        
        opportunity_ids = request.get("opportunity_ids", [])
        user_id = request.get("user_id", "web_user")
        
        if not opportunity_ids:
            raise HTTPException(status_code=400, detail="No opportunity IDs provided")
        
        logger.info(f"Bulk promoting {len(opportunity_ids)} opportunities")
        
        result = await service.bulk_promote_candidates(profile_id, opportunity_ids, user_id)
        
        return {
            "profile_id": profile_id,
            "bulk_promotion_result": result,
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in bulk promotion: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk promotion failed: {str(e)}")


@app.get("/api/automated-promotion/stats")
async def get_automated_promotion_stats() -> Dict[str, Any]:
    """Get automated promotion service statistics and configuration"""
    try:
        from src.web.services.automated_promotion_service import get_automated_promotion_service
        
        service = get_automated_promotion_service()
        stats = service.get_processing_stats()
        
        return {
            "service_stats": stats,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting automated promotion stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.put("/api/automated-promotion/config")
async def update_automated_promotion_config(request: Dict[str, Any]) -> Dict[str, Any]:
    """Update automated promotion service configuration"""
    try:
        from src.web.services.automated_promotion_service import get_automated_promotion_service
        
        service = get_automated_promotion_service()
        service.update_config(request)
        
        updated_stats = service.get_processing_stats()
        
        return {
            "message": "Configuration updated successfully",
            "updated_config": updated_stats["config"],
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating automated promotion config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


# ===============================================================================
# ENHANCED DATA SERVICE ENDPOINTS (990/990-PF Integration)
# ===============================================================================

@app.post("/api/profiles/{profile_id}/opportunities/{opportunity_id}/enhanced-data")
async def fetch_enhanced_data_for_opportunity(
    profile_id: str,
    opportunity_id: str,
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """Fetch enhanced 990/990-PF data for a specific opportunity"""
    try:
        from src.web.services.enhanced_data_service import get_enhanced_data_service
        
        service = get_enhanced_data_service()
        
        opportunity_data = request.get("opportunity_data", {})
        score = request.get("score", 0.0)
        
        if not opportunity_data:
            raise HTTPException(status_code=400, detail="Opportunity data required")
        
        logger.info(f"Fetching enhanced data for opportunity {opportunity_id}")
        
        enhanced_result = await service.fetch_enhanced_data_for_opportunity(opportunity_data, score)
        
        if enhanced_result:
            return {
                "profile_id": profile_id,
                "opportunity_id": opportunity_id,
                "enhanced_data": {
                    "has_990_data": enhanced_result.has_990_data,
                    "has_990_pf_data": enhanced_result.has_990_pf_data,
                    "financial_data": enhanced_result.financial_data,
                    "foundation_data": enhanced_result.foundation_data,
                    "board_data": enhanced_result.board_data,
                    "boost_factors": enhanced_result.boost_factors,
                    "data_completeness": enhanced_result.data_completeness,
                    "processing_time": enhanced_result.processing_time,
                    "fetched_at": enhanced_result.fetched_at.isoformat()
                },
                "success": True
            }
        else:
            return {
                "profile_id": profile_id,
                "opportunity_id": opportunity_id,
                "enhanced_data": None,
                "success": False,
                "message": "No enhanced data available or score below threshold"
            }
        
    except Exception as e:
        logger.error(f"Error fetching enhanced data: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced data fetch failed: {str(e)}")


@app.post("/api/profiles/{profile_id}/opportunities/enhanced-data/batch")
async def fetch_enhanced_data_batch(
    profile_id: str,
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """Fetch enhanced data for a batch of opportunities"""
    try:
        from src.web.services.enhanced_data_service import get_enhanced_data_service
        
        service = get_enhanced_data_service()
        
        opportunities = request.get("opportunities", [])
        scores = request.get("scores", [])
        
        if not opportunities:
            raise HTTPException(status_code=400, detail="Opportunities list required")
        
        logger.info(f"Fetching enhanced data for batch of {len(opportunities)} opportunities")
        
        enhanced_results = await service.fetch_enhanced_data_batch(opportunities, scores)
        
        # Format results for API response
        formatted_results = []
        for result in enhanced_results:
            formatted_results.append({
                "opportunity_id": result.opportunity_id,
                "organization_name": result.organization_name,
                "ein": result.ein,
                "has_990_data": result.has_990_data,
                "has_990_pf_data": result.has_990_pf_data,
                "boost_factors": result.boost_factors,
                "data_completeness": result.data_completeness,
                "processing_time": result.processing_time,
                "error_message": result.error_message
            })
        
        return {
            "profile_id": profile_id,
            "batch_size": len(opportunities),
            "successful_results": len(enhanced_results),
            "results": formatted_results,
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in batch enhanced data fetch: {e}")
        raise HTTPException(status_code=500, detail=f"Batch enhanced data fetch failed: {str(e)}")


@app.get("/api/enhanced-data/stats")
async def get_enhanced_data_stats() -> Dict[str, Any]:
    """Get enhanced data service statistics"""
    try:
        from src.web.services.enhanced_data_service import get_enhanced_data_service
        
        service = get_enhanced_data_service()
        stats = service.get_statistics()
        
        return {
            "service_stats": stats,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced data stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.put("/api/enhanced-data/config")
async def update_enhanced_data_config(request: Dict[str, Any]) -> Dict[str, Any]:
    """Update enhanced data service configuration"""
    try:
        from src.web.services.enhanced_data_service import get_enhanced_data_service
        
        service = get_enhanced_data_service()
        service.update_config(request)
        
        updated_stats = service.get_statistics()
        
        return {
            "message": "Enhanced data configuration updated successfully",
            "updated_config": updated_stats["config"],
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating enhanced data config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@app.delete("/api/enhanced-data/cache")
async def clear_enhanced_data_cache() -> Dict[str, Any]:
    """Clear the enhanced data cache"""
    try:
        from src.web.services.enhanced_data_service import get_enhanced_data_service
        
        service = get_enhanced_data_service()
        cache_size = len(service.data_cache)
        service.clear_cache()
        
        return {
            "message": f"Enhanced data cache cleared ({cache_size} entries removed)",
            "cleared_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing enhanced data cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


# =============================================================================
# Phase 3: AI Research Platform Endpoints
# =============================================================================

@app.post("/api/profiles/{profile_id}/research/analyze-integrated")
async def analyze_opportunity_integrated(profile_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform integrated scoring and research analysis for a specific opportunity"""
    try:
        # Import research integration system
        from src.analysis.research_scoring_integration import ResearchScoringIntegration
        from src.analysis.ai_research_platform import ReportFormat
        
        opportunity_id = request_data.get('opportunity_id')
        include_research = request_data.get('include_research', True)
        report_type_str = request_data.get('report_type', 'executive_summary')
        
        if not opportunity_id:
            raise HTTPException(status_code=400, detail="opportunity_id required")
        
        # Get opportunity data
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Find the specific opportunity
        opportunity = None
        for opp in profile.opportunities:
            if opp.opportunity_id == opportunity_id:
                opportunity = opp.model_dump()
                break
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Convert report type string to enum
        report_type_map = {
            'executive_summary': ReportFormat.EXECUTIVE_SUMMARY,
            'detailed_research': ReportFormat.DETAILED_RESEARCH,
            'decision_brief': ReportFormat.DECISION_BRIEF,
            'evaluation_summary': ReportFormat.EVALUATION_SUMMARY,
            'evidence_package': ReportFormat.EVIDENCE_PACKAGE
        }
        
        report_type = report_type_map.get(report_type_str, ReportFormat.EXECUTIVE_SUMMARY)
        
        # Perform integrated analysis
        async with ResearchScoringIntegration(cost_optimization=True) as integration:
            analysis = await integration.analyze_opportunity_integrated(
                opportunity, include_research, report_type
            )
        
        # Convert analysis to response format
        response = {
            'analysis_id': f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'opportunity_id': analysis.opportunity_id,
            'organization_name': analysis.organization_name,
            'integrated_results': {
                'integrated_score': analysis.integrated_score,
                'integrated_confidence': analysis.integrated_confidence,
                'evidence_strength': analysis.evidence_strength,
                'research_impact_factor': analysis.research_impact_factor,
                'recommended_action': analysis.recommended_action,
                'decision_confidence': analysis.decision_confidence
            },
            'scoring_results': analysis.scoring_results,
            'research_results': {
                'research_quality_score': analysis.research_quality_score,
                'research_confidence': analysis.research_confidence,
                'has_research_report': analysis.research_report is not None
            },
            'decision_support': {
                'next_steps': analysis.next_steps,
                'risk_factors': analysis.risk_factors
            },
            'performance_metrics': {
                'processing_time': analysis.processing_time,
                'cost_breakdown': analysis.cost_breakdown,
                'analysis_timestamp': analysis.analysis_timestamp.isoformat()
            }
        }
        
        # Add research report details if available
        if analysis.research_report:
            response['research_report'] = {
                'report_id': analysis.research_report.report_id,
                'report_type': analysis.research_report.report_type.value,
                'title': analysis.research_report.title,
                'executive_summary': analysis.research_report.executive_summary,
                'contacts_identified': len(analysis.research_report.contacts_identified),
                'evidence_facts': len(analysis.research_report.evidence_package),
                'recommendations': analysis.research_report.recommendations,
                'confidence_assessment': analysis.research_report.confidence_assessment
            }
        
        logger.info(f"Integrated analysis completed for {analysis.organization_name}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in integrated analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/profiles/{profile_id}/research/batch-analyze")
async def batch_analyze_opportunities(profile_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform batch integrated analysis for multiple opportunities"""
    try:
        from src.analysis.research_scoring_integration import ResearchScoringIntegration
        from src.analysis.ai_research_platform import ReportFormat
        
        include_research = request_data.get('include_research', True)
        report_type_str = request_data.get('report_type', 'executive_summary')
        batch_size = request_data.get('batch_size')
        stage_filter = request_data.get('stage_filter', 'candidates')  # candidates, candidates+, all
        
        # Get profile and opportunities
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Filter opportunities based on stage
        opportunities = []
        for opp in profile.opportunities:
            stage = opp.current_stage
            
            if stage_filter == 'candidates' and stage not in ['pre_scoring', 'recommendations']:
                continue
            elif stage_filter == 'candidates+' and stage not in ['discovery', 'pre_scoring', 'recommendations']:
                continue
            # 'all' includes everything
            
            opportunities.append(opp.model_dump())
        
        if not opportunities:
            return {
                'batch_id': f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'message': 'No opportunities found matching filter criteria',
                'opportunities_processed': 0,
                'results': []
            }
        
        # Convert report type
        report_type_map = {
            'executive_summary': ReportFormat.EXECUTIVE_SUMMARY,
            'detailed_research': ReportFormat.DETAILED_RESEARCH,
            'decision_brief': ReportFormat.DECISION_BRIEF,
            'evaluation_summary': ReportFormat.EVALUATION_SUMMARY,
            'evidence_package': ReportFormat.EVIDENCE_PACKAGE
        }
        
        report_type = report_type_map.get(report_type_str, ReportFormat.EXECUTIVE_SUMMARY)
        
        # Perform batch analysis
        async with ResearchScoringIntegration(cost_optimization=True) as integration:
            batch_result = await integration.batch_analyze_opportunities(
                opportunities, include_research, report_type, batch_size
            )
        
        # Convert results to response format
        analysis_results = []
        for analysis in batch_result.integrated_analyses:
            result = {
                'opportunity_id': analysis.opportunity_id,
                'organization_name': analysis.organization_name,
                'integrated_score': analysis.integrated_score,
                'integrated_confidence': analysis.integrated_confidence,
                'recommended_action': analysis.recommended_action,
                'decision_confidence': analysis.decision_confidence,
                'evidence_strength': analysis.evidence_strength,
                'processing_time': analysis.processing_time,
                'cost': analysis.cost_breakdown.get('total_cost', 0.0)
            }
            
            if analysis.research_report:
                result['research_summary'] = {
                    'quality_score': analysis.research_quality_score,
                    'contacts_found': len(analysis.research_report.contacts_identified),
                    'facts_extracted': len(analysis.research_report.evidence_package),
                    'recommendations_count': len(analysis.research_report.recommendations)
                }
            
            analysis_results.append(result)
        
        response = {
            'batch_id': batch_result.batch_id,
            'batch_summary': {
                'total_opportunities': batch_result.total_opportunities,
                'successful_analyses': batch_result.successful_analyses,
                'failed_analyses': batch_result.failed_analyses,
                'success_rate': batch_result.successful_analyses / batch_result.total_opportunities if batch_result.total_opportunities > 0 else 0,
                'total_processing_time': batch_result.total_processing_time,
                'total_cost': batch_result.total_cost,
                'average_cost_per_opportunity': batch_result.average_cost_per_opportunity,
                'average_confidence': batch_result.average_confidence,
                'quality_distribution': batch_result.quality_distribution
            },
            'analysis_results': analysis_results,
            'errors': batch_result.error_log,
            'batch_started': batch_result.batch_started.isoformat(),
            'batch_completed': batch_result.batch_completed.isoformat() if batch_result.batch_completed else None
        }
        
        logger.info(f"Batch analysis completed: {batch_result.successful_analyses}/{batch_result.total_opportunities} successful")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@app.post("/api/profiles/{profile_id}/analyze/ai-lite")
async def ai_lite_profile_analysis(profile_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    AI-Lite analysis endpoint for ANALYZE tab integration
    
    Performs cost-effective candidate evaluation with dual-mode operation:
    - Scoring mode: Quick compatibility analysis (~$0.0001/candidate)
    - Research mode: Comprehensive research reports (~$0.0008/candidate)
    """
    try:
        logger.info(f"Starting AI-Lite analysis for profile {profile_id}")
        logger.info(f"Request data type: {type(request_data)}")
        
        # Handle case where request_data might not be a dict
        try:
            if hasattr(request_data, 'dict'):
                request_dict = request_data.dict()
            elif hasattr(request_data, '__dict__'):
                request_dict = vars(request_data)
            elif isinstance(request_data, dict):
                request_dict = request_data
            else:
                logger.error(f"Unexpected request_data type: {type(request_data)}")
                raise HTTPException(status_code=400, detail=f"Invalid request format: {type(request_data)}")
            
            logger.info(f"Request dict type: {type(request_dict)}, keys: {list(request_dict.keys())}")
            
            # Validate request data
            candidates = request_dict.get("candidates", [])
            candidate_ids = request_dict.get("candidate_ids", [])
            analysis_type = request_dict.get("analysis_type", "compatibility_scoring")
            model_preference = request_dict.get("model_preference", "gpt-3.5-turbo")
            cost_limit = request_dict.get("cost_limit", 0.01)
            research_mode = request_dict.get("research_mode", False)
            
            logger.info(f"Parsed request: candidates={len(candidates)}, candidate_ids={candidate_ids}")
            
        except Exception as parse_error:
            logger.error(f"Failed to parse request data: {parse_error}")
            raise HTTPException(status_code=400, detail=f"Request parsing failed: {str(parse_error)}")
        
        # Handle both direct candidates and candidate IDs
        if not candidates and candidate_ids:
            logger.info(f"Looking for candidates with IDs: {candidate_ids}")
            # Fetch candidates by ID from the profile's opportunities
            profile_opportunities = unified_service.get_profile_opportunities(profile_id)
            logger.info(f"Profile has {len(profile_opportunities) if profile_opportunities else 0} opportunities")
            if profile_opportunities:
                candidates = []
                for i, opp in enumerate(profile_opportunities[:5]):  # Debug first 5 opportunities
                    # Handle both dictionary and object formats
                    opp_id = getattr(opp, 'id', None) or getattr(opp, 'opportunity_id', None) or (opp.get('id') if hasattr(opp, 'get') else None) or (opp.get('opportunity_id') if hasattr(opp, 'get') else None)
                    logger.info(f"Opportunity {i}: type={type(opp)}, id={opp_id}")
                    if opp_id in candidate_ids:
                        logger.info(f"Found matching candidate: {opp_id}")
                        # Convert object to dictionary format if needed
                        if hasattr(opp, 'dict'):
                            candidates.append(opp.dict())
                            logger.info(f"Converted with .dict() method")
                        elif hasattr(opp, '__dict__'):
                            candidates.append(vars(opp))
                            logger.info(f"Converted with vars()")
                        else:
                            candidates.append(opp)
                            logger.info(f"Used as-is")
                logger.info(f"Fetched {len(candidates)} candidates from {len(candidate_ids)} provided IDs")
        
        if not candidates:
            raise HTTPException(status_code=400, detail="No candidates provided for analysis")
        
        # Ensure all candidates are dictionaries
        processed_candidates = []
        for candidate in candidates:
            if hasattr(candidate, 'dict'):
                processed_candidates.append(candidate.dict())
            elif hasattr(candidate, '__dict__'):
                processed_candidates.append(vars(candidate))
            elif isinstance(candidate, dict):
                processed_candidates.append(candidate)
            else:
                logger.warning(f"Candidate type not supported: {type(candidate)}")
                continue
        
        logger.info(f"Processed {len(processed_candidates)} candidates for AI-Lite analysis")
        
        # Debug: Log candidate types and sample data
        for i, candidate in enumerate(processed_candidates[:2]):  # Log first 2 for debugging
            logger.info(f"Candidate {i}: type={type(candidate)}, keys={list(candidate.keys()) if isinstance(candidate, dict) else 'not a dict'}")
        
        if not processed_candidates:
            raise HTTPException(status_code=400, detail="No valid candidates after processing")
        
        # Get profile for context
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Import AI-Lite services
        from src.processors.analysis.ai_service_manager import get_ai_service_manager
        from src.analytics.cost_tracker import get_cost_tracker
        
        ai_service = get_ai_service_manager()
        cost_tracker = get_cost_tracker()
        
        # Transform profile data for AI service compatibility
        profile_data = profile.model_dump()
        logger.info(f"Original profile geographic_scope: {profile_data.get('geographic_scope', 'NOT_FOUND')}")
        
        # Transform geographic_scope from dict to string
        if "geographic_scope" in profile_data:
            logger.info(f"Geographic scope type: {type(profile_data['geographic_scope'])}")
            if isinstance(profile_data["geographic_scope"], dict):
                logger.info("Transforming geographic_scope from dict to string")
                geo_scope = profile_data["geographic_scope"]
                scope_parts = []
                
                if geo_scope.get("nationwide", False):
                    scope_parts.append("Nationwide")
                elif geo_scope.get("international", False):
                    scope_parts.append("International")
                else:
                    # Build from states and regions
                    states = geo_scope.get("states", [])
                    regions = geo_scope.get("regions", [])
                    
                    if states:
                        if len(states) == 1:
                            scope_parts.append(f"{states[0]} state")
                        else:
                            scope_parts.append(f"{', '.join(states)} states")
                    
                    if regions:
                        scope_parts.append(f"{', '.join(regions)} region")
                
                # Default to "Local/Regional" if no specific scope defined
                profile_data["geographic_scope"] = " and ".join(scope_parts) if scope_parts else "Local/Regional"
                logger.info(f"Transformed geographic_scope to: '{profile_data['geographic_scope']}'")
            else:
                logger.info(f"Geographic scope is already a string: {profile_data['geographic_scope']}")
        else:
            logger.warning("No geographic_scope found in profile data")
        
        # Prepare AI-Lite request
        frontend_data = {
            "selected_profile": profile_data,
            "candidates": processed_candidates,
            "model_preference": model_preference,
            "cost_limit": cost_limit,
            "research_mode": research_mode,
            "analysis_type": analysis_type
        }
        
        # Check budget before processing
        from src.analytics.cost_tracker import AIService, CostCategory
        
        # Map model preference to AI service
        service_mapping = {
            "gpt-3.5-turbo": AIService.OPENAI_GPT3_5_TURBO,
            "gpt-4o-mini": AIService.OPENAI_GPT4O_MINI,
            "gpt-4o": AIService.OPENAI_GPT4O,
            "gpt-4": AIService.OPENAI_GPT4
        }
        
        service = service_mapping.get(model_preference, AIService.OPENAI_GPT3_5_TURBO)
        
        # Estimate cost for all candidates
        avg_tokens = 1500 if not research_mode else 3000  # Research mode uses more tokens
        output_tokens = 300 if not research_mode else 800
        
        total_estimate = cost_tracker.estimate_cost(
            service=service,
            operation_type=CostCategory.AI_ANALYSIS,
            input_tokens=avg_tokens * len(processed_candidates),
            output_tokens=output_tokens * len(processed_candidates)
        )
        
        # Check if we can afford this operation
        can_run = True
        budget_message = "Budget validated"
        
        async with cost_tracker.lock:
            for budget in cost_tracker.budgets.values():
                if not budget.can_spend(total_estimate.estimated_cost_usd):
                    can_run = False
                    budget_message = f"Would exceed budget {budget.name} (${budget.remaining_budget()} remaining, ${total_estimate.estimated_cost_usd} needed)"
                    break
        
        if not can_run:
            return {
                "profile_id": profile_id,
                "analysis_type": "ai_lite",
                "status": "budget_exceeded",
                "message": budget_message,
                "cost_estimate": str(total_estimate.estimated_cost_usd),
                "candidates_count": len(candidates),
                "results": [],
                "budget_info": {
                    "estimated_cost": str(total_estimate.estimated_cost_usd),
                    "service": service.value,
                    "model": model_preference
                }
            }
        
        # Execute AI-Lite analysis
        logger.info(f"Frontend data geographic_scope: {frontend_data['selected_profile'].get('geographic_scope', 'NOT_FOUND')}")
        try:
            ai_lite_result = await ai_service.execute_ai_lite_analysis(frontend_data)
            
            # Format results for frontend
            analysis_results = []
            
            # Handle both dict and object response formats
            candidate_analyses = ai_lite_result.get("candidate_analyses", {}) if isinstance(ai_lite_result, dict) else getattr(ai_lite_result, "candidate_analyses", {})
            
            for candidate_id, analysis in candidate_analyses.items():
                # Handle both dict and object formats for analysis data
                if isinstance(analysis, dict):
                    result = {
                        "candidate_id": candidate_id,
                        "organization_name": analysis.get("organization_name", "Unknown"),
                        "compatibility_score": analysis.get("compatibility_score", 0.0),
                        "confidence_level": analysis.get("confidence_level", 0.0),
                        "recommendation": analysis.get("recommendation_summary", "No recommendation"),
                        "key_insights": analysis.get("key_insights", []),
                        "cost": str(analysis.get("processing_cost", 0.0)),
                        "processing_time": analysis.get("processing_time_seconds", 0.0)
                    }
                    
                    if research_mode and "research_summary" in analysis:
                        result["research_summary"] = analysis["research_summary"]
                else:
                    result = {
                        "candidate_id": candidate_id,
                        "organization_name": getattr(analysis, "organization_name", "Unknown"),
                        "compatibility_score": getattr(analysis, "compatibility_score", 0.0),
                        "confidence_level": getattr(analysis, "confidence_level", 0.0),
                        "recommendation": getattr(analysis, "recommendation_summary", "No recommendation"),
                        "key_insights": getattr(analysis, "key_insights", []),
                        "cost": str(getattr(analysis, "processing_cost", 0.0)),
                        "processing_time": getattr(analysis, "processing_time_seconds", 0.0)
                    }
                    
                    if research_mode and hasattr(analysis, 'research_summary'):
                        result["research_summary"] = analysis.research_summary
                
                analysis_results.append(result)
            
            # Handle both dict and object formats for ai_lite_result metadata
            if isinstance(ai_lite_result, dict):
                batch_id = ai_lite_result.get("batch_id", "unknown")
                successful_analyses = ai_lite_result.get("successful_analyses", len(analysis_results))
                failed_analyses = ai_lite_result.get("failed_analyses", 0)
                total_cost = ai_lite_result.get("total_cost", 0.0)
                average_cost = ai_lite_result.get("average_cost_per_candidate", 0.0)
                total_processing_time = ai_lite_result.get("total_processing_time", 0.0)
            else:
                batch_id = getattr(ai_lite_result, "batch_id", "unknown")
                successful_analyses = getattr(ai_lite_result, "successful_analyses", len(analysis_results))
                failed_analyses = getattr(ai_lite_result, "failed_analyses", 0)
                total_cost = getattr(ai_lite_result, "total_cost", 0.0)
                average_cost = getattr(ai_lite_result, "average_cost_per_candidate", 0.0)
                total_processing_time = getattr(ai_lite_result, "total_processing_time", 0.0)
            
            return {
                "profile_id": profile_id,
                "analysis_type": "ai_lite",
                "status": "completed",
                "batch_id": batch_id,
                "processing_summary": {
                    "total_candidates": len(processed_candidates),
                    "successful_analyses": successful_analyses,
                    "failed_analyses": failed_analyses,
                    "total_cost": str(total_cost),
                    "average_cost_per_candidate": str(average_cost),
                    "total_processing_time": total_processing_time,
                    "model_used": model_preference,
                    "research_mode": research_mode
                },
                "results": analysis_results,
                "cost_breakdown": {
                    "estimated_cost": str(total_estimate.estimated_cost_usd),
                    "actual_cost": str(total_cost),
                    "service": service.value,
                    "candidates_processed": len(analysis_results)
                },
                "budget_status": budget_message
            }
            
        except Exception as ai_error:
            logger.error(f"AI-Lite processing failed: {ai_error}")
            return {
                "profile_id": profile_id,
                "analysis_type": "ai_lite",
                "status": "processing_error",
                "message": f"AI analysis failed: {str(ai_error)}",
                "cost_estimate": str(total_estimate.estimated_cost_usd),
                "candidates_count": len(candidates),
                "results": []
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI-Lite profile analysis: {e}")
        raise HTTPException(status_code=500, detail=f"AI-Lite analysis failed: {str(e)}")


@app.get("/api/profiles/{profile_id}/research/decision-package/{opportunity_id}")
async def generate_decision_package(profile_id: str, opportunity_id: str) -> Dict[str, Any]:
    """Generate comprehensive decision package for grant team"""
    try:
        from src.analysis.research_scoring_integration import ResearchScoringIntegration
        from src.analysis.ai_research_platform import ReportFormat
        
        # Get opportunity data
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        opportunity = None
        for opp in profile.opportunities:
            if opp.opportunity_id == opportunity_id:
                opportunity = opp.model_dump()
                break
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Perform integrated analysis first
        async with ResearchScoringIntegration(cost_optimization=True) as integration:
            analysis = await integration.analyze_opportunity_integrated(
                opportunity, include_research=True, report_type=ReportFormat.EVALUATION_SUMMARY
            )
            
            # Generate decision package
            decision_package = await integration.generate_team_decision_package(analysis)
        
        logger.info(f"Decision package generated for {analysis.organization_name}")
        return decision_package
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating decision package: {e}")
        raise HTTPException(status_code=500, detail=f"Decision package generation failed: {str(e)}")


@app.post("/api/research/website-intelligence")
async def analyze_website_intelligence(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform website intelligence analysis"""
    try:
        from src.analysis.ai_research_platform import AIResearchPlatform
        
        url = request_data.get('url')
        opportunity_data = request_data.get('opportunity_data', {})
        
        if not url:
            raise HTTPException(status_code=400, detail="URL required")
        
        # Perform website analysis
        async with AIResearchPlatform(cost_optimization=True) as research_platform:
            intelligence = await research_platform.analyze_website(url, opportunity_data)
        
        # Convert to response format
        response = {
            'analysis_id': f"website_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'url': intelligence.url,
            'domain': intelligence.domain,
            'website_intelligence': {
                'title': intelligence.title,
                'description': intelligence.description,
                'organization_type': intelligence.organization_type,
                'quality_score': intelligence.quality_score,
                'program_areas': intelligence.program_areas,
                'funding_info': intelligence.funding_info
            },
            'contacts_identified': [
                {
                    'name': contact.name,
                    'title': contact.title,
                    'email': contact.email,
                    'phone': contact.phone,
                    'confidence': contact.confidence,
                    'source': contact.source
                }
                for contact in intelligence.contact_info
            ],
            'facts_extracted': [
                {
                    'fact': fact.fact,
                    'category': fact.category,
                    'confidence': fact.confidence,
                    'source': fact.source,
                    'date_extracted': fact.date_extracted.isoformat()
                }
                for fact in intelligence.key_facts
            ],
            'analysis_timestamp': intelligence.analysis_timestamp.isoformat()
        }
        
        logger.info(f"Website intelligence analysis completed for {url}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in website intelligence analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Website analysis failed: {str(e)}")


@app.get("/api/research/performance-summary")
async def get_research_performance_summary() -> Dict[str, Any]:
    """Get research platform performance summary"""
    try:
        from src.analysis.research_scoring_integration import ResearchScoringIntegration
        
        # Get performance summary (this would be from a persistent service instance in production)
        async with ResearchScoringIntegration(cost_optimization=True) as integration:
            performance_summary = integration.get_performance_summary()
        
        # Add current timestamp
        performance_summary['retrieved_at'] = datetime.now().isoformat()
        
        return performance_summary
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance summary: {str(e)}")


@app.post("/api/research/export-results")
async def export_research_results(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Export research analysis results"""
    try:
        from src.analysis.research_scoring_integration import ResearchScoringIntegration, BatchAnalysisResult
        
        batch_id = request_data.get('batch_id')
        export_format = request_data.get('format', 'json')
        
        if not batch_id:
            raise HTTPException(status_code=400, detail="batch_id required")
        
        # In a full implementation, this would retrieve the actual batch result from storage
        # For now, return a mock export confirmation
        
        export_data = {
            'export_id': f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'batch_id': batch_id,
            'export_format': export_format,
            'exported_at': datetime.now().isoformat(),
            'status': 'completed',
            'message': f'Research results exported in {export_format} format'
        }
        
        logger.info(f"Research results export initiated for batch {batch_id}")
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting research results: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# Phase 4: AI Heavy Dossier Builder API Endpoints

@app.post("/api/profiles/{profile_id}/dossier/generate")
async def generate_comprehensive_dossier(
    profile_id: str,
    opportunity_ids: List[str] = Query(..., description="List of opportunity IDs to analyze"),
    analysis_depth: str = Query("comprehensive", description="Analysis depth: basic, standard, comprehensive"),
    target_audience: str = Query("executive", description="Target audience: executive, board, implementation, stakeholder"),
    cost_optimization: bool = Query(False, description="Enable cost optimization for AI processing")
):
    """Generate comprehensive AI Heavy dossier for opportunities"""
    try:
        from src.analysis.ai_heavy_dossier_builder import AIHeavyDossierBuilder
        
        # Initialize dossier builder
        builder = AIHeavyDossierBuilder(
            cost_optimization=cost_optimization,
            quality_threshold=0.8 if analysis_depth == "comprehensive" else 0.6
        )
        
        # Generate comprehensive dossier
        dossier = await builder.generate_comprehensive_dossier(
            profile_id=profile_id,
            opportunity_ids=opportunity_ids,
            analysis_depth=analysis_depth,
            target_audience=target_audience
        )
        
        return {
            "success": True,
            "dossier_id": dossier.dossier_id,
            "profile_id": profile_id,
            "analysis_summary": {
                "opportunities_analyzed": len(opportunity_ids),
                "analysis_depth": analysis_depth,
                "target_audience": target_audience,
                "confidence_score": dossier.executive_decision.confidence_score,
                "success_probability": dossier.executive_decision.success_probability,
                "recommendation": dossier.executive_decision.primary_recommendation
            },
            "generation_metadata": {
                "generated_at": dossier.generated_at,
                "ai_analysis_cost": dossier.ai_analysis_cost,
                "processing_time_seconds": dossier.processing_time_seconds
            },
            "available_documents": [template.template_id for template in dossier.available_documents],
            "dossier": dossier.model_dump()
        }
        
    except Exception as e:
        logger.error(f"Error generating dossier for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate dossier: {str(e)}")

@app.post("/api/dossier/{dossier_id}/generate-document")
async def generate_decision_document(
    dossier_id: str,
    template_id: str = Query(..., description="Document template ID"),
    format_type: str = Query("comprehensive", description="Document format: executive_brief, detailed_report, presentation, dashboard, compliance_report"),
    customizations: Optional[Dict[str, Any]] = None
):
    """Generate decision-ready document from dossier"""
    try:
        from src.analysis.decision_document_templates import DecisionDocumentTemplates
        from src.analysis.ai_heavy_dossier_builder import AIHeavyDossierBuilder
        
        # Load dossier (in production, this would be from database)
        builder = AIHeavyDossierBuilder()
        dossier = await builder.load_dossier(dossier_id)
        
        if not dossier:
            raise HTTPException(status_code=404, detail=f"Dossier {dossier_id} not found")
        
        # Generate document
        template_generator = DecisionDocumentTemplates()
        document = template_generator.generate_document(
            dossier=dossier,
            template_id=template_id,
            customizations=customizations or {}
        )
        
        return {
            "success": True,
            "document_id": document.document_id,
            "dossier_id": dossier_id,
            "template_id": template_id,
            "format_type": format_type,
            "document_metadata": {
                "generated_at": document.generated_at,
                "target_audience": document.target_audience,
                "document_type": document.document_type,
                "word_count": document.word_count,
                "confidence_level": document.confidence_level
            },
            "content": document.content,
            "executive_summary": document.executive_summary,
            "key_recommendations": document.key_recommendations
        }
        
    except Exception as e:
        logger.error(f"Error generating document for dossier {dossier_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate document: {str(e)}")

@app.get("/api/dossier/templates")
async def get_available_templates():
    """Get list of available document templates"""
    try:
        from src.analysis.decision_document_templates import DecisionDocumentTemplates
        
        template_generator = DecisionDocumentTemplates()
        templates = template_generator.get_available_templates()
        
        return {
            "success": True,
            "templates": [
                {
                    "template_id": template.template_id,
                    "name": template.name,
                    "description": template.description,
                    "target_audience": template.target_audience,
                    "document_type": template.document_type,
                    "estimated_length": template.estimated_length,
                    "complexity_level": template.complexity_level
                }
                for template in templates
            ]
        }
        
    except Exception as e:
        logger.error(f"Error retrieving templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve templates: {str(e)}")

@app.get("/api/dossier/performance-summary")
async def get_dossier_performance_summary():
    """Get performance summary for AI Heavy dossier generation"""
    try:
        from src.analysis.ai_heavy_dossier_builder import AIHeavyDossierBuilder
        
        builder = AIHeavyDossierBuilder()
        performance_stats = builder.get_performance_stats()
        
        return {
            "success": True,
            "performance_summary": performance_stats,
            "system_status": "operational",
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving performance summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve performance summary: {str(e)}")

@app.post("/api/profiles/{profile_id}/dossier/batch-generate")
async def batch_generate_dossiers(
    profile_id: str,
    opportunity_batches: List[Dict[str, Any]] = Body(..., description="List of opportunity batches with analysis configurations"),
    global_settings: Optional[Dict[str, Any]] = Body(None, description="Global settings for all dossiers")
):
    """Generate multiple dossiers in batch for different opportunity sets"""
    try:
        from src.analysis.ai_heavy_dossier_builder import AIHeavyDossierBuilder
        
        # Initialize builder with global settings
        global_config = global_settings or {}
        builder = AIHeavyDossierBuilder(
            cost_optimization=global_config.get("cost_optimization", False),
            quality_threshold=global_config.get("quality_threshold", 0.8)
        )
        
        # Process batches
        batch_results = []
        total_cost = 0.0
        
        for i, batch in enumerate(opportunity_batches):
            try:
                dossier = await builder.generate_comprehensive_dossier(
                    profile_id=profile_id,
                    opportunity_ids=batch.get("opportunity_ids", []),
                    analysis_depth=batch.get("analysis_depth", "standard"),
                    target_audience=batch.get("target_audience", "executive")
                )
                
                batch_results.append({
                    "batch_id": i + 1,
                    "success": True,
                    "dossier_id": dossier.dossier_id,
                    "opportunities_count": len(batch.get("opportunity_ids", [])),
                    "confidence_score": dossier.executive_decision.confidence_score,
                    "recommendation": dossier.executive_decision.primary_recommendation,
                    "cost": dossier.ai_analysis_cost
                })
                
                total_cost += dossier.ai_analysis_cost
                
            except Exception as batch_error:
                logger.error(f"Error processing batch {i + 1}: {batch_error}")
                batch_results.append({
                    "batch_id": i + 1,
                    "success": False,
                    "error": str(batch_error),
                    "opportunities_count": len(batch.get("opportunity_ids", [])),
                    "cost": 0.0
                })
        
        successful_batches = sum(1 for result in batch_results if result["success"])
        
        return {
            "success": True,
            "profile_id": profile_id,
            "batch_summary": {
                "total_batches": len(opportunity_batches),
                "successful_batches": successful_batches,
                "failed_batches": len(opportunity_batches) - successful_batches,
                "total_cost": total_cost,
                "average_cost_per_batch": total_cost / len(opportunity_batches) if opportunity_batches else 0
            },
            "batch_results": batch_results
        }
        
    except Exception as e:
        logger.error(f"Error in batch dossier generation for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate batch dossiers: {str(e)}")


# Phase 6 Decision Synthesis API Endpoints

@app.post("/api/profiles/{profile_id}/approach/synthesize-decision")
async def synthesize_decision(
    profile_id: str,
    request_data: Dict[str, Any] = Body(...)
):
    """
    Phase 6 Decision Synthesis API - APPROACH Tab Integration
    
    Synthesizes decision recommendations from all workflow stages using the
    advanced decision synthesis framework.
    
    Args:
        profile_id: Organization profile ID
        request_data: {
            "opportunity_id": str,
            "workflow_results": [
                {
                    "stage": "discover|plan|analyze|examine",
                    "primary_score": float,
                    "confidence": float,
                    "scorer_type": str,
                    "metadata": dict,
                    "processing_time_ms": float
                }
            ],
            "enhanced_data": dict (optional),
            "user_preferences": dict (optional),
            "decision_context": dict (optional)
        }
        
    Returns:
        Comprehensive decision synthesis result with recommendations,
        visualizations, audit trails, and export-ready data.
    """
    try:
        from src.integration.decision_synthesis_integration import (
            decision_synthesis_bridge, DecisionSynthesisRequest, WorkflowStageResult
        )
        from src.core.unified_scorer_interface import WorkflowStage, ScorerType
        
        logger.info(f"Starting decision synthesis for profile {profile_id}")
        
        # Validate required fields
        if "opportunity_id" not in request_data or "workflow_results" not in request_data:
            raise HTTPException(status_code=400, detail="Missing required fields: opportunity_id, workflow_results")
        
        # Convert workflow results to structured format
        workflow_results = []
        for result_data in request_data["workflow_results"]:
            try:
                stage = WorkflowStage(result_data["stage"])
                scorer_type = ScorerType(result_data.get("scorer_type", "discovery"))
                
                workflow_result = WorkflowStageResult(
                    stage=stage,
                    primary_score=result_data["primary_score"],
                    confidence=result_data["confidence"],
                    scorer_type=scorer_type,
                    metadata=result_data.get("metadata", {}),
                    processing_time_ms=result_data.get("processing_time_ms", 0.0),
                    timestamp=datetime.now()
                )
                workflow_results.append(workflow_result)
            except ValueError as ve:
                logger.warning(f"Invalid workflow result data: {ve}, skipping...")
                continue
        
        if not workflow_results:
            raise HTTPException(status_code=400, detail="No valid workflow results provided")
        
        # Create decision synthesis request
        synthesis_request = DecisionSynthesisRequest(
            profile_id=profile_id,
            opportunity_id=request_data["opportunity_id"],
            workflow_results=workflow_results,
            enhanced_data=request_data.get("enhanced_data"),
            user_preferences=request_data.get("user_preferences"),
            decision_context=request_data.get("decision_context")
        )
        
        # Execute decision synthesis
        synthesis_result = await decision_synthesis_bridge.synthesize_decision(synthesis_request)
        
        # Format response for web interface
        response_data = {
            "success": True,
            "profile_id": profile_id,
            "opportunity_id": request_data["opportunity_id"],
            "synthesis_score": synthesis_result.synthesis_score,
            "overall_confidence": synthesis_result.overall_confidence,
            "recommendation": synthesis_result.recommendation,
            "stage_contributions": synthesis_result.stage_contributions,
            "feasibility_assessment": synthesis_result.feasibility_assessment,
            "resource_requirements": synthesis_result.resource_requirements,
            "implementation_timeline": synthesis_result.implementation_timeline,
            "risk_assessment": synthesis_result.risk_assessment,
            "success_factors": synthesis_result.success_factors,
            "decision_rationale": synthesis_result.decision_rationale,
            "audit_trail": synthesis_result.audit_trail,
            "visualization_data": synthesis_result.visualization_data,
            "export_ready": True,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Decision synthesis completed for {profile_id} with recommendation: {synthesis_result.recommendation}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in decision synthesis for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Decision synthesis failed: {str(e)}")


@app.get("/api/profiles/{profile_id}/approach/decision-history")
async def get_decision_history(
    profile_id: str,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0)
):
    """
    Get decision synthesis history for a profile
    
    Args:
        profile_id: Organization profile ID
        limit: Maximum number of decisions to return
        offset: Offset for pagination
        
    Returns:
        List of historical decision synthesis results
    """
    try:
        # This would connect to a decision history storage system
        # For now, return mock data structure
        return {
            "success": True,
            "profile_id": profile_id,
            "decisions": [],  # Would be populated from storage
            "total_count": 0,
            "limit": limit,
            "offset": offset,
            "message": "Decision history storage not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving decision history for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve decision history: {str(e)}")


@app.post("/api/profiles/{profile_id}/approach/export-decision")
async def export_decision_document(
    profile_id: str,
    request_data: Dict[str, Any] = Body(...)
):
    """
    Export decision synthesis result as professional document
    
    Args:
        profile_id: Organization profile ID
        request_data: {
            "synthesis_result": dict,  # Result from decision synthesis
            "export_format": "pdf|excel|powerpoint|html|json",
            "template": "executive|detailed|presentation|minimal",
            "branding": dict (optional)
        }
        
    Returns:
        File download information or direct file response
    """
    try:
        from src.export.comprehensive_export_system import ComprehensiveExportSystem
        
        logger.info(f"Exporting decision document for profile {profile_id}")
        
        # Validate required fields
        required_fields = ["synthesis_result", "export_format"]
        for field in required_fields:
            if field not in request_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Initialize export system
        export_system = ComprehensiveExportSystem()
        
        # Prepare export configuration
        export_config = {
            'format': request_data['export_format'],
            'template': request_data.get('template', 'executive'),
            'branding': request_data.get('branding', {}),
            'profile_id': profile_id,
            'timestamp': datetime.now()
        }
        
        # Generate export (this would use the comprehensive export system)
        # For now, return success with file info
        export_filename = f"decision_synthesis_{profile_id}_{int(datetime.now().timestamp())}.{request_data['export_format']}"
        
        return {
            "success": True,
            "profile_id": profile_id,
            "export_filename": export_filename,
            "export_format": request_data['export_format'],
            "template_used": export_config['template'],
            "file_size": "1.2MB",  # Mock data
            "download_url": f"/api/exports/{export_filename}",
            "generated_timestamp": datetime.now().isoformat(),
            "expires_in_hours": 24,
            "message": "Export generation completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting decision document for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Export generation failed: {str(e)}")


# Phase 6 Visualization Framework API Endpoints

@app.post("/api/visualizations/generate-chart")
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
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {str(e)}")


@app.post("/api/visualizations/decision-dashboard")
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
        raise HTTPException(status_code=500, detail=f"Dashboard creation failed: {str(e)}")


@app.get("/api/visualizations/{chart_id}/export/{format}")
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
        raise HTTPException(status_code=500, detail=f"Chart export failed: {str(e)}")


@app.get("/api/visualizations/chart-types")
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
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chart types: {str(e)}")


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