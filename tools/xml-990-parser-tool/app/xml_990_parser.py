#!/usr/bin/env python3
"""
XML 990 Parser Tool - 12-Factor Agents Implementation
Human Layer Framework - Factor 4: Tools as Structured Outputs

Single Responsibility: XML download and 990 form schedule parsing for REGULAR NONPROFITS ONLY
- Object_id discovery from ProPublica pages
- Direct XML download with intelligent caching
- Form 990 officer, governance, program, and financial data extraction
- Strict 990 schema validation (rejects 990-PF and 990-EZ forms)
- NO foundation analysis (handled by separate 990-PF tool)
- NO small org analysis (handled by separate 990-EZ tool)
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

print("XML 990 Parser Tool initializing...")


@dataclass
class XML990ParseCriteria:
    """Input criteria for XML 990 parsing following Factor 4 principles."""
    target_eins: List[str]
    schedules_to_extract: List[str] = field(default_factory=lambda: ["officers", "governance", "programs", "financials"])
    cache_enabled: bool = True
    max_years_back: int = 5
    download_if_missing: bool = True
    validate_990_schema: bool = True


@dataclass
class RegularNonprofitOfficer:
    """Form 990 Part VII Section A - Officers, Directors, Trustees, Key Employees."""
    ein: str
    person_name: str
    title: str = "Unknown"
    average_hours_per_week: Optional[float] = None
    is_individual_trustee: bool = False
    is_institutional_trustee: bool = False
    is_officer: bool = False
    is_key_employee: bool = False
    is_highest_compensated: bool = False
    is_former_officer: bool = False
    reportable_comp_from_org: Optional[float] = None
    reportable_comp_from_related_org: Optional[float] = None
    other_compensation: Optional[float] = None
    tax_year: int = 0
    data_source: str = "Form 990 XML"


@dataclass
class OrganizationContactInfo:
    """Contact and organizational information from Form 990."""
    ein: str
    tax_year: int
    website_url: Optional[str] = None
    primary_phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    email_address: Optional[str] = None
    formation_year: Optional[int] = None
    legal_domicile_state: Optional[str] = None
    activity_mission_desc: Optional[str] = None
    organization_type: Optional[str] = None
    multi_state_operations: Optional[List[str]] = None
    operational_footprint: Optional[str] = None


@dataclass
class Schedule990APublicCharity:
    """Schedule A - Public Charity Classification (Grant Eligibility Intelligence)."""
    ein: str
    tax_year: int
    public_charity_status: Optional[bool] = None
    public_support_percentage: Optional[float] = None
    support_test_passed: Optional[bool] = None
    total_public_support: Optional[float] = None
    total_support_amount: Optional[float] = None
    grant_eligibility_classification: Optional[str] = None
    grant_eligibility_confidence: Optional[str] = None


@dataclass
class Schedule990BMajorContributors:
    """Schedule B - Major Contributor Intelligence (Foundation Relationship Patterns)."""
    ein: str
    tax_year: int
    contributor_data_available: bool = False
    major_contributor_count: Optional[int] = None
    contributor_information_restricted: bool = False
    foundation_relationship_indicator: bool = False


@dataclass
class Form990GrantRecord:
    """Schedule I: Grants and other assistance made."""
    ein: str
    recipient_name: str
    recipient_ein: Optional[str] = None
    recipient_address: Optional[str] = None
    grant_amount: float = 0.0
    grant_purpose: Optional[str] = None
    assistance_type: Optional[str] = None
    relationship_description: Optional[str] = None
    tax_year: int = 0
    schedule_part: str = "Schedule I"


@dataclass
class GovernanceIndicators:
    """Governance and management data from Form 990."""
    ein: str
    tax_year: int
    voting_members_governing_body: Optional[int] = None
    independent_voting_members: Optional[int] = None
    total_employees: Optional[int] = None
    total_volunteers: Optional[int] = None
    family_or_business_relationships: Optional[bool] = None
    delegation_of_management_duties: Optional[bool] = None
    minutes_of_governing_body: Optional[bool] = None
    minutes_of_committees: Optional[bool] = None
    conflict_of_interest_policy: Optional[bool] = None
    annual_disclosure_covered_persons: Optional[bool] = None
    regular_monitoring_enforcement: Optional[bool] = None
    whistleblower_policy: Optional[bool] = None
    document_retention_policy: Optional[bool] = None
    compensation_process_ceo: Optional[bool] = None
    compensation_process_other: Optional[bool] = None


@dataclass
class ProgramActivity:
    """Program activity from Form 990 Part III."""
    ein: str
    tax_year: int
    activity_sequence: int
    expense_amount: Optional[float] = None
    description: Optional[str] = None
    program_service_accomplishments: Optional[str] = None
    grants_and_allocations: Optional[float] = None
    program_service_revenue: Optional[float] = None


@dataclass
class Form990FinancialSummary:
    """Financial summary from Form 990."""
    ein: str
    tax_year: int
    contributions_grants_current_year: Optional[float] = None
    contributions_grants_prior_year: Optional[float] = None
    program_service_revenue_current_year: Optional[float] = None
    investment_income_current_year: Optional[float] = None
    other_revenue_current_year: Optional[float] = None
    total_revenue_current_year: Optional[float] = None
    program_service_expenses: Optional[float] = None
    management_general_expenses: Optional[float] = None
    fundraising_expenses: Optional[float] = None
    total_expenses_current_year: Optional[float] = None
    total_assets_end_of_year: Optional[float] = None
    total_liabilities_end_of_year: Optional[float] = None
    net_assets_end_of_year: Optional[float] = None


@dataclass
class XML990FileMetadata:
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
    schema_validation_passed: bool = False


@dataclass
class XML990ExecutionMetadata:
    """Execution metadata."""
    execution_time_ms: float
    organizations_processed: int = 0
    xml_files_found: int = 0
    xml_files_downloaded: int = 0
    xml_files_parsed: int = 0
    schema_validation_failures: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0
    total_officers_extracted: int = 0
    total_grants_extracted: int = 0
    parsing_errors: int = 0
    download_errors: int = 0


@dataclass
class XML990QualityAssessment:
    """Quality assessment."""
    overall_success_rate: float
    schema_validation_rate: float
    officer_data_completeness: float
    financial_data_completeness: float
    governance_data_completeness: float
    data_freshness_score: float
    limitation_notes: List[str] = field(default_factory=list)


@dataclass
class XML990Result:
    """Complete XML 990 parsing result - Factor 4 structured output."""
    officers: List[RegularNonprofitOfficer]
    grants_made: List[Form990GrantRecord]
    governance_indicators: List[GovernanceIndicators]
    program_activities: List[ProgramActivity]
    financial_summaries: List[Form990FinancialSummary]
    contact_information: List[OrganizationContactInfo]
    schedule_a_public_charity: List[Schedule990APublicCharity]
    schedule_b_contributors: List[Schedule990BMajorContributors]
    xml_files_processed: List[XML990FileMetadata]
    execution_metadata: XML990ExecutionMetadata
    quality_assessment: XML990QualityAssessment
    tool_name: str = "XML 990 Parser Tool"
    framework_compliance: str = "Human Layer 12-Factor Agents"
    factor_4_implementation: str = "Tools as Structured Outputs - eliminates XML parsing errors"
    form_type_specialization: str = "990 Forms Only - Regular Nonprofits"
    organizations_processed: int = 0
    officers_extracted: int = 0
    grants_extracted: int = 0
    extraction_failures: int = 0


class XML990ParserTool:
    """
    XML 990 Parser Tool - 12-Factor Agents Implementation

    Single Responsibility: XML download and 990 form parsing for regular nonprofits
    Strict schema validation ensures only 990 forms are processed
    """

    def __init__(self):
        self.tool_name = "XML 990 Parser Tool"
        self.version = "1.0.0"
        self.form_specialization = "990"

        # Cache configuration (specialized for 990 forms)
        self.cache_dir = Path("cache/xml_filings_990")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # ProPublica endpoints (from existing infrastructure)
        self.propublica_base = "https://projects.propublica.org/nonprofits"

        # Download configuration
        self.max_concurrent_downloads = 3
        self.download_timeout = 60
        self.max_retries = 2
        self.retry_delay = 5.0

    async def execute(self, criteria: XML990ParseCriteria) -> XML990Result:
        """
        Execute XML 990 parsing with guaranteed structured output.

        Factor 4 Implementation: Always returns XML990Result with structured data
        """
        start_time = time.time()

        # Initialize result structure
        result = XML990Result(
            officers=[],
            grants_made=[],
            governance_indicators=[],
            program_activities=[],
            financial_summaries=[],
            contact_information=[],
            schedule_a_public_charity=[],
            schedule_b_contributors=[],
            xml_files_processed=[],
            execution_metadata=XML990ExecutionMetadata(
                execution_time_ms=0.0,
                organizations_processed=0,
                parsing_errors=0,
                download_errors=0
            ),
            quality_assessment=XML990QualityAssessment(
                overall_success_rate=0.0,
                schema_validation_rate=0.0,
                officer_data_completeness=0.0,
                financial_data_completeness=0.0,
                governance_data_completeness=0.0,
                data_freshness_score=0.0
            )
        )

        try:
            print(f"Starting XML 990 parsing for {len(criteria.target_eins)} organizations")
            print(f"Form specialization: {self.form_specialization} (Regular Nonprofits Only)")
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

            # Calculate totals
            result.officers_extracted = len(result.officers)
            result.grants_extracted = len(result.grants_made)
            result.execution_metadata.total_officers_extracted = result.officers_extracted
            result.execution_metadata.total_grants_extracted = result.grants_extracted

            # Calculate cache hit rate
            total_cache_operations = result.execution_metadata.cache_hits + result.execution_metadata.cache_misses
            if total_cache_operations > 0:
                result.execution_metadata.cache_hit_rate = result.execution_metadata.cache_hits / total_cache_operations

            # Generate quality assessment
            result.quality_assessment = self._assess_quality(result)

            print(f"XML 990 parsing completed:")
            print(f"   Organizations processed: {result.organizations_processed}")
            print(f"   XML files processed: {len(result.xml_files_processed)}")
            print(f"   Officers extracted: {result.officers_extracted}")
            print(f"   Grants extracted: {result.grants_extracted}")
            print(f"   Schema validation rate: {result.quality_assessment.schema_validation_rate:.1%}")
            print(f"   Cache hit rate: {result.execution_metadata.cache_hit_rate:.1%}")
            print(f"   Execution time: {result.execution_metadata.execution_time_ms:.1f}ms")

            return result

        except Exception as e:
            print(f"Critical error in XML 990 parsing: {e}")
            # Factor 4: Even on critical error, return structured result
            result.execution_metadata.execution_time_ms = (time.time() - start_time) * 1000
            result.quality_assessment.limitation_notes.append(f"Critical error: {str(e)}")
            return result

    async def _process_single_organization(
        self,
        ein: str,
        criteria: XML990ParseCriteria,
        result: XML990Result
    ) -> None:
        """Process XML 990 data for a single organization."""

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

    async def _download_xml_for_organization(self, ein: str, result: XML990Result) -> List[Path]:
        """Download XML files for an organization using ProPublica method."""

        downloaded_files = []

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.download_timeout)
            ) as session:

                # Find object_id by scraping ProPublica page
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
        """Scrape ProPublica organization page to find object_id for XML download."""
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
        result: XML990Result
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
        criteria: XML990ParseCriteria,
        result: XML990Result
    ) -> None:
        """Parse XML file and extract Form 990 data."""

        try:
            # Create file metadata
            file_metadata = XML990FileMetadata(
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

            # Validate this is a 990 form (not 990-PF or 990-EZ)
            file_metadata.form_type = self._extract_form_type(root)
            file_metadata.schema_validation_passed = self._validate_990_schema(root, criteria.validate_990_schema)

            if criteria.validate_990_schema and not file_metadata.schema_validation_passed:
                print(f"   SKIPPING: {file_path.name} is not a Form 990 (detected: {file_metadata.form_type})")
                file_metadata.parsing_errors.append(f"Not a Form 990: {file_metadata.form_type}")
                result.execution_metadata.schema_validation_failures += 1
                result.xml_files_processed.append(file_metadata)
                return

            # Extract tax year
            file_metadata.tax_year = self._extract_tax_year(root)

            print(f"   Parsing XML: {file_path.name} ({file_metadata.tax_year} {file_metadata.form_type})")

            # Extract data based on criteria
            parsing_success = True

            if "officers" in criteria.schedules_to_extract:
                officers = self._extract_990_officers(root, ein, file_metadata.tax_year)
                result.officers.extend(officers)
                if officers:
                    print(f"     Officers: {len(officers)} extracted")

            if "governance" in criteria.schedules_to_extract:
                governance = self._extract_governance_indicators(root, ein, file_metadata.tax_year)
                if governance:
                    result.governance_indicators.append(governance)
                    print(f"     Governance: indicators extracted")

            if "programs" in criteria.schedules_to_extract:
                programs = self._extract_program_activities(root, ein, file_metadata.tax_year)
                result.program_activities.extend(programs)
                if programs:
                    print(f"     Programs: {len(programs)} activities extracted")

            if "financials" in criteria.schedules_to_extract:
                financials = self._extract_financial_summary(root, ein, file_metadata.tax_year)
                if financials:
                    result.financial_summaries.append(financials)
                    print(f"     Financials: summary extracted")

            # Extract grants if available (Schedule I)
            grants = self._extract_990_grants(root, ein, file_metadata.tax_year)
            result.grants_made.extend(grants)
            if grants:
                print(f"     Grants: {len(grants)} records extracted")

            # Extract contact information
            contact_info = self._extract_contact_information(root, ein, file_metadata.tax_year)
            if contact_info:
                result.contact_information.append(contact_info)
                print(f"     Contact: information extracted (URL: {contact_info.website_url or 'N/A'})")

            # Extract Schedule A (Grant Eligibility Intelligence)
            schedule_a = self._extract_schedule_a_public_charity(root, ein, file_metadata.tax_year)
            if schedule_a:
                result.schedule_a_public_charity.append(schedule_a)
                print(f"     Schedule A: {schedule_a.grant_eligibility_classification} ({schedule_a.grant_eligibility_confidence} confidence)")

            # Extract Schedule B (Foundation Relationship Intelligence)
            schedule_b = self._extract_schedule_b_contributors(root, ein, file_metadata.tax_year)
            if schedule_b:
                result.schedule_b_contributors.append(schedule_b)
                print(f"     Schedule B: contributor data {'available' if schedule_b.contributor_data_available else 'not available'}")

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
        """Extract form type from XML root with proper namespace handling."""
        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Check for IRS990 element (regular 990 form) - try multiple paths
            irs990_paths = ['.//IRS990', f'.//{ns}IRS990', './/ReturnData/IRS990', f'.//{ns}ReturnData/{ns}IRS990']
            for path in irs990_paths:
                if root.find(path) is not None:
                    return "990"

            # Check for 990-PF elements
            irs990pf_paths = ['.//IRS990PF', f'.//{ns}IRS990PF', './/ReturnData/IRS990PF', f'.//{ns}ReturnData/{ns}IRS990PF']
            for path in irs990pf_paths:
                if root.find(path) is not None:
                    return "990-PF"

            # Check for 990-EZ elements
            irs990ez_paths = ['.//IRS990EZ', f'.//{ns}IRS990EZ', './/ReturnData/IRS990EZ', f'.//{ns}ReturnData/{ns}IRS990EZ']
            for path in irs990ez_paths:
                if root.find(path) is not None:
                    return "990-EZ"

            # Fallback: check all elements for form type indicators
            for elem in root.iter():
                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if tag_name == 'IRS990':
                    return "990"
                elif tag_name == 'IRS990PF':
                    return "990-PF"
                elif tag_name == 'IRS990EZ':
                    return "990-EZ"

        except Exception as e:
            print(f"Error detecting form type: {e}")

        return "Unknown"

    def _validate_990_schema(self, root: ET.Element, validate: bool) -> bool:
        """Validate that this is actually a Form 990 (not 990-PF or 990-EZ)."""
        if not validate:
            return True

        form_type = self._extract_form_type(root)
        return form_type == "990"

    def _extract_990_officers(self, root: ET.Element, ein: str, tax_year: int) -> List[RegularNonprofitOfficer]:
        """Extract Form 990 Part VII Section A officers and board members."""
        officers = []

        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Look for Form990PartVIISectionAGrp elements (Form 990 specific)
            officer_elements = []

            # Try different search strategies
            if ns:
                # Search with full namespace
                officer_elements = root.findall(f'.//{ns}Form990PartVIISectionAGrp')

            # Fallback to search without namespace
            if not officer_elements:
                officer_elements = root.findall('.//Form990PartVIISectionAGrp')

            # Final fallback: search within IRS990 element if we found one
            if not officer_elements:
                irs990_elem = None
                if ns:
                    irs990_elem = root.find(f'.//{ns}IRS990')
                if irs990_elem is None:
                    irs990_elem = root.find('.//IRS990')

                if irs990_elem is not None:
                    if ns:
                        officer_elements = irs990_elem.findall(f'.//{ns}Form990PartVIISectionAGrp')
                    if not officer_elements:
                        officer_elements = irs990_elem.findall('.//Form990PartVIISectionAGrp')

            for officer_elem in officer_elements:
                try:
                    person_name = self._get_element_text(officer_elem, ".//PersonNm")
                    title = self._get_element_text(officer_elem, ".//TitleTxt")

                    if person_name:
                        officer = RegularNonprofitOfficer(
                            ein=ein,
                            person_name=person_name,
                            title=title or "Unknown",
                            average_hours_per_week=self._get_element_float(officer_elem, ".//AverageHoursPerWeekRt"),
                            is_individual_trustee=self._get_element_bool(officer_elem, ".//IndividualTrusteeOrDirectorInd"),
                            is_institutional_trustee=self._get_element_bool(officer_elem, ".//InstitutionalTrusteeInd"),
                            is_officer=self._get_element_bool(officer_elem, ".//OfficerInd"),
                            is_key_employee=self._get_element_bool(officer_elem, ".//KeyEmployeeInd"),
                            is_highest_compensated=self._get_element_bool(officer_elem, ".//HighestCompensatedEmployeeInd"),
                            is_former_officer=self._get_element_bool(officer_elem, ".//FormerOfcrDirectorTrusteeInd"),
                            reportable_comp_from_org=self._get_element_float(officer_elem, ".//ReportableCompFromOrgAmt"),
                            reportable_comp_from_related_org=self._get_element_float(officer_elem, ".//ReportableCompFromRltdOrgAmt"),
                            other_compensation=self._get_element_float(officer_elem, ".//OtherCompensationAmt"),
                            tax_year=tax_year
                        )
                        officers.append(officer)

                except Exception as e:
                    continue

        except Exception as e:
            print(f"     Error extracting officers: {e}")

        return officers

    def _extract_governance_indicators(self, root: ET.Element, ein: str, tax_year: int) -> Optional[GovernanceIndicators]:
        """Extract governance indicators from Form 990."""

        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Find the IRS990 element (Form 990 specific)
            irs990_elem = None
            irs990_paths = ['.//IRS990', f'.//{ns}IRS990']
            for path in irs990_paths:
                irs990_elem = root.find(path)
                if irs990_elem is not None:
                    break

            if irs990_elem is None:
                return None

            governance = GovernanceIndicators(
                ein=ein,
                tax_year=tax_year,
                voting_members_governing_body=self._get_element_int(irs990_elem, ".//VotingMembersGoverningBodyCnt"),
                independent_voting_members=self._get_element_int(irs990_elem, ".//VotingMembersIndependentCnt"),
                total_employees=self._get_element_int(irs990_elem, ".//TotalEmployeeCnt"),
                total_volunteers=self._get_element_int(irs990_elem, ".//TotalVolunteersCnt"),
                family_or_business_relationships=self._get_element_bool(irs990_elem, ".//FamilyOrBusinessRlnInd"),
                delegation_of_management_duties=self._get_element_bool(irs990_elem, ".//DelegationOfMgmtDutiesInd"),
                minutes_of_governing_body=self._get_element_bool(irs990_elem, ".//MinutesOfGoverningBodyInd"),
                minutes_of_committees=self._get_element_bool(irs990_elem, ".//MinutesOfCommitteesInd"),
                conflict_of_interest_policy=self._get_element_bool(irs990_elem, ".//ConflictOfInterestPolicyInd"),
                annual_disclosure_covered_persons=self._get_element_bool(irs990_elem, ".//AnnualDisclosureCoveredPrsnInd"),
                regular_monitoring_enforcement=self._get_element_bool(irs990_elem, ".//RegularMonitoringEnfrcInd"),
                whistleblower_policy=self._get_element_bool(irs990_elem, ".//WhistleblowerPolicyInd"),
                document_retention_policy=self._get_element_bool(irs990_elem, ".//DocumentRetentionPolicyInd"),
                compensation_process_ceo=self._get_element_bool(irs990_elem, ".//CompensationProcessCEOInd"),
                compensation_process_other=self._get_element_bool(irs990_elem, ".//CompensationProcessOtherInd")
            )

            return governance

        except Exception as e:
            print(f"     Error extracting governance: {e}")
            return None

    def _extract_contact_information(self, root: ET.Element, ein: str, tax_year: int) -> Optional[OrganizationContactInfo]:
        """Extract contact information from Form 990."""

        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Find the IRS990 element (Form 990 specific)
            irs990_elem = None
            irs990_paths = ['.//IRS990', f'.//{ns}IRS990']
            for path in irs990_paths:
                irs990_elem = root.find(path)
                if irs990_elem is not None:
                    break

            if irs990_elem is None:
                return None

            # Extract phone numbers (multiple may exist)
            phone_numbers = []
            phone_paths = ['.//PhoneNum', f'.//{ns}PhoneNum']
            for path in phone_paths:
                phone_elems = irs990_elem.findall(path)
                for phone_elem in phone_elems:
                    if phone_elem is not None and phone_elem.text:
                        phone_numbers.append(phone_elem.text.strip())

            # Remove duplicates while preserving order
            unique_phones = []
            for phone in phone_numbers:
                if phone not in unique_phones:
                    unique_phones.append(phone)

            # Extract organization type indicators
            org_type_indicators = []
            if self._get_element_text(irs990_elem, './/TypeOfOrganizationCorpInd'):
                org_type_indicators.append('Corporation')
            if self._get_element_text(irs990_elem, './/TypeOfOrganizationTrustInd'):
                org_type_indicators.append('Trust')
            if self._get_element_text(irs990_elem, './/TypeOfOrganizationAssocInd'):
                org_type_indicators.append('Association')

            # Extract multi-state operations (Geographic Intelligence)
            states_paths = ['.//StatesWhereCopyOfReturnIsFldCd', f'.//{ns}StatesWhereCopyOfReturnIsFldCd']
            multi_state_list = []
            for path in states_paths:
                states_elements = irs990_elem.findall(path)
                if states_elements:
                    multi_state_list = [elem.text.strip() for elem in states_elements if elem.text]
                    break

            # Create operational footprint description
            operational_footprint = None
            if multi_state_list:
                state_count = len(multi_state_list)
                if state_count == 1:
                    operational_footprint = f"Single-state operations ({multi_state_list[0]})"
                elif state_count <= 5:
                    operational_footprint = f"Multi-state regional operations ({state_count} states)"
                else:
                    operational_footprint = f"National operations ({state_count} states)"

            contact_info = OrganizationContactInfo(
                ein=ein,
                tax_year=tax_year,
                website_url=self._get_element_text(irs990_elem, './/WebsiteAddressTxt'),
                primary_phone=unique_phones[0] if len(unique_phones) > 0 else None,
                alternate_phone=unique_phones[1] if len(unique_phones) > 1 else None,
                email_address=self._get_element_text(irs990_elem, './/EmailAddressTxt'),
                formation_year=self._get_element_int(irs990_elem, './/FormationYr'),
                legal_domicile_state=self._get_element_text(irs990_elem, './/LegalDomicileStateCd'),
                activity_mission_desc=self._get_element_text(irs990_elem, './/ActivityOrMissionDesc'),
                organization_type=', '.join(org_type_indicators) if org_type_indicators else None,
                multi_state_operations=multi_state_list if multi_state_list else None,
                operational_footprint=operational_footprint
            )

            return contact_info

        except Exception as e:
            print(f"     Error extracting contact information: {e}")
            return None

    def _extract_schedule_a_public_charity(self, root: ET.Element, ein: str, tax_year: int) -> Optional[Schedule990APublicCharity]:
        """Extract Schedule A public charity classification data for grant eligibility intelligence."""

        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Find the IRS990ScheduleA element
            schedule_a_elem = None
            schedule_a_paths = ['.//IRS990ScheduleA', f'.//{ns}IRS990ScheduleA']
            for path in schedule_a_paths:
                schedule_a_elem = root.find(path)
                if schedule_a_elem is not None:
                    break

            if schedule_a_elem is None:
                return None

            # Extract public charity status
            public_charity_status = self._get_element_text(schedule_a_elem, './/PublicOrganization170Ind') == 'X'

            # Extract public support percentage
            public_support_pct = self._get_element_float(schedule_a_elem, './/PublicSupportCY170Pct')

            # Extract support test results
            support_test_passed = self._get_element_text(schedule_a_elem, './/ThirtyThrPctSuprtTestsCY170Ind') == 'X'

            # Extract support amounts
            total_public_support = self._get_element_float(schedule_a_elem, './/PublicSupportTotal170Amt')
            total_support = self._get_element_float(schedule_a_elem, './/TotalSupportAmt')

            # Determine grant eligibility classification
            if public_charity_status:
                classification = "Public Charity"
            else:
                classification = "Private Foundation"

            # Determine grant eligibility confidence based on public support percentage
            confidence = "Low"
            if public_support_pct is not None:
                if public_support_pct >= 0.333:  # 33⅓% test
                    confidence = "High" if public_support_pct >= 0.5 else "Medium"

            schedule_a_data = Schedule990APublicCharity(
                ein=ein,
                tax_year=tax_year,
                public_charity_status=public_charity_status,
                public_support_percentage=public_support_pct,
                support_test_passed=support_test_passed,
                total_public_support=total_public_support,
                total_support_amount=total_support,
                grant_eligibility_classification=classification,
                grant_eligibility_confidence=confidence
            )

            return schedule_a_data

        except Exception as e:
            print(f"     Error extracting Schedule A: {e}")
            return None

    def _extract_schedule_b_contributors(self, root: ET.Element, ein: str, tax_year: int) -> Optional[Schedule990BMajorContributors]:
        """Extract Schedule B major contributor data for foundation relationship intelligence."""

        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Find the IRS990ScheduleB element
            schedule_b_elem = None
            schedule_b_paths = ['.//IRS990ScheduleB', f'.//{ns}IRS990ScheduleB']
            for path in schedule_b_paths:
                schedule_b_elem = root.find(path)
                if schedule_b_elem is not None:
                    break

            if schedule_b_elem is None:
                return None

            # Check for contributor information groups
            contributor_groups = schedule_b_elem.findall('.//ContributorInformationGrp')
            contributor_count = len(contributor_groups)

            # Check if contributor information is restricted/redacted
            restricted_info = False
            foundation_relationship = False

            if contributor_groups:
                # Check first contributor for restriction patterns
                first_contributor = contributor_groups[0]
                contributor_num = self._get_element_text(first_contributor, './/ContributorNum')
                business_name = self._get_element_text(first_contributor, './/BusinessNameLine1')

                if contributor_num == 'RESTRICTED' or business_name == 'RESTRICTED':
                    restricted_info = True

                # Foundation relationship indicator based on presence of business names vs individual names
                business_names = [self._get_element_text(grp, './/BusinessNameLine1') for grp in contributor_groups]
                if any(name and 'FOUNDATION' in name.upper() or 'FUND' in name.upper() for name in business_names if name != 'RESTRICTED'):
                    foundation_relationship = True

            schedule_b_data = Schedule990BMajorContributors(
                ein=ein,
                tax_year=tax_year,
                contributor_data_available=contributor_count > 0,
                major_contributor_count=contributor_count if not restricted_info else None,
                contributor_information_restricted=restricted_info,
                foundation_relationship_indicator=foundation_relationship
            )

            return schedule_b_data

        except Exception as e:
            print(f"     Error extracting Schedule B: {e}")
            return None

    def _extract_program_activities(self, root: ET.Element, ein: str, tax_year: int) -> List[ProgramActivity]:
        """Extract program activities from Form 990 Part III."""
        activities = []

        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Find the IRS990 element
            irs990_elem = None
            irs990_paths = ['.//IRS990', f'.//{ns}IRS990']
            for path in irs990_paths:
                irs990_elem = root.find(path)
                if irs990_elem is not None:
                    break

            if irs990_elem is None:
                return activities

            # Look for program service accomplishment groups
            activity_sequence = 1

            # Main program activity
            main_activity = irs990_elem.find('.//ExpenseAmt')
            main_desc = irs990_elem.find('.//Desc')
            if main_activity is not None and main_desc is not None:
                activities.append(ProgramActivity(
                    ein=ein,
                    tax_year=tax_year,
                    activity_sequence=activity_sequence,
                    expense_amount=self._safe_float(main_activity.text),
                    description=main_desc.text,
                    program_service_accomplishments=main_desc.text
                ))
                activity_sequence += 1

            # Additional program activities
            for grp_name in ['ProgSrvcAccomActy2Grp', 'ProgSrvcAccomActy3Grp', 'ProgSrvcAccomActyOtherGrp']:
                grp_elem = irs990_elem.find(f'.//{grp_name}')
                if grp_elem is not None:
                    expense_elem = grp_elem.find('.//ExpenseAmt')
                    desc_elem = grp_elem.find('.//Desc')

                    if expense_elem is not None or desc_elem is not None:
                        activities.append(ProgramActivity(
                            ein=ein,
                            tax_year=tax_year,
                            activity_sequence=activity_sequence,
                            expense_amount=self._safe_float(expense_elem.text) if expense_elem is not None else None,
                            description=desc_elem.text if desc_elem is not None else None,
                            program_service_accomplishments=desc_elem.text if desc_elem is not None else None
                        ))
                        activity_sequence += 1

        except Exception as e:
            print(f"     Error extracting program activities: {e}")

        return activities

    def _extract_financial_summary(self, root: ET.Element, ein: str, tax_year: int) -> Optional[Form990FinancialSummary]:
        """Extract financial summary from Form 990."""

        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Find the IRS990 element
            irs990_elem = None
            irs990_paths = ['.//IRS990', f'.//{ns}IRS990']
            for path in irs990_paths:
                irs990_elem = root.find(path)
                if irs990_elem is not None:
                    break

            if irs990_elem is None:
                return None

            financial = Form990FinancialSummary(
                ein=ein,
                tax_year=tax_year,
                contributions_grants_current_year=self._get_element_float(irs990_elem, ".//CYContributionsGrantsAmt"),
                contributions_grants_prior_year=self._get_element_float(irs990_elem, ".//PYContributionsGrantsAmt"),
                program_service_revenue_current_year=self._get_element_float(irs990_elem, ".//CYProgramServiceRevenueAmt"),
                investment_income_current_year=self._get_element_float(irs990_elem, ".//CYInvestmentIncomeAmt"),
                other_revenue_current_year=self._get_element_float(irs990_elem, ".//CYOtherRevenueAmt"),
                total_revenue_current_year=self._get_element_float(irs990_elem, ".//CYTotalRevenueAmt"),
                program_service_expenses=self._get_element_float(irs990_elem, ".//TotalProgramServiceExpensesAmt"),
                management_general_expenses=self._get_element_float(irs990_elem, ".//ManagementAndGeneralAmt"),
                fundraising_expenses=self._get_element_float(irs990_elem, ".//FundraisingAmt"),
                total_expenses_current_year=self._get_element_float(irs990_elem, ".//CYTotalExpensesAmt"),
                total_assets_end_of_year=self._get_element_float(irs990_elem, ".//TotalAssetsEOYAmt"),
                total_liabilities_end_of_year=self._get_element_float(irs990_elem, ".//TotalLiabilitiesEOYAmt"),
                net_assets_end_of_year=self._get_element_float(irs990_elem, ".//NetAssetsOrFundBalancesEOYAmt")
            )

            return financial

        except Exception as e:
            print(f"     Error extracting financials: {e}")
            return None

    def _extract_990_grants(self, root: ET.Element, ein: str, tax_year: int) -> List[Form990GrantRecord]:
        """Extract grants made from Schedule I (if available)."""
        grants = []

        try:
            # Look for grant elements (Schedule I data)
            grant_elements = root.findall(".//GrantOrContribution") + root.findall(".//RecipientTable")

            for grant_elem in grant_elements[:10]:  # Limit to 10 grants
                try:
                    recipient_name = self._get_element_text(grant_elem, ".//RecipientName", ".//RecipientBusinessName")
                    amount = self._get_element_float(grant_elem, ".//Amount", ".//CashGrant")

                    if recipient_name and amount:
                        grant = Form990GrantRecord(
                            ein=ein,
                            recipient_name=recipient_name,
                            grant_amount=amount,
                            grant_purpose=self._get_element_text(grant_elem, ".//Purpose", ".//GrantPurpose"),
                            recipient_address=self._get_element_text(grant_elem, ".//RecipientAddress"),
                            recipient_ein=self._get_element_text(grant_elem, ".//RecipientEIN"),
                            tax_year=tax_year
                        )
                        grants.append(grant)

                except Exception as e:
                    continue

        except Exception as e:
            print(f"     Error extracting grants: {e}")

        return grants

    def _get_element_text(self, parent: ET.Element, *xpath_options: str) -> Optional[str]:
        """Get text from first matching element with namespace handling."""
        # Handle namespace if present
        ns = ""
        if '}' in parent.tag:
            ns = parent.tag.split('}')[0] + '}'

        for xpath in xpath_options:
            try:
                # Try original xpath first
                elem = parent.find(xpath)
                if elem is not None and elem.text:
                    return elem.text.strip()

                # Try with namespace - need to add namespace to each element in path
                if ns:
                    # Handle the namespace more carefully
                    if xpath.startswith('.//'):
                        # For paths like ".//PersonNm", convert to ".//{ns}PersonNm"
                        element_name = xpath[3:]  # Remove ".//"
                        ns_xpath = f'.//{ns}{element_name}'
                    else:
                        # For other path patterns
                        ns_xpath = xpath.replace('.//', f'.//{ns}').replace('/', f'/{ns}')

                    elem = parent.find(ns_xpath)
                    if elem is not None and elem.text:
                        return elem.text.strip()
            except:
                continue
        return None

    def _get_element_float(self, parent: ET.Element, *xpath_options: str) -> Optional[float]:
        """Get float value from first matching element with namespace handling."""
        # Handle namespace if present
        ns = ""
        if '}' in parent.tag:
            ns = parent.tag.split('}')[0] + '}'

        for xpath in xpath_options:
            try:
                # Try original xpath first
                elem = parent.find(xpath)
                if elem is not None and elem.text:
                    return self._safe_float(elem.text)

                # Try with namespace - need to add namespace to each element in path
                if ns:
                    # Handle the namespace more carefully
                    if xpath.startswith('.//'):
                        # For paths like ".//PersonNm", convert to ".//{ns}PersonNm"
                        element_name = xpath[3:]  # Remove ".//"
                        ns_xpath = f'.//{ns}{element_name}'
                    else:
                        # For other path patterns
                        ns_xpath = xpath.replace('.//', f'.//{ns}').replace('/', f'/{ns}')

                    elem = parent.find(ns_xpath)
                    if elem is not None and elem.text:
                        return self._safe_float(elem.text)
            except:
                continue
        return None

    def _get_element_int(self, parent: ET.Element, *xpath_options: str) -> Optional[int]:
        """Get int value from first matching element with namespace handling."""
        # Handle namespace if present
        ns = ""
        if '}' in parent.tag:
            ns = parent.tag.split('}')[0] + '}'

        for xpath in xpath_options:
            try:
                # Try original xpath first
                elem = parent.find(xpath)
                if elem is not None and elem.text:
                    return int(elem.text.replace(',', '').strip())

                # Try with namespace - need to add namespace to each element in path
                if ns:
                    # Handle the namespace more carefully
                    if xpath.startswith('.//'):
                        # For paths like ".//PersonNm", convert to ".//{ns}PersonNm"
                        element_name = xpath[3:]  # Remove ".//"
                        ns_xpath = f'.//{ns}{element_name}'
                    else:
                        # For other path patterns
                        ns_xpath = xpath.replace('.//', f'.//{ns}').replace('/', f'/{ns}')

                    elem = parent.find(ns_xpath)
                    if elem is not None and elem.text:
                        return int(elem.text.replace(',', '').strip())
            except:
                continue
        return None

    def _get_element_bool(self, parent: ET.Element, *xpath_options: str) -> Optional[bool]:
        """Get boolean value from first matching element with namespace handling."""
        # Handle namespace if present
        ns = ""
        if '}' in parent.tag:
            ns = parent.tag.split('}')[0] + '}'

        for xpath in xpath_options:
            try:
                # Try original xpath first
                elem = parent.find(xpath)
                if elem is not None:
                    if elem.text:
                        return elem.text.strip().lower() in ['1', 'true', 'x', 'yes']
                    else:
                        # Element exists but no text, check for 'X' marker
                        return True

                # Try with namespace - need to add namespace to each element in path
                if ns:
                    # Handle the namespace more carefully
                    if xpath.startswith('.//'):
                        # For paths like ".//PersonNm", convert to ".//{ns}PersonNm"
                        element_name = xpath[3:]  # Remove ".//"
                        ns_xpath = f'.//{ns}{element_name}'
                    else:
                        # For other path patterns
                        ns_xpath = xpath.replace('.//', f'.//{ns}').replace('/', f'/{ns}')

                    elem = parent.find(ns_xpath)
                    if elem is not None:
                        if elem.text:
                            return elem.text.strip().lower() in ['1', 'true', 'x', 'yes']
                        else:
                            # Element exists but no text, check for 'X' marker
                            return True
            except:
                continue
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
                import re
                cleaned = re.sub(r'[,$]', '', value.strip())
                if cleaned:
                    return float(cleaned)

        except (ValueError, TypeError):
            pass

        return None

    def _assess_quality(self, result: XML990Result) -> XML990QualityAssessment:
        """Assess the quality of the XML 990 parsing results."""

        if result.organizations_processed == 0:
            return XML990QualityAssessment(
                overall_success_rate=0.0,
                schema_validation_rate=0.0,
                officer_data_completeness=0.0,
                financial_data_completeness=0.0,
                governance_data_completeness=0.0,
                data_freshness_score=0.0,
                limitation_notes=["No organizations processed"]
            )

        # Calculate success rates
        successful_parses = result.execution_metadata.xml_files_parsed
        schema_validation_failures = result.execution_metadata.schema_validation_failures
        total_attempts = successful_parses + result.execution_metadata.parsing_errors + schema_validation_failures

        overall_success_rate = successful_parses / max(total_attempts, 1)
        schema_validation_rate = (total_attempts - schema_validation_failures) / max(total_attempts, 1)

        # Calculate data completeness
        officer_completeness = 0.0
        if result.officers:
            # Average completeness based on non-null fields
            total_fields = 0
            filled_fields = 0
            for officer in result.officers:
                total_fields += 8  # Key fields: name, title, hours, compensation, etc.
                filled_fields += sum(1 for field in [
                    officer.person_name, officer.title, officer.average_hours_per_week,
                    officer.reportable_comp_from_org, officer.is_officer, officer.is_individual_trustee
                ] if field is not None and field != "Unknown")
            officer_completeness = filled_fields / max(total_fields, 1)

        financial_completeness = 0.0
        if result.financial_summaries:
            # Average completeness of financial data
            for summary in result.financial_summaries:
                fields_count = 13  # Key financial fields
                filled_count = sum(1 for field in [
                    summary.total_revenue_current_year, summary.total_expenses_current_year,
                    summary.total_assets_end_of_year, summary.program_service_expenses,
                    summary.contributions_grants_current_year
                ] if field is not None)
                financial_completeness += filled_count / fields_count
            financial_completeness /= len(result.financial_summaries)

        governance_completeness = 0.0
        if result.governance_indicators:
            # Average completeness of governance data
            for governance in result.governance_indicators:
                fields_count = 17  # Key governance fields
                filled_count = sum(1 for field in [
                    governance.voting_members_governing_body, governance.independent_voting_members,
                    governance.conflict_of_interest_policy, governance.minutes_of_governing_body,
                    governance.whistleblower_policy
                ] if field is not None)
                governance_completeness += filled_count / fields_count
            governance_completeness /= len(result.governance_indicators)

        limitation_notes = []
        if result.execution_metadata.parsing_errors > 0:
            limitation_notes.append(f"{result.execution_metadata.parsing_errors} XML parsing errors")
        if schema_validation_failures > 0:
            limitation_notes.append(f"{schema_validation_failures} files rejected (not Form 990)")
        if result.execution_metadata.download_errors > 0:
            limitation_notes.append(f"{result.execution_metadata.download_errors} XML download errors")

        return XML990QualityAssessment(
            overall_success_rate=overall_success_rate,
            schema_validation_rate=schema_validation_rate,
            officer_data_completeness=officer_completeness,
            financial_data_completeness=financial_completeness,
            governance_data_completeness=governance_completeness,
            data_freshness_score=0.8,  # Assume reasonably fresh for now
            limitation_notes=limitation_notes
        )


# Test function for EIN 81-2827604 (HEROS BRIDGE - confirmed Form 990)
async def test_xml_990_parser():
    """Test the XML 990 parser tool with HEROS BRIDGE."""

    print("Testing XML 990 Parser Tool")
    print("=" * 60)

    # Initialize tool
    tool = XML990ParserTool()

    # Create test criteria
    criteria = XML990ParseCriteria(
        target_eins=["812827604"],  # HEROS BRIDGE (confirmed Form 990)
        schedules_to_extract=["officers", "governance", "programs", "financials"],
        cache_enabled=True,
        max_years_back=5,
        download_if_missing=True,
        validate_990_schema=True  # Strict validation
    )

    # Execute parsing
    result = await tool.execute(criteria)

    # Display results
    print("\nParsing Results:")
    print(f"Tool: {result.tool_name}")
    print(f"Framework: {result.framework_compliance}")
    print(f"Specialization: {result.form_type_specialization}")
    print(f"Factor 4: {result.factor_4_implementation}")
    print(f"Organizations processed: {result.organizations_processed}")
    print(f"XML files processed: {len(result.xml_files_processed)}")

    if result.xml_files_processed:
        print(f"\nXML Files:")
        for xml_file in result.xml_files_processed:
            status = "SUCCESS" if xml_file.parsing_success else "FAILED"
            validation = "VALID 990" if xml_file.schema_validation_passed else f"INVALID ({xml_file.form_type})"
            print(f"  {xml_file.tax_year} {xml_file.form_type}: {xml_file.file_size_bytes:,} bytes - {status} - {validation}")

    if result.officers:
        print(f"\nOfficers Extracted ({len(result.officers)}):")
        for officer in result.officers[:5]:  # Show first 5
            comp = f"${officer.reportable_comp_from_org:,.0f}" if officer.reportable_comp_from_org else "$0"
            hours = f"{officer.average_hours_per_week}hrs/wk" if officer.average_hours_per_week else "N/A"
            print(f"  {officer.person_name}: {officer.title} ({hours}, {comp})")

    if result.governance_indicators:
        print(f"\nGovernance Indicators:")
        gov = result.governance_indicators[0]
        print(f"  Board members: {gov.voting_members_governing_body}")
        print(f"  Independent members: {gov.independent_voting_members}")
        print(f"  Employees: {gov.total_employees}")
        print(f"  Volunteers: {gov.total_volunteers}")
        print(f"  Conflict of interest policy: {gov.conflict_of_interest_policy}")

    if result.program_activities:
        print(f"\nProgram Activities ({len(result.program_activities)}):")
        for activity in result.program_activities:
            expense = f"${activity.expense_amount:,.0f}" if activity.expense_amount else "N/A"
            desc = activity.description[:50] + "..." if activity.description and len(activity.description) > 50 else activity.description
            print(f"  Activity {activity.activity_sequence}: {expense} - {desc}")

    if result.financial_summaries:
        print(f"\nFinancial Summary:")
        fin = result.financial_summaries[0]
        print(f"  Total revenue: ${fin.total_revenue_current_year:,.0f}" if fin.total_revenue_current_year else "N/A")
        print(f"  Total expenses: ${fin.total_expenses_current_year:,.0f}" if fin.total_expenses_current_year else "N/A")
        print(f"  Net assets: ${fin.net_assets_end_of_year:,.0f}" if fin.net_assets_end_of_year else "N/A")

    print(f"\nExecution Metadata:")
    print(f"  Execution time: {result.execution_metadata.execution_time_ms:.1f}ms")
    print(f"  Cache hit rate: {result.execution_metadata.cache_hit_rate:.1%}")
    print(f"  Schema validation rate: {result.quality_assessment.schema_validation_rate:.1%}")
    print(f"  Parsing errors: {result.execution_metadata.parsing_errors}")

    print(f"\nQuality Assessment:")
    print(f"  Overall success: {result.quality_assessment.overall_success_rate:.1%}")
    print(f"  Officer completeness: {result.quality_assessment.officer_data_completeness:.2f}")
    print(f"  Financial completeness: {result.quality_assessment.financial_data_completeness:.2f}")
    print(f"  Governance completeness: {result.quality_assessment.governance_data_completeness:.2f}")

    return result


if __name__ == "__main__":
    asyncio.run(test_xml_990_parser())