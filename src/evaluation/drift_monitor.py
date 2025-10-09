"""
Drift Monitoring System (V1.0)

Detects model performance degradation over time through quarterly validation
against gold set and automated alerting.

Key Concepts:
- **Model Drift**: Degradation in performance over time
- **Quarterly Validation**: Re-evaluate against gold set every 3 months
- **Alert Thresholds**: Warning at 5% drop, critical at 10% drop
- **Trend Analysis**: Track metrics over multiple validation periods
- **Automatic Re-evaluation**: Trigger evaluation when drift detected

Phase 5, Week 9-10 Implementation
Expected Impact: Maintain >95% of initial performance over 12+ months
"""

import logging
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum


logger = logging.getLogger(__name__)


class DriftSeverity(str, Enum):
    """Severity of detected drift"""
    NONE = "none"                    # <2% degradation
    MINIMAL = "minimal"              # 2-5% degradation
    WARNING = "warning"              # 5-10% degradation
    CRITICAL = "critical"            # 10-15% degradation
    SEVERE = "severe"                # >15% degradation


class AlertLevel(str, Enum):
    """Alert level for drift detection"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ValidationSnapshot:
    """Single validation snapshot"""
    snapshot_id: str
    validation_date: str
    model_version: str

    # Core metrics
    f1_score: float
    precision: float
    recall: float
    precision_at_10: float
    expected_calibration_error: float

    # Sample info
    total_evaluated: int
    gold_set_version: str

    # Metadata
    notes: Optional[str] = None


@dataclass
class DriftAlert:
    """Alert for detected drift"""
    alert_id: str
    alert_level: AlertLevel
    metric_name: str
    current_value: float
    baseline_value: float
    degradation_pct: float
    severity: DriftSeverity
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    acknowledged: bool = False


@dataclass
class DriftAnalysis:
    """Analysis of drift over time"""
    analysis_id: str
    analysis_date: str
    model_version: str

    # Comparison
    baseline_snapshot: ValidationSnapshot
    current_snapshot: ValidationSnapshot
    time_elapsed_days: int

    # Drift detection
    has_drift: bool
    severity: DriftSeverity
    degraded_metrics: List[str] = field(default_factory=list)

    # Metric changes
    f1_delta: float = 0.0
    precision_delta: float = 0.0
    recall_delta: float = 0.0
    p_at_10_delta: float = 0.0
    ece_delta: float = 0.0

    # Alerts
    alerts: List[DriftAlert] = field(default_factory=list)

    # Recommendation
    recommendation: str = ""
    requires_action: bool = False


@dataclass
class TrendAnalysis:
    """Long-term trend analysis"""
    metric_name: str
    snapshots: List[ValidationSnapshot]
    trend_direction: str  # "improving", "stable", "degrading"
    linear_slope: float   # Rate of change per quarter
    volatility: float     # Standard deviation
    projection_next_quarter: float


class DriftMonitor:
    """
    Monitor model performance drift over time

    Workflow:
    1. Baseline: Initial validation after deployment
    2. Quarterly: Re-validate every 3 months
    3. Detection: Compare current vs baseline
    4. Alerting: Generate alerts for significant drift
    5. Action: Trigger re-training if drift severe

    Thresholds:
    - Minimal (<5%): Monitor
    - Warning (5-10%): Investigate
    - Critical (10-15%): Re-train recommended
    - Severe (>15%): Immediate re-train required
    """

    # Degradation thresholds (as percentages)
    THRESHOLD_MINIMAL = 2.0
    THRESHOLD_WARNING = 5.0
    THRESHOLD_CRITICAL = 10.0
    THRESHOLD_SEVERE = 15.0

    # Validation frequency
    VALIDATION_INTERVAL_DAYS = 90  # Quarterly

    def __init__(self, output_dir: str = "data/evaluation/drift_monitoring"):
        """
        Initialize drift monitor

        Args:
            output_dir: Directory for drift monitoring data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(f"{__name__}.DriftMonitor")

        # Snapshot storage
        self.snapshots_file = self.output_dir / "validation_snapshots.json"
        self.snapshots: List[ValidationSnapshot] = []

        # Alert storage
        self.alerts_file = self.output_dir / "drift_alerts.json"
        self.alerts: List[DriftAlert] = []

        # Load existing data
        self._load_snapshots()
        self._load_alerts()

    def record_validation(
        self,
        model_version: str,
        metrics: Dict[str, float],
        total_evaluated: int,
        gold_set_version: str = "v1.0",
        notes: Optional[str] = None
    ) -> ValidationSnapshot:
        """
        Record validation snapshot

        Args:
            model_version: Version of model validated
            metrics: Validation metrics
            total_evaluated: Number of samples evaluated
            gold_set_version: Version of gold set used
            notes: Optional notes

        Returns:
            ValidationSnapshot
        """
        snapshot_id = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        snapshot = ValidationSnapshot(
            snapshot_id=snapshot_id,
            validation_date=datetime.now().isoformat(),
            model_version=model_version,
            f1_score=metrics.get('f1_score', 0.0),
            precision=metrics.get('precision', 0.0),
            recall=metrics.get('recall', 0.0),
            precision_at_10=metrics.get('precision_at_10', 0.0),
            expected_calibration_error=metrics.get('expected_calibration_error', 0.0),
            total_evaluated=total_evaluated,
            gold_set_version=gold_set_version,
            notes=notes,
        )

        self.snapshots.append(snapshot)
        self._save_snapshots()

        self.logger.info(
            f"Recorded validation snapshot: {snapshot_id}, "
            f"F1={snapshot.f1_score:.3f}, P@10={snapshot.precision_at_10:.3f}"
        )

        return snapshot

    def detect_drift(
        self,
        baseline_snapshot_id: Optional[str] = None,
        current_snapshot_id: Optional[str] = None
    ) -> DriftAnalysis:
        """
        Detect drift between baseline and current snapshots

        Args:
            baseline_snapshot_id: ID of baseline snapshot (defaults to first)
            current_snapshot_id: ID of current snapshot (defaults to latest)

        Returns:
            DriftAnalysis
        """
        if not self.snapshots:
            raise ValueError("No validation snapshots available")

        # Get baseline (first snapshot or specified)
        if baseline_snapshot_id:
            baseline = next(
                (s for s in self.snapshots if s.snapshot_id == baseline_snapshot_id),
                None
            )
            if not baseline:
                raise ValueError(f"Baseline snapshot {baseline_snapshot_id} not found")
        else:
            baseline = self.snapshots[0]

        # Get current (latest snapshot or specified)
        if current_snapshot_id:
            current = next(
                (s for s in self.snapshots if s.snapshot_id == current_snapshot_id),
                None
            )
            if not current:
                raise ValueError(f"Current snapshot {current_snapshot_id} not found")
        else:
            current = self.snapshots[-1]

        # Calculate time elapsed
        baseline_date = datetime.fromisoformat(baseline.validation_date)
        current_date = datetime.fromisoformat(current.validation_date)
        time_elapsed = (current_date - baseline_date).days

        # Calculate metric deltas (as percentages)
        f1_delta = self._calculate_degradation_pct(baseline.f1_score, current.f1_score)
        precision_delta = self._calculate_degradation_pct(baseline.precision, current.precision)
        recall_delta = self._calculate_degradation_pct(baseline.recall, current.recall)
        p_at_10_delta = self._calculate_degradation_pct(baseline.precision_at_10, current.precision_at_10)

        # ECE is inverse (lower is better)
        ece_delta = self._calculate_degradation_pct(
            current.expected_calibration_error,
            baseline.expected_calibration_error,
            higher_is_better=False
        )

        # Detect degraded metrics
        degraded_metrics = []
        worst_degradation = 0.0

        metric_deltas = {
            'f1_score': f1_delta,
            'precision': precision_delta,
            'recall': recall_delta,
            'precision_at_10': p_at_10_delta,
            'expected_calibration_error': ece_delta,
        }

        for metric_name, delta in metric_deltas.items():
            if delta >= self.THRESHOLD_MINIMAL:
                degraded_metrics.append(metric_name)
                worst_degradation = max(worst_degradation, delta)

        # Determine severity
        severity = self._determine_severity(worst_degradation)
        has_drift = severity != DriftSeverity.NONE

        # Generate alerts
        alerts = self._generate_alerts(baseline, current, metric_deltas, severity)

        # Generate recommendation
        recommendation, requires_action = self._generate_drift_recommendation(
            severity, degraded_metrics, time_elapsed
        )

        analysis_id = f"drift_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        analysis = DriftAnalysis(
            analysis_id=analysis_id,
            analysis_date=datetime.now().isoformat(),
            model_version=current.model_version,
            baseline_snapshot=baseline,
            current_snapshot=current,
            time_elapsed_days=time_elapsed,
            has_drift=has_drift,
            severity=severity,
            degraded_metrics=degraded_metrics,
            f1_delta=f1_delta,
            precision_delta=precision_delta,
            recall_delta=recall_delta,
            p_at_10_delta=p_at_10_delta,
            ece_delta=ece_delta,
            alerts=alerts,
            recommendation=recommendation,
            requires_action=requires_action,
        )

        # Save alerts
        self.alerts.extend(alerts)
        self._save_alerts()

        # Save analysis
        self._save_analysis(analysis)

        self.logger.info(
            f"Drift analysis complete: severity={severity.value}, "
            f"degraded_metrics={len(degraded_metrics)}, requires_action={requires_action}"
        )

        return analysis

    def _calculate_degradation_pct(
        self,
        baseline: float,
        current: float,
        higher_is_better: bool = True
    ) -> float:
        """
        Calculate degradation percentage

        Returns positive percentage if performance degraded
        """
        if baseline == 0:
            return 0.0

        if higher_is_better:
            # Lower current value = degradation
            delta = baseline - current
        else:
            # Higher current value = degradation
            delta = current - baseline

        degradation_pct = (delta / baseline) * 100
        return max(0.0, degradation_pct)  # Only positive degradation

    def _determine_severity(self, degradation_pct: float) -> DriftSeverity:
        """Determine drift severity from degradation percentage"""
        if degradation_pct >= self.THRESHOLD_SEVERE:
            return DriftSeverity.SEVERE
        elif degradation_pct >= self.THRESHOLD_CRITICAL:
            return DriftSeverity.CRITICAL
        elif degradation_pct >= self.THRESHOLD_WARNING:
            return DriftSeverity.WARNING
        elif degradation_pct >= self.THRESHOLD_MINIMAL:
            return DriftSeverity.MINIMAL
        else:
            return DriftSeverity.NONE

    def _generate_alerts(
        self,
        baseline: ValidationSnapshot,
        current: ValidationSnapshot,
        metric_deltas: Dict[str, float],
        severity: DriftSeverity
    ) -> List[DriftAlert]:
        """Generate alerts for degraded metrics"""
        alerts = []

        baseline_values = {
            'f1_score': baseline.f1_score,
            'precision': baseline.precision,
            'recall': baseline.recall,
            'precision_at_10': baseline.precision_at_10,
            'expected_calibration_error': baseline.expected_calibration_error,
        }

        current_values = {
            'f1_score': current.f1_score,
            'precision': current.precision,
            'recall': current.recall,
            'precision_at_10': current.precision_at_10,
            'expected_calibration_error': current.expected_calibration_error,
        }

        for metric_name, degradation_pct in metric_deltas.items():
            if degradation_pct < self.THRESHOLD_MINIMAL:
                continue  # No alert needed

            # Determine alert level
            if degradation_pct >= self.THRESHOLD_CRITICAL:
                alert_level = AlertLevel.CRITICAL
            elif degradation_pct >= self.THRESHOLD_WARNING:
                alert_level = AlertLevel.WARNING
            else:
                alert_level = AlertLevel.INFO

            metric_severity = self._determine_severity(degradation_pct)

            message = (
                f"Performance degradation detected in {metric_name}: "
                f"{baseline_values[metric_name]:.3f} → {current_values[metric_name]:.3f} "
                f"({degradation_pct:.1f}% degradation)"
            )

            alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{metric_name}"

            alert = DriftAlert(
                alert_id=alert_id,
                alert_level=alert_level,
                metric_name=metric_name,
                current_value=current_values[metric_name],
                baseline_value=baseline_values[metric_name],
                degradation_pct=degradation_pct,
                severity=metric_severity,
                message=message,
            )

            alerts.append(alert)

        return alerts

    def _generate_drift_recommendation(
        self,
        severity: DriftSeverity,
        degraded_metrics: List[str],
        time_elapsed_days: int
    ) -> tuple[str, bool]:
        """
        Generate recommendation based on drift severity

        Returns:
            (recommendation text, requires_action flag)
        """
        if severity == DriftSeverity.NONE:
            return (
                "✓ No significant drift detected. Model performance stable.",
                False
            )

        if severity == DriftSeverity.MINIMAL:
            return (
                f"ℹ️ Minimal drift detected ({len(degraded_metrics)} metrics). "
                f"Continue monitoring. Re-validate in {self.VALIDATION_INTERVAL_DAYS} days.",
                False
            )

        if severity == DriftSeverity.WARNING:
            return (
                f"⚠️ WARNING - Performance degradation in {len(degraded_metrics)} metrics. "
                f"Investigate root causes. Consider re-training if degradation continues.",
                True
            )

        if severity == DriftSeverity.CRITICAL:
            return (
                f"🚨 CRITICAL - Significant degradation in {len(degraded_metrics)} metrics. "
                f"Re-training recommended. Review recent data changes and feature distributions.",
                True
            )

        if severity == DriftSeverity.SEVERE:
            return (
                f"🚨🚨 SEVERE - Major performance degradation. "
                f"IMMEDIATE RE-TRAINING REQUIRED. "
                f"Model may not be suitable for production use.",
                True
            )

        return "Unknown severity", False

    def analyze_trends(self, metric_name: str) -> TrendAnalysis:
        """
        Analyze long-term trends for a metric

        Args:
            metric_name: Metric to analyze

        Returns:
            TrendAnalysis
        """
        if len(self.snapshots) < 2:
            raise ValueError("Need at least 2 snapshots for trend analysis")

        # Extract metric values
        values = []
        for snapshot in self.snapshots:
            if metric_name == 'f1_score':
                values.append(snapshot.f1_score)
            elif metric_name == 'precision':
                values.append(snapshot.precision)
            elif metric_name == 'recall':
                values.append(snapshot.recall)
            elif metric_name == 'precision_at_10':
                values.append(snapshot.precision_at_10)
            elif metric_name == 'expected_calibration_error':
                values.append(snapshot.expected_calibration_error)
            else:
                raise ValueError(f"Unknown metric: {metric_name}")

        # Calculate linear trend (simple slope)
        n = len(values)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0.0

        # Determine trend direction
        if slope > 0.005:
            trend_direction = "improving"
        elif slope < -0.005:
            trend_direction = "degrading"
        else:
            trend_direction = "stable"

        # Calculate volatility (standard deviation)
        variance = sum((v - y_mean) ** 2 for v in values) / n
        volatility = variance ** 0.5

        # Project next quarter
        projection = values[-1] + slope

        return TrendAnalysis(
            metric_name=metric_name,
            snapshots=self.snapshots,
            trend_direction=trend_direction,
            linear_slope=slope,
            volatility=volatility,
            projection_next_quarter=projection,
        )

    def get_unacknowledged_alerts(self) -> List[DriftAlert]:
        """Get all unacknowledged alerts"""
        return [a for a in self.alerts if not a.acknowledged]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert

        Args:
            alert_id: ID of alert to acknowledge

        Returns:
            True if successful
        """
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                self._save_alerts()
                self.logger.info(f"Acknowledged alert: {alert_id}")
                return True

        self.logger.warning(f"Alert not found: {alert_id}")
        return False

    def should_validate(self, last_validation_date: Optional[str] = None) -> bool:
        """
        Check if validation is due

        Args:
            last_validation_date: ISO format date of last validation

        Returns:
            True if validation recommended
        """
        if not last_validation_date:
            if not self.snapshots:
                return True  # No snapshots, should validate
            last_validation_date = self.snapshots[-1].validation_date

        last_date = datetime.fromisoformat(last_validation_date)
        days_since = (datetime.now() - last_date).days

        return days_since >= self.VALIDATION_INTERVAL_DAYS

    # Persistence methods

    def _save_snapshots(self):
        """Save validation snapshots to file"""
        try:
            data = [asdict(s) for s in self.snapshots]
            with open(self.snapshots_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.debug(f"Saved {len(self.snapshots)} snapshots")
        except Exception as e:
            self.logger.error(f"Failed to save snapshots: {e}")

    def _load_snapshots(self):
        """Load validation snapshots from file"""
        if self.snapshots_file.exists():
            try:
                with open(self.snapshots_file, 'r') as f:
                    data = json.load(f)
                self.snapshots = [ValidationSnapshot(**s) for s in data]
                self.logger.info(f"Loaded {len(self.snapshots)} snapshots")
            except Exception as e:
                self.logger.error(f"Failed to load snapshots: {e}")

    def _save_alerts(self):
        """Save alerts to file"""
        try:
            data = [asdict(a) for a in self.alerts]
            with open(self.alerts_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.debug(f"Saved {len(self.alerts)} alerts")
        except Exception as e:
            self.logger.error(f"Failed to save alerts: {e}")

    def _load_alerts(self):
        """Load alerts from file"""
        if self.alerts_file.exists():
            try:
                with open(self.alerts_file, 'r') as f:
                    data = json.load(f)
                self.alerts = [DriftAlert(**a) for a in data]
                self.logger.info(f"Loaded {len(self.alerts)} alerts")
            except Exception as e:
                self.logger.error(f"Failed to load alerts: {e}")

    def _save_analysis(self, analysis: DriftAnalysis):
        """Save drift analysis to file"""
        analysis_file = self.output_dir / f"{analysis.analysis_id}.json"

        try:
            with open(analysis_file, 'w') as f:
                json.dump(asdict(analysis), f, indent=2)
            self.logger.info(f"Saved drift analysis: {analysis_file}")
        except Exception as e:
            self.logger.error(f"Failed to save analysis: {e}")


def monitor_drift(
    metrics: Dict[str, float],
    model_version: str,
    total_evaluated: int,
    output_dir: str = "data/evaluation/drift_monitoring"
) -> Optional[DriftAnalysis]:
    """
    Convenience function for drift monitoring

    Args:
        metrics: Current validation metrics
        model_version: Model version
        total_evaluated: Number of samples evaluated
        output_dir: Output directory

    Returns:
        DriftAnalysis if baseline exists, None otherwise
    """
    monitor = DriftMonitor(output_dir)

    # Record current validation
    monitor.record_validation(model_version, metrics, total_evaluated)

    # Detect drift if we have a baseline
    if len(monitor.snapshots) >= 2:
        return monitor.detect_drift()

    return None
