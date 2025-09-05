#!/usr/bin/env python3
"""
AI Lite Scorer Integration Test
Tests the AI Lite Scorer integration with the ANALYZE tab API endpoints

This test validates:
1. AI Lite Scorer API endpoint functionality
2. Request/response data structure validation
3. ANALYZE tab integration flow
4. Error handling and fallback mechanisms
"""

import asyncio
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AILiteIntegrationTester:
    """
    Tests AI Lite Scorer integration with ANALYZE tab
    
    Validates that the AI Lite Scorer properly integrates with the
    frontend ANALYZE tab functionality and backend API endpoints
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_ai_lite_api_endpoint(self, profile_id: str) -> Dict[str, Any]:
        """Test AI Lite API endpoint with realistic data"""
        
        # Prepare sample analysis request
        ai_lite_request = {
            "opportunities": [
                {
                    "opportunity_id": "opp_test_result_001", 
                    "organization_name": "Test Foundation for Enhanced Discovery",
                    "source_type": "test_integration",
                    "description": "Test foundation discovered through enhanced discovery integration with education focus",
                    "funding_amount": 50000,
                    "application_deadline": "2024-06-15",
                    "current_score": 0.85,
                    "geographic_location": "National"
                },
                {
                    "opportunity_id": "opp_test_norfolk_foundation_1755640392",
                    "organization_name": "Norfolk Foundation Test 1755640392", 
                    "source_type": "foundation",
                    "description": "Norfolk Foundation - Test high-scoring opportunity for auto-promotion with healthcare focus",
                    "funding_amount": 75000,
                    "application_deadline": "2024-04-30",
                    "current_score": 0.89,
                    "geographic_location": "Virginia"
                },
                {
                    "opportunity_id": "opp_test_medium_foundation_1755640392",
                    "organization_name": "Medium Score Foundation Test 1755640392",
                    "source_type": "foundation", 
                    "description": "Medium Score Foundation - Test medium-scoring opportunity with community health programs",
                    "funding_amount": 25000,
                    "application_deadline": "2024-08-01",
                    "current_score": 0.7,
                    "geographic_location": "Virginia"
                }
            ],
            "analysis_type": "compatibility_scoring",
            "model_preference": "gpt-3.5-turbo",
            "cost_limit": 0.05,
            "priority": "standard"
        }
        
        # Test API endpoint
        result = {
            "test_name": "ai_lite_api_endpoint",
            "profile_id": profile_id,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            logger.info(f"Testing AI Lite API endpoint for profile: {profile_id}")
            
            # Make request to AI Lite endpoint
            endpoint = f"/api/profiles/{profile_id}/analyze/ai-lite"
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                json=ai_lite_request,
                timeout=60  # Allow time for AI processing
            )
            
            result["endpoint"] = endpoint
            result["request_data"] = ai_lite_request
            result["status_code"] = response.status_code
            result["response_headers"] = dict(response.headers)
            
            if response.status_code in [200, 202]:
                result["success"] = True
                result["response_data"] = response.json()
                
                # Validate response structure
                if "analysis_results" in result["response_data"]:
                    result["analysis_validation"] = "AI analysis results returned"
                elif "operation_id" in result["response_data"]:
                    result["analysis_validation"] = "Async operation initiated"
                else:
                    result["analysis_validation"] = "Unexpected response structure"
                    
                logger.info(f"AI Lite API test successful: {response.status_code}")
                
            else:
                result["success"] = False
                result["error"] = f"API returned status {response.status_code}"
                try:
                    result["error_details"] = response.json()
                except:
                    result["error_details"] = response.text
                    
                logger.error(f"AI Lite API test failed: {response.status_code}")
                
        except Exception as e:
            result["success"] = False
            result["error"] = f"Request failed: {str(e)}"
            logger.error(f"AI Lite integration test error: {str(e)}")
        
        return result
    
    def test_analyze_tab_integration(self, profile_id: str) -> Dict[str, Any]:
        """Test ANALYZE tab specific integration points"""
        
        result = {
            "test_name": "analyze_tab_integration", 
            "profile_id": profile_id,
            "timestamp": datetime.now().isoformat(),
            "integration_tests": []
        }
        
        # Test 1: Profile analytics endpoint (used by ANALYZE tab)
        analytics_test = {
            "test": "profile_analytics_endpoint",
            "endpoint": f"/api/profiles/{profile_id}/analytics",
            "description": "Test analytics data retrieval for ANALYZE tab"
        }
        
        try:
            response = self.session.get(f"{self.base_url}{analytics_test['endpoint']}", timeout=15)
            analytics_test["status_code"] = response.status_code
            analytics_test["success"] = response.status_code == 200
            
            if analytics_test["success"]:
                analytics_data = response.json()
                analytics_test["has_opportunities"] = "opportunities" in analytics_data
                analytics_test["has_scoring_stats"] = "scoring_stats" in analytics_data.get("analytics", {})
                analytics_test["data_validation"] = "Analytics data structure valid"
            else:
                analytics_test["error"] = f"Analytics endpoint failed: {response.status_code}"
                
        except Exception as e:
            analytics_test["success"] = False
            analytics_test["error"] = str(e)
        
        result["integration_tests"].append(analytics_test)
        
        # Test 2: Opportunities endpoint (feeds ANALYZE tab)
        opportunities_test = {
            "test": "opportunities_endpoint",
            "endpoint": f"/api/profiles/{profile_id}/opportunities", 
            "description": "Test opportunities data for ANALYZE tab display"
        }
        
        try:
            response = self.session.get(f"{self.base_url}{opportunities_test['endpoint']}", timeout=15)
            opportunities_test["status_code"] = response.status_code
            opportunities_test["success"] = response.status_code == 200
            
            if opportunities_test["success"]:
                opps_data = response.json()
                opportunities_test["total_opportunities"] = opps_data.get("total_opportunities", 0)
                opportunities_test["has_scoring_data"] = any(
                    opp.get("compatibility_score") is not None 
                    for opp in opps_data.get("opportunities", [])
                )
                opportunities_test["data_validation"] = f"Found {opportunities_test['total_opportunities']} opportunities"
            else:
                opportunities_test["error"] = f"Opportunities endpoint failed: {response.status_code}"
                
        except Exception as e:
            opportunities_test["success"] = False
            opportunities_test["error"] = str(e)
        
        result["integration_tests"].append(opportunities_test)
        
        # Test 3: AI service availability check
        ai_service_test = {
            "test": "ai_service_availability",
            "endpoint": "/api/analysis/status",
            "description": "Test AI analysis service availability"
        }
        
        try:
            response = self.session.get(f"{self.base_url}{ai_service_test['endpoint']}", timeout=10)
            ai_service_test["status_code"] = response.status_code
            ai_service_test["success"] = response.status_code == 200
            
            if ai_service_test["success"]:
                service_data = response.json()
                ai_service_test["ai_lite_available"] = service_data.get("ai_lite_service", "unknown")
                ai_service_test["ai_heavy_available"] = service_data.get("ai_heavy_service", "unknown")
            else:
                ai_service_test["error"] = f"AI service status failed: {response.status_code}"
                
        except Exception as e:
            ai_service_test["success"] = False
            ai_service_test["error"] = str(e)
        
        result["integration_tests"].append(ai_service_test)
        
        # Calculate overall success
        result["total_tests"] = len(result["integration_tests"])
        result["successful_tests"] = sum(1 for test in result["integration_tests"] if test.get("success", False))
        result["success_rate"] = result["successful_tests"] / result["total_tests"] if result["total_tests"] > 0 else 0
        result["overall_success"] = result["success_rate"] >= 0.7  # 70% success threshold
        
        return result
    
    def test_error_handling(self, profile_id: str) -> Dict[str, Any]:
        """Test AI Lite error handling and fallback mechanisms"""
        
        result = {
            "test_name": "error_handling",
            "profile_id": profile_id,
            "timestamp": datetime.now().isoformat(),
            "error_tests": []
        }
        
        # Test 1: Invalid request data
        invalid_request_test = {
            "test": "invalid_request_data",
            "description": "Test handling of malformed request data"
        }
        
        try:
            invalid_request = {
                "opportunities": [
                    {
                        "opportunity_id": "invalid_test",
                        # Missing required fields intentionally
                        "description": "Invalid test opportunity"
                    }
                ],
                "analysis_type": "invalid_type"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/profiles/{profile_id}/analyze/ai-lite",
                json=invalid_request,
                timeout=30
            )
            
            invalid_request_test["status_code"] = response.status_code
            invalid_request_test["success"] = response.status_code in [400, 422]  # Expect validation error
            invalid_request_test["handles_validation"] = response.status_code == 422
            
            if response.status_code in [400, 422]:
                invalid_request_test["error_response"] = response.json()
                invalid_request_test["validation"] = "Properly rejects invalid data"
            else:
                invalid_request_test["error"] = f"Unexpected response: {response.status_code}"
                
        except Exception as e:
            invalid_request_test["success"] = False
            invalid_request_test["error"] = str(e)
        
        result["error_tests"].append(invalid_request_test)
        
        # Test 2: Empty opportunities list
        empty_opportunities_test = {
            "test": "empty_opportunities_list",
            "description": "Test handling of empty opportunities list"
        }
        
        try:
            empty_request = {
                "opportunities": [],
                "analysis_type": "compatibility_scoring"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/profiles/{profile_id}/analyze/ai-lite",
                json=empty_request,
                timeout=30
            )
            
            empty_opportunities_test["status_code"] = response.status_code
            empty_opportunities_test["success"] = response.status_code in [400, 422]
            
            if response.status_code in [400, 422]:
                empty_opportunities_test["validation"] = "Properly handles empty opportunities"
            else:
                empty_opportunities_test["error"] = f"Unexpected response: {response.status_code}"
                
        except Exception as e:
            empty_opportunities_test["success"] = False
            empty_opportunities_test["error"] = str(e)
        
        result["error_tests"].append(empty_opportunities_test)
        
        # Calculate error handling success
        result["total_error_tests"] = len(result["error_tests"])
        result["successful_error_tests"] = sum(1 for test in result["error_tests"] if test.get("success", False))
        result["error_handling_score"] = result["successful_error_tests"] / result["total_error_tests"] if result["total_error_tests"] > 0 else 0
        
        return result
    
    def run_comprehensive_ai_lite_test(self, profile_id: str) -> Dict[str, Any]:
        """Run comprehensive AI Lite Scorer integration test"""
        
        logger.info(f"Starting comprehensive AI Lite integration test for profile: {profile_id}")
        
        # Run all test categories
        api_endpoint_results = self.test_ai_lite_api_endpoint(profile_id)
        analyze_tab_results = self.test_analyze_tab_integration(profile_id) 
        error_handling_results = self.test_error_handling(profile_id)
        
        # Compile comprehensive results
        comprehensive_results = {
            "test_suite": "AI Lite Scorer Integration Testing",
            "profile_id": profile_id,
            "timestamp": datetime.now().isoformat(),
            "test_results": {
                "api_endpoint": api_endpoint_results,
                "analyze_tab_integration": analyze_tab_results,
                "error_handling": error_handling_results
            }
        }
        
        # Calculate overall statistics
        all_tests = []
        
        # Count API endpoint test
        if api_endpoint_results.get("success") is not None:
            all_tests.append(api_endpoint_results)
        
        # Count integration tests
        for test in analyze_tab_results.get("integration_tests", []):
            all_tests.append(test)
            
        # Count error handling tests
        for test in error_handling_results.get("error_tests", []):
            all_tests.append(test)
        
        comprehensive_results["overall_statistics"] = {
            "total_test_categories": 3,
            "total_individual_tests": len(all_tests),
            "successful_tests": sum(1 for test in all_tests if test.get("success", False)),
            "failed_tests": sum(1 for test in all_tests if not test.get("success", False)),
            "overall_success_rate": sum(1 for test in all_tests if test.get("success", False)) / len(all_tests) if all_tests else 0
        }
        
        # Determine overall assessment
        success_rate = comprehensive_results["overall_statistics"]["overall_success_rate"]
        if success_rate >= 0.8:
            comprehensive_results["assessment"] = "EXCELLENT - AI Lite integration fully functional"
        elif success_rate >= 0.6:
            comprehensive_results["assessment"] = "GOOD - AI Lite integration mostly functional with minor issues"
        elif success_rate >= 0.4:
            comprehensive_results["assessment"] = "FAIR - AI Lite integration has significant issues requiring attention"
        else:
            comprehensive_results["assessment"] = "POOR - AI Lite integration requires major fixes"
        
        logger.info(f"AI Lite integration test completed. Success rate: {success_rate:.2%}")
        
        return comprehensive_results

def main():
    """Main test execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Lite Scorer Integration Tests")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for API tests")
    parser.add_argument("--profile-id", default="profile_f3adef3b653c", help="Profile ID to test with")
    parser.add_argument("--output", default="ai_lite_integration_results.json", help="Output file for test results")
    args = parser.parse_args()
    
    # Initialize tester
    tester = AILiteIntegrationTester(base_url=args.base_url)
    
    # Run comprehensive test
    results = tester.run_comprehensive_ai_lite_test(args.profile_id)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    stats = results["overall_statistics"]
    print(f"\nAI Lite Scorer Integration Test Results:")
    print(f"Profile: {args.profile_id}")
    print(f"Total Tests: {stats['total_individual_tests']}")
    print(f"Successful: {stats['successful_tests']}")
    print(f"Failed: {stats['failed_tests']}")
    print(f"Success Rate: {stats['overall_success_rate']:.2%}")
    print(f"Assessment: {results['assessment']}")
    print(f"Results saved to: {args.output}")

if __name__ == "__main__":
    main()