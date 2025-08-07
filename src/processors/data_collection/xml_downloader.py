#!/usr/bin/env python3
"""
XML Downloader Processor (Step 4a)
Downloads XML versions of 990 filings when available.

This processor:
1. Takes scored organizations from financial scorer
2. Identifies available XML filings from IRS/ProPublica
3. Downloads XML files with proper error handling
4. Parses and extracts structured data from XML documents
5. Caches downloaded files to avoid re-processing
"""

import asyncio
import aiohttp
import aiofiles
from pathlib import Path
import time
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile


class XMLDownloaderProcessor(BaseProcessor):
    """Processor for downloading and parsing 990 XML filings."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="xml_downloader",
            description="Download and parse XML versions of 990 filings",
            version="1.0.0",
            dependencies=["financial_scorer"],  # Depends on scored organizations
            estimated_duration=600,  # 10 minutes for downloading files
            requires_network=True,
            requires_api_key=False
        )
        super().__init__(metadata)
        
        # Download configuration
        self.max_concurrent_downloads = 3
        self.download_timeout = 60  # seconds
        self.max_retries = 2
        self.retry_delay = 5.0
        
        # XML file storage
        self.cache_dir = Path("cache/xml_filings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # ProPublica endpoints for XML downloads
        self.propublica_base = "https://projects.propublica.org/nonprofits"
        
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute XML downloading and parsing."""
        start_time = time.time()
        
        try:
            # Get organizations from previous step
            organizations = await self._get_input_organizations(config, workflow_state)
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No organizations found from financial scorer step"]
                )
            
            self.logger.info(f"Processing XML downloads for {len(organizations)} organizations")
            
            # Filter organizations that need XML downloads
            orgs_needing_xml = self._filter_organizations_for_xml(organizations)
            self.logger.info(f"Found {len(orgs_needing_xml)} organizations needing XML downloads")
            
            # Download XML files with concurrency control
            download_results = await self._download_xml_files(orgs_needing_xml)
            
            # Parse downloaded XML files
            enriched_organizations = await self._parse_xml_files(organizations, download_results)
            
            execution_time = time.time() - start_time
            
            # Prepare results
            result_data = {
                "organizations": [org.dict() for org in enriched_organizations],
                "download_stats": {
                    "total_orgs": len(organizations),
                    "attempted_downloads": len(orgs_needing_xml),
                    "successful_downloads": len([r for r in download_results if r["success"]]),
                    "failed_downloads": len([r for r in download_results if not r["success"]]),
                    "cached_files": len([r for r in download_results if r.get("cached", False)])
                }
            }
            
            warnings = []
            failed_downloads = [r for r in download_results if not r["success"]]
            if failed_downloads:
                warnings.append(f"Failed to download XML for {len(failed_downloads)} organizations")
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                warnings=warnings,
                metadata={
                    "cache_directory": str(self.cache_dir),
                    "xml_source": "IRS S3 Bucket",
                    "concurrent_downloads": self.max_concurrent_downloads
                }
            )
            
        except Exception as e:
            self.logger.error(f"XML download failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"XML download failed: {str(e)}"]
            )
    
    async def _get_input_organizations(self, config: ProcessorConfig, workflow_state=None) -> List[OrganizationProfile]:
        """Get organizations from the financial scorer step."""
        try:
            # Get organizations from financial scorer processor
            if workflow_state and workflow_state.has_processor_succeeded('financial_scorer'):
                org_dicts = workflow_state.get_organizations_from_processor('financial_scorer')
                if org_dicts:
                    self.logger.info(f"Retrieved {len(org_dicts)} scored organizations")
                    
                    # Convert dictionaries to OrganizationProfile objects
                    organizations = []
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
            
            # Fallback: create test organization
            self.logger.warning("Financial scorer not completed - using test data")
        except Exception as e:
            self.logger.error(f"Failed to get organizations from financial scorer: {e}")
        
        # For now, we'll create a test organization since we're testing
        # In a real workflow, this would get data from the previous processor
        if hasattr(config, 'workflow_config') and config.workflow_config.target_ein:
            # Create a test organization with the target EIN
            test_org = OrganizationProfile(
                ein=config.workflow_config.target_ein,
                name="Test Organization",
                state="VA",
                composite_score=0.8,  # High score to trigger download
                revenue=1000000,
                filing_years=[2022, 2021, 2020]
            )
            return [test_org]
        
        return []
    
    def _filter_organizations_for_xml(self, organizations: List[OrganizationProfile]) -> List[Dict[str, Any]]:
        """Filter organizations that need XML downloads."""
        orgs_needing_xml = []
        
        for org in organizations:
            # Only download for top-scoring organizations to save time
            if org.composite_score and org.composite_score > 0.5:
                # Check if XML already exists for this EIN
                existing_files = list(self.cache_dir.glob(f"{org.ein}_*.xml"))
                if existing_files:
                    self.logger.info(f"XML already exists for {org.ein}")
                    continue
                
                # Add to download queue - we'll find object_id during download
                xml_info = {
                    "ein": org.ein,
                    "name": org.name,
                    "object_id": None,  # Will be found during download
                    "cache_path": None  # Will be set after object_id is found
                }
                orgs_needing_xml.append(xml_info)
        
        return orgs_needing_xml
    
    async def _find_object_id(self, session: aiohttp.ClientSession, ein: str) -> Optional[str]:
        """
        Scrape ProPublica organization page to find the object_id for XML download.
        Returns the first object_id found in download-xml links.
        """
        url = f"{self.propublica_base}/organizations/{ein}"
        headers = {"User-Agent": "Grant Research Automation Tool"}
        
        try:
            async with session.get(url, headers=headers, timeout=15) as response:
                if response.status != 200:
                    return None
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, "html.parser")
                
                # Look for links containing "/download-xml?object_id="
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"]
                    if "/download-xml?object_id=" in href:
                        # Extract object_id from query parameters
                        parsed_url = urlparse(href)
                        query_params = parse_qs(parsed_url.query)
                        object_id = query_params.get("object_id", [None])[0]
                        if object_id:
                            return object_id
                
                return None
                
        except Exception as e:
            self.logger.warning(f"Failed to find object_id for EIN {ein}: {e}")
            return None
    
    def _get_cache_path(self, ein: str, object_id: str) -> Path:
        """Get the local cache path for an XML file using object_id."""
        filename = f"{ein}_{object_id}.xml"
        return self.cache_dir / filename
    
    async def _download_xml_files(self, xml_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Download XML files with concurrency control."""
        semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
        
        async def download_single_xml(xml_info):
            async with semaphore:
                return await self._download_xml_file(xml_info)
        
        # Create download tasks
        tasks = [download_single_xml(xml_info) for xml_info in xml_requests]
        
        # Execute downloads with progress tracking
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)
            self._update_progress(
                i + 1, 
                len(tasks), 
                f"Downloaded XML for {result.get('ein', 'unknown')}"
            )
        
        return results
    
    async def _download_xml_file(self, xml_info: Dict[str, Any]) -> Dict[str, Any]:
        """Download a single XML file using ProPublica's object_id method."""
        ein = xml_info["ein"]
        
        result = {
            "ein": ein,
            "success": False,
            "cached": False,
            "file_path": None,
            "object_id": None,
            "error": None
        }
        
        try:
            # Check if file already exists in cache
            existing_files = list(self.cache_dir.glob(f"{ein}_*.xml"))
            if existing_files:
                cache_path = existing_files[0]
                self.logger.info(f"Using cached XML for {ein}")
                result["success"] = True
                result["cached"] = True
                result["file_path"] = str(cache_path)
                # Extract object_id from filename
                result["object_id"] = cache_path.stem.split("_", 1)[1]
                return result
            
            # Download the file using ProPublica method
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.download_timeout)
            ) as session:
                
                # Step 1: Find object_id by scraping the organization page
                object_id = await self._find_object_id(session, ein)
                if not object_id:
                    result["error"] = "No XML download link found"
                    return result
                
                result["object_id"] = object_id
                cache_path = self._get_cache_path(ein, object_id)
                
                # Step 2: Download XML using the object_id
                download_url = f"{self.propublica_base}/download-xml"
                headers = {
                    "User-Agent": "Grant Research Automation Tool",
                    "Referer": self.propublica_base
                }
                params = {"object_id": object_id}
                
                for attempt in range(self.max_retries + 1):
                    try:
                        async with session.get(download_url, headers=headers, params=params, allow_redirects=True) as response:
                            if response.status == 200:
                                # Check content type
                                content_type = response.headers.get("Content-Type", "").lower()
                                if "xml" not in content_type:
                                    result["error"] = f"Unexpected content type: {content_type}"
                                    return result
                                
                                # Save to cache
                                xml_content = await response.read()
                                async with aiofiles.open(cache_path, 'wb') as f:
                                    await f.write(xml_content)
                                
                                self.logger.info(f"Downloaded XML for {ein} (object_id: {object_id}, {len(xml_content):,} bytes)")
                                result["success"] = True
                                result["file_path"] = str(cache_path)
                                return result
                                
                            elif response.status == 404:
                                result["error"] = "XML file not found"
                                return result
                            else:
                                raise aiohttp.ClientResponseError(
                                    None, None, status=response.status
                                )
                    
                    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                        if attempt < self.max_retries:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        else:
                            raise e
        
        except Exception as e:
            self.logger.warning(f"Failed to download XML for {ein}: {e}")
            result["error"] = str(e)
        
        return result
    
    async def _parse_xml_files(
        self, 
        organizations: List[OrganizationProfile],
        download_results: List[Dict[str, Any]]
    ) -> List[OrganizationProfile]:
        """Parse downloaded XML files and enrich organization profiles."""
        
        # Create mapping of successful downloads
        xml_files = {}
        for result in download_results:
            if result["success"] and result["file_path"]:
                ein = result["ein"]
                # For now, we'll assume 2022 as the filing year
                # In a real implementation, this would be extracted from the XML filename or content
                year = 2022
                if ein not in xml_files:
                    xml_files[ein] = {}
                xml_files[ein][year] = result["file_path"]
        
        enriched_orgs = []
        
        for org in organizations:
            try:
                if org.ein in xml_files:
                    # Parse XML data for this organization
                    xml_data = await self._parse_organization_xml(org.ein, xml_files[org.ein])
                    
                    if xml_data:
                        # Enrich organization with XML data
                        enriched_org = self._enrich_with_xml_data(org, xml_data)
                        enriched_orgs.append(enriched_org)
                    else:
                        enriched_orgs.append(org)
                else:
                    enriched_orgs.append(org)
                    
            except Exception as e:
                self.logger.warning(f"Failed to parse XML for {org.ein}: {e}")
                enriched_orgs.append(org)
        
        return enriched_orgs
    
    async def _parse_organization_xml(self, ein: str, xml_files: Dict[int, str]) -> Optional[Dict[str, Any]]:
        """Parse XML files for an organization and extract structured data."""
        
        parsed_data = {
            "ein": ein,
            "filings": {},
            "board_members": [],
            "grants_made": [],
            "financial_details": {}
        }
        
        for year, file_path in xml_files.items():
            try:
                filing_data = await self._parse_single_xml_file(file_path, year)
                if filing_data:
                    parsed_data["filings"][year] = filing_data
                    
                    # Extract board members (Schedule J)
                    if "board_members" in filing_data:
                        parsed_data["board_members"].extend(filing_data["board_members"])
                    
                    # Extract grants made (Schedule I)
                    if "grants_made" in filing_data:
                        parsed_data["grants_made"].extend(filing_data["grants_made"])
                        
            except Exception as e:
                self.logger.warning(f"Failed to parse XML file {file_path}: {e}")
                continue
        
        return parsed_data if parsed_data["filings"] else None
    
    async def _parse_single_xml_file(self, file_path: str, year: int) -> Optional[Dict[str, Any]]:
        """Parse a single XML file and extract key data."""
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Define namespace (990 XML files use namespaces)
            ns = {'': 'http://www.irs.gov/efile'}
            
            filing_data = {
                "year": year,
                "file_path": file_path,
                "financial_data": {},
                "board_members": [],
                "grants_made": []
            }
            
            # Extract basic financial data
            financial_mapping = {
                "TotalRevenue": "total_revenue",
                "TotalAssets": "total_assets", 
                "TotalLiabilities": "total_liabilities",
                "NetAssets": "net_assets",
                "TotalExpenses": "total_expenses",
                "ProgramServiceExpenses": "program_expenses"
            }
            
            for xml_field, data_field in financial_mapping.items():
                elements = root.findall(f".//{xml_field}")
                if elements:
                    try:
                        filing_data["financial_data"][data_field] = float(elements[0].text)
                    except (ValueError, AttributeError):
                        pass
            
            # Extract board members (simplified)
            officer_elements = root.findall(".//Officer")
            for officer in officer_elements[:10]:  # Limit to 10 officers
                name_elem = officer.find("PersonName")
                title_elem = officer.find("Title")
                
                if name_elem is not None and name_elem.text:
                    board_member = {
                        "name": name_elem.text.strip(),
                        "title": title_elem.text.strip() if title_elem is not None else "Unknown"
                    }
                    filing_data["board_members"].append(board_member)
            
            # Extract grants made (simplified)
            grant_elements = root.findall(".//GrantOrContribution")
            for grant in grant_elements[:5]:  # Limit to 5 grants
                recipient_elem = grant.find("RecipientName")
                amount_elem = grant.find("Amount")
                
                if recipient_elem is not None and amount_elem is not None:
                    try:
                        grant_info = {
                            "recipient": recipient_elem.text.strip(),
                            "amount": float(amount_elem.text),
                            "year": year
                        }
                        filing_data["grants_made"].append(grant_info)
                    except (ValueError, AttributeError):
                        pass
            
            return filing_data
            
        except ET.ParseError as e:
            self.logger.warning(f"XML parse error in {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"Error parsing XML file {file_path}: {e}")
            return None
    
    def _enrich_with_xml_data(self, org: OrganizationProfile, xml_data: Dict[str, Any]) -> OrganizationProfile:
        """Enrich organization profile with parsed XML data."""
        
        # Add board members
        if xml_data["board_members"]:
            # Deduplicate board members by name
            unique_members = []
            seen_names = set()
            
            for member in xml_data["board_members"]:
                name = member["name"]
                if name not in seen_names:
                    unique_members.append(f"{name} ({member.get('title', 'Unknown')})")
                    seen_names.add(name)
            
            org.board_members = unique_members[:10]  # Limit to 10
        
        # Add key personnel information
        if xml_data["board_members"]:
            org.key_personnel = xml_data["board_members"][:5]  # Top 5 personnel
        
        # Set Schedule I flag if grants were found
        if xml_data["grants_made"]:
            org.has_schedule_i = True
        
        # Update data sources
        org.data_sources.append("IRS XML Filings")
        org.last_updated = datetime.now()
        
        # Add processing notes
        filing_years = list(xml_data["filings"].keys())
        org.add_processing_note(f"Parsed XML filings for years: {filing_years}")
        
        if org.board_members:
            org.add_processing_note(f"Extracted {len(org.board_members)} board members")
        
        if xml_data["grants_made"]:
            total_grants = len(xml_data["grants_made"])
            org.add_processing_note(f"Found {total_grants} grants made in recent filings")
        
        return org
    
    def validate_inputs(self, config: ProcessorConfig) -> List[str]:
        """Validate inputs for XML downloading."""
        errors = []
        
        # Check cache directory permissions
        try:
            test_file = self.cache_dir / "test_write.tmp"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            errors.append(f"Cannot write to cache directory {self.cache_dir}: {e}")
        
        return errors


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return XMLDownloaderProcessor()