"""
990 Tax Filing Validation Pipeline

Cross-validates scraped web data against authoritative IRS 990 tax filing data.

This pipeline is the KEY differentiator of Catalynx web intelligence:
- Verifies leadership against 990 Part VII (Officers/Directors)
- Validates financial data against 990 Part I (Revenue/Expenses)
- Cross-checks mission statements
- Calculates confidence scores based on verification results

Architecture:
1. Spider scrapes website → raw Item data
2. This pipeline enriches with 990 verification status
3. Downstream pipeline converts to BAML structured output
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import difflib

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.tax_filing_leadership_service import TaxFilingLeadershipService, TaxFilingBaseline

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of 990 verification check"""
    verified: bool
    confidence_score: float  # 0.0-1.0
    verification_method: str
    matched_990_data: Optional[Dict[str, Any]] = None
    verification_notes: List[str] = None

    def __post_init__(self):
        if self.verification_notes is None:
            self.verification_notes = []


class NinetyValidationPipeline:
    """
    Pipeline to validate scraped data against 990 tax filing data.

    For each scraped item, attempts to:
    1. Load 990 tax filing baseline for the EIN
    2. Verify leadership data (names, titles, compensation)
    3. Verify financial data (revenue, assets, expenses)
    4. Calculate overall verification confidence score
    5. Add verification metadata to item
    """

    def __init__(self):
        self.tax_service = TaxFilingLeadershipService(context="web_intelligence")
        self._baseline_cache = {}  # Cache 990 data per-spider run

    async def process_item(self, item, spider):
        """
        Process scraped item and add 990 verification.

        Args:
            item: Scrapy item (dict-like object with scraped data)
            spider: Scrapy spider instance

        Returns:
            item: Enhanced with verification metadata
        """
        try:
            # Check if spider has EIN
            if not hasattr(spider, 'ein') or not spider.ein:
                logger.warning(f"Spider {spider.name} has no EIN. Skipping 990 validation.")
                item['verification_enabled'] = False
                return item

            ein = spider.ein

            # Get 990 baseline (with caching)
            baseline = await self._get_or_load_baseline(ein)

            if not baseline:
                logger.warning(f"No 990 tax filing data found for EIN {ein}. Verification skipped.")
                item['verification_enabled'] = False
                item['verification_confidence'] = 0.0
                item['verification_notes'] = [f"No 990 data available for EIN {ein}"]
                return item

            # Verify different data types
            item['verification_enabled'] = True
            item['baseline_filing_year'] = baseline.filing_year
            item['baseline_form_type'] = baseline.form_type

            # Verify leadership if present
            if 'leadership' in item and item['leadership']:
                await self._verify_leadership(item, baseline)

            # Verify financials if present
            if 'financial_info' in item and item['financial_info']:
                await self._verify_financials(item, baseline)

            # Verify mission if present
            if 'mission_statement' in item and item['mission_statement']:
                await self._verify_mission(item, baseline)

            # Calculate overall verification confidence
            overall_confidence = self._calculate_overall_confidence(item)
            item['verification_confidence'] = overall_confidence

            logger.info(
                f"990 Validation complete for {spider.organization_name}:\n"
                f"  Filing Year: {baseline.filing_year}\n"
                f"  Officers in 990: {len(baseline.officers) if baseline.officers else 0}\n"
                f"  Verification Confidence: {overall_confidence:.2%}"
            )

            return item

        except Exception as e:
            logger.error(f"Error in 990 validation pipeline: {e}", exc_info=True)
            item['verification_error'] = str(e)
            return item

    async def _get_or_load_baseline(self, ein: str) -> Optional[TaxFilingBaseline]:
        """
        Get 990 baseline from cache or load from service.

        Args:
            ein: Organization EIN

        Returns:
            TaxFilingBaseline or None if not found
        """
        if ein in self._baseline_cache:
            return self._baseline_cache[ein]

        # Load from tax filing service
        baseline = await self.tax_service.get_leadership_baseline(ein)

        if baseline:
            self._baseline_cache[ein] = baseline

        return baseline

    async def _verify_leadership(self, item: Dict, baseline: TaxFilingBaseline):
        """
        Verify scraped leadership data against 990 Part VII.

        For each scraped leader:
        1. Find best match in 990 officers list
        2. Compare names (fuzzy matching)
        3. Compare titles
        4. Mark verification status
        """
        if not baseline.officers:
            logger.debug("No officers in 990 baseline for leadership verification")
            return

        verified_leadership = []

        for leader in item['leadership']:
            # Find best match in 990 officers
            verification = self._match_leader_to_990(leader, baseline.officers)

            # Add verification data to leader
            leader['verification_status'] = verification.verification_method
            leader['matches_990'] = verification.verified
            leader['verification_confidence'] = verification.confidence_score

            if verification.matched_990_data:
                leader['compensation_990'] = verification.matched_990_data.get('compensation')
                leader['average_hours_per_week'] = verification.matched_990_data.get('average_hours_per_week')

            leader['verification_notes'] = verification.verification_notes

            verified_leadership.append(leader)

        # Update item
        item['leadership'] = verified_leadership

        # Calculate leadership verification rate
        verified_count = sum(1 for l in verified_leadership if l['matches_990'])
        verification_rate = verified_count / len(verified_leadership) if verified_leadership else 0.0

        item['leadership_verification_rate'] = verification_rate
        logger.debug(
            f"Leadership verification: {verified_count}/{len(verified_leadership)} "
            f"matched 990 data ({verification_rate:.1%})"
        )

    def _match_leader_to_990(self, leader: Dict, officers: List) -> VerificationResult:
        """
        Match a scraped leader to 990 officer using fuzzy matching.

        Args:
            leader: Scraped leader dict with 'name' and 'title'
            officers: List of 990 officers

        Returns:
            VerificationResult with match details
        """
        scraped_name = leader.get('name', '').strip().lower()
        scraped_title = leader.get('title', '').strip().lower()

        if not scraped_name:
            return VerificationResult(
                verified=False,
                confidence_score=0.0,
                verification_method="WEB_ONLY",
                verification_notes=["No name provided for matching"]
            )

        # Try to find best match
        best_match = None
        best_score = 0.0
        best_officer = None

        for officer in officers:
            officer_name = officer.name.strip().lower()
            officer_title = officer.title.strip().lower()

            # Calculate name similarity (fuzzy matching)
            name_similarity = difflib.SequenceMatcher(None, scraped_name, officer_name).ratio()

            # Calculate title similarity
            title_similarity = difflib.SequenceMatcher(None, scraped_title, officer_title).ratio()

            # Combined score (name weighted more heavily)
            combined_score = (name_similarity * 0.7) + (title_similarity * 0.3)

            if combined_score > best_score:
                best_score = combined_score
                best_officer = officer

        # Determine verification status based on match quality
        if best_score >= 0.85:  # High confidence match
            return VerificationResult(
                verified=True,
                confidence_score=best_score,
                verification_method="VERIFIED_990",
                matched_990_data={
                    'name': best_officer.name,
                    'title': best_officer.title,
                    'compensation': best_officer.compensation,
                    'average_hours_per_week': best_officer.average_hours_per_week
                },
                verification_notes=[
                    f"Matched 990 officer: {best_officer.name} ({best_officer.title})",
                    f"Match confidence: {best_score:.1%}"
                ]
            )
        elif best_score >= 0.60:  # Partial match
            return VerificationResult(
                verified=False,
                confidence_score=best_score,
                verification_method="CONFLICTING",
                matched_990_data={
                    'name': best_officer.name,
                    'title': best_officer.title
                },
                verification_notes=[
                    f"Partial match to 990 officer: {best_officer.name} ({best_officer.title})",
                    f"Match confidence: {best_score:.1%}",
                    "Names/titles differ - possible data discrepancy"
                ]
            )
        else:  # No good match
            return VerificationResult(
                verified=False,
                confidence_score=0.0,
                verification_method="WEB_ONLY",
                verification_notes=[
                    "No matching officer found in 990 filing",
                    f"Best match score: {best_score:.1%} (too low)"
                ]
            )

    async def _verify_financials(self, item: Dict, baseline: TaxFilingBaseline):
        """
        Verify scraped financial data against 990 Part I.

        Compares:
        - Annual budget/revenue against 990 total revenue
        - Fiscal year
        - Major discrepancies flagged
        """
        financial_info = item['financial_info']

        if not baseline.total_revenue:
            financial_info['verification_notes'] = ["No financial data in 990 for verification"]
            return

        # Compare budget/revenue
        scraped_budget = financial_info.get('annual_budget')
        if scraped_budget and baseline.total_revenue:
            budget_990 = float(baseline.total_revenue)
            scraped_budget_float = float(scraped_budget) if isinstance(scraped_budget, (int, float, str)) else None

            if scraped_budget_float:
                # Calculate difference
                difference = abs(scraped_budget_float - budget_990)
                percent_diff = (difference / budget_990) * 100 if budget_990 > 0 else 100

                financial_info['budget_990_value'] = budget_990
                financial_info['budget_difference_percent'] = percent_diff

                if percent_diff < 10:  # Within 10%
                    financial_info['budget_matches_990'] = True
                    financial_info['verification_notes'] = [
                        f"Budget matches 990 within {percent_diff:.1f}%"
                    ]
                else:
                    financial_info['budget_matches_990'] = False
                    financial_info['verification_notes'] = [
                        f"Budget differs from 990 by {percent_diff:.1f}%",
                        f"Website: ${scraped_budget_float:,.0f}, 990: ${budget_990:,.0f}"
                    ]

        # Compare fiscal year
        if baseline.filing_year:
            financial_info['fiscal_year_990'] = baseline.filing_year

    async def _verify_mission(self, item: Dict, baseline: TaxFilingBaseline):
        """
        Verify mission statement against 990 mission description.

        Uses fuzzy text matching to compare web mission with 990 mission.
        """
        if not baseline.mission_description:
            item['mission_verification_notes'] = ["No mission in 990 for comparison"]
            return

        scraped_mission = item['mission_statement'].strip().lower()
        baseline_mission = baseline.mission_description.strip().lower()

        # Calculate similarity
        similarity = difflib.SequenceMatcher(None, scraped_mission, baseline_mission).ratio()

        item['mission_similarity_to_990'] = similarity

        if similarity >= 0.7:
            item['mission_verification_notes'] = [f"Mission matches 990 ({similarity:.1%} similar)"]
        elif similarity >= 0.4:
            item['mission_verification_notes'] = [f"Mission partially matches 990 ({similarity:.1%} similar)"]
        else:
            item['mission_verification_notes'] = [
                f"Mission differs from 990 ({similarity:.1%} similar)",
                "Website mission may be more current than 990 filing"
            ]

    def _calculate_overall_confidence(self, item: Dict) -> float:
        """
        Calculate overall verification confidence score.

        Combines:
        - Leadership verification rate
        - Financial verification status
        - Mission verification status
        - Data completeness

        Returns:
            float: Overall confidence 0.0-1.0
        """
        confidence_components = []

        # Leadership verification (weight: 0.4)
        if 'leadership_verification_rate' in item:
            confidence_components.append(item['leadership_verification_rate'] * 0.4)

        # Financial verification (weight: 0.3)
        if 'financial_info' in item and item['financial_info'].get('budget_matches_990'):
            confidence_components.append(0.3)
        elif 'financial_info' in item:
            confidence_components.append(0.1)  # Some financial data but not verified

        # Mission verification (weight: 0.2)
        if 'mission_similarity_to_990' in item:
            similarity = item['mission_similarity_to_990']
            confidence_components.append(similarity * 0.2)

        # Data completeness (weight: 0.1)
        has_data_count = sum([
            'leadership' in item and bool(item['leadership']),
            'financial_info' in item and bool(item['financial_info']),
            'mission_statement' in item and bool(item['mission_statement'])
        ])
        completeness_score = has_data_count / 3.0
        confidence_components.append(completeness_score * 0.1)

        # Calculate weighted average
        overall_confidence = sum(confidence_components) if confidence_components else 0.0

        return min(overall_confidence, 1.0)  # Cap at 1.0
