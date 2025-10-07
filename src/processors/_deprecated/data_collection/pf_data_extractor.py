#!/usr/bin/env python3
"""
990-PF Data Extractor Processor
Specialized processor for extracting private foundation data from 990-PF forms.

This processor focuses on the key sections that make private foundations valuable for grant research:
- Part XV: Grants and Contributions (enhanced grantee information) 
- Part VIII: Officers, Directors, Trustees (decision maker information)
- Part I: Financial Summary (investment income, grant-making capacity)
- Part XVI: Analysis of Income-Producing Activities (program areas)
"""

import asyncio
import aiohttp
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import time
import logging

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.profiles.models import (
    FoundationGrantRecord, FoundationBoardMember, FoundationFinancialData,
    FoundationProgramAreas, FoundationApplicationProcess, ApplicationAcceptanceStatus,
    FormType, FoundationType
)


class PFDataExtractorProcessor(BaseProcessor):
    """Processor for extracting 990-PF specific data from ProPublica and IRS sources."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="pf_data_extractor",
            description="Extract 990-PF specific data including grants, board members, and application processes",
            version="1.0.0",
            dependencies=["propublica_fetch"],  # Runs after ProPublica data fetch
            estimated_duration=240,  # 4 minutes for detailed PF analysis
            requires_network=True,
            requires_api_key=False
        )
        super().__init__(metadata)
        
        # Rate limiting for ProPublica API
        self.max_requests_per_second = 8
        self.request_delay = 1.0 / self.max_requests_per_second
        
        # ProPublica API endpoints
        self.base_url = "https://projects.propublica.org/nonprofits/api/v2"
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute 990-PF data extraction."""
        start_time = time.time()
        
        try:
            # Get organizations from previous step
            organizations = await self._get_input_organizations(config, workflow_state)
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No organizations found from previous step"]
                )
            
            # Filter for 990-PF organizations only
            pf_organizations = [
                org for org in organizations 
                if org.form_type == FormType.FORM_990_PF or org.foundation_code in ['03', '04']
            ]
            
            if not pf_organizations:
                self.logger.info("No 990-PF organizations found - skipping PF data extraction")
                return ProcessorResult(
                    success=True,
                    processor_name=self.metadata.name,
                    data={"organizations": [org.dict() for org in organizations]},
                    metadata={"pf_organizations_processed": 0}
                )
            
            self.logger.info(f"Processing 990-PF data for {len(pf_organizations)} private foundations")
            
            # Process each 990-PF organization
            enriched_organizations = []
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                for i, org in enumerate(pf_organizations):
                    try:
                        self._update_progress(i + 1, len(pf_organizations), f"Processing PF data for {org.name}")
                        
                        # Rate limiting
                        if i > 0:
                            await asyncio.sleep(self.request_delay)
                        
                        # Extract 990-PF specific data
                        enriched_org = await self._extract_pf_data(session, org)
                        if enriched_org:
                            enriched_organizations.append(enriched_org)
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to process PF data for {org.ein}: {e}")
                        enriched_organizations.append(org)  # Keep original if extraction fails
                        continue
            
            # Add non-PF organizations unchanged
            for org in organizations:
                if org not in pf_organizations:
                    enriched_organizations.append(org)
            
            execution_time = time.time() - start_time
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data={
                    "organizations": [org.dict() for org in enriched_organizations],
                    "total_processed": len(organizations),
                    "pf_organizations_processed": len(pf_organizations)
                },
                metadata={
                    "pf_count": len(pf_organizations),
                    "total_count": len(enriched_organizations)
                }
            )
            
        except Exception as e:
            self.logger.error(f"PF data extraction failed: {e}")
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                errors=[str(e)]
            )
    
    async def _get_input_organizations(self, config: ProcessorConfig, workflow_state) -> List[OrganizationProfile]:
        """Get organizations from previous processing step."""
        if not workflow_state:
            return []
        
        try:
            # Look for organizations from ProPublica fetch or BMF filter
            for step_name in ["propublica_fetch", "bmf_filter"]:
                if step_name in workflow_state.step_results:
                    step_data = workflow_state.step_results[step_name]
                    if "organizations" in step_data.data:
                        org_dicts = step_data.data["organizations"]
                        organizations = [OrganizationProfile(**org_dict) for org_dict in org_dicts]
                        return organizations
            
            return []
        except Exception as e:
            self.logger.error(f"Failed to get input organizations: {e}")
            return []
    
    async def _extract_pf_data(self, session: aiohttp.ClientSession, org: OrganizationProfile) -> Optional[OrganizationProfile]:
        """Extract detailed 990-PF data for a single organization."""
        
        try:
            # Get organization ID from ProPublica
            org_id = await self._get_propublica_org_id(session, org.ein)
            if not org_id:
                self.logger.info(f"No ProPublica data found for PF {org.ein}")
                return org
            
            # Fetch detailed organization data
            detail_url = f"{self.base_url}/organizations/{org_id}.json"
            
            async with session.get(detail_url) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to fetch PF details for {org.ein}: HTTP {response.status}")
                    return org
                
                detail_data = await response.json()
                
                # Extract 990-PF specific data
                enriched_org = await self._enrich_with_pf_data(org, detail_data)
                
                # Fetch XML data for detailed Part XV analysis
                xml_data = await self._fetch_latest_xml_data(session, org_id)
                if xml_data:
                    enriched_org = await self._extract_xml_pf_data(enriched_org, xml_data)
                
                return enriched_org
                
        except Exception as e:
            self.logger.warning(f"Error extracting PF data for {org.ein}: {e}")
            return org
    
    async def _get_propublica_org_id(self, session: aiohttp.ClientSession, ein: str) -> Optional[str]:
        """Get ProPublica organization ID for an EIN."""
        
        try:
            search_url = f"{self.base_url}/search.json"
            params = {"q": ein}
            
            async with session.get(search_url, params=params) as response:
                if response.status != 200:
                    return None
                
                search_data = await response.json()
                organizations = search_data.get('organizations', [])
                
                if organizations:
                    return organizations[0].get('id')
                
        except Exception as e:
            self.logger.debug(f"Error searching for org ID {ein}: {e}")
        
        return None
    
    async def _enrich_with_pf_data(self, org: OrganizationProfile, pp_data: Dict[str, Any]) -> OrganizationProfile:
        """Enrich organization with 990-PF specific data from ProPublica JSON."""
        
        organization = pp_data.get('organization', {})
        filings = pp_data.get('filings_with_data', [])
        
        if not filings:
            return org
        
        # Get most recent 990-PF filing
        pf_filing = None
        for filing in filings:
            if filing.get('formtype') in ['990PF', '990-PF']:
                pf_filing = filing
                break
        
        if not pf_filing:
            return org
        
        # Extract Part I - Financial Information
        financial_data = self._extract_part_i_financial_data(pf_filing)
        if financial_data:
            org.foundation_financial_data = financial_data
        
        # Extract basic board information if available
        board_members = self._extract_basic_board_data(pf_filing)
        if board_members:
            org.foundation_board_members = board_members
        
        # Update form type confirmation
        org.form_type = FormType.FORM_990_PF
        
        return org
    
    def _extract_part_i_financial_data(self, filing: Dict[str, Any]) -> Optional[FoundationFinancialData]:
        """Extract Part I financial data from 990-PF filing."""
        
        try:
            return FoundationFinancialData(
                investment_income=self._safe_float(filing.get('totinvstinc')),
                capital_gains=self._safe_float(filing.get('totcapgn')),
                total_revenue=self._safe_float(filing.get('totrevenue')),
                total_assets_beginning=self._safe_float(filing.get('totassetsboy')),
                total_assets_end=self._safe_float(filing.get('totassetsend')),
                grants_paid=self._safe_float(filing.get('totgrntstoindv')) or self._safe_float(filing.get('totgrntsto')),
                qualifying_distributions=self._safe_float(filing.get('qlfydistrib')),
                minimum_investment_return=self._safe_float(filing.get('mininvstret')),
                distributable_amount=self._safe_float(filing.get('distribamt'))
            )
        except Exception as e:
            self.logger.debug(f"Error extracting Part I financial data: {e}")
            return None
    
    def _extract_basic_board_data(self, filing: Dict[str, Any]) -> List[FoundationBoardMember]:
        """Extract basic board member information from JSON filing data."""
        
        board_members = []
        
        # Look for officer/director information in various possible fields
        officer_fields = ['officers', 'directors', 'trustees', 'officerdir']
        
        for field in officer_fields:
            if field in filing and isinstance(filing[field], list):
                for member_data in filing[field]:
                    if isinstance(member_data, dict):
                        board_member = self._parse_board_member(member_data)
                        if board_member:
                            board_members.append(board_member)
        
        return board_members
    
    def _parse_board_member(self, member_data: Dict[str, Any]) -> Optional[FoundationBoardMember]:
        """Parse individual board member data."""
        
        try:
            name = member_data.get('name', '').strip()
            if not name:
                return None
            
            return FoundationBoardMember(
                name=name,
                title=member_data.get('title', '').strip(),
                average_hours_per_week=self._safe_float(member_data.get('hours')),
                compensation=self._safe_float(member_data.get('compensation')),
                is_officer='officer' in member_data.get('title', '').lower(),
                is_director='director' in member_data.get('title', '').lower() or 'trustee' in member_data.get('title', '').lower()
            )
        except Exception as e:
            self.logger.debug(f"Error parsing board member: {e}")
            return None
    
    async def _fetch_latest_xml_data(self, session: aiohttp.ClientSession, org_id: str) -> Optional[str]:
        """Fetch the latest XML filing data for detailed analysis."""
        
        try:
            # Get list of filings
            filings_url = f"{self.base_url}/organizations/{org_id}/filings.json"
            
            async with session.get(filings_url) as response:
                if response.status != 200:
                    return None
                
                filings_data = await response.json()
                filings = filings_data.get('filings', [])
                
                # Find most recent 990-PF filing with XML URL
                for filing in filings:
                    if filing.get('formtype') in ['990PF', '990-PF'] and filing.get('xml_url'):
                        xml_url = filing['xml_url']
                        
                        # Fetch XML data
                        async with session.get(xml_url) as xml_response:
                            if xml_response.status == 200:
                                return await xml_response.text()
                
        except Exception as e:
            self.logger.debug(f"Error fetching XML data: {e}")
        
        return None
    
    async def _extract_xml_pf_data(self, org: OrganizationProfile, xml_data: str) -> OrganizationProfile:
        """Extract detailed 990-PF data from XML filing."""
        
        try:
            # Extract Part XV grants (enhanced)
            foundation_grants = self._extract_part_xv_grants(xml_data)
            if foundation_grants:
                org.foundation_grants = foundation_grants
            
            # Extract application process information
            application_process = self._extract_application_process(xml_data)
            if application_process:
                org.application_process = application_process
                org.accepts_unsolicited_applications = application_process.accepts_applications == ApplicationAcceptanceStatus.ACCEPTS_APPLICATIONS
            
            # Extract program areas from Part XVI
            program_areas = self._extract_part_xvi_program_areas(xml_data)
            if program_areas:
                org.foundation_program_areas = program_areas
                
        except Exception as e:
            self.logger.debug(f"Error extracting XML PF data: {e}")
        
        return org
    
    def _extract_part_xv_grants(self, xml_data: str) -> List[FoundationGrantRecord]:
        """Extract Part XV grant records with enhanced detail."""
        
        grants = []
        
        try:
            # Look for grant patterns in XML
            # This is a simplified extraction - real implementation would parse XML properly
            grant_patterns = [
                r'<GrantOrContribution.*?</GrantOrContribution>',
                r'<Grant.*?</Grant>',
                r'<Contribution.*?</Contribution>'
            ]
            
            for pattern in grant_patterns:
                matches = re.findall(pattern, xml_data, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    grant = self._parse_grant_xml(match)
                    if grant:
                        grants.append(grant)
        
        except Exception as e:
            self.logger.debug(f"Error extracting Part XV grants: {e}")
        
        return grants[:50]  # Limit to prevent excessive data
    
    def _parse_grant_xml(self, grant_xml: str) -> Optional[FoundationGrantRecord]:
        """Parse individual grant record from XML."""
        
        try:
            # Extract basic grant information using regex
            # This is simplified - production code would use proper XML parsing
            
            name_match = re.search(r'<RecipientName.*?>(.*?)</RecipientName>', grant_xml, re.IGNORECASE | re.DOTALL)
            amount_match = re.search(r'<Amount.*?>(.*?)</Amount>', grant_xml, re.IGNORECASE)
            purpose_match = re.search(r'<Purpose.*?>(.*?)</Purpose>', grant_xml, re.IGNORECASE | re.DOTALL)
            address_match = re.search(r'<Address.*?>(.*?)</Address>', grant_xml, re.IGNORECASE | re.DOTALL)
            
            if name_match and amount_match:
                return FoundationGrantRecord(
                    recipient_name=name_match.group(1).strip(),
                    grant_amount=self._safe_float(amount_match.group(1)) or 0.0,
                    grant_year=datetime.now().year,  # Would extract from filing year
                    grant_purpose=purpose_match.group(1).strip() if purpose_match else None,
                    recipient_address=address_match.group(1).strip() if address_match else None,
                    support_type="Unknown"  # Would extract from XML if available
                )
        except Exception as e:
            self.logger.debug(f"Error parsing grant XML: {e}")
        
        return None
    
    def _extract_application_process(self, xml_data: str) -> Optional[FoundationApplicationProcess]:
        """Extract application process information from Part XV."""
        
        try:
            # Look for application-related text in XML
            accepts_apps = ApplicationAcceptanceStatus.UNKNOWN
            
            if re.search(r'accept.*applications?', xml_data, re.IGNORECASE):
                accepts_apps = ApplicationAcceptanceStatus.ACCEPTS_APPLICATIONS
            elif re.search(r'not.*accept.*applications?|no.*applications?', xml_data, re.IGNORECASE):
                accepts_apps = ApplicationAcceptanceStatus.NO_APPLICATIONS
            elif re.search(r'invitation.*only|by.*invitation', xml_data, re.IGNORECASE):
                accepts_apps = ApplicationAcceptanceStatus.INVITATION_ONLY
            
            return FoundationApplicationProcess(
                accepts_applications=accepts_apps
            )
            
        except Exception as e:
            self.logger.debug(f"Error extracting application process: {e}")
        
        return None
    
    def _extract_part_xvi_program_areas(self, xml_data: str) -> Optional[FoundationProgramAreas]:
        """Extract Part XVI program area information."""
        
        try:
            # Extract program descriptions from XML
            program_descriptions = []
            
            # Look for program-related patterns
            program_patterns = [
                r'<ProgramService.*?>(.*?)</ProgramService>',
                r'<ActivityDescription.*?>(.*?)</ActivityDescription>'
            ]
            
            for pattern in program_patterns:
                matches = re.findall(pattern, xml_data, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    clean_text = re.sub(r'<[^>]+>', '', match).strip()
                    if clean_text and len(clean_text) > 10:
                        program_descriptions.append(clean_text)
            
            if program_descriptions:
                return FoundationProgramAreas(
                    program_descriptions=program_descriptions[:10]  # Limit to prevent excessive data
                )
                
        except Exception as e:
            self.logger.debug(f"Error extracting Part XVI program areas: {e}")
        
        return None
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            if isinstance(value, str):
                # Remove common formatting
                cleaned = re.sub(r'[,$]', '', value.strip())
                if cleaned:
                    return float(cleaned)
                    
        except (ValueError, TypeError):
            pass
        
        return None