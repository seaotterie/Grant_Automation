"""
Unit Tests for Composite Scorer V2 (Critical Scoring Module)
============================================================

Comprehensive tests for the 990-PF Composite Scoring System V2.

Test Categories:
1. Component Scoring - Tests individual scoring components
2. Weighted Integration - Tests weighted score calculation
3. Recommendation Logic - Tests PASS/ABSTAIN/FAIL thresholds
4. Confidence Calculation - Tests confidence scoring
5. Data Quality Handling - Tests missing data scenarios
6. Edge Cases - Tests boundary conditions

Scorer Under Test:
- Name: Composite Scorer V2
- Purpose: Multi-dimensional foundation matching (8 components)
- Weights: NTEE (30%), Geographic (20%), Coherence (12%), +5 others
- Thresholds: PASS ≥58, ABSTAIN 45-58, FAIL <45
"""

import pytest
from datetime import datetime
from typing import List, Dict

from src.scoring.composite_scorer_v2 import (
    CompositeScoreV2,
    CompositeScoreResult,
    FoundationOpportunityData
)
from src.profiles.models import OrganizationProfile, ScheduleIGrantee, OrganizationType
from src.scoring.ntee_scorer import NTEEDataSource


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_profile():
    """Sample nonprofit organization profile."""
    return OrganizationProfile(
        profile_id="test_profile_001",
        name="Heroes Bridge",
        organization_type=OrganizationType.NONPROFIT,
        ein="54-1026365",
        location="Raleigh, VA 27601",
        focus_areas=["Veteran Services", "Community Support"],
        ntee_codes=["W30", "P85"],
        program_areas=["Veteran Services", "Community Support"],
        mission_statement="Supporting military veterans and their families"
    )


@pytest.fixture
def high_match_foundation():
    """Foundation with high match potential to sample profile."""
    return FoundationOpportunityData(
        foundation_ein="123456789",
        foundation_name="Veterans Support Foundation",
        ntee_codes=["W30", "W90"],
        ntee_code_sources={"W30": NTEEDataSource.BMF, "W90": NTEEDataSource.SCHEDULE_I},
        ntee_code_dates={"W30": datetime(2023, 1, 1), "W90": datetime(2023, 1, 1)},
        geographic_focus_states=["VA", "NC", "MD"],
        total_assets=25000000.0,
        grants_paid_total=1000000.0,
        typical_grant_amount=100000.0,
        grant_amount_min=50000.0,
        grant_amount_max=250000.0,
        accepts_applications=True,
        most_recent_filing_year=2023,
        schedule_i_grantees=_create_sample_grantees(ntee_codes=["W30", "W90", "W30", "W90", "W30"])
    )


@pytest.fixture
def low_match_foundation():
    """Foundation with low match potential to sample profile."""
    return FoundationOpportunityData(
        foundation_ein="987654321",
        foundation_name="Arts and Culture Foundation",
        ntee_codes=["A20", "A60"],
        ntee_code_sources={"A20": NTEEDataSource.BMF, "A60": NTEEDataSource.SCHEDULE_I},
        geographic_focus_states=["CA", "NY"],  # Different states
        total_assets=500000.0,  # Smaller foundation
        grants_paid_total=25000.0,
        typical_grant_amount=10000.0,  # Smaller grants
        accepts_applications=False,  # Doesn't accept applications
        most_recent_filing_year=2020,  # Older filing
        schedule_i_grantees=_create_sample_grantees(ntee_codes=["A20", "A60", "A20"])
    )


@pytest.fixture
def missing_data_foundation():
    """Foundation with missing optional data."""
    return FoundationOpportunityData(
        foundation_ein="555555555",
        foundation_name="Unknown Foundation",
        ntee_codes=["W30"],
        ntee_code_sources={"W30": NTEEDataSource.BMF},
        geographic_focus_states=None,  # No geographic restrictions
        total_assets=None,  # Missing financial data
        grants_paid_total=None,
        typical_grant_amount=None,
        accepts_applications=None,  # Unknown application policy
        most_recent_filing_year=None,  # Missing filing year
        schedule_i_grantees=None  # No Schedule I data
    )


def _create_sample_grantees(ntee_codes: List[str]) -> List[ScheduleIGrantee]:
    """Create sample Schedule I grantees with specified NTEE codes."""
    grantees = []
    for i, ntee in enumerate(ntee_codes):
        grantees.append(ScheduleIGrantee(
            recipient_name=f"Grantee {i+1}",
            recipient_ein=f"12345678{i}",
            recipient_ntee_code=ntee,
            grant_amount=50000.0,
            recipient_city="Test City",
            recipient_state="VA"
        ))
    return grantees


# ============================================================================
# Test Class 1: Component Scoring
# ============================================================================

class TestComponentScoring:
    """Test individual scoring components."""

    def test_ntee_alignment_high_match(self, sample_profile, high_match_foundation):
        """Test NTEE alignment with high match."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, high_match_foundation)

        # NTEE W30 exact match should score well
        assert result.ntee_alignment_score > 50.0
        assert "W30" in result.ntee_explanation or "exact match" in result.ntee_explanation.lower()

    def test_ntee_alignment_low_match(self, sample_profile, low_match_foundation):
        """Test NTEE alignment with low match."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, low_match_foundation)

        # NTEE mismatch (W30 vs A20) should score low
        assert result.ntee_alignment_score < 40.0

    def test_geographic_match_exact(self, sample_profile, high_match_foundation):
        """Test geographic match with exact state match."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, high_match_foundation)

        # VA in both profile and foundation states
        assert result.geographic_match_score == 100.0

    def test_geographic_match_mismatch(self, sample_profile, low_match_foundation):
        """Test geographic match with state mismatch."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, low_match_foundation)

        # VA vs CA/NY mismatch
        assert result.geographic_match_score == 0.0

    def test_geographic_match_national(self, sample_profile, missing_data_foundation):
        """Test geographic match with national foundation (no restrictions)."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, missing_data_foundation)

        # No geographic restrictions = national = 50.0
        assert result.geographic_match_score == 50.0

    def test_financial_capacity_major(self, sample_profile):
        """Test financial capacity scoring for major foundation."""
        scorer = CompositeScoreV2()
        major_foundation = FoundationOpportunityData(
            foundation_ein="111111111",
            foundation_name="Major Foundation",
            ntee_codes=["W30"],
            ntee_code_sources={"W30": NTEEDataSource.BMF},
            total_assets=75000000.0  # > $50M = major
        )

        result = scorer.score_foundation_match(sample_profile, major_foundation)
        assert result.financial_capacity_score == 100.0

    def test_financial_capacity_small(self, sample_profile):
        """Test financial capacity scoring for small foundation."""
        scorer = CompositeScoreV2()
        small_foundation = FoundationOpportunityData(
            foundation_ein="222222222",
            foundation_name="Small Foundation",
            ntee_codes=["W30"],
            ntee_code_sources={"W30": NTEEDataSource.BMF},
            total_assets=150000.0  # $100K-$1M = small
        )

        result = scorer.score_foundation_match(sample_profile, small_foundation)
        assert result.financial_capacity_score == 50.0

    def test_application_policy_accepts(self, sample_profile):
        """Test application policy scoring when foundation accepts applications."""
        scorer = CompositeScoreV2()
        accepts_foundation = FoundationOpportunityData(
            foundation_ein="333333333",
            foundation_name="Accepting Foundation",
            ntee_codes=["W30"],
            ntee_code_sources={"W30": NTEEDataSource.BMF},
            accepts_applications=True
        )

        result = scorer.score_foundation_match(sample_profile, accepts_foundation)
        assert result.application_policy_score == 100.0

    def test_application_policy_rejects(self, sample_profile, low_match_foundation):
        """Test application policy scoring when foundation doesn't accept applications."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, low_match_foundation)

        # Does not accept = major penalty
        assert result.application_policy_score == 20.0

    def test_filing_recency_recent(self, sample_profile, high_match_foundation):
        """Test filing recency scoring with recent filing."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, high_match_foundation)

        # 2023 filing = recent = high score
        assert result.filing_recency_score > 80.0
        assert result.time_decay_penalty > 0.9  # Minimal penalty

    def test_filing_recency_old(self, sample_profile, low_match_foundation):
        """Test filing recency scoring with older filing."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, low_match_foundation)

        # 2020 filing = older = lower score
        assert result.filing_recency_score < 80.0
        assert result.time_decay_penalty < 1.0


# ============================================================================
# Test Class 2: Weighted Integration
# ============================================================================

class TestWeightedIntegration:
    """Test weighted score calculation and integration."""

    def test_high_match_final_score(self, sample_profile, high_match_foundation):
        """Test that high match foundation scores above PASS threshold."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, high_match_foundation)

        # High match should score >= 58 (PASS threshold)
        assert result.final_score >= 58.0
        assert result.recommendation == "PASS"

    def test_low_match_final_score(self, sample_profile, low_match_foundation):
        """Test that low match foundation scores below PASS threshold."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, low_match_foundation)

        # Low match should score < 58
        assert result.final_score < 58.0
        assert result.recommendation in ["ABSTAIN", "FAIL"]

    def test_score_components_sum_correctly(self, sample_profile, high_match_foundation):
        """Test that component scores are weighted correctly."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, high_match_foundation)

        # Verify all component scores are present
        assert isinstance(result.ntee_alignment_score, float)
        assert isinstance(result.geographic_match_score, float)
        assert isinstance(result.recipient_coherence_score, float)
        assert isinstance(result.financial_capacity_score, float)
        assert isinstance(result.grant_size_fit_score, float)
        assert isinstance(result.application_policy_score, float)
        assert isinstance(result.filing_recency_score, float)
        assert isinstance(result.foundation_type_score, float)

        # All scores should be 0-100
        assert 0.0 <= result.ntee_alignment_score <= 100.0
        assert 0.0 <= result.geographic_match_score <= 100.0
        assert 0.0 <= result.recipient_coherence_score <= 100.0

    def test_coherence_boost_application(self, sample_profile, high_match_foundation):
        """Test that coherence boost is applied correctly."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, high_match_foundation)

        # Coherence boost should be 0.0-0.15
        assert 0.0 <= result.coherence_boost <= 0.15

    def test_time_decay_penalty_application(self, sample_profile, high_match_foundation):
        """Test that time decay penalty is applied correctly."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, high_match_foundation)

        # Time decay penalty should be 0.0-1.0 (multiplier)
        assert 0.0 <= result.time_decay_penalty <= 1.0

    def test_final_score_capped_at_100(self, sample_profile):
        """Test that final score is capped at 100 even with boosts."""
        scorer = CompositeScoreV2()

        # Create perfect match foundation
        perfect_foundation = FoundationOpportunityData(
            foundation_ein="999999999",
            foundation_name="Perfect Foundation",
            ntee_codes=["W30", "P85"],  # Exact matches
            ntee_code_sources={"W30": NTEEDataSource.BMF, "P85": NTEEDataSource.SCHEDULE_I},
            ntee_code_dates={"W30": datetime(2024, 1, 1), "P85": datetime(2024, 1, 1)},
            geographic_focus_states=["VA"],
            total_assets=100000000.0,  # Major foundation
            grants_paid_total=5000000.0,
            typical_grant_amount=150000.0,  # Good fit
            accepts_applications=True,
            most_recent_filing_year=datetime.now().year,  # Current year
            schedule_i_grantees=_create_sample_grantees(["W30"] * 10)  # High coherence
        )

        result = scorer.score_foundation_match(sample_profile, perfect_foundation)

        # Final score should be capped at 100
        assert result.final_score <= 100.0


# ============================================================================
# Test Class 3: Recommendation Logic
# ============================================================================

class TestRecommendationLogic:
    """Test PASS/ABSTAIN/FAIL recommendation thresholds."""

    def test_pass_threshold(self, sample_profile, high_match_foundation):
        """Test PASS recommendation at >= 58 threshold."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, high_match_foundation)

        if result.final_score >= 58.0:
            assert result.recommendation == "PASS"
            assert result.should_abstain is False

    def test_fail_threshold(self, sample_profile, low_match_foundation):
        """Test FAIL recommendation at < 45 threshold."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, low_match_foundation)

        if result.final_score < 45.0:
            assert result.recommendation == "FAIL"
            # FAIL might also trigger abstain in some cases

    def test_abstain_borderline_score(self, sample_profile):
        """Test ABSTAIN recommendation for borderline scores (45-58)."""
        scorer = CompositeScoreV2()

        # Create borderline foundation (tuned to score ~50)
        borderline_foundation = FoundationOpportunityData(
            foundation_ein="444444444",
            foundation_name="Borderline Foundation",
            ntee_codes=["W30"],  # Some alignment
            ntee_code_sources={"W30": NTEEDataSource.BMF},
            geographic_focus_states=["VA"],  # Geographic match
            total_assets=750000.0,  # Medium assets
            accepts_applications=None,  # Unknown
            most_recent_filing_year=2022  # Somewhat recent
        )

        result = scorer.score_foundation_match(sample_profile, borderline_foundation)

        # If score is in abstain range, should recommend ABSTAIN
        if 45.0 <= result.final_score <= 58.0:
            assert result.recommendation == "ABSTAIN"
            assert result.should_abstain is True
            assert result.abstain_reason is not None

    def test_abstain_missing_critical_data(self, sample_profile):
        """Test ABSTAIN recommendation when critical data is missing."""
        scorer = CompositeScoreV2()

        # Foundation missing NTEE codes
        no_ntee_foundation = FoundationOpportunityData(
            foundation_ein="666666666",
            foundation_name="No NTEE Foundation",
            ntee_codes=[],  # Missing NTEE!
            ntee_code_sources={},
            geographic_focus_states=["VA"],
            accepts_applications=True
        )

        result = scorer.score_foundation_match(sample_profile, no_ntee_foundation)

        # Should abstain due to missing NTEE codes
        assert result.recommendation == "ABSTAIN"
        assert result.should_abstain is True
        assert "NTEE" in result.abstain_reason or "mission" in result.abstain_reason.lower()

    def test_abstain_geographic_mismatch(self, sample_profile):
        """Test ABSTAIN recommendation for geographic mismatch."""
        scorer = CompositeScoreV2()

        # Foundation with strict geographic focus (not VA)
        geo_mismatch_foundation = FoundationOpportunityData(
            foundation_ein="777777777",
            foundation_name="California Only Foundation",
            ntee_codes=["W30"],
            ntee_code_sources={"W30": NTEEDataSource.BMF},
            geographic_focus_states=["CA"],  # Only CA, not VA
            total_assets=10000000.0,
            accepts_applications=True,
            most_recent_filing_year=2023
        )

        result = scorer.score_foundation_match(sample_profile, geo_mismatch_foundation)

        # Should likely abstain or fail due to geographic mismatch
        if result.geographic_match_score == 0.0:
            # Could be ABSTAIN or FAIL depending on other factors
            assert result.recommendation in ["ABSTAIN", "FAIL"]


# ============================================================================
# Test Class 4: Confidence Calculation
# ============================================================================

class TestConfidenceCalculation:
    """Test confidence scoring."""

    def test_high_confidence_recent_data(self, sample_profile, high_match_foundation):
        """Test high confidence with recent, complete data."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, high_match_foundation)

        # Recent filing + Schedule I data + strong NTEE = high confidence
        assert result.confidence > 0.6
        assert 0.0 <= result.confidence <= 1.0

    def test_low_confidence_missing_data(self, sample_profile, missing_data_foundation):
        """Test lower confidence with missing data."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, missing_data_foundation)

        # Missing data = lower confidence
        assert result.confidence <= 0.8  # Not maximum confidence
        assert 0.0 <= result.confidence <= 1.0

    def test_confidence_range_valid(self, sample_profile, high_match_foundation):
        """Test that confidence is always in valid range."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, high_match_foundation)

        assert 0.0 <= result.confidence <= 1.0


# ============================================================================
# Test Class 5: Data Quality Handling
# ============================================================================

class TestDataQualityHandling:
    """Test handling of missing and incomplete data."""

    def test_missing_profile_ntee_codes(self, high_match_foundation):
        """Test handling when profile has no NTEE codes."""
        scorer = CompositeScoreV2()

        profile_no_ntee = OrganizationProfile(
            ein="999999999",
            name="No NTEE Org",
            ntee_codes=[],  # No NTEE codes
            state="VA",
            revenue=1000000.0
        )

        result = scorer.score_foundation_match(profile_no_ntee, high_match_foundation)

        # Should handle gracefully
        assert isinstance(result, CompositeScoreResult)
        assert result.ntee_alignment_score == 0.0  # No NTEE = 0 score

    def test_missing_foundation_schedule_i(self, sample_profile):
        """Test handling when foundation has no Schedule I data."""
        scorer = CompositeScoreV2()

        foundation_no_schedule_i = FoundationOpportunityData(
            foundation_ein="888888888",
            foundation_name="No Schedule I Foundation",
            ntee_codes=["W30"],
            ntee_code_sources={"W30": NTEEDataSource.BMF},
            schedule_i_grantees=None  # No Schedule I data
        )

        result = scorer.score_foundation_match(sample_profile, foundation_no_schedule_i)

        # Should handle gracefully with neutral scores
        assert isinstance(result, CompositeScoreResult)
        assert result.recipient_coherence_score == 50.0  # Neutral
        assert result.coherence_boost == 0.0  # No boost
        assert result.schedule_i_analysis is None

    def test_missing_grant_size_data(self, sample_profile):
        """Test handling when grant size data is missing."""
        scorer = CompositeScoreV2()

        foundation_no_grant_size = FoundationOpportunityData(
            foundation_ein="101010101",
            foundation_name="No Grant Size Foundation",
            ntee_codes=["W30"],
            ntee_code_sources={"W30": NTEEDataSource.BMF},
            typical_grant_amount=None  # Missing
        )

        result = scorer.score_foundation_match(sample_profile, foundation_no_grant_size)

        # Should handle gracefully
        assert result.grant_size_fit_score == 50.0  # Neutral
        assert result.grant_size_analysis is None

    def test_complete_missing_data_foundation(self, sample_profile, missing_data_foundation):
        """Test handling foundation with all optional data missing."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, missing_data_foundation)

        # Should complete without errors
        assert isinstance(result, CompositeScoreResult)
        assert 0.0 <= result.final_score <= 100.0
        assert result.recommendation in ["PASS", "ABSTAIN", "FAIL"]


# ============================================================================
# Test Class 6: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test boundary conditions and edge cases."""

    def test_zero_revenue_organization(self, high_match_foundation):
        """Test with organization that has zero revenue."""
        scorer = CompositeScoreV2()

        zero_revenue_profile = OrganizationProfile(
            ein="000000000",
            name="Zero Revenue Org",
            ntee_codes=["W30"],
            state="VA",
            revenue=0.0  # Zero revenue
        )

        result = scorer.score_foundation_match(zero_revenue_profile, high_match_foundation)

        # Should handle without division by zero errors
        assert isinstance(result, CompositeScoreResult)
        assert 0.0 <= result.final_score <= 100.0

    def test_very_large_grant_amount(self, sample_profile):
        """Test with extremely large grant amount."""
        scorer = CompositeScoreV2()

        huge_grant_foundation = FoundationOpportunityData(
            foundation_ein="121212121",
            foundation_name="Huge Grant Foundation",
            ntee_codes=["W30"],
            ntee_code_sources={"W30": NTEEDataSource.BMF},
            typical_grant_amount=50000000.0,  # $50M grant
            total_assets=1000000000.0  # $1B assets
        )

        result = scorer.score_foundation_match(sample_profile, huge_grant_foundation)

        # Should handle without overflow
        assert isinstance(result, CompositeScoreResult)
        assert 0.0 <= result.final_score <= 100.0

    def test_future_filing_year(self, sample_profile):
        """Test with filing year in the future (data error)."""
        scorer = CompositeScoreV2()

        future_foundation = FoundationOpportunityData(
            foundation_ein="131313131",
            foundation_name="Future Foundation",
            ntee_codes=["W30"],
            ntee_code_sources={"W30": NTEEDataSource.BMF},
            most_recent_filing_year=datetime.now().year + 1  # Future year!
        )

        result = scorer.score_foundation_match(sample_profile, future_foundation)

        # Should handle gracefully (might treat as recent or apply specific logic)
        assert isinstance(result, CompositeScoreResult)
        assert 0.0 <= result.final_score <= 100.0

    def test_empty_ntee_codes_list(self, sample_profile):
        """Test with empty NTEE codes list."""
        scorer = CompositeScoreV2()

        empty_ntee_foundation = FoundationOpportunityData(
            foundation_ein="141414141",
            foundation_name="Empty NTEE Foundation",
            ntee_codes=[],  # Empty list
            ntee_code_sources={},
            geographic_focus_states=["VA"]
        )

        result = scorer.score_foundation_match(sample_profile, empty_ntee_foundation)

        # Should handle empty list
        assert isinstance(result, CompositeScoreResult)
        assert result.ntee_alignment_score == 0.0

    def test_multiple_identical_ntee_codes(self, sample_profile):
        """Test with duplicate NTEE codes."""
        scorer = CompositeScoreV2()

        duplicate_ntee_foundation = FoundationOpportunityData(
            foundation_ein="151515151",
            foundation_name="Duplicate NTEE Foundation",
            ntee_codes=["W30", "W30", "W30"],  # Duplicates
            ntee_code_sources={
                "W30": NTEEDataSource.BMF  # Same code from different sources
            },
            geographic_focus_states=["VA"]
        )

        result = scorer.score_foundation_match(sample_profile, duplicate_ntee_foundation)

        # Should handle duplicates gracefully
        assert isinstance(result, CompositeScoreResult)
        assert result.ntee_alignment_score > 0.0  # Should still match


# ============================================================================
# Test Class 7: Structure and Types
# ============================================================================

class TestStructureAndTypes:
    """Test data structure and type validation."""

    def test_composite_score_result_structure(self, sample_profile, high_match_foundation):
        """Test that CompositeScoreResult has all required fields."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, high_match_foundation)

        # Required fields
        assert hasattr(result, 'final_score')
        assert hasattr(result, 'recommendation')
        assert hasattr(result, 'ntee_alignment_score')
        assert hasattr(result, 'geographic_match_score')
        assert hasattr(result, 'recipient_coherence_score')
        assert hasattr(result, 'financial_capacity_score')
        assert hasattr(result, 'grant_size_fit_score')
        assert hasattr(result, 'application_policy_score')
        assert hasattr(result, 'filing_recency_score')
        assert hasattr(result, 'foundation_type_score')
        assert hasattr(result, 'coherence_boost')
        assert hasattr(result, 'time_decay_penalty')
        assert hasattr(result, 'ntee_explanation')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'should_abstain')

        # Optional fields
        assert hasattr(result, 'schedule_i_analysis')
        assert hasattr(result, 'grant_size_analysis')
        assert hasattr(result, 'abstain_reason')

    def test_recommendation_values(self, sample_profile, high_match_foundation, low_match_foundation):
        """Test that recommendation is always one of valid values."""
        scorer = CompositeScoreV2()

        result1 = scorer.score_foundation_match(sample_profile, high_match_foundation)
        result2 = scorer.score_foundation_match(sample_profile, low_match_foundation)

        assert result1.recommendation in ["PASS", "ABSTAIN", "FAIL"]
        assert result2.recommendation in ["PASS", "ABSTAIN", "FAIL"]

    def test_score_ranges(self, sample_profile, high_match_foundation):
        """Test that all scores are in valid 0-100 range."""
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(sample_profile, high_match_foundation)

        assert 0.0 <= result.final_score <= 100.0
        assert 0.0 <= result.ntee_alignment_score <= 100.0
        assert 0.0 <= result.geographic_match_score <= 100.0
        assert 0.0 <= result.recipient_coherence_score <= 100.0
        assert 0.0 <= result.financial_capacity_score <= 100.0
        assert 0.0 <= result.grant_size_fit_score <= 100.0
        assert 0.0 <= result.application_policy_score <= 100.0
        assert 0.0 <= result.filing_recency_score <= 100.0
        assert 0.0 <= result.foundation_type_score <= 100.0


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
