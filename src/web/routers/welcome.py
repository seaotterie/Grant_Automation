#!/usr/bin/env python3
"""
Welcome Router
Handles welcome status, sample profile creation, and quick-start demo endpoints.
Extracted from monolithic main.py for better modularity.
"""

from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime

from src.core.tool_registry import get_tool_summary
from src.profiles.unified_service import get_unified_profile_service

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/api/welcome", tags=["Welcome"])

# Service instances (lazy init)
_profile_service = None


def _get_profile_service():
    global _profile_service
    if _profile_service is None:
        _profile_service = get_unified_profile_service()
    return _profile_service


@router.get("/status")
async def get_welcome_status():
    """Get welcome stage status and system overview."""
    try:
        tool_summary = get_tool_summary()

        return {
            "status": "ready",
            "system_health": "operational",
            "processors_available": tool_summary["operational_tools"],
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


@router.post("/sample-profile")
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

        profile_service = _get_profile_service()
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
        logger.error(f"Failed to create sample profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/quick-start")
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
        logger.error(f"Quick start demo failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
