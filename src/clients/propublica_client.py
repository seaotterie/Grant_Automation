"""
ProPublica Nonprofit Explorer API Client
Client for 990 tax filing data and nonprofit information.
"""
from typing import Dict, Any, List, Optional

from .base_client import BaseAPIClient
from ..core.http_client import HTTPConfig


class ProPublicaClient(BaseAPIClient):
    """
    Client for ProPublica Nonprofit Explorer API
    
    Handles:
    - Organization search and lookup
    - 990 tax filing retrieval
    - Financial data extraction
    - Organization profile building
    """
    
    def __init__(self):
        http_config = HTTPConfig(
            timeout=30,
            max_retries=3,
            user_agent="Catalynx/2.0 Grant Research Platform"
        )
        
        super().__init__(
            api_name="propublica",
            base_url="https://projects.propublica.org/nonprofits/api/v2",
            http_config=http_config,
            requires_api_key=False  # ProPublica API is public
        )
        
        self.rate_limit_config = {
            'calls_per_hour': 1000,
            'delay_between_calls': 0.1
        }
    
    def _configure_rate_limits(self):
        """Configure ProPublica specific rate limits"""
        self.http_client.set_api_rate_limit(
            self.api_name,
            calls_per_hour=1000,
            delay_between_calls=0.1
        )
    
    def _format_auth_headers(self, api_key: str) -> Dict[str, str]:
        """ProPublica doesn't require authentication"""
        return {}
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to ProPublica API"""
        try:
            # Test with a simple search
            response = await self.search_organizations("red cross", limit=1)
            return {
                'status': 'success',
                'api_name': self.api_name,
                'results_count': len(response)
            }
        except Exception as e:
            return {
                'status': 'error',
                'api_name': self.api_name,
                'error': str(e)
            }
    
    async def search_organizations(self,
                                 query: str,
                                 state: Optional[str] = None,
                                 ntee_code: Optional[str] = None,
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for organizations by name
        
        Args:
            query: Search query string
            state: State abbreviation filter
            ntee_code: NTEE code filter
            limit: Maximum results to return
            
        Returns:
            List of organization data
        """
        params = {
            'q': query,
            'limit': min(limit, 100)  # API limit
        }
        
        if state:
            params['state'] = state.upper()
        if ntee_code:
            params['ntee'] = ntee_code
        
        response = await self._get("search.json", params=params)
        
        # ProPublica returns different structures
        if isinstance(response, dict):
            return response.get('organizations', [])
        elif isinstance(response, list):
            return response
        else:
            return []
    
    async def get_organization_by_ein(self, ein: str) -> Optional[Dict[str, Any]]:
        """
        Get organization details by EIN
        
        Args:
            ein: Employer Identification Number
            
        Returns:
            Organization data or None if not found
        """
        try:
            response = await self._get(f"organizations/{ein}.json")
            return response if isinstance(response, dict) else None
        except Exception as e:
            self.logger.warning(f"Organization not found for EIN {ein}: {e}")
            return None
    
    async def get_organization_filings(self, 
                                     ein: str,
                                     limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get 990 filings for an organization
        
        Args:
            ein: Employer Identification Number
            limit: Maximum filings to return
            
        Returns:
            List of filing data
        """
        try:
            org_data = await self.get_organization_by_ein(ein)
            if not org_data:
                return []
            
            # Get filings from organization data
            filings = org_data.get('filings_with_data', [])
            
            # Limit results
            if limit and len(filings) > limit:
                filings = filings[:limit]
            
            return filings
            
        except Exception as e:
            self.logger.error(f"Failed to get filings for EIN {ein}: {e}")
            return []
    
    async def get_filing_details(self, 
                               ein: str, 
                               tax_year: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed 990 filing data for specific year
        
        Args:
            ein: Employer Identification Number
            tax_year: Tax year of filing
            
        Returns:
            Detailed filing data or None
        """
        try:
            response = await self._get(f"organizations/{ein}/{tax_year}.json")
            return response if isinstance(response, dict) else None
        except Exception as e:
            self.logger.warning(f"Filing not found for EIN {ein}, year {tax_year}: {e}")
            return None
    
    async def get_similar_organizations(self,
                                      ein: str,
                                      ntee_code: Optional[str] = None,
                                      state: Optional[str] = None,
                                      revenue_range: Optional[tuple] = None,
                                      limit: int = 50) -> List[Dict[str, Any]]:
        """
        Find organizations similar to the given EIN
        
        Args:
            ein: Reference organization EIN
            ntee_code: NTEE code filter
            state: State filter
            revenue_range: Tuple of (min_revenue, max_revenue)
            limit: Maximum results
            
        Returns:
            List of similar organizations
        """
        # First get the reference organization to determine similarity criteria
        reference_org = await self.get_organization_by_ein(ein)
        if not reference_org:
            return []
        
        # Extract characteristics for similarity search
        search_criteria = {}
        
        if not ntee_code and 'ntee_code' in reference_org:
            ntee_code = reference_org['ntee_code']
        
        if not state and 'state' in reference_org:
            state = reference_org['state']
        
        # Build search query based on organization name/type
        org_name = reference_org.get('name', '')
        search_terms = self._extract_search_terms(org_name)
        
        similar_orgs = []
        
        # Search using extracted terms
        for term in search_terms[:3]:  # Limit search terms
            try:
                results = await self.search_organizations(
                    query=term,
                    state=state,
                    ntee_code=ntee_code,
                    limit=min(limit, 25)
                )
                
                # Filter out the reference organization itself
                filtered_results = [
                    org for org in results 
                    if org.get('ein') != ein
                ]
                
                similar_orgs.extend(filtered_results)
                
                if len(similar_orgs) >= limit:
                    break
                    
            except Exception as e:
                self.logger.warning(f"Search failed for term '{term}': {e}")
                continue
        
        # Remove duplicates and limit results
        seen_eins = set()
        unique_orgs = []
        
        for org in similar_orgs:
            org_ein = org.get('ein')
            if org_ein and org_ein not in seen_eins:
                seen_eins.add(org_ein)
                unique_orgs.append(org)
                
                if len(unique_orgs) >= limit:
                    break
        
        return unique_orgs
    
    def _extract_search_terms(self, org_name: str) -> List[str]:
        """Extract meaningful search terms from organization name"""
        if not org_name:
            return []
        
        # Remove common organization suffixes
        suffixes = [
            'inc', 'incorporated', 'corp', 'corporation', 'llc', 'ltd', 'limited',
            'foundation', 'fund', 'trust', 'society', 'association', 'org',
            'organization', 'centre', 'center', 'institute', 'university',
            'college', 'school', 'hospital', 'clinic', 'church'
        ]
        
        words = org_name.lower().replace(',', ' ').replace('.', ' ').split()
        
        # Filter out common words and suffixes
        meaningful_words = []
        for word in words:
            word = word.strip('()')
            if len(word) > 2 and word not in suffixes:
                meaningful_words.append(word)
        
        # Return combinations of words
        search_terms = []
        if meaningful_words:
            # Single most meaningful word
            search_terms.append(meaningful_words[0])
            
            # Two-word combinations
            if len(meaningful_words) > 1:
                search_terms.append(' '.join(meaningful_words[:2]))
                
            # Three-word combinations
            if len(meaningful_words) > 2:
                search_terms.append(' '.join(meaningful_words[:3]))
        
        return search_terms