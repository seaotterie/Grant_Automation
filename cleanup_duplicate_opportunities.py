#!/usr/bin/env python3
"""
Cleanup Script for Duplicate Opportunities

This script identifies and removes duplicate opportunities using the same
enhanced deduplication logic implemented in UnifiedDiscoveryAdapter.

Usage:
    python cleanup_duplicate_opportunities.py --profile-id profile_f3adef3b653c --dry-run
    python cleanup_duplicate_opportunities.py --profile-id profile_f3adef3b653c --execute
"""

import sys
import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any

sys.path.append('.')

from src.profiles.unified_service import get_unified_profile_service
from src.discovery.unified_discovery_adapter import get_unified_discovery_adapter

def clean_org_name(name: str) -> str:
    """Clean organization name for better duplicate detection (same as adapter)"""
    # Convert to lowercase and strip
    name = name.lower().strip()
    
    # Remove common organizational suffixes
    suffixes = [
        r'\b(inc\.?|incorporated)\b',
        r'\b(llc\.?|l\.l\.c\.?)\b',
        r'\b(corp\.?|corporation)\b',
        r'\b(ltd\.?|limited)\b',
        r'\b(foundation|fund)\b',
        r'\b(org\.?|organization)\b',
        r'\b(assoc\.?|association)\b',
        r'\b(inst\.?|institute)\b',
        r'\b(center|centre)\b',
        r'\b(society|soc\.?)\b',
        r'\b(trust|company|co\.?)\b'
    ]
    
    for suffix in suffixes:
        name = re.sub(suffix, '', name).strip()
    
    # Remove extra whitespace and punctuation
    name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
    name = re.sub(r'\s+', ' ', name)     # Normalize whitespace
    
    return name.strip()

def calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two organization names using Levenshtein distance"""
    if not name1 or not name2:
        return 0.0
    
    if name1 == name2:
        return 1.0
    
    # Simple character-based similarity calculation
    def levenshtein_distance(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    max_len = max(len(name1), len(name2))
    if max_len == 0:
        return 1.0
    
    distance = levenshtein_distance(name1, name2)
    similarity = 1.0 - (distance / max_len)
    
    return max(0.0, similarity)

def find_duplicates(opportunities: List[Any]) -> Dict[str, List[Any]]:
    """Find duplicate opportunities using enhanced detection logic"""
    duplicate_groups = {}
    processed = set()
    
    for i, opp in enumerate(opportunities):
        if i in processed:
            continue
            
        duplicates = [opp]
        processed.add(i)
        
        for j, other_opp in enumerate(opportunities[i+1:], i+1):
            if j in processed:
                continue
                
            is_duplicate = False
            duplicate_reason = None
            
            # Method 1: Exact EIN match (most reliable)
            if (opp.ein and other_opp.ein and opp.ein == other_opp.ein):
                duplicate_reason = "duplicate_by_ein"
                is_duplicate = True
            
            # Method 2: Exact organization name match (case-insensitive)
            elif (opp.organization_name and other_opp.organization_name and
                  opp.organization_name.lower().strip() == other_opp.organization_name.lower().strip()):
                duplicate_reason = "duplicate_by_name"
                is_duplicate = True
            
            # Method 3: Fuzzy name matching for similar organizations
            elif (opp.organization_name and other_opp.organization_name):
                name1 = opp.organization_name.lower().strip()
                name2 = other_opp.organization_name.lower().strip()
                
                # Remove common suffixes/prefixes for comparison
                name1_clean = clean_org_name(name1)
                name2_clean = clean_org_name(name2)
                
                # Check for high similarity (>= 85% match)
                similarity = calculate_name_similarity(name1_clean, name2_clean)
                if similarity >= 0.85:
                    duplicate_reason = f"duplicate_by_fuzzy_name_similarity_{similarity:.2f}"
                    is_duplicate = True
            
            # Method 4: Cross-source duplicate detection
            elif (opp.organization_name and other_opp.organization_name and
                  opp.source != other_opp.source and
                  opp.organization_name.lower().strip() == other_opp.organization_name.lower().strip()):
                duplicate_reason = "duplicate_cross_source"
                is_duplicate = True
            
            if is_duplicate:
                duplicates.append(other_opp)
                processed.add(j)
        
        if len(duplicates) > 1:
            # Use organization name as key for the group
            key = f"{opp.organization_name}_group_{len(duplicate_groups)}"
            duplicate_groups[key] = {
                'opportunities': duplicates,
                'count': len(duplicates),
                'reason': duplicate_reason or 'multiple_criteria'
            }
    
    return duplicate_groups

def cleanup_duplicates(profile_id: str, dry_run: bool = True):
    """Clean up duplicate opportunities for a profile"""
    print(f"=== Cleaning up duplicates for profile: {profile_id} ===")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    
    # Get unified service
    unified_service = get_unified_profile_service()
    
    # Get all opportunities
    opportunities = unified_service.get_profile_opportunities(profile_id)
    
    if not opportunities:
        print(f"No opportunities found for profile {profile_id}")
        return
    
    print(f"Found {len(opportunities)} total opportunities")
    
    # Find duplicates
    duplicate_groups = find_duplicates(opportunities)
    
    if not duplicate_groups:
        print("No duplicates found!")
        return
    
    print(f"\nFound {len(duplicate_groups)} duplicate groups:")
    
    total_duplicates_to_remove = 0
    
    for group_key, group_data in duplicate_groups.items():
        duplicates = group_data['opportunities']
        count = group_data['count']
        reason = group_data['reason']
        
        print(f"\n--- Duplicate Group: {group_key} ---")
        print(f"   Reason: {reason}")
        print(f"   Count: {count} duplicates")
        print(f"   Organization: {duplicates[0].organization_name}")
        
        # Show all duplicates
        for i, dup in enumerate(duplicates):
            print(f"     {i+1}. ID: {dup.opportunity_id}")
            print(f"        Stage: {dup.current_stage}")
            print(f"        EIN: {dup.ein}")
            print(f"        Source: {dup.source}")
            print(f"        Discovered: {dup.discovered_at}")
        
        # Keep the best one (highest stage, newest)
        # Sort by stage priority and discovery date
        stage_priority = {"recommendations": 4, "deep_analysis": 3, "pre_scoring": 2, "discovery": 1}
        
        sorted_duplicates = sorted(duplicates, key=lambda x: (
            stage_priority.get(x.current_stage, 0),
            x.discovered_at or "1900-01-01"
        ), reverse=True)
        
        keep = sorted_duplicates[0]
        remove = sorted_duplicates[1:]
        
        print(f"   KEEP: {keep.opportunity_id} (stage: {keep.current_stage}, discovered: {keep.discovered_at})")
        print(f"   REMOVE: {len(remove)} duplicates")
        
        total_duplicates_to_remove += len(remove)
        
        if not dry_run:
            # Actually remove the duplicates
            for dup_to_remove in remove:
                print(f"      Removing: {dup_to_remove.opportunity_id}")
                try:
                    # Remove the opportunity file directly - handle different naming patterns
                    opp_id = dup_to_remove.opportunity_id
                    
                    # Try different file naming patterns
                    file_patterns = [
                        f"data/profiles/{profile_id}/opportunities/{opp_id}.json",
                        f"data/profiles/{profile_id}/opportunities/opportunity_{opp_id}.json",
                        f"data/profiles/{profile_id}/opportunities/opportunity_{opp_id.replace('opp_', '')}.json",
                        f"data/profiles/{profile_id}/opportunities/opportunity_{opp_id.replace('opp_lead_', '')}.json",
                        f"data/profiles/{profile_id}/opportunities/opportunity_{opp_id.replace('opp_test_', '')}.json"
                    ]
                    
                    opp_file = None
                    for pattern in file_patterns:
                        test_file = Path(pattern)
                        if test_file.exists():
                            opp_file = test_file
                            break
                    if opp_file and opp_file.exists():
                        opp_file.unlink()
                        print(f"        Deleted file: {opp_file}")
                    else:
                        print(f"        File not found for ID: {opp_id}")
                except Exception as e:
                    print(f"        ERROR removing {dup_to_remove.opportunity_id}: {e}")
    
    print(f"\nSummary:")
    print(f"  Total opportunities: {len(opportunities)}")
    print(f"  Duplicate groups: {len(duplicate_groups)}")
    print(f"  Duplicates to remove: {total_duplicates_to_remove}")
    print(f"  Opportunities after cleanup: {len(opportunities) - total_duplicates_to_remove}")
    
    if dry_run:
        print(f"\nThis was a DRY RUN. Use --execute to actually remove duplicates.")
    else:
        print(f"\nDuplicates have been removed.")

def main():
    parser = argparse.ArgumentParser(description='Clean up duplicate opportunities')
    parser.add_argument('--profile-id', required=True, help='Profile ID to clean up')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be removed without actually removing')
    parser.add_argument('--execute', action='store_true', help='Actually remove duplicates')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.execute:
        print("ERROR: Must specify either --dry-run or --execute")
        sys.exit(1)
    
    if args.dry_run and args.execute:
        print("ERROR: Cannot specify both --dry-run and --execute")
        sys.exit(1)
    
    try:
        cleanup_duplicates(args.profile_id, dry_run=args.dry_run)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()