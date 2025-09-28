import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools', 'xml-990ez-parser-tool'))

from app.xml_990ez_parser import XML990EZParserTool, XML990EZParseCriteria

async def test_small_org():
    parser = XML990EZParserTool()
    criteria = XML990EZParseCriteria(
        target_eins=['812827604'],  # HEROS BRIDGE (should be rejected as it files 990, not 990-EZ)
        schedules_to_extract=['officers', 'revenue', 'expenses', 'balance_sheet', 'public_support'],
        cache_enabled=True,
        max_years_back=3,
        download_if_missing=True,
        validate_990ez_schema=True
    )

    print('Testing XML 990-EZ Parser Tool with HEROS BRIDGE (EIN 812827604 - should reject 990 form)')
    print('=' * 70)

    try:
        result = await parser.execute(criteria)

        print(f'Tool: {result.tool_name}')
        print(f'Framework: {result.framework_compliance}')
        print(f'Factor 4: {result.factor_4_implementation}')
        print(f'Form Specialization: {result.form_type_specialization}')
        print()

        print(f'Organizations Processed: {result.organizations_processed}')
        print(f'Officers Extracted: {result.officers_extracted}')
        print(f'Accomplishments Extracted: {result.accomplishments_extracted}')
        print(f'Extraction Failures: {result.extraction_failures}')
        print()

        print('Small Organization Officers:')
        for officer in result.officers[:5]:  # Show first 5
            print(f'  • {officer.person_name} - {officer.title}')
            if officer.compensation:
                print(f'    Compensation: ${officer.compensation:,.2f}')

        print()
        print('Revenue Data:')
        for revenue in result.revenue_data:
            if revenue.total_revenue:
                print(f'  • Total Revenue: ${revenue.total_revenue:,.2f}')
            if revenue.contributions_gifts_grants:
                print(f'  • Contributions: ${revenue.contributions_gifts_grants:,.2f}')

        print()
        print('Program Accomplishments:')
        for accomplishment in result.program_accomplishments:
            print(f'  • Program {accomplishment.accomplishment_number}:')
            if accomplishment.description:
                print(f'    Description: {accomplishment.description[:100]}...')
            if accomplishment.expense_amount:
                print(f'    Expense: ${accomplishment.expense_amount:,.2f}')

        print()
        print('Execution Metadata:')
        print(f'  Execution Time: {result.execution_metadata.execution_time_ms:.2f}ms')
        print(f'  XML Files Found: {result.execution_metadata.xml_files_found}')
        print(f'  XML Files Parsed: {result.execution_metadata.xml_files_parsed}')
        print(f'  Schema Validation Rate: {result.quality_assessment.schema_validation_rate:.1%}')

    except Exception as e:
        print(f'Error testing 990-EZ parser: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_small_org())