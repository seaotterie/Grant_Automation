import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools', 'propublica-api-enrichment-tool'))

from app.propublica_api_enricher import ProPublicaAPIEnrichmentTool, ProPublicaAPIEnrichmentCriteria

async def test_propublica_api():
    tool = ProPublicaAPIEnrichmentTool()
    criteria = ProPublicaAPIEnrichmentCriteria(
        target_eins=['812827604'],  # HEROS BRIDGE
        include_filing_history=True,
        years_to_include=3,
        include_mission_data=True,
        include_leadership_summary=True,
        include_similar_orgs=False,
        max_similar_orgs=5
    )

    print('Testing Enhanced ProPublica API Enrichment Tool with Leadership Data')
    print('=' * 75)

    try:
        result = await tool.execute(criteria)

        print(f'Tool: {result.tool_name}')
        print(f'Framework: {result.framework_compliance}')
        print(f'Factor 4: {result.factor_4_implementation}')
        print(f'Leadership Data Note: {result.leadership_data_note}')
        print()

        print(f'Organizations Processed: {result.total_organizations_processed}')
        print(f'Organizations Enriched: {result.organizations_enriched}')
        print(f'Filing Summaries: {len(result.filing_summaries)}')
        print(f'Leadership Summaries: {len(result.leadership_summaries)}')
        print()

        print('Organization Profiles:')
        for org in result.enriched_organizations:
            print(f'  • {org.name} ({org.ein})')
            print(f'    State: {org.state}, NTEE: {org.ntee_code}')

        print()
        print('Leadership Summaries (API Data):')
        for leadership in result.leadership_summaries:
            if leadership.total_compensation:
                print(f'  • {leadership.tax_year}: Total Compensation ${leadership.total_compensation:,.2f}')
            else:
                print(f'  • {leadership.tax_year}: No compensation data available')

        if result.leadership_summaries:
            print(f'  Note: {result.leadership_data_note}')
        else:
            print('  No leadership compensation data available from API')

        print()
        print('Filing History:')
        for filing in result.filing_summaries[:3]:  # Show first 3
            revenue_text = f'${filing.total_revenue:,.2f}' if filing.total_revenue else 'No data'
            print(f'  • {filing.tax_year} {filing.form_type}: Revenue {revenue_text}')

        print()
        print('Execution Metadata:')
        print(f'  Execution Time: {result.execution_metadata.execution_time_ms:.2f}ms')
        print(f'  API Calls Made: {result.execution_metadata.api_calls_made}')
        print(f'  Success Rate: {result.execution_metadata.success_rate:.1%}')

    except Exception as e:
        print(f'Error testing ProPublica API tool: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_propublica_api())