#!/usr/bin/env python3
"""
Profile-Specific Matching and Scoring
Combines shared analytics with profile-specific criteria for opportunity matching.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import logging

from ..analytics.financial_analytics import get_financial_analytics, FinancialMetrics
from ..analytics.network_analytics import get_network_analytics, NetworkMetrics
from ..core.data_models import OrganizationProfile
from ..profiles.models import FundingPreferences

logger = logging.getLogger(__name__)


@dataclass
class OpportunityMatch:
    """Represents a match between an organization and an opportunity with profile-specific scoring"""
    organization_ein: str
    organization_name: str
    opportunity_id: str
    opportunity_title: str
    base_compatibility_score: float  # From shared analytics
    profile_specific_score: float    # Based on profile criteria
    final_match_score: float         # Combined score
    match_reasons: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    recommendation: str = ""
    computed_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProfileMatchResults:
    """Complete matching results for a profile"""
    profile_name: str
    total_organizations_analyzed: int
    total_opportunities_analyzed: int
    matches: List[OpportunityMatch]
    top_matches: List[OpportunityMatch] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)
    computed_at: datetime = field(default_factory=datetime.now)


class ProfileMatcher:
    """
    Profile-specific analysis engine that combines shared analytics with profile criteria.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.financial_analytics = get_financial_analytics()
        self.network_analytics = get_network_analytics()
        
        # Profile-specific scoring weights
        self.profile_weights = {
            "financial_health": 0.25,
            "network_strength": 0.15,
            "mission_alignment": 0.20,
            "geographic_fit": 0.15,
            "funding_history": 0.15,
            "risk_tolerance": 0.10
        }
    
    def analyze_organization_for_profile(self, 
                                       organization_data: Dict[str, Any],
                                       profile_criteria: Optional[FundingPreferences] = None) -> Dict[str, Any]:
        """
        Analyze an organization against specific profile criteria.
        
        Args:
            organization_data: Raw organization data from entity cache
            profile_criteria: Optional profile-specific matching criteria
            
        Returns:
            Dictionary with profile-specific analysis results
        """
        try:
            ein = organization_data.get('organization', {}).get('ein', '')
            org_name = organization_data.get('organization', {}).get('name', 'Unknown')
            
            # Get shared analytics (reuse if already computed)
            financial_metrics = self.financial_analytics.analyze_organization_financials(
                filing_data=organization_data,
                organization_name=org_name,
                ein=ein
            )
            
            # Profile-specific scoring
            profile_score = self._calculate_profile_specific_score(
                organization_data, financial_metrics, profile_criteria
            )
            
            # Combine shared analytics with profile scoring
            analysis = {
                "ein": ein,
                "organization_name": org_name,
                "financial_metrics": financial_metrics,
                "profile_compatibility_score": profile_score["total_score"],
                "compatibility_breakdown": profile_score["breakdown"],
                "match_strengths": profile_score["strengths"],
                "potential_concerns": profile_score["concerns"],
                "recommendation": self._generate_recommendation(profile_score["total_score"]),
                "computed_at": datetime.now().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing organization for profile: {e}")
            return {"error": str(e)}
    
    def _calculate_profile_specific_score(self, 
                                        org_data: Dict[str, Any],
                                        financial_metrics: FinancialMetrics,
                                        criteria: Optional[FundingPreferences]) -> Dict[str, Any]:
        """Calculate profile-specific compatibility score"""
        try:
            breakdown = {}
            strengths = []
            concerns = []
            
            # Financial health alignment
            if financial_metrics.financial_stability_score is not None:
                breakdown["financial_health"] = financial_metrics.financial_stability_score
                if financial_metrics.financial_stability_score >= 0.7:
                    strengths.append("Strong financial stability")
                elif financial_metrics.financial_stability_score < 0.4:
                    concerns.append("Below-average financial stability")
            else:
                breakdown["financial_health"] = 0.5  # Neutral score
                concerns.append("Limited financial data available")
            
            # Revenue size alignment
            breakdown["revenue_fit"] = self._score_revenue_fit(
                financial_metrics.revenue, criteria
            )
            
            # NTEE code alignment
            breakdown["mission_alignment"] = self._score_mission_alignment(
                org_data, criteria
            )
            
            # Geographic alignment
            breakdown["geographic_fit"] = self._score_geographic_fit(
                org_data, criteria
            )
            
            # Keywords/mission match
            breakdown["keyword_match"] = self._score_keyword_match(
                org_data, criteria
            )
            
            # Calculate weighted total score
            total_score = 0.0
            weight_sum = 0.0
            
            for component, score in breakdown.items():
                if score is not None:
                    weight = self.profile_weights.get(component, 0.1)
                    total_score += score * weight
                    weight_sum += weight
            
            if weight_sum > 0:
                total_score = total_score / weight_sum
            else:
                total_score = 0.5  # Neutral score
            
            return {
                "total_score": max(0.0, min(1.0, total_score)),
                "breakdown": breakdown,
                "strengths": strengths,
                "concerns": concerns
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating profile-specific score: {e}")
            return {
                "total_score": 0.0,
                "breakdown": {},
                "strengths": [],
                "concerns": ["Error in analysis"]
            }
    
    def _score_revenue_fit(self, revenue: Optional[float], criteria: Optional[FundingPreferences]) -> float:
        """Score how well organization revenue fits profile criteria"""
        if not revenue:
            return 0.5  # Neutral score for missing data
        
        # This would use profile-specific revenue preferences
        # For now, use a simple scoring based on revenue size
        if revenue >= 1000000:  # $1M+
            return 0.8
        elif revenue >= 100000:  # $100K+
            return 0.6
        elif revenue >= 10000:   # $10K+
            return 0.4
        else:
            return 0.2
    
    def _score_mission_alignment(self, org_data: Dict[str, Any], criteria: Optional[FundingPreferences]) -> float:
        """Score mission alignment based on NTEE codes and criteria"""
        try:
            org_ntee = org_data.get('organization', {}).get('ntee_code', '')
            if not org_ntee:
                return 0.5  # Neutral for missing data
            
            # This would compare against profile NTEE preferences
            # For now, give higher scores to certain beneficial categories
            beneficial_prefixes = ['P', 'Q', 'S', 'T', 'U', 'V', 'W', 'X', 'Y']  # Human services, etc.
            
            if any(org_ntee.startswith(prefix) for prefix in beneficial_prefixes):
                return 0.8
            else:
                return 0.6
                
        except Exception as e:
            self.logger.debug(f"Error scoring mission alignment: {e}")
            return 0.5
    
    def _score_geographic_fit(self, org_data: Dict[str, Any], criteria: Optional[FundingPreferences]) -> float:
        """Score geographic alignment"""
        try:
            org_state = org_data.get('organization', {}).get('state', '')
            if not org_state:
                return 0.5
            
            # This would compare against profile geographic preferences
            # For now, favor certain states
            preferred_states = ['VA', 'MD', 'DC', 'NC', 'WV']  # Regional preference
            
            if org_state in preferred_states:
                return 0.8
            else:
                return 0.6
                
        except Exception as e:
            self.logger.debug(f"Error scoring geographic fit: {e}")
            return 0.5
    
    def _score_keyword_match(self, org_data: Dict[str, Any], criteria: Optional[FundingPreferences]) -> float:
        """Score keyword/mission text matching"""
        try:
            # Extract text fields from organization
            text_fields = []
            org = org_data.get('organization', {})
            
            if 'mission' in org:
                text_fields.append(org['mission'])
            if 'activities' in org:
                text_fields.append(org['activities'])
            if 'name' in org:
                text_fields.append(org['name'])
            
            if not text_fields:
                return 0.5
            
            # This would match against profile keywords
            # For now, look for beneficial keywords
            beneficial_keywords = [
                'education', 'health', 'community', 'environment', 'youth',
                'research', 'development', 'support', 'assistance', 'program'
            ]
            
            text_content = ' '.join(text_fields).lower()
            matches = sum(1 for keyword in beneficial_keywords if keyword in text_content)
            
            # Score based on keyword density
            if matches >= 3:
                return 0.8
            elif matches >= 1:
                return 0.6
            else:
                return 0.4
                
        except Exception as e:
            self.logger.debug(f"Error scoring keyword match: {e}")
            return 0.5
    
    def _generate_recommendation(self, total_score: float) -> str:
        """Generate recommendation based on total score"""
        if total_score >= 0.8:
            return "Highly recommended - Strong alignment with profile criteria"
        elif total_score >= 0.6:
            return "Recommended - Good fit with some considerations"
        elif total_score >= 0.4:
            return "Consider with caution - Mixed alignment"
        else:
            return "Not recommended - Poor fit with profile criteria"
    
    def score_opportunity_match(self, 
                               organization_analysis: Dict[str, Any],
                               opportunity_data: Dict[str, Any],
                               profile_criteria: Optional[FundingPreferences] = None) -> OpportunityMatch:
        """
        Score how well an opportunity matches an organization given profile criteria.
        
        Args:
            organization_analysis: Analysis results from analyze_organization_for_profile
            opportunity_data: Raw opportunity data
            profile_criteria: Profile-specific criteria
            
        Returns:
            OpportunityMatch with combined scoring
        """
        try:
            # Extract basic info
            org_ein = organization_analysis.get('ein', '')
            org_name = organization_analysis.get('organization_name', 'Unknown')
            opp_id = opportunity_data.get('opportunity_id', '')
            opp_title = opportunity_data.get('funding_opportunity_title', 'Unknown')
            
            # Base compatibility from shared analytics
            base_score = organization_analysis.get('profile_compatibility_score', 0.0)
            
            # Profile-specific opportunity scoring
            profile_opp_score = self._score_opportunity_for_profile(
                opportunity_data, profile_criteria
            )
            
            # Combine scores (weighted average)
            final_score = (base_score * 0.6) + (profile_opp_score * 0.4)
            
            # Generate match reasons
            match_reasons = []
            risk_factors = []
            
            if base_score >= 0.7:
                match_reasons.append("Strong organizational compatibility")
            if profile_opp_score >= 0.7:
                match_reasons.append("Excellent opportunity alignment")
            
            if base_score < 0.4:
                risk_factors.append("Below-average organizational fit")
            if profile_opp_score < 0.4:
                risk_factors.append("Poor opportunity alignment")
            
            # Generate recommendation
            if final_score >= 0.8:
                recommendation = "Pursue immediately - Excellent match"
            elif final_score >= 0.6:
                recommendation = "Strong candidate - Consider for application"
            elif final_score >= 0.4:
                recommendation = "Moderate fit - Evaluate carefully"
            else:
                recommendation = "Low priority - Focus on better matches"
            
            return OpportunityMatch(
                organization_ein=org_ein,
                organization_name=org_name,
                opportunity_id=opp_id,
                opportunity_title=opp_title,
                base_compatibility_score=base_score,
                profile_specific_score=profile_opp_score,
                final_match_score=final_score,
                match_reasons=match_reasons,
                risk_factors=risk_factors,
                recommendation=recommendation
            )
            
        except Exception as e:
            self.logger.error(f"Error scoring opportunity match: {e}")
            return OpportunityMatch(
                organization_ein="",
                organization_name="Error",
                opportunity_id="",
                opportunity_title="Error",
                base_compatibility_score=0.0,
                profile_specific_score=0.0,
                final_match_score=0.0,
                match_reasons=[],
                risk_factors=["Analysis error"],
                recommendation="Unable to evaluate"
            )
    
    def _score_opportunity_for_profile(self, 
                                     opportunity_data: Dict[str, Any],
                                     profile_criteria: Optional[FundingPreferences]) -> float:
        """Score an opportunity based on profile-specific criteria"""
        try:
            score_components = []
            
            # Funding amount alignment
            funding_amount = opportunity_data.get('award_ceiling', 0)
            if funding_amount:
                # This would compare against profile funding preferences
                if funding_amount >= 100000:  # $100K+
                    score_components.append(0.8)
                elif funding_amount >= 50000:   # $50K+
                    score_components.append(0.6)
                else:
                    score_components.append(0.4)
            else:
                score_components.append(0.5)  # Neutral for missing data
            
            # Category alignment
            category = opportunity_data.get('category_of_funding_activity', '')
            if category:
                # This would match against profile focus areas
                beneficial_categories = [
                    'Education', 'Health', 'Environment', 'Community Development',
                    'Research', 'Social Services'
                ]
                if any(cat.lower() in category.lower() for cat in beneficial_categories):
                    score_components.append(0.8)
                else:
                    score_components.append(0.6)
            else:
                score_components.append(0.5)
            
            # Eligibility check
            eligibility = opportunity_data.get('eligibility', {})
            if eligibility:
                # Check if nonprofits are eligible
                codes = eligibility.get('codes', [])
                if '25' in codes:  # Nonprofit eligibility code
                    score_components.append(1.0)
                else:
                    score_components.append(0.2)  # Low score if not eligible
            else:
                score_components.append(0.5)
            
            # Return average of components
            if score_components:
                return sum(score_components) / len(score_components)
            else:
                return 0.5
                
        except Exception as e:
            self.logger.debug(f"Error scoring opportunity for profile: {e}")
            return 0.5
    
    def generate_profile_matches(self,
                               organizations: List[Dict[str, Any]],
                               opportunities: List[Dict[str, Any]],
                               profile_criteria: Optional[FundingPreferences],
                               profile_name: str) -> ProfileMatchResults:
        """
        Generate complete matching results for a profile.
        
        Args:
            organizations: List of organization data
            opportunities: List of opportunity data
            profile_criteria: Profile-specific criteria
            profile_name: Name of the profile
            
        Returns:
            ProfileMatchResults with all matches and analysis
        """
        try:
            all_matches = []
            
            # Analyze each organization
            org_analyses = []
            for org_data in organizations:
                analysis = self.analyze_organization_for_profile(org_data, profile_criteria)
                org_analyses.append(analysis)
            
            # Score all organization-opportunity combinations
            for org_analysis in org_analyses:
                for opp_data in opportunities:
                    match = self.score_opportunity_match(
                        org_analysis, opp_data, profile_criteria
                    )
                    all_matches.append(match)
            
            # Sort by final match score
            all_matches.sort(key=lambda x: x.final_match_score, reverse=True)
            
            # Get top matches (top 20%)
            top_count = max(1, len(all_matches) // 5)
            top_matches = all_matches[:top_count]
            
            # Generate summary statistics
            summary_stats = {
                "average_match_score": sum(m.final_match_score for m in all_matches) / len(all_matches) if all_matches else 0,
                "high_quality_matches": len([m for m in all_matches if m.final_match_score >= 0.7]),
                "medium_quality_matches": len([m for m in all_matches if 0.4 <= m.final_match_score < 0.7]),
                "low_quality_matches": len([m for m in all_matches if m.final_match_score < 0.4]),
                "top_match_score": all_matches[0].final_match_score if all_matches else 0
            }
            
            return ProfileMatchResults(
                profile_name=profile_name,
                total_organizations_analyzed=len(organizations),
                total_opportunities_analyzed=len(opportunities),
                matches=all_matches,
                top_matches=top_matches,
                summary_stats=summary_stats
            )
            
        except Exception as e:
            self.logger.error(f"Error generating profile matches: {e}")
            return ProfileMatchResults(
                profile_name=profile_name,
                total_organizations_analyzed=0,
                total_opportunities_analyzed=0,
                matches=[]
            )


# Global matcher instance
_profile_matcher: Optional[ProfileMatcher] = None


def get_profile_matcher() -> ProfileMatcher:
    """Get or create global profile matcher instance"""
    global _profile_matcher
    if _profile_matcher is None:
        _profile_matcher = ProfileMatcher()
    return _profile_matcher