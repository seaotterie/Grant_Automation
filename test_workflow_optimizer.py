#!/usr/bin/env python3
"""
Test script for the Workflow Optimizer
Demonstrates advanced workflow optimization and filtering capabilities.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.web.services.workflow_optimizer import get_workflow_optimizer, FilterSet, WorkflowStage


async def main():
    """Run comprehensive workflow optimization tests."""
    print("Starting Workflow Optimization Analysis")
    print("=" * 60)
    
    # Initialize optimizer
    optimizer = get_workflow_optimizer()
    
    # Test profile (using an existing profile from the system)
    test_profile_id = "f3adef3b653c"  # Heros Bridge profile
    
    try:
        print(f"Testing with profile: {test_profile_id}")
        print("-" * 40)
        
        # Test 1: Workflow Analytics
        print("\n1. WORKFLOW ANALYTICS")
        print("-" * 30)
        analytics = await optimizer.get_workflow_analytics(test_profile_id)
        
        if analytics:
            print(f"Total Entities: {analytics['performance_metrics']['total_entities']}")
            print("Stage Distribution:")
            for stage, count in analytics['stage_distribution'].items():
                print(f"  {stage.replace('_', ' ').title()}: {count}")
            
            print("\nConversion Rates:")
            for transition, rate in analytics['performance_metrics']['conversion_rates'].items():
                print(f"  {transition.replace('_', ' ').title()}: {rate:.1%}")
            
            print("\nTop Optimization Opportunities:")
            for i, opp in enumerate(analytics['optimization_opportunities'][:3], 1):
                print(f"  {i}. {opp['description']} (Impact: {opp['impact_score']:.1f})")
        else:
            print("No analytics data available")
        
        # Test 2: Workflow Optimization
        print("\n\n2. WORKFLOW OPTIMIZATION RECOMMENDATIONS")
        print("-" * 40)
        optimizations = await optimizer.optimize_workflow(test_profile_id)
        
        if optimizations:
            for i, opt in enumerate(optimizations[:5], 1):
                print(f"\n{i}. {opt.optimization_type.upper()}")
                print(f"   Stage: {opt.stage.value.replace('_', ' ').title()}")
                print(f"   Description: {opt.description}")
                print(f"   Impact Score: {opt.impact_score:.1f}")
                print(f"   Effort: {opt.implementation_effort}")
                print(f"   Time Savings: {opt.estimated_time_savings}")
        else:
            print("No optimization opportunities found")
        
        # Test 3: Advanced Search
        print("\n\n3. ADVANCED SEARCH CAPABILITIES")
        print("-" * 40)
        
        # Test search with filters
        search_filters = FilterSet(
            revenue_min=100000,  # Organizations with revenue > $100k
            states=["VA"],       # Virginia organizations
            min_match_score=0.5  # Match score > 50%
        )
        
        print("Searching for 'health' with filters:")
        print(f"  - Revenue > $100,000")
        print(f"  - Located in Virginia") 
        print(f"  - Match score > 50%")
        
        search_results = await optimizer.advanced_search(
            query="health",
            filters=search_filters,
            profile_id=test_profile_id,
            limit=10
        )
        
        print(f"\nFound {len(search_results)} results:")
        for i, result in enumerate(search_results[:5], 1):
            print(f"\n{i}. {result.entity_data.get('name', result.entity_id)}")
            print(f"   Type: {result.entity_type}")
            print(f"   Relevance: {result.relevance_score:.1%}")
            print(f"   Stage: {result.stage.value.replace('_', ' ').title()}")
            print(f"   Reasons: {', '.join(result.match_reasons[:2])}")
        
        # Test 4: Batch Processing Recommendations
        print("\n\n4. BATCH PROCESSING RECOMMENDATIONS")
        print("-" * 40)
        batch_recommendations = await optimizer.batch_process_recommendations(test_profile_id)
        
        if batch_recommendations['batch_opportunities']:
            print(f"Total Time Savings: {batch_recommendations['estimated_time_savings']:.0f} minutes")
            print("\nBatch Opportunities:")
            
            for opp in batch_recommendations['batch_opportunities']:
                print(f"\n  Stage: {opp['stage'].replace('_', ' ').title()}")
                print(f"  Entities: {opp['entity_count']}")
                print(f"  Batch Size: {opp['batch_size']}")
                print(f"  Time Savings: {opp['estimated_time_savings']:.0f} minutes")
                print(f"  Priority: {opp['priority']:.2f}")
            
            print(f"\nOptimal Processing Order: {', '.join(batch_recommendations['processing_order'])}")
        else:
            print("No batch processing opportunities found")
        
        # Test 5: Different Search Scenarios
        print("\n\n5. SEARCH SCENARIO TESTING")
        print("-" * 40)
        
        scenarios = [
            ("education", FilterSet(ntee_codes=["B"]), "Education organizations"),
            ("funding", FilterSet(deadline_within_days=30), "Opportunities with deadlines within 30 days"),
            ("", FilterSet(revenue_min=500000), "Large organizations (>$500k revenue)")
        ]
        
        for query, filters, description in scenarios:
            print(f"\nScenario: {description}")
            results = await optimizer.advanced_search(query, filters, test_profile_id, limit=3)
            print(f"Results: {len(results)} found")
            
            for result in results[:1]:  # Show top result
                name = result.entity_data.get('name', result.entity_id)[:50]
                print(f"  Top: {name} (Relevance: {result.relevance_score:.1%})")
        
        # Summary
        print("\n" + "=" * 60)
        print("WORKFLOW OPTIMIZATION SUMMARY")
        print("-" * 40)
        
        total_optimizations = len(optimizations) if optimizations else 0
        total_search_results = len(search_results)
        total_batch_savings = batch_recommendations['estimated_time_savings'] if batch_recommendations else 0
        
        print(f"Optimization Opportunities Found: {total_optimizations}")
        print(f"Search Results Demonstrated: {total_search_results}")
        print(f"Potential Time Savings: {total_batch_savings:.0f} minutes")
        
        if total_optimizations > 0:
            print("\nRecommendation: Review and implement top optimization opportunities")
        if total_batch_savings > 30:
            print("Recommendation: Consider batch processing for efficiency gains")
        if total_search_results > 0:
            print("Recommendation: Use advanced search to quickly find relevant entities")
        
        print("\nWorkflow optimization analysis complete!")
        
        # Save detailed results
        output_file = Path("workflow_optimization_report.json")
        report_data = {
            "profile_id": test_profile_id,
            "generated_at": analytics.get('generated_at') if analytics else None,
            "analytics": analytics,
            "optimizations": [
                {
                    "stage": opt.stage.value,
                    "type": opt.optimization_type,
                    "description": opt.description,
                    "impact_score": opt.impact_score,
                    "effort": opt.implementation_effort,
                    "time_savings": opt.estimated_time_savings
                } for opt in optimizations
            ] if optimizations else [],
            "batch_recommendations": batch_recommendations,
            "search_demo_results": len(search_results)
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\nDetailed report saved to: {output_file}")
        
    except Exception as e:
        print(f"Error during workflow optimization: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())