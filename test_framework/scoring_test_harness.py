"""
Scoring Test Harness - Export Discovery Results for Monte Carlo Optimization

This script:
1. Runs discovery on all test profiles
2. Exports detailed scoring data to CSV
3. Allows configurable scoring weights for parameter testing
4. Generates statistics for Monte Carlo optimization input

Usage:
    python test_framework/scoring_test_harness.py [--profile PROFILE_ID] [--export-dir DIR]
"""

import sys
import os
import csv
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

# API Configuration
API_BASE = "http://localhost:8000/api/v2"

# Test Profiles
TEST_PROFILES = [
    "profile_f3adef3b653c",  # Heros Bridge
    "profile_aefa1d788b1e",  # Fauquier Free Clinic
    "profile_b3db970a10ff",  # Ford Foundation
]

# Scoring Configuration (for testing different parameter sets)
DEFAULT_SCORING_CONFIG = {
    "min_score_threshold": 0.55,
    "max_return_limit": 5000,  # High limit to capture all qualified
    "weights": {
        "mission_alignment": 0.25,
        "geographic_fit": 0.20,
        "financial_match": 0.15,
        "grant_making_capacity": 0.25,
        "eligibility": 0.10,
        "timing": 0.05
    },
    "grant_tiers": {
        "tier1_min": 10000,   # $10K-$25K
        "tier2_min": 25000,   # $25K-$100K
        "tier3_min": 100000,  # $100K-$500K
        "tier4_min": 500000,  # $500K+
    }
}


def run_discovery(profile_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run discovery for a profile with optional custom configuration."""
    if config is None:
        config = DEFAULT_SCORING_CONFIG

    url = f"{API_BASE}/profiles/{profile_id}/discover"

    # Extract request parameters (not weights - those are server-side)
    request_data = {
        "min_score_threshold": config.get("min_score_threshold", 0.55),
        "max_return_limit": config.get("max_return_limit", 5000)
    }

    print(f"Running discovery for {profile_id}...")
    print(f"  Threshold: {request_data['min_score_threshold']}")
    print(f"  Max limit: {request_data['max_return_limit']}")

    try:
        response = requests.post(url, json=request_data, timeout=300)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Discovery failed for {profile_id}: {e}")
        return None


def export_to_csv(profile_id: str, discovery_data: Dict[str, Any], export_dir: Path):
    """Export discovery results to CSV for analysis."""

    if not discovery_data or discovery_data.get('status') != 'success':
        print(f"Skipping export for {profile_id} - no valid data")
        return

    # Create export directory
    export_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = export_dir / f"discovery_{profile_id}_{timestamp}.csv"

    opportunities = discovery_data.get('opportunities', [])

    if not opportunities:
        print(f"No opportunities to export for {profile_id}")
        return

    # Define CSV columns
    fieldnames = [
        'organization_name',
        'ein',
        'state',
        'city',
        'revenue',
        'overall_score',
        'confidence',
        'stage_category',
        'foundation_code',
        'grants_distributed',
        'mission_alignment_score',
        'mission_alignment_weight',
        'geographic_fit_score',
        'geographic_fit_weight',
        'financial_match_score',
        'financial_match_weight',
        'grant_making_capacity_score',
        'grant_making_capacity_weight',
        'eligibility_score',
        'eligibility_weight',
        'timing_score',
        'timing_weight',
    ]

    # Write CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for opp in opportunities:
            dims = opp.get('dimensional_scores', {})
            gm = dims.get('grant_making_capacity', {})

            row = {
                'organization_name': opp.get('organization_name', ''),
                'ein': opp.get('ein', ''),
                'state': opp.get('location', {}).get('state', ''),
                'city': opp.get('location', {}).get('city', ''),
                'revenue': opp.get('revenue', 0),
                'overall_score': opp.get('overall_score', 0),
                'confidence': opp.get('confidence', ''),
                'stage_category': opp.get('stage_category', ''),
                'foundation_code': gm.get('foundation_code', ''),
                'grants_distributed': gm.get('grants_distributed', 0),
            }

            # Add dimensional scores
            for dim_name in ['mission_alignment', 'geographic_fit', 'financial_match',
                            'grant_making_capacity', 'eligibility', 'timing']:
                dim_data = dims.get(dim_name, {})
                row[f'{dim_name}_score'] = dim_data.get('raw_score', 0)
                row[f'{dim_name}_weight'] = dim_data.get('weight', 0)

            writer.writerow(row)

    print(f"[OK] Exported {len(opportunities)} opportunities to {csv_file}")
    return csv_file


def export_summary_stats(profile_id: str, discovery_data: Dict[str, Any], export_dir: Path):
    """Export summary statistics for Monte Carlo analysis."""

    if not discovery_data or discovery_data.get('status') != 'success':
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stats_file = export_dir / f"stats_{profile_id}_{timestamp}.json"

    summary = discovery_data.get('summary', {})
    performance = discovery_data.get('performance', {})

    stats = {
        "profile_id": profile_id,
        "timestamp": timestamp,
        "summary": summary,
        "performance": performance,
        "funnel_metrics": {
            "bmf_to_scored_ratio": summary.get('total_scored', 0) / summary.get('total_bmf_matches', 1),
            "scored_to_qualified_ratio": summary.get('total_qualified', 0) / summary.get('total_scored', 1),
            "qualification_rate": summary.get('total_qualified', 0) / summary.get('total_bmf_matches', 1),
        },
        "category_distribution": {
            "auto_qualified": summary.get('auto_qualified', 0),
            "review": summary.get('review', 0),
            "consider": summary.get('consider', 0),
            "low_priority": summary.get('low_priority', 0),
        }
    }

    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"[OK] Exported statistics to {stats_file}")
    return stats_file


def main():
    """Main test harness execution."""
    import argparse

    parser = argparse.ArgumentParser(description='Scoring Test Harness for Monte Carlo Optimization')
    parser.add_argument('--profile', help='Specific profile ID to test (default: all test profiles)')
    parser.add_argument('--export-dir', default='test_framework/monte_carlo_data',
                       help='Export directory for CSV files')
    parser.add_argument('--threshold', type=float, help='Override min_score_threshold')
    args = parser.parse_args()

    # Determine profiles to test
    if args.profile:
        profiles = [args.profile]
    else:
        profiles = TEST_PROFILES

    export_dir = Path(args.export_dir)

    # Override config if specified
    config = DEFAULT_SCORING_CONFIG.copy()
    if args.threshold:
        config['min_score_threshold'] = args.threshold

    print("="*70)
    print("SCORING TEST HARNESS - Monte Carlo Data Collection")
    print("="*70)
    print(f"Testing {len(profiles)} profile(s)")
    print(f"Export directory: {export_dir}")
    print(f"Configuration: {json.dumps(config, indent=2)}")
    print("="*70)
    print()

    results = []

    for profile_id in profiles:
        print(f"\n{'='*70}")
        print(f"Testing Profile: {profile_id}")
        print(f"{'='*70}")

        # Run discovery
        start_time = time.time()
        discovery_data = run_discovery(profile_id, config)
        elapsed = time.time() - start_time

        if not discovery_data:
            print(f"[FAIL] Discovery failed for {profile_id}")
            continue

        print(f"[OK] Discovery completed in {elapsed:.2f}s")

        # Display summary
        summary = discovery_data.get('summary', {})
        print(f"\nResults:")
        print(f"  BMF Matches: {summary.get('total_bmf_matches', 0):,}")
        print(f"  Scored: {summary.get('total_scored', 0):,}")
        print(f"  Qualified: {summary.get('total_qualified', 0):,}")
        print(f"    - Auto: {summary.get('auto_qualified', 0)}")
        print(f"    - Review: {summary.get('review', 0)}")
        print(f"    - Consider: {summary.get('consider', 0)}")

        # Export data
        csv_file = export_to_csv(profile_id, discovery_data, export_dir)
        stats_file = export_summary_stats(profile_id, discovery_data, export_dir)

        results.append({
            'profile_id': profile_id,
            'csv_file': str(csv_file) if csv_file else None,
            'stats_file': str(stats_file) if stats_file else None,
            'qualified_count': summary.get('total_qualified', 0),
            'execution_time': elapsed
        })

    # Summary report
    print(f"\n{'='*70}")
    print("TEST HARNESS COMPLETE")
    print(f"{'='*70}")
    print(f"Profiles tested: {len(results)}")
    print(f"Exports saved to: {export_dir}")
    print(f"\nNext step: Run Monte Carlo optimization on exported data")
    print(f"{'='*70}")

    return results


if __name__ == "__main__":
    main()
