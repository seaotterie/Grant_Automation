"""
Form 990/990-PF Data Mining Engine - Phase 2 Week 11-12 Implementation

Implements comprehensive 990/990-PF data mining with:
- Financial health indicators extraction
- Unsolicited request opportunity analysis  
- Governance intelligence mining
- Program compatibility assessment
- Hidden opportunity identification through narrative analysis

This provides the deep 990 data mining layer for the PLAN stage intelligence.
"""

import asyncio
import logging
import pandas as pd
import numpy as np
import re
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from enum import Enum
import json

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile

logger = logging.getLogger(__name__)


class FinancialHealthRating(Enum):
    """Financial health rating categories."""
    EXCELLENT = "excellent"      # Strong financial position
    GOOD = "good"               # Stable financial position  
    FAIR = "fair"               # Adequate financial position
    POOR = "poor"               # Concerning financial position
    CRITICAL = "critical"       # Severe financial distress


class GovernanceQuality(Enum):
    """Governance quality assessment levels."""
    EXCEPTIONAL = "exceptional"  # Best-in-class governance
    STRONG = "strong"           # Well-governed organization
    ADEQUATE = "adequate"       # Standard governance practices
    WEAK = "weak"               # Governance concerns
    DEFICIENT = "deficient"     # Serious governance issues


@dataclass
class FinancialHealthIndicators:
    """Comprehensive financial health indicators from 990 data."""
    revenue_trend: str = ""  # increasing, stable, decreasing
    revenue_growth_rate: float = 0.0
    revenue_diversification_score: float = 0.0
    
    expense_ratio: float = 0.0
    program_expense_ratio: float = 0.0
    administrative_ratio: float = 0.0
    fundraising_ratio: float = 0.0
    
    asset_growth_rate: float = 0.0
    liquidity_ratio: float = 0.0
    working_capital: float = 0.0
    
    financial_efficiency_score: float = 0.0
    financial_stability_score: float = 0.0
    overall_financial_health: FinancialHealthRating = FinancialHealthRating.FAIR
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'revenue_trend': self.revenue_trend,
            'revenue_growth_rate': round(self.revenue_growth_rate, 3),
            'revenue_diversification_score': round(self.revenue_diversification_score, 3),
            'expense_ratio': round(self.expense_ratio, 3),
            'program_expense_ratio': round(self.program_expense_ratio, 3),
            'administrative_ratio': round(self.administrative_ratio, 3),
            'fundraising_ratio': round(self.fundraising_ratio, 3),
            'asset_growth_rate': round(self.asset_growth_rate, 3),
            'liquidity_ratio': round(self.liquidity_ratio, 3),
            'working_capital': self.working_capital,
            'financial_efficiency_score': round(self.financial_efficiency_score, 3),
            'financial_stability_score': round(self.financial_stability_score, 3),
            'overall_financial_health': self.overall_financial_health.value
        }


@dataclass
class UnsolicitedOpportunity:
    """Unsolicited funding opportunity identified from 990-PF data."""
    foundation_ein: str
    foundation_name: str
    accepts_unsolicited: bool = False
    
    # Application process intelligence
    application_process_description: str = ""
    application_deadlines: List[str] = field(default_factory=list)
    contact_information: Dict[str, str] = field(default_factory=dict)
    
    # Grant characteristics  
    typical_grant_range: Tuple[float, float] = (0.0, 0.0)
    focus_areas: List[str] = field(default_factory=list)
    geographic_restrictions: List[str] = field(default_factory=list)
    
    # Opportunity indicators
    recent_similar_grants: List[Dict[str, Any]] = field(default_factory=list)
    opportunity_signals: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'foundation_ein': self.foundation_ein,
            'foundation_name': self.foundation_name,
            'accepts_unsolicited': self.accepts_unsolicited,
            'application_process_description': self.application_process_description,
            'application_deadlines': self.application_deadlines,
            'contact_information': self.contact_information,
            'typical_grant_range': self.typical_grant_range,
            'focus_areas': self.focus_areas,
            'geographic_restrictions': self.geographic_restrictions,
            'recent_similar_grants': self.recent_similar_grants,
            'opportunity_signals': self.opportunity_signals,
            'confidence_score': round(self.confidence_score, 3)
        }


@dataclass
class GovernanceIntelligence:
    """Governance intelligence extracted from 990 data."""
    board_size: int = 0
    board_independence_score: float = 0.0
    
    # Compensation analysis
    executive_compensation: Dict[str, float] = field(default_factory=dict)
    board_compensation: float = 0.0
    compensation_reasonableness: str = ""
    
    # Meeting and oversight
    board_meetings_per_year: int = 0
    committee_structure: List[str] = field(default_factory=list)
    
    # Policies and procedures
    conflict_of_interest_policy: bool = False
    whistleblower_policy: bool = False
    document_retention_policy: bool = False
    
    # Governance metrics
    governance_quality_score: float = 0.0
    governance_quality: GovernanceQuality = GovernanceQuality.ADEQUATE
    governance_strengths: List[str] = field(default_factory=list)
    governance_concerns: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'board_size': self.board_size,
            'board_independence_score': round(self.board_independence_score, 3),
            'executive_compensation': self.executive_compensation,
            'board_compensation': self.board_compensation,
            'compensation_reasonableness': self.compensation_reasonableness,
            'board_meetings_per_year': self.board_meetings_per_year,
            'committee_structure': self.committee_structure,
            'conflict_of_interest_policy': self.conflict_of_interest_policy,
            'whistleblower_policy': self.whistleblower_policy,
            'document_retention_policy': self.document_retention_policy,
            'governance_quality_score': round(self.governance_quality_score, 3),
            'governance_quality': self.governance_quality.value,
            'governance_strengths': self.governance_strengths,
            'governance_concerns': self.governance_concerns
        }


@dataclass
class HiddenOpportunity:
    """Hidden opportunity identified through narrative analysis."""
    opportunity_type: str  # strategic_initiative, capacity_need, partnership_signal, etc.
    description: str
    source_section: str  # Which part of 990 this was found in
    confidence_level: float  # 0.0 to 1.0
    strategic_value: float   # 0.0 to 1.0
    
    # Context
    organization_ein: str
    organization_name: str
    related_text: str = ""
    
    # Opportunity details
    potential_funding_need: Optional[float] = None
    timing_indicators: List[str] = field(default_factory=list)
    action_recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'opportunity_type': self.opportunity_type,
            'description': self.description,
            'source_section': self.source_section,
            'confidence_level': round(self.confidence_level, 3),
            'strategic_value': round(self.strategic_value, 3),
            'organization_ein': self.organization_ein,
            'organization_name': self.organization_name,
            'related_text': self.related_text,
            'potential_funding_need': self.potential_funding_need,
            'timing_indicators': self.timing_indicators,
            'action_recommendations': self.action_recommendations
        }


class Form990DataMiningEngine(BaseProcessor):
    """
    Comprehensive 990/990-PF Data Mining Engine.
    
    Implements Phase 2 Week 11-12 requirements:
    - Comprehensive 990/990-PF data mining
    - Unsolicited request analysis system
    - Financial health indicators
    - Governance intelligence 
    - Hidden opportunity identification through narrative analysis
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="form_990_data_mining_engine",
            description="Comprehensive 990/990-PF data mining with financial, governance, and opportunity analysis",
            version="2.0.0",
            dependencies=["foundation_intelligence_engine"],
            estimated_duration=240,  # 4 minutes for comprehensive data mining
            requires_network=False,
            requires_api_key=False,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Data mining targets and weights
        self.mining_targets = {
            'financial_health_indicators': ['revenue_trends', 'expense_ratios', 'asset_growth'],
            'unsolicited_request_opportunities': ['990_pf_checkbox', 'application_processes'],
            'governance_intelligence': ['board_compensation', 'meeting_frequency', 'governance_quality'],
            'program_compatibility': ['program_expenses', 'activity_descriptions', 'outcome_metrics'],
            'hidden_opportunities': ['non_standard_data', 'narrative_analysis', 'timing_signals']
        }
        
        # Opportunity detection patterns
        self.opportunity_patterns = {
            'expansion_signals': [
                r'expand\w*\s+(?:program|service|operation)',
                r'new\s+(?:initiative|program|location)',
                r'grow\w*\s+(?:capacity|reach|impact)'
            ],
            'capacity_needs': [
                r'(?:need|require|seek)\s+(?:funding|support|resources)',
                r'(?:lack|insufficient|limited)\s+(?:capacity|resources)',
                r'(?:challenge|difficulty|constraint)'
            ],
            'partnership_signals': [
                r'collaborate\w*\s+(?:with|on)',
                r'partnership\s+(?:opportunity|potential)',
                r'joint\s+(?:venture|initiative|program)'
            ],
            'strategic_initiatives': [
                r'strategic\s+(?:plan|initiative|goal)',
                r'(?:priority|focus)\s+(?:area|initiative)',
                r'multi-year\s+(?:plan|strategy|commitment)'
            ]
        }
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute comprehensive 990/990-PF data mining analysis."""
        start_time = datetime.now()
        
        try:
            self.logger.info("Starting Form 990 Data Mining Engine")
            
            # Get organizations and their 990 data
            organizations = await self._get_input_organizations(config, workflow_state)
            form_990_data = await self._extract_990_data(config, workflow_state)
            
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No organizations found for 990 data mining"]
                )
            
            # Phase 1: Mine financial health indicators
            financial_health_analysis = await self._mine_financial_health_indicators(
                organizations, form_990_data
            )
            
            # Phase 2: Identify unsolicited funding opportunities  
            unsolicited_opportunities = await self._mine_990_pf_opportunities(form_990_data)
            
            # Phase 3: Extract governance intelligence
            governance_analysis = await self._mine_governance_intelligence(
                organizations, form_990_data
            )
            
            # Phase 4: Analyze program compatibility
            program_compatibility = await self._analyze_program_compatibility(
                organizations, form_990_data
            )
            
            # Phase 5: Identify hidden opportunities through narrative analysis
            hidden_opportunities = await self._identify_hidden_opportunities(
                organizations, form_990_data
            )
            
            # Phase 6: Generate comprehensive insights and recommendations
            data_mining_insights = self._generate_data_mining_insights(
                financial_health_analysis, unsolicited_opportunities, 
                governance_analysis, hidden_opportunities
            )
            
            # Prepare comprehensive results
            result_data = {
                "data_mining_summary": {
                    "organizations_analyzed": len(organizations),
                    "990_forms_processed": len(form_990_data),
                    "unsolicited_opportunities_found": len(unsolicited_opportunities),
                    "hidden_opportunities_identified": len(hidden_opportunities),
                    "analysis_timestamp": start_time.isoformat()
                },
                "financial_health_analysis": financial_health_analysis,
                "unsolicited_opportunities": [opp.to_dict() for opp in unsolicited_opportunities],
                "governance_analysis": governance_analysis,
                "program_compatibility": program_compatibility,
                "hidden_opportunities": [opp.to_dict() for opp in hidden_opportunities],
                "data_mining_insights": data_mining_insights
            }
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                start_time=start_time,
                end_time=datetime.now(),
                data=result_data
            )
            
        except Exception as e:
            self.logger.error(f"Form 990 Data Mining Engine failed: {str(e)}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                start_time=start_time,
                end_time=datetime.now(),
                errors=[f"990 data mining error: {str(e)}"]
            )
    
    async def _extract_990_data(self, config: ProcessorConfig, workflow_state) -> List[Dict[str, Any]]:
        """Extract 990/990-PF data from various sources."""
        form_990_data = []
        
        # Try to get from workflow state
        if workflow_state and hasattr(workflow_state, 'form_990_data'):
            form_990_data.extend(workflow_state.form_990_data)
        
        # Try to get from config input data
        if config.input_data and '990_data' in config.input_data:
            form_990_data.extend(config.input_data['990_data'])
        
        # Extract from organization financial data
        organizations = await self._get_input_organizations(config, workflow_state)
        for org in organizations:
            org_990_data = self._extract_org_990_data(org)
            if org_990_data:
                form_990_data.append(org_990_data)
        
        return form_990_data
    
    def _extract_org_990_data(self, org: OrganizationProfile) -> Optional[Dict[str, Any]]:
        """Extract available 990 data from organization profile."""
        ein = getattr(org, 'ein', '')
        if not ein:
            return None
        
        return {
            'ein': ein,
            'name': getattr(org, 'name', ''),
            'revenue': getattr(org, 'revenue', None),
            'assets': getattr(org, 'assets', None),
            'expenses': getattr(org, 'expenses', None),
            'program_expenses': getattr(org, 'program_expenses', None),
            'program_expense_ratio': getattr(org, 'program_expense_ratio', None),
            'administrative_ratio': getattr(org, 'administrative_ratio', None),
            'fundraising_efficiency': getattr(org, 'fundraising_efficiency', None),
            'financial_history': getattr(org, 'financial_history', []),
            'board_members': getattr(org, 'board_members', []),
            'key_personnel': getattr(org, 'key_personnel', []),
            'mission_description': getattr(org, 'mission_description', ''),
            'activity_description': getattr(org, 'activity_description', ''),
            'grant_recipients': getattr(org, 'grant_recipients', [])
        }
    
    async def _mine_financial_health_indicators(self, organizations: List[OrganizationProfile], 
                                              form_990_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Phase 2 Requirement: Financial health indicators extraction.
        
        Extracts comprehensive financial health indicators from 990 data.
        """
        financial_analysis = {}
        
        for org in organizations:
            org_ein = getattr(org, 'ein', '')
            if not org_ein:
                continue
            
            # Find corresponding 990 data
            org_990 = next((data for data in form_990_data if data.get('ein') == org_ein), None)
            if not org_990:
                continue
            
            # Build financial health indicators
            indicators = FinancialHealthIndicators()
            
            # Revenue trend analysis
            financial_history = org_990.get('financial_history', [])
            if len(financial_history) >= 2:
                revenues = [year.get('revenue', 0) for year in financial_history if year.get('revenue')]
                if len(revenues) >= 2:
                    indicators.revenue_growth_rate = self._calculate_growth_rate(revenues)
                    indicators.revenue_trend = self._determine_trend(revenues)
            
            # Expense ratios
            revenue = org_990.get('revenue', 0)
            expenses = org_990.get('expenses', 0)
            program_expenses = org_990.get('program_expenses', 0)
            
            if revenue and revenue > 0:
                indicators.expense_ratio = expenses / revenue if expenses else 0.0
                indicators.program_expense_ratio = (
                    org_990.get('program_expense_ratio', 0) or 
                    (program_expenses / revenue if program_expenses else 0.0)
                )
                indicators.administrative_ratio = org_990.get('administrative_ratio', 0)
                indicators.fundraising_ratio = org_990.get('fundraising_efficiency', 0)
            
            # Asset analysis
            assets = org_990.get('assets', 0)
            if assets and len(financial_history) >= 2:
                asset_values = [year.get('assets', 0) for year in financial_history if year.get('assets')]
                if len(asset_values) >= 2:
                    indicators.asset_growth_rate = self._calculate_growth_rate(asset_values)
            
            # Liquidity analysis (simplified)
            if assets and expenses:
                indicators.liquidity_ratio = assets / (expenses / 12) if expenses > 0 else 0.0  # Months of expenses
            
            # Calculate composite scores
            indicators.financial_efficiency_score = self._calculate_efficiency_score(indicators)
            indicators.financial_stability_score = self._calculate_stability_score(indicators)
            indicators.overall_financial_health = self._determine_financial_health_rating(indicators)
            
            financial_analysis[org_ein] = {
                'organization_name': getattr(org, 'name', ''),
                'financial_indicators': indicators.to_dict(),
                'key_strengths': self._identify_financial_strengths(indicators),
                'areas_of_concern': self._identify_financial_concerns(indicators),
                'investment_readiness': self._assess_investment_readiness(indicators)
            }
        
        return financial_analysis
    
    def _calculate_growth_rate(self, values: List[float]) -> float:
        """Calculate compound annual growth rate."""
        if len(values) < 2 or values[0] == 0:
            return 0.0
        
        first_value = values[0]
        last_value = values[-1]
        years = len(values) - 1
        
        if first_value <= 0:
            return 0.0
        
        return ((last_value / first_value) ** (1 / years)) - 1
    
    def _determine_trend(self, values: List[float]) -> str:
        """Determine trend direction from values."""
        if len(values) < 2:
            return "stable"
        
        increasing_count = 0
        decreasing_count = 0
        
        for i in range(1, len(values)):
            if values[i] > values[i-1]:
                increasing_count += 1
            elif values[i] < values[i-1]:
                decreasing_count += 1
        
        if increasing_count > decreasing_count:
            return "increasing"
        elif decreasing_count > increasing_count:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_efficiency_score(self, indicators: FinancialHealthIndicators) -> float:
        """Calculate financial efficiency score."""
        score = 0.0
        
        # Program expense ratio (higher is better, optimal around 0.75-0.85)
        if indicators.program_expense_ratio > 0:
            if 0.75 <= indicators.program_expense_ratio <= 0.85:
                score += 0.4
            elif 0.65 <= indicators.program_expense_ratio < 0.75:
                score += 0.3
            elif 0.85 < indicators.program_expense_ratio <= 0.90:
                score += 0.3
            else:
                score += 0.1
        
        # Administrative ratio (lower is better, optimal below 0.15)
        if indicators.administrative_ratio > 0:
            if indicators.administrative_ratio <= 0.10:
                score += 0.3
            elif indicators.administrative_ratio <= 0.15:
                score += 0.2
            elif indicators.administrative_ratio <= 0.25:
                score += 0.1
        
        # Fundraising ratio (lower is better, optimal below 0.10)
        if indicators.fundraising_ratio > 0:
            if indicators.fundraising_ratio <= 0.05:
                score += 0.3
            elif indicators.fundraising_ratio <= 0.10:
                score += 0.2
            elif indicators.fundraising_ratio <= 0.20:
                score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_stability_score(self, indicators: FinancialHealthIndicators) -> float:
        """Calculate financial stability score."""
        score = 0.0
        
        # Revenue growth (stable positive growth is best)
        if -0.05 <= indicators.revenue_growth_rate <= 0.15:  # Stable growth
            score += 0.4
        elif 0.15 < indicators.revenue_growth_rate <= 0.30:  # High growth
            score += 0.3
        elif -0.10 <= indicators.revenue_growth_rate < -0.05:  # Mild decline
            score += 0.2
        
        # Asset growth
        if indicators.asset_growth_rate > 0:
            score += 0.3
        elif indicators.asset_growth_rate >= -0.05:
            score += 0.1
        
        # Liquidity (months of expenses covered)
        if indicators.liquidity_ratio >= 12:  # 1 year of expenses
            score += 0.3
        elif indicators.liquidity_ratio >= 6:   # 6 months
            score += 0.2
        elif indicators.liquidity_ratio >= 3:   # 3 months
            score += 0.1
        
        return min(score, 1.0)
    
    def _determine_financial_health_rating(self, indicators: FinancialHealthIndicators) -> FinancialHealthRating:
        """Determine overall financial health rating."""
        avg_score = (indicators.financial_efficiency_score + indicators.financial_stability_score) / 2
        
        if avg_score >= 0.8:
            return FinancialHealthRating.EXCELLENT
        elif avg_score >= 0.6:
            return FinancialHealthRating.GOOD
        elif avg_score >= 0.4:
            return FinancialHealthRating.FAIR
        elif avg_score >= 0.2:
            return FinancialHealthRating.POOR
        else:
            return FinancialHealthRating.CRITICAL
    
    def _identify_financial_strengths(self, indicators: FinancialHealthIndicators) -> List[str]:
        """Identify financial strengths."""
        strengths = []
        
        if indicators.program_expense_ratio >= 0.75:
            strengths.append("High program expense ratio - efficient program delivery")
        
        if indicators.administrative_ratio <= 0.15:
            strengths.append("Low administrative costs - efficient operations")
        
        if indicators.revenue_growth_rate > 0.05:
            strengths.append("Positive revenue growth trend")
        
        if indicators.liquidity_ratio >= 6:
            strengths.append("Strong liquidity position")
        
        return strengths
    
    def _identify_financial_concerns(self, indicators: FinancialHealthIndicators) -> List[str]:
        """Identify financial concerns."""
        concerns = []
        
        if indicators.program_expense_ratio < 0.65:
            concerns.append("Low program expense ratio - may indicate inefficient resource allocation")
        
        if indicators.administrative_ratio > 0.25:
            concerns.append("High administrative costs")
        
        if indicators.revenue_growth_rate < -0.10:
            concerns.append("Declining revenue trend")
        
        if indicators.liquidity_ratio < 3:
            concerns.append("Limited liquidity - potential cash flow issues")
        
        return concerns
    
    def _assess_investment_readiness(self, indicators: FinancialHealthIndicators) -> str:
        """Assess readiness for investment/grants."""
        if indicators.overall_financial_health in [FinancialHealthRating.EXCELLENT, FinancialHealthRating.GOOD]:
            if indicators.revenue_growth_rate > 0:
                return "High investment readiness - strong growth potential"
            else:
                return "Good investment readiness - stable foundation"
        elif indicators.overall_financial_health == FinancialHealthRating.FAIR:
            return "Moderate investment readiness - may need capacity building support"
        else:
            return "Low investment readiness - requires financial stabilization"
    
    async def _mine_990_pf_opportunities(self, form_990_data: List[Dict[str, Any]]) -> List[UnsolicitedOpportunity]:
        """
        Phase 2 Requirement: Extract unsolicited funding opportunities from 990-PF data.
        
        Mines 990-PF forms for unsolicited proposal opportunities and application processes.
        """
        opportunities = []
        
        for data in form_990_data:
            # Only process foundations (990-PF filers)
            if not self._is_foundation_990_data(data):
                continue
            
            opportunity = UnsolicitedOpportunity(
                foundation_ein=data.get('ein', ''),
                foundation_name=data.get('name', '')
            )
            
            # Analyze grant recipients for patterns
            grant_recipients = data.get('grant_recipients', [])
            if grant_recipients:
                opportunity.recent_similar_grants = grant_recipients[:10]  # Recent grants
                
                # Calculate typical grant range
                grant_amounts = [grant.get('amount', 0) for grant in grant_recipients if grant.get('amount')]
                if grant_amounts:
                    opportunity.typical_grant_range = (min(grant_amounts), max(grant_amounts))
                
                # Extract focus areas from grant purposes
                purposes = [grant.get('purpose', '') for grant in grant_recipients if grant.get('purpose')]
                opportunity.focus_areas = self._extract_focus_areas_from_purposes(purposes)
            
            # Determine if accepts unsolicited proposals (heuristic analysis)
            opportunity.accepts_unsolicited = self._determine_unsolicited_acceptance(data)
            
            # Extract application process information
            opportunity.application_process_description = self._extract_application_process(data)
            
            # Identify opportunity signals
            opportunity.opportunity_signals = self._identify_opportunity_signals(data)
            
            # Calculate confidence score
            opportunity.confidence_score = self._calculate_opportunity_confidence(opportunity)
            
            if opportunity.confidence_score > 0.3:  # Only include promising opportunities
                opportunities.append(opportunity)
        
        return opportunities
    
    def _is_foundation_990_data(self, data: Dict[str, Any]) -> bool:
        """Determine if 990 data is from a foundation."""
        # Check for foundation indicators
        if data.get('grant_recipients'):  # Has grant recipients
            return True
        
        # Check form type
        form_type = data.get('form_type', '')
        if 'pf' in str(form_type).lower():
            return True
        
        return False
    
    def _extract_focus_areas_from_purposes(self, purposes: List[str]) -> List[str]:
        """Extract focus areas from grant purposes."""
        focus_areas = set()
        
        # Define focus area keywords
        focus_keywords = {
            'Education': ['education', 'school', 'student', 'scholarship', 'university', 'learning'],
            'Health': ['health', 'medical', 'hospital', 'healthcare', 'wellness', 'disease'],
            'Arts & Culture': ['arts', 'culture', 'museum', 'music', 'theater', 'cultural'],
            'Environment': ['environment', 'conservation', 'green', 'sustainability', 'nature'],
            'Human Services': ['human services', 'social services', 'poverty', 'homeless', 'food'],
            'Religion': ['religious', 'church', 'faith', 'spiritual', 'ministry'],
            'Community Development': ['community', 'development', 'housing', 'economic', 'neighborhood']
        }
        
        for purpose in purposes:
            purpose_lower = purpose.lower()
            for area, keywords in focus_keywords.items():
                if any(keyword in purpose_lower for keyword in keywords):
                    focus_areas.add(area)
        
        return list(focus_areas)
    
    def _determine_unsolicited_acceptance(self, data: Dict[str, Any]) -> bool:
        """Determine if foundation accepts unsolicited proposals."""
        # Heuristic based on grant patterns and foundation characteristics
        grant_recipients = data.get('grant_recipients', [])
        
        if not grant_recipients:
            return False
        
        # Large number of diverse recipients suggests open application process
        if len(grant_recipients) > 20:
            return True
        
        # Diverse recipient types suggest open process
        recipient_types = set()
        for recipient in grant_recipients:
            name = recipient.get('name', '').lower()
            if any(word in name for word in ['foundation', 'fund', 'institute']):
                recipient_types.add('institutional')
            elif any(word in name for word in ['school', 'university', 'college']):
                recipient_types.add('educational')
            elif any(word in name for word in ['church', 'religious', 'ministry']):
                recipient_types.add('religious')
            else:
                recipient_types.add('other')
        
        return len(recipient_types) >= 3  # Diverse recipients
    
    def _extract_application_process(self, data: Dict[str, Any]) -> str:
        """Extract application process information."""
        # This would typically be extracted from narrative sections of 990-PF
        # For now, provide standard guidance based on foundation type
        grant_count = len(data.get('grant_recipients', []))
        
        if grant_count > 50:
            return "Likely has formal application process given high grant volume"
        elif grant_count > 10:
            return "May have structured application process - contact foundation directly"
        else:
            return "Limited grant activity - may be invitation-only or family foundation"
    
    def _identify_opportunity_signals(self, data: Dict[str, Any]) -> List[str]:
        """Identify opportunity signals from 990-PF data."""
        signals = []
        
        grant_recipients = data.get('grant_recipients', [])
        if not grant_recipients:
            return signals
        
        # Recent activity signal
        if len(grant_recipients) > 5:
            signals.append("Active grantmaking - recent grants awarded")
        
        # Growth in grantmaking
        # This would require multi-year data analysis
        
        # Diverse funding areas
        purposes = [grant.get('purpose', '') for grant in grant_recipients if grant.get('purpose')]
        if len(set(purposes)) > 3:
            signals.append("Diverse funding interests")
        
        # Geographic spread
        states = [grant.get('state', '') for grant in grant_recipients if grant.get('state')]
        if len(set(states)) > 2:
            signals.append("Geographic flexibility in funding")
        
        return signals
    
    def _calculate_opportunity_confidence(self, opportunity: UnsolicitedOpportunity) -> float:
        """Calculate confidence score for opportunity."""
        score = 0.0
        
        # Base score for unsolicited acceptance
        if opportunity.accepts_unsolicited:
            score += 0.5
        else:
            score += 0.2  # Still possible through networking
        
        # Recent grant activity
        if len(opportunity.recent_similar_grants) > 10:
            score += 0.3
        elif len(opportunity.recent_similar_grants) > 5:
            score += 0.2
        
        # Opportunity signals
        score += len(opportunity.opportunity_signals) * 0.05
        
        # Focus area clarity
        if opportunity.focus_areas:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _mine_governance_intelligence(self, organizations: List[OrganizationProfile], 
                                          form_990_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Phase 2 Requirement: Governance intelligence mining.
        
        Extracts governance intelligence including board composition, compensation, and policies.
        """
        governance_analysis = {}
        
        for org in organizations:
            org_ein = getattr(org, 'ein', '')
            if not org_ein:
                continue
            
            # Find corresponding 990 data
            org_990 = next((data for data in form_990_data if data.get('ein') == org_ein), None)
            if not org_990:
                continue
            
            # Build governance intelligence
            governance = GovernanceIntelligence()
            
            # Board analysis
            board_members = org_990.get('board_members', [])
            governance.board_size = len(board_members)
            
            # Extract executive compensation (simplified)
            key_personnel = org_990.get('key_personnel', [])
            for person in key_personnel:
                if isinstance(person, dict) and person.get('compensation'):
                    role = person.get('role', '').lower()
                    if any(title in role for title in ['ceo', 'executive', 'president', 'director']):
                        governance.executive_compensation[person.get('name', '')] = person.get('compensation', 0)
            
            # Governance quality assessment
            governance.governance_quality_score = self._calculate_governance_score(governance)
            governance.governance_quality = self._determine_governance_quality(governance.governance_quality_score)
            
            # Identify strengths and concerns
            governance.governance_strengths = self._identify_governance_strengths(governance)
            governance.governance_concerns = self._identify_governance_concerns(governance)
            
            governance_analysis[org_ein] = {
                'organization_name': getattr(org, 'name', ''),
                'governance_intelligence': governance.to_dict(),
                'board_composition_analysis': self._analyze_board_composition(board_members),
                'compensation_analysis': self._analyze_compensation_structure(governance),
                'governance_recommendations': self._generate_governance_recommendations(governance)
            }
        
        return governance_analysis
    
    def _calculate_governance_score(self, governance: GovernanceIntelligence) -> float:
        """Calculate governance quality score."""
        score = 0.0
        
        # Board size (optimal range 7-15 members)
        if 7 <= governance.board_size <= 15:
            score += 0.3
        elif 5 <= governance.board_size < 7 or 15 < governance.board_size <= 20:
            score += 0.2
        elif governance.board_size > 0:
            score += 0.1
        
        # Policy indicators
        policy_count = sum([
            governance.conflict_of_interest_policy,
            governance.whistleblower_policy,
            governance.document_retention_policy
        ])
        score += policy_count * 0.1
        
        # Executive compensation reasonableness (simplified)
        if governance.executive_compensation:
            max_compensation = max(governance.executive_compensation.values())
            if max_compensation < 200000:  # Reasonable for nonprofit
                score += 0.2
            elif max_compensation < 500000:
                score += 0.1
        
        return min(score, 1.0)
    
    def _determine_governance_quality(self, score: float) -> GovernanceQuality:
        """Determine governance quality from score."""
        if score >= 0.8:
            return GovernanceQuality.EXCEPTIONAL
        elif score >= 0.6:
            return GovernanceQuality.STRONG
        elif score >= 0.4:
            return GovernanceQuality.ADEQUATE
        elif score >= 0.2:
            return GovernanceQuality.WEAK
        else:
            return GovernanceQuality.DEFICIENT
    
    def _identify_governance_strengths(self, governance: GovernanceIntelligence) -> List[str]:
        """Identify governance strengths."""
        strengths = []
        
        if 7 <= governance.board_size <= 15:
            strengths.append("Optimal board size for effective governance")
        
        if governance.conflict_of_interest_policy:
            strengths.append("Has conflict of interest policy")
        
        if governance.whistleblower_policy:
            strengths.append("Has whistleblower protection policy")
        
        return strengths
    
    def _identify_governance_concerns(self, governance: GovernanceIntelligence) -> List[str]:
        """Identify governance concerns."""
        concerns = []
        
        if governance.board_size < 5:
            concerns.append("Board size may be too small for effective oversight")
        elif governance.board_size > 20:
            concerns.append("Board size may be too large for efficient decision-making")
        
        if not governance.conflict_of_interest_policy:
            concerns.append("No documented conflict of interest policy")
        
        if governance.executive_compensation:
            max_comp = max(governance.executive_compensation.values())
            if max_comp > 500000:
                concerns.append("High executive compensation may raise donor concerns")
        
        return concerns
    
    def _analyze_board_composition(self, board_members: List[Any]) -> Dict[str, Any]:
        """Analyze board composition."""
        analysis = {
            "total_members": len(board_members),
            "composition_notes": []
        }
        
        if len(board_members) > 0:
            analysis["composition_notes"].append(f"Board of {len(board_members)} members")
        
        return analysis
    
    def _analyze_compensation_structure(self, governance: GovernanceIntelligence) -> Dict[str, Any]:
        """Analyze compensation structure."""
        analysis = {
            "executive_count": len(governance.executive_compensation),
            "total_executive_compensation": sum(governance.executive_compensation.values()),
            "average_compensation": 0,
            "compensation_notes": []
        }
        
        if governance.executive_compensation:
            analysis["average_compensation"] = analysis["total_executive_compensation"] / len(governance.executive_compensation)
            
            max_comp = max(governance.executive_compensation.values())
            if max_comp > 200000:
                analysis["compensation_notes"].append("Executive compensation above $200K threshold")
        
        return analysis
    
    def _generate_governance_recommendations(self, governance: GovernanceIntelligence) -> List[str]:
        """Generate governance recommendations."""
        recommendations = []
        
        if governance.governance_quality in [GovernanceQuality.EXCEPTIONAL, GovernanceQuality.STRONG]:
            recommendations.append("Strong governance foundation supports funding confidence")
        elif governance.governance_quality == GovernanceQuality.ADEQUATE:
            recommendations.append("Consider governance capacity building support")
        else:
            recommendations.append("Governance improvement required before major funding consideration")
        
        return recommendations
    
    async def _analyze_program_compatibility(self, organizations: List[OrganizationProfile], 
                                           form_990_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze program compatibility between organizations and funders."""
        compatibility_analysis = {}
        
        # This would analyze program descriptions, activity codes, and outcome metrics
        # For now, provide structure for future implementation
        
        for org in organizations:
            org_ein = getattr(org, 'ein', '')
            if not org_ein:
                continue
            
            compatibility_analysis[org_ein] = {
                "program_focus_analysis": self._analyze_program_focus(org),
                "outcome_metrics_available": self._check_outcome_metrics(org),
                "program_scalability": self._assess_program_scalability(org)
            }
        
        return compatibility_analysis
    
    def _analyze_program_focus(self, org: OrganizationProfile) -> Dict[str, Any]:
        """Analyze program focus areas."""
        return {
            "primary_focus": getattr(org, 'ntee_code', ''),
            "mission_alignment": "Standard analysis pending narrative processing"
        }
    
    def _check_outcome_metrics(self, org: OrganizationProfile) -> bool:
        """Check if organization has outcome metrics."""
        # This would check for outcome reporting in 990 data
        return False  # Placeholder
    
    def _assess_program_scalability(self, org: OrganizationProfile) -> str:
        """Assess program scalability potential."""
        revenue = getattr(org, 'revenue', 0)
        if revenue > 1000000:
            return "High scalability potential"
        elif revenue > 100000:
            return "Moderate scalability potential"
        else:
            return "Limited scalability without capacity building"
    
    async def _identify_hidden_opportunities(self, organizations: List[OrganizationProfile], 
                                           form_990_data: List[Dict[str, Any]]) -> List[HiddenOpportunity]:
        """
        Phase 2 Requirement: Hidden opportunity identification through narrative analysis.
        
        Identifies hidden opportunities through analysis of narrative sections and non-standard data.
        """
        hidden_opportunities = []
        
        for org in organizations:
            org_ein = getattr(org, 'ein', '')
            org_name = getattr(org, 'name', '')
            if not org_ein:
                continue
            
            # Find corresponding 990 data
            org_990 = next((data for data in form_990_data if data.get('ein') == org_ein), None)
            if not org_990:
                continue
            
            # Analyze mission and activity descriptions
            mission_text = org_990.get('mission_description', '')
            activity_text = org_990.get('activity_description', '')
            
            # Search for opportunity patterns
            for pattern_type, patterns in self.opportunity_patterns.items():
                opportunities = self._find_pattern_opportunities(
                    org_ein, org_name, mission_text + ' ' + activity_text, 
                    pattern_type, patterns
                )
                hidden_opportunities.extend(opportunities)
        
        return hidden_opportunities
    
    def _find_pattern_opportunities(self, org_ein: str, org_name: str, text: str, 
                                  pattern_type: str, patterns: List[str]) -> List[HiddenOpportunity]:
        """Find opportunities matching specific patterns."""
        opportunities = []
        
        if not text:
            return opportunities
        
        text_lower = text.lower()
        
        for pattern in patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                # Extract context around match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                opportunity = HiddenOpportunity(
                    opportunity_type=pattern_type,
                    description=self._generate_opportunity_description(pattern_type, match.group()),
                    source_section="narrative_analysis",
                    confidence_level=0.6,  # Medium confidence for pattern matching
                    strategic_value=self._calculate_strategic_value(pattern_type),
                    organization_ein=org_ein,
                    organization_name=org_name,
                    related_text=context.strip()
                )
                
                opportunity.action_recommendations = self._generate_action_recommendations(opportunity)
                opportunities.append(opportunity)
        
        return opportunities
    
    def _generate_opportunity_description(self, pattern_type: str, matched_text: str) -> str:
        """Generate description for identified opportunity."""
        descriptions = {
            'expansion_signals': f"Organization shows expansion signals: '{matched_text}'",
            'capacity_needs': f"Capacity building need identified: '{matched_text}'",
            'partnership_signals': f"Partnership opportunity indicated: '{matched_text}'",
            'strategic_initiatives': f"Strategic initiative mentioned: '{matched_text}'"
        }
        return descriptions.get(pattern_type, f"Opportunity identified: '{matched_text}'")
    
    def _calculate_strategic_value(self, pattern_type: str) -> float:
        """Calculate strategic value based on opportunity type."""
        values = {
            'expansion_signals': 0.8,
            'capacity_needs': 0.7,
            'partnership_signals': 0.6,
            'strategic_initiatives': 0.9
        }
        return values.get(pattern_type, 0.5)
    
    def _generate_action_recommendations(self, opportunity: HiddenOpportunity) -> List[str]:
        """Generate action recommendations for opportunity."""
        recommendations = []
        
        if opportunity.opportunity_type == 'expansion_signals':
            recommendations.append("Explore growth funding opportunities")
            recommendations.append("Assess capacity building needs for expansion")
        elif opportunity.opportunity_type == 'capacity_needs':
            recommendations.append("Consider organizational development grants")
            recommendations.append("Evaluate technical assistance partnerships")
        elif opportunity.opportunity_type == 'partnership_signals':
            recommendations.append("Facilitate partnership introductions")
            recommendations.append("Explore collaborative funding opportunities")
        elif opportunity.opportunity_type == 'strategic_initiatives':
            recommendations.append("Align funding proposals with strategic priorities")
            recommendations.append("Provide multi-year funding consideration")
        
        return recommendations
    
    def _generate_data_mining_insights(self, financial_analysis: Dict[str, Any], 
                                     unsolicited_opportunities: List[UnsolicitedOpportunity],
                                     governance_analysis: Dict[str, Any], 
                                     hidden_opportunities: List[HiddenOpportunity]) -> Dict[str, Any]:
        """Generate comprehensive insights from data mining analysis."""
        insights = {
            "executive_summary": {},
            "key_findings": [],
            "strategic_recommendations": [],
            "priority_actions": []
        }
        
        # Executive summary
        total_orgs = len(financial_analysis)
        strong_financial_orgs = sum(1 for org in financial_analysis.values() 
                                  if org.get('financial_indicators', {}).get('overall_financial_health') in ['excellent', 'good'])
        
        insights["executive_summary"] = {
            "organizations_analyzed": total_orgs,
            "financially_strong_organizations": strong_financial_orgs,
            "unsolicited_opportunities_identified": len(unsolicited_opportunities),
            "hidden_opportunities_found": len(hidden_opportunities),
            "governance_quality_distribution": self._analyze_governance_distribution(governance_analysis)
        }
        
        # Key findings
        if strong_financial_orgs / max(total_orgs, 1) > 0.7:
            insights["key_findings"].append("Portfolio shows strong financial health across organizations")
        
        if len(unsolicited_opportunities) > 0:
            insights["key_findings"].append(f"Identified {len(unsolicited_opportunities)} foundations accepting unsolicited proposals")
        
        # Strategic recommendations
        insights["strategic_recommendations"] = [
            "Focus on financially strong organizations for growth funding",
            "Leverage identified unsolicited opportunities for direct approaches",
            "Address governance concerns before major funding initiatives"
        ]
        
        return insights
    
    def _analyze_governance_distribution(self, governance_analysis: Dict[str, Any]) -> Dict[str, int]:
        """Analyze distribution of governance quality."""
        distribution = defaultdict(int)
        
        for org_data in governance_analysis.values():
            quality = org_data.get('governance_intelligence', {}).get('governance_quality', 'adequate')
            distribution[quality] += 1
        
        return dict(distribution)
    
    async def _get_input_organizations(self, config: ProcessorConfig, workflow_state) -> List[OrganizationProfile]:
        """Get organizations from previous workflow steps or config."""
        # Try to get from workflow state first
        if workflow_state and hasattr(workflow_state, 'organizations'):
            return workflow_state.organizations
        
        # Try to get from config input data
        if config.input_data and 'organizations' in config.input_data:
            org_data = config.input_data['organizations']
            organizations = []
            for org_dict in org_data:
                if isinstance(org_dict, dict):
                    organizations.append(OrganizationProfile(**org_dict))
                elif hasattr(org_dict, 'dict'):
                    organizations.append(OrganizationProfile(**org_dict.dict()))
            return organizations
        
        return []


# Register the processor
def register_processor():
    """Register this processor with the workflow engine."""
    from src.core.workflow_engine import get_workflow_engine
    
    engine = get_workflow_engine()
    engine.register_processor(Form990DataMiningEngine)
    
    return Form990DataMiningEngine


# Factory function for processor registration
def get_processor():
    """Factory function for processor registration."""
    return Form990DataMiningEngine()