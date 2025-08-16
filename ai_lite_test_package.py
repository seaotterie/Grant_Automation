"""
AI Lite Test Package for External Review
Simplified version of Catalynx AI Lite Scorer for testing with ChatGPT or other AI systems
"""

import json
from typing import Dict, List, Optional, Any

# Sample Organization Profile Data
SAMPLE_ORGANIZATION_PROFILE = {
    "name": "Community Tech Foundation",
    "mission_statement": "To bridge the digital divide and empower underserved communities through accessible technology education, resources, and sustainable digital infrastructure programs.",
    "focus_areas": ["digital_literacy", "stem_education", "community_development", "workforce_development"],
    "ntee_codes": ["P20", "P30", "S20"],  # Computer Science/Data Processing, Technology, Community Improvement
    "government_criteria": ["technology_innovation", "rural_development", "education_training", "economic_development"],
    "keywords": ["digital divide", "technology access", "computer training", "internet connectivity", "digital skills"],
    "geographic_scope": "Regional (Mid-Atlantic: VA, MD, DC)",
    "typical_grant_size": "$50,000-$250,000",
    "annual_budget": "$2.5M",
    "grant_seeking_capacity": "$750K annually"
}

# Sample Funding Opportunities (Candidates for Analysis)
SAMPLE_CANDIDATES = [
    {
        "opportunity_id": "tech_equity_001",
        "organization_name": "Digital Equity Foundation",
        "source_type": "Private Foundation",
        "description": "Technology Access Program supporting digital literacy initiatives in underserved communities. Focus on computer labs, internet access, and training programs for low-income families and seniors. Preference for organizations with existing community partnerships and measurable outcomes. Must demonstrate sustainable program model.",
        "funding_amount": 150000,
        "application_deadline": "2025-04-15",
        "geographic_location": "Mid-Atlantic Region",
        "current_score": 0.73,
        "additional_info": {
            "priority_areas": ["digital_literacy", "community_partnerships", "sustainability"],
            "application_requirements": ["detailed_budget", "outcome_metrics", "partnership_letters"],
            "past_grantees": ["similar community tech nonprofits"],
            "competitive_factors": "moderate_competition"
        }
    },
    {
        "opportunity_id": "workforce_tech_002", 
        "organization_name": "National Skills Development Corporation",
        "source_type": "Corporate Foundation",
        "description": "Workforce Technology Training Grants for programs that prepare unemployed and underemployed adults for technology careers. Must include job placement component and industry partnerships. Priority given to programs serving rural areas and minority communities. Requires 6-month outcome tracking.",
        "funding_amount": 300000,
        "application_deadline": "2025-03-01",
        "geographic_location": "National (Rural Priority)",
        "current_score": 0.68,
        "additional_info": {
            "priority_areas": ["workforce_development", "job_placement", "industry_partnerships"],
            "application_requirements": ["industry_partner_commitments", "placement_metrics", "rural_focus"],
            "past_grantees": ["workforce development organizations", "community colleges"],
            "competitive_factors": "high_competition"
        }
    },
    {
        "opportunity_id": "rural_broadband_003",
        "organization_name": "Virginia Rural Development Authority", 
        "source_type": "State Government",
        "description": "Rural Broadband Access Initiative providing grants for expanding internet infrastructure and digital literacy programming in rural Virginia communities. Must partner with local government and demonstrate community need. Includes both infrastructure and education components.",
        "funding_amount": 500000,
        "application_deadline": "2025-05-30",
        "geographic_location": "Rural Virginia",
        "current_score": 0.82,
        "additional_info": {
            "priority_areas": ["rural_development", "infrastructure", "government_partnerships"],
            "application_requirements": ["local_government_partnership", "needs_assessment", "community_support"],
            "past_grantees": ["rural nonprofits", "community development corporations"],
            "competitive_factors": "low_competition"
        }
    },
    {
        "opportunity_id": "stem_education_004",
        "organization_name": "STEM Learning Alliance",
        "source_type": "Private Foundation", 
        "description": "K-12 STEM Education Technology Grants supporting innovative technology integration in underperforming schools. Focus on hands-on learning, coding education, and teacher professional development. Must demonstrate measurable student outcome improvements and scalability potential.",
        "funding_amount": 200000,
        "application_deadline": "2025-06-15", 
        "geographic_location": "National",
        "current_score": 0.71,
        "additional_info": {
            "priority_areas": ["k12_education", "teacher_training", "student_outcomes"],
            "application_requirements": ["school_partnerships", "outcome_measurements", "scalability_plan"],
            "past_grantees": ["education nonprofits", "schools", "educational_technology_organizations"],
            "competitive_factors": "high_competition"
        }
    },
    {
        "opportunity_id": "senior_tech_005",
        "organization_name": "Elder Care Technology Fund",
        "source_type": "Private Foundation",
        "description": "Senior Technology Access Program providing tablets, internet access, and digital literacy training for seniors aged 65+. Focus on reducing social isolation and improving access to telehealth services. Must demonstrate cultural competency and accessibility accommodations.",
        "funding_amount": 75000,
        "application_deadline": "2025-02-28",
        "geographic_location": "Metro DC Area", 
        "current_score": 0.79,
        "additional_info": {
            "priority_areas": ["senior_services", "digital_inclusion", "health_access"],
            "application_requirements": ["cultural_competency", "accessibility_plan", "health_partnerships"],
            "past_grantees": ["senior_centers", "health_organizations", "community_nonprofits"],
            "competitive_factors": "moderate_competition"
        }
    }
]

# AI Lite Scoring Prompt Template
AI_LITE_SCORING_PROMPT = """
You are an expert grant strategist analyzing funding opportunities for optimal compatibility and strategic value.

ORGANIZATION PROFILE:
Name: {organization_name}
Mission: {mission_statement}
Focus Areas: {focus_areas}
NTEE Codes: {ntee_codes}
Government Criteria: {government_criteria}
Geographic Scope: {geographic_scope}
Typical Grant Size: {typical_grant_size}
Annual Budget: {annual_budget}

FUNDING OPPORTUNITY CANDIDATES FOR ANALYSIS:

{candidate_summaries}

ANALYSIS REQUIREMENTS:
For each opportunity, provide analysis in this EXACT JSON format:

{{
  "opportunity_id": {{
    "compatibility_score": 0.85,
    "strategic_value": "high",
    "risk_assessment": ["high_competition", "technical_requirements"],
    "priority_rank": 1,
    "funding_likelihood": 0.75,
    "strategic_rationale": "Clear explanation of strategic fit and key advantages in 1-2 sentences.",
    "action_priority": "immediate",
    "confidence_level": 0.9
  }}
}}

SCORING CRITERIA:
- compatibility_score: 0.0-1.0 based on mission alignment, focus area overlap, geographic fit, and funding size appropriateness
- strategic_value: "high", "medium", or "low" - overall strategic importance to organization
- risk_assessment: Choose applicable risks from ["high_competition", "technical_requirements", "geographic_mismatch", "capacity_concerns", "timeline_pressure", "compliance_complex", "matching_required", "reporting_intensive", "board_connections_needed", "sustainability_requirements"]
- priority_rank: 1=highest priority, rank ALL opportunities 1-{candidate_count}
- funding_likelihood: 0.0-1.0 probability of successful funding based on fit and competition
- strategic_rationale: Concise explanation of strategic reasoning (1-2 sentences max)
- action_priority: "immediate" (apply ASAP), "planned" (include in pipeline), or "monitor" (watch for changes)
- confidence_level: 0.0-1.0 confidence in analysis based on available information

Focus on practical funding strategy, organizational fit, competitive positioning, and implementation feasibility.

RESPONSE (JSON only, no additional text):
"""

def format_candidate_summary(candidate: Dict[str, Any], index: int) -> str:
    """Format a single candidate for the prompt"""
    funding_info = f"${candidate['funding_amount']:,}" if candidate['funding_amount'] else "Amount TBD"
    deadline_info = f"Deadline: {candidate['application_deadline']}" if candidate.get('application_deadline') else "Deadline: Rolling"
    
    summary = f"""
{index}. {candidate['organization_name']} ({candidate['opportunity_id']})
   Source: {candidate['source_type']} | Funding: {funding_info}
   Location: {candidate['geographic_location']} | Current Score: {(candidate['current_score'] * 100):.1f}%
   {deadline_info}
   
   Description: {candidate['description']}
   
   Priority Areas: {', '.join(candidate.get('additional_info', {}).get('priority_areas', []))}
   Application Requirements: {', '.join(candidate.get('additional_info', {}).get('application_requirements', []))}
   Competition Level: {candidate.get('additional_info', {}).get('competitive_factors', 'Unknown')}
"""
    return summary

def generate_ai_lite_prompt(organization_profile: Dict[str, Any], candidates: List[Dict[str, Any]]) -> str:
    """Generate the complete AI Lite scoring prompt"""
    
    # Format candidate summaries
    candidate_summaries = ""
    for i, candidate in enumerate(candidates, 1):
        candidate_summaries += format_candidate_summary(candidate, i)
    
    # Fill in the prompt template
    return AI_LITE_SCORING_PROMPT.format(
        organization_name=organization_profile['name'],
        mission_statement=organization_profile['mission_statement'],
        focus_areas=', '.join(organization_profile['focus_areas']),
        ntee_codes=', '.join(organization_profile['ntee_codes']),
        government_criteria=', '.join(organization_profile['government_criteria']),
        geographic_scope=organization_profile['geographic_scope'],
        typical_grant_size=organization_profile['typical_grant_size'],
        annual_budget=organization_profile['annual_budget'],
        candidate_summaries=candidate_summaries,
        candidate_count=len(candidates)
    )

def validate_ai_response(response_json: Dict[str, Any], expected_candidates: List[str]) -> Dict[str, Any]:
    """Validate and score the AI response quality"""
    validation_results = {
        "valid_json": True,
        "all_candidates_analyzed": True,
        "correct_scoring_ranges": True,
        "ranking_consistency": True,
        "missing_candidates": [],
        "scoring_errors": [],
        "quality_score": 0.0
    }
    
    try:
        # Check if all candidates are present
        analyzed_candidates = set(response_json.keys())
        expected_set = set(expected_candidates)
        missing = expected_set - analyzed_candidates
        
        if missing:
            validation_results["all_candidates_analyzed"] = False
            validation_results["missing_candidates"] = list(missing)
        
        # Check scoring ranges and required fields
        required_fields = ["compatibility_score", "strategic_value", "priority_rank", "funding_likelihood", "confidence_level"]
        ranks_used = []
        
        for opp_id, analysis in response_json.items():
            # Check required fields
            for field in required_fields:
                if field not in analysis:
                    validation_results["scoring_errors"].append(f"{opp_id}: Missing {field}")
            
            # Check score ranges
            if "compatibility_score" in analysis:
                score = analysis["compatibility_score"]
                if not (0.0 <= score <= 1.0):
                    validation_results["correct_scoring_ranges"] = False
                    validation_results["scoring_errors"].append(f"{opp_id}: compatibility_score {score} out of range")
            
            if "priority_rank" in analysis:
                rank = analysis["priority_rank"]
                ranks_used.append(rank)
                if not (1 <= rank <= len(expected_candidates)):
                    validation_results["ranking_consistency"] = False
                    validation_results["scoring_errors"].append(f"{opp_id}: priority_rank {rank} out of range")
        
        # Check for duplicate ranks
        if len(ranks_used) != len(set(ranks_used)):
            validation_results["ranking_consistency"] = False
            validation_results["scoring_errors"].append("Duplicate priority ranks found")
        
        # Calculate overall quality score
        quality_components = [
            validation_results["valid_json"],
            validation_results["all_candidates_analyzed"], 
            validation_results["correct_scoring_ranges"],
            validation_results["ranking_consistency"]
        ]
        validation_results["quality_score"] = sum(quality_components) / len(quality_components)
        
    except Exception as e:
        validation_results["valid_json"] = False
        validation_results["scoring_errors"].append(f"JSON parsing error: {str(e)}")
        validation_results["quality_score"] = 0.0
    
    return validation_results

# Main execution function
def run_ai_lite_test():
    """Run the complete AI Lite test package"""
    
    print("=" * 80)
    print("CATALYNX AI LITE SCORER - EXTERNAL TEST PACKAGE")
    print("=" * 80)
    
    print("\n1. ORGANIZATION PROFILE:")
    print(json.dumps(SAMPLE_ORGANIZATION_PROFILE, indent=2))
    
    print(f"\n2. FUNDING CANDIDATES ({len(SAMPLE_CANDIDATES)} opportunities):")
    for i, candidate in enumerate(SAMPLE_CANDIDATES, 1):
        print(f"\n   {i}. {candidate['organization_name']} - ${candidate['funding_amount']:,}")
        print(f"      {candidate['description'][:100]}...")
    
    print("\n3. AI LITE SCORING PROMPT:")
    print("-" * 50)
    
    # Generate the complete prompt
    full_prompt = generate_ai_lite_prompt(SAMPLE_ORGANIZATION_PROFILE, SAMPLE_CANDIDATES)
    print(full_prompt)
    
    print("\n4. EXPECTED OUTPUT FORMAT:")
    print("The AI should return a JSON object with analysis for each opportunity_id.")
    print("Expected opportunity IDs:", [c['opportunity_id'] for c in SAMPLE_CANDIDATES])
    
    print("\n5. TESTING INSTRUCTIONS:")
    print("- Copy the prompt above and paste it into ChatGPT or another AI system")
    print("- Review the JSON response for completeness and accuracy")
    print("- Use the validate_ai_response() function to check response quality")
    print("- Compare strategic reasoning against known grant strategy best practices")
    
    print("\n6. VALIDATION CRITERIA:")
    print("- All opportunity IDs present in response")
    print("- Scores within valid ranges (0.0-1.0)")
    print("- Unique priority rankings (1-5)")
    print("- Strategic rationale makes logical sense")
    print("- Risk assessments are appropriate")
    
    return full_prompt

if __name__ == "__main__":
    # Generate the test package
    prompt = run_ai_lite_test()
    
    # Save to file for easy copy/paste
    with open("ai_lite_test_prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt)
    
    print(f"\n7. TEST PROMPT SAVED:")
    print("The complete prompt has been saved to 'ai_lite_test_prompt.txt'")
    print("You can copy this file and test it with any AI system.")