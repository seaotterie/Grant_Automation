#!/usr/bin/env python3
"""
Test Government Integration
Tests the complete government track: Grants.gov + USASpending.gov integration.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.data_models import WorkflowConfig, ProcessorConfig
from src.processors.data_collection.grants_gov_fetch import GrantsGovFetchProcessor
from src.processors.data_collection.usaspending_fetch import USASpendingFetchProcessor
from src.processors.analysis.government_opportunity_scorer import GovernmentOpportunityScorerProcessor
from src.core.government_models import GovernmentOpportunity
from src.auth.api_key_manager import get_api_key_manager


async def test_grants_gov_fetch():
    """Test Grants.gov API integration."""
    print("Testing Grants.gov fetch...")
    
    try:
        processor = GrantsGovFetchProcessor()
        
        # Create test configuration
        workflow_config = WorkflowConfig(
            workflow_id="test_grants_gov",
            state_filter="VA",
            max_results=10
        )
        
        config = ProcessorConfig(
            workflow_id="test_grants_gov",
            processor_name="grants_gov_fetch",
            workflow_config=workflow_config,
            processor_specific_config={
                "max_opportunities": 5,  # Small test run
                "test_mode": True  # Enable test mode
            }
        )
        
        # Execute processor
        result = await processor.run(config)
        
        print(f"Grants.gov fetch result: {result.success}")
        if result.success and result.data:
            opportunities = result.data.get("opportunities", [])
            print(f"Found {len(opportunities)} opportunities")
            
            if opportunities:
                # Show first opportunity details
                first_opp = opportunities[0]
                print(f"Sample opportunity: {first_opp.get('title', 'Unknown')}")
                print(f"Agency: {first_opp.get('agency_name', 'Unknown')}")
                print(f"Deadline: {first_opp.get('application_due_date', 'Unknown')}")
        else:
            print("No opportunities found or fetch failed")
            if result.errors:
                print(f"Errors: {result.errors}")
        
        return result
        
    except Exception as e:
        print(f"Grants.gov test failed: {e}")
        return None


async def test_usaspending_fetch():
    """Test USASpending.gov API integration."""
    print("\nTesting USASpending.gov fetch...")
    
    try:
        processor = USASpendingFetchProcessor()
        
        # Create test configuration
        workflow_config = WorkflowConfig(
            workflow_id="test_usaspending",
            state_filter="VA"
        )
        
        config = ProcessorConfig(
            workflow_id="test_usaspending",
            processor_name="usaspending_fetch",
            workflow_config=workflow_config
        )
        
        # Mock workflow state with test organization
        class MockWorkflowState:
            def __init__(self):
                self.completed_processors = ['bmf_filter']
                
            def has_processor_succeeded(self, name):
                return name == 'bmf_filter'
            
            def get_organizations_from_processor(self, name):
                # Return test organization
                return [{
                    "ein": "541669652",
                    "name": "FAMILY FORWARD FOUNDATION",
                    "state": "VA",
                    "ntee_code": "P81",
                    "revenue": 1000000
                }]
        
        workflow_state = MockWorkflowState()
        
        # Execute processor
        result = await processor.run(config, workflow_state)
        
        print(f"USASpending fetch result: {result.success}")
        if result.success and result.data:
            award_histories = result.data.get("award_histories", [])
            print(f"Found award histories for {len(award_histories)} organizations")
            
            total_awards = result.data.get("total_awards_found", 0)
            total_funding = result.data.get("total_funding_found", 0)
            print(f"Total awards found: {total_awards}")
            print(f"Total funding found: ${total_funding:,.2f}")
        else:
            print("No award data found or fetch failed")
            if result.errors:
                print(f"Errors: {result.errors}")
        
        return result
        
    except Exception as e:
        print(f"USASpending test failed: {e}")
        return None


async def test_opportunity_scoring():
    """Test government opportunity scoring."""
    print("\nTesting opportunity scoring...")
    
    try:
        processor = GovernmentOpportunityScorerProcessor()
        
        # Create test configuration
        workflow_config = WorkflowConfig(
            workflow_id="test_scoring",
            state_filter="VA"
        )
        
        config = ProcessorConfig(
            workflow_id="test_scoring",
            processor_name="government_opportunity_scorer",
            workflow_config=workflow_config
        )
        
        # Mock workflow state with test data
        class MockWorkflowState:
            def __init__(self):
                self.completed_processors = ['grants_gov_fetch', 'usaspending_fetch', 'bmf_filter']
                
            def has_processor_succeeded(self, name):
                return name in ['grants_gov_fetch', 'usaspending_fetch', 'bmf_filter']
            
            def get_processor_data(self, name):
                if name == 'grants_gov_fetch':
                    # Mock opportunity data
                    return {
                        "opportunities": [{
                            "opportunity_id": "TEST-001",
                            "opportunity_number": "TEST-001",
                            "title": "Test Health Initiative Grant",
                            "description": "Test description",
                            "agency_code": "HHS",
                            "agency_name": "Health and Human Services",
                            "status": "posted",
                            "funding_instrument_type": "grant",
                            "estimated_total_funding": 5000000,
                            "award_ceiling": 500000,
                            "award_floor": 50000,
                            "eligible_applicants": ["nonprofit"],
                            "eligible_states": ["VA"],
                            "application_due_date": "2025-03-01T00:00:00"
                        }]
                    }
                return None
            
            def get_organizations_from_processor(self, name):
                return [{
                    "ein": "541669652",
                    "name": "FAMILY FORWARD FOUNDATION",
                    "state": "VA",
                    "ntee_code": "P81",
                    "revenue": 1000000,
                    "component_scores": {
                        "award_history": {
                            "total_awards": 3,
                            "total_amount": 750000,
                            "unique_agencies": 2
                        },
                        "funding_track_record": 0.7
                    }
                }]
        
        workflow_state = MockWorkflowState()
        
        # Execute processor
        result = await processor.run(config, workflow_state)
        
        print(f"Opportunity scoring result: {result.success}")
        if result.success and result.data:
            matches = result.data.get("opportunity_matches", [])
            stats = result.data.get("match_statistics", {})
            
            print(f"Found {len(matches)} opportunity matches")
            print(f"Match statistics: {stats}")
            
            if matches:
                # Show top match
                top_match = matches[0]
                print(f"Top match score: {top_match.get('relevance_score', 0):.2f}")
                print(f"Recommendation: {top_match.get('recommendation_level', 'unknown')}")
        else:
            print("Scoring failed or no matches found")
            if result.errors:
                print(f"Errors: {result.errors}")
        
        return result
        
    except Exception as e:
        print(f"Opportunity scoring test failed: {e}")
        return None


async def test_data_models():
    """Test data model validation."""
    print("\nTesting data models...")
    
    try:
        # Test GovernmentOpportunity model
        opportunity = GovernmentOpportunity(
            opportunity_id="TEST-001",
            opportunity_number="TEST-001",
            title="Test Opportunity",
            agency_code="HHS",
            agency_name="Health and Human Services",
            status="posted",
            funding_instrument_type="grant"
        )
        
        print(f"Created opportunity: {opportunity.title}")
        print(f"Is active: {opportunity.is_active()}")
        print(f"Nonprofit eligible: {opportunity.is_eligible_for_nonprofits()}")
        
        # Test serialization
        data = opportunity.model_dump()
        reconstructed = GovernmentOpportunity(**data)
        print(f"Serialization test: {reconstructed.title == opportunity.title}")
        
        return True
        
    except Exception as e:
        print(f"Data model test failed: {e}")
        return False


def check_api_keys():
    """Check if required API keys are available."""
    print("Checking API key availability...")
    
    try:
        manager = get_api_key_manager()
        
        # Check Grants.gov API key
        grants_gov_key = manager.get_api_key("grants_gov")
        if grants_gov_key:
            print("Grants.gov API key: Available")
        else:
            print("Grants.gov API key: Not found (may use public access)")
        
        # USASpending.gov doesn't require API key
        print("USASpending.gov API key: Not required (free API)")
        
        return True
        
    except Exception as e:
        print(f"API key check failed: {e}")
        return False


async def main():
    """Run all government integration tests."""
    print("=== Government Integration Test ===\n")
    
    # Check API keys first
    check_api_keys()
    
    # Test data models
    await test_data_models()
    
    # Test API integrations
    # Note: These may fail without proper API keys or network access
    grants_result = await test_grants_gov_fetch()
    usa_result = await test_usaspending_fetch()
    scoring_result = await test_opportunity_scoring()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Grants.gov fetch: {'PASS' if grants_result and grants_result.success else 'FAIL'}")
    print(f"USASpending fetch: {'PASS' if usa_result and usa_result.success else 'FAIL'}")
    print(f"Opportunity scoring: {'PASS' if scoring_result and scoring_result.success else 'FAIL'}")
    
    print("\nGovernment integration testing complete!")


if __name__ == "__main__":
    asyncio.run(main())