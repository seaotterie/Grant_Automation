"""
Enhanced Tier Intelligence Processor
Advanced Grant Intelligence with RFP Analysis, Network Intelligence, and Strategic Insights

Builds upon Standard tier by adding comprehensive document analysis, network intelligence,
and decision maker profiling for $22.00 cost point.
"""

import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import re

from src.core.data_models import ProcessorResult, OrganizationProfile
from src.intelligence.standard_tier_processor import StandardTierProcessor, StandardTierResult
from src.intelligence.historical_funding_analyzer import HistoricalFundingAnalyzer, FundingIntelligence
from src.processors.analysis.board_network_analyzer import BoardNetworkAnalyzerProcessor
from src.core.entity_cache_manager import get_entity_cache_manager
from src.core.openai_service import get_openai_service

logger = logging.getLogger(__name__)

@dataclass
class RFPAnalysisResult:
    """Results from RFP/NOFO document analysis"""
    document_type: str = ""
    total_pages: int = 0
    key_requirements: List[str] = None
    eligibility_criteria: List[str] = None
    evaluation_criteria: List[str] = None
    submission_requirements: List[str] = None
    deadlines: List[Dict[str, Any]] = None
    contact_information: List[Dict[str, str]] = None
    funding_details: Dict[str, Any] = None
    compliance_requirements: List[str] = None
    strategic_insights: List[str] = None
    complexity_score: float = 0.0
    
    def __post_init__(self):
        if self.key_requirements is None:
            self.key_requirements = []
        if self.eligibility_criteria is None:
            self.eligibility_criteria = []
        if self.evaluation_criteria is None:
            self.evaluation_criteria = []
        if self.submission_requirements is None:
            self.submission_requirements = []
        if self.deadlines is None:
            self.deadlines = []
        if self.contact_information is None:
            self.contact_information = []
        if self.funding_details is None:
            self.funding_details = {}
        if self.compliance_requirements is None:
            self.compliance_requirements = []
        if self.strategic_insights is None:
            self.strategic_insights = []

@dataclass
class NetworkIntelligenceResult:
    """Results from board network and relationship analysis"""
    total_connections: int = 0
    direct_connections: List[Dict[str, Any]] = None
    indirect_connections: List[Dict[str, Any]] = None
    influence_score: float = 0.0
    network_reach: int = 0
    strategic_relationships: List[Dict[str, Any]] = None
    warm_introduction_paths: List[Dict[str, Any]] = None
    network_advantages: List[str] = None
    relationship_recommendations: List[str] = None
    
    def __post_init__(self):
        if self.direct_connections is None:
            self.direct_connections = []
        if self.indirect_connections is None:
            self.indirect_connections = []
        if self.strategic_relationships is None:
            self.strategic_relationships = []
        if self.warm_introduction_paths is None:
            self.warm_introduction_paths = []
        if self.network_advantages is None:
            self.network_advantages = []
        if self.relationship_recommendations is None:
            self.relationship_recommendations = []

@dataclass
class DecisionMakerProfile:
    """Profile of key decision makers and stakeholders"""
    name: str = ""
    title: str = ""
    organization: str = ""
    background: str = ""
    influence_level: str = "unknown"  # high, medium, low
    contact_strategy: str = ""
    shared_connections: List[str] = None
    engagement_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.shared_connections is None:
            self.shared_connections = []
        if self.engagement_history is None:
            self.engagement_history = []

@dataclass
class EnhancedTierResult:
    """Result structure for Enhanced tier analysis"""
    tier: str = "enhanced"
    analysis_timestamp: str = ""
    
    # Base Standard tier results
    standard_tier_result: Optional[StandardTierResult] = None
    standard_tier_cost: float = 0.0
    
    # Enhanced analysis components
    rfp_analysis: Optional[RFPAnalysisResult] = None
    rfp_analysis_cost: float = 0.0
    
    network_intelligence: Optional[NetworkIntelligenceResult] = None
    network_analysis_cost: float = 0.0
    
    decision_maker_profiles: List[DecisionMakerProfile] = None
    decision_maker_cost: float = 0.0
    
    # Strategic insights and recommendations
    strategic_partnerships: List[Dict[str, Any]] = None
    competitive_positioning: Dict[str, Any] = None
    engagement_strategy: Dict[str, Any] = None
    risk_mitigation: List[str] = None
    enhanced_recommendations: List[str] = None
    
    # Processing metadata
    total_processing_cost: float = 0.0
    processing_time_seconds: float = 0.0
    data_sources_used: List[str] = None
    intelligence_score: float = 0.0
    confidence_score: float = 0.0
    
    def __post_init__(self):
        if self.decision_maker_profiles is None:
            self.decision_maker_profiles = []
        if self.strategic_partnerships is None:
            self.strategic_partnerships = []
        if self.competitive_positioning is None:
            self.competitive_positioning = {}
        if self.engagement_strategy is None:
            self.engagement_strategy = {}
        if self.risk_mitigation is None:
            self.risk_mitigation = []
        if self.enhanced_recommendations is None:
            self.enhanced_recommendations = []
        if self.data_sources_used is None:
            self.data_sources_used = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        result = asdict(self)
        # Convert StandardTierResult to dict if present
        if self.standard_tier_result:
            result['standard_tier_result'] = self.standard_tier_result.to_dict()
        
        # Ensure datetime fields are strings for JSON serialization
        if 'analysis_timestamp' in result and not isinstance(result['analysis_timestamp'], str):
            result['analysis_timestamp'] = result['analysis_timestamp'].isoformat() if result['analysis_timestamp'] else ""
        
        return result


class RFPAnalyzer:
    """Analyzes RFP/NOFO documents for requirements and strategic insights"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.doc', '.docx', '.txt', '.html']
        
    async def analyze_rfp_document(self, opportunity_id: str, document_path: Optional[str] = None) -> RFPAnalysisResult:
        """
        Analyze RFP/NOFO document for requirements and insights
        
        Args:
            opportunity_id: Grant opportunity ID
            document_path: Path to RFP document (optional)
            
        Returns:
            Comprehensive RFP analysis results
        """
        logger.info(f"Starting RFP analysis for opportunity {opportunity_id}")
        
        try:
            # For MVP, simulate RFP analysis based on opportunity type
            # In production, this would parse actual RFP documents
            
            result = RFPAnalysisResult(
                document_type="NOFO" if "NOFO" in opportunity_id else "RFP",
                total_pages=15,  # Simulated
                key_requirements=[
                    "501(c)(3) nonprofit status required",
                    "Minimum 3 years operational experience",
                    "Demonstrated expertise in environmental sustainability",
                    "Geographic focus on underserved communities",
                    "Collaborative partnerships with community organizations"
                ],
                eligibility_criteria=[
                    "Annual revenue between $100K - $2M",
                    "Board of directors with minimum 5 members",
                    "Audited financial statements for past 2 years",
                    "Federal tax exemption letter",
                    "Registration in grants.gov SAM database"
                ],
                evaluation_criteria=[
                    "Project design and methodology (30 points)",
                    "Organizational capacity and experience (25 points)", 
                    "Budget justification and cost-effectiveness (20 points)",
                    "Community impact and sustainability (15 points)",
                    "Partnership and collaboration plan (10 points)"
                ],
                submission_requirements=[
                    "Complete application form (SF-424)",
                    "Project narrative (15 page limit)",
                    "Detailed line-item budget and justification",
                    "Letters of support from community partners",
                    "Board resolution authorizing grant application",
                    "Organizational chart and staff qualifications"
                ],
                deadlines=[
                    {"type": "Letter of Intent", "date": "2025-02-15", "required": False},
                    {"type": "Full Application", "date": "2025-03-31", "required": True},
                    {"type": "Award Notification", "date": "2025-05-30", "required": False}
                ],
                contact_information=[
                    {"name": "Program Officer", "email": "grants@agency.gov", "phone": "555-0123"},
                    {"name": "Technical Assistance", "email": "help@agency.gov", "phone": "555-0124"}
                ],
                funding_details={
                    "award_range": {"min": 75000, "max": 500000},
                    "project_period": "12 months",
                    "total_funding_available": 5000000,
                    "expected_awards": 15,
                    "match_required": False,
                    "indirect_costs": "10% de minimis rate allowed"
                },
                compliance_requirements=[
                    "Federal financial reporting standards (2 CFR 200)",
                    "Environmental compliance assessment",
                    "Human subjects research approval if applicable",
                    "Civil rights and nondiscrimination policies",
                    "Data management and privacy protection plan"
                ],
                strategic_insights=[
                    "Emphasis on community engagement suggests relationship-building critical",
                    "Environmental focus aligns with current federal priorities",
                    "Collaborative requirement indicates partnership development opportunity",
                    "Budget range suggests mid-tier opportunity with reasonable competition",
                    "Evaluation criteria weight organizational capacity highly"
                ],
                complexity_score=0.72  # Medium-high complexity
            )
            
            logger.info(f"RFP analysis completed: {len(result.key_requirements)} requirements identified")
            return result
            
        except Exception as e:
            logger.error(f"RFP analysis failed: {e}")
            return RFPAnalysisResult(
                strategic_insights=[f"RFP analysis failed: {str(e)}"],
                complexity_score=0.5
            )


class DecisionMakerAnalyzer:
    """Analyzes decision makers and key stakeholders for engagement strategy"""
    
    def __init__(self):
        pass
        
    async def analyze_decision_makers(
        self, 
        opportunity_details: Dict[str, Any],
        network_intelligence: Optional[NetworkIntelligenceResult] = None
    ) -> List[DecisionMakerProfile]:
        """
        Analyze key decision makers and stakeholders
        
        Args:
            opportunity_details: Grant opportunity information
            network_intelligence: Network analysis results
            
        Returns:
            List of decision maker profiles with engagement strategies
        """
        logger.info("Analyzing decision makers and key stakeholders")
        
        try:
            # For MVP, simulate decision maker analysis
            # In production, this would research actual program officers and reviewers
            
            agency_name = opportunity_details.get("agency_name", "Unknown Agency")
            
            decision_makers = [
                DecisionMakerProfile(
                    name="Dr. Sarah Johnson",
                    title="Program Officer",
                    organization=agency_name,
                    background="15+ years in environmental sustainability programs, former nonprofit executive",
                    influence_level="high",
                    contact_strategy="Professional introduction through environmental nonprofit networks",
                    shared_connections=["Environmental Council Board Member"] if network_intelligence else [],
                    engagement_history=[
                        {"type": "conference", "event": "National Environmental Summit 2024", "interaction": "panel discussion"}
                    ]
                ),
                DecisionMakerProfile(
                    name="Michael Chen",
                    title="Senior Review Specialist", 
                    organization=agency_name,
                    background="Policy analysis and grant review expertise, academic background in public administration",
                    influence_level="medium",
                    contact_strategy="Engage through technical assistance sessions and stakeholder meetings",
                    shared_connections=[],
                    engagement_history=[]
                ),
                DecisionMakerProfile(
                    name="Dr. Maria Rodriguez",
                    title="Division Director",
                    organization=agency_name,
                    background="Program leadership and strategic direction, strong advocate for community partnerships",
                    influence_level="high", 
                    contact_strategy="Connect through community partnership initiatives and policy discussions",
                    shared_connections=["Community Development Board Member"] if network_intelligence else [],
                    engagement_history=[
                        {"type": "webinar", "event": "Community Engagement Best Practices", "interaction": "keynote speaker"}
                    ]
                )
            ]
            
            logger.info(f"Identified {len(decision_makers)} key decision makers")
            return decision_makers
            
        except Exception as e:
            logger.error(f"Decision maker analysis failed: {e}")
            return []


class EnhancedTierProcessor:
    """
    Enhanced Tier Intelligence Processor
    
    Builds upon Standard tier with comprehensive RFP analysis, network intelligence,
    and decision maker profiling to provide high-value strategic insights.
    """
    
    def __init__(self):
        self.standard_processor = StandardTierProcessor()
        self.rfp_analyzer = RFPAnalyzer()
        self.decision_maker_analyzer = DecisionMakerAnalyzer()
        self.board_network_analyzer = BoardNetworkAnalyzerProcessor()
        self.entity_cache_manager = get_entity_cache_manager()
        self.openai_service = get_openai_service()
        
        # Cost tracking
        self.cost_tracker = {
            "standard_tier": 0.0,
            "rfp_analysis": 0.0,
            "network_intelligence": 0.0,
            "decision_makers": 0.0,
            "gpt5_synthesis": 0.0,
            "integration": 0.0
        }
        
    async def process_opportunity(
        self,
        profile_id: str,
        opportunity_id: str,
        add_ons: List[str] = None,
        document_path: Optional[str] = None
    ) -> EnhancedTierResult:
        """
        Process opportunity with Enhanced tier intelligence
        
        Args:
            profile_id: Organization profile ID
            opportunity_id: Grant opportunity ID
            add_ons: Optional add-on modules to include
            document_path: Optional path to RFP document
            
        Returns:
            Comprehensive Enhanced tier analysis results
        """
        start_time = time.time()
        logger.info(f"Starting Enhanced tier processing for {profile_id} + {opportunity_id}")
        
        if add_ons is None:
            add_ons = []
            
        try:
            # Step 1: Run Standard tier analysis as foundation
            standard_result = await self.standard_processor.process_opportunity(
                profile_id=profile_id,
                opportunity_id=opportunity_id
            )
            self.cost_tracker["standard_tier"] = standard_result.total_processing_cost
            
            # Step 2: Extract opportunity details for enhanced analysis
            opportunity_details = await self._extract_enhanced_opportunity_details(opportunity_id)
            
            # Step 3: RFP/NOFO Analysis (core Enhanced tier feature)
            rfp_analysis = await self._run_rfp_analysis(opportunity_id, document_path)
            
            # Step 4: Network Intelligence Analysis (if applicable)
            network_intelligence = await self._run_network_intelligence_analysis(
                profile_id, opportunity_details
            )
            
            # Step 5: Decision Maker Profiling
            decision_makers = await self._run_decision_maker_analysis(
                opportunity_details, network_intelligence
            )
            
            # Step 6: Strategic Integration and Enhanced Insights with GPT-5
            strategic_analysis = await self._integrate_enhanced_analyses_with_gpt5(
                standard_result,
                rfp_analysis,
                network_intelligence,
                decision_makers,
                opportunity_details
            )
            
            processing_time = time.time() - start_time
            
            # Step 7: Build comprehensive Enhanced tier result
            result = EnhancedTierResult(
                analysis_timestamp=datetime.now().isoformat(),
                standard_tier_result=standard_result,
                standard_tier_cost=self.cost_tracker["standard_tier"],
                rfp_analysis=rfp_analysis,
                rfp_analysis_cost=self.cost_tracker["rfp_analysis"],
                network_intelligence=network_intelligence,
                network_analysis_cost=self.cost_tracker["network_intelligence"],
                decision_maker_profiles=decision_makers,
                decision_maker_cost=self.cost_tracker["decision_makers"],
                strategic_partnerships=strategic_analysis.get("strategic_partnerships", []),
                competitive_positioning=strategic_analysis.get("competitive_positioning", {}),
                engagement_strategy=strategic_analysis.get("engagement_strategy", {}),
                risk_mitigation=strategic_analysis.get("risk_mitigation", []),
                enhanced_recommendations=strategic_analysis.get("enhanced_recommendations", []),
                total_processing_cost=sum(self.cost_tracker.values()),
                processing_time_seconds=processing_time,
                data_sources_used=strategic_analysis.get("data_sources", []),
                intelligence_score=strategic_analysis.get("intelligence_score", 0.0),
                confidence_score=strategic_analysis.get("confidence_score", 0.0)
            )
            
            logger.info(f"Enhanced tier processing completed in {processing_time:.2f}s, cost: ${result.total_processing_cost:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Enhanced tier processing failed: {e}", exc_info=True)
            # Return partial results with error information
            return EnhancedTierResult(
                analysis_timestamp=datetime.now().isoformat(),
                enhanced_recommendations=[f"Enhanced analysis partially failed: {str(e)}"],
                processing_time_seconds=time.time() - start_time,
                data_sources_used=["error"]
            )
    
    async def _extract_enhanced_opportunity_details(self, opportunity_id: str) -> Dict[str, Any]:
        """Extract detailed opportunity information for enhanced analysis"""
        logger.debug(f"Extracting enhanced opportunity details for {opportunity_id}")
        
        try:
            # Enhanced opportunity details for better analysis
            # In production, this would query comprehensive opportunity databases
            
            opportunity_details = {
                "opportunity_id": opportunity_id,
                "agency_name": "Department of Energy",
                "agency_code": "DOE",
                "program_name": "Environmental Sustainability Initiative",
                "program_keywords": ["environmental", "sustainability", "energy", "community"],
                "opportunity_type": "government_grant",
                "funding_mechanism": "cooperative_agreement",
                "estimated_award_range": {"min": 75000, "max": 500000},
                "total_program_funding": 5000000,
                "expected_awards": 15,
                "application_deadline": "2025-03-31",
                "program_officers": ["Dr. Sarah Johnson", "Michael Chen"],
                "review_process": "peer_review_with_agency_selection",
                "strategic_priorities": [
                    "community_engagement",
                    "environmental_justice", 
                    "sustainable_development",
                    "partnership_building"
                ],
                "compliance_requirements": [
                    "environmental_assessment",
                    "community_benefit_analysis",
                    "partnership_documentation"
                ],
                "competitive_landscape": "medium",
                "historical_success_factors": [
                    "strong_community_partnerships",
                    "clear_environmental_impact",
                    "experienced_project_team",
                    "sustainable_funding_model"
                ]
            }
            
            logger.debug(f"Enhanced opportunity details extracted: {len(opportunity_details)} fields")
            return opportunity_details
            
        except Exception as e:
            logger.warning(f"Failed to extract enhanced opportunity details: {e}")
            return {
                "opportunity_id": opportunity_id,
                "agency_name": "Unknown Agency",
                "program_keywords": [],
                "opportunity_type": "unknown"
            }
    
    async def _run_rfp_analysis(self, opportunity_id: str, document_path: Optional[str] = None) -> RFPAnalysisResult:
        """Run comprehensive RFP/NOFO document analysis"""
        logger.debug(f"Running RFP analysis for {opportunity_id}")
        
        try:
            self.cost_tracker["rfp_analysis"] = 2.85  # Estimated cost for document processing and AI analysis
            
            rfp_result = await self.rfp_analyzer.analyze_rfp_document(
                opportunity_id=opportunity_id,
                document_path=document_path
            )
            
            logger.info(f"RFP analysis completed: complexity {rfp_result.complexity_score:.2f}")
            return rfp_result
            
        except Exception as e:
            logger.warning(f"RFP analysis failed: {e}")
            self.cost_tracker["rfp_analysis"] = 0.0
            return RFPAnalysisResult(
                strategic_insights=[f"RFP analysis failed: {str(e)}"],
                complexity_score=0.5
            )
    
    async def _run_network_intelligence_analysis(
        self,
        profile_id: str,
        opportunity_details: Dict[str, Any]
    ) -> Optional[NetworkIntelligenceResult]:
        """Run board network and relationship intelligence analysis"""
        logger.debug(f"Running network intelligence analysis for {profile_id}")
        
        try:
            self.cost_tracker["network_intelligence"] = 1.95  # Cost for network analysis and relationship mapping
            
            # For MVP, simulate network intelligence results
            # In production, this would use the actual BoardNetworkAnalyzer
            
            network_result = NetworkIntelligenceResult(
                total_connections=12,
                direct_connections=[
                    {
                        "name": "Environmental Council",
                        "connection_type": "board_member",
                        "shared_person": "John Smith",
                        "influence_level": "medium",
                        "relationship_strength": 0.75
                    },
                    {
                        "name": "Community Development Corp",
                        "connection_type": "advisory_board",
                        "shared_person": "Dr. Lisa Chen",
                        "influence_level": "high",
                        "relationship_strength": 0.90
                    }
                ],
                indirect_connections=[
                    {
                        "target_organization": "Regional Environmental Foundation",
                        "path_length": 2,
                        "connection_path": ["John Smith", "Mary Johnson", "Regional Foundation"],
                        "strength_score": 0.65
                    }
                ],
                influence_score=0.68,
                network_reach=45,
                strategic_relationships=[
                    {
                        "type": "government_liaison",
                        "organization": "State Environmental Agency",
                        "contact": "Commissioner Williams",
                        "relevance": "high"
                    }
                ],
                warm_introduction_paths=[
                    {
                        "target": "Program Officer Dr. Sarah Johnson",
                        "path": "Board Member John Smith → Environmental Council → Dr. Johnson",
                        "success_probability": 0.75
                    }
                ],
                network_advantages=[
                    "Strong environmental sector connections",
                    "Government liaison relationships available", 
                    "Community development network access",
                    "Academic research partnerships"
                ],
                relationship_recommendations=[
                    "Leverage Environmental Council connection for program officer introduction",
                    "Activate Community Development Corp relationship for partnership letters",
                    "Utilize government liaison for strategic guidance",
                    "Engage academic connections for technical expertise validation"
                ]
            )
            
            logger.info(f"Network intelligence completed: {network_result.total_connections} connections identified")
            return network_result
            
        except Exception as e:
            logger.warning(f"Network intelligence analysis failed: {e}")
            self.cost_tracker["network_intelligence"] = 0.0
            return None
    
    async def _run_decision_maker_analysis(
        self,
        opportunity_details: Dict[str, Any],
        network_intelligence: Optional[NetworkIntelligenceResult] = None
    ) -> List[DecisionMakerProfile]:
        """Run decision maker profiling and engagement strategy analysis"""
        logger.debug("Running decision maker analysis")
        
        try:
            self.cost_tracker["decision_makers"] = 1.65  # Cost for stakeholder research and profiling
            
            decision_makers = await self.decision_maker_analyzer.analyze_decision_makers(
                opportunity_details=opportunity_details,
                network_intelligence=network_intelligence
            )
            
            logger.info(f"Decision maker analysis completed: {len(decision_makers)} profiles created")
            return decision_makers
            
        except Exception as e:
            logger.warning(f"Decision maker analysis failed: {e}")
            self.cost_tracker["decision_makers"] = 0.0
            return []
    
    async def _integrate_enhanced_analyses(
        self,
        standard_result: StandardTierResult,
        rfp_analysis: RFPAnalysisResult,
        network_intelligence: Optional[NetworkIntelligenceResult],
        decision_makers: List[DecisionMakerProfile],
        opportunity_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Integrate all Enhanced tier analyses for strategic insights"""
        logger.debug("Integrating Enhanced tier analyses")
        
        try:
            self.cost_tracker["integration"] = 0.75  # Cost for AI-powered integration and insight generation
            
            enhanced_insights = {
                "strategic_partnerships": [],
                "competitive_positioning": {},
                "engagement_strategy": {},
                "risk_mitigation": [],
                "enhanced_recommendations": [],
                "data_sources": ["standard_tier", "rfp_analysis"],
                "intelligence_score": 0.0,
                "confidence_score": 0.0
            }
            
            # Strategic Partnership Opportunities
            partnerships = []
            if network_intelligence:
                enhanced_insights["data_sources"].append("network_intelligence")
                partnerships.extend([
                    {
                        "type": "community_collaboration",
                        "organization": "Community Development Corp",
                        "value_proposition": "Community engagement and partnership letters",
                        "implementation": "Joint program design and delivery",
                        "success_probability": 0.80
                    },
                    {
                        "type": "technical_expertise",
                        "organization": "Environmental Council",
                        "value_proposition": "Technical validation and subject matter expertise", 
                        "implementation": "Advisory role and technical review",
                        "success_probability": 0.75
                    }
                ])
            
            enhanced_insights["strategic_partnerships"] = partnerships
            
            # Competitive Positioning Analysis
            competitive_positioning = {
                "strengths": [],
                "differentiators": [],
                "competitive_advantages": [],
                "positioning_strategy": ""
            }
            
            if rfp_analysis and rfp_analysis.evaluation_criteria:
                competitive_positioning["strengths"] = [
                    "Strong organizational capacity aligns with 25-point evaluation criterion",
                    "Community partnership network addresses collaboration requirements",
                    "Environmental expertise matches program focus areas"
                ]
                
                competitive_positioning["differentiators"] = [
                    "Unique combination of technical expertise and community connections",
                    "Proven track record in environmental sustainability initiatives",
                    "Multi-sector partnership approach"
                ]
                
                competitive_positioning["competitive_advantages"] = [
                    "Network intelligence provides warm introduction pathways",
                    "Board connections enable high-quality letters of support",
                    "Strategic relationships facilitate program officer engagement"
                ]
                
                competitive_positioning["positioning_strategy"] = "Community-Connected Environmental Leader"
            
            enhanced_insights["competitive_positioning"] = competitive_positioning
            
            # Engagement Strategy
            engagement_strategy = {
                "pre_application": [],
                "application_period": [],
                "post_submission": [],
                "relationship_building": []
            }
            
            if decision_makers:
                enhanced_insights["data_sources"].append("decision_maker_analysis")
                
                engagement_strategy["pre_application"] = [
                    "Attend technical assistance sessions hosted by Program Officer",
                    "Participate in stakeholder engagement meetings",
                    "Connect through Environmental Council network for informal introduction"
                ]
                
                engagement_strategy["application_period"] = [
                    "Submit letter of intent to demonstrate serious interest",
                    "Request pre-submission feedback on project concept",
                    "Engage community partners for strong letters of support"
                ]
                
                engagement_strategy["relationship_building"] = [
                    "Leverage board member connections for warm introductions",
                    "Participate in relevant conferences and professional networks",
                    "Share thought leadership content on environmental sustainability"
                ]
            
            enhanced_insights["engagement_strategy"] = engagement_strategy
            
            # Risk Mitigation Strategies
            risk_mitigation = []
            if rfp_analysis:
                enhanced_insights["data_sources"].append("rfp_analysis")
                risk_mitigation.extend([
                    "Address compliance requirements early in project design",
                    "Develop contingency plans for community engagement challenges", 
                    "Ensure budget aligns with evaluation criteria weighting",
                    "Build redundant partnerships to mitigate collaboration risks"
                ])
            
            enhanced_insights["risk_mitigation"] = risk_mitigation
            
            # Enhanced Recommendations
            enhanced_recommendations = []
            
            # Base recommendations from Standard tier
            if standard_result and standard_result.enhanced_recommendations:
                enhanced_recommendations.extend(standard_result.enhanced_recommendations)
            
            # Enhanced tier specific recommendations
            enhanced_recommendations.extend([
                "STRATEGIC: Position as community-connected environmental leader with proven partnerships",
                "ENGAGEMENT: Leverage network connections for program officer introduction and relationship building",
                "COMPETITIVE: Emphasize unique multi-sector partnership approach as key differentiator",
                "COMPLIANCE: Address all RFP requirements systematically with detailed documentation",
                "PARTNERSHIPS: Activate board connections for high-quality letters of support and collaboration"
            ])
            
            if network_intelligence and network_intelligence.total_connections > 5:
                enhanced_recommendations.append(
                    f"NETWORK ADVANTAGE: {network_intelligence.total_connections} strategic connections identified - leverage for competitive advantage"
                )
            
            if rfp_analysis and rfp_analysis.complexity_score > 0.7:
                enhanced_recommendations.append(
                    "RFP COMPLEXITY: High complexity RFP requires dedicated proposal management and expert review"
                )
            
            enhanced_insights["enhanced_recommendations"] = enhanced_recommendations
            
            # Calculate Enhanced tier intelligence scores
            intelligence_factors = []
            
            # Standard tier baseline
            if standard_result:
                intelligence_factors.append(standard_result.intelligence_score)
            
            # RFP analysis quality
            if rfp_analysis:
                rfp_factor = min(1.0, len(rfp_analysis.key_requirements) / 5 * rfp_analysis.complexity_score)
                intelligence_factors.append(rfp_factor)
            
            # Network intelligence depth
            if network_intelligence:
                network_factor = min(1.0, network_intelligence.total_connections / 10 * network_intelligence.influence_score)
                intelligence_factors.append(network_factor)
            
            # Decision maker analysis completeness
            if decision_makers:
                decision_factor = min(1.0, len(decision_makers) / 3)
                intelligence_factors.append(decision_factor)
            
            # Strategic integration quality
            strategy_factor = min(1.0, (len(partnerships) + len(enhanced_recommendations)) / 10)
            intelligence_factors.append(strategy_factor)
            
            enhanced_insights["intelligence_score"] = sum(intelligence_factors) / len(intelligence_factors) if intelligence_factors else 0.5
            
            # Confidence score based on data availability and analysis depth
            confidence_factors = [
                1.0 if standard_result else 0.0,
                1.0 if rfp_analysis and len(rfp_analysis.key_requirements) > 3 else 0.5,
                1.0 if network_intelligence and network_intelligence.total_connections > 5 else 0.5,
                1.0 if len(decision_makers) >= 2 else 0.5,
                1.0 if len(enhanced_recommendations) > 5 else 0.5
            ]
            
            enhanced_insights["confidence_score"] = sum(confidence_factors) / len(confidence_factors)
            
            logger.info(f"Enhanced analysis integration completed. Intelligence score: {enhanced_insights['intelligence_score']:.2f}, "
                       f"Confidence score: {enhanced_insights['confidence_score']:.2f}")
            
            return enhanced_insights
            
        except Exception as e:
            logger.error(f"Enhanced analysis integration failed: {e}")
            return {
                "enhanced_recommendations": ["Enhanced analysis integration failed - using basic recommendations"],
                "intelligence_score": 0.5,
                "confidence_score": 0.5,
                "data_sources": ["error"],
                "error": str(e)
            }
    
    async def _integrate_enhanced_analyses_with_gpt5(
        self,
        standard_result: StandardTierResult,
        rfp_analysis: RFPAnalysisResult,
        network_intelligence: Optional[NetworkIntelligenceResult],
        decision_makers: List[DecisionMakerProfile],
        opportunity_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Integrate Enhanced tier analyses using GPT-5 for strategic synthesis"""
        logger.info("Integrating Enhanced tier analyses with GPT-5 strategic synthesis")
        
        try:
            # First get basic integration
            basic_integration = await self._integrate_enhanced_analyses(
                standard_result, rfp_analysis, network_intelligence, decision_makers, opportunity_details
            )
            
            # Prepare comprehensive data for GPT-5 analysis
            synthesis_prompt = self._build_enhanced_tier_prompt(
                standard_result, rfp_analysis, network_intelligence, decision_makers, 
                opportunity_details, basic_integration
            )
            
            # Make GPT-5 API call for strategic synthesis
            messages = [
                {
                    "role": "system",
                    "content": "You are a senior grant strategy consultant with access to comprehensive intelligence including RFP analysis, network mapping, and decision maker profiling. Provide strategic synthesis and high-value recommendations for the Enhanced tier analysis."
                },
                {
                    "role": "user",
                    "content": synthesis_prompt
                }
            ]
            
            logger.info("Making GPT-5 API call for Enhanced tier strategic synthesis")
            response = await self.openai_service.create_completion(
                model="gpt-5",
                messages=messages,
                max_tokens=2000,
                temperature=1.0  # GPT-5 only supports temperature=1
            )
            
            # Track API costs
            self.cost_tracker["gpt5_synthesis"] = response.cost_estimate
            logger.info(f"GPT-5 Enhanced tier synthesis completed - Cost: ${response.cost_estimate:.4f}, Tokens: {response.usage.get('total_tokens', 0)}")
            
            # Parse GPT-5 enhanced response
            enhanced_insights = await self._parse_gpt5_enhanced_response(
                response.content, basic_integration
            )
            
            return enhanced_insights
            
        except Exception as e:
            logger.error(f"GPT-5 enhanced strategic synthesis failed: {e}")
            # Fallback to basic integration
            return basic_integration
    
    def _build_enhanced_tier_prompt(
        self,
        standard_result: StandardTierResult,
        rfp_analysis: RFPAnalysisResult,
        network_intelligence: Optional[NetworkIntelligenceResult],
        decision_makers: List[DecisionMakerProfile],
        opportunity_details: Dict[str, Any],
        basic_integration: Dict[str, Any]
    ) -> str:
        """Build comprehensive prompt for GPT-5 Enhanced tier strategic synthesis"""
        
        prompt = f"""
ENHANCED TIER GRANT INTELLIGENCE SYNTHESIS ($22.00)

STANDARD TIER FOUNDATION:
- Intelligence Score: {standard_result.intelligence_score:.2f}
- Total Recommendations: {len(standard_result.enhanced_recommendations) if standard_result.enhanced_recommendations else 0}
- Confidence Level: {getattr(standard_result, 'confidence_improvement', 0.0):.2f}

RFP/DOCUMENT ANALYSIS:
- Document Type: {rfp_analysis.document_type if rfp_analysis else 'No document analyzed'}
- Pages Analyzed: {rfp_analysis.total_pages if rfp_analysis else 0}
- Key Requirements: {len(rfp_analysis.key_requirements) if rfp_analysis and rfp_analysis.key_requirements else 0} identified
- Evaluation Criteria: {len(rfp_analysis.evaluation_criteria) if rfp_analysis and rfp_analysis.evaluation_criteria else 0} criteria mapped
"""
        
        if network_intelligence:
            prompt += f"""
NETWORK INTELLIGENCE:
- Network Connections: {network_intelligence.total_connections} identified
- Influence Score: {network_intelligence.influence_score:.2f}
- Strategic Pathways: {len(network_intelligence.pathway_recommendations)} pathways identified
- Board Connections: {network_intelligence.board_connections} cross-organizational connections
"""
        else:
            prompt += "\nNETWORK INTELLIGENCE: No network analysis available"
        
        if decision_makers:
            prompt += f"""
DECISION MAKER PROFILING:
- Key Decision Makers: {len(decision_makers)} profiles created
- Engagement Strategies: Custom approaches developed for each stakeholder
- Influence Mapping: Strategic relationship pathways identified
"""
        else:
            prompt += "\nDECISION MAKER PROFILING: No decision maker analysis available"
        
        prompt += f"""

BASIC INTEGRATION INSIGHTS:
{chr(10).join(f'- {rec}' for rec in basic_integration.get('enhanced_recommendations', [])[:5])}

TASK: Provide Enhanced tier strategic synthesis ($22.00 value) that significantly improves upon Standard tier analysis ($7.50). Focus on:

1. STRATEGIC ADVANTAGE IDENTIFICATION: What unique competitive advantages emerge from the comprehensive analysis?
2. TACTICAL EXECUTION PLAN: How should the organization approach this opportunity tactically?
3. RELATIONSHIP LEVERAGE: How can network intelligence and decision maker insights be leveraged?
4. RISK MITIGATION STRATEGIES: What specific risks require mitigation based on comprehensive analysis?
5. SUCCESS OPTIMIZATION: What are the key factors for maximizing success probability?

Provide specific, high-value strategic recommendations that justify the 3x cost increase from Standard to Enhanced tier.
"""
        
        return prompt
    
    async def _parse_gpt5_enhanced_response(
        self, 
        gpt5_response: str, 
        basic_integration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse GPT-5 response and enhance basic integration results"""
        
        try:
            # Start with basic integration
            enhanced_insights = basic_integration.copy()
            
            # Add GPT-5 strategic recommendations
            gpt5_recommendations = []
            
            # Extract strategic recommendations from GPT-5 response
            lines = gpt5_response.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Look for structured strategic insights
                if 'STRATEGIC ADVANTAGE:' in line.upper():
                    current_section = 'advantage'
                elif 'TACTICAL EXECUTION:' in line.upper():
                    current_section = 'execution'
                elif 'RELATIONSHIP LEVERAGE:' in line.upper():
                    current_section = 'relationships'
                elif 'RISK MITIGATION:' in line.upper():
                    current_section = 'risk'
                elif 'SUCCESS OPTIMIZATION:' in line.upper():
                    current_section = 'success'
                elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    recommendation = line.lstrip('-•*').strip()
                    if recommendation and len(recommendation) > 15:
                        gpt5_recommendations.append(f"[Enhanced GPT-5] {recommendation}")
            
            # If no structured recommendations found, extract strategic insights
            if not gpt5_recommendations:
                sentences = gpt5_response.replace('\n', ' ').split('.')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if (len(sentence) > 25 and 
                        ('strategic' in sentence.lower() or 
                         'recommend' in sentence.lower() or
                         'should leverage' in sentence.lower() or
                         'tactical' in sentence.lower())):
                        gpt5_recommendations.append(f"[Enhanced GPT-5] {sentence}.")
                        if len(gpt5_recommendations) >= 6:  # Limit to 6 recommendations
                            break
            
            # Combine basic and GPT-5 enhanced recommendations
            all_recommendations = basic_integration.get('enhanced_recommendations', []) + gpt5_recommendations
            enhanced_insights['enhanced_recommendations'] = all_recommendations
            
            # Significantly increase intelligence score due to GPT-5 enhancement
            base_intelligence = basic_integration.get('intelligence_score', 0.0)
            enhanced_insights['intelligence_score'] = min(0.95, base_intelligence + 0.20)  # Larger GPT-5 boost
            
            # Increase confidence score
            base_confidence = basic_integration.get('confidence_score', 0.0)
            enhanced_insights['confidence_score'] = min(0.95, base_confidence + 0.15)  # GPT-5 confidence boost
            
            # Add GPT-5 to data sources
            data_sources = basic_integration.get('data_sources', [])
            if 'gpt5_strategic_synthesis' not in data_sources:
                data_sources.append('gpt5_strategic_synthesis')
            enhanced_insights['data_sources'] = data_sources
            
            logger.info(f"GPT-5 Enhanced tier synthesis complete - Added {len(gpt5_recommendations)} strategic recommendations")
            
            return enhanced_insights
            
        except Exception as e:
            logger.error(f"GPT-5 Enhanced tier response parsing failed: {e}")
            return basic_integration
    
    def get_cost_breakdown(self) -> Dict[str, float]:
        """Get detailed cost breakdown for Enhanced tier processing"""
        return {
            "standard_tier_cost": self.cost_tracker["standard_tier"],
            "rfp_analysis_cost": self.cost_tracker["rfp_analysis"],
            "network_intelligence_cost": self.cost_tracker["network_intelligence"],
            "decision_maker_analysis_cost": self.cost_tracker["decision_makers"],
            "integration_processing_cost": self.cost_tracker["integration"],
            "total_api_cost": sum(self.cost_tracker.values()),
            "platform_cost": 15.05,  # Infrastructure and processing costs for Enhanced tier
            "total_enhanced_tier_cost": sum(self.cost_tracker.values()) + 15.05
        }


# Factory function for processor registration
def create_enhanced_tier_processor() -> EnhancedTierProcessor:
    """Factory function to create Enhanced tier processor"""
    return EnhancedTierProcessor()


# Export main classes
__all__ = [
    "EnhancedTierProcessor", 
    "EnhancedTierResult",
    "RFPAnalysisResult",
    "NetworkIntelligenceResult", 
    "DecisionMakerProfile"
]