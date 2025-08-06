#!/usr/bin/env python3
"""
Export Intelligent Classification Results
Exports classified organizations with detailed scoring breakdown.
"""

import asyncio
import pandas as pd
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append('.')

from src.processors.analysis.intelligent_classifier import IntelligentClassifier
from src.core.data_models import ProcessorConfig, WorkflowConfig


async def export_classification_results(
    state: str = 'VA',
    min_score: float = 0.3,
    max_results: int = None,
    export_all: bool = False
):
    """
    Run intelligent classification and export results to CSV.
    
    Args:
        state: State to analyze (default: VA)
        min_score: Minimum composite score threshold (default: 0.3)
        max_results: Maximum results to export (None = all)
        export_all: Export all classified orgs, not just promising ones
    """
    
    print("Catalynx - Intelligent Classification Export")
    print("=" * 50)
    print(f"State: {state}")
    print(f"Score threshold: {min_score}")
    print()
    
    # Create configuration
    config = WorkflowConfig(
        workflow_id=f"classification_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        name="Classification Export",
        states=[state],
        max_results=50000  # Process all available
    )
    
    # Create processor config
    processor_config = ProcessorConfig(
        workflow_id=config.workflow_id,
        processor_name="intelligent_classifier",
        workflow_config=config
    )
    
    # Initialize and run classifier
    print("Running intelligent classification...")
    classifier = IntelligentClassifier()
    result = await classifier.execute(processor_config)
    
    if not result.success:
        print("FAILED: Classification failed")
        for error in result.errors:
            print(f"  Error: {error}")
        return None
    
    # Extract results
    classified_orgs = result.data.get('classified_organizations', [])
    promising_candidates = result.data.get('promising_candidates', [])
    total_unclassified = result.data.get('total_unclassified', 0)
    
    print(f"SUCCESS: Classification completed!")
    print(f"Total unclassified organizations: {total_unclassified:,}")
    print(f"Promising candidates (score >= {min_score}): {len(promising_candidates):,}")
    print()
    
    # Choose dataset to export
    if export_all:
        export_data = classified_orgs
        dataset_name = "All Classified"
    else:
        # Filter by score threshold
        export_data = [
            org for org in promising_candidates 
            if org['composite_score'] >= min_score
        ]
        dataset_name = "Promising Candidates"
    
    # Apply result limit
    if max_results and len(export_data) > max_results:
        export_data = export_data[:max_results]
        print(f"Limited to top {max_results} results")
    
    if not export_data:
        print("No organizations to export")
        return None
    
    # Convert to DataFrame
    print(f"Converting {len(export_data)} organizations to DataFrame...")
    results = []
    
    for org in export_data:
        row = {
            # Basic Information
            'EIN': org.get('ein'),
            'Name': org.get('name'),
            'City': org.get('city'),
            'State': org.get('state'),
            'ZIP': org.get('zip'),
            
            # Classification Results
            'Predicted_Category': org.get('predicted_category'),
            'Composite_Score': round(org.get('composite_score', 0), 4),
            'Classification_Confidence': round(org.get('classification_confidence', 0), 4),
            
            # NEW: Qualification Analysis
            'Primary_Qualification_Reason': org.get('primary_qualification_reason', 'Unknown'),
            'Qualification_Strength': org.get('qualification_strength', 'Unknown'),
            'Qualification_Details': '; '.join(org.get('qualification_factors', {}).get('qualification_details', [])),
            
            # Keyword Scores
            'Health_Keywords': round(org.get('keyword_scores', {}).get('health', 0), 4),
            'Nutrition_Keywords': round(org.get('keyword_scores', {}).get('nutrition', 0), 4),
            'Safety_Keywords': round(org.get('keyword_scores', {}).get('safety', 0), 4),
            'Education_Keywords': round(org.get('keyword_scores', {}).get('education', 0), 4),
            
            # Component Scores
            'Financial_Score': round(org.get('financial_score', 0), 4),
            'Geographic_Score': round(org.get('geographic_score', 0), 4),
            'Foundation_Score': round(org.get('foundation_score', 0), 4),
            'Activity_Score': round(org.get('activity_score', 0), 4),
            
            # Financial Data
            'Assets': org.get('assets'),
            'Revenue': org.get('revenue'),
            'Foundation_Code': org.get('foundation_code'),
            'Activity_Code': org.get('activity_code'),
            
            # Export Metadata
            'Export_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Classification_Version': '1.0.0'
        }
        
        results.append(row)
    
    # Create DataFrame and sort by composite score
    df = pd.DataFrame(results)
    df = df.sort_values('Composite_Score', ascending=False)
    df = df.reset_index(drop=True)
    df['Rank'] = df.index + 1
    
    # Move Rank to first column
    cols = ['Rank'] + [col for col in df.columns if col != 'Rank']
    df = df[cols]
    
    # Export to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"catalynx_intelligent_classification_{state}_{timestamp}.csv"
    df.to_csv(csv_filename, index=False)
    
    print(f"SUCCESS: Results exported to: {csv_filename}")
    print()
    
    # Summary statistics
    category_counts = df['Predicted_Category'].value_counts()
    print("Category Distribution:")
    for category, count in category_counts.items():
        percentage = count / len(df) * 100
        print(f"  {category.title()}: {count:,} ({percentage:.1f}%)")
    print()
    
    # Score distribution
    print("Score Distribution:")
    score_ranges = [(0.8, 1.0), (0.6, 0.8), (0.4, 0.6), (0.3, 0.4), (0.2, 0.3), (0.0, 0.2)]
    for min_range, max_range in score_ranges:
        count = len(df[(df['Composite_Score'] >= min_range) & (df['Composite_Score'] < max_range)])
        percentage = count / len(df) * 100 if len(df) > 0 else 0
        print(f"  {min_range:.1f} - {max_range:.1f}: {count:,} ({percentage:.1f}%)")
    print()
    
    # Display top 10
    print(f"Top 10 {dataset_name}:")
    print("Rank | Score  | Category  | EIN       | Organization Name")
    print("-" * 85)
    
    for idx, row in df.head(10).iterrows():
        name = str(row['Name'])[:45] if row['Name'] else 'N/A'
        print(f"{row['Rank']:4d} | {row['Composite_Score']:.3f} | {row['Predicted_Category']:9s} | {row['EIN']} | {name}")
    
    print()
    print(f"Full results saved to: {csv_filename}")
    
    return csv_filename


async def export_combined_results(
    state: str = 'VA',
    ntee_codes: list = None,
    classification_threshold: float = 0.5,
    max_results: int = 500
):
    """
    Export combined results from both NTEE-coded and classified organizations.
    
    Args:
        state: State to analyze
        ntee_codes: NTEE codes to include from standard workflow
        classification_threshold: Minimum score for classified organizations
        max_results: Maximum combined results
    """
    
    print("Catalynx - Combined Export (NTEE + Classified)")
    print("=" * 55)
    
    if ntee_codes is None:
        ntee_codes = ['E21', 'E30', 'E32', 'E60', 'E86', 'F30', 'F32']
    
    print(f"State: {state}")
    print(f"NTEE Codes: {', '.join(ntee_codes)}")
    print(f"Classification threshold: {classification_threshold}")
    print()
    
    # Run classification
    print("1. Running intelligent classification...")
    classification_file = await export_classification_results(
        state=state,
        min_score=classification_threshold,
        max_results=max_results//2  # Reserve half for NTEE results
    )
    
    if not classification_file:
        print("Classification export failed!")
        return None
    
    # Load classification results
    classified_df = pd.read_csv(classification_file)
    classified_df['Source'] = 'Intelligent_Classification'
    
    print(f"2. Found {len(classified_df)} classified organizations")
    
    # TODO: Add NTEE-coded organization results here
    # For now, just return classification results with source annotation
    
    # Export combined results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    combined_filename = f"catalynx_combined_results_{state}_{timestamp}.csv"
    classified_df.to_csv(combined_filename, index=False)
    
    print(f"SUCCESS: Combined results exported to: {combined_filename}")
    print(f"Total organizations: {len(classified_df):,}")
    
    return combined_filename


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Export intelligent classification results')
    parser.add_argument('--state', default='VA', help='State to analyze (default: VA)')
    parser.add_argument('--min-score', type=float, default=0.3, help='Minimum score threshold (default: 0.3)')
    parser.add_argument('--max-results', type=int, help='Maximum results to export')
    parser.add_argument('--export-all', action='store_true', help='Export all classified orgs, not just promising ones')
    parser.add_argument('--combined', action='store_true', help='Export combined NTEE + classified results')
    
    args = parser.parse_args()
    
    if args.combined:
        asyncio.run(export_combined_results(
            state=args.state,
            classification_threshold=args.min_score,
            max_results=args.max_results or 1000
        ))
    else:
        asyncio.run(export_classification_results(
            state=args.state,
            min_score=args.min_score,
            max_results=args.max_results,
            export_all=args.export_all
        ))