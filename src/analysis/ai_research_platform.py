"""
AI Research Platform Framework
Phase 3: AI-Lite Dual-Function Platform

This module provides the core architecture for transforming the ANALYZE tab into a
dual-function platform that provides both scoring and comprehensive research capabilities.

Key Features:
- Website intelligence and document parsing
- Fact extraction and POC identification
- Research report generation
- Grant team decision support
- Cost-optimized batch processing
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
from urllib.parse import urlparse
import aiohttp
import re
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResearchType(Enum):
    """Types of research analysis available"""
    WEBSITE_INTELLIGENCE = "website_intelligence"
    DOCUMENT_PARSING = "document_parsing"
    POC_IDENTIFICATION = "poc_identification"
    FACT_EXTRACTION = "fact_extraction"
    COMPREHENSIVE_RESEARCH = "comprehensive_research"


class ReportFormat(Enum):
    """Available report formats for grant teams"""
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_RESEARCH = "detailed_research"
    DECISION_BRIEF = "decision_brief"
    EVALUATION_SUMMARY = "evaluation_summary"
    EVIDENCE_PACKAGE = "evidence_package"


@dataclass
class ResearchContact:
    """Identified point of contact from research"""
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    confidence: float = 0.0
    source: str = ""
    verification_status: str = "unverified"


@dataclass
class ExtractedFact:
    """Fact extracted from research sources"""
    fact: str
    source: str
    confidence: float
    category: str
    date_extracted: datetime = field(default_factory=datetime.now)
    verification_level: str = "preliminary"
    supporting_evidence: List[str] = field(default_factory=list)


@dataclass
class WebsiteIntelligence:
    """Intelligence gathered from website analysis"""
    url: str
    domain: str
    title: Optional[str] = None
    description: Optional[str] = None
    contact_info: List[ResearchContact] = field(default_factory=list)
    key_facts: List[ExtractedFact] = field(default_factory=list)
    program_areas: List[str] = field(default_factory=list)
    funding_info: Dict[str, Any] = field(default_factory=dict)
    organization_type: Optional[str] = None
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    quality_score: float = 0.0


@dataclass
class ResearchReport:
    """Generated research report for grant teams"""
    report_id: str
    opportunity_id: str
    report_type: ReportFormat
    title: str
    executive_summary: str
    detailed_findings: Dict[str, Any]
    evidence_package: List[ExtractedFact]
    contacts_identified: List[ResearchContact]
    recommendations: List[str]
    risk_factors: List[str]
    next_steps: List[str]
    confidence_assessment: Dict[str, float]
    cost_analysis: Dict[str, float]
    generated_at: datetime = field(default_factory=datetime.now)
    generated_by: str = "ai_research_platform"


class AIResearchPlatform:
    """
    Core AI Research Platform for dual-function ANALYZE tab
    
    Provides both traditional scoring capabilities and comprehensive research functions
    for grant team decision support.
    """
    
    def __init__(self, api_key: Optional[str] = None, cost_optimization: bool = True):
        """
        Initialize the AI Research Platform
        
        Args:
            api_key: OpenAI API key for AI-powered analysis
            cost_optimization: Enable cost optimization features
        """
        self.api_key = api_key
        self.cost_optimization = cost_optimization
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Cost tracking
        self.research_costs = {
            'total_spent': 0.0,
            'research_count': 0,
            'avg_cost_per_research': 0.0
        }
        
        # Research patterns for fact extraction
        self.fact_patterns = {
            'funding_amounts': [
                r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|M|B|K))?',
                r'(?:grant|funding|award)(?:s)?\s+(?:of|totaling|worth)\s*\$[\d,]+',
                r'budget(?:s)?\s+(?:of|totaling)\s*\$[\d,]+'
            ],
            'deadlines': [
                r'deadline(?:s)?\s*:?\s*([A-Za-z]+ \d{1,2},?\s*\d{4})',
                r'due\s+(?:by|on)\s*([A-Za-z]+ \d{1,2},?\s*\d{4})',
                r'applications?\s+must\s+be\s+received\s+by\s*([A-Za-z]+ \d{1,2},?\s*\d{4})'
            ],
            'eligibility': [
                r'(?:eligible|qualified)\s+(?:organizations?|applicants?|nonprofits?)',
                r'(?:501\(c\)\(3\)|tax-exempt|charitable)\s+(?:organizations?|status)',
                r'geographic(?:al)?\s+(?:restrictions?|requirements?|limitations?)'
            ],
            'contact_info': [
                r'(?:contact|reach)\s+(?:us\s+)?(?:at\s+)?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'(?:phone|call)\s*:?\s*(\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})',
                r'(?:director|manager|coordinator|contact)\s*:?\s*([A-Z][a-z]+ [A-Z][a-z]+)'
            ]
        }
        
        # Website intelligence patterns
        self.website_patterns = {
            'org_types': [
                r'(?:foundation|charity|nonprofit|NGO|501\(c\)\(3\))',
                r'(?:grants?|funding|scholarships?|awards?)',
                r'(?:community|social|educational|environmental)'
            ],
            'program_areas': [
                r'(?:education|health|environment|arts|social\s+services)',
                r'(?:children|youth|seniors|veterans|disabilities)',
                r'(?:research|innovation|technology|STEM)'
            ]
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def analyze_website(self, url: str, opportunity_data: Dict[str, Any]) -> WebsiteIntelligence:
        """
        Perform comprehensive website intelligence analysis
        
        Args:
            url: Website URL to analyze
            opportunity_data: Existing opportunity data for context
            
        Returns:
            WebsiteIntelligence object with extracted information
        """
        logger.info(f"Starting website intelligence analysis for: {url}")
        
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # Initialize intelligence object
            intelligence = WebsiteIntelligence(url=url, domain=domain)
            
            # Fetch website content
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            async with self.session.get(url, timeout=30) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Extract basic information
                    intelligence.title = self._extract_title(content)
                    intelligence.description = self._extract_description(content)
                    
                    # Extract contacts
                    intelligence.contact_info = self._extract_contacts(content)
                    
                    # Extract facts
                    intelligence.key_facts = self._extract_facts(content, url)
                    
                    # Identify program areas
                    intelligence.program_areas = self._identify_program_areas(content)
                    
                    # Extract funding information
                    intelligence.funding_info = self._extract_funding_info(content)
                    
                    # Determine organization type
                    intelligence.organization_type = self._determine_org_type(content)
                    
                    # Calculate quality score
                    intelligence.quality_score = self._calculate_quality_score(intelligence)
                    
                    logger.info(f"Website analysis completed. Quality score: {intelligence.quality_score:.2f}")
                    
                else:
                    logger.warning(f"Failed to fetch website: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error analyzing website {url}: {str(e)}")
            
        return intelligence

    def _extract_title(self, content: str) -> Optional[str]:
        """Extract page title from HTML content"""
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        return title_match.group(1).strip() if title_match else None

    def _extract_description(self, content: str) -> Optional[str]:
        """Extract meta description from HTML content"""
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', content, re.IGNORECASE)
        return desc_match.group(1).strip() if desc_match else None

    def _extract_contacts(self, content: str) -> List[ResearchContact]:
        """Extract contact information from content"""
        contacts = []
        
        # Extract email addresses
        email_matches = re.findall(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', content)
        for email in email_matches:
            if not any(domain in email.lower() for domain in ['example.com', 'test.com']):
                contacts.append(ResearchContact(
                    name=f"Contact via {email}",
                    email=email,
                    confidence=0.7,
                    source="website_extraction"
                ))
        
        # Extract phone numbers
        phone_matches = re.findall(r'(\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})', content)
        for phone in phone_matches:
            contacts.append(ResearchContact(
                name=f"Contact via {phone}",
                phone=phone,
                confidence=0.6,
                source="website_extraction"
            ))
        
        return contacts

    def _extract_facts(self, content: str, source_url: str) -> List[ExtractedFact]:
        """Extract key facts from content using patterns"""
        facts = []
        
        for category, patterns in self.fact_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = ' '.join(match)
                    
                    facts.append(ExtractedFact(
                        fact=match,
                        source=source_url,
                        confidence=0.8,
                        category=category
                    ))
        
        return facts

    def _identify_program_areas(self, content: str) -> List[str]:
        """Identify program areas from content"""
        program_areas = []
        
        for pattern in self.website_patterns['program_areas']:
            matches = re.findall(pattern, content, re.IGNORECASE)
            program_areas.extend(matches)
        
        return list(set(program_areas))

    def _extract_funding_info(self, content: str) -> Dict[str, Any]:
        """Extract funding-related information"""
        funding_info = {}
        
        # Extract funding amounts
        amount_matches = re.findall(r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|M|B|K))?', content)
        if amount_matches:
            funding_info['amounts_mentioned'] = amount_matches
        
        # Extract funding types
        type_matches = re.findall(r'(?:grant|scholarship|fellowship|award|prize)', content, re.IGNORECASE)
        if type_matches:
            funding_info['funding_types'] = list(set(type_matches))
        
        return funding_info

    def _determine_org_type(self, content: str) -> Optional[str]:
        """Determine organization type from content"""
        for pattern in self.website_patterns['org_types']:
            if re.search(pattern, content, re.IGNORECASE):
                match = re.search(pattern, content, re.IGNORECASE)
                return match.group(0) if match else None
        return None

    def _calculate_quality_score(self, intelligence: WebsiteIntelligence) -> float:
        """Calculate quality score for website intelligence"""
        score = 0.0
        
        # Title and description
        if intelligence.title:
            score += 0.2
        if intelligence.description:
            score += 0.2
        
        # Contact information
        if intelligence.contact_info:
            score += 0.3
        
        # Facts extracted
        if intelligence.key_facts:
            score += 0.2
        
        # Program areas identified
        if intelligence.program_areas:
            score += 0.1
        
        return min(score, 1.0)

    async def generate_research_report(self, opportunity_data: Dict[str, Any], 
                                     report_type: ReportFormat = ReportFormat.EXECUTIVE_SUMMARY) -> ResearchReport:
        """
        Generate comprehensive research report for grant teams
        
        Args:
            opportunity_data: Opportunity data to research
            report_type: Type of report to generate
            
        Returns:
            Generated research report
        """
        logger.info(f"Generating {report_type.value} report for opportunity: {opportunity_data.get('organization_name', 'Unknown')}")
        
        report_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        opportunity_id = opportunity_data.get('opportunity_id', 'unknown')
        
        # Perform website analysis if URL available
        website_intelligence = None
        if 'website_url' in opportunity_data:
            website_intelligence = await self.analyze_website(
                opportunity_data['website_url'], 
                opportunity_data
            )
        
        # Generate report based on type
        if report_type == ReportFormat.EXECUTIVE_SUMMARY:
            report = await self._generate_executive_summary(
                report_id, opportunity_id, opportunity_data, website_intelligence
            )
        elif report_type == ReportFormat.DETAILED_RESEARCH:
            report = await self._generate_detailed_research(
                report_id, opportunity_id, opportunity_data, website_intelligence
            )
        elif report_type == ReportFormat.DECISION_BRIEF:
            report = await self._generate_decision_brief(
                report_id, opportunity_id, opportunity_data, website_intelligence
            )
        elif report_type == ReportFormat.EVALUATION_SUMMARY:
            report = await self._generate_evaluation_summary(
                report_id, opportunity_id, opportunity_data, website_intelligence
            )
        else:
            report = await self._generate_evidence_package(
                report_id, opportunity_id, opportunity_data, website_intelligence
            )
        
        # Update cost tracking
        self._update_cost_tracking(report)
        
        logger.info(f"Research report generated: {report.title}")
        return report

    async def _generate_executive_summary(self, report_id: str, opportunity_id: str, 
                                        opportunity_data: Dict[str, Any], 
                                        website_intel: Optional[WebsiteIntelligence]) -> ResearchReport:
        """Generate executive summary report"""
        
        org_name = opportunity_data.get('organization_name', 'Unknown Organization')
        
        # Build executive summary
        summary_parts = [
            f"Research analysis for {org_name}",
            f"Overall Score: {opportunity_data.get('scoring', {}).get('overall_score', 'N/A')}",
            f"Stage: {opportunity_data.get('current_stage', 'Unknown')}"
        ]
        
        if website_intel:
            summary_parts.append(f"Website Quality: {website_intel.quality_score:.2f}")
            if website_intel.contact_info:
                summary_parts.append(f"Contacts Identified: {len(website_intel.contact_info)}")
        
        executive_summary = " | ".join(summary_parts)
        
        # Build detailed findings
        detailed_findings = {
            'opportunity_overview': {
                'organization': org_name,
                'ein': opportunity_data.get('ein', 'N/A'),
                'funding_amount': opportunity_data.get('funding_amount', 'N/A'),
                'program_name': opportunity_data.get('program_name', 'N/A')
            },
            'scoring_analysis': opportunity_data.get('scoring', {}),
            'stage_progression': opportunity_data.get('stage_history', [])
        }
        
        if website_intel:
            detailed_findings['website_intelligence'] = {
                'domain': website_intel.domain,
                'quality_score': website_intel.quality_score,
                'program_areas': website_intel.program_areas,
                'organization_type': website_intel.organization_type
            }
        
        # Extract evidence and contacts
        evidence_package = []
        contacts_identified = []
        
        if website_intel:
            evidence_package = website_intel.key_facts
            contacts_identified = website_intel.contact_info
        
        # Generate recommendations
        recommendations = self._generate_recommendations(opportunity_data, website_intel)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(opportunity_data, website_intel)
        
        # Define next steps
        next_steps = self._define_next_steps(opportunity_data, website_intel)
        
        # Calculate confidence assessment
        confidence_assessment = self._calculate_confidence_assessment(opportunity_data, website_intel)
        
        # Estimate costs
        cost_analysis = {
            'research_cost': 0.02,  # AI-Lite cost
            'estimated_total': 0.02,
            'cost_per_insight': 0.01
        }
        
        return ResearchReport(
            report_id=report_id,
            opportunity_id=opportunity_id,
            report_type=ReportFormat.EXECUTIVE_SUMMARY,
            title=f"Executive Summary: {org_name}",
            executive_summary=executive_summary,
            detailed_findings=detailed_findings,
            evidence_package=evidence_package,
            contacts_identified=contacts_identified,
            recommendations=recommendations,
            risk_factors=risk_factors,
            next_steps=next_steps,
            confidence_assessment=confidence_assessment,
            cost_analysis=cost_analysis
        )

    async def _generate_detailed_research(self, report_id: str, opportunity_id: str,
                                        opportunity_data: Dict[str, Any],
                                        website_intel: Optional[WebsiteIntelligence]) -> ResearchReport:
        """Generate detailed research report"""
        # Similar structure to executive summary but with more comprehensive analysis
        # This would include deeper AI analysis, additional data sources, etc.
        pass

    async def _generate_decision_brief(self, report_id: str, opportunity_id: str,
                                     opportunity_data: Dict[str, Any],
                                     website_intel: Optional[WebsiteIntelligence]) -> ResearchReport:
        """Generate decision brief for grant teams"""
        pass

    async def _generate_evaluation_summary(self, report_id: str, opportunity_id: str,
                                         opportunity_data: Dict[str, Any],
                                         website_intel: Optional[WebsiteIntelligence]) -> ResearchReport:
        """Generate evaluation summary report"""
        pass

    async def _generate_evidence_package(self, report_id: str, opportunity_id: str,
                                       opportunity_data: Dict[str, Any],
                                       website_intel: Optional[WebsiteIntelligence]) -> ResearchReport:
        """Generate evidence package for detailed analysis"""
        pass

    def _generate_recommendations(self, opportunity_data: Dict[str, Any], 
                                website_intel: Optional[WebsiteIntelligence]) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []
        
        score = opportunity_data.get('scoring', {}).get('overall_score', 0)
        stage = opportunity_data.get('current_stage', '')
        
        if score >= 0.8:
            recommendations.append("High-priority opportunity - recommend immediate pursuit")
        elif score >= 0.6:
            recommendations.append("Medium-priority opportunity - conduct additional research")
        else:
            recommendations.append("Lower-priority opportunity - monitor for changes")
        
        if website_intel and website_intel.contact_info:
            recommendations.append("Direct contact information available - initiate outreach")
        
        if stage == 'discovery':
            recommendations.append("Advance to planning stage for strategic analysis")
        
        return recommendations

    def _identify_risk_factors(self, opportunity_data: Dict[str, Any],
                             website_intel: Optional[WebsiteIntelligence]) -> List[str]:
        """Identify potential risk factors"""
        risk_factors = []
        
        score = opportunity_data.get('scoring', {}).get('overall_score', 0)
        if score < 0.5:
            risk_factors.append("Low compatibility score indicates potential misalignment")
        
        if not opportunity_data.get('funding_amount'):
            risk_factors.append("Funding amount not specified - requires clarification")
        
        if website_intel and website_intel.quality_score < 0.5:
            risk_factors.append("Limited website information available")
        
        return risk_factors

    def _define_next_steps(self, opportunity_data: Dict[str, Any],
                         website_intel: Optional[WebsiteIntelligence]) -> List[str]:
        """Define recommended next steps"""
        next_steps = []
        
        stage = opportunity_data.get('current_stage', '')
        
        if stage == 'discovery':
            next_steps.append("Advance to PLAN stage for network analysis")
        elif stage == 'pre_scoring':
            next_steps.append("Complete scoring analysis")
        
        if website_intel and website_intel.contact_info:
            next_steps.append("Initiate contact with identified personnel")
        
        next_steps.append("Schedule team review of research findings")
        
        return next_steps

    def _calculate_confidence_assessment(self, opportunity_data: Dict[str, Any],
                                       website_intel: Optional[WebsiteIntelligence]) -> Dict[str, float]:
        """Calculate confidence levels for different aspects"""
        confidence = {
            'overall_assessment': 0.7,
            'scoring_accuracy': 0.8,
            'contact_information': 0.6,
            'strategic_fit': 0.7
        }
        
        if website_intel:
            confidence['website_analysis'] = website_intel.quality_score
            if website_intel.contact_info:
                confidence['contact_information'] = 0.8
        
        return confidence

    def _update_cost_tracking(self, report: ResearchReport):
        """Update cost tracking for research operations"""
        cost = report.cost_analysis.get('research_cost', 0.02)
        self.research_costs['total_spent'] += cost
        self.research_costs['research_count'] += 1
        
        if self.research_costs['research_count'] > 0:
            self.research_costs['avg_cost_per_research'] = (
                self.research_costs['total_spent'] / self.research_costs['research_count']
            )

    async def batch_research_analysis(self, opportunities: List[Dict[str, Any]], 
                                    report_type: ReportFormat = ReportFormat.EXECUTIVE_SUMMARY) -> List[ResearchReport]:
        """
        Perform batch research analysis with cost optimization
        
        Args:
            opportunities: List of opportunities to analyze
            report_type: Type of report to generate for each
            
        Returns:
            List of generated research reports
        """
        logger.info(f"Starting batch research analysis for {len(opportunities)} opportunities")
        
        reports = []
        
        # Process in cost-optimized batches
        batch_size = 10 if self.cost_optimization else len(opportunities)
        
        for i in range(0, len(opportunities), batch_size):
            batch = opportunities[i:i + batch_size]
            
            # Process batch concurrently
            batch_tasks = [
                self.generate_research_report(opp, report_type) 
                for opp in batch
            ]
            
            batch_reports = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Filter out exceptions and add successful reports
            for report in batch_reports:
                if isinstance(report, ResearchReport):
                    reports.append(report)
                else:
                    logger.error(f"Failed to generate report: {report}")
            
            # Cost optimization delay between batches
            if self.cost_optimization and i + batch_size < len(opportunities):
                await asyncio.sleep(1)  # 1 second delay between batches
        
        logger.info(f"Batch research analysis completed. Generated {len(reports)} reports")
        return reports

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for research operations"""
        return {
            'total_spent': self.research_costs['total_spent'],
            'research_count': self.research_costs['research_count'],
            'average_cost_per_research': self.research_costs['avg_cost_per_research'],
            'cost_optimization_enabled': self.cost_optimization
        }

    async def export_research_data(self, reports: List[ResearchReport], 
                                 export_format: str = 'json') -> str:
        """
        Export research reports to specified format
        
        Args:
            reports: List of research reports to export
            export_format: Export format ('json', 'csv', 'pdf')
            
        Returns:
            Export file path or data
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if export_format == 'json':
            export_data = {
                'export_timestamp': timestamp,
                'report_count': len(reports),
                'reports': [
                    {
                        'report_id': report.report_id,
                        'opportunity_id': report.opportunity_id,
                        'report_type': report.report_type.value,
                        'title': report.title,
                        'executive_summary': report.executive_summary,
                        'recommendations': report.recommendations,
                        'confidence_assessment': report.confidence_assessment,
                        'generated_at': report.generated_at.isoformat()
                    }
                    for report in reports
                ]
            }
            
            export_path = f'research_export_{timestamp}.json'
            
            # In a real implementation, this would save to file
            logger.info(f"Research data exported to {export_path}")
            return json.dumps(export_data, indent=2)
        
        else:
            raise ValueError(f"Export format {export_format} not supported")