"""
Tests for PersonDeduplicationService — find and merge duplicate person records.

Uses temporary SQLite files via pytest's tmp_path fixture. No external
services required.
"""

import sqlite3
from datetime import datetime, timezone

import pytest

from src.network.name_normalizer import NameNormalizer
from src.network.person_deduplication import PersonDeduplicationService


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

_PEOPLE_DDL = """
CREATE TABLE IF NOT EXISTS people (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    normalized_name TEXT    NOT NULL,
    original_name   TEXT    NOT NULL,
    name_hash       TEXT    UNIQUE,
    first_name      TEXT,
    last_name       TEXT,
    middle_name     TEXT,
    prefix          TEXT,
    suffix          TEXT,
    biography       TEXT,
    linkedin_url    TEXT,
    personal_website TEXT,
    data_quality_score INTEGER DEFAULT 50,
    confidence_level   REAL    DEFAULT 0.5,
    source_count    INTEGER DEFAULT 1,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP,
    last_verified_at TIMESTAMP
);
"""

_ROLES_DDL = """
CREATE TABLE IF NOT EXISTS organization_roles (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id           INTEGER NOT NULL REFERENCES people(id),
    organization_ein    TEXT    NOT NULL,
    organization_name   TEXT    NOT NULL,
    title               TEXT    NOT NULL,
    position_type       TEXT    DEFAULT 'board',
    position_category   TEXT,
    start_date          DATE,
    end_date            DATE,
    is_current          BOOLEAN DEFAULT TRUE,
    tenure_years        REAL,
    data_source         TEXT    NOT NULL,
    source_url          TEXT,
    filing_year         INTEGER,
    web_intelligence_id TEXT,
    verification_status TEXT    DEFAULT 'unverified',
    quality_score       INTEGER DEFAULT 50,
    created_at          TIMESTAMP,
    updated_at          TIMESTAMP,
    UNIQUE(person_id, organization_ein, title, data_source)
);
"""


def _make_db(tmp_path):
    """Create a fresh test database with people and organization_roles tables."""
    db_path = str(tmp_path / "dedup_test.db")
    conn = sqlite3.connect(db_path)
    conn.executescript(_PEOPLE_DDL + _ROLES_DDL)
    conn.commit()
    conn.close()
    return db_path


def _insert_person(conn, *, original_name, normalized_name=None, name_hash=None,
                   first_name=None, last_name=None, quality=50, source_count=1):
    """Insert a person and return the new row id."""
    normalizer = NameNormalizer()
    if normalized_name is None:
        normalized_name = normalizer.normalize(original_name)
    if name_hash is None:
        name_hash = normalizer.person_hash(original_name)
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "INSERT INTO people "
        "(normalized_name, original_name, name_hash, first_name, last_name, "
        "data_quality_score, source_count, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (normalized_name, original_name, name_hash, first_name, last_name,
         quality, source_count, now, now),
    )
    return cursor.lastrowid


def _insert_role(conn, person_id, *, ein="11-1111111", org_name="Org A",
                 title="Board Member", position_type="board", data_source="990_filing",
                 quality_score=50):
    """Insert an organization_role row."""
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO organization_roles "
        "(person_id, organization_ein, organization_name, title, position_type, "
        "data_source, quality_score, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (person_id, ein, org_name, title, position_type, data_source, quality_score,
         now, now),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_path(tmp_path):
    return _make_db(tmp_path)


@pytest.fixture()
def svc(db_path):
    return PersonDeduplicationService(db_path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFindExactDuplicates:
    def test_find_exact_duplicates(self, db_path, svc):
        """Two people with the same normalized_name but different ids should be
        detected as duplicates with high confidence."""
        conn = sqlite3.connect(db_path)
        _insert_person(
            conn, original_name="John Smith", name_hash="aaa111",
            first_name="john", last_name="smith",
            normalized_name="john smith",
        )
        _insert_person(
            conn, original_name="JOHN SMITH", name_hash="bbb222",
            first_name="john", last_name="smith",
            normalized_name="john smith",
        )
        conn.commit()
        conn.close()

        dupes = svc.find_duplicates(min_confidence=0.5)
        assert len(dupes) >= 1
        pair = dupes[0]
        assert pair["confidence"] >= 0.90
        assert "exact_normalized_name" in pair["match_reasons"]


class TestFindSimilarNames:
    def test_find_similar_names(self, db_path, svc):
        """John Smith and John Smyth share first initial + last-name prefix,
        so they should appear as candidates (possibly lower confidence)."""
        conn = sqlite3.connect(db_path)
        _insert_person(
            conn, original_name="John Smith", name_hash="aaa111",
            first_name="john", last_name="smith",
            normalized_name="john smith",
        )
        _insert_person(
            conn, original_name="John Smyth", name_hash="bbb222",
            first_name="john", last_name="smyth",
            normalized_name="john smyth",
        )
        conn.commit()
        conn.close()

        dupes = svc.find_duplicates(min_confidence=0.5)
        assert len(dupes) >= 1
        pair = dupes[0]
        # Should be found via last_name_first_initial or fuzzy strategies
        assert pair["confidence"] < 0.95  # not exact


class TestSharedOrgBoost:
    def test_shared_org_increases_confidence(self, db_path, svc):
        """Two similar names sharing an organisation should receive a +0.15
        confidence boost."""
        conn = sqlite3.connect(db_path)
        pid_a = _insert_person(
            conn, original_name="John Smith", name_hash="aaa111",
            first_name="john", last_name="smith",
            normalized_name="john smith",
        )
        pid_b = _insert_person(
            conn, original_name="John Smyth", name_hash="bbb222",
            first_name="john", last_name="smyth",
            normalized_name="john smyth",
        )
        # Both at the same organisation
        _insert_role(conn, pid_a, ein="99-0000001", org_name="Shared Org")
        _insert_role(conn, pid_b, ein="99-0000001", org_name="Shared Org",
                     title="Director")
        conn.commit()
        conn.close()

        dupes_with_org = svc.find_duplicates(min_confidence=0.5)
        assert len(dupes_with_org) >= 1
        pair = dupes_with_org[0]
        assert "shared_organization" in pair["match_reasons"]
        assert len(pair["shared_orgs"]) >= 1

        # Verify boost was applied -- confidence should be higher than base
        # fuzzy/last-name match alone (~0.65-0.70) by at least ~0.10
        assert pair["confidence"] >= 0.75


class TestMergePeople:
    def test_merge_transfers_roles_and_deletes_old(self, db_path, svc):
        conn = sqlite3.connect(db_path)
        pid_keep = _insert_person(
            conn, original_name="Alice Johnson", name_hash="keep111",
            first_name="alice", last_name="johnson", quality=80,
        )
        pid_merge = _insert_person(
            conn, original_name="Alice M. Johnson", name_hash="merge222",
            first_name="alice", last_name="johnson", quality=60,
        )
        # Role on keep
        _insert_role(conn, pid_keep, ein="11-1111111", org_name="Org A",
                     title="Chair", quality_score=80)
        # Role on merge (different org -- should transfer)
        _insert_role(conn, pid_merge, ein="22-2222222", org_name="Org B",
                     title="Director", quality_score=70)
        conn.commit()
        conn.close()

        result = svc.merge_people(keep_id=pid_keep, merge_id=pid_merge)
        assert result["success"] is True
        assert result["roles_transferred"] == 1

        # Verify merge_id person is deleted
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        remaining = conn.execute("SELECT * FROM people").fetchall()
        assert len(remaining) == 1
        assert remaining[0]["id"] == pid_keep

        roles = conn.execute(
            "SELECT * FROM organization_roles WHERE person_id = ?", (pid_keep,)
        ).fetchall()
        assert len(roles) == 2
        conn.close()

    def test_merge_handles_conflicting_roles(self, db_path, svc):
        """When both people have a role at the same org+title, the higher
        quality_score wins."""
        conn = sqlite3.connect(db_path)
        pid_keep = _insert_person(
            conn, original_name="Bob Smith", name_hash="keep333",
            first_name="bob", last_name="smith",
        )
        pid_merge = _insert_person(
            conn, original_name="Robert Smith", name_hash="merge444",
            first_name="robert", last_name="smith",
        )
        # Same org+title on both
        _insert_role(conn, pid_keep, ein="11-1111111", org_name="Same Org",
                     title="Treasurer", quality_score=50)
        _insert_role(conn, pid_merge, ein="11-1111111", org_name="Same Org",
                     title="Treasurer", quality_score=90)
        conn.commit()
        conn.close()

        result = svc.merge_people(keep_id=pid_keep, merge_id=pid_merge)
        assert result["success"] is True
        assert result["conflicts_resolved"] == 1

        # The higher-quality role (90) should survive
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        roles = conn.execute(
            "SELECT * FROM organization_roles WHERE person_id = ?", (pid_keep,)
        ).fetchall()
        assert len(roles) == 1
        assert roles[0]["quality_score"] == 90
        conn.close()

    def test_merge_nonexistent_person_fails(self, db_path, svc):
        result = svc.merge_people(keep_id=9999, merge_id=8888)
        assert result["success"] is False


class TestAutoMerge:
    def test_auto_merge_exact_duplicates(self, db_path, svc):
        """Insert two people with the same normalized_name, run auto_merge,
        verify one is merged away."""
        conn = sqlite3.connect(db_path)
        _insert_person(
            conn, original_name="Jane Doe", name_hash="auto1",
            first_name="jane", last_name="doe",
            normalized_name="jane doe",
        )
        _insert_person(
            conn, original_name="JANE DOE", name_hash="auto2",
            first_name="jane", last_name="doe",
            normalized_name="jane doe",
        )
        conn.commit()
        conn.close()

        result = svc.auto_merge(min_confidence=0.90)
        assert result["pairs_found"] >= 1
        assert result["pairs_merged"] >= 1

        # Verify only one person remains
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        assert count == 1
        conn.close()


class TestMergeHistory:
    def test_merge_history_recorded(self, db_path, svc):
        conn = sqlite3.connect(db_path)
        pid_keep = _insert_person(
            conn, original_name="Carol White", name_hash="hist1",
            first_name="carol", last_name="white",
        )
        pid_merge = _insert_person(
            conn, original_name="Carol M White", name_hash="hist2",
            first_name="carol", last_name="white",
        )
        conn.commit()
        conn.close()

        svc.merge_people(keep_id=pid_keep, merge_id=pid_merge, merged_by="test_user")

        history = svc.get_merge_history(limit=10)
        assert len(history) >= 1
        entry = history[0]
        assert entry["kept_person_id"] == pid_keep
        assert entry["merged_person_id"] == pid_merge
        assert "test_user" in entry["merge_reason"]
        assert entry["merged_by"] == "test_user"
