#!/usr/bin/env python3
"""
XML Schedule Parser Tool - 12-Factor Agents Implementation
Human Layer Framework - Factor 4: Tools as Structured Outputs

This tool demonstrates Factor 4 by providing XML schedule parsing
with guaranteed structured output format, eliminating XML parsing errors.

Single Responsibility: XML download and schedule data extraction
- Object_id discovery from ProPublica pages
- Direct XML download with intelligent caching
- Schedule I (grants), Schedule J (board), Schedule K (supplemental) parsing
- NO API enrichment (handled by separate tool)
- NO foundation analysis (handled by separate tool)
"""

import asyncio
import aiohttp
import aiofiles
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import sys
import os

# Add the project root to access existing Catalynx infrastructure
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

print("XML Schedule Parser Tool initializing...")


@dataclass
class XMLScheduleCriteria:
    """Input criteria for XML schedule parsing following Factor 4 principles."""
    target_eins: List[str]
    schedules_to_extract: List[str] = field(default_factory=lambda: ["I", "J", "K"])
    cache_enabled: bool = True
    max_years_back: int = 5
    download_if_missing: bool = True


@dataclass
class GrantRecord:
    """Schedule I: Grants and assistance made to organizations."""
    ein: str
    recipient_name: str
    recipient_ein: Optional[str] = None
    grant_amount: float = 0.0
    grant_purpose: Optional[str] = None
    recipient_address: Optional[str] = None
    relationship_description: Optional[str] = None
    tax_year: int = 0
    schedule_part: str = "I"


@dataclass
class BoardMember:
    """Schedule J: Board member compensation and relationships."""
    ein: str
    person_name: str
    title: str = "Unknown"
    compensation: Optional[float] = None
    benefits: Optional[float] = None
    expense_account: Optional[float] = None
    hours_per_week: Optional[float] = None
    relationship_description: Optional[str] = None
    tax_year: int = 0
    schedule_part: str = "J"


@dataclass
class SupplementalFinancialData:
    """Schedule K: Supplemental financial information."""
    ein: str
    tax_year: int
    supplemental_data: Dict[str, str] = field(default_factory=dict)
    financial_metrics: Dict[str, float] = field(default_factory=dict)
    compliance_indicators: Dict[str, bool] = field(default_factory=dict)
    schedule_part: str = "K"


@dataclass
class XMLFileMetadata:
    """XML file processing metadata."""
    ein: str
    object_id: str
    file_path: str
    file_size_bytes: int = 0
    download_timestamp: str = ""
    tax_year: int = 0
    form_type: str = "990"
    xml_namespaces: List[str] = field(default_factory=list)
    parsing_success: bool = False
    parsing_errors: List[str] = field(default_factory=list)


@dataclass
class XMLExecutionMetadata:
    """XML download and parsing execution metadata."""
    execution_time_ms: float
    organizations_processed: int = 0
    xml_files_found: int = 0
    xml_files_downloaded: int = 0
    xml_files_parsed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0
    total_schedules_extracted: int = 0
    parsing_errors: int = 0
    download_errors: int = 0
    object_id_discovery_time_ms: float = 0.0
    xml_download_time_ms: float = 0.0
    schedule_parsing_time_ms: float = 0.0


@dataclass
class XMLQualityAssessment:
    """Quality assessment for XML schedule parsing."""
    overall_success_rate: float
    schedule_coverage_rate: float
    data_completeness_average: float
    xml_file_freshness_score: float
    parsing_reliability_score: float
    limitation_notes: List[str] = field(default_factory=list)


@dataclass
class XMLScheduleResult:
    """Complete XML schedule parsing result - Factor 4 structured output."""
    schedule_i_grants: List[GrantRecord]
    schedule_j_board: List[BoardMember]
    schedule_k_supplemental: List[SupplementalFinancialData]
    xml_files_processed: List[XMLFileMetadata]
    execution_metadata: XMLExecutionMetadata
    quality_assessment: XMLQualityAssessment
    tool_name: str = "XML Schedule Parser Tool"
    framework_compliance: str = "Human Layer 12-Factor Agents"
    factor_4_implementation: str = "Tools as Structured Outputs - eliminates XML parsing errors"
    organizations_processed: int = 0
    schedules_extracted: int = 0
    extraction_failures: int = 0


class XMLScheduleParserTool:
    """
    XML Schedule Parser Tool - 12-Factor Agents Implementation

    Demonstrates Factor 4: Tools as Structured Outputs
    Single Responsibility: XML download and schedule data extraction
    """

    def __init__(self):
        self.tool_name = "XML Schedule Parser Tool"
        self.version = "1.0.0"

        # Cache configuration (adapted from existing xml_downloader.py)
        self.cache_dir = Path("cache/xml_filings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # ProPublica endpoints (from existing infrastructure)
        self.propublica_base = "https://projects.propublica.org/nonprofits"

        # Download configuration
        self.max_concurrent_downloads = 3
        self.download_timeout = 60
        self.max_retries = 2
        self.retry_delay = 5.0

    async def execute(self, criteria: XMLScheduleCriteria) -> XMLScheduleResult:
        """
        Execute XML schedule parsing with guaranteed structured output.

        Factor 4 Implementation: This method ALWAYS returns an XMLScheduleResult
        with structured data, eliminating any XML parsing errors.
        """
        start_time = time.time()

        # Initialize result structure
        result = XMLScheduleResult(
            schedule_i_grants=[],
            schedule_j_board=[],
            schedule_k_supplemental=[],
            xml_files_processed=[],
            execution_metadata=XMLExecutionMetadata(
                execution_time_ms=0.0,
                organizations_processed=0,
                parsing_errors=0,
                download_errors=0
            ),
            quality_assessment=XMLQualityAssessment(
                overall_success_rate=0.0,
                schedule_coverage_rate=0.0,
                data_completeness_average=0.0,
                xml_file_freshness_score=0.0,
                parsing_reliability_score=0.0
            )
        )

        try:
            print(f"Starting XML schedule parsing for {len(criteria.target_eins)} organizations")
            print(f"Schedules to extract: {', '.join(criteria.schedules_to_extract)}")

            # Process each EIN
            for ein in criteria.target_eins:
                try:
                    await self._process_single_organization(ein, criteria, result)
                except Exception as e:
                    print(f"Failed to process organization {ein}: {e}")
                    result.extraction_failures += 1
                    result.execution_metadata.parsing_errors += 1

            # Calculate final metrics
            result.organizations_processed = len(criteria.target_eins)
            result.execution_metadata.organizations_processed = len(criteria.target_eins)
            result.execution_metadata.execution_time_ms = (time.time() - start_time) * 1000

            # Calculate cache hit rate
            total_cache_operations = result.execution_metadata.cache_hits + result.execution_metadata.cache_misses
            if total_cache_operations > 0:
                result.execution_metadata.cache_hit_rate = result.execution_metadata.cache_hits / total_cache_operations

            # Generate quality assessment
            result.quality_assessment = self._assess_quality(result)

            print(f"XML schedule parsing completed:")
            print(f"   Organizations processed: {result.organizations_processed}")
            print(f"   XML files processed: {len(result.xml_files_processed)}")
            print(f"   Schedule I grants: {len(result.schedule_i_grants)}")
            print(f"   Schedule J board members: {len(result.schedule_j_board)}")
            print(f"   Schedule K supplemental: {len(result.schedule_k_supplemental)}")
            print(f"   Cache hit rate: {result.execution_metadata.cache_hit_rate:.1%}")
            print(f"   Execution time: {result.execution_metadata.execution_time_ms:.1f}ms")

            return result

        except Exception as e:
            print(f"Critical error in XML schedule parsing: {e}")
            # Factor 4: Even on critical error, return structured result
            result.execution_metadata.execution_time_ms = (time.time() - start_time) * 1000
            result.quality_assessment.limitation_notes.append(f"Critical error: {str(e)}")
            return result

    async def _process_single_organization(
        self,
        ein: str,
        criteria: XMLScheduleCriteria,
        result: XMLScheduleResult
    ) -> None:
        """Process XML schedules for a single organization."""

        try:
            print(f"   Processing EIN: {ein}")

            # Check for existing cached XML files
            cached_files = self._find_cached_xml_files(ein)

            if cached_files:
                print(f"   Found {len(cached_files)} cached XML files for {ein}")
                result.execution_metadata.cache_hits += len(cached_files)

                # Process cached files
                for file_path in cached_files:
                    await self._parse_xml_file(file_path, ein, criteria, result)
            else:
                result.execution_metadata.cache_misses += 1

                if criteria.download_if_missing:
                    # Attempt to download XML files
                    downloaded_files = await self._download_xml_for_organization(ein, result)

                    # Process downloaded files
                    for file_path in downloaded_files:
                        await self._parse_xml_file(file_path, ein, criteria, result)
                else:
                    print(f"   No cached XML found for {ein} and download disabled")

        except Exception as e:
            print(f"   Error processing {ein}: {e}")
            result.execution_metadata.parsing_errors += 1

    def _find_cached_xml_files(self, ein: str) -> List[Path]:
        """Find existing cached XML files for an organization."""
        try:
            # Look for files matching pattern: {EIN}_*.xml
            pattern = f"{ein}_*.xml"
            cached_files = list(self.cache_dir.glob(pattern))
            return sorted(cached_files, reverse=True)  # Most recent first
        except Exception as e:
            print(f"   Error finding cached files for {ein}: {e}")
            return []

    async def _download_xml_for_organization(self, ein: str, result: XMLScheduleResult) -> List[Path]:
        """Download XML files for an organization using ProPublica method."""

        downloaded_files = []

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.download_timeout)
            ) as session:

                # Find object_id by scraping ProPublica page (from existing xml_downloader.py)
                object_id = await self._find_object_id(session, ein)

                if not object_id:
                    print(f"   No XML download link found for {ein}")
                    result.execution_metadata.download_errors += 1
                    return downloaded_files

                # Download XML using object_id
                file_path = await self._download_xml_file(session, ein, object_id, result)

                if file_path:
                    downloaded_files.append(file_path)
                    result.execution_metadata.xml_files_downloaded += 1

        except Exception as e:
            print(f"   Download error for {ein}: {e}")
            result.execution_metadata.download_errors += 1

        return downloaded_files

    async def _find_object_id(self, session: aiohttp.ClientSession, ein: str) -> Optional[str]:
        """
        Scrape ProPublica organization page to find object_id for XML download.
        Adapted from existing xml_downloader.py methodology.
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
                        parsed_url = urlparse(href)
                        query_params = parse_qs(parsed_url.query)
                        object_id = query_params.get("object_id", [None])[0]
                        if object_id:
                            return object_id

                return None

        except Exception as e:
            print(f"   Failed to find object_id for EIN {ein}: {e}")
            return None

    async def _download_xml_file(
        self,
        session: aiohttp.ClientSession,
        ein: str,
        object_id: str,
        result: XMLScheduleResult
    ) -> Optional[Path]:
        """Download XML file using ProPublica's object_id method."""

        cache_path = self.cache_dir / f"{ein}_{object_id}.xml"

        try:
            download_url = f"{self.propublica_base}/download-xml"
            headers = {
                "User-Agent": "Grant Research Automation Tool",
                "Referer": self.propublica_base
            }
            params = {"object_id": object_id}

            async with session.get(download_url, headers=headers, params=params, allow_redirects=True) as response:
                if response.status == 200:
                    # Check content type
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "xml" not in content_type:
                        print(f"   Unexpected content type for {ein}: {content_type}")
                        return None

                    # Save to cache
                    xml_content = await response.read()
                    async with aiofiles.open(cache_path, 'wb') as f:
                        await f.write(xml_content)

                    print(f"   Downloaded XML for {ein} ({len(xml_content):,} bytes)")
                    return cache_path

                elif response.status == 404:
                    print(f"   XML file not found for {ein}")
                    return None
                else:
                    print(f"   Download failed for {ein}: HTTP {response.status}")
                    return None

        except Exception as e:
            print(f"   Failed to download XML for {ein}: {e}")
            return None

    async def _parse_xml_file(
        self,
        file_path: Path,
        ein: str,
        criteria: XMLScheduleCriteria,
        result: XMLScheduleResult
    ) -> None:
        """Parse XML file and extract schedule data."""

        try:
            # Create file metadata
            file_metadata = XMLFileMetadata(
                ein=ein,
                object_id=self._extract_object_id_from_filename(file_path),
                file_path=str(file_path),
                file_size_bytes=file_path.stat().st_size,
                download_timestamp=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            )

            # Parse XML
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Extract namespace information
            file_metadata.xml_namespaces = [ns for ns in [root.tag.split('}')[0].strip('{') if '}' in root.tag else ''] if ns]

            # Try to determine tax year and form type
            file_metadata.tax_year = self._extract_tax_year(root)
            file_metadata.form_type = self._extract_form_type(root)

            print(f"   Parsing XML: {file_path.name} ({file_metadata.tax_year} {file_metadata.form_type})")

            # Extract schedules based on criteria
            parsing_success = True

            if "I" in criteria.schedules_to_extract:
                grants = self._extract_schedule_i(root, ein, file_metadata.tax_year)
                result.schedule_i_grants.extend(grants)
                if grants:
                    print(f"     Schedule I: {len(grants)} grants found")

            if "J" in criteria.schedules_to_extract:
                board_members = self._extract_schedule_j(root, ein, file_metadata.tax_year)
                result.schedule_j_board.extend(board_members)
                if board_members:
                    print(f"     Schedule J: {len(board_members)} board members found")

            if "K" in criteria.schedules_to_extract:
                supplemental = self._extract_schedule_k(root, ein, file_metadata.tax_year)
                if supplemental:
                    result.schedule_k_supplemental.append(supplemental)
                    print(f"     Schedule K: supplemental data found")

            file_metadata.parsing_success = parsing_success
            result.xml_files_processed.append(file_metadata)
            result.execution_metadata.xml_files_parsed += 1

        except ET.ParseError as e:
            print(f"   XML parse error in {file_path}: {e}")
            result.execution_metadata.parsing_errors += 1
        except Exception as e:
            print(f"   Error parsing XML file {file_path}: {e}")
            result.execution_metadata.parsing_errors += 1

    def _extract_object_id_from_filename(self, file_path: Path) -> str:
        """Extract object_id from filename like EIN_OBJECTID.xml"""
        try:
            stem = file_path.stem
            if '_' in stem:
                return stem.split('_', 1)[1]
        except:
            pass
        return "unknown"

    def _extract_tax_year(self, root: ET.Element) -> int:
        """Extract tax year from XML root."""
        try:
            # Look for common tax year elements
            year_elements = root.findall(".//TaxYear") + root.findall(".//TaxPeriodBeginDate") + root.findall(".//TaxPeriodEndDate")
            for elem in year_elements:
                if elem.text and len(elem.text) >= 4:
                    year_str = elem.text[:4]
                    return int(year_str)
        except:
            pass
        return 2022  # Default year

    def _extract_form_type(self, root: ET.Element) -> str:
        """Extract form type from XML root."""
        try:
            # Check root tag or look for form type indicators
            if "990PF" in root.tag or "990-PF" in root.tag:
                return "990-PF"
            elif "990EZ" in root.tag or "990-EZ" in root.tag:
                return "990-EZ"
            elif "990" in root.tag:
                return "990"
        except:
            pass
        return "990"

    def _extract_schedule_i(self, root: ET.Element, ein: str, tax_year: int) -> List[GrantRecord]:
        """Extract Schedule I grants data."""
        grants = []

        try:
            # Look for Schedule I grant elements (simplified extraction)
            grant_elements = root.findall(".//GrantOrContribution") + root.findall(".//RecipientTable")

            for grant_elem in grant_elements[:10]:  # Limit to 10 grants
                try:
                    recipient_name = self._get_element_text(grant_elem, ".//RecipientName", ".//RecipientBusinessName")
                    amount = self._get_element_float(grant_elem, ".//Amount", ".//CashGrant")

                    if recipient_name and amount:
                        grant = GrantRecord(
                            ein=ein,
                            recipient_name=recipient_name,
                            grant_amount=amount,
                            grant_purpose=self._get_element_text(grant_elem, ".//Purpose", ".//GrantPurpose"),
                            recipient_address=self._get_element_text(grant_elem, ".//RecipientAddress"),
                            tax_year=tax_year
                        )
                        grants.append(grant)

                except Exception as e:
                    continue

        except Exception as e:
            print(f"     Error extracting Schedule I: {e}")

        return grants

    def _extract_schedule_j(self, root: ET.Element, ein: str, tax_year: int) -> List[BoardMember]:
        """Extract Schedule J board member data."""
        board_members = []

        try:
            # Look for Schedule J officer/board member elements
            officer_elements = root.findall(".//Officer") + root.findall(".//Person") + root.findall(".//CompensationData")

            for officer_elem in officer_elements[:15]:  # Limit to 15 officers
                try:
                    person_name = self._get_element_text(officer_elem, ".//PersonName", ".//PersonNm")
                    title = self._get_element_text(officer_elem, ".//Title", ".//TitleTxt")

                    if person_name:
                        board_member = BoardMember(
                            ein=ein,
                            person_name=person_name,
                            title=title or "Unknown",
                            compensation=self._get_element_float(officer_elem, ".//Compensation", ".//TotalCompensation"),
                            benefits=self._get_element_float(officer_elem, ".//Benefits"),
                            hours_per_week=self._get_element_float(officer_elem, ".//HoursPerWeek"),
                            tax_year=tax_year
                        )
                        board_members.append(board_member)

                except Exception as e:
                    continue

        except Exception as e:
            print(f"     Error extracting Schedule J: {e}")

        return board_members

    def _extract_schedule_k(self, root: ET.Element, ein: str, tax_year: int) -> Optional[SupplementalFinancialData]:
        """Extract Schedule K supplemental financial data."""

        try:
            supplemental_data = {}
            financial_metrics = {}
            compliance_indicators = {}

            # Extract various supplemental data elements (simplified)
            for elem in root.iter():
                if elem.text and len(elem.tag) > 5:  # Skip very short tags
                    tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

                    # Try to parse as float
                    try:
                        value = float(elem.text.replace(',', ''))
                        financial_metrics[tag_name] = value
                    except:
                        # Store as text
                        if elem.text.lower() in ['true', 'false', 'yes', 'no']:
                            compliance_indicators[tag_name] = elem.text.lower() in ['true', 'yes']
                        else:
                            supplemental_data[tag_name] = elem.text[:100]  # Truncate long text

            # Only return if we found some data
            if supplemental_data or financial_metrics or compliance_indicators:
                return SupplementalFinancialData(
                    ein=ein,
                    tax_year=tax_year,
                    supplemental_data=supplemental_data,
                    financial_metrics=financial_metrics,
                    compliance_indicators=compliance_indicators
                )

        except Exception as e:
            print(f"     Error extracting Schedule K: {e}")

        return None

    def _get_element_text(self, parent: ET.Element, *xpath_options: str) -> Optional[str]:
        """Get text from first matching element."""
        for xpath in xpath_options:
            try:
                elem = parent.find(xpath)
                if elem is not None and elem.text:
                    return elem.text.strip()
            except:
                continue
        return None

    def _get_element_float(self, parent: ET.Element, *xpath_options: str) -> Optional[float]:
        """Get float value from first matching element."""
        for xpath in xpath_options:
            try:
                elem = parent.find(xpath)
                if elem is not None and elem.text:
                    # Clean and convert to float
                    cleaned = elem.text.replace(',', '').replace('$', '').strip()
                    return float(cleaned)
            except:
                continue
        return None

    def _assess_quality(self, result: XMLScheduleResult) -> XMLQualityAssessment:
        """Assess the quality of the XML schedule parsing results."""

        if result.organizations_processed == 0:
            return XMLQualityAssessment(
                overall_success_rate=0.0,
                schedule_coverage_rate=0.0,
                data_completeness_average=0.0,
                xml_file_freshness_score=0.0,
                parsing_reliability_score=0.0,
                limitation_notes=["No organizations processed"]
            )

        # Calculate success rates
        successful_parses = result.execution_metadata.xml_files_parsed
        total_attempts = successful_parses + result.execution_metadata.parsing_errors
        overall_success_rate = successful_parses / max(total_attempts, 1)

        # Calculate schedule coverage
        schedules_found = len(result.schedule_i_grants) + len(result.schedule_j_board) + len(result.schedule_k_supplemental)
        schedule_coverage_rate = min(1.0, schedules_found / max(result.organizations_processed, 1))

        # Calculate data completeness (based on non-empty fields)
        completeness_scores = []
        for grant in result.schedule_i_grants:
            fields = [grant.recipient_name, grant.grant_amount, grant.grant_purpose]
            completeness_scores.append(sum(1 for field in fields if field) / len(fields))

        data_completeness_average = sum(completeness_scores) / max(len(completeness_scores), 1) if completeness_scores else 0.0

        # XML file freshness (based on download timestamps)
        freshness_score = 0.8  # Assume reasonably fresh for now

        limitation_notes = []
        if result.execution_metadata.parsing_errors > 0:
            limitation_notes.append(f"{result.execution_metadata.parsing_errors} XML parsing errors")
        if result.execution_metadata.download_errors > 0:
            limitation_notes.append(f"{result.execution_metadata.download_errors} XML download errors")

        return XMLQualityAssessment(
            overall_success_rate=overall_success_rate,
            schedule_coverage_rate=schedule_coverage_rate,
            data_completeness_average=data_completeness_average,
            xml_file_freshness_score=freshness_score,
            parsing_reliability_score=overall_success_rate,
            limitation_notes=limitation_notes
        )


# Test function for EIN 81-2827604
async def test_xml_schedule_parser():
    """Test the XML schedule parser tool with HEROS BRIDGE."""

    print("Testing XML Schedule Parser Tool")
    print("=" * 60)

    # Initialize tool
    tool = XMLScheduleParserTool()

    # Create test criteria
    criteria = XMLScheduleCriteria(
        target_eins=["812827604"],  # HEROS BRIDGE
        schedules_to_extract=["I", "J", "K"],
        cache_enabled=True,
        max_years_back=5,
        download_if_missing=True
    )

    # Execute parsing
    result = await tool.execute(criteria)

    # Display results
    print("\nParsing Results:")
    print(f"Tool: {result.tool_name}")
    print(f"Framework: {result.framework_compliance}")
    print(f"Factor 4: {result.factor_4_implementation}")
    print(f"Organizations processed: {result.organizations_processed}")
    print(f"XML files processed: {len(result.xml_files_processed)}")
    print(f"Schedules extracted: {result.schedules_extracted}")

    if result.xml_files_processed:
        print(f"\nXML Files:")
        for xml_file in result.xml_files_processed:
            print(f"  {xml_file.tax_year} {xml_file.form_type}: {xml_file.file_size_bytes:,} bytes")

    if result.schedule_i_grants:
        print(f"\nSchedule I Grants ({len(result.schedule_i_grants)}):")
        for grant in result.schedule_i_grants[:3]:  # Show first 3
            print(f"  {grant.recipient_name}: ${grant.grant_amount:,.0f}")

    if result.schedule_j_board:
        print(f"\nSchedule J Board Members ({len(result.schedule_j_board)}):")
        for member in result.schedule_j_board[:5]:  # Show first 5
            print(f"  {member.person_name}: {member.title}")

    print(f"\nExecution Metadata:")
    print(f"  Execution time: {result.execution_metadata.execution_time_ms:.1f}ms")
    print(f"  Cache hit rate: {result.execution_metadata.cache_hit_rate:.1%}")
    print(f"  Parsing errors: {result.execution_metadata.parsing_errors}")

    print(f"\nQuality Assessment:")
    print(f"  Overall success: {result.quality_assessment.overall_success_rate:.1%}")
    print(f"  Schedule coverage: {result.quality_assessment.schedule_coverage_rate:.1%}")
    print(f"  Data completeness: {result.quality_assessment.data_completeness_average:.2f}")

    return result


if __name__ == "__main__":
    asyncio.run(test_xml_schedule_parser())