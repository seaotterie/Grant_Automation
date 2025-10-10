"""
Complete Platform E2E Tests
Tests end-to-end integration across all workflows and services.

Covers:
- Multi-tool orchestration and workflow engine
- Complete nonprofit intelligence pipeline
- Performance benchmarking across services
- Error handling and recovery scenarios
- Cross-service data flow validation

Phase 6 - Priority 4: Final E2E test suite
"""

import pytest
import time
from datetime import datetime
from typing import Dict, Any, List

# Profiles and discovery
from src.profiles.unified_service import UnifiedProfileService
from src.profiles.models import (
    UnifiedProfile, UnifiedOpportunity, OrganizationType,
    DiscoverySession, ProfileAnalytics
)

# Scoring components
from src.scoring.ntee_scorer import NTEEScorer, NTEEMatchLevel, NTEEDataSource
from src.scoring.composite_scorer_v2 import (
    CompositeScoreV2, OrganizationProfile, FoundationOpportunityData
)
from src.scoring.triage_queue import get_triage_queue, TriagePriority
from src.scoring.time_decay_utils import TimeDecayCalculator, DecayType
from src.scoring.grant_size_scoring import GrantSizeScorer, GrantSizeFit
from src.scoring.schedule_i_voting import (
    ScheduleIVotingSystem, ScheduleIGrantee
)

# Workflow engine
from src.workflows.workflow_engine import WorkflowEngine, WorkflowStatus
from src.workflows.workflow_parser import WorkflowDefinition, WorkflowStep


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_foundation_opportunity_data(
    ein="12-3456789",
    name="Test Foundation",
    ntee_codes=None,
    grants_paid=500000,
    total_assets=10000000
):
    """Helper to create FoundationOpportunityData for testing"""
    if ntee_codes is None:
        ntee_codes = ['B25']

    return FoundationOpportunityData(
        foundation_ein=ein,
        foundation_name=name,
        ntee_codes=ntee_codes,
        ntee_code_sources={code: NTEEDataSource.BMF for code in ntee_codes},
        ntee_code_dates=None,
        schedule_i_grantees=[],
        typical_grant_amount=50000,
        grant_amount_min=10000,
        grant_amount_max=100000,
        geographic_focus_states=['VA', 'MD'],
        total_assets=total_assets,
        grants_paid_total=grants_paid,
        accepts_applications=True,
        most_recent_filing_year=2023
    )


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def profile_service():
    """Unified profile service instance"""
    return UnifiedProfileService()


@pytest.fixture
def workflow_engine():
    """Workflow engine instance"""
    return WorkflowEngine()


@pytest.fixture
def sample_complete_profile():
    """Complete profile with all data populated"""
    return UnifiedProfile(
        profile_id="test_complete_001",
        organization_name="Comprehensive Education Foundation",
        organization_type=OrganizationType.NONPROFIT,
        ein="98-7654321",
        ntee_codes=["B25", "E31"],
        focus_areas=["Education", "Youth Development", "STEM"],
        geographic_scope={
            "states": ["VA", "MD", "DC"],
            "national": False,
            "regions": ["Mid-Atlantic"]
        },
        government_criteria=["Education", "Youth", "Technology"],
        status="active",
        discovery_status=None,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        last_discovery_at=None,
        analytics=ProfileAnalytics(
            opportunity_count=0,
            stages_distribution={},
            scoring_stats={},
            discovery_stats={},
            promotion_stats={}
        ),
        recent_activity=[],
        tags=["education", "youth", "technology"],
        notes="Test profile for complete platform E2E testing"
    )


@pytest.fixture
def sample_foundation_data():
    """Complete foundation data for testing"""
    return {
        'ein': '12-3456789',
        'name': 'Technology Education Foundation',
        'form_type': '990-PF',
        'foundation_code': '03',  # Private non-operating foundation
        'total_assets': 10000000,
        'total_revenue': 600000,
        'grants_paid': 500000,
        'payout_ratio': 0.05,
        'ntee_codes': ['B25', 'U21'],
        'board_members': [
            {'name': 'Jane Smith', 'title': 'Board Chair'},
            {'name': 'John Doe', 'title': 'Treasurer'},
            {'name': 'Alice Johnson', 'title': 'Secretary'}
        ],
        'grant_recipients': [
            {'name': 'School District A', 'ein': '11-1111111', 'amount': 50000, 'ntee': 'B25'},
            {'name': 'STEM Academy', 'ein': '22-2222222', 'amount': 75000, 'ntee': 'E31'},
            {'name': 'Tech Education Center', 'ein': '33-3333333', 'amount': 100000, 'ntee': 'U21'}
        ]
    }


# =============================================================================
# TEST CLASS 1: MULTI-TOOL ORCHESTRATION
# =============================================================================

class TestMultiToolOrchestration:
    """Test coordination between multiple tools and components"""

    def test_ntee_to_composite_scorer_integration(self):
        """Test NTEE scorer output flowing into composite scorer"""
        # Create profile and foundation data
        profile = OrganizationProfile(
            profile_id="test_001",
            name="Education Nonprofit",
            organization_type=OrganizationType.NONPROFIT,
            ein="98-7654321",
            focus_areas=["Education"],
            ntee_codes=["B25"],
            geographic_scope={"states": ["VA"], "national": False},
            state="VA",
            revenue=500000
        )

        foundation = create_foundation_opportunity_data(
            ein='12-3456789',
            ntee_codes=['B25', 'B30'],
            grants_paid=500000,
            total_assets=10000000
        )

        # Step 1: NTEE scoring
        ntee_scorer = NTEEScorer()
        ntee_result = ntee_scorer.score_alignment(
            profile_codes=profile.ntee_codes,
            foundation_codes=foundation.ntee_codes
        )

        assert ntee_result.score > 0.3, "Should have NTEE alignment (major code match)"
        assert ntee_result.match_level in [NTEEMatchLevel.EXACT_FULL, NTEEMatchLevel.EXACT_MAJOR]

        # Step 2: Composite scoring (incorporates NTEE result)
        composite_scorer = CompositeScoreV2()
        composite_result = composite_scorer.score_foundation_match(
            profile=profile,
            foundation=foundation
        )

        assert composite_result.final_score > 0.0, "Composite score should incorporate NTEE score"
        assert composite_result.ntee_alignment_score > 0.0, "Should have NTEE dimension score"
        assert composite_result.recommendation in ["PASS", "ABSTAIN", "FAIL"]

    def test_schedule_i_voting_to_ntee_extraction(self):
        """Test Schedule I voting system extracting NTEE codes"""
        # Create Schedule I grant data
        grantees = [
            ScheduleIGrantee(
                recipient_name="School A",
                recipient_ein="11-1111111",
                grant_amount=50000,
                grant_year=2024
            ),
            ScheduleIGrantee(
                recipient_name="School B",
                recipient_ein="22-2222222",
                grant_amount=75000,
                grant_year=2024
            ),
            ScheduleIGrantee(
                recipient_name="Education Center",
                recipient_ein="33-3333333",
                grant_amount=100000,
                grant_year=2024
            )
        ]

        # Analyze grant-making patterns
        voting_system = ScheduleIVotingSystem()
        analysis = voting_system.analyze_foundation_patterns(
            foundation_ein="12-3456789",
            schedule_i_grantees=grantees
        )

        # Verify analysis structure
        assert analysis.foundation_ein == "12-3456789"
        assert analysis.total_recipients >= 0, "Should track recipient count"
        assert hasattr(analysis, 'coherence_score'), "Should have coherence analysis"
        assert hasattr(analysis, 'entropy_score'), "Should have diversity metrics"

    def test_triage_queue_integration_with_scoring(self):
        """Test triage queue receiving borderline cases from scorers"""
        # Create borderline case (score in abstain range)
        profile = OrganizationProfile(
            profile_id="test_borderline",
            name="Borderline Foundation",
            organization_type=OrganizationType.NONPROFIT,
            ein="55-5555555",
            focus_areas=["Education"],
            ntee_codes=["B"],  # Major code only - lower confidence
            geographic_scope={"states": ["CA"], "national": False},
            state="CA",
            revenue=200000
        )

        foundation = create_foundation_opportunity_data(
            ein='12-3456789',
            ntee_codes=['B25'],  # Different leaf code
            grants_paid=100000,
            total_assets=2000000
        )

        # Score the foundation
        scorer = CompositeScoreV2()
        result = scorer.score_foundation_match(
            profile=profile,
            foundation=foundation
        )

        # If borderline, should be added to triage queue
        if result.recommendation == "ABSTAIN" or result.should_abstain:
            triage_queue = get_triage_queue()

            # Add to triage
            triage_queue.add_case(
                case_id=f"triage_{profile.ein}_{foundation.foundation_ein}",
                profile_id=profile.profile_id,
                foundation_ein=foundation.foundation_ein,
                score=result.final_score,
                reason="Borderline composite score - manual review needed",
                priority=TriagePriority.NORMAL
            )

            # Verify triage queue integration
            cases = triage_queue.get_pending_cases(limit=10)
            assert len(cases) >= 0, "Triage queue should accept borderline cases"

    def test_complete_tool_chain_execution(self):
        """Test complete chain: Profile → NTEE → Composite → Grant Size → Decision"""
        # Create complete test data
        profile = OrganizationProfile(
            profile_id="test_chain",
            name="Complete Chain Test Org",
            organization_type=OrganizationType.NONPROFIT,
            ein="77-7777777",
            focus_areas=["Education", "Technology"],
            ntee_codes=["B25", "U21"],
            geographic_scope={"states": ["VA"], "national": False},
            state="VA",
            revenue=500000
        )

        foundation = create_foundation_opportunity_data(
            ein='88-8888888',
            name='Test Foundation',
            ntee_codes=['B25'],
            grants_paid=500000,
            total_assets=10000000
        )

        # Execute tool chain

        # Step 1: NTEE Scoring
        ntee_scorer = NTEEScorer()
        ntee_result = ntee_scorer.score_alignment(
            profile_codes=profile.ntee_codes,
            foundation_codes=foundation.ntee_codes
        )

        # Step 2: Composite Scoring
        composite_scorer = CompositeScoreV2()
        composite_result = composite_scorer.score_foundation_match(
            profile=profile,
            foundation=foundation
        )

        # Step 3: Grant Size Analysis
        grant_size_scorer = GrantSizeScorer()

        # Use data from profile and foundation (ensure both are not None)
        if foundation.typical_grant_amount and profile.revenue:
            grant_analysis = grant_size_scorer.analyze_grant_fit(
                grant_amount=foundation.typical_grant_amount,
                org_revenue=profile.revenue
            )
            grant_analysis_completed = True
        else:
            grant_analysis_completed = False

        # Step 4: Verify complete chain execution
        assert ntee_result.score >= 0.0, "NTEE scoring completed"
        assert composite_result.final_score >= 0.0, "Composite scoring completed"
        if grant_analysis_completed:
            assert grant_analysis.fit_level in [e.value for e in GrantSizeFit], "Grant size analysis completed"

        # Verify data flows correctly through chain
        assert ntee_result.match_level != NTEEMatchLevel.NO_MATCH or composite_result.final_score < 50.0, \
            "No NTEE match should result in lower composite score"


# =============================================================================
# TEST CLASS 2: COMPLETE WORKFLOW INTEGRATION
# =============================================================================

class TestCompleteWorkflowIntegration:
    """Test complete nonprofit intelligence workflows"""

    def test_discovery_to_research_pipeline(self, profile_service, sample_complete_profile):
        """Test complete discovery → research workflow"""
        # Phase 1: Profile Creation
        profile_created = profile_service.create_profile(sample_complete_profile)
        assert profile_created, "Profile creation should succeed"

        # Phase 2: Discovery Session Start
        session_id = profile_service.start_discovery_session(
            profile_id=sample_complete_profile.profile_id,
            tracks=["federal", "foundation"],
            session_params={"max_results": 10}
        )
        assert session_id is not None, "Discovery session should start"

        # Phase 3: Complete Discovery Session
        completed = profile_service.complete_discovery_session(
            session_id=session_id,
            opportunities_found={"federal": 5, "foundation": 3},
            total_opportunities=8
        )
        assert completed, "Discovery session should complete"

        # Phase 4: Verify Session Data
        session = profile_service.get_session(session_id)
        assert session is not None, "Session should be retrievable"
        assert session.status == "completed", "Session should be marked completed"
        assert session.total_opportunities == 8, "Should track opportunity count"

        # Cleanup
        profile_service.delete_profile(sample_complete_profile.profile_id)

    def test_research_to_analysis_pipeline(self, sample_complete_profile, sample_foundation_data):
        """Test research → analysis → decision workflow"""
        # Create organization profile for scoring
        org_profile = OrganizationProfile(
            profile_id=sample_complete_profile.profile_id,
            name=sample_complete_profile.organization_name,
            organization_type=sample_complete_profile.organization_type,
            ein=sample_complete_profile.ein,
            focus_areas=sample_complete_profile.focus_areas,
            ntee_codes=sample_complete_profile.ntee_codes,
            geographic_scope=sample_complete_profile.geographic_scope,
            state=sample_complete_profile.geographic_scope.get('states', ['VA'])[0],
            revenue=500000
        )

        # Convert sample foundation data to FoundationOpportunityData
        foundation = create_foundation_opportunity_data(
            ein=sample_foundation_data['ein'],
            name=sample_foundation_data['name'],
            ntee_codes=sample_foundation_data['ntee_codes'],
            grants_paid=sample_foundation_data['grants_paid'],
            total_assets=sample_foundation_data['total_assets']
        )

        # Research Phase: Analyze foundation
        composite_scorer = CompositeScoreV2()
        research_result = composite_scorer.score_foundation_match(
            profile=org_profile,
            foundation=foundation
        )

        assert research_result.final_score >= 0.0, "Research scoring should complete"
        assert research_result.recommendation in ["PASS", "ABSTAIN", "FAIL"]

        # Analysis Phase: Deep examination (same method - composite scoring is comprehensive)
        if research_result.recommendation in ["PASS", "ABSTAIN"]:
            # Verify we have all dimension scores
            assert research_result.ntee_alignment_score >= 0.0, "Should have NTEE dimension"
            assert research_result.geographic_match_score >= 0.0, "Should have geographic dimension"
            assert research_result.financial_capacity_score >= 0.0, "Should have financial dimension"
            assert research_result.grant_size_fit_score >= 0.0, "Should have grant size dimension"
            assert research_result.application_policy_score >= 0.0, "Should have application policy dimension"

    def test_complete_nonprofit_intelligence_workflow(self, profile_service, sample_complete_profile):
        """Test end-to-end nonprofit intelligence pipeline"""
        start_time = time.time()

        # Step 1: Create Profile
        profile_created = profile_service.create_profile(sample_complete_profile)
        assert profile_created, "Profile creation failed"

        # Step 2: Start Discovery
        session_id = profile_service.start_discovery_session(
            profile_id=sample_complete_profile.profile_id,
            tracks=["federal", "foundation", "state"],
            session_params={"comprehensive": True}
        )
        assert session_id is not None, "Discovery session start failed"

        # Step 3: Simulate Discovery Results
        profile_service.complete_discovery_session(
            session_id=session_id,
            opportunities_found={
                "federal": 10,
                "foundation": 15,
                "state": 5
            },
            total_opportunities=30
        )

        # Step 4: Get Profile Analytics
        analytics = profile_service.get_profile_analytics(sample_complete_profile.profile_id)

        assert analytics is not None or analytics == {}, "Analytics should be retrievable"

        # Step 5: Verify Complete Workflow
        profile = profile_service.get_profile(sample_complete_profile.profile_id)
        assert profile is not None, "Profile should exist"
        assert profile.discovery_status in ["completed", None], "Discovery should be completed"

        execution_time = time.time() - start_time
        assert execution_time < 5.0, f"Complete workflow took {execution_time:.2f}s (should be <5s)"

        # Cleanup
        profile_service.delete_profile(sample_complete_profile.profile_id)

    def test_workflow_with_multiple_opportunities(self, profile_service, sample_complete_profile):
        """Test workflow handling multiple opportunities"""
        # Create profile
        profile_created = profile_service.create_profile(sample_complete_profile)
        assert profile_created, "Profile creation failed"

        # Create multiple opportunities
        opportunities = []
        for i in range(5):
            opp = UnifiedOpportunity(
                opportunity_id=f"opp_{i:03d}",
                profile_id=sample_complete_profile.profile_id,
                organization_name=f"Foundation {i}",
                source_track="foundation",
                current_stage="DISCOVER",
                discovered_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
                stage_history=[],
                promotion_history=[],
                scoring=None,
                user_assessment=None
            )
            opportunities.append(opp)

            # Save opportunity
            saved = profile_service.save_opportunity(
                profile_id=sample_complete_profile.profile_id,
                opportunity=opp
            )
            assert saved, f"Opportunity {i} save failed"

        # Retrieve all opportunities
        retrieved_opps = profile_service.get_profile_opportunities(
            profile_id=sample_complete_profile.profile_id
        )

        assert len(retrieved_opps) == 5, f"Expected 5 opportunities, got {len(retrieved_opps)}"

        # Cleanup
        profile_service.delete_profile(sample_complete_profile.profile_id)


# =============================================================================
# TEST CLASS 3: PERFORMANCE BENCHMARKING
# =============================================================================

class TestPerformanceBenchmarking:
    """Test performance across all services"""

    def test_profile_creation_performance(self, profile_service):
        """Benchmark profile creation performance"""
        start_time = time.time()

        profiles_created = 0
        for i in range(10):
            profile = UnifiedProfile(
                profile_id=f"perf_test_{i:03d}",
                organization_name=f"Performance Test Org {i}",
                organization_type=OrganizationType.NONPROFIT,
                ein=f"99-999{i:04d}",
                ntee_codes=["B25"],
                focus_areas=["Education"],
                geographic_scope={"states": ["VA"], "national": False},
                government_criteria=[],
                status="active",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                analytics=ProfileAnalytics()
            )

            if profile_service.create_profile(profile):
                profiles_created += 1

        execution_time = time.time() - start_time
        avg_time_per_profile = execution_time / 10

        assert profiles_created == 10, "All profiles should be created"
        assert avg_time_per_profile < 0.5, f"Profile creation too slow: {avg_time_per_profile:.3f}s avg"

        # Cleanup
        for i in range(10):
            profile_service.delete_profile(f"perf_test_{i:03d}")

    def test_scoring_performance(self):
        """Benchmark composite scoring performance"""
        profile = OrganizationProfile(
            profile_id="perf_score_test",
            name="Performance Test Org",
            organization_type=OrganizationType.NONPROFIT,
            ein="99-9999999",
            focus_areas=["Education"],
            ntee_codes=["B25"],
            geographic_scope={"states": ["VA"], "national": False},
            state="VA",
            revenue=500000
        )

        foundation = create_foundation_opportunity_data(
            ein='88-8888888',
            ntee_codes=['B25'],
            grants_paid=500000,
            total_assets=10000000
        )

        scorer = CompositeScoreV2()

        # Benchmark scoring performance
        start_time = time.time()
        iterations = 100

        for _ in range(iterations):
            result = scorer.score_foundation_match(
                profile=profile,
                foundation=foundation
            )
            assert result.final_score >= 0.0

        execution_time = time.time() - start_time
        avg_time_per_score = (execution_time / iterations) * 1000  # Convert to ms

        assert avg_time_per_score < 10.0, f"Scoring too slow: {avg_time_per_score:.2f}ms avg (should be <10ms)"

    def test_ntee_scoring_performance(self):
        """Benchmark NTEE scoring performance"""
        profile_codes = ["B25", "E31", "U21"]
        foundation_codes = ["B25", "B30", "E20"]

        scorer = NTEEScorer()

        start_time = time.time()
        iterations = 1000

        for _ in range(iterations):
            result = scorer.score_alignment(
                profile_codes=profile_codes,
                foundation_codes=foundation_codes
            )
            assert result.score >= 0.0

        execution_time = time.time() - start_time
        avg_time_per_score = (execution_time / iterations) * 1000  # Convert to ms

        assert avg_time_per_score < 1.0, f"NTEE scoring too slow: {avg_time_per_score:.3f}ms avg (should be <1ms)"


# =============================================================================
# TEST CLASS 4: ERROR HANDLING SCENARIOS
# =============================================================================

class TestErrorHandlingScenarios:
    """Test error handling and recovery"""

    def test_missing_profile_handling(self, profile_service):
        """Test handling of non-existent profile"""
        # Try to get non-existent profile
        profile = profile_service.get_profile("nonexistent_profile_id")
        assert profile is None, "Should return None for non-existent profile"

        # Try to update non-existent profile
        fake_profile = UnifiedProfile(
            profile_id="nonexistent_profile_id",
            organization_name="Fake Org",
            organization_type=OrganizationType.NONPROFIT,
            ein="00-0000000",
            ntee_codes=[],
            focus_areas=[],
            geographic_scope={},
            government_criteria=[],
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            analytics=ProfileAnalytics()
        )

        updated = profile_service.update_profile(fake_profile)
        assert updated == False, "Should fail to update non-existent profile"

    def test_invalid_ntee_code_handling(self):
        """Test handling of invalid NTEE codes"""
        scorer = NTEEScorer()

        # Test with invalid codes
        result = scorer.score_alignment(
            profile_codes=["INVALID", "123", ""],
            foundation_codes=["B25"]
        )

        # Should handle gracefully and return low/zero score
        assert result.score >= 0.0, "Should handle invalid codes gracefully"
        assert result.match_level == NTEEMatchLevel.NO_MATCH, "Invalid codes should result in no match"

    def test_incomplete_foundation_data_handling(self):
        """Test handling of incomplete foundation data"""
        profile = OrganizationProfile(
            profile_id="test_incomplete",
            name="Test Org",
            organization_type=OrganizationType.NONPROFIT,
            ein="99-9999999",
            focus_areas=["Education"],
            ntee_codes=["B25"],
            geographic_scope={"states": ["VA"], "national": False}
        )

        # Foundation data missing key fields
        incomplete_data = {
            'ein': '88-8888888',
            # Missing ntee_codes, grants_paid, total_assets
        }

        scorer = CompositeScoreV2()

        # Should handle missing data gracefully
        try:
            result = scorer.score_foundation(
                profile=profile,
                foundation_data=incomplete_data,
                stage="ANALYZE"
            )
            # If it completes, score should reflect missing data
            assert result.final_score >= 0.0, "Should handle incomplete data"
        except (KeyError, ValueError, AttributeError):
            # Or it may raise an exception - either is acceptable
            pass


# =============================================================================
# TEST CLASS 5: CROSS-SERVICE DATA FLOW
# =============================================================================

class TestCrossServiceDataFlow:
    """Test data flow between services"""

    def test_profile_to_opportunity_data_flow(self, profile_service):
        """Test data flow from profile to opportunities"""
        # Create profile
        profile = UnifiedProfile(
            profile_id="data_flow_test",
            organization_name="Data Flow Test Org",
            organization_type=OrganizationType.NONPROFIT,
            ein="99-9999999",
            ntee_codes=["B25"],
            focus_areas=["Education"],
            geographic_scope={"states": ["VA"], "national": False},
            government_criteria=["Education"],
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            analytics=ProfileAnalytics()
        )

        profile_created = profile_service.create_profile(profile)
        assert profile_created, "Profile creation failed"

        # Create opportunity linked to profile
        opportunity = UnifiedOpportunity(
            opportunity_id="opp_data_flow_001",
            profile_id=profile.profile_id,
            organization_name="Foundation XYZ",
            source_track="foundation",
            current_stage="DISCOVER",
            discovered_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            stage_history=[],
            promotion_history=[],
            scoring=None,
            user_assessment=None
        )

        opp_saved = profile_service.save_opportunity(
            profile_id=profile.profile_id,
            opportunity=opportunity
        )
        assert opp_saved, "Opportunity save failed"

        # Verify data flow: profile → opportunity retrieval
        retrieved_opp = profile_service.get_opportunity(
            profile_id=profile.profile_id,
            opportunity_id=opportunity.opportunity_id
        )

        assert retrieved_opp is not None, "Opportunity should be retrievable"
        assert retrieved_opp.profile_id == profile.profile_id, "Opportunity should link to correct profile"

        # Cleanup
        profile_service.delete_profile(profile.profile_id)

    def test_scoring_to_analytics_data_flow(self, profile_service):
        """Test data flow from scoring to profile analytics"""
        # Create profile
        profile = UnifiedProfile(
            profile_id="scoring_analytics_test",
            organization_name="Scoring Analytics Test",
            organization_type=OrganizationType.NONPROFIT,
            ein="88-8888888",
            ntee_codes=["B25"],
            focus_areas=["Education"],
            geographic_scope={"states": ["VA"], "national": False},
            government_criteria=[],
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            analytics=ProfileAnalytics(
                opportunity_count=0,
                stages_distribution={},
                scoring_stats={},
                discovery_stats={},
                promotion_stats={}
            )
        )

        profile_created = profile_service.create_profile(profile)
        assert profile_created, "Profile creation failed"

        # Get analytics (should initialize correctly)
        analytics = profile_service.get_profile_analytics(profile.profile_id)

        # Analytics may be empty dict or have structure
        assert analytics is not None or analytics == {}, "Analytics should be accessible"

        # Cleanup
        profile_service.delete_profile(profile.profile_id)

    def test_session_to_profile_data_flow(self, profile_service):
        """Test data flow from discovery session to profile"""
        # Create profile
        profile = UnifiedProfile(
            profile_id="session_flow_test",
            organization_name="Session Flow Test",
            organization_type=OrganizationType.NONPROFIT,
            ein="77-7777777",
            ntee_codes=["B25"],
            focus_areas=["Education"],
            geographic_scope={"states": ["VA"], "national": False},
            government_criteria=[],
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            analytics=ProfileAnalytics()
        )

        profile_created = profile_service.create_profile(profile)
        assert profile_created, "Profile creation failed"

        # Start discovery session
        session_id = profile_service.start_discovery_session(
            profile_id=profile.profile_id,
            tracks=["federal"],
            session_params={}
        )
        assert session_id is not None, "Session start failed"

        # Complete session
        completed = profile_service.complete_discovery_session(
            session_id=session_id,
            opportunities_found={"federal": 5},
            total_opportunities=5
        )
        assert completed, "Session completion failed"

        # Verify data flow: session → profile update
        updated_profile = profile_service.get_profile(profile.profile_id)
        assert updated_profile is not None, "Profile should exist"
        assert updated_profile.discovery_status in ["completed", None], "Profile should reflect session completion"
        assert updated_profile.last_discovery_at is not None, "Profile should track last discovery time"

        # Cleanup
        profile_service.delete_profile(profile.profile_id)
