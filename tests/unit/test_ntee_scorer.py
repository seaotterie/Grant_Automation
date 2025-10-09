"""
Unit Tests for NTEE Scorer
===========================

Tests for the Two-Part NTEE Scoring System (V2.0) that implements enhanced NTEE
code alignment scoring with multi-source validation and time-decay integration.

Test Categories:
1. NTEE Code Parsing - Parse and validate NTEE code strings
2. Exact Matching - Test exact major and leaf code matches
3. Related Majors - Test related major code partial matches
4. Confidence Scoring - Test confidence penalties for incomplete codes
5. Time Decay - Test time-decay integration for aging data
6. Multi-Source - Test source prioritization (BMF > Schedule I > Website)
7. Edge Cases - Test boundary conditions and error handling
"""

import pytest
from datetime import datetime, timedelta
from src.scoring.ntee_scorer import (
    NTEEScorer,
    NTEECode,
    NTEEDataSource,
    NTEEMatchLevel,
    score_ntee_alignment,
    get_ntee_major_description
)


# ============================================================================
# Test Class 1: NTEE Code Parsing
# ============================================================================

class TestNTEECodeParsing:
    """Test NTEE code parsing and validation"""

    def test_parse_full_code(self):
        """Test parsing full NTEE code (major + leaf)"""
        code = NTEECode.parse("B25")

        assert code is not None
        assert code.major == "B"
        assert code.leaf == "25"
        assert code.full_code == "B25"
        assert code.confidence == 1.0  # Full code = high confidence

    def test_parse_major_only(self):
        """Test parsing major code only"""
        code = NTEECode.parse("B")

        assert code is not None
        assert code.major == "B"
        assert code.leaf is None
        assert code.full_code == "B"
        assert code.confidence == 0.7  # Major-only = confidence penalty

    def test_parse_with_source(self):
        """Test parsing with data source metadata"""
        code = NTEECode.parse("P20", source=NTEEDataSource.BMF)

        assert code.source == NTEEDataSource.BMF
        assert code.major == "P"
        assert code.leaf == "20"

    def test_parse_with_date(self):
        """Test parsing with source date for time-decay"""
        date = datetime(2023, 1, 1)
        code = NTEECode.parse("E20", source=NTEEDataSource.SCHEDULE_I, source_date=date)

        assert code.source_date == date
        assert code.source == NTEEDataSource.SCHEDULE_I

    def test_parse_invalid_codes(self):
        """Test parsing invalid NTEE codes"""
        assert NTEECode.parse("") is None
        assert NTEECode.parse(None) is None
        assert NTEECode.parse("123") is None  # Must start with letter
        assert NTEECode.parse("1B5") is None  # Can't start with number

    def test_parse_case_insensitive(self):
        """Test parsing handles lowercase codes"""
        code_upper = NTEECode.parse("B25")
        code_lower = NTEECode.parse("b25")

        assert code_upper.major == code_lower.major
        assert code_upper.leaf == code_lower.leaf


# ============================================================================
# Test Class 2: Exact Matching
# ============================================================================

class TestExactMatching:
    """Test exact NTEE code matching"""

    def test_exact_full_match(self):
        """Test exact major + leaf match (highest score)"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=["B25"],
            foundation_codes=["B25"]
        )

        assert result.score == 1.0  # Perfect match
        assert result.match_level == NTEEMatchLevel.EXACT_FULL
        assert result.major_score == 1.0
        assert result.leaf_score == 1.0
        assert "Exact NTEE match" in result.explanation

    def test_exact_major_only(self):
        """Test exact major code match with different leafs"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=["B25"],
            foundation_codes=["B30"]
        )

        # Major match (40% weight) only
        assert result.score == 0.4  # 1.0 * 0.4 + 0.0 * 0.6
        assert result.match_level == NTEEMatchLevel.EXACT_MAJOR
        assert result.major_score == 1.0
        assert result.leaf_score == 0.0
        assert "Major match but different subcategory" in result.explanation

    def test_multiple_codes_best_match(self):
        """Test that scorer finds best match among multiple codes"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=["B25", "P20"],  # Education and Health
            foundation_codes=["A20", "B25", "E30"]  # Arts, Education, Health
        )

        # Should find exact B25 match
        assert result.score == 1.0
        assert result.match_level == NTEEMatchLevel.EXACT_FULL

    def test_incomplete_leaf_codes(self):
        """Test matching when one code lacks leaf"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=["B"],  # Major only
            foundation_codes=["B25"]  # Full code
        )

        # Major match + partial leaf credit (0.5) with confidence penalty
        assert result.match_level == NTEEMatchLevel.EXACT_MAJOR
        assert result.major_score == 1.0
        assert result.leaf_score == 0.5  # Partial credit
        # Confidence penalty applied: (1.0 * 0.4 + 0.5 * 0.6) * avg_confidence
        # avg_confidence = (0.7 + 1.0) / 2 = 0.85
        expected_score = (1.0 * 0.4 + 0.5 * 0.6) * 0.85
        assert result.score == pytest.approx(expected_score, abs=0.01)


# ============================================================================
# Test Class 3: Related Majors
# ============================================================================

class TestRelatedMajors:
    """Test related major code partial matching"""

    def test_related_education_codes(self):
        """Test related education major codes (B, E, O)"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=["B25"],  # Education
            foundation_codes=["E20"]  # Elementary/Secondary (related to education)
        )

        # Related major = 0.5 score * 0.4 weight = 0.2
        assert result.score == 0.2
        assert result.match_level == NTEEMatchLevel.RELATED_MAJOR
        assert result.major_score == 0.5
        assert result.leaf_score == 0.0
        assert "Related major codes" in result.explanation

    def test_related_health_codes(self):
        """Test related health major codes (P, Q)"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=["P20"],  # Health
            foundation_codes=["Q30"]  # Hospitals (related to health)
        )

        assert result.score == 0.2  # Related major = 0.5 * 0.4
        assert result.match_level == NTEEMatchLevel.RELATED_MAJOR

    def test_related_environment_codes(self):
        """Test related environment major codes (C, D, K)"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=["C30"],  # Environment
            foundation_codes=["D20"]  # Animal-related (related to environment)
        )

        assert result.score == 0.2
        assert result.match_level == NTEEMatchLevel.RELATED_MAJOR


# ============================================================================
# Test Class 4: No Match and Edge Cases
# ============================================================================

class TestNoMatchAndEdgeCases:
    """Test no-match scenarios and edge cases"""

    def test_complete_mismatch(self):
        """Test completely unrelated NTEE codes"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=["B25"],  # Education
            foundation_codes=["P20"]  # Health (not related)
        )

        assert result.score == 0.0
        assert result.match_level == NTEEMatchLevel.NO_MATCH
        assert result.major_score == 0.0
        assert result.leaf_score == 0.0
        assert "No NTEE code alignment" in result.explanation

    def test_empty_profile_codes(self):
        """Test with no profile NTEE codes"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=[],
            foundation_codes=["B25"]
        )

        assert result.score == 0.0
        assert result.confidence == 0.0
        assert "No valid NTEE codes for profile" in result.explanation

    def test_empty_foundation_codes(self):
        """Test with no foundation NTEE codes"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=["B25"],
            foundation_codes=[]
        )

        assert result.score == 0.0
        assert result.confidence == 0.0
        assert "No valid NTEE codes for foundation" in result.explanation

    def test_both_empty(self):
        """Test with both profiles and foundation having no codes"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=[],
            foundation_codes=[]
        )

        assert result.score == 0.0
        assert "No NTEE codes provided" in result.explanation


# ============================================================================
# Test Class 5: Confidence Scoring
# ============================================================================

class TestConfidenceScoring:
    """Test confidence penalties for incomplete data"""

    def test_confidence_penalty_major_only(self):
        """Test confidence penalty when using major-only codes"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=["B"],  # Major only (confidence = 0.7)
            foundation_codes=["B"]  # Major only (confidence = 0.7)
        )

        # Both codes have 0.7 confidence, avg = 0.7
        # Raw score = 1.0 * 0.4 + 0.5 * 0.6 = 0.7
        # Final = 0.7 * 0.7 confidence = 0.49
        assert result.confidence == 0.7
        expected_score = (1.0 * 0.4 + 0.5 * 0.6) * 0.7
        assert result.score == pytest.approx(expected_score, abs=0.01)

    def test_mixed_confidence(self):
        """Test mixed confidence (full + major-only codes)"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=["B25"],  # Full code (confidence = 1.0)
            foundation_codes=["B"]  # Major only (confidence = 0.7)
        )

        # Average confidence = (1.0 + 0.7) / 2 = 0.85
        assert result.confidence == 0.85

    def test_full_confidence_exact_match(self):
        """Test full confidence with complete codes"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=["B25"],
            foundation_codes=["B25"]
        )

        assert result.confidence == 1.0
        assert result.score == 1.0  # No confidence penalty


# ============================================================================
# Test Class 6: Time Decay Integration
# ============================================================================

class TestTimeDecay:
    """Test time-decay integration for aging NTEE data"""

    def test_recent_data_no_decay(self):
        """Test that recent data has minimal decay"""
        scorer = NTEEScorer(enable_time_decay=True)

        recent_date = datetime.now() - timedelta(days=30)  # 1 month old

        result = scorer.score_alignment(
            profile_codes=["B25"],
            foundation_codes=["B25"],
            profile_code_dates={"B25": recent_date}
        )

        # Recent data should have minimal decay
        assert result.time_decay_factor > 0.95
        assert result.weighted_score > 0.95  # score * decay_factor

    def test_old_data_significant_decay(self):
        """Test that old data has significant decay"""
        scorer = NTEEScorer(enable_time_decay=True)

        old_date = datetime.now() - timedelta(days=3*365)  # 3 years old

        result = scorer.score_alignment(
            profile_codes=["B25"],
            foundation_codes=["B25"],
            foundation_code_dates={"B25": old_date}
        )

        # Old data should have noticeable decay
        assert result.time_decay_factor < 0.95
        assert result.weighted_score < result.score  # Decay applied

    def test_disable_time_decay(self):
        """Test disabling time-decay"""
        scorer = NTEEScorer(enable_time_decay=False)

        old_date = datetime.now() - timedelta(days=3*365)

        result = scorer.score_alignment(
            profile_codes=["B25"],
            foundation_codes=["B25"],
            foundation_code_dates={"B25": old_date}
        )

        # Decay disabled = factor should be 1.0
        assert result.time_decay_factor == 1.0
        assert result.weighted_score == result.score

    def test_missing_dates_no_penalty(self):
        """Test that missing dates don't cause decay penalty"""
        scorer = NTEEScorer(enable_time_decay=True)

        result = scorer.score_alignment(
            profile_codes=["B25"],
            foundation_codes=["B25"]
            # No dates provided
        )

        # Missing dates = no decay penalty
        assert result.time_decay_factor == 1.0


# ============================================================================
# Test Class 7: Convenience Functions
# ============================================================================

class TestConvenienceFunctions:
    """Test convenience functions and utilities"""

    def test_score_ntee_alignment_convenience(self):
        """Test convenience scoring function"""
        result = score_ntee_alignment(
            profile_codes=["B25"],
            foundation_codes=["B25"],
            enable_time_decay=False
        )

        assert result.score == 1.0
        assert result.match_level == NTEEMatchLevel.EXACT_FULL

    def test_get_major_descriptions(self):
        """Test NTEE major code descriptions"""
        assert get_ntee_major_description("B") == "Education"
        assert get_ntee_major_description("P") == "Human Services"
        assert get_ntee_major_description("A") == "Arts, Culture, and Humanities"
        assert get_ntee_major_description("Z") == "Unknown"
        assert get_ntee_major_description("INVALID") == "Unknown"

    def test_major_description_case_insensitive(self):
        """Test major descriptions are case-insensitive"""
        assert get_ntee_major_description("b") == get_ntee_major_description("B")
        assert get_ntee_major_description("p") == get_ntee_major_description("P")


# ============================================================================
# Test Class 8: Multi-Source Validation
# ============================================================================

class TestMultiSourceValidation:
    """Test multi-source NTEE code validation"""

    def test_source_metadata_tracking(self):
        """Test that source metadata is tracked correctly"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=["B25"],
            foundation_codes=["B25"],
            profile_code_sources={"B25": NTEEDataSource.BMF},
            foundation_code_sources={"B25": NTEEDataSource.SCHEDULE_I}
        )

        # Verify source tracking
        assert len(result.profile_codes) == 1
        assert result.profile_codes[0].source == NTEEDataSource.BMF
        assert len(result.foundation_codes) == 1
        assert result.foundation_codes[0].source == NTEEDataSource.SCHEDULE_I

    def test_mixed_sources(self):
        """Test handling multiple codes from different sources"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=["B25", "P20"],
            foundation_codes=["B30", "P20"],
            profile_code_sources={
                "B25": NTEEDataSource.BMF,
                "P20": NTEEDataSource.WEBSITE
            },
            foundation_code_sources={
                "B30": NTEEDataSource.SCHEDULE_I,
                "P20": NTEEDataSource.BMF
            }
        )

        # Should find exact match on P20
        assert result.score == 1.0
        assert result.match_level == NTEEMatchLevel.EXACT_FULL


# ============================================================================
# Test Class 9: Weighted Score Calculation
# ============================================================================

class TestWeightedScoreCalculation:
    """Test that weighted score property works correctly"""

    def test_weighted_score_with_decay(self):
        """Test weighted score includes time decay"""
        scorer = NTEEScorer(enable_time_decay=True)

        old_date = datetime.now() - timedelta(days=2*365)

        result = scorer.score_alignment(
            profile_codes=["B25"],
            foundation_codes=["B25"],
            foundation_code_dates={"B25": old_date}
        )

        # Weighted score should be score * time_decay_factor
        expected_weighted = result.score * result.time_decay_factor
        assert result.weighted_score == pytest.approx(expected_weighted, abs=0.001)

    def test_weighted_score_without_decay(self):
        """Test weighted score equals score when no decay"""
        scorer = NTEEScorer(enable_time_decay=False)

        result = scorer.score_alignment(
            profile_codes=["B25"],
            foundation_codes=["B25"]
        )

        # No decay = weighted_score should equal score
        assert result.weighted_score == result.score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
