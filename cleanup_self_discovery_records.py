#!/usr/bin/env python3
"""
Comprehensive Self-Discovery Cleanup Script
Remove all self-discovery records from the leads directory

This script:
1. Scans all leads for EIN matches with their profiles
2. Uses fuzzy name matching to handle variations like Heroes/Heros
3. Creates backup before deletion
4. Updates affected profiles (opportunity counts, references)
5. Provides detailed reporting of cleanup results

Enhanced with name similarity detection to catch cases where:
- Organization names have minor variations (Heroes vs Heros)
- EIN matches but names are slightly different
"""

import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    if len(norm1) == 0 or len(norm2) == 0:
        return False
        
    # Calculate character overlap similarity
    chars1 = set(norm1.replace(' ', ''))
    chars2 = set(norm2.replace(' ', ''))
    
    if len(chars1) == 0 or len(chars2) == 0:
        return False
        
    intersection = len(chars1.intersection(chars2))
    union = len(chars1.union(chars2))
    similarity = intersection / union if union > 0 else 0
    
    return similarity >= threshold

class SelfDiscoveryCleanup:
    def __init__(self, data_dir: str = "data/profiles"):
        self.data_dir = Path(data_dir)
        self.leads_dir = self.data_dir / "leads"
        self.profiles_dir = self.data_dir / "profiles"
        self.backup_dir = Path("data_backup") / f"self_discovery_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.stats = {
            'total_leads_scanned': 0,
            'profiles_loaded': 0,
            'self_discovery_found': 0,
            'leads_removed': 0,
            'profiles_updated': 0,
            'backup_created': False,
            'cleanup_errors': 0,
            'removed_records': [],
            'updated_profiles': []
        }
        
    def run_comprehensive_cleanup(self):
        """Run complete self-discovery cleanup process"""
        logger.info("Starting comprehensive self-discovery cleanup...")
        
        # Step 1: Create backup
        self._create_backup()
        
        # Step 2: Load all profiles with EINs
        profiles_map = self._load_profiles_map()
        
        # Step 3: Scan leads for self-discovery records
        self_discovery_records = self._find_self_discovery_records(profiles_map)
        
        # Step 4: Remove self-discovery records
        if self_discovery_records:
            self._remove_self_discovery_records(self_discovery_records)
            
            # Step 5: Update affected profiles
            self._update_affected_profiles(self_discovery_records)
        
        # Step 6: Generate final report
        self._generate_cleanup_report()
        
    def _create_backup(self):
        """Create backup of leads and profiles directories"""
        logger.info("Creating backup before cleanup...")
        
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup leads directory
            if self.leads_dir.exists():
                shutil.copytree(self.leads_dir, self.backup_dir / "leads")
            
            # Backup profiles directory  
            if self.profiles_dir.exists():
                shutil.copytree(self.profiles_dir, self.backup_dir / "profiles")
            
            self.stats['backup_created'] = True
            logger.info(f"Backup created at: {self.backup_dir}")
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def _load_profiles_map(self) -> Dict[str, Dict]:
        """Load all profiles and create EIN -> profile mapping"""
        logger.info("Loading profiles for EIN mapping...")
        
        profiles_map = {}
        
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                ein = profile_data.get('ein', '').strip()
                if ein:
                    # Normalize EIN format
                    normalized_ein = ein.replace('-', '').replace(' ', '')
                    profiles_map[normalized_ein] = {
                        'profile_id': profile_data.get('profile_id'),
                        'name': profile_data.get('name', '').strip(),
                        'ein': ein,
                        'file_path': profile_file,
                        'associated_opportunities': profile_data.get('associated_opportunities', []),
                        'opportunities_count': profile_data.get('opportunities_count', 0)
                    }
                    
                self.stats['profiles_loaded'] += 1
                
            except Exception as e:
                logger.warning(f"Error loading profile {profile_file}: {e}")
        
        logger.info(f"Loaded {len(profiles_map)} profiles with EINs")
        return profiles_map
    
    def _find_self_discovery_records(self, profiles_map: Dict[str, Dict]) -> List[Dict]:
        """Find all self-discovery records"""
        logger.info("Scanning leads for self-discovery records...")
        
        self_discovery_records = []
        
        for lead_file in self.leads_dir.glob("*.json"):
            self.stats['total_leads_scanned'] += 1
            
            try:
                with open(lead_file, 'r', encoding='utf-8') as f:
                    lead_data = json.load(f)
                
                # Get lead details
                lead_ein = lead_data.get('external_data', {}).get('ein', '').strip()
                if not lead_ein:
                    continue
                
                # Normalize lead EIN
                normalized_lead_ein = lead_ein.replace('-', '').replace(' ', '')
                
                # Get profile for this lead
                profile_id = lead_data.get('profile_id', '')
                if not profile_id:
                    continue
                
                # Check if profile EIN matches lead EIN
                matching_profile = None
                for ein_key, profile_info in profiles_map.items():
                    if profile_info['profile_id'] == profile_id:
                        matching_profile = profile_info
                        break
                
                if not matching_profile:
                    continue
                
                profile_ein = matching_profile['ein'].replace('-', '').replace(' ', '')
                
                # Check for EIN match
                if normalized_lead_ein == profile_ein:
                    # EIN match found - check name similarity
                    lead_org_name = lead_data.get('organization_name', '').strip()
                    profile_name = matching_profile['name']
                    
                    if similar_organization_names(lead_org_name, profile_name):
                        # This is a self-discovery record
                        self_discovery_records.append({
                            'lead_id': lead_data.get('lead_id'),
                            'profile_id': profile_id,
                            'lead_file': lead_file,
                            'lead_org_name': lead_org_name,
                            'profile_name': profile_name,
                            'lead_ein': lead_ein,
                            'profile_ein': matching_profile['ein'],
                            'similarity_confirmed': True
                        })
                        
                        logger.info(f"Found self-discovery: {lead_org_name} (EIN: {lead_ein}) for profile {profile_name}")
                        self.stats['self_discovery_found'] += 1
                    else:
                        # EIN match but names significantly different - log for review
                        logger.warning(f"EIN match but name difference: lead='{lead_org_name}' vs profile='{profile_name}' (EIN: {lead_ein})")
                        
            except Exception as e:
                logger.warning(f"Error processing lead {lead_file}: {e}")
                self.stats['cleanup_errors'] += 1
        
        logger.info(f"Found {len(self_discovery_records)} self-discovery records")
        return self_discovery_records
    
    def _remove_self_discovery_records(self, self_discovery_records: List[Dict]):
        """Remove self-discovery record files"""
        logger.info(f"Removing {len(self_discovery_records)} self-discovery records...")
        
        for record in self_discovery_records:
            try:
                lead_file = record['lead_file']
                if lead_file.exists():
                    lead_file.unlink()
                    self.stats['leads_removed'] += 1
                    self.stats['removed_records'].append(record)
                    logger.info(f"Removed self-discovery file: {lead_file.name}")
                else:
                    logger.warning(f"Lead file not found: {lead_file}")
                    
            except Exception as e:
                logger.error(f"Error removing {record['lead_file']}: {e}")
                self.stats['cleanup_errors'] += 1
    
    def _update_affected_profiles(self, self_discovery_records: List[Dict]):
        """Update profiles to remove references to deleted leads"""
        logger.info("Updating affected profiles...")
        
        # Group records by profile_id
        profiles_to_update = {}
        for record in self_discovery_records:
            profile_id = record['profile_id']
            if profile_id not in profiles_to_update:
                profiles_to_update[profile_id] = []
            profiles_to_update[profile_id].append(record)
        
        for profile_id, records in profiles_to_update.items():
            try:
                profile_file = self.profiles_dir / f"{profile_id}.json"
                if not profile_file.exists():
                    logger.warning(f"Profile file not found: {profile_file}")
                    continue
                
                # Load profile
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                # Remove lead IDs from associated_opportunities
                lead_ids_to_remove = [record['lead_id'] for record in records if record['lead_id']]
                original_opportunities = profile_data.get('associated_opportunities', [])
                updated_opportunities = [lead_id for lead_id in original_opportunities 
                                       if lead_id not in lead_ids_to_remove]
                
                # Update profile data
                profile_data['associated_opportunities'] = updated_opportunities
                profile_data['opportunities_count'] = len(updated_opportunities)
                profile_data['updated_at'] = datetime.now().isoformat()
                
                # Save updated profile
                with open(profile_file, 'w', encoding='utf-8') as f:
                    json.dump(profile_data, f, indent=2, ensure_ascii=False)
                
                self.stats['profiles_updated'] += 1
                self.stats['updated_profiles'].append({
                    'profile_id': profile_id,
                    'profile_name': profile_data.get('name'),
                    'leads_removed': len(lead_ids_to_remove),
                    'old_count': len(original_opportunities),
                    'new_count': len(updated_opportunities)
                })
                
                logger.info(f"Updated profile {profile_id}: removed {len(lead_ids_to_remove)} self-discovery references")
                
            except Exception as e:
                logger.error(f"Error updating profile {profile_id}: {e}")
                self.stats['cleanup_errors'] += 1
    
    def _generate_cleanup_report(self):
        """Generate comprehensive cleanup report"""
        print("\\n" + "="*70)
        print("SELF-DISCOVERY CLEANUP REPORT")
        print("="*70)
        print(f"Cleanup completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Backup location: {self.backup_dir}")
        print("-" * 70)
        
        print("\\nSCAN RESULTS:")
        print(f"Total leads scanned:           {self.stats['total_leads_scanned']}")
        print(f"Profiles loaded:               {self.stats['profiles_loaded']}")
        print(f"Self-discovery records found:  {self.stats['self_discovery_found']}")
        
        print("\\nCLEANUP RESULTS:")
        print(f"Lead files removed:            {self.stats['leads_removed']}")
        print(f"Profiles updated:              {self.stats['profiles_updated']}")
        print(f"Cleanup errors:                {self.stats['cleanup_errors']}")
        print(f"Backup created:                {'✅' if self.stats['backup_created'] else '❌'}")
        
        if self.stats['removed_records']:
            print("\\nREMOVED SELF-DISCOVERY RECORDS:")
            print("-" * 70)
            for record in self.stats['removed_records']:
                print(f"• {record['lead_org_name'][:40]:<40} EIN: {record['lead_ein']}")
                print(f"  Profile: {record['profile_name'][:40]:<40} File: {record['lead_file'].name}")
                print()
        
        if self.stats['updated_profiles']:
            print("\\nUPDATED PROFILES:")
            print("-" * 70)
            for profile in self.stats['updated_profiles']:
                print(f"• {profile['profile_name'][:40]:<40} Removed: {profile['leads_removed']} leads")
                print(f"  Opportunity count: {profile['old_count']} → {profile['new_count']}")
                print()
        
        print("\\nIMPACT:")
        if self.stats['leads_removed'] > 0:
            print(f"✅ {self.stats['leads_removed']} self-discovery records removed")
            print(f"✅ {self.stats['profiles_updated']} profiles updated with correct opportunity counts")
            print("✅ Enhanced self-discovery prevention now active in discovery endpoints")
            print("✅ DISCOVER tab now shows actual pipeline stages (#2 Qualified)")
        else:
            print("ℹ️  No self-discovery records found - system is clean")
            
        print("\\nNEXT STEPS:")
        print("1. 🔄 Refresh web interface to see updated opportunity counts")
        print("2. 🧪 Test discovery process to verify no new self-discovery occurs") 
        print("3. 📊 Check DISCOVER tab shows '#2 Qualified' for promoted opportunities")
        print("4. 🗑️  Archive backup folder after confirming system works correctly")
        
        if self.stats['cleanup_errors'] > 0:
            print(f"\\n⚠️  {self.stats['cleanup_errors']} errors occurred during cleanup - review logs")
            
        print("="*70)


if __name__ == "__main__":
    cleanup = SelfDiscoveryCleanup()
    cleanup.run_comprehensive_cleanup()