#!/usr/bin/env python3
"""
Heroes Bridge Complete Profile Enhancement Test
Tests the full GPT URL Discovery → Fetch MCP → Profile Enhancement pipeline
"""

import asyncio
import json
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_heroes_bridge_profile_enhancement():
    """Test complete Heroes Bridge profile enhancement pipeline"""
    logger.info("Heroes Bridge Profile Enhancement Test")
    
    # Heroes Bridge test data (corrected location: Warrenton, VA)
    test_request = {
        'ein': '812827604',
        'enable_web_scraping': True
    }
    
    logger.info(f"Testing EIN: {test_request['ein']} (Heroes Bridge, Warrenton, VA)")
    
    try:
        # Import the FastAPI endpoint function
        import sys
        sys.path.append('src')
        from web.main import fetch_ein_data
        
        # Call the actual API endpoint
        logger.info("Calling fetch_ein_data API endpoint...")
        result = await fetch_ein_data(test_request)
        
        # Analyze the results
        print("\n" + "="*80)
        print("HEROES BRIDGE PROFILE ENHANCEMENT RESULTS")
        print("="*80)
        
        # Basic organization info
        print(f"Organization: {result.get('organization_name', 'N/A')}")
        print(f"EIN: {result.get('ein', 'N/A')}")
        print(f"Location: {result.get('address', 'N/A')}")
        print(f"State: {result.get('state', 'N/A')}")
        
        # Mission statement analysis
        mission = result.get('mission_statement', '')
        print(f"\nMission Statement ({len(mission)} chars):")
        print(f"   {mission[:200]}{'...' if len(mission) > 200 else ''}")
        
        # Web scraping results
        web_data = result.get('web_scraping_data', {})
        enhanced = result.get('enhanced_with_web_data', False)
        
        print(f"\nWeb Enhancement Status: {'ENHANCED' if enhanced else 'NOT ENHANCED'}")
        
        if web_data and 'successful_scrapes' in web_data:
            scrapes = web_data['successful_scrapes']
            print(f"Successful Scrapes: {len(scrapes)}")
            
            for i, scrape in enumerate(scrapes[:3], 1):
                print(f"   {i}. {scrape.get('url', 'N/A')} (Score: {scrape.get('content_score', 0.0):.2f})")
        
        # Enhanced profile data
        programs = result.get('programs', [])
        leadership = result.get('leadership', [])
        contact_info = result.get('contact_info', [])
        
        print(f"\nPrograms Found: {len(programs)}")
        for i, program in enumerate(programs[:3], 1):
            print(f"   {i}. {program[:100]}{'...' if len(program) > 100 else ''}")
        
        print(f"\nLeadership Found: {len(leadership)}")
        for i, leader in enumerate(leadership[:3], 1):
            print(f"   {i}. {leader[:100]}{'...' if len(leader) > 100 else ''}")
        
        print(f"\nContact Info Found: {len(contact_info)}")
        for i, contact in enumerate(contact_info[:3], 1):
            print(f"   {i}. {contact[:100]}{'...' if len(contact) > 100 else ''}")
        
        # URL Discovery analysis
        if web_data and 'url_source' in web_data:
            source = web_data['url_source']
            print(f"\nURL Discovery Source: {source}")
            
            if source == 'gpt_prediction':
                print("   GPT-5-nano URL prediction successful")
            else:
                print("   Fallback to pattern-based URL discovery")
        
        # Financial data
        revenue = result.get('revenue', 0)
        assets = result.get('assets', 0)
        expenses = result.get('expenses', 0)
        
        print(f"\nFinancial Data:")
        print(f"   Revenue: ${revenue:,}" if revenue else "   Revenue: N/A")
        print(f"   Assets: ${assets:,}" if assets else "   Assets: N/A")  
        print(f"   Expenses: ${expenses:,}" if expenses else "   Expenses: N/A")
        
        # Schedule I grantees
        grantees = result.get('schedule_i_grantees', [])
        print(f"\nSchedule I Grantees: {len(grantees)}")
        for i, grantee in enumerate(grantees[:3], 1):
            name = grantee.get('name', 'N/A')
            amount = grantee.get('amount', 0)
            print(f"   {i}. {name} - ${amount:,}")
        
        print("\n" + "="*80)
        
        # Assessment
        enhancement_score = 0
        if enhanced:
            enhancement_score += 3
        if len(programs) > 0:
            enhancement_score += 2
        if len(leadership) > 0:
            enhancement_score += 2
        if len(contact_info) > 0:
            enhancement_score += 2
        if len(mission) > 100:
            enhancement_score += 1
        
        print(f"Profile Enhancement Score: {enhancement_score}/10")
        
        if enhancement_score >= 7:
            print("EXCELLENT - Rich profile data successfully extracted")
        elif enhancement_score >= 4:
            print("GOOD - Solid profile enhancement achieved")
        else:
            print("BASIC - Limited enhancement, may need debugging")
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing Heroes Bridge profile enhancement: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Run Heroes Bridge profile enhancement test"""
    result = await test_heroes_bridge_profile_enhancement()
    
    if result:
        # Save detailed results
        with open('heroes_bridge_profile_test.json', 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\nDetailed results saved to: heroes_bridge_profile_test.json")

if __name__ == "__main__":
    asyncio.run(main())