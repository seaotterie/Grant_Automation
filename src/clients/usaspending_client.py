"""
USASpending.gov API Client
Client for federal spending and award data analysis.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_client import PaginatedAPIClient
from ..core.http_client import HTTPConfig


class USASpendingClient(PaginatedAPIClient):
    """
    Client for USASpending.gov API
    
    Handles:
    - Federal award history lookup
    - Agency spending patterns
    - Recipient organization analysis
    - Award trend analysis
    """
    
    def __init__(self):
        http_config = HTTPConfig(
            timeout=60,  # USASpending can be slow with large datasets
            max_retries=3,
            user_agent="Catalynx/2.0 Grant Research Platform"
        )
        
        super().__init__(
            api_name="usaspending",
            base_url="https://api.usaspending.gov/api/v2",
            http_config=http_config,
            requires_api_key=False  # USASpending is public API
        )
        
        self.rate_limit_config = {
            'calls_per_hour': 2000,
            'delay_between_calls': 0.05
        }
    
    def _configure_rate_limits(self):
        """Configure USASpending specific rate limits"""
        self.http_client.set_api_rate_limit(
            self.api_name,
            calls_per_hour=2000,
            delay_between_calls=0.05
        )
    
    def _format_auth_headers(self, api_key: str) -> Dict[str, str]:
        """USASpending doesn't require authentication"""
        return {}
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to USASpending API"""
        try:
            response = await self._get("references/agency")
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
    
    async def search_awards_by_recipient(self,
                                       recipient_name: Optional[str] = None,
                                       recipient_ein: Optional[str] = None,
                                       award_types: Optional[List[str]] = None,
                                       agencies: Optional[List[str]] = None,
                                       start_date: Optional[str] = None,
                                       end_date: Optional[str] = None,
                                       max_results: int = 1000) -> List[Dict[str, Any]]:
        """
        Search for awards by recipient organization
        
        Args:
            recipient_name: Name of recipient organization
            recipient_ein: EIN of recipient organization
            award_types: Types of awards (grants, contracts, etc.)
            agencies: Awarding agencies
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            max_results: Maximum results to return
            
        Returns:
            List of award data
        """
        # Build search filters
        filters = {}
        
        if recipient_name:
            filters['recipient_search_text'] = [recipient_name]
        
        if recipient_ein:
            # Ensure EIN is properly formatted (9 digits)
            clean_ein = str(recipient_ein).replace('-', '').strip()
            if len(clean_ein) == 9 and clean_ein.isdigit():
                filters['recipient_id'] = [clean_ein]
            else:
                self.logger.warning(f"Invalid EIN format: {recipient_ein}")
                return []
        
        if award_types:
            filters['award_type_codes'] = award_types
        else:
            # Default to grants and cooperative agreements
            filters['award_type_codes'] = ['A', 'B', 'C', 'D']  # Grant types
        
        if agencies:
            filters['agencies'] = [{'type': 'awarding', 'tier': 'toptier', 'name': agency} for agency in agencies]
        
        # Date range
        if start_date or end_date:
            time_period = []
            if start_date and end_date:
                time_period.append({
                    'start_date': start_date,
                    'end_date': end_date
                })
            filters['time_period'] = time_period
        
        # Request payload
        payload = {
            'filters': filters,
            'fields': [
                'Award ID',
                'Award Title', 
                'Award Type',
                'Total Award Amount',
                'Description',
                'Start Date',
                'End Date',
                'Awarding Agency',
                'Awarding Sub Agency',
                'Recipient Name',
                'recipient_id'
            ],
            'page': 1,
            'limit': min(max_results, 100),
            'sort': 'Award Amount',
            'order': 'desc'
        }
        
        # Log the payload for debugging
        self.logger.debug(f"USASpending API payload: {payload}")
        
        max_pages = (max_results // 100) + 1
        try:
            return await self.get_all_pages_post(
                endpoint="search/spending_by_award",
                initial_payload=payload,
                max_pages=max_pages
            )
        except Exception as e:
            self.logger.error(f"USASpending API request failed with payload: {payload}")
            self.logger.error(f"Error details: {e}")
            return []
    
    async def get_recipient_profile(self, recipient_hash: str) -> Dict[str, Any]:
        """
        Get profile information for a recipient
        
        Args:
            recipient_hash: USASpending recipient hash/ID
            
        Returns:
            Recipient profile data
        """
        return await self._get(f"recipient/{recipient_hash}")
    
    async def get_agency_awards(self,
                              agency_code: str,
                              fiscal_year: Optional[int] = None,
                              award_types: Optional[List[str]] = None,
                              max_results: int = 1000) -> List[Dict[str, Any]]:
        """
        Get awards made by a specific agency
        
        Args:
            agency_code: Agency code or name
            fiscal_year: Specific fiscal year
            award_types: Award type codes
            max_results: Maximum results
            
        Returns:
            List of agency award data
        """
        filters = {
            'agencies': [{
                'type': 'awarding',
                'tier': 'toptier',
                'name': agency_code
            }]
        }
        
        if fiscal_year:
            filters['time_period'] = [{
                'start_date': f'{fiscal_year}-10-01',
                'end_date': f'{fiscal_year + 1}-09-30'
            }]
        
        if award_types:
            filters['award_type_codes'] = award_types
        
        payload = {
            'filters': filters,
            'fields': [
                'Award ID',
                'Award Title',
                'Award Type', 
                'Total Award Amount',
                'Start Date',
                'End Date',
                'Recipient Name',
                'recipient_id'
            ],
            'page': 1,
            'limit': min(max_results, 100),
            'sort': 'Award Amount',
            'order': 'desc'
        }
        
        # Log the payload for debugging
        self.logger.debug(f"USASpending API payload: {payload}")
        
        max_pages = (max_results // 100) + 1
        try:
            return await self.get_all_pages_post(
                endpoint="search/spending_by_award",
                initial_payload=payload,
                max_pages=max_pages
            )
        except Exception as e:
            self.logger.error(f"USASpending API request failed with payload: {payload}")
            self.logger.error(f"Error details: {e}")
            return []
    
    async def get_all_pages_post(self,
                               endpoint: str,
                               initial_payload: Dict[str, Any],
                               max_pages: int = 10,
                               progress_callback=None) -> List[Dict[str, Any]]:
        """
        Fetch all pages using POST requests (for complex search)
        
        Args:
            endpoint: API endpoint
            initial_payload: Initial POST payload
            max_pages: Maximum pages to fetch
            progress_callback: Optional progress callback
            
        Returns:
            List of all response data from all pages
        """
        all_results = []
        payload = initial_payload.copy()
        page_count = 0
        
        while page_count < max_pages:
            if progress_callback:
                progress_callback(f"Fetching page {page_count + 1}/{max_pages}")
            
            response = await self._post(endpoint, json_data=payload)
            
            # Extract data from response
            page_data = self._extract_page_data(response)
            if not page_data:
                break
                
            all_results.extend(page_data)
            
            # Check for next page
            pagination_info = self._extract_pagination_info(response)
            if not self._has_next_page(pagination_info):
                break
            
            # Update payload for next page
            payload['page'] = payload.get('page', 1) + 1
            page_count += 1
        
        self.logger.info(f"Fetched {len(all_results)} total results from {page_count + 1} pages")
        return all_results
    
    def _has_next_page(self, pagination_info: Dict[str, Any]) -> bool:
        """Check if there are more pages available"""
        current_page = pagination_info.get('page', 1)
        total_pages = pagination_info.get('total_pages', 1)
        return current_page < total_pages
    
    def _extract_pagination_info(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pagination info from USASpending response"""
        if not isinstance(response, dict):
            return {}
        
        return {
            'page': response.get('page', 1),
            'total_pages': response.get('page_metadata', {}).get('total_pages', 1),
            'total_count': response.get('page_metadata', {}).get('total_count', 0),
            'page_size': response.get('page_metadata', {}).get('page_size', 100)
        }
    
    def _build_next_page_params(self,
                               current_params: Dict[str, Any],
                               pagination_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build parameters for next page (not used for POST pagination)"""
        return None
    
    def _extract_page_data(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract award data from response"""
        if not isinstance(response, dict):
            return []
        
        return response.get('results', [])