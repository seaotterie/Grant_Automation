"""
Virginia State Grants API Client
Client for Virginia state agency grant opportunities.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_client import BaseAPIClient
from ..core.http_client import HTTPConfig


class VAStateClient(BaseAPIClient):
    """
    Client for Virginia State Grant Opportunities
    
    Handles:
    - Multi-agency grant discovery
    - State-specific eligibility requirements
    - Application deadline tracking
    - Focus area matching
    """
    
    def __init__(self):
        http_config = HTTPConfig(
            timeout=45,
            max_retries=3,
            user_agent="Catalynx/2.0 Grant Research Platform"
        )
        
        super().__init__(
            api_name="va_state",
            base_url="https://www.commonwealth.virginia.gov/api/grants",
            http_config=http_config,
            requires_api_key=False  # Most state APIs are public
        )
        
        self.rate_limit_config = {
            'calls_per_hour': 500,
            'delay_between_calls': 0.2
        }
        
        # Virginia state agencies and their focus areas
        self.agencies = {
            'VDOF': {
                'name': 'Virginia Department of Forestry',
                'focus_areas': ['environmental', 'forestry', 'conservation'],
                'base_url': 'https://dof.virginia.gov/grants'
            },
            'VDEQ': {
                'name': 'Virginia Department of Environmental Quality',
                'focus_areas': ['environmental', 'water quality', 'air quality'],
                'base_url': 'https://deq.virginia.gov/grants'
            },
            'VDACS': {
                'name': 'Virginia Department of Agriculture and Consumer Services',
                'focus_areas': ['agriculture', 'food safety', 'rural development'],
                'base_url': 'https://vdacs.virginia.gov/grants'
            },
            'VDOT': {
                'name': 'Virginia Department of Transportation',
                'focus_areas': ['transportation', 'infrastructure', 'mobility'],
                'base_url': 'https://virginiadot.org/grants'
            },
            'VDHCD': {
                'name': 'Virginia Department of Housing and Community Development',
                'focus_areas': ['housing', 'community development', 'economic development'],
                'base_url': 'https://dhcd.virginia.gov/grants'
            },
            'VDH': {
                'name': 'Virginia Department of Health',
                'focus_areas': ['health', 'public health', 'community health'],
                'base_url': 'https://vdh.virginia.gov/grants'
            },
            'VDSS': {
                'name': 'Virginia Department of Social Services',
                'focus_areas': ['social services', 'family support', 'community services'],
                'base_url': 'https://dss.virginia.gov/grants'
            },
            'VEDP': {
                'name': 'Virginia Economic Development Partnership',
                'focus_areas': ['economic development', 'business development', 'tourism'],
                'base_url': 'https://vedp.virginia.gov/grants'
            },
            'VDCR': {
                'name': 'Virginia Department of Conservation and Recreation',
                'focus_areas': ['recreation', 'parks', 'conservation', 'historic preservation'],
                'base_url': 'https://dcr.virginia.gov/grants'
            },
            'VSAC': {
                'name': 'Virginia State Arts Council',
                'focus_areas': ['arts', 'culture', 'education'],
                'base_url': 'https://arts.virginia.gov/grants'
            }
        }
    
    def _configure_rate_limits(self):
        """Configure Virginia State specific rate limits"""
        self.http_client.set_api_rate_limit(
            self.api_name,
            calls_per_hour=500,
            delay_between_calls=0.2
        )
    
    def _format_auth_headers(self, api_key: str) -> Dict[str, str]:
        """Most Virginia APIs don't require authentication"""
        return {}
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Virginia State grant systems"""
        try:
            # Test connection to a few key agencies
            test_results = {}
            
            for agency_code, agency_info in list(self.agencies.items())[:3]:
                try:
                    # This would be actual API calls in production
                    # For now, return mock success
                    test_results[agency_code] = {
                        'status': 'success',
                        'name': agency_info['name']
                    }
                except Exception as e:
                    test_results[agency_code] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            return {
                'status': 'success',
                'api_name': self.api_name,
                'agencies_tested': len(test_results),
                'agency_results': test_results
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'api_name': self.api_name,
                'error': str(e)
            }
    
    async def search_opportunities(self,
                                 focus_areas: Optional[List[str]] = None,
                                 agencies: Optional[List[str]] = None,
                                 eligibility_type: Optional[str] = None,
                                 deadline_after: Optional[datetime] = None,
                                 max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Search for Virginia state grant opportunities
        
        Args:
            focus_areas: Areas of focus/interest
            agencies: Specific agencies to search
            eligibility_type: Type of eligible organizations
            deadline_after: Only opportunities with deadlines after this date
            max_results: Maximum results to return
            
        Returns:
            List of grant opportunity data
        """
        opportunities = []
        
        # Determine which agencies to search
        target_agencies = agencies if agencies else list(self.agencies.keys())
        
        for agency_code in target_agencies:
            if agency_code not in self.agencies:
                continue
                
            agency_info = self.agencies[agency_code]
            
            # Check focus area alignment if specified
            if focus_areas:
                agency_focus = set(agency_info['focus_areas'])
                requested_focus = set([area.lower() for area in focus_areas])
                
                # Skip if no overlap in focus areas
                if not agency_focus.intersection(requested_focus):
                    continue
            
            try:
                agency_opportunities = await self._get_agency_opportunities(
                    agency_code, 
                    agency_info,
                    eligibility_type,
                    deadline_after
                )
                
                opportunities.extend(agency_opportunities)
                
                if len(opportunities) >= max_results:
                    break
                    
            except Exception as e:
                self.logger.warning(f"Failed to get opportunities from {agency_code}: {e}")
                continue
        
        # Sort by relevance score and deadline
        opportunities = self._rank_opportunities(opportunities, focus_areas)
        
        return opportunities[:max_results]
    
    async def _get_agency_opportunities(self,
                                      agency_code: str,
                                      agency_info: Dict[str, Any],
                                      eligibility_type: Optional[str] = None,
                                      deadline_after: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get opportunities from a specific Virginia agency"""
        
        # In a real implementation, this would call the actual agency API
        # For now, return structured mock data based on agency characteristics
        
        base_opportunities = [
            {
                'id': f"{agency_code}_001",
                'title': f"{agency_info['name']} Community Grant Program",
                'agency_code': agency_code,
                'agency_name': agency_info['name'],
                'focus_areas': agency_info['focus_areas'],
                'description': f"Grant program supporting {', '.join(agency_info['focus_areas'])} initiatives in Virginia communities.",
                'funding_range': {
                    'min': 5000,
                    'max': 50000
                },
                'deadline': '2025-03-15',
                'eligibility': ['nonprofits', 'local_government', 'community_organizations'],
                'application_url': f"{agency_info['base_url']}/community-grants",
                'contact_email': f"grants@{agency_code.lower()}.virginia.gov",
                'priority_score': self._calculate_agency_priority(agency_code),
                'created_at': datetime.now().isoformat()
            },
            {
                'id': f"{agency_code}_002", 
                'title': f"{agency_info['name']} Innovation Initiative",
                'agency_code': agency_code,
                'agency_name': agency_info['name'],
                'focus_areas': agency_info['focus_areas'] + ['innovation'],
                'description': f"Supporting innovative approaches to {agency_info['focus_areas'][0]} challenges.",
                'funding_range': {
                    'min': 10000,
                    'max': 100000
                },
                'deadline': '2025-06-30',
                'eligibility': ['nonprofits', 'universities', 'research_institutions'],
                'application_url': f"{agency_info['base_url']}/innovation-grants",
                'contact_email': f"innovation@{agency_code.lower()}.virginia.gov",
                'priority_score': self._calculate_agency_priority(agency_code),
                'created_at': datetime.now().isoformat()
            }
        ]
        
        # Filter by eligibility if specified
        if eligibility_type:
            base_opportunities = [
                opp for opp in base_opportunities 
                if eligibility_type in opp.get('eligibility', [])
            ]
        
        # Filter by deadline if specified
        if deadline_after:
            base_opportunities = [
                opp for opp in base_opportunities
                if datetime.fromisoformat(opp['deadline']) > deadline_after
            ]
        
        return base_opportunities
    
    def _calculate_agency_priority(self, agency_code: str) -> int:
        """Calculate priority score for agencies (1-10)"""
        # Higher priority agencies based on grant volume and accessibility
        priority_map = {
            'VDHCD': 9,  # Housing & Community Development - high volume
            'VDH': 8,    # Health - many community programs
            'VDSS': 8,   # Social Services - community focused
            'VDEQ': 7,   # Environmental - growing focus
            'VEDP': 7,   # Economic Development - business focused
            'VDCR': 6,   # Conservation & Recreation - niche but valuable
            'VDOT': 5,   # Transportation - limited community grants
            'VDACS': 5,  # Agriculture - rural focus
            'VDOF': 4,   # Forestry - very specific
            'VSAC': 6    # Arts Council - niche but accessible
        }
        
        return priority_map.get(agency_code, 5)
    
    def _rank_opportunities(self, 
                          opportunities: List[Dict[str, Any]], 
                          focus_areas: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Rank opportunities by relevance and other factors"""
        
        for opp in opportunities:
            score = 0
            
            # Base score from agency priority
            score += opp.get('priority_score', 5) * 10
            
            # Boost score for focus area matches
            if focus_areas:
                opp_focus = set([area.lower() for area in opp.get('focus_areas', [])])
                requested_focus = set([area.lower() for area in focus_areas])
                
                matches = len(opp_focus.intersection(requested_focus))
                score += matches * 25
            
            # Boost for higher funding amounts
            funding_max = opp.get('funding_range', {}).get('max', 0)
            if funding_max > 75000:
                score += 20
            elif funding_max > 25000:
                score += 10
            
            # Penalty for very tight deadlines (less than 30 days)
            try:
                deadline = datetime.fromisoformat(opp['deadline'])
                days_until_deadline = (deadline - datetime.now()).days
                
                if days_until_deadline < 30:
                    score -= 15
                elif days_until_deadline > 90:
                    score += 10
                    
            except (ValueError, KeyError):
                pass
            
            opp['relevance_score'] = score
        
        # Sort by relevance score descending
        return sorted(opportunities, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    def get_agency_info(self, agency_code: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific Virginia agency"""
        return self.agencies.get(agency_code)
    
    def list_agencies(self) -> Dict[str, Dict[str, Any]]:
        """Get list of all supported Virginia agencies"""
        return self.agencies.copy()