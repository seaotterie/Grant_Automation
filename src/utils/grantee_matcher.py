"""
Grantee Matcher - Match discovered organizations against Schedule I grantees
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
import logging

from src.profiles.models import ScheduleIGrantee, OrganizationProfile
from src.discovery.base_discoverer import DiscoveryResult, FunnelStage

logger = logging.getLogger(__name__)


class GranteeMatcher:
    """Match discovered organizations against Schedule I grantees for fast-tracking"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Matching thresholds
        self.name_similarity_threshold = 0.85  # Name similarity threshold for matches
        self.ein_match_threshold = 1.0         # EIN matches must be exact
        self.fuzzy_match_threshold = 0.75      # Fuzzy matching threshold
        
    def match_discovery_results_against_grantees(
        self,
        discovery_results: List[DiscoveryResult],
        profile: OrganizationProfile
    ) -> List[DiscoveryResult]:
        """
        Match discovery results against profile's Schedule I grantees.
        Updates discovery results with grantee match information and fast-tracks them.
        
        Args:
            discovery_results: List of discovered opportunities
            profile: Organization profile containing Schedule I grantees
            
        Returns:
            Updated discovery results with grantee matches identified and fast-tracked
        """
        if not profile.schedule_i_grantees:
            self.logger.info(f"No Schedule I grantees found in profile {profile.name}")
            return discovery_results
        
        self.logger.info(f"Matching {len(discovery_results)} discoveries against {len(profile.schedule_i_grantees)} Schedule I grantees")
        
        matched_count = 0
        fast_tracked_count = 0
        
        for result in discovery_results:
            grantee_match = self._find_grantee_match(result, profile.schedule_i_grantees)
            
            if grantee_match:
                # Mark as Schedule I grantee match
                result.is_schedule_i_grantee = True
                result.schedule_i_match_data = grantee_match
                
                # Fast-track to CANDIDATES stage
                result.funnel_stage = FunnelStage.CANDIDATES
                result.stage_notes = f"Auto-promoted to CANDIDATES: Schedule I grantee match with {grantee_match['grantee_name']} (${grantee_match['grant_amount']:,.0f} in {grantee_match['grant_year']})"
                
                # Boost compatibility score to ensure continued progression
                original_score = result.compatibility_score
                result.compatibility_score = max(0.85, original_score)  # Minimum 85% score
                
                # Add to match factors
                result.match_factors['schedule_i_grantee'] = True
                result.match_factors['historical_grant_amount'] = grantee_match['grant_amount']
                result.match_factors['historical_grant_year'] = grantee_match['grant_year']
                
                matched_count += 1
                if result.funnel_stage == FunnelStage.CANDIDATES:
                    fast_tracked_count += 1
                
                self.logger.info(f"Matched '{result.organization_name}' to Schedule I grantee '{grantee_match['grantee_name']}' (${grantee_match['grant_amount']:,.0f}, {grantee_match['grant_year']})")
        
        self.logger.info(f"Schedule I matching complete: {matched_count} matches found, {fast_tracked_count} fast-tracked to CANDIDATES")
        
        return discovery_results
    
    def _find_grantee_match(
        self,
        discovery_result: DiscoveryResult,
        grantees: List[ScheduleIGrantee]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best matching Schedule I grantee for a discovery result.
        
        Args:
            discovery_result: The discovered organization
            grantees: List of Schedule I grantees to match against
            
        Returns:
            Match data if found, None otherwise
        """
        best_match = None
        best_score = 0.0
        
        discovery_name = discovery_result.organization_name.strip()
        discovery_ein = self._extract_ein_from_external_data(discovery_result)
        
        for grantee in grantees:
            match_score = 0.0
            match_method = ""
            
            # Try EIN match first (highest priority)
            if discovery_ein and grantee.recipient_ein:
                if self._normalize_ein(discovery_ein) == self._normalize_ein(grantee.recipient_ein):
                    match_score = 1.0
                    match_method = "ein_exact"
            
            # If no EIN match, try name matching
            if match_score < self.ein_match_threshold:
                name_similarity = self._calculate_name_similarity(discovery_name, grantee.recipient_name)
                if name_similarity >= self.name_similarity_threshold:
                    match_score = name_similarity
                    match_method = "name_similarity"
                elif name_similarity >= self.fuzzy_match_threshold:
                    # Additional checks for fuzzy matches
                    if self._additional_fuzzy_checks(discovery_result, grantee):
                        match_score = name_similarity
                        match_method = "name_fuzzy"
            
            # Update best match if this is better
            if match_score > best_score:
                best_score = match_score
                best_match = {
                    "grantee_name": grantee.recipient_name,
                    "grantee_ein": grantee.recipient_ein,
                    "grant_amount": grantee.grant_amount,
                    "grant_year": grantee.grant_year,
                    "grant_purpose": grantee.grant_purpose,
                    "match_score": match_score,
                    "match_method": match_method,
                    "discovery_name": discovery_name,
                    "discovery_ein": discovery_ein
                }
        
        # Return match if score meets threshold
        if best_match and best_score >= self.fuzzy_match_threshold:
            return best_match
        
        return None
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two organization names"""
        if not name1 or not name2:
            return 0.0
        
        # Normalize names for comparison
        norm1 = self._normalize_organization_name(name1)
        norm2 = self._normalize_organization_name(name2)
        
        # Use SequenceMatcher for similarity
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        return similarity
    
    def _normalize_organization_name(self, name: str) -> str:
        """Normalize organization name for matching"""
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove common organization suffixes and prefixes
        suffixes = [
            r'\b(inc\.?|incorporated)\b',
            r'\b(llc|l\.l\.c\.?)\b',
            r'\b(corp\.?|corporation)\b',
            r'\b(ltd\.?|limited)\b',
            r'\b(co\.?|company)\b',
            r'\b(org\.?|organization)\b',
            r'\b(found\.?|foundation)\b',
            r'\b(assoc\.?|association)\b',
            r'\b(inst\.?|institute)\b',
            r'\b(soc\.?|society)\b',
            r'\b(ctr\.?|center|centre)\b'
        ]
        
        for suffix in suffixes:
            normalized = re.sub(suffix, '', normalized)
        
        # Remove extra whitespace and punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _normalize_ein(self, ein: str) -> str:
        """Normalize EIN format"""
        if not ein:
            return ""
        
        # Remove all non-digits
        digits_only = re.sub(r'\D', '', ein)
        
        # Ensure it's 9 digits
        if len(digits_only) == 9:
            return digits_only
        
        return ""
    
    def _extract_ein_from_external_data(self, discovery_result: DiscoveryResult) -> Optional[str]:
        """Extract EIN from discovery result's external data"""
        if not discovery_result.external_data:
            return None
        
        # Check various possible EIN field names
        ein_fields = ['ein', 'EIN', 'tax_id', 'taxid', 'federal_tax_id']
        
        for field in ein_fields:
            if field in discovery_result.external_data:
                ein = discovery_result.external_data[field]
                if ein:
                    return str(ein).strip()
        
        return None
    
    def _additional_fuzzy_checks(self, discovery_result: DiscoveryResult, grantee: ScheduleIGrantee) -> bool:
        """Additional checks for fuzzy matches to reduce false positives"""
        
        # Check if both names contain similar key words
        discovery_words = set(self._normalize_organization_name(discovery_result.organization_name).split())
        grantee_words = set(self._normalize_organization_name(grantee.recipient_name).split())
        
        # Remove common words
        common_words = {'the', 'of', 'for', 'and', 'in', 'to', 'a', 'an', 'at', 'by', 'on'}
        discovery_words -= common_words
        grantee_words -= common_words
        
        # Check if there's significant word overlap
        if discovery_words and grantee_words:
            overlap = len(discovery_words & grantee_words)
            min_words = min(len(discovery_words), len(grantee_words))
            
            if min_words > 0:
                overlap_ratio = overlap / min_words
                return overlap_ratio >= 0.5  # At least 50% word overlap
        
        return False


def apply_schedule_i_fast_tracking(
    discovery_results: List[DiscoveryResult],
    profile: OrganizationProfile
) -> List[DiscoveryResult]:
    """
    Convenience function to apply Schedule I grantee fast-tracking to discovery results.
    
    Args:
        discovery_results: List of discovered opportunities
        profile: Organization profile containing Schedule I grantees
        
    Returns:
        Updated discovery results with grantee matches identified and fast-tracked
    """
    matcher = GranteeMatcher()
    return matcher.match_discovery_results_against_grantees(discovery_results, profile)