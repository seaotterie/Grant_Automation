"""
Debug Deeper Virginia State Discovery
"""
import asyncio
from src.processors.data_collection.va_state_grants_fetch import VirginiaStateGrantsFetch


async def debug_deeper_va():
    """Debug the complete Virginia discovery flow"""
    
    print("Deep Debugging Virginia State Discovery Flow")
    print("=" * 60)
    
    focus_areas = ["community_health", "health_equity", "disease_prevention", "maternal_health"]
    funding_range = {"min_amount": 25000, "max_amount": 200000}
    
    va_processor = VirginiaStateGrantsFetch()
    
    # Test step by step
    print("1. Testing _discover_state_opportunities")
    state_opportunities = await va_processor._discover_state_opportunities(
        focus_areas=focus_areas,
        geographic_scope=["VA"],
        funding_range=funding_range,
        max_results=10
    )
    print(f"   Found {len(state_opportunities)} opportunities")
    
    # Test agency discovery directly
    print("\n2. Testing _discover_agency_opportunities for VA Health")
    va_health_config = va_processor.state_agencies["va_dept_health"]
    
    agency_opportunities = await va_processor._discover_agency_opportunities(
        va_health_config, focus_areas, funding_range
    )
    print(f"   Agency opportunities: {len(agency_opportunities)}")
    
    for opp in agency_opportunities:
        print(f"   - {opp.program_name} (Focus: {opp.focus_area})")
    
    # Test filtering
    print("\n3. Testing _filter_opportunities_by_focus")
    if agency_opportunities:
        filtered_opportunities = va_processor._filter_opportunities_by_focus(
            agency_opportunities, focus_areas
        )
        print(f"   Filtered opportunities: {len(filtered_opportunities)}")
        
        for opp in filtered_opportunities:
            relevance_score = va_processor._calculate_opportunity_relevance(opp, focus_areas)
            print(f"   - {opp.program_name}: relevance={relevance_score:.3f}, confidence={opp.confidence_score:.3f}")
    
    # Test the VA Health discovery method directly
    print("\n4. Testing _discover_va_health_opportunities directly")
    health_opportunities = await va_processor._discover_va_health_opportunities(
        va_health_config, focus_areas
    )
    print(f"   Health opportunities: {len(health_opportunities)}")
    
    for opp in health_opportunities:
        print(f"   - {opp.program_name}")
        relevance_score = va_processor._calculate_opportunity_relevance(opp, focus_areas)
        print(f"     Relevance score: {relevance_score:.3f}")
        print(f"     Above 0.3 threshold: {relevance_score > 0.3}")
        
        # Debug the relevance calculation
        opportunity_text = (
            opp.focus_area + " " +
            opp.description + " " +
            " ".join(opp.target_populations)
        ).lower()
        
        matches_found = []
        total_score = 0.0
        for focus in focus_areas:
            focus_terms = focus.lower().split()
            for term in focus_terms:
                if term in opportunity_text:
                    matches_found.append(f"{focus}:{term}")
                    total_score += 0.2
        
        print(f"     Matches found: {matches_found}")
        print(f"     Raw score: {total_score}")


if __name__ == "__main__":
    asyncio.run(debug_deeper_va())