#!/usr/bin/env python3
"""
Catalynx Success Scoring Algorithms
Multi-dimensional success scoring system with real-time updates
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass 
class SuccessScore:
    overall_score: float
    dimension_scores: Dict[str, float]
    confidence_level: float
    improvement_suggestions: List[str]
    score_breakdown: Dict[str, Any]
    last_updated: datetime

class SuccessScorer:
    """Advanced multi-dimensional success scoring system"""
    
    def __init__(self):
        # Scoring weights for different dimensions
        self.dimension_weights = {
            'financial_health': 0.25,
            'organizational_capacity': 0.20,
            'strategic_alignment': 0.20,
            'network_influence': 0.15,
            'track_record': 0.20
        }
        
        # Scoring algorithms for each dimension
        self.scorers = {
            'financial_health': self._score_financial_health,
            'organizational_capacity': self._score_organizational_capacity,
            'strategic_alignment': self._score_strategic_alignment,
            'network_influence': self._score_network_influence,
            'track_record': self._score_track_record
        }
    
    def calculate_success_score(self, organization_data: Dict[str, Any]) -> SuccessScore:
        """Calculate comprehensive success score"""
        dimension_scores = {}
        score_breakdown = {}
        
        # Calculate score for each dimension
        for dimension, weight in self.dimension_weights.items():
            if dimension in self.scorers:
                score, breakdown = self.scorers[dimension](organization_data)
                dimension_scores[dimension] = score
                score_breakdown[dimension] = breakdown
            else:
                dimension_scores[dimension] = 0.5  # Neutral score if no data
                score_breakdown[dimension] = {"error": "No scoring algorithm available"}
        
        # Calculate weighted overall score
        overall_score = sum(score * self.dimension_weights[dim] 
                          for dim, score in dimension_scores.items())
        
        # Calculate confidence level
        confidence_level = self._calculate_confidence(organization_data, dimension_scores)
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            dimension_scores, score_breakdown
        )
        
        return SuccessScore(
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            confidence_level=confidence_level,
            improvement_suggestions=improvement_suggestions,
            score_breakdown=score_breakdown,
            last_updated=datetime.now()
        )
    
    def _score_financial_health(self, data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Score financial health dimension"""
        breakdown = {}
        
        # Revenue metrics
        current_revenue = data.get('total_revenue', 0)
        previous_revenue = data.get('previous_revenue', current_revenue)
        revenue_growth = (current_revenue - previous_revenue) / max(previous_revenue, 1)
        
        # Revenue stability (variation over time)
        revenue_history = data.get('revenue_history', [current_revenue])
        revenue_stability = 1 - (np.std(revenue_history) / max(np.mean(revenue_history), 1))
        
        # Financial ratios
        assets = data.get('total_assets', current_revenue * 1.5)
        liabilities = data.get('total_liabilities', 0)
        equity_ratio = max(0, (assets - liabilities) / max(assets, 1))
        
        # Expense efficiency
        total_expenses = data.get('total_expenses', current_revenue * 0.8)
        expense_ratio = 1 - (total_expenses / max(current_revenue, 1))
        
        # Component scores
        growth_score = min(1.0, max(0, 0.5 + revenue_growth))
        stability_score = max(0, min(1.0, revenue_stability))
        equity_score = min(1.0, equity_ratio)
        efficiency_score = max(0, min(1.0, expense_ratio))
        
        # Size factor (logarithmic scaling)
        size_factor = min(1.0, np.log10(max(current_revenue, 1000)) / 7)  # Scale to $10M
        
        breakdown = {
            'revenue_growth': revenue_growth,
            'revenue_stability': revenue_stability,
            'equity_ratio': equity_ratio,
            'expense_efficiency': efficiency_score,
            'size_factor': size_factor,
            'growth_score': growth_score,
            'stability_score': stability_score,
            'equity_score': equity_score
        }
        
        # Weighted combination
        financial_score = (
            growth_score * 0.3 +
            stability_score * 0.25 +
            equity_score * 0.2 +
            efficiency_score * 0.15 +
            size_factor * 0.1
        )
        
        return min(1.0, financial_score), breakdown
    
    def _score_organizational_capacity(self, data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Score organizational capacity dimension"""
        breakdown = {}
        
        # Staff metrics
        staff_count = data.get('staff_count', 5)
        leadership_experience = data.get('avg_leadership_experience', 5)
        board_size = data.get('board_size', 7)
        
        # Experience and expertise
        years_active = data.get('years_active', 1)
        program_diversity = len(data.get('program_areas', ['general']))
        
        # Infrastructure scores
        staff_score = min(1.0, np.log10(max(staff_count, 1)) / 2)  # Scale to 100 staff
        experience_score = min(1.0, leadership_experience / 15)  # Scale to 15 years
        board_score = min(1.0, board_size / 15)  # Scale to 15 board members
        longevity_score = min(1.0, years_active / 20)  # Scale to 20 years
        diversity_score = min(1.0, program_diversity / 10)  # Scale to 10 programs
        
        breakdown = {
            'staff_count': staff_count,
            'leadership_experience': leadership_experience,
            'board_size': board_size,
            'years_active': years_active,
            'program_diversity': program_diversity,
            'staff_score': staff_score,
            'experience_score': experience_score,
            'board_score': board_score,
            'longevity_score': longevity_score,
            'diversity_score': diversity_score
        }
        
        capacity_score = (
            staff_score * 0.25 +
            experience_score * 0.25 +
            board_score * 0.2 +
            longevity_score * 0.2 +
            diversity_score * 0.1
        )
        
        return capacity_score, breakdown
    
    def _score_strategic_alignment(self, data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Score strategic alignment dimension"""
        breakdown = {}
        
        # Mission alignment score (would be calculated by ML model)
        mission_alignment = data.get('mission_alignment_score', 0.7)
        
        # Program fit
        program_areas = data.get('program_areas', [])
        target_areas = data.get('target_program_areas', [])
        program_overlap = len(set(program_areas) & set(target_areas)) / max(len(target_areas), 1) if target_areas else 0.5
        
        # Geographic alignment
        service_states = data.get('service_states', [])
        target_states = data.get('target_states', [])
        geographic_fit = len(set(service_states) & set(target_states)) / max(len(target_states), 1) if target_states else 0.5
        
        # Population alignment
        populations_served = data.get('populations_served', [])
        target_populations = data.get('target_populations', [])
        population_fit = len(set(populations_served) & set(target_populations)) / max(len(target_populations), 1) if target_populations else 0.5
        
        # Strategic focus score
        focus_areas = data.get('focus_areas', [])
        focus_clarity = min(1.0, len(focus_areas) / 5) if focus_areas else 0.3
        
        breakdown = {
            'mission_alignment': mission_alignment,
            'program_overlap': program_overlap,
            'geographic_fit': geographic_fit,
            'population_fit': population_fit,
            'focus_clarity': focus_clarity
        }
        
        alignment_score = (
            mission_alignment * 0.3 +
            program_overlap * 0.25 +
            geographic_fit * 0.2 +
            population_fit * 0.15 +
            focus_clarity * 0.1
        )
        
        return alignment_score, breakdown
    
    def _score_network_influence(self, data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Score network influence dimension"""
        breakdown = {}
        
        # Board connections
        board_connections = data.get('board_connections', 0)
        connection_score = min(1.0, board_connections / 20)  # Scale to 20 connections
        
        # Network centrality measures
        betweenness_centrality = data.get('betweenness_centrality', 0)
        closeness_centrality = data.get('closeness_centrality', 0)
        eigenvector_centrality = data.get('eigenvector_centrality', 0)
        
        # Partnership and collaboration
        partnerships = len(data.get('active_partnerships', []))
        partnership_score = min(1.0, partnerships / 15)  # Scale to 15 partnerships
        
        # Influence metrics
        media_mentions = data.get('media_mentions', 0)
        media_score = min(1.0, media_mentions / 50)  # Scale to 50 mentions
        
        # Awards and recognition
        awards = len(data.get('awards', []))
        recognition_score = min(1.0, awards / 10)  # Scale to 10 awards
        
        breakdown = {
            'board_connections': board_connections,
            'betweenness_centrality': betweenness_centrality,
            'closeness_centrality': closeness_centrality,
            'eigenvector_centrality': eigenvector_centrality,
            'partnerships': partnerships,
            'media_mentions': media_mentions,
            'awards': awards,
            'connection_score': connection_score,
            'partnership_score': partnership_score,
            'media_score': media_score,
            'recognition_score': recognition_score
        }
        
        network_score = (
            connection_score * 0.25 +
            (betweenness_centrality + closeness_centrality + eigenvector_centrality) / 3 * 0.3 +
            partnership_score * 0.2 +
            media_score * 0.15 +
            recognition_score * 0.1
        )
        
        return network_score, breakdown
    
    def _score_track_record(self, data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Score track record dimension"""
        breakdown = {}
        
        # Grant history
        total_grants = data.get('total_grants_received', 0)
        successful_grants = data.get('successful_grants', total_grants)
        success_rate = successful_grants / max(total_grants, 1)
        
        # Grant amounts
        total_funding = data.get('total_funding_received', 0)
        avg_grant_size = total_funding / max(total_grants, 1)
        
        # Project completion
        completed_projects = data.get('completed_projects', 0)
        total_projects = data.get('total_projects', completed_projects)
        completion_rate = completed_projects / max(total_projects, 1)
        
        # Time performance
        on_time_completions = data.get('on_time_completions', completed_projects)
        timeliness_rate = on_time_completions / max(completed_projects, 1)
        
        # Impact metrics
        people_served = data.get('people_served', 0)
        impact_score = min(1.0, np.log10(max(people_served, 1)) / 6)  # Scale to 1M people
        
        # Component scores
        success_score_component = success_rate
        funding_score = min(1.0, np.log10(max(total_funding, 1000)) / 7)  # Scale to $10M
        completion_score = completion_rate
        timeliness_score = timeliness_rate
        
        breakdown = {
            'total_grants': total_grants,
            'success_rate': success_rate,
            'total_funding': total_funding,
            'avg_grant_size': avg_grant_size,
            'completion_rate': completion_rate,
            'timeliness_rate': timeliness_rate,
            'people_served': people_served,
            'impact_score': impact_score,
            'funding_score': funding_score
        }
        
        track_record_score = (
            success_score_component * 0.3 +
            completion_score * 0.25 +
            timeliness_score * 0.2 +
            funding_score * 0.15 +
            impact_score * 0.1
        )
        
        return track_record_score, breakdown
    
    def _calculate_confidence(self, data: Dict[str, Any], dimension_scores: Dict[str, float]) -> float:
        """Calculate confidence in the overall score"""
        confidence_factors = []
        
        # Data completeness
        required_fields = [
            'total_revenue', 'staff_count', 'years_active', 'program_areas',
            'total_grants_received', 'successful_grants'
        ]
        available_fields = sum(1 for field in required_fields if field in data and data[field] is not None)
        completeness = available_fields / len(required_fields)
        confidence_factors.append(completeness * 0.4)
        
        # Score consistency (low variance indicates reliable data)
        score_variance = np.var(list(dimension_scores.values()))
        consistency = 1 - min(1.0, score_variance * 4)  # Scale variance
        confidence_factors.append(consistency * 0.3)
        
        # Data recency
        last_updated = data.get('last_financial_report', '2023-01-01')
        try:
            update_date = datetime.fromisoformat(last_updated)
            days_old = (datetime.now() - update_date).days
            recency = max(0, 1 - days_old / 365)  # Decay over a year
        except Exception as e:

            logger.error(f"Unexpected error: {e}")
            recency = 0.5
        confidence_factors.append(recency * 0.3)
        
        return sum(confidence_factors)
    
    def _generate_improvement_suggestions(self, dimension_scores: Dict[str, float], 
                                        score_breakdown: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate actionable improvement suggestions"""
        suggestions = []
        
        # Sort dimensions by score (lowest first)
        sorted_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1])
        
        for dimension, score in sorted_dimensions[:3]:  # Focus on bottom 3
            if score < 0.6:  # Only suggest improvements for low scores
                dimension_suggestions = self._get_dimension_suggestions(dimension, score_breakdown.get(dimension, {}))
                suggestions.extend(dimension_suggestions[:2])  # Limit suggestions per dimension
        
        return suggestions[:5]  # Limit total suggestions
    
    def _get_dimension_suggestions(self, dimension: str, breakdown: Dict[str, Any]) -> List[str]:
        """Get specific suggestions for a dimension"""
        suggestions = []
        
        if dimension == 'financial_health':
            if breakdown.get('growth_score', 1) < 0.5:
                suggestions.append("Focus on revenue growth strategies and new funding sources")
            if breakdown.get('stability_score', 1) < 0.5:
                suggestions.append("Improve financial stability through diversified revenue streams")
            if breakdown.get('efficiency_score', 1) < 0.5:
                suggestions.append("Optimize operational expenses to improve financial efficiency")
        
        elif dimension == 'organizational_capacity':
            if breakdown.get('staff_score', 1) < 0.5:
                suggestions.append("Consider expanding staff to support organizational growth")
            if breakdown.get('experience_score', 1) < 0.5:
                suggestions.append("Invest in leadership development and experienced hires")
            if breakdown.get('board_score', 1) < 0.5:
                suggestions.append("Strengthen board governance with additional qualified members")
        
        elif dimension == 'strategic_alignment':
            if breakdown.get('mission_alignment', 1) < 0.6:
                suggestions.append("Refine mission statement to better align with target opportunities")
            if breakdown.get('program_overlap', 1) < 0.5:
                suggestions.append("Develop programs that better match target funding areas")
        
        elif dimension == 'network_influence':
            if breakdown.get('connection_score', 1) < 0.5:
                suggestions.append("Build strategic board connections and partnerships")
            if breakdown.get('partnership_score', 1) < 0.5:
                suggestions.append("Develop collaborative partnerships with peer organizations")
        
        elif dimension == 'track_record':
            if breakdown.get('success_rate', 1) < 0.7:
                suggestions.append("Improve grant application quality and project management")
            if breakdown.get('completion_rate', 1) < 0.8:
                suggestions.append("Strengthen project management processes for better completion rates")
        
        return suggestions

# Global success scorer instance
success_scorer = SuccessScorer()