#!/usr/bin/env python3
"""
Discovery Scoring Engine
Unified multi-dimensional scoring system for opportunity evaluation

This scorer evaluates Discovery opportunities across 5 key dimensions:
1. Base Compatibility - Core match between opportunity and profile
2. Financial Viability - Award size vs organization capacity  
3. Geographic Advantage - Location-based competitive advantage
4. Timing Score - Deadline urgency and preparation time
5. Strategic Alignment - Mission and program area alignment
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

from src.profiles.models import OrganizationProfile
from src.core.unified_scorer_interface import (
    UnifiedScorerInterface, ScorerType, WorkflowStage, 
    ScoringDimension, ScoringResult as UnifiedScoringResult,
    ScoringContext, scorer_factory
)

logger = logging.getLogger(__name__)


class OpportunityType(Enum):
    """Types of opportunities for specialized scoring"""
    NONPROFIT = "nonprofit"
    GOVERNMENT = "government" 
    FOUNDATION = "foundation"
    STATE = "state"
    COMMERCIAL = "commercial"


class ScoringDimensions(Enum):
    """Five core scoring dimensions"""
    BASE_COMPATIBILITY = "base_compatibility"
    FINANCIAL_VIABILITY = "financial_viability"
    GEOGRAPHIC_ADVANTAGE = "geographic_advantage"
    TIMING_SCORE = "timing_score"
    STRATEGIC_ALIGNMENT = "strategic_alignment"


@dataclass
class ScoringResult:
    """Comprehensive scoring result with breakdown"""
    overall_score: float
    dimension_scores: Dict[ScoringDimensions, float]
    confidence_level: float
    boost_factors: Dict[str, float]
    scoring_metadata: Dict[str, Any]
    scored_at: datetime
    
    @property
    def promotion_recommended(self) -> bool:
        """Whether this score recommends promotion to Qualified Prospects"""
        return self.overall_score >= 0.65
    
    @property
    def auto_promotion_threshold(self) -> bool:
        """Whether this score meets auto-promotion threshold"""
        return self.overall_score >= 0.75  # Lowered from 0.80 to catch more high-scoring opportunities


class DiscoveryScorer(UnifiedScorerInterface):
    """Unified discovery opportunity scoring engine"""
    
    def __init__(self):
        super().__init__()
        self.scorer_type = ScorerType.DISCOVERY
        self.supported_stages = [WorkflowStage.DISCOVER]
        
        # Define scoring dimensions with metadata
        self.scoring_dimensions = [
            ScoringDimension("base_compatibility", 0.35, "Core match between opportunity and profile", 
                           "ntee_alignment_analysis", ["ntee_codes", "organization_name", "description"]),
            ScoringDimension("strategic_alignment", 0.25, "Mission and program area alignment",
                           "focus_area_matching", ["focus_areas", "mission_statement", "keywords"]),
            ScoringDimension("geographic_advantage", 0.20, "Location-based competitive advantage",
                           "geographic_proximity_analysis", ["state", "geographic_scope"]),
            ScoringDimension("timing_score", 0.12, "Deadline urgency and preparation time",
                           "deadline_analysis", ["application_deadline", "posting_date"]),
            ScoringDimension("financial_viability", 0.08, "Award size vs organization capacity",
                           "financial_capacity_matching", ["funding_amount", "total_revenue"])
        ]
        
        # Dimension weights optimized for discovery stage
        self.dimension_weights = {
            ScoringDimensions.BASE_COMPATIBILITY: 0.35,  # Most important at discovery
            ScoringDimensions.STRATEGIC_ALIGNMENT: 0.25,  # High value for filtering
            ScoringDimensions.GEOGRAPHIC_ADVANTAGE: 0.20, # Based on VA concentration
            ScoringDimensions.TIMING_SCORE: 0.12,         # Important but not critical
            ScoringDimensions.FINANCIAL_VIABILITY: 0.08   # Less critical at discovery
        }
        
        # Boost factors for enhanced data
        self.boost_factors = {
            "has_990_data": 0.10,           # Financial data available
            "exact_ntee_match": 0.15,       # Perfect program alignment
            "board_connections": 0.05,      # Shared board members
            "historical_success": 0.08,     # Past award history
            "geographic_priority": 0.03     # Target state preference
        }
        
        # Confidence thresholds
        self.confidence_thresholds = {
            "high": 0.85,    # Strong confidence in score
            "medium": 0.65,  # Moderate confidence
            "low": 0.45      # Low confidence
        }
    
    async def score_opportunity(
        self, 
        opportunity: Dict[str, Any], 
        profile: OrganizationProfile,
        enhanced_data: Optional[Dict[str, Any]] = None
    ) -> ScoringResult:
        """
        Score a discovery opportunity against an organization profile
        
        Args:
            opportunity: Opportunity data from discovery
            profile: Organization profile for matching
            enhanced_data: Optional 990/990-PF data for boost factors
            
        Returns:
            ScoringResult with comprehensive scoring breakdown
        """
        try:
            logger.info(f"Scoring opportunity {opportunity.get('organization_name')} for profile {profile.profile_id}")
            
            # Determine opportunity type for specialized scoring
            opp_type = self._determine_opportunity_type(opportunity)
            
            # Calculate dimension scores
            dimension_scores = await self._calculate_dimension_scores(
                opportunity, profile, opp_type, enhanced_data
            )
            
            # Calculate overall weighted score
            overall_score = self._calculate_weighted_score(dimension_scores)
            
            # Apply boost factors if enhanced data available
            boost_factors = self._calculate_boost_factors(opportunity, profile, enhanced_data)
            boosted_score = min(1.0, overall_score + sum(boost_factors.values()))
            
            # Calculate confidence level
            confidence = self._calculate_confidence_level(dimension_scores, enhanced_data)
            
            # Create scoring metadata
            metadata = {
                "opportunity_type": opp_type.value,
                "profile_id": profile.profile_id,
                "scoring_version": "1.0.0",
                "dimension_weights": {dim.value: weight for dim, weight in self.dimension_weights.items()},
                "data_completeness": self._assess_data_completeness(opportunity, enhanced_data)
            }
            
            return ScoringResult(
                overall_score=boosted_score,
                dimension_scores=dimension_scores,
                confidence_level=confidence,
                boost_factors=boost_factors,
                scoring_metadata=metadata,
                scored_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error scoring opportunity: {e}")
            # Return default low score on error
            return ScoringResult(
                overall_score=0.1,
                dimension_scores={dim: 0.1 for dim in ScoringDimensions},
                confidence_level=0.0,
                boost_factors={},
                scoring_metadata={"error": str(e)},
                scored_at=datetime.now()
            )
    
    def _determine_opportunity_type(self, opportunity: Dict[str, Any]) -> OpportunityType:
        """Determine opportunity type for specialized scoring"""
        source_type = opportunity.get('source_type', '').lower()
        discovery_source = opportunity.get('discovery_source', '').lower()
        
        if 'nonprofit' in source_type or 'bmf' in discovery_source:
            return OpportunityType.NONPROFIT
        elif 'government' in source_type or 'grants.gov' in discovery_source:
            return OpportunityType.GOVERNMENT
        elif 'foundation' in source_type or 'pf' in discovery_source:
            return OpportunityType.FOUNDATION
        elif 'state' in source_type or 'va_state' in discovery_source:
            return OpportunityType.STATE
        else:
            return OpportunityType.COMMERCIAL
    
    async def _calculate_dimension_scores(
        self, 
        opportunity: Dict[str, Any], 
        profile: OrganizationProfile,
        opp_type: OpportunityType,
        enhanced_data: Optional[Dict[str, Any]]
    ) -> Dict[ScoringDimensions, float]:
        """Calculate scores for each dimension"""
        
        scores = {}
        
        # Base Compatibility - core match assessment
        scores[ScoringDimensions.BASE_COMPATIBILITY] = await self._score_base_compatibility(
            opportunity, profile, opp_type
        )
        
        # Financial Viability - award size vs capacity
        scores[ScoringDimensions.FINANCIAL_VIABILITY] = await self._score_financial_viability(
            opportunity, profile, enhanced_data
        )
        
        # Geographic Advantage - location benefits
        scores[ScoringDimensions.GEOGRAPHIC_ADVANTAGE] = await self._score_geographic_advantage(
            opportunity, profile
        )
        
        # Timing Score - deadline and urgency
        scores[ScoringDimensions.TIMING_SCORE] = await self._score_timing(
            opportunity
        )
        
        # Strategic Alignment - mission and program fit
        scores[ScoringDimensions.STRATEGIC_ALIGNMENT] = await self._score_strategic_alignment(
            opportunity, profile, opp_type
        )
        
        return scores
    
    async def _score_base_compatibility(
        self, opportunity: Dict[str, Any], profile: OrganizationProfile, opp_type: OpportunityType
    ) -> float:
        """Score basic compatibility between opportunity and profile"""
        score = 0.5  # Base score
        
        # NTEE code alignment for nonprofits
        if hasattr(profile, 'ntee_codes') and profile.ntee_codes:
            opp_ntee = opportunity.get('external_data', {}).get('ntee_code', '')
            if opp_ntee and any(ntee in opp_ntee for ntee in profile.ntee_codes):
                score += 0.3
        
        # Government criteria alignment for government opportunities
        if opp_type == OpportunityType.GOVERNMENT and hasattr(profile, 'government_criteria'):
            # Check for matching criteria in opportunity description/eligibility
            opp_text = f"{opportunity.get('organization_name', '')} {opportunity.get('description', '')}".lower()
            matching_criteria = sum(1 for criteria in profile.government_criteria 
                                  if criteria.lower() in opp_text)
            if matching_criteria > 0:
                score += min(0.4, matching_criteria * 0.1)
        
        # Revenue size compatibility
        org_revenue = opportunity.get('external_data', {}).get('revenue', 0)
        if org_revenue > 0:
            if 50000 <= org_revenue <= 50000000:  # Reasonable nonprofit range
                score += 0.2
        
        return min(1.0, score)
    
    async def _score_financial_viability(
        self, opportunity: Dict[str, Any], profile: OrganizationProfile, enhanced_data: Optional[Dict[str, Any]]
    ) -> float:
        """Score financial viability and capacity match"""
        score = 0.6  # Neutral default
        
        # Use enhanced 990 data if available
        if enhanced_data and 'financial_data' in enhanced_data:
            financial_data = enhanced_data['financial_data']
            total_revenue = financial_data.get('total_revenue', 0)
            
            # Score based on organizational capacity
            if total_revenue > 0:
                if total_revenue >= 1000000:  # Large organization
                    score = 0.9
                elif total_revenue >= 250000:   # Medium organization
                    score = 0.8
                elif total_revenue >= 50000:    # Small organization
                    score = 0.7
                else:                           # Very small organization
                    score = 0.5
        
        # Award amount vs capacity (if available)
        award_amount = opportunity.get('funding_amount') or opportunity.get('external_data', {}).get('award_amount', 0)
        if award_amount > 0 and enhanced_data:
            org_revenue = enhanced_data.get('financial_data', {}).get('total_revenue', 0)
            if org_revenue > 0:
                ratio = award_amount / org_revenue
                if 0.1 <= ratio <= 0.5:  # Reasonable award to revenue ratio
                    score += 0.1
        
        return min(1.0, score)
    
    async def _score_geographic_advantage(
        self, opportunity: Dict[str, Any], profile: OrganizationProfile
    ) -> float:
        """Score geographic advantages and eligibility"""
        score = 0.5  # Base score
        
        opp_state = opportunity.get('external_data', {}).get('state', '').upper()
        profile_state = getattr(profile, 'state', '').upper()
        
        # Same state advantage
        if opp_state and profile_state and opp_state == profile_state:
            score += 0.4
        
        # Virginia preference (based on analysis showing VA concentration)
        if profile_state == 'VA':
            score += 0.1
        
        return min(1.0, score)
    
    async def _score_timing(self, opportunity: Dict[str, Any]) -> float:
        """Score timing factors like deadlines and urgency"""
        score = 0.7  # Default good timing
        
        # Check for deadline information
        deadline_str = opportunity.get('external_data', {}).get('deadline') or opportunity.get('deadline')
        if deadline_str:
            try:
                # Try to parse deadline
                if isinstance(deadline_str, str):
                    # Simple date parsing - could be enhanced
                    if 'days' in deadline_str.lower() or 'week' in deadline_str.lower():
                        score = 0.9  # Good timing for application
                    elif 'month' in deadline_str.lower():
                        score = 0.8  # Reasonable timing
                    elif 'year' in deadline_str.lower():
                        score = 0.6  # Distant deadline
            except:
                pass
        
        return min(1.0, score)
    
    async def _score_strategic_alignment(
        self, opportunity: Dict[str, Any], profile: OrganizationProfile, opp_type: OpportunityType
    ) -> float:
        """Score strategic alignment with mission and focus areas"""
        score = 0.5  # Base alignment
        
        # Focus area alignment
        if hasattr(profile, 'focus_areas') and profile.focus_areas:
            opp_text = f"{opportunity.get('organization_name', '')} {opportunity.get('description', '')}".lower()
            
            for focus_area in profile.focus_areas:
                if focus_area.lower() in opp_text:
                    score += 0.15
        
        # Mission statement keyword alignment
        if hasattr(profile, 'mission_statement') and profile.mission_statement:
            mission_keywords = profile.mission_statement.lower().split()
            opp_text = f"{opportunity.get('organization_name', '')} {opportunity.get('description', '')}".lower()
            
            keyword_matches = sum(1 for keyword in mission_keywords 
                                if len(keyword) > 4 and keyword in opp_text)
            if keyword_matches > 0:
                score += min(0.3, keyword_matches * 0.05)
        
        return min(1.0, score)
    
    def _calculate_weighted_score(self, dimension_scores: Dict[ScoringDimensions, float]) -> float:
        """Calculate overall weighted score from dimension scores"""
        weighted_sum = sum(
            score * self.dimension_weights[dimension] 
            for dimension, score in dimension_scores.items()
        )
        return min(1.0, weighted_sum)
    
    def _calculate_boost_factors(
        self, opportunity: Dict[str, Any], profile: OrganizationProfile, enhanced_data: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate boost factors from enhanced data"""
        boosts = {}
        
        if enhanced_data:
            # 990 data available boost
            if 'financial_data' in enhanced_data:
                boosts['has_990_data'] = self.boost_factors['has_990_data']
            
            # Exact NTEE match boost
            if 'ntee_exact_match' in enhanced_data and enhanced_data['ntee_exact_match']:
                boosts['exact_ntee_match'] = self.boost_factors['exact_ntee_match']
            
            # Board connections boost
            if 'board_connections' in enhanced_data and enhanced_data['board_connections']:
                boosts['board_connections'] = self.boost_factors['board_connections']
        
        return boosts
    
    def _calculate_confidence_level(
        self, dimension_scores: Dict[ScoringDimensions, float], enhanced_data: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate confidence level in the scoring"""
        base_confidence = 0.6
        
        # Higher confidence with more data
        if enhanced_data:
            base_confidence += 0.2
        
        # Higher confidence with consistent dimension scores
        score_variance = np.var(list(dimension_scores.values()))
        if score_variance < 0.1:  # Low variance = consistent scores
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _assess_data_completeness(
        self, opportunity: Dict[str, Any], enhanced_data: Optional[Dict[str, Any]]
    ) -> float:
        """Assess completeness of available data for scoring"""
        completeness = 0.5  # Base completeness
        
        # Required fields present
        required_fields = ['organization_name', 'source_type']
        present_fields = sum(1 for field in required_fields if opportunity.get(field))
        completeness += (present_fields / len(required_fields)) * 0.3
        
        # Enhanced data available
        if enhanced_data:
            completeness += 0.2
        
        return min(1.0, completeness)
    
    # Unified Interface Implementation
    
    async def score(self, 
                   opportunity_data: Dict[str, Any],
                   profile_data: Dict[str, Any], 
                   context: ScoringContext) -> UnifiedScoringResult:
        """
        Unified interface score method with enhanced caching
        
        Args:
            opportunity_data: Opportunity information to score
            profile_data: Organization profile to score against
            context: Scoring context and metadata
            
        Returns:
            UnifiedScoringResult with standardized 0-1 score and metadata
        """
        start_time = datetime.now()
        
        try:
            # Try to get cached result first
            cached_result = await self.get_cached_score(opportunity_data, profile_data, context)
            if cached_result:
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                self.update_performance_metrics(processing_time, cache_hit=True, error=False)
                
                # Convert cached result back to UnifiedScoringResult
                return UnifiedScoringResult(
                    overall_score=cached_result['overall_score'],
                    dimension_scores=cached_result['dimension_scores'],
                    confidence_level=cached_result['confidence_level'],
                    metadata=cached_result['metadata'],
                    scorer_type=self.scorer_type,
                    workflow_stage=context.workflow_stage,
                    scoring_timestamp=datetime.fromisoformat(cached_result['scoring_timestamp']),
                    processing_time_ms=cached_result['processing_time_ms'],
                    data_quality_score=cached_result['data_quality_score']
                )
            # Convert profile_data to OrganizationProfile if needed
            if isinstance(profile_data, dict):
                profile = OrganizationProfile(**profile_data)
            else:
                profile = profile_data
            
            # Use existing scoring method
            result = await self.score_opportunity(
                opportunity_data, profile, context.enhanced_data
            )
            
            # Convert to unified result format
            dimension_scores_dict = {dim.value: score for dim, score in result.dimension_scores.items()}
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            unified_result = UnifiedScoringResult(
                overall_score=result.overall_score,
                dimension_scores=dimension_scores_dict,
                confidence_level=result.confidence_level,
                metadata={
                    **result.scoring_metadata,
                    'boost_factors': result.boost_factors,
                    'opportunity_type': result.scoring_metadata.get('opportunity_type'),
                    'promotion_recommended': result.promotion_recommended,
                    'auto_promotion_eligible': result.auto_promotion_threshold
                },
                scorer_type=self.scorer_type,
                workflow_stage=context.workflow_stage,
                scoring_timestamp=result.scored_at,
                processing_time_ms=processing_time,
                data_quality_score=result.scoring_metadata.get('data_completeness', 0.5)
            )
            
            # Cache the result for future use
            cache_success = await self.cache_score(opportunity_data, profile_data, context, unified_result)
            
            # Update performance metrics  
            self.update_performance_metrics(processing_time, cache_hit=False, error=False)
            
            return unified_result
            
        except Exception as e:
            logger.error(f"Error in unified scoring: {e}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Update performance metrics with error
            self.update_performance_metrics(processing_time, False, True)
            
            # Return error result
            return UnifiedScoringResult(
                overall_score=0.1,
                dimension_scores={dim.name: 0.1 for dim in self.scoring_dimensions},
                confidence_level=0.0,
                metadata={'error': str(e)},
                scorer_type=self.scorer_type,
                workflow_stage=context.workflow_stage,
                scoring_timestamp=datetime.now(),
                processing_time_ms=processing_time,
                data_quality_score=0.0
            )
    
    def get_scoring_dimensions(self) -> List[ScoringDimension]:
        """Get the scoring dimensions used by this scorer"""
        return self.scoring_dimensions
    
    def validate_input_data(self, 
                          opportunity_data: Dict[str, Any],
                          profile_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that required data is present for scoring
        
        Returns:
            (is_valid, list_of_missing_fields)
        """
        missing_fields = []
        
        # Check required opportunity fields
        required_opp_fields = ['organization_name', 'source_type']
        for field in required_opp_fields:
            if not opportunity_data.get(field):
                missing_fields.append(f"opportunity.{field}")
        
        # Check required profile fields
        required_profile_fields = ['profile_id', 'organization_name']
        for field in required_profile_fields:
            if isinstance(profile_data, dict):
                if not profile_data.get(field):
                    missing_fields.append(f"profile.{field}")
            else:
                if not hasattr(profile_data, field) or not getattr(profile_data, field):
                    missing_fields.append(f"profile.{field}")
        
        return len(missing_fields) == 0, missing_fields


def get_discovery_scorer() -> DiscoveryScorer:
    """Get singleton instance of discovery scorer"""
    if not hasattr(get_discovery_scorer, '_instance'):
        get_discovery_scorer._instance = DiscoveryScorer()
    return get_discovery_scorer._instance


# Register the scorer with the factory
scorer_factory.register_scorer(ScorerType.DISCOVERY, DiscoveryScorer)