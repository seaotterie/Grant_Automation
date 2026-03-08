"""
Tests for Enhanced URL Discovery Pipeline

Tests the cascading 6-stage URL discovery pipeline including:
- Stage 0: User-provided URL
- Stage 1: 990 XML extraction
- Stage 2: Multi-year 990 cross-form consolidation
- Stage 3: ProPublica JSON API
- Stage 4: DuckDuckGo + Wikidata
- Stage 6: Haiku predictor
- Stage 8: Name → domain heuristic

Tests use mocking to avoid external API calls.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.enhanced_url_discovery import (
    EnhancedURLDiscoveryPipeline,
    URLCandidate,
    PipelineResult,
    _normalize_url,
    _extract_website_from_xml,
    _is_reference_site,
    _extract_url_array,
    _generate_domain_guesses,
)


# ---------------------------------------------------------------------------
# Unit tests for pure helper functions
# ---------------------------------------------------------------------------

class TestNormalizeUrl:
    def test_adds_https(self):
        assert _normalize_url("example.org") == "https://example.org"

    def test_strips_trailing_slash(self):
        assert _normalize_url("https://example.org/") == "https://example.org"

    def test_lowercases_domain(self):
        assert _normalize_url("HTTPS://EXAMPLE.ORG") == "https://example.org"

    def test_rejects_junk(self):
        assert _normalize_url("none") is None
        assert _normalize_url("n/a") is None
        assert _normalize_url("") is None
        assert _normalize_url(None) is None
        assert _normalize_url("null") is None

    def test_preserves_path(self):
        result = _normalize_url("https://Example.Org/About/Us")
        assert result == "https://example.org/About/Us"

    def test_rejects_no_dot(self):
        assert _normalize_url("localhost") is None


class TestExtractWebsiteFromXml:
    def test_extracts_with_namespace(self):
        xml = b'''<?xml version="1.0"?>
        <Return xmlns="http://www.irs.gov/efile">
          <ReturnData>
            <IRS990>
              <WebsiteAddressTxt>www.example.org</WebsiteAddressTxt>
            </IRS990>
          </ReturnData>
        </Return>'''
        result = _extract_website_from_xml(xml)
        assert result == "https://www.example.org"

    def test_extracts_without_namespace(self):
        xml = b'''<?xml version="1.0"?>
        <Return>
          <ReturnData>
            <IRS990>
              <WebsiteAddressTxt>https://example.org</WebsiteAddressTxt>
            </IRS990>
          </ReturnData>
        </Return>'''
        result = _extract_website_from_xml(xml)
        assert result == "https://example.org"

    def test_returns_none_for_missing(self):
        xml = b'''<?xml version="1.0"?>
        <Return><ReturnData><IRS990></IRS990></ReturnData></Return>'''
        assert _extract_website_from_xml(xml) is None

    def test_returns_none_for_invalid_xml(self):
        assert _extract_website_from_xml(b"not xml") is None


class TestIsReferenceSite:
    def test_detects_wikipedia(self):
        assert _is_reference_site("https://en.wikipedia.org/wiki/Example") is True

    def test_detects_facebook(self):
        assert _is_reference_site("https://www.facebook.com/example") is True

    def test_passes_org_domain(self):
        assert _is_reference_site("https://www.herosbridge.org") is False


class TestExtractUrlArray:
    def test_parses_json_array(self):
        result = _extract_url_array('["https://a.org", "https://b.org"]')
        assert result == ["https://a.org", "https://b.org"]

    def test_extracts_from_text(self):
        result = _extract_url_array('Here is the URL: ["https://a.org"] done')
        assert result == ["https://a.org"]

    def test_regex_fallback(self):
        result = _extract_url_array("The website is https://example.org and also https://test.org")
        assert "https://example.org" in result
        assert "https://test.org" in result


class TestGenerateDomainGuesses:
    def test_basic_name(self):
        guesses = _generate_domain_guesses("Heroes Bridge")
        urls = [g[0] for g in guesses]
        assert "https://www.herosbridge.org" in urls or "https://www.heroesbridge.org" in urls

    def test_strips_suffix(self):
        guesses = _generate_domain_guesses("American Red Cross Foundation Inc")
        urls = [g[0] for g in guesses]
        # Should produce domain without inc/foundation
        assert any("redcross" in u or "americanredcross" in u for u in urls)

    def test_empty_name(self):
        assert _generate_domain_guesses("") == []
        assert _generate_domain_guesses(None) == []

    def test_includes_hyphenated(self):
        guesses = _generate_domain_guesses("Open Source Initiative")
        urls = [g[0] for g in guesses]
        assert any("-" in u for u in urls)  # should have hyphenated variant


# ---------------------------------------------------------------------------
# Unit tests for URLCandidate
# ---------------------------------------------------------------------------

class TestURLCandidate:
    def test_final_confidence_valid(self):
        c = URLCandidate(url="https://a.org", source="990_xml", stage=1, confidence=0.85)
        c.validation_status = "valid"
        # valid + not ein_verified → 0.85 * 0.90 = 0.765
        assert 0.76 <= c.final_confidence <= 0.77

    def test_final_confidence_valid_with_ein(self):
        c = URLCandidate(url="https://a.org", source="haiku", stage=6, confidence=0.85)
        c.validation_status = "valid"
        c.ein_verified = True
        # valid + ein_verified → 0.85 * 1.10 = 0.935, capped at 0.95
        assert c.final_confidence == 0.935

    def test_final_confidence_invalid(self):
        c = URLCandidate(url="https://a.org", source="test", stage=8, confidence=0.50)
        c.validation_status = "invalid"
        assert c.final_confidence == 0.0

    def test_final_confidence_timeout(self):
        c = URLCandidate(url="https://a.org", source="test", stage=4, confidence=0.70)
        c.validation_status = "timeout"
        # 0.70 * 0.85 = 0.595
        assert abs(c.final_confidence - 0.595) < 0.01


# ---------------------------------------------------------------------------
# Integration-style tests for pipeline stages (mocked external calls)
# ---------------------------------------------------------------------------

class TestPipelineStage0:
    """Stage 0: User-provided URL"""

    @pytest.mark.asyncio
    async def test_user_url_returned(self):
        pipeline = EnhancedURLDiscoveryPipeline(validate_urls=False)
        result = await pipeline.discover(
            ein="123456789",
            organization_name="Test Org",
            user_url="https://testorg.org",
        )
        assert result.primary_url is not None
        assert result.primary_url.url == "https://testorg.org"
        assert result.primary_url.source == "user_provided"
        assert result.stage_resolved == 0

    @pytest.mark.asyncio
    async def test_no_user_url_falls_through(self):
        pipeline = EnhancedURLDiscoveryPipeline(validate_urls=False)
        # Patch all stages to return empty so we can test cascade
        with patch.object(pipeline, '_stage_1_990_xml', return_value=[]), \
             patch.object(pipeline, '_stage_2_multiyear_990', return_value=[]), \
             patch.object(pipeline, '_stage_3_propublica_json', return_value=[]), \
             patch.object(pipeline, '_stage_4_public_apis', return_value=[]), \
             patch.object(pipeline, '_stage_6_haiku_predictor', return_value=[]), \
             patch.object(pipeline, '_stage_8_name_heuristic', return_value=[]):
            result = await pipeline.discover(
                ein="123456789",
                organization_name="Test Org",
            )
            assert result.primary_url is None
            assert 0 in result.stages_attempted


class TestPipelineStage8:
    """Stage 8: Name heuristic (no external deps, easy to test)"""

    @pytest.mark.asyncio
    async def test_heuristic_generates_candidates(self):
        pipeline = EnhancedURLDiscoveryPipeline(validate_urls=False)
        ctx = {"ein": "123456789", "name": "Heroes Bridge", "city": "", "state": "", "ntee": ""}

        candidates = await pipeline._stage_8_name_heuristic(ctx)
        assert len(candidates) > 0
        assert all(c.stage == 8 for c in candidates)
        assert all(c.source == "name_heuristic" for c in candidates)
        urls = [c.url for c in candidates]
        assert any("heroesbridge" in u for u in urls)


class TestPipelineCascade:
    """Test that pipeline cascades correctly through stages."""

    @pytest.mark.asyncio
    async def test_stops_at_first_hit(self):
        pipeline = EnhancedURLDiscoveryPipeline(validate_urls=False)

        # Stage 1 returns a hit → pipeline should stop
        stage1_candidate = URLCandidate(
            url="https://example990.org",
            source="990_xml",
            stage=1,
            confidence=0.85,
        )

        with patch.object(pipeline, '_stage_1_990_xml', return_value=[stage1_candidate]), \
             patch.object(pipeline, '_stage_2_multiyear_990', return_value=[]) as mock_s2:
            result = await pipeline.discover(
                ein="123456789",
                organization_name="Test Org",
            )
            assert result.primary_url.url == "https://example990.org"
            assert result.stage_resolved == 1
            # Stage 2 should NOT have been called since stage 1 found a result
            mock_s2.assert_not_called()

    @pytest.mark.asyncio
    async def test_falls_to_later_stage(self):
        pipeline = EnhancedURLDiscoveryPipeline(validate_urls=False)

        stage4_candidate = URLCandidate(
            url="https://fromddg.org",
            source="duckduckgo",
            stage=4,
            confidence=0.70,
        )

        with patch.object(pipeline, '_stage_1_990_xml', return_value=[]), \
             patch.object(pipeline, '_stage_2_multiyear_990', return_value=[]), \
             patch.object(pipeline, '_stage_3_propublica_json', return_value=[]), \
             patch.object(pipeline, '_stage_4_public_apis', return_value=[stage4_candidate]):
            result = await pipeline.discover(
                ein="123456789",
                organization_name="Test Org",
            )
            assert result.primary_url.url == "https://fromddg.org"
            assert result.stage_resolved == 4


class TestPipelineResult:
    """Test PipelineResult serialization."""

    def test_to_dict(self):
        pr = PipelineResult(ein="123456789", organization_name="Test")
        pr.primary_url = URLCandidate(
            url="https://test.org", source="user_provided",
            stage=0, confidence=0.95,
        )
        pr.primary_url.validation_status = "valid"
        pr.stage_resolved = 0
        pr.stages_attempted = [0]
        pr.elapsed_ms = 50.5

        d = pr.to_dict()
        assert d["ein"] == "123456789"
        assert d["primary_url"]["url"] == "https://test.org"
        assert d["stage_resolved"] == 0
        assert d["elapsed_ms"] == 50.5
