#!/usr/bin/env python3
"""
Migration script to move Heros Bridge profile from JSON archive to SQLite database
Fixes the "Run All Tracks" issue by ensuring profile exists in active database
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

from database.database_manager import DatabaseManager, Profile

def load_heros_bridge_profile():
    """Load Heros Bridge profile from JSON archive"""
    profile_path = Path("data/archive/legacy_profiles/20250829_225103/profiles/profile_f3adef3b653c.json")
    
    if not profile_path.exists():
        raise FileNotFoundError(f"Heros Bridge profile not found at {profile_path}")
    
    with open(profile_path, 'r') as f:
        profile_data = json.load(f)
    
    return profile_data

def convert_json_to_profile(json_data):
    """Convert JSON profile data to Profile dataclass"""
    
    # Handle datetime fields
    created_at = None
    updated_at = None
    last_discovery_date = None
    
    if json_data.get('created_at'):
        created_at = datetime.fromisoformat(json_data['created_at'].replace('Z', '+00:00')) if 'Z' in json_data['created_at'] else datetime.fromisoformat(json_data['created_at'])
    
    if json_data.get('updated_at'):
        updated_at = datetime.fromisoformat(json_data['updated_at'].replace('Z', '+00:00')) if 'Z' in json_data['updated_at'] else datetime.fromisoformat(json_data['updated_at'])
        
    if json_data.get('last_discovery_date'):
        last_discovery_date = datetime.fromisoformat(json_data['last_discovery_date'].replace('Z', '+00:00')) if 'Z' in json_data['last_discovery_date'] else datetime.fromisoformat(json_data['last_discovery_date'])
    
    # Create Profile object
    profile = Profile(
        id=json_data.get('profile_id', 'profile_f3adef3b653c'),
        name=json_data.get('name', ''),
        organization_type=json_data.get('organization_type', 'nonprofit'),
        ein=json_data.get('ein'),
        mission_statement=json_data.get('mission_statement'),
        status='active',  # Ensure active status
        keywords=json_data.get('keywords', ''),
        focus_areas=json_data.get('focus_areas', []),
        program_areas=json_data.get('program_areas', []),
        target_populations=json_data.get('target_populations', []),
        ntee_codes=json_data.get('ntee_codes', []),
        government_criteria=json_data.get('government_criteria', []),
        geographic_scope=json_data.get('geographic_scope', {}),
        service_areas=json_data.get('service_areas', []),
        funding_preferences=json_data.get('funding_preferences', {}),
        annual_revenue=json_data.get('annual_revenue'),
        form_type=json_data.get('form_type'),
        foundation_grants=json_data.get('foundation_grants', []),
        board_members=json_data.get('foundation_board_members', []),
        discovery_count=json_data.get('discovery_count', 0),
        opportunities_count=json_data.get('opportunities_count', 0),
        last_discovery_date=last_discovery_date,
        performance_metrics=json_data.get('metrics', {}),
        created_at=created_at,
        updated_at=updated_at,
        processing_history=json_data.get('processing_history', [])
    )
    
    return profile

def main():
    """Main migration function"""
    print("Starting Heros Bridge profile migration...")
    
    try:
        # Initialize database
        db_manager = DatabaseManager("data/catalynx.db")
        print("SUCCESS: Database connection established")
        
        # Initialize database if needed (done automatically in constructor)
        print("SUCCESS: Database schema verified")
        
        # Load JSON profile
        json_data = load_heros_bridge_profile()
        print("SUCCESS: Heros Bridge JSON profile loaded")
        print(f"   - Name: {json_data.get('name')}")
        print(f"   - EIN: {json_data.get('ein')}")
        print(f"   - Opportunities: {json_data.get('opportunities_count', 0)}")
        
        # Convert to Profile dataclass
        profile = convert_json_to_profile(json_data)
        print("SUCCESS: Profile data converted")
        
        # Check if profile already exists
        existing_profile = db_manager.get_profile(profile.id)
        if existing_profile:
            print(f"WARNING: Profile {profile.id} already exists in database")
            print("INFO: Automatically overwriting existing profile for migration")
            
            # Delete existing profile
            success = db_manager.delete_profile(profile.id)
            if success:
                print("SUCCESS: Existing profile deleted")
            else:
                print("ERROR: Failed to delete existing profile")
                return False
        
        # Create profile in database
        success = db_manager.create_profile(profile)
        if success:
            print("SUCCESS: Profile migrated to database successfully")
            
            # Verify migration
            migrated_profile = db_manager.get_profile(profile.id)
            if migrated_profile:
                print("SUCCESS: Migration verified - profile accessible in database")
                print(f"   - Database ID: {migrated_profile.id}")
                print(f"   - Database Name: {migrated_profile.name}")
                print(f"   - Database EIN: {migrated_profile.ein}")
                return True
            else:
                print("ERROR: Migration verification failed")
                return False
        else:
            print("ERROR: Failed to migrate profile to database")
            return False
            
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\nSUCCESS: Heros Bridge profile migration completed successfully!")
        print("   The 'Run All Tracks' button should now work properly.")
    else:
        print("\nERROR: Migration failed. Please check the error messages above.")
        sys.exit(1)