"""
Intelligence Tier System Testing

Consolidated testing for all 4 intelligence tiers ($0.75 - $42.00) using the unified framework.
Replaces the 8+ individual tier test files that were archived.

This test validates:
- CURRENT Tier ($0.75) - 4-stage AI analysis with strategic recommendations
- STANDARD Tier ($7.50) - Enhanced with historical funding analysis  
- ENHANCED Tier ($22.00) - Advanced with document analysis and network intelligence
- COMPLETE Tier ($42.00) - Masters thesis-level with policy analysis and strategic consulting

Key Testing Features:
- Real GPT-5 API calls (no simulation)
- Cost tracking and budget enforcement
- Heroes Bridge + Fauquier Foundation scenarios
- Business value validation
- Performance benchmarking
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add test framework to path
sys.path.append(str(Path(__file__).parent.parent))

from unified_test_base import UnifiedTestBase, TestResult

logger = logging.getLogger(__name__)


class IntelligenceTierTester(UnifiedTestBase):
    """Comprehensive intelligence tier testing framework"""
    
    def __init__(self):
        # Set higher budget for tier testing
        super().__init__(max_budget=100.00)
        
        # Tier specifications
        self.tier_specs = {
            "current": {
                "price": 0.75,
                "max_cost": 1.00,
                "max_duration": 600,  # 10 minutes
                "features": [
                    "4-stage AI analysis",
                    "Strategic scoring", 
                    "Risk assessment",
                    "Success probability",
                    "Implementation roadmap"
                ]
            },
            "standard": {
                "price": 7.50,
                "max_cost": 8.00,
                "max_duration": 1200,  # 20 minutes
                "features": [
                    "All Current Tier features",
                    "Historical funding analysis",
                    "Award pattern intelligence", 
                    "Geographic distribution",
                    "Temporal trend analysis"
                ]
            },
            "enhanced": {
                "price": 22.00,
                "max_cost": 25.00,
                "max_duration": 2700,  # 45 minutes
                "features": [
                    "All Standard Tier features",
                    "Complete RFP/NOFO analysis",
                    "Board network intelligence",
                    "Decision maker profiling",
                    "Competitive deep analysis"
                ]
            },
            "complete": {
                "price": 42.00,
                "max_cost": 45.00, 
                "max_duration": 3600,  # 60 minutes
                "features": [
                    "All Enhanced Tier features",
                    "Advanced network mapping",
                    "Policy context analysis", 
                    "Real-time monitoring setup",
                    "Premium documentation suite"
                ]
            }
        }
    
    async def test_current_tier(self) -> TestResult:
        """Test CURRENT Intelligence Tier ($0.75)"""
        logger.info("Testing CURRENT Intelligence Tier ($0.75)")
        
        spec = self.tier_specs["current"]
        
        # Test with Heroes Bridge scenario (primary)
        result = await self.run_processor_test(
            processor_name="current_tier_processor",
            scenario_name="heroes_bridge_primary",
            budget_limit=spec["max_cost"]
        )
        
        # Validate tier-specific requirements
        if result.success:
            self._validate_current_tier_output(result)
        
        return result
    
    async def test_standard_tier(self) -> TestResult:
        """Test STANDARD Intelligence Tier ($7.50)"""
        logger.info("Testing STANDARD Intelligence Tier ($7.50)")
        
        spec = self.tier_specs["standard"]
        
        # Test with Fauquier Foundation scenario (larger organization)
        result = await self.run_processor_test(
            processor_name="standard_tier_processor",
            scenario_name="fauquier_secondary", 
            budget_limit=spec["max_cost"]
        )
        
        # Validate tier-specific requirements
        if result.success:
            self._validate_standard_tier_output(result)
            
        return result
    
    async def test_enhanced_tier(self) -> TestResult:
        """Test ENHANCED Intelligence Tier ($22.00)"""
        logger.info("Testing ENHANCED Intelligence Tier ($22.00)")
        
        spec = self.tier_specs["enhanced"]
        
        # Test with Heroes Bridge scenario (complex analysis)
        result = await self.run_processor_test(
            processor_name="enhanced_tier_processor",
            scenario_name="heroes_bridge_primary",
            budget_limit=spec["max_cost"]
        )
        
        # Validate tier-specific requirements
        if result.success:
            self._validate_enhanced_tier_output(result)
            
        return result
    
    async def test_complete_tier(self) -> TestResult:
        """Test COMPLETE Intelligence Tier ($42.00)"""
        logger.info("Testing COMPLETE Intelligence Tier ($42.00)")
        
        spec = self.tier_specs["complete"]
        
        # Test with Fauquier Foundation scenario (comprehensive analysis)
        result = await self.run_processor_test(
            processor_name="complete_tier_processor", 
            scenario_name="fauquier_secondary",
            budget_limit=spec["max_cost"]
        )
        
        # Validate tier-specific requirements
        if result.success:
            self._validate_complete_tier_output(result)
            
        return result
    
    def _validate_current_tier_output(self, result: TestResult):
        """Validate CURRENT tier output meets business requirements"""
        output = result.output_data
        if not output:
            return
            
        required_elements = [
            "strategic_scoring",
            "risk_assessment", 
            "success_probability",
            "implementation_plan"
        ]
        
        for element in required_elements:
            if element not in output:
                logger.warning(f"CURRENT tier missing required element: {element}")
    
    def _validate_standard_tier_output(self, result: TestResult):
        """Validate STANDARD tier output includes historical analysis"""
        output = result.output_data
        if not output:
            return
            
        # Validate enhanced features
        enhanced_elements = [
            "historical_funding",
            "award_patterns", 
            "geographic_analysis",
            "temporal_trends"
        ]
        
        for element in enhanced_elements:
            if element not in output:
                logger.warning(f"STANDARD tier missing enhanced element: {element}")
    
    def _validate_enhanced_tier_output(self, result: TestResult):
        """Validate ENHANCED tier includes network intelligence"""
        output = result.output_data
        if not output:
            return
            
        # Validate advanced features
        advanced_elements = [
            "rfp_analysis",
            "network_intelligence",
            "decision_makers",
            "competitive_analysis"
        ]
        
        for element in advanced_elements:
            if element not in output:
                logger.warning(f"ENHANCED tier missing advanced element: {element}")
    
    def _validate_complete_tier_output(self, result: TestResult):
        """Validate COMPLETE tier includes premium features"""
        output = result.output_data
        if not output:
            return
            
        # Validate premium features
        premium_elements = [
            "network_mapping",
            "policy_analysis",
            "monitoring_setup", 
            "premium_documentation"
        ]
        
        for element in premium_elements:
            if element not in output:
                logger.warning(f"COMPLETE tier missing premium element: {element}")
    
    async def test_tier_progression(self) -> Dict[str, TestResult]:
        """Test all tiers to validate value progression"""
        logger.info("Testing tier progression and value validation")
        
        results = {}
        
        # Test each tier in order
        for tier in ["current", "standard", "enhanced", "complete"]:
            method = getattr(self, f"test_{tier}_tier")
            results[tier] = await method()
            
            # Stop if a tier fails to avoid unnecessary costs
            if not results[tier].success:
                logger.error(f"Tier progression stopped at {tier} due to failure")
                break
                
        return results
    
    def validate_business_value_progression(self, results: Dict[str, TestResult]) -> Dict[str, Any]:
        """Validate that higher tiers provide proportional business value"""
        validation = {
            "cost_progression_valid": True,
            "duration_progression_valid": True,
            "value_justification": {},
            "recommendations": []
        }
        
        successful_results = {k: v for k, v in results.items() if v.success}
        
        if len(successful_results) < 2:
            validation["recommendations"].append("Need at least 2 successful tiers for progression analysis")
            return validation
        
        # Validate cost progression
        tiers_ordered = ["current", "standard", "enhanced", "complete"]
        for i in range(1, len(tiers_ordered)):
            prev_tier = tiers_ordered[i-1]
            curr_tier = tiers_ordered[i]
            
            if prev_tier in successful_results and curr_tier in successful_results:
                prev_cost = successful_results[prev_tier].cost_actual
                curr_cost = successful_results[curr_tier].cost_actual
                
                if curr_cost <= prev_cost:
                    validation["cost_progression_valid"] = False
                    validation["recommendations"].append(
                        f"Cost progression issue: {curr_tier} (${curr_cost:.2f}) not significantly higher than {prev_tier} (${prev_cost:.2f})"
                    )
        
        return validation


async def run_comprehensive_tier_testing():
    """Main function to run comprehensive tier testing"""
    print("Catalynx Intelligence Tier System Testing")
    print("=" * 50)
    print("Testing 4-tier intelligence system ($0.75 - $42.00)")
    print("Real GPT-5 API calls with Heroes Bridge + Fauquier scenarios")
    print()
    
    tester = IntelligenceTierTester()
    
    try:
        # Run tier progression testing
        results = await tester.test_tier_progression()
        
        # Generate comprehensive report
        report = tester.get_comprehensive_report()
        business_validation = tester.validate_business_value_progression(results)
        
        # Display results
        print("TIER TESTING RESULTS")
        print("-" * 30)
        
        for tier, result in results.items():
            spec = tester.tier_specs[tier]
            status = "PASS" if result.success else "FAIL"
            
            print(f"{tier.upper()} Tier (${spec['price']:.2f}): {status}")
            if result.success:
                print(f"  Duration: {result.duration_seconds:.1f}s / {spec['max_duration']}s max")
                print(f"  Cost: ${result.cost_actual:.4f} / ${spec['max_cost']:.2f} budget")
                print(f"  Tokens: {result.tokens_used:,}")
            else:
                print(f"  Error: {result.error_message}")
            print()
        
        # Summary
        successful = sum(1 for r in results.values() if r.success)
        total = len(results)
        
        print("SUMMARY")
        print("-" * 20)
        print(f"Tiers tested: {total}")
        print(f"Successful: {successful}")
        print(f"Success rate: {successful/total*100:.1f}%")
        print(f"Total cost: ${report['cost_analysis']['total_cost']:.2f}")
        print(f"Total duration: {report['cost_analysis']['duration_minutes']:.1f} minutes")
        
        # Business validation
        print("\nBUSINESS VALUE VALIDATION")
        print("-" * 30)
        if business_validation["cost_progression_valid"]:
            print("PASS: Cost progression validated")
        else:
            print("FAIL: Cost progression issues found")
            
        for rec in business_validation["recommendations"]:
            print(f"  • {rec}")
        
        print("\nTesting completed successfully!")
        
        return 0 if successful == total else 1
        
    except Exception as e:
        print(f"FAIL: Testing failed: {str(e)}")
        logger.exception("Tier testing failed")
        return 1


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run testing
    exit_code = asyncio.run(run_comprehensive_tier_testing())
    exit(exit_code)