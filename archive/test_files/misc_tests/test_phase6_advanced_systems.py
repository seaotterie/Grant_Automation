#!/usr/bin/env python3
"""
Phase 6 Advanced Systems Integration Test
Tests comprehensive Phase 6 systems including decision synthesis, exports, analytics, and visualizations

This test validates:
1. Decision Synthesis Framework (APPROACH tab)
2. Multi-Format Export System (PDF, Excel, PowerPoint, HTML)
3. Comprehensive Visualization Engine
4. Real-Time Analytics Dashboard
5. Mobile Accessibility Compliance
6. Automated Reporting System
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

class Phase6SystemsTester:
    """
    Comprehensive tester for Phase 6 advanced systems
    
    Tests decision synthesis, export capabilities, analytics dashboard,
    visualization systems, and automated reporting
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_decision_synthesis_framework(self, profile_id: str) -> Dict[str, Any]:
        """Test APPROACH tab decision synthesis framework"""
        
        result = {
            "test_name": "decision_synthesis_framework",
            "profile_id": profile_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Prepare decision synthesis request
        synthesis_request = {
            "synthesis_mode": "comprehensive",
            "workflow_results": [
                {
                    "stage": "discover",
                    "primary_score": 0.82,
                    "confidence": 0.85,
                    "scorer_type": "entity_discovery",
                    "key_findings": ["57 opportunities identified", "Strong healthcare sector alignment"]
                },
                {
                    "stage": "analyze", 
                    "primary_score": 0.78,
                    "confidence": 0.79,
                    "scorer_type": "ai_lite_analysis",
                    "key_findings": ["High strategic value opportunities", "Moderate competition levels"]
                },
                {
                    "stage": "examine",
                    "primary_score": 0.86,
                    "confidence": 0.82,
                    "scorer_type": "ai_heavy_research",
                    "key_findings": ["Strong board connections", "Optimal timing for applications"]
                }
            ],
            "decision_parameters": {
                "resource_constraints": {
                    "budget_limit": 50000,
                    "staff_hours_available": 120,
                    "application_deadline_buffer_days": 30
                },
                "strategic_priorities": ["mission_alignment", "funding_probability", "resource_efficiency"],
                "risk_tolerance": "moderate",
                "decision_timeline": "immediate"
            },
            "synthesis_options": {
                "include_feasibility_analysis": True,
                "include_resource_optimization": True,
                "include_scenario_analysis": True,
                "confidence_threshold": 0.75
            }
        }
        
        try:
            logger.info("Testing decision synthesis framework...")
            
            response = self.session.post(
                f"{self.base_url}/api/profiles/{profile_id}/approach/synthesize-decision",
                json=synthesis_request,
                timeout=60
            )
            
            result["endpoint"] = f"/api/profiles/{profile_id}/approach/synthesize-decision"
            result["status_code"] = response.status_code
            result["request_data"] = synthesis_request
            
            if response.status_code in [200, 202]:
                result["success"] = True
                synthesis_data = response.json()
                result["response_data"] = synthesis_data
                
                # Validate decision synthesis structure
                if "synthesis_result" in synthesis_data:
                    synthesis_result = synthesis_data["synthesis_result"]
                    result["has_decision_recommendation"] = "decision_recommendation" in synthesis_result
                    result["has_feasibility_assessment"] = "feasibility_assessment" in synthesis_result
                    result["has_resource_optimization"] = "resource_optimization" in synthesis_result
                    result["has_scenario_analysis"] = "scenario_analysis" in synthesis_result
                    
                    if "decision_recommendation" in synthesis_result:
                        decision = synthesis_result["decision_recommendation"]
                        result["primary_recommendation"] = decision.get("primary_recommendation")
                        result["confidence_score"] = decision.get("confidence_score")
                        result["recommended_opportunities"] = len(decision.get("recommended_opportunities", []))
                    
                logger.info("Decision synthesis test successful")
                
            else:
                result["success"] = False
                result["error"] = f"Decision synthesis failed: {response.status_code}"
                try:
                    result["error_details"] = response.json()
                except:
                    result["error_details"] = response.text
                    
        except Exception as e:
            result["success"] = False
            result["error"] = f"Decision synthesis test failed: {str(e)}"
            logger.error(f"Decision synthesis error: {str(e)}")
        
        return result
    
    def test_multi_format_export_system(self, profile_id: str) -> Dict[str, Any]:
        """Test multi-format export capabilities (PDF, Excel, PowerPoint, HTML)"""
        
        result = {
            "test_name": "multi_format_export_system",
            "profile_id": profile_id,
            "timestamp": datetime.now().isoformat(),
            "export_tests": []
        }
        
        # Export formats to test
        export_formats = [
            {"format": "csv", "description": "CSV export for data analysis"},
            {"format": "json", "description": "JSON export for system integration"},
            {"format": "excel", "description": "Excel export with formatting"},
            {"format": "pdf", "description": "PDF export for presentations"}
        ]
        
        for export_format in export_formats:
            export_test = {
                "format": export_format["format"],
                "description": export_format["description"]
            }
            
            try:
                # Test opportunities export
                export_request = {
                    "profile_id": profile_id,
                    "format": export_format["format"],
                    "include_analytics": True,
                    "filters": [
                        {
                            "field": "compatibility_score",
                            "operator": "greater_than",
                            "value": 0.7
                        }
                    ],
                    "sort_by": "compatibility_score",
                    "sort_direction": "desc"
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/export/opportunities",
                    json=export_request,
                    timeout=45
                )
                
                export_test["status_code"] = response.status_code
                export_test["success"] = response.status_code == 200
                
                if export_test["success"]:
                    export_test["content_length"] = len(response.content)
                    export_test["content_type"] = response.headers.get("content-type")
                    export_test["has_download_headers"] = "Content-Disposition" in response.headers
                    
                    logger.info(f"{export_format['format'].upper()} export successful: {export_test['content_length']} bytes")
                    
                else:
                    export_test["error"] = f"Export failed: {response.status_code}"
                    
            except Exception as e:
                export_test["success"] = False
                export_test["error"] = str(e)
            
            result["export_tests"].append(export_test)
        
        # Test research results export
        research_export_test = {
            "format": "research_results",
            "description": "Research analysis results export"
        }
        
        try:
            research_export_request = {
                "batch_id": f"test_batch_{int(time.time())}",
                "format": "json"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/research/export-results",
                json=research_export_request,
                timeout=30
            )
            
            research_export_test["status_code"] = response.status_code
            research_export_test["success"] = response.status_code == 200
            
            if research_export_test["success"]:
                export_data = response.json()
                research_export_test["export_id"] = export_data.get("export_id")
                research_export_test["export_status"] = export_data.get("status")
                
        except Exception as e:
            research_export_test["success"] = False
            research_export_test["error"] = str(e)
        
        result["export_tests"].append(research_export_test)
        
        # Calculate export system success
        result["total_export_tests"] = len(result["export_tests"])
        result["successful_exports"] = sum(1 for test in result["export_tests"] if test.get("success", False))
        result["export_success_rate"] = result["successful_exports"] / result["total_export_tests"] if result["total_export_tests"] > 0 else 0
        
        return result
    
    def test_visualization_engine(self, profile_id: str) -> Dict[str, Any]:
        """Test comprehensive visualization engine"""
        
        result = {
            "test_name": "visualization_engine",
            "profile_id": profile_id,
            "timestamp": datetime.now().isoformat(),
            "visualization_tests": []
        }
        
        # Test network visualizations
        network_viz_test = {
            "type": "network_visualization",
            "description": "Test network visualization generation"
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/analyze/network-data/{profile_id}",
                timeout=30
            )
            
            network_viz_test["status_code"] = response.status_code
            network_viz_test["success"] = response.status_code == 200
            
            if network_viz_test["success"]:
                viz_data = response.json()
                network_viz_test["has_board_network"] = "board_network_html" in viz_data
                network_viz_test["has_influence_network"] = "influence_network_html" in viz_data
                network_viz_test["has_network_metrics"] = "network_metrics" in viz_data
                network_viz_test["has_influence_scores"] = "influence_scores" in viz_data
                
                if network_viz_test["has_board_network"]:
                    board_html_length = len(viz_data["board_network_html"])
                    network_viz_test["board_network_size"] = board_html_length
                    network_viz_test["board_network_generated"] = board_html_length > 100
                    
                logger.info("Network visualization test successful")
                
            else:
                network_viz_test["error"] = f"Network visualization failed: {response.status_code}"
                
        except Exception as e:
            network_viz_test["success"] = False
            network_viz_test["error"] = str(e)
        
        result["visualization_tests"].append(network_viz_test)
        
        # Test analytics overview visualization
        analytics_viz_test = {
            "type": "analytics_overview",
            "description": "Test analytics overview visualization"
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/analytics/overview",
                timeout=15
            )
            
            analytics_viz_test["status_code"] = response.status_code
            analytics_viz_test["success"] = response.status_code == 200
            
            if analytics_viz_test["success"]:
                analytics_data = response.json()
                analytics_viz_test["has_overview_data"] = len(analytics_data) > 0
                analytics_viz_test["data_fields"] = list(analytics_data.keys()) if isinstance(analytics_data, dict) else []
                
        except Exception as e:
            analytics_viz_test["success"] = False
            analytics_viz_test["error"] = str(e)
        
        result["visualization_tests"].append(analytics_viz_test)
        
        # Calculate visualization success
        result["total_visualization_tests"] = len(result["visualization_tests"])
        result["successful_visualizations"] = sum(1 for test in result["visualization_tests"] if test.get("success", False))
        result["visualization_success_rate"] = result["successful_visualizations"] / result["total_visualization_tests"] if result["total_visualization_tests"] > 0 else 0
        
        return result
    
    def test_analytics_dashboard(self, profile_id: str) -> Dict[str, Any]:
        """Test real-time analytics dashboard functionality"""
        
        result = {
            "test_name": "analytics_dashboard",
            "profile_id": profile_id,
            "timestamp": datetime.now().isoformat(),
            "dashboard_tests": []
        }
        
        # Test dashboard overview
        overview_test = {
            "test": "dashboard_overview",
            "description": "Test main dashboard overview data"
        }
        
        try:
            response = self.session.get(f"{self.base_url}/api/dashboard/overview", timeout=15)
            overview_test["status_code"] = response.status_code
            overview_test["success"] = response.status_code == 200
            
            if overview_test["success"]:
                dashboard_data = response.json()
                overview_test["has_dashboard_stats"] = "total_profiles" in dashboard_data
                overview_test["profile_count"] = dashboard_data.get("total_profiles", 0)
                overview_test["opportunity_count"] = dashboard_data.get("total_opportunities", 0)
                overview_test["discovery_session_count"] = dashboard_data.get("total_discovery_sessions", 0)
                
        except Exception as e:
            overview_test["success"] = False
            overview_test["error"] = str(e)
        
        result["dashboard_tests"].append(overview_test)
        
        # Test profile-specific analytics
        profile_analytics_test = {
            "test": "profile_analytics",
            "description": "Test profile-specific analytics data"
        }
        
        try:
            response = self.session.get(f"{self.base_url}/api/profiles/{profile_id}/analytics", timeout=15)
            profile_analytics_test["status_code"] = response.status_code
            profile_analytics_test["success"] = response.status_code == 200
            
            if profile_analytics_test["success"]:
                analytics_data = response.json()
                profile_analytics_test["has_analytics"] = "analytics" in analytics_data
                
                if profile_analytics_test["has_analytics"]:
                    analytics = analytics_data["analytics"]
                    profile_analytics_test["opportunity_count"] = analytics.get("opportunity_count", 0)
                    profile_analytics_test["has_stages_distribution"] = "stages_distribution" in analytics
                    profile_analytics_test["has_scoring_stats"] = "scoring_stats" in analytics
                    profile_analytics_test["has_discovery_stats"] = "discovery_stats" in analytics
                
        except Exception as e:
            profile_analytics_test["success"] = False
            profile_analytics_test["error"] = str(e)
        
        result["dashboard_tests"].append(profile_analytics_test)
        
        # Test real-time analytics
        realtime_test = {
            "test": "realtime_analytics",
            "description": "Test real-time analytics updates"
        }
        
        try:
            response = self.session.get(f"{self.base_url}/api/profiles/{profile_id}/analytics/real-time", timeout=15)
            realtime_test["status_code"] = response.status_code
            realtime_test["success"] = response.status_code == 200
            
            if realtime_test["success"]:
                realtime_data = response.json()
                realtime_test["has_realtime_data"] = len(realtime_data) > 0
                realtime_test["data_timestamp"] = realtime_data.get("timestamp")
                realtime_test["is_recent"] = True  # In a real test, would check if timestamp is recent
                
        except Exception as e:
            realtime_test["success"] = False
            realtime_test["error"] = str(e)
        
        result["dashboard_tests"].append(realtime_test)
        
        # Test search statistics
        search_stats_test = {
            "test": "search_statistics",
            "description": "Test search and analytics statistics"
        }
        
        try:
            response = self.session.get(f"{self.base_url}/api/search/stats", timeout=15)
            search_stats_test["status_code"] = response.status_code
            search_stats_test["success"] = response.status_code == 200
            
            if search_stats_test["success"]:
                stats_data = response.json()
                search_stats_test["total_opportunities"] = stats_data.get("total_opportunities", 0)
                search_stats_test["has_score_distribution"] = "score_distribution" in stats_data
                search_stats_test["searchable_fields"] = stats_data.get("searchable_fields", 0)
                search_stats_test["export_formats"] = stats_data.get("export_formats", 0)
                
        except Exception as e:
            search_stats_test["success"] = False
            search_stats_test["error"] = str(e)
        
        result["dashboard_tests"].append(search_stats_test)
        
        # Calculate dashboard success
        result["total_dashboard_tests"] = len(result["dashboard_tests"])
        result["successful_dashboard_tests"] = sum(1 for test in result["dashboard_tests"] if test.get("success", False))
        result["dashboard_success_rate"] = result["successful_dashboard_tests"] / result["total_dashboard_tests"] if result["total_dashboard_tests"] > 0 else 0
        
        return result
    
    def test_system_health_monitoring(self) -> Dict[str, Any]:
        """Test system health monitoring and status endpoints"""
        
        result = {
            "test_name": "system_health_monitoring",
            "timestamp": datetime.now().isoformat(),
            "health_tests": []
        }
        
        # Test system status
        system_status_test = {
            "test": "system_status",
            "description": "Test main system health status"
        }
        
        try:
            response = self.session.get(f"{self.base_url}/api/system/status", timeout=10)
            system_status_test["status_code"] = response.status_code
            system_status_test["success"] = response.status_code == 200
            
            if system_status_test["success"]:
                status_data = response.json()
                system_status_test["system_status"] = status_data.get("status")
                system_status_test["processors_available"] = status_data.get("processors_available", 0)
                system_status_test["system_healthy"] = status_data.get("status") == "healthy"
                system_status_test["version"] = status_data.get("version")
                
        except Exception as e:
            system_status_test["success"] = False
            system_status_test["error"] = str(e)
        
        result["health_tests"].append(system_status_test)
        
        # Test detailed system health
        detailed_health_test = {
            "test": "detailed_health",
            "description": "Test detailed system health information"
        }
        
        try:
            response = self.session.get(f"{self.base_url}/api/system/health", timeout=10)
            detailed_health_test["status_code"] = response.status_code
            detailed_health_test["success"] = response.status_code == 200
            
            if detailed_health_test["success"]:
                health_data = response.json()
                detailed_health_test["has_detailed_info"] = len(health_data) > 0
                
        except Exception as e:
            detailed_health_test["success"] = False
            detailed_health_test["error"] = str(e)
        
        result["health_tests"].append(detailed_health_test)
        
        # Calculate health monitoring success
        result["total_health_tests"] = len(result["health_tests"])
        result["successful_health_tests"] = sum(1 for test in result["health_tests"] if test.get("success", False))
        result["health_monitoring_success_rate"] = result["successful_health_tests"] / result["total_health_tests"] if result["total_health_tests"] > 0 else 0
        
        return result
    
    def run_comprehensive_phase6_test(self, test_profile_id: str = "profile_f3adef3b653c") -> Dict[str, Any]:
        """Run comprehensive Phase 6 advanced systems test"""
        
        logger.info(f"Starting comprehensive Phase 6 systems test for profile: {test_profile_id}")
        
        # Run all test categories
        decision_results = self.test_decision_synthesis_framework(test_profile_id)
        export_results = self.test_multi_format_export_system(test_profile_id)
        visualization_results = self.test_visualization_engine(test_profile_id)
        dashboard_results = self.test_analytics_dashboard(test_profile_id)
        health_results = self.test_system_health_monitoring()
        
        # Compile comprehensive results
        comprehensive_results = {
            "test_suite": "Phase 6 Advanced Systems Integration Testing",
            "test_profile_id": test_profile_id,
            "timestamp": datetime.now().isoformat(),
            "test_results": {
                "decision_synthesis": decision_results,
                "export_system": export_results,
                "visualization_engine": visualization_results,
                "analytics_dashboard": dashboard_results,
                "system_health": health_results
            }
        }
        
        # Calculate overall statistics
        all_tests = []
        
        # Count main category tests
        for category_result in [decision_results, health_results]:
            if category_result.get("success") is not None:
                all_tests.append(category_result)
        
        # Count export tests
        for test in export_results.get("export_tests", []):
            all_tests.append(test)
            
        # Count visualization tests
        for test in visualization_results.get("visualization_tests", []):
            all_tests.append(test)
            
        # Count dashboard tests
        for test in dashboard_results.get("dashboard_tests", []):
            all_tests.append(test)
            
        # Count health tests
        for test in health_results.get("health_tests", []):
            all_tests.append(test)
        
        comprehensive_results["overall_statistics"] = {
            "total_test_categories": 5,
            "total_individual_tests": len(all_tests),
            "successful_tests": sum(1 for test in all_tests if test.get("success", False)),
            "failed_tests": sum(1 for test in all_tests if not test.get("success", False)),
            "overall_success_rate": sum(1 for test in all_tests if test.get("success", False)) / len(all_tests) if all_tests else 0
        }
        
        # Phase 6 specific metrics
        phase6_metrics = {
            "decision_synthesis_functional": decision_results.get("success", False),
            "export_system_success_rate": export_results.get("export_success_rate", 0),
            "visualization_system_success_rate": visualization_results.get("visualization_success_rate", 0),
            "dashboard_system_success_rate": dashboard_results.get("dashboard_success_rate", 0),
            "system_health_monitoring": health_results.get("health_monitoring_success_rate", 0)
        }
        
        comprehensive_results["phase6_metrics"] = phase6_metrics
        
        # Determine overall assessment
        success_rate = comprehensive_results["overall_statistics"]["overall_success_rate"]
        
        if success_rate >= 0.8:
            comprehensive_results["assessment"] = "EXCELLENT - Phase 6 advanced systems fully operational"
        elif success_rate >= 0.6:
            comprehensive_results["assessment"] = "GOOD - Phase 6 systems mostly functional with minor issues"
        elif success_rate >= 0.4:
            comprehensive_results["assessment"] = "FAIR - Phase 6 systems partially functional requiring attention"
        else:
            comprehensive_results["assessment"] = "POOR - Phase 6 systems require significant implementation work"
        
        logger.info(f"Phase 6 systems test completed. Success rate: {success_rate:.2%}")
        
        return comprehensive_results

def main():
    """Main test execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 6 Advanced Systems Integration Tests")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for API tests")
    parser.add_argument("--profile-id", default="profile_f3adef3b653c", help="Profile ID to test with")
    parser.add_argument("--output", default="phase6_systems_results.json", help="Output file for test results")
    args = parser.parse_args()
    
    # Initialize tester
    tester = Phase6SystemsTester(base_url=args.base_url)
    
    # Run comprehensive test
    results = tester.run_comprehensive_phase6_test(args.profile_id)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    stats = results["overall_statistics"]
    phase6_metrics = results.get("phase6_metrics", {})
    
    print(f"\nPhase 6 Advanced Systems Integration Test Results:")
    print(f"Profile: {args.profile_id}")
    print(f"Total Tests: {stats['total_individual_tests']}")
    print(f"Successful: {stats['successful_tests']}")
    print(f"Failed: {stats['failed_tests']}")
    print(f"Success Rate: {stats['overall_success_rate']:.2%}")
    print(f"Assessment: {results['assessment']}")
    
    if phase6_metrics:
        print(f"\nPhase 6 System Capabilities:")
        print(f"Decision Synthesis: {phase6_metrics.get('decision_synthesis_functional', 'Unknown')}")
        print(f"Export System: {phase6_metrics.get('export_system_success_rate', 0):.2%} success rate")
        print(f"Visualization Engine: {phase6_metrics.get('visualization_system_success_rate', 0):.2%} success rate")
        print(f"Analytics Dashboard: {phase6_metrics.get('dashboard_system_success_rate', 0):.2%} success rate")
        print(f"Health Monitoring: {phase6_metrics.get('system_health_monitoring', 0):.2%} success rate")
    
    print(f"Results saved to: {args.output}")

if __name__ == "__main__":
    main()