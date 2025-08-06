"""
Profile-driven search engine that converts organization profiles into 
discovery parameters for different opportunity types (nonprofits, government, commercial)
"""
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from .models import (
    OrganizationProfile, 
    ProfileSearchParams, 
    FundingType, 
    OrganizationType,
    GeographicScope
)


@dataclass
class SearchStrategy:
    """Search strategy configuration for different opportunity types"""
    funding_type: FundingType
    weight_factors: Dict[str, float]  # Factor name -> weight
    required_fields: List[str]
    optional_fields: List[str]
    filters: Dict[str, Any]


class ProfileSearchEngine:
    """Converts organization profiles into targeted search parameters"""
    
    def __init__(self):
        """Initialize search engine with strategy configurations"""
        self.search_strategies = self._initialize_strategies()
        self.keyword_mappings = self._initialize_keyword_mappings()
        self.geographic_mappings = self._initialize_geographic_mappings()
    
    def generate_search_params(
        self, 
        profile: OrganizationProfile, 
        funding_types: Optional[List[FundingType]] = None,
        max_results_per_type: int = 100
    ) -> Dict[FundingType, ProfileSearchParams]:
        """
        Generate search parameters for each funding type based on profile
        
        Returns:
            Dictionary mapping funding type to search parameters
        """
        if not funding_types:
            funding_types = profile.funding_preferences.funding_types
        
        search_params = {}
        
        for funding_type in funding_types:
            params = self._generate_params_for_type(profile, funding_type, max_results_per_type)
            if params:
                search_params[funding_type] = params
        
        return search_params
    
    def _generate_params_for_type(
        self, 
        profile: OrganizationProfile, 
        funding_type: FundingType,
        max_results: int
    ) -> Optional[ProfileSearchParams]:
        """Generate search parameters for specific funding type"""
        
        strategy = self.search_strategies.get(funding_type)
        if not strategy:
            return None
        
        # Base parameters
        params_dict = {
            'profile_id': profile.profile_id,
            'funding_types': [funding_type],
            'max_results_per_type': max_results,
            'min_compatibility_threshold': 0.3
        }
        
        # Generate type-specific filters
        if funding_type == FundingType.GRANTS:
            params_dict.update(self._generate_nonprofit_params(profile, strategy))
        elif funding_type == FundingType.GOVERNMENT:
            params_dict.update(self._generate_government_params(profile, strategy))
        elif funding_type == FundingType.COMMERCIAL:
            params_dict.update(self._generate_commercial_params(profile, strategy))
        elif funding_type == FundingType.SPONSORSHIPS:
            params_dict.update(self._generate_sponsorship_params(profile, strategy))
        elif funding_type == FundingType.PARTNERSHIPS:
            params_dict.update(self._generate_partnership_params(profile, strategy))
        
        return ProfileSearchParams(**params_dict)
    
    def _generate_nonprofit_params(self, profile: OrganizationProfile, strategy: SearchStrategy) -> Dict[str, Any]:
        """Generate parameters for nonprofit/foundation grant search"""
        params = {
            'discovery_filters': {
                'organization_types': ['private_foundation', 'public_charity', 'corporate_foundation'],
                'ntee_codes': self._map_focus_to_ntee_codes(profile.focus_areas),
                'keywords': self._extract_search_keywords(profile),
                'geographic_scope': self._convert_geographic_scope(profile.geographic_scope),
                'funding_range': {
                    'min_amount': profile.funding_preferences.min_amount or 10000,
                    'max_amount': profile.funding_preferences.max_amount or 1000000
                },
                'program_alignment': {
                    'focus_areas': profile.focus_areas,
                    'target_populations': profile.target_populations,
                    'program_areas': profile.program_areas
                }
            },
            'pre_scoring_threshold': 0.5,
            'deep_analysis_limit': 20
        }
        
        # Add organization-specific factors
        if profile.organization_type == OrganizationType.NONPROFIT:
            params['discovery_filters']['prefer_nonprofit_funders'] = True
        elif profile.organization_type == OrganizationType.HEALTHCARE:
            params['discovery_filters']['health_focus_bonus'] = 0.2
        
        return params
    
    def _generate_government_params(self, profile: OrganizationProfile, strategy: SearchStrategy) -> Dict[str, Any]:
        """Generate parameters for government grant search (Grants.gov)"""
        params = {
            'discovery_filters': {
                'agencies': self._map_focus_to_agencies(profile.focus_areas),
                'cfda_categories': self._map_focus_to_cfda(profile.focus_areas),
                'eligibility_types': self._determine_government_eligibility(profile),
                'keywords': self._extract_search_keywords(profile, government_focused=True),
                'geographic_restrictions': self._convert_geographic_scope(profile.geographic_scope),
                'funding_range': {
                    'min_amount': profile.funding_preferences.min_amount or 25000,
                    'max_amount': profile.funding_preferences.max_amount or 5000000
                }
            },
            'pre_scoring_threshold': 0.4,
            'deep_analysis_limit': 15
        }
        
        return params
    
    def _generate_commercial_params(self, profile: OrganizationProfile, strategy: SearchStrategy) -> Dict[str, Any]:
        """Generate parameters for commercial/corporate funding search"""
        params = {
            'discovery_filters': {
                'industries': self._map_focus_to_industries(profile.focus_areas),
                'company_sizes': ['large_corp', 'fortune_500'] if profile.annual_revenue and profile.annual_revenue > 1000000 else ['mid_size', 'large_corp'],
                'csr_focus_areas': profile.focus_areas,
                'geographic_presence': self._convert_geographic_scope(profile.geographic_scope),
                'partnership_types': ['grants', 'sponsorships', 'cause_marketing'],
                'funding_range': {
                    'min_amount': profile.funding_preferences.min_amount or 5000,
                    'max_amount': profile.funding_preferences.max_amount or 250000
                }
            },
            'pre_scoring_threshold': 0.3,
            'deep_analysis_limit': 25
        }
        
        return params
    
    def _generate_sponsorship_params(self, profile: OrganizationProfile, strategy: SearchStrategy) -> Dict[str, Any]:
        """Generate parameters for sponsorship opportunity search"""
        params = {
            'discovery_filters': {
                'event_types': self._infer_event_types(profile),
                'sponsorship_levels': self._determine_sponsorship_levels(profile),
                'target_demographics': profile.target_populations,
                'geographic_reach': self._convert_geographic_scope(profile.geographic_scope),
                'brand_alignment': profile.focus_areas
            },
            'pre_scoring_threshold': 0.35,
            'deep_analysis_limit': 30
        }
        
        return params
    
    def _generate_partnership_params(self, profile: OrganizationProfile, strategy: SearchStrategy) -> Dict[str, Any]:
        """Generate parameters for strategic partnership search"""
        params = {
            'discovery_filters': {
                'partnership_types': ['strategic', 'program', 'capacity_building'],
                'complementary_focuses': self._find_complementary_areas(profile.focus_areas),
                'organization_sizes': self._determine_compatible_sizes(profile),
                'collaboration_history': profile.partnership_interests,
                'resource_sharing': ['expertise', 'funding', 'networks', 'facilities']
            },
            'pre_scoring_threshold': 0.4,
            'deep_analysis_limit': 20
        }
        
        return params
    
    # Mapping and conversion methods
    
    def _map_focus_to_ntee_codes(self, focus_areas: List[str]) -> List[str]:
        """Map focus areas to NTEE codes for nonprofit search"""
        ntee_codes = set()
        
        for focus in focus_areas:
            focus_lower = focus.lower()
            for keyword, codes in self.keyword_mappings['ntee'].items():
                if keyword in focus_lower:
                    ntee_codes.update(codes)
        
        return list(ntee_codes)
    
    def _map_focus_to_agencies(self, focus_areas: List[str]) -> List[str]:
        """Map focus areas to federal agencies"""
        agencies = set()
        
        for focus in focus_areas:
            focus_lower = focus.lower()
            for keyword, agency_list in self.keyword_mappings['agencies'].items():
                if keyword in focus_lower:
                    agencies.update(agency_list)
        
        return list(agencies)
    
    def _map_focus_to_cfda(self, focus_areas: List[str]) -> List[str]:
        """Map focus areas to CFDA categories"""
        cfda_categories = set()
        
        for focus in focus_areas:
            focus_lower = focus.lower()
            for keyword, categories in self.keyword_mappings['cfda'].items():
                if keyword in categories:
                    cfda_categories.update(categories)
        
        return list(cfda_categories)
    
    def _map_focus_to_industries(self, focus_areas: List[str]) -> List[str]:
        """Map focus areas to industry sectors"""
        industries = set()
        
        for focus in focus_areas:
            focus_lower = focus.lower()
            for keyword, industry_list in self.keyword_mappings['industries'].items():
                if keyword in focus_lower:
                    industries.update(industry_list)
        
        return list(industries)
    
    def _extract_search_keywords(self, profile: OrganizationProfile, government_focused: bool = False) -> List[str]:
        """Extract and optimize search keywords from profile"""
        keywords = set()
        
        # Add focus areas
        keywords.update(profile.focus_areas)
        
        # Add target populations
        keywords.update(profile.target_populations)
        
        # Extract from mission statement
        mission_keywords = self._extract_keywords_from_text(profile.mission_statement)
        keywords.update(mission_keywords)
        
        # Add program areas
        keywords.update(profile.program_areas)
        
        # Government-specific keyword enhancement
        if government_focused:
            gov_keywords = self._enhance_government_keywords(list(keywords))
            keywords.update(gov_keywords)
        
        return list(keywords)
    
    def _extract_keywords_from_text(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract meaningful keywords from text using simple NLP"""
        # Remove common words and extract meaningful terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 
            'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 
            'shall', 'through', 'during', 'before', 'after', 'above', 'below', 'up', 'down', 
            'out', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'our', 'we', 
            'they', 'them', 'their', 'organization', 'provide', 'services', 'support'
        }
        
        # Simple tokenization and filtering
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Return most frequent words (simple frequency count)
        word_freq = {}
        for word in meaningful_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)
        return sorted_words[:max_keywords]
    
    def _convert_geographic_scope(self, geo_scope: GeographicScope) -> Dict[str, Any]:
        """Convert geographic scope to search parameters"""
        return {
            'states': geo_scope.states,
            'regions': geo_scope.regions,
            'nationwide': geo_scope.nationwide,
            'international': geo_scope.international,
            'priority_states': geo_scope.states[:3] if geo_scope.states else []
        }
    
    def _determine_government_eligibility(self, profile: OrganizationProfile) -> List[str]:
        """Determine government grant eligibility types"""
        eligibility = []
        
        if profile.organization_type == OrganizationType.NONPROFIT:
            eligibility.extend(['501c3', 'nonprofit', 'public_charity'])
        elif profile.organization_type == OrganizationType.GOVERNMENT:
            eligibility.extend(['state_gov', 'local_gov', 'municipal'])
        elif profile.organization_type == OrganizationType.ACADEMIC:
            eligibility.extend(['educational', 'university', 'research'])
        elif profile.organization_type == OrganizationType.HEALTHCARE:
            eligibility.extend(['healthcare', 'hospital', 'medical'])
        
        return eligibility
    
    # Strategy initialization methods
    
    def _initialize_strategies(self) -> Dict[FundingType, SearchStrategy]:
        """Initialize search strategies for each funding type"""
        return {
            FundingType.GRANTS: SearchStrategy(
                funding_type=FundingType.GRANTS,
                weight_factors={
                    'focus_alignment': 0.3,
                    'geographic_match': 0.2,
                    'funding_range_fit': 0.2,
                    'organization_type_match': 0.15,
                    'program_alignment': 0.15
                },
                required_fields=['focus_areas', 'organization_type'],
                optional_fields=['geographic_scope', 'funding_preferences'],
                filters={'min_assets': 100000}
            ),
            FundingType.GOVERNMENT: SearchStrategy(
                funding_type=FundingType.GOVERNMENT,
                weight_factors={
                    'agency_alignment': 0.35,
                    'eligibility_match': 0.25,
                    'geographic_eligibility': 0.2,
                    'funding_history': 0.1,
                    'compliance_readiness': 0.1
                },
                required_fields=['focus_areas', 'organization_type'],
                optional_fields=['compliance_requirements', 'certifications'],
                filters={'federal_eligible': True}
            ),
            FundingType.COMMERCIAL: SearchStrategy(
                funding_type=FundingType.COMMERCIAL,
                weight_factors={
                    'csr_alignment': 0.3,
                    'brand_compatibility': 0.25,
                    'market_presence': 0.2,
                    'partnership_potential': 0.15,
                    'funding_capacity': 0.1
                },
                required_fields=['focus_areas', 'target_populations'],
                optional_fields=['partnership_interests', 'growth_goals'],
                filters={'commercial_friendly': True}
            )
        }
    
    def _initialize_keyword_mappings(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize keyword mappings for different search types"""
        return {
            'ntee': {
                'health': ['E20', 'E21', 'E22', 'E30', 'E31', 'E32', 'E60', 'E61', 'E86'],
                'education': ['B01', 'B02', 'B03', 'B11', 'B12', 'B20', 'B21', 'B24', 'B25'],
                'community': ['S20', 'S21', 'S22', 'S30', 'S31', 'S32', 'S40', 'S41'],
                'environment': ['C01', 'C02', 'C03', 'C11', 'C12', 'C20', 'C27', 'C30'],
                'arts': ['A01', 'A02', 'A03', 'A11', 'A12', 'A20', 'A23', 'A24', 'A25'],
                'human_services': ['P01', 'P02', 'P03', 'P11', 'P12', 'P20', 'P21', 'P22'],
                'youth': ['O20', 'O21', 'O22', 'O23', 'O50', 'O51', 'O52', 'O53'],
                'food': ['F30', 'F31', 'F32', 'F40', 'F41', 'F42', 'K30', 'K31']
            },
            'agencies': {
                'health': ['HHS', 'CDC', 'NIH', 'HRSA'],
                'education': ['ED', 'NSF'],
                'environment': ['EPA', 'DOI', 'NOAA'],
                'community': ['HUD', 'USDA', 'DOL'],
                'justice': ['DOJ', 'OJJDP'],
                'agriculture': ['USDA', 'NIFA'],
                'energy': ['DOE', 'EERE']
            },
            'cfda': {
                'health': ['93.xxx'],
                'education': ['84.xxx'],
                'community': ['14.xxx', '10.xxx'],
                'environment': ['66.xxx']
            },
            'industries': {
                'health': ['healthcare', 'pharmaceuticals', 'medical_devices', 'biotechnology'],
                'education': ['education_technology', 'publishing', 'training'],
                'environment': ['clean_energy', 'environmental_services', 'sustainability'],
                'technology': ['software', 'telecommunications', 'it_services'],
                'financial': ['banking', 'insurance', 'investment']
            }
        }
    
    def _initialize_geographic_mappings(self) -> Dict[str, List[str]]:
        """Initialize geographic region mappings"""
        return {
            'northeast': ['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA'],
            'southeast': ['DE', 'MD', 'DC', 'VA', 'WV', 'KY', 'TN', 'NC', 'SC', 'GA', 'FL', 'AL', 'MS', 'AR', 'LA'],
            'midwest': ['OH', 'MI', 'IN', 'WI', 'IL', 'MN', 'IA', 'MO', 'ND', 'SD', 'NE', 'KS'],
            'southwest': ['TX', 'OK', 'NM', 'AZ'],
            'west': ['MT', 'WY', 'CO', 'UT', 'ID', 'WA', 'OR', 'NV', 'CA', 'AK', 'HI']
        }
    
    # Helper methods for parameter generation
    
    def _enhance_government_keywords(self, keywords: List[str]) -> List[str]:
        """Add government-specific keyword variations"""
        gov_keywords = []
        gov_terms = ['federal', 'grant', 'program', 'initiative', 'funding', 'assistance']
        
        for keyword in keywords:
            for term in gov_terms:
                gov_keywords.append(f"{keyword} {term}")
        
        return gov_keywords
    
    def _infer_event_types(self, profile: OrganizationProfile) -> List[str]:
        """Infer potential event types based on profile"""
        event_types = []
        
        focus_to_events = {
            'health': ['health_fair', 'wellness_event', 'medical_conference'],
            'education': ['educational_conference', 'scholarship_event', 'academic_competition'],
            'community': ['community_festival', 'fundraising_gala', 'awareness_campaign'],
            'environment': ['environmental_fair', 'sustainability_summit', 'clean_up_event'],
            'arts': ['art_exhibition', 'cultural_festival', 'performance_event']
        }
        
        for focus in profile.focus_areas:
            focus_lower = focus.lower()
            for key, events in focus_to_events.items():
                if key in focus_lower:
                    event_types.extend(events)
        
        return event_types
    
    def _determine_sponsorship_levels(self, profile: OrganizationProfile) -> List[str]:
        """Determine appropriate sponsorship levels based on profile"""
        if not profile.annual_revenue:
            return ['bronze', 'silver']
        
        if profile.annual_revenue >= 5000000:
            return ['platinum', 'gold', 'silver']
        elif profile.annual_revenue >= 1000000:
            return ['gold', 'silver', 'bronze']
        elif profile.annual_revenue >= 250000:
            return ['silver', 'bronze']
        else:
            return ['bronze', 'community']
    
    def _find_complementary_areas(self, focus_areas: List[str]) -> List[str]:
        """Find complementary focus areas for partnerships"""
        complementary_map = {
            'health': ['education', 'community development', 'research'],
            'education': ['health', 'technology', 'workforce development'],
            'environment': ['education', 'community development', 'research'],
            'community': ['health', 'education', 'economic development'],
            'arts': ['education', 'community development', 'tourism']
        }
        
        complementary = set()
        for focus in focus_areas:
            focus_lower = focus.lower()
            for key, comp_areas in complementary_map.items():
                if key in focus_lower:
                    complementary.update(comp_areas)
        
        return list(complementary)
    
    def _determine_compatible_sizes(self, profile: OrganizationProfile) -> List[str]:
        """Determine compatible organization sizes for partnerships"""
        if not profile.annual_revenue:
            return ['small', 'medium', 'large']
        
        if profile.annual_revenue >= 10000000:
            return ['large', 'enterprise']
        elif profile.annual_revenue >= 1000000:
            return ['medium', 'large']
        elif profile.annual_revenue >= 100000:
            return ['small', 'medium']
        else:
            return ['micro', 'small']