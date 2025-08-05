"""
BMF Filter Processor - Step 1
Filters IRS Business Master File data based on NTEE codes, state, and financial criteria.
"""
import asyncio
import logging
import csv
import io
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from pathlib import Path

from src.core.base_processor import BaseProcessor, ProcessorMetadata, SyncProcessorMixin, BatchProcessorMixin
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.utils.decorators import retry_on_failure, cache_result
from src.utils.validators import validate_ein, validate_state_code, validate_ntee_code, normalize_ein


class BMFFilterProcessor(BaseProcessor, SyncProcessorMixin, BatchProcessorMixin):
    """
    BMF Filter Processor - filters IRS Business Master File data.
    
    This is the second step in the grant research workflow, equivalent to your
    original Step_01_filter_irsbmf.py script.
    
    Features:
    - Downloads and processes IRS Business Master File
    - Filters by NTEE codes, state, and financial criteria
    - Extracts relevant organization data
    - Creates organization profiles for matching organizations
    - Handles large datasets efficiently with batch processing
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="bmf_filter",
            description="Filter IRS Business Master File by NTEE codes, state, and financial criteria",
            version="1.0.0",
            dependencies=["ein_lookup"],  # Depends on EIN lookup for target organization data
            estimated_duration=300,  # 5 minutes estimated (large file processing)
            requires_network=True,
            requires_api_key=False,
            can_run_parallel=False,  # Large file processing, better to run sequentially
            processor_type="filtering"
        )
        super().__init__(metadata)
        
        # BMF download URL (this is the public IRS data)
        self.bmf_url = "https://www.irs.gov/pub/irs-teb/eo_xx.csv"
        self.cache_dir = Path("cache/bmf")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_processor_inputs(self, config: ProcessorConfig) -> List[str]:
        """Validate BMF filter specific inputs."""
        errors = []
        
        workflow_config = config.workflow_config
        
        # Validate NTEE codes
        if not workflow_config.ntee_codes:
            errors.append("At least one NTEE code is required for BMF filtering")
        else:
            for ntee_code in workflow_config.ntee_codes:
                if not validate_ntee_code(ntee_code):
                    errors.append(f"Invalid NTEE code format: {ntee_code}")
        
        # Validate states
        all_states = workflow_config.get_all_states()
        if not all_states:
            errors.append("At least one state is required for BMF filtering")
        else:
            for state in all_states:
                if not validate_state_code(state):
                    errors.append(f"Invalid state code: {state}")
        
        # Validate financial criteria
        if workflow_config.min_revenue is not None and workflow_config.min_revenue < 0:
            errors.append("Minimum revenue cannot be negative")
        
        if (workflow_config.max_revenue is not None and 
            workflow_config.min_revenue is not None and 
            workflow_config.max_revenue < workflow_config.min_revenue):
            errors.append("Maximum revenue cannot be less than minimum revenue")
        
        return errors
    
    @cache_result(ttl_seconds=3600)  # Cache for 1 hour
    async def _download_bmf_data(self) -> str:
        """
        Get BMF data file path (checks for local files first, then downloads if needed).
        
        Returns:
            Path to BMF file
            
        Raises:
            Exception: If no BMF file available
        """
        # Check for Virginia-specific file first
        va_file = self.cache_dir / "eo_va.csv"
        if va_file.exists():
            self.logger.info(f"Using Virginia BMF file: {va_file}")
            return str(va_file)
        
        # Check for general cached file
        cache_file = self.cache_dir / "eo_bmf.csv"
        if cache_file.exists():
            # Check if file is less than 24 hours old
            file_age = datetime.now().timestamp() - cache_file.stat().st_mtime
            if file_age < 24 * 3600:  # 24 hours
                self.logger.info(f"Using cached BMF file: {cache_file}")
                return str(cache_file)
        
        # Try to download if no local file
        self.logger.info(f"Downloading BMF data from: {self.bmf_url}")
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
                async with session.get(self.bmf_url) as response:
                    if response.status == 200:
                        # Download in chunks to handle large file
                        with open(cache_file, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        self.logger.info(f"BMF data downloaded successfully: {cache_file}")
                        return str(cache_file)
                    else:
                        raise ValueError(f"Failed to download BMF data: HTTP {response.status}")
        
        except Exception as e:
            self.logger.error(f"Failed to download BMF data: {e}")
            # If download fails but we have a cached version, use it
            if cache_file.exists():
                self.logger.warning("Using older cached BMF file due to download failure")
                return str(cache_file)
            raise ValueError("No BMF data file available - please ensure eo_va.csv is in cache/bmf/ directory")
    
    def _parse_bmf_record(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Parse a single BMF record into a standardized format.
        
        Args:
            row: Raw CSV row from BMF file
            
        Returns:
            Parsed organization data or None if invalid
        """
        try:
            # Extract and validate EIN
            ein = row.get('EIN', '').strip()
            if not ein or not validate_ein(ein):
                return None
            
            ein = normalize_ein(ein)
            if not ein:
                return None
            
            # Extract basic information
            name = row.get('NAME', '').strip()
            if not name:
                return None
            
            # Extract location
            city = row.get('CITY', '').strip()
            state = row.get('STATE', '').strip()
            if not state or not validate_state_code(state):
                return None
            
            # Extract NTEE code
            ntee_code = row.get('NTEE_CD', '').strip()
            if not ntee_code:
                return None
            
            # Extract financial data (these may be empty in BMF)
            revenue = None
            assets = None
            
            revenue_str = row.get('INCOME_AMT', '').strip()
            if revenue_str and revenue_str.isdigit():
                revenue = float(revenue_str)
            
            assets_str = row.get('ASSET_AMT', '').strip()
            if assets_str and assets_str.isdigit():
                assets = float(assets_str)
            
            # Extract other useful fields
            classification = row.get('CLASSIFICATION', '').strip()
            foundation_code = row.get('FOUNDATION', '').strip()
            activity_code = row.get('ACTIVITY', '').strip()
            subsection_code = row.get('SUBSECTION', '').strip()
            asset_code = row.get('ASSET_CD', '').strip()
            income_code = row.get('INCOME_CD', '').strip()
            
            return {
                'ein': ein,
                'name': name,
                'city': city,
                'state': state,
                'ntee_code': ntee_code,
                'revenue': revenue,
                'assets': assets,
                'classification': classification,
                'foundation_code': foundation_code,
                'activity_code': activity_code,
                'subsection_code': subsection_code,
                'asset_code': asset_code,
                'income_code': income_code
            }
        
        except Exception as e:
            self.logger.debug(f"Failed to parse BMF record: {e}")
            return None
    
    def _matches_criteria(self, org_data: Dict[str, Any], config: ProcessorConfig) -> bool:
        """
        Check if organization matches filtering criteria.
        
        Args:
            org_data: Parsed organization data
            config: Processor configuration
            
        Returns:
            True if organization matches criteria
        """
        workflow_config = config.workflow_config
        
        # Check state filter
        all_states = workflow_config.get_all_states()
        if org_data['state'] not in all_states:
            return False
        
        # Check NTEE code filter
        org_ntee = org_data['ntee_code']
        if not any(org_ntee.startswith(code) for code in workflow_config.ntee_codes):
            return False
        
        # Check revenue filters
        org_revenue = org_data.get('revenue')
        if org_revenue is not None:
            if workflow_config.min_revenue is not None and org_revenue < workflow_config.min_revenue:
                return False
            if workflow_config.max_revenue is not None and org_revenue > workflow_config.max_revenue:
                return False
        
        # Check asset filters
        org_assets = org_data.get('assets')
        if org_assets is not None:
            if workflow_config.min_assets is not None and org_assets < workflow_config.min_assets:
                return False
            if workflow_config.max_assets is not None and org_assets > workflow_config.max_assets:
                return False
        
        return True
    
    def _create_organization_profile(self, org_data: Dict[str, Any]) -> OrganizationProfile:
        """
        Create OrganizationProfile from BMF data.
        
        Args:
            org_data: Parsed organization data
            
        Returns:
            OrganizationProfile object
        """
        profile = OrganizationProfile(
            ein=org_data['ein'],
            name=org_data['name'],
            ntee_code=org_data['ntee_code'],
            state=org_data['state'],
            city=org_data['city'],
            revenue=org_data.get('revenue'),
            assets=org_data.get('assets'),
            subsection_code=org_data.get('subsection_code'),
            asset_code=org_data.get('asset_code'),
            income_code=org_data.get('income_code'),
            last_updated=datetime.now()
        )
        
        # Add data source
        profile.add_data_source("IRS Business Master File")
        
        # Add processing notes
        profile.add_processing_note("Filtered from IRS BMF data")
        
        # Add additional data as processing notes
        if org_data.get('classification'):
            profile.add_processing_note(f"IRS Classification: {org_data['classification']}")
        if org_data.get('foundation_code'):
            profile.add_processing_note(f"Foundation Code: {org_data['foundation_code']}")
        if org_data.get('activity_code'):
            profile.add_processing_note(f"Activity Code: {org_data['activity_code']}")
        
        return profile
    
    async def _process_bmf_file(self, bmf_file_path: str, config: ProcessorConfig) -> List[OrganizationProfile]:
        """
        Process the BMF file and extract matching organizations.
        
        Args:
            bmf_file_path: Path to BMF CSV file
            config: Processor configuration
            
        Returns:
            List of matching organization profiles
        """
        matching_orgs = []
        total_records = 0
        processed_records = 0
        
        # First pass: count total records for progress tracking
        try:
            with open(bmf_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                total_records = sum(1 for _ in reader)
        except Exception as e:
            self.logger.warning(f"Could not count BMF records: {e}")
            total_records = 1000000  # Estimate
        
        self.logger.info(f"Processing {total_records} BMF records")
        
        # Second pass: process records
        try:
            with open(bmf_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                
                batch = []
                batch_size = 1000
                
                for row in reader:
                    processed_records += 1
                    
                    # Update progress every 1000 records
                    if processed_records % 1000 == 0:
                        progress_pct = (processed_records / total_records) * 100
                        self._update_progress(
                            processed_records, 
                            total_records, 
                            f"Processed {processed_records:,} records, found {len(matching_orgs)} matches"
                        )
                    
                    # Check for cancellation
                    if self.is_cancelled():
                        self.logger.info("BMF processing cancelled")
                        break
                    
                    # Parse record
                    org_data = self._parse_bmf_record(row)
                    if not org_data:
                        continue
                    
                    # Check if matches criteria
                    if self._matches_criteria(org_data, config):
                        profile = self._create_organization_profile(org_data)
                        matching_orgs.append(profile)
                        
                        # Check max results limit
                        if len(matching_orgs) >= config.workflow_config.max_results:
                            self.logger.info(f"Reached max results limit: {config.workflow_config.max_results}")
                            break
        
        except Exception as e:
            self.logger.error(f"Error processing BMF file: {e}")
            raise
        
        self.logger.info(f"BMF filtering complete: {len(matching_orgs)} organizations found")
        return matching_orgs
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """
        Execute the BMF filtering process.
        
        Args:
            config: Processor configuration
            
        Returns:
            ProcessorResult with filtered organization data
        """
        result = ProcessorResult(
            success=False,
            processor_name=self.metadata.name,
            start_time=datetime.now()
        )
        
        try:
            self.logger.info("Starting BMF filtering process")
            
            # Step 1: Download BMF data
            self._update_progress(1, 5, "Downloading IRS Business Master File")
            bmf_file_path = await self._download_bmf_data()
            
            # Step 2: Process BMF file
            self._update_progress(2, 5, "Processing BMF data")
            matching_orgs = await self._process_bmf_file(bmf_file_path, config)
            
            # Step 3: Store results
            self._update_progress(4, 5, f"Found {len(matching_orgs)} matching organizations")
            
            # Convert to dictionaries for storage
            org_dicts = [org.dict() for org in matching_orgs]
            
            result.add_data("organizations", org_dicts)
            result.add_data("organizations_count", len(matching_orgs))
            result.add_data("bmf_file_path", bmf_file_path)
            
            # Add metadata
            result.add_metadata("bmf_source", self.bmf_url)
            result.add_metadata("filter_criteria", {
                "ntee_codes": config.workflow_config.ntee_codes,
                "states": config.workflow_config.get_all_states(),
                "min_revenue": config.workflow_config.min_revenue,
                "max_revenue": config.workflow_config.max_revenue,
                "max_results": config.workflow_config.max_results
            })
            
            # Log summary
            states_str = ", ".join(config.workflow_config.get_all_states())
            ntee_str = ", ".join(config.workflow_config.ntee_codes)
            self.logger.info(
                f"BMF filtering successful: {len(matching_orgs)} organizations found "
                f"(States: {states_str}, NTEE: {ntee_str})"
            )
            
            self._update_progress(5, 5, f"BMF filtering completed - {len(matching_orgs)} organizations")
            
            result.success = True
        
        except Exception as e:
            self.logger.error(f"BMF filtering failed: {str(e)}", exc_info=True)
            result.add_error(f"BMF filtering error: {str(e)}")
        
        finally:
            result.end_time = datetime.now()
            if result.start_time and result.end_time:
                result.execution_time = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    async def cleanup(self, config: ProcessorConfig) -> None:
        """Clean up temporary files if needed."""
        # BMF files are cached, so we don't clean them up
        pass


# Register the processor
def register_processor():
    """Register this processor with the workflow engine."""
    from src.core.workflow_engine import get_workflow_engine
    
    engine = get_workflow_engine()
    engine.register_processor(BMFFilterProcessor)
    
    return BMFFilterProcessor


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return BMFFilterProcessor()