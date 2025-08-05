#!/usr/bin/env python3
"""
PDF Downloader Processor (Step 4b)
Downloads PDF versions of 990 filings as fallback when XML is not available.

This processor:
1. Takes organizations from XML downloader step
2. Identifies organizations missing XML data
3. Downloads PDF filings when XML not available
4. Manages file storage and organization
5. Implements retry logic for failed downloads
"""

import asyncio
import aiohttp
import aiofiles
from pathlib import Path
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile


class PDFDownloaderProcessor(BaseProcessor):
    """Processor for downloading 990 PDF filings as fallback."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="pdf_downloader",
            description="Download PDF versions of 990 filings when XML not available (fallback only)",
            version="1.0.0",
            dependencies=["xml_downloader"],  # Depends on XML downloader results
            estimated_duration=900,  # 15 minutes for downloading PDFs
            requires_network=True,
            requires_api_key=False
        )
        super().__init__(metadata)
        
        # Download configuration
        self.max_concurrent_downloads = 2  # PDFs are larger, use fewer concurrent downloads
        self.download_timeout = 120  # 2 minutes for PDF downloads
        self.max_retries = 2
        self.retry_delay = 5.0
        
        # PDF file storage
        self.cache_dir = Path("cache/pdf_filings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # ProPublica PDF endpoints
        self.propublica_pdf_base = "https://projects.propublica.org/nonprofits/organizations"
        
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute PDF downloading."""
        start_time = time.time()
        
        try:
            # Get organizations from previous step
            organizations = await self._get_input_organizations(config)
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No organizations found from XML downloader step"]
                )
            
            self.logger.info(f"Processing PDF downloads for {len(organizations)} organizations")
            
            # Filter organizations that need PDF downloads
            orgs_needing_pdf = self._filter_organizations_for_pdf(organizations)
            self.logger.info(f"Found {len(orgs_needing_pdf)} organizations needing PDF downloads")
            
            # Download PDF files with concurrency control
            download_results = await self._download_pdf_files(orgs_needing_pdf)
            
            # Update organizations with PDF information
            enriched_organizations = self._update_organizations_with_pdf_info(organizations, download_results)
            
            execution_time = time.time() - start_time
            
            # Prepare results
            result_data = {
                "organizations": [org.dict() for org in enriched_organizations],
                "download_stats": {
                    "total_orgs": len(organizations),
                    "attempted_pdf_downloads": len(orgs_needing_pdf),
                    "successful_pdf_downloads": len([r for r in download_results if r["success"]]),
                    "failed_pdf_downloads": len([r for r in download_results if not r["success"]]),
                    "cached_pdf_files": len([r for r in download_results if r.get("cached", False)])
                }
            }
            
            warnings = []
            failed_downloads = [r for r in download_results if not r["success"]]
            if failed_downloads:
                warnings.append(f"Failed to download PDF for {len(failed_downloads)} organizations")
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                warnings=warnings,
                metadata={
                    "cache_directory": str(self.cache_dir),
                    "pdf_source": "ProPublica Nonprofit Explorer",
                    "concurrent_downloads": self.max_concurrent_downloads
                }
            )
            
        except Exception as e:
            self.logger.error(f"PDF download failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"PDF download failed: {str(e)}"]
            )
    
    async def _get_input_organizations(self, config: ProcessorConfig) -> List[OrganizationProfile]:
        """Get organizations from the XML downloader step."""
        workflow_id = config.workflow_id
        
        # Get previous step results from workflow state
        from src.core.workflow_engine import WorkflowEngine
        engine = WorkflowEngine()
        
        try:
            state = engine.state_manager.get_workflow_state(workflow_id)
            if state and 'xml_downloader' in state:
                xml_results = state['xml_downloader']
                if xml_results.success and 'organizations' in xml_results.data:
                    return [
                        OrganizationProfile(**org_data) 
                        for org_data in xml_results.data['organizations']
                    ]
        except Exception as e:
            self.logger.warning(f"Could not load XML downloader results: {e}")
        
        return []
    
    def _filter_organizations_for_pdf(self, organizations: List[OrganizationProfile]) -> List[Dict[str, Any]]:
        """Filter organizations that need PDF downloads (only when XML is missing)."""
        orgs_needing_pdf = []
        
        # Check which organizations have XML files available
        xml_cache_dir = Path("cache/xml_filings")
        
        for org in organizations:
            # Only download PDFs for top organizations that don't have XML data
            if org.composite_score and org.composite_score > 0.6:
                # Check if we have recent filing years
                if org.filing_years:
                    recent_years = [year for year in org.filing_years if year >= 2020]
                    if recent_years:
                        most_recent_year = max(recent_years)
                        
                        # Check if XML file exists for this organization/year
                        xml_file = xml_cache_dir / f"{org.ein}_{most_recent_year}.xml"
                        
                        if not xml_file.exists():
                            # No XML available, need PDF as fallback
                            pdf_info = {
                                "ein": org.ein,
                                "name": org.name,
                                "filing_year": most_recent_year,
                                "pdf_url": self._construct_pdf_url(org.ein, most_recent_year),
                                "cache_path": self._get_cache_path(org.ein, most_recent_year),
                                "reason": "XML not available"
                            }
                            orgs_needing_pdf.append(pdf_info)
        
        return orgs_needing_pdf
    
    def _construct_pdf_url(self, ein: str, year: int) -> str:
        """Construct the ProPublica PDF URL for a filing."""
        # ProPublica URL format: https://projects.propublica.org/nonprofits/organizations/123456789/201812345678900001_990_public.pdf
        # This is a simplified approach - actual URLs require the specific document ID
        return f"{self.propublica_pdf_base}/{ein}/{year}{ein}_990_public.pdf"
    
    def _get_cache_path(self, ein: str, year: int) -> Path:
        """Get the local cache path for a PDF file."""
        filename = f"{ein}_{year}_990.pdf"
        return self.cache_dir / filename
    
    async def _download_pdf_files(self, pdf_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Download PDF files with concurrency control."""
        semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
        
        async def download_single_pdf(pdf_info):
            async with semaphore:
                return await self._download_pdf_file(pdf_info)
        
        # Create download tasks
        tasks = [download_single_pdf(pdf_info) for pdf_info in pdf_requests]
        
        # Execute downloads with progress tracking
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)
            self._update_progress(
                i + 1, 
                len(tasks), 
                f"Downloaded PDF for {result.get('ein', 'unknown')}"
            )
        
        return results
    
    async def _download_pdf_file(self, pdf_info: Dict[str, Any]) -> Dict[str, Any]:
        """Download a single PDF file."""
        ein = pdf_info["ein"]
        year = pdf_info["filing_year"]
        url = pdf_info["pdf_url"]
        cache_path = pdf_info["cache_path"]
        
        result = {
            "ein": ein,
            "year": year,
            "success": False,
            "cached": False,
            "file_path": None,
            "file_size": 0,
            "error": None
        }
        
        try:
            # Check if file already exists in cache
            if cache_path.exists():
                self.logger.info(f"Using cached PDF for {ein}_{year}")
                result["success"] = True
                result["cached"] = True
                result["file_path"] = str(cache_path)
                result["file_size"] = cache_path.stat().st_size
                return result
            
            # Download the file
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.download_timeout)
            ) as session:
                
                for attempt in range(self.max_retries + 1):
                    try:
                        # Note: This is a simplified PDF URL approach
                        # In practice, you'd need to get the actual PDF URLs from ProPublica API
                        async with session.get(url) as response:
                            if response.status == 200:
                                # Check content type
                                content_type = response.headers.get('content-type', '')
                                if 'pdf' not in content_type.lower():
                                    self.logger.warning(f"Unexpected content type for {ein}_{year}: {content_type}")
                                
                                # Save to cache
                                async with aiofiles.open(cache_path, 'wb') as f:
                                    file_size = 0
                                    async for chunk in response.content.iter_chunked(8192):
                                        await f.write(chunk)
                                        file_size += len(chunk)
                                
                                self.logger.info(f"Downloaded PDF for {ein}_{year} ({file_size:,} bytes)")
                                result["success"] = True
                                result["file_path"] = str(cache_path)
                                result["file_size"] = file_size
                                return result
                                
                            elif response.status == 404:
                                # File doesn't exist - try alternative approach
                                # This would be where you'd implement ProPublica API lookup
                                self.logger.info(f"PDF not found at direct URL for {ein}_{year}")
                                result["error"] = "File not found at direct URL"
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
            self.logger.warning(f"Failed to download PDF for {ein}_{year}: {e}")
            result["error"] = str(e)
        
        return result
    
    def _update_organizations_with_pdf_info(
        self, 
        organizations: List[OrganizationProfile],
        download_results: List[Dict[str, Any]]
    ) -> List[OrganizationProfile]:
        """Update organization profiles with PDF download information."""
        
        # Create mapping of successful downloads
        pdf_files = {}
        for result in download_results:
            if result["success"] and result["file_path"]:
                ein = result["ein"]
                year = result["year"]
                if ein not in pdf_files:
                    pdf_files[ein] = {}
                pdf_files[ein][year] = {
                    "file_path": result["file_path"],
                    "file_size": result["file_size"],
                    "cached": result.get("cached", False)
                }
        
        enriched_orgs = []
        
        for org in organizations:
            try:
                if org.ein in pdf_files:
                    # Add PDF information to organization
                    org.data_sources.append("PDF 990 Filings")
                    org.last_updated = datetime.now()
                    
                    # Add processing notes about PDF downloads
                    pdf_years = list(pdf_files[org.ein].keys())
                    org.add_processing_note(f"Downloaded PDF filings for years: {pdf_years}")
                    
                    total_size = sum(
                        info["file_size"] for info in pdf_files[org.ein].values()
                    )
                    if total_size > 0:
                        org.add_processing_note(f"PDF files total size: {total_size:,} bytes")
                
                enriched_orgs.append(org)
                    
            except Exception as e:
                self.logger.warning(f"Failed to update PDF info for {org.ein}: {e}")
                enriched_orgs.append(org)
        
        return enriched_orgs
    
    async def _get_propublica_pdf_urls(self, ein: str) -> List[Dict[str, Any]]:
        """Get actual PDF URLs from ProPublica API (future enhancement)."""
        # This would implement the actual ProPublica API call to get PDF URLs
        # For now, return empty list
        return []
    
    def validate_inputs(self, config: ProcessorConfig) -> List[str]:
        """Validate inputs for PDF downloading."""
        errors = []
        
        # Check if XML downloader step completed successfully
        workflow_id = config.workflow_id
        from src.core.workflow_engine import WorkflowEngine
        engine = WorkflowEngine()
        
        try:
            state = engine.state_manager.get_workflow_state(workflow_id)
            if not state or 'xml_downloader' not in state:
                errors.append("XML downloader step must complete before PDF download")
            elif not state['xml_downloader'].success:
                errors.append("XML downloader step failed - cannot proceed with PDF download")
        except Exception as e:
            errors.append(f"Cannot validate workflow state: {e}")
        
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
    return PDFDownloaderProcessor()