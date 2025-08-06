"""
Nonprofit/Foundation Discovery Engine
Integrates with existing ProPublica and 990 filing systems for grant opportunities
"""
import asyncio
import uuid
from typing import Dict, List, Optional, Any, AsyncIterator
from datetime import datetime

from .base_discoverer import BaseDiscoverer, DiscoveryResult
from src.profiles.models import OrganizationProfile, ProfileSearchParams, FundingType
from src.core.workflow_engine import get_workflow_engine
from src.core.data_models import WorkflowConfig


class NonprofitDiscoverer(BaseDiscoverer):
    """Discovers grant opportunities from nonprofit foundations and charitable organizations"""
    
    def __init__(self):
        super().__init__("ProPublica Nonprofit Foundation Discovery", FundingType.GRANTS)
        self.workflow_engine = get_workflow_engine()
    
    async def discover_opportunities(
        self, 
        profile: OrganizationProfile,
        search_params: ProfileSearchParams,
        max_results: int = 100
    ) -> AsyncIterator[DiscoveryResult]:
        """Discover nonprofit grant opportunities using existing workflow system"""
        
        # Convert search params to workflow configuration
        workflow_config = self._create_workflow_config(profile, search_params, max_results)
        
        try:
            # Execute the existing workflow
            workflow_results = await self.workflow_engine.execute_workflow(workflow_config)
            
            # Stream results as DiscoveryResult objects
            raw_results = workflow_results.get("results", [])
            
            for i, result in enumerate(raw_results):
                if i >= max_results:
                    break
                
                # Convert workflow result to DiscoveryResult
                discovery_result = await self._convert_to_discovery_result(profile, result)
                yield discovery_result
                
                # Respect rate limiting
                if i < len(raw_results) - 1:
                    await asyncio.sleep(self.rate_limit_delay)
        
        except Exception as e:
            # Yield error result
            yield DiscoveryResult(
                organization_name="Discovery Error",
                source_type=self.funding_type,
                discovery_source=self.name,
                opportunity_id=f"error_{uuid.uuid4().hex[:8]}",
                description=f"Error during nonprofit discovery: {str(e)}",
                raw_score=0.0,
                compatibility_score=0.0,
                confidence_level=0.0,
                external_data={"error": str(e), "error_type": type(e).__name__}
            )
    
    async def validate_search_params(self, search_params: ProfileSearchParams) -> bool:
        """Validate search parameters for nonprofit discovery"""
        discovery_filters = search_params.discovery_filters
        
        # Check required fields
        if not discovery_filters:
            return False
        
        # Validate NTEE codes if provided
        ntee_codes = discovery_filters.get("ntee_codes", [])
        if ntee_codes:
            valid_ntee_pattern = r'^[A-Z]\d{2}$'
            import re
            if not all(re.match(valid_ntee_pattern, code) for code in ntee_codes):
                return False
        
        # Validate geographic scope
        geo_scope = discovery_filters.get("geographic_scope", {})
        states = geo_scope.get("states", [])
        if states:
            valid_states = {
                'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
            }
            if not all(state in valid_states for state in states):
                return False
        
        return True
    
    async def get_discoverer_status(self) -> Dict[str, Any]:
        """Get current status of nonprofit discoverer"""
        try:
            # Test workflow engine availability
            engine_status = await self._test_workflow_engine()
            
            return {
                "name": self.name,
                "funding_type": self.funding_type.value,
                "enabled": self.enabled,
                "status": "healthy" if engine_status else "error",
                "workflow_engine_available": engine_status,
                "last_check": datetime.now().isoformat(),
                "capabilities": {
                    "max_results": 1000,
                    "supports_ntee_filtering": True,
                    "supports_geographic_filtering": True,
                    "supports_revenue_filtering": True,
                    "supports_intelligent_classification": True
                }
            }
        except Exception as e:
            return {
                "name": self.name,
                "funding_type": self.funding_type.value,
                "enabled": self.enabled,
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    def _create_workflow_config(
        self, 
        profile: OrganizationProfile, 
        search_params: ProfileSearchParams, 
        max_results: int
    ) -> WorkflowConfig:
        """Convert profile search params to workflow configuration"""
        
        discovery_filters = search_params.discovery_filters
        
        # Extract parameters
        geo_scope = discovery_filters.get("geographic_scope", {})
        states = geo_scope.get("states", ["VA"])  # Default to Virginia
        
        ntee_codes = discovery_filters.get("ntee_codes", [])
        if not ntee_codes:
            # Default NTEE codes based on common focus areas
            ntee_codes = ["E21", "E30", "F30", "P30", "S30"]
        
        funding_range = discovery_filters.get("funding_range", {})
        min_revenue = funding_range.get("min_amount", 50000)
        
        # Create workflow configuration
        config = WorkflowConfig(
            workflow_id=f"nonprofit_discovery_{profile.profile_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=f"Nonprofit Discovery: {profile.name}",
            target_ein=profile.ein,
            states=states[:5],  # Limit to 5 states for performance
            ntee_codes=ntee_codes[:10],  # Limit NTEE codes
            min_revenue=min_revenue,
            max_results=min(max_results, 500),  # Cap at 500 for performance
            include_classified_organizations=True,
            classification_score_threshold=search_params.min_compatibility_threshold
        )
        
        return config
    
    async def _convert_to_discovery_result(
        self, 
        profile: OrganizationProfile, 
        workflow_result: Dict[str, Any]
    ) -> DiscoveryResult:
        """Convert workflow result to standardized DiscoveryResult"""
        
        # Extract basic information
        org_name = workflow_result.get("organization_name", "Unknown Organization")
        ein = workflow_result.get("ein", "")
        
        # Calculate compatibility score using existing composite score
        raw_score = workflow_result.get("composite_score", 0.0)
        compatibility_score = self.calculate_compatibility_score(profile, workflow_result)
        
        # Analyze match factors
        match_factors = {
            "ntee_alignment": self._analyze_ntee_alignment(profile, workflow_result),
            "geographic_match": self._analyze_geographic_match(profile, workflow_result),
            "financial_capacity": self._analyze_financial_capacity(workflow_result),
            "program_alignment": self._analyze_program_alignment(profile, workflow_result),
            "filing_recency": self._analyze_filing_recency(workflow_result)
        }
        
        # Identify risk factors
        risk_factors = {
            "low_assets": workflow_result.get("asset_amount", 0) < 100000,
            "outdated_filing": self._check_filing_age(workflow_result),
            "geographic_distance": not match_factors["geographic_match"],
            "focus_mismatch": not match_factors["ntee_alignment"]
        }
        
        # Prepare contact and geographic info
        contact_info = {
            "address": workflow_result.get("address", ""),
            "city": workflow_result.get("city", ""),
            "state": workflow_result.get("state", ""),
            "zip_code": workflow_result.get("zip_code", ""),
            "ein": ein
        }
        
        geographic_info = {
            "state": workflow_result.get("state", ""),
            "city": workflow_result.get("city", ""),
            "region": self._determine_region(workflow_result.get("state", ""))
        }
        
        # Confidence level based on data quality
        confidence_level = self._calculate_confidence_level(workflow_result)
        
        return DiscoveryResult(
            organization_name=org_name,
            source_type=self.funding_type,
            discovery_source=self.name,
            opportunity_id=f"nonprofit_{ein}_{uuid.uuid4().hex[:8]}",
            program_name=f"{org_name} Grant Program",
            description=f"Grant-making organization with focus on {workflow_result.get('ntee_description', 'various causes')}",
            funding_amount=self._estimate_funding_capacity(workflow_result),
            raw_score=raw_score,
            compatibility_score=compatibility_score,
            confidence_level=confidence_level,
            match_factors=match_factors,
            risk_factors=risk_factors,
            contact_info=contact_info,
            geographic_info=geographic_info,
            external_data={
                "ein": ein,
                "ntee_code": workflow_result.get("ntee_code", ""),
                "asset_amount": workflow_result.get("asset_amount"),
                "revenue_amount": workflow_result.get("revenue_amount"),
                "filing_year": workflow_result.get("filing_year"),
                "data_source": workflow_result.get("data_source", "ProPublica"),
                "composite_score_breakdown": workflow_result.get("score_breakdown", {}),
                "classification_data": workflow_result.get("classification_results", {})
            }
        )
    
    def _analyze_ntee_alignment(self, profile: OrganizationProfile, result: Dict[str, Any]) -> bool:
        """Analyze NTEE code alignment with profile focus areas"""
        result_ntee = result.get("ntee_code", "")
        if not result_ntee:
            return False
        
        # Map focus areas to NTEE categories
        focus_categories = set()
        for focus in profile.focus_areas:
            focus_lower = focus.lower()
            if any(term in focus_lower for term in ["health", "medical", "wellness"]):
                focus_categories.update(["E", "F"])
            elif any(term in focus_lower for term in ["education", "school", "learning"]):
                focus_categories.add("B")
            elif any(term in focus_lower for term in ["community", "social", "human"]):
                focus_categories.update(["P", "S"])
            elif any(term in focus_lower for term in ["environment", "conservation"]):
                focus_categories.add("C")
            elif any(term in focus_lower for term in ["arts", "culture", "music"]):
                focus_categories.add("A")
        
        return any(result_ntee.startswith(cat) for cat in focus_categories)
    
    def _analyze_geographic_match(self, profile: OrganizationProfile, result: Dict[str, Any]) -> bool:
        """Analyze geographic alignment"""
        result_state = result.get("state", "")
        profile_states = profile.geographic_scope.states
        
        if profile.geographic_scope.nationwide:
            return True
        
        if not profile_states:
            return True  # No geographic restrictions
        
        return result_state in profile_states
    
    def _analyze_financial_capacity(self, result: Dict[str, Any]) -> str:
        """Analyze financial capacity level"""
        revenue = result.get("revenue_amount", 0)
        assets = result.get("asset_amount", 0)
        
        max_financial = max(revenue, assets)
        
        if max_financial >= 10000000:
            return "high"
        elif max_financial >= 1000000:
            return "medium"
        elif max_financial >= 100000:
            return "low"
        else:
            return "very_low"
    
    def _analyze_program_alignment(self, profile: OrganizationProfile, result: Dict[str, Any]) -> bool:
        """Analyze program alignment potential"""
        # This is a simplified analysis - could be enhanced with AI/ML
        return self._analyze_ntee_alignment(profile, result)
    
    def _analyze_filing_recency(self, result: Dict[str, Any]) -> bool:
        """Check if organization has recent filings"""
        filing_year = result.get("filing_year", 0)
        current_year = datetime.now().year
        
        return (current_year - filing_year) <= 3  # Filed within last 3 years
    
    def _check_filing_age(self, result: Dict[str, Any]) -> bool:
        """Check if filings are outdated (risk factor)"""
        return not self._analyze_filing_recency(result)
    
    def _estimate_funding_capacity(self, result: Dict[str, Any]) -> Optional[int]:
        """Estimate potential funding capacity"""
        revenue = result.get("revenue_amount", 0)
        assets = result.get("asset_amount", 0)
        
        if not revenue and not assets:
            return None
        
        # Rough estimate: foundations typically grant 5-10% of assets or revenue annually
        max_financial = max(revenue, assets)
        estimated_capacity = int(max_financial * 0.075)  # 7.5% average
        
        return max(estimated_capacity, 1000)  # Minimum $1,000
    
    def _calculate_confidence_level(self, result: Dict[str, Any]) -> float:
        """Calculate confidence level based on data quality"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for complete data
        if result.get("revenue_amount"):
            confidence += 0.1
        if result.get("asset_amount"):
            confidence += 0.1
        if result.get("ntee_code"):
            confidence += 0.1
        if result.get("address"):
            confidence += 0.1
        if self._analyze_filing_recency(result):
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _determine_region(self, state: str) -> str:
        """Determine region from state code"""
        region_map = {
            'northeast': ['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA'],
            'southeast': ['DE', 'MD', 'DC', 'VA', 'WV', 'KY', 'TN', 'NC', 'SC', 'GA', 'FL', 'AL', 'MS', 'AR', 'LA'],
            'midwest': ['OH', 'MI', 'IN', 'WI', 'IL', 'MN', 'IA', 'MO', 'ND', 'SD', 'NE', 'KS'],
            'southwest': ['TX', 'OK', 'NM', 'AZ'],
            'west': ['MT', 'WY', 'CO', 'UT', 'ID', 'WA', 'OR', 'NV', 'CA', 'AK', 'HI']
        }
        
        for region, states in region_map.items():
            if state in states:
                return region
        
        return 'unknown'
    
    async def _test_workflow_engine(self) -> bool:
        """Test if workflow engine is available and healthy"""
        try:
            # Simple test - get engine status
            engine = get_workflow_engine()
            stats = engine.get_workflow_statistics()
            return isinstance(stats, dict)
        except Exception:
            return False