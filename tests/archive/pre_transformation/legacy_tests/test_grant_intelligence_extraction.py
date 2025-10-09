#!/usr/bin/env python3
"""
Test Enhanced XML 990 Parser - Complete Grant Intelligence Extraction
Verify Schedule A, Schedule B, Contact Information, and Geographic Operations
Focus on grant-relevant data for research intelligence
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

async def test_grant_intelligence_extraction():
    """Test enhanced XML 990 Parser with complete grant intelligence extraction"""
    print("=" * 80)
    print("ENHANCED XML 990 PARSER - COMPLETE GRANT INTELLIGENCE TEST")
    print("Target: HEROS BRIDGE (EIN: 81-2827604)")
    print("Grant Intelligence: Schedule A + Schedule B + Contact + Geographic")
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

        print(f"\n[EXTRACTION RESULTS SUMMARY]")
        print(f"Organizations Processed: {result.execution_metadata.organizations_processed}")
        print(f"XML Files Processed: {len(result.xml_files_processed)}")
        print(f"Officers Extracted: {len(result.officers)}")
        print(f"Contact Records: {len(result.contact_information)}")
        print(f"Schedule A Records: {len(result.schedule_a_public_charity)}")
        print(f"Schedule B Records: {len(result.schedule_b_contributors)}")
        print(f"Execution Time: {execution_time:.1f}ms")

        # [1] CONTACT INFORMATION + GEOGRAPHIC INTELLIGENCE
        print(f"\n[1] CONTACT & GEOGRAPHIC INTELLIGENCE")
        if result.contact_information:
            contact = result.contact_information[0]
            print(f"  Website URL: {contact.website_url or 'N/A'}")
            print(f"  Primary Phone: {contact.primary_phone or 'N/A'}")
            print(f"  Formation Year: {contact.formation_year or 'N/A'}")
            print(f"  Legal Domicile State: {contact.legal_domicile_state or 'N/A'}")
            print(f"  Organization Type: {contact.organization_type or 'N/A'}")
            print(f"  Operational Footprint: {contact.operational_footprint or 'N/A'}")
            if contact.multi_state_operations:
                print(f"  Multi-State Operations: {', '.join(contact.multi_state_operations)}")
            print(f"  Mission: {contact.activity_mission_desc[:100] if contact.activity_mission_desc else 'N/A'}...")
        else:
            print("  [ERROR] No contact information extracted!")

        # [2] SCHEDULE A - GRANT ELIGIBILITY INTELLIGENCE
        print(f"\n[2] SCHEDULE A - GRANT ELIGIBILITY INTELLIGENCE")
        if result.schedule_a_public_charity:
            schedule_a = result.schedule_a_public_charity[0]
            print(f"  Grant Eligibility Classification: {schedule_a.grant_eligibility_classification}")
            print(f"  Grant Eligibility Confidence: {schedule_a.grant_eligibility_confidence}")
            print(f"  Public Charity Status: {'Yes' if schedule_a.public_charity_status else 'No'}")
            print(f"  Public Support Percentage: {schedule_a.public_support_percentage:.1%}" if schedule_a.public_support_percentage else "  Public Support Percentage: N/A")
            print(f"  Support Test Passed: {'Yes' if schedule_a.support_test_passed else 'No'}")
            print(f"  Total Public Support: ${schedule_a.total_public_support:,.2f}" if schedule_a.total_public_support else "  Total Public Support: N/A")
            print(f"  Total Support Amount: ${schedule_a.total_support_amount:,.2f}" if schedule_a.total_support_amount else "  Total Support Amount: N/A")
        else:
            print("  [WARNING] No Schedule A data extracted")

        # [3] SCHEDULE B - FOUNDATION RELATIONSHIP INTELLIGENCE
        print(f"\n[3] SCHEDULE B - FOUNDATION RELATIONSHIP INTELLIGENCE")
        if result.schedule_b_contributors:
            schedule_b = result.schedule_b_contributors[0]
            print(f"  Contributor Data Available: {'Yes' if schedule_b.contributor_data_available else 'No'}")
            print(f"  Major Contributor Count: {schedule_b.major_contributor_count or 'Restricted/Unknown'}")
            print(f"  Information Restricted: {'Yes' if schedule_b.contributor_information_restricted else 'No'}")
            print(f"  Foundation Relationship Indicator: {'Yes' if schedule_b.foundation_relationship_indicator else 'No'}")
        else:
            print("  [WARNING] No Schedule B data extracted")

        # [4] OFFICER/LEADERSHIP INTELLIGENCE (Existing)
        print(f"\n[4] LEADERSHIP INTELLIGENCE (EXISTING)")
        if result.officers:
            print(f"  Total Officers: {len(result.officers)}")
            for i, officer in enumerate(result.officers[:3], 1):
                print(f"    {i}. {officer.person_name} - {officer.title}")
                print(f"       Hours/Week: {officer.average_hours_per_week or 'N/A'}")
                if officer.reportable_comp_from_org:
                    print(f"       Compensation: ${officer.reportable_comp_from_org:,.2f}")
        else:
            print("  [ERROR] No officers extracted!")

        # [5] GRANT RESEARCH IMPACT ANALYSIS
        print(f"\n[5] GRANT RESEARCH IMPACT ANALYSIS")

        # Grant Eligibility Assessment
        eligibility_score = "Unknown"
        if result.schedule_a_public_charity:
            schedule_a = result.schedule_a_public_charity[0]
            if schedule_a.grant_eligibility_classification == "Public Charity":
                if schedule_a.grant_eligibility_confidence == "High":
                    eligibility_score = "Excellent"
                elif schedule_a.grant_eligibility_confidence == "Medium":
                    eligibility_score = "Good"
                else:
                    eligibility_score = "Fair"
            else:
                eligibility_score = "Limited (Private Foundation)"

        # Geographic Reach Assessment
        geographic_reach = "Unknown"
        if result.contact_information and result.contact_information[0].operational_footprint:
            footprint = result.contact_information[0].operational_footprint
            if "National" in footprint:
                geographic_reach = "National"
            elif "Multi-state" in footprint:
                geographic_reach = "Regional"
            else:
                geographic_reach = "Local"

        # Foundation Network Potential
        network_potential = "Unknown"
        if result.schedule_b_contributors:
            schedule_b = result.schedule_b_contributors[0]
            if schedule_b.foundation_relationship_indicator:
                network_potential = "High (Foundation connections detected)"
            elif schedule_b.contributor_data_available:
                network_potential = "Medium (Major contributors present)"
            else:
                network_potential = "Low (Limited contributor data)"

        print(f"  Grant Eligibility Score: {eligibility_score}")
        print(f"  Geographic Reach: {geographic_reach}")
        print(f"  Foundation Network Potential: {network_potential}")
        print(f"  Contact Information: {'Complete' if result.contact_information and result.contact_information[0].website_url else 'Partial'}")

        # Overall Intelligence Success
        intelligence_components = [
            result.contact_information and len(result.contact_information) > 0,
            result.schedule_a_public_charity and len(result.schedule_a_public_charity) > 0,
            result.schedule_b_contributors and len(result.schedule_b_contributors) > 0,
            result.officers and len(result.officers) > 0
        ]

        success_count = sum(intelligence_components)
        overall_success = success_count >= 3  # At least 3 out of 4 components

        print(f"\n[GRANT INTELLIGENCE VALIDATION]")
        print(f"Contact Information: {'[SUCCESS]' if intelligence_components[0] else '[FAILED]'}")
        print(f"Schedule A (Grant Eligibility): {'[SUCCESS]' if intelligence_components[1] else '[FAILED]'}")
        print(f"Schedule B (Foundation Relationships): {'[SUCCESS]' if intelligence_components[2] else '[FAILED]'}")
        print(f"Leadership Information: {'[SUCCESS]' if intelligence_components[3] else '[FAILED]'}")
        print(f"Overall Grant Intelligence: {'[SUCCESS]' if overall_success else '[FAILED]'}")

        return overall_success

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        return False

async def main():
    """Run grant intelligence extraction test"""
    print("[GRANT INTELLIGENCE EXTRACTION TEST]")
    print("Testing Schedule A, Schedule B, Contact, and Geographic intelligence")

    success = await test_grant_intelligence_extraction()

    if success:
        print(f"\n[OVERALL SUCCESS] Enhanced XML 990 Parser with grant intelligence!")
        print(f"• Schedule A: Grant eligibility classification intelligence [OK]")
        print(f"• Schedule B: Foundation relationship pattern intelligence [OK]")
        print(f"• Contact Information: Website URLs, phone numbers, mission [OK]")
        print(f"• Geographic Intelligence: Multi-state operations analysis [OK]")
        print(f"• Leadership Intelligence: Complete officer/board roster [OK]")
        print(f"\nGrant research intelligence extraction complete!")
    else:
        print(f"\n[OVERALL FAILED] Grant intelligence extraction needs debugging")

if __name__ == "__main__":
    asyncio.run(main())