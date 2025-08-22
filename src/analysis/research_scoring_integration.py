"""
Research-Scoring Integration Framework
Phase 3: AI-Lite Dual-Function Platform

This module integrates the AI Research Platform with existing scoring systems,
providing seamless dual-function capabilities for the ANALYZE tab.

Key Features:
- Research evidence integration with scoring
- Dual-function batch processing
- Cost optimization for research operations
- Quality assurance for research outputs
- Unified scoring and research API
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path

from .ai_research_platform import AIResearchPlatform, ResearchReport, ReportFormat
from .grant_team_templates import GrantTeamTemplates, DecisionCategory, RiskLevel
from ..processors.analysis.ai_lite_scorer import AILiteScorer

logger = logging.getLogger(__name__)


@dataclass
class IntegratedAnalysis:
    """Combined scoring and research analysis result"""
    opportunity_id: str
    organization_name: str
    
    # Scoring Results
    scoring_results: Dict[str, Any]
    scoring_confidence: float
    auto_promotion_eligible: bool
    
    # Research Results
    research_report: Optional[ResearchReport] = None
    research_confidence: float = 0.0
    research_quality_score: float = 0.0
    
    # Integrated Assessment
    integrated_score: float = 0.0
    integrated_confidence: float = 0.0
    evidence_strength: float = 0.0
    research_impact_factor: float = 0.0
    
    # Decision Support
    recommended_action: str = "pending"
    decision_confidence: float = 0.0
    next_steps: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    
    # Metadata
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    cost_breakdown: Dict[str, float] = field(default_factory=dict)
    processing_time: float = 0.0


@dataclass
class BatchAnalysisResult:
    """Result of batch analysis operation"""
    batch_id: str
    total_opportunities: int
    successful_analyses: int
    failed_analyses: int
    
    # Results
    integrated_analyses: List[IntegratedAnalysis]
    error_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # Performance Metrics
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    total_cost: float = 0.0
    average_cost_per_opportunity: float = 0.0
    
    # Quality Metrics
    average_confidence: float = 0.0
    quality_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Batch Metadata
    batch_started: datetime = field(default_factory=datetime.now)
    batch_completed: Optional[datetime] = None
    cost_optimization_enabled: bool = True


class ResearchScoringIntegration:
    """
    Integration layer between AI Research Platform and existing scoring systems
    
    Provides unified dual-function capabilities for comprehensive opportunity analysis
    """
    
    def __init__(self, api_key: Optional[str] = None, 
                 cost_optimization: bool = True,
                 quality_threshold: float = 0.6):
        """
        Initialize the integration system
        
        Args:
            api_key: OpenAI API key for AI operations
            cost_optimization: Enable cost optimization features
            quality_threshold: Minimum quality threshold for research outputs
        """
        self.api_key = api_key
        self.cost_optimization = cost_optimization
        self.quality_threshold = quality_threshold
        
        # Initialize components
        self.research_platform = AIResearchPlatform(api_key, cost_optimization)
        self.template_system = GrantTeamTemplates()
        self.ai_lite_scorer = AILiteScorer()
        
        # Performance tracking
        self.performance_metrics = {
            'total_analyses': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'total_cost': 0.0,
            'total_processing_time': 0.0,
            'average_quality_score': 0.0
        }
        
        # Integration weights for scoring combination
        self.integration_weights = {
            'scoring_weight': 0.7,        # Weight for algorithmic scoring
            'research_weight': 0.3,       # Weight for research evidence
            'confidence_threshold': 0.8,  # Threshold for high confidence
            'evidence_boost': 0.1,        # Boost for strong research evidence
            'quality_penalty': 0.05       # Penalty for low quality research
        }

    async def __aenter__(self):
        """Async context manager entry"""
        await self.research_platform.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.research_platform.__aexit__(exc_type, exc_val, exc_tb)

    async def analyze_opportunity_integrated(self, opportunity_data: Dict[str, Any],
                                           include_research: bool = True,
                                           report_type: ReportFormat = ReportFormat.EXECUTIVE_SUMMARY) -> IntegratedAnalysis:
        """
        Perform integrated scoring and research analysis
        
        Args:
            opportunity_data: Opportunity data to analyze
            include_research: Whether to include research analysis
            report_type: Type of research report to generate
            
        Returns:
            Integrated analysis results
        """
        start_time = datetime.now()
        opportunity_id = opportunity_data.get('opportunity_id', 'unknown')
        org_name = opportunity_data.get('organization_name', 'Unknown')
        
        logger.info(f"Starting integrated analysis for: {org_name}")
        
        try:
            # Initialize result
            analysis = IntegratedAnalysis(
                opportunity_id=opportunity_id,
                organization_name=org_name,
                scoring_results={},
                scoring_confidence=0.0,
                auto_promotion_eligible=False
            )
            
            # Perform scoring analysis
            await self._perform_scoring_analysis(opportunity_data, analysis)
            
            # Perform research analysis if requested
            if include_research:
                await self._perform_research_analysis(opportunity_data, analysis, report_type)
            
            # Integrate results
            self._integrate_scoring_and_research(analysis)
            
            # Generate decision support
            self._generate_decision_support(analysis)
            
            # Calculate cost breakdown
            analysis.cost_breakdown = self._calculate_cost_breakdown(analysis, include_research)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            analysis.processing_time = processing_time
            
            # Update performance metrics
            self._update_performance_metrics(analysis, True)
            
            logger.info(f"Integrated analysis completed for {org_name}. "
                       f"Integrated score: {analysis.integrated_score:.3f}, "
                       f"Processing time: {processing_time:.2f}s")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in integrated analysis for {org_name}: {str(e)}")
            
            # Create error analysis
            analysis = IntegratedAnalysis(
                opportunity_id=opportunity_id,
                organization_name=org_name,
                scoring_results={'error': str(e)},
                scoring_confidence=0.0,
                auto_promotion_eligible=False,
                recommended_action="error_review_required"
            )
            
            self._update_performance_metrics(analysis, False)
            return analysis

    async def _perform_scoring_analysis(self, opportunity_data: Dict[str, Any], 
                                      analysis: IntegratedAnalysis):
        """Perform scoring analysis component"""
        try:
            # Extract existing scoring or perform new scoring
            existing_scoring = opportunity_data.get('scoring', {})
            
            if existing_scoring:
                # Use existing scoring results
                analysis.scoring_results = existing_scoring
                analysis.scoring_confidence = existing_scoring.get('confidence_level', 0.7)
                analysis.auto_promotion_eligible = existing_scoring.get('auto_promotion_eligible', False)
            else:
                # Perform new AI Lite scoring
                scoring_result = await self._perform_ai_lite_scoring(opportunity_data)
                analysis.scoring_results = scoring_result
                analysis.scoring_confidence = scoring_result.get('confidence_level', 0.7)
                analysis.auto_promotion_eligible = scoring_result.get('auto_promotion_eligible', False)
            
            logger.debug(f"Scoring analysis completed. Score: {analysis.scoring_results.get('overall_score', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Error in scoring analysis: {str(e)}")
            analysis.scoring_results = {'error': str(e)}
            analysis.scoring_confidence = 0.0

    async def _perform_research_analysis(self, opportunity_data: Dict[str, Any],
                                       analysis: IntegratedAnalysis,
                                       report_type: ReportFormat):
        """Perform research analysis component"""
        try:
            # Generate research report
            research_report = await self.research_platform.generate_research_report(
                opportunity_data, report_type
            )
            
            analysis.research_report = research_report
            analysis.research_confidence = research_report.confidence_assessment.get('overall_assessment', 0.7)
            
            # Calculate research quality score
            analysis.research_quality_score = self._calculate_research_quality_score(research_report)
            
            logger.debug(f"Research analysis completed. Quality score: {analysis.research_quality_score:.3f}")
            
        except Exception as e:
            logger.error(f"Error in research analysis: {str(e)}")
            analysis.research_confidence = 0.0
            analysis.research_quality_score = 0.0

    def _integrate_scoring_and_research(self, analysis: IntegratedAnalysis):
        """Integrate scoring and research results into unified score"""
        
        # Get base scoring
        base_score = analysis.scoring_results.get('overall_score', 0.5)
        scoring_confidence = analysis.scoring_confidence
        
        # Initialize integrated score with base scoring
        analysis.integrated_score = base_score
        analysis.integrated_confidence = scoring_confidence
        
        # Add research impact if available
        if analysis.research_report:
            research_impact = self._calculate_research_impact(analysis)
            analysis.research_impact_factor = research_impact
            
            # Apply research weight
            research_contribution = research_impact * self.integration_weights['research_weight']
            scoring_contribution = base_score * self.integration_weights['scoring_weight']
            
            analysis.integrated_score = scoring_contribution + research_contribution
            
            # Adjust for evidence strength
            analysis.evidence_strength = self._calculate_evidence_strength(analysis)
            if analysis.evidence_strength > 0.8:
                analysis.integrated_score += self.integration_weights['evidence_boost']
            elif analysis.evidence_strength < 0.4:
                analysis.integrated_score -= self.integration_weights['quality_penalty']
            
            # Ensure score bounds
            analysis.integrated_score = max(0.0, min(1.0, analysis.integrated_score))
            
            # Calculate integrated confidence
            confidence_components = [
                scoring_confidence * self.integration_weights['scoring_weight'],
                analysis.research_confidence * self.integration_weights['research_weight']
            ]
            analysis.integrated_confidence = sum(confidence_components)
        
        logger.debug(f"Integration completed. Integrated score: {analysis.integrated_score:.3f}, "
                    f"Confidence: {analysis.integrated_confidence:.3f}")

    def _calculate_research_impact(self, analysis: IntegratedAnalysis) -> float:
        """Calculate impact of research on overall assessment"""
        if not analysis.research_report:
            return 0.0
        
        impact_factors = []
        
        # Quality of research
        impact_factors.append(analysis.research_quality_score * 0.4)
        
        # Number of contacts identified
        contacts_count = len(analysis.research_report.contacts_identified)
        contact_impact = min(contacts_count / 5.0, 1.0) * 0.2  # Normalize to 5 contacts max
        impact_factors.append(contact_impact)
        
        # Evidence package strength
        evidence_count = len(analysis.research_report.evidence_package)
        evidence_impact = min(evidence_count / 10.0, 1.0) * 0.2  # Normalize to 10 facts max
        impact_factors.append(evidence_impact)
        
        # Recommendation strength
        recommendation_count = len(analysis.research_report.recommendations)
        recommendation_impact = min(recommendation_count / 5.0, 1.0) * 0.2  # Normalize to 5 recommendations max
        impact_factors.append(recommendation_impact)
        
        return sum(impact_factors)

    def _calculate_evidence_strength(self, analysis: IntegratedAnalysis) -> float:
        """Calculate strength of evidence from research"""
        if not analysis.research_report:
            return 0.0
        
        evidence_factors = []
        
        # Research confidence
        evidence_factors.append(analysis.research_confidence * 0.4)
        
        # Evidence package quality
        evidence_factors.append(analysis.research_quality_score * 0.3)
        
        # Contact verification level
        verified_contacts = sum(
            1 for contact in analysis.research_report.contacts_identified
            if contact.confidence > 0.7
        )
        if analysis.research_report.contacts_identified:
            contact_verification = verified_contacts / len(analysis.research_report.contacts_identified) * 0.3
        else:
            contact_verification = 0.0
        evidence_factors.append(contact_verification)
        
        return sum(evidence_factors)

    def _calculate_research_quality_score(self, research_report: ResearchReport) -> float:
        """Calculate quality score for research report"""
        quality_factors = []
        
        # Completeness of executive summary
        if research_report.executive_summary and len(research_report.executive_summary) > 50:
            quality_factors.append(0.2)
        
        # Presence of detailed findings
        if research_report.detailed_findings:
            quality_factors.append(0.2)
        
        # Evidence package size and quality
        evidence_quality = min(len(research_report.evidence_package) / 5.0, 1.0) * 0.2
        quality_factors.append(evidence_quality)
        
        # Contact information quality
        contact_quality = min(len(research_report.contacts_identified) / 3.0, 1.0) * 0.2
        quality_factors.append(contact_quality)
        
        # Recommendation relevance
        recommendation_quality = min(len(research_report.recommendations) / 3.0, 1.0) * 0.2
        quality_factors.append(recommendation_quality)
        
        return sum(quality_factors)

    def _generate_decision_support(self, analysis: IntegratedAnalysis):
        """Generate decision support recommendations"""
        
        # Determine recommended action
        if analysis.integrated_score >= 0.8 and analysis.integrated_confidence >= 0.8:
            analysis.recommended_action = "strong_go"
        elif analysis.integrated_score >= 0.6 and analysis.integrated_confidence >= 0.6:
            analysis.recommended_action = "conditional_go"
        elif analysis.integrated_score >= 0.4:
            analysis.recommended_action = "proceed_with_caution"
        else:
            analysis.recommended_action = "no_go"
        
        # Calculate decision confidence
        confidence_factors = [
            analysis.integrated_confidence * 0.6,
            analysis.evidence_strength * 0.4
        ]
        analysis.decision_confidence = sum(confidence_factors)
        
        # Generate next steps
        analysis.next_steps = self._generate_next_steps(analysis)
        
        # Identify risk factors
        analysis.risk_factors = self._identify_integrated_risk_factors(analysis)

    def _generate_next_steps(self, analysis: IntegratedAnalysis) -> List[str]:
        """Generate recommended next steps"""
        next_steps = []
        
        if analysis.recommended_action == "strong_go":
            next_steps.extend([
                "Proceed with detailed proposal development",
                "Initiate contact with identified personnel",
                "Develop comprehensive implementation plan"
            ])
        elif analysis.recommended_action == "conditional_go":
            next_steps.extend([
                "Address identified risk factors",
                "Gather additional information on key uncertainties",
                "Develop contingency plans for identified risks"
            ])
        elif analysis.recommended_action == "proceed_with_caution":
            next_steps.extend([
                "Conduct additional due diligence",
                "Reassess strategic alignment",
                "Consider alternative opportunities"
            ])
        else:  # no_go
            next_steps.extend([
                "Document lessons learned",
                "Monitor for future changes",
                "Focus resources on higher-priority opportunities"
            ])
        
        # Add research-specific next steps
        if analysis.research_report and analysis.research_report.contacts_identified:
            next_steps.append("Follow up with identified contacts")
        
        if analysis.evidence_strength < 0.5:
            next_steps.append("Strengthen evidence base through additional research")
        
        return next_steps

    def _identify_integrated_risk_factors(self, analysis: IntegratedAnalysis) -> List[str]:
        """Identify risk factors from integrated analysis"""
        risk_factors = []
        
        # Scoring-based risks
        if analysis.scoring_confidence < 0.6:
            risk_factors.append("Low confidence in algorithmic scoring")
        
        if not analysis.auto_promotion_eligible:
            risk_factors.append("Manual review required for advancement")
        
        # Research-based risks
        if analysis.research_quality_score < 0.5:
            risk_factors.append("Limited research quality and evidence")
        
        if analysis.research_report and len(analysis.research_report.contacts_identified) == 0:
            risk_factors.append("No direct contact information identified")
        
        # Integration risks
        if analysis.integrated_confidence < 0.7:
            risk_factors.append("Overall assessment confidence below threshold")
        
        if analysis.evidence_strength < 0.4:
            risk_factors.append("Weak supporting evidence for decision")
        
        # Add research report risk factors if available
        if analysis.research_report:
            risk_factors.extend(analysis.research_report.risk_factors)
        
        return list(set(risk_factors))  # Remove duplicates

    def _calculate_cost_breakdown(self, analysis: IntegratedAnalysis, include_research: bool) -> Dict[str, float]:
        """Calculate cost breakdown for analysis"""
        costs = {
            'scoring_cost': 0.001,  # Minimal cost for algorithmic scoring
            'research_cost': 0.0,
            'integration_cost': 0.0005,  # Cost for integration processing
            'total_cost': 0.0
        }
        
        if include_research and analysis.research_report:
            costs['research_cost'] = analysis.research_report.cost_analysis.get('research_cost', 0.02)
        
        costs['total_cost'] = sum(costs.values())
        
        return costs

    async def _perform_ai_lite_scoring(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform AI Lite scoring for opportunity"""
        try:
            # This would integrate with the existing AI Lite scorer
            # For now, return a mock result based on existing data structure
            
            base_score = 0.65  # Default moderate score
            
            # Adjust score based on available data
            if opportunity_data.get('funding_amount'):
                base_score += 0.1
            
            if opportunity_data.get('current_stage') in ['recommendations', 'deep_analysis']:
                base_score += 0.05
            
            return {
                'overall_score': min(base_score, 1.0),
                'confidence_level': 0.75,
                'auto_promotion_eligible': base_score >= 0.7,
                'dimension_scores': {
                    'strategic_fit': base_score,
                    'financial_potential': base_score + 0.05,
                    'risk_assessment': max(base_score - 0.1, 0.0)
                },
                'scored_at': datetime.now().isoformat(),
                'scorer_version': 'integrated_ai_lite_v1.0'
            }
            
        except Exception as e:
            logger.error(f"Error in AI Lite scoring: {str(e)}")
            return {
                'overall_score': 0.5,
                'confidence_level': 0.3,
                'auto_promotion_eligible': False,
                'error': str(e)
            }

    async def batch_analyze_opportunities(self, opportunities: List[Dict[str, Any]],
                                        include_research: bool = True,
                                        report_type: ReportFormat = ReportFormat.EXECUTIVE_SUMMARY,
                                        batch_size: Optional[int] = None) -> BatchAnalysisResult:
        """
        Perform batch analysis of multiple opportunities with cost optimization
        
        Args:
            opportunities: List of opportunities to analyze
            include_research: Whether to include research analysis
            report_type: Type of research report to generate
            batch_size: Size of processing batches (auto-determined if None)
            
        Returns:
            Batch analysis results
        """
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting batch analysis {batch_id} for {len(opportunities)} opportunities")
        
        start_time = datetime.now()
        
        # Determine optimal batch size
        if batch_size is None:
            batch_size = 5 if self.cost_optimization else 10
        
        result = BatchAnalysisResult(
            batch_id=batch_id,
            total_opportunities=len(opportunities),
            successful_analyses=0,
            failed_analyses=0,
            integrated_analyses=[],
            cost_optimization_enabled=self.cost_optimization
        )
        
        # Process in batches
        for i in range(0, len(opportunities), batch_size):
            batch = opportunities[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} with {len(batch)} opportunities")
            
            # Process batch concurrently
            batch_tasks = [
                self.analyze_opportunity_integrated(opp, include_research, report_type)
                for opp in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for j, analysis_result in enumerate(batch_results):
                if isinstance(analysis_result, IntegratedAnalysis):
                    result.integrated_analyses.append(analysis_result)
                    if analysis_result.recommended_action != "error_review_required":
                        result.successful_analyses += 1
                    else:
                        result.failed_analyses += 1
                else:
                    result.failed_analyses += 1
                    result.error_log.append({
                        'opportunity_index': i + j,
                        'opportunity_id': batch[j].get('opportunity_id', 'unknown'),
                        'error': str(analysis_result)
                    })
            
            # Cost optimization delay between batches
            if self.cost_optimization and i + batch_size < len(opportunities):
                await asyncio.sleep(2)  # 2 second delay between batches
        
        # Calculate batch metrics
        result.batch_completed = datetime.now()
        result.total_processing_time = (result.batch_completed - start_time).total_seconds()
        
        if result.successful_analyses > 0:
            result.average_processing_time = (
                sum(a.processing_time for a in result.integrated_analyses) / result.successful_analyses
            )
            
            result.total_cost = sum(
                a.cost_breakdown.get('total_cost', 0.0) for a in result.integrated_analyses
            )
            result.average_cost_per_opportunity = result.total_cost / result.successful_analyses
            
            result.average_confidence = sum(
                a.integrated_confidence for a in result.integrated_analyses
            ) / result.successful_analyses
        
        # Calculate quality distribution
        result.quality_distribution = self._calculate_quality_distribution(result.integrated_analyses)
        
        logger.info(f"Batch analysis {batch_id} completed. "
                   f"Success rate: {result.successful_analyses}/{result.total_opportunities}, "
                   f"Total cost: ${result.total_cost:.4f}, "
                   f"Processing time: {result.total_processing_time:.2f}s")
        
        return result

    def _calculate_quality_distribution(self, analyses: List[IntegratedAnalysis]) -> Dict[str, int]:
        """Calculate distribution of analysis quality"""
        distribution = {
            'high_quality': 0,    # >= 0.8
            'medium_quality': 0,  # 0.6 - 0.8
            'low_quality': 0,     # < 0.6
            'error': 0
        }
        
        for analysis in analyses:
            if analysis.recommended_action == "error_review_required":
                distribution['error'] += 1
            elif analysis.integrated_confidence >= 0.8:
                distribution['high_quality'] += 1
            elif analysis.integrated_confidence >= 0.6:
                distribution['medium_quality'] += 1
            else:
                distribution['low_quality'] += 1
        
        return distribution

    def _update_performance_metrics(self, analysis: IntegratedAnalysis, success: bool):
        """Update performance tracking metrics"""
        self.performance_metrics['total_analyses'] += 1
        
        if success:
            self.performance_metrics['successful_analyses'] += 1
            self.performance_metrics['total_cost'] += analysis.cost_breakdown.get('total_cost', 0.0)
            self.performance_metrics['total_processing_time'] += analysis.processing_time
            
            # Update average quality score
            current_avg = self.performance_metrics['average_quality_score']
            total_successful = self.performance_metrics['successful_analyses']
            
            self.performance_metrics['average_quality_score'] = (
                (current_avg * (total_successful - 1) + analysis.integrated_confidence) / total_successful
            )
        else:
            self.performance_metrics['failed_analyses'] += 1

    async def generate_team_decision_package(self, analysis: IntegratedAnalysis) -> Dict[str, Any]:
        """
        Generate comprehensive decision package for grant teams
        
        Args:
            analysis: Integrated analysis results
            
        Returns:
            Complete decision package
        """
        logger.info(f"Generating team decision package for {analysis.organization_name}")
        
        # Generate all report types
        opportunity_data = {
            'opportunity_id': analysis.opportunity_id,
            'organization_name': analysis.organization_name,
            'scoring': analysis.scoring_results,
            'current_stage': 'analyze',  # Current stage for decision package
            'funding_amount': analysis.scoring_results.get('funding_amount'),
            'analysis': {
                'integrated_analysis': {
                    'integrated_score': analysis.integrated_score,
                    'integrated_confidence': analysis.integrated_confidence,
                    'evidence_strength': analysis.evidence_strength,
                    'research_impact_factor': analysis.research_impact_factor
                }
            }
        }
        
        # Add research data if available
        research_data = None
        if analysis.research_report:
            research_data = {
                'contacts_identified': [
                    {
                        'name': contact.name,
                        'title': contact.title,
                        'email': contact.email,
                        'phone': contact.phone,
                        'confidence': contact.confidence
                    }
                    for contact in analysis.research_report.contacts_identified
                ],
                'evidence_package': [
                    {
                        'fact': fact.fact,
                        'source': fact.source,
                        'confidence': fact.confidence,
                        'category': fact.category
                    }
                    for fact in analysis.research_report.evidence_package
                ],
                'confidence_assessment': analysis.research_report.confidence_assessment
            }
        
        # Generate templates
        executive_summary = self.template_system.generate_executive_summary_template(
            opportunity_data, research_data
        )
        
        decision_brief = self.template_system.generate_decision_brief_template(
            opportunity_data
        )
        
        evaluation_summary = self.template_system.generate_evaluation_summary_template(
            opportunity_data
        )
        
        evidence_package = self.template_system.generate_evidence_package_template(
            opportunity_data, research_data
        )
        
        # Compile decision package
        decision_package = {
            'package_id': f"decision_pkg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'opportunity_id': analysis.opportunity_id,
            'organization_name': analysis.organization_name,
            'generated_at': datetime.now().isoformat(),
            
            # Integrated Analysis Summary
            'integrated_analysis': {
                'integrated_score': analysis.integrated_score,
                'integrated_confidence': analysis.integrated_confidence,
                'recommended_action': analysis.recommended_action,
                'decision_confidence': analysis.decision_confidence,
                'evidence_strength': analysis.evidence_strength,
                'next_steps': analysis.next_steps,
                'risk_factors': analysis.risk_factors
            },
            
            # Report Templates
            'reports': {
                'executive_summary': executive_summary,
                'decision_brief': decision_brief,
                'evaluation_summary': evaluation_summary,
                'evidence_package': evidence_package
            },
            
            # Research Results
            'research_results': {
                'research_report': analysis.research_report.__dict__ if analysis.research_report else None,
                'research_quality_score': analysis.research_quality_score,
                'research_confidence': analysis.research_confidence
            },
            
            # Cost and Performance
            'cost_breakdown': analysis.cost_breakdown,
            'processing_metrics': {
                'processing_time': analysis.processing_time,
                'analysis_timestamp': analysis.analysis_timestamp.isoformat()
            }
        }
        
        logger.info(f"Team decision package generated for {analysis.organization_name}")
        return decision_package

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            'performance_metrics': self.performance_metrics.copy(),
            'integration_weights': self.integration_weights.copy(),
            'quality_threshold': self.quality_threshold,
            'cost_optimization_enabled': self.cost_optimization,
            'component_status': {
                'research_platform': 'operational',
                'template_system': 'operational',
                'ai_lite_scorer': 'operational'
            }
        }

    async def export_batch_results(self, batch_result: BatchAnalysisResult, 
                                 format: str = 'json') -> str:
        """
        Export batch analysis results
        
        Args:
            batch_result: Batch results to export
            format: Export format ('json', 'csv')
            
        Returns:
            Export data or file path
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'json':
            export_data = {
                'batch_summary': {
                    'batch_id': batch_result.batch_id,
                    'total_opportunities': batch_result.total_opportunities,
                    'successful_analyses': batch_result.successful_analyses,
                    'failed_analyses': batch_result.failed_analyses,
                    'success_rate': batch_result.successful_analyses / batch_result.total_opportunities,
                    'total_processing_time': batch_result.total_processing_time,
                    'total_cost': batch_result.total_cost,
                    'average_cost_per_opportunity': batch_result.average_cost_per_opportunity,
                    'quality_distribution': batch_result.quality_distribution
                },
                'analyses': [
                    {
                        'opportunity_id': analysis.opportunity_id,
                        'organization_name': analysis.organization_name,
                        'integrated_score': analysis.integrated_score,
                        'integrated_confidence': analysis.integrated_confidence,
                        'recommended_action': analysis.recommended_action,
                        'decision_confidence': analysis.decision_confidence,
                        'processing_time': analysis.processing_time,
                        'cost_breakdown': analysis.cost_breakdown
                    }
                    for analysis in batch_result.integrated_analyses
                ],
                'errors': batch_result.error_log,
                'export_timestamp': timestamp
            }
            
            logger.info(f"Batch results exported to JSON format")
            return json.dumps(export_data, indent=2)
        
        else:
            raise ValueError(f"Export format {format} not supported")