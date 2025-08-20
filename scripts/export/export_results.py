#!/usr/bin/env python3
"""
Export workflow results to CSV/Excel files.
"""

import asyncio
import pandas as pd
from datetime import datetime
from src.core.workflow_engine import WorkflowEngine
from src.core.data_models import WorkflowConfig

async def export_workflow_results():
    """Run workflow and export results to CSV."""
    
    print("Running Grant Research Workflow...")
    
    # Create workflow
    engine = WorkflowEngine()
    config = WorkflowConfig(
        workflow_id=f'export_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        target_ein='541669652',
        max_results=15,
        states=['VA'],
        ntee_codes=['E21','E30','E32','E60','E86','F30','F32'],
        min_revenue=50000
    )
    
    # Execute workflow
    state = await engine.run_workflow(config)
    
    # Get final scored organizations
    if state.has_processor_succeeded('financial_scorer'):
        organizations = state.get_organizations_from_processor('financial_scorer')
        
        print(f"\nProcessing {len(organizations)} organizations...")
        
        # Convert to DataFrame
        results = []
        for org in organizations:
            row = {
                'EIN': org.get('ein'),
                'Name': org.get('name', 'N/A'),
                'State': org.get('state', 'N/A'),
                'NTEE_Code': org.get('ntee_code', 'N/A'),
                'Composite_Score': round(org.get('composite_score', 0), 3),
                'Revenue': org.get('revenue', 0),
                'Assets': org.get('assets', 0),
                'Most_Recent_Filing_Year': org.get('most_recent_filing_year', 'N/A'),
                'Score_Rank': org.get('score_rank', 'N/A')
            }
            
            # Add scoring components if available
            if 'scoring_components' in org:
                components = org['scoring_components']
                row.update({
                    'Financial_Score': round(components.get('financial_score', 0), 3),
                    'Recency_Score': round(components.get('recency_score', 0), 3),
                    'Consistency_Score': round(components.get('consistency_score', 0), 3),
                    'Program_Ratio_Score': round(components.get('program_ratio_score', 0), 3),
                    'NTEE_Score': components.get('ntee_score', 0),
                    'State_Score': components.get('state_score', 0),
                    'PF_Score': components.get('pf_score', 0)
                })
            
            results.append(row)
        
        # Create DataFrame and sort by composite score
        df = pd.DataFrame(results)
        df = df.sort_values('Composite_Score', ascending=False)
        df = df.reset_index(drop=True)
        df['Rank'] = df.index + 1
        
        # Export to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"grant_research_results_{timestamp}.csv"
        df.to_csv(csv_filename, index=False)
        
        print(f"\nResults exported to: {csv_filename}")
        print(f"Top 5 Organizations by Composite Score:")
        print("="*80)
        
        # Display top 5
        for idx, row in df.head(5).iterrows():
            print(f"{row['Rank']}. {row['Name']} (EIN: {row['EIN']})")
            print(f"   Score: {row['Composite_Score']} | State: {row['State']} | NTEE: {row['NTEE_Code']}")
            print(f"   Revenue: ${row['Revenue']:,} | Assets: ${row['Assets']:,}")
            print()
        
        return csv_filename
    else:
        print("No scoring results found!")
        return None

if __name__ == "__main__":
    asyncio.run(export_workflow_results())