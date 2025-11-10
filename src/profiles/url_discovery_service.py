"""
URL Discovery Service

Bulk URL discovery for opportunities with $0.00 cost.

Pipeline:
1. Check opportunities table cache (instant if already discovered)
2. Fetch XML 990 filing from ProPublica
3. Parse XML to extract <WebsiteAddressTxt>
4. Mark as "not_found" if no URL in 990 filing
5. Update opportunities table with results

Cost: $0.00 (no AI APIs, pure XML parsing)
Performance: 2-4 seconds per organization (includes ProPublica fetch + XML parse)
"""

import logging
import sqlite3
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path

from src.config.database_config import get_nonprofit_intelligence_db, get_catalynx_db
from src.database.database_manager import DatabaseManager
from src.utils.xml_fetcher import fetch_xml_for_ein

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
    discoveries: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.discoveries is None:
            self.discoveries = []


class URLDiscoveryService:
    """
    Service for discovering and caching organization website URLs.

    Process:
    1. Check opportunities table cache (instant if already discovered)
    2. Fetch XML 990 filing from ProPublica (2-3 seconds)
    3. Parse XML to extract <WebsiteAddressTxt>
    4. Normalize and cache URL in opportunities table

    Cost: $0.00 (no AI APIs, pure XML parsing)
    """

    def __init__(self):
        self.intelligence_db_path = get_nonprofit_intelligence_db()
        self.catalynx_db_path = get_catalynx_db()
        self.database_manager = DatabaseManager(self.catalynx_db_path)
        logger.info(f"URLDiscoveryService initialized")
        logger.info(f"Intelligence DB: {self.intelligence_db_path}")
        logger.info(f"Catalynx DB: {self.catalynx_db_path}")

    async def discover_urls_for_opportunities(
        self,
        profile_id: str,
        opportunity_ids: Optional[List[str]] = None,
        force_refresh: bool = False,
        exclude_low_priority: bool = True,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> URLDiscoveryResult:
        """
        Discover URLs for opportunities belonging to a profile.

        Args:
            profile_id: Profile ID to discover URLs for
            opportunity_ids: Optional list of specific opportunity IDs (if None, discovers all)
            force_refresh: If True, re-discover even if cached
            exclude_low_priority: If True, skip low_priority category opportunities (default: True)
            progress_callback: Optional callback for progress updates

        Returns:
            URLDiscoveryResult with statistics and discovered URLs
        """
        import time
        start_time = time.time()

        result = URLDiscoveryResult()

        try:
            # Step 1: Get opportunities for this profile
            opportunities = self._get_opportunities_for_profile(profile_id, opportunity_ids, exclude_low_priority)
            result.total = len(opportunities)

            logger.info(f"Starting URL discovery for profile {profile_id} (exclude_low_priority={exclude_low_priority})")
            logger.info(f"Total opportunities: {result.total}")

            if result.total == 0:
                logger.warning(f"No opportunities found for profile {profile_id}")
                return result

            # Step 2: Process each opportunity
            for idx, opp in enumerate(opportunities):
                opp_id = opp['id']
                ein = opp.get('ein')
                org_name = opp.get('organization_name')
                cached_url = opp.get('website_url')

                logger.debug(f"Processing {idx+1}/{result.total}: {org_name} (EIN: {ein})")

                # Check cache first (unless force_refresh)
                if cached_url and not force_refresh:
                    result.cached += 1
                    result.processed += 1
                    result.found += 1
                    logger.debug(f"  ✓ URL cached: {cached_url}")

                    if progress_callback:
                        progress_callback({
                            'processed': result.processed,
                            'total': result.total,
                            'found': result.found,
                            'cached': result.cached,
                            'organization': org_name,
                            'status': 'cached'
                        })
                    continue

                # Discover URL from 990 filings
                if ein:
                    url, source = await self._discover_url_from_990(ein)

                    if url:
                        result.discovered += 1
                        result.found += 1
                        logger.info(f"  ✓ Discovered URL: {url} (source: {source})")

                        # Update opportunities table
                        self._update_opportunity_url(
                            opp_id,
                            url,
                            source,
                            'pending'  # Pending Tool 25 verification
                        )

                        result.discoveries.append({
                            'opportunity_id': opp_id,
                            'organization_name': org_name,
                            'ein': ein,
                            'url': url,
                            'source': source
                        })
                    else:
                        result.not_found += 1
                        logger.debug(f"  ✗ No URL found for {org_name}")

                        # Mark as not_found in database
                        self._update_opportunity_url(
                            opp_id,
                            None,
                            'not_found',
                            'not_found'
                        )
                else:
                    result.not_found += 1
                    logger.debug(f"  ✗ No EIN for {org_name}")

                    self._update_opportunity_url(
                        opp_id,
                        None,
                        'not_found',
                        'not_found'
                    )

                result.processed += 1

                # Progress callback
                if progress_callback:
                    progress_callback({
                        'processed': result.processed,
                        'total': result.total,
                        'found': result.found,
                        'not_found': result.not_found,
                        'cached': result.cached,
                        'discovered': result.discovered,
                        'organization': org_name,
                        'status': 'found' if url else 'not_found'
                    })

            result.elapsed_seconds = time.time() - start_time

            logger.info(f"URL discovery complete: {result.found} found, {result.not_found} not found, {result.cached} cached in {result.elapsed_seconds:.1f}s")

            return result

        except Exception as e:
            logger.error(f"URL discovery failed: {e}", exc_info=True)
            result.elapsed_seconds = time.time() - start_time
            return result

    def _get_opportunities_for_profile(
        self,
        profile_id: str,
        opportunity_ids: Optional[List[str]] = None,
        exclude_low_priority: bool = True
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
                        json_extract(analysis_discovery, '$.category_level') as category_level
                    FROM opportunities
                    WHERE profile_id = ? AND id IN ({placeholders})
                """
                params = [profile_id] + opportunity_ids

                # Add low_priority filter if requested (INCLUSIVE: only qualified/review/consider)
                if exclude_low_priority:
                    query += " AND json_extract(analysis_discovery, '$.category_level') IN ('qualified', 'review', 'consider')"

            else:
                # All opportunities for profile
                query = """
                    SELECT
                        id,
                        ein,
                        organization_name,
                        website_url,
                        url_source,
                        json_extract(analysis_discovery, '$.category_level') as category_level
                    FROM opportunities
                    WHERE profile_id = ?
                """
                params = [profile_id]

                # Add low_priority filter if requested (INCLUSIVE: only qualified/review/consider)
                if exclude_low_priority:
                    query += " AND json_extract(analysis_discovery, '$.category_level') IN ('qualified', 'review', 'consider')"

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
