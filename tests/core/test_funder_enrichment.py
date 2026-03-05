"""
Tests for funder enrichment module — database lookups for screening context.

Tests cover:
- FunderIntelligence dataclass and prompt formatting
- Database lookups (foundation index, BMF, form 990)
- Batch enrichment
- Graceful degradation when database is missing
- Integration with thorough screening prompt
"""

import json
import os
import sqlite3
import tempfile
import pytest
from unittest.mock import patch

from tools.opportunity_screening_tool.app.funder_enrichment import (
    FunderIntelligence,
    lookup_funder,
    enrich_opportunities_batch,
)
from tools.opportunity_screening_tool.app.screening_models import Opportunity
from tools.opportunity_screening_tool.app.screening_tool import (
    _build_thorough_screening_prompt,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_db():
    """Create a temporary intelligence database with test data."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # Create foundation_intelligence_index
    cursor.execute("""
        CREATE TABLE foundation_intelligence_index (
            ein TEXT PRIMARY KEY,
            capacity_tier TEXT,
            grants_paid_latest INTEGER DEFAULT 0,
            assets_fmv_latest INTEGER DEFAULT 0,
            avg_grant_size INTEGER DEFAULT 0,
            annual_grant_budget_estimate INTEGER DEFAULT 0,
            giving_trend TEXT DEFAULT 'unknown',
            giving_trend_pct REAL,
            years_of_data INTEGER DEFAULT 0,
            is_eligible_grantmaker INTEGER DEFAULT 1,
            accepts_applications TEXT DEFAULT 'unknown',
            is_operating_foundation INTEGER DEFAULT 0,
            health_status TEXT DEFAULT 'unknown',
            payout_compliance TEXT DEFAULT 'unknown',
            primary_states TEXT,
            geographic_concentration REAL,
            primary_archetype TEXT,
            secondary_archetypes TEXT,
            ntee_code TEXT,
            data_quality_score REAL DEFAULT 0.0,
            source_tax_year INTEGER
        )
    """)

    # Create bmf_organizations
    cursor.execute("""
        CREATE TABLE bmf_organizations (
            ein TEXT PRIMARY KEY,
            name TEXT,
            ntee_code TEXT,
            state TEXT,
            city TEXT,
            foundation_code TEXT
        )
    """)

    # Create form_990
    cursor.execute("""
        CREATE TABLE form_990 (
            ein TEXT,
            tax_year INTEGER,
            totrevenue INTEGER,
            totfuncexpns INTEGER,
            totassetsend INTEGER,
            totliabend INTEGER
        )
    """)

    # Insert test data
    cursor.execute("""
        INSERT INTO foundation_intelligence_index VALUES (
            '123456789', 'major', 5000000, 100000000, 50000, 6000000,
            'growing', 12.5, 3, 1, 'yes', 0, 'strong', 'compliant',
            '["VA", "MD", "DC"]', 0.65,
            'education_k12', '["youth_development"]',
            'B25', 0.85, 2024
        )
    """)

    cursor.execute("""
        INSERT INTO bmf_organizations VALUES (
            '123456789', 'SMITH FAMILY FOUNDATION', 'B25', 'VA', 'ARLINGTON', '04'
        )
    """)

    cursor.execute("""
        INSERT INTO bmf_organizations VALUES (
            '987654321', 'ACME NONPROFIT ORG', 'P20', 'MD', 'BALTIMORE', '00'
        )
    """)

    cursor.execute("""
        INSERT INTO form_990 VALUES (
            '987654321', 2024, 5000000, 4500000, 2000000, 500000
        )
    """)

    conn.commit()
    conn.close()

    yield path

    os.unlink(path)


@pytest.fixture
def sample_org():
    from tools.opportunity_screening_tool.app.screening_models import OrganizationProfile
    return OrganizationProfile(
        ein="541234567",
        name="Youth Education Alliance",
        mission="Quality education for underserved youth",
        ntee_codes=["B25"],
        geographic_focus=["Virginia"],
        program_areas=["education"],
    )


# ---------------------------------------------------------------------------
# FunderIntelligence Tests
# ---------------------------------------------------------------------------

class TestFunderIntelligence:

    def test_prompt_context_with_full_data(self):
        intel = FunderIntelligence(
            funder_name="Smith Family Foundation",
            ein="123456789",
            capacity_tier="major",
            grants_paid=5_000_000,
            total_assets=100_000_000,
            avg_grant_size=50_000,
            annual_grant_budget=6_000_000,
            giving_trend="growing",
            giving_trend_pct=12.5,
            health_status="strong",
            payout_compliance="compliant",
            accepts_applications="yes",
            primary_grant_states=["VA", "MD", "DC"],
            geographic_concentration=0.65,
            primary_archetype="education_k12",
            ntee_code="B25",
        )
        context = intel.to_prompt_context()

        assert "Smith Family Foundation" in context
        assert "major" in context
        assert "$5,000,000" in context
        assert "growing" in context
        assert "+12.5%" in context
        assert "VA" in context
        assert "education_k12" in context

    def test_prompt_context_with_no_data(self):
        intel = FunderIntelligence(funder_name="Unknown Foundation")
        context = intel.to_prompt_context()
        assert "No intelligence data available" in context

    def test_operating_foundation_warning(self):
        intel = FunderIntelligence(
            funder_name="Operating Foundation",
            is_operating_foundation=True,
            capacity_tier="major",
        )
        context = intel.to_prompt_context()
        assert "Operating foundation" in context

    def test_geographic_concentration_warning(self):
        intel = FunderIntelligence(
            funder_name="Local Foundation",
            primary_grant_states=["VA"],
            geographic_concentration=0.95,
            capacity_tier="modest",
        )
        context = intel.to_prompt_context()
        assert "geographically concentrated" in context


# ---------------------------------------------------------------------------
# Database Lookup Tests
# ---------------------------------------------------------------------------

class TestDatabaseLookup:

    def test_lookup_foundation_by_ein(self, temp_db):
        result = lookup_funder(
            funder_name="Smith Family Foundation",
            funder_ein="123456789",
            db_path=temp_db,
        )
        assert result.capacity_tier == "major"
        assert result.grants_paid == 5_000_000
        assert result.giving_trend == "growing"
        assert result.health_status == "strong"
        assert "VA" in result.primary_grant_states

    def test_lookup_nonprofit_by_ein(self, temp_db):
        result = lookup_funder(
            funder_name="ACME Nonprofit",
            funder_ein="987654321",
            db_path=temp_db,
        )
        assert result.total_revenue == 5_000_000
        assert result.total_assets == 2_000_000
        assert result.state == "MD"

    def test_lookup_by_name_fallback(self, temp_db):
        result = lookup_funder(
            funder_name="Smith Family Foundation",
            funder_ein=None,
            db_path=temp_db,
        )
        # Should find via name match in BMF
        assert result.ein == "123456789"
        assert result.capacity_tier == "major"

    def test_lookup_unknown_funder(self, temp_db):
        result = lookup_funder(
            funder_name="Nonexistent Foundation",
            funder_ein="000000000",
            db_path=temp_db,
        )
        assert result.capacity_tier is None
        assert result.total_assets is None

    def test_lookup_missing_database(self):
        result = lookup_funder(
            funder_name="Test",
            db_path="/nonexistent/path.db",
        )
        assert result.funder_name == "Test"
        assert result.capacity_tier is None


# ---------------------------------------------------------------------------
# Batch Enrichment Tests
# ---------------------------------------------------------------------------

class TestBatchEnrichment:

    def test_batch_enriches_unique_funders(self, temp_db):
        opps = [
            Opportunity(
                opportunity_id="1", title="Grant A",
                funder="Smith Family Foundation", funder_type="foundation",
                description="test",
            ),
            Opportunity(
                opportunity_id="2", title="Grant B",
                funder="Smith Family Foundation", funder_type="foundation",
                description="test",
            ),
            Opportunity(
                opportunity_id="3", title="Grant C",
                funder="Unknown Funder", funder_type="government",
                description="test",
            ),
        ]
        cache = enrich_opportunities_batch(opps, db_path=temp_db)

        assert len(cache) == 2  # 2 unique funders
        assert "Smith Family Foundation" in cache
        assert cache["Smith Family Foundation"].capacity_tier == "major"

    def test_batch_handles_empty_list(self, temp_db):
        cache = enrich_opportunities_batch([], db_path=temp_db)
        assert len(cache) == 0


# ---------------------------------------------------------------------------
# Prompt Integration Tests
# ---------------------------------------------------------------------------

class TestPromptIntegration:

    def test_thorough_prompt_includes_funder_intel(self, sample_org):
        opp = Opportunity(
            opportunity_id="1", title="Education Grant",
            funder="Smith Foundation", funder_type="foundation",
            description="Funding for education programs",
        )
        intel = FunderIntelligence(
            funder_name="Smith Foundation",
            capacity_tier="major",
            grants_paid=5_000_000,
            total_assets=100_000_000,
            giving_trend="growing",
            primary_grant_states=["VA"],
        )

        system, user = _build_thorough_screening_prompt(opp, sample_org, intel)

        assert "FUNDER INTELLIGENCE" in user
        assert "major" in user
        assert "$5,000,000" in user
        assert "Use the funder intelligence" in user

    def test_thorough_prompt_without_funder_intel(self, sample_org):
        opp = Opportunity(
            opportunity_id="1", title="Education Grant",
            funder="Unknown", funder_type="government",
            description="Funding for education programs",
        )

        system, user = _build_thorough_screening_prompt(opp, sample_org, None)

        assert "FUNDER INTELLIGENCE" not in user

    def test_thorough_prompt_with_empty_intel(self, sample_org):
        opp = Opportunity(
            opportunity_id="1", title="Grant",
            funder="Unknown", funder_type="foundation",
            description="test",
        )
        intel = FunderIntelligence(funder_name="Unknown")

        # Empty intel (no capacity_tier, no total_assets) should not inject
        system, user = _build_thorough_screening_prompt(opp, sample_org, intel)
        assert "FUNDER INTELLIGENCE" not in user
