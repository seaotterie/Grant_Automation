# Database Fixtures and Test Data Factory
# Provides database setup and test data generation for Catalynx testing

import pytest
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Test database configuration
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_catalynx.db")
TEST_ASYNC_DATABASE_URL = os.getenv("TEST_ASYNC_DATABASE_URL", "sqlite+aiosqlite:///./test_catalynx_async.db")

class DatabaseFixtures:
    """Database fixtures and utilities for testing"""
    
    @staticmethod
    def create_test_database():
        """Create a fresh test database"""
        if "sqlite" in TEST_DATABASE_URL:
            # For SQLite, just delete the file
            db_path = TEST_DATABASE_URL.replace("sqlite:///", "")
            if os.path.exists(db_path):
                os.remove(db_path)
        
        # Create engine and tables
        engine = create_engine(TEST_DATABASE_URL)
        
        # Import and create tables if models are available
        try:
            from src.core.database import Base
            Base.metadata.create_all(engine)
        except ImportError:
            # If models aren't available, create basic test tables
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS profiles (
                        id INTEGER PRIMARY KEY,
                        profile_id VARCHAR(255) UNIQUE,
                        organization_name VARCHAR(255),
                        revenue INTEGER,
                        state VARCHAR(2),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS opportunities (
                        id INTEGER PRIMARY KEY,
                        opportunity_id VARCHAR(255) UNIQUE,
                        organization_name VARCHAR(255),
                        funding_amount INTEGER,
                        source_type VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        id INTEGER PRIMARY KEY,
                        entity_id VARCHAR(255) UNIQUE,
                        data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP
                    )
                """))
                
                conn.commit()
        
        return engine
    
    @staticmethod
    def populate_test_data(engine):
        """Populate database with test data"""
        with engine.connect() as conn:
            # Insert test profiles
            test_profiles = [
                {
                    "profile_id": "test_profile_001",
                    "organization_name": "Test Education Foundation",
                    "revenue": 2500000,
                    "state": "VA"
                },
                {
                    "profile_id": "test_profile_002", 
                    "organization_name": "Community Health Initiative",
                    "revenue": 1500000,
                    "state": "MD"
                },
                {
                    "profile_id": "test_profile_003",
                    "organization_name": "Environmental Action Group",
                    "revenue": 750000,
                    "state": "NC"
                }
            ]
            
            for profile in test_profiles:
                conn.execute(text("""
                    INSERT OR REPLACE INTO profiles (profile_id, organization_name, revenue, state)
                    VALUES (:profile_id, :organization_name, :revenue, :state)
                """), profile)
            
            # Insert test opportunities
            test_opportunities = [
                {
                    "opportunity_id": "opp_001",
                    "organization_name": "Department of Education",
                    "funding_amount": 250000,
                    "source_type": "Government"
                },
                {
                    "opportunity_id": "opp_002",
                    "organization_name": "Gates Foundation", 
                    "funding_amount": 500000,
                    "source_type": "Foundation"
                },
                {
                    "opportunity_id": "opp_003",
                    "organization_name": "Corporate Giving Program",
                    "funding_amount": 100000,
                    "source_type": "Corporate"
                }
            ]
            
            for opportunity in test_opportunities:
                conn.execute(text("""
                    INSERT OR REPLACE INTO opportunities (opportunity_id, organization_name, funding_amount, source_type)
                    VALUES (:opportunity_id, :organization_name, :funding_amount, :source_type)
                """), opportunity)
            
            conn.commit()
    
    @staticmethod
    def cleanup_test_database():
        """Clean up test database"""
        if "sqlite" in TEST_DATABASE_URL:
            db_path = TEST_DATABASE_URL.replace("sqlite:///", "")
            if os.path.exists(db_path):
                os.remove(db_path)
        
        if "sqlite" in TEST_ASYNC_DATABASE_URL:
            db_path = TEST_ASYNC_DATABASE_URL.replace("sqlite+aiosqlite:///", "")
            if os.path.exists(db_path):
                os.remove(db_path)


@pytest.fixture(scope="session")
def test_database_engine():
    """Create test database engine for session"""
    engine = DatabaseFixtures.create_test_database()
    DatabaseFixtures.populate_test_data(engine)
    
    yield engine
    
    # Cleanup
    engine.dispose()
    DatabaseFixtures.cleanup_test_database()


@pytest.fixture(scope="session") 
async def async_test_database_engine():
    """Create async test database engine for session"""
    engine = create_async_engine(TEST_ASYNC_DATABASE_URL)
    
    # Create tables
    try:
        from src.core.database import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except ImportError:
        # Create basic tables if models not available
        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY,
                    profile_id VARCHAR(255) UNIQUE,
                    organization_name VARCHAR(255),
                    revenue INTEGER,
                    state VARCHAR(2)
                )
            """))
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
def db_session(test_database_engine):
    """Create database session for test"""
    SessionLocal = sessionmaker(bind=test_database_engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
async def async_db_session(async_test_database_engine):
    """Create async database session for test"""
    AsyncSessionLocal = AsyncSession(async_test_database_engine)
    
    try:
        yield AsyncSessionLocal
    finally:
        await AsyncSessionLocal.rollback()
        await AsyncSessionLocal.close()


@pytest.fixture
def clean_database(test_database_engine):
    """Provide clean database for each test"""
    # Clear all data
    with test_database_engine.connect() as conn:
        # Get all table names
        try:
            from src.core.database import Base
            tables = Base.metadata.tables.keys()
        except ImportError:
            tables = ["profiles", "opportunities", "cache_entries"]
        
        # Clear each table
        for table in tables:
            try:
                conn.execute(text(f"DELETE FROM {table}"))
            except:
                pass  # Ignore if table doesn't exist
        
        conn.commit()
    
    yield test_database_engine
    
    # Cleanup after test
    with test_database_engine.connect() as conn:
        for table in tables:
            try:
                conn.execute(text(f"DELETE FROM {table}"))
            except:
                pass
        conn.commit()


class TestDataFactory:
    """Factory for generating test data"""
    
    @staticmethod
    def create_test_profile(profile_id=None, **kwargs):
        """Create a test profile with optional overrides"""
        import random
        
        if profile_id is None:
            profile_id = f"test_profile_{random.randint(1000, 9999)}"
        
        base_profile = {
            "profile_id": profile_id,
            "organization_name": f"Test Organization {random.randint(100, 999)}",
            "mission_statement": "Supporting community development through innovative programs",
            "ntee_codes": random.choice([["B25"], ["P20"], ["T30"], ["B25", "B28"]]),
            "revenue": random.randint(100000, 10000000),
            "staff_count": random.randint(5, 100),
            "years_active": random.randint(3, 30),
            "state": random.choice(["VA", "MD", "NC", "DC", "NY", "CA"]),
            "city": random.choice(["Richmond", "Baltimore", "Raleigh", "Washington", "New York", "Los Angeles"]),
            "focus_areas": random.choice([
                ["education", "literacy"],
                ["health", "community"],
                ["environment", "conservation"],
                ["arts", "culture"]
            ])
        }
        
        # Override with provided kwargs
        base_profile.update(kwargs)
        return base_profile
    
    @staticmethod
    def create_test_opportunity(opportunity_id=None, **kwargs):
        """Create a test opportunity with optional overrides"""
        import random
        from datetime import datetime, timedelta
        
        if opportunity_id is None:
            opportunity_id = f"test_opp_{random.randint(1000, 9999)}"
        
        base_opportunity = {
            "opportunity_id": opportunity_id,
            "organization_name": f"Test Funder {random.randint(100, 999)}",
            "source_type": random.choice(["Foundation", "Government", "Corporate"]),
            "discovery_source": random.choice(["ProPublica", "Grants.gov", "Foundation Directory"]),
            "program_name": f"Test Grant Program {random.randint(10, 99)}",
            "description": "Funding opportunity for community-based initiatives",
            "funding_amount": random.randint(25000, 1000000),
            "application_deadline": (datetime.now() + timedelta(days=random.randint(30, 365))).isoformat(),
            "ntee_codes": random.choice([["B25"], ["P20"], ["T30"]]),
            "external_data": {
                "state": random.choice(["VA", "MD", "NC", "DC"]),
                "geographic_scope": random.choice(["Local", "Regional", "National"])
            },
            "raw_score": random.uniform(0.3, 0.95),
            "compatibility_score": random.uniform(0.4, 0.9),
            "confidence_level": random.uniform(0.6, 0.95),
            "funnel_stage": random.choice(["prospects", "qualified", "candidates"])
        }
        
        # Override with provided kwargs
        base_opportunity.update(kwargs)
        return base_opportunity
    
    @staticmethod
    def create_test_entity_data(entity_id=None, **kwargs):
        """Create test entity cache data"""
        import random
        
        if entity_id is None:
            entity_id = f"test_entity_{random.randint(10000, 99999)}"
        
        base_entity = {
            "entity_id": entity_id,
            "ein": f"12-{random.randint(1000000, 9999999)}",
            "organization_name": f"Entity {random.randint(100, 999)}",
            "revenue": random.randint(100000, 50000000),
            "assets": random.randint(50000, 25000000),
            "expenses": random.randint(80000, 45000000),
            "ntee_codes": random.choice([["B25"], ["P20"], ["T30"]]),
            "state": random.choice(["VA", "MD", "NC", "DC"]),
            "board_members": [
                {
                    "name": f"Board Member {i+1}",
                    "title": random.choice(["Chair", "Vice Chair", "Treasurer", "Secretary", "Member"])
                }
                for i in range(random.randint(3, 12))
            ],
            "financial_data": {
                "revenue_growth": random.uniform(-0.1, 0.3),
                "expense_ratio": random.uniform(0.7, 0.95),
                "admin_ratio": random.uniform(0.05, 0.25)
            },
            "cached_at": datetime.now().isoformat()
        }
        
        # Override with provided kwargs
        base_entity.update(kwargs)
        return base_entity
    
    @staticmethod
    def create_batch_test_data(count=10, data_type="profile"):
        """Create a batch of test data"""
        if data_type == "profile":
            return [TestDataFactory.create_test_profile() for _ in range(count)]
        elif data_type == "opportunity":
            return [TestDataFactory.create_test_opportunity() for _ in range(count)]
        elif data_type == "entity":
            return [TestDataFactory.create_test_entity_data() for _ in range(count)]
        else:
            raise ValueError(f"Unknown data type: {data_type}")


# Performance test data generators
class PerformanceDataFactory:
    """Factory for generating performance test data"""
    
    @staticmethod
    def create_large_dataset(profiles=100, opportunities=1000, entities=500):
        """Create large dataset for performance testing"""
        return {
            "profiles": TestDataFactory.create_batch_test_data(profiles, "profile"),
            "opportunities": TestDataFactory.create_batch_test_data(opportunities, "opportunity"), 
            "entities": TestDataFactory.create_batch_test_data(entities, "entity")
        }
    
    @staticmethod
    def create_realistic_dataset():
        """Create realistic dataset mimicking production data"""
        import random
        
        # Create profiles with realistic distribution
        profiles = []
        
        # Small organizations (60%)
        for _ in range(60):
            profile = TestDataFactory.create_test_profile(
                revenue=random.randint(50000, 500000),
                staff_count=random.randint(1, 15)
            )
            profiles.append(profile)
        
        # Medium organizations (30%)
        for _ in range(30):
            profile = TestDataFactory.create_test_profile(
                revenue=random.randint(500000, 5000000),
                staff_count=random.randint(15, 75)
            )
            profiles.append(profile)
        
        # Large organizations (10%)
        for _ in range(10):
            profile = TestDataFactory.create_test_profile(
                revenue=random.randint(5000000, 50000000),
                staff_count=random.randint(75, 500)
            )
            profiles.append(profile)
        
        # Create opportunities with realistic distribution
        opportunities = []
        
        # Small grants (50%)
        for _ in range(500):
            opp = TestDataFactory.create_test_opportunity(
                funding_amount=random.randint(5000, 50000)
            )
            opportunities.append(opp)
        
        # Medium grants (35%)
        for _ in range(350):
            opp = TestDataFactory.create_test_opportunity(
                funding_amount=random.randint(50000, 500000)
            )
            opportunities.append(opp)
        
        # Large grants (15%)
        for _ in range(150):
            opp = TestDataFactory.create_test_opportunity(
                funding_amount=random.randint(500000, 5000000)
            )
            opportunities.append(opp)
        
        return {
            "profiles": profiles,
            "opportunities": opportunities
        }


# Fixtures using the factories
@pytest.fixture
def test_profiles_batch():
    """Provide batch of test profiles"""
    return TestDataFactory.create_batch_test_data(10, "profile")


@pytest.fixture
def test_opportunities_batch():
    """Provide batch of test opportunities"""
    return TestDataFactory.create_batch_test_data(20, "opportunity")


@pytest.fixture
def large_performance_dataset():
    """Provide large dataset for performance testing"""
    return PerformanceDataFactory.create_large_dataset()


@pytest.fixture
def realistic_dataset():
    """Provide realistic dataset for testing"""
    return PerformanceDataFactory.create_realistic_dataset()


if __name__ == "__main__":
    # Test the fixtures
    print("Testing database fixtures...")
    
    # Create test database
    engine = DatabaseFixtures.create_test_database()
    DatabaseFixtures.populate_test_data(engine)
    
    # Test data factory
    print("Testing data factory...")
    profile = TestDataFactory.create_test_profile()
    print(f"Sample profile: {profile['organization_name']}")
    
    opportunity = TestDataFactory.create_test_opportunity()
    print(f"Sample opportunity: {opportunity['organization_name']}")
    
    # Cleanup
    DatabaseFixtures.cleanup_test_database()
    print("Database fixtures test completed.")