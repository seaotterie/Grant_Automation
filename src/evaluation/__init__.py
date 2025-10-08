"""
Evaluation Module for 990-PF Screening Enhancement
Gold set validation, drift monitoring, and A/B testing infrastructure.

Version: 2.1
Created: Phase 1, Week 1 (runs through Phase 5, Week 10)
Updated: Phase 5, Week 9-10 (complete evaluation framework)
"""

from .gold_set_evaluator import (
    GoldSetEvaluator,
    ProfileFoundationPair,
    GoldSetMetrics,
    MatchLabel,
    SamplingStrategy,
    create_gold_set,
    get_labeling_status,
)

from .performance_reporter import (
    PerformanceReporter,
    PerformanceReport,
    MetricComparison,
    ErrorBreakdown,
    ThresholdAnalysis,
    MetricStatus,
    MetricTarget,
    generate_performance_report,
)

__all__ = [
    # Gold Set Evaluation
    "GoldSetEvaluator",
    "ProfileFoundationPair",
    "GoldSetMetrics",
    "MatchLabel",
    "SamplingStrategy",
    "create_gold_set",
    "get_labeling_status",

    # Performance Reporting
    "PerformanceReporter",
    "PerformanceReport",
    "MetricComparison",
    "ErrorBreakdown",
    "ThresholdAnalysis",
    "MetricStatus",
    "MetricTarget",
    "generate_performance_report",
]

__version__ = "2.1.0"
