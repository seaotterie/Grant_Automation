"""
Deprecation Middleware - Phase 9 API Consolidation

Automatically adds deprecation headers to legacy endpoints,
guiding API consumers to modern V2/tool-based alternatives.
"""

from fastapi import Request, Response
from typing import Dict, Any
import logging
from collections import Counter
from datetime import datetime

logger = logging.getLogger(__name__)

# Track usage of deprecated endpoints
deprecated_usage = Counter()

# Deprecation mappings - Phase 1: AI & Analysis Endpoints
DEPRECATED_ENDPOINTS: Dict[str, Dict[str, Any]] = {
    # AI Analysis Endpoints → Tool Execution API
    "/api/ai/lite-analysis": {
        "replacement": "/api/v1/tools/opportunity-screening-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1,
        "migration_notes": "Use mode='fast' for lite analysis"
    },
    "/api/ai/heavy-light/analyze": {
        "replacement": "/api/v1/tools/opportunity-screening-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1,
        "migration_notes": "Use mode='thorough' for heavy-light analysis"
    },
    "/api/ai/heavy-1/research-bridge": {
        "replacement": "/api/v1/tools/deep-intelligence-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1,
        "migration_notes": "Use depth='standard' for research bridge"
    },
    "/api/ai/deep-research": {
        "replacement": "/api/v1/tools/deep-intelligence-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1,
        "migration_notes": "Use depth='complete' for deep research"
    },
    "/api/ai/lite-1/validate": {
        "replacement": "/api/v1/tools/opportunity-screening-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/ai/lite-2/strategic-score": {
        "replacement": "/api/v1/tools/opportunity-screening-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/ai/batch-analysis": {
        "replacement": "/api/v1/workflows/screen-opportunities",
        "sunset_date": "2025-11-15",
        "phase": 1,
        "migration_notes": "Use workflow API for batch processing"
    },
    "/api/ai/orchestrated-pipeline": {
        "replacement": "/api/v1/workflows/deep-intelligence",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/ai/analysis-status/{request_id}": {
        "replacement": "/api/v1/workflows/status/{execution_id}",
        "sunset_date": "2025-11-15",
        "phase": 1
    },

    # Research Endpoints → Tool Execution API
    "/api/research/ai-lite/analyze": {
        "replacement": "/api/v1/tools/opportunity-screening-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/research/capabilities": {
        "replacement": "/api/v1/tools",
        "sunset_date": "2025-11-15",
        "phase": 1,
        "migration_notes": "Use GET /api/v1/tools to list all tool capabilities"
    },
    "/api/research/status/{profile_id}": {
        "replacement": "/api/v1/workflows/status/{execution_id}",
        "sunset_date": "2025-11-15",
        "phase": 1
    },

    # Profile-scoped AI Endpoints → Tool Execution API
    "/api/profiles/{id}/analyze/ai-lite": {
        "replacement": "/api/v1/tools/opportunity-screening-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/profiles/{id}/research/analyze-integrated": {
        "replacement": "/api/v1/tools/deep-intelligence-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/profiles/{id}/research/batch-analyze": {
        "replacement": "/api/v1/workflows/screen-opportunities",
        "sunset_date": "2025-11-15",
        "phase": 1
    },

    # Classification Endpoints → Workflow API
    "/api/classification/start": {
        "replacement": "/api/v1/workflows/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/classification/{workflow_id}/results": {
        "replacement": "/api/v1/workflows/results/{execution_id}",
        "sunset_date": "2025-11-15",
        "phase": 1
    },

    # Scoring Endpoints → Tool Execution API
    "/api/analysis/scoring": {
        "replacement": "/api/v1/tools/multi-dimensional-scorer-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/analysis/enhanced-scoring": {
        "replacement": "/api/v1/tools/multi-dimensional-scorer-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/scoring/government": {
        "replacement": "/api/v1/tools/multi-dimensional-scorer-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/scoring/financial": {
        "replacement": "/api/v1/tools/financial-intelligence-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/scoring/network": {
        "replacement": "/api/v1/tools/network-intelligence-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/scoring/ai-lite": {
        "replacement": "/api/v1/tools/opportunity-screening-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/scoring/comprehensive": {
        "replacement": "/api/v1/tools/multi-dimensional-scorer-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/analysis/network": {
        "replacement": "/api/v1/tools/network-intelligence-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/profiles/{id}/opportunity-scores": {
        "replacement": "/api/v2/profiles/{id}/opportunities/score",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/profiles/{id}/opportunities/{opp_id}/score": {
        "replacement": "/api/v2/profiles/{id}/opportunities/score",
        "sunset_date": "2025-11-15",
        "phase": 1
    },

    # Export & Reporting Endpoints → Tool Execution API
    "/api/export/opportunities": {
        "replacement": "/api/v1/tools/data-export-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/analysis/export": {
        "replacement": "/api/v1/tools/data-export-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/analysis/reports": {
        "replacement": "/api/v1/tools/report-generator-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
    "/api/dossier/{dossier_id}/generate-document": {
        "replacement": "/api/v1/tools/report-generator-tool/execute",
        "sunset_date": "2025-11-15",
        "phase": 1
    },
}


async def add_deprecation_headers(request: Request, call_next) -> Response:
    """
    Middleware to add deprecation headers to legacy endpoints.

    Adds the following headers to deprecated endpoints:
    - X-Deprecated: true
    - X-Replacement-Endpoint: New endpoint path
    - X-Migration-Guide: Link to migration documentation
    - Sunset: RFC 8594 sunset date
    - X-Deprecation-Phase: Migration phase number
    - X-Migration-Notes: Additional migration guidance
    """
    # Execute the request
    response = await call_next(request)

    # Check if endpoint is deprecated
    endpoint_path = request.url.path

    # Try exact match first
    if endpoint_path in DEPRECATED_ENDPOINTS:
        info = DEPRECATED_ENDPOINTS[endpoint_path]
        _add_headers(response, endpoint_path, info)
    else:
        # Try pattern matching for parameterized endpoints
        for pattern, info in DEPRECATED_ENDPOINTS.items():
            if _matches_pattern(endpoint_path, pattern):
                _add_headers(response, endpoint_path, info)
                break

    return response


def _matches_pattern(path: str, pattern: str) -> bool:
    """
    Check if path matches pattern with parameters.

    Example: /api/profiles/123/analyze matches /api/profiles/{id}/analyze
    """
    path_parts = path.split('/')
    pattern_parts = pattern.split('/')

    if len(path_parts) != len(pattern_parts):
        return False

    for path_part, pattern_part in zip(path_parts, pattern_parts):
        # If pattern part is a parameter (contains {})
        if '{' in pattern_part and '}' in pattern_part:
            continue  # Parameter matches anything
        # Otherwise must match exactly
        if path_part != pattern_part:
            return False

    return True


def _add_headers(response: Response, endpoint_path: str, info: Dict[str, Any]) -> None:
    """Add deprecation headers to response."""
    response.headers["X-Deprecated"] = "true"
    response.headers["X-Replacement-Endpoint"] = info["replacement"]
    response.headers["Sunset"] = info["sunset_date"]
    response.headers["X-Migration-Guide"] = "https://docs.catalynx.com/api/migration"
    response.headers["X-Deprecation-Phase"] = str(info.get("phase", 1))

    if "migration_notes" in info:
        response.headers["X-Migration-Notes"] = info["migration_notes"]

    # Track usage
    deprecated_usage[endpoint_path] += 1

    # Log warning
    logger.warning(
        f"Deprecated endpoint accessed: {endpoint_path} "
        f"(usage count: {deprecated_usage[endpoint_path]}, "
        f"replacement: {info['replacement']})"
    )


async def track_deprecated_usage(request: Request, call_next) -> Response:
    """
    Track usage of deprecated endpoints for monitoring.

    This middleware tracks all deprecated endpoint usage and logs
    warnings to help monitor migration progress.
    """
    endpoint_path = request.url.path

    # Check if endpoint is deprecated
    if endpoint_path in DEPRECATED_ENDPOINTS or any(
        _matches_pattern(endpoint_path, pattern)
        for pattern in DEPRECATED_ENDPOINTS.keys()
    ):
        # Increment usage counter
        deprecated_usage[endpoint_path] += 1

        # Log warning with details
        logger.warning(
            f"Deprecated endpoint accessed: {endpoint_path} | "
            f"Method: {request.method} | "
            f"User-Agent: {request.headers.get('user-agent', 'unknown')} | "
            f"Usage count: {deprecated_usage[endpoint_path]} | "
            f"Timestamp: {datetime.utcnow().isoformat()}"
        )

    return await call_next(request)


def get_deprecation_stats() -> Dict[str, Any]:
    """
    Get deprecation usage statistics.

    Returns:
        Dictionary with usage statistics including:
        - total_calls: Total number of deprecated endpoint calls
        - by_endpoint: Usage count by endpoint
        - by_phase: Usage count by migration phase
        - top_10: Top 10 most-used deprecated endpoints
    """
    # Calculate stats by phase
    by_phase = {}
    for endpoint, count in deprecated_usage.items():
        # Find endpoint info
        info = DEPRECATED_ENDPOINTS.get(endpoint)
        if info:
            phase = info.get("phase", 1)
            by_phase[phase] = by_phase.get(phase, 0) + count

    return {
        "total_calls": sum(deprecated_usage.values()),
        "unique_endpoints_used": len(deprecated_usage),
        "total_deprecated_endpoints": len(DEPRECATED_ENDPOINTS),
        "by_endpoint": dict(deprecated_usage),
        "by_phase": by_phase,
        "top_10": dict(deprecated_usage.most_common(10)),
        "last_updated": datetime.utcnow().isoformat()
    }


def reset_deprecation_stats() -> None:
    """Reset deprecation usage statistics."""
    deprecated_usage.clear()
    logger.info("Deprecation usage statistics reset")
