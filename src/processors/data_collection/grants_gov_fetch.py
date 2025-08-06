#!/usr/bin/env python3
"""
Grants.gov Fetch Processor
Fetches federal grant opportunities from Grants.gov API.

This processor:
1. Searches for active grant opportunities 
2. Filters by eligibility criteria (nonprofits)
3. Extracts opportunity details and deadlines
4. Handles API rate limiting and pagination
5. Returns standardized government opportunities
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
import logging
from urllib.parse import urlencode

from src.core.base_processor import BaseProcessor, ProcessorMetadata, SyncProcessorMixin
from src.core.data_models import ProcessorConfig, ProcessorResult
from src.core.government_models import (
    GovernmentOpportunity, OpportunityStatus, FundingInstrumentType, 
    EligibilityCategory, GovernmentOpportunityMatch
)
from src.auth.api_key_manager import get_api_key_manager


class GrantsGovFetchProcessor(BaseProcessor, SyncProcessorMixin):
    """Processor for fetching opportunities from Grants.gov API."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="grants_gov_fetch",
            description="Fetch federal grant opportunities from Grants.gov API",
            version="1.0.0",
            dependencies=[],  # No dependencies - this is a discovery processor
            estimated_duration=120,  # 2 minutes for typical search
            requires_network=True,
            requires_api_key=True,
            processor_type="data_collection"
        )
        super().__init__(metadata)
        
        # API Configuration
        self.base_url = "https://www.grants.gov/grantsws/rest"
        self.max_requests_per_hour = 1000  # Grants.gov rate limit
        self.request_delay = 3.6  # Seconds between requests
        self.max_retries = 3
        self.retry_delay = 5.0
        
        # Search defaults
        self.default_page_size = 25
        self.max_opportunities = 100
    
    def check_processor_api_requirements(self, config: ProcessorConfig) -> List[str]:
        """Check for Grants.gov API key requirement."""
        errors = []
        
        # Check for test mode
        if config.get_config("test_mode", False):
            return []  # Skip API key check in test mode
        
        manager = get_api_key_manager()
        
        if not manager.get_api_key("grants_gov"):
            # For now, we'll try to work without API key (some endpoints may be public)
            self.logger.warning("No Grants.gov API key found. Will attempt public access.")
        
        return errors
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute Grants.gov opportunity search."""
        start_time = time.time()
        
        try:
            self.logger.info("Starting Grants.gov opportunity search")
            
            # Get search parameters from config
            search_params = self._build_search_parameters(config)
            self.logger.info(f"Search parameters: {search_params}")
            
            # Perform search with pagination
            opportunities = []
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            ) as session:
                opportunities = await self._search_opportunities(session, search_params)
            
            if not opportunities:
                return ProcessorResult(
                    success=True,
                    processor_name=self.metadata.name,
                    execution_time=time.time() - start_time,
                    data={"opportunities": [], "total_found": 0},
                    warnings=["No opportunities found matching search criteria"]
                )
            
            self.logger.info(f"Found {len(opportunities)} opportunities")
            
            # Score and rank opportunities
            scored_opportunities = await self._score_opportunities(opportunities, config)
            
            # Prepare results
            result_data = {
                "opportunities": [opp.dict() for opp in scored_opportunities],
                "total_found": len(opportunities),
                "active_opportunities": len([o for o in opportunities if o.is_active()]),
                "nonprofit_eligible": len([o for o in opportunities if o.is_eligible_for_nonprofits()])
            }
            
            execution_time = time.time() - start_time
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "api_source": "Grants.gov",
                    "search_params": search_params,
                    "rate_limit": self.max_requests_per_hour
                }
            )
            
        except Exception as e:
            self.logger.error(f"Grants.gov fetch failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"Grants.gov fetch failed: {str(e)}"]
            )
    
    def _build_search_parameters(self, config: ProcessorConfig) -> Dict[str, Any]:
        """Build Grants.gov API search parameters."""
        params = {
            "oppStatus": "posted|forecasted",  # Active opportunities
            "eligibilities": "25",  # Code 25 = Nonprofits
            "sortBy": "openDate|desc",
            "rows": self.default_page_size,
            "startRecordNum": 0
        }
        
        # Add state filter if specified
        workflow_config = config.workflow_config
        if workflow_config.state_filter:
            # Note: Grants.gov uses state names, not codes
            state_name = self._state_code_to_name(workflow_config.state_filter)
            if state_name:
                params["eligibleStates"] = state_name
        
        # Add CFDA filter if available from configuration
        if hasattr(workflow_config, 'cfda_numbers') and workflow_config.cfda_numbers:
            params["cfdaNumbers"] = "|".join(workflow_config.cfda_numbers)
        
        # Add agency filter if specified
        processor_config = config.processor_specific_config
        if "agency_codes" in processor_config:
            params["agencies"] = "|".join(processor_config["agency_codes"])
        
        # Add funding amount filters
        if "min_award_amount" in processor_config:
            params["awardFloorFrom"] = processor_config["min_award_amount"]
        if "max_award_amount" in processor_config:
            params["awardCeilingTo"] = processor_config["max_award_amount"]
        
        return params
    
    async def _search_opportunities(
        self, 
        session: aiohttp.ClientSession, 
        search_params: Dict[str, Any]
    ) -> List[GovernmentOpportunity]:
        """Search for opportunities with pagination."""
        all_opportunities = []
        page_num = 0
        max_pages = (self.max_opportunities // self.default_page_size) + 1
        
        manager = get_api_key_manager()
        api_key = manager.get_api_key("grants_gov")
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Grant-Research-Automation/1.0"
        }
        
        # Add API key to headers if available
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        while page_num < max_pages and len(all_opportunities) < self.max_opportunities:
            try:
                # Update pagination parameters
                current_params = search_params.copy()
                current_params["startRecordNum"] = page_num * self.default_page_size
                
                # Build URL
                url = f"{self.base_url}/opportunities"
                query_string = urlencode(current_params, safe="|")
                full_url = f"{url}?{query_string}"
                
                self.logger.debug(f"Fetching page {page_num + 1}: {full_url}")
                
                # Rate limiting delay
                if page_num > 0:
                    await asyncio.sleep(self.request_delay)
                
                async with session.get(full_url, headers=headers) as response:
                    if response.status != 200:
                        self.logger.warning(f"API request failed with status {response.status}")
                        if response.status == 429:  # Rate limited
                            await asyncio.sleep(60)  # Wait 1 minute
                            continue
                        break
                    
                    data = await response.json()
                    opportunities_data = data.get("oppHits", [])
                    
                    if not opportunities_data:
                        self.logger.info("No more opportunities found")
                        break
                    
                    # Parse opportunities
                    page_opportunities = []
                    for opp_data in opportunities_data:
                        try:
                            opportunity = self._parse_opportunity(opp_data)
                            if opportunity:
                                page_opportunities.append(opportunity)
                        except Exception as e:
                            self.logger.warning(f"Failed to parse opportunity: {e}")
                            continue
                    
                    all_opportunities.extend(page_opportunities)
                    
                    self.logger.info(f"Page {page_num + 1}: Found {len(page_opportunities)} opportunities")
                    
                    # Check if we've reached the end
                    if len(opportunities_data) < self.default_page_size:
                        break
                    
                    page_num += 1
                    
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout on page {page_num + 1}")
                break
            except Exception as e:
                self.logger.error(f"Error fetching page {page_num + 1}: {e}")
                break
        
        return all_opportunities[:self.max_opportunities]
    
    def _parse_opportunity(self, opp_data: Dict[str, Any]) -> Optional[GovernmentOpportunity]:
        """Parse opportunity data from Grants.gov API response."""
        try:
            # Extract basic information
            opportunity_id = opp_data.get("id", "")
            opportunity_number = opp_data.get("number", "")
            title = opp_data.get("title", "").strip()
            description = opp_data.get("description", "").strip()
            
            if not opportunity_id or not title:
                return None
            
            # Parse status
            status_str = opp_data.get("oppStatus", "").lower()
            if "posted" in status_str:
                status = OpportunityStatus.POSTED
            elif "forecast" in status_str:
                status = OpportunityStatus.FORECASTED
            elif "closed" in status_str:
                status = OpportunityStatus.CLOSED
            else:
                status = OpportunityStatus.POSTED
            
            # Parse agency information
            agency_code = opp_data.get("agencyCode", "")
            agency_name = opp_data.get("agencyName", "")
            
            # Parse funding information
            award_ceiling = self._safe_float(opp_data.get("awardCeiling"))
            award_floor = self._safe_float(opp_data.get("awardFloor"))
            estimated_funding = self._safe_float(opp_data.get("estimatedTotalProgramFunding"))
            expected_awards = self._safe_int(opp_data.get("expectedAwards"))
            
            # Parse dates
            posted_date = self._parse_date(opp_data.get("postDate"))
            due_date = self._parse_date(opp_data.get("closeDate"))
            archive_date = self._parse_date(opp_data.get("archiveDate"))
            
            # Parse eligibility
            eligible_applicants = self._parse_eligibility(opp_data.get("eligibilityCodes", []))
            
            # Parse CFDA numbers
            cfda_numbers = []
            cfda_list = opp_data.get("cfdaNumbers", [])
            if isinstance(cfda_list, list):
                cfda_numbers = [str(cfda) for cfda in cfda_list if cfda]
            elif isinstance(cfda_list, str):
                cfda_numbers = [cfda_list] if cfda_list else []
            
            # Create opportunity object
            opportunity = GovernmentOpportunity(
                opportunity_id=opportunity_id,
                opportunity_number=opportunity_number,
                title=title,
                description=description,
                agency_code=agency_code,
                agency_name=agency_name,
                status=status,
                funding_instrument_type=FundingInstrumentType.GRANT,
                cfda_numbers=cfda_numbers,
                estimated_total_funding=estimated_funding,
                award_ceiling=award_ceiling,
                award_floor=award_floor,
                expected_number_of_awards=expected_awards,
                posted_date=posted_date,
                application_due_date=due_date,
                archive_date=archive_date,
                eligible_applicants=eligible_applicants,
                grants_gov_url=f"https://www.grants.gov/web/grants/view-opportunity.html?oppId={opportunity_id}"
            )
            
            opportunity.add_processing_note("Parsed from Grants.gov API")
            return opportunity
            
        except Exception as e:
            self.logger.warning(f"Error parsing opportunity data: {e}")
            return None
    
    def _parse_eligibility(self, eligibility_codes: List[Any]) -> List[EligibilityCategory]:
        """Parse eligibility codes to categories."""
        eligible_applicants = []
        
        # Grants.gov eligibility code mappings
        code_mapping = {
            "25": EligibilityCategory.NONPROFIT,
            "00": EligibilityCategory.STATE_GOVERNMENT,
            "01": EligibilityCategory.LOCAL_GOVERNMENT,
            "02": EligibilityCategory.TRIBAL_GOVERNMENT,
            "05": EligibilityCategory.UNIVERSITY,
            "20": EligibilityCategory.FOR_PROFIT,
            "22": EligibilityCategory.INDIVIDUAL
        }
        
        for code in eligibility_codes:
            code_str = str(code).strip()
            if code_str in code_mapping:
                category = code_mapping[code_str]
                if category not in eligible_applicants:
                    eligible_applicants.append(category)
        
        return eligible_applicants
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int."""
        if value is None:
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        
        # Common Grants.gov date formats
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%m-%d-%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        self.logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _state_code_to_name(self, state_code: str) -> Optional[str]:
        """Convert state code to state name for Grants.gov API."""
        state_mapping = {
            "VA": "Virginia", "MD": "Maryland", "DC": "District of Columbia",
            "NC": "North Carolina", "SC": "South Carolina", "WV": "West Virginia",
            "DE": "Delaware", "PA": "Pennsylvania", "NJ": "New Jersey",
            # Add more mappings as needed
        }
        return state_mapping.get(state_code.upper())
    
    async def _score_opportunities(
        self, 
        opportunities: List[GovernmentOpportunity],
        config: ProcessorConfig
    ) -> List[GovernmentOpportunity]:
        """Score and rank opportunities for relevance."""
        
        for opportunity in opportunities:
            score = 0.0
            
            # Base score for nonprofit eligibility
            if opportunity.is_eligible_for_nonprofits():
                score += 0.3
            
            # Timing score (closer deadlines get higher priority)
            days_until_deadline = opportunity.calculate_days_until_deadline()
            if days_until_deadline is not None:
                if days_until_deadline >= 30:
                    score += 0.2
                elif days_until_deadline >= 14:
                    score += 0.15
                elif days_until_deadline >= 7:
                    score += 0.1
            
            # Status score
            if opportunity.status == OpportunityStatus.POSTED:
                score += 0.2
            elif opportunity.status == OpportunityStatus.FORECASTED:
                score += 0.1
            
            # Funding amount score
            if opportunity.award_ceiling:
                if opportunity.award_ceiling >= 1_000_000:
                    score += 0.1
                elif opportunity.award_ceiling >= 100_000:
                    score += 0.05
            
            # Geographic eligibility score
            workflow_config = config.workflow_config
            if workflow_config.state_filter and opportunity.matches_state(workflow_config.state_filter):
                score += 0.2
            
            opportunity.relevance_score = min(1.0, score)
            
            # Add match reasons
            if opportunity.is_eligible_for_nonprofits():
                opportunity.match_reasons.append("Nonprofit eligible")
            if opportunity.is_active():
                opportunity.match_reasons.append("Currently active")
            if days_until_deadline and days_until_deadline >= 30:
                opportunity.match_reasons.append("Adequate time to apply")
        
        # Sort by relevance score
        opportunities.sort(key=lambda x: x.relevance_score, reverse=True)
        return opportunities


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return GrantsGovFetchProcessor()