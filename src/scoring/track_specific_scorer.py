#!/usr/bin/env python3
"""
Track-Specific Discovery Scorer - Phase 1 Implementation
4-Track system with integrated BMF processing and opportunity-type-aware scoring

Implements the 4-track discovery system:
1. Nonprofit + BMF Integration (NTEE-first approach)
2. Federal Opportunities (Government eligibility focus)
3. State Opportunities (Geographic advantage emphasis)
4. Commercial Opportunities (Partnership potential focus)
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

from src.profiles.models import OrganizationProfile

logger = logging.getLogger(__name__)


class DiscoveryTrack(Enum):
    """Four discovery tracks for streamlined user experience"""
    NONPROFIT_BMF = "nonprofit_bmf"      # Track 1: Nonprofit + BMF Integration
    FEDERAL = "federal"                  # Track 2: Federal Opportunities
    STATE = "state"                      # Track 3: State Opportunities  
    COMMERCIAL = "commercial"            # Track 4: Commercial Opportunities


class TrackScoringDimensions(Enum):
    """Track-specific scoring dimensions"""
    # Track 1: Nonprofit + BMF
    NTEE_COMPATIBILITY = "ntee_compatibility"
    PROGRAM_ALIGNMENT = "program_alignment"
    REVENUE_COMPATIBILITY = "revenue_compatibility"
    GEOGRAPHIC_PROXIMITY = "geographic_proximity"
    BOARD_NETWORK_PREVIEW = "board_network_preview"
    
    # Track 2: Federal
    ELIGIBILITY_COMPLIANCE = "eligibility_compliance"
    AWARD_SIZE_COMPATIBILITY = "award_size_compatibility"
    AGENCY_ALIGNMENT = "agency_alignment"
    HISTORICAL_SUCCESS = "historical_success"
    GEOGRAPHIC_ELIGIBILITY = "geographic_eligibility"
    
    # Track 3: State
    GEOGRAPHIC_ADVANTAGE = "geographic_advantage"
    STATE_PROGRAM_ALIGNMENT = "state_program_alignment"
    LOCAL_NETWORK_STRENGTH = "local_network_strength"
    TIMING_ADVANTAGE = "timing_advantage"
    
    # Track 4: Commercial
    STRATEGIC_PARTNERSHIP_FIT = "strategic_partnership_fit"
    INDUSTRY_ALIGNMENT = "industry_alignment"
    PARTNERSHIP_POTENTIAL = "partnership_potential"
    FOUNDATION_TYPE_MATCH = "foundation_type_match"


@dataclass
class TrackConfiguration:
    """Configuration for each discovery track"""
    track: DiscoveryTrack
    revenue_range: Tuple[int, int]  # (min, max) in dollars
    scoring_weights: Dict[TrackScoringDimensions, float]
    promotion_thresholds: Dict[str, float]
    primary_filter: str
    description: str


@dataclass
class TrackScoringResult:
    """Enhanced scoring result with track-specific information"""
    track: DiscoveryTrack
    overall_score: float
    dimension_scores: Dict[TrackScoringDimensions, float]
    confidence_level: float
    revenue_compatibility: float
    track_specific_factors: Dict[str, Any]
    promotion_category: str
    scored_at: datetime
    
    @property
    def is_auto_promote(self) -> bool:
        """Whether this result qualifies for auto-promotion"""
        return self.promotion_category == "auto_promote"
    
    @property  
    def is_high_priority(self) -> bool:
        """Whether this result is high priority for review"""
        return self.promotion_category in ["auto_promote", "high_priority"]


class TrackSpecificScorer:
    """Enhanced discovery scorer with 4-track system and BMF integration"""
    
    def __init__(self):
        """Initialize track configurations and scoring parameters"""
        
        # Track 1: Nonprofit + BMF Integration Configuration
        self.nonprofit_config = TrackConfiguration(
            track=DiscoveryTrack.NONPROFIT_BMF,
            revenue_range=(50000, 50000000),  # $50K-$50M nonprofit range
            scoring_weights={
                TrackScoringDimensions.NTEE_COMPATIBILITY: 0.40,
                TrackScoringDimensions.PROGRAM_ALIGNMENT: 0.25,
                TrackScoringDimensions.REVENUE_COMPATIBILITY: 0.20,
                TrackScoringDimensions.GEOGRAPHIC_PROXIMITY: 0.10,
                TrackScoringDimensions.BOARD_NETWORK_PREVIEW: 0.05
            },
            promotion_thresholds={
                "auto_promote": 0.80,
                "high_priority": 0.70,
                "medium_priority": 0.55,
                "low_priority": 0.35
            },
            primary_filter="NTEE_codes",
            description="Nonprofit organizations with integrated BMF filtering"
        )
        
        # Track 2: Federal Opportunities Configuration
        self.federal_config = TrackConfiguration(
            track=DiscoveryTrack.FEDERAL,
            revenue_range=(100000, 10000000),  # $100K-$10M+ federal capacity
            scoring_weights={
                TrackScoringDimensions.ELIGIBILITY_COMPLIANCE: 0.35,
                TrackScoringDimensions.AWARD_SIZE_COMPATIBILITY: 0.25,
                TrackScoringDimensions.AGENCY_ALIGNMENT: 0.20,
                TrackScoringDimensions.HISTORICAL_SUCCESS: 0.15,
                TrackScoringDimensions.GEOGRAPHIC_ELIGIBILITY: 0.05
            },
            promotion_thresholds={
                "auto_promote": 0.75,
                "high_priority": 0.65,
                "medium_priority": 0.50,
                "low_priority": 0.30
            },
            primary_filter="government_eligibility",
            description="Federal grant opportunities with agency focus"
        )
        
        # Track 3: State Opportunities Configuration  
        self.state_config = TrackConfiguration(
            track=DiscoveryTrack.STATE,
            revenue_range=(25000, 2000000),  # $25K-$2M state range
            scoring_weights={
                TrackScoringDimensions.GEOGRAPHIC_ADVANTAGE: 0.35,
                TrackScoringDimensions.STATE_PROGRAM_ALIGNMENT: 0.25,
                TrackScoringDimensions.REVENUE_COMPATIBILITY: 0.20,
                TrackScoringDimensions.LOCAL_NETWORK_STRENGTH: 0.15,
                TrackScoringDimensions.TIMING_ADVANTAGE: 0.05
            },
            promotion_thresholds={
                "auto_promote": 0.80,
                "high_priority": 0.65,
                "medium_priority": 0.50,
                "low_priority": 0.35
            },
            primary_filter="geographic_advantage",
            description="State and regional grant opportunities"
        )
        
        # Track 4: Commercial Opportunities Configuration
        self.commercial_config = TrackConfiguration(
            track=DiscoveryTrack.COMMERCIAL,
            revenue_range=(10000, 500000),  # $10K-$500K partnership range
            scoring_weights={
                TrackScoringDimensions.STRATEGIC_PARTNERSHIP_FIT: 0.30,
                TrackScoringDimensions.REVENUE_COMPATIBILITY: 0.25,
                TrackScoringDimensions.INDUSTRY_ALIGNMENT: 0.20,
                TrackScoringDimensions.PARTNERSHIP_POTENTIAL: 0.15,
                TrackScoringDimensions.FOUNDATION_TYPE_MATCH: 0.10
            },
            promotion_thresholds={
                "auto_promote": 0.75,
                "high_priority": 0.65,
                "medium_priority": 0.50,
                "low_priority": 0.30
            },
            primary_filter="partnership_potential",
            description="Corporate foundations and commercial partnerships"
        )
        
        # Configuration mapping for easy access
        self.track_configs = {
            DiscoveryTrack.NONPROFIT_BMF: self.nonprofit_config,
            DiscoveryTrack.FEDERAL: self.federal_config,
            DiscoveryTrack.STATE: self.state_config,
            DiscoveryTrack.COMMERCIAL: self.commercial_config
        }
    
    async def score_opportunity_by_track(
        self,
        opportunity: Dict[str, Any],
        profile: OrganizationProfile,
        track: DiscoveryTrack,
        enhanced_data: Optional[Dict[str, Any]] = None
    ) -> TrackScoringResult:
        """
        Score opportunity using track-specific algorithms
        
        Args:
            opportunity: Opportunity data
            profile: Organization profile
            track: Specific discovery track to use
            enhanced_data: Optional 990/BMF data for enhanced scoring
            
        Returns:
            TrackScoringResult with track-aware scoring
        """
        try:
            logger.info(f"Scoring opportunity {opportunity.get('organization_name')} using {track.value} track")
            
            config = self.track_configs[track]
            
            # Calculate track-specific dimension scores
            dimension_scores = await self._calculate_track_scores(
                opportunity, profile, config, enhanced_data
            )
            
            # Calculate overall weighted score
            overall_score = self._calculate_weighted_score(dimension_scores, config)
            
            # Calculate revenue compatibility
            revenue_compatibility = await self._calculate_revenue_compatibility(
                opportunity, profile, config, enhanced_data
            )
            
            # Calculate confidence level
            confidence = self._calculate_confidence(dimension_scores, enhanced_data, config)
            
            # Determine promotion category
            promotion_category = self._determine_promotion_category(overall_score, confidence, config)
            
            # Generate track-specific factors
            track_factors = await self._generate_track_factors(
                opportunity, profile, config, enhanced_data
            )
            
            return TrackScoringResult(
                track=track,
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                confidence_level=confidence,
                revenue_compatibility=revenue_compatibility,
                track_specific_factors=track_factors,
                promotion_category=promotion_category,
                scored_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error scoring opportunity with track {track.value}: {e}")
            return self._create_error_result(track, str(e))
    
    async def determine_best_track(
        self,
        opportunity: Dict[str, Any],
        profile: OrganizationProfile
    ) -> DiscoveryTrack:
        """
        Determine the most appropriate track for an opportunity
        
        Args:
            opportunity: Opportunity data
            profile: Organization profile
            
        Returns:
            Best matching DiscoveryTrack
        """
        source_type = opportunity.get('source_type', '').lower()
        discovery_source = opportunity.get('discovery_source', '').lower()
        
        # Priority 1: Nonprofit + BMF (most common)
        if ('nonprofit' in source_type or 
            'bmf' in discovery_source or 
            opportunity.get('external_data', {}).get('ntee_code')):
            return DiscoveryTrack.NONPROFIT_BMF
        
        # Priority 2: Federal opportunities  
        if ('government' in source_type or 
            'grants.gov' in discovery_source or
            'federal' in source_type):
            return DiscoveryTrack.FEDERAL
        
        # Priority 3: State opportunities
        if ('state' in source_type or 
            'va_state' in discovery_source or
            opportunity.get('external_data', {}).get('state')):
            return DiscoveryTrack.STATE
        
        # Priority 4: Commercial (fallback)
        return DiscoveryTrack.COMMERCIAL
    
    async def score_with_bmf_integration(
        self,
        opportunity: Dict[str, Any],
        profile: OrganizationProfile,
        bmf_data: Optional[Dict[str, Any]] = None
    ) -> TrackScoringResult:
        """
        Score opportunity with integrated BMF processing (Track 1 specific)
        This replaces the separate BMF Filter functionality
        
        Args:
            opportunity: Opportunity data
            profile: Organization profile  
            bmf_data: BMF data for enhanced nonprofit scoring
            
        Returns:
            TrackScoringResult with BMF integration
        """
        # Always use nonprofit track for BMF integration
        enhanced_data = {}
        
        if bmf_data:
            enhanced_data['bmf_data'] = bmf_data
            enhanced_data['financial_data'] = bmf_data.get('financial_data', {})
            enhanced_data['ntee_exact_match'] = self._check_ntee_match(opportunity, profile, bmf_data)
        
        return await self.score_opportunity_by_track(
            opportunity, profile, DiscoveryTrack.NONPROFIT_BMF, enhanced_data
        )
    
    # Track-specific scoring implementations
    
    async def _calculate_track_scores(
        self,
        opportunity: Dict[str, Any],
        profile: OrganizationProfile,
        config: TrackConfiguration,
        enhanced_data: Optional[Dict[str, Any]]
    ) -> Dict[TrackScoringDimensions, float]:
        """Calculate scores for all dimensions in the specified track"""
        
        scores = {}
        
        if config.track == DiscoveryTrack.NONPROFIT_BMF:
            scores = await self._score_nonprofit_dimensions(opportunity, profile, enhanced_data)
        elif config.track == DiscoveryTrack.FEDERAL:
            scores = await self._score_federal_dimensions(opportunity, profile, enhanced_data)
        elif config.track == DiscoveryTrack.STATE:
            scores = await self._score_state_dimensions(opportunity, profile, enhanced_data)
        elif config.track == DiscoveryTrack.COMMERCIAL:
            scores = await self._score_commercial_dimensions(opportunity, profile, enhanced_data)
        
        return scores
    
    async def _score_nonprofit_dimensions(
        self,
        opportunity: Dict[str, Any],
        profile: OrganizationProfile,
        enhanced_data: Optional[Dict[str, Any]]
    ) -> Dict[TrackScoringDimensions, float]:
        """Score dimensions specific to Nonprofit + BMF track"""
        
        scores = {}
        
        # NTEE Compatibility (40% weight)
        scores[TrackScoringDimensions.NTEE_COMPATIBILITY] = await self._score_ntee_compatibility(
            opportunity, profile, enhanced_data
        )
        
        # Program Alignment (25% weight)
        scores[TrackScoringDimensions.PROGRAM_ALIGNMENT] = await self._score_program_alignment(
            opportunity, profile
        )
        
        # Revenue Compatibility (20% weight) 
        scores[TrackScoringDimensions.REVENUE_COMPATIBILITY] = await self._score_nonprofit_revenue(
            opportunity, profile, enhanced_data
        )
        
        # Geographic Proximity (10% weight)
        scores[TrackScoringDimensions.GEOGRAPHIC_PROXIMITY] = await self._score_geographic_proximity(
            opportunity, profile
        )
        
        # Board Network Preview (5% weight)
        scores[TrackScoringDimensions.BOARD_NETWORK_PREVIEW] = await self._score_board_network_preview(
            opportunity, profile, enhanced_data
        )
        
        return scores
    
    async def _score_federal_dimensions(
        self,
        opportunity: Dict[str, Any],
        profile: OrganizationProfile,
        enhanced_data: Optional[Dict[str, Any]]
    ) -> Dict[TrackScoringDimensions, float]:
        """Score dimensions specific to Federal track"""
        
        scores = {}
        
        # Eligibility Compliance (35% weight)
        scores[TrackScoringDimensions.ELIGIBILITY_COMPLIANCE] = await self._score_eligibility_compliance(
            opportunity, profile
        )
        
        # Award Size Compatibility (25% weight)
        scores[TrackScoringDimensions.AWARD_SIZE_COMPATIBILITY] = await self._score_federal_award_size(
            opportunity, profile, enhanced_data
        )
        
        # Agency Alignment (20% weight)
        scores[TrackScoringDimensions.AGENCY_ALIGNMENT] = await self._score_agency_alignment(
            opportunity, profile
        )
        
        # Historical Success (15% weight)
        scores[TrackScoringDimensions.HISTORICAL_SUCCESS] = await self._score_historical_success(
            opportunity, profile, enhanced_data
        )
        
        # Geographic Eligibility (5% weight)
        scores[TrackScoringDimensions.GEOGRAPHIC_ELIGIBILITY] = await self._score_geographic_eligibility(
            opportunity, profile
        )
        
        return scores
    
    async def _score_state_dimensions(
        self,
        opportunity: Dict[str, Any],
        profile: OrganizationProfile,
        enhanced_data: Optional[Dict[str, Any]]
    ) -> Dict[TrackScoringDimensions, float]:
        """Score dimensions specific to State track"""
        
        scores = {}
        
        # Geographic Advantage (35% weight)
        scores[TrackScoringDimensions.GEOGRAPHIC_ADVANTAGE] = await self._score_state_geographic_advantage(
            opportunity, profile
        )
        
        # State Program Alignment (25% weight)
        scores[TrackScoringDimensions.STATE_PROGRAM_ALIGNMENT] = await self._score_state_program_alignment(
            opportunity, profile
        )
        
        # Revenue Compatibility (20% weight)
        scores[TrackScoringDimensions.REVENUE_COMPATIBILITY] = await self._score_state_revenue(
            opportunity, profile, enhanced_data
        )
        
        # Local Network Strength (15% weight)
        scores[TrackScoringDimensions.LOCAL_NETWORK_STRENGTH] = await self._score_local_network_strength(
            opportunity, profile, enhanced_data
        )
        
        # Timing Advantage (5% weight)
        scores[TrackScoringDimensions.TIMING_ADVANTAGE] = await self._score_timing_advantage(
            opportunity
        )
        
        return scores
    
    async def _score_commercial_dimensions(
        self,
        opportunity: Dict[str, Any],
        profile: OrganizationProfile,
        enhanced_data: Optional[Dict[str, Any]]
    ) -> Dict[TrackScoringDimensions, float]:
        """Score dimensions specific to Commercial track"""
        
        scores = {}
        
        # Strategic Partnership Fit (30% weight)
        scores[TrackScoringDimensions.STRATEGIC_PARTNERSHIP_FIT] = await self._score_partnership_fit(
            opportunity, profile
        )
        
        # Revenue Compatibility (25% weight)
        scores[TrackScoringDimensions.REVENUE_COMPATIBILITY] = await self._score_commercial_revenue(
            opportunity, profile, enhanced_data
        )
        
        # Industry Alignment (20% weight)
        scores[TrackScoringDimensions.INDUSTRY_ALIGNMENT] = await self._score_industry_alignment(
            opportunity, profile
        )
        
        # Partnership Potential (15% weight)
        scores[TrackScoringDimensions.PARTNERSHIP_POTENTIAL] = await self._score_partnership_potential(
            opportunity, profile
        )
        
        # Foundation Type Match (10% weight)
        scores[TrackScoringDimensions.FOUNDATION_TYPE_MATCH] = await self._score_foundation_type_match(
            opportunity, profile
        )
        
        return scores
    
    # Individual scoring methods (implementations to follow in next update)
    
    async def _score_ntee_compatibility(self, opportunity, profile, enhanced_data) -> float:
        """Score NTEE code compatibility with detailed matching"""
        score = 0.3  # Base score
        
        opp_ntee = opportunity.get('external_data', {}).get('ntee_code', '')
        if hasattr(profile, 'ntee_codes') and profile.ntee_codes and opp_ntee:
            # Exact match gets full points
            if opp_ntee in profile.ntee_codes:
                score = 1.0
            # Similar codes get partial credit  
            elif any(ntee[:3] == opp_ntee[:3] for ntee in profile.ntee_codes):
                score = 0.8
            # Same category gets some credit
            elif any(ntee[0] == opp_ntee[0] for ntee in profile.ntee_codes):
                score = 0.6
        
        # BMF data enhancement
        if enhanced_data and 'bmf_data' in enhanced_data:
            bmf_ntee = enhanced_data['bmf_data'].get('ntee_code')
            if bmf_ntee and hasattr(profile, 'ntee_codes') and bmf_ntee in profile.ntee_codes:
                score = min(1.0, score + 0.1)
        
        return score
    
    async def _score_program_alignment(self, opportunity, profile) -> float:
        """Score program and activity alignment"""
        score = 0.4  # Base alignment score
        
        if hasattr(profile, 'focus_areas') and profile.focus_areas:
            opp_text = f"{opportunity.get('organization_name', '')} {opportunity.get('description', '')}".lower()
            
            matches = 0
            for focus_area in profile.focus_areas:
                if focus_area.lower() in opp_text:
                    matches += 1
            
            if matches > 0:
                score = min(1.0, 0.4 + matches * 0.2)
        
        return score
    
    async def _score_nonprofit_revenue(self, opportunity, profile, enhanced_data) -> float:
        """Score revenue compatibility for nonprofit track ($50K-$50M range)"""
        org_revenue = 0
        
        # Try to get revenue from multiple sources
        if enhanced_data and 'financial_data' in enhanced_data:
            org_revenue = enhanced_data['financial_data'].get('total_revenue', 0)
        elif enhanced_data and 'bmf_data' in enhanced_data:
            org_revenue = enhanced_data['bmf_data'].get('income_amount', 0)
        else:
            org_revenue = opportunity.get('external_data', {}).get('revenue', 0)
        
        # Score based on nonprofit capacity range
        if org_revenue == 0:
            return 0.5  # No data available
        elif 50000 <= org_revenue <= 50000000:  # Target range
            if org_revenue >= 1000000:  # Large nonprofit
                return 0.9
            elif org_revenue >= 250000:  # Medium nonprofit
                return 0.8
            else:  # Small but viable nonprofit
                return 0.7
        elif org_revenue < 50000:  # Too small
            return 0.3
        else:  # Too large for typical nonprofit grants
            return 0.4
    
    # Placeholder implementations for other scoring methods
    async def _score_geographic_proximity(self, opportunity, profile) -> float:
        return 0.6  # Placeholder
    
    async def _score_board_network_preview(self, opportunity, profile, enhanced_data) -> float:
        return 0.5  # Placeholder - will integrate with network analysis
    
    async def _score_eligibility_compliance(self, opportunity, profile) -> float:
        return 0.7  # Placeholder for federal eligibility
    
    async def _score_federal_award_size(self, opportunity, profile, enhanced_data) -> float:
        return 0.6  # Placeholder for federal award sizing
    
    async def _score_agency_alignment(self, opportunity, profile) -> float:
        return 0.5  # Placeholder for agency mission alignment
    
    async def _score_historical_success(self, opportunity, profile, enhanced_data) -> float:
        return 0.4  # Placeholder for historical federal success
    
    async def _score_geographic_eligibility(self, opportunity, profile) -> float:
        return 0.8  # Placeholder for federal geographic eligibility
    
    async def _score_state_geographic_advantage(self, opportunity, profile) -> float:
        return 0.7  # Placeholder for state geographic scoring
    
    async def _score_state_program_alignment(self, opportunity, profile) -> float:
        return 0.6  # Placeholder for state program alignment
    
    async def _score_state_revenue(self, opportunity, profile, enhanced_data) -> float:
        return 0.5  # Placeholder for state revenue compatibility
    
    async def _score_local_network_strength(self, opportunity, profile, enhanced_data) -> float:
        return 0.4  # Placeholder for local network analysis
    
    async def _score_timing_advantage(self, opportunity) -> float:
        return 0.6  # Placeholder for timing analysis
    
    async def _score_partnership_fit(self, opportunity, profile) -> float:
        return 0.6  # Placeholder for partnership fit
    
    async def _score_commercial_revenue(self, opportunity, profile, enhanced_data) -> float:
        return 0.5  # Placeholder for commercial revenue compatibility
    
    async def _score_industry_alignment(self, opportunity, profile) -> float:
        return 0.5  # Placeholder for industry alignment
    
    async def _score_partnership_potential(self, opportunity, profile) -> float:
        return 0.6  # Placeholder for partnership potential
    
    async def _score_foundation_type_match(self, opportunity, profile) -> float:
        return 0.5  # Placeholder for foundation type matching
    
    # Helper methods
    
    def _calculate_weighted_score(
        self, 
        dimension_scores: Dict[TrackScoringDimensions, float], 
        config: TrackConfiguration
    ) -> float:
        """Calculate overall weighted score using track-specific weights"""
        weighted_sum = sum(
            score * config.scoring_weights[dimension] 
            for dimension, score in dimension_scores.items()
            if dimension in config.scoring_weights
        )
        return min(1.0, weighted_sum)
    
    async def _calculate_revenue_compatibility(
        self,
        opportunity: Dict[str, Any],
        profile: OrganizationProfile,
        config: TrackConfiguration,
        enhanced_data: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate revenue compatibility for the specific track"""
        
        org_revenue = 0
        if enhanced_data and 'financial_data' in enhanced_data:
            org_revenue = enhanced_data['financial_data'].get('total_revenue', 0)
        else:
            org_revenue = opportunity.get('external_data', {}).get('revenue', 0)
        
        if org_revenue == 0:
            return 0.5  # No data available
        
        min_revenue, max_revenue = config.revenue_range
        
        if min_revenue <= org_revenue <= max_revenue:
            return 0.9  # Perfect fit for track
        elif org_revenue < min_revenue:
            # Calculate how far below minimum
            ratio = org_revenue / min_revenue
            return max(0.1, ratio * 0.7)
        else:  # Above maximum
            # Calculate how far above maximum  
            ratio = max_revenue / org_revenue
            return max(0.2, ratio * 0.8)
    
    def _calculate_confidence(
        self,
        dimension_scores: Dict[TrackScoringDimensions, float],
        enhanced_data: Optional[Dict[str, Any]],
        config: TrackConfiguration
    ) -> float:
        """Calculate confidence in the track-specific scoring"""
        base_confidence = 0.6
        
        # Higher confidence with more data
        if enhanced_data:
            data_sources = len(enhanced_data.keys())
            base_confidence += min(0.2, data_sources * 0.05)
        
        # Higher confidence with consistent dimension scores
        if dimension_scores:
            score_variance = np.var(list(dimension_scores.values()))
            if score_variance < 0.1:  # Consistent scores
                base_confidence += 0.1
        
        # Track-specific confidence adjustments
        if config.track == DiscoveryTrack.NONPROFIT_BMF and enhanced_data and 'bmf_data' in enhanced_data:
            base_confidence += 0.1  # BMF data increases nonprofit confidence
        
        return min(1.0, base_confidence)
    
    def _determine_promotion_category(
        self,
        overall_score: float,
        confidence: float,
        config: TrackConfiguration
    ) -> str:
        """Determine promotion category using track-specific thresholds"""
        
        thresholds = config.promotion_thresholds
        
        # Require minimum confidence for auto-promotion
        if overall_score >= thresholds["auto_promote"] and confidence >= 0.8:
            return "auto_promote"
        elif overall_score >= thresholds["high_priority"] and confidence >= 0.6:
            return "high_priority"
        elif overall_score >= thresholds["medium_priority"]:
            return "medium_priority"
        elif overall_score >= thresholds["low_priority"]:
            return "low_priority"
        else:
            return "exclude"
    
    async def _generate_track_factors(
        self,
        opportunity: Dict[str, Any],
        profile: OrganizationProfile,
        config: TrackConfiguration,
        enhanced_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate track-specific factors for analysis"""
        
        factors = {
            "track_name": config.description,
            "primary_filter": config.primary_filter,
            "revenue_range": f"${config.revenue_range[0]:,} - ${config.revenue_range[1]:,}",
            "data_sources": list(enhanced_data.keys()) if enhanced_data else []
        }
        
        # Track-specific factors
        if config.track == DiscoveryTrack.NONPROFIT_BMF:
            factors["bmf_integrated"] = enhanced_data and 'bmf_data' in enhanced_data
            factors["ntee_match"] = self._check_ntee_match(opportunity, profile, enhanced_data)
        elif config.track == DiscoveryTrack.FEDERAL:
            factors["government_eligible"] = True  # Placeholder
            factors["agency_type"] = opportunity.get('agency', 'Unknown')
        
        return factors
    
    def _check_ntee_match(
        self, 
        opportunity: Dict[str, Any], 
        profile: OrganizationProfile, 
        enhanced_data: Optional[Dict[str, Any]]
    ) -> bool:
        """Check for NTEE code match in BMF data"""
        if not hasattr(profile, 'ntee_codes') or not profile.ntee_codes:
            return False
        
        # Check opportunity NTEE
        opp_ntee = opportunity.get('external_data', {}).get('ntee_code', '')
        if opp_ntee and opp_ntee in profile.ntee_codes:
            return True
        
        # Check BMF NTEE if available
        if enhanced_data and 'bmf_data' in enhanced_data:
            bmf_ntee = enhanced_data['bmf_data'].get('ntee_code', '')
            if bmf_ntee and bmf_ntee in profile.ntee_codes:
                return True
        
        return False
    
    def _create_error_result(self, track: DiscoveryTrack, error_msg: str) -> TrackScoringResult:
        """Create error result for failed scoring"""
        return TrackScoringResult(
            track=track,
            overall_score=0.1,
            dimension_scores={},
            confidence_level=0.0,
            revenue_compatibility=0.0,
            track_specific_factors={"error": error_msg},
            promotion_category="exclude",
            scored_at=datetime.now()
        )


def get_track_specific_scorer() -> TrackSpecificScorer:
    """Get singleton instance of track-specific scorer"""
    if not hasattr(get_track_specific_scorer, '_instance'):
        get_track_specific_scorer._instance = TrackSpecificScorer()
    return get_track_specific_scorer._instance