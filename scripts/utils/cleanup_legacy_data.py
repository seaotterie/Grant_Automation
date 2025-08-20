#!/usr/bin/env python3
"""
Legacy Data Cleanup Script
Comprehensive cleanup of corrupt and duplicate opportunity data

This script:
1. Removes leads with empty organization names
2. Removes low-scoring unified_discovery_foundation records  
3. Deduplicates remaining records
4. Updates profile references and counts
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Set
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LegacyDataCleanup:
    def __init__(self, data_dir: str = "data/profiles"):
        self.data_dir = Path(data_dir)
        self.profiles_dir = self.data_dir / "profiles"
        self.leads_dir = self.data_dir / "leads"
        
        self.stats = {
            'total_leads_before': 0,
            'empty_names_removed': 0,
            'low_score_foundation_removed': 0,
            'duplicates_removed': 0,
            'total_leads_after': 0,
            'profiles_updated': 0
        }
        
    def run_cleanup(self):
        """Run complete cleanup process"""
        logger.info("Starting legacy data cleanup...")
        
        # Get initial counts
        self.stats['total_leads_before'] = len(list(self.leads_dir.glob("*.json")))
        logger.info(f"Found {self.stats['total_leads_before']} total lead files")
        
        # Phase 1: Remove corrupt records
        self._remove_empty_organization_names()
        self._remove_low_score_foundation_records()
        
        # Phase 2: Deduplicate remaining records
        self._deduplicate_records()
        
        # Phase 3: Update profile references
        self._update_profile_references()
        
        # Final stats
        self.stats['total_leads_after'] = len(list(self.leads_dir.glob("*.json")))
        
        self._print_cleanup_summary()
        
    def _remove_empty_organization_names(self):
        """Remove all leads with empty organization names"""
        logger.info("Removing leads with empty organization names...")
        
        removed_count = 0
        for lead_file in self.leads_dir.glob("*.json"):
            try:
                with open(lead_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                org_name = data.get("organization_name", "").strip()
                
                if not org_name or org_name in ["[Organization Name Missing]", "N/A"]:
                    logger.info(f"Removing lead with empty name: {data.get('lead_id', 'unknown')} - Score: {data.get('compatibility_score', 0)}")
                    lead_file.unlink()
                    removed_count += 1
                    
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Error processing {lead_file}: {e}")
                
        self.stats['empty_names_removed'] = removed_count
        logger.info(f"Removed {removed_count} leads with empty organization names")
        
    def _remove_low_score_foundation_records(self):
        """Remove low-scoring records from unified_discovery_foundation source"""
        logger.info("Removing low-scoring unified_discovery_foundation records...")
        
        removed_count = 0
        for lead_file in self.leads_dir.glob("*.json"):
            try:
                with open(lead_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                source = data.get("source", "")
                score = data.get("compatibility_score", 0.0)
                
                if source == "unified_discovery_foundation" and score < 0.5:
                    logger.info(f"Removing low-score foundation record: {data.get('lead_id', 'unknown')} - Score: {score}")
                    lead_file.unlink()
                    removed_count += 1
                    
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Error processing {lead_file}: {e}")
                
        self.stats['low_score_foundation_removed'] = removed_count
        logger.info(f"Removed {removed_count} low-scoring foundation records")
        
    def _deduplicate_records(self):
        """Remove duplicate records based on improved logic"""
        logger.info("Deduplicating remaining records...")
        
        # Group leads by profile
        profile_leads = {}
        for lead_file in self.leads_dir.glob("*.json"):
            try:
                with open(lead_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                profile_id = data.get("profile_id")
                if profile_id not in profile_leads:
                    profile_leads[profile_id] = []
                    
                profile_leads[profile_id].append({
                    'file': lead_file,
                    'data': data
                })
                
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Error processing {lead_file}: {e}")
        
        # Deduplicate within each profile
        removed_count = 0
        for profile_id, leads in profile_leads.items():
            duplicates = self._find_duplicates_in_profile(leads)
            for duplicate_file in duplicates:
                logger.info(f"Removing duplicate: {duplicate_file.name}")
                duplicate_file.unlink()
                removed_count += 1
                
        self.stats['duplicates_removed'] = removed_count
        logger.info(f"Removed {removed_count} duplicate records")
        
    def _find_duplicates_in_profile(self, leads: List[Dict]) -> List[Path]:
        """Find duplicate leads within a profile"""
        duplicates = []
        seen_combinations = {}
        
        for lead_info in leads:
            data = lead_info['data']
            file_path = lead_info['file']
            
            # Create unique key based on organization name and EIN if available
            org_name = data.get("organization_name", "").strip().lower()
            ein = data.get("external_data", {}).get("ein", "").strip().replace("-", "")
            source = data.get("source", "")
            
            # Skip if org_name is empty (should have been removed already)
            if not org_name:
                continue
                
            # Create combination key
            key = f"{org_name}:{ein}:{source}"
            
            if key in seen_combinations:
                # This is a duplicate - keep the one with higher score
                existing_info = seen_combinations[key]
                existing_score = existing_info['data'].get("compatibility_score", 0.0)
                current_score = data.get("compatibility_score", 0.0)
                
                if current_score > existing_score:
                    # Current has better score, remove the existing one
                    duplicates.append(existing_info['file'])
                    seen_combinations[key] = lead_info
                else:
                    # Existing has better score, remove current one
                    duplicates.append(file_path)
            else:
                seen_combinations[key] = lead_info
                
        return duplicates
        
    def _update_profile_references(self):
        """Update profile associated_opportunities and counts"""
        logger.info("Updating profile references...")
        
        # Get current lead IDs for each profile
        profile_leads = {}
        for lead_file in self.leads_dir.glob("*.json"):
            try:
                with open(lead_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                profile_id = data.get("profile_id")
                lead_id = data.get("lead_id")
                
                if profile_id not in profile_leads:
                    profile_leads[profile_id] = []
                profile_leads[profile_id].append(lead_id)
                
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Error processing {lead_file}: {e}")
        
        # Update each profile
        updated_count = 0
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                profile_id = profile_data.get("profile_id")
                current_leads = profile_leads.get(profile_id, [])
                
                # Update associated_opportunities and count
                old_count = profile_data.get("opportunities_count", 0)
                profile_data["associated_opportunities"] = current_leads
                profile_data["opportunities_count"] = len(current_leads)
                profile_data["updated_at"] = datetime.now().isoformat()
                
                # Save updated profile
                with open(profile_file, 'w', encoding='utf-8') as f:
                    json.dump(profile_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Updated profile {profile_id}: {old_count} → {len(current_leads)} opportunities")
                updated_count += 1
                
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Error updating profile {profile_file}: {e}")
                
        self.stats['profiles_updated'] = updated_count
        logger.info(f"Updated {updated_count} profiles")
        
    def _print_cleanup_summary(self):
        """Print comprehensive cleanup summary"""
        print("\n" + "="*60)
        print("LEGACY DATA CLEANUP SUMMARY")
        print("="*60)
        print(f"Total leads before cleanup:      {self.stats['total_leads_before']}")
        print(f"Empty organization names removed: {self.stats['empty_names_removed']}")
        print(f"Low-score foundation removed:     {self.stats['low_score_foundation_removed']}")
        print(f"Duplicate records removed:        {self.stats['duplicates_removed']}")
        print("-" * 60)
        print(f"Total records removed:            {self.stats['empty_names_removed'] + self.stats['low_score_foundation_removed'] + self.stats['duplicates_removed']}")
        print(f"Total leads after cleanup:        {self.stats['total_leads_after']}")
        print(f"Profiles updated:                 {self.stats['profiles_updated']}")
        print("-" * 60)
        
        reduction_pct = ((self.stats['total_leads_before'] - self.stats['total_leads_after']) / self.stats['total_leads_before'] * 100) if self.stats['total_leads_before'] > 0 else 0
        print(f"Data reduction:                   {reduction_pct:.1f}%")
        print("="*60)
        
        # Recommendations
        print("\nRECOMMENDATIONS:")
        if self.stats['total_leads_after'] < 100:
            print("✅ Dataset size is now manageable")
        if self.stats['empty_names_removed'] > 0:
            print("✅ Removed all corrupt empty-name records")
        if self.stats['duplicates_removed'] > 0:
            print("✅ Deduplicated successfully")
        print("🔄 Next: Run auto-promotion to advance high-scoring opportunities")


if __name__ == "__main__":
    cleanup = LegacyDataCleanup()
    cleanup.run_cleanup()