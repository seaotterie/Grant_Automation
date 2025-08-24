#!/usr/bin/env python3
"""
Manual Testing Execution Script
Systematic validation of Catalynx core functionality following the manual testing checklist
"""

import requests
import json
import time
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

class ManualTestExecutor:
    """Execute manual testing checklist systematically"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        self.profile_id = None
        
    def log_result(self, test_name, status, details="", expected="", actual=""):
        """Log test result"""
        result = {
            "test_name": test_name,
            "status": status,  # PASS, FAIL, SKIP
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "expected": expected,
            "actual": actual
        }
        self.results.append(result)
        
        status_emoji = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[SKIP]"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if status == "FAIL" and expected and actual:
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")
        print()
    
    def test_api_health(self):
        """Test 1.1: API Health Check"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_result(
                        "API Health Check",
                        "PASS",
                        f"Health endpoint responding correctly: {data}"
                    )
                else:
                    self.log_result(
                        "API Health Check", 
                        "FAIL",
                        f"Unexpected health status: {data}",
                        "status: healthy",
                        f"status: {data.get('status')}"
                    )
            else:
                self.log_result(
                    "API Health Check",
                    "FAIL", 
                    f"Health endpoint returned {response.status_code}",
                    "200 OK",
                    f"{response.status_code}"
                )
        except Exception as e:
            self.log_result(
                "API Health Check",
                "FAIL",
                f"Exception: {str(e)}"
            )
    
    def test_dashboard_load(self):
        """Test 1.2: Dashboard Loading"""
        try:
            response = self.session.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                content = response.text
                # Check for essential dashboard elements
                essential_elements = [
                    "Catalynx",  # Title
                    "Profile Management",  # Section
                    "Discovery",  # Section
                    "Analytics"  # Section
                ]
                
                missing_elements = []
                for element in essential_elements:
                    if element not in content:
                        missing_elements.append(element)
                
                if not missing_elements:
                    self.log_result(
                        "Dashboard Loading",
                        "PASS",
                        "All essential dashboard elements present"
                    )
                else:
                    self.log_result(
                        "Dashboard Loading",
                        "FAIL",
                        f"Missing elements: {missing_elements}",
                        "All essential elements present",
                        f"Missing: {missing_elements}"
                    )
            else:
                self.log_result(
                    "Dashboard Loading",
                    "FAIL",
                    f"Dashboard returned {response.status_code}",
                    "200 OK",
                    f"{response.status_code}"
                )
        except Exception as e:
            self.log_result(
                "Dashboard Loading",
                "FAIL",
                f"Exception: {str(e)}"
            )
    
    def test_profile_creation(self):
        """Test 2.1: Profile Creation"""
        try:
            profile_data = {
                "name": "Manual Test Organization",
                "organization_type": "nonprofit",
                "mission_statement": "Testing the Catalynx platform functionality",
                "ntee_codes": ["B25"],
                "focus_areas": ["education", "technology"],
                "annual_revenue": 1000000,
                "staff_size": 15,
                "geographic_scope": {
                    "states": ["VA"],
                    "nationwide": False,
                    "international": False
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/profiles",
                json=profile_data
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                # Handle nested profile structure
                profile_data = data.get("profile", data)
                self.profile_id = profile_data.get("profile_id")
                
                if self.profile_id:
                    self.log_result(
                        "Profile Creation",
                        "PASS",
                        f"Profile created successfully with ID: {self.profile_id}"
                    )
                else:
                    self.log_result(
                        "Profile Creation",
                        "FAIL",
                        "Profile created but no profile_id returned",
                        "profile_id in response",
                        "No profile_id"
                    )
            else:
                self.log_result(
                    "Profile Creation",
                    "FAIL",
                    f"Profile creation failed with {response.status_code}: {response.text}",
                    "200/201 status",
                    f"{response.status_code}"
                )
        except Exception as e:
            self.log_result(
                "Profile Creation",
                "FAIL",
                f"Exception: {str(e)}"
            )
    
    def test_profile_retrieval(self):
        """Test 2.2: Profile Retrieval"""
        if not self.profile_id:
            self.log_result(
                "Profile Retrieval",
                "SKIP",
                "No profile_id available (profile creation may have failed)"
            )
            return
        
        try:
            response = self.session.get(f"{self.base_url}/api/profiles/{self.profile_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle nested profile structure
                profile_data = data.get("profile", data)
                
                # Verify profile data integrity
                if (profile_data.get("name") == "Manual Test Organization" and
                    "B25" in profile_data.get("ntee_codes", []) and
                    profile_data.get("annual_revenue") == 1000000):
                    
                    self.log_result(
                        "Profile Retrieval",
                        "PASS",
                        "Profile data retrieved correctly"
                    )
                else:
                    self.log_result(
                        "Profile Retrieval",
                        "FAIL",
                        "Profile data integrity check failed",
                        "Correct profile data",
                        f"Data mismatch: {data}"
                    )
            else:
                self.log_result(
                    "Profile Retrieval",
                    "FAIL",
                    f"Profile retrieval failed with {response.status_code}",
                    "200 OK",
                    f"{response.status_code}"
                )
        except Exception as e:
            self.log_result(
                "Profile Retrieval",
                "FAIL",
                f"Exception: {str(e)}"
            )
    
    def test_entity_discovery(self):
        """Test 3.1: Entity-Based Discovery"""
        if not self.profile_id:
            self.log_result(
                "Entity Discovery",
                "SKIP",
                "No profile_id available"
            )
            return
        
        try:
            discovery_params = {
                "max_results": 5,
                "ntee_filter": ["B25"],
                "revenue_range": {
                    "min": 500000,
                    "max": 5000000
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/profiles/{self.profile_id}/discover/entity-analytics",
                json=discovery_params
            )
            
            if response.status_code in [200, 202]:
                if response.status_code == 200:
                    data = response.json()
                    opportunities = data.get("opportunities", [])
                    
                    if opportunities:
                        self.log_result(
                            "Entity Discovery",
                            "PASS",
                            f"Discovery returned {len(opportunities)} opportunities"
                        )
                    else:
                        self.log_result(
                            "Entity Discovery",
                            "PASS",
                            "Discovery completed successfully (no opportunities found)"
                        )
                else:  # 202 - Accepted for async processing
                    self.log_result(
                        "Entity Discovery",
                        "PASS",
                        "Discovery request accepted for async processing"
                    )
            else:
                self.log_result(
                    "Entity Discovery",
                    "FAIL",
                    f"Discovery failed with {response.status_code}: {response.text}",
                    "200/202 status",
                    f"{response.status_code}"
                )
        except Exception as e:
            self.log_result(
                "Entity Discovery",
                "FAIL",
                f"Exception: {str(e)}"
            )
    
    def test_cache_stats(self):
        """Test 3.2: Entity Cache Statistics"""
        try:
            response = self.session.get(f"{self.base_url}/api/discovery/entity-cache-stats")
            
            if response.status_code in [200, 404]:  # 404 is acceptable if cache is empty
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(
                        "Cache Statistics",
                        "PASS",
                        f"Cache stats retrieved: {data}"
                    )
                else:
                    self.log_result(
                        "Cache Statistics", 
                        "PASS",
                        "Cache stats endpoint accessible (cache may be empty)"
                    )
            else:
                self.log_result(
                    "Cache Statistics",
                    "FAIL",
                    f"Cache stats failed with {response.status_code}",
                    "200/404 status",
                    f"{response.status_code}"
                )
        except Exception as e:
            self.log_result(
                "Cache Statistics",
                "FAIL",
                f"Exception: {str(e)}"
            )
    
    def test_performance_baseline(self):
        """Test 4.1: Performance Baseline Validation"""
        try:
            # Test API response time
            start_time = time.perf_counter()
            response = self.session.get(f"{self.base_url}/api/health")
            api_response_time = (time.perf_counter() - start_time) * 1000  # ms
            
            if response.status_code == 200 and api_response_time < 100:  # <100ms target
                self.log_result(
                    "API Performance",
                    "PASS",
                    f"API response time: {api_response_time:.2f}ms (target: <100ms)"
                )
            elif response.status_code == 200:
                self.log_result(
                    "API Performance",
                    "FAIL",
                    f"API response too slow: {api_response_time:.2f}ms",
                    "<100ms",
                    f"{api_response_time:.2f}ms"
                )
            else:
                self.log_result(
                    "API Performance",
                    "FAIL",
                    f"API health check failed: {response.status_code}"
                )
        except Exception as e:
            self.log_result(
                "API Performance",
                "FAIL",
                f"Exception: {str(e)}"
            )
    
    def test_static_resources(self):
        """Test 5.1: Static Resource Loading"""
        try:
            static_resources = [
                "/static/style.css",
                "/static/app.js"
            ]
            
            all_passed = True
            failed_resources = []
            
            for resource in static_resources:
                try:
                    response = self.session.get(f"{self.base_url}{resource}")
                    if response.status_code != 200:
                        all_passed = False
                        failed_resources.append(f"{resource}: {response.status_code}")
                except Exception as e:
                    all_passed = False
                    failed_resources.append(f"{resource}: {str(e)}")
            
            if all_passed:
                self.log_result(
                    "Static Resources",
                    "PASS",
                    "All static resources loading correctly"
                )
            else:
                self.log_result(
                    "Static Resources",
                    "FAIL",
                    f"Failed resources: {failed_resources}",
                    "All resources load successfully",
                    f"Failures: {failed_resources}"
                )
        except Exception as e:
            self.log_result(
                "Static Resources",
                "FAIL",
                f"Exception: {str(e)}"
            )
    
    def cleanup_test_data(self):
        """Clean up test profile"""
        if self.profile_id:
            try:
                response = self.session.delete(f"{self.base_url}/api/profiles/{self.profile_id}")
                if response.status_code in [200, 204, 404]:
                    self.log_result(
                        "Test Cleanup",
                        "PASS",
                        f"Test profile {self.profile_id} cleaned up successfully"
                    )
                else:
                    self.log_result(
                        "Test Cleanup",
                        "FAIL",
                        f"Failed to clean up profile: {response.status_code}"
                    )
            except Exception as e:
                self.log_result(
                    "Test Cleanup",
                    "FAIL",
                    f"Cleanup exception: {str(e)}"
                )
    
    def generate_report(self):
        """Generate test execution report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in self.results if r["status"] == "SKIP"])
        
        print("\n" + "="*60)
        print("MANUAL TEST EXECUTION REPORT")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} [PASS]")
        print(f"Failed: {failed_tests} [FAIL]")
        print(f"Skipped: {skipped_tests} [SKIP]")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print("="*60)
        
        if failed_tests > 0:
            print("\nFAILED TESTS:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"[FAIL] {result['test_name']}: {result['details']}")
        
        # Save detailed report
        report_data = {
            "execution_time": datetime.now().isoformat(),
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "success_rate": passed_tests/total_tests*100
            },
            "results": self.results
        }
        
        report_file = Path(__file__).parent / f"manual_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\nDetailed report saved: {report_file}")
        return passed_tests == total_tests
    
    def run_all_tests(self):
        """Execute all manual tests systematically"""
        print("Starting Manual Test Execution...")
        print("="*60)
        
        # Core functionality tests
        self.test_api_health()
        self.test_dashboard_load()
        
        # Profile management tests
        self.test_profile_creation()
        self.test_profile_retrieval()
        
        # Discovery system tests
        self.test_entity_discovery()
        self.test_cache_stats()
        
        # Performance tests
        self.test_performance_baseline()
        
        # Static resource tests
        self.test_static_resources()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Generate report
        return self.generate_report()

def main():
    """Main execution function"""
    executor = ManualTestExecutor()
    
    try:
        success = executor.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()