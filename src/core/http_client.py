"""
HTTP Client Abstraction Layer
Centralized HTTP client with retry logic, caching, rate limiting, and error handling.
"""
import asyncio
import aiohttp
import time
import logging
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import json
import hashlib

from .cache_manager import get_cache_manager, CacheType


@dataclass
class HTTPConfig:
    """HTTP client configuration"""
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    rate_limit_calls: int = 100
    rate_limit_window: int = 3600  # 1 hour
    cache_ttl: int = 3600  # 1 hour
    user_agent: str = "Catalynx/2.0 Grant Research Platform"
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class APIRateLimit:
    """Rate limiting configuration for specific APIs"""
    calls_remaining: int
    window_reset: datetime
    delay_between_calls: float = 0.0


class HTTPError(Exception):
    """Custom HTTP error with response details"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class CatalynxHTTPClient:
    """
    Centralized HTTP client for all API interactions in Catalynx.
    
    Features:
    - Automatic retry with exponential backoff
    - Response caching
    - Rate limiting per API endpoint
    - Structured error handling
    - Progress tracking integration
    - Connection pooling
    """
    
    def __init__(self, config: Optional[HTTPConfig] = None):
        self.config = config or HTTPConfig()
        self.logger = logging.getLogger(__name__)
        self.cache_manager = get_cache_manager()
        
        # Rate limiting tracking
        self.rate_limits: Dict[str, APIRateLimit] = {}
        self.call_history: List[float] = []
        
        # Session will be created lazily
        self._session: Optional[aiohttp.ClientSession] = None
        
    @asynccontextmanager
    async def get_session(self):
        """Get or create HTTP session with proper cleanup"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                enable_cleanup_closed=True
            )
            
            headers = {
                'User-Agent': self.config.user_agent,
                **self.config.headers
            }
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=headers,
                raise_for_status=False
            )
        
        try:
            yield self._session
        finally:
            # Session cleanup is handled by context manager consumer
            pass
    
    async def close(self):
        """Close HTTP session and cleanup resources"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def get(self, 
                  url: str, 
                  params: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None,
                  cache_key: Optional[str] = None,
                  rate_limit_key: Optional[str] = None,
                  progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Perform GET request with caching, rate limiting, and retry logic
        
        Args:
            url: Target URL
            params: Query parameters
            headers: Additional headers
            cache_key: Key for caching (auto-generated if None)
            rate_limit_key: Key for rate limiting (uses domain if None)
            progress_callback: Optional progress callback
            
        Returns:
            Response data as dictionary
        """
        return await self._request(
            'GET', url, params=params, headers=headers,
            cache_key=cache_key, rate_limit_key=rate_limit_key,
            progress_callback=progress_callback
        )
    
    async def post(self,
                   url: str,
                   data: Optional[Dict[str, Any]] = None,
                   json_data: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None,
                   rate_limit_key: Optional[str] = None,
                   progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Perform POST request with rate limiting and retry logic
        
        Args:
            url: Target URL
            data: Form data
            json_data: JSON data
            headers: Additional headers
            rate_limit_key: Key for rate limiting
            progress_callback: Optional progress callback
            
        Returns:
            Response data as dictionary
        """
        return await self._request(
            'POST', url, data=data, json_data=json_data, headers=headers,
            rate_limit_key=rate_limit_key, progress_callback=progress_callback
        )
    
    async def _request(self,
                      method: str,
                      url: str,
                      params: Optional[Dict[str, Any]] = None,
                      data: Optional[Dict[str, Any]] = None,
                      json_data: Optional[Dict[str, Any]] = None,
                      headers: Optional[Dict[str, str]] = None,
                      cache_key: Optional[str] = None,
                      rate_limit_key: Optional[str] = None,
                      progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Internal request method with all the logic"""
        
        # Generate cache key for GET requests
        if method == 'GET' and not cache_key:
            cache_key = self._generate_cache_key(url, params)
        
        # Check cache first for GET requests
        if method == 'GET' and cache_key:
            cached_data = await self.cache_manager.get(
                identifier=cache_key,
                cache_type=CacheType.API_RESPONSE
            )
            if cached_data:
                self.logger.debug(f"Cache hit for {cache_key}")
                return cached_data
        
        # Apply rate limiting
        if rate_limit_key:
            await self._apply_rate_limit(rate_limit_key)
        
        # Prepare headers
        request_headers = headers.copy() if headers else {}
        
        # Retry logic
        last_error = None
        for attempt in range(self.config.max_retries + 1):
            try:
                if progress_callback:
                    progress_callback(f"HTTP {method} attempt {attempt + 1}/{self.config.max_retries + 1}: {url}")
                
                async with self.get_session() as session:
                    kwargs = {
                        'headers': request_headers,
                        'allow_redirects': True
                    }
                    
                    if params:
                        kwargs['params'] = params
                    if data:
                        kwargs['data'] = data
                    if json_data:
                        kwargs['json'] = json_data
                    
                    async with session.request(method, url, **kwargs) as response:
                        response_data = await self._process_response(response, url)
                        
                        # Cache successful GET responses
                        if method == 'GET' and cache_key and response.status == 200:
                            await self.cache_manager.set(
                                identifier=cache_key,
                                cache_type=CacheType.API_RESPONSE,
                                content=response_data,
                                ttl=timedelta(seconds=self.config.cache_ttl)
                            )
                        
                        return response_data
                        
            except (aiohttp.ClientError, asyncio.TimeoutError, HTTPError) as e:
                last_error = e
                self.logger.warning(f"HTTP request attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (self.config.retry_backoff ** attempt)
                    await asyncio.sleep(delay)
                else:
                    break
        
        # All retries failed
        error_msg = f"HTTP {method} to {url} failed after {self.config.max_retries + 1} attempts"
        if last_error:
            error_msg += f": {last_error}"
        
        raise HTTPError(error_msg)
    
    async def _process_response(self, response: aiohttp.ClientResponse, url: str) -> Dict[str, Any]:
        """Process HTTP response and handle errors"""
        try:
            # Read response content
            if response.content_type and 'json' in response.content_type:
                response_data = await response.json()
            else:
                text_data = await response.text()
                try:
                    response_data = json.loads(text_data)
                except json.JSONDecodeError:
                    response_data = {'content': text_data}
            
            # Handle HTTP errors
            if response.status >= 400:
                error_msg = f"HTTP {response.status} for {url}"
                if isinstance(response_data, dict) and 'error' in response_data:
                    error_msg += f": {response_data['error']}"
                
                raise HTTPError(error_msg, response.status, response_data)
            
            return response_data
            
        except aiohttp.ContentTypeError as e:
            # Handle non-JSON responses
            text_data = await response.text()
            self.logger.warning(f"Non-JSON response from {url}: {e}")
            return {'content': text_data, 'content_type': response.content_type}
    
    def _generate_cache_key(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key from URL and parameters"""
        key_parts = [url]
        if params:
            # Sort params for consistent cache keys
            sorted_params = sorted(params.items())
            key_parts.append(str(sorted_params))
        
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def _apply_rate_limit(self, rate_limit_key: str):
        """Apply rate limiting for specific API"""
        now = time.time()
        
        # Clean old calls from history
        window_start = now - self.config.rate_limit_window
        self.call_history = [call_time for call_time in self.call_history if call_time > window_start]
        
        # Check if we're exceeding rate limit
        if len(self.call_history) >= self.config.rate_limit_calls:
            # Calculate wait time until oldest call expires
            oldest_call = min(self.call_history)
            wait_time = oldest_call + self.config.rate_limit_window - now
            
            if wait_time > 0:
                self.logger.info(f"Rate limit reached for {rate_limit_key}, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
        
        # Apply API-specific rate limiting
        if rate_limit_key in self.rate_limits:
            rate_limit = self.rate_limits[rate_limit_key]
            if rate_limit.delay_between_calls > 0:
                await asyncio.sleep(rate_limit.delay_between_calls)
        
        # Record this call
        self.call_history.append(now)
    
    def set_api_rate_limit(self, api_key: str, calls_per_hour: int, delay_between_calls: float = 0.0):
        """Set specific rate limiting for an API"""
        self.rate_limits[api_key] = APIRateLimit(
            calls_remaining=calls_per_hour,
            window_reset=datetime.now() + timedelta(hours=1),
            delay_between_calls=delay_between_calls
        )
        
        self.logger.info(f"Set rate limit for {api_key}: {calls_per_hour} calls/hour, {delay_between_calls}s delay")


# Global HTTP client instance
_http_client: Optional[CatalynxHTTPClient] = None


def get_http_client(config: Optional[HTTPConfig] = None) -> CatalynxHTTPClient:
    """Get global HTTP client instance"""
    global _http_client
    if _http_client is None:
        _http_client = CatalynxHTTPClient(config)
    return _http_client


async def cleanup_http_client():
    """Cleanup global HTTP client"""
    global _http_client
    if _http_client:
        await _http_client.close()
        _http_client = None