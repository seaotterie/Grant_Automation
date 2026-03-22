"""
Tests for ConnectionStrengthScorer -- multi-factor connection scoring,
board-connection rebuilding, and person influence computation.

Uses temporary SQLite files via pytest's tmp_path fixture. No external
services required.
"""

import sqlite3
from datetime import datetime, timezone

import pytest

from src.network.connection_strength import ConnectionStrengthScorer


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

_SCHEMA = """
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

CREATE TABLE IF NOT EXISTS board_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    org1_ein TEXT NOT NULL,
    org1_name TEXT NOT NULL,
    org2_ein TEXT NOT NULL,
    org2_name TEXT NOT NULL,
    connection_strength REAL DEFAULT 1.0,
    shared_positions INTEGER DEFAULT 1,
    connection_type TEXT DEFAULT 'board',
    betweenness_score REAL,
    closeness_score REAL,
    influence_score REAL,
    connection_start_date DATE,
    connection_end_date DATE,
    is_current_connection BOOLEAN DEFAULT TRUE,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    algorithm_version TEXT DEFAULT '2.0.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(person_id, org1_ein, org2_ein),
    CHECK(org1_ein < org2_ein)
);

CREATE TABLE IF NOT EXISTS person_influence_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    person_name TEXT NOT NULL,
    total_board_positions INTEGER,
    total_organizations INTEGER,
    executive_positions INTEGER,
    board_chair_positions INTEGER,
    network_reach INTEGER,
    bridge_connections INTEGER,
    cluster_spanning INTEGER,
    position_influence_score REAL,
    network_influence_score REAL,
    total_influence_score REAL,
    influence_rank INTEGER,
    sector_diversity INTEGER,
    geographic_reach INTEGER,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    algorithm_version TEXT DEFAULT '2.0.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(person_id)
);
"""


def _make_db(tmp_path, name="conn_test.db"):
    db_path = str(tmp_path / name)
    conn = sqlite3.connect(db_path)
    conn.executescript(_SCHEMA)
    conn.commit()
    conn.close()
    return db_path


def _insert_person(conn, original_name, name_hash):
    now = datetime.now(timezone.utc).isoformat()
    first = original_name.split()[0].lower() if " " in original_name else original_name.lower()
    last = original_name.split()[-1].lower() if " " in original_name else None
    cursor = conn.execute(
        "INSERT INTO people (normalized_name, original_name, name_hash, "
        "first_name, last_name, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (original_name.lower(), original_name, name_hash, first, last, now, now),
    )
    return cursor.lastrowid


def _insert_role(conn, person_id, *, ein="11-1111111", org_name="Org A",
                 title="Board Member", position_type="board", is_current=True,
                 start_date=None, end_date=None, data_source="990_filing",
                 position_category=None):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO organization_roles "
        "(person_id, organization_ein, organization_name, title, position_type, "
        "position_category, is_current, start_date, end_date, data_source, "
        "created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (person_id, ein, org_name, title, position_type, position_category,
         is_current, start_date, end_date, data_source, now, now),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_path(tmp_path):
    return _make_db(tmp_path)


@pytest.fixture()
def scorer(db_path):
    return ConnectionStrengthScorer(db_path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestScoreCurrentConcurrent:
    def test_both_current_at_two_orgs_high_score(self, db_path, scorer):
        """A person with current roles at two orgs should produce a high
        connection score between those orgs."""
        conn = sqlite3.connect(db_path)
        pa = _insert_person(conn, "Alice Jones", "h1")
        # Person serves at two different orgs currently
        _insert_role(conn, pa, ein="11-0000001", org_name="Org Alpha",
                     title="Chair", position_type="board", is_current=True)
        _insert_role(conn, pa, ein="22-0000002", org_name="Org Beta",
                     title="Director", position_type="board", is_current=True,
                     data_source="web_data")
        conn.commit()
        conn.close()

        result = scorer.score_connection(pa, "11-0000001", "22-0000002")
        assert result["total_score"] > 0
        assert result["is_current"] is True
        assert result["factors"]["concurrent_service"] == 1.0
        assert result["factors"]["recency"] == 1.0

    def test_missing_role_returns_zero(self, db_path, scorer):
        """If a person has no role at one of the orgs, score should be 0."""
        conn = sqlite3.connect(db_path)
        pa = _insert_person(conn, "Alice Jones", "h1")
        _insert_role(conn, pa, ein="11-0000001", org_name="Org Alpha",
                     title="Chair", position_type="board")
        conn.commit()
        conn.close()

        result = scorer.score_connection(pa, "11-0000001", "99-9999999")
        assert result["total_score"] == 0.0
        assert result["is_current"] is False


class TestScoreExpiredConnection:
    def test_expired_roles_lower_score(self, db_path, scorer):
        """Roles that both ended years ago should produce a lower score than
        current concurrent roles."""
        conn = sqlite3.connect(db_path)
        pa = _insert_person(conn, "Alice Jones", "h1")
        _insert_role(conn, pa, ein="11-0000001", org_name="Old Org A",
                     title="Chair", position_type="board",
                     is_current=False, end_date="2018-12-31")
        _insert_role(conn, pa, ein="22-0000002", org_name="Old Org B",
                     title="Treasurer", position_type="board",
                     is_current=False, end_date="2018-12-31",
                     data_source="web_data")
        conn.commit()
        conn.close()

        result_expired = scorer.score_connection(pa, "11-0000001", "22-0000002")

        # Create a current pair for comparison
        db_path2 = _make_db(scorer.db_path.replace("conn_test", "").rsplit("/", 1)[0] + "/../tmp2",
                            name="conn_current.db") if False else None
        # Use a simpler approach: build in same DB with different person+orgs
        conn2 = sqlite3.connect(db_path)
        pb = _insert_person(conn2, "Bob Current", "h2")
        _insert_role(conn2, pb, ein="33-0000003", org_name="Current Org A",
                     title="Chair", position_type="board", is_current=True)
        _insert_role(conn2, pb, ein="44-0000004", org_name="Current Org B",
                     title="Treasurer", position_type="board", is_current=True,
                     data_source="web_data")
        conn2.commit()
        conn2.close()

        result_current = scorer.score_connection(pb, "33-0000003", "44-0000004")

        assert result_expired["total_score"] < result_current["total_score"]
        assert result_expired["factors"]["concurrent_service"] < result_current["factors"]["concurrent_service"]


class TestRoleProximityScoring:
    def test_executive_pair_scores_higher_than_board_staff(self, db_path, scorer):
        """Executive roles at both orgs should yield a higher role_proximity
        factor than board at one + staff at the other."""
        conn = sqlite3.connect(db_path)
        # Person A: executive at both orgs
        p1 = _insert_person(conn, "Exec Alice", "e1")
        _insert_role(conn, p1, ein="11-0000001", org_name="Corp A",
                     title="CEO", position_type="executive", is_current=True)
        _insert_role(conn, p1, ein="22-0000002", org_name="Corp B",
                     title="CFO", position_type="executive", is_current=True,
                     data_source="web_data")

        # Person B: board at one, staff at the other
        p2 = _insert_person(conn, "Mixed Bob", "m1")
        _insert_role(conn, p2, ein="33-0000003", org_name="NonProfit A",
                     title="Chair", position_type="board", is_current=True)
        _insert_role(conn, p2, ein="44-0000004", org_name="NonProfit B",
                     title="Coordinator", position_type="staff", is_current=True,
                     data_source="web_data")
        conn.commit()
        conn.close()

        exec_result = scorer.score_connection(p1, "11-0000001", "22-0000002")
        mixed_result = scorer.score_connection(p2, "33-0000003", "44-0000004")

        assert exec_result["factors"]["role_proximity"] > mixed_result["factors"]["role_proximity"]
        assert exec_result["total_score"] > mixed_result["total_score"]

    def test_factor_role_proximity_values(self):
        """Verify known role proximity return values directly."""
        assert ConnectionStrengthScorer._factor_role_proximity("executive", "executive") == 1.0
        assert ConnectionStrengthScorer._factor_role_proximity("board", "board") == 0.8
        assert ConnectionStrengthScorer._factor_role_proximity("executive", "board") == 0.6
        assert ConnectionStrengthScorer._factor_role_proximity("advisory", "board") == 0.4
        assert ConnectionStrengthScorer._factor_role_proximity("board", "staff") == 0.3


class TestRebuildBoardConnections:
    def test_rebuild_creates_connections_for_multi_org_person(self, db_path, scorer):
        """A person at 2+ orgs should generate a board_connections row."""
        conn = sqlite3.connect(db_path)
        pa = _insert_person(conn, "Alice Bridge", "br1")
        _insert_role(conn, pa, ein="11-0000001", org_name="Org Alpha",
                     title="Chair", position_type="board", is_current=True)
        _insert_role(conn, pa, ein="22-0000002", org_name="Org Beta",
                     title="Director", position_type="board", is_current=True,
                     data_source="web_data")
        conn.commit()
        conn.close()

        result = scorer.rebuild_board_connections()
        assert result["connections_created"] >= 1
        assert result["total_connections"] >= 1

        # Verify the board_connections table has rows
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM board_connections").fetchall()
        assert len(rows) >= 1
        # Verify EIN ordering constraint
        for row in rows:
            assert row["org1_ein"] < row["org2_ein"]
        conn.close()

    def test_rebuild_single_org_person_no_connections(self, db_path, scorer):
        """A person at only one org should not generate connections."""
        conn = sqlite3.connect(db_path)
        pa = _insert_person(conn, "Solo Steve", "s1")
        _insert_role(conn, pa, ein="11-0000001", org_name="Only Org",
                     title="Member", position_type="board")
        conn.commit()
        conn.close()

        result = scorer.rebuild_board_connections()
        assert result["connections_created"] == 0
        assert result["total_connections"] == 0


class TestComputePersonInfluence:
    def test_person_with_many_roles_higher_influence(self, db_path, scorer):
        """A person with executive and chair roles at multiple orgs should have
        higher influence than a person with a single staff role."""
        conn = sqlite3.connect(db_path)
        p_many = _insert_person(conn, "Well Connected Alice", "wc1")
        _insert_role(conn, p_many, ein="11-0000001", org_name="Org A",
                     title="CEO", position_type="executive", is_current=True)
        _insert_role(conn, p_many, ein="22-0000002", org_name="Org B",
                     title="Chair", position_type="board",
                     position_category="chair", data_source="web_data",
                     is_current=True)
        _insert_role(conn, p_many, ein="33-0000003", org_name="Org C",
                     title="Advisor", position_type="advisory",
                     data_source="pdf_analysis", is_current=True)

        p_few = _insert_person(conn, "Quiet Bob", "qb1")
        _insert_role(conn, p_few, ein="44-0000004", org_name="Org D",
                     title="Staff Member", position_type="staff", is_current=True)
        conn.commit()
        conn.close()

        inf_many = scorer.compute_person_influence(p_many)
        inf_few = scorer.compute_person_influence(p_few)

        assert inf_many["total_influence_score"] > inf_few["total_influence_score"]
        assert inf_many["total_organizations"] == 3
        assert inf_many["executive_positions"] == 1
        assert inf_many["board_chair_positions"] == 1

        assert inf_few["total_organizations"] == 1
        assert inf_few["executive_positions"] == 0

    def test_no_roles_returns_zero_influence(self, db_path, scorer):
        """A person with no roles should have zero influence scores."""
        conn = sqlite3.connect(db_path)
        pid = _insert_person(conn, "Nobody Special", "n1")
        conn.commit()
        conn.close()

        result = scorer.compute_person_influence(pid)
        assert result["total_influence_score"] == 0.0
        assert result["total_organizations"] == 0
        assert result["executive_positions"] == 0

    def test_influence_persisted_to_db(self, db_path, scorer):
        """compute_person_influence should write results to person_influence_metrics."""
        conn = sqlite3.connect(db_path)
        pid = _insert_person(conn, "Persisted Pat", "pp1")
        _insert_role(conn, pid, ein="11-0000001", org_name="Org A",
                     title="President", position_type="executive", is_current=True)
        conn.commit()
        conn.close()

        scorer.compute_person_influence(pid)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM person_influence_metrics WHERE person_id = ?", (pid,)
        ).fetchone()
        conn.close()

        assert row is not None
        assert row["person_id"] == pid
        assert row["executive_positions"] == 1


class TestGetStrongestConnections:
    def test_ordering_by_strength(self, db_path, scorer):
        """Connections returned by get_strongest_connections should be ordered
        by descending strength."""
        conn = sqlite3.connect(db_path)
        # Create people who bridge orgs
        pa = _insert_person(conn, "Alice Bridge", "a1")
        pb = _insert_person(conn, "Bob Bridge", "b1")

        # Alice bridges Org-A <-> Org-B (executive at both = strong)
        _insert_role(conn, pa, ein="11-0000001", org_name="Org A",
                     title="CEO", position_type="executive", is_current=True)
        _insert_role(conn, pa, ein="22-0000002", org_name="Org B",
                     title="CFO", position_type="executive", is_current=True,
                     data_source="web_data")

        # Bob bridges Org-A <-> Org-C (staff at Org-C = weaker)
        _insert_role(conn, pb, ein="11-0000001", org_name="Org A",
                     title="Director", position_type="board", is_current=True)
        _insert_role(conn, pb, ein="33-0000003", org_name="Org C",
                     title="Assistant", position_type="staff", is_current=True,
                     data_source="web_data")
        conn.commit()
        conn.close()

        # Rebuild so board_connections table is populated
        scorer.rebuild_board_connections()

        connections = scorer.get_strongest_connections("11-0000001", limit=10)
        assert len(connections) >= 2

        # Verify descending order
        for i in range(len(connections) - 1):
            assert connections[i]["strength"] >= connections[i + 1]["strength"]

        # The executive-executive connection (Org B) should rank above
        # the board-staff connection (Org C)
        org_eins = [c["connected_org_ein"] for c in connections]
        assert org_eins.index("22-0000002") < org_eins.index("33-0000003")

    def test_limit_respected(self, db_path, scorer):
        """get_strongest_connections should respect the limit parameter."""
        conn = sqlite3.connect(db_path)
        pa = _insert_person(conn, "Hub Person", "hub1")
        for i in range(5):
            ein_val = f"{10+i:02d}-0000001"
            _insert_role(conn, pa, ein=ein_val, org_name=f"Org {i}",
                         title="Member", position_type="board", is_current=True,
                         data_source=f"src{i}")
        conn.commit()
        conn.close()

        scorer.rebuild_board_connections()
        # Ask for only 2 -- the person bridges 5 orgs -> C(5,2)=10 pairs
        connections = scorer.get_strongest_connections("10-0000001", limit=2)
        assert len(connections) <= 2
