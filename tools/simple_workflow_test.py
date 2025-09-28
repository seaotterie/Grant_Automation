"""
Simple Two-Tool Workflow Test - Direct Import
"""

import sys
import os
import asyncio
import time

# Add both tool directories to path for direct imports
current_dir = os.path.dirname(os.path.abspath(__file__))
bmf_tool_path = os.path.join(current_dir, 'bmf-filter-tool', 'app')
form990_tool_path = os.path.join(current_dir, 'form990-analysis-tool', 'app')

sys.path.insert(0, bmf_tool_path)
sys.path.insert(0, form990_tool_path)

# Import directly
from bmf_filter import BMFFilterTool
from generated import BMFFilterIntent, BMFFilterCriteria
from form990_analyzer import Form990AnalysisTool, Form990AnalysisCriteria

async def test_workflow():
    """Test the complete two-tool workflow"""

    print("🔄 Two-Tool Workflow Integration Test")
    print("=" * 50)

    # Initialize both tools
    print("🔧 Initializing tools...")
    bmf_tool = BMFFilterTool()
    form990_tool = Form990AnalysisTool()
    print("✅ Both tools initialized successfully")

    # Step 1: BMF Filter - Find organizations
    print("\n📊 STEP 1: BMF Organization Discovery")
    print("-" * 40)

    bmf_start = time.time()

    # Create BMF search criteria
    bmf_criteria = BMFFilterCriteria(
        states=['VA', 'MD'],
        ntee_codes=['P20', 'B25'],  # Education and Health
        revenue_min=500000,
        limit=5,  # Small number for testing
        sort_by='revenue_desc'
    )

    bmf_intent = BMFFilterIntent(
        what_youre_looking_for="Large education and health organizations in VA/MD",
        criteria=bmf_criteria
    )

    # Execute BMF search
    bmf_result = await bmf_tool.execute(bmf_intent)
    bmf_time = time.time() - bmf_start

    print(f"✅ BMF Discovery Results:")
    print(f"   Organizations found: {len(bmf_result.organizations)}")
    print(f"   Search time: {bmf_time * 1000:.1f}ms")
    print(f"   Database records: {bmf_result.summary.total_in_database:,}")

    if bmf_result.organizations:
        print(f"\n📋 Organizations Found:")
        for i, org in enumerate(bmf_result.organizations, 1):
            revenue = org.revenue or 0
            print(f"   {i}. {org.name} (EIN: {org.ein})")
            print(f"      Revenue: ${revenue:,}, State: {org.state}, NTEE: {org.ntee_code}")

    # Step 2: Form 990 Analysis - Deep financial analysis
    print(f"\n💰 STEP 2: Form 990 Deep Financial Analysis")
    print("-" * 40)

    form990_start = time.time()

    # Extract EINs for analysis
    target_eins = [org.ein for org in bmf_result.organizations]

    if target_eins:
        form990_criteria = Form990AnalysisCriteria(
            target_eins=target_eins,
            years_to_analyze=3,
            financial_health_analysis=True
        )

        form990_result = await form990_tool.execute(form990_criteria)
        form990_time = time.time() - form990_start

        print(f"✅ Form 990 Analysis Results:")
        print(f"   Organizations analyzed: {form990_result.total_organizations_analyzed}")
        print(f"   Analysis time: {form990_time * 1000:.1f}ms")
        print(f"   Analysis period: {form990_result.analysis_period}")

        if form990_result.organizations:
            print(f"\n📈 Financial Analysis Summary:")
            for i, org in enumerate(form990_result.organizations, 1):
                health = org.financial_health
                print(f"   {i}. {org.name}")
                print(f"      Financial Health: {health.health_category.upper()} (Score: {health.overall_score:.1f})")
                print(f"      Latest Year: {org.latest_year}, Data Quality: {org.data_quality_score:.2f}")
                if org.key_insights:
                    print(f"      Key Insight: {org.key_insights[0]}")

    # Summary
    total_time = bmf_time + form990_time
    print(f"\n🎯 WORKFLOW SUMMARY")
    print("-" * 40)
    print(f"Total execution time: {total_time * 1000:.1f}ms")
    print(f"BMF stage: {bmf_time * 1000:.1f}ms ({bmf_time/total_time*100:.1f}%)")
    print(f"990 stage: {form990_time * 1000:.1f}ms ({form990_time/total_time*100:.1f}%)")
    print(f"Organizations: {bmf_result.summary.total_in_database:,} → {len(bmf_result.organizations)} → {form990_result.total_organizations_analyzed}")

    if bmf_result.organizations:
        reduction_ratio = bmf_result.summary.total_in_database / len(bmf_result.organizations)
        print(f"Filter efficiency: {reduction_ratio:,.0f}:1 reduction")

    print(f"\n🎉 Two-tool workflow test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_workflow())