#!/usr/bin/env python3
"""
Export Government Opportunities
Comprehensive export of government funding opportunities and organizational matches.
"""

import asyncio
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import sys

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.workflow_engine import get_workflow_engine
from src.core.data_models import WorkflowConfig
from src.processors.registry import register_all_processors


async def export_government_opportunities():
    """Run multi-track workflow and export government opportunities."""
    
    print("Running Enhanced Multi-Track Workflow (Phase 2)...")
    print("Including: Organizations + Government Opportunities + Historical Awards")
    
    # Register processors
    registered_count = register_all_processors()
    print(f"Registered {registered_count} processors")
    
    # Create enhanced workflow configuration
    config = WorkflowConfig(
        workflow_id=f'government_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        name='Multi-Track Government Opportunities Export',
        target_ein='541669652',  # Example organization
        max_results=10,  # Smaller for testing
        states=['VA'],  # Single state for testing
        ntee_codes=['P81', 'E31'],  # Simplified for testing
        min_revenue=100000,
        include_classified_organizations=False  # Simplified for testing
    )
    
    print(f"Workflow ID: {config.workflow_id}")
    print(f"States: {', '.join(config.states)}")
    print(f"NTEE Codes: {', '.join(config.ntee_codes)}")
    print(f"Min Revenue: ${config.min_revenue:,}")
    
    # Execute enhanced workflow
    engine = get_workflow_engine()
    
    # Add progress tracking
    def progress_callback(workflow_id: str, progress: float, message: str):
        print(f"Progress: {progress:.1f}% - {message}")
    
    engine.add_progress_callback(progress_callback)
    
    try:
        state = await engine.run_workflow(config)
        
        if state.status.value != "completed":
            print(f"FAILED: Workflow failed with status: {state.status.value}")
            if state.errors:
                print("Errors:")
                for error in state.errors:
                    print(f"  - {error}")
            return
        
        print(f"SUCCESS: Workflow completed in {state.get_execution_time():.2f} seconds")
        print(f"Organizations processed: {state.organizations_processed}")
        
        # Export organizations
        await export_organizations(state)
        
        # Export government opportunities
        await export_opportunities(state)
        
        # Export opportunity matches
        await export_opportunity_matches(state)
        
        # Export historical awards
        await export_historical_awards(state)
        
        # Generate summary report
        await generate_summary_report(state, config)
        
        print("Multi-track export completed successfully!")
        
    except Exception as e:
        print(f"ERROR: Workflow execution failed: {e}")
        raise


async def export_organizations(state):
    """Export organization data to CSV."""
    print("\n📋 Exporting Organizations...")
    
    # Get organizations from financial scorer (most complete data)
    organizations = []
    if state.has_processor_succeeded('financial_scorer'):
        orgs_data = state.get_organizations_from_processor('financial_scorer')
        organizations.extend(orgs_data)
    
    if not organizations:
        print("⚠️  No organization data found")
        return
    
    # Convert to DataFrame
    results = []
    for org in organizations:
        row = {
            'EIN': org.get('ein'),
            'Name': org.get('name', 'N/A'),
            'State': org.get('state', 'N/A'),
            'City': org.get('city', 'N/A'),
            'NTEE_Code': org.get('ntee_code', 'N/A'),
            'Composite_Score': round(org.get('composite_score', 0), 3),
            'Revenue': org.get('revenue', 0),
            'Assets': org.get('assets', 0),
            'Expenses': org.get('expenses', 0),
            'Program_Expense_Ratio': round(org.get('program_expense_ratio', 0), 3),
            'Most_Recent_Filing_Year': org.get('most_recent_filing_year', 'N/A'),
            'Filing_Consistency_Score': round(org.get('filing_consistency_score', 0), 3),
            'Score_Rank': org.get('score_rank', 'N/A'),
            'Federal_Awards_Count': org.get('component_scores', {}).get('award_history', {}).get('total_awards', 0),
            'Federal_Awards_Total': org.get('component_scores', {}).get('award_history', {}).get('total_amount', 0),
            'Funding_Track_Record_Score': round(org.get('component_scores', {}).get('funding_track_record', 0), 3),
            'Data_Sources': '; '.join(org.get('data_sources', [])),
            'Last_Updated': org.get('last_updated', 'N/A')
        }
        results.append(row)
    
    # Create DataFrame and save
    df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"enhanced_organization_analysis_{timestamp}.csv"
    
    df.to_csv(filename, index=False)
    print(f"✅ Organizations exported to {filename}")
    print(f"📊 Total organizations: {len(results)}")


async def export_opportunities(state):
    """Export government opportunities to CSV."""
    print("\n🏛️  Exporting Government Opportunities...")
    
    if not state.has_processor_succeeded('grants_gov_fetch'):
        print("⚠️  No government opportunities data found")
        return
    
    opportunities_data = state.get_processor_data('grants_gov_fetch')
    opportunities = opportunities_data.get('opportunities', [])
    
    if not opportunities:
        print("⚠️  No opportunities found")
        return
    
    # Convert to DataFrame
    results = []
    for opp in opportunities:
        row = {
            'Opportunity_ID': opp.get('opportunity_id'),
            'Opportunity_Number': opp.get('opportunity_number'),
            'Title': opp.get('title', '').replace('\n', ' ')[:200],  # Clean title
            'Agency_Code': opp.get('agency_code'),
            'Agency_Name': opp.get('agency_name'),
            'Status': opp.get('status'),
            'Funding_Instrument': opp.get('funding_instrument_type'),
            'Estimated_Total_Funding': opp.get('estimated_total_funding', 0),
            'Award_Ceiling': opp.get('award_ceiling', 0),
            'Award_Floor': opp.get('award_floor', 0),
            'Expected_Awards': opp.get('expected_number_of_awards', 0),
            'Posted_Date': opp.get('posted_date', ''),
            'Application_Due_Date': opp.get('application_due_date', ''),
            'Days_Until_Deadline': '',  # Will calculate
            'Eligible_Applicants': ', '.join(opp.get('eligible_applicants', [])),
            'Eligible_States': ', '.join(opp.get('eligible_states', [])) if opp.get('eligible_states') else 'All States',
            'CFDA_Numbers': ', '.join(opp.get('cfda_numbers', [])),
            'Relevance_Score': round(opp.get('relevance_score', 0), 3),
            'Match_Reasons': '; '.join(opp.get('match_reasons', [])),
            'Grants_Gov_URL': opp.get('grants_gov_url', ''),
            'Retrieved_At': opp.get('retrieved_at', '')
        }
        
        # Calculate days until deadline
        if opp.get('application_due_date'):
            try:
                due_date = pd.to_datetime(opp['application_due_date'])
                days_left = (due_date - pd.Timestamp.now()).days
                row['Days_Until_Deadline'] = max(0, days_left)
            except:
                row['Days_Until_Deadline'] = 'Unknown'
        
        results.append(row)
    
    # Create DataFrame and save
    df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"federal_grant_opportunities_{timestamp}.csv"
    
    df.to_csv(filename, index=False)
    print(f"✅ Opportunities exported to {filename}")
    print(f"🎯 Total opportunities: {len(results)}")
    print(f"📅 Active opportunities: {len([r for r in results if r['Status'] == 'posted'])}")


async def export_opportunity_matches(state):
    """Export organization-opportunity matches to CSV."""
    print("\n🎯 Exporting Opportunity Matches...")
    
    if not state.has_processor_succeeded('government_opportunity_scorer'):
        print("⚠️  No opportunity matches data found")
        return
    
    matches_data = state.get_processor_data('government_opportunity_scorer')
    matches = matches_data.get('opportunity_matches', [])
    
    if not matches:
        print("⚠️  No opportunity matches found")
        return
    
    # Convert to DataFrame
    results = []
    for match in matches:
        opp = match.get('opportunity', {})
        row = {
            'Organization_EIN': match.get('organization'),
            'Opportunity_ID': opp.get('opportunity_id'),
            'Opportunity_Title': opp.get('title', '').replace('\n', ' ')[:150],
            'Agency_Name': opp.get('agency_name'),
            'Award_Ceiling': opp.get('award_ceiling', 0),
            'Application_Due_Date': opp.get('application_due_date', ''),
            'Overall_Relevance_Score': round(match.get('relevance_score', 0), 3),
            'Eligibility_Score': round(match.get('eligibility_score', 0), 3),
            'Geographic_Score': round(match.get('geographic_score', 0), 3),
            'Timing_Score': round(match.get('timing_score', 0), 3),
            'Financial_Fit_Score': round(match.get('financial_fit_score', 0), 3),
            'Historical_Success_Score': round(match.get('historical_success_score', 0), 3),
            'Recommendation_Level': match.get('recommendation_level'),
            'Competition_Assessment': match.get('competition_assessment'),
            'Preparation_Time_Days': match.get('preparation_time_needed', ''),
            'Action_Items': '; '.join(match.get('action_items', [])),
            'Match_Reasons': '; '.join(opp.get('match_reasons', [])),
            'Match_Date': match.get('match_date', '')
        }
        results.append(row)
    
    # Sort by relevance score
    results.sort(key=lambda x: x['Overall_Relevance_Score'], reverse=True)
    
    # Create DataFrame and save
    df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"opportunity_matches_{timestamp}.csv"
    
    df.to_csv(filename, index=False)
    print(f"✅ Opportunity matches exported to {filename}")
    print(f"🎯 Total matches: {len(results)}")
    
    # Show top matches
    high_matches = len([r for r in results if r['Recommendation_Level'] == 'high'])
    medium_matches = len([r for r in results if r['Recommendation_Level'] == 'medium'])
    print(f"🔥 High priority matches: {high_matches}")
    print(f"⚡ Medium priority matches: {medium_matches}")


async def export_historical_awards(state):
    """Export historical federal awards data."""
    print("\n🏆 Exporting Historical Awards...")
    
    if not state.has_processor_succeeded('usaspending_fetch'):
        print("⚠️  No historical awards data found")
        return
    
    awards_data = state.get_processor_data('usaspending_fetch')
    award_histories = awards_data.get('award_histories', [])
    
    if not award_histories:
        print("⚠️  No historical awards found")
        return
    
    # Flatten award histories into individual awards
    results = []
    for history in award_histories:
        org_ein = history.get('ein')
        org_name = history.get('name')
        awards = history.get('awards', [])
        
        for award in awards:
            row = {
                'Organization_EIN': org_ein,
                'Organization_Name': org_name,
                'Award_ID': award.get('award_id'),
                'Award_Title': award.get('award_title', 'N/A'),
                'Award_Amount': award.get('award_amount', 0),
                'Award_Type': award.get('award_type'),
                'Start_Date': award.get('start_date', ''),
                'End_Date': award.get('end_date', ''),
                'Action_Date': award.get('action_date', ''),
                'Awarding_Agency': award.get('awarding_agency_name'),
                'Awarding_Sub_Agency': award.get('awarding_sub_agency', ''),
                'CFDA_Number': award.get('cfda_number', ''),
                'CFDA_Title': award.get('cfda_title', ''),
                'Source': award.get('source')
            }
            results.append(row)
    
    if results:
        # Create DataFrame and save
        df = pd.DataFrame(results)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"historical_federal_awards_{timestamp}.csv"
        
        df.to_csv(filename, index=False)
        print(f"✅ Historical awards exported to {filename}")
        print(f"🏆 Total awards: {len(results)}")
        print(f"💰 Total funding: ${sum(r['Award_Amount'] for r in results):,.2f}")
    else:
        print("⚠️  No awards to export")


async def generate_summary_report(state, config):
    """Generate comprehensive summary report."""
    print("\n📄 Generating Summary Report...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Collect summary statistics
    summary = {
        'workflow_info': {
            'workflow_id': config.workflow_id,
            'execution_time': state.get_execution_time(),
            'status': state.status.value,
            'generated_at': datetime.now().isoformat()
        },
        'configuration': {
            'states': config.states,
            'ntee_codes': config.ntee_codes,
            'min_revenue': config.min_revenue,
            'max_results': config.max_results,
            'include_classified': config.include_classified_organizations
        },
        'processing_results': {
            'organizations_found': state.organizations_found,
            'organizations_processed': state.organizations_processed,
            'completed_processors': len(state.completed_processors),
            'failed_processors': len(state.failed_processors)
        }
    }
    
    # Add processor-specific results
    processor_results = {}
    for processor_name, result in state.processor_results.items():
        if result.success and result.data:
            processor_results[processor_name] = {
                'success': result.success,
                'execution_time': result.execution_time,
                'data_summary': {k: len(v) if isinstance(v, list) else str(v)[:100] 
                               for k, v in result.data.items() if k != 'organizations'}
            }
    
    summary['processor_results'] = processor_results
    
    # Save summary as JSON
    summary_filename = f"workflow_summary_{timestamp}.json"
    with open(summary_filename, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"✅ Summary report saved to {summary_filename}")
    
    # Create human-readable summary
    txt_filename = f"workflow_summary_{timestamp}.txt"
    with open(txt_filename, 'w') as f:
        f.write("=== CATALYNX MULTI-TRACK WORKFLOW SUMMARY ===\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Workflow ID: {config.workflow_id}\n")
        f.write(f"Execution Time: {state.get_execution_time():.2f} seconds\n")
        f.write(f"Status: {state.status.value.upper()}\n\n")
        
        f.write("CONFIGURATION:\n")
        f.write(f"- States: {', '.join(config.states)}\n")
        f.write(f"- NTEE Codes: {', '.join(config.ntee_codes)}\n")
        f.write(f"- Min Revenue: ${config.min_revenue:,}\n")
        f.write(f"- Max Results: {config.max_results}\n\n")
        
        f.write("PROCESSING RESULTS:\n")
        f.write(f"- Organizations Found: {state.organizations_found}\n")
        f.write(f"- Organizations Processed: {state.organizations_processed}\n")
        f.write(f"- Processors Completed: {len(state.completed_processors)}\n")
        f.write(f"- Processors Failed: {len(state.failed_processors)}\n\n")
        
        f.write("COMPLETED PROCESSORS:\n")
        for proc in state.completed_processors:
            f.write(f"- ✅ {proc}\n")
        
        if state.failed_processors:
            f.write("\nFAILED PROCESSORS:\n")
            for proc in state.failed_processors:
                f.write(f"- ❌ {proc}\n")
    
    print(f"✅ Human-readable summary saved to {txt_filename}")


if __name__ == "__main__":
    asyncio.run(export_government_opportunities())