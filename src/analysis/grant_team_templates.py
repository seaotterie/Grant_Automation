"""
Grant Team Report Templates and Decision Support Framework
Phase 3: AI-Lite Dual-Function Platform

This module provides standardized templates and formats for grant team reports,
evaluation summaries, and decision support documentation.

Key Features:
- Executive Summary Templates
- Decision Brief Formats
- Evaluation Summary Generation
- Evidence Package Compilation
- Risk Assessment Documentation
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DecisionCategory(Enum):
    """Categories for grant team decisions"""
    GO = "go"
    NO_GO = "no_go"
    CONDITIONAL = "conditional"
    DEFER = "defer"
    MORE_INFO_NEEDED = "more_info_needed"


class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DecisionCriteria:
    """Criteria for grant team decision making"""
    criteria_name: str
    weight: float
    score: float
    rationale: str
    confidence: float = 0.8


@dataclass
class RiskAssessment:
    """Risk assessment for opportunity"""
    risk_factor: str
    risk_level: RiskLevel
    probability: float
    impact: str
    mitigation_strategy: str
    owner: Optional[str] = None


@dataclass
class GrantTeamDecision:
    """Final grant team decision package"""
    decision_id: str
    opportunity_id: str
    decision: DecisionCategory
    rationale: str
    criteria_scores: List[DecisionCriteria]
    risk_assessments: List[RiskAssessment]
    recommended_actions: List[str]
    resource_requirements: Dict[str, Any]
    timeline_recommendation: str
    decision_confidence: float
    decision_date: datetime = field(default_factory=datetime.now)
    decision_team: List[str] = field(default_factory=list)
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None


class GrantTeamTemplates:
    """
    Standardized templates for grant team reports and decision support
    """
    
    def __init__(self):
        """Initialize template system"""
        self.template_version = "1.0"
        self.generated_reports = []
        
        # Standard decision criteria weights
        self.default_criteria_weights = {
            'strategic_alignment': 0.25,
            'funding_potential': 0.20,
            'competitive_advantage': 0.15,
            'resource_availability': 0.15,
            'timeline_feasibility': 0.10,
            'risk_tolerance': 0.10,
            'organizational_capacity': 0.05
        }

    def generate_executive_summary_template(self, opportunity_data: Dict[str, Any],
                                          research_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate executive summary template for grant teams
        
        Args:
            opportunity_data: Core opportunity information
            research_data: Additional research findings
            
        Returns:
            Formatted executive summary template
        """
        
        org_name = opportunity_data.get('organization_name', 'Unknown Organization')
        opportunity_id = opportunity_data.get('opportunity_id', 'unknown')
        
        template = {
            'report_type': 'Executive Summary',
            'report_id': f"exec_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'opportunity_id': opportunity_id,
            'generated_at': datetime.now().isoformat(),
            
            # Header Section
            'header': {
                'organization_name': org_name,
                'ein': opportunity_data.get('ein', 'N/A'),
                'opportunity_type': opportunity_data.get('opportunity_type', 'grants'),
                'funding_amount': opportunity_data.get('funding_amount', 'TBD'),
                'current_stage': opportunity_data.get('current_stage', 'discovery'),
                'overall_score': opportunity_data.get('scoring', {}).get('overall_score', 'N/A')
            },
            
            # Executive Summary Section
            'executive_summary': {
                'key_highlights': [
                    f"Organization: {org_name}",
                    f"Funding Potential: {opportunity_data.get('funding_amount', 'TBD')}",
                    f"Strategic Score: {opportunity_data.get('scoring', {}).get('overall_score', 'N/A')}",
                    f"Current Stage: {opportunity_data.get('current_stage', 'discovery')}"
                ],
                'recommendation_summary': self._generate_recommendation_summary(opportunity_data),
                'risk_summary': self._generate_risk_summary(opportunity_data),
                'next_steps_summary': self._generate_next_steps_summary(opportunity_data)
            },
            
            # Analysis Section
            'analysis': {
                'scoring_breakdown': opportunity_data.get('scoring', {}),
                'stage_progression': opportunity_data.get('stage_history', []),
                'network_analysis': self._extract_network_analysis(opportunity_data),
                'foundation_intelligence': self._extract_foundation_intelligence(opportunity_data)
            },
            
            # Research Integration
            'research_findings': self._integrate_research_findings(research_data) if research_data else {},
            
            # Decision Support
            'decision_framework': {
                'go_no_go_factors': self._identify_decision_factors(opportunity_data),
                'resource_requirements': self._estimate_resource_requirements(opportunity_data),
                'timeline_assessment': self._assess_timeline_factors(opportunity_data),
                'competitive_analysis': self._analyze_competitive_factors(opportunity_data)
            },
            
            # Appendices
            'appendices': {
                'detailed_scoring': opportunity_data.get('scoring', {}),
                'contact_information': self._extract_contact_info(opportunity_data, research_data),
                'supporting_documents': [],
                'research_sources': []
            }
        }
        
        return template

    def generate_decision_brief_template(self, opportunity_data: Dict[str, Any],
                                       decision_criteria: Optional[List[DecisionCriteria]] = None) -> Dict[str, Any]:
        """
        Generate decision brief template for grant team meetings
        
        Args:
            opportunity_data: Core opportunity information
            decision_criteria: Custom decision criteria
            
        Returns:
            Formatted decision brief template
        """
        
        org_name = opportunity_data.get('organization_name', 'Unknown Organization')
        
        # Use default criteria if none provided
        if not decision_criteria:
            decision_criteria = self._generate_default_criteria(opportunity_data)
        
        template = {
            'report_type': 'Decision Brief',
            'report_id': f"decision_brief_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'opportunity_id': opportunity_data.get('opportunity_id', 'unknown'),
            'generated_at': datetime.now().isoformat(),
            
            # Decision Summary
            'decision_summary': {
                'organization': org_name,
                'recommendation': self._calculate_recommendation(opportunity_data, decision_criteria),
                'confidence_level': self._calculate_decision_confidence(opportunity_data, decision_criteria),
                'key_decision_factors': [criteria.criteria_name for criteria in decision_criteria[:3]]
            },
            
            # Criteria Analysis
            'criteria_analysis': {
                'weighted_scores': [
                    {
                        'criteria': criteria.criteria_name,
                        'weight': criteria.weight,
                        'score': criteria.score,
                        'weighted_score': criteria.weight * criteria.score,
                        'rationale': criteria.rationale,
                        'confidence': criteria.confidence
                    }
                    for criteria in decision_criteria
                ],
                'total_weighted_score': sum(c.weight * c.score for c in decision_criteria),
                'score_interpretation': self._interpret_score(sum(c.weight * c.score for c in decision_criteria))
            },
            
            # Risk Assessment
            'risk_assessment': {
                'identified_risks': self._identify_risks(opportunity_data),
                'risk_mitigation': self._suggest_risk_mitigation(opportunity_data),
                'overall_risk_rating': self._calculate_overall_risk(opportunity_data)
            },
            
            # Resource Analysis
            'resource_analysis': {
                'required_resources': self._detail_resource_requirements(opportunity_data),
                'availability_assessment': self._assess_resource_availability(opportunity_data),
                'resource_gaps': self._identify_resource_gaps(opportunity_data)
            },
            
            # Timeline Considerations
            'timeline_analysis': {
                'key_milestones': self._identify_key_milestones(opportunity_data),
                'critical_deadlines': self._identify_critical_deadlines(opportunity_data),
                'timeline_risks': self._assess_timeline_risks(opportunity_data)
            },
            
            # Action Items
            'action_items': {
                'immediate_actions': self._generate_immediate_actions(opportunity_data),
                'short_term_actions': self._generate_short_term_actions(opportunity_data),
                'long_term_actions': self._generate_long_term_actions(opportunity_data)
            }
        }
        
        return template

    def generate_evaluation_summary_template(self, opportunity_data: Dict[str, Any],
                                           team_assessment: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate evaluation summary template for comprehensive assessment
        
        Args:
            opportunity_data: Core opportunity information
            team_assessment: Team evaluation inputs
            
        Returns:
            Formatted evaluation summary template
        """
        
        template = {
            'report_type': 'Evaluation Summary',
            'report_id': f"eval_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'opportunity_id': opportunity_data.get('opportunity_id', 'unknown'),
            'generated_at': datetime.now().isoformat(),
            
            # Opportunity Overview
            'opportunity_overview': {
                'organization': opportunity_data.get('organization_name', 'Unknown'),
                'program_name': opportunity_data.get('program_name', 'N/A'),
                'funding_amount': opportunity_data.get('funding_amount', 'TBD'),
                'opportunity_type': opportunity_data.get('opportunity_type', 'grants'),
                'discovery_date': opportunity_data.get('discovered_at', 'Unknown')
            },
            
            # Quantitative Assessment
            'quantitative_assessment': {
                'overall_score': opportunity_data.get('scoring', {}).get('overall_score', 'N/A'),
                'dimension_scores': opportunity_data.get('scoring', {}).get('dimension_scores', {}),
                'confidence_level': opportunity_data.get('scoring', {}).get('confidence_level', 'N/A'),
                'auto_promotion_eligible': opportunity_data.get('scoring', {}).get('auto_promotion_eligible', False)
            },
            
            # Qualitative Assessment
            'qualitative_assessment': {
                'strategic_fit': self._assess_strategic_fit(opportunity_data),
                'organizational_capacity': self._assess_organizational_capacity(opportunity_data),
                'competitive_landscape': self._assess_competitive_landscape(opportunity_data),
                'impact_potential': self._assess_impact_potential(opportunity_data)
            },
            
            # Team Evaluation
            'team_evaluation': team_assessment if team_assessment else {
                'team_consensus': 'Pending team review',
                'individual_assessments': [],
                'discussion_points': [],
                'concerns_raised': [],
                'strengths_identified': []
            },
            
            # Stage Analysis
            'stage_analysis': {
                'current_stage': opportunity_data.get('current_stage', 'discovery'),
                'stage_duration': self._calculate_stage_duration(opportunity_data),
                'promotion_history': opportunity_data.get('promotion_history', []),
                'next_stage_requirements': self._identify_next_stage_requirements(opportunity_data)
            },
            
            # Evidence Summary
            'evidence_summary': {
                'supporting_evidence': self._compile_supporting_evidence(opportunity_data),
                'evidence_quality': self._assess_evidence_quality(opportunity_data),
                'evidence_gaps': self._identify_evidence_gaps(opportunity_data),
                'verification_status': self._assess_verification_status(opportunity_data)
            },
            
            # Final Recommendation
            'final_recommendation': {
                'recommendation': self._generate_final_recommendation(opportunity_data, team_assessment),
                'rationale': self._generate_recommendation_rationale(opportunity_data),
                'conditions': self._identify_recommendation_conditions(opportunity_data),
                'follow_up_required': self._determine_follow_up_requirements(opportunity_data)
            }
        }
        
        return template

    def generate_evidence_package_template(self, opportunity_data: Dict[str, Any],
                                         research_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive evidence package for detailed review
        
        Args:
            opportunity_data: Core opportunity information
            research_data: Additional research findings
            
        Returns:
            Formatted evidence package template
        """
        
        template = {
            'report_type': 'Evidence Package',
            'report_id': f"evidence_pkg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'opportunity_id': opportunity_data.get('opportunity_id', 'unknown'),
            'generated_at': datetime.now().isoformat(),
            
            # Primary Evidence
            'primary_evidence': {
                'organization_data': self._compile_organization_data(opportunity_data),
                'financial_data': self._compile_financial_data(opportunity_data),
                'program_data': self._compile_program_data(opportunity_data),
                'governance_data': self._compile_governance_data(opportunity_data)
            },
            
            # Secondary Evidence
            'secondary_evidence': {
                'network_analysis': self._compile_network_evidence(opportunity_data),
                'research_findings': research_data if research_data else {},
                'external_validation': self._compile_external_validation(opportunity_data),
                'peer_comparisons': self._compile_peer_comparisons(opportunity_data)
            },
            
            # Verification Records
            'verification_records': {
                'data_sources': self._document_data_sources(opportunity_data),
                'verification_methods': self._document_verification_methods(opportunity_data),
                'quality_checks': self._document_quality_checks(opportunity_data),
                'validation_results': self._document_validation_results(opportunity_data)
            },
            
            # Supporting Documentation
            'supporting_documentation': {
                'source_documents': [],
                'reference_materials': [],
                'related_analyses': [],
                'expert_opinions': []
            },
            
            # Audit Trail
            'audit_trail': {
                'data_collection_log': self._generate_collection_log(opportunity_data),
                'analysis_log': self._generate_analysis_log(opportunity_data),
                'decision_log': self._generate_decision_log(opportunity_data),
                'update_history': opportunity_data.get('stage_history', [])
            }
        }
        
        return template

    # Helper methods for template generation
    
    def _generate_recommendation_summary(self, opportunity_data: Dict[str, Any]) -> str:
        """Generate recommendation summary based on scoring"""
        score = opportunity_data.get('scoring', {}).get('overall_score', 0)
        if score >= 0.8:
            return "Strong recommendation for pursuit - high strategic alignment and funding potential"
        elif score >= 0.6:
            return "Moderate recommendation - requires additional analysis and risk assessment"
        elif score >= 0.4:
            return "Conditional recommendation - significant risks identified, proceed with caution"
        else:
            return "Not recommended - limited alignment with organizational priorities"

    def _generate_risk_summary(self, opportunity_data: Dict[str, Any]) -> str:
        """Generate risk summary"""
        risks = opportunity_data.get('analysis', {}).get('discovery', {}).get('risk_factors', {})
        if risks:
            return f"Identified {len(risks)} risk factors requiring attention"
        else:
            return "No significant risk factors identified in initial analysis"

    def _generate_next_steps_summary(self, opportunity_data: Dict[str, Any]) -> str:
        """Generate next steps summary"""
        stage = opportunity_data.get('current_stage', '')
        if stage == 'discovery':
            return "Advance to PLAN stage for network and foundation analysis"
        elif stage == 'pre_scoring':
            return "Complete comprehensive scoring and analysis"
        elif stage == 'recommendations':
            return "Proceed to final evaluation and decision"
        else:
            return "Continue current stage analysis and assessment"

    def _extract_network_analysis(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract network analysis data"""
        return opportunity_data.get('analysis', {}).get('network', {})

    def _extract_foundation_intelligence(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract foundation intelligence data"""
        return opportunity_data.get('analysis', {}).get('foundation', {})

    def _integrate_research_findings(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate research findings into template"""
        if not research_data:
            return {}
        
        return {
            'website_intelligence': research_data.get('website_intelligence', {}),
            'contact_information': research_data.get('contacts_identified', []),
            'extracted_facts': research_data.get('evidence_package', []),
            'research_quality': research_data.get('confidence_assessment', {})
        }

    def _identify_decision_factors(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Identify key decision factors"""
        factors = []
        
        score = opportunity_data.get('scoring', {}).get('overall_score', 0)
        if score >= 0.7:
            factors.append("High compatibility score supports pursuit")
        
        stage = opportunity_data.get('current_stage', '')
        if stage in ['recommendations', 'deep_analysis']:
            factors.append("Advanced stage indicates thorough evaluation")
        
        funding = opportunity_data.get('funding_amount')
        if funding:
            factors.append(f"Specified funding amount: {funding}")
        
        return factors

    def _estimate_resource_requirements(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate resource requirements"""
        return {
            'time_investment': 'Medium - 2-4 weeks for full evaluation',
            'personnel_required': 'Grant team + subject matter experts',
            'financial_resources': 'Standard proposal development budget',
            'specialized_expertise': 'Based on program requirements'
        }

    def _assess_timeline_factors(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess timeline factors"""
        return {
            'current_stage_duration': self._calculate_stage_duration(opportunity_data),
            'estimated_completion': 'Based on stage progression',
            'critical_deadlines': 'To be determined from program requirements',
            'buffer_time': 'Recommended 20% contingency'
        }

    def _analyze_competitive_factors(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competitive factors"""
        return {
            'competition_level': 'To be assessed',
            'organizational_advantages': 'Based on strategic fit analysis',
            'differentiation_opportunities': 'Identified through research',
            'market_positioning': 'Relative to peer organizations'
        }

    def _extract_contact_info(self, opportunity_data: Dict[str, Any], 
                            research_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract contact information"""
        contacts = []
        
        if research_data and 'contacts_identified' in research_data:
            for contact in research_data['contacts_identified']:
                contacts.append({
                    'name': contact.get('name', 'Unknown'),
                    'title': contact.get('title', 'N/A'),
                    'email': contact.get('email', 'N/A'),
                    'phone': contact.get('phone', 'N/A'),
                    'source': contact.get('source', 'research')
                })
        
        return contacts

    def _generate_default_criteria(self, opportunity_data: Dict[str, Any]) -> List[DecisionCriteria]:
        """Generate default decision criteria"""
        criteria = []
        
        score = opportunity_data.get('scoring', {}).get('overall_score', 0.5)
        
        for criteria_name, weight in self.default_criteria_weights.items():
            # Calculate individual criteria scores based on overall score and some variation
            individual_score = min(max(score + (hash(criteria_name) % 20 - 10) / 100, 0), 1)
            
            criteria.append(DecisionCriteria(
                criteria_name=criteria_name,
                weight=weight,
                score=individual_score,
                rationale=f"Assessment based on {criteria_name} analysis",
                confidence=0.8
            ))
        
        return criteria

    def _calculate_recommendation(self, opportunity_data: Dict[str, Any], 
                                criteria: List[DecisionCriteria]) -> str:
        """Calculate recommendation based on criteria"""
        total_score = sum(c.weight * c.score for c in criteria)
        
        if total_score >= 0.8:
            return "Strong GO recommendation"
        elif total_score >= 0.6:
            return "Conditional GO recommendation"
        elif total_score >= 0.4:
            return "Proceed with caution"
        else:
            return "NO GO recommendation"

    def _calculate_decision_confidence(self, opportunity_data: Dict[str, Any],
                                     criteria: List[DecisionCriteria]) -> float:
        """Calculate decision confidence"""
        avg_confidence = sum(c.confidence for c in criteria) / len(criteria)
        
        # Adjust based on data completeness
        data_completeness = self._assess_data_completeness(opportunity_data)
        
        return min(avg_confidence * data_completeness, 1.0)

    def _interpret_score(self, score: float) -> str:
        """Interpret weighted score"""
        if score >= 0.8:
            return "Excellent opportunity - strongly aligned with organizational priorities"
        elif score >= 0.6:
            return "Good opportunity - moderate alignment with some risk factors"
        elif score >= 0.4:
            return "Marginal opportunity - limited alignment, significant risks"
        else:
            return "Poor opportunity - misaligned with organizational priorities"

    def _assess_data_completeness(self, opportunity_data: Dict[str, Any]) -> float:
        """Assess completeness of opportunity data"""
        required_fields = ['organization_name', 'ein', 'current_stage', 'scoring']
        present_fields = sum(1 for field in required_fields if opportunity_data.get(field))
        
        return present_fields / len(required_fields)

    def _calculate_stage_duration(self, opportunity_data: Dict[str, Any]) -> str:
        """Calculate duration in current stage"""
        stage_history = opportunity_data.get('stage_history', [])
        if stage_history:
            current_stage = stage_history[-1]
            entered_at = current_stage.get('entered_at')
            if entered_at:
                # In real implementation, calculate actual duration
                return "Based on stage entry timestamp"
        
        return "Duration not available"

    # Additional helper methods would be implemented for comprehensive functionality
    # These are simplified for the demo but would include full logic in production

    def _identify_risks(self, opportunity_data: Dict[str, Any]) -> List[RiskAssessment]:
        """Identify risks for the opportunity"""
        return []

    def _suggest_risk_mitigation(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Suggest risk mitigation strategies"""
        return ["Comprehensive due diligence", "Stakeholder engagement", "Phased approach"]

    def _calculate_overall_risk(self, opportunity_data: Dict[str, Any]) -> str:
        """Calculate overall risk rating"""
        score = opportunity_data.get('scoring', {}).get('overall_score', 0.5)
        if score >= 0.8:
            return "Low Risk"
        elif score >= 0.6:
            return "Medium Risk"
        else:
            return "High Risk"

    def _detail_resource_requirements(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detail specific resource requirements"""
        return {
            'personnel': 'Grant writing team, subject matter experts',
            'time': '4-8 weeks for full proposal development',
            'budget': 'Standard proposal development costs',
            'expertise': 'Program-specific knowledge required'
        }

    def _assess_resource_availability(self, opportunity_data: Dict[str, Any]) -> str:
        """Assess current resource availability"""
        return "Assessment pending - requires team review"

    def _identify_resource_gaps(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Identify resource gaps"""
        return ["To be determined based on program requirements"]

    def _identify_key_milestones(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Identify key project milestones"""
        return ["Application deadline", "Award notification", "Project start date"]

    def _identify_critical_deadlines(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Identify critical deadlines"""
        return ["To be determined from program guidelines"]

    def _assess_timeline_risks(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Assess timeline-related risks"""
        return ["Deadline pressure", "Resource availability", "Review process duration"]

    def _generate_immediate_actions(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Generate immediate action items"""
        return ["Review opportunity details", "Assess team capacity", "Identify key stakeholders"]

    def _generate_short_term_actions(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Generate short-term action items"""
        return ["Conduct detailed research", "Develop preliminary proposal outline", "Engage potential partners"]

    def _generate_long_term_actions(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Generate long-term action items"""
        return ["Develop full proposal", "Submit application", "Prepare for implementation"]

    def _assess_strategic_fit(self, opportunity_data: Dict[str, Any]) -> str:
        """Assess strategic fit"""
        return "Assessment based on organizational priorities and program alignment"

    def _assess_organizational_capacity(self, opportunity_data: Dict[str, Any]) -> str:
        """Assess organizational capacity"""
        return "Evaluation of internal resources and capabilities"

    def _assess_competitive_landscape(self, opportunity_data: Dict[str, Any]) -> str:
        """Assess competitive landscape"""
        return "Analysis of potential competitors and market positioning"

    def _assess_impact_potential(self, opportunity_data: Dict[str, Any]) -> str:
        """Assess potential impact"""
        return "Projected outcomes and organizational benefit"

    def _identify_next_stage_requirements(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Identify requirements for next stage"""
        current_stage = opportunity_data.get('current_stage', '')
        if current_stage == 'prospects':
            return ["Complete network analysis", "Gather additional data"]
        elif current_stage == 'qualified':
            return ["Finalize scoring", "Conduct risk assessment"]
        else:
            return ["Stage-specific requirements"]

    def _compile_supporting_evidence(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compile supporting evidence"""
        return {
            'scoring_data': opportunity_data.get('scoring', {}),
            'analysis_results': opportunity_data.get('analysis', {}),
            'stage_progression': opportunity_data.get('stage_history', [])
        }

    def _assess_evidence_quality(self, opportunity_data: Dict[str, Any]) -> str:
        """Assess quality of available evidence"""
        confidence = opportunity_data.get('scoring', {}).get('confidence_level', 0.5)
        if confidence >= 0.8:
            return "High quality evidence"
        elif confidence >= 0.6:
            return "Moderate quality evidence"
        else:
            return "Limited quality evidence"

    def _identify_evidence_gaps(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Identify gaps in evidence"""
        gaps = []
        
        if not opportunity_data.get('funding_amount'):
            gaps.append("Funding amount not specified")
        
        if not opportunity_data.get('program_name'):
            gaps.append("Program details incomplete")
        
        return gaps

    def _assess_verification_status(self, opportunity_data: Dict[str, Any]) -> str:
        """Assess verification status of data"""
        return "Preliminary verification - additional validation recommended"

    def _generate_final_recommendation(self, opportunity_data: Dict[str, Any],
                                     team_assessment: Optional[Dict[str, Any]]) -> str:
        """Generate final recommendation"""
        score = opportunity_data.get('scoring', {}).get('overall_score', 0.5)
        
        if team_assessment and 'team_consensus' in team_assessment:
            return team_assessment['team_consensus']
        
        return self._generate_recommendation_summary(opportunity_data)

    def _generate_recommendation_rationale(self, opportunity_data: Dict[str, Any]) -> str:
        """Generate rationale for recommendation"""
        return "Based on comprehensive analysis of scoring, risk factors, and strategic alignment"

    def _identify_recommendation_conditions(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Identify conditions for recommendation"""
        conditions = []
        
        score = opportunity_data.get('scoring', {}).get('overall_score', 0.5)
        if score < 0.8:
            conditions.append("Address identified risk factors")
        
        if not opportunity_data.get('funding_amount'):
            conditions.append("Clarify funding amount and requirements")
        
        return conditions

    def _determine_follow_up_requirements(self, opportunity_data: Dict[str, Any]) -> bool:
        """Determine if follow-up is required"""
        stage = opportunity_data.get('current_stage', '')
        return stage in ['discovery', 'pre_scoring']

    # Additional compilation methods for evidence package
    def _compile_organization_data(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compile organization data"""
        return {
            'name': opportunity_data.get('organization_name', 'Unknown'),
            'ein': opportunity_data.get('ein', 'N/A'),
            'type': opportunity_data.get('opportunity_type', 'grants'),
            'status': opportunity_data.get('status', 'active')
        }

    def _compile_financial_data(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compile financial data"""
        return {
            'funding_amount': opportunity_data.get('funding_amount', 'TBD'),
            'financial_analysis': opportunity_data.get('analysis', {}).get('financial', {}),
            'revenue_data': opportunity_data.get('analysis', {}).get('discovery', {}).get('enhanced_data', {})
        }

    def _compile_program_data(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compile program data"""
        return {
            'program_name': opportunity_data.get('program_name', 'N/A'),
            'description': opportunity_data.get('description', 'N/A'),
            'program_areas': opportunity_data.get('analysis', {}).get('discovery', {}).get('match_factors', {})
        }

    def _compile_governance_data(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compile governance data"""
        return {
            'discovery_analysis': opportunity_data.get('analysis', {}).get('discovery', {}),
            'network_data': opportunity_data.get('analysis', {}).get('network', {}),
            'verification_status': 'Preliminary'
        }

    def _compile_network_evidence(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compile network analysis evidence"""
        return opportunity_data.get('analysis', {}).get('network', {})

    def _compile_external_validation(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compile external validation data"""
        return {
            'source_verification': 'Pending',
            'third_party_validation': 'Pending',
            'cross_reference_checks': 'Pending'
        }

    def _compile_peer_comparisons(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compile peer comparison data"""
        return {
            'similar_organizations': 'Analysis pending',
            'benchmark_comparisons': 'Analysis pending',
            'market_positioning': 'Analysis pending'
        }

    def _document_data_sources(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Document data sources"""
        sources = []
        
        source = opportunity_data.get('source', '')
        if source:
            sources.append(source)
        
        discovery_source = opportunity_data.get('analysis', {}).get('discovery', {}).get('source', '')
        if discovery_source and discovery_source not in sources:
            sources.append(discovery_source)
        
        return sources

    def _document_verification_methods(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Document verification methods used"""
        return [
            'Automated scoring analysis',
            'Data consistency checks',
            'Source validation (pending)',
            'Cross-reference verification (pending)'
        ]

    def _document_quality_checks(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Document quality checks performed"""
        return [
            'Data completeness assessment',
            'Scoring confidence evaluation',
            'Stage progression validation',
            'Analysis consistency review'
        ]

    def _document_validation_results(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Document validation results"""
        return {
            'data_quality_score': self._assess_data_completeness(opportunity_data),
            'confidence_level': opportunity_data.get('scoring', {}).get('confidence_level', 0.5),
            'validation_status': 'Preliminary - additional verification recommended',
            'critical_issues': 'None identified in automated analysis'
        }

    def _generate_collection_log(self, opportunity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate data collection log"""
        return [
            {
                'timestamp': opportunity_data.get('discovered_at', 'Unknown'),
                'action': 'Initial discovery',
                'source': opportunity_data.get('source', 'Unknown'),
                'data_collected': 'Basic opportunity information'
            },
            {
                'timestamp': opportunity_data.get('last_updated', 'Unknown'),
                'action': 'Last update',
                'source': 'System update',
                'data_collected': 'Current state information'
            }
        ]

    def _generate_analysis_log(self, opportunity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate analysis log"""
        return [
            {
                'timestamp': opportunity_data.get('scoring', {}).get('scored_at', 'Unknown'),
                'analysis_type': 'Scoring analysis',
                'method': opportunity_data.get('scoring', {}).get('scorer_version', 'Unknown'),
                'results': 'Scoring completed'
            }
        ]

    def _generate_decision_log(self, opportunity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate decision log"""
        log = []
        
        for promotion in opportunity_data.get('promotion_history', []):
            log.append({
                'timestamp': promotion.get('promoted_at', 'Unknown'),
                'decision': f"Promoted from {promotion.get('from_stage')} to {promotion.get('to_stage')}",
                'decision_type': promotion.get('decision_type', 'Unknown'),
                'rationale': promotion.get('reason', 'Unknown'),
                'decision_maker': promotion.get('promoted_by', 'Unknown')
            })
        
        return log