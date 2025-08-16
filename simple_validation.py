"""
Simple validation script for AI Lite Test Package (no Unicode)
"""

import json
import os
from ai_lite_test_package import (
    SAMPLE_ORGANIZATION_PROFILE, 
    SAMPLE_CANDIDATES, 
    generate_ai_lite_prompt
)

def validate_package():
    """Simple validation check"""
    
    print("CATALYNX AI LITE TEST PACKAGE VALIDATION")
    print("=" * 50)
    
    checks_passed = 0
    total_checks = 5
    
    # 1. Organization profile
    print("\n1. Organization Profile Check:")
    required_fields = ["name", "mission_statement", "focus_areas", "ntee_codes"]
    
    profile_ok = True
    for field in required_fields:
        if field in SAMPLE_ORGANIZATION_PROFILE and SAMPLE_ORGANIZATION_PROFILE[field]:
            print(f"   [OK] {field}")
        else:
            print(f"   [ERROR] Missing or empty: {field}")
            profile_ok = False
    
    if profile_ok:
        checks_passed += 1
        print("   [PASS] Organization profile complete")
    
    # 2. Candidate data
    print("\n2. Candidate Data Check:")
    if len(SAMPLE_CANDIDATES) >= 3:
        print(f"   [OK] {len(SAMPLE_CANDIDATES)} candidates available")
        checks_passed += 1
        print("   [PASS] Candidate data sufficient")
    else:
        print(f"   [ERROR] Only {len(SAMPLE_CANDIDATES)} candidates (need at least 3)")
    
    # 3. Prompt generation
    print("\n3. Prompt Generation Check:")
    try:
        prompt = generate_ai_lite_prompt(SAMPLE_ORGANIZATION_PROFILE, SAMPLE_CANDIDATES)
        if len(prompt) > 1000 and "JSON only" in prompt:
            print(f"   [OK] Prompt generated ({len(prompt):,} chars)")
            checks_passed += 1
            print("   [PASS] Prompt generation working")
        else:
            print("   [ERROR] Prompt too short or missing key elements")
    except Exception as e:
        print(f"   [ERROR] Prompt generation failed: {e}")
    
    # 4. File outputs
    print("\n4. File Output Check:")
    files = ["ai_lite_test_prompt.txt", "AI_LITE_TEST_PACKAGE_README.md"]
    files_exist = 0
    
    for filename in files:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"   [OK] {filename} ({size:,} bytes)")
            files_exist += 1
        else:
            print(f"   [ERROR] Missing: {filename}")
    
    if files_exist == len(files):
        checks_passed += 1
        print("   [PASS] All files present")
    
    # 5. Prompt file content
    print("\n5. Prompt File Check:")
    try:
        with open("ai_lite_test_prompt.txt", "r", encoding="utf-8") as f:
            prompt_content = f.read()
        
        if "Community Tech Foundation" in prompt_content and "JSON only" in prompt_content:
            print("   [OK] Prompt file contains expected content")
            checks_passed += 1
            print("   [PASS] Prompt file ready for testing")
        else:
            print("   [ERROR] Prompt file missing key content")
    except Exception as e:
        print(f"   [ERROR] Cannot read prompt file: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    score = checks_passed / total_checks
    print(f"Checks Passed: {checks_passed}/{total_checks} ({score:.1%})")
    
    if score >= 0.8:
        print("\n[SUCCESS] Package ready for external testing!")
        print("Copy 'ai_lite_test_prompt.txt' to ChatGPT for testing.")
    elif score >= 0.6:
        print("\n[WARNING] Package mostly ready, minor issues detected.")
    else:
        print("\n[ERROR] Package not ready, significant issues found.")
    
    return score >= 0.8

if __name__ == "__main__":
    success = validate_package()
    
    if success:
        print("\nQuick Test Instructions:")
        print("1. Copy content from 'ai_lite_test_prompt.txt'")
        print("2. Paste into ChatGPT-4 or Claude")
        print("3. Check JSON response includes all 5 opportunity IDs")
        print("4. Verify scores are between 0.0-1.0")
        print("5. Confirm unique priority rankings 1-5")