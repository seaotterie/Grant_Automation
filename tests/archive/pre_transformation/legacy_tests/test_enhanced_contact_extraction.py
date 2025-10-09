#!/usr/bin/env python3
"""
Test Enhanced XML 990 Parser - Contact Information Extraction
Verify that website URL and phone numbers are now extracted from HEROS BRIDGE XML
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# Add XML 990 parser tool path
current_dir = os.path.dirname(os.path.abspath(__file__))
xml_990_tool_path = os.path.join(current_dir, 'tools', 'xml-990-parser-tool', 'app')
sys.path.insert(0, xml_990_tool_path)

from xml_990_parser import XML990ParserTool, XML990ParseCriteria

async def test_enhanced_contact_extraction():
    """Test enhanced XML 990 Parser with contact information extraction"""
    print("=" * 80)
    print("ENHANCED XML 990 PARSER - CONTACT INFORMATION EXTRACTION TEST")
    print("Target: HEROS BRIDGE (EIN: 81-2827604)")
    print("Expected: Website URL, Phone Numbers, Formation Year, Mission")
    print("=" * 80)

    start_time = time.time()

    try:
        tool = XML990ParserTool()
        criteria = XML990ParseCriteria(
            target_eins=["812827604"],
            schedules_to_extract=['officers', 'governance', 'financials'],
            cache_enabled=True,
            max_years_back=3,
            download_if_missing=True,
            validate_990_schema=True
        )

        result = await tool.execute(criteria)
        execution_time = (time.time() - start_time) * 1000

        print(f"\n[ENHANCED EXTRACTION RESULTS]")
        print(f"Organizations Processed: {result.execution_metadata.organizations_processed}")
        print(f"XML Files Processed: {len(result.xml_files_processed)}")
        print(f"Officers Extracted: {len(result.officers)}")
        print(f"Contact Records: {len(result.contact_information)}")
        print(f"Execution Time: {execution_time:.1f}ms")

        # Display contact information (the new enhancement)
        print(f"\n[CONTACT INFORMATION - NEW ENHANCEMENT]")
        if result.contact_information:
            for contact in result.contact_information:
                print(f"  EIN: {contact.ein}")
                print(f"  Tax Year: {contact.tax_year}")
                print(f"  Website URL: {contact.website_url or 'N/A'}")
                print(f"  Primary Phone: {contact.primary_phone or 'N/A'}")
                print(f"  Alternate Phone: {contact.alternate_phone or 'N/A'}")
                print(f"  Email: {contact.email_address or 'N/A'}")
                print(f"  Formation Year: {contact.formation_year or 'N/A'}")
                print(f"  Legal Domicile State: {contact.legal_domicile_state or 'N/A'}")
                print(f"  Organization Type: {contact.organization_type or 'N/A'}")
                print(f"  Activity/Mission: {contact.activity_mission_desc[:100] if contact.activity_mission_desc else 'N/A'}...")
                print()
        else:
            print("  [ERROR] No contact information extracted!")

        # Display officers for comparison (existing functionality)
        print(f"[OFFICER INFORMATION - EXISTING FUNCTIONALITY]")
        if result.officers:
            for i, officer in enumerate(result.officers[:3], 1):
                print(f"  {i}. {officer.person_name} - {officer.title}")
                print(f"     Hours/Week: {officer.average_hours_per_week or 'N/A'}")
                if officer.reportable_comp_from_org:
                    print(f"     Compensation: ${officer.reportable_comp_from_org:,.2f}")

        # Validation
        success = len(result.contact_information) > 0 and any(c.website_url for c in result.contact_information)

        print(f"\n[ENHANCEMENT VALIDATION]")
        print(f"Contact information extracted: {'[SUCCESS]' if len(result.contact_information) > 0 else '[FAILED]'}")
        print(f"Website URL found: {'[SUCCESS]' if any(c.website_url for c in result.contact_information) else '[FAILED]'}")
        print(f"Phone numbers found: {'[SUCCESS]' if any(c.primary_phone for c in result.contact_information) else '[FAILED]'}")

        if success:
            print(f"\n[SUCCESS] Enhanced XML 990 Parser now extracts contact information!")
            print(f"The missing website URL issue has been resolved.")
        else:
            print(f"\n[FAILED] Contact information extraction not working properly.")

        return success

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        return False

async def main():
    """Run enhanced contact extraction test"""
    print("[ENHANCED CONTACT EXTRACTION TEST]")
    print("Verifying fix for missing website URL and contact information")

    success = await test_enhanced_contact_extraction()

    if success:
        print(f"\n[OVERALL SUCCESS] XML 990 Parser enhancement complete!")
        print(f"• Website URLs now extracted from <WebsiteAddressTxt> elements")
        print(f"• Phone numbers now extracted from <PhoneNum> elements")
        print(f"• Additional organizational data now available")
        print(f"• No more missing contact information gap")
    else:
        print(f"\n[OVERALL FAILED] Enhancement needs debugging")

if __name__ == "__main__":
    asyncio.run(main())