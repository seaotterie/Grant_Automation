#!/usr/bin/env python3
"""
Test 990-PF Parser with Fauquier Health Foundation
Major private foundation with $287M assets for comprehensive testing
Analyze current extraction vs grant research needs
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# Add XML 990-PF parser tool path
current_dir = os.path.dirname(os.path.abspath(__file__))
xml_990pf_tool_path = os.path.join(current_dir, 'tools', 'xml-990pf-parser-tool', 'app')
sys.path.insert(0, xml_990pf_tool_path)

from xml_990pf_parser import XML990PFParserTool, XML990PFParseCriteria

async def test_990pf_fauquier_foundation():
    """Test 990-PF parser with Fauquier Health Foundation - major private foundation"""
    print("=" * 80)
    print("990-PF PARSER TEST - FAUQUIER HEALTH FOUNDATION")
    print("EIN: 30-0219424 | Assets: $287M | Type: Private Foundation")
    print("Focus: Grant research intelligence for foundation analysis")
    print("=" * 80)

    start_time = time.time()

    try:
        tool = XML990PFParserTool()
        criteria = XML990PFParseCriteria(
            target_eins=["300219424"],
            schedules_to_extract=['officers', 'grants_paid', 'investments', 'excise_tax', 'payout_requirements'],
            cache_enabled=True,
            max_years_back=3,
            download_if_missing=True,
            validate_990pf_schema=True
        )

        result = await tool.execute(criteria)
        execution_time = (time.time() - start_time) * 1000

        print(f"\n[RAW BAML STRUCTURED OUTPUT]")
        print(f"=" * 60)

        # Show exact BAML result structure
        print(f"XML990PFResult Object:")
        print(f"  tool_name: {result.tool_name}")
        print(f"  framework_compliance: {result.framework_compliance}")
        print(f"  factor_4_implementation: {result.factor_4_implementation}")
        print(f"  organizations_processed: {result.organizations_processed}")
        print(f"  officers_extracted: {result.officers_extracted}")
        print(f"  grants_extracted: {result.grants_extracted}")
        print(f"  investments_extracted: {result.investments_extracted}")
        print(f"  extraction_failures: {result.extraction_failures}")

        print(f"\n[CONTACT INFO BAML OBJECTS]")
        for i, contact in enumerate(result.contact_info):
            print(f"  FoundationContactInfo[{i}]:")
            print(f"    ein: {contact.ein}")
            print(f"    foundation_name: {contact.foundation_name}")
            print(f"    phone_number: {contact.phone_number}")
            print(f"    principal_officer_name: {contact.principal_officer_name}")
            print(f"    principal_officer_title: {contact.principal_officer_title}")
            print(f"    tax_year: {contact.tax_year}")
            print(f"    data_source: {contact.data_source}")

        print(f"\n[OFFICER BAML OBJECTS] (All {len(result.officers)} Officers)")
        for i, officer in enumerate(result.officers):
            print(f"  FoundationOfficer[{i}]:")
            print(f"    ein: {officer.ein}")
            print(f"    person_name: {officer.person_name}")
            print(f"    normalized_person_name: {officer.normalized_person_name}")
            print(f"    title: {officer.title}")
            print(f"    role_category: {officer.role_category}")
            print(f"    average_hours_per_week: {officer.average_hours_per_week}")
            print(f"    compensation: {officer.compensation}")
            print(f"    employee_benefit_program: {officer.employee_benefit_program}")
            print(f"    expense_account_allowance: {officer.expense_account_allowance}")
            print(f"    is_officer: {officer.is_officer}")
            print(f"    is_director: {officer.is_director}")
            print(f"    influence_score: {officer.influence_score}")
            print(f"    tax_year: {officer.tax_year}")
            print(f"    data_source: {officer.data_source}")

        print(f"\n[GRANT BAML OBJECTS] (All {len(result.grants_paid)} Grants)")
        for i, grant in enumerate(result.grants_paid):
            print(f"  FoundationGrant[{i}]:")
            print(f"    ein: {grant.ein}")
            print(f"    recipient_name: {grant.recipient_name}")
            print(f"    normalized_recipient_name: {grant.normalized_recipient_name}")
            print(f"    recipient_ein: {grant.recipient_ein}")
            print(f"    recipient_type: {grant.recipient_type}")
            print(f"    recipient_address: {grant.recipient_address}")
            print(f"    recipient_relationship: {grant.recipient_relationship}")
            print(f"    grant_amount: {grant.grant_amount}")
            print(f"    grant_purpose: {grant.grant_purpose}")
            print(f"    foundation_status_of_recipient: {grant.foundation_status_of_recipient}")
            print(f"    grant_monitoring_procedures: {grant.grant_monitoring_procedures}")
            print(f"    tax_year: {grant.tax_year}")
            print(f"    schedule_part: {grant.schedule_part}")

        print(f"\n[GRANT ANALYSIS BAML OBJECT]")
        if result.grant_analysis:
            analysis = result.grant_analysis[0]
            print(f"  FoundationGrantAnalysis:")
            print(f"    ein: {analysis.ein}")
            print(f"    tax_year: {analysis.tax_year}")
            print(f"    total_grants_count: {analysis.total_grants_count}")
            print(f"    total_grants_amount: {analysis.total_grants_amount}")
            print(f"    average_grant_size: {analysis.average_grant_size}")
            print(f"    median_grant_amount: {analysis.median_grant_amount}")
            print(f"    large_grants_count: {analysis.large_grants_count}")
            print(f"    medium_grants_count: {analysis.medium_grants_count}")
            print(f"    small_grants_count: {analysis.small_grants_count}")
            print(f"    grant_size_strategy: {analysis.grant_size_strategy}")
            print(f"    funding_focus_areas: {analysis.funding_focus_areas}")
            print(f"    impact_grant_percentage: {analysis.impact_grant_percentage}")
            print(f"    flexible_funding_percentage: {analysis.flexible_funding_percentage}")
            print(f"    top_grant_purposes: {analysis.top_grant_purposes}")
            print(f"    data_source: {analysis.data_source}")

        print(f"\n[FOUNDATION CLASSIFICATION BAML OBJECT]")
        if result.foundation_classification:
            classification = result.foundation_classification[0]
            print(f"  FoundationClassification:")
            print(f"    ein: {classification.ein}")
            print(f"    tax_year: {classification.tax_year}")
            print(f"    foundation_type: {classification.foundation_type}")
            print(f"    foundation_size_category: {classification.foundation_size_category}")
            print(f"    grant_making_approach: {classification.grant_making_approach}")
            print(f"    funding_model: {classification.funding_model}")
            print(f"    geographic_scope: {classification.geographic_scope}")
            print(f"    professional_management: {classification.professional_management}")
            print(f"    risk_tolerance: {classification.risk_tolerance}")
            print(f"    grant_accessibility_score: {classification.grant_accessibility_score}")
            print(f"    sector_focus: {classification.sector_focus}")
            print(f"    grant_seeker_recommendations: {classification.grant_seeker_recommendations}")
            print(f"    data_source: {classification.data_source}")

        print(f"\n[INVESTMENT ANALYSIS BAML OBJECT]")
        if result.investment_analysis:
            investment = result.investment_analysis[0]
            print(f"  InvestmentAnalysis:")
            print(f"    ein: {investment.ein}")
            print(f"    tax_year: {investment.tax_year}")
            print(f"    total_investment_value: {investment.total_investment_value}")
            print(f"    total_investment_count: {investment.total_investment_count}")
            print(f"    portfolio_diversification_score: {investment.portfolio_diversification_score}")
            print(f"    equity_percentage: {investment.equity_percentage}")
            print(f"    fixed_income_percentage: {investment.fixed_income_percentage}")
            print(f"    alternative_investments_percentage: {investment.alternative_investments_percentage}")
            print(f"    sustainable_grant_capacity: {investment.sustainable_grant_capacity}")
            print(f"    grant_funding_stability: {investment.grant_funding_stability}")
            print(f"    investment_strategy_type: {investment.investment_strategy_type}")
            print(f"    grant_capacity_trend: {investment.grant_capacity_trend}")
            print(f"    multi_year_grant_feasibility: {investment.multi_year_grant_feasibility}")
            print(f"    endowment_sustainability_years: {investment.endowment_sustainability_years}")
            print(f"    data_source: {investment.data_source}")

        print(f"\n[INVESTMENT HOLDINGS BAML OBJECTS] (All {len(result.investment_holdings)} Holdings)")
        for i, holding in enumerate(result.investment_holdings):
            print(f"  InvestmentHolding[{i}]:")
            print(f"    ein: {holding.ein}")
            print(f"    tax_year: {holding.tax_year}")
            print(f"    investment_type: {holding.investment_type}")
            print(f"    investment_description: {holding.investment_description}")
            print(f"    book_value: {holding.book_value}")
            print(f"    fair_market_value: {holding.fair_market_value}")
            print(f"    investment_category: {holding.investment_category}")
            print(f"    acquisition_date: {holding.acquisition_date}")
            print(f"    cost_basis: {holding.cost_basis}")

        print(f"\n[EXECUTION METADATA BAML OBJECT]")
        metadata = result.execution_metadata
        print(f"  XML990PFExecutionMetadata:")
        print(f"    execution_time_ms: {metadata.execution_time_ms}")
        print(f"    organizations_processed: {metadata.organizations_processed}")
        print(f"    xml_files_found: {metadata.xml_files_found}")
        print(f"    xml_files_downloaded: {metadata.xml_files_downloaded}")
        print(f"    xml_files_parsed: {metadata.xml_files_parsed}")
        print(f"    cache_hits: {metadata.cache_hits}")
        print(f"    cache_misses: {metadata.cache_misses}")
        print(f"    cache_hit_rate: {metadata.cache_hit_rate}")
        print(f"    total_officers_extracted: {metadata.total_officers_extracted}")
        print(f"    total_grants_extracted: {metadata.total_grants_extracted}")
        print(f"    total_investments_extracted: {metadata.total_investments_extracted}")
        print(f"    parsing_errors: {metadata.parsing_errors}")
        print(f"    download_errors: {metadata.download_errors}")

        print(f"\n[QUALITY ASSESSMENT BAML OBJECT]")
        quality = result.quality_assessment
        print(f"  XML990PFQualityAssessment:")
        print(f"    overall_success_rate: {quality.overall_success_rate}")
        print(f"    schema_validation_rate: {quality.schema_validation_rate}")
        print(f"    officer_data_completeness: {quality.officer_data_completeness}")
        print(f"    grant_data_completeness: {quality.grant_data_completeness}")
        print(f"    investment_data_completeness: {quality.investment_data_completeness}")
        print(f"    financial_data_completeness: {quality.financial_data_completeness}")
        print(f"    governance_data_completeness: {quality.governance_data_completeness}")
        print(f"    data_freshness_score: {quality.data_freshness_score}")

        print(f"=" * 60)

        print(f"\n[EXTRACTION RESULTS SUMMARY]")
        print(f"Organizations Processed: {result.execution_metadata.organizations_processed}")
        print(f"XML Files Processed: {len(result.xml_files_processed)}")
        print(f"Officers Extracted: {len(result.officers)}")
        print(f"Grants Paid: {len(result.grants_paid)}")
        print(f"Investment Holdings: {len(result.investment_holdings)}")
        print(f"Excise Tax Records: {len(result.excise_tax_data)}")
        print(f"Payout Requirements: {len(result.payout_requirements)}")
        print(f"Governance Records: {len(result.governance_indicators)}")
        print(f"Financial Summaries: {len(result.financial_summaries)}")
        print(f"Execution Time: {execution_time:.1f}ms")

        # [0] FOUNDATION CONTACT INFORMATION (Grant Application Details)
        print(f"\\n[0] FOUNDATION CONTACT INFORMATION - GRANT APPLICATION")
        if result.contact_info:
            contact = result.contact_info[0]
            print(f"  Foundation Name: {contact.foundation_name}")
            if contact.address_line_1:
                print(f"  Address: {contact.address_line_1}")
                if contact.address_line_2:
                    print(f"           {contact.address_line_2}")
                print(f"           {contact.city}, {contact.state} {contact.zip_code}")
            if contact.phone_number:
                print(f"  Phone: {contact.phone_number}")
            if contact.principal_officer_name:
                print(f"  Principal Officer: {contact.principal_officer_name}")
                if contact.principal_officer_title:
                    print(f"  Title: {contact.principal_officer_title}")
        else:
            print("  [WARNING] No contact information extracted")

        # [1] FOUNDATION OFFICERS (Grant Decision Makers)
        print(f"\n[1] FOUNDATION OFFICERS - GRANT DECISION MAKERS")
        if result.officers:
            print(f"  Total Officers: {len(result.officers)}")
            for i, officer in enumerate(result.officers, 1):
                print(f"    {i}. {officer.person_name} - {officer.title}")
                print(f"       Hours/Week: {officer.average_hours_per_week or 'N/A'}")
                if officer.compensation:
                    print(f"       Compensation: ${officer.compensation:,.2f}")
        else:
            print("  [WARNING] No officers extracted")

        # [2] GRANTS PAID (Grant Distribution Intelligence)
        print(f"\n[2] GRANTS PAID - FOUNDATION DISTRIBUTION PATTERNS")
        if result.grants_paid:
            print(f"  Total Grants: {len(result.grants_paid)}")
            total_granted = sum(grant.grant_amount for grant in result.grants_paid)
            print(f"  Total Amount Granted: ${total_granted:,.2f}")

            print(f"  All Grants:")
            for i, grant in enumerate(result.grants_paid, 1):
                print(f"    {i}. {grant.recipient_name}")
                print(f"       Amount: ${grant.grant_amount:,.2f}")
                print(f"       Purpose: {grant.grant_purpose[:80] if grant.grant_purpose else 'N/A'}...")
        else:
            print("  [WARNING] No grants extracted")

        # [3] FINANCIAL CAPACITY (Grant Making Capacity)
        print(f"\n[3] FINANCIAL CAPACITY - GRANT MAKING ABILITY")
        if result.financial_summaries:
            financial = result.financial_summaries[0]
            print(f"  Total Assets: ${financial.total_assets:,.2f}" if financial.total_assets else "  Total Assets: N/A")
            print(f"  Total Revenue: ${financial.total_revenue:,.2f}" if financial.total_revenue else "  Total Revenue: N/A")
            print(f"  Corporate Stock Investments: ${financial.investments_corporate_stock:,.2f}" if financial.investments_corporate_stock else "  Corporate Stock: N/A")
            print(f"  Corporate Bond Investments: ${financial.investments_corporate_bonds:,.2f}" if financial.investments_corporate_bonds else "  Corporate Bonds: N/A")
        else:
            print("  [WARNING] No financial summaries extracted")

        # [4] PAYOUT REQUIREMENTS (5% Distribution Rule)
        print(f"\n[4] PAYOUT REQUIREMENTS - MANDATORY DISTRIBUTION ANALYSIS")
        if result.payout_requirements:
            payout = result.payout_requirements[0]
            print(f"  Average Monthly FMV: ${payout.average_monthly_fair_market_value:,.2f}" if payout.average_monthly_fair_market_value else "  Average Monthly FMV: N/A")
            print(f"  Minimum Investment Return (5%): ${payout.minimum_investment_return:,.2f}" if payout.minimum_investment_return else "  Minimum Return: N/A")
            print(f"  Distributable Amount Required: ${payout.distributable_amount:,.2f}" if payout.distributable_amount else "  Distributable Amount: N/A")
            print(f"  Qualifying Distributions Made: ${payout.qualifying_distributions_made:,.2f}" if payout.qualifying_distributions_made else "  Distributions Made: N/A")
            print(f"  Excess Distributions: ${payout.excess_distributions:,.2f}" if payout.excess_distributions else "  Excess: N/A")
            print(f"  Underdistributions: ${payout.underdistributions:,.2f}" if payout.underdistributions else "  Under: N/A")
        else:
            print("  [WARNING] No payout requirements extracted")

        # [5] GOVERNANCE (Foundation Management)
        print(f"\n[5] GOVERNANCE - FOUNDATION MANAGEMENT STRUCTURE")
        if result.governance_indicators:
            governance = result.governance_indicators[0]
            print(f"  Operating Foundation: {'Yes' if governance.operating_foundation else 'No'}")
            print(f"  Private Foundation Status: {'Yes' if governance.private_foundation_status else 'No'}")
            print(f"  Grant Making Procedures: {'Yes' if governance.grant_making_procedures else 'No'}")
            print(f"  Grant Monitoring Procedures: {'Yes' if governance.grant_monitoring_procedures else 'No'}")
            print(f"  Website Grant Process: {'Yes' if governance.website_grant_application_process else 'No'}")
        else:
            print("  [WARNING] No governance indicators extracted")

        # [6] GRANT RESEARCH ASSESSMENT
        print(f"\n[6] GRANT RESEARCH INTELLIGENCE ASSESSMENT")

        # Grant Making Capacity
        grant_capacity = "Unknown"
        if result.payout_requirements and result.payout_requirements[0].distributable_amount:
            required_dist = result.payout_requirements[0].distributable_amount
            if required_dist >= 10000000:  # $10M+
                grant_capacity = "Major ($10M+ required distribution)"
            elif required_dist >= 1000000:  # $1M+
                grant_capacity = "Significant ($1M+ required distribution)"
            elif required_dist >= 100000:  # $100K+
                grant_capacity = "Moderate ($100K+ required distribution)"
            else:
                grant_capacity = "Limited (<$100K required distribution)"

        # Grant Process Sophistication
        process_sophistication = "Unknown"
        if result.governance_indicators:
            governance = result.governance_indicators[0]
            sophistication_score = sum([
                governance.grant_making_procedures or False,
                governance.grant_monitoring_procedures or False,
                governance.website_grant_application_process or False
            ])
            if sophistication_score >= 2:
                process_sophistication = "High (formal procedures)"
            elif sophistication_score == 1:
                process_sophistication = "Medium (some procedures)"
            else:
                process_sophistication = "Low (minimal procedures)"

        # Historical Grant Activity
        grant_activity = "Unknown"
        if result.grants_paid:
            grant_count = len(result.grants_paid)
            if grant_count >= 20:
                grant_activity = "Very Active (20+ grants)"
            elif grant_count >= 10:
                grant_activity = "Active (10+ grants)"
            elif grant_count >= 5:
                grant_activity = "Moderate (5+ grants)"
            else:
                grant_activity = "Limited (<5 grants)"

        print(f"  Grant Making Capacity: {grant_capacity}")
        print(f"  Grant Process Sophistication: {process_sophistication}")
        print(f"  Historical Grant Activity: {grant_activity}")
        print(f"  Foundation Leadership Contact: {'Available' if result.officers else 'Limited'}")

        # [7] GRANT DISTRIBUTION INTELLIGENCE (Advanced Analysis)
        print(f"\\n[7] GRANT DISTRIBUTION INTELLIGENCE - STRATEGIC ANALYSIS")
        if result.grant_analysis:
            analysis = result.grant_analysis[0]
            print(f"  Grant Size Strategy: {analysis.grant_size_strategy}")
            print(f"  Average Grant Size: ${analysis.average_grant_size:,.2f}")
            print(f"  Median Grant Size: ${analysis.median_grant_amount:,.2f}" if analysis.median_grant_amount else "  Median Grant Size: N/A")
            print(f"  Grant Size Distribution:")
            print(f"    • Large Grants (>=$100K): {analysis.large_grants_count}")
            print(f"    • Medium Grants ($10K-$99K): {analysis.medium_grants_count}")
            print(f"    • Small Grants (<$10K): {analysis.small_grants_count}")

            if analysis.funding_focus_areas:
                print(f"  Funding Focus Areas: {', '.join(analysis.funding_focus_areas)}")

            if analysis.impact_grant_percentage:
                print(f"  Impact Grant Emphasis: {analysis.impact_grant_percentage:.1f}% of grants")

            if analysis.flexible_funding_percentage:
                print(f"  Flexible Funding: {analysis.flexible_funding_percentage:.1f}% of grants")

            if analysis.top_grant_purposes:
                print(f"  Top Grant Purposes: {', '.join(analysis.top_grant_purposes[:3])}")
        else:
            print("  [WARNING] No grant analysis available")

        # [8] FOUNDATION CLASSIFICATION (Strategic Positioning)
        print(f"\\n[8] FOUNDATION CLASSIFICATION - STRATEGIC POSITIONING")
        if result.foundation_classification:
            classification = result.foundation_classification[0]
            print(f"  Foundation Type: {classification.foundation_type}")
            print(f"  Size Category: {classification.foundation_size_category}")
            print(f"  Grant-Making Approach: {classification.grant_making_approach}")
            print(f"  Funding Model: {classification.funding_model}")
            print(f"  Professional Management: {classification.professional_management}")
            print(f"  Operational Sophistication: {classification.operational_sophistication}")
            print(f"  Risk Tolerance: {classification.risk_tolerance}")
            print(f"  Grant Accessibility Score: {classification.grant_accessibility_score:.2f}/1.0")

            if classification.sector_focus:
                print(f"  Sector Focus: {', '.join(classification.sector_focus)}")

            if classification.unique_value_proposition:
                print(f"  Unique Value: {classification.unique_value_proposition}")

            if classification.grant_seeker_recommendations:
                print(f"  Grant Strategy Recommendations:")
                for i, rec in enumerate(classification.grant_seeker_recommendations, 1):
                    print(f"    {i}. {rec}")
        else:
            print("  [WARNING] No foundation classification available")

        # [9] INVESTMENT ANALYSIS (Grant Capacity Assessment)
        print(f"\\n[9] INVESTMENT ANALYSIS - GRANT CAPACITY ASSESSMENT")
        if result.investment_analysis:
            analysis = result.investment_analysis[0]
            print(f"  Total Investment Value: ${analysis.total_investment_value:,.2f}")
            print(f"  Investment Holdings: {analysis.total_investment_count}")
            print(f"  Portfolio Diversification: {analysis.portfolio_diversification_score:.2f}/1.0")
            print(f"  Investment Strategy: {analysis.investment_strategy_type}")
            print(f"  Portfolio Allocation:")
            print(f"    • Equity: {analysis.equity_percentage:.1f}%")
            print(f"    • Fixed Income: {analysis.fixed_income_percentage:.1f}%")
            print(f"    • Cash/Equivalents: {analysis.cash_equivalent_percentage:.1f}%")
            print(f"    • Alternative: {analysis.alternative_investments_percentage:.1f}%")
            print(f"  Grant Capacity Intelligence:")
            print(f"    • Sustainable Grant Capacity: ${analysis.sustainable_grant_capacity:,.2f}/year")
            print(f"    • Grant Funding Stability: {analysis.grant_funding_stability}")
            print(f"    • Grant Capacity Trend: {analysis.grant_capacity_trend}")
            print(f"    • Multi-Year Grant Feasibility: {analysis.multi_year_grant_feasibility}")
            print(f"  Investment Risk Profile:")
            print(f"    • Volatility Assessment: {analysis.investment_volatility_assessment}")
            print(f"    • Liquidity Assessment: {analysis.liquidity_assessment}")
            print(f"    • Professional Management: {'Yes' if analysis.professional_management_indicators else 'No'}")
            if analysis.endowment_sustainability_years:
                print(f"    • Endowment Sustainability: {analysis.endowment_sustainability_years} years")
        else:
            print("  [WARNING] No investment analysis available")

        # Overall Foundation Intelligence Score
        intelligence_components = [
            bool(result.contact_info and len(result.contact_info) > 0),
            bool(result.officers and len(result.officers) > 0),
            bool(result.grants_paid and len(result.grants_paid) > 0),
            bool(result.grant_analysis and len(result.grant_analysis) > 0),
            bool(result.foundation_classification and len(result.foundation_classification) > 0),
            bool(result.investment_analysis and len(result.investment_analysis) > 0),
            bool(result.financial_summaries and len(result.financial_summaries) > 0),
            bool(result.payout_requirements and len(result.payout_requirements) > 0),
            bool(result.governance_indicators and len(result.governance_indicators) > 0)
        ]

        success_count = sum(intelligence_components)
        overall_success = success_count >= 7  # At least 7 out of 9 components

        print(f"\n[FOUNDATION INTELLIGENCE VALIDATION]")
        print(f"Foundation Contact Info: {'[SUCCESS]' if intelligence_components[0] else '[FAILED]'}")
        print(f"Foundation Officers: {'[SUCCESS]' if intelligence_components[1] else '[FAILED]'}")
        print(f"Grant Distribution Data: {'[SUCCESS]' if intelligence_components[2] else '[FAILED]'}")
        print(f"Grant Distribution Analysis: {'[SUCCESS]' if intelligence_components[3] else '[FAILED]'}")
        print(f"Foundation Classification: {'[SUCCESS]' if intelligence_components[4] else '[FAILED]'}")
        print(f"Investment Analysis: {'[SUCCESS]' if intelligence_components[5] else '[FAILED]'}")
        print(f"Financial Capacity: {'[SUCCESS]' if intelligence_components[6] else '[FAILED]'}")
        print(f"Payout Requirements: {'[SUCCESS]' if intelligence_components[7] else '[FAILED]'}")
        print(f"Governance Structure: {'[SUCCESS]' if intelligence_components[8] else '[FAILED]'}")
        print(f"Overall Foundation Intelligence: {'[SUCCESS]' if overall_success else '[FAILED]'}")

        return overall_success

    except Exception as e:
        print(f"\n[ERROR] 990-PF test failed: {e}")
        return False

async def main():
    """Run 990-PF foundation intelligence test"""
    print("[990-PF FOUNDATION INTELLIGENCE TEST]")
    print("Testing Fauquier Health Foundation - major private foundation analysis")

    success = await test_990pf_fauquier_foundation()

    if success:
        print(f"\n[OVERALL SUCCESS] 990-PF Parser foundation intelligence extraction!")
        print(f"• Foundation Leadership: Grant decision maker contacts [OK]")
        print(f"• Grant Distribution: Historical grant patterns and recipients [OK]")
        print(f"• Financial Capacity: Asset base and grant making ability [OK]")
        print(f"• Payout Requirements: Mandatory 5% distribution analysis [OK]")
        print(f"• Governance Structure: Grant making procedures and policies [OK]")
        print(f"\nFoundation grant research intelligence complete!")
    else:
        print(f"\n[OVERALL FAILED] 990-PF foundation intelligence needs enhancement")

if __name__ == "__main__":
    asyncio.run(main())