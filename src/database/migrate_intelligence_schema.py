#!/usr/bin/env python3
"""
Intelligence Database Migration Script
Creates and migrates intelligence storage tables for enhanced web scraping data.

This script:
1. Creates the intelligence database schema
2. Migrates existing URL cache data (if any)
3. Sets up proper indexes and views
4. Validates the migration
5. Provides rollback capabilities

Usage:
    python src/database/migrate_intelligence_schema.py
    python src/database/migrate_intelligence_schema.py --rollback
    python src/database/migrate_intelligence_schema.py --validate
"""

import asyncio
import sqlite3
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse
import logging

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.database.database_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntelligenceMigrationManager:
    """Manages migration of intelligence database schema."""
    
    def __init__(self, database_path: str = None):
        """Initialize migration manager."""
        if database_path is None:
            database_path = "data/catalynx.db"
        
        self.database_path = database_path
        self.schema_path = Path(__file__).parent / "intelligence_schema.sql"
        self.backup_path = f"{database_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Note: Using direct SQLite connections instead of DatabaseManager for migration
        
    def create_backup(self) -> bool:
        """Create database backup before migration."""
        try:
            logger.info(f"Creating backup: {self.backup_path}")
            
            # Copy database file
            import shutil
            shutil.copy2(self.database_path, self.backup_path)
            
            logger.info("SUCCESS: Backup created successfully")
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Failed to create backup: {e}")
            return False
    
    def load_schema_sql(self) -> str:
        """Load SQL schema from file."""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"ERROR: Schema file not found: {self.schema_path}")
            raise
        except Exception as e:
            logger.error(f"ERROR: Failed to load schema: {e}")
            raise
    
    def execute_migration(self) -> bool:
        """Execute the intelligence schema migration."""
        try:
            logger.info("STARTING: Starting intelligence database migration")
            
            # Load schema SQL
            schema_sql = self.load_schema_sql()
            
            # Split into individual statements, filtering out comments
            statements = []
            for stmt in schema_sql.split(';'):
                stmt = stmt.strip()
                if stmt and not stmt.startswith('--') and not stmt.startswith('/*'):
                    statements.append(stmt)
            
            # Execute each statement
            success_count = 0
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("PRAGMA foreign_keys = OFF")  # Temporarily disable FK constraints
                
                for i, statement in enumerate(statements):
                    if not statement or statement.startswith('--') or statement.startswith('/*'):
                        continue
                    
                    try:
                        conn.execute(statement)
                        success_count += 1
                        
                        # Log progress for major components
                        if 'CREATE TABLE' in statement:
                            table_name = statement.split('CREATE TABLE')[1].split('(')[0].strip()
                            table_name = table_name.replace('IF NOT EXISTS', '').strip()
                            logger.info(f"SUCCESS: Created table: {table_name}")
                        elif 'CREATE VIEW' in statement:
                            view_name = statement.split('CREATE VIEW')[1].split('AS')[0].strip()
                            view_name = view_name.replace('IF NOT EXISTS', '').strip()
                            logger.info(f"SUCCESS: Created view: {view_name}")
                        elif 'CREATE INDEX' in statement:
                            index_name = statement.split('CREATE INDEX')[1].split('ON')[0].strip()
                            index_name = index_name.replace('IF NOT EXISTS', '').strip()
                            logger.info(f"SUCCESS: Created index: {index_name}")
                    
                    except sqlite3.Error as e:
                        logger.warning(f"WARNING: Statement {i+1} failed (may be expected): {str(e)[:100]}")
                        continue
                
                conn.execute("PRAGMA foreign_keys = ON")  # Re-enable FK constraints
                conn.commit()
            
            logger.info(f"SUCCESS: Migration completed: {success_count} statements executed")
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Migration failed: {e}")
            return False
    
    def migrate_existing_url_cache(self) -> bool:
        """Migrate any existing URL cache data to new schema."""
        try:
            logger.info("PROCESSING: Checking for existing URL cache data to migrate")
            
            with sqlite3.connect(self.database_path) as conn:
                # Check if old URL cache table exists
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name LIKE '%url%' AND name != 'organization_urls'
                """)
                old_tables = cursor.fetchall()
                
                if not old_tables:
                    logger.info("SUCCESS: No existing URL cache data to migrate")
                    return True
                
                # Migrate data from old tables (implementation would depend on old structure)
                logger.info(f"Found {len(old_tables)} old URL-related tables")
                for table in old_tables:
                    logger.info(f"INFO: Old table found: {table[0]} (manual review recommended)")
                
                return True
                
        except Exception as e:
            logger.error(f"ERROR: URL cache migration failed: {e}")
            return False
    
    def validate_migration(self) -> bool:
        """Validate that migration was successful."""
        try:
            logger.info("VALIDATING: Checking migration")
            
            expected_tables = [
                'organization_urls',
                'web_intelligence', 
                'board_member_intelligence',
                'intelligence_processing_log',
                'intelligent_discovery_results'
            ]
            
            expected_views = [
                'v_organization_intelligence',
                'v_high_value_intelligence'
            ]
            
            with sqlite3.connect(self.database_path) as conn:
                # Check tables exist
                for table in expected_tables:
                    cursor = conn.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name=?
                    """, (table,))
                    if not cursor.fetchone():
                        logger.error(f"ERROR: Missing table: {table}")
                        return False
                    logger.info(f"SUCCESS: Table verified: {table}")
                
                # Check views exist
                for view in expected_views:
                    cursor = conn.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='view' AND name=?
                    """, (view,))
                    if not cursor.fetchone():
                        logger.error(f"ERROR: Missing view: {view}")
                        return False
                    logger.info(f"SUCCESS: View verified: {view}")
                
                # Test basic operations
                conn.execute("SELECT COUNT(*) FROM organization_urls")
                conn.execute("SELECT COUNT(*) FROM web_intelligence")
                conn.execute("SELECT COUNT(*) FROM v_organization_intelligence")
                
                logger.info("SUCCESS: All validation checks passed")
                return True
                
        except Exception as e:
            logger.error(f"ERROR: Validation failed: {e}")
            return False
    
    def rollback_migration(self) -> bool:
        """Rollback migration using backup."""
        try:
            if not os.path.exists(self.backup_path):
                logger.error(f"ERROR: Backup file not found: {self.backup_path}")
                return False
            
            logger.info(f"PROCESSING: Rolling back to backup: {self.backup_path}")
            
            # Restore from backup
            import shutil
            shutil.copy2(self.backup_path, self.database_path)
            
            logger.info("SUCCESS: Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Rollback failed: {e}")
            return False
    
    def generate_sample_data(self) -> bool:
        """Generate sample data for testing."""
        try:
            logger.info("GENERATING: Creating sample data")
            
            sample_data = [
                {
                    'ein': '812827604',
                    'organization_name': 'HEROS BRIDGE', 
                    'predicted_url': 'https://www.herosbridge.org',
                    'url_status': 'verified',
                    'http_status_code': 200
                },
                {
                    'ein': '541026365',
                    'organization_name': 'SAMPLE NONPROFIT',
                    'predicted_url': 'https://www.samplenonprofit.org', 
                    'url_status': 'pending',
                    'http_status_code': None
                }
            ]
            
            with sqlite3.connect(self.database_path) as conn:
                for data in sample_data:
                    conn.execute("""
                        INSERT OR IGNORE INTO organization_urls 
                        (ein, organization_name, predicted_url, url_status, http_status_code)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        data['ein'],
                        data['organization_name'],
                        data['predicted_url'],
                        data['url_status'],
                        data['http_status_code']
                    ))
                
                conn.commit()
            
            logger.info("SUCCESS: Sample data generated")
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Sample data generation failed: {e}")
            return False
    
    def print_schema_summary(self):
        """Print summary of created schema."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Get table info
                tables = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name LIKE '%intelligence%' 
                       OR name = 'organization_urls'
                    ORDER BY name
                """).fetchall()
                
                views = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='view' AND name LIKE 'v_%intelligence%'
                    ORDER BY name
                """).fetchall()
                
                indexes = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name LIKE 'idx_%intelligence%'
                       OR name LIKE 'idx_%org_urls%'
                    ORDER BY name
                """).fetchall()
                
                print("\n" + "="*60)
                print("INTELLIGENCE DATABASE SCHEMA SUMMARY")
                print("="*60)
                print(f"STATS: Tables Created: {len(tables)}")
                for table in tables:
                    print(f"  • {table[0]}")
                
                print(f"\nVIEWS: Views Created: {len(views)}")
                for view in views:
                    print(f"  • {view[0]}")
                
                print(f"\nINDEXES: Indexes Created: {len(indexes)}")
                for index in indexes:
                    print(f"  • {index[0]}")
                
                print(f"\nDATABASE: Database: {self.database_path}")
                print(f"BACKUP: Backup: {self.backup_path}")
                print("="*60)
                
        except Exception as e:
            logger.error(f"ERROR: Failed to generate summary: {e}")


def main():
    """Main migration script."""
    parser = argparse.ArgumentParser(description='Intelligence Database Migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback migration')
    parser.add_argument('--validate', action='store_true', help='Validate migration only')
    parser.add_argument('--sample-data', action='store_true', help='Generate sample data')
    parser.add_argument('--database', type=str, help='Database path override')
    
    args = parser.parse_args()
    
    # Initialize migration manager
    migration = IntelligenceMigrationManager(args.database)
    
    try:
        if args.rollback:
            # Rollback migration
            success = migration.rollback_migration()
            sys.exit(0 if success else 1)
        
        elif args.validate:
            # Validate only
            success = migration.validate_migration()
            if success:
                migration.print_schema_summary()
            sys.exit(0 if success else 1)
        
        else:
            # Full migration
            print("\nSTARTING: INTELLIGENCE DATABASE MIGRATION")
            print("="*50)
            
            # Step 1: Create backup
            if not migration.create_backup():
                logger.error("Failed to create backup - aborting migration")
                sys.exit(1)
            
            # Step 2: Execute migration
            if not migration.execute_migration():
                logger.error("Migration failed - rollback available")
                sys.exit(1)
            
            # Step 3: Migrate existing data
            if not migration.migrate_existing_url_cache():
                logger.warning("URL cache migration had issues - review manually")
            
            # Step 4: Validate migration
            if not migration.validate_migration():
                logger.error("Migration validation failed - rollback recommended")
                sys.exit(1)
            
            # Step 5: Generate sample data if requested
            if args.sample_data:
                migration.generate_sample_data()
            
            # Step 6: Print summary
            migration.print_schema_summary()
            
            print("\nSUCCESS: MIGRATION COMPLETED SUCCESSFULLY")
            print(f"NEXT: Next steps:")
            print(f"  1. Update MCP client to use new intelligence storage")
            print(f"  2. Integrate board member intelligence extraction")
            print(f"  3. Test enhanced discovery with intelligence scoring")
            print("="*50)
    
    except Exception as e:
        logger.error(f"ERROR: Migration failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()