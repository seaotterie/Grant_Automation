#!/usr/bin/env python3
"""
Generate GPT-5 Content for Masters Thesis Dossier
Real GPT-5 analysis for Heroes Bridge → Fauquier Health Foundation
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.openai_service import OpenAIService
from dotenv import load_dotenv

load_dotenv()

async def generate_gpt5_dossier_content():
    """Generate comprehensive GPT-5 content for masters thesis dossier"""
    
    print("=" * 80)
    print("GENERATING GPT-5 CONTENT FOR MASTERS THESIS DOSSIER")
    print("=" * 80)
    print("Heroes Bridge -> Fauquier Health Foundation Analysis")
    print("Using real GPT-5 models for masters thesis-level content")
    print("-" * 80)
    
    service = OpenAIService()
    
    if not service.client:
        print("ERROR: OpenAI service not initialized")
        return None
    
    # Load real data
    print("Loading real Heroes Bridge and Fauquier Health Foundation data...")
    
    fauquier_file = Path('data/source_data/nonprofits/300219424/propublica.json')
    heroes_file = Path('data/source_data/nonprofits/812827604/propublica.json')
    
    with open(fauquier_file, 'r') as f:
        fauquier_data = json.load(f)
    with open(heroes_file, 'r') as f:
        heroes_data = json.load(f)
    
    # Extract data
    fauquier_org = fauquier_data.get('organization', {})
    heroes_org = heroes_data.get('organization', {})
    fauquier_filings = fauquier_data.get('filings_with_data', [])
    heroes_filings = heroes_data.get('filings_with_data', [])
    fauquier_latest = fauquier_filings[0] if fauquier_filings else {}
    heroes_latest = heroes_filings[0] if heroes_filings else {}
    
    print(f"SUCCESS: Data loaded: {heroes_org.get('name')} -> {fauquier_org.get('name')}")
    
    dossier_content = {}
    
    # Executive Summary (GPT-5)
    print("\n1. Generating Executive Summary (GPT-5)...")
    exec_response = await service.create_completion(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "You are creating an executive summary for a masters thesis-level grant opportunity dossier. Provide comprehensive strategic overview with specific scores and recommendations."},
            {"role": "user", "content": f"""
            Create comprehensive executive summary for this real grant opportunity:
            
            OPPORTUNITY: {heroes_org.get('name')} (EIN: {heroes_org.get('ein')}) seeking funding from {fauquier_org.get('name')} (EIN: {fauquier_org.get('ein')})
            
            KEY FACTS:
            - Applicant Revenue: ${heroes_latest.get('totrevenue', 0):,}
            - Foundation Revenue: ${fauquier_latest.get('totrevenue', 0):,}  
            - Both located: Warrenton, VA
            - Veteran services → Health foundation
            
            Provide executive summary including:
            - Strategic alignment score (0-100)
            - Success probability percentage
            - Recommended funding amount
            - Key competitive advantages
            - Primary risks and mitigation
            - Final recommendation (PURSUE/DECLINE)
            """}
        ],
        max_tokens=800
    )
    
    dossier_content['executive_summary'] = exec_response.content
    print(f"   Generated: {len(exec_response.content)} characters")
    
    # Strategic Analysis (GPT-5)
    print("\n2. Generating Strategic Analysis (GPT-5)...")
    strategic_response = await service.create_completion(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "You are conducting strategic analysis for a masters thesis-level grant opportunity assessment. Provide detailed quantitative analysis with specific metrics."},
            {"role": "user", "content": f"""
            Conduct comprehensive strategic analysis:
            
            APPLICANT PROFILE:
            Name: {heroes_org.get('name')}
            EIN: {heroes_org.get('ein')}
            Revenue: ${heroes_latest.get('totrevenue', 0):,}
            Expenses: ${heroes_latest.get('totfuncexpns', 0):,}
            Net Assets: ${heroes_latest.get('totnetassets', 0):,}
            NTEE: {heroes_org.get('ntee_code')}
            Location: {heroes_org.get('city')}, {heroes_org.get('state')}
            
            FUNDING SOURCE:
            Name: {fauquier_org.get('name')}
            EIN: {fauquier_org.get('ein')}
            Revenue: ${fauquier_latest.get('totrevenue', 0):,}
            Assets: ${fauquier_latest.get('totnetassets', 0):,}
            NTEE: {fauquier_org.get('ntee_code')}
            Location: {fauquier_org.get('city')}, {fauquier_org.get('state')}
            
            Analyze:
            1. Mission alignment (score 0-100 with detailed rationale)
            2. Financial compatibility assessment
            3. Geographic synergy advantages
            4. Organizational capacity evaluation
            5. Market positioning strengths
            6. Success factors identification
            """}
        ],
        max_tokens=1200
    )
    
    dossier_content['strategic_analysis'] = strategic_response.content
    print(f"   Generated: {len(strategic_response.content)} characters")
    
    # Financial Analysis (GPT-5-Mini)
    print("\n3. Generating Financial Analysis (GPT-5-Mini)...")
    financial_response = await service.create_completion(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "You are conducting financial analysis for a grant funding decision. Provide detailed financial assessment with specific dollar amounts and ratios."},
            {"role": "user", "content": f"""
            Conduct detailed financial analysis:
            
            FOUNDATION FINANCIALS:
            Annual Revenue: ${fauquier_latest.get('totrevenue', 0):,}
            Total Expenses: ${fauquier_latest.get('totfuncexpns', 0):,}
            Net Assets: ${fauquier_latest.get('totnetassets', 0):,}
            Program Revenue: ${fauquier_latest.get('totprgmrevnue', 0):,}
            Investment Income: ${fauquier_latest.get('invstmntinc', 0):,}
            
            APPLICANT FINANCIALS:
            Annual Revenue: ${heroes_latest.get('totrevenue', 0):,}
            Total Expenses: ${heroes_latest.get('totfuncexpns', 0):,}
            Program Expenses: ${heroes_latest.get('totprgmexpns', 0):,}
            Net Assets: ${heroes_latest.get('totnetassets', 0):,}
            
            Analyze:
            1. Foundation grant-making capacity
            2. Optimal funding amount recommendation
            3. Applicant financial stability assessment
            4. Budget efficiency ratios
            5. Multi-year funding potential
            6. Financial risk assessment
            """}
        ],
        max_tokens=1000
    )
    
    dossier_content['financial_analysis'] = financial_response.content
    print(f"   Generated: {len(financial_response.content)} characters")
    
    # Implementation Strategy (GPT-5-Nano)
    print("\n4. Generating Implementation Strategy (GPT-5-Nano)...")
    implementation_response = await service.create_completion(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": "You are developing implementation strategy for a grant application. Provide detailed actionable plan with timelines."},
            {"role": "user", "content": f"""
            Develop implementation strategy for {heroes_org.get('name')} approaching {fauquier_org.get('name')}:
            
            CONTEXT:
            - Both organizations in Warrenton, VA
            - Veteran services seeking health foundation funding
            - Target amount: $25,000
            - Geographic proximity advantage
            
            Create implementation plan including:
            1. Pre-approach research phase (timeline)
            2. Relationship building strategy
            3. Proposal development milestones
            4. Stakeholder engagement plan
            5. Partnership development opportunities
            6. Success metrics and evaluation framework
            7. Risk mitigation strategies
            8. Follow-up and stewardship plan
            """}
        ],
        max_tokens=800
    )
    
    dossier_content['implementation_strategy'] = implementation_response.content
    print(f"   Generated: {len(implementation_response.content)} characters")
    
    # Save comprehensive content
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    complete_analysis = {
        'generation_timestamp': timestamp,
        'analysis_type': 'GPT5_MASTERS_THESIS_DOSSIER_CONTENT',
        'organizations': {
            'applicant': {
                'name': heroes_org.get('name'),
                'ein': heroes_org.get('ein'),
                'revenue': heroes_latest.get('totrevenue', 0),
                'location': f"{heroes_org.get('city')}, {heroes_org.get('state')}"
            },
            'funder': {
                'name': fauquier_org.get('name'),
                'ein': fauquier_org.get('ein'),
                'revenue': fauquier_latest.get('totrevenue', 0),
                'location': f"{fauquier_org.get('city')}, {fauquier_org.get('state')}"
            }
        },
        'gpt5_analysis_content': dossier_content,
        'processing_info': {
            'models_used': ['gpt-5', 'gpt-5-mini', 'gpt-5-nano'],
            'quality_level': 'Masters Thesis Level',
            'real_gpt5_processing': True,
            'simulation_mode': False
        }
    }
    
    output_file = f'gpt5_masters_dossier_content_{timestamp}.json'
    with open(output_file, 'w') as f:
        json.dump(complete_analysis, f, indent=2, default=str)
    
    print(f"\n" + "=" * 80)
    print("GPT-5 DOSSIER CONTENT GENERATION COMPLETE")
    print("=" * 80)
    print(f"Content generated: {len(dossier_content)} sections")
    print(f"Total characters: {sum(len(str(content)) for content in dossier_content.values()):,}")
    print(f"Results saved to: {output_file}")
    print("Ready for masters thesis dossier integration")
    
    return complete_analysis

async def main():
    """Main execution"""
    try:
        result = await generate_gpt5_dossier_content()
        if result:
            print("\nSUCCESS: GPT-5 dossier content generated")
            print("Next: Update complete_masters_thesis_dossier with real findings")
            return result
        else:
            print("\nFAILED: Could not generate GPT-5 content")
            return None
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(main())