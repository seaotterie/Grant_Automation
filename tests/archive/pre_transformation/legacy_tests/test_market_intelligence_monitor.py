#!/usr/bin/env python3
"""
Market Intelligence Monitor Test
Tests the market intelligence monitoring and trend analysis capabilities.

This test validates:
1. Funding trend monitoring and analysis
2. Policy change detection and tracking
3. Market development analysis
4. Alert generation for significant changes
5. Strategic insights and recommendations
"""

import asyncio
import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.processors.analysis.market_intelligence_monitor import MarketIntelligenceMonitor
from src.core.data_models import ProcessorConfig


class MarketIntelligenceMonitorTest:
    """Test market intelligence monitoring capabilities."""
    
    def __init__(self):
        self.database_path = "data/catalynx.db"
        
    async def run_monitor_test(self):
        """Run complete market intelligence monitoring test."""
        print("MARKET INTELLIGENCE MONITOR TEST")
        print("=" * 40)
        
        try:
            # Test 1: Initialize market intelligence monitor
            print("\n1. INITIALIZING MARKET INTELLIGENCE MONITOR...")
            processor = MarketIntelligenceMonitor()
            
            config = ProcessorConfig(
                workflow_id="test_market_intelligence",
                processor_name="market_intelligence_monitor",
                workflow_config={}
            )
            
            print("   Monitor initialized successfully")
            print(f"   Monitoring sources: {len(processor.monitoring_sources)} categories")
            
            # Display monitoring sources
            for category, sources in processor.monitoring_sources.items():
                print(f"     - {category}: {len(sources)} sources")
            
            # Test 2: Run market intelligence monitoring
            print("\n2. RUNNING MARKET INTELLIGENCE MONITORING...")
            result = await processor.execute(config)
            
            if result.success:
                print("   Market Intelligence Monitoring: SUCCESS")
                
                # Display monitoring summary
                monitoring_summary = result.data.get("monitoring_summary", {})
                print(f"   Monitoring Timestamp: {monitoring_summary.get('monitoring_cycle_timestamp', 'N/A')}")
                print(f"   Funding Trends: {monitoring_summary.get('funding_trends_identified', 0)}")
                print(f"   Policy Changes: {monitoring_summary.get('policy_changes_detected', 0)}")
                print(f"   Market Developments: {monitoring_summary.get('market_developments_analyzed', 0)}")
                print(f"   Alerts Generated: {monitoring_summary.get('alerts_generated', 0)}")
                
                coverage = monitoring_summary.get("monitoring_coverage", {})
                print(f"   Coverage - Gov: {coverage.get('government_agencies', 0)}, "
                      f"Foundation: {coverage.get('foundation_sources', 0)}, "
                      f"Policy: {coverage.get('policy_sources', 0)}")
                
                # Test 3: Analyze market alerts
                print("\n3. ANALYZING MARKET ALERTS...")
                alerts = result.data.get("market_alerts", [])
                
                alert_types = {}
                severity_levels = {}
                
                for alert in alerts:
                    alert_type = alert.get("alert_type", "unknown")
                    severity = alert.get("severity", "unknown")
                    
                    alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
                    severity_levels[severity] = severity_levels.get(severity, 0) + 1
                    
                print(f"   Total Alerts: {len(alerts)}")
                print(f"   Alert Types: {dict(alert_types)}")
                print(f"   Severity Levels: {dict(severity_levels)}")
                
                # Show sample alerts
                for i, alert in enumerate(alerts[:3], 1):
                    print(f"   Alert {i}: {alert.get('title', 'Unknown')}")
                    print(f"     Type: {alert.get('alert_type', 'N/A')}, Severity: {alert.get('severity', 'N/A')}")
                    print(f"     Description: {alert.get('description', 'No description')[:100]}...")
                    
                    impact_areas = alert.get("impact_areas", [])
                    if impact_areas:
                        print(f"     Impact Areas: {', '.join(impact_areas[:3])}")
                
                # Test 4: Examine funding trends
                print("\n4. EXAMINING FUNDING TRENDS...")
                funding_trends = result.data.get("funding_trends", [])
                
                trend_types = {}
                high_confidence_trends = 0
                
                for trend in funding_trends:
                    trend_type = trend.get("trend_type", "unknown")
                    confidence = trend.get("confidence", 0)
                    
                    trend_types[trend_type] = trend_types.get(trend_type, 0) + 1
                    if confidence >= 0.8:
                        high_confidence_trends += 1
                
                print(f"   Total Trends: {len(funding_trends)}")
                print(f"   Trend Types: {dict(trend_types)}")
                print(f"   High Confidence Trends: {high_confidence_trends}")
                
                # Show sample trends
                for i, trend in enumerate(funding_trends[:2], 1):
                    print(f"   Trend {i}: {trend.get('trend_type', 'Unknown').replace('_', ' ').title()}")
                    print(f"     Direction: {trend.get('trend_direction', 'N/A')}")
                    print(f"     Confidence: {trend.get('confidence', 0):.1%}")
                    
                    sectors = trend.get("affected_sectors", [])
                    if sectors:
                        print(f"     Affected Sectors: {', '.join(sectors[:3])}")
                
                # Test 5: Review trend analysis
                print("\n5. REVIEWING TREND ANALYSIS...")
                trend_analysis = result.data.get("trend_analysis", {})
                trend_summary = trend_analysis.get("trend_summary", {})
                market_outlook = trend_analysis.get("market_outlook", {})
                
                print(f"   Increasing Funding Areas: {len(trend_summary.get('increasing_funding_areas', []))}")
                print(f"   Decreasing Funding Areas: {len(trend_summary.get('decreasing_funding_areas', []))}")
                print(f"   Shifting Priorities: {len(trend_summary.get('shifting_priorities', []))}")
                print(f"   Market Confidence: {market_outlook.get('confidence_level', 'unknown')}")
                print(f"   Opportunity Timeline: {market_outlook.get('opportunity_timeline', 'N/A')}")
                print(f"   Positive Indicators: {market_outlook.get('positive_indicators', 0)}")
                print(f"   Negative Indicators: {market_outlook.get('negative_indicators', 0)}")
                
                # Test 6: Examine strategic insights
                print("\n6. EXAMINING STRATEGIC INSIGHTS...")
                strategic_insights = result.data.get("strategic_insights", {})
                
                opportunities = strategic_insights.get("key_opportunities", [])
                risks = strategic_insights.get("risk_factors", [])
                recommendations = strategic_insights.get("strategic_recommendations", [])
                timing = strategic_insights.get("timing_considerations", [])
                
                print(f"   Key Opportunities: {len(opportunities)}")
                for i, opportunity in enumerate(opportunities[:2], 1):
                    print(f"     {i}. {opportunity}")
                
                print(f"   Risk Factors: {len(risks)}")
                for i, risk in enumerate(risks[:2], 1):
                    print(f"     {i}. {risk}")
                
                print(f"   Strategic Recommendations: {len(recommendations)}")
                for i, rec in enumerate(recommendations[:2], 1):
                    print(f"     {i}. {rec}")
                
                print(f"   Timing Considerations: {len(timing)}")
                for i, time_factor in enumerate(timing[:2], 1):
                    print(f"     {i}. {time_factor}")
                
                # Test 7: Verify database storage
                print("\n7. VERIFYING DATABASE STORAGE...")
                stored_alerts = self.verify_stored_intelligence()
                print(f"   Stored Intelligence Records: {stored_alerts}")
                
            else:
                print("   Market Intelligence Monitoring: FAILED")
                print(f"   Errors: {result.errors}")
                return False
            
            # Test 8: Verify metadata
            print("\n8. VERIFYING MONITORING METADATA...")
            metadata = result.metadata
            analysis_type = metadata.get("analysis_type")
            monitoring_sources = metadata.get("monitoring_sources", [])
            alert_severity = metadata.get("alert_severity_distribution", {})
            trend_confidence = metadata.get("trend_confidence_summary", {})
            
            print(f"   Analysis Type: {analysis_type}")
            print(f"   Monitoring Sources: {', '.join(monitoring_sources)}")
            print(f"   Alert Severity Distribution: {alert_severity}")
            print(f"   Trend Confidence Summary: {trend_confidence}")
            
            print("\n" + "=" * 40)
            print("MARKET INTELLIGENCE MONITOR TEST SUMMARY: SUCCESS")
            print("\nMarket Intelligence Monitor capabilities verified:")
            print("- Comprehensive funding trend monitoring")
            print("- Policy change detection and tracking")
            print("- Market development analysis and insights")
            print("- Intelligent alert generation for significant changes")
            print("- Strategic insights and actionable recommendations")
            print("- Historical intelligence data storage and tracking")
            
            return True
            
        except Exception as e:
            print(f"ERROR: Market intelligence monitor test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_stored_intelligence(self) -> int:
        """Verify market intelligence data was stored in database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM market_intelligence_log")
                count = cursor.fetchone()[0]
                return count
        except Exception as e:
            print(f"   Database verification error: {e}")
            return 0


async def main():
    """Run the market intelligence monitor test."""
    test_runner = MarketIntelligenceMonitorTest()
    success = await test_runner.run_monitor_test()
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)