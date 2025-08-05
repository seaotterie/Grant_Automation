#!/usr/bin/env python3
"""
PDF OCR Processor (Step 5)
Extracts text and data from PDF filings using OCR technology.

This processor:
1. Takes organizations with downloaded PDF filings
2. Converts PDF pages to images  
3. Runs OCR (Tesseract) to extract text
4. Parses specific sections (Schedule I, board members, financial data)
5. Handles various PDF layouts and quality issues
"""

import time
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
import json

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile


class PDFOCRProcessor(BaseProcessor):
    """Processor for extracting text from PDF filings using OCR."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="pdf_ocr",
            description="Extract text and structured data from PDF filings using OCR (fallback only)",
            version="1.0.0",
            dependencies=["pdf_downloader"],  # Depends on PDF downloads
            estimated_duration=1800,  # 30 minutes for OCR processing
            requires_network=False,
            requires_api_key=False
        )
        super().__init__(metadata)
        
        # OCR configuration
        self.max_concurrent_ocr = 1  # OCR is CPU intensive, process sequentially
        self.dpi = 200  # DPI for PDF to image conversion
        self.tesseract_config = '--oem 3 --psm 6'  # OCR configuration
        
        # Output directory for OCR results
        self.ocr_cache_dir = Path("cache/ocr_results")
        self.ocr_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Text patterns for data extraction
        self.patterns = {
            "schedule_i_header": re.compile(r"Schedule\s*I.*Grants.*Organizations", re.IGNORECASE),
            "board_member": re.compile(r"(Director|Trustee|Officer|President|Secretary|Treasurer)", re.IGNORECASE),
            "financial_amounts": re.compile(r"\$?[\d,]+\.?\d*"),
            "ein_pattern": re.compile(r"\b\d{2}-\d{7}\b"),
            "grant_amount": re.compile(r"[\$]?[\d,]+\.?\d*")
        }
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute PDF OCR processing."""
        start_time = time.time()
        
        try:
            # Check if OCR dependencies are available
            if not OCR_AVAILABLE:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["OCR dependencies not available. Install pytesseract and pdf2image."]
                )
            
            # Get organizations from previous step
            organizations = await self._get_input_organizations(config)
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No organizations found from PDF downloader step"]
                )
            
            self.logger.info(f"Processing OCR for {len(organizations)} organizations")
            
            # Filter organizations that have PDF files to process
            orgs_with_pdfs = self._filter_organizations_with_pdfs(organizations)
            self.logger.info(f"Found {len(orgs_with_pdfs)} organizations with PDFs for OCR")
            
            # Process PDF files with OCR
            ocr_results = await self._process_pdf_ocr(orgs_with_pdfs)
            
            # Enrich organizations with OCR data
            enriched_organizations = await self._enrich_with_ocr_data(organizations, ocr_results)
            
            execution_time = time.time() - start_time
            
            # Prepare results
            result_data = {
                "organizations": [org.dict() for org in enriched_organizations],
                "ocr_stats": {
                    "total_orgs": len(organizations),
                    "orgs_with_pdfs": len(orgs_with_pdfs),
                    "successful_ocr": len([r for r in ocr_results if r["success"]]),
                    "failed_ocr": len([r for r in ocr_results if not r["success"]]),
                    "pages_processed": sum(r.get("pages_processed", 0) for r in ocr_results)
                }
            }
            
            warnings = []
            failed_ocr = [r for r in ocr_results if not r["success"]]
            if failed_ocr:
                warnings.append(f"Failed OCR processing for {len(failed_ocr)} organizations")
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                warnings=warnings,
                metadata={
                    "ocr_engine": "Tesseract",
                    "dpi_setting": self.dpi,
                    "cache_directory": str(self.ocr_cache_dir)
                }
            )
            
        except Exception as e:
            self.logger.error(f"PDF OCR processing failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"PDF OCR processing failed: {str(e)}"]
            )
    
    async def _get_input_organizations(self, config: ProcessorConfig) -> List[OrganizationProfile]:
        """Get organizations from the PDF downloader step."""
        workflow_id = config.workflow_id
        
        # Get previous step results from workflow state
        from src.core.workflow_engine import WorkflowEngine
        engine = WorkflowEngine()
        
        try:
            state = engine.state_manager.get_workflow_state(workflow_id)
            if state and 'pdf_downloader' in state:
                pdf_results = state['pdf_downloader']
                if pdf_results.success and 'organizations' in pdf_results.data:
                    return [
                        OrganizationProfile(**org_data) 
                        for org_data in pdf_results.data['organizations']
                    ]
        except Exception as e:
            self.logger.warning(f"Could not load PDF downloader results: {e}")
        
        return []
    
    def _filter_organizations_with_pdfs(self, organizations: List[OrganizationProfile]) -> List[Dict[str, Any]]:
        """Filter organizations that have PDF files available for OCR (only when XML not available)."""
        orgs_with_pdfs = []
        
        # Look for PDF files in the cache directory
        pdf_cache_dir = Path("cache/pdf_filings")
        xml_cache_dir = Path("cache/xml_filings")
        
        for org in organizations:
            # Only process high-scoring organizations to save processing time
            if org.composite_score and org.composite_score > 0.7:
                # Look for PDF files for this organization
                pdf_files = list(pdf_cache_dir.glob(f"{org.ein}_*.pdf"))
                
                if pdf_files:
                    for pdf_file in pdf_files:
                        # Extract year from filename
                        year_match = re.search(r"_(\d{4})_", pdf_file.name)
                        year = int(year_match.group(1)) if year_match else None
                        
                        # Only process PDF if no corresponding XML exists
                        xml_file = xml_cache_dir / f"{org.ein}_{year}.xml"
                        
                        if not xml_file.exists():
                            # No XML available, process PDF with OCR
                            org_pdf_info = {
                                "ein": org.ein,
                                "name": org.name,
                                "pdf_path": str(pdf_file),
                                "year": year,
                                "ocr_cache_path": self._get_ocr_cache_path(org.ein, year),
                                "reason": "XML not available, using PDF fallback"
                            }
                            orgs_with_pdfs.append(org_pdf_info)
        
        return orgs_with_pdfs
    
    def _get_ocr_cache_path(self, ein: str, year: Optional[int]) -> Path:
        """Get the cache path for OCR results."""
        year_str = str(year) if year else "unknown"
        filename = f"{ein}_{year_str}_ocr.json"
        return self.ocr_cache_dir / filename
    
    async def _process_pdf_ocr(self, pdf_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process PDF files with OCR (sequential processing due to CPU intensity)."""
        results = []
        
        for i, pdf_info in enumerate(pdf_requests):
            self._update_progress(
                i + 1, 
                len(pdf_requests), 
                f"OCR processing {pdf_info['name']}"
            )
            
            result = await self._process_single_pdf_ocr(pdf_info)
            results.append(result)
            
            # Small delay to prevent CPU overload
            await asyncio.sleep(1)
        
        return results
    
    async def _process_single_pdf_ocr(self, pdf_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process OCR for a single PDF file."""
        ein = pdf_info["ein"]
        year = pdf_info["year"]
        pdf_path = Path(pdf_info["pdf_path"])
        cache_path = pdf_info["ocr_cache_path"]
        
        result = {
            "ein": ein,
            "year": year,
            "success": False,
            "pages_processed": 0,
            "extracted_data": {},
            "error": None
        }
        
        try:
            # Check if OCR results are already cached
            if cache_path.exists():
                self.logger.info(f"Using cached OCR results for {ein}_{year}")
                with open(cache_path, 'r') as f:
                    cached_data = json.load(f)
                result.update(cached_data)
                result["success"] = True
                return result
            
            # Convert PDF to images
            self.logger.info(f"Converting PDF to images for {ein}_{year}")
            images = convert_from_path(
                pdf_path, 
                dpi=self.dpi,
                first_page=1,
                last_page=10  # Limit to first 10 pages for performance
            )
            
            if not images:
                result["error"] = "No images extracted from PDF"
                return result
            
            # Extract text from each page
            extracted_text = {}
            extracted_data = {
                "board_members": [],
                "grants_made": [],
                "financial_data": {},
                "schedule_i_data": []
            }
            
            for page_num, image in enumerate(images, 1):
                try:
                    # Run OCR on the page
                    text = pytesseract.image_to_string(image, config=self.tesseract_config)
                    extracted_text[f"page_{page_num}"] = text
                    
                    # Parse specific data from this page
                    page_data = self._parse_page_text(text, page_num)
                    
                    # Merge page data into extracted_data
                    for key in extracted_data:
                        if key in page_data:
                            if isinstance(extracted_data[key], list):
                                extracted_data[key].extend(page_data[key])
                            elif isinstance(extracted_data[key], dict):
                                extracted_data[key].update(page_data[key])
                    
                    result["pages_processed"] += 1
                    
                except Exception as e:
                    self.logger.warning(f"OCR failed for page {page_num} of {ein}_{year}: {e}")
                    continue
            
            if result["pages_processed"] > 0:
                result["success"] = True
                result["extracted_data"] = extracted_data
                
                # Cache the results
                cache_data = {
                    "extracted_text": extracted_text,
                    "extracted_data": extracted_data,
                    "pages_processed": result["pages_processed"],
                    "processed_date": datetime.now().isoformat()
                }
                
                with open(cache_path, 'w') as f:
                    json.dump(cache_data, f, indent=2)
                
                self.logger.info(f"OCR completed for {ein}_{year}: {result['pages_processed']} pages")
            else:
                result["error"] = "No pages successfully processed"
        
        except Exception as e:
            self.logger.error(f"OCR processing failed for {ein}_{year}: {e}")
            result["error"] = str(e)
        
        return result
    
    def _parse_page_text(self, text: str, page_num: int) -> Dict[str, Any]:
        """Parse specific data elements from OCR text."""
        page_data = {
            "board_members": [],
            "grants_made": [],
            "financial_data": {},
            "schedule_i_data": []
        }
        
        lines = text.split('\n')
        
        # Look for Schedule I (grants) section
        in_schedule_i = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Detect Schedule I section
            if self.patterns["schedule_i_header"].search(line):
                in_schedule_i = True
                continue
            
            # Extract board members
            if self.patterns["board_member"].search(line):
                # Look for names in surrounding lines
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    potential_name = lines[j].strip()
                    if len(potential_name) > 5 and not potential_name.isdigit():
                        # Simple name validation
                        if ' ' in potential_name and len(potential_name.split()) >= 2:
                            page_data["board_members"].append({
                                "name": potential_name,
                                "title": line,
                                "page": page_num
                            })
                            break
            
            # Extract Schedule I grants (simplified)
            if in_schedule_i and line:
                amounts = self.patterns["grant_amount"].findall(line)
                if amounts:
                    # Look for organization names in the line
                    clean_line = re.sub(r'[\$,\d\.]', '', line).strip()
                    if len(clean_line) > 10:  # Potential organization name
                        grant_info = {
                            "recipient": clean_line[:100],  # Limit length
                            "amount_text": amounts[0] if amounts else "",
                            "page": page_num,
                            "line": line[:200]  # Store original line for reference
                        }
                        page_data["schedule_i_data"].append(grant_info)
            
            # Stop Schedule I parsing if we hit a new section
            if in_schedule_i and ("Schedule" in line and "I" not in line):
                in_schedule_i = False
        
        return page_data
    
    async def _enrich_with_ocr_data(
        self, 
        organizations: List[OrganizationProfile],
        ocr_results: List[Dict[str, Any]]
    ) -> List[OrganizationProfile]:
        """Enrich organization profiles with OCR extracted data."""
        
        # Create mapping of OCR results by EIN
        ocr_data_map = {}
        for result in ocr_results:
            if result["success"]:
                ein = result["ein"]
                if ein not in ocr_data_map:
                    ocr_data_map[ein] = []
                ocr_data_map[ein].append(result)
        
        enriched_orgs = []
        
        for org in organizations:
            try:
                if org.ein in ocr_data_map:
                    # Merge OCR data for this organization
                    merged_data = self._merge_ocr_data(ocr_data_map[org.ein])
                    
                    # Update organization with OCR data
                    if merged_data["board_members"]:
                        # Add unique board members
                        existing_names = set(member.split(' (')[0] for member in org.board_members)
                        new_members = []
                        
                        for member_data in merged_data["board_members"][:10]:  # Limit to 10
                            name = member_data["name"]
                            if name not in existing_names:
                                new_members.append(f"{name} ({member_data.get('title', 'Unknown')})")
                                existing_names.add(name)
                        
                        org.board_members.extend(new_members)
                    
                    # Add data source tracking
                    org.data_sources.append("PDF OCR Extraction")
                    org.last_updated = datetime.now()
                    
                    # Add processing notes
                    total_pages = sum(r["pages_processed"] for r in ocr_data_map[org.ein])
                    org.add_processing_note(f"OCR processed {total_pages} pages from PDF filings")
                    
                    if merged_data["board_members"]:
                        org.add_processing_note(f"Extracted {len(merged_data['board_members'])} board members via OCR")
                    
                    if merged_data["schedule_i_data"]:
                        org.add_processing_note(f"Found {len(merged_data['schedule_i_data'])} potential grants via OCR")
                
                enriched_orgs.append(org)
                
            except Exception as e:
                self.logger.warning(f"Failed to enrich OCR data for {org.ein}: {e}")
                enriched_orgs.append(org)
        
        return enriched_orgs
    
    def _merge_ocr_data(self, ocr_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge OCR data from multiple files for the same organization."""
        merged = {
            "board_members": [],
            "grants_made": [],
            "financial_data": {},
            "schedule_i_data": []
        }
        
        seen_names = set()
        
        for result in ocr_results:
            extracted_data = result.get("extracted_data", {})
            
            # Merge board members (deduplicate by name)
            for member in extracted_data.get("board_members", []):
                name = member.get("name", "").strip()
                if name and name not in seen_names:
                    merged["board_members"].append(member)
                    seen_names.add(name)
            
            # Merge other data
            merged["schedule_i_data"].extend(extracted_data.get("schedule_i_data", []))
            merged["grants_made"].extend(extracted_data.get("grants_made", []))
            merged["financial_data"].update(extracted_data.get("financial_data", {}))
        
        return merged
    
    def validate_inputs(self, config: ProcessorConfig) -> List[str]:
        """Validate inputs for PDF OCR processing."""
        errors = []
        
        # Check OCR dependencies
        if not OCR_AVAILABLE:
            errors.append("OCR dependencies not available. Install: pip install pytesseract pdf2image")
        
        # Check if Tesseract is installed
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            errors.append("Tesseract OCR engine not found. Please install Tesseract.")
        
        # Check if PDF downloader step completed
        workflow_id = config.workflow_id
        from src.core.workflow_engine import WorkflowEngine
        engine = WorkflowEngine()
        
        try:
            state = engine.state_manager.get_workflow_state(workflow_id)
            if not state or 'pdf_downloader' not in state:
                errors.append("PDF downloader step must complete before OCR processing")
            elif not state['pdf_downloader'].success:
                errors.append("PDF downloader step failed - cannot proceed with OCR")
        except Exception as e:
            errors.append(f"Cannot validate workflow state: {e}")
        
        # Check cache directory permissions
        try:
            test_file = self.ocr_cache_dir / "test_write.tmp"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            errors.append(f"Cannot write to OCR cache directory {self.ocr_cache_dir}: {e}")
        
        return errors


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return PDFOCRProcessor()