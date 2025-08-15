"""
Discovery Strategy Pattern
Simplified discovery architecture using strategy pattern with unified execution.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

from ..core.data_models import (
    BaseOpportunity, 
    GovernmentOpportunity, 
    FoundationOpportunity, 
    CorporateOpportunity,
    OpportunityCollection,
    FundingSourceType
)
from ..profiles.models import OrganizationProfile
from ..clients import (
    GrantsGovClient, 
    FoundationDirectoryClient, 
    USASpendingClient, 
    ProPublicaClient, 
    VAStateClient
)


class DiscoveryStrategy(ABC):
    """
    Abstract base class for discovery strategies.
    
    Each strategy handles one type of funding source
    (government, foundation, corporate) and knows how to:
    1. Search for opportunities 
    2. Convert raw data to unified opportunity models
    3. Score opportunities based on organization profile
    """
    
    def __init__(self, strategy_name: str, source_type: FundingSourceType):
        self.strategy_name = strategy_name
        self.source_type = source_type
        self.logger = logging.getLogger(f"discovery.{strategy_name}")
    
    @abstractmethod
    async def discover_opportunities(self, 
                                   profile: OrganizationProfile,
                                   max_results: int = 100,
                                   progress_callback: Optional[Callable] = None) -> List[BaseOpportunity]:
        """
        Discover opportunities for the given organization profile
        
        Args:
            profile: Organization profile to match against
            max_results: Maximum number of opportunities to return
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of discovered opportunities
        """
        pass
    
    @abstractmethod
    def calculate_relevance_score(self, 
                                opportunity: BaseOpportunity, 
                                profile: OrganizationProfile) -> float:
        """
        Calculate relevance score for an opportunity
        
        Args:
            opportunity: Opportunity to score
            profile: Organization profile to match against
            
        Returns:
            Relevance score (0-100)
        """
        pass
    
    async def get_strategy_status(self) -> Dict[str, Any]:
        """Get status information about this strategy"""
        return {
            'name': self.strategy_name,
            'source_type': self.source_type,
            'status': 'active'
        }
    
    def _extract_keywords_from_profile(self, profile: OrganizationProfile) -> List[str]:
        """Extract relevant keywords from organization profile"""
        keywords = []
        
        # From NTEE description
        if profile.ntee_description:
            keywords.extend(profile.ntee_description.lower().split())
        
        # From mission description  
        if hasattr(profile, 'mission_description') and profile.mission_description:
            keywords.extend(profile.mission_description.lower().split())
        
        # From activity description
        if hasattr(profile, 'activity_description') and profile.activity_description:
            keywords.extend(profile.activity_description.lower().split())
        
        # Clean and filter keywords
        meaningful_keywords = []
        for keyword in keywords:
            keyword = keyword.strip('.,!?;:"()[]{}')
            if len(keyword) > 3 and keyword.isalpha():
                meaningful_keywords.append(keyword)
        
        return list(set(meaningful_keywords))[:10]  # Top 10 unique keywords


class GovernmentDiscoveryStrategy(DiscoveryStrategy):
    """Strategy for discovering federal and state government opportunities"""
    
    def __init__(self):
        super().__init__("government", FundingSourceType.GOVERNMENT_FEDERAL)
        # Phase 2 Integration: Use migrated processors instead of direct clients
        self.grants_gov_processor = None
        self.usaspending_processor = None
        self.va_state_processor = None
        
        # Legacy client fallback for immediate operation
        self.grants_gov_client = GrantsGovClient()
        self.usaspending_client = USASpendingClient()
        self.va_state_client = VAStateClient()
        
        # Initialize processors
        self._initialize_processors()
    
    def _initialize_processors(self):
        """Initialize Phase 2 migrated processors"""
        try:
            # Import migrated processors
            from ..processors.data_collection.grants_gov_fetch import GrantsGovFetchProcessor
            from ..processors.data_collection.usaspending_fetch import USASpendingFetchProcessor
            from ..processors.data_collection.va_state_grants_fetch import VirginiaStateGrantsFetch
            
            self.grants_gov_processor = GrantsGovFetchProcessor()
            self.usaspending_processor = USASpendingFetchProcessor()
            self.va_state_processor = VirginiaStateGrantsFetch()
            
            self.logger.info("Phase 2 processors initialized successfully")
            
        except ImportError as e:
            self.logger.warning(f"Could not initialize processors, using client fallback: {e}")
        except Exception as e:
            self.logger.error(f"Processor initialization failed: {e}")
    
    async def discover_opportunities(self, 
                                   profile: OrganizationProfile,
                                   max_results: int = 100,
                                   progress_callback: Optional[Callable] = None) -> List[GovernmentOpportunity]:
        """Discover government opportunities using Phase 2 processors when available"""
        
        opportunities = []
        
        # Search federal opportunities via Grants.gov using processor or client
        if progress_callback:
            progress_callback("Searching federal grant opportunities...")
        
        try:
            # Extract search terms from profile
            keywords = self._extract_keywords_from_profile(profile)
            search_keyword = ' '.join(keywords[:3]) if keywords else None
            
            # Use processor if available, otherwise fallback to client
            if self.grants_gov_processor:
                grants_gov_results = await self._search_grants_gov_with_processor(
                    profile, keywords, max_results // 2
                )
            else:
                grants_gov_results = await self.grants_gov_client.search_opportunities(
                    keyword=search_keyword,
                    eligibility_code="25",  # Nonprofits
                    max_results=max_results // 2
                )
            
            # Convert to GovernmentOpportunity objects
            for result in grants_gov_results:
                opportunity = self._convert_grants_gov_result(result)
                if opportunity:
                    opportunity.relevance_score = self.calculate_relevance_score(opportunity, profile)
                    opportunities.append(opportunity)
                    
        except Exception as e:
            self.logger.error(f"Failed to search Grants.gov: {e}")
        
        # Search state opportunities (Virginia)
        if progress_callback:
            progress_callback("Searching Virginia state opportunities...")
            
        try:
            focus_areas = keywords[:5] if keywords else None
            
            # Use processor if available, otherwise fallback to client
            if self.va_state_processor:
                va_results = await self._search_va_state_with_processor(
                    profile, focus_areas, max_results // 2
                )
            else:
                va_results = await self.va_state_client.search_opportunities(
                    focus_areas=focus_areas,
                    eligibility_type="nonprofits",
                    max_results=max_results // 2
                )
            
            # Convert to GovernmentOpportunity objects  
            for result in va_results:
                opportunity = self._convert_va_state_result(result)
                if opportunity:
                    opportunity.relevance_score = self.calculate_relevance_score(opportunity, profile)
                    opportunities.append(opportunity)
                    
        except Exception as e:
            self.logger.error(f"Failed to search VA state opportunities: {e}")
        
        # Sort by relevance and return top results
        opportunities.sort(key=lambda x: x.relevance_score, reverse=True)
        return opportunities[:max_results]
    
    def calculate_relevance_score(self, 
                                opportunity: GovernmentOpportunity, 
                                profile: OrganizationProfile) -> float:
        """Calculate relevance score for government opportunity"""
        
        score = 0.0
        
        # Base score for government opportunities
        score += 20.0
        
        # NTEE code alignment
        if profile.ntee_code:
            profile_ntee_major = profile.ntee_code[0] if profile.ntee_code else ''
            
            # Map NTEE codes to government focus areas
            if profile_ntee_major in ['P', 'Q']:  # Health
                if any(word in opportunity.title.lower() for word in ['health', 'medical', 'wellness']):
                    score += 25.0
            elif profile_ntee_major in ['B', 'E']:  # Education
                if any(word in opportunity.title.lower() for word in ['education', 'school', 'student']):
                    score += 25.0
            elif profile_ntee_major in ['C', 'D']:  # Environment
                if any(word in opportunity.title.lower() for word in ['environment', 'conservation', 'green']):
                    score += 25.0
        
        # Geographic alignment
        if profile.state and hasattr(opportunity, 'eligible_states'):
            if not opportunity.eligible_states or profile.state in opportunity.eligible_states:
                score += 15.0
        
        # Funding amount appropriateness
        if hasattr(opportunity, 'funding_amount_max') and opportunity.funding_amount_max:
            if profile.revenue:
                # Prefer opportunities where max funding is 10-50% of org revenue
                funding_ratio = opportunity.funding_amount_max / profile.revenue
                if 0.1 <= funding_ratio <= 0.5:
                    score += 15.0
                elif 0.05 <= funding_ratio <= 0.8:
                    score += 10.0
        
        # Deadline urgency (prefer deadlines 30-120 days out)
        days_until_deadline = opportunity.calculate_days_until_deadline()
        if days_until_deadline:
            if 30 <= days_until_deadline <= 120:
                score += 10.0
            elif 15 <= days_until_deadline <= 180:
                score += 5.0
        
        return min(100.0, score)
    
    def _convert_grants_gov_result(self, result: Dict[str, Any]) -> Optional[GovernmentOpportunity]:
        """Convert Grants.gov API result to GovernmentOpportunity"""
        try:
            return GovernmentOpportunity(
                id=result.get('opportunityId', ''),
                title=result.get('opportunityTitle', ''),
                description=result.get('description', ''),
                funder_name=result.get('agencyName', ''),
                agency_code=result.get('agencyCode', ''),
                grants_gov_id=result.get('opportunityId'),
                funding_amount_max=result.get('awardCeiling'),
                funding_amount_min=result.get('awardFloor'),
                total_available=result.get('estimatedTotalProgramFunding'),
                application_deadline=self._parse_date(result.get('closeDate')),
                posted_date=self._parse_date(result.get('postDate')),
                source_url=result.get('grantsGovUrl', ''),
                contact_info={
                    'email': result.get('contactEmail', ''),
                    'phone': result.get('contactPhone', ''),
                    'name': result.get('contactName', '')
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to convert Grants.gov result: {e}")
            return None
    
    def _convert_va_state_result(self, result: Dict[str, Any]) -> Optional[GovernmentOpportunity]:
        """Convert Virginia state result to GovernmentOpportunity"""
        try:
            return GovernmentOpportunity(
                id=result.get('id', ''),
                title=result.get('title', ''),
                description=result.get('description', ''),
                funder_name=result.get('agency_name', ''),
                agency_code=result.get('agency_code', ''),
                source_type=FundingSourceType.GOVERNMENT_STATE,
                funding_amount_max=result.get('funding_range', {}).get('max'),
                funding_amount_min=result.get('funding_range', {}).get('min'),
                application_deadline=self._parse_date(result.get('deadline')),
                source_url=result.get('application_url', ''),
                focus_areas=result.get('focus_areas', []),
                contact_info={'email': result.get('contact_email', '')}
            )
        except Exception as e:
            self.logger.error(f"Failed to convert VA state result: {e}")
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None
        try:
            # Handle various date formats
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(date_str)
        except:
            return None
    
    async def _search_grants_gov_with_processor(self, profile: OrganizationProfile, keywords: List[str], max_results: int) -> List[Dict[str, Any]]:
        """Search Grants.gov using Phase 2 processor"""
        try:
            # Create proper config for processor
            from ..core.data_models import ProcessorConfig, WorkflowConfig
            import uuid
            
            # Create workflow config
            workflow_config = WorkflowConfig(
                workflow_id=f"discovery_{uuid.uuid4().hex[:8]}",
                name="Discovery Bridge Grants.gov Search",
                description="Grants.gov search via unified discovery bridge"
            )
            
            # Create complete config for processor execution
            config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="grants_gov_fetch",
                workflow_config=workflow_config,
                processor_specific_config={
                    "keywords": keywords[:3],
                    "eligibility_codes": ["25"],  # Nonprofits
                    "max_opportunities": max_results,
                    "organization_profile": {
                        "name": profile.name,
                        "state": getattr(profile, 'state', None),
                        "ntee_code": getattr(profile, 'ntee_code', None)
                    }
                }
            )
            
            # Execute processor
            result = await self.grants_gov_processor.execute(config)
            
            if result.success and result.data:
                opportunities = result.data.get("opportunities", [])
                self.logger.info(f"Grants.gov processor returned {len(opportunities)} opportunities")
                return opportunities
            else:
                self.logger.warning("Grants.gov processor failed, using client fallback")
                return []
                
        except Exception as e:
            self.logger.error(f"Grants.gov processor error: {e}")
            return []
    
    async def _search_va_state_with_processor(self, profile: OrganizationProfile, focus_areas: List[str], max_results: int) -> List[Dict[str, Any]]:
        """Search VA state opportunities using Phase 2 processor"""
        try:
            # Create proper config for processor
            from ..core.data_models import ProcessorConfig, WorkflowConfig
            import uuid
            
            # Create workflow config
            workflow_config = WorkflowConfig(
                workflow_id=f"discovery_{uuid.uuid4().hex[:8]}",
                name="Discovery Bridge VA State Search",
                description="Virginia state grants search via unified discovery bridge"
            )
            
            config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="va_state_grants_fetch",
                workflow_config=workflow_config,
                processor_specific_config={
                    "focus_areas": focus_areas or [],
                    "geographic_scope": [getattr(profile, 'state', 'VA')],
                    "max_results": max_results,
                    "organization_profile": {
                        "name": profile.name,
                        "state": getattr(profile, 'state', None),
                        "ntee_code": getattr(profile, 'ntee_code', None)
                    }
                }
            )
            
            # Execute processor
            result = await self.va_state_processor.execute(config)
            
            if result.success and result.data:
                opportunities = result.data.get("opportunities", [])
                self.logger.info(f"VA State processor returned {len(opportunities)} opportunities")
                return opportunities
            else:
                self.logger.warning("VA State processor failed, using client fallback")
                return []
                
        except Exception as e:
            self.logger.error(f"VA State processor error: {e}")
            return []


class FoundationDiscoveryStrategy(DiscoveryStrategy):
    """Strategy for discovering foundation opportunities"""
    
    def __init__(self):
        super().__init__("foundation", FundingSourceType.FOUNDATION_PRIVATE)
        # Phase 2 Integration: Use migrated processor
        self.foundation_processor = None
        
        # Legacy client fallback
        self.foundation_client = FoundationDirectoryClient()
        
        # Initialize processor
        self._initialize_processor()
    
    def _initialize_processor(self):
        """Initialize Phase 2 foundation directory processor"""
        try:
            from ..processors.data_collection.foundation_directory_fetch import FoundationDirectoryFetch
            self.foundation_processor = FoundationDirectoryFetch()
            self.logger.info("Foundation Directory processor initialized successfully")
        except ImportError as e:
            self.logger.warning(f"Could not initialize foundation processor, using client fallback: {e}")
        except Exception as e:
            self.logger.error(f"Foundation processor initialization failed: {e}")
    
    async def discover_opportunities(self, 
                                   profile: OrganizationProfile,
                                   max_results: int = 100,
                                   progress_callback: Optional[Callable] = None) -> List[FoundationOpportunity]:
        """Discover foundation opportunities"""
        
        opportunities = []
        
        if progress_callback:
            progress_callback("Searching foundation opportunities...")
        
        try:
            # Extract focus areas from profile
            keywords = self._extract_keywords_from_profile(profile)
            
            # Use processor if available, otherwise fallback to client
            if self.foundation_processor:
                corporate_results = await self._search_foundations_with_processor(
                    profile, keywords, max_results // 2
                )
            else:
                corporate_results = await self.foundation_client.search_corporate_foundations(
                    giving_areas=keywords[:5] if keywords else None,
                    geographic_focus=getattr(profile, 'state', None),
                    max_results=max_results // 2
                )
            
            # Convert to FoundationOpportunity objects
            for result in corporate_results:
                opportunity = self._convert_foundation_result(result, 'corporate')
                if opportunity:
                    opportunity.relevance_score = self.calculate_relevance_score(opportunity, profile)
                    opportunities.append(opportunity)
            
            # Search private foundations (would be similar implementation)
            # private_results = await self.foundation_client.search_private_foundations(...)
            
        except Exception as e:
            self.logger.error(f"Failed to search foundations: {e}")
        
        # Sort by relevance and return top results
        opportunities.sort(key=lambda x: x.relevance_score, reverse=True)
        return opportunities[:max_results]
    
    def calculate_relevance_score(self, 
                                opportunity: FoundationOpportunity, 
                                profile: OrganizationProfile) -> float:
        """Calculate relevance score for foundation opportunity"""
        
        score = 0.0
        
        # Base score for foundation opportunities
        score += 15.0
        
        # Add foundation-specific scoring logic here
        # This would include focus area matching, geographic alignment, etc.
        
        return min(100.0, score)
    
    def _convert_foundation_result(self, result: Dict[str, Any], foundation_type: str) -> Optional[FoundationOpportunity]:
        """Convert foundation API result to FoundationOpportunity"""
        try:
            return FoundationOpportunity(
                id=result.get('id', ''),
                title=f"{result.get('name', '')} Grants",
                description=result.get('description', ''),
                funder_name=result.get('name', ''),
                foundation_type=foundation_type,
                # Add more field mappings based on API structure
            )
        except Exception as e:
            self.logger.error(f"Failed to convert foundation result: {e}")
            return None
    
    async def _search_foundations_with_processor(self, profile: OrganizationProfile, keywords: List[str], max_results: int) -> List[Dict[str, Any]]:
        """Search foundations using Phase 2 processor"""
        try:
            from ..core.data_models import ProcessorConfig, WorkflowConfig
            import uuid
            
            # Create workflow config
            workflow_config = WorkflowConfig(
                workflow_id=f"discovery_{uuid.uuid4().hex[:8]}",
                name="Discovery Bridge Foundation Search",
                description="Foundation Directory search via unified discovery bridge"
            )
            
            config = ProcessorConfig(
                workflow_id=workflow_config.workflow_id,
                processor_name="foundation_directory_fetch",
                workflow_config=workflow_config,
                processor_specific_config={
                    "focus_areas": keywords[:5] if keywords else [],
                    "geographic_scope": [getattr(profile, 'state', None)] if getattr(profile, 'state', None) else [],
                    "funding_range": {"min_amount": 10000, "max_amount": 500000},  # Default range
                    "max_results": max_results,
                    "organization_profile": {
                        "name": profile.name,
                        "state": getattr(profile, 'state', None),
                        "ntee_code": getattr(profile, 'ntee_code', None)
                    }
                }
            )
            
            # Execute processor
            result = await self.foundation_processor.execute(config)
            
            if result and isinstance(result, dict) and result.get("status") == "completed":
                opportunities = result.get("foundation_opportunities", [])
                self.logger.info(f"Foundation processor returned {len(opportunities)} opportunities")
                return opportunities
            else:
                self.logger.warning("Foundation processor failed, using client fallback")
                return []
                
        except Exception as e:
            self.logger.error(f"Foundation processor error: {e}")
            return []


class CorporateDiscoveryStrategy(DiscoveryStrategy):
    """Strategy for discovering corporate CSR and sponsorship opportunities"""
    
    def __init__(self):
        super().__init__("corporate", FundingSourceType.CORPORATE_CSR)
    
    async def discover_opportunities(self, 
                                   profile: OrganizationProfile,
                                   max_results: int = 100,
                                   progress_callback: Optional[Callable] = None) -> List[CorporateOpportunity]:
        """Discover corporate opportunities"""
        
        opportunities = []
        
        if progress_callback:
            progress_callback("Searching corporate CSR opportunities...")
        
        # Implementation would search corporate databases
        # For now, return empty list as placeholder
        
        return opportunities
    
    def calculate_relevance_score(self, 
                                opportunity: CorporateOpportunity, 
                                profile: OrganizationProfile) -> float:
        """Calculate relevance score for corporate opportunity"""
        return 0.0


class UnifiedDiscoveryEngine:
    """
    Unified discovery engine using strategy pattern
    
    Manages multiple discovery strategies and orchestrates
    parallel discovery across all funding sources.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.strategies: Dict[str, DiscoveryStrategy] = {
            'government': GovernmentDiscoveryStrategy(),
            'foundation': FoundationDiscoveryStrategy(),
            'corporate': CorporateDiscoveryStrategy()
        }
    
    async def discover_all_opportunities(self,
                                       profile: OrganizationProfile,
                                       max_results_per_source: int = 50,
                                       progress_callback: Optional[Callable] = None) -> OpportunityCollection:
        """
        Discover opportunities across all sources using parallel execution
        
        Args:
            profile: Organization profile to match against
            max_results_per_source: Maximum results per source type
            progress_callback: Optional callback for progress updates
            
        Returns:
            OpportunityCollection with discovered opportunities
        """
        
        collection = OpportunityCollection(
            collection_id=f"discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=f"Opportunities for {profile.name}",
            profile_used=profile.ein if hasattr(profile, 'ein') else None
        )
        
        # Execute all strategies in parallel
        discovery_tasks = []
        for strategy_name, strategy in self.strategies.items():
            
            def create_progress_callback(strategy_name):
                def callback(message):
                    if progress_callback:
                        progress_callback(f"{strategy_name.title()}: {message}")
                return callback
            
            task = strategy.discover_opportunities(
                profile=profile,
                max_results=max_results_per_source,
                progress_callback=create_progress_callback(strategy_name)
            )
            discovery_tasks.append((strategy_name, task))
        
        # Wait for all discoveries to complete
        results = await asyncio.gather(
            *[task for _, task in discovery_tasks],
            return_exceptions=True
        )
        
        # Process results and add to collection
        for i, (strategy_name, result) in enumerate(zip([name for name, _ in discovery_tasks], results)):
            if isinstance(result, Exception):
                self.logger.error(f"Discovery failed for {strategy_name}: {result}")
                continue
                
            if isinstance(result, list):
                for opportunity in result:
                    collection.add_opportunity(opportunity)
                    
                self.logger.info(f"Discovered {len(result)} opportunities from {strategy_name}")
        
        return collection
    
    async def get_engine_status(self) -> Dict[str, Any]:
        """Get status of all discovery strategies"""
        strategy_status = {}
        
        for name, strategy in self.strategies.items():
            try:
                status = await strategy.get_strategy_status()
                strategy_status[name] = status
            except Exception as e:
                strategy_status[name] = {
                    'name': name,
                    'status': 'error',
                    'error': str(e)
                }
        
        return {
            'engine_status': 'active',
            'strategies': strategy_status,
            'total_strategies': len(self.strategies)
        }


# Global unified discovery engine instance
_discovery_engine: Optional[UnifiedDiscoveryEngine] = None


def get_discovery_engine() -> UnifiedDiscoveryEngine:
    """Get global discovery engine instance"""
    global _discovery_engine
    if _discovery_engine is None:
        _discovery_engine = UnifiedDiscoveryEngine()
    return _discovery_engine