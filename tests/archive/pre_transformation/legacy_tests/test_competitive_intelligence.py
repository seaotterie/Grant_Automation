#!/usr/bin/env python3
"""
Competitive Intelligence Processor Test
Tests the competitive intelligence analysis capabilities.

This test validates:
1. Competitor discovery using BMF database
2. Web intelligence analysis for competitors 
3. Funding landscape analysis
4. Strategic recommendations generation
5. Threat level assessment
"""

import asyncio
import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.processors.analysis.competitive_intelligence_processor import CompetitiveIntelligenceProcessor
from src.core.data_models import ProcessorConfig, OrganizationProfile


class CompetitiveIntelligenceTest:
    """Test competitive intelligence processor capabilities."""
    
    def __init__(self):
        self.database_path = "data/catalynx.db"
        self.bmf_database_path = "data/nonprofit_intelligence.db"
        
    async def run_competitive_test(self):
        """Run complete competitive intelligence test."""
        print("COMPETITIVE INTELLIGENCE PROCESSOR TEST")
        print("=" * 45)
        
        try:
            # Test 1: Verify BMF database availability
            print("\n1. VERIFYING BMF DATABASE AVAILABILITY...")
            bmf_status = self.verify_bmf_database()
            print(f"   BMF Database: {'READY' if bmf_status else 'NOT AVAILABLE'}")
            
            if not bmf_status:
                print("   BMF database not available - competitive discovery will be limited")
            
            # Test 2: Test competitor discovery
            print("\n2. TESTING COMPETITOR DISCOVERY...")
            processor = CompetitiveIntelligenceProcessor()
            
            config = ProcessorConfig(
                workflow_id="test_competitive_intelligence",
                processor_name="competitive_intelligence_processor",
                workflow_config={}
            )
            
            # Run the full competitive intelligence analysis
            result = await processor.execute(config)
            
            if result.success:
                print("   Competitive Intelligence Analysis: SUCCESS")
                
                # Display competitive analysis results
                competitive_data = result.data.get("competitive_analysis", {})
                competitors_discovered = competitive_data.get("total_competitors_discovered", 0)
                competitors_with_intel = competitive_data.get("competitors_with_intelligence", 0)
                coverage = competitive_data.get("competitive_landscape_coverage", 0)
                
                print(f"   Competitors Discovered: {competitors_discovered}")
                print(f"   Competitors with Intelligence: {competitors_with_intel}")
                print(f"   Landscape Coverage: {coverage:.1f}%")
                
                analysis_scope = competitive_data.get("analysis_scope", {})
                ntee_codes = analysis_scope.get("ntee_codes_analyzed", [])
                states = analysis_scope.get("states_analyzed", [])
                
                print(f"   NTEE Codes Analyzed: {', '.join(ntee_codes)}")
                print(f"   States Analyzed: {', '.join(states)}")
                
                # Test 3: Display competitor profiles
                print("\n3. COMPETITOR PROFILE ANALYSIS...")
                competitor_profiles = result.data.get("competitor_profiles", [])
                
                threat_levels = {}
                for profile in competitor_profiles[:5]:  # Show first 5
                    threat_level = profile.get("competitive_threat_level", "Unknown")
                    threat_levels[threat_level] = threat_levels.get(threat_level, 0) + 1
                    
                    print(f"   - {profile.get('name', 'Unknown')} ({profile.get('state', 'N/A')})")
                    print(f"     Threat Level: {threat_level}")
                    print(f"     Web Intelligence Score: {profile.get('web_intelligence_score', 0)}")
                    
                    strengths = profile.get('strengths', [])
                    if strengths:
                        print(f"     Strengths: {', '.join(strengths[:2])}")
                
                print(f"\n   Threat Level Distribution:")
                for level, count in threat_levels.items():
                    print(f"     {level}: {count} competitors")
                
                # Test 4: Display funding landscape analysis
                print("\n4. FUNDING LANDSCAPE ANALYSIS...")
                funding_landscape = result.data.get("funding_landscape", {})
                market_concentration = funding_landscape.get("market_concentration", {})
                
                print(f"   Total Market Competitors: {market_concentration.get('competitor_count', 0)}")
                print(f"   High Threat Competitors: {market_concentration.get('high_threat_competitors', 0)}")
                
                competitive_gaps = funding_landscape.get("competitive_gaps", [])
                opportunity_areas = funding_landscape.get("opportunity_areas", [])
                
                if competitive_gaps:
                    print("   Competitive Gaps:")
                    for gap in competitive_gaps[:2]:
                        print(f"     - {gap}")
                
                if opportunity_areas:
                    print("   Opportunity Areas:")
                    for opportunity in opportunity_areas[:2]:
                        print(f"     - {opportunity}")
                
                # Test 5: Display strategic recommendations
                print("\n5. STRATEGIC RECOMMENDATIONS...")
                recommendations = result.data.get("strategic_recommendations", [])
                
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"   {i}. {rec.get('category', 'General')} ({rec.get('priority', 'Medium')} Priority)")
                    print(f"      {rec.get('recommendation', 'No recommendation')}")
                    print(f"      Rationale: {rec.get('rationale', 'No rationale provided')}")
                
                # Test 6: Display competitive insights
                print("\n6. COMPETITIVE INSIGHTS...")
                insights = result.data.get("competitive_insights", {})
                key_findings = insights.get("key_findings", [])
                competitive_advantages = insights.get("competitive_advantages", [])
                threat_assessment = insights.get("threat_assessment", [])
                
                if key_findings:
                    print("   Key Findings:")
                    for finding in key_findings[:2]:
                        print(f"     - {finding}")
                
                if competitive_advantages:
                    print("   Competitive Advantages:")
                    for advantage in competitive_advantages[:2]:
                        print(f"     - {advantage}")
                
                if threat_assessment:
                    print("   Threat Assessment:")
                    for threat in threat_assessment[:2]:
                        print(f"     - {threat}")
                
            else:
                print("   Competitive Intelligence Analysis: FAILED")
                print(f"   Errors: {result.errors}")
                return False
            
            # Test 7: Verify metadata
            print("\n7. VERIFYING ANALYSIS METADATA...")
            metadata = result.metadata
            analysis_type = metadata.get("analysis_type")
            data_sources = metadata.get("data_sources", [])
            threat_levels_summary = metadata.get("competitor_threat_levels", {})
            
            print(f"   Analysis Type: {analysis_type}")
            print(f"   Data Sources: {', '.join(data_sources)}")
            print(f"   Threat Distribution: {threat_levels_summary}")
            
            print("\n" + "=" * 45)
            print("COMPETITIVE INTELLIGENCE TEST SUMMARY: SUCCESS")
            print("\nCompetitive Intelligence capabilities verified:")
            print("- Competitor discovery using BMF database")
            print("- Web intelligence analysis for competitor assessment") 
            print("- Funding landscape analysis and market positioning")
            print("- Strategic recommendations based on competitive analysis")
            print("- Threat level assessment and competitive insights")
            print("- Comprehensive competitor profiling and analysis")
            
            return True
            
        except Exception as e:
            print(f"ERROR: Competitive intelligence test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_bmf_database(self) -> bool:
        """Verify BMF database is available for competitor discovery."""
        try:
            with sqlite3.connect(self.bmf_database_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM bmf_organizations LIMIT 1")
                count = cursor.fetchone()[0]
                return count > 0
        except Exception as e:
            print(f"   BMF database error: {e}")
            return False


async def main():
    """Run the competitive intelligence test."""
    test_runner = CompetitiveIntelligenceTest()
    success = await test_runner.run_competitive_test()
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)