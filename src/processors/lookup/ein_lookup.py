"""
EIN Lookup Processor - Step 0
Validates and looks up organization information by EIN using ProPublica API.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.base_processor import BaseProcessor, ProcessorMetadata, SyncProcessorMixin
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.utils.decorators import retry_on_failure, rate_limit
from src.utils.validators import validate_ein, normalize_ein, ValidationError
# API key manager not needed - ProPublica API is public


class EINLookupProcessor(BaseProcessor, SyncProcessorMixin):
    """
    EIN Lookup Processor - validates EIN and fetches basic organization info.
    
    This is the first step in the grant research workflow, equivalent to your
    original Step_00_lookup_from_ein.py script.
    
    Features:
    - EIN validation and normalization
    - ProPublica API integration with rate limiting
    - Basic organization profile creation
    - Error handling and retry logic
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="ein_lookup",
            description="Look up organization information by EIN using ProPublica API",
            version="1.0.0",
            dependencies=[],  # No dependencies - this is Step 0
            estimated_duration=30,  # 30 seconds estimated
            requires_network=True,
            requires_api_key=False,  # ProPublica API is public
            can_run_parallel=True,
            processor_type="lookup"
        )
        super().__init__(metadata)
    
    def validate_processor_inputs(self, config: ProcessorConfig) -> List[str]:
        """Validate EIN lookup specific inputs."""
        errors = []
        
        target_ein = config.workflow_config.target_ein
        if not target_ein:
            errors.append("Target EIN is required for EIN lookup processor")
        elif not validate_ein(target_ein):
            errors.append(f"Invalid EIN format: {target_ein}")
        
        return errors
    
    def check_processor_api_requirements(self, config: ProcessorConfig) -> List[str]:
        """Check API requirements - ProPublica API is public, no key needed."""
        # ProPublica API is public and doesn't require authentication
        return []
    
    @rate_limit(calls_per_second=0.5)  # ProPublica rate limit: 2 seconds between calls
    async def _fetch_organization_data(self, ein: str) -> Dict[str, Any]:
        """
        Fetch organization data from ProPublica API.
        
        Args:
            ein: 9-digit EIN
            
        Returns:
            Organization data from API
            
        Raises:
            Exception: If API request fails
        """
        import aiohttp
        
        # ProPublica API endpoint (public API, no authentication required)
        url = f"https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"
        
        headers = {
            'User-Agent': 'Grant Research Automation Tool',
            'Accept': 'application/json'
        }
        
        self.logger.info(f"Fetching organization data for EIN: {ein}")
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self.logger.info(f"Successfully fetched data for EIN: {ein}")
                    return data
                elif response.status == 404:
                    raise ValueError(f"Organization not found for EIN: {ein}")
                elif response.status == 429:
                    raise ValueError("API rate limit exceeded - will retry")
                else:
                    error_text = await response.text()
                    raise ValueError(f"API request failed with status {response.status}: {error_text}")
    
    def _parse_propublica_data(self, api_data: Dict[str, Any], ein: str) -> OrganizationProfile:
        """
        Parse ProPublica API response into OrganizationProfile.
        
        Args:
            api_data: Raw API response data
            ein: EIN for the organization
            
        Returns:
            OrganizationProfile object
        """
        organization = api_data.get('organization', {})
        
        # Extract basic information
        name = organization.get('name', '').strip()
        if not name:
            raise ValueError(f"Organization name not found for EIN: {ein}")
        
        # Extract location information
        city = organization.get('city', '').strip()
        state = organization.get('state', '').strip()
        if not state:
            raise ValueError(f"State information not found for EIN: {ein}")
        
        # Extract NTEE code and description
        ntee_code = organization.get('ntee_code', '').strip()
        ntee_description = None
        
        # Get the most recent filing data for financial information
        filings = api_data.get('filings_with_data', [])
        most_recent_filing = None
        filing_years = []
        
        if filings:
            # Sort by tax period descending to get most recent
            sorted_filings = sorted(filings, key=lambda x: x.get('tax_prd_yr', 0), reverse=True)
            most_recent_filing = sorted_filings[0] if sorted_filings else None
            filing_years = [f.get('tax_prd_yr') for f in filings if f.get('tax_prd_yr')]
        
        # Extract financial data from most recent filing
        revenue = None
        assets = None
        expenses = None
        net_assets = None
        program_expenses = None
        most_recent_year = None
        
        if most_recent_filing:
            most_recent_year = most_recent_filing.get('tax_prd_yr')
            
            # Revenue (total revenue and support)
            revenue = most_recent_filing.get('totrevenue')
            
            # Assets
            assets = most_recent_filing.get('totassetsend')  # Total assets end of year
            
            # Expenses
            expenses = most_recent_filing.get('totfuncexpns')  # Total functional expenses
            
            # Net assets
            net_assets = most_recent_filing.get('netassetsend')  # Net assets end of year
            
            # Program expenses
            program_expenses = most_recent_filing.get('totprogrevn')  # Total program service revenue
        
        # Create organization profile
        profile = OrganizationProfile(
            ein=ein,
            name=name,
            ntee_code=ntee_code if ntee_code else None,
            ntee_description=ntee_description,
            state=state,
            city=city if city else None,
            revenue=revenue,
            assets=assets,
            expenses=expenses,
            net_assets=net_assets,
            program_expenses=program_expenses,
            most_recent_filing_year=most_recent_year,
            filing_years=filing_years,
            has_990_filing=len(filings) > 0,
            last_updated=datetime.now()
        )
        
        # Add data source
        profile.add_data_source("ProPublica Nonprofit Explorer API")
        
        # Calculate financial ratios if we have the data
        profile.calculate_financial_ratios()
        
        # Add processing notes
        profile.add_processing_note(f"Fetched from ProPublica API - {len(filings)} filings found")
        
        self.logger.info(f"Created organization profile for {name} (EIN: {ein})")
        
        return profile
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """
        Execute the EIN lookup process.
        
        Args:
            config: Processor configuration
            
        Returns:
            ProcessorResult with organization data
        """
        result = ProcessorResult(
            success=False,
            processor_name=self.metadata.name,
            start_time=datetime.now()
        )
        
        try:
            # Get and normalize EIN
            target_ein = config.workflow_config.target_ein
            normalized_ein = normalize_ein(target_ein)
            
            if not normalized_ein:
                result.add_error(f"Invalid EIN format: {target_ein}")
                return result
            
            self.logger.info(f"Starting EIN lookup for: {normalized_ein}")
            
            # Update progress
            self._update_progress(1, 4, f"Looking up EIN: {normalized_ein}")
            
            # Fetch organization data from ProPublica API
            try:
                api_data = await self._fetch_organization_data(normalized_ein)
                self._update_progress(2, 4, "Parsing organization data")
                
            except Exception as e:
                if "not found" in str(e).lower():
                    result.add_error(f"Organization not found for EIN: {normalized_ein}")
                    result.add_metadata("lookup_status", "not_found")
                else:
                    result.add_error(f"API request failed: {str(e)}")
                    result.add_metadata("lookup_status", "api_error")
                
                return result
            
            # Parse the API data into OrganizationProfile
            try:
                organization_profile = self._parse_propublica_data(api_data, normalized_ein)
                self._update_progress(3, 4, f"Processed data for {organization_profile.name}")
                
            except Exception as e:
                result.add_error(f"Failed to parse organization data: {str(e)}")
                return result
            
            # Store results
            result.add_data("target_organization", organization_profile.dict())
            result.add_data("ein", normalized_ein)
            result.add_data("organization_name", organization_profile.name)
            result.add_data("state", organization_profile.state)
            result.add_data("ntee_code", organization_profile.ntee_code)
            
            # Add metadata
            result.add_metadata("api_source", "ProPublica Nonprofit Explorer")
            result.add_metadata("filing_years_count", len(organization_profile.filing_years))
            result.add_metadata("most_recent_filing_year", organization_profile.most_recent_filing_year)
            result.add_metadata("lookup_status", "success")
            
            # Log summary
            filing_info = f"({len(organization_profile.filing_years)} filings)" if organization_profile.filing_years else "(no filings)"
            self.logger.info(
                f"EIN lookup successful: {organization_profile.name} "
                f"({organization_profile.state}) {filing_info}"
            )
            
            self._update_progress(4, 4, f"EIN lookup completed for {organization_profile.name}")
            
            result.success = True
            
        except Exception as e:
            self.logger.error(f"Unexpected error in EIN lookup: {str(e)}", exc_info=True)
            result.add_error(f"Unexpected error: {str(e)}")
        
        finally:
            result.end_time = datetime.now()
            if result.start_time and result.end_time:
                result.execution_time = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    async def cleanup(self, config: ProcessorConfig) -> None:
        """Clean up any resources (none needed for EIN lookup)."""
        pass


# Register the processor
def register_processor():
    """Register this processor with the workflow engine."""
    from src.core.workflow_engine import get_workflow_engine
    
    engine = get_workflow_engine()
    engine.register_processor(EINLookupProcessor)
    
    return EINLookupProcessor


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return EINLookupProcessor()