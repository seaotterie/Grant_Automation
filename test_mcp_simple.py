#!/usr/bin/env python3
"""
Simple test script for MCP integration without Unicode characters
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

async def test_mcp_basic():
    """Test basic MCP functionality"""
    print("Testing MCP Fetch server...")
    
    try:
        from src.core.mcp_client import MCPFetchClient, ScrapingConfig
        
        config = ScrapingConfig(max_length=1000, timeout=10)
        async with MCPFetchClient(config) as client:
            result = await client.fetch_url("https://httpbin.org/html")
            
            if result.success:
                print("PASS: MCP connection successful")
                print(f"Content length: {len(result.content)} chars")
                return True
            else:
                print(f"FAIL: {result.error}")
                return False
                
    except Exception as e:
        print(f"ERROR: {e}")
        return False

async def test_web_scraping():
    """Test web scraping service"""
    print("\nTesting web scraping service...")
    
    try:
        from src.core.mcp_client import WebScrapingService, ScrapingConfig
        
        config = ScrapingConfig(max_length=3000, timeout=15)
        service = WebScrapingService(config)
        
        # Test with a sample organization
        scraped_data = await service.scrape_organization_websites(
            organization_name="American Red Cross",
            ein="530196605"
        )
        
        if scraped_data:
            print("PASS: Web scraping successful")
            print(f"Successful scrapes: {len(scraped_data['successful_scrapes'])}")
            return True
        else:
            print("FAIL: No data scraped")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

async def main():
    """Run tests"""
    print("MCP Integration Test")
    print("=" * 30)
    
    tests = [
        ("MCP Basic", test_mcp_basic),
        ("Web Scraping", test_web_scraping),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"EXCEPTION in {name}: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 30)
    print("Results:")
    passed = 0
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} passed")
    return passed == len(results)

if __name__ == "__main__":
    success = asyncio.run(main())
    print("\nTest completed successfully!" if success else "\nSome tests failed!")
    sys.exit(0 if success else 1)