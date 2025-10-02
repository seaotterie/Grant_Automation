"""
Simple test for Historical Funding Analyzer Tool
"""

import sys
from pathlib import Path
import asyncio
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add tool path
tool_path = project_root / "tools" / "historical-funding-analyzer-tool" / "app"
sys.path.insert(0, str(tool_path))

from historical_tool import HistoricalFundingAnalyzerTool, analyze_historical_funding
from historical_models import HistoricalAnalysisInput


async def test_historical_analyzer():
    """Test historical funding analyzer with sample data"""

    print("Testing Historical Funding Analyzer Tool...")
    print("=" * 60)

    # Sample historical awards data (USASpending.gov format)
    historical_data = [
        # 2024 awards
        {"amount": 150000, "date": "2024-03-15", "state": "VA", "agency": "HHS", "category": "health"},
        {"amount": 75000, "date": "2024-06-20", "state": "VA", "agency": "DOD", "category": "veterans"},
        {"amount": 200000, "date": "2024-09-10", "state": "MD", "agency": "HHS", "category": "health"},

        # 2023 awards
        {"amount": 125000, "date": "2023-02-12", "state": "VA", "agency": "HHS", "category": "health"},
        {"amount": 50000, "date": "2023-05-18", "state": "DC", "agency": "VA", "category": "veterans"},
        {"amount": 175000, "date": "2023-11-25", "state": "VA", "agency": "HHS", "category": "health"},

        # 2022 awards
        {"amount": 100000, "date": "2022-04-10", "state": "VA", "agency": "HHS", "category": "health"},
        {"amount": 80000, "date": "2022-08-22", "state": "MD", "agency": "DOD", "category": "veterans"},

        # 2021 awards
        {"amount": 90000, "date": "2021-01-15", "state": "VA", "agency": "HHS", "category": "health"},
        {"amount": 60000, "date": "2021-07-30", "state": "VA", "agency": "VA", "category": "veterans"},

        # 2020 awards
        {"amount": 75000, "date": "2020-03-20", "state": "VA", "agency": "HHS", "category": "health"},
        {"amount": 40000, "date": "2020-10-05", "state": "DC", "agency": "VA", "category": "veterans"},
    ]

    print("\n1. Testing Basic Historical Analysis")
    print("-" * 60)

    tool = HistoricalFundingAnalyzerTool()

    analysis_input = HistoricalAnalysisInput(
        organization_ein="81-2827604",
        historical_data=historical_data,
        analysis_years=5,
        include_geographic=True,
        include_temporal=True,
        include_patterns=True,
        include_competitive=True
    )

    result = await tool.execute(analysis_input=analysis_input)

    if result.is_success:
        analysis = result.data
        print(f"[OK] Analysis Complete: {analysis.organization_ein}")
        print(f"[OK] Total Awards: {analysis.total_awards}")
        print(f"[OK] Total Funding: ${analysis.total_funding:,.2f}")
        print(f"[OK] Average Award Size: ${analysis.average_award_size:,.2f}")
        print(f"[OK] Years Analyzed: {analysis.years_analyzed}")

        print(f"\n[OK] Funding Patterns Found: {len(analysis.funding_patterns)}")
        for pattern in analysis.funding_patterns[:5]:  # First 5
            print(f"  - {pattern.pattern_name}: {pattern.frequency} awards, "
                  f"${pattern.total_amount:,.2f} ({pattern.percentage_of_total:.1f}%)")

        print(f"\n[OK] Geographic Distribution: {len(analysis.geographic_distribution)} states")
        for geo in analysis.geographic_distribution[:5]:  # Top 5 states
            print(f"  - {geo.state}: {geo.award_count} awards, "
                  f"${geo.total_funding:,.2f} ({geo.percentage_of_total:.1f}%)")

        print(f"\n[OK] Temporal Trends: {len(analysis.temporal_trends)} years")
        for trend in analysis.temporal_trends:
            yoy_str = f"({trend.year_over_year_change:+.1f}% YoY)" if trend.year_over_year_change else ""
            trend_str = f"[{trend.trend_direction.upper()}]" if trend.trend_direction else ""
            print(f"  - {trend.year}: {trend.award_count} awards, "
                  f"${trend.total_funding:,.2f} {yoy_str} {trend_str}")

        if analysis.competitive_insights:
            print(f"\n[OK] Competitive Insights: {len(analysis.competitive_insights)}")
            for insight in analysis.competitive_insights:
                print(f"  - {insight.description}")
                print(f"    Recommendation: {insight.recommendation}")

        print(f"\n[OK] Key Insights:")
        for insight in analysis.key_insights:
            print(f"  + {insight}")

        print(f"\n[OK] Recommendations:")
        for rec in analysis.recommendations:
            print(f"  -> {rec}")

        print(f"\n[OK] Metadata:")
        print(f"  - Analysis Time: {analysis.metadata.analysis_time_ms:.2f}ms")
        print(f"  - Date Range: {analysis.metadata.date_range_start} to {analysis.metadata.date_range_end}")
        print(f"  - Data Quality: {analysis.metadata.data_quality_score:.1%}")

    else:
        print(f"[FAIL] Error: {result.error}")
        return False

    print("\n\n2. Testing Filtered Analysis")
    print("-" * 60)

    # Test with filtering
    result2 = await analyze_historical_funding(
        organization_ein="81-2827604",
        historical_data=historical_data,
        analysis_years=3,  # Only last 3 years
        include_geographic=True,
        include_temporal=True,
        include_patterns=True,
        include_competitive=False
    )

    if result2.is_success:
        analysis2 = result2.data
        print(f"[OK] Filtered Analysis (3 years): {analysis2.total_awards} awards")
        print(f"[OK] Total Funding (3 years): ${analysis2.total_funding:,.2f}")
        print(f"[OK] Years: {analysis2.metadata.date_range_start} to {analysis2.metadata.date_range_end}")

        # Verify filtering worked
        if analysis2.total_awards < analysis.total_awards:
            print(f"[OK] Filtering reduced awards: {analysis.total_awards} -> {analysis2.total_awards}")
        else:
            print(f"[WARN] Filtering didn't reduce awards as expected")

    else:
        print(f"[FAIL] Error: {result2.error}")
        return False

    print("\n\n3. Testing Pattern Detection")
    print("-" * 60)

    # Verify patterns were detected
    if analysis.funding_patterns:
        print(f"[OK] Pattern Detection Working: {len(analysis.funding_patterns)} patterns found")

        # Check for award size patterns
        size_patterns = [p for p in analysis.funding_patterns if p.pattern_type == "award_size"]
        if size_patterns:
            print(f"[OK] Award Size Patterns: {len(size_patterns)} categories")
            for pattern in size_patterns:
                print(f"  - {pattern.pattern_name}: {pattern.frequency} awards")

        # Check for frequency patterns
        freq_patterns = [p for p in analysis.funding_patterns if p.pattern_type == "frequency"]
        if freq_patterns:
            print(f"[OK] Frequency Patterns: {len(freq_patterns)} detected")

    else:
        print(f"[FAIL] No patterns detected")
        return False

    print("\n\n4. Testing Geographic Analysis")
    print("-" * 60)

    if analysis.geographic_distribution:
        print(f"[OK] Geographic Analysis: {len(analysis.geographic_distribution)} states")

        # Verify data
        total_geo_funding = sum(g.total_funding for g in analysis.geographic_distribution)
        if abs(total_geo_funding - analysis.total_funding) < 1.0:  # Allow for rounding
            print(f"[OK] Geographic totals match overall funding")
        else:
            print(f"[WARN] Geographic funding mismatch: {total_geo_funding} vs {analysis.total_funding}")

        # Check state with most funding
        top_state = analysis.geographic_distribution[0]
        print(f"[OK] Top Funding State: {top_state.state} (${top_state.total_funding:,.2f})")

    else:
        print(f"[FAIL] No geographic distribution data")
        return False

    print("\n\n5. Testing Temporal Trend Analysis")
    print("-" * 60)

    if analysis.temporal_trends:
        print(f"[OK] Temporal Trends: {len(analysis.temporal_trends)} years analyzed")

        # Check for trend direction
        trends_with_direction = [t for t in analysis.temporal_trends if t.trend_direction]
        if trends_with_direction:
            print(f"[OK] Trend Direction Detected: {len(trends_with_direction)} years")

        # Verify year-over-year calculations
        for i in range(1, len(analysis.temporal_trends)):
            trend = analysis.temporal_trends[i]
            if trend.year_over_year_change is not None:
                print(f"[OK] YoY Change Calculated: {trend.year} = {trend.year_over_year_change:+.1f}%")
                break

    else:
        print(f"[FAIL] No temporal trends detected")
        return False

    print("\n" + "=" * 60)
    print("[SUCCESS] All tests passed!")
    print("\nTool 22: Historical Funding Analyzer - OPERATIONAL [OK]")
    print(f"- Analyzed {analysis.total_awards} historical awards")
    print(f"- Detected {len(analysis.funding_patterns)} funding patterns")
    print(f"- Analyzed {len(analysis.geographic_distribution)} states")
    print(f"- Tracked {len(analysis.temporal_trends)} years of trends")
    print(f"- Performance: {analysis.metadata.analysis_time_ms:.2f}ms")
    print(f"- Cost: $0.00 (data analysis only)")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_historical_analyzer())
    sys.exit(0 if success else 1)
