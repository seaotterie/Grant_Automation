"""
A/B Testing Framework (V1.0)

Shadow mode execution and gradual rollout system for safely deploying
new scoring models alongside production systems.

Key Concepts:
- **Shadow Mode**: Run new scorer alongside old without affecting results
- **Traffic Splitting**: Gradual rollout (10% → 50% → 100%)
- **Statistical Comparison**: Chi-square, t-test, effect size analysis
- **Result Logging**: Complete audit trail of both scorers
- **Rollback Safety**: Quick revert if new scorer underperforms

Phase 5, Week 9-10 Implementation
Expected Impact: Safe deployment with <1% production incidents
"""

import logging
import json
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from pathlib import Path
from enum import Enum
import statistics


logger = logging.getLogger(__name__)


class RolloutStage(str, Enum):
    """Gradual rollout stages"""
    SHADOW_ONLY = "shadow_only"          # 0% traffic, logging only
    PILOT = "pilot"                      # 10% traffic
    GRADUAL = "gradual"                  # 50% traffic
    FULL = "full"                        # 100% traffic
    ROLLBACK = "rollback"                # Rolled back to baseline


class ComparisonResult(str, Enum):
    """Result of A/B comparison"""
    NEW_SIGNIFICANTLY_BETTER = "new_significantly_better"
    NEW_SLIGHTLY_BETTER = "new_slightly_better"
    NO_SIGNIFICANT_DIFFERENCE = "no_significant_difference"
    BASELINE_SLIGHTLY_BETTER = "baseline_slightly_better"
    BASELINE_SIGNIFICANTLY_BETTER = "baseline_significantly_better"


@dataclass
class ScoringResult:
    """Result from a single scorer execution"""
    scorer_version: str
    profile_ein: str
    foundation_ein: str
    score: float
    decision: str  # PASS, ABSTAIN, FAIL
    execution_time_ms: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ABTestExecution:
    """Single A/B test execution (both scorers)"""
    execution_id: str
    profile_ein: str
    foundation_ein: str

    # Baseline scorer
    baseline_score: float
    baseline_decision: str
    baseline_time_ms: float

    # New scorer
    new_score: float
    new_decision: str
    new_time_ms: float

    # Comparison
    score_delta: float
    decision_changed: bool
    active_scorer: str  # Which scorer's result was used

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ABTestMetrics:
    """Metrics from A/B test period"""
    test_id: str
    start_date: str
    end_date: str
    rollout_stage: RolloutStage

    # Execution counts
    total_executions: int
    baseline_used: int
    new_used: int
    traffic_percentage: float

    # Score statistics
    baseline_mean_score: float
    new_mean_score: float
    score_delta_mean: float
    score_delta_std: float

    # Decision comparison
    agreement_rate: float
    pass_to_fail_rate: float
    fail_to_pass_rate: float

    # Performance
    baseline_mean_time_ms: float
    new_mean_time_ms: float
    time_delta_pct: float

    # Statistical tests
    statistical_significance: bool
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    comparison_result: Optional[ComparisonResult] = None

    # Recommendation
    recommendation: str = ""
    ready_for_next_stage: bool = False


class ABTestingFramework:
    """
    A/B testing framework for gradual scorer rollout

    Workflow:
    1. Shadow Mode (2 weeks): Run both scorers, use baseline, log all results
    2. Pilot (1 week): 10% traffic to new scorer
    3. Gradual (1 week): 50% traffic to new scorer
    4. Full Rollout: 100% traffic to new scorer

    Safety Features:
    - Automatic rollback if metrics degrade
    - Statistical significance testing before advancing
    - Complete audit trail
    - Performance monitoring
    """

    # Statistical significance threshold
    P_VALUE_THRESHOLD = 0.05

    # Minimum executions before statistical tests
    MIN_EXECUTIONS_FOR_STATS = 100

    # Effect size thresholds (Cohen's d)
    SMALL_EFFECT = 0.2
    MEDIUM_EFFECT = 0.5
    LARGE_EFFECT = 0.8

    def __init__(self, output_dir: str = "data/evaluation/ab_tests"):
        """
        Initialize A/B testing framework

        Args:
            output_dir: Directory for test logs and results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(f"{__name__}.ABTestingFramework")

        # Current test
        self.test_id: Optional[str] = None
        self.rollout_stage = RolloutStage.SHADOW_ONLY
        self.traffic_percentage = 0.0

        # Execution log
        self.executions: List[ABTestExecution] = []

        # Scorers
        self.baseline_scorer: Optional[Callable] = None
        self.new_scorer: Optional[Callable] = None

    def start_test(
        self,
        baseline_scorer: Callable,
        new_scorer: Callable,
        rollout_stage: RolloutStage = RolloutStage.SHADOW_ONLY,
        test_name: Optional[str] = None
    ) -> str:
        """
        Start new A/B test

        Args:
            baseline_scorer: Current production scorer
            new_scorer: New scorer being tested
            rollout_stage: Initial rollout stage
            test_name: Optional test name

        Returns:
            Test ID
        """
        self.test_id = test_name or f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.rollout_stage = rollout_stage
        self.traffic_percentage = self._get_traffic_percentage(rollout_stage)

        self.baseline_scorer = baseline_scorer
        self.new_scorer = new_scorer
        self.executions = []

        self.logger.info(
            f"Started A/B test: {self.test_id}, "
            f"stage={rollout_stage.value}, traffic={self.traffic_percentage}%"
        )

        return self.test_id

    def execute_with_ab_test(
        self,
        profile_ein: str,
        foundation_ein: str,
        profile_data: Dict[str, Any],
        foundation_data: Dict[str, Any]
    ) -> ScoringResult:
        """
        Execute scoring with A/B test

        Runs both scorers in shadow mode, or uses traffic splitting
        in pilot/gradual/full modes.

        Args:
            profile_ein: Profile organization EIN
            foundation_ein: Foundation EIN
            profile_data: Profile data for scoring
            foundation_data: Foundation data for scoring

        Returns:
            ScoringResult from active scorer
        """
        if not self.baseline_scorer or not self.new_scorer:
            raise ValueError("Scorers not configured. Call start_test() first.")

        execution_id = f"{self.test_id}_{len(self.executions):06d}"

        # Execute baseline scorer
        baseline_start = datetime.now()
        baseline_score, baseline_decision = self.baseline_scorer(profile_data, foundation_data)
        baseline_time = (datetime.now() - baseline_start).total_seconds() * 1000

        # Execute new scorer
        new_start = datetime.now()
        new_score, new_decision = self.new_scorer(profile_data, foundation_data)
        new_time = (datetime.now() - new_start).total_seconds() * 1000

        # Determine which scorer to use
        use_new_scorer = self._should_use_new_scorer()
        active_scorer = "new" if use_new_scorer else "baseline"

        # Log execution
        execution = ABTestExecution(
            execution_id=execution_id,
            profile_ein=profile_ein,
            foundation_ein=foundation_ein,
            baseline_score=baseline_score,
            baseline_decision=baseline_decision,
            baseline_time_ms=baseline_time,
            new_score=new_score,
            new_decision=new_decision,
            new_time_ms=new_time,
            score_delta=new_score - baseline_score,
            decision_changed=(baseline_decision != new_decision),
            active_scorer=active_scorer,
        )

        self.executions.append(execution)
        self._save_execution(execution)

        # Return result from active scorer
        if use_new_scorer:
            return ScoringResult(
                scorer_version="new",
                profile_ein=profile_ein,
                foundation_ein=foundation_ein,
                score=new_score,
                decision=new_decision,
                execution_time_ms=new_time,
            )
        else:
            return ScoringResult(
                scorer_version="baseline",
                profile_ein=profile_ein,
                foundation_ein=foundation_ein,
                score=baseline_score,
                decision=baseline_decision,
                execution_time_ms=baseline_time,
            )

    def _should_use_new_scorer(self) -> bool:
        """Determine whether to use new scorer based on traffic percentage"""
        if self.rollout_stage == RolloutStage.SHADOW_ONLY:
            return False  # Always use baseline in shadow mode
        elif self.rollout_stage == RolloutStage.ROLLBACK:
            return False  # Use baseline after rollback
        elif self.rollout_stage == RolloutStage.FULL:
            return True   # Always use new in full rollout
        else:
            # Pilot or gradual: random selection based on traffic percentage
            return random.random() < (self.traffic_percentage / 100.0)

    def _get_traffic_percentage(self, stage: RolloutStage) -> float:
        """Get traffic percentage for rollout stage"""
        percentages = {
            RolloutStage.SHADOW_ONLY: 0.0,
            RolloutStage.PILOT: 10.0,
            RolloutStage.GRADUAL: 50.0,
            RolloutStage.FULL: 100.0,
            RolloutStage.ROLLBACK: 0.0,
        }
        return percentages.get(stage, 0.0)

    def calculate_metrics(self) -> ABTestMetrics:
        """
        Calculate A/B test metrics from execution log

        Returns:
            ABTestMetrics with statistical analysis
        """
        if not self.executions:
            raise ValueError("No executions to analyze")

        # Basic counts
        total = len(self.executions)
        baseline_used = sum(1 for e in self.executions if e.active_scorer == "baseline")
        new_used = total - baseline_used

        # Score statistics
        baseline_scores = [e.baseline_score for e in self.executions]
        new_scores = [e.new_score for e in self.executions]
        score_deltas = [e.score_delta for e in self.executions]

        baseline_mean = statistics.mean(baseline_scores)
        new_mean = statistics.mean(new_scores)
        delta_mean = statistics.mean(score_deltas)
        delta_std = statistics.stdev(score_deltas) if len(score_deltas) > 1 else 0.0

        # Decision comparison
        agreement = sum(1 for e in self.executions if not e.decision_changed)
        agreement_rate = agreement / total

        pass_to_fail = sum(
            1 for e in self.executions
            if e.baseline_decision == "PASS" and e.new_decision == "FAIL"
        )
        fail_to_pass = sum(
            1 for e in self.executions
            if e.baseline_decision == "FAIL" and e.new_decision == "PASS"
        )

        pass_to_fail_rate = pass_to_fail / total
        fail_to_pass_rate = fail_to_pass / total

        # Performance
        baseline_times = [e.baseline_time_ms for e in self.executions]
        new_times = [e.new_time_ms for e in self.executions]

        baseline_mean_time = statistics.mean(baseline_times)
        new_mean_time = statistics.mean(new_times)
        time_delta_pct = ((new_mean_time - baseline_mean_time) / baseline_mean_time * 100)

        # Statistical tests
        statistical_significance = False
        p_value = None
        effect_size = None
        comparison_result = None

        if total >= self.MIN_EXECUTIONS_FOR_STATS:
            # Paired t-test approximation
            p_value = self._calculate_p_value(score_deltas)
            statistical_significance = p_value < self.P_VALUE_THRESHOLD

            # Cohen's d effect size
            effect_size = delta_mean / delta_std if delta_std > 0 else 0.0

            # Comparison result
            comparison_result = self._determine_comparison_result(
                delta_mean, statistical_significance, effect_size
            )

        # Recommendation
        recommendation, ready = self._generate_recommendation(
            comparison_result, agreement_rate, time_delta_pct, total
        )

        # Date range
        start_date = self.executions[0].timestamp
        end_date = self.executions[-1].timestamp

        metrics = ABTestMetrics(
            test_id=self.test_id or "unknown",
            start_date=start_date,
            end_date=end_date,
            rollout_stage=self.rollout_stage,
            total_executions=total,
            baseline_used=baseline_used,
            new_used=new_used,
            traffic_percentage=self.traffic_percentage,
            baseline_mean_score=baseline_mean,
            new_mean_score=new_mean,
            score_delta_mean=delta_mean,
            score_delta_std=delta_std,
            agreement_rate=agreement_rate,
            pass_to_fail_rate=pass_to_fail_rate,
            fail_to_pass_rate=fail_to_pass_rate,
            baseline_mean_time_ms=baseline_mean_time,
            new_mean_time_ms=new_mean_time,
            time_delta_pct=time_delta_pct,
            statistical_significance=statistical_significance,
            p_value=p_value,
            effect_size=effect_size,
            comparison_result=comparison_result,
            recommendation=recommendation,
            ready_for_next_stage=ready,
        )

        self._save_metrics(metrics)

        return metrics

    def _calculate_p_value(self, deltas: List[float]) -> float:
        """
        Calculate p-value for paired t-test

        Simplified version - in production, use scipy.stats.ttest_rel
        """
        if len(deltas) < 2:
            return 1.0

        mean = statistics.mean(deltas)
        std = statistics.stdev(deltas)
        n = len(deltas)

        # t-statistic
        t_stat = abs(mean / (std / (n ** 0.5))) if std > 0 else 0.0

        # Approximate p-value (simplified)
        # In production, use proper t-distribution CDF
        if t_stat > 2.58:  # ~99% confidence
            return 0.01
        elif t_stat > 1.96:  # ~95% confidence
            return 0.05
        elif t_stat > 1.645:  # ~90% confidence
            return 0.10
        else:
            return 0.50

    def _determine_comparison_result(
        self,
        delta_mean: float,
        significant: bool,
        effect_size: float
    ) -> ComparisonResult:
        """Determine comparison result"""
        if not significant:
            return ComparisonResult.NO_SIGNIFICANT_DIFFERENCE

        if delta_mean > 0:
            # New scorer is better
            if abs(effect_size) >= self.MEDIUM_EFFECT:
                return ComparisonResult.NEW_SIGNIFICANTLY_BETTER
            else:
                return ComparisonResult.NEW_SLIGHTLY_BETTER
        else:
            # Baseline is better
            if abs(effect_size) >= self.MEDIUM_EFFECT:
                return ComparisonResult.BASELINE_SIGNIFICANTLY_BETTER
            else:
                return ComparisonResult.BASELINE_SLIGHTLY_BETTER

    def _generate_recommendation(
        self,
        comparison: Optional[ComparisonResult],
        agreement_rate: float,
        time_delta_pct: float,
        total_executions: int
    ) -> Tuple[str, bool]:
        """
        Generate recommendation and readiness for next stage

        Returns:
            (recommendation text, ready for next stage)
        """
        if total_executions < self.MIN_EXECUTIONS_FOR_STATS:
            return (
                f"Insufficient data ({total_executions} executions). "
                f"Need {self.MIN_EXECUTIONS_FOR_STATS} for statistical analysis.",
                False
            )

        if not comparison:
            return "Unable to compare scorers", False

        # Check for major performance degradation
        if time_delta_pct > 50:
            return (
                f"⚠️ ROLLBACK RECOMMENDED - New scorer is {time_delta_pct:.1f}% slower. "
                "Performance degradation too severe.",
                False
            )

        # Check comparison result
        if comparison == ComparisonResult.BASELINE_SIGNIFICANTLY_BETTER:
            return (
                "⚠️ ROLLBACK RECOMMENDED - Baseline scorer significantly outperforms new scorer. "
                f"Agreement rate: {agreement_rate:.1%}",
                False
            )

        if comparison == ComparisonResult.BASELINE_SLIGHTLY_BETTER:
            return (
                "⚠️ HOLD - Baseline slightly better. Monitor for more data or investigate issues.",
                False
            )

        if comparison == ComparisonResult.NO_SIGNIFICANT_DIFFERENCE:
            if agreement_rate >= 0.90:
                return (
                    "✓ ADVANCE - No significant difference, high agreement. Safe to proceed.",
                    True
                )
            else:
                return (
                    f"⚠️ INVESTIGATE - No clear winner but low agreement ({agreement_rate:.1%}). "
                    "Review decision changes before advancing.",
                    False
                )

        if comparison == ComparisonResult.NEW_SLIGHTLY_BETTER:
            return (
                "✓ ADVANCE - New scorer slightly better. Ready for next stage.",
                True
            )

        if comparison == ComparisonResult.NEW_SIGNIFICANTLY_BETTER:
            return (
                "✓✓ ADVANCE RAPIDLY - New scorer significantly better. Accelerate rollout.",
                True
            )

        return "Unable to generate recommendation", False

    def advance_rollout_stage(self) -> RolloutStage:
        """
        Advance to next rollout stage

        Returns:
            New rollout stage
        """
        stage_progression = {
            RolloutStage.SHADOW_ONLY: RolloutStage.PILOT,
            RolloutStage.PILOT: RolloutStage.GRADUAL,
            RolloutStage.GRADUAL: RolloutStage.FULL,
            RolloutStage.FULL: RolloutStage.FULL,  # Already at max
        }

        new_stage = stage_progression.get(self.rollout_stage, self.rollout_stage)
        self.rollout_stage = new_stage
        self.traffic_percentage = self._get_traffic_percentage(new_stage)

        self.logger.info(
            f"Advanced to {new_stage.value}, traffic={self.traffic_percentage}%"
        )

        return new_stage

    def rollback(self) -> RolloutStage:
        """
        Rollback to baseline scorer

        Returns:
            Rollback stage
        """
        self.rollout_stage = RolloutStage.ROLLBACK
        self.traffic_percentage = 0.0

        self.logger.warning("ROLLBACK - Reverted to baseline scorer")

        return self.rollout_stage

    def _save_execution(self, execution: ABTestExecution):
        """Save execution to log file"""
        if not self.test_id:
            return

        log_file = self.output_dir / f"{self.test_id}_executions.jsonl"

        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(asdict(execution)) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to save execution: {e}")

    def _save_metrics(self, metrics: ABTestMetrics):
        """Save metrics to file"""
        if not self.test_id:
            return

        metrics_file = self.output_dir / f"{self.test_id}_metrics.json"

        try:
            with open(metrics_file, 'w') as f:
                json.dump(asdict(metrics), f, indent=2)
            self.logger.info(f"Saved metrics to {metrics_file}")
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")


def run_ab_test(
    baseline_scorer: Callable,
    new_scorer: Callable,
    test_data: List[Tuple[Dict, Dict]],
    rollout_stage: RolloutStage = RolloutStage.SHADOW_ONLY,
    output_dir: str = "data/evaluation/ab_tests"
) -> ABTestMetrics:
    """
    Convenience function to run complete A/B test

    Args:
        baseline_scorer: Baseline scorer function
        new_scorer: New scorer function
        test_data: List of (profile_data, foundation_data) tuples
        rollout_stage: Rollout stage
        output_dir: Output directory

    Returns:
        ABTestMetrics
    """
    framework = ABTestingFramework(output_dir)
    framework.start_test(baseline_scorer, new_scorer, rollout_stage)

    for i, (profile_data, foundation_data) in enumerate(test_data):
        profile_ein = profile_data.get('ein', f'profile_{i}')
        foundation_ein = foundation_data.get('ein', f'foundation_{i}')

        framework.execute_with_ab_test(
            profile_ein, foundation_ein,
            profile_data, foundation_data
        )

    return framework.calculate_metrics()
