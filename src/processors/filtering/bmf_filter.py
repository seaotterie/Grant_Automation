"""
BMF Filter Processor - Enhanced with Web Validation
Filters IRS Business Master File data and validates organizations with web presence.
"""
import asyncio
import logging
import sqlite3
import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path

from src.core.base_processor import BaseProcessor, ProcessorMetadata, SyncProcessorMixin, BatchProcessorMixin
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.profiles.models import FormType, FoundationType, ApplicationAcceptanceStatus
from src.utils.decorators import retry_on_failure, cache_result
from src.utils.validators import validate_ein, validate_state_code, validate_ntee_code, normalize_ein
from src.core.simple_mcp_client import SimpleMCPClient


class BMFFilterProcessor(BaseProcessor, SyncProcessorMixin, BatchProcessorMixin):
    """
    BMF Filter Processor - filters IRS Business Master File data from SQLite database.
    
    This is the second step in the grant research workflow, equivalent to your
    original Step_01_filter_irsbmf.py script.
    
    Features:
    - Queries SQLite database with BMF and SOI data
    - Filters by NTEE codes, state, and financial criteria
    - Extracts relevant organization data with rich financial information
    - Creates organization profiles for matching organizations
    - Handles large datasets efficiently with SQL queries
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="bmf_filter",
            description="Filter IRS Business Master File by NTEE codes, state, and financial criteria using SQL database",
            version="2.0.0",
            dependencies=["bmf_soi_database"],  # Depends on BMF/SOI database
            estimated_duration=30,  # Much faster with SQL queries
            requires_network=False,  # Uses local database
            requires_api_key=False,
            can_run_parallel=True,  # SQL queries can run in parallel
            processor_type="filtering"
        )
        super().__init__(metadata)
        
        # Database configuration
        self.db_path = Path("data/nonprofit_intelligence.db")
        self.catalynx_db_path = "data/catalynx.db"
        
        # Web validation configuration
        self.mcp_client = SimpleMCPClient(timeout=10)  # Shorter timeout for bulk validation
        self.enable_web_validation = True  # Can be disabled via config
        
        # Performance optimization settings
        self.max_processing_time = 30  # seconds
        self.batch_size = 1000  # Process in batches for better performance
        self.early_exit_threshold = 500  # Exit early if we have enough results
        self.progress_update_interval = 1000  # Update progress every N records
        
        # Web validation settings
        self.web_validation_batch_size = 20  # Validate URLs in smaller batches
        self.web_validation_delay = 0.5  # Delay between web validation requests
        self.max_web_validations_per_run = 100  # Limit validations to avoid overwhelming
    
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
    
    def _check_database_exists(self) -> bool:
        """
        Check if the BMF/SOI database exists and is accessible.
        
        Returns:
            True if database is accessible
        """
        try:
            if not self.db_path.exists():
                self.logger.error(f"Database not found at: {self.db_path}")
                return False
            
            # Test database connection
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM bmf_organizations LIMIT 1")
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Database check failed: {e}")
            return False
    
    def _parse_database_record(self, row: tuple, columns: List[str]) -> Optional[Dict[str, Any]]:
        """
        Parse a database row into a standardized format.
        
        Args:
            row: Database row tuple
            columns: Column names
            
        Returns:
            Parsed organization data or None if invalid
        """
        try:
            # Convert tuple to dictionary
            record = dict(zip(columns, row))
            
            # Validate EIN
            ein = record.get('ein', '').strip() if record.get('ein') else ''
            if not ein or not validate_ein(ein):
                return None
            
            # Extract basic information
            name = record.get('name', '').strip() if record.get('name') else ''
            if not name:
                return None
            
            # Extract location
            city = record.get('city', '').strip() if record.get('city') else ''
            state = record.get('state', '').strip() if record.get('state') else ''
            if not state or not validate_state_code(state):
                return None
            
            # Extract NTEE code
            ntee_code = record.get('ntee_code', '').strip() if record.get('ntee_code') else ''
            if not ntee_code:
                return None
            
            return {
                'ein': ein,
                'name': name,
                'city': city,
                'state': state,
                'ntee_code': ntee_code,
                'revenue': record.get('revenue'),
                'assets': record.get('assets'),
                'classification': record.get('classification'),
                'foundation_code': record.get('foundation_code'),
                'activity_code': record.get('organization_code'),
                'subsection_code': record.get('subsection'),
                'asset_code': record.get('asset_cd'),
                'income_code': record.get('income_cd'),
                # Additional SOI data if available
                'total_revenue_990': record.get('total_revenue'),
                'total_expenses_990': record.get('total_expenses'),
                'net_assets_990': record.get('net_assets'),
                'contributions_990': record.get('contributions'),
                'program_service_revenue_990': record.get('program_service_revenue')
            }
        
        except Exception as e:
            self.logger.debug(f"Failed to parse database record: {e}")
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
        
        # Revenue and asset data are collected for analysis but do not exclude organizations
        # This ensures comprehensive discovery with financial data as analysis inputs rather than filtering constraints
        
        return True
    
    def _create_organization_profile(self, org_data: Dict[str, Any]) -> OrganizationProfile:
        """
        Create OrganizationProfile from BMF and SOI data with enriched financial information.
        
        Args:
            org_data: Parsed organization data from database
            
        Returns:
            OrganizationProfile object
        """
        # Classify foundation type and form type
        foundation_code = org_data.get('foundation_code', '').strip()
        foundation_type = self._classify_foundation_type(foundation_code)
        form_type = self._determine_form_type(foundation_code)
        
        # Use most recent/complete financial data available
        revenue = org_data.get('total_revenue_990') or org_data.get('pf_total_revenue') or org_data.get('revenue')
        assets = org_data.get('net_assets_990') or org_data.get('pf_net_assets') or org_data.get('assets')
        
        profile = OrganizationProfile(
            ein=org_data['ein'],
            name=org_data['name'],
            ntee_code=org_data['ntee_code'],
            state=org_data['state'],
            city=org_data['city'],
            revenue=revenue,
            assets=assets,
            subsection_code=org_data.get('subsection_code'),
            asset_code=org_data.get('asset_code'),
            income_code=org_data.get('income_code'),
            last_updated=datetime.now(),
            
            # 990-PF specific fields
            form_type=form_type,
            foundation_type=foundation_type,
            foundation_code=foundation_code if foundation_code else None
        )
        
        # Add data sources
        profile.add_data_source("IRS Business Master File")
        if org_data.get('total_revenue_990'):
            profile.add_data_source("IRS Form 990 (SOI Extract)")
        if org_data.get('pf_total_revenue'):
            profile.add_data_source("IRS Form 990-PF (SOI Extract)")
        
        # Add processing notes
        profile.add_processing_note("Filtered from BMF/SOI integrated database")
        
        # Add foundation-specific processing notes
        if foundation_code:
            profile.add_processing_note(f"Foundation Code: {foundation_code} ({foundation_type.value})")
            if foundation_code == '03':
                profile.add_processing_note("PRIORITY: Private Non-Operating Foundation (990-PF) - High Grant Research Value")
        
        # Add financial analysis notes
        if org_data.get('total_expenses_990') or org_data.get('pf_total_expenses'):
            expenses = org_data.get('total_expenses_990') or org_data.get('pf_total_expenses')
            if revenue and expenses:
                efficiency_ratio = (revenue - expenses) / revenue if revenue > 0 else 0
                profile.add_processing_note(f"Financial Efficiency Ratio: {efficiency_ratio:.2%}")
        
        # Add program service revenue information for 990 filers
        if org_data.get('program_service_revenue_990'):
            psr = org_data['program_service_revenue_990']
            if revenue and psr:
                psr_ratio = psr / revenue
                profile.add_processing_note(f"Program Service Revenue: {psr_ratio:.1%} of total revenue")
        
        # Add additional data as processing notes
        if org_data.get('classification'):
            profile.add_processing_note(f"IRS Classification: {org_data['classification']}")
        if org_data.get('activity_code'):
            profile.add_processing_note(f"Activity Code: {org_data['activity_code']}")
        
        return profile
    
    def _classify_foundation_type(self, foundation_code: str) -> FoundationType:
        """
        Classify foundation type based on IRS Foundation Code.
        
        Foundation Codes:
        03 = Private Non-Operating Foundation (990-PF) - PRIMARY TARGET
        04 = Private Operating Foundation (990-PF) 
        12 = Supporting Organization
        15 = Donor Advised Fund
        """
        if not foundation_code:
            return FoundationType.UNKNOWN
        
        code_mapping = {
            '03': FoundationType.PRIVATE_NON_OPERATING,  # Primary target - 990-PF
            '04': FoundationType.PRIVATE_OPERATING,      # 990-PF
            '12': FoundationType.SUPPORTING_ORGANIZATION,
            '15': FoundationType.DONOR_ADVISED_FUND
        }
        
        return code_mapping.get(foundation_code, FoundationType.PUBLIC_CHARITY)
    
    def _determine_form_type(self, foundation_code: str) -> FormType:
        """
        Determine IRS form type based on Foundation Code.
        
        Returns:
            FormType enum indicating expected form type
        """
        if not foundation_code:
            return FormType.UNKNOWN
        
        # Foundation codes 03 and 04 typically file 990-PF
        if foundation_code in ['03', '04']:
            return FormType.FORM_990_PF
        
        # Most others file regular 990
        return FormType.FORM_990
    
    def _prioritize_foundation_results(self, organizations: List[OrganizationProfile]) -> List[OrganizationProfile]:
        """
        Sort organizations to prioritize private foundations by research value.
        
        Priority order:
        1. Foundation Code 03 (Private Non-Operating) - Highest value for grant research
        2. Foundation Code 04 (Private Operating) 
        3. Other foundation codes
        4. Regular nonprofits
        
        Within each category, sort by assets (descending) then revenue (descending)
        """
        def priority_key(org):
            # Primary sort: Foundation priority (lower number = higher priority)
            foundation_priority = {
                '03': 1,  # Private Non-Operating - Primary target
                '04': 2,  # Private Operating 
                '12': 3,  # Supporting Organization
                '15': 4,  # Donor Advised Fund
            }.get(getattr(org, 'foundation_code', None), 5)  # Everything else
            
            # Secondary sort: Assets (descending, None = 0)
            assets = -(org.assets or 0)
            
            # Tertiary sort: Revenue (descending, None = 0) 
            revenue = -(org.revenue or 0)
            
            return (foundation_priority, assets, revenue)
        
        return sorted(organizations, key=priority_key)
    
    async def _query_database(self, config: ProcessorConfig) -> List[OrganizationProfile]:
        """
        Query the SQLite database for matching organizations.
        
        Args:
            config: Processor configuration
            
        Returns:
            List of matching organization profiles
        """
        matching_orgs = []
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Build SQL query based on criteria
            workflow_config = config.workflow_config
            
            # Base query with LEFT JOINs to get enriched data (using correct column names)
            query = """
                SELECT 
                    b.ein, b.name, b.city, b.state, b.ntee_code, b.income_amt as revenue, b.asset_amt as assets,
                    b.classification, b.foundation_code, b.organization_code, b.subsection,
                    b.asset_cd, b.income_cd,
                    f990.totrevenue as total_revenue, f990.totfuncexpns as total_expenses, f990.totassetsend as net_assets, 
                    f990.totcntrbgfts as contributions, f990.prgmservrevnue as program_service_revenue,
                    f990pf.totrcptperbks as pf_total_revenue, f990pf.totexpnspbks as pf_total_expenses,
                    f990pf.totassetsend as pf_net_assets, f990pf.grscontrgifts as pf_contributions
                FROM bmf_organizations b
                LEFT JOIN form_990 f990 ON b.ein = f990.ein
                LEFT JOIN form_990pf f990pf ON b.ein = f990pf.ein
                WHERE 1=1
            """
            
            params = []
            
            # Add NTEE code filter
            if workflow_config.ntee_codes:
                ntee_conditions = []
                for ntee_code in workflow_config.ntee_codes:
                    ntee_conditions.append("b.ntee_code LIKE ?")
                    params.append(f"{ntee_code}%")
                query += f" AND ({' OR '.join(ntee_conditions)})"
            
            # Add state filter
            all_states = workflow_config.get_all_states()
            if all_states:
                state_placeholders = ','.join(['?'] * len(all_states))
                query += f" AND b.state IN ({state_placeholders})"
                params.extend(all_states)
            
            # Add ORDER BY for prioritizing foundations and larger organizations
            query += """
                ORDER BY 
                    CASE 
                        WHEN b.foundation_code = '03' THEN 1
                        WHEN b.foundation_code = '04' THEN 2
                        WHEN b.foundation_code IN ('12', '15') THEN 3
                        ELSE 4
                    END,
                    COALESCE(b.asset_amt, f990.totassetsend, f990pf.totassetsend, 0) DESC,
                    COALESCE(b.income_amt, f990.totrevenue, f990pf.totrcptperbks, 0) DESC
            """
            
            # Add LIMIT
            if config.workflow_config.max_results:
                query += " LIMIT ?"
                params.append(config.workflow_config.max_results)
            
            self.logger.info(f"Executing BMF query with {len(params)} parameters")
            
            # Execute query
            cursor.execute(query, params)
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Process results
            processed_records = 0
            for row in cursor.fetchall():
                processed_records += 1
                
                # Update progress periodically
                if processed_records % 100 == 0:
                    self._update_progress(
                        processed_records, 
                        config.workflow_config.max_results or 1000, 
                        f"Processed {processed_records} database records"
                    )
                    await asyncio.sleep(0)  # Yield control
                
                # Check for cancellation
                if self.is_cancelled():
                    self.logger.info("Database query processing cancelled")
                    break
                
                # Parse record
                org_data = self._parse_database_record(row, columns)
                if not org_data:
                    continue
                
                # Check if matches criteria (mainly for validation)
                if self._matches_criteria(org_data, config):
                    profile = self._create_organization_profile(org_data)
                    matching_orgs.append(profile)
            
            conn.close()
            
        except sqlite3.Error as db_error:
            self.logger.error(f"Database error: {db_error}")
            raise ValueError(f"Database query failed: {db_error}")
        except Exception as e:
            self.logger.error(f"Unexpected error querying database: {e}")
            raise ValueError(f"Database processing failed: {e}")
        
        # Sort results to prioritize Foundation Code 03 (Private Non-Operating Foundations)
        matching_orgs = self._prioritize_foundation_results(matching_orgs)
        
        self.logger.info(f"BMF filtering complete: {len(matching_orgs)} organizations found")
        foundation_03_count = sum(1 for org in matching_orgs if getattr(org, 'foundation_code', None) == '03')
        if foundation_03_count > 0:
            self.logger.info(f"Found {foundation_03_count} Private Non-Operating Foundations (990-PF) - prioritized for grant research")
        
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
            self.logger.info("Starting BMF filtering process with timeout protection")
            
            # Step 1: Check database availability
            self._update_progress(1, 4, "Checking BMF/SOI database")
            if not self._check_database_exists():
                raise ValueError("BMF/SOI database not found - please run ETL process first")
            
            # Step 2: Query database with timeout
            self._update_progress(2, 4, "Querying BMF/SOI database")
            try:
                matching_orgs = await asyncio.wait_for(
                    self._query_database(config),
                    timeout=self.max_processing_time
                )
            except asyncio.TimeoutError:
                self.logger.error(f"Database query timed out after {self.max_processing_time} seconds")
                raise ValueError(f"Database query timed out after {self.max_processing_time} seconds")
            
            # Step 3: Web validation (if enabled)
            if config.get_config("enable_web_validation", self.enable_web_validation):
                self._update_progress(3, 5, f"Validating web presence for {len(matching_orgs)} organizations")
                matching_orgs = await self._validate_web_presence(matching_orgs, config)
                self.logger.info(f"Web validation completed: {len(matching_orgs)} organizations with validated presence")
            
            # Step 4: Store results
            self._update_progress(4, 5, f"Found {len(matching_orgs)} matching organizations")
            
            # Convert to dictionaries for storage
            org_dicts = [org.dict() for org in matching_orgs]
            
            result.add_data("organizations", org_dicts)
            result.add_data("organizations_count", len(matching_orgs))
            result.add_data("database_path", str(self.db_path))
            
            # Add metadata
            result.add_metadata("bmf_source", "SQLite Database with BMF and SOI data")
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

    async def _validate_web_presence(
        self, 
        organizations: List[OrganizationProfile], 
        config: ProcessorConfig
    ) -> List[OrganizationProfile]:
        """Validate web presence for organizations and filter out inactive ones."""
        try:
            validated_orgs = []
            max_validations = config.get_config("max_web_validations", self.max_web_validations_per_run)
            
            # Limit validations to avoid overwhelming the system
            orgs_to_validate = organizations[:max_validations]
            remaining_orgs = organizations[max_validations:]
            
            self.logger.info(f"Web validating {len(orgs_to_validate)} organizations, {len(remaining_orgs)} will be included without validation")
            
            # Process in batches to avoid overwhelming servers
            for i in range(0, len(orgs_to_validate), self.web_validation_batch_size):
                batch = orgs_to_validate[i:i + self.web_validation_batch_size]
                batch_results = await self._validate_batch_web_presence(batch)
                validated_orgs.extend(batch_results)
                
                # Rate limiting between batches
                if i + self.web_validation_batch_size < len(orgs_to_validate):
                    await asyncio.sleep(self.web_validation_delay)
            
            # Add remaining organizations without validation
            validated_orgs.extend(remaining_orgs)
            
            # Log validation statistics
            validated_count = len([org for org in validated_orgs if hasattr(org, 'web_validation_status')])
            active_count = len([org for org in validated_orgs 
                              if getattr(org, 'web_validation_status', None) == 'active'])
            
            self.logger.info(f"Web validation: {validated_count} checked, {active_count} active, {len(validated_orgs)} total organizations")
            
            return validated_orgs
            
        except Exception as e:
            self.logger.warning(f"Web validation failed: {e}. Returning original organizations.")
            return organizations

    async def _validate_batch_web_presence(self, batch: List[OrganizationProfile]) -> List[OrganizationProfile]:
        """Validate web presence for a batch of organizations."""
        validated_batch = []
        
        # Get or predict URLs for organizations
        url_tasks = []
        for org in batch:
            url_tasks.append(self._get_or_predict_organization_url(org))
        
        try:
            urls = await asyncio.gather(*url_tasks, return_exceptions=True)
            
            # Validate each URL
            validation_tasks = []
            for i, org in enumerate(batch):
                url = urls[i] if not isinstance(urls[i], Exception) else None
                if url:
                    validation_tasks.append(self._validate_single_url(org, url))
                else:
                    # No URL available, mark as unknown
                    org.web_validation_status = 'no_url'
                    org.web_validation_date = datetime.now()
                    validation_tasks.append(asyncio.create_task(self._return_org_unchanged(org)))
            
            validated_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            for result in validated_results:
                if not isinstance(result, Exception) and result:
                    validated_batch.append(result)
            
            return validated_batch
            
        except Exception as e:
            self.logger.warning(f"Batch validation error: {e}")
            return batch

    async def _get_or_predict_organization_url(self, org: OrganizationProfile) -> Optional[str]:
        """Get cached URL or predict one for the organization."""
        try:
            # Check if URL is already cached
            with sqlite3.connect(self.catalynx_db_path) as conn:
                cursor = conn.execute("""
                    SELECT predicted_url, url_status, last_verified
                    FROM organization_urls 
                    WHERE ein = ? OR organization_name LIKE ?
                """, (org.ein, f"%{org.name}%"))
                
                result = cursor.fetchone()
                if result:
                    predicted_url, url_status, last_verified = result
                    
                    # Use cached URL if it's verified or recent
                    if url_status == 'verified':
                        return predicted_url
                    elif url_status == 'pending' and last_verified:
                        # Check if cache is recent (within 7 days)
                        last_verified_date = datetime.fromisoformat(last_verified)
                        if (datetime.now() - last_verified_date).days < 7:
                            return predicted_url
            
            # Predict URL using simple heuristics (could be enhanced with GPT integration)
            predicted_url = self._predict_organization_url(org)
            
            # Cache the prediction
            if predicted_url:
                await self._cache_predicted_url(org, predicted_url)
            
            return predicted_url
            
        except Exception as e:
            self.logger.debug(f"URL prediction failed for {org.name}: {e}")
            return None

    def _predict_organization_url(self, org: OrganizationProfile) -> Optional[str]:
        """Predict organization URL using simple heuristics."""
        try:
            if not org.name:
                return None
            
            # Clean organization name for URL prediction
            clean_name = org.name.lower()
            clean_name = clean_name.replace(' ', '').replace('-', '').replace('_', '')
            clean_name = ''.join(c for c in clean_name if c.isalnum())
            
            # Remove common nonprofit suffixes
            suffixes_to_remove = ['inc', 'org', 'foundation', 'fund', 'trust', 'corp', 'ltd']
            for suffix in suffixes_to_remove:
                if clean_name.endswith(suffix):
                    clean_name = clean_name[:-len(suffix)]
            
            # Common URL patterns for nonprofits
            url_patterns = [
                f"https://www.{clean_name}.org",
                f"https://{clean_name}.org",
                f"https://www.{clean_name}.com", 
                f"https://{clean_name}.com"
            ]
            
            return url_patterns[0]  # Return most likely pattern
            
        except Exception:
            return None

    async def _cache_predicted_url(self, org: OrganizationProfile, url: str):
        """Cache predicted URL for future use."""
        try:
            with sqlite3.connect(self.catalynx_db_path) as conn:
                # Ensure organization_urls table exists with compatible schema
                conn.execute("""
                    INSERT OR REPLACE INTO organization_urls 
                    (ein, organization_name, predicted_url, url_status, discovery_method, 
                     discovery_date, verification_attempts, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ein) DO UPDATE SET
                        predicted_url = excluded.predicted_url,
                        url_status = excluded.url_status,
                        updated_at = excluded.updated_at
                """, (
                    org.ein,
                    org.name,
                    url,
                    'pending',
                    'heuristic_prediction',
                    datetime.now().isoformat(),
                    0,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            self.logger.debug(f"Failed to cache predicted URL for {org.name}: {e}")

    async def _validate_single_url(self, org: OrganizationProfile, url: str) -> OrganizationProfile:
        """Validate a single organization URL."""
        try:
            # Try to fetch the URL with a short timeout
            result = await self.mcp_client.fetch_url(url, max_length=2000)
            
            if result.success and result.status_code and 200 <= result.status_code < 400:
                # URL is active
                org.web_validation_status = 'active'
                org.web_validation_url = url
                org.web_validation_date = datetime.now()
                org.web_validation_details = {
                    'status_code': result.status_code,
                    'title': result.title[:100] if result.title else None,
                    'content_length': len(result.content) if result.content else 0
                }
                
                # Update cache with verification
                await self._update_url_verification(org.ein, url, 'verified', result.status_code)
                
            else:
                # URL is not accessible
                org.web_validation_status = 'inactive'
                org.web_validation_url = url
                org.web_validation_date = datetime.now()
                org.web_validation_details = {
                    'status_code': result.status_code if result.status_code else 'timeout',
                    'error': 'URL not accessible'
                }
                
                # Update cache with failed verification
                await self._update_url_verification(org.ein, url, 'failed', 
                                                  result.status_code if result.status_code else 0)
            
            return org
            
        except Exception as e:
            # Validation error - keep organization but mark as unknown
            org.web_validation_status = 'error'
            org.web_validation_url = url
            org.web_validation_date = datetime.now()
            org.web_validation_details = {'error': str(e)}
            
            return org

    async def _update_url_verification(self, ein: str, url: str, status: str, status_code: int):
        """Update URL verification status in cache."""
        try:
            with sqlite3.connect(self.catalynx_db_path) as conn:
                conn.execute("""
                    UPDATE organization_urls 
                    SET url_status = ?, 
                        http_status_code = ?, 
                        last_verified = ?,
                        verification_attempts = verification_attempts + 1,
                        updated_at = ?
                    WHERE ein = ?
                """, (
                    status,
                    status_code,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    ein
                ))
                conn.commit()
        except Exception as e:
            self.logger.debug(f"Failed to update URL verification for {ein}: {e}")

    async def _return_org_unchanged(self, org: OrganizationProfile) -> OrganizationProfile:
        """Helper method to return organization unchanged (for async compatibility)."""
        return org
    
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