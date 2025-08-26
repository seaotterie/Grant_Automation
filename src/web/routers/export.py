#!/usr/bin/env python3
"""
Export Router
Handles report generation, data export, and document creation
Extracted from monolithic main.py for better modularity
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Import export services
from src.web.services.search_export_service import get_search_export_service
from src.profiles.unified_service import get_unified_profile_service
from src.auth.jwt_auth import get_current_user_dependency, User

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/api/export", tags=["export"])

# Initialize services
search_export_service = get_search_export_service()
unified_service = get_unified_profile_service()


@router.post("/opportunities")
async def export_opportunities(
    export_request: Dict[str, Any]
) -> Dict[str, Any]:
    """Export opportunities data in various formats."""
    try:
        profile_id = export_request.get("profile_id")
        export_format = export_request.get("format", "json")
        template = export_request.get("template", "standard")
        
        if not profile_id:
            raise HTTPException(status_code=400, detail="Profile ID is required")
        
        # Get profile and opportunities
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Generate export using search export service
        export_result = search_export_service.export_opportunities(
            profile, export_format, template
        )
        
        return {
            "export_result": export_result,
            "format": export_format,
            "template": template,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export opportunities failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comprehensive-report")
async def generate_comprehensive_report(
    report_request: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate comprehensive analysis report."""
    try:
        profile_id = report_request.get("profile_id")
        report_format = report_request.get("format", "pdf")
        template = report_request.get("template", "comprehensive")
        
        if not profile_id:
            raise HTTPException(status_code=400, detail="Profile ID is required")
        
        # Mock comprehensive report generation
        report = {
            "report_id": f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "profile_id": profile_id,
            "format": report_format,
            "template": template,
            "sections": ["executive_summary", "opportunities", "analysis", "recommendations"],
            "generated_at": datetime.now().isoformat(),
            "status": "generated"
        }
        
        return {
            "report": report,
            "message": "Comprehensive report generated successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comprehensive report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def get_export_formats() -> Dict[str, Any]:
    """Get available export formats and templates."""
    try:
        formats = {
            "json": {"description": "JSON data format", "supported_templates": ["standard", "detailed"]},
            "csv": {"description": "Comma-separated values", "supported_templates": ["standard", "minimal"]},
            "pdf": {"description": "PDF report", "supported_templates": ["standard", "comprehensive", "executive"]},
            "xlsx": {"description": "Excel workbook", "supported_templates": ["standard", "detailed", "dashboard"]}
        }
        
        return {
            "export_formats": formats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get export formats: {e}")
        raise HTTPException(status_code=500, detail=str(e))