#!/usr/bin/env python3
"""
18-Processor Pipeline Validation Test
Comprehensive test of all 18 processors in the Catalynx system

This test validates:
1. All 18 processors are registered and available
2. Processor categories and functionality
3. Discovery pipeline integration
4. Error handling and resilience
"""

import asyncio
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from src.processors.registry import ProcessorAutoRegistry, get_processor_summary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessorPipelineValidator:
    """
    Comprehensive validator for 18-processor pipeline
    
    Tests processor registration, availability, and integration
    with the discovery and analysis pipeline
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.processor_registry = ProcessorAutoRegistry()
        
    def test_processor_registration(self) -> Dict[str, Any]:
        """Test that all 18 processors are properly registered"""
        
        result = {
            "test_name": "processor_registration",
            "timestamp": datetime.now().isoformat(),
            "expected_processors": 18
        }
        
        try:
            # Get processor summary from registry
            processor_summary = get_processor_summary()
            
            result["total_registered"] = processor_summary["total_processors"]
            result["processor_categories"] = processor_summary["categories"]
            result["processors"] = processor_summary["processors"]
            
            # Validate expected processor count
            result["registration_success"] = result["total_registered"] >= 18
            
            # Categorize processors
            data_fetchers = []
            analysis_processors = []
            other_processors = []
            
            for proc_info in result["processors"]:
                proc_name = proc_info["name"]
                if any(keyword in proc_name.lower() for keyword in ["fetch", "lookup", "downloader"]):
                    data_fetchers.append(proc_name)
                elif any(keyword in proc_name.lower() for keyword in ["scorer", "analyzer", "classifier", "assessor"]):
                    analysis_processors.append(proc_name)
                else:
                    other_processors.append(proc_name)
            
            result["categorized_processors"] = {
                "data_fetchers": data_fetchers,
                "analysis_processors": analysis_processors, 
                "other_processors": other_processors
            }
            
            result["category_counts"] = {
                "data_fetchers": len(data_fetchers),
                "analysis_processors": len(analysis_processors),
                "other_processors": len(other_processors)
            }
            
            logger.info(f"Found {result['total_registered']} registered processors")
            
        except Exception as e:
            result["registration_success"] = False
            result["error"] = str(e)
            logger.error(f"Processor registration test failed: {str(e)}")
        
        return result
    
    def test_system_status_endpoint(self) -> Dict[str, Any]:
        """Test system status API endpoint for processor information"""
        
        result = {
            "test_name": "system_status_endpoint",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = self.session.get(f"{self.base_url}/api/system/status", timeout=10)
            result["status_code"] = response.status_code
            
            if response.status_code == 200:
                status_data = response.json()
                result["system_status"] = status_data
                result["api_processor_count"] = status_data.get("processors_available", 0)
                result["system_health"] = status_data.get("status")
                result["api_success"] = True
                
                logger.info(f"System API reports {result['api_processor_count']} processors available")
                
            else:
                result["api_success"] = False
                result["error"] = f"API returned status {response.status_code}"
                
        except Exception as e:
            result["api_success"] = False
            result["error"] = str(e)
            logger.error(f"System status test failed: {str(e)}")
        
        return result
    
    def test_discovery_pipeline_integration(self, profile_id: str) -> Dict[str, Any]:
        """Test processors integration with discovery pipeline"""
        
        result = {
            "test_name": "discovery_pipeline_integration",
            "profile_id": profile_id,
            "timestamp": datetime.now().isoformat(),
            "pipeline_tests": []
        }
        
        # Test 1: Entity-based discovery (uses multiple processors)
        entity_discovery_test = {
            "test": "entity_based_discovery",
            "description": "Test entity-based discovery using multiple processors"
        }
        
        try:
            discovery_request = {
                "max_results": 3,
                "tracks": ["nonprofit_bmf"],
                "filters": {
                    "ntee_codes": ["A20"],
                    "revenue_range": {"min": 50000, "max": 1000000}
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/profiles/{profile_id}/discover/entity-analytics",
                json=discovery_request,
                timeout=45
            )
            
            entity_discovery_test["status_code"] = response.status_code
            entity_discovery_test["success"] = response.status_code in [200, 202]
            
            if entity_discovery_test["success"]:
                discovery_data = response.json()
                entity_discovery_test["discovery_results"] = discovery_data
                
                # Check for processor usage indicators
                if "processing_summary" in discovery_data:
                    entity_discovery_test["processors_used"] = discovery_data["processing_summary"].get("processors_used", [])
                elif "results" in discovery_data:
                    entity_discovery_test["results_count"] = len(discovery_data["results"])
                
                logger.info("Entity-based discovery test successful")
            else:
                entity_discovery_test["error"] = f"Discovery failed: {response.status_code}"
                
        except Exception as e:
            entity_discovery_test["success"] = False
            entity_discovery_test["error"] = str(e)
        
        result["pipeline_tests"].append(entity_discovery_test)
        
        # Test 2: Entity cache statistics (tests BMF and other data processors)
        cache_stats_test = {
            "test": "entity_cache_stats",
            "description": "Test entity cache populated by data processors"
        }
        
        try:
            response = self.session.get(f"{self.base_url}/api/discovery/entity-cache-stats", timeout=15)
            cache_stats_test["status_code"] = response.status_code
            cache_stats_test["success"] = response.status_code == 200
            
            if cache_stats_test["success"]:
                cache_data = response.json()
                cache_stats_test["entity_stats"] = cache_data
                
                # Validate cache shows processor activity
                total_entities = 0
                if "nonprofit_entities" in cache_data:
                    total_entities += cache_data["nonprofit_entities"].get("total", 0)
                if "government_entities" in cache_data:
                    total_entities += cache_data["government_entities"].get("total", 0)
                
                cache_stats_test["total_cached_entities"] = total_entities
                cache_stats_test["cache_populated"] = total_entities > 0
                
                logger.info(f"Entity cache contains {total_entities} entities from processors")
            else:
                cache_stats_test["error"] = f"Cache stats failed: {response.status_code}"
                
        except Exception as e:
            cache_stats_test["success"] = False
            cache_stats_test["error"] = str(e)
        
        result["pipeline_tests"].append(cache_stats_test)
        
        # Test 3: Profile analytics (tests scoring and analysis processors)
        analytics_test = {
            "test": "profile_analytics",
            "description": "Test analytics generation using analysis processors"
        }
        
        try:
            response = self.session.get(f"{self.base_url}/api/profiles/{profile_id}/analytics", timeout=15)
            analytics_test["status_code"] = response.status_code
            analytics_test["success"] = response.status_code == 200
            
            if analytics_test["success"]:
                analytics_data = response.json()
                analytics_test["has_analytics"] = "analytics" in analytics_data
                
                if analytics_test["has_analytics"]:
                    analytics = analytics_data["analytics"]
                    analytics_test["opportunity_count"] = analytics.get("opportunity_count", 0)
                    analytics_test["has_scoring_stats"] = "scoring_stats" in analytics
                    analytics_test["has_discovery_stats"] = "discovery_stats" in analytics
                
                logger.info("Profile analytics test successful")
            else:
                analytics_test["error"] = f"Analytics failed: {response.status_code}"
                
        except Exception as e:
            analytics_test["success"] = False
            analytics_test["error"] = str(e)
        
        result["pipeline_tests"].append(analytics_test)
        
        # Calculate pipeline integration success
        result["total_pipeline_tests"] = len(result["pipeline_tests"])
        result["successful_pipeline_tests"] = sum(1 for test in result["pipeline_tests"] if test.get("success", False))
        result["pipeline_success_rate"] = result["successful_pipeline_tests"] / result["total_pipeline_tests"] if result["total_pipeline_tests"] > 0 else 0
        
        return result
    
    def test_processor_resilience(self) -> Dict[str, Any]:
        """Test processor error handling and resilience"""
        
        result = {
            "test_name": "processor_resilience",
            "timestamp": datetime.now().isoformat(),
            "resilience_tests": []
        }
        
        # Test 1: Invalid profile discovery (should fail gracefully)
        invalid_profile_test = {
            "test": "invalid_profile_discovery",
            "description": "Test processor resilience with invalid profile"
        }
        
        try:
            invalid_request = {
                "max_results": 5,
                "tracks": ["nonprofit_bmf"]
            }
            
            response = self.session.post(
                f"{self.base_url}/api/profiles/invalid_profile_id/discover/entity-analytics",
                json=invalid_request,
                timeout=30
            )
            
            invalid_profile_test["status_code"] = response.status_code
            invalid_profile_test["handles_gracefully"] = response.status_code in [400, 404, 422]
            invalid_profile_test["success"] = invalid_profile_test["handles_gracefully"]
            
            if response.status_code >= 400:
                invalid_profile_test["error_response"] = response.json()
                
        except Exception as e:
            invalid_profile_test["success"] = False
            invalid_profile_test["error"] = str(e)
        
        result["resilience_tests"].append(invalid_profile_test)
        
        # Test 2: Malformed discovery request (should validate properly)
        malformed_request_test = {
            "test": "malformed_request",
            "description": "Test processor input validation"
        }
        
        try:
            malformed_request = {
                "max_results": "invalid_number",
                "tracks": ["invalid_track"],
                "invalid_field": "should_be_ignored"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/profiles/profile_test_metrics/discover/entity-analytics",
                json=malformed_request,
                timeout=30
            )
            
            malformed_request_test["status_code"] = response.status_code
            malformed_request_test["validates_input"] = response.status_code in [400, 422]
            malformed_request_test["success"] = malformed_request_test["validates_input"]
            
            if response.status_code >= 400:
                malformed_request_test["validation_response"] = response.json()
                
        except Exception as e:
            malformed_request_test["success"] = False
            malformed_request_test["error"] = str(e)
        
        result["resilience_tests"].append(malformed_request_test)
        
        # Calculate resilience test success
        result["total_resilience_tests"] = len(result["resilience_tests"])
        result["successful_resilience_tests"] = sum(1 for test in result["resilience_tests"] if test.get("success", False))
        result["resilience_success_rate"] = result["successful_resilience_tests"] / result["total_resilience_tests"] if result["total_resilience_tests"] > 0 else 0
        
        return result
    
    def run_comprehensive_processor_test(self, test_profile_id: str = "profile_test_metrics") -> Dict[str, Any]:
        """Run comprehensive processor pipeline validation"""
        
        logger.info("Starting comprehensive 18-processor pipeline validation")
        
        # Run all test categories
        registration_results = self.test_processor_registration()
        system_status_results = self.test_system_status_endpoint()
        pipeline_results = self.test_discovery_pipeline_integration(test_profile_id)
        resilience_results = self.test_processor_resilience()
        
        # Compile comprehensive results
        comprehensive_results = {
            "test_suite": "18-Processor Pipeline Validation",
            "test_profile_id": test_profile_id,
            "timestamp": datetime.now().isoformat(),
            "test_results": {
                "processor_registration": registration_results,
                "system_status": system_status_results,
                "pipeline_integration": pipeline_results,
                "processor_resilience": resilience_results
            }
        }
        
        # Calculate overall statistics
        all_tests = []
        
        # Count registration test
        if registration_results.get("registration_success") is not None:
            all_tests.append(registration_results)
        
        # Count system status test
        if system_status_results.get("api_success") is not None:
            all_tests.append(system_status_results)
        
        # Count pipeline tests
        for test in pipeline_results.get("pipeline_tests", []):
            all_tests.append(test)
            
        # Count resilience tests
        for test in resilience_results.get("resilience_tests", []):
            all_tests.append(test)
        
        comprehensive_results["overall_statistics"] = {
            "total_test_categories": 4,
            "total_individual_tests": len(all_tests),
            "successful_tests": sum(1 for test in all_tests if test.get("success", False) or test.get("registration_success", False) or test.get("api_success", False)),
            "failed_tests": sum(1 for test in all_tests if not (test.get("success", False) or test.get("registration_success", False) or test.get("api_success", False))),
            "overall_success_rate": 0
        }
        
        # Calculate success rate
        if comprehensive_results["overall_statistics"]["total_individual_tests"] > 0:
            comprehensive_results["overall_statistics"]["overall_success_rate"] = (
                comprehensive_results["overall_statistics"]["successful_tests"] / 
                comprehensive_results["overall_statistics"]["total_individual_tests"]
            )
        
        # Processor summary
        processor_count = registration_results.get("total_registered", 0)
        api_processor_count = system_status_results.get("api_processor_count", 0)
        
        comprehensive_results["processor_summary"] = {
            "expected_processors": 18,
            "registered_processors": processor_count,
            "api_reported_processors": api_processor_count,
            "processor_count_consistent": processor_count == api_processor_count,
            "meets_expectations": processor_count >= 18
        }
        
        # Determine overall assessment
        success_rate = comprehensive_results["overall_statistics"]["overall_success_rate"]
        processor_count_ok = comprehensive_results["processor_summary"]["meets_expectations"]
        
        if success_rate >= 0.8 and processor_count_ok:
            comprehensive_results["assessment"] = "EXCELLENT - 18-processor pipeline fully operational"
        elif success_rate >= 0.6 and processor_count_ok:
            comprehensive_results["assessment"] = "GOOD - Processor pipeline mostly functional with minor issues"
        elif success_rate >= 0.4 or processor_count_ok:
            comprehensive_results["assessment"] = "FAIR - Processor pipeline has some issues requiring attention"
        else:
            comprehensive_results["assessment"] = "POOR - Processor pipeline requires significant fixes"
        
        logger.info(f"Processor pipeline validation completed. Success rate: {success_rate:.2%}")
        
        return comprehensive_results

def main():
    """Main test execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="18-Processor Pipeline Validation Tests")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for API tests")
    parser.add_argument("--profile-id", default="profile_test_metrics", help="Profile ID to test with")
    parser.add_argument("--output", default="processor_pipeline_results.json", help="Output file for test results")
    args = parser.parse_args()
    
    # Initialize validator
    validator = ProcessorPipelineValidator(base_url=args.base_url)
    
    # Run comprehensive test
    results = validator.run_comprehensive_processor_test(args.profile_id)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    stats = results["overall_statistics"]
    processor_summary = results["processor_summary"]
    
    print(f"\n18-Processor Pipeline Validation Results:")
    print(f"Expected Processors: {processor_summary['expected_processors']}")
    print(f"Registered Processors: {processor_summary['registered_processors']}")
    print(f"API Reported Processors: {processor_summary['api_reported_processors']}")
    print(f"Processor Count Consistent: {processor_summary['processor_count_consistent']}")
    print(f"Meets Expectations: {processor_summary['meets_expectations']}")
    print(f"\nTotal Tests: {stats['total_individual_tests']}")
    print(f"Successful: {stats['successful_tests']}")
    print(f"Failed: {stats['failed_tests']}")
    print(f"Success Rate: {stats['overall_success_rate']:.2%}")
    print(f"Assessment: {results['assessment']}")
    print(f"Results saved to: {args.output}")

if __name__ == "__main__":
    main()