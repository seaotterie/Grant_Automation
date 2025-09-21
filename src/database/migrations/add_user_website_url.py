#!/usr/bin/env python3
"""
Database Migration: Add User Website URL to Profiles
Adds website_url field to profiles table for user-provided organization websites
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

def migrate_add_user_website_url(db_path: str = "data/catalynx.db") -> bool:
    """
    Add website_url field to profiles table for user-provided organization websites.
    
    This supports the new data source hierarchy:
    1. Primary: User-provided website URL
    2. Secondary: 990/990-PF declared website  
    3. Tertiary: GPT-predicted URLs
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(profiles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'website_url' in columns:
            logger.info("Column 'website_url' already exists in profiles table")
            conn.close()
            return True
        
        # Add the website_url column
        logger.info("Adding website_url column to profiles table...")
        cursor.execute("""
            ALTER TABLE profiles 
            ADD COLUMN website_url TEXT;
        """)
        
        # Add comment/documentation for the column
        cursor.execute("""
            UPDATE profiles 
            SET website_url = NULL 
            WHERE website_url IS NULL;
        """)
        
        # Create index for website URL lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_profiles_website_url 
            ON profiles(website_url);
        """)
        
        conn.commit()
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(profiles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'website_url' in columns:
            logger.info("✅ Successfully added website_url column to profiles table")
            
            # Log migration details
            cursor.execute("SELECT COUNT(*) FROM profiles")
            profile_count = cursor.fetchone()[0]
            logger.info(f"Migration affects {profile_count} existing profiles")
            
            conn.close()
            return True
        else:
            logger.error("❌ Failed to add website_url column")
            conn.close()
            return False
            
    except Exception as e:
        logger.error(f"Migration error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def rollback_add_user_website_url(db_path: str = "data/catalynx.db") -> bool:
    """
    Rollback the website_url column addition.
    Note: SQLite doesn't support DROP COLUMN, so this creates a new table without the column.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create backup table without website_url column
        logger.info("Rolling back website_url column addition...")
        
        # Get current schema without website_url
        cursor.execute("""
            CREATE TABLE profiles_backup AS 
            SELECT id, name, organization_type, ein, mission_statement, status,
                   keywords, focus_areas, program_areas, target_populations, 
                   ntee_codes, government_criteria, geographic_scope, service_areas,
                   funding_preferences, annual_revenue, form_type, foundation_grants,
                   board_members, created_at, updated_at
            FROM profiles;
        """)
        
        # Drop original table
        cursor.execute("DROP TABLE profiles")
        
        # Rename backup to original
        cursor.execute("ALTER TABLE profiles_backup RENAME TO profiles")
        
        # Recreate indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_ein ON profiles(ein)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_type ON profiles(organization_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_status ON profiles(status)")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Successfully rolled back website_url column addition")
        return True
        
    except Exception as e:
        logger.error(f"Rollback error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run migration
    success = migrate_add_user_website_url()
    if success:
        print("✅ Migration completed successfully")
    else:
        print("❌ Migration failed")