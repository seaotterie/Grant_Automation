#!/usr/bin/env python3
"""
Test Intelligent Classifier for Organizations Without NTEE Codes
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append('.')

from src.processors.analysis.intelligent_classifier import IntelligentClassifier
from src.core.data_models import ProcessorConfig, WorkflowConfig

async def test_intelligent_classifier():
    """Test the intelligent classifier on unclassified organizations."""
    print("Testing Intelligent Classifier")
    print("=" * 50)
    
    # Create config
    config = ProcessorConfig(
        workflow_id="classifier_test",
        processor_name="intelligent_classifier", 
        workflow_config=WorkflowConfig(
            target_ein="541669652",
            ntee_codes=["P81", "E31", "P30", "W70"],
            state_filter="VA",
            max_results=100
        )
    )
    
    # Initialize classifier
    classifier = IntelligentClassifier()
    
    try:
        print("Running intelligent classification...")
        result = await classifier.execute(config)
        
        if result.success:
            classified_orgs = result.data.get('classified_organizations', [])
            promising_candidates = result.data.get('promising_candidates', [])
            total_unclassified = result.data.get('total_unclassified', 0)
            
            print(f"\nClassification Results:")
            print(f"Total unclassified organizations: {total_unclassified:,}")
            print(f"Promising candidates found: {len(promising_candidates):,}")
            print(f"Success rate: {len(promising_candidates)/total_unclassified*100:.1f}%")
            
            # Show category breakdown
            category_breakdown = result.metadata.get('category_breakdown', {})
            print(f"\nCategory Breakdown:")
            for category, count in sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True):
                print(f"  {category.title()}: {count}")
            
            # Show top 20 promising candidates
            print(f"\nTop 20 Promising Candidates (Score >= 0.3):")
            print("Rank | Score | Category  | EIN       | Organization Name")
            print("-" * 80)
            
            for i, org in enumerate(promising_candidates[:20]):
                score = org['composite_score']
                category = org['predicted_category']
                ein = org['ein']
                name = org['name'][:40]
                
                print(f"{i+1:4d} | {score:.3f} | {category:9s} | {ein} | {name}")
            
            # Show detailed breakdown for top 5
            print(f"\nDetailed Analysis - Top 5 Candidates:")
            for i, org in enumerate(promising_candidates[:5]):
                print(f"\n{i+1}. {org['name']} (EIN: {org['ein']})")
                print(f"   Composite Score: {org['composite_score']:.3f}")
                print(f"   Predicted Category: {org['predicted_category']}")
                print(f"   Keyword Scores: Health={org['keyword_scores']['health']:.2f}, "
                      f"Nutrition={org['keyword_scores']['nutrition']:.2f}, "
                      f"Safety={org['keyword_scores']['safety']:.2f}")
                print(f"   Financial Score: {org['financial_score']:.3f}")
                print(f"   Assets: ${org['assets']:,}" if org['assets'] else "   Assets: N/A")
                print(f"   Revenue: ${org['revenue']:,}" if org['revenue'] else "   Revenue: N/A")
                print(f"   Location: {org['city']}, {org['state']}")
            
            # Show scoring distribution
            print(f"\nScore Distribution:")
            score_ranges = [(0.8, 1.0), (0.6, 0.8), (0.4, 0.6), (0.3, 0.4), (0.2, 0.3), (0.0, 0.2)]
            for min_score, max_score in score_ranges:
                count = len([org for org in classified_orgs 
                           if min_score <= org['composite_score'] < max_score])
                print(f"  {min_score:.1f} - {max_score:.1f}: {count:,} organizations")
            
        else:
            print(f"Classification failed: {result.errors}")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_intelligent_classifier())