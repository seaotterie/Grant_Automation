"""
Debug Virginia State Discovery
"""
import asyncio
from src.processors.data_collection.va_state_grants_fetch import VirginiaStateGrantsFetch


async def debug_va_discovery():
    """Debug Virginia state discovery"""
    
    print("Debugging Virginia State Discovery")
    print("=" * 50)
    
    # Test focus areas
    focus_areas = ["community_health", "health_equity", "disease_prevention", "maternal_health"]
    
    # Initialize VA processor
    va_processor = VirginiaStateGrantsFetch()
    
    # Test agency configuration loading
    print(f"Loaded {len(va_processor.state_agencies)} Virginia agencies:")
    for key, agency in va_processor.state_agencies.items():
        print(f"  {key}: {agency['name']} (Priority: {agency['priority']})")
    
    # Test health opportunities generation
    print(f"\nTesting VA Health opportunity discovery:")
    agency_config = va_processor.state_agencies["va_dept_health"]
    
    health_opportunities = await va_processor._discover_va_health_opportunities(agency_config, focus_areas)
    print(f"Generated {len(health_opportunities)} health opportunities:")
    
    for opp in health_opportunities:
        print(f"\n  Opportunity: {opp.program_name}")
        print(f"  Focus Area: {opp.focus_area}")
        print(f"  Description: {opp.description[:100]}...")
        
        # Test focus alignment manually
        alignment = va_processor._check_focus_alignment(focus_areas, [opp.focus_area, opp.description])
        print(f"  Focus Alignment: {alignment}")
        
        # Show matching details
        for focus in focus_areas:
            focus_terms = focus.lower().split()
            opp_text = (opp.focus_area + " " + opp.description).lower()
            matches = [term for term in focus_terms if term in opp_text]
            if matches:
                print(f"    '{focus}' matches: {matches}")
    
    # Test full discovery process
    print(f"\nTesting full discovery process:")
    
    search_data = {
        "focus_areas": focus_areas,
        "geographic_scope": ["VA"],
        "funding_range": {"min_amount": 25000, "max_amount": 200000},
        "max_results": 10
    }
    
    results = await va_processor.process(search_data, {})
    print(f"Process results: {results.get('status')}")
    print(f"Total found: {results.get('total_found', 0)}")
    
    if results.get("state_opportunities"):
        print(f"First opportunity: {results['state_opportunities'][0]['program_name']}")


if __name__ == "__main__":
    asyncio.run(debug_va_discovery())