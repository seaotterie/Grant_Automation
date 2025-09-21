#!/usr/bin/env python3
"""
Test HTML to Text Conversion
Debug what's happening with the Heroes Bridge content
"""

import asyncio
import aiohttp
import ssl
from bs4 import BeautifulSoup

async def test_html_conversion():
    """Test HTML to text conversion step by step"""
    url = "https://www.herosbridge.org"
    
    print("="*60)
    print("HTML TO TEXT CONVERSION DEBUG")  
    print("="*60)
    
    # Get the raw HTML first
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
            if response.status == 200:
                html_content = await response.text()
                print(f"Raw HTML length: {len(html_content)}")
                
                # Test BeautifulSoup processing
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get raw text
                raw_text = soup.get_text()
                print(f"Raw text length: {len(raw_text)}")
                print(f"Raw text preview (first 1000 chars):\n{raw_text[:1000]}")
                print("\n" + "="*40)
                
                # Apply cleaning
                lines = (line.strip() for line in raw_text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                clean_text = ' '.join(chunk for chunk in chunks if chunk)
                
                print(f"Clean text length: {len(clean_text)}")
                print(f"Clean text preview (first 1000 chars):\n{clean_text[:1000]}")
                
                # Look for key terms
                print(f"\nContent Analysis:")
                print(f"Contains 'hero': {'hero' in clean_text.lower()}")
                print(f"Contains 'bridge': {'bridge' in clean_text.lower()}")
                print(f"Contains 'veteran': {'veteran' in clean_text.lower()}")
                print(f"Contains 'mission': {'mission' in clean_text.lower()}")
                print(f"Contains 'service': {'service' in clean_text.lower()}")
                
if __name__ == "__main__":
    asyncio.run(test_html_conversion())