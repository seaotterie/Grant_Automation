#!/usr/bin/env python3
"""
Dashboard Router
Handles dashboard overview, system status, and health check endpoints
Extracted from monolithic main.py for better modularity
"""

from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime
from typing import Dict, Any

from src.core.workflow_engine import get_workflow_engine  
from src.web.models.responses import DashboardStats, SystemStatus

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/overview")
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


@router.get("/system/status")
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


@router.get("/system/health")
async def system_health() -> Dict[str, Any]:
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


@router.get("/metrics")
async def system_metrics() -> Dict[str, Any]:
    """Get system performance metrics."""
    try:
        # This endpoint might be referenced in the main file
        # Adding basic implementation for completeness
        engine = get_workflow_engine()
        processors = engine.registry.list_processors()
        
        return {
            "processors": {
                "total": len(processors),
                "active": len(processors),  # All processors considered active for now
                "failed": 0
            },
            "performance": {
                "avg_response_time": 0.1,  # Placeholder metrics
                "requests_per_second": 10,
                "cache_hit_rate": 85.0
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/processors")
async def system_processors() -> Dict[str, Any]:
    """Get information about available processors."""
    try:
        engine = get_workflow_engine()
        processors = engine.registry.list_processors()
        
        processor_info = []
        for processor_name in processors:
            try:
                processor_meta = engine.registry.get_processor_info(processor_name)
                if processor_meta:
                    processor_info.append({
                        "name": processor_name,
                        "description": processor_meta.get("description", ""),
                        "version": processor_meta.get("version", "1.0.0"),
                        "status": "available"
                    })
                else:
                    processor_info.append({
                        "name": processor_name,
                        "description": "No description available",
                        "version": "unknown",
                        "status": "available"
                    })
            except Exception as e:
                logger.warning(f"Failed to get info for processor {processor_name}: {e}")
                processor_info.append({
                    "name": processor_name,
                    "description": "Error retrieving info",
                    "version": "unknown", 
                    "status": "error"
                })
        
        return {
            "total_processors": len(processors),
            "processors": processor_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get processor information: {e}")
        raise HTTPException(status_code=500, detail=str(e))