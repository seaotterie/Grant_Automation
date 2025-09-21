#!/usr/bin/env python3
"""
Test script for GitHub CLI integration with Bug Resolution Workflow

This script tests the complete integration between the bug resolution system
and local GitHub CLI for issue tracking and project management.
"""

import asyncio
import os
import sys
# Configure UTF-8 encoding for Windows
if os.name == 'nt':
    import codecs
    try:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except AttributeError:
        # stdout/stderr may already be wrapped or redirected
        pass

import json
import logging
from datetime import datetime
from pathlib import Path
import sys

# Add the integrated testing path to sys.path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from bug_resolution_workflow import (
        Bug, BugSeverity, BugCategory, BugStatus,
        BugResolutionWorkflow
    )
except ImportError:
    # Try importing from the same directory without relative imports
    import bug_resolution_workflow
    Bug = bug_resolution_workflow.Bug
    BugSeverity = bug_resolution_workflow.BugSeverity
    BugCategory = bug_resolution_workflow.BugCategory
    BugStatus = bug_resolution_workflow.BugStatus
    BugResolutionWorkflow = bug_resolution_workflow.BugResolutionWorkflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubIntegrationTester:
    """Test GitHub CLI integration with bug resolution workflow"""

    def __init__(self):
        self.workflow = BugResolutionWorkflow()
        self.test_results = {
            "test_start": datetime.now().isoformat(),
            "tests_executed": [],
            "integration_status": {},
            "github_issues_created": [],
            "errors": []
        }

    async def run_complete_integration_test(self):
        """Run complete GitHub CLI integration test"""
        logger.info("GITHUB CLI INTEGRATION TEST")
        logger.info("Testing complete bug-to-issue workflow")
        logger.info("=" * 60)

        try:
            # Test 1: Verify GitHub integration availability
            logger.info("Test 1: Checking GitHub integration availability...")
            github_available = await self._test_github_integration_availability()
            self.test_results["integration_status"]["github_available"] = github_available

            if not github_available:
                logger.warning("GitHub CLI integration not available - testing workflow without GitHub")
                return await self._test_workflow_without_github()

            # Test 2: Create sample bugs
            logger.info("Test 2: Creating sample bugs for testing...")
            test_bugs = self._create_sample_test_bugs()
            self.test_results["tests_executed"].append("sample_bugs_created")

            # Test 3: Test bug-to-issue creation
            logger.info("Test 3: Testing automated bug-to-issue creation...")
            await self._test_bug_to_issue_creation(test_bugs)

            # Test 4: Test subagent coordination
            logger.info("Test 4: Testing subagent coordination with GitHub...")
            await self._test_subagent_github_coordination(test_bugs)

            # Test 5: Test complete workflow integration
            logger.info("Test 5: Testing complete workflow integration...")
            await self._test_complete_workflow_integration()

            # Generate final test report
            await self._generate_test_report()

        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            self.test_results["errors"].append(str(e))

        return self.test_results

    async def _test_github_integration_availability(self) -> bool:
        """Test if GitHub CLI integration is available and configured"""
        try:
            if not self.workflow.github_integration:
                logger.warning("GitHub integration not initialized")
                return False

            # Test basic GitHub CLI functionality
            test_result = self.workflow.github_integration.test_github_cli_connection()

            if test_result.get("success"):
                logger.info("GitHub CLI integration available and working")
                return True
            else:
                logger.warning(f"GitHub CLI test failed: {test_result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            logger.error(f"Error testing GitHub integration: {e}")
            return False

    def _create_sample_test_bugs(self) -> list:
        """Create sample bugs for testing"""
        test_bugs = [
            Bug(
                bug_id="TEST-001",
                title="Frontend form validation not working",
                description="User form validation fails to show error messages properly",
                severity=BugSeverity.HIGH,
                category=BugCategory.FRONTEND,
                source_test="test_frontend_validation",
                reproduction_steps=[
                    "1. Navigate to user registration form",
                    "2. Enter invalid email address",
                    "3. Submit form",
                    "4. No error message displayed"
                ]
            ),
            Bug(
                bug_id="TEST-002",
                title="API response timeout on large datasets",
                description="Backend API times out when processing large nonprofit datasets",
                severity=BugSeverity.CRITICAL,
                category=BugCategory.BACKEND,
                source_test="test_api_performance",
                reproduction_steps=[
                    "1. Query for nonprofits with >50K organizations",
                    "2. API call times out after 30 seconds",
                    "3. No response returned to frontend"
                ]
            ),
            Bug(
                bug_id="TEST-003",
                title="Cross-validation data mismatch",
                description="Backend processing results don't match frontend display",
                severity=BugSeverity.MEDIUM,
                category=BugCategory.INTEGRATION,
                source_test="test_cross_validation",
                reproduction_steps=[
                    "1. Process Heroes Bridge Foundation profile",
                    "2. Backend returns 15 opportunities",
                    "3. Frontend displays only 12 opportunities"
                ]
            )
        ]

        # Set effort estimates
        test_bugs[0].estimate_effort(4)  # Frontend fix
        test_bugs[1].estimate_effort(8)  # Backend performance fix
        test_bugs[2].estimate_effort(2)  # Integration fix

        logger.info(f"Created {len(test_bugs)} sample test bugs")
        return test_bugs

    async def _test_bug_to_issue_creation(self, bugs: list):
        """Test automated creation of GitHub issues from bugs"""
        try:
            logger.info("Testing GitHub issue creation from bugs...")

            # Test the bug-to-issue creation workflow
            await self.workflow._create_github_issues_for_bugs(bugs)

            # Verify bugs were updated with GitHub issue information
            issues_created = 0
            for bug in bugs:
                if bug.github_created and bug.github_issue_number:
                    issues_created += 1
                    self.test_results["github_issues_created"].append({
                        "bug_id": bug.bug_id,
                        "github_issue_number": bug.github_issue_number,
                        "github_issue_url": bug.github_issue_url,
                        "labels": bug.github_labels
                    })

            logger.info(f"Successfully created {issues_created} GitHub issues")
            self.test_results["tests_executed"].append("bug_to_issue_creation")

        except Exception as e:
            logger.error(f"Bug-to-issue creation test failed: {e}")
            self.test_results["errors"].append(f"Bug-to-issue creation: {e}")

    async def _test_subagent_github_coordination(self, bugs: list):
        """Test subagent coordination with GitHub issue assignment"""
        try:
            logger.info("Testing subagent coordination with GitHub...")

            # Create mock assignments for testing
            assignments = {
                "frontend-specialist": [bugs[0]],  # Frontend bug
                "performance-optimizer": [bugs[1]],  # Backend performance bug
                "integration-debugger": [bugs[2]]   # Integration bug
            }

            # Test GitHub issue assignment updates
            self.workflow._update_github_issue_assignments(assignments)

            # Verify assignment labels were added
            assignments_updated = 0
            for subagent, assigned_bugs in assignments.items():
                for bug in assigned_bugs:
                    expected_labels = self.workflow._map_subagent_to_github_labels(subagent)
                    if any(label in bug.github_labels for label in expected_labels):
                        assignments_updated += 1

            logger.info(f"Successfully updated {assignments_updated} GitHub issue assignments")
            self.test_results["tests_executed"].append("subagent_github_coordination")

        except Exception as e:
            logger.error(f"Subagent GitHub coordination test failed: {e}")
            self.test_results["errors"].append(f"Subagent coordination: {e}")

    async def _test_complete_workflow_integration(self):
        """Test complete workflow integration with GitHub"""
        try:
            logger.info("Testing complete workflow integration...")

            # Create mock test results that would trigger bugs
            mock_test_results = {
                "python_results": {
                    "TestProfileValidation": {
                        "success": False,
                        "stderr": "Profile validation failed: Invalid EIN format",
                        "execution_time": 2.5
                    }
                },
                "playwright_results": {
                    "TestUserInterface": {
                        "success": False,
                        "stderr": "Element not found: #submit-button",
                        "execution_time": 5.0
                    }
                }
            }

            # Execute the complete workflow
            workflow_results = await self.workflow.execute_bug_resolution_workflow(mock_test_results)

            # Verify workflow completed with GitHub integration
            if workflow_results.get("bugs_identified"):
                logger.info(f"Workflow identified {len(workflow_results['bugs_identified'])} bugs")

            if workflow_results.get("subagent_assignments"):
                logger.info(f"Workflow assigned bugs to {len(workflow_results['subagent_assignments'])} subagents")

            self.test_results["tests_executed"].append("complete_workflow_integration")
            self.test_results["workflow_results"] = workflow_results

        except Exception as e:
            logger.error(f"Complete workflow integration test failed: {e}")
            self.test_results["errors"].append(f"Complete workflow: {e}")

    async def _test_workflow_without_github(self):
        """Test workflow functionality when GitHub integration is not available"""
        logger.info("Testing workflow without GitHub CLI integration...")

        try:
            # Create simple test results
            mock_test_results = {
                "python_results": {
                    "TestSimple": {"success": False, "stderr": "Simple test error"}
                }
            }

            # Execute workflow
            workflow_results = await self.workflow.execute_bug_resolution_workflow(mock_test_results)

            logger.info("Workflow completed successfully without GitHub integration")
            self.test_results["tests_executed"].append("workflow_without_github")
            self.test_results["workflow_results"] = workflow_results

        except Exception as e:
            logger.error(f"Workflow without GitHub test failed: {e}")
            self.test_results["errors"].append(f"Workflow without GitHub: {e}")

    async def _generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("Generating GitHub integration test report...")

        self.test_results["test_end"] = datetime.now().isoformat()
        self.test_results["test_summary"] = {
            "total_tests": len(self.test_results["tests_executed"]),
            "errors_count": len(self.test_results["errors"]),
            "github_issues_created": len(self.test_results["github_issues_created"]),
            "integration_successful": len(self.test_results["errors"]) == 0,
            "github_available": self.test_results["integration_status"].get("github_available", False)
        }

        # Save test report
        report_file = Path(__file__).parent / "github_integration_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)

        logger.info(f"Test report saved to: {report_file}")

        # Print summary
        print("\n" + "=" * 60)
        print("GITHUB CLI INTEGRATION TEST RESULTS")
        print("=" * 60)
        print(f"Tests executed: {self.test_results['test_summary']['total_tests']}")
        print(f"GitHub available: {self.test_results['test_summary']['github_available']}")
        print(f"Issues created: {self.test_results['test_summary']['github_issues_created']}")
        print(f"Errors: {self.test_results['test_summary']['errors_count']}")
        print(f"Integration successful: {self.test_results['test_summary']['integration_successful']}")

        if self.test_results["errors"]:
            print("\nErrors encountered:")
            for error in self.test_results["errors"]:
                print(f"  - {error}")

        print(f"\nGitHub CLI Integration: {'PASSED' if self.test_results['test_summary']['integration_successful'] else 'FAILED'}")

async def main():
    """Main test execution"""
    print("Catalynx GitHub CLI Integration Test")
    print("Testing local GitHub issue tracking integration")
    print("=" * 60)

    tester = GitHubIntegrationTester()

    try:
        results = await tester.run_complete_integration_test()

        # Return appropriate exit code
        if results and results.get("test_summary", {}).get("integration_successful"):
            print("\nAll GitHub CLI integration tests passed!")
            return 0
        else:
            print("\nSome GitHub CLI integration tests failed.")
            return 1

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\nTest execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)