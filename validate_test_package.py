"""
Validation script for AI Lite Test Package
Checks package completeness and format
"""

import json
import os
from ai_lite_test_package import (
    SAMPLE_ORGANIZATION_PROFILE, 
    SAMPLE_CANDIDATES, 
    generate_ai_lite_prompt,
    validate_ai_response
)

def check_package_completeness():
    """Validate the test package is complete and properly formatted"""
    
    print("CATALYNX AI LITE TEST PACKAGE VALIDATION")
    print("=" * 50)
    
    validation_results = {
        "organization_profile": False,
        "candidate_data": False, 
        "prompt_generation": False,
        "file_outputs": False,
        "documentation": False,
        "overall_score": 0.0
    }
    
    # Check organization profile
    print("\n1. Validating Organization Profile...")
    required_profile_fields = ["name", "mission_statement", "focus_areas", "ntee_codes", "geographic_scope"]
    
    profile_valid = True
    for field in required_profile_fields:
        if field not in SAMPLE_ORGANIZATION_PROFILE:
            print(f"   [ERROR] Missing field: {field}")
            profile_valid = False
        elif not SAMPLE_ORGANIZATION_PROFILE[field]:
            print(f"   [WARNING] Empty field: {field}")
    
    if profile_valid:
        print("   [OK] Organization profile complete")
        validation_results["organization_profile"] = True
    
    # Check candidate data
    print("\n2. Validating Candidate Data...")
    required_candidate_fields = ["opportunity_id", "organization_name", "description", "funding_amount"]
    
    candidates_valid = True
    for i, candidate in enumerate(SAMPLE_CANDIDATES):
        for field in required_candidate_fields:
            if field not in candidate:
                print(f"   ❌ Candidate {i+1} missing field: {field}")
                candidates_valid = False
    
    if candidates_valid:
        print(f"   [OK] All {len(SAMPLE_CANDIDATES)} candidates properly formatted")
        validation_results["candidate_data"] = True
    
    # Check prompt generation
    print("\n3. Validating Prompt Generation...")
    try:
        prompt = generate_ai_lite_prompt(SAMPLE_ORGANIZATION_PROFILE, SAMPLE_CANDIDATES)
        
        # Check prompt contains key elements
        required_prompt_elements = [
            "ORGANIZATION PROFILE:",
            "FUNDING OPPORTUNITY CANDIDATES",
            "ANALYSIS REQUIREMENTS:",
            "compatibility_score",
            "priority_rank",
            "JSON only"
        ]
        
        prompt_valid = True
        for element in required_prompt_elements:
            if element not in prompt:
                print(f"   ❌ Missing prompt element: {element}")
                prompt_valid = False
        
        if prompt_valid:
            print("   ✅ Prompt generation working correctly")
            print(f"   📊 Prompt length: {len(prompt):,} characters")
            validation_results["prompt_generation"] = True
        
    except Exception as e:
        print(f"   ❌ Prompt generation failed: {str(e)}")
    
    # Check file outputs
    print("\n4. Validating File Outputs...")
    expected_files = [
        "ai_lite_test_package.py",
        "ai_lite_test_prompt.txt", 
        "AI_LITE_TEST_PACKAGE_README.md"
    ]
    
    files_exist = True
    for filename in expected_files:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"   ✅ {filename} ({size:,} bytes)")
        else:
            print(f"   ❌ Missing file: {filename}")
            files_exist = False
    
    if files_exist:
        validation_results["file_outputs"] = True
    
    # Check documentation
    print("\n5. Validating Documentation...")
    if os.path.exists("AI_LITE_TEST_PACKAGE_README.md"):
        with open("AI_LITE_TEST_PACKAGE_README.md", "r", encoding="utf-8") as f:
            readme_content = f.read()
            
        required_sections = [
            "## Overview",
            "## How to Test", 
            "## Expected Performance Benchmarks",
            "## Evaluation Criteria"
        ]
        
        doc_valid = True
        for section in required_sections:
            if section not in readme_content:
                print(f"   ❌ Missing documentation section: {section}")
                doc_valid = False
        
        if doc_valid:
            print("   ✅ Documentation complete")
            validation_results["documentation"] = True
    
    # Calculate overall score
    score_components = list(validation_results.values())[:-1]  # Exclude overall_score
    validation_results["overall_score"] = sum(score_components) / len(score_components)
    
    # Summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    for component, status in validation_results.items():
        if component != "overall_score":
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {component.replace('_', ' ').title()}: {'PASS' if status else 'FAIL'}")
    
    print(f"\n🎯 Overall Score: {validation_results['overall_score']:.1%}")
    
    if validation_results["overall_score"] >= 0.8:
        print("🟢 READY FOR TESTING - Package is complete and properly formatted")
    elif validation_results["overall_score"] >= 0.6:
        print("🟡 MOSTLY READY - Minor issues need addressing")
    else:
        print("🔴 NOT READY - Significant issues need fixing")
    
    return validation_results

def test_sample_response():
    """Test the validation function with a sample AI response"""
    
    print("\n" + "=" * 50)
    print("TESTING RESPONSE VALIDATION")
    print("=" * 50)
    
    # Sample AI response for testing
    sample_response = {
        "tech_equity_001": {
            "compatibility_score": 0.88,
            "strategic_value": "high",
            "risk_assessment": ["moderate_competition", "sustainability_requirements"],
            "priority_rank": 2,
            "funding_likelihood": 0.78,
            "strategic_rationale": "Perfect mission alignment with digital literacy focus.",
            "action_priority": "immediate",
            "confidence_level": 0.85
        },
        "workforce_tech_002": {
            "compatibility_score": 0.74,
            "strategic_value": "medium",
            "risk_assessment": ["high_competition", "capacity_concerns"],
            "priority_rank": 4,
            "funding_likelihood": 0.62,
            "strategic_rationale": "Good workforce development alignment but high competition.",
            "action_priority": "planned",
            "confidence_level": 0.75
        },
        "rural_broadband_003": {
            "compatibility_score": 0.92,
            "strategic_value": "high",
            "risk_assessment": ["government_partnerships"],
            "priority_rank": 1,
            "funding_likelihood": 0.85,
            "strategic_rationale": "Excellent geographic and mission fit with lower competition.",
            "action_priority": "immediate",
            "confidence_level": 0.90
        },
        "stem_education_004": {
            "compatibility_score": 0.79,
            "strategic_value": "medium",
            "risk_assessment": ["high_competition", "technical_requirements"],
            "priority_rank": 3,
            "funding_likelihood": 0.68,
            "strategic_rationale": "Strong STEM alignment but competitive landscape.",
            "action_priority": "planned",
            "confidence_level": 0.80
        },
        "senior_tech_005": {
            "compatibility_score": 0.83,
            "strategic_value": "high",
            "risk_assessment": ["timeline_pressure"],
            "priority_rank": 5,
            "funding_likelihood": 0.72,
            "strategic_rationale": "Good fit but tight application deadline.",
            "action_priority": "immediate",
            "confidence_level": 0.82
        }
    }
    
    expected_candidates = [c["opportunity_id"] for c in SAMPLE_CANDIDATES]
    validation = validate_ai_response(sample_response, expected_candidates)
    
    print("Sample Response Validation:")
    for key, value in validation.items():
        if key == "quality_score":
            print(f"   🎯 {key}: {value:.1%}")
        elif isinstance(value, bool):
            icon = "✅" if value else "❌"
            print(f"   {icon} {key}: {'PASS' if value else 'FAIL'}")
        elif isinstance(value, list) and value:
            print(f"   ⚠️  {key}: {value}")
    
    return validation

if __name__ == "__main__":
    # Run validation
    package_validation = check_package_completeness()
    
    # Test sample response
    response_validation = test_sample_response()
    
    print(f"\n🚀 AI LITE TEST PACKAGE READY FOR EXTERNAL TESTING!")
    print(f"📁 Copy 'ai_lite_test_prompt.txt' to test with ChatGPT or other AI systems")