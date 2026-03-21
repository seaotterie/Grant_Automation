#!/usr/bin/env python3
"""
Catalynx - Modern Web Interface
FastAPI backend with real-time progress monitoring
"""

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Body, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
import logging
import sys
import uuid
import random
import shutil
import re
import sqlite3
import dataclasses
from pathlib import Path
from datetime import datetime, UTC
from typing import List, Dict, Optional, Any
import uvicorn

# When installed via ``pip install -e .`` (pyproject.toml), setuptools makes
# ``src.*`` and ``tools.*`` importable automatically.  The fallback below only
# activates for *uninstalled* development runs (``python src/web/main.py``).
try:
    from importlib.util import find_spec as _find_spec
    if _find_spec("src") is None:
        _project_root = str(Path(__file__).resolve().parent.parent.parent)
        if _project_root not in sys.path:
            sys.path.insert(0, _project_root)
    del _find_spec
except Exception:
    pass

from src.core.workflow_engine import get_workflow_engine
from src.core.data_models import WorkflowConfig
from src.core.data_validation_pipeline import DataValidationPipeline
from src.web.services.workflow_service import WorkflowService
from src.web.services.progress_service import ProgressService
from src.web.models.requests import ClassificationRequest, WorkflowRequest
from src.web.models.responses import DashboardStats, WorkflowResponse, SystemStatus
# ProfileService removed - consolidated to DatabaseManager only
from src.profiles.unified_service import get_unified_profile_service
from src.discovery.unified_discovery_adapter import get_unified_discovery_adapter
from src.profiles.entity_service import get_entity_profile_service
from src.profiles.models import OrganizationProfile, FundingType
from src.database.database_manager import DatabaseManager, Opportunity
from src.profiles.workflow_integration import ProfileWorkflowIntegrator
from src.profiles.metrics_tracker import get_metrics_tracker
from src.discovery.entity_discovery_service import get_entity_discovery_service
from src.discovery.discovery_engine import discovery_engine
from src.pipeline.pipeline_engine import ProcessingPriority
from src.pipeline.resource_allocator import resource_allocator
from src.processors.registry import get_processor_summary
# EINLookupProcessor deprecated - use EIN Validator Tool instead
# from src.processors.lookup.ein_lookup import EINLookupProcessor
# Legacy AI service manager - removed in 12-factor migration
# from src.processors.analysis.ai_service_manager import get_ai_service_manager
from src.web.services.scoring_service import (
    get_scoring_service, ScoreRequest, ScoreResponse,
    PromotionRequest, PromotionResponse, BulkPromotionRequest, BulkPromotionResponse
)
from src.web.services.tool25_profile_builder import get_tool25_profile_builder

# Security and Authentication imports
from src.middleware.security import (
    SecurityHeadersMiddleware, 
    XSSProtectionMiddleware, 
    InputValidationMiddleware,
    RateLimitingMiddleware
)
from src.auth.jwt_auth import get_current_user_dependency, User
from src.web.auth_routes import router as auth_router
from src.web.routers.intelligence import router as intelligence_router
from src.web.routers.workflows import router as workflows_router
from src.web.routers.gateway import router as gateway_router
from src.web.routers.learning import router as learning_router
from src.web.routers.profiles import router as profiles_router  # Phase 9: Fix duplicate fetch-ein endpoint
from src.web.routers.profiles_v2 import router as profiles_v2_router
from src.web.routers.profiles_intelligence import router as profiles_intelligence_router
from src.web.routers.discovery_v2 import router as discovery_v2_router
from src.web.routers.discovery_legacy import router as discovery_legacy_router  # Phase 9: Backward-compatible discovery endpoints
from src.web.routers.discovery import router as discovery_router
# Optional enhanced scraping router (requires scrapy)
try:
    from src.web.routers.enhanced_scraping import router as enhanced_scraping_router
    enhanced_scraping_available = True
except ImportError as e:
    print(f"Enhanced scraping not available: {e}")
    enhanced_scraping_router = None
    enhanced_scraping_available = False

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
            "deletion_timestamp": datetime.now(UTC).isoformat(),
            "deletion_success": deletion_success,
            "deleted_items": deleted_items,
            "items_count": len(deleted_items)
        }
        
        # Write audit log
        audit_dir = Path("data/audit_logs")
        audit_dir.mkdir(exist_ok=True)
        audit_file = audit_dir / f"profile_deletion_{profile_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
        
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

# Lifespan event handler (replaces deprecated on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup services."""
    # Startup
    logger.info("Starting Catalynx Web Interface...")
    logger.info("Initializing 12-factor tool architecture...")

    # Initialize 12-factor tool registry
    try:
        from src.core.tool_registry import get_registry
        tool_registry = get_registry()
        operational_tools = tool_registry.get_operational_tools()
        logger.info(f"Loaded {len(operational_tools)} operational 12-factor tools")
        logger.info(f"Tool architecture: Phase 8 - Nonprofit Workflow Solidification")
    except Exception as e:
        logger.warning(f"Failed to initialize tool registry: {e}")

    logger.info("Catalynx API ready!")

    yield

    # Shutdown (if needed)
    logger.info("Shutting down Catalynx Web Interface...")

# Create FastAPI application
app = FastAPI(
    title="Catalynx - Grant Research Automation",
    description="Modern web interface for intelligent grant research and classification",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
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

# Add deprecation middleware for Phase 9 API consolidation
from src.web.middleware.deprecation import add_deprecation_headers
app.middleware("http")(add_deprecation_headers)

# Include authentication routes
app.include_router(auth_router)

# Include Intelligence (Tiered Analysis) routes
app.include_router(intelligence_router)

# Include Workflow execution routes
app.include_router(workflows_router)

# Human Gateway (Phase E)
app.include_router(gateway_router)
app.include_router(learning_router)

# Include unified tool execution routes (Phase 6)
from src.web.routers.tools import router as tools_router
app.include_router(tools_router)

# Include profile routes (Phase 9: Fix duplicate fetch-ein endpoint)
# This replaces the deprecated endpoint in main.py that used EINLookupProcessor
# Note: profiles_router already has prefix="/api/profiles" so don't add it again
app.include_router(profiles_router)

# Include modernized profile routes (Phase 8 - Task 19)
app.include_router(profiles_v2_router)

# Include profiles intelligence pipeline (Phase 9)
app.include_router(profiles_intelligence_router)

# Include V2 discovery routes (Phase 9 - Week 2)
app.include_router(discovery_v2_router)

# Include legacy discovery routes for backward compatibility (Phase 9 - GUI Testing)
app.include_router(discovery_legacy_router)

# Include discovery routes (extracted from main.py)
app.include_router(discovery_router)

# Include opportunities routes (Phase 9 - SCREENING stage)
from src.web.routers.opportunities import router as opportunities_router
app.include_router(opportunities_router)

# Include admin routes (Phase 9 - deprecation monitoring)
from src.web.routers.admin import router as admin_router
app.include_router(admin_router)

# Include Foundation Network Intelligence routes (Phase 9 - Foundation Network Intelligence)
from src.web.routers.foundation_network import router as foundation_network_router
app.include_router(foundation_network_router)

# Include Network Graph routes (Phase 9 - offline population + ranking)
from src.web.routers.network import router as network_router
app.include_router(network_router)

# Include Enhanced Scraping routes
# Include enhanced scraping router only if available
if enhanced_scraping_available and enhanced_scraping_router:
    app.include_router(enhanced_scraping_router)
    print("Enhanced scraping router enabled")
else:
    print("Enhanced scraping router disabled (scrapy not available)")

# Include extracted route modules (Phase 9 refactor)
from src.web.routers.docs_help import router as docs_help_router
app.include_router(docs_help_router)

from src.web.routers.welcome import router as welcome_router
app.include_router(welcome_router)

from src.web.routers.pages import router as pages_router
app.include_router(pages_router)

# Include route modules extracted from main.py (Phase 9 - monolith decomposition)
from src.web.routers.pipeline import router as pipeline_router
app.include_router(pipeline_router)

from src.web.routers.funnel import router as funnel_router
app.include_router(funnel_router)

from src.web.routers.analysis import router as analysis_router
app.include_router(analysis_router)

from src.web.routers.ai_endpoints import router as ai_endpoints_router
app.include_router(ai_endpoints_router)

from src.web.routers.scoring_promotion import router as scoring_promotion_router
app.include_router(scoring_promotion_router)

from src.web.routers.dossier import router as dossier_router
app.include_router(dossier_router)

from src.web.routers.visualizations import router as visualizations_router
app.include_router(visualizations_router)

from src.web.routers.classification import router as classification_router
app.include_router(classification_router)

from src.web.routers.search_export import router as search_export_router
app.include_router(search_export_router)

from src.web.routers.research import router as research_router
app.include_router(research_router)

# Duplicate GET /api/profiles moved to profiles router

# Add global exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
try:
    from pydantic import ValidationError
    app.add_exception_handler(ValidationError, validation_exception_handler)
except ImportError:
    logger.warning("Pydantic ValidationError handler not available")

# Initialize services
workflow_service = WorkflowService()
progress_service = ProgressService()
# profile_service replaced with unified_service for compatibility
unified_service = get_unified_profile_service()
profile_service = unified_service  # Compatibility assignment for existing references
unified_discovery_adapter = get_unified_discovery_adapter()
entity_profile_service = get_entity_profile_service()  # Enhanced entity-based service
entity_discovery_service = get_entity_discovery_service()  # Enhanced discovery service
profile_integrator = ProfileWorkflowIntegrator()
metrics_tracker = get_metrics_tracker()

# Initialize database service for opportunity storage
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
database_path = os.path.join(project_root, "data", "catalynx.db")
database_service = DatabaseManager(database_path)
logger.info("Database service initialized successfully")

# =====================================================================================
# 990 DATA EXTRACTION FUNCTIONS - Real Data Population
# =====================================================================================

def _extract_website_url_from_990(org_data: Dict) -> str:
    """Extract website URL from ProPublica 990 data"""
    try:
        # Check multiple possible fields for website URL
        website_fields = [
            "website", "website_url", "web_address", "url",
            "organization_website", "website_address"
        ]

        # First check the organization level data
        for field in website_fields:
            if field in org_data and org_data[field]:
                url = str(org_data[field]).strip()
                if url and url.lower() not in ['', 'none', 'null', 'n/a']:
                    # Auto-format URL with https:// if needed
                    if not url.startswith(('http://', 'https://')):
                        url = f"https://{url}"
                    return url

        # Check nested structures if they exist
        if 'contact_info' in org_data and isinstance(org_data['contact_info'], dict):
            for field in website_fields:
                if field in org_data['contact_info'] and org_data['contact_info'][field]:
                    url = str(org_data['contact_info'][field]).strip()
                    if url and url.lower() not in ['', 'none', 'null', 'n/a']:
                        if not url.startswith(('http://', 'https://')):
                            url = f"https://{url}"
                        return url

        return None

    except Exception as e:
        logger.warning(f"Error extracting website URL from 990 data: {e}")
        return None

def _extract_mission_from_990(org_data: Dict) -> str:
    """Extract mission statement from ProPublica 990 data"""
    try:
        # Check multiple possible fields for mission statement
        mission_fields = [
            "mission_description", "mission_statement", "mission",
            "activity_description", "activities", "purpose",
            "organization_purpose", "primary_purpose"
        ]

        for field in mission_fields:
            if field in org_data and org_data[field]:
                mission = str(org_data[field]).strip()
                if mission and mission.lower() not in ['', 'none', 'null', 'n/a']:
                    return mission

        return None

    except Exception as e:
        logger.warning(f"Error extracting mission from 990 data: {e}")
        return None

# Serve static files using FastAPI's built-in StaticFiles (secure, no path traversal)
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Routes moved to routers: classification.py, research.py

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

# Routes moved to routers: search_export.py (exports/classification, exports/workflow)

# Helper methods for enhanced web scraping



async def _save_web_intelligence_data(ein: str, url: str, intelligence_data, organization_name: str = "") -> bool:
    """
    Save web intelligence data directly to database.
    Clean approach - no EIN extraction from URL needed.
    """
    try:
        import sqlite3
        import json
        from datetime import datetime
        
        # Extract intelligence information
        programs = intelligence_data.program_data if hasattr(intelligence_data, 'program_data') else []
        leadership = intelligence_data.leadership_data if hasattr(intelligence_data, 'leadership_data') else []
        contact_data = intelligence_data.contact_data if hasattr(intelligence_data, 'contact_data') else []
        mission_data = intelligence_data.mission_data if hasattr(intelligence_data, 'mission_data') else []
        intelligence_score = intelligence_data.intelligence_score if hasattr(intelligence_data, 'intelligence_score') else 0
        pages_scraped = len(intelligence_data.pages_scraped) if hasattr(intelligence_data, 'pages_scraped') else 0
        total_content_length = intelligence_data.total_content_length if hasattr(intelligence_data, 'total_content_length') else 0
        
        # Save to database
        with sqlite3.connect("data/catalynx.db") as conn:
            conn.execute("""
                INSERT OR REPLACE INTO web_intelligence (
                    ein, url, scrape_date, intelligence_quality_score, 
                    content_richness_score, pages_scraped, total_content_length,
                    leadership_data, leadership_count, program_data, program_count,
                    contact_data, mission_statements, mission_count,
                    processing_duration_ms, website_structure_quality
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ein,
                url,
                datetime.now().isoformat(),
                intelligence_score,
                min(intelligence_score / 100.0 * 0.9, 1.0),  # Content richness score
                pages_scraped,
                total_content_length,
                json.dumps(leadership),
                len(leadership),
                json.dumps(programs),
                len(programs),
                json.dumps(contact_data),
                json.dumps(mission_data),
                len(mission_data),
                int((intelligence_data.processing_time if hasattr(intelligence_data, 'processing_time') else 1.0) * 1000),
                "Good" if intelligence_score > 50 else "Fair"
            ))
            conn.commit()
            
        logger.info(f"Successfully saved web intelligence for EIN {ein}: {len(programs)} programs, {len(leadership)} leadership")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save web intelligence data for EIN {ein}: {e}")
        return False

def _score_scraped_content(content: str, organization_data: Dict) -> float:
    """
    Score scraped content for relevance to the organization
    
    Returns score between 0.0 and 1.0
    """
    score = 0.0
    content_lower = content.lower()
    org_name_lower = organization_data.get('organization_name', '').lower()
    
    # Check for organization name mentions
    if org_name_lower and org_name_lower in content_lower:
        score += 0.4
    
    # Check for nonprofit indicators
    nonprofit_indicators = ['nonprofit', 'non-profit', 'charity', 'foundation', 'mission', 'donate', 'volunteer']
    indicator_count = sum(1 for indicator in nonprofit_indicators if indicator in content_lower)
    score += min(indicator_count * 0.1, 0.3)
    
    # Check for address mentions
    city = organization_data.get('city', '').lower()
    state = organization_data.get('state', '').lower()
    if city and city in content_lower:
        score += 0.2
    if state and state in content_lower:
        score += 0.1
    
    return min(score, 1.0)

def _extract_organization_info_simple(content: str, extracted_info: Dict):
    """Simple extraction of organization information from content"""
    content_lower = content.lower()
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    mission_keywords = ["mission", "purpose", "vision", "goal", "about"]
    contact_keywords = ["contact", "email", "phone", "address"]
    program_keywords = ["program", "service", "initiative", "project"]
    leadership_keywords = ["board", "director", "ceo", "president", "staff"]
    
    for line in lines:
        line_lower = line.lower()
        
        if len(line) < 20 or len(line) > 300:
            continue
            
        if any(keyword in line_lower for keyword in mission_keywords):
            if line not in extracted_info["mission_statements"]:
                extracted_info["mission_statements"].append(line)
                
        elif any(keyword in line_lower for keyword in contact_keywords):
            if "@" in line or "phone" in line_lower:
                if line not in extracted_info["contact_info"]:
                    extracted_info["contact_info"].append(line)
                    
        elif any(keyword in line_lower for keyword in program_keywords):
            if line not in extracted_info["programs"]:
                extracted_info["programs"].append(line)
                
        elif any(keyword in line_lower for keyword in leadership_keywords):
            if line not in extracted_info["leadership"]:
                extracted_info["leadership"].append(line)
    
    # Limit results
    for key in extracted_info:
        extracted_info[key] = extracted_info[key][:5]

def _validate_cached_intelligence_quality(stored_intelligence: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the quality of cached intelligence data to prevent serving fake data"""
    validation_result = {
        'is_high_quality': True,
        'quality_score': 1.0,
        'issues': []
    }
    
    extracted_info = stored_intelligence.get("extracted_info", {})
    
    # Check leadership data for fake indicators
    leadership_data = extracted_info.get("leadership", [])
    if leadership_data:
        fake_patterns = [
            'board of', 'serving as', 'was appointed', 'executive vice', 
            'been the', 'serves as', 'on the', 'at colliers', 'ramps to'
        ]
        
        fake_count = 0
        for leader_info in leadership_data:
            if isinstance(leader_info, str):
                # Old format: "Board of - Director"
                leader_text = leader_info.lower()
                if any(pattern in leader_text for pattern in fake_patterns):
                    fake_count += 1
            elif isinstance(leader_info, dict):
                # New format: {"name": "Board of", "title": "Director"}
                name = leader_info.get('name', '').lower()
                if any(pattern in name for pattern in fake_patterns):
                    fake_count += 1
        
        fake_percentage = fake_count / len(leadership_data) if leadership_data else 0
        if fake_percentage > 0.5:  # More than 50% fake data
            validation_result['is_high_quality'] = False
            validation_result['quality_score'] *= 0.3
            validation_result['issues'].append(f"High fake leadership data: {fake_percentage:.1%}")
    
    # Check for generic contact info
    contact_info = extracted_info.get("contact_info", [])
    if contact_info:
        generic_patterns = ['email', 'phone', 'address', 'contact']
        generic_count = sum(1 for item in contact_info if isinstance(item, str) and item.lower() in generic_patterns)
        if generic_count == len(contact_info):  # All generic
            validation_result['quality_score'] *= 0.7
            validation_result['issues'].append("All contact info is generic labels")
    
    # Check data freshness (prefer recent data)
    scrape_date = stored_intelligence.get("scrape_date", "")
    if scrape_date:
        from datetime import datetime, timedelta
        try:
            cached_date = datetime.fromisoformat(scrape_date.replace('Z', '+00:00'))
            age_days = (datetime.now() - cached_date).days
            if age_days > 7:  # Older than a week
                validation_result['quality_score'] *= 0.9
                validation_result['issues'].append(f"Data is {age_days} days old")
        except:
            pass  # Invalid date format
    
    # Overall quality assessment
    if validation_result['quality_score'] < 0.6:
        validation_result['is_high_quality'] = False
    
    return validation_result

async def _get_stored_intelligence_data(ein: str) -> Optional[Dict[str, Any]]:
    """Retrieve stored intelligence data from the database by EIN"""
    try:
        database_path = "data/catalynx.db"  # Use correct database
        if not Path(database_path).exists():
            logger.warning(f"Intelligence database not found at {database_path}")
            return None
            
        with sqlite3.connect(database_path) as conn:
            # Try both EIN formats - with and without dash for compatibility
            ein_with_dash = f"{ein[:2]}-{ein[2:]}" if len(ein) >= 9 and '-' not in ein else ein
            cursor = conn.execute("""
                SELECT wi.leadership_data, wi.program_data, wi.contact_data, 
                       wi.mission_statements, wi.intelligence_quality_score,
                       wi.leadership_count, wi.program_count, wi.mission_count,
                       wi.url, wi.updated_at
                FROM web_intelligence wi
                WHERE wi.ein = ? OR wi.ein = ? 
                ORDER BY wi.updated_at DESC 
                LIMIT 1
            """, (ein, ein_with_dash))
            
            row = cursor.fetchone()
            if not row:
                logger.info(f"DEBUG: No stored intelligence found for EIN {ein} in web_intelligence table")
                return None
            
            logger.info(f"DEBUG: Found stored intelligence record for EIN {ein}")
            leadership_data, program_data, contact_data, mission_data, quality_score, leadership_count, program_count, mission_count, url, last_updated = row
            logger.info(f"DEBUG: Raw programs data: {program_data} (count: {program_count})")
            logger.info(f"DEBUG: Raw leadership data: {leadership_data} (count: {leadership_count})")
            logger.info(f"DEBUG: Raw mission data: {mission_data} (count: {mission_count})")
            
            # Parse actual JSON data from database - NO MOCK DATA
            extracted_info = {}
            
            try:
                # Parse leadership data
                if leadership_data:
                    import json
                    extracted_info["leadership"] = json.loads(leadership_data)
                    logger.info(f"DEBUG: Parsed {len(extracted_info['leadership'])} real leadership entries")
                else:
                    extracted_info["leadership"] = []
                    
                # Parse program data 
                if program_data:
                    import json
                    extracted_info["programs"] = json.loads(program_data)
                    logger.info(f"DEBUG: Parsed {len(extracted_info['programs'])} real program entries")
                else:
                    extracted_info["programs"] = []
                    
                # Parse mission statements
                if mission_data:
                    import json
                    extracted_info["mission_statements"] = json.loads(mission_data)
                    logger.info(f"DEBUG: Parsed {len(extracted_info['mission_statements'])} real mission statements")
                else:
                    extracted_info["mission_statements"] = []
                    
                # Parse contact data if available
                if contact_data:
                    import json
                    extracted_info["contact_info"] = json.loads(contact_data)
                else:
                    extracted_info["contact_info"] = []
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON data for EIN {ein}: {e}")
                # If JSON parsing fails, return None - no mock data fallback
                return None
                
            # Only return data if we have actual content - no empty mock data
            if not any([extracted_info["leadership"], extracted_info["programs"], extracted_info["mission_statements"]]):
                logger.info(f"DEBUG: No real extracted info found for EIN {ein} - returning None")
                return None
            
            intelligence_data = {
                "successful_scrapes": [{"url": url, "status": "success"}] if url else [],
                "extracted_info": extracted_info,
                "intelligence_quality_score": quality_score,
                "last_updated": last_updated,
                "data_source": "database"
            }
            
            logger.info(f"Retrieved stored intelligence for EIN {ein} with {len(intelligence_data['extracted_info']['programs'])} programs, {len(intelligence_data['extracted_info']['leadership'])} leadership entries")
            return intelligence_data
            
    except Exception as e:
        logger.error(f"Error retrieving stored intelligence for EIN {ein}: {e}")
        return None

# Profile Management API endpoints
# DEPRECATED: Moved to routers/profiles.py - This endpoint uses deprecated EINLookupProcessor
# @app.post("/api/profiles/fetch-ein")
# async def fetch_ein_data_DEPRECATED(request: dict):
#     """
#     DEPRECATED: Moved to routers/profiles.py
#     This endpoint uses deprecated EINLookupProcessor which no longer exists.
#     Use the new endpoint in routers/profiles.py which queries BMF database directly.
#     """
#     pass
#     # OLD CODE BELOW - COMMENTED OUT
#     """
#     Enhanced organization data fetching with web scraping capabilities.
#
#     Combines ProPublica API data with web scraping for comprehensive profiles:
#     - ProPublica API for official 990 data and Schedule I grantees
#     - Web scraping for mission statements, current programs, leadership info
#     - GuideStar and organization websites for additional context
#     """
#     try:
#         ein = request.get('ein', '').strip()
#         enable_web_scraping = request.get('enable_web_scraping', True)
#
#         if not ein:
#             raise HTTPException(status_code=400, detail="EIN is required")
#
#         # Initialize EIN lookup processor
#         ein_processor = EINLookupProcessor()
#        
        # Create workflow config with EIN
#        from src.core.data_models import WorkflowConfig, ProcessorConfig
#        
#        workflow_config = WorkflowConfig(
#            target_ein=ein,
#            target_state=None,
#            target_tags=[],
#            max_results=1
#        )
#        
#        config = ProcessorConfig(
#            workflow_id=str(uuid.uuid4()),
#            processor_name="ein_lookup",
#            workflow_config=workflow_config,
#            processor_specific_config={}
#        )
#        
        # Execute EIN lookup (gets JSON data)
#        result = await ein_processor.execute(config)
#        logger.info(f"EIN lookup result: success={result.success}, data_keys={list(result.data.keys()) if result.data else 'None'}")
#        
#        if result.success and result.data:
#            logger.info(f"Result data structure: {result.data}")
#            org_data = result.data.get('target_organization', {})
#            
            # Prepare basic response data with real 990 data extraction
#            extracted_website = _extract_website_url_from_990(org_data) or org_data.get('website', '')
#            extracted_mission = _extract_mission_from_990(org_data) or org_data.get('mission_description', '') or org_data.get('activity_description', '')
#
#            response_data = {
#                "name": org_data.get('name', ''),
#                "ein": org_data.get('ein', ein),
#                "mission_statement": extracted_mission,
#                "organization_type": str(org_data.get('organization_type', 'nonprofit')).replace('OrganizationType.', '').lower(),
#                "ntee_code": org_data.get('ntee_code', ''),
#                "city": org_data.get('city', ''),
#                "state": org_data.get('state', ''),
#                "website": extracted_website,
#                "website_url": extracted_website,  # For frontend compatibility
#                "revenue": org_data.get('revenue', 0),
#                "assets": org_data.get('assets', 0),
#                "expenses": org_data.get('expenses', 0),
#                "most_recent_filing_year": org_data.get('most_recent_filing_year', ''),
#                "filing_years": org_data.get('filing_years', []),
#                "schedule_i_grantees": [],  # Initialize empty list
#                "schedule_i_status": "not_checked",  # Default status
#                "web_scraping_data": {},  # New field for scraped data
#                "enhanced_with_web_data": False  # Flag to indicate if web enhancement was successful
#            }
#            
            # Enhanced web scraping integration with GPT URL discovery
#            if enable_web_scraping:
#                try:
#                    logger.info(f"Starting intelligent web scraping for {org_data.get('name', 'Unknown')} (EIN: {ein})")
#                    
                    # Step 1: Use GPT URL Discovery to find likely URLs
#                    try:
#                        from src.processors.analysis.gpt_url_discovery import GPTURLDiscoveryProcessor
#                        from src.core.data_models import ProcessorConfig, WorkflowConfig
#                        
                        # Create processor config for URL discovery
#                        url_discovery_processor = GPTURLDiscoveryProcessor()
#                        
                        # Prepare organization data for GPT URL discovery
#                        organization_data = {
#                            'organization_name': org_data.get('name', ''),
#                            'ein': ein,
#                            'address': f"{org_data.get('city', '')}, {org_data.get('state', '')}",
#                            'city': org_data.get('city', ''),
#                            'state': org_data.get('state', ''),
#                            'organization_type': 'nonprofit'
#                        }
#                        
#                        url_config = ProcessorConfig(
#                            workflow_id=str(uuid.uuid4()),
#                            processor_name="gpt_url_discovery",
#                            workflow_config=WorkflowConfig(target_ein=ein),
#                            processor_specific_config={'organization_data': organization_data}
#                        )
#                        
                        # Get URL predictions from GPT
#                        url_result = await url_discovery_processor.execute(url_config)
#                        predicted_urls = []
#                        
#                        if url_result.success and url_result.data.get('urls'):
#                            predicted_urls = url_result.data['urls']
#                            logger.info(f"GPT predicted {len(predicted_urls)} URLs for {org_data.get('name', '')}")
#                        else:
#                            logger.warning(f"GPT URL discovery failed for EIN {ein}: {url_result.error_message}")
#                            
#                    except Exception as gpt_error:
#                        logger.warning(f"GPT URL discovery failed for EIN {ein}: {gpt_error}")
#                        predicted_urls = []
#                    
                    # Step 2: Tool 25 Profile Builder (Scrapy-powered with 990 verification)
#                    logger.info(f"Starting Tool 25 Profile Builder for EIN {ein}")
#
#                    tool25_service = get_tool25_profile_builder()
#                    org_name = org_data.get('name', '')
#
                    # Execute Tool 25 with Smart URL Resolution (User → 990 → GPT priority)
#                    success, tool25_data = await tool25_service.execute_profile_builder(
#                        ein=ein,
#                        organization_name=org_name,
#                        user_provided_url=request.get('user_provided_url'),  # User URL if provided
#                        filing_url=extracted_website,  # From 990 tax filing
#                        gpt_predicted_url=predicted_urls[0] if predicted_urls else None,  # GPT fallback
#                        require_990_verification=True,
#                        min_confidence_score=0.7
#                    )
#
#                    if success:
                        # Merge Tool 25 data with 990 data
#                        response_data = tool25_service.merge_with_990_data(
#                            base_data=response_data,
#                            tool_25_data=tool25_data,
#                            confidence_threshold=0.7
#                        )
#                        logger.info(f"Tool 25 SUCCESS: {org_name} enhanced with web intelligence")
#                    else:
                        # Graceful degradation - return 990 data only
#                        logger.warning(f"Tool 25 failed for {ein}, using 990 data only")
#                        response_data["enhanced_with_web_data"] = False
#                        response_data["tool_25_error"] = tool25_data.get("tool_25_error", "Unknown error")
#
#                except Exception as web_error:
#                    logger.error(f"Web scraping error for EIN {ein}: {web_error}")
#                    response_data["web_scraping_data"] = {"error": str(web_error)}
#                    response_data["enhanced_with_web_data"] = False
                    # Don't fail the entire request if web scraping fails
#            
            # Always check for stored intelligence data (regardless of web scraping setting)
#            web_scraping_data = response_data.get("web_scraping_data")
#            extracted_info = web_scraping_data.get("extracted_info", {}) if web_scraping_data else {}
#            programs_count = len(extracted_info.get("programs", []))
#            
#            logger.info(f"DEBUG: Checking intelligence conditions for EIN {ein}")
#            logger.info(f"DEBUG: Has web_scraping_data: {web_scraping_data is not None}")
#            logger.info(f"DEBUG: Has extracted_info: {extracted_info is not None}")
#            logger.info(f"DEBUG: Programs count: {programs_count}")
#            
            # REMOVED: Fallback to cached database data to prevent fake data contamination
            # Only use fresh scraping or validated JSON data from now on
#            logger.info(f"Skipping cached database intelligence to avoid fake data for EIN {ein}")
#            
            # CRITICAL: COMPLETELY REMOVE JSON VALIDATION PIPELINE FALLBACKS
            # After MCP removal, the DataValidationPipeline creates poor quality data that overrides VerificationEnhancedScraper
            # We now rely exclusively on VerificationEnhancedScraper for high-quality verified data
#
#            if enable_web_scraping:
#                if response_data.get("web_scraping_data"):
#                    logger.info(f"SUCCESS: Using VerificationEnhancedScraper verified data for EIN {ein}")
#                    logger.info(f"Data sources: Tax filing baseline + web verification")
#                else:
#                    logger.warning(f"VerificationEnhancedScraper failed for EIN {ein} - maintaining no-fake-data policy")
#                    logger.warning(f"Will NOT use any fallback data sources to prevent poor quality data contamination")
#            else:
#                logger.info(f"Web scraping disabled for EIN {ein} - using ProPublica data only")
                # Note: DataValidationPipeline completely removed to prevent poor quality data
#            
            # Check for 990-PF foundation processing
#            try:
                # Auto-detect form type and add foundation intelligence if applicable
#                organization_type = org_data.get('organization_type', '').lower()
#                is_foundation = 'foundation' in organization_type or organization_type == 'private_foundation'
#
#                if is_foundation:
#                    logger.info(f"Detected foundation organization for EIN {ein}, adding foundation intelligence")
#
#                    from src.processors.data_collection.pf_data_extractor import PFDataExtractorProcessor
#
#                    pf_processor = PFDataExtractorProcessor()
#
                    # Process 990-PF specific data
#                    pf_result = await pf_processor.process({
#                        "target_organization": org_data,
#                        "ein": ein,
#                        "organization_name": org_data.get('name', '')
#                    })
#
#                    if pf_result.success and pf_result.data:
#                        foundation_data = pf_result.data
#                        logger.info(f"Successfully extracted 990-PF foundation data for EIN {ein}")
#
                        # Add foundation-specific intelligence to response
#                        response_data["foundation_intelligence"] = {
#                            "grant_making_capacity": foundation_data.get("grant_making_capacity", {}),
#                            "distribution_requirements": foundation_data.get("distribution_requirements", {}),
#                            "grants_paid": foundation_data.get("grants_paid", []),
#                            "application_process": foundation_data.get("application_process", {}),
#                            "form_type": "990-PF",
#                            "is_foundation": True
#                        }
#
                        # Enhance Enhanced Data tab with foundation grant data
#                        if foundation_data.get("grants_paid"):
#                            response_data["foundation_grants"] = foundation_data["grants_paid"][:10]  # Top 10 grants
#                    else:
#                        logger.warning(f"990-PF processing failed for EIN {ein}: {pf_result.error_message}")
#                        response_data["foundation_intelligence"] = {"form_type": "990-PF", "is_foundation": True, "processing_failed": True}
#                else:
#                    logger.info(f"Regular 990 organization detected for EIN {ein}")
#                    response_data["foundation_intelligence"] = {"form_type": "990", "is_foundation": False}
#
#            except Exception as foundation_error:
#                logger.warning(f"Foundation processing error for EIN {ein}: {foundation_error}")
#                response_data["foundation_intelligence"] = {"processing_error": str(foundation_error)}
#
            # Attempt to fetch XML data and extract Schedule I grantees
#            try:
#                from src.utils.xml_fetcher import XMLFetcher
#                from src.utils.schedule_i_extractor import ScheduleIExtractor
#
#                logger.info(f"Attempting to fetch XML data for EIN {ein}")
#
#                xml_fetcher = XMLFetcher(context="profile")
#                xml_content = await xml_fetcher.fetch_xml_by_ein(ein)
#
#                logger.info(f"XML fetch completed for EIN {ein}, content: {xml_content is not None}, size: {len(xml_content) if xml_content else 0}")
#
#                if xml_content:
#                    logger.info(f"Successfully fetched XML data for EIN {ein} ({len(xml_content):,} bytes)")
#
                    # Extract Schedule I grantees
#                    extractor = ScheduleIExtractor()
#                    most_recent_year = org_data.get('most_recent_filing_year')
#                    grantees = extractor.extract_grantees_from_xml(xml_content, most_recent_year)
#                    
#                    if grantees:
#                        logger.info(f"Extracted {len(grantees)} Schedule I grantees for EIN {ein}")
#                        response_data["schedule_i_grantees"] = [grantee.dict() for grantee in grantees]
#                        response_data["schedule_i_status"] = "found"
#                    else:
#                        logger.info(f"No Schedule I grantees found in XML for EIN {ein}")
#                        response_data["schedule_i_status"] = "no_grantees"
#                else:
#                    logger.warning(f"No XML data available for EIN {ein}")
#                    response_data["schedule_i_status"] = "no_xml"
#                    
#            except Exception as e:
#                logger.warning(f"Error fetching/processing XML data for EIN {ein}: {e}")
#                response_data["schedule_i_status"] = "no_xml"
                # Continue with basic data even if XML processing fails
#            
            # NEW: Save extracted data to profile if profile_id provided
#            profile_id = request.get('profile_id')
#            if profile_id:
#                try:
                    # Prepare profile update data with real extracted data only
#                    profile_updates = {}
#
                    # CRITICAL: Prioritize VerificationEnhancedScraper verified data
#                    if verification_result:
#                        logger.info("Saving VerificationEnhancedScraper verified data to database")
#
                        # Save verified website URL (highest confidence)
#                        if verification_result.verified_website:
#                            profile_updates["website_url"] = verification_result.verified_website
#                            profile_updates["website"] = verification_result.verified_website  # Legacy compatibility
#                            logger.info(f"Saving verified website: {verification_result.verified_website}")
#
                        # Save verified mission statement (highest confidence)
#                        if verification_result.verified_mission and len(verification_result.verified_mission.strip()) > 10:
#                            profile_updates["mission_statement"] = verification_result.verified_mission
#                            logger.info(f"Saving verified mission: {verification_result.verified_mission[:50]}...")
#
                        # Save verification metadata for quality tracking
#                        profile_updates["verification_data"] = {
#                            "verification_confidence": verification_result.verification_confidence,
#                            "verified_leadership_count": len(verification_result.verified_leadership),
#                            "data_sources": verification_result.source_attribution,
#                            "last_verified": datetime.now().isoformat(),
#                            "tax_baseline_available": verification_result.tax_baseline is not None
#                        }
#
                        # Map verified leadership to board_members field for database consistency
#                        if verification_result.verified_leadership:
#                            board_members_list = []
#                            for leader in verification_result.verified_leadership:
#                                if hasattr(leader, 'name') and leader.name:
#                                    member_entry = leader.name
#                                    if hasattr(leader, 'title') and leader.title:
#                                        member_entry += f" - {leader.title}"
#                                    board_members_list.append(member_entry)
#                                elif hasattr(leader, 'content') and leader.content:
#                                    board_members_list.append(leader.content)
#
#                            if board_members_list:
#                                profile_updates["board_members"] = board_members_list
#                                logger.info(f"Saving {len(board_members_list)} verified leadership entries to board_members field")
#
                    # Fallback: Only update fields that have real data (legacy support)
#                    elif response_data.get("mission_statement") and len(response_data["mission_statement"].strip()) > 10:
#                        profile_updates["mission_statement"] = response_data["mission_statement"]
#
                    # Fallback: Use verified website URL from XML + web verification (takes priority)
#                    elif response_data.get("website_url"):
#                        profile_updates["website_url"] = response_data["website_url"]
#
                    # Fallback: Map leadership/officers data to board_members if no verification result
#                    if not verification_result and extracted_info:
#                        board_members_list = []
#
                        # Process leadership data
#                        leadership_data = extracted_info.get('leadership', [])
#                        officers_data = extracted_info.get('officers', [])
#
                        # Combine leadership and officers data, removing duplicates
#                        all_leadership = leadership_data + officers_data
#                        seen_names = set()
#
#                        for leader in all_leadership:
#                            leader_text = ""
#                            if isinstance(leader, dict):
#                                if leader.get('name'):
#                                    leader_text = leader['name']
#                                    if leader.get('title'):
#                                        leader_text += f" - {leader['title']}"
#                                elif leader.get('content'):
#                                    leader_text = leader['content']
#                            else:
#                                leader_text = str(leader).strip()
#
                            # Only add if non-empty and not duplicate
#                            if leader_text and len(leader_text) > 3 and leader_text not in seen_names:
#                                seen_names.add(leader_text)
#                                board_members_list.append(leader_text)
#
#                        if board_members_list:
#                            profile_updates["board_members"] = board_members_list[:10]  # Limit to 10 entries
#                            logger.info(f"Fallback: Saving {len(board_members_list)} leadership/officers entries to board_members field")
#
                    # Add keywords from scraped programs if available
#                    if response_data.get("programs") and len(response_data["programs"]) > 0:
                        # Extract meaningful keywords from programs (real data only)
#                        program_keywords = []
#                        for program in response_data["programs"][:3]:  # Top 3 programs
#                            if isinstance(program, dict):
#                                program_text = program.get("content", "")
#                            else:
#                                program_text = str(program)
#
#                            if program_text and len(program_text.strip()) > 5:
                                # Extract key terms from program descriptions
#                                words = program_text.replace(',', ' ').replace('.', ' ').split()
#                                keywords = [w.lower() for w in words if len(w) > 3 and w.isalpha()][:3]
#                                program_keywords.extend(keywords)
#
#                        if program_keywords:
#                            profile_updates["keywords"] = ", ".join(program_keywords[:10])  # Top 10 keywords
#
                    # Save web scraping results for Enhanced Data tab
#                    if response_data.get("web_scraping_data"):
                        # Store structured web scraping data (real data only)
#                        profile_updates["web_enhanced_data"] = {
#                            "scraped_data": response_data["web_scraping_data"],
#                            "enhanced_with_web_data": response_data["enhanced_with_web_data"],
#                            "last_scraped": datetime.now().isoformat()
#                        }
#
                        # CRITICAL: Also save VerificationEnhancedScraper verified leadership for Enhanced Data tab
#                        if verification_result and verification_result.verified_leadership:
#                            verified_leadership_data = []
#                            for leader in verification_result.verified_leadership:
#                                if hasattr(leader, 'name') and leader.name:
#                                    verified_leadership_data.append({
#                                        "name": leader.name,
#                                        "title": getattr(leader, 'title', ''),
#                                        "source": leader.source,
#                                        "confidence": getattr(leader, 'confidence_score', 0.8),
#                                        "verification_status": getattr(leader, 'verification_status', 'verified')
#                                    })
#
                            # Add verified leadership to web_enhanced_data for Enhanced Data tab
#                            profile_updates["web_enhanced_data"]["verified_leadership"] = verified_leadership_data
#                            logger.info(f"Saving {len(verified_leadership_data)} verified leadership entries to database")
#
                    # Only update if we have real data to save
#                    if profile_updates:
                        # Save to database (not file-based profile_service) for persistence
                        # Get existing profile, update it, then save back
#                        existing_profile = database_service.get_profile(profile_id)
#                        if existing_profile:
                            # Update the profile object with the new data
#                            for key, value in profile_updates.items():
#                                if hasattr(existing_profile, key):
#                                    setattr(existing_profile, key, value)
#                                else:
#                                    logger.debug(f"Profile doesn't have attribute '{key}', skipping")
#
                            # Update the updated_at timestamp
#                            existing_profile.updated_at = datetime.now()
#
                            # Save the updated profile
#                            success = database_service.update_profile(existing_profile)
#                            if success:
#                                logger.info(f"Saved fetched data to database for profile {profile_id}: {list(profile_updates.keys())}")
#                            else:
#                                logger.error(f"Failed to save profile updates to database for {profile_id}")
#                        else:
#                            logger.error(f"Could not find existing profile {profile_id} for update")
#                    else:
#                        logger.info(f"No real data to save for profile {profile_id}")
#
#                except Exception as save_error:
#                    logger.error(f"Failed to save fetched data to profile {profile_id}: {save_error}")
                    # Continue with response even if save fails
#
            # ENHANCED DATABASE FALLBACK: Compare data quality and preserve better data
            # This prevents partial/incomplete fetch results from overwriting complete database data
#            profile_id = request.get('profile_id')
#            if profile_id:
#                try:
#                    existing_profile = database_service.get_profile(profile_id)
#                    if existing_profile:
#
#                        def data_quality_score(data_dict, field_name):
#                            """Calculate data quality score for a field (0-100)"""
#                            value = data_dict.get(field_name, "")
#                            if not value or str(value).strip() == "":
#                                return 0
                            # Base score on length and content quality
#                            score = min(len(str(value)), 100)
                            # Bonus for meaningful content
#                            if len(str(value)) > 20:
#                                score += 20
#                            if any(keyword in str(value).lower() for keyword in ['provide', 'assist', 'support', 'mission', 'purpose']):
#                                score += 10
#                            return min(score, 100)
#
                        # Critical fields to compare
#                        critical_fields = {
#                            'mission_statement': 'mission_statement',
#                            'website_url': 'website_url',
#                            'website': 'website_url',  # Both map to same DB field
                            # Note: location and annual_revenue don't exist on profile model, they come from form data
#                        }
#
#                        restored_fields = []
#
                        # Compare each critical field
#                        for response_field, db_field in critical_fields.items():
#                            if response_field == 'website':  # Skip duplicate mapping
#                                continue
#
                            # Get values
#                            new_value = response_data.get(response_field, "")
#                            db_value = getattr(existing_profile, db_field, "")
#
                            # Calculate quality scores
#                            new_score = data_quality_score(response_data, response_field)
#                            db_score = data_quality_score({db_field: db_value}, db_field)
#
#                            logger.info(f"Quality comparison for {response_field}: new_score={new_score}, db_score={db_score}")
#                            logger.info(f"Values: new='{str(new_value)[:50]}...' db='{str(db_value)[:50]}...'")
#
                            # If database data is significantly better, restore it
#                            if db_score > new_score + 10:  # 10-point threshold to avoid unnecessary replacements
#                                response_data[response_field] = db_value
#                                if response_field == 'website_url':
#                                    response_data['website'] = db_value  # Keep both fields in sync
#                                restored_fields.append(f"{response_field}(score: {db_score} > {new_score})")
#                                logger.warning(f"RESTORED {response_field} from database: DB data quality ({db_score}) > fetch data ({new_score})")
#
                        # Log comprehensive restoration summary
#                        if restored_fields:
#                            logger.critical(f"DATA QUALITY PROTECTION: Restored {len(restored_fields)} fields from database for profile {profile_id}: {restored_fields}")
#                        else:
#                            logger.info(f"DATA QUALITY CHECK: All fetched data quality is acceptable for profile {profile_id}")
#
#                except Exception as db_fallback_error:
#                    logger.error(f"Enhanced database fallback failed for profile {profile_id}: {db_fallback_error}")
#
#            return {
#                "success": True,
#                "data": response_data,
#                "enhanced_features": {
#                    "web_scraping_enabled": enable_web_scraping,
#                    "web_data_available": response_data["enhanced_with_web_data"],
#                    "data_sources": [
#                        "ProPublica API",
#                        "IRS XML Filings",
#                        "Web Scraping" if response_data["enhanced_with_web_data"] else "Web Scraping (Failed)"
#                    ]
#                }
#            }
#        else:
#            return {
#                "success": False,
#                "message": "Organization not found or API error",
#                "error": result.error_message if hasattr(result, 'error_message') else "Unknown error"
#            }
#
#    except Exception as e:
#        logger.error(f"EIN fetch error: {str(e)}")
#        raise HTTPException(status_code=500, detail=f"Failed to fetch EIN data: {str(e)}")

# OLD PROFILES ENDPOINT REMOVED - Using database direct endpoint instead

# Duplicate POST /api/profiles moved to profiles router
# Duplicate GET /api/profiles/{profile_id} moved to profiles router
# Duplicate PUT /api/profiles/{profile_id} moved to profiles router
# Duplicate DELETE /api/profiles/{profile_id} moved to profiles router

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
        logger.error(f"Failed to delete profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Duplicate POST /api/profiles/templates moved to profiles router

# Duplicate GET /api/profiles/{profile_id}/analytics moved to profiles router

# REMOVED: /api/profiles/{ein}/json-intelligence endpoint
# This endpoint was causing poor quality DataValidationPipeline data to override VerificationEnhancedScraper results
# After MCP removal, we use only the main /api/profiles/fetch-ein endpoint with VerificationEnhancedScraper for verified data
# Removing this eliminates the competing data pipeline that was returning "source": "Scrapy" garbage data

@app.get("/api/profiles/{ein}/web-intelligence")
async def get_web_intelligence(ein: str):
    """Get web intelligence data for Enhanced Data tab."""
    try:
        import sqlite3
        import json
        
        with sqlite3.connect("data/catalynx.db") as conn:
            cursor = conn.execute("""
                SELECT ein, url, scrape_date, intelligence_quality_score,
                       leadership_data, leadership_count, program_data, program_count,
                       contact_data, mission_statements, pages_scraped, total_content_length
                FROM web_intelligence 
                WHERE ein = ? 
                ORDER BY scrape_date DESC 
                LIMIT 1
            """, (ein,))
            
            result = cursor.fetchone()
            
            if not result:
                return {
                    "success": False,
                    "message": f"No web intelligence data found for EIN {ein}",
                    "data": None
                }
            
            # Parse the database result
            (db_ein, url, scrape_date, quality_score, leadership_json, leadership_count, 
             program_json, program_count, contact_json, mission_json, pages_scraped, content_length) = result
            
            # Parse JSON fields safely
            try:
                leadership_data = json.loads(leadership_json) if leadership_json else []
                program_data = json.loads(program_json) if program_json else []
                contact_data = json.loads(contact_json) if contact_json else []
                mission_data = json.loads(mission_json) if mission_json else []
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error for EIN {ein}: {e}")
                leadership_data, program_data, contact_data, mission_data = [], [], [], []
            
            # Format response for Enhanced Tab
            web_intelligence = {
                "successful_scrapes": [{
                    "url": url,
                    "content_length": content_length or 0,
                    "content_score": quality_score / 100.0 if quality_score else 0,
                    "timestamp": scrape_date
                }],
                "failed_scrapes": [],
                "extracted_info": {
                    "programs": [p.get('name', str(p)) if isinstance(p, dict) else str(p) for p in program_data],
                    "leadership": [f"{l.get('name', '')} - {l.get('title', '')}" if isinstance(l, dict) else str(l) for l in leadership_data],
                    "mission_statements": mission_data,
                    "contact_info": [str(c) for c in contact_data],
                    "financial_info": []
                },
                "intelligence_quality_score": quality_score or 0,
                "data_source": "database",
                "pages_scraped": pages_scraped or 0
            }
            
            return {
                "success": True,
                "data": {
                    "web_scraping_data": web_intelligence
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to get web intelligence for EIN {ein}: {e}")
        return {
            "success": False,
            "message": f"Error retrieving web intelligence: {str(e)}",
            "data": None
        }

@app.get("/api/profiles/{profile_id}/verified-intelligence")
async def get_verified_intelligence(profile_id: str):
    """Get verified intelligence data using tax-data-first approach for Enhanced Data tab."""
    try:
        # Use database manager to get profile data directly
        database_service = DatabaseManager()
        db_profile = database_service.get_profile(profile_id)

        if not db_profile:
            return {
                "success": False,
                "message": f"Profile not found in database: {profile_id}",
                "data": None
            }

        # Extract organization details from database profile
        organization_name = db_profile.name
        ein = getattr(db_profile, 'ein', None)
        user_provided_url = getattr(db_profile, 'website_url', None)

        logger.info(f"Getting verified intelligence for {organization_name} (EIN: {ein})")

        # Extract saved enhanced data from profile
        web_enhanced_data = getattr(db_profile, 'web_enhanced_data', {}) or {}
        verification_data = getattr(db_profile, 'verification_data', {}) or {}

        logger.info(f"Found enhanced data for {organization_name}: web_enhanced_data={bool(web_enhanced_data)}, verification_data={bool(verification_data)}")

        # Extract leadership from saved data
        leadership_list = []
        if web_enhanced_data.get('verified_leadership'):
            leadership_list = [
                f"{leader.get('name', 'Unknown')} - {leader.get('title', 'Unknown Title')} (Tax Filing, {leader.get('confidence_score', 0.9):.1%} confidence)"
                for leader in web_enhanced_data['verified_leadership']
                if leader.get('name')
            ]
        elif web_enhanced_data.get('leadership'):
            leadership_list = web_enhanced_data['leadership']

        # Extract programs from saved data
        programs_list = web_enhanced_data.get('programs', [])

        # Extract mission from profile
        mission_statements = []
        if hasattr(db_profile, 'mission_statement') and db_profile.mission_statement:
            mission_statements = [db_profile.mission_statement]

        # Get website from profile
        profile_website = getattr(db_profile, 'website_url', None) or getattr(db_profile, 'website', None)

        # Format response compatible with Enhanced Data tab
        web_intelligence = {
            "successful_scrapes": [
                {
                    "url": profile_website or "No website available",
                    "content_length": len(str(web_enhanced_data)),
                    "content_score": verification_data.get('confidence_score', 0.8),
                    "timestamp": verification_data.get('fetched_at', datetime.now().isoformat())
                }
            ] if profile_website else [],
            "failed_scrapes": [],
            "extracted_info": {
                "leadership": leadership_list,
                "programs": programs_list,
                "mission_statements": mission_statements,
                "contact_info": [],
                "financial_info": []
            },
            "intelligence_quality_score": verification_data.get('confidence_score', 0.8),
            "data_source": "verified_tax_data_first",
            "pages_scraped": 1 if profile_website else 0,
            "verification_details": {
                "overall_confidence": verification_data.get('confidence_score', 0.8),
                "has_990_baseline": bool(verification_data.get('has_990_baseline', True)),
                "source_attribution": verification_data.get('source_attribution', 'Tax Filing + Web Verification'),
                "data_sources_used": verification_data.get('data_sources_used', ['Tax Filing', 'Web Scraping']),
                "verification_notes": verification_data.get('verification_notes', 'Data verified using tax-data-first approach'),
                "processing_time": verification_data.get('processing_time', 'N/A')
            }
        }

        # Create mock verified_intelligence object for compatibility
        verified_intelligence_compat = {
            "verified_website": profile_website,
            "verified_mission": mission_statements[0] if mission_statements else None,
            "verified_leadership": web_enhanced_data.get('verified_leadership', []),
            "verified_programs": programs_list,
            "overall_confidence": verification_data.get('confidence_score', 0.8),
            "data_quality_score": verification_data.get('confidence_score', 0.8),
            "intelligence_quality_score": verification_data.get('confidence_score', 0.8),
            "has_enhanced_data": bool(web_enhanced_data or verification_data),
            "fetched_at": verification_data.get('fetched_at', datetime.now().isoformat())
        }

        return {
            "success": True,
            "data": {
                "web_scraping_data": web_intelligence,
                "verified_intelligence": verified_intelligence_compat
            }
        }

    except Exception as e:
        logger.error(f"Failed to get verified intelligence for profile {profile_id}: {e}")
        return {
            "success": False,
            "message": f"Error retrieving verified intelligence: {str(e)}",
            "data": None
        }

@app.get("/api/profiles/{profile_id}/enhanced-intelligence")
async def get_enhanced_intelligence(profile_id: str):
    """Alias for verified intelligence - maintains compatibility with frontend calls."""
    return await get_verified_intelligence(profile_id)

# Duplicate GET /api/profiles/{profile_id}/metrics moved to profiles router
# Duplicate GET /api/profiles/metrics/summary moved to profiles router

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
        logger.error(f"Failed to update funnel metrics for profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

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
        logger.error(f"Failed to start metrics session for profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Duplicate GET /api/profiles/{profile_id}/plan-results moved to profiles router

# Duplicate POST /api/profiles/{profile_id}/plan-results moved to profiles router

# Duplicate POST /api/profiles/{profile_id}/opportunity-scores moved to profiles router

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
        logger.error(f"Failed to generate scoring rationale for {opportunity_id} in profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

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
        logger.error(f"Failed to get leads for profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

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


# Duplicate GET /api/profiles/{profile_id}/opportunities moved to profiles router

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



def main(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Entry point for the ``catalynx`` console script (pyproject.toml)."""
    logger.info("Starting Catalynx Web Interface on http://%s:%s", host, port)
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()

