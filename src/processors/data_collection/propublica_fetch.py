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
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
import logging

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.core.entity_cache_manager import get_entity_cache_manager, EntityType, DataSourceType
from src.profiles.models import FormType, FoundationType
from src.clients.propublica_client import ProPublicaClient
from src.auth.api_key_manager import get_api_key_manager


class ProPublicaFetchProcessor(BaseProcessor):
    """Processor for fetching organization data from ProPublica API."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="propublica_fetch",
            description="Fetch detailed organization data from ProPublica Nonprofit Explorer API",
            version="3.0.0",  # Upgraded to use entity-based caching
            dependencies=["bmf_filter"],  # Depends on BMF filter results
            estimated_duration=300,  # 5 minutes for typical dataset
            requires_network=True,
            requires_api_key=False  # ProPublica API is public, no key required
        )
        super().__init__(metadata)
        
        # Initialize API client and entity cache manager
        self.propublica_client = ProPublicaClient()
        self.entity_cache_manager = get_entity_cache_manager()
        
        # Processing limits
        self.max_requests_per_second = 10  # Conservative rate limit
        self.request_delay = 1.0 / self.max_requests_per_second
        
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
            
            # Process organizations with rate limiting using new client
            enriched_organizations = []
            failed_eins = []
            
            for i, org in enumerate(organizations):
                try:
                    self._update_progress(i + 1, len(organizations), f"Processing {org.name}")
                    
                    # Rate limiting delay
                    if i > 0:
                        await asyncio.sleep(self.request_delay)
                    
                    # Fetch organization data using the client
                    enriched_org = await self._fetch_organization_data(org)
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
            # First check if input data was provided directly in config
            if hasattr(config, 'input_data') and config.input_data:
                input_orgs = config.input_data.get('organizations', [])
                if input_orgs:
                    self.logger.info(f"Using direct input data: {len(input_orgs)} organizations")
                    organizations = []
                    for org_dict in input_orgs:
                        try:
                            if isinstance(org_dict, dict):
                                org = OrganizationProfile(**org_dict)
                            else:
                                org = org_dict
                            organizations.append(org)
                        except Exception as e:
                            self.logger.warning(f"Failed to parse direct input organization data: {e}")
                            continue
                    return organizations
            
            # Get organizations from BMF filter processor via workflow_state
            if workflow_state and workflow_state.has_processor_succeeded('bmf_filter'):
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
        org: OrganizationProfile
    ) -> Optional[OrganizationProfile]:
        """Fetch detailed data for a single organization using entity cache first, then API."""
        
        try:
            # First check entity cache for existing ProPublica data
            cached_data = self.entity_cache_manager.get_entity_data(org.ein)
            
            if cached_data:
                self.logger.info(f"Using cached ProPublica data for {org.ein}")
                return await self._enrich_organization(org, cached_data)
            
            # No cached data, fetch from API
            self.logger.info(f"Fetching new ProPublica data for {org.ein}")
            
            # Search for organization by EIN using the client
            search_results = await self.propublica_client.search_organizations(org.ein)
            
            if not search_results:
                self.logger.info(f"No ProPublica data found for {org.ein}")
                return org  # Return original org without enrichment
            
            # Get the first matching organization
            pp_org = search_results[0]
            
            # Try to fetch detailed organization data by EIN
            detail_data = None
            try:
                detail_data = await self.propublica_client.get_organization_by_ein(org.ein)
                if detail_data:
                    # Cache the detailed data in entity-based structure
                    await self.entity_cache_manager.cache_nonprofit_propublica_data(
                        propublica_data=detail_data,
                        ein=org.ein
                    )
                    return await self._enrich_organization(org, detail_data)
            except Exception as e:
                self.logger.debug(f"Failed to get detailed data for {org.ein}: {e}")
            
            # If detailed fetch fails, use search data and cache it
            if pp_org:
                await self.entity_cache_manager.cache_nonprofit_propublica_data(
                    propublica_data=pp_org,
                    ein=org.ein
                )
                return await self._enrich_organization_from_search(org, pp_org)
            
            return org
                
        except Exception as e:
            self.logger.warning(f"Error fetching ProPublica data for {org.ein}: {e}")
            return None
    
    async def _enrich_organization(
        self, 
        org: OrganizationProfile, 
        pp_data: Dict[str, Any]
    ) -> OrganizationProfile:
        """Enrich organization profile with ProPublica detailed data, handling 990-PF forms specially."""
        
        organization = pp_data.get('organization', {})
        filings = pp_data.get('filings_with_data', [])
        
        # Update basic information
        if organization.get('name'):
            org.name = organization['name']
        
        # Detect form type and handle accordingly
        form_types_found = set()
        pf_filings = []
        regular_filings = []
        
        for filing in filings:
            form_type = filing.get('formtype', '').upper()
            form_types_found.add(form_type)
            
            if form_type in ['990PF', '990-PF']:
                pf_filings.append(filing)
            else:
                regular_filings.append(filing)
        
        # Determine primary form type
        if pf_filings:
            org.form_type = FormType.FORM_990_PF
            self.logger.info(f"Detected 990-PF form for {org.name} ({org.ein})")
            primary_filings = pf_filings
        else:
            org.form_type = FormType.FORM_990 if regular_filings else FormType.UNKNOWN
            primary_filings = regular_filings
        
        # Update financial data from most recent filing
        if primary_filings:
            recent_filing = primary_filings[0]  # Most recent filing
            
            # Extract financial data (990-PF has different field structure)
            if org.form_type == FormType.FORM_990_PF:
                await self._extract_990_pf_financial_data(org, recent_filing)
            else:
                await self._extract_990_financial_data(org, recent_filing)
            
            # Update filing information
            org.most_recent_filing_year = recent_filing.get('tax_prd_yr')
            org.filing_years = [f.get('tax_prd_yr') for f in filings if f.get('tax_prd_yr')]
            org.filing_consistency_score = len(org.filing_years) / 5.0  # Score based on 5-year consistency
            
            # Store raw filing data for financial scorer
            org.filing_data = {
                "filings": filings[:5]  # Store up to 5 most recent filings
            }
        
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
        
        # Add 990-PF specific processing notes
        if org.form_type == FormType.FORM_990_PF:
            org.add_processing_note("990-PF FOUNDATION: High-priority for grant research")
            if org.foundation_type == FoundationType.PRIVATE_NON_OPERATING:
                org.add_processing_note("Private Non-Operating Foundation - Prime grant research target")
        
        return org
    
    async def _extract_990_pf_financial_data(self, org: OrganizationProfile, filing: Dict[str, Any]) -> None:
        """Extract financial data specific to 990-PF forms."""
        
        try:
            # 990-PF specific fields from Part I
            if filing.get('totrevenue'):
                org.revenue = float(filing['totrevenue'])
            if filing.get('totassetsend'):
                org.assets = float(filing['totassetsend'])
            
            # Foundation-specific financial indicators
            investment_income = self._safe_float(filing.get('totinvstinc'))
            grants_paid = self._safe_float(filing.get('totgrntstoindv')) or self._safe_float(filing.get('totgrntsto'))
            
            # Mark as high-value for grant research if significant grant-making activity
            if grants_paid and grants_paid > 100000:  # $100K+ in grants
                org.add_processing_note(f"HIGH VALUE: Foundation paid ${grants_paid:,.0f} in grants - Strong grant research prospect")
            
            # Update foundation classification if needed
            if org.foundation_type == FoundationType.UNKNOWN and grants_paid:
                if investment_income and investment_income > grants_paid * 2:
                    org.foundation_type = FoundationType.PRIVATE_NON_OPERATING
                else:
                    org.foundation_type = FoundationType.PRIVATE_OPERATING
            
        except Exception as e:
            self.logger.debug(f"Error extracting 990-PF financial data: {e}")
    
    async def _extract_990_financial_data(self, org: OrganizationProfile, filing: Dict[str, Any]) -> None:
        """Extract financial data from regular 990 forms."""
        
        try:
            # Regular 990 fields
            if filing.get('totrevenue'):
                org.revenue = float(filing['totrevenue'])
            if filing.get('totassetsend'):
                org.assets = float(filing['totassetsend'])
            if filing.get('totfuncexpns'):
                org.expenses = float(filing['totfuncexpns'])
            
            # Calculate program expense ratio for nonprofits
            if org.expenses and filing.get('totprogrevs'):
                program_expenses = float(filing['totprogrevs'])
                org.program_expense_ratio = program_expenses / org.expenses
                
        except Exception as e:
            self.logger.debug(f"Error extracting 990 financial data: {e}")
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            if isinstance(value, str):
                # Remove common formatting
                import re
                cleaned = re.sub(r'[,$]', '', value.strip())
                if cleaned:
                    return float(cleaned)
                    
        except (ValueError, TypeError):
            pass
        
        return None
    
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