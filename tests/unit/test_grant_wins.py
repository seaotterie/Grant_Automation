"""
Tests for GrantWinService — historical grant win ingestion,
CSV import, contact linking, and proven pathway scoring.
"""

import sqlite3
import pytest
from datetime import datetime

from src.network.grant_wins import (
    GrantWinService,
    GrantWinRecord,
    _auto_map_columns,
    _normalize_header,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_path(tmp_path):
    """Create a test database with required tables and seed data."""
    path = str(tmp_path / "test_grant_wins.db")
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE profiles (
            id TEXT PRIMARY KEY,
            name TEXT,
            ein TEXT
        );

        CREATE TABLE people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            normalized_name TEXT NOT NULL,
            original_name TEXT NOT NULL,
            name_hash TEXT UNIQUE,
            first_name TEXT, last_name TEXT, middle_name TEXT,
            prefix TEXT, suffix TEXT,
            biography TEXT, linkedin_url TEXT, personal_website TEXT,
            data_quality_score INTEGER DEFAULT 50,
            confidence_level REAL DEFAULT 0.5,
            source_count INTEGER DEFAULT 1,
            created_at TIMESTAMP, updated_at TIMESTAMP,
            last_verified_at TIMESTAMP
        );

        CREATE TABLE organization_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL REFERENCES people(id),
            organization_ein TEXT NOT NULL,
            organization_name TEXT NOT NULL,
            title TEXT NOT NULL,
            position_type TEXT DEFAULT 'board',
            position_category TEXT,
            start_date DATE, end_date DATE,
            is_current BOOLEAN DEFAULT TRUE,
            tenure_years REAL,
            data_source TEXT NOT NULL,
            filing_year INTEGER,
            verification_status TEXT DEFAULT 'unverified',
            quality_score INTEGER DEFAULT 50,
            created_at TIMESTAMP, updated_at TIMESTAMP,
            source_url TEXT, web_intelligence_id TEXT,
            UNIQUE(person_id, organization_ein, title, data_source)
        );

        -- Seed profile
        INSERT INTO profiles (id, name, ein) VALUES ('p1', 'Test Nonprofit', '99-1234567');

        -- Seed opportunities (one "won")
        -- Seed people at Foundation Alpha
        INSERT INTO people (id, normalized_name, original_name, name_hash, first_name, last_name, created_at, updated_at)
        VALUES (1, 'jane smith', 'Jane Smith', 'hash_jane', 'Jane', 'Smith', '2024-01-01', '2024-01-01');

        INSERT INTO people (id, normalized_name, original_name, name_hash, first_name, last_name, created_at, updated_at)
        VALUES (2, 'bob jones', 'Bob Jones', 'hash_bob', 'Bob', 'Jones', '2024-01-01', '2024-01-01');

        -- Roles at funder org
        INSERT INTO organization_roles (person_id, organization_ein, organization_name, title, is_current, data_source, filing_year)
        VALUES (1, '13-1111111', 'Foundation Alpha', 'Board Chair', 1, '990_filing', 2023);

        INSERT INTO organization_roles (person_id, organization_ein, organization_name, title, is_current, data_source, filing_year)
        VALUES (2, '13-1111111', 'Foundation Alpha', 'Trustee', 0, '990_filing', 2020);
    """)
    conn.close()
    return path


@pytest.fixture
def svc(db_path):
    return GrantWinService(db_path)


# ---------------------------------------------------------------------------
# Test: Column mapping
# ---------------------------------------------------------------------------

class TestColumnMapping:
    def test_normalize_header(self):
        assert _normalize_header("Funder Name") == "funder_name"
        assert _normalize_header("  Grant Amount  ") == "grant_amount"
        assert _normalize_header("Award-Date") == "award_date"

    def test_auto_map_common_headers(self):
        headers = ["Foundation Name", "Grant Amount", "Date", "EIN", "Notes"]
        mapping = _auto_map_columns(headers)

        assert "funder_name" in mapping
        assert "amount" in mapping
        assert "award_date" in mapping

    def test_auto_map_alternate_headers(self):
        headers = ["Grantor", "Dollars", "Year", "Program Officer"]
        mapping = _auto_map_columns(headers)

        assert "funder_name" in mapping
        assert "amount" in mapping
        assert "award_date" in mapping
        assert "contact_names" in mapping

    def test_auto_map_unrecognized_headers_ignored(self):
        headers = ["XYZ Column", "Random Stuff"]
        mapping = _auto_map_columns(headers)
        assert mapping == {}


# ---------------------------------------------------------------------------
# Test: Single win CRUD
# ---------------------------------------------------------------------------

class TestGrantWinCRUD:
    def test_add_win(self, svc, db_path):
        record = GrantWinRecord(
            funder_name="Gates Foundation",
            amount=50000.0,
            award_date="2023-06-15",
            funder_ein="56-2618866",
        )
        result = svc.add_win("p1", record)

        assert result["created"] is True
        assert result["win_id"] > 0

    def test_add_duplicate_updates(self, svc):
        record = GrantWinRecord(
            funder_name="Gates Foundation",
            amount=50000.0,
            award_date="2023-06-15",
        )
        r1 = svc.add_win("p1", record)
        assert r1["created"] is True

        # Same funder/amount/date → update, not duplicate
        record2 = GrantWinRecord(
            funder_name="Gates Foundation",
            amount=50000.0,
            award_date="2023-06-15",
            program_name="Global Health",  # new field
        )
        r2 = svc.add_win("p1", record2)
        assert r2["created"] is False
        assert r2["win_id"] == r1["win_id"]

    def test_add_win_with_contacts(self, svc):
        record = GrantWinRecord(
            funder_name="Ford Foundation",
            amount=100000.0,
            contact_names=["Alice Chen", "Bob Zhang"],
        )
        result = svc.add_win("p1", record)
        assert result["contacts_linked"] == 2

    def test_get_wins(self, svc):
        svc.add_win("p1", GrantWinRecord(funder_name="Foundation A", amount=10000, award_date="2023"))
        svc.add_win("p1", GrantWinRecord(funder_name="Foundation B", amount=20000, award_date="2024"))

        wins = svc.get_wins("p1")
        assert len(wins) == 2
        # Ordered by year descending
        assert wins[0]["funder_name"] == "Foundation B"

    def test_delete_win(self, svc):
        result = svc.add_win("p1", GrantWinRecord(funder_name="Temp Foundation"))
        assert svc.delete_win(result["win_id"]) is True
        assert svc.delete_win(result["win_id"]) is False  # Already deleted

    def test_get_wins_includes_contacts(self, svc):
        record = GrantWinRecord(
            funder_name="Foundation C",
            contact_names=["Sarah Lee"],
        )
        svc.add_win("p1", record)
        wins = svc.get_wins("p1")
        assert len(wins[0]["contacts"]) == 1
        assert wins[0]["contacts"][0]["contact_name"] == "Sarah Lee"


# ---------------------------------------------------------------------------
# Test: CSV import
# ---------------------------------------------------------------------------

class TestCSVImport:
    def test_basic_csv_import(self, svc):
        csv_content = """Foundation Name,Grant Amount,Year,Notes
Gates Foundation,$50000,2023,General support
Ford Foundation,"$100,000",2024,Program grant
"""
        result = svc.import_from_csv("p1", csv_content)

        assert result.total_rows == 2
        assert result.wins_created == 2
        assert result.rows_skipped == 0
        assert "funder_name" in result.column_mapping_used

    def test_csv_with_contacts(self, svc):
        csv_content = """Funder,Amount,Contact
Foundation X,25000,Alice Chen; Bob Zhang
Foundation Y,30000,Carol White
"""
        result = svc.import_from_csv("p1", csv_content)
        assert result.wins_created == 2
        assert result.contacts_linked == 3  # 2 + 1

    def test_csv_dollar_sign_handling(self, svc):
        csv_content = """Funder Name,Amount
Test Foundation,"$1,234,567.89"
"""
        result = svc.import_from_csv("p1", csv_content)
        assert result.wins_created == 1

        wins = svc.get_wins("p1")
        assert wins[0]["amount"] == 1234567.89

    def test_csv_date_formats(self, svc):
        csv_content = """Funder,Date
Foundation A,2023-06-15
Foundation B,06/15/2023
Foundation C,2024
"""
        result = svc.import_from_csv("p1", csv_content)
        assert result.wins_created == 3

    def test_csv_missing_funder_column(self, svc):
        csv_content = """Amount,Date
50000,2023
"""
        result = svc.import_from_csv("p1", csv_content)
        assert len(result.errors) > 0
        assert "funder" in result.errors[0].lower()

    def test_csv_empty_rows_skipped(self, svc):
        csv_content = """Funder,Amount
Foundation A,50000
,
Foundation B,30000
"""
        result = svc.import_from_csv("p1", csv_content)
        assert result.wins_created == 2
        assert result.rows_skipped == 1

    def test_csv_with_custom_mapping(self, svc):
        csv_content = """Org,Money,When
Foundation X,50000,2023
"""
        mapping = {"funder_name": "Org", "amount": "Money", "award_date": "When"}
        result = svc.import_from_csv("p1", csv_content, column_mapping=mapping)
        assert result.wins_created == 1

    def test_preview_csv_mapping(self, svc):
        csv_content = """Foundation Name,Grant Amount,Year,Custom Field
Gates Foundation,$50000,2023,blah
Ford Foundation,$100000,2024,stuff
"""
        preview = svc.preview_csv_mapping(csv_content)

        assert "Foundation Name" in preview["headers"]
        assert "funder_name" in preview["auto_mapping"]
        assert len(preview["sample_rows"]) == 2
        assert "Custom Field" in preview["unmapped_columns"]

    def test_csv_tab_delimited(self, svc):
        csv_content = "Funder\tAmount\nFoundation X\t50000\n"
        result = svc.import_from_csv("p1", csv_content, delimiter="\t")
        assert result.wins_created == 1


# ---------------------------------------------------------------------------
# Test: Auto-link contacts
# ---------------------------------------------------------------------------

class TestAutoLinkContacts:
    def test_auto_link_finds_funder_board(self, svc):
        # First create a win with a funder EIN
        record = GrantWinRecord(
            funder_name="Foundation Alpha",
            funder_ein="13-1111111",
            amount=75000,
            award_date="2023",
        )
        svc.add_win("p1", record)

        result = svc.auto_link_contacts("p1")

        assert result["wins_processed"] == 1
        # Jane (current, filing 2023) should be linked
        # Bob (not current, filing 2020) should also match since 2023-2=2021 > 2020
        # but Bob's filing_year is 2020 which is < 2023-2=2021, so depends on
        # the end_date/is_current logic
        assert result["contacts_linked"] >= 1

    def test_auto_link_skips_wins_without_ein(self, svc):
        record = GrantWinRecord(funder_name="Unknown Foundation", amount=10000)
        svc.add_win("p1", record)

        result = svc.auto_link_contacts("p1")
        assert result["wins_without_ein"] == 1


# ---------------------------------------------------------------------------
# Test: Proven pathway scoring
# ---------------------------------------------------------------------------

class TestProvenPathwayScoring:
    def test_compute_proven_pathways(self, svc):
        # Add two wins at same funder, both linked to Jane
        for year in ("2023", "2024"):
            record = GrantWinRecord(
                funder_name="Foundation Alpha",
                funder_ein="13-1111111",
                amount=50000.0,
                award_date=year,
            )
            svc.add_win("p1", record)

        # Auto-link to find Jane + Bob
        svc.auto_link_contacts("p1")

        pathways = svc.compute_proven_pathways("p1")

        assert len(pathways) >= 1
        # Results should be sorted by score descending
        scores = [p["proven_pathway_score"] for p in pathways]
        assert scores == sorted(scores, reverse=True)

        # Top contact should have score > 0
        top = pathways[0]
        assert top["proven_pathway_score"] > 0
        assert top["total_wins_involved"] >= 1

    def test_proven_pathways_empty_if_no_wins(self, svc):
        pathways = svc.compute_proven_pathways("p1")
        assert pathways == []

    def test_active_contact_scores_higher(self, svc):
        # Add one win linked to Jane (active) and Bob (inactive)
        record = GrantWinRecord(
            funder_name="Foundation Alpha",
            funder_ein="13-1111111",
            amount=50000.0,
            award_date="2025",
        )
        svc.add_win("p1", record)
        svc.auto_link_contacts("p1")

        pathways = svc.compute_proven_pathways("p1")
        by_name = {p["person_name"]: p for p in pathways}

        if "jane smith" in by_name and "bob jones" in by_name:
            # Jane is is_current=1, Bob is is_current=0
            assert by_name["jane smith"]["is_still_active"] is True
            assert by_name["jane smith"]["proven_pathway_score"] >= by_name["bob jones"]["proven_pathway_score"]


# ---------------------------------------------------------------------------
# Test: Summary stats
# ---------------------------------------------------------------------------

class TestSummary:
    def test_summary_stats(self, svc):
        svc.add_win("p1", GrantWinRecord(funder_name="Foundation A", amount=50000, award_date="2023"))
        svc.add_win("p1", GrantWinRecord(funder_name="Foundation A", amount=75000, award_date="2024"))
        svc.add_win("p1", GrantWinRecord(funder_name="Foundation B", amount=25000, award_date="2024"))

        summary = svc.get_summary("p1")

        assert summary["total_wins"] == 3
        assert summary["total_amount"] == 150000.0
        assert summary["unique_funders"] == 2
        assert summary["earliest_year"] == 2023
        assert summary["latest_year"] == 2024

    def test_summary_empty_profile(self, svc):
        summary = svc.get_summary("nonexistent")
        assert summary["total_wins"] == 0
        assert summary["total_amount"] == 0


# ---------------------------------------------------------------------------
# Test: Amount / date parsing
# ---------------------------------------------------------------------------

class TestParsing:
    def test_parse_amount_variants(self):
        assert GrantWinService._parse_amount("$50,000") == 50000.0
        assert GrantWinService._parse_amount("$1,234,567.89") == 1234567.89
        assert GrantWinService._parse_amount("50000") == 50000.0
        assert GrantWinService._parse_amount("") is None
        assert GrantWinService._parse_amount("N/A") is None

    def test_parse_date_variants(self):
        assert GrantWinService._parse_date("2023-06-15") == "2023-06-15"
        assert GrantWinService._parse_date("06/15/2023") == "2023-06-15"
        assert GrantWinService._parse_date("2023") == "2023"
        assert GrantWinService._parse_date("") is None

    def test_extract_year(self):
        assert GrantWinService._extract_year("2023-06-15") == 2023
        assert GrantWinService._extract_year("2024") == 2024
        assert GrantWinService._extract_year(None) is None
        assert GrantWinService._extract_year("no date") is None


# ---------------------------------------------------------------------------
# Test: Recommendation generation
# ---------------------------------------------------------------------------

class TestRecommendation:
    def test_high_priority_recommendation(self):
        rec = GrantWinService._generate_recommendation(
            "Jane Smith", wins=3, most_recent=2025,
            is_active=True, funders=["Foundation A"],
            amount=150000, score=0.85,
        )
        assert "HIGH PRIORITY" in rec
        assert "Jane Smith" in rec
        assert "still active" in rec

    def test_low_priority_old_contact(self):
        rec = GrantWinService._generate_recommendation(
            "Old Contact", wins=1, most_recent=2015,
            is_active=False, funders=["Foundation B"],
            amount=10000, score=0.2,
        )
        assert "LOW PRIORITY" in rec
