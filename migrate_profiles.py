#!/usr/bin/env python3
"""
Profile Migration Script
Updates existing profiles to include new discovery tracking fields
"""

import json
import os
from pathlib import Path
from datetime import datetime

def migrate_profile(profile_path):
    """Add discovery tracking fields to a profile if they don't exist"""
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        
        # Check if profile already has discovery fields
        if 'last_discovery_date' in profile_data:
            print(f"Profile {profile_data.get('name', 'Unknown')} already migrated")
            return False
        
        # Add new discovery tracking fields with defaults
        profile_data.update({
            'last_discovery_date': None,
            'discovery_count': 0,
            'discovery_status': 'never_run',
            'next_recommended_discovery': None,
            'opportunities_count': 0
        })
        
        # Update the updated_at timestamp
        profile_data['updated_at'] = datetime.now().isoformat()
        
        # Write back to file
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        print(f"MIGRATED: {profile_data.get('name', 'Unknown')}")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to migrate {profile_path}: {e}")
        return False

def main():
    """Run the migration on all existing profiles"""
    profiles_dir = Path("data/profiles/profiles")
    
    if not profiles_dir.exists():
        print("❌ Profiles directory not found!")
        return
    
    profile_files = list(profiles_dir.glob("*.json"))
    
    if not profile_files:
        print("No profiles found to migrate")
        return
    
    print(f"Found {len(profile_files)} profiles to migrate...")
    
    migrated_count = 0
    
    for profile_file in profile_files:
        if migrate_profile(profile_file):
            migrated_count += 1
    
    print(f"\nSUCCESS: Migration complete! Migrated {migrated_count}/{len(profile_files)} profiles")

if __name__ == "__main__":
    main()