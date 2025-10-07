#!/usr/bin/env python3
"""
GPT URL Discovery Processor
Intelligent organization website discovery using GPT API and BMF data with SQL caching.

This processor:
1. Takes organization data (BMF/990 information)
2. Uses GPT-5 to intelligently predict likely website URLs
3. Caches successful URLs in SQL database to avoid repeated API calls
4. Returns ranked list of URL candidates for web scraping

Single Purpose: Organization data → GPT reasoning → URL predictions
Does NOT handle web scraping (that's for MCP Fetch to handle)
"""

import asyncio
import logging
import sqlite3
import aiosqlite
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult
from src.core.openai_service import get_openai_service

logger = logging.getLogger(__name__)


@dataclass
class URLPrediction:
    """URL prediction with confidence score"""
    url: str
    confidence: float
    reasoning: Optional[str] = None


@dataclass 
class OrganizationURLCache:
    """Cached URL for an organization"""
    ein: str
    url: str
    verified_date: datetime
    success_score: float
    last_verified: datetime


class GPTURLDiscoveryProcessor(BaseProcessor):
    """
    Processor for intelligent URL discovery using GPT API.
    
    Features:
    - GPT-5 powered URL prediction based on organization patterns
    - SQL caching to avoid repeated API calls
    - Handles nonprofit naming conventions and abbreviations
    - Returns ranked URL candidates for verification
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="gpt_url_discovery",
            description="Intelligent organization URL discovery using GPT and BMF data",
            version="1.0.0",
            dependencies=[],  # No processor dependencies - uses BMF data directly
            estimated_duration=10,  # 10 seconds for GPT call
            requires_network=True,  # For GPT API
            requires_api_key=True,  # OpenAI API key
            can_run_parallel=True,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Database paths
        self.db_path = "data/catalynx.db"  # For URL caching
        self.bmf_db_path = Path("data/nonprofit_intelligence.db")  # BMF/SOI database
        
        # Initialize URL cache table
        asyncio.create_task(self._initialize_url_cache_table())
    
    async def _initialize_url_cache_table(self):
        """Create URL cache table if it doesn't exist"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS organization_urls (
                        ein TEXT PRIMARY KEY,
                        url TEXT NOT NULL,
                        verified_date DATETIME NOT NULL,
                        success_score REAL NOT NULL DEFAULT 1.0,
                        last_verified DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                await db.commit()
                logger.info("URL cache table initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing URL cache table: {e}")
    
    async def _query_bmf_organization(self, ein: str) -> Optional[Dict[str, Any]]:
        """Query BMF database for organization data by EIN"""
        try:
            if not self.bmf_db_path.exists():
                logger.warning(f"BMF database not found at {self.bmf_db_path}")
                return None
            
            # Query BMF database for organization details
            conn = sqlite3.connect(str(self.bmf_db_path))
            cursor = conn.cursor()
            
            query = """
                SELECT ein, name, city, state, street, zip, ntee_code, 
                       asset_amt, income_amt, revenue_amt, foundation_code
                FROM bmf_organizations 
                WHERE ein = ?
            """
            
            cursor.execute(query, (ein,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                ein, name, city, state, street, zip_code, ntee_code, asset_amt, income_amt, revenue_amt, foundation_code = result
                
                # Build full address
                address_parts = []
                if street:
                    address_parts.append(street)
                if city:
                    address_parts.append(city)
                if state:
                    address_parts.append(state)
                if zip_code:
                    address_parts.append(zip_code)
                
                full_address = ", ".join(address_parts)
                
                # Determine organization type from NTEE code or foundation code
                org_type = "nonprofit"
                if ntee_code:
                    if ntee_code.startswith(('A', 'B', 'C', 'D', 'E')):
                        org_type = "arts/education"
                    elif ntee_code.startswith(('F', 'G', 'H', 'I', 'J', 'K', 'L')):
                        org_type = "human services" 
                    elif ntee_code.startswith(('M', 'N', 'O', 'P')):
                        org_type = "health/public benefit"
                    elif ntee_code.startswith('T'):
                        org_type = "foundation"
                
                return {
                    'ein': ein,
                    'organization_name': name,  # This is the authoritative BMF name
                    'city': city or '',
                    'state': state or '',
                    'address': full_address,
                    'ntee_code': ntee_code or '',
                    'organization_type': org_type,
                    'asset_amount': asset_amt or 0,
                    'revenue_amount': revenue_amt or 0,
                    'data_source': 'bmf_database'
                }
            
            logger.info(f"No BMF data found for EIN {ein}")
            return None
            
        except Exception as e:
            logger.error(f"Error querying BMF database for EIN {ein}: {e}")
            return None
    
    async def execute(self, config: ProcessorConfig) -> ProcessorResult:
        """
        Execute URL discovery for organization.
        
        Expected config data:
        - organization_name: Official organization name from BMF
        - ein: Organization EIN
        - address: Full address (street, city, state, zip)
        - organization_type: NTEE description or type
        - force_refresh: Optional flag to bypass cache
        """
        start_time = datetime.now()
        
        try:
            # Extract organization data from config (with BMF database integration)
            org_data = await self._extract_organization_data(config)
            if not org_data:
                return ProcessorResult(
                    success=False,
                    processor_name="gpt_url_discovery",
                    data={},
                    errors=["Missing required organization data"],
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Check cache first (unless force refresh is requested)
            force_refresh = config.processor_specific_config.get('force_refresh', False)
            
            if not force_refresh:
                cached_url = await self._get_cached_url(org_data['ein'])
                if cached_url:
                    logger.info(f"Found cached URL for EIN {org_data['ein']}: {cached_url}")
                    return ProcessorResult(
                        success=True,
                        processor_name="gpt_url_discovery",
                        data={
                            'urls': [cached_url],
                            'source': 'cache',
                            'organization_data': org_data
                        },
                        execution_time=(datetime.now() - start_time).total_seconds()
                    )
            
            # No cache hit - use GPT to predict URLs
            org_name = org_data.get('organization_name') or org_data.get('name', 'Unknown Organization')
            logger.info(f"Discovering URLs for {org_name} (EIN: {org_data['ein']})")
            
            predicted_urls = await self._predict_urls_with_gpt(org_data)
            
            if not predicted_urls:
                return ProcessorResult(
                    success=False,
                    processor_name="gpt_url_discovery",
                    data={'organization_data': org_data},
                    errors=["GPT failed to predict any URLs"],
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Return predicted URLs (calling processor will handle verification)
            return ProcessorResult(
                success=True,
                processor_name="gpt_url_discovery",
                data={
                    'urls': [pred.url for pred in predicted_urls],
                    'predictions': [{'url': p.url, 'confidence': p.confidence, 'reasoning': p.reasoning} 
                                   for p in predicted_urls],
                    'source': 'gpt_prediction',
                    'organization_data': org_data
                },
                execution_time=(datetime.now() - start_time).total_seconds(),
                metadata={'cost_estimate': 0.002}  # Estimate for GPT call
            )
            
        except Exception as e:
            logger.error(f"Error in GPT URL discovery: {e}")
            return ProcessorResult(
                success=False,
                processor_name="gpt_url_discovery",
                data={},
                errors=[f"URL discovery failed: {str(e)}"],
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _extract_organization_data(self, config: ProcessorConfig) -> Optional[Dict[str, Any]]:
        """Extract organization data from processor config with BMF database integration"""
        try:
            # Try to get from processor specific config first
            org_data = config.processor_specific_config.get('organization_data')
            
            if org_data and org_data.get('data_source') == 'bmf_database':
                # Already have BMF data, use it directly
                return org_data
            
            # Extract EIN from various sources
            ein = None
            
            # 1. Try processor specific config
            if org_data and org_data.get('ein'):
                ein = org_data['ein']
            
            # 2. Try workflow config
            workflow_config = config.workflow_config
            if not ein and hasattr(workflow_config, 'target_ein') and workflow_config.target_ein:
                ein = workflow_config.target_ein
                
            # 3. Try processor specific config direct EIN
            if not ein:
                ein = config.processor_specific_config.get('ein')
            
            # If we have an EIN, query BMF database for authoritative data
            if ein:
                logger.info(f"Querying BMF database for EIN: {ein}")
                bmf_data = await self._query_bmf_organization(str(ein))
                
                if bmf_data:
                    logger.info(f"Found BMF data for {bmf_data['organization_name']} (EIN: {ein})")
                    return bmf_data
                else:
                    logger.warning(f"No BMF data found for EIN {ein}, falling back to config data")
            
            # Fallback: use provided org_data or create from config
            if org_data:
                return org_data
                
            # Last resort: extract from workflow config with warning
            if hasattr(workflow_config, 'target_ein') and workflow_config.target_ein:
                logger.warning("Using hardcoded config data instead of BMF database - this may cause URL prediction errors")
                target_org = {
                    'ein': workflow_config.target_ein,
                    'organization_name': config.processor_specific_config.get('name', ''),
                    'address': config.processor_specific_config.get('address', ''),
                    'city': config.processor_specific_config.get('city', ''),
                    'state': config.processor_specific_config.get('state', ''),
                    'organization_type': config.processor_specific_config.get('organization_type', 'nonprofit'),
                    'data_source': 'config_fallback'
                }
                return target_org
                
            logger.error("No organization data or EIN found in config")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting organization data: {e}")
            return None
    
    async def _get_cached_url(self, ein: str) -> Optional[str]:
        """Get cached URL for organization by EIN"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT url, verified_date FROM organization_urls WHERE ein = ?",
                    (ein,)
                ) as cursor:
                    row = await cursor.fetchone()
                    
                    if row:
                        url, verified_date_str = row
                        verified_date = datetime.fromisoformat(verified_date_str)
                        
                        # Check if cache is still fresh (within 30 days)
                        if datetime.now() - verified_date < timedelta(days=30):
                            return url
                        else:
                            logger.info(f"Cached URL for EIN {ein} is stale, will refresh")
                    
                    return None
                    
        except Exception as e:
            logger.error(f"Error checking URL cache: {e}")
            return None
    
    async def _predict_urls_with_gpt(self, org_data: Dict[str, Any]) -> List[URLPrediction]:
        """Use GPT to predict likely URLs for organization"""
        try:
            prompt = self._create_url_prediction_prompt(org_data)
            
            openai_service = get_openai_service()
            response = await openai_service.create_completion(
                model="gpt-5-nano",  # Use GPT-5-nano for cost-effective predictions
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000,  # Large budget: ~1500 for reasoning + 1500 for visible output
                temperature=0.3,  # Lower temperature for consistent results (will be ignored for GPT-5)
                # Explicitly disable tool calling to prevent interference
                tools=[],
                tool_choice="none"
            )
            
            # Parse GPT response into URL predictions
            predictions = self._parse_gpt_response(response.content)
            
            org_name = org_data.get('organization_name') or org_data.get('name', 'Unknown Organization')
            logger.info(f"GPT predicted {len(predictions)} URLs for {org_name}")
            return predictions
            
        except Exception as e:
            logger.error(f"Error calling GPT for URL prediction: {e}")
            return []
    
    def _create_url_prediction_prompt(self, org_data: Dict[str, Any]) -> str:
        """Create structured prompt for GPT URL prediction"""
        org_name = org_data.get('organization_name') or org_data.get('name', '')
        address = org_data.get('address', '')
        city = org_data.get('city', '')
        state = org_data.get('state', '')
        org_type = org_data.get('organization_type', 'nonprofit')
        
        prompt = f"""You are an expert at predicting nonprofit organization website URLs based on official IRS Business Master File data.

Organization Information (FROM OFFICIAL BMF RECORDS):
Name: {org_name}
Location: {city}, {state}
Type: {org_type}
Address: {address}

CRITICAL INSTRUCTIONS FOR ACCURATE URL PREDICTION:

1. SPELLING ACCURACY IS PARAMOUNT
   - Use the EXACT organization name spelling from BMF records
   - DO NOT "correct" unusual spellings (e.g., "Heros Bridge" should stay "Heros", not "Heroes")
   - Preserve all unique spellings and naming conventions from the official data
   
2. SUBDOMAIN PATTERNS TO TEST
   - Always consider BOTH www and non-www variations
   - Many organizations use www. subdomain (e.g., www.herosbridge.org vs herosbridge.org)
   - Include both variations in your predictions when confidence is similar

3. DOMAIN CONSTRUCTION RULES
   - Most nonprofits use .org domains
   - Remove spaces, convert to lowercase
   - Replace "&" with "and", remove punctuation except hyphens
   - Keep organization-specific terms intact (avoid generic abbreviations)

4. EXAMPLES OF PROPER SPELLING PRESERVATION
   - "Heros Bridge" → "herosbridge.org" (NOT "heroesbridge.org")
   - "St. Mary's Hospital" → "stmaryshospital.org" (remove apostrophes)
   - "YMCA of Greater Boston" → "ymcaofgreaterboston.org" (keep specific terms)

5. CONFIDENCE SCORING
   - High confidence (0.8-0.9): Direct name match with .org
   - Medium confidence (0.6-0.7): Common variations or geographic additions
   - Lower confidence (0.4-0.5): Abbreviated forms or alternative patterns

IMPORTANT: After your internal reasoning, provide your visible response in this exact format:

URL: [url]
Confidence: [0.1-1.0]
Reasoning: [brief explanation focusing on spelling accuracy and subdomain choice]

Example for "Heros Bridge":
URL: https://www.herosbridge.org
Confidence: 0.85
Reasoning: Preserves exact BMF spelling "Heros" with www subdomain, standard .org pattern

Only provide 3-5 predictions, ranked by confidence (highest first). Focus on spelling accuracy first, then subdomain variations."""

        return prompt
    
    def _parse_gpt_response(self, response_text: str) -> List[URLPrediction]:
        """Parse GPT response into URLPrediction objects"""
        predictions = []
        
        try:
            lines = response_text.strip().split('\n')
            current_url = None
            current_confidence = 0.5
            current_reasoning = None
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('URL:'):
                    current_url = line.replace('URL:', '').strip()
                    # Clean up URL format
                    if current_url and not current_url.startswith('http'):
                        current_url = f"https://{current_url}"
                        
                elif line.startswith('Confidence:'):
                    try:
                        confidence_str = line.replace('Confidence:', '').strip()
                        current_confidence = float(confidence_str)
                    except ValueError:
                        current_confidence = 0.5
                        
                elif line.startswith('Reasoning:'):
                    current_reasoning = line.replace('Reasoning:', '').strip()
                    
                    # Complete prediction when we have all parts
                    if current_url:
                        predictions.append(URLPrediction(
                            url=current_url,
                            confidence=current_confidence,
                            reasoning=current_reasoning
                        ))
                        current_url = None
                        current_confidence = 0.5
                        current_reasoning = None
            
            # Sort by confidence (highest first)
            predictions.sort(key=lambda x: x.confidence, reverse=True)
            
            return predictions[:5]  # Limit to top 5 predictions
            
        except Exception as e:
            logger.error(f"Error parsing GPT response: {e}")
            return []
    
    async def cache_successful_url(self, ein: str, url: str, success_score: float = 1.0):
        """Cache a successfully verified URL for future use"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                now = datetime.now()
                
                await db.execute("""
                    INSERT OR REPLACE INTO organization_urls 
                    (ein, url, verified_date, success_score, last_verified)
                    VALUES (?, ?, ?, ?, ?)
                """, (ein, url, now, success_score, now))
                
                await db.commit()
                logger.info(f"Cached successful URL for EIN {ein}: {url}")
                
        except Exception as e:
            logger.error(f"Error caching URL: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the URL cache"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT COUNT(*) FROM organization_urls") as cursor:
                    total_cached = (await cursor.fetchone())[0]
                
                async with db.execute("""
                    SELECT COUNT(*) FROM organization_urls 
                    WHERE verified_date > datetime('now', '-30 days')
                """) as cursor:
                    recent_cached = (await cursor.fetchone())[0]
                
                return {
                    'total_cached_urls': total_cached,
                    'recent_cached_urls': recent_cached,
                    'cache_hit_potential': f"{recent_cached}/{total_cached}" if total_cached > 0 else "0/0"
                }
                
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}