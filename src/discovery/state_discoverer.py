"""
State-Level Grant Discovery Engine
Discovers state and local government grant opportunities
"""
import asyncio
import uuid
import logging
from typing import Dict, List, Optional, Any, AsyncIterator
from datetime import datetime, timedelta

from .base_discoverer import BaseDiscoverer, DiscoveryResult
from src.profiles.models import OrganizationProfile, ProfileSearchParams, FundingType
from src.processors.data_collection.va_state_grants_fetch import VirginiaStateGrantsFetch


class StateDiscoverer(BaseDiscoverer):
    """Discovers state-level grant opportunities from state agencies and local foundations"""
    
    def __init__(self):
        super().__init__("State & Local Grant Discovery", FundingType.GRANTS)
        self.logger = logging.getLogger(__name__)
        self.state_processors = {
            "virginia": VirginiaStateGrantsFetch()
        }
        
        # State-specific configurations
        self.state_mappings = self._load_state_mappings()
        
        # Priority states for discovery
        self.priority_states = ["VA", "MD", "DC", "NC", "WV", "TN", "KY"]
    
    async def discover_opportunities(
        self, 
        profile: OrganizationProfile,
        search_params: ProfileSearchParams,
        max_results: int = 1000
    ) -> AsyncIterator[DiscoveryResult]:
        """Discover state-level grant opportunities"""
        
        # Determine target states from profile
        target_states = self._determine_target_states(profile)
        
        # Extract search parameters
        discovery_filters = search_params.discovery_filters or {}
        focus_areas = profile.focus_areas
        funding_range = {
            "min_amount": profile.funding_preferences.min_amount,
            "max_amount": profile.funding_preferences.max_amount
        }
        
        results_count = 0
        
        self.logger.info(f"Searching state opportunities in: {', '.join(target_states)}")
        
        # Discover opportunities by state
        for state in target_states:
            if results_count >= max_results:
                break
                
            state_limit = min(max_results - results_count, max_results // len(target_states))
            
            try:
                async for opportunity in self._discover_state_opportunities(
                    state, profile, focus_areas, funding_range, state_limit
                ):
                    if results_count < max_results:
                        results_count += 1
                        yield opportunity
                        await asyncio.sleep(self.rate_limit_delay)
                    else:
                        break
                        
            except Exception as e:
                self.logger.warning(f"Failed to search {state}: {str(e)}")
                continue
    
    async def _discover_state_opportunities(
        self,
        state: str,
        profile: OrganizationProfile,
        focus_areas: List[str],
        funding_range: Dict[str, int],
        max_results: int
    ) -> AsyncIterator[DiscoveryResult]:
        """Discover opportunities for a specific state"""
        
        state_lower = state.lower()
        
        # Route to state-specific processors
        if state_lower == "va" or state_lower == "virginia":
            async for result in self._discover_virginia_opportunities(
                profile, focus_areas, funding_range, max_results
            ):
                yield result
        else:
            # Future: Add other state processors
            # For now, generate representative mock opportunities for other states
            async for result in self._discover_generic_state_opportunities(
                state, profile, focus_areas, funding_range, min(max_results, 3)
            ):
                yield result
    
    async def _discover_virginia_opportunities(
        self,
        profile: OrganizationProfile,
        focus_areas: List[str],
        funding_range: Dict[str, int],
        max_results: int
    ) -> AsyncIterator[DiscoveryResult]:
        """Discover Virginia state opportunities using dedicated processor"""
        
        try:
            # Prepare data for Virginia state processor
            va_search_data = {
                "focus_areas": focus_areas,
                "geographic_scope": ["VA"],
                "funding_range": funding_range,
                "max_results": max_results
            }
            
            # Execute Virginia state discovery
            va_processor = self.state_processors["virginia"]
            va_results = await va_processor.process(va_search_data, {})
            
            if va_results.get("status") == "completed":
                opportunities = va_results.get("state_opportunities", [])
                
                # Convert state opportunities to discovery results
                for opportunity in opportunities:
                    discovery_result = self._convert_state_opportunity_to_result(opportunity, profile)
                    if discovery_result:
                        yield discovery_result
                        
        except Exception as e:
            self.logger.error(f"Virginia state discovery failed: {str(e)}")
            return
    
    async def _discover_generic_state_opportunities(
        self,
        state: str,
        profile: OrganizationProfile,
        focus_areas: List[str],
        funding_range: Dict[str, int],
        max_results: int
    ) -> AsyncIterator[DiscoveryResult]:
        """Generate representative opportunities for other states"""
        
        # Mock opportunities for states not yet implemented
        state_agencies = self._get_state_agency_examples(state)
        
        for i, agency in enumerate(state_agencies[:max_results]):
            opportunity = self._create_mock_state_opportunity(state, agency, profile, i)
            yield opportunity
    
    def _convert_state_opportunity_to_result(
        self,
        opportunity: Dict[str, Any],
        profile: OrganizationProfile
    ) -> Optional[DiscoveryResult]:
        """Convert state opportunity to DiscoveryResult"""
        
        try:
            # Calculate compatibility score
            compatibility = self._calculate_state_compatibility(opportunity, profile)
            
            # Create match factors
            match_factors = {
                "focus_area_alignment": self._check_state_focus_alignment(opportunity, profile),
                "geographic_alignment": self._check_state_geographic_alignment(opportunity, profile),
                "eligibility_match": self._check_state_eligibility(opportunity, profile),
                "funding_range_fit": self._check_state_funding_fit(opportunity, profile)
            }
            
            # Identify risk factors
            risk_factors = {
                "limited_funding": opportunity.get("funding_amount", 0) < 50000,
                "competitive_process": "competitive" in opportunity.get("application_process", "").lower(),
                "matching_required": bool(opportunity.get("matching_requirements")),
                "new_program": "new" in opportunity.get("description", "").lower()
            }
            
            # Handle funding amount
            funding_amount = opportunity.get("funding_amount")
            if not funding_amount and opportunity.get("funding_range"):
                funding_range = opportunity["funding_range"]
                if isinstance(funding_range, (list, tuple)) and len(funding_range) >= 2:
                    funding_amount = (funding_range[0] + funding_range[1]) // 2
            
            return DiscoveryResult(
                organization_name=opportunity.get("agency_name", "State Agency"),
                source_type=self.funding_type,
                discovery_source=f"{self.name} - {opportunity.get('data_source', 'State Database')}",
                opportunity_id=opportunity.get("opportunity_id", f"state_{uuid.uuid4().hex[:12]}"),
                program_name=opportunity.get("program_name", "State Grant Program"),
                description=opportunity.get("description", "State-level grant opportunity"),
                funding_amount=funding_amount,
                application_deadline=opportunity.get("application_deadline"),
                raw_score=compatibility,
                compatibility_score=compatibility,
                confidence_level=opportunity.get("confidence_score", 0.6),
                match_factors=match_factors,
                risk_factors=risk_factors,
                contact_info=opportunity.get("contact_info", {}),
                geographic_info={
                    "geographic_scope": opportunity.get("geographic_scope", []),
                    "target_populations": opportunity.get("target_populations", [])
                },
                external_data={
                    "agency_name": opportunity.get("agency_name"),
                    "opportunity_type": opportunity.get("opportunity_type"),
                    "focus_area": opportunity.get("focus_area"),
                    "eligibility_requirements": opportunity.get("eligibility_requirements", []),
                    "application_process": opportunity.get("application_process", "online"),
                    "program_duration": opportunity.get("program_duration"),
                    "matching_requirements": opportunity.get("matching_requirements"),
                    "data_source": opportunity.get("data_source")
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error converting state opportunity: {str(e)}")
            return None
    
    def _create_mock_state_opportunity(
        self,
        state: str,
        agency_info: Dict[str, Any],
        profile: OrganizationProfile,
        index: int
    ) -> DiscoveryResult:
        """Create mock state opportunity for states not yet implemented"""
        
        # Generate realistic opportunity details
        program_types = ["Community Grant", "Capacity Building Grant", "Innovation Fund", "Partnership Initiative"]
        program_type = program_types[index % len(program_types)]
        program_name = f"{agency_info['name']} {program_type}"
        
        # Generate funding amount based on agency type
        base_amounts = {"health": 150000, "education": 100000, "social_services": 75000, "environment": 125000}
        base_amount = base_amounts.get(agency_info.get("focus"), 100000)
        funding_amount = base_amount + (index * 10000)
        
        # Generate deadline
        deadline = (datetime.now() + timedelta(days=60 + (index * 30))).strftime("%Y-%m-%d")
        
        # Calculate compatibility
        compatibility = 0.6 + (0.1 * (3 - index))  # Decreasing compatibility
        
        return DiscoveryResult(
            organization_name=agency_info["name"],
            source_type=self.funding_type,
            discovery_source=f"{self.name} - {state} State Database",
            opportunity_id=f"{state.lower()}_state_{uuid.uuid4().hex[:8]}",
            program_name=program_name,
            description=f"{agency_info['name']} funding opportunity supporting {', '.join(profile.focus_areas[:2])} initiatives in {state}.",
            funding_amount=funding_amount,
            application_deadline=deadline,
            raw_score=compatibility,
            compatibility_score=compatibility,
            confidence_level=0.5,  # Lower confidence for mock data
            match_factors={
                "focus_area_alignment": True,
                "geographic_alignment": True,
                "eligibility_match": True,
                "funding_range_fit": True
            },
            risk_factors={
                "state_budget_dependent": True,
                "annual_competition": True,
                "limited_funding": funding_amount < 100000,
                "mock_data": True  # Indicate this is mock data
            },
            contact_info={
                "email": f"grants@{agency_info['name'].lower().replace(' ', '')}.{state.lower()}.gov",
                "website": f"https://www.{agency_info['name'].lower().replace(' ', '')}.{state.lower()}.gov"
            },
            geographic_info={
                "geographic_scope": [state, f"{state} localities"],
                "target_populations": profile.target_populations[:2]
            },
            external_data={
                "agency_type": agency_info.get("focus", "general"),
                "state": state,
                "opportunity_type": "state_grant",
                "data_source": f"{state}_state_mock",
                "note": "Mock opportunity - actual opportunities available through state-specific integration"
            }
        )
    
    def _calculate_state_compatibility(self, opportunity: Dict[str, Any], profile: OrganizationProfile) -> float:
        """Calculate compatibility score for state opportunity"""
        score = 0.3  # Base score
        
        # Focus area alignment (35%)
        if self._check_state_focus_alignment(opportunity, profile):
            score += 0.35
        
        # Geographic alignment (25%)
        if self._check_state_geographic_alignment(opportunity, profile):
            score += 0.25
        
        # Eligibility match (25%)
        if self._check_state_eligibility(opportunity, profile):
            score += 0.25
        
        # Funding range fit (15%)
        if self._check_state_funding_fit(opportunity, profile):
            score += 0.15
        
        return min(score, 1.0)
    
    def _check_state_focus_alignment(self, opportunity: Dict[str, Any], profile: OrganizationProfile) -> bool:
        """Check focus area alignment for state opportunity"""
        opportunity_text = (
            opportunity.get("focus_area", "") + " " +
            opportunity.get("description", "") + " " +
            " ".join(opportunity.get("target_populations", []))
        ).lower()
        
        for focus in profile.focus_areas:
            focus_terms = focus.lower().split()
            if any(term in opportunity_text for term in focus_terms):
                return True
        
        return False
    
    def _check_state_geographic_alignment(self, opportunity: Dict[str, Any], profile: OrganizationProfile) -> bool:
        """Check geographic alignment for state opportunity"""
        if not profile.geographic_scope.states:
            return True  # No geographic restrictions
        
        opportunity_scope = opportunity.get("geographic_scope", [])
        profile_states = set(profile.geographic_scope.states)
        
        # Check for state overlap
        for scope in opportunity_scope:
            if any(state in scope for state in profile_states):
                return True
        
        return False
    
    def _check_state_eligibility(self, opportunity: Dict[str, Any], profile: OrganizationProfile) -> bool:
        """Check eligibility alignment for state opportunity"""
        requirements = opportunity.get("eligibility_requirements", [])
        
        if not requirements:
            return True  # No specific requirements
        
        # Check for 501(c)(3) requirement
        if profile.organization_type.value == "nonprofit":
            for req in requirements:
                if "501(c)(3)" in req or "nonprofit" in req.lower():
                    return True
        
        # Check for general organizational alignment
        org_type_keywords = {
            "nonprofit": ["nonprofit", "community", "charitable"],
            "academic": ["university", "college", "academic", "educational"],
            "healthcare": ["health", "medical", "clinic", "hospital"]
        }
        
        profile_keywords = org_type_keywords.get(profile.organization_type.value, [])
        requirements_text = " ".join(requirements).lower()
        
        return any(keyword in requirements_text for keyword in profile_keywords)
    
    def _check_state_funding_fit(self, opportunity: Dict[str, Any], profile: OrganizationProfile) -> bool:
        """Check funding amount fit for state opportunity"""
        funding_amount = opportunity.get("funding_amount")
        funding_range = opportunity.get("funding_range")
        
        if not funding_amount and not funding_range:
            return True  # No funding restrictions
        
        min_preferred = profile.funding_preferences.min_amount
        max_preferred = profile.funding_preferences.max_amount
        
        if funding_amount:
            if min_preferred and funding_amount < min_preferred:
                return False
            if max_preferred and funding_amount > max_preferred:
                return False
        
        if funding_range and isinstance(funding_range, (list, tuple)) and len(funding_range) >= 2:
            range_min, range_max = funding_range[0], funding_range[1]
            if max_preferred and range_min > max_preferred:
                return False
            if min_preferred and range_max < min_preferred:
                return False
        
        return True
    
    def _determine_target_states(self, profile: OrganizationProfile) -> List[str]:
        """Determine target states for discovery based on profile"""
        
        # Primary: Profile geographic scope
        target_states = list(profile.geographic_scope.states) if profile.geographic_scope.states else []
        
        # If nationwide or no specific states, use priority states
        if profile.geographic_scope.nationwide or not target_states:
            target_states = self.priority_states[:3]  # Focus on top 3 priority states
        
        # Ensure we have at least one state
        if not target_states:
            target_states = ["VA"]  # Default to Virginia
        
        return target_states
    
    def _get_state_agency_examples(self, state: str) -> List[Dict[str, Any]]:
        """Get example state agencies for mock opportunities"""
        
        generic_agencies = [
            {"name": f"{state} Department of Health", "focus": "health"},
            {"name": f"{state} Department of Education", "focus": "education"},
            {"name": f"{state} Department of Social Services", "focus": "social_services"},
            {"name": f"{state} Environmental Agency", "focus": "environment"}
        ]
        
        return generic_agencies
    
    def _load_state_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Load state-specific configuration mappings"""
        
        return {
            "VA": {
                "full_name": "Virginia",
                "processor_available": True,
                "priority_level": 5,
                "agency_count": 10,
                "data_quality": "high"
            },
            "MD": {
                "full_name": "Maryland", 
                "processor_available": False,
                "priority_level": 3,
                "agency_count": 8,
                "data_quality": "medium"
            },
            "DC": {
                "full_name": "District of Columbia",
                "processor_available": False, 
                "priority_level": 3,
                "agency_count": 6,
                "data_quality": "medium"
            },
            "NC": {
                "full_name": "North Carolina",
                "processor_available": False,
                "priority_level": 2,
                "agency_count": 12,
                "data_quality": "medium"
            }
        }
    
    async def validate_search_params(self, search_params: ProfileSearchParams) -> bool:
        """Validate search parameters for state discovery"""
        # State discovery is flexible - basic validation sufficient
        return True
    
    async def get_discoverer_status(self) -> Dict[str, Any]:
        """Get current status of state discoverer"""
        
        return {
            "name": self.name,
            "funding_type": self.funding_type.value,
            "enabled": self.enabled,
            "status": "operational_multi_state",
            "state_processors": {
                "virginia": "operational_dedicated",
                "maryland": "mock_data_available",
                "north_carolina": "mock_data_available", 
                "district_of_columbia": "mock_data_available"
            },
            "total_states_supported": len(self.state_mappings),
            "priority_states": self.priority_states,
            "last_check": datetime.now().isoformat(),
            "capabilities": {
                "virginia_integration": True,
                "multi_state_discovery": True,
                "state_agency_mapping": True,
                "geographic_filtering": True,
                "mock_data_fallback": True,
                "focus_area_alignment": True,
                "eligibility_matching": True
            },
            "data_sources": {
                "va_dept_health": "operational",
                "va_dept_social_services": "operational", 
                "va_community_foundations": "operational",
                "va_dept_education": "operational",
                "other_va_agencies": "operational",
                "other_states": "mock_data"
            },
            "note": "Virginia state integration complete. Other states use representative mock data pending dedicated processors."
        }