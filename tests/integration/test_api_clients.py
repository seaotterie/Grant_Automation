"""
Integration tests for API client implementations
"""
import pytest
from unittest.mock import AsyncMock, patch

from src.clients import GrantsGovClient, FoundationDirectoryClient, USASpendingClient, ProPublicaClient


class TestGrantsGovClient:
    """Test Grants.gov API client integration"""
    
    def test_client_initialization(self):
        client = GrantsGovClient()
        assert client.api_name == "grants_gov"
        assert client.base_url == "https://www.grants.gov/grantsws/rest"
        assert client.requires_api_key is False
    
    @pytest.mark.asyncio
    @patch('src.clients.grants_gov_client.CatalynxHTTPClient.get')
    async def test_search_opportunities(self, mock_get, mock_grants_gov_response):
        mock_get.return_value = mock_grants_gov_response
        
        client = GrantsGovClient()
        results = await client.search_opportunities(
            keyword="health",
            max_results=10
        )
        
        assert isinstance(results, list)
        mock_get.assert_called_once()
        
        # Verify the API call was made with correct parameters
        call_args = mock_get.call_args
        assert 'opportunities/search' in str(call_args)
    
    @pytest.mark.asyncio
    @patch('src.clients.grants_gov_client.CatalynxHTTPClient.get')
    async def test_get_opportunity_details(self, mock_get):
        mock_response = {
            "opportunityId": "EPA-Test-001",
            "opportunityTitle": "Environmental Grant",
            "description": "Detailed description"
        }
        mock_get.return_value = mock_response
        
        client = GrantsGovClient()
        result = await client.get_opportunity_details("EPA-Test-001")
        
        assert result["opportunityId"] == "EPA-Test-001"
        mock_get.assert_called_once()
    
    def test_pagination_info_extraction(self, mock_grants_gov_response):
        client = GrantsGovClient()
        pagination_info = client._extract_pagination_info(mock_grants_gov_response)
        
        assert 'total_hits' in pagination_info
        assert pagination_info['total_hits'] == 1
    
    def test_page_data_extraction(self, mock_grants_gov_response):
        client = GrantsGovClient()
        page_data = client._extract_page_data(mock_grants_gov_response)
        
        assert isinstance(page_data, list)
        assert len(page_data) == 1
        assert page_data[0]['opportunityId'] == "EPA-Test-001"


class TestFoundationDirectoryClient:
    """Test Foundation Directory API client integration"""
    
    def test_client_initialization(self):
        client = FoundationDirectoryClient()
        assert client.api_name == "foundation_directory"
        assert client.base_url == "https://api.foundationcenter.org/v2"
        assert client.requires_api_key is True
    
    @pytest.mark.asyncio
    @patch('src.clients.foundation_directory_client.CatalynxHTTPClient.get')
    async def test_search_corporate_foundations(self, mock_get):
        mock_response = {
            "foundations": [
                {
                    "id": "foundation_001",
                    "name": "Test Corporate Foundation",
                    "foundation_type": "corporate",
                    "assets": 1000000
                }
            ],
            "pagination": {
                "total_count": 1,
                "current_page": 1,
                "total_pages": 1
            }
        }
        mock_get.return_value = mock_response
        
        client = FoundationDirectoryClient()
        results = await client.search_corporate_foundations(
            industry="technology",
            max_results=10
        )
        
        assert isinstance(results, list)
        mock_get.assert_called_once()
    
    def test_auth_headers_format(self):
        client = FoundationDirectoryClient()
        headers = client._format_auth_headers("test_api_key")
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_api_key"
        assert headers["Content-Type"] == "application/json"


class TestUSASpendingClient:
    """Test USASpending.gov API client integration"""
    
    def test_client_initialization(self):
        client = USASpendingClient()
        assert client.api_name == "usaspending"
        assert client.base_url == "https://api.usaspending.gov/api/v2"
        assert client.requires_api_key is False
    
    @pytest.mark.asyncio
    @patch('src.clients.usaspending_client.CatalynxHTTPClient.post')
    async def test_search_awards_by_recipient(self, mock_post):
        mock_response = {
            "results": [
                {
                    "Award ID": "12345",
                    "Award Title": "Test Award",
                    "Total Award Amount": 50000,
                    "Recipient Name": "Test Organization"
                }
            ],
            "page_metadata": {
                "page": 1,
                "total_pages": 1,
                "total_count": 1
            }
        }
        mock_post.return_value = mock_response
        
        client = USASpendingClient()
        results = await client.search_awards_by_recipient(
            recipient_name="Test Organization",
            max_results=10
        )
        
        assert isinstance(results, list)
        mock_post.assert_called_once()
        
        # Verify POST data structure
        call_args = mock_post.call_args
        assert 'json_data' in call_args.kwargs
        json_data = call_args.kwargs['json_data']
        assert 'filters' in json_data
        assert 'fields' in json_data


class TestProPublicaClient:
    """Test ProPublica API client integration"""
    
    def test_client_initialization(self):
        client = ProPublicaClient()
        assert client.api_name == "propublica"
        assert client.base_url == "https://projects.propublica.org/nonprofits/api/v2"
        assert client.requires_api_key is False
    
    @pytest.mark.asyncio
    @patch('src.clients.propublica_client.CatalynxHTTPClient.get')
    async def test_search_organizations(self, mock_get):
        mock_response = {
            "organizations": [
                {
                    "ein": "123456789",
                    "name": "Test Nonprofit",
                    "state": "VA",
                    "ntee_code": "P81"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = ProPublicaClient()
        results = await client.search_organizations("test nonprofit")
        
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["ein"] == "123456789"
        mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.clients.propublica_client.CatalynxHTTPClient.get')
    async def test_get_organization_by_ein(self, mock_get):
        mock_response = {
            "ein": "123456789",
            "name": "Test Organization",
            "filings_with_data": [
                {"tax_year": 2023, "total_revenue": 500000}
            ]
        }
        mock_get.return_value = mock_response
        
        client = ProPublicaClient()
        result = await client.get_organization_by_ein("123456789")
        
        assert result["ein"] == "123456789"
        assert "filings_with_data" in result
        mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.clients.propublica_client.CatalynxHTTPClient.get')
    async def test_get_organization_filings(self, mock_get):
        mock_response = {
            "filings_with_data": [
                {"tax_year": 2023, "total_revenue": 500000},
                {"tax_year": 2022, "total_revenue": 450000}
            ]
        }
        mock_get.return_value = mock_response
        
        client = ProPublicaClient()
        filings = await client.get_organization_filings("123456789", limit=5)
        
        assert isinstance(filings, list)
        assert len(filings) == 2
        mock_get.assert_called_once()
    
    def test_extract_search_terms(self):
        client = ProPublicaClient()
        
        # Test with typical organization name
        terms = client._extract_search_terms("American Red Cross Foundation Inc")
        assert "american" in terms
        assert "red" in terms
        assert "cross" in terms
        assert "inc" not in terms  # Should be filtered out
        assert "foundation" not in terms  # Should be filtered out
        
        # Test with empty/None input
        terms = client._extract_search_terms("")
        assert terms == []
        
        terms = client._extract_search_terms(None)
        assert terms == []