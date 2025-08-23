#!/usr/bin/env python3
"""
ChatGPT App Prototype Testing Scripts
Extracts AI prompts from processors for manual testing in ChatGPT web app

This tool extracts prompts from:
1. AI Lite Scorer (ANALYZE tab)
2. AI Heavy Researcher (EXAMINE tab)  
3. AI Heavy Dossier Builder

Generates formatted prompts with sample data for testing in ChatGPT app
before implementing actual OpenAI API integration.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.processors.analysis.ai_lite_scorer import (
    AILiteScorer, AILiteRequest, ProfileContext, CandidateData, 
    RequestMetadata, FundingHistory, ExistingAnalysis
)
from src.processors.analysis.ai_heavy_researcher import (
    AIHeavyResearcher, AIHeavyRequest, ContextData, ContextProfileData,
    AILiteResults, TargetPreliminaryData, ResearchFocus, ResearchMetadata
)

logger = logging.getLogger(__name__)

class ChatGPTPromptExtractor:
    """
    Extracts and formats AI prompts for testing in ChatGPT app
    
    Creates ready-to-use prompts with sample data that can be
    copy-pasted into ChatGPT web interface for testing
    """
    
    def __init__(self):
        self.ai_lite_scorer = AILiteScorer()
        self.ai_heavy_researcher = AIHeavyResearcher()
        
    def create_sample_ai_lite_request(self) -> AILiteRequest:
        """Create sample AI Lite request with realistic data"""
        
        # Sample organization profile
        profile_context = ProfileContext(
            organization_name="Heroes Bridge Foundation",
            mission_statement="Supporting military veterans and their families through comprehensive health and wellness programs",
            focus_areas=["veteran support", "mental health", "family services", "healthcare access"],
            ntee_codes=["B25", "E20", "F30"],
            government_criteria=["health", "veteran_affairs", "mental_health"],
            keywords=["veterans", "PTSD", "family support", "mental health", "healthcare"],
            geographic_scope="National",
            funding_history=FundingHistory(
                typical_grant_size="$100,000-500,000",
                annual_budget="$2.5M", 
                grant_making_capacity="$750K"
            )
        )
        
        # Sample candidate opportunities
        candidates = [
            CandidateData(
                opportunity_id="foundation_opp_001",
                organization_name="Johnson Family Foundation",
                source_type="private_foundation",
                description="Supports health and wellness programs for military veterans with focus on PTSD treatment, family counseling, and reintegration services. Preference for evidence-based programs with measurable outcomes.",
                funding_amount=250000,
                application_deadline="2024-06-15",
                geographic_location="National",
                current_score=0.85,
                existing_analysis=ExistingAnalysis(
                    raw_score=0.78,
                    confidence_level=0.82,
                    match_factors=["veteran focus", "mental health alignment", "family services"]
                )
            ),
            CandidateData(
                opportunity_id="government_opp_002", 
                organization_name="Department of Veterans Affairs",
                source_type="government",
                description="Federal grant program supporting innovative approaches to veteran mental health care, including community-based interventions and family support systems.",
                funding_amount=500000,
                application_deadline="2024-04-30",
                geographic_location="National",
                current_score=0.92
            ),
            CandidateData(
                opportunity_id="corporate_opp_003",
                organization_name="TechCorp Veterans Initiative", 
                source_type="corporate",
                description="Corporate social responsibility program providing technology solutions and funding for veteran-focused nonprofits. Emphasis on digital mental health tools.",
                funding_amount=150000,
                application_deadline="2024-08-01",
                geographic_location="National", 
                current_score=0.67
            )
        ]
        
        # Request metadata
        request_metadata = RequestMetadata(
            batch_id="chatgpt_test_batch_001",
            profile_id="heroes_bridge_test",
            analysis_type="compatibility_scoring",
            model_preference="gpt-3.5-turbo",
            cost_limit=0.01,
            priority="standard"
        )
        
        return AILiteRequest(
            request_metadata=request_metadata,
            profile_context=profile_context,
            candidates=candidates
        )
    
    def create_sample_ai_heavy_request(self) -> AIHeavyRequest:
        """Create sample AI Heavy request with comprehensive data"""
        
        # Research metadata
        research_metadata = ResearchMetadata(
            research_id="chatgpt_heavy_test_001",
            profile_id="heroes_bridge_test",
            target_organization="Johnson Family Foundation",
            analysis_depth="comprehensive",
            model_preference="gpt-4",
            cost_budget=0.25,
            priority="high"
        )
        
        # Organization context
        profile_context = ContextProfileData(
            organization_name="Heroes Bridge Foundation",
            mission_statement="Supporting military veterans and their families through comprehensive health and wellness programs",
            strategic_priorities=["PTSD treatment expansion", "family counseling services", "community reintegration"],
            leadership_team=["Dr. Sarah Johnson (Executive Director)", "Col. Michael Smith (Program Director)", "Lisa Chen (Development Director)"],
            recent_grants=["$300K Robert Wood Johnson Foundation", "$150K Ford Foundation", "$200K VA Community Partnership Grant"],
            funding_capacity="$1M annually",
            geographic_scope="National"
        )
        
        # AI Lite preliminary results
        ai_lite_results = AILiteResults(
            compatibility_score=0.89,
            strategic_value="high",
            risk_assessment=["high_competition", "reporting_intensive"],
            priority_rank=1,
            funding_likelihood=0.82,
            strategic_rationale="Excellent mission alignment with Johnson Family Foundation's veteran health focus. Strong track record and proven outcomes position Heroes Bridge as competitive candidate.",
            action_priority="immediate"
        )
        
        # Target organization data
        target_data = TargetPreliminaryData(
            organization_name="Johnson Family Foundation",
            basic_info="Private family foundation established in 1995, focusing on health and wellness programs for underserved populations including veterans and military families.",
            funding_capacity="$3-5M annually",
            geographic_focus="National with preference for West Coast",
            known_board_members=["Robert Johnson (Chairman)", "Dr. Patricia Wilson (Health Program Director)", "James Martinez (Finance Committee)"],
            recent_grants_given=["$400K for PTSD research", "$250K for family therapy programs", "$300K for community health centers"],
            website_url="https://johnsonfamilyfoundation.org",
            annual_revenue="$15M endowment"
        )
        
        # Research focus areas
        research_focus = ResearchFocus(
            priority_areas=["strategic_partnership", "funding_approach", "board_connections"],
            risk_mitigation=["competition_analysis", "application_requirements"],
            intelligence_gaps=["decision_makers", "funding_timeline", "preferred_grantee_profile"]
        )
        
        # Context data
        context_data = ContextData(
            profile_context=profile_context,
            ai_lite_results=ai_lite_results,
            target_preliminary_data=target_data
        )
        
        return AIHeavyRequest(
            request_metadata=research_metadata,
            context_data=context_data,
            research_focus=research_focus
        )
    
    def extract_ai_lite_prompt(self) -> Dict[str, Any]:
        """Extract AI Lite prompt formatted for ChatGPT app testing"""
        
        # Create sample request
        sample_request = self.create_sample_ai_lite_request()
        
        # Generate prompt using processor logic
        prompt = self.ai_lite_scorer._create_enhanced_batch_prompt(sample_request)
        
        return {
            "prompt_type": "AI Lite Scorer (ANALYZE Tab)",
            "model_recommendation": "GPT-3.5 Turbo",
            "estimated_cost": "$0.001-0.003 per test",
            "description": "Cost-effective candidate analysis for grant opportunity prioritization",
            "instructions": [
                "Copy the full prompt below into ChatGPT",
                "The prompt includes sample organization and opportunity data",
                "Expected response is JSON format with compatibility scores",
                "Validate that response structure matches AILiteAnalysis model",
                "Test with different organization profiles to verify consistency"
            ],
            "sample_request_data": {
                "organization": sample_request.profile_context.model_dump(),
                "candidates": [candidate.model_dump() for candidate in sample_request.candidates],
                "metadata": sample_request.request_metadata.model_dump()
            },
            "full_prompt": prompt,
            "expected_response_format": {
                "opportunity_id": {
                    "compatibility_score": "float 0.0-1.0",
                    "strategic_value": "high|medium|low",
                    "risk_assessment": ["array of risk factors"],
                    "priority_rank": "integer ranking",
                    "funding_likelihood": "float 0.0-1.0", 
                    "strategic_rationale": "2-sentence analysis",
                    "action_priority": "immediate|planned|monitor",
                    "confidence_level": "float 0.0-1.0"
                }
            },
            "validation_checklist": [
                "Response is valid JSON format",
                "All required fields present for each opportunity",
                "Compatibility scores between 0.0-1.0",
                "Strategic value is high/medium/low",
                "Risk assessment contains valid risk factors",
                "Priority rankings are unique integers",
                "Strategic rationale is concise and relevant",
                "Action priority matches enum values"
            ]
        }
    
    def extract_ai_heavy_prompt(self) -> Dict[str, Any]:
        """Extract AI Heavy prompt formatted for ChatGPT app testing"""
        
        # Create sample request
        sample_request = self.create_sample_ai_heavy_request()
        
        # Generate prompt using processor logic
        prompt = self.ai_heavy_researcher._create_comprehensive_research_prompt(sample_request)
        
        return {
            "prompt_type": "AI Heavy Researcher (EXAMINE Tab)",
            "model_recommendation": "GPT-4",
            "estimated_cost": "$0.15-0.30 per test",
            "description": "Comprehensive strategic dossier generation with grant application intelligence",
            "instructions": [
                "Copy the full prompt below into ChatGPT (GPT-4 recommended)",
                "The prompt includes comprehensive organization and target data",
                "Expected response is extensive JSON with strategic dossier",
                "Pay attention to grant application intelligence section",
                "Test with different target organizations to verify adaptability"
            ],
            "sample_request_data": {
                "organization": sample_request.context_data.profile_context.model_dump(),
                "target": sample_request.context_data.target_preliminary_data.model_dump(),
                "ai_lite_results": sample_request.context_data.ai_lite_results.model_dump(),
                "research_focus": sample_request.research_focus.model_dump(),
                "metadata": sample_request.request_metadata.model_dump()
            },
            "full_prompt": prompt,
            "expected_response_format": {
                "strategic_dossier": {
                    "partnership_assessment": "Mission alignment and strategic value",
                    "funding_strategy": "Optimal approach and requirements",
                    "competitive_analysis": "Market positioning and advantages", 
                    "relationship_strategy": "Board connections and engagement",
                    "financial_analysis": "Funding capacity and optimization",
                    "risk_assessment": "Risks and mitigation strategies",
                    "grant_application_intelligence": "Detailed application requirements",
                    "recommended_approach": "Strategic pursuit decision"
                },
                "action_plan": {
                    "immediate_actions": "Next steps with timelines",
                    "six_month_roadmap": "Strategic milestone planning",
                    "success_metrics": "Measurable outcomes",
                    "investment_recommendation": "Resource allocation"
                }
            },
            "validation_checklist": [
                "Response is valid JSON format",
                "Strategic dossier contains all required sections",
                "Grant application intelligence is detailed and actionable",
                "Partnership assessment includes scored metrics",
                "Funding strategy provides specific amounts and timing",
                "Relationship strategy includes specific contact approaches",
                "Risk assessment provides mitigation strategies",
                "Action plan includes specific, measurable items",
                "Recommended approach includes go/no-go decision"
            ]
        }
    
    def generate_test_scenarios(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate various test scenarios for comprehensive prompt testing"""
        
        return {
            "ai_lite_scenarios": [
                {
                    "scenario": "High-alignment opportunities",
                    "description": "Test with opportunities that closely match organization mission",
                    "expected_outcome": "High compatibility scores, immediate action priorities"
                },
                {
                    "scenario": "Mixed-alignment batch",
                    "description": "Test with mix of high, medium, and low alignment opportunities",
                    "expected_outcome": "Varied scores with clear differentiation"
                },
                {
                    "scenario": "High-risk opportunities", 
                    "description": "Test with competitive or complex opportunities",
                    "expected_outcome": "Lower confidence scores, detailed risk assessments"
                },
                {
                    "scenario": "Small vs large funding amounts",
                    "description": "Test scoring consistency across different funding levels",
                    "expected_outcome": "Funding amount should not bias compatibility scoring"
                }
            ],
            "ai_heavy_scenarios": [
                {
                    "scenario": "Strategic partner opportunity",
                    "description": "Test with long-term strategic partnership potential",
                    "expected_outcome": "Comprehensive relationship strategy, multi-year planning"
                },
                {
                    "scenario": "Competitive funding opportunity",
                    "description": "Test with highly competitive major foundation",
                    "expected_outcome": "Detailed competitive analysis, differentiation strategy"
                },
                {
                    "scenario": "Board connection opportunity",
                    "description": "Test with known board member connections",
                    "expected_outcome": "Specific relationship leverage strategies"
                },
                {
                    "scenario": "Complex application requirements",
                    "description": "Test with opportunity having extensive application process", 
                    "expected_outcome": "Detailed grant application intelligence with LOE estimates"
                }
            ]
        }
    
    def generate_comprehensive_test_package(self, output_dir: str = "chatgpt_test_package") -> str:
        """Generate complete test package for ChatGPT app testing"""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate AI Lite test package
        ai_lite_package = self.extract_ai_lite_prompt()
        with open(output_path / "ai_lite_chatgpt_test.json", 'w') as f:
            json.dump(ai_lite_package, f, indent=2)
        
        # Generate AI Heavy test package
        ai_heavy_package = self.extract_ai_heavy_prompt()
        with open(output_path / "ai_heavy_chatgpt_test.json", 'w') as f:
            json.dump(ai_heavy_package, f, indent=2)
        
        # Generate test scenarios
        test_scenarios = self.generate_test_scenarios()
        with open(output_path / "test_scenarios.json", 'w') as f:
            json.dump(test_scenarios, f, indent=2)
        
        # Generate comprehensive README
        readme_content = self._generate_test_readme(ai_lite_package, ai_heavy_package, test_scenarios)
        with open(output_path / "README_ChatGPT_Testing.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # Generate quick start prompts (formatted for easy copy-paste)
        self._generate_quick_start_files(output_path, ai_lite_package, ai_heavy_package)
        
        return str(output_path)
    
    def _generate_test_readme(self, ai_lite_package: Dict, ai_heavy_package: Dict, scenarios: Dict) -> str:
        """Generate comprehensive README for ChatGPT testing"""
        
        return f"""# ChatGPT App Testing Package for Catalynx AI Analysis

Generated on: {datetime.now().isoformat()}

## Overview

This package contains extracted prompts from the Catalynx AI analysis systems for testing in ChatGPT web app before implementing full OpenAI API integration.

## Package Contents

### 1. AI Lite Scorer Testing (`ai_lite_chatgpt_test.json`)
- **Purpose**: Cost-effective candidate analysis for ANALYZE tab
- **Model**: GPT-3.5 Turbo recommended
- **Cost**: ~$0.001-0.003 per test
- **Processing**: Batch analysis of 3-15 opportunities

### 2. AI Heavy Researcher Testing (`ai_heavy_chatgpt_test.json`) 
- **Purpose**: Comprehensive strategic dossier for EXAMINE tab
- **Model**: GPT-4 required
- **Cost**: ~$0.15-0.30 per test
- **Processing**: Individual deep analysis with grant application intelligence

### 3. Test Scenarios (`test_scenarios.json`)
- Multiple testing scenarios for each AI system
- Covers various organization types and opportunity profiles
- Validation criteria for each scenario

## Quick Start Guide

### Step 1: AI Lite Testing
1. Open `ai_lite_prompt.txt`
2. Copy entire prompt to ChatGPT 3.5
3. Verify JSON response structure
4. Test with scenarios from `test_scenarios.json`

### Step 2: AI Heavy Testing  
1. Open `ai_heavy_prompt.txt`
2. Copy entire prompt to ChatGPT 4 (required)
3. Verify comprehensive dossier structure
4. Test grant application intelligence section

### Step 3: Validation
1. Use validation checklists in each JSON file
2. Verify response structure matches expected format
3. Test multiple scenarios for consistency
4. Document any prompt refinements needed

## Expected Response Structures

### AI Lite Response
```json
{{
  "opportunity_id": {{
    "compatibility_score": 0.85,
    "strategic_value": "high",
    "risk_assessment": ["competition_level", "capacity_requirements"],
    "priority_rank": 1,
    "funding_likelihood": 0.75,
    "strategic_rationale": "Strong alignment with proven outcomes",
    "action_priority": "immediate",
    "confidence_level": 0.9
  }}
}}
```

### AI Heavy Response
```json
{{
  "strategic_dossier": {{
    "partnership_assessment": {{ ... }},
    "funding_strategy": {{ ... }},
    "grant_application_intelligence": {{ ... }},
    ...
  }},
  "action_plan": {{ ... }}
}}
```

## Testing Checklist

### AI Lite Testing
- [ ] Prompt generates valid JSON response
- [ ] All opportunities receive scores
- [ ] Compatibility scores between 0.0-1.0
- [ ] Strategic values are high/medium/low
- [ ] Risk assessments contain valid factors
- [ ] Priority rankings are unique
- [ ] Confidence levels are realistic

### AI Heavy Testing
- [ ] Comprehensive dossier generated
- [ ] Grant application intelligence detailed
- [ ] Partnership assessment scored
- [ ] Funding strategy specific
- [ ] Risk mitigation strategies provided
- [ ] Action plan actionable
- [ ] Recommended approach clear

## Troubleshooting

### Common Issues
1. **JSON Format Errors**: Ensure proper JSON syntax in response
2. **Missing Fields**: Verify all required fields present
3. **Invalid Values**: Check enum values match specifications
4. **Incomplete Analysis**: May need prompt refinement for thoroughness

### Prompt Refinement
- Document any ChatGPT response issues
- Note which sections need clarification
- Test prompt variations for optimization
- Validate refined prompts with multiple scenarios

## Integration Notes

After successful ChatGPT testing:
1. Incorporate refined prompts into AI processors
2. Implement proper error handling for API integration
3. Add response validation using Pydantic models
4. Test cost optimization with batch processing

## Test Results Documentation

Create test result files:
- `ai_lite_test_results.json`: AI Lite testing outcomes
- `ai_heavy_test_results.json`: AI Heavy testing outcomes  
- `prompt_refinements.md`: Notes on prompt improvements needed

## Support

For questions about this testing package:
- Review validation checklists in JSON files
- Check expected response formats
- Consult test scenarios for guidance
- Document issues for development team review
"""
    
    def _generate_quick_start_files(self, output_path: Path, ai_lite_package: Dict, ai_heavy_package: Dict):
        """Generate quick-start prompt files for easy copy-paste"""
        
        # AI Lite quick start prompt
        with open(output_path / "ai_lite_prompt.txt", 'w', encoding='utf-8') as f:
            f.write(f"""# AI Lite Scorer Prompt for ChatGPT 3.5 Testing
# Copy everything below this line into ChatGPT

{ai_lite_package['full_prompt']}
""")
        
        # AI Heavy quick start prompt  
        with open(output_path / "ai_heavy_prompt.txt", 'w', encoding='utf-8') as f:
            f.write(f"""# AI Heavy Researcher Prompt for ChatGPT 4 Testing  
# Copy everything below this line into ChatGPT 4 (GPT-4 required)

{ai_heavy_package['full_prompt']}
""")
        
        # Testing instructions
        with open(output_path / "TESTING_INSTRUCTIONS.md", 'w', encoding='utf-8') as f:
            f.write("""# Quick Testing Instructions

## AI Lite Testing (5-10 minutes)
1. Open `ai_lite_prompt.txt`
2. Copy entire prompt to ChatGPT 3.5
3. Paste and send
4. Verify JSON response structure
5. Check compatibility scores are 0.0-1.0
6. Ensure all opportunities have rankings

## AI Heavy Testing (10-15 minutes)  
1. Open `ai_heavy_prompt.txt`
2. Copy entire prompt to ChatGPT 4 (required)
3. Paste and send (may take 30-60 seconds)
4. Verify comprehensive dossier structure
5. Check grant application intelligence section
6. Ensure action plan is specific and actionable

## Success Criteria
- Valid JSON responses  
- All required fields present
- Realistic scores and assessments
- Actionable recommendations
- Consistent formatting

## Common Issues
- JSON formatting errors - check brackets and commas
- Missing fields - verify complete response structure  
- Unrealistic scores - may need prompt refinement
- Vague recommendations - add specificity requirements
""")

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ChatGPT Prompt Extraction Tool")
    parser.add_argument("--output-dir", default="chatgpt_test_package", help="Output directory for test package")
    parser.add_argument("--ai-lite-only", action="store_true", help="Extract AI Lite prompt only")
    parser.add_argument("--ai-heavy-only", action="store_true", help="Extract AI Heavy prompt only")
    args = parser.parse_args()
    
    # Initialize extractor
    extractor = ChatGPTPromptExtractor()
    
    if args.ai_lite_only:
        # Extract AI Lite only
        ai_lite_package = extractor.extract_ai_lite_prompt()
        output_path = Path(args.output_dir)
        output_path.mkdir(exist_ok=True)
        
        with open(output_path / "ai_lite_chatgpt_test.json", 'w') as f:
            json.dump(ai_lite_package, f, indent=2)
            
        print(f"AI Lite prompt extracted to: {output_path / 'ai_lite_chatgpt_test.json'}")
        
    elif args.ai_heavy_only:
        # Extract AI Heavy only
        ai_heavy_package = extractor.extract_ai_heavy_prompt()
        output_path = Path(args.output_dir)
        output_path.mkdir(exist_ok=True)
        
        with open(output_path / "ai_heavy_chatgpt_test.json", 'w') as f:
            json.dump(ai_heavy_package, f, indent=2)
            
        print(f"AI Heavy prompt extracted to: {output_path / 'ai_heavy_chatgpt_test.json'}")
        
    else:
        # Generate complete test package
        package_path = extractor.generate_comprehensive_test_package(args.output_dir)
        print(f"Complete ChatGPT test package generated at: {package_path}")
        print(f"Start with: {package_path}/README_ChatGPT_Testing.md")

if __name__ == "__main__":
    main()