"""
Base classes and interfaces for the multi-track discovery engine
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.profiles.models import OrganizationProfile, ProfileSearchParams, FundingType


class DiscoveryStatus(str, Enum):
    """Discovery execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class FunnelStage(str, Enum):
    """Grant opportunity funnel stages"""
    PROSPECTS = "prospects"                    # Initial ProPublica/API broad filtering
    QUALIFIED_PROSPECTS = "qualified_prospects" # 990 XML/eligibility detailed analysis  
    CANDIDATES = "candidates"                  # Mission/eligibility matched
    TARGETS = "targets"                        # High-potential for deep research
    OPPORTUNITIES = "opportunities"            # Decision-ready final stage


@dataclass
class DiscoveryResult:
    """Single opportunity discovery result"""
    # Basic Information
    organization_name: str
    source_type: FundingType
    discovery_source: str  # e.g., "ProPublica", "Grants.gov", "Corporate Database"
    
    # Opportunity Details
    opportunity_id: str
    program_name: Optional[str] = None
    description: Optional[str] = None
    funding_amount: Optional[int] = None
    application_deadline: Optional[str] = None
    
    # Scoring and Matching
    raw_score: float = 0.0
    compatibility_score: float = 0.0
    confidence_level: float = 0.0
    
    # Matching Analysis
    match_factors: Dict[str, Any] = None
    risk_factors: Dict[str, Any] = None
    
    # Contact and Location
    contact_info: Dict[str, str] = None
    geographic_info: Dict[str, str] = None
    
    # Funnel Tracking
    funnel_stage: FunnelStage = FunnelStage.PROSPECTS
    stage_updated_at: Optional[datetime] = None
    stage_notes: Optional[str] = None
    
    # Metadata
    external_data: Dict[str, Any] = None
    discovered_at: datetime = None
    
    def __post_init__(self):
        if self.match_factors is None:
            self.match_factors = {}
        if self.risk_factors is None:
            self.risk_factors = {}
        if self.contact_info is None:
            self.contact_info = {}
        if self.geographic_info is None:
            self.geographic_info = {}
        if self.external_data is None:
            self.external_data = {}
        if self.discovered_at is None:
            self.discovered_at = datetime.now()
        if self.stage_updated_at is None:
            self.stage_updated_at = datetime.now()
    
    def promote_to_next_stage(self, notes: Optional[str] = None) -> bool:
        """Move opportunity to next funnel stage"""
        stage_order = [
            FunnelStage.PROSPECTS,
            FunnelStage.QUALIFIED_PROSPECTS, 
            FunnelStage.CANDIDATES,
            FunnelStage.TARGETS,
            FunnelStage.OPPORTUNITIES
        ]
        
        current_index = stage_order.index(self.funnel_stage)
        if current_index < len(stage_order) - 1:
            self.funnel_stage = stage_order[current_index + 1]
            self.stage_updated_at = datetime.now()
            if notes:
                self.stage_notes = notes
            return True
        return False
    
    def demote_to_previous_stage(self, notes: Optional[str] = None) -> bool:
        """Move opportunity to previous funnel stage"""
        stage_order = [
            FunnelStage.PROSPECTS,
            FunnelStage.QUALIFIED_PROSPECTS,
            FunnelStage.CANDIDATES, 
            FunnelStage.TARGETS,
            FunnelStage.OPPORTUNITIES
        ]
        
        current_index = stage_order.index(self.funnel_stage)
        if current_index > 0:
            self.funnel_stage = stage_order[current_index - 1]
            self.stage_updated_at = datetime.now()
            if notes:
                self.stage_notes = notes
            return True
        return False
    
    def set_stage(self, new_stage: FunnelStage, notes: Optional[str] = None) -> None:
        """Set opportunity to specific funnel stage"""
        self.funnel_stage = new_stage
        self.stage_updated_at = datetime.now()
        if notes:
            self.stage_notes = notes
    
    def get_stage_color(self) -> str:
        """Get display color for current funnel stage"""
        stage_colors = {
            FunnelStage.PROSPECTS: "gray",
            FunnelStage.QUALIFIED_PROSPECTS: "yellow",
            FunnelStage.CANDIDATES: "orange", 
            FunnelStage.TARGETS: "blue",
            FunnelStage.OPPORTUNITIES: "green"
        }
        return stage_colors.get(self.funnel_stage, "gray")
    
    def get_stage_display_name(self) -> str:
        """Get human-readable stage name"""
        stage_names = {
            FunnelStage.PROSPECTS: "Prospects",
            FunnelStage.QUALIFIED_PROSPECTS: "Qualified",
            FunnelStage.CANDIDATES: "Candidates",
            FunnelStage.TARGETS: "Targets", 
            FunnelStage.OPPORTUNITIES: "Opportunities"
        }
        return stage_names.get(self.funnel_stage, "Unknown")



@dataclass
class DiscoverySession:
    """Discovery session tracking and metadata"""
    session_id: str
    profile_id: str
    profile_name: str
    funding_types: List[FundingType]
    search_params: Dict[FundingType, ProfileSearchParams]
    
    # Session State
    status: DiscoveryStatus = DiscoveryStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results Tracking
    total_results: int = 0
    results_by_type: Dict[FundingType, int] = None
    errors_by_type: Dict[FundingType, str] = None
    
    # Performance Metrics
    execution_time_seconds: Optional[float] = None
    api_calls_made: int = 0
    cache_hits: int = 0
    
    def __post_init__(self):
        if self.results_by_type is None:
            self.results_by_type = {}
        if self.errors_by_type is None:
            self.errors_by_type = {}


class BaseDiscoverer(ABC):
    """Abstract base class for opportunity discoverers"""
    
    def __init__(self, name: str, funding_type: FundingType):
        self.name = name
        self.funding_type = funding_type
        self.enabled = True
        self.rate_limit_delay = 0.5  # seconds between requests
        self.max_retries = 3
        self.timeout_seconds = 30
    
    @abstractmethod
    async def discover_opportunities(
        self, 
        profile: OrganizationProfile,
        search_params: ProfileSearchParams,
        max_results: int = 100
    ) -> AsyncIterator[DiscoveryResult]:
        """
        Discover opportunities for a profile
        
        Args:
            profile: Organization profile to search for
            search_params: Search parameters generated from profile
            max_results: Maximum number of results to return
            
        Yields:
            DiscoveryResult: Individual opportunity results
        """
        pass
    
    @abstractmethod
    async def validate_search_params(self, search_params: ProfileSearchParams) -> bool:
        """Validate that search parameters are compatible with this discoverer"""
        pass
    
    @abstractmethod
    async def get_discoverer_status(self) -> Dict[str, Any]:
        """Get current status and health of the discoverer"""
        pass
    
    async def pre_discovery_setup(self, profile: OrganizationProfile) -> bool:
        """Setup before discovery starts (authentication, validation, etc.)"""
        return True
    
    async def post_discovery_cleanup(self, session: DiscoverySession) -> None:
        """Cleanup after discovery completes"""
        pass
    
    def calculate_compatibility_score(
        self, 
        profile: OrganizationProfile, 
        raw_result: Dict[str, Any]
    ) -> float:
        """Calculate compatibility score between profile and opportunity"""
        # Default implementation - can be overridden by specific discoverers
        base_score = 0.5
        
        # Geographic alignment
        if self._check_geographic_alignment(profile, raw_result):
            base_score += 0.2
        
        # Focus area alignment  
        if self._check_focus_alignment(profile, raw_result):
            base_score += 0.2
        
        # Funding amount fit
        if self._check_funding_fit(profile, raw_result):
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _check_geographic_alignment(self, profile: OrganizationProfile, result: Dict[str, Any]) -> bool:
        """Check if opportunity aligns geographically with profile"""
        if not profile.geographic_scope.states:
            return True  # No geographic restrictions
        
        result_state = result.get("state", "")
        return result_state in profile.geographic_scope.states
    
    def _check_focus_alignment(self, profile: OrganizationProfile, result: Dict[str, Any]) -> bool:
        """Check if opportunity aligns with profile focus areas"""
        if not profile.focus_areas:
            return True
        
        result_description = result.get("description", "").lower()
        result_keywords = result.get("keywords", [])
        
        # Check if any focus area keywords appear in opportunity
        for focus in profile.focus_areas:
            focus_lower = focus.lower()
            if focus_lower in result_description:
                return True
            if any(focus_lower in keyword.lower() for keyword in result_keywords):
                return True
        
        return False
    
    def _check_funding_fit(self, profile: OrganizationProfile, result: Dict[str, Any]) -> bool:
        """Check if opportunity funding amount fits profile needs"""
        result_amount = result.get("funding_amount")
        if not result_amount:
            return True  # No funding amount specified
        
        min_amount = profile.funding_preferences.min_amount
        max_amount = profile.funding_preferences.max_amount
        
        if min_amount and result_amount < min_amount:
            return False
        if max_amount and result_amount > max_amount:
            return False
        
        return True


class DiscovererRegistry:
    """Registry for managing multiple discovery sources"""
    
    def __init__(self):
        self._discoverers: Dict[FundingType, List[BaseDiscoverer]] = {}
        self._enabled_discoverers: Dict[FundingType, List[BaseDiscoverer]] = {}
    
    def register_discoverer(self, discoverer: BaseDiscoverer) -> None:
        """Register a new discoverer"""
        funding_type = discoverer.funding_type
        
        if funding_type not in self._discoverers:
            self._discoverers[funding_type] = []
        
        self._discoverers[funding_type].append(discoverer)
        self._update_enabled_cache()
    
    def get_discoverers_for_type(self, funding_type: FundingType) -> List[BaseDiscoverer]:
        """Get all enabled discoverers for a funding type"""
        return self._enabled_discoverers.get(funding_type, [])
    
    def get_all_discoverers(self) -> List[BaseDiscoverer]:
        """Get all registered discoverers"""
        all_discoverers = []
        for discoverer_list in self._discoverers.values():
            all_discoverers.extend(discoverer_list)
        return all_discoverers
    
    def enable_discoverer(self, name: str) -> bool:
        """Enable a discoverer by name"""
        for discoverer in self.get_all_discoverers():
            if discoverer.name == name:
                discoverer.enabled = True
                self._update_enabled_cache()
                return True
        return False
    
    def disable_discoverer(self, name: str) -> bool:
        """Disable a discoverer by name"""
        for discoverer in self.get_all_discoverers():
            if discoverer.name == name:
                discoverer.enabled = False
                self._update_enabled_cache()
                return True
        return False
    
    def _update_enabled_cache(self):
        """Update the cache of enabled discoverers"""
        self._enabled_discoverers.clear()
        
        for funding_type, discoverers in self._discoverers.items():
            enabled = [d for d in discoverers if d.enabled]
            if enabled:
                self._enabled_discoverers[funding_type] = enabled
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get status of all discoverers in registry"""
        status = {
            "total_discoverers": len(self.get_all_discoverers()),
            "enabled_discoverers": len([d for d in self.get_all_discoverers() if d.enabled]),
            "by_funding_type": {},
            "discoverers": []
        }
        
        for funding_type in FundingType:
            discoverers = self._discoverers.get(funding_type, [])
            enabled = len([d for d in discoverers if d.enabled])
            status["by_funding_type"][funding_type.value] = {
                "total": len(discoverers),
                "enabled": enabled
            }
        
        for discoverer in self.get_all_discoverers():
            status["discoverers"].append({
                "name": discoverer.name,
                "funding_type": discoverer.funding_type.value,
                "enabled": discoverer.enabled,
                "rate_limit_delay": discoverer.rate_limit_delay,
                "max_retries": discoverer.max_retries
            })
        
        return status


# Global registry instance
discoverer_registry = DiscovererRegistry()