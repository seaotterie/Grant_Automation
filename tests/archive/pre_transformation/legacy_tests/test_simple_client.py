#!/usr/bin/env python3
"""
Test the simple web scraping client
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

async def test_simple_client():
    """Test the simple web scraping client"""
    print("Testing Simple Web Scraping Client")
    print("=" * 40)
    
    try:
        from src.core.simple_mcp_client import SimpleWebScrapingService
        
        service = SimpleWebScrapingService(timeout=15)
        
        # Test with American Red Cross
        print("Testing with American Red Cross...")
        result = await service.scrape_organization_websites(
            organization_name="American Red Cross",
            ein="530196605"
        )
        
        print(f"Successful scrapes: {len(result['successful_scrapes'])}")
        print(f"Failed scrapes: {len(result['failed_scrapes'])}")
        
        # Show some results
        if result['successful_scrapes']:
            print("\nSuccessful URLs:")
            for scrape in result['successful_scrapes'][:3]:
                print(f"  - {scrape['url']} ({scrape['content_length']} chars)")
                
        extracted = result['extracted_info']
        print(f"\nExtracted information:")
        print(f"  Mission statements: {len(extracted['mission_statements'])}")
        print(f"  Programs: {len(extracted['programs'])}")
        print(f"  Leadership: {len(extracted['leadership'])}")
        print(f"  Contact info: {len(extracted['contact_info'])}")
        
        if extracted['mission_statements']:
            print(f"\nSample mission statement:")
            print(f"  {extracted['mission_statements'][0][:200]}...")
            
        return len(result['successful_scrapes']) > 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_client())
    print(f"\nTest {'PASSED' if success else 'FAILED'}!")
    sys.exit(0 if success else 1)