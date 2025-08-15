"""
Base API Client
Abstract base class for all external API clients.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..core.http_client import CatalynxHTTPClient, HTTPConfig, get_http_client
from ..auth.api_key_manager import get_api_key_manager


class BaseAPIClient(ABC):
    """
    Abstract base class for all API clients.
    
    Provides common functionality:
    - HTTP client integration
    - API key management
    - Rate limiting configuration
    - Error handling patterns
    - Progress tracking
    """
    
    def __init__(self, 
                 api_name: str,
                 base_url: str,
                 http_config: Optional[HTTPConfig] = None,
                 requires_api_key: bool = True):
        
        self.api_name = api_name
        self.base_url = base_url.rstrip('/')
        self.requires_api_key = requires_api_key
        self.logger = logging.getLogger(f"clients.{api_name}")
        
        # Get HTTP client
        self.http_client = get_http_client(http_config)
        
        # Get API key if required
        if requires_api_key:
            self.api_key_manager = get_api_key_manager()
            self.api_key = self.api_key_manager.get_key(api_name)
            if not self.api_key:
                self.logger.warning(f"No API key configured for {api_name}")
        else:
            self.api_key = None
        
        # Configure rate limiting
        self._configure_rate_limits()
    
    @abstractmethod
    def _configure_rate_limits(self):
        """Configure API-specific rate limits"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection and return status"""
        pass
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for this API"""
        if self.api_key:
            return self._format_auth_headers(self.api_key)
        return {}
    
    @abstractmethod
    def _format_auth_headers(self, api_key: str) -> Dict[str, str]:
        """Format API key into appropriate headers"""
        pass
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint"""
        return f"{self.base_url}/{endpoint.lstrip('/')}"
    
    async def _get(self, 
                   endpoint: str,
                   params: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None,
                   cache_ttl: Optional[int] = None) -> Dict[str, Any]:
        """Perform authenticated GET request"""
        
        url = self._build_url(endpoint)
        
        # Merge auth headers
        request_headers = self._get_auth_headers()
        if headers:
            request_headers.update(headers)
        
        # Generate cache key
        cache_key = f"{self.api_name}:{endpoint}:{hash(str(params))}" if cache_ttl else None
        
        return await self.http_client.get(
            url=url,
            params=params,
            headers=request_headers,
            cache_key=cache_key,
            rate_limit_key=self.api_name
        )
    
    async def _post(self,
                    endpoint: str,
                    data: Optional[Dict[str, Any]] = None,
                    json_data: Optional[Dict[str, Any]] = None,
                    headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Perform authenticated POST request"""
        
        url = self._build_url(endpoint)
        
        # Merge auth headers
        request_headers = self._get_auth_headers()
        if headers:
            request_headers.update(headers)
        
        return await self.http_client.post(
            url=url,
            data=data,
            json_data=json_data,
            headers=request_headers,
            rate_limit_key=self.api_name
        )
    
    def get_client_info(self) -> Dict[str, Any]:
        """Get information about this client"""
        return {
            'api_name': self.api_name,
            'base_url': self.base_url,
            'requires_api_key': self.requires_api_key,
            'has_api_key': bool(self.api_key),
            'rate_limits': getattr(self, 'rate_limit_config', {})
        }


class PaginatedAPIClient(BaseAPIClient):
    """
    Base class for APIs that support pagination.
    """
    
    @abstractmethod
    def _extract_pagination_info(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pagination information from response"""
        pass
    
    @abstractmethod
    def _build_next_page_params(self, 
                                current_params: Dict[str, Any],
                                pagination_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build parameters for next page request"""
        pass
    
    async def get_all_pages(self,
                           endpoint: str,
                           initial_params: Optional[Dict[str, Any]] = None,
                           max_pages: int = 10,
                           progress_callback=None) -> List[Dict[str, Any]]:
        """
        Fetch all pages from a paginated endpoint
        
        Args:
            endpoint: API endpoint
            initial_params: Initial query parameters
            max_pages: Maximum pages to fetch
            progress_callback: Optional progress callback
            
        Returns:
            List of all response data from all pages
        """
        all_results = []
        params = initial_params or {}
        page_count = 0
        
        while page_count < max_pages:
            if progress_callback:
                progress_callback(f"Fetching page {page_count + 1}/{max_pages}")
            
            response = await self._get(endpoint, params=params)
            
            # Extract data from response
            page_data = self._extract_page_data(response)
            if not page_data:
                break
                
            all_results.extend(page_data)
            
            # Check for next page
            pagination_info = self._extract_pagination_info(response)
            next_params = self._build_next_page_params(params, pagination_info)
            
            if not next_params:
                break
                
            params = next_params
            page_count += 1
        
        self.logger.info(f"Fetched {len(all_results)} total results from {page_count + 1} pages")
        return all_results
    
    @abstractmethod
    def _extract_page_data(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract data items from a single page response"""
        pass