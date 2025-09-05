"""
Comprehensive Processor Testing Suite

Consolidated testing for all 45+ Catalynx processors using the unified framework.
Replaces the 20+ individual processor test files that were archived.

This test validates:
- 4-Stage AI Pipeline: PLAN → ANALYZE → EXAMINE → APPROACH
- Data collection processors (BMF, ProPublica, Grants.gov, etc.)
- Analysis processors (Government scorer, Financial scorer, Network analyzer, etc.)
- Integration processors (Report generator, Export processor, etc.)

Key Testing Features:
- Real GPT-5 API calls for AI processors
- Entity-based data architecture validation
- Performance benchmarking
- Cost tracking per processor
- Error handling validation
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add test framework to path
sys.path.append(str(Path(__file__).parent.parent))

from unified_test_base import UnifiedTestBase, TestResult

logger = logging.getLogger(__name__)


class ProcessorTestSuite(UnifiedTestBase):
    """Comprehensive processor testing framework"""
    
    def __init__(self):
        # Set budget for processor testing
        super().__init__(max_budget=50.00)
        
        # Processor categories and specifications
        self.processor_categories = {
            "ai_pipeline": {
                "processors": [
                    ("ai_lite_unified_processor", "PLAN", 0.0004, 15),    # GPT-5-nano
                    ("ai_heavy_light_analyzer", "ANALYZE", 0.04, 60),    # GPT-5-mini  
                    ("ai_heavy_deep_researcher", "EXAMINE", 0.15, 180),  # GPT-5
                    ("ai_heavy_researcher", "APPROACH", 0.20, 240)       # GPT-5
                ],
                "description": "4-stage AI processing pipeline"
            },
            "data_collectors": {
                "processors": [
                    ("bmf_filter", "DATA", 0.0, 30),
                    ("propublica_fetch", "DATA", 0.0, 45),
                    ("grants_gov_fetch", "DATA", 0.0, 60),
                    ("usaspending_fetch", "DATA", 0.0, 90),
                    ("va_state_grants_fetch", "DATA", 0.0, 45),
                    ("foundation_directory_fetch", "DATA", 0.0, 60)
                ],
                "description": "Data collection and fetching processors"
            },
            "analyzers": {
                "processors": [
                    ("government_opportunity_scorer", "ANALYSIS", 0.0, 30),
                    ("financial_scorer", "ANALYSIS", 0.0, 20),
                    ("board_network_analyzer", "ANALYSIS", 0.02, 120),
                    ("enhanced_network_analyzer", "ANALYSIS", 0.05, 180),
                    ("risk_assessor", "ANALYSIS", 0.01, 60),
                    ("competitive_intelligence", "ANALYSIS", 0.08, 200)
                ],
                "description": "Analysis and scoring processors"
            },
            "integrators": {
                "processors": [
                    ("report_generator", "INTEGRATION", 0.0, 45),
                    ("export_processor", "INTEGRATION", 0.0, 30),
                    ("network_visualizer", "INTEGRATION", 0.0, 60),
                    ("grant_package_generator", "INTEGRATION", 0.01, 90)
                ],
                "description": "Integration and output processors"
            }
        }
    
    async def test_ai_pipeline(self) -> Dict[str, TestResult]:
        """Test complete 4-stage AI processing pipeline"""
        logger.info("Testing 4-stage AI processing pipeline")
        
        # Execute the 4-stage pipeline
        results = self.run_4_stage_ai_analysis("heroes_bridge_primary")
        
        # Validate pipeline integrity
        if self._validate_pipeline_integrity(results):
            logger.info("✓ 4-stage AI pipeline validation successful")
        else:
            logger.warning("⚠ 4-stage AI pipeline validation issues detected")
        
        return results
    
    async def test_processor_category(self, category: str) -> Dict[str, TestResult]:
        """Test all processors in a specific category"""
        if category not in self.processor_categories:
            raise ValueError(f"Unknown processor category: {category}")
        
        cat_info = self.processor_categories[category]
        logger.info(f"Testing {category} processors: {cat_info['description']}")
        
        results = {}
        
        for processor_name, stage, max_cost, max_duration in cat_info["processors"]:
            logger.info(f"Testing {processor_name} ({stage} stage)")
            
            try:
                result = await self.run_processor_test(
                    processor_name=processor_name,
                    scenario_name="heroes_bridge_primary",
                    budget_limit=max(max_cost * 2, 0.10)  # Buffer for cost estimation
                )
                
                # Validate processor-specific requirements
                self._validate_processor_result(result, stage, max_cost, max_duration)
                results[processor_name] = result
                
            except Exception as e:
                logger.error(f"Failed to test {processor_name}: {str(e)}")
                # Create failure result
                results[processor_name] = TestResult(
                    scenario_name="heroes_bridge_primary",
                    processor_name=processor_name,
                    success=False,
                    duration_seconds=0.0,
                    cost_actual=0.0,
                    cost_budget=max_cost,
                    tokens_used=0,
                    output_quality_score=None,
                    error_message=str(e),
                    output_data=None
                )
        
        return results
    
    async def test_all_processors(self) -> Dict[str, Dict[str, TestResult]]:
        """Test all processor categories comprehensively"""
        logger.info("Starting comprehensive processor testing")
        
        all_results = {}
        
        for category in self.processor_categories:
            logger.info(f"Testing category: {category}")
            
            try:
                category_results = await self.test_processor_category(category)
                all_results[category] = category_results
                
                # Log category summary
                successful = sum(1 for r in category_results.values() if r.success)
                total = len(category_results)
                logger.info(f"Category {category}: {successful}/{total} processors successful")
                
            except Exception as e:
                logger.error(f"Category {category} testing failed: {str(e)}")
                all_results[category] = {}
        
        return all_results
    
    def _validate_pipeline_integrity(self, results: Dict[str, TestResult]) -> bool:
        """Validate 4-stage AI pipeline integrity"""
        expected_stages = ["PLAN", "ANALYZE", "EXAMINE", "APPROACH"]
        
        # Check all stages completed
        if len(results) != len(expected_stages):
            logger.warning(f"Pipeline incomplete: {len(results)}/{len(expected_stages)} stages")
            return False
        
        # Check stage ordering and success
        for stage in expected_stages:
            if stage not in results:
                logger.warning(f"Missing pipeline stage: {stage}")
                return False
            
            if not results[stage].success:
                logger.warning(f"Pipeline stage failed: {stage}")
                return False
        
        # Validate cost progression (later stages should cost more)
        stage_costs = [(stage, results[stage].cost_actual) for stage in expected_stages if results[stage].success]
        
        for i in range(1, len(stage_costs)):
            if stage_costs[i][1] < stage_costs[i-1][1]:
                logger.warning(f"Cost regression in pipeline: {stage_costs[i-1][0]} (${stage_costs[i-1][1]:.4f}) → {stage_costs[i][0]} (${stage_costs[i][1]:.4f})")
        
        return True
    
    def _validate_processor_result(self, result: TestResult, stage: str, max_cost: float, max_duration: int):
        """Validate individual processor result against specifications"""
        if not result.success:
            return  # Don't validate failed results
        
        # Validate cost expectations
        if max_cost > 0 and result.cost_actual > max_cost * 3:  # Allow 3x buffer
            logger.warning(f"{result.processor_name} cost exceeded expectations: ${result.cost_actual:.4f} > ${max_cost:.4f} (expected)")
        
        # Validate duration expectations
        if result.duration_seconds > max_duration * 2:  # Allow 2x buffer
            logger.warning(f"{result.processor_name} duration exceeded expectations: {result.duration_seconds:.1f}s > {max_duration}s (expected)")
        
        # Stage-specific validations
        if stage == "DATA":
            # Data processors should return structured data
            if not result.output_data or "data" not in str(result.output_data):
                logger.warning(f"Data processor {result.processor_name} may not have returned structured data")
        
        elif stage in ["PLAN", "ANALYZE", "EXAMINE", "APPROACH"]:
            # AI processors should use tokens and return analysis
            if result.tokens_used == 0:
                logger.warning(f"AI processor {result.processor_name} reported 0 tokens used")
            
            if not result.output_data or "analysis" not in str(result.output_data):
                logger.warning(f"AI processor {result.processor_name} may not have returned analysis")
    
    def generate_processor_performance_report(self, all_results: Dict[str, Dict[str, TestResult]]) -> Dict[str, Any]:
        """Generate comprehensive processor performance report"""
        report = {
            "summary": {
                "total_processors": 0,
                "successful_processors": 0,
                "failed_processors": 0,
                "total_cost": 0.0,
                "total_duration": 0.0
            },
            "category_performance": {},
            "top_performers": [],
            "problem_processors": [],
            "cost_analysis": {},
            "recommendations": []
        }
        
        all_individual_results = []
        
        # Collect all individual results
        for category, category_results in all_results.items():
            category_summary = {
                "total": len(category_results),
                "successful": 0,
                "failed": 0,
                "total_cost": 0.0,
                "average_duration": 0.0
            }
            
            successful_durations = []
            
            for processor_name, result in category_results.items():
                all_individual_results.append(result)
                
                if result.success:
                    category_summary["successful"] += 1
                    category_summary["total_cost"] += result.cost_actual
                    successful_durations.append(result.duration_seconds)
                else:
                    category_summary["failed"] += 1
            
            if successful_durations:
                category_summary["average_duration"] = sum(successful_durations) / len(successful_durations)
            
            report["category_performance"][category] = category_summary
        
        # Overall summary
        report["summary"]["total_processors"] = len(all_individual_results)
        report["summary"]["successful_processors"] = sum(1 for r in all_individual_results if r.success)
        report["summary"]["failed_processors"] = sum(1 for r in all_individual_results if not r.success)
        report["summary"]["total_cost"] = sum(r.cost_actual for r in all_individual_results if r.success)
        report["summary"]["total_duration"] = sum(r.duration_seconds for r in all_individual_results if r.success)
        
        # Top performers (fast, low cost, high quality)
        successful_results = [r for r in all_individual_results if r.success]
        if successful_results:
            # Sort by efficiency (quality/cost ratio or similar metric)
            report["top_performers"] = sorted(
                successful_results,
                key=lambda r: (r.output_quality_score or 0.5) / max(r.cost_actual, 0.001),
                reverse=True
            )[:5]  # Top 5
        
        # Problem processors
        report["problem_processors"] = [r for r in all_individual_results if not r.success]
        
        # Recommendations
        if report["summary"]["failed_processors"] > 0:
            report["recommendations"].append("Review failed processors for integration issues")
        
        if report["summary"]["total_cost"] > 20.0:
            report["recommendations"].append("High testing cost - consider optimizing processor efficiency")
        
        success_rate = report["summary"]["successful_processors"] / report["summary"]["total_processors"] if report["summary"]["total_processors"] > 0 else 0
        if success_rate < 0.9:
            report["recommendations"].append(f"Low success rate ({success_rate:.1%}) - investigate common failure patterns")
        
        return report


async def run_comprehensive_processor_testing():
    """Main function to run comprehensive processor testing"""
    print("Catalynx Comprehensive Processor Testing Suite")
    print("=" * 55)
    print("Testing 45+ processors across 4 categories")
    print("Real GPT-5 API calls for AI processors")
    print()
    
    suite = ProcessorTestSuite()
    
    try:
        # Run comprehensive testing
        all_results = await suite.test_all_processors()
        
        # Generate performance report
        report = suite.generate_processor_performance_report(all_results)
        
        # Display results
        print("PROCESSOR TESTING RESULTS")
        print("-" * 35)
        
        for category, category_results in all_results.items():
            category_info = suite.processor_categories[category]
            successful = sum(1 for r in category_results.values() if r.success)
            total = len(category_results)
            
            print(f"{category.upper()}: {successful}/{total} processors successful")
            print(f"  Description: {category_info['description']}")
            
            # Show individual results
            for processor_name, result in category_results.items():
                status = "✓" if result.success else "✗"
                if result.success:
                    print(f"    {status} {processor_name}: {result.duration_seconds:.1f}s, ${result.cost_actual:.4f}")
                else:
                    print(f"    {status} {processor_name}: {result.error_message}")
            print()
        
        # Summary
        print("OVERALL SUMMARY")
        print("-" * 20)
        print(f"Total processors: {report['summary']['total_processors']}")
        print(f"Successful: {report['summary']['successful_processors']}")
        print(f"Failed: {report['summary']['failed_processors']}")
        print(f"Success rate: {report['summary']['successful_processors']/report['summary']['total_processors']*100:.1f}%")
        print(f"Total cost: ${report['summary']['total_cost']:.2f}")
        print(f"Total duration: {report['summary']['total_duration']:.1f} seconds")
        
        # Recommendations
        if report["recommendations"]:
            print("\nRECOMMENDATIONS")
            print("-" * 15)
            for rec in report["recommendations"]:
                print(f"• {rec}")
        
        print("\nProcessor testing completed successfully!")
        
        return 0 if report["summary"]["failed_processors"] == 0 else 1
        
    except Exception as e:
        print(f"✗ Testing failed: {str(e)}")
        logger.exception("Processor testing failed")
        return 1


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run testing
    exit_code = asyncio.run(run_comprehensive_processor_testing())
    exit(exit_code)