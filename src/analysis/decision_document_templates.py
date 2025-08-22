"""
Decision-Ready Document Templates
Phase 4: AI Heavy Dossier Builder

This module provides comprehensive document templates for decision-ready materials,
including executive briefs, implementation blueprints, risk assessments, and 
strategic intelligence reports.

Key Features:
- Executive decision brief templates
- Implementation blueprint formats
- Risk mitigation plan templates
- Resource requirement analysis templates
- Success factor documentation
- Audit trail and compliance templates
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import uuid

from .ai_heavy_dossier_builder import (
    ComprehensiveDossier, ExecutiveDecision, ImplementationBlueprint,
    RelationshipIntelligence, SuccessFactorAnalysis, DossierType, DecisionStatus
)

logger = logging.getLogger(__name__)


class DocumentFormat(Enum):
    """Available document formats"""
    EXECUTIVE_BRIEF = "executive_brief"
    DETAILED_REPORT = "detailed_report"
    PRESENTATION = "presentation"
    DASHBOARD = "dashboard"
    COMPLIANCE_REPORT = "compliance_report"


class AudienceType(Enum):
    """Target audience types"""
    EXECUTIVES = "executives"
    BOARD_MEMBERS = "board_members"
    IMPLEMENTATION_TEAM = "implementation_team"
    STAKEHOLDERS = "stakeholders"
    COMPLIANCE_TEAM = "compliance_team"


@dataclass
class DocumentTemplate:
    """Document template structure"""
    template_id: str
    template_name: str
    document_format: DocumentFormat
    target_audience: AudienceType
    sections: List[Dict[str, Any]]
    formatting_rules: Dict[str, Any]
    required_data: List[str]
    optional_data: List[str]
    template_version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GeneratedDocument:
    """Generated document from template"""
    document_id: str
    template_id: str
    dossier_id: str
    document_format: DocumentFormat
    target_audience: AudienceType
    title: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.now)
    generated_by: str = "decision_document_generator"
    quality_score: float = 0.0
    approval_status: str = "draft"


class DecisionDocumentTemplates:
    """
    Comprehensive document template system for decision-ready materials
    
    Generates professional documents for different audiences and purposes
    from comprehensive dossier data.
    """
    
    def __init__(self):
        """Initialize document template system"""
        self.template_registry = {}
        self.generated_documents = {}
        
        # Initialize standard templates
        self._initialize_standard_templates()
        
        # Document generation statistics
        self.generation_stats = {
            'documents_generated': 0,
            'templates_used': {},
            'audience_distribution': {},
            'format_distribution': {},
            'average_quality_score': 0.0
        }

    def _initialize_standard_templates(self):
        """Initialize standard document templates"""
        
        # Executive Decision Brief Template
        self.template_registry['executive_decision_brief'] = DocumentTemplate(
            template_id='executive_decision_brief',
            template_name='Executive Decision Brief',
            document_format=DocumentFormat.EXECUTIVE_BRIEF,
            target_audience=AudienceType.EXECUTIVES,
            sections=[
                {
                    'section_id': 'executive_summary',
                    'title': 'Executive Summary',
                    'content_type': 'summary',
                    'max_length': 500,
                    'required': True,
                    'data_sources': ['executive_decision', 'integrated_analysis']
                },
                {
                    'section_id': 'recommendation',
                    'title': 'Decision Recommendation',
                    'content_type': 'recommendation',
                    'max_length': 300,
                    'required': True,
                    'data_sources': ['executive_decision']
                },
                {
                    'section_id': 'key_factors',
                    'title': 'Key Decision Factors',
                    'content_type': 'bullet_list',
                    'max_items': 7,
                    'required': True,
                    'data_sources': ['executive_decision', 'success_factor_analysis']
                },
                {
                    'section_id': 'risk_assessment',
                    'title': 'Risk Assessment',
                    'content_type': 'risk_matrix',
                    'required': True,
                    'data_sources': ['risk_analysis', 'executive_decision']
                },
                {
                    'section_id': 'financial_impact',
                    'title': 'Financial Impact',
                    'content_type': 'financial_summary',
                    'required': True,
                    'data_sources': ['financial_projections', 'resource_analysis']
                },
                {
                    'section_id': 'next_steps',
                    'title': 'Recommended Next Steps',
                    'content_type': 'action_items',
                    'max_items': 5,
                    'required': True,
                    'data_sources': ['executive_decision', 'implementation_blueprint']
                }
            ],
            formatting_rules={
                'page_limit': 3,
                'font_size': 11,
                'include_charts': True,
                'executive_summary_first': True,
                'highlight_recommendations': True
            },
            required_data=['executive_decision', 'integrated_analysis'],
            optional_data=['success_factor_analysis', 'risk_analysis', 'financial_projections']
        )
        
        # Implementation Blueprint Template
        self.template_registry['implementation_blueprint'] = DocumentTemplate(
            template_id='implementation_blueprint',
            template_name='Implementation Blueprint',
            document_format=DocumentFormat.DETAILED_REPORT,
            target_audience=AudienceType.IMPLEMENTATION_TEAM,
            sections=[
                {
                    'section_id': 'project_overview',
                    'title': 'Project Overview',
                    'content_type': 'overview',
                    'required': True,
                    'data_sources': ['implementation_blueprint', 'executive_decision']
                },
                {
                    'section_id': 'implementation_phases',
                    'title': 'Implementation Phases',
                    'content_type': 'phase_timeline',
                    'required': True,
                    'data_sources': ['implementation_blueprint']
                },
                {
                    'section_id': 'detailed_steps',
                    'title': 'Detailed Implementation Steps',
                    'content_type': 'step_by_step',
                    'required': True,
                    'data_sources': ['implementation_blueprint']
                },
                {
                    'section_id': 'resource_requirements',
                    'title': 'Resource Requirements',
                    'content_type': 'resource_breakdown',
                    'required': True,
                    'data_sources': ['implementation_blueprint', 'resource_analysis']
                },
                {
                    'section_id': 'risk_mitigation',
                    'title': 'Risk Mitigation Plan',
                    'content_type': 'risk_mitigation_matrix',
                    'required': True,
                    'data_sources': ['implementation_blueprint', 'risk_analysis']
                },
                {
                    'section_id': 'success_metrics',
                    'title': 'Success Metrics and KPIs',
                    'content_type': 'metrics_dashboard',
                    'required': True,
                    'data_sources': ['success_factor_analysis', 'implementation_blueprint']
                },
                {
                    'section_id': 'stakeholder_communication',
                    'title': 'Stakeholder Communication Plan',
                    'content_type': 'communication_matrix',
                    'required': True,
                    'data_sources': ['implementation_blueprint', 'relationship_intelligence']
                }
            ],
            formatting_rules={
                'page_limit': 15,
                'include_gantt_chart': True,
                'include_risk_matrix': True,
                'detailed_appendices': True
            },
            required_data=['implementation_blueprint'],
            optional_data=['resource_analysis', 'risk_analysis', 'success_factor_analysis', 'relationship_intelligence']
        )
        
        # Strategic Intelligence Report Template
        self.template_registry['strategic_intelligence'] = DocumentTemplate(
            template_id='strategic_intelligence',
            template_name='Strategic Intelligence Report',
            document_format=DocumentFormat.DETAILED_REPORT,
            target_audience=AudienceType.STAKEHOLDERS,
            sections=[
                {
                    'section_id': 'intelligence_summary',
                    'title': 'Intelligence Summary',
                    'content_type': 'intelligence_brief',
                    'required': True,
                    'data_sources': ['relationship_intelligence', 'success_factor_analysis']
                },
                {
                    'section_id': 'relationship_mapping',
                    'title': 'Relationship Mapping',
                    'content_type': 'network_diagram',
                    'required': True,
                    'data_sources': ['relationship_intelligence']
                },
                {
                    'section_id': 'engagement_strategy',
                    'title': 'Engagement Strategy',
                    'content_type': 'strategy_framework',
                    'required': True,
                    'data_sources': ['relationship_intelligence']
                },
                {
                    'section_id': 'competitive_analysis',
                    'title': 'Competitive Analysis',
                    'content_type': 'competitive_matrix',
                    'required': True,
                    'data_sources': ['success_factor_analysis', 'integrated_analysis']
                },
                {
                    'section_id': 'market_positioning',
                    'title': 'Market Positioning',
                    'content_type': 'positioning_analysis',
                    'required': True,
                    'data_sources': ['success_factor_analysis']
                }
            ],
            formatting_rules={
                'page_limit': 12,
                'include_network_diagrams': True,
                'confidentiality_notice': True,
                'strategic_focus': True
            },
            required_data=['relationship_intelligence', 'success_factor_analysis'],
            optional_data=['integrated_analysis']
        )
        
        # Risk Assessment Report Template
        self.template_registry['risk_assessment_report'] = DocumentTemplate(
            template_id='risk_assessment_report',
            template_name='Risk Assessment Report',
            document_format=DocumentFormat.COMPLIANCE_REPORT,
            target_audience=AudienceType.COMPLIANCE_TEAM,
            sections=[
                {
                    'section_id': 'risk_overview',
                    'title': 'Risk Assessment Overview',
                    'content_type': 'risk_summary',
                    'required': True,
                    'data_sources': ['risk_analysis', 'executive_decision']
                },
                {
                    'section_id': 'risk_identification',
                    'title': 'Risk Identification and Classification',
                    'content_type': 'risk_taxonomy',
                    'required': True,
                    'data_sources': ['risk_analysis']
                },
                {
                    'section_id': 'risk_assessment_matrix',
                    'title': 'Risk Assessment Matrix',
                    'content_type': 'risk_matrix',
                    'required': True,
                    'data_sources': ['risk_analysis']
                },
                {
                    'section_id': 'mitigation_strategies',
                    'title': 'Risk Mitigation Strategies',
                    'content_type': 'mitigation_plan',
                    'required': True,
                    'data_sources': ['risk_analysis', 'implementation_blueprint']
                },
                {
                    'section_id': 'monitoring_framework',
                    'title': 'Risk Monitoring Framework',
                    'content_type': 'monitoring_plan',
                    'required': True,
                    'data_sources': ['risk_analysis', 'compliance_framework']
                }
            ],
            formatting_rules={
                'page_limit': 10,
                'compliance_format': True,
                'risk_color_coding': True,
                'formal_language': True
            },
            required_data=['risk_analysis'],
            optional_data=['executive_decision', 'implementation_blueprint', 'compliance_framework']
        )
        
        # Board Presentation Template
        self.template_registry['board_presentation'] = DocumentTemplate(
            template_id='board_presentation',
            template_name='Board Presentation',
            document_format=DocumentFormat.PRESENTATION,
            target_audience=AudienceType.BOARD_MEMBERS,
            sections=[
                {
                    'section_id': 'opportunity_overview',
                    'title': 'Opportunity Overview',
                    'content_type': 'slide_overview',
                    'slide_count': 2,
                    'required': True,
                    'data_sources': ['executive_decision', 'integrated_analysis']
                },
                {
                    'section_id': 'strategic_alignment',
                    'title': 'Strategic Alignment',
                    'content_type': 'alignment_slides',
                    'slide_count': 3,
                    'required': True,
                    'data_sources': ['success_factor_analysis', 'executive_decision']
                },
                {
                    'section_id': 'financial_analysis',
                    'title': 'Financial Analysis',
                    'content_type': 'financial_slides',
                    'slide_count': 3,
                    'required': True,
                    'data_sources': ['financial_projections', 'resource_analysis']
                },
                {
                    'section_id': 'risk_assessment',
                    'title': 'Risk Assessment',
                    'content_type': 'risk_slides',
                    'slide_count': 2,
                    'required': True,
                    'data_sources': ['risk_analysis', 'executive_decision']
                },
                {
                    'section_id': 'recommendation',
                    'title': 'Recommendation',
                    'content_type': 'recommendation_slide',
                    'slide_count': 1,
                    'required': True,
                    'data_sources': ['executive_decision']
                },
                {
                    'section_id': 'next_steps',
                    'title': 'Next Steps',
                    'content_type': 'action_slides',
                    'slide_count': 1,
                    'required': True,
                    'data_sources': ['executive_decision', 'implementation_blueprint']
                }
            ],
            formatting_rules={
                'total_slides': 12,
                'executive_format': True,
                'visual_heavy': True,
                'minimal_text': True,
                'professional_design': True
            },
            required_data=['executive_decision', 'integrated_analysis'],
            optional_data=['success_factor_analysis', 'financial_projections', 'risk_analysis', 'implementation_blueprint']
        )

    def generate_document(self, dossier: ComprehensiveDossier, 
                         template_id: str,
                         customizations: Optional[Dict[str, Any]] = None) -> GeneratedDocument:
        """
        Generate document from dossier using specified template
        
        Args:
            dossier: Comprehensive dossier to generate document from
            template_id: ID of template to use
            customizations: Optional customizations to apply
            
        Returns:
            Generated document
        """
        
        if template_id not in self.template_registry:
            raise ValueError(f"Template {template_id} not found")
        
        template = self.template_registry[template_id]
        
        logger.info(f"Generating {template.template_name} for {dossier.organization_name}")
        
        try:
            # Generate document content
            content = self._generate_document_content(dossier, template, customizations)
            
            # Create document metadata
            metadata = self._create_document_metadata(dossier, template)
            
            # Calculate quality score
            quality_score = self._calculate_document_quality(content, template)
            
            # Create generated document
            document = GeneratedDocument(
                document_id=f"doc_{uuid.uuid4().hex[:12]}",
                template_id=template_id,
                dossier_id=dossier.dossier_id,
                document_format=template.document_format,
                target_audience=template.target_audience,
                title=f"{template.template_name}: {dossier.organization_name}",
                content=content,
                metadata=metadata,
                quality_score=quality_score
            )
            
            # Store and update statistics
            self.generated_documents[document.document_id] = document
            self._update_generation_stats(document, template)
            
            logger.info(f"Document generated: {document.title} (Quality: {quality_score:.3f})")
            
            return document
            
        except Exception as e:
            logger.error(f"Error generating document: {str(e)}")
            raise

    def _generate_document_content(self, dossier: ComprehensiveDossier, 
                                 template: DocumentTemplate,
                                 customizations: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate document content based on template and dossier data"""
        
        content = {
            'header': {
                'title': f"{template.template_name}: {dossier.organization_name}",
                'subtitle': f"Generated on {datetime.now().strftime('%B %d, %Y')}",
                'organization': dossier.organization_name,
                'opportunity_id': dossier.opportunity_id,
                'dossier_type': dossier.dossier_type.value
            },
            'sections': {}
        }
        
        # Generate each section
        for section in template.sections:
            section_content = self._generate_section_content(
                section, dossier, customizations
            )
            content['sections'][section['section_id']] = section_content
        
        # Apply formatting rules
        content['formatting'] = template.formatting_rules
        
        return content

    def _generate_section_content(self, section: Dict[str, Any], 
                                dossier: ComprehensiveDossier,
                                customizations: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate content for a specific section"""
        
        section_id = section['section_id']
        content_type = section['content_type']
        data_sources = section['data_sources']
        
        # Extract relevant data from dossier
        section_data = self._extract_section_data(dossier, data_sources)
        
        # Generate content based on type
        if content_type == 'summary':
            return self._generate_summary_content(section_data, section)
        elif content_type == 'recommendation':
            return self._generate_recommendation_content(section_data, section)
        elif content_type == 'bullet_list':
            return self._generate_bullet_list_content(section_data, section)
        elif content_type == 'risk_matrix':
            return self._generate_risk_matrix_content(section_data, section)
        elif content_type == 'financial_summary':
            return self._generate_financial_summary_content(section_data, section)
        elif content_type == 'action_items':
            return self._generate_action_items_content(section_data, section)
        elif content_type == 'phase_timeline':
            return self._generate_phase_timeline_content(section_data, section)
        elif content_type == 'step_by_step':
            return self._generate_step_by_step_content(section_data, section)
        elif content_type == 'resource_breakdown':
            return self._generate_resource_breakdown_content(section_data, section)
        elif content_type == 'network_diagram':
            return self._generate_network_diagram_content(section_data, section)
        elif content_type == 'strategy_framework':
            return self._generate_strategy_framework_content(section_data, section)
        else:
            return self._generate_generic_content(section_data, section)

    def _extract_section_data(self, dossier: ComprehensiveDossier, 
                            data_sources: List[str]) -> Dict[str, Any]:
        """Extract relevant data from dossier for section"""
        
        data = {}
        
        for source in data_sources:
            if source == 'executive_decision' and dossier.executive_decision:
                data['executive_decision'] = dossier.executive_decision
            elif source == 'integrated_analysis' and dossier.integrated_analysis:
                data['integrated_analysis'] = dossier.integrated_analysis
            elif source == 'implementation_blueprint' and dossier.implementation_blueprint:
                data['implementation_blueprint'] = dossier.implementation_blueprint
            elif source == 'relationship_intelligence' and dossier.relationship_intelligence:
                data['relationship_intelligence'] = dossier.relationship_intelligence
            elif source == 'success_factor_analysis' and dossier.success_factor_analysis:
                data['success_factor_analysis'] = dossier.success_factor_analysis
            elif source == 'risk_analysis':
                data['risk_analysis'] = dossier.risk_analysis
            elif source == 'resource_analysis':
                data['resource_analysis'] = dossier.resource_analysis
            elif source == 'financial_projections':
                data['financial_projections'] = dossier.financial_projections
            elif source == 'compliance_framework':
                data['compliance_framework'] = dossier.compliance_framework
        
        return data

    # Content generation methods for different content types
    
    def _generate_summary_content(self, data: Dict[str, Any], 
                                section: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary content"""
        
        summary_parts = []
        
        if 'executive_decision' in data:
            exec_decision = data['executive_decision']
            summary_parts.append(f"Decision Recommendation: {exec_decision.decision.value.replace('_', ' ').title()}")
            summary_parts.append(f"Confidence Level: {exec_decision.confidence_level:.1%}")
            summary_parts.append(f"Success Probability: {exec_decision.success_probability:.1%}")
        
        if 'integrated_analysis' in data:
            analysis = data['integrated_analysis']
            summary_parts.append(f"Strategic Compatibility: {analysis.integrated_score:.1%}")
            summary_parts.append(f"Evidence Strength: {analysis.evidence_strength:.1%}")
        
        return {
            'content_type': 'summary',
            'summary_text': ' | '.join(summary_parts),
            'key_points': summary_parts,
            'word_count': len(' '.join(summary_parts).split())
        }

    def _generate_recommendation_content(self, data: Dict[str, Any], 
                                       section: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendation content"""
        
        if 'executive_decision' in data:
            exec_decision = data['executive_decision']
            return {
                'content_type': 'recommendation',
                'primary_recommendation': exec_decision.decision.value.replace('_', ' ').title(),
                'rationale': exec_decision.decision_rationale,
                'confidence_level': exec_decision.confidence_level,
                'implementation_priority': exec_decision.implementation_priority,
                'timeline_recommendation': exec_decision.timeline_recommendation
            }
        else:
            return {
                'content_type': 'recommendation',
                'primary_recommendation': 'Pending Analysis',
                'rationale': 'Comprehensive analysis required',
                'confidence_level': 0.5,
                'implementation_priority': 'medium',
                'timeline_recommendation': 'TBD'
            }

    def _generate_bullet_list_content(self, data: Dict[str, Any], 
                                    section: Dict[str, Any]) -> Dict[str, Any]:
        """Generate bullet list content"""
        
        items = []
        
        if 'executive_decision' in data:
            items.extend(data['executive_decision'].key_factors)
        
        if 'success_factor_analysis' in data:
            success_analysis = data['success_factor_analysis']
            items.extend([f['factor'] for f in success_analysis.critical_success_factors[:3]])
        
        # Limit items based on section constraints
        max_items = section.get('max_items', 10)
        items = items[:max_items]
        
        return {
            'content_type': 'bullet_list',
            'items': items,
            'item_count': len(items),
            'formatted_list': '\n'.join(f'• {item}' for item in items)
        }

    def _generate_risk_matrix_content(self, data: Dict[str, Any], 
                                    section: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk matrix content"""
        
        risk_items = []
        
        if 'risk_analysis' in data:
            risk_analysis = data['risk_analysis']
            for category, risks in risk_analysis.get('risk_categories', {}).items():
                for risk in risks:
                    risk_items.append({
                        'risk': risk,
                        'category': category,
                        'probability': 'Medium',  # Simplified for template
                        'impact': 'Medium',
                        'severity': 'Medium'
                    })
        
        return {
            'content_type': 'risk_matrix',
            'risk_items': risk_items,
            'risk_count': len(risk_items),
            'overall_risk_level': data.get('risk_analysis', {}).get('overall_risk_rating', 'medium')
        }

    def _generate_financial_summary_content(self, data: Dict[str, Any], 
                                          section: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financial summary content"""
        
        if 'financial_projections' in data:
            projections = data['financial_projections']
            return {
                'content_type': 'financial_summary',
                'cost_projections': projections.get('cost_projections', {}),
                'benefit_projections': projections.get('benefit_projections', {}),
                'roi_projection': projections.get('benefit_projections', {}).get('roi_projection', 'TBD'),
                'financial_scenarios': projections.get('financial_scenarios', {})
            }
        else:
            return {
                'content_type': 'financial_summary',
                'cost_projections': {'total_3_year': 'TBD'},
                'benefit_projections': {'roi_projection': 'TBD'},
                'roi_projection': 'TBD',
                'financial_scenarios': {}
            }

    def _generate_action_items_content(self, data: Dict[str, Any], 
                                     section: Dict[str, Any]) -> Dict[str, Any]:
        """Generate action items content"""
        
        action_items = []
        
        if 'executive_decision' in data:
            exec_decision = data['executive_decision']
            action_items.append({
                'action': 'Execute decision recommendation',
                'timeline': exec_decision.timeline_recommendation,
                'responsible_party': 'Executive team',
                'priority': exec_decision.implementation_priority
            })
        
        if 'implementation_blueprint' in data:
            blueprint = data['implementation_blueprint']
            for milestone in blueprint.key_milestones[:3]:
                action_items.append({
                    'action': milestone.get('description', 'Implementation milestone'),
                    'timeline': milestone.get('timeline', 'TBD'),
                    'responsible_party': milestone.get('responsible_party', 'Implementation team'),
                    'priority': 'high'
                })
        
        # Limit items
        max_items = section.get('max_items', 5)
        action_items = action_items[:max_items]
        
        return {
            'content_type': 'action_items',
            'actions': action_items,
            'action_count': len(action_items)
        }

    # Additional content generation methods for other content types...
    
    def _generate_generic_content(self, data: Dict[str, Any], 
                                section: Dict[str, Any]) -> Dict[str, Any]:
        """Generate generic content for unknown content types"""
        return {
            'content_type': 'generic',
            'section_title': section.get('title', 'Section'),
            'data_summary': f"Contains data from {len(data)} sources",
            'available_data': list(data.keys())
        }

    def _create_document_metadata(self, dossier: ComprehensiveDossier, 
                                template: DocumentTemplate) -> Dict[str, Any]:
        """Create document metadata"""
        return {
            'dossier_metadata': {
                'organization_name': dossier.organization_name,
                'opportunity_id': dossier.opportunity_id,
                'dossier_type': dossier.dossier_type.value,
                'quality_score': dossier.quality_score
            },
            'template_metadata': {
                'template_name': template.template_name,
                'template_version': template.template_version,
                'target_audience': template.target_audience.value,
                'document_format': template.document_format.value
            },
            'generation_metadata': {
                'generated_at': datetime.now().isoformat(),
                'generator_version': 'decision_document_templates_v1.0',
                'data_completeness': self._assess_data_completeness(dossier, template)
            }
        }

    def _calculate_document_quality(self, content: Dict[str, Any], 
                                  template: DocumentTemplate) -> float:
        """Calculate quality score for generated document"""
        
        quality_factors = []
        
        # Completeness score
        required_sections = [s for s in template.sections if s.get('required', False)]
        completed_sections = len([s for s in required_sections if s['section_id'] in content['sections']])
        completeness = completed_sections / len(required_sections) if required_sections else 1.0
        quality_factors.append(completeness * 0.4)
        
        # Content depth score
        total_content_items = sum(
            len(section_content.get('items', [])) if 'items' in section_content 
            else 1 for section_content in content['sections'].values()
        )
        depth_score = min(total_content_items / 10, 1.0)  # Normalized to 10 items
        quality_factors.append(depth_score * 0.3)
        
        # Data source coverage
        available_sources = len([s for s in content['sections'].values() 
                               if s.get('available_data', [])])
        coverage_score = min(available_sources / 5, 1.0)  # Normalized to 5 sources
        quality_factors.append(coverage_score * 0.3)
        
        return sum(quality_factors)

    def _assess_data_completeness(self, dossier: ComprehensiveDossier, 
                                template: DocumentTemplate) -> float:
        """Assess completeness of data for template"""
        
        required_data = template.required_data
        available_data = []
        
        if dossier.executive_decision and 'executive_decision' in required_data:
            available_data.append('executive_decision')
        if dossier.integrated_analysis and 'integrated_analysis' in required_data:
            available_data.append('integrated_analysis')
        if dossier.implementation_blueprint and 'implementation_blueprint' in required_data:
            available_data.append('implementation_blueprint')
        if dossier.relationship_intelligence and 'relationship_intelligence' in required_data:
            available_data.append('relationship_intelligence')
        if dossier.success_factor_analysis and 'success_factor_analysis' in required_data:
            available_data.append('success_factor_analysis')
        
        return len(available_data) / len(required_data) if required_data else 1.0

    def _update_generation_stats(self, document: GeneratedDocument, template: DocumentTemplate):
        """Update document generation statistics"""
        
        self.generation_stats['documents_generated'] += 1
        
        # Template usage
        template_id = template.template_id
        self.generation_stats['templates_used'][template_id] = (
            self.generation_stats['templates_used'].get(template_id, 0) + 1
        )
        
        # Audience distribution
        audience = template.target_audience.value
        self.generation_stats['audience_distribution'][audience] = (
            self.generation_stats['audience_distribution'].get(audience, 0) + 1
        )
        
        # Format distribution
        format_type = template.document_format.value
        self.generation_stats['format_distribution'][format_type] = (
            self.generation_stats['format_distribution'].get(format_type, 0) + 1
        )
        
        # Average quality score
        current_avg = self.generation_stats['average_quality_score']
        total_docs = self.generation_stats['documents_generated']
        
        self.generation_stats['average_quality_score'] = (
            (current_avg * (total_docs - 1) + document.quality_score) / total_docs
        )

    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available templates"""
        return {
            template_id: {
                'name': template.template_name,
                'format': template.document_format.value,
                'audience': template.target_audience.value,
                'sections': len(template.sections),
                'required_data': template.required_data
            }
            for template_id, template in self.template_registry.items()
        }

    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get document generation statistics"""
        return self.generation_stats.copy()

    def export_document(self, document_id: str, export_format: str = 'json') -> str:
        """Export generated document"""
        
        if document_id not in self.generated_documents:
            raise ValueError(f"Document {document_id} not found")
        
        document = self.generated_documents[document_id]
        
        if export_format == 'json':
            return json.dumps({
                'document_id': document.document_id,
                'title': document.title,
                'content': document.content,
                'metadata': document.metadata,
                'quality_score': document.quality_score,
                'generated_at': document.generated_at.isoformat()
            }, indent=2)
        else:
            raise ValueError(f"Export format {export_format} not supported")