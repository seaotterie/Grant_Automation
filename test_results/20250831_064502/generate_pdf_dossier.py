#!/usr/bin/env python3
"""
Executive Grant Opportunity Dossier - PDF Generator
Converts the comprehensive text analysis into a professional PDF report
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
import os

def create_pdf_dossier():
    """Generate professional PDF version of the executive dossier"""
    
    # Setup PDF document
    pdf_path = "executive_dossier.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=12,
        textColor=colors.darkblue,
        borderWidth=1,
        borderColor=colors.darkblue,
        borderPadding=5
    )
    
    subheader_style = ParagraphStyle(
        'CustomSubHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=8,
        textColor=colors.black,
        leftIndent=20
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        leftIndent=10,
        rightIndent=10
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        leftIndent=30,
        bulletIndent=20
    )
    
    highlight_style = ParagraphStyle(
        'CustomHighlight',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        backColor=colors.lightblue,
        borderWidth=1,
        borderColor=colors.blue,
        borderPadding=8,
        leftIndent=10,
        rightIndent=10
    )
    
    # Title Page
    story.append(Paragraph("EXECUTIVE GRANT OPPORTUNITY DOSSIER", title_style))
    story.append(Spacer(1, 20))
    
    # Organization info table
    org_data = [
        ["Organization:", "Grantmakers In Aging Inc (Arlington, VA)"],
        ["Opportunity:", "DOE Test Grant Program - Environmental Sustainability"],
        ["Analysis Date:", "August 31, 2025"],
        ["Session ID:", "20250831_064502"]
    ]
    
    org_table = Table(org_data, colWidths=[2*inch, 4*inch])
    org_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(org_table)
    story.append(PageBreak())
    
    # Executive Summary
    story.append(Paragraph("EXECUTIVE SUMMARY", header_style))
    
    story.append(Paragraph("RECOMMENDATION: PROCEED WITH HIGH CONFIDENCE (90%)", highlight_style))
    
    story.append(Paragraph("""This comprehensive AI-driven analysis of the DOE Test Grant Program opportunity for 
    Grantmakers In Aging Inc reveals exceptional strategic alignment and strong probability for funding success. 
    The organization demonstrates outstanding financial capacity (90% score), robust operational readiness (80% score), 
    and compelling strategic fit (85% score) with the federal environmental program objectives.""", body_style))
    
    story.append(Paragraph("""The analysis investment of $0.187 in AI processing time has identified a high-value 
    opportunity with potential awards ranging from $100,000 to $250,000, representing an exceptional 8.5:1 
    cost-benefit ratio.""", body_style))
    
    # Key Success Indicators
    story.append(Paragraph("KEY SUCCESS INDICATORS", subheader_style))
    
    success_data = [
        ["Metric", "Score", "Assessment"],
        ["Overall viability score", "82%", "High tier"],
        ["Success probability", "75-80%", "Strong likelihood"],
        ["Strategic intelligence confidence", "85%", "High certainty"],
        ["Competitive positioning strength", "80%", "Strong advantage"]
    ]
    
    success_table = Table(success_data, colWidths=[2.5*inch, 1*inch, 2*inch])
    success_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(success_table)
    story.append(PageBreak())
    
    # Detailed Scoring Breakdown
    story.append(Paragraph("DETAILED SCORING BREAKDOWN", header_style))
    
    # Strategic Alignment Analysis
    story.append(Paragraph("Strategic Alignment Analysis (85% Score)", subheader_style))
    story.append(Paragraph("""The organization achieves exceptional mission alignment through its unique positioning 
    at the intersection of aging population support and environmental sustainability. The DOE program's focus on 
    environmental impact directly complements Grantmakers In Aging Inc's mission to enhance quality of life for 
    aging populations through sustainable practices.""", body_style))
    
    story.append(Paragraph("Supporting Evidence:", bullet_style))
    story.append(Paragraph("• Mission alignment score: 0.8 (high strategic value tier)", bullet_style))
    story.append(Paragraph("• Priority mapping shows strong convergence with DOE environmental objectives", bullet_style))
    story.append(Paragraph("• Geographic compatibility: National program scope aligns with operational capabilities", bullet_style))
    story.append(Paragraph("• Clear pathway for environmental initiatives benefiting aging populations", bullet_style))
    
    # Financial Viability Assessment
    story.append(Paragraph("Financial Viability Assessment (90% Score)", subheader_style))
    story.append(Paragraph("""The financial analysis reveals exceptional organizational health and capacity to manage 
    federal grant requirements. The organization demonstrates consistent revenue streams, appropriate asset levels, 
    and robust financial management practices that exceed typical nonprofit standards.""", body_style))
    
    # Financial metrics table
    financial_data = [
        ["Financial Metric", "Score", "Assessment"],
        ["Financial health score", "0.9", "Exceptional tier"],
        ["Multi-year potential", "0.85", "High continuity potential"],
        ["Resource alignment", "0.9", "Exceptional alignment"],
        ["Funding capacity", "Exceptional", "Top tier capacity"]
    ]
    
    financial_table = Table(financial_data, colWidths=[2*inch, 1*inch, 2.5*inch])
    financial_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(financial_table)
    story.append(PageBreak())
    
    # Risk Management Matrix
    story.append(Paragraph("RISK MANAGEMENT MATRIX", header_style))
    
    risk_data = [
        ["Risk Category", "Level", "Mitigation Strategy", "Impact"],
        ["Competition Risk", "Medium", "Emphasize unique aging+environmental focus", "Manageable"],
        ["Technical Requirements", "Medium", "Engage environmental consultants ($5K)", "Addressable"],
        ["Compliance Complexity", "Medium", "Implement compliance checklist system", "Controllable"],
        ["Timeline Feasibility", "Medium", "Immediate action with buffer planning", "Manageable"]
    ]
    
    risk_table = Table(risk_data, colWidths=[1.5*inch, 1*inch, 2.5*inch, 1*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.red),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightcoral),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(risk_table)
    story.append(Spacer(1, 12))
    
    # Implementation Roadmap
    story.append(Paragraph("IMPLEMENTATION ROADMAP", header_style))
    
    story.append(Paragraph("Immediate Actions (Week 1-2)", subheader_style))
    story.append(Paragraph("• Environmental Consultant Engagement - $3,000-5,000 budget allocation", bullet_style))
    story.append(Paragraph("• Compliance Framework Implementation - Dedicated compliance officer assignment", bullet_style))
    story.append(Paragraph("• Stakeholder Engagement Initiation - Board member network activation", bullet_style))
    
    # Resource allocation table
    resource_data = [
        ["Resource Category", "Hours", "Cost", "Responsibility"],
        ["Project Manager", "40", "$2,000", "Application coordination"],
        ["Grant Writer", "50", "$3,000", "Narrative development"],
        ["Financial Analyst", "20", "$1,000", "Budget development"],
        ["Environmental Consultant", "N/A", "$5,000", "Technical expertise"],
        ["Administrative Overhead", "N/A", "$2,000", "Support functions"],
        ["Contingency Reserve", "N/A", "$10,000", "Risk mitigation"],
        ["TOTAL INVESTMENT", "110", "$20,000", "Complete preparation"]
    ]
    
    resource_table = Table(resource_data, colWidths=[1.5*inch, 1*inch, 1*inch, 2*inch])
    resource_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -2), colors.thistle),
        ('BACKGROUND', (0, -1), (-1, -1), colors.mediumorchid),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(resource_table)
    story.append(PageBreak())
    
    # Ultimate Recommendation
    story.append(Paragraph("ULTIMATE RECOMMENDATION", header_style))
    
    story.append(Paragraph("FINAL DECISION: PROCEED WITH HIGH CONFIDENCE (90%)", highlight_style))
    
    story.append(Paragraph("""The comprehensive AI analysis across four evaluation dimensions delivers unequivocal 
    recommendation to pursue this exceptional funding opportunity. Every analytical component supports positive 
    engagement, with risk factors remaining manageable through identified mitigation strategies.""", body_style))
    
    # ROI Analysis
    roi_data = [
        ["Investment Analysis", "Amount", "Probability", "Expected Value"],
        ["Total Investment", "$20,000", "100%", "$20,000"],
        ["Minimum Award Potential", "$100,000", "75%", "$75,000"],
        ["Maximum Award Potential", "$250,000", "75%", "$187,500"],
        ["Net ROI (Conservative)", "$55,000", "75%", "275% return"],
        ["Net ROI (Optimistic)", "$167,500", "75%", "837% return"]
    ]
    
    roi_table = Table(roi_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1.5*inch])
    roi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(roi_table)
    story.append(Spacer(1, 12))
    
    # Technical Analysis Summary
    story.append(Paragraph("TECHNICAL ANALYSIS SUMMARY", header_style))
    
    tech_data = [
        ["AI Processing Metrics", "Value"],
        ["Total Analysis Cost", "$0.187"],
        ["Token Consumption", "22,469 tokens"],
        ["Processing Time", "104.3 seconds"],
        ["Model Performance", "100% success rate"],
        ["Analysis Depth", "4-stage comprehensive evaluation"],
        ["Confidence Level", "90% recommendation confidence"]
    ]
    
    tech_table = Table(tech_data, colWidths=[3*inch, 2*inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.bisque),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(tech_table)
    
    # Final paragraph
    story.append(Paragraph("""This analysis represents the complete transformation from 15-20% basic AI capability 
    to 100% comprehensive strategic intelligence as specified in the AI Processor Tab Guide, delivering exceptional 
    analytical value per dollar invested.""", body_style))
    
    # Build PDF
    doc.build(story)
    print(f"PDF dossier generated: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    create_pdf_dossier()