#!/usr/bin/env python3
"""
Catalynx Testing Platform Cleanup Validation

Quick validation script to verify the cleanup was successful and the new framework is operational.
"""

import os
import sys
from pathlib import Path

def validate_file_structure():
    """Validate the new file structure is in place"""
    print("Validating file structure...")
    
    # Check archive structure
    archive_dirs = [
        "archive/test_files/ai_integration_tests",
        "archive/test_files/tier_system_tests", 
        "archive/test_files/processor_tests",
        "archive/test_files/misc_tests"
    ]
    
    for dir_path in archive_dirs:
        if not Path(dir_path).exists():
            print(f"X Missing archive directory: {dir_path}")
            return False
        else:
            file_count = len(list(Path(dir_path).glob("*.py")))
            print(f"+ {dir_path}: {file_count} files archived")
    
    # Check test framework structure
    framework_files = [
        "test_framework/unified_test_base.py",
        "test_framework/essential_tests/test_intelligence_tiers.py",
        "test_framework/essential_tests/test_processor_suite.py"
    ]
    
    for file_path in framework_files:
        if not Path(file_path).exists():
            print(f"X Missing framework file: {file_path}")
            return False
        else:
            print(f"+ {file_path} exists")
    
    return True

def validate_env_configuration():
    """Validate .env file has proper GPT-5 configurations"""
    print("\nValidating .env configuration...")
    
    if not Path('.env').exists():
        print("X .env file not found")
        return False
    
    with open('.env', 'r') as f:
        env_content = f.read()
    
    # Check for GPT-5 model configurations
    required_models = [
        'AI_LITE_MODEL="gpt-5-nano"',
        'AI_HEAVY_MODEL="gpt-5-mini"', 
        'AI_RESEARCH_MODEL="gpt-5"'
    ]
    
    for model_config in required_models:
        if model_config in env_content:
            print(f"+ {model_config}")
        else:
            print(f"X Missing or incorrect: {model_config}")
            return False
    
    # Check for OpenAI API key presence
    if "OPENAI_API_KEY=" in env_content and len(env_content.split("OPENAI_API_KEY=")[1].split('\n')[0]) > 10:
        print("+ OpenAI API key configured")
    else:
        print("! OpenAI API key not found or too short")
        return False
    
    return True

def count_archived_files():
    """Count files that were successfully archived"""
    print("\nCounting archived files...")
    
    archive_base = Path("archive/test_files")
    if not archive_base.exists():
        print("X Archive directory not found")
        return 0
    
    total_archived = 0
    for subdir in archive_base.iterdir():
        if subdir.is_dir():
            py_files = list(subdir.glob("*.py"))
            count = len(py_files)
            total_archived += count
            print(f"  {subdir.name}: {count} files")
    
    print(f"+ Total archived files: {total_archived}")
    return total_archived

def count_remaining_files():
    """Count remaining test files in root directory"""
    print("\nCounting remaining test files in root...")
    
    root_test_files = list(Path(".").glob("*test*.py"))
    essential_files = list(Path("test_framework/essential_tests").glob("*.py"))
    
    print(f"Root directory test files: {len(root_test_files)}")
    for f in root_test_files:
        print(f"  - {f.name}")
    
    print(f"Essential test files: {len(essential_files)}")
    for f in essential_files:
        print(f"  - {f.name}")
    
    total_remaining = len(root_test_files) + len(essential_files)
    print(f"+ Total remaining test files: {total_remaining}")
    
    return total_remaining

def validate_cleanup_metrics():
    """Validate cleanup achieved the target metrics"""
    print("\nValidating cleanup metrics...")
    
    archived_count = count_archived_files()
    remaining_count = count_remaining_files()
    
    original_count = 76  # From audit report
    expected_remaining = 8  # Target from cleanup plan
    
    # Calculate reduction
    if archived_count + remaining_count != original_count:
        print(f"! File count mismatch: {archived_count} archived + {remaining_count} remaining != {original_count} original")
    else:
        print(f"+ File accounting correct: {archived_count} + {remaining_count} = {original_count}")
    
    reduction_percent = (archived_count / original_count) * 100
    print(f"+ Reduction achieved: {reduction_percent:.1f}% (target: >85%)")
    
    if remaining_count <= expected_remaining:
        print(f"+ Essential files count: {remaining_count} <= {expected_remaining} (target)")
    else:
        print(f"! More essential files than expected: {remaining_count} > {expected_remaining}")
    
    return reduction_percent >= 85

def test_framework_import():
    """Test that the unified framework can be imported"""
    print("\nTesting framework import...")
    
    try:
        # Add test framework to path
        sys.path.append(str(Path("test_framework")))
        
        # Test import
        from unified_test_base import UnifiedTestBase, CostTracker, TestResult
        print("+ UnifiedTestBase import successful")
        
        # Test basic instantiation
        framework = UnifiedTestBase(max_budget=1.00)
        print("+ Framework instantiation successful")
        
        # Test cost tracker
        if hasattr(framework, 'cost_tracker'):
            print("+ Cost tracker initialized")
        
        # Test test scenarios  
        if hasattr(framework, 'test_scenarios') and len(framework.test_scenarios) > 0:
            print(f"+ Test scenarios loaded: {len(framework.test_scenarios)}")
        
        return True
        
    except ImportError as e:
        print(f"X Import failed: {e}")
        return False
    except Exception as e:
        print(f"X Framework initialization failed: {e}")
        return False

def main():
    """Run comprehensive validation"""
    print("CATALYNX TESTING PLATFORM CLEANUP VALIDATION")
    print("=" * 50)
    
    validations = [
        ("File Structure", validate_file_structure),
        ("Environment Configuration", validate_env_configuration), 
        ("Cleanup Metrics", validate_cleanup_metrics),
        ("Framework Import", test_framework_import)
    ]
    
    results = {}
    
    for name, validator in validations:
        print(f"\n{name.upper()}")
        print("-" * len(name))
        
        try:
            result = validator()
            results[name] = result
        except Exception as e:
            print(f"X Validation failed with exception: {e}")
            results[name] = False
    
    # Summary
    print("\nVALIDATION SUMMARY")
    print("=" * 20)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for name, result in results.items():
        status = "+ PASS" if result else "X FAIL"
        print(f"{name}: {status}")
    
    print(f"\nOverall: {passed}/{total} validations passed")
    
    if passed == total:
        print("SUCCESS: CLEANUP VALIDATION COMPLETE!")
        print("The testing platform cleanup has been completed successfully.")
        print("\nNext steps:")
        print("1. Run test_framework/essential_tests/test_intelligence_tiers.py")
        print("2. Run test_framework/essential_tests/test_processor_suite.py") 
        print("3. Review TESTING_PLATFORM_CLEANUP_IMPLEMENTATION_REPORT.md")
        return 0
    else:
        print("WARNING: CLEANUP VALIDATION ISSUES DETECTED")
        print("Please review the failed validations above.")
        return 1

if __name__ == "__main__":
    exit(main())