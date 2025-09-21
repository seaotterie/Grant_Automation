#!/usr/bin/env python3
"""
Database Migration: Add Location to Profiles
Adds location field to profiles table for organization location information
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

def migrate_add_location_field(db_path: str = "data/catalynx.db") -> bool:
    """
    Add location field to profiles table for organization location information.

    This supports enhanced profile data including:
    - Organization address/city/state
    - Location-based filtering and matching
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("PRAGMA table_info(profiles)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'location' in columns:
            logger.info("Column 'location' already exists in profiles table")
            conn.close()
            return True

        # Add the location column
        logger.info("Adding location column to profiles table...")
        cursor.execute("""
            ALTER TABLE profiles
            ADD COLUMN location TEXT;
        """)

        # Set default value for existing records
        cursor.execute("""
            UPDATE profiles
            SET location = NULL
            WHERE location IS NULL;
        """)

        # Create index for location lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_profiles_location
            ON profiles(location);
        """)

        conn.commit()

        # Verify the migration
        cursor.execute("PRAGMA table_info(profiles)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'location' in columns:
            logger.info("✅ Successfully added location column to profiles table")

            # Log migration details
            cursor.execute("SELECT COUNT(*) FROM profiles")
            profile_count = cursor.fetchone()[0]
            logger.info(f"Migration affects {profile_count} existing profiles")

            conn.close()
            return True
        else:
            logger.error("❌ Failed to add location column")
            conn.close()
            return False

    except Exception as e:
        logger.error(f"Migration error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    # Direct execution for testing
    logging.basicConfig(level=logging.INFO)
    result = migrate_add_location_field()
    print(f"Migration completed: {'✅ SUCCESS' if result else '❌ FAILED'}")