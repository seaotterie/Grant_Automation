#!/usr/bin/env python3
"""
XML 990-PF Parser Tool - 12-Factor Agents Implementation
Human Layer Framework - Factor 4: Tools as Structured Outputs

Single Responsibility: XML download and 990-PF form schedule parsing for PRIVATE FOUNDATIONS ONLY
- Object_id discovery from ProPublica pages
- Direct XML download with intelligent caching
- Form 990-PF officer, grant, investment, and payout data extraction
- Strict 990-PF schema validation (rejects 990 and 990-EZ forms)
- NO regular nonprofit analysis (handled by separate 990 tool)
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

print("XML 990-PF Parser Tool initializing...")


@dataclass
class XML990PFParseCriteria:
    """Input criteria for XML 990-PF parsing following Factor 4 principles."""
    target_eins: List[str]
    schedules_to_extract: List[str] = field(default_factory=lambda: ["officers", "grants_paid", "investments", "excise_tax", "payout_requirements"])
    cache_enabled: bool = True
    max_years_back: int = 5
    download_if_missing: bool = True
    validate_990pf_schema: bool = True


@dataclass
class FoundationOfficer:
    """Form 990-PF Part VIII - Officers, Directors, Trustees, Foundation Managers."""
    ein: str
    person_name: str
    title: str = "Unknown"
    average_hours_per_week: Optional[float] = None
    compensation: Optional[float] = None
    employee_benefit_program: Optional[bool] = None
    expense_account_allowance: Optional[float] = None
    is_officer: bool = False
    is_director: bool = False
    tax_year: int = 0
    data_source: str = "Form 990-PF XML"


@dataclass
class FoundationGrant:
    """Part XV: Grants and contributions paid."""
    ein: str
    recipient_name: str
    recipient_type: Optional[str] = None
    recipient_address: Optional[str] = None
    recipient_relationship: Optional[str] = None
    grant_amount: float = 0.0
    grant_purpose: Optional[str] = None
    foundation_status_of_recipient: Optional[str] = None
    grant_monitoring_procedures: Optional[str] = None
    tax_year: int = 0
    schedule_part: str = "Part XV - Grants"


@dataclass
class InvestmentHolding:
    """Part II: Investment holdings."""
    ein: str
    tax_year: int
    investment_type: str
    book_value: Optional[float] = None
    fair_market_value: Optional[float] = None
    investment_description: Optional[str] = None
    acquisition_date: Optional[str] = None
    cost_basis: Optional[float] = None
    investment_category: str = "Unknown"


@dataclass
class ExciseTaxData:
    """Part VI: Excise tax computation."""
    ein: str
    tax_year: int
    net_investment_income: Optional[float] = None
    excise_tax_rate: Optional[float] = None
    excise_tax_owed: Optional[float] = None
    prior_year_tax_underpayment: Optional[float] = None
    total_excise_tax_and_underpayment: Optional[float] = None
    qualifying_distributions_made: Optional[float] = None


@dataclass
class PayoutRequirement:
    """Part XII: Payout requirements."""
    ein: str
    tax_year: int
    average_monthly_fair_market_value: Optional[float] = None
    minimum_investment_return: Optional[float] = None
    distributable_amount: Optional[float] = None
    qualifying_distributions_made: Optional[float] = None
    excess_distributions: Optional[float] = None
    underdistributions: Optional[float] = None
    carryover_from_prior_years: Optional[float] = None
    remaining_underdistributions: Optional[float] = None


@dataclass
class FoundationGovernance:
    """Foundation governance and operations."""
    ein: str
    tax_year: int
    operating_foundation: Optional[bool] = None
    private_foundation_status: Optional[bool] = None
    section_4942_j_election: Optional[bool] = None
    board_meetings_held: Optional[int] = None
    compensation_policy: Optional[bool] = None
    conflict_of_interest_policy: Optional[bool] = None
    minutes_of_governing_body: Optional[bool] = None
    independent_audit: Optional[bool] = None
    audit_committee: Optional[bool] = None
    investment_policy: Optional[bool] = None
    grant_making_procedures: Optional[bool] = None
    grant_monitoring_procedures: Optional[bool] = None
    website_grant_application_process: Optional[bool] = None


@dataclass
class Foundation990PFFinancialSummary:
    """Financial summary from 990-PF."""
    ein: str
    tax_year: int
    contributions_received: Optional[float] = None
    interest_dividends_received: Optional[float] = None
    gross_rents: Optional[float] = None
    net_rental_income: Optional[float] = None
    net_gain_sales_assets: Optional[float] = None
    gross_sales_price: Optional[float] = None
    total_revenue: Optional[float] = None
    compensation_officers_directors: Optional[float] = None
    other_employee_salaries: Optional[float] = None
    pension_plans_benefits: Optional[float] = None
    legal_fees: Optional[float] = None
    accounting_fees: Optional[float] = None
    other_professional_fees: Optional[float] = None
    interest_expense: Optional[float] = None
    taxes: Optional[float] = None
    other_expenses: Optional[float] = None
    total_operating_expenses: Optional[float] = None
    cash_non_interest_bearing: Optional[float] = None
    savings_temporary_investments: Optional[float] = None
    accounts_receivable: Optional[float] = None
    pledges_receivable: Optional[float] = None
    grants_receivable: Optional[float] = None
    investments_corporate_stock: Optional[float] = None
    investments_corporate_bonds: Optional[float] = None
    total_assets: Optional[float] = None
    accounts_payable: Optional[float] = None
    grants_payable: Optional[float] = None
    total_liabilities: Optional[float] = None
    net_assets: Optional[float] = None


@dataclass
class XML990PFFileMetadata:
    """XML file processing metadata."""
    ein: str
    object_id: str
    file_path: str
    file_size_bytes: int = 0
    download_timestamp: str = ""
    tax_year: int = 0
    form_type: str = "990-PF"
    xml_namespaces: List[str] = field(default_factory=list)
    parsing_success: bool = False
    parsing_errors: List[str] = field(default_factory=list)
    schema_validation_passed: bool = False


@dataclass
class XML990PFExecutionMetadata:
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
    total_investments_extracted: int = 0
    parsing_errors: int = 0
    download_errors: int = 0


@dataclass
class XML990PFQualityAssessment:
    """Quality assessment."""
    overall_success_rate: float
    schema_validation_rate: float
    officer_data_completeness: float
    grant_data_completeness: float
    investment_data_completeness: float
    financial_data_completeness: float
    governance_data_completeness: float
    data_freshness_score: float
    limitation_notes: List[str] = field(default_factory=list)


@dataclass
class XML990PFResult:
    """Complete XML 990-PF parsing result - Factor 4 structured output."""
    officers: List[FoundationOfficer]
    grants_paid: List[FoundationGrant]
    investment_holdings: List[InvestmentHolding]
    excise_tax_data: List[ExciseTaxData]
    payout_requirements: List[PayoutRequirement]
    governance_indicators: List[FoundationGovernance]
    financial_summaries: List[Foundation990PFFinancialSummary]
    xml_files_processed: List[XML990PFFileMetadata]
    execution_metadata: XML990PFExecutionMetadata
    quality_assessment: XML990PFQualityAssessment
    tool_name: str = "XML 990-PF Parser Tool"
    framework_compliance: str = "Human Layer 12-Factor Agents"
    factor_4_implementation: str = "Tools as Structured Outputs - eliminates XML parsing errors"
    form_type_specialization: str = "990-PF Forms Only - Private Foundations"
    organizations_processed: int = 0
    officers_extracted: int = 0
    grants_extracted: int = 0
    investments_extracted: int = 0
    extraction_failures: int = 0


class XML990PFParserTool:
    """
    XML 990-PF Parser Tool - 12-Factor Agents Implementation

    Single Responsibility: XML download and 990-PF form parsing for private foundations
    Strict schema validation ensures only 990-PF forms are processed
    """

    def __init__(self):
        self.tool_name = "XML 990-PF Parser Tool"
        self.version = "1.0.0"
        self.form_specialization = "990-PF"

        # Cache configuration (specialized for 990-PF forms)
        self.cache_dir = Path("cache/xml_filings_990pf")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # ProPublica endpoints (from existing infrastructure)
        self.propublica_base = "https://projects.propublica.org/nonprofits"

        # Download configuration
        self.max_concurrent_downloads = 3
        self.download_timeout = 60
        self.max_retries = 2
        self.retry_delay = 5.0

    async def execute(self, criteria: XML990PFParseCriteria) -> XML990PFResult:
        """
        Execute XML 990-PF parsing with guaranteed structured output.

        Factor 4 Implementation: Always returns XML990PFResult with structured data
        """
        start_time = time.time()

        # Initialize result structure
        result = XML990PFResult(
            officers=[],
            grants_paid=[],
            investment_holdings=[],
            excise_tax_data=[],
            payout_requirements=[],
            governance_indicators=[],
            financial_summaries=[],
            xml_files_processed=[],
            execution_metadata=XML990PFExecutionMetadata(
                execution_time_ms=0.0,
                organizations_processed=0,
                parsing_errors=0,
                download_errors=0
            ),
            quality_assessment=XML990PFQualityAssessment(
                overall_success_rate=0.0,
                schema_validation_rate=0.0,
                officer_data_completeness=0.0,
                grant_data_completeness=0.0,
                investment_data_completeness=0.0,
                financial_data_completeness=0.0,
                governance_data_completeness=0.0,
                data_freshness_score=0.0
            )
        )

        try:
            print(f"Starting XML 990-PF parsing for {len(criteria.target_eins)} organizations")
            print(f"Form specialization: {self.form_specialization} (Private Foundations Only)")
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
            result.grants_extracted = len(result.grants_paid)
            result.investments_extracted = len(result.investment_holdings)
            result.execution_metadata.total_officers_extracted = result.officers_extracted
            result.execution_metadata.total_grants_extracted = result.grants_extracted
            result.execution_metadata.total_investments_extracted = result.investments_extracted

            # Calculate cache hit rate
            total_cache_operations = result.execution_metadata.cache_hits + result.execution_metadata.cache_misses
            if total_cache_operations > 0:
                result.execution_metadata.cache_hit_rate = result.execution_metadata.cache_hits / total_cache_operations

            # Generate quality assessment
            result.quality_assessment = self._assess_quality(result)

            print(f"XML 990-PF parsing completed:")
            print(f"   Organizations processed: {result.organizations_processed}")
            print(f"   XML files processed: {len(result.xml_files_processed)}")
            print(f"   Officers extracted: {result.officers_extracted}")
            print(f"   Grants extracted: {result.grants_extracted}")
            print(f"   Investments extracted: {result.investments_extracted}")
            print(f"   Schema validation rate: {result.quality_assessment.schema_validation_rate:.1%}")
            print(f"   Cache hit rate: {result.execution_metadata.cache_hit_rate:.1%}")
            print(f"   Execution time: {result.execution_metadata.execution_time_ms:.1f}ms")

            return result

        except Exception as e:
            print(f"Critical error in XML 990-PF parsing: {e}")
            # Factor 4: Even on critical error, return structured result
            result.execution_metadata.execution_time_ms = (time.time() - start_time) * 1000
            result.quality_assessment.limitation_notes.append(f"Critical error: {str(e)}")
            return result

    async def _process_single_organization(
        self,
        ein: str,
        criteria: XML990PFParseCriteria,
        result: XML990PFResult
    ) -> None:
        """Process XML 990-PF data for a single organization."""

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

    async def _download_xml_for_organization(self, ein: str, result: XML990PFResult) -> List[Path]:
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
        result: XML990PFResult
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
        criteria: XML990PFParseCriteria,
        result: XML990PFResult
    ) -> None:
        """Parse XML file and extract Form 990-PF data."""

        try:
            # Create file metadata
            file_metadata = XML990PFFileMetadata(
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

            # Validate this is a 990-PF form (not 990 or 990-EZ)
            file_metadata.form_type = self._extract_form_type(root)
            file_metadata.schema_validation_passed = self._validate_990pf_schema(root, criteria.validate_990pf_schema)

            if criteria.validate_990pf_schema and not file_metadata.schema_validation_passed:
                print(f"   SKIPPING: {file_path.name} is not a Form 990-PF (detected: {file_metadata.form_type})")
                file_metadata.parsing_errors.append(f"Not a Form 990-PF: {file_metadata.form_type}")
                result.execution_metadata.schema_validation_failures += 1
                result.xml_files_processed.append(file_metadata)
                return

            # Extract tax year
            file_metadata.tax_year = self._extract_tax_year(root)

            print(f"   Parsing XML: {file_path.name} ({file_metadata.tax_year} {file_metadata.form_type})")

            # Extract data based on criteria
            parsing_success = True

            if "officers" in criteria.schedules_to_extract:
                officers = self._extract_990pf_officers(root, ein, file_metadata.tax_year)
                result.officers.extend(officers)
                if officers:
                    print(f"     Officers: {len(officers)} extracted")

            if "grants_paid" in criteria.schedules_to_extract:
                grants = self._extract_990pf_grants(root, ein, file_metadata.tax_year)
                result.grants_paid.extend(grants)
                if grants:
                    print(f"     Grants: {len(grants)} extracted")

            if "investments" in criteria.schedules_to_extract:
                investments = self._extract_990pf_investments(root, ein, file_metadata.tax_year)
                result.investment_holdings.extend(investments)
                if investments:
                    print(f"     Investments: {len(investments)} extracted")

            if "excise_tax" in criteria.schedules_to_extract:
                excise_tax = self._extract_excise_tax_data(root, ein, file_metadata.tax_year)
                if excise_tax:
                    result.excise_tax_data.append(excise_tax)
                    print(f"     Excise tax: data extracted")

            if "payout_requirements" in criteria.schedules_to_extract:
                payout = self._extract_payout_requirements(root, ein, file_metadata.tax_year)
                if payout:
                    result.payout_requirements.append(payout)
                    print(f"     Payout requirements: data extracted")

            # Always extract governance and financial summaries
            governance = self._extract_foundation_governance(root, ein, file_metadata.tax_year)
            if governance:
                result.governance_indicators.append(governance)
                print(f"     Governance: indicators extracted")

            financials = self._extract_990pf_financial_summary(root, ein, file_metadata.tax_year)
            if financials:
                result.financial_summaries.append(financials)
                print(f"     Financials: summary extracted")

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

            # Check for IRS990PF element (990-PF form) - try multiple paths
            irs990pf_paths = ['.//IRS990PF', f'.//{ns}IRS990PF', './/ReturnData/IRS990PF', f'.//{ns}ReturnData/{ns}IRS990PF']
            for path in irs990pf_paths:
                if root.find(path) is not None:
                    return "990-PF"

            # Check for other form types for validation
            irs990_paths = ['.//IRS990', f'.//{ns}IRS990', './/ReturnData/IRS990', f'.//{ns}ReturnData/{ns}IRS990']
            for path in irs990_paths:
                if root.find(path) is not None:
                    return "990"

            irs990ez_paths = ['.//IRS990EZ', f'.//{ns}IRS990EZ', './/ReturnData/IRS990EZ', f'.//{ns}ReturnData/{ns}IRS990EZ']
            for path in irs990ez_paths:
                if root.find(path) is not None:
                    return "990-EZ"

            # Fallback: check all elements for form type indicators
            for elem in root.iter():
                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if tag_name == 'IRS990PF':
                    return "990-PF"
                elif tag_name == 'IRS990':
                    return "990"
                elif tag_name == 'IRS990EZ':
                    return "990-EZ"

        except Exception as e:
            print(f"Error detecting form type: {e}")

        return "Unknown"

    def _validate_990pf_schema(self, root: ET.Element, validate: bool) -> bool:
        """Validate that this is actually a Form 990-PF (not 990 or 990-EZ)."""
        if not validate:
            return True

        form_type = self._extract_form_type(root)
        return form_type == "990-PF"

    def _extract_990pf_officers(self, root: ET.Element, ein: str, tax_year: int) -> List[FoundationOfficer]:
        """Extract Form 990-PF Part VIII officers and foundation managers."""
        officers = []

        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Look for OfcrDirTrstKeyEmplGrp elements (990-PF specific)
            officer_elements = []

            # Try different search strategies
            if ns:
                officer_elements = root.findall(f'.//{ns}OfcrDirTrstKeyEmplGrp')

            if not officer_elements:
                officer_elements = root.findall('.//OfcrDirTrstKeyEmplGrp')

            # Final fallback: search within IRS990PF element
            if not officer_elements:
                irs990pf_elem = None
                if ns:
                    irs990pf_elem = root.find(f'.//{ns}IRS990PF')
                if irs990pf_elem is None:
                    irs990pf_elem = root.find('.//IRS990PF')

                if irs990pf_elem is not None:
                    if ns:
                        officer_elements = irs990pf_elem.findall(f'.//{ns}OfcrDirTrstKeyEmplGrp')
                    if not officer_elements:
                        officer_elements = irs990pf_elem.findall('.//OfcrDirTrstKeyEmplGrp')

            for officer_elem in officer_elements:
                try:
                    person_name = self._get_element_text(officer_elem, ".//PersonNm")
                    title = self._get_element_text(officer_elem, ".//TitleTxt")

                    if person_name:
                        officer = FoundationOfficer(
                            ein=ein,
                            person_name=person_name,
                            title=title or "Unknown",
                            average_hours_per_week=self._get_element_float(officer_elem, ".//AverageHoursPerWeekRt"),
                            compensation=self._get_element_float(officer_elem, ".//CompensationAmt"),
                            employee_benefit_program=self._get_element_bool(officer_elem, ".//EmployeeBenefitProgramAmt"),
                            expense_account_allowance=self._get_element_float(officer_elem, ".//ExpenseAccountOtherAllwncAmt"),
                            is_officer=self._get_element_bool(officer_elem, ".//OfficerInd") or False,
                            is_director=self._get_element_bool(officer_elem, ".//DirectorOrTrusteeInd") or False,
                            tax_year=tax_year
                        )
                        officers.append(officer)

                except Exception as e:
                    continue

        except Exception as e:
            print(f"     Error extracting officers: {e}")

        return officers

    def _extract_990pf_grants(self, root: ET.Element, ein: str, tax_year: int) -> List[FoundationGrant]:
        """Extract grants paid from Form 990-PF Part XV."""
        grants = []

        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Look for grant elements in Part XV
            grant_elements = []

            # Try different search patterns for 990-PF grants
            grant_paths = [
                './/GrantOrContributionPdGrp',
                './/SupplementaryInformationGrp',
                './/GrantOrContribution'
            ]

            for path in grant_paths:
                if ns:
                    elements = root.findall(f'.//{ns}{path[3:]}')  # Remove './' and add namespace
                else:
                    elements = root.findall(path)

                if elements:
                    grant_elements.extend(elements)

            for grant_elem in grant_elements[:20]:  # Limit to 20 grants
                try:
                    recipient_name = self._get_element_text(grant_elem, ".//RecipientPersonNm", ".//RecipientBusinessName", ".//RecipientName")
                    amount = self._get_element_float(grant_elem, ".//Amt", ".//Amount", ".//GrantOrContributionAmt")

                    if recipient_name and amount:
                        grant = FoundationGrant(
                            ein=ein,
                            recipient_name=recipient_name,
                            recipient_type=self._get_element_text(grant_elem, ".//RecipientTypeTxt"),
                            recipient_address=self._get_element_text(grant_elem, ".//RecipientUSAddress", ".//RecipientAddress"),
                            recipient_relationship=self._get_element_text(grant_elem, ".//RecipientRlnTxt"),
                            grant_amount=amount,
                            grant_purpose=self._get_element_text(grant_elem, ".//GrantOrContributionPurposeTxt", ".//PurposeTxt"),
                            foundation_status_of_recipient=self._get_element_text(grant_elem, ".//FoundationStatusTxt"),
                            tax_year=tax_year
                        )
                        grants.append(grant)

                except Exception as e:
                    continue

        except Exception as e:
            print(f"     Error extracting grants: {e}")

        return grants

    def _extract_990pf_investments(self, root: ET.Element, ein: str, tax_year: int) -> List[InvestmentHolding]:
        """Extract investment holdings from Form 990-PF Part II."""
        investments = []

        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Look for investment elements in Part II
            investment_paths = [
                './/InvestmentsCorpStockGrp',
                './/InvestmentsCorpBondGrp',
                './/InvestmentsOtherGrp',
                './/AssetGrp'
            ]

            for path in investment_paths:
                elements = []
                if ns:
                    elements = root.findall(f'.//{ns}{path[3:]}')  # Remove './' and add namespace
                else:
                    elements = root.findall(path)

                for investment_elem in elements[:10]:  # Limit to 10 per category
                    try:
                        description = self._get_element_text(investment_elem, ".//Desc", ".//InvestmentDescription")
                        book_value = self._get_element_float(investment_elem, ".//BookValueAmt")
                        fair_market_value = self._get_element_float(investment_elem, ".//FairMarketValueAmt")

                        if description or book_value or fair_market_value:
                            # Determine investment category from the path
                            category = "Unknown"
                            if "CorpStock" in path:
                                category = "Corporate Stock"
                            elif "CorpBond" in path:
                                category = "Corporate Bonds"
                            elif "Other" in path:
                                category = "Other Investments"

                            investment = InvestmentHolding(
                                ein=ein,
                                tax_year=tax_year,
                                investment_type=category,
                                book_value=book_value,
                                fair_market_value=fair_market_value,
                                investment_description=description,
                                investment_category=category
                            )
                            investments.append(investment)

                    except Exception as e:
                        continue

        except Exception as e:
            print(f"     Error extracting investments: {e}")

        return investments

    def _extract_excise_tax_data(self, root: ET.Element, ein: str, tax_year: int) -> Optional[ExciseTaxData]:
        """Extract excise tax computation from Form 990-PF Part VI."""
        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Find the IRS990PF element
            irs990pf_elem = None
            if ns:
                irs990pf_elem = root.find(f'.//{ns}IRS990PF')
            if irs990pf_elem is None:
                irs990pf_elem = root.find('.//IRS990PF')

            if irs990pf_elem is None:
                return None

            excise_tax = ExciseTaxData(
                ein=ein,
                tax_year=tax_year,
                net_investment_income=self._get_element_float(irs990pf_elem, ".//NetInvestmentIncomeAmt"),
                excise_tax_owed=self._get_element_float(irs990pf_elem, ".//ExciseTaxBasedOnInvstIncmAmt"),
                qualifying_distributions_made=self._get_element_float(irs990pf_elem, ".//QualifyingDistributionsAmt")
            )

            return excise_tax

        except Exception as e:
            print(f"     Error extracting excise tax: {e}")
            return None

    def _extract_payout_requirements(self, root: ET.Element, ein: str, tax_year: int) -> Optional[PayoutRequirement]:
        """Extract payout requirements from Form 990-PF Part XII."""
        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Find the IRS990PF element
            irs990pf_elem = None
            if ns:
                irs990pf_elem = root.find(f'.//{ns}IRS990PF')
            if irs990pf_elem is None:
                irs990pf_elem = root.find('.//IRS990PF')

            if irs990pf_elem is None:
                return None

            payout = PayoutRequirement(
                ein=ein,
                tax_year=tax_year,
                average_monthly_fair_market_value=self._get_element_float(irs990pf_elem, ".//AverageMonthlyFMVOfSecAmt"),
                minimum_investment_return=self._get_element_float(irs990pf_elem, ".//MinimumInvestmentReturnAmt"),
                distributable_amount=self._get_element_float(irs990pf_elem, ".//DistributableAmountAmt"),
                qualifying_distributions_made=self._get_element_float(irs990pf_elem, ".//QualifyingDistributionsAmt"),
                underdistributions=self._get_element_float(irs990pf_elem, ".//UnderdistributionsAmt")
            )

            return payout

        except Exception as e:
            print(f"     Error extracting payout requirements: {e}")
            return None

    def _extract_foundation_governance(self, root: ET.Element, ein: str, tax_year: int) -> Optional[FoundationGovernance]:
        """Extract foundation governance indicators."""
        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Find the IRS990PF element
            irs990pf_elem = None
            if ns:
                irs990pf_elem = root.find(f'.//{ns}IRS990PF')
            if irs990pf_elem is None:
                irs990pf_elem = root.find('.//IRS990PF')

            if irs990pf_elem is None:
                return None

            governance = FoundationGovernance(
                ein=ein,
                tax_year=tax_year,
                operating_foundation=self._get_element_bool(irs990pf_elem, ".//OperatingFoundationInd"),
                private_foundation_status=self._get_element_bool(irs990pf_elem, ".//PrivateFoundationInd"),
                compensation_policy=self._get_element_bool(irs990pf_elem, ".//CompensationPolicyInd"),
                conflict_of_interest_policy=self._get_element_bool(irs990pf_elem, ".//ConflictOfInterestPolicyInd"),
                minutes_of_governing_body=self._get_element_bool(irs990pf_elem, ".//MinutesOfGoverningBodyInd"),
                independent_audit=self._get_element_bool(irs990pf_elem, ".//IndependentAuditFinclStmtInd")
            )

            return governance

        except Exception as e:
            print(f"     Error extracting governance: {e}")
            return None

    def _extract_990pf_financial_summary(self, root: ET.Element, ein: str, tax_year: int) -> Optional[Foundation990PFFinancialSummary]:
        """Extract financial summary from Form 990-PF."""
        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Find the IRS990PF element
            irs990pf_elem = None
            if ns:
                irs990pf_elem = root.find(f'.//{ns}IRS990PF')
            if irs990pf_elem is None:
                irs990pf_elem = root.find('.//IRS990PF')

            if irs990pf_elem is None:
                return None

            financial = Foundation990PFFinancialSummary(
                ein=ein,
                tax_year=tax_year,
                contributions_received=self._get_element_float(irs990pf_elem, ".//ContributionsRcvdAmt"),
                interest_dividends_received=self._get_element_float(irs990pf_elem, ".//InterestOnSavingsAmt", ".//DividendsAndInterestFromSecAmt"),
                total_revenue=self._get_element_float(irs990pf_elem, ".//TotalRevenueAmt"),
                compensation_officers_directors=self._get_element_float(irs990pf_elem, ".//CompOfcrDirTrstKeyEmplAmt"),
                other_employee_salaries=self._get_element_float(irs990pf_elem, ".//OtherEmployeeSalariesAmt"),
                legal_fees=self._get_element_float(irs990pf_elem, ".//LegalFeesAmt"),
                accounting_fees=self._get_element_float(irs990pf_elem, ".//AccountingFeesAmt"),
                total_operating_expenses=self._get_element_float(irs990pf_elem, ".//TotalOperatingExpensesAmt"),
                total_assets=self._get_element_float(irs990pf_elem, ".//TotalAssetsAmt"),
                total_liabilities=self._get_element_float(irs990pf_elem, ".//TotalLiabilitiesAmt"),
                net_assets=self._get_element_float(irs990pf_elem, ".//NetAssetsOrFundBalancesAmt")
            )

            return financial

        except Exception as e:
            print(f"     Error extracting financials: {e}")
            return None

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

    def _assess_quality(self, result: XML990PFResult) -> XML990PFQualityAssessment:
        """Assess the quality of the XML 990-PF parsing results."""

        if result.organizations_processed == 0:
            return XML990PFQualityAssessment(
                overall_success_rate=0.0,
                schema_validation_rate=0.0,
                officer_data_completeness=0.0,
                grant_data_completeness=0.0,
                investment_data_completeness=0.0,
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
            total_fields = 0
            filled_fields = 0
            for officer in result.officers:
                total_fields += 6  # Key fields
                filled_fields += sum(1 for field in [
                    officer.person_name, officer.title, officer.compensation,
                    officer.is_officer, officer.is_director, officer.average_hours_per_week
                ] if field is not None and field != "Unknown")
            officer_completeness = filled_fields / max(total_fields, 1)

        grant_completeness = 0.0
        if result.grants_paid:
            total_fields = 0
            filled_fields = 0
            for grant in result.grants_paid:
                total_fields += 4  # Key fields
                filled_fields += sum(1 for field in [
                    grant.recipient_name, grant.grant_amount, grant.grant_purpose, grant.recipient_type
                ] if field is not None)
            grant_completeness = filled_fields / max(total_fields, 1)

        investment_completeness = 0.0
        if result.investment_holdings:
            total_fields = 0
            filled_fields = 0
            for investment in result.investment_holdings:
                total_fields += 4  # Key fields
                filled_fields += sum(1 for field in [
                    investment.investment_description, investment.book_value,
                    investment.fair_market_value, investment.investment_category
                ] if field is not None)
            investment_completeness = filled_fields / max(total_fields, 1)

        financial_completeness = 0.0
        if result.financial_summaries:
            for summary in result.financial_summaries:
                fields_count = 8  # Key financial fields
                filled_count = sum(1 for field in [
                    summary.total_revenue, summary.total_operating_expenses,
                    summary.total_assets, summary.net_assets,
                    summary.contributions_received, summary.compensation_officers_directors
                ] if field is not None)
                financial_completeness += filled_count / fields_count
            financial_completeness /= len(result.financial_summaries)

        governance_completeness = 0.0
        if result.governance_indicators:
            for governance in result.governance_indicators:
                fields_count = 6  # Key governance fields
                filled_count = sum(1 for field in [
                    governance.operating_foundation, governance.private_foundation_status,
                    governance.conflict_of_interest_policy, governance.minutes_of_governing_body,
                    governance.independent_audit, governance.compensation_policy
                ] if field is not None)
                governance_completeness += filled_count / fields_count
            governance_completeness /= len(result.governance_indicators)

        limitation_notes = []
        if result.execution_metadata.parsing_errors > 0:
            limitation_notes.append(f"{result.execution_metadata.parsing_errors} XML parsing errors")
        if schema_validation_failures > 0:
            limitation_notes.append(f"{schema_validation_failures} files rejected (not Form 990-PF)")
        if result.execution_metadata.download_errors > 0:
            limitation_notes.append(f"{result.execution_metadata.download_errors} XML download errors")

        return XML990PFQualityAssessment(
            overall_success_rate=overall_success_rate,
            schema_validation_rate=schema_validation_rate,
            officer_data_completeness=officer_completeness,
            grant_data_completeness=grant_completeness,
            investment_data_completeness=investment_completeness,
            financial_data_completeness=financial_completeness,
            governance_data_completeness=governance_completeness,
            data_freshness_score=0.8,  # Assume reasonably fresh for now
            limitation_notes=limitation_notes
        )


# Test function for a foundation EIN (would need an actual 990-PF filing)
async def test_xml_990pf_parser():
    """Test the XML 990-PF parser tool with a foundation."""

    print("Testing XML 990-PF Parser Tool")
    print("=" * 60)

    # Initialize tool
    tool = XML990PFParserTool()

    # Create test criteria
    criteria = XML990PFParseCriteria(
        target_eins=["131624165"],  # Example foundation EIN (Gates Foundation)
        schedules_to_extract=["officers", "grants_paid", "investments", "excise_tax", "payout_requirements"],
        cache_enabled=True,
        max_years_back=5,
        download_if_missing=True,
        validate_990pf_schema=True  # Strict validation
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
            validation = "VALID 990-PF" if xml_file.schema_validation_passed else f"INVALID ({xml_file.form_type})"
            print(f"  {xml_file.tax_year} {xml_file.form_type}: {xml_file.file_size_bytes:,} bytes - {status} - {validation}")

    if result.officers:
        print(f"\nOfficers Extracted ({len(result.officers)}):")
        for officer in result.officers[:5]:  # Show first 5
            comp = f"${officer.compensation:,.0f}" if officer.compensation else "$0"
            hours = f"{officer.average_hours_per_week}hrs/wk" if officer.average_hours_per_week else "N/A"
            print(f"  {officer.person_name}: {officer.title} ({hours}, {comp})")

    if result.grants_paid:
        print(f"\nGrants Paid ({len(result.grants_paid)}):")
        for grant in result.grants_paid[:5]:  # Show first 5
            print(f"  {grant.recipient_name}: ${grant.grant_amount:,.0f}")

    if result.investment_holdings:
        print(f"\nInvestment Holdings ({len(result.investment_holdings)}):")
        for investment in result.investment_holdings[:3]:  # Show first 3
            fmv = f"${investment.fair_market_value:,.0f}" if investment.fair_market_value else "N/A"
            print(f"  {investment.investment_category}: {fmv}")

    print(f"\nExecution Metadata:")
    print(f"  Execution time: {result.execution_metadata.execution_time_ms:.1f}ms")
    print(f"  Cache hit rate: {result.execution_metadata.cache_hit_rate:.1%}")
    print(f"  Schema validation rate: {result.quality_assessment.schema_validation_rate:.1%}")
    print(f"  Parsing errors: {result.execution_metadata.parsing_errors}")

    print(f"\nQuality Assessment:")
    print(f"  Overall success: {result.quality_assessment.overall_success_rate:.1%}")
    print(f"  Officer completeness: {result.quality_assessment.officer_data_completeness:.2f}")
    print(f"  Grant completeness: {result.quality_assessment.grant_data_completeness:.2f}")
    print(f"  Investment completeness: {result.quality_assessment.investment_data_completeness:.2f}")
    print(f"  Financial completeness: {result.quality_assessment.financial_data_completeness:.2f}")

    return result


if __name__ == "__main__":
    asyncio.run(test_xml_990pf_parser())