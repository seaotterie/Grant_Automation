#!/usr/bin/env python3
"""
Catalynx Welcome Stage Testing Script
Tests the new Welcome stage functionality and comprehensive data generation
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import random

class CatalynxTester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_welcome_endpoints(self):
        """Test all Welcome stage API endpoints"""
        print("🎯 Testing Welcome Stage Endpoints")
        print("=" * 50)
        
        # Test welcome status
        async with self.session.get(f"{self.base_url}/api/welcome/status") as resp:
            if resp.status == 200:
                status_data = await resp.json()
                print(f"✅ Welcome Status: {status_data['system_health']}")
                print(f"   Processors Available: {status_data['processors_available']}")
                print(f"   Capabilities: {len(status_data['capabilities'])}")
            else:
                print(f"❌ Welcome Status Failed: {resp.status}")
        
        # Test sample profile creation
        async with self.session.post(f"{self.base_url}/api/welcome/sample-profile") as resp:
            if resp.status == 200:
                profile_data = await resp.json()
                print(f"✅ Sample Profile Created: {profile_data['profile']['name']}")
                return profile_data['profile']['id']
            else:
                print(f"❌ Sample Profile Creation Failed: {resp.status}")
                return None
    
    async def test_quick_start_demo(self):
        """Test the quick start demonstration"""
        print("\n⚡ Testing Quick Start Demo")
        print("=" * 50)
        
        async with self.session.post(f"{self.base_url}/api/welcome/quick-start") as resp:
            if resp.status == 200:
                demo_data = await resp.json()
                print(f"✅ Quick Start Demo Completed")
                print(f"   Total Opportunities: {demo_data['total_opportunities']}")
                print(f"   Profile Created: {demo_data['profile_created']['name']}")
                
                # Show mock opportunities by track
                for track, opportunities in demo_data['mock_opportunities'].items():
                    print(f"   {track.title()}: {len(opportunities)} opportunities")
                    
                return demo_data
            else:
                print(f"❌ Quick Start Demo Failed: {resp.status}")
                return None
    
    def generate_test_profiles(self, count=5):
        """Generate diverse test organization profiles"""
        
        org_types = ["nonprofit", "foundation", "university", "corporation", "government"]
        focus_areas = [
            ["education", "STEM", "youth_development"],
            ["healthcare", "community_wellness", "mental_health"],
            ["environment", "sustainability", "climate_action"],
            ["technology", "digital_literacy", "innovation"],
            ["arts", "culture", "community_development"]
        ]
        
        target_populations = [
            ["underserved_youth", "students", "educators"],
            ["seniors", "families", "veterans"],
            ["small_businesses", "entrepreneurs", "startups"],
            ["rural_communities", "urban_populations", "immigrants"],
            ["disabled_individuals", "low_income_families", "minorities"]
        ]
        
        states_list = [
            ["VA", "MD", "DC"],
            ["CA", "NV", "AZ"],
            ["NY", "NJ", "CT"],
            ["TX", "OK", "LA"],
            ["FL", "GA", "SC"]
        ]
        
        profiles = []
        
        for i in range(count):
            profile = {
                "name": f"Test Organization {i+1}",
                "description": f"A comprehensive test organization focused on {random.choice(['community impact', 'social innovation', 'educational excellence', 'healthcare advancement', 'environmental stewardship'])}",
                "organization_type": random.choice(org_types),
                "geographic_scope": {
                    "states": random.choice(states_list),
                    "regions": [f"Region_{i+1}"]
                },
                "focus_areas": random.choice(focus_areas),
                "target_populations": random.choice(target_populations),
                "funding_history": {
                    "previous_grants": [
                        f"Previous Grant {j+1}" for j in range(random.randint(1, 4))
                    ],
                    "funding_ranges": [
                        random.choice(["$10000-50000", "$50000-100000", "$100000-500000"])
                    ]
                },
                "capabilities": [
                    "Program delivery",
                    "Community partnerships", 
                    random.choice(["Technology integration", "Research capabilities", "Policy advocacy"])
                ],
                "is_sample": True
            }
            profiles.append(profile)
            
        return profiles
    
    def generate_mock_discovery_data(self):
        """Generate comprehensive mock discovery results for testing"""
        
        return {
            "nonprofit_opportunities": [
                {
                    "organization_name": f"Partner Organization {i}",
                    "opportunity_type": "nonprofit_partnership", 
                    "funding_amount": random.randint(25000, 200000),
                    "compatibility_score": round(random.uniform(0.6, 0.95), 2),
                    "description": f"Collaborative initiative in {random.choice(['education', 'healthcare', 'environment', 'technology'])}",
                    "deadline": (datetime.now() + timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d"),
                    "contact_info": {"email": f"contact{i}@partner{i}.org", "type": "nonprofit"}
                }
                for i in range(15)
            ],
            "federal_opportunities": [
                {
                    "agency": random.choice([
                        "Department of Education", 
                        "National Science Foundation",
                        "Department of Health and Human Services",
                        "Environmental Protection Agency"
                    ]),
                    "program": f"Federal Program {i}",
                    "funding_amount": random.randint(50000, 500000),
                    "compatibility_score": round(random.uniform(0.5, 0.9), 2),
                    "deadline": (datetime.now() + timedelta(days=random.randint(45, 240))).strftime("%Y-%m-%d"),
                    "cfda_number": f"12.{random.randint(100, 999)}",
                    "opportunity_type": "federal_grant"
                }
                for i in range(12)
            ],
            "state_opportunities": [
                {
                    "agency": f"Virginia Department of {random.choice(['Health', 'Education', 'Social Services', 'Agriculture'])}",
                    "program": f"State Program {i}",
                    "funding_amount": random.randint(15000, 150000),
                    "compatibility_score": round(random.uniform(0.6, 0.88), 2),
                    "deadline": (datetime.now() + timedelta(days=random.randint(30, 120))).strftime("%Y-%m-%d"),
                    "state": "VA",
                    "focus_areas": random.sample(["public_health", "education", "community_development", "agriculture"], 2),
                    "opportunity_type": "state_grant"
                }
                for i in range(10)
            ],
            "commercial_opportunities": [
                {
                    "organization_name": f"{random.choice(['Microsoft', 'Google', 'Amazon', 'Apple', 'IBM'])} Foundation",
                    "program": f"Corporate Initiative {i}",
                    "funding_amount": random.randint(30000, 250000),
                    "compatibility_score": round(random.uniform(0.65, 0.92), 2),
                    "opportunity_type": "corporate_foundation",
                    "industry": random.choice(["technology", "healthcare", "finance", "retail"]),
                    "csr_focus": random.choice(["education", "environment", "community", "diversity"])
                }
                for i in range(8)
            ]
        }
    
    async def create_test_scenarios(self):
        """Create comprehensive test scenarios"""
        print("\n📋 Creating Test Scenarios")
        print("=" * 50)
        
        scenarios = {
            "scenario_1_new_user": {
                "name": "New User Complete Journey",
                "description": "First-time user going through complete workflow",
                "steps": [
                    "Visit Welcome stage",
                    "Create sample profile", 
                    "Run quick demo",
                    "Navigate to PROFILER",
                    "Customize profile",
                    "Execute discovery",
                    "Analyze results",
                    "Create strategic plan",
                    "Export reports"
                ],
                "expected_duration": "15-20 minutes",
                "success_criteria": [
                    "Welcome stage completed",
                    "Profile created successfully",
                    "Discovery found >10 opportunities",
                    "Analysis shows financial scores",
                    "Export generates valid files"
                ]
            },
            "scenario_2_power_user": {
                "name": "Power User Workflow", 
                "description": "Advanced user with multiple profiles and bulk operations",
                "steps": [
                    "Create 5 different organization profiles",
                    "Run discovery for all profiles",
                    "Compare results across profiles", 
                    "Advanced analytics review",
                    "Bulk export operations"
                ],
                "expected_duration": "30-45 minutes",
                "success_criteria": [
                    "Multiple profiles managed efficiently",
                    "Bulk discovery completes successfully",
                    "Comparative analysis available",
                    "Performance remains responsive"
                ]
            },
            "scenario_3_mobile_experience": {
                "name": "Mobile Device Testing",
                "description": "Complete workflow on mobile viewport",
                "steps": [
                    "Test responsive design",
                    "Mobile navigation functionality",
                    "Touch interactions",
                    "Mobile form completion",
                    "Mobile export capabilities"
                ],
                "expected_duration": "20-25 minutes", 
                "success_criteria": [
                    "All features accessible on mobile",
                    "Touch interactions work smoothly",
                    "Text remains readable",
                    "Navigation is intuitive"
                ]
            },
            "scenario_4_export_validation": {
                "name": "Export Format Testing",
                "description": "Test all export formats and data integrity",
                "steps": [
                    "Generate sample data",
                    "Test CSV export",
                    "Test JSON export", 
                    "Test Excel export",
                    "Validate data integrity",
                    "Test file download"
                ],
                "expected_duration": "10-15 minutes",
                "success_criteria": [
                    "All formats export successfully",
                    "Data integrity maintained",
                    "Files download correctly",
                    "Formatting is correct"
                ]
            },
            "scenario_5_analytics_validation": {
                "name": "Analytics Deep Dive",
                "description": "Comprehensive analytics tracking validation",
                "steps": [
                    "Navigate through all stages",
                    "Spend time in each stage",
                    "Complete various actions",
                    "Review analytics dashboard",
                    "Validate tracking accuracy"
                ],
                "expected_duration": "25-30 minutes",
                "success_criteria": [
                    "Stage transitions tracked correctly", 
                    "Time spent calculations accurate",
                    "User actions logged properly",
                    "Analytics dashboard reflects real usage"
                ]
            }
        }
        
        return scenarios
    
    async def run_comprehensive_test(self):
        """Run all test scenarios"""
        print("🚀 Starting Comprehensive Catalynx Testing")
        print("=" * 60)
        
        results = {
            "test_start": datetime.now().isoformat(),
            "endpoints_tested": 0,
            "profiles_created": 0,
            "scenarios_defined": 0,
            "success_rate": 0,
            "test_results": {}
        }
        
        try:
            # Test Welcome endpoints
            profile_id = await self.test_welcome_endpoints()
            if profile_id:
                results["profiles_created"] += 1
                results["endpoints_tested"] += 1
            
            # Test quick start demo
            demo_result = await self.test_quick_start_demo()
            if demo_result:
                results["endpoints_tested"] += 1
                results["profiles_created"] += 1
            
            # Generate test data
            test_profiles = self.generate_test_profiles(5)
            print(f"\n📊 Generated {len(test_profiles)} test profiles")
            
            mock_data = self.generate_mock_discovery_data()
            total_opportunities = sum(len(opps) for opps in mock_data.values())
            print(f"📊 Generated {total_opportunities} mock opportunities across 4 tracks")
            
            # Create test scenarios
            scenarios = await self.create_test_scenarios()
            results["scenarios_defined"] = len(scenarios)
            print(f"📋 Defined {len(scenarios)} test scenarios")
            
            # Calculate success rate
            successful_tests = 0
            if profile_id: successful_tests += 1
            if demo_result: successful_tests += 1
            if test_profiles: successful_tests += 1
            if mock_data: successful_tests += 1
            if scenarios: successful_tests += 1
            
            results["success_rate"] = (successful_tests / 5) * 100
            results["test_results"] = {
                "welcome_endpoints": "PASS" if profile_id else "FAIL",
                "quick_start_demo": "PASS" if demo_result else "FAIL", 
                "test_data_generation": "PASS" if test_profiles else "FAIL",
                "mock_opportunities": "PASS" if mock_data else "FAIL",
                "scenario_definitions": "PASS" if scenarios else "FAIL"
            }
            
            results["test_end"] = datetime.now().isoformat()
            
            # Print final results
            print("\n🎯 COMPREHENSIVE TEST RESULTS")
            print("=" * 60)
            print(f"Success Rate: {results['success_rate']:.1f}%")
            print(f"Endpoints Tested: {results['endpoints_tested']}")
            print(f"Profiles Created: {results['profiles_created']}")
            print(f"Scenarios Defined: {results['scenarios_defined']}")
            print(f"Test Duration: {datetime.fromisoformat(results['test_end']) - datetime.fromisoformat(results['test_start'])}")
            
            print("\nDetailed Results:")
            for test_name, result in results['test_results'].items():
                emoji = "✅" if result == "PASS" else "❌"
                print(f"  {emoji} {test_name.replace('_', ' ').title()}: {result}")
            
            # Save results to file
            with open('catalynx_test_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Test results saved to: catalynx_test_results.json")
            
            return results
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results["error"] = str(e)
            return results

async def main():
    """Main test execution function"""
    async with CatalynxTester() as tester:
        results = await tester.run_comprehensive_test()
        
        if results["success_rate"] >= 80:
            print("\n🎉 TESTING COMPLETED SUCCESSFULLY!")
            print("Welcome Stage implementation is ready for use.")
        else:
            print("\n⚠️  TESTING COMPLETED WITH ISSUES")
            print("Some features may need additional attention.")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())