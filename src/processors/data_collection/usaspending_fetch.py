#!/usr/bin/env python3
"""
USASpending.gov Fetch Processor
Fetches historical award data from USASpending.gov API.

This processor:
1. Takes organizations from previous steps (BMF filter, ProPublica)
2. Queries USASpending.gov API for historical federal awards by EIN
3. Analyzes funding track record and success patterns
4. Calculates success probability scores for government grants
5. Returns enriched organization profiles with funding history
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import time
import logging

from src.core.base_processor import BaseProcessor, ProcessorMetadata, SyncProcessorMixin
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.core.government_models import HistoricalAward, OrganizationAwardHistory
from src.clients.usaspending_client import USASpendingClient


class USASpendingFetchProcessor(BaseProcessor, SyncProcessorMixin):
    """Processor for fetching historical award data from USASpending.gov API."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="usaspending_fetch", 
            description="Fetch historical federal award data from USASpending.gov API",
            version="2.0.0",  # Upgraded to use new client architecture
            dependencies=[],  # Optional dependencies - can run standalone for testing
            estimated_duration=180,  # 3 minutes for typical dataset
            requires_network=True,
            requires_api_key=False,  # USASpending.gov is free, no API key required
            processor_type="data_collection"
        )
        super().__init__(metadata)
        
        # Initialize API client
        self.usaspending_client = USASpendingClient()
        
        # Processing limits
        self.max_requests_per_second = 5  # Conservative rate limit
        self.request_delay = 0.2  # 200ms between requests
        
        # Search configuration
        self.max_awards_per_org = 100
        self.award_lookback_years = 5
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute USASpending historical data fetch."""
        start_time = time.time()
        
        try:
            # Get organizations from previous steps
            organizations = await self._get_input_organizations(config, workflow_state)
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No organizations found from previous steps"]
                )
            
            self.logger.info(f"Fetching USASpending data for {len(organizations)} organizations")
            
            # Process organizations with rate limiting using new client
            enriched_organizations = []
            award_histories = []
            failed_eins = []
            
            for i, org in enumerate(organizations):
                try:
                    self._update_progress(i + 1, len(organizations), f"Processing {org.name}")
                    
                    # Rate limiting delay
                    if i > 0:
                        await asyncio.sleep(self.request_delay)
                    
                    # Fetch award history for organization using the client
                    award_history = await self._fetch_organization_awards(org)
                    if award_history and award_history.awards:
                        award_histories.append(award_history)
                        
                        # Enrich organization with award history
                        enriched_org = await self._enrich_organization_with_awards(org, award_history)
                        enriched_organizations.append(enriched_org)
                    else:
                        # No awards found, but still include organization
                        enriched_organizations.append(org)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to process organization {org.ein}: {e}")
                    failed_eins.append(org.ein)
                    enriched_organizations.append(org)  # Include without enrichment
                    continue
            
            execution_time = time.time() - start_time
            
            # Calculate summary statistics
            total_awards = sum(len(history.awards) for history in award_histories)
            total_funding = sum(history.total_award_amount for history in award_histories)
            orgs_with_awards = len([h for h in award_histories if h.awards])
            
            # Prepare results
            result_data = {
                "organizations": [org.dict() for org in enriched_organizations],
                "award_histories": [history.dict() for history in award_histories],
                "total_processed": len(organizations),
                "organizations_with_awards": orgs_with_awards,
                "total_awards_found": total_awards,
                "total_funding_found": total_funding,
                "failed_fetches": len(failed_eins)
            }
            
            warnings = []
            if failed_eins:
                warnings.append(f"Failed to fetch data for {len(failed_eins)} organizations")
            if orgs_with_awards == 0:
                warnings.append("No federal award history found for any organizations")
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                warnings=warnings,
                metadata={
                    "api_source": "USASpending.gov",
                    "rate_limit": self.max_requests_per_second,
                    "lookback_years": self.award_lookback_years,
                    "failed_eins": failed_eins[:10]  # First 10 failed EINs
                }
            )
            
        except Exception as e:
            self.logger.error(f"USASpending fetch failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"USASpending fetch failed: {str(e)}"]
            )
    
    async def _get_input_organizations(self, config: ProcessorConfig, workflow_state) -> List[OrganizationProfile]:
        """Get organizations from previous steps."""
        try:
            organizations = []
            
            # Try to get from ProPublica fetch first (more detailed data)
            if workflow_state and workflow_state.has_processor_succeeded('propublica_fetch'):
                org_dicts = workflow_state.get_organizations_from_processor('propublica_fetch')
                if org_dicts:
                    self.logger.info(f"Retrieved {len(org_dicts)} organizations from ProPublica fetch")
                    for org_dict in org_dicts:
                        try:
                            if isinstance(org_dict, dict):
                                org = OrganizationProfile(**org_dict)
                            else:
                                org = org_dict
                            organizations.append(org)
                        except Exception as e:
                            self.logger.warning(f"Failed to parse organization data: {e}")
                            continue
                    return organizations
            
            # Fallback to BMF filter
            if workflow_state and workflow_state.has_processor_succeeded('bmf_filter'):
                org_dicts = workflow_state.get_organizations_from_processor('bmf_filter')
                if org_dicts:
                    self.logger.info(f"Retrieved {len(org_dicts)} organizations from BMF filter")
                    for org_dict in org_dicts:
                        try:
                            if isinstance(org_dict, dict):
                                org = OrganizationProfile(**org_dict)
                            else:
                                org = org_dict
                            organizations.append(org)
                        except Exception as e:
                            self.logger.warning(f"Failed to parse organization data: {e}")
                            continue
                    return organizations
            
            # If no previous data, use test data
            self.logger.warning("No previous processor data found - using test data")
            test_orgs = [
                OrganizationProfile(
                    ein="541669652",
                    name="FAMILY FORWARD FOUNDATION",
                    state="VA",
                    ntee_code="P81"
                )
            ]
            return test_orgs
            
        except Exception as e:
            self.logger.error(f"Failed to get input organizations: {e}")
            return []
    
    async def _fetch_organization_awards(
        self,
        org: OrganizationProfile
    ) -> Optional[OrganizationAwardHistory]:
        """Fetch historical awards for a single organization using the client."""
        
        try:
            # Use the client to search for awards by recipient EIN
            award_results = await self.usaspending_client.search_awards_by_recipient(
                recipient_ein=org.ein,
                max_results=self.max_awards_per_org,
                award_types=["02", "03", "04", "05"],  # Grant types only
                fiscal_year_start=datetime.now().year - self.award_lookback_years,
                fiscal_year_end=datetime.now().year
            )
            
            if not award_results:
                self.logger.debug(f"No award history found for {org.ein}")
                return OrganizationAwardHistory(ein=org.ein, name=org.name)
            
            # Parse awards
            awards = []
            for award_data in award_results:
                try:
                    award = self._parse_award_data(award_data, org)
                    if award:
                        awards.append(award)
                except Exception as e:
                    self.logger.warning(f"Failed to parse award data: {e}")
                    continue
            
            # Create award history object
            award_history = OrganizationAwardHistory(
                ein=org.ein,
                name=org.name,
                awards=awards
            )
            
            # Calculate statistics
            award_history.calculate_statistics()
            
            self.logger.info(f"Found {len(awards)} awards for {org.name} totaling ${award_history.total_award_amount:,.2f}")
            
            return award_history
                
        except Exception as e:
            self.logger.warning(f"Error fetching USASpending data for {org.ein}: {e}")
            return None
    
    def _get_time_period_filter(self) -> List[Dict[str, str]]:
        """Get time period filter for the last N years."""
        current_year = datetime.now().year
        start_year = current_year - self.award_lookback_years
        
        periods = []
        for year in range(start_year, current_year + 1):
            periods.append({
                "start_date": f"{year}-01-01",
                "end_date": f"{year}-12-31"
            })
        
        return periods
    
    def _parse_award_data(self, award_data: Dict[str, Any], org: OrganizationProfile) -> Optional[HistoricalAward]:
        """Parse award data from USASpending.gov API response."""
        try:
            # Extract required fields
            award_id = str(award_data.get("Award ID", ""))
            award_amount = self._safe_float(award_data.get("Award Amount", 0))
            
            if not award_id or award_amount is None:
                return None
            
            # Parse dates
            award_date = self._parse_date(award_data.get("Award Date"))
            start_date = self._parse_date(award_data.get("Start Date"))
            end_date = self._parse_date(award_data.get("End Date"))
            
            # Extract award details
            award_title = award_data.get("Award Description", "").strip()
            award_type = award_data.get("Award Type", "grant").lower()
            
            # Extract agency information
            agency_name = award_data.get("Awarding Agency", "").strip()
            sub_agency = award_data.get("Awarding Sub Agency", "").strip()
            
            # Extract CFDA information
            cfda_number = award_data.get("CFDA Number", "").strip()
            cfda_title = award_data.get("CFDA Title", "").strip()
            
            # Create award object
            award = HistoricalAward(
                award_id=award_id,
                award_title=award_title if award_title else None,
                award_amount=award_amount,
                award_type=award_type,
                cfda_number=cfda_number if cfda_number else None,
                cfda_title=cfda_title if cfda_title else None,
                start_date=start_date.date() if start_date else None,
                end_date=end_date.date() if end_date else None,
                action_date=award_date.date() if award_date else None,
                recipient_name=org.name,
                recipient_ein=org.ein,
                recipient_state=org.state,
                awarding_agency_code="",  # USASpending doesn't always provide codes
                awarding_agency_name=agency_name,
                awarding_sub_agency=sub_agency if sub_agency else None
            )
            
            return award
            
        except Exception as e:
            self.logger.warning(f"Error parsing award data: {e}")
            return None
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                # Remove currency symbols and commas
                cleaned = value.replace("$", "").replace(",", "").strip()
                return float(cleaned)
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        
        # Common USASpending date formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
            "%m/%d/%Y",
            "%m-%d-%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str).strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    async def _enrich_organization_with_awards(
        self,
        org: OrganizationProfile,
        award_history: OrganizationAwardHistory
    ) -> OrganizationProfile:
        """Enrich organization profile with award history data."""
        
        # Add funding track record scores
        org.component_scores["funding_track_record"] = award_history.funding_track_record_score
        org.component_scores["funding_diversity"] = award_history.funding_diversity_score
        
        # Add award summary to processing notes
        if award_history.awards:
            org.add_processing_note(
                f"Found {award_history.award_count} federal awards totaling ${award_history.total_award_amount:,.2f}"
            )
            
            # Add recent awards note
            recent_awards = award_history.get_recent_awards(1095)  # 3 years
            if recent_awards:
                recent_total = sum(award.award_amount for award in recent_awards)
                org.add_processing_note(
                    f"{len(recent_awards)} awards in last 3 years totaling ${recent_total:,.2f}"
                )
            
            # Add agency diversity note
            if len(award_history.unique_agencies) > 1:
                org.add_processing_note(
                    f"Awards from {len(award_history.unique_agencies)} different agencies: {', '.join(award_history.unique_agencies[:3])}"
                )
        else:
            org.add_processing_note("No federal award history found")
        
        # Add data source
        org.add_data_source("USASpending.gov")
        
        # Store raw award history for further analysis
        if hasattr(org, 'award_history'):
            org.award_history = award_history.dict()
        else:
            # Add as metadata if not directly supported
            org.component_scores["award_history"] = {
                "total_awards": award_history.award_count,
                "total_amount": award_history.total_award_amount,
                "unique_agencies": len(award_history.unique_agencies),
                "track_record_score": award_history.funding_track_record_score
            }
        
        return org


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return USASpendingFetchProcessor()