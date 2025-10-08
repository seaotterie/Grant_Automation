"""
Performance Reporter (V1.0)

Comprehensive reporting system for gold set evaluation results with visualization,
comparison across model versions, and exportable reports.

Key Concepts:
- **Performance Reports**: Detailed analysis of model metrics
- **Version Comparison**: Compare metrics across model iterations
- **Visual Reports**: HTML/JSON reports with charts and tables
- **Threshold Analysis**: Optimal threshold recommendation
- **Error Analysis**: Breakdown of false positives and false negatives

Phase 5, Week 9-10 Implementation
Expected Impact: 30-40% improvement in model optimization visibility
"""

import logging
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from enum import Enum


logger = logging.getLogger(__name__)


class MetricStatus(str, Enum):
    """Status of metric vs target"""
    EXCELLENT = "excellent"      # Exceeds target by 10%+
    GOOD = "good"               # Meets or slightly exceeds target
    ACCEPTABLE = "acceptable"    # Within 5% of target
    BELOW_TARGET = "below_target"  # 5-15% below target
    POOR = "poor"               # 15%+ below target


@dataclass
class MetricTarget:
    """Target value for a metric"""
    metric_name: str
    target_value: float
    minimum_acceptable: float
    higher_is_better: bool = True
    description: str = ""


@dataclass
class MetricComparison:
    """Comparison of a metric across versions"""
    metric_name: str
    baseline_value: float
    current_value: float
    delta: float
    delta_pct: float
    status: MetricStatus
    target: Optional[float] = None


@dataclass
class ErrorBreakdown:
    """Analysis of prediction errors"""
    false_positives: int
    false_negatives: int
    false_positive_rate: float
    false_negative_rate: float

    # Error characteristics
    fp_avg_score: float  # Average score of false positives
    fn_avg_score: float  # Average score of false negatives

    # Common patterns
    fp_common_issues: List[str] = field(default_factory=list)
    fn_common_issues: List[str] = field(default_factory=list)


@dataclass
class ThresholdAnalysis:
    """Analysis of different threshold values"""
    threshold: float
    precision: float
    recall: float
    f1_score: float
    pass_rate: float  # Percentage of pairs passing threshold


@dataclass
class PerformanceReport:
    """Comprehensive performance report"""
    # Metadata
    report_id: str
    model_version: str
    evaluation_date: str
    total_pairs: int
    labeled_pairs: int

    # Core metrics
    accuracy: float
    precision: float
    recall: float
    f1_score: float

    # Ranking metrics
    precision_at_10: float
    precision_at_50: float
    top_2_accuracy: float

    # Calibration
    expected_calibration_error: float

    # Metric status
    metric_comparisons: List[MetricComparison] = field(default_factory=list)
    overall_status: str = "unknown"

    # Error analysis
    error_breakdown: Optional[ErrorBreakdown] = None

    # Threshold analysis
    threshold_analyses: List[ThresholdAnalysis] = field(default_factory=list)
    recommended_threshold: Optional[float] = None

    # Insights
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class PerformanceReporter:
    """
    Generate comprehensive performance reports for gold set evaluation

    Features:
    - Metric target tracking (F1 ≥0.75, P@10 ≥0.80, ECE ≤0.10)
    - Version comparison (baseline vs current)
    - Error analysis with common patterns
    - Threshold optimization
    - HTML/JSON report generation
    """

    # Default metric targets
    DEFAULT_TARGETS = [
        MetricTarget("f1_score", 0.75, 0.70, True, "F1 score (precision-recall balance)"),
        MetricTarget("precision_at_10", 0.80, 0.75, True, "Precision at top 10 results"),
        MetricTarget("expected_calibration_error", 0.10, 0.15, False, "Calibration error"),
        MetricTarget("precision", 0.75, 0.70, True, "Precision (positive predictive value)"),
        MetricTarget("recall", 0.75, 0.70, True, "Recall (sensitivity)"),
    ]

    def __init__(self, output_dir: str = "data/evaluation/reports"):
        """
        Initialize performance reporter

        Args:
            output_dir: Directory for report output
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}.PerformanceReporter")

        self.targets = self.DEFAULT_TARGETS

    def generate_report(
        self,
        metrics: Dict[str, Any],
        model_version: str,
        baseline_metrics: Optional[Dict[str, Any]] = None,
        gold_set_pairs: Optional[List] = None,
        score_threshold: float = 0.58
    ) -> PerformanceReport:
        """
        Generate comprehensive performance report

        Args:
            metrics: Current model metrics
            model_version: Version identifier
            baseline_metrics: Optional baseline for comparison
            gold_set_pairs: Optional gold set pairs for error analysis
            score_threshold: Classification threshold

        Returns:
            PerformanceReport with all analyses
        """
        report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Extract core metrics
        accuracy = metrics.get('accuracy', 0.0)
        precision = metrics.get('precision', 0.0)
        recall = metrics.get('recall', 0.0)
        f1_score = metrics.get('f1_score', 0.0)
        p_at_10 = metrics.get('precision_at_10', 0.0)
        p_at_50 = metrics.get('precision_at_50', 0.0)
        top_2_acc = metrics.get('top_2_accuracy', 0.0)
        ece = metrics.get('expected_calibration_error', 0.0)

        # Metric comparisons
        comparisons = self._compare_to_targets(metrics)
        if baseline_metrics:
            baseline_comparisons = self._compare_to_baseline(metrics, baseline_metrics)
            comparisons.extend(baseline_comparisons)

        # Overall status
        overall_status = self._determine_overall_status(comparisons)

        # Error analysis
        error_breakdown = None
        if gold_set_pairs:
            error_breakdown = self._analyze_errors(gold_set_pairs, score_threshold)

        # Threshold analysis
        threshold_analyses = []
        recommended_threshold = score_threshold
        if gold_set_pairs:
            threshold_analyses = self._analyze_thresholds(gold_set_pairs)
            recommended_threshold = self._recommend_threshold(threshold_analyses)

        # Generate insights
        strengths, weaknesses, recommendations = self._generate_insights(
            metrics, comparisons, error_breakdown, threshold_analyses
        )

        report = PerformanceReport(
            report_id=report_id,
            model_version=model_version,
            evaluation_date=datetime.now().isoformat(),
            total_pairs=metrics.get('total_pairs', 0),
            labeled_pairs=metrics.get('labeled_pairs', 0),
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            precision_at_10=p_at_10,
            precision_at_50=p_at_50,
            top_2_accuracy=top_2_acc,
            expected_calibration_error=ece,
            metric_comparisons=comparisons,
            overall_status=overall_status,
            error_breakdown=error_breakdown,
            threshold_analyses=threshold_analyses,
            recommended_threshold=recommended_threshold,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )

        # Save report
        self._save_report(report)

        return report

    def _compare_to_targets(self, metrics: Dict[str, Any]) -> List[MetricComparison]:
        """Compare metrics against targets"""
        comparisons = []

        for target in self.targets:
            current_value = metrics.get(target.metric_name, 0.0)

            # Calculate delta
            if target.higher_is_better:
                delta = current_value - target.target_value
                delta_pct = (delta / target.target_value * 100) if target.target_value > 0 else 0
            else:
                delta = target.target_value - current_value
                delta_pct = (delta / target.target_value * 100) if target.target_value > 0 else 0

            # Determine status
            if target.higher_is_better:
                if current_value >= target.target_value * 1.10:
                    status = MetricStatus.EXCELLENT
                elif current_value >= target.target_value:
                    status = MetricStatus.GOOD
                elif current_value >= target.target_value * 0.95:
                    status = MetricStatus.ACCEPTABLE
                elif current_value >= target.minimum_acceptable:
                    status = MetricStatus.BELOW_TARGET
                else:
                    status = MetricStatus.POOR
            else:
                if current_value <= target.target_value * 0.90:
                    status = MetricStatus.EXCELLENT
                elif current_value <= target.target_value:
                    status = MetricStatus.GOOD
                elif current_value <= target.target_value * 1.05:
                    status = MetricStatus.ACCEPTABLE
                elif current_value <= target.minimum_acceptable:
                    status = MetricStatus.BELOW_TARGET
                else:
                    status = MetricStatus.POOR

            comparisons.append(MetricComparison(
                metric_name=target.metric_name,
                baseline_value=target.target_value,
                current_value=current_value,
                delta=delta,
                delta_pct=delta_pct,
                status=status,
                target=target.target_value,
            ))

        return comparisons

    def _compare_to_baseline(
        self,
        current_metrics: Dict[str, Any],
        baseline_metrics: Dict[str, Any]
    ) -> List[MetricComparison]:
        """Compare current metrics to baseline"""
        comparisons = []

        metric_names = ['accuracy', 'precision', 'recall', 'f1_score',
                       'precision_at_10', 'precision_at_50', 'expected_calibration_error']

        for metric_name in metric_names:
            baseline_value = baseline_metrics.get(metric_name, 0.0)
            current_value = current_metrics.get(metric_name, 0.0)

            delta = current_value - baseline_value
            delta_pct = (delta / baseline_value * 100) if baseline_value > 0 else 0

            # Status based on improvement
            if abs(delta_pct) >= 10:
                status = MetricStatus.EXCELLENT if delta > 0 else MetricStatus.POOR
            elif abs(delta_pct) >= 5:
                status = MetricStatus.GOOD if delta > 0 else MetricStatus.BELOW_TARGET
            else:
                status = MetricStatus.ACCEPTABLE

            comparisons.append(MetricComparison(
                metric_name=f"{metric_name}_vs_baseline",
                baseline_value=baseline_value,
                current_value=current_value,
                delta=delta,
                delta_pct=delta_pct,
                status=status,
            ))

        return comparisons

    def _determine_overall_status(self, comparisons: List[MetricComparison]) -> str:
        """Determine overall model status"""
        target_comparisons = [c for c in comparisons if c.target is not None]

        if not target_comparisons:
            return "unknown"

        status_counts = {
            MetricStatus.EXCELLENT: 0,
            MetricStatus.GOOD: 0,
            MetricStatus.ACCEPTABLE: 0,
            MetricStatus.BELOW_TARGET: 0,
            MetricStatus.POOR: 0,
        }

        for comp in target_comparisons:
            status_counts[comp.status] += 1

        # Overall status logic
        if status_counts[MetricStatus.POOR] > 0:
            return "needs_improvement"
        elif status_counts[MetricStatus.BELOW_TARGET] >= 2:
            return "below_targets"
        elif status_counts[MetricStatus.EXCELLENT] >= 3:
            return "excellent"
        elif status_counts[MetricStatus.GOOD] >= 3:
            return "production_ready"
        else:
            return "acceptable"

    def _analyze_errors(
        self,
        pairs: List,
        threshold: float
    ) -> ErrorBreakdown:
        """Analyze false positives and false negatives"""
        from .gold_set_evaluator import MatchLabel

        labeled_pairs = [p for p in pairs if p.expert_label is not None]

        false_positives = []
        false_negatives = []

        for pair in labeled_pairs:
            if pair.expert_label == MatchLabel.UNCERTAIN:
                continue

            predicted_match = pair.predicted_score >= threshold
            actual_match = pair.expert_label == MatchLabel.STRONG_MATCH

            if predicted_match and not actual_match:
                false_positives.append(pair)
            elif not predicted_match and actual_match:
                false_negatives.append(pair)

        fp_count = len(false_positives)
        fn_count = len(false_negatives)

        total = len([p for p in labeled_pairs if p.expert_label != MatchLabel.UNCERTAIN])
        fp_rate = fp_count / total if total > 0 else 0.0
        fn_rate = fn_count / total if total > 0 else 0.0

        fp_avg_score = sum(p.predicted_score for p in false_positives) / fp_count if fp_count > 0 else 0.0
        fn_avg_score = sum(p.predicted_score for p in false_negatives) / fn_count if fn_count > 0 else 0.0

        # Identify common issues
        fp_issues = self._identify_fp_patterns(false_positives)
        fn_issues = self._identify_fn_patterns(false_negatives)

        return ErrorBreakdown(
            false_positives=fp_count,
            false_negatives=fn_count,
            false_positive_rate=fp_rate,
            false_negative_rate=fn_rate,
            fp_avg_score=fp_avg_score,
            fn_avg_score=fn_avg_score,
            fp_common_issues=fp_issues,
            fn_common_issues=fn_issues,
        )

    def _identify_fp_patterns(self, false_positives: List) -> List[str]:
        """Identify common patterns in false positives"""
        issues = []

        if not false_positives:
            return issues

        # Check for geographic mismatches
        geo_mismatches = sum(1 for p in false_positives if not p.geographic_overlap)
        if geo_mismatches / len(false_positives) > 0.3:
            issues.append(f"Geographic mismatch in {geo_mismatches} cases ({geo_mismatches/len(false_positives)*100:.0f}%)")

        # Check for NTEE misalignment
        ntee_mismatches = sum(1 for p in false_positives if not p.ntee_major_match)
        if ntee_mismatches / len(false_positives) > 0.3:
            issues.append(f"NTEE misalignment in {ntee_mismatches} cases ({ntee_mismatches/len(false_positives)*100:.0f}%)")

        # Check for edge cases with conflicts
        conflicts = sum(1 for p in false_positives if p.has_conflicts)
        if conflicts / len(false_positives) > 0.2:
            issues.append(f"Conflicting signals in {conflicts} cases ({conflicts/len(false_positives)*100:.0f}%)")

        return issues

    def _identify_fn_patterns(self, false_negatives: List) -> List[str]:
        """Identify common patterns in false negatives"""
        issues = []

        if not false_negatives:
            return issues

        # Check for missed matches with good alignment
        good_alignment = sum(1 for p in false_negatives if p.ntee_major_match and p.geographic_overlap)
        if good_alignment / len(false_negatives) > 0.3:
            issues.append(f"Missed {good_alignment} matches with good NTEE+geo alignment ({good_alignment/len(false_negatives)*100:.0f}%)")

        # Check for Schedule I evidence
        schedule_i_matches = sum(1 for p in false_negatives if len(p.schedule_i_grantees) > 0)
        if schedule_i_matches / len(false_negatives) > 0.2:
            issues.append(f"Underweighted Schedule I evidence in {schedule_i_matches} cases ({schedule_i_matches/len(false_negatives)*100:.0f}%)")

        return issues

    def _analyze_thresholds(self, pairs: List) -> List[ThresholdAnalysis]:
        """Analyze performance at different thresholds"""
        from .gold_set_evaluator import MatchLabel

        labeled_pairs = [p for p in pairs if p.expert_label is not None and p.expert_label != MatchLabel.UNCERTAIN]

        thresholds = [0.45, 0.50, 0.55, 0.58, 0.60, 0.65, 0.70, 0.75]
        analyses = []

        for threshold in thresholds:
            tp = sum(1 for p in labeled_pairs if p.predicted_score >= threshold and p.expert_label == MatchLabel.STRONG_MATCH)
            fp = sum(1 for p in labeled_pairs if p.predicted_score >= threshold and p.expert_label == MatchLabel.NO_MATCH)
            fn = sum(1 for p in labeled_pairs if p.predicted_score < threshold and p.expert_label == MatchLabel.STRONG_MATCH)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

            pass_rate = sum(1 for p in labeled_pairs if p.predicted_score >= threshold) / len(labeled_pairs)

            analyses.append(ThresholdAnalysis(
                threshold=threshold,
                precision=precision,
                recall=recall,
                f1_score=f1,
                pass_rate=pass_rate,
            ))

        return analyses

    def _recommend_threshold(self, analyses: List[ThresholdAnalysis]) -> float:
        """Recommend optimal threshold based on F1 score"""
        if not analyses:
            return 0.58  # Default

        best_analysis = max(analyses, key=lambda a: a.f1_score)
        return best_analysis.threshold

    def _generate_insights(
        self,
        metrics: Dict[str, Any],
        comparisons: List[MetricComparison],
        error_breakdown: Optional[ErrorBreakdown],
        threshold_analyses: List[ThresholdAnalysis]
    ) -> Tuple[List[str], List[str], List[str]]:
        """Generate strengths, weaknesses, and recommendations"""
        strengths = []
        weaknesses = []
        recommendations = []

        # Analyze metrics
        f1 = metrics.get('f1_score', 0.0)
        p_at_10 = metrics.get('precision_at_10', 0.0)
        ece = metrics.get('expected_calibration_error', 0.0)

        if f1 >= 0.75:
            strengths.append(f"Strong F1 score ({f1:.3f}) meets target threshold")
        elif f1 < 0.70:
            weaknesses.append(f"F1 score ({f1:.3f}) below minimum acceptable (0.70)")
            recommendations.append("Focus on improving both precision and recall through feature engineering")

        if p_at_10 >= 0.80:
            strengths.append(f"Excellent ranking performance (P@10={p_at_10:.3f})")
        elif p_at_10 < 0.75:
            weaknesses.append(f"P@10 ({p_at_10:.3f}) below target - top recommendations need improvement")
            recommendations.append("Increase weights on high-confidence signals (NTEE match, Schedule I votes)")

        if ece <= 0.10:
            strengths.append(f"Well-calibrated predictions (ECE={ece:.3f})")
        elif ece > 0.15:
            weaknesses.append(f"Poor calibration (ECE={ece:.3f}) - scores don't reflect true probabilities")
            recommendations.append("Apply calibration methods (temperature scaling, isotonic regression)")

        # Error analysis insights
        if error_breakdown:
            if error_breakdown.false_positive_rate > 0.15:
                weaknesses.append(f"High false positive rate ({error_breakdown.false_positive_rate:.1%})")
                recommendations.append(f"Common FP issues: {', '.join(error_breakdown.fp_common_issues[:2])}")

            if error_breakdown.false_negative_rate > 0.15:
                weaknesses.append(f"High false negative rate ({error_breakdown.false_negative_rate:.1%})")
                recommendations.append(f"Common FN issues: {', '.join(error_breakdown.fn_common_issues[:2])}")

        # Threshold insights
        if threshold_analyses:
            recommended = self._recommend_threshold(threshold_analyses)
            current = 0.58
            if abs(recommended - current) >= 0.05:
                recommendations.append(f"Consider adjusting threshold from {current} to {recommended} for better F1")

        return strengths, weaknesses, recommendations

    def _save_report(self, report: PerformanceReport):
        """Save report to JSON file"""
        report_file = self.output_dir / f"{report.report_id}.json"

        try:
            with open(report_file, 'w') as f:
                json.dump(asdict(report), f, indent=2)
            self.logger.info(f"Saved report to {report_file}")
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")

    def generate_html_report(self, report: PerformanceReport) -> str:
        """
        Generate HTML visualization of report

        Returns:
            Path to generated HTML file
        """
        html_file = self.output_dir / f"{report.report_id}.html"

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Report - {report.model_version}</title>
    <style>
        body {{ font-family: -apple-system, system-ui, sans-serif; padding: 2rem; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; }}
        h1 {{ color: #1a1a1a; margin-bottom: 0.5rem; }}
        .subtitle {{ color: #666; margin-bottom: 2rem; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 2rem 0; }}
        .metric-card {{ padding: 1.5rem; border-radius: 8px; background: #f9f9f9; }}
        .metric-value {{ font-size: 2rem; font-weight: bold; margin: 0.5rem 0; }}
        .metric-label {{ color: #666; font-size: 0.875rem; text-transform: uppercase; }}
        .status-excellent {{ color: #10b981; }}
        .status-good {{ color: #3b82f6; }}
        .status-acceptable {{ color: #f59e0b; }}
        .status-poor {{ color: #ef4444; }}
        .section {{ margin: 2rem 0; }}
        .section-title {{ font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem; border-bottom: 2px solid #e5e5e5; padding-bottom: 0.5rem; }}
        ul {{ line-height: 1.8; }}
        .strength {{ color: #10b981; }}
        .weakness {{ color: #ef4444; }}
        .recommendation {{ color: #3b82f6; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Performance Report</h1>
        <div class="subtitle">
            Model: {report.model_version} |
            Date: {report.evaluation_date[:10]} |
            Status: {report.overall_status.replace('_', ' ').title()}
        </div>

        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">F1 Score</div>
                <div class="metric-value">{report.f1_score:.3f}</div>
                <div class="metric-label">Target: 0.750</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Precision</div>
                <div class="metric-value">{report.precision:.3f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Recall</div>
                <div class="metric-value">{report.recall:.3f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">P@10</div>
                <div class="metric-value">{report.precision_at_10:.3f}</div>
                <div class="metric-label">Target: 0.800</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Calibration (ECE)</div>
                <div class="metric-value">{report.expected_calibration_error:.3f}</div>
                <div class="metric-label">Target: ≤0.100</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Strengths</div>
            <ul>
                {"".join(f'<li class="strength">✓ {s}</li>' for s in report.strengths)}
            </ul>
        </div>

        <div class="section">
            <div class="section-title">Weaknesses</div>
            <ul>
                {"".join(f'<li class="weakness">✗ {w}</li>' for w in report.weaknesses)}
            </ul>
        </div>

        <div class="section">
            <div class="section-title">Recommendations</div>
            <ul>
                {"".join(f'<li class="recommendation">→ {r}</li>' for r in report.recommendations)}
            </ul>
        </div>
    </div>
</body>
</html>
"""

        try:
            with open(html_file, 'w') as f:
                f.write(html_content)
            self.logger.info(f"Generated HTML report: {html_file}")
            return str(html_file)
        except Exception as e:
            self.logger.error(f"Failed to generate HTML report: {e}")
            return ""


def generate_performance_report(
    metrics: Dict[str, Any],
    model_version: str,
    baseline_metrics: Optional[Dict[str, Any]] = None,
    gold_set_pairs: Optional[List] = None,
    output_dir: str = "data/evaluation/reports"
) -> PerformanceReport:
    """
    Convenience function to generate performance report

    Args:
        metrics: Current model metrics
        model_version: Version identifier
        baseline_metrics: Optional baseline for comparison
        gold_set_pairs: Optional gold set pairs for error analysis
        output_dir: Output directory

    Returns:
        PerformanceReport
    """
    reporter = PerformanceReporter(output_dir)
    return reporter.generate_report(metrics, model_version, baseline_metrics, gold_set_pairs)
