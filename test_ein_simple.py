"""
Simple Test EIN 81-2827604 with 12-Factor Agent Tools
"""

import sys
import os
import asyncio
import time
import json

# Add tool paths
current_dir = os.path.dirname(os.path.abspath(__file__))
form990_tool_path = os.path.join(current_dir, 'tools', 'form990-analysis-tool', 'app')
propublica_tool_path = os.path.join(current_dir, 'tools', 'form990-propublica-tool', 'app')

sys.path.insert(0, form990_tool_path)
sys.path.insert(0, propublica_tool_path)

async def test_simple():
    print("TESTING EIN 81-2827604: HEROS BRIDGE")
    print("=" * 60)

    test_ein = "812827604"

    # Test Form 990 Tool
    print("\nSTAGE 1: Form 990 Analysis Tool")
    print("-" * 40)

    try:
        from form990_analyzer import Form990AnalysisTool, Form990AnalysisCriteria

        tool = Form990AnalysisTool()
        criteria = Form990AnalysisCriteria(
            target_eins=[test_ein],
            years_to_analyze=3,
            financial_health_analysis=True
        )

        result = await tool.execute(criteria)

        print(f"Organizations analyzed: {result.total_organizations_analyzed}")
        print(f"Execution time: {result.execution_time_ms:.1f}ms")

        if result.organizations:
            org = result.organizations[0]
            print(f"Organization: {org.name}")
            print(f"Type: {org.organization_type}")
            print(f"Financial years: {len(org.financial_years)}")
            print(f"Health category: {org.financial_health.health_category}")
            print(f"Overall score: {org.financial_health.overall_score:.1f}")

            # Show detailed financial data
            if org.financial_years:
                latest = org.financial_years[0]
                print(f"Latest year ({latest.year}):")
                print(f"  Revenue: ${latest.total_revenue:,}" if latest.total_revenue else "  Revenue: N/A")
                print(f"  Expenses: ${latest.total_expenses:,}" if latest.total_expenses else "  Expenses: N/A")
                print(f"  Assets: ${latest.total_assets:,}" if latest.total_assets else "  Assets: N/A")
        else:
            print("No Form 990 data found")

    except Exception as e:
        print(f"Form 990 Analysis failed: {e}")

    # Test ProPublica Tool
    print("\nSTAGE 2: ProPublica Enrichment Tool")
    print("-" * 40)

    try:
        from propublica_enricher import ProPublicaEnrichmentTool, ProPublicaEnrichmentCriteria

        tool = ProPublicaEnrichmentTool()
        criteria = ProPublicaEnrichmentCriteria(
            target_eins=[test_ein],
            enrichment_depth="standard"
        )

        result = await tool.execute(criteria)

        print(f"Organizations processed: {result.organizations_processed}")
        print(f"API calls made: {result.api_calls_made}")
        print(f"Execution time: {result.execution_time_ms:.1f}ms")
        print(f"Success rate: {result.enrichment_success_rate:.1%}")

        if result.enriched_organizations:
            org = result.enriched_organizations[0]
            print(f"Organization: {org.name}")
            print(f"Type: {org.organization_type}")
            print(f"Filing records: {len(org.filing_records)}")
            print(f"Leadership members: {len(org.leadership_members)}")
            print(f"Peer organizations: {len(org.peer_organizations)}")
            print(f"Data completeness: {org.data_completeness_score:.2f}")
        else:
            print("No ProPublica enrichment data found")

    except Exception as e:
        print(f"ProPublica Enrichment failed: {e}")

    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_simple())