"""
Tests for post-screening network analysis features:
  - Funder-to-funder connections (PathFinder.find_funder_connections)
  - Funder cluster detection (PathFinder.find_funder_clusters)
  - Grant-win warm paths (PathFinder.find_warm_paths)
  - PostScreeningAnalyzer full report
  - Network diagnostics

Uses temporary SQLite files via pytest's tmp_path fixture.
"""

import sqlite3
from datetime import datetime, timezone

import pytest

from src.network.path_finder import PathFinder, FunderConnection, WarmPath
from src.network.post_screening_analyzer import (
    PostScreeningAnalyzer,
    PostScreeningReport,
    NetworkDiagnostic,
)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    id              TEXT PRIMARY KEY,
    name            TEXT,
    ein             TEXT,
    board_members   TEXT,
    mission_statement TEXT,
    focus_areas     TEXT,
    program_areas   TEXT,
    ntee_codes      TEXT,
    service_areas   TEXT,
    location        TEXT,
    annual_revenue  REAL
);

CREATE TABLE IF NOT EXISTS opportunities (
    id                  TEXT PRIMARY KEY,
    profile_id          TEXT NOT NULL,
    ein                 TEXT,
    organization_name   TEXT,
    analysis_discovery  TEXT,
    current_stage       TEXT DEFAULT 'discovery',
    overall_score       REAL,
    created_at          TIMESTAMP,
    updated_at          TIMESTAMP
);

CREATE TABLE IF NOT EXISTS network_memberships (
    id              TEXT PRIMARY KEY,
    person_hash     TEXT NOT NULL,
    display_name    TEXT NOT NULL,
    org_ein         TEXT,
    org_name        TEXT,
    org_type        TEXT NOT NULL,  -- 'seeker' or 'funder'
    profile_id      TEXT,
    source          TEXT,
    title           TEXT,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP,
    UNIQUE(id)
);

CREATE TABLE IF NOT EXISTS ein_intelligence (
    ein             TEXT PRIMARY KEY,
    web_data        TEXT,
    pdf_analyses    TEXT,
    filing_history  TEXT,
    updated_at      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS grant_wins (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id      TEXT NOT NULL,
    funder_name     TEXT NOT NULL,
    funder_ein      TEXT,
    amount          REAL,
    award_date      TEXT,
    award_year      INTEGER,
    program_name    TEXT,
    grant_purpose   TEXT,
    grant_type      TEXT,
    notes           TEXT,
    source          TEXT DEFAULT 'manual',
    source_ref      TEXT,
    win_hash        TEXT UNIQUE,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS grant_win_contacts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    grant_win_id    INTEGER NOT NULL REFERENCES grant_wins(id),
    person_id       INTEGER,
    contact_name    TEXT NOT NULL,
    contact_role    TEXT,
    side            TEXT DEFAULT 'funder',
    linked_at       TIMESTAMP,
    link_source     TEXT DEFAULT 'auto',
    UNIQUE(grant_win_id, contact_name, side)
);

CREATE TABLE IF NOT EXISTS people (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    normalized_name TEXT NOT NULL,
    original_name   TEXT NOT NULL,
    name_hash       TEXT UNIQUE,
    first_name      TEXT,
    last_name       TEXT,
    data_quality_score INTEGER DEFAULT 50,
    confidence_level REAL DEFAULT 0.5,
    source_count    INTEGER DEFAULT 1,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP
);
"""

NOW = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_path(tmp_path):
    """Create a temp database with the required schema."""
    path = str(tmp_path / "test.db")
    conn = sqlite3.connect(path)
    conn.executescript(_SCHEMA)
    conn.close()
    return path


@pytest.fixture
def populated_db(db_path):
    """Database with profile, opportunities, and network memberships for testing."""
    conn = sqlite3.connect(db_path)

    # Profile with board members
    conn.execute(
        "INSERT INTO profiles (id, name, board_members) VALUES (?, ?, ?)",
        ("prof1", "Test Nonprofit", '[{"name": "Alice Johnson", "title": "Board Chair"}]'),
    )

    # 5 funder opportunities
    for i, (ein, name) in enumerate([
        ("11-1111111", "Alpha Foundation"),
        ("22-2222222", "Beta Fund"),
        ("33-3333333", "Gamma Trust"),
        ("44-4444444", "Delta Foundation"),
        ("55-5555555", "Epsilon Fund"),
    ]):
        conn.execute(
            "INSERT INTO opportunities (id, profile_id, ein, organization_name) "
            "VALUES (?, 'prof1', ?, ?)",
            (f"opp{i+1}", ein, name),
        )

    # Seeker board member in network
    conn.execute(
        "INSERT INTO network_memberships (id, person_hash, display_name, org_ein, org_name, "
        "org_type, profile_id, source, title, created_at, updated_at) "
        "VALUES ('s1', 'hash_alice', 'Alice Johnson', NULL, 'Test Nonprofit', "
        "'seeker', 'prof1', 'board_members', 'Board Chair', ?, ?)",
        (NOW, NOW),
    )

    # Funder officers — some shared across funders
    funder_people = [
        # person_hash, name, ein, org_name, title
        ("hash_bob", "Bob Smith", "11-1111111", "Alpha Foundation", "Director"),
        ("hash_bob", "Bob Smith", "22-2222222", "Beta Fund", "Trustee"),       # shared!
        ("hash_carol", "Carol White", "22-2222222", "Beta Fund", "Director"),
        ("hash_carol", "Carol White", "33-3333333", "Gamma Trust", "Board Chair"),  # shared!
        ("hash_dave", "Dave Brown", "33-3333333", "Gamma Trust", "Secretary"),
        ("hash_dave", "Dave Brown", "44-4444444", "Delta Foundation", "Trustee"),  # shared!
        ("hash_eve", "Eve Green", "44-4444444", "Delta Foundation", "Director"),
        ("hash_frank", "Frank Jones", "55-5555555", "Epsilon Fund", "President"),
        # Alice also appears at Alpha Foundation — direct overlap!
        ("hash_alice", "Alice Johnson", "11-1111111", "Alpha Foundation", "Advisory"),
    ]

    for idx, (ph, name, ein, org_name, title) in enumerate(funder_people):
        conn.execute(
            "INSERT INTO network_memberships (id, person_hash, display_name, org_ein, "
            "org_name, org_type, profile_id, source, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'funder', NULL, 'test', ?, ?, ?)",
            (f"f{idx+1}", ph, name, ein, org_name, title, NOW, NOW),
        )

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def db_with_grant_wins(populated_db):
    """Add grant win history to the populated database."""
    conn = sqlite3.connect(populated_db)

    # Past win from Alpha Foundation
    conn.execute(
        "INSERT INTO grant_wins (profile_id, funder_name, funder_ein, amount, "
        "award_year, program_name, source, win_hash) "
        "VALUES ('prof1', 'Alpha Foundation', '11-1111111', 50000, 2024, "
        "'Community Program', 'manual', 'win1')",
    )

    # Past win from an external funder NOT in opportunities
    conn.execute(
        "INSERT INTO grant_wins (profile_id, funder_name, funder_ein, amount, "
        "award_year, program_name, source, win_hash) "
        "VALUES ('prof1', 'Zeta Foundation', '99-9999999', 25000, 2023, "
        "'Education', 'manual', 'win2')",
    )

    # Add Zeta Foundation officers that overlap with Beta Fund
    conn.execute(
        "INSERT INTO network_memberships (id, person_hash, display_name, org_ein, "
        "org_name, org_type, source, title, created_at, updated_at) "
        "VALUES ('z1', 'hash_carol', 'Carol White', '99-9999999', 'Zeta Foundation', "
        "'funder', 'test', 'Director', ?, ?)",
        (NOW, NOW),
    )

    conn.commit()
    conn.close()
    return populated_db


# ---------------------------------------------------------------------------
# Tests: Funder-to-funder connections
# ---------------------------------------------------------------------------

class TestFunderConnections:
    def test_finds_shared_board_members(self, populated_db):
        finder = PathFinder(populated_db)
        connections = finder.find_funder_connections("prof1")

        assert len(connections) > 0
        # Bob connects Alpha ↔ Beta
        alpha_beta = [
            c for c in connections
            if {c.funder1_ein, c.funder2_ein} == {"11-1111111", "22-2222222"}
        ]
        assert len(alpha_beta) == 1
        assert alpha_beta[0].connection_count >= 1
        assert any("Bob" in p["name"] for p in alpha_beta[0].shared_people)

    def test_finds_chain_connections(self, populated_db):
        """Carol connects Beta ↔ Gamma, Dave connects Gamma ↔ Delta."""
        finder = PathFinder(populated_db)
        connections = finder.find_funder_connections("prof1")

        beta_gamma = [
            c for c in connections
            if {c.funder1_ein, c.funder2_ein} == {"22-2222222", "33-3333333"}
        ]
        assert len(beta_gamma) == 1

        gamma_delta = [
            c for c in connections
            if {c.funder1_ein, c.funder2_ein} == {"33-3333333", "44-4444444"}
        ]
        assert len(gamma_delta) == 1

    def test_isolated_funder_has_no_connections(self, populated_db):
        """Epsilon Fund has only Frank — no shared people with other funders."""
        finder = PathFinder(populated_db)
        connections = finder.find_funder_connections("prof1")

        epsilon_conns = [
            c for c in connections
            if "55-5555555" in (c.funder1_ein, c.funder2_ein)
        ]
        assert len(epsilon_conns) == 0

    def test_strength_classification(self, populated_db):
        finder = PathFinder(populated_db)
        connections = finder.find_funder_connections("prof1")

        for c in connections:
            if c.connection_count >= 3:
                assert c.strength == "strong"
            elif c.connection_count == 2:
                assert c.strength == "moderate"
            else:
                assert c.strength == "weak"

    def test_min_shared_filter(self, populated_db):
        finder = PathFinder(populated_db)
        # With min_shared=2, only connections with 2+ shared people
        connections = finder.find_funder_connections("prof1", min_shared=2)
        for c in connections:
            assert c.connection_count >= 2

    def test_empty_profile(self, db_path):
        finder = PathFinder(db_path)
        connections = finder.find_funder_connections("nonexistent")
        assert connections == []


# ---------------------------------------------------------------------------
# Tests: Funder clusters
# ---------------------------------------------------------------------------

class TestFunderClusters:
    def test_finds_connected_cluster(self, populated_db):
        """Alpha-Beta-Gamma-Delta should form a cluster via shared people chain."""
        finder = PathFinder(populated_db)
        clusters = finder.find_funder_clusters("prof1")

        assert len(clusters) >= 1
        # The largest cluster should contain Alpha, Beta, Gamma, Delta
        largest = clusters[0]
        cluster_eins = {f["ein"] for f in largest["funders"]}
        assert "11-1111111" in cluster_eins  # Alpha
        assert "22-2222222" in cluster_eins  # Beta
        assert "33-3333333" in cluster_eins  # Gamma

    def test_isolated_funder_not_in_cluster(self, populated_db):
        finder = PathFinder(populated_db)
        clusters = finder.find_funder_clusters("prof1")

        all_clustered_eins = set()
        for c in clusters:
            for f in c["funders"]:
                all_clustered_eins.add(f["ein"])

        # Epsilon has no shared people — not in any cluster
        assert "55-5555555" not in all_clustered_eins

    def test_cluster_stats(self, populated_db):
        finder = PathFinder(populated_db)
        clusters = finder.find_funder_clusters("prof1")

        for cluster in clusters:
            assert "cluster_id" in cluster
            assert cluster["size"] == len(cluster["funders"])
            assert cluster["internal_connections"] >= 0
            assert cluster["shared_people_count"] >= 0


# ---------------------------------------------------------------------------
# Tests: Grant-win warm paths
# ---------------------------------------------------------------------------

class TestWarmPaths:
    def test_direct_repeat_funder(self, db_with_grant_wins):
        """Alpha Foundation was a past funder and is in current opportunities."""
        finder = PathFinder(db_with_grant_wins)
        paths = finder.find_warm_paths("prof1")

        alpha_paths = [p for p in paths if p.funder_ein == "11-1111111"]
        assert len(alpha_paths) >= 1
        direct = [p for p in alpha_paths if p.source == "grant_win_direct"]
        assert len(direct) == 1
        assert direct[0].warmth_score >= 0.8

    def test_funder_bridge_via_shared_people(self, db_with_grant_wins):
        """Zeta Foundation (past win) shares Carol with Beta Fund (target)."""
        finder = PathFinder(db_with_grant_wins)
        paths = finder.find_warm_paths("prof1")

        beta_paths = [p for p in paths if p.funder_ein == "22-2222222"]
        bridge_paths = [p for p in beta_paths if p.source == "grant_win_funder_bridge"]
        assert len(bridge_paths) >= 1
        assert bridge_paths[0].connected_funder_ein == "99-9999999"

    def test_no_wins_returns_empty(self, populated_db):
        """No grant wins → no warm paths."""
        finder = PathFinder(populated_db)
        paths = finder.find_warm_paths("prof1")
        assert paths == []

    def test_warmth_score_ordering(self, db_with_grant_wins):
        finder = PathFinder(db_with_grant_wins)
        paths = finder.find_warm_paths("prof1")

        # Should be sorted by warmth descending
        for i in range(len(paths) - 1):
            assert paths[i].warmth_score >= paths[i + 1].warmth_score


# ---------------------------------------------------------------------------
# Tests: PostScreeningAnalyzer
# ---------------------------------------------------------------------------

class TestPostScreeningAnalyzer:
    def test_full_report(self, populated_db):
        analyzer = PostScreeningAnalyzer(populated_db)
        report = analyzer.analyze("prof1")

        assert isinstance(report, PostScreeningReport)
        assert report.profile_id == "prof1"
        assert report.total_unique_funders == 5
        assert report.total_funder_connections > 0
        assert len(report.funder_clusters) > 0
        assert report.network_readiness_score > 0.0
        assert report.people_in_graph > 0
        assert report.seeker_board_size == 1

    def test_funder_frequency(self, populated_db):
        analyzer = PostScreeningAnalyzer(populated_db)
        report = analyzer.analyze("prof1")

        assert len(report.top_funders) == 5
        for f in report.top_funders:
            assert f.opportunity_count >= 1

    def test_diagnostics_seeker_board_warning(self, populated_db):
        """With only 1 board member, should get a warning."""
        analyzer = PostScreeningAnalyzer(populated_db)
        report = analyzer.analyze("prof1")

        board_warnings = [
            d for d in report.diagnostics
            if d["category"] == "seeker_profile" and d["severity"] == "warning"
        ]
        assert len(board_warnings) >= 1

    def test_empty_graph_critical_diagnostic(self, db_path):
        """Empty graph should produce a critical diagnostic."""
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO profiles (id, name) VALUES ('empty', 'Empty Org')"
        )
        conn.execute(
            "INSERT INTO opportunities (id, profile_id, ein, organization_name) "
            "VALUES ('o1', 'empty', '11-1111111', 'Some Funder')"
        )
        conn.commit()
        conn.close()

        analyzer = PostScreeningAnalyzer(db_path)
        report = analyzer.analyze("empty")

        critical = [d for d in report.diagnostics if d["severity"] == "critical"]
        assert len(critical) >= 1
        assert report.network_readiness_score == 0.0

    def test_readiness_score_ranges(self, populated_db):
        analyzer = PostScreeningAnalyzer(populated_db)
        report = analyzer.analyze("prof1")

        assert 0.0 <= report.network_readiness_score <= 1.0


# ---------------------------------------------------------------------------
# Tests: Seeker-to-funder overlap still works
# ---------------------------------------------------------------------------

class TestSeekerFunderOverlap:
    def test_direct_overlap_detected(self, populated_db):
        """Alice is both seeker board member and at Alpha Foundation."""
        finder = PathFinder(populated_db)
        paths = finder.find_paths("prof1", "11-1111111")

        degree1 = [p for p in paths if p.degree == 1]
        assert len(degree1) >= 1
        assert degree1[0].strength == "strong"
