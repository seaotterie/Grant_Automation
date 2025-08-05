#!/usr/bin/env python3
"""
Catalynx Analytics Export Utility
Professional analytics report generation with strategic insights.

This utility generates comprehensive reports from analytics processors including:
- Executive summary reports
- Trend analysis reports  
- Risk assessment reports
- Competitive intelligence reports
- Strategic insights and recommendations
"""

import asyncio
import pandas as pd
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.workflow_engine import WorkflowEngine
from src.core.data_models import WorkflowConfig

class AnalyticsExporter:
    """Professional analytics report exporter."""
    
    def __init__(self, output_dir: str = "analytics_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    async def export_all_reports(self, workflow_id: Optional[str] = None):
        """Export all analytics reports."""
        print("🚀 Starting Catalynx Analytics Export...")
        
        try:
            # Load analytics data
            analytics_data = await self._load_analytics_data(workflow_id)
            if not analytics_data:
                print("❌ No analytics data found to export")
                return
            
            print(f"📊 Found analytics data with {len(analytics_data.get('organizations', []))} organizations")
            
            # Export individual reports
            reports_generated = []
            
            # Executive Summary
            exec_summary_path = await self._export_executive_summary(analytics_data)
            if exec_summary_path:
                reports_generated.append(exec_summary_path)
            
            # Trend Analysis Report  
            trend_report_path = await self._export_trend_analysis(analytics_data)
            if trend_report_path:
                reports_generated.append(trend_report_path)
            
            # Risk Assessment Report
            risk_report_path = await self._export_risk_assessment(analytics_data)
            if risk_report_path:
                reports_generated.append(risk_report_path)
            
            # Competitive Intelligence Report
            competitive_report_path = await self._export_competitive_intelligence(analytics_data)
            if competitive_report_path:
                reports_generated.append(competitive_report_path)
            
            # Strategic Insights Report
            strategic_report_path = await self._export_strategic_insights(analytics_data)
            if strategic_report_path:
                reports_generated.append(strategic_report_path)
            
            # Organization Details Report
            org_details_path = await self._export_organization_details(analytics_data)
            if org_details_path:
                reports_generated.append(org_details_path)
            
            print(f"\n✅ Analytics export completed successfully!")
            print(f"📁 {len(reports_generated)} reports generated in: {self.output_dir}")
            
            for report_path in reports_generated:
                print(f"   📄 {report_path.name}")
            
            return reports_generated
            
        except Exception as e:
            print(f"❌ Analytics export failed: {e}")
            raise
    
    async def _load_analytics_data(self, workflow_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load analytics data from latest workflow results."""
        try:
            # Try to load from workflow engine results
            workflow_engine = WorkflowEngine()
            
            if workflow_id:
                # Load specific workflow
                results = await workflow_engine.get_workflow_results(workflow_id)
                if results:
                    return self._combine_processor_results(results)
            
            # Load latest results from logs directory
            logs_dir = Path("logs")
            if logs_dir.exists():
                # Look for latest workflow results
                result_files = list(logs_dir.glob("workflow_*.json"))
                if result_files:
                    latest_file = max(result_files, key=lambda x: x.stat().st_mtime)
                    print(f"📂 Loading analytics data from: {latest_file}")
                    
                    with open(latest_file, 'r') as f:
                        workflow_data = json.load(f)
                        return self._combine_processor_results(workflow_data)
            
            print("⚠️  No analytics data found. Please run the analytics workflow first.")
            return None
            
        except Exception as e:
            print(f"❌ Error loading analytics data: {e}")
            return None
    
    def _combine_processor_results(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Combine results from multiple processors into unified analytics data."""
        combined_data = {
            "organizations": [],
            "trend_analysis": [],
            "risk_assessments": [],
            "competitive_insights": {},
            "market_analysis": {},
            "peer_analysis": {},
            "funding_opportunities": {}
        }
        
        # Extract data from each processor
        processor_results = workflow_data.get("processor_results", {})
        
        # Get organizations from financial scorer
        if "financial_scorer" in processor_results:
            scorer_data = processor_results["financial_scorer"].get("data", {})
            combined_data["organizations"] = scorer_data.get("organizations", [])
        
        # Get trend analysis
        if "trend_analyzer" in processor_results:
            trend_data = processor_results["trend_analyzer"].get("data", {})
            combined_data["trend_analysis"] = trend_data.get("trend_analysis", [])
        
        # Get risk assessments
        if "risk_assessor" in processor_results:
            risk_data = processor_results["risk_assessor"].get("data", {})
            combined_data["risk_assessments"] = risk_data.get("risk_assessments", [])
        
        # Get competitive intelligence
        if "competitive_intelligence" in processor_results:
            comp_data = processor_results["competitive_intelligence"].get("data", {})
            combined_data["competitive_insights"] = comp_data.get("competitive_insights", {})
            combined_data["market_analysis"] = comp_data.get("market_analysis", {})
            combined_data["peer_analysis"] = comp_data.get("peer_analysis", {})
            combined_data["funding_opportunities"] = comp_data.get("funding_opportunities", {})
        
        return combined_data
    
    async def _export_executive_summary(self, analytics_data: Dict[str, Any]) -> Optional[Path]:
        """Export executive summary report."""
        try:
            print("📊 Generating executive summary report...")
            
            # Create executive summary data
            organizations = analytics_data.get("organizations", [])
            risk_assessments = analytics_data.get("risk_assessments", [])
            competitive_insights = analytics_data.get("competitive_insights", {})
            
            # Key metrics
            total_orgs = len(organizations)
            avg_revenue = sum(org.get("revenue", 0) for org in organizations) / total_orgs if total_orgs > 0 else 0
            total_market_size = sum(org.get("revenue", 0) for org in organizations)
            
            low_risk_count = sum(1 for r in risk_assessments if r.get("risk_classification") == "low")
            grant_ready_count = sum(1 for r in risk_assessments if r.get("grant_readiness_score", 0) > 0.7)
            
            # Market insights
            market_health = competitive_insights.get("competitive_landscape_summary", {}).get("competitive_health", "unknown")
            key_findings = competitive_insights.get("key_findings", [])
            strategic_recommendations = competitive_insights.get("strategic_recommendations", [])
            
            # Create executive summary
            summary_data = {
                "Report Title": "Catalynx Analytics - Executive Summary",
                "Generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Analysis Period": "Multi-year trend analysis",
                "": "",
                "KEY METRICS": "",
                "Total Organizations Analyzed": total_orgs,
                "Average Organization Revenue": f"${avg_revenue:,.0f}",
                "Total Market Size": f"${total_market_size:,.0f}",
                "Low Risk Organizations": f"{low_risk_count} ({low_risk_count/total_orgs*100:.0f}%)" if total_orgs > 0 else "0",
                "Grant Ready Organizations": f"{grant_ready_count} ({grant_ready_count/total_orgs*100:.0f}%)" if total_orgs > 0 else "0",
                "Market Health Assessment": market_health.title(),
                " ": "",
                "TOP INSIGHTS": "",
            }
            
            # Add key findings
            for i, finding in enumerate(key_findings[:5]):
                summary_data[f"Key Finding {i+1}"] = finding
            
            summary_data["  "] = ""
            summary_data["STRATEGIC RECOMMENDATIONS"] = ""
            
            # Add strategic recommendations
            for i, rec in enumerate(strategic_recommendations[:5]):
                summary_data[f"Recommendation {i+1}"] = rec
            
            # Convert to DataFrame and export
            df_summary = pd.DataFrame(list(summary_data.items()), columns=["Metric", "Value"])
            
            output_path = self.output_dir / f"catalynx_executive_summary_{self.timestamp}.csv"
            df_summary.to_csv(output_path, index=False)
            
            print(f"   ✅ Executive summary: {output_path.name}")
            return output_path
            
        except Exception as e:
            print(f"   ❌ Failed to generate executive summary: {e}")
            return None
    
    async def _export_trend_analysis(self, analytics_data: Dict[str, Any]) -> Optional[Path]:
        """Export trend analysis report."""
        try:
            print("📈 Generating trend analysis report...")
            
            trend_analysis = analytics_data.get("trend_analysis", [])
            if not trend_analysis:
                print("   ⚠️  No trend analysis data available")
                return None
            
            # Create trend summary data
            trend_data = []
            
            for org_trend in trend_analysis:
                ein = org_trend.get("ein", "")
                name = org_trend.get("name", "Unknown")
                years_of_data = org_trend.get("years_of_data", 0)
                
                # Revenue trend
                revenue_trend = org_trend.get("revenue_trend", {})
                revenue_growth = revenue_trend.get("annual_growth_rate", 0)
                revenue_classification = revenue_trend.get("trend", "unknown")
                
                # Financial stability
                financial_stability = org_trend.get("financial_stability", {})
                stability_score = financial_stability.get("stability_score", 0)
                
                # Growth classification
                growth_class = org_trend.get("growth_classification", "unknown")
                grant_readiness = org_trend.get("grant_readiness_score", 0)
                
                # Recommendations
                recommendations = org_trend.get("strategic_recommendations", [])
                primary_recommendation = recommendations[0] if recommendations else "No specific recommendation"
                
                trend_data.append({
                    "EIN": ein,
                    "Organization Name": name,
                    "Years of Data": years_of_data,
                    "Revenue Growth Rate": f"{revenue_growth*100:.1f}%",
                    "Revenue Trend": revenue_classification.replace("_", " ").title(),
                    "Growth Classification": growth_class.replace("_", " ").title(),
                    "Financial Stability Score": f"{stability_score:.2f}",
                    "Grant Readiness Score": f"{grant_readiness:.2f}",
                    "Primary Recommendation": primary_recommendation
                })
            
            # Create DataFrame and export
            df_trends = pd.DataFrame(trend_data)
            
            output_path = self.output_dir / f"catalynx_trend_analysis_{self.timestamp}.csv"
            df_trends.to_csv(output_path, index=False)
            
            print(f"   ✅ Trend analysis: {output_path.name}")
            return output_path
            
        except Exception as e:
            print(f"   ❌ Failed to generate trend analysis: {e}")
            return None
    
    async def _export_risk_assessment(self, analytics_data: Dict[str, Any]) -> Optional[Path]:
        """Export risk assessment report."""
        try:
            print("🎯 Generating risk assessment report...")
            
            risk_assessments = analytics_data.get("risk_assessments", [])
            if not risk_assessments:
                print("   ⚠️  No risk assessment data available")
                return None
            
            # Create risk assessment data
            risk_data = []
            
            for assessment in risk_assessments:
                ein = assessment.get("ein", "")
                name = assessment.get("name", "Unknown")
                composite_risk = assessment.get("composite_risk_score", 0)
                risk_classification = assessment.get("risk_classification", "unknown")
                grant_readiness = assessment.get("grant_readiness_score", 0)
                readiness_level = assessment.get("grant_readiness_level", "unknown")
                
                # Risk components
                risk_components = assessment.get("risk_components", {})
                financial_risk = risk_components.get("financial_stability", {}).get("score", 0)
                operational_risk = risk_components.get("operational_risk", {}).get("score", 0)
                sustainability_risk = risk_components.get("sustainability_risk", {}).get("score", 0)
                compliance_risk = risk_components.get("compliance_risk", {}).get("score", 0)
                capacity_risk = risk_components.get("capacity_risk", {}).get("score", 0)
                external_risk = risk_components.get("external_risk", {}).get("score", 0)
                
                # Key risk factors
                key_risks = assessment.get("key_risk_factors", [])
                risk_summary = ", ".join(key_risks[:3]) if key_risks else "No major risk factors"
                
                # Funding recommendations
                funding_recs = assessment.get("funding_recommendations", [])
                funding_rec = funding_recs[0] if funding_recs else "Standard grant consideration"
                
                risk_data.append({
                    "EIN": ein,
                    "Organization Name": name,
                    "Composite Risk Score": f"{composite_risk:.2f}",
                    "Risk Classification": risk_classification.replace("_", " ").title(),
                    "Grant Readiness Score": f"{grant_readiness:.2f}",
                    "Grant Readiness Level": readiness_level.title(),
                    "Financial Stability": f"{financial_risk:.2f}",
                    "Operational Risk": f"{operational_risk:.2f}",
                    "Sustainability Risk": f"{sustainability_risk:.2f}",
                    "Compliance Risk": f"{compliance_risk:.2f}",
                    "Capacity Risk": f"{capacity_risk:.2f}",
                    "External Risk": f"{external_risk:.2f}",
                    "Key Risk Factors": risk_summary,
                    "Funding Recommendation": funding_rec
                })
            
            # Create DataFrame and export
            df_risk = pd.DataFrame(risk_data)
            
            output_path = self.output_dir / f"catalynx_risk_assessment_{self.timestamp}.csv"
            df_risk.to_csv(output_path, index=False)
            
            print(f"   ✅ Risk assessment: {output_path.name}")
            return output_path
            
        except Exception as e:
            print(f"   ❌ Failed to generate risk assessment: {e}")
            return None
    
    async def _export_competitive_intelligence(self, analytics_data: Dict[str, Any]) -> Optional[Path]:
        """Export competitive intelligence report."""
        try:
            print("🏆 Generating competitive intelligence report...")
            
            competitive_insights = analytics_data.get("competitive_insights", {})
            market_analysis = analytics_data.get("market_analysis", {})
            
            if not competitive_insights:
                print("   ⚠️  No competitive intelligence data available")
                return None
            
            # Market overview data
            market_data = []
            
            # Market dynamics
            market_dynamics = competitive_insights.get("market_dynamics", {})
            landscape_summary = competitive_insights.get("competitive_landscape_summary", {})
            
            market_data.extend([
                ["MARKET OVERVIEW", ""],
                ["Market Maturity", market_dynamics.get("market_maturity", "unknown").title()],
                ["Competitive Intensity", market_dynamics.get("competitive_intensity", "unknown").title()],
                ["Market Growth Potential", market_dynamics.get("market_growth_potential", "unknown").title()],
                ["Consolidation Potential", market_dynamics.get("consolidation_potential", "unknown").title()],
                ["Total Organizations", landscape_summary.get("total_organizations", 0)],
                ["Total Market Size", f"${landscape_summary.get('total_market_size', 0):,.0f}"],
                ["Geographic Reach", f"{landscape_summary.get('geographic_reach', 0)} states"],
                ["Competitive Health", landscape_summary.get("competitive_health", "unknown").title()],
                ["", ""],
            ])
            
            # Market concentration
            concentration = market_analysis.get("market_concentration", {})
            market_data.extend([
                ["MARKET CONCENTRATION", ""],
                ["Market Structure", concentration.get("market_structure", "unknown").replace("_", " ").title()],
                ["Top 4 Concentration Ratio", f"{concentration.get('concentration_ratio_4', 0)*100:.0f}%"],
                ["Herfindahl Index", f"{concentration.get('herfindahl_index', 0):.3f}"],
                ["", ""],
            ])
            
            # Market leaders
            market_leaders = market_analysis.get("market_leaders", [])
            if market_leaders:
                market_data.append(["MARKET LEADERS", ""])
                for i, leader in enumerate(market_leaders[:5]):
                    leadership_type = leader.get("leadership_type", "unknown").replace("_", " ").title()
                    metric_value = leader.get("metric_value", 0)
                    if "revenue" in leader.get("leadership_type", ""):
                        metric_display = f"${metric_value:,.0f}"
                    else:
                        metric_display = f"{metric_value:.2f}"
                    
                    market_data.append([
                        f"Leader {i+1} - {leadership_type}",
                        f"{leader.get('name', 'Unknown')} ({metric_display})"
                    ])
                market_data.append(["", ""])
            
            # Key findings
            key_findings = competitive_insights.get("key_findings", [])
            if key_findings:
                market_data.append(["KEY MARKET FINDINGS", ""])
                for i, finding in enumerate(key_findings):
                    market_data.append([f"Finding {i+1}", finding])
                market_data.append(["", ""])
            
            # Strategic recommendations
            strategic_recs = competitive_insights.get("strategic_recommendations", [])
            if strategic_recs:
                market_data.append(["STRATEGIC RECOMMENDATIONS", ""])
                for i, rec in enumerate(strategic_recs):
                    market_data.append([f"Recommendation {i+1}", rec])
            
            # Create DataFrame and export
            df_competitive = pd.DataFrame(market_data, columns=["Category", "Details"])
            
            output_path = self.output_dir / f"catalynx_competitive_intelligence_{self.timestamp}.csv"
            df_competitive.to_csv(output_path, index=False)
            
            print(f"   ✅ Competitive intelligence: {output_path.name}")
            return output_path
            
        except Exception as e:
            print(f"   ❌ Failed to generate competitive intelligence: {e}")
            return None
    
    async def _export_strategic_insights(self, analytics_data: Dict[str, Any]) -> Optional[Path]:
        """Export strategic insights and recommendations."""
        try:
            print("🎯 Generating strategic insights report...")
            
            funding_opportunities = analytics_data.get("funding_opportunities", {})
            competitive_insights = analytics_data.get("competitive_insights", {})
            
            if not funding_opportunities:
                print("   ⚠️  No strategic insights data available")
                return None
            
            # Strategic insights data
            insights_data = []
            
            # Funding priorities
            funding_priorities = funding_opportunities.get("funding_priorities", [])
            if funding_priorities:
                insights_data.extend([
                    ["FUNDING PRIORITIES", ""],
                ])
                
                for i, priority in enumerate(funding_priorities):
                    priority_type = priority.get("type", "unknown").replace("_", " ").title()
                    priority_level = priority.get("priority_level", "medium").upper()
                    rationale = priority.get("rationale", "No rationale provided")
                    organization = priority.get("organization", priority.get("segment", "Multiple"))
                    
                    insights_data.extend([
                        [f"Priority {i+1} - {priority_level}", priority_type],
                        ["Target", organization],
                        ["Rationale", rationale],
                        ["", ""],
                    ])
            
            # Risk-adjusted opportunities
            risk_adjusted_opps = funding_opportunities.get("risk_adjusted_opportunities", [])
            if risk_adjusted_opps:
                insights_data.extend([
                    ["RISK-ADJUSTED OPPORTUNITIES", ""],
                ])
                
                for i, opp in enumerate(risk_adjusted_opps):
                    opp_type = opp.get("opportunity_type", "unknown").replace("_", " ").title()
                    risk_level = opp.get("risk_level", "unknown").title()
                    expected_impact = opp.get("expected_impact", "unknown").title()
                    rationale = opp.get("rationale", "No rationale provided")
                    
                    insights_data.extend([
                        [f"Opportunity {i+1}", opp.get("name", "Unknown Organization")],
                        ["Type", opp_type],
                        ["Risk Level", risk_level],
                        ["Expected Impact", expected_impact],
                        ["Rationale", rationale],
                        ["", ""],
                    ])
            
            # Portfolio recommendations
            portfolio_recs = funding_opportunities.get("portfolio_recommendations", [])
            if portfolio_recs:
                insights_data.extend([
                    ["PORTFOLIO RECOMMENDATIONS", ""],
                ])
                
                for i, rec in enumerate(portfolio_recs):
                    insights_data.append([f"Portfolio Strategy {i+1}", rec])
                
                insights_data.append(["", ""])
            
            # Strategic themes
            strategic_themes = funding_opportunities.get("strategic_funding_themes", [])
            if strategic_themes:
                insights_data.extend([
                    ["STRATEGIC FUNDING THEMES", ""],
                ])
                
                for i, theme in enumerate(strategic_themes):
                    theme_display = theme.replace("_", " ").title()
                    insights_data.append([f"Theme {i+1}", theme_display])
                
                insights_data.append(["", ""])
            
            # Market gaps
            market_gaps = funding_opportunities.get("market_gaps", [])
            if market_gaps:
                insights_data.extend([
                    ["MARKET OPPORTUNITIES", ""],
                ])
                
                for i, gap in enumerate(market_gaps):
                    gap_type = gap.get("type", "unknown").replace("_", " ").title()
                    segment = gap.get("segment", "Unknown segment")
                    insights_data.append([f"Opportunity {i+1} - {gap_type}", segment])
            
            # Create DataFrame and export
            df_insights = pd.DataFrame(insights_data, columns=["Category", "Details"])
            
            output_path = self.output_dir / f"catalynx_strategic_insights_{self.timestamp}.csv"
            df_insights.to_csv(output_path, index=False)
            
            print(f"   ✅ Strategic insights: {output_path.name}")
            return output_path
            
        except Exception as e:
            print(f"   ❌ Failed to generate strategic insights: {e}")
            return None
    
    async def _export_organization_details(self, analytics_data: Dict[str, Any]) -> Optional[Path]:
        """Export detailed organization information."""
        try:
            print("📋 Generating organization details report...")
            
            organizations = analytics_data.get("organizations", [])
            risk_assessments = analytics_data.get("risk_assessments", [])
            
            if not organizations:
                print("   ⚠️  No organization data available")
                return None
            
            # Create organization details data
            org_data = []
            
            # Create lookup for risk assessments
            risk_lookup = {}
            for assessment in risk_assessments:
                risk_lookup[assessment.get("ein", "")] = assessment
            
            for org in organizations:
                ein = org.get("ein", "")
                risk_assessment = risk_lookup.get(ein, {})
                
                org_record = {
                    "EIN": ein,
                    "Organization Name": org.get("name", "Unknown"),
                    "State": org.get("state", ""),
                    "NTEE Code": org.get("ntee_code", ""),
                    "Revenue": f"${org.get('revenue', 0):,.0f}",
                    "Assets": f"${org.get('assets', 0):,.0f}",
                    "Composite Score": f"{org.get('composite_score', 0):.2f}",
                    "Score Rank": org.get("score_rank", ""),
                    "Program Expense Ratio": f"{org.get('program_expense_ratio', 0):.2f}",
                    "Filing Recency Score": f"{org.get('filing_recency_score', 0):.2f}",
                    "Financial Health Score": f"{org.get('financial_health_score', 0):.2f}",
                    "Most Recent Filing Year": org.get("most_recent_filing_year", ""),
                    "Risk Classification": risk_assessment.get("risk_classification", "unknown").replace("_", " ").title(),
                    "Grant Readiness Level": risk_assessment.get("grant_readiness_level", "unknown").title(),
                    "Risk Score": f"{risk_assessment.get('composite_risk_score', 0):.2f}",
                    "Grant Readiness Score": f"{risk_assessment.get('grant_readiness_score', 0):.2f}"
                }
                
                org_data.append(org_record)
            
            # Create DataFrame and export
            df_orgs = pd.DataFrame(org_data)
            
            output_path = self.output_dir / f"catalynx_organization_details_{self.timestamp}.csv"
            df_orgs.to_csv(output_path, index=False)
            
            print(f"   ✅ Organization details: {output_path.name}")
            return output_path
            
        except Exception as e:
            print(f"   ❌ Failed to generate organization details: {e}")
            return None


async def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Export Catalynx Analytics Reports")
    parser.add_argument("--workflow-id", help="Specific workflow ID to export")
    parser.add_argument("--output-dir", default="analytics_reports", help="Output directory for reports")
    
    args = parser.parse_args()
    
    # Create exporter and run
    exporter = AnalyticsExporter(output_dir=args.output_dir)
    await exporter.export_all_reports(workflow_id=args.workflow_id)


if __name__ == "__main__":
    asyncio.run(main())