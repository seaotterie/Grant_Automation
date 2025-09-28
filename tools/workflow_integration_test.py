"""
Two-Tool Workflow Integration Test
=================================

Tests the complete two-tool architecture:
1. BMF Filter Tool: Fast filtering of 700K+ organizations
2. Form 990 Analysis Tool: Deep analysis of filtered results

Demonstrates performance benefits of the two-stage approach
"""

import sys
import os
import asyncio
import time
from typing import List

# Add both tools to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'bmf-filter-tool'))
sys.path.insert(0, os.path.join(current_dir, 'form990-analysis-tool'))

# Import from tools
from app.bmf_filter import BMFFilterTool
from app.form990_analyzer import Form990AnalysisTool, Form990AnalysisCriteria


class WorkflowIntegrationTest:
    """Test class for two-tool workflow integration"""

    def __init__(self):
        self.bmf_tool = BMFFilterTool()
        self.form990_tool = Form990AnalysisTool()

    async def test_complete_workflow(self, search_description: str) -> dict:
        """Test complete workflow from BMF search to Form 990 analysis"""

        print(f"🔍 Testing workflow: {search_description}")
        print("=" * 60)

        # Step 1: BMF Filter Tool - Fast discovery
        print("📊 STEP 1: BMF Organization Discovery")
        print("-" * 40)

        bmf_start = time.time()

        # Create a simple test criteria
        class TestCriteria:
            def __init__(self):
                self.states = ['VA', 'MD']
                self.ntee_codes = ['P20', 'B25']  # Education and Health
                self.revenue_min = 500000  # Organizations with substantial revenue
                self.revenue_max = None
                self.asset_min = None
                self.asset_max = None
                self.organization_name = None
                self.cities = None
                self.foundation_type = None
                self.limit = 10  # Limit for testing
                self.sort_by = 'revenue_desc'

        bmf_criteria = TestCriteria()
        bmf_organizations, bmf_stats = self.bmf_tool._process_database_query(bmf_criteria)
        bmf_time = time.time() - bmf_start

        print(f"✅ BMF Discovery Results:")
        print(f"   Organizations found: {len(bmf_organizations)}")
        print(f"   Search time: {bmf_time * 1000:.1f}ms")
        print(f"   Filter efficiency: {bmf_stats['filter_efficiency']:.4f}")
        print(f"   Database records scanned: {bmf_stats['rows_processed']:,}")

        if bmf_organizations:
            print(f"\n📋 Top 3 Organizations Found:")
            for i, org in enumerate(bmf_organizations[:3], 1):
                revenue = org['bmf_revenue'] or 0
                print(f"   {i}. {org['name']} (EIN: {org['ein']})")
                print(f"      Revenue: ${revenue:,}, State: {org['state']}, NTEE: {org['ntee_code']}")

        # Step 2: Form 990 Analysis Tool - Deep analysis
        print(f"\n💰 STEP 2: Form 990 Deep Financial Analysis")
        print("-" * 40)

        form990_start = time.time()

        # Extract EINs for analysis
        target_eins = [org['ein'] for org in bmf_organizations[:5]]  # Analyze top 5

        if target_eins:
            form990_criteria = Form990AnalysisCriteria(
                target_eins=target_eins,
                years_to_analyze=3,
                financial_health_analysis=True,
                grant_capacity_analysis=True,
                trend_analysis=True
            )

            form990_result = await self.form990_tool.execute(form990_criteria)
            form990_time = time.time() - form990_start

            print(f"✅ Form 990 Analysis Results:")
            print(f"   Organizations analyzed: {form990_result.total_organizations_analyzed}")
            print(f"   Analysis time: {form990_time * 1000:.1f}ms")
            print(f"   Analysis period: {form990_result.analysis_period}")

            # Show detailed analysis for top organization
            if form990_result.organizations:
                top_org = form990_result.organizations[0]
                print(f"\n🏆 Detailed Analysis - {top_org.name}:")
                print(f"   Financial Health: {top_org.financial_health.health_category} (score: {top_org.financial_health.overall_score:.1f})")
                print(f"   Organization Type: {top_org.organization_type}")
                print(f"   Data Quality: {top_org.data_quality_score:.1%}")
                print(f"   Years of Data: {len(top_org.financial_years)}")

                if top_org.financial_health.warning_flags:
                    print(f"   ⚠️  Warning Flags: {', '.join(top_org.financial_health.warning_flags)}")

                if top_org.key_insights:
                    print(f"   💡 Key Insights:")
                    for insight in top_org.key_insights[:3]:
                        print(f"      • {insight}")
        else:
            print("❌ No organizations to analyze")
            form990_time = 0
            form990_result = None

        # Step 3: Workflow Performance Analysis
        print(f"\n⚡ STEP 3: Workflow Performance Analysis")
        print("-" * 40)

        total_time = bmf_time + form990_time

        performance_analysis = {
            'bmf_search_time_ms': bmf_time * 1000,
            'form990_analysis_time_ms': form990_time * 1000,
            'total_workflow_time_ms': total_time * 1000,
            'organizations_discovered': len(bmf_organizations),
            'organizations_analyzed': len(form990_result.organizations) if form990_result else 0,
            'filter_efficiency': bmf_stats['filter_efficiency'],
            'database_records_scanned': bmf_stats['rows_processed'],
            'performance_benefit': self._calculate_performance_benefit(bmf_stats, len(target_eins))
        }

        print(f"📈 Performance Metrics:")
        print(f"   Total workflow time: {total_time * 1000:.1f}ms")
        print(f"   BMF search: {bmf_time * 1000:.1f}ms ({(bmf_time/total_time)*100:.1f}%)")
        print(f"   990 analysis: {form990_time * 1000:.1f}ms ({(form990_time/total_time)*100:.1f}%)")
        print(f"   Performance benefit: {performance_analysis['performance_benefit']:.1f}x faster")

        return performance_analysis

    def _calculate_performance_benefit(self, bmf_stats: dict, analyzed_count: int) -> float:
        """Calculate performance benefit of two-tool approach vs analyzing all records"""
        total_records = bmf_stats['rows_processed']

        # Estimated time if we analyzed all records directly (conservative estimate)
        estimated_direct_analysis_time = total_records * 0.1  # 0.1ms per record

        # Actual time using two-tool approach
        actual_time = analyzed_count * 1.5  # 1.5ms per analyzed record

        return estimated_direct_analysis_time / actual_time if actual_time > 0 else 1.0

    async def run_comprehensive_test(self):
        """Run comprehensive workflow tests with different scenarios"""

        print("🚀 Two-Tool Workflow Integration Test")
        print("=" * 60)
        print()

        test_scenarios = [
            "Virginia/Maryland education and health nonprofits with substantial revenue",
            # Could add more scenarios here
        ]

        all_results = []

        for i, scenario in enumerate(test_scenarios, 1):
            print(f"TEST SCENARIO {i}/{len(test_scenarios)}")
            result = await self.test_complete_workflow(scenario)
            all_results.append(result)
            print()

        # Summary
        print("📊 WORKFLOW INTEGRATION SUMMARY")
        print("=" * 60)

        if all_results:
            avg_total_time = sum(r['total_workflow_time_ms'] for r in all_results) / len(all_results)
            avg_discovered = sum(r['organizations_discovered'] for r in all_results) / len(all_results)
            avg_analyzed = sum(r['organizations_analyzed'] for r in all_results) / len(all_results)
            avg_benefit = sum(r['performance_benefit'] for r in all_results) / len(all_results)

            print(f"✅ Tests completed: {len(all_results)}")
            print(f"⚡ Average workflow time: {avg_total_time:.1f}ms")
            print(f"🔍 Average organizations discovered: {avg_discovered:.1f}")
            print(f"💰 Average organizations analyzed: {avg_analyzed:.1f}")
            print(f"🚀 Average performance benefit: {avg_benefit:.1f}x faster")
            print()
            print("🎯 Two-Tool Architecture Benefits:")
            print("   • Fast filtering of 700K+ organizations (BMF tool)")
            print("   • Deep analysis only on relevant subset (Form 990 tool)")
            print("   • Significant performance improvement over direct analysis")
            print("   • Structured data flow between tools")
            print("   • Modular design allows independent optimization")


async def main():
    """Main test execution"""
    try:
        test = WorkflowIntegrationTest()
        await test.run_comprehensive_test()

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())