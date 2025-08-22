"""
PHASE 6: Comprehensive Export System
Advanced export capabilities for all reports, visualizations, and analyses
with support for multiple formats, templates, and customization options.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union, BinaryIO
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
import tempfile
import zipfile
from io import BytesIO
import base64
import uuid

# Import for document generation
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not available - PDF generation disabled")

# Import for Excel generation
try:
    import xlsxwriter
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False
    logger.warning("XlsxWriter not available - Excel generation disabled")

# Import for PowerPoint generation
try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.enum.text import PP_ALIGN
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False
    logger.warning("python-pptx not available - PowerPoint generation disabled")

from src.core.base_processor import BaseProcessor
from src.decision.decision_synthesis_framework import DecisionRecommendation
from src.visualization.advanced_visualization_framework import ChartConfiguration, DashboardLayout

logger = logging.getLogger(__name__)

class ExportFormat(Enum):
    """Supported export formats"""
    PDF_REPORT = "pdf"
    EXCEL_WORKBOOK = "xlsx"
    POWERPOINT = "pptx"
    HTML_REPORT = "html"
    JSON_DATA = "json"
    CSV_DATA = "csv"
    WORD_DOCUMENT = "docx"
    ZIP_PACKAGE = "zip"

class ReportType(Enum):
    """Types of reports that can be generated"""
    EXECUTIVE_SUMMARY = "executive"
    DETAILED_ANALYSIS = "detailed"
    DECISION_SUPPORT = "decision_support"
    COMPARATIVE_ANALYSIS = "comparative"
    PORTFOLIO_OVERVIEW = "portfolio"
    SENSITIVITY_ANALYSIS = "sensitivity"
    CUSTOM_REPORT = "custom"

class ExportTemplate(Enum):
    """Available export templates"""
    PROFESSIONAL = "professional"
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    PRESENTATION = "presentation"
    MINIMAL = "minimal"
    BRANDED = "branded"

@dataclass
class ExportConfiguration:
    """Configuration for export operations"""
    export_id: str
    format: ExportFormat
    report_type: ReportType
    template: ExportTemplate = ExportTemplate.PROFESSIONAL
    
    # Content selection
    include_visualizations: bool = True
    include_raw_data: bool = False
    include_methodology: bool = True
    include_recommendations: bool = True
    include_appendices: bool = False
    
    # Formatting options
    page_orientation: str = 'portrait'  # 'portrait', 'landscape'
    page_size: str = 'letter'          # 'letter', 'A4', 'legal'
    font_family: str = 'Helvetica'
    font_size: int = 11
    
    # Branding and customization
    organization_name: str = ''
    organization_logo: Optional[str] = None  # Path or base64
    custom_colors: Dict[str, str] = field(default_factory=dict)
    custom_styles: Dict[str, Any] = field(default_factory=dict)
    
    # Export-specific settings
    high_quality_images: bool = True
    include_interactive_elements: bool = True
    watermark: Optional[str] = None
    password_protect: bool = False
    password: Optional[str] = None
    
    # Metadata
    author: str = 'Catalynx Grant Research Platform'
    title: str = ''
    subject: str = ''
    keywords: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExportResult:
    """Result of export operation"""
    export_id: str
    success: bool
    format: ExportFormat
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    
    # Export statistics
    pages_generated: int = 0
    charts_included: int = 0
    data_rows_exported: int = 0
    processing_time: float = 0.0
    
    # Error information
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    # Additional metadata
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class PDFReportGenerator:
    """Generator for PDF reports using ReportLab"""
    
    def __init__(self):
        self.styles = None
        if REPORTLAB_AVAILABLE:
            self.styles = getSampleStyleSheet()
            self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        if not REPORTLAB_AVAILABLE:
            return
        
        # Executive summary style
        self.styles.add(ParagraphStyle(
            name='ExecutiveTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica-Bold'
        ))
        
        # Recommendation style
        self.styles.add(ParagraphStyle(
            name='Recommendation',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=20,
            spaceAfter=8,
            textColor=colors.HexColor('#27ae60')
        ))
        
        # Warning style
        self.styles.add(ParagraphStyle(
            name='Warning',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=20,
            spaceAfter=8,
            textColor=colors.HexColor('#e74c3c')
        ))
    
    async def generate_pdf_report(self, 
                                config: ExportConfiguration,
                                recommendations: List[DecisionRecommendation],
                                visualizations: List[ChartConfiguration],
                                profile_data: Dict[str, Any]) -> ExportResult:
        """Generate comprehensive PDF report"""
        
        if not REPORTLAB_AVAILABLE:
            return ExportResult(
                export_id=config.export_id,
                success=False,
                format=ExportFormat.PDF_REPORT,
                error_message="ReportLab library not available"
            )
        
        try:
            start_time = datetime.now()
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_path = temp_file.name
            temp_file.close()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                temp_path,
                pagesize=letter if config.page_size == 'letter' else A4,
                topMargin=72,
                bottomMargin=72,
                leftMargin=72,
                rightMargin=72
            )
            
            # Build document content
            story = []
            
            # Title page
            story.extend(await self._create_title_page(config, profile_data))
            
            # Executive summary
            if config.report_type in [ReportType.EXECUTIVE_SUMMARY, ReportType.DETAILED_ANALYSIS]:
                story.extend(await self._create_executive_summary(recommendations, config))
            
            # Detailed analysis
            if config.report_type == ReportType.DETAILED_ANALYSIS:
                story.extend(await self._create_detailed_analysis(recommendations, config))
            
            # Decision support section
            if config.report_type == ReportType.DECISION_SUPPORT:
                story.extend(await self._create_decision_support_section(recommendations, config))
            
            # Recommendations section
            if config.include_recommendations:
                story.extend(await self._create_recommendations_section(recommendations, config))
            
            # Visualizations
            if config.include_visualizations and visualizations:
                story.extend(await self._create_visualizations_section(visualizations, config))
            
            # Methodology
            if config.include_methodology:
                story.extend(await self._create_methodology_section(config))
            
            # Appendices
            if config.include_appendices:
                story.extend(await self._create_appendices_section(recommendations, config))
            
            # Build PDF
            doc.build(story)
            
            # Calculate statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            file_size = Path(temp_path).stat().st_size
            
            return ExportResult(
                export_id=config.export_id,
                success=True,
                format=ExportFormat.PDF_REPORT,
                file_path=temp_path,
                file_size=file_size,
                pages_generated=len(story) // 10,  # Rough estimate
                charts_included=len(visualizations) if config.include_visualizations else 0,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return ExportResult(
                export_id=config.export_id,
                success=False,
                format=ExportFormat.PDF_REPORT,
                error_message=str(e)
            )
    
    async def _create_title_page(self, config: ExportConfiguration, profile_data: Dict[str, Any]) -> List[Any]:
        """Create title page elements"""
        elements = []
        
        # Title
        title = config.title or "Grant Research Analysis Report"
        elements.append(Paragraph(title, self.styles['Title']))
        elements.append(Spacer(1, 36))
        
        # Organization name
        if config.organization_name:
            elements.append(Paragraph(config.organization_name, self.styles['Heading2']))
            elements.append(Spacer(1, 24))
        
        # Report metadata
        metadata_text = f"""
        <b>Report Type:</b> {config.report_type.value.replace('_', ' ').title()}<br/>
        <b>Generated:</b> {config.created_at.strftime('%B %d, %Y')}<br/>
        <b>Author:</b> {config.author}<br/>
        """
        
        elements.append(Paragraph(metadata_text, self.styles['Normal']))
        elements.append(Spacer(1, 48))
        
        return elements
    
    async def _create_executive_summary(self, recommendations: List[DecisionRecommendation], config: ExportConfiguration) -> List[Any]:
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['ExecutiveTitle']))
        elements.append(Spacer(1, 12))
        
        if not recommendations:
            elements.append(Paragraph("No recommendations available for analysis.", self.styles['Normal']))
            return elements
        
        # Summary statistics
        high_priority = len([r for r in recommendations if r.priority_score > 0.75])
        medium_priority = len([r for r in recommendations if 0.5 <= r.priority_score <= 0.75])
        
        summary_text = f"""
        This analysis evaluated {len(recommendations)} opportunities and generated comprehensive 
        recommendations based on integrated scoring, feasibility assessment, and resource optimization.
        <br/><br/>
        <b>Key Findings:</b><br/>
        • {high_priority} high-priority opportunities identified<br/>
        • {medium_priority} medium-priority opportunities for consideration<br/>
        • Recommendations include detailed feasibility assessments and resource allocation guidance<br/>
        """
        
        elements.append(Paragraph(summary_text, self.styles['Normal']))
        elements.append(Spacer(1, 24))
        
        # Top recommendations
        if high_priority > 0:
            elements.append(Paragraph("Top Priority Recommendations:", self.styles['Heading3']))
            
            top_recs = sorted(recommendations, key=lambda r: r.priority_score, reverse=True)[:3]
            for i, rec in enumerate(top_recs, 1):
                rec_text = f"{i}. <b>{rec.opportunity_id}</b> (Priority: {rec.priority_score:.2f}) - {rec.recommendation.value.replace('_', ' ').title()}"
                elements.append(Paragraph(rec_text, self.styles['Recommendation']))
        
        elements.append(Spacer(1, 24))
        return elements
    
    async def _create_detailed_analysis(self, recommendations: List[DecisionRecommendation], config: ExportConfiguration) -> List[Any]:
        """Create detailed analysis section"""
        elements = []
        
        elements.append(Paragraph("Detailed Analysis", self.styles['Heading1']))
        elements.append(Spacer(1, 12))
        
        for rec in recommendations[:5]:  # Limit to top 5 for detailed analysis
            elements.extend(await self._create_recommendation_detail(rec))
            elements.append(Spacer(1, 24))
        
        return elements
    
    async def _create_recommendation_detail(self, rec: DecisionRecommendation) -> List[Any]:
        """Create detailed recommendation section"""
        elements = []
        
        # Opportunity header
        elements.append(Paragraph(f"Opportunity: {rec.opportunity_id}", self.styles['Heading2']))
        elements.append(Spacer(1, 8))
        
        # Recommendation summary
        rec_summary = f"""
        <b>Recommendation:</b> {rec.recommendation.value.replace('_', ' ').title()}<br/>
        <b>Priority Score:</b> {rec.priority_score:.2f}<br/>
        <b>Confidence:</b> {rec.confidence.value.replace('_', ' ').title()}<br/>
        """
        elements.append(Paragraph(rec_summary, self.styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Feasibility breakdown
        feasibility_data = [
            ['Dimension', 'Score', 'Assessment'],
            ['Technical', f"{rec.feasibility_assessment.technical_feasibility:.2f}", self._get_score_assessment(rec.feasibility_assessment.technical_feasibility)],
            ['Resource', f"{rec.feasibility_assessment.resource_feasibility:.2f}", self._get_score_assessment(rec.feasibility_assessment.resource_feasibility)],
            ['Timeline', f"{rec.feasibility_assessment.timeline_feasibility:.2f}", self._get_score_assessment(rec.feasibility_assessment.timeline_feasibility)],
            ['Compliance', f"{rec.feasibility_assessment.compliance_feasibility:.2f}", self._get_score_assessment(rec.feasibility_assessment.compliance_feasibility)],
            ['Strategic', f"{rec.feasibility_assessment.strategic_alignment:.2f}", self._get_score_assessment(rec.feasibility_assessment.strategic_alignment)]
        ]
        
        feasibility_table = Table(feasibility_data)
        feasibility_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(Paragraph("Feasibility Assessment:", self.styles['Heading3']))
        elements.append(feasibility_table)
        elements.append(Spacer(1, 12))
        
        # Key reasons
        if rec.primary_reasons:
            elements.append(Paragraph("Primary Reasons:", self.styles['Heading4']))
            for reason in rec.primary_reasons[:3]:
                elements.append(Paragraph(f"• {reason}", self.styles['Normal']))
            elements.append(Spacer(1, 8))
        
        # Immediate actions
        if rec.immediate_actions:
            elements.append(Paragraph("Immediate Actions:", self.styles['Heading4']))
            for action in rec.immediate_actions[:3]:
                elements.append(Paragraph(f"• {action}", self.styles['Normal']))
        
        return elements
    
    def _get_score_assessment(self, score: float) -> str:
        """Get qualitative assessment for numeric score"""
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Fair"
        else:
            return "Poor"
    
    async def _create_decision_support_section(self, recommendations: List[DecisionRecommendation], config: ExportConfiguration) -> List[Any]:
        """Create decision support section"""
        elements = []
        
        elements.append(Paragraph("Decision Support Analysis", self.styles['Heading1']))
        elements.append(Spacer(1, 12))
        
        # Decision matrix
        if len(recommendations) > 1:
            elements.append(Paragraph("Opportunity Comparison Matrix", self.styles['Heading2']))
            
            matrix_data = [['Opportunity', 'Priority', 'Recommendation', 'Confidence', 'Strategic Value']]
            
            for rec in recommendations[:10]:  # Limit to top 10
                matrix_data.append([
                    rec.opportunity_id[:20] + '...' if len(rec.opportunity_id) > 20 else rec.opportunity_id,
                    f"{rec.priority_score:.2f}",
                    rec.recommendation.value.replace('_', ' ').title(),
                    rec.confidence.value.replace('_', ' ').title(),
                    f"{rec.resource_allocation.strategic_value:.2f}"
                ])
            
            matrix_table = Table(matrix_data)
            matrix_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(matrix_table)
            elements.append(Spacer(1, 24))
        
        return elements
    
    async def _create_recommendations_section(self, recommendations: List[DecisionRecommendation], config: ExportConfiguration) -> List[Any]:
        """Create recommendations section"""
        elements = []
        
        elements.append(Paragraph("Recommendations Summary", self.styles['Heading1']))
        elements.append(Spacer(1, 12))
        
        # Group by recommendation type
        rec_groups = {}
        for rec in recommendations:
            rec_type = rec.recommendation.value
            if rec_type not in rec_groups:
                rec_groups[rec_type] = []
            rec_groups[rec_type].append(rec)
        
        for rec_type, recs in rec_groups.items():
            elements.append(Paragraph(f"{rec_type.replace('_', ' ').title()} ({len(recs)} opportunities)", self.styles['Heading2']))
            
            for rec in recs[:3]:  # Show top 3 per category
                elements.append(Paragraph(f"• {rec.opportunity_id} (Priority: {rec.priority_score:.2f})", self.styles['Normal']))
            
            elements.append(Spacer(1, 12))
        
        return elements
    
    async def _create_visualizations_section(self, visualizations: List[ChartConfiguration], config: ExportConfiguration) -> List[Any]:
        """Create visualizations section"""
        elements = []
        
        elements.append(Paragraph("Analysis Visualizations", self.styles['Heading1']))
        elements.append(Spacer(1, 12))
        
        # Note: In a real implementation, this would render actual charts
        # For now, we'll include placeholders
        for viz in visualizations[:5]:  # Limit to 5 visualizations
            elements.append(Paragraph(f"Chart: {viz.title}", self.styles['Heading3']))
            elements.append(Paragraph(viz.description, self.styles['Normal']))
            elements.append(Spacer(1, 24))
        
        return elements
    
    async def _create_methodology_section(self, config: ExportConfiguration) -> List[Any]:
        """Create methodology section"""
        elements = []
        
        elements.append(Paragraph("Methodology", self.styles['Heading1']))
        elements.append(Spacer(1, 12))
        
        methodology_text = """
        This analysis employs a comprehensive decision synthesis framework that integrates multiple
        scoring components, feasibility assessments, and resource optimization algorithms.
        <br/><br/>
        <b>Key Components:</b><br/>
        • Multi-Score Integration System: Combines scores from government opportunity analysis,
          workflow-aware enhancements, AI-based analysis, and compliance assessments<br/>
        • Feasibility Assessment Engine: Evaluates technical, resource, timeline, compliance,
          and strategic alignment factors<br/>
        • Resource Optimization Engine: Optimizes resource allocation recommendations based on
          organizational constraints and opportunity requirements<br/>
        • Decision Recommendation Engine: Generates comprehensive recommendations with
          confidence assessments and implementation guidance<br/>
        """
        
        elements.append(Paragraph(methodology_text, self.styles['Normal']))
        elements.append(Spacer(1, 24))
        
        return elements
    
    async def _create_appendices_section(self, recommendations: List[DecisionRecommendation], config: ExportConfiguration) -> List[Any]:
        """Create appendices section"""
        elements = []
        
        elements.append(Paragraph("Appendices", self.styles['Heading1']))
        elements.append(Spacer(1, 12))
        
        # Appendix A: Detailed Scoring Breakdown
        elements.append(Paragraph("Appendix A: Detailed Scoring Components", self.styles['Heading2']))
        
        for rec in recommendations[:3]:
            if rec.integrated_score.components:
                elements.append(Paragraph(f"Opportunity: {rec.opportunity_id}", self.styles['Heading3']))
                
                score_data = [['Component', 'Raw Score', 'Weighted Score', 'Confidence']]
                for comp in rec.integrated_score.components:
                    score_data.append([
                        comp.source,
                        f"{comp.raw_score:.3f}",
                        f"{comp.weighted_score:.3f}",
                        f"{comp.confidence:.3f}"
                    ])
                
                score_table = Table(score_data)
                score_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(score_table)
                elements.append(Spacer(1, 12))
        
        return elements

class ExcelReportGenerator:
    """Generator for Excel reports using XlsxWriter"""
    
    def __init__(self):
        self.workbook = None
        self.formats = {}
    
    async def generate_excel_report(self,
                                  config: ExportConfiguration,
                                  recommendations: List[DecisionRecommendation],
                                  visualizations: List[ChartConfiguration],
                                  profile_data: Dict[str, Any]) -> ExportResult:
        """Generate comprehensive Excel report"""
        
        if not XLSXWRITER_AVAILABLE:
            return ExportResult(
                export_id=config.export_id,
                success=False,
                format=ExportFormat.EXCEL_WORKBOOK,
                error_message="XlsxWriter library not available"
            )
        
        try:
            start_time = datetime.now()
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
            temp_path = temp_file.name
            temp_file.close()
            
            # Create workbook
            self.workbook = xlsxwriter.Workbook(temp_path)
            self._setup_formats()
            
            # Create worksheets
            await self._create_summary_worksheet(recommendations, config)
            await self._create_detailed_analysis_worksheet(recommendations, config)
            await self._create_feasibility_worksheet(recommendations, config)
            await self._create_resource_allocation_worksheet(recommendations, config)
            
            if config.include_raw_data:
                await self._create_raw_data_worksheet(recommendations, config)
            
            # Close workbook
            self.workbook.close()
            
            # Calculate statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            file_size = Path(temp_path).stat().st_size
            
            return ExportResult(
                export_id=config.export_id,
                success=True,
                format=ExportFormat.EXCEL_WORKBOOK,
                file_path=temp_path,
                file_size=file_size,
                data_rows_exported=len(recommendations),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error generating Excel report: {e}")
            return ExportResult(
                export_id=config.export_id,
                success=False,
                format=ExportFormat.EXCEL_WORKBOOK,
                error_message=str(e)
            )
    
    def _setup_formats(self):
        """Setup Excel formatting styles"""
        self.formats = {
            'title': self.workbook.add_format({
                'bold': True,
                'font_size': 16,
                'font_color': '#2c3e50',
                'align': 'center'
            }),
            'header': self.workbook.add_format({
                'bold': True,
                'font_size': 12,
                'bg_color': '#34495e',
                'font_color': 'white',
                'align': 'center',
                'border': 1
            }),
            'data': self.workbook.add_format({
                'font_size': 10,
                'align': 'left',
                'border': 1
            }),
            'numeric': self.workbook.add_format({
                'font_size': 10,
                'align': 'center',
                'border': 1,
                'num_format': '0.00'
            }),
            'percentage': self.workbook.add_format({
                'font_size': 10,
                'align': 'center',
                'border': 1,
                'num_format': '0.0%'
            }),
            'currency': self.workbook.add_format({
                'font_size': 10,
                'align': 'right',
                'border': 1,
                'num_format': '$#,##0'
            }),
            'high_priority': self.workbook.add_format({
                'font_size': 10,
                'align': 'center',
                'border': 1,
                'bg_color': '#d5f4e6'
            }),
            'medium_priority': self.workbook.add_format({
                'font_size': 10,
                'align': 'center',
                'border': 1,
                'bg_color': '#ffeaa7'
            }),
            'low_priority': self.workbook.add_format({
                'font_size': 10,
                'align': 'center',
                'border': 1,
                'bg_color': '#fab1a0'
            })
        }
    
    async def _create_summary_worksheet(self, recommendations: List[DecisionRecommendation], config: ExportConfiguration):
        """Create executive summary worksheet"""
        worksheet = self.workbook.add_worksheet('Executive Summary')
        
        # Title
        worksheet.write('A1', 'Grant Research Analysis - Executive Summary', self.formats['title'])
        worksheet.merge_range('A1:F1', 'Grant Research Analysis - Executive Summary', self.formats['title'])
        
        # Summary statistics
        row = 3
        worksheet.write(row, 0, 'Total Opportunities Analyzed:', self.formats['header'])
        worksheet.write(row, 1, len(recommendations), self.formats['data'])
        row += 1
        
        high_priority = len([r for r in recommendations if r.priority_score > 0.75])
        worksheet.write(row, 0, 'High Priority Opportunities:', self.formats['header'])
        worksheet.write(row, 1, high_priority, self.formats['data'])
        row += 1
        
        medium_priority = len([r for r in recommendations if 0.5 <= r.priority_score <= 0.75])
        worksheet.write(row, 0, 'Medium Priority Opportunities:', self.formats['header'])
        worksheet.write(row, 1, medium_priority, self.formats['data'])
        row += 2
        
        # Top recommendations table
        worksheet.write(row, 0, 'Top Priority Recommendations', self.formats['title'])
        row += 2
        
        headers = ['Opportunity ID', 'Priority Score', 'Recommendation', 'Confidence', 'Strategic Value']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1
        
        # Sort recommendations by priority
        top_recs = sorted(recommendations, key=lambda r: r.priority_score, reverse=True)[:10]
        
        for rec in top_recs:
            priority_format = self._get_priority_format(rec.priority_score)
            
            worksheet.write(row, 0, rec.opportunity_id, self.formats['data'])
            worksheet.write(row, 1, rec.priority_score, priority_format)
            worksheet.write(row, 2, rec.recommendation.value.replace('_', ' ').title(), self.formats['data'])
            worksheet.write(row, 3, rec.confidence.value.replace('_', ' ').title(), self.formats['data'])
            worksheet.write(row, 4, rec.resource_allocation.strategic_value, self.formats['numeric'])
            row += 1
        
        # Auto-adjust column widths
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
    
    def _get_priority_format(self, priority_score: float):
        """Get appropriate format based on priority score"""
        if priority_score > 0.75:
            return self.formats['high_priority']
        elif priority_score >= 0.5:
            return self.formats['medium_priority']
        else:
            return self.formats['low_priority']
    
    async def _create_detailed_analysis_worksheet(self, recommendations: List[DecisionRecommendation], config: ExportConfiguration):
        """Create detailed analysis worksheet"""
        worksheet = self.workbook.add_worksheet('Detailed Analysis')
        
        # Headers
        row = 0
        headers = [
            'Opportunity ID', 'Priority Score', 'Recommendation', 'Confidence',
            'Integrated Score', 'Technical Feasibility', 'Resource Feasibility',
            'Timeline Feasibility', 'Compliance Feasibility', 'Strategic Alignment',
            'Expected ROI', 'Resource Conflicts', 'Primary Reasons'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1
        
        # Data rows
        for rec in recommendations:
            col = 0
            worksheet.write(row, col, rec.opportunity_id, self.formats['data'])
            col += 1
            
            worksheet.write(row, col, rec.priority_score, self._get_priority_format(rec.priority_score))
            col += 1
            
            worksheet.write(row, col, rec.recommendation.value.replace('_', ' ').title(), self.formats['data'])
            col += 1
            
            worksheet.write(row, col, rec.confidence.value.replace('_', ' ').title(), self.formats['data'])
            col += 1
            
            worksheet.write(row, col, rec.integrated_score.final_score, self.formats['numeric'])
            col += 1
            
            worksheet.write(row, col, rec.feasibility_assessment.technical_feasibility, self.formats['percentage'])
            col += 1
            
            worksheet.write(row, col, rec.feasibility_assessment.resource_feasibility, self.formats['percentage'])
            col += 1
            
            worksheet.write(row, col, rec.feasibility_assessment.timeline_feasibility, self.formats['percentage'])
            col += 1
            
            worksheet.write(row, col, rec.feasibility_assessment.compliance_feasibility, self.formats['percentage'])
            col += 1
            
            worksheet.write(row, col, rec.feasibility_assessment.strategic_alignment, self.formats['percentage'])
            col += 1
            
            roi = rec.resource_allocation.expected_roi if rec.resource_allocation.expected_roi else 0
            worksheet.write(row, col, roi, self.formats['numeric'])
            col += 1
            
            conflicts_count = len(rec.resource_allocation.resource_conflicts)
            worksheet.write(row, col, conflicts_count, self.formats['data'])
            col += 1
            
            primary_reasons = '; '.join(rec.primary_reasons[:2]) if rec.primary_reasons else ''
            worksheet.write(row, col, primary_reasons, self.formats['data'])
            
            row += 1
        
        # Auto-adjust column widths
        for col in range(len(headers)):
            if col == 0:  # Opportunity ID
                worksheet.set_column(col, col, 25)
            elif col == len(headers) - 1:  # Primary Reasons
                worksheet.set_column(col, col, 40)
            else:
                worksheet.set_column(col, col, 15)
    
    async def _create_feasibility_worksheet(self, recommendations: List[DecisionRecommendation], config: ExportConfiguration):
        """Create feasibility analysis worksheet"""
        worksheet = self.workbook.add_worksheet('Feasibility Analysis')
        
        # Create a detailed feasibility breakdown
        row = 0
        worksheet.write(row, 0, 'Feasibility Assessment Details', self.formats['title'])
        row += 2
        
        for rec in recommendations:
            # Opportunity header
            worksheet.write(row, 0, f"Opportunity: {rec.opportunity_id}", self.formats['header'])
            worksheet.merge_range(row, 0, row, 4, f"Opportunity: {rec.opportunity_id}", self.formats['header'])
            row += 1
            
            # Feasibility dimensions
            dimensions = [
                ('Technical Feasibility', rec.feasibility_assessment.technical_feasibility),
                ('Resource Feasibility', rec.feasibility_assessment.resource_feasibility),
                ('Timeline Feasibility', rec.feasibility_assessment.timeline_feasibility),
                ('Compliance Feasibility', rec.feasibility_assessment.compliance_feasibility),
                ('Strategic Alignment', rec.feasibility_assessment.strategic_alignment)
            ]
            
            for dim_name, score in dimensions:
                worksheet.write(row, 1, dim_name, self.formats['data'])
                worksheet.write(row, 2, score, self.formats['percentage'])
                worksheet.write(row, 3, self._get_score_assessment(score), self.formats['data'])
                row += 1
            
            # Strengths and weaknesses
            if rec.feasibility_assessment.strengths:
                worksheet.write(row, 1, 'Key Strengths:', self.formats['header'])
                worksheet.write(row, 2, '; '.join(rec.feasibility_assessment.strengths[:3]), self.formats['data'])
                row += 1
            
            if rec.feasibility_assessment.weaknesses:
                worksheet.write(row, 1, 'Key Weaknesses:', self.formats['header'])
                worksheet.write(row, 2, '; '.join(rec.feasibility_assessment.weaknesses[:3]), self.formats['data'])
                row += 1
            
            row += 1  # Extra space between opportunities
        
        # Set column widths
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
    
    def _get_score_assessment(self, score: float) -> str:
        """Get qualitative assessment for score"""
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Fair"
        else:
            return "Poor"
    
    async def _create_resource_allocation_worksheet(self, recommendations: List[DecisionRecommendation], config: ExportConfiguration):
        """Create resource allocation analysis worksheet"""
        worksheet = self.workbook.add_worksheet('Resource Allocation')
        
        # Headers
        row = 0
        worksheet.write(row, 0, 'Resource Allocation Analysis', self.formats['title'])
        row += 2
        
        headers = [
            'Opportunity ID', 'Priority Ranking', 'Staff Time (%)', 'Budget (%)', 
            'Expertise (%)', 'Partnerships (%)', 'Infrastructure (%)',
            'Expected ROI', 'Strategic Value', 'Resource Conflicts'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1
        
        # Data rows
        for rec in recommendations:
            allocation = rec.resource_allocation.recommended_allocation
            
            col = 0
            worksheet.write(row, col, rec.opportunity_id, self.formats['data'])
            col += 1
            
            worksheet.write(row, col, rec.resource_allocation.priority_ranking, self.formats['data'])
            col += 1
            
            # Resource allocation percentages
            from src.decision.decision_synthesis_framework import ResourceType
            resource_types = [ResourceType.STAFF_TIME, ResourceType.BUDGET, ResourceType.EXPERTISE, 
                            ResourceType.PARTNERSHIPS, ResourceType.INFRASTRUCTURE]
            
            for resource_type in resource_types:
                value = allocation.get(resource_type, 0.0) * 100  # Convert to percentage
                worksheet.write(row, col, value, self.formats['percentage'])
                col += 1
            
            roi = rec.resource_allocation.expected_roi if rec.resource_allocation.expected_roi else 0
            worksheet.write(row, col, roi, self.formats['numeric'])
            col += 1
            
            worksheet.write(row, col, rec.resource_allocation.strategic_value, self.formats['numeric'])
            col += 1
            
            conflicts = len(rec.resource_allocation.resource_conflicts)
            worksheet.write(row, col, conflicts, self.formats['data'])
            
            row += 1
        
        # Auto-adjust column widths
        for col in range(len(headers)):
            if col == 0:  # Opportunity ID
                worksheet.set_column(col, col, 25)
            else:
                worksheet.set_column(col, col, 12)
    
    async def _create_raw_data_worksheet(self, recommendations: List[DecisionRecommendation], config: ExportConfiguration):
        """Create raw data worksheet with full details"""
        worksheet = self.workbook.add_worksheet('Raw Data')
        
        row = 0
        worksheet.write(row, 0, 'Complete Raw Data Export', self.formats['title'])
        row += 2
        
        # This would include all raw data from the analysis
        # For brevity, we'll include key raw metrics
        headers = ['Opportunity ID', 'Timestamp', 'Raw Components', 'Full Metadata']
        
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1
        
        for rec in recommendations:
            worksheet.write(row, 0, rec.opportunity_id, self.formats['data'])
            worksheet.write(row, 1, rec.timestamp.isoformat(), self.formats['data'])
            
            # Component details
            components_text = '; '.join([f"{c.source}:{c.raw_score:.3f}" for c in rec.integrated_score.components])
            worksheet.write(row, 2, components_text, self.formats['data'])
            
            # Metadata as JSON string
            metadata = json.dumps(rec.metadata, indent=None)[:1000]  # Limit length
            worksheet.write(row, 3, metadata, self.formats['data'])
            
            row += 1
        
        # Set column widths
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 50)
        worksheet.set_column('D:D', 50)

class ComprehensiveExportSystem(BaseProcessor):
    """Main comprehensive export system"""
    
    def __init__(self):
        super().__init__()
        self.pdf_generator = PDFReportGenerator()
        self.excel_generator = ExcelReportGenerator()
        self.export_history = {}
    
    async def process(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Main processing method for export operations"""
        try:
            logger.info(f"Starting export process for profile {profile_id}")
            
            # Parse export configuration
            config = await self._parse_export_configuration(kwargs)
            
            # Get data for export
            recommendations = kwargs.get('recommendations', [])
            visualizations = kwargs.get('visualizations', [])
            profile_data = kwargs.get('profile_data', {'profile_id': profile_id})
            
            # Perform export based on format
            if config.format == ExportFormat.PDF_REPORT:
                result = await self.pdf_generator.generate_pdf_report(
                    config, recommendations, visualizations, profile_data
                )
            elif config.format == ExportFormat.EXCEL_WORKBOOK:
                result = await self.excel_generator.generate_excel_report(
                    config, recommendations, visualizations, profile_data
                )
            elif config.format == ExportFormat.JSON_DATA:
                result = await self._generate_json_export(
                    config, recommendations, visualizations, profile_data
                )
            elif config.format == ExportFormat.HTML_REPORT:
                result = await self._generate_html_report(
                    config, recommendations, visualizations, profile_data
                )
            elif config.format == ExportFormat.ZIP_PACKAGE:
                result = await self._generate_zip_package(
                    config, recommendations, visualizations, profile_data
                )
            else:
                result = ExportResult(
                    export_id=config.export_id,
                    success=False,
                    format=config.format,
                    error_message=f"Unsupported export format: {config.format.value}"
                )
            
            # Store in history
            self.export_history[config.export_id] = result
            
            # Return processing result
            return {
                'profile_id': profile_id,
                'export_id': config.export_id,
                'export_result': self._serialize_export_result(result),
                'configuration': self._serialize_export_config(config),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive export system: {e}")
            return {
                'profile_id': profile_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _parse_export_configuration(self, kwargs: Dict[str, Any]) -> ExportConfiguration:
        """Parse export configuration from kwargs"""
        
        export_id = kwargs.get('export_id', str(uuid.uuid4()))
        format_str = kwargs.get('format', 'pdf')
        report_type_str = kwargs.get('report_type', 'detailed')
        template_str = kwargs.get('template', 'professional')
        
        # Parse enums
        format_enum = ExportFormat(format_str) if format_str in [f.value for f in ExportFormat] else ExportFormat.PDF_REPORT
        report_type_enum = ReportType(report_type_str) if report_type_str in [r.value for r in ReportType] else ReportType.DETAILED_ANALYSIS
        template_enum = ExportTemplate(template_str) if template_str in [t.value for t in ExportTemplate] else ExportTemplate.PROFESSIONAL
        
        return ExportConfiguration(
            export_id=export_id,
            format=format_enum,
            report_type=report_type_enum,
            template=template_enum,
            include_visualizations=kwargs.get('include_visualizations', True),
            include_raw_data=kwargs.get('include_raw_data', False),
            include_methodology=kwargs.get('include_methodology', True),
            include_recommendations=kwargs.get('include_recommendations', True),
            include_appendices=kwargs.get('include_appendices', False),
            organization_name=kwargs.get('organization_name', ''),
            title=kwargs.get('title', ''),
            author=kwargs.get('author', 'Catalynx Grant Research Platform')
        )
    
    async def _generate_json_export(self,
                                  config: ExportConfiguration,
                                  recommendations: List[DecisionRecommendation],
                                  visualizations: List[ChartConfiguration],
                                  profile_data: Dict[str, Any]) -> ExportResult:
        """Generate JSON data export"""
        
        try:
            start_time = datetime.now()
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
            temp_path = temp_file.name
            
            # Serialize data
            export_data = {
                'export_metadata': {
                    'export_id': config.export_id,
                    'created_at': config.created_at.isoformat(),
                    'format': config.format.value,
                    'report_type': config.report_type.value
                },
                'profile_data': profile_data,
                'recommendations': [self._serialize_recommendation_for_json(r) for r in recommendations],
                'visualizations': [self._serialize_visualization_for_json(v) for v in visualizations] if config.include_visualizations else [],
                'summary_statistics': self._calculate_summary_statistics(recommendations)
            }
            
            # Write to file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            temp_file.close()
            
            # Calculate statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            file_size = Path(temp_path).stat().st_size
            
            return ExportResult(
                export_id=config.export_id,
                success=True,
                format=ExportFormat.JSON_DATA,
                file_path=temp_path,
                file_size=file_size,
                data_rows_exported=len(recommendations),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error generating JSON export: {e}")
            return ExportResult(
                export_id=config.export_id,
                success=False,
                format=ExportFormat.JSON_DATA,
                error_message=str(e)
            )
    
    async def _generate_html_report(self,
                                  config: ExportConfiguration,
                                  recommendations: List[DecisionRecommendation],
                                  visualizations: List[ChartConfiguration],
                                  profile_data: Dict[str, Any]) -> ExportResult:
        """Generate HTML report"""
        
        try:
            start_time = datetime.now()
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
            temp_path = temp_file.name
            
            # Generate HTML content
            html_content = await self._create_html_content(config, recommendations, visualizations, profile_data)
            
            # Write to file
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            temp_file.close()
            
            # Calculate statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            file_size = Path(temp_path).stat().st_size
            
            return ExportResult(
                export_id=config.export_id,
                success=True,
                format=ExportFormat.HTML_REPORT,
                file_path=temp_path,
                file_size=file_size,
                data_rows_exported=len(recommendations),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            return ExportResult(
                export_id=config.export_id,
                success=False,
                format=ExportFormat.HTML_REPORT,
                error_message=str(e)
            )
    
    async def _create_html_content(self,
                                 config: ExportConfiguration,
                                 recommendations: List[DecisionRecommendation],
                                 visualizations: List[ChartConfiguration],
                                 profile_data: Dict[str, Any]) -> str:
        """Create HTML report content"""
        
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; margin-bottom: 20px; }}
                .summary {{ background: #ecf0f1; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
                .recommendation {{ border: 1px solid #bdc3c7; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .high-priority {{ border-left: 5px solid #27ae60; }}
                .medium-priority {{ border-left: 5px solid #f39c12; }}
                .low-priority {{ border-left: 5px solid #e74c3c; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #34495e; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <p>Generated on {date} | {organization}</p>
            </div>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <p><strong>Total Opportunities:</strong> {total_opportunities}</p>
                <p><strong>High Priority:</strong> {high_priority}</p>
                <p><strong>Medium Priority:</strong> {medium_priority}</p>
                <p><strong>Average Confidence:</strong> {avg_confidence}</p>
            </div>
            
            <h2>Detailed Recommendations</h2>
            {recommendations_html}
            
            {methodology_html}
        </body>
        </html>
        """
        
        # Calculate summary statistics
        total_opportunities = len(recommendations)
        high_priority = len([r for r in recommendations if r.priority_score > 0.75])
        medium_priority = len([r for r in recommendations if 0.5 <= r.priority_score <= 0.75])
        avg_confidence = sum(self._confidence_to_numeric(r.confidence) for r in recommendations) / len(recommendations) if recommendations else 0
        
        # Generate recommendations HTML
        recommendations_html = ""
        for rec in recommendations:
            priority_class = self._get_priority_css_class(rec.priority_score)
            
            recommendations_html += f"""
            <div class="recommendation {priority_class}">
                <h3>{rec.opportunity_id}</h3>
                <p><strong>Recommendation:</strong> {rec.recommendation.value.replace('_', ' ').title()}</p>
                <p><strong>Priority Score:</strong> {rec.priority_score:.2f}</p>
                <p><strong>Confidence:</strong> {rec.confidence.value.replace('_', ' ').title()}</p>
                
                <h4>Feasibility Assessment</h4>
                <table>
                    <tr><th>Dimension</th><th>Score</th><th>Assessment</th></tr>
                    <tr><td>Technical</td><td>{rec.feasibility_assessment.technical_feasibility:.2f}</td><td>{self._get_score_assessment(rec.feasibility_assessment.technical_feasibility)}</td></tr>
                    <tr><td>Resource</td><td>{rec.feasibility_assessment.resource_feasibility:.2f}</td><td>{self._get_score_assessment(rec.feasibility_assessment.resource_feasibility)}</td></tr>
                    <tr><td>Timeline</td><td>{rec.feasibility_assessment.timeline_feasibility:.2f}</td><td>{self._get_score_assessment(rec.feasibility_assessment.timeline_feasibility)}</td></tr>
                    <tr><td>Compliance</td><td>{rec.feasibility_assessment.compliance_feasibility:.2f}</td><td>{self._get_score_assessment(rec.feasibility_assessment.compliance_feasibility)}</td></tr>
                    <tr><td>Strategic</td><td>{rec.feasibility_assessment.strategic_alignment:.2f}</td><td>{self._get_score_assessment(rec.feasibility_assessment.strategic_alignment)}</td></tr>
                </table>
                
                {f'<p><strong>Key Reasons:</strong> {"; ".join(rec.primary_reasons[:3])}</p>' if rec.primary_reasons else ''}
                {f'<p><strong>Immediate Actions:</strong> {"; ".join(rec.immediate_actions[:3])}</p>' if rec.immediate_actions else ''}
            </div>
            """
        
        # Methodology section
        methodology_html = ""
        if config.include_methodology:
            methodology_html = """
            <h2>Methodology</h2>
            <div class="summary">
                <p>This analysis employs a comprehensive decision synthesis framework that integrates multiple
                scoring components, feasibility assessments, and resource optimization algorithms.</p>
                
                <h3>Key Components:</h3>
                <ul>
                    <li><strong>Multi-Score Integration System:</strong> Combines scores from government opportunity analysis,
                        workflow-aware enhancements, AI-based analysis, and compliance assessments</li>
                    <li><strong>Feasibility Assessment Engine:</strong> Evaluates technical, resource, timeline, compliance,
                        and strategic alignment factors</li>
                    <li><strong>Resource Optimization Engine:</strong> Optimizes resource allocation recommendations based on
                        organizational constraints and opportunity requirements</li>
                    <li><strong>Decision Recommendation Engine:</strong> Generates comprehensive recommendations with
                        confidence assessments and implementation guidance</li>
                </ul>
            </div>
            """
        
        return html_template.format(
            title=config.title or "Grant Research Analysis Report",
            date=config.created_at.strftime('%B %d, %Y'),
            organization=config.organization_name or "Catalynx Grant Research Platform",
            total_opportunities=total_opportunities,
            high_priority=high_priority,
            medium_priority=medium_priority,
            avg_confidence=f"{avg_confidence:.2f}",
            recommendations_html=recommendations_html,
            methodology_html=methodology_html
        )
    
    async def _generate_zip_package(self,
                                  config: ExportConfiguration,
                                  recommendations: List[DecisionRecommendation],
                                  visualizations: List[ChartConfiguration],
                                  profile_data: Dict[str, Any]) -> ExportResult:
        """Generate comprehensive ZIP package with multiple formats"""
        
        try:
            start_time = datetime.now()
            
            # Create temporary directory for package contents
            temp_dir = tempfile.mkdtemp()
            
            # Generate individual format exports
            exports = []
            
            # PDF Report
            pdf_config = config
            pdf_config.format = ExportFormat.PDF_REPORT
            pdf_result = await self.pdf_generator.generate_pdf_report(pdf_config, recommendations, visualizations, profile_data)
            if pdf_result.success:
                exports.append(('Grant_Analysis_Report.pdf', pdf_result.file_path))
            
            # Excel Workbook
            excel_config = config
            excel_config.format = ExportFormat.EXCEL_WORKBOOK
            excel_result = await self.excel_generator.generate_excel_report(excel_config, recommendations, visualizations, profile_data)
            if excel_result.success:
                exports.append(('Grant_Analysis_Data.xlsx', excel_result.file_path))
            
            # JSON Data
            json_config = config
            json_config.format = ExportFormat.JSON_DATA
            json_result = await self._generate_json_export(json_config, recommendations, visualizations, profile_data)
            if json_result.success:
                exports.append(('Grant_Analysis_Data.json', json_result.file_path))
            
            # HTML Report
            html_config = config
            html_config.format = ExportFormat.HTML_REPORT
            html_result = await self._generate_html_report(html_config, recommendations, visualizations, profile_data)
            if html_result.success:
                exports.append(('Grant_Analysis_Report.html', html_result.file_path))
            
            # Create ZIP file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            temp_path = temp_file.name
            temp_file.close()
            
            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filename, filepath in exports:
                    if filepath and Path(filepath).exists():
                        zip_file.write(filepath, filename)
                
                # Add README
                readme_content = f"""
Grant Research Analysis Package
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
Profile: {profile_data.get('profile_id', 'Unknown')}

Contents:
- Grant_Analysis_Report.pdf: Comprehensive PDF report
- Grant_Analysis_Data.xlsx: Excel workbook with detailed data
- Grant_Analysis_Data.json: Raw data in JSON format
- Grant_Analysis_Report.html: Interactive HTML report

Total Opportunities Analyzed: {len(recommendations)}
High Priority Opportunities: {len([r for r in recommendations if r.priority_score > 0.75])}

For questions or support, please contact the Catalynx team.
                """
                
                zip_file.writestr('README.txt', readme_content)
            
            # Calculate statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            file_size = Path(temp_path).stat().st_size
            
            return ExportResult(
                export_id=config.export_id,
                success=True,
                format=ExportFormat.ZIP_PACKAGE,
                file_path=temp_path,
                file_size=file_size,
                data_rows_exported=len(recommendations),
                processing_time=processing_time,
                metadata={'package_contents': len(exports)}
            )
            
        except Exception as e:
            logger.error(f"Error generating ZIP package: {e}")
            return ExportResult(
                export_id=config.export_id,
                success=False,
                format=ExportFormat.ZIP_PACKAGE,
                error_message=str(e)
            )
    
    def _confidence_to_numeric(self, confidence) -> float:
        """Convert confidence enum to numeric value"""
        from src.decision.decision_synthesis_framework import DecisionConfidence
        mapping = {
            DecisionConfidence.VERY_HIGH: 1.0,
            DecisionConfidence.HIGH: 0.8,
            DecisionConfidence.MEDIUM: 0.6,
            DecisionConfidence.LOW: 0.4,
            DecisionConfidence.VERY_LOW: 0.2
        }
        return mapping.get(confidence, 0.5)
    
    def _get_priority_css_class(self, priority_score: float) -> str:
        """Get CSS class for priority score"""
        if priority_score > 0.75:
            return "high-priority"
        elif priority_score >= 0.5:
            return "medium-priority"
        else:
            return "low-priority"
    
    def _get_score_assessment(self, score: float) -> str:
        """Get qualitative assessment for score"""
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Fair"
        else:
            return "Poor"
    
    def _calculate_summary_statistics(self, recommendations: List[DecisionRecommendation]) -> Dict[str, Any]:
        """Calculate summary statistics for recommendations"""
        if not recommendations:
            return {}
        
        from collections import Counter
        
        recommendation_counts = Counter(r.recommendation.value for r in recommendations)
        confidence_counts = Counter(r.confidence.value for r in recommendations)
        
        return {
            'total_opportunities': len(recommendations),
            'average_priority_score': sum(r.priority_score for r in recommendations) / len(recommendations),
            'high_priority_count': len([r for r in recommendations if r.priority_score > 0.75]),
            'medium_priority_count': len([r for r in recommendations if 0.5 <= r.priority_score <= 0.75]),
            'low_priority_count': len([r for r in recommendations if r.priority_score < 0.5]),
            'recommendation_distribution': dict(recommendation_counts),
            'confidence_distribution': dict(confidence_counts),
            'average_feasibility': sum(r.feasibility_assessment.overall_feasibility for r in recommendations) / len(recommendations),
            'average_strategic_value': sum(r.resource_allocation.strategic_value for r in recommendations) / len(recommendations)
        }
    
    def _serialize_recommendation_for_json(self, rec: DecisionRecommendation) -> Dict[str, Any]:
        """Serialize recommendation for JSON export"""
        return {
            'opportunity_id': rec.opportunity_id,
            'recommendation': rec.recommendation.value,
            'confidence': rec.confidence.value,
            'priority_score': rec.priority_score,
            'timestamp': rec.timestamp.isoformat(),
            
            'integrated_score': {
                'final_score': rec.integrated_score.final_score,
                'confidence': rec.integrated_score.confidence.value,
                'integration_method': rec.integrated_score.integration_method,
                'components': [
                    {
                        'source': c.source,
                        'raw_score': c.raw_score,
                        'weighted_score': c.weighted_score,
                        'confidence': c.confidence,
                        'timestamp': c.timestamp.isoformat()
                    }
                    for c in rec.integrated_score.components
                ]
            },
            
            'feasibility_assessment': {
                'overall_feasibility': rec.feasibility_assessment.overall_feasibility,
                'confidence': rec.feasibility_assessment.confidence.value,
                'technical_feasibility': rec.feasibility_assessment.technical_feasibility,
                'resource_feasibility': rec.feasibility_assessment.resource_feasibility,
                'timeline_feasibility': rec.feasibility_assessment.timeline_feasibility,
                'compliance_feasibility': rec.feasibility_assessment.compliance_feasibility,
                'strategic_alignment': rec.feasibility_assessment.strategic_alignment,
                'strengths': rec.feasibility_assessment.strengths,
                'weaknesses': rec.feasibility_assessment.weaknesses,
                'requirements': rec.feasibility_assessment.requirements,
                'risks': rec.feasibility_assessment.risks,
                'mitigation_strategies': rec.feasibility_assessment.mitigation_strategies,
                'estimated_effort_hours': rec.feasibility_assessment.estimated_effort_hours,
                'required_budget': rec.feasibility_assessment.required_budget,
                'key_personnel': rec.feasibility_assessment.key_personnel,
                'external_partnerships': rec.feasibility_assessment.external_partnerships
            },
            
            'resource_allocation': {
                'priority_ranking': rec.resource_allocation.priority_ranking,
                'expected_roi': rec.resource_allocation.expected_roi,
                'strategic_value': rec.resource_allocation.strategic_value,
                'risk_adjusted_value': rec.resource_allocation.risk_adjusted_value,
                'opportunity_cost': rec.resource_allocation.opportunity_cost,
                'recommended_allocation': {
                    k.value: v for k, v in rec.resource_allocation.recommended_allocation.items()
                },
                'recommended_timeline': rec.resource_allocation.recommended_timeline,
                'critical_path': rec.resource_allocation.critical_path,
                'resource_conflicts': rec.resource_allocation.resource_conflicts
            },
            
            'decision_rationale': {
                'primary_reasons': rec.primary_reasons,
                'supporting_evidence': rec.supporting_evidence,
                'concerns': rec.concerns,
                'conditions': rec.conditions,
                'immediate_actions': rec.immediate_actions,
                'preparation_steps': rec.preparation_steps,
                'success_metrics': rec.success_metrics,
                'review_timeline_days': rec.review_timeline.days
            },
            
            'metadata': rec.metadata
        }
    
    def _serialize_visualization_for_json(self, viz: ChartConfiguration) -> Dict[str, Any]:
        """Serialize visualization for JSON export"""
        return {
            'chart_id': viz.chart_id,
            'chart_type': viz.chart_type.value,
            'title': viz.title,
            'description': viz.description,
            'data_source': viz.data_source,
            'chart_configuration': {
                'x_axis': viz.x_axis,
                'y_axis': viz.y_axis,
                'color_field': viz.color_field,
                'size_field': viz.size_field,
                'width': viz.width,
                'height': viz.height,
                'theme': viz.theme.value,
                'interactions': [i.value for i in viz.interactions],
                'options': viz.options
            },
            'data_preview': viz.metadata.get('data', [])[:10] if 'data' in viz.metadata else []
        }
    
    def _serialize_export_result(self, result: ExportResult) -> Dict[str, Any]:
        """Serialize export result for JSON output"""
        return {
            'export_id': result.export_id,
            'success': result.success,
            'format': result.format.value,
            'file_path': result.file_path,
            'file_size': result.file_size,
            'pages_generated': result.pages_generated,
            'charts_included': result.charts_included,
            'data_rows_exported': result.data_rows_exported,
            'processing_time': result.processing_time,
            'error_message': result.error_message,
            'warnings': result.warnings,
            'timestamp': result.timestamp.isoformat(),
            'metadata': result.metadata
        }
    
    def _serialize_export_config(self, config: ExportConfiguration) -> Dict[str, Any]:
        """Serialize export configuration for JSON output"""
        return {
            'export_id': config.export_id,
            'format': config.format.value,
            'report_type': config.report_type.value,
            'template': config.template.value,
            'content_options': {
                'include_visualizations': config.include_visualizations,
                'include_raw_data': config.include_raw_data,
                'include_methodology': config.include_methodology,
                'include_recommendations': config.include_recommendations,
                'include_appendices': config.include_appendices
            },
            'formatting': {
                'page_orientation': config.page_orientation,
                'page_size': config.page_size,
                'font_family': config.font_family,
                'font_size': config.font_size
            },
            'branding': {
                'organization_name': config.organization_name,
                'title': config.title,
                'author': config.author
            },
            'created_at': config.created_at.isoformat()
        }

# Export main components
__all__ = [
    'ComprehensiveExportSystem',
    'ExportConfiguration',
    'ExportResult',
    'ExportFormat',
    'ReportType',
    'ExportTemplate'
]