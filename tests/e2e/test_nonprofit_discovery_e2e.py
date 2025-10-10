"""
End-to-End Test: Nonprofit Discovery Workflow
=============================================

Tests the complete nonprofit discovery workflow from data sources through
profile creation and enrichment.

Workflow Steps:
1. Profile Creation - Create nonprofit profile
2. Discovery Session - Track discovery workflow
3. NTEE Scoring - Score alignment with foundations
4. Triage Queue - Handle borderline cases
5. Analytics - Compute profile analytics

Test Approach:
- Tests actual service layer integration
- Validates complete data flow
- Ensures profile lifecycle management
- Verifies scoring and triage integration
"""

import pytest
import logging
from datetime import datetime
from typing import Dict, Any, List

# Core service imports
from src.profiles.unified_service import UnifiedProfileService
from src.profiles.models import UnifiedProfile, ProfileAnalytics

# Scoring imports
from src.scoring.ntee_scorer import NTEEScorer, score_ntee_alignment, NTEEMatchLevel
from src.scoring.triage_queue import TriageQueue, get_triage_queue, TriagePriority, ExpertDecision

logger = logging.getLogger(__name__)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def profile_service():
    """Create Profile Service instance"""
    return UnifiedProfileService()


@pytest.fixture
def ntee_scorer():
    """Create NTEE Scorer instance"""
    return NTEEScorer(enable_time_decay=False)


@pytest.fixture
def triage_queue():
    """Get global triage queue instance and clear it"""
    queue = get_triage_queue()
    # Clear queue for clean testing (use public attributes)
    queue.queue.clear()
    queue.review_history.clear()
    return queue


@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing"""
    return {
        "profile_id": "e2e_test_profile_001",
        "organization_name": "E2E Test Nonprofit Organization",
        "ein": "12-3456789",
        "organization_type": "501c3",
        "ntee_codes": ["P20", "E31"],
        "focus_areas": ["Education", "Youth Development"],
        "geographic_scope": {
            "states": ["VA", "MD", "DC"],
            "national": False
        },
        "government_criteria": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active"
    }


@pytest.fixture
def cleanup_profiles(profile_service):
    """Cleanup test profiles after tests"""
    created_profiles = []

    def track(profile_id):
        created_profiles.append(profile_id)

    yield track

    # Cleanup
    for profile_id in created_profiles:
        try:
            profile_service.delete_profile(profile_id)
            logger.info(f"Cleaned up profile: {profile_id}")
        except Exception as e:
            logger.warning(f"Could not cleanup {profile_id}: {e}")


# ============================================================================
# Test Class 1: Profile Lifecycle
# ============================================================================

class TestProfileLifecycle:
    """Test complete profile lifecycle from creation to deletion"""

    def test_create_profile(self, profile_service, sample_profile_data, cleanup_profiles):
        """Test creating a new nonprofit profile"""
        # Create profile
        profile = UnifiedProfile(**sample_profile_data)
        success = profile_service.save_profile(profile)

        assert success, "Profile creation should succeed"
        cleanup_profiles(sample_profile_data["profile_id"])

        # Verify profile was created
        retrieved = profile_service.get_profile(sample_profile_data["profile_id"])
        assert retrieved is not None, "Should retrieve created profile"
        assert retrieved.organization_name == "E2E Test Nonprofit Organization"
        assert retrieved.ein == "12-3456789"
        assert "P20" in retrieved.ntee_codes
        assert "E31" in retrieved.ntee_codes

        logger.info(f"Created profile: {retrieved.organization_name} ({retrieved.ein})")

    def test_update_profile(self, profile_service, sample_profile_data, cleanup_profiles):
        """Test updating an existing profile"""
        # Create initial profile
        profile = UnifiedProfile(**sample_profile_data)
        profile_service.save_profile(profile)
        cleanup_profiles(sample_profile_data["profile_id"])

        # Update profile
        updated = profile_service.get_profile(sample_profile_data["profile_id"])
        updated.focus_areas.append("Community Development")
        updated.ntee_codes.append("S20")

        success = profile_service.save_profile(updated)
        assert success, "Profile update should succeed"

        # Verify updates
        final = profile_service.get_profile(sample_profile_data["profile_id"])
        assert "Community Development" in final.focus_areas
        assert "S20" in final.ntee_codes

        logger.info(f"Updated profile with new focus areas: {final.focus_areas}")

    def test_profile_list_operations(self, profile_service, cleanup_profiles):
        """Test listing and searching profiles"""
        # Create multiple test profiles
        for i in range(3):
            profile_data = {
                "profile_id": f"e2e_list_test_{i:03d}",
                "organization_name": f"E2E List Test Organization {i}",
                "ein": f"22-{i:07d}",
                "organization_type": "501c3",
                "ntee_codes": ["P20"],
                "focus_areas": ["Education"],
                "geographic_scope": {"states": ["VA"]},
                "government_criteria": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "active"
            }
            profile = UnifiedProfile(**profile_data)
            profile_service.save_profile(profile)
            cleanup_profiles(f"e2e_list_test_{i:03d}")

        # List profiles
        profiles = profile_service.list_profiles(limit=50)
        e2e_profiles = [p for p in profiles if p["profile_id"].startswith("e2e_list_test")]
        assert len(e2e_profiles) >= 3, "Should find at least 3 test profiles"

        # Search profiles
        search_results = profile_service.list_profiles(search="E2E List Test")
        e2e_results = [p for p in search_results if p["profile_id"].startswith("e2e_list_test")]
        assert len(e2e_results) >= 3, "Should find test profiles in search"

        logger.info(f"Found {len(e2e_profiles)} E2E test profiles")


# ============================================================================
# Test Class 2: Discovery Session Management
# ============================================================================

class TestDiscoverySessionManagement:
    """Test discovery session tracking and management"""

    def test_start_discovery_session(self, profile_service, sample_profile_data, cleanup_profiles):
        """Test starting a discovery session"""
        # Create profile
        profile = UnifiedProfile(**sample_profile_data)
        profile_service.save_profile(profile)
        cleanup_profiles(sample_profile_data["profile_id"])

        # Start discovery session
        session_id = profile_service.start_discovery_session(
            profile_id=sample_profile_data["profile_id"],
            tracks=["bmf", "990", "schedule_i"]
        )

        assert session_id is not None, "Should create discovery session"
        assert session_id.startswith("session_"), "Session ID should have correct format"

        # Verify session was created
        session = profile_service.get_session(session_id)
        assert session is not None
        assert session.status == "in_progress"
        assert session.profile_id == sample_profile_data["profile_id"]
        assert "bmf" in session.tracks_executed

        logger.info(f"Started discovery session: {session_id}")

    def test_complete_discovery_session(self, profile_service, sample_profile_data, cleanup_profiles):
        """Test completing a discovery session"""
        # Create profile and start session
        profile = UnifiedProfile(**sample_profile_data)
        profile_service.save_profile(profile)
        cleanup_profiles(sample_profile_data["profile_id"])

        session_id = profile_service.start_discovery_session(
            profile_id=sample_profile_data["profile_id"],
            tracks=["bmf"]
        )

        # Complete session
        success = profile_service.complete_discovery_session(
            session_id=session_id,
            opportunities_found={"bmf": 15, "990": 8},
            total_opportunities=23
        )

        assert success, "Session completion should succeed"

        # Verify session status
        session = profile_service.get_session(session_id)
        assert session.status == "completed"
        assert session.total_opportunities == 23
        assert session.opportunities_found["bmf"] == 15

        logger.info(f"Completed session {session_id}: {session.total_opportunities} opportunities found")

    def test_fail_discovery_session(self, profile_service, sample_profile_data, cleanup_profiles):
        """Test failing a discovery session with errors"""
        # Create profile and start session
        profile = UnifiedProfile(**sample_profile_data)
        profile_service.save_profile(profile)
        cleanup_profiles(sample_profile_data["profile_id"])

        session_id = profile_service.start_discovery_session(
            profile_id=sample_profile_data["profile_id"],
            tracks=["bmf"]
        )

        # Fail session
        success = profile_service.fail_discovery_session(
            session_id=session_id,
            errors=["Database connection timeout", "BMF service unavailable"]
        )

        assert success, "Session failure should be recorded"

        # Verify session status
        session = profile_service.get_session(session_id)
        assert session.status == "failed"
        assert len(session.error_messages) == 2
        assert "Database connection timeout" in session.error_messages

        logger.info(f"Failed session {session_id}: {session.error_messages}")

    def test_abandoned_session_handling(self, profile_service, sample_profile_data, cleanup_profiles):
        """Test handling abandoned sessions"""
        # Create profile
        profile = UnifiedProfile(**sample_profile_data)
        profile_service.save_profile(profile)
        cleanup_profiles(sample_profile_data["profile_id"])

        # Start first session
        session1_id = profile_service.start_discovery_session(
            profile_id=sample_profile_data["profile_id"],
            tracks=["bmf"]
        )

        # Start second session (should mark first as failed)
        session2_id = profile_service.start_discovery_session(
            profile_id=sample_profile_data["profile_id"],
            tracks=["990"]
        )

        # Verify first session was marked as failed
        session1 = profile_service.get_session(session1_id)
        assert session1.status == "failed"
        assert "Session abandoned" in session1.error_messages[0]

        # Verify second session is active
        session2 = profile_service.get_session(session2_id)
        assert session2.status == "in_progress"

        logger.info(f"Abandoned session handling: {session1_id} failed, {session2_id} active")


# ============================================================================
# Test Class 3: NTEE Scoring Integration
# ============================================================================

class TestNTEEScoring:
    """Test NTEE code alignment scoring"""

    def test_perfect_ntee_match(self, ntee_scorer):
        """Test perfect NTEE code alignment"""
        result = ntee_scorer.score_alignment(
            profile_codes=["P20", "E31"],
            foundation_codes=["P20", "E31"]
        )

        assert result.score == 1.0, "Perfect match should score 1.0"
        assert result.match_level == NTEEMatchLevel.EXACT_FULL
        assert result.major_score == 1.0
        assert result.leaf_score == 1.0
        assert "Exact NTEE match" in result.explanation

        logger.info(f"Perfect NTEE match: Score={result.score:.3f}")

    def test_major_only_match(self, ntee_scorer):
        """Test NTEE major code match with different leafs"""
        result = ntee_scorer.score_alignment(
            profile_codes=["P20"],  # Education P20
            foundation_codes=["P30"]  # Education P30 (different leaf)
        )

        assert result.score == 0.4, "Major-only match should score 0.4"
        assert result.match_level == NTEEMatchLevel.EXACT_MAJOR
        assert result.major_score == 1.0
        assert result.leaf_score == 0.0
        assert "Major match but different subcategory" in result.explanation

        logger.info(f"Major-only match: Score={result.score:.3f}")

    def test_no_ntee_match(self, ntee_scorer):
        """Test NTEE codes with no alignment"""
        result = ntee_scorer.score_alignment(
            profile_codes=["E31"],  # Education
            foundation_codes=["A20"]  # Arts (unrelated)
        )

        assert result.score == 0.0, "No match should score 0.0"
        assert result.match_level == NTEEMatchLevel.NO_MATCH
        assert "No NTEE code alignment" in result.explanation

        logger.info(f"No NTEE match: Score={result.score:.3f}")

    def test_multiple_code_best_match(self, ntee_scorer):
        """Test finding best match among multiple codes"""
        result = ntee_scorer.score_alignment(
            profile_codes=["P20", "E31", "B25"],
            foundation_codes=["A20", "E31", "Q30"]
        )

        # Should find exact match on E31
        assert result.score == 1.0, "Should find best match (E31)"
        assert result.match_level == NTEEMatchLevel.EXACT_FULL

        logger.info(f"Multiple codes best match: Score={result.score:.3f}")


# ============================================================================
# Test Class 4: Triage Queue Integration
# ============================================================================

class TestTriageQueueIntegration:
    """Test triage queue for borderline scoring cases"""

    def test_add_borderline_case(self, triage_queue):
        """Test adding borderline case to triage queue"""
        item = triage_queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Test Nonprofit",
            foundation_ein="98-7654321",
            foundation_name="Test Foundation",
            composite_score=52.0,  # Borderline score
            confidence=0.75,
            abstain_reason="Borderline NTEE alignment",
            component_scores={
                "ntee_alignment": 30.0,
                "filing_recency": 50.0,
                "board_network": 60.0
            }
        )

        assert item is not None
        assert item.composite_score == 52.0
        assert item.priority == TriagePriority.MEDIUM
        assert item.abstain_reason == "Borderline NTEE alignment"

        logger.info(f"Added borderline case: Priority={item.priority}, Score={item.composite_score}")

    def test_critical_priority_assignment(self, triage_queue):
        """Test critical priority for missing data cases"""
        item = triage_queue.add_to_queue(
            profile_ein="11-1111111",
            profile_name="Critical Case",
            foundation_ein="99-9999999",
            foundation_name="Test Foundation",
            composite_score=52.0,
            confidence=0.5,  # Low confidence
            abstain_reason="Missing critical NTEE data",
            component_scores={}
        )

        assert item.priority == TriagePriority.CRITICAL
        logger.info(f"Critical priority assigned: Confidence={item.confidence}")

    def test_triage_review_workflow(self, triage_queue):
        """Test complete triage review workflow"""
        # Add item to queue
        item = triage_queue.add_to_queue(
            profile_ein="22-2222222",
            profile_name="Review Test",
            foundation_ein="99-9999999",
            foundation_name="Test Foundation",
            composite_score=55.0,
            confidence=0.8,
            abstain_reason="Borderline score",
            component_scores={"ntee_alignment": 35.0}
        )

        # Get next item for review
        review_item = triage_queue.get_next_for_review(analyst_id="test_analyst")
        assert review_item is not None
        assert review_item.item_id == item.item_id

        # Submit review decision
        success = triage_queue.submit_review(
            item_id=item.item_id,
            decision=ExpertDecision.PASS,
            rationale="Strong mission alignment confirmed",
            reviewer_id="test_analyst"
        )

        assert success
        logger.info(f"Triage review completed: Decision={ExpertDecision.PASS}")

    def test_triage_queue_statistics(self, triage_queue):
        """Test triage queue statistics calculation"""
        # Add multiple items
        for i in range(5):
            triage_queue.add_to_queue(
                profile_ein=f"33-{i:07d}",
                profile_name=f"Stats Test {i}",
                foundation_ein="99-9999999",
                foundation_name="Test Foundation",
                composite_score=50.0 + i,
                confidence=0.7 + (i * 0.05),
                abstain_reason="Borderline",
                component_scores={}
            )

        # Get statistics
        stats = triage_queue.get_queue_stats()

        assert stats.total_items >= 5
        assert stats.pending_count >= 5
        assert stats.medium_count >= 5  # All should be medium priority

        logger.info(f"Queue stats: {stats.total_items} items, Medium priority={stats.medium_count}")


# ============================================================================
# Test Class 5: Complete Discovery Workflow
# ============================================================================

class TestCompleteDiscoveryWorkflow:
    """Test complete end-to-end discovery workflow"""

    def test_full_workflow_integration(self, profile_service, ntee_scorer, triage_queue, cleanup_profiles):
        """Test complete workflow from profile creation through scoring"""
        # Step 1: Create nonprofit profile
        profile_data = {
            "profile_id": "e2e_workflow_001",
            "organization_name": "Workflow Test Nonprofit",
            "ein": "44-5566778",
            "organization_type": "501c3",
            "ntee_codes": ["P20", "E31"],
            "focus_areas": ["Education", "Youth Services"],
            "geographic_scope": {"states": ["VA", "MD"]},
            "government_criteria": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active"
        }

        profile = UnifiedProfile(**profile_data)
        success = profile_service.save_profile(profile)
        assert success
        cleanup_profiles("e2e_workflow_001")

        logger.info(f"Step 1: Created profile {profile.organization_name}")

        # Step 2: Start discovery session
        session_id = profile_service.start_discovery_session(
            profile_id="e2e_workflow_001",
            tracks=["bmf", "990"]
        )
        assert session_id is not None

        logger.info(f"Step 2: Started discovery session {session_id}")

        # Step 3: Score NTEE alignment (simulated foundation match)
        ntee_result = ntee_scorer.score_alignment(
            profile_codes=profile.ntee_codes,
            foundation_codes=["P20", "E30"]  # Good but not perfect match
        )

        logger.info(f"Step 3: NTEE Score={ntee_result.score:.3f}, Level={ntee_result.match_level}")

        # Step 4: Add to triage queue if borderline
        if 0.3 < ntee_result.score < 0.6:
            triage_item = triage_queue.add_to_queue(
                profile_ein=profile.ein,
                profile_name=profile.organization_name,
                foundation_ein="99-8877665",
                foundation_name="Test Foundation",
                composite_score=ntee_result.score * 100,
                confidence=ntee_result.confidence,
                abstain_reason="Borderline NTEE alignment",
                component_scores={"ntee_alignment": ntee_result.score * 100}
            )

            logger.info(f"Step 4: Added to triage queue, Priority={triage_item.priority}")

        # Step 5: Complete discovery session
        success = profile_service.complete_discovery_session(
            session_id=session_id,
            opportunities_found={"bmf": 12, "990": 8},
            total_opportunities=20
        )
        assert success

        logger.info(f"Step 5: Completed discovery session with 20 opportunities")

        # Step 6: Verify analytics
        analytics = profile_service.get_profile_analytics("e2e_workflow_001")
        assert analytics is not None
        assert "total_opportunities" in analytics

        logger.info(f"Step 6: Profile analytics computed: {analytics['total_opportunities']} opportunities")

    def test_workflow_error_handling(self, profile_service, cleanup_profiles):
        """Test error handling in discovery workflow"""
        # Test with non-existent profile
        session_id = profile_service.start_discovery_session(
            profile_id="nonexistent_profile",
            tracks=["bmf"]
        )

        # Should handle gracefully (likely returns None or empty session)
        assert session_id is None or session_id.startswith("session_")

    def test_workflow_performance_tracking(self, profile_service, cleanup_profiles):
        """Test performance tracking throughout workflow"""
        # Create profile
        profile_data = {
            "profile_id": "e2e_perf_001",
            "organization_name": "Performance Test Org",
            "ein": "55-6677889",
            "organization_type": "501c3",
            "ntee_codes": ["P20"],
            "focus_areas": ["Education"],
            "geographic_scope": {"states": ["VA"]},
            "government_criteria": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active"
        }

        profile = UnifiedProfile(**profile_data)
        start_time = datetime.now()

        profile_service.save_profile(profile)
        cleanup_profiles("e2e_perf_001")

        # Start and complete session
        session_id = profile_service.start_discovery_session(
            profile_id="e2e_perf_001",
            tracks=["bmf"]
        )

        profile_service.complete_discovery_session(
            session_id=session_id,
            opportunities_found={"bmf": 10},
            total_opportunities=10
        )

        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        # Verify session tracked execution time
        session = profile_service.get_session(session_id)
        assert session.execution_time_seconds is not None

        logger.info(f"Workflow completed in {duration_ms:.1f}ms")
        logger.info(f"Session execution time: {session.execution_time_seconds}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--log-cli-level=INFO"])
