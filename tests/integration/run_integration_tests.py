#!/usr/bin/env python3
"""
Integration Test Suite Runner
Comprehensive test execution for backend-frontend integration testing

This script orchestrates all integration tests:
1. API-GUI binding verification
2. WebSocket integration testing  
3. ChatGPT prompt extraction for manual testing
4. Test result compilation and reporting
"""

import asyncio
import json
import sys
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import time

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from test_api_gui_binding import APIGUIBindingTester
from test_websocket_integration import WebSocketTester
from chatgpt_prompt_extractor import ChatGPTPromptExtractor

logger = logging.getLogger(__name__)

class IntegrationTestOrchestrator:
    """
    Orchestrates comprehensive integration testing suite
    
    Manages execution of all integration tests and compiles
    comprehensive results for analysis
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def check_server_availability(self) -> bool:
        """Check if Catalynx server is running and available"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"Server available: {health_data}")
                return True
            else:
                logger.error(f"Server health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Server not available: {str(e)}")
            return False
    
    def run_api_gui_binding_tests(self) -> Dict[str, Any]:
        """Run API-GUI binding verification tests"""
        logger.info("Starting API-GUI binding verification tests...")
        
        try:
            tester = APIGUIBindingTester(base_url=self.base_url)
            results = tester.run_all_tests()
            
            logger.info(f"API-GUI binding tests completed: {results.get('overall_statistics', {}).get('overall_success_rate', 0):.2%} success rate")
            return results
            
        except Exception as e:
            logger.error(f"API-GUI binding tests failed: {str(e)}")
            return {
                "error": f"API-GUI binding test execution failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_websocket_integration_tests(self) -> Dict[str, Any]:
        """Run WebSocket integration tests"""
        logger.info("Starting WebSocket integration tests...")
        
        try:
            tester = WebSocketTester(base_url=self.base_url)
            results = await tester.run_all_websocket_tests()
            
            logger.info(f"WebSocket integration tests completed: {results.get('overall_statistics', {}).get('overall_success_rate', 0):.2%} success rate")
            return results
            
        except Exception as e:
            logger.error(f"WebSocket integration tests failed: {str(e)}")
            return {
                "error": f"WebSocket test execution failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def run_chatgpt_prompt_extraction(self, output_dir: str = "chatgpt_test_package") -> Dict[str, Any]:
        """Run ChatGPT prompt extraction for manual testing"""
        logger.info("Extracting ChatGPT prompts for manual testing...")
        
        try:
            extractor = ChatGPTPromptExtractor()
            package_path = extractor.generate_comprehensive_test_package(output_dir)
            
            # Generate summary of extracted prompts
            return {
                "extraction_successful": True,
                "package_path": package_path,
                "ai_lite_prompt_extracted": Path(package_path) / "ai_lite_chatgpt_test.json",
                "ai_heavy_prompt_extracted": Path(package_path) / "ai_heavy_chatgpt_test.json",
                "instructions": f"Manual testing instructions available at: {package_path}/README_ChatGPT_Testing.md",
                "quick_start": f"Use prompts in: {package_path}/ai_lite_prompt.txt and {package_path}/ai_heavy_prompt.txt",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"ChatGPT prompt extraction failed: {str(e)}")
            return {
                "extraction_successful": False,
                "error": f"Prompt extraction failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def run_system_health_checks(self) -> Dict[str, Any]:
        """Run comprehensive system health checks"""
        logger.info("Running system health checks...")
        
        health_results = {
            "test_name": "system_health_checks",
            "checks": []
        }
        
        # Check 1: Server availability
        server_check = {
            "check": "server_availability",
            "description": "Verify Catalynx server is running and responsive",
            "success": False
        }
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            server_check["status_code"] = response.status_code
            server_check["response_data"] = response.json()
            server_check["success"] = response.status_code == 200
        except Exception as e:
            server_check["error"] = str(e)
        
        health_results["checks"].append(server_check)
        
        # Check 2: Processor registry status
        processor_check = {
            "check": "processor_registry",
            "description": "Verify all 18 processors are registered and available",
            "success": False
        }
        
        try:
            response = requests.get(f"{self.base_url}/api/processors/status", timeout=10)
            processor_check["status_code"] = response.status_code
            if response.status_code == 200:
                processor_data = response.json()
                processor_check["total_processors"] = len(processor_data.get("processors", []))
                processor_check["operational_processors"] = sum(
                    1 for p in processor_data.get("processors", []) 
                    if p.get("status") == "ready"
                )
                processor_check["success"] = processor_check["operational_processors"] >= 15
                processor_check["response_data"] = processor_data
        except Exception as e:
            processor_check["error"] = str(e)
        
        health_results["checks"].append(processor_check)
        
        # Check 3: Entity cache status
        cache_check = {
            "check": "entity_cache_status",
            "description": "Verify entity cache is operational with good hit rate",
            "success": False
        }
        
        try:
            response = requests.get(f"{self.base_url}/api/discovery/entity-cache-stats", timeout=10)
            cache_check["status_code"] = response.status_code
            if response.status_code == 200:
                cache_data = response.json()
                hit_rate = cache_data.get("hit_rate", 0)
                cache_check["hit_rate"] = hit_rate
                cache_check["success"] = hit_rate >= 0.75  # 75% minimum
                cache_check["response_data"] = cache_data
        except Exception as e:
            cache_check["error"] = str(e)
        
        health_results["checks"].append(cache_check)
        
        # Calculate overall health
        health_results["total_checks"] = len(health_results["checks"])
        health_results["successful_checks"] = sum(1 for check in health_results["checks"] if check.get("success", False))
        health_results["health_score"] = health_results["successful_checks"] / health_results["total_checks"]
        
        return health_results
    
    def generate_test_report(self, output_file: str = None) -> str:
        """Generate comprehensive test report"""
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"integration_test_report_{timestamp}.json"
        
        # Compile comprehensive report
        report = {
            "test_suite": "Catalynx Integration Testing Suite",
            "execution_summary": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration_seconds": (self.end_time - self.start_time).total_seconds() if (self.start_time and self.end_time) else None,
                "base_url": self.base_url
            },
            "test_results": self.test_results,
            "overall_analysis": self._analyze_overall_results()
        }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_file
    
    def _analyze_overall_results(self) -> Dict[str, Any]:
        """Analyze overall test results for summary"""
        
        analysis = {
            "total_test_categories": len(self.test_results),
            "successful_categories": 0,
            "failed_categories": 0,
            "individual_test_summary": {
                "total_tests": 0,
                "successful_tests": 0,
                "failed_tests": 0
            },
            "critical_issues": [],
            "recommendations": []
        }
        
        # Analyze each test category
        for category_name, category_results in self.test_results.items():
            if "error" in category_results:
                analysis["failed_categories"] += 1
                analysis["critical_issues"].append(f"{category_name}: {category_results['error']}")
            else:
                analysis["successful_categories"] += 1
                
                # Count individual tests if available
                if "overall_statistics" in category_results:
                    stats = category_results["overall_statistics"]
                    analysis["individual_test_summary"]["total_tests"] += stats.get("total_individual_tests", 0)
                    analysis["individual_test_summary"]["successful_tests"] += stats.get("successful_tests", 0)
                    analysis["individual_test_summary"]["failed_tests"] += stats.get("failed_tests", 0)
        
        # Calculate success rates
        if analysis["total_test_categories"] > 0:
            analysis["category_success_rate"] = analysis["successful_categories"] / analysis["total_test_categories"]
        
        if analysis["individual_test_summary"]["total_tests"] > 0:
            analysis["individual_test_success_rate"] = (
                analysis["individual_test_summary"]["successful_tests"] / 
                analysis["individual_test_summary"]["total_tests"]
            )
        
        # Generate recommendations
        if analysis.get("category_success_rate", 0) < 0.8:
            analysis["recommendations"].append("System has integration issues requiring immediate attention")
        if analysis.get("individual_test_success_rate", 0) < 0.7:
            analysis["recommendations"].append("Multiple individual tests failing - review system functionality")
        if len(analysis["critical_issues"]) > 0:
            analysis["recommendations"].append("Address critical issues before production deployment")
        
        return analysis
    
    async def run_comprehensive_integration_tests(self, chatgpt_output_dir: str = "chatgpt_test_package") -> str:
        """
        Run comprehensive integration test suite
        
        Args:
            chatgpt_output_dir: Directory for ChatGPT prompt extraction
            
        Returns:
            Path to generated test report
        """
        logger.info("Starting comprehensive integration test suite")
        self.start_time = datetime.now()
        
        # Step 1: System health checks
        logger.info("Step 1: System health checks")
        health_results = self.run_system_health_checks()
        self.test_results["system_health"] = health_results
        
        # Check if server is available before proceeding
        if not self.check_server_availability():
            self.test_results["server_availability"] = {
                "error": "Catalynx server not available",
                "recommendation": "Start server with: launch_catalynx_web.bat or python src/web/main.py",
                "timestamp": datetime.now().isoformat()
            }
            
            # Still run ChatGPT extraction since it doesn't require server
            logger.info("Server unavailable, running offline tests only")
            chatgpt_results = self.run_chatgpt_prompt_extraction(chatgpt_output_dir)
            self.test_results["chatgpt_prompt_extraction"] = chatgpt_results
            
            self.end_time = datetime.now()
            return self.generate_test_report()
        
        # Step 2: API-GUI binding tests
        logger.info("Step 2: API-GUI binding verification tests")
        api_gui_results = self.run_api_gui_binding_tests()
        self.test_results["api_gui_binding"] = api_gui_results
        
        # Step 3: WebSocket integration tests
        logger.info("Step 3: WebSocket integration tests")
        websocket_results = await self.run_websocket_integration_tests()
        self.test_results["websocket_integration"] = websocket_results
        
        # Step 4: ChatGPT prompt extraction
        logger.info("Step 4: ChatGPT prompt extraction")
        chatgpt_results = self.run_chatgpt_prompt_extraction(chatgpt_output_dir)
        self.test_results["chatgpt_prompt_extraction"] = chatgpt_results
        
        self.end_time = datetime.now()
        
        # Generate comprehensive report
        report_path = self.generate_test_report()
        logger.info(f"Comprehensive integration test suite completed. Report: {report_path}")
        
        return report_path

def print_test_summary(report_path: str):
    """Print summary of test results to console"""
    try:
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        print("\n" + "="*60)
        print("CATALYNX INTEGRATION TEST RESULTS SUMMARY")
        print("="*60)
        
        execution = report.get("execution_summary", {})
        print(f"Test Duration: {execution.get('duration_seconds', 0):.1f} seconds")
        print(f"Base URL: {execution.get('base_url', 'Unknown')}")
        
        analysis = report.get("overall_analysis", {})
        print(f"\nTest Categories: {analysis.get('total_test_categories', 0)}")
        print(f"Successful Categories: {analysis.get('successful_categories', 0)}")
        print(f"Failed Categories: {analysis.get('failed_categories', 0)}")
        
        if "category_success_rate" in analysis:
            print(f"Category Success Rate: {analysis['category_success_rate']:.1%}")
        
        individual = analysis.get("individual_test_summary", {})
        if individual.get("total_tests", 0) > 0:
            print(f"\nIndividual Tests: {individual['total_tests']}")
            print(f"Successful Tests: {individual['successful_tests']}")
            print(f"Failed Tests: {individual['failed_tests']}")
            
            if "individual_test_success_rate" in analysis:
                print(f"Individual Success Rate: {analysis['individual_test_success_rate']:.1%}")
        
        # Critical issues
        if analysis.get("critical_issues"):
            print(f"\n⚠️  CRITICAL ISSUES:")
            for issue in analysis["critical_issues"]:
                print(f"  - {issue}")
        
        # Recommendations
        if analysis.get("recommendations"):
            print(f"\n📋 RECOMMENDATIONS:")
            for rec in analysis["recommendations"]:
                print(f"  - {rec}")
        
        # ChatGPT extraction status
        chatgpt_results = report.get("test_results", {}).get("chatgpt_prompt_extraction", {})
        if chatgpt_results.get("extraction_successful"):
            print(f"\n🤖 CHATGPT TESTING PACKAGE READY:")
            print(f"  Location: {chatgpt_results.get('package_path', 'Unknown')}")
            print(f"  Instructions: {chatgpt_results.get('instructions', 'See README')}")
        
        print(f"\n📊 Full Report: {report_path}")
        print("="*60)
        
    except Exception as e:
        print(f"Error reading test report: {e}")

async def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Catalynx Integration Test Suite")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for API tests")
    parser.add_argument("--chatgpt-dir", default="chatgpt_test_package", help="Directory for ChatGPT prompt package")
    parser.add_argument("--output", help="Test report output file (auto-generated if not specified)")
    parser.add_argument("--quiet", action="store_true", help="Suppress console output")
    args = parser.parse_args()
    
    # Setup logging
    if not args.quiet:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    # Initialize test orchestrator
    orchestrator = IntegrationTestOrchestrator(base_url=args.base_url)
    
    # Run comprehensive test suite
    report_path = await orchestrator.run_comprehensive_integration_tests(args.chatgpt_dir)
    
    # Print summary unless quiet mode
    if not args.quiet:
        print_test_summary(report_path)
    else:
        print(f"Integration test report: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())