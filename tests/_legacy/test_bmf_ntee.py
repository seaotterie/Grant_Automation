"""
Test BMF Discovery Tool with NTEE Filters
Phase 8, Task 11
"""
import sys
import os
import asyncio
sys.path.insert(0, 'tools/bmf-filter-tool')

from app.bmf_filter import BMFFilterTool, BMFFilterCriteria

# Set database path
os.environ['BMF_DATABASE_PATH'] = 'data/nonprofit_intelligence.db'

async def test_ntee_filtering():
    """Test BMF filtering with NTEE codes P20 (Human Services) and B25 (Schools)"""
    print("=" * 60)
    print("BMF Discovery Tool - NTEE Filter Test")
    print("=" * 60)

    # Initialize tool
    tool = BMFFilterTool()
    print("[OK] Tool initialized successfully")
    print(f"Database: {tool.database_path}")
    print()

    # Test 1: Health & Nutrition nonprofits in Virginia
    print("Test 1: Health & Nutrition Nonprofits in Virginia")
    print("-" * 60)
    criteria = BMFFilterCriteria(
        ntee_codes=["E", "K"],  # E = Health, K = Food/Nutrition
        states=["VA"],
        min_revenue=100000,
        max_revenue=10000000
    )

    result = await tool.execute(criteria)
    print(f"Organizations found: {result.total_count}")
    print(f"Execution time: {result.execution_metadata['duration_seconds']:.3f}s")
    print()

    if result.organizations:
        print("Sample results:")
        for i, org in enumerate(result.organizations[:5], 1):
            print(f"  {i}. {org.name} ({org.city}, {org.state})")
            print(f"     NTEE: {org.ntee_code} | Revenue: ${org.revenue:,.0f}")
        print()

    # Test 2: Human Services & Schools (P20, B25)
    print("Test 2: Human Services & Schools in Virginia")
    print("-" * 60)
    criteria = BMFFilterCriteria(
        ntee_codes=["P20", "B25"],
        states=["VA"],
        min_revenue=500000,
        max_revenue=50000000
    )

    result = await tool.execute(criteria)
    print(f"Organizations found: {result.total_count}")
    print(f"Execution time: {result.execution_metadata['duration_seconds']:.3f}s")
    print()

    if result.organizations:
        print("Sample results:")
        for i, org in enumerate(result.organizations[:5], 1):
            print(f"  {i}. {org.name} ({org.city}, {org.state})")
            print(f"     NTEE: {org.ntee_code} | Revenue: ${org.revenue:,.0f}")
        print()

    # Test 3: Multi-state discovery
    print("Test 3: Multi-State Health Nonprofits")
    print("-" * 60)
    criteria = BMFFilterCriteria(
        ntee_codes=["E"],  # Health
        states=["VA", "MD", "DC"],
        min_revenue=1000000,
        max_revenue=100000000
    )

    result = await tool.execute(criteria)
    print(f"Organizations found: {result.total_count}")
    print(f"Execution time: {result.execution_metadata['duration_seconds']:.3f}s")

    # Count by state
    if result.organizations:
        state_counts = {}
        for org in result.organizations:
            state_counts[org.state] = state_counts.get(org.state, 0) + 1
        print("\nDistribution by state:")
        for state, count in sorted(state_counts.items()):
            print(f"  {state}: {count} organizations")

    print("\n" + "=" * 60)
    print("[SUCCESS] All tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(test_ntee_filtering())
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
