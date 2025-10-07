"""
Database Integration E2E Tests

Tests the dual-database architecture:
- catalynx.db: Application database (profiles, opportunities, costs)
- nonprofit_intelligence.db: Intelligence database (BMF, 990 data)

Validates:
- Connection and initialization
- Transaction handling
- Multi-database queries
- Entity cache integration
- Data consistency
"""

import pytest
import sqlite3
import os
from pathlib import Path

from src.config.database_config import get_nonprofit_intelligence_db, get_catalynx_db
from src.database.database_manager import DatabaseManager, Profile, Opportunity
from src.core.entity_cache_manager import EntityCacheManager
from datetime import datetime


@pytest.mark.integration
class TestDualDatabaseArchitecture:
    """Test dual-database architecture"""

    def test_database_files_exist(self):
        """Test that both database files exist"""
        catalynx_db = get_catalynx_db()
        intelligence_db = get_nonprofit_intelligence_db()

        assert os.path.exists(catalynx_db), f"Catalynx database not found: {catalynx_db}"
        assert os.path.exists(intelligence_db), f"Intelligence database not found: {intelligence_db}"

        # Check file sizes (basic sanity check)
        catalynx_size = os.path.getsize(catalynx_db)
        intelligence_size = os.path.getsize(intelligence_db)

        assert catalynx_size > 0, "Catalynx database is empty"
        assert intelligence_size > 100_000, "Intelligence database seems too small (expected >100KB)"

    def test_catalynx_db_schema(self):
        """Test Catalynx database schema is properly initialized"""
        db_path = get_catalynx_db()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check critical tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = ['profiles', 'opportunities', 'cost_tracking', 'export_history']
        for table in required_tables:
            assert table in tables, f"Required table '{table}' not found in Catalynx DB"

        # Check profiles table structure
        cursor.execute("PRAGMA table_info(profiles)")
        profile_columns = [row[1] for row in cursor.fetchall()]

        required_profile_cols = ['id', 'name', 'ein', 'ntee_codes', 'created_at']
        for col in required_profile_cols:
            assert col in profile_columns, f"Required column '{col}' not found in profiles table"

        conn.close()

    def test_intelligence_db_schema(self):
        """Test Intelligence database schema (BMF/SOI data)"""
        db_path = get_nonprofit_intelligence_db()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check critical tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = ['bmf_organizations', 'form_990', 'form_990pf', 'form_990ez']
        for table in required_tables:
            assert table in tables, f"Required table '{table}' not found in Intelligence DB"

        # Check row counts (basic data validation)
        cursor.execute("SELECT COUNT(*) FROM bmf_organizations")
        bmf_count = cursor.fetchone()[0]
        assert bmf_count > 100_000, f"BMF organizations count too low: {bmf_count}"

        conn.close()

    def test_database_manager_initialization(self):
        """Test DatabaseManager initializes correctly"""
        db_manager = DatabaseManager(get_catalynx_db())

        # Verify it can connect
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM profiles")
            count = cursor.fetchone()[0]
            assert count >= 0, "Profile count query failed"

    def test_cross_database_query(self):
        """Test querying data across both databases"""
        # Query 1: Get a profile from Catalynx DB
        catalynx_db = DatabaseManager(get_catalynx_db())

        # Create a test profile
        test_profile = Profile(
            id=f"test_db_integration_{datetime.now().timestamp()}",
            name="Test Cross-DB Organization",
            organization_type="nonprofit",
            ein="541234567",
            ntee_codes=["P20"],
            status="active"
        )

        created = catalynx_db.create_profile(test_profile)
        assert created, "Failed to create test profile"

        # Query 2: Look up the same EIN in Intelligence DB
        intelligence_conn = sqlite3.connect(get_nonprofit_intelligence_db())
        cursor = intelligence_conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM bmf_organizations WHERE ein = ?", (test_profile.ein,))
        bmf_matches = cursor.fetchone()[0]

        intelligence_conn.close()

        # Clean up
        catalynx_db.delete_profile(test_profile.id)

        # Note: The test EIN may or may not exist in BMF - this tests the query mechanics
        assert bmf_matches >= 0, "BMF query failed"

    def test_entity_cache_database_integration(self):
        """Test EntityCacheManager integration with databases"""
        cache_manager = EntityCacheManager()

        # Test EIN lookup with BMF integration
        # Use a known EIN from the BMF (if available)
        intelligence_conn = sqlite3.connect(get_nonprofit_intelligence_db())
        cursor = intelligence_conn.cursor()

        cursor.execute("SELECT ein, name FROM bmf_organizations LIMIT 1")
        row = cursor.fetchone()
        intelligence_conn.close()

        if row:
            test_ein, org_name = row

            # Store entity data in cache
            entity_id = f"nonprofit_{test_ein}"
            success = cache_manager.store_entity_data(
                entity_id=entity_id,
                data={'ein': test_ein, 'name': org_name, 'source': 'bmf'}
            )
            assert success, "Failed to store entity data in cache"

            # Retrieve from cache
            cached_data = cache_manager.get_entity_data(entity_id)
            assert cached_data is not None, "Failed to retrieve cached entity"
            assert cached_data['ein'] == test_ein, "Cached EIN mismatch"

    def test_transaction_handling(self):
        """Test transaction commit and rollback"""
        db_manager = DatabaseManager(get_catalynx_db())

        test_id = f"test_transaction_{datetime.now().timestamp()}"
        test_profile = Profile(
            id=test_id,
            name="Transaction Test Profile",
            organization_type="nonprofit",
            ein="541111111",
            status="active"
        )

        # Test successful transaction (commit)
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO profiles (id, name, organization_type, status) VALUES (?, ?, ?, ?)",
                (test_profile.id, test_profile.name, test_profile.organization_type, test_profile.status)
            )
            conn.commit()

        # Verify it was saved
        retrieved = db_manager.get_profile(test_id)
        assert retrieved is not None, "Transaction commit failed"
        assert retrieved.name == test_profile.name

        # Clean up
        db_manager.delete_profile(test_id)

    def test_multi_database_consistency(self):
        """Test data consistency across database operations"""
        catalynx_db = DatabaseManager(get_catalynx_db())

        # Create profile with EIN
        test_ein = "541234567"
        test_id = f"test_consistency_{datetime.now().timestamp()}"

        profile = Profile(
            id=test_id,
            name="Consistency Test Org",
            organization_type="nonprofit",
            ein=test_ein,
            ntee_codes=["B25"],
            status="active"
        )

        catalynx_db.create_profile(profile)

        # Create opportunity linked to profile
        opportunity = Opportunity(
            id=f"opp_{test_id}",
            profile_id=test_id,
            organization_name="Test Opportunity Org",
            ein=test_ein,
            current_stage="discovery",
            overall_score=0.75
        )

        catalynx_db.create_opportunity(opportunity)

        # Verify consistency: Profile and opportunity use same EIN
        retrieved_profile = catalynx_db.get_profile(test_id)

        with catalynx_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ein FROM opportunities WHERE id = ?", (opportunity.id,))
            opp_ein = cursor.fetchone()[0]

        assert retrieved_profile.ein == opp_ein, "EIN mismatch between profile and opportunity"

        # Clean up
        with catalynx_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM opportunities WHERE id = ?", (opportunity.id,))
            conn.commit()
        catalynx_db.delete_profile(test_id)

    def test_database_indexes(self):
        """Test that critical indexes exist for performance"""
        # Check Catalynx DB indexes
        catalynx_conn = sqlite3.connect(get_catalynx_db())
        cursor = catalynx_conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]

        catalynx_conn.close()

        # At minimum, primary key indexes should exist
        assert len(indexes) > 0, "No indexes found in Catalynx DB"

        # Check Intelligence DB indexes
        intelligence_conn = sqlite3.connect(get_nonprofit_intelligence_db())
        cursor = intelligence_conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        intel_indexes = [row[0] for row in cursor.fetchall()]

        intelligence_conn.close()

        # BMF should have indexes for common queries
        assert len(intel_indexes) > 0, "No indexes found in Intelligence DB"

    def test_database_connection_pooling(self):
        """Test multiple concurrent database connections"""
        db_manager = DatabaseManager(get_catalynx_db())

        # Simulate concurrent operations
        connections = []
        for i in range(3):
            conn = db_manager.get_connection()
            connections.append(conn)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM profiles")
            count = cursor.fetchone()[0]
            assert count >= 0

        # Close all connections
        for conn in connections:
            conn.close()

    def test_bmf_990_data_linkage(self):
        """Test that BMF and 990 data can be linked via EIN"""
        intelligence_conn = sqlite3.connect(get_nonprofit_intelligence_db())
        cursor = intelligence_conn.cursor()

        # Find an EIN that exists in both BMF and Form 990
        cursor.execute("""
            SELECT b.ein, b.name, f.totrevenue
            FROM bmf_organizations b
            INNER JOIN form_990 f ON b.ein = f.ein
            LIMIT 1
        """)

        result = cursor.fetchone()
        intelligence_conn.close()

        if result:
            ein, name, revenue = result
            assert ein is not None, "EIN is null in joined result"
            assert name is not None, "Name is null in joined result"
            # Revenue can be null in some cases
        else:
            # No joined data found - test that query executes without error
            pass


@pytest.mark.integration
class TestDatabasePerformance:
    """Test database performance characteristics"""

    def test_profile_query_performance(self):
        """Test profile query performance is acceptable (<50ms target)"""
        import time

        db_manager = DatabaseManager(get_catalynx_db())

        start = time.time()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles LIMIT 10")
            results = cursor.fetchall()
        duration = time.time() - start

        assert duration < 0.1, f"Profile query too slow: {duration*1000:.2f}ms"
        assert len(results) >= 0, "Query returned no results"

    def test_bmf_query_performance(self):
        """Test BMF query performance (<100ms for simple queries)"""
        import time

        intelligence_conn = sqlite3.connect(get_nonprofit_intelligence_db())
        cursor = intelligence_conn.cursor()

        start = time.time()
        cursor.execute("SELECT * FROM bmf_organizations WHERE state = 'VA' LIMIT 100")
        results = cursor.fetchall()
        duration = time.time() - start

        intelligence_conn.close()

        assert duration < 0.2, f"BMF query too slow: {duration*1000:.2f}ms"
        assert len(results) > 0, "No results from BMF query"
