import csv
from pathlib import Path

csv_file = Path('test_framework/monte_carlo_data/discovery_profile_f3adef3b653c_20251004_155613.csv')

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Sort by overall_score
rows_sorted = sorted(rows, key=lambda x: float(x['overall_score']), reverse=True)

print('=== TOP 20 ORGANIZATIONS (NEW Evidence-Based Scoring) ===\n')
for i, row in enumerate(rows_sorted[:20], 1):
    overall = float(row['overall_score'])
    grant_cap = float(row['grant_making_capacity_score'])
    name = row['organization_name'][:50]
    fc = row.get('foundation_code', 'N/A')
    grants = float(row.get('grants_distributed', 0) or 0)

    print(f'{i:2d}. Score={overall:.4f} GrantCap={grant_cap:.2f} - {name:50s}')
    print(f'    FC:{fc:2s} Grants:${grants:>12,.0f}')
    print()
