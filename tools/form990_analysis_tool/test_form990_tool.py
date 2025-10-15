"""
Test Form 990 Analysis Tool
"""

import sys
import os
import asyncio

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.form990_analyzer import Form990AnalysisTool, Form990AnalysisCriteria

async def test_form990_tool():
    print("Testing Form 990 Analysis Tool...")

    # Initialize tool
    tool = Form990AnalysisTool()
    print("Tool initialized successfully")

    # Test with known EIN
    test_ein = "300219424"  # United Way of the National Capital Area
    criteria = Form990AnalysisCriteria(
        target_eins=[test_ein],
        years_to_analyze=3,
        financial_health_analysis=True
    )

    print(f"Analyzing organization: {test_ein}")
    result = await tool.execute(criteria)

    print(f"Analysis completed:")
    print(f"  Organizations analyzed: {result.total_organizations_analyzed}")
    print(f"  Execution time: {result.execution_time_ms:.1f}ms")
    print(f"  Analysis period: {result.analysis_period}")

    if result.organizations:
        org = result.organizations[0]
        print(f"\nOrganization Details:")
        print(f"  Name: {org.name}")
        print(f"  Type: {org.organization_type}")
        print(f"  Latest Year: {org.latest_year}")
        print(f"  Financial Years: {len(org.financial_years)}")
        print(f"  Health Category: {org.financial_health.health_category}")
        print(f"  Overall Score: {org.financial_health.overall_score:.1f}")
        print(f"  Data Quality: {org.data_quality_score:.2f}")

        if org.key_insights:
            print(f"  Key Insights:")
            for insight in org.key_insights:
                print(f"    - {insight}")

    print("\nForm 990 Analysis Tool test completed successfully!")
    return result

if __name__ == "__main__":
    asyncio.run(test_form990_tool())