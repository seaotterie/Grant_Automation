#!/usr/bin/env python3
"""
Smart URL Resolution Service

Implements intelligent URL prioritization for web scraping with confidence scoring.

Data Source Priority Hierarchy:
1. User-provided Profile URL (highest confidence - user knows the organization)
2. 990/990-PF declared website (official tax filing data)

This service eliminates URL guessing errors and provides transparent source attribution.
User is responsible for manual URL entry if automatic sources fail.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from urllib.parse import urlparse
import re
import logging
from datetime import datetime

from .tax_filing_leadership_service import TaxFilingLeadershipService

logger = logging.getLogger(__name__)


@dataclass
class URLCandidate:
    """URL candidate with confidence and source attribution"""
    url: str
    source: str  # 'user_provided', '990_declared'
    confidence_score: float  # 0.0 to 1.0
    source_description: str
    validation_status: str = "pending"  # 'pending', 'valid', 'invalid', 'timeout'
    http_status_code: Optional[int] = None
    discovered_at: datetime = field(default_factory=datetime.now)
    notes: List[str] = field(default_factory=list)


@dataclass
class URLResolutionResult:
    """Complete URL resolution with ranked candidates"""
    ein: str
    organization_name: str
    primary_url: Optional[URLCandidate] = None
    all_candidates: List[URLCandidate] = field(default_factory=list)
    resolution_strategy: str = ""
    confidence_assessment: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class SmartURLResolutionService:
    """
    Intelligent URL resolution with multi-source prioritization.
    
    Combines user input, tax filing data, and algorithmic predictions
    to select the most reliable URLs for web scraping.
    """
    
    def __init__(self):
        self.tax_filing_service = TaxFilingLeadershipService()
        self.url_validation_cache = {}  # Simple cache for URL validation results
        
    async def resolve_organization_url(self, 
                                     ein: str, 
                                     organization_name: str,
                                     user_provided_url: Optional[str] = None) -> URLResolutionResult:
        """
        Resolve the best URL for an organization using smart prioritization.
        
        Args:
            ein: Organization EIN
            organization_name: Organization name
            user_provided_url: Optional user-provided website URL
            
        Returns:
            URLResolutionResult with ranked URL candidates
        """
        logger.info(f"Resolving URLs for {organization_name} (EIN: {ein})")
        
        result = URLResolutionResult(
            ein=ein,
            organization_name=organization_name
        )
        
        try:
            # Step 1: Collect URL candidates from all sources
            candidates = await self._collect_url_candidates(ein, organization_name, user_provided_url)
            result.all_candidates = candidates
            
            # Step 2: Validate and score candidates
            validated_candidates = await self._validate_url_candidates(candidates)
            result.all_candidates = validated_candidates
            
            # Step 3: Select primary URL using smart prioritization
            primary_url = self._select_primary_url(validated_candidates)
            result.primary_url = primary_url
            
            # Step 4: Generate resolution strategy and recommendations
            result.resolution_strategy = self._generate_resolution_strategy(validated_candidates, primary_url)
            result.confidence_assessment = self._assess_confidence(validated_candidates, primary_url)
            result.recommendations = self._generate_recommendations(validated_candidates, primary_url)
            
            logger.info(f"URL resolution completed for {organization_name}: {primary_url.url if primary_url else 'No valid URL found'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in URL resolution for {organization_name}: {e}")
            result.recommendations.append(f"Resolution error: {str(e)}")
            return result
    
    async def _collect_url_candidates(self, 
                                    ein: str, 
                                    organization_name: str,
                                    user_provided_url: Optional[str]) -> List[URLCandidate]:
        """Collect URL candidates from all available sources"""
        candidates = []
        
        # Source 1: User-provided URL (highest priority)
        if user_provided_url:
            user_candidate = URLCandidate(
                url=self._normalize_url(user_provided_url),
                source="user_provided",
                confidence_score=0.95,  # High confidence - user knows their organization
                source_description="User-provided organization website",
                notes=["Provided by user during profile creation"]
            )
            candidates.append(user_candidate)
            logger.info(f"Added user-provided URL: {user_candidate.url}")
        
        # Source 2: 990/990-PF declared website (high confidence)
        tax_baseline = await self.tax_filing_service.get_leadership_baseline(ein)
        if tax_baseline and tax_baseline.declared_website:
            tax_candidate = URLCandidate(
                url=self._normalize_url(tax_baseline.declared_website),
                source="990_declared",
                confidence_score=0.85,  # High confidence - official tax filing
                source_description=f"Declared in {tax_baseline.filing_year} tax filing",
                notes=[f"From 990 filing year {tax_baseline.filing_year}"]
            )
            candidates.append(tax_candidate)
            logger.info(f"Added 990-declared URL: {tax_candidate.url}")

        # GPT URL prediction removed - unreliable and unnecessary
        # User is responsible for manual URL entry if automatic sources fail

        # Remove duplicates while preserving highest confidence source
        candidates = self._deduplicate_candidates(candidates)
        
        return candidates
    
    # GPT URL prediction method removed (deprecated)
    # gpt_url_discovery.py processor deprecated - unreliable and unnecessary AI costs

    def _normalize_url(self, url: str) -> str:
        """Normalize URL format for consistency"""
        if not url:
            return ""
        
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            # Prefer HTTPS for security
            url = f"https://{url}"
        
        # Remove trailing slashes
        url = url.rstrip('/')
        
        # Convert to lowercase domain (preserving path case)
        parsed = urlparse(url)
        normalized = url.replace(parsed.netloc, parsed.netloc.lower())
        
        return normalized
    
    def _deduplicate_candidates(self, candidates: List[URLCandidate]) -> List[URLCandidate]:
        """Remove duplicate URLs, keeping highest confidence source"""
        seen_urls = {}
        
        for candidate in candidates:
            normalized_url = candidate.url.lower()
            
            if normalized_url not in seen_urls:
                seen_urls[normalized_url] = candidate
            else:
                # Keep the candidate with higher confidence
                existing = seen_urls[normalized_url]
                if candidate.confidence_score > existing.confidence_score:
                    candidate.notes.append(f"Replaced lower confidence {existing.source} source")
                    seen_urls[normalized_url] = candidate
                else:
                    existing.notes.append(f"Duplicate found from {candidate.source} source")
        
        return list(seen_urls.values())
    
    async def _validate_url_candidates(self, candidates: List[URLCandidate]) -> List[URLCandidate]:
        """Validate URL candidates and update their status"""
        import aiohttp
        import asyncio
        
        async def validate_single_url(candidate: URLCandidate) -> URLCandidate:
            try:
                # Check cache first
                if candidate.url in self.url_validation_cache:
                    cached_result = self.url_validation_cache[candidate.url]
                    candidate.validation_status = cached_result['status']
                    candidate.http_status_code = cached_result['status_code']
                    candidate.notes.append("Validation from cache")
                    return candidate
                
                # Perform HTTP validation
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.head(candidate.url, allow_redirects=True) as response:
                        candidate.http_status_code = response.status
                        
                        if response.status == 200:
                            candidate.validation_status = "valid"
                            candidate.notes.append("HTTP 200 OK - Website accessible")
                        elif response.status in [301, 302, 303, 307, 308]:
                            candidate.validation_status = "valid"
                            candidate.notes.append(f"HTTP {response.status} - Redirects properly")
                        else:
                            candidate.validation_status = "invalid"
                            candidate.notes.append(f"HTTP {response.status} - Website issue")
                
                # Cache the result
                self.url_validation_cache[candidate.url] = {
                    'status': candidate.validation_status,
                    'status_code': candidate.http_status_code
                }
                
            except asyncio.TimeoutError:
                candidate.validation_status = "timeout"
                candidate.notes.append("Validation timeout - slow response")
            except Exception as e:
                candidate.validation_status = "invalid"
                candidate.notes.append(f"Validation error: {str(e)}")
            
            return candidate
        
        # Validate all candidates concurrently
        validated_candidates = await asyncio.gather(
            *[validate_single_url(candidate) for candidate in candidates],
            return_exceptions=True
        )
        
        # Handle any exceptions from validation
        result_candidates = []
        for i, result in enumerate(validated_candidates):
            if isinstance(result, Exception):
                candidates[i].validation_status = "invalid"
                candidates[i].notes.append(f"Validation exception: {str(result)}")
                result_candidates.append(candidates[i])
            else:
                result_candidates.append(result)
        
        return result_candidates
    
    def _select_primary_url(self, candidates: List[URLCandidate]) -> Optional[URLCandidate]:
        """Select the primary URL using smart prioritization logic"""
        if not candidates:
            return None
        
        # Filter to valid URLs only
        valid_candidates = [c for c in candidates if c.validation_status == "valid"]
        
        if not valid_candidates:
            # If no valid URLs, try accessible ones (timeout/redirects)
            accessible_candidates = [c for c in candidates 
                                   if c.validation_status in ["valid", "timeout"]]
            if accessible_candidates:
                valid_candidates = accessible_candidates
            else:
                # Last resort: use highest confidence regardless of validation
                valid_candidates = candidates
        
        # Priority hierarchy: User > 990 (only 2 sources)
        source_priority = {
            "user_provided": 2,
            "990_declared": 1
        }
        
        # Sort by source priority, then confidence score
        sorted_candidates = sorted(
            valid_candidates,
            key=lambda c: (source_priority.get(c.source, 0), c.confidence_score),
            reverse=True
        )
        
        return sorted_candidates[0] if sorted_candidates else None
    
    def _generate_resolution_strategy(self, 
                                    candidates: List[URLCandidate], 
                                    primary_url: Optional[URLCandidate]) -> str:
        """Generate human-readable resolution strategy"""
        if not primary_url:
            return "No valid URL found - manual verification required"
        
        source_strategies = {
            "user_provided": "Using user-provided URL (highest confidence)",
            "990_declared": "Using 990-declared website (official tax filing)"
        }
        
        strategy = source_strategies.get(primary_url.source, "Using best available URL")
        
        # Add validation context
        if primary_url.validation_status == "valid":
            strategy += " - validated as accessible"
        elif primary_url.validation_status == "timeout":
            strategy += " - slow response but likely valid"
        else:
            strategy += " - validation inconclusive"
        
        return strategy
    
    def _assess_confidence(self, 
                         candidates: List[URLCandidate], 
                         primary_url: Optional[URLCandidate]) -> Dict[str, Any]:
        """Assess overall confidence in URL resolution"""
        assessment = {
            "overall_confidence": 0.0,
            "confidence_factors": [],
            "risk_factors": [],
            "data_quality": "unknown"
        }
        
        if not primary_url:
            assessment["overall_confidence"] = 0.0
            assessment["risk_factors"].append("No valid URL found")
            assessment["data_quality"] = "poor"
            return assessment
        
        # Base confidence from source
        base_confidence = primary_url.confidence_score
        
        # Adjust for validation status
        validation_multiplier = {
            "valid": 1.0,
            "timeout": 0.9,
            "invalid": 0.5,
            "pending": 0.8
        }
        
        validated_confidence = base_confidence * validation_multiplier.get(
            primary_url.validation_status, 0.8
        )
        
        assessment["overall_confidence"] = validated_confidence
        
        # Confidence factors
        if primary_url.source == "user_provided":
            assessment["confidence_factors"].append("User-provided URL (high trust)")
        elif primary_url.source == "990_declared":
            assessment["confidence_factors"].append("Official tax filing declaration")
        
        if primary_url.validation_status == "valid":
            assessment["confidence_factors"].append("HTTP validation successful")
        
        # Risk factors
        if primary_url.validation_status == "invalid":
            assessment["risk_factors"].append("URL validation failed")
        
        if len(candidates) == 1:
            assessment["risk_factors"].append("Single URL source (no alternatives)")
        
        # Data quality assessment
        if validated_confidence >= 0.9:
            assessment["data_quality"] = "excellent"
        elif validated_confidence >= 0.7:
            assessment["data_quality"] = "good"
        elif validated_confidence >= 0.5:
            assessment["data_quality"] = "fair"
        else:
            assessment["data_quality"] = "poor"
        
        return assessment
    
    def _generate_recommendations(self, 
                                candidates: List[URLCandidate], 
                                primary_url: Optional[URLCandidate]) -> List[str]:
        """Generate actionable recommendations for URL usage"""
        recommendations = []
        
        if not primary_url:
            recommendations.append("Manual URL verification required - no valid URLs found")
            recommendations.append("Consider adding organization website to profile")
            return recommendations
        
        # Source-specific recommendations
        if primary_url.source == "user_provided":
            recommendations.append("High confidence URL - proceed with web scraping")
        elif primary_url.source == "990_declared":
            recommendations.append("Official website from tax filing - reliable source")

        # Validation-based recommendations
        if primary_url.validation_status == "invalid":
            recommendations.append("URL validation failed - manual verification recommended")
        elif primary_url.validation_status == "timeout":
            recommendations.append("Slow website response - consider timeout adjustments")
        
        # Multi-source recommendations
        user_sources = [c for c in candidates if c.source == "user_provided"]
        tax_sources = [c for c in candidates if c.source == "990_declared"] 
        
        if not user_sources and tax_sources:
            recommendations.append("Consider adding user-provided URL for higher confidence")
        
        if len([c for c in candidates if c.validation_status == "valid"]) > 1:
            recommendations.append("Multiple valid URLs available - current selection prioritized")
        
        return recommendations