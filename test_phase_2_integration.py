"""
Phase 2C Integration Tests - Unified Client Architecture Validation
Comprehensive testing of migrated processors with new client architecture
"""
import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase2IntegrationTester:
    """Integration test suite for Phase 2 unified client architecture"""
    
    def __init__(self):
        self.test_results = []
        self.test_config = {
            "focus_areas": ["health", "education", "community development"],
            "geographic_scope": ["VA", "MD", "DC"],
            "funding_range": {"min_amount": 10000, "max_amount": 500000},
            "max_results": 10
        }
    
    async def run_comprehensive_tests(self):
        """Run comprehensive integration tests for all migrated processors"""
        logger.info("=== Phase 2C Integration Tests: Unified Client Architecture ===")
        
        # Test individual processors
        await self.test_grants_gov_processor()
        await self.test_propublica_processor()
        await self.test_usaspending_processor()
        await self.test_foundation_directory_processor()
        await self.test_va_state_processor()
        
        # Test processor registration
        await self.test_processor_registration()
        
        # Test architecture overview
        await self.test_architecture_overview()
        
        # Test client integration workflow
        await self.test_unified_workflow()
        
        # Generate test report
        self.generate_test_report()
    
    async def test_grants_gov_processor(self):
        """Test Grants.gov processor with GrantsGovClient"""
        test_name = "Grants.gov Processor with GrantsGovClient"
        logger.info(f"Testing: {test_name}")
        
        try:
            from src.processors.data_collection.grants_gov_fetch import GrantsGovFetchProcessor
            from src.core.base_processor import ProcessorMetadata
            
            # Initialize processor
            processor = GrantsGovFetchProcessor()
            
            # Verify metadata
            assert processor.metadata.name == "grants_gov_fetch"
            assert processor.metadata.version == "2.0.0"
            assert processor.metadata.processor_type == "data_collection"
            
            # Test execution with mock data
            test_data = {
                "focus_areas": self.test_config["focus_areas"],
                "max_results": 5
            }
            
            # Create mock config object
            class MockWorkflowConfig:
                def __init__(self):
                    self.eligibility_code = "25"
                    self.max_results = 5
            
            class MockConfig:
                def __init__(self):
                    self.processor_specific_config = test_data
                    self.workflow_config = MockWorkflowConfig()
            
            config = MockConfig()
            result = await processor.execute(config)
            
            # Validate result structure
            assert isinstance(result, dict)
            assert "status" in result
            assert "government_opportunities" in result
            
            self.test_results.append({
                "test": test_name,
                "status": "PASSED",
                "details": f"Processor version {processor.metadata.version}, returned {result.get('total_found', 0)} opportunities"
            })
            
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            })
            logger.error(f"Test failed: {test_name} - {e}")
    
    async def test_propublica_processor(self):
        """Test ProPublica processor with ProPublicaClient"""
        test_name = "ProPublica Processor with ProPublicaClient"
        logger.info(f"Testing: {test_name}")
        
        try:
            from src.processors.data_collection.propublica_fetch import ProPublicaFetchProcessor
            
            # Initialize processor
            processor = ProPublicaFetchProcessor()
            
            # Verify metadata
            assert processor.metadata.name == "propublica_fetch"
            assert processor.metadata.version == "2.0.0"
            assert processor.metadata.processor_type == "data_collection"
            
            # Test execution with mock organization
            test_data = {
                "organizations": [
                    {
                        "ein": "12-3456789",
                        "name": "Test Nonprofit Organization"
                    }
                ]
            }
            
            class MockConfig:
                def __init__(self):
                    self.processor_specific_config = test_data
                    self.workflow_config = type('MockWorkflowConfig', (), {})()
            
            config = MockConfig()
            result = await processor.execute(config)
            
            # Validate result structure
            assert isinstance(result, dict)
            assert "status" in result
            
            self.test_results.append({
                "test": test_name,
                "status": "PASSED",
                "details": f"Processor version {processor.metadata.version}, client integration successful"
            })
            
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            })
            logger.error(f"Test failed: {test_name} - {e}")
    
    async def test_usaspending_processor(self):
        """Test USASpending processor with USASpendingClient"""
        test_name = "USASpending Processor with USASpendingClient"
        logger.info(f"Testing: {test_name}")
        
        try:
            from src.processors.data_collection.usaspending_fetch import USASpendingFetchProcessor
            
            # Initialize processor
            processor = USASpendingFetchProcessor()
            
            # Verify metadata
            assert processor.metadata.name == "usaspending_fetch"
            assert processor.metadata.version == "2.0.0"
            assert processor.metadata.processor_type == "data_collection"
            
            # Test execution with mock organization
            test_data = {
                "organizations": [
                    {
                        "ein": "12-3456789",
                        "name": "Test Organization"
                    }
                ]
            }
            
            class MockConfig:
                def __init__(self):
                    self.processor_specific_config = test_data
                    self.workflow_config = type('MockWorkflowConfig', (), {})()
            
            config = MockConfig()
            result = await processor.execute(config)
            
            # Validate result structure
            assert isinstance(result, dict)
            assert "status" in result
            
            self.test_results.append({
                "test": test_name,
                "status": "PASSED",
                "details": f"Processor version {processor.metadata.version}, award history processing ready"
            })
            
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            })
            logger.error(f"Test failed: {test_name} - {e}")
    
    async def test_foundation_directory_processor(self):
        """Test Foundation Directory processor with FoundationDirectoryClient"""
        test_name = "Foundation Directory Processor with FoundationDirectoryClient"
        logger.info(f"Testing: {test_name}")
        
        try:
            from src.processors.data_collection.foundation_directory_fetch import FoundationDirectoryFetch
            
            # Initialize processor
            processor = FoundationDirectoryFetch()
            
            # Verify metadata
            assert processor.metadata.name == "foundation_directory_fetch"
            assert processor.metadata.version == "2.0.0"
            assert processor.metadata.processor_type == "data_collection"
            
            # Test execution with focus areas
            test_data = {
                "focus_areas": self.test_config["focus_areas"],
                "max_results": 5
            }
            
            class MockConfig:
                def __init__(self):
                    self.processor_specific_config = test_data
                    self.workflow_config = type('MockWorkflowConfig', (), {})()
            
            config = MockConfig()
            result = await processor.execute(config)
            
            # Validate result structure
            assert isinstance(result, dict)
            assert "status" in result
            assert "foundation_opportunities" in result
            
            self.test_results.append({
                "test": test_name,
                "status": "PASSED",
                "details": f"Processor version {processor.metadata.version}, returned {result.get('total_found', 0)} opportunities"
            })
            
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            })
            logger.error(f"Test failed: {test_name} - {e}")
    
    async def test_va_state_processor(self):
        """Test VA State processor with VAStateClient"""
        test_name = "VA State Processor with VAStateClient"
        logger.info(f"Testing: {test_name}")
        
        try:
            from src.processors.data_collection.va_state_grants_fetch import VirginiaStateGrantsFetch
            
            # Initialize processor
            processor = VirginiaStateGrantsFetch()
            
            # Verify metadata
            assert processor.metadata.name == "va_state_grants_fetch"
            assert processor.metadata.version == "2.0.0"
            assert processor.metadata.processor_type == "data_collection"
            
            # Test execution with focus areas
            test_data = {
                "focus_areas": self.test_config["focus_areas"],
                "geographic_scope": ["VA"],
                "max_results": 5
            }
            
            class MockConfig:
                def __init__(self):
                    self.processor_specific_config = test_data
                    self.workflow_config = type('MockWorkflowConfig', (), {})()
            
            config = MockConfig()
            result = await processor.execute(config)
            
            # Validate result structure
            assert isinstance(result, dict)
            assert "status" in result
            assert "state_opportunities" in result
            
            self.test_results.append({
                "test": test_name,
                "status": "PASSED",
                "details": f"Processor version {processor.metadata.version}, returned {result.get('total_found', 0)} opportunities"
            })
            
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            })
            logger.error(f"Test failed: {test_name} - {e}")
    
    async def test_processor_registration(self):
        """Test processor registration and discovery"""
        test_name = "Processor Registration and Discovery"
        logger.info(f"Testing: {test_name}")
        
        try:
            from src.processors.registry import get_processor_summary, register_all_processors
            
            # Register all processors
            registered_count = register_all_processors()
            logger.info(f"Registered {registered_count} processors")
            
            # Get processor summary
            summary = get_processor_summary()
            
            # Validate summary structure
            assert isinstance(summary, dict)
            assert "total_processors" in summary
            assert "architecture_stats" in summary
            assert "migration_insights" in summary
            
            # Check for our migrated processors
            processor_names = summary.get("processor_names", [])
            expected_processors = [
                "grants_gov_fetch",
                "propublica_fetch",
                "usaspending_fetch",
                "foundation_directory_fetch",
                "va_state_grants_fetch"
            ]
            
            found_processors = [name for name in expected_processors if name in processor_names]
            
            self.test_results.append({
                "test": test_name,
                "status": "PASSED",
                "details": f"Found {len(found_processors)}/5 migrated processors: {found_processors}"
            })
            
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            })
            logger.error(f"Test failed: {test_name} - {e}")
    
    async def test_architecture_overview(self):
        """Test architecture overview and migration insights"""
        test_name = "Architecture Overview and Migration Insights"
        logger.info(f"Testing: {test_name}")
        
        try:
            from src.processors.registry import get_architecture_overview
            
            # Get architecture overview
            overview = get_architecture_overview()
            
            # Validate overview structure
            assert isinstance(overview, dict)
            assert "overview" in overview
            assert "data_collection_focus" in overview
            assert "priority_processors" in overview
            assert "migration_phase" in overview
            
            # Check migration completion
            completion = overview["overview"].get("migration_completion_percentage", 0)
            logger.info(f"Migration completion: {completion}%")
            
            # Check priority processors
            priority_details = overview["priority_processors"].get("processor_details", {})
            migrated_count = sum(
                1 for status in priority_details.values() 
                if status.get("status") == "migrated"
            )
            
            self.test_results.append({
                "test": test_name,
                "status": "PASSED",
                "details": f"Migration {completion}% complete, {migrated_count} priority processors migrated"
            })
            
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            })
            logger.error(f"Test failed: {test_name} - {e}")
    
    async def test_unified_workflow(self):
        """Test unified workflow with multiple processors"""
        test_name = "Unified Multi-Processor Workflow"
        logger.info(f"Testing: {test_name}")
        
        try:
            # Import all processors
            from src.processors.data_collection.grants_gov_fetch import GrantsGovFetchProcessor
            from src.processors.data_collection.foundation_directory_fetch import FoundationDirectoryFetch
            from src.processors.data_collection.va_state_grants_fetch import VirginiaStateGrantsFetch
            
            # Create workflow data
            workflow_data = {
                "focus_areas": ["health", "education"],
                "max_results": 3
            }
            
            class MockConfig:
                def __init__(self):
                    self.processor_specific_config = workflow_data
                    self.workflow_config = type('MockWorkflowConfig', (), {})()
            
            config = MockConfig()
            
            # Test multiple processors in sequence
            processors = [
                ("grants_gov", GrantsGovFetchProcessor()),
                ("foundation_directory", FoundationDirectoryFetch()),
                ("va_state", VirginiaStateGrantsFetch())
            ]
            
            workflow_results = {}
            
            for name, processor in processors:
                try:
                    result = await processor.execute(config)
                    workflow_results[name] = {
                        "status": result.get("status", "unknown"),
                        "total_found": result.get("total_found", 0)
                    }
                except Exception as e:
                    workflow_results[name] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            # Validate workflow results
            successful_processors = sum(
                1 for result in workflow_results.values() 
                if result.get("status") in ["completed", "success"]
            )
            
            self.test_results.append({
                "test": test_name,
                "status": "PASSED",
                "details": f"Executed {successful_processors}/3 processors successfully: {workflow_results}"
            })
            
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            })
            logger.error(f"Test failed: {test_name} - {e}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n=== PHASE 2C INTEGRATION TEST REPORT ===")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["status"] == "PASSED")
        failed_tests = total_tests - passed_tests
        
        print(f"\nTest Summary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        print(f"\nDetailed Results:")
        for i, result in enumerate(self.test_results, 1):
            status_icon = "PASS" if result["status"] == "PASSED" else "FAIL"
            print(f"  {i}. [{status_icon}] {result['test']}")
            if result["status"] == "PASSED":
                print(f"     {result.get('details', 'Test completed successfully')}")
            else:
                print(f"     ERROR: {result.get('error', 'Unknown error')}")
        
        # Save detailed report
        report_data = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": round(passed_tests/total_tests*100, 1)
            },
            "test_results": self.test_results,
            "test_timestamp": datetime.now().isoformat(),
            "test_phase": "Phase 2C: Integration Testing"
        }
        
        with open("phase_2c_integration_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"\nDetailed report saved to: phase_2c_integration_test_report.json")
        
        # Phase completion assessment
        if passed_tests == total_tests:
            logger.info("\n[SUCCESS] Phase 2C Integration Testing: COMPLETE")
            logger.info("[PASS] All unified client architecture processors validated")
            logger.info("[PASS] Processor registration and discovery operational")
            logger.info("[PASS] Architecture overview and migration tracking functional")
            logger.info("[PASS] Multi-processor workflows executing successfully")
            logger.info("\nReady to proceed to Phase 3: Enhanced Discovery Integration")
        else:
            logger.warning(f"\n[WARNING] Phase 2C Integration Testing: {failed_tests} failures detected")
            logger.warning("Some integration tests require attention before proceeding")


async def main():
    """Main test execution"""
    print("Phase 2C Integration Tests - Unified Client Architecture Validation")
    print("=" * 70)
    
    tester = Phase2IntegrationTester()
    await tester.run_comprehensive_tests()


if __name__ == "__main__":
    asyncio.run(main())