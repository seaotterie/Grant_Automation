"""
Unit tests for HTTP client abstraction layer
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from aiohttp import ClientTimeout

from src.core.http_client import CatalynxHTTPClient, HTTPConfig, HTTPError


class TestHTTPConfig:
    """Test HTTPConfig data class"""
    
    def test_default_config(self):
        config = HTTPConfig()
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.rate_limit_calls == 100
        assert config.user_agent == "Catalynx/2.0 Grant Research Platform"
    
    def test_custom_config(self):
        config = HTTPConfig(
            timeout=60,
            max_retries=5,
            rate_limit_calls=200
        )
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.rate_limit_calls == 200


class TestCatalynxHTTPClient:
    """Test CatalynxHTTPClient functionality"""
    
    def test_client_initialization(self):
        client = CatalynxHTTPClient()
        assert client.config.timeout == 30
        assert client.rate_limits == {}
        assert client.call_history == []
    
    def test_custom_config_initialization(self):
        config = HTTPConfig(timeout=60, max_retries=5)
        client = CatalynxHTTPClient(config)
        assert client.config.timeout == 60
        assert client.config.max_retries == 5
    
    def test_cache_key_generation(self):
        client = CatalynxHTTPClient()
        
        # Test URL only
        key1 = client._generate_cache_key("https://example.com/api")
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hash length
        
        # Test URL with params
        key2 = client._generate_cache_key(
            "https://example.com/api", 
            {"param1": "value1", "param2": "value2"}
        )
        assert isinstance(key2, str)
        assert key1 != key2
        
        # Test consistent generation
        key3 = client._generate_cache_key(
            "https://example.com/api", 
            {"param2": "value2", "param1": "value1"}  # Different order
        )
        assert key2 == key3  # Should be same due to sorting
    
    def test_rate_limit_configuration(self):
        client = CatalynxHTTPClient()
        
        client.set_api_rate_limit("test_api", 500, 0.1)
        
        assert "test_api" in client.rate_limits
        rate_limit = client.rate_limits["test_api"]
        assert rate_limit.calls_remaining == 500
        assert rate_limit.delay_between_calls == 0.1
    
    @pytest.mark.asyncio
    async def test_get_session(self):
        client = CatalynxHTTPClient()
        
        async with client.get_session() as session:
            assert session is not None
            assert hasattr(session, 'get')
            assert hasattr(session, 'post')
        
        # Test session reuse
        async with client.get_session() as session1:
            async with client.get_session() as session2:
                assert session1 is session2
        
        await client.close()
    
    @pytest.mark.asyncio
    @patch('src.core.http_client.aiohttp.ClientSession')
    async def test_successful_get_request(self, mock_session_class):
        # Mock the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "success"})
        mock_response.content_type = "application/json"
        
        mock_session = AsyncMock()
        mock_session.request = AsyncMock()
        mock_session.request.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.request.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session_class.return_value = mock_session
        
        client = CatalynxHTTPClient()
        
        result = await client.get("https://example.com/api", params={"key": "value"})
        
        assert result == {"result": "success"}
        mock_session.request.assert_called_once()
        
        await client.close()
    
    @pytest.mark.asyncio
    @patch('src.core.http_client.aiohttp.ClientSession')
    async def test_http_error_handling(self, mock_session_class):
        # Mock error response
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.json = AsyncMock(return_value={"error": "Not found"})
        mock_response.content_type = "application/json"
        
        mock_session = AsyncMock()
        mock_session.request = AsyncMock()
        mock_session.request.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.request.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session_class.return_value = mock_session
        
        client = CatalynxHTTPClient()
        
        with pytest.raises(HTTPError) as exc_info:
            await client.get("https://example.com/nonexistent")
        
        assert exc_info.value.status_code == 404
        assert "Not found" in str(exc_info.value)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        client = CatalynxHTTPClient()
        client.config.rate_limit_calls = 2
        client.config.rate_limit_window = 1  # 1 second for testing
        
        # Simulate rate limiting
        import time
        start_time = time.time()
        
        # This should not trigger rate limiting initially
        await client._apply_rate_limit("test_api")
        await client._apply_rate_limit("test_api")  # Still within limit
        
        # This should trigger rate limiting
        with patch('asyncio.sleep') as mock_sleep:
            await client._apply_rate_limit("test_api")
            mock_sleep.assert_called()
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        client = CatalynxHTTPClient()
        
        # Initialize session
        async with client.get_session():
            pass
        
        # Verify session exists
        assert client._session is not None
        
        # Cleanup
        await client.close()
        
        # Verify session is cleaned up
        assert client._session is None


class TestHTTPError:
    """Test HTTPError exception class"""
    
    def test_basic_error(self):
        error = HTTPError("Test error")
        assert str(error) == "Test error"
        assert error.status_code is None
        assert error.response_data is None
    
    def test_error_with_details(self):
        response_data = {"error": "Invalid request"}
        error = HTTPError("Test error", 400, response_data)
        
        assert str(error) == "Test error"
        assert error.status_code == 400
        assert error.response_data == response_data