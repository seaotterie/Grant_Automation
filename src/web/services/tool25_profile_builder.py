"""
Tool 25 Profile Builder Integration
Provides clean integration between FastAPI endpoints and Tool 25 Web Intelligence Tool

This module:
- Handles Smart URL Resolution (User → 990 → GPT priority)
- Executes Tool 25 Profile Builder use case
- Auto-populates profile fields from intelligence data
- Provides graceful degradation on failures
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Add tools directory to path
tools_dir = Path(__file__).parent.parent.parent.parent / "tools" / "web-intelligence-tool"
sys.path.insert(0, str(tools_dir))

from app.web_intelligence_tool import (
    WebIntelligenceTool,
    WebIntelligenceRequest,
    WebIntelligenceResponse,
    UseCase
)

logger = logging.getLogger(__name__)


class Tool25ProfileBuilder:
    """
    Tool 25 Profile Builder service for profile creation workflow.

    Replaces legacy VerificationEnhancedScraper with 12-factor compliant
    Scrapy-powered web intelligence tool.
    """

    def __init__(self):
        """Initialize Tool 25"""
        self.tool = WebIntelligenceTool()

    async def execute_profile_builder(
        self,
        ein: str,
        organization_name: str,
        user_provided_url: Optional[str] = None,
        filing_url: Optional[str] = None,
        gpt_predicted_url: Optional[str] = None,
        require_990_verification: bool = True,
        min_confidence_score: float = 0.7
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute Tool 25 Profile Builder with Smart URL Resolution.

        Args:
            ein: Organization EIN
            organization_name: Organization name
            user_provided_url: User-supplied URL (highest priority)
            filing_url: URL from 990 tax filing (second priority)
            gpt_predicted_url: GPT-predicted URL (fallback)
            require_990_verification: Require 990 verification pipeline
            min_confidence_score: Minimum confidence to accept data

        Returns:
            (success: bool, data: dict)
        """
        try:
            # Smart URL Resolution (User → 990 → GPT priority)
            resolved_url, resolution_method = self._resolve_url(
                user_provided_url,
                filing_url,
                gpt_predicted_url
            )

            logger.info(
                f"Smart URL Resolution for {organization_name}:\n"
                f"  User URL: {user_provided_url or 'None'}\n"
                f"  990 Filing URL: {filing_url or 'None'}\n"
                f"  GPT Predicted URL: {gpt_predicted_url or 'None'}\n"
                f"  RESOLVED: {resolved_url or 'None (will search)'} via {resolution_method}"
            )

            # Create Tool 25 request
            request = WebIntelligenceRequest(
                ein=ein,
                organization_name=organization_name,
                use_case=UseCase.PROFILE_BUILDER,
                user_provided_url=resolved_url,
                require_990_verification=require_990_verification,
                min_confidence_score=min_confidence_score
            )

            # Execute Tool 25
            logger.info(f"Executing Tool 25 Profile Builder for {organization_name} (EIN: {ein})")
            response = await self.tool.execute(request)

            if not response.success:
                error_msg = "; ".join(response.errors) if response.errors else "Unknown error"
                logger.warning(f"Tool 25 failed for {ein}: {error_msg}")
                return False, {
                    "tool_25_error": error_msg,
                    "resolution_method": resolution_method
                }

            # Map intelligence data to profile fields
            profile_data = self._map_intelligence_to_profile(
                response,
                resolved_url,
                resolution_method
            )

            logger.info(
                f"Tool 25 SUCCESS for {organization_name}:\n"
                f"  Execution time: {response.execution_time_seconds:.2f}s\n"
                f"  Pages scraped: {response.pages_scraped}\n"
                f"  Data quality: {response.data_quality_score:.2%}\n"
                f"  Verification confidence: {response.verification_confidence:.2%}"
            )

            return True, profile_data

        except Exception as e:
            logger.error(f"Tool 25 exception for {ein}: {e}", exc_info=True)
            return False, {
                "tool_25_error": str(e),
                "resolution_method": "error"
            }

    def _resolve_url(
        self,
        user_url: Optional[str],
        filing_url: Optional[str],
        gpt_url: Optional[str]
    ) -> Tuple[Optional[str], str]:
        """
        Smart URL Resolution with priority order.

        Priority:
        1. User-provided URL (highest confidence)
        2. 990 Tax Filing URL (most reliable)
        3. GPT-predicted URL (AI fallback)

        Returns:
            (resolved_url, resolution_method)
        """
        if user_url:
            return user_url, "user_provided"
        elif filing_url:
            return filing_url, "990_filing"
        elif gpt_url:
            return gpt_url, "gpt_predicted"
        else:
            return None, "none_available"

    def _map_intelligence_to_profile(
        self,
        response: WebIntelligenceResponse,
        resolved_url: Optional[str],
        resolution_method: str
    ) -> Dict[str, Any]:
        """
        Map Tool 25 intelligence data to profile format.

        Args:
            response: WebIntelligenceResponse from Tool 25
            resolved_url: URL that was used for scraping
            resolution_method: How URL was resolved

        Returns:
            Dict with profile data ready for frontend
        """
        intel_data = response.intelligence_data

        if not intel_data:
            return {
                "enhanced_with_web_data": False,
                "tool_25_metadata": {
                    "execution_time_seconds": response.execution_time_seconds,
                    "url_resolution_method": resolution_method
                }
            }

        # Extract leadership data
        leadership_data = [
            {
                "name": leader.name,
                "title": leader.title,
                "bio": leader.bio,
                "email": leader.email,
                "phone": leader.phone,
                "linkedin_url": leader.linkedin_url,
                "verification_status": leader.verification_status.value,
                "matches_990": leader.matches_990,
                "compensation_990": leader.compensation_990,
                "confidence": 0.9 if leader.matches_990 else 0.7  # Higher confidence for 990-verified
            }
            for leader in intel_data.leadership
        ]

        # Extract program data
        program_data = [
            {
                "name": program.name,
                "description": program.description,
                "target_population": program.target_population,
                "geographic_scope": program.geographic_scope or [],
                "budget_estimate": program.budget_estimate,
                "outcomes": program.outcomes or [],
                "confidence": 0.75  # Default program confidence
            }
            for program in intel_data.programs
        ]

        # Extract contact data
        contact_data = []
        if intel_data.contact_info:
            contact = intel_data.contact_info
            if contact.phone:
                contact_data.append({"type": "phone", "value": contact.phone, "confidence": 0.8})
            if contact.email:
                contact_data.append({"type": "email", "value": contact.email, "confidence": 0.8})
            if contact.mailing_address:
                contact_data.append({"type": "mailing_address", "value": contact.mailing_address, "confidence": 0.8})

        # Build response data
        return {
            "mission_statement": intel_data.mission_statement,
            "vision_statement": intel_data.vision_statement,
            "website": intel_data.website_url,
            "website_url": intel_data.website_url,
            "founded_year": intel_data.founded_year,

            "web_scraping_data": {
                "leadership": leadership_data,
                "programs": program_data,
                "contacts": contact_data,
                "mission_statements": [
                    {
                        "text": intel_data.mission_statement,
                        "source": intel_data.website_url,
                        "confidence": intel_data.scraping_metadata.verification_confidence
                    }
                ] if intel_data.mission_statement else [],
                "vision_statements": [
                    {
                        "text": intel_data.vision_statement,
                        "source": intel_data.website_url,
                        "confidence": intel_data.scraping_metadata.data_quality_score
                    }
                ] if intel_data.vision_statement else [],
                "achievements": [
                    {"text": achievement, "confidence": 0.7}
                    for achievement in intel_data.key_achievements or []
                ],
                "initiatives": [
                    {"text": initiative, "confidence": 0.7}
                    for initiative in intel_data.current_initiatives or []
                ]
            },

            "enhanced_with_web_data": True,
            "data_quality_score": response.data_quality_score,
            "verification_confidence": response.verification_confidence,
            "pages_scraped": response.pages_scraped,

            "tool_25_metadata": {
                "use_case": "PROFILE_BUILDER",
                "execution_time_seconds": response.execution_time_seconds,
                "url_resolution": {
                    "resolved_url": resolved_url,
                    "resolution_method": resolution_method
                },
                "data_quality": intel_data.scraping_metadata.data_quality.value,
                "extraction_status": {
                    "mission_extracted": intel_data.scraping_metadata.mission_extracted,
                    "programs_extracted": intel_data.scraping_metadata.programs_extracted,
                    "leadership_extracted": intel_data.scraping_metadata.leadership_extracted,
                    "contact_extracted": intel_data.scraping_metadata.contact_extracted,
                    "financial_extracted": intel_data.scraping_metadata.financial_extracted
                },
                "extraction_errors": intel_data.extraction_errors or [],
                "validation_warnings": intel_data.validation_warnings or []
            }
        }

    def merge_with_990_data(
        self,
        base_data: Dict[str, Any],
        tool_25_data: Dict[str, Any],
        confidence_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Merge Tool 25 data with 990 tax filing data.

        Auto-population rules:
        - High confidence (>= 0.8): Override existing data
        - Medium confidence (>= 0.6): Populate if empty
        - Low confidence (< 0.6): Do not populate

        Args:
            base_data: Base profile data (from 990)
            tool_25_data: Tool 25 intelligence data
            confidence_threshold: Minimum confidence for auto-population

        Returns:
            Merged profile data
        """
        merged = base_data.copy()

        # Mission statement (high priority)
        tool_mission = tool_25_data.get("mission_statement")
        verification_confidence = tool_25_data.get("verification_confidence", 0.0)

        if tool_mission and verification_confidence >= 0.7:
            if verification_confidence >= 0.8:
                # High confidence: override
                merged["mission_statement"] = tool_mission
            elif not merged.get("mission_statement"):
                # Medium confidence: populate if empty
                merged["mission_statement"] = tool_mission

        # Website URL (high priority)
        tool_website = tool_25_data.get("website")
        if tool_website and verification_confidence >= 0.8:
            merged["website"] = tool_website
            merged["website_url"] = tool_website

        # Vision statement (always add if available)
        if tool_25_data.get("vision_statement"):
            merged["vision_statement"] = tool_25_data["vision_statement"]

        # Founded year (only if not in 990 data)
        if tool_25_data.get("founded_year") and not merged.get("founded_year"):
            merged["founded_year"] = tool_25_data["founded_year"]

        # Web scraping data (always merge)
        if tool_25_data.get("web_scraping_data"):
            merged["web_scraping_data"] = tool_25_data["web_scraping_data"]

        # Tool 25 metadata
        merged["enhanced_with_web_data"] = tool_25_data.get("enhanced_with_web_data", False)
        merged["data_quality_score"] = tool_25_data.get("data_quality_score", 0.0)
        merged["verification_confidence"] = tool_25_data.get("verification_confidence", 0.0)
        merged["pages_scraped"] = tool_25_data.get("pages_scraped", 0)
        merged["tool_25_metadata"] = tool_25_data.get("tool_25_metadata", {})

        return merged


# Singleton instance
_tool25_service = None

def get_tool25_profile_builder() -> Tool25ProfileBuilder:
    """Get singleton Tool 25 Profile Builder instance"""
    global _tool25_service
    if _tool25_service is None:
        _tool25_service = Tool25ProfileBuilder()
    return _tool25_service
