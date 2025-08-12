"""
XML Fetcher Utility - Fetch XML data from ProPublica for Schedule I extraction
"""
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class XMLFetcher:
    """Utility class to fetch XML data from ProPublica"""
    
    def __init__(self):
        self.propublica_base = "https://projects.propublica.org/nonprofits"
        self.timeout = 30
    
    async def fetch_xml_by_ein(self, ein: str) -> Optional[bytes]:
        """
        Fetch XML data for an organization by EIN.
        
        Args:
            ein: Organization EIN
            
        Returns:
            XML content as bytes, or None if not found
        """
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                
                # Step 1: Find object_id by scraping the organization page
                object_id = await self._find_object_id(session, ein)
                if not object_id:
                    logger.warning(f"No XML download link found for EIN {ein}")
                    return None
                
                # Step 2: Download XML using the object_id
                xml_content = await self._download_xml(session, object_id)
                return xml_content
                
        except Exception as e:
            logger.error(f"Error fetching XML for EIN {ein}: {e}")
            return None
    
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
        Download XML content using object_id.
        
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
                    # Check content type
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "xml" not in content_type and "application/octet-stream" not in content_type:
                        logger.warning(f"Unexpected content type for object_id {object_id}: {content_type}")
                        # Still try to process - sometimes content-type is not set correctly
                    
                    xml_content = await response.read()
                    logger.info(f"Downloaded XML for object_id {object_id} ({len(xml_content):,} bytes)")
                    return xml_content
                    
                elif response.status == 404:
                    logger.warning(f"XML file not found for object_id {object_id}")
                    return None
                else:
                    logger.error(f"Failed to download XML for object_id {object_id}: status {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error downloading XML for object_id {object_id}: {e}")
            return None


async def fetch_xml_for_ein(ein: str) -> Optional[bytes]:
    """
    Convenience function to fetch XML data for an EIN.
    
    Args:
        ein: Organization EIN
        
    Returns:
        XML content as bytes, or None if not found
    """
    fetcher = XMLFetcher()
    return await fetcher.fetch_xml_by_ein(ein)