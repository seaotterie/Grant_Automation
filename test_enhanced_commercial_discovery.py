"""
Test Enhanced Commercial Discovery System
Tests Foundation Directory integration and CSR analysis capabilities
"""
import asyncio
import json
from datetime import datetime
from src.discovery.commercial_discoverer import CommercialDiscoverer
from src.profiles.models import (
    OrganizationProfile, FundingType, OrganizationType, 
    GeographicScope, FundingPreferences, ProfileSearchParams
)


async def test_enhanced_commercial_discovery():
    """Test enhanced commercial discovery with multiple data sources"""
    
    print("Testing Enhanced Commercial Discovery System")
    print("=" * 60)
    
    # Create test organization profile
    test_profile = OrganizationProfile(
        profile_id="test_health_org_001",
        name="Community Health Innovations",
        organization_type=OrganizationType.NONPROFIT,
        ein="12-3456789",
        mission_statement="Improving community health outcomes through innovative programs and partnerships",
        focus_areas=["health", "community_wellness", "disease_prevention", "health_equity"],
        program_areas=["community_health_workers", "health_education", "chronic_disease_management"],
        target_populations=["underserved_communities", "low_income_families", "seniors"],
        geographic_scope=GeographicScope(
            states=["VA", "MD", "DC"],
            regions=["Mid-Atlantic"],
            nationwide=False
        ),
        service_areas=["Northern Virginia", "Washington DC Metro"],
        funding_preferences=FundingPreferences(
            min_amount=50000,
            max_amount=300000,
            funding_types=[FundingType.COMMERCIAL, FundingType.GRANTS],
            recurring=True,
            multi_year=True
        ),
        current_funders=["Local Community Foundation", "United Way"],
        annual_revenue=500000,
        staff_size=12,
        volunteer_count=45,
        board_size=8,
        strategic_priorities=["expand_services", "build_partnerships", "enhance_technology"],
        growth_goals=["increase_program_reach", "diversify_funding"],
        partnership_interests=["corporate_partnerships", "healthcare_systems", "technology_companies"]
    )
    
    # Create search parameters
    search_params = ProfileSearchParams(
        profile_id=test_profile.profile_id,
        funding_types=[FundingType.COMMERCIAL],
        max_results_per_type=20,
        discovery_filters={
            "industries": ["healthcare", "technology", "financial_services"],
            "company_sizes": ["large_corp", "fortune_500"],
            "csr_focus_areas": test_profile.focus_areas,
            "funding_range": {
                "min_amount": test_profile.funding_preferences.min_amount,
                "max_amount": test_profile.funding_preferences.max_amount
            },
            "geographic_presence": {
                "states": test_profile.geographic_scope.states,
                "regions": test_profile.geographic_scope.regions
            }
        }
    )
    
    # Initialize commercial discoverer
    discoverer = CommercialDiscoverer()
    
    # Test discoverer status
    print("\nDiscoverer Status:")
    status = await discoverer.get_discoverer_status()
    print(f"  Name: {status['name']}")
    print(f"  Status: {status['status']}")
    print(f"  Data Sources: {status['data_sources']['total_sources']}")
    print(f"  Foundation Directory: {status['data_sources']['foundation_directory_api']}")
    print(f"  CSR Analysis: {status['data_sources']['csr_analysis_engine']}")
    print(f"  Enhanced Database: {status['data_sources']['enhanced_corporate_database']}")
    
    # Test search parameters validation
    print("\nValidating Search Parameters:")
    is_valid = await discoverer.validate_search_params(search_params)
    print(f"  Search parameters valid: {is_valid}")
    
    if not is_valid:
        print("Invalid search parameters, aborting test")
        return
    
    # Execute discovery
    print("\nExecuting Enhanced Commercial Discovery:")
    print(f"  Organization: {test_profile.name}")
    print(f"  Focus Areas: {', '.join(test_profile.focus_areas)}")
    print(f"  Geographic Scope: {', '.join(test_profile.geographic_scope.states)}")
    print(f"  Funding Range: ${test_profile.funding_preferences.min_amount:,} - ${test_profile.funding_preferences.max_amount:,}")
    
    opportunities = []
    source_breakdown = {
        "Foundation Directory": 0,
        "CSR Analysis": 0,
        "Enhanced Database": 0
    }
    
    start_time = datetime.now()
    
    try:
        async for opportunity in discoverer.discover_opportunities(
            test_profile, search_params, max_results=15
        ):
            opportunities.append(opportunity)
            
            # Track source breakdown
            if "Foundation Directory" in opportunity.discovery_source:
                source_breakdown["Foundation Directory"] += 1
            elif "CSR Analysis" in opportunity.discovery_source:
                source_breakdown["CSR Analysis"] += 1
            else:
                source_breakdown["Enhanced Database"] += 1
            
            print(f"    Found: {opportunity.program_name} ({opportunity.organization_name})")
    
    except Exception as e:
        print(f"Discovery failed: {str(e)}")
        return
    
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    
    # Analysis Results
    print(f"\nDiscovery Results Summary:")
    print(f"  Total Opportunities Found: {len(opportunities)}")
    print(f"  Execution Time: {execution_time:.2f} seconds")
    print(f"  Average Compatibility Score: {sum(opp.compatibility_score for opp in opportunities) / len(opportunities):.3f}")
    
    print(f"\nSource Breakdown:")
    for source, count in source_breakdown.items():
        percentage = (count / len(opportunities)) * 100 if opportunities else 0
        print(f"  {source}: {count} opportunities ({percentage:.1f}%)")
    
    # Top opportunities analysis
    if opportunities:
        print(f"\nTop 5 Opportunities (by compatibility score):")
        top_opportunities = sorted(opportunities, key=lambda x: x.compatibility_score, reverse=True)[:5]
        
        for i, opp in enumerate(top_opportunities, 1):
            print(f"\n  {i}. {opp.program_name}")
            print(f"     Organization: {opp.organization_name}")
            print(f"     Source: {opp.discovery_source}")
            print(f"     Compatibility: {opp.compatibility_score:.3f}")
            print(f"     Confidence: {opp.confidence_level:.3f}")
            print(f"     Funding: ${opp.funding_amount:,}" if opp.funding_amount else "     Funding: Not specified")
            print(f"     Deadline: {opp.application_deadline}")
            
            # Show key match factors
            match_factors = [k for k, v in opp.match_factors.items() if v]
            if match_factors:
                print(f"     Strengths: {', '.join(match_factors)}")
            
            # Show risk factors
            risk_factors = [k for k, v in opp.risk_factors.items() if v]
            if risk_factors:
                print(f"     Risks: {', '.join(risk_factors)}")
    
    # Data source performance analysis
    print(f"\nData Source Performance:")
    
    foundation_opps = [opp for opp in opportunities if "Foundation Directory" in opp.discovery_source]
    csr_opps = [opp for opp in opportunities if "CSR Analysis" in opp.discovery_source]
    database_opps = [opp for opp in opportunities if "Foundation Directory" not in opp.discovery_source and "CSR Analysis" not in opp.discovery_source]
    
    if foundation_opps:
        avg_foundation_score = sum(opp.compatibility_score for opp in foundation_opps) / len(foundation_opps)
        avg_foundation_confidence = sum(opp.confidence_level for opp in foundation_opps) / len(foundation_opps)
        print(f"  Foundation Directory - Avg Compatibility: {avg_foundation_score:.3f}, Confidence: {avg_foundation_confidence:.3f}")
    
    if csr_opps:
        avg_csr_score = sum(opp.compatibility_score for opp in csr_opps) / len(csr_opps)
        avg_csr_confidence = sum(opp.confidence_level for opp in csr_opps) / len(csr_opps)
        print(f"  CSR Analysis - Avg Compatibility: {avg_csr_score:.3f}, Confidence: {avg_csr_confidence:.3f}")
    
    if database_opps:
        avg_database_score = sum(opp.compatibility_score for opp in database_opps) / len(database_opps)
        avg_database_confidence = sum(opp.confidence_level for opp in database_opps) / len(database_opps)
        print(f"  Enhanced Database - Avg Compatibility: {avg_database_score:.3f}, Confidence: {avg_database_confidence:.3f}")
    
    # Strategic insights
    print(f"\nStrategic Insights:")
    
    # Geographic coverage
    geographic_matches = sum(1 for opp in opportunities if opp.match_factors.get("geographic_alignment", False))
    geographic_coverage = (geographic_matches / len(opportunities)) * 100 if opportunities else 0
    print(f"  Geographic Alignment: {geographic_coverage:.1f}% of opportunities")
    
    # Focus area alignment
    focus_matches = sum(1 for opp in opportunities if opp.match_factors.get("focus_area_alignment", False))
    focus_alignment = (focus_matches / len(opportunities)) * 100 if opportunities else 0
    print(f"  Focus Area Alignment: {focus_alignment:.1f}% of opportunities")
    
    # Funding fit
    funding_matches = sum(1 for opp in opportunities if opp.match_factors.get("funding_range_fit", False))
    funding_fit = (funding_matches / len(opportunities)) * 100 if opportunities else 0
    print(f"  Funding Range Fit: {funding_fit:.1f}% of opportunities")
    
    # Risk analysis
    high_competition = sum(1 for opp in opportunities if opp.risk_factors.get("highly_competitive", False))
    competition_rate = (high_competition / len(opportunities)) * 100 if opportunities else 0
    print(f"  High Competition Risk: {competition_rate:.1f}% of opportunities")
    
    print(f"\nEnhanced Commercial Discovery Test Complete!")
    print(f"   Successfully integrated {len(set(opp.discovery_source for opp in opportunities))} data sources")
    print(f"   Average opportunity quality score: {sum(opp.compatibility_score for opp in opportunities) / len(opportunities):.3f}/1.0")


if __name__ == "__main__":
    asyncio.run(test_enhanced_commercial_discovery())