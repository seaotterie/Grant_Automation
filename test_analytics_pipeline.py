#!/usr/bin/env python3
"""
Test Analytics Pipeline
Test the complete advanced analytics pipeline with trend analysis, risk assessment, and competitive intelligence.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.workflow_engine import WorkflowEngine
from src.core.data_models import WorkflowConfig
from src.processors.analysis.trend_analyzer import TrendAnalyzerProcessor
from src.processors.analysis.risk_assessor import RiskAssessorProcessor
from src.processors.analysis.competitive_intelligence import CompetitiveIntelligenceProcessor

async def test_analytics_pipeline():
    """Test the complete analytics pipeline."""
    print("Testing Catalynx Advanced Analytics Pipeline")
    print("=" * 60)
    
    try:
        # Initialize workflow engine
        print("Initializing workflow engine...")
        workflow_engine = WorkflowEngine()
        
        # Create workflow configuration
        config = WorkflowConfig(
            workflow_id="analytics_test",
            name="Analytics Pipeline Test",
            description="Test advanced analytics processors",
            target_ein="541669652",
            ntee_codes=["E21", "E30", "E31", "E32", "F30", "F32", "P81"],
            states=["VA"],
            min_revenue=50000,
            max_results=15
        )
        
        print(f"Created workflow configuration: {config.workflow_id}")
        
        # Define the analytics processor pipeline
        analytics_processors = [
            "ein_lookup",          # Step 1: Get organizations
            "bmf_filter",          # Step 2: Filter BMF records
            "propublica_fetch",    # Step 3: Fetch detailed data
            "financial_scorer",    # Step 4: Score organizations
            "trend_analyzer",      # Step 5: Analyze trends
            "risk_assessor",       # Step 6: Assess risks
            "competitive_intelligence"  # Step 7: Competitive analysis
        ]
        
        print("Analytics processor pipeline:")
        for i, processor in enumerate(analytics_processors, 1):
            print(f"   {i}. {processor.replace('_', ' ').title()}")
        
        print("\nRunning analytics pipeline...")
        print("-" * 40)
        
        # Execute the workflow
        result = await workflow_engine.execute_workflow(config, analytics_processors)
        
        if result.success:
            print(f"\nAnalytics pipeline completed successfully!")
            print(f"Total execution time: {result.execution_time:.2f} seconds")
            
            # Display results summary
            await display_analytics_summary(result)
            
            # Save results for later use
            await save_analytics_results(result)
            
        else:
            print(f"\nAnalytics pipeline failed!")
            for error in result.errors:
                print(f"   ERROR: {error}")
        
        return result
        
    except Exception as e:
        print(f"Analytics pipeline test failed: {e}")
        raise

async def display_analytics_summary(workflow_result):
    """Display summary of analytics results."""
    print("\n[STATS] ANALYTICS RESULTS SUMMARY")
    print("=" * 50)
    
    processor_results = workflow_result.processor_results
    
    # Financial Scorer Results
    if "financial_scorer" in processor_results:
        scorer_result = processor_results["financial_scorer"]
        if scorer_result.success:
            scorer_data = scorer_result.data
            organizations = scorer_data.get("organizations", [])
            scoring_stats = scorer_data.get("scoring_stats", {})
            
            print(f"[FINANCIAL] Financial Scoring:")
            print(f"   Organizations scored: {scoring_stats.get('fully_scored', 0)}")
            print(f"   Partial scores: {scoring_stats.get('partially_scored', 0)}")
            
            if organizations:
                top_org = organizations[0]
                print(f"   Top organization: {top_org.get('name', 'Unknown')} (Score: {top_org.get('composite_score', 0):.2f})")
    
    # Trend Analysis Results
    if "trend_analyzer" in processor_results:
        trend_result = processor_results["trend_analyzer"]
        if trend_result.success:
            trend_data = trend_result.data
            trend_analysis = trend_data.get("trend_analysis", [])
            market_insights = trend_data.get("market_insights", {})
            
            print(f"\n[TRENDS] Trend Analysis:")
            print(f"   Organizations analyzed: {len(trend_analysis)}")
            
            # Growth classification summary
            growth_patterns = {}
            for org_trend in trend_analysis:
                pattern = org_trend.get("growth_classification", "unknown")
                growth_patterns[pattern] = growth_patterns.get(pattern, 0) + 1
            
            print(f"   Growth patterns:")
            for pattern, count in growth_patterns.items():
                print(f"     - {pattern.replace('_', ' ').title()}: {count}")
            
            if market_insights:
                market_health = market_insights.get("market_health_assessment", "unknown")
                print(f"   Market health: {market_health.title()}")
    
    # Risk Assessment Results
    if "risk_assessor" in processor_results:
        risk_result = processor_results["risk_assessor"]
        if risk_result.success:
            risk_data = risk_result.data
            risk_assessments = risk_data.get("risk_assessments", [])
            
            print(f"\n[RISK] Risk Assessment:")
            print(f"   Organizations assessed: {len(risk_assessments)}")
            
            # Risk level summary
            risk_levels = {}
            grant_ready_count = 0
            
            for assessment in risk_assessments:
                risk_level = assessment.get("risk_classification", "unknown")
                risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
                
                if assessment.get("grant_readiness_score", 0) > 0.7:
                    grant_ready_count += 1
            
            print(f"   Risk distribution:")
            for level, count in risk_levels.items():
                print(f"     - {level.replace('_', ' ').title()}: {count}")
            
            print(f"   Grant ready organizations: {grant_ready_count}")
    
    # Competitive Intelligence Results
    if "competitive_intelligence" in processor_results:
        comp_result = processor_results["competitive_intelligence"]
        if comp_result.success:
            comp_data = comp_result.data
            competitive_insights = comp_data.get("competitive_insights", {})
            market_analysis = comp_data.get("market_analysis", {})
            peer_analysis = comp_data.get("peer_analysis", {})
            
            print(f"\n[COMPETITIVE] Competitive Intelligence:")
            
            # Market structure
            concentration = market_analysis.get("market_concentration", {})
            market_structure = concentration.get("market_structure", "unknown")
            print(f"   Market structure: {market_structure.replace('_', ' ').title()}")
            
            # Competitive clusters
            clusters = peer_analysis.get("clusters", [])
            print(f"   Competitive clusters: {len(clusters)}")
            
            # Market health
            landscape_summary = competitive_insights.get("competitive_landscape_summary", {})
            competitive_health = landscape_summary.get("competitive_health", "unknown")
            print(f"   Competitive health: {competitive_health.title()}")
            
            # Strategic recommendations
            strategic_recs = competitive_insights.get("strategic_recommendations", [])
            if strategic_recs:
                print(f"   Key recommendations:")
                for i, rec in enumerate(strategic_recs[:2], 1):
                    print(f"     {i}. {rec}")

async def save_analytics_results(workflow_result):
    """Save analytics results to files."""
    print(f"\n[SAVE] Saving analytics results...")
    
    # Save to logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    timestamp = workflow_result.end_time.strftime("%Y%m%d_%H%M%S")
    
    # Save workflow results as JSON
    import json
    
    # Convert workflow result to dict for JSON serialization
    result_dict = {
        "workflow_id": workflow_result.workflow_id,
        "success": workflow_result.success,
        "start_time": workflow_result.start_time.isoformat(),
        "end_time": workflow_result.end_time.isoformat(),
        "execution_time": workflow_result.execution_time,
        "processor_results": {}
    }
    
    # Convert processor results
    for processor_name, result in workflow_result.processor_results.items():
        result_dict["processor_results"][processor_name] = {
            "success": result.success,
            "execution_time": result.execution_time,
            "data": result.data,
            "errors": result.errors,
            "metadata": result.metadata
        }
    
    # Save results
    results_file = logs_dir / f"analytics_workflow_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(result_dict, f, indent=2, default=str)
    
    print(f"   [FILE] Results saved to: {results_file}")
    
    # Also save a summary file
    summary_file = logs_dir / f"analytics_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write("CATALYNX ANALYTICS PIPELINE RESULTS\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Workflow ID: {workflow_result.workflow_id}\n")
        f.write(f"Execution Time: {workflow_result.execution_time:.2f} seconds\n")
        f.write(f"Success: {workflow_result.success}\n\n")
        
        f.write("PROCESSOR RESULTS:\n")
        f.write("-" * 20 + "\n")
        for processor_name, result in workflow_result.processor_results.items():
            f.write(f"{processor_name}: {'SUCCESS' if result.success else 'FAILED'}\n")
            if result.execution_time:
                f.write(f"  Execution time: {result.execution_time:.2f}s\n")
            if result.errors:
                f.write(f"  Errors: {len(result.errors)}\n")
        
        f.write(f"\nGenerated: {workflow_result.end_time.isoformat()}\n")
    
    print(f"   [SUMMARY] Summary saved to: {summary_file}")

async def test_individual_processors():
    """Test individual analytics processors."""
    print("\n[TEST] Testing Individual Analytics Processors")
    print("=" * 50)
    
    # Test data (mock organizations with filing data)
    from src.core.data_models import OrganizationProfile, ProcessorConfig
    
    test_orgs = [
        OrganizationProfile(
            ein="541669652",
            name="FAMILY FORWARD FOUNDATION",
            state="VA",
            ntee_code="P81",
            revenue=2500000,
            assets=3200000,
            program_expense_ratio=0.85,
            filing_recency_score=0.9,
            filing_consistency_score=0.8,
            financial_health_score=0.87,
            most_recent_filing_year=2022,
            composite_score=0.85,
            filing_data={
                "filings": [
                    {
                        "tax_prd_yr": 2022,
                        "totrevenue": 2500000,
                        "totassetsend": 3200000,
                        "totfuncexpns": 2100000,
                        "totexpns": 2300000
                    },
                    {
                        "tax_prd_yr": 2021,
                        "totrevenue": 2200000,
                        "totassetsend": 2900000,
                        "totfuncexpns": 1800000,
                        "totexpns": 2000000
                    }
                ]
            }
        ),
        OrganizationProfile(
            ein="123456789",
            name="COMMUNITY HEALTH CENTER",
            state="VA",
            ntee_code="E31",
            revenue=1500000,
            assets=1800000,
            program_expense_ratio=0.75,
            filing_recency_score=0.8,
            filing_consistency_score=0.7,
            financial_health_score=0.72,
            most_recent_filing_year=2022,
            composite_score=0.72,
            filing_data={
                "filings": [
                    {
                        "tax_prd_yr": 2022,
                        "totrevenue": 1500000,
                        "totassetsend": 1800000,
                        "totfuncexpns": 1200000,
                        "totexpns": 1400000
                    }
                ]
            }
        )
    ]
    
    config = ProcessorConfig(
        workflow_id="individual_test",
        workflow_config=WorkflowConfig(
            target_ein="541669652",
            states=["VA"]
        )
    )
    
    # Test Trend Analyzer
    print("[TRENDS] Testing Trend Analyzer...")
    trend_processor = TrendAnalyzerProcessor()
    
    # Mock workflow state for testing
    class MockWorkflowState:
        def __init__(self, organizations):
            self.organizations = organizations
            
        def has_processor_succeeded(self, processor_name):
            return True
            
        def get_organizations_from_processor(self, processor_name):
            return [org.dict() for org in self.organizations]
    
    mock_state = MockWorkflowState(test_orgs)
    trend_result = await trend_processor.execute(config, mock_state)
    
    if trend_result.success:
        print("   [PASS] Trend analysis completed")
        trend_data = trend_result.data.get("trend_analysis", [])
        print(f"   [STATS] Analyzed {len(trend_data)} organizations")
    else:
        print("   [FAIL] Trend analysis failed")
        for error in trend_result.errors:
            print(f"      [ERROR] {error}")
    
    # Test Risk Assessor
    print("\n[RISK] Testing Risk Assessor...")
    risk_processor = RiskAssessorProcessor()
    
    # Update mock state with trend results
    if trend_result.success:
        trend_organizations = trend_result.data.get("organizations", [])
        mock_state = MockWorkflowState([OrganizationProfile(**org) for org in trend_organizations])
    
    risk_result = await risk_processor.execute(config, mock_state)
    
    if risk_result.success:
        print("   [PASS] Risk assessment completed")
        risk_data = risk_result.data.get("risk_assessments", [])
        print(f"   [RISK] Assessed {len(risk_data)} organizations")
    else:
        print("   [FAIL] Risk assessment failed")
        for error in risk_result.errors:
            print(f"      [ERROR] {error}")
    
    # Test Competitive Intelligence
    print("\n[COMPETITIVE] Testing Competitive Intelligence...")
    comp_processor = CompetitiveIntelligenceProcessor()
    
    # Update mock state with risk results
    if risk_result.success:
        risk_organizations = risk_result.data.get("organizations", [])
        mock_state = MockWorkflowState([OrganizationProfile(**org) for org in risk_organizations])
    
    comp_result = await comp_processor.execute(config, mock_state)
    
    if comp_result.success:
        print("   [PASS] Competitive intelligence completed")
        market_analysis = comp_result.data.get("market_analysis", {})
        competitive_insights = comp_result.data.get("competitive_insights", {})
        print(f"   [COMPETITIVE] Market analysis: {len(market_analysis)} components")
        print(f"   Strategic insights generated")
    else:
        print("   [FAIL] Competitive intelligence failed")
        for error in comp_result.errors:
            print(f"      [ERROR] {error}")
    
    return trend_result.success and risk_result.success and comp_result.success

async def main():
    """Main test function."""
    print("CATALYNX ADVANCED ANALYTICS TEST SUITE")
    print("=" * 60)
    
    # Test individual processors first
    individual_success = await test_individual_processors()
    
    if individual_success:
        print("\n[PASS] Individual processor tests passed!")
        
        # Test full pipeline
        pipeline_result = await test_analytics_pipeline()
        
        if pipeline_result and pipeline_result.success:
            print("\n[SUCCESS] ANALYTICS PIPELINE TEST COMPLETED SUCCESSFULLY!")
            print("\n[NEXT STEPS] Next Steps:")
            print("   1. Launch analytics dashboard: python -m streamlit run src/dashboard/analytics_dashboard.py")
            print("   2. Export analytics reports: python export_analytics.py")
            print("   3. Run full workflow: python main.py run-workflow --analytics")
        else:
            print("\n[FAIL] Pipeline test failed")
    else:
        print("\n[FAIL] Individual processor tests failed")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main())