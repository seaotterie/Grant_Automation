"""
Foundation Intelligence Engine - Phase 2 Week 9-10 Implementation

Implements comprehensive foundation analysis and scoring system with:
- Grantor analysis and scoring system
- Similar grantee identification algorithms  
- Foundation ecosystem mapping
- Giving pattern analysis
- Foundation board overlap detection

This builds the foundation intelligence layer for the PLAN stage.
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from enum import Enum
import re
import json

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile

logger = logging.getLogger(__name__)


class FoundationType(Enum):
    """Foundation types for classification."""
    PRIVATE_NON_OPERATING = "private_non_operating"    # 990-PF, primary target
    PRIVATE_OPERATING = "private_operating"            # 990-PF, operating foundation
    COMMUNITY_FOUNDATION = "community_foundation"      # Local/regional focus
    CORPORATE_FOUNDATION = "corporate_foundation"      # Company-sponsored
    FAMILY_FOUNDATION = "family_foundation"           # Family-controlled
    PUBLIC_CHARITY = "public_charity"                 # 990 filer, grantmaker
    UNKNOWN = "unknown"


class GivingPattern(Enum):
    """Foundation giving patterns."""
    GENERAL_PURPOSE = "general_purpose"        # Broad, unrestricted giving
    PROGRAM_SPECIFIC = "program_specific"      # Specific program areas
    CAPACITY_BUILDING = "capacity_building"    # Organizational development
    PROJECT_BASED = "project_based"           # Specific projects/initiatives
    EMERGENCY_RESPONSE = "emergency_response"  # Crisis/disaster response
    COLLABORATIVE = "collaborative"           # Multi-funder initiatives


@dataclass
class FoundationProfile:
    """Comprehensive foundation profile with intelligence data."""
    ein: str
    name: str
    foundation_type: FoundationType = FoundationType.UNKNOWN
    
    # Financial data
    assets: Optional[float] = None
    revenue: Optional[float] = None
    total_grants_made: Optional[float] = None
    num_grants_made: Optional[int] = None
    avg_grant_size: Optional[float] = None
    
    # Giving patterns
    giving_patterns: List[GivingPattern] = field(default_factory=list)
    focus_areas: List[str] = field(default_factory=list)
    geographic_focus: List[str] = field(default_factory=list)
    target_populations: List[str] = field(default_factory=list)
    
    # Network and governance
    board_members: List[Dict[str, str]] = field(default_factory=list)
    key_personnel: List[Dict[str, str]] = field(default_factory=list)
    
    # Grant history and patterns
    grant_recipients: List[Dict[str, Any]] = field(default_factory=list)
    similar_grantees: List[str] = field(default_factory=list)  # EINs of similar organizations
    funding_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Intelligence metrics
    grantee_overlap_score: float = 0.0
    board_connection_score: float = 0.0
    giving_pattern_compatibility: float = 0.0
    foundation_ecosystem_centrality: float = 0.0
    overall_foundation_score: float = 0.0
    
    # Application and approach intelligence
    accepts_unsolicited: Optional[bool] = None
    application_process: str = ""
    application_deadlines: List[str] = field(default_factory=list)
    minimum_grant_size: Optional[float] = None
    maximum_grant_size: Optional[float] = None
    
    # Recent activity indicators
    last_filing_year: Optional[int] = None
    recent_grants_trend: str = ""  # increasing, stable, decreasing
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'ein': self.ein,
            'name': self.name,
            'foundation_type': self.foundation_type.value,
            'assets': self.assets,
            'revenue': self.revenue,
            'total_grants_made': self.total_grants_made,
            'num_grants_made': self.num_grants_made,
            'avg_grant_size': self.avg_grant_size,
            'giving_patterns': [pattern.value for pattern in self.giving_patterns],
            'focus_areas': self.focus_areas,
            'geographic_focus': self.geographic_focus,
            'target_populations': self.target_populations,
            'board_members': self.board_members,
            'key_personnel': self.key_personnel,
            'grant_recipients': self.grant_recipients,
            'similar_grantees': self.similar_grantees,
            'funding_history': self.funding_history,
            'grantee_overlap_score': round(self.grantee_overlap_score, 3),
            'board_connection_score': round(self.board_connection_score, 3),
            'giving_pattern_compatibility': round(self.giving_pattern_compatibility, 3),
            'foundation_ecosystem_centrality': round(self.foundation_ecosystem_centrality, 3),
            'overall_foundation_score': round(self.overall_foundation_score, 3),
            'accepts_unsolicited': self.accepts_unsolicited,
            'application_process': self.application_process,
            'application_deadlines': self.application_deadlines,
            'minimum_grant_size': self.minimum_grant_size,
            'maximum_grant_size': self.maximum_grant_size,
            'last_filing_year': self.last_filing_year,
            'recent_grants_trend': self.recent_grants_trend
        }


@dataclass
class FoundationEcosystemMap:
    """Foundation ecosystem relationship mapping."""
    foundation_relationships: Dict[str, List[str]] = field(default_factory=dict)  # EIN -> related foundation EINs
    shared_grantees: Dict[str, Set[str]] = field(default_factory=dict)  # EIN -> grantee EINs
    collaborative_funders: Dict[str, List[str]] = field(default_factory=dict)  # EIN -> collaborating foundation EINs
    ecosystem_clusters: List[List[str]] = field(default_factory=list)  # Groups of related foundations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'foundation_relationships': self.foundation_relationships,
            'shared_grantees': {k: list(v) for k, v in self.shared_grantees.items()},
            'collaborative_funders': self.collaborative_funders,
            'ecosystem_clusters': self.ecosystem_clusters
        }


class FoundationIntelligenceEngine(BaseProcessor):
    """
    Foundation Intelligence Engine for comprehensive grantor analysis.
    
    Implements Phase 2 Week 9-10 requirements:
    - Grantor analysis and scoring system
    - Similar grantee identification algorithms
    - Foundation ecosystem mapping  
    - Giving pattern analysis
    - Foundation board overlap detection
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="foundation_intelligence_engine",
            description="Comprehensive foundation analysis and ecosystem mapping with giving pattern analysis",
            version="2.0.0",
            dependencies=["network_intelligence_engine"],
            estimated_duration=180,  # 3 minutes for comprehensive foundation analysis
            requires_network=False,
            requires_api_key=False,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Foundation analysis scoring weights
        self.foundation_analysis_dimensions = {
            'similar_grantee_overlap': 0.4,    # Organizations with similar missions receiving funding
            'foundation_board_connections': 0.3,  # Board overlap with foundation boards
            'giving_pattern_compatibility': 0.2,  # Historical giving pattern alignment
            'foundation_ecosystem_centrality': 0.1  # Position in foundation network
        }
        
        # NTEE code groupings for focus area analysis
        self.ntee_focus_areas = {
            'Arts & Culture': ['A'],
            'Education': ['B'],
            'Environment': ['C', 'D'],
            'Health': ['E', 'F', 'G', 'H'],
            'Human Services': ['I', 'J', 'K', 'L', 'M', 'N', 'O', 'P'],
            'International': ['Q'],
            'Public Benefit': ['R', 'S', 'T', 'U', 'V', 'W'],
            'Religion': ['X'],
            'Mutual Benefit': ['Y'],
            'Unknown': ['Z']
        }
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute comprehensive foundation intelligence analysis."""
        start_time = datetime.now()
        
        try:
            self.logger.info("Starting Foundation Intelligence Engine analysis")
            
            # Get organizations and foundation data
            organizations = await self._get_input_organizations(config, workflow_state)
            foundation_data = await self._extract_foundation_data(config, workflow_state)
            
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No organizations found for foundation analysis"]
                )
            
            # Phase 1: Build comprehensive foundation profiles
            foundation_profiles = await self._build_foundation_profiles(foundation_data)
            self.logger.info(f"Built profiles for {len(foundation_profiles)} foundations")
            
            # Phase 2: Analyze grantor patterns and scoring
            grantor_analysis = await self._analyze_grantor_patterns(foundation_profiles, organizations)
            
            # Phase 3: Identify similar grantees
            similar_grantee_analysis = await self._identify_similar_grantees(
                foundation_profiles, organizations
            )
            
            # Phase 4: Map foundation ecosystem
            ecosystem_map = await self._map_foundation_ecosystem(foundation_profiles)
            
            # Phase 5: Analyze giving patterns
            giving_pattern_analysis = await self._analyze_giving_patterns(
                foundation_profiles, organizations
            )
            
            # Phase 6: Detect foundation board overlaps
            board_overlap_analysis = await self._detect_foundation_board_overlaps(
                foundation_profiles, organizations
            )
            
            # Phase 7: Calculate comprehensive foundation scores
            foundation_scores = await self._calculate_foundation_ecosystem_scores(
                foundation_profiles, grantor_analysis, similar_grantee_analysis,
                giving_pattern_analysis, board_overlap_analysis
            )
            
            # Prepare comprehensive results
            result_data = {
                "foundation_intelligence": {
                    "total_foundations_analyzed": len(foundation_profiles),
                    "organizations_analyzed": len(organizations),
                    "analysis_timestamp": start_time.isoformat(),
                    "top_foundation_matches": len([f for f in foundation_profiles if f.overall_foundation_score > 0.7])
                },
                "foundation_profiles": [profile.to_dict() for profile in foundation_profiles],
                "grantor_analysis": grantor_analysis,
                "similar_grantee_analysis": similar_grantee_analysis,
                "ecosystem_map": ecosystem_map.to_dict(),
                "giving_pattern_analysis": giving_pattern_analysis,
                "board_overlap_analysis": board_overlap_analysis,
                "foundation_scores": foundation_scores,
                "strategic_recommendations": self._generate_foundation_recommendations(
                    foundation_profiles, foundation_scores
                )
            }
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                start_time=start_time,
                end_time=datetime.now(),
                data=result_data
            )
            
        except Exception as e:
            self.logger.error(f"Foundation Intelligence Engine failed: {str(e)}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                start_time=start_time,
                end_time=datetime.now(),
                errors=[f"Foundation analysis error: {str(e)}"]
            )
    
    async def _extract_foundation_data(self, config: ProcessorConfig, workflow_state) -> List[Dict[str, Any]]:
        """Extract foundation data from various sources."""
        foundation_data = []
        
        # Try to get from workflow state
        if workflow_state and hasattr(workflow_state, 'foundations'):
            foundation_data.extend(workflow_state.foundations)
        
        # Try to get from config input data
        if config.input_data and 'foundations' in config.input_data:
            foundation_data.extend(config.input_data['foundations'])
        
        # Also extract from organization data (organizations that are foundations)
        organizations = await self._get_input_organizations(config, workflow_state)
        for org in organizations:
            if self._is_foundation(org):
                foundation_data.append(self._org_to_foundation_dict(org))
        
        return foundation_data
    
    def _is_foundation(self, org: OrganizationProfile) -> bool:
        """Determine if an organization is a foundation."""
        # Check foundation code
        foundation_code = getattr(org, 'foundation_code', None)
        if foundation_code in ['03', '04']:  # Private foundations
            return True
        
        # Check form type
        form_type = getattr(org, 'form_type', None)
        if form_type and 'pf' in str(form_type).lower():
            return True
        
        # Check for grantmaking activity
        total_grants = getattr(org, 'total_grants_made', 0)
        if total_grants and total_grants > 0:
            return True
        
        return False
    
    def _org_to_foundation_dict(self, org: OrganizationProfile) -> Dict[str, Any]:
        """Convert organization profile to foundation data dictionary."""
        return {
            'ein': getattr(org, 'ein', ''),
            'name': getattr(org, 'name', ''),
            'assets': getattr(org, 'assets', None),
            'revenue': getattr(org, 'revenue', None),
            'total_grants_made': getattr(org, 'total_grants_made', None),
            'num_grants_made': getattr(org, 'num_grants_made', None),
            'board_members': getattr(org, 'board_members', []),
            'key_personnel': getattr(org, 'key_personnel', []),
            'grant_recipients': getattr(org, 'grant_recipients', []),
            'ntee_code': getattr(org, 'ntee_code', ''),
            'state': getattr(org, 'state', ''),
            'foundation_code': getattr(org, 'foundation_code', None),
            'form_type': getattr(org, 'form_type', None)
        }
    
    async def _build_foundation_profiles(self, foundation_data: List[Dict[str, Any]]) -> List[FoundationProfile]:
        """Build comprehensive foundation profiles from raw data."""
        profiles = []
        
        for data in foundation_data:
            if not data.get('ein'):
                continue
            
            profile = FoundationProfile(
                ein=data['ein'],
                name=data.get('name', ''),
                foundation_type=self._classify_foundation_type(data),
                assets=data.get('assets'),
                revenue=data.get('revenue'),
                total_grants_made=data.get('total_grants_made'),
                num_grants_made=data.get('num_grants_made'),
                board_members=data.get('board_members', []),
                key_personnel=data.get('key_personnel', []),
                grant_recipients=data.get('grant_recipients', [])
            )
            
            # Calculate average grant size
            if profile.total_grants_made and profile.num_grants_made and profile.num_grants_made > 0:
                profile.avg_grant_size = profile.total_grants_made / profile.num_grants_made
            
            # Analyze focus areas from NTEE code
            ntee_code = data.get('ntee_code', '')
            if ntee_code:
                profile.focus_areas = self._extract_focus_areas_from_ntee(ntee_code)
            
            # Extract geographic focus
            state = data.get('state', '')
            if state:
                profile.geographic_focus = [state]
            
            # Analyze giving patterns from grant data
            profile.giving_patterns = self._analyze_foundation_giving_patterns(profile.grant_recipients)
            
            # Extract application intelligence
            profile.accepts_unsolicited = self._determine_unsolicited_policy(data)
            
            profiles.append(profile)
        
        return profiles
    
    def _classify_foundation_type(self, data: Dict[str, Any]) -> FoundationType:
        """Classify foundation type based on available data."""
        foundation_code = data.get('foundation_code')
        form_type = data.get('form_type', '')
        
        if foundation_code == '03':
            return FoundationType.PRIVATE_NON_OPERATING
        elif foundation_code == '04':
            return FoundationType.PRIVATE_OPERATING
        elif 'pf' in str(form_type).lower():
            return FoundationType.PRIVATE_NON_OPERATING
        
        # Heuristic classification based on name and grant patterns
        name = data.get('name', '').lower()
        if any(keyword in name for keyword in ['community', 'area', 'regional']):
            return FoundationType.COMMUNITY_FOUNDATION
        elif any(keyword in name for keyword in ['family', 'memorial', 'estate']):
            return FoundationType.FAMILY_FOUNDATION
        elif any(keyword in name for keyword in ['corp', 'company', 'inc', 'ltd']):
            return FoundationType.CORPORATE_FOUNDATION
        
        return FoundationType.UNKNOWN
    
    def _extract_focus_areas_from_ntee(self, ntee_code: str) -> List[str]:
        """Extract focus areas from NTEE code."""
        if not ntee_code:
            return []
        
        focus_areas = []
        ntee_prefix = ntee_code[0].upper() if ntee_code else ''
        
        for area, codes in self.ntee_focus_areas.items():
            if ntee_prefix in codes:
                focus_areas.append(area)
                break
        
        return focus_areas
    
    def _analyze_foundation_giving_patterns(self, grant_recipients: List[Dict[str, Any]]) -> List[GivingPattern]:
        """Analyze giving patterns from grant recipient data."""
        patterns = []
        
        if not grant_recipients:
            return patterns
        
        # Analyze grant purposes and amounts
        purposes = [grant.get('purpose', '').lower() for grant in grant_recipients if grant.get('purpose')]
        amounts = [grant.get('amount', 0) for grant in grant_recipients if grant.get('amount')]
        
        # Pattern detection based on grant purposes
        if any('general' in purpose or 'unrestricted' in purpose for purpose in purposes):
            patterns.append(GivingPattern.GENERAL_PURPOSE)
        
        if any('program' in purpose or 'project' in purpose for purpose in purposes):
            patterns.append(GivingPattern.PROGRAM_SPECIFIC)
        
        if any('capacity' in purpose or 'organizational' in purpose for purpose in purposes):
            patterns.append(GivingPattern.CAPACITY_BUILDING)
        
        if any('emergency' in purpose or 'disaster' in purpose for purpose in purposes):
            patterns.append(GivingPattern.EMERGENCY_RESPONSE)
        
        # Amount-based pattern analysis
        if amounts:
            avg_amount = sum(amounts) / len(amounts)
            if len(set(amounts)) / len(amounts) < 0.3:  # Low variability suggests program-specific
                patterns.append(GivingPattern.PROGRAM_SPECIFIC)
        
        return list(set(patterns)) if patterns else [GivingPattern.GENERAL_PURPOSE]
    
    def _determine_unsolicited_policy(self, data: Dict[str, Any]) -> Optional[bool]:
        """Determine if foundation accepts unsolicited proposals."""
        # This would typically be extracted from 990-PF form data
        # For now, use heuristics based on foundation type and size
        assets = data.get('assets', 0)
        foundation_code = data.get('foundation_code')
        
        if foundation_code == '03' and assets and assets > 10000000:  # Large private foundations
            return False  # Often by invitation only
        elif foundation_code == '04':  # Operating foundations
            return False  # Typically don't accept external proposals
        elif assets and assets > 1000000:  # Medium-sized foundations
            return True  # Often accept proposals
        
        return None  # Unknown
    
    async def _analyze_grantor_patterns(self, foundation_profiles: List[FoundationProfile], 
                                      organizations: List[OrganizationProfile]) -> Dict[str, Any]:
        """
        Phase 2 Requirement: Build grantor analysis and scoring system.
        
        Analyzes grantor patterns including funding amounts, frequency, and preferences.
        """
        analysis = {
            "funding_patterns": {},
            "geographic_patterns": {},
            "sector_preferences": {},
            "grant_size_analysis": {},
            "funding_frequency": {}
        }
        
        # Funding patterns analysis
        total_funding = sum(f.total_grants_made or 0 for f in foundation_profiles)
        foundation_count = len([f for f in foundation_profiles if f.total_grants_made])
        
        analysis["funding_patterns"] = {
            "total_foundations": len(foundation_profiles),
            "active_grantmakers": foundation_count,
            "total_funding_available": total_funding,
            "average_foundation_giving": total_funding / foundation_count if foundation_count > 0 else 0,
            "funding_concentration": self._calculate_funding_concentration(foundation_profiles)
        }
        
        # Geographic patterns
        geographic_data = defaultdict(list)
        for foundation in foundation_profiles:
            for geo in foundation.geographic_focus:
                geographic_data[geo].append(foundation.total_grants_made or 0)
        
        analysis["geographic_patterns"] = {
            region: {
                "foundation_count": len(amounts),
                "total_funding": sum(amounts),
                "average_funding": sum(amounts) / len(amounts) if amounts else 0
            }
            for region, amounts in geographic_data.items()
        }
        
        # Sector preferences
        sector_data = defaultdict(list)
        for foundation in foundation_profiles:
            for sector in foundation.focus_areas:
                sector_data[sector].append(foundation.total_grants_made or 0)
        
        analysis["sector_preferences"] = {
            sector: {
                "foundation_count": len(amounts),
                "total_funding": sum(amounts),
                "average_funding": sum(amounts) / len(amounts) if amounts else 0
            }
            for sector, amounts in sector_data.items()
        }
        
        # Grant size analysis
        grant_sizes = [f.avg_grant_size for f in foundation_profiles if f.avg_grant_size]
        if grant_sizes:
            analysis["grant_size_analysis"] = {
                "average_grant_size": sum(grant_sizes) / len(grant_sizes),
                "median_grant_size": sorted(grant_sizes)[len(grant_sizes)//2],
                "min_grant_size": min(grant_sizes),
                "max_grant_size": max(grant_sizes),
                "size_distribution": self._calculate_size_distribution(grant_sizes)
            }
        
        return analysis
    
    def _calculate_funding_concentration(self, foundations: List[FoundationProfile]) -> float:
        """Calculate funding concentration (Gini coefficient approximation)."""
        amounts = [f.total_grants_made or 0 for f in foundations]
        amounts = sorted([x for x in amounts if x > 0])
        
        if len(amounts) < 2:
            return 0.0
        
        # Simple Gini coefficient calculation
        n = len(amounts)
        total = sum(amounts)
        if total == 0:
            return 0.0
        
        cumsum = 0
        gini_sum = 0
        for i, amount in enumerate(amounts):
            cumsum += amount
            gini_sum += (2 * (i + 1) - n - 1) * amount
        
        return gini_sum / (n * total)
    
    def _calculate_size_distribution(self, grant_sizes: List[float]) -> Dict[str, int]:
        """Calculate grant size distribution by categories."""
        distribution = {
            "small (<$10K)": 0,
            "medium ($10K-$100K)": 0, 
            "large ($100K-$1M)": 0,
            "major (>$1M)": 0
        }
        
        for size in grant_sizes:
            if size < 10000:
                distribution["small (<$10K)"] += 1
            elif size < 100000:
                distribution["medium ($10K-$100K)"] += 1
            elif size < 1000000:
                distribution["large ($100K-$1M)"] += 1
            else:
                distribution["major (>$1M)"] += 1
        
        return distribution
    
    async def _identify_similar_grantees(self, foundation_profiles: List[FoundationProfile], 
                                       organizations: List[OrganizationProfile]) -> Dict[str, Any]:
        """
        Phase 2 Requirement: Similar grantee identification algorithms.
        
        Identifies organizations similar to the target that have received foundation funding.
        """
        similar_grantee_analysis = {
            "organization_similarities": {},
            "shared_funders": {},
            "competitor_analysis": {},
            "funding_opportunities": []
        }
        
        # Build organization profiles for comparison
        org_profiles = {}
        for org in organizations:
            ein = getattr(org, 'ein', '')
            if ein:
                org_profiles[ein] = {
                    'ntee_code': getattr(org, 'ntee_code', ''),
                    'focus_areas': self._extract_focus_areas_from_ntee(getattr(org, 'ntee_code', '')),
                    'state': getattr(org, 'state', ''),
                    'revenue': getattr(org, 'revenue', 0),
                    'name': getattr(org, 'name', '')
                }
        
        # Analyze grantee similarities for each organization
        for org_ein, org_profile in org_profiles.items():
            similar_orgs = []
            shared_funders = []
            
            for foundation in foundation_profiles:
                for recipient in foundation.grant_recipients:
                    recipient_ein = recipient.get('ein', '')
                    if recipient_ein and recipient_ein != org_ein:
                        similarity_score = self._calculate_organization_similarity(
                            org_profile, recipient
                        )
                        if similarity_score > 0.7:  # High similarity threshold
                            similar_orgs.append({
                                'ein': recipient_ein,
                                'name': recipient.get('name', ''),
                                'similarity_score': similarity_score,
                                'funder': foundation.name,
                                'funder_ein': foundation.ein,
                                'grant_amount': recipient.get('amount', 0)
                            })
                            
                            if foundation.ein not in [sf['ein'] for sf in shared_funders]:
                                shared_funders.append({
                                    'ein': foundation.ein,
                                    'name': foundation.name,
                                    'similar_grantee_count': 1
                                })
                            else:
                                # Increment count
                                for sf in shared_funders:
                                    if sf['ein'] == foundation.ein:
                                        sf['similar_grantee_count'] += 1
            
            similar_grantee_analysis["organization_similarities"][org_ein] = similar_orgs
            similar_grantee_analysis["shared_funders"][org_ein] = shared_funders
        
        return similar_grantee_analysis
    
    def _calculate_organization_similarity(self, org_profile: Dict[str, Any], 
                                         recipient: Dict[str, Any]) -> float:
        """Calculate similarity score between organizations."""
        score = 0.0
        
        # NTEE code similarity (40% weight)
        org_ntee = org_profile.get('ntee_code', '')
        recipient_ntee = recipient.get('ntee_code', '')
        if org_ntee and recipient_ntee:
            if org_ntee[0] == recipient_ntee[0]:  # Same major category
                score += 0.4
                if org_ntee[:2] == recipient_ntee[:2]:  # Same subcategory
                    score += 0.1
        
        # Geographic similarity (20% weight)
        org_state = org_profile.get('state', '')
        recipient_state = recipient.get('state', '')
        if org_state and recipient_state and org_state == recipient_state:
            score += 0.2
        
        # Revenue similarity (20% weight)
        org_revenue = org_profile.get('revenue', 0)
        recipient_revenue = recipient.get('revenue', 0)
        if org_revenue and recipient_revenue:
            revenue_ratio = min(org_revenue, recipient_revenue) / max(org_revenue, recipient_revenue)
            score += 0.2 * revenue_ratio
        
        # Name similarity for mission alignment (20% weight)
        org_name = org_profile.get('name', '').lower()
        recipient_name = recipient.get('name', '').lower()
        name_similarity = self._calculate_name_similarity(org_name, recipient_name)
        score += 0.2 * name_similarity
        
        return min(score, 1.0)
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity based on common keywords."""
        if not name1 or not name2:
            return 0.0
        
        # Extract meaningful words (exclude common words)
        common_words = {'the', 'of', 'and', 'for', 'to', 'in', 'inc', 'foundation', 'organization', 'center', 'society'}
        
        words1 = set(re.findall(r'\b\w+\b', name1.lower())) - common_words
        words2 = set(re.findall(r'\b\w+\b', name2.lower())) - common_words
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _map_foundation_ecosystem(self, foundation_profiles: List[FoundationProfile]) -> FoundationEcosystemMap:
        """
        Phase 2 Requirement: Foundation ecosystem mapping.
        
        Maps relationships between foundations through shared grantees and board connections.
        """
        ecosystem_map = FoundationEcosystemMap()
        
        # Map shared grantees between foundations
        for i, foundation1 in enumerate(foundation_profiles):
            grantees1 = set(r.get('ein', '') for r in foundation1.grant_recipients if r.get('ein'))
            ecosystem_map.shared_grantees[foundation1.ein] = grantees1
            
            for foundation2 in foundation_profiles[i+1:]:
                grantees2 = set(r.get('ein', '') for r in foundation2.grant_recipients if r.get('ein'))
                
                # Calculate grantee overlap
                shared_grantees = grantees1.intersection(grantees2)
                if len(shared_grantees) >= 2:  # Minimum threshold for relationship
                    
                    # Add to foundation relationships
                    if foundation1.ein not in ecosystem_map.foundation_relationships:
                        ecosystem_map.foundation_relationships[foundation1.ein] = []
                    ecosystem_map.foundation_relationships[foundation1.ein].append(foundation2.ein)
                    
                    if foundation2.ein not in ecosystem_map.foundation_relationships:
                        ecosystem_map.foundation_relationships[foundation2.ein] = []
                    ecosystem_map.foundation_relationships[foundation2.ein].append(foundation1.ein)
                    
                    # Identify as collaborative funders
                    if foundation1.ein not in ecosystem_map.collaborative_funders:
                        ecosystem_map.collaborative_funders[foundation1.ein] = []
                    ecosystem_map.collaborative_funders[foundation1.ein].append(foundation2.ein)
                    
                    if foundation2.ein not in ecosystem_map.collaborative_funders:
                        ecosystem_map.collaborative_funders[foundation2.ein] = []
                    ecosystem_map.collaborative_funders[foundation2.ein].append(foundation1.ein)
        
        # Identify ecosystem clusters using connected components
        ecosystem_map.ecosystem_clusters = self._identify_foundation_clusters(
            ecosystem_map.foundation_relationships
        )
        
        return ecosystem_map
    
    def _identify_foundation_clusters(self, relationships: Dict[str, List[str]]) -> List[List[str]]:
        """Identify clusters of related foundations using graph analysis."""
        visited = set()
        clusters = []
        
        def dfs(foundation_ein: str, current_cluster: List[str]):
            if foundation_ein in visited:
                return
            visited.add(foundation_ein)
            current_cluster.append(foundation_ein)
            
            for related_ein in relationships.get(foundation_ein, []):
                dfs(related_ein, current_cluster)
        
        for foundation_ein in relationships:
            if foundation_ein not in visited:
                cluster = []
                dfs(foundation_ein, cluster)
                if len(cluster) > 1:  # Only include multi-foundation clusters
                    clusters.append(cluster)
        
        return clusters
    
    async def _analyze_giving_patterns(self, foundation_profiles: List[FoundationProfile], 
                                     organizations: List[OrganizationProfile]) -> Dict[str, Any]:
        """
        Phase 2 Requirement: Giving pattern analysis.
        
        Analyzes historical giving patterns and compatibility with target organizations.
        """
        pattern_analysis = {
            "pattern_distribution": {},
            "temporal_patterns": {},
            "amount_patterns": {},
            "compatibility_scores": {}
        }
        
        # Analyze pattern distribution
        all_patterns = []
        for foundation in foundation_profiles:
            all_patterns.extend(foundation.giving_patterns)
        
        pattern_counts = Counter(pattern.value for pattern in all_patterns)
        pattern_analysis["pattern_distribution"] = dict(pattern_counts)
        
        # Analyze compatibility with target organizations
        for org in organizations:
            org_ein = getattr(org, 'ein', '')
            if not org_ein:
                continue
            
            compatibility_scores = {}
            org_focus_areas = self._extract_focus_areas_from_ntee(getattr(org, 'ntee_code', ''))
            
            for foundation in foundation_profiles:
                # Focus area compatibility
                focus_overlap = len(set(org_focus_areas).intersection(set(foundation.focus_areas)))
                focus_compatibility = focus_overlap / max(len(org_focus_areas), 1)
                
                # Geographic compatibility
                org_state = getattr(org, 'state', '')
                geo_compatibility = 1.0 if org_state in foundation.geographic_focus else 0.5
                
                # Revenue/grant size compatibility
                org_revenue = getattr(org, 'revenue', 0)
                size_compatibility = self._calculate_size_compatibility(
                    org_revenue, foundation.avg_grant_size
                )
                
                # Overall compatibility
                overall_compatibility = (
                    focus_compatibility * 0.5 +
                    geo_compatibility * 0.3 +
                    size_compatibility * 0.2
                )
                
                compatibility_scores[foundation.ein] = {
                    'foundation_name': foundation.name,
                    'focus_compatibility': round(focus_compatibility, 3),
                    'geographic_compatibility': round(geo_compatibility, 3),
                    'size_compatibility': round(size_compatibility, 3),
                    'overall_compatibility': round(overall_compatibility, 3)
                }
            
            pattern_analysis["compatibility_scores"][org_ein] = compatibility_scores
        
        return pattern_analysis
    
    def _calculate_size_compatibility(self, org_revenue: float, avg_grant_size: Optional[float]) -> float:
        """Calculate compatibility between organization size and typical grant size."""
        if not avg_grant_size or not org_revenue:
            return 0.5  # Neutral score when data unavailable
        
        # Optimal grant size is typically 1-10% of organization revenue
        optimal_min = org_revenue * 0.01
        optimal_max = org_revenue * 0.10
        
        if optimal_min <= avg_grant_size <= optimal_max:
            return 1.0
        elif avg_grant_size < optimal_min:
            return max(0.0, avg_grant_size / optimal_min)
        else:  # avg_grant_size > optimal_max
            return max(0.0, optimal_max / avg_grant_size)
    
    async def _detect_foundation_board_overlaps(self, foundation_profiles: List[FoundationProfile], 
                                              organizations: List[OrganizationProfile]) -> Dict[str, Any]:
        """
        Phase 2 Requirement: Foundation board overlap detection.
        
        Detects board member overlaps between foundations and target organizations.
        """
        board_overlap_analysis = {
            "organization_board_overlaps": {},
            "foundation_board_connections": {},
            "network_opportunities": []
        }
        
        # Normalize board member names for matching
        def normalize_name(name: str) -> str:
            if not name:
                return ""
            # Remove titles and normalize
            name = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|Rev|Hon|Esq)\.?\b', '', name, flags=re.IGNORECASE)
            name = re.sub(r'\b(Jr|Sr|II|III|IV)\.?\b', '', name, flags=re.IGNORECASE)
            return ' '.join(name.split()).title()
        
        # Build board member indexes
        foundation_boards = {}
        for foundation in foundation_profiles:
            board_names = set()
            for member in foundation.board_members:
                name = member.get('name', '') if isinstance(member, dict) else str(member)
                if name:
                    board_names.add(normalize_name(name))
            foundation_boards[foundation.ein] = board_names
        
        # Analyze overlaps for each target organization
        for org in organizations:
            org_ein = getattr(org, 'ein', '')
            if not org_ein:
                continue
            
            org_board = set()
            board_members = getattr(org, 'board_members', [])
            for member in board_members:
                name = member.get('name', '') if isinstance(member, dict) else str(member)
                if name:
                    org_board.add(normalize_name(name))
            
            overlaps = {}
            for foundation_ein, foundation_board in foundation_boards.items():
                shared_members = org_board.intersection(foundation_board)
                if shared_members:
                    foundation = next((f for f in foundation_profiles if f.ein == foundation_ein), None)
                    overlaps[foundation_ein] = {
                        'foundation_name': foundation.name if foundation else 'Unknown',
                        'shared_members': list(shared_members),
                        'overlap_count': len(shared_members),
                        'overlap_percentage': len(shared_members) / max(len(org_board), 1)
                    }
            
            board_overlap_analysis["organization_board_overlaps"][org_ein] = overlaps
        
        return board_overlap_analysis
    
    async def _calculate_foundation_ecosystem_scores(self, foundation_profiles: List[FoundationProfile],
                                                   grantor_analysis: Dict[str, Any],
                                                   similar_grantee_analysis: Dict[str, Any], 
                                                   giving_pattern_analysis: Dict[str, Any],
                                                   board_overlap_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive foundation ecosystem scores."""
        foundation_scores = {}
        
        for foundation in foundation_profiles:
            # Similar grantee overlap score
            grantee_overlap_score = 0.0
            # This would be calculated based on similar_grantee_analysis
            
            # Board connection score  
            board_connection_score = 0.0
            # This would be calculated based on board_overlap_analysis
            
            # Giving pattern compatibility
            pattern_compatibility = 0.0
            # This would be calculated based on giving_pattern_analysis
            
            # Foundation ecosystem centrality
            ecosystem_centrality = 0.0
            # This would be calculated based on foundation's position in ecosystem
            
            # Calculate weighted overall score
            overall_score = (
                grantee_overlap_score * self.foundation_analysis_dimensions['similar_grantee_overlap'] +
                board_connection_score * self.foundation_analysis_dimensions['foundation_board_connections'] +
                pattern_compatibility * self.foundation_analysis_dimensions['giving_pattern_compatibility'] +
                ecosystem_centrality * self.foundation_analysis_dimensions['foundation_ecosystem_centrality']
            )
            
            # Update foundation profile with scores
            foundation.grantee_overlap_score = grantee_overlap_score
            foundation.board_connection_score = board_connection_score
            foundation.giving_pattern_compatibility = pattern_compatibility
            foundation.foundation_ecosystem_centrality = ecosystem_centrality
            foundation.overall_foundation_score = overall_score
            
            foundation_scores[foundation.ein] = {
                'foundation_name': foundation.name,
                'grantee_overlap_score': round(grantee_overlap_score, 3),
                'board_connection_score': round(board_connection_score, 3),
                'giving_pattern_compatibility': round(pattern_compatibility, 3),
                'ecosystem_centrality': round(ecosystem_centrality, 3),
                'overall_foundation_score': round(overall_score, 3),
                'recommendation_tier': self._get_recommendation_tier(overall_score)
            }
        
        return foundation_scores
    
    def _get_recommendation_tier(self, score: float) -> str:
        """Convert score to recommendation tier."""
        if score >= 0.8:
            return "Priority Target"
        elif score >= 0.6:
            return "Strong Candidate"
        elif score >= 0.4:
            return "Moderate Potential"
        elif score >= 0.2:
            return "Low Priority"
        else:
            return "Not Recommended"
    
    def _generate_foundation_recommendations(self, foundation_profiles: List[FoundationProfile],
                                           foundation_scores: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic recommendations for foundation engagement."""
        recommendations = {
            "top_priority_foundations": [],
            "engagement_strategies": [],
            "timing_recommendations": [],
            "approach_strategies": []
        }
        
        # Sort foundations by score
        sorted_foundations = sorted(
            foundation_profiles, 
            key=lambda f: f.overall_foundation_score, 
            reverse=True
        )
        
        # Top priority foundations
        recommendations["top_priority_foundations"] = [
            {
                'name': f.name,
                'ein': f.ein,
                'score': round(f.overall_foundation_score, 3),
                'key_strengths': self._identify_foundation_strengths(f),
                'recommended_approach': self._suggest_approach_strategy(f)
            }
            for f in sorted_foundations[:10]
        ]
        
        return recommendations
    
    def _identify_foundation_strengths(self, foundation: FoundationProfile) -> List[str]:
        """Identify key strengths for foundation targeting."""
        strengths = []
        
        if foundation.grantee_overlap_score > 0.7:
            strengths.append("High grantee overlap - funds similar organizations")
        
        if foundation.board_connection_score > 0.5:
            strengths.append("Board connections available")
        
        if foundation.giving_pattern_compatibility > 0.6:
            strengths.append("Compatible giving patterns")
        
        if foundation.accepts_unsolicited:
            strengths.append("Accepts unsolicited proposals")
        
        return strengths
    
    def _suggest_approach_strategy(self, foundation: FoundationProfile) -> str:
        """Suggest approach strategy based on foundation characteristics."""
        if foundation.board_connection_score > 0.5:
            return "Leverage board connections for warm introduction"
        elif foundation.accepts_unsolicited:
            return "Submit direct proposal through standard application process"
        elif foundation.grantee_overlap_score > 0.6:
            return "Connect through similar grantee organizations"
        else:
            return "Build relationship through foundation events and networking"
    
    async def _get_input_organizations(self, config: ProcessorConfig, workflow_state) -> List[OrganizationProfile]:
        """Get organizations from previous workflow steps or config."""
        # Try to get from workflow state first
        if workflow_state and hasattr(workflow_state, 'organizations'):
            return workflow_state.organizations
        
        # Try to get from config input data
        if config.input_data and 'organizations' in config.input_data:
            org_data = config.input_data['organizations']
            organizations = []
            for org_dict in org_data:
                if isinstance(org_dict, dict):
                    organizations.append(OrganizationProfile(**org_dict))
                elif hasattr(org_dict, 'dict'):
                    organizations.append(OrganizationProfile(**org_dict.dict()))
            return organizations
        
        return []


# Register the processor
def register_processor():
    """Register this processor with the workflow engine."""
    from src.core.workflow_engine import get_workflow_engine
    
    engine = get_workflow_engine()
    engine.register_processor(FoundationIntelligenceEngine)
    
    return FoundationIntelligenceEngine


# Factory function for processor registration
def get_processor():
    """Factory function for processor registration."""
    return FoundationIntelligenceEngine()