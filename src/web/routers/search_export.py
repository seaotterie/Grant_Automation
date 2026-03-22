"""
Search & Export Router
API endpoints for advanced opportunity search, export, and classification/workflow exports.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from typing import Dict, Optional, Any
from datetime import datetime
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Search & Export"])


# === ADVANCED SEARCH & EXPORT ENDPOINTS ===

@router.post("/search/opportunities")
async def search_opportunities(
    search_request: Dict[str, Any],
    profile_id: Optional[str] = None
):
    """Advanced search across opportunities with flexible filtering"""
    try:
        from src.web.services.search_export_service import (
            get_search_export_service, SearchCriteria, SearchFilter, SearchOperator,
            SortDirection
        )

        search_service = get_search_export_service()

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
        logger.error(f"Failed to search opportunities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/fields")
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


@router.post("/export/opportunities")
async def export_opportunities(
    export_request: Dict[str, Any]
):
    """Export opportunities with advanced filtering and format options"""
    try:
        from src.web.services.search_export_service import (
            get_search_export_service, SearchCriteria, SearchFilter, SearchOperator,
            SortDirection, ExportFormat
        )

        search_service = get_search_export_service()

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export opportunities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/stats")
async def get_search_stats():
    """Get search and export statistics"""
    try:
        from src.profiles.unified_service import get_unified_profile_service

        unified_service = get_unified_profile_service()
        profile_service = unified_service

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
        logger.error(f"Failed to get search stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# === CLASSIFICATION & WORKFLOW EXPORT ENDPOINTS ===

@router.get("/exports/classification/{workflow_id}")
async def export_classification(workflow_id: str, format: str = "csv"):
    """Export classification results."""
    try:
        from src.web.services.workflow_service import WorkflowService
        workflow_service = WorkflowService()

        file_path = await workflow_service.export_classification_results(workflow_id, format)
        return FileResponse(
            path=file_path,
            filename=f"classification_{workflow_id}.{format}",
            media_type="application/octet-stream"
        )
    except Exception as e:
        logger.error(f"Failed to export classification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/exports/workflow/{workflow_id}")
async def export_workflow(workflow_id: str, format: str = "csv"):
    """Export workflow results."""
    try:
        from src.web.services.workflow_service import WorkflowService
        workflow_service = WorkflowService()

        file_path = await workflow_service.export_workflow_results(workflow_id, format)
        return FileResponse(
            path=file_path,
            filename=f"workflow_{workflow_id}.{format}",
            media_type="application/octet-stream"
        )
    except Exception as e:
        logger.error(f"Failed to export workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
