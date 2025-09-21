#!/usr/bin/env python3
"""
Debug Heroes Bridge Website Access
Simple test to understand what's happening with the website
"""

import asyncio
import aiohttp
import ssl
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_website_access():
    """Test different approaches to access Heroes Bridge website"""
    url = "https://www.herosbridge.org"
    
    print("="*60)
    print("HEROES BRIDGE WEBSITE DEBUG TEST")
    print("="*60)
    
    # Test 1: Basic aiohttp request
    print(f"\nTest 1: Basic aiohttp request to {url}")
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=20)
        ) as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with session.get(url, headers=headers) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    content = await response.text()
                    print(f"Content length: {len(content)}")
                    print(f"First 500 chars: {content[:500]}")
                    
                    # Check for title
                    if '<title>' in content.lower():
                        try:
                            start = content.lower().find('<title>') + 7
                            end = content.lower().find('</title>', start)
                            if end > start:
                                title = content[start:end].strip()
                                print(f"Title: {title}")
                        except:
                            print("Title extraction failed")
                else:
                    error_content = await response.text()
                    print(f"Error content: {error_content[:200]}")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_website_access())