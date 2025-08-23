"""
PHASE 6: Interactive Decision Support Tools
Advanced interactive tools for decision-making with scenario analysis,
sensitivity testing, decision trees, and collaborative features.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
import numpy as np
from collections import defaultdict
import uuid

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult
from src.decision.decision_synthesis_framework import (
    DecisionRecommendation, DecisionConfidence, RecommendationType,
    IntegratedScore, FeasibilityAssessment, ResourceAllocation
)

logger = logging.getLogger(__name__)

class DecisionSupportMode(Enum):
    """Decision support interaction modes"""
    GUIDED_ANALYSIS = "guided"         # Step-by-step guided decision process
    EXPLORATORY = "exploratory"       # Free-form exploration and comparison
    COLLABORATIVE = "collaborative"   # Multi-user collaborative decision making
    SCENARIO_TESTING = "scenario"     # What-if scenario analysis
    SENSITIVITY_ANALYSIS = "sensitivity"  # Parameter sensitivity testing

class InteractionType(Enum):
    """Types of decision support interactions"""
    PARAMETER_ADJUSTMENT = "parameter_adjust"
    SCENARIO_COMPARISON = "scenario_compare"
    CONSTRAINT_MODIFICATION = "constraint_modify"
    PREFERENCE_WEIGHTING = "preference_weight"
    RISK_TOLERANCE_SETTING = "risk_tolerance"
    TIMELINE_ADJUSTMENT = "timeline_adjust"
    RESOURCE_REALLOCATION = "resource_realloc"

class DecisionStageType(Enum):
    """Decision process stages"""
    OPPORTUNITY_REVIEW = "review"
    CRITERIA_DEFINITION = "criteria"
    ANALYSIS_PARAMETERS = "parameters"
    SCENARIO_EXPLORATION = "scenarios"
    RISK_ASSESSMENT = "risk"
    FINAL_DECISION = "decision"
    IMPLEMENTATION_PLANNING = "implementation"

@dataclass
class DecisionParameter:
    """Individual parameter for decision analysis"""
    parameter_id: str
    name: str
    description: str
    parameter_type: str               # 'numeric', 'categorical', 'boolean', 'range'
    current_value: Any
    default_value: Any
    
    # Constraints and validation
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    validation_rules: List[str] = field(default_factory=list)
    
    # UI configuration
    input_type: str = 'slider'        # 'slider', 'input', 'dropdown', 'checkbox', 'range'
    display_format: str = '{:.2f}'    # Format for display
    help_text: str = ''               # Additional help text
    
    # Impact tracking
    sensitivity_score: float = 0.0    # How sensitive final decision is to this parameter
    last_modified: datetime = field(default_factory=datetime.now)
    modification_count: int = 0

@dataclass
class DecisionScenario:
    """Complete decision scenario with parameters and results"""
    scenario_id: str
    name: str
    description: str
    created_by: str
    created_at: datetime = field(default_factory=datetime.now)
    
    # Parameter settings
    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, float] = field(default_factory=dict)
    
    # Scenario results
    results: Optional[Dict[str, Any]] = None
    recommendations: List[DecisionRecommendation] = field(default_factory=list)
    
    # Scenario metadata
    is_baseline: bool = False
    parent_scenario_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    notes: str = ''

@dataclass
class SensitivityAnalysis:
    """Sensitivity analysis results for decision parameters"""
    parameter_id: str
    parameter_name: str
    
    # Sensitivity metrics
    impact_score: float               # Overall impact on final decision (0-1)
    variance_contribution: float      # Contribution to decision variance
    elasticity: float                # Elasticity of decision to parameter changes
    
    # Parameter sweep results
    parameter_values: List[float]     # Parameter values tested
    decision_outcomes: List[Any]      # Resulting decision outcomes
    score_variations: List[float]     # Score variations across parameter range
    
    # Critical thresholds
    decision_thresholds: Dict[str, float]  # Parameter values that change decisions
    stability_ranges: List[Tuple[float, float]]  # Ranges where decision is stable
    
    # Visualization data
    visualization_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CollaborativeSession:
    """Collaborative decision-making session"""
    session_id: str
    session_name: str
    created_by: str
    created_at: datetime = field(default_factory=datetime.now)
    
    # Participants
    participants: List[str] = field(default_factory=list)
    current_participants: List[str] = field(default_factory=list)
    
    # Session state
    current_stage: DecisionStageType = DecisionStageType.OPPORTUNITY_REVIEW
    shared_scenarios: List[str] = field(default_factory=list)  # Scenario IDs
    
    # Collaboration features
    comments: List[Dict[str, Any]] = field(default_factory=list)
    votes: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # {scenario_id: {participant: vote}}
    consensus_threshold: float = 0.75
    
    # Session settings
    allow_anonymous_participation: bool = False
    require_justification: bool = True
    auto_save_interval: int = 30  # seconds
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class ParameterManager:
    """Manager for decision parameters and their interactions"""
    
    def __init__(self):
        self.parameter_definitions = {}
        self.parameter_dependencies = {}
        self.validation_rules = {}
    
    def register_parameter(self, parameter: DecisionParameter) -> None:
        """Register a new decision parameter"""
        self.parameter_definitions[parameter.parameter_id] = parameter
        logger.info(f"Registered parameter: {parameter.name}")
    
    def create_standard_parameters(self) -> Dict[str, DecisionParameter]:
        """Create standard decision parameters"""
        
        parameters = {}
        
        # Score weighting parameters
        parameters['government_score_weight'] = DecisionParameter(
            parameter_id='government_score_weight',
            name='Government Score Weight',
            description='Weight given to government opportunity scoring',
            parameter_type='numeric',
            current_value=0.25,
            default_value=0.25,
            min_value=0.0,
            max_value=1.0,
            input_type='slider',
            display_format='{:.2f}',
            help_text='How much to weight government scoring in final decision'
        )
        
        parameters['feasibility_weight'] = DecisionParameter(
            parameter_id='feasibility_weight',
            name='Feasibility Weight',
            description='Weight given to feasibility assessment',
            parameter_type='numeric',
            current_value=0.4,
            default_value=0.4,
            min_value=0.0,
            max_value=1.0,
            input_type='slider',
            display_format='{:.2f}',
            help_text='How much to weight feasibility in final decision'
        )
        
        parameters['risk_tolerance'] = DecisionParameter(
            parameter_id='risk_tolerance',
            name='Risk Tolerance',
            description='Organizational risk tolerance level',
            parameter_type='numeric',
            current_value=0.6,
            default_value=0.6,
            min_value=0.0,
            max_value=1.0,
            input_type='slider',
            display_format='{:.1%}',
            help_text='Higher values indicate greater willingness to take risks'
        )
        
        parameters['minimum_score_threshold'] = DecisionParameter(
            parameter_id='minimum_score_threshold',
            name='Minimum Score Threshold',
            description='Minimum integrated score for consideration',
            parameter_type='numeric',
            current_value=0.5,
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            input_type='slider',
            display_format='{:.2f}',
            help_text='Opportunities below this score will not be recommended'
        )
        
        parameters['resource_constraint_factor'] = DecisionParameter(
            parameter_id='resource_constraint_factor',
            name='Resource Constraint Factor',
            description='Factor reflecting current resource constraints',
            parameter_type='numeric',
            current_value=1.0,
            default_value=1.0,
            min_value=0.1,
            max_value=2.0,
            input_type='slider',
            display_format='{:.1f}x',
            help_text='1.0 = normal capacity, <1.0 = constrained, >1.0 = expanded capacity'
        )
        
        parameters['strategic_alignment_weight'] = DecisionParameter(
            parameter_id='strategic_alignment_weight',
            name='Strategic Alignment Weight',
            description='Importance of strategic alignment with mission',
            parameter_type='numeric',
            current_value=0.3,
            default_value=0.3,
            min_value=0.0,
            max_value=1.0,
            input_type='slider',
            display_format='{:.2f}',
            help_text='Weight given to strategic mission alignment'
        )
        
        # Categorical parameters
        parameters['decision_timeline'] = DecisionParameter(
            parameter_id='decision_timeline',
            name='Decision Timeline',
            description='Timeline pressure for decision making',
            parameter_type='categorical',
            current_value='moderate',
            default_value='moderate',
            allowed_values=['urgent', 'moderate', 'flexible'],
            input_type='dropdown',
            help_text='Urgency of decision timeline'
        )
        
        parameters['confidence_requirement'] = DecisionParameter(
            parameter_id='confidence_requirement',
            name='Confidence Requirement',
            description='Required confidence level for recommendations',
            parameter_type='categorical',
            current_value='medium',
            default_value='medium',
            allowed_values=['low', 'medium', 'high', 'very_high'],
            input_type='dropdown',
            help_text='Minimum confidence level required for positive recommendations'
        )
        
        # Register all parameters
        for param in parameters.values():
            self.register_parameter(param)
        
        return parameters
    
    def validate_parameter_value(self, parameter_id: str, value: Any) -> Tuple[bool, str]:
        """Validate a parameter value against its constraints"""
        
        if parameter_id not in self.parameter_definitions:
            return False, f"Unknown parameter: {parameter_id}"
        
        param = self.parameter_definitions[parameter_id]
        
        # Type validation
        if param.parameter_type == 'numeric':
            try:
                value = float(value)
                if param.min_value is not None and value < param.min_value:
                    return False, f"Value {value} below minimum {param.min_value}"
                if param.max_value is not None and value > param.max_value:
                    return False, f"Value {value} above maximum {param.max_value}"
            except (ValueError, TypeError):
                return False, f"Invalid numeric value: {value}"
        
        elif param.parameter_type == 'categorical':
            if param.allowed_values and value not in param.allowed_values:
                return False, f"Value {value} not in allowed values: {param.allowed_values}"
        
        elif param.parameter_type == 'boolean':
            if not isinstance(value, bool):
                return False, f"Invalid boolean value: {value}"
        
        return True, "Valid"
    
    def update_parameter(self, parameter_id: str, new_value: Any) -> bool:
        """Update parameter value with validation"""
        
        is_valid, message = self.validate_parameter_value(parameter_id, new_value)
        if not is_valid:
            logger.warning(f"Invalid parameter update: {message}")
            return False
        
        if parameter_id in self.parameter_definitions:
            param = self.parameter_definitions[parameter_id]
            param.current_value = new_value
            param.last_modified = datetime.now()
            param.modification_count += 1
            logger.info(f"Updated parameter {parameter_id} to {new_value}")
            return True
        
        return False

class ScenarioEngine:
    """Engine for managing and comparing decision scenarios"""
    
    def __init__(self, parameter_manager: ParameterManager):
        self.parameter_manager = parameter_manager
        self.scenarios = {}
        self.baseline_scenario_id = None
    
    async def create_scenario(self, 
                            name: str, 
                            description: str,
                            created_by: str,
                            parameters: Optional[Dict[str, Any]] = None,
                            is_baseline: bool = False) -> DecisionScenario:
        """Create a new decision scenario"""
        
        scenario_id = str(uuid.uuid4())
        
        # Use current parameter values if not specified
        if parameters is None:
            parameters = {
                param_id: param.current_value 
                for param_id, param in self.parameter_manager.parameter_definitions.items()
            }
        
        scenario = DecisionScenario(
            scenario_id=scenario_id,
            name=name,
            description=description,
            created_by=created_by,
            parameters=parameters,
            is_baseline=is_baseline
        )
        
        self.scenarios[scenario_id] = scenario
        
        if is_baseline:
            self.baseline_scenario_id = scenario_id
        
        logger.info(f"Created scenario: {name} (ID: {scenario_id})")
        return scenario
    
    async def clone_scenario(self, 
                           source_scenario_id: str,
                           new_name: str,
                           created_by: str,
                           parameter_modifications: Optional[Dict[str, Any]] = None) -> DecisionScenario:
        """Clone an existing scenario with optional modifications"""
        
        if source_scenario_id not in self.scenarios:
            raise ValueError(f"Source scenario not found: {source_scenario_id}")
        
        source_scenario = self.scenarios[source_scenario_id]
        
        # Copy parameters from source
        new_parameters = source_scenario.parameters.copy()
        
        # Apply modifications
        if parameter_modifications:
            new_parameters.update(parameter_modifications)
        
        # Create cloned scenario
        cloned_scenario = await self.create_scenario(
            name=new_name,
            description=f"Cloned from: {source_scenario.name}",
            created_by=created_by,
            parameters=new_parameters
        )
        
        cloned_scenario.parent_scenario_id = source_scenario_id
        
        return cloned_scenario
    
    async def run_scenario_analysis(self, 
                                  scenario_id: str,
                                  opportunities: List[Dict[str, Any]],
                                  organizational_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Run decision analysis for a specific scenario"""
        
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario not found: {scenario_id}")
        
        scenario = self.scenarios[scenario_id]
        
        # Apply scenario parameters to decision framework
        # This would integrate with the DecisionSynthesisFramework
        # For now, we'll simulate the analysis
        
        results = {
            'scenario_id': scenario_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'parameter_settings': scenario.parameters,
            'opportunities_analyzed': len(opportunities),
            'recommendations': [],
            'summary_metrics': {
                'high_priority_count': 0,
                'medium_priority_count': 0,
                'low_priority_count': 0,
                'average_confidence': 0.0,
                'total_resource_requirements': 0.0
            }
        }
        
        # Store results in scenario
        scenario.results = results
        
        logger.info(f"Completed analysis for scenario: {scenario.name}")
        return results
    
    async def compare_scenarios(self, scenario_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple scenarios and their results"""
        
        if not all(sid in self.scenarios for sid in scenario_ids):
            missing = [sid for sid in scenario_ids if sid not in self.scenarios]
            raise ValueError(f"Scenarios not found: {missing}")
        
        scenarios = [self.scenarios[sid] for sid in scenario_ids]
        comparison = {
            'comparison_id': str(uuid.uuid4()),
            'compared_scenarios': scenario_ids,
            'comparison_timestamp': datetime.now().isoformat(),
            'parameter_differences': {},
            'result_differences': {},
            'recommendations': []
        }
        
        # Compare parameters across scenarios
        all_params = set()
        for scenario in scenarios:
            all_params.update(scenario.parameters.keys())
        
        param_comparison = {}
        for param in all_params:
            param_values = {}
            for scenario in scenarios:
                param_values[scenario.scenario_id] = scenario.parameters.get(param, None)
            
            # Check if parameter varies across scenarios
            unique_values = set(v for v in param_values.values() if v is not None)
            if len(unique_values) > 1:
                param_comparison[param] = {
                    'varies': True,
                    'values': param_values,
                    'range': max(unique_values) - min(unique_values) if all(isinstance(v, (int, float)) for v in unique_values) else None
                }
            else:
                param_comparison[param] = {'varies': False, 'common_value': list(unique_values)[0] if unique_values else None}
        
        comparison['parameter_differences'] = param_comparison
        
        # Compare results if available
        if all(s.results for s in scenarios):
            result_comparison = self._compare_scenario_results([s.results for s in scenarios])
            comparison['result_differences'] = result_comparison
        
        # Generate comparison recommendations
        comparison['recommendations'] = await self._generate_scenario_recommendations(scenarios)
        
        return comparison
    
    def _compare_scenario_results(self, results_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare results across scenarios"""
        
        comparison = {
            'metric_comparisons': {},
            'ranking_changes': {},
            'decision_stability': {}
        }
        
        # Compare summary metrics
        metrics_to_compare = ['high_priority_count', 'average_confidence', 'total_resource_requirements']
        
        for metric in metrics_to_compare:
            values = [r['summary_metrics'].get(metric, 0) for r in results_list]
            comparison['metric_comparisons'][metric] = {
                'values': values,
                'min': min(values) if values else 0,
                'max': max(values) if values else 0,
                'variance': np.var(values) if values else 0,
                'coefficient_of_variation': np.std(values) / np.mean(values) if values and np.mean(values) != 0 else 0
            }
        
        return comparison
    
    async def _generate_scenario_recommendations(self, scenarios: List[DecisionScenario]) -> List[str]:
        """Generate recommendations based on scenario comparison"""
        
        recommendations = []
        
        if len(scenarios) < 2:
            recommendations.append("Need at least 2 scenarios for meaningful comparison")
            return recommendations
        
        # Find baseline scenario
        baseline = next((s for s in scenarios if s.is_baseline), scenarios[0])
        
        # Compare each scenario to baseline
        for scenario in scenarios:
            if scenario.scenario_id == baseline.scenario_id:
                continue
            
            if scenario.results and baseline.results:
                baseline_confidence = baseline.results['summary_metrics'].get('average_confidence', 0)
                scenario_confidence = scenario.results['summary_metrics'].get('average_confidence', 0)
                
                if scenario_confidence > baseline_confidence * 1.1:
                    recommendations.append(f"Scenario '{scenario.name}' shows significantly higher confidence than baseline")
                elif scenario_confidence < baseline_confidence * 0.9:
                    recommendations.append(f"Scenario '{scenario.name}' shows lower confidence than baseline")
        
        # Parameter sensitivity insights
        varying_params = []
        if len(scenarios) > 1:
            all_params = set()
            for scenario in scenarios:
                all_params.update(scenario.parameters.keys())
            
            for param in all_params:
                values = [s.parameters.get(param) for s in scenarios]
                if len(set(values)) > 1:
                    varying_params.append(param)
        
        if varying_params:
            recommendations.append(f"Key varying parameters: {', '.join(varying_params[:3])}")
        
        return recommendations

class SensitivityAnalysisEngine:
    """Engine for parameter sensitivity analysis"""
    
    def __init__(self, parameter_manager: ParameterManager, scenario_engine: ScenarioEngine):
        self.parameter_manager = parameter_manager
        self.scenario_engine = scenario_engine
    
    async def analyze_parameter_sensitivity(self,
                                          parameter_id: str,
                                          baseline_scenario_id: str,
                                          opportunities: List[Dict[str, Any]],
                                          organizational_profile: Dict[str, Any],
                                          num_samples: int = 10) -> SensitivityAnalysis:
        """Analyze sensitivity of decisions to parameter changes"""
        
        if parameter_id not in self.parameter_manager.parameter_definitions:
            raise ValueError(f"Parameter not found: {parameter_id}")
        
        param = self.parameter_manager.parameter_definitions[parameter_id]
        baseline_scenario = self.scenario_engine.scenarios[baseline_scenario_id]
        
        # Generate parameter value range
        if param.parameter_type == 'numeric':
            if param.min_value is not None and param.max_value is not None:
                parameter_values = np.linspace(param.min_value, param.max_value, num_samples)
            else:
                # Use ±50% of current value
                current = param.current_value
                parameter_values = np.linspace(current * 0.5, current * 1.5, num_samples)
        else:
            # For categorical parameters, use all allowed values
            parameter_values = param.allowed_values or [param.current_value]
        
        # Run analysis for each parameter value
        decision_outcomes = []
        score_variations = []
        scenario_results = []
        
        for param_value in parameter_values:
            # Create temporary scenario with modified parameter
            temp_params = baseline_scenario.parameters.copy()
            temp_params[parameter_id] = param_value
            
            temp_scenario = await self.scenario_engine.create_scenario(
                name=f"Sensitivity_{parameter_id}_{param_value}",
                description=f"Sensitivity test for {parameter_id}",
                created_by="sensitivity_analysis",
                parameters=temp_params
            )
            
            # Run analysis
            results = await self.scenario_engine.run_scenario_analysis(
                temp_scenario.scenario_id, opportunities, organizational_profile
            )
            
            scenario_results.append(results)
            
            # Extract key decision metrics
            avg_confidence = results['summary_metrics'].get('average_confidence', 0)
            high_priority_count = results['summary_metrics'].get('high_priority_count', 0)
            
            decision_outcomes.append({
                'parameter_value': param_value,
                'average_confidence': avg_confidence,
                'high_priority_count': high_priority_count,
                'total_opportunities': results['opportunities_analyzed']
            })
            
            score_variations.append(avg_confidence)
        
        # Calculate sensitivity metrics
        impact_score = self._calculate_impact_score(score_variations)
        variance_contribution = np.var(score_variations)
        elasticity = self._calculate_elasticity(parameter_values, score_variations)
        
        # Find decision thresholds
        decision_thresholds = self._find_decision_thresholds(decision_outcomes)
        
        # Find stability ranges
        stability_ranges = self._find_stability_ranges(decision_outcomes)
        
        # Generate visualization data
        visualization_data = {
            'sensitivity_curve': {
                'x': parameter_values.tolist() if hasattr(parameter_values, 'tolist') else list(parameter_values),
                'y': score_variations,
                'type': 'line'
            },
            'decision_distribution': {
                'parameter_values': parameter_values.tolist() if hasattr(parameter_values, 'tolist') else list(parameter_values),
                'outcomes': decision_outcomes
            }
        }
        
        return SensitivityAnalysis(
            parameter_id=parameter_id,
            parameter_name=param.name,
            impact_score=impact_score,
            variance_contribution=variance_contribution,
            elasticity=elasticity,
            parameter_values=parameter_values.tolist() if hasattr(parameter_values, 'tolist') else list(parameter_values),
            decision_outcomes=decision_outcomes,
            score_variations=score_variations,
            decision_thresholds=decision_thresholds,
            stability_ranges=stability_ranges,
            visualization_data=visualization_data
        )
    
    def _calculate_impact_score(self, score_variations: List[float]) -> float:
        """Calculate overall impact score based on score variations"""
        if len(score_variations) < 2:
            return 0.0
        
        score_range = max(score_variations) - min(score_variations)
        normalized_impact = min(1.0, score_range / 1.0)  # Normalize to 0-1 scale
        
        return normalized_impact
    
    def _calculate_elasticity(self, parameter_values: List[float], score_variations: List[float]) -> float:
        """Calculate elasticity of decision scores to parameter changes"""
        if len(parameter_values) < 2 or len(score_variations) < 2:
            return 0.0
        
        # Simple elasticity calculation using percentage changes
        try:
            param_change = (parameter_values[-1] - parameter_values[0]) / parameter_values[0]
            score_change = (score_variations[-1] - score_variations[0]) / score_variations[0]
            
            if param_change != 0:
                elasticity = score_change / param_change
                return abs(elasticity)  # Return absolute elasticity
        except (ZeroDivisionError, IndexError):
            pass
        
        return 0.0
    
    def _find_decision_thresholds(self, decision_outcomes: List[Dict[str, Any]]) -> Dict[str, float]:
        """Find parameter values that cause significant decision changes"""
        
        thresholds = {}
        
        if len(decision_outcomes) < 2:
            return thresholds
        
        # Look for changes in high priority count
        for i in range(1, len(decision_outcomes)):
            prev_count = decision_outcomes[i-1]['high_priority_count']
            curr_count = decision_outcomes[i]['high_priority_count']
            
            if prev_count != curr_count:
                param_value = decision_outcomes[i]['parameter_value']
                thresholds[f'priority_change_{i}'] = param_value
        
        # Look for significant confidence changes (>10%)
        for i in range(1, len(decision_outcomes)):
            prev_conf = decision_outcomes[i-1]['average_confidence']
            curr_conf = decision_outcomes[i]['average_confidence']
            
            if abs(curr_conf - prev_conf) > 0.1:
                param_value = decision_outcomes[i]['parameter_value']
                thresholds[f'confidence_change_{i}'] = param_value
        
        return thresholds
    
    def _find_stability_ranges(self, decision_outcomes: List[Dict[str, Any]]) -> List[Tuple[float, float]]:
        """Find parameter ranges where decisions remain stable"""
        
        stability_ranges = []
        
        if len(decision_outcomes) < 3:
            return stability_ranges
        
        # Find ranges where high priority count remains constant
        current_count = decision_outcomes[0]['high_priority_count']
        range_start = decision_outcomes[0]['parameter_value']
        
        for i in range(1, len(decision_outcomes)):
            if decision_outcomes[i]['high_priority_count'] != current_count:
                # End of stable range
                range_end = decision_outcomes[i-1]['parameter_value']
                if range_end != range_start:
                    stability_ranges.append((range_start, range_end))
                
                # Start new range
                current_count = decision_outcomes[i]['high_priority_count']
                range_start = decision_outcomes[i]['parameter_value']
        
        # Add final range if it exists
        if range_start != decision_outcomes[-1]['parameter_value']:
            stability_ranges.append((range_start, decision_outcomes[-1]['parameter_value']))
        
        return stability_ranges
    
    async def analyze_multi_parameter_sensitivity(self,
                                                parameter_ids: List[str],
                                                baseline_scenario_id: str,
                                                opportunities: List[Dict[str, Any]],
                                                organizational_profile: Dict[str, Any],
                                                num_samples_per_param: int = 5) -> Dict[str, Any]:
        """Analyze sensitivity across multiple parameters simultaneously"""
        
        individual_analyses = {}
        
        # Run individual sensitivity analysis for each parameter
        for param_id in parameter_ids:
            try:
                analysis = await self.analyze_parameter_sensitivity(
                    param_id, baseline_scenario_id, opportunities, 
                    organizational_profile, num_samples_per_param
                )
                individual_analyses[param_id] = analysis
            except Exception as e:
                logger.error(f"Error in sensitivity analysis for {param_id}: {e}")
                continue
        
        # Rank parameters by impact
        parameter_rankings = sorted(
            individual_analyses.items(),
            key=lambda x: x[1].impact_score,
            reverse=True
        )
        
        # Calculate interaction effects (simplified)
        interaction_effects = {}
        if len(parameter_ids) >= 2:
            for i in range(len(parameter_ids)):
                for j in range(i+1, len(parameter_ids)):
                    param1_id = parameter_ids[i]
                    param2_id = parameter_ids[j]
                    
                    if param1_id in individual_analyses and param2_id in individual_analyses:
                        # Simple interaction score based on combined variance
                        param1_variance = individual_analyses[param1_id].variance_contribution
                        param2_variance = individual_analyses[param2_id].variance_contribution
                        
                        interaction_score = min(param1_variance, param2_variance) * 0.5
                        interaction_effects[f"{param1_id}_{param2_id}"] = interaction_score
        
        return {
            'individual_analyses': {k: self._serialize_sensitivity_analysis(v) for k, v in individual_analyses.items()},
            'parameter_rankings': [(param_id, analysis.impact_score) for param_id, analysis in parameter_rankings],
            'interaction_effects': interaction_effects,
            'summary': {
                'most_influential_parameter': parameter_rankings[0][0] if parameter_rankings else None,
                'total_parameters_analyzed': len(individual_analyses),
                'high_impact_parameters': [param_id for param_id, analysis in parameter_rankings if analysis.impact_score > 0.3],
                'stability_assessment': 'stable' if all(a.impact_score < 0.2 for a in individual_analyses.values()) else 'sensitive'
            }
        }
    
    def _serialize_sensitivity_analysis(self, analysis: SensitivityAnalysis) -> Dict[str, Any]:
        """Serialize sensitivity analysis for JSON output"""
        return {
            'parameter_id': analysis.parameter_id,
            'parameter_name': analysis.parameter_name,
            'impact_score': analysis.impact_score,
            'variance_contribution': analysis.variance_contribution,
            'elasticity': analysis.elasticity,
            'decision_thresholds_count': len(analysis.decision_thresholds),
            'stability_ranges_count': len(analysis.stability_ranges),
            'visualization_data': analysis.visualization_data
        }

class InteractiveDecisionSupportTools(BaseProcessor):
    """Main interactive decision support tools framework"""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="interactive_decision_support_tools",
            description="Interactive decision support tools with parameter management and scenario analysis",
            version="1.0.0",
            dependencies=[],
            estimated_duration=30,
            requires_network=False,
            requires_api_key=False,
            can_run_parallel=True,
            processor_type="analysis"
        )
        super().__init__(metadata)
        self.parameter_manager = ParameterManager()
        self.scenario_engine = ScenarioEngine(self.parameter_manager)
        self.sensitivity_engine = SensitivityAnalysisEngine(self.parameter_manager, self.scenario_engine)
        
        # Initialize standard parameters
        self.parameter_manager.create_standard_parameters()
        
        # Collaborative sessions
        self.collaborative_sessions = {}
    
    async def process(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Main processing method for interactive decision support"""
        try:
            logger.info(f"Starting interactive decision support for profile {profile_id}")
            
            mode = kwargs.get('mode', DecisionSupportMode.EXPLORATORY.value)
            interaction_type = kwargs.get('interaction_type', InteractionType.PARAMETER_ADJUSTMENT.value)
            
            # Get opportunities and profile data
            opportunities = kwargs.get('opportunities', [])
            organizational_profile = kwargs.get('organizational_profile', {})
            
            if not opportunities:
                return {
                    'profile_id': profile_id,
                    'mode': mode,
                    'message': 'No opportunities available for interactive analysis',
                    'available_tools': self._get_available_tools()
                }
            
            # Route to appropriate tool based on interaction type
            if interaction_type == InteractionType.PARAMETER_ADJUSTMENT.value:
                result = await self._handle_parameter_adjustment(profile_id, opportunities, **kwargs)
            elif interaction_type == InteractionType.SCENARIO_COMPARISON.value:
                result = await self._handle_scenario_comparison(profile_id, opportunities, **kwargs)
            elif interaction_type == InteractionType.RISK_TOLERANCE_SETTING.value:
                result = await self._handle_risk_tolerance_setting(profile_id, **kwargs)
            else:
                result = await self._handle_exploratory_analysis(profile_id, opportunities, organizational_profile, **kwargs)
            
            result.update({
                'profile_id': profile_id,
                'mode': mode,
                'interaction_type': interaction_type,
                'available_parameters': self._serialize_parameters(),
                'timestamp': datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error in interactive decision support: {e}")
            return {
                'profile_id': profile_id,
                'error': str(e),
                'available_tools': self._get_available_tools(),
                'timestamp': datetime.now().isoformat()
            }
    
    async def execute(self, config: ProcessorConfig) -> ProcessorResult:
        """Execute the interactive decision support tools as a processor"""
        try:
            # Extract profile ID from config
            profile_id = self._extract_profile_id_from_config(config)
            if not profile_id:
                result = ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    start_time=datetime.now()
                )
                result.add_error("Profile ID not found in configuration")
                return result
            
            # Default to exploratory analysis mode
            support_result = await self.process(
                profile_id=profile_id,
                mode=DecisionSupportMode.EXPLORATORY.value,
                opportunities=[],
                organizational_profile={}
            )
            
            # Convert to ProcessorResult format
            result = ProcessorResult(
                success=not support_result.get('error'),
                processor_name=self.metadata.name,
                start_time=datetime.now(),
                data=support_result
            )
            
            if support_result.get('error'):
                result.add_error(support_result['error'])
            
            return result
            
        except Exception as e:
            result = ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                start_time=datetime.now()
            )
            result.add_error(f"Interactive decision support execution error: {str(e)}")
            return result
    
    async def _handle_parameter_adjustment(self, profile_id: str, opportunities: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Handle parameter adjustment interactions"""
        
        parameter_updates = kwargs.get('parameter_updates', {})
        run_analysis = kwargs.get('run_analysis', True)
        
        # Apply parameter updates
        update_results = {}
        for param_id, new_value in parameter_updates.items():
            success = self.parameter_manager.update_parameter(param_id, new_value)
            update_results[param_id] = {
                'success': success,
                'new_value': new_value,
                'updated': success
            }
        
        result = {
            'interaction': 'parameter_adjustment',
            'parameter_updates': update_results,
            'current_parameters': self._serialize_parameters()
        }
        
        # Run analysis with new parameters if requested
        if run_analysis and any(r['success'] for r in update_results.values()):
            # Create scenario with updated parameters
            scenario = await self.scenario_engine.create_scenario(
                name=f"Interactive_{datetime.now().strftime('%H%M%S')}",
                description="Interactive parameter adjustment",
                created_by=f"user_{profile_id}",
                is_baseline=False
            )
            
            # Run scenario analysis
            analysis_results = await self.scenario_engine.run_scenario_analysis(
                scenario.scenario_id, opportunities, {'profile_id': profile_id}
            )
            
            result['analysis_results'] = analysis_results
        
        return result
    
    async def _handle_scenario_comparison(self, profile_id: str, opportunities: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Handle scenario comparison interactions"""
        
        scenario_configs = kwargs.get('scenarios', [])
        
        # Create scenarios
        created_scenarios = []
        for i, config in enumerate(scenario_configs):
            scenario = await self.scenario_engine.create_scenario(
                name=config.get('name', f'Scenario_{i+1}'),
                description=config.get('description', f'Scenario {i+1} for comparison'),
                created_by=f'user_{profile_id}',
                parameters=config.get('parameters', {})
            )
            created_scenarios.append(scenario)
            
            # Run analysis for each scenario
            await self.scenario_engine.run_scenario_analysis(
                scenario.scenario_id, opportunities, {'profile_id': profile_id}
            )
        
        # Compare scenarios
        scenario_ids = [s.scenario_id for s in created_scenarios]
        comparison = await self.scenario_engine.compare_scenarios(scenario_ids)
        
        return {
            'interaction': 'scenario_comparison',
            'scenarios_created': len(created_scenarios),
            'scenario_details': [self._serialize_scenario(s) for s in created_scenarios],
            'comparison_results': comparison
        }
    
    async def _handle_risk_tolerance_setting(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Handle risk tolerance setting interactions"""
        
        risk_tolerance = kwargs.get('risk_tolerance', 0.6)
        risk_factors = kwargs.get('risk_factors', {})
        
        # Update risk tolerance parameter
        success = self.parameter_manager.update_parameter('risk_tolerance', risk_tolerance)
        
        # Apply risk factor adjustments to other parameters
        risk_adjustments = {}
        if risk_factors:
            # Adjust feasibility weights based on risk factors
            current_feasibility_weight = self.parameter_manager.parameter_definitions['feasibility_weight'].current_value
            
            if risk_factors.get('conservative', False):
                new_feasibility_weight = min(1.0, current_feasibility_weight * 1.2)
                risk_adjustments['feasibility_weight'] = new_feasibility_weight
            elif risk_factors.get('aggressive', False):
                new_feasibility_weight = max(0.1, current_feasibility_weight * 0.8)
                risk_adjustments['feasibility_weight'] = new_feasibility_weight
        
        # Apply risk adjustments
        for param_id, new_value in risk_adjustments.items():
            self.parameter_manager.update_parameter(param_id, new_value)
        
        return {
            'interaction': 'risk_tolerance_setting',
            'risk_tolerance': risk_tolerance,
            'risk_tolerance_updated': success,
            'risk_adjustments': risk_adjustments,
            'current_risk_profile': {
                'risk_tolerance': risk_tolerance,
                'conservative_factors': risk_factors.get('conservative', False),
                'aggressive_factors': risk_factors.get('aggressive', False)
            }
        }
    
    async def _handle_exploratory_analysis(self, profile_id: str, opportunities: List[Dict[str, Any]], organizational_profile: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Handle exploratory analysis mode"""
        
        # Create baseline scenario
        baseline = await self.scenario_engine.create_scenario(
            name="Baseline",
            description="Current parameter settings",
            created_by=f"user_{profile_id}",
            is_baseline=True
        )
        
        # Run baseline analysis
        baseline_results = await self.scenario_engine.run_scenario_analysis(
            baseline.scenario_id, opportunities, organizational_profile
        )
        
        # Run sensitivity analysis on key parameters
        key_parameters = ['government_score_weight', 'feasibility_weight', 'risk_tolerance']
        sensitivity_results = await self.sensitivity_engine.analyze_multi_parameter_sensitivity(
            key_parameters, baseline.scenario_id, opportunities, organizational_profile
        )
        
        # Generate exploration recommendations
        exploration_recommendations = self._generate_exploration_recommendations(sensitivity_results)
        
        return {
            'interaction': 'exploratory_analysis',
            'baseline_scenario': self._serialize_scenario(baseline),
            'baseline_results': baseline_results,
            'sensitivity_analysis': sensitivity_results,
            'exploration_recommendations': exploration_recommendations,
            'suggested_parameter_adjustments': self._suggest_parameter_adjustments(sensitivity_results)
        }
    
    def _generate_exploration_recommendations(self, sensitivity_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations for exploration based on sensitivity analysis"""
        
        recommendations = []
        
        # Check for highly sensitive parameters
        high_impact_params = sensitivity_results['summary'].get('high_impact_parameters', [])
        if high_impact_params:
            recommendations.append(f"Focus exploration on high-impact parameters: {', '.join(high_impact_params)}")
        
        # Stability assessment
        stability = sensitivity_results['summary'].get('stability_assessment', 'unknown')
        if stability == 'sensitive':
            recommendations.append("Decision is sensitive to parameter changes - careful calibration recommended")
        elif stability == 'stable':
            recommendations.append("Decision is relatively stable - current parameters appear robust")
        
        # Most influential parameter
        most_influential = sensitivity_results['summary'].get('most_influential_parameter')
        if most_influential:
            recommendations.append(f"'{most_influential}' has the highest impact on decisions - consider careful tuning")
        
        # Interaction effects
        interaction_effects = sensitivity_results.get('interaction_effects', {})
        if interaction_effects:
            strong_interactions = [k for k, v in interaction_effects.items() if v > 0.1]
            if strong_interactions:
                recommendations.append(f"Parameter interactions detected: {', '.join(strong_interactions[:2])}")
        
        return recommendations
    
    def _suggest_parameter_adjustments(self, sensitivity_results: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest specific parameter adjustments based on sensitivity analysis"""
        
        suggestions = {}
        
        # Get parameter rankings
        rankings = sensitivity_results.get('parameter_rankings', [])
        
        for param_id, impact_score in rankings[:3]:  # Top 3 most impactful
            param = self.parameter_manager.parameter_definitions.get(param_id)
            if not param:
                continue
            
            current_value = param.current_value
            
            if impact_score > 0.5:  # High impact
                suggestions[param_id] = {
                    'current_value': current_value,
                    'suggestion': 'high_impact_parameter',
                    'recommendation': 'Consider small adjustments and observe impact',
                    'suggested_range': self._get_suggested_range(param, 0.1)  # ±10% adjustment
                }
            elif impact_score > 0.3:  # Medium impact
                suggestions[param_id] = {
                    'current_value': current_value,
                    'suggestion': 'medium_impact_parameter',
                    'recommendation': 'Safe to make moderate adjustments',
                    'suggested_range': self._get_suggested_range(param, 0.2)  # ±20% adjustment
                }
        
        return suggestions
    
    def _get_suggested_range(self, param: DecisionParameter, adjustment_factor: float) -> Dict[str, Any]:
        """Get suggested adjustment range for parameter"""
        
        if param.parameter_type == 'numeric':
            current = param.current_value
            adjustment = current * adjustment_factor
            
            min_suggested = max(param.min_value or 0, current - adjustment)
            max_suggested = min(param.max_value or 1, current + adjustment)
            
            return {
                'min': min_suggested,
                'max': max_suggested,
                'current': current
            }
        elif param.parameter_type == 'categorical':
            return {
                'current': param.current_value,
                'alternatives': [v for v in param.allowed_values if v != param.current_value]
            }
        
        return {'current': param.current_value}
    
    def _serialize_parameters(self) -> Dict[str, Any]:
        """Serialize current parameter state"""
        return {
            param_id: {
                'name': param.name,
                'description': param.description,
                'type': param.parameter_type,
                'current_value': param.current_value,
                'default_value': param.default_value,
                'constraints': {
                    'min_value': param.min_value,
                    'max_value': param.max_value,
                    'allowed_values': param.allowed_values
                },
                'ui_config': {
                    'input_type': param.input_type,
                    'display_format': param.display_format,
                    'help_text': param.help_text
                },
                'modification_count': param.modification_count,
                'last_modified': param.last_modified.isoformat()
            }
            for param_id, param in self.parameter_manager.parameter_definitions.items()
        }
    
    def _serialize_scenario(self, scenario: DecisionScenario) -> Dict[str, Any]:
        """Serialize scenario for JSON output"""
        return {
            'scenario_id': scenario.scenario_id,
            'name': scenario.name,
            'description': scenario.description,
            'created_by': scenario.created_by,
            'created_at': scenario.created_at.isoformat(),
            'parameters': scenario.parameters,
            'is_baseline': scenario.is_baseline,
            'parent_scenario_id': scenario.parent_scenario_id,
            'has_results': scenario.results is not None,
            'tags': scenario.tags,
            'notes': scenario.notes
        }
    
    def _get_available_tools(self) -> List[str]:
        """Get list of available interactive tools"""
        return [
            'parameter_adjustment',
            'scenario_comparison', 
            'sensitivity_analysis',
            'risk_tolerance_setting',
            'exploratory_analysis',
            'collaborative_decision_making'
        ]

# Export main components
__all__ = [
    'InteractiveDecisionSupportTools',
    'DecisionParameter',
    'DecisionScenario',
    'SensitivityAnalysis',
    'DecisionSupportMode',
    'InteractionType'
]