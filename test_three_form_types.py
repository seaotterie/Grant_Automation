#!/usr/bin/env python3
"""
Comprehensive Test: XML Parser Tools with Three Form Types
Tests 990, 990-PF, and 990-EZ parser tools with appropriate organizations
"""

import asyncio
import time
import json
import sys
import os
from pathlib import Path

# Add tool paths
current_dir = os.path.dirname(os.path.abspath(__file__))
xml_990_tool_path = os.path.join(current_dir, 'tools', 'xml-990-parser-tool', 'app')
xml_990pf_tool_path = os.path.join(current_dir, 'tools', 'xml-990pf-parser-tool', 'app')
xml_990ez_tool_path = os.path.join(current_dir, 'tools', 'xml-990ez-parser-tool', 'app')

sys.path.insert(0, xml_990_tool_path)
sys.path.insert(0, xml_990pf_tool_path)
sys.path.insert(0, xml_990ez_tool_path)

# Import tools
try:
    from xml_990_parser import XML990ParserTool, XML990ParseCriteria
    from xml_990pf_parser import XML990PFParserTool, XML990PFParseCriteria
    from xml_990ez_parser import XML990EZParserTool, XML990EZParseCriteria
    print("Successfully imported all XML parser tools")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

async def test_990_organization():
    """Test 990 Regular: HEROS BRIDGE (EIN: 812827604)"""
    print("\n" + "="*80)
    print("TEST 1: XML 990 PARSER TOOL")
    print("Organization: HEROS BRIDGE (EIN: 812827604)")
    print("Expected: Regular nonprofit, $504K revenue, should file Form 990")
    print("="*80)

    start_time = time.time()

    try:
        tool = XML990ParserTool()
        criteria = XML990ParseCriteria(
            target_eins=["812827604"],
            schedules_to_extract=['officers', 'grants', 'governance', 'financials'],
            cache_enabled=True,
            max_years_back=3,
            download_if_missing=True,
            validate_990_schema=True
        )

        result = await tool.execute(criteria)
        execution_time = (time.time() - start_time) * 1000

        print(f"\n[RESULTS] XML 990 Parser Tool:")
        print(f"  Organizations processed: {result.execution_metadata.organizations_processed}")
        print(f"  XML files processed: {result.execution_metadata.xml_files_processed}")
        print(f"  Officers extracted: {len(result.officers)}")

        if result.officers:
            print(f"  Sample officers:")
            for i, officer in enumerate(result.officers[:3], 1):
                print(f"    {i}. {officer.person_name} - {officer.title}")
                if hasattr(officer, 'average_hours_per_week') and officer.average_hours_per_week:
                    print(f"       Hours/week: {officer.average_hours_per_week}")
                if hasattr(officer, 'reportable_comp_from_org') and officer.reportable_comp_from_org:
                    print(f"       Compensation: ${officer.reportable_comp_from_org:,.2f}")

        print(f"  Grants made: {len(result.grants_made)}")
        print(f"  Program activities: {len(result.program_activities)}")
        print(f"  Financial summaries: {len(result.financial_summaries)}")
        print(f"  Governance indicators: {len(result.governance_indicators)}")
        print(f"  Schema validation rate: {result.execution_metadata.schema_validation_rate:.1f}%")
        print(f"  Cache hit rate: {result.execution_metadata.cache_hit_rate:.1f}%")
        print(f"  Execution time: {execution_time:.1f}ms")

        if result.xml_files_processed:
            for file_meta in result.xml_files_processed:
                print(f"  File processed: {Path(file_meta.file_path).name}")
                print(f"    Form type: {file_meta.form_type}")
                print(f"    Tax year: {file_meta.tax_year}")
                print(f"    Schema validation: {'PASS' if file_meta.schema_validation_passed else 'FAIL'}")
                if file_meta.parsing_errors:
                    print(f"    Errors: {file_meta.parsing_errors}")

        return {
            "status": "SUCCESS",
            "officers_count": len(result.officers),
            "files_processed": result.execution_metadata.xml_files_processed,
            "execution_time_ms": execution_time,
            "form_specialization": "990 Regular Nonprofits Only"
        }

    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        print(f"\n[ERROR] XML 990 Parser failed: {e}")
        print(f"  Execution time: {execution_time:.1f}ms")
        return {
            "status": "FAILED",
            "error": str(e),
            "execution_time_ms": execution_time
        }

async def test_990pf_organization():
    """Test 990-PF: INTERNATIONAL INSTITUTE OF ISLAMIC THOUGHT (EIN: 232202414)"""
    print("\n" + "="*80)
    print("TEST 2: XML 990-PF PARSER TOOL")
    print("Organization: INTERNATIONAL INSTITUTE OF ISLAMIC THOUGHT (EIN: 232202414)")
    print("Expected: Private foundation, $8.9M revenue, should file Form 990-PF")
    print("="*80)

    start_time = time.time()

    try:
        tool = XML990PFParserTool()
        criteria = XML990PFParseCriteria(
            target_eins=["232202414"],
            schedules_to_extract=['officers', 'grants', 'investments', 'requirements'],
            cache_enabled=True,
            max_years_back=3,
            download_if_missing=True,
            validate_990pf_schema=True
        )

        result = await tool.execute(criteria)
        execution_time = (time.time() - start_time) * 1000

        print(f"\n[RESULTS] XML 990-PF Parser Tool:")
        print(f"  Organizations processed: {result.execution_metadata.organizations_processed}")
        print(f"  XML files processed: {result.execution_metadata.xml_files_processed}")
        print(f"  Foundation officers: {len(result.officers)}")

        if result.officers:
            print(f"  Sample officers:")
            for i, officer in enumerate(result.officers[:3], 1):
                print(f"    {i}. {officer.person_name} - {officer.title}")
                if hasattr(officer, 'compensation') and officer.compensation:
                    print(f"       Compensation: ${officer.compensation:,.2f}")

        print(f"  Grants distributed: {len(result.grants_made)}")
        print(f"  Investment activities: {len(result.investment_activities)}")
        print(f"  Payout requirements: {len(result.payout_requirements)}")
        print(f"  Schema validation rate: {result.execution_metadata.schema_validation_rate:.1f}%")
        print(f"  Cache hit rate: {result.execution_metadata.cache_hit_rate:.1f}%")
        print(f"  Execution time: {execution_time:.1f}ms")

        if result.xml_files_processed:
            for file_meta in result.xml_files_processed:
                print(f"  File processed: {Path(file_meta.file_path).name}")
                print(f"    Form type: {file_meta.form_type}")
                print(f"    Tax year: {file_meta.tax_year}")
                print(f"    Schema validation: {'PASS' if file_meta.schema_validation_passed else 'FAIL'}")
                if file_meta.parsing_errors:
                    print(f"    Errors: {file_meta.parsing_errors}")

        return {
            "status": "SUCCESS",
            "officers_count": len(result.officers),
            "grants_count": len(result.grants_made),
            "files_processed": result.execution_metadata.xml_files_processed,
            "execution_time_ms": execution_time,
            "form_specialization": "990-PF Private Foundations Only"
        }

    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        print(f"\n[ERROR] XML 990-PF Parser failed: {e}")
        print(f"  Execution time: {execution_time:.1f}ms")
        return {
            "status": "FAILED",
            "error": str(e),
            "execution_time_ms": execution_time
        }

async def test_990ez_organization():
    """Test 990-EZ: JOURNEY HOME EQUINE RESCUE (EIN: 824012869)"""
    print("\n" + "="*80)
    print("TEST 3: XML 990-EZ PARSER TOOL")
    print("Organization: JOURNEY HOME EQUINE RESCUE (EIN: 824012869)")
    print("Expected: Small organization, $199K revenue, may file Form 990-EZ")
    print("="*80)

    start_time = time.time()

    try:
        tool = XML990EZParserTool()
        criteria = XML990EZParseCriteria(
            target_eins=["824012869"],
            schedules_to_extract=['officers', 'revenue', 'expenses', 'balance_sheet'],
            cache_enabled=True,
            max_years_back=3,
            download_if_missing=True,
            validate_990ez_schema=True
        )

        result = await tool.execute(criteria)
        execution_time = (time.time() - start_time) * 1000

        print(f"\n[RESULTS] XML 990-EZ Parser Tool:")
        print(f"  Organizations processed: {result.execution_metadata.organizations_processed}")
        print(f"  XML files processed: {result.execution_metadata.xml_files_processed}")
        print(f"  Small org officers: {len(result.officers)}")

        if result.officers:
            print(f"  Sample officers:")
            for i, officer in enumerate(result.officers[:3], 1):
                print(f"    {i}. {officer.person_name} - {officer.title}")
                if hasattr(officer, 'compensation') and officer.compensation:
                    print(f"       Compensation: ${officer.compensation:,.2f}")

        print(f"  Revenue records: {len(result.revenue_data)}")
        print(f"  Program accomplishments: {len(result.program_accomplishments)}")
        print(f"  Balance sheet data: {len(result.balance_sheet_data)}")
        print(f"  Schema validation rate: {result.execution_metadata.schema_validation_rate:.1f}%")
        print(f"  Cache hit rate: {result.execution_metadata.cache_hit_rate:.1f}%")
        print(f"  Execution time: {execution_time:.1f}ms")

        if result.xml_files_processed:
            for file_meta in result.xml_files_processed:
                print(f"  File processed: {Path(file_meta.file_path).name}")
                print(f"    Form type: {file_meta.form_type}")
                print(f"    Tax year: {file_meta.tax_year}")
                print(f"    Schema validation: {'PASS' if file_meta.schema_validation_passed else 'FAIL'}")
                if file_meta.parsing_errors:
                    print(f"    Errors: {file_meta.parsing_errors}")

        return {
            "status": "SUCCESS",
            "officers_count": len(result.officers),
            "revenue_records": len(result.revenue_data),
            "files_processed": result.execution_metadata.xml_files_processed,
            "execution_time_ms": execution_time,
            "form_specialization": "990-EZ Small Organizations Only"
        }

    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        print(f"\n[ERROR] XML 990-EZ Parser failed: {e}")
        print(f"  Execution time: {execution_time:.1f}ms")
        return {
            "status": "FAILED",
            "error": str(e),
            "execution_time_ms": execution_time
        }

async def main():
    """Run all three tests and provide comprehensive analysis"""
    print("[COMPREHENSIVE] XML PARSER TOOLS TEST")
    print("Testing three different form types with appropriate organizations")
    print("12-Factor Agents Framework - Factor 4 & Factor 10 Implementation")

    workflow_start = time.time()

    # Run all tests
    test_990_result = await test_990_organization()
    test_990pf_result = await test_990pf_organization()
    test_990ez_result = await test_990ez_organization()

    total_time = (time.time() - workflow_start) * 1000

    # Summary
    print("\n" + "="*80)
    print("[SUMMARY] COMPREHENSIVE TEST SUMMARY")
    print("="*80)
    print(f"Total execution time: {total_time:.1f}ms")
    print(f"Tests completed: 3")
    print()

    tests = [
        ("XML 990 Parser (HEROS BRIDGE)", test_990_result),
        ("XML 990-PF Parser (ISLAMIC THOUGHT)", test_990pf_result),
        ("XML 990-EZ Parser (EQUINE RESCUE)", test_990ez_result)
    ]

    for test_name, result in tests:
        status_icon = "[OK]" if result["status"] == "SUCCESS" else "[ERROR]"
        print(f"{status_icon} {test_name}:")
        print(f"   Status: {result['status']}")
        if "officers_count" in result:
            print(f"   Officers extracted: {result['officers_count']}")
        if "files_processed" in result:
            print(f"   Files processed: {result['files_processed']}")
        print(f"   Execution time: {result['execution_time_ms']:.1f}ms")
        if "error" in result:
            print(f"   Error: {result['error']}")
        print()

    # Save results
    complete_results = {
        "test_990": test_990_result,
        "test_990pf": test_990pf_result,
        "test_990ez": test_990ez_result,
        "summary": {
            "total_execution_time_ms": total_time,
            "tests_run": 3,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }

    with open('three_form_types_test_results.json', 'w') as f:
        json.dump(complete_results, f, indent=2, default=str)

    print(f"[SAVE] Complete results saved to: three_form_types_test_results.json")
    print("[SUCCESS] Three form types test completed!")

if __name__ == "__main__":
    asyncio.run(main())