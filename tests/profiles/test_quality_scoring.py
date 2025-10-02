"""
Task 18: Test Data Quality Scoring System

Comprehensive tests for profile and opportunity quality scoring.

Tests:
1. BMF data quality scoring
2. Form 990 data quality scoring
3. Tool 25 data quality scoring
4. Tool 2 data quality scoring
5. Overall profile quality calculation
6. Funding opportunity scoring
7. Networking opportunity scoring
8. Data completeness validation
"""

import logging
from src.profiles.quality_scoring import (
    ProfileQualityScorer,
    OpportunityQualityScorer,
    DataCompletenessValidator,
    QualityRating,
    QualityScore
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def print_section(title: str):
    """Print section header"""
    print("\n" + "="*60)
    print(title)
    print("="*60 + "\n")

def print_quality_score(score: QualityScore, label: str):
    """Print quality score details"""
    print(f"{label}:")
    print(f"  Overall Score: {score.overall_score:.2f}")
    print(f"  Rating: {score.rating.value}")

    if score.component_scores:
        print(f"  Component Scores:")
        for component, value in score.component_scores.items():
            print(f"    {component}: {value:.2f}")

    if score.confidence_level is not None:
        print(f"  Confidence Level: {score.confidence_level:.2f}")

    if score.missing_fields:
        print(f"  Missing Fields: {len(score.missing_fields)}")
        for field in score.missing_fields[:5]:  # Show first 5
            print(f"    - {field}")

    if score.validation_errors:
        print(f"  Validation Errors:")
        for error in score.validation_errors:
            print(f"    - {error}")

    if score.recommendations:
        print(f"  Recommendations:")
        for rec in score.recommendations:
            print(f"    - {rec}")

    print()

def test_bmf_quality_scoring():
    """Test 1: BMF Data Quality Scoring"""
    print_section("TEST 1: BMF Data Quality Scoring")

    scorer = ProfileQualityScorer()

    # Test Case 1a: Complete BMF data
    complete_bmf = {
        'ein': '208295721',
        'name': 'UPMC',
        'state': 'PA',
        'ntee_code': 'E22',
        'city': 'Pittsburgh',
        'address': '600 Grant Street'
    }

    score = scorer.score_bmf_data(complete_bmf)
    print_quality_score(score, "Complete BMF Data")

    assert score.overall_score >= 0.90, "Complete data should score >=0.90"
    assert score.rating == QualityRating.EXCELLENT, "Complete data should be EXCELLENT"
    print("[OK] Complete BMF data scores EXCELLENT")

    # Test Case 1b: BMF data without NTEE code (35% of orgs)
    no_ntee_bmf = {
        'ein': '350868122',
        'name': 'Lilly Endowment Inc',
        'state': 'IN'
    }

    score = scorer.score_bmf_data(no_ntee_bmf)
    print_quality_score(score, "BMF Data Without NTEE Code")

    assert score.overall_score >= 0.75, "Data without NTEE should still score >=0.75"
    assert "NTEE code missing" in str(score.recommendations), "Should recommend NTEE code"
    print("[OK] BMF without NTEE code still scores GOOD")

    # Test Case 1c: Incomplete BMF data
    incomplete_bmf = {
        'ein': '123456789'
    }

    score = scorer.score_bmf_data(incomplete_bmf)
    print_quality_score(score, "Incomplete BMF Data")

    assert score.overall_score < 0.50, "Incomplete data should score <0.50"
    assert score.rating == QualityRating.POOR, "Incomplete data should be POOR"
    assert len(score.validation_errors) > 0, "Should have validation errors"
    print("[OK] Incomplete BMF data scores POOR with errors")

def test_form_990_quality_scoring():
    """Test 2: Form 990 Data Quality Scoring"""
    print_section("TEST 2: Form 990 Data Quality Scoring")

    scorer = ProfileQualityScorer()

    # Test Case 2a: Complete Form 990 data
    complete_990 = {
        'ein': '208295721',
        'tax_year': 2024,
        'totrevenue': 22568515184,
        'totfuncexpns': 22671786620,
        'totassetsend': 12455585375,
        'totliabend': 8234567890,
        'totnetassetend': 4221017485,
        'topempcompexpens': 12345678,
        'numemps': 92000,
        'numvols': 5000
    }

    score = scorer.score_form_990(complete_990)
    print_quality_score(score, "Complete Form 990 Data")

    assert score.overall_score >= 0.90, "Complete 990 should score >=0.90"
    assert score.rating == QualityRating.EXCELLENT, "Complete 990 should be EXCELLENT"
    print("[OK] Complete Form 990 scores EXCELLENT")

    # Test Case 2b: Minimal Form 990 (critical fields only)
    minimal_990 = {
        'ein': '350868122',
        'totrevenue': 1000000,
        'totfuncexpns': 950000,
        'totassetsend': 2000000
    }

    score = scorer.score_form_990(minimal_990)
    print_quality_score(score, "Minimal Form 990 Data")

    assert score.overall_score >= 0.50, "Minimal 990 with critical fields should score >=0.50"
    print("[OK] Minimal Form 990 with critical fields scores FAIR+")

    # Test Case 2c: Form 990 with missing critical data
    incomplete_990 = {
        'ein': '123456789',
        'tax_year': 2024
    }

    score = scorer.score_form_990(incomplete_990)
    print_quality_score(score, "Incomplete Form 990 Data")

    assert score.overall_score < 0.50, "Incomplete 990 should score <0.50"
    assert score.rating == QualityRating.POOR, "Incomplete 990 should be POOR"
    print("[OK] Incomplete Form 990 scores POOR")

    # Test Case 2d: Negative operating margin
    negative_margin_990 = {
        'ein': '999999999',
        'totrevenue': 1000000,
        'totfuncexpns': 1200000,  # Expenses > Revenue
        'totassetsend': 500000
    }

    score = scorer.score_form_990(negative_margin_990)
    print_quality_score(score, "Form 990 with Negative Margin")

    assert any('negative' in r.lower() for r in score.recommendations), "Should flag negative margin"
    print("[OK] Negative operating margin flagged in recommendations")

def test_tool25_quality_scoring():
    """Test 3: Tool 25 Data Quality Scoring"""
    print_section("TEST 3: Tool 25 Data Quality Scoring")

    scorer = ProfileQualityScorer()

    # Test Case 3a: High-confidence Tool 25 data
    high_confidence_tool25 = {
        'mission_statement': {'text': 'Sample mission', 'confidence': 0.85},
        'contact_info': {'phone': '555-1234', 'email': 'info@org.org', 'confidence': 0.90},
        'leadership': {'ceo': 'John Doe', 'confidence': 0.75},
        'programs': {'count': 5, 'confidence': 0.70},
        'achievements': {'text': 'Sample achievements', 'confidence': 0.65}
    }

    score = scorer.score_tool25_data(high_confidence_tool25)
    print_quality_score(score, "High-Confidence Tool 25 Data")

    assert score.overall_score >= 0.70, "High-confidence Tool 25 should score >=0.70"
    assert score.confidence_level >= 0.75, "Average confidence should be >=0.75"
    print("[OK] High-confidence Tool 25 data scores GOOD+")

    # Test Case 3b: Low-confidence Tool 25 data
    low_confidence_tool25 = {
        'mission_statement': {'text': 'Uncertain mission', 'confidence': 0.45},
        'contact_info': {'phone': '555-0000', 'confidence': 0.50}
    }

    score = scorer.score_tool25_data(low_confidence_tool25)
    print_quality_score(score, "Low-Confidence Tool 25 Data")

    assert score.confidence_level < 0.60, "Average confidence should be <0.60"
    assert any('low average confidence' in r.lower() for r in score.recommendations), "Should recommend verification"
    print("[OK] Low-confidence Tool 25 data flagged for verification")

    # Test Case 3c: No Tool 25 data
    score = scorer.score_tool25_data(None)
    print_quality_score(score, "No Tool 25 Data")

    assert score.overall_score == 0.0, "No data should score 0.0"
    assert score.rating == QualityRating.POOR, "No data should be POOR"
    print("[OK] Missing Tool 25 data handled gracefully")

def test_tool2_quality_scoring():
    """Test 4: Tool 2 Data Quality Scoring"""
    print_section("TEST 4: Tool 2 Data Quality Scoring")

    scorer = ProfileQualityScorer()

    # Test Case 4a: Complete Tool 2 analysis
    complete_tool2 = {
        'strategic_positioning': 'Strong educational focus',
        'competitive_advantages': ['Large endowment', 'Strong brand'],
        'organizational_strengths': ['Financial health', 'Board expertise'],
        'grant_readiness': 0.85,
        'recommendations': ['Focus on major gifts', 'Expand foundation relationships']
    }

    score = scorer.score_tool2_data(complete_tool2)
    print_quality_score(score, "Complete Tool 2 Analysis")

    assert score.overall_score >= 0.80, "Complete Tool 2 should score >=0.80"
    assert score.rating == QualityRating.EXCELLENT, "Complete Tool 2 should be EXCELLENT"
    print("[OK] Complete Tool 2 analysis scores EXCELLENT")

    # Test Case 4b: Partial Tool 2 analysis
    partial_tool2 = {
        'strategic_positioning': 'Moderate focus',
        'grant_readiness': 0.60
    }

    score = scorer.score_tool2_data(partial_tool2)
    print_quality_score(score, "Partial Tool 2 Analysis")

    assert score.overall_score < 0.80, "Partial Tool 2 should score <0.80"
    print("[OK] Partial Tool 2 analysis scores appropriately")

    # Test Case 4c: No Tool 2 data (optional)
    score = scorer.score_tool2_data(None)
    print_quality_score(score, "No Tool 2 Analysis")

    assert score.overall_score == 0.0, "No Tool 2 should score 0.0"
    assert score.rating == QualityRating.FAIR, "No Tool 2 should be FAIR (optional)"
    print("[OK] Missing Tool 2 handled as optional")

def test_overall_profile_quality():
    """Test 5: Overall Profile Quality Calculation"""
    print_section("TEST 5: Overall Profile Quality Calculation")

    scorer = ProfileQualityScorer()

    # Test Case 5a: Excellent profile (all sources, high quality)
    excellent_bmf = {
        'ein': '208295721',
        'name': 'UPMC',
        'state': 'PA',
        'ntee_code': 'E22',
        'city': 'Pittsburgh',
        'address': '600 Grant Street'
    }

    excellent_990 = {
        'totrevenue': 22568515184,
        'totfuncexpns': 21000000000,  # Lower expenses for positive margin
        'totassetsend': 12455585375,
        'totliabend': 8234567890,
        'totnetassetend': 4221017485,
        'tax_year': 2024,
        'topempcompexpens': 12345678,
        'numemps': 92000,
        'numvols': 5000
    }

    excellent_tool25 = {
        'mission_statement': {'text': 'Sample mission', 'confidence': 0.85},
        'contact_info': {'phone': '555-1234', 'confidence': 0.90},
        'leadership': {'ceo': 'John Doe', 'confidence': 0.80},
        'programs': {'count': 5, 'confidence': 0.75},
        'achievements': {'text': 'Awards and recognition', 'confidence': 0.70},
        'initiatives': {'text': 'Current initiatives', 'confidence': 0.75},
        'partnerships': {'text': 'Key partnerships', 'confidence': 0.80}
    }

    excellent_tool2 = {
        'strategic_positioning': 'Strong position',
        'competitive_advantages': ['Large endowment', 'Strong brand'],
        'organizational_strengths': ['Financial health', 'Board expertise'],
        'grant_readiness': 0.90,
        'recommendations': ['Focus on major gifts']
    }

    score = scorer.calculate_profile_quality(
        excellent_bmf,
        excellent_990,
        excellent_tool25,
        excellent_tool2
    )

    print_quality_score(score, "Excellent Profile (All Sources)")

    assert score.overall_score >= 0.85, "Excellent profile should score >=0.85"
    assert score.rating == QualityRating.EXCELLENT, "Should be rated EXCELLENT"
    print(f"[OK] Excellent profile scores {score.overall_score:.2f} (EXCELLENT)")

    # Test Case 5b: Good profile (BMF + 990 only)
    # For a "GOOD" score (0.70-0.84) without Tool 25/Tool 2, we need:
    # BMF (20%) + 990 (35%) to carry most weight
    # Target: BMF=1.0, 990=1.0 -> (1.0*0.20)+(1.0*0.35)+(0.0*0.25)+(0.0*0.20) = 0.55
    # This still only gives 0.55, so "GOOD" requires at least Tool 25 or Tool 2
    # Let's adjust test expectations for realistic scenario
    good_bmf = {
        'ein': '350868122',
        'name': 'Lilly Endowment',
        'state': 'IN',
        'ntee_code': 'T20',
        'city': 'Indianapolis',
        'address': '2801 North Meridian Street'
    }

    good_990 = {
        'totrevenue': 5000000,
        'totfuncexpns': 4750000,  # Positive 5% margin
        'totassetsend': 10000000,
        'totliabend': 2000000,
        'totnetassetend': 8000000,
        'tax_year': 2024
    }

    # Add Tool 25 data to reach GOOD threshold
    good_tool25 = {
        'mission_statement': {'text': 'Sample mission', 'confidence': 0.80},
        'contact_info': {'phone': '555-1234', 'confidence': 0.85},
        'leadership': {'ceo': 'Jane Doe', 'confidence': 0.75},
        'programs': {'count': 3, 'confidence': 0.75},
        'achievements': {'text': 'Sample achievements', 'confidence': 0.70}
    }

    score = scorer.calculate_profile_quality(
        good_bmf,
        good_990,
        good_tool25,  # Include Tool 25 to reach GOOD threshold
        None   # No Tool 2
    )

    print_quality_score(score, "Good Profile (BMF + 990 + Tool 25)")

    assert 0.70 <= score.overall_score < 0.85, "Good profile should score 0.70-0.84"
    assert score.rating == QualityRating.GOOD, "Should be rated GOOD"
    print(f"[OK] Good profile scores {score.overall_score:.2f} (GOOD)")

    # Test Case 5c: Fair profile (BMF only)
    fair_bmf = {
        'ein': '123456789',
        'name': 'Sample Org',
        'state': 'VA'
    }

    score = scorer.calculate_profile_quality(
        fair_bmf,
        None,  # No 990
        None,  # No Tool 25
        None   # No Tool 2
    )

    print_quality_score(score, "Fair Profile (BMF Only)")

    assert score.overall_score < 0.50, "Fair profile should score <0.50"
    print(f"[OK] Fair profile scores {score.overall_score:.2f} (POOR-FAIR)")

def test_funding_opportunity_scoring():
    """Test 6: Funding Opportunity Scoring"""
    print_section("TEST 6: Funding Opportunity Scoring")

    scorer = OpportunityQualityScorer()

    # Profile: Education nonprofit in VA with $5M budget
    profile = {
        'ntee_codes': ['P20', 'B25'],
        'geographic_scope': {'states': ['VA', 'MD', 'DC']},
        'annual_budget': 5000000
    }

    # Test Case 6a: Excellent match foundation
    excellent_foundation = {
        'ein': '540012345',
        'name': 'Education Excellence Foundation',
        'state': 'VA',
        'funded_ntee_codes': ['P20', 'P30'],
        'avg_grant_size': 750000,  # 15% of profile budget
        'similar_recipient_count': 8,
        'accepts_applications': True,
        'next_deadline': '2025-12-31',
        'nationwide_scope': False
    }

    score = scorer.score_funding_opportunity(profile, excellent_foundation)
    print_quality_score(score, "Excellent Match Foundation")

    assert score.overall_score >= 0.80, "Excellent match should score >=0.80"
    assert score.rating == QualityRating.EXCELLENT, "Should be rated EXCELLENT"
    print(f"[OK] Excellent foundation match scores {score.overall_score:.2f}")

    # Test Case 6b: Good match foundation (different state)
    good_foundation = {
        'ein': '540098765',
        'name': 'National Education Fund',
        'state': 'NY',
        'funded_ntee_codes': ['P20'],
        'avg_grant_size': 500000,
        'similar_recipient_count': 5,
        'accepts_applications': True,
        'nationwide_scope': True
    }

    score = scorer.score_funding_opportunity(profile, good_foundation)
    print_quality_score(score, "Good Match Foundation")

    assert 0.65 <= score.overall_score < 0.80, "Good match should score 0.65-0.79"
    print(f"[OK] Good foundation match scores {score.overall_score:.2f}")

    # Test Case 6c: Poor match foundation
    poor_foundation = {
        'ein': '540011111',
        'name': 'Arts Foundation',
        'state': 'CA',
        'funded_ntee_codes': ['A20', 'A30'],  # Arts, not education
        'avg_grant_size': 50000,  # Too small
        'similar_recipient_count': 0,
        'accepts_applications': False
    }

    score = scorer.score_funding_opportunity(profile, poor_foundation)
    print_quality_score(score, "Poor Match Foundation")

    assert score.overall_score < 0.50, "Poor match should score <0.50"
    assert score.rating == QualityRating.POOR, "Should be rated POOR"
    print(f"[OK] Poor foundation match scores {score.overall_score:.2f}")

def test_networking_opportunity_scoring():
    """Test 7: Networking Opportunity Scoring"""
    print_section("TEST 7: Networking Opportunity Scoring")

    scorer = OpportunityQualityScorer()

    # Profile: Education nonprofit in VA with $5M budget
    profile = {
        'ntee_codes': ['P20', 'B25'],
        'geographic_scope': {'states': ['VA']},
        'annual_budget': 5000000
    }

    # Test Case 7a: High-value peer (shared funders + board)
    high_value_peer = {
        'ein': '510012345',
        'name': 'Similar Education Org',
        'ntee_codes': ['P20', 'P30'],
        'state': 'VA',
        'annual_budget': 4500000,
        'shared_board_members': 3,
        'shared_funders': 12
    }

    score = scorer.score_networking_opportunity(profile, high_value_peer)
    print_quality_score(score, "High-Value Peer Organization")

    assert score.overall_score >= 0.70, "High-value peer should score >=0.70"
    assert score.rating == QualityRating.HIGH, "Should be rated HIGH"
    print(f"[OK] High-value peer scores {score.overall_score:.2f}")

    # Test Case 7b: Medium-value peer (shared mission, moderate connections)
    medium_value_peer = {
        'ein': '510098765',
        'name': 'Related Education Org',
        'ntee_codes': ['P20'],
        'state': 'VA',
        'annual_budget': 3000000,
        'shared_board_members': 1,
        'shared_funders': 7
    }

    score = scorer.score_networking_opportunity(profile, medium_value_peer)
    print_quality_score(score, "Medium-Value Peer Organization")

    assert 0.50 <= score.overall_score < 0.70, "Medium-value peer should score 0.50-0.69"
    assert score.rating == QualityRating.MEDIUM, "Should be rated MEDIUM"
    print(f"[OK] Medium-value peer scores {score.overall_score:.2f}")

    # Test Case 7c: Low-value peer (different mission, no connections)
    low_value_peer = {
        'ein': '510011111',
        'name': 'Arts Organization',
        'ntee_codes': ['A20'],
        'state': 'CA',
        'annual_budget': 500000,
        'shared_board_members': 0,
        'shared_funders': 0
    }

    score = scorer.score_networking_opportunity(profile, low_value_peer)
    print_quality_score(score, "Low-Value Peer Organization")

    assert score.overall_score < 0.50, "Low-value peer should score <0.50"
    assert score.rating == QualityRating.LOW, "Should be rated LOW"
    print(f"[OK] Low-value peer scores {score.overall_score:.2f}")

def test_data_completeness_validation():
    """Test 8: Data Completeness Validation"""
    print_section("TEST 8: Data Completeness Validation")

    validator = DataCompletenessValidator()

    # Test Case 8a: Complete profile (all sources)
    complete_bmf = {'ein': '123', 'name': 'Test', 'state': 'VA'}
    complete_990 = {'totrevenue': 1000000, 'totfuncexpns': 950000}
    complete_tool25 = {'mission_statement': 'Test', 'contact_info': 'Test'}
    complete_tool2 = {'strategic_positioning': 'Test'}

    result = validator.validate_profile_completeness(
        complete_bmf,
        complete_990,
        complete_tool25,
        complete_tool2
    )

    print("Complete Profile:")
    print(f"  Sources Present: {result['sources_present']}")
    print(f"  Sources Missing: {result['sources_missing']}")
    print(f"  Overall Completeness: {result['overall_completeness']:.2f}")
    print(f"  Recommendations:")
    for rec in result['recommendations']:
        print(f"    - {rec}")
    print()

    assert result['overall_completeness'] == 1.0, "Complete profile should be 1.0"
    assert len(result['sources_present']) == 4, "Should have 4 sources"
    assert len(result['sources_missing']) == 0, "Should have no missing sources"
    print("[OK] Complete profile validation passed")

    # Test Case 8b: Partial profile (BMF + 990 only)
    result = validator.validate_profile_completeness(
        complete_bmf,
        complete_990,
        None,
        None
    )

    print("Partial Profile (BMF + 990):")
    print(f"  Sources Present: {result['sources_present']}")
    print(f"  Sources Missing: {result['sources_missing']}")
    print(f"  Overall Completeness: {result['overall_completeness']:.2f}")
    print(f"  Recommendations:")
    for rec in result['recommendations']:
        print(f"    - {rec}")
    print()

    expected_completeness = 0.20 + 0.35  # BMF + 990 weights
    assert abs(result['overall_completeness'] - expected_completeness) < 0.01, "Should be 0.55"
    assert 'tool_25' in result['sources_missing'], "Should flag Tool 25 missing"
    print("[OK] Partial profile validation passed")

    # Test Case 8c: Minimal profile (BMF only)
    result = validator.validate_profile_completeness(
        complete_bmf,
        None,
        None,
        None
    )

    print("Minimal Profile (BMF Only):")
    print(f"  Sources Present: {result['sources_present']}")
    print(f"  Sources Missing: {result['sources_missing']}")
    print(f"  Overall Completeness: {result['overall_completeness']:.2f}")
    print(f"  Recommendations:")
    for rec in result['recommendations']:
        print(f"    - {rec}")
    print()

    assert result['overall_completeness'] == 0.20, "Should be 0.20 (BMF only)"
    assert 'form_990' in result['sources_missing'], "Should flag Form 990 missing"
    assert any('HIGH PRIORITY' in r for r in result['recommendations']), "Should prioritize Form 990"
    print("[OK] Minimal profile validation passed")

def main():
    """Run all quality scoring tests"""
    print("\n" + "="*60)
    print("TASK 18: Data Quality Scoring System Tests")
    print("Comprehensive Quality Scoring Across All Sources")
    print("="*60)

    # Run all tests
    test_bmf_quality_scoring()
    test_form_990_quality_scoring()
    test_tool25_quality_scoring()
    test_tool2_quality_scoring()
    test_overall_profile_quality()
    test_funding_opportunity_scoring()
    test_networking_opportunity_scoring()
    test_data_completeness_validation()

    # Summary
    print_section("TEST SUMMARY")
    print("[PASS] BMF data quality scoring")
    print("[PASS] Form 990 data quality scoring")
    print("[PASS] Tool 25 web intelligence quality scoring")
    print("[PASS] Tool 2 AI analysis quality scoring")
    print("[PASS] Overall profile quality calculation")
    print("[PASS] Funding opportunity scoring (foundations)")
    print("[PASS] Networking opportunity scoring (peer nonprofits)")
    print("[PASS] Data completeness validation")
    print()
    print("[OK] Task 18 Complete - Quality scoring system operational!")
    print("[OK] Features:")
    print("  - Profile quality: BMF(20%) + 990(35%) + Tool25(25%) + Tool2(20%)")
    print("  - Funding opportunity: Mission(30%) + Geo(20%) + Grant(25%) + Recipients(15%) + Feasibility(10%)")
    print("  - Networking opportunity: Mission(25%) + Board(25%) + Funders(30%) + Collab(20%)")
    print("  - Quality ratings: EXCELLENT, GOOD, FAIR, POOR (profiles/funding)")
    print("  - Quality ratings: HIGH, MEDIUM, LOW (networking)")
    print("  - Comprehensive recommendations for each score")
    print()
    print("[OK] Ready for Task 19: Update profile API endpoints to use tools")

if __name__ == "__main__":
    main()
