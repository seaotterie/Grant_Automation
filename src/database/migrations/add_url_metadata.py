#!/usr/bin/env python3
"""
Database Migration: Add URL Metadata to Opportunities Table

Migration Version: 1.1.0
Created: 2025-10-31
Purpose: Add website URL caching columns to opportunities table for Tool 25 integration

Columns Added:
- website_url: Cached website URL (from 990, user-provided, or not_found)
- url_source: Source of URL (990_xml, user_provided, not_found)
- url_discovered_at: Timestamp when URL was discovered
- url_last_verified_at: Timestamp of last Tool 25 verification
- url_verification_status: Status from Tool 25 (pending, valid, invalid, timeout)

Benefits:
- Eliminates re-discovery of URLs ($0.00 caching vs repeated API calls)
- Enables bulk URL discovery operations
- Tracks URL freshness and validation status
- Supports progressive Tool 25 web research workflow
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class URLMetadataMigration:
    """Migration to add URL metadata columns to opportunities table."""

    VERSION = "1.3.0"
    DESCRIPTION = "Add URL metadata columns for Tool 25 web intelligence caching"

    def __init__(self, database_path: Optional[str] = None):
        if database_path:
            self.database_path = database_path
        else:
            # Default to project data directory
            project_root = Path(__file__).parent.parent.parent.parent
            self.database_path = project_root / "data" / "catalynx.db"

        logger.info(f"Migration database path: {self.database_path}")

    def check_migration_needed(self) -> bool:
        """Check if migration is needed (columns don't exist yet)."""
        try:
            conn = sqlite3.connect(str(self.database_path))
            cursor = conn.cursor()

            # Check if website_url column exists
            cursor.execute("PRAGMA table_info(opportunities)")
            columns = [col[1] for col in cursor.fetchall()]

            conn.close()

            has_url_columns = 'website_url' in columns
            logger.info(f"URL metadata columns exist: {has_url_columns}")

            return not has_url_columns

        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            return False

    def check_current_version(self) -> Optional[str]:
        """Get current schema version from database."""
        try:
            conn = sqlite3.connect(str(self.database_path))
            cursor = conn.cursor()

            cursor.execute("SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1")
            row = cursor.fetchone()

            conn.close()

            if row:
                current_version = row[0]
                logger.info(f"Current schema version: {current_version}")
                return current_version
            else:
                logger.warning("No schema version found in database")
                return None

        except Exception as e:
            logger.error(f"Error checking schema version: {e}")
            return None

    def apply_migration(self) -> bool:
        """Apply the migration to add URL metadata columns."""
        try:
            conn = sqlite3.connect(str(self.database_path))
            cursor = conn.cursor()

            logger.info("=" * 80)
            logger.info("APPLYING MIGRATION: Add URL Metadata Columns")
            logger.info("=" * 80)

            # Step 1: Add website_url column
            logger.info("Adding column: website_url TEXT")
            cursor.execute("""
                ALTER TABLE opportunities
                ADD COLUMN website_url TEXT
            """)

            # Step 2: Add url_source column
            logger.info("Adding column: url_source TEXT")
            cursor.execute("""
                ALTER TABLE opportunities
                ADD COLUMN url_source TEXT
            """)

            # Step 3: Add url_discovered_at column
            logger.info("Adding column: url_discovered_at TIMESTAMP")
            cursor.execute("""
                ALTER TABLE opportunities
                ADD COLUMN url_discovered_at TIMESTAMP
            """)

            # Step 4: Add url_last_verified_at column
            logger.info("Adding column: url_last_verified_at TIMESTAMP")
            cursor.execute("""
                ALTER TABLE opportunities
                ADD COLUMN url_last_verified_at TIMESTAMP
            """)

            # Step 5: Add url_verification_status column
            logger.info("Adding column: url_verification_status TEXT")
            cursor.execute("""
                ALTER TABLE opportunities
                ADD COLUMN url_verification_status TEXT
            """)

            # Step 6: Create indexes for URL lookups
            logger.info("Creating index: idx_opportunities_url_source")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_opportunities_url_source
                ON opportunities (url_source)
            """)

            logger.info("Creating index: idx_opportunities_website_url")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_opportunities_website_url
                ON opportunities (website_url)
            """)

            # Step 7: Update schema_version table
            logger.info(f"Updating schema version to {self.VERSION}")
            cursor.execute("""
                INSERT OR REPLACE INTO schema_version (version, description, applied_at)
                VALUES (?, ?, ?)
            """, (self.VERSION, self.DESCRIPTION, datetime.now().isoformat()))

            # Commit all changes
            conn.commit()
            conn.close()

            logger.info("=" * 80)
            logger.info("MIGRATION COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)

            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            return False

    def verify_migration(self) -> bool:
        """Verify that migration was applied correctly."""
        try:
            conn = sqlite3.connect(str(self.database_path))
            cursor = conn.cursor()

            # Check all columns were added
            cursor.execute("PRAGMA table_info(opportunities)")
            columns = [col[1] for col in cursor.fetchall()]

            required_columns = [
                'website_url',
                'url_source',
                'url_discovered_at',
                'url_last_verified_at',
                'url_verification_status'
            ]

            all_present = all(col in columns for col in required_columns)

            # Check indexes were created
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='opportunities'")
            indexes = [row[0] for row in cursor.fetchall()]

            required_indexes = [
                'idx_opportunities_url_source',
                'idx_opportunities_website_url'
            ]

            indexes_present = all(idx in indexes for idx in required_indexes)

            # Check schema version
            cursor.execute("SELECT version FROM schema_version WHERE version = ?", (self.VERSION,))
            version_present = cursor.fetchone() is not None

            conn.close()

            logger.info(f"Columns present: {all_present}")
            logger.info(f"Indexes present: {indexes_present}")
            logger.info(f"Schema version updated: {version_present}")

            return all_present and indexes_present and version_present

        except Exception as e:
            logger.error(f"Verification failed: {e}", exc_info=True)
            return False

    def rollback_migration(self) -> bool:
        """
        Rollback migration by removing added columns.

        NOTE: SQLite doesn't support DROP COLUMN directly (requires full table rebuild).
        For safety, this is not implemented. If rollback is needed, restore from backup.
        """
        logger.warning("Rollback not implemented - SQLite ALTER TABLE limitations")
        logger.warning("To rollback, restore database from backup taken before migration")
        return False


def run_migration(database_path: Optional[str] = None) -> bool:
    """
    Run the URL metadata migration.

    Args:
        database_path: Optional path to database file

    Returns:
        True if migration successful, False otherwise
    """
    migration = URLMetadataMigration(database_path)

    # Check current version
    current_version = migration.check_current_version()
    logger.info(f"Current database version: {current_version}")

    # Check if migration is needed
    if not migration.check_migration_needed():
        logger.info("Migration not needed - URL metadata columns already exist")
        return True

    # Apply migration
    logger.info("Starting migration...")
    success = migration.apply_migration()

    if not success:
        logger.error("Migration failed!")
        return False

    # Verify migration
    logger.info("Verifying migration...")
    verified = migration.verify_migration()

    if not verified:
        logger.error("Migration verification failed!")
        return False

    logger.info("✅ Migration completed and verified successfully!")
    return True


if __name__ == "__main__":
    import sys

    # Allow custom database path as command line argument
    db_path = sys.argv[1] if len(sys.argv) > 1 else None

    logger.info("=" * 80)
    logger.info("URL Metadata Migration Tool")
    logger.info("=" * 80)

    success = run_migration(db_path)

    if success:
        logger.info("\n✅ Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n❌ Migration failed!")
        sys.exit(1)
