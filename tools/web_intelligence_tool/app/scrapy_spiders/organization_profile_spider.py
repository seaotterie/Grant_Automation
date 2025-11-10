"""
Organization Profile Spider

Use Case 1: Profile Builder - Scrapes nonprofit organization websites
to extract profile data for auto-population.

Extraction targets:
- Mission statement (About Us, Mission pages)
- Program areas (Programs, Services pages)
- Leadership team (Board, Staff pages)
- Contact information
- Financial data (if public)
- Service areas/geographic scope

This spider uses intelligent page discovery and content extraction
to build comprehensive organization profiles.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import scrapy
from scrapy.http import Response
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class OrganizationProfileSpider(scrapy.Spider):
    """
    Spider for scraping nonprofit organization profiles.

    Attributes (set by caller):
        ein: Organization EIN
        organization_name: Organization name
        user_provided_url: Optional user URL (SmartURLMiddleware handles resolution)
        use_case: "profile_builder" (for pipeline routing)
    """

    name = 'organization_profile'
    allowed_domains = []  # Set dynamically based on start_urls

    # Custom settings for this spider
    custom_settings = {
        'DEPTH_LIMIT': 3,  # Don't crawl too deep
        'DOWNLOAD_DELAY': 2.0,  # Respectful crawling
    }

    # Target page keywords for different content types
    TARGET_PAGES = {
        'mission': ['mission', 'who-we-are', 'our-story', 'vision', 'values'],
        'programs': ['programs', 'services', 'what-we-do', 'our-work', 'initiatives'],
        'leadership': ['about', 'board', 'staff', 'team', 'leadership', 'directors', 'people', 'governance', 'attorney', 'attorneys', 'officers', 'trustees'],
        'contact': ['contact', 'connect', 'reach-us', 'get-in-touch'],
        'financial': ['financials', 'annual-report', 'transparency', '990', 'financial-info']
    }

    def __init__(self, ein: str, organization_name: str, user_provided_url: Optional[str] = None, start_url: Optional[str] = None, *args, **kwargs):
        """
        Initialize spider.

        Args:
            ein: Organization EIN
            organization_name: Organization name
            user_provided_url: Optional user-provided URL (legacy - for reference)
            start_url: Optional pre-resolved URL to start scraping (NEW)
        """
        super().__init__(*args, **kwargs)

        self.ein = ein
        self.organization_name = organization_name
        self.user_provided_url = user_provided_url
        self.use_case = 'profile_builder'

        # NEW: Set start_urls directly if provided (bypasses SmartURLMiddleware)
        if start_url:
            self.start_urls = [start_url]
            logger.info(f"Spider initialized with start_url: {start_url}")
        else:
            logger.warning(f"Spider initialized without start_url - will rely on SmartURLMiddleware")

        # Initialize data collection
        self.scraped_data = {
            'mission_statement': None,
            'vision_statement': None,
            'programs': [],
            'leadership': [],
            'contact_info': {},
            'financial_info': {},
            'founded_year': None,
            'service_area': [],
            'target_populations': [],
            'key_achievements': [],
            'current_initiatives': [],
            'pages_scraped': 0,
            'pages_attempted': 0,
            'scraped_urls': [],  # List of URLs that were successfully scraped
            'extraction_errors': [],
        }

        # Track pages we've visited
        self.visited_urls = set()

        # Track pending requests for final yield
        self.requests_pending = 1  # Start with homepage request

        # Track whether we've yielded final results (to prevent double yielding)
        self.results_yielded = False

        logger.info(f"Initialized OrganizationProfileSpider for {organization_name} (EIN: {ein})")

    def start_requests(self):
        """
        Generate initial requests.

        Note: SmartURLMiddleware will have already set self.start_urls
        to the best resolved URL.
        """
        if not hasattr(self, 'start_urls') or not self.start_urls:
            logger.error(f"No start URLs available for {self.organization_name}")
            return

        # Set allowed_domains from start URL
        start_url = self.start_urls[0]
        domain = urlparse(start_url).netloc
        self.allowed_domains = [domain]

        logger.info(f"Starting scrape of {self.organization_name} from {start_url}")

        # Start with homepage
        yield scrapy.Request(
            url=start_url,
            callback=self.parse_homepage,
            errback=self.handle_error,
            meta={'page_type': 'homepage'}
        )

    def parse_homepage(self, response: Response):
        """
        Parse homepage and discover target pages.

        Extracts:
        - Links to mission, programs, leadership, contact pages
        - Any mission/overview content on homepage itself
        - Basic organization info
        """
        self.scraped_data['pages_attempted'] += 1
        self.scraped_data['pages_scraped'] += 1
        self.visited_urls.add(response.url)

        logger.info(f"Parsing homepage: {response.url}")

        # Extract homepage content
        soup = BeautifulSoup(response.text, 'lxml')

        # Try to extract mission from homepage
        mission = self._extract_mission_statement(soup, response.url)
        if mission and not self.scraped_data['mission_statement']:
            self.scraped_data['mission_statement'] = mission

        # Extract any leadership info on homepage
        leadership = self._extract_leadership(soup, response.url)
        if leadership:
            self.scraped_data['leadership'].extend(leadership)

        # Extract contact info
        contact = self._extract_contact_info(soup, response.url)
        if contact:
            self.scraped_data['contact_info'].update(contact)

        # Discover and crawl target pages
        target_links = self._discover_target_pages(response)

        for link, page_type in target_links:
            if link not in self.visited_urls:
                # Mark as visited BEFORE yielding to avoid duplicate filtering issues
                self.visited_urls.add(link)
                self.requests_pending += 1  # Track pending request
                logger.debug(f"Queued {page_type} page, requests_pending now: {self.requests_pending}")
                yield scrapy.Request(
                    url=link,
                    callback=self.parse_target_page,
                    errback=self.handle_error,
                    meta={'page_type': page_type},
                    dont_filter=True  # We're already tracking visited URLs manually
                )

        # Decrement for completed homepage
        self.requests_pending -= 1
        logger.info(f"Homepage complete, requests_pending now: {self.requests_pending}")
        if self.requests_pending == 0:
            # All pages processed - calculate quality and yield final data
            self.scraped_data['data_quality_score'] = self._calculate_data_quality()
            # Convert visited_urls set to sorted list for frontend display
            self.scraped_data['scraped_urls'] = sorted(list(self.visited_urls))
            logger.info("All pages processed, yielding final scraped data")
            self.results_yielded = True
            yield self.scraped_data

    def parse_target_page(self, response: Response):
        """
        Parse a target page (mission, programs, leadership, etc.).

        Extracts content based on page type AND discovers more links
        to enable deeper crawling (respecting DEPTH_LIMIT).
        """
        self.scraped_data['pages_attempted'] += 1

        page_type = response.meta.get('page_type', 'unknown')
        logger.info(f"Parsing {page_type} page: {response.url}")

        # CRITICAL FIX: Skip non-HTML content (PDFs, images, etc.)
        content_type = response.headers.get('Content-Type', b'').decode('utf-8', errors='ignore').lower()
        if 'pdf' in content_type or 'image' in content_type or not hasattr(response, 'text'):
            logger.warning(f"Skipping non-HTML content ({content_type}): {response.url}")
            # Decrement pending requests and check if done
            self.requests_pending -= 1
            logger.info(f"Skipped page, requests_pending now: {self.requests_pending}")
            if self.requests_pending == 0:
                self.scraped_data['data_quality_score'] = self._calculate_data_quality()
                self.scraped_data['scraped_urls'] = sorted(list(self.visited_urls))
                logger.info("All pages processed, yielding final scraped data")
                self.results_yielded = True
                yield self.scraped_data
            return

        self.scraped_data['pages_scraped'] += 1
        self.visited_urls.add(response.url)

        soup = BeautifulSoup(response.text, 'lxml')

        # Extract based on page type
        if page_type == 'mission':
            mission = self._extract_mission_statement(soup, response.url)
            if mission and not self.scraped_data['mission_statement']:
                self.scraped_data['mission_statement'] = mission

        elif page_type == 'programs':
            programs = self._extract_programs(soup, response.url)
            if programs:
                self.scraped_data['programs'].extend(programs)

        elif page_type == 'leadership':
            leadership = self._extract_leadership(soup, response.url)
            if leadership:
                self.scraped_data['leadership'].extend(leadership)

        elif page_type == 'contact':
            contact = self._extract_contact_info(soup, response.url)
            if contact:
                self.scraped_data['contact_info'].update(contact)

        elif page_type == 'financial':
            financial = self._extract_financial_info(soup, response.url)
            if financial:
                self.scraped_data['financial_info'].update(financial)

        # RECURSIVE LINK DISCOVERY: Only enabled for deeper searches (depth > 3)
        # For shallow searches (depth ≤ 3), we only crawl links from homepage
        # This prevents queuing too many requests that hit page limits
        depth_limit = self.settings.getint('DEPTH_LIMIT', 3)

        if depth_limit > 3:
            # Deeper search - discover and follow links recursively
            target_links = self._discover_target_pages(response)
            logger.info(f"Recursive discovery enabled (depth={depth_limit}): Found {len(target_links)} potential links from {page_type} page")

            new_links_queued = 0
            for link, discovered_page_type in target_links:
                if link not in self.visited_urls:
                    # Mark as visited BEFORE yielding to avoid duplicate filtering issues
                    self.visited_urls.add(link)
                    self.requests_pending += 1  # Track pending request
                    new_links_queued += 1
                    logger.debug(f"Queued {discovered_page_type} page from {page_type}, requests_pending now: {self.requests_pending}")
                    yield scrapy.Request(
                        url=link,
                        callback=self.parse_target_page,
                        errback=self.handle_error,
                        meta={'page_type': discovered_page_type},
                        dont_filter=True  # We're already tracking visited URLs manually
                    )

            logger.info(f"Queued {new_links_queued} new links from {page_type} page (out of {len(target_links)} discovered)")
        else:
            logger.debug(f"Recursive discovery disabled for shallow search (depth={depth_limit} ≤ 3)")

        # Decrement pending requests counter
        self.requests_pending -= 1
        logger.info(f"{page_type} page complete, requests_pending now: {self.requests_pending}")
        if self.requests_pending == 0:
            # All pages processed - calculate quality and yield final data
            self.scraped_data['data_quality_score'] = self._calculate_data_quality()
            # Convert visited_urls set to sorted list for frontend display
            self.scraped_data['scraped_urls'] = sorted(list(self.visited_urls))
            logger.info("All pages processed, yielding final scraped data")
            self.results_yielded = True
            yield self.scraped_data

    def _discover_target_pages(self, response: Response) -> List[tuple]:
        """
        Discover links to target pages.

        Returns:
            List of (url, page_type) tuples
        """
        discovered_pages = []
        soup = BeautifulSoup(response.text, 'lxml')

        # Find all links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            link_text = link.get_text(strip=True).lower()

            # Resolve relative URLs
            absolute_url = urljoin(response.url, link.get('href'))

            # Check if link matches target page keywords
            for page_type, keywords in self.TARGET_PAGES.items():
                for keyword in keywords:
                    if keyword in href or keyword in link_text:
                        if absolute_url not in self.visited_urls:
                            discovered_pages.append((absolute_url, page_type))
                            logger.debug(f"Discovered {page_type} page: {absolute_url}")
                            break

        return discovered_pages[:20]  # Limit to avoid too many requests

    def _extract_mission_statement(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract mission statement from page content."""
        try:
            # Common patterns for mission statements
            mission_patterns = [
                ('id', re.compile(r'mission|our-mission|about', re.I)),
                ('class', re.compile(r'mission|about|overview', re.I)),
            ]

            for attr, pattern in mission_patterns:
                element = soup.find(attrs={attr: pattern})
                if element:
                    # Get text from element
                    mission_text = element.get_text(separator=' ', strip=True)
                    if len(mission_text) > 50:  # Reasonable mission length
                        logger.debug(f"Extracted mission statement from {url}")
                        return mission_text[:1000]  # Limit length

            # Fallback: Look for paragraphs with "mission" nearby
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if 'mission' in text.lower() and len(text) > 50:
                    return text[:1000]

        except Exception as e:
            logger.error(f"Error extracting mission from {url}: {e}")
            self.scraped_data['extraction_errors'].append(f"Mission extraction error: {str(e)}")

        return None

    def _extract_programs(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract program/service information."""
        programs = []

        try:
            # Look for program listings
            program_sections = soup.find_all(['div', 'section'], class_=re.compile(r'program|service', re.I))

            for section in program_sections[:10]:  # Limit to 10 programs
                # Try to extract program name and description
                name_elem = section.find(['h2', 'h3', 'h4'])
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    description = section.get_text(separator=' ', strip=True)

                    programs.append({
                        'name': name,
                        'description': description[:500]  # Limit description length
                    })

                    logger.debug(f"Extracted program: {name}")

        except Exception as e:
            logger.error(f"Error extracting programs from {url}: {e}")
            self.scraped_data['extraction_errors'].append(f"Programs extraction error: {str(e)}")

        return programs

    def _is_valid_leader_name(self, name: str, title: str) -> bool:
        """Validate that a name looks like a real person, not junk data."""
        # Skip if name contains organizational keywords or looks invalid
        junk_keywords = ['foundation', 'board member', 'opera', 'arts society', 'was also', 'the chair', 'omaha', 'member\n',
                         'vice chair', 'also the', 'treasurer', 'secretary']
        name_lower = name.lower()

        for keyword in junk_keywords:
            if keyword in name_lower:
                logger.debug(f"Rejected (junk keyword '{keyword}'): {name}")
                return False

        # Skip if name starts with title/role prefixes (indicates bad extraction)
        bad_prefixes = ['member ', 'board ', 'director ', 'officer ', 'trustee ', 'chair ', 'president ',
                        'ceo ', 'cfo ', 'executive ', 'the ']
        for prefix in bad_prefixes:
            if name_lower.startswith(prefix):
                logger.debug(f"Rejected (starts with '{prefix}'): {name}")
                return False

        # Skip if name is too short or too long (should be 2-5 words for a person's name)
        word_count = len(name.split())
        if word_count < 2 or word_count > 5:
            logger.debug(f"Rejected (word count {word_count}): {name}")
            return False

        # Skip if has camelCase concatenation in middle of word (like "HobermanBoard")
        # Look for pattern: lowercase followed by uppercase in middle of a word
        import re
        if re.search(r'[a-z][A-Z]', name):
            # Check if this is NOT just standard name capitalization (like "McDonald")
            # by seeing if the uppercase letter is at the start of a word
            words = name.split()
            for word in words:
                if re.search(r'[a-z][A-Z]', word) and not re.match(r'^Mc[A-Z]|^O\'[A-Z]', word):
                    logger.debug(f"Rejected (camelCase concatenation): {name}")
                    return False

        # Skip if title contains the name (usually means bad extraction)
        if name.lower() in title.lower() and len(name) > 5:
            logger.debug(f"Rejected (name in title): {name} - {title}")
            return False

        # Skip if name contains line breaks (bad extraction)
        if '\n' in name or '\r' in name:
            logger.debug(f"Rejected (contains linebreaks): {name}")
            return False

        return True

    def _extract_leadership(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract leadership/staff information with improved pattern matching."""
        leadership = []

        try:
            # Strategy 1: Look for H3/H4/H5 tags followed by titles (common pattern)
            # This handles structures like: <h4>Name</h4><p>Title</p> or <h4>Name</h4><h4><span>Title</span></h4>
            title_keywords = re.compile(r'president|chair|director|officer|member|ceo|cfo|coo|executive|treasurer|secretary|board|trustee', re.I)

            for heading in soup.find_all(['h3', 'h4', 'h5']):
                name_text = heading.get_text(strip=True)

                # Skip if looks like a section heading
                if len(name_text) < 3 or name_text.lower() in ['board', 'staff', 'team', 'leadership', 'board members', 'directors']:
                    continue

                # Look for title in next sibling elements
                title = None
                current = heading.find_next_sibling()

                # Check next few siblings for title
                for _ in range(3):
                    if current is None:
                        break

                    sibling_text = current.get_text(strip=True)

                    # Check if this sibling contains a title keyword
                    if title_keywords.search(sibling_text) and len(sibling_text) < 100:
                        title = sibling_text
                        break

                    current = current.find_next_sibling()

                # If we found a valid name and title
                if title and len(name_text) > 2:
                    # Clean zero-width spaces and other invisible characters
                    clean_name = name_text.replace('\u200b', '').replace('\ufeff', '').strip()
                    clean_title = title.replace('\u200b', '').replace('\ufeff', '').strip()

                    # Validate the extracted data
                    if self._is_valid_leader_name(clean_name, clean_title):
                        # Check if not already added
                        if not any(l['name'] == clean_name for l in leadership):
                            leadership.append({
                                'name': clean_name,
                                'title': clean_title,
                                'bio': ''
                            })
                            logger.debug(f"Extracted leader (Strategy 1 - Heading+Title): {clean_name} - {clean_title}")

            # Strategy 2: Look for staff/board listings with class names
            people_sections = soup.find_all(['div', 'li', 'tr'], class_=re.compile(r'staff|board|team|member|person|director|trustee', re.I))

            for section in people_sections[:20]:  # Limit to 20 people
                # Try to extract name and title
                name_elem = section.find(['h3', 'h4', 'h5', 'strong', 'b'])
                if name_elem:
                    name = name_elem.get_text(strip=True)

                    # Skip if name is too short or looks like a heading
                    if len(name) < 3 or name.lower() in ['board', 'staff', 'team', 'leadership']:
                        continue

                    # Try to find title
                    title_patterns = [
                        section.find(class_=re.compile(r'title|position|role', re.I)),
                        section.find('p'),
                        section.find('em'),
                        section.find('i'),
                    ]

                    title = ''
                    for pattern in title_patterns:
                        if pattern and pattern != name_elem:
                            title = pattern.get_text(strip=True)
                            if title and title != name:
                                break

                    if name and title:
                        # Validate the extracted data
                        if self._is_valid_leader_name(name, title):
                            # Check if not already added
                            if not any(l['name'] == name for l in leadership):
                                leadership.append({
                                    'name': name,
                                    'title': title,
                                    'bio': section.get_text(strip=True)[:300]
                                })
                                logger.debug(f"Extracted leader (Strategy 2 - Class): {name} - {title}")

            # Strategy 3: Look for table rows (common for board listings)
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:21]:  # Skip header, limit to 20
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        # Assume first cell is name, second is title
                        name = cells[0].get_text(strip=True)
                        title = cells[1].get_text(strip=True)

                        if len(name) > 3 and len(title) > 2:
                            # Validate the extracted data
                            if self._is_valid_leader_name(name, title):
                                # Check if not already added
                                if not any(l['name'] == name for l in leadership):
                                    leadership.append({
                                        'name': name,
                                        'title': title,
                                        'bio': row.get_text(strip=True)[:300]
                                    })
                                    logger.debug(f"Extracted leader (Strategy 3 - Table): {name} - {title}")

            # Strategy 4: Look for text patterns like "Name, Title" or "Name - Title"
            text_content = soup.get_text()
            name_title_pattern = re.compile(r'([A-Z][a-z]+(?:\s+\([A-Z][a-z]+\))?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,\-–—]?\s*((?:Vice\s+)?(?:President|Chair|Chairman|Director|Officer|Member|CEO|CFO|COO|Executive|Treasurer|Secretary|Board\s+Member))', re.MULTILINE | re.IGNORECASE)

            matches = name_title_pattern.findall(text_content)
            for name, title in matches[:15]:  # Limit to 15 matches
                name = name.strip()
                title = title.strip()
                # Validate and check if not already added
                if len(name) > 3 and len(title) > 2:
                    if self._is_valid_leader_name(name, title):
                        if not any(l['name'] == name for l in leadership):
                            leadership.append({
                                'name': name,
                                'title': title,
                                'bio': ''
                            })
                            logger.debug(f"Extracted leader (Strategy 4 - Pattern): {name} - {title}")

        except Exception as e:
            logger.error(f"Error extracting leadership from {url}: {e}")
            self.scraped_data['extraction_errors'].append(f"Leadership extraction error: {str(e)}")

        return leadership

    def _extract_contact_info(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract contact information."""
        contact = {}

        try:
            # Extract email
            email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
            emails = email_pattern.findall(soup.get_text())
            if emails:
                contact['email'] = emails[0]

            # Extract phone
            phone_pattern = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
            phones = phone_pattern.findall(soup.get_text())
            if phones:
                contact['phone'] = phones[0]

            # Extract address elements
            address_keywords = ['address', 'location', 'office']
            for keyword in address_keywords:
                address_elem = soup.find(class_=re.compile(keyword, re.I))
                if address_elem:
                    contact['mailing_address'] = address_elem.get_text(strip=True)
                    break

        except Exception as e:
            logger.error(f"Error extracting contact info from {url}: {e}")

        return contact

    def _extract_financial_info(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract financial information if available."""
        financial = {}

        try:
            # Look for budget/revenue mentions
            text = soup.get_text()

            # Try to find budget mentions
            budget_pattern = re.compile(r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?(?:\s*(?:million|M|billion|B))?', re.I)
            budgets = budget_pattern.findall(text)

            if budgets:
                # Try to parse first budget mention
                budget_str = budgets[0]
                financial['annual_budget_text'] = budget_str

        except Exception as e:
            logger.error(f"Error extracting financial info from {url}: {e}")

        return financial

    def closed(self, reason):
        """
        Called when spider closes.

        Final cleanup and logging (data already yielded from parse methods).
        """
        logger.info(
            f"Spider closed for {self.organization_name}:\n"
            f"  Reason: {reason}\n"
            f"  Pages scraped: {self.scraped_data['pages_scraped']}\n"
            f"  Mission: {'Yes' if self.scraped_data['mission_statement'] else 'No'}\n"
            f"  Programs: {len(self.scraped_data['programs'])}\n"
            f"  Leadership: {len(self.scraped_data['leadership'])}\n"
            f"  Contact: {'Yes' if self.scraped_data['contact_info'] else 'No'}"
        )

    def _calculate_data_quality(self) -> float:
        """Calculate overall data quality score (0.0-1.0)."""
        quality_score = 0.0

        # Mission statement (25%)
        if self.scraped_data['mission_statement']:
            quality_score += 0.25

        # Programs (25%)
        if len(self.scraped_data['programs']) >= 3:
            quality_score += 0.25
        elif len(self.scraped_data['programs']) >= 1:
            quality_score += 0.15

        # Leadership (30%)
        if len(self.scraped_data['leadership']) >= 5:
            quality_score += 0.30
        elif len(self.scraped_data['leadership']) >= 2:
            quality_score += 0.20
        elif len(self.scraped_data['leadership']) >= 1:
            quality_score += 0.10

        # Contact info (20%)
        contact_fields = sum([
            bool(self.scraped_data['contact_info'].get('email')),
            bool(self.scraped_data['contact_info'].get('phone')),
            bool(self.scraped_data['contact_info'].get('mailing_address'))
        ])
        quality_score += (contact_fields / 3) * 0.20

        return min(quality_score, 1.0)

    def handle_error(self, failure):
        """Handle request errors."""
        logger.error(f"Request failed: {failure.request.url} - {failure.value}")
        self.scraped_data['extraction_errors'].append(f"Request error: {str(failure.value)}")

        # Decrement pending requests counter (failed requests count too!)
        self.requests_pending -= 1
        logger.info(f"Error handler: requests_pending now: {self.requests_pending}")
        if self.requests_pending == 0:
            # All pages processed (including failures) - calculate quality and yield final data
            self.scraped_data['data_quality_score'] = self._calculate_data_quality()
            logger.info("All pages processed (with errors), yielding final scraped data")
            self.results_yielded = True
            return self.scraped_data

    def closed(self, reason):
        """
        Called when spider closes.

        Logs final statistics for debugging.
        """
        logger.info(f"Spider closing - reason: {reason}")
        logger.info(f"Final stats - Pages scraped: {self.scraped_data['pages_scraped']}, Requests pending: {self.requests_pending}, Results yielded: {self.results_yielded}")

        if not self.results_yielded:
            logger.error(f"BUG: Spider closed without yielding results! This indicates a counter logic error.")
            logger.error(f"Visited URLs: {len(self.visited_urls)}, URLs: {list(self.visited_urls)[:10]}")
