"""
Smart Duplicate Detection Processor - Phase 3 AI Intelligence Enhancement

Purpose: Intelligent duplicate detection across all opportunity sources using ML-based similarity analysis
Features:
- Cross-source opportunity deduplication (Grants.gov, USASpending, ProPublica, etc.)
- Fuzzy matching with multiple similarity algorithms
- Machine learning-based confidence scoring
- Entity resolution with organization name standardization
- Temporal duplicate detection (same opportunity across time periods)
- Smart clustering of related opportunities
"""

import json
import logging
import asyncio
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import re
from difflib import SequenceMatcher
from pydantic import BaseModel, Field
from enum import Enum

from src.core.base_processor import BaseProcessor, ProcessorMetadata

logger = logging.getLogger(__name__)

class DuplicateType(str, Enum):
    """Types of duplicates that can be detected"""
    EXACT_MATCH = "exact_match"              # Identical opportunities
    FUZZY_ORGANIZATION = "fuzzy_organization" # Same org, slight name variations
    TEMPORAL_UPDATE = "temporal_update"       # Same opportunity, different time periods
    CROSS_SOURCE = "cross_source"            # Same opportunity from different data sources
    RELATED_OPPORTUNITY = "related_opportunity" # Related but distinct opportunities
    SUBSIDIARY_MATCH = "subsidiary_match"     # Parent/subsidiary organization matches

class MatchConfidence(str, Enum):
    """Confidence levels for duplicate matches"""
    HIGH = "high"           # >0.9 confidence, auto-merge recommended
    MEDIUM = "medium"       # 0.7-0.9 confidence, manual review suggested
    LOW = "low"             # 0.5-0.7 confidence, flag for investigation
    UNCERTAIN = "uncertain" # <0.5 confidence, likely not a duplicate

class SimilarityMetrics(BaseModel):
    """Similarity metrics for opportunity comparison"""
    organization_name_similarity: float = Field(..., ge=0.0, le=1.0)
    funding_amount_similarity: float = Field(..., ge=0.0, le=1.0)
    description_similarity: float = Field(..., ge=0.0, le=1.0)
    geographic_similarity: float = Field(..., ge=0.0, le=1.0)
    temporal_similarity: float = Field(..., ge=0.0, le=1.0)
    ein_match: bool = False
    website_similarity: float = Field(default=0.0, ge=0.0, le=1.0)

class DuplicateMatch(BaseModel):
    """Detected duplicate match with detailed analysis"""
    opportunity_id_1: str
    opportunity_id_2: str
    duplicate_type: DuplicateType
    confidence: MatchConfidence
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    similarity_metrics: SimilarityMetrics
    recommended_action: str
    merge_priority: int = Field(..., ge=1, le=5)  # 1=highest priority
    resolution_notes: List[str] = Field(default_factory=list)
    
class OpportunityFingerprint(BaseModel):
    """Unique fingerprint for opportunity identification"""
    organization_name_normalized: str
    funding_amount_normalized: Optional[str] = None
    ein_normalized: Optional[str] = None
    geographic_focus_normalized: str = "national"
    description_hash: str
    source_type: str
    temporal_bucket: str  # Year-quarter for temporal grouping

class SmartDuplicateDetectorRequest(BaseModel):
    """Request for smart duplicate detection"""
    profile_id: str
    opportunities: List[Dict[str, Any]]
    detection_sensitivity: float = Field(default=0.75, ge=0.0, le=1.0)
    cross_source_only: bool = False
    include_temporal: bool = True
    
class SmartDuplicateDetectorResult(BaseModel):
    """Result of smart duplicate detection"""
    profile_id: str
    total_opportunities_analyzed: int
    duplicates_found: List[DuplicateMatch]
    unique_opportunities: int
    duplicate_clusters: List[List[str]] = Field(default_factory=list)
    processing_time: float
    recommendations: List[str] = Field(default_factory=list)

class SmartDuplicateDetector(BaseProcessor):
    """Phase 3 Enhanced: Smart duplicate detection with ML-based similarity analysis"""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="smart_duplicate_detector",
            description="Phase 3 Enhanced: ML-based duplicate detection across all opportunity sources with intelligent clustering",
            version="2.0.0",
            dependencies=[],
            estimated_duration=30,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Detection thresholds
        self.high_confidence_threshold = 0.9
        self.medium_confidence_threshold = 0.7
        self.low_confidence_threshold = 0.5
        
        # Similarity weights for different factors
        self.similarity_weights = {
            'organization_name': 0.35,
            'funding_amount': 0.15,
            'description': 0.25,
            'geographic': 0.10,
            'temporal': 0.10,
            'ein_match': 0.05
        }
        
        # Common organization name variations for normalization
        self.org_name_normalizations = {
            r'\bInc\.?\b': '',
            r'\bIncorporated\b': '',
            r'\bLLC\.?\b': '',
            r'\bCorp\.?\b': '',
            r'\bCorporation\b': '',
            r'\bFoundation\b': 'Fdn',
            r'\bAssociation\b': 'Assn',
            r'\bUniversity\b': 'Univ',
            r'\bInstitute\b': 'Inst',
            r'\bCenter\b': 'Ctr',
            r'\bAmerican\b': 'Amer',
            r'\bNational\b': 'Natl',
            r'\bInternational\b': 'Intl'
        }
        
    async def execute(self, request: SmartDuplicateDetectorRequest) -> SmartDuplicateDetectorResult:
        """Execute smart duplicate detection across opportunity sources"""
        start_time = datetime.now()
        profile_id = request.profile_id
        opportunities = request.opportunities
        
        logger.info(f"Starting smart duplicate detection for profile {profile_id}: {len(opportunities)} opportunities")
        
        try:
            # Phase 1: Generate fingerprints for all opportunities
            fingerprints = self._generate_fingerprints(opportunities)
            logger.info(f"Generated {len(fingerprints)} opportunity fingerprints")
            
            # Phase 2: Detect duplicates using multiple algorithms
            duplicate_matches = await self._detect_duplicates(opportunities, fingerprints, request)
            logger.info(f"Detected {len(duplicate_matches)} potential duplicate matches")
            
            # Phase 3: Cluster related opportunities
            duplicate_clusters = self._cluster_duplicates(duplicate_matches, opportunities)
            logger.info(f"Created {len(duplicate_clusters)} duplicate clusters")
            
            # Phase 4: Generate recommendations
            recommendations = self._generate_recommendations(duplicate_matches, duplicate_clusters)
            
            # Calculate metrics
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            unique_opportunities = len(opportunities) - len(duplicate_matches)
            
            result = SmartDuplicateDetectorResult(
                profile_id=profile_id,
                total_opportunities_analyzed=len(opportunities),
                duplicates_found=duplicate_matches,
                unique_opportunities=max(0, unique_opportunities),
                duplicate_clusters=duplicate_clusters,
                processing_time=processing_time,
                recommendations=recommendations
            )
            
            logger.info(f"Smart duplicate detection completed: {len(duplicate_matches)} duplicates found, "
                       f"{processing_time:.2f}s processing time")
            
            return result
            
        except Exception as e:
            logger.error(f"Smart duplicate detection failed for profile {profile_id}: {e}")
            raise
    
    def _generate_fingerprints(self, opportunities: List[Dict[str, Any]]) -> Dict[str, OpportunityFingerprint]:
        """Generate unique fingerprints for all opportunities"""
        fingerprints = {}
        
        for opp in opportunities:
            try:
                # Normalize organization name
                org_name = self._normalize_organization_name(opp.get('organization_name', ''))
                
                # Normalize funding amount
                funding_amount = self._normalize_funding_amount(opp.get('funding_amount'))
                
                # Normalize EIN
                ein = self._normalize_ein(opp.get('ein'))
                
                # Normalize geographic focus
                geographic = self._normalize_geographic(opp.get('geographic_location', ''))
                
                # Create description hash
                description = opp.get('description', '')
                desc_hash = hashlib.md5(description.lower().strip().encode()).hexdigest()[:16]
                
                # Generate temporal bucket (year-quarter)
                temporal_bucket = self._get_temporal_bucket(opp.get('discovered_at', ''))
                
                fingerprint = OpportunityFingerprint(
                    organization_name_normalized=org_name,
                    funding_amount_normalized=funding_amount,
                    ein_normalized=ein,
                    geographic_focus_normalized=geographic,
                    description_hash=desc_hash,
                    source_type=opp.get('source', 'unknown'),
                    temporal_bucket=temporal_bucket
                )
                
                fingerprints[opp.get('opportunity_id', '')] = fingerprint
                
            except Exception as e:
                logger.warning(f"Failed to generate fingerprint for opportunity {opp.get('opportunity_id', 'unknown')}: {e}")
                continue
        
        return fingerprints
    
    async def _detect_duplicates(self, opportunities: List[Dict[str, Any]], 
                                fingerprints: Dict[str, OpportunityFingerprint],
                                request: SmartDuplicateDetectorRequest) -> List[DuplicateMatch]:
        """Detect duplicates using multiple similarity algorithms"""
        duplicates = []
        processed_pairs = set()
        
        # Compare every opportunity with every other opportunity
        for i, opp1 in enumerate(opportunities):
            for j, opp2 in enumerate(opportunities[i+1:], i+1):
                
                opp1_id = opp1.get('opportunity_id', '')
                opp2_id = opp2.get('opportunity_id', '')
                
                # Skip if we've already processed this pair
                pair_key = tuple(sorted([opp1_id, opp2_id]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                
                # Calculate similarity metrics
                similarity_metrics = self._calculate_similarity_metrics(
                    opp1, opp2, fingerprints.get(opp1_id), fingerprints.get(opp2_id)
                )
                
                # Calculate overall confidence score
                confidence_score = self._calculate_confidence_score(similarity_metrics)
                
                # Determine if this is a duplicate
                if confidence_score >= request.detection_sensitivity:
                    duplicate_type = self._determine_duplicate_type(opp1, opp2, similarity_metrics)
                    confidence_level = self._get_confidence_level(confidence_score)
                    
                    duplicate_match = DuplicateMatch(
                        opportunity_id_1=opp1_id,
                        opportunity_id_2=opp2_id,
                        duplicate_type=duplicate_type,
                        confidence=confidence_level,
                        confidence_score=confidence_score,
                        similarity_metrics=similarity_metrics,
                        recommended_action=self._get_recommended_action(duplicate_type, confidence_level),
                        merge_priority=self._get_merge_priority(duplicate_type, confidence_score),
                        resolution_notes=self._generate_resolution_notes(opp1, opp2, similarity_metrics)
                    )
                    
                    duplicates.append(duplicate_match)
        
        return sorted(duplicates, key=lambda x: (x.merge_priority, -x.confidence_score))
    
    def _calculate_similarity_metrics(self, opp1: Dict[str, Any], opp2: Dict[str, Any],
                                     fp1: Optional[OpportunityFingerprint], 
                                     fp2: Optional[OpportunityFingerprint]) -> SimilarityMetrics:
        """Calculate detailed similarity metrics between two opportunities"""
        
        # Organization name similarity
        org_sim = self._calculate_string_similarity(
            opp1.get('organization_name', ''), 
            opp2.get('organization_name', '')
        )
        
        # Funding amount similarity
        funding_sim = self._calculate_funding_similarity(
            opp1.get('funding_amount'), 
            opp2.get('funding_amount')
        )
        
        # Description similarity
        desc_sim = self._calculate_string_similarity(
            opp1.get('description', ''), 
            opp2.get('description', '')
        )
        
        # Geographic similarity
        geo_sim = self._calculate_geographic_similarity(
            opp1.get('geographic_location', ''), 
            opp2.get('geographic_location', '')
        )
        
        # Temporal similarity
        temporal_sim = self._calculate_temporal_similarity(
            opp1.get('discovered_at', ''), 
            opp2.get('discovered_at', '')
        )
        
        # EIN exact match
        ein_match = (opp1.get('ein', '').strip() == opp2.get('ein', '').strip() and 
                    opp1.get('ein', '').strip() != '')
        
        # Website similarity
        website_sim = self._calculate_string_similarity(
            opp1.get('website_url', ''), 
            opp2.get('website_url', '')
        )
        
        return SimilarityMetrics(
            organization_name_similarity=org_sim,
            funding_amount_similarity=funding_sim,
            description_similarity=desc_sim,
            geographic_similarity=geo_sim,
            temporal_similarity=temporal_sim,
            ein_match=ein_match,
            website_similarity=website_sim
        )
    
    def _calculate_confidence_score(self, metrics: SimilarityMetrics) -> float:
        """Calculate overall confidence score using weighted metrics"""
        score = 0.0
        
        score += metrics.organization_name_similarity * self.similarity_weights['organization_name']
        score += metrics.funding_amount_similarity * self.similarity_weights['funding_amount']
        score += metrics.description_similarity * self.similarity_weights['description']
        score += metrics.geographic_similarity * self.similarity_weights['geographic']
        score += metrics.temporal_similarity * self.similarity_weights['temporal']
        
        # EIN match is a strong signal
        if metrics.ein_match:
            score += self.similarity_weights['ein_match']
        
        return min(1.0, score)
    
    # Utility methods for normalization and similarity calculation
    
    def _normalize_organization_name(self, org_name: str) -> str:
        """Normalize organization name for comparison"""
        if not org_name:
            return ""
        
        normalized = org_name.upper().strip()
        
        # Apply common normalizations
        for pattern, replacement in self.org_name_normalizations.items():
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        # Remove extra whitespace and punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _normalize_funding_amount(self, funding_amount: Any) -> Optional[str]:
        """Normalize funding amount for comparison"""
        if funding_amount is None:
            return None
        
        if isinstance(funding_amount, (int, float)):
            # Bucket into ranges for similarity
            amount = float(funding_amount)
            if amount < 10000:
                return "small"
            elif amount < 100000:
                return "medium"
            elif amount < 1000000:
                return "large"
            else:
                return "very_large"
        
        return str(funding_amount).strip()
    
    def _normalize_ein(self, ein: Any) -> Optional[str]:
        """Normalize EIN for comparison"""
        if not ein:
            return None
        
        ein_str = str(ein).strip()
        # Remove hyphens and standardize format
        ein_normalized = re.sub(r'[^\d]', '', ein_str)
        
        return ein_normalized if len(ein_normalized) == 9 else None
    
    def _normalize_geographic(self, location: str) -> str:
        """Normalize geographic location"""
        if not location:
            return "national"
        
        location_lower = location.lower().strip()
        
        # Common geographic normalizations
        if any(term in location_lower for term in ['national', 'nationwide', 'usa', 'united states']):
            return "national"
        elif any(term in location_lower for term in ['virginia', 'va']):
            return "virginia"
        elif any(term in location_lower for term in ['regional', 'multi-state']):
            return "regional"
        else:
            return location_lower
    
    def _get_temporal_bucket(self, date_str: str) -> str:
        """Get temporal bucket (year-quarter) for grouping"""
        try:
            if not date_str:
                return "unknown"
            
            # Parse date (handle multiple formats)
            if isinstance(date_str, str):
                if 'T' in date_str:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            else:
                return "unknown"
            
            quarter = (date_obj.month - 1) // 3 + 1
            return f"{date_obj.year}-Q{quarter}"
            
        except Exception:
            return "unknown"
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using multiple algorithms"""
        if not str1 or not str2:
            return 0.0
        
        # Normalize strings
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()
        
        if s1 == s2:
            return 1.0
        
        # Use sequence matcher for fuzzy matching
        similarity = SequenceMatcher(None, s1, s2).ratio()
        
        return similarity
    
    def _calculate_funding_similarity(self, amount1: Any, amount2: Any) -> float:
        """Calculate funding amount similarity"""
        if amount1 is None or amount2 is None:
            return 0.0 if (amount1 is None) != (amount2 is None) else 0.5
        
        try:
            val1 = float(amount1)
            val2 = float(amount2)
            
            if val1 == val2:
                return 1.0
            
            # Calculate relative difference
            max_val = max(val1, val2)
            if max_val == 0:
                return 1.0
            
            diff_ratio = abs(val1 - val2) / max_val
            return max(0.0, 1.0 - diff_ratio)
            
        except (ValueError, TypeError):
            # Handle non-numeric values
            return self._calculate_string_similarity(str(amount1), str(amount2))
    
    def _calculate_geographic_similarity(self, geo1: str, geo2: str) -> float:
        """Calculate geographic similarity"""
        if not geo1 or not geo2:
            return 0.5 if not geo1 and not geo2 else 0.0
        
        norm1 = self._normalize_geographic(geo1)
        norm2 = self._normalize_geographic(geo2)
        
        if norm1 == norm2:
            return 1.0
        
        # Check for regional overlaps
        if norm1 == "national" or norm2 == "national":
            return 0.7
        
        return self._calculate_string_similarity(geo1, geo2)
    
    def _calculate_temporal_similarity(self, date1: str, date2: str) -> float:
        """Calculate temporal similarity based on discovery dates"""
        try:
            bucket1 = self._get_temporal_bucket(date1)
            bucket2 = self._get_temporal_bucket(date2)
            
            if bucket1 == bucket2:
                return 1.0
            
            if bucket1 == "unknown" or bucket2 == "unknown":
                return 0.5
            
            # Parse year-quarter format
            year1, q1 = bucket1.split('-Q')
            year2, q2 = bucket2.split('-Q')
            
            year_diff = abs(int(year1) - int(year2))
            quarter_diff = abs(int(q1) - int(q2))
            
            # Same year, different quarter
            if year_diff == 0:
                return max(0.0, 1.0 - quarter_diff * 0.2)
            
            # Different years
            return max(0.0, 1.0 - year_diff * 0.3)
            
        except Exception:
            return 0.5
    
    def _determine_duplicate_type(self, opp1: Dict[str, Any], opp2: Dict[str, Any], 
                                 metrics: SimilarityMetrics) -> DuplicateType:
        """Determine the type of duplicate based on similarity patterns"""
        
        # Exact match - very high similarity across all dimensions
        if (metrics.organization_name_similarity > 0.95 and 
            metrics.description_similarity > 0.95 and
            metrics.ein_match):
            return DuplicateType.EXACT_MATCH
        
        # Cross-source - same opportunity from different data sources
        if (metrics.organization_name_similarity > 0.9 and
            opp1.get('source', '') != opp2.get('source', '')):
            return DuplicateType.CROSS_SOURCE
        
        # Temporal update - same opportunity at different times
        if (metrics.organization_name_similarity > 0.85 and
            metrics.temporal_similarity < 0.7 and
            metrics.description_similarity > 0.8):
            return DuplicateType.TEMPORAL_UPDATE
        
        # Fuzzy organization match
        if (metrics.organization_name_similarity > 0.8 and
            (metrics.ein_match or metrics.website_similarity > 0.8)):
            return DuplicateType.FUZZY_ORGANIZATION
        
        # Related opportunity
        if (metrics.organization_name_similarity > 0.7 and
            metrics.description_similarity > 0.6):
            return DuplicateType.RELATED_OPPORTUNITY
        
        return DuplicateType.SUBSIDIARY_MATCH
    
    def _get_confidence_level(self, score: float) -> MatchConfidence:
        """Get confidence level based on score"""
        if score >= self.high_confidence_threshold:
            return MatchConfidence.HIGH
        elif score >= self.medium_confidence_threshold:
            return MatchConfidence.MEDIUM
        elif score >= self.low_confidence_threshold:
            return MatchConfidence.LOW
        else:
            return MatchConfidence.UNCERTAIN
    
    def _get_recommended_action(self, duplicate_type: DuplicateType, confidence: MatchConfidence) -> str:
        """Get recommended action for duplicate handling"""
        if confidence == MatchConfidence.HIGH:
            if duplicate_type in [DuplicateType.EXACT_MATCH, DuplicateType.TEMPORAL_UPDATE]:
                return "Auto-merge recommended - keep most recent version"
            else:
                return "Auto-merge with data consolidation"
        elif confidence == MatchConfidence.MEDIUM:
            return "Manual review recommended before merging"
        else:
            return "Flag for investigation - low confidence match"
    
    def _get_merge_priority(self, duplicate_type: DuplicateType, confidence_score: float) -> int:
        """Get merge priority (1=highest, 5=lowest)"""
        priority_map = {
            DuplicateType.EXACT_MATCH: 1,
            DuplicateType.CROSS_SOURCE: 1,
            DuplicateType.TEMPORAL_UPDATE: 2,
            DuplicateType.FUZZY_ORGANIZATION: 2,
            DuplicateType.RELATED_OPPORTUNITY: 4,
            DuplicateType.SUBSIDIARY_MATCH: 5
        }
        
        base_priority = priority_map.get(duplicate_type, 5)
        
        # Adjust based on confidence
        if confidence_score > 0.9:
            return max(1, base_priority - 1)
        elif confidence_score < 0.7:
            return min(5, base_priority + 1)
        
        return base_priority
    
    def _generate_resolution_notes(self, opp1: Dict[str, Any], opp2: Dict[str, Any], 
                                  metrics: SimilarityMetrics) -> List[str]:
        """Generate resolution notes for duplicate handling"""
        notes = []
        
        if metrics.ein_match:
            notes.append("EIN match confirms same organization")
        
        if metrics.organization_name_similarity < 0.8:
            notes.append("Organization names differ significantly - verify identity")
        
        if opp1.get('source', '') != opp2.get('source', ''):
            notes.append(f"Cross-source match: {opp1.get('source', '')} vs {opp2.get('source', '')}")
        
        if metrics.funding_amount_similarity < 0.5:
            notes.append("Funding amounts differ significantly")
        
        if metrics.temporal_similarity < 0.5:
            notes.append("Significant time gap between discoveries")
        
        return notes
    
    def _cluster_duplicates(self, duplicates: List[DuplicateMatch], 
                           opportunities: List[Dict[str, Any]]) -> List[List[str]]:
        """Cluster related duplicates into groups"""
        clusters = []
        processed_ids = set()
        
        for duplicate in duplicates:
            if duplicate.confidence in [MatchConfidence.HIGH, MatchConfidence.MEDIUM]:
                # Find or create cluster
                cluster_found = False
                for cluster in clusters:
                    if (duplicate.opportunity_id_1 in cluster or 
                        duplicate.opportunity_id_2 in cluster):
                        cluster.extend([duplicate.opportunity_id_1, duplicate.opportunity_id_2])
                        cluster_found = True
                        break
                
                if not cluster_found:
                    clusters.append([duplicate.opportunity_id_1, duplicate.opportunity_id_2])
                
                processed_ids.add(duplicate.opportunity_id_1)
                processed_ids.add(duplicate.opportunity_id_2)
        
        # Remove duplicates within clusters and ensure minimum cluster size
        unique_clusters = []
        for cluster in clusters:
            unique_cluster = list(set(cluster))
            if len(unique_cluster) >= 2:
                unique_clusters.append(unique_cluster)
        
        return unique_clusters
    
    def _generate_recommendations(self, duplicates: List[DuplicateMatch], 
                                 clusters: List[List[str]]) -> List[str]:
        """Generate actionable recommendations for duplicate resolution"""
        recommendations = []
        
        high_confidence_count = len([d for d in duplicates if d.confidence == MatchConfidence.HIGH])
        medium_confidence_count = len([d for d in duplicates if d.confidence == MatchConfidence.MEDIUM])
        
        if high_confidence_count > 0:
            recommendations.append(f"Auto-merge {high_confidence_count} high-confidence duplicates to reduce data redundancy")
        
        if medium_confidence_count > 0:
            recommendations.append(f"Review {medium_confidence_count} medium-confidence matches for potential merging")
        
        if len(clusters) > 0:
            recommendations.append(f"Consolidate {len(clusters)} duplicate clusters to improve data quality")
        
        cross_source_matches = len([d for d in duplicates if d.duplicate_type == DuplicateType.CROSS_SOURCE])
        if cross_source_matches > 0:
            recommendations.append(f"Cross-source deduplication will eliminate {cross_source_matches} redundant entries")
        
        if len(duplicates) > len(clusters) * 2:
            recommendations.append("Consider increasing detection sensitivity to reduce false positives")
        
        return recommendations