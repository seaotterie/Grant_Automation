"""
Test optimized scoring across all 5 test profiles
"""
import requests
import json
import time
from pathlib import Path
from datetime import datetime

API_BASE = "http://localhost:8000/api/v2"

# All 5 test profiles
TEST_PROFILES = [
    "profile_f3adef3b653c",  # Heros Bridge
    "profile_aefa1d788b1e",  # Fauquier Free Clinic
    "profile_b3db970a10ff",  # Ford Foundation
]

def test_profile(profile_id: str):
    """Run discovery and collect results for a profile."""
    print(f"\n{'='*70}")
    print(f"Testing Profile: {profile_id}")
    print(f"{'='*70}")

    url = f"{API_BASE}/profiles/{profile_id}/discover"
    request_data = {
        "min_score_threshold": 0.62,  # NEW optimized threshold
        "max_return_limit": 5000
    }

    start_time = time.time()

    try:
        response = requests.post(url, json=request_data, timeout=120)
        elapsed = time.time() - start_time

        if response.status_code != 200:
            print(f"[ERROR] HTTP {response.status_code}: {response.text[:200]}")
            return None

        data = response.json()

        if data.get('status') != 'success':
            print(f"[ERROR] Discovery failed: {data}")
            return None

        summary = data.get('summary', {})
        performance = data.get('performance', {})
        opportunities = data.get('opportunities', [])

        # Analyze top opportunities
        top_10 = opportunities[:10]
        grants_in_top_10 = sum(1 for opp in top_10
                               if opp.get('dimensional_scores', {})
                                     .get('grant_making_capacity', {})
                                     .get('grants_distributed', 0) > 0)

        results = {
            'profile_id': profile_id,
            'status': 'success',
            'execution_time': elapsed,
            'total_bmf': summary.get('total_bmf_matches', 0),
            'total_scored': summary.get('total_scored', 0),
            'total_qualified': summary.get('total_qualified', 0),
            'auto_qualified': summary.get('auto_qualified', 0),
            'review': summary.get('review', 0),
            'consider': summary.get('consider', 0),
            'low_priority': summary.get('low_priority', 0),
            'intelligence_cost': summary.get('total_qualified', 0) * 7.50,
            'grants_in_top_10': grants_in_top_10,
            'top_10': [
                {
                    'name': opp.get('organization_name', ''),
                    'score': opp.get('overall_score', 0),
                    'grant_cap_score': opp.get('dimensional_scores', {}).get('grant_making_capacity', {}).get('raw_score', 0),
                    'foundation_code': opp.get('dimensional_scores', {}).get('grant_making_capacity', {}).get('foundation_code', ''),
                    'grants': opp.get('dimensional_scores', {}).get('grant_making_capacity', {}).get('grants_distributed', 0),
                }
                for opp in top_10
            ]
        }

        # Print summary
        print(f"\n[OK] Discovery completed in {elapsed:.2f}s")
        print(f"\nResults:")
        print(f"  BMF Matches: {results['total_bmf']:,}")
        print(f"  Scored: {results['total_scored']:,}")
        print(f"  Qualified (≥0.62): {results['total_qualified']:,}")
        print(f"    - Auto-Qualified (≥0.74): {results['auto_qualified']}")
        print(f"    - Review (≥0.71): {results['review']}")
        print(f"    - Consider (≥0.68): {results['consider']}")
        print(f"    - Low Priority (≥0.62): {results['low_priority']}")
        print(f"  Intelligence Cost: ${results['intelligence_cost']:,.2f}")
        print(f"  Orgs with grants in top 10: {results['grants_in_top_10']}/10")

        print(f"\n  Top 10 Organizations:")
        for i, org in enumerate(results['top_10'], 1):
            print(f"  {i:2d}. Score={org['score']:.3f} GrantCap={org['grant_cap_score']:.2f} - {org['name'][:50]}")
            print(f"      FC:{org['foundation_code']:2s} Grants:${org['grants']:>12,.0f}")

        return results

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return None


def main():
    """Test all profiles and generate comparison report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("="*70)
    print("OPTIMIZED SCORING TEST - ALL PROFILES")
    print("="*70)
    print(f"Timestamp: {timestamp}")
    print(f"Testing {len(TEST_PROFILES)} profiles")
    print(f"\nOptimized Parameters:")
    print(f"  Weights: grant_making=36%, mission=23%, financial=16%, geo=11%, timing=8%, eligibility=7%")
    print(f"  Thresholds: min=0.62, consider=0.68, review=0.71, auto=0.74")
    print("="*70)

    all_results = []

    for profile_id in TEST_PROFILES:
        result = test_profile(profile_id)
        if result:
            all_results.append(result)
        time.sleep(2)  # Brief pause between tests

    # Generate comparison report
    print(f"\n\n{'='*70}")
    print("COMPARISON REPORT")
    print(f"{'='*70}\n")

    if not all_results:
        print("[ERROR] No successful results to compare")
        return

    print(f"{'Profile':<30} {'Qualified':<12} {'Cost':<12} {'Top10 w/Grants':<15}")
    print(f"{'-'*70}")

    for result in all_results:
        print(f"{result['profile_id']:<30} "
              f"{result['total_qualified']:<12,} "
              f"${result['intelligence_cost']:<11,.2f} "
              f"{result['grants_in_top_10']}/10")

    # Summary statistics
    avg_qualified = sum(r['total_qualified'] for r in all_results) / len(all_results)
    avg_cost = sum(r['intelligence_cost'] for r in all_results) / len(all_results)
    avg_grants_in_top = sum(r['grants_in_top_10'] for r in all_results) / len(all_results)

    print(f"{'-'*70}")
    print(f"{'AVERAGE':<30} {avg_qualified:<12,.0f} ${avg_cost:<11,.2f} {avg_grants_in_top:.1f}/10")

    print(f"\n{'='*70}")
    print("KEY INSIGHTS")
    print(f"{'='*70}")
    print(f"1. Average qualified orgs: {avg_qualified:,.0f}")
    print(f"2. Average intelligence cost: ${avg_cost:,.2f}")
    print(f"3. Average grants in top 10: {avg_grants_in_top:.1f}/10 ({avg_grants_in_top*10:.0f}%)")

    # Export results
    export_dir = Path("test_framework/profile_comparison")
    export_dir.mkdir(parents=True, exist_ok=True)

    export_file = export_dir / f"comparison_{timestamp}.json"
    with open(export_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n[OK] Results exported to {export_file}")
    print("="*70)


if __name__ == "__main__":
    main()
