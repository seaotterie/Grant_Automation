#!/usr/bin/env python3
"""
ProPublica Fetch Processor (Step 2)
Fetches organization data from ProPublica's Nonprofit Explorer API.

This processor:
1. Takes organizations from BMF filter results
2. Queries ProPublica API for detailed 990 filing data
3. Extracts financial information and organizational details
4. Handles API rate limiting and error responses
5. Returns enriched organization profiles
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
import logging

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.auth.api_key_manager import get_api_key_manager


class ProPublicaFetchProcessor(BaseProcessor):
    """Processor for fetching organization data from ProPublica API."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="propublica_fetch",
            description="Fetch detailed organization data from ProPublica Nonprofit Explorer API",
            version="1.0.0",
            dependencies=["bmf_filter"],  # Depends on BMF filter results
            estimated_duration=300,  # 5 minutes for typical dataset
            requires_network=True,
            requires_api_key=False  # ProPublica API is public, no key required
        )
        super().__init__(metadata)
        
        # Rate limiting configuration
        self.max_requests_per_second = 10  # Conservative rate limit
        self.request_delay = 1.0 / self.max_requests_per_second
        self.max_retries = 3
        self.retry_delay = 2.0
        
        # ProPublica API endpoints
        self.base_url = "https://projects.propublica.org/nonprofits/api/v2"
        
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute ProPublica data fetching."""
        start_time = time.time()
        
        try:
            # Get organizations from previous step (BMF filter)
            organizations = await self._get_input_organizations(config, workflow_state)
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No organizations found from BMF filter step"]
                )
            
            self.logger.info(f"Fetching ProPublica data for {len(organizations)} organizations")
            
            # Process organizations with rate limiting
            enriched_organizations = []
            failed_eins = []
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                for i, org in enumerate(organizations):
                    try:
                        self._update_progress(i + 1, len(organizations), f"Processing {org.name}")
                        
                        # Rate limiting delay
                        if i > 0:
                            await asyncio.sleep(self.request_delay)
                        
                        # Fetch organization data
                        enriched_org = await self._fetch_organization_data(session, org)
                        if enriched_org:
                            enriched_organizations.append(enriched_org)
                        else:
                            failed_eins.append(org.ein)
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to process organization {org.ein}: {e}")
                        failed_eins.append(org.ein)
                        continue
            
            execution_time = time.time() - start_time
            
            # Prepare results
            result_data = {
                "organizations": [org.dict() for org in enriched_organizations],
                "total_processed": len(organizations),
                "successful_fetches": len(enriched_organizations),
                "failed_fetches": len(failed_eins)
            }
            
            warnings = []
            if failed_eins:
                warnings.append(f"Failed to fetch data for {len(failed_eins)} organizations")
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                warnings=warnings,
                metadata={
                    "api_source": "ProPublica Nonprofit Explorer",
                    "rate_limit": self.max_requests_per_second,
                    "failed_eins": failed_eins[:10]  # Include first 10 failed EINs
                }
            )
            
        except Exception as e:
            self.logger.error(f"ProPublica fetch failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"ProPublica fetch failed: {str(e)}"]
            )
    
    async def _get_input_organizations(self, config: ProcessorConfig, workflow_state) -> List[OrganizationProfile]:
        """Get organizations from the BMF filter step using improved data flow."""
        try:
            # Get organizations from BMF filter processor
            if workflow_state.has_processor_succeeded('bmf_filter'):
                org_dicts = workflow_state.get_organizations_from_processor('bmf_filter')
                if org_dicts:
                    self.logger.info(f"Retrieved {len(org_dicts)} organizations from BMF filter")
                    
                    # Convert dictionaries to OrganizationProfile objects
                    organizations = []
                    for org_dict in org_dicts:
                        try:
                            # Handle both dict and already instantiated objects
                            if isinstance(org_dict, dict):
                                org = OrganizationProfile(**org_dict)
                            else:
                                org = org_dict
                            organizations.append(org)
                        except Exception as e:
                            self.logger.warning(f"Failed to parse organization data: {e}")
                            continue
                    
                    return organizations
            
            # Fallback: create test organizations if BMF filter not available
            self.logger.warning("BMF filter not completed - using test data")
            test_orgs = [
                OrganizationProfile(
                    ein="541669652",
                    name="FAMILY FORWARD FOUNDATION", 
                    state="VA",
                    ntee_code="P81",
                    revenue=1000000,
                    asset_code="5",
                    income_code="7"
                )
            ]
            return test_orgs
            
        except Exception as e:
            self.logger.error(f"Failed to get input organizations: {e}")
            return []
    
    async def _fetch_organization_data(
        self, 
        session: aiohttp.ClientSession, 
        org: OrganizationProfile
    ) -> Optional[OrganizationProfile]:
        """Fetch detailed data for a single organization from ProPublica API."""
        
        try:
            # Search for organization by EIN
            search_url = f"{self.base_url}/search.json"
            params = {"q": org.ein}
            
            async with session.get(search_url, params=params) as response:
                if response.status != 200:
                    self.logger.warning(f"ProPublica search failed for {org.ein}: HTTP {response.status}")
                    return None
                
                search_data = await response.json()
                
                if not search_data.get('organizations'):
                    self.logger.info(f"No ProPublica data found for {org.ein}")
                    return org  # Return original org without enrichment
                
                # Get the first matching organization
                pp_org = search_data['organizations'][0]
                
                # Fetch detailed organization data
                org_id = pp_org.get('id')
                if org_id:
                    detail_url = f"{self.base_url}/organizations/{org_id}.json"
                    
                    async with session.get(detail_url) as detail_response:
                        if detail_response.status == 200:
                            detail_data = await detail_response.json()
                            return await self._enrich_organization(org, detail_data)
                
                # If detailed fetch fails, use search data
                return await self._enrich_organization_from_search(org, pp_org)
                
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout fetching ProPublica data for {org.ein}")
            return None
        except Exception as e:
            self.logger.warning(f"Error fetching ProPublica data for {org.ein}: {e}")
            return None
    
    async def _enrich_organization(
        self, 
        org: OrganizationProfile, 
        pp_data: Dict[str, Any]
    ) -> OrganizationProfile:
        """Enrich organization profile with ProPublica detailed data."""
        
        organization = pp_data.get('organization', {})
        filings = pp_data.get('filings_with_data', [])
        
        # Update basic information
        if organization.get('name'):
            org.name = organization['name']
        
        # Update financial data from most recent filing
        if filings:
            recent_filing = filings[0]  # Most recent filing
            
            # Extract financial data
            if recent_filing.get('totrevenue'):
                org.revenue = float(recent_filing['totrevenue'])
            if recent_filing.get('totassetsend'):
                org.assets = float(recent_filing['totassetsend'])
            if recent_filing.get('totfuncexpns'):
                org.expenses = float(recent_filing['totfuncexpns'])
            
            # Calculate program expense ratio
            if org.expenses and recent_filing.get('totprogrevs'):
                program_expenses = float(recent_filing['totprogrevs'])
                org.program_expense_ratio = program_expenses / org.expenses
            
            # Update filing information
            org.most_recent_filing_year = recent_filing.get('tax_prd_yr')
            org.filing_years = [f.get('tax_prd_yr') for f in filings if f.get('tax_prd_yr')]
            org.filing_consistency_score = len(org.filing_years) / 5.0  # Score based on 5-year consistency
        
        # Add mission and activity descriptions
        if organization.get('mission'):
            org.mission_description = organization['mission']
        if organization.get('activities'):
            org.activity_description = organization['activities']
        
        # Add NTEE code if available
        if organization.get('ntee_code'):
            org.ntee_code = organization['ntee_code']
        
        # Add data source tracking
        org.data_sources.append("ProPublica Nonprofit Explorer")
        org.last_updated = datetime.now()
        
        # Add processing notes
        org.add_processing_note("Enriched with ProPublica data")
        if filings:
            org.add_processing_note(f"Found {len(filings)} years of filing data")
        
        return org
    
    async def _enrich_organization_from_search(
        self, 
        org: OrganizationProfile, 
        search_result: Dict[str, Any]
    ) -> OrganizationProfile:
        """Enrich organization with limited search result data."""
        
        # Update name if available
        if search_result.get('name'):
            org.name = search_result['name']
        
        # Update state if available
        if search_result.get('state'):
            org.state = search_result['state']
        
        # Add any available revenue data
        if search_result.get('revenue_amount'):
            org.revenue = float(search_result['revenue_amount'])
        
        # Add data source
        org.data_sources.append("ProPublica Search")
        org.last_updated = datetime.now()
        org.add_processing_note("Limited ProPublica data from search")
        
        return org
    
    def validate_inputs(self, config: ProcessorConfig) -> List[str]:
        """Validate inputs for ProPublica fetch."""
        errors = []
        
        # Note: Input validation will be handled by the workflow engine
        # through dependency checking. BMF filter dependency is declared
        # in the processor metadata.
        
        return errors


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return ProPublicaFetchProcessor()