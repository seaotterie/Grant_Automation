"""
URL Discovery Service

Bulk URL discovery for opportunities using the Enhanced URL Discovery Pipeline.

Pipeline Stages (cascading – stops when URL found):
  0: User-provided URL (0.95 confidence)          - $0.00
  B: Bulk DB lookup — organization_websites table (0.85) - $0.00 (instant)
  1: 990 XML WebsiteAddressTxt via ProPublica (0.85) - $0.00
  2: Multi-year 990 + cross-form consolidation (0.82) - $0.00
  3: ProPublica JSON API website field (0.80)      - $0.00
  4: DuckDuckGo + Wikidata public APIs (0.70)      - $0.00
  6: Haiku URL predictor + validation (0.65-0.85)  - ~$0.001/org
  8: Org name → domain heuristic (0.50)            - $0.00

Estimated discovery rate: ~73% (up from ~35% with single-stage 990 XML)
Cost: ~$0.38 per 1000 orgs (only orgs reaching stage 6 incur cost)
"""

import asyncio
import logging
import sqlite3
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime, timezone
from dataclasses import dataclass

from src.config.database_config import get_nonprofit_intelligence_db, get_catalynx_db
from src.database.database_manager import DatabaseManager
from src.core.enhanced_url_discovery import EnhancedURLDiscoveryPipeline

logger = logging.getLogger(__name__)


@dataclass
class URLDiscoveryResult:
    """Result from URL discovery operation."""
    total: int = 0
    processed: int = 0
    found: int = 0
    not_found: int = 0
    cached: int = 0
    discovered: int = 0
    elapsed_seconds: float = 0.0
    total_cost_usd: float = 0.0
    discoveries: List[Dict[str, Any]] = None
    stage_breakdown: Dict[int, int] = None

    def __post_init__(self):
        if self.discoveries is None:
            self.discoveries = []
        if self.stage_breakdown is None:
            self.stage_breakdown = {}


class URLDiscoveryService:
    """
    Service for discovering and caching organization website URLs.

    Uses the Enhanced URL Discovery Pipeline with 6 cascading stages
    for ~73% discovery rate at near-zero cost.
    """

    def __init__(self):
        self.intelligence_db_path = get_nonprofit_intelligence_db()
        self.catalynx_db_path = get_catalynx_db()
        self.database_manager = DatabaseManager(self.catalynx_db_path)
        self._pipeline = EnhancedURLDiscoveryPipeline(
            validate_urls=True,
            check_ein_on_page=True,
        )
        logger.info("URLDiscoveryService initialized (enhanced pipeline)")

    async def discover_urls_for_opportunities(
        self,
        profile_id: str,
        opportunity_ids: Optional[List[str]] = None,
        force_refresh: bool = False,
        exclude_low_priority: bool = True,
        limit: Optional[int] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> URLDiscoveryResult:
        """
        Discover URLs for opportunities belonging to a profile.

        Uses the enhanced 6-stage cascading pipeline for each org.

        Args:
            profile_id: Profile ID to discover URLs for
            opportunity_ids: Optional list of specific opportunity IDs
            force_refresh: If True, re-discover even if cached
            exclude_low_priority: If True, skip low_priority category opportunities
            progress_callback: Optional callback for progress updates

        Returns:
            URLDiscoveryResult with statistics and discovered URLs
        """
        import time
        start_time = time.time()

        result = URLDiscoveryResult()

        try:
            opportunities = await asyncio.to_thread(
                self._get_opportunities_for_profile,
                profile_id, opportunity_ids, exclude_low_priority, limit
            )
            result.total = len(opportunities)

            logger.info(
                f"Starting enhanced URL discovery for profile {profile_id} "
                f"({result.total} opportunities, exclude_low_priority={exclude_low_priority})"
            )

            if result.total == 0:
                logger.warning(f"No opportunities found for profile {profile_id}")
                return result

            for idx, opp in enumerate(opportunities):
                opp_id = opp['id']
                ein = opp.get('ein')
                org_name = opp.get('organization_name', 'Unknown')
                cached_url = opp.get('website_url')
                url_source = opp.get('url_source')

                logger.debug(f"Processing {idx+1}/{result.total}: {org_name} (EIN: {ein})")

                # Skip if already processed (found or not_found), unless force_refresh
                if (cached_url is not None or url_source is not None) and not force_refresh:
                    result.processed += 1
                    if cached_url:
                        result.cached += 1
                        result.found += 1
                    else:
                        result.not_found += 1

                    if progress_callback:
                        progress_callback({
                            'processed': result.processed,
                            'total': result.total,
                            'found': result.found,
                            'not_found': result.not_found,
                            'cached': result.cached,
                            'organization': org_name,
                            'status': 'cached' if cached_url else 'not_found',
                        })
                    continue

                # Fast-path: check bulk-loaded organization_websites table before
                # hitting the ProPublica pipeline (instant DB lookup, no network call)
                if ein and not force_refresh:
                    bulk_url = await asyncio.to_thread(self._lookup_bulk_website, ein)
                    if bulk_url:
                        await asyncio.to_thread(
                            self._update_opportunity_url, opp_id, bulk_url, '990_xml_bulk', 'bulk_loaded'
                        )
                        result.discovered += 1
                        result.found += 1
                        result.processed += 1
                        result.stage_breakdown['bulk_db'] = result.stage_breakdown.get('bulk_db', 0) + 1
                        logger.info(f"  -> Bulk DB hit for {org_name}: {bulk_url}")
                        if progress_callback:
                            progress_callback({
                                'processed': result.processed,
                                'total': result.total,
                                'found': result.found,
                                'not_found': result.not_found,
                                'cached': result.cached,
                                'organization': org_name,
                                'status': 'found',
                            })
                        continue

                # Run enhanced pipeline
                if ein:
                    pipeline_result = await self._pipeline.discover(
                        ein=ein,
                        organization_name=org_name,
                    )

                    if pipeline_result.primary_url:
                        url = pipeline_result.primary_url.url
                        source = pipeline_result.primary_url.source
                        confidence = pipeline_result.primary_url.final_confidence
                        stage = pipeline_result.stage_resolved

                        result.discovered += 1
                        result.found += 1
                        result.total_cost_usd += pipeline_result.total_cost_usd

                        # Track stage breakdown
                        result.stage_breakdown[stage] = result.stage_breakdown.get(stage, 0) + 1

                        logger.info(
                            f"  -> Discovered URL: {url} "
                            f"(source={source}, stage={stage}, confidence={confidence:.2f})"
                        )

                        verification = 'verified' if confidence >= 0.70 else 'pending'
                        await asyncio.to_thread(self._update_opportunity_url, opp_id, url, source, verification)

                        result.discoveries.append({
                            'opportunity_id': opp_id,
                            'organization_name': org_name,
                            'ein': ein,
                            'url': url,
                            'source': source,
                            'stage': stage,
                            'confidence': round(confidence, 4),
                        })
                    else:
                        result.not_found += 1
                        await asyncio.to_thread(self._update_opportunity_url, opp_id, None, 'not_found', 'not_found')
                else:
                    result.not_found += 1
                    await asyncio.to_thread(self._update_opportunity_url, opp_id, None, 'not_found', 'not_found')

                result.processed += 1

                if progress_callback:
                    progress_callback({
                        'processed': result.processed,
                        'total': result.total,
                        'found': result.found,
                        'not_found': result.not_found,
                        'cached': result.cached,
                        'discovered': result.discovered,
                        'organization': org_name,
                        'status': 'found' if result.found > (result.cached + result.discovered - 1) else 'not_found',
                    })

            result.elapsed_seconds = time.time() - start_time

            logger.info(
                f"URL discovery complete: {result.found} found, "
                f"{result.not_found} not found, {result.cached} cached "
                f"in {result.elapsed_seconds:.1f}s "
                f"(cost: ${result.total_cost_usd:.4f})"
            )
            if result.stage_breakdown:
                logger.info(f"Stage breakdown: {result.stage_breakdown}")

            return result

        except Exception as e:
            logger.error(f"URL discovery failed: {e}", exc_info=True)
            result.elapsed_seconds = time.time() - start_time
            return result

    def _get_opportunities_for_profile(
        self,
        profile_id: str,
        opportunity_ids: Optional[List[str]] = None,
        exclude_low_priority: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get opportunities from database.

        Args:
            profile_id: Profile ID to fetch opportunities for
            opportunity_ids: Optional list of specific opportunity IDs
            exclude_low_priority: If True, filter out low_priority category opportunities

        Returns:
            List of opportunities with id, ein, organization_name, website_url, url_source, category_level
        """
        try:
            conn = sqlite3.connect(self.catalynx_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if opportunity_ids:
                # Specific opportunity IDs
                placeholders = ','.join('?' * len(opportunity_ids))
                query = f"""
                    SELECT
                        id,
                        ein,
                        organization_name,
                        website_url,
                        url_source,
                        category_level
                    FROM opportunities
                    WHERE profile_id = ? AND id IN ({placeholders})
                """
                params = [profile_id] + opportunity_ids

                if exclude_low_priority:
                    query += " AND category_level IN ('qualified', 'review', 'consider')"

            else:
                # All opportunities for profile
                query = """
                    SELECT
                        id,
                        ein,
                        organization_name,
                        website_url,
                        url_source,
                        category_level
                    FROM opportunities
                    WHERE profile_id = ?
                """
                params = [profile_id]

                if exclude_low_priority:
                    query += " AND category_level IN ('qualified', 'review', 'consider')"

                if limit:
                    query += f" LIMIT {limit}"

            cursor.execute(query, params)
            opportunities = [dict(row) for row in cursor.fetchall()]
            conn.close()

            # Log category breakdown
            category_counts = {}
            for opp in opportunities:
                category = opp.get('category_level', 'unknown')
                category_counts[category] = category_counts.get(category, 0) + 1
            logger.info(f"Opportunities by category: {category_counts}")

            return opportunities

        except Exception as e:
            logger.error(f"Error fetching opportunities: {e}", exc_info=True)
            return []

    def _lookup_bulk_website(self, ein: str) -> Optional[str]:
        """
        Fast-path: check organization_websites table in nonprofit_intelligence.db.
        Populated by the IRS 990 XML bulk loader from WebsiteAddressTxt field.
        Returns URL string or None if not found.
        """
        try:
            normalized = ein.replace("-", "").replace(" ", "").zfill(9)
            conn = sqlite3.connect(self.intelligence_db_path, timeout=5)
            row = conn.execute(
                "SELECT website_url FROM organization_websites WHERE ein = ?", (normalized,)
            ).fetchone()
            conn.close()
            return row[0] if row and row[0] else None
        except Exception:
            return None

    async def _discover_url_from_990(self, ein: str) -> tuple[Optional[str], Optional[str]]:
        """
        Discover URL from 990 XML filing via ProPublica.

        Process:
        1. Fetch XML 990 filing from ProPublica
        2. Parse XML to extract <WebsiteAddressTxt>
        3. Normalize and return URL

        Returns:
            Tuple of (url, source) or (None, None)
        """
        try:
            # Fetch XML from ProPublica
            xml_content = await fetch_xml_for_ein(ein, context="profile")

            if not xml_content:
                logger.debug(f"No XML 990 filing found for EIN {ein}")
                return (None, None)

            # Parse XML to extract WebsiteAddressTxt
            try:
                root = ET.fromstring(xml_content)

                # Define XML namespaces
                namespaces = {
                    '': 'http://www.irs.gov/efile'  # Default namespace
                }

                # Try to find WebsiteAddressTxt (works for 990, 990-EZ, 990-PF)
                website_elem = root.find('.//WebsiteAddressTxt', namespaces)
                if website_elem is None:
                    # Try without namespace
                    website_elem = root.find('.//WebsiteAddressTxt')

                if website_elem is not None and website_elem.text:
                    url = self._normalize_url(website_elem.text)
                    if url:
                        logger.info(f"Found website URL in 990 XML for EIN {ein}: {url}")
                        return (url, '990_xml')

                logger.debug(f"No WebsiteAddressTxt found in 990 XML for EIN {ein}")
                return (None, None)

            except ET.ParseError as e:
                logger.error(f"Failed to parse XML for EIN {ein}: {e}")
                return (None, None)

        except Exception as e:
            logger.error(f"Error fetching/parsing 990 XML for EIN {ein}: {e}", exc_info=True)
            return (None, None)

    def _normalize_url(self, url: str) -> Optional[str]:
        """
        Normalize URL format.

        Examples:
        - "WWW.EXAMPLE.ORG" -> "https://www.example.org"
        - "example.org" -> "https://example.org"
        - "HTTP://EXAMPLE.ORG" -> "https://example.org"
        """
        if not url:
            return None

        url = url.strip().lower()

        # Remove common invalid entries
        invalid_entries = ['none', 'n/a', 'na', 'null', 'unknown', '']
        if url in invalid_entries:
            return None

        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        # Remove trailing slashes
        url = url.rstrip('/')

        # Basic validation (has domain)
        if '.' not in url:
            return None

        return url

    def _update_opportunity_url(
        self,
        opportunity_id: str,
        url: Optional[str],
        source: str,
        verification_status: str
    ):
        """Update opportunity with discovered URL metadata."""
        try:
            conn = sqlite3.connect(self.catalynx_db_path)
            cursor = conn.cursor()

            now = datetime.now(timezone.utc).isoformat()

            cursor.execute("""
                UPDATE opportunities
                SET
                    website_url = ?,
                    url_source = ?,
                    url_discovered_at = ?,
                    url_verification_status = ?,
                    updated_at = ?
                WHERE id = ?
            """, (url, source, now, verification_status, now, opportunity_id))

            conn.commit()
            conn.close()

            logger.debug(f"Updated opportunity {opportunity_id}: url={url}, source={source}")

        except Exception as e:
            logger.error(f"Error updating opportunity {opportunity_id}: {e}", exc_info=True)

    async def get_url_statistics(self, profile_id: str) -> Dict[str, Any]:
        """
        Get URL availability statistics for a profile.

        Returns:
            Dictionary with URL statistics
        """
        return await asyncio.to_thread(self._get_url_statistics_sync, profile_id)

    def _get_url_statistics_sync(self, profile_id: str) -> Dict[str, Any]:
        """Synchronous implementation of URL statistics — call via asyncio.to_thread."""
        try:
            conn = sqlite3.connect(self.catalynx_db_path)
            cursor = conn.cursor()

            # Total opportunities
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM opportunities
                WHERE profile_id = ?
            """, (profile_id,))
            total = cursor.fetchone()[0]

            # URLs available
            cursor.execute("""
                SELECT COUNT(*) as available
                FROM opportunities
                WHERE profile_id = ? AND website_url IS NOT NULL AND url_source != 'not_found'
            """, (profile_id,))
            available = cursor.fetchone()[0]

            # By source
            cursor.execute("""
                SELECT url_source, COUNT(*) as count
                FROM opportunities
                WHERE profile_id = ? AND url_source IS NOT NULL
                GROUP BY url_source
            """, (profile_id,))
            by_source = {row[0]: row[1] for row in cursor.fetchall()}

            # Verification status
            cursor.execute("""
                SELECT url_verification_status, COUNT(*) as count
                FROM opportunities
                WHERE profile_id = ? AND url_verification_status IS NOT NULL
                GROUP BY url_verification_status
            """, (profile_id,))
            by_verification = {row[0]: row[1] for row in cursor.fetchall()}

            conn.close()

            missing = total - available

            return {
                'total': total,
                'available': available,
                'missing': missing,
                'percentage_available': round((available / total * 100), 1) if total > 0 else 0,
                'by_source': by_source,
                'by_verification': by_verification
            }

        except Exception as e:
            logger.error(f"Error getting URL statistics: {e}", exc_info=True)
            return {
                'total': 0,
                'available': 0,
                'missing': 0,
                'percentage_available': 0,
                'by_source': {},
                'by_verification': {}
            }
