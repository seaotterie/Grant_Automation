"""
Unit Tests for Triage Queue System
===================================

Tests for the Abstain/Triage Queue System (V2.0) that enables human-in-the-loop
validation for borderline 990-PF screening results (scores 45-58).

Test Categories:
1. Queue Management - Add items, retrieve items, queue state
2. Priority System - Priority determination and ordering
3. Review Workflow - Get next item, submit reviews, status changes
4. Statistics - Queue stats calculation and metrics
5. Export - JSON export for review dashboards
6. Edge Cases - Empty queues, missing items, invalid operations
"""

import pytest
from datetime import datetime, timedelta
from src.scoring.triage_queue import (
    TriageQueue,
    TriageItem,
    TriageStatus,
    TriagePriority,
    ExpertDecision,
    TriageQueueStats,
    get_triage_queue
)


# ============================================================================
# Test Class 1: Queue Management
# ============================================================================

class TestQueueManagement:
    """Test basic queue operations"""

    def test_add_to_queue(self):
        """Test adding item to triage queue"""
        queue = TriageQueue()

        item = queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Test Nonprofit",
            foundation_ein="98-7654321",
            foundation_name="Test Foundation",
            composite_score=52.0,
            confidence=0.75,
            abstain_reason="Borderline NTEE match",
            component_scores={
                'ntee': 45.0,
                'geographic': 60.0,
                'coherence': 50.0,
                'grant_size': 55.0
            }
        )

        assert item is not None
        assert item.profile_ein == "12-3456789"
        assert item.foundation_ein == "98-7654321"
        assert item.composite_score == 52.0
        assert item.status == TriageStatus.PENDING
        assert len(queue.queue) == 1

    def test_item_id_generation(self):
        """Test unique item ID generation across different EINs"""
        queue = TriageQueue()

        item1 = queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Org1",
            foundation_ein="98-7654321",
            foundation_name="Found1",
            composite_score=50.0,
            confidence=0.7,
            abstain_reason="Test",
            component_scores={}
        )

        # Different foundation EIN should create different ID
        item2 = queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Org1",
            foundation_ein="98-0000000",  # Different foundation
            foundation_name="Found2",
            composite_score=50.0,
            confidence=0.7,
            abstain_reason="Test",
            component_scores={}
        )

        # IDs should be unique (different foundation EINs)
        assert item1.item_id != item2.item_id
        assert len(queue.queue) == 2
        assert "98-7654321" in item1.item_id
        assert "98-0000000" in item2.item_id

    def test_component_scores_extraction(self):
        """Test component scores are properly extracted"""
        queue = TriageQueue()

        item = queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Test",
            foundation_ein="98-7654321",
            foundation_name="Test",
            composite_score=50.0,
            confidence=0.7,
            abstain_reason="Test",
            component_scores={
                'ntee': 45.0,
                'geographic': 60.0,
                'coherence': 50.0,
                'grant_size': 55.0
            }
        )

        assert item.ntee_score == 45.0
        assert item.geographic_score == 60.0
        assert item.coherence_score == 50.0
        assert item.grant_size_score == 55.0

    def test_missing_component_scores(self):
        """Test handling of missing component scores"""
        queue = TriageQueue()

        item = queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Test",
            foundation_ein="98-7654321",
            foundation_name="Test",
            composite_score=50.0,
            confidence=0.7,
            abstain_reason="Test",
            component_scores={}  # Empty scores
        )

        # Should default to 0.0
        assert item.ntee_score == 0.0
        assert item.geographic_score == 0.0
        assert item.coherence_score == 0.0
        assert item.grant_size_score == 0.0

    def test_tags_support(self):
        """Test optional tags functionality"""
        queue = TriageQueue()

        item = queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Test",
            foundation_ein="98-7654321",
            foundation_name="Test",
            composite_score=50.0,
            confidence=0.7,
            abstain_reason="Test",
            component_scores={},
            tags=["education", "local"]
        )

        assert item.tags == ["education", "local"]


# ============================================================================
# Test Class 2: Priority System
# ============================================================================

class TestPrioritySystem:
    """Test priority determination and ordering"""

    def test_critical_priority_missing_data(self):
        """Test CRITICAL priority for missing data with decent score"""
        queue = TriageQueue()

        item = queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Test",
            foundation_ein="98-7654321",
            foundation_name="Test",
            composite_score=52.0,
            confidence=0.7,
            abstain_reason="Missing critical NTEE data",
            component_scores={}
        )

        assert item.priority == TriagePriority.CRITICAL

    def test_high_priority_upper_borderline(self):
        """Test HIGH priority for scores 55-58"""
        queue = TriageQueue()

        item = queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Test",
            foundation_ein="98-7654321",
            foundation_name="Test",
            composite_score=56.0,
            confidence=0.7,
            abstain_reason="Borderline high",
            component_scores={}
        )

        assert item.priority == TriagePriority.HIGH

    def test_medium_priority_true_borderline(self):
        """Test MEDIUM priority for scores 50-55"""
        queue = TriageQueue()

        item = queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Test",
            foundation_ein="98-7654321",
            foundation_name="Test",
            composite_score=52.5,
            confidence=0.7,
            abstain_reason="True borderline",
            component_scores={}
        )

        assert item.priority == TriagePriority.MEDIUM

    def test_low_priority_lower_borderline(self):
        """Test LOW priority for scores 45-50"""
        queue = TriageQueue()

        item = queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Test",
            foundation_ein="98-7654321",
            foundation_name="Test",
            composite_score=47.0,
            confidence=0.7,
            abstain_reason="Lower borderline",
            component_scores={}
        )

        assert item.priority == TriagePriority.LOW

    def test_priority_ordering(self):
        """Test that items are retrieved in priority order"""
        queue = TriageQueue()

        # Add items in mixed priority order
        low_item = queue.add_to_queue(
            profile_ein="12-0000001",
            profile_name="Low",
            foundation_ein="98-0000001",
            foundation_name="Low",
            composite_score=47.0,
            confidence=0.7,
            abstain_reason="Low",
            component_scores={}
        )

        critical_item = queue.add_to_queue(
            profile_ein="12-0000002",
            profile_name="Critical",
            foundation_ein="98-0000002",
            foundation_name="Critical",
            composite_score=52.0,
            confidence=0.7,
            abstain_reason="Missing critical data",
            component_scores={}
        )

        medium_item = queue.add_to_queue(
            profile_ein="12-0000003",
            profile_name="Medium",
            foundation_ein="98-0000003",
            foundation_name="Medium",
            composite_score=52.0,
            confidence=0.7,
            abstain_reason="Borderline",
            component_scores={}
        )

        # Should retrieve in order: CRITICAL > HIGH > MEDIUM > LOW
        next_item = queue.get_next_for_review()
        assert next_item.item_id == critical_item.item_id


# ============================================================================
# Test Class 3: Review Workflow
# ============================================================================

class TestReviewWorkflow:
    """Test review workflow operations"""

    def test_get_next_for_review(self):
        """Test getting next item for review"""
        queue = TriageQueue()

        item = queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Test",
            foundation_ein="98-7654321",
            foundation_name="Test",
            composite_score=50.0,
            confidence=0.7,
            abstain_reason="Test",
            component_scores={}
        )

        next_item = queue.get_next_for_review(analyst_id="analyst1")

        assert next_item is not None
        assert next_item.item_id == item.item_id
        assert next_item.status == TriageStatus.IN_REVIEW
        assert next_item.assigned_to == "analyst1"

    def test_get_next_empty_queue(self):
        """Test getting next item from empty queue"""
        queue = TriageQueue()

        next_item = queue.get_next_for_review()
        assert next_item is None

    def test_get_next_with_priority_filter(self):
        """Test filtering by priority when getting next item"""
        queue = TriageQueue()

        # Add low priority item
        low_item = queue.add_to_queue(
            profile_ein="12-0000001",
            profile_name="Low",
            foundation_ein="98-0000001",
            foundation_name="Low",
            composite_score=47.0,
            confidence=0.7,
            abstain_reason="Low",
            component_scores={}
        )

        # Add high priority item
        high_item = queue.add_to_queue(
            profile_ein="12-0000002",
            profile_name="High",
            foundation_ein="98-0000002",
            foundation_name="High",
            composite_score=56.0,
            confidence=0.7,
            abstain_reason="High",
            component_scores={}
        )

        # Filter for HIGH priority only
        next_item = queue.get_next_for_review(priority_filter=TriagePriority.HIGH)
        assert next_item.item_id == high_item.item_id

        # Filter for MEDIUM priority (none available)
        next_item = queue.get_next_for_review(priority_filter=TriagePriority.MEDIUM)
        assert next_item is None

    def test_submit_review_pass(self):
        """Test submitting PASS decision"""
        queue = TriageQueue()

        item = queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Test",
            foundation_ein="98-7654321",
            foundation_name="Test",
            composite_score=56.0,
            confidence=0.7,
            abstain_reason="Test",
            component_scores={}
        )

        # Get for review
        queue.get_next_for_review(analyst_id="analyst1")

        # Submit PASS decision
        success = queue.submit_review(
            item_id=item.item_id,
            decision=ExpertDecision.PASS,
            rationale="Strong NTEE match after manual verification",
            reviewer_id="analyst1"
        )

        assert success is True
        assert item.expert_decision == ExpertDecision.PASS
        assert item.status == TriageStatus.APPROVED
        assert item.reviewed_by == "analyst1"
        assert item.reviewed_at is not None
        assert len(queue.review_history) == 1
        assert item.item_id not in queue.queue  # Removed from active queue

    def test_submit_review_fail(self):
        """Test submitting FAIL decision"""
        queue = TriageQueue()

        item = queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Test",
            foundation_ein="98-7654321",
            foundation_name="Test",
            composite_score=47.0,
            confidence=0.7,
            abstain_reason="Test",
            component_scores={}
        )

        queue.get_next_for_review()

        success = queue.submit_review(
            item_id=item.item_id,
            decision=ExpertDecision.FAIL,
            rationale="Geographic mismatch confirmed",
            reviewer_id="analyst1"
        )

        assert success is True
        assert item.expert_decision == ExpertDecision.FAIL
        assert item.status == TriageStatus.REJECTED

    def test_submit_review_uncertain(self):
        """Test submitting UNCERTAIN decision (escalation)"""
        queue = TriageQueue()

        item = queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Test",
            foundation_ein="98-7654321",
            foundation_name="Test",
            composite_score=52.0,
            confidence=0.7,
            abstain_reason="Test",
            component_scores={}
        )

        queue.get_next_for_review()

        success = queue.submit_review(
            item_id=item.item_id,
            decision=ExpertDecision.UNCERTAIN,
            rationale="Needs senior analyst review",
            reviewer_id="analyst1"
        )

        assert success is True
        assert item.expert_decision == ExpertDecision.UNCERTAIN
        assert item.status == TriageStatus.ESCALATED

    def test_submit_review_invalid_item(self):
        """Test submitting review for non-existent item"""
        queue = TriageQueue()

        success = queue.submit_review(
            item_id="invalid_id",
            decision=ExpertDecision.PASS,
            rationale="Test",
            reviewer_id="analyst1"
        )

        assert success is False


# ============================================================================
# Test Class 4: Statistics
# ============================================================================

class TestStatistics:
    """Test queue statistics calculation"""

    def test_empty_queue_stats(self):
        """Test stats for empty queue"""
        queue = TriageQueue()

        stats = queue.get_queue_stats()

        assert stats.total_items == 0
        assert stats.pending_count == 0
        assert stats.approved_count == 0
        assert stats.rejected_count == 0
        assert stats.avg_review_time_hours == 0.0
        assert stats.approval_rate == 0.0

    def test_queue_stats_counts(self):
        """Test basic count statistics"""
        queue = TriageQueue()

        # Add 3 pending items
        for i in range(3):
            queue.add_to_queue(
                profile_ein=f"12-000000{i}",
                profile_name=f"Test{i}",
                foundation_ein=f"98-000000{i}",
                foundation_name=f"Test{i}",
                composite_score=50.0,
                confidence=0.7,
                abstain_reason="Test",
                component_scores={}
            )

        # Review 1 item (PASS)
        item1 = queue.get_next_for_review()
        queue.submit_review(
            item_id=item1.item_id,
            decision=ExpertDecision.PASS,
            rationale="Test",
            reviewer_id="analyst1"
        )

        # Review 1 item (FAIL)
        item2 = queue.get_next_for_review()
        queue.submit_review(
            item_id=item2.item_id,
            decision=ExpertDecision.FAIL,
            rationale="Test",
            reviewer_id="analyst1"
        )

        stats = queue.get_queue_stats()

        assert stats.total_items == 3
        assert stats.pending_count == 1
        assert stats.in_review_count == 0
        assert stats.approved_count == 1
        assert stats.rejected_count == 1

    def test_priority_counts(self):
        """Test priority breakdown statistics"""
        queue = TriageQueue()

        # Add items with different priorities
        queue.add_to_queue(
            profile_ein="12-0000001",
            profile_name="Critical",
            foundation_ein="98-0000001",
            foundation_name="Critical",
            composite_score=52.0,
            confidence=0.7,
            abstain_reason="Missing critical data",
            component_scores={}
        )

        queue.add_to_queue(
            profile_ein="12-0000002",
            profile_name="High",
            foundation_ein="98-0000002",
            foundation_name="High",
            composite_score=56.0,
            confidence=0.7,
            abstain_reason="High",
            component_scores={}
        )

        queue.add_to_queue(
            profile_ein="12-0000003",
            profile_name="Medium",
            foundation_ein="98-0000003",
            foundation_name="Medium",
            composite_score=52.0,
            confidence=0.7,
            abstain_reason="Medium",
            component_scores={}
        )

        queue.add_to_queue(
            profile_ein="12-0000004",
            profile_name="Low",
            foundation_ein="98-0000004",
            foundation_name="Low",
            composite_score=47.0,
            confidence=0.7,
            abstain_reason="Low",
            component_scores={}
        )

        stats = queue.get_queue_stats()

        assert stats.critical_count == 1
        assert stats.high_count == 1
        assert stats.medium_count == 1
        assert stats.low_count == 1

    def test_approval_rate_calculation(self):
        """Test approval rate metric"""
        queue = TriageQueue()

        # Add 4 items
        for i in range(4):
            item = queue.add_to_queue(
                profile_ein=f"12-000000{i}",
                profile_name=f"Test{i}",
                foundation_ein=f"98-000000{i}",
                foundation_name=f"Test{i}",
                composite_score=50.0,
                confidence=0.7,
                abstain_reason="Test",
                component_scores={}
            )

        # Approve 3, reject 1
        for i in range(3):
            item = queue.get_next_for_review()
            queue.submit_review(
                item_id=item.item_id,
                decision=ExpertDecision.PASS,
                rationale="Test",
                reviewer_id="analyst1"
            )

        item = queue.get_next_for_review()
        queue.submit_review(
            item_id=item.item_id,
            decision=ExpertDecision.FAIL,
            rationale="Test",
            reviewer_id="analyst1"
        )

        stats = queue.get_queue_stats()

        # 3 approved out of 4 reviewed = 75%
        assert stats.approval_rate == 0.75

    def test_agreement_rate_calculation(self):
        """Test agreement rate metric"""
        queue = TriageQueue()

        # Add high score item (should PASS)
        high_item = queue.add_to_queue(
            profile_ein="12-0000001",
            profile_name="High",
            foundation_ein="98-0000001",
            foundation_name="High",
            composite_score=56.0,  # Above 52.5 threshold
            confidence=0.7,
            abstain_reason="Test",
            component_scores={}
        )

        # Add low score item (should FAIL)
        low_item = queue.add_to_queue(
            profile_ein="12-0000002",
            profile_name="Low",
            foundation_ein="98-0000002",
            foundation_name="Low",
            composite_score=48.0,  # Below 52.5 threshold
            confidence=0.7,
            abstain_reason="Test",
            component_scores={}
        )

        # Review with expected decisions (agreement)
        item1 = queue.get_next_for_review()
        queue.submit_review(
            item_id=item1.item_id,
            decision=ExpertDecision.PASS,  # Agrees with high score
            rationale="Test",
            reviewer_id="analyst1"
        )

        item2 = queue.get_next_for_review()
        queue.submit_review(
            item_id=item2.item_id,
            decision=ExpertDecision.FAIL,  # Agrees with low score
            rationale="Test",
            reviewer_id="analyst1"
        )

        stats = queue.get_queue_stats()

        # Both decisions agree with score expectations
        assert stats.agreement_rate == 1.0


# ============================================================================
# Test Class 5: Export
# ============================================================================

class TestExport:
    """Test JSON export functionality"""

    def test_export_pending_items(self):
        """Test exporting pending items to JSON"""
        import json

        queue = TriageQueue()

        queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Test Nonprofit",
            foundation_ein="98-7654321",
            foundation_name="Test Foundation",
            composite_score=52.0,
            confidence=0.75,
            abstain_reason="Borderline match",
            component_scores={
                'ntee': 45.0,
                'geographic': 60.0,
                'coherence': 50.0,
                'grant_size': 55.0
            },
            tags=["education"]
        )

        export_json = queue.export_for_review()
        export_data = json.loads(export_json)

        assert len(export_data) == 1
        assert export_data[0]['profile_name'] == "Test Nonprofit"
        assert export_data[0]['composite_score'] == 52.0
        assert export_data[0]['priority'] == 'medium'
        assert export_data[0]['tags'] == ["education"]

    def test_export_with_priority_filter(self):
        """Test exporting with priority filter"""
        import json

        queue = TriageQueue()

        # Add high priority
        queue.add_to_queue(
            profile_ein="12-0000001",
            profile_name="High",
            foundation_ein="98-0000001",
            foundation_name="High",
            composite_score=56.0,
            confidence=0.7,
            abstain_reason="High",
            component_scores={}
        )

        # Add low priority
        queue.add_to_queue(
            profile_ein="12-0000002",
            profile_name="Low",
            foundation_ein="98-0000002",
            foundation_name="Low",
            composite_score=47.0,
            confidence=0.7,
            abstain_reason="Low",
            component_scores={}
        )

        # Export only HIGH priority
        export_json = queue.export_for_review(priority_filter=TriagePriority.HIGH)
        export_data = json.loads(export_json)

        assert len(export_data) == 1
        assert export_data[0]['priority'] == 'high'

    def test_export_excludes_completed_reviews(self):
        """Test that export excludes completed reviews"""
        import json

        queue = TriageQueue()

        item = queue.add_to_queue(
            profile_ein="12-3456789",
            profile_name="Test",
            foundation_ein="98-7654321",
            foundation_name="Test",
            composite_score=50.0,
            confidence=0.7,
            abstain_reason="Test",
            component_scores={}
        )

        # Complete review
        queue.get_next_for_review()
        queue.submit_review(
            item_id=item.item_id,
            decision=ExpertDecision.PASS,
            rationale="Test",
            reviewer_id="analyst1"
        )

        # Export should be empty (no pending/in_review items)
        export_json = queue.export_for_review()
        export_data = json.loads(export_json)

        assert len(export_data) == 0


# ============================================================================
# Test Class 6: Singleton Pattern
# ============================================================================

class TestSingletonPattern:
    """Test global triage queue singleton"""

    def test_singleton_instance(self):
        """Test that get_triage_queue returns singleton"""
        queue1 = get_triage_queue()
        queue2 = get_triage_queue()

        # Should be same instance
        assert queue1 is queue2


# ============================================================================
# Test Class 7: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_oldest_first_within_priority(self):
        """Test that within same priority, oldest items come first"""
        queue = TriageQueue()

        # Add two items with same priority (delay between them)
        item1 = queue.add_to_queue(
            profile_ein="12-0000001",
            profile_name="First",
            foundation_ein="98-0000001",
            foundation_name="First",
            composite_score=52.0,
            confidence=0.7,
            abstain_reason="Test",
            component_scores={}
        )

        import time
        time.sleep(0.01)  # Small delay to ensure different timestamps

        item2 = queue.add_to_queue(
            profile_ein="12-0000002",
            profile_name="Second",
            foundation_ein="98-0000002",
            foundation_name="Second",
            composite_score=52.0,
            confidence=0.7,
            abstain_reason="Test",
            component_scores={}
        )

        # Should get older item first
        next_item = queue.get_next_for_review()
        assert next_item.item_id == item1.item_id

    def test_skip_in_review_items(self):
        """Test that already in-review items are skipped"""
        queue = TriageQueue()

        item1 = queue.add_to_queue(
            profile_ein="12-0000001",
            profile_name="First",
            foundation_ein="98-0000001",
            foundation_name="First",
            composite_score=52.0,
            confidence=0.7,
            abstain_reason="Test",
            component_scores={}
        )

        item2 = queue.add_to_queue(
            profile_ein="12-0000002",
            profile_name="Second",
            foundation_ein="98-0000002",
            foundation_name="Second",
            composite_score=52.0,
            confidence=0.7,
            abstain_reason="Test",
            component_scores={}
        )

        # Get first item
        first = queue.get_next_for_review()
        assert first.item_id == item1.item_id

        # Get second item (should skip item1 which is IN_REVIEW)
        second = queue.get_next_for_review()
        assert second.item_id == item2.item_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
