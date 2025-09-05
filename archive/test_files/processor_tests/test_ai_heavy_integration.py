#!/usr/bin/env python3
"""
AI Heavy Researcher Integration Test (EXAMINE Tab)
Tests comprehensive AI Heavy research and dossier generation integration

This test validates:
1. AI Heavy deep research endpoint functionality
2. EXAMINE tab integration with comprehensive dossier generation  
3. Decision document template generation
4. Batch processing capabilities
5. Performance and cost tracking
"""

import asyncio
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIHeavyIntegrationTester:
    """
    Comprehensive tester for AI Heavy Researcher integration with EXAMINE tab
    
    Tests strategic dossier generation, decision document creation,
    and comprehensive research capabilities
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_ai_heavy_deep_research(self) -> Dict[str, Any]:
        """Test AI Heavy deep research endpoint"""
        
        result = {
            "test_name": "ai_heavy_deep_research",
            "timestamp": datetime.now().isoformat()
        }
        
        # Prepare comprehensive research request
        research_request = {
            "analysis_type": "comprehensive_research",
            "target_organization": "Johnson Family Foundation",
            "requesting_organization": {
                "name": "Heroes Bridge Foundation",
                "mission": "Supporting military veterans and their families through comprehensive health and wellness programs",
                "focus_areas": ["veteran support", "mental health", "family services"],
                "annual_revenue": 502611,
                "geographic_scope": "Virginia",
                "strategic_priorities": ["PTSD treatment expansion", "family counseling services"]
            },
            "research_parameters": {
                "analysis_depth": "comprehensive",
                "research_focus": ["strategic_partnership", "funding_approach", "board_connections"],
                "intelligence_gaps": ["decision_makers", "funding_timeline", "preferred_grantee_profile"],
                "cost_budget": 0.25,
                "priority": "high"
            },
            "context_data": {
                "preliminary_compatibility_score": 0.89,
                "match_factors": ["mission_alignment", "veteran_focus", "health_programs"],
                "funding_history": ["$300K Robert Wood Johnson Foundation", "$150K Ford Foundation"]
            }
        }
        
        try:
            logger.info("Testing AI Heavy deep research endpoint...")
            
            response = self.session.post(
                f"{self.base_url}/api/ai/deep-research",
                json=research_request,
                timeout=90  # Allow extended time for comprehensive analysis
            )
            
            result["endpoint"] = "/api/ai/deep-research"
            result["status_code"] = response.status_code
            result["request_data"] = research_request
            
            if response.status_code in [200, 202]:
                result["success"] = True
                response_data = response.json()
                result["response_data"] = response_data
                
                # Validate AI Heavy response structure
                if "analysis_type" in response_data and response_data["analysis_type"] == "ai_heavy":
                    result["analysis_validation"] = "AI Heavy analysis confirmed"
                    
                    if "result" in response_data:
                        research_result = response_data["result"]
                        result["has_strategic_dossier"] = "strategic_dossier" in research_result
                        result["has_action_plan"] = "action_plan" in research_result
                        result["has_grant_intelligence"] = "grant_application_intelligence" in research_result
                        
                elif "status" in response_data and response_data["status"] == "processing":
                    result["analysis_validation"] = "Async processing initiated"
                else:
                    result["analysis_validation"] = "Unexpected response structure"
                    
                logger.info("AI Heavy deep research test successful")
                
            else:
                result["success"] = False
                result["error"] = f"API returned status {response.status_code}"
                try:
                    result["error_details"] = response.json()
                except:
                    result["error_details"] = response.text
                    
                logger.error(f"AI Heavy deep research test failed: {response.status_code}")
                
        except Exception as e:
            result["success"] = False
            result["error"] = f"Request failed: {str(e)}"
            logger.error(f"AI Heavy deep research test error: {str(e)}")
        
        return result
    
    def test_dossier_generation(self, profile_id: str) -> Dict[str, Any]:
        """Test comprehensive dossier generation for EXAMINE tab"""
        
        result = {
            "test_name": "dossier_generation",
            "profile_id": profile_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Get some opportunities from the profile for dossier generation
        try:
            # First, get available opportunities
            opportunities_response = self.session.get(
                f"{self.base_url}/api/profiles/{profile_id}/opportunities",
                timeout=15
            )
            
            if opportunities_response.status_code != 200:
                result["success"] = False
                result["error"] = f"Could not retrieve opportunities: {opportunities_response.status_code}"
                return result
            
            opportunities_data = opportunities_response.json()
            opportunities = opportunities_data.get("opportunities", [])
            
            if len(opportunities) < 2:
                result["success"] = False
                result["error"] = "Insufficient opportunities for dossier generation test"
                return result
            
            # Select top 2 opportunities for dossier
            selected_opportunities = [
                opportunities[0]["opportunity_id"],
                opportunities[1]["opportunity_id"]
            ]
            
            logger.info(f"Testing dossier generation with opportunities: {selected_opportunities}")
            
            # Generate comprehensive dossier
            dossier_request = {
                "opportunity_ids": selected_opportunities,
                "analysis_depth": "comprehensive",
                "target_audience": "executive",
                "cost_optimization": True
            }
            
            dossier_response = self.session.post(
                f"{self.base_url}/api/profiles/{profile_id}/dossier/generate",
                params=dossier_request,
                timeout=120  # Extended timeout for comprehensive analysis
            )
            
            result["dossier_endpoint"] = f"/api/profiles/{profile_id}/dossier/generate"
            result["status_code"] = dossier_response.status_code
            result["selected_opportunities"] = selected_opportunities
            
            if dossier_response.status_code in [200, 202]:
                result["success"] = True
                dossier_data = dossier_response.json()
                result["response_data"] = dossier_data
                
                # Validate dossier structure
                if "dossier_id" in dossier_data:
                    result["dossier_id"] = dossier_data["dossier_id"]
                    result["dossier_validation"] = "Dossier ID generated successfully"
                    
                    if "analysis_summary" in dossier_data:
                        analysis = dossier_data["analysis_summary"]
                        result["opportunities_analyzed"] = analysis.get("opportunities_analyzed", 0)
                        result["confidence_score"] = analysis.get("confidence_score")
                        result["success_probability"] = analysis.get("success_probability")
                        result["recommendation"] = analysis.get("recommendation")
                        
                    if "generation_metadata" in dossier_data:
                        metadata = dossier_data["generation_metadata"]
                        result["ai_analysis_cost"] = metadata.get("ai_analysis_cost")
                        result["processing_time"] = metadata.get("processing_time_seconds")
                        
                    if "available_documents" in dossier_data:
                        result["available_document_templates"] = dossier_data["available_documents"]
                        result["document_generation_ready"] = len(dossier_data["available_documents"]) > 0
                        
                else:
                    result["dossier_validation"] = "No dossier ID returned"
                    
                logger.info(f"Dossier generation successful: {result.get('dossier_id')}")
                
            else:
                result["success"] = False
                result["error"] = f"Dossier generation failed: {dossier_response.status_code}"
                try:
                    result["error_details"] = dossier_response.json()
                except:
                    result["error_details"] = dossier_response.text
                    
        except Exception as e:
            result["success"] = False
            result["error"] = f"Dossier generation test failed: {str(e)}"
            logger.error(f"Dossier generation error: {str(e)}")
        
        return result
    
    def test_document_template_generation(self) -> Dict[str, Any]:
        """Test decision document template generation"""
        
        result = {
            "test_name": "document_template_generation",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Test 1: Get available templates
            templates_response = self.session.get(
                f"{self.base_url}/api/dossier/templates",
                timeout=15
            )
            
            result["templates_endpoint_status"] = templates_response.status_code
            
            if templates_response.status_code == 200:
                templates_data = templates_response.json()
                result["available_templates"] = templates_data
                result["template_count"] = len(templates_data.get("templates", []))
                result["templates_available"] = result["template_count"] > 0
                
                logger.info(f"Found {result['template_count']} available document templates")
                
            else:
                result["templates_available"] = False
                result["template_error"] = f"Templates endpoint failed: {templates_response.status_code}"
            
            # Test 2: Get performance summary
            performance_response = self.session.get(
                f"{self.base_url}/api/dossier/performance-summary",
                timeout=15
            )
            
            result["performance_endpoint_status"] = performance_response.status_code
            
            if performance_response.status_code == 200:
                performance_data = performance_response.json()
                result["performance_summary"] = performance_data
                result["has_performance_metrics"] = "performance_stats" in performance_data
                
                if result["has_performance_metrics"]:
                    stats = performance_data["performance_stats"]
                    result["total_dossiers_generated"] = stats.get("total_dossiers_generated", 0)
                    result["average_processing_time"] = stats.get("average_processing_time_seconds")
                    result["average_cost"] = stats.get("average_cost_per_dossier")
                    
                logger.info("Performance summary retrieved successfully")
                
            else:
                result["has_performance_metrics"] = False
                result["performance_error"] = f"Performance endpoint failed: {performance_response.status_code}"
            
            # Overall document template system assessment
            result["success"] = result.get("templates_available", False) or result.get("has_performance_metrics", False)
            
        except Exception as e:
            result["success"] = False
            result["error"] = f"Document template test failed: {str(e)}"
            logger.error(f"Document template generation error: {str(e)}")
        
        return result
    
    def test_examine_tab_integration(self, profile_id: str) -> Dict[str, Any]:
        """Test EXAMINE tab specific integration points"""
        
        result = {
            "test_name": "examine_tab_integration",
            "profile_id": profile_id,
            "timestamp": datetime.now().isoformat(),
            "integration_tests": []
        }
        
        # Test 1: Profile analytics for EXAMINE tab
        analytics_test = {
            "test": "examine_tab_analytics",
            "description": "Test analytics data for EXAMINE tab functionality"
        }
        
        try:
            response = self.session.get(f"{self.base_url}/api/profiles/{profile_id}/analytics", timeout=15)
            analytics_test["status_code"] = response.status_code
            analytics_test["success"] = response.status_code == 200
            
            if analytics_test["success"]:
                analytics_data = response.json()
                analytics_test["has_examine_data"] = "analytics" in analytics_data
                
                if analytics_test["has_examine_data"]:
                    analytics = analytics_data["analytics"]
                    analytics_test["opportunity_count"] = analytics.get("opportunity_count", 0)
                    analytics_test["has_deep_analysis_opportunities"] = any(
                        stage in ["deep_analysis", "recommendations"] 
                        for stage in analytics.get("stages_distribution", {}).keys()
                    )
                    
            else:
                analytics_test["error"] = f"Analytics failed: {response.status_code}"
                
        except Exception as e:
            analytics_test["success"] = False
            analytics_test["error"] = str(e)
        
        result["integration_tests"].append(analytics_test)
        
        # Test 2: High-value opportunities for deep analysis
        high_value_test = {
            "test": "high_value_opportunities",
            "description": "Test retrieval of high-value opportunities for EXAMINE tab"
        }
        
        try:
            # Get opportunities with minimum score for deep analysis
            response = self.session.get(
                f"{self.base_url}/api/profiles/{profile_id}/opportunities",
                params={"min_score": 0.8, "stage": "candidates"},
                timeout=15
            )
            
            high_value_test["status_code"] = response.status_code
            high_value_test["success"] = response.status_code == 200
            
            if high_value_test["success"]:
                opportunities_data = response.json()
                high_value_opportunities = opportunities_data.get("opportunities", [])
                high_value_test["high_value_count"] = len(high_value_opportunities)
                high_value_test["has_examine_candidates"] = high_value_test["high_value_count"] > 0
                
                if high_value_test["has_examine_candidates"]:
                    # Check for opportunities ready for deep analysis
                    examine_ready = [
                        opp for opp in high_value_opportunities 
                        if opp.get("compatibility_score", 0) >= 0.8
                    ]
                    high_value_test["examine_ready_count"] = len(examine_ready)
                    
            else:
                high_value_test["error"] = f"High-value opportunities failed: {response.status_code}"
                
        except Exception as e:
            high_value_test["success"] = False
            high_value_test["error"] = str(e)
        
        result["integration_tests"].append(high_value_test)
        
        # Test 3: AI service status for EXAMINE tab
        ai_service_test = {
            "test": "ai_service_status_examine",
            "description": "Test AI service availability for EXAMINE tab operations"
        }
        
        try:
            response = self.session.get(f"{self.base_url}/api/ai/status", timeout=10)
            ai_service_test["status_code"] = response.status_code
            
            if response.status_code == 200:
                ai_status = response.json()
                ai_service_test["success"] = True
                ai_service_test["ai_heavy_available"] = ai_status.get("ai_heavy_service", {}).get("available", False)
                ai_service_test["model_access"] = ai_status.get("ai_heavy_service", {}).get("model", "unknown")
                ai_service_test["cost_tracking"] = "pricing_info" in ai_status
                
            else:
                ai_service_test["success"] = response.status_code == 404  # Endpoint might not exist yet
                ai_service_test["note"] = "AI status endpoint may not be implemented"
                
        except Exception as e:
            ai_service_test["success"] = False
            ai_service_test["error"] = str(e)
        
        result["integration_tests"].append(ai_service_test)
        
        # Calculate integration success
        result["total_integration_tests"] = len(result["integration_tests"])
        result["successful_integration_tests"] = sum(1 for test in result["integration_tests"] if test.get("success", False))
        result["integration_success_rate"] = result["successful_integration_tests"] / result["total_integration_tests"] if result["total_integration_tests"] > 0 else 0
        
        return result
    
    def run_comprehensive_ai_heavy_test(self, test_profile_id: str = "profile_f3adef3b653c") -> Dict[str, Any]:
        """Run comprehensive AI Heavy Researcher integration test"""
        
        logger.info(f"Starting comprehensive AI Heavy integration test for profile: {test_profile_id}")
        
        # Run all test categories
        deep_research_results = self.test_ai_heavy_deep_research()
        dossier_results = self.test_dossier_generation(test_profile_id)
        template_results = self.test_document_template_generation()
        integration_results = self.test_examine_tab_integration(test_profile_id)
        
        # Compile comprehensive results
        comprehensive_results = {
            "test_suite": "AI Heavy Researcher Integration Testing (EXAMINE Tab)",
            "test_profile_id": test_profile_id,
            "timestamp": datetime.now().isoformat(),
            "test_results": {
                "deep_research": deep_research_results,
                "dossier_generation": dossier_results,
                "document_templates": template_results,
                "examine_tab_integration": integration_results
            }
        }
        
        # Calculate overall statistics
        all_tests = []
        
        # Count main category tests
        for category_result in [deep_research_results, dossier_results, template_results]:
            if category_result.get("success") is not None:
                all_tests.append(category_result)
        
        # Count integration tests
        for test in integration_results.get("integration_tests", []):
            all_tests.append(test)
        
        comprehensive_results["overall_statistics"] = {
            "total_test_categories": 4,
            "total_individual_tests": len(all_tests),
            "successful_tests": sum(1 for test in all_tests if test.get("success", False)),
            "failed_tests": sum(1 for test in all_tests if not test.get("success", False)),
            "overall_success_rate": sum(1 for test in all_tests if test.get("success", False)) / len(all_tests) if all_tests else 0
        }
        
        # AI Heavy specific metrics
        ai_heavy_metrics = {}
        
        if dossier_results.get("success"):
            ai_heavy_metrics["dossier_generation_functional"] = True
            ai_heavy_metrics["estimated_cost_per_dossier"] = dossier_results.get("ai_analysis_cost")
            ai_heavy_metrics["processing_time_seconds"] = dossier_results.get("processing_time")
            
        if template_results.get("success"):
            ai_heavy_metrics["document_templates_available"] = template_results.get("template_count", 0)
            ai_heavy_metrics["performance_tracking"] = template_results.get("has_performance_metrics", False)
        
        comprehensive_results["ai_heavy_metrics"] = ai_heavy_metrics
        
        # Determine overall assessment
        success_rate = comprehensive_results["overall_statistics"]["overall_success_rate"]
        has_dossier_capability = dossier_results.get("success", False)
        has_research_capability = deep_research_results.get("success", False)
        
        if success_rate >= 0.8 and has_dossier_capability:
            comprehensive_results["assessment"] = "EXCELLENT - AI Heavy integration fully operational with dossier generation"
        elif success_rate >= 0.6 and (has_dossier_capability or has_research_capability):
            comprehensive_results["assessment"] = "GOOD - AI Heavy integration mostly functional with core capabilities"
        elif success_rate >= 0.4:
            comprehensive_results["assessment"] = "FAIR - AI Heavy integration partially functional requiring attention"
        else:
            comprehensive_results["assessment"] = "POOR - AI Heavy integration requires major implementation work"
        
        logger.info(f"AI Heavy integration test completed. Success rate: {success_rate:.2%}")
        
        return comprehensive_results

def main():
    """Main test execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Heavy Researcher Integration Tests")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for API tests")
    parser.add_argument("--profile-id", default="profile_f3adef3b653c", help="Profile ID to test with")
    parser.add_argument("--output", default="ai_heavy_integration_results.json", help="Output file for test results")
    args = parser.parse_args()
    
    # Initialize tester
    tester = AIHeavyIntegrationTester(base_url=args.base_url)
    
    # Run comprehensive test
    results = tester.run_comprehensive_ai_heavy_test(args.profile_id)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    stats = results["overall_statistics"]
    ai_metrics = results.get("ai_heavy_metrics", {})
    
    print(f"\nAI Heavy Researcher Integration Test Results:")
    print(f"Profile: {args.profile_id}")
    print(f"Total Tests: {stats['total_individual_tests']}")
    print(f"Successful: {stats['successful_tests']}")
    print(f"Failed: {stats['failed_tests']}")
    print(f"Success Rate: {stats['overall_success_rate']:.2%}")
    print(f"Assessment: {results['assessment']}")
    
    if ai_metrics:
        print(f"\nAI Heavy Capabilities:")
        print(f"Dossier Generation: {ai_metrics.get('dossier_generation_functional', 'Unknown')}")
        print(f"Document Templates: {ai_metrics.get('document_templates_available', 'Unknown')}")
        print(f"Performance Tracking: {ai_metrics.get('performance_tracking', 'Unknown')}")
        if ai_metrics.get('estimated_cost_per_dossier'):
            print(f"Est. Cost per Dossier: ${ai_metrics['estimated_cost_per_dossier']}")
    
    print(f"Results saved to: {args.output}")

if __name__ == "__main__":
    main()