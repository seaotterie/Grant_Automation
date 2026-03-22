"""
Tests for PeopleETL — migration of network_memberships into normalised
people + organization_roles tables.

Uses temporary SQLite files via pytest's tmp_path fixture. No external
services required.
"""

import sqlite3

import pytest

from src.network.people_etl import PeopleETL


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MEMBERSHIPS_DDL = """
CREATE TABLE IF NOT EXISTS network_memberships (
    id TEXT,
    person_hash TEXT,
    display_name TEXT,
    org_ein TEXT,
    org_name TEXT,
    org_type TEXT,
    profile_id TEXT,
    source TEXT,
    title TEXT,
    created_at TEXT,
    updated_at TEXT,
    UNIQUE(person_hash, org_ein)
);
"""

_PROFILES_DDL = """
CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    name TEXT,
    ein TEXT
);
"""


def _make_db(tmp_path, *, with_memberships: bool = False):
    """Return the path to a fresh SQLite database. Optionally create the
    network_memberships table."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.execute(_PROFILES_DDL)
    if with_memberships:
        conn.execute(_MEMBERSHIPS_DDL)
    conn.commit()
    conn.close()
    return db_path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_path(tmp_path):
    """Database path with memberships table pre-created."""
    return _make_db(tmp_path, with_memberships=True)


@pytest.fixture()
def etl(db_path):
    """PeopleETL instance wired to the test database."""
    inst = PeopleETL(db_path)
    inst.ensure_tables()
    return inst


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEnsureTables:
    def test_ensure_tables_creates_people_and_roles(self, tmp_path):
        db_path = _make_db(tmp_path, with_memberships=False)
        etl = PeopleETL(db_path)
        etl.ensure_tables()

        conn = sqlite3.connect(db_path)
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()

        assert "people" in tables
        assert "organization_roles" in tables

    def test_ensure_tables_idempotent(self, tmp_path):
        """Calling ensure_tables twice must not raise."""
        db_path = _make_db(tmp_path, with_memberships=False)
        etl = PeopleETL(db_path)
        etl.ensure_tables()
        etl.ensure_tables()  # second call should not error


class TestParseNameParts:
    def test_full_name_with_prefix_and_suffix(self, etl):
        parts = etl._parse_name_parts("Dr. John Michael Smith Jr.")
        assert parts["first_name"].lower() == "john"
        assert parts["last_name"].lower() == "smith"
        assert parts["middle_name"].lower() == "michael"
        assert parts["prefix"].lower().rstrip(".") == "dr"
        assert parts["suffix"].lower().rstrip(".") == "jr"

    def test_simple_two_token_name(self, etl):
        parts = etl._parse_name_parts("Jane Doe")
        assert parts["first_name"] == "Jane"
        assert parts["last_name"] == "Doe"
        assert parts["middle_name"] is None
        assert parts["prefix"] is None
        assert parts["suffix"] is None

    def test_single_token_name(self, etl):
        parts = etl._parse_name_parts("Madonna")
        assert parts["first_name"] == "Madonna"
        assert parts["last_name"] is None

    def test_empty_name(self, etl):
        parts = etl._parse_name_parts("")
        assert parts["first_name"] is None
        assert parts["last_name"] is None

    def test_parenthetical_stripped(self, etl):
        parts = etl._parse_name_parts("Alice Wonderland (Board Chair)")
        assert parts["first_name"] == "Alice"
        assert parts["last_name"] == "Wonderland"


class TestClassifyPosition:
    @pytest.mark.parametrize(
        "title, expected_type, expected_category",
        [
            ("Board Chair", "board", "chair"),
            ("CEO", "executive", "ceo"),
            ("Program Director", "board", "member"),
            ("Advisory Board Member", "advisory", "advisor"),
            ("Chief Financial Officer", "executive", "cfo"),
            ("Treasurer", "board", "treasurer"),
            ("Manager of Operations", "staff", "manager"),
        ],
    )
    def test_classify_position(self, etl, title, expected_type, expected_category):
        pos_type, pos_cat = etl._classify_position(title)
        assert pos_type == expected_type
        assert pos_cat == expected_category

    def test_empty_title_defaults_to_board_member(self, etl):
        pos_type, pos_cat = etl._classify_position("")
        assert pos_type == "board"
        assert pos_cat == "member"


class TestQualityScore:
    def test_990_filing_with_title_and_ein(self, etl):
        score = etl._calculate_quality_score("990_filing", has_title=True, has_ein=True)
        # base=85 + title=10 + ein=5 = 100 (capped)
        assert score == 100

    def test_web_data_no_title(self, etl):
        score = etl._calculate_quality_score("web_data", has_title=False, has_ein=False)
        # base=60, no bonuses
        assert score == 60

    def test_unknown_source_minimum(self, etl):
        score = etl._calculate_quality_score("random_source", has_title=False, has_ein=False)
        # default=40
        assert score == 40

    def test_score_capped_at_100(self, etl):
        score = etl._calculate_quality_score("990_filing", has_title=True, has_ein=True)
        assert score <= 100

    def test_score_minimum_is_one(self, etl):
        # Even a low source should not go below 1
        score = etl._calculate_quality_score("unknown", has_title=False, has_ein=False)
        assert score >= 1


class TestMigrateFromMemberships:
    def test_basic_migration(self, db_path, etl):
        # Insert test rows into network_memberships
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO network_memberships "
            "(id, person_hash, display_name, org_ein, org_name, org_type, "
            "profile_id, source, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "m1", "hash1", "Alice Johnson", "12-3456789",
                "Good Foundation", "funder", "prof1", "990_filing",
                "Board Chair", "2025-01-01", "2025-01-01",
            ),
        )
        conn.execute(
            "INSERT INTO network_memberships "
            "(id, person_hash, display_name, org_ein, org_name, org_type, "
            "profile_id, source, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "m2", "hash2", "Bob Williams", "98-7654321",
                "Better Foundation", "funder", "prof1", "web_data",
                "CEO", "2025-01-01", "2025-01-01",
            ),
        )
        conn.commit()
        conn.close()

        stats = etl.migrate_from_memberships()

        assert stats["people_created"] == 2
        assert stats["roles_created"] == 2
        assert stats["errors"] == 0

        # Verify people table
        conn = sqlite3.connect(db_path)
        people = conn.execute("SELECT * FROM people").fetchall()
        assert len(people) == 2

        roles = conn.execute("SELECT * FROM organization_roles").fetchall()
        assert len(roles) == 2
        conn.close()

    def test_empty_display_name_counted_as_error(self, db_path, etl):
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO network_memberships "
            "(id, person_hash, display_name, org_ein, org_name, org_type, "
            "profile_id, source, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "m1", "hash1", "", "12-3456789",
                "Good Foundation", "funder", "prof1", "990_filing",
                "Board Chair", "2025-01-01", "2025-01-01",
            ),
        )
        conn.commit()
        conn.close()

        stats = etl.migrate_from_memberships()
        assert stats["people_created"] == 0
        assert stats["errors"] == 1

    def test_duplicate_person_updates_source_count(self, db_path, etl):
        conn = sqlite3.connect(db_path)
        # Two memberships for the same person at different orgs
        conn.execute(
            "INSERT INTO network_memberships "
            "(id, person_hash, display_name, org_ein, org_name, org_type, "
            "profile_id, source, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "m1", "hash1", "Alice Johnson", "12-3456789",
                "Good Foundation", "funder", "prof1", "990_filing",
                "Board Chair", "2025-01-01", "2025-01-01",
            ),
        )
        conn.execute(
            "INSERT INTO network_memberships "
            "(id, person_hash, display_name, org_ein, org_name, org_type, "
            "profile_id, source, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "m2", "hash2", "Alice Johnson", "98-7654321",
                "Better Foundation", "funder", "prof1", "web_data",
                "Director", "2025-01-01", "2025-01-01",
            ),
        )
        conn.commit()
        conn.close()

        stats = etl.migrate_from_memberships()
        assert stats["people_created"] == 1
        assert stats["people_updated"] == 1
        assert stats["roles_created"] == 2

    def test_no_memberships_table(self, tmp_path):
        """When network_memberships does not exist, migration returns zeros."""
        db_path = _make_db(tmp_path, with_memberships=False)
        etl = PeopleETL(db_path)
        etl.ensure_tables()
        stats = etl.migrate_from_memberships()
        assert stats["people_created"] == 0
        assert stats["errors"] == 0


class TestIngestFrom990Officers:
    def test_basic_officer_ingestion(self, db_path, etl):
        officers = [
            {
                "name": "Carol Davis",
                "title": "President",
                "hours_per_week": 40,
                "compensation": 120000,
                "is_officer": True,
                "is_director": False,
                "is_trustee": False,
                "is_key_employee": False,
            },
            {
                "name": "David Lee",
                "title": "Trustee",
                "hours_per_week": 2,
                "compensation": 0,
                "is_officer": False,
                "is_director": False,
                "is_trustee": True,
                "is_key_employee": False,
            },
        ]

        stats = etl.ingest_from_990_officers(
            ein="55-1234567",
            org_name="Helpful Charity",
            officers=officers,
            filing_year=2024,
        )

        assert stats["people_created"] == 2
        assert stats["roles_created"] == 2
        assert stats["errors"] == 0

        # Verify data in DB
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        people = conn.execute("SELECT * FROM people").fetchall()
        assert len(people) == 2

        roles = conn.execute("SELECT * FROM organization_roles").fetchall()
        assert len(roles) == 2

        # Check filing_year stored
        for role in roles:
            assert role["filing_year"] == 2024
            assert role["data_source"] == "990_filing"
        conn.close()

    def test_empty_name_officer_skipped(self, db_path, etl):
        officers = [
            {"name": "", "title": "Director"},
        ]
        stats = etl.ingest_from_990_officers(
            ein="55-1234567",
            org_name="Helpful Charity",
            officers=officers,
            filing_year=2024,
        )
        assert stats["people_created"] == 0
        assert stats["errors"] == 1

    def test_officer_upsert_updates_existing(self, db_path, etl):
        officer = {
            "name": "Carol Davis",
            "title": "President",
            "is_officer": True,
            "is_director": False,
            "is_trustee": False,
            "is_key_employee": False,
        }

        # First ingestion
        stats1 = etl.ingest_from_990_officers(
            ein="55-1234567", org_name="Helpful Charity",
            officers=[officer], filing_year=2023,
        )
        assert stats1["people_created"] == 1
        assert stats1["roles_created"] == 1

        # Second ingestion, same person + org + title + source => update
        stats2 = etl.ingest_from_990_officers(
            ein="55-1234567", org_name="Helpful Charity",
            officers=[officer], filing_year=2024,
        )
        assert stats2["people_updated"] == 1
        assert stats2["roles_updated"] == 1
        assert stats2["people_created"] == 0
        assert stats2["roles_created"] == 0
