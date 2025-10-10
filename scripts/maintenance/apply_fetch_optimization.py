#!/usr/bin/env python3
"""
Apply fetch optimization indexes to improve database performance.
Run this script to add EIN indexes and other fetch-related optimizations.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database.database_manager import DatabaseManager

def main():
    """Apply fetch optimization migration"""

    # Get database path
    project_root = Path(__file__).parent
    database_path = project_root / "data" / "catalynx.db"

    print(f"Applying fetch optimization to database: {database_path}")

    # Initialize database manager
    db_manager = DatabaseManager(str(database_path))

    # Apply the fetch optimization migration
    migration_file = "add_fetch_optimization_indexes.sql"
    success = db_manager.apply_migration(migration_file)

    if success:
        print("✅ Fetch optimization indexes applied successfully!")
        print("Database is now optimized for:")
        print("  - EIN-based lookups (ProPublica, BMF)")
        print("  - Organization name searches")
        print("  - Processing status tracking")
        print("  - Source attribution queries")
        print("  - AI processing optimization")
    else:
        print("❌ Failed to apply fetch optimization indexes")
        print("Check the logs for more details")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())