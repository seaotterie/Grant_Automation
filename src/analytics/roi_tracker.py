#!/usr/bin/env python3
"""
Catalynx ROI Tracking and Optimization System
Comprehensive ROI analysis, tracking, and optimization for grant opportunities
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class ROIMetricType(Enum):
    FINANCIAL = "financial"
    TIME = "time"
    RESOURCE = "resource"
    OPPORTUNITY_COST = "opportunity_cost"
    STRATEGIC = "strategic"

@dataclass
class ROIMetrics:
    financial_roi: float
    time_roi: float
    resource_efficiency: float
    opportunity_cost: float
    strategic_value: float
    total_weighted_roi: float
    confidence_level: float
    calculation_date: datetime

@dataclass
class CostBreakdown:
    personnel_hours: float
    personnel_cost: float
    research_time: float
    application_prep_time: float
    follow_up_time: float
    opportunity_costs: float
    total_investment: float

@dataclass
class BenefitAnalysis:
    grant_amount: float
    indirect_benefits: float
    strategic_benefits: float
    network_benefits: float
    reputation_benefits: float
    total_benefits: float

@dataclass
class ROIOptimization:
    current_roi: float
    optimized_roi: float
    improvement_potential: float
    recommended_actions: List[str]
    resource_reallocation: Dict[str, float]
    timeline_optimization: Dict[str, int]

class ROITracker:
    """Advanced ROI tracking and optimization system"""
    
    def __init__(self):
        # ROI calculation weights
        self.roi_weights = {
            ROIMetricType.FINANCIAL: 0.40,
            ROIMetricType.TIME: 0.20,
            ROIMetricType.RESOURCE: 0.15,
            ROIMetricType.OPPORTUNITY_COST: 0.15,
            ROIMetricType.STRATEGIC: 0.10
        }
        
        # Cost estimation models
        self.cost_models = {
            'personnel_hourly_rate': 75.0,  # Average hourly rate
            'overhead_multiplier': 1.3,     # Overhead costs
            'opportunity_cost_rate': 0.12   # Annual opportunity cost rate
        }
        
        # Historical ROI data for benchmarking
        self.historical_data = []
        
    def calculate_comprehensive_roi(self, opportunity_data: Dict[str, Any], 
                                  actual_costs: Optional[Dict[str, float]] = None,
                                  actual_outcome: Optional[Dict[str, Any]] = None) -> ROIMetrics:
        """Calculate comprehensive ROI including all dimensions"""
        
        # Calculate costs
        if actual_costs:
            cost_breakdown = self._parse_actual_costs(actual_costs)
        else:
            cost_breakdown = self._estimate_costs(opportunity_data)
        
        # Calculate benefits
        if actual_outcome:
            benefit_analysis = self._parse_actual_benefits(actual_outcome)
        else:
            benefit_analysis = self._estimate_benefits(opportunity_data)
        
        # Calculate individual ROI metrics
        financial_roi = self._calculate_financial_roi(cost_breakdown, benefit_analysis)
        time_roi = self._calculate_time_roi(opportunity_data, cost_breakdown)
        resource_efficiency = self._calculate_resource_efficiency(opportunity_data, cost_breakdown)
        opportunity_cost = self._calculate_opportunity_cost(opportunity_data, cost_breakdown)
        strategic_value = self._calculate_strategic_value(opportunity_data)
        
        # Calculate weighted total ROI
        total_weighted_roi = (
            financial_roi * self.roi_weights[ROIMetricType.FINANCIAL] +
            time_roi * self.roi_weights[ROIMetricType.TIME] +
            resource_efficiency * self.roi_weights[ROIMetricType.RESOURCE] +
            (1 - opportunity_cost) * self.roi_weights[ROIMetricType.OPPORTUNITY_COST] +
            strategic_value * self.roi_weights[ROIMetricType.STRATEGIC]
        )
        
        # Calculate confidence level
        confidence_level = self._calculate_roi_confidence(opportunity_data, actual_costs, actual_outcome)
        
        return ROIMetrics(
            financial_roi=financial_roi,
            time_roi=time_roi,
            resource_efficiency=resource_efficiency,
            opportunity_cost=opportunity_cost,
            strategic_value=strategic_value,
            total_weighted_roi=total_weighted_roi,
            confidence_level=confidence_level,
            calculation_date=datetime.now()
        )
    
    def _estimate_costs(self, opportunity_data: Dict[str, Any]) -> CostBreakdown:
        """Estimate costs for pursuing an opportunity"""
        
        # Base time estimates (in hours)
        grant_size = opportunity_data.get('grant_amount', 100000)
        complexity_factor = min(3.0, np.log10(max(grant_size, 1000)) / 3)
        
        # Time estimates based on grant size and complexity
        research_time = 8 + (complexity_factor * 12)
        application_prep_time = 20 + (complexity_factor * 30)
        follow_up_time = 5 + (complexity_factor * 10)
        
        total_hours = research_time + application_prep_time + follow_up_time
        
        # Cost calculations
        personnel_cost = total_hours * self.cost_models['personnel_hourly_rate']
        overhead_cost = personnel_cost * (self.cost_models['overhead_multiplier'] - 1)
        
        # Opportunity cost (time could be spent on other activities)
        opportunity_costs = total_hours * self.cost_models['personnel_hourly_rate'] * 0.3
        
        total_investment = personnel_cost + overhead_cost + opportunity_costs
        
        return CostBreakdown(
            personnel_hours=total_hours,
            personnel_cost=personnel_cost,
            research_time=research_time,
            application_prep_time=application_prep_time,
            follow_up_time=follow_up_time,
            opportunity_costs=opportunity_costs,
            total_investment=total_investment
        )
    
    def _estimate_benefits(self, opportunity_data: Dict[str, Any]) -> BenefitAnalysis:
        """Estimate benefits from an opportunity"""
        
        grant_amount = opportunity_data.get('grant_amount', 0)
        success_probability = opportunity_data.get('success_probability', 0.5)
        
        # Expected grant value
        expected_grant_value = grant_amount * success_probability
        
        # Indirect benefits
        indirect_benefits = expected_grant_value * 0.2  # 20% indirect value
        
        # Strategic benefits (long-term value)
        strategic_alignment = opportunity_data.get('strategic_alignment', 0.5)
        strategic_benefits = expected_grant_value * strategic_alignment * 0.3
        
        # Network benefits (relationship building)
        network_value = opportunity_data.get('network_value', 0.3)
        network_benefits = grant_amount * network_value * 0.15
        
        # Reputation benefits
        reputation_value = min(grant_amount * 0.1, 50000)  # Cap reputation value
        
        total_benefits = (expected_grant_value + indirect_benefits + 
                         strategic_benefits + network_benefits + reputation_value)
        
        return BenefitAnalysis(
            grant_amount=expected_grant_value,
            indirect_benefits=indirect_benefits,
            strategic_benefits=strategic_benefits,
            network_benefits=network_benefits,
            reputation_benefits=reputation_value,
            total_benefits=total_benefits
        )
    
    def _calculate_financial_roi(self, costs: CostBreakdown, benefits: BenefitAnalysis) -> float:
        """Calculate traditional financial ROI"""
        if costs.total_investment <= 0:
            return 0.0
        
        return (benefits.total_benefits - costs.total_investment) / costs.total_investment
    
    def _calculate_time_roi(self, opportunity_data: Dict[str, Any], costs: CostBreakdown) -> float:
        """Calculate time-based ROI"""
        expected_timeline = opportunity_data.get('expected_timeline_days', 180)
        grant_amount = opportunity_data.get('grant_amount', 0)
        success_probability = opportunity_data.get('success_probability', 0.5)
        
        # Value per day if successful
        daily_value = (grant_amount * success_probability) / max(expected_timeline, 1)
        
        # Time investment in days
        time_investment_days = costs.personnel_hours / 8  # Assume 8-hour workdays
        
        # Time ROI
        if time_investment_days > 0:
            return daily_value / (time_investment_days * self.cost_models['personnel_hourly_rate'] * 8)
        
        return 0.0
    
    def _calculate_resource_efficiency(self, opportunity_data: Dict[str, Any], costs: CostBreakdown) -> float:
        """Calculate resource utilization efficiency"""
        grant_amount = opportunity_data.get('grant_amount', 0)
        success_probability = opportunity_data.get('success_probability', 0.5)
        
        expected_value_per_hour = (grant_amount * success_probability) / max(costs.personnel_hours, 1)
        
        # Benchmark against industry standards (e.g., $1000 per hour is excellent)
        benchmark_value_per_hour = 1000
        
        return min(2.0, expected_value_per_hour / benchmark_value_per_hour)
    
    def _calculate_opportunity_cost(self, opportunity_data: Dict[str, Any], costs: CostBreakdown) -> float:
        """Calculate opportunity cost ratio"""
        # Opportunity cost as a ratio of total investment
        return costs.opportunity_costs / max(costs.total_investment, 1)
    
    def _calculate_strategic_value(self, opportunity_data: Dict[str, Any]) -> float:
        """Calculate strategic value score"""
        factors = [
            opportunity_data.get('strategic_alignment', 0.5),
            opportunity_data.get('mission_fit', 0.5),
            opportunity_data.get('capacity_building_potential', 0.5),
            opportunity_data.get('network_expansion_potential', 0.5),
            opportunity_data.get('reputation_enhancement', 0.5)
        ]
        
        return np.mean(factors)
    
    def _calculate_roi_confidence(self, opportunity_data: Dict[str, Any], 
                                actual_costs: Optional[Dict[str, float]], 
                                actual_outcome: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence level in ROI calculation"""
        confidence_factors = []
        
        # Data completeness
        required_fields = ['grant_amount', 'success_probability', 'expected_timeline_days']
        available_fields = sum(1 for field in required_fields if field in opportunity_data)
        completeness = available_fields / len(required_fields)
        confidence_factors.append(completeness * 0.4)
        
        # Actual data availability
        if actual_costs:
            confidence_factors.append(0.3)
        if actual_outcome:
            confidence_factors.append(0.3)
        
        # Historical data similarity
        if self.historical_data:
            similarity_score = self._calculate_historical_similarity(opportunity_data)
            confidence_factors.append(similarity_score * 0.2)
        
        return sum(confidence_factors)
    
    def optimize_roi(self, opportunities: List[Dict[str, Any]], 
                    resource_constraints: Dict[str, float]) -> ROIOptimization:
        """Optimize ROI across multiple opportunities given resource constraints"""
        
        # Calculate ROI for each opportunity
        opportunity_rois = []
        for opp in opportunities:
            roi_metrics = self.calculate_comprehensive_roi(opp)
            opportunity_rois.append({
                'opportunity_id': opp.get('id', 'unknown'),
                'roi_metrics': roi_metrics,
                'resource_required': self._estimate_costs(opp).total_investment,
                'expected_value': opp.get('grant_amount', 0) * opp.get('success_probability', 0.5)
            })
        
        # Sort by ROI efficiency
        opportunity_rois.sort(key=lambda x: x['roi_metrics'].total_weighted_roi, reverse=True)
        
        # Resource allocation optimization
        total_budget = resource_constraints.get('budget', 100000)
        total_time = resource_constraints.get('time_hours', 160)  # 1 month
        
        # Greedy optimization (can be enhanced with more sophisticated algorithms)
        selected_opportunities = []
        remaining_budget = total_budget
        remaining_time = total_time
        
        for opp in opportunity_rois:
            required_investment = opp['resource_required']
            required_time = self._estimate_costs({'grant_amount': opp['expected_value']}).personnel_hours
            
            if required_investment <= remaining_budget and required_time <= remaining_time:
                selected_opportunities.append(opp)
                remaining_budget -= required_investment
                remaining_time -= required_time
        
        # Calculate optimization results
        current_roi = np.mean([opp['roi_metrics'].total_weighted_roi for opp in opportunity_rois[:3]])
        optimized_roi = np.mean([opp['roi_metrics'].total_weighted_roi for opp in selected_opportunities])
        
        improvement_potential = optimized_roi - current_roi
        
        # Generate recommendations
        recommendations = self._generate_optimization_recommendations(
            selected_opportunities, opportunity_rois, resource_constraints
        )
        
        # Resource reallocation suggestions
        resource_reallocation = {
            'high_roi_opportunities': len(selected_opportunities),
            'budget_utilization': (total_budget - remaining_budget) / total_budget,
            'time_utilization': (total_time - remaining_time) / total_time
        }
        
        return ROIOptimization(
            current_roi=current_roi,
            optimized_roi=optimized_roi,
            improvement_potential=improvement_potential,
            recommended_actions=recommendations,
            resource_reallocation=resource_reallocation,
            timeline_optimization={'recommended_sequence': list(range(len(selected_opportunities)))}
        )
    
    def _generate_optimization_recommendations(self, selected_opportunities: List[Dict[str, Any]], 
                                            all_opportunities: List[Dict[str, Any]], 
                                            constraints: Dict[str, float]) -> List[str]:
        """Generate actionable optimization recommendations"""
        recommendations = []
        
        if len(selected_opportunities) < len(all_opportunities):
            recommendations.append(f"Focus on top {len(selected_opportunities)} opportunities for maximum ROI")
        
        # ROI-based recommendations
        avg_roi = np.mean([opp['roi_metrics'].total_weighted_roi for opp in selected_opportunities])
        if avg_roi > 2.0:
            recommendations.append("Excellent ROI portfolio - consider increasing resource allocation")
        elif avg_roi > 1.0:
            recommendations.append("Good ROI portfolio - monitor performance and adjust as needed")
        else:
            recommendations.append("ROI below target - review opportunity selection criteria")
        
        # Resource utilization recommendations
        budget_util = constraints.get('budget', 0)
        if budget_util > 0:
            utilization = sum(opp['resource_required'] for opp in selected_opportunities) / budget_util
            if utilization < 0.8:
                recommendations.append("Consider additional opportunities to fully utilize budget")
            elif utilization > 0.95:
                recommendations.append("Budget nearly fully allocated - monitor for overruns")
        
        return recommendations
    
    def track_actual_performance(self, opportunity_id: str, actual_outcome: Dict[str, Any]):
        """Track actual performance against ROI predictions"""
        
        performance_record = {
            'opportunity_id': opportunity_id,
            'actual_outcome': actual_outcome,
            'tracking_date': datetime.now(),
            'success': actual_outcome.get('success', False),
            'actual_grant_amount': actual_outcome.get('grant_amount', 0),
            'actual_timeline': actual_outcome.get('completion_days', 0),
            'actual_costs': actual_outcome.get('total_costs', 0)
        }
        
        # Add to historical data
        self.historical_data.append(performance_record)
        
        # Calculate actual ROI
        if performance_record['actual_costs'] > 0:
            actual_roi = (performance_record['actual_grant_amount'] - performance_record['actual_costs']) / performance_record['actual_costs']
            performance_record['actual_roi'] = actual_roi
        
        return performance_record
    
    def generate_roi_report(self, opportunities: List[Dict[str, Any]], 
                          time_period: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Generate comprehensive ROI performance report"""
        
        # Calculate ROI for all opportunities
        roi_analyses = []
        for opp in opportunities:
            roi_metrics = self.calculate_comprehensive_roi(opp)
            roi_analyses.append({
                'opportunity_id': opp.get('id', 'unknown'),
                'opportunity_name': opp.get('name', 'Unknown'),
                'roi_metrics': asdict(roi_metrics),
                'grant_amount': opp.get('grant_amount', 0),
                'success_probability': opp.get('success_probability', 0.5)
            })
        
        # Aggregate statistics
        roi_values = [analysis['roi_metrics']['total_weighted_roi'] for analysis in roi_analyses]
        
        report = {
            'summary': {
                'total_opportunities': len(opportunities),
                'average_roi': np.mean(roi_values) if roi_values else 0,
                'median_roi': np.median(roi_values) if roi_values else 0,
                'roi_standard_deviation': np.std(roi_values) if roi_values else 0,
                'high_roi_count': sum(1 for roi in roi_values if roi > 1.0),
                'report_date': datetime.now().isoformat()
            },
            'top_opportunities': sorted(roi_analyses, 
                                      key=lambda x: x['roi_metrics']['total_weighted_roi'], 
                                      reverse=True)[:10],
            'roi_distribution': {
                'excellent': sum(1 for roi in roi_values if roi > 2.0),
                'good': sum(1 for roi in roi_values if 1.0 < roi <= 2.0),
                'fair': sum(1 for roi in roi_values if 0.5 < roi <= 1.0),
                'poor': sum(1 for roi in roi_values if roi <= 0.5)
            },
            'recommendations': self._generate_portfolio_recommendations(roi_analyses),
            'historical_performance': self._analyze_historical_performance(time_period)
        }
        
        return report
    
    def _generate_portfolio_recommendations(self, roi_analyses: List[Dict[str, Any]]) -> List[str]:
        """Generate portfolio-level recommendations"""
        recommendations = []
        
        roi_values = [analysis['roi_metrics']['total_weighted_roi'] for analysis in roi_analyses]
        avg_roi = np.mean(roi_values) if roi_values else 0
        
        if avg_roi > 1.5:
            recommendations.append("Strong portfolio performance - consider scaling successful strategies")
        elif avg_roi > 1.0:
            recommendations.append("Solid portfolio performance - identify top performers for replication")
        else:
            recommendations.append("Portfolio underperforming - review selection criteria and processes")
        
        # Diversification recommendations
        high_value_opps = sum(1 for analysis in roi_analyses if analysis['grant_amount'] > 500000)
        if high_value_opps / len(roi_analyses) > 0.7:
            recommendations.append("Portfolio heavily weighted toward large grants - consider diversification")
        
        return recommendations
    
    def _analyze_historical_performance(self, time_period: Optional[Tuple[datetime, datetime]]) -> Dict[str, Any]:
        """Analyze historical ROI performance"""
        if not self.historical_data:
            return {"message": "No historical data available"}
        
        filtered_data = self.historical_data
        if time_period:
            start_date, end_date = time_period
            filtered_data = [record for record in self.historical_data 
                           if start_date <= record['tracking_date'] <= end_date]
        
        if not filtered_data:
            return {"message": "No data available for specified time period"}
        
        success_rate = sum(1 for record in filtered_data if record['success']) / len(filtered_data)
        avg_actual_roi = np.mean([record.get('actual_roi', 0) for record in filtered_data 
                                if 'actual_roi' in record])
        
        return {
            'total_tracked': len(filtered_data),
            'success_rate': success_rate,
            'average_actual_roi': avg_actual_roi,
            'successful_opportunities': [record for record in filtered_data if record['success']]
        }
    
    def _calculate_historical_similarity(self, opportunity_data: Dict[str, Any]) -> float:
        """Calculate similarity to historical opportunities"""
        if not self.historical_data:
            return 0.5
        
        # Simple similarity based on grant amount and type
        grant_amount = opportunity_data.get('grant_amount', 0)
        similarities = []
        
        for record in self.historical_data:
            historical_amount = record['actual_outcome'].get('grant_amount', 0)
            amount_similarity = 1 - abs(grant_amount - historical_amount) / max(grant_amount, historical_amount, 1)
            similarities.append(max(0, amount_similarity))
        
        return np.mean(similarities) if similarities else 0.5
    
    def _parse_actual_costs(self, actual_costs: Dict[str, float]) -> CostBreakdown:
        """Parse actual cost data into structured format"""
        return CostBreakdown(
            personnel_hours=actual_costs.get('personnel_hours', 0),
            personnel_cost=actual_costs.get('personnel_cost', 0),
            research_time=actual_costs.get('research_time', 0),
            application_prep_time=actual_costs.get('application_prep_time', 0),
            follow_up_time=actual_costs.get('follow_up_time', 0),
            opportunity_costs=actual_costs.get('opportunity_costs', 0),
            total_investment=actual_costs.get('total_investment', 0)
        )
    
    def _parse_actual_benefits(self, actual_outcome: Dict[str, Any]) -> BenefitAnalysis:
        """Parse actual outcome data into structured format"""
        return BenefitAnalysis(
            grant_amount=actual_outcome.get('grant_amount', 0),
            indirect_benefits=actual_outcome.get('indirect_benefits', 0),
            strategic_benefits=actual_outcome.get('strategic_benefits', 0),
            network_benefits=actual_outcome.get('network_benefits', 0),
            reputation_benefits=actual_outcome.get('reputation_benefits', 0),
            total_benefits=actual_outcome.get('total_benefits', 0)
        )

# Global ROI tracker instance
roi_tracker = ROITracker()