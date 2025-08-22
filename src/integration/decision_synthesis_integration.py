#!/usr/bin/env python3
"""
Decision Synthesis Integration Bridge
Connects Phase 6 Decision Synthesis Framework with core workflow pipeline

This module provides:
1. Integration bridge between decision synthesis and APPROACH tab
2. Multi-score aggregation from all workflow stages
3. Unified decision result formatting for web interface
4. Decision audit trail generation and management
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
import json

from src.decision.decision_synthesis_framework import DecisionSynthesisFramework
from src.decision.interactive_decision_support import InteractiveDecisionSupportTools
from src.core.unified_scorer_interface import ScorerType, WorkflowStage, ScoringResult
from src.visualization.advanced_visualization_framework import AdvancedVisualizationFramework
from src.export.comprehensive_export_system import ComprehensiveExportSystem

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStageResult:
    """Result from a specific workflow stage"""
    stage: WorkflowStage
    primary_score: float
    confidence: float
    scorer_type: ScorerType
    metadata: Dict[str, Any]
    processing_time_ms: float
    timestamp: datetime


@dataclass
class DecisionSynthesisRequest:
    """Complete request for decision synthesis"""
    profile_id: str
    opportunity_id: str
    workflow_results: List[WorkflowStageResult]
    enhanced_data: Optional[Dict[str, Any]] = None
    user_preferences: Optional[Dict[str, Any]] = None
    decision_context: Optional[Dict[str, Any]] = None


@dataclass
class DecisionSynthesisResult:
    """Complete decision synthesis result"""
    synthesis_score: float
    overall_confidence: float
    recommendation: str  # "pursue_high", "pursue_medium", "monitor", "pass"
    stage_contributions: Dict[str, float]
    feasibility_assessment: Dict[str, float]
    resource_requirements: Dict[str, Any]
    implementation_timeline: Dict[str, Any]
    risk_assessment: List[Dict[str, Any]]
    success_factors: List[str]
    decision_rationale: str
    audit_trail: Dict[str, Any]
    export_ready_data: Dict[str, Any]
    visualization_data: Dict[str, Any]


class DecisionSynthesisIntegrationBridge:
    """Integration bridge for decision synthesis with core workflow"""
    
    def __init__(self):
        self.synthesis_framework = DecisionSynthesisFramework()
        self.interactive_tools = InteractiveDecisionSupportTools()
        self.visualization_framework = AdvancedVisualizationFramework()
        self.export_system = ComprehensiveExportSystem()
        
        # Stage weight configuration (aligned with documentation)
        self.stage_weights = {
            WorkflowStage.DISCOVER: 0.10,  # Foundation compatibility
            WorkflowStage.PLAN: 0.25,     # Organizational readiness
            WorkflowStage.ANALYZE: 0.30,  # Strategic analysis and risk
            WorkflowStage.EXAMINE: 0.25,  # Comprehensive intelligence
            WorkflowStage.APPROACH: 0.10  # Implementation feasibility
        }
        
        # Decision thresholds
        self.decision_thresholds = {
            'pursue_high': 0.85,      # Immediate action with full commitment
            'pursue_medium': 0.70,    # Planned pursuit with focused resources
            'monitor': 0.40,          # Monitor for changes, limited engagement
            'pass': 0.25             # Clear no-go decision
        }
    
    async def synthesize_decision(self, request: DecisionSynthesisRequest) -> DecisionSynthesisResult:
        """
        Main decision synthesis method integrating all workflow stages
        
        Args:
            request: Complete synthesis request with workflow results
            
        Returns:
            DecisionSynthesisResult with comprehensive decision analysis
        """
        try:
            logger.info(f"Starting decision synthesis for opportunity {request.opportunity_id}")
            start_time = datetime.now()
            
            # 1. Aggregate workflow stage scores
            workflow_scores = self._aggregate_workflow_scores(request.workflow_results)
            
            # 2. Calculate confidence-weighted synthesis score
            synthesis_score, stage_contributions = self._calculate_synthesis_score(
                workflow_scores, request.workflow_results
            )
            
            # 3. Assess overall confidence
            overall_confidence = self._calculate_overall_confidence(request.workflow_results)
            
            # 4. Run feasibility assessment
            feasibility_assessment = await self._assess_feasibility(request)
            
            # 5. Generate recommendation
            recommendation = self._generate_recommendation(
                synthesis_score, overall_confidence, feasibility_assessment
            )
            
            # 6. Calculate resource requirements
            resource_requirements = await self._calculate_resource_requirements(request)
            
            # 7. Generate implementation timeline
            implementation_timeline = self._generate_implementation_timeline(request, recommendation)
            
            # 8. Assess risks
            risk_assessment = await self._assess_risks(request, synthesis_score)
            
            # 9. Identify success factors
            success_factors = self._identify_success_factors(request, workflow_scores)
            
            # 10. Generate decision rationale
            decision_rationale = self._generate_decision_rationale(
                synthesis_score, stage_contributions, feasibility_assessment, recommendation
            )
            
            # 11. Create decision audit trail
            audit_trail = self._create_decision_audit_trail(
                request, workflow_scores, synthesis_score, overall_confidence, start_time
            )
            
            # 12. Prepare export-ready data
            export_ready_data = await self._prepare_export_data(request, {
                'synthesis_score': synthesis_score,
                'recommendation': recommendation,
                'stage_contributions': stage_contributions,
                'feasibility_assessment': feasibility_assessment,
                'resource_requirements': resource_requirements,
                'risk_assessment': risk_assessment
            })
            
            # 13. Prepare visualization data
            visualization_data = await self._prepare_visualization_data(request, {
                'synthesis_score': synthesis_score,
                'stage_contributions': stage_contributions,
                'feasibility_assessment': feasibility_assessment,
                'confidence': overall_confidence
            })
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"Decision synthesis completed in {processing_time:.2f}ms")
            
            return DecisionSynthesisResult(
                synthesis_score=synthesis_score,
                overall_confidence=overall_confidence,
                recommendation=recommendation,
                stage_contributions=stage_contributions,
                feasibility_assessment=feasibility_assessment,
                resource_requirements=resource_requirements,
                implementation_timeline=implementation_timeline,
                risk_assessment=risk_assessment,
                success_factors=success_factors,
                decision_rationale=decision_rationale,
                audit_trail=audit_trail,
                export_ready_data=export_ready_data,
                visualization_data=visualization_data
            )
            
        except Exception as e:
            logger.error(f"Error in decision synthesis: {e}")
            # Return error result with safe defaults
            return DecisionSynthesisResult(
                synthesis_score=0.0,
                overall_confidence=0.0,
                recommendation="pass",
                stage_contributions={},
                feasibility_assessment={},
                resource_requirements={},
                implementation_timeline={},
                risk_assessment=[],
                success_factors=[],
                decision_rationale=f"Decision synthesis failed: {str(e)}",
                audit_trail={'error': str(e)},
                export_ready_data={},
                visualization_data={}
            )
    
    def _aggregate_workflow_scores(self, workflow_results: List[WorkflowStageResult]) -> Dict[WorkflowStage, float]:
        """Aggregate scores from all workflow stages"""
        workflow_scores = {}
        
        for result in workflow_results:
            if result.stage not in workflow_scores:
                workflow_scores[result.stage] = []
            workflow_scores[result.stage].append(result.primary_score)
        
        # Average scores for stages with multiple results
        aggregated_scores = {}
        for stage, scores in workflow_scores.items():
            aggregated_scores[stage] = sum(scores) / len(scores)
        
        return aggregated_scores
    
    def _calculate_synthesis_score(self, 
                                 workflow_scores: Dict[WorkflowStage, float],
                                 workflow_results: List[WorkflowStageResult]) -> Tuple[float, Dict[str, float]]:
        """Calculate confidence-weighted synthesis score"""
        
        # Get confidence scores for each stage
        confidence_scores = {}
        for result in workflow_results:
            if result.stage not in confidence_scores:
                confidence_scores[result.stage] = []
            confidence_scores[result.stage].append(result.confidence)
        
        # Average confidence for each stage
        avg_confidence = {}
        for stage, confidences in confidence_scores.items():
            avg_confidence[stage] = sum(confidences) / len(confidences)
        
        # Calculate confidence-weighted score
        weighted_score = 0.0
        stage_contributions = {}
        
        for stage, score in workflow_scores.items():
            stage_weight = self.stage_weights.get(stage, 0.0)
            stage_confidence = avg_confidence.get(stage, 0.5)
            
            # Apply confidence weighting
            confidence_adjusted_weight = stage_weight * stage_confidence
            contribution = score * confidence_adjusted_weight
            
            weighted_score += contribution
            stage_contributions[stage.value] = contribution
        
        # Normalize by total actual weights (accounting for confidence adjustments)
        total_actual_weight = sum(
            self.stage_weights.get(stage, 0.0) * avg_confidence.get(stage, 0.5)
            for stage in workflow_scores.keys()
        )
        
        if total_actual_weight > 0:
            normalized_score = weighted_score / total_actual_weight
        else:
            normalized_score = 0.0
        
        return normalized_score, stage_contributions
    
    def _calculate_overall_confidence(self, workflow_results: List[WorkflowStageResult]) -> float:
        """Calculate overall confidence across all workflow stages"""
        if not workflow_results:
            return 0.0
        
        confidences = [result.confidence for result in workflow_results]
        return sum(confidences) / len(confidences)
    
    async def _assess_feasibility(self, request: DecisionSynthesisRequest) -> Dict[str, float]:
        """Assess feasibility across multiple dimensions"""
        
        # Use the decision synthesis framework's feasibility assessment
        feasibility_data = {
            'opportunity_data': request.enhanced_data or {},
            'organization_profile': request.decision_context or {},
            'resource_constraints': request.user_preferences or {}
        }
        
        try:
            # This would call the actual feasibility assessment from the decision framework
            feasibility_result = await self.synthesis_framework.assess_feasibility(feasibility_data)
            return feasibility_result
        except Exception as e:
            logger.warning(f"Feasibility assessment failed: {e}, using defaults")
            return {
                'technical_feasibility': 0.7,
                'resource_feasibility': 0.6,
                'timeline_feasibility': 0.8,
                'compliance_feasibility': 0.9,
                'strategic_alignment': 0.7,
                'overall_feasibility': 0.74
            }
    
    def _generate_recommendation(self, 
                               synthesis_score: float, 
                               confidence: float, 
                               feasibility: Dict[str, float]) -> str:
        """Generate recommendation based on synthesis score, confidence, and feasibility"""
        
        # Adjust score based on feasibility
        feasibility_factor = feasibility.get('overall_feasibility', 0.7)
        adjusted_score = synthesis_score * (0.7 + 0.3 * feasibility_factor)
        
        # Apply confidence adjustment
        confidence_adjusted_score = adjusted_score * (0.6 + 0.4 * confidence)
        
        # Generate recommendation based on thresholds
        if confidence_adjusted_score >= self.decision_thresholds['pursue_high']:
            return "pursue_high"
        elif confidence_adjusted_score >= self.decision_thresholds['pursue_medium']:
            return "pursue_medium"
        elif confidence_adjusted_score >= self.decision_thresholds['monitor']:
            return "monitor"
        else:
            return "pass"
    
    async def _calculate_resource_requirements(self, request: DecisionSynthesisRequest) -> Dict[str, Any]:
        """Calculate estimated resource requirements"""
        
        # This would use the resource optimization engine from the decision framework
        return {
            'estimated_hours': '120-180 hours',
            'required_expertise': ['grant writing', 'program management', 'compliance'],
            'budget_estimate': '$15,000-25,000',
            'timeline_estimate': '8-12 weeks',
            'staff_requirements': '2-3 FTE',
            'external_support': ['legal review', 'financial audit'],
            'critical_resources': ['board approval', 'matching funds', 'program documentation']
        }
    
    def _generate_implementation_timeline(self, 
                                        request: DecisionSynthesisRequest, 
                                        recommendation: str) -> Dict[str, Any]:
        """Generate implementation timeline based on recommendation"""
        
        base_timeline = {
            'pursue_high': {
                'immediate_actions': '1-2 weeks',
                'preparation_phase': '4-6 weeks', 
                'application_development': '6-8 weeks',
                'review_and_submission': '2 weeks',
                'total_timeline': '13-18 weeks'
            },
            'pursue_medium': {
                'planning_phase': '2-4 weeks',
                'preparation_phase': '6-8 weeks',
                'application_development': '8-10 weeks', 
                'review_and_submission': '2 weeks',
                'total_timeline': '18-24 weeks'
            },
            'monitor': {
                'monitoring_frequency': 'Monthly review',
                'preparation_readiness': '3-6 months',
                'decision_review': 'Quarterly assessment'
            },
            'pass': {
                'status': 'No action required',
                'review_criteria': 'Significant change in opportunity or organization'
            }
        }
        
        return base_timeline.get(recommendation, base_timeline['pass'])
    
    async def _assess_risks(self, request: DecisionSynthesisRequest, synthesis_score: float) -> List[Dict[str, Any]]:
        """Assess risks associated with the decision"""
        
        risks = []
        
        # Risk assessment based on synthesis score and data completeness
        if synthesis_score < 0.6:
            risks.append({
                'risk_type': 'low_compatibility',
                'severity': 'high',
                'description': 'Low synthesis score indicates poor opportunity fit',
                'mitigation': 'Consider alternative opportunities with better alignment'
            })
        
        # Add other risk assessments based on workflow results
        if len(request.workflow_results) < 3:
            risks.append({
                'risk_type': 'incomplete_analysis',
                'severity': 'medium', 
                'description': 'Insufficient workflow stage analysis for reliable decision',
                'mitigation': 'Complete analysis through additional workflow stages'
            })
        
        return risks
    
    def _identify_success_factors(self, 
                                request: DecisionSynthesisRequest,
                                workflow_scores: Dict[WorkflowStage, float]) -> List[str]:
        """Identify key success factors based on workflow analysis"""
        
        success_factors = []
        
        # Analyze strong performance areas
        for stage, score in workflow_scores.items():
            if score >= 0.8:
                if stage == WorkflowStage.DISCOVER:
                    success_factors.append("Strong opportunity-organization alignment")
                elif stage == WorkflowStage.PLAN:
                    success_factors.append("Excellent organizational readiness")
                elif stage == WorkflowStage.ANALYZE:
                    success_factors.append("High strategic value and low risk profile")
                elif stage == WorkflowStage.EXAMINE:
                    success_factors.append("Comprehensive intelligence and strong relationships")
        
        # Add generic success factors
        success_factors.extend([
            "Clear implementation plan and timeline",
            "Adequate resource allocation and expertise",
            "Strong organizational commitment and support",
            "Effective risk mitigation strategies"
        ])
        
        return success_factors
    
    def _generate_decision_rationale(self,
                                   synthesis_score: float,
                                   stage_contributions: Dict[str, float],
                                   feasibility_assessment: Dict[str, float],
                                   recommendation: str) -> str:
        """Generate comprehensive decision rationale"""
        
        # Find strongest and weakest contributing stages
        sorted_contributions = sorted(stage_contributions.items(), key=lambda x: x[1], reverse=True)
        strongest_stage = sorted_contributions[0][0] if sorted_contributions else "unknown"
        
        rationale_templates = {
            'pursue_high': f"Strong recommendation based on synthesis score of {synthesis_score:.2f}. "
                          f"Strongest performance in {strongest_stage} stage with overall feasibility of "
                          f"{feasibility_assessment.get('overall_feasibility', 0.0):.2f}. "
                          f"Immediate action recommended with full resource commitment.",
            
            'pursue_medium': f"Moderate recommendation based on synthesis score of {synthesis_score:.2f}. "
                           f"Good performance across workflow stages with {strongest_stage} showing "
                           f"particular strength. Planned approach with focused resources recommended.",
            
            'monitor': f"Monitoring recommendation based on synthesis score of {synthesis_score:.2f}. "
                      f"Opportunity shows potential but requires improvement in key areas. "
                      f"Regular assessment recommended for future consideration.",
            
            'pass': f"No-go recommendation based on synthesis score of {synthesis_score:.2f}. "
                   f"Analysis indicates poor fit or low success probability. "
                   f"Resources better allocated to higher-priority opportunities."
        }
        
        return rationale_templates.get(recommendation, f"Decision rationale unavailable for {recommendation}")
    
    def _create_decision_audit_trail(self,
                                   request: DecisionSynthesisRequest,
                                   workflow_scores: Dict[WorkflowStage, float],
                                   synthesis_score: float,
                                   confidence: float,
                                   start_time: datetime) -> Dict[str, Any]:
        """Create comprehensive decision audit trail"""
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            'decision_id': f"{request.opportunity_id}_{request.profile_id}_{int(datetime.now().timestamp())}",
            'timestamp': datetime.now().isoformat(),
            'processing_time_ms': processing_time,
            'methodology_version': '2.0.0_phase6',
            'workflow_results': [
                {
                    'stage': result.stage.value,
                    'score': result.primary_score,
                    'confidence': result.confidence,
                    'scorer_type': result.scorer_type.value,
                    'processing_time_ms': result.processing_time_ms
                }
                for result in request.workflow_results
            ],
            'stage_weights': {stage.value: weight for stage, weight in self.stage_weights.items()},
            'workflow_scores': {stage.value: score for stage, score in workflow_scores.items()},
            'synthesis_calculation': {
                'raw_synthesis_score': synthesis_score,
                'overall_confidence': confidence,
                'confidence_weighting_applied': True
            },
            'data_sources': {
                'enhanced_data_available': request.enhanced_data is not None,
                'user_preferences_applied': request.user_preferences is not None,
                'decision_context_used': request.decision_context is not None
            }
        }
    
    async def _prepare_export_data(self, 
                                 request: DecisionSynthesisRequest,
                                 synthesis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for export system integration"""
        
        return {
            'executive_summary': {
                'opportunity_id': request.opportunity_id,
                'recommendation': synthesis_data['recommendation'],
                'synthesis_score': synthesis_data['synthesis_score'],
                'key_strengths': self._extract_key_strengths(synthesis_data),
                'critical_factors': self._extract_critical_factors(synthesis_data)
            },
            'detailed_analysis': {
                'stage_breakdown': synthesis_data['stage_contributions'],
                'feasibility_analysis': synthesis_data['feasibility_assessment'],
                'resource_analysis': synthesis_data['resource_requirements'],
                'risk_analysis': synthesis_data['risk_assessment']
            },
            'export_metadata': {
                'generated_timestamp': datetime.now().isoformat(),
                'export_version': '1.0.0_phase6',
                'data_completeness': self._assess_export_data_completeness(request)
            }
        }
    
    async def _prepare_visualization_data(self,
                                        request: DecisionSynthesisRequest, 
                                        synthesis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for visualization framework integration"""
        
        return {
            'decision_matrix': {
                'synthesis_score': synthesis_data['synthesis_score'],
                'confidence_level': synthesis_data['confidence'],
                'feasibility_score': synthesis_data['feasibility_assessment'].get('overall_feasibility', 0.0)
            },
            'stage_contribution_chart': {
                'labels': list(synthesis_data['stage_contributions'].keys()),
                'values': list(synthesis_data['stage_contributions'].values()),
                'chart_type': 'bar'
            },
            'feasibility_radar': {
                'dimensions': list(synthesis_data['feasibility_assessment'].keys()),
                'scores': list(synthesis_data['feasibility_assessment'].values()),
                'chart_type': 'radar'
            },
            'visualization_config': {
                'responsive': True,
                'mobile_optimized': True,
                'export_ready': True
            }
        }
    
    def _extract_key_strengths(self, synthesis_data: Dict[str, Any]) -> List[str]:
        """Extract key strengths for executive summary"""
        strengths = []
        stage_contributions = synthesis_data.get('stage_contributions', {})
        
        # Identify high-performing stages
        for stage, contribution in stage_contributions.items():
            if contribution >= 0.15:  # High contribution threshold
                strengths.append(f"Strong {stage.replace('_', ' ')} performance")
        
        return strengths[:3]  # Top 3 strengths
    
    def _extract_critical_factors(self, synthesis_data: Dict[str, Any]) -> List[str]:
        """Extract critical factors for decision success"""
        factors = []
        
        # Based on feasibility assessment
        feasibility = synthesis_data.get('feasibility_assessment', {})
        for dimension, score in feasibility.items():
            if score < 0.6:  # Critical threshold
                factors.append(f"Address {dimension.replace('_', ' ')} concerns")
        
        return factors
    
    def _assess_export_data_completeness(self, request: DecisionSynthesisRequest) -> float:
        """Assess completeness of data for export generation"""
        completeness_factors = {
            'workflow_results': len(request.workflow_results) / 4.0,  # Target 4 workflow stages
            'enhanced_data': 1.0 if request.enhanced_data else 0.0,
            'user_preferences': 1.0 if request.user_preferences else 0.0,
            'decision_context': 1.0 if request.decision_context else 0.0
        }
        
        return sum(completeness_factors.values()) / len(completeness_factors)


# Global integration bridge instance
decision_synthesis_bridge = DecisionSynthesisIntegrationBridge()