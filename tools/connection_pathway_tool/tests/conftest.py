"""
Pytest configuration for Connection Pathway Tool tests.
"""

import sys
import sqlite3
from pathlib import Path

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Add tool's app directory to Python path
tool_root = Path(__file__).parent.parent
sys.path.insert(0, str(tool_root))


@pytest.fixture
def pathway_db(tmp_path):
    """
    Create an in-memory SQLite DB pre-populated with people,
    organization_roles, profiles, and network_memberships tables.
    """
    db_path = str(tmp_path / "test_pathway.db")
    conn = sqlite3.connect(db_path)

    conn.executescript(
        """
        -- profiles table
        CREATE TABLE IF NOT EXISTS profiles (
            id   TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            ein  TEXT
        );

        -- people table
        CREATE TABLE IF NOT EXISTS people (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            normalized_name TEXT NOT NULL,
            original_name   TEXT NOT NULL,
            name_hash       TEXT UNIQUE,
            first_name      TEXT,
            last_name       TEXT,
            middle_name     TEXT,
            prefix          TEXT,
            suffix          TEXT,
            biography       TEXT,
            linkedin_url    TEXT,
            personal_website TEXT,
            data_quality_score INTEGER DEFAULT 50,
            confidence_level   REAL DEFAULT 0.5,
            source_count    INTEGER DEFAULT 1,
            created_at      TIMESTAMP,
            updated_at      TIMESTAMP,
            last_verified_at TIMESTAMP
        );

        -- organization_roles table
        CREATE TABLE IF NOT EXISTS organization_roles (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id           INTEGER NOT NULL REFERENCES people(id),
            organization_ein    TEXT NOT NULL,
            organization_name   TEXT NOT NULL,
            title               TEXT NOT NULL,
            position_type       TEXT DEFAULT 'board',
            position_category   TEXT,
            start_date          DATE,
            end_date            DATE,
            is_current          BOOLEAN DEFAULT TRUE,
            tenure_years        REAL,
            data_source         TEXT NOT NULL,
            source_url          TEXT,
            filing_year         INTEGER,
            web_intelligence_id TEXT,
            verification_status TEXT DEFAULT 'unverified',
            quality_score       INTEGER DEFAULT 50,
            created_at          TIMESTAMP,
            updated_at          TIMESTAMP,
            UNIQUE(person_id, organization_ein, title, data_source)
        );

        -- network_memberships table (fallback)
        CREATE TABLE IF NOT EXISTS network_memberships (
            id           TEXT PRIMARY KEY,
            person_hash  TEXT NOT NULL,
            display_name TEXT NOT NULL,
            org_ein      TEXT,
            org_name     TEXT NOT NULL,
            org_type     TEXT NOT NULL,
            profile_id   TEXT,
            source       TEXT NOT NULL,
            title        TEXT,
            created_at   TEXT NOT NULL,
            updated_at   TEXT NOT NULL,
            UNIQUE(person_hash, org_ein)
        );

        -- Seed profiles
        INSERT INTO profiles (id, name, ein) VALUES
            ('profile_001', 'Seeker Nonprofit', '11-1111111'),
            ('profile_002', 'Another Org', '22-2222222');

        -- Seed people
        -- Person 1: Alice — at seeker and funder (direct connection)
        INSERT INTO people (id, normalized_name, original_name, name_hash)
            VALUES (1, 'alice johnson', 'Alice Johnson', 'hash_alice');

        -- Person 2: Bob — at seeker only
        INSERT INTO people (id, normalized_name, original_name, name_hash)
            VALUES (2, 'bob smith', 'Bob Smith', 'hash_bob');

        -- Person 3: Carol — at intermediary org and funder (for 2-hop)
        INSERT INTO people (id, normalized_name, original_name, name_hash)
            VALUES (3, 'carol white', 'Carol White', 'hash_carol');

        -- Person 4: Dave — at intermediary org only (for 3-hop testing)
        INSERT INTO people (id, normalized_name, original_name, name_hash)
            VALUES (4, 'dave brown', 'Dave Brown', 'hash_dave');

        -- Person 5: Eve — at funder only (isolated)
        INSERT INTO people (id, normalized_name, original_name, name_hash)
            VALUES (5, 'eve green', 'Eve Green', 'hash_eve');

        -- Seed organization_roles
        -- Alice at seeker
        INSERT INTO organization_roles
            (person_id, organization_ein, organization_name, title, position_type, is_current, data_source)
            VALUES (1, '11-1111111', 'Seeker Nonprofit', 'Board Member', 'board', 1, 'test');

        -- Alice at funder (direct connection!)
        INSERT INTO organization_roles
            (person_id, organization_ein, organization_name, title, position_type, is_current, data_source)
            VALUES (1, '99-9999999', 'Target Foundation', 'Advisor', 'advisory', 1, 'test');

        -- Bob at seeker
        INSERT INTO organization_roles
            (person_id, organization_ein, organization_name, title, position_type, is_current, data_source)
            VALUES (2, '11-1111111', 'Seeker Nonprofit', 'Executive Director', 'executive', 1, 'test');

        -- Bob at intermediary
        INSERT INTO organization_roles
            (person_id, organization_ein, organization_name, title, position_type, is_current, data_source)
            VALUES (2, '55-5555555', 'Intermediary Org', 'Board Member', 'board', 1, 'test');

        -- Carol at intermediary
        INSERT INTO organization_roles
            (person_id, organization_ein, organization_name, title, position_type, is_current, data_source)
            VALUES (3, '55-5555555', 'Intermediary Org', 'President', 'executive', 1, 'test');

        -- Carol at funder
        INSERT INTO organization_roles
            (person_id, organization_ein, organization_name, title, position_type, is_current, data_source)
            VALUES (3, '99-9999999', 'Target Foundation', 'Board Member', 'board', 1, 'test');

        -- Dave at a second intermediary
        INSERT INTO organization_roles
            (person_id, organization_ein, organization_name, title, position_type, is_current, data_source)
            VALUES (4, '66-6666666', 'Second Intermediary', 'Staff', 'staff', 1, 'test');

        -- Eve at funder only
        INSERT INTO organization_roles
            (person_id, organization_ein, organization_name, title, position_type, is_current, data_source)
            VALUES (5, '99-9999999', 'Target Foundation', 'CEO', 'executive', 1, 'test');

        -- Seed network_memberships (for fallback test)
        INSERT INTO network_memberships
            (id, person_hash, display_name, org_ein, org_name, org_type, profile_id, source, title, created_at, updated_at)
            VALUES
            ('nm1', 'phash_x', 'Xavier Lee', '11-1111111', 'Seeker Nonprofit', 'nonprofit', 'profile_001', 'test', 'Director', '2025-01-01', '2025-01-01'),
            ('nm2', 'phash_x', 'Xavier Lee', '99-9999999', 'Target Foundation', 'foundation', NULL, 'test', 'Trustee', '2025-01-01', '2025-01-01'),
            ('nm3', 'phash_y', 'Yolanda Cruz', '11-1111111', 'Seeker Nonprofit', 'nonprofit', 'profile_001', 'test', 'Board Chair', '2025-01-01', '2025-01-01'),
            ('nm4', 'phash_z', 'Zack Patel', '77-7777777', 'Bridge Org', 'nonprofit', NULL, 'test', 'VP', '2025-01-01', '2025-01-01'),
            ('nm5', 'phash_y', 'Yolanda Cruz', '77-7777777', 'Bridge Org', 'nonprofit', NULL, 'test', 'Advisor', '2025-01-01', '2025-01-01'),
            ('nm6', 'phash_z', 'Zack Patel', '99-9999999', 'Target Foundation', 'foundation', NULL, 'test', 'Program Officer', '2025-01-01', '2025-01-01');
        """
    )
    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def empty_people_db(tmp_path):
    """
    DB with network_memberships but empty people table (for fallback test).
    """
    db_path = str(tmp_path / "test_fallback.db")
    conn = sqlite3.connect(db_path)

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS profiles (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, ein TEXT
        );
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            normalized_name TEXT NOT NULL,
            original_name TEXT NOT NULL,
            name_hash TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS organization_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            organization_ein TEXT NOT NULL,
            organization_name TEXT NOT NULL,
            title TEXT NOT NULL,
            position_type TEXT DEFAULT 'board',
            is_current BOOLEAN DEFAULT TRUE,
            data_source TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS network_memberships (
            id TEXT PRIMARY KEY,
            person_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            org_ein TEXT,
            org_name TEXT NOT NULL,
            org_type TEXT NOT NULL,
            profile_id TEXT,
            source TEXT NOT NULL,
            title TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(person_hash, org_ein)
        );

        INSERT INTO profiles (id, name, ein) VALUES ('profile_001', 'Seeker Nonprofit', '11-1111111');

        -- Only memberships, no people rows
        INSERT INTO network_memberships
            (id, person_hash, display_name, org_ein, org_name, org_type, profile_id, source, title, created_at, updated_at)
            VALUES
            ('nm1', 'ph_a', 'Amy Lin', '11-1111111', 'Seeker Nonprofit', 'nonprofit', 'profile_001', 'test', 'Director', '2025-01-01', '2025-01-01'),
            ('nm2', 'ph_a', 'Amy Lin', '99-9999999', 'Target Foundation', 'foundation', NULL, 'test', 'Trustee', '2025-01-01', '2025-01-01');
        """
    )
    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def no_connection_db(tmp_path):
    """
    DB with people but no shared connections to the target funder.
    """
    db_path = str(tmp_path / "test_no_conn.db")
    conn = sqlite3.connect(db_path)

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS profiles (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, ein TEXT
        );
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            normalized_name TEXT NOT NULL,
            original_name TEXT NOT NULL,
            name_hash TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS organization_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            organization_ein TEXT NOT NULL,
            organization_name TEXT NOT NULL,
            title TEXT NOT NULL,
            position_type TEXT DEFAULT 'board',
            is_current BOOLEAN DEFAULT TRUE,
            data_source TEXT NOT NULL
        );

        INSERT INTO profiles (id, name, ein) VALUES ('profile_001', 'Seeker Nonprofit', '11-1111111');

        -- Person at seeker only, nobody at funder
        INSERT INTO people (id, normalized_name, original_name, name_hash)
            VALUES (1, 'lonely larry', 'Lonely Larry', 'hash_lonely');
        INSERT INTO organization_roles
            (person_id, organization_ein, organization_name, title, data_source)
            VALUES (1, '11-1111111', 'Seeker Nonprofit', 'Board Member', 'test');
        """
    )
    conn.commit()
    conn.close()

    return db_path
