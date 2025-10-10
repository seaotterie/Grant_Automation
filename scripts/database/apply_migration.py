#!/usr/bin/env python3
"""
Apply database migration to add enhanced data fields.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.database_manager import DatabaseManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Apply the enhanced data fields migration"""
    try:
        # Initialize database manager
        db_manager = DatabaseManager()

        # Apply the migration
        logger.info("Applying migration: add_enhanced_data_fields.sql")
        success = db_manager.apply_migration("add_enhanced_data_fields.sql")

        if success:
            logger.info("✅ Migration applied successfully!")
            logger.info("Enhanced data fields (verification_data, web_enhanced_data) added to profiles table")
        else:
            logger.error("❌ Migration failed!")
            return 1

    except Exception as e:
        logger.error(f"❌ Migration error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())