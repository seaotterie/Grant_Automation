"""
Test the new leadership extraction logic on Holland Foundation HTML.
"""

from bs4 import BeautifulSoup
import re

# Read the saved HTML
with open('holland_attorneys_page.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'lxml')

print("=== TESTING NEW EXTRACTION LOGIC ===\n")

leadership = []

# Strategy 1: Look for H3/H4/H5 tags followed by titles
title_keywords = re.compile(r'president|chair|director|officer|member|ceo|cfo|coo|executive|treasurer|secretary|board|trustee', re.I)

print("Strategy 1: H3/H4/H5 + Sibling Title")
print("-" * 50)

for heading in soup.find_all(['h3', 'h4', 'h5']):
    name_text = heading.get_text(strip=True)

    # Skip if looks like a section heading
    if len(name_text) < 3 or name_text.lower() in ['board', 'staff', 'team', 'leadership', 'board members', 'directors']:
        continue

    # Look for title in next sibling elements
    title = None
    current = heading.find_next_sibling()

    # Check next few siblings for title
    for i in range(3):
        if current is None:
            break

        sibling_text = current.get_text(strip=True)

        # Check if this sibling contains a title keyword
        if title_keywords.search(sibling_text) and len(sibling_text) < 100:
            title = sibling_text
            break

        current = current.find_next_sibling()

    # If we found a valid name and title
    if title and len(name_text) > 2:
        # Check if not already added
        if not any(l['name'] == name_text for l in leadership):
            leadership.append({
                'name': name_text,
                'title': title,
                'bio': ''
            })
            # Remove zero-width spaces for printing
            clean_name = name_text.replace('\u200b', '')
            clean_title = title.replace('\u200b', '')
            print(f"[OK] Found: {clean_name} - {clean_title}")

print(f"\n=== TOTAL EXTRACTED: {len(leadership)} board members ===\n")

for i, leader in enumerate(leadership, 1):
    print(f"{i}. {leader['name']} - {leader['title']}")
