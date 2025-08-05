#!/usr/bin/env python3
"""
Test Filing Data Flow
Test if ProPublica filing data is properly flowing through to the financial scorer.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.processors.data_collection.propublica_fetch import ProPublicaFetchProcessor
from src.processors.analysis.financial_scorer import FinancialScorerProcessor
from src.core.data_models import ProcessorConfig, WorkflowConfig, OrganizationProfile

async def test_filing_data_flow():
    """Test the flow of filing data from ProPublica to Financial Scorer."""
    print("TESTING FILING DATA FLOW")
    print("=" * 50)
    
    # Create test organization (simulating BMF filter output)
    test_org = OrganizationProfile(
        ein="541669652",  # We know this has filing data
        name="The Fauquier Free Clinic Inc",
        state="VA",
        ntee_code="P81",
        subsection_code="3"
    )
    print(f"Test organization: {test_org.name} (EIN: {test_org.ein})")
    
    # Step 1: Test ProPublica Fetch
    print("\nSTEP 1: Testing ProPublica Fetch")
    print("-" * 30)
    
    propublica_processor = ProPublicaFetchProcessor()
    
    # Create mock workflow state
    class MockWorkflowState:
        def has_processor_succeeded(self, processor_name):
            return True
            
        def get_organizations_from_processor(self, processor_name):
            return [test_org.dict()]
    
    config = ProcessorConfig(
        workflow_id="test_filing_flow",
        workflow_config=WorkflowConfig(target_ein="541669652")
    )
    
    mock_state = MockWorkflowState()
    pp_result = await propublica_processor.execute(config, mock_state)
    
    if pp_result.success:
        pp_organizations = pp_result.data.get("organizations", [])
        print(f"ProPublica SUCCESS: {len(pp_organizations)} organizations returned")
        
        if pp_organizations:
            org_dict = pp_organizations[0]
            print(f"Organization: {org_dict.get('name', 'Unknown')}")
            print(f"Has filing_data: {'filing_data' in org_dict}")
            
            if 'filing_data' in org_dict:
                filing_data = org_dict['filing_data']
                filings = filing_data.get('filings', [])
                print(f"Number of filings: {len(filings)}")
                
                if filings:
                    sample_filing = filings[0]
                    print("Sample filing data:")
                    print(f"  Tax year: {sample_filing.get('tax_prd_yr', 'N/A')}")
                    print(f"  Revenue: ${sample_filing.get('totrevenue', 0):,}")
                    print(f"  Assets: ${sample_filing.get('totassetsend', 0):,}")
                    print(f"  Program expenses: ${sample_filing.get('totfuncexpns', 0):,}")
                
                # Step 2: Test Financial Scorer with this data
                print("\nSTEP 2: Testing Financial Scorer")
                print("-" * 30)
                
                financial_processor = FinancialScorerProcessor()
                
                # Create mock state with ProPublica results
                class MockWorkflowStateWithPP:
                    def has_processor_succeeded(self, processor_name):
                        return True
                        
                    def get_organizations_from_processor(self, processor_name):
                        return pp_organizations
                
                mock_state_with_pp = MockWorkflowStateWithPP()
                fs_result = await financial_processor.execute(config, mock_state_with_pp)
                
                if fs_result.success:
                    fs_organizations = fs_result.data.get("organizations", [])
                    scoring_stats = fs_result.data.get("scoring_stats", {})
                    
                    print(f"Financial Scorer SUCCESS: {len(fs_organizations)} organizations scored")
                    print(f"Fully scored: {scoring_stats.get('fully_scored', 0)}")
                    print(f"Partially scored: {scoring_stats.get('partially_scored', 0)}")
                    
                    if fs_organizations:
                        scored_org = fs_organizations[0]
                        print(f"Scored organization: {scored_org.get('name', 'Unknown')}")
                        print(f"Composite score: {scored_org.get('composite_score', 'N/A')}")
                        
                        scoring_components = scored_org.get('scoring_components', {})
                        if scoring_components:
                            print("Scoring breakdown:")
                            for component, score in scoring_components.items():
                                print(f"  {component}: {score:.3f}")
                        
                        # Check if filing data is present in scored org
                        print(f"Scored org has filing_data: {'filing_data' in scored_org}")
                else:
                    print("Financial Scorer FAILED:")
                    for error in fs_result.errors:
                        print(f"  ERROR: {error}")
            else:
                print("ERROR: No filing_data found in ProPublica result")
    else:
        print("ProPublica FAILED:")
        for error in pp_result.errors:
            print(f"  ERROR: {error}")
    
    # Step 3: Direct API test for comparison
    print("\nSTEP 3: Direct API Verification")
    print("-" * 30)
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            url = f"https://projects.propublica.org/nonprofits/api/v2/organizations/541669652.json"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    api_data = await response.json()
                    api_filings = api_data.get('filings_with_data', [])
                    print(f"Direct API: {len(api_filings)} filings available")
                    
                    if api_filings:
                        recent = api_filings[0]
                        print(f"Recent filing (API): {recent.get('tax_prd_yr', 'N/A')}, Revenue: ${recent.get('totrevenue', 0):,}")
                else:
                    print(f"Direct API failed: {response.status}")
    except Exception as e:
        print(f"Direct API error: {e}")

if __name__ == "__main__":
    asyncio.run(test_filing_data_flow())