#!/usr/bin/env python3
"""
Entity-Based Discovery Service
Enhanced discovery engine that leverages entity-based architecture and shared analytics.
"""

import asyncio
import uuid
import time
from typing import Dict, List, Optional, Any, AsyncIterator, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

from .base_discoverer import DiscoveryResult, DiscoveryStatus, FunnelStage
from ..core.entity_cache_manager import get_entity_cache_manager, EntityType, DataSourceType
from ..analytics.financial_analytics import get_financial_analytics, FinancialMetrics
from ..analytics.network_analytics import get_network_analytics, NetworkMetrics
from ..analysis.profile_matcher import get_profile_matcher, OpportunityMatch
from ..profiles.models import OrganizationProfile, ProfileSearchParams, FundingType

logger = logging.getLogger(__name__)


@dataclass
class EntityDiscoveryResult:
    """Enhanced discovery result with entity references and analytics"""
    # Entity References
    organization_ein: str
    organization_name: str
    opportunity_id: Optional[str] = None
    opportunity_title: Optional[str] = None
    
    # Discovery Metadata
    source_type: FundingType = FundingType.GRANTS
    discovery_source: str = "entity_cache"
    discovered_at: datetime = field(default_factory=datetime.now)
    
    # Enhanced Analytics
    financial_metrics: Optional[FinancialMetrics] = None
    network_metrics: Optional[NetworkMetrics] = None
    opportunity_match: Optional[OpportunityMatch] = None
    
    # Scoring
    entity_health_score: float = 0.0
    profile_compatibility_score: float = 0.0
    opportunity_match_score: float = 0.0
    final_discovery_score: float = 0.0
    
    # Classification
    funnel_stage: FunnelStage = FunnelStage.PROSPECTS
    confidence_level: float = 0.0
    
    # Additional Data
    data_sources: List[str] = field(default_factory=list)
    match_reasons: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    
    def to_legacy_result(self) -> DiscoveryResult:
        """Convert to legacy DiscoveryResult format for compatibility"""
        return DiscoveryResult(
            organization_name=self.organization_name,
            source_type=self.source_type,
            discovery_source=self.discovery_source,
            opportunity_id=self.opportunity_id or f"entity_{self.organization_ein}",
            program_name=self.opportunity_title,
            description=f"Entity-based discovery: {self.organization_name}",
            funding_amount=None,  # Would be extracted from opportunity data
            raw_score=self.entity_health_score,
            compatibility_score=self.profile_compatibility_score,
            confidence_level=self.confidence_level,
            funnel_stage=self.funnel_stage,
            stage_notes="; ".join(self.match_reasons) if self.match_reasons else None,
            external_data={'match_reasons': self.match_reasons, 'risk_factors': self.risk_factors}
        )


class EntityDiscoveryService:
    """
    Enhanced discovery service using entity-based architecture.
    
    Features:
    - Entity cache-based data sources
    - Shared analytics integration
    - Profile-specific matching
    - Entity reference tracking
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize entity-based components
        self.entity_cache_manager = get_entity_cache_manager()
        self.financial_analytics = get_financial_analytics()
        self.network_analytics = get_network_analytics()
        self.profile_matcher = get_profile_matcher()
        
        # Discovery configuration
        self.max_entities_per_type = 50
        self.scoring_weights = {
            "financial_health": 0.35,
            "profile_compatibility": 0.40,
            "opportunity_match": 0.25
        }
    
    async def discover_nonprofit_opportunities(self, 
                                             profile: OrganizationProfile,
                                             max_results: int = 100,
                                             filters: Optional[Dict[str, Any]] = None) -> AsyncIterator[EntityDiscoveryResult]:
        """
        Discover nonprofit grant opportunities using entity-based data.
        
        Args:
            profile: Organization profile for matching
            max_results: Maximum results to return
            filters: Additional discovery filters
            
        Yields:
            EntityDiscoveryResult objects with comprehensive analysis
        """
        try:
            self.logger.info(f"Starting entity-based nonprofit discovery for profile: {profile.name}")
            
            # Get nonprofit entities from cache
            nonprofit_eins = await self.entity_cache_manager.list_entities(EntityType.NONPROFIT)
            
            # Apply filters if provided
            if filters:
                nonprofit_eins = self._apply_entity_filters(nonprofit_eins, filters)
            
            # Limit for performance
            nonprofit_eins = nonprofit_eins[:min(max_results, self.max_entities_per_type)]
            
            self.logger.info(f"Analyzing {len(nonprofit_eins)} nonprofit entities")
            
            # Process each nonprofit entity
            results_count = 0
            for ein in nonprofit_eins:
                if results_count >= max_results:
                    break
                
                try:
                    result = await self._analyze_nonprofit_entity(ein, profile)
                    if result and result.final_discovery_score > 0.3:  # Quality threshold
                        yield result
                        results_count += 1
                        
                        # Rate limiting for processing
                        if results_count % 10 == 0:
                            await asyncio.sleep(0.1)
                            
                except Exception as e:
                    self.logger.warning(f"Error analyzing nonprofit entity {ein}: {e}")
                    continue
            
            self.logger.info(f"Completed nonprofit discovery: {results_count} results")
            
        except Exception as e:
            self.logger.error(f"Error in nonprofit discovery: {e}")
            raise
    
    async def discover_government_opportunities(self,
                                              profile: OrganizationProfile,
                                              max_results: int = 100,
                                              filters: Optional[Dict[str, Any]] = None) -> AsyncIterator[EntityDiscoveryResult]:
        """
        Discover government funding opportunities using entity-based data.
        
        Args:
            profile: Organization profile for matching
            max_results: Maximum results to return
            filters: Additional discovery filters
            
        Yields:
            EntityDiscoveryResult objects with opportunity matches
        """
        try:
            self.logger.info(f"Starting entity-based government discovery for profile: {profile.name}")
            
            # Get government opportunities from cache
            opportunity_ids = await self.entity_cache_manager.list_entities(EntityType.GOVERNMENT_OPPORTUNITY)
            
            # Apply filters
            if filters:
                opportunity_ids = self._apply_opportunity_filters(opportunity_ids, filters)
            
            # Limit for performance
            opportunity_ids = opportunity_ids[:min(max_results, self.max_entities_per_type)]
            
            self.logger.info(f"Analyzing {len(opportunity_ids)} government opportunities")
            
            # Process each opportunity
            results_count = 0
            for opp_id in opportunity_ids:
                if results_count >= max_results:
                    break
                
                try:
                    result = await self._analyze_government_opportunity(opp_id, profile)
                    if result and result.final_discovery_score > 0.4:  # Higher threshold for opportunities
                        yield result
                        results_count += 1
                        
                        # Rate limiting
                        if results_count % 5 == 0:
                            await asyncio.sleep(0.1)
                            
                except Exception as e:
                    self.logger.warning(f"Error analyzing government opportunity {opp_id}: {e}")
                    continue
            
            self.logger.info(f"Completed government discovery: {results_count} results")
            
        except Exception as e:
            self.logger.error(f"Error in government discovery: {e}")
            raise
    
    async def discover_combined_opportunities(self,
                                            profile: OrganizationProfile,
                                            max_results: int = 100,
                                            include_types: List[str] = None,
                                            filters: Optional[Dict[str, Any]] = None) -> List[EntityDiscoveryResult]:
        """
        Combined discovery across multiple entity types with cross-matching.
        
        Args:
            profile: Organization profile for matching
            max_results: Maximum total results
            include_types: Types to include ['nonprofits', 'government', 'foundations']
            filters: Discovery filters
            
        Returns:
            Sorted list of discovery results
        """
        try:
            if include_types is None:
                include_types = ['nonprofits', 'government']
            
            all_results = []
            
            # Discover nonprofits
            if 'nonprofits' in include_types:
                nonprofit_results = []
                async for result in self.discover_nonprofit_opportunities(
                    profile, max_results=max_results//2, filters=filters
                ):
                    nonprofit_results.append(result)
                all_results.extend(nonprofit_results)
            
            # Discover government opportunities
            if 'government' in include_types:
                gov_results = []
                async for result in self.discover_government_opportunities(
                    profile, max_results=max_results//2, filters=filters
                ):
                    gov_results.append(result)
                all_results.extend(gov_results)
            
            # Sort by final discovery score
            all_results.sort(key=lambda x: x.final_discovery_score, reverse=True)
            
            # Limit to max_results
            final_results = all_results[:max_results]
            
            # Apply cross-entity analysis for top results
            if len(final_results) > 0:
                await self._apply_cross_entity_analysis(final_results)
            
            self.logger.info(f"Combined discovery completed: {len(final_results)} total results")
            return final_results
            
        except Exception as e:
            self.logger.error(f"Error in combined discovery: {e}")
            return []
    
    async def _analyze_nonprofit_entity(self, ein: str, profile: OrganizationProfile) -> Optional[EntityDiscoveryResult]:
        """Analyze a single nonprofit entity for discovery"""
        try:
            # Get entity data
            org_data = await self.entity_cache_manager.get_entity_data(
                entity_id=ein,
                entity_type=EntityType.NONPROFIT,
                data_source=DataSourceType.PROPUBLICA
            )
            
            if not org_data:
                return None
            
            # Extract organization info
            org_info = org_data.get('organization', {})
            org_name = org_info.get('name', 'Unknown Organization')
            
            # Shared financial analytics
            financial_metrics = self.financial_analytics.analyze_organization_financials(
                filing_data=org_data,
                organization_name=org_name,
                ein=ein
            )
            
            # Shared network analytics
            board_members = self.network_analytics.extract_board_members_from_data(
                filing_data=org_data,
                ein=ein,
                organization_name=org_name
            )
            
            # Profile-specific analysis
            profile_analysis = self.profile_matcher.analyze_organization_for_profile(
                organization_data=org_data,
                profile_criteria=None  # Would use profile.funding_preferences
            )
            
            # Create result
            result = EntityDiscoveryResult(
                organization_ein=ein,
                organization_name=org_name,
                source_type=FundingType.GRANTS,
                discovery_source="entity_cache_nonprofit",
                financial_metrics=financial_metrics,
                data_sources=org_data.get('data_sources', [])
            )
            
            # Calculate scores
            result.entity_health_score = financial_metrics.financial_stability_score or 0.5
            result.profile_compatibility_score = profile_analysis.get('profile_compatibility_score', 0.5)
            
            # Calculate final score
            result.final_discovery_score = (
                result.entity_health_score * self.scoring_weights["financial_health"] +
                result.profile_compatibility_score * self.scoring_weights["profile_compatibility"]
            )
            
            # Determine funnel stage
            result.funnel_stage = self._determine_funnel_stage(result.final_discovery_score)
            result.confidence_level = min(result.final_discovery_score * 1.2, 1.0)
            
            # Add match reasons
            if result.entity_health_score >= 0.7:
                result.match_reasons.append("Strong financial health")
            if result.profile_compatibility_score >= 0.6:
                result.match_reasons.append("Good profile compatibility")
            if len(board_members) > 3:
                result.match_reasons.append("Active board governance")
            
            # Add risk factors
            if result.entity_health_score < 0.4:
                result.risk_factors.append("Below-average financial stability")
            if not result.data_sources:
                result.risk_factors.append("Limited data sources")
            
            return result
            
        except Exception as e:
            self.logger.debug(f"Error analyzing nonprofit entity {ein}: {e}")
            return None
    
    async def _analyze_government_opportunity(self, opp_id: str, profile: OrganizationProfile) -> Optional[EntityDiscoveryResult]:
        """Analyze a government opportunity for discovery"""
        try:
            # Get opportunity data
            opp_data = await self.entity_cache_manager.get_entity_data(
                entity_id=opp_id,
                entity_type=EntityType.GOVERNMENT_OPPORTUNITY,
                data_source=DataSourceType.GRANTS_GOV
            )
            
            if not opp_data:
                return None
            
            # Extract opportunity info
            opp_title = opp_data.get('funding_opportunity_title', 'Unknown Opportunity')
            agency = opp_data.get('agency_code', 'Unknown Agency')
            
            # Create result for government opportunity
            result = EntityDiscoveryResult(
                organization_ein="government_opportunity",  # Special case for opportunities
                organization_name=f"{agency} - Federal Grant",
                opportunity_id=opp_id,
                opportunity_title=opp_title,
                source_type=FundingType.GOVERNMENT,
                discovery_source="entity_cache_government"
            )
            
            # Score opportunity against profile
            opp_score = self._score_opportunity_for_profile(opp_data, profile)
            result.opportunity_match_score = opp_score
            result.profile_compatibility_score = opp_score  # For government, these are similar
            
            # Government opportunities get boosted entity health (reliable source)
            result.entity_health_score = 0.8
            
            # Calculate final score
            result.final_discovery_score = (
                result.entity_health_score * self.scoring_weights["financial_health"] +
                result.profile_compatibility_score * self.scoring_weights["profile_compatibility"] +
                result.opportunity_match_score * self.scoring_weights["opportunity_match"]
            )
            
            # Determine funnel stage
            result.funnel_stage = self._determine_funnel_stage(result.final_discovery_score)
            result.confidence_level = min(result.final_discovery_score * 1.1, 1.0)
            
            # Add match reasons and risk factors
            funding_amount = opp_data.get('award_ceiling', 0)
            if funding_amount and funding_amount >= 100000:
                result.match_reasons.append(f"Significant funding: ${funding_amount:,.0f}")
            
            eligibility = opp_data.get('eligibility', {})
            if '25' in eligibility.get('codes', []):  # Nonprofit eligibility
                result.match_reasons.append("Nonprofit eligible")
            else:
                result.risk_factors.append("Eligibility uncertain")
            
            category = opp_data.get('category_of_funding_activity', '')
            if category:
                result.match_reasons.append(f"Category: {category}")
            
            return result
            
        except Exception as e:
            self.logger.debug(f"Error analyzing government opportunity {opp_id}: {e}")
            return None
    
    def _score_opportunity_for_profile(self, opp_data: Dict[str, Any], profile: OrganizationProfile) -> float:
        """Score an opportunity against a profile"""
        try:
            score_components = []
            
            # Funding amount scoring
            funding_amount = opp_data.get('award_ceiling', 0)
            if funding_amount:
                if funding_amount >= 100000:
                    score_components.append(0.8)
                elif funding_amount >= 50000:
                    score_components.append(0.6)
                else:
                    score_components.append(0.4)
            else:
                score_components.append(0.5)
            
            # Category matching
            category = opp_data.get('category_of_funding_activity', '').lower()
            if category:
                # Match against profile focus areas
                focus_matches = 0
                for focus_area in profile.focus_areas:
                    if focus_area.lower() in category:
                        focus_matches += 1
                
                if focus_matches > 0:
                    score_components.append(min(0.8, 0.5 + (focus_matches * 0.1)))
                else:
                    score_components.append(0.4)
            else:
                score_components.append(0.5)
            
            # Eligibility scoring
            eligibility = opp_data.get('eligibility', {})
            if '25' in eligibility.get('codes', []):  # Nonprofit eligible
                score_components.append(1.0)
            else:
                score_components.append(0.2)
            
            return sum(score_components) / len(score_components) if score_components else 0.5
            
        except Exception as e:
            self.logger.debug(f"Error scoring opportunity: {e}")
            return 0.5
    
    def _determine_funnel_stage(self, score: float) -> FunnelStage:
        """Determine appropriate funnel stage based on score"""
        if score >= 0.8:
            return FunnelStage.OPPORTUNITIES
        elif score >= 0.7:
            return FunnelStage.TARGETS
        elif score >= 0.6:
            return FunnelStage.CANDIDATES
        elif score >= 0.5:
            return FunnelStage.QUALIFIED_PROSPECTS
        else:
            return FunnelStage.PROSPECTS
    
    def _apply_entity_filters(self, eins: List[str], filters: Dict[str, Any]) -> List[str]:
        """Apply filters to entity list"""
        # For now, return limited list - could be enhanced with actual filtering
        max_entities = filters.get('max_entities', 50)
        return eins[:max_entities]
    
    def _apply_opportunity_filters(self, opp_ids: List[str], filters: Dict[str, Any]) -> List[str]:
        """Apply filters to opportunity list"""
        max_opportunities = filters.get('max_opportunities', 50)
        return opp_ids[:max_opportunities]
    
    async def _apply_cross_entity_analysis(self, results: List[EntityDiscoveryResult]):
        """Apply cross-entity analysis to enhance results"""
        try:
            # Group by type
            nonprofits = [r for r in results if r.source_type == FundingType.GRANTS]
            opportunities = [r for r in results if r.source_type == FundingType.GOVERNMENT]
            
            # Look for potential matches between nonprofits and opportunities
            for nonprofit in nonprofits[:10]:  # Limit for performance
                for opportunity in opportunities[:10]:
                    # Check for keyword/category matches
                    nonprofit_name = nonprofit.organization_name.lower()
                    opp_title = opportunity.opportunity_title.lower() if opportunity.opportunity_title else ""
                    
                    # Simple keyword matching - could be enhanced
                    common_keywords = ['education', 'health', 'community', 'environment', 'research']
                    matches = 0
                    for keyword in common_keywords:
                        if keyword in nonprofit_name and keyword in opp_title:
                            matches += 1
                    
                    if matches > 0:
                        nonprofit.match_reasons.append(f"Potential match with {opportunity.opportunity_title}")
                        opportunity.match_reasons.append(f"Potential match with {nonprofit.organization_name}")
            
        except Exception as e:
            self.logger.debug(f"Error in cross-entity analysis: {e}")


# Global service instance
_entity_discovery_service: Optional[EntityDiscoveryService] = None


def get_entity_discovery_service() -> EntityDiscoveryService:
    """Get or create global entity discovery service instance"""
    global _entity_discovery_service
    if _entity_discovery_service is None:
        _entity_discovery_service = EntityDiscoveryService()
    return _entity_discovery_service