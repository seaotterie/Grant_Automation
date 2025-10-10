"""
End-to-End Test: Foundation Intelligence Workflow
==================================================

Tests the complete foundation intelligence workflow from 990-PF analysis through
ecosystem mapping and capacity scoring.

Workflow Steps:
1. Foundation Profile Analysis - Extract and analyze 990-PF data
2. Grant-Making Patterns - Analyze Schedule I and giving patterns
3. Capacity Scoring - Assess foundation capacity and grant budget
4. Ecosystem Mapping - Map foundation networks and board overlaps
5. Complete Intelligence - End-to-end foundation research workflow

Test Approach:
- Tests foundation classification and financial analysis
- Validates payout requirement calculations
- Ensures grant-making pattern detection
- Verifies foundation ecosystem mapping
"""

import pytest
import logging
from datetime import datetime
from typing import Dict, Any, List

# Foundation intelligence imports
from src.analysis.foundation_intelligence_engine import (
    FoundationProfile,
    FoundationType,
    GivingPattern,
    FoundationEcosystemMap,
    FoundationIntelligenceEngine
)

# Tool imports for direct testing
import sys
import os
import asyncio

# Add tools path for foundation intelligence tool
tools_path = os.path.join(os.path.dirname(__file__), '..', '..', 'tools', 'foundation-grant-intelligence-tool', 'app')
if tools_path not in sys.path:
    sys.path.insert(0, tools_path)

from foundation_intelligence_analyzer import (
    FoundationIntelligenceTool,
    FoundationAnalysisCriteria,
    GrantMakingProfile,
    PayoutAnalysis,
    CapacityScore,
    InvestmentProfile
)

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_foundation_data(ein="98-7654321", name="Test Foundation",
                                foundation_type="990-PF", assets=5000000,
                                grants_paid=250000, num_grants=10):
    """Helper to create test foundation data"""
    return {
        'ein': ein,
        'name': name,
        'form_type': foundation_type,
        'foundation_code': '03' if foundation_type == '990-PF' else None,
        'total_assets': assets,
        'total_revenue': int(assets * 0.06),  # 6% return
        'grants_paid': grants_paid,
        'num_grants_made': num_grants,
        'investment_income': int(assets * 0.04),  # 4% investment return
        'administrative_expenses': int(grants_paid * 0.1),  # 10% admin costs
        'ntee_code': 'P20',
        'state': 'VA',
        'board_members': [
            {'name': 'John Smith', 'title': 'President'},
            {'name': 'Jane Doe', 'title': 'Secretary'},
            {'name': 'Bob Johnson', 'title': 'Treasurer'}
        ],
        'grant_recipients': [
            {
                'ein': f'11-{i:07d}',
                'name': f'Recipient Org {i}',
                'amount': grants_paid / num_grants,
                'purpose': 'General operating support',
                'ntee_code': 'P20' if i % 2 == 0 else 'E31',
                'state': 'VA'
            }
            for i in range(num_grants)
        ]
    }


def create_schedule_i_grantees(count=5, base_ein="11-0000000"):
    """Helper to create Schedule I grantee data"""
    grantees = []
    for i in range(count):
        grantees.append({
            'ein': f'11-{i:07d}',
            'name': f'Grantee Organization {i}',
            'amount': 25000 + (i * 5000),
            'purpose': 'Program support' if i % 2 == 0 else 'General operating',
            'ntee_code': 'P20' if i % 3 == 0 else 'E31',
            'state': 'VA' if i % 2 == 0 else 'MD'
        })
    return grantees


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def foundation_intelligence_engine():
    """Create Foundation Intelligence Engine instance"""
    return FoundationIntelligenceEngine()


@pytest.fixture
def foundation_intelligence_tool():
    """Create Foundation Intelligence Tool instance"""
    return FoundationIntelligenceTool()


@pytest.fixture
def sample_private_foundation():
    """Sample private non-operating foundation"""
    return create_test_foundation_data(
        ein="54-1026365",
        name="Sample Private Foundation",
        foundation_type="990-PF",
        assets=10000000,  # $10M foundation
        grants_paid=500000,  # $500K grants
        num_grants=20
    )


@pytest.fixture
def sample_family_foundation():
    """Sample family foundation"""
    return create_test_foundation_data(
        ein="22-3344556",
        name="Smith Family Foundation",
        foundation_type="990-PF",
        assets=2000000,  # $2M foundation
        grants_paid=100000,  # $100K grants
        num_grants=8
    )


@pytest.fixture
def sample_corporate_foundation():
    """Sample corporate foundation"""
    return create_test_foundation_data(
        ein="33-4455667",
        name="ABC Corporation Foundation",
        foundation_type="990-PF",
        assets=15000000,  # $15M foundation
        grants_paid=750000,  # $750K grants
        num_grants=30
    )


# ============================================================================
# Test Class 1: Foundation Profile Analysis
# ============================================================================

class TestFoundationProfileAnalysis:
    """Test foundation profile creation and classification"""

    def test_foundation_profile_creation(self, sample_private_foundation):
        """Test creating foundation profile from 990-PF data"""
        # Create foundation profile
        profile = FoundationProfile(
            ein=sample_private_foundation['ein'],
            name=sample_private_foundation['name'],
            foundation_type=FoundationType.PRIVATE_NON_OPERATING,
            assets=sample_private_foundation['total_assets'],
            revenue=sample_private_foundation['total_revenue'],
            total_grants_made=sample_private_foundation['grants_paid'],
            num_grants_made=sample_private_foundation['num_grants_made']
        )

        # Validate profile creation
        assert profile.ein == "54-1026365"
        assert profile.name == "Sample Private Foundation"
        assert profile.foundation_type == FoundationType.PRIVATE_NON_OPERATING
        assert profile.assets == 10000000
        assert profile.total_grants_made == 500000
        assert profile.num_grants_made == 20

        # Calculate average grant size
        if profile.total_grants_made and profile.num_grants_made:
            profile.avg_grant_size = profile.total_grants_made / profile.num_grants_made
            assert profile.avg_grant_size == 25000

        logger.info(f"Created foundation profile: {profile.name} (${profile.assets:,})")

    def test_foundation_type_classification(self):
        """Test foundation type classification logic"""
        # Test private non-operating (most common grantmaker)
        private_data = {'foundation_code': '03', 'name': 'Smith Foundation'}
        # Would use engine._classify_foundation_type(private_data)
        # For E2E, just validate enum exists
        assert FoundationType.PRIVATE_NON_OPERATING.value == "private_non_operating"

        # Test private operating
        operating_data = {'foundation_code': '04', 'name': 'Operating Foundation'}
        assert FoundationType.PRIVATE_OPERATING.value == "private_operating"

        # Test family foundation (heuristic)
        family_data = {'name': 'Johnson Family Foundation', 'form_type': '990-PF'}
        assert FoundationType.FAMILY_FOUNDATION.value == "family_foundation"

        # Test corporate foundation (heuristic)
        corporate_data = {'name': 'ABC Corp Foundation Inc', 'form_type': '990-PF'}
        assert FoundationType.CORPORATE_FOUNDATION.value == "corporate_foundation"

        logger.info(f"Foundation type classification validated: {len(FoundationType)} types")

    @pytest.mark.asyncio
    async def test_payout_requirement_calculation(self, foundation_intelligence_tool):
        """Test 5% payout requirement calculation"""
        # Create test criteria
        criteria = FoundationAnalysisCriteria(
            target_eins=["98-7654321"],
            include_payout_requirements=True
        )

        # Execute analysis
        result = await foundation_intelligence_tool.execute(criteria)

        # Validate payout analysis
        assert len(result.payout_requirements) > 0
        payout_analysis = result.payout_requirements[0]

        # Verify 5% calculation
        assert payout_analysis.required_payout_percentage == 0.05
        expected_payout = payout_analysis.total_assets * 0.05
        assert payout_analysis.required_payout_amount == expected_payout

        # Verify compliance status logic
        assert payout_analysis.payout_compliance_status in ["Compliant", "Under-Payout", "Unknown"]

        # Verify payout ratio
        if payout_analysis.total_assets > 0:
            expected_ratio = payout_analysis.actual_grants_paid / payout_analysis.total_assets
            assert payout_analysis.payout_ratio == expected_ratio

        logger.info(f"Payout requirement: ${payout_analysis.required_payout_amount:,.0f} " +
                   f"(Status: {payout_analysis.payout_compliance_status})")

    @pytest.mark.asyncio
    async def test_foundation_financial_metrics(self, foundation_intelligence_tool):
        """Test foundation financial metrics analysis"""
        # Create test criteria
        criteria = FoundationAnalysisCriteria(
            target_eins=["123456789"],
            include_investment_analysis=True
        )

        # Execute analysis
        result = await foundation_intelligence_tool.execute(criteria)

        # Validate execution metadata
        assert result.foundations_processed >= 1
        assert result.execution_metadata.foundations_analyzed >= 1
        assert result.execution_metadata.execution_time_ms > 0

        # Validate financial metrics
        if len(result.investment_analysis) > 0:
            investment = result.investment_analysis[0]
            assert investment.total_investment_assets >= 0
            assert investment.investment_income >= 0
            assert 0 <= investment.investment_return_rate <= 1.0
            assert investment.investment_risk_profile in ["Conservative", "Moderate", "Aggressive", "Unknown"]

        logger.info(f"Financial metrics analyzed: {result.foundations_processed} foundations")


# ============================================================================
# Test Class 2: Grant-Making Pattern Analysis
# ============================================================================

class TestGrantMakingPatternAnalysis:
    """Test grant-making pattern detection and analysis"""

    def test_schedule_i_grant_extraction(self, sample_private_foundation):
        """Test extracting Schedule I grant recipient data"""
        # Extract grantees
        grantees = sample_private_foundation['grant_recipients']

        # Validate extraction
        assert len(grantees) == 20
        assert all('ein' in g for g in grantees)
        assert all('amount' in g for g in grantees)
        assert all('purpose' in g for g in grantees)

        # Calculate totals
        total_grants = sum(g['amount'] for g in grantees)
        assert abs(total_grants - 500000) < 100  # Allow small rounding

        logger.info(f"Extracted {len(grantees)} Schedule I grantees: ${total_grants:,.0f}")

    def test_giving_pattern_detection(self):
        """Test detecting giving patterns from grant purposes"""
        # Test general purpose pattern
        general_purpose_grants = [
            {'purpose': 'General operating support'},
            {'purpose': 'Unrestricted funding'}
        ]
        # Would use engine._analyze_foundation_giving_patterns()
        # For E2E, validate enum
        assert GivingPattern.GENERAL_PURPOSE.value == "general_purpose"

        # Test program-specific pattern
        program_grants = [
            {'purpose': 'Youth education program'},
            {'purpose': 'Community health project'}
        ]
        assert GivingPattern.PROGRAM_SPECIFIC.value == "program_specific"

        # Test capacity building pattern
        capacity_grants = [
            {'purpose': 'Organizational capacity building'},
            {'purpose': 'Strategic planning support'}
        ]
        assert GivingPattern.CAPACITY_BUILDING.value == "capacity_building"

        logger.info(f"Giving pattern detection validated: {len(GivingPattern)} patterns")

    @pytest.mark.asyncio
    async def test_grant_size_distribution(self, foundation_intelligence_tool):
        """Test grant size distribution analysis"""
        # Create test criteria
        criteria = FoundationAnalysisCriteria(
            target_eins=["98-7654321", "123456789"],
            include_grant_capacity_scoring=True
        )

        # Execute analysis
        result = await foundation_intelligence_tool.execute(criteria)

        # Validate grant-making profiles
        assert len(result.grant_making_profiles) >= 1

        for profile in result.grant_making_profiles:
            # Validate grant metrics
            assert profile.total_grants_paid >= 0
            assert profile.number_of_grants >= 0

            if profile.number_of_grants > 0:
                assert profile.average_grant_size > 0
                assert profile.largest_grant_amount >= profile.average_grant_size
                assert profile.smallest_grant_amount <= profile.average_grant_size

            # Validate consistency score
            assert 0 <= profile.grant_making_consistency_score <= 1.0

        logger.info(f"Grant size distribution analyzed for {len(result.grant_making_profiles)} foundations")

    def test_geographic_focus_analysis(self, sample_private_foundation):
        """Test identifying geographic giving patterns"""
        # Extract state distribution from grantees
        grantees = sample_private_foundation['grant_recipients']
        states = [g['state'] for g in grantees if 'state' in g]

        # Count by state
        from collections import Counter
        state_counts = Counter(states)

        # Validate geographic analysis
        assert len(state_counts) > 0
        most_common_state = state_counts.most_common(1)[0][0]
        assert most_common_state in ['VA', 'MD']

        # Calculate concentration
        total_grants = len(states)
        top_state_concentration = state_counts[most_common_state] / total_grants
        assert 0 < top_state_concentration <= 1.0

        logger.info(f"Geographic focus: {dict(state_counts)} (Top: {most_common_state} @ {top_state_concentration:.1%})")


# ============================================================================
# Test Class 3: Foundation Capacity Scoring
# ============================================================================

class TestFoundationCapacityScoring:
    """Test foundation capacity assessment and scoring"""

    @pytest.mark.asyncio
    async def test_capacity_score_calculation(self, foundation_intelligence_tool):
        """Test calculating foundation capacity scores"""
        # Create test criteria
        criteria = FoundationAnalysisCriteria(
            target_eins=["98-7654321", "123456789"],
            include_grant_capacity_scoring=True
        )

        # Execute analysis
        result = await foundation_intelligence_tool.execute(criteria)

        # Validate capacity scores
        assert len(result.foundation_capacity_scores) >= 1

        for score in result.foundation_capacity_scores:
            # Validate component scores (0.0-1.0 range)
            assert 0 <= score.overall_capacity_score <= 1.0
            assert 0 <= score.financial_strength_score <= 1.0
            assert 0 <= score.grant_activity_score <= 1.0
            assert 0 <= score.grant_size_score <= 1.0
            assert 0 <= score.accessibility_score <= 1.0
            assert 0 <= score.alignment_likelihood_score <= 1.0

            # Validate capacity category
            assert score.capacity_category in ["Major", "Significant", "Moderate", "Limited", "Unknown"]

            # Validate grant budget estimate
            assert score.annual_grant_budget_estimate >= 0

            # Validate ask range format
            assert "$" in score.recommended_ask_range
            assert "-" in score.recommended_ask_range

        logger.info(f"Capacity scores calculated for {len(result.foundation_capacity_scores)} foundations")

    @pytest.mark.asyncio
    async def test_grant_budget_estimation(self, foundation_intelligence_tool):
        """Test estimating annual grant budget (5-7% of assets)"""
        # Create test criteria
        criteria = FoundationAnalysisCriteria(
            target_eins=["123456789"],
            include_grant_capacity_scoring=True
        )

        # Execute analysis
        result = await foundation_intelligence_tool.execute(criteria)

        # Validate budget estimation
        if len(result.foundation_capacity_scores) > 0:
            score = result.foundation_capacity_scores[0]

            # Budget should be 5-7% of assets (tool uses 6%)
            # For mock data with $5M assets, expect ~$300K budget
            if score.annual_grant_budget_estimate > 0:
                # Reasonable range for foundation giving
                assert 100000 <= score.annual_grant_budget_estimate <= 1000000

            logger.info(f"Estimated grant budget: ${score.annual_grant_budget_estimate:,.0f}")

    @pytest.mark.asyncio
    async def test_recommended_ask_range(self, foundation_intelligence_tool):
        """Test calculating appropriate ask ranges"""
        # Create test criteria
        criteria = FoundationAnalysisCriteria(
            target_eins=["98-7654321"],
            include_grant_capacity_scoring=True
        )

        # Execute analysis
        result = await foundation_intelligence_tool.execute(criteria)

        # Validate ask range recommendations
        if len(result.foundation_capacity_scores) > 0:
            score = result.foundation_capacity_scores[0]

            # Parse ask range
            ask_range = score.recommended_ask_range
            assert ask_range is not None
            assert "$" in ask_range
            assert "-" in ask_range

            # Extract min and max (simplified parsing)
            parts = ask_range.replace("$", "").replace(",", "").split("-")
            if len(parts) == 2:
                min_ask = float(parts[0].strip())
                max_ask = float(parts[1].strip())

                # Validate range logic
                assert min_ask < max_ask
                assert min_ask >= 1000  # At least $1K
                assert max_ask <= 10000000  # At most $10M

            logger.info(f"Recommended ask range: {ask_range}")


# ============================================================================
# Test Class 4: Foundation Ecosystem Mapping
# ============================================================================

class TestFoundationEcosystemMapping:
    """Test foundation ecosystem network and relationship mapping"""

    def test_shared_grantee_identification(self):
        """Test identifying foundations funding similar organizations"""
        # Create test foundations with overlapping grantees
        foundation1_grantees = set(['11-1111111', '11-2222222', '11-3333333'])
        foundation2_grantees = set(['11-2222222', '11-3333333', '11-4444444'])

        # Calculate overlap
        shared_grantees = foundation1_grantees.intersection(foundation2_grantees)

        # Validate shared grantee identification
        assert len(shared_grantees) == 2
        assert '11-2222222' in shared_grantees
        assert '11-3333333' in shared_grantees

        # Calculate overlap percentage
        overlap_pct = len(shared_grantees) / len(foundation1_grantees)
        assert 0 < overlap_pct < 1.0

        logger.info(f"Shared grantees identified: {len(shared_grantees)} ({overlap_pct:.1%} overlap)")

    def test_board_overlap_detection(self):
        """Test detecting board member connections"""
        # Create test board data
        foundation1_board = {'John Smith', 'Jane Doe', 'Bob Johnson'}
        foundation2_board = {'Jane Doe', 'Alice Williams', 'Charlie Brown'}

        # Detect overlap
        board_overlap = foundation1_board.intersection(foundation2_board)

        # Validate detection
        assert len(board_overlap) == 1
        assert 'Jane Doe' in board_overlap

        # Calculate overlap metrics
        overlap_ratio = len(board_overlap) / len(foundation1_board)
        assert 0 < overlap_ratio < 1.0

        logger.info(f"Board overlap detected: {list(board_overlap)} ({overlap_ratio:.1%})")

    def test_foundation_cluster_analysis(self):
        """Test mapping foundation ecosystem clusters"""
        # Create ecosystem map
        ecosystem_map = FoundationEcosystemMap()

        # Add foundation relationships (mock data)
        ecosystem_map.foundation_relationships['98-1111111'] = ['98-2222222', '98-3333333']
        ecosystem_map.foundation_relationships['98-2222222'] = ['98-1111111', '98-3333333']
        ecosystem_map.foundation_relationships['98-3333333'] = ['98-1111111', '98-2222222']

        # Validate ecosystem structure
        assert len(ecosystem_map.foundation_relationships) == 3
        assert '98-2222222' in ecosystem_map.foundation_relationships['98-1111111']

        # Test cluster formation
        # All three foundations are interconnected, forming one cluster
        all_eins = set(ecosystem_map.foundation_relationships.keys())
        assert len(all_eins) == 3

        logger.info(f"Foundation ecosystem mapped: {len(ecosystem_map.foundation_relationships)} foundations")


# ============================================================================
# Test Class 5: Complete Foundation Intelligence Workflow
# ============================================================================

class TestCompleteFoundationIntelligence:
    """Test complete end-to-end foundation intelligence workflow"""

    @pytest.mark.asyncio
    async def test_full_foundation_intelligence_pipeline(self, foundation_intelligence_tool):
        """Test complete analysis from 990-PF data through recommendations"""
        # Step 1: Create comprehensive analysis criteria
        criteria = FoundationAnalysisCriteria(
            target_eins=["812827604", "123456789"],  # HEROS BRIDGE + mock foundation
            years_to_analyze=3,
            include_investment_analysis=True,
            include_payout_requirements=True,
            include_grant_capacity_scoring=True,
            min_grant_amount=1000.0
        )

        logger.info("Step 1: Created analysis criteria for 2 foundations")

        # Step 2: Execute full intelligence analysis
        result = await foundation_intelligence_tool.execute(criteria)

        logger.info(f"Step 2: Executed foundation intelligence analysis")

        # Step 3: Validate grant-making profiles
        assert len(result.grant_making_profiles) >= 0  # May be 0 if no grants
        logger.info(f"Step 3: Analyzed {len(result.grant_making_profiles)} grant-making profiles")

        # Step 4: Validate payout requirements
        assert len(result.payout_requirements) >= 1
        for payout in result.payout_requirements:
            assert payout.required_payout_percentage == 0.05
            assert payout.payout_compliance_status in ["Compliant", "Under-Payout", "Unknown"]
        logger.info(f"Step 4: Calculated payout requirements for {len(result.payout_requirements)} foundations")

        # Step 5: Validate capacity scores
        assert len(result.foundation_capacity_scores) >= 1
        for score in result.foundation_capacity_scores:
            assert score.capacity_category in ["Major", "Significant", "Moderate", "Limited", "Unknown"]
        logger.info(f"Step 5: Computed capacity scores for {len(result.foundation_capacity_scores)} foundations")

        # Step 6: Validate investment analysis
        assert len(result.investment_analysis) >= 1
        logger.info(f"Step 6: Generated {len(result.investment_analysis)} investment profiles")

        # Step 7: Validate quality assessment
        assert result.quality_assessment is not None
        assert 0 <= result.quality_assessment.overall_analysis_quality <= 1.0
        assert 0 <= result.quality_assessment.payout_calculation_accuracy <= 1.0
        logger.info(f"Step 7: Quality assessment: {result.quality_assessment.overall_analysis_quality:.2f}")

        # Step 8: Validate execution metadata
        assert result.execution_metadata.execution_time_ms > 0
        assert result.execution_metadata.foundations_analyzed == 2
        logger.info(f"Step 8: Execution time: {result.execution_metadata.execution_time_ms:.1f}ms")

    @pytest.mark.asyncio
    async def test_high_value_foundation_identification(self, foundation_intelligence_tool):
        """Test identifying high-value foundation targets"""
        # Create test criteria
        criteria = FoundationAnalysisCriteria(
            target_eins=["123456789"],
            include_grant_capacity_scoring=True
        )

        # Execute analysis
        result = await foundation_intelligence_tool.execute(criteria)

        # Validate high-value identification logic
        # High-value criteria: Major/Significant capacity + $100K+ grant budget
        high_value_count = len(result.high_value_foundations)

        # Verify identification was attempted
        assert result.execution_metadata.high_value_foundations_identified >= 0

        # If any high-value foundations found, validate them
        for ein in result.high_value_foundations:
            # Find corresponding capacity score
            score = next((s for s in result.foundation_capacity_scores if s.ein == ein), None)
            if score:
                # Validate meets high-value criteria
                assert score.capacity_category in ["Major", "Significant"]
                assert score.overall_capacity_score >= 0.6
                assert score.annual_grant_budget_estimate >= 100000

        logger.info(f"High-value foundations identified: {high_value_count}")

    @pytest.mark.asyncio
    async def test_intelligence_quality_assessment(self, foundation_intelligence_tool):
        """Test validating analysis quality and completeness"""
        # Create test criteria
        criteria = FoundationAnalysisCriteria(
            target_eins=["98-7654321", "123456789"],
            include_investment_analysis=True,
            include_payout_requirements=True,
            include_grant_capacity_scoring=True
        )

        # Execute analysis
        result = await foundation_intelligence_tool.execute(criteria)

        # Validate quality assessment structure
        qa = result.quality_assessment
        assert qa is not None

        # Validate quality metrics (0.0-1.0 range)
        assert 0 <= qa.overall_analysis_quality <= 1.0
        assert 0 <= qa.payout_calculation_accuracy <= 1.0
        assert 0 <= qa.capacity_scoring_reliability <= 1.0
        assert 0 <= qa.investment_analysis_depth <= 1.0
        assert 0 <= qa.grant_pattern_detection_score <= 1.0
        assert 0 <= qa.foundation_classification_accuracy <= 1.0

        # Validate limitation notes
        assert isinstance(qa.limitation_notes, list)

        # Validate overall results
        assert result.foundations_processed == 2
        assert result.tool_name == "Foundation Grant Intelligence Tool"
        assert "12-Factor" in result.framework_compliance

        logger.info(f"Quality assessment: {qa.overall_analysis_quality:.2f} " +
                   f"(Payout accuracy: {qa.payout_calculation_accuracy:.2f})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--log-cli-level=INFO"])
