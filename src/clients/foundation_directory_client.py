"""
Foundation Directory Online API Client
Client for corporate foundation and CSR program discovery.
"""
from typing import Dict, Any, List, Optional

from .base_client import PaginatedAPIClient
from ..core.http_client import HTTPConfig


class FoundationDirectoryClient(PaginatedAPIClient):
    """
    Client for Foundation Directory Online API
    
    Handles:
    - Corporate foundation discovery
    - CSR program analysis
    - Giving pattern analysis
    - Partnership opportunity identification
    """
    
    def __init__(self):
        http_config = HTTPConfig(
            timeout=45,
            max_retries=3,
            user_agent="Catalynx/2.0 Grant Research Platform"
        )
        
        super().__init__(
            api_name="foundation_directory",
            base_url="https://api.foundationcenter.org/v2",
            http_config=http_config,
            requires_api_key=True
        )
        
        self.rate_limit_config = {
            'calls_per_hour': 500,
            'delay_between_calls': 0.2
        }
    
    def _configure_rate_limits(self):
        """Configure Foundation Directory specific rate limits"""
        self.http_client.set_api_rate_limit(
            self.api_name,
            calls_per_hour=500,
            delay_between_calls=0.2
        )
    
    def _format_auth_headers(self, api_key: str) -> Dict[str, str]:
        """Format Foundation Directory API key"""
        return {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Foundation Directory API"""
        try:
            response = await self._get("foundations", params={'limit': 1})
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
    
    async def search_corporate_foundations(self,
                                         industry: Optional[str] = None,
                                         company_size: Optional[str] = None,
                                         giving_areas: Optional[List[str]] = None,
                                         geographic_focus: Optional[str] = None,
                                         min_assets: Optional[int] = None,
                                         max_results: int = 1000) -> List[Dict[str, Any]]:
        """
        Search for corporate foundations
        
        Args:
            industry: Industry/sector filter
            company_size: Company size category
            giving_areas: Areas of giving interest
            geographic_focus: Geographic focus area
            min_assets: Minimum foundation assets
            max_results: Maximum results to return
            
        Returns:
            List of corporate foundation data
        """
        params = {
            'foundation_type': 'corporate',
            'status': 'active',
            'limit': min(max_results, 100)
        }
        
        if industry:
            params['industry'] = industry
        if company_size:
            params['company_size'] = company_size
        if giving_areas:
            params['giving_areas'] = ','.join(giving_areas)
        if geographic_focus:
            params['geographic_focus'] = geographic_focus
        if min_assets:
            params['min_assets'] = min_assets
        
        max_pages = (max_results // 100) + 1
        return await self.get_all_pages(
            endpoint="foundations/search",
            initial_params=params,
            max_pages=max_pages
        )
    
    async def get_foundation_details(self, foundation_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific foundation
        
        Args:
            foundation_id: Foundation Directory ID
            
        Returns:
            Detailed foundation information
        """
        return await self._get(f"foundations/{foundation_id}")
    
    async def get_foundation_grants(self, 
                                  foundation_id: str,
                                  year: Optional[int] = None,
                                  limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get grants made by a specific foundation
        
        Args:
            foundation_id: Foundation Directory ID
            year: Specific year filter
            limit: Maximum grants to return
            
        Returns:
            List of grants made by foundation
        """
        params = {'limit': limit}
        if year:
            params['year'] = year
        
        response = await self._get(f"foundations/{foundation_id}/grants", params=params)
        return response.get('grants', [])
    
    async def search_csr_programs(self,
                                industry: Optional[str] = None,
                                program_type: Optional[str] = None,
                                focus_areas: Optional[List[str]] = None,
                                max_results: int = 500) -> List[Dict[str, Any]]:
        """
        Search for corporate social responsibility programs
        
        Args:
            industry: Industry filter
            program_type: Type of CSR program
            focus_areas: Program focus areas
            max_results: Maximum results
            
        Returns:
            List of CSR program data
        """
        params = {
            'program_type': 'csr',
            'status': 'active',
            'limit': min(max_results, 100)
        }
        
        if industry:
            params['industry'] = industry
        if program_type:
            params['csr_type'] = program_type
        if focus_areas:
            params['focus_areas'] = ','.join(focus_areas)
        
        max_pages = (max_results // 100) + 1
        return await self.get_all_pages(
            endpoint="csr/search",
            initial_params=params,
            max_pages=max_pages
        )
    
    def _extract_pagination_info(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pagination info from Foundation Directory response"""
        if not isinstance(response, dict):
            return {}
        
        pagination = response.get('pagination', {})
        return {
            'total_count': pagination.get('total_count', 0),
            'current_page': pagination.get('current_page', 1),
            'per_page': pagination.get('per_page', 100),
            'total_pages': pagination.get('total_pages', 1)
        }
    
    def _build_next_page_params(self,
                               current_params: Dict[str, Any],
                               pagination_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build parameters for next page"""
        current_page = pagination_info.get('current_page', 1)
        total_pages = pagination_info.get('total_pages', 1)
        
        if current_page >= total_pages:
            return None
        
        next_params = current_params.copy()
        next_params['page'] = current_page + 1
        return next_params
    
    def _extract_page_data(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract foundation/CSR data from response"""
        if not isinstance(response, dict):
            return []
        
        # Could be 'foundations', 'csr_programs', or 'data'
        for key in ['foundations', 'csr_programs', 'data', 'results']:
            if key in response and isinstance(response[key], list):
                return response[key]
        
        return []