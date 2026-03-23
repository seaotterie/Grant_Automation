"""
Tests for NetworkBatchPreprocessor — the multi-stage pipeline that
bulk-populates the people database from free data sources.
"""

import sqlite3
import sys
import types
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.network.batch_preprocessor import NetworkBatchPreprocessor, StageResult


# ---------------------------------------------------------------------------
# Mock the ProPublica client module to avoid the cryptography import chain
# ---------------------------------------------------------------------------

_mock_propublica_module = types.ModuleType("src.clients.propublica_client")


class _MockProPublicaClient:
    """Lightweight mock that tests can reconfigure via monkeypatch."""
    async def get_organization_by_ein(self, ein):
        return {"filings_with_data": []}


_mock_propublica_module.ProPublicaClient = _MockProPublicaClient
sys.modules.setdefault("src.clients.propublica_client", _mock_propublica_module)

# Similarly mock xml_fetcher to avoid aiohttp/bs4 imports in unit tests
_mock_xml_module = types.ModuleType("src.utils.xml_fetcher")


class _MockXMLFetcher:
    async def fetch_xml_by_ein(self, ein):
        return None


_mock_xml_module.XMLFetcher = _MockXMLFetcher
sys.modules.setdefault("src.utils.xml_fetcher", _mock_xml_module)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_path(tmp_path):
    """Create a test database with the required tables and seed data."""
    path = str(tmp_path / "test_batch.db")
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE profiles (
            id TEXT PRIMARY KEY,
            name TEXT,
            ein TEXT,
            board_members TEXT
        );

        CREATE TABLE opportunities (
            id TEXT PRIMARY KEY,
            profile_id TEXT,
            ein TEXT,
            organization_name TEXT,
            current_stage TEXT DEFAULT 'prospects'
        );

        CREATE TABLE ein_intelligence (
            ein TEXT PRIMARY KEY,
            org_name TEXT,
            web_data TEXT,
            web_data_fetched_at TEXT,
            web_data_source TEXT,
            filing_history TEXT,
            filing_history_fetched_at TEXT,
            pdf_analyses TEXT,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE network_memberships (
            id TEXT PRIMARY KEY,
            person_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            org_ein TEXT,
            org_name TEXT NOT NULL,
            org_type TEXT NOT NULL,
            profile_id TEXT,
            source TEXT NOT NULL,
            title TEXT,
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(person_hash, org_ein)
        );

        -- Seed data: a profile with 3 funder opportunities
        INSERT INTO profiles (id, name, ein) VALUES ('p1', 'Test Nonprofit', '99-1234567');

        INSERT INTO opportunities (id, profile_id, ein, organization_name)
        VALUES
            ('opp1', 'p1', '13-1234567', 'Foundation Alpha'),
            ('opp2', 'p1', '26-7654321', 'Foundation Beta'),
            ('opp3', 'p1', '52-1111111', 'Foundation Gamma');

        -- Foundation Alpha already has filing history
        INSERT INTO ein_intelligence (ein, org_name, filing_history, updated_at)
        VALUES ('13-1234567', 'Foundation Alpha',
                '[{"tax_year": 2023, "pdf_url": "https://example.com/a.pdf"}]',
                '2024-01-01T00:00:00');

        -- Foundation Beta has nothing
        -- Foundation Gamma has nothing
    """)
    conn.close()
    return path


# ---------------------------------------------------------------------------
# Test: Coverage report (free, no external calls)
# ---------------------------------------------------------------------------

class TestCoverageReport:
    def test_coverage_report_returns_all_funders(self, db_path):
        preprocessor = NetworkBatchPreprocessor(db_path)
        report = preprocessor.get_coverage_report("p1")

        assert report["profile_id"] == "p1"
        assert len(report["funders"]) == 3

        eins = {f["ein"] for f in report["funders"]}
        assert eins == {"13-1234567", "26-7654321", "52-1111111"}

    def test_coverage_report_identifies_actions(self, db_path):
        preprocessor = NetworkBatchPreprocessor(db_path)
        report = preprocessor.get_coverage_report("p1")

        by_ein = {f["ein"]: f for f in report["funders"]}

        # Alpha has filing history → needs XML parse
        assert by_ein["13-1234567"]["has_filing_history"] is True
        assert by_ein["13-1234567"]["recommended_action"] == "run_xml_parse"

        # Beta has nothing → needs discovery
        assert by_ein["26-7654321"]["has_filing_history"] is False
        assert by_ein["26-7654321"]["recommended_action"] == "needs_discovery"

    def test_empty_profile_returns_empty(self, db_path):
        preprocessor = NetworkBatchPreprocessor(db_path)
        report = preprocessor.get_coverage_report("nonexistent")
        assert report["funders"] == []


# ---------------------------------------------------------------------------
# Test: Stage 1 — Filing discovery
# ---------------------------------------------------------------------------

class TestStageDiscoverFilings:
    @pytest.mark.asyncio
    async def test_skips_eins_with_existing_filings(self, db_path):
        preprocessor = NetworkBatchPreprocessor(db_path)
        funder_eins = [{"ein": "13-1234567", "org_name": "Foundation Alpha"}]

        result = await preprocessor._stage_discover_filings(funder_eins, concurrency=1)

        assert result.status == "skipped"
        assert result.items_skipped == 1

    @pytest.mark.asyncio
    async def test_discovers_missing_filings(self, db_path, monkeypatch):
        """Mock ProPublica to return filings for EINs missing them."""
        preprocessor = NetworkBatchPreprocessor(db_path)
        funder_eins = [
            {"ein": "26-7654321", "org_name": "Foundation Beta"},
        ]

        mock_client_instance = AsyncMock()
        mock_client_instance.get_organization_by_ein = AsyncMock(return_value={
            "filings_with_data": [
                {"tax_prd_yr": 2023, "pdf_url": "https://example.com/b.pdf", "updated": "2024-01-01"},
            ]
        })

        monkeypatch.setattr(
            _mock_propublica_module, "ProPublicaClient",
            lambda: mock_client_instance,
        )

        with patch("src.network.batch_preprocessor.asyncio.sleep", new_callable=AsyncMock):
            result = await preprocessor._stage_discover_filings(funder_eins, concurrency=1)

        assert result.status == "completed"
        assert result.items_added == 1
        assert result.cost_usd == 0.0


# ---------------------------------------------------------------------------
# Test: Stage 2 — XML officer extraction
# ---------------------------------------------------------------------------

class TestStageXmlOfficers:
    @pytest.mark.asyncio
    async def test_skips_eins_already_populated(self, db_path):
        """If an EIN already has people in network_memberships, skip it."""
        # Insert a membership for Alpha
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO network_memberships (id, person_hash, display_name, org_ein, org_name, org_type, source, created_at, updated_at) "
            "VALUES ('m1', 'hash1', 'John Doe', '13-1234567', 'Foundation Alpha', 'funder', 'xml', '2024-01-01', '2024-01-01')"
        )
        conn.commit()
        conn.close()

        preprocessor = NetworkBatchPreprocessor(db_path)
        funder_eins = [{"ein": "13-1234567", "org_name": "Foundation Alpha"}]

        result = await preprocessor._stage_xml_officer_extraction(funder_eins, concurrency=1)
        assert result.status == "skipped"

    @pytest.mark.asyncio
    async def test_extracts_officers_from_xml(self, db_path, monkeypatch):
        """Mock XML fetcher to return sample 990 XML."""
        sample_xml = b"""<?xml version="1.0"?>
        <Return xmlns="http://www.irs.gov/efile">
          <ReturnData>
            <IRS990>
              <Form990PartVIISectionAGrp>
                <PersonNm>Jane Smith</PersonNm>
                <TitleTxt>Board Chair</TitleTxt>
              </Form990PartVIISectionAGrp>
              <Form990PartVIISectionAGrp>
                <PersonNm>Bob Jones</PersonNm>
                <TitleTxt>Treasurer</TitleTxt>
              </Form990PartVIISectionAGrp>
            </IRS990>
          </ReturnData>
        </Return>"""

        preprocessor = NetworkBatchPreprocessor(db_path)
        funder_eins = [{"ein": "26-7654321", "org_name": "Foundation Beta"}]

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_xml_by_ein = AsyncMock(return_value=sample_xml)

        monkeypatch.setattr(
            _mock_xml_module, "XMLFetcher",
            lambda: mock_fetcher_instance,
        )

        with patch("src.network.batch_preprocessor.asyncio.sleep", new_callable=AsyncMock):
            result = await preprocessor._stage_xml_officer_extraction(funder_eins, concurrency=1)

        assert result.status == "completed"
        assert result.items_added >= 2  # Jane + Bob
        assert result.cost_usd == 0.0


# ---------------------------------------------------------------------------
# Test: Stage 3 — Ingest + ETL
# ---------------------------------------------------------------------------

class TestStageIngestEtl:
    def test_ingest_and_etl_runs(self, db_path):
        """Insert some memberships, then run stage 3 — should create people."""
        # Pre-populate memberships
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO network_memberships (id, person_hash, display_name, org_ein, org_name, org_type, source, title, created_at, updated_at) "
            "VALUES ('m1', 'aaa111', 'Alice Chen', '13-1234567', 'Foundation Alpha', 'funder', 'xml', 'CEO', '2024-01-01', '2024-01-01')"
        )
        conn.commit()
        conn.close()

        preprocessor = NetworkBatchPreprocessor(db_path)
        funder_eins = [{"ein": "13-1234567", "org_name": "Foundation Alpha"}]

        result = preprocessor._stage_ingest_and_etl("p1", funder_eins)

        assert result.status == "completed"
        assert result.cost_usd == 0.0

        # Verify people table was created and populated
        conn2 = sqlite3.connect(db_path)
        count = conn2.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        conn2.close()
        assert count >= 1


# ---------------------------------------------------------------------------
# Test: Stage 4 — Dedup + score
# ---------------------------------------------------------------------------

class TestStageDedupScore:
    def test_dedup_and_score_runs_without_error(self, db_path):
        """Even with no data, the stage should complete gracefully."""
        # Ensure tables exist
        from src.network.people_etl import PeopleETL
        etl = PeopleETL(db_path)
        etl.ensure_tables()

        preprocessor = NetworkBatchPreprocessor(db_path)
        result = preprocessor._stage_dedup_and_score("p1")

        assert result.status == "completed"
        assert result.cost_usd == 0.0


# ---------------------------------------------------------------------------
# Test: Full pipeline (mocked external calls)
# ---------------------------------------------------------------------------

class TestFullPipeline:
    @pytest.mark.asyncio
    async def test_pipeline_runs_all_free_stages(self, db_path, monkeypatch):
        """Pipeline should run stages 1-4 with no AI costs."""
        preprocessor = NetworkBatchPreprocessor(db_path)

        mock_client = AsyncMock()
        mock_client.get_organization_by_ein = AsyncMock(return_value={"filings_with_data": []})
        monkeypatch.setattr(_mock_propublica_module, "ProPublicaClient", lambda: mock_client)

        mock_fetcher = AsyncMock()
        mock_fetcher.fetch_xml_by_ein = AsyncMock(return_value=None)
        monkeypatch.setattr(_mock_xml_module, "XMLFetcher", lambda: mock_fetcher)

        with patch("src.network.batch_preprocessor.asyncio.sleep", new_callable=AsyncMock):
            result = await preprocessor.run_pipeline(
                profile_id="p1",
                max_eins=10,
                include_web_scraping=False,
            )

        assert result.profile_id == "p1"
        assert result.total_cost_usd == 0.0
        assert len(result.stages) == 4  # Stages 1-4 only
        assert all(s.cost_usd == 0.0 for s in result.stages)

    @pytest.mark.asyncio
    async def test_pipeline_skips_web_scraping_by_default(self, db_path, monkeypatch):
        """Web scraping stage should not run unless explicitly enabled."""
        preprocessor = NetworkBatchPreprocessor(db_path)

        mock_client = AsyncMock()
        mock_client.get_organization_by_ein = AsyncMock(return_value={"filings_with_data": []})
        monkeypatch.setattr(_mock_propublica_module, "ProPublicaClient", lambda: mock_client)

        mock_fetcher = AsyncMock()
        mock_fetcher.fetch_xml_by_ein = AsyncMock(return_value=None)
        monkeypatch.setattr(_mock_xml_module, "XMLFetcher", lambda: mock_fetcher)

        with patch("src.network.batch_preprocessor.asyncio.sleep", new_callable=AsyncMock):
            result = await preprocessor.run_pipeline(
                profile_id="p1",
                include_web_scraping=False,
            )

        stage_names = [s.stage for s in result.stages]
        assert "web_enrichment" not in stage_names
