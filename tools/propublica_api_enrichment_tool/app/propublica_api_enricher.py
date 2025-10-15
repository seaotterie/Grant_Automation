#!/usr/bin/env python3
"""
ProPublica API Enrichment Tool - 12-Factor Agents Implementation
Human Layer Framework - Factor 4: Tools as Structured Outputs

This tool demonstrates Factor 4 by providing ProPublica API enrichment
with guaranteed structured output format, eliminating API parsing errors.

Single Responsibility: ProPublica API-only data enrichment
- Organization profiles from API
- Filing summaries and basic financial data
- Mission and activity descriptions
- Similar organization discovery
- NO XML processing (handled by separate tool)
- NO complex analysis (handled by separate tool)
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
import os

# Add the project root to the path to access existing Catalynx infrastructure
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

try:
    from src.clients.propublica_client import ProPublicaClient
    CATALYNX_INTEGRATION = True
    print("Successfully integrated with existing Catalynx ProPublica infrastructure")
except ImportError as e:
    CATALYNX_INTEGRATION = False
    print(f"Catalynx integration not available: {e}")
    print("Running in standalone mode with mock ProPublica client")


@dataclass
class ProPublicaAPIEnrichmentCriteria:
    """Input criteria for ProPublica API enrichment following Factor 4 principles."""
    target_eins: List[str]
    include_filing_history: bool = True
    years_to_include: int = 3
    include_mission_data: bool = True
    include_leadership_summary: bool = True
    include_similar_orgs: bool = False
    max_similar_orgs: int = 5


@dataclass
class ProPublicaOrganizationProfile:
    """Core organization profile from ProPublica API."""
    ein: str
    name: str
    organization_type: str = "unknown"
    state: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    ntee_code: Optional[str] = None
    ntee_description: Optional[str] = None
    mission_description: Optional[str] = None
    activity_description: Optional[str] = None
    website_url: Optional[str] = None
    ruling_date: Optional[str] = None
    classification: Optional[str] = None
    api_data_freshness: float = 0.0
    data_completeness_score: float = 0.0


@dataclass
class FilingSummary:
    """Filing summary from ProPublica API."""
    ein: str
    tax_year: int
    form_type: str
    total_revenue: Optional[float] = None
    total_expenses: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    net_assets: Optional[float] = None
    filing_date: Optional[str] = None
    pdf_url: Optional[str] = None
    data_source: str = "ProPublica API"


@dataclass
class APILeadershipSummary:
    """Basic leadership compensation data from ProPublica API."""
    ein: str
    tax_year: int
    total_compensation: Optional[float] = None
    highest_compensation: Optional[float] = None
    number_of_officers: Optional[int] = None
    compensation_data_quality: str = "Limited - API only provides totals, use XML tools for detailed rosters"
    data_source: str = "ProPublica API"


@dataclass
class SimilarOrganization:
    """Similar organization found through API search."""
    ein: str
    name: str
    state: Optional[str] = None
    ntee_code: Optional[str] = None
    revenue_amount: Optional[float] = None
    similarity_score: float = 0.0
    similarity_reasons: List[str] = field(default_factory=list)


@dataclass
class APIExecutionMetadata:
    """API execution metadata for monitoring and optimization."""
    execution_time_ms: float
    api_calls_made: int
    rate_limit_delays_ms: float = 0.0
    cache_hits: int = 0
    cache_hit_rate: float = 0.0
    failed_requests: int = 0
    success_rate: float = 0.0
    api_limitations: List[str] = field(default_factory=list)


@dataclass
class QualityAssessment:
    """Data quality assessment for the enrichment process."""
    overall_quality_score: float
    api_data_freshness: float
    completeness_distribution: List[float]
    enrichment_success_rate: float
    limitation_notes: List[str] = field(default_factory=list)


@dataclass
class ProPublicaAPIResult:
    """Complete ProPublica API enrichment result - Factor 4 structured output."""
    enriched_organizations: List[ProPublicaOrganizationProfile]
    filing_summaries: List[FilingSummary]
    leadership_summaries: List[APILeadershipSummary]
    similar_organizations: List[SimilarOrganization]
    execution_metadata: APIExecutionMetadata
    tool_name: str = "ProPublica API Enrichment Tool"
    framework_compliance: str = "Human Layer 12-Factor Agents"
    factor_4_implementation: str = "Tools as Structured Outputs - eliminates API parsing errors"
    leadership_data_note: str = "Limited API data - use XML 990/990-PF/990-EZ tools for complete leadership rosters"
    total_organizations_processed: int = 0
    organizations_enriched: int = 0
    organizations_failed: int = 0
    quality_assessment: Optional[QualityAssessment] = None


class MockProPublicaClient:
    """Mock client for testing when Catalynx integration is not available."""

    async def get_organization_by_ein(self, ein: str) -> Optional[Dict[str, Any]]:
        """Mock organization lookup."""
        # Return mock data for testing
        if ein == "812827604":  # HEROS BRIDGE
            return {
                "organization": {
                    "ein": ein,
                    "name": "HEROS BRIDGE",
                    "state": "VA",
                    "city": "WARRENTON",
                    "ntee_code": "P20",
                    "classification": "Public Charity",
                    "mission": "Educational services for K-12 students"
                },
                "filings_with_data": [
                    {
                        "tax_prd_yr": 2024,
                        "formtype": "990",
                        "totrevenue": 504030,
                        "totassetsend": 157689,
                        "totfuncexpns": 610101
                    },
                    {
                        "tax_prd_yr": 2022,
                        "formtype": "990",
                        "totrevenue": 284159,
                        "totassetsend": 137008,
                        "totfuncexpns": 268151
                    }
                ]
            }
        return None

    async def get_similar_organizations(self, ein: str, **kwargs) -> List[Dict[str, Any]]:
        """Mock similar organizations search."""
        return []


class ProPublicaAPIEnrichmentTool:
    """
    ProPublica API Enrichment Tool - 12-Factor Agents Implementation

    Demonstrates Factor 4: Tools as Structured Outputs
    Single Responsibility: ProPublica API-only data enrichment
    """

    def __init__(self):
        self.tool_name = "ProPublica API Enrichment Tool"
        self.version = "1.0.0"

        # Initialize ProPublica client (existing Catalynx infrastructure or mock)
        if CATALYNX_INTEGRATION:
            self.propublica_client = ProPublicaClient()
        else:
            self.propublica_client = MockProPublicaClient()

        # Rate limiting configuration (from existing Catalynx setup)
        self.rate_limit_delay = 0.2  # 200ms delay between requests
        self.max_retries = 3

    async def execute(self, criteria: ProPublicaAPIEnrichmentCriteria) -> ProPublicaAPIResult:
        """
        Execute ProPublica API enrichment with guaranteed structured output.

        Factor 4 Implementation: This method ALWAYS returns a ProPublicaAPIResult
        with structured data, eliminating any API parsing errors.
        """
        start_time = time.time()

        # Initialize result structure
        result = ProPublicaAPIResult(
            enriched_organizations=[],
            filing_summaries=[],
            leadership_summaries=[],
            similar_organizations=[],
            execution_metadata=APIExecutionMetadata(
                execution_time_ms=0.0,
                api_calls_made=0,
                failed_requests=0
            )
        )

        try:
            print(f"Starting ProPublica API enrichment for {len(criteria.target_eins)} organizations")

            # Process each EIN with rate limiting
            for i, ein in enumerate(criteria.target_eins):
                try:
                    # Rate limiting delay
                    if i > 0:
                        await asyncio.sleep(self.rate_limit_delay)

                    # Enrich single organization
                    await self._enrich_single_organization(ein, criteria, result)

                except Exception as e:
                    print(f"Failed to enrich EIN {ein}: {e}")
                    result.organizations_failed += 1
                    result.execution_metadata.failed_requests += 1

            # Calculate final metrics
            result.total_organizations_processed = len(criteria.target_eins)
            result.organizations_enriched = len(result.enriched_organizations)
            result.execution_metadata.execution_time_ms = (time.time() - start_time) * 1000

            if result.execution_metadata.api_calls_made > 0:
                result.execution_metadata.success_rate = (
                    (result.execution_metadata.api_calls_made - result.execution_metadata.failed_requests) /
                    result.execution_metadata.api_calls_made
                )

            # Generate quality assessment
            result.quality_assessment = self._assess_quality(result)

            print(f"ProPublica API enrichment completed:")
            print(f"   Organizations enriched: {result.organizations_enriched}")
            print(f"   Filing summaries: {len(result.filing_summaries)}")
            print(f"   Leadership summaries: {len(result.leadership_summaries)}")
            print(f"   API calls made: {result.execution_metadata.api_calls_made}")
            print(f"   Success rate: {result.execution_metadata.success_rate:.1%}")
            print(f"   Execution time: {result.execution_metadata.execution_time_ms:.1f}ms")

            return result

        except Exception as e:
            print(f"Critical error in ProPublica API enrichment: {e}")
            # Factor 4: Even on critical error, return structured result
            result.execution_metadata.execution_time_ms = (time.time() - start_time) * 1000
            result.execution_metadata.api_limitations.append(f"Critical error: {str(e)}")
            return result

    async def _enrich_single_organization(
        self,
        ein: str,
        criteria: ProPublicaAPIEnrichmentCriteria,
        result: ProPublicaAPIResult
    ) -> None:
        """Enrich a single organization using ProPublica API."""

        try:
            print(f"   Processing EIN: {ein}")

            # Get organization data from API
            org_data = await self.propublica_client.get_organization_by_ein(ein)
            result.execution_metadata.api_calls_made += 1

            if not org_data:
                print(f"   No data found for EIN {ein}")
                return

            # Extract organization profile
            org_profile = self._extract_organization_profile(ein, org_data)
            result.enriched_organizations.append(org_profile)

            # Extract filing summaries if requested
            if criteria.include_filing_history:
                filing_summaries = self._extract_filing_summaries(ein, org_data, criteria.years_to_include)
                result.filing_summaries.extend(filing_summaries)

            # Extract leadership summary if requested
            if criteria.include_leadership_summary:
                leadership_summaries = self._extract_leadership_summaries(ein, org_data, criteria.years_to_include)
                result.leadership_summaries.extend(leadership_summaries)

            # Find similar organizations if requested
            if criteria.include_similar_orgs and CATALYNX_INTEGRATION:
                similar_orgs = await self._find_similar_organizations(
                    ein, org_data, criteria.max_similar_orgs, result
                )
                result.similar_organizations.extend(similar_orgs)

        except Exception as e:
            print(f"   Error processing {ein}: {e}")
            result.execution_metadata.failed_requests += 1

    def _extract_organization_profile(self, ein: str, org_data: Dict[str, Any]) -> ProPublicaOrganizationProfile:
        """Extract organization profile from ProPublica API response."""

        organization = org_data.get('organization', {})

        profile = ProPublicaOrganizationProfile(
            ein=ein,
            name=organization.get('name', f"Organization {ein}"),
            state=organization.get('state'),
            city=organization.get('city'),
            zip_code=organization.get('zip'),
            ntee_code=organization.get('ntee_code'),
            ntee_description=organization.get('ntee_description'),
            mission_description=organization.get('mission'),
            activity_description=organization.get('activities'),
            website_url=organization.get('website'),
            ruling_date=organization.get('ruling_date'),
            classification=organization.get('classification', 'Public Charity')
        )

        # Calculate data completeness score
        fields = [profile.name, profile.state, profile.ntee_code, profile.mission_description,
                 profile.activity_description, profile.classification]
        completed_fields = sum(1 for field in fields if field)
        profile.data_completeness_score = completed_fields / len(fields)

        # API data freshness (assume recent for ProPublica)
        profile.api_data_freshness = 0.8

        return profile

    def _extract_filing_summaries(self, ein: str, org_data: Dict[str, Any], years_limit: int) -> List[FilingSummary]:
        """Extract filing summaries from ProPublica API response."""

        filings = org_data.get('filings_with_data', [])
        summaries = []

        for filing in filings[:years_limit]:
            try:
                summary = FilingSummary(
                    ein=ein,
                    tax_year=filing.get('tax_prd_yr', 0),
                    form_type=filing.get('formtype', '990'),
                    total_revenue=self._safe_float(filing.get('totrevenue')),
                    total_expenses=self._safe_float(filing.get('totfuncexpns')),
                    total_assets=self._safe_float(filing.get('totassetsend')),
                    total_liabilities=self._safe_float(filing.get('totliabend')),
                    net_assets=self._safe_float(filing.get('totnetassetsend')),
                    filing_date=filing.get('filing_date'),
                    pdf_url=filing.get('pdf_url')
                )
                summaries.append(summary)

            except Exception as e:
                print(f"   Warning: Failed to parse filing for {ein}: {e}")
                continue

        return summaries

    def _extract_leadership_summaries(self, ein: str, org_data: Dict[str, Any], years_limit: int) -> List[APILeadershipSummary]:
        """Extract basic leadership compensation data from ProPublica API response."""

        filings = org_data.get('filings_with_data', [])
        leadership_summaries = []

        for filing in filings[:years_limit]:
            try:
                # ProPublica API provides very limited leadership data
                # Typical fields: totcompnstntdir, totcompcurrdir, totcomp, compnstntdir
                total_compensation = self._safe_float(filing.get('totcomp'))
                compensation_current_directors = self._safe_float(filing.get('totcompcurrdir'))

                # Use the higher of the two values as "highest compensation"
                highest_compensation = max(
                    total_compensation or 0,
                    compensation_current_directors or 0
                ) if (total_compensation or compensation_current_directors) else None

                # Count of officers/directors not typically available in API
                officers_count = None

                if total_compensation or compensation_current_directors:
                    summary = APILeadershipSummary(
                        ein=ein,
                        tax_year=filing.get('tax_prd_yr', 0),
                        total_compensation=total_compensation,
                        highest_compensation=highest_compensation,
                        number_of_officers=officers_count
                    )
                    leadership_summaries.append(summary)

            except Exception as e:
                print(f"   Warning: Failed to parse leadership data for {ein}: {e}")
                continue

        return leadership_summaries

    async def _find_similar_organizations(
        self,
        ein: str,
        org_data: Dict[str, Any],
        max_similar: int,
        result: ProPublicaAPIResult
    ) -> List[SimilarOrganization]:
        """Find similar organizations using ProPublica API."""

        try:
            similar_orgs_data = await self.propublica_client.get_similar_organizations(
                ein=ein,
                limit=max_similar
            )
            result.execution_metadata.api_calls_made += 1

            similar_orgs = []
            for similar_data in similar_orgs_data:
                try:
                    similar_org = SimilarOrganization(
                        ein=similar_data.get('ein', ''),
                        name=similar_data.get('name', ''),
                        state=similar_data.get('state'),
                        ntee_code=similar_data.get('ntee_code'),
                        revenue_amount=self._safe_float(similar_data.get('revenue_amount')),
                        similarity_score=0.8,  # Default similarity score
                        similarity_reasons=["ProPublica API match"]
                    )
                    similar_orgs.append(similar_org)

                except Exception as e:
                    print(f"   Warning: Failed to parse similar org data: {e}")
                    continue

            return similar_orgs

        except Exception as e:
            print(f"   Warning: Similar organizations search failed: {e}")
            return []

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if value is None:
            return None

        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                cleaned = value.replace(',', '').replace('$', '').strip()
                if cleaned:
                    return float(cleaned)
        except (ValueError, TypeError):
            pass

        return None

    def _assess_quality(self, result: ProPublicaAPIResult) -> QualityAssessment:
        """Assess the quality of the enrichment results."""

        if not result.enriched_organizations:
            return QualityAssessment(
                overall_quality_score=0.0,
                api_data_freshness=0.0,
                completeness_distribution=[],
                enrichment_success_rate=0.0,
                limitation_notes=["No organizations successfully enriched"]
            )

        # Calculate metrics
        completeness_scores = [org.data_completeness_score for org in result.enriched_organizations]
        freshness_scores = [org.api_data_freshness for org in result.enriched_organizations]

        overall_quality = sum(completeness_scores) / len(completeness_scores)
        avg_freshness = sum(freshness_scores) / len(freshness_scores)
        enrichment_rate = len(result.enriched_organizations) / result.total_organizations_processed

        limitation_notes = []
        if result.execution_metadata.failed_requests > 0:
            limitation_notes.append(f"{result.execution_metadata.failed_requests} API requests failed")
        if avg_freshness < 0.5:
            limitation_notes.append("API data may not be current")

        return QualityAssessment(
            overall_quality_score=overall_quality,
            api_data_freshness=avg_freshness,
            completeness_distribution=completeness_scores,
            enrichment_success_rate=enrichment_rate,
            limitation_notes=limitation_notes
        )


# Test function for EIN 81-2827604
async def test_propublica_api_enrichment():
    """Test the ProPublica API enrichment tool with HEROS BRIDGE."""

    print("Testing ProPublica API Enrichment Tool")
    print("=" * 60)

    # Initialize tool
    tool = ProPublicaAPIEnrichmentTool()

    # Create test criteria
    criteria = ProPublicaAPIEnrichmentCriteria(
        target_eins=["812827604"],  # HEROS BRIDGE
        include_filing_history=True,
        years_to_include=3,
        include_mission_data=True,
        include_similar_orgs=False,  # Disable for faster testing
        max_similar_orgs=5
    )

    # Execute enrichment
    result = await tool.execute(criteria)

    # Display results
    print("\nEnrichment Results:")
    print(f"Tool: {result.tool_name}")
    print(f"Framework: {result.framework_compliance}")
    print(f"Factor 4: {result.factor_4_implementation}")
    print(f"Organizations processed: {result.total_organizations_processed}")
    print(f"Organizations enriched: {result.organizations_enriched}")
    print(f"Organizations failed: {result.organizations_failed}")

    if result.enriched_organizations:
        org = result.enriched_organizations[0]
        print(f"\nFirst Organization:")
        print(f"  Name: {org.name}")
        print(f"  EIN: {org.ein}")
        print(f"  State: {org.state}")
        print(f"  NTEE: {org.ntee_code}")
        print(f"  Classification: {org.classification}")
        print(f"  Data completeness: {org.data_completeness_score:.2f}")

        if org.mission_description:
            print(f"  Mission: {org.mission_description}")

    if result.filing_summaries:
        print(f"\nFiling Summaries ({len(result.filing_summaries)}):")
        for filing in result.filing_summaries:
            print(f"  {filing.tax_year} {filing.form_type}: Revenue ${filing.total_revenue:,}" if filing.total_revenue else f"  {filing.tax_year} {filing.form_type}: No revenue data")

    if result.leadership_summaries:
        print(f"\nLeadership Summaries ({len(result.leadership_summaries)}):")
        for leadership in result.leadership_summaries:
            compensation_text = f"Total: ${leadership.total_compensation:,.2f}" if leadership.total_compensation else "No compensation data"
            print(f"  {leadership.tax_year}: {compensation_text}")
        print(f"  Note: {result.leadership_data_note}")

    print(f"\nExecution Metadata:")
    print(f"  Execution time: {result.execution_metadata.execution_time_ms:.1f}ms")
    print(f"  API calls made: {result.execution_metadata.api_calls_made}")
    print(f"  Success rate: {result.execution_metadata.success_rate:.1%}")

    if result.quality_assessment:
        print(f"\nQuality Assessment:")
        print(f"  Overall quality: {result.quality_assessment.overall_quality_score:.2f}")
        print(f"  API freshness: {result.quality_assessment.api_data_freshness:.2f}")
        print(f"  Enrichment rate: {result.quality_assessment.enrichment_success_rate:.1%}")

    return result


if __name__ == "__main__":
    asyncio.run(test_propublica_api_enrichment())