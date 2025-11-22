"""
Test spider extraction on Holland attorneys page
"""
import sys
sys.path.insert(0, r'C:\Users\cotte\Documents\Home\03_Dad\_Projects\2025\ClaudeCode\Grant_Automation\tools\web_intelligence_tool\app')

from scrapy_spiders.organization_profile_spider import OrganizationProfileSpider
from bs4 import BeautifulSoup

# Read the saved HTML
with open('holland_attorneys_page.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'lxml')

# Create spider instance
spider = OrganizationProfileSpider(ein='470804949', organization_name='HOLLAND FOUNDATION', start_url='https://www.thehollandfoundation.org')

# Test extraction
print("Testing _extract_leadership method:")
print("=" * 60)

leadership = spider._extract_leadership(soup, 'https://www.thehollandfoundation.org/attorneys.html')

print(f"\nExtracted {len(leadership)} leaders:")
for i, leader in enumerate(leadership, 1):
    print(f"{i}. {leader['name']} - {leader['title']}")
