#!/usr/bin/env python3
"""
Verified Intelligence Service

Hybrid data pipeline that combines tax-data-first verification with web intelligence.
Replaces the basic enhanced data service with a comprehensive verification system.

Architecture:
1. User-provided Profile URL (highest confidence - user knows the organization)
2. 990/990-PF declared website (official tax filing data)  
3. GPT prediction URLs (lowest confidence - algorithmic guess)

For board members: 990/990-PF officers first, then web scraping for verification/enhancement.
Eliminates fake data by using authoritative sources for verification.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from pathlib import Path

from src.core.verification_enhanced_scraper import VerificationEnhancedScraper, VerificationResult
from src.web.services.enhanced_data_service import EnhancedDataService, EnhancedDataResult
from src.core.data_source_priority import (
    DataPriorityResolver, DataSource, DataSourceEntry, get_data_priority_resolver
)

logger = logging.getLogger(__name__)


@dataclass
class VerifiedIntelligenceResult:
    """Result from verified intelligence gathering with source attribution"""
    profile_id: str
    organization_name: str
    ein: Optional[str]
    
    # Core verification data
    verification_result: Optional[VerificationResult]
    
    # Legacy enhanced data (for compatibility)
    enhanced_data: Optional[EnhancedDataResult]
    
    # Consolidated intelligence
    verified_leadership: List[Dict[str, Any]]  # With source attribution and confidence
    verified_mission: Optional[str]
    verified_programs: List[str]
    verified_website: Optional[str]
    
    # Quality metrics
    overall_confidence: float
    data_quality_score: float
    source_attribution: Dict[str, str]
    
    # Processing metadata
    processing_time: float
    fetched_at: datetime
    data_sources_used: List[str]
    verification_notes: List[str]
    
    # Compatibility fields for existing UI
    intelligence_quality_score: int  # 0-100 for UI compatibility
    leadership_count: int
    program_count: int
    pages_scraped: int
    has_990_baseline: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            'profile_id': self.profile_id,
            'organization_name': self.organization_name,
            'ein': self.ein,
            'verified_leadership': self.verified_leadership,
            'verified_mission': self.verified_mission,
            'verified_programs': self.verified_programs,
            'verified_website': self.verified_website,
            'overall_confidence': self.overall_confidence,
            'data_quality_score': self.data_quality_score,
            'source_attribution': self.source_attribution,
            'processing_time': self.processing_time,
            'fetched_at': self.fetched_at.isoformat(),
            'data_sources_used': self.data_sources_used,
            'verification_notes': self.verification_notes,
            'intelligence_quality_score': self.intelligence_quality_score,
            'leadership_count': self.leadership_count,
            'program_count': self.program_count,
            'pages_scraped': self.pages_scraped,
            'has_990_baseline': self.has_990_baseline
        }


class VerifiedIntelligenceService:
    """
    Service for verified intelligence gathering with tax-data-first approach.
    
    Combines 990/990-PF baseline verification with web scraping intelligence
    to provide high-confidence organizational data with transparent source attribution.
    """
    
    def __init__(self):
        self.verification_scraper = VerificationEnhancedScraper()
        self.enhanced_data_service = EnhancedDataService()  # For backward compatibility
        self.priority_resolver = get_data_priority_resolver()  # Data source conflict resolution

        # Cache for verified results
        self.verification_cache: Dict[str, VerifiedIntelligenceResult] = {}
        self.cache_duration_hours = 24

        # Statistics tracking
        self.stats = {
            'total_requests': 0,
            'verification_success': 0,
            'tax_baseline_found': 0,
            'web_scraping_success': 0,
            'cache_hits': 0,
            'average_confidence': 0.0,
            'conflicts_resolved': 0,
            'data_sources_merged': 0
        }
    
    async def get_verified_intelligence(
        self, 
        profile_id: str,
        organization_name: str, 
        ein: Optional[str],
        user_provided_url: Optional[str] = None,
        force_refresh: bool = False
    ) -> VerifiedIntelligenceResult:
        """
        Get verified intelligence for an organization using tax-data-first approach.
        
        Args:
            profile_id: Profile identifier
            organization_name: Organization name
            ein: Organization EIN
            user_provided_url: Optional user-provided website URL
            force_refresh: Force refresh ignoring cache
            
        Returns:
            VerifiedIntelligenceResult with comprehensive verified data
        """
        start_time = datetime.now()
        logger.info(f"Getting verified intelligence for {organization_name} (EIN: {ein})")
        
        try:
            # Check cache first
            if not force_refresh:
                cached_result = self._get_cached_result(profile_id)
                if cached_result:
                    self.stats['cache_hits'] += 1
                    logger.info(f"Using cached verified intelligence for {organization_name}")
                    return cached_result
            
            # Perform verification-enhanced scraping
            verification_result = None
            if ein:
                verification_result = await self.verification_scraper.scrape_with_verification(
                    ein=ein,
                    organization_name=organization_name,
                    user_provided_url=user_provided_url
                )
            
            # Get legacy enhanced data for compatibility (optional)
            enhanced_data = None
            try:
                # Create opportunity-like object for enhanced data service
                opportunity = {
                    'opportunity_id': profile_id,
                    'organization_name': organization_name,
                    'ein': ein,
                    'external_data': {'ein': ein} if ein else {}
                }
                enhanced_data = await self.enhanced_data_service.fetch_enhanced_data_for_opportunity(
                    opportunity, score=0.8  # Always fetch for profiles
                )
            except Exception as e:
                logger.warning(f"Enhanced data fetch failed for {organization_name}: {e}")
            
            # Create consolidated verified intelligence result
            verified_result = self._create_verified_intelligence_result(
                profile_id, organization_name, ein, verification_result, enhanced_data, start_time
            )
            
            # Cache the result
            self._cache_result(profile_id, verified_result)
            
            # Update statistics
            self._update_stats(verified_result)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            verified_result.processing_time = processing_time
            
            logger.info(f"Verified intelligence complete for {organization_name}: {verified_result.overall_confidence:.2%} confidence")
            
            return verified_result
            
        except Exception as e:
            logger.error(f"Error getting verified intelligence for {organization_name}: {e}")
            
            # Return minimal error result
            return VerifiedIntelligenceResult(
                profile_id=profile_id,
                organization_name=organization_name,
                ein=ein,
                verification_result=None,
                enhanced_data=None,
                verified_leadership=[],
                verified_mission=None,
                verified_programs=[],
                verified_website=user_provided_url,
                overall_confidence=0.0,
                data_quality_score=0.0,
                source_attribution={'error': f'Processing failed: {str(e)}'},
                processing_time=(datetime.now() - start_time).total_seconds(),
                fetched_at=datetime.now(),
                data_sources_used=['error'],
                verification_notes=[f'Error: {str(e)}'],
                intelligence_quality_score=0,
                leadership_count=0,
                program_count=0,
                pages_scraped=0,
                has_990_baseline=False
            )
    
    def _create_verified_intelligence_result(
        self,
        profile_id: str,
        organization_name: str,
        ein: Optional[str],
        verification_result: Optional[VerificationResult],
        enhanced_data: Optional[EnhancedDataResult],
        start_time: datetime
    ) -> VerifiedIntelligenceResult:
        """Create consolidated verified intelligence result"""
        
        # Initialize with defaults
        verified_leadership = []
        verified_mission = None
        verified_programs = []
        verified_website = None
        overall_confidence = 0.0
        data_quality_score = 0.0
        source_attribution = {}
        data_sources_used = []
        verification_notes = []
        pages_scraped = 0
        has_990_baseline = False
        
        # Process verification result (primary data source)
        if verification_result:
            # Extract verified leadership with source attribution
            for leader in verification_result.verified_leadership:
                verified_leadership.append({
                    'name': leader.name,
                    'title': leader.title,
                    'source': leader.source,
                    'confidence_score': leader.confidence_score,
                    'verification_status': leader.verification_status,
                    'notes': leader.notes,
                    'compensation': (leader.tax_filing_match.get('compensation') 
                                   if leader.tax_filing_match else None)
                })
            
            verified_mission = verification_result.verified_mission
            verified_programs = verification_result.verified_programs
            verified_website = verification_result.verified_website
            overall_confidence = verification_result.verification_confidence
            data_quality_score = verification_result.data_quality_score
            source_attribution = verification_result.source_attribution.copy()
            verification_notes = verification_result.verification_notes.copy()
            
            # Track data sources used
            if verification_result.tax_baseline:
                data_sources_used.append('990_tax_filing')
                has_990_baseline = True
            if verification_result.url_resolution:
                data_sources_used.append('smart_url_resolution')
            if verification_result.web_scraping_data:
                data_sources_used.append('web_scraping')
                pages_scraped = verification_result.web_scraping_data.get('pages_scraped', 0)
        
        # Use priority resolver to consolidate data from multiple sources
        consolidated_data = self._consolidate_multi_source_data(
            verification_result, enhanced_data, overall_confidence
        )

        # Update consolidated results
        verified_leadership = consolidated_data['leadership']
        verified_mission = consolidated_data['mission']
        verified_website = consolidated_data['website']
        verified_programs = consolidated_data['programs']
        data_sources_used.extend(consolidated_data['sources_used'])
        source_attribution.update(consolidated_data['source_attribution'])
        self.stats['conflicts_resolved'] += consolidated_data['conflicts_resolved']
        self.stats['data_sources_merged'] += consolidated_data['sources_merged']
        
        # Calculate UI compatibility metrics
        intelligence_quality_score = int(data_quality_score * 100)
        leadership_count = len(verified_leadership)
        program_count = len(verified_programs)
        
        return VerifiedIntelligenceResult(
            profile_id=profile_id,
            organization_name=organization_name,
            ein=ein,
            verification_result=verification_result,
            enhanced_data=enhanced_data,
            verified_leadership=verified_leadership,
            verified_mission=verified_mission,
            verified_programs=verified_programs,
            verified_website=verified_website,
            overall_confidence=overall_confidence,
            data_quality_score=data_quality_score,
            source_attribution=source_attribution,
            processing_time=0.0,  # Will be set by caller
            fetched_at=datetime.now(),
            data_sources_used=data_sources_used,
            verification_notes=verification_notes,
            intelligence_quality_score=intelligence_quality_score,
            leadership_count=leadership_count,
            program_count=program_count,
            pages_scraped=pages_scraped,
            has_990_baseline=has_990_baseline
        )
    
    def _names_similar(self, name1: str, name2: str) -> bool:
        """Check if two names likely refer to the same person"""
        if not name1 or not name2:
            return False
        
        name1_clean = name1.lower().strip()
        name2_clean = name2.lower().strip()
        
        # Exact match
        if name1_clean == name2_clean:
            return True
        
        # Check if both first and last names match
        name1_parts = set(name1_clean.split())
        name2_parts = set(name2_clean.split())
        
        return len(name1_parts.intersection(name2_parts)) >= 2
    
    def _get_cached_result(self, profile_id: str) -> Optional[VerifiedIntelligenceResult]:
        """Get cached verified intelligence result if still valid"""
        if profile_id in self.verification_cache:
            cached_result = self.verification_cache[profile_id]
            cache_age = datetime.now() - cached_result.fetched_at
            
            if cache_age < timedelta(hours=self.cache_duration_hours):
                return cached_result
            else:
                # Remove expired cache entry
                del self.verification_cache[profile_id]
        
        return None
    
    def _cache_result(self, profile_id: str, result: VerifiedIntelligenceResult):
        """Cache verified intelligence result"""
        self.verification_cache[profile_id] = result
        
        # Clean old entries to prevent memory bloat
        if len(self.verification_cache) > 100:
            # Remove oldest entries
            oldest_entries = sorted(
                self.verification_cache.items(),
                key=lambda x: x[1].fetched_at
            )[:20]
            for old_profile_id, _ in oldest_entries:
                del self.verification_cache[old_profile_id]
    
    def _update_stats(self, result: VerifiedIntelligenceResult):
        """Update service statistics"""
        self.stats['total_requests'] += 1
        
        if result.overall_confidence > 0:
            self.stats['verification_success'] += 1
        
        if result.has_990_baseline:
            self.stats['tax_baseline_found'] += 1
        
        if result.pages_scraped > 0:
            self.stats['web_scraping_success'] += 1
        
        # Update running average confidence
        total_requests = self.stats['total_requests']
        current_avg = self.stats['average_confidence']
        self.stats['average_confidence'] = (
            (current_avg * (total_requests - 1) + result.overall_confidence) / total_requests
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        total_requests = self.stats['total_requests']
        
        return {
            **self.stats,
            'verification_success_rate': (self.stats['verification_success'] / max(total_requests, 1)) * 100,
            'tax_baseline_rate': (self.stats['tax_baseline_found'] / max(total_requests, 1)) * 100,
            'web_scraping_rate': (self.stats['web_scraping_success'] / max(total_requests, 1)) * 100,
            'cache_hit_rate': (self.stats['cache_hits'] / max(total_requests, 1)) * 100,
            'cache_size': len(self.verification_cache)
        }
    
    def clear_cache(self):
        """Clear the verification cache"""
        cache_size = len(self.verification_cache)
        self.verification_cache.clear()
        logger.info(f"Cleared verified intelligence cache ({cache_size} entries)")

    def _consolidate_multi_source_data(
        self,
        verification_result: Optional[VerificationResult],
        enhanced_data: Optional[EnhancedDataResult],
        base_confidence: float
    ) -> Dict[str, Any]:
        """
        Consolidate data from multiple sources using priority-based conflict resolution.

        Returns dict with consolidated data and resolution metadata.
        """
        # Collect all data sources for each field
        website_entries = []
        mission_entries = []
        leadership_entries = []
        program_entries = []

        sources_used = []
        source_attribution = {}
        conflicts_resolved = 0
        sources_merged = 0

        # Extract data from verification result
        if verification_result:
            if verification_result.tax_baseline:
                tax_data = verification_result.tax_baseline

                # Website from tax filing
                if tax_data.get('website'):
                    website_entries.append(DataSourceEntry(
                        value=tax_data['website'],
                        source=DataSource.TAX_FILING_990,
                        confidence_score=0.90,
                        notes=['From official 990 tax filing']
                    ))

                # Mission from tax filing
                if tax_data.get('mission'):
                    mission_entries.append(DataSourceEntry(
                        value=tax_data['mission'],
                        source=DataSource.TAX_FILING_990,
                        confidence_score=0.90,
                        notes=['From official 990 tax filing']
                    ))

                # Leadership from tax filing
                if tax_data.get('officers'):
                    for officer in tax_data['officers']:
                        leadership_entries.append(DataSourceEntry(
                            value={
                                'name': officer.get('name', 'Unknown'),
                                'title': officer.get('title', 'Officer'),
                                'source': 'tax_filing_990',
                                'confidence_score': 0.90,
                                'verification_status': 'tax_verified',
                                'notes': ['From official 990 tax filing'],
                                'compensation': officer.get('compensation')
                            },
                            source=DataSource.TAX_FILING_990,
                            confidence_score=0.90,
                            notes=['From official 990 tax filing']
                        ))

            # Data from web scraping
            if verification_result.web_scraping_data:
                scrape_data = verification_result.web_scraping_data

                # Website from web scraping (if different)
                if scrape_data.get('website_url'):
                    website_entries.append(DataSourceEntry(
                        value=scrape_data['website_url'],
                        source=DataSource.WEB_SCRAPING,
                        confidence_score=0.70,
                        notes=['From web scraping']
                    ))

                # Leadership from web scraping
                if scrape_data.get('leadership'):
                    for leader in scrape_data['leadership']:
                        leadership_entries.append(DataSourceEntry(
                            value={
                                'name': leader.get('name', 'Unknown'),
                                'title': leader.get('title', 'Staff'),
                                'source': 'web_scraping',
                                'confidence_score': 0.70,
                                'verification_status': 'web_found',
                                'notes': ['From web scraping'],
                                'bio': leader.get('bio')
                            },
                            source=DataSource.WEB_SCRAPING,
                            confidence_score=0.70,
                            notes=['From web scraping']
                        ))

                # Programs from web scraping
                if scrape_data.get('programs'):
                    program_entries.append(DataSourceEntry(
                        value=scrape_data['programs'],
                        source=DataSource.WEB_SCRAPING,
                        confidence_score=0.70,
                        notes=['From web scraping']
                    ))

        # Extract data from enhanced data (legacy support)
        if enhanced_data:
            if enhanced_data.board_data and enhanced_data.board_data.get('officers'):
                for officer in enhanced_data.board_data['officers']:
                    leadership_entries.append(DataSourceEntry(
                        value={
                            'name': officer.get('name', 'Unknown'),
                            'title': officer.get('title', 'Officer'),
                            'source': 'enhanced_990_supplemental',
                            'confidence_score': 0.65,
                            'verification_status': 'supplemental',
                            'notes': ['From enhanced 990 analysis'],
                            'compensation': officer.get('compensation')
                        },
                        source=DataSource.ENHANCED_990,
                        confidence_score=0.65,
                        notes=['From enhanced 990 analysis']
                    ))

        # Resolve conflicts using priority resolver
        consolidated_website = None
        consolidated_mission = None

        if website_entries:
            if len(website_entries) > 1:
                conflicts_resolved += 1
            website_result, website_meta = self.priority_resolver.resolve_field_conflict(
                'website', website_entries
            )
            consolidated_website = website_result.value
            source_attribution['website'] = {
                'source': website_result.source.value,
                'confidence': website_result.confidence_score,
                'resolution': website_meta
            }
            sources_used.append(website_result.source.value)

        if mission_entries:
            if len(mission_entries) > 1:
                conflicts_resolved += 1
            mission_result, mission_meta = self.priority_resolver.resolve_field_conflict(
                'mission', mission_entries
            )
            consolidated_mission = mission_result.value
            source_attribution['mission'] = {
                'source': mission_result.source.value,
                'confidence': mission_result.confidence_score,
                'resolution': mission_meta
            }
            sources_used.append(mission_result.source.value)

        # For leadership, merge unique entries (no conflicts, just combine)
        consolidated_leadership = []
        if leadership_entries:
            # Group by name to avoid duplicates
            leadership_by_name = {}
            for entry in leadership_entries:
                leader_data = entry.value
                name = leader_data['name'].lower().strip()

                if name in leadership_by_name:
                    # Choose higher priority source
                    existing_entry = leadership_by_name[name]
                    if self.priority_resolver.SOURCE_PRIORITY[entry.source] < \
                       self.priority_resolver.SOURCE_PRIORITY[existing_entry.source]:
                        leadership_by_name[name] = entry
                        conflicts_resolved += 1
                else:
                    leadership_by_name[name] = entry

            consolidated_leadership = [entry.value for entry in leadership_by_name.values()]
            sources_merged += len(set(entry.source.value for entry in leadership_entries))

        # For programs, merge lists
        consolidated_programs = []
        if program_entries:
            programs_result, programs_meta = self.priority_resolver.resolve_list_conflict(
                'programs', program_entries
            )
            consolidated_programs = programs_result
            source_attribution['programs'] = programs_meta
            sources_merged += len(program_entries)

        return {
            'website': consolidated_website,
            'mission': consolidated_mission,
            'leadership': consolidated_leadership,
            'programs': consolidated_programs,
            'sources_used': list(set(sources_used)),  # Remove duplicates
            'source_attribution': source_attribution,
            'conflicts_resolved': conflicts_resolved,
            'sources_merged': sources_merged
        }


def get_verified_intelligence_service() -> VerifiedIntelligenceService:
    """Get singleton instance of verified intelligence service"""
    if not hasattr(get_verified_intelligence_service, '_instance'):
        get_verified_intelligence_service._instance = VerifiedIntelligenceService()
    return get_verified_intelligence_service._instance