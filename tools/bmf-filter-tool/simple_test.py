#!/usr/bin/env python3
"""
Simple validation test for BMF Filter Tool
"""

import os
import sys
import asyncio
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Set up test environment
os.environ['BMF_INPUT_PATH'] = 'test_data/sample_bmf.csv'
os.environ['BMF_FILTER_CONFIG_PATH'] = 'test_data/sample_config.json'
os.environ['BMF_CACHE_ENABLED'] = 'false'

async def test_basic():
    """Simple basic test"""
    try:
        from app.bmf_filter import BMFFilterTool
        from app.generated import BMFFilterIntent, BMFFilterCriteria

        print("SUCCESS: Imports working")

        tool = BMFFilterTool()
        print(f"SUCCESS: Tool initialized")
        print(f"Input path: {tool.input_path}")
        print(f"Default NTEE codes: {tool.default_ntee_codes}")

        # Test basic filtering
        intent = BMFFilterIntent(
            criteria=BMFFilterCriteria(
                states=["VA"],
                limit=5
            ),
            what_youre_looking_for="Test filtering"
        )

        result = await tool.execute(intent)
        print(f"SUCCESS: Found {len(result.organizations)} organizations")
        print(f"Execution time: {result.execution_metadata.execution_time_ms:.1f}ms")

        if result.organizations:
            org = result.organizations[0]
            print(f"Sample: {org.name} in {org.state}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("BMF Filter Tool - Simple Test")
    print("=" * 40)

    success = await test_basic()

    if success:
        print("\nSUCCESS: Basic functionality working!")
        print("\nNext steps:")
        print("- Run server: python app/server.py")
        print("- Run full demo: python app/main.py")
    else:
        print("\nERROR: Basic test failed")

    return success

if __name__ == "__main__":
    asyncio.run(main())