"""
Abstain/Triage Queue System (V2.0)

Manual review queue for borderline 990-PF screening results (scores 45-58).
Enables human-in-the-loop validation and continuous learning from expert decisions.

Key Concepts:
- **Abstain Decision**: Composite scorer identifies uncertain matches
- **Triage Queue**: Holds candidates needing manual review
- **Expert Review**: Human analyst makes final PASS/FAIL decision
- **Feedback Loop**: Expert decisions improve future scoring thresholds

Phase 3, Week 6 Implementation
Expected Impact: 15-20% reduction in false positives/negatives through human validation
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import json


logger = logging.getLogger(__name__)


class TriageStatus(str, Enum):
    """Status of triage queue item"""
    PENDING = "pending"          # Awaiting review
    IN_REVIEW = "in_review"      # Currently being reviewed
    APPROVED = "approved"        # Expert decided PASS
    REJECTED = "rejected"        # Expert decided FAIL
    ESCALATED = "escalated"      # Needs senior review
    DEFERRED = "deferred"        # Postponed for later


class TriagePriority(str, Enum):
    """Priority level for manual review"""
    CRITICAL = "critical"    # High confidence but critical data missing
    HIGH = "high"            # Borderline high score (55-58)
    MEDIUM = "medium"        # True borderline (50-55)
    LOW = "low"              # Borderline low score (45-50)


class ExpertDecision(str, Enum):
    """Expert's final decision"""
    PASS = "pass"            # Recommend this foundation
    FAIL = "fail"            # Do not recommend
    UNCERTAIN = "uncertain"  # Still unclear, need more data


@dataclass
class TriageItem:
    """Single item in the triage queue"""
    # Identification
    item_id: str
    profile_ein: str
    profile_name: str
    foundation_ein: str
    foundation_name: str

    # Scoring data
    composite_score: float  # 45-58 range typically
    confidence: float  # 0.0-1.0
    abstain_reason: str

    # Component scores (for analyst context)
    ntee_score: float
    geographic_score: float
    coherence_score: float
    grant_size_score: float

    # Triage metadata
    status: TriageStatus = TriageStatus.PENDING
    priority: TriagePriority = TriagePriority.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None

    # Expert review
    expert_decision: Optional[ExpertDecision] = None
    expert_rationale: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

    # Additional context
    notes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class TriageQueueStats:
    """Statistics for triage queue"""
    total_items: int
    pending_count: int
    in_review_count: int
    approved_count: int
    rejected_count: int

    # Priority breakdown
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int

    # Performance metrics
    avg_review_time_hours: float
    approval_rate: float  # % of reviewed items approved
    agreement_rate: float  # % where expert agrees with borderline score


class TriageQueue:
    """
    Manual review queue for abstain decisions

    Workflow:
    1. Composite scorer identifies borderline match (score 45-58)
    2. Create TriageItem and add to queue
    3. Assign priority based on score and confidence
    4. Analyst reviews item with full context
    5. Expert makes PASS/FAIL decision
    6. Decision logged for feedback loop

    Storage:
    - In-memory queue for active items
    - Database persistence for history (TODO)
    - Export to JSON for review dashboards
    """

    def __init__(self):
        """Initialize triage queue"""
        self.logger = logging.getLogger(f"{__name__}.TriageQueue")
        self.queue: Dict[str, TriageItem] = {}
        self.review_history: List[TriageItem] = []

    def add_to_queue(self,
                     profile_ein: str,
                     profile_name: str,
                     foundation_ein: str,
                     foundation_name: str,
                     composite_score: float,
                     confidence: float,
                     abstain_reason: str,
                     component_scores: Dict[str, float],
                     tags: Optional[List[str]] = None) -> TriageItem:
        """
        Add abstain decision to triage queue

        Args:
            profile_ein: Applicant organization EIN
            profile_name: Applicant organization name
            foundation_ein: Foundation EIN
            foundation_name: Foundation name
            composite_score: Final composite score (typically 45-58)
            confidence: Confidence in score (0.0-1.0)
            abstain_reason: Why this was sent to manual review
            component_scores: Dict of individual component scores
            tags: Optional tags for categorization

        Returns:
            Created TriageItem
        """
        # Generate unique ID
        item_id = f"{profile_ein}_{foundation_ein}_{int(datetime.now().timestamp())}"

        # Determine priority
        priority = self._determine_priority(composite_score, confidence, abstain_reason)

        # Create triage item
        item = TriageItem(
            item_id=item_id,
            profile_ein=profile_ein,
            profile_name=profile_name,
            foundation_ein=foundation_ein,
            foundation_name=foundation_name,
            composite_score=composite_score,
            confidence=confidence,
            abstain_reason=abstain_reason,
            ntee_score=component_scores.get('ntee', 0.0),
            geographic_score=component_scores.get('geographic', 0.0),
            coherence_score=component_scores.get('coherence', 0.0),
            grant_size_score=component_scores.get('grant_size', 0.0),
            priority=priority,
            tags=tags or [],
        )

        # Add to queue
        self.queue[item_id] = item

        self.logger.info(
            f"Added to triage queue: {foundation_name} for {profile_name} "
            f"(score={composite_score:.1f}, priority={priority.value})"
        )

        return item

    def _determine_priority(self,
                           score: float,
                           confidence: float,
                           reason: str) -> TriagePriority:
        """
        Determine priority for manual review

        Logic:
        - CRITICAL: Missing critical data but otherwise strong
        - HIGH: Borderline high (55-58) - likely to pass
        - MEDIUM: True borderline (50-55) - unclear
        - LOW: Borderline low (45-50) - likely to fail
        """
        # Critical if missing data but decent score
        if "missing" in reason.lower() and score >= 50.0:
            return TriagePriority.CRITICAL

        # High priority for upper borderline
        if score >= 55.0:
            return TriagePriority.HIGH

        # Medium for true borderline
        if 50.0 <= score < 55.0:
            return TriagePriority.MEDIUM

        # Low for lower borderline
        return TriagePriority.LOW

    def get_next_for_review(self,
                           analyst_id: Optional[str] = None,
                           priority_filter: Optional[TriagePriority] = None) -> Optional[TriageItem]:
        """
        Get next item for manual review (highest priority first)

        Args:
            analyst_id: Optional analyst ID to assign item to
            priority_filter: Optional filter by priority level

        Returns:
            Next TriageItem or None if queue empty
        """
        # Filter to pending items
        pending_items = [
            item for item in self.queue.values()
            if item.status == TriageStatus.PENDING
        ]

        # Apply priority filter if specified
        if priority_filter:
            pending_items = [
                item for item in pending_items
                if item.priority == priority_filter
            ]

        if not pending_items:
            return None

        # Sort by priority (CRITICAL > HIGH > MEDIUM > LOW)
        priority_order = {
            TriagePriority.CRITICAL: 0,
            TriagePriority.HIGH: 1,
            TriagePriority.MEDIUM: 2,
            TriagePriority.LOW: 3,
        }

        pending_items.sort(key=lambda x: (
            priority_order[x.priority],
            x.created_at  # Oldest first within same priority
        ))

        # Get first item
        item = pending_items[0]

        # Mark as in review
        item.status = TriageStatus.IN_REVIEW
        if analyst_id:
            item.assigned_to = analyst_id

        self.logger.info(
            f"Assigned for review: {item.foundation_name} for {item.profile_name} "
            f"(priority={item.priority.value}, analyst={analyst_id})"
        )

        return item

    def submit_review(self,
                     item_id: str,
                     decision: ExpertDecision,
                     rationale: str,
                     reviewer_id: str) -> bool:
        """
        Submit expert review decision

        Args:
            item_id: Triage item ID
            decision: Expert's PASS/FAIL/UNCERTAIN decision
            rationale: Explanation for decision
            reviewer_id: Reviewer's identifier

        Returns:
            True if successful, False if item not found
        """
        if item_id not in self.queue:
            self.logger.error(f"Triage item not found: {item_id}")
            return False

        item = self.queue[item_id]

        # Update review fields
        item.expert_decision = decision
        item.expert_rationale = rationale
        item.reviewed_by = reviewer_id
        item.reviewed_at = datetime.now()

        # Update status based on decision
        if decision == ExpertDecision.PASS:
            item.status = TriageStatus.APPROVED
        elif decision == ExpertDecision.FAIL:
            item.status = TriageStatus.REJECTED
        elif decision == ExpertDecision.UNCERTAIN:
            item.status = TriageStatus.ESCALATED

        # Move to history
        self.review_history.append(item)
        del self.queue[item_id]

        self.logger.info(
            f"Review submitted: {item.foundation_name} for {item.profile_name} "
            f"(decision={decision.value}, reviewer={reviewer_id})"
        )

        return True

    def get_queue_stats(self) -> TriageQueueStats:
        """Calculate statistics for triage queue"""
        all_items = list(self.queue.values()) + self.review_history

        # Count by status
        pending = sum(1 for i in self.queue.values() if i.status == TriageStatus.PENDING)
        in_review = sum(1 for i in self.queue.values() if i.status == TriageStatus.IN_REVIEW)
        approved = sum(1 for i in self.review_history if i.status == TriageStatus.APPROVED)
        rejected = sum(1 for i in self.review_history if i.status == TriageStatus.REJECTED)

        # Count by priority (pending only)
        pending_items = [i for i in self.queue.values() if i.status == TriageStatus.PENDING]
        critical = sum(1 for i in pending_items if i.priority == TriagePriority.CRITICAL)
        high = sum(1 for i in pending_items if i.priority == TriagePriority.HIGH)
        medium = sum(1 for i in pending_items if i.priority == TriagePriority.MEDIUM)
        low = sum(1 for i in pending_items if i.priority == TriagePriority.LOW)

        # Calculate metrics
        reviewed_items = [i for i in self.review_history if i.reviewed_at]

        if reviewed_items:
            # Average review time
            review_times = [
                (i.reviewed_at - i.created_at).total_seconds() / 3600
                for i in reviewed_items
            ]
            avg_review_time = sum(review_times) / len(review_times)

            # Approval rate
            approval_rate = approved / len(reviewed_items) if reviewed_items else 0.0

            # Agreement rate (expert agrees with borderline score)
            # Score 55-58 should mostly pass, 45-50 should mostly fail
            agreements = 0
            for item in reviewed_items:
                if item.expert_decision == ExpertDecision.PASS and item.composite_score >= 52.5:
                    agreements += 1
                elif item.expert_decision == ExpertDecision.FAIL and item.composite_score < 52.5:
                    agreements += 1
            agreement_rate = agreements / len(reviewed_items)
        else:
            avg_review_time = 0.0
            approval_rate = 0.0
            agreement_rate = 0.0

        return TriageQueueStats(
            total_items=len(all_items),
            pending_count=pending,
            in_review_count=in_review,
            approved_count=approved,
            rejected_count=rejected,
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            avg_review_time_hours=avg_review_time,
            approval_rate=approval_rate,
            agreement_rate=agreement_rate,
        )

    def export_for_review(self,
                         priority_filter: Optional[TriagePriority] = None) -> str:
        """
        Export queue items to JSON for review dashboard

        Args:
            priority_filter: Optional filter by priority

        Returns:
            JSON string of queue items
        """
        items = [
            item for item in self.queue.values()
            if item.status in [TriageStatus.PENDING, TriageStatus.IN_REVIEW]
        ]

        if priority_filter:
            items = [i for i in items if i.priority == priority_filter]

        # Sort by priority
        priority_order = {
            TriagePriority.CRITICAL: 0,
            TriagePriority.HIGH: 1,
            TriagePriority.MEDIUM: 2,
            TriagePriority.LOW: 3,
        }
        items.sort(key=lambda x: (priority_order[x.priority], x.created_at))

        # Convert to JSON-serializable format
        items_data = []
        for item in items:
            items_data.append({
                'item_id': item.item_id,
                'profile_ein': item.profile_ein,
                'profile_name': item.profile_name,
                'foundation_ein': item.foundation_ein,
                'foundation_name': item.foundation_name,
                'composite_score': item.composite_score,
                'confidence': item.confidence,
                'abstain_reason': item.abstain_reason,
                'component_scores': {
                    'ntee': item.ntee_score,
                    'geographic': item.geographic_score,
                    'coherence': item.coherence_score,
                    'grant_size': item.grant_size_score,
                },
                'priority': item.priority.value,
                'status': item.status.value,
                'created_at': item.created_at.isoformat(),
                'assigned_to': item.assigned_to,
                'tags': item.tags,
            })

        return json.dumps(items_data, indent=2)


# Global triage queue instance
_triage_queue = None


def get_triage_queue() -> TriageQueue:
    """Get global triage queue instance (singleton)"""
    global _triage_queue
    if _triage_queue is None:
        _triage_queue = TriageQueue()
    return _triage_queue
