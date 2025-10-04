"""
Analyze category distribution with optimized weights
"""
import csv
import statistics
from pathlib import Path

# Load the CSV data (use latest export)
csv_file = Path('test_framework/monte_carlo_data/discovery_profile_f3adef3b653c_20251004_155239.csv')

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    orgs = list(reader)

print(f'Total organizations: {len(orgs)}')

# Apply optimized weights from best Monte Carlo result
weights = {
    'mission_alignment': 0.230,
    'geographic_fit': 0.108,
    'financial_match': 0.156,
    'grant_making_capacity': 0.358,
    'eligibility': 0.069,
    'timing': 0.078
}

# Percentile-based thresholds (implemented in production)
thresholds = {
    'min_score': 0.62,  # 50th percentile - baseline qualification
    'auto_qualified': 0.74,  # ~99.5th percentile - best matches
    'review': 0.71,  # ~97th percentile - strong candidates
    'consider': 0.68  # ~90th percentile - worth deeper look
}

# Recalculate scores
categories = {
    'auto_qualified': 0,
    'review': 0,
    'consider': 0,
    'low_priority': 0,
    'no_match': 0
}

scores = []

for org in orgs:
    # Recalculate overall score with new weights
    score = 0.0
    for dim, weight in weights.items():
        dim_score = float(org.get(f'{dim}_score', 0))
        score += dim_score * weight

    scores.append(score)

    # Categorize
    if score >= thresholds['auto_qualified']:
        categories['auto_qualified'] += 1
    elif score >= thresholds['review']:
        categories['review'] += 1
    elif score >= thresholds['consider']:
        categories['consider'] += 1
    elif score >= thresholds['min_score']:
        categories['low_priority'] += 1
    else:
        categories['no_match'] += 1

# Summary
print(f'\n=== CATEGORY DISTRIBUTION (Optimized Weights) ===')
print(f'Auto-Qualified (>={thresholds["auto_qualified"]:.3f}): {categories["auto_qualified"]:4d} ({categories["auto_qualified"]/len(orgs)*100:5.2f}%)')
print(f'Review         (>={thresholds["review"]:.3f}): {categories["review"]:4d} ({categories["review"]/len(orgs)*100:5.2f}%)')
print(f'Consider       (>={thresholds["consider"]:.3f}): {categories["consider"]:4d} ({categories["consider"]/len(orgs)*100:5.2f}%)')
print(f'Low Priority   (>={thresholds["min_score"]:.3f}): {categories["low_priority"]:4d} ({categories["low_priority"]/len(orgs)*100:5.2f}%)')
print(f'No Match       (<{thresholds["min_score"]:.3f}): {categories["no_match"]:4d} ({categories["no_match"]/len(orgs)*100:5.2f}%)')
print(f'\nQualified (>=min_score): {sum([categories["auto_qualified"], categories["review"], categories["consider"], categories["low_priority"]])} orgs')
print(f'Intelligence Cost: ${sum([categories["auto_qualified"], categories["review"], categories["consider"], categories["low_priority"]]) * 7.50:.2f}')

# Score distribution
print(f'\n=== SCORE DISTRIBUTION ===')
print(f'Min:    {min(scores):.4f}')
print(f'Max:    {max(scores):.4f}')
print(f'Mean:   {statistics.mean(scores):.4f}')
print(f'Median: {statistics.median(scores):.4f}')
print(f'StdDev: {statistics.stdev(scores):.4f}')

# Show top 20 scoring orgs
print(f'\n=== TOP 20 ORGANIZATIONS (by optimized score) ===')
org_scores = [(org, score) for org, score in zip(orgs, scores)]
org_scores.sort(key=lambda x: x[1], reverse=True)

for i, (org, score) in enumerate(org_scores[:20], 1):
    name = org.get('organization_name', 'Unknown')[:50]
    foundation_code = org.get('foundation_code', 'N/A')
    grants = float(org.get('grants_distributed', 0))

    # Determine category
    if score >= thresholds['auto_qualified']:
        cat = 'AUTO'
    elif score >= thresholds['review']:
        cat = 'REVIEW'
    elif score >= thresholds['consider']:
        cat = 'CONSIDER'
    elif score >= thresholds['min_score']:
        cat = 'LOW'
    else:
        cat = 'NO MATCH'

    print(f'{i:2d}. [{cat:8s}] {score:.4f} - {name}')
    print(f'    Foundation: {foundation_code}, Grants: ${grants:,.0f}')
