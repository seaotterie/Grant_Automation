"""
Foundation Grantee Bundling Tool
12-Factor compliant tool for multi-foundation grant aggregation.

Purpose: Aggregate grants across multiple foundations to identify co-funded organizations
Cost: $0.00 per analysis (no AI calls)
Replaces: N/A (new capability)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Optional, Dict, List, Any, Set
import time
from datetime import datetime
from collections import defaultdict, Counter
import re
from difflib import SequenceMatcher

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext
from .bundling_models import (
    GranteeBundlingInput,
    GranteeBundlingOutput,
    BundledGrantee,
    FundingSource,
    FoundationOverlap,
    ThematicCluster,
    FundingStability,
    BUNDLING_TOOL_COST,
    GRANT_TIER_THRESHOLDS
)

# Import Schedule I tool for foundation grant extraction
from tools.schedule_i_grant_analyzer_tool.app.schedule_i_tool import analyze_schedule_i_grants


class FoundationGranteeBundlingTool(BaseTool[GranteeBundlingOutput]):
    """
    12-Factor Foundation Grantee Bundling Tool

    Factor 4: Returns structured GranteeBundlingOutput
    Factor 6: Stateless - no persistence between runs
    Factor 10: Single responsibility - multi-foundation grant aggregation only
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize bundling tool."""
        super().__init__(config)

    def get_tool_name(self) -> str:
        return "Foundation Grantee Bundling Tool"

    def get_tool_version(self) -> str:
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        return "Multi-foundation grant aggregation and co-funding analysis"

    async def _execute(
        self,
        context: ToolExecutionContext,
        bundling_input: GranteeBundlingInput
    ) -> GranteeBundlingOutput:
        """Execute multi-foundation bundling analysis."""
        start_time = time.time()

        self.logger.info(
            f"Starting multi-foundation bundling: {len(bundling_input.foundation_eins)} "
            f"foundations, years {bundling_input.tax_years}"
        )

        # Step 1: Collect grants from all foundations
        all_grants_by_foundation = await self._collect_foundation_grants(bundling_input)

        # Step 2: Aggregate by recipient (with normalization)
        aggregated_recipients = self._aggregate_by_recipient(
            all_grants_by_foundation, bundling_input
        )

        # Step 3: Identify bundled grantees (funded by ≥ min_foundations)
        bundled_grantees = self._identify_bundled_grantees(
            aggregated_recipients, bundling_input.min_foundations
        )

        # Step 4: Compute foundation overlap matrix
        overlap_matrix = self._compute_foundation_overlaps(
            all_grants_by_foundation, bundling_input.foundation_eins
        )

        # Step 5: Thematic clustering
        thematic_clusters = self._cluster_by_theme(bundled_grantees)

        # Step 6: Compute aggregate statistics
        total_grants = sum(
            len(grants) for grants in all_grants_by_foundation.values()
        )
        total_funding = sum(
            bg.total_funding for bg in bundled_grantees
        )

        # Step 7: Data quality assessment
        data_quality = self._assess_data_quality(all_grants_by_foundation)

        processing_time = time.time() - start_time

        output = GranteeBundlingOutput(
            total_foundations_analyzed=len(bundling_input.foundation_eins),
            foundation_eins=bundling_input.foundation_eins,
            tax_years_analyzed=bundling_input.tax_years,
            total_unique_grantees=len(aggregated_recipients),
            bundled_grantees=bundled_grantees,
            single_funder_grantees_count=len(aggregated_recipients) - len(bundled_grantees),
            foundation_overlap_matrix=overlap_matrix,
            top_co_funded_orgs=sorted(
                bundled_grantees, key=lambda x: x.funder_count, reverse=True
            )[:20],
            thematic_clusters=thematic_clusters,
            total_grants_analyzed=total_grants,
            total_funding_amount=total_funding,
            average_grants_per_foundation=total_grants / len(bundling_input.foundation_eins),
            average_grantees_per_foundation=len(aggregated_recipients) / len(bundling_input.foundation_eins),
            data_completeness_score=data_quality['completeness'],
            recipient_matching_confidence=data_quality['matching_confidence'],
            processing_time_seconds=processing_time,
            analysis_date=datetime.now().isoformat(),
            api_cost_usd=BUNDLING_TOOL_COST
        )

        self.logger.info(
            f"Completed bundling: {len(bundled_grantees)} bundled grantees "
            f"from {len(aggregated_recipients)} total recipients"
        )

        return output

    async def _collect_foundation_grants(
        self, input: GranteeBundlingInput
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Collect Schedule I grants from all foundations."""

        all_grants = {}

        for foundation_ein in input.foundation_eins:
            try:
                self.logger.debug(f"Fetching grants for foundation {foundation_ein}")

                # Use Schedule I analyzer to get grants
                # Note: In production, this would fetch from database or XML parser
                # For now, we'll need the grants to be provided or fetched separately

                # TODO: Integrate with XML 990-PF parser to automatically fetch grants
                # For Phase 1, we'll require grants to be provided in database

                foundation_grants = await self._fetch_foundation_grants(
                    foundation_ein, input.tax_years
                )

                if foundation_grants:
                    all_grants[foundation_ein] = foundation_grants
                    self.logger.debug(f"  Found {len(foundation_grants)} grants")

            except Exception as e:
                self.logger.warning(f"Failed to fetch grants for {foundation_ein}: {e}")
                continue

        return all_grants

    async def _fetch_foundation_grants(
        self, foundation_ein: str, tax_years: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Fetch foundation grants from database.
        """
        from .database_service import FoundationGrantsDatabaseService

        try:
            db_service = FoundationGrantsDatabaseService()
            grants = db_service.fetch_foundation_grants(foundation_ein, tax_years)

            if not grants:
                self.logger.warning(
                    f"No grants found for {foundation_ein} in years {tax_years}. "
                    "Ensure Schedule I data has been loaded into foundation_grants table."
                )

            return grants

        except Exception as e:
            self.logger.error(f"Error fetching grants for {foundation_ein}: {e}")
            return []

    def _aggregate_by_recipient(
        self,
        all_grants: Dict[str, List[Dict[str, Any]]],
        input: GranteeBundlingInput
    ) -> Dict[str, Dict[str, Any]]:
        """Aggregate grants by recipient with name normalization."""

        aggregated = {}

        for foundation_ein, grants in all_grants.items():
            for grant in grants:
                recipient_ein = grant.get('recipient_ein')
                recipient_name = grant.get('recipient_name', 'Unknown')

                # Create unique key for recipient
                if recipient_ein:
                    recipient_key = f"ein:{recipient_ein}"
                else:
                    # Use normalized name if no EIN
                    normalized = self._normalize_recipient_name(recipient_name)
                    recipient_key = f"name:{normalized}"

                # Initialize recipient if new
                if recipient_key not in aggregated:
                    aggregated[recipient_key] = {
                        'recipient_ein': recipient_ein,
                        'recipient_name': recipient_name,
                        'normalized_name': self._normalize_recipient_name(recipient_name),
                        'funding_sources': [],
                        'grant_years': set(),
                        'grant_purposes': []
                    }

                # Add funding source
                aggregated[recipient_key]['funding_sources'].append({
                    'foundation_ein': foundation_ein,
                    'foundation_name': grant.get('foundation_name', ''),
                    'amount': grant.get('grant_amount', 0),
                    'year': grant.get('tax_year', 0),
                    'purpose': grant.get('grant_purpose', ''),
                    'tier': self._classify_grant_tier(grant.get('grant_amount', 0))
                })

                aggregated[recipient_key]['grant_years'].add(grant.get('tax_year', 0))
                if grant.get('grant_purpose'):
                    aggregated[recipient_key]['grant_purposes'].append(
                        grant.get('grant_purpose')
                    )

        return aggregated

    def _identify_bundled_grantees(
        self,
        aggregated: Dict[str, Dict[str, Any]],
        min_foundations: int
    ) -> List[BundledGrantee]:
        """Identify grantees funded by multiple foundations."""

        bundled = []

        for recipient_key, recipient_data in aggregated.items():
            funding_sources = recipient_data['funding_sources']

            # Count unique funders
            unique_funders = set(fs['foundation_ein'] for fs in funding_sources)
            funder_count = len(unique_funders)

            if funder_count >= min_foundations:
                # Create BundledGrantee object
                total_funding = sum(fs['amount'] for fs in funding_sources)
                grant_years = sorted(recipient_data['grant_years'])

                bundled_grantee = BundledGrantee(
                    grantee_ein=recipient_data.get('recipient_ein'),
                    grantee_name=recipient_data['recipient_name'],
                    normalized_name=recipient_data['normalized_name'],
                    funder_count=funder_count,
                    total_funding=total_funding,
                    average_grant_size=total_funding / len(funding_sources),
                    funding_sources=[
                        FundingSource(
                            foundation_ein=fs['foundation_ein'],
                            foundation_name=fs['foundation_name'],
                            grant_amount=fs['amount'],
                            grant_year=fs['year'],
                            grant_purpose=fs['purpose'],
                            grant_tier=fs['tier']
                        )
                        for fs in funding_sources
                    ],
                    first_grant_year=min(grant_years) if grant_years else 0,
                    last_grant_year=max(grant_years) if grant_years else 0,
                    funding_consistency=self._calculate_funding_consistency(grant_years),
                    geographic_location=None,  # TODO: Extract from grant data
                    common_purposes=self._extract_common_purposes(
                        recipient_data['grant_purposes']
                    ),
                    purpose_diversity_score=self._calculate_purpose_diversity(
                        recipient_data['grant_purposes']
                    ),
                    funding_stability=self._classify_funding_stability(
                        funding_sources, grant_years
                    ),
                    co_funding_strength=self._calculate_cofunding_strength(
                        funding_sources
                    )
                )

                bundled.append(bundled_grantee)

        return bundled

    def _compute_foundation_overlaps(
        self,
        all_grants: Dict[str, List[Dict[str, Any]]],
        foundation_eins: List[str]
    ) -> List[FoundationOverlap]:
        """Compute overlap matrix for all foundation pairs."""

        overlaps = []

        # Build grantee sets for each foundation
        foundation_grantees = {}
        for foundation_ein, grants in all_grants.items():
            grantees = set()
            for grant in grants:
                ein = grant.get('recipient_ein')
                if ein:
                    grantees.add(ein)
                else:
                    # Use normalized name if no EIN
                    normalized = self._normalize_recipient_name(
                        grant.get('recipient_name', '')
                    )
                    grantees.add(f"name:{normalized}")
            foundation_grantees[foundation_ein] = grantees

        # Compute overlaps for all pairs
        for i, ein1 in enumerate(foundation_eins):
            for ein2 in foundation_eins[i+1:]:
                if ein1 not in foundation_grantees or ein2 not in foundation_grantees:
                    continue

                grantees1 = foundation_grantees[ein1]
                grantees2 = foundation_grantees[ein2]

                shared = grantees1 & grantees2
                union = grantees1 | grantees2

                if len(shared) > 0:
                    jaccard = len(shared) / len(union) if union else 0

                    overlap = FoundationOverlap(
                        foundation_ein_1=ein1,
                        foundation_name_1=all_grants[ein1][0].get('foundation_name', ''),
                        foundation_ein_2=ein2,
                        foundation_name_2=all_grants[ein2][0].get('foundation_name', ''),
                        shared_grantees_count=len(shared),
                        shared_grantee_eins=list(shared),
                        total_overlap_funding=0,  # TODO: Calculate from grants
                        jaccard_similarity=jaccard,
                        overlap_percentage_1=len(shared) / len(grantees1) if grantees1 else 0,
                        overlap_percentage_2=len(shared) / len(grantees2) if grantees2 else 0
                    )

                    overlaps.append(overlap)

        return overlaps

    def _cluster_by_theme(
        self, bundled_grantees: List[BundledGrantee]
    ) -> List[ThematicCluster]:
        """Cluster grantees by common purpose themes."""

        # Extract all purpose keywords
        keyword_to_grantees = defaultdict(list)

        for grantee in bundled_grantees:
            for purpose in grantee.common_purposes:
                keyword_to_grantees[purpose].append(grantee)

        # Create clusters for top themes
        clusters = []
        for i, (keyword, grantees) in enumerate(
            sorted(keyword_to_grantees.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        ):
            total_funding = sum(g.total_funding for g in grantees)
            funding_foundations = set()
            for g in grantees:
                for fs in g.funding_sources:
                    funding_foundations.add(fs.foundation_ein)

            cluster = ThematicCluster(
                cluster_id=f"cluster_{i}",
                cluster_name=keyword.title(),
                grantee_count=len(grantees),
                total_funding=total_funding,
                member_grantees=[g.grantee_ein or g.normalized_name for g in grantees],
                common_keywords=[keyword],
                funding_foundations=list(funding_foundations)
            )
            clusters.append(cluster)

        return clusters

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def _normalize_recipient_name(self, name: str) -> str:
        """Normalize recipient name for matching."""
        if not name:
            return ""

        # Convert to lowercase
        name = name.lower()

        # Remove common suffixes
        suffixes = [' inc', ' inc.', ' llc', ' foundation', ' fund', ' corp', ' corporation']
        for suffix in suffixes:
            name = name.replace(suffix, '')

        # Remove punctuation and extra whitespace
        name = re.sub(r'[^\w\s]', ' ', name)
        name = ' '.join(name.split())

        return name.strip()

    def _classify_grant_tier(self, amount: float) -> str:
        """Classify grant into size tier."""
        if amount >= GRANT_TIER_THRESHOLDS['major']:
            return 'major'
        elif amount >= GRANT_TIER_THRESHOLDS['significant']:
            return 'significant'
        elif amount >= GRANT_TIER_THRESHOLDS['moderate']:
            return 'moderate'
        else:
            return 'small'

    def _calculate_funding_consistency(self, grant_years: Set[int]) -> float:
        """Calculate funding consistency (0-1)."""
        if not grant_years or len(grant_years) < 2:
            return 0.5

        years_sorted = sorted(grant_years)
        year_range = years_sorted[-1] - years_sorted[0] + 1
        years_with_grants = len(grant_years)

        return years_with_grants / year_range

    def _extract_common_purposes(self, purposes: List[str]) -> List[str]:
        """Extract common keywords from grant purposes."""
        if not purposes:
            return []

        # Simple keyword extraction (can be enhanced with NLP)
        all_words = []
        for purpose in purposes:
            words = re.findall(r'\b[a-z]{4,}\b', purpose.lower())
            all_words.extend(words)

        # Count and return top keywords
        word_counts = Counter(all_words)
        # Filter out common stop words
        stop_words = {'with', 'from', 'that', 'this', 'will', 'their', 'have', 'been'}
        common = [
            word for word, count in word_counts.most_common(10)
            if word not in stop_words and count > 1
        ]

        return common[:5]

    def _calculate_purpose_diversity(self, purposes: List[str]) -> float:
        """Calculate diversity of grant purposes (0-1)."""
        if not purposes:
            return 0

        unique_purposes = set(p.lower() for p in purposes)
        return min(1.0, len(unique_purposes) / len(purposes))

    def _classify_funding_stability(
        self, funding_sources: List[Dict], grant_years: Set[int]
    ) -> str:
        """Classify funding stability pattern."""
        if not grant_years:
            return FundingStability.NEW.value

        years_sorted = sorted(grant_years)

        # New grantee (< 2 years history)
        if len(years_sorted) == 1 or years_sorted[-1] - years_sorted[0] <= 1:
            return FundingStability.NEW.value

        # Calculate year-over-year funding
        funding_by_year = defaultdict(float)
        for fs in funding_sources:
            funding_by_year[fs['year']] += fs['amount']

        # Check trend
        amounts = [funding_by_year[year] for year in years_sorted]
        if len(amounts) >= 3:
            # Simple trend detection
            increasing = all(amounts[i] <= amounts[i+1] for i in range(len(amounts)-1))
            decreasing = all(amounts[i] >= amounts[i+1] for i in range(len(amounts)-1))

            if increasing:
                return FundingStability.GROWING.value
            elif decreasing:
                return FundingStability.DECLINING.value

        # Check consistency
        consistency = self._calculate_funding_consistency(grant_years)
        if consistency > 0.7:
            return FundingStability.STABLE.value
        else:
            return FundingStability.SPORADIC.value

    def _calculate_cofunding_strength(self, funding_sources: List[Dict]) -> float:
        """Calculate co-funding strength (0-1)."""
        if len(funding_sources) <= 1:
            return 0

        # Group by year
        years_with_multiple_funders = 0
        funding_by_year = defaultdict(set)

        for fs in funding_sources:
            funding_by_year[fs['year']].add(fs['foundation_ein'])

        for year, funders in funding_by_year.items():
            if len(funders) > 1:
                years_with_multiple_funders += 1

        return years_with_multiple_funders / len(funding_by_year)

    def _assess_data_quality(
        self, all_grants: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, float]:
        """Assess data quality and completeness."""

        total_grants = 0
        grants_with_ein = 0
        grants_with_purpose = 0

        for foundation_ein, grants in all_grants.items():
            for grant in grants:
                total_grants += 1
                if grant.get('recipient_ein'):
                    grants_with_ein += 1
                if grant.get('grant_purpose'):
                    grants_with_purpose += 1

        return {
            'completeness': (grants_with_ein + grants_with_purpose) / (2 * total_grants) if total_grants > 0 else 0,
            'matching_confidence': grants_with_ein / total_grants if total_grants > 0 else 0
        }

    def get_cost_estimate(self) -> Optional[float]:
        return BUNDLING_TOOL_COST

    def validate_inputs(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate tool inputs."""
        bundling_input = kwargs.get("bundling_input")

        if not bundling_input:
            return False, "bundling_input is required"

        if not isinstance(bundling_input, GranteeBundlingInput):
            return False, "bundling_input must be GranteeBundlingInput instance"

        if not bundling_input.foundation_eins:
            return False, "foundation_eins list is required"

        if len(bundling_input.foundation_eins) < 2:
            return False, "At least 2 foundation EINs required for bundling analysis"

        return True, None


# Convenience function
async def analyze_foundation_bundling(
    foundation_eins: List[str],
    tax_years: List[int] = None,
    min_foundations: int = 2,
    include_grant_purposes: bool = True,
    geographic_filter: Optional[List[str]] = None,
    config: Optional[dict] = None
) -> ToolResult[GranteeBundlingOutput]:
    """Analyze multi-foundation grant bundling."""

    if tax_years is None:
        tax_years = [2022, 2023, 2024]

    tool = FoundationGranteeBundlingTool(config)

    bundling_input = GranteeBundlingInput(
        foundation_eins=foundation_eins,
        tax_years=tax_years,
        min_foundations=min_foundations,
        include_grant_purposes=include_grant_purposes,
        geographic_filter=geographic_filter
    )

    return await tool.execute(bundling_input=bundling_input)
