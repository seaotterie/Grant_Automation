#!/usr/bin/env python3
"""
GPT URL Discovery Service
Uses GPT-5 to intelligently predict and discover URLs for government opportunities and organizations.

This service:
1. Predicts agency/program URLs based on opportunity descriptions
2. Discovers sub-pages and related documentation
3. Validates predicted URLs and provides confidence scores
4. Caches successful discoveries for performance
5. Integrates with MCP client for web content fetching
"""

import asyncio
import time
import sqlite3
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

try:
    from src.core.openai_service import OpenAIService
except ImportError:
    OpenAIService = None

try:
    from src.core.simple_mcp_client import SimpleMCPClient
except ImportError:
    SimpleMCPClient = None


@dataclass
class URLDiscoveryResult:
    """Result of URL discovery process."""
    predicted_url: str
    confidence: float  # 0.0 to 1.0
    prediction_method: str  # gpt_prediction, heuristic, cached
    is_valid: Optional[bool] = None
    sub_pages: List[str] = None
    related_urls: List[str] = None
    error_message: str = None
    
    def __post_init__(self):
        if self.sub_pages is None:
            self.sub_pages = []
        if self.related_urls is None:
            self.related_urls = []


class GPTURLDiscoveryService:
    """Service for intelligent URL discovery using GPT and web validation."""
    
    def __init__(self):
        self.openai_service = OpenAIService() if OpenAIService else None
        self.mcp_client = SimpleMCPClient(timeout=15) if SimpleMCPClient else None
        self.database_path = "data/catalynx.db"
        
        # URL discovery cache
        self._url_cache = {}
        self._cache_expiry = timedelta(hours=24)
        
        # Initialize database
        self._init_url_discovery_database()
        
    def _init_url_discovery_database(self):
        """Initialize URL discovery database tables."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS url_discovery_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        search_key TEXT UNIQUE NOT NULL,
                        predicted_url TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        prediction_method TEXT NOT NULL,
                        is_valid INTEGER,
                        sub_pages TEXT,
                        related_urls TEXT,
                        created_timestamp TEXT NOT NULL,
                        last_validated TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_url_discovery_search_key 
                    ON url_discovery_cache(search_key)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_url_discovery_created 
                    ON url_discovery_cache(created_timestamp)
                """)
                
        except Exception as e:
            print(f"Failed to initialize URL discovery database: {e}")
    
    async def discover_opportunity_url(self, opportunity_title: str, 
                                     agency_name: str, 
                                     opportunity_description: str = "") -> URLDiscoveryResult:
        """Discover URL for a government opportunity."""
        search_key = self._create_search_key(opportunity_title, agency_name)
        
        # Check cache first
        cached_result = await self._get_cached_discovery(search_key)
        if cached_result:
            return cached_result
        
        # Use GPT for intelligent URL prediction
        if self.openai_service:
            gpt_result = await self._gpt_url_prediction(opportunity_title, agency_name, opportunity_description)
            if gpt_result.confidence >= 0.7:
                # Validate the predicted URL
                await self._validate_predicted_url(gpt_result)
                await self._cache_discovery_result(search_key, gpt_result)
                return gpt_result
        
        # Fallback to heuristic-based prediction
        heuristic_result = self._heuristic_url_prediction(opportunity_title, agency_name)
        if heuristic_result:
            await self._validate_predicted_url(heuristic_result)
            await self._cache_discovery_result(search_key, heuristic_result)
            return heuristic_result
        
        # Return failure result
        return URLDiscoveryResult(
            predicted_url="",
            confidence=0.0,
            prediction_method="failed",
            error_message="Unable to predict URL using available methods"
        )
    
    async def discover_organization_url(self, organization_name: str, 
                                      state: str = "", 
                                      ntee_code: str = "") -> URLDiscoveryResult:
        """Discover URL for an organization."""
        search_key = self._create_search_key(organization_name, f"{state}_{ntee_code}")
        
        # Check cache first
        cached_result = await self._get_cached_discovery(search_key)
        if cached_result:
            return cached_result
        
        # Use GPT for intelligent URL prediction
        if self.openai_service:
            gpt_result = await self._gpt_organization_url_prediction(organization_name, state, ntee_code)
            if gpt_result.confidence >= 0.6:  # Lower threshold for organizations
                await self._validate_predicted_url(gpt_result)
                await self._cache_discovery_result(search_key, gpt_result)
                return gpt_result
        
        # Fallback to heuristic prediction
        heuristic_result = self._heuristic_organization_url_prediction(organization_name)
        if heuristic_result:
            await self._validate_predicted_url(heuristic_result)
            await self._cache_discovery_result(search_key, heuristic_result)
            return heuristic_result
        
        return URLDiscoveryResult(
            predicted_url="",
            confidence=0.0,
            prediction_method="failed",
            error_message="Unable to predict organization URL"
        )
    
    async def _gpt_url_prediction(self, opportunity_title: str, 
                                agency_name: str, 
                                opportunity_description: str) -> URLDiscoveryResult:
        """Use GPT-5 for intelligent URL prediction."""
        try:
            prompt = f"""
Predict the most likely website URL for this government funding opportunity:

**Opportunity Title:** {opportunity_title}
**Agency:** {agency_name}
**Description:** {opportunity_description[:500]}

Based on common government agency URL patterns and the specific opportunity details, predict the most likely URL where this opportunity would be posted or where more information can be found.

Consider:
- Government agency website structures
- Program-specific pages
- Grant/funding opportunity pages
- Agency acronyms and common URL patterns

Respond with ONLY the predicted URL (no explanation or additional text).
Examples of good predictions:
- https://www.grants.gov/web/grants/search-grants.html
- https://www.nih.gov/grants-funding
- https://www.nsf.gov/funding/pgm_summ.jsp?pims_id=5761
"""

            response = await self.openai_service.acomplete_chat(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-5-nano",
                max_tokens=100,
                temperature=0.3
            )
            
            predicted_url = response.strip()
            
            # Validate URL format
            if self._is_valid_url_format(predicted_url):
                confidence = self._calculate_gpt_confidence(predicted_url, agency_name)
                return URLDiscoveryResult(
                    predicted_url=predicted_url,
                    confidence=confidence,
                    prediction_method="gpt_prediction"
                )
            else:
                return URLDiscoveryResult(
                    predicted_url="",
                    confidence=0.0,
                    prediction_method="gpt_prediction",
                    error_message="GPT returned invalid URL format"
                )
                
        except Exception as e:
            return URLDiscoveryResult(
                predicted_url="",
                confidence=0.0,
                prediction_method="gpt_prediction",
                error_message=f"GPT prediction failed: {str(e)}"
            )
    
    async def _gpt_organization_url_prediction(self, organization_name: str, 
                                             state: str, 
                                             ntee_code: str) -> URLDiscoveryResult:
        """Use GPT-5 for organization URL prediction."""
        try:
            ntee_context = self._get_ntee_context(ntee_code) if ntee_code else ""
            
            prompt = f"""
Predict the most likely website URL for this nonprofit organization:

**Organization:** {organization_name}
**State:** {state}
**Sector:** {ntee_context}

Based on common nonprofit website patterns and the organization details, predict the most likely website URL.

Consider:
- Organization name conversion to domain format
- Common nonprofit URL patterns (.org, .com, .net)
- Geographic and sector-specific patterns
- Acronyms and abbreviations

Respond with ONLY the predicted URL (no explanation or additional text).
Examples of good predictions:
- https://www.americanredcross.org
- https://www.unitedway.org
- https://www.herosbridge.org
"""

            response = await self.openai_service.acomplete_chat(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-5-nano",
                max_tokens=100,
                temperature=0.3
            )
            
            predicted_url = response.strip()
            
            if self._is_valid_url_format(predicted_url):
                confidence = self._calculate_organization_confidence(predicted_url, organization_name)
                return URLDiscoveryResult(
                    predicted_url=predicted_url,
                    confidence=confidence,
                    prediction_method="gpt_prediction"
                )
            else:
                return URLDiscoveryResult(
                    predicted_url="",
                    confidence=0.0,
                    prediction_method="gpt_prediction",
                    error_message="GPT returned invalid URL format"
                )
                
        except Exception as e:
            return URLDiscoveryResult(
                predicted_url="",
                confidence=0.0,
                prediction_method="gpt_prediction",
                error_message=f"GPT prediction failed: {str(e)}"
            )
    
    def _heuristic_url_prediction(self, opportunity_title: str, agency_name: str) -> URLDiscoveryResult:
        """Heuristic-based URL prediction for government opportunities."""
        agency_lower = agency_name.lower()
        
        # Agency URL mappings
        agency_mappings = {
            'national science foundation': 'https://www.nsf.gov/funding/',
            'nsf': 'https://www.nsf.gov/funding/',
            'national institutes of health': 'https://www.nih.gov/grants-funding',
            'nih': 'https://www.nih.gov/grants-funding',
            'department of education': 'https://www.ed.gov/fund/grants-overview',
            'department of veterans affairs': 'https://www.va.gov/grants/',
            'department of defense': 'https://www.defense.gov/Resources/Grants/',
            'department of health and human services': 'https://www.hhs.gov/grants/index.html',
            'hhs': 'https://www.hhs.gov/grants/index.html'
        }
        
        # Check direct agency mappings
        for agency_key, url in agency_mappings.items():
            if agency_key in agency_lower:
                return URLDiscoveryResult(
                    predicted_url=url,
                    confidence=0.8,
                    prediction_method="heuristic_direct"
                )
        
        # Extract agency acronym and create URL
        agency_acronym = self._extract_agency_acronym(agency_name)
        if agency_acronym:
            predicted_url = f"https://www.{agency_acronym.lower()}.gov"
            return URLDiscoveryResult(
                predicted_url=predicted_url,
                confidence=0.6,
                prediction_method="heuristic_acronym"
            )
        
        # Fallback to grants.gov
        return URLDiscoveryResult(
            predicted_url="https://www.grants.gov/web/grants/search-grants.html",
            confidence=0.4,
            prediction_method="heuristic_fallback"
        )
    
    def _heuristic_organization_url_prediction(self, organization_name: str) -> URLDiscoveryResult:
        """Heuristic-based URL prediction for organizations."""
        # Clean organization name for URL conversion
        clean_name = re.sub(r'[^\w\s]', '', organization_name.lower())
        clean_name = re.sub(r'\s+', '', clean_name)
        
        # Remove common words
        remove_words = ['inc', 'foundation', 'organization', 'corp', 'company', 'the', 'of', 'for']
        for word in remove_words:
            clean_name = clean_name.replace(word, '')
        
        if len(clean_name) >= 4:  # Minimum length for meaningful URL
            predicted_url = f"https://www.{clean_name}.org"
            confidence = 0.6 if len(clean_name) <= 15 else 0.4  # Shorter names more likely
            
            return URLDiscoveryResult(
                predicted_url=predicted_url,
                confidence=confidence,
                prediction_method="heuristic_name_conversion"
            )
        
        return None
    
    async def _validate_predicted_url(self, result: URLDiscoveryResult):
        """Validate predicted URL by attempting to fetch it."""
        if not self.mcp_client or not result.predicted_url:
            return
        
        try:
            # Attempt to fetch the URL
            intelligence_result = await self.mcp_client.fetch_deep_intelligence(result.predicted_url)
            
            if intelligence_result and intelligence_result.success:
                result.is_valid = True
                result.confidence = min(result.confidence + 0.1, 1.0)  # Boost confidence
                
                # Extract sub-pages if available
                if hasattr(intelligence_result, 'pages_scraped'):
                    result.sub_pages = intelligence_result.pages_scraped[:5]  # Limit to 5
                    
            else:
                result.is_valid = False
                result.confidence = max(result.confidence - 0.2, 0.0)  # Reduce confidence
                
        except Exception as e:
            result.is_valid = False
            result.error_message = f"Validation failed: {str(e)}"
    
    async def _get_cached_discovery(self, search_key: str) -> Optional[URLDiscoveryResult]:
        """Get cached URL discovery result."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT predicted_url, confidence, prediction_method, is_valid, 
                           sub_pages, related_urls, created_timestamp
                    FROM url_discovery_cache 
                    WHERE search_key = ?
                """, (search_key,))
                
                result = cursor.fetchone()
                if result:
                    predicted_url, confidence, prediction_method, is_valid, sub_pages, related_urls, created_timestamp = result
                    
                    # Check if cache is still valid
                    created_time = datetime.fromisoformat(created_timestamp)
                    if datetime.now() - created_time < self._cache_expiry:
                        return URLDiscoveryResult(
                            predicted_url=predicted_url,
                            confidence=confidence,
                            prediction_method=f"cached_{prediction_method}",
                            is_valid=bool(is_valid) if is_valid is not None else None,
                            sub_pages=json.loads(sub_pages) if sub_pages else [],
                            related_urls=json.loads(related_urls) if related_urls else []
                        )
        except Exception as e:
            # Cache read failed, continue without cached result
            pass
        
        return None
    
    async def _cache_discovery_result(self, search_key: str, result: URLDiscoveryResult):
        """Cache URL discovery result."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO url_discovery_cache 
                    (search_key, predicted_url, confidence, prediction_method, is_valid,
                     sub_pages, related_urls, created_timestamp, last_validated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    search_key,
                    result.predicted_url,
                    result.confidence,
                    result.prediction_method,
                    int(result.is_valid) if result.is_valid is not None else None,
                    json.dumps(result.sub_pages),
                    json.dumps(result.related_urls),
                    datetime.now().isoformat(),
                    datetime.now().isoformat() if result.is_valid is not None else None
                ))
                
        except Exception as e:
            # Cache write failed, continue without caching
            pass
    
    def _create_search_key(self, primary_term: str, secondary_term: str) -> str:
        """Create a normalized search key for caching."""
        combined = f"{primary_term}|{secondary_term}".lower()
        # Remove special characters and normalize whitespace
        normalized = re.sub(r'[^\w\s|]', '', combined)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()
    
    def _is_valid_url_format(self, url: str) -> bool:
        """Check if string has valid URL format."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(url))
    
    def _calculate_gpt_confidence(self, predicted_url: str, agency_name: str) -> float:
        """Calculate confidence score for GPT-predicted URL."""
        base_confidence = 0.8  # Base confidence for GPT predictions
        
        # Boost confidence for known government domains
        gov_domains = ['.gov', '.mil']
        if any(domain in predicted_url for domain in gov_domains):
            base_confidence += 0.1
        
        # Check if agency name appears in URL
        agency_words = agency_name.lower().split()
        url_lower = predicted_url.lower()
        matching_words = sum(1 for word in agency_words if len(word) > 3 and word in url_lower)
        if matching_words > 0:
            base_confidence += 0.05 * matching_words
        
        return min(base_confidence, 1.0)
    
    def _calculate_organization_confidence(self, predicted_url: str, organization_name: str) -> float:
        """Calculate confidence score for organization URL prediction."""
        base_confidence = 0.7  # Base confidence for organization predictions
        
        # Boost confidence for .org domains
        if '.org' in predicted_url:
            base_confidence += 0.1
        
        # Check name similarity
        org_words = organization_name.lower().split()
        url_lower = predicted_url.lower()
        matching_words = sum(1 for word in org_words if len(word) > 3 and word in url_lower)
        if matching_words > 0:
            base_confidence += 0.05 * matching_words
        
        return min(base_confidence, 1.0)
    
    def _extract_agency_acronym(self, agency_name: str) -> Optional[str]:
        """Extract likely acronym from agency name."""
        words = agency_name.upper().split()
        if len(words) >= 2:
            # Take first letter of each significant word
            acronym = ''.join(word[0] for word in words if len(word) > 2)
            if 2 <= len(acronym) <= 5:  # Reasonable acronym length
                return acronym
        return None
    
    def _get_ntee_context(self, ntee_code: str) -> str:
        """Get context description for NTEE code."""
        ntee_mappings = {
            'P20': 'Veterans services and support',
            'P23': 'Military families support',
            'E32': 'Community health and healthcare',
            'T31': 'Foundation and grantmaking',
            'B25': 'Educational programs',
            'F30': 'Food and nutrition services'
        }
        return ntee_mappings.get(ntee_code, f'NTEE code {ntee_code}')


# Global service instance
_gpt_url_discovery_service = None

def get_gpt_url_discovery_service() -> GPTURLDiscoveryService:
    """Get global GPT URL discovery service instance."""
    global _gpt_url_discovery_service
    if _gpt_url_discovery_service is None:
        _gpt_url_discovery_service = GPTURLDiscoveryService()
    return _gpt_url_discovery_service