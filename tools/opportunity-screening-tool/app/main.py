"""
Opportunity Screening Tool - Main Entry Point
============================================

12-Factor compliant tool for mass screening of grant opportunities.

Purpose: Screen 100s of opportunities → shortlist of ~10 for deep analysis
Cost: Fast mode $0.0004/opp, Thorough mode $0.02/opp
Replaces: ai_lite_unified, ai_heavy_light processors

12-Factor Principles:
- Factor 4: Structured input/output (ScreeningInput → ScreeningOutput)
- Factor 6: Stateless execution (no persistence between runs)
- Factor 10: Single responsibility (opportunity screening only)
"""

import asyncio
import sys
from pathlib import Path
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.screening_tool import OpportunityScreeningTool, screen_opportunities
from app.screening_models import (
    ScreeningInput,
    ScreeningMode,
    Opportunity,
    OrganizationProfile
)


async def demo_fast_screening():
    """
    Demo 1: Fast screening mode

    Use Case: Quickly filter 200 opportunities down to 50 candidates
    Cost: ~$0.08 for 200 opportunities
    Time: ~6-7 minutes (2s per opportunity, batched)
    """
    print("\n" + "="*60)
    print("🔍 DEMO 1: Fast Screening Mode (PLAN Tab Equivalent)")
    print("="*60)

    # Create sample organization profile
    organization = OrganizationProfile(
        ein="541026365",
        name="Sample Youth Development Organization",
        mission="Empowering youth through education and mentorship programs",
        ntee_codes=["O50", "P20"],
        geographic_focus=["VA", "MD", "DC"],
        program_areas=["Youth Development", "Education", "Mentorship"],
        annual_revenue=2500000.0,
        staff_count=25,
        years_established=15
    )

    # Create sample opportunities
    opportunities = [
        Opportunity(
            opportunity_id="OPP-001",
            title="Youth Education Grant Program",
            funder="Example Foundation",
            funder_type="foundation",
            description="Supporting educational programs for underserved youth",
            amount_min=50000,
            amount_max=150000,
            typical_award_size=100000,
            deadline="2025-12-31",
            focus_areas=["Education", "Youth Development"],
            geographic_restrictions=["VA", "MD"]
        ),
        Opportunity(
            opportunity_id="OPP-002",
            title="Healthcare Innovation Grant",
            funder="Health Foundation",
            funder_type="foundation",
            description="Innovative healthcare delivery for rural communities",
            amount_min=100000,
            amount_max=500000,
            typical_award_size=250000,
            deadline="2025-11-15",
            focus_areas=["Healthcare", "Rural Development"],
            geographic_restrictions=["VA"]
        ),
        Opportunity(
            opportunity_id="OPP-003",
            title="Community Mentorship Initiative",
            funder="Corporate Foundation",
            funder_type="corporate",
            description="Mentorship programs connecting youth with professionals",
            amount_min=25000,
            amount_max=75000,
            typical_award_size=50000,
            deadline="2026-01-31",
            focus_areas=["Mentorship", "Youth Development", "Career Development"],
            geographic_restrictions=["DC", "MD", "VA"]
        )
    ]

    print(f"📊 Organization: {organization.name}")
    print(f"📋 Opportunities to screen: {len(opportunities)}")
    print(f"🎯 Mode: Fast (PLAN tab)")
    print(f"💰 Estimated cost: ${len(opportunities) * 0.0004:.4f}")

    # Execute fast screening
    result = await screen_opportunities(
        opportunities=opportunities,
        organization=organization,
        mode="fast",
        threshold=0.55,
        max_recommendations=10
    )

    if result.is_success():
        output = result.data
        print(f"\n✅ Screening Complete!")
        print(f"   Total Screened: {output.total_screened}")
        print(f"   Passed Threshold: {output.passed_threshold}")
        print(f"   Recommended: {len(output.recommended_for_deep_analysis)}")
        print(f"   Processing Time: {output.processing_time_seconds:.2f}s")
        print(f"   Total Cost: ${output.total_cost_usd:.4f}")

        print(f"\n📈 Top Scoring Opportunities:")
        for score in sorted(output.opportunity_scores, key=lambda s: s.overall_score, reverse=True)[:3]:
            print(f"\n   {score.opportunity_title}")
            print(f"   Overall Score: {score.overall_score:.2f}")
            print(f"   Strategic Fit: {score.strategic_fit_score:.2f}")
            print(f"   Eligibility: {score.eligibility_score:.2f}")
            print(f"   Proceed to Deep Analysis: {'✅ Yes' if score.proceed_to_deep_analysis else '❌ No'}")
            print(f"   Summary: {score.one_sentence_summary}")
    else:
        print(f"❌ Screening failed: {result.error}")


async def demo_thorough_screening():
    """
    Demo 2: Thorough screening mode

    Use Case: Comprehensive analysis of 50 pre-filtered opportunities
    Cost: ~$1.00-$2.00 for 50 opportunities
    Time: ~4-5 minutes (5s per opportunity, batched)
    """
    print("\n" + "="*60)
    print("🔬 DEMO 2: Thorough Screening Mode (ANALYZE Tab Equivalent)")
    print("="*60)

    organization = OrganizationProfile(
        ein="541026365",
        name="Sample Youth Development Organization",
        mission="Empowering youth through education and mentorship programs",
        ntee_codes=["O50", "P20"],
        geographic_focus=["VA", "MD", "DC"],
        program_areas=["Youth Development", "Education", "Mentorship"],
        annual_revenue=2500000.0,
        staff_count=25,
        years_established=15
    )

    # Fewer opportunities for thorough analysis
    opportunities = [
        Opportunity(
            opportunity_id="OPP-001",
            title="Youth Education Grant Program",
            funder="Example Foundation",
            funder_type="foundation",
            description="Supporting educational programs for underserved youth with focus on college readiness",
            amount_min=50000,
            amount_max=150000,
            typical_award_size=100000,
            deadline="2025-12-31",
            focus_areas=["Education", "Youth Development", "College Access"],
            geographic_restrictions=["VA", "MD"],
            past_recipients=["Youth Org A", "Education Nonprofit B"]
        )
    ]

    print(f"📊 Organization: {organization.name}")
    print(f"📋 Opportunities to screen: {len(opportunities)}")
    print(f"🎯 Mode: Thorough (ANALYZE tab)")
    print(f"💰 Estimated cost: ${len(opportunities) * 0.02:.2f}")

    # Execute thorough screening
    result = await screen_opportunities(
        opportunities=opportunities,
        organization=organization,
        mode="thorough",
        threshold=0.60,
        max_recommendations=10
    )

    if result.is_success():
        output = result.data
        print(f"\n✅ Screening Complete!")
        print(f"   Total Screened: {output.total_screened}")
        print(f"   Passed Threshold: {output.passed_threshold}")
        print(f"   High Confidence: {output.high_confidence_count}")
        print(f"   Processing Time: {output.processing_time_seconds:.2f}s")
        print(f"   Total Cost: ${output.total_cost_usd:.2f}")

        print(f"\n📊 Detailed Analysis:")
        for score in output.opportunity_scores:
            print(f"\n   {score.opportunity_title}")
            print(f"   Overall Score: {score.overall_score:.2f} ({score.confidence_level} confidence)")
            print(f"   Dimensional Scores:")
            print(f"     • Strategic Fit: {score.strategic_fit_score:.2f}")
            print(f"     • Eligibility: {score.eligibility_score:.2f}")
            print(f"     • Timing: {score.timing_score:.2f}")
            print(f"     • Financial: {score.financial_score:.2f}")
            print(f"     • Competition: {score.competition_score:.2f}")
            print(f"   Proceed: {'✅ Yes' if score.proceed_to_deep_analysis else '❌ No'}")
            print(f"   Estimated Effort: {score.estimated_effort_hours} hours")
            if score.recommended_actions:
                print(f"   Recommended Actions:")
                for action in score.recommended_actions:
                    print(f"     • {action}")
    else:
        print(f"❌ Screening failed: {result.error}")


async def demo_two_stage_pipeline():
    """
    Demo 3: Complete two-stage screening pipeline

    Stage 1: Fast screening (200 opps → 50 candidates)
    Stage 2: Thorough screening (50 candidates → 10 recommendations)

    Total Cost: ~$0.08 + ~$1.00 = ~$1.08
    Total Time: ~8-10 minutes
    """
    print("\n" + "="*60)
    print("🔗 DEMO 3: Two-Stage Screening Pipeline")
    print("="*60)

    organization = OrganizationProfile(
        ein="541026365",
        name="Sample Youth Development Organization",
        mission="Empowering youth through education and mentorship programs",
        ntee_codes=["O50", "P20"],
        geographic_focus=["VA", "MD", "DC"],
        program_areas=["Youth Development", "Education", "Mentorship"],
        annual_revenue=2500000.0
    )

    # Simulate 10 opportunities (in reality, would be 200+)
    opportunities = [
        Opportunity(
            opportunity_id=f"OPP-{i:03d}",
            title=f"Opportunity {i}",
            funder="Various Funders",
            funder_type="foundation",
            description="Sample opportunity description",
            amount_min=25000,
            amount_max=150000,
            focus_areas=["Education"] if i % 2 == 0 else ["Healthcare"],
            geographic_restrictions=["VA", "MD"]
        )
        for i in range(1, 11)
    ]

    print(f"📊 Organization: {organization.name}")
    print(f"📋 Initial opportunities: {len(opportunities)}")

    # Stage 1: Fast screening
    print(f"\n🔍 Stage 1: Fast Screening")
    print(f"   Goal: Filter {len(opportunities)} → top candidates")

    stage1_result = await screen_opportunities(
        opportunities=opportunities,
        organization=organization,
        mode="fast",
        threshold=0.55,
        max_recommendations=5  # Top 5 for thorough analysis
    )

    if stage1_result.is_success():
        stage1_output = stage1_result.data
        print(f"   ✅ Passed threshold: {stage1_output.passed_threshold}")
        print(f"   ✅ Selected for Stage 2: {len(stage1_output.recommended_for_deep_analysis)}")
        print(f"   💰 Cost: ${stage1_output.total_cost_usd:.4f}")

        # Stage 2: Thorough screening on top candidates
        print(f"\n🔬 Stage 2: Thorough Screening")
        print(f"   Goal: Deep analysis of {len(stage1_output.recommended_for_deep_analysis)} candidates")

        # Filter opportunities for stage 2
        stage2_opportunities = [
            opp for opp in opportunities
            if opp.opportunity_id in stage1_output.recommended_for_deep_analysis
        ]

        stage2_result = await screen_opportunities(
            opportunities=stage2_opportunities,
            organization=organization,
            mode="thorough",
            threshold=0.60,
            max_recommendations=10
        )

        if stage2_result.is_success():
            stage2_output = stage2_result.data
            print(f"   ✅ Final recommendations: {len(stage2_output.recommended_for_deep_analysis)}")
            print(f"   💰 Cost: ${stage2_output.total_cost_usd:.2f}")

            # Pipeline summary
            print(f"\n📈 Pipeline Summary:")
            print(f"   Stage 1 (Fast): {len(opportunities)} → {stage1_output.passed_threshold} candidates")
            print(f"   Stage 2 (Thorough): {len(stage2_opportunities)} → {len(stage2_output.recommended_for_deep_analysis)} recommendations")
            print(f"   Total Cost: ${stage1_output.total_cost_usd + stage2_output.total_cost_usd:.2f}")
            print(f"   Total Time: {stage1_output.processing_time_seconds + stage2_output.processing_time_seconds:.2f}s")
            print(f"\n   🎯 Ready for Deep Intelligence Tool (Tool 2)")
        else:
            print(f"   ❌ Stage 2 failed: {stage2_result.error}")
    else:
        print(f"   ❌ Stage 1 failed: {stage1_result.error}")


async def demo_direct_tool_usage():
    """
    Demo 4: Direct tool instantiation and execution

    Shows low-level tool API for custom integrations
    """
    print("\n" + "="*60)
    print("⚙️  DEMO 4: Direct Tool API Usage")
    print("="*60)

    # Create tool instance with configuration
    config = {
        "openai_api_key": "sk-...",  # Would come from environment
        "default_mode": "fast",
        "default_threshold": 0.55
    }

    tool = OpportunityScreeningTool(config)

    print(f"🔧 Tool: {tool.get_tool_name()}")
    print(f"📦 Version: {tool.get_tool_version()}")
    print(f"🎯 Responsibility: {tool.get_single_responsibility()}")

    # Create structured input
    organization = OrganizationProfile(
        ein="541026365",
        name="Sample Organization",
        mission="Sample mission",
        ntee_codes=["O50"],
        geographic_focus=["VA"],
        program_areas=["Youth Development"]
    )

    opportunities = [
        Opportunity(
            opportunity_id="OPP-001",
            title="Sample Opportunity",
            funder="Sample Funder",
            funder_type="foundation",
            description="Sample description",
            focus_areas=["Youth Development"]
        )
    ]

    screening_input = ScreeningInput(
        opportunities=opportunities,
        organization_profile=organization,
        screening_mode=ScreeningMode.FAST,
        minimum_threshold=0.55,
        max_recommendations=10
    )

    print(f"\n📥 Input: ScreeningInput object")
    print(f"   Opportunities: {len(screening_input.opportunities)}")
    print(f"   Mode: {screening_input.screening_mode.value}")
    print(f"   Threshold: {screening_input.minimum_threshold}")

    # Execute with tool API
    result = await tool.execute(screening_input=screening_input)

    print(f"\n📤 Output: ToolResult[ScreeningOutput]")
    print(f"   Status: {result.status.value}")
    print(f"   Execution Time: {result.execution_time_ms:.2f}ms")
    print(f"   Tool: {result.tool_name} v{result.tool_version}")

    if result.is_success():
        print(f"   Data: ScreeningOutput with {result.data.total_screened} opportunities")
        print(f"\n✅ Demonstrates Factor 4: Structured I/O")
        print(f"✅ Demonstrates Factor 6: Stateless execution")
        print(f"✅ Demonstrates Factor 10: Single responsibility")


async def main():
    """Run all demonstrations"""
    print("🚀 Opportunity Screening Tool - 12-Factor Demonstration")
    print("="*60)
    print("\nTool Purpose: Mass screening of grant opportunities")
    print("Pipeline Position: Stage 1 → Human Gateway → Deep Intelligence Tool")
    print("Cost Efficiency: $0.0004-$0.02 per opportunity vs manual review")

    try:
        # Run demonstrations
        await demo_fast_screening()
        await demo_thorough_screening()
        await demo_two_stage_pipeline()
        await demo_direct_tool_usage()

        print("\n" + "="*60)
        print("🎉 All Demonstrations Complete!")
        print("="*60)

        print("\n💡 Key Features Demonstrated:")
        print("  ✅ Factor 4: Structured Input/Output (ScreeningInput → ScreeningOutput)")
        print("  ✅ Factor 6: Stateless Execution (no persistence)")
        print("  ✅ Factor 10: Single Responsibility (screening only)")
        print("  ✅ Two screening modes (fast $0.0004, thorough $0.02)")
        print("  ✅ Batch processing with parallel execution")
        print("  ✅ Multi-dimensional scoring")
        print("  ✅ Cost and time tracking")

        print("\n🔗 Integration Points:")
        print("  • Input: Opportunity discovery tools (BMF, Grants.gov, etc.)")
        print("  • Output: Human Gateway for manual review")
        print("  • Next Tool: Deep Intelligence Tool (Tool 2)")

        print("\n📊 Typical Workflow:")
        print("  1. Discover 200 opportunities (various tools)")
        print("  2. Fast screen 200 → 50 candidates ($0.08)")
        print("  3. Thorough screen 50 → 10 recommendations ($1.00)")
        print("  4. Human review and selection")
        print("  5. Deep analysis of 10 selected ($20-$80)")
        print("  Total cost: ~$21-81 vs $800-1,600 manual research")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
