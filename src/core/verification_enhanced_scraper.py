#!/usr/bin/env python3
"""
Verification-Enhanced Web Scraping Service

Integrates tax filing baseline data with web scraping to provide verified intelligence.
Uses 990/990-PF officer data to validate scraped leadership information and
provides confidence scoring based on verification results.

Architecture:
1. Get tax filing baseline (authoritative leadership)
2. Perform smart URL resolution (user > 990 > GPT)
3. Scrape website using priority URL
4. Verify scraped data against tax baseline
5. Return enhanced results with confidence attribution
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import logging

from .tax_filing_leadership_service import TaxFilingLeadershipService, TaxFilingBaseline
from .smart_url_resolution_service import SmartURLResolutionService, URLResolutionResult
# SimpleMCPClient removed - using direct web scraping approach

logger = logging.getLogger(__name__)


@dataclass
class VerifiedLeadershipEntry:
    """Leadership entry with verification status"""
    name: str
    title: str
    source: str  # 'tax_filing', 'web_verified', 'web_supplemental'
    confidence_score: float
    verification_status: str  # 'verified', 'unverified', 'conflicting'
    tax_filing_match: Optional[Dict[str, Any]] = None
    web_scraping_data: Optional[Dict[str, Any]] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class VerificationResult:
    """Complete verification results"""
    ein: str
    organization_name: str
    
    # Data sources
    tax_baseline: Optional[TaxFilingBaseline] = None
    url_resolution: Optional[URLResolutionResult] = None
    web_scraping_data: Optional[Dict[str, Any]] = None
    
    # Verified results
    verified_leadership: List[VerifiedLeadershipEntry] = field(default_factory=list)
    verified_website: Optional[str] = None
    verified_mission: Optional[str] = None
    verified_programs: List[str] = field(default_factory=list)
    
    # Verification metrics
    verification_confidence: float = 0.0
    data_quality_score: float = 0.0
    source_attribution: Dict[str, str] = field(default_factory=dict)
    verification_notes: List[str] = field(default_factory=list)
    
    # Processing metadata
    processed_at: datetime = field(default_factory=datetime.now)


class VerificationEnhancedScraper:
    """
    Enhanced web scraper that uses 990 tax filing data for verification.
    
    Provides authoritative baseline validation and confidence scoring
    for all scraped organization intelligence.
    """
    
    def __init__(self):
        self.tax_service = TaxFilingLeadershipService(context="profile")
        self.url_service = SmartURLResolutionService()
        # Web scraper functionality simplified - no longer using MCP
        
    async def scrape_with_verification(self, 
                                     ein: str, 
                                     organization_name: str,
                                     user_provided_url: Optional[str] = None) -> VerificationResult:
        """
        Perform verified web scraping using tax filing baseline.
        
        Args:
            ein: Organization EIN
            organization_name: Organization name
            user_provided_url: Optional user-provided website URL
            
        Returns:
            VerificationResult with verified and attributed data
        """
        logger.info(f"Starting verification-enhanced scraping for {organization_name} (EIN: {ein})")
        
        result = VerificationResult(
            ein=ein,
            organization_name=organization_name
        )
        
        try:
            # Step 1: Get tax filing baseline (authoritative data)
            logger.info("Step 1: Extracting tax filing baseline...")
            tax_baseline = await self.tax_service.get_leadership_baseline(ein)
            result.tax_baseline = tax_baseline
            
            if tax_baseline:
                officer_count = len(tax_baseline.officers) if tax_baseline.officers else 0
                logger.info(f"Tax baseline found: {officer_count} officers, revenue ${tax_baseline.total_revenue:,.0f}" if tax_baseline.total_revenue else "Tax baseline found")
                result.source_attribution["leadership_baseline"] = f"990 filing {tax_baseline.filing_year}"
            else:
                logger.warning(f"No tax filing baseline found for EIN {ein}")
                result.verification_notes.append("No 990 tax filing data available for verification")
            
            # Step 2: Smart URL resolution
            logger.info("Step 2: Resolving organization URLs...")
            url_resolution = await self.url_service.resolve_organization_url(
                ein=ein,
                organization_name=organization_name,
                user_provided_url=user_provided_url
            )
            result.url_resolution = url_resolution
            
            if url_resolution.primary_url:
                logger.info(f"Primary URL resolved: {url_resolution.primary_url.url} (source: {url_resolution.primary_url.source})")
                result.verified_website = url_resolution.primary_url.url
                result.source_attribution["website"] = url_resolution.primary_url.source_description
            else:
                logger.warning("No valid URLs found for web scraping")
                result.verification_notes.append("No valid URLs available for web scraping")
                return result
            
            # Step 3: Web scraping skipped (MCP removed)
            logger.info("Step 3: Web scraping skipped - MCP client no longer available")
            try:
                # Note: Web scraping capability removed with MCP integration
                # This section now focuses only on tax filing verification
                scraping_result = None

                if False:  # Disabled web scraping section
                    # Store minimal web scraping metadata only - DO NOT store poor quality extracted data
                    # The verification step will handle data quality and only include verified results
                    pages_count = len(scraping_result.pages_scraped) if scraping_result.pages_scraped else 0
                    result.web_scraping_data = {
                        "pages_scraped": pages_count,
                        "scraping_success": True,
                        "intelligence_score": scraping_result.intelligence_score,
                        "processing_time": scraping_result.processing_time,
                        "raw_data_quality_note": "Raw data not included - only verified results used"
                    }

                    # Store raw scraping data temporarily for verification step only
                    result._raw_scraping_data = {
                        "leadership": scraping_result.leadership_data if scraping_result.leadership_data else [],
                        "programs": scraping_result.program_data if scraping_result.program_data else [],
                        "mission_statements": scraping_result.mission_data if scraping_result.mission_data else [],
                        "contact": scraping_result.contact_data if scraping_result.contact_data else {}
                    }

                    logger.info(f"Web scraping successful: {pages_count} pages (raw data stored for verification only)")
                elif scraping_result:
                    error_msg = "; ".join(scraping_result.errors) if scraping_result.errors else "Unknown error"
                    result.web_scraping_data = {"scraping_success": False, "error": error_msg}
                    logger.warning(f"Web scraping failed: {error_msg}")
                else:
                    result.web_scraping_data = {"scraping_success": False, "error": "Scraping result is None"}
                    logger.warning("Web scraping returned None result")

            except Exception as e:
                logger.error(f"Web scraping error: {e}")
                result.web_scraping_data = {"scraping_success": False, "error": str(e)}
            
            # Step 4: Verification and data fusion
            logger.info("Step 4: Verifying scraped data against tax baseline...")
            result = await self._verify_and_fuse_data(result)
            
            # Step 5: Calculate overall quality metrics
            result = self._calculate_quality_metrics(result)
            
            leadership_count = len(result.verified_leadership) if result.verified_leadership else 0
            logger.info(f"Verification complete: {result.verification_confidence:.2%} confidence, {leadership_count} verified leaders")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in verification-enhanced scraping: {e}")
            result.verification_notes.append(f"Processing error: {str(e)}")
            return result
    
    async def _verify_and_fuse_data(self, result: VerificationResult) -> VerificationResult:
        """Verify scraped data against tax baseline and create verified dataset"""
        
        # Verify leadership data
        result.verified_leadership = await self._verify_leadership_data(result)
        
        # Verify mission statement
        result.verified_mission = self._verify_mission_statement(result)
        
        # Verify programs
        result.verified_programs = self._verify_program_data(result)
        
        # Calculate verification confidence
        result.verification_confidence = self._calculate_verification_confidence(result)
        
        return result
    
    async def _verify_leadership_data(self, result: VerificationResult) -> List[VerifiedLeadershipEntry]:
        """Verify leadership data using tax filing baseline"""
        verified_leaders = []

        # Start with tax filing officers (highest confidence)
        if result.tax_baseline and result.tax_baseline.officers:
            for officer in result.tax_baseline.officers:
                verified_leader = VerifiedLeadershipEntry(
                    name=officer.name,
                    title=officer.title,
                    source="tax_filing",
                    confidence_score=1.0,  # Highest confidence
                    verification_status="verified",
                    tax_filing_match={
                        "name": officer.name,
                        "title": officer.title,
                        "compensation": officer.compensation
                    },
                    notes=["From 990 tax filing - authoritative source"]
                )
                verified_leaders.append(verified_leader)

            # When we have tax filing data, only add HIGH-QUALITY web scraping data
            officer_count = len(result.tax_baseline.officers) if result.tax_baseline.officers else 0
            logger.info(f"Using {officer_count} authoritative tax filing officers, filtering low-quality web data")
        
        # Add verified web scraped leadership (using raw data for verification)
        if (result.web_scraping_data and
            result.web_scraping_data.get("scraping_success") and
            hasattr(result, '_raw_scraping_data') and
            result._raw_scraping_data.get("leadership")):

            scraped_leadership = result._raw_scraping_data.get("leadership", [])
            if not scraped_leadership:
                logger.info("No leadership data found in web scraping results")
                scraped_leadership = []

            # Filter out poor quality web scraping data
            quality_leadership = []
            for leader in scraped_leadership:
                if isinstance(leader, dict):
                    name = leader.get("name", "")
                    title = leader.get("title", "")

                    # Quality checks: reject clearly bad extractions
                    if (len(name) > 3 and len(name) < 50 and  # Reasonable name length
                        not any(bad_word in name.lower() for bad_word in ["facebook", "instagram", "twitter", "aging veterans", "items about", "contact us"]) and
                        len(title) > 2 and len(title) < 30 and  # Reasonable title length
                        title.lower() != "leadership"):  # Not just generic "Leadership"
                        quality_leadership.append(leader)
                    else:
                        logger.info(f"Filtered out poor quality leadership entry: {name} - {title}")

            scraped_count = len(scraped_leadership) if scraped_leadership else 0
            quality_count = len(quality_leadership) if quality_leadership else 0
            logger.info(f"Quality filter: {scraped_count} -> {quality_count} leadership entries")
            scraped_leadership = quality_leadership

            # Use tax service verification if baseline available
            if result.tax_baseline:
                verification_results = self.tax_service.verify_web_scraping_against_baseline(
                    scraped_leadership, result.tax_baseline
                )
                
                # Add verified matches (web data that matches tax filing)
                for match in verification_results["verified_matches"]:
                    # Check if we already have this person from tax filing
                    existing_leader = None
                    for leader in verified_leaders:
                        if self._names_match(leader.name, match["scraped_data"]["name"]):
                            existing_leader = leader
                            break
                    
                    if existing_leader:
                        # Enhance existing tax filing entry with web data
                        existing_leader.web_scraping_data = match["scraped_data"]
                        existing_leader.source = "web_verified"
                        existing_leader.notes.append("Verified by web scraping match")
                    else:
                        # New verified leader from web scraping
                        verified_leader = VerifiedLeadershipEntry(
                            name=match["scraped_data"]["name"],
                            title=match["scraped_data"].get("title", "Officer"),
                            source="web_verified",
                            confidence_score=match["confidence_score"],
                            verification_status="verified",
                            web_scraping_data=match["scraped_data"],
                            tax_filing_match=match["baseline_data"],
                            notes=["Web scraped data verified against 990 filing"]
                        )
                        verified_leaders.append(verified_leader)
                
                # Add unverified web data as supplemental (lower confidence)
                for unverified in verification_results["unverified_scraped"]:
                    # Filter out obvious fake data
                    if not self._is_likely_fake_data(unverified.get("name", "")):
                        verified_leader = VerifiedLeadershipEntry(
                            name=unverified["name"],
                            title=unverified.get("title", "Officer"),
                            source="web_supplemental",
                            confidence_score=0.3,  # Lower confidence
                            verification_status="unverified",
                            web_scraping_data=unverified,
                            notes=["Web scraped data - no 990 verification available"]
                        )
                        verified_leaders.append(verified_leader)
            
            else:
                # No tax baseline - treat all web data as unverified
                for leader_data in scraped_leadership:
                    if not self._is_likely_fake_data(leader_data.get("name", "")):
                        verified_leader = VerifiedLeadershipEntry(
                            name=leader_data["name"],
                            title=leader_data.get("title", "Officer"),
                            source="web_supplemental",
                            confidence_score=0.5,  # Medium confidence without verification
                            verification_status="unverified",
                            web_scraping_data=leader_data,
                            notes=["Web scraped data - no tax filing available for verification"]
                        )
                        verified_leaders.append(verified_leader)
        
        return verified_leaders
    
    def _verify_mission_statement(self, result: VerificationResult) -> Optional[str]:
        """Verify and select best mission statement"""
        tax_mission = result.tax_baseline.mission_statement if result.tax_baseline else None
        web_mission = None
        
        if (result.web_scraping_data and
            result.web_scraping_data.get("scraping_success") and
            hasattr(result, '_raw_scraping_data') and
            result._raw_scraping_data.get("mission_statements")):
            missions = result._raw_scraping_data.get("mission_statements", [])
            web_mission = missions[0] if missions and len(missions) > 0 else None
        
        # Prioritize tax filing mission, fall back to web
        if tax_mission:
            result.source_attribution["mission"] = "990 tax filing"
            return tax_mission
        elif web_mission:
            result.source_attribution["mission"] = "web scraping"
            return web_mission
        
        return None
    
    def _verify_program_data(self, result: VerificationResult) -> List[str]:
        """Verify and combine program data"""
        programs = []
        
        # Add tax filing programs (high confidence)
        if result.tax_baseline and result.tax_baseline.program_activities:
            programs.extend(result.tax_baseline.program_activities)
            result.source_attribution["programs"] = "990 tax filing + web scraping"

        # Add web scraped programs (supplemental, from raw data)
        if (result.web_scraping_data and
            result.web_scraping_data.get("scraping_success") and
            hasattr(result, '_raw_scraping_data') and
            result._raw_scraping_data.get("programs")):
            web_programs = result._raw_scraping_data.get("programs", [])
            if web_programs:
                for program in web_programs:
                    if program and program not in programs:  # Avoid duplicates and None values
                        programs.append(program)
            
            if not result.tax_baseline:
                result.source_attribution["programs"] = "web scraping"
        
        return programs
    
    def _calculate_verification_confidence(self, result: VerificationResult) -> float:
        """Calculate overall verification confidence"""
        confidence_factors = []
        
        # Tax baseline availability
        if result.tax_baseline:
            confidence_factors.append(0.4)  # High weight for tax data
        
        # URL resolution confidence
        if result.url_resolution and result.url_resolution.primary_url:
            url_confidence = result.url_resolution.confidence_assessment.get("overall_confidence", 0)
            confidence_factors.append(url_confidence * 0.2)
        
        # Web scraping success
        if result.web_scraping_data and result.web_scraping_data.get("scraping_success"):
            confidence_factors.append(0.2)
        
        # Leadership verification rate
        if result.verified_leadership:
            verified_count = len([l for l in result.verified_leadership if l.verification_status == "verified"])
            total_leadership = len(result.verified_leadership)
            verification_rate = verified_count / total_leadership if total_leadership > 0 else 0
            confidence_factors.append(verification_rate * 0.2)
        
        return sum(confidence_factors) if confidence_factors else 0.0
    
    def _calculate_quality_metrics(self, result: VerificationResult) -> VerificationResult:
        """Calculate overall data quality metrics"""
        quality_factors = []
        
        # Data completeness
        completeness = 0.0
        if result.verified_leadership:
            completeness += 0.4
        if result.verified_mission:
            completeness += 0.3
        if result.verified_programs:
            completeness += 0.3
        
        quality_factors.append(completeness)
        
        # Data verification rate
        if result.verified_leadership:
            verified_count = len([l for l in result.verified_leadership if l.verification_status == "verified"])
            total_leadership = len(result.verified_leadership)
            verified_rate = verified_count / total_leadership if total_leadership > 0 else 0
            quality_factors.append(verified_rate)
        
        # Source diversity (multiple sources are better)
        source_count = len(set(result.source_attribution.values()))
        source_diversity = min(source_count / 3.0, 1.0)  # Max 3 sources
        quality_factors.append(source_diversity)
        
        result.data_quality_score = sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
        
        return result
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if two names likely refer to the same person"""
        # Simple name matching - could be enhanced with fuzzy matching
        name1_clean = name1.lower().strip()
        name2_clean = name2.lower().strip()
        
        # Exact match
        if name1_clean == name2_clean:
            return True
        
        # Check if one name is contained in the other (handles "John Smith" vs "John A. Smith")
        name1_parts = set(name1_clean.split())
        name2_parts = set(name2_clean.split())
        
        # If both first and last names match
        if len(name1_parts.intersection(name2_parts)) >= 2:
            return True
        
        return False
    
    def _is_likely_fake_data(self, name: str) -> bool:
        """Filter out obviously fake or fragmented data"""
        if not name or len(name.strip()) < 3:
            return True
        
        # Known fake patterns from previous analysis
        fake_patterns = [
            'board of', 'serving as', 'was appointed', 'executive vice',
            'been the', 'serves as', 'on the', 'at colliers', 'ramps to',
            'john smith', 'jane doe'  # Common test names
        ]
        
        name_lower = name.lower().strip()
        return any(pattern in name_lower for pattern in fake_patterns)