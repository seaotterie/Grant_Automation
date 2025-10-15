"""
Form 990 ProPublica Enrichment Tool - API Enrichment and Intelligence
===================================================================

12-Factor Factor 4: Structured input/output with comprehensive ProPublica API integration
Third tool in the three-tool nonprofit grant research architecture

Key Features:
- ProPublica API integration for rich organizational data
- Peer organization discovery and analysis
- Complete filing history with document access
- Leadership and governance intelligence
- Program service detailed analysis
- Geographic expansion and service area mapping
"""

import os
import sys
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json
from datetime import datetime

# Add the src directory to path for ProPublica client import
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# For now, using simple dataclasses instead of BAML-generated classes
@dataclass
class ProPublicaEnrichmentCriteria:
    target_eins: List[str]
    enrichment_depth: str = "standard"  # basic, standard, comprehensive
    max_organizations: int = 25
    include_filing_history: bool = True
    include_peer_analysis: bool = True
    include_leadership_details: bool = True
    include_program_details: bool = True
    peer_search_radius: int = 50
    max_peer_organizations: int = 10
    filing_years_limit: int = 5

@dataclass
class ProPublicaFilingRecord:
    tax_year: int
    form_type: str
    pdf_url: Optional[str] = None
    filing_date: Optional[str] = None
    total_revenue: Optional[int] = None
    total_expenses: Optional[int] = None
    total_assets: Optional[int] = None
    has_form_data: bool = False

@dataclass
class ProPublicaLeadershipMember:
    name: str
    title: Optional[str] = None
    compensation: Optional[int] = None
    hours_per_week: Optional[float] = None
    is_key_employee: bool = False
    is_officer: bool = False
    is_director: bool = False

@dataclass
class ProPublicaPeerOrganization:
    ein: str
    name: str
    ntee_code: Optional[str] = None
    state: Optional[str] = None
    total_revenue: Optional[int] = None
    similarity_score: float = 0.0
    similarity_reasons: List[str] = None

    def __post_init__(self):
        if self.similarity_reasons is None:
            self.similarity_reasons = []

@dataclass
class ProPublicaOrganizationProfile:
    ein: str
    name: str
    organization_type: str
    filing_records: List[ProPublicaFilingRecord]
    leadership_members: List[ProPublicaLeadershipMember]
    peer_organizations: List[ProPublicaPeerOrganization]
    latest_filing_year: Optional[int] = None
    data_completeness_score: float = 0.0
    enrichment_timestamp: str = ""
    api_response_time_ms: float = 0.0

@dataclass
class ProPublicaEnrichmentResult:
    enriched_organizations: List[ProPublicaOrganizationProfile]
    execution_time_ms: float
    api_calls_made: int
    cache_hit_rate: float
    organizations_processed: int
    enrichment_success_rate: float


class ProPublicaEnrichmentTool:
    """
    Form 990 ProPublica Enrichment Tool implementing 12-factor principles

    Provides comprehensive organization enrichment using ProPublica Nonprofit Explorer API
    """

    def __init__(self):
        """Initialize ProPublica Enrichment Tool with 12-factor configuration"""

        # Factor 3: Config from environment
        self.api_base_url = os.getenv("PROPUBLICA_API_BASE_URL", "https://projects.propublica.org/nonprofits/api/v2")
        self.cache_enabled = os.getenv("PROPUBLICA_CACHE_ENABLED", "true").lower() == "true"
        self.rate_limit_calls = int(os.getenv("PROPUBLICA_RATE_LIMIT_CALLS", "500"))
        self.rate_limit_delay = float(os.getenv("PROPUBLICA_RATE_LIMIT_DELAY", "0.2"))
        self.max_organizations = int(os.getenv("PROPUBLICA_MAX_ORGANIZATIONS", "25"))
        self.timeout_seconds = int(os.getenv("PROPUBLICA_TIMEOUT_SECONDS", "30"))
        self.log_performance = os.getenv("PROPUBLICA_LOG_PERFORMANCE", "true").lower() == "true"

        # Initialize ProPublica client
        self.propublica_client = self._initialize_propublica_client()

        # Factor 6: Stateless caching
        self._cache = {} if self.cache_enabled else None

        # Performance tracking
        self._api_calls_made = 0
        self._cache_hits = 0

        logger.info("ProPublica Enrichment Tool initialized successfully")

    def _initialize_propublica_client(self):
        """Initialize ProPublica API client"""
        try:
            # Try multiple import paths for the ProPublica client
            try:
                from clients.propublica_client import ProPublicaClient
            except ImportError:
                # Try alternative path
                sys.path.insert(0, os.path.join(project_root, "src", "clients"))
                from propublica_client import ProPublicaClient

            client = ProPublicaClient()
            logger.info("ProPublica API client initialized")
            return client
        except ImportError as e:
            logger.error(f"Failed to import ProPublica client: {e}")
            logger.warning("ProPublica enrichment will be limited without API client")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize ProPublica client: {e}")
            logger.warning("ProPublica enrichment will be limited without API client")
            return None

    async def execute(self, criteria: ProPublicaEnrichmentCriteria) -> ProPublicaEnrichmentResult:
        """
        Execute ProPublica enrichment with structured criteria

        Args:
            criteria: Structured enrichment criteria

        Returns:
            ProPublicaEnrichmentResult: Comprehensive enrichment results
        """
        start_time = time.time()

        try:
            # Validate input criteria
            self._validate_criteria(criteria)

            # Reset performance counters
            self._api_calls_made = 0
            self._cache_hits = 0

            # Check cache first (Factor 6: Stateless caching)
            cache_key = self._make_cache_key(criteria)
            if self.cache_enabled and cache_key in self._cache:
                logger.info("Returning cached ProPublica enrichment result")
                self._cache_hits += 1
                return self._cache[cache_key]

            # Process organizations
            logger.info(f"Enriching {len(criteria.target_eins)} organizations with ProPublica API")

            enriched_organizations = []
            organizations_processed = 0
            organizations_failed = 0

            for ein in criteria.target_eins[:criteria.max_organizations]:
                try:
                    profile = await self._enrich_organization(ein, criteria)
                    if profile:
                        enriched_organizations.append(profile)
                        organizations_processed += 1
                    else:
                        organizations_failed += 1

                    # Rate limiting delay
                    if self.rate_limit_delay > 0:
                        await asyncio.sleep(self.rate_limit_delay)

                except Exception as e:
                    logger.error(f"Failed to enrich organization {ein}: {str(e)}")
                    organizations_failed += 1

            # Calculate metrics
            execution_time = (time.time() - start_time) * 1000
            cache_hit_rate = self._cache_hits / max(self._api_calls_made + self._cache_hits, 1)
            success_rate = organizations_processed / max(len(criteria.target_eins), 1)

            # Create result
            result = ProPublicaEnrichmentResult(
                enriched_organizations=enriched_organizations,
                execution_time_ms=execution_time,
                api_calls_made=self._api_calls_made,
                cache_hit_rate=cache_hit_rate,
                organizations_processed=organizations_processed,
                enrichment_success_rate=success_rate
            )

            # Cache result (Factor 6: Stateless caching)
            if self.cache_enabled:
                self._cache[cache_key] = result

            # Performance logging (Factor 11: Logs as event streams)
            if self.log_performance:
                logger.info(
                    f"ProPublica Enrichment completed - "
                    f"Organizations: {organizations_processed}, "
                    f"API calls: {self._api_calls_made}, "
                    f"Time: {execution_time:.1f}ms, "
                    f"Success rate: {success_rate:.1%}"
                )

            return result

        except Exception as e:
            logger.error(f"ProPublica Enrichment execution failed: {str(e)}")
            raise

    def _validate_criteria(self, criteria: ProPublicaEnrichmentCriteria) -> None:
        """Validate the incoming criteria"""
        if not criteria.target_eins:
            raise ValueError("Target EINs are required")

        if len(criteria.target_eins) > self.max_organizations:
            raise ValueError(f"Too many organizations requested. Max: {self.max_organizations}")

        # Validate EIN formats
        for ein in criteria.target_eins:
            if not ein.isdigit() or len(ein) != 9:
                raise ValueError(f"Invalid EIN format: {ein}")

        # Validate enrichment depth
        valid_depths = ["basic", "standard", "comprehensive"]
        if criteria.enrichment_depth not in valid_depths:
            raise ValueError(f"Invalid enrichment depth. Must be one of: {valid_depths}")

    def _make_cache_key(self, criteria: ProPublicaEnrichmentCriteria) -> str:
        """Create cache key from enrichment criteria"""
        key_parts = [
            f"eins:{','.join(sorted(criteria.target_eins))}",
            f"depth:{criteria.enrichment_depth}",
            f"filing:{criteria.include_filing_history}",
            f"peer:{criteria.include_peer_analysis}",
            f"leadership:{criteria.include_leadership_details}",
            f"programs:{criteria.include_program_details}",
            f"years:{criteria.filing_years_limit}"
        ]
        return "|".join(key_parts)

    async def _enrich_organization(self, ein: str, criteria: ProPublicaEnrichmentCriteria) -> Optional[ProPublicaOrganizationProfile]:
        """Enrich a single organization using ProPublica API"""
        try:
            api_start_time = time.time()

            if not self.propublica_client:
                logger.warning(f"No ProPublica client available for enrichment of {ein}")
                return self._create_minimal_profile(ein)

            # Get organization details from ProPublica
            org_data = await self.propublica_client.get_organization_by_ein(ein)
            self._api_calls_made += 1

            if not org_data:
                logger.warning(f"Organization {ein} not found in ProPublica API")
                return None

            # Extract basic information
            name = org_data.get('name', f'Organization-{ein}')
            organization_type = self._determine_org_type(org_data)

            # Get filing records
            filing_records = []
            if criteria.include_filing_history:
                filing_records = await self._get_filing_records(ein, criteria.filing_years_limit)

            # Get leadership details
            leadership_members = []
            if criteria.include_leadership_details:
                leadership_members = self._extract_leadership_info(org_data)

            # Get peer organizations
            peer_organizations = []
            if criteria.include_peer_analysis:
                peer_organizations = await self._find_peer_organizations(
                    ein, org_data, criteria.max_peer_organizations
                )

            # Calculate metrics
            api_response_time = (time.time() - api_start_time) * 1000
            data_completeness = self._calculate_data_completeness(
                org_data, filing_records, leadership_members, peer_organizations
            )

            # Get latest filing year
            latest_filing_year = None
            if filing_records:
                latest_filing_year = max(record.tax_year for record in filing_records)

            return ProPublicaOrganizationProfile(
                ein=ein,
                name=name,
                organization_type=organization_type,
                filing_records=filing_records,
                leadership_members=leadership_members,
                peer_organizations=peer_organizations,
                latest_filing_year=latest_filing_year,
                data_completeness_score=data_completeness,
                enrichment_timestamp=datetime.now().isoformat(),
                api_response_time_ms=api_response_time
            )

        except Exception as e:
            logger.error(f"Failed to enrich organization {ein}: {str(e)}")
            return None

    def _create_minimal_profile(self, ein: str) -> ProPublicaOrganizationProfile:
        """Create minimal profile when API is not available"""
        return ProPublicaOrganizationProfile(
            ein=ein,
            name=f"Organization-{ein}",
            organization_type="unknown",
            filing_records=[],
            leadership_members=[],
            peer_organizations=[],
            data_completeness_score=0.0,
            enrichment_timestamp=datetime.now().isoformat(),
            api_response_time_ms=0.0
        )

    async def _get_filing_records(self, ein: str, years_limit: int) -> List[ProPublicaFilingRecord]:
        """Get filing records from ProPublica API"""
        try:
            filings = await self.propublica_client.get_organization_filings(ein, limit=years_limit)
            self._api_calls_made += 1

            filing_records = []
            for filing in filings:
                record = ProPublicaFilingRecord(
                    tax_year=filing.get('tax_year', 0),
                    form_type=filing.get('form_type', 'Unknown'),
                    pdf_url=filing.get('pdf_url'),
                    filing_date=filing.get('filing_date'),
                    total_revenue=filing.get('total_revenue'),
                    total_expenses=filing.get('total_expenses'),
                    total_assets=filing.get('total_assets'),
                    has_form_data=bool(filing.get('has_form_data', False))
                )
                filing_records.append(record)

            return filing_records

        except Exception as e:
            logger.error(f"Failed to get filing records for {ein}: {str(e)}")
            return []

    def _extract_leadership_info(self, org_data: Dict[str, Any]) -> List[ProPublicaLeadershipMember]:
        """Extract leadership information from organization data"""
        leadership_members = []

        # ProPublica API may have leadership data in various formats
        leadership_data = org_data.get('leadership', []) or org_data.get('officers', []) or []

        for member_data in leadership_data:
            member = ProPublicaLeadershipMember(
                name=member_data.get('name', 'Unknown'),
                title=member_data.get('title'),
                compensation=member_data.get('compensation'),
                hours_per_week=member_data.get('hours_per_week'),
                is_key_employee=member_data.get('is_key_employee', False),
                is_officer=member_data.get('is_officer', False),
                is_director=member_data.get('is_director', False)
            )
            leadership_members.append(member)

        return leadership_members

    async def _find_peer_organizations(self, ein: str, org_data: Dict[str, Any], max_peers: int) -> List[ProPublicaPeerOrganization]:
        """Find peer organizations using ProPublica API"""
        try:
            # Get similar organizations from ProPublica
            similar_orgs = await self.propublica_client.get_similar_organizations(
                ein, limit=max_peers
            )
            self._api_calls_made += 1

            peer_organizations = []
            for similar_org in similar_orgs:
                # Calculate similarity score based on available data
                similarity_score = self._calculate_similarity_score(org_data, similar_org)

                peer = ProPublicaPeerOrganization(
                    ein=similar_org.get('ein', ''),
                    name=similar_org.get('name', 'Unknown'),
                    ntee_code=similar_org.get('ntee_code'),
                    state=similar_org.get('state'),
                    total_revenue=similar_org.get('total_revenue'),
                    similarity_score=similarity_score,
                    similarity_reasons=self._generate_similarity_reasons(org_data, similar_org)
                )
                peer_organizations.append(peer)

            # Sort by similarity score
            peer_organizations.sort(key=lambda x: x.similarity_score, reverse=True)

            return peer_organizations

        except Exception as e:
            logger.error(f"Failed to find peer organizations for {ein}: {str(e)}")
            return []

    def _determine_org_type(self, org_data: Dict[str, Any]) -> str:
        """Determine organization type from ProPublica data"""
        # Check various fields that might indicate organization type
        org_type = org_data.get('organization_type', '').lower()
        subsection = org_data.get('subsection', '')
        foundation_code = org_data.get('foundation_code', '')

        if 'foundation' in org_type or foundation_code:
            return "private_foundation"
        elif 'charity' in org_type or subsection == '03':
            return "public_charity"
        else:
            return "other"

    def _calculate_similarity_score(self, org1: Dict[str, Any], org2: Dict[str, Any]) -> float:
        """Calculate similarity score between two organizations"""
        score = 0.0
        max_score = 0.0

        # NTEE code similarity (40% weight)
        if org1.get('ntee_code') and org2.get('ntee_code'):
            max_score += 0.4
            if org1['ntee_code'] == org2['ntee_code']:
                score += 0.4
            elif org1['ntee_code'][:1] == org2['ntee_code'][:1]:  # Same major group
                score += 0.2

        # State similarity (20% weight)
        if org1.get('state') and org2.get('state'):
            max_score += 0.2
            if org1['state'] == org2['state']:
                score += 0.2

        # Revenue similarity (40% weight)
        if org1.get('total_revenue') and org2.get('total_revenue'):
            max_score += 0.4
            revenue1 = org1['total_revenue']
            revenue2 = org2['total_revenue']
            if revenue1 > 0 and revenue2 > 0:
                ratio = min(revenue1, revenue2) / max(revenue1, revenue2)
                score += 0.4 * ratio

        return score / max_score if max_score > 0 else 0.0

    def _generate_similarity_reasons(self, org1: Dict[str, Any], org2: Dict[str, Any]) -> List[str]:
        """Generate human-readable similarity reasons"""
        reasons = []

        if org1.get('ntee_code') == org2.get('ntee_code'):
            reasons.append(f"Same NTEE code ({org1.get('ntee_code')})")
        elif org1.get('ntee_code', '')[:1] == org2.get('ntee_code', '')[:1]:
            reasons.append(f"Same NTEE major group ({org1.get('ntee_code', '')[:1]})")

        if org1.get('state') == org2.get('state'):
            reasons.append(f"Same state ({org1.get('state')})")

        # Revenue similarity
        if org1.get('total_revenue') and org2.get('total_revenue'):
            revenue1 = org1['total_revenue']
            revenue2 = org2['total_revenue']
            if abs(revenue1 - revenue2) / max(revenue1, revenue2) < 0.5:
                reasons.append("Similar revenue size")

        return reasons

    def _calculate_data_completeness(self, org_data: Dict[str, Any],
                                   filing_records: List[ProPublicaFilingRecord],
                                   leadership_members: List[ProPublicaLeadershipMember],
                                   peer_organizations: List[ProPublicaPeerOrganization]) -> float:
        """Calculate data completeness score"""
        total_fields = 0
        completed_fields = 0

        # Basic organization data
        basic_fields = ['name', 'ntee_code', 'state', 'total_revenue']
        for field in basic_fields:
            total_fields += 1
            if org_data.get(field):
                completed_fields += 1

        # Filing records
        total_fields += 1
        if filing_records:
            completed_fields += 1

        # Leadership data
        total_fields += 1
        if leadership_members:
            completed_fields += 1

        # Peer analysis
        total_fields += 1
        if peer_organizations:
            completed_fields += 1

        return completed_fields / total_fields if total_fields > 0 else 0.0


# Test functionality
if __name__ == "__main__":
    async def test_propublica_tool():
        print("Testing ProPublica Enrichment Tool...")

        # Initialize tool
        tool = ProPublicaEnrichmentTool()
        print("Tool initialized successfully")

        # Test with known EIN
        test_ein = "300219424"  # United Way of the National Capital Area
        criteria = ProPublicaEnrichmentCriteria(
            target_eins=[test_ein],
            enrichment_depth="standard",
            include_filing_history=True,
            include_peer_analysis=True
        )

        print(f"Enriching organization: {test_ein}")
        result = await tool.execute(criteria)

        print(f"Enrichment completed:")
        print(f"  Organizations processed: {result.organizations_processed}")
        print(f"  API calls made: {result.api_calls_made}")
        print(f"  Execution time: {result.execution_time_ms:.1f}ms")
        print(f"  Success rate: {result.enrichment_success_rate:.1%}")

        if result.enriched_organizations:
            org = result.enriched_organizations[0]
            print(f"\nOrganization Details:")
            print(f"  Name: {org.name}")
            print(f"  Type: {org.organization_type}")
            print(f"  Filing records: {len(org.filing_records)}")
            print(f"  Leadership members: {len(org.leadership_members)}")
            print(f"  Peer organizations: {len(org.peer_organizations)}")
            print(f"  Data completeness: {org.data_completeness_score:.2f}")

        print("\nProPublica Enrichment Tool test completed!")

    asyncio.run(test_propublica_tool())