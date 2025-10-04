"""
Monte Carlo Optimizer - Find Optimal Scoring Parameters

This script uses Monte Carlo simulation to find the optimal scoring weights and thresholds
that minimize INTELLIGENCE costs while maximizing precision and recall.

Strategy:
1. Load discovery results from CSV (exported by scoring_test_harness.py)
2. Generate random parameter combinations (weights, thresholds)
3. Re-score organizations with new parameters
4. Evaluate against optimization criteria:
   - Target qualified count: 10-50 orgs
   - INTELLIGENCE cost: $75-$375 (10-50 × $7.50 avg)
   - Precision: >80% (minimize false positives)
   - Recall: >90% (minimize missed opportunities)
5. Track best parameter sets
6. Export results for validation

Usage:
    python test_framework/monte_carlo_optimizer.py --csv-file DATA.csv --iterations 10000
"""

import sys
import csv
import json
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
from collections import defaultdict

# Optimization Constraints
TARGET_QUALIFIED_MIN = 10
TARGET_QUALIFIED_MAX = 50
INTELLIGENCE_COST_PER_ORG = 7.50  # Average cost (quick $0.75 to complete $42)
TARGET_PRECISION = 0.80  # 80% precision (minimize false positives)
TARGET_RECALL = 0.90     # 90% recall (minimize missed opportunities)

# Parameter Ranges for Monte Carlo Sampling
WEIGHT_RANGES = {
    "mission_alignment": (0.15, 0.35),
    "geographic_fit": (0.10, 0.30),
    "financial_match": (0.10, 0.25),
    "grant_making_capacity": (0.15, 0.40),
    "eligibility": (0.05, 0.15),
    "timing": (0.00, 0.10),
}

THRESHOLD_RANGES = {
    "min_score": (0.50, 0.70),
    "auto_qualified": (0.80, 0.90),
    "review": (0.65, 0.80),
    "consider": (0.50, 0.65),
}


def load_discovery_csv(csv_file: Path) -> List[Dict[str, Any]]:
    """Load discovery results from CSV export."""
    print(f"Loading discovery data from {csv_file}...")

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows):,} organizations")
    return rows


def generate_random_weights() -> Dict[str, float]:
    """Generate random weights that sum to 1.0."""
    weights = {}

    # Sample from ranges
    for dim, (min_val, max_val) in WEIGHT_RANGES.items():
        weights[dim] = random.uniform(min_val, max_val)

    # Normalize to sum to 1.0
    total = sum(weights.values())
    weights = {k: v/total for k, v in weights.items()}

    return weights


def generate_random_thresholds() -> Dict[str, float]:
    """Generate random score thresholds."""
    thresholds = {}

    for name, (min_val, max_val) in THRESHOLD_RANGES.items():
        thresholds[name] = random.uniform(min_val, max_val)

    # Ensure logical ordering: auto > review > consider > min
    thresholds["auto_qualified"] = max(thresholds["auto_qualified"], thresholds["review"] + 0.05)
    thresholds["review"] = max(thresholds["review"], thresholds["consider"] + 0.05)
    thresholds["consider"] = max(thresholds["consider"], thresholds["min_score"] + 0.05)

    return thresholds


def recalculate_score(org: Dict[str, Any], weights: Dict[str, float]) -> float:
    """Recalculate overall score with new weights."""
    score = 0.0

    for dim_name, weight in weights.items():
        dim_score = float(org.get(f"{dim_name}_score", 0))
        score += dim_score * weight

    return score


def apply_parameters(orgs: List[Dict[str, Any]], weights: Dict[str, float],
                    thresholds: Dict[str, float]) -> List[Dict[str, Any]]:
    """Apply new parameters to re-score and re-categorize organizations."""

    rescored = []

    for org in orgs:
        # Recalculate score
        new_score = recalculate_score(org, weights)

        # Recategorize
        if new_score >= thresholds["auto_qualified"]:
            category = "auto_qualified"
        elif new_score >= thresholds["review"]:
            category = "review"
        elif new_score >= thresholds["consider"]:
            category = "consider"
        else:
            category = "low_priority"

        rescored.append({
            **org,
            "new_score": new_score,
            "new_category": category,
        })

    return rescored


def evaluate_parameters(orgs: List[Dict[str, Any]], weights: Dict[str, float],
                       thresholds: Dict[str, float]) -> Dict[str, Any]:
    """Evaluate parameter set against optimization criteria."""

    # Apply parameters
    rescored = apply_parameters(orgs, weights, thresholds)

    # Filter by min threshold
    qualified = [o for o in rescored if o["new_score"] >= thresholds["min_score"]]
    qualified_count = len(qualified)

    # Calculate costs
    intelligence_cost = qualified_count * INTELLIGENCE_COST_PER_ORG

    # Category breakdown
    auto = len([o for o in qualified if o["new_category"] == "auto_qualified"])
    review = len([o for o in qualified if o["new_category"] == "review"])
    consider = len([o for o in qualified if o["new_category"] == "consider"])

    # Calculate fitness score (how well it meets our criteria)
    fitness = 0.0

    # 1. Qualified count penalty (prefer 10-50 range)
    if TARGET_QUALIFIED_MIN <= qualified_count <= TARGET_QUALIFIED_MAX:
        count_score = 1.0
    elif qualified_count < TARGET_QUALIFIED_MIN:
        count_score = qualified_count / TARGET_QUALIFIED_MIN
    else:  # Too many
        count_score = TARGET_QUALIFIED_MAX / qualified_count
    fitness += count_score * 0.40  # 40% weight

    # 2. Cost efficiency (prefer lower intelligence costs)
    target_cost = (TARGET_QUALIFIED_MIN + TARGET_QUALIFIED_MAX) / 2 * INTELLIGENCE_COST_PER_ORG
    if intelligence_cost <= target_cost:
        cost_score = 1.0
    else:
        cost_score = target_cost / intelligence_cost
    fitness += cost_score * 0.20  # 20% weight

    # 3. Precision proxy (prefer higher concentration in auto/review)
    precision_proxy = (auto + review) / qualified_count if qualified_count > 0 else 0
    fitness += precision_proxy * 0.20  # 20% weight

    # 4. Score spread (prefer good separation between categories)
    if len(qualified) > 0:
        scores = [o["new_score"] for o in qualified]
        spread = max(scores) - min(scores)
        spread_score = min(spread / 0.30, 1.0)  # Prefer at least 0.30 spread
    else:
        spread_score = 0
    fitness += spread_score * 0.10  # 10% weight

    # 5. Grant-making weight bonus (encourage focusing on grantors)
    gm_weight = weights.get("grant_making_capacity", 0)
    if gm_weight >= 0.20:
        gm_bonus = min(gm_weight / 0.30, 1.0)
    else:
        gm_bonus = 0
    fitness += gm_bonus * 0.10  # 10% weight

    return {
        "weights": weights,
        "thresholds": thresholds,
        "qualified_count": qualified_count,
        "intelligence_cost": intelligence_cost,
        "category_breakdown": {
            "auto": auto,
            "review": review,
            "consider": consider
        },
        "fitness": fitness,
        "count_score": count_score,
        "cost_score": cost_score,
        "precision_proxy": precision_proxy,
        "spread_score": spread_score,
        "gm_bonus": gm_bonus,
    }


def run_monte_carlo(orgs: List[Dict[str, Any]], iterations: int = 10000) -> List[Dict[str, Any]]:
    """Run Monte Carlo optimization."""

    print(f"\nRunning Monte Carlo optimization ({iterations:,} iterations)...")
    print("="*70)

    results = []
    best_fitness = 0

    for i in range(iterations):
        # Generate random parameters
        weights = generate_random_weights()
        thresholds = generate_random_thresholds()

        # Evaluate
        result = evaluate_parameters(orgs, weights, thresholds)
        results.append(result)

        # Track best
        if result["fitness"] > best_fitness:
            best_fitness = result["fitness"]
            print(f"\n[Iteration {i+1:,}] New best fitness: {best_fitness:.4f}")
            print(f"  Qualified: {result['qualified_count']}")
            print(f"  Cost: ${result['intelligence_cost']:.2f}")
            print(f"  Auto: {result['category_breakdown']['auto']}, "
                  f"Review: {result['category_breakdown']['review']}, "
                  f"Consider: {result['category_breakdown']['consider']}")

        # Progress indicator
        if (i + 1) % 1000 == 0:
            print(f"[Progress] {i+1:,}/{iterations:,} iterations complete")

    return results


def export_results(results: List[Dict[str, Any]], export_dir: Path, csv_file: Path):
    """Export optimization results."""

    export_dir.mkdir(parents=True, exist_ok=True)

    # Sort by fitness
    results.sort(key=lambda x: x["fitness"], reverse=True)

    # Export top 20 parameter sets
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    top_results_file = export_dir / f"monte_carlo_top20_{timestamp}.json"

    with open(top_results_file, 'w') as f:
        json.dump(results[:20], f, indent=2)

    print(f"\n[OK] Exported top 20 parameter sets to {top_results_file}")

    # Export summary statistics
    summary_file = export_dir / f"monte_carlo_summary_{timestamp}.txt"

    with open(summary_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("MONTE CARLO OPTIMIZATION RESULTS\n")
        f.write("="*70 + "\n\n")
        f.write(f"Input CSV: {csv_file}\n")
        f.write(f"Total iterations: {len(results):,}\n")
        f.write(f"Timestamp: {timestamp}\n\n")

        f.write("TOP 10 PARAMETER SETS:\n")
        f.write("-"*70 + "\n\n")

        for i, result in enumerate(results[:10], 1):
            f.write(f"Rank #{i}:\n")
            f.write(f"  Fitness Score: {result['fitness']:.4f}\n")
            f.write(f"  Qualified Count: {result['qualified_count']}\n")
            f.write(f"  Intelligence Cost: ${result['intelligence_cost']:.2f}\n")
            f.write(f"  Breakdown: Auto={result['category_breakdown']['auto']}, "
                   f"Review={result['category_breakdown']['review']}, "
                   f"Consider={result['category_breakdown']['consider']}\n")
            f.write(f"\n  Weights:\n")
            for dim, weight in result['weights'].items():
                f.write(f"    {dim}: {weight:.3f}\n")
            f.write(f"\n  Thresholds:\n")
            for name, threshold in result['thresholds'].items():
                f.write(f"    {name}: {threshold:.3f}\n")
            f.write("\n" + "-"*70 + "\n\n")

    print(f"[OK] Exported summary to {summary_file}")

    return top_results_file, summary_file


def main():
    """Main Monte Carlo optimization."""
    import argparse

    parser = argparse.ArgumentParser(description='Monte Carlo Parameter Optimization')
    parser.add_argument('--csv-file', required=True, help='Discovery CSV file from scoring harness')
    parser.add_argument('--iterations', type=int, default=10000, help='Number of MC iterations')
    parser.add_argument('--export-dir', default='test_framework/monte_carlo_results',
                       help='Export directory for results')
    args = parser.parse_args()

    csv_file = Path(args.csv_file)
    export_dir = Path(args.export_dir)

    if not csv_file.exists():
        print(f"ERROR: CSV file not found: {csv_file}")
        return

    print("="*70)
    print("MONTE CARLO PARAMETER OPTIMIZATION")
    print("="*70)
    print(f"Input: {csv_file}")
    print(f"Iterations: {args.iterations:,}")
    print(f"Target qualified: {TARGET_QUALIFIED_MIN}-{TARGET_QUALIFIED_MAX} orgs")
    print(f"Target cost: ${TARGET_QUALIFIED_MIN * INTELLIGENCE_COST_PER_ORG:.2f}-"
          f"${TARGET_QUALIFIED_MAX * INTELLIGENCE_COST_PER_ORG:.2f}")
    print("="*70)

    # Load data
    orgs = load_discovery_csv(csv_file)

    # Run optimization
    results = run_monte_carlo(orgs, args.iterations)

    # Export
    top_file, summary_file = export_results(results, export_dir, csv_file)

    # Display best result
    best = results[0]
    print("\n" + "="*70)
    print("OPTIMIZATION COMPLETE")
    print("="*70)
    print(f"\nBest Parameter Set (Fitness: {best['fitness']:.4f}):")
    print(f"  Qualified Count: {best['qualified_count']} orgs")
    print(f"  Intelligence Cost: ${best['intelligence_cost']:.2f}")
    print(f"  Category Breakdown:")
    print(f"    - Auto-Qualified: {best['category_breakdown']['auto']}")
    print(f"    - Review: {best['category_breakdown']['review']}")
    print(f"    - Consider: {best['category_breakdown']['consider']}")
    print(f"\n  Optimized Weights:")
    for dim, weight in sorted(best['weights'].items(), key=lambda x: x[1], reverse=True):
        print(f"    {dim:25s}: {weight:.3f} ({weight*100:.1f}%)")
    print(f"\n  Optimized Thresholds:")
    for name, threshold in sorted(best['thresholds'].items(), key=lambda x: x[1], reverse=True):
        print(f"    {name:20s}: {threshold:.3f}")

    print(f"\nResults exported to: {export_dir}")
    print("="*70)


if __name__ == "__main__":
    main()
