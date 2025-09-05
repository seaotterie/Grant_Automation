#!/usr/bin/env python3
"""
Tier Comparison Testing Framework - Side-by-Side Analysis
Comprehensive comparison testing between tab processors and tier services to validate
the dual architecture approach and demonstrate value proposition of each tier.

This framework provides:
1. Direct comparison between tab processors vs tier services
2. Cost-benefit analysis across all 4 tiers 
3. ROI validation for tier selection decisions
4. Quality assessment and business value analysis
5. Use case scenario validation
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import matplotlib.pyplot as plt
import pandas as pd

# Import from integrated tier test framework
from integrated_tier_test import (
    TierLevel, TestConfiguration, TestDataSet, TabProcessorResult, TierServiceResult,
    IntegratedTierTester, TestDataManager, CostTracker
)

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ComparisonMetrics:
    """Metrics for comparing different approaches"""
    approach_name: str
    total_cost: float
    processing_time_seconds: float
    quality_score: float
    professional_deliverables: int
    business_readiness_score: float
    technical_depth_score: float
    roi_score: float
    user_experience_score: float
    
@dataclass
class ScenarioComparison:
    """Comparison results for a specific scenario"""
    scenario_name: str
    dataset_id: str
    opportunity_value: float
    organization_size: str
    tab_processor_metrics: ComparisonMetrics
    tier_service_metrics: Dict[TierLevel, ComparisonMetrics]
    optimal_approach: str
    cost_efficiency_analysis: Dict[str, Any]
    value_proposition_analysis: Dict[str, Any]
    recommendation: str
    
class ComparisonAnalyzer:
    """Analyzes and compares different testing approaches"""
    
    def __init__(self):
        self.results_dir = Path("comparison_results")
        self.results_dir.mkdir(exist_ok=True)
        
    def analyze_cost_efficiency(self, tab_metrics: ComparisonMetrics, 
                               tier_metrics: Dict[TierLevel, ComparisonMetrics],
                               opportunity_value: float) -> Dict[str, Any]:
        """Analyze cost efficiency across approaches"""
        
        analysis = {
            "opportunity_value": opportunity_value,
            "approaches": {}
        }
        
        # Tab processor analysis
        tab_roi = (opportunity_value * tab_metrics.quality_score - tab_metrics.total_cost) / tab_metrics.total_cost if tab_metrics.total_cost > 0 else 0
        analysis["approaches"]["tab_processors"] = {
            "cost": tab_metrics.total_cost,
            "roi": tab_roi,
            "cost_per_quality_point": tab_metrics.total_cost / tab_metrics.quality_score if tab_metrics.quality_score > 0 else 0,
            "efficiency_rating": "high" if tab_roi > 1000 else "medium" if tab_roi > 100 else "low"
        }
        
        # Tier service analysis
        for tier_level, tier_metric in tier_metrics.items():
            tier_roi = (opportunity_value * tier_metric.quality_score - tier_metric.total_cost) / tier_metric.total_cost if tier_metric.total_cost > 0 else 0
            analysis["approaches"][tier_level.value] = {
                "cost": tier_metric.total_cost,
                "roi": tier_roi,
                "cost_per_quality_point": tier_metric.total_cost / tier_metric.quality_score if tier_metric.quality_score > 0 else 0,
                "efficiency_rating": "high" if tier_roi > 100 else "medium" if tier_roi > 50 else "low"
            }
            
        # Determine most cost-effective approach
        best_roi = max([analysis["approaches"][approach]["roi"] for approach in analysis["approaches"]])
        best_approach = [approach for approach, data in analysis["approaches"].items() if data["roi"] == best_roi][0]
        
        analysis["cost_efficiency_winner"] = best_approach
        analysis["cost_efficiency_summary"] = f"{best_approach} provides best ROI at {best_roi:.1f}:1"
        
        return analysis
        
    def analyze_value_proposition(self, tab_metrics: ComparisonMetrics,
                                tier_metrics: Dict[TierLevel, ComparisonMetrics]) -> Dict[str, Any]:
        """Analyze value proposition across approaches"""
        
        analysis = {
            "quality_comparison": {},
            "deliverable_comparison": {},
            "business_readiness_comparison": {},
            "value_progression": {}
        }
        
        # Quality comparison
        analysis["quality_comparison"]["tab_processors"] = tab_metrics.quality_score
        for tier_level, tier_metric in tier_metrics.items():
            analysis["quality_comparison"][tier_level.value] = tier_metric.quality_score
            
        # Deliverable comparison
        analysis["deliverable_comparison"]["tab_processors"] = {
            "professional_deliverables": tab_metrics.professional_deliverables,
            "business_readiness": tab_metrics.business_readiness_score,
            "technical_depth": tab_metrics.technical_depth_score
        }
        
        for tier_level, tier_metric in tier_metrics.items():
            analysis["deliverable_comparison"][tier_level.value] = {
                "professional_deliverables": tier_metric.professional_deliverables,
                "business_readiness": tier_metric.business_readiness_score,
                "technical_depth": tier_metric.technical_depth_score
            }
            
        # Value progression analysis
        quality_progression = []
        cost_progression = []
        
        quality_progression.append(("tab_processors", tab_metrics.quality_score))
        cost_progression.append(("tab_processors", tab_metrics.total_cost))
        
        for tier_level in [TierLevel.CURRENT, TierLevel.STANDARD, TierLevel.ENHANCED, TierLevel.COMPLETE]:
            if tier_level in tier_metrics:
                quality_progression.append((tier_level.value, tier_metrics[tier_level].quality_score))
                cost_progression.append((tier_level.value, tier_metrics[tier_level].total_cost))
                
        analysis["value_progression"] = {
            "quality_progression": quality_progression,
            "cost_progression": cost_progression,
            "value_efficiency": [(name, quality/cost if cost > 0 else 0) for (name, quality), (_, cost) in zip(quality_progression, cost_progression)]
        }
        
        return analysis
        
    def generate_recommendations(self, scenario_comparison: ScenarioComparison) -> List[str]:
        """Generate recommendations based on scenario analysis"""
        
        recommendations = []
        
        opportunity_value = scenario_comparison.opportunity_value
        org_size = scenario_comparison.organization_size
        
        # Size-based recommendations
        if org_size == "small":
            if opportunity_value < 50000:
                recommendations.append("Small organizations with small opportunities: Use tab processors for cost control")
                recommendations.append("Consider Current tier only if professional deliverables required for board presentation")
            else:
                recommendations.append("Small organizations with larger opportunities: Standard tier provides optimal ROI")
                
        elif org_size == "medium":
            if opportunity_value < 100000:
                recommendations.append("Medium organizations: Standard tier balances cost and intelligence value")
            else:
                recommendations.append("Medium organizations with significant opportunities: Enhanced tier for relationship leverage")
                
        elif org_size == "large":
            recommendations.append("Large organizations: Enhanced or Complete tier justified by organizational capacity")
            recommendations.append("Use Complete tier for transformational opportunities (>$1M)")
            
        # Cost efficiency recommendations
        cost_analysis = scenario_comparison.cost_efficiency_analysis
        winner = cost_analysis.get("cost_efficiency_winner", "")
        
        if winner == "tab_processors":
            recommendations.append("Tab processors provide best ROI - recommended for technical users with cost constraints")
        elif winner in ["current", "standard"]:
            recommendations.append(f"{winner.title()} tier provides optimal cost-benefit balance for this scenario")
        else:
            recommendations.append(f"{winner.title()} tier justified by high-value opportunity and comprehensive intelligence needs")
            
        # Business readiness recommendations
        value_analysis = scenario_comparison.value_proposition_analysis
        business_readiness_scores = value_analysis.get("deliverable_comparison", {})
        
        max_business_score = 0
        best_business_approach = ""
        for approach, metrics in business_readiness_scores.items():
            if metrics.get("business_readiness", 0) > max_business_score:
                max_business_score = metrics["business_readiness"]
                best_business_approach = approach
                
        if best_business_approach != "tab_processors":
            recommendations.append(f"For executive presentations: {best_business_approach} tier provides superior business deliverables")
        else:
            recommendations.append("Tab processors sufficient for technical analysis - supplement with custom presentation materials")
            
        return recommendations

class TierComparisonTester:
    """Main tier comparison testing framework"""
    
    def __init__(self, config: TestConfiguration = None):
        self.config = config or TestConfiguration()
        self.integrated_tester = IntegratedTierTester(self.config)
        self.analyzer = ComparisonAnalyzer()
        self.test_data_manager = TestDataManager()
        
        # Results storage
        self.comparison_results = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = Path(f"comparison_results/tier_comparison_{self.session_id}")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Tier Comparison Testing Framework initialized - Session: {self.session_id}")
        
    async def run_comprehensive_comparison(self) -> Dict[str, Any]:
        """Run comprehensive comparison testing across all scenarios"""
        
        logger.info("Starting comprehensive tier comparison testing")
        
        comparison_suite = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "scenario_comparisons": [],
            "summary_analysis": {},
            "tier_recommendations": {},
            "cost_efficiency_matrix": {},
            "roi_analysis": {}
        }
        
        # Test each dataset with comprehensive comparison
        datasets = self.test_data_manager.test_datasets
        
        for dataset in datasets:
            logger.info(f"\n{'='*80}")
            logger.info(f"Comparison Testing: {dataset.dataset_id}")
            logger.info(f"Organization: {dataset.nonprofit_profile['name']} ({dataset.organization_size})")
            logger.info(f"Opportunity: ${dataset.opportunity_data.get('award_ceiling', 0):,}")
            logger.info(f"{'='*80}")
            
            scenario_comparison = await self.test_scenario_comparison(dataset)
            comparison_suite["scenario_comparisons"].append(scenario_comparison)
            
        # Generate comprehensive analysis
        comparison_suite["summary_analysis"] = self._analyze_comparison_suite(comparison_suite["scenario_comparisons"])
        comparison_suite["tier_recommendations"] = self._generate_tier_recommendations(comparison_suite["scenario_comparisons"])
        comparison_suite["cost_efficiency_matrix"] = self._create_cost_efficiency_matrix(comparison_suite["scenario_comparisons"])
        comparison_suite["roi_analysis"] = self._analyze_roi_across_scenarios(comparison_suite["scenario_comparisons"])
        
        comparison_suite["end_time"] = datetime.now().isoformat()
        
        # Save results and generate reports
        await self._save_comparison_results(comparison_suite)
        await self._generate_comparison_visualizations(comparison_suite)
        
        # Print summary
        self._print_comparison_summary(comparison_suite)
        
        return comparison_suite
        
    async def test_scenario_comparison(self, dataset: TestDataSet) -> ScenarioComparison:
        """Test comprehensive comparison for a single scenario"""
        
        logger.info(f"Testing scenario comparison for: {dataset.dataset_id}")
        
        # Test tab processors
        tab_metrics = await self._test_tab_processor_approach(dataset)
        
        # Test all tier services
        tier_metrics = {}
        for tier_level in TierLevel:
            tier_result = await self.integrated_tester.tier_tester.test_tier_service(tier_level, dataset)
            tier_metrics[tier_level] = self._convert_tier_result_to_metrics(tier_result, tier_level.value)
            
        # Analyze comparison
        opportunity_value = dataset.opportunity_data.get("award_ceiling", 0)
        
        cost_efficiency = self.analyzer.analyze_cost_efficiency(tab_metrics, tier_metrics, opportunity_value)
        value_proposition = self.analyzer.analyze_value_proposition(tab_metrics, tier_metrics)
        
        # Determine optimal approach
        optimal_approach = self._determine_optimal_approach(tab_metrics, tier_metrics, dataset)
        
        scenario_comparison = ScenarioComparison(
            scenario_name=f"{dataset.organization_size}_{dataset.complexity_level}_{dataset.sector_type}",
            dataset_id=dataset.dataset_id,
            opportunity_value=opportunity_value,
            organization_size=dataset.organization_size,
            tab_processor_metrics=tab_metrics,
            tier_service_metrics=tier_metrics,
            optimal_approach=optimal_approach,
            cost_efficiency_analysis=cost_efficiency,
            value_proposition_analysis=value_proposition,
            recommendation=""
        )
        
        # Generate recommendations
        scenario_comparison.recommendation = "\n".join(self.analyzer.generate_recommendations(scenario_comparison))
        
        return scenario_comparison
        
    async def _test_tab_processor_approach(self, dataset: TestDataSet) -> ComparisonMetrics:
        """Test tab processor approach and convert to comparison metrics"""
        
        # Run all tab processors
        tab_results = []
        previous_results = None
        
        for tab_name in ["PLAN", "ANALYZE", "EXAMINE", "APPROACH"]:
            tab_result = await self.integrated_tester.tab_tester.test_tab_processor(tab_name, dataset, previous_results)
            tab_results.append(tab_result)
            
            if tab_result.success:
                previous_results = tab_result.output_data
                
        # Calculate metrics
        total_cost = sum(r.api_cost_usd for r in tab_results if r.success)
        avg_processing_time = sum(r.processing_time_seconds for r in tab_results if r.success)
        avg_confidence = sum(r.confidence_score for r in tab_results if r.success) / len([r for r in tab_results if r.success]) if tab_results else 0
        
        return ComparisonMetrics(
            approach_name="tab_processors",
            total_cost=total_cost,
            processing_time_seconds=avg_processing_time,
            quality_score=avg_confidence,
            professional_deliverables=0,  # Tab processors don't provide professional deliverables
            business_readiness_score=0.3,  # Raw technical output
            technical_depth_score=0.9,    # High technical depth
            roi_score=0.0,  # Will be calculated
            user_experience_score=0.7  # Good for technical users
        )
        
    def _convert_tier_result_to_metrics(self, tier_result: TierServiceResult, tier_name: str) -> ComparisonMetrics:
        """Convert tier service result to comparison metrics"""
        
        if not tier_result.success:
            return ComparisonMetrics(
                approach_name=tier_name,
                total_cost=0.0,
                processing_time_seconds=0.0,
                quality_score=0.0,
                professional_deliverables=0,
                business_readiness_score=0.0,
                technical_depth_score=0.0,
                roi_score=0.0,
                user_experience_score=0.0
            )
            
        # Calculate deliverables count
        professional_deliverables = len(tier_result.professional_package)
        
        # Calculate business readiness score based on tier
        business_readiness_scores = {
            "current": 0.7,
            "standard": 0.8, 
            "enhanced": 0.9,
            "complete": 1.0
        }
        
        return ComparisonMetrics(
            approach_name=tier_name,
            total_cost=tier_result.total_cost_usd,
            processing_time_seconds=tier_result.processing_time_seconds,
            quality_score=tier_result.quality_score,
            professional_deliverables=professional_deliverables,
            business_readiness_score=business_readiness_scores.get(tier_name, 0.7),
            technical_depth_score=0.8,  # Consistent technical depth
            roi_score=0.0,  # Will be calculated
            user_experience_score=business_readiness_scores.get(tier_name, 0.7)  # Better UX for higher tiers
        )
        
    def _determine_optimal_approach(self, tab_metrics: ComparisonMetrics,
                                  tier_metrics: Dict[TierLevel, ComparisonMetrics],
                                  dataset: TestDataSet) -> str:
        """Determine optimal approach based on scenario characteristics"""
        
        opportunity_value = dataset.opportunity_data.get("award_ceiling", 0)
        org_size = dataset.organization_size
        complexity = dataset.complexity_level
        
        # Decision matrix based on scenario characteristics
        if org_size == "small" and opportunity_value < 50000:
            return "tab_processors"
        elif org_size == "small" and opportunity_value < 200000:
            return "current_tier"
        elif org_size == "medium" and opportunity_value < 100000:
            return "standard_tier"
        elif org_size == "medium" and opportunity_value < 500000:
            return "enhanced_tier"
        elif complexity == "transformational" or opportunity_value > 1000000:
            return "complete_tier"
        else:
            return "enhanced_tier"
            
    def _analyze_comparison_suite(self, scenario_comparisons: List[ScenarioComparison]) -> Dict[str, Any]:
        """Analyze results across all scenario comparisons"""
        
        analysis = {
            "total_scenarios_tested": len(scenario_comparisons),
            "approach_performance": {},
            "cost_efficiency_trends": {},
            "quality_trends": {},
            "optimal_approach_distribution": {}
        }
        
        # Analyze performance by approach
        approaches = ["tab_processors", "current", "standard", "enhanced", "complete"]
        
        for approach in approaches:
            costs = []
            quality_scores = []
            roi_scores = []
            
            for scenario in scenario_comparisons:
                if approach == "tab_processors":
                    costs.append(scenario.tab_processor_metrics.total_cost)
                    quality_scores.append(scenario.tab_processor_metrics.quality_score)
                else:
                    tier_level = TierLevel(approach)
                    if tier_level in scenario.tier_service_metrics:
                        costs.append(scenario.tier_service_metrics[tier_level].total_cost)
                        quality_scores.append(scenario.tier_service_metrics[tier_level].quality_score)
                        
            if costs and quality_scores:
                analysis["approach_performance"][approach] = {
                    "average_cost": sum(costs) / len(costs),
                    "average_quality": sum(quality_scores) / len(quality_scores),
                    "cost_range": [min(costs), max(costs)],
                    "quality_range": [min(quality_scores), max(quality_scores)]
                }
                
        # Analyze optimal approach distribution
        optimal_counts = {}
        for scenario in scenario_comparisons:
            optimal = scenario.optimal_approach
            optimal_counts[optimal] = optimal_counts.get(optimal, 0) + 1
            
        analysis["optimal_approach_distribution"] = optimal_counts
        
        return analysis
        
    def _generate_tier_recommendations(self, scenario_comparisons: List[ScenarioComparison]) -> Dict[str, List[str]]:
        """Generate tier recommendations by organization size and opportunity type"""
        
        recommendations = {
            "small_organizations": [],
            "medium_organizations": [], 
            "large_organizations": [],
            "general_guidelines": []
        }
        
        # Analyze patterns by organization size
        small_org_scenarios = [s for s in scenario_comparisons if s.organization_size == "small"]
        medium_org_scenarios = [s for s in scenario_comparisons if s.organization_size == "medium"]
        large_org_scenarios = [s for s in scenario_comparisons if s.organization_size == "large"]
        
        # Small organization recommendations
        if small_org_scenarios:
            small_optimal = [s.optimal_approach for s in small_org_scenarios]
            most_common_small = max(set(small_optimal), key=small_optimal.count) if small_optimal else "tab_processors"
            recommendations["small_organizations"].append(f"Most optimal approach: {most_common_small}")
            recommendations["small_organizations"].append("Focus on cost efficiency and ROI optimization")
            recommendations["small_organizations"].append("Use tab processors for small opportunities (<$50K)")
            recommendations["small_organizations"].append("Current tier for opportunities requiring professional deliverables")
            
        # Medium organization recommendations
        if medium_org_scenarios:
            medium_optimal = [s.optimal_approach for s in medium_org_scenarios]
            most_common_medium = max(set(medium_optimal), key=medium_optimal.count) if medium_optimal else "standard_tier"
            recommendations["medium_organizations"].append(f"Most optimal approach: {most_common_medium}")
            recommendations["medium_organizations"].append("Standard tier provides optimal balance for most scenarios")
            recommendations["medium_organizations"].append("Enhanced tier for relationship-critical opportunities")
            
        # Large organization recommendations
        if large_org_scenarios:
            large_optimal = [s.optimal_approach for s in large_org_scenarios]
            most_common_large = max(set(large_optimal), key=large_optimal.count) if large_optimal else "enhanced_tier"
            recommendations["large_organizations"].append(f"Most optimal approach: {most_common_large}")
            recommendations["large_organizations"].append("Enhanced/Complete tiers justified by organizational capacity")
            recommendations["large_organizations"].append("Complete tier for transformational opportunities")
            
        # General guidelines
        recommendations["general_guidelines"].extend([
            "Tab processors: Best for technical users with cost constraints",
            "Current tier: Professional deliverables at budget-friendly cost",
            "Standard tier: Historical intelligence for competitive advantage", 
            "Enhanced tier: Relationship intelligence for high-stakes opportunities",
            "Complete tier: Comprehensive intelligence for transformational initiatives"
        ])
        
        return recommendations
        
    def _create_cost_efficiency_matrix(self, scenario_comparisons: List[ScenarioComparison]) -> Dict[str, Any]:
        """Create cost efficiency matrix across scenarios and approaches"""
        
        matrix = {
            "scenarios": [],
            "approaches": ["tab_processors", "current", "standard", "enhanced", "complete"],
            "efficiency_scores": {},
            "roi_scores": {}
        }
        
        for scenario in scenario_comparisons:
            scenario_name = f"{scenario.dataset_id}"
            matrix["scenarios"].append(scenario_name)
            
            opportunity_value = scenario.opportunity_value
            
            # Calculate efficiency scores for each approach
            matrix["efficiency_scores"][scenario_name] = {}
            matrix["roi_scores"][scenario_name] = {}
            
            # Tab processors
            tab_cost = scenario.tab_processor_metrics.total_cost
            tab_quality = scenario.tab_processor_metrics.quality_score
            tab_roi = (opportunity_value * tab_quality - tab_cost) / tab_cost if tab_cost > 0 else 0
            
            matrix["efficiency_scores"][scenario_name]["tab_processors"] = tab_quality / tab_cost if tab_cost > 0 else 0
            matrix["roi_scores"][scenario_name]["tab_processors"] = tab_roi
            
            # Tier services
            for tier_level in TierLevel:
                tier_name = tier_level.value
                if tier_level in scenario.tier_service_metrics:
                    tier_metrics = scenario.tier_service_metrics[tier_level]
                    tier_cost = tier_metrics.total_cost
                    tier_quality = tier_metrics.quality_score
                    tier_roi = (opportunity_value * tier_quality - tier_cost) / tier_cost if tier_cost > 0 else 0
                    
                    matrix["efficiency_scores"][scenario_name][tier_name] = tier_quality / tier_cost if tier_cost > 0 else 0
                    matrix["roi_scores"][scenario_name][tier_name] = tier_roi
                    
        return matrix
        
    def _analyze_roi_across_scenarios(self, scenario_comparisons: List[ScenarioComparison]) -> Dict[str, Any]:
        """Analyze ROI patterns across different scenarios"""
        
        roi_analysis = {
            "by_organization_size": {},
            "by_opportunity_value": {},
            "by_complexity": {},
            "overall_trends": {}
        }
        
        # Analyze by organization size
        for org_size in ["small", "medium", "large"]:
            size_scenarios = [s for s in scenario_comparisons if s.organization_size == org_size]
            
            if size_scenarios:
                # Calculate average ROI by approach for this size
                approach_rois = {}
                
                for scenario in size_scenarios:
                    # Tab processors
                    tab_roi = self._calculate_roi(scenario.tab_processor_metrics, scenario.opportunity_value)
                    if "tab_processors" not in approach_rois:
                        approach_rois["tab_processors"] = []
                    approach_rois["tab_processors"].append(tab_roi)
                    
                    # Tier services
                    for tier_level, tier_metrics in scenario.tier_service_metrics.items():
                        tier_roi = self._calculate_roi(tier_metrics, scenario.opportunity_value)
                        tier_name = tier_level.value
                        if tier_name not in approach_rois:
                            approach_rois[tier_name] = []
                        approach_rois[tier_name].append(tier_roi)
                        
                # Calculate averages
                roi_analysis["by_organization_size"][org_size] = {}
                for approach, rois in approach_rois.items():
                    roi_analysis["by_organization_size"][org_size][approach] = {
                        "average_roi": sum(rois) / len(rois) if rois else 0,
                        "roi_range": [min(rois), max(rois)] if rois else [0, 0]
                    }
                    
        return roi_analysis
        
    def _calculate_roi(self, metrics: ComparisonMetrics, opportunity_value: float) -> float:
        """Calculate ROI for given metrics and opportunity value"""
        if metrics.total_cost <= 0:
            return 0.0
        return (opportunity_value * metrics.quality_score - metrics.total_cost) / metrics.total_cost
        
    async def _save_comparison_results(self, comparison_suite: Dict[str, Any]):
        """Save comprehensive comparison results"""
        
        # Save main results
        results_file = self.results_dir / "comprehensive_comparison_results.json"
        with open(results_file, 'w') as f:
            json.dump(comparison_suite, f, indent=2, default=str)
            
        # Save individual scenario comparisons
        for i, scenario in enumerate(comparison_suite["scenario_comparisons"]):
            scenario_file = self.results_dir / f"scenario_comparison_{i+1}_{scenario.dataset_id}.json"
            with open(scenario_file, 'w') as f:
                json.dump(asdict(scenario), f, indent=2, default=str)
                
        # Save analysis summaries
        summary_file = self.results_dir / "comparison_analysis_summary.json"
        with open(summary_file, 'w') as f:
            json.dump({
                "summary_analysis": comparison_suite["summary_analysis"],
                "tier_recommendations": comparison_suite["tier_recommendations"],
                "cost_efficiency_matrix": comparison_suite["cost_efficiency_matrix"],
                "roi_analysis": comparison_suite["roi_analysis"]
            }, f, indent=2, default=str)
            
        logger.info(f"Comparison results saved to: {self.results_dir}")
        
    async def _generate_comparison_visualizations(self, comparison_suite: Dict[str, Any]):
        """Generate visualization charts for comparison results"""
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # Create visualizations directory
            viz_dir = self.results_dir / "visualizations"
            viz_dir.mkdir(exist_ok=True)
            
            # Cost vs Quality scatter plot
            fig, ax = plt.subplots(figsize=(12, 8))
            
            scenarios = comparison_suite["scenario_comparisons"]
            approaches = ["tab_processors", "current", "standard", "enhanced", "complete"]
            colors = ['blue', 'green', 'orange', 'red', 'purple']
            
            for i, approach in enumerate(approaches):
                costs = []
                qualities = []
                
                for scenario in scenarios:
                    if approach == "tab_processors":
                        costs.append(scenario.tab_processor_metrics.total_cost)
                        qualities.append(scenario.tab_processor_metrics.quality_score)
                    else:
                        tier_level = TierLevel(approach)
                        if tier_level in scenario.tier_service_metrics:
                            costs.append(scenario.tier_service_metrics[tier_level].total_cost)
                            qualities.append(scenario.tier_service_metrics[tier_level].quality_score)
                            
                if costs and qualities:
                    ax.scatter(costs, qualities, c=colors[i], label=approach, alpha=0.7, s=100)
                    
            ax.set_xlabel('Total Cost ($)')
            ax.set_ylabel('Quality Score')
            ax.set_title('Cost vs Quality Comparison Across Approaches')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(viz_dir / "cost_vs_quality_comparison.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            # ROI comparison bar chart
            fig, ax = plt.subplots(figsize=(14, 8))
            
            roi_data = comparison_suite["roi_analysis"]["by_organization_size"]
            
            org_sizes = list(roi_data.keys())
            approaches_roi = ["tab_processors", "current", "standard", "enhanced", "complete"]
            
            x = np.arange(len(org_sizes))
            width = 0.15
            
            for i, approach in enumerate(approaches_roi):
                roi_values = []
                for org_size in org_sizes:
                    roi_info = roi_data[org_size].get(approach, {})
                    roi_values.append(roi_info.get("average_roi", 0))
                    
                ax.bar(x + i*width, roi_values, width, label=approach)
                
            ax.set_xlabel('Organization Size')
            ax.set_ylabel('Average ROI')
            ax.set_title('Average ROI by Organization Size and Approach')
            ax.set_xticks(x + width * 2)
            ax.set_xticklabels(org_sizes)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(viz_dir / "roi_comparison_by_org_size.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Comparison visualizations saved to: {viz_dir}")
            
        except ImportError:
            logger.warning("Matplotlib not available - skipping visualization generation")
            
    def _print_comparison_summary(self, comparison_suite: Dict[str, Any]):
        """Print comprehensive comparison summary"""
        
        print(f"\n{'='*100}")
        print("TIER COMPARISON TESTING FRAMEWORK - COMPREHENSIVE RESULTS")
        print(f"{'='*100}")
        
        summary = comparison_suite["summary_analysis"]
        
        print(f"Session ID: {comparison_suite['session_id']}")
        print(f"Total Scenarios Tested: {summary['total_scenarios_tested']}")
        
        print(f"\n{'='*50} APPROACH PERFORMANCE {'='*50}")
        
        for approach, performance in summary["approach_performance"].items():
            print(f"\n{approach.upper()}:")
            print(f"  Average Cost: ${performance['average_cost']:.2f}")
            print(f"  Average Quality: {performance['average_quality']:.2f}")
            print(f"  Cost Range: ${performance['cost_range'][0]:.2f} - ${performance['cost_range'][1]:.2f}")
            print(f"  Quality Range: {performance['quality_range'][0]:.2f} - {performance['quality_range'][1]:.2f}")
            
        print(f"\n{'='*50} OPTIMAL APPROACH DISTRIBUTION {'='*50}")
        
        optimal_dist = summary["optimal_approach_distribution"]
        for approach, count in optimal_dist.items():
            percentage = (count / summary['total_scenarios_tested']) * 100
            print(f"{approach}: {count} scenarios ({percentage:.1f}%)")
            
        print(f"\n{'='*50} TIER RECOMMENDATIONS {'='*50}")
        
        recommendations = comparison_suite["tier_recommendations"]
        
        for category, recs in recommendations.items():
            print(f"\n{category.replace('_', ' ').title()}:")
            for rec in recs:
                print(f"  • {rec}")
                
        print(f"\n{'='*50} SCENARIO RESULTS {'='*50}")
        
        for scenario in comparison_suite["scenario_comparisons"]:
            print(f"\n{scenario.scenario_name} ({scenario.dataset_id}):")
            print(f"  Opportunity Value: ${scenario.opportunity_value:,}")
            print(f"  Optimal Approach: {scenario.optimal_approach}")
            print(f"  Cost Efficiency Winner: {scenario.cost_efficiency_analysis.get('cost_efficiency_winner', 'N/A')}")
            
        print(f"\n{'='*100}")
        print("COMPARISON TESTING COMPLETE - See detailed results and visualizations in comparison_results directory")
        print(f"{'='*100}\n")

# Main execution function
async def run_tier_comparison_testing():
    """Run comprehensive tier comparison testing"""
    
    print("Tier Comparison Testing Framework - Side-by-Side Analysis")
    print("=" * 100)
    
    # Initialize with comprehensive configuration
    config = TestConfiguration(
        max_total_budget=100.00,  # Higher budget for comprehensive comparison
        enable_real_api=False,  # Set to True for real API testing
        enable_simulation=True,
        save_detailed_results=True
    )
    
    # Create comparison tester
    tester = TierComparisonTester(config)
    
    try:
        # Run comprehensive comparison
        results = await tester.run_comprehensive_comparison()
        
        print(f"\n✓ Comprehensive comparison testing completed successfully!")
        print(f"✓ Results saved to: {tester.results_dir}")
        print(f"✓ Total scenarios tested: {len(results['scenario_comparisons'])}")
        
        return results
        
    except Exception as e:
        logger.error(f"Comparison testing failed: {e}")
        print(f"✗ Testing failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the comprehensive comparison testing
    asyncio.run(run_tier_comparison_testing())