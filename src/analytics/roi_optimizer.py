#!/usr/bin/env python3
"""
Catalynx ROI Optimization Engine
Advanced algorithms for maximizing ROI across opportunity portfolios
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from scipy.optimize import minimize, linprog
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)

@dataclass
class OptimizationResult:
    selected_opportunities: List[str]
    expected_total_roi: float
    resource_allocation: Dict[str, float]
    optimization_method: str
    confidence_score: float
    improvement_over_baseline: float

@dataclass
class PortfolioMetrics:
    total_expected_value: float
    total_investment: float
    portfolio_roi: float
    risk_score: float
    diversification_index: float
    time_to_completion: int

class ROIOptimizer:
    """Advanced ROI optimization using multiple algorithms"""
    
    def __init__(self):
        self.optimization_methods = {
            'greedy': self._greedy_optimization,
            'knapsack': self._knapsack_optimization,
            'linear_programming': self._linear_programming_optimization,
            'risk_adjusted': self._risk_adjusted_optimization,
            'portfolio_balanced': self._portfolio_balanced_optimization
        }
        
        # Risk parameters
        self.risk_tolerance = 0.3  # 30% risk tolerance
        self.diversification_target = 0.7  # Target diversification score
        
    def optimize_portfolio(self, opportunities: List[Dict[str, Any]], 
                         constraints: Dict[str, float],
                         method: str = 'portfolio_balanced') -> OptimizationResult:
        """Optimize opportunity portfolio using specified method"""
        
        if method not in self.optimization_methods:
            raise ValueError(f"Unknown optimization method: {method}")
        
        # Prepare opportunity data
        prepared_opps = self._prepare_opportunities(opportunities)
        
        # Run optimization
        optimizer_func = self.optimization_methods[method]
        result = optimizer_func(prepared_opps, constraints)
        
        # Calculate improvement over baseline
        baseline_roi = self._calculate_baseline_roi(prepared_opps, constraints)
        improvement = result.expected_total_roi - baseline_roi
        
        result.improvement_over_baseline = improvement
        
        return result
    
    def _prepare_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare and enrich opportunity data for optimization"""
        
        prepared = []
        for opp in opportunities:
            # Calculate expected value and risk metrics
            grant_amount = opp.get('grant_amount', 0)
            success_prob = opp.get('success_probability', 0.5)
            expected_value = grant_amount * success_prob
            
            # Risk calculation
            risk_factors = [
                1 - success_prob,  # Success risk
                opp.get('complexity_factor', 0.5),  # Complexity risk
                opp.get('timeline_risk', 0.3),  # Timeline risk
                opp.get('competitive_risk', 0.4)  # Competition risk
            ]
            risk_score = np.mean(risk_factors)
            
            # Investment requirements
            investment = self._estimate_investment_required(opp)
            
            # Strategic value
            strategic_value = opp.get('strategic_alignment', 0.5) * grant_amount * 0.2
            
            prepared_opp = {
                **opp,
                'expected_value': expected_value,
                'risk_score': risk_score,
                'investment_required': investment,
                'strategic_value': strategic_value,
                'roi_potential': (expected_value + strategic_value - investment) / max(investment, 1),
                'risk_adjusted_roi': (expected_value + strategic_value - investment) / max(investment, 1) * (1 - risk_score)
            }
            prepared.append(prepared_opp)
        
        return prepared
    
    def _estimate_investment_required(self, opportunity: Dict[str, Any]) -> float:
        """Estimate investment required for an opportunity"""
        grant_amount = opportunity.get('grant_amount', 0)
        complexity_factor = min(3.0, np.log10(max(grant_amount, 1000)) / 3)
        
        # Base investment (time + overhead)
        base_hours = 30 + (complexity_factor * 25)
        hourly_rate = 75
        overhead_multiplier = 1.3
        
        return base_hours * hourly_rate * overhead_multiplier
    
    def _greedy_optimization(self, opportunities: List[Dict[str, Any]], 
                           constraints: Dict[str, float]) -> OptimizationResult:
        """Simple greedy optimization by ROI ranking"""
        
        # Sort by ROI potential
        sorted_opps = sorted(opportunities, key=lambda x: x['roi_potential'], reverse=True)
        
        selected = []
        total_investment = 0
        total_expected_value = 0
        budget = constraints.get('budget', float('inf'))
        
        for opp in sorted_opps:
            if total_investment + opp['investment_required'] <= budget:
                selected.append(opp['id'])
                total_investment += opp['investment_required']
                total_expected_value += opp['expected_value']
        
        expected_roi = (total_expected_value - total_investment) / max(total_investment, 1)
        
        return OptimizationResult(
            selected_opportunities=selected,
            expected_total_roi=expected_roi,
            resource_allocation={'budget_used': total_investment},
            optimization_method='greedy',
            confidence_score=0.7,
            improvement_over_baseline=0.0  # Will be calculated later
        )
    
    def _knapsack_optimization(self, opportunities: List[Dict[str, Any]], 
                             constraints: Dict[str, float]) -> OptimizationResult:
        """Dynamic programming knapsack optimization"""
        
        budget = int(constraints.get('budget', 100000))
        n_opportunities = len(opportunities)
        
        # Convert to integer weights and values for knapsack
        weights = [int(opp['investment_required']) for opp in opportunities]
        values = [int(opp['expected_value'] + opp['strategic_value']) for opp in opportunities]
        
        # Dynamic programming knapsack solution
        dp = [[0 for _ in range(budget + 1)] for _ in range(n_opportunities + 1)]
        
        for i in range(1, n_opportunities + 1):
            for w in range(budget + 1):
                if weights[i-1] <= w:
                    dp[i][w] = max(values[i-1] + dp[i-1][w-weights[i-1]], dp[i-1][w])
                else:
                    dp[i][w] = dp[i-1][w]
        
        # Backtrack to find selected opportunities
        selected = []
        w = budget
        total_value = dp[n_opportunities][budget]
        total_weight = 0
        
        for i in range(n_opportunities, 0, -1):
            if dp[i][w] != dp[i-1][w]:
                selected.append(opportunities[i-1]['id'])
                total_weight += weights[i-1]
                w -= weights[i-1]
        
        expected_roi = (total_value - total_weight) / max(total_weight, 1)
        
        return OptimizationResult(
            selected_opportunities=selected,
            expected_total_roi=expected_roi,
            resource_allocation={'budget_used': total_weight},
            optimization_method='knapsack',
            confidence_score=0.8,
            improvement_over_baseline=0.0
        )
    
    def _linear_programming_optimization(self, opportunities: List[Dict[str, Any]], 
                                       constraints: Dict[str, float]) -> OptimizationResult:
        """Linear programming optimization with multiple constraints"""
        
        n_opps = len(opportunities)
        
        # Objective function: maximize expected value - investment
        c = [-opp['expected_value'] + opp['investment_required'] for opp in opportunities]
        
        # Constraints
        A_ub = []
        b_ub = []
        
        # Budget constraint
        if 'budget' in constraints:
            budget_constraint = [opp['investment_required'] for opp in opportunities]
            A_ub.append(budget_constraint)
            b_ub.append(constraints['budget'])
        
        # Time constraint
        if 'time_hours' in constraints:
            time_constraint = [opp.get('time_required', 40) for opp in opportunities]
            A_ub.append(time_constraint)
            b_ub.append(constraints['time_hours'])
        
        # Risk constraint
        if 'max_risk' in constraints:
            risk_constraint = [opp['risk_score'] for opp in opportunities]
            A_ub.append(risk_constraint)
            b_ub.append(constraints['max_risk'] * n_opps)
        
        # Variable bounds (0 <= x <= 1 for each opportunity)
        bounds = [(0, 1) for _ in range(n_opps)]
        
        try:
            result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
            
            if result.success:
                # Select opportunities with allocation > 0.5
                selected = [opportunities[i]['id'] for i, x in enumerate(result.x) if x > 0.5]
                
                total_investment = sum(opportunities[i]['investment_required'] * result.x[i] 
                                     for i in range(n_opps))
                total_value = sum(opportunities[i]['expected_value'] * result.x[i] 
                                for i in range(n_opps))
                
                expected_roi = (total_value - total_investment) / max(total_investment, 1)
                
                return OptimizationResult(
                    selected_opportunities=selected,
                    expected_total_roi=expected_roi,
                    resource_allocation={'budget_used': total_investment},
                    optimization_method='linear_programming',
                    confidence_score=0.9,
                    improvement_over_baseline=0.0
                )
            else:
                # Fallback to greedy if LP fails
                return self._greedy_optimization(opportunities, constraints)
                
        except Exception as e:
            logger.warning(f"Linear programming failed: {e}, falling back to greedy")
            return self._greedy_optimization(opportunities, constraints)
    
    def _risk_adjusted_optimization(self, opportunities: List[Dict[str, Any]], 
                                  constraints: Dict[str, float]) -> OptimizationResult:
        """Risk-adjusted optimization using Sharpe ratio-like metric"""
        
        # Calculate risk-adjusted returns
        for opp in opportunities:
            risk_free_return = 0.03  # 3% risk-free rate
            excess_return = opp['roi_potential'] - risk_free_return
            risk_adjusted_metric = excess_return / max(opp['risk_score'], 0.1)
            opp['risk_adjusted_metric'] = risk_adjusted_metric
        
        # Sort by risk-adjusted metric
        sorted_opps = sorted(opportunities, key=lambda x: x['risk_adjusted_metric'], reverse=True)
        
        selected = []
        total_investment = 0
        total_expected_value = 0
        total_risk = 0
        budget = constraints.get('budget', float('inf'))
        max_risk = constraints.get('max_risk', 0.7)
        
        for opp in sorted_opps:
            new_total_investment = total_investment + opp['investment_required']
            new_total_risk = (total_risk * len(selected) + opp['risk_score']) / (len(selected) + 1)
            
            if new_total_investment <= budget and new_total_risk <= max_risk:
                selected.append(opp['id'])
                total_investment = new_total_investment
                total_expected_value += opp['expected_value']
                total_risk = new_total_risk
        
        expected_roi = (total_expected_value - total_investment) / max(total_investment, 1)
        
        return OptimizationResult(
            selected_opportunities=selected,
            expected_total_roi=expected_roi,
            resource_allocation={
                'budget_used': total_investment,
                'portfolio_risk': total_risk
            },
            optimization_method='risk_adjusted',
            confidence_score=0.85,
            improvement_over_baseline=0.0
        )
    
    def _portfolio_balanced_optimization(self, opportunities: List[Dict[str, Any]], 
                                       constraints: Dict[str, float]) -> OptimizationResult:
        """Balanced portfolio optimization considering diversification"""
        
        # Cluster opportunities for diversification
        features = []
        for opp in opportunities:
            features.append([
                opp['grant_amount'],
                opp['risk_score'],
                opp.get('strategic_alignment', 0.5),
                opp.get('timeline_days', 180)
            ])
        
        # Normalize features
        features_array = np.array(features)
        features_normalized = (features_array - features_array.mean(axis=0)) / features_array.std(axis=0)
        
        # Cluster into opportunity types
        n_clusters = min(5, len(opportunities) // 2)
        if n_clusters > 1:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(features_normalized)
        else:
            clusters = [0] * len(opportunities)
        
        # Add cluster information
        for i, opp in enumerate(opportunities):
            opp['cluster'] = clusters[i]
        
        # Select best opportunities from each cluster for diversification
        selected = []
        cluster_allocations = {}
        total_investment = 0
        total_expected_value = 0
        budget = constraints.get('budget', float('inf'))
        
        # Allocate budget across clusters
        unique_clusters = set(clusters)
        budget_per_cluster = budget / len(unique_clusters)
        
        for cluster_id in unique_clusters:
            cluster_opps = [opp for opp in opportunities if opp['cluster'] == cluster_id]
            cluster_opps.sort(key=lambda x: x['roi_potential'], reverse=True)
            
            cluster_investment = 0
            cluster_value = 0
            
            for opp in cluster_opps:
                if cluster_investment + opp['investment_required'] <= budget_per_cluster:
                    selected.append(opp['id'])
                    cluster_investment += opp['investment_required']
                    cluster_value += opp['expected_value']
            
            cluster_allocations[f'cluster_{cluster_id}'] = cluster_investment
            total_investment += cluster_investment
            total_expected_value += cluster_value
        
        # Calculate diversification score
        diversification_score = len(unique_clusters) / max(len(opportunities), 1)
        
        expected_roi = (total_expected_value - total_investment) / max(total_investment, 1)
        
        # Boost ROI score based on diversification
        diversification_bonus = diversification_score * 0.1
        adjusted_roi = expected_roi * (1 + diversification_bonus)
        
        return OptimizationResult(
            selected_opportunities=selected,
            expected_total_roi=adjusted_roi,
            resource_allocation={
                'budget_used': total_investment,
                'diversification_score': diversification_score,
                **cluster_allocations
            },
            optimization_method='portfolio_balanced',
            confidence_score=0.9,
            improvement_over_baseline=0.0
        )
    
    def _calculate_baseline_roi(self, opportunities: List[Dict[str, Any]], 
                              constraints: Dict[str, float]) -> float:
        """Calculate baseline ROI (random selection)"""
        
        np.random.seed(42)  # For reproducibility
        budget = constraints.get('budget', float('inf'))
        
        # Random selection
        shuffled_opps = opportunities.copy()
        np.random.shuffle(shuffled_opps)
        
        total_investment = 0
        total_expected_value = 0
        
        for opp in shuffled_opps:
            if total_investment + opp['investment_required'] <= budget:
                total_investment += opp['investment_required']
                total_expected_value += opp['expected_value']
        
        return (total_expected_value - total_investment) / max(total_investment, 1)
    
    def compare_optimization_methods(self, opportunities: List[Dict[str, Any]], 
                                   constraints: Dict[str, float]) -> Dict[str, OptimizationResult]:
        """Compare all optimization methods"""
        
        results = {}
        
        for method_name in self.optimization_methods.keys():
            try:
                result = self.optimize_portfolio(opportunities, constraints, method_name)
                results[method_name] = result
            except Exception as e:
                logger.error(f"Failed to run {method_name} optimization: {e}")
                continue
        
        return results
    
    def calculate_portfolio_metrics(self, opportunities: List[Dict[str, Any]], 
                                  selected_ids: List[str]) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics"""
        
        selected_opps = [opp for opp in opportunities if opp.get('id') in selected_ids]
        
        if not selected_opps:
            return PortfolioMetrics(0, 0, 0, 0, 0, 0)
        
        # Basic metrics
        total_expected_value = sum(opp['expected_value'] for opp in selected_opps)
        total_investment = sum(opp['investment_required'] for opp in selected_opps)
        portfolio_roi = (total_expected_value - total_investment) / max(total_investment, 1)
        
        # Risk score (weighted average)
        risk_scores = [opp['risk_score'] for opp in selected_opps]
        investments = [opp['investment_required'] for opp in selected_opps]
        weighted_risk = np.average(risk_scores, weights=investments) if investments else 0
        
        # Diversification index
        grant_amounts = [opp['grant_amount'] for opp in selected_opps]
        diversification_index = self._calculate_diversification_index(grant_amounts)
        
        # Time to completion (maximum timeline)
        timelines = [opp.get('timeline_days', 180) for opp in selected_opps]
        time_to_completion = max(timelines) if timelines else 0
        
        return PortfolioMetrics(
            total_expected_value=total_expected_value,
            total_investment=total_investment,
            portfolio_roi=portfolio_roi,
            risk_score=weighted_risk,
            diversification_index=diversification_index,
            time_to_completion=time_to_completion
        )
    
    def _calculate_diversification_index(self, values: List[float]) -> float:
        """Calculate Herfindahl-Hirschman Index for diversification"""
        if not values:
            return 0
        
        total = sum(values)
        if total == 0:
            return 0
        
        # Calculate market share squares
        shares = [(v / total) ** 2 for v in values]
        hhi = sum(shares)
        
        # Convert to diversification index (inverse of concentration)
        diversification = 1 - hhi
        
        return diversification
    
    def generate_optimization_recommendations(self, comparison_results: Dict[str, OptimizationResult], 
                                            opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate recommendations based on optimization comparison"""
        
        if not comparison_results:
            return {"error": "No optimization results available"}
        
        # Find best method
        best_method = max(comparison_results.items(), key=lambda x: x[1].expected_total_roi)
        
        # Calculate consensus selections (opportunities selected by multiple methods)
        all_selections = {}
        for method, result in comparison_results.items():
            for opp_id in result.selected_opportunities:
                all_selections[opp_id] = all_selections.get(opp_id, 0) + 1
        
        consensus_opportunities = [opp_id for opp_id, count in all_selections.items() 
                                 if count >= len(comparison_results) / 2]
        
        recommendations = {
            "best_method": {
                "method": best_method[0],
                "expected_roi": best_method[1].expected_total_roi,
                "selected_opportunities": best_method[1].selected_opportunities
            },
            "consensus_opportunities": consensus_opportunities,
            "method_comparison": {
                method: {
                    "roi": result.expected_total_roi,
                    "confidence": result.confidence_score,
                    "improvement": result.improvement_over_baseline
                }
                for method, result in comparison_results.items()
            },
            "recommendations": self._generate_actionable_recommendations(comparison_results, opportunities)
        }
        
        return recommendations
    
    def _generate_actionable_recommendations(self, results: Dict[str, OptimizationResult], 
                                           opportunities: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # ROI performance recommendations
        best_roi = max(result.expected_total_roi for result in results.values())
        if best_roi > 2.0:
            recommendations.append("Excellent optimization results - implement recommended portfolio")
        elif best_roi > 1.0:
            recommendations.append("Good optimization potential - proceed with selected opportunities")
        else:
            recommendations.append("Low ROI potential - review opportunity quality and selection criteria")
        
        # Method selection recommendations
        method_performances = [(method, result.expected_total_roi) for method, result in results.items()]
        method_performances.sort(key=lambda x: x[1], reverse=True)
        
        if method_performances[0][1] > method_performances[-1][1] * 1.2:
            recommendations.append(f"Use {method_performances[0][0]} method for best results")
        else:
            recommendations.append("Multiple methods show similar performance - use portfolio_balanced for stability")
        
        return recommendations

# Global ROI optimizer instance
roi_optimizer = ROIOptimizer()