"""
XML Fetcher Utility - Fetch XML data from ProPublica for Schedule I extraction
"""
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from typing import Optional, Tuple, List, Dict, Any
from datetime import timedelta
import logging

from src.core.cache_manager import get_cache_manager, CacheType

logger = logging.getLogger(__name__)

XML_CACHE_TTL = timedelta(days=180)  # 990 XML filings are immutable once filed; IRS bulk releases ~2x/year
_XML_NOT_FOUND_SENTINEL = "__NOT_FOUND__"


class XMLFetcher:
    """Utility class to fetch XML data from ProPublica"""

    def __init__(self, context: str = "opportunity"):
        self.propublica_base = "https://projects.propublica.org/nonprofits"
        self.timeout = 30
        self.context = context  # "profile" or "opportunity"
    
    async def fetch_xml_by_ein(self, ein: str) -> Optional[bytes]:
        """
        Fetch XML data for an organization by EIN.

        Checks EIN-keyed cache first (30-day TTL). Cache hit avoids all HTTP calls.

        Args:
            ein: Organization EIN

        Returns:
            XML content as bytes, or None if not found
        """
        cache = get_cache_manager()

        # 1. Cache check (EIN-keyed)
        cached = await cache.get(ein, CacheType.XML_DOWNLOAD)
        if cached is not None:
            if cached == _XML_NOT_FOUND_SENTINEL:
                logger.debug(f"XML cache hit (not found) for EIN {ein}")
                return None
            logger.debug(f"XML cache hit for EIN {ein}")
            return cached.encode('utf-8') if isinstance(cached, str) else cached

        # 2. Original HTTP logic
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:

                # Step 1: Find object_id by scraping the organization page
                object_id = await self._find_object_id(session, ein)
                if not object_id:
                    logger.warning(f"No XML download link found for EIN {ein}")
                    await cache.set(ein, CacheType.XML_DOWNLOAD, _XML_NOT_FOUND_SENTINEL, ttl=XML_CACHE_TTL)
                    return None

                # Step 2: Download XML using the object_id
                xml_content = await self._download_xml(session, object_id)

        except Exception as e:
            logger.error(f"Error fetching XML for EIN {ein}: {e}")
            return None

        # 3. Store result
        if xml_content:
            await cache.set(ein, CacheType.XML_DOWNLOAD, xml_content, ttl=XML_CACHE_TTL)
        else:
            await cache.set(ein, CacheType.XML_DOWNLOAD, _XML_NOT_FOUND_SENTINEL, ttl=XML_CACHE_TTL)
        return xml_content
    
    async def _find_object_id(self, session: aiohttp.ClientSession, ein: str) -> Optional[str]:
        """
        Scrape ProPublica organization page to find the object_id for XML download.
        Returns the first object_id found in download-xml links.
        """
        url = f"{self.propublica_base}/organizations/{ein}"
        headers = {"User-Agent": "Grant Research Automation Tool"}
        
        try:
            async with session.get(url, headers=headers, timeout=15) as response:
                if response.status != 200:
                    logger.warning(f"Failed to access ProPublica page for EIN {ein}: status {response.status}")
                    return None
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, "html.parser")
                
                # Look for links containing "/download-xml?object_id="
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"]
                    if "/download-xml?object_id=" in href:
                        # Extract object_id from query parameters
                        parsed_url = urlparse(href)
                        query_params = parse_qs(parsed_url.query)
                        object_id = query_params.get("object_id", [None])[0]
                        if object_id:
                            logger.info(f"Found object_id {object_id} for EIN {ein}")
                            return object_id
                
                logger.warning(f"No XML download links found for EIN {ein}")
                return None
                
        except Exception as e:
            logger.error(f"Error finding object_id for EIN {ein}: {e}")
            return None
    
    async def _download_xml(self, session: aiohttp.ClientSession, object_id: str) -> Optional[bytes]:
        """
        Download XML content using object_id from ProPublica.

        Note: The AWS S3 irs-form-990 public dataset was discontinued (~Oct 2021).
        ProPublica's download-xml endpoint is the primary source; it may be blocked
        by Cloudflare bot-protection (403) for automated requests.

        Args:
            session: aiohttp session
            object_id: ProPublica object_id for the filing

        Returns:
            XML content as bytes, or None if failed
        """
        download_url = f"{self.propublica_base}/download-xml"
        headers = {
            "User-Agent": "Grant Research Automation Tool",
            "Referer": self.propublica_base
        }
        params = {"object_id": object_id}

        try:
            async with session.get(download_url, headers=headers, params=params, allow_redirects=True) as response:
                if response.status == 200:
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "xml" not in content_type and "application/octet-stream" not in content_type:
                        logger.warning(f"Unexpected content type for object_id {object_id}: {content_type}")
                    xml_content = await response.read()
                    logger.info(f"Downloaded XML for object_id {object_id} ({len(xml_content):,} bytes)")
                    return xml_content
                elif response.status == 403:
                    logger.debug(f"ProPublica XML blocked (Cloudflare) for object_id {object_id} — no XML fallback available")
                    return None
                elif response.status == 404:
                    logger.warning(f"XML not found for object_id {object_id}")
                    return None
                elif response.status == 429:
                    logger.warning(f"Rate limited for object_id {object_id}")
                    return None
                else:
                    logger.warning(f"ProPublica returned {response.status} for object_id {object_id}")
                    return None

        except Exception as e:
            logger.error(f"Error downloading XML for object_id {object_id}: {e}")
            return None

    async def find_filing_pdf_links(self, ein: str) -> List[Dict[str, Any]]:
        """
        Scrape ProPublica org page to find PDF and schedule download links.

        Extends _find_object_id() pattern — same page, different href patterns.
        Returns list of {year, form_type, pdf_url, link_text, source} dicts.
        """
        url = f"{self.propublica_base}/organizations/{ein}"
        headers = {"User-Agent": "Grant Research Automation Tool"}
        results: List[Dict[str, Any]] = []

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.warning(f"ProPublica page returned {response.status} for EIN {ein}")
                        return []

                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, "html.parser")

                    for a_tag in soup.find_all("a", href=True):
                        href = a_tag["href"]
                        link_text = a_tag.get_text(strip=True)

                        # Build absolute URL
                        if href.startswith("/"):
                            abs_url = f"https://projects.propublica.org{href}"
                        elif href.startswith("http"):
                            abs_url = href
                        else:
                            continue

                        # Skip generic IRS form PDFs (not specific filings)
                        if "irs.gov" in abs_url and "/pub/irs-pdf/" in abs_url:
                            continue

                        if "/download-pdf" in href or "/download-filing" in href:
                            results.append({
                                "year": self._extract_year_from_text(link_text),
                                "form_type": self._extract_form_type_from_text(link_text) or "990",
                                "pdf_url": abs_url,
                                "link_text": link_text,
                                "source": "scraped",
                            })
                        elif "/download-schedule" in href:
                            results.append({
                                "year": self._extract_year_from_text(link_text),
                                "form_type": self._extract_form_type_from_text(link_text) or "Schedule",
                                "pdf_url": abs_url,
                                "link_text": link_text,
                                "source": "scraped",
                            })
                        elif href.endswith(".pdf"):
                            results.append({
                                "year": self._extract_year_from_text(link_text),
                                "form_type": self._extract_form_type_from_text(link_text) or "990",
                                "pdf_url": abs_url,
                                "link_text": link_text,
                                "source": "scraped",
                            })

        except Exception as e:
            logger.error(f"Error finding PDF links for EIN {ein}: {e}")

        return results

    def _extract_year_from_text(self, text: str) -> Optional[int]:
        """Extract 4-digit year from text string."""
        import re
        match = re.search(r'\b(20\d{2})\b', text)
        return int(match.group(1)) if match else None

    def _extract_form_type_from_text(self, text: str) -> Optional[str]:
        """Extract IRS form type from text string."""
        text_upper = text.upper()
        if "990-PF" in text_upper:
            return "990-PF"
        elif "990-EZ" in text_upper:
            return "990-EZ"
        elif "SCHEDULE" in text_upper:
            import re
            m = re.search(r'SCHEDULE\s+([A-Z])', text_upper)
            return f"Schedule {m.group(1)}" if m else "Schedule"
        elif "990" in text_upper:
            return "990"
        return None


async def fetch_xml_for_ein(ein: str, context: str = "opportunity") -> Optional[bytes]:
    """
    Convenience function to fetch XML data for an EIN.

    Args:
        ein: Organization EIN
        context: "profile" or "opportunity" - affects rate limiting behavior

    Returns:
        XML content as bytes, or None if not found
    """
    fetcher = XMLFetcher(context=context)
    return await fetcher.fetch_xml_by_ein(ein)