#!/usr/bin/env python3
"""
Smart URL Resolution Service

Delegates to the Enhanced URL Discovery Pipeline for cascading multi-stage
URL resolution with confidence scoring.

Pipeline Stages:
  0: User-provided URL (0.95)
  1: 990 XML WebsiteAddressTxt (0.85)
  2: Multi-year 990 + cross-form consolidation (0.82)
  3: ProPublica JSON API website field (0.80)
  4: DuckDuckGo + Wikidata public APIs (0.70)
  6: Haiku URL predictor + validation (0.65-0.85)
  8: Org name → domain heuristic (0.50)

Estimated cumulative discovery rate: ~73%
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse
import logging
from datetime import datetime

from .enhanced_url_discovery import (
    EnhancedURLDiscoveryPipeline,
    PipelineResult,
    URLCandidate as EnhancedURLCandidate,
)

logger = logging.getLogger(__name__)


# ---- Backward-compatible data classes (used by existing callers) ----

@dataclass
class URLCandidate:
    """URL candidate with confidence and source attribution"""
    url: str
    source: str
    confidence_score: float
    source_description: str
    validation_status: str = "pending"
    http_status_code: Optional[int] = None
    discovered_at: datetime = field(default_factory=datetime.now)
    notes: List[str] = field(default_factory=list)


@dataclass
class URLResolutionResult:
    """Complete URL resolution with ranked candidates"""
    ein: str
    organization_name: str
    primary_url: Optional[URLCandidate] = None
    all_candidates: List[URLCandidate] = field(default_factory=list)
    resolution_strategy: str = ""
    confidence_assessment: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    # New fields from enhanced pipeline
    stage_resolved: Optional[int] = None
    stages_attempted: List[int] = field(default_factory=list)
    pipeline_cost_usd: float = 0.0


def _convert_candidate(ec: EnhancedURLCandidate) -> URLCandidate:
    """Convert an enhanced pipeline candidate to the legacy format."""
    return URLCandidate(
        url=ec.url,
        source=ec.source,
        confidence_score=ec.final_confidence,
        source_description=ec.description,
        validation_status=ec.validation_status,
        http_status_code=ec.http_status_code,
        discovered_at=ec.discovered_at,
        notes=list(ec.notes),
    )


class SmartURLResolutionService:
    """
    Intelligent URL resolution with cascading multi-stage pipeline.

    Delegates to EnhancedURLDiscoveryPipeline for the actual work while
    preserving the original interface consumed by Tool 25 and the profiles
    workflow.
    """

    def __init__(self, *, haiku_api_key: Optional[str] = None):
        self._pipeline = EnhancedURLDiscoveryPipeline(
            validate_urls=True,
            check_ein_on_page=True,
            haiku_api_key=haiku_api_key,
        )

    async def resolve_organization_url(
        self,
        ein: str,
        organization_name: str,
        user_provided_url: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        ntee_code: Optional[str] = None,
    ) -> URLResolutionResult:
        """
        Resolve the best URL for an organization using the enhanced pipeline.

        Args:
            ein: Organization EIN
            organization_name: Organization name
            user_provided_url: Optional user-provided website URL
            city: Optional city for Haiku predictor context
            state: Optional state for Haiku predictor context
            ntee_code: Optional NTEE code for Haiku predictor context

        Returns:
            URLResolutionResult with ranked URL candidates
        """
        logger.info(f"Resolving URLs for {organization_name} (EIN: {ein})")

        pipeline_result: PipelineResult = await self._pipeline.discover(
            ein=ein,
            organization_name=organization_name,
            user_url=user_provided_url,
            city=city,
            state=state,
            ntee_code=ntee_code,
        )

        # Convert to legacy result format
        result = URLResolutionResult(
            ein=ein,
            organization_name=organization_name,
            stage_resolved=pipeline_result.stage_resolved,
            stages_attempted=pipeline_result.stages_attempted,
            pipeline_cost_usd=pipeline_result.total_cost_usd,
        )

        # Convert candidates
        result.all_candidates = [_convert_candidate(c) for c in pipeline_result.all_candidates]

        if pipeline_result.primary_url:
            result.primary_url = _convert_candidate(pipeline_result.primary_url)

        # Build assessment from pipeline data
        result.resolution_strategy = self._build_strategy(pipeline_result)
        result.confidence_assessment = self._build_confidence(pipeline_result)
        result.recommendations = self._build_recommendations(pipeline_result)

        url_str = result.primary_url.url if result.primary_url else "No valid URL found"
        logger.info(f"URL resolution completed for {organization_name}: {url_str}")

        return result

    # ------------------------------------------------------------------
    # Assessment helpers
    # ------------------------------------------------------------------

    _SOURCE_LABELS = {
        "user_provided": "User-provided URL (highest confidence)",
        "990_xml": "990 XML declared website",
        "990_xml_multiyear": "Historical 990 filing website",
        "propublica_json": "ProPublica JSON API",
        "duckduckgo": "DuckDuckGo Instant Answer",
        "duckduckgo_infobox": "DuckDuckGo Infobox",
        "wikidata": "Wikidata official website",
        "haiku_predictor": "Haiku AI prediction (validated)",
        "name_heuristic": "Organization name heuristic",
    }

    def _build_strategy(self, pr: PipelineResult) -> str:
        if not pr.primary_url:
            return "No valid URL found after all 6 pipeline stages"
        label = self._SOURCE_LABELS.get(pr.primary_url.source, pr.primary_url.source)
        status = pr.primary_url.validation_status
        return f"Resolved at stage {pr.stage_resolved}: {label} – {status}"

    def _build_confidence(self, pr: PipelineResult) -> Dict[str, Any]:
        if not pr.primary_url:
            return {
                "overall_confidence": 0.0,
                "confidence_factors": [],
                "risk_factors": ["No valid URL found after all stages"],
                "data_quality": "poor",
            }

        conf = pr.primary_url.final_confidence
        factors = [self._SOURCE_LABELS.get(pr.primary_url.source, pr.primary_url.source)]
        risks = []

        if pr.primary_url.validation_status == "valid":
            factors.append("HTTP validation successful")
        if pr.primary_url.ein_verified:
            factors.append("EIN confirmed on target page")
        if pr.primary_url.validation_status in ("timeout", "invalid"):
            risks.append(f"Validation status: {pr.primary_url.validation_status}")
        if len(pr.all_candidates) == 1:
            risks.append("Single URL source (no alternatives)")
        if pr.primary_url.stage >= 6:
            risks.append("Resolved via prediction/heuristic – verify manually")

        quality = "excellent" if conf >= 0.85 else "good" if conf >= 0.70 else "fair" if conf >= 0.50 else "poor"

        return {
            "overall_confidence": round(conf, 4),
            "confidence_factors": factors,
            "risk_factors": risks,
            "data_quality": quality,
        }

    def _build_recommendations(self, pr: PipelineResult) -> List[str]:
        if not pr.primary_url:
            return [
                "Manual URL verification required – no valid URLs found after all stages",
                "Consider adding organization website to profile",
            ]

        recs = []
        if pr.primary_url.final_confidence >= 0.80:
            recs.append("High confidence URL – proceed with web scraping")
        elif pr.primary_url.final_confidence >= 0.60:
            recs.append("Moderate confidence – consider manual verification")
        else:
            recs.append("Low confidence – manual verification recommended")

        if pr.primary_url.source != "user_provided":
            recs.append("Consider adding user-provided URL for higher confidence")

        valid_count = sum(1 for c in pr.all_candidates if c.validation_status == "valid")
        if valid_count > 1:
            recs.append(f"{valid_count} valid URLs found – best candidate selected")

        return recs