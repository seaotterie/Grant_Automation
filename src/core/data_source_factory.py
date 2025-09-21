#!/usr/bin/env python3
"""
Data Source Factory Pattern

Creates appropriate data fetchers based on organization type, data availability,
and fetch strategy preferences. Implements factory pattern for different
fetch strategies: ProPublica vs BMF vs web scraping.
"""

from enum import Enum
from typing import Optional, Dict, Any, List, Type, Protocol
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class FetchStrategy(Enum):
    """Available fetch strategies"""
    TAX_DATA_FIRST = "tax_data_first"      # 990 forms first, then web scraping
    WEB_SCRAPING_FIRST = "web_first"       # Web scraping first, then tax data
    BMF_COMPREHENSIVE = "bmf_comprehensive" # BMF database comprehensive search
    PROPUBLICA_ONLY = "propublica_only"    # ProPublica API only
    HYBRID_INTELLIGENCE = "hybrid"         # All sources with conflict resolution
    CACHE_OPTIMIZED = "cache_optimized"    # Cache-first with minimal API calls


class DataSourceType(Enum):
    """Types of data sources"""
    PROPUBLICA_990 = "propublica_990"
    BMF_DATABASE = "bmf_database"
    WEB_SCRAPING = "web_scraping"
    TAX_FILING_DIRECT = "tax_filing_direct"
    ENHANCED_990 = "enhanced_990"
    USER_PROVIDED = "user_provided"


class FetchResult:
    """Standardized result from any fetch operation"""

    def __init__(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[DataSourceType] = None,
        confidence: float = 0.0,
        error_message: Optional[str] = None,
        processing_time: float = 0.0,
        cost: float = 0.0
    ):
        self.success = success
        self.data = data or {}
        self.source = source
        self.confidence = confidence
        self.error_message = error_message
        self.processing_time = processing_time
        self.cost = cost
        self.timestamp = None


class DataFetcher(Protocol):
    """Protocol for all data fetchers"""

    async def fetch_organization_data(
        self,
        ein: Optional[str] = None,
        organization_name: Optional[str] = None,
        **kwargs
    ) -> FetchResult:
        """Fetch organization data"""
        ...

    def get_source_type(self) -> DataSourceType:
        """Get the data source type this fetcher provides"""
        ...

    def get_confidence_score(self) -> float:
        """Get base confidence score for this source"""
        ...


class ProPublicaFetcher:
    """ProPublica 990 data fetcher"""

    def __init__(self):
        from src.clients.propublica_client import ProPublicaClient
        self.client = ProPublicaClient()

    async def fetch_organization_data(
        self,
        ein: Optional[str] = None,
        organization_name: Optional[str] = None,
        **kwargs
    ) -> FetchResult:
        """Fetch from ProPublica API"""
        try:
            if not ein:
                return FetchResult(
                    success=False,
                    error_message="EIN required for ProPublica fetch",
                    source=DataSourceType.PROPUBLICA_990
                )

            # Use existing ProPublica client
            org_data = await self.client.get_organization(ein)

            if org_data:
                return FetchResult(
                    success=True,
                    data=org_data,
                    source=DataSourceType.PROPUBLICA_990,
                    confidence=0.80,  # High confidence for official 990 data
                    cost=0.001  # Estimated API cost
                )
            else:
                return FetchResult(
                    success=False,
                    error_message="Organization not found in ProPublica",
                    source=DataSourceType.PROPUBLICA_990
                )

        except Exception as e:
            return FetchResult(
                success=False,
                error_message=f"ProPublica fetch error: {str(e)}",
                source=DataSourceType.PROPUBLICA_990
            )

    def get_source_type(self) -> DataSourceType:
        return DataSourceType.PROPUBLICA_990

    def get_confidence_score(self) -> float:
        return 0.80


class BMFFetcher:
    """BMF (Business Master File) database fetcher"""

    def __init__(self):
        # Import BMF processor when needed
        self.bmf_processor = None

    async def fetch_organization_data(
        self,
        ein: Optional[str] = None,
        organization_name: Optional[str] = None,
        **kwargs
    ) -> FetchResult:
        """Fetch from BMF database"""
        try:
            if not self.bmf_processor:
                from src.processors.filtering.enhanced_bmf_filter import EnhancedBMFFilter
                self.bmf_processor = EnhancedBMFFilter()

            # Use EIN or name for BMF lookup
            if ein:
                bmf_data = await self._fetch_by_ein(ein)
            elif organization_name:
                bmf_data = await self._fetch_by_name(organization_name)
            else:
                return FetchResult(
                    success=False,
                    error_message="EIN or organization name required for BMF fetch",
                    source=DataSourceType.BMF_DATABASE
                )

            if bmf_data:
                return FetchResult(
                    success=True,
                    data=bmf_data,
                    source=DataSourceType.BMF_DATABASE,
                    confidence=0.85,  # Very high confidence for IRS data
                    cost=0.0  # Local database, no API cost
                )
            else:
                return FetchResult(
                    success=False,
                    error_message="Organization not found in BMF database",
                    source=DataSourceType.BMF_DATABASE
                )

        except Exception as e:
            return FetchResult(
                success=False,
                error_message=f"BMF fetch error: {str(e)}",
                source=DataSourceType.BMF_DATABASE
            )

    async def _fetch_by_ein(self, ein: str) -> Optional[Dict[str, Any]]:
        """Fetch BMF data by EIN"""
        # Implementation would use the existing BMF filter
        # This is a placeholder for the actual BMF lookup
        return None

    async def _fetch_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Fetch BMF data by organization name"""
        # Implementation would use the existing BMF filter
        # This is a placeholder for the actual BMF lookup
        return None

    def get_source_type(self) -> DataSourceType:
        return DataSourceType.BMF_DATABASE

    def get_confidence_score(self) -> float:
        return 0.85


class WebScrapingFetcher:
    """Web scraping data fetcher"""

    def __init__(self):
        from src.core.verification_enhanced_scraper import VerificationEnhancedScraper
        self.scraper = VerificationEnhancedScraper()

    async def fetch_organization_data(
        self,
        ein: Optional[str] = None,
        organization_name: Optional[str] = None,
        website_url: Optional[str] = None,
        **kwargs
    ) -> FetchResult:
        """Fetch via web scraping"""
        try:
            if not website_url:
                return FetchResult(
                    success=False,
                    error_message="Website URL required for web scraping",
                    source=DataSourceType.WEB_SCRAPING
                )

            # Use existing verification scraper
            scraping_result = await self.scraper.scrape_organization_website(
                website_url, organization_name or "Unknown"
            )

            if scraping_result and scraping_result.success:
                return FetchResult(
                    success=True,
                    data=scraping_result.to_dict(),
                    source=DataSourceType.WEB_SCRAPING,
                    confidence=0.70,  # Medium confidence for web data
                    cost=0.005  # Estimated scraping cost
                )
            else:
                return FetchResult(
                    success=False,
                    error_message="Web scraping failed",
                    source=DataSourceType.WEB_SCRAPING
                )

        except Exception as e:
            return FetchResult(
                success=False,
                error_message=f"Web scraping error: {str(e)}",
                source=DataSourceType.WEB_SCRAPING
            )

    def get_source_type(self) -> DataSourceType:
        return DataSourceType.WEB_SCRAPING

    def get_confidence_score(self) -> float:
        return 0.70


class DataSourceFactory:
    """Factory for creating appropriate data fetchers based on strategy"""

    def __init__(self):
        self.fetchers: Dict[DataSourceType, Type[DataFetcher]] = {
            DataSourceType.PROPUBLICA_990: ProPublicaFetcher,
            DataSourceType.BMF_DATABASE: BMFFetcher,
            DataSourceType.WEB_SCRAPING: WebScrapingFetcher
        }

        # Cache fetcher instances
        self._fetcher_instances: Dict[DataSourceType, DataFetcher] = {}

    def get_fetcher(self, source_type: DataSourceType) -> DataFetcher:
        """Get a fetcher instance for the specified source type"""
        if source_type not in self._fetcher_instances:
            fetcher_class = self.fetchers.get(source_type)
            if not fetcher_class:
                raise ValueError(f"No fetcher available for source type: {source_type}")
            self._fetcher_instances[source_type] = fetcher_class()

        return self._fetcher_instances[source_type]

    def get_strategy_fetchers(self, strategy: FetchStrategy) -> List[DataSourceType]:
        """Get the list of fetchers for a given strategy in priority order"""
        strategy_mappings = {
            FetchStrategy.TAX_DATA_FIRST: [
                DataSourceType.BMF_DATABASE,
                DataSourceType.PROPUBLICA_990,
                DataSourceType.WEB_SCRAPING
            ],
            FetchStrategy.WEB_SCRAPING_FIRST: [
                DataSourceType.WEB_SCRAPING,
                DataSourceType.BMF_DATABASE,
                DataSourceType.PROPUBLICA_990
            ],
            FetchStrategy.BMF_COMPREHENSIVE: [
                DataSourceType.BMF_DATABASE
            ],
            FetchStrategy.PROPUBLICA_ONLY: [
                DataSourceType.PROPUBLICA_990
            ],
            FetchStrategy.HYBRID_INTELLIGENCE: [
                DataSourceType.BMF_DATABASE,
                DataSourceType.PROPUBLICA_990,
                DataSourceType.WEB_SCRAPING
            ],
            FetchStrategy.CACHE_OPTIMIZED: [
                DataSourceType.BMF_DATABASE,  # Local, no API cost
                DataSourceType.PROPUBLICA_990,
                DataSourceType.WEB_SCRAPING
            ]
        }

        return strategy_mappings.get(strategy, [DataSourceType.BMF_DATABASE])

    def create_fetch_plan(
        self,
        strategy: FetchStrategy,
        organization_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an execution plan for fetching data with the given strategy"""
        fetcher_types = self.get_strategy_fetchers(strategy)

        plan = {
            'strategy': strategy.value,
            'fetchers': [],
            'estimated_cost': 0.0,
            'estimated_time': 0.0,
            'expected_confidence': 0.0
        }

        for source_type in fetcher_types:
            fetcher = self.get_fetcher(source_type)

            fetcher_info = {
                'source_type': source_type.value,
                'confidence': fetcher.get_confidence_score(),
                'estimated_cost': self._estimate_cost(source_type),
                'estimated_time': self._estimate_time(source_type)
            }

            plan['fetchers'].append(fetcher_info)
            plan['estimated_cost'] += fetcher_info['estimated_cost']
            plan['estimated_time'] += fetcher_info['estimated_time']

        # Calculate expected confidence (weighted average)
        if plan['fetchers']:
            total_weight = sum(f['confidence'] for f in plan['fetchers'])
            plan['expected_confidence'] = total_weight / len(plan['fetchers'])

        return plan

    def _estimate_cost(self, source_type: DataSourceType) -> float:
        """Estimate cost for a fetch operation"""
        cost_estimates = {
            DataSourceType.BMF_DATABASE: 0.0,      # Local database
            DataSourceType.PROPUBLICA_990: 0.001,  # API call
            DataSourceType.WEB_SCRAPING: 0.005,    # Scraping + processing
        }
        return cost_estimates.get(source_type, 0.001)

    def _estimate_time(self, source_type: DataSourceType) -> float:
        """Estimate time for a fetch operation in seconds"""
        time_estimates = {
            DataSourceType.BMF_DATABASE: 0.1,      # Fast local lookup
            DataSourceType.PROPUBLICA_990: 2.0,    # API call + processing
            DataSourceType.WEB_SCRAPING: 10.0,     # Web scraping + parsing
        }
        return time_estimates.get(source_type, 1.0)


# Global factory instance
_factory_instance = None

def get_data_source_factory() -> DataSourceFactory:
    """Get singleton data source factory"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = DataSourceFactory()
    return _factory_instance


class FetchOrchestrator:
    """Orchestrates data fetching using multiple strategies and sources"""

    def __init__(self):
        self.factory = get_data_source_factory()
        from src.core.data_source_priority import get_data_priority_resolver
        self.priority_resolver = get_data_priority_resolver()

    async def fetch_with_strategy(
        self,
        strategy: FetchStrategy,
        ein: Optional[str] = None,
        organization_name: Optional[str] = None,
        website_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch organization data using the specified strategy.

        Returns consolidated result with data from multiple sources.
        """
        fetcher_types = self.factory.get_strategy_fetchers(strategy)
        results = []
        total_cost = 0.0
        total_time = 0.0

        for source_type in fetcher_types:
            try:
                fetcher = self.factory.get_fetcher(source_type)

                # Fetch data from this source
                result = await fetcher.fetch_organization_data(
                    ein=ein,
                    organization_name=organization_name,
                    website_url=website_url,
                    **kwargs
                )

                results.append(result)
                total_cost += result.cost
                total_time += result.processing_time

                # For some strategies, stop after first successful result
                if strategy in [FetchStrategy.BMF_COMPREHENSIVE, FetchStrategy.PROPUBLICA_ONLY]:
                    if result.success:
                        break

            except Exception as e:
                logger.error(f"Error fetching from {source_type}: {e}")
                continue

        # Consolidate results using priority resolver
        consolidated_data = self._consolidate_results(results)

        return {
            'success': any(r.success for r in results),
            'data': consolidated_data,
            'sources_used': [r.source.value for r in results if r.success],
            'total_cost': total_cost,
            'total_time': total_time,
            'strategy_used': strategy.value,
            'results_count': len([r for r in results if r.success])
        }

    def _consolidate_results(self, results: List[FetchResult]) -> Dict[str, Any]:
        """Consolidate data from multiple fetch results"""
        if not results:
            return {}

        successful_results = [r for r in results if r.success]
        if not successful_results:
            return {}

        # For now, return the highest confidence result
        # In future, could use priority resolver for field-level consolidation
        best_result = max(successful_results, key=lambda r: r.confidence)
        return best_result.data

    def get_recommended_strategy(
        self,
        organization_data: Dict[str, Any]
    ) -> FetchStrategy:
        """Recommend the best fetch strategy based on available data"""

        has_ein = bool(organization_data.get('ein'))
        has_website = bool(organization_data.get('website_url'))
        org_type = organization_data.get('organization_type', '').lower()

        # Strategy selection logic
        if has_ein and org_type in ['nonprofit', 'foundation']:
            return FetchStrategy.TAX_DATA_FIRST
        elif has_website and not has_ein:
            return FetchStrategy.WEB_SCRAPING_FIRST
        elif has_ein:
            return FetchStrategy.BMF_COMPREHENSIVE
        else:
            return FetchStrategy.HYBRID_INTELLIGENCE


# Global orchestrator instance
_orchestrator_instance = None

def get_fetch_orchestrator() -> FetchOrchestrator:
    """Get singleton fetch orchestrator"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = FetchOrchestrator()
    return _orchestrator_instance