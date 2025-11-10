"""
Test script to debug board member extraction from The Holland Foundation website.
"""

import requests
from bs4 import BeautifulSoup
import re

# Fetch the Holland Foundation website
url = "https://www.thehollandfoundation.org"
print(f"Fetching {url}...")

try:
    # Disable SSL verification since there's a certificate issue
    response = requests.get(url, verify=False, timeout=10)
    response.raise_for_status()
    print(f"Status: {response.status_code}")

    soup = BeautifulSoup(response.text, 'lxml')

    # Save the HTML for inspection
    with open('holland_foundation_page.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print("Saved HTML to holland_foundation_page.html")

    # Look for links to board/leadership pages
    print("\n=== SEARCHING FOR BOARD/LEADERSHIP LINKS ===")
    for link in soup.find_all('a', href=True):
        href = link.get('href', '').lower()
        link_text = link.get_text(strip=True).lower()

        keywords = ['board', 'team', 'leadership', 'directors', 'staff', 'about', 'people', 'governance']
        for keyword in keywords:
            if keyword in href or keyword in link_text:
                print(f"Found link: {link.get_text(strip=True)} -> {link.get('href')}")
                break

    # Test Strategy 1: Class-based search
    print("\n=== STRATEGY 1: CLASS-BASED SEARCH ===")
    people_sections = soup.find_all(['div', 'li', 'tr'], class_=re.compile(r'staff|board|team|member|person|director|trustee', re.I))
    print(f"Found {len(people_sections)} potential sections with board/staff classes")
    for i, section in enumerate(people_sections[:5]):
        print(f"\nSection {i+1}:")
        print(f"  Tag: {section.name}, Class: {section.get('class')}")
        print(f"  Text (first 100 chars): {section.get_text(strip=True)[:100]}")

    # Test Strategy 2: Table-based search
    print("\n=== STRATEGY 2: TABLE-BASED SEARCH ===")
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables")
    for i, table in enumerate(tables):
        rows = table.find_all('tr')
        print(f"\nTable {i+1}: {len(rows)} rows")
        if rows:
            first_row = rows[0]
            print(f"  First row: {first_row.get_text(strip=True)[:100]}")

    # Test Strategy 3: Text pattern matching
    print("\n=== STRATEGY 3: TEXT PATTERN MATCHING ===")
    text_content = soup.get_text()

    # Look for "Name, Title" or "Name - Title" patterns
    pattern = re.compile(r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,\-–—]\s*([A-Za-z\s]+(?:Chair|President|Director|Officer|Member|CEO|CFO|COO|Executive|Treasurer|Secretary))', re.I)
    matches = pattern.findall(text_content)

    print(f"Found {len(matches)} name-title patterns")
    for i, (name, title) in enumerate(matches[:10]):
        print(f"  {i+1}. {name} - {title}")

    # Search for specific board-related text
    print("\n=== SEARCHING FOR BOARD-RELATED TEXT ===")
    if 'board' in text_content.lower():
        # Find position of "board" in text
        board_positions = [m.start() for m in re.finditer(r'board', text_content, re.I)]
        print(f"Found {len(board_positions)} mentions of 'board'")

        # Show context around first few mentions
        for i, pos in enumerate(board_positions[:3]):
            context_start = max(0, pos - 50)
            context_end = min(len(text_content), pos + 100)
            context = text_content[context_start:context_end]
            print(f"\nMention {i+1} context: ...{context}...")

    print("\n=== COMPLETE ===")
    print("Check holland_foundation_page.html for full HTML content")

except requests.exceptions.SSLError as e:
    print(f"SSL Error: {e}")
    print("The website has SSL certificate issues, trying with verify=False")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
