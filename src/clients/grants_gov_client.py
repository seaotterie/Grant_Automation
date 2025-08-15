"""
Grants.gov API Client
Standardized client for federal grant opportunities from Grants.gov API.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_client import PaginatedAPIClient
from ..core.http_client import HTTPConfig


class GrantsGovClient(PaginatedAPIClient):
    """
    Client for Grants.gov API
    
    Handles:
    - Federal grant opportunity search
    - Eligibility filtering
    - Deadline tracking
    - Opportunity details retrieval
    """
    
    def __init__(self):
        http_config = HTTPConfig(
            timeout=60,  # Grants.gov can be slow
            max_retries=3,
            user_agent="Catalynx/2.0 Grant Research Platform"
        )
        
        super().__init__(
            api_name="grants_gov",
            base_url="https://www.grants.gov/grantsws/rest",
            http_config=http_config,
            requires_api_key=False  # Grants.gov is public API
        )
        
        # Store rate limit config for reference
        self.rate_limit_config = {
            'calls_per_hour': 1000,
            'delay_between_calls': 0.1
        }
    
    def _configure_rate_limits(self):
        """Configure Grants.gov specific rate limits"""
        self.http_client.set_api_rate_limit(
            self.api_name,
            calls_per_hour=1000,
            delay_between_calls=0.1  # Be respectful to public API
        )
    
    def _format_auth_headers(self, api_key: str) -> Dict[str, str]:
        """Grants.gov doesn't require authentication"""
        return {}
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Grants.gov API"""
        try:
            # Try to get opportunity types as a simple test
            response = await self._get("opportunitytypes")
            return {
                'status': 'success',
                'api_name': self.api_name,
                'response_keys': list(response.keys()) if isinstance(response, dict) else []
            }
        except Exception as e:
            return {
                'status': 'error',
                'api_name': self.api_name,
                'error': str(e)
            }
    
    async def search_opportunities(self,
                                 keyword: Optional[str] = None,
                                 opportunity_category: Optional[str] = None,
                                 eligibility_code: str = "25",  # Nonprofits
                                 funding_instrument: Optional[str] = None,
                                 agency_code: Optional[str] = None,
                                 max_results: int = 1000) -> List[Dict[str, Any]]:
        """
        Search for grant opportunities
        
        Args:
            keyword: Search keyword
            opportunity_category: Category filter
            eligibility_code: Eligibility code (25 = Nonprofits)
            funding_instrument: Type of funding (G = Grant, CA = Cooperative Agreement)
            agency_code: Specific agency code
            max_results: Maximum results to return
            
        Returns:
            List of opportunity data
        """
        
        params = {
            'oppStatus': 'forecasted|posted',  # Active opportunities
            'sortBy': 'openDate|desc',
            'rows': min(max_results, 25),  # API limit per page
            'eligibilities.code': eligibility_code
        }
        
        if keyword:
            params['keyword'] = keyword
        if opportunity_category:
            params['oppCategories'] = opportunity_category  
        if funding_instrument:
            params['fundingInstruments'] = funding_instrument
        if agency_code:
            params['agencies'] = agency_code
        
        # Use pagination to get all results
        max_pages = (max_results // 25) + 1
        return await self.get_all_pages(
            endpoint="opportunities/search",
            initial_params=params,
            max_pages=max_pages
        )
    
    async def get_opportunity_details(self, opportunity_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific opportunity
        
        Args:
            opportunity_id: Grants.gov opportunity ID
            
        Returns:
            Detailed opportunity information
        """
        return await self._get(f"opportunity/{opportunity_id}")
    
    async def get_opportunity_synopsis(self, opportunity_id: str) -> Dict[str, Any]:
        """
        Get synopsis for a specific opportunity
        
        Args:
            opportunity_id: Grants.gov opportunity ID
            
        Returns:
            Opportunity synopsis
        """
        return await self._get(f"opportunity/{opportunity_id}/synopsis")
    
    def _extract_pagination_info(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pagination info from Grants.gov response"""
        if not isinstance(response, dict):
            return {}
        
        # Grants.gov uses 'hitCountTotal' and 'startRecordNum'
        return {
            'total_hits': response.get('hitCountTotal', 0),
            'start_record': response.get('startRecordNum', 0),
            'current_page_size': len(response.get('oppHits', []))
        }
    
    def _build_next_page_params(self, 
                               current_params: Dict[str, Any],
                               pagination_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build parameters for next page"""
        total_hits = pagination_info.get('total_hits', 0)
        start_record = pagination_info.get('start_record', 0)
        page_size = current_params.get('rows', 25)
        
        next_start = start_record + page_size
        
        if next_start >= total_hits:
            return None
        
        next_params = current_params.copy()
        next_params['startRecordNum'] = next_start
        return next_params
    
    def _extract_page_data(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract opportunity data from response"""
        if not isinstance(response, dict):
            return []
        
        return response.get('oppHits', [])