#!/usr/bin/env python3
"""
Show actual input/output data from BMF Filter Tool
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Set up test environment
os.environ['BMF_INPUT_PATH'] = 'test_data/sample_bmf.csv'
os.environ['BMF_FILTER_CONFIG_PATH'] = 'test_data/sample_config.json'
os.environ['BMF_CACHE_ENABLED'] = 'false'

from app.bmf_filter import BMFFilterTool
from app.generated import BMFFilterIntent, BMFFilterCriteria

async def show_actual_data():
    """Show the actual input data and output results"""

    print("BMF Filter Tool - Actual Input/Output Data")
    print("=" * 50)

    # Show the CSV data we're working with
    print("\nINPUT DATA (CSV):")
    print("-" * 20)
    csv_path = 'test_data/sample_bmf.csv'
    with open(csv_path, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            print(f"{i+1:2}: {line.strip()}")

    # Initialize tool
    tool = BMFFilterTool()

    # Test 1: Find VA Education Organizations
    print("\n" + "=" * 50)
    print("TEST 1: Virginia Education Organizations")
    print("=" * 50)

    intent1 = BMFFilterIntent(
        criteria=BMFFilterCriteria(
            states=['VA'],
            ntee_codes=['P20'],
            limit=5
        ),
        what_youre_looking_for='Virginia Education Organizations'
    )

    print("\nINPUT CRITERIA:")
    print(f"  States: {intent1.criteria.states}")
    print(f"  NTEE Codes: {intent1.criteria.ntee_codes}")
    print(f"  Limit: {intent1.criteria.limit}")
    print(f"  Looking for: '{intent1.what_youre_looking_for}'")

    result1 = await tool.execute(intent1)

    print(f"\nOUTPUT RESULTS:")
    print(f"  Organizations Found: {len(result1.organizations)}")
    print(f"  Execution Time: {result1.execution_metadata.execution_time_ms:.1f}ms")
    print(f"  Total Records Processed: {result1.summary.total_in_database}")

    print("\n  Organizations:")
    for i, org in enumerate(result1.organizations, 1):
        print(f"    {i}. {org.name}")
        print(f"       EIN: {org.ein}")
        print(f"       Location: {org.city}, {org.state}")
        print(f"       NTEE: {org.ntee_code} ({org.ntee_description})")
        print(f"       Revenue: ${org.revenue:,}")
        print(f"       Assets: ${org.assets:,}")
        print(f"       Match Reasons: {', '.join(org.match_reasons)}")
        print()

    # Test 2: Multi-state Health Organizations
    print("=" * 50)
    print("TEST 2: Multi-State Health Organizations")
    print("=" * 50)

    intent2 = BMFFilterIntent(
        criteria=BMFFilterCriteria(
            states=['VA', 'MD', 'DC'],
            ntee_codes=['B25'],
            revenue_min=1000000,
            limit=5
        ),
        what_youre_looking_for='Large Health Organizations in DMV Area'
    )

    print("\nINPUT CRITERIA:")
    print(f"  States: {intent2.criteria.states}")
    print(f"  NTEE Codes: {intent2.criteria.ntee_codes}")
    print(f"  Revenue Min: ${intent2.criteria.revenue_min:,}")
    print(f"  Limit: {intent2.criteria.limit}")
    print(f"  Looking for: '{intent2.what_youre_looking_for}'")

    result2 = await tool.execute(intent2)

    print(f"\nOUTPUT RESULTS:")
    print(f"  Organizations Found: {len(result2.organizations)}")
    print(f"  Execution Time: {result2.execution_metadata.execution_time_ms:.1f}ms")
    print(f"  Geographic Distribution: {result2.summary.geographic_distribution}")
    print(f"  Financial Summary: {result2.summary.financial_summary}")

    print("\n  Organizations:")
    for i, org in enumerate(result2.organizations, 1):
        print(f"    {i}. {org.name}")
        print(f"       EIN: {org.ein}")
        print(f"       Location: {org.city}, {org.state}")
        print(f"       NTEE: {org.ntee_code} ({org.ntee_description})")
        print(f"       Revenue: ${org.revenue:,}")
        print(f"       Assets: ${org.assets:,}")
        print(f"       Match Reasons: {', '.join(org.match_reasons)}")
        print()

    # Test 3: Show all data to see what's available
    print("=" * 50)
    print("TEST 3: All Available Organizations")
    print("=" * 50)

    intent3 = BMFFilterIntent(
        criteria=BMFFilterCriteria(
            limit=20  # Get all
        ),
        what_youre_looking_for='All organizations in dataset'
    )

    result3 = await tool.execute(intent3)

    print(f"\nDATASET OVERVIEW:")
    print(f"  Total Organizations: {len(result3.organizations)}")
    print(f"  States Represented: {set(org.state for org in result3.organizations)}")
    print(f"  NTEE Codes: {set(org.ntee_code for org in result3.organizations)}")
    print(f"  Revenue Range: ${min(org.revenue for org in result3.organizations):,} - ${max(org.revenue for org in result3.organizations):,}")

    print("\n  Complete List:")
    for i, org in enumerate(result3.organizations, 1):
        print(f"    {i:2}. {org.name} ({org.state}) - {org.ntee_code} - ${org.revenue:,}")

if __name__ == "__main__":
    asyncio.run(show_actual_data())