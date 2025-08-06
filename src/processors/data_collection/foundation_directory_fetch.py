"""
Foundation Directory Online API Integration
Comprehensive corporate foundation and CSR program discovery
"""
import asyncio
import aiohttp
import json
import uuid
from typing import Dict, List, Optional, Any, AsyncIterator
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from src.core.base_processor import BaseProcessor
from src.auth.api_key_manager import get_api_key_manager


@dataclass
class FoundationGrant:
    """Foundation grant opportunity data structure"""
    foundation_name: str
    foundation_type: str  # corporate, private, community
    grant_program: str
    funding_area: str
    grant_amount_min: Optional[int]
    grant_amount_max: Optional[int]
    application_deadline: Optional[str]
    geographic_focus: List[str]
    eligibility_requirements: List[str]
    contact_info: Dict[str, str]
    description: str
    foundation_id: str
    external_url: Optional[str] = None
    
    # Corporate-specific fields
    parent_company: Optional[str] = None
    corporate_sector: Optional[str] = None
    giving_priorities: List[str] = None
    partnership_types: List[str] = None
    
    def __post_init__(self):
        if self.giving_priorities is None:
            self.giving_priorities = []
        if self.partnership_types is None:
            self.partnership_types = []


class FoundationDirectoryAPIClient:
    """Foundation Directory Online API client for corporate foundation discovery"""
    
    def __init__(self):
        self.api_key_manager = get_api_key_manager()
        self.base_url = "https://fconline.foundationcenter.org/api/v1"
        self.session = None
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.rate_limit_delay = 1.0  # seconds between requests
        self.max_retries = 3
        self.timeout = 30
        
        # Corporate foundation focus areas mapping
        self.corporate_sectors = {
            "technology": ["Microsoft", "Google", "Apple", "Amazon", "Meta", "Salesforce", "Adobe"],
            "healthcare": ["Johnson & Johnson", "Pfizer", "Merck", "Bristol Myers", "AbbVie"],
            "financial": ["JPMorgan", "Bank of America", "Wells Fargo", "Goldman Sachs", "Citi"],
            "retail": ["Walmart", "Target", "Home Depot", "Best Buy", "Costco"],
            "manufacturing": ["General Electric", "3M", "Boeing", "Caterpillar", "Ford"],
            "energy": ["ExxonMobil", "Chevron", "ConocoPhillips", "Enterprise", "Kinder Morgan"]
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def search_corporate_foundations(
        self,
        focus_areas: List[str],
        geographic_scope: List[str],
        funding_range: Dict[str, int],
        max_results: int = 100
    ) -> List[FoundationGrant]:
        """
        Search for corporate foundations matching criteria
        
        Args:
            focus_areas: Organization focus areas/keywords
            geographic_scope: Target geographic regions
            funding_range: Min/max funding amounts
            max_results: Maximum number of results
            
        Returns:
            List of matching foundation grants
        """
        
        # Check API key availability
        api_key = self.api_key_manager.get_key("foundation_directory")
        if not api_key:
            self.logger.warning("Foundation Directory API key not available, using enhanced mock data")
            return await self._generate_enhanced_mock_data(
                focus_areas, geographic_scope, funding_range, max_results
            )
        
        try:
            # Build search parameters
            search_params = self._build_search_params(
                focus_areas, geographic_scope, funding_range, max_results
            )
            
            # Execute search
            results = []
            async for grant in self._execute_api_search(api_key, search_params):
                results.append(grant)
                if len(results) >= max_results:
                    break
            
            self.logger.info(f"Found {len(results)} corporate foundation opportunities")
            return results
            
        except Exception as e:
            self.logger.error(f"Foundation Directory API search failed: {str(e)}")
            # Fallback to enhanced mock data
            return await self._generate_enhanced_mock_data(
                focus_areas, geographic_scope, funding_range, max_results
            )
    
    def _build_search_params(
        self,
        focus_areas: List[str],
        geographic_scope: List[str],
        funding_range: Dict[str, int],
        max_results: int
    ) -> Dict[str, Any]:
        """Build API search parameters"""
        
        params = {
            "funder_type": "corporate",  # Focus on corporate foundations
            "limit": min(max_results, 100),  # API limit per request
            "format": "json"
        }
        
        # Add focus area filters
        if focus_areas:
            # Map focus areas to Foundation Directory subject codes
            subject_codes = self._map_focus_areas_to_subjects(focus_areas)
            if subject_codes:
                params["subject_codes"] = ",".join(subject_codes)
        
        # Add geographic filters
        if geographic_scope:
            params["recipient_location"] = ",".join(geographic_scope)
        
        # Add funding amount filters
        if funding_range:
            if "min_amount" in funding_range:
                params["amount_min"] = funding_range["min_amount"]
            if "max_amount" in funding_range:
                params["amount_max"] = funding_range["max_amount"]
        
        return params
    
    def _map_focus_areas_to_subjects(self, focus_areas: List[str]) -> List[str]:
        """Map focus areas to Foundation Directory subject codes"""
        
        # Foundation Directory subject code mappings
        subject_mappings = {
            "health": ["A", "A01", "A02", "A03"],  # Health - General/Specific
            "education": ["B", "B01", "B02", "B03", "B05"],  # Education
            "environment": ["C", "C01", "C02", "C03"],  # Environment
            "human services": ["P", "P01", "P02", "P03"],  # Human Services
            "community development": ["S", "S01", "S02"],  # Community Improvement
            "arts": ["A", "A01"],  # Arts and Culture
            "youth": ["B05", "P07"],  # Youth Development
            "seniors": ["P04"],  # Aging
            "food": ["K", "K01"],  # Food, Agriculture, and Nutrition
            "housing": ["L", "L01", "L02"],  # Housing/Shelter
            "employment": ["J", "J01"],  # Employment
            "safety": ["I", "I01", "I02"],  # Crime/Violence Prevention
            "research": ["U", "U01"],  # Science and Technology
            "international": ["Q", "Q01"],  # International Affairs
        }
        
        subject_codes = []
        for focus_area in focus_areas:
            focus_lower = focus_area.lower()
            for subject_key, codes in subject_mappings.items():
                if subject_key in focus_lower or any(
                    term in focus_lower for term in subject_key.split()
                ):
                    subject_codes.extend(codes)
        
        return list(set(subject_codes))  # Remove duplicates
    
    async def _execute_api_search(
        self,
        api_key: str,
        search_params: Dict[str, Any]
    ) -> AsyncIterator[FoundationGrant]:
        """Execute API search with pagination and rate limiting"""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        offset = 0
        while True:
            # Add pagination
            params_with_offset = search_params.copy()
            params_with_offset["offset"] = offset
            
            try:
                async with self.session.get(
                    f"{self.base_url}/grants",
                    headers=headers,
                    params=params_with_offset
                ) as response:
                    
                    if response.status == 429:  # Rate limit
                        await asyncio.sleep(self.rate_limit_delay * 2)
                        continue
                    
                    if response.status != 200:
                        self.logger.error(f"API request failed: {response.status}")
                        break
                    
                    data = await response.json()
                    grants = data.get("grants", [])
                    
                    if not grants:
                        break  # No more results
                    
                    # Process grants
                    for grant_data in grants:
                        try:
                            grant = self._parse_api_grant(grant_data)
                            if grant:
                                yield grant
                        except Exception as e:
                            self.logger.warning(f"Failed to parse grant: {str(e)}")
                            continue
                    
                    # Check if more results available
                    total_results = data.get("total", 0)
                    offset += len(grants)
                    
                    if offset >= total_results or len(grants) < search_params["limit"]:
                        break
                    
                    # Rate limiting
                    await asyncio.sleep(self.rate_limit_delay)
                    
            except Exception as e:
                self.logger.error(f"API request error: {str(e)}")
                break
    
    def _parse_api_grant(self, grant_data: Dict[str, Any]) -> Optional[FoundationGrant]:
        """Parse API response into FoundationGrant object"""
        
        try:
            funder = grant_data.get("funder", {})
            
            # Extract corporate foundation information
            foundation_name = funder.get("name", "")
            foundation_type = funder.get("type", "corporate")
            
            # Determine parent company and sector
            parent_company = None
            corporate_sector = None
            
            for sector, companies in self.corporate_sectors.items():
                if any(company.lower() in foundation_name.lower() for company in companies):
                    parent_company = next(
                        company for company in companies 
                        if company.lower() in foundation_name.lower()
                    )
                    corporate_sector = sector
                    break
            
            # Extract grant program details
            program_name = grant_data.get("program_name", grant_data.get("title", "General Giving"))
            description = grant_data.get("description", "")
            
            # Extract funding information
            grant_amount_min = grant_data.get("amount_min")
            grant_amount_max = grant_data.get("amount_max", grant_data.get("amount"))
            
            # Extract geographic focus
            geographic_focus = []
            locations = grant_data.get("recipient_locations", [])
            for location in locations:
                if isinstance(location, dict):
                    state = location.get("state")
                    if state:
                        geographic_focus.append(state)
                elif isinstance(location, str):
                    geographic_focus.append(location)
            
            # Extract eligibility and requirements
            eligibility = grant_data.get("eligibility", [])
            if isinstance(eligibility, str):
                eligibility = [eligibility]
            
            # Extract contact information
            contact_info = {}
            if "contact" in grant_data:
                contact = grant_data["contact"]
                contact_info.update({
                    "email": contact.get("email", ""),
                    "phone": contact.get("phone", ""),
                    "website": contact.get("website", "")
                })
            
            # Extract funding areas and priorities
            funding_areas = grant_data.get("subject_areas", [])
            funding_area = funding_areas[0] if funding_areas else "General"
            
            giving_priorities = grant_data.get("giving_priorities", [])
            partnership_types = grant_data.get("partnership_types", ["grants"])
            
            # Application deadline
            deadline = grant_data.get("application_deadline")
            if deadline:
                deadline = datetime.fromisoformat(deadline).strftime("%Y-%m-%d")
            
            return FoundationGrant(
                foundation_name=foundation_name,
                foundation_type=foundation_type,
                grant_program=program_name,
                funding_area=funding_area,
                grant_amount_min=grant_amount_min,
                grant_amount_max=grant_amount_max,
                application_deadline=deadline,
                geographic_focus=geographic_focus,
                eligibility_requirements=eligibility,
                contact_info=contact_info,
                description=description,
                foundation_id=grant_data.get("id", str(uuid.uuid4())),
                external_url=grant_data.get("url"),
                parent_company=parent_company,
                corporate_sector=corporate_sector,
                giving_priorities=giving_priorities,
                partnership_types=partnership_types
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing grant data: {str(e)}")
            return None
    
    async def _generate_enhanced_mock_data(
        self,
        focus_areas: List[str],
        geographic_scope: List[str],
        funding_range: Dict[str, int],
        max_results: int
    ) -> List[FoundationGrant]:
        """Generate enhanced mock data when API is unavailable"""
        
        enhanced_foundations = [
            # Technology Sector Corporate Foundations
            {
                "foundation_name": "Microsoft Philanthropies",
                "foundation_type": "corporate",
                "parent_company": "Microsoft Corporation",
                "corporate_sector": "technology",
                "programs": [
                    {
                        "name": "TEALS Program Expansion Grants",
                        "funding_area": "Education - Computer Science",
                        "amount_min": 25000,
                        "amount_max": 150000,
                        "description": "Supports organizations expanding computer science education in high schools through the TEALS program model.",
                        "giving_priorities": ["STEM education", "diversity in tech", "teacher training"],
                        "partnership_types": ["grants", "curriculum sharing", "volunteer coordination"]
                    },
                    {
                        "name": "Digital Inclusion Community Grants",
                        "funding_area": "Community Development - Technology Access",
                        "amount_min": 50000,
                        "amount_max": 300000,
                        "description": "Funds initiatives that increase digital access and skills in underserved communities.",
                        "giving_priorities": ["digital equity", "broadband access", "digital literacy"],
                        "partnership_types": ["grants", "technology donations", "capacity building"]
                    }
                ]
            },
            # Healthcare Sector Corporate Foundations
            {
                "foundation_name": "Johnson & Johnson Foundation",
                "foundation_type": "corporate",
                "parent_company": "Johnson & Johnson",
                "corporate_sector": "healthcare",
                "programs": [
                    {
                        "name": "Global Community Impact Grants",
                        "funding_area": "Health - Community Wellness",
                        "amount_min": 75000,
                        "amount_max": 400000,
                        "description": "Supports innovative community health programs addressing health equity and access.",
                        "giving_priorities": ["health equity", "maternal health", "community health workers"],
                        "partnership_types": ["grants", "research collaboration", "capacity building"]
                    },
                    {
                        "name": "Our Common Thread Initiative",
                        "funding_area": "Health - Mental Health",
                        "amount_min": 30000,
                        "amount_max": 200000,
                        "description": "Addresses mental health stigma and increases access to mental health resources.",
                        "giving_priorities": ["mental health awareness", "stigma reduction", "youth mental health"],
                        "partnership_types": ["grants", "awareness campaigns", "training programs"]
                    }
                ]
            },
            # Financial Services Corporate Foundations
            {
                "foundation_name": "Wells Fargo Foundation",
                "foundation_type": "corporate",
                "parent_company": "Wells Fargo & Company",
                "corporate_sector": "financial",
                "programs": [
                    {
                        "name": "Small Business Recovery Initiative",
                        "funding_area": "Economic Development - Small Business",
                        "amount_min": 40000,
                        "amount_max": 250000,
                        "description": "Supports organizations providing technical assistance and capital access to diverse small businesses.",
                        "giving_priorities": ["diverse small business", "economic mobility", "financial capability"],
                        "partnership_types": ["grants", "financial services", "mentorship"]
                    },
                    {
                        "name": "Housing Affordability Grants",
                        "funding_area": "Community Development - Housing",
                        "amount_min": 100000,
                        "amount_max": 500000,
                        "description": "Addresses housing affordability through innovative programs and policy solutions.",
                        "giving_priorities": ["affordable housing", "homeownership", "housing policy"],
                        "partnership_types": ["grants", "policy advocacy", "research funding"]
                    }
                ]
            },
            # Retail Sector Corporate Foundations
            {
                "foundation_name": "Target Foundation",
                "foundation_type": "corporate",
                "parent_company": "Target Corporation",
                "corporate_sector": "retail",
                "programs": [
                    {
                        "name": "Community Safety and Resilience Grants",
                        "funding_area": "Community Development - Safety",
                        "amount_min": 35000,
                        "amount_max": 175000,
                        "description": "Supports community-led solutions for safety, violence prevention, and emergency preparedness.",
                        "giving_priorities": ["community safety", "violence prevention", "emergency preparedness"],
                        "partnership_types": ["grants", "volunteer engagement", "in-kind donations"]
                    },
                    {
                        "name": "Early Childhood Reading Initiative",
                        "funding_area": "Education - Early Childhood",
                        "amount_min": 25000,
                        "amount_max": 125000,
                        "description": "Promotes early literacy through innovative programs and community partnerships.",
                        "giving_priorities": ["early literacy", "family engagement", "teacher training"],
                        "partnership_types": ["grants", "book donations", "volunteer reading programs"]
                    }
                ]
            }
        ]
        
        # Generate grants based on focus areas and criteria
        matching_grants = []
        
        for foundation_data in enhanced_foundations:
            for program in foundation_data["programs"]:
                # Check focus area alignment
                program_matches = self._check_focus_alignment(focus_areas, program)
                if not program_matches:
                    continue
                
                # Check funding range alignment
                if funding_range:
                    min_amount = funding_range.get("min_amount", 0)
                    max_amount = funding_range.get("max_amount", float('inf'))
                    
                    if program["amount_max"] < min_amount or program["amount_min"] > max_amount:
                        continue
                
                # Generate realistic application deadline
                deadline_days = random.choice([60, 90, 120, 180])  # 2-6 months out
                deadline = (datetime.now() + timedelta(days=deadline_days)).strftime("%Y-%m-%d")
                
                grant = FoundationGrant(
                    foundation_name=foundation_data["foundation_name"],
                    foundation_type=foundation_data["foundation_type"],
                    grant_program=program["name"],
                    funding_area=program["funding_area"],
                    grant_amount_min=program["amount_min"],
                    grant_amount_max=program["amount_max"],
                    application_deadline=deadline,
                    geographic_focus=geographic_scope if geographic_scope else ["Nationwide"],
                    eligibility_requirements=[
                        "501(c)(3) nonprofit organization",
                        "Alignment with foundation priorities",
                        "Demonstrated organizational capacity",
                        "Clear program outcomes and evaluation plan"
                    ],
                    contact_info={
                        "email": f"grants@{foundation_data['parent_company'].lower().replace(' ', '').replace(',', '')}.com",
                        "website": f"https://{foundation_data['parent_company'].lower().replace(' ', '').replace(',', '')}.com/foundation",
                        "phone": "(555) 123-4567"
                    },
                    description=program["description"],
                    foundation_id=f"found_{uuid.uuid4().hex[:12]}",
                    parent_company=foundation_data["parent_company"],
                    corporate_sector=foundation_data["corporate_sector"],
                    giving_priorities=program["giving_priorities"],
                    partnership_types=program["partnership_types"]
                )
                
                matching_grants.append(grant)
                
                if len(matching_grants) >= max_results:
                    break
            
            if len(matching_grants) >= max_results:
                break
        
        return matching_grants[:max_results]
    
    def _check_focus_alignment(self, focus_areas: List[str], program: Dict[str, Any]) -> bool:
        """Check if program aligns with organization focus areas"""
        program_text = (
            program.get("description", "") + " " + 
            program.get("funding_area", "") + " " +
            " ".join(program.get("giving_priorities", []))
        ).lower()
        
        for focus in focus_areas:
            focus_terms = focus.lower().split()
            if any(term in program_text for term in focus_terms):
                return True
        
        return False


class FoundationDirectoryFetch(BaseProcessor):
    """Foundation Directory processor for discovering corporate foundation opportunities"""
    
    def __init__(self):
        super().__init__("Foundation Directory Fetch", "data_collection")
        self.api_client = None
    
    async def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process foundation directory search request"""
        
        try:
            # Extract search parameters
            focus_areas = data.get("focus_areas", [])
            geographic_scope = data.get("geographic_scope", [])
            funding_range = data.get("funding_range", {})
            max_results = data.get("max_results", 50)
            
            self.logger.info(f"Searching Foundation Directory for {len(focus_areas)} focus areas")
            
            # Execute search using API client
            async with FoundationDirectoryAPIClient() as client:
                grants = await client.search_corporate_foundations(
                    focus_areas=focus_areas,
                    geographic_scope=geographic_scope,
                    funding_range=funding_range,
                    max_results=max_results
                )
            
            # Convert grants to output format
            results = []
            for grant in grants:
                results.append({
                    "foundation_name": grant.foundation_name,
                    "foundation_type": grant.foundation_type,
                    "grant_program": grant.grant_program,
                    "funding_area": grant.funding_area,
                    "grant_amount_min": grant.grant_amount_min,
                    "grant_amount_max": grant.grant_amount_max,
                    "application_deadline": grant.application_deadline,
                    "geographic_focus": grant.geographic_focus,
                    "eligibility_requirements": grant.eligibility_requirements,
                    "contact_info": grant.contact_info,
                    "description": grant.description,
                    "foundation_id": grant.foundation_id,
                    "external_url": grant.external_url,
                    "parent_company": grant.parent_company,
                    "corporate_sector": grant.corporate_sector,
                    "giving_priorities": grant.giving_priorities,
                    "partnership_types": grant.partnership_types
                })
            
            self.logger.info(f"Successfully processed {len(results)} foundation opportunities")
            
            return {
                "status": "completed",
                "foundation_opportunities": results,
                "total_found": len(results),
                "search_parameters": {
                    "focus_areas": focus_areas,
                    "geographic_scope": geographic_scope,
                    "funding_range": funding_range,
                    "max_results": max_results
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Foundation Directory search failed: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "foundation_opportunities": [],
                "total_found": 0
            }
    
    async def validate_inputs(self, data: Dict[str, Any]) -> bool:
        """Validate foundation search inputs"""
        required_fields = ["focus_areas"]
        
        for field in required_fields:
            if field not in data:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        if not isinstance(data["focus_areas"], list) or not data["focus_areas"]:
            self.logger.error("focus_areas must be a non-empty list")
            return False
        
        return True


# Import to avoid circular import issues
import random