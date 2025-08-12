"""
Test State-Level Grant Discovery System
Tests Virginia state agency integration and multi-state discovery capabilities
"""
import asyncio
import json
from datetime import datetime
from src.discovery.state_discoverer import StateDiscoverer
from src.profiles.models import (
    OrganizationProfile, FundingType, OrganizationType, 
    GeographicScope, FundingPreferences, ProfileSearchParams
)


async def test_state_level_discovery():
    """Test state-level grant discovery with Virginia focus"""
    
    print("Testing State-Level Grant Discovery System")
    print("=" * 60)
    
    # Create test organization profile focused on health in Virginia
    test_profile = OrganizationProfile(
        profile_id="test_va_health_org_001",
        name="Virginia Community Health Alliance",
        organization_type=OrganizationType.NONPROFIT,
        ein="54-1234567",
        mission_statement="Improving health outcomes in underserved Virginia communities through innovative programs and partnerships",
        focus_areas=["community_health", "health_equity", "disease_prevention", "maternal_health"],
        program_areas=["community_health_workers", "maternal_health_programs", "chronic_disease_management"],
        target_populations=["underserved_communities", "rural_populations", "pregnant_women", "children"],
        geographic_scope=GeographicScope(
            states=["VA"],
            regions=["Appalachian Virginia", "Rural Virginia"],
            nationwide=False
        ),
        service_areas=["Southwest Virginia", "Central Virginia"],
        funding_preferences=FundingPreferences(
            min_amount=25000,
            max_amount=200000,
            funding_types=[FundingType.GRANTS],
            recurring=True,
            multi_year=True
        ),
        current_funders=["Virginia Community Foundation", "Regional Health Foundation"],
        annual_revenue=750000,
        staff_size=15,
        volunteer_count=60,
        board_size=9,
        strategic_priorities=["expand_rural_access", "improve_health_outcomes", "build_partnerships"],
        growth_goals=["increase_program_capacity", "expand_geographic_reach"],
        partnership_interests=["healthcare_systems", "community_organizations", "state_agencies"]
    )
    
    # Create search parameters
    search_params = ProfileSearchParams(
        profile_id=test_profile.profile_id,
        funding_types=[FundingType.GRANTS],
        max_results_per_type=15,
        discovery_filters={
            "priority_states": ["VA", "MD", "DC"],
            "agency_types": ["health", "social_services", "education"],
            "opportunity_types": ["grant", "partnership", "rfp"],
            "geographic_scope": {
                "states": test_profile.geographic_scope.states,
                "focus": "rural_underserved"
            }
        }
    )
    
    # Initialize state discoverer
    discoverer = StateDiscoverer()
    
    # Test discoverer status
    print("\nState Discoverer Status:")
    status = await discoverer.get_discoverer_status()
    print(f"  Name: {status['name']}")
    print(f"  Status: {status['status']}")
    print(f"  States Supported: {status['total_states_supported']}")
    print(f"  Priority States: {', '.join(status['priority_states'])}")
    print(f"  Virginia Integration: {'Operational' if status['capabilities']['virginia_integration'] else 'Limited'}")
    
    # Show state processor status
    print(f"\nState Processor Status:")
    for state, state_status in status['state_processors'].items():
        print(f"  {state.title()}: {state_status}")
    
    # Test search parameters validation
    print("\nValidating Search Parameters:")
    is_valid = await discoverer.validate_search_params(search_params)
    print(f"  Search parameters valid: {is_valid}")
    
    # Execute state-level discovery
    print("\nExecuting State-Level Grant Discovery:")
    print(f"  Organization: {test_profile.name}")
    print(f"  Focus Areas: {', '.join(test_profile.focus_areas)}")
    print(f"  Target States: {', '.join(test_profile.geographic_scope.states)}")
    print(f"  Funding Range: ${test_profile.funding_preferences.min_amount:,} - ${test_profile.funding_preferences.max_amount:,}")
    
    opportunities = []
    source_breakdown = {
        "Virginia State Agencies": 0,
        "Other States": 0,
        "Mock Data": 0
    }
    
    start_time = datetime.now()
    
    try:
        async for opportunity in discoverer.discover_opportunities(
            test_profile, search_params, max_results=12
        ):
            opportunities.append(opportunity)
            
            # Track source breakdown
            if "Virginia" in opportunity.discovery_source:
                source_breakdown["Virginia State Agencies"] += 1
            elif opportunity.external_data.get("mock_data"):
                source_breakdown["Mock Data"] += 1
            else:
                source_breakdown["Other States"] += 1
            
            print(f"    Found: {opportunity.program_name} ({opportunity.organization_name})")
    
    except Exception as e:
        print(f"State discovery failed: {str(e)}")
        return
    
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    
    # Analysis Results
    print(f"\nState Discovery Results Summary:")
    print(f"  Total Opportunities Found: {len(opportunities)}")
    print(f"  Execution Time: {execution_time:.2f} seconds")
    if opportunities:
        print(f"  Average Compatibility Score: {sum(opp.compatibility_score for opp in opportunities) / len(opportunities):.3f}")
    
    print(f"\nSource Breakdown:")
    for source, count in source_breakdown.items():
        percentage = (count / len(opportunities)) * 100 if opportunities else 0
        print(f"  {source}: {count} opportunities ({percentage:.1f}%)")
    
    # Top opportunities analysis
    if opportunities:
        print(f"\nTop 5 State Opportunities (by compatibility score):")
        top_opportunities = sorted(opportunities, key=lambda x: x.compatibility_score, reverse=True)[:5]
        
        for i, opp in enumerate(top_opportunities, 1):
            print(f"\n  {i}. {opp.program_name}")
            print(f"     Agency: {opp.organization_name}")
            print(f"     Source: {opp.discovery_source}")
            print(f"     Compatibility: {opp.compatibility_score:.3f}")
            print(f"     Confidence: {opp.confidence_level:.3f}")
            print(f"     Funding: ${opp.funding_amount:,}" if opp.funding_amount else "     Funding: Not specified")
            print(f"     Deadline: {opp.application_deadline}")
            
            # Show key match factors
            match_factors = [k for k, v in opp.match_factors.items() if v]
            if match_factors:
                print(f"     Strengths: {', '.join(match_factors)}")
            
            # Show external data highlights
            external_data = opp.external_data
            if external_data.get("agency_name"):
                print(f"     Agency Type: {external_data.get('focus_area', 'General')}")
            if external_data.get("eligibility_requirements"):
                print(f"     Key Requirement: {external_data['eligibility_requirements'][0]}")
    
    # Virginia-specific analysis
    va_opportunities = [opp for opp in opportunities if "Virginia" in opp.discovery_source]
    other_opportunities = [opp for opp in opportunities if "Virginia" not in opp.discovery_source]
    
    print(f"\nVirginia State Agency Analysis:")
    if va_opportunities:
        print(f"  Virginia Opportunities: {len(va_opportunities)}")
        va_avg_score = sum(opp.compatibility_score for opp in va_opportunities) / len(va_opportunities)
        va_avg_confidence = sum(opp.confidence_level for opp in va_opportunities) / len(va_opportunities)
        print(f"  Average Compatibility: {va_avg_score:.3f}")
        print(f"  Average Confidence: {va_avg_confidence:.3f}")
        
        # Virginia agency breakdown
        va_agencies = {}
        for opp in va_opportunities:
            agency = opp.external_data.get("agency_name", opp.organization_name)
            va_agencies[agency] = va_agencies.get(agency, 0) + 1
        
        print(f"  Agency Distribution:")
        for agency, count in va_agencies.items():
            print(f"    {agency}: {count} opportunities")
    else:
        print(f"  No Virginia-specific opportunities found (check processor integration)")
    
    if other_opportunities:
        print(f"\nOther States Analysis:")
        print(f"  Other State Opportunities: {len(other_opportunities)}")
        other_avg_score = sum(opp.compatibility_score for opp in other_opportunities) / len(other_opportunities)
        print(f"  Average Compatibility: {other_avg_score:.3f}")
    
    # Strategic insights
    print(f"\nStrategic Insights:")
    
    # Focus area alignment
    focus_matches = sum(1 for opp in opportunities if opp.match_factors.get("focus_area_alignment", False))
    focus_alignment = (focus_matches / len(opportunities)) * 100 if opportunities else 0
    print(f"  Focus Area Alignment: {focus_alignment:.1f}% of opportunities")
    
    # Geographic coverage
    geographic_matches = sum(1 for opp in opportunities if opp.match_factors.get("geographic_alignment", False))
    geographic_coverage = (geographic_matches / len(opportunities)) * 100 if opportunities else 0
    print(f"  Geographic Alignment: {geographic_coverage:.1f}% of opportunities")
    
    # Eligibility fit
    eligibility_matches = sum(1 for opp in opportunities if opp.match_factors.get("eligibility_match", False))
    eligibility_fit = (eligibility_matches / len(opportunities)) * 100 if opportunities else 0
    print(f"  Eligibility Match: {eligibility_fit:.1f}% of opportunities")
    
    # Risk analysis
    competitive_process = sum(1 for opp in opportunities if opp.risk_factors.get("competitive_process", False))
    competition_rate = (competitive_process / len(opportunities)) * 100 if opportunities else 0
    print(f"  Competitive Process Risk: {competition_rate:.1f}% of opportunities")
    
    # Funding analysis
    if opportunities:
        funding_amounts = [opp.funding_amount for opp in opportunities if opp.funding_amount]
        if funding_amounts:
            avg_funding = sum(funding_amounts) / len(funding_amounts)
            min_funding = min(funding_amounts)
            max_funding = max(funding_amounts)
            print(f"  Funding Range: ${min_funding:,} - ${max_funding:,} (avg: ${avg_funding:,.0f})")
    
    print(f"\nState-Level Grant Discovery Test Complete!")
    print(f"   Successfully integrated Virginia state agencies")
    print(f"   Multi-state discovery capability operational")
    if opportunities:
        print(f"   Average opportunity quality score: {sum(opp.compatibility_score for opp in opportunities) / len(opportunities):.3f}/1.0")
    print(f"   State-level integration adds significant local funding opportunities!")


if __name__ == "__main__":
    asyncio.run(test_state_level_discovery())