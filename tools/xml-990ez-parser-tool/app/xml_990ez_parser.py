#!/usr/bin/env python3
"""
XML 990-EZ Parser Tool - 12-Factor Agents Implementation
Human Layer Framework - Factor 4: Tools as Structured Outputs

Single Responsibility: XML download and 990-EZ form schedule parsing for SMALL ORGANIZATIONS ONLY
- Object_id discovery from ProPublica pages
- Direct XML download with intelligent caching
- Form 990-EZ officer, revenue, expense, and balance sheet data extraction
- Strict 990-EZ schema validation (rejects 990 and 990-PF forms)
- NO regular nonprofit analysis (handled by separate 990 tool)
- NO foundation analysis (handled by separate 990-PF tool)
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

print("XML 990-EZ Parser Tool initializing...")


@dataclass
class XML990EZParseCriteria:
    """Input criteria for XML 990-EZ parsing following Factor 4 principles."""
    target_eins: List[str]
    schedules_to_extract: List[str] = field(default_factory=lambda: ["officers", "revenue", "expenses", "balance_sheet", "public_support"])
    cache_enabled: bool = True
    max_years_back: int = 5
    download_if_missing: bool = True
    validate_990ez_schema: bool = True


@dataclass
class SmallOrgOfficer:
    """Form 990-EZ Part V - Officers, Directors, Trustees, Key Employees."""
    ein: str
    person_name: str
    title: str
    average_hours_per_week: Optional[float] = None
    compensation: Optional[float] = None
    is_officer: bool = False
    is_director: bool = False
    is_trustee: bool = False
    is_key_employee: bool = False
    tax_year: int = 0
    data_source: str = "Form 990-EZ XML"


@dataclass
class Form990EZRevenue:
    """Form 990-EZ Part I - Revenue breakdown."""
    ein: str
    tax_year: int
    contributions_gifts_grants: Optional[float] = None
    program_service_revenue: Optional[float] = None
    membership_dues_assessments: Optional[float] = None
    investment_income: Optional[float] = None
    gross_amount_from_sale_assets: Optional[float] = None
    special_events_gross_revenue: Optional[float] = None
    special_events_direct_expenses: Optional[float] = None
    special_events_net_income: Optional[float] = None
    gross_sales_inventory: Optional[float] = None
    cost_goods_sold: Optional[float] = None
    gross_profit_loss_inventory: Optional[float] = None
    other_revenue: Optional[float] = None
    total_revenue: Optional[float] = None


@dataclass
class Form990EZExpenses:
    """Form 990-EZ Part I - Expenses breakdown."""
    ein: str
    tax_year: int
    grants_similar_amounts_paid: Optional[float] = None
    benefits_paid_members: Optional[float] = None
    salaries_wages_benefits: Optional[float] = None
    professional_fees: Optional[float] = None
    occupancy_rent_utilities: Optional[float] = None
    printing_publications_postage: Optional[float] = None
    other_expenses: Optional[float] = None
    total_expenses: Optional[float] = None
    excess_deficit_current_year: Optional[float] = None


@dataclass
class Form990EZBalanceSheet:
    """Form 990-EZ Part II - Balance Sheet."""
    ein: str
    tax_year: int
    cash_savings_investments_boy: Optional[float] = None
    cash_savings_investments_eoy: Optional[float] = None
    land_buildings_boy: Optional[float] = None
    land_buildings_eoy: Optional[float] = None
    other_assets_boy: Optional[float] = None
    other_assets_eoy: Optional[float] = None
    total_assets_boy: Optional[float] = None
    total_assets_eoy: Optional[float] = None
    total_liabilities_boy: Optional[float] = None
    total_liabilities_eoy: Optional[float] = None
    net_assets_boy: Optional[float] = None
    net_assets_eoy: Optional[float] = None


@dataclass
class PublicSupportData:
    """Form 990-EZ Part VI - Public Support Test."""
    ein: str
    tax_year: int
    total_support: Optional[float] = None
    gross_receipts_related_activities: Optional[float] = None
    first_five_years_support: Optional[float] = None
    public_support_percentage: Optional[float] = None
    public_charity_status: Optional[bool] = None
    gifts_grants_contributions: Optional[float] = None
    membership_fees_received: Optional[float] = None
    gross_receipts_admissions: Optional[float] = None
    gross_receipts_merchandise: Optional[float] = None
    gross_receipts_other: Optional[float] = None


@dataclass
class ProgramAccomplishment:
    """Form 990-EZ Part III - Program Accomplishments."""
    ein: str
    tax_year: int
    accomplishment_number: int
    description: Optional[str] = None
    expense_amount: Optional[float] = None


@dataclass
class SmallOrgOperations:
    """Small organization operations summary."""
    ein: str
    tax_year: int
    organization_type: Optional[str] = None
    formation_year: Optional[int] = None
    activity_codes: List[str] = field(default_factory=list)
    significant_change_activities: Optional[bool] = None
    unrelated_business_income: Optional[bool] = None
    organization_dissolved: Optional[bool] = None
    gross_receipts_normally_not_more_50k: Optional[bool] = None
    total_assets_less_than_25k: Optional[bool] = None


@dataclass
class XML990EZFileMetadata:
    """XML file processing metadata for 990-EZ."""
    ein: str
    object_id: str
    file_path: str
    file_size_bytes: int
    download_timestamp: str
    tax_year: int
    form_type: str
    xml_namespaces: List[str] = field(default_factory=list)
    parsing_success: bool = False
    parsing_errors: List[str] = field(default_factory=list)
    schema_validation_passed: bool = False


@dataclass
class XML990EZExecutionMetadata:
    """Execution metadata for 990-EZ processing."""
    execution_time_ms: float = 0.0
    organizations_processed: int = 0
    xml_files_found: int = 0
    xml_files_downloaded: int = 0
    xml_files_parsed: int = 0
    schema_validation_failures: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0
    total_officers_extracted: int = 0
    total_accomplishments_extracted: int = 0
    parsing_errors: int = 0
    download_errors: int = 0


@dataclass
class XML990EZQualityAssessment:
    """Quality assessment for 990-EZ parsing."""
    overall_success_rate: float = 0.0
    schema_validation_rate: float = 0.0
    officer_data_completeness: float = 0.0
    revenue_data_completeness: float = 0.0
    expense_data_completeness: float = 0.0
    balance_sheet_completeness: float = 0.0
    data_freshness_score: float = 0.0
    limitation_notes: List[str] = field(default_factory=list)


@dataclass
class XML990EZResult:
    """Complete XML 990-EZ parsing result - Factor 4 structured output."""
    officers: List[SmallOrgOfficer] = field(default_factory=list)
    revenue_data: List[Form990EZRevenue] = field(default_factory=list)
    expense_data: List[Form990EZExpenses] = field(default_factory=list)
    balance_sheets: List[Form990EZBalanceSheet] = field(default_factory=list)
    public_support_data: List[PublicSupportData] = field(default_factory=list)
    program_accomplishments: List[ProgramAccomplishment] = field(default_factory=list)
    operations_data: List[SmallOrgOperations] = field(default_factory=list)
    xml_files_processed: List[XML990EZFileMetadata] = field(default_factory=list)
    execution_metadata: XML990EZExecutionMetadata = field(default_factory=XML990EZExecutionMetadata)
    quality_assessment: XML990EZQualityAssessment = field(default_factory=XML990EZQualityAssessment)
    tool_name: str = "XML 990-EZ Parser Tool"
    framework_compliance: str = "Human Layer 12-Factor Agents"
    factor_4_implementation: str = "Tools as Structured Outputs - eliminates XML parsing errors"
    form_type_specialization: str = "990-EZ Forms Only - Small Organizations"
    organizations_processed: int = 0
    officers_extracted: int = 0
    accomplishments_extracted: int = 0
    extraction_failures: int = 0


class XML990EZParserTool:
    """
    XML 990-EZ Parser Tool - Factor 4 & 10 Compliance

    Factor 4: Tools as Structured Outputs
    - Returns XML990EZResult dataclass with predictable structure
    - Eliminates XML parsing errors through structured interfaces

    Factor 10: Small, Focused Agents
    - Single responsibility: 990-EZ forms only
    - Rejects 990 and 990-PF forms (handled by other tools)
    """

    def __init__(self):
        self.cache_dir = Path("tools/xml-990ez-parser-tool/cache/xml_filings_990ez")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self, criteria: XML990EZParseCriteria) -> XML990EZResult:
        """
        Execute XML 990-EZ parsing following Factor 4 principles.

        Returns structured XML990EZResult eliminating parsing errors.
        """
        start_time = time.time()
        result = XML990EZResult()

        print(f"Starting XML 990-EZ parsing for {len(criteria.target_eins)} organizations")
        print(f"Form specialization: 990-EZ (Small Organizations Only)")
        print(f"Schedules to extract: {', '.join(criteria.schedules_to_extract)}")

        for ein in criteria.target_eins:
            try:
                await self._process_single_organization(ein, criteria, result)
            except Exception as e:
                print(f"   Error processing {ein}: {e}")
                result.extraction_failures += 1

        # Finalize execution metadata
        execution_time = (time.time() - start_time) * 1000
        result.execution_metadata.execution_time_ms = execution_time
        result.execution_metadata.organizations_processed = len(criteria.target_eins)

        # Calculate cache hit rate
        total_requests = result.execution_metadata.cache_hits + result.execution_metadata.cache_misses
        if total_requests > 0:
            result.execution_metadata.cache_hit_rate = result.execution_metadata.cache_hits / total_requests

        # Calculate quality metrics
        result.quality_assessment.overall_success_rate = 1.0 - (result.extraction_failures / len(criteria.target_eins)) if criteria.target_eins else 0.0
        result.quality_assessment.schema_validation_rate = (result.execution_metadata.xml_files_parsed / result.execution_metadata.xml_files_found) if result.execution_metadata.xml_files_found > 0 else 0.0

        # Set summary counters
        result.organizations_processed = len(criteria.target_eins)
        result.officers_extracted = len(result.officers)
        result.accomplishments_extracted = len(result.program_accomplishments)

        print(f"XML 990-EZ parsing completed:")
        print(f"   Organizations processed: {result.organizations_processed}")
        print(f"   XML files processed: {result.execution_metadata.xml_files_parsed}")
        print(f"   Officers extracted: {result.officers_extracted}")
        print(f"   Accomplishments extracted: {result.accomplishments_extracted}")
        print(f"   Schema validation rate: {result.quality_assessment.schema_validation_rate:.1%}")
        print(f"   Cache hit rate: {result.execution_metadata.cache_hit_rate:.1%}")
        print(f"   Execution time: {execution_time:.1f}ms")

        return result

    async def _process_single_organization(
        self,
        ein: str,
        criteria: XML990EZParseCriteria,
        result: XML990EZResult
    ) -> None:
        """Process XML data for a single organization."""
        print(f"   Processing EIN: {ein}")

        # Check cache first
        xml_files = self._find_cached_xml_files(ein)
        if xml_files:
            result.execution_metadata.cache_hits += len(xml_files)
        else:
            result.execution_metadata.cache_misses += 1

        # Download if needed and allowed
        if not xml_files and criteria.download_if_missing:
            xml_files = await self._download_xml_for_organization(ein, result)

        if not xml_files:
            return

        # Process each XML file
        for xml_file in xml_files:
            await self._process_xml_file(xml_file, ein, criteria, result)

    def _find_cached_xml_files(self, ein: str) -> List[Path]:
        """Find cached XML files for an organization."""
        xml_files = []
        if self.cache_dir.exists():
            for file_path in self.cache_dir.glob(f"{ein}_*.xml"):
                xml_files.append(file_path)
        return sorted(xml_files, key=lambda x: x.name, reverse=True)  # Most recent first

    async def _download_xml_for_organization(self, ein: str, result: XML990EZResult) -> List[Path]:
        """Download XML files for an organization using ProPublica object_id methodology."""
        async with aiohttp.ClientSession() as session:
            object_id = await self._find_object_id(session, ein)
            if not object_id:
                print(f"   No XML download link found for {ein}")
                result.execution_metadata.download_errors += 1
                return []

            xml_url = f"https://projects.propublica.org/nonprofits/download-xml/{object_id}"

            try:
                async with session.get(xml_url) as response:
                    if response.status == 200:
                        content = await response.read()

                        # Save to cache
                        filename = f"{ein}_{object_id}.xml"
                        file_path = self.cache_dir / filename

                        async with aiofiles.open(file_path, 'wb') as f:
                            await f.write(content)

                        print(f"   Downloaded XML for {ein} ({len(content):,} bytes)")
                        result.execution_metadata.xml_files_downloaded += 1
                        return [file_path]
                    else:
                        print(f"   Failed to download XML for {ein}: HTTP {response.status}")
                        result.execution_metadata.download_errors += 1
                        return []
            except Exception as e:
                print(f"   Download error for {ein}: {e}")
                result.execution_metadata.download_errors += 1
                return []

    async def _find_object_id(self, session: aiohttp.ClientSession, ein: str) -> Optional[str]:
        """Find ProPublica object_id for an organization."""
        try:
            url = f"https://projects.propublica.org/nonprofits/organizations/{ein}"
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Look for XML download link
                    xml_link = soup.find('a', string='Download XML')
                    if xml_link and xml_link.get('href'):
                        href = xml_link.get('href')
                        # Extract object_id from /download-xml/{object_id}
                        if '/download-xml/' in href:
                            return href.split('/download-xml/')[-1]
                    return None
                else:
                    return None
        except Exception:
            return None

    async def _process_xml_file(
        self,
        xml_file: Path,
        ein: str,
        criteria: XML990EZParseCriteria,
        result: XML990EZResult
    ) -> None:
        """Process a single XML file."""
        try:
            # Parse XML
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Extract tax year and validate form type
            tax_year = self._extract_tax_year(root)
            form_type = self._extract_form_type(root)

            # Create file metadata
            file_metadata = XML990EZFileMetadata(
                ein=ein,
                object_id=xml_file.stem.split('_')[-1] if '_' in xml_file.stem else "",
                file_path=str(xml_file),
                file_size_bytes=xml_file.stat().st_size,
                download_timestamp=datetime.now().isoformat(),
                tax_year=tax_year,
                form_type=form_type,
                xml_namespaces=self._extract_namespaces(root)
            )

            # Strict schema validation for 990-EZ
            if criteria.validate_990ez_schema and form_type != "990EZ":
                print(f"   SKIPPING: {xml_file.name} is not a Form 990-EZ (detected: {form_type})")
                file_metadata.schema_validation_passed = False
                result.execution_metadata.schema_validation_failures += 1
                result.xml_files_processed.append(file_metadata)
                return

            file_metadata.schema_validation_passed = True
            file_metadata.parsing_success = True
            result.execution_metadata.xml_files_found += 1
            result.execution_metadata.xml_files_parsed += 1

            print(f"   Parsing XML: {xml_file.name} ({tax_year} {form_type})")

            # Extract data based on schedules
            if "officers" in criteria.schedules_to_extract:
                officers = self._extract_990ez_officers(root, ein, tax_year)
                result.officers.extend(officers)
                if officers:
                    print(f"     Officers: {len(officers)} extracted")

            if "revenue" in criteria.schedules_to_extract:
                revenue = self._extract_990ez_revenue(root, ein, tax_year)
                if revenue:
                    result.revenue_data.append(revenue)
                    print(f"     Revenue: data extracted")

            if "expenses" in criteria.schedules_to_extract:
                expenses = self._extract_990ez_expenses(root, ein, tax_year)
                if expenses:
                    result.expense_data.append(expenses)
                    print(f"     Expenses: data extracted")

            if "balance_sheet" in criteria.schedules_to_extract:
                balance_sheet = self._extract_990ez_balance_sheet(root, ein, tax_year)
                if balance_sheet:
                    result.balance_sheets.append(balance_sheet)
                    print(f"     Balance sheet: data extracted")

            if "public_support" in criteria.schedules_to_extract:
                public_support = self._extract_990ez_public_support(root, ein, tax_year)
                if public_support:
                    result.public_support_data.append(public_support)
                    print(f"     Public support: data extracted")

            # Always extract program accomplishments and operations
            accomplishments = self._extract_990ez_accomplishments(root, ein, tax_year)
            result.program_accomplishments.extend(accomplishments)

            operations = self._extract_990ez_operations(root, ein, tax_year)
            if operations:
                result.operations_data.append(operations)

            result.xml_files_processed.append(file_metadata)

        except Exception as e:
            print(f"   Error parsing {xml_file.name}: {e}")
            result.execution_metadata.parsing_errors += 1

    def _extract_tax_year(self, root: ET.Element) -> int:
        """Extract tax year from XML."""
        # Handle namespace if present
        ns = ""
        if '}' in root.tag:
            ns = root.tag.split('}')[0] + '}'

        # Try multiple year element patterns
        year_elements = [
            f'.//{ns}TaxYr',
            f'.//{ns}TaxYear',
            f'.//{ns}ReturnTypeCd/../{ns}TaxYr'
        ]

        for xpath in year_elements:
            element = root.find(xpath)
            if element is not None and element.text:
                try:
                    return int(element.text)
                except ValueError:
                    continue

        return 2023  # Default fallback

    def _extract_form_type(self, root: ET.Element) -> str:
        """Extract and validate form type from XML."""
        # Handle namespace if present
        ns = ""
        if '}' in root.tag:
            ns = root.tag.split('}')[0] + '}'

        # Try multiple form type detection strategies
        form_patterns = [
            f'.//{ns}ReturnTypeCd',
            f'.//{ns}FormTypeCd',
            f'.//{ns}DocumentSystemId'
        ]

        for xpath in form_patterns:
            element = root.find(xpath)
            if element is not None and element.text:
                form_type = element.text.strip()
                if "990EZ" in form_type or "990-EZ" in form_type:
                    return "990EZ"
                elif "990PF" in form_type or "990-PF" in form_type:
                    return "990PF"
                elif "990" in form_type:
                    return "990"

        # Check for 990EZ-specific elements
        ez_specific_elements = [
            f'.//{ns}Form990EZPartI',
            f'.//{ns}TotalGrossReceiptsAmt',
            f'.//{ns}TotalAssetsEOYAmt'
        ]

        for xpath in ez_specific_elements:
            if root.find(xpath) is not None:
                return "990EZ"

        return "Unknown"

    def _extract_namespaces(self, root: ET.Element) -> List[str]:
        """Extract XML namespaces."""
        namespaces = []
        if '}' in root.tag:
            namespace = root.tag.split('}')[0] + '}'
            namespaces.append(namespace)
        return namespaces

    def _get_element_text(self, root: ET.Element, xpath: str, ns: str = "") -> Optional[str]:
        """Get text from XML element with namespace handling."""
        if ns and xpath.startswith('.//'):
            element_name = xpath[3:]  # Remove ".//"
            ns_xpath = f'.//{ns}{element_name}'
            element = root.find(ns_xpath)
        else:
            element = root.find(xpath)

        return element.text.strip() if element is not None and element.text else None

    def _get_element_float(self, root: ET.Element, xpath: str, ns: str = "") -> Optional[float]:
        """Get float value from XML element."""
        text = self._get_element_text(root, xpath, ns)
        if text:
            try:
                return float(text)
            except ValueError:
                return None
        return None

    def _extract_990ez_officers(self, root: ET.Element, ein: str, tax_year: int) -> List[SmallOrgOfficer]:
        """Extract officers from Form 990-EZ Part V."""
        officers = []

        # Handle namespace if present
        ns = ""
        if '}' in root.tag:
            ns = root.tag.split('}')[0] + '}'

        # Look for Form990EZPartVOfcrDirTrstKeyEmplGrp elements
        officer_elements = []
        if ns:
            officer_elements = root.findall(f'.//{ns}Form990EZPartVOfcrDirTrstKeyEmplGrp')

        # Fallback patterns for 990-EZ officers
        if not officer_elements:
            fallback_patterns = [
                f'.//{ns}OfcrDirTrstKeyEmplGrp',
                f'.//{ns}OfficerDirectorTrusteeGrp',
                f'.//{ns}OfficerGrp'
            ]

            for pattern in fallback_patterns:
                officer_elements = root.findall(pattern)
                if officer_elements:
                    break

        for officer_elem in officer_elements:
            try:
                name = self._get_element_text(officer_elem, f'.//{ns}PersonNm', ns) or \
                       self._get_element_text(officer_elem, f'.//PersonNm') or \
                       self._get_element_text(officer_elem, f'.//{ns}NamePerson', ns)

                title = self._get_element_text(officer_elem, f'.//{ns}TitleTxt', ns) or \
                        self._get_element_text(officer_elem, f'.//TitleTxt') or \
                        self._get_element_text(officer_elem, f'.//{ns}Title', ns)

                if name and title:
                    hours = self._get_element_float(officer_elem, f'.//{ns}AverageHrsPerWkDevotedToPosRt', ns) or \
                            self._get_element_float(officer_elem, f'.//AverageHrsPerWkDevotedToPosRt')

                    compensation = self._get_element_float(officer_elem, f'.//{ns}CompensationAmt', ns) or \
                                   self._get_element_float(officer_elem, f'.//CompensationAmt')

                    # Check for various officer types
                    is_officer = self._get_element_text(officer_elem, f'.//{ns}OfficerInd', ns) == 'X'
                    is_director = self._get_element_text(officer_elem, f'.//{ns}DirectorInd', ns) == 'X'
                    is_trustee = self._get_element_text(officer_elem, f'.//{ns}TrusteeInd', ns) == 'X'
                    is_key_employee = self._get_element_text(officer_elem, f'.//{ns}KeyEmployeeInd', ns) == 'X'

                    officer = SmallOrgOfficer(
                        ein=ein,
                        person_name=name,
                        title=title,
                        average_hours_per_week=hours,
                        compensation=compensation,
                        is_officer=is_officer,
                        is_director=is_director,
                        is_trustee=is_trustee,
                        is_key_employee=is_key_employee,
                        tax_year=tax_year
                    )
                    officers.append(officer)

            except Exception as e:
                print(f"     Error extracting officer: {e}")
                continue

        return officers

    def _extract_990ez_revenue(self, root: ET.Element, ein: str, tax_year: int) -> Optional[Form990EZRevenue]:
        """Extract revenue data from Form 990-EZ Part I."""
        # Handle namespace if present
        ns = ""
        if '}' in root.tag:
            ns = root.tag.split('}')[0] + '}'

        revenue = Form990EZRevenue(ein=ein, tax_year=tax_year)

        # Revenue line items from Part I
        revenue.contributions_gifts_grants = self._get_element_float(root, f'.//{ns}ContributionsGrantsAmt', ns)
        revenue.program_service_revenue = self._get_element_float(root, f'.//{ns}ProgramServiceRevenueAmt', ns)
        revenue.membership_dues_assessments = self._get_element_float(root, f'.//{ns}MembershipDuesAmt', ns)
        revenue.investment_income = self._get_element_float(root, f'.//{ns}InvestmentIncomeAmt', ns)
        revenue.gross_amount_from_sale_assets = self._get_element_float(root, f'.//{ns}GrossAmountSalesAssetsAmt', ns)
        revenue.special_events_gross_revenue = self._get_element_float(root, f'.//{ns}SpecialEventsGrossRevenueAmt', ns)
        revenue.special_events_direct_expenses = self._get_element_float(root, f'.//{ns}SpecialEventsDirectExpensesAmt', ns)
        revenue.special_events_net_income = self._get_element_float(root, f'.//{ns}SpecialEventsNetIncomeLossAmt', ns)
        revenue.gross_sales_inventory = self._get_element_float(root, f'.//{ns}GrossSalesInventoryAmt', ns)
        revenue.cost_goods_sold = self._get_element_float(root, f'.//{ns}CostGoodsSoldAmt', ns)
        revenue.gross_profit_loss_inventory = self._get_element_float(root, f'.//{ns}GrossProfitLossSlsInvntryAmt', ns)
        revenue.other_revenue = self._get_element_float(root, f'.//{ns}OtherRevenueAmt', ns)
        revenue.total_revenue = self._get_element_float(root, f'.//{ns}TotalRevenueAmt', ns)

        return revenue

    def _extract_990ez_expenses(self, root: ET.Element, ein: str, tax_year: int) -> Optional[Form990EZExpenses]:
        """Extract expense data from Form 990-EZ Part I."""
        # Handle namespace if present
        ns = ""
        if '}' in root.tag:
            ns = root.tag.split('}')[0] + '}'

        expenses = Form990EZExpenses(ein=ein, tax_year=tax_year)

        # Expense line items from Part I
        expenses.grants_similar_amounts_paid = self._get_element_float(root, f'.//{ns}GrantsAndSimilarAmtsPaidAmt', ns)
        expenses.benefits_paid_members = self._get_element_float(root, f'.//{ns}BenefitsPaidToMembersAmt', ns)
        expenses.salaries_wages_benefits = self._get_element_float(root, f'.//{ns}SalariesOtherCompEmplBnftAmt', ns)
        expenses.professional_fees = self._get_element_float(root, f'.//{ns}ProfessionalFeesAmt', ns)
        expenses.occupancy_rent_utilities = self._get_element_float(root, f'.//{ns}OccupancyRentUtltsAndMaintAmt', ns)
        expenses.printing_publications_postage = self._get_element_float(root, f'.//{ns}PrintingPublicationsPostageAmt', ns)
        expenses.other_expenses = self._get_element_float(root, f'.//{ns}OtherExpensesAmt', ns)
        expenses.total_expenses = self._get_element_float(root, f'.//{ns}TotalExpensesAmt', ns)
        expenses.excess_deficit_current_year = self._get_element_float(root, f'.//{ns}ExcessOrDeficitForYearAmt', ns)

        return expenses

    def _extract_990ez_balance_sheet(self, root: ET.Element, ein: str, tax_year: int) -> Optional[Form990EZBalanceSheet]:
        """Extract balance sheet data from Form 990-EZ Part II."""
        # Handle namespace if present
        ns = ""
        if '}' in root.tag:
            ns = root.tag.split('}')[0] + '}'

        balance_sheet = Form990EZBalanceSheet(ein=ein, tax_year=tax_year)

        # Balance sheet items from Part II
        balance_sheet.cash_savings_investments_boy = self._get_element_float(root, f'.//{ns}CashSavingsInvestmentsBOYAmt', ns)
        balance_sheet.cash_savings_investments_eoy = self._get_element_float(root, f'.//{ns}CashSavingsInvestmentsEOYAmt', ns)
        balance_sheet.land_buildings_boy = self._get_element_float(root, f'.//{ns}LandBldgEquipCostOrOtherBsssBOYAmt', ns)
        balance_sheet.land_buildings_eoy = self._get_element_float(root, f'.//{ns}LandBldgEquipCostOrOtherBsssEOYAmt', ns)
        balance_sheet.other_assets_boy = self._get_element_float(root, f'.//{ns}OtherAssetsBOYAmt', ns)
        balance_sheet.other_assets_eoy = self._get_element_float(root, f'.//{ns}OtherAssetsEOYAmt', ns)
        balance_sheet.total_assets_boy = self._get_element_float(root, f'.//{ns}TotalAssetsBOYAmt', ns)
        balance_sheet.total_assets_eoy = self._get_element_float(root, f'.//{ns}TotalAssetsEOYAmt', ns)
        balance_sheet.total_liabilities_boy = self._get_element_float(root, f'.//{ns}TotalLiabilitiesBOYAmt', ns)
        balance_sheet.total_liabilities_eoy = self._get_element_float(root, f'.//{ns}TotalLiabilitiesEOYAmt', ns)
        balance_sheet.net_assets_boy = self._get_element_float(root, f'.//{ns}NetAssetsOrFundBalancesBOYAmt', ns)
        balance_sheet.net_assets_eoy = self._get_element_float(root, f'.//{ns}NetAssetsOrFundBalancesEOYAmt', ns)

        return balance_sheet

    def _extract_990ez_public_support(self, root: ET.Element, ein: str, tax_year: int) -> Optional[PublicSupportData]:
        """Extract public support test data from Form 990-EZ Part VI."""
        # Handle namespace if present
        ns = ""
        if '}' in root.tag:
            ns = root.tag.split('}')[0] + '}'

        public_support = PublicSupportData(ein=ein, tax_year=tax_year)

        # Public support test items from Part VI
        public_support.total_support = self._get_element_float(root, f'.//{ns}TotalSupportAmt', ns)
        public_support.gross_receipts_related_activities = self._get_element_float(root, f'.//{ns}GrossReceiptsRltdActivitiesAmt', ns)
        public_support.first_five_years_support = self._get_element_float(root, f'.//{ns}First5YrsSupportAmt', ns)

        # Support sources
        public_support.gifts_grants_contributions = self._get_element_float(root, f'.//{ns}GiftsGrantsContribReceived5YrsAmt', ns)
        public_support.membership_fees_received = self._get_element_float(root, f'.//{ns}MembershipFeesReceived5YrsAmt', ns)
        public_support.gross_receipts_admissions = self._get_element_float(root, f'.//{ns}GrossReceiptsAdmissions5YrsAmt', ns)
        public_support.gross_receipts_merchandise = self._get_element_float(root, f'.//{ns}GrossReceiptsSalesAssets5YrsAmt', ns)
        public_support.gross_receipts_other = self._get_element_float(root, f'.//{ns}GrossReceiptsOther5YrsAmt', ns)

        return public_support

    def _extract_990ez_accomplishments(self, root: ET.Element, ein: str, tax_year: int) -> List[ProgramAccomplishment]:
        """Extract program accomplishments from Form 990-EZ Part III."""
        accomplishments = []

        # Handle namespace if present
        ns = ""
        if '}' in root.tag:
            ns = root.tag.split('}')[0] + '}'

        # Look for program accomplishments (typically 4 main accomplishments plus sub-accomplishments)
        accomplishment_patterns = [
            (1, f'.//{ns}ProgramSrvcAccomplishmentAct1', f'.//{ns}Program1ExpenseAmt'),
            (2, f'.//{ns}ProgramSrvcAccomplishmentAct2', f'.//{ns}Program2ExpenseAmt'),
            (3, f'.//{ns}ProgramSrvcAccomplishmentAct3', f'.//{ns}Program3ExpenseAmt'),
            (4, f'.//{ns}OtherProgramRelatedExpenseAmt', None)
        ]

        for number, desc_xpath, expense_xpath in accomplishment_patterns:
            description = self._get_element_text(root, desc_xpath, ns)
            expense = self._get_element_float(root, expense_xpath, ns) if expense_xpath else None

            if description or expense:
                accomplishment = ProgramAccomplishment(
                    ein=ein,
                    tax_year=tax_year,
                    accomplishment_number=number,
                    description=description,
                    expense_amount=expense
                )
                accomplishments.append(accomplishment)

        return accomplishments

    def _extract_990ez_operations(self, root: ET.Element, ein: str, tax_year: int) -> Optional[SmallOrgOperations]:
        """Extract operations data from various 990-EZ sections."""
        # Handle namespace if present
        ns = ""
        if '}' in root.tag:
            ns = root.tag.split('}')[0] + '}'

        operations = SmallOrgOperations(ein=ein, tax_year=tax_year)

        # Organization type and formation
        operations.organization_type = self._get_element_text(root, f'.//{ns}OrganizationTypeInd', ns)
        formation_year_text = self._get_element_text(root, f'.//{ns}FormationYr', ns)
        if formation_year_text:
            try:
                operations.formation_year = int(formation_year_text)
            except ValueError:
                pass

        # Activity codes (NTEE codes)
        activity_elements = root.findall(f'.//{ns}ActivityOrMissionDesc')
        if activity_elements:
            operations.activity_codes = [elem.text.strip() for elem in activity_elements if elem.text]

        # Operational indicators
        operations.significant_change_activities = self._get_element_text(root, f'.//{ns}SignificantChangeInd', ns) == 'X'
        operations.unrelated_business_income = self._get_element_text(root, f'.//{ns}UnrelatedBusIncmOverLimitInd', ns) == 'X'
        operations.organization_dissolved = self._get_element_text(root, f'.//{ns}OrganizationDissolvedEtcInd', ns) == 'X'

        # Financial thresholds
        operations.gross_receipts_normally_not_more_50k = self._get_element_text(root, f'.//{ns}GrossReceiptsLessThan25000Ind', ns) == 'X'
        operations.total_assets_less_than_25k = self._get_element_text(root, f'.//{ns}TotalAssetsLessThan25000Ind', ns) == 'X'

        return operations


# Tool execution entry point
if __name__ == "__main__":
    async def main():
        parser = XML990EZParserTool()
        criteria = XML990EZParseCriteria(
            target_eins=["123456789"],  # Example EIN
            schedules_to_extract=["officers", "revenue", "expenses", "balance_sheet", "public_support"],
            cache_enabled=True,
            max_years_back=3,
            download_if_missing=True,
            validate_990ez_schema=True
        )

        result = await parser.execute(criteria)
        print(f"XML 990-EZ parsing completed for {result.organizations_processed} organizations")
        print(f"Officers extracted: {result.officers_extracted}")
        print(f"Accomplishments extracted: {result.accomplishments_extracted}")

    asyncio.run(main())