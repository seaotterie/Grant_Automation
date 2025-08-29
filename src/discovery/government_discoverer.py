"""
Government Grants Discovery Engine
Placeholder for Grants.gov API integration and federal/state grant opportunities
"""
import asyncio
import uuid
import json
from typing import Dict, List, Optional, Any, AsyncIterator
from datetime import datetime, timedelta
import random

from .base_discoverer import BaseDiscoverer, DiscoveryResult
from src.profiles.models import OrganizationProfile, ProfileSearchParams, FundingType


class GovernmentDiscoverer(BaseDiscoverer):
    """Discovers government grant opportunities from federal and state sources"""
    
    def __init__(self):
        super().__init__("Grants.gov Federal Grant Discovery", FundingType.GOVERNMENT)
        # API key loaded via auth system when configured
        self.api_key = None  # Managed by API key manager
        self.base_url = "https://www.grants.gov/web/grants/search-grants.html"  # Placeholder
        self.supported_agencies = self._load_agency_data()
        self.cfda_categories = self._load_cfda_data()
    
    async def discover_opportunities(
        self, 
        profile: OrganizationProfile,
        search_params: ProfileSearchParams,
        max_results: int = 1000
    ) -> AsyncIterator[DiscoveryResult]:
        """Discover government grant opportunities"""
        
        discovery_filters = search_params.discovery_filters
        
        # Extract search parameters
        agencies = discovery_filters.get("agencies", ["HHS", "ED"])
        eligibility_types = discovery_filters.get("eligibility_types", ["nonprofit"])
        funding_range = discovery_filters.get("funding_range", {})
        keywords = discovery_filters.get("keywords", profile.focus_areas)
        
        # Mock mode for development - production uses grants_gov_fetch processor
        # Actual API integration available via processor system
        # For now, generate realistic mock opportunities
        opportunities = await self._generate_realistic_government_opportunities(
            profile, agencies, eligibility_types, funding_range, keywords, max_results
        )
        
        for opportunity in opportunities:
            yield opportunity
            await asyncio.sleep(self.rate_limit_delay)
    
    async def validate_search_params(self, search_params: ProfileSearchParams) -> bool:
        """Validate search parameters for government discovery"""
        discovery_filters = search_params.discovery_filters
        
        if not discovery_filters:
            return False
        
        # Validate agencies
        agencies = discovery_filters.get("agencies", [])
        if agencies:
            valid_agencies = set(self.supported_agencies.keys())
            if not all(agency in valid_agencies for agency in agencies):
                return False
        
        # Validate eligibility types
        eligibility_types = discovery_filters.get("eligibility_types", [])
        valid_eligibility = {
            "nonprofit", "501c3", "public_charity", "state_gov", "local_gov", 
            "municipal", "educational", "university", "research", "healthcare", 
            "hospital", "medical", "tribal", "individual"
        }
        if eligibility_types:
            if not all(etype in valid_eligibility for etype in eligibility_types):
                return False
        
        return True
    
    async def get_discoverer_status(self) -> Dict[str, Any]:
        """Get current status of government discoverer"""
        return {
            "name": self.name,
            "funding_type": self.funding_type.value,
            "enabled": self.enabled,
            "status": "development_mock",  # Production uses grants_gov_fetch processor
            "api_available": False,  # Real API connectivity via grants_gov_fetch processor
            "supported_agencies": len(self.supported_agencies),
            "cfda_categories": len(self.cfda_categories),
            "last_check": datetime.now().isoformat(),
            "capabilities": {
                "max_results": 500,
                "supports_agency_filtering": True,
                "supports_eligibility_filtering": True,
                "supports_keyword_search": True,
                "supports_geographic_filtering": True,
                "supports_deadline_filtering": True
            },
            "note": "Currently using mock data. Grants.gov API integration pending."
        }
    
    async def _generate_realistic_government_opportunities(
        self, 
        profile: OrganizationProfile,
        agencies: List[str],
        eligibility_types: List[str],
        funding_range: Dict[str, int],
        keywords: List[str],
        max_results: int
    ) -> List[DiscoveryResult]:
        """Generate realistic government grant opportunities for demonstration"""
        
        opportunities = []
        
        # Program templates based on common federal programs
        program_templates = [
            {
                "agency": "HHS",
                "program_name": "Community Health Centers Program",
                "base_amount": 750000,
                "description": "Federal funding to establish and operate community health centers",
                "cfda": "93.224",
                "focus_areas": ["health", "community", "healthcare"],
                "eligibility": ["nonprofit", "501c3", "public_charity", "healthcare"]
            },
            {
                "agency": "ED",
                "program_name": "Title I School Improvement Grants",
                "base_amount": 500000,
                "description": "Federal grants to improve educational outcomes in high-need schools",
                "cfda": "84.377",
                "focus_areas": ["education", "school", "academic"],
                "eligibility": ["educational", "state_gov", "local_gov"]
            },
            {
                "agency": "EPA",
                "program_name": "Environmental Justice Small Grants",
                "base_amount": 50000,
                "description": "Grants to address environmental justice issues in communities",
                "cfda": "66.604",
                "focus_areas": ["environment", "community", "justice"],
                "eligibility": ["nonprofit", "501c3", "community"]
            },
            {
                "agency": "USDA",
                "program_name": "Rural Community Development Initiative",
                "base_amount": 250000,
                "description": "Support for rural community development and capacity building",
                "cfda": "10.446",
                "focus_areas": ["rural", "community", "development"],
                "eligibility": ["nonprofit", "501c3", "rural"]
            },
            {
                "agency": "DOJ",
                "program_name": "Juvenile Justice and Delinquency Prevention",
                "base_amount": 300000,
                "description": "Programs to prevent juvenile delinquency and support at-risk youth",
                "cfda": "16.540",
                "focus_areas": ["youth", "justice", "prevention"],
                "eligibility": ["nonprofit", "501c3", "state_gov", "local_gov"]
            },
            {
                "agency": "HUD",
                "program_name": "Community Development Block Grant",
                "base_amount": 1000000,
                "description": "Flexible grants to address community development needs",
                "cfda": "14.218",
                "focus_areas": ["housing", "community", "development"],
                "eligibility": ["state_gov", "local_gov", "municipal"]
            },
            {
                "agency": "NSF",
                "program_name": "STEM Education and Diversity",
                "base_amount": 400000,
                "description": "Grants to improve STEM education and increase diversity",
                "cfda": "47.076",
                "focus_areas": ["education", "stem", "diversity"],
                "eligibility": ["educational", "university", "research", "nonprofit"]
            }
        ]
        
        # Filter templates by agency and alignment
        relevant_templates = []
        for template in program_templates:
            # Check agency filter
            if agencies and template["agency"] not in agencies:
                continue
            
            # Check eligibility alignment
            if eligibility_types:
                if not any(elig in template["eligibility"] for elig in eligibility_types):
                    continue
            
            # Check focus area alignment
            focus_match = False
            for profile_focus in profile.focus_areas:
                if any(focus in profile_focus.lower() for focus in template["focus_areas"]):
                    focus_match = True
                    break
            
            if focus_match or not profile.focus_areas:
                relevant_templates.append(template)
        
        # Generate opportunities from templates
        for i, template in enumerate(relevant_templates[:max_results]):
            opportunity = await self._create_government_opportunity(
                profile, template, i
            )
            opportunities.append(opportunity)
        
        # Add some variation with similar programs
        while len(opportunities) < min(max_results, 15):
            base_template = random.choice(program_templates)
            variation = await self._create_program_variation(profile, base_template, len(opportunities))
            opportunities.append(variation)
        
        return opportunities[:max_results]
    
    async def _create_government_opportunity(
        self, 
        profile: OrganizationProfile, 
        template: Dict[str, Any], 
        index: int
    ) -> DiscoveryResult:
        """Create a government opportunity from a template"""
        
        # Generate realistic deadline (30-90 days from now)
        days_ahead = random.randint(30, 90)
        deadline = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        
        # Calculate funding amount with some variation
        base_amount = template["base_amount"]
        funding_amount = int(base_amount * random.uniform(0.8, 1.3))
        
        # Calculate compatibility score
        compatibility = self._calculate_government_compatibility(profile, template)
        
        # Generate opportunity ID
        opportunity_id = f"gov_{template['cfda'].replace('.', '')}_{uuid.uuid4().hex[:8]}"
        
        # Create match factors
        match_factors = {
            "agency_alignment": template["agency"] in ["HHS", "ED", "EPA"],  # Common agencies
            "eligibility_match": self._check_eligibility_match(profile, template),
            "focus_alignment": self._check_focus_alignment_gov(profile, template),
            "funding_range_fit": self._check_funding_fit_gov(profile, funding_amount),
            "geographic_eligible": True  # Most federal grants are nationwide
        }
        
        # Identify risk factors
        risk_factors = {
            "competitive_program": funding_amount > 500000,
            "complex_application": template["agency"] in ["NSF", "HHS"],
            "matching_funds_required": template["agency"] in ["HUD", "DOJ"],
            "strict_eligibility": len(template["eligibility"]) < 3
        }
        
        return DiscoveryResult(
            organization_name=f"Department of {self.supported_agencies.get(template['agency'], template['agency'])}",
            source_type=self.funding_type,
            discovery_source=self.name,
            opportunity_id=opportunity_id,
            program_name=template["program_name"],
            description=template["description"],
            funding_amount=funding_amount,
            application_deadline=deadline,
            raw_score=compatibility,
            compatibility_score=compatibility,
            confidence_level=0.8,  # High confidence for federal programs
            match_factors=match_factors,
            risk_factors=risk_factors,
            contact_info={
                "agency": template["agency"],
                "program_office": f"{template['program_name']} Office",
                "website": f"https://grants.gov/search/?cfda={template['cfda']}",
                "email": f"grants@{template['agency'].lower()}.gov"
            },
            geographic_info={
                "scope": "national",
                "restrictions": "None",
                "preference": "Underserved areas may receive priority"
            },
            external_data={
                "cfda_number": template["cfda"],
                "agency_code": template["agency"],
                "program_type": "discretionary_grant",
                "funding_source": "federal",
                "award_type": "competitive",
                "estimated_awards": random.randint(20, 100),
                "application_deadline": deadline,
                "project_period": "1-3 years",
                "matching_requirements": "0-25% match may be required",
                "eligibility_requirements": template["eligibility"]
            }
        )
    
    async def _create_program_variation(
        self, 
        profile: OrganizationProfile, 
        base_template: Dict[str, Any], 
        index: int
    ) -> DiscoveryResult:
        """Create a variation of an existing program template"""
        
        # Create variation
        variation = base_template.copy()
        variation["program_name"] = f"{base_template['program_name']} - Special Initiative"
        variation["base_amount"] = int(base_template["base_amount"] * random.uniform(0.5, 1.5))
        variation["cfda"] = f"{base_template['cfda'][:-1]}{random.randint(1, 9)}"
        
        return await self._create_government_opportunity(profile, variation, index)
    
    def _calculate_government_compatibility(
        self, 
        profile: OrganizationProfile, 
        template: Dict[str, Any]
    ) -> float:
        """Calculate compatibility score for government opportunity"""
        score = 0.3  # Base score
        
        # Focus area alignment (30%)
        if self._check_focus_alignment_gov(profile, template):
            score += 0.3
        
        # Eligibility match (25%)
        if self._check_eligibility_match(profile, template):
            score += 0.25
        
        # Organization capacity (15%)
        if profile.annual_revenue and profile.annual_revenue >= 100000:
            score += 0.15
        elif profile.annual_revenue and profile.annual_revenue >= 50000:
            score += 0.1
        
        # Geographic alignment (10%)
        # Federal grants are typically nationwide eligible
        score += 0.1
        
        return min(score, 1.0)
    
    def _check_focus_alignment_gov(self, profile: OrganizationProfile, template: Dict[str, Any]) -> bool:
        """Check focus area alignment for government programs"""
        template_focuses = template["focus_areas"]
        profile_focuses = [focus.lower() for focus in profile.focus_areas]
        
        return any(
            any(template_focus in profile_focus for template_focus in template_focuses)
            for profile_focus in profile_focuses
        )
    
    def _check_eligibility_match(self, profile: OrganizationProfile, template: Dict[str, Any]) -> bool:
        """Check if profile matches eligibility requirements"""
        template_eligibility = template["eligibility"]
        
        # Map organization type to eligibility categories
        org_type_map = {
            "nonprofit": ["nonprofit", "501c3", "public_charity"],
            "for_profit": ["business", "private"],
            "government": ["state_gov", "local_gov", "municipal"],
            "academic": ["educational", "university", "research"],
            "healthcare": ["healthcare", "hospital", "medical"],
            "foundation": ["nonprofit", "501c3", "foundation"]
        }
        
        profile_eligibility = org_type_map.get(profile.organization_type.value, [])
        
        return any(elig in template_eligibility for elig in profile_eligibility)
    
    def _check_funding_fit_gov(self, profile: OrganizationProfile, amount: int) -> bool:
        """Check if funding amount fits profile needs"""
        min_amount = profile.funding_preferences.min_amount
        max_amount = profile.funding_preferences.max_amount
        
        if min_amount and amount < min_amount:
            return False
        if max_amount and amount > max_amount:
            return False
        
        return True
    
    def _load_agency_data(self) -> Dict[str, str]:
        """Load federal agency data"""
        return {
            "HHS": "Health and Human Services",
            "ED": "Education",
            "EPA": "Environmental Protection Agency",
            "USDA": "Agriculture",
            "DOJ": "Justice",
            "HUD": "Housing and Urban Development",
            "NSF": "National Science Foundation",
            "DOL": "Labor",
            "DOT": "Transportation",
            "DHS": "Homeland Security",
            "NIH": "National Institutes of Health",
            "CDC": "Centers for Disease Control and Prevention",
            "HRSA": "Health Resources and Services Administration"
        }
    
    def _load_cfda_data(self) -> Dict[str, str]:
        """Load CFDA (Catalog of Federal Domestic Assistance) category data"""
        return {
            "10": "Agriculture",
            "11": "Commerce",
            "12": "Defense",
            "14": "Housing and Urban Development",
            "15": "Interior",
            "16": "Justice",
            "17": "Labor",
            "19": "State",
            "20": "Transportation", 
            "21": "Treasury",
            "23": "Appalachian Regional Commission",
            "39": "General Services Administration",
            "43": "Small Business Administration",
            "45": "National Science Foundation",
            "47": "Social Security Administration",
            "59": "Small Business Administration",
            "64": "Veterans Affairs",
            "66": "Environmental Protection Agency",
            "81": "Energy",
            "84": "Education",
            "93": "Health and Human Services",
            "94": "Corporation for National and Community Service",
            "97": "Homeland Security"
        }