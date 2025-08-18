#!/usr/bin/env python3
"""
Enhanced Data Service
Service for fetching 990/990-PF data for high-scoring opportunities to boost their scores

This service provides:
1. Automatic 990 data fetching for opportunities scoring above threshold
2. 990-PF foundation data extraction for private foundations
3. Enhanced scoring boost factors based on available financial data
4. Intelligent caching and prioritization of data requests
5. Integration with existing processors and automated promotion
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from pathlib import Path

from src.processors.data_collection.xml_downloader import XMLDownloaderProcessor
from src.processors.data_collection.pf_data_extractor import PFDataExtractorProcessor
from src.clients.propublica_client import ProPublicaClient
from src.analytics.financial_analytics import FinancialAnalytics
from src.core.data_models import OrganizationProfile

logger = logging.getLogger(__name__)


@dataclass
class EnhancedDataResult:
    """Result of enhanced data fetching for an opportunity"""
    opportunity_id: str
    organization_name: str
    ein: Optional[str]
    has_990_data: bool
    has_990_pf_data: bool
    financial_data: Optional[Dict[str, Any]]
    foundation_data: Optional[Dict[str, Any]]
    board_data: Optional[Dict[str, Any]]
    boost_factors: Dict[str, float]
    data_completeness: float
    fetched_at: datetime
    processing_time: float
    error_message: Optional[str] = None


@dataclass
class EnhancedDataConfig:
    """Configuration for enhanced data fetching"""
    score_threshold: float = 0.65  # Minimum score to trigger 990 fetching
    enable_990_fetching: bool = True
    enable_990_pf_fetching: bool = True
    max_concurrent_requests: int = 5
    request_timeout: int = 30
    cache_duration_hours: int = 24
    priority_score_threshold: float = 0.80  # High priority threshold


class EnhancedDataService:
    """Service for fetching enhanced 990/990-PF data for high-scoring opportunities"""
    
    def __init__(self):
        self.config = EnhancedDataConfig()
        
        # Initialize processors
        self.xml_downloader = XMLDownloaderProcessor()
        self.pf_extractor = PFDataExtractorProcessor()
        self.propublica_client = ProPublicaClient()
        self.financial_analytics = FinancialAnalytics()
        
        # Data cache
        self.data_cache: Dict[str, EnhancedDataResult] = {}
        
        # Processing statistics
        self.stats = {
            'total_requests': 0,
            'successful_fetches': 0,
            'cache_hits': 0,
            'error_count': 0,
            'average_processing_time': 0.0
        }
    
    async def fetch_enhanced_data_for_opportunity(
        self, 
        opportunity: Dict[str, Any], 
        score: Optional[float] = None
    ) -> Optional[EnhancedDataResult]:
        """
        Fetch enhanced 990/990-PF data for a single opportunity
        
        Args:
            opportunity: Opportunity dictionary with organization information
            score: Current opportunity score to determine if fetching is warranted
            
        Returns:
            EnhancedDataResult if data was fetched, None if not warranted
        """
        start_time = datetime.now()
        opportunity_id = opportunity.get('opportunity_id', 'unknown')
        organization_name = opportunity.get('organization_name', 'Unknown')
        ein = opportunity.get('external_data', {}).get('ein') or opportunity.get('ein')
        
        logger.info(f"Fetching enhanced data for {organization_name} (EIN: {ein})")
        
        try:
            # Check if fetching is warranted based on score
            if score and score < self.config.score_threshold:
                logger.debug(f"Score {score:.3f} below threshold {self.config.score_threshold}, skipping enhanced data")
                return None
            
            # Check cache first
            cache_key = f"{ein}_{organization_name}".replace(' ', '_').lower()
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.stats['cache_hits'] += 1
                logger.debug(f"Using cached enhanced data for {organization_name}")
                return cached_result
            
            # Fetch 990 data
            enhanced_result = await self._fetch_organization_data(
                opportunity_id, organization_name, ein, score or 0.0
            )
            
            # Cache the result
            if enhanced_result:
                self.data_cache[cache_key] = enhanced_result
                self.stats['successful_fetches'] += 1
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(processing_time, enhanced_result is not None)
            
            if enhanced_result:
                enhanced_result.processing_time = processing_time
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error fetching enhanced data for {organization_name}: {e}")
            self.stats['error_count'] += 1
            return EnhancedDataResult(
                opportunity_id=opportunity_id,
                organization_name=organization_name,
                ein=ein,
                has_990_data=False,
                has_990_pf_data=False,
                financial_data=None,
                foundation_data=None,
                board_data=None,
                boost_factors={},
                data_completeness=0.0,
                fetched_at=datetime.now(),
                processing_time=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )
    
    async def fetch_enhanced_data_batch(
        self, 
        opportunities: List[Dict[str, Any]], 
        scores: Optional[List[float]] = None
    ) -> List[EnhancedDataResult]:
        """
        Fetch enhanced data for a batch of opportunities with concurrent processing
        
        Args:
            opportunities: List of opportunity dictionaries
            scores: Optional list of scores corresponding to opportunities
            
        Returns:
            List of EnhancedDataResult objects
        """
        logger.info(f"Fetching enhanced data for batch of {len(opportunities)} opportunities")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        # Create tasks for each opportunity
        tasks = []
        for i, opportunity in enumerate(opportunities):
            score = scores[i] if scores and i < len(scores) else None
            task = self._fetch_with_semaphore(semaphore, opportunity, score)
            tasks.append(task)
        
        # Execute tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and None results
        enhanced_results = []
        for result in results:
            if isinstance(result, EnhancedDataResult):
                enhanced_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Exception in batch processing: {result}")
        
        logger.info(f"Enhanced data batch complete: {len(enhanced_results)} successful results")
        return enhanced_results
    
    async def _fetch_with_semaphore(
        self, 
        semaphore: asyncio.Semaphore, 
        opportunity: Dict[str, Any], 
        score: Optional[float]
    ) -> Optional[EnhancedDataResult]:
        """Wrapper to fetch enhanced data with semaphore control"""
        async with semaphore:
            return await self.fetch_enhanced_data_for_opportunity(opportunity, score)
    
    async def _fetch_organization_data(
        self, 
        opportunity_id: str, 
        organization_name: str, 
        ein: Optional[str], 
        score: float
    ) -> Optional[EnhancedDataResult]:
        """Fetch 990/990-PF data for a specific organization"""
        
        if not ein:
            logger.warning(f"No EIN available for {organization_name}, cannot fetch 990 data")
            return None
        
        has_990_data = False
        has_990_pf_data = False
        financial_data = None
        foundation_data = None
        board_data = None
        boost_factors = {}
        
        try:
            # Check if this is a private foundation (990-PF) or regular nonprofit (990)
            is_foundation = await self._is_private_foundation(ein)
            
            if is_foundation and self.config.enable_990_pf_fetching:
                # Fetch 990-PF data for private foundations
                foundation_result = await self._fetch_990_pf_data(ein, organization_name)
                if foundation_result:
                    has_990_pf_data = True
                    foundation_data = foundation_result.get('foundation_data')
                    financial_data = foundation_result.get('financial_data')
                    board_data = foundation_result.get('board_data')
                    boost_factors['foundation_data'] = 0.15
                    boost_factors['has_990_data'] = 0.10
            
            elif self.config.enable_990_fetching:
                # Fetch regular 990 data for nonprofits
                nonprofit_result = await self._fetch_990_data(ein, organization_name)
                if nonprofit_result:
                    has_990_data = True
                    financial_data = nonprofit_result.get('financial_data')
                    board_data = nonprofit_result.get('board_data')
                    boost_factors['has_990_data'] = 0.10
                    
                    # Additional boost for detailed financial data
                    if financial_data and financial_data.get('total_revenue', 0) > 0:
                        boost_factors['detailed_financials'] = 0.05
            
            # Calculate data completeness score
            data_completeness = self._calculate_data_completeness(
                has_990_data, has_990_pf_data, financial_data, board_data
            )
            
            return EnhancedDataResult(
                opportunity_id=opportunity_id,
                organization_name=organization_name,
                ein=ein,
                has_990_data=has_990_data,
                has_990_pf_data=has_990_pf_data,
                financial_data=financial_data,
                foundation_data=foundation_data,
                board_data=board_data,
                boost_factors=boost_factors,
                data_completeness=data_completeness,
                fetched_at=datetime.now(),
                processing_time=0.0  # Will be set by caller
            )
            
        except Exception as e:
            logger.error(f"Error fetching organization data for {organization_name}: {e}")
            return None
    
    async def _is_private_foundation(self, ein: str) -> bool:
        """Check if an organization is a private foundation based on EIN or data"""
        try:
            # Quick check using ProPublica API to get organization type
            org_data = await self.propublica_client.get_organization_by_ein(ein)
            if org_data:
                # Check for foundation indicators
                org_type = org_data.get('organization_type', '').lower()
                if 'foundation' in org_type or 'private foundation' in org_type:
                    return True
                
                # Check NTEE codes that indicate foundations
                ntee_code = org_data.get('ntee_code', '')
                if ntee_code.startswith('T'):  # Philanthropy codes
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Could not determine foundation status for EIN {ein}: {e}")
            return False
    
    async def _fetch_990_data(self, ein: str, organization_name: str) -> Optional[Dict[str, Any]]:
        """Fetch regular 990 data for nonprofit organizations"""
        try:
            # Use ProPublica client to get basic financial data
            org_data = await self.propublica_client.get_organization_by_ein(ein)
            if not org_data:
                return None
            
            # Extract financial data
            financial_data = {
                'total_revenue': org_data.get('total_revenue', 0),
                'total_expenses': org_data.get('total_expenses', 0),
                'total_assets': org_data.get('total_assets', 0),
                'total_liabilities': org_data.get('total_liabilities', 0),
                'net_assets': org_data.get('net_assets', 0),
                'tax_year': org_data.get('tax_year'),
                'organization_type': org_data.get('organization_type'),
                'ntee_code': org_data.get('ntee_code')
            }
            
            # Extract board/officer data if available
            board_data = {
                'officers': org_data.get('officers', []),
                'board_size': len(org_data.get('officers', [])),
                'compensation_data': org_data.get('compensation', {})
            }
            
            logger.info(f"Successfully fetched 990 data for {organization_name}")
            return {
                'financial_data': financial_data,
                'board_data': board_data,
                'source': 'propublica_990'
            }
            
        except Exception as e:
            logger.error(f"Error fetching 990 data for {organization_name}: {e}")
            return None
    
    async def _fetch_990_pf_data(self, ein: str, organization_name: str) -> Optional[Dict[str, Any]]:
        """Fetch 990-PF data for private foundations"""
        try:
            # Use the PF data extractor processor
            # This would need to be adapted to work with individual requests
            # For now, use ProPublica API with foundation-specific parsing
            
            org_data = await self.propublica_client.get_organization_by_ein(ein)
            if not org_data:
                return None
            
            # Extract foundation-specific financial data
            financial_data = {
                'total_assets': org_data.get('total_assets', 0),
                'total_revenue': org_data.get('total_revenue', 0),
                'investment_income': org_data.get('investment_income', 0),
                'grants_paid': org_data.get('grants_paid', 0),
                'operating_expenses': org_data.get('operating_expenses', 0),
                'tax_year': org_data.get('tax_year'),
                'foundation_type': 'private_foundation'
            }
            
            # Foundation-specific data
            foundation_data = {
                'grant_making_capacity': org_data.get('grants_paid', 0),
                'asset_size': org_data.get('total_assets', 0),
                'application_process': org_data.get('application_process', 'Unknown'),
                'focus_areas': org_data.get('focus_areas', []),
                'geographic_scope': org_data.get('geographic_scope', [])
            }
            
            # Board data
            board_data = {
                'trustees': org_data.get('officers', []),
                'board_size': len(org_data.get('officers', [])),
                'key_personnel': org_data.get('key_personnel', [])
            }
            
            logger.info(f"Successfully fetched 990-PF data for {organization_name}")
            return {
                'financial_data': financial_data,
                'foundation_data': foundation_data,
                'board_data': board_data,
                'source': 'propublica_990_pf'
            }
            
        except Exception as e:
            logger.error(f"Error fetching 990-PF data for {organization_name}: {e}")
            return None
    
    def _calculate_data_completeness(
        self, 
        has_990_data: bool, 
        has_990_pf_data: bool, 
        financial_data: Optional[Dict], 
        board_data: Optional[Dict]
    ) -> float:
        """Calculate data completeness score"""
        completeness = 0.0
        
        # Base points for having any 990 data
        if has_990_data or has_990_pf_data:
            completeness += 0.5
        
        # Additional points for financial data
        if financial_data:
            completeness += 0.3
            # Bonus for detailed financial data
            if financial_data.get('total_revenue', 0) > 0:
                completeness += 0.1
        
        # Additional points for board data
        if board_data and board_data.get('board_size', 0) > 0:
            completeness += 0.1
        
        return min(1.0, completeness)
    
    def _get_cached_result(self, cache_key: str) -> Optional[EnhancedDataResult]:
        """Get cached result if still valid"""
        if cache_key in self.data_cache:
            cached_result = self.data_cache[cache_key]
            cache_age = datetime.now() - cached_result.fetched_at
            
            if cache_age < timedelta(hours=self.config.cache_duration_hours):
                return cached_result
            else:
                # Remove expired cache entry
                del self.data_cache[cache_key]
        
        return None
    
    def _update_stats(self, processing_time: float, success: bool):
        """Update service statistics"""
        self.stats['total_requests'] += 1
        
        if success:
            # Update running average of processing time
            current_avg = self.stats['average_processing_time']
            total_requests = self.stats['total_requests']
            self.stats['average_processing_time'] = (
                (current_avg * (total_requests - 1) + processing_time) / total_requests
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        total_requests = self.stats['total_requests']
        success_rate = (self.stats['successful_fetches'] / max(total_requests, 1)) * 100
        cache_hit_rate = (self.stats['cache_hits'] / max(total_requests, 1)) * 100
        
        return {
            **self.stats,
            'success_rate': success_rate,
            'cache_hit_rate': cache_hit_rate,
            'cache_size': len(self.data_cache),
            'config': {
                'score_threshold': self.config.score_threshold,
                'enable_990_fetching': self.config.enable_990_fetching,
                'enable_990_pf_fetching': self.config.enable_990_pf_fetching,
                'cache_duration_hours': self.config.cache_duration_hours
            }
        }
    
    def update_config(self, config_updates: Dict[str, Any]):
        """Update service configuration"""
        for key, value in config_updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated enhanced data config: {key} = {value}")
    
    def clear_cache(self):
        """Clear the data cache"""
        cache_size = len(self.data_cache)
        self.data_cache.clear()
        logger.info(f"Cleared enhanced data cache ({cache_size} entries)")


def get_enhanced_data_service() -> EnhancedDataService:
    """Get singleton instance of enhanced data service"""
    if not hasattr(get_enhanced_data_service, '_instance'):
        get_enhanced_data_service._instance = EnhancedDataService()
    return get_enhanced_data_service._instance