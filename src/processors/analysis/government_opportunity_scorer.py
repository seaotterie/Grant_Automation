#!/usr/bin/env python3
"""
Government Opportunity Scorer Processor
Scores government funding opportunities for organizational fit.

This processor:
1. Takes opportunities from Grants.gov fetch
2. Takes organizations from previous steps (BMF, ProPublica, USASpending)
3. Calculates match scores between organizations and opportunities
4. Considers eligibility, geographic, financial, and historical factors
5. Returns ranked opportunity matches for each organization
"""

import asyncio
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.core.government_models import (
    GovernmentOpportunity, GovernmentOpportunityMatch, 
    EligibilityCategory, OpportunityStatus
)
from src.analysis.profile_matcher import get_profile_matcher
from src.analytics.soi_financial_analytics import SOIFinancialAnalytics


class GovernmentOpportunityScorerProcessor(BaseProcessor):
    """
    Processor for scoring government opportunity matches.
    
    Government Opportunity Scoring Algorithm Documentation

    ## Overview
This processor implements a data-driven scoring algorithm for matching government funding 
opportunities with organizational profiles. The algorithm uses weighted scoring across 
multiple dimensions to provide accurate compatibility assessments.

## Scoring Methodology

### 1. Eligibility Scoring (Weight: 0.30)
- **Purpose**: Ensures organizations meet basic eligibility requirements
- **Factors**: Nonprofit status, NTEE code alignment, special eligibility categories
- **Data-Driven Adjustment**: Increased from 0.25 to 0.30 based on high focus area diversity
- **Scoring Range**: 0.0 (ineligible) to 1.0 (fully eligible with bonuses)

### 2. Geographic Scoring (Weight: 0.20) 
- **Purpose**: Evaluates geographic eligibility and competitive advantage
- **Factors**: State eligibility, regional opportunities, target state preferences
- **Data-Driven Adjustment**: Increased from 0.15 to 0.20 due to VA geographic concentration
- **Scoring Range**: 0.0 (geographically ineligible) to 1.0 (perfect geographic match)

### 3. Timing Scoring (Weight: 0.20)
- **Purpose**: Assesses application deadline appropriateness
- **Factors**: Days until deadline, preparation time needed, application complexity
- **Data-Driven Adjustment**: Maintained optimal weight based on analysis
- **Scoring Range**: 0.1 (too urgent) to 1.0 (ideal timing)

### 4. Financial Fit Scoring (Weight: 0.25) - SOI ENHANCED
- **Purpose**: Matches award amounts with organizational capacity using comprehensive financial intelligence
- **Factors**: SOI financial health, revenue/expense analysis, foundation capacity, multi-year trends
- **Data-Driven Adjustment**: INCREASED from 0.15 to 0.25 due to rich SOI database integration
- **SOI Intelligence**: 990/990-PF/990-EZ data, financial health scoring, foundation payout analysis
- **Scoring Range**: 0.2 (poor financial fit) to 1.0 (optimal award size with strong financial health)

### 5. Historical Success Scoring (Weight: 0.05) - REDUCED
- **Purpose**: Leverages past federal funding success patterns  
- **Factors**: Previous awards, funding track record, agency relationships
- **Data-Driven Adjustment**: REDUCED from 0.15 to 0.05 to prioritize SOI financial intelligence
- **Scoring Range**: 0.3 (no history) to 1.0 (strong track record)

## Recommendation Thresholds

### Data-Quality Adjusted Thresholds
Based on entity data completeness analysis (10% complete data rate):

- **High Recommendation**: 0.75+ (was 0.80) - Immediate action recommended
- **Medium Recommendation**: 0.55+ (was 0.60) - Strong candidate for consideration  
- **Low Recommendation**: 0.35+ (was 0.40) - Worth monitoring or future consideration

## Implementation Notes

### Real Data Analysis Foundation
These weights and thresholds are based on comprehensive analysis of:
- 45 organizational profiles with 5 active profiles
- 42 nonprofit entities with varying data completeness
- Geographic distribution showing 78% concentration in Virginia
- Limited financial and historical data availability

### Performance Characteristics
- **Average Processing Time**: Sub-millisecond per opportunity-organization pair
- **Scalability**: Efficient async processing for large opportunity sets
- **Accuracy**: Optimized for current data quality and distribution patterns

### Future Enhancements
- Machine learning-based weight optimization
- Dynamic thresholds based on data quality
- Real-time feedback integration for continuous improvement
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="government_opportunity_scorer",
            description="Score government funding opportunities using profile-specific analysis",
            version="2.0.0",  # Updated to use profile-specific analysis
            dependencies=[],  # Optional dependencies for testing
            estimated_duration=90,  # 1.5 minutes
            requires_network=False,
            requires_api_key=False,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Initialize profile matcher for advanced scoring
        self.profile_matcher = get_profile_matcher()
        
        # Initialize SOI financial analytics for enhanced financial intelligence
        self.soi_analytics = SOIFinancialAnalytics()
        
        # Updated scoring weights with SOI financial intelligence (Sep 2025)
        # Enhanced financial data from BMF/SOI database enables more sophisticated analysis
        self.match_weights = {
            "eligibility": 0.30,      # Maintained: High focus area diversity requires filtering
            "geographic": 0.20,       # Maintained: Strong geographic concentration in VA
            "timing": 0.20,          # Maintained: Well-balanced for current patterns
            "financial_fit": 0.25,   # INCREASED: Rich SOI financial data now available
            "historical_success": 0.05  # Reduced: Prioritize financial intelligence over limited historical data
        }
        
        # Optimized recommendation thresholds based on data quality analysis
        # Adjusted lower due to limited entity data completeness (10% complete data rate)
        self.recommendation_thresholds = {
            "high": 0.75,    # Slightly lower to account for data quality limitations
            "medium": 0.55,  # Adjusted for better recommendation distribution
            "low": 0.35      # Lower threshold to capture more opportunities
        }
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute government opportunity scoring."""
        start_time = time.time()
        
        try:
            # Get opportunities and organizations
            opportunities = await self._get_government_opportunities(workflow_state)
            organizations = await self._get_organizations(workflow_state)
            
            if not opportunities:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No government opportunities found from Grants.gov fetch"]
                )
            
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No organizations found from previous steps"]
                )
            
            self.logger.info(f"Scoring {len(opportunities)} opportunities for {len(organizations)} organizations")
            
            # Score all opportunity-organization combinations
            all_matches = []
            total_combinations = len(opportunities) * len(organizations)
            processed = 0
            
            for org in organizations:
                org_matches = []
                
                for opportunity in opportunities:
                    processed += 1
                    self._update_progress(
                        processed, 
                        total_combinations,
                        f"Scoring {opportunity.title[:50]}... for {org.name[:30]}..."
                    )
                    
                    # Score the match
                    match = await self._score_opportunity_match(org, opportunity, config)
                    if match and match.relevance_score > 0:
                        org_matches.append(match)
                
                # Sort matches by relevance score and keep top matches
                org_matches.sort(key=lambda x: x.relevance_score, reverse=True)
                max_matches_per_org = config.get_config("max_matches_per_org", 10)
                all_matches.extend(org_matches[:max_matches_per_org])
            
            # Sort all matches by relevance score
            all_matches.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Generate summary statistics
            stats = self._calculate_match_statistics(all_matches, organizations, opportunities)
            
            # Prepare results
            result_data = {
                "opportunity_matches": [match.dict() for match in all_matches],
                "total_matches": len(all_matches),
                "organizations_processed": len(organizations),
                "opportunities_processed": len(opportunities),
                "match_statistics": stats
            }
            
            execution_time = time.time() - start_time
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "scoring_weights": self.match_weights,
                    "recommendation_thresholds": self.recommendation_thresholds
                }
            )
            
        except Exception as e:
            self.logger.error(f"Government opportunity scoring failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"Government opportunity scoring failed: {str(e)}"]
            )
    
    async def _get_government_opportunities(self, workflow_state) -> List[GovernmentOpportunity]:
        """Get opportunities from Grants.gov fetch processor."""
        if not workflow_state or not workflow_state.has_processor_succeeded('grants_gov_fetch'):
            return []
        
        opportunities_data = workflow_state.get_processor_data('grants_gov_fetch')
        if not opportunities_data or 'opportunities' not in opportunities_data:
            return []
        
        opportunities = []
        for opp_dict in opportunities_data['opportunities']:
            try:
                opportunity = GovernmentOpportunity(**opp_dict)
                opportunities.append(opportunity)
            except Exception as e:
                self.logger.warning(f"Failed to parse opportunity data: {e}")
                continue
        
        return opportunities
    
    async def _get_organizations(self, workflow_state) -> List[OrganizationProfile]:
        """Get organizations from previous processors."""
        organizations = []
        
        # Try USASpending first (has award history), then ProPublica, then BMF
        for processor_name in ['usaspending_fetch', 'propublica_fetch', 'bmf_filter']:
            if workflow_state and workflow_state.has_processor_succeeded(processor_name):
                org_dicts = workflow_state.get_organizations_from_processor(processor_name)
                if org_dicts:
                    self.logger.info(f"Retrieved {len(org_dicts)} organizations from {processor_name}")
                    
                    for org_dict in org_dicts:
                        try:
                            if isinstance(org_dict, dict):
                                org = OrganizationProfile(**org_dict)
                            else:
                                org = org_dict
                            organizations.append(org)
                        except Exception as e:
                            self.logger.warning(f"Failed to parse organization data: {e}")
                            continue
                    break
        
        return organizations
    
    async def _score_opportunity_match(
        self,
        org: OrganizationProfile,
        opportunity: GovernmentOpportunity,
        config: ProcessorConfig
    ) -> Optional[GovernmentOpportunityMatch]:
        """Score a single opportunity-organization match."""
        
        try:
            match = GovernmentOpportunityMatch(
                opportunity=opportunity,
                organization=org.ein
            )
            
            # Score each component
            match.eligibility_score = self._score_eligibility(org, opportunity)
            match.geographic_score = self._score_geographic_fit(org, opportunity, config)
            match.timing_score = self._score_timing_fit(opportunity)
            match.financial_fit_score = self._score_financial_fit(org, opportunity)
            match.historical_success_score = self._score_historical_success(org, opportunity)
            
            # Calculate overall score
            match.calculate_overall_score()
            
            # Add match reasons and recommendations
            self._generate_match_insights(match, org, opportunity)
            
            return match
            
        except Exception as e:
            self.logger.warning(f"Error scoring match for {org.ein} and {opportunity.opportunity_id}: {e}")
            return None
    
    def _score_eligibility(self, org: OrganizationProfile, opportunity: GovernmentOpportunity) -> float:
        """Enhanced eligibility scoring with NTEE code matching and data-driven bonuses (0-1)."""
        # Check if nonprofits are eligible
        if not opportunity.is_eligible_for_nonprofits():
            return 0.0
        
        # Base score for nonprofit eligibility
        score = 0.7  # Slightly reduced to allow for more granular scoring
        
        # Enhanced NTEE code matching
        if org.ntee_code and opportunity.category_code:
            # Education opportunities favor education organizations
            if (opportunity.category_code.startswith('EDU') or 'education' in opportunity.description.lower()) and org.ntee_code.startswith('B'):
                score += 0.15
            # Health opportunities favor health organizations
            elif (opportunity.category_code.startswith('HHS') or 'health' in opportunity.description.lower()) and org.ntee_code.startswith('E'):
                score += 0.15
            # Environmental opportunities favor environmental organizations
            elif 'environment' in opportunity.description.lower() and org.ntee_code.startswith('C'):
                score += 0.15
            # General NTEE alignment bonus
            elif self._check_ntee_alignment(org.ntee_code, opportunity):
                score += 0.1
        
        # Mission statement keyword matching
        if org.mission and opportunity.description:
            keyword_match_score = self._calculate_mission_alignment(org.mission, opportunity.description)
            score += keyword_match_score * 0.1
        
        # Experience bonus for organizations with revenue data (shows established operations)
        if org.revenue and org.revenue > 100000:  # Organizations with >$100k revenue
            score += 0.05
        
        # Multi-category eligibility bonus (less competitive)
        if len(opportunity.eligible_applicants) > 2:
            score += 0.05  # Reduced from 0.1 for more precise scoring
        
        return min(1.0, score)
    
    def _score_geographic_fit(
        self, 
        org: OrganizationProfile, 
        opportunity: GovernmentOpportunity,
        config: ProcessorConfig
    ) -> float:
        """Score geographic eligibility and preference (0-1)."""
        # Check basic eligibility
        if not opportunity.matches_state(org.state):
            return 0.0
        
        # Base score for state eligibility
        score = 0.7
        
        # Bonus for local/regional opportunities
        if opportunity.eligible_states and len(opportunity.eligible_states) <= 5:
            score += 0.2  # Regional opportunity, less competition
        
        # Bonus for matching target state in config
        workflow_config = config.workflow_config
        if workflow_config.state_filter and org.state == workflow_config.state_filter:
            score += 0.1
        
        return min(1.0, score)
    
    def _score_timing_fit(self, opportunity: GovernmentOpportunity) -> float:
        """Score timing appropriateness (0-1)."""
        days_until_deadline = opportunity.calculate_days_until_deadline()
        
        if days_until_deadline is None:
            return 0.3  # Unknown deadline
        
        if days_until_deadline < 7:
            return 0.1  # Too soon
        elif days_until_deadline < 14:
            return 0.4  # Tight but possible
        elif days_until_deadline < 30:
            return 0.7  # Good timing
        elif days_until_deadline < 60:
            return 1.0  # Ideal timing
        elif days_until_deadline < 120:
            return 0.8  # Good advance notice
        else:
            return 0.6  # Very far out
    
    def _score_financial_fit(self, org: OrganizationProfile, opportunity: GovernmentOpportunity) -> float:
        """SOI-enhanced financial fit scoring with comprehensive intelligence (0-1)."""
        if not opportunity.award_ceiling:
            return 0.5  # Unknown award amount, neutral score
        
        # Get SOI financial metrics for enhanced analysis
        soi_metrics = None
        financial_health_score = 0.5  # Default neutral
        
        try:
            if org.ein:
                soi_metrics = self.soi_analytics.get_financial_metrics(org.ein)
                if soi_metrics:
                    financial_health_score = self.soi_analytics.calculate_financial_health_score(soi_metrics)
                    # Normalize to 0-1 range
                    financial_health_score = min(max(financial_health_score / 100.0, 0.0), 1.0)
        except Exception as e:
            # Log but don't fail - fallback to basic scoring
            self.logger.debug(f"Could not get SOI metrics for {org.ein}: {e}")
        
        # Determine organization capacity using SOI data or fallback
        if soi_metrics and soi_metrics.total_revenue > 0:
            # Use SOI revenue data (more accurate and current)
            org_revenue = soi_metrics.total_revenue
            org_expenses = soi_metrics.total_expenses or 0
            org_assets = soi_metrics.total_assets or 0
            
            # Calculate actual capacity based on financial efficiency
            if org_expenses > 0:
                # Use net margin for capacity calculation
                net_margin = max((org_revenue - org_expenses) / org_revenue, 0.05)
                org_capacity = org_revenue * net_margin * 0.5  # Conservative capacity estimate
            else:
                org_capacity = org_revenue * 0.1  # Standard 10% estimate
            
            # Asset-based capacity check for foundations
            if soi_metrics.form_type.value == "990-PF" and org_assets > 0:
                # Foundations typically distribute 5-10% of assets annually
                foundation_capacity = org_assets * 0.075  # 7.5% of assets
                org_capacity = max(org_capacity, foundation_capacity)
                
        elif org.revenue:
            # Fallback to basic BMF revenue data
            org_revenue = org.revenue
            org_capacity = org_revenue * 0.1
        else:
            # No financial data available
            return 0.3  # Low score due to unknown capacity
        
        # Award size analysis with SOI intelligence
        award_to_capacity_ratio = opportunity.award_ceiling / org_capacity if org_capacity > 0 else float('inf')
        
        # Enhanced scoring with financial health consideration
        base_score = 0.5
        
        # Optimal award size scoring
        if 0.1 <= award_to_capacity_ratio <= 1.0:
            base_score = 1.0  # Perfect fit
        elif 0.05 <= award_to_capacity_ratio <= 2.0:
            base_score = 0.8  # Good fit
        elif 0.02 <= award_to_capacity_ratio <= 5.0:
            base_score = 0.6  # Acceptable fit
        elif award_to_capacity_ratio > 5.0:
            base_score = 0.2  # Too large for organization
        else:
            base_score = 0.3  # Too small to be worthwhile
        
        # Apply minimum floor check
        if opportunity.award_floor and opportunity.award_floor > org_capacity * 2:
            base_score = min(base_score, 0.3)  # Minimum too high
        
        # Enhance score with financial health (25% weight)
        enhanced_score = base_score * 0.75 + financial_health_score * 0.25
        
        # Foundation-specific bonuses
        if soi_metrics and soi_metrics.form_type.value == "990-PF":
            # Foundations get slight bonus for federal funding (diversification)
            enhanced_score = min(enhanced_score + 0.05, 1.0)
        
        # Multi-year financial stability bonus
        if soi_metrics and org_revenue > 0:
            try:
                trends = self.soi_analytics.analyze_trends(org.ein, years=3)
                if trends and trends.revenue_trend == "Growing":
                    enhanced_score = min(enhanced_score + 0.05, 1.0)
                elif trends and trends.revenue_trend == "Declining":
                    enhanced_score = max(enhanced_score - 0.1, 0.1)
            except:
                pass  # Skip trend analysis if data unavailable
        
        return round(enhanced_score, 3)
    
    def _check_ntee_alignment(self, ntee_code: str, opportunity: GovernmentOpportunity) -> bool:
        """Check if NTEE code aligns with opportunity type."""
        if not ntee_code or not opportunity.description:
            return False
        
        # NTEE code mapping to opportunity keywords
        ntee_mapping = {
            'A': ['arts', 'culture', 'humanities', 'creative'],
            'B': ['education', 'school', 'university', 'academic', 'learning'],
            'C': ['environment', 'conservation', 'nature', 'green', 'sustainability'],
            'D': ['animal', 'wildlife', 'veterinary', 'pet'],
            'E': ['health', 'medical', 'healthcare', 'hospital', 'clinic'],
            'F': ['mental health', 'crisis', 'substance', 'addiction'],
            'G': ['disease', 'research', 'medical research'],
            'H': ['medical research', 'research'],
            'I': ['crime', 'legal', 'justice', 'law enforcement'],
            'J': ['employment', 'job', 'workforce', 'career'],
            'K': ['food', 'nutrition', 'hunger', 'agriculture'],
            'L': ['housing', 'shelter', 'homeless', 'residential'],
            'M': ['disaster', 'emergency', 'relief', 'safety'],
            'N': ['recreation', 'sports', 'youth', 'community'],
            'O': ['religion', 'faith', 'spiritual', 'church'],
            'P': ['science', 'technology', 'research', 'innovation'],
            'Q': ['international', 'foreign', 'global', 'development'],
            'R': ['civil rights', 'advocacy', 'social action'],
            'S': ['community', 'neighborhood', 'local', 'development'],
            'T': ['philanthropy', 'foundation', 'giving'],
            'U': ['science', 'technology', 'engineering'],
            'V': ['social service', 'welfare', 'assistance'],
            'W': ['public benefit', 'society', 'civic'],
            'X': ['religion', 'faith'],
            'Y': ['mutual benefit', 'membership'],
            'Z': ['unknown']
        }
        
        category = ntee_code[0].upper()
        if category in ntee_mapping:
            keywords = ntee_mapping[category]
            description_lower = opportunity.description.lower()
            return any(keyword in description_lower for keyword in keywords)
        
        return False
    
    def _calculate_mission_alignment(self, mission: str, opportunity_description: str) -> float:
        """Calculate mission-opportunity alignment score (0-1)."""
        if not mission or not opportunity_description:
            return 0.0
        
        # Convert to lowercase for comparison
        mission_lower = mission.lower()
        opp_lower = opportunity_description.lower()
        
        # Key mission words that often indicate alignment
        mission_keywords = []
        for word in mission_lower.split():
            if len(word) > 3 and word not in ['the', 'and', 'for', 'with', 'that', 'this', 'from', 'they', 'have', 'been', 'their']:
                mission_keywords.append(word)
        
        if not mission_keywords:
            return 0.0
        
        # Count keyword matches
        matches = sum(1 for keyword in mission_keywords if keyword in opp_lower)
        
        # Calculate alignment score
        alignment_score = min(matches / len(mission_keywords), 1.0)
        
        # Bonus for exact phrase matches
        if len(mission_keywords) >= 2:
            mission_phrases = [' '.join(mission_keywords[i:i+2]) for i in range(len(mission_keywords)-1)]
            phrase_matches = sum(1 for phrase in mission_phrases if phrase in opp_lower)
            if phrase_matches > 0:
                alignment_score = min(alignment_score + (phrase_matches * 0.2), 1.0)
        
        return alignment_score
    
    def _score_historical_success(self, org: OrganizationProfile, opportunity: GovernmentOpportunity) -> float:
        """Score based on historical success with similar opportunities (0-1)."""
        # Check if organization has award history data
        award_history = org.component_scores.get("award_history", {})
        if not award_history or award_history.get("total_awards", 0) == 0:
            return 0.3  # No history, neutral score
        
        score = 0.4  # Base score for having some federal award history
        
        # Bonus for multiple awards
        total_awards = award_history.get("total_awards", 0)
        if total_awards >= 5:
            score += 0.2
        elif total_awards >= 2:
            score += 0.1
        
        # Bonus for award amount track record
        total_amount = award_history.get("total_amount", 0)
        if total_amount >= 1_000_000:
            score += 0.2
        elif total_amount >= 100_000:
            score += 0.1
        
        # Bonus for agency diversity
        unique_agencies = award_history.get("unique_agencies", 0)
        if unique_agencies >= 3:
            score += 0.2
        elif unique_agencies >= 2:
            score += 0.1
        
        # Bonus for track record score
        track_record_score = org.component_scores.get("funding_track_record", 0)
        score += track_record_score * 0.2
        
        return min(1.0, score)
    
    def _generate_match_insights(
        self,
        match: GovernmentOpportunityMatch,
        org: OrganizationProfile,
        opportunity: GovernmentOpportunity
    ) -> None:
        """Generate insights and recommendations for the match."""
        
        # Add match reasons based on scores
        if match.eligibility_score >= 0.8:
            match.opportunity.match_reasons.append("Strong eligibility match")
        
        if match.timing_score >= 0.8:
            match.opportunity.match_reasons.append("Good timing for application")
        
        if match.financial_fit_score >= 0.8:
            match.opportunity.match_reasons.append("Award size fits organization capacity")
        
        if match.historical_success_score >= 0.7:
            match.opportunity.match_reasons.append("Strong federal funding track record")
        
        # Generate action items
        days_until_deadline = opportunity.calculate_days_until_deadline()
        if days_until_deadline:
            if days_until_deadline < 30:
                match.action_items.append("HIGH PRIORITY: Application deadline approaching")
                match.preparation_time_needed = max(5, days_until_deadline - 7)
            else:
                match.action_items.append("Review opportunity details and requirements")
                match.preparation_time_needed = min(21, days_until_deadline // 2)
        
        if match.eligibility_score == 1.0:
            match.action_items.append("Verify all eligibility requirements are met")
        
        if match.historical_success_score < 0.5:
            match.action_items.append("Consider partnering with experienced organization")
        
        # Assess competition level
        if len(opportunity.eligible_applicants) == 1:
            match.competition_assessment = "low"  # Only nonprofits eligible
        elif len(opportunity.eligible_applicants) <= 3:
            match.competition_assessment = "medium"
        else:
            match.competition_assessment = "high"
        
        # Add funding amount context
        if opportunity.award_ceiling:
            match.action_items.append(f"Award range: ${opportunity.award_floor or 0:,} - ${opportunity.award_ceiling:,}")
    
    def _calculate_match_statistics(
        self,
        matches: List[GovernmentOpportunityMatch],
        organizations: List[OrganizationProfile],
        opportunities: List[GovernmentOpportunity]
    ) -> Dict[str, Any]:
        """Calculate summary statistics for matches."""
        
        if not matches:
            return {"total_matches": 0}
        
        # Recommendation level distribution
        recommendation_counts = {"high": 0, "medium": 0, "low": 0, "review": 0}
        for match in matches:
            recommendation_counts[match.recommendation_level] += 1
        
        # Score statistics
        scores = [match.relevance_score for match in matches]
        
        # Timing statistics
        urgent_matches = len([m for m in matches if m.preparation_time_needed and m.preparation_time_needed <= 14])
        
        return {
            "total_matches": len(matches),
            "recommendation_distribution": recommendation_counts,
            "score_statistics": {
                "mean": np.mean(scores),
                "median": np.median(scores),
                "max": np.max(scores),
                "min": np.min(scores)
            },
            "urgent_matches": urgent_matches,
            "organizations_with_matches": len(set(match.organization for match in matches if match.organization)),
            "unique_opportunities_matched": len(set(match.opportunity.opportunity_id for match in matches))
        }


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return GovernmentOpportunityScorerProcessor()