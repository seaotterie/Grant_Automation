#!/usr/bin/env python3
"""
Organization Name Similarity Service
Extracted from monolithic main.py for better modularity and testing
"""

from typing import List, Dict, Any, Optional
import re


def similar_organization_names(name1: str, name2: str, threshold: float = 0.85) -> bool:
    """
    Check if two organization names are similar enough to be considered the same organization.
    Handles common variations like Heroes/Heros, Inc/Inc., etc.
    
    Args:
        name1: First organization name
        name2: Second organization name
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        True if names are similar enough to be considered the same organization
    """
    if not name1 or not name2:
        return False
        
    # Normalize names for comparison
    def normalize_name(name: str) -> str:
        name = name.lower().strip()
        # Remove common suffixes and variations
        suffixes = [' inc', ' inc.', ' incorporated', ' llc', ' ltd', ' ltd.', ' corp', ' corp.', ' corporation']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()
        return name
    
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)
    
    # Exact match after normalization
    if norm1 == norm2:
        return True
    
    # Simple character-based similarity for fuzzy matching
    # This handles cases like "Heroes Bridge" vs "Heros Bridge"
    shorter = norm1 if len(norm1) <= len(norm2) else norm2
    longer = norm2 if shorter == norm1 else norm1
    
    if len(shorter) == 0:
        return False
    
    # Calculate character overlap
    matches = 0
    for char in shorter:
        if char in longer:
            matches += 1
            longer = longer.replace(char, '', 1)  # Remove matched character
    
    similarity = matches / len(shorter)
    return similarity >= threshold


def normalize_organization_name(name: str) -> str:
    """
    Normalize organization name for consistent comparison and storage.
    
    Args:
        name: Organization name to normalize
        
    Returns:
        Normalized organization name
    """
    if not name:
        return ""
    
    # Basic cleanup
    normalized = name.strip()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Standardize common abbreviations
    abbreviations = {
        r'\bInc\.?\b': 'Inc',
        r'\bIncorporated\b': 'Inc', 
        r'\bLLC\b': 'LLC',
        r'\bLtd\.?\b': 'Ltd',
        r'\bLimited\b': 'Ltd',
        r'\bCorp\.?\b': 'Corp',
        r'\bCorporation\b': 'Corp',
        r'\bFoundation\b': 'Foundation',
        r'\bFdn\.?\b': 'Foundation',
        r'\bAssociation\b': 'Association',
        r'\bAssn\.?\b': 'Association'
    }
    
    for pattern, replacement in abbreviations.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    
    return normalized


def find_similar_organizations(target_name: str, organization_list: List[Dict[str, Any]], 
                              name_field: str = "organization_name", 
                              threshold: float = 0.85) -> List[Dict[str, Any]]:
    """
    Find organizations with similar names from a list.
    
    Args:
        target_name: Name to search for
        organization_list: List of organization dictionaries
        name_field: Field name containing the organization name
        threshold: Similarity threshold
        
    Returns:
        List of similar organizations with similarity scores
    """
    if not target_name or not organization_list:
        return []
    
    similar_orgs = []
    
    for org in organization_list:
        if name_field not in org:
            continue
            
        org_name = org[name_field]
        if similar_organization_names(target_name, org_name, threshold):
            # Calculate exact similarity score for ranking
            norm_target = normalize_organization_name(target_name).lower()
            norm_org = normalize_organization_name(org_name).lower()
            
            # Simple character-based similarity calculation
            shorter = norm_target if len(norm_target) <= len(norm_org) else norm_org
            longer = norm_org if shorter == norm_target else norm_target
            
            if len(shorter) > 0:
                matches = sum(1 for c in shorter if c in longer)
                similarity_score = matches / len(shorter)
            else:
                similarity_score = 0.0
            
            similar_orgs.append({
                **org,
                "similarity_score": similarity_score,
                "matched_name": org_name
            })
    
    # Sort by similarity score (descending)
    similar_orgs.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    return similar_orgs


def detect_duplicate_organizations(organizations: List[Dict[str, Any]], 
                                 name_field: str = "organization_name",
                                 threshold: float = 0.90) -> List[List[Dict[str, Any]]]:
    """
    Detect groups of potentially duplicate organizations.
    
    Args:
        organizations: List of organization dictionaries
        name_field: Field name containing the organization name
        threshold: Similarity threshold for considering duplicates
        
    Returns:
        List of groups, where each group contains potentially duplicate organizations
    """
    if not organizations:
        return []
    
    duplicate_groups = []
    processed_indices = set()
    
    for i, org1 in enumerate(organizations):
        if i in processed_indices or name_field not in org1:
            continue
            
        current_group = [org1]
        processed_indices.add(i)
        
        for j, org2 in enumerate(organizations[i+1:], start=i+1):
            if j in processed_indices or name_field not in org2:
                continue
                
            if similar_organization_names(org1[name_field], org2[name_field], threshold):
                current_group.append(org2)
                processed_indices.add(j)
        
        # Only include groups with more than one organization
        if len(current_group) > 1:
            duplicate_groups.append(current_group)
    
    return duplicate_groups


# Service class for dependency injection
class SimilarityService:
    """Service class for organization name similarity operations"""
    
    def __init__(self, default_threshold: float = 0.85):
        self.default_threshold = default_threshold
    
    def are_similar(self, name1: str, name2: str, threshold: Optional[float] = None) -> bool:
        """Check if two organization names are similar"""
        threshold = threshold or self.default_threshold
        return similar_organization_names(name1, name2, threshold)
    
    def normalize_name(self, name: str) -> str:
        """Normalize organization name"""
        return normalize_organization_name(name)
    
    def find_similar(self, target_name: str, organizations: List[Dict[str, Any]], 
                    name_field: str = "organization_name", 
                    threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Find similar organizations from a list"""
        threshold = threshold or self.default_threshold
        return find_similar_organizations(target_name, organizations, name_field, threshold)
    
    def detect_duplicates(self, organizations: List[Dict[str, Any]], 
                         name_field: str = "organization_name",
                         threshold: Optional[float] = None) -> List[List[Dict[str, Any]]]:
        """Detect duplicate organizations"""
        threshold = threshold or self.default_threshold
        return detect_duplicate_organizations(organizations, name_field, threshold)


# Global service instance
_similarity_service = None

def get_similarity_service() -> SimilarityService:
    """Get the global similarity service instance"""
    global _similarity_service
    if _similarity_service is None:
        _similarity_service = SimilarityService()
    return _similarity_service