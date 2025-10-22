#!/usr/bin/env python3
"""
One-time cleanup script to eliminate duplicate discovered opportunities.

Problem: UPSERT logic should prevent duplicates, but database may have:
- Orphaned opportunities from failed runs
- Duplicate EINs with different opportunity IDs
- Old discovery records that were never properly updated

Solution: Keep only the most recent opportunity per profile+EIN combination.

Usage:
    python src/database/scripts/cleanup_discovery_duplicates.py
    python src/database/scripts/cleanup_discovery_duplicates.py --auto-confirm
"""

import sqlite3
import logging
import sys
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# SQL Queries
GET_STATS_QUERY = """
SELECT
    COUNT(*) as total_opportunities,
    COUNT(DISTINCT ein || '-' || profile_id) as unique_profile_ein_pairs,
    COUNT(*) - COUNT(DISTINCT ein || '-' || profile_id) as duplicates,
    source
FROM opportunities
WHERE source = 'nonprofit'
GROUP BY source
"""

GET_ALL_STATS_QUERY = """
SELECT
    COUNT(*) as total_all_opportunities,
    SUM(CASE WHEN source = 'nonprofit' THEN 1 ELSE 0 END) as nonprofit_opportunities,
    SUM(CASE WHEN source != 'nonprofit' OR source IS NULL THEN 1 ELSE 0 END) as other_opportunities
FROM opportunities
"""

DELETE_DUPLICATES_QUERY = """
-- Delete duplicate opportunities, keeping only the newest per profile+EIN
DELETE FROM opportunities
WHERE id IN (
    -- Find all opportunity IDs that are NOT the most recent
    SELECT o1.id
    FROM opportunities o1
    WHERE o1.source = 'nonprofit'
    AND o1.ein IS NOT NULL  -- Only process opportunities with EINs
    AND EXISTS (
        -- Check if there's a newer opportunity for same profile+EIN
        SELECT 1
        FROM opportunities o2
        WHERE o2.profile_id = o1.profile_id
        AND o2.ein = o1.ein
        AND o2.source = 'nonprofit'
        AND o2.discovery_date > o1.discovery_date
    )
)
"""

GET_DUPLICATE_DETAILS_QUERY = """
SELECT
    profile_id,
    ein,
    COUNT(*) as duplicate_count,
    MIN(discovery_date) as oldest_discovery,
    MAX(discovery_date) as newest_discovery
FROM opportunities
WHERE source = 'nonprofit' AND ein IS NOT NULL
GROUP BY profile_id, ein
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 10
"""


def get_database_path() -> Path:
    """Get path to catalynx.db database"""
    # Try project root
    db_path = Path("data/catalynx.db")
    if db_path.exists():
        return db_path

    # Try relative to script location
    script_dir = Path(__file__).parent
    db_path = script_dir.parent.parent.parent / "data" / "catalynx.db"
    if db_path.exists():
        return db_path

    raise FileNotFoundError("Could not find catalynx.db database")


def get_stats(conn: sqlite3.Connection) -> dict:
    """Get current statistics about opportunities"""
    cursor = conn.cursor()

    # Get nonprofit-specific stats
    cursor.execute(GET_STATS_QUERY)
    nonprofit_stats = cursor.fetchone()

    # Get overall stats
    cursor.execute(GET_ALL_STATS_QUERY)
    all_stats = cursor.fetchone()

    return {
        'total_opportunities': all_stats[0] if all_stats else 0,
        'nonprofit_opportunities': all_stats[1] if all_stats else 0,
        'other_opportunities': all_stats[2] if all_stats else 0,
        'unique_profile_ein_pairs': nonprofit_stats[1] if nonprofit_stats else 0,
        'duplicates': nonprofit_stats[2] if nonprofit_stats else 0
    }


def get_duplicate_details(conn: sqlite3.Connection):
    """Get details about duplicate opportunities"""
    cursor = conn.cursor()
    cursor.execute(GET_DUPLICATE_DETAILS_QUERY)
    return cursor.fetchall()


def cleanup_duplicates(conn: sqlite3.Connection) -> int:
    """Delete duplicate opportunities, keeping only the most recent"""
    cursor = conn.cursor()
    cursor.execute(DELETE_DUPLICATES_QUERY)
    deleted_count = cursor.rowcount
    conn.commit()
    return deleted_count


def main():
    """Main cleanup execution"""
    logger.info("="*80)
    logger.info("Discovery Opportunities Cleanup Script")
    logger.info("="*80)

    try:
        # Get database path
        db_path = get_database_path()
        logger.info(f"Database: {db_path}")

        # Connect to database
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Get BEFORE statistics
        logger.info("\n" + "="*80)
        logger.info("BEFORE CLEANUP")
        logger.info("="*80)
        before_stats = get_stats(conn)
        logger.info(f"Total Opportunities: {before_stats['total_opportunities']}")
        logger.info(f"  - Nonprofit: {before_stats['nonprofit_opportunities']}")
        logger.info(f"  - Other: {before_stats['other_opportunities']}")
        logger.info(f"Unique Profile+EIN Pairs: {before_stats['unique_profile_ein_pairs']}")
        logger.info(f"Duplicates Detected: {before_stats['duplicates']}")

        # Show duplicate details
        if before_stats['duplicates'] > 0:
            logger.info("\nTop 10 Duplicate Groups:")
            logger.info("-" * 80)
            duplicates = get_duplicate_details(conn)
            for dup in duplicates:
                logger.info(f"  Profile: {dup[0][:20]}... | EIN: {dup[1]} | Count: {dup[2]} | "
                           f"Oldest: {dup[3]} | Newest: {dup[4]}")

            # Confirm cleanup
            logger.info("\n" + "="*80)
            logger.info("CLEANUP OPERATION")
            logger.info("="*80)
            logger.info(f"This will DELETE {before_stats['duplicates']} duplicate opportunities")
            logger.info("Keeping only the NEWEST opportunity for each profile+EIN pair")

            # Check for auto-confirm flag
            auto_confirm = '--auto-confirm' in sys.argv or '-y' in sys.argv

            if auto_confirm:
                logger.info("\n✅ Auto-confirm enabled, proceeding with cleanup...")
                response = 'yes'
            else:
                response = input("\nProceed with cleanup? (yes/no): ").strip().lower()

            if response != 'yes':
                logger.info("Cleanup cancelled by user")
                conn.close()
                return

            # Perform cleanup
            logger.info("\nDeleting duplicates...")
            deleted_count = cleanup_duplicates(conn)
            logger.info(f"✅ Deleted {deleted_count} duplicate opportunities")

            # Get AFTER statistics
            logger.info("\n" + "="*80)
            logger.info("AFTER CLEANUP")
            logger.info("="*80)
            after_stats = get_stats(conn)
            logger.info(f"Total Opportunities: {after_stats['total_opportunities']}")
            logger.info(f"  - Nonprofit: {after_stats['nonprofit_opportunities']}")
            logger.info(f"  - Other: {after_stats['other_opportunities']}")
            logger.info(f"Unique Profile+EIN Pairs: {after_stats['unique_profile_ein_pairs']}")
            logger.info(f"Duplicates Remaining: {after_stats['duplicates']}")

            # Summary
            logger.info("\n" + "="*80)
            logger.info("CLEANUP SUMMARY")
            logger.info("="*80)
            logger.info(f"Opportunities Deleted: {deleted_count}")
            logger.info(f"Space Savings: {before_stats['total_opportunities'] - after_stats['total_opportunities']} records")
            logger.info(f"Duplicate Reduction: {before_stats['duplicates']} → {after_stats['duplicates']}")
            logger.info("✅ Cleanup complete!")

        else:
            logger.info("\n✅ No duplicates detected - database is clean!")

        conn.close()

    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
