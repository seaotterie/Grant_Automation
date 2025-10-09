# 990-PF Screening Enhancement - Deployment Guide

## Quick Start

This guide provides step-by-step instructions for deploying the enhanced 990-PF screening system to production.

---

## Prerequisites

### System Requirements
- Python 3.9+
- Dependencies from `requirements.txt`
- Database: SQLite (Catalynx.db, Nonprofit_Intelligence.db)
- Disk space: 10GB+ for BMF/SOI data

### Data Requirements
- ✅ IRS BMF data (752K+ organizations)
- ✅ Form 990/990-PF/990-EZ data (2M+ records)
- ⏳ Gold set labels (1,500 pairs) - **NEEDS COMPLETION**

---

## Phase 1: Gold Set Preparation (Est. 2-3 weeks)

### Step 1: Generate Gold Set Samples

```python
from src.evaluation import create_gold_set

# Generate 1,500 stratified samples
evaluator = create_gold_set(output_dir="data/evaluation/gold_set")

# Stratification:
# - 300 obvious matches (high scores)
# - 600 borderline cases (0.50-0.70 range)
# - 300 obvious non-matches (low scores)
# - 300 edge cases (conflicts, sparse data)
```

**Output**: `data/evaluation/gold_set/gold_set_pairs.json`

### Step 2: Expert Labeling

**Effort**: 250-300 hours (10 min/pair × 1,500)
**Team Size**: 2-3 reviewers recommended

```python
from src.evaluation import GoldSetEvaluator, MatchLabel

evaluator = GoldSetEvaluator("data/evaluation/gold_set")

# Get next unlabeled pair
unlabeled = evaluator.get_unlabeled_pairs(limit=1)
pair = unlabeled[0]

# Review and label
evaluator.label_pair(
    pair_id=pair.pair_id,
    label=MatchLabel.STRONG_MATCH,  # or NO_MATCH, UNCERTAIN
    labeler_name="reviewer_initials",
    notes="Foundation's NTEE matches, geographic overlap, similar grant sizes"
)

# Check progress
progress = evaluator.get_labeling_progress()
print(f"Progress: {progress['percent_complete']}%")
```

**Guidelines for Labeling**:
- **STRONG_MATCH**: Clear alignment, high probability of success
- **NO_MATCH**: Clear misalignment, low probability
- **UNCERTAIN**: Borderline, requires deeper analysis

---

## Phase 2: Baseline Evaluation (Est. 1 week)

### Step 3: Run Baseline Evaluation

```python
from src.evaluation import GoldSetEvaluator, generate_performance_report

# Load labeled gold set
evaluator = GoldSetEvaluator("data/evaluation/gold_set")

# Evaluate current scorer (baseline)
metrics = evaluator.evaluate_model(score_threshold=0.58)

# Generate performance report
from src.scoring import CompositeScoreV2

# Collect component scores for error analysis
gold_set_pairs = evaluator.pairs

report = generate_performance_report(
    metrics={
        'f1_score': metrics.f1_score,
        'precision': metrics.precision,
        'recall': metrics.recall,
        'precision_at_10': metrics.precision_at_10,
        'expected_calibration_error': metrics.expected_calibration_error,
        'total_pairs': metrics.total_pairs,
        'labeled_pairs': metrics.labeled_pairs,
    },
    model_version="baseline_v1.0",
    gold_set_pairs=gold_set_pairs,
    output_dir="data/evaluation/reports"
)

print(f"F1 Score: {metrics.f1_score:.3f}")
print(f"P@10: {metrics.precision_at_10:.3f}")
print(f"ECE: {metrics.expected_calibration_error:.3f}")
```

**Success Criteria**:
- F1 Score ≥0.75
- Precision@10 ≥0.80
- ECE ≤0.10

**Action if Below Target**: Review error analysis, adjust weights, re-test

---

## Phase 3: Shadow Mode Deployment (2 weeks)

### Step 4: Configure A/B Testing

```python
from src.evaluation import ABTestingFramework, RolloutStage
from src.scoring import CompositeScoreV2

# Initialize framework
ab_test = ABTestingFramework(output_dir="data/evaluation/ab_tests")

# Define scorers
def baseline_scorer(profile_data, foundation_data):
    # Your current production scorer
    score = legacy_composite_score(profile_data, foundation_data)
    decision = "PASS" if score >= 0.58 else "FAIL"
    return score, decision

def new_scorer(profile_data, foundation_data):
    # New Composite Scorer V2
    scorer = CompositeScoreV2()
    result = scorer.score_foundation_match(profile_data, foundation_data)
    decision = result.decision  # PASS, ABSTAIN, FAIL
    return result.final_score, decision

# Start shadow mode (0% traffic to new scorer)
ab_test.start_test(
    baseline_scorer=baseline_scorer,
    new_scorer=new_scorer,
    rollout_stage=RolloutStage.SHADOW_ONLY,
    test_name="composite_v2_shadow"
)
```

### Step 5: Execute in Production

```python
# In your production scoring loop
for profile in profiles_to_score:
    for foundation in candidate_foundations:

        # Execute with A/B test (runs both, uses baseline)
        result = ab_test.execute_with_ab_test(
            profile_ein=profile['ein'],
            foundation_ein=foundation['ein'],
            profile_data=profile,
            foundation_data=foundation
        )

        # Use baseline result (new scorer logged in background)
        apply_result(result)
```

**Duration**: 2 weeks minimum
**Target**: 1,000+ executions for statistical significance

### Step 6: Analyze Shadow Mode Results

```python
# After 2 weeks
metrics = ab_test.calculate_metrics()

print(f"Total Executions: {metrics.total_executions}")
print(f"Score Delta Mean: {metrics.score_delta_mean:.3f}")
print(f"Agreement Rate: {metrics.agreement_rate:.1%}")
print(f"Statistical Significance: {metrics.statistical_significance}")
print(f"Comparison: {metrics.comparison_result.value}")
print(f"Recommendation: {metrics.recommendation}")
print(f"Ready for Next Stage: {metrics.ready_for_next_stage}")
```

**Go/No-Go Decision**:
- ✅ **PROCEED** if: `ready_for_next_stage == True`
- ⚠️ **INVESTIGATE** if: Warning level issues
- 🛑 **ROLLBACK** if: Critical/severe degradation

---

## Phase 4: Pilot Rollout (1 week)

### Step 7: Activate 10% Traffic

```python
# Advance to pilot stage
ab_test.advance_rollout_stage()
# Now: 10% of traffic uses new scorer, 90% uses baseline

# Continue production execution
# Monitor for 1 week, collect metrics
```

### Step 8: Monitor Pilot Performance

```python
# Daily monitoring
metrics = ab_test.calculate_metrics()

# Check for issues
if not metrics.ready_for_next_stage:
    print(f"⚠️ Issue detected: {metrics.recommendation}")
    # Investigate or rollback
    ab_test.rollback()
else:
    print("✓ Pilot successful, ready for gradual rollout")
```

---

## Phase 5: Gradual Rollout (1 week)

### Step 9: Increase to 50% Traffic

```python
# Advance to gradual stage
ab_test.advance_rollout_stage()
# Now: 50% traffic to new scorer

# Monitor for 1 week
```

### Step 10: Validate Performance

```python
# End of week validation
metrics = ab_test.calculate_metrics()

if metrics.ready_for_next_stage:
    print("✓ Ready for full rollout")
else:
    print(f"⚠️ {metrics.recommendation}")
```

---

## Phase 6: Full Deployment

### Step 11: 100% Traffic Cutover

```python
# Advance to full rollout
ab_test.advance_rollout_stage()
# Now: 100% traffic to new scorer

# Monitor closely for 2 weeks
```

### Step 12: Establish Drift Monitoring

```python
from src.evaluation import DriftMonitor

# Initialize drift monitor
monitor = DriftMonitor(output_dir="data/evaluation/drift_monitoring")

# Record baseline (post-deployment)
monitor.record_validation(
    model_version="composite_v2.0",
    metrics={
        'f1_score': 0.78,
        'precision': 0.76,
        'recall': 0.80,
        'precision_at_10': 0.82,
        'expected_calibration_error': 0.09,
    },
    total_evaluated=1500,
    gold_set_version="v1.0",
    notes="Initial production deployment"
)
```

---

## Phase 7: Ongoing Maintenance

### Quarterly Validation (Every 90 days)

```python
from src.evaluation import monitor_drift

# Re-run evaluation on gold set
evaluator = GoldSetEvaluator("data/evaluation/gold_set")
metrics = evaluator.evaluate_model(score_threshold=0.58)

# Check for drift
drift_analysis = monitor_drift(
    metrics={
        'f1_score': metrics.f1_score,
        'precision': metrics.precision,
        'recall': metrics.recall,
        'precision_at_10': metrics.precision_at_10,
        'expected_calibration_error': metrics.expected_calibration_error,
    },
    model_version="composite_v2.0",
    total_evaluated=metrics.labeled_pairs
)

if drift_analysis and drift_analysis.requires_action:
    print(f"🚨 DRIFT DETECTED: {drift_analysis.recommendation}")
    print(f"Severity: {drift_analysis.severity.value}")
    print(f"Degraded Metrics: {drift_analysis.degraded_metrics}")

    # Review alerts
    for alert in drift_analysis.alerts:
        print(f"- {alert.message}")
```

### Alert Monitoring

```python
from src.evaluation import DriftMonitor

monitor = DriftMonitor("data/evaluation/drift_monitoring")

# Check for unacknowledged alerts
alerts = monitor.get_unacknowledged_alerts()

for alert in alerts:
    print(f"[{alert.alert_level.value.upper()}] {alert.message}")

    # Acknowledge after review
    monitor.acknowledge_alert(alert.alert_id)
```

---

## Rollback Procedures

### Emergency Rollback

```python
from src.evaluation import ABTestingFramework

ab_test = ABTestingFramework("data/evaluation/ab_tests")

# Immediate rollback to baseline
ab_test.rollback()
# Now: 0% traffic to new scorer, 100% to baseline

print("✓ Rolled back to baseline scorer")
```

### Identifying Rollback Triggers

**Automatic Rollback** if:
- Performance degradation >50% slower
- Baseline significantly outperforms new scorer
- Critical/severe drift detected

**Manual Rollback** if:
- User complaints increase
- Business metrics decline
- Unexpected behavior observed

---

## Performance Monitoring

### Key Metrics Dashboard

Create monitoring dashboard tracking:

1. **Scoring Metrics**:
   - F1 Score (target ≥0.75)
   - Precision@10 (target ≥0.80)
   - Calibration ECE (target ≤0.10)

2. **Operational Metrics**:
   - Scoring time (ms/execution)
   - Throughput (executions/hour)
   - Error rate

3. **Business Metrics**:
   - User satisfaction
   - Recommendation acceptance rate
   - Time to decision

### Alerting Thresholds

```python
# Set up automated alerts
thresholds = {
    'f1_score_min': 0.70,
    'precision_at_10_min': 0.75,
    'calibration_ece_max': 0.15,
    'avg_time_ms_max': 100,
    'error_rate_max': 0.01,
}
```

---

## Troubleshooting

### Issue: Low F1 Score (<0.75)

**Diagnosis**:
```python
# Review error breakdown
report = generate_performance_report(metrics, "current_version")
print(f"False Positive Rate: {report.error_breakdown.false_positive_rate}")
print(f"False Negative Rate: {report.error_breakdown.false_negative_rate}")
```

**Solutions**:
- High FP: Increase threshold, reduce weight on noisy features
- High FN: Decrease threshold, increase weight on strong signals
- Review common error patterns in error_breakdown

### Issue: Drift Detected

**Diagnosis**:
```python
monitor = DriftMonitor("data/evaluation/drift_monitoring")
analysis = monitor.detect_drift()

print(f"Degraded metrics: {analysis.degraded_metrics}")
print(f"Time elapsed: {analysis.time_elapsed_days} days")
```

**Solutions**:
- Data distribution changed: Re-train model
- Feature quality degraded: Fix data pipeline
- External factors: Update features/weights

### Issue: Slow Performance

**Diagnosis**:
```python
# Profile execution time
import time

start = time.time()
result = scorer.score_foundation_match(profile, foundation)
elapsed = (time.time() - start) * 1000

print(f"Execution time: {elapsed:.2f}ms")
```

**Solutions**:
- >100ms: Review expensive computations
- Optimize Schedule I analysis (caching)
- Consider async execution

---

## Support Resources

### Documentation
- `/docs/TIER_SYSTEM.md` - Tier architecture
- `/src/scoring/README.md` - Scoring components
- `/src/evaluation/README.md` - Evaluation framework

### Code References
- **Scoring**: `src/scoring/composite_scorer_v2.py:87`
- **Evaluation**: `src/evaluation/gold_set_evaluator.py:366`
- **A/B Testing**: `src/evaluation/ab_testing.py:195`
- **Drift Monitor**: `src/evaluation/drift_monitor.py:212`

### Configuration Files
- `src/scoring/scoring_config.py` - Weights, thresholds, feature flags
- `.env` - Environment variables, API keys

---

## Success Metrics

### Target Achievement

| Metric | Baseline | Target | Current |
|--------|----------|--------|---------|
| F1 Score | TBD | ≥0.75 | Pending validation |
| Precision@10 | TBD | ≥0.80 | Pending validation |
| ECE | TBD | ≤0.10 | Pending validation |
| Accuracy Improvement | - | 70-90% | Pending validation |

### Timeline

- **Week 1-3**: Gold set labeling
- **Week 4**: Baseline evaluation
- **Week 5-6**: Shadow mode (2 weeks)
- **Week 7**: Pilot (10% traffic)
- **Week 8**: Gradual (50% traffic)
- **Week 9**: Full deployment (100%)
- **Week 10+**: Quarterly validation cadence

**Total Deployment Timeline**: ~8-10 weeks from start

---

## Contact & Escalation

For deployment issues:
1. Review troubleshooting section above
2. Check evaluation reports in `data/evaluation/reports/`
3. Review A/B test logs in `data/evaluation/ab_tests/`
4. Consult drift monitoring in `data/evaluation/drift_monitoring/`

For critical issues:
- **Rollback**: Execute emergency rollback procedure
- **Investigation**: Use performance reporter for root cause analysis
- **Re-training**: Use gold set evaluator with updated labels

---

**Last Updated**: 2025-10-08
**Version**: 1.0
**Status**: ✅ Ready for Production Deployment

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
