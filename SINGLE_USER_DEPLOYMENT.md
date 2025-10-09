# Single-User Deployment Guide - 990-PF Screening Enhancement

## Overview

This is a **simplified deployment guide** for a single-user system. The A/B testing and drift monitoring frameworks are **not necessary** for your use case - they're designed for multi-user production systems with high traffic.

---

## What You Actually Need

### ✅ Keep These (Essential)

1. **Composite Scorer V2** - The enhanced scoring system
2. **Evidence Cards** - Explains why foundations were recommended/rejected
3. **Triage Queue** - Manual review for borderline cases (scores 45-58)
4. **Gold Set (Small Sample)** - ~50-100 pairs for validation, not 1,500

### ❌ Skip These (Overkill for Single User)

1. **A/B Testing Framework** - Needs 100s of executions for statistical significance
2. **Drift Monitoring** - Requires months of data, multiple validation points
3. **Large Gold Set (1,500 pairs)** - Designed for enterprise ML validation
4. **Phased Rollout** - No gradual deployment needed for personal use

---

## Simplified Deployment Plan

### Phase 1: Quick Validation (1-2 days)

**Step 1: Create Small Test Set**

Instead of 1,500 labeled pairs, create 20-50 test cases manually:

```python
# Manual test cases - quick validation
test_cases = [
    {
        'profile_ein': '300219424',  # Your org
        'foundation_ein': '541234567',  # Known good match
        'expected': 'PASS',
        'notes': 'Education foundation, VA-based, similar size'
    },
    {
        'profile_ein': '300219424',
        'foundation_ein': '549999999',  # Known mismatch
        'expected': 'FAIL',
        'notes': 'Arts foundation, CA-based, completely different focus'
    },
    # Add 18-48 more realistic examples
]
```

**Step 2: Run Scorer on Test Cases**

```python
from src.scoring import CompositeScoreV2

scorer = CompositeScoreV2()

correct = 0
total = len(test_cases)

for test in test_cases:
    result = scorer.score_foundation_match(
        profile=get_profile(test['profile_ein']),
        foundation=get_foundation(test['foundation_ein'])
    )

    actual = result.decision
    expected = test['expected']

    if actual == expected:
        correct += 1
        print(f"✓ {test['foundation_ein']}: {actual} (correct)")
    else:
        print(f"✗ {test['foundation_ein']}: {actual} (expected {expected})")
        print(f"   Score: {result.final_score:.2f}")
        print(f"   Reason: {test['notes']}")

accuracy = correct / total
print(f"\nAccuracy: {accuracy:.1%} ({correct}/{total})")
```

**Good Enough**: 80%+ accuracy on your test cases

### Phase 2: Direct Deployment (Same Day)

**Just Use It!**

```python
from src.scoring import CompositeScoreV2
from src.scoring.evidence_cards import generate_evidence_collection

# Initialize scorer
scorer = CompositeScoreV2()

# Score foundations for your profile
for foundation in candidate_foundations:

    # Get score
    result = scorer.score_foundation_match(
        profile=your_profile,
        foundation=foundation
    )

    # Review decision
    if result.decision == "PASS":
        print(f"✓ RECOMMENDED: {foundation['name']}")
        print(f"  Score: {result.final_score:.1f}/100")

        # Get evidence cards to understand why
        evidence = generate_evidence_collection(
            profile_ein=your_profile['ein'],
            foundation_ein=foundation['ein'],
            composite_score=result.final_score,
            decision=result.decision,
            scoring_components={
                'ntee': {
                    'ntee_score': result.ntee_score,
                    'profile_ntee': your_profile['ntee'],
                    'foundation_ntee': foundation['ntee'],
                    'match_level': result.ntee_match_level,
                    'citation_date': datetime.now()
                },
                # ... other components
            }
        )

        # Review evidence
        print(f"\n  Evidence:")
        for card in evidence.supporting_cards[:3]:
            print(f"  • {card.title}: {card.summary}")

    elif result.decision == "ABSTAIN":
        print(f"⚠ REVIEW NEEDED: {foundation['name']}")
        print(f"  Score: {result.final_score:.1f}/100 (borderline)")
        print(f"  Manual review recommended")

    else:  # FAIL
        print(f"✗ NOT RECOMMENDED: {foundation['name']}")
        print(f"  Score: {result.final_score:.1f}/100")
```

### Phase 3: Manual Refinement (Ongoing)

**Iterate Based on Your Experience**

Track foundations you apply to and their outcomes:

```python
# Simple tracking file: foundation_outcomes.json
{
    "541234567": {
        "score": 72.5,
        "decision": "PASS",
        "applied": true,
        "outcome": "rejected",  # Update after you hear back
        "notes": "Score was good but they funded larger orgs"
    },
    "549876543": {
        "score": 58.3,
        "decision": "ABSTAIN",
        "applied": true,
        "outcome": "funded",  # This was a good one!
        "notes": "Borderline score but perfect mission match"
    }
}
```

**Adjust Weights Based on Outcomes**

If you notice patterns (e.g., NTEE match more important than score suggests):

```python
# src/scoring/scoring_config.py

# Current weights
COMPOSITE_WEIGHTS_V2 = {
    "ntee": 0.30,
    "geographic": 0.20,
    # ... etc
}

# Adjust based on your experience
# If NTEE match is critical for you:
COMPOSITE_WEIGHTS_V2 = {
    "ntee": 0.35,  # Increased
    "geographic": 0.18,  # Reduced slightly
    # ... rebalance others
}
```

---

## Simplified Architecture

### What You're Actually Using

```
Your Profile
    ↓
Composite Scorer V2
    ├─ NTEE Scoring (two-part)
    ├─ Geographic Match
    ├─ Grant Size Fit
    ├─ Schedule I Voting
    ├─ Payout Sufficiency
    ├─ Application Policy
    ├─ Reliability Safeguards
    └─ Financial Health
    ↓
Decision + Score
    ├─ PASS (≥58): Apply
    ├─ ABSTAIN (45-58): Manual Review
    └─ FAIL (<45): Skip
    ↓
Evidence Cards
    └─ Explains the decision
```

### What to Ignore

- `src/evaluation/ab_testing.py` - **Skip entirely**
- `src/evaluation/drift_monitor.py` - **Skip entirely**
- `src/evaluation/gold_set_evaluator.py` - **Use simplified version**
- `src/evaluation/performance_reporter.py` - **Optional, not critical**

---

## Practical Usage Examples

### Example 1: Batch Score Foundations

```python
from src.scoring import CompositeScoreV2

scorer = CompositeScoreV2()
your_profile = get_profile('300219424')  # Your EIN

# Get all VA foundations from BMF
foundations = get_foundations_by_state('VA')

recommendations = []

for foundation in foundations:
    result = scorer.score_foundation_match(your_profile, foundation)

    if result.decision in ["PASS", "ABSTAIN"]:
        recommendations.append({
            'ein': foundation['ein'],
            'name': foundation['name'],
            'score': result.final_score,
            'decision': result.decision,
            'ntee_match': result.ntee_score,
            'grant_size_fit': result.grant_size_score
        })

# Sort by score
recommendations.sort(key=lambda x: x['score'], reverse=True)

# Review top 20
for i, rec in enumerate(recommendations[:20], 1):
    print(f"{i}. {rec['name']}")
    print(f"   Score: {rec['score']:.1f}, Decision: {rec['decision']}")
    print(f"   NTEE: {rec['ntee_match']:.1f}, Grant Size: {rec['grant_size_fit']:.1f}")
    print()
```

### Example 2: Deep Dive on One Foundation

```python
from src.scoring import CompositeScoreV2
from src.scoring.evidence_cards import EvidenceCardGenerator

scorer = CompositeScoreV2()
generator = EvidenceCardGenerator()

foundation = get_foundation('541234567')
result = scorer.score_foundation_match(your_profile, foundation)

print(f"Foundation: {foundation['name']}")
print(f"Final Score: {result.final_score:.1f}/100")
print(f"Decision: {result.decision}")
print()

# Component scores
print("Component Breakdown:")
print(f"  NTEE Alignment: {result.ntee_score:.1f}")
print(f"  Geographic: {result.geographic_score:.1f}")
print(f"  Grant Size Fit: {result.grant_size_score:.1f}")
print(f"  Schedule I Coherence: {result.coherence_score:.1f}")
print(f"  Payout Sufficiency: {result.payout_score:.1f}")
print(f"  Application Policy: {result.application_policy_score:.1f}")
print(f"  Filing Recency: {result.filing_recency_score:.1f}")
print()

# Generate evidence cards
# ... (code from earlier example)
```

### Example 3: Review Abstain Cases

```python
from src.scoring import get_triage_queue

# Get borderline cases that need manual review
queue = get_triage_queue()

for item in queue.get_pending_items(priority="HIGH"):
    print(f"Foundation: {item.foundation_name}")
    print(f"Score: {item.composite_score:.1f}")
    print(f"Reason for Abstain: {item.abstain_reason}")
    print(f"Missing Data: {', '.join(item.missing_data)}")
    print()

    # Manual decision
    decision = input("Approve? (y/n/skip): ")

    if decision == 'y':
        queue.expert_decision(item.item_id, "PASS", "researcher_name",
                             "Good mission match despite borderline score")
    elif decision == 'n':
        queue.expert_decision(item.item_id, "FAIL", "researcher_name",
                             "Geographic mismatch too significant")
```

---

## Performance Expectations

### Realistic Metrics (Single User)

**Don't worry about**:
- Statistical significance
- P-values, confidence intervals
- Large-scale validation
- Quarterly drift monitoring

**Do care about**:
- Does it find foundations you actually want to apply to?
- Does it filter out obvious mismatches?
- Are the explanations (evidence cards) helpful?

### Good Enough Validation

- **10-20 test cases**: Cover your common scenarios
- **80%+ accuracy**: On your test cases
- **Subjective quality**: "This feels better than my old method"
- **Time savings**: "I'm finding good foundations faster"

---

## When to Adjust

### Signs You Should Tweak Weights

1. **Too many rejections**: Lower the threshold or increase weight on your priority features
2. **Too many poor matches**: Increase threshold or adjust component weights
3. **Missing good foundations**: Review abstain cases, adjust borderline handling
4. **Geographic issues**: Adjust geographic weight for your search radius

### Simple Weight Tuning

```python
# src/scoring/scoring_config.py

# If you find NTEE is most important for you:
COMPOSITE_WEIGHTS_V2 = {
    "ntee": 0.40,           # Increased from 0.30
    "geographic": 0.15,     # Reduced from 0.20
    "coherence": 0.12,
    "financial_health": 0.08,
    "grant_size": 0.08,
    "application_policy": 0.07,
    "filing_recency": 0.06,
    "foundation_type": 0.04,
}

# If geographic match is critical:
COMPOSITE_WEIGHTS_V2 = {
    "ntee": 0.25,
    "geographic": 0.30,     # Increased from 0.20
    "coherence": 0.12,
    # ... adjust others
}
```

---

## Bottom Line

For a single user:

1. **Use the Composite Scorer V2** - It's the actual improvement
2. **Use Evidence Cards** - They explain the decisions
3. **Use Triage Queue** - For manual review of borderline cases
4. **Skip A/B Testing** - You don't have the data volume
5. **Skip Drift Monitoring** - Just re-run periodically if you notice issues
6. **Small validation set** - 20-50 test cases, not 1,500
7. **Manual tracking** - Simple JSON file of outcomes
8. **Adjust as needed** - Based on your real-world results

The complex evaluation infrastructure was built for enterprise deployment with 1000s of users. You just need the scoring engine!

---

**Deployment Time**: 1-2 hours (vs 8-10 weeks for full enterprise deployment)

**Status**: ✅ Ready to use right now with Composite Scorer V2

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
