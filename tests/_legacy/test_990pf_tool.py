import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools', 'xml-990pf-parser-tool'))

from app.xml_990pf_parser import XML990PFParserTool

async def test_foundation():
    parser = XML990PFParserTool()
    criteria = {
        'target_eins': ['131684331'],  # Ford Foundation
        'schedules_to_extract': ['officers', 'grants_paid', 'investments', 'excise_tax', 'payout_requirements'],
        'cache_enabled': True,
        'max_years_back': 3,
        'download_if_missing': True,
        'validate_990pf_schema': True
    }

    print('Testing XML 990-PF Parser Tool with Ford Foundation (EIN 131684331)')
    print('=' * 70)

    try:
        from app.xml_990pf_parser import XML990PFParseCriteria
        criteria_obj = XML990PFParseCriteria(**criteria)
        result = await parser.execute(criteria_obj)

        print(f'Tool: {result.tool_name}')
        print(f'Framework: {result.framework_compliance}')
        print(f'Factor 4: {result.factor_4_implementation}')
        print(f'Form Specialization: {result.form_type_specialization}')
        print()

        print(f'Organizations Processed: {result.organizations_processed}')
        print(f'Officers Extracted: {result.officers_extracted}')
        print(f'Grants Extracted: {result.grants_extracted}')
        print(f'Investments Extracted: {result.investments_extracted}')
        print(f'Extraction Failures: {result.extraction_failures}')
        print()

        print('Foundation Officers:')
        for officer in result.officers[:5]:  # Show first 5
            print(f'  • {officer.person_name} - {officer.title}')
            if officer.compensation:
                print(f'    Compensation: ${officer.compensation:,.2f}')

        print()
        print('Foundation Grants:')
        for grant in result.grants_paid[:3]:  # Show first 3
            print(f'  • {grant.recipient_name}: ${grant.grant_amount:,.2f}')
            if grant.grant_purpose:
                print(f'    Purpose: {grant.grant_purpose[:100]}...')

        print()
        print('Execution Metadata:')
        print(f'  Execution Time: {result.execution_metadata.execution_time_ms:.2f}ms')
        print(f'  XML Files Found: {result.execution_metadata.xml_files_found}')
        print(f'  XML Files Parsed: {result.execution_metadata.xml_files_parsed}')
        print(f'  Schema Validation Rate: {result.quality_assessment.schema_validation_rate:.1%}')

    except Exception as e:
        print(f'Error testing 990-PF parser: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_foundation())