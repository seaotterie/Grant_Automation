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
        'mission': ['about', 'mission', 'who-we-are', 'our-story', 'vision', 'values'],
        'programs': ['programs', 'services', 'what-we-do', 'our-work', 'initiatives'],
        'leadership': ['board', 'staff', 'team', 'leadership', 'directors', 'people', 'governance'],
        'contact': ['contact', 'connect', 'reach-us', 'get-in-touch'],
        'financial': ['financials', 'annual-report', 'transparency', '990', 'financial-info']
    }

    def __init__(self, ein: str, organization_name: str, user_provided_url: Optional[str] = None, *args, **kwargs):
        """
        Initialize spider.

        Args:
            ein: Organization EIN
            organization_name: Organization name
            user_provided_url: Optional user-provided URL (SmartURLMiddleware will resolve)
        """
        super().__init__(*args, **kwargs)

        self.ein = ein
        self.organization_name = organization_name
        self.user_provided_url = user_provided_url
        self.use_case = 'profile_builder'

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
            'extraction_errors': [],
        }

        # Track pages we've visited
        self.visited_urls = set()

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
                yield scrapy.Request(
                    url=link,
                    callback=self.parse_target_page,
                    errback=self.handle_error,
                    meta={'page_type': page_type}
                )

    def parse_target_page(self, response: Response):
        """
        Parse a target page (mission, programs, leadership, etc.).

        Extracts content based on page type.
        """
        self.scraped_data['pages_attempted'] += 1
        self.scraped_data['pages_scraped'] += 1
        self.visited_urls.add(response.url)

        page_type = response.meta.get('page_type', 'unknown')
        logger.info(f"Parsing {page_type} page: {response.url}")

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

    def _extract_leadership(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract leadership/staff information."""
        leadership = []

        try:
            # Look for staff/board listings
            people_sections = soup.find_all(['div', 'li'], class_=re.compile(r'staff|board|team|member|person', re.I))

            for section in people_sections[:20]:  # Limit to 20 people
                # Try to extract name and title
                name_elem = section.find(['h3', 'h4', 'strong', 'b'])
                if name_elem:
                    name = name_elem.get_text(strip=True)

                    # Try to find title
                    title_patterns = [
                        section.find(class_=re.compile(r'title|position|role', re.I)),
                        section.find('p'),
                    ]

                    title = ''
                    for pattern in title_patterns:
                        if pattern:
                            title = pattern.get_text(strip=True)
                            break

                    if name and title:
                        leadership.append({
                            'name': name,
                            'title': title,
                            'bio': section.get_text(strip=True)[:300]  # Short bio
                        })

                        logger.debug(f"Extracted leader: {name} - {title}")

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

        Yields final scraped data item to pipeline.
        """
        logger.info(
            f"Spider closed for {self.organization_name}:\n"
            f"  Reason: {reason}\n"
            f"  Pages scraped: {self.scraped_data['pages_scraped']}\n"
            f"  Mission: {'✓' if self.scraped_data['mission_statement'] else '✗'}\n"
            f"  Programs: {len(self.scraped_data['programs'])}\n"
            f"  Leadership: {len(self.scraped_data['leadership'])}\n"
            f"  Contact: {'✓' if self.scraped_data['contact_info'] else '✗'}"
        )

        # Calculate data quality score
        self.scraped_data['data_quality_score'] = self._calculate_data_quality()

        # Yield final item to pipeline
        yield self.scraped_data

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
