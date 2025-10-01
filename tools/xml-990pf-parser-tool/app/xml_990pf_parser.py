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
class FoundationContactInfo:
    """Foundation contact information from 990-PF header."""
    ein: str
    foundation_name: str
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    phone_number: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    principal_officer_name: Optional[str] = None
    principal_officer_title: Optional[str] = None
    contact_person_name: Optional[str] = None
    contact_person_title: Optional[str] = None
    tax_year: int = 0
    data_source: str = "Form 990-PF XML Header"


@dataclass
class FoundationGrantAnalysis:
    """Foundation grant distribution analysis for strategic intelligence."""
    ein: str
    tax_year: int
    total_grants_count: int
    total_grants_amount: float
    average_grant_size: float
    largest_grant_amount: Optional[float] = None
    smallest_grant_amount: Optional[float] = None
    median_grant_amount: Optional[float] = None

    # Grant recipient patterns
    individual_recipients_count: int = 0
    organization_recipients_count: int = 0
    geographic_concentration: Optional[str] = None
    recipient_diversity_score: Optional[float] = None

    # Grant purpose analysis
    top_grant_purposes: List[str] = field(default_factory=list)
    funding_focus_areas: List[str] = field(default_factory=list)
    impact_grant_percentage: Optional[float] = None
    flexible_funding_percentage: Optional[float] = None

    # Grant size distribution
    large_grants_count: int = 0  # >= $100K
    medium_grants_count: int = 0  # $10K - $99K
    small_grants_count: int = 0  # < $10K
    grant_size_strategy: str = "Unknown"

    # Historical patterns
    grant_making_consistency: str = "Unknown"
    repeat_recipient_percentage: Optional[float] = None
    new_recipient_percentage: Optional[float] = None

    data_source: str = "Form 990-PF Grant Analysis"


@dataclass
class FoundationClassification:
    """Foundation classification and grant-making approach analysis."""
    ein: str
    tax_year: int

    # Foundation type classification
    foundation_type: str = "Private Foundation"
    foundation_size_category: str = "Unknown"
    grant_making_approach: str = "Unknown"

    # Grant-making characteristics
    funding_model: str = "Unknown"
    geographic_scope: str = "Unknown"
    sector_focus: List[str] = field(default_factory=list)

    # Foundation maturity and sophistication
    operational_sophistication: str = "Unknown"
    grant_making_maturity: str = "Unknown"
    professional_management: str = "Unknown"

    # Grant strategy intelligence
    risk_tolerance: str = "Unknown"
    innovation_focus: str = "Unknown"
    capacity_building_emphasis: str = "Unknown"

    # Foundation accessibility for grant seekers
    grant_accessibility_score: float = 0.0
    application_complexity: str = "Unknown"
    funding_predictability: str = "Unknown"

    # Strategic positioning
    competitive_landscape_position: str = "Unknown"
    unique_value_proposition: Optional[str] = None
    grant_seeker_recommendations: List[str] = field(default_factory=list)

    data_source: str = "Form 990-PF Classification Analysis"


@dataclass
class FoundationOfficer:
    """Form 990-PF Part VIII - Officers, Directors, Trustees, Foundation Managers."""
    ein: str
    person_name: str
    normalized_person_name: str = ""  # Cleaned name for network matching
    title: str = "Unknown"
    role_category: str = "Unknown"  # Executive, Board, Staff, Volunteer
    average_hours_per_week: Optional[float] = None
    compensation: Optional[float] = None
    employee_benefit_program: Optional[bool] = None
    expense_account_allowance: Optional[float] = None
    is_officer: bool = False
    is_director: bool = False
    influence_score: Optional[float] = None  # Calculated decision-making power (0-1)
    tax_year: int = 0
    data_source: str = "Form 990-PF XML"


@dataclass
class FoundationGrant:
    """Part XV: Grants and contributions paid."""
    ein: str
    recipient_name: str
    normalized_recipient_name: str = ""  # Cleaned org name for network matching
    recipient_ein: Optional[str] = None  # **CRITICAL** for org-to-org network mapping
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
class InvestmentAnalysis:
    """Investment portfolio analysis for grant capacity assessment."""
    ein: str
    tax_year: int

    # Portfolio composition
    total_investment_value: float = 0.0
    total_investment_count: int = 0
    portfolio_diversification_score: float = 0.0

    # Asset allocation analysis
    equity_percentage: Optional[float] = None
    fixed_income_percentage: Optional[float] = None
    alternative_investments_percentage: Optional[float] = None
    cash_equivalent_percentage: Optional[float] = None

    # Investment performance indicators
    unrealized_gains_losses: Optional[float] = None
    investment_return_estimate: Optional[float] = None
    investment_volatility_assessment: str = "Unknown"

    # Grant capacity analysis
    sustainable_grant_capacity: float = 0.0
    grant_funding_stability: str = "Unknown"
    endowment_sustainability_years: Optional[int] = None

    # Strategic investment insights
    investment_strategy_type: str = "Unknown"
    liquidity_assessment: str = "Unknown"
    professional_management_indicators: bool = False

    # Grant-making implications
    grant_capacity_trend: str = "Unknown"
    optimal_grant_timing: Optional[str] = None
    multi_year_grant_feasibility: str = "Unknown"

    data_source: str = "Form 990-PF Investment Analysis"


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
    contact_info: List[FoundationContactInfo]
    officers: List[FoundationOfficer]
    grants_paid: List[FoundationGrant]
    grant_analysis: List[FoundationGrantAnalysis]
    foundation_classification: List[FoundationClassification]
    investment_holdings: List[InvestmentHolding]
    investment_analysis: List[InvestmentAnalysis]
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


# ========================================
# NETWORK ANALYSIS HELPER FUNCTIONS
# ========================================

def normalize_person_name(name: str) -> str:
    """
    Normalize person name for network matching across 990 forms.

    Examples:
        "Christine M. Connolly" → "CHRISTINE M CONNOLLY"
        "Dr. Major Warner" → "MAJOR WARNER"
        "John W. McCarthy III" → "JOHN W MCCARTHY III"

    Returns:
        Cleaned uppercase name without titles or punctuation
    """
    if not name:
        return ""

    # Remove common titles
    titles = ['Dr.', 'Dr', 'MD', 'PhD', 'Esq', 'Jr.', 'Jr', 'Sr.', 'Sr', 'II', 'III', 'IV']
    cleaned = name
    for title in titles:
        cleaned = cleaned.replace(f" {title} ", " ")
        cleaned = cleaned.replace(f" {title}", "")
        if cleaned.startswith(f"{title} "):
            cleaned = cleaned[len(title)+1:]

    # Remove punctuation
    for char in ['.', ',', ';', ':', '-', '(', ')']:
        cleaned = cleaned.replace(char, '')

    # Normalize whitespace and uppercase
    cleaned = ' '.join(cleaned.split()).upper()

    return cleaned


def normalize_org_name(name: str) -> str:
    """
    Normalize organization name for network matching.

    Examples:
        "Boys and Girls Club of Fauquier" → "BOYS AND GIRLS CLUB OF FAUQUIER"
        "4P FOODS INC" → "4P FOODS INC"
        "AFRO-AMERICAN HISTORICAL ASSOC" → "AFROAMERICAN HISTORICAL ASSOC"

    Returns:
        Cleaned uppercase org name
    """
    if not name:
        return ""

    # Remove common legal suffixes (but preserve for matching accuracy)
    cleaned = name

    # Remove punctuation (except spaces)
    for char in ['.', ',', ';', ':', '(', ')']:
        cleaned = cleaned.replace(char, '')

    # Normalize hyphens to spaces
    cleaned = cleaned.replace('-', ' ')

    # Normalize whitespace and uppercase
    cleaned = ' '.join(cleaned.split()).upper()

    return cleaned


def categorize_role(title: str, is_officer: bool, is_director: bool, compensation: Optional[float]) -> str:
    """
    Categorize officer role for network analysis.

    Categories:
        - Executive: CEO, President, CFO, COO, Executive Director
        - Board: Chair, Director, Trustee, Secretary, Treasurer (unpaid)
        - Staff: Paid administrative positions
        - Volunteer: Unpaid non-executive positions

    Returns:
        Role category string
    """
    if not title:
        return "Unknown"

    title_upper = title.upper()

    # Executive roles
    executive_keywords = ['CEO', 'PRESIDENT', 'CFO', 'COO', 'EXECUTIVE DIRECTOR', 'EXECUTIVE DIR']
    if any(keyword in title_upper for keyword in executive_keywords):
        return "Executive"

    # Board roles (typically unpaid or low compensation)
    board_keywords = ['CHAIR', 'DIRECTOR', 'TRUSTEE', 'SECRETARY', 'TREASURER', 'BOARD']
    if any(keyword in title_upper for keyword in board_keywords):
        # Check if paid staff vs volunteer board
        if compensation and compensation > 50000:
            return "Staff"  # Paid staff director
        return "Board"  # Volunteer board member

    # Staff roles
    staff_keywords = ['MANAGER', 'COORDINATOR', 'ADMINISTRATOR', 'OFFICER']
    if any(keyword in title_upper for keyword in staff_keywords):
        return "Staff"

    # Default categorization
    if is_officer:
        return "Executive"
    if is_director:
        return "Board"

    return "Volunteer"


def calculate_influence_score(
    role_category: str,
    is_officer: bool,
    is_director: bool,
    compensation: Optional[float],
    average_hours: Optional[float]
) -> float:
    """
    Calculate influence score for board member network analysis.

    Scoring factors:
        - Role category: Executive (1.0), Board (0.7), Staff (0.4), Volunteer (0.2)
        - Compensation: Normalized 0-1 based on $0-$500K range
        - Hours per week: Normalized 0-1 based on 0-40 hours range
        - Officer flag: +0.2 bonus
        - Director flag: +0.1 bonus

    Returns:
        Influence score between 0-1
    """
    score = 0.0

    # Base score from role category
    role_scores = {
        'Executive': 1.0,
        'Board': 0.7,
        'Staff': 0.4,
        'Volunteer': 0.2,
        'Unknown': 0.3
    }
    score = role_scores.get(role_category, 0.3)

    # Compensation factor (0-0.3 bonus)
    if compensation and compensation > 0:
        comp_normalized = min(compensation / 500000, 1.0)
        score += comp_normalized * 0.3

    # Hours per week factor (0-0.2 bonus)
    if average_hours and average_hours > 0:
        hours_normalized = min(average_hours / 40, 1.0)
        score += hours_normalized * 0.2

    # Role flag bonuses
    if is_officer:
        score += 0.2
    if is_director:
        score += 0.1

    # Normalize to 0-1 range
    return min(score, 1.0)


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
            contact_info=[],
            officers=[],
            grants_paid=[],
            grant_analysis=[],
            foundation_classification=[],
            investment_holdings=[],
            investment_analysis=[],
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

            # Always extract contact information (foundation header)
            contact_info = self._extract_990pf_contact_info(root, ein, file_metadata.tax_year)
            if contact_info:
                result.contact_info.append(contact_info)
                print(f"     Contact Info: Foundation details extracted")

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

                    # Generate investment analysis for grant capacity assessment
                    investment_analysis = self._analyze_foundation_investments(investments, ein, file_metadata.tax_year)
                    if investment_analysis:
                        result.investment_analysis.append(investment_analysis)
                        print(f"     Investment analysis: grant capacity assessment completed")

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

            # Generate grant analysis if grants were extracted
            if result.grants_paid:
                grant_analysis = self._analyze_foundation_grants(result.grants_paid, ein, file_metadata.tax_year)
                if grant_analysis:
                    result.grant_analysis.append(grant_analysis)
                    print(f"     Grant Analysis: distribution intelligence extracted")

            # Generate foundation classification based on all extracted data
            foundation_classification = self._classify_foundation(
                result.officers, result.grants_paid, result.grant_analysis,
                result.payout_requirements, result.governance_indicators,
                ein, file_metadata.tax_year
            )
            if foundation_classification:
                result.foundation_classification.append(foundation_classification)
                print(f"     Foundation Classification: strategic analysis extracted")

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

            # Look for OfficerDirTrstKeyEmplInfoGrp wrapper and OfcrDirTrstKeyEmplGrp elements (990-PF specific)
            officer_elements = []

            # Strategy 1: Look for wrapper element first, then inner elements
            wrapper_elem = None
            if ns:
                wrapper_elem = root.find(f'.//{ns}OfficerDirTrstKeyEmplInfoGrp')
            if wrapper_elem is None:
                wrapper_elem = root.find('.//OfficerDirTrstKeyEmplInfoGrp')

            if wrapper_elem is not None:
                # Found wrapper, extract individual officer elements from within
                if ns:
                    officer_elements = wrapper_elem.findall(f'.//{ns}OfficerDirTrstKeyEmplGrp')
                if not officer_elements:
                    officer_elements = wrapper_elem.findall('.//OfficerDirTrstKeyEmplGrp')

            # Strategy 2: Direct search for officer elements (fallback)
            if not officer_elements:
                if ns:
                    officer_elements = root.findall(f'.//{ns}OfficerDirTrstKeyEmplGrp')
                if not officer_elements:
                    officer_elements = root.findall('.//OfficerDirTrstKeyEmplGrp')

            # Strategy 3: Search within IRS990PF element (final fallback)
            if not officer_elements:
                irs990pf_elem = None
                if ns:
                    irs990pf_elem = root.find(f'.//{ns}IRS990PF')
                if irs990pf_elem is None:
                    irs990pf_elem = root.find('.//IRS990PF')

                if irs990pf_elem is not None:
                    if ns:
                        officer_elements = irs990pf_elem.findall(f'.//{ns}OfficerDirTrstKeyEmplGrp')
                    if not officer_elements:
                        officer_elements = irs990pf_elem.findall('.//OfficerDirTrstKeyEmplGrp')

            for officer_elem in officer_elements:
                try:
                    person_name = self._get_element_text(officer_elem, ".//PersonNm")
                    title = self._get_element_text(officer_elem, ".//TitleTxt")

                    if person_name:
                        # Extract raw data
                        compensation = self._get_element_float(officer_elem, ".//CompensationAmt")
                        average_hours = self._get_element_float(officer_elem, ".//AverageHoursPerWeekRt")
                        is_officer = self._get_element_bool(officer_elem, ".//OfficerInd") or False
                        is_director = self._get_element_bool(officer_elem, ".//DirectorOrTrusteeInd") or False

                        # Apply network analysis normalization
                        normalized_name = normalize_person_name(person_name)
                        role_category = categorize_role(title or "Unknown", is_officer, is_director, compensation)
                        influence_score = calculate_influence_score(role_category, is_officer, is_director, compensation, average_hours)

                        officer = FoundationOfficer(
                            ein=ein,
                            person_name=person_name,
                            normalized_person_name=normalized_name,
                            title=title or "Unknown",
                            role_category=role_category,
                            average_hours_per_week=average_hours,
                            compensation=compensation,
                            employee_benefit_program=self._get_element_bool(officer_elem, ".//EmployeeBenefitProgramAmt"),
                            expense_account_allowance=self._get_element_float(officer_elem, ".//ExpenseAccountOtherAllwncAmt"),
                            is_officer=is_officer,
                            is_director=is_director,
                            influence_score=influence_score,
                            tax_year=tax_year
                        )
                        officers.append(officer)

                except Exception as e:
                    continue

        except Exception as e:
            print(f"     Error extracting officers: {e}")

        return officers

    def _extract_990pf_contact_info(self, root: ET.Element, ein: str, tax_year: int) -> FoundationContactInfo:
        """Extract foundation contact information from 990-PF header."""
        try:
            # Handle namespace if present
            ns = ""
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'

            # Look for Return Header and Filer elements
            foundation_name = ""
            address_line_1 = ""
            address_line_2 = ""
            city = ""
            state = ""
            zip_code = ""
            phone_number = ""

            # Strategy 1: Look for ReturnHeader/Filer
            filer_elem = None
            if ns:
                filer_elem = root.find(f'.//{ns}Filer')
            if filer_elem is None:
                filer_elem = root.find('.//Filer')

            if filer_elem is not None:
                foundation_name = self._get_element_text(filer_elem, ".//BusinessName") or self._get_element_text(filer_elem, ".//OrganizationName")

                # Address information
                address_elem = filer_elem.find(".//USAddress") or filer_elem.find(".//ForeignAddress")
                if address_elem is not None:
                    address_line_1 = self._get_element_text(address_elem, ".//AddressLine1Txt")
                    address_line_2 = self._get_element_text(address_elem, ".//AddressLine2Txt")
                    city = self._get_element_text(address_elem, ".//CityNm")
                    state = self._get_element_text(address_elem, ".//StateAbbreviationCd")
                    zip_code = self._get_element_text(address_elem, ".//ZIPCd")

                # Phone number
                phone_number = self._get_element_text(filer_elem, ".//PhoneNum")

            # Strategy 2: Look within IRS990PF element for additional contact info
            irs990pf_elem = None
            if ns:
                irs990pf_elem = root.find(f'.//{ns}IRS990PF')
            if irs990pf_elem is None:
                irs990pf_elem = root.find('.//IRS990PF')

            principal_officer_name = ""
            principal_officer_title = ""

            if irs990pf_elem is not None:
                # Look for principal officer information
                principal_officer_name = self._get_element_text(irs990pf_elem, ".//PrincipalOfficerNm")
                principal_officer_title = self._get_element_text(irs990pf_elem, ".//PrincipalOfficerTitleTxt")

            # If we couldn't find foundation name in filer, try alternative locations
            if not foundation_name:
                foundation_name = self._get_element_text(root, ".//OrganizationName") or self._get_element_text(root, ".//BusinessName")

            return FoundationContactInfo(
                ein=ein,
                foundation_name=foundation_name or "Unknown Foundation",
                address_line_1=address_line_1,
                address_line_2=address_line_2,
                city=city,
                state=state,
                zip_code=zip_code,
                country="US" if state else None,
                phone_number=phone_number,
                website=None,  # Not typically in XML
                email=None,    # Not typically in XML
                principal_officer_name=principal_officer_name,
                principal_officer_title=principal_officer_title,
                contact_person_name=None,  # Would need additional parsing
                contact_person_title=None,
                tax_year=tax_year,
                data_source="Form 990-PF XML Header"
            )

        except Exception as e:
            print(f"     Error extracting contact info: {e}")
            # Return minimal contact info even on error
            return FoundationContactInfo(
                ein=ein,
                foundation_name="Unknown Foundation",
                address_line_1=None,
                address_line_2=None,
                city=None,
                state=None,
                zip_code=None,
                country=None,
                phone_number=None,
                website=None,
                email=None,
                principal_officer_name=None,
                principal_officer_title=None,
                contact_person_name=None,
                contact_person_title=None,
                tax_year=tax_year,
                data_source="Form 990-PF XML Header"
            )

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
                './/GrantOrContributionPdDurYrGrp',  # Most common in 990-PF
                './/GrantOrContributionPdGrp',       # Alternative format
                './/SupplementaryInformationGrp',    # Supplementary grants
                './/GrantOrContribution'             # General pattern
            ]

            for path in grant_paths:
                if ns:
                    # Replace './' with namespace
                    ns_path = path.replace('.//', f'.//{ns}')
                    elements = root.findall(ns_path)
                else:
                    elements = root.findall(path)

                if elements:
                    grant_elements.extend(elements)

            for grant_elem in grant_elements[:20]:  # Limit to 20 grants
                try:
                    # Extract recipient name from various formats (handle namespaces)
                    recipient_name = None

                    # Business name format: RecipientBusinessName/BusinessNameLine1Txt
                    business_paths = [".//RecipientBusinessName", f".//{ns}RecipientBusinessName"] if ns else [".//RecipientBusinessName"]
                    for business_path in business_paths:
                        business_elem = grant_elem.find(business_path)
                        if business_elem is not None:
                            # Try both namespaced and non-namespaced child search
                            line_paths = [".//BusinessNameLine1Txt", f".//{ns}BusinessNameLine1Txt"] if ns else [".//BusinessNameLine1Txt"]
                            for line_path in line_paths:
                                business_line = business_elem.find(line_path)
                                if business_line is not None and business_line.text:
                                    recipient_name = business_line.text.strip()
                                    break
                            if recipient_name:
                                break

                    # Person name format: RecipientPersonNm
                    if not recipient_name:
                        person_paths = [".//RecipientPersonNm", f".//{ns}RecipientPersonNm"] if ns else [".//RecipientPersonNm"]
                        for person_path in person_paths:
                            person_elem = grant_elem.find(person_path)
                            if person_elem is not None and person_elem.text:
                                recipient_name = person_elem.text.strip()
                                break

                    # Alternative recipient name formats
                    if not recipient_name:
                        name_paths = [".//RecipientName", f".//{ns}RecipientName"] if ns else [".//RecipientName"]
                        for name_path in name_paths:
                            name_elem = grant_elem.find(name_path)
                            if name_elem is not None and name_elem.text:
                                recipient_name = name_elem.text.strip()
                                break

                    # Extract amount in various formats (handle namespaces)
                    amount = None
                    amount_base_paths = [".//Amt", ".//Amount", ".//GrantOrContributionAmt"]
                    amount_paths = []
                    for base_path in amount_base_paths:
                        amount_paths.append(base_path)
                        if ns:
                            amount_paths.append(f".//{ns}{base_path[3:]}")  # Replace './/' with namespace

                    for path in amount_paths:
                        amt_elem = grant_elem.find(path)
                        if amt_elem is not None and amt_elem.text:
                            try:
                                amount = float(amt_elem.text.strip())
                                break
                            except ValueError:
                                continue


                    if recipient_name and amount:
                        # Apply network analysis normalization for org names
                        normalized_recipient_name = normalize_org_name(recipient_name)

                        # Extract recipient EIN if available (critical for org-to-org network mapping)
                        recipient_ein = self._get_element_text(grant_elem, ".//RecipientEIN")

                        grant = FoundationGrant(
                            ein=ein,
                            recipient_name=recipient_name,
                            normalized_recipient_name=normalized_recipient_name,
                            recipient_ein=recipient_ein,
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

    def _analyze_foundation_grants(self, grants: List[FoundationGrant], ein: str, tax_year: int) -> FoundationGrantAnalysis:
        """Analyze foundation grant patterns for strategic intelligence."""
        try:
            if not grants:
                return None

            # Basic statistics
            total_grants_count = len(grants)
            grant_amounts = [grant.grant_amount for grant in grants if grant.grant_amount]
            total_grants_amount = sum(grant_amounts)
            average_grant_size = total_grants_amount / total_grants_count if total_grants_count > 0 else 0

            largest_grant_amount = max(grant_amounts) if grant_amounts else None
            smallest_grant_amount = min(grant_amounts) if grant_amounts else None

            # Calculate median
            sorted_amounts = sorted(grant_amounts)
            n = len(sorted_amounts)
            median_grant_amount = None
            if n > 0:
                if n % 2 == 0:
                    median_grant_amount = (sorted_amounts[n//2 - 1] + sorted_amounts[n//2]) / 2
                else:
                    median_grant_amount = sorted_amounts[n//2]

            # Grant size distribution analysis
            large_grants_count = sum(1 for amt in grant_amounts if amt >= 100000)  # >= $100K
            medium_grants_count = sum(1 for amt in grant_amounts if 10000 <= amt < 100000)  # $10K-$99K
            small_grants_count = sum(1 for amt in grant_amounts if amt < 10000)  # < $10K

            # Determine grant size strategy
            total_value_large = sum(amt for amt in grant_amounts if amt >= 100000)
            large_value_percentage = (total_value_large / total_grants_amount * 100) if total_grants_amount > 0 else 0

            if large_grants_count >= total_grants_count * 0.6:
                grant_size_strategy = "Large Impact Focus"
            elif large_value_percentage >= 70:
                grant_size_strategy = "Strategic Large Grants"
            elif small_grants_count >= total_grants_count * 0.6:
                grant_size_strategy = "Broad Distribution"
            else:
                grant_size_strategy = "Mixed Strategy"

            # Purpose analysis
            purposes = [grant.grant_purpose for grant in grants if grant.grant_purpose]
            purpose_counts = {}
            for purpose in purposes:
                purpose_upper = purpose.upper()
                if purpose_upper in purpose_counts:
                    purpose_counts[purpose_upper] += 1
                else:
                    purpose_counts[purpose_upper] = 1

            # Get top purposes (most common)
            top_grant_purposes = []
            if purpose_counts:
                sorted_purposes = sorted(purpose_counts.items(), key=lambda x: x[1], reverse=True)
                top_grant_purposes = [purpose for purpose, count in sorted_purposes[:5]]

            # Calculate percentages for specific grant types
            impact_grants = sum(1 for purpose in purposes if purpose and 'IMPACT' in purpose.upper())
            impact_grant_percentage = (impact_grants / len(purposes) * 100) if purposes else None

            flexible_grants = sum(1 for purpose in purposes if purpose and 'FLEXIBLE' in purpose.upper())
            flexible_funding_percentage = (flexible_grants / len(purposes) * 100) if purposes else None

            # Identify funding focus areas from purposes
            funding_focus_areas = []
            health_terms = ['HEALTH', 'MEDICAL', 'WELLNESS', 'MENTAL HEALTH', 'HEALTHCARE']
            education_terms = ['EDUCATION', 'SCHOOL', 'SCHOLARSHIP', 'LEARNING', 'ACADEMIC']
            community_terms = ['COMMUNITY', 'SOCIAL', 'CIVIC', 'LOCAL', 'NEIGHBORHOOD']
            arts_terms = ['ARTS', 'CULTURE', 'MUSIC', 'THEATER', 'CULTURAL']

            purpose_text = ' '.join(purposes).upper()
            if any(term in purpose_text for term in health_terms):
                funding_focus_areas.append("Health & Wellness")
            if any(term in purpose_text for term in education_terms):
                funding_focus_areas.append("Education")
            if any(term in purpose_text for term in community_terms):
                funding_focus_areas.append("Community Development")
            if any(term in purpose_text for term in arts_terms):
                funding_focus_areas.append("Arts & Culture")

            # Recipient analysis (basic for single year data)
            individual_recipients_count = 0  # Would need to analyze recipient types more deeply
            organization_recipients_count = total_grants_count  # Assume all are organizations for now

            return FoundationGrantAnalysis(
                ein=ein,
                tax_year=tax_year,
                total_grants_count=total_grants_count,
                total_grants_amount=total_grants_amount,
                average_grant_size=average_grant_size,
                largest_grant_amount=largest_grant_amount,
                smallest_grant_amount=smallest_grant_amount,
                median_grant_amount=median_grant_amount,
                individual_recipients_count=individual_recipients_count,
                organization_recipients_count=organization_recipients_count,
                geographic_concentration=None,  # Would need address analysis
                recipient_diversity_score=None,  # Would need multi-year analysis
                top_grant_purposes=top_grant_purposes,
                funding_focus_areas=funding_focus_areas,
                impact_grant_percentage=impact_grant_percentage,
                flexible_funding_percentage=flexible_funding_percentage,
                large_grants_count=large_grants_count,
                medium_grants_count=medium_grants_count,
                small_grants_count=small_grants_count,
                grant_size_strategy=grant_size_strategy,
                grant_making_consistency="Single Year Data",  # Would need multi-year analysis
                repeat_recipient_percentage=None,  # Would need multi-year analysis
                new_recipient_percentage=None,  # Would need multi-year analysis
                data_source="Form 990-PF Grant Analysis"
            )

        except Exception as e:
            print(f"     Error analyzing grants: {e}")
            return None

    def _classify_foundation(self, officers, grants_paid, grant_analysis, payout_requirements, governance_indicators, ein: str, tax_year: int) -> FoundationClassification:
        """Classify foundation based on comprehensive analysis of all data."""
        try:
            # Foundation size classification based on payout requirements
            foundation_size_category = "Unknown"
            if payout_requirements:
                payout = payout_requirements[0]
                if payout.average_monthly_fair_market_value:
                    assets = payout.average_monthly_fair_market_value * 12  # Annual assets
                    if assets >= 1000000000:  # $1B+
                        foundation_size_category = "Major"
                    elif assets >= 100000000:  # $100M+
                        foundation_size_category = "Large"
                    elif assets >= 10000000:  # $10M+
                        foundation_size_category = "Medium"
                    else:
                        foundation_size_category = "Small"

            # Professional management analysis based on officer compensation
            professional_management = "Unknown"
            if officers:
                compensated_officers = [o for o in officers if o.compensation and o.compensation > 0]
                high_compensation = [o for o in compensated_officers if o.compensation >= 100000]

                if len(high_compensation) >= 3:
                    professional_management = "Professional"
                elif len(compensated_officers) >= 2:
                    professional_management = "Mixed"
                else:
                    professional_management = "Board-Managed"

            # Grant-making approach based on grant analysis
            grant_making_approach = "Unknown"
            funding_model = "Unknown"
            risk_tolerance = "Unknown"

            if grant_analysis:
                analysis = grant_analysis[0]

                # Determine grant-making approach
                if analysis.grant_size_strategy == "Large Impact Focus":
                    grant_making_approach = "Strategic"
                    risk_tolerance = "Moderate"
                elif analysis.grant_size_strategy == "Strategic Large Grants":
                    grant_making_approach = "Strategic"
                    risk_tolerance = "Conservative"
                elif analysis.grant_size_strategy == "Broad Distribution":
                    grant_making_approach = "Responsive"
                    risk_tolerance = "Conservative"
                else:
                    grant_making_approach = "Mixed"
                    risk_tolerance = "Moderate"

                # Determine funding model based on flexibility
                if analysis.flexible_funding_percentage and analysis.flexible_funding_percentage >= 40:
                    funding_model = "Responsive"
                elif analysis.impact_grant_percentage and analysis.impact_grant_percentage >= 20:
                    funding_model = "Strategic"
                else:
                    funding_model = "Mixed"

            # Operational sophistication based on governance
            operational_sophistication = "Basic"
            grant_making_maturity = "Emerging"
            application_complexity = "Simple"

            if governance_indicators:
                governance = governance_indicators[0]
                sophistication_score = 0

                # Count sophisticated governance features
                features = [
                    governance.grant_making_procedures,
                    governance.grant_monitoring_procedures,
                    governance.website_grant_application_process,
                    governance.compensation_policy,
                    governance.conflict_of_interest_policy,
                    governance.independent_audit
                ]

                sophistication_score = sum(1 for f in features if f)

                if sophistication_score >= 4:
                    operational_sophistication = "High"
                    grant_making_maturity = "Mature"
                    application_complexity = "Complex"
                elif sophistication_score >= 2:
                    operational_sophistication = "Medium"
                    grant_making_maturity = "Developing"
                    application_complexity = "Moderate"

            # Innovation focus based on grant purposes
            innovation_focus = "Low"
            sector_focus = []

            if grant_analysis:
                analysis = grant_analysis[0]

                # Check for innovation keywords in purposes
                innovation_keywords = ['INNOVATION', 'TECHNOLOGY', 'RESEARCH', 'PILOT', 'EMERGING']
                if analysis.top_grant_purposes:
                    purpose_text = ' '.join(analysis.top_grant_purposes).upper()
                    innovation_count = sum(1 for keyword in innovation_keywords if keyword in purpose_text)
                    if innovation_count >= 2:
                        innovation_focus = "High"
                    elif innovation_count >= 1:
                        innovation_focus = "Medium"

                # Set sector focus from funding focus areas
                sector_focus = analysis.funding_focus_areas or []

            # Geographic scope analysis (simplified for single-year data)
            geographic_scope = "Regional"  # Default assumption for most foundations

            # Accessibility score calculation
            accessibility_factors = []
            if funding_model == "Responsive":
                accessibility_factors.append(0.3)
            if application_complexity == "Simple":
                accessibility_factors.append(0.3)
            if grant_analysis and grant_analysis[0].flexible_funding_percentage and grant_analysis[0].flexible_funding_percentage >= 30:
                accessibility_factors.append(0.4)

            grant_accessibility_score = sum(accessibility_factors) if accessibility_factors else 0.2

            # Grant seeker recommendations
            recommendations = []
            if funding_model == "Responsive":
                recommendations.append("Focus on clear project outcomes and community impact")
            if grant_analysis and grant_analysis[0].flexible_funding_percentage and grant_analysis[0].flexible_funding_percentage >= 40:
                recommendations.append("Consider flexible funding applications for operational support")
            if professional_management == "Professional":
                recommendations.append("Prepare comprehensive proposals with detailed budgets")
            if foundation_size_category in ["Major", "Large"]:
                recommendations.append("Consider multi-year project proposals")

            # Unique value proposition
            unique_value_proposition = None
            if grant_analysis:
                analysis = grant_analysis[0]
                if analysis.flexible_funding_percentage and analysis.flexible_funding_percentage >= 50:
                    unique_value_proposition = "High emphasis on flexible funding for organizational capacity"
                elif len(analysis.funding_focus_areas) >= 3:
                    unique_value_proposition = "Multi-sector approach with diverse funding priorities"

            return FoundationClassification(
                ein=ein,
                tax_year=tax_year,
                foundation_type="Private Foundation",  # 990-PF assumption
                foundation_size_category=foundation_size_category,
                grant_making_approach=grant_making_approach,
                funding_model=funding_model,
                geographic_scope=geographic_scope,
                sector_focus=sector_focus,
                operational_sophistication=operational_sophistication,
                grant_making_maturity=grant_making_maturity,
                professional_management=professional_management,
                risk_tolerance=risk_tolerance,
                innovation_focus=innovation_focus,
                capacity_building_emphasis="Medium",  # Default assumption
                grant_accessibility_score=grant_accessibility_score,
                application_complexity=application_complexity,
                funding_predictability="Variable",  # Default for single-year data
                competitive_landscape_position=f"{foundation_size_category} Foundation in Regional Market",
                unique_value_proposition=unique_value_proposition,
                grant_seeker_recommendations=recommendations,
                data_source="Form 990-PF Classification Analysis"
            )

        except Exception as e:
            print(f"     Error classifying foundation: {e}")
            return None

    def _analyze_foundation_investments(self, investments: List[InvestmentHolding], ein: str, tax_year: int) -> InvestmentAnalysis:
        """Generate investment portfolio analysis for grant capacity assessment."""
        try:
            if not investments:
                return None

            # Portfolio composition analysis
            total_investment_value = 0.0
            total_investment_count = len(investments)

            # Asset allocation categories
            equity_value = 0.0
            fixed_income_value = 0.0
            alternative_investments_value = 0.0
            cash_equivalent_value = 0.0

            # Investment performance indicators
            total_book_value = 0.0
            total_fair_market_value = 0.0

            for investment in investments:
                # Calculate total values - handle None and string values
                try:
                    fmv = float(investment.fair_market_value) if investment.fair_market_value is not None else 0.0
                except (ValueError, TypeError):
                    fmv = 0.0

                try:
                    book_val = float(investment.book_value) if investment.book_value is not None else 0.0
                except (ValueError, TypeError):
                    book_val = 0.0

                # Use fair market value if available, otherwise fall back to book value
                investment_value = fmv if fmv > 0 else book_val

                total_investment_value += investment_value
                total_book_value += book_val
                total_fair_market_value += fmv

                # Categorize investments by type
                inv_type = (investment.investment_type or "").lower()
                inv_category = (investment.investment_category or "").lower()

                if "stock" in inv_type or "stock" in inv_category or "equity" in inv_type:
                    equity_value += investment_value
                elif "bond" in inv_type or "bond" in inv_category or "debt" in inv_type:
                    fixed_income_value += investment_value
                elif "cash" in inv_type or "savings" in inv_type or "money market" in inv_type:
                    cash_equivalent_value += investment_value
                else:
                    alternative_investments_value += investment_value

            # Check if we have any investment value - if not, return None
            if total_investment_value <= 0:
                print(f"     Warning: No investment values found for analysis")
                return None

            # Calculate allocation percentages
            equity_percentage = (equity_value / total_investment_value * 100) if total_investment_value > 0 else 0.0
            fixed_income_percentage = (fixed_income_value / total_investment_value * 100) if total_investment_value > 0 else 0.0
            alternative_investments_percentage = (alternative_investments_value / total_investment_value * 100) if total_investment_value > 0 else 0.0
            cash_equivalent_percentage = (cash_equivalent_value / total_investment_value * 100) if total_investment_value > 0 else 0.0

            # Portfolio diversification score (0-1)
            diversification_components = [
                min(equity_percentage / 60.0, 1.0),  # Ideal equity allocation around 60%
                min(fixed_income_percentage / 30.0, 1.0),  # Ideal fixed income around 30%
                min(total_investment_count / 10.0, 1.0)  # More holdings = better diversification
            ]
            portfolio_diversification_score = sum(diversification_components) / len(diversification_components)

            # Unrealized gains/losses
            unrealized_gains_losses = total_fair_market_value - total_book_value if total_book_value > 0 else 0.0

            # Investment strategy assessment
            investment_strategy_type = "Balanced"
            if equity_percentage >= 70:
                investment_strategy_type = "Growth"
            elif fixed_income_percentage >= 60:
                investment_strategy_type = "Income"
            elif cash_equivalent_percentage >= 30:
                investment_strategy_type = "Conservative"

            # Investment volatility assessment
            investment_volatility_assessment = "Medium"
            if equity_percentage >= 80:
                investment_volatility_assessment = "High"
            elif equity_percentage <= 30:
                investment_volatility_assessment = "Low"

            # Grant capacity analysis - key for grant research intelligence
            # Estimate sustainable grant capacity based on investment income
            estimated_annual_return = 0.05  # Conservative 5% assumption
            if investment_strategy_type == "Growth":
                estimated_annual_return = 0.07
            elif investment_strategy_type == "Income":
                estimated_annual_return = 0.04

            sustainable_grant_capacity = total_investment_value * estimated_annual_return

            # Grant funding stability assessment
            grant_funding_stability = "Stable"
            if portfolio_diversification_score >= 0.8 and investment_volatility_assessment == "Low":
                grant_funding_stability = "Very Stable"
            elif portfolio_diversification_score <= 0.4 or investment_volatility_assessment == "High":
                grant_funding_stability = "Variable"

            # Endowment sustainability estimate
            endowment_sustainability_years = None
            if sustainable_grant_capacity > 0:
                # Estimate how many years foundation could operate at current grant levels
                endowment_sustainability_years = min(int(total_investment_value / sustainable_grant_capacity), 100)

            # Liquidity assessment
            liquidity_assessment = "Medium"
            if cash_equivalent_percentage >= 20:
                liquidity_assessment = "High"
            elif cash_equivalent_percentage <= 5 and equity_percentage >= 80:
                liquidity_assessment = "Low"

            # Professional management indicators
            professional_management_indicators = (
                total_investment_count >= 10 and  # Diversified portfolio suggests professional management
                portfolio_diversification_score >= 0.6  # Good diversification
            )

            # Grant capacity trend assessment
            grant_capacity_trend = "Stable"
            if unrealized_gains_losses > 0 and unrealized_gains_losses / total_investment_value > 0.1:
                grant_capacity_trend = "Growing"
            elif unrealized_gains_losses < 0 and abs(unrealized_gains_losses) / total_investment_value > 0.1:
                grant_capacity_trend = "Declining"

            # Multi-year grant feasibility
            multi_year_grant_feasibility = "Medium"
            if grant_funding_stability in ["Very Stable", "Stable"] and grant_capacity_trend in ["Growing", "Stable"]:
                multi_year_grant_feasibility = "High"
            elif grant_funding_stability == "Variable" or grant_capacity_trend == "Declining":
                multi_year_grant_feasibility = "Low"

            return InvestmentAnalysis(
                ein=ein,
                tax_year=tax_year,
                total_investment_value=total_investment_value,
                total_investment_count=total_investment_count,
                portfolio_diversification_score=portfolio_diversification_score,
                equity_percentage=equity_percentage,
                fixed_income_percentage=fixed_income_percentage,
                alternative_investments_percentage=alternative_investments_percentage,
                cash_equivalent_percentage=cash_equivalent_percentage,
                unrealized_gains_losses=unrealized_gains_losses,
                investment_return_estimate=estimated_annual_return,
                investment_volatility_assessment=investment_volatility_assessment,
                sustainable_grant_capacity=sustainable_grant_capacity,
                grant_funding_stability=grant_funding_stability,
                endowment_sustainability_years=endowment_sustainability_years,
                investment_strategy_type=investment_strategy_type,
                liquidity_assessment=liquidity_assessment,
                professional_management_indicators=professional_management_indicators,
                grant_capacity_trend=grant_capacity_trend,
                multi_year_grant_feasibility=multi_year_grant_feasibility,
                data_source="Form 990-PF Investment Analysis"
            )

        except Exception as e:
            print(f"     Error analyzing foundation investments: {e}")
            return None

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