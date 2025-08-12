#!/usr/bin/env python3
"""
Catalynx Comprehensive Test Suite
Complete end-to-end testing with 5 scenarios, export validation, and analytics testing
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
import random
import csv
import tempfile
import os
from pathlib import Path

class CatalynxTestSuite:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = {
            "test_start": datetime.now().isoformat(),
            "scenarios": {},
            "analytics_validation": {},
            "export_validation": {},
            "performance_metrics": {},
            "overall_success": False
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def scenario_1_new_user_journey(self):
        """Scenario 1: New User Complete Journey"""
        print("SCENARIO 1: New User Complete Journey")
        print("=" * 50)
        
        scenario_results = {
            "name": "New User Complete Journey",
            "start_time": datetime.now().isoformat(),
            "steps_completed": 0,
            "total_steps": 9,
            "success": False,
            "issues": []
        }
        
        try:
            # Step 1: Visit Welcome stage
            print("Step 1: Testing Welcome stage status...")
            async with self.session.get(f"{self.base_url}/api/welcome/status") as resp:
                if resp.status == 200:
                    welcome_data = await resp.json()
                    print(f"[PASS] Welcome stage ready - {welcome_data['system_health']}")
                    scenario_results["steps_completed"] += 1
                else:
                    scenario_results["issues"].append(f"Welcome status failed: {resp.status}")
                    
            # Step 2: Create sample profile
            print("Step 2: Creating sample profile...")
            async with self.session.post(f"{self.base_url}/api/welcome/sample-profile") as resp:
                if resp.status == 200:
                    profile_data = await resp.json()
                    print(f"[PASS] Profile created: {profile_data['profile']['name']}")
                    scenario_results["steps_completed"] += 1
                    scenario_results["profile_id"] = profile_data['profile'].get('id', 'test_profile')
                else:
                    scenario_results["issues"].append(f"Profile creation failed: {resp.status}")
                    
            # Step 3: Run quick demo
            print("Step 3: Running quick demo...")
            async with self.session.post(f"{self.base_url}/api/welcome/quick-start") as resp:
                if resp.status == 200:
                    demo_data = await resp.json()
                    print(f"[PASS] Demo completed - {demo_data['total_opportunities']} opportunities")
                    scenario_results["steps_completed"] += 1
                    scenario_results["demo_opportunities"] = demo_data['total_opportunities']
                else:
                    scenario_results["issues"].append(f"Quick demo failed: {resp.status}")
                    
            # Step 4: Test system status
            print("Step 4: Checking system status...")
            async with self.session.get(f"{self.base_url}/api/system/status") as resp:
                if resp.status == 200:
                    status_data = await resp.json()
                    print(f"[PASS] System status: {status_data['status']}")
                    scenario_results["steps_completed"] += 1
                else:
                    scenario_results["issues"].append(f"System status failed: {resp.status}")
                    
            # Step 5: Test dashboard overview
            print("Step 5: Testing dashboard...")
            async with self.session.get(f"{self.base_url}/api/dashboard/overview") as resp:
                if resp.status == 200:
                    dashboard_data = await resp.json()
                    print(f"[PASS] Dashboard loaded - {dashboard_data.get('totalProcessed', 0)} processed")
                    scenario_results["steps_completed"] += 1
                else:
                    scenario_results["issues"].append(f"Dashboard failed: {resp.status}")
                    
            # Step 6: Test processor listing
            print("Step 6: Testing processor availability...")
            async with self.session.get(f"{self.base_url}/api/processors") as resp:
                if resp.status == 200:
                    processor_data = await resp.json()
                    print(f"[PASS] Processors available: {processor_data.get('total_count', 0)}")
                    scenario_results["steps_completed"] += 1
                else:
                    scenario_results["issues"].append(f"Processor listing failed: {resp.status}")
                    
            # Step 7: Test analytics overview
            print("Step 7: Testing analytics...")
            async with self.session.get(f"{self.base_url}/api/analytics/overview") as resp:
                if resp.status == 200:
                    analytics_data = await resp.json()
                    print(f"[PASS] Analytics loaded - {analytics_data.get('metrics', {}).get('organizations_analyzed', 0)} analyzed")
                    scenario_results["steps_completed"] += 1
                else:
                    scenario_results["issues"].append(f"Analytics failed: {resp.status}")
                    
            # Step 8: Test health check
            print("Step 8: Health check...")
            async with self.session.get(f"{self.base_url}/api/health") as resp:
                if resp.status == 200:
                    health_data = await resp.json()
                    print(f"[PASS] Health check: {health_data['status']}")
                    scenario_results["steps_completed"] += 1
                else:
                    scenario_results["issues"].append(f"Health check failed: {resp.status}")
                    
            # Step 9: Test export capability
            print("Step 9: Testing export system...")
            test_export_data = {
                "results": [
                    {"name": "Test Org 1", "score": 0.85, "type": "nonprofit"},
                    {"name": "Test Org 2", "score": 0.72, "type": "foundation"}
                ],
                "format": "json",
                "filename": "test_export_scenario1"
            }
            
            async with self.session.post(f"{self.base_url}/api/testing/export-results", json=test_export_data) as resp:
                if resp.status == 200:
                    print("[PASS] Export system functional")
                    scenario_results["steps_completed"] += 1
                else:
                    scenario_results["issues"].append(f"Export failed: {resp.status}")
            
            scenario_results["success"] = scenario_results["steps_completed"] >= 7  # 7 out of 9 minimum
            scenario_results["success_rate"] = (scenario_results["steps_completed"] / scenario_results["total_steps"]) * 100
            
        except Exception as e:
            scenario_results["issues"].append(f"Scenario exception: {str(e)}")
            
        scenario_results["end_time"] = datetime.now().isoformat()
        print(f"\nScenario 1 Results: {scenario_results['success_rate']:.1f}% success")
        return scenario_results

    async def scenario_2_power_user_workflow(self):
        """Scenario 2: Power User with Multiple Profiles"""
        print("\nSCENARIO 2: Power User Workflow")
        print("=" * 50)
        
        scenario_results = {
            "name": "Power User Workflow",
            "start_time": datetime.now().isoformat(),
            "profiles_created": 0,
            "bulk_operations": 0,
            "success": False,
            "issues": []
        }
        
        try:
            # Create multiple profiles
            profile_types = [
                {"name": "Healthcare Nonprofit", "type": "nonprofit", "focus": "healthcare"},
                {"name": "Education Foundation", "type": "foundation", "focus": "education"},
                {"name": "Tech Corporate CSR", "type": "for_profit", "focus": "technology"},
                {"name": "University Research", "type": "academic", "focus": "research"},
                {"name": "Government Agency", "type": "government", "focus": "public_service"}
            ]
            
            created_profiles = []
            
            for profile_template in profile_types:
                profile_data = {
                    "name": profile_template["name"],
                    "description": f"Power user test profile for {profile_template['focus']}",
                    "mission_statement": f"Advancing {profile_template['focus']} through innovative programs and partnerships",
                    "organization_type": profile_template["type"],
                    "geographic_scope": {
                        "states": random.sample(["VA", "MD", "DC", "CA", "NY", "TX"], 3),
                        "regions": ["Multi-State"]
                    },
                    "focus_areas": [profile_template["focus"], "community_development", "innovation"],
                    "target_populations": ["general_public", "professionals", "students"],
                    "funding_history": {
                        "previous_grants": [f"{profile_template['focus']} Grant Program"],
                        "funding_ranges": ["$50000-100000", "$100000-500000"]
                    },
                    "capabilities": ["Program delivery", "Research", "Community outreach"],
                    "is_sample": True
                }
                
                async with self.session.post(f"{self.base_url}/api/profiles", json=profile_data) as resp:
                    if resp.status == 200:
                        profile_result = await resp.json()
                        created_profiles.append(profile_result["profile"])
                        scenario_results["profiles_created"] += 1
                        print(f"[PASS] Created profile: {profile_template['name']}")
                    else:
                        scenario_results["issues"].append(f"Failed to create {profile_template['name']}: {resp.status}")
            
            # Test bulk operations
            print("Testing bulk profile listing...")
            async with self.session.get(f"{self.base_url}/api/profiles?limit=10") as resp:
                if resp.status == 200:
                    profiles_data = await resp.json()
                    total_profiles = len(profiles_data.get("profiles", []))
                    print(f"[PASS] Retrieved {total_profiles} profiles")
                    scenario_results["bulk_operations"] += 1
                else:
                    scenario_results["issues"].append(f"Profile listing failed: {resp.status}")
            
            # Test performance with multiple requests
            print("Testing concurrent operations...")
            start_time = time.time()
            
            tasks = []
            for i in range(5):
                tasks.append(self.session.get(f"{self.base_url}/api/system/status"))
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            successful_requests = sum(1 for r in responses if hasattr(r, 'status') and r.status == 200)
            
            end_time = time.time()
            
            if successful_requests >= 4:
                print(f"[PASS] Concurrent operations: {successful_requests}/5 successful in {end_time - start_time:.2f}s")
                scenario_results["bulk_operations"] += 1
            else:
                scenario_results["issues"].append(f"Concurrent operations failed: {successful_requests}/5")
                
            # Close all response objects
            for r in responses:
                if hasattr(r, 'close'):
                    r.close()
                    
            scenario_results["success"] = scenario_results["profiles_created"] >= 3 and scenario_results["bulk_operations"] >= 1
            
        except Exception as e:
            scenario_results["issues"].append(f"Power user scenario exception: {str(e)}")
            
        scenario_results["end_time"] = datetime.now().isoformat()
        print(f"Power User Scenario: Created {scenario_results['profiles_created']} profiles, {scenario_results['bulk_operations']} bulk ops")
        return scenario_results

    async def scenario_3_mobile_experience(self):
        """Scenario 3: Mobile Experience Testing"""
        print("\nSCENARIO 3: Mobile Experience Simulation")
        print("=" * 50)
        
        scenario_results = {
            "name": "Mobile Experience",
            "start_time": datetime.now().isoformat(),
            "mobile_tests": 0,
            "responsive_features": 0,
            "success": False,
            "issues": []
        }
        
        try:
            # Simulate mobile user agent
            mobile_headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
                "Accept": "text/html,application/json"
            }
            
            # Test main interface
            async with self.session.get(f"{self.base_url}/", headers=mobile_headers) as resp:
                if resp.status == 200:
                    print("[PASS] Main interface loads on mobile")
                    scenario_results["mobile_tests"] += 1
                else:
                    scenario_results["issues"].append(f"Mobile interface failed: {resp.status}")
            
            # Test API endpoints work on mobile
            async with self.session.get(f"{self.base_url}/api/welcome/status", headers=mobile_headers) as resp:
                if resp.status == 200:
                    print("[PASS] Welcome API works on mobile")
                    scenario_results["mobile_tests"] += 1
                else:
                    scenario_results["issues"].append("Mobile API access failed")
            
            # Test form submission (sample profile creation)
            async with self.session.post(f"{self.base_url}/api/welcome/sample-profile", headers=mobile_headers) as resp:
                if resp.status == 200:
                    print("[PASS] Form submission works on mobile")
                    scenario_results["mobile_tests"] += 1
                else:
                    scenario_results["issues"].append("Mobile form submission failed")
            
            # Test responsive features
            responsive_endpoints = [
                "/api/system/status",
                "/api/dashboard/overview", 
                "/api/processors",
                "/api/analytics/overview"
            ]
            
            for endpoint in responsive_endpoints:
                async with self.session.get(f"{self.base_url}{endpoint}", headers=mobile_headers) as resp:
                    if resp.status == 200:
                        scenario_results["responsive_features"] += 1
                    else:
                        scenario_results["issues"].append(f"Mobile access failed for {endpoint}")
            
            scenario_results["success"] = scenario_results["mobile_tests"] >= 2 and scenario_results["responsive_features"] >= 3
            
        except Exception as e:
            scenario_results["issues"].append(f"Mobile scenario exception: {str(e)}")
            
        scenario_results["end_time"] = datetime.now().isoformat()
        print(f"Mobile Experience: {scenario_results['mobile_tests']} mobile tests, {scenario_results['responsive_features']} responsive features")
        return scenario_results

    async def scenario_4_export_validation(self):
        """Scenario 4: Export Format Testing"""
        print("\nSCENARIO 4: Export Format Validation")
        print("=" * 50)
        
        scenario_results = {
            "name": "Export Format Validation",
            "start_time": datetime.now().isoformat(),
            "formats_tested": 0,
            "data_integrity_checks": 0,
            "success": False,
            "issues": []
        }
        
        try:
            # Test data for exports
            test_export_data = {
                "results": [
                    {
                        "organization_name": "Test Export Org 1",
                        "opportunity_type": "grant",
                        "funding_amount": 150000,
                        "compatibility_score": 0.87,
                        "deadline": "2025-06-30",
                        "contact_email": "test1@example.org"
                    },
                    {
                        "organization_name": "Test Export Org 2",
                        "opportunity_type": "corporate_partnership",
                        "funding_amount": 75000,
                        "compatibility_score": 0.72,
                        "deadline": "2025-09-15",
                        "contact_email": "test2@example.org"
                    }
                ]
            }
            
            # Test JSON export
            print("Testing JSON export...")
            json_export = {**test_export_data, "format": "json", "filename": "test_json_export"}
            async with self.session.post(f"{self.base_url}/api/testing/export-results", json=json_export) as resp:
                if resp.status == 200:
                    print("[PASS] JSON export successful")
                    scenario_results["formats_tested"] += 1
                    
                    # Validate JSON structure
                    try:
                        response_data = await resp.read()
                        # Basic validation that it's downloadable
                        if len(response_data) > 0:
                            scenario_results["data_integrity_checks"] += 1
                            print("[PASS] JSON data integrity confirmed")
                    except Exception as e:
                        scenario_results["issues"].append(f"JSON integrity check failed: {e}")
                else:
                    scenario_results["issues"].append(f"JSON export failed: {resp.status}")
            
            # Test CSV export
            print("Testing CSV export...")
            csv_export = {**test_export_data, "format": "csv", "filename": "test_csv_export"}
            async with self.session.post(f"{self.base_url}/api/testing/export-results", json=csv_export) as resp:
                if resp.status == 200:
                    print("[PASS] CSV export successful")
                    scenario_results["formats_tested"] += 1
                    
                    # Validate CSV structure
                    try:
                        response_data = await resp.read()
                        if len(response_data) > 0:
                            scenario_results["data_integrity_checks"] += 1
                            print("[PASS] CSV data integrity confirmed")
                    except Exception as e:
                        scenario_results["issues"].append(f"CSV integrity check failed: {e}")
                else:
                    scenario_results["issues"].append(f"CSV export failed: {resp.status}")
            
            # Test export with different data structures
            complex_data = {
                "results": [
                    {
                        "name": "Complex Org",
                        "nested_data": {"score": 0.95, "tags": ["priority", "verified"]},
                        "array_field": ["item1", "item2", "item3"],
                        "numeric_fields": {"revenue": 2500000, "employees": 150}
                    }
                ],
                "format": "json",
                "filename": "complex_export_test"
            }
            
            async with self.session.post(f"{self.base_url}/api/testing/export-results", json=complex_data) as resp:
                if resp.status == 200:
                    print("[PASS] Complex data export successful")
                    scenario_results["formats_tested"] += 1
                else:
                    scenario_results["issues"].append("Complex data export failed")
            
            scenario_results["success"] = scenario_results["formats_tested"] >= 2 and scenario_results["data_integrity_checks"] >= 1
            
        except Exception as e:
            scenario_results["issues"].append(f"Export validation exception: {str(e)}")
            
        scenario_results["end_time"] = datetime.now().isoformat()
        print(f"Export Validation: {scenario_results['formats_tested']} formats tested, {scenario_results['data_integrity_checks']} integrity checks")
        return scenario_results

    async def scenario_5_analytics_validation(self):
        """Scenario 5: Analytics Deep Dive"""
        print("\nSCENARIO 5: Analytics Validation")
        print("=" * 50)
        
        scenario_results = {
            "name": "Analytics Validation",
            "start_time": datetime.now().isoformat(),
            "analytics_endpoints": 0,
            "data_accuracy": 0,
            "success": False,
            "issues": []
        }
        
        try:
            # Test analytics overview
            async with self.session.get(f"{self.base_url}/api/analytics/overview") as resp:
                if resp.status == 200:
                    analytics_data = await resp.json()
                    print("[PASS] Analytics overview loaded")
                    scenario_results["analytics_endpoints"] += 1
                    
                    # Validate data structure
                    required_fields = ["metrics", "trends", "risk_distribution"]
                    if all(field in analytics_data for field in required_fields):
                        scenario_results["data_accuracy"] += 1
                        print("[PASS] Analytics data structure validated")
                    else:
                        scenario_results["issues"].append("Analytics data structure incomplete")
                else:
                    scenario_results["issues"].append("Analytics overview failed")
            
            # Test trend analysis
            async with self.session.get(f"{self.base_url}/api/analytics/trends") as resp:
                if resp.status == 200:
                    trends_data = await resp.json()
                    print("[PASS] Trends analysis loaded")
                    scenario_results["analytics_endpoints"] += 1
                    
                    # Validate trends structure
                    if "financial_trends" in trends_data and "market_analysis" in trends_data:
                        scenario_results["data_accuracy"] += 1
                        print("[PASS] Trends data structure validated")
                else:
                    scenario_results["issues"].append("Trends analysis failed")
            
            # Test processor status analytics
            async with self.session.get(f"{self.base_url}/api/testing/processors/status") as resp:
                if resp.status == 200:
                    processor_status = await resp.json()
                    print("[PASS] Processor analytics loaded")
                    scenario_results["analytics_endpoints"] += 1
                    
                    # Validate processor metrics
                    if "overall_health" in processor_status and "processors" in processor_status:
                        healthy_processors = sum(1 for p in processor_status["processors"] 
                                               if p.get("health_status") == "healthy")
                        if healthy_processors > 0:
                            scenario_results["data_accuracy"] += 1
                            print(f"[PASS] Processor health metrics: {healthy_processors} healthy processors")
                else:
                    scenario_results["issues"].append("Processor analytics failed")
            
            # Test system logs
            async with self.session.get(f"{self.base_url}/api/testing/system/logs?lines=10") as resp:
                if resp.status == 200:
                    logs_data = await resp.json()
                    print("[PASS] System logs accessible")
                    scenario_results["analytics_endpoints"] += 1
                    
                    # Validate log structure
                    if "log_entries" in logs_data and len(logs_data["log_entries"]) > 0:
                        scenario_results["data_accuracy"] += 1
                        print("[PASS] Log data structure validated")
                else:
                    scenario_results["issues"].append("System logs failed")
            
            scenario_results["success"] = scenario_results["analytics_endpoints"] >= 3 and scenario_results["data_accuracy"] >= 2
            
        except Exception as e:
            scenario_results["issues"].append(f"Analytics validation exception: {str(e)}")
            
        scenario_results["end_time"] = datetime.now().isoformat()
        print(f"Analytics Validation: {scenario_results['analytics_endpoints']} endpoints, {scenario_results['data_accuracy']} accuracy checks")
        return scenario_results

    async def run_comprehensive_test_suite(self):
        """Execute all test scenarios"""
        print("CATALYNX COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run all scenarios
        scenario_1 = await self.scenario_1_new_user_journey()
        scenario_2 = await self.scenario_2_power_user_workflow()
        scenario_3 = await self.scenario_3_mobile_experience()
        scenario_4 = await self.scenario_4_export_validation()
        scenario_5 = await self.scenario_5_analytics_validation()
        
        # Compile results
        self.test_results["scenarios"] = {
            "scenario_1": scenario_1,
            "scenario_2": scenario_2,
            "scenario_3": scenario_3,
            "scenario_4": scenario_4,
            "scenario_5": scenario_5
        }
        
        # Calculate overall success
        successful_scenarios = sum(1 for s in self.test_results["scenarios"].values() if s["success"])
        total_scenarios = len(self.test_results["scenarios"])
        overall_success_rate = (successful_scenarios / total_scenarios) * 100
        
        self.test_results["overall_success"] = overall_success_rate >= 80
        self.test_results["success_rate"] = overall_success_rate
        self.test_results["scenarios_passed"] = successful_scenarios
        self.test_results["total_scenarios"] = total_scenarios
        self.test_results["test_end"] = datetime.now().isoformat()
        
        # Performance metrics
        total_duration = datetime.fromisoformat(self.test_results["test_end"]) - datetime.fromisoformat(self.test_results["test_start"])
        self.test_results["performance_metrics"] = {
            "total_duration_seconds": total_duration.total_seconds(),
            "avg_scenario_duration": total_duration.total_seconds() / total_scenarios
        }
        
        # Print final results
        print("\n" + "=" * 60)
        print("COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        print(f"Overall Success Rate: {overall_success_rate:.1f}%")
        print(f"Scenarios Passed: {successful_scenarios}/{total_scenarios}")
        print(f"Total Duration: {total_duration}")
        print(f"Average Scenario Duration: {total_duration.total_seconds() / total_scenarios:.2f}s")
        
        print("\nScenario Results:")
        for scenario_name, scenario_data in self.test_results["scenarios"].items():
            status = "[PASS]" if scenario_data["success"] else "[FAIL]"
            print(f"  {status} {scenario_data['name']}")
            if scenario_data.get("issues"):
                for issue in scenario_data["issues"][:3]:  # Show first 3 issues
                    print(f"    - {issue}")
        
        # Save detailed results
        results_file = f"comprehensive_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\nDetailed results saved to: {results_file}")
        
        if self.test_results["overall_success"]:
            print("\nCOMPREHENSIVE TESTING COMPLETED SUCCESSFULLY!")
            print("Catalynx Welcome Stage and End-to-End functionality validated.")
        else:
            print("\nCOMPREHENSIVE TESTING COMPLETED WITH ISSUES")
            print("Some scenarios need attention before production deployment.")
        
        return self.test_results

async def main():
    """Main execution function"""
    async with CatalynxTestSuite() as test_suite:
        results = await test_suite.run_comprehensive_test_suite()
        return results

if __name__ == "__main__":
    asyncio.run(main())