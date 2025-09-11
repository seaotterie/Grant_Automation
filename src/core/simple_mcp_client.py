"""
Simplified MCP Client for Web Scraping
Direct implementation using subprocess for better compatibility
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
import aiohttp
import ssl
import re
from urllib.parse import urljoin, urlparse

# Import database components with fallback handling
import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from database.database_manager import DatabaseManager
except ImportError:
    DatabaseManager = None

# Handle config import gracefully - not critical for operation
try:
    from core.config import Config
    DEFAULT_DB_PATH = getattr(Config, 'DATABASE_PATH', None) or "data/catalynx.db"
except ImportError:
    DEFAULT_DB_PATH = "data/catalynx.db"

logger = logging.getLogger(__name__)

@dataclass
class SimpleFetchResult:
    """Result from web fetching operation"""
    url: str
    content: str
    title: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = None
    success: bool = True
    page_type: Optional[str] = None  # 'homepage', 'about', 'leadership', 'programs', 'contact'
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class DeepIntelligenceResult:
    """Result from multi-page deep intelligence extraction"""
    organization_url: str
    pages_scraped: List[SimpleFetchResult]
    leadership_data: List[Dict[str, str]]  # [{'name': 'John Smith', 'title': 'Board Chair', 'bio': '...'}]
    program_data: List[Dict[str, str]]     # [{'name': 'Battle Buddy', 'description': '...'}]
    contact_data: Dict[str, str]           # {'phone': '...', 'email': '...', 'address': '...'}
    mission_data: List[str]                # Detailed mission statements
    intelligence_score: int                # 0-100 based on data quality and completeness
    total_content_length: int
    processing_time: float
    success: bool = True
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class SimpleMCPClient:
    """
    Enhanced MCP client with intelligence database storage
    Uses HTTP requests for web scraping and stores results in SQL database
    """
    
    def __init__(self, timeout: int = 30, database_path: str = None):
        self.timeout = timeout
        self.database_path = database_path or DEFAULT_DB_PATH
        self.db_manager = DatabaseManager(self.database_path) if DatabaseManager else None
        
    async def fetch_url(self, url: str, max_length: int = 5000) -> SimpleFetchResult:
        """
        Fetch content from URL using aiohttp as fallback
        """
        try:
            # Create SSL context that's more permissive
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                headers = {
                    'User-Agent': 'Catalynx-Grant-Research/1.0 (Educational; +https://github.com/catalynx-research)'
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Try to extract title from full HTML
                        title = None
                        if '<title>' in content.lower():
                            try:
                                start = content.lower().find('<title>') + 7
                                end = content.lower().find('</title>', start)
                                if end > start:
                                    title = content[start:end].strip()
                            except:
                                pass
                                
                        # Convert HTML to markdown-like format (simple) first
                        clean_content = self._html_to_text(content)
                        
                        # Then truncate the processed text if needed
                        if len(clean_content) > max_length:
                            clean_content = clean_content[:max_length]
                        
                        return SimpleFetchResult(
                            url=url,
                            content=clean_content,
                            title=title,
                            success=True
                        )
                    else:
                        return SimpleFetchResult(
                            url=url,
                            content="",
                            error=f"HTTP {response.status}",
                            success=False
                        )
                        
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return SimpleFetchResult(
                url=url,
                content="",
                error=str(e),
                success=False
            )
            
    def _html_to_text(self, html: str) -> str:
        """
        Simple HTML to text conversion
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Get text and clean it up
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except ImportError:
            # Fallback if BeautifulSoup not available
            import re
            # Remove HTML tags
            clean = re.compile('<.*?>')
            text = re.sub(clean, '', html)
            # Clean up whitespace
            text = ' '.join(text.split())
            return text
            
    async def fetch_multiple_urls(self, urls: List[str], **kwargs) -> List[SimpleFetchResult]:
        """
        Fetch multiple URLs concurrently
        """
        if not urls:
            return []
            
        tasks = [self.fetch_url(url, **kwargs) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(SimpleFetchResult(
                    url=urls[i],
                    content="",
                    error=str(result),
                    success=False
                ))
            else:
                processed_results.append(result)
                
        return processed_results
    
    def _discover_high_value_links(self, homepage_content: str, base_url: str) -> Dict[str, List[str]]:
        """
        Discover high-value internal links from homepage content
        Returns categorized links for deep intelligence gathering
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(homepage_content, 'html.parser')
            
            # Link categories with their keywords and priorities
            link_categories = {
                'about': ['about', 'about-us', 'who-we-are', 'our-story', 'history', 'mission'],
                'leadership': ['board', 'leadership', 'team', 'staff', 'directors', 'management', 'executives'],
                'programs': ['programs', 'services', 'initiatives', 'what-we-do', 'our-work'],
                'contact': ['contact', 'contact-us', 'get-in-touch', 'reach-us', 'connect']
            }
            
            discovered_links = {category: [] for category in link_categories}
            
            # Find all internal links
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '').lower().strip()
                link_text = link.get_text().lower().strip()
                
                # Skip external links, anchors, and empty links
                if not href or href.startswith(('http://', 'https://', '#', 'mailto:', 'tel:')):
                    continue
                
                # Convert relative URLs to absolute
                full_url = urljoin(base_url, href)
                
                # Check if this link belongs to any high-value category
                for category, keywords in link_categories.items():
                    if any(keyword in href or keyword in link_text for keyword in keywords):
                        if full_url not in discovered_links[category]:
                            discovered_links[category].append(full_url)
                        break  # Only add to first matching category
            
            # Limit to top 2 links per category to avoid overwhelming
            for category in discovered_links:
                discovered_links[category] = discovered_links[category][:2]
            
            return discovered_links
            
        except Exception as e:
            logger.error(f"Error discovering links: {e}")
            return {category: [] for category in ['about', 'leadership', 'programs', 'contact']}
    
    def _classify_page_type(self, url: str, content: str) -> str:
        """Classify the type of page based on URL and content"""
        url_lower = url.lower()
        content_lower = content.lower()
        
        # URL-based classification
        if any(keyword in url_lower for keyword in ['about', 'who-we-are', 'our-story', 'history']):
            return 'about'
        elif any(keyword in url_lower for keyword in ['board', 'leadership', 'team', 'staff', 'directors']):
            return 'leadership'
        elif any(keyword in url_lower for keyword in ['programs', 'services', 'what-we-do', 'initiatives']):
            return 'programs'
        elif any(keyword in url_lower for keyword in ['contact', 'get-in-touch', 'reach-us']):
            return 'contact'
        
        # Content-based classification (fallback)
        if any(phrase in content_lower for phrase in ['board of directors', 'leadership team', 'our staff']):
            return 'leadership'
        elif any(phrase in content_lower for phrase in ['our programs', 'services we provide', 'initiatives']):
            return 'programs'
        elif any(phrase in content_lower for phrase in ['contact us', 'get in touch', 'reach out']):
            return 'contact'
        elif any(phrase in content_lower for phrase in ['about us', 'our mission', 'our history']):
            return 'about'
        
        return 'homepage'
    
    async def fetch_deep_intelligence(self, organization_url: str, max_pages: int = 5) -> DeepIntelligenceResult:
        """
        Perform deep intelligence gathering across multiple pages of an organization's website
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Fetch homepage
            logger.info(f"Starting deep intelligence gathering for {organization_url}")
            homepage_result = await self.fetch_url(organization_url, max_length=50000)
            
            if not homepage_result.success:
                return DeepIntelligenceResult(
                    organization_url=organization_url,
                    pages_scraped=[homepage_result],
                    leadership_data=[],
                    program_data=[],
                    contact_data={},
                    mission_data=[],
                    intelligence_score=0,
                    total_content_length=0,
                    processing_time=0,
                    success=False,
                    errors=[f"Failed to fetch homepage: {homepage_result.error}"]
                )
            
            # Classify homepage
            homepage_result.page_type = 'homepage'
            
            # Step 2: Discover high-value internal links
            discovered_links = self._discover_high_value_links(homepage_result.content, organization_url)
            
            # Step 3: Prioritize and fetch sub-pages
            priority_urls = []
            
            # Add links in priority order: leadership > programs > about > contact
            for category in ['leadership', 'programs', 'about', 'contact']:
                priority_urls.extend(discovered_links[category])
            
            # Limit to max_pages - 1 (since we already have homepage)
            sub_urls = priority_urls[:max_pages - 1]
            
            logger.info(f"Discovered {len(sub_urls)} high-value sub-pages to scrape")
            
            # Step 4: Fetch sub-pages with respectful delays
            all_results = [homepage_result]
            
            for i, sub_url in enumerate(sub_urls):
                if i > 0:  # Add delay between requests
                    await asyncio.sleep(1.5)
                
                logger.info(f"Fetching sub-page {i+1}/{len(sub_urls)}: {sub_url}")
                sub_result = await self.fetch_url(sub_url, max_length=30000)
                
                if sub_result.success:
                    sub_result.page_type = self._classify_page_type(sub_url, sub_result.content)
                    all_results.append(sub_result)
                else:
                    logger.warning(f"Failed to fetch {sub_url}: {sub_result.error}")
            
            # Step 5: Extract structured intelligence
            intelligence = self._extract_structured_intelligence(all_results)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            total_content_length = sum(len(result.content) for result in all_results)
            
            # Create the intelligence result
            result = DeepIntelligenceResult(
                organization_url=organization_url,
                pages_scraped=all_results,
                leadership_data=intelligence['leadership'],
                program_data=intelligence['programs'], 
                contact_data=intelligence['contact'],
                mission_data=intelligence['mission'],
                intelligence_score=intelligence['score'],
                total_content_length=total_content_length,
                processing_time=processing_time,
                success=True
            )
            
            # Store intelligence in database (async, don't block on failure)
            try:
                await self._store_intelligence_data(result)
            except Exception as e:
                logger.warning(f"Failed to store intelligence data: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in deep intelligence gathering: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return DeepIntelligenceResult(
                organization_url=organization_url,
                pages_scraped=[],
                leadership_data=[],
                program_data=[],
                contact_data={},
                mission_data=[],
                intelligence_score=0,
                total_content_length=0,
                processing_time=processing_time,
                success=False,
                errors=[str(e)]
            )
    
    def _extract_structured_intelligence(self, page_results: List[SimpleFetchResult]) -> Dict[str, Any]:
        """
        Extract structured intelligence from multiple pages
        Returns leadership, programs, contact, mission data with quality scoring
        """
        intelligence = {
            'leadership': [],
            'programs': [],
            'contact': {},
            'mission': [],
            'score': 0
        }
        
        # Combine all content for analysis
        all_content = ' '.join([result.content for result in page_results if result.success])
        
        # Extract leadership information
        leadership_data = self._extract_leadership_data(page_results)
        intelligence['leadership'] = leadership_data
        
        # Extract program information
        program_data = self._extract_program_data(page_results)
        intelligence['programs'] = program_data
        
        # Extract contact information
        contact_data = self._extract_contact_data(all_content)
        intelligence['contact'] = contact_data
        
        # Extract mission information
        mission_data = self._extract_mission_data(page_results)
        intelligence['mission'] = mission_data
        
        # Calculate intelligence quality score
        intelligence['score'] = self._calculate_intelligence_score(intelligence)
        
        return intelligence
    
    def _extract_leadership_data(self, page_results: List[SimpleFetchResult]) -> List[Dict[str, str]]:
        """Extract actual leadership names and titles from content"""
        leadership_data = []
        
        # Focus on leadership pages first
        leadership_pages = [r for r in page_results if r.page_type == 'leadership']
        other_pages = [r for r in page_results if r.page_type != 'leadership']
        
        # Process leadership pages with higher priority
        for page in leadership_pages + other_pages:
            if not page.success:
                continue
                
            content = page.content
            leaders = self._parse_leadership_content(content)
            leadership_data.extend(leaders)
        
        # Remove duplicates and limit results
        seen_names = set()
        unique_leaders = []
        
        for leader in leadership_data:
            name_key = leader.get('name', '').lower()
            if name_key and name_key not in seen_names:
                seen_names.add(name_key)
                unique_leaders.append(leader)
                
        return unique_leaders[:10]  # Limit to top 10 leaders
    
    def _parse_leadership_content(self, content: str) -> List[Dict[str, str]]:
        """Parse leadership content to extract names and titles"""
        leaders = []
        
        # Common leadership title patterns
        title_patterns = [
            r'([A-Z][a-z]+ [A-Z][a-z]+),?\s+(CEO|President|Director|Chair|Vice\s*Chair|Secretary|Treasurer|Board\s+Member)',
            r'(CEO|President|Director|Chair|Vice\s*Chair|Secretary|Treasurer|Board\s+Member):?\s+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)\s*-\s*(CEO|President|Director|Chair|Vice\s*Chair|Secretary|Treasurer|Board\s+Member)'
        ]
        
        for pattern in title_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    # Determine which group is name and which is title
                    if any(title_word in groups[0].lower() for title_word in ['ceo', 'president', 'director', 'chair', 'secretary', 'treasurer']):
                        title, name = groups[0], groups[1]
                    else:
                        name, title = groups[0], groups[1]
                    
                    # Basic validation
                    if len(name.split()) >= 2 and not any(skip in name.lower() for skip in ['lorem', 'ipsum', 'example', 'test']):
                        leaders.append({
                            'name': name.strip(),
                            'title': title.strip(),
                            'bio': ''  # Could be enhanced with nearby content
                        })
        
        return leaders
    
    def _extract_program_data(self, page_results: List[SimpleFetchResult]) -> List[Dict[str, str]]:
        """Extract program and service information"""
        programs = []
        
        # Focus on program pages
        program_pages = [r for r in page_results if r.page_type == 'programs']
        other_pages = [r for r in page_results if r.page_type in ['homepage', 'about']]
        
        for page in program_pages + other_pages:
            if not page.success:
                continue
                
            content = page.content
            page_programs = self._parse_program_content(content)
            programs.extend(page_programs)
        
        # Remove duplicates and limit
        seen_names = set()
        unique_programs = []
        
        for program in programs:
            name_key = program.get('name', '').lower()
            if name_key and name_key not in seen_names:
                seen_names.add(name_key)
                unique_programs.append(program)
        
        return unique_programs[:8]  # Limit to top 8 programs
    
    def _parse_program_content(self, content: str) -> List[Dict[str, str]]:
        """Parse content for program names and descriptions"""
        programs = []
        
        # Look for program patterns
        program_patterns = [
            r'([A-Z][a-zA-Z\s]{5,40})\s*Program',
            r'([A-Z][a-zA-Z\s]{5,40})\s*Initiative',
            r'([A-Z][a-zA-Z\s]{5,40})\s*Service'
        ]
        
        content_lower = content.lower()
        
        # Known program keywords for Heroes Bridge and similar orgs
        known_programs = ['Battle Buddy', 'Honor Guard', 'Paw Patrol', 'Homefront', 'Veterans Services', 'Mental Health', 'Counseling', 'Support Group']
        
        for program_name in known_programs:
            if program_name.lower() in content_lower:
                # Find context around the program name
                start = content_lower.find(program_name.lower())
                context = content[max(0, start-100):start+200]
                
                programs.append({
                    'name': program_name,
                    'description': context.strip()[:200]  # Limit description length
                })
        
        # Pattern-based extraction
        for pattern in program_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                program_name = match.group(1).strip()
                if len(program_name) >= 5:  # Minimum length filter
                    programs.append({
                        'name': program_name,
                        'description': ''
                    })
        
        return programs
    
    def _extract_contact_data(self, content: str) -> Dict[str, str]:
        """Extract comprehensive contact information"""
        contact_data = {}
        
        # Email extraction
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        emails = email_pattern.findall(content)
        if emails:
            # Filter for organization emails, prioritize info@ and contact@
            org_emails = [email for email in emails if not any(generic in email.lower() for generic in ['example', 'lorem', 'test'])]
            if org_emails:
                contact_data['email'] = org_emails[0]
        
        # Phone extraction
        phone_pattern = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        phones = phone_pattern.findall(content)
        if phones:
            contact_data['phone'] = phones[0]
        
        # Address extraction (basic)
        # Look for ZIP code patterns and surrounding text
        zip_pattern = re.compile(r'\b\d{5}(?:-\d{4})?\b')
        zip_matches = zip_pattern.finditer(content)
        
        for zip_match in zip_matches:
            start = max(0, zip_match.start() - 200)
            end = min(len(content), zip_match.end() + 50)
            address_context = content[start:end].strip()
            
            # Basic address validation - look for street indicators
            if any(indicator in address_context.lower() for indicator in ['st', 'street', 'ave', 'avenue', 'rd', 'road', 'blvd', 'boulevard', 'pike']):
                contact_data['address'] = address_context[:150]  # Limit length
                break
        
        return contact_data
    
    def _extract_mission_data(self, page_results: List[SimpleFetchResult]) -> List[str]:
        """Extract detailed mission statements and organizational purpose"""
        mission_statements = []
        
        # Prioritize about pages for mission content
        about_pages = [r for r in page_results if r.page_type == 'about']
        other_pages = [r for r in page_results if r.page_type in ['homepage']]
        
        for page in about_pages + other_pages:
            if not page.success:
                continue
                
            content = page.content
            missions = self._parse_mission_content(content)
            mission_statements.extend(missions)
        
        # Remove duplicates and limit
        unique_missions = []
        for mission in mission_statements:
            if mission not in unique_missions and len(mission) > 30:
                unique_missions.append(mission)
        
        return unique_missions[:5]  # Top 5 mission statements
    
    def _parse_mission_content(self, content: str) -> List[str]:
        """Parse content for mission statements"""
        missions = []
        
        # Split content into sentences
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if 50 <= len(sentence) <= 300:  # Reasonable length
                sentence_lower = sentence.lower()
                
                # Look for mission indicators
                if any(indicator in sentence_lower for indicator in [
                    'our mission', 'we are dedicated to', 'we serve', 'we help',
                    'our purpose', 'we believe', 'committed to', 'focused on',
                    'they fought for us', 'we fight for them'  # Heroes Bridge specific
                ]):
                    missions.append(sentence.strip())
        
        return missions
    
    def _calculate_intelligence_score(self, intelligence: Dict[str, Any]) -> int:
        """Calculate quality score for extracted intelligence (0-100)"""
        score = 0
        
        # Leadership data scoring (30 points max)
        leadership_count = len(intelligence['leadership'])
        if leadership_count >= 5:
            score += 30
        elif leadership_count >= 3:
            score += 20
        elif leadership_count >= 1:
            score += 10
        
        # Program data scoring (25 points max)
        program_count = len(intelligence['programs'])
        if program_count >= 4:
            score += 25
        elif program_count >= 2:
            score += 15
        elif program_count >= 1:
            score += 8
        
        # Contact data scoring (25 points max)
        contact_score = 0
        if intelligence['contact'].get('email'):
            contact_score += 10
        if intelligence['contact'].get('phone'):
            contact_score += 10
        if intelligence['contact'].get('address'):
            contact_score += 5
        score += contact_score
        
        # Mission data scoring (20 points max)
        mission_count = len(intelligence['mission'])
        if mission_count >= 3:
            score += 20
        elif mission_count >= 2:
            score += 15
        elif mission_count >= 1:
            score += 10
        
        return min(score, 100)  # Cap at 100

    async def _store_intelligence_data(self, result: DeepIntelligenceResult, ein: str = None):
        """Store deep intelligence data in the database."""
        try:
            # Extract EIN from the organization URL if not provided
            if not ein:
                ein = self._extract_ein_from_url(result.organization_url)
                if not ein:
                    logger.warning(f"Could not extract EIN for URL: {result.organization_url}")
                    return
            
            # Store web intelligence data
            with sqlite3.connect(self.database_path) as conn:
                # Insert into web_intelligence table
                conn.execute("""
                    INSERT OR REPLACE INTO web_intelligence (
                        ein, url, scrape_date, intelligence_quality_score, 
                        content_richness_score, pages_scraped, total_content_length,
                        leadership_data, leadership_count, program_data, program_count,
                        contact_data, mission_statements, mission_count,
                        processing_duration_ms, website_structure_quality
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ein,
                    result.organization_url,
                    datetime.now().isoformat(),
                    result.intelligence_score,
                    self._calculate_content_richness_score(result),
                    len(result.pages_scraped),
                    result.total_content_length,
                    json.dumps(result.leadership_data),
                    len(result.leadership_data),
                    json.dumps(result.program_data),
                    len(result.program_data),
                    json.dumps(result.contact_data),
                    json.dumps(result.mission_data),
                    len(result.mission_data),
                    int(result.processing_time * 1000),  # Convert to milliseconds
                    self._assess_website_structure_quality(result)
                ))
                
                # Store individual board members in board_member_intelligence table
                for leader in result.leadership_data:
                    if leader.get('name'):
                        conn.execute("""
                            INSERT OR REPLACE INTO board_member_intelligence (
                                ein, member_name, normalized_name, title_position, 
                                data_source, source_confidence, biography,
                                data_quality_score, last_verified
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            ein,
                            leader['name'],
                            self._normalize_name(leader['name']),
                            leader.get('title', 'Leadership'),
                            'web_scraping',
                            'high' if leader.get('bio') else 'medium',
                            leader.get('bio', ''),
                            self._calculate_board_member_quality_score(leader),
                            datetime.now().isoformat()
                        ))
                
                # Log processing activity
                conn.execute("""
                    INSERT INTO intelligence_processing_log (
                        ein, processing_type, status, start_time, end_time,
                        duration_ms, data_points_extracted, quality_score,
                        pages_processed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ein,
                    'web_scraping',
                    'success' if result.success else 'failed',
                    (datetime.now() - datetime.timedelta(seconds=result.processing_time)).isoformat(),
                    datetime.now().isoformat(),
                    int(result.processing_time * 1000),
                    len(result.leadership_data) + len(result.program_data) + (1 if result.contact_data else 0),
                    result.intelligence_score,
                    len(result.pages_scraped)
                ))
                
                conn.commit()
                logger.info(f"✅ Stored intelligence data for EIN {ein}")
                
        except Exception as e:
            logger.error(f"Failed to store intelligence data: {e}")
            raise

    def _extract_ein_from_url(self, url: str) -> Optional[str]:
        """Extract EIN from organization URL by looking up in organization_urls table."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT ein FROM organization_urls 
                    WHERE predicted_url = ? OR predicted_url LIKE ?
                """, (url, f"%{urlparse(url).netloc}%"))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to extract EIN from URL: {e}")
            return None

    def _normalize_name(self, name: str) -> str:
        """Normalize board member name for consistent storage."""
        if not name:
            return ""
        
        # Remove common titles and suffixes
        name = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|Rev|Hon|Esq)\.?\b', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\b(Jr|Sr|II|III|IV)\.?\b', '', name, flags=re.IGNORECASE)
        
        # Clean up whitespace and punctuation
        name = re.sub(r'[^\w\s]', ' ', name)
        name = ' '.join(name.split())
        
        return name.strip().title()

    def _calculate_content_richness_score(self, result: DeepIntelligenceResult) -> float:
        """Calculate content richness based on data variety and depth."""
        richness = 0.0
        
        # Leadership data richness
        if result.leadership_data:
            richness += min(len(result.leadership_data) * 0.15, 0.30)
            # Bonus for biographical details
            bio_count = sum(1 for leader in result.leadership_data if leader.get('bio'))
            richness += min(bio_count * 0.10, 0.20)
        
        # Program data richness  
        if result.program_data:
            richness += min(len(result.program_data) * 0.10, 0.25)
        
        # Contact data richness
        contact_fields = sum(1 for key in ['phone', 'email', 'address'] if result.contact_data.get(key))
        richness += contact_fields * 0.05
        
        # Mission data richness
        if result.mission_data:
            richness += min(len(result.mission_data) * 0.08, 0.15)
        
        # Multi-page bonus
        if len(result.pages_scraped) > 1:
            richness += min((len(result.pages_scraped) - 1) * 0.05, 0.10)
        
        return min(richness, 1.0)  # Cap at 1.0

    def _assess_website_structure_quality(self, result: DeepIntelligenceResult) -> str:
        """Assess website structure quality based on page organization."""
        if len(result.pages_scraped) >= 4 and result.intelligence_score >= 70:
            return 'excellent'
        elif len(result.pages_scraped) >= 3 and result.intelligence_score >= 50:
            return 'good'  
        elif len(result.pages_scraped) >= 2 and result.intelligence_score >= 30:
            return 'moderate'
        else:
            return 'minimal'

    def _calculate_board_member_quality_score(self, leader: Dict[str, str]) -> int:
        """Calculate data quality score for individual board member."""
        score = 0
        
        # Name quality (20 points)
        if leader.get('name') and len(leader['name']) > 5:
            score += 20
        elif leader.get('name'):
            score += 10
        
        # Title quality (15 points)
        if leader.get('title') and len(leader['title']) > 3:
            score += 15
        elif leader.get('title'):
            score += 8
        
        # Biography quality (40 points) 
        bio = leader.get('bio', '')
        if len(bio) > 200:
            score += 40
        elif len(bio) > 100:
            score += 25
        elif len(bio) > 50:
            score += 15
        elif bio:
            score += 5
        
        # Contact information (25 points)
        if leader.get('email'):
            score += 15
        if leader.get('linkedin'):
            score += 10
        
        return min(score, 100)

class SimpleWebScrapingService:
    """
    Simplified web scraping service for organization data
    """
    
    def __init__(self, timeout: int = 30):
        self.client = SimpleMCPClient(timeout)
        
    async def scrape_organization_websites(
        self, 
        organization_name: str, 
        ein: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scrape organization websites for profile enhancement
        """
        urls_to_scrape = []
        
        # Build URLs to scrape
        if ein:
            # GuideStar profile (may not work due to login requirements)
            urls_to_scrape.append(f"https://www.guidestar.org/profile/{ein}")
            
        # Try common website patterns
        org_slug = organization_name.lower().replace(" ", "").replace(",", "").replace(".", "")
        potential_urls = [
            f"https://{org_slug}.org",
            f"https://www.{org_slug}.org", 
            f"https://{org_slug}.com",
            f"https://www.{org_slug}.com",
        ]
        
        # Add potential URLs
        urls_to_scrape.extend(potential_urls)
        
        # Fetch all URLs
        results = await self.client.fetch_multiple_urls(urls_to_scrape, max_length=3000)
        
        # Process results
        scraped_data = {
            "organization_name": organization_name,
            "ein": ein,
            "successful_scrapes": [],
            "failed_scrapes": [],
            "extracted_info": {
                "mission_statements": [],
                "contact_info": [],
                "programs": [],
                "leadership": [],
                "financial_info": []
            }
        }
        
        for result in results:
            if result.success and result.content and len(result.content) > 100:
                scraped_data["successful_scrapes"].append({
                    "url": result.url,
                    "title": result.title,
                    "content_length": len(result.content),
                    "timestamp": result.timestamp.isoformat()
                })
                
                # Extract key information
                self._extract_organization_info(result.content, scraped_data["extracted_info"])
                
            else:
                scraped_data["failed_scrapes"].append({
                    "url": result.url,
                    "error": result.error or "No content"
                })
                
        return scraped_data
        
    def _extract_organization_info(self, content: str, extracted_info: Dict):
        """Extract organization information from content"""
        content_lower = content.lower()
        lines = content.split('\n')
        
        # Keywords for different types of information
        mission_keywords = ["mission", "purpose", "vision", "goal", "objective", "about us"]
        contact_keywords = ["contact", "email", "phone", "address", "reach us"]
        program_keywords = ["program", "service", "initiative", "project", "offering"]
        leadership_keywords = ["board", "director", "ceo", "president", "leadership", "staff", "team"]
        
        for line in lines:
            line_clean = line.strip()
            line_lower = line_clean.lower()
            
            if len(line_clean) < 20:  # Skip very short lines
                continue
                
            # Extract mission statements
            if any(keyword in line_lower for keyword in mission_keywords):
                if len(line_clean) > 30 and len(line_clean) < 500:
                    if line_clean not in extracted_info["mission_statements"]:
                        extracted_info["mission_statements"].append(line_clean)
                        
            # Extract contact information
            elif any(keyword in line_lower for keyword in contact_keywords):
                if "@" in line_clean or "phone" in line_lower or "address" in line_lower:
                    if line_clean not in extracted_info["contact_info"]:
                        extracted_info["contact_info"].append(line_clean)
                        
            # Extract programs
            elif any(keyword in line_lower for keyword in program_keywords):
                if len(line_clean) > 20 and len(line_clean) < 300:
                    if line_clean not in extracted_info["programs"]:
                        extracted_info["programs"].append(line_clean)
                        
            # Extract leadership
            elif any(keyword in line_lower for keyword in leadership_keywords):
                if len(line_clean) > 15 and len(line_clean) < 200:
                    if line_clean not in extracted_info["leadership"]:
                        extracted_info["leadership"].append(line_clean)
        
        # Limit results to prevent overwhelming
        for key in extracted_info:
            extracted_info[key] = extracted_info[key][:10]  # Max 10 items each

# Global service instance
simple_web_scraping_service = SimpleWebScrapingService()