#!/usr/bin/env python3
"""
Database Migration: Foundation Network Intelligence Tables
Adds tables for multi-foundation grant aggregation and network analysis.

Migration: add_foundation_network_tables
Version: 2.0.0
Date: 2025-10-08

Tables Added:
1. foundation_grants - Schedule I grant records from 990-PF filings
2. network_nodes - Foundation, grantee, and person nodes
3. network_edges - Grant and board relationships
4. bundling_analysis_cache - Cached bundling analysis results
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class FoundationNetworkMigration:
    """Migration manager for foundation network tables."""

    def __init__(self, db_path: str = "data/catalynx.db"):
        self.db_path = Path(db_path)
        self.migration_version = "2.0.0_foundation_network"

    def run_migration(self):
        """Execute the migration."""
        logger.info(f"Starting foundation network tables migration: {self.migration_version}")

        if not self.db_path.exists():
            logger.error(f"Database not found: {self.db_path}")
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if migration already applied
            if self._is_migration_applied(cursor):
                logger.info("Migration already applied, skipping")
                conn.close()
                return True

            # Create tables
            self._create_foundation_grants_table(cursor)
            self._create_network_nodes_table(cursor)
            self._create_network_edges_table(cursor)
            self._create_bundling_cache_table(cursor)

            # Record migration
            self._record_migration(cursor)

            conn.commit()
            logger.info("Migration completed successfully")
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False

    def _is_migration_applied(self, cursor: sqlite3.Cursor) -> bool:
        """Check if migration was already applied."""
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='table' AND name='foundation_grants'
        """)
        return cursor.fetchone()[0] > 0

    def _create_foundation_grants_table(self, cursor: sqlite3.Cursor):
        """Create foundation_grants table for Schedule I data."""
        logger.info("Creating foundation_grants table...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS foundation_grants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Foundation identification
                foundation_ein TEXT NOT NULL,
                foundation_name TEXT,

                -- Grantee identification
                grantee_ein TEXT,                      -- May be NULL if not in Schedule I
                grantee_name TEXT NOT NULL,
                normalized_grantee_name TEXT NOT NULL, -- For fuzzy matching

                -- Grant details
                grant_amount REAL NOT NULL,
                grant_year INTEGER NOT NULL,
                grant_purpose TEXT,
                grant_tier TEXT,                       -- 'major', 'significant', 'moderate', 'small'

                -- Geographic data
                grantee_city TEXT,
                grantee_state TEXT,
                grantee_country TEXT,

                -- Additional metadata
                recipient_type TEXT,                   -- From Schedule I if available
                relationship_to_foundation TEXT,

                -- Data provenance
                source_form TEXT DEFAULT '990-PF',     -- '990-PF', 'manual', 'imported'
                source_object_id TEXT,                 -- ProPublica object_id if applicable
                data_quality_score REAL,               -- 0-1 completeness score

                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- Uniqueness constraint
                UNIQUE(foundation_ein, grantee_name, grant_year, grant_amount)
            )
        """)

        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_foundation_grants_foundation
            ON foundation_grants(foundation_ein)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_foundation_grants_grantee_ein
            ON foundation_grants(grantee_ein)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_foundation_grants_year
            ON foundation_grants(grant_year)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_foundation_grants_normalized_name
            ON foundation_grants(normalized_grantee_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_foundation_grants_amount
            ON foundation_grants(grant_amount)
        """)

        logger.info("  ✓ foundation_grants table created with indexes")

    def _create_network_nodes_table(self, cursor: sqlite3.Cursor):
        """Create network_nodes table for graph analysis."""
        logger.info("Creating network_nodes table...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS network_nodes (
                node_id TEXT PRIMARY KEY,              -- EIN or person_id
                node_type TEXT NOT NULL,               -- 'foundation', 'grantee', 'person'

                -- Basic info
                name TEXT NOT NULL,
                normalized_name TEXT,

                -- Attributes (JSON)
                attributes TEXT,                       -- JSON blob with NTEE, geography, etc.

                -- Network metrics (computed)
                degree_centrality REAL,
                betweenness_centrality REAL,
                closeness_centrality REAL,
                pagerank_score REAL,
                influence_score REAL,

                -- Metadata
                data_source TEXT,                      -- 'bmf', '990', 'manual'
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                CHECK(node_type IN ('foundation', 'grantee', 'person'))
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_network_nodes_type
            ON network_nodes(node_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_network_nodes_name
            ON network_nodes(normalized_name)
        """)

        logger.info("  ✓ network_nodes table created")

    def _create_network_edges_table(self, cursor: sqlite3.Cursor):
        """Create network_edges table for relationships."""
        logger.info("Creating network_edges table...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS network_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Edge definition
                from_node TEXT NOT NULL,               -- Node ID (foundation or person)
                to_node TEXT NOT NULL,                 -- Node ID (grantee or org)
                edge_type TEXT NOT NULL,               -- 'grant', 'board_member'

                -- Edge weight/attributes
                weight REAL DEFAULT 1.0,               -- Grant amount or connection strength
                metadata TEXT,                         -- JSON blob with years, roles, etc.

                -- Temporal data
                first_year INTEGER,
                last_year INTEGER,
                years_active TEXT,                     -- JSON array of years

                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(from_node) REFERENCES network_nodes(node_id),
                FOREIGN KEY(to_node) REFERENCES network_nodes(node_id),
                CHECK(edge_type IN ('grant', 'board_member', 'partnership'))
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_network_edges_from
            ON network_edges(from_node)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_network_edges_to
            ON network_edges(to_node)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_network_edges_type
            ON network_edges(edge_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_network_edges_weight
            ON network_edges(weight)
        """)

        logger.info("  ✓ network_edges table created")

    def _create_bundling_cache_table(self, cursor: sqlite3.Cursor):
        """Create cache table for bundling analysis results."""
        logger.info("Creating bundling_analysis_cache table...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bundling_analysis_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Cache key
                cache_key TEXT UNIQUE NOT NULL,        -- Hash of foundation_eins + tax_years

                -- Input parameters
                foundation_eins TEXT NOT NULL,         -- JSON array
                tax_years TEXT NOT NULL,               -- JSON array
                min_foundations INTEGER DEFAULT 2,

                -- Cached results
                results TEXT NOT NULL,                 -- JSON serialized GranteeBundlingOutput

                -- Cache metadata
                bundled_grantees_count INTEGER,
                total_grants_analyzed INTEGER,
                processing_time_seconds REAL,

                -- Cache lifecycle
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,                  -- Optional expiration
                hit_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bundling_cache_key
            ON bundling_analysis_cache(cache_key)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bundling_cache_expires
            ON bundling_analysis_cache(expires_at)
        """)

        logger.info("  ✓ bundling_analysis_cache table created")

    def _record_migration(self, cursor: sqlite3.Cursor):
        """Record migration in schema_version table."""
        cursor.execute("""
            INSERT OR REPLACE INTO schema_version (version, applied_at, description)
            VALUES (?, ?, ?)
        """, (
            self.migration_version,
            datetime.now().isoformat(),
            "Foundation Network Intelligence tables: grants, nodes, edges, cache"
        ))
        logger.info(f"  ✓ Migration {self.migration_version} recorded")


def run_migration(db_path: str = "data/catalynx.db"):
    """Run the foundation network migration."""
    migration = FoundationNetworkMigration(db_path)
    return migration.run_migration()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("\n" + "="*70)
    print("Foundation Network Intelligence - Database Migration")
    print("="*70 + "\n")

    success = run_migration()

    if success:
        print("\n✓ Migration completed successfully!")
        print("\nNew tables added:")
        print("  1. foundation_grants - Schedule I grant records")
        print("  2. network_nodes - Foundation, grantee, person nodes")
        print("  3. network_edges - Grant and board relationships")
        print("  4. bundling_analysis_cache - Cached analysis results")
        print("\nYou can now use the Foundation Grantee Bundling Tool.")
    else:
        print("\n✗ Migration failed. Check logs for details.")
        exit(1)
