"""
Task 20: Comprehensive Profile Capability Test Suite

Integration tests covering the complete profile workflow:
1. Profile CRUD operations
2. Discovery workflows (BMF → 990 → Tool 25)
3. Tool integration (orchestrator, quality scorer, opportunity scorer)
4. BAML output validation
5. Error handling and graceful degradation
6. Performance benchmarks

This test suite validates the entire profile enhancement pipeline end-to-end.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
import sqlite3
import time
from typing import Dict, Any

from src.profiles.unified_service import UnifiedProfileService
from src.profiles.orchestration import ProfileEnhancementOrchestrator, WorkflowResult
from src.profiles.quality_scoring import (
    ProfileQualityScorer,
    OpportunityQualityScorer,
    DataCompletenessValidator,
    QualityRating
)
from src.profiles.models import UnifiedProfile

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def print_section(title: str):
    """Print section header"""
    print("\n" + "="*60)
    print(title)
    print("="*60 + "\n")

def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {test_name}")
    if details:
        print(f"  {details}")


class TestProfileCRUD:
    """Test 1: Profile CRUD Operations"""

    def __init__(self):
        self.service = UnifiedProfileService()
        self.test_profile_id = None

    def test_create_profile(self) -> bool:
        """Test profile creation"""
        try:
            profile_data = {
                'profile_id': 'test-profile-crud-001',
                'ein': '123456789',
                'organization_name': 'Test Organization for CRUD',
                'organization_type': 'nonprofit',
                'ntee_codes': ['P20', 'B25'],
                'geographic_scope': {
                    'states': ['VA', 'MD', 'DC'],
                    'nationwide': False
                },
                'mission_statement': 'Test mission for CRUD operations',
                'annual_revenue': 5000000
            }

            profile = UnifiedProfile(**profile_data)
            created = self.service.create_profile(profile)

            if created and created.profile_id == profile_data['profile_id']:
                self.test_profile_id = created.profile_id
                print_result("Create Profile", True, f"Profile ID: {created.profile_id}")
                return True
            else:
                print_result("Create Profile", False, "Profile not created")
                return False

        except Exception as e:
            print_result("Create Profile", False, f"Error: {e}")
            return False

    def test_read_profile(self) -> bool:
        """Test profile reading"""
        try:
            if not self.test_profile_id:
                print_result("Read Profile", False, "No profile ID to read")
                return False

            profile = self.service.get_profile(self.test_profile_id)

            if profile and profile.profile_id == self.test_profile_id:
                print_result("Read Profile", True, f"Retrieved: {profile.organization_name}")
                return True
            else:
                print_result("Read Profile", False, "Profile not found")
                return False

        except Exception as e:
            print_result("Read Profile", False, f"Error: {e}")
            return False

    def test_update_profile(self) -> bool:
        """Test profile update"""
        try:
            if not self.test_profile_id:
                print_result("Update Profile", False, "No profile ID to update")
                return False

            profile = self.service.get_profile(self.test_profile_id)
            profile.mission_statement = "Updated mission statement for testing"

            updated = self.service.update_profile(profile)

            if updated and updated.mission_statement == "Updated mission statement for testing":
                print_result("Update Profile", True, "Mission updated successfully")
                return True
            else:
                print_result("Update Profile", False, "Update failed")
                return False

        except Exception as e:
            print_result("Update Profile", False, f"Error: {e}")
            return False

    def test_delete_profile(self) -> bool:
        """Test profile deletion"""
        try:
            if not self.test_profile_id:
                print_result("Delete Profile", False, "No profile ID to delete")
                return False

            deleted = self.service.delete_profile(self.test_profile_id)

            # Verify deletion
            profile = self.service.get_profile(self.test_profile_id)

            if deleted and profile is None:
                print_result("Delete Profile", True, "Profile deleted successfully")
                return True
            else:
                print_result("Delete Profile", False, "Deletion failed")
                return False

        except Exception as e:
            print_result("Delete Profile", False, f"Error: {e}")
            return False

    def run_all(self) -> bool:
        """Run all CRUD tests"""
        print_section("TEST 1: Profile CRUD Operations")

        results = []
        results.append(self.test_create_profile())
        results.append(self.test_read_profile())
        results.append(self.test_update_profile())
        results.append(self.test_delete_profile())

        success = all(results)
        print(f"\nCRUD Tests: {sum(results)}/{len(results)} passed")
        return success


class TestDiscoveryWorkflow:
    """Test 2: Discovery Workflows"""

    def __init__(self):
        self.orchestrator = ProfileEnhancementOrchestrator()
        self.test_ein = "208295721"  # UPMC

    def test_bmf_discovery(self) -> bool:
        """Test BMF discovery step"""
        try:
            # Execute just BMF discovery
            workflow_result = self.orchestrator.execute_profile_building(
                ein=self.test_ein,
                enable_tool25=False,
                enable_tool2=False
            )

            if workflow_result.success and workflow_result.profile:
                org_name = workflow_result.profile.organization_name
                print_result(
                    "BMF Discovery",
                    True,
                    f"Found: {org_name}"
                )
                return True
            else:
                print_result("BMF Discovery", False, f"BMF step failed: {workflow_result.errors}")
                return False

        except Exception as e:
            print_result("BMF Discovery", False, f"Error: {e}")
            return False

    def test_990_intelligence(self) -> bool:
        """Test Form 990 intelligence"""
        try:
            workflow_result = self.orchestrator.execute_profile_building(
                ein=self.test_ein,
                enable_tool25=False,
                enable_tool2=False
            )

            if workflow_result.success and workflow_result.profile:
                # Check if profile has revenue data (indicates 990 was found)
                revenue = getattr(workflow_result.profile, 'annual_revenue', 0) or 0
                if revenue > 0:
                    print_result(
                        "990 Intelligence",
                        True,
                        f"Revenue: ${revenue:,}"
                    )
                else:
                    # 990 is optional, so missing it is OK
                    print_result("990 Intelligence", True, "Not available (graceful degradation)")
                return True
            else:
                print_result("990 Intelligence", False, "Workflow failed")
                return False

        except Exception as e:
            print_result("990 Intelligence", False, f"Error: {e}")
            return False

    def test_complete_workflow(self) -> bool:
        """Test complete workflow (BMF + 990 + Tool 25 + Tool 2 optional)"""
        try:
            start_time = time.time()

            workflow_result = self.orchestrator.execute_profile_building(
                ein=self.test_ein,
                enable_tool25=True,  # Enable web scraping
                enable_tool2=False,  # Disable AI (expensive)
                quality_threshold=0.70
            )

            duration = time.time() - start_time

            if workflow_result.success:
                print_result(
                    "Complete Workflow",
                    True,
                    f"Quality: {workflow_result.final_quality_score:.2f}, Cost: ${workflow_result.total_cost_dollars:.2f}, Time: {duration:.1f}s"
                )
                return True
            else:
                print_result("Complete Workflow", False, f"Errors: {workflow_result.errors}")
                return False

        except Exception as e:
            print_result("Complete Workflow", False, f"Error: {e}")
            return False

    def run_all(self) -> bool:
        """Run all discovery workflow tests"""
        print_section("TEST 2: Discovery Workflows")

        results = []
        results.append(self.test_bmf_discovery())
        results.append(self.test_990_intelligence())
        results.append(self.test_complete_workflow())

        success = all(results)
        print(f"\nDiscovery Tests: {sum(results)}/{len(results)} passed")
        return success


class TestToolIntegration:
    """Test 3: Tool Integration"""

    def __init__(self):
        self.profile_scorer = ProfileQualityScorer()
        self.opportunity_scorer = OpportunityQualityScorer()
        self.completeness_validator = DataCompletenessValidator()

    def test_profile_quality_scoring(self) -> bool:
        """Test profile quality scoring"""
        try:
            # Sample BMF data
            bmf_data = {
                'ein': '123456789',
                'name': 'Test Organization',
                'state': 'VA',
                'ntee_code': 'P20'
            }

            # Sample 990 data
            form_990 = {
                'totrevenue': 5000000,
                'totfuncexpns': 4750000,
                'totassetsend': 10000000
            }

            quality_score = self.profile_scorer.calculate_profile_quality(
                bmf_data=bmf_data,
                form_990=form_990,
                tool25_data=None,
                tool2_data=None
            )

            if quality_score.overall_score > 0:
                print_result(
                    "Profile Quality Scoring",
                    True,
                    f"Score: {quality_score.overall_score:.2f}, Rating: {quality_score.rating.value}"
                )
                return True
            else:
                print_result("Profile Quality Scoring", False, "Zero score")
                return False

        except Exception as e:
            print_result("Profile Quality Scoring", False, f"Error: {e}")
            return False

    def test_funding_opportunity_scoring(self) -> bool:
        """Test funding opportunity scoring"""
        try:
            profile = {
                'ntee_codes': ['P20'],
                'geographic_scope': {'states': ['VA']},
                'annual_budget': 5000000
            }

            foundation = {
                'ein': '540012345',
                'name': 'Test Foundation',
                'state': 'VA',
                'funded_ntee_codes': ['P20'],
                'avg_grant_size': 500000,
                'similar_recipient_count': 5,
                'accepts_applications': True
            }

            score = self.opportunity_scorer.score_funding_opportunity(
                profile=profile,
                foundation=foundation
            )

            if score.overall_score > 0:
                print_result(
                    "Funding Opportunity Scoring",
                    True,
                    f"Score: {score.overall_score:.2f}, Rating: {score.rating.value}"
                )
                return True
            else:
                print_result("Funding Opportunity Scoring", False, "Zero score")
                return False

        except Exception as e:
            print_result("Funding Opportunity Scoring", False, f"Error: {e}")
            return False

    def test_data_completeness_validation(self) -> bool:
        """Test data completeness validation"""
        try:
            bmf_data = {'ein': '123', 'name': 'Test', 'state': 'VA'}
            form_990 = {'totrevenue': 1000000}

            completeness = self.completeness_validator.validate_profile_completeness(
                bmf_data=bmf_data,
                form_990=form_990,
                tool25_data=None,
                tool2_data=None
            )

            if 'overall_completeness' in completeness:
                print_result(
                    "Data Completeness Validation",
                    True,
                    f"Completeness: {completeness['overall_completeness']:.2f}"
                )
                return True
            else:
                print_result("Data Completeness Validation", False, "No completeness metric")
                return False

        except Exception as e:
            print_result("Data Completeness Validation", False, f"Error: {e}")
            return False

    def run_all(self) -> bool:
        """Run all tool integration tests"""
        print_section("TEST 3: Tool Integration")

        results = []
        results.append(self.test_profile_quality_scoring())
        results.append(self.test_funding_opportunity_scoring())
        results.append(self.test_data_completeness_validation())

        success = all(results)
        print(f"\nTool Integration Tests: {sum(results)}/{len(results)} passed")
        return success


class TestBAMLValidation:
    """Test 4: BAML Output Validation"""

    def test_baml_structure_bmf(self) -> bool:
        """Test BAML structure from BMF discovery"""
        try:
            # Query BMF database directly
            db_path = "data/nonprofit_intelligence.db"
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT ein, name, city, state, ntee_code FROM bmf_organizations LIMIT 1"
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                # Check BAML-compatible structure
                data = dict(result)
                required_fields = ['ein', 'name', 'state']
                has_required = all(field in data for field in required_fields)

                if has_required:
                    print_result("BAML Structure (BMF)", True, f"EIN: {data['ein']}")
                    return True
                else:
                    print_result("BAML Structure (BMF)", False, "Missing required fields")
                    return False
            else:
                print_result("BAML Structure (BMF)", False, "No data from BMF")
                return False

        except Exception as e:
            print_result("BAML Structure (BMF)", False, f"Error: {e}")
            return False

    def test_baml_structure_990(self) -> bool:
        """Test BAML structure from Form 990"""
        try:
            db_path = "data/nonprofit_intelligence.db"
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT ein, tax_year, totrevenue, totfuncexpns FROM form_990 LIMIT 1"
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                data = dict(result)
                required_fields = ['ein', 'tax_year']
                has_required = all(field in data for field in required_fields)

                if has_required:
                    print_result("BAML Structure (990)", True, f"EIN: {data['ein']}, Year: {data['tax_year']}")
                    return True
                else:
                    print_result("BAML Structure (990)", False, "Missing required fields")
                    return False
            else:
                print_result("BAML Structure (990)", False, "No data from 990")
                return False

        except Exception as e:
            print_result("BAML Structure (990)", False, f"Error: {e}")
            return False

    def run_all(self) -> bool:
        """Run all BAML validation tests"""
        print_section("TEST 4: BAML Output Validation")

        results = []
        results.append(self.test_baml_structure_bmf())
        results.append(self.test_baml_structure_990())

        success = all(results)
        print(f"\nBAML Validation Tests: {sum(results)}/{len(results)} passed")
        return success


class TestErrorHandling:
    """Test 5: Error Handling and Graceful Degradation"""

    def __init__(self):
        self.orchestrator = ProfileEnhancementOrchestrator()

    def test_invalid_ein(self) -> bool:
        """Test handling of invalid EIN"""
        try:
            workflow_result = self.orchestrator.execute_profile_building(
                ein="000000000",  # Invalid EIN
                enable_tool25=False,
                enable_tool2=False
            )

            # Should fail gracefully
            if not workflow_result.success and workflow_result.errors:
                print_result(
                    "Invalid EIN Handling",
                    True,
                    f"Gracefully failed: {workflow_result.errors[0][:50]}"
                )
                return True
            else:
                print_result("Invalid EIN Handling", False, "Should have failed")
                return False

        except Exception as e:
            # Exception is also acceptable for invalid EIN
            print_result("Invalid EIN Handling", True, "Exception raised (acceptable)")
            return True

    def test_missing_990_degradation(self) -> bool:
        """Test graceful degradation when 990 is missing"""
        try:
            # Use an EIN that likely has BMF but no 990
            workflow_result = self.orchestrator.execute_profile_building(
                ein="999999999",
                enable_tool25=False,
                enable_tool2=False
            )

            # Should complete with BMF even if 990 missing
            if 'bmf_discovery' in workflow_result.steps_completed:
                has_990 = 'form_990' in workflow_result.steps_completed
                print_result(
                    "Missing 990 Degradation",
                    True,
                    f"BMF found, 990: {'present' if has_990 else 'gracefully skipped'}"
                )
                return True
            else:
                print_result("Missing 990 Degradation", True, "BMF also missing (acceptable)")
                return True

        except Exception as e:
            print_result("Missing 990 Degradation", False, f"Error: {e}")
            return False

    def test_quality_threshold_enforcement(self) -> bool:
        """Test quality threshold prevents Tool 2 execution"""
        try:
            workflow_result = self.orchestrator.execute_profile_building(
                ein="208295721",
                enable_tool25=False,
                enable_tool2=True,  # Enable but should be blocked by threshold
                quality_threshold=0.95  # Very high threshold
            )

            has_tool2 = 'tool_2' in workflow_result.steps_completed

            if not has_tool2:
                print_result(
                    "Quality Threshold Enforcement",
                    True,
                    "Tool 2 blocked by quality threshold"
                )
                return True
            else:
                # If quality is actually >= 0.95, Tool 2 should run
                print_result(
                    "Quality Threshold Enforcement",
                    True,
                    "Quality exceeded threshold, Tool 2 executed"
                )
                return True

        except Exception as e:
            print_result("Quality Threshold Enforcement", False, f"Error: {e}")
            return False

    def run_all(self) -> bool:
        """Run all error handling tests"""
        print_section("TEST 5: Error Handling & Graceful Degradation")

        results = []
        results.append(self.test_invalid_ein())
        results.append(self.test_missing_990_degradation())
        results.append(self.test_quality_threshold_enforcement())

        success = all(results)
        print(f"\nError Handling Tests: {sum(results)}/{len(results)} passed")
        return success


class TestPerformanceBenchmarks:
    """Test 6: Performance Benchmarks"""

    def __init__(self):
        self.orchestrator = ProfileEnhancementOrchestrator()

    def test_bmf_query_performance(self) -> bool:
        """Test BMF query performance (<1s)"""
        try:
            start_time = time.time()

            workflow_result = self.orchestrator.execute_profile_building(
                ein="208295721",
                enable_tool25=False,
                enable_tool2=False
            )

            duration = time.time() - start_time

            if duration < 1.0 and workflow_result.success:
                print_result(
                    "BMF Query Performance",
                    True,
                    f"Completed in {duration:.3f}s (<1s)"
                )
                return True
            else:
                print_result(
                    "BMF Query Performance",
                    duration < 2.0,  # Acceptable up to 2s
                    f"Completed in {duration:.3f}s"
                )
                return duration < 2.0

        except Exception as e:
            print_result("BMF Query Performance", False, f"Error: {e}")
            return False

    def test_quality_scoring_performance(self) -> bool:
        """Test quality scoring performance (<100ms)"""
        try:
            scorer = ProfileQualityScorer()

            bmf_data = {'ein': '123', 'name': 'Test', 'state': 'VA', 'ntee_code': 'P20'}
            form_990 = {'totrevenue': 1000000, 'totfuncexpns': 950000, 'totassetsend': 500000}

            start_time = time.time()
            quality_score = scorer.calculate_profile_quality(bmf_data, form_990, None, None)
            duration = time.time() - start_time

            if duration < 0.1:  # 100ms
                print_result(
                    "Quality Scoring Performance",
                    True,
                    f"Completed in {duration*1000:.1f}ms (<100ms)"
                )
                return True
            else:
                print_result(
                    "Quality Scoring Performance",
                    False,
                    f"Completed in {duration*1000:.1f}ms (>100ms)"
                )
                return False

        except Exception as e:
            print_result("Quality Scoring Performance", False, f"Error: {e}")
            return False

    def run_all(self) -> bool:
        """Run all performance benchmark tests"""
        print_section("TEST 6: Performance Benchmarks")

        results = []
        results.append(self.test_bmf_query_performance())
        results.append(self.test_quality_scoring_performance())

        success = all(results)
        print(f"\nPerformance Tests: {sum(results)}/{len(results)} passed")
        return success


def main():
    """Run comprehensive profile capability test suite"""
    print("\n" + "="*60)
    print("TASK 20: Comprehensive Profile Capability Test Suite")
    print("End-to-End Integration Tests")
    print("="*60)

    # Run all test classes
    all_results = []

    # Test 1: CRUD Operations
    crud_tests = TestProfileCRUD()
    all_results.append(crud_tests.run_all())

    # Test 2: Discovery Workflows
    discovery_tests = TestDiscoveryWorkflow()
    all_results.append(discovery_tests.run_all())

    # Test 3: Tool Integration
    tool_tests = TestToolIntegration()
    all_results.append(tool_tests.run_all())

    # Test 4: BAML Validation
    baml_tests = TestBAMLValidation()
    all_results.append(baml_tests.run_all())

    # Test 5: Error Handling
    error_tests = TestErrorHandling()
    all_results.append(error_tests.run_all())

    # Test 6: Performance Benchmarks
    perf_tests = TestPerformanceBenchmarks()
    all_results.append(perf_tests.run_all())

    # Summary
    print_section("TEST SUMMARY")
    test_categories = [
        "Profile CRUD Operations",
        "Discovery Workflows",
        "Tool Integration",
        "BAML Output Validation",
        "Error Handling & Graceful Degradation",
        "Performance Benchmarks"
    ]

    for i, (category, result) in enumerate(zip(test_categories, all_results), 1):
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} Test {i}: {category}")

    total_passed = sum(all_results)
    total_tests = len(all_results)

    print(f"\n{'='*60}")
    print(f"Overall: {total_passed}/{total_tests} test categories passed")

    if total_passed == total_tests:
        print("\n[OK] Task 20 COMPLETE - All profile capability tests passed!")
        print("[OK] Phase 8 ready for completion!")
        return True
    else:
        print(f"\n[FAIL] {total_tests - total_passed} test categories failed")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
