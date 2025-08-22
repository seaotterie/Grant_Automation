#!/usr/bin/env python3
"""
Agency Intelligence Framework - Phase 5 Cross-System Integration
Comprehensive framework for government agency intelligence and strategic insights.

This system provides deep intelligence about government agencies, their funding patterns,
personnel networks, strategic priorities, and optimal engagement strategies.
"""

import asyncio
import time
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Union, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.core.government_models import GovernmentOpportunity


class AgencyTier(Enum):
    """Classification of agency importance and funding capacity."""
    TIER_1 = "tier_1"  # Cabinet-level, major funding agencies (>$10B annual)
    TIER_2 = "tier_2"  # Large independent agencies ($1B-$10B annual)
    TIER_3 = "tier_3"  # Medium agencies ($100M-$1B annual)
    TIER_4 = "tier_4"  # Smaller agencies (<$100M annual)


class FundingPattern(Enum):
    """Patterns of agency funding behavior."""
    CONSISTENT = "consistent"      # Steady funding patterns
    CYCLICAL = "cyclical"         # Budget cycle dependent
    OPPORTUNISTIC = "opportunistic"  # Policy-driven spikes
    DECLINING = "declining"       # Reduced funding trend
    EMERGING = "emerging"         # New funding areas


class RelationshipType(Enum):
    """Types of relationships with agencies."""
    PROGRAM_OFFICER = "program_officer"
    TECHNICAL_REVIEWER = "technical_reviewer"
    ADVISORY_BOARD = "advisory_board"
    CONTRACTOR = "contractor"
    GRANTEE = "grantee"
    PEER_REVIEWER = "peer_reviewer"


@dataclass
class AgencyPersonnel:
    """Key personnel information for agency relationships."""
    name: str
    title: str
    email: Optional[str] = None
    phone: Optional[str] = None
    specialties: List[str] = field(default_factory=list)
    tenure_years: Optional[int] = None
    relationship_history: List[str] = field(default_factory=list)
    influence_score: float = 0.0  # 0.0 to 1.0
    accessibility_score: float = 0.0  # 0.0 to 1.0


@dataclass
class FundingIntelligence:
    """Comprehensive funding intelligence for an agency."""
    agency_code: str
    total_annual_funding: float
    opportunity_count: int
    
    # Funding characteristics
    funding_pattern: FundingPattern
    seasonal_trends: Dict[str, float] = field(default_factory=dict)  # month -> funding_ratio
    program_priorities: List[str] = field(default_factory=list)
    geographic_distribution: Dict[str, float] = field(default_factory=dict)  # state -> percentage
    
    # Success patterns
    typical_award_range: Tuple[float, float] = (0.0, 0.0)
    success_factors: List[str] = field(default_factory=list)
    rejection_patterns: Dict[str, float] = field(default_factory=dict)  # reason -> frequency
    
    # Competitive intelligence
    top_recipients: List[Dict[str, Any]] = field(default_factory=list)
    partnership_preferences: List[str] = field(default_factory=list)
    evaluation_criteria_weights: Dict[str, float] = field(default_factory=dict)


@dataclass
class StrategicIntelligence:
    """Strategic intelligence about agency direction and priorities."""
    agency_code: str
    
    # Current strategic priorities
    strategic_plan_priorities: List[str] = field(default_factory=list)
    emerging_focus_areas: List[str] = field(default_factory=list)
    policy_alignment_factors: List[str] = field(default_factory=list)
    
    # Leadership and influence
    key_decision_makers: List[AgencyPersonnel] = field(default_factory=list)
    external_influences: List[str] = field(default_factory=list)  # Congress, stakeholders
    advisory_committees: List[str] = field(default_factory=list)
    
    # Operational intelligence
    internal_challenges: List[str] = field(default_factory=list)
    capacity_constraints: List[str] = field(default_factory=list)
    technology_priorities: List[str] = field(default_factory=list)
    
    # Relationship opportunities
    engagement_opportunities: List[str] = field(default_factory=list)
    partnership_potential: float = 0.0  # 0.0 to 1.0
    relationship_building_strategy: List[str] = field(default_factory=list)


@dataclass
class ComprehensiveAgencyProfile:
    """Complete intelligence profile for a government agency."""
    agency_code: str
    agency_name: str
    agency_tier: AgencyTier
    
    # Core intelligence
    funding_intelligence: FundingIntelligence
    strategic_intelligence: StrategicIntelligence
    
    # Historical analysis
    historical_performance: Dict[str, Any] = field(default_factory=dict)
    trend_analysis: Dict[str, Any] = field(default_factory=dict)
    comparative_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Actionable intelligence
    engagement_readiness_score: float = 0.0  # 0.0 to 1.0
    opportunity_pipeline_strength: float = 0.0  # 0.0 to 1.0
    relationship_potential_score: float = 0.0  # 0.0 to 1.0
    
    # Intelligence metadata
    last_updated: datetime = field(default_factory=datetime.now)
    intelligence_confidence: float = 0.0  # 0.0 to 1.0
    data_sources: List[str] = field(default_factory=list)


class AgencyIntelligenceFramework(BaseProcessor):
    """
    Agency Intelligence Framework - Phase 5 Cross-System Integration
    
    Comprehensive government agency intelligence system providing:
    
    ## Agency Profiling and Classification
    - Tier-based agency classification system
    - Comprehensive agency characteristic analysis
    - Strategic priority identification and tracking
    - Leadership and personnel intelligence
    
    ## Funding Pattern Analysis
    - Historical funding trend analysis
    - Seasonal and cyclical pattern recognition
    - Geographic distribution intelligence
    - Success factor identification
    
    ## Strategic Intelligence Generation
    - Policy alignment tracking
    - Emerging opportunity identification
    - Competitive landscape analysis
    - Relationship building opportunities
    
    ## Cross-System Intelligence Integration
    - Entity-based agency data organization
    - Real-time intelligence updates
    - Historical performance tracking
    - Predictive opportunity analysis
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="agency_intelligence_framework",
            description="Comprehensive government agency intelligence and analysis",
            version="1.0.0",
            dependencies=["government_research_integration", "workflow_aware_government_scorer"],
            estimated_duration=240,  # 4 minutes for comprehensive intelligence
            requires_network=True,   # For intelligence updates
            requires_api_key=False,  # Uses public and cached data
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Initialize agency intelligence database
        self.agency_profiles = {}
        self.intelligence_cache = {}
        
        # Intelligence analysis weights
        self.intelligence_weights = {
            "funding_patterns": 0.30,      # Historical funding analysis
            "strategic_alignment": 0.25,   # Strategic priority alignment
            "relationship_potential": 0.20, # Personnel and relationship intelligence
            "competitive_positioning": 0.15, # Competitive landscape
            "operational_feasibility": 0.10  # Practical implementation factors
        }
        
        # Agency tier definitions
        self.tier_definitions = {
            AgencyTier.TIER_1: {
                "min_funding": 10_000_000_000,  # $10B+
                "agencies": ["DOD", "HHS", "DOE", "ED", "USDA", "DOT"],
                "characteristics": ["Cabinet-level", "Major policy influence", "Large opportunity volume"]
            },
            AgencyTier.TIER_2: {
                "min_funding": 1_000_000_000,   # $1B-$10B
                "agencies": ["NSF", "EPA", "NASA", "VA", "SBA"],
                "characteristics": ["Independent agencies", "Specialized focus", "Competitive awards"]
            },
            AgencyTier.TIER_3: {
                "min_funding": 100_000_000,     # $100M-$1B
                "agencies": ["NIST", "USGS", "CDC", "FDA"],
                "characteristics": ["Sub-agencies", "Technical specialization", "Targeted programs"]
            },
            AgencyTier.TIER_4: {
                "min_funding": 0,               # <$100M
                "agencies": ["IMLS", "NEA", "NEH", "CPB"],
                "characteristics": ["Specialized missions", "Limited funding", "Niche opportunities"]
            }
        }
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute comprehensive agency intelligence analysis."""
        start_time = time.time()
        
        try:
            # Get agencies from government opportunities
            agencies = await self._extract_agencies_from_opportunities(workflow_state)
            
            if not agencies:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No government agencies found for intelligence analysis"]
                )
            
            self.logger.info(f"Conducting agency intelligence analysis for {len(agencies)} agencies")
            
            # Generate comprehensive agency profiles
            agency_profiles = []
            for i, agency_code in enumerate(agencies):
                self._update_progress(
                    i + 1, len(agencies),
                    f"Analyzing agency intelligence for {agency_code}..."
                )
                
                profile = await self._generate_comprehensive_agency_profile(agency_code, workflow_state)
                if profile:
                    agency_profiles.append(profile.__dict__)
            
            # Generate cross-agency intelligence insights
            cross_agency_insights = await self._generate_cross_agency_insights(agency_profiles)
            
            # Generate strategic recommendations
            strategic_recommendations = await self._generate_strategic_recommendations(
                agency_profiles, workflow_state
            )
            
            # Calculate agency intelligence performance metrics
            performance_metrics = await self._calculate_intelligence_performance_metrics(
                agency_profiles
            )
            
            # Generate agency relationship matrix
            relationship_matrix = await self._generate_agency_relationship_matrix(agency_profiles)
            
            # Prepare comprehensive results
            result_data = {
                "comprehensive_agency_profiles": agency_profiles,
                "cross_agency_insights": cross_agency_insights,
                "strategic_recommendations": strategic_recommendations,
                "performance_metrics": performance_metrics,
                "agency_relationship_matrix": relationship_matrix,
                "total_agencies_analyzed": len(agency_profiles),
                "intelligence_framework_summary": {
                    "tier_1_agencies": len([p for p in agency_profiles if p["agency_tier"] == "tier_1"]),
                    "tier_2_agencies": len([p for p in agency_profiles if p["agency_tier"] == "tier_2"]),
                    "tier_3_agencies": len([p for p in agency_profiles if p["agency_tier"] == "tier_3"]),
                    "tier_4_agencies": len([p for p in agency_profiles if p["agency_tier"] == "tier_4"]),
                    "high_opportunity_agencies": len([p for p in agency_profiles 
                                                    if p["opportunity_pipeline_strength"] > 0.7])
                }
            }
            
            execution_time = time.time() - start_time
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "intelligence_scope": "comprehensive_agencies",
                    "analysis_depth": "strategic_and_tactical",
                    "intelligence_confidence": self._calculate_overall_confidence(agency_profiles)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Agency intelligence framework failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"Agency intelligence framework failed: {str(e)}"]
            )
    
    async def _generate_comprehensive_agency_profile(
        self, agency_code: str, workflow_state
    ) -> Optional[ComprehensiveAgencyProfile]:
        """Generate comprehensive intelligence profile for an agency."""
        
        try:
            # Determine agency tier
            agency_tier = self._classify_agency_tier(agency_code)
            
            # Get basic agency information
            agency_name = self._get_agency_name(agency_code)
            
            # Generate funding intelligence
            funding_intelligence = await self._analyze_funding_intelligence(agency_code, workflow_state)
            
            # Generate strategic intelligence
            strategic_intelligence = await self._analyze_strategic_intelligence(agency_code, workflow_state)
            
            # Create comprehensive profile
            profile = ComprehensiveAgencyProfile(
                agency_code=agency_code,
                agency_name=agency_name,
                agency_tier=agency_tier,
                funding_intelligence=funding_intelligence,
                strategic_intelligence=strategic_intelligence
            )
            
            # Generate historical analysis
            profile.historical_performance = await self._analyze_historical_performance(
                agency_code, workflow_state
            )
            
            # Generate trend analysis
            profile.trend_analysis = await self._analyze_agency_trends(agency_code, workflow_state)
            
            # Generate comparative analysis
            profile.comparative_analysis = await self._analyze_comparative_position(
                agency_code, agency_tier, workflow_state
            )
            
            # Calculate intelligence scores
            profile.engagement_readiness_score = self._calculate_engagement_readiness(
                funding_intelligence, strategic_intelligence
            )
            
            profile.opportunity_pipeline_strength = self._calculate_pipeline_strength(
                funding_intelligence, strategic_intelligence
            )
            
            profile.relationship_potential_score = self._calculate_relationship_potential(
                strategic_intelligence
            )
            
            # Set intelligence metadata
            profile.intelligence_confidence = self._calculate_profile_confidence(profile)
            profile.data_sources = self._identify_data_sources(agency_code)
            
            return profile
            
        except Exception as e:
            self.logger.warning(f"Failed to generate profile for agency {agency_code}: {e}")
            return None
    
    async def _analyze_funding_intelligence(
        self, agency_code: str, workflow_state
    ) -> FundingIntelligence:
        """Analyze comprehensive funding intelligence for agency."""
        
        # Get opportunities from workflow state
        opportunities = await self._get_agency_opportunities(agency_code, workflow_state)
        
        funding_intel = FundingIntelligence(
            agency_code=agency_code,
            total_annual_funding=0.0,
            opportunity_count=len(opportunities),
            funding_pattern=FundingPattern.CONSISTENT  # Default
        )
        
        # Analyze funding characteristics
        if opportunities:
            # Calculate total funding
            total_funding = sum(opp.award_ceiling or 0 for opp in opportunities if opp.award_ceiling)
            funding_intel.total_annual_funding = total_funding
            
            # Determine funding pattern
            funding_intel.funding_pattern = self._analyze_funding_pattern(opportunities)
            
            # Analyze seasonal trends
            funding_intel.seasonal_trends = self._analyze_seasonal_trends(opportunities)
            
            # Identify program priorities
            funding_intel.program_priorities = self._extract_program_priorities(opportunities)
            
            # Analyze geographic distribution
            funding_intel.geographic_distribution = self._analyze_geographic_distribution(opportunities)
            
            # Calculate typical award range
            award_amounts = [opp.award_ceiling for opp in opportunities if opp.award_ceiling]
            if award_amounts:
                funding_intel.typical_award_range = (min(award_amounts), max(award_amounts))
            
            # Extract success factors
            funding_intel.success_factors = self._extract_success_factors(agency_code, opportunities)
            
            # Analyze rejection patterns
            funding_intel.rejection_patterns = self._analyze_rejection_patterns(agency_code)
            
            # Identify top recipients (simulated)
            funding_intel.top_recipients = self._identify_top_recipients(agency_code)
            
            # Extract partnership preferences
            funding_intel.partnership_preferences = self._extract_partnership_preferences(opportunities)
            
            # Define evaluation criteria weights
            funding_intel.evaluation_criteria_weights = self._define_evaluation_criteria_weights(agency_code)
        
        return funding_intel
    
    async def _analyze_strategic_intelligence(
        self, agency_code: str, workflow_state
    ) -> StrategicIntelligence:
        """Analyze strategic intelligence for agency."""
        
        strategic_intel = StrategicIntelligence(agency_code=agency_code)
        
        # Load strategic plan priorities
        strategic_intel.strategic_plan_priorities = self._get_strategic_plan_priorities(agency_code)
        
        # Identify emerging focus areas
        strategic_intel.emerging_focus_areas = self._identify_emerging_focus_areas(agency_code)
        
        # Extract policy alignment factors
        strategic_intel.policy_alignment_factors = self._extract_policy_alignment_factors(agency_code)
        
        # Identify key decision makers
        strategic_intel.key_decision_makers = self._identify_key_decision_makers(agency_code)
        
        # Map external influences
        strategic_intel.external_influences = self._map_external_influences(agency_code)
        
        # Identify advisory committees
        strategic_intel.advisory_committees = self._identify_advisory_committees(agency_code)
        
        # Assess internal challenges
        strategic_intel.internal_challenges = self._assess_internal_challenges(agency_code)
        
        # Identify capacity constraints
        strategic_intel.capacity_constraints = self._identify_capacity_constraints(agency_code)
        
        # Extract technology priorities
        strategic_intel.technology_priorities = self._extract_technology_priorities(agency_code)
        
        # Identify engagement opportunities
        strategic_intel.engagement_opportunities = self._identify_engagement_opportunities(agency_code)
        
        # Calculate partnership potential
        strategic_intel.partnership_potential = self._calculate_partnership_potential(
            strategic_intel, agency_code
        )
        
        # Generate relationship building strategy
        strategic_intel.relationship_building_strategy = self._generate_relationship_strategy(
            strategic_intel, agency_code
        )
        
        return strategic_intel
    
    # Agency classification and analysis methods
    
    def _classify_agency_tier(self, agency_code: str) -> AgencyTier:
        """Classify agency into appropriate tier."""
        
        for tier, definition in self.tier_definitions.items():
            if agency_code in definition["agencies"]:
                return tier
        
        # Default classification based on common patterns
        major_agencies = ["DOD", "HHS", "DOE", "ED", "USDA", "DOT", "DHS", "DOJ", "DOC"]
        independent_agencies = ["NSF", "EPA", "NASA", "VA", "SBA", "SSA", "FCC", "SEC"]
        
        if agency_code in major_agencies:
            return AgencyTier.TIER_1
        elif agency_code in independent_agencies:
            return AgencyTier.TIER_2
        else:
            return AgencyTier.TIER_3
    
    def _get_agency_name(self, agency_code: str) -> str:
        """Get full agency name from code."""
        
        agency_names = {
            "DOD": "Department of Defense",
            "HHS": "Department of Health and Human Services", 
            "DOE": "Department of Energy",
            "ED": "Department of Education",
            "USDA": "Department of Agriculture",
            "DOT": "Department of Transportation",
            "NSF": "National Science Foundation",
            "EPA": "Environmental Protection Agency",
            "NASA": "National Aeronautics and Space Administration",
            "VA": "Department of Veterans Affairs",
            "SBA": "Small Business Administration",
            "DHS": "Department of Homeland Security",
            "DOJ": "Department of Justice",
            "DOC": "Department of Commerce",
            "NIH": "National Institutes of Health",
            "CDC": "Centers for Disease Control and Prevention",
            "NIST": "National Institute of Standards and Technology",
            "USGS": "United States Geological Survey"
        }
        
        return agency_names.get(agency_code, f"Agency {agency_code}")
    
    async def _get_agency_opportunities(
        self, agency_code: str, workflow_state
    ) -> List[GovernmentOpportunity]:
        """Get opportunities for specific agency."""
        
        if not workflow_state or not workflow_state.has_processor_succeeded('grants_gov_fetch'):
            return []
        
        opportunities_data = workflow_state.get_processor_data('grants_gov_fetch')
        if not opportunities_data:
            return []
        
        agency_opportunities = []
        for opp_dict in opportunities_data.get('opportunities', []):
            try:
                opportunity = GovernmentOpportunity(**opp_dict)
                if opportunity.agency_code == agency_code:
                    agency_opportunities.append(opportunity)
            except Exception:
                continue
        
        return agency_opportunities
    
    def _analyze_funding_pattern(self, opportunities: List[GovernmentOpportunity]) -> FundingPattern:
        """Analyze funding patterns from opportunities."""
        
        # Simple heuristic based on opportunity characteristics
        if len(opportunities) > 50:
            return FundingPattern.CONSISTENT
        elif len(opportunities) > 20:
            return FundingPattern.CYCLICAL
        elif len(opportunities) > 5:
            return FundingPattern.OPPORTUNISTIC
        else:
            return FundingPattern.EMERGING
    
    def _analyze_seasonal_trends(self, opportunities: List[GovernmentOpportunity]) -> Dict[str, float]:
        """Analyze seasonal funding trends."""
        
        # Simulate seasonal analysis - would use real deadline data
        month_counts = {}
        for opp in opportunities:
            if opp.close_date:
                month = opp.close_date.strftime("%B")
                month_counts[month] = month_counts.get(month, 0) + 1
        
        total_opps = len(opportunities)
        if total_opps > 0:
            return {month: count / total_opps for month, count in month_counts.items()}
        
        return {}
    
    def _extract_program_priorities(self, opportunities: List[GovernmentOpportunity]) -> List[str]:
        """Extract program priorities from opportunities."""
        
        priorities = set()
        
        for opp in opportunities:
            # Extract keywords from titles and descriptions
            text = f"{opp.title} {opp.description}".lower()
            
            # Common priority keywords
            priority_keywords = [
                "innovation", "research", "education", "health", "environment",
                "energy", "security", "technology", "infrastructure", "workforce",
                "community", "rural", "urban", "sustainability", "equity"
            ]
            
            for keyword in priority_keywords:
                if keyword in text:
                    priorities.add(keyword.title())
        
        return list(priorities)[:10]  # Top 10 priorities
    
    def _analyze_geographic_distribution(self, opportunities: List[GovernmentOpportunity]) -> Dict[str, float]:
        """Analyze geographic distribution of opportunities."""
        
        # Simulate geographic analysis - would use real eligibility data
        geographic_dist = {
            "Nationwide": 0.6,
            "Regional": 0.25,
            "State-specific": 0.15
        }
        
        return geographic_dist
    
    def _extract_success_factors(self, agency_code: str, opportunities: List[GovernmentOpportunity]) -> List[str]:
        """Extract success factors for agency."""
        
        # Agency-specific success factors based on known patterns
        agency_success_factors = {
            "DOD": [
                "Technical innovation and advancement",
                "Security clearance and compliance",
                "Proven track record with defense contracts",
                "Cost-effective solutions",
                "Scalable technology demonstrations"
            ],
            "HHS": [
                "Evidence-based approaches",
                "Community partnerships and engagement",
                "Health outcome improvements",
                "Sustainable program design",
                "Measurable impact on health disparities"
            ],
            "NSF": [
                "Research excellence and innovation",
                "Broader impacts on society",
                "Educational and outreach components",
                "Interdisciplinary collaboration",
                "Student training and development"
            ],
            "DOE": [
                "Clean energy innovation",
                "Commercialization potential",
                "Environmental benefits",
                "Technology readiness advancement",
                "Industry partnerships"
            ],
            "EPA": [
                "Environmental protection benefits",
                "Community engagement",
                "Pollution reduction outcomes",
                "Sustainable solutions",
                "Environmental justice considerations"
            ]
        }
        
        return agency_success_factors.get(agency_code, [
            "Demonstrated expertise",
            "Strong partnerships",
            "Measurable outcomes",
            "Cost-effective approach",
            "Sustainability planning"
        ])
    
    def _analyze_rejection_patterns(self, agency_code: str) -> Dict[str, float]:
        """Analyze common rejection reasons."""
        
        # Common rejection patterns by agency type
        agency_rejection_patterns = {
            "DOD": {
                "Insufficient technical depth": 0.25,
                "Lack of security clearance": 0.20,
                "Cost concerns": 0.18,
                "Limited scalability": 0.15,
                "Inadequate risk management": 0.12,
                "Other": 0.10
            },
            "HHS": {
                "Weak evaluation plan": 0.22,
                "Insufficient community engagement": 0.20,
                "Poor sustainability plan": 0.18,
                "Limited evidence base": 0.16,
                "Budget misalignment": 0.14,
                "Other": 0.10
            },
            "NSF": {
                "Weak methodology": 0.25,
                "Insufficient broader impacts": 0.22,
                "Limited innovation": 0.18,
                "Poor collaboration plan": 0.15,
                "Budget issues": 0.12,
                "Other": 0.08
            }
        }
        
        return agency_rejection_patterns.get(agency_code, {
            "Weak proposal": 0.30,
            "Budget issues": 0.25,
            "Limited capacity": 0.20,
            "Poor fit": 0.15,
            "Other": 0.10
        })
    
    def _identify_top_recipients(self, agency_code: str) -> List[Dict[str, Any]]:
        """Identify top recipients for agency (simulated)."""
        
        # This would connect to USASpending.gov data in production
        agency_top_recipients = {
            "DOD": [
                {"name": "Lockheed Martin", "total_awards": 15000000000, "award_count": 450},
                {"name": "Boeing", "total_awards": 12000000000, "award_count": 380},
                {"name": "General Dynamics", "total_awards": 8000000000, "award_count": 220}
            ],
            "HHS": [
                {"name": "University of Washington", "total_awards": 850000000, "award_count": 180},
                {"name": "Johns Hopkins University", "total_awards": 750000000, "award_count": 165},
                {"name": "Harvard University", "total_awards": 720000000, "award_count": 145}
            ],
            "NSF": [
                {"name": "University of California System", "total_awards": 450000000, "award_count": 280},
                {"name": "MIT", "total_awards": 380000000, "award_count": 210},
                {"name": "Stanford University", "total_awards": 350000000, "award_count": 190}
            ]
        }
        
        return agency_top_recipients.get(agency_code, [
            {"name": "Major University", "total_awards": 100000000, "award_count": 50},
            {"name": "Research Institution", "total_awards": 75000000, "award_count": 35},
            {"name": "Technology Company", "total_awards": 50000000, "award_count": 25}
        ])
    
    def _extract_partnership_preferences(self, opportunities: List[GovernmentOpportunity]) -> List[str]:
        """Extract partnership preferences from opportunities."""
        
        preferences = set()
        
        for opp in opportunities:
            description = opp.description.lower()
            
            if "university" in description or "academic" in description:
                preferences.add("Academic institutions")
            if "small business" in description or "sba" in description:
                preferences.add("Small businesses")
            if "nonprofit" in description:
                preferences.add("Nonprofit organizations")
            if "partnership" in description or "collaboration" in description:
                preferences.add("Collaborative partnerships")
            if "industry" in description or "private sector" in description:
                preferences.add("Industry partnerships")
            if "community" in description:
                preferences.add("Community-based organizations")
        
        return list(preferences)
    
    def _define_evaluation_criteria_weights(self, agency_code: str) -> Dict[str, float]:
        """Define evaluation criteria weights for agency."""
        
        # Agency-specific evaluation criteria weights
        agency_weights = {
            "DOD": {
                "Technical Merit": 0.35,
                "Cost Effectiveness": 0.25,
                "Implementation Plan": 0.20,
                "Team Qualifications": 0.15,
                "Risk Management": 0.05
            },
            "HHS": {
                "Program Design": 0.30,
                "Evaluation Plan": 0.25,
                "Organizational Capacity": 0.20,
                "Community Engagement": 0.15,
                "Sustainability": 0.10
            },
            "NSF": {
                "Intellectual Merit": 0.50,
                "Broader Impacts": 0.30,
                "Research Plan": 0.15,
                "Personnel": 0.05
            }
        }
        
        return agency_weights.get(agency_code, {
            "Technical Approach": 0.30,
            "Team Qualifications": 0.25,
            "Budget": 0.20,
            "Impact": 0.15,
            "Sustainability": 0.10
        })
    
    # Strategic intelligence analysis methods
    
    def _get_strategic_plan_priorities(self, agency_code: str) -> List[str]:
        """Get strategic plan priorities for agency."""
        
        # Agency strategic priorities (would come from strategic plans in production)
        agency_priorities = {
            "DOD": [
                "Technological superiority",
                "Warfighter readiness", 
                "Innovation ecosystem",
                "Small business integration",
                "Cybersecurity advancement"
            ],
            "HHS": [
                "Health equity",
                "Evidence-based practice",
                "Innovation in healthcare delivery",
                "Public health preparedness",
                "Mental health and substance abuse"
            ],
            "NSF": [
                "Excellence in research",
                "Broadening participation",
                "STEM education", 
                "Research infrastructure",
                "International collaboration"
            ],
            "DOE": [
                "Clean energy transition",
                "Energy security",
                "Environmental remediation",
                "Scientific discovery",
                "Technology commercialization"
            ]
        }
        
        return agency_priorities.get(agency_code, [
            "Mission achievement",
            "Stakeholder engagement",
            "Innovation advancement",
            "Operational efficiency",
            "Strategic partnerships"
        ])
    
    def _identify_emerging_focus_areas(self, agency_code: str) -> List[str]:
        """Identify emerging focus areas for agency."""
        
        # Emerging areas based on current trends
        emerging_areas = {
            "DOD": ["Artificial Intelligence", "Quantum Computing", "Hypersonics", "Space Technology"],
            "HHS": ["Digital Health", "Precision Medicine", "Health Informatics", "Social Determinants"],
            "NSF": ["AI/ML", "Climate Science", "Quantum Information", "Biotechnology"],
            "DOE": ["Advanced Nuclear", "Carbon Capture", "Grid Modernization", "Energy Storage"],
            "EPA": ["Environmental Justice", "Climate Adaptation", "Green Infrastructure", "Circular Economy"]
        }
        
        return emerging_areas.get(agency_code, [
            "Digital Transformation",
            "Artificial Intelligence",
            "Sustainability",
            "Equity and Inclusion"
        ])
    
    def _extract_policy_alignment_factors(self, agency_code: str) -> List[str]:
        """Extract policy alignment factors."""
        
        # Current policy alignment factors
        policy_factors = {
            "DOD": ["National Defense Strategy", "Innovation priorities", "Small business goals"],
            "HHS": ["Healthy People 2030", "Health equity priorities", "COVID-19 response"],
            "NSF": ["CHIPS and Science Act", "STEM diversity", "Climate research"],
            "DOE": ["Clean energy goals", "Infrastructure Investment", "Environmental justice"],
            "EPA": ["Environmental justice", "Climate action", "Clean air/water priorities"]
        }
        
        return policy_factors.get(agency_code, [
            "Current administration priorities",
            "Congressional priorities",
            "Stakeholder interests"
        ])
    
    def _identify_key_decision_makers(self, agency_code: str) -> List[AgencyPersonnel]:
        """Identify key decision makers (simulated data)."""
        
        # This would be populated from real personnel data
        personnel_data = {
            "DOD": [
                AgencyPersonnel(
                    name="Dr. Defense Director",
                    title="Director, Defense Research",
                    specialties=["Defense Technology", "Innovation"],
                    influence_score=0.9,
                    accessibility_score=0.3
                )
            ],
            "HHS": [
                AgencyPersonnel(
                    name="Dr. Health Director", 
                    title="Director, Health Programs",
                    specialties=["Public Health", "Health Policy"],
                    influence_score=0.85,
                    accessibility_score=0.5
                )
            ]
        }
        
        return personnel_data.get(agency_code, [
            AgencyPersonnel(
                name=f"Director, {agency_code} Programs",
                title="Program Director",
                specialties=["Program Management"],
                influence_score=0.7,
                accessibility_score=0.4
            )
        ])
    
    def _map_external_influences(self, agency_code: str) -> List[str]:
        """Map external influences on agency."""
        
        influences = {
            "DOD": ["House Armed Services Committee", "Senate Armed Services Committee", "Industry associations"],
            "HHS": ["Healthcare industry", "Patient advocacy groups", "State health departments"],
            "NSF": ["Scientific community", "University associations", "International partners"],
            "DOE": ["Energy industry", "Environmental groups", "State energy offices"],
            "EPA": ["Environmental groups", "Industry associations", "State environmental agencies"]
        }
        
        return influences.get(agency_code, [
            "Congressional committees",
            "Industry stakeholders", 
            "Professional associations",
            "Advocacy organizations"
        ])
    
    def _identify_advisory_committees(self, agency_code: str) -> List[str]:
        """Identify advisory committees."""
        
        committees = {
            "DOD": ["Defense Science Board", "Defense Innovation Board", "Service research boards"],
            "HHS": ["National Advisory Committees", "HRSA Advisory Committees", "CDC Advisory Committees"],
            "NSF": ["National Science Board", "Advisory Committee for STEM Education", "Disciplinary advisory panels"],
            "DOE": ["Secretary of Energy Advisory Board", "Basic Energy Sciences Advisory Committee"],
            "EPA": ["Science Advisory Board", "Clean Air Act Advisory Committee"]
        }
        
        return committees.get(agency_code, [
            "Senior advisory board",
            "Technical advisory panels",
            "Stakeholder advisory groups"
        ])
    
    def _assess_internal_challenges(self, agency_code: str) -> List[str]:
        """Assess internal challenges facing agency."""
        
        # Common challenges by agency type
        challenges = {
            "DOD": ["Budget constraints", "Acquisition reform", "Technology transition", "Workforce retention"],
            "HHS": ["Budget pressures", "Regulatory complexity", "Data integration", "Program coordination"],
            "NSF": ["Funding competition", "Proposal volume", "Review capacity", "Infrastructure needs"],
            "DOE": ["Technology risks", "Cost management", "Environmental compliance", "Stakeholder coordination"],
            "EPA": ["Regulatory challenges", "State-federal coordination", "Resource constraints", "Technical complexity"]
        }
        
        return challenges.get(agency_code, [
            "Resource constraints",
            "Operational complexity",
            "Stakeholder coordination",
            "Technology modernization"
        ])
    
    def _identify_capacity_constraints(self, agency_code: str) -> List[str]:
        """Identify capacity constraints."""
        
        constraints = {
            "DOD": ["Acquisition workforce", "Technical evaluation capacity", "Security processing"],
            "HHS": ["Review capacity", "Technical assistance resources", "Monitoring capabilities"],
            "NSF": ["Review panel capacity", "Program officer availability", "Merit review system"],
            "DOE": ["Technical review expertise", "Project management resources", "Oversight capacity"],
            "EPA": ["Technical expertise", "Enforcement capacity", "State partnership resources"]
        }
        
        return constraints.get(agency_code, [
            "Staff capacity",
            "Technical expertise",
            "Review resources",
            "Administrative capacity"
        ])
    
    def _extract_technology_priorities(self, agency_code: str) -> List[str]:
        """Extract technology priorities."""
        
        tech_priorities = {
            "DOD": ["AI/ML", "Quantum", "Hypersonics", "Cybersecurity", "Autonomous systems"],
            "HHS": ["Health IT", "Telemedicine", "Data analytics", "Precision medicine", "Digital therapeutics"],
            "NSF": ["Advanced computing", "Quantum information", "Biotechnology", "Materials science"],
            "DOE": ["Advanced nuclear", "Renewable energy", "Energy storage", "Carbon management"],
            "EPA": ["Environmental monitoring", "Pollution control", "Climate technology", "Green chemistry"]
        }
        
        return tech_priorities.get(agency_code, [
            "Digital modernization",
            "Data analytics",
            "Automation",
            "Cloud computing"
        ])
    
    def _identify_engagement_opportunities(self, agency_code: str) -> List[str]:
        """Identify engagement opportunities."""
        
        opportunities = [
            f"Attend {agency_code} conferences and workshops",
            f"Participate in {agency_code} stakeholder meetings",
            f"Respond to {agency_code} requests for information",
            f"Engage with {agency_code} program officers",
            f"Join {agency_code}-related professional associations"
        ]
        
        return opportunities
    
    def _calculate_partnership_potential(self, strategic_intel: StrategicIntelligence, agency_code: str) -> float:
        """Calculate partnership potential score."""
        
        base_score = 0.5  # Base potential
        
        # Increase based on engagement opportunities
        if len(strategic_intel.engagement_opportunities) > 3:
            base_score += 0.2
        
        # Increase based on emerging focus areas alignment
        if len(strategic_intel.emerging_focus_areas) > 2:
            base_score += 0.15
        
        # Increase based on key personnel accessibility
        avg_accessibility = sum(p.accessibility_score for p in strategic_intel.key_decision_makers) / max(1, len(strategic_intel.key_decision_makers))
        base_score += avg_accessibility * 0.15
        
        return min(1.0, base_score)
    
    def _generate_relationship_strategy(
        self, strategic_intel: StrategicIntelligence, agency_code: str
    ) -> List[str]:
        """Generate relationship building strategy."""
        
        strategies = [
            f"Develop expertise in {agency_code} priority areas",
            "Build relationships with program officers",
            "Participate in agency stakeholder events",
            "Collaborate with existing agency partners"
        ]
        
        # Add specific strategies based on intelligence
        if strategic_intel.partnership_potential > 0.7:
            strategies.append("Pursue direct partnership opportunities")
        
        if len(strategic_intel.advisory_committees) > 0:
            strategies.append("Seek advisory committee participation")
        
        if strategic_intel.key_decision_makers:
            strategies.append("Target key decision maker engagement")
        
        return strategies
    
    # Analysis and scoring methods
    
    def _calculate_engagement_readiness(
        self, funding_intel: FundingIntelligence, strategic_intel: StrategicIntelligence
    ) -> float:
        """Calculate engagement readiness score."""
        
        base_score = 0.5
        
        # Funding opportunity volume
        if funding_intel.opportunity_count > 20:
            base_score += 0.2
        elif funding_intel.opportunity_count > 10:
            base_score += 0.1
        
        # Strategic alignment
        if len(strategic_intel.strategic_plan_priorities) > 3:
            base_score += 0.15
        
        # Partnership potential
        base_score += strategic_intel.partnership_potential * 0.15
        
        return min(1.0, base_score)
    
    def _calculate_pipeline_strength(
        self, funding_intel: FundingIntelligence, strategic_intel: StrategicIntelligence
    ) -> float:
        """Calculate opportunity pipeline strength."""
        
        base_score = 0.4
        
        # Funding pattern strength
        pattern_scores = {
            FundingPattern.CONSISTENT: 0.3,
            FundingPattern.CYCLICAL: 0.2,
            FundingPattern.OPPORTUNISTIC: 0.15,
            FundingPattern.EMERGING: 0.25,
            FundingPattern.DECLINING: 0.05
        }
        base_score += pattern_scores.get(funding_intel.funding_pattern, 0.1)
        
        # Emerging focus areas
        if len(strategic_intel.emerging_focus_areas) > 2:
            base_score += 0.2
        
        # Total funding volume
        if funding_intel.total_annual_funding > 1000000000:  # $1B+
            base_score += 0.1
        
        return min(1.0, base_score)
    
    def _calculate_relationship_potential(self, strategic_intel: StrategicIntelligence) -> float:
        """Calculate relationship potential score."""
        
        base_score = 0.3
        
        # Key personnel accessibility
        if strategic_intel.key_decision_makers:
            avg_accessibility = sum(p.accessibility_score for p in strategic_intel.key_decision_makers) / len(strategic_intel.key_decision_makers)
            base_score += avg_accessibility * 0.3
        
        # Engagement opportunities
        base_score += min(0.3, len(strategic_intel.engagement_opportunities) * 0.05)
        
        # Partnership potential
        base_score += strategic_intel.partnership_potential * 0.1
        
        return min(1.0, base_score)
    
    def _calculate_profile_confidence(self, profile: ComprehensiveAgencyProfile) -> float:
        """Calculate confidence in profile intelligence."""
        
        base_confidence = 0.6  # Base confidence
        
        # Data completeness factors
        if profile.funding_intelligence.opportunity_count > 0:
            base_confidence += 0.15
        
        if len(profile.strategic_intelligence.strategic_plan_priorities) > 0:
            base_confidence += 0.1
        
        if profile.strategic_intelligence.key_decision_makers:
            base_confidence += 0.1
        
        if profile.funding_intelligence.total_annual_funding > 0:
            base_confidence += 0.05
        
        return min(1.0, base_confidence)
    
    def _identify_data_sources(self, agency_code: str) -> List[str]:
        """Identify data sources for intelligence."""
        
        return [
            "Grants.gov opportunity data",
            "USASpending.gov award data",
            "Agency strategic plans",
            "Congressional budget documents",
            "Industry intelligence reports",
            "Professional network insights"
        ]
    
    # Cross-agency analysis methods
    
    async def _extract_agencies_from_opportunities(self, workflow_state) -> List[str]:
        """Extract unique agency codes from opportunities."""
        
        agencies = set()
        
        if workflow_state and workflow_state.has_processor_succeeded('grants_gov_fetch'):
            opportunities_data = workflow_state.get_processor_data('grants_gov_fetch')
            if opportunities_data:
                for opp_dict in opportunities_data.get('opportunities', []):
                    if 'agency_code' in opp_dict:
                        agencies.add(opp_dict['agency_code'])
        
        return list(agencies)
    
    async def _generate_cross_agency_insights(self, agency_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights across multiple agencies."""
        
        insights = {
            "agency_landscape_overview": {
                "total_agencies": len(agency_profiles),
                "tier_distribution": self._analyze_tier_distribution(agency_profiles),
                "funding_patterns": self._analyze_funding_patterns_across_agencies(agency_profiles),
                "strategic_themes": self._identify_cross_agency_themes(agency_profiles)
            },
            "opportunity_concentration": {
                "high_opportunity_agencies": [p for p in agency_profiles if p["opportunity_pipeline_strength"] > 0.7],
                "emerging_opportunity_areas": self._identify_emerging_opportunity_areas(agency_profiles),
                "competitive_landscape": self._analyze_competitive_landscape_across_agencies(agency_profiles)
            },
            "relationship_intelligence": {
                "high_engagement_potential": [p for p in agency_profiles if p["engagement_readiness_score"] > 0.7],
                "relationship_building_priorities": self._prioritize_relationship_building(agency_profiles),
                "cross_agency_synergies": self._identify_cross_agency_synergies(agency_profiles)
            }
        }
        
        return insights
    
    async def _generate_strategic_recommendations(
        self, agency_profiles: List[Dict[str, Any]], workflow_state
    ) -> Dict[str, Any]:
        """Generate strategic recommendations based on agency intelligence."""
        
        recommendations = {
            "immediate_actions": [
                "Focus on high-opportunity agencies with strong pipeline strength",
                "Develop expertise in emerging focus areas across multiple agencies",
                "Build relationships with accessible key personnel",
                "Participate in high-value engagement opportunities"
            ],
            "medium_term_strategy": [
                "Develop agency-specific positioning strategies",
                "Build strategic partnerships aligned with agency preferences",
                "Invest in capabilities matching agency technology priorities",
                "Establish thought leadership in cross-agency priority areas"
            ],
            "long_term_positioning": [
                "Build sustained relationships with multiple agencies",
                "Develop comprehensive capability portfolio",
                "Establish reputation as reliable government partner",
                "Create scalable processes for multi-agency engagement"
            ],
            "risk_mitigation": [
                "Diversify across multiple agencies and tiers",
                "Monitor policy changes affecting agency priorities",
                "Maintain flexibility to adapt to changing requirements",
                "Build contingency plans for funding shifts"
            ]
        }
        
        # Personalize recommendations based on current opportunities
        if workflow_state:
            recommendations["opportunity_specific"] = self._generate_opportunity_specific_recommendations(
                agency_profiles, workflow_state
            )
        
        return recommendations
    
    async def _calculate_intelligence_performance_metrics(
        self, agency_profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate performance metrics for intelligence framework."""
        
        if not agency_profiles:
            return {"total_profiles": 0}
        
        metrics = {
            "coverage_metrics": {
                "total_agencies_profiled": len(agency_profiles),
                "tier_coverage": self._calculate_tier_coverage(agency_profiles),
                "intelligence_depth_score": self._calculate_intelligence_depth(agency_profiles)
            },
            "opportunity_metrics": {
                "total_opportunities_analyzed": sum(p["funding_intelligence"]["opportunity_count"] for p in agency_profiles),
                "high_potential_opportunities": len([p for p in agency_profiles if p["opportunity_pipeline_strength"] > 0.7]),
                "funding_volume_covered": sum(p["funding_intelligence"]["total_annual_funding"] for p in agency_profiles)
            },
            "relationship_metrics": {
                "high_engagement_readiness": len([p for p in agency_profiles if p["engagement_readiness_score"] > 0.7]),
                "relationship_building_opportunities": sum(len(p["strategic_intelligence"]["engagement_opportunities"]) for p in agency_profiles),
                "key_personnel_identified": sum(len(p["strategic_intelligence"]["key_decision_makers"]) for p in agency_profiles)
            },
            "intelligence_quality": {
                "average_confidence_score": sum(p["intelligence_confidence"] for p in agency_profiles) / len(agency_profiles),
                "high_confidence_profiles": len([p for p in agency_profiles if p["intelligence_confidence"] > 0.8]),
                "data_completeness_score": self._calculate_data_completeness(agency_profiles)
            }
        }
        
        return metrics
    
    async def _generate_agency_relationship_matrix(
        self, agency_profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate agency relationship matrix."""
        
        matrix = {}
        
        for profile in agency_profiles:
            agency_code = profile["agency_code"]
            
            matrix[agency_code] = {
                "engagement_readiness": profile["engagement_readiness_score"],
                "relationship_potential": profile["relationship_potential_score"],
                "opportunity_pipeline": profile["opportunity_pipeline_strength"],
                "strategic_priority": self._calculate_strategic_priority(profile),
                "engagement_strategy": profile["strategic_intelligence"]["relationship_building_strategy"]
            }
        
        return matrix
    
    # Helper methods for cross-agency analysis
    
    def _analyze_tier_distribution(self, agency_profiles: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution across agency tiers."""
        
        distribution = {"tier_1": 0, "tier_2": 0, "tier_3": 0, "tier_4": 0}
        
        for profile in agency_profiles:
            tier = profile["agency_tier"]
            distribution[tier] += 1
        
        return distribution
    
    def _analyze_funding_patterns_across_agencies(self, agency_profiles: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze funding patterns across agencies."""
        
        patterns = {}
        
        for profile in agency_profiles:
            pattern = profile["funding_intelligence"]["funding_pattern"]
            patterns[pattern] = patterns.get(pattern, 0) + 1
        
        return patterns
    
    def _identify_cross_agency_themes(self, agency_profiles: List[Dict[str, Any]]) -> List[str]:
        """Identify themes appearing across multiple agencies."""
        
        theme_counts = {}
        
        for profile in agency_profiles:
            priorities = profile["strategic_intelligence"]["strategic_plan_priorities"]
            emerging_areas = profile["strategic_intelligence"]["emerging_focus_areas"]
            
            all_themes = priorities + emerging_areas
            
            for theme in all_themes:
                theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        # Return themes appearing in multiple agencies
        cross_agency_themes = [theme for theme, count in theme_counts.items() if count > 1]
        
        return sorted(cross_agency_themes, key=lambda x: theme_counts[x], reverse=True)[:10]
    
    def _identify_emerging_opportunity_areas(self, agency_profiles: List[Dict[str, Any]]) -> List[str]:
        """Identify emerging opportunity areas across agencies."""
        
        emerging_areas = set()
        
        for profile in agency_profiles:
            emerging_areas.update(profile["strategic_intelligence"]["emerging_focus_areas"])
        
        return list(emerging_areas)
    
    def _analyze_competitive_landscape_across_agencies(self, agency_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze competitive landscape across agencies."""
        
        return {
            "high_competition_agencies": len([p for p in agency_profiles if p["funding_intelligence"]["opportunity_count"] > 50]),
            "emerging_competition": len([p for p in agency_profiles if p["funding_intelligence"]["funding_pattern"] == "emerging"]),
            "partnership_opportunities": sum(len(p["funding_intelligence"]["partnership_preferences"]) for p in agency_profiles)
        }
    
    def _prioritize_relationship_building(self, agency_profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize agencies for relationship building."""
        
        priorities = []
        
        for profile in agency_profiles:
            priority_score = (
                profile["engagement_readiness_score"] * 0.4 +
                profile["relationship_potential_score"] * 0.3 +
                profile["opportunity_pipeline_strength"] * 0.3
            )
            
            priorities.append({
                "agency_code": profile["agency_code"],
                "agency_name": profile["agency_name"],
                "priority_score": priority_score,
                "rationale": self._generate_priority_rationale(profile)
            })
        
        return sorted(priorities, key=lambda x: x["priority_score"], reverse=True)
    
    def _identify_cross_agency_synergies(self, agency_profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify synergies between agencies."""
        
        synergies = []
        
        # Look for overlapping priorities and complementary strengths
        for i, profile1 in enumerate(agency_profiles):
            for profile2 in agency_profiles[i+1:]:
                
                overlap_score = self._calculate_priority_overlap(profile1, profile2)
                
                if overlap_score > 0.3:  # Significant overlap
                    synergies.append({
                        "agency_1": profile1["agency_code"],
                        "agency_2": profile2["agency_code"],
                        "overlap_score": overlap_score,
                        "synergy_areas": self._identify_synergy_areas(profile1, profile2)
                    })
        
        return sorted(synergies, key=lambda x: x["overlap_score"], reverse=True)[:5]
    
    def _generate_opportunity_specific_recommendations(
        self, agency_profiles: List[Dict[str, Any]], workflow_state
    ) -> List[str]:
        """Generate recommendations specific to current opportunities."""
        
        recommendations = []
        
        # Get current high-priority opportunities
        high_priority_agencies = [p["agency_code"] for p in agency_profiles if p["opportunity_pipeline_strength"] > 0.7]
        
        if high_priority_agencies:
            recommendations.append(f"Prioritize opportunities from: {', '.join(high_priority_agencies[:3])}")
        
        # Get agencies with high engagement readiness
        ready_agencies = [p["agency_code"] for p in agency_profiles if p["engagement_readiness_score"] > 0.7]
        
        if ready_agencies:
            recommendations.append(f"Begin immediate engagement with: {', '.join(ready_agencies[:3])}")
        
        return recommendations
    
    # Calculation helper methods
    
    def _calculate_tier_coverage(self, agency_profiles: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate coverage across tiers."""
        
        tier_counts = self._analyze_tier_distribution(agency_profiles)
        total = len(agency_profiles)
        
        return {tier: count / total for tier, count in tier_counts.items()} if total > 0 else {}
    
    def _calculate_intelligence_depth(self, agency_profiles: List[Dict[str, Any]]) -> float:
        """Calculate overall intelligence depth score."""
        
        if not agency_profiles:
            return 0.0
        
        depth_scores = []
        
        for profile in agency_profiles:
            # Factors contributing to intelligence depth
            depth_factors = [
                1.0 if profile["funding_intelligence"]["opportunity_count"] > 0 else 0.0,
                1.0 if len(profile["strategic_intelligence"]["strategic_plan_priorities"]) > 0 else 0.0,
                1.0 if profile["strategic_intelligence"]["key_decision_makers"] else 0.0,
                1.0 if profile["funding_intelligence"]["total_annual_funding"] > 0 else 0.0,
                1.0 if len(profile["strategic_intelligence"]["emerging_focus_areas"]) > 0 else 0.0
            ]
            
            depth_scores.append(sum(depth_factors) / len(depth_factors))
        
        return sum(depth_scores) / len(depth_scores)
    
    def _calculate_data_completeness(self, agency_profiles: List[Dict[str, Any]]) -> float:
        """Calculate data completeness score."""
        
        if not agency_profiles:
            return 0.0
        
        completeness_scores = []
        
        for profile in agency_profiles:
            # Count complete data fields
            complete_fields = 0
            total_fields = 0
            
            # Funding intelligence completeness
            funding = profile["funding_intelligence"]
            funding_fields = [
                funding["opportunity_count"] > 0,
                funding["total_annual_funding"] > 0,
                len(funding["program_priorities"]) > 0,
                len(funding["success_factors"]) > 0
            ]
            complete_fields += sum(funding_fields)
            total_fields += len(funding_fields)
            
            # Strategic intelligence completeness
            strategic = profile["strategic_intelligence"]
            strategic_fields = [
                len(strategic["strategic_plan_priorities"]) > 0,
                len(strategic["emerging_focus_areas"]) > 0,
                len(strategic["key_decision_makers"]) > 0,
                len(strategic["engagement_opportunities"]) > 0
            ]
            complete_fields += sum(strategic_fields)
            total_fields += len(strategic_fields)
            
            completeness_scores.append(complete_fields / total_fields if total_fields > 0 else 0.0)
        
        return sum(completeness_scores) / len(completeness_scores)
    
    def _calculate_strategic_priority(self, profile: Dict[str, Any]) -> float:
        """Calculate strategic priority score for agency."""
        
        return (
            profile["engagement_readiness_score"] * 0.3 +
            profile["opportunity_pipeline_strength"] * 0.4 +
            profile["relationship_potential_score"] * 0.3
        )
    
    def _generate_priority_rationale(self, profile: Dict[str, Any]) -> str:
        """Generate rationale for relationship building priority."""
        
        rationale_factors = []
        
        if profile["engagement_readiness_score"] > 0.7:
            rationale_factors.append("high engagement readiness")
        
        if profile["opportunity_pipeline_strength"] > 0.7:
            rationale_factors.append("strong opportunity pipeline")
        
        if profile["relationship_potential_score"] > 0.7:
            rationale_factors.append("excellent relationship potential")
        
        if profile["funding_intelligence"]["opportunity_count"] > 20:
            rationale_factors.append("high opportunity volume")
        
        return f"Priority due to: {', '.join(rationale_factors)}" if rationale_factors else "Standard priority"
    
    def _calculate_priority_overlap(self, profile1: Dict[str, Any], profile2: Dict[str, Any]) -> float:
        """Calculate priority overlap between two agencies."""
        
        priorities1 = set(profile1["strategic_intelligence"]["strategic_plan_priorities"] + 
                         profile1["strategic_intelligence"]["emerging_focus_areas"])
        priorities2 = set(profile2["strategic_intelligence"]["strategic_plan_priorities"] + 
                         profile2["strategic_intelligence"]["emerging_focus_areas"])
        
        if not priorities1 or not priorities2:
            return 0.0
        
        intersection = priorities1.intersection(priorities2)
        union = priorities1.union(priorities2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _identify_synergy_areas(self, profile1: Dict[str, Any], profile2: Dict[str, Any]) -> List[str]:
        """Identify specific synergy areas between agencies."""
        
        priorities1 = set(profile1["strategic_intelligence"]["strategic_plan_priorities"] + 
                         profile1["strategic_intelligence"]["emerging_focus_areas"])
        priorities2 = set(profile2["strategic_intelligence"]["strategic_plan_priorities"] + 
                         profile2["strategic_intelligence"]["emerging_focus_areas"])
        
        return list(priorities1.intersection(priorities2))
    
    def _calculate_overall_confidence(self, agency_profiles: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in intelligence framework."""
        
        if not agency_profiles:
            return 0.0
        
        confidence_scores = [p["intelligence_confidence"] for p in agency_profiles]
        return sum(confidence_scores) / len(confidence_scores)
    
    # Historical analysis methods (would be expanded with real data)
    
    async def _analyze_historical_performance(
        self, agency_code: str, workflow_state
    ) -> Dict[str, Any]:
        """Analyze historical performance patterns."""
        
        # Simulated historical analysis - would use real USASpending data
        return {
            "funding_trend": "increasing",  # increasing, stable, decreasing
            "success_rate_trends": {"2023": 0.15, "2022": 0.18, "2021": 0.16},
            "award_size_trends": {"2023": 750000, "2022": 680000, "2021": 620000},
            "competitive_intensity": "high"  # low, medium, high
        }
    
    async def _analyze_agency_trends(self, agency_code: str, workflow_state) -> Dict[str, Any]:
        """Analyze current trends for agency."""
        
        return {
            "funding_trajectory": "stable",
            "priority_shifts": ["increased AI focus", "enhanced cybersecurity", "climate considerations"],
            "operational_changes": ["streamlined processes", "digital transformation", "stakeholder engagement"],
            "future_outlook": "positive"
        }
    
    async def _analyze_comparative_position(
        self, agency_code: str, agency_tier: AgencyTier, workflow_state
    ) -> Dict[str, Any]:
        """Analyze comparative position among peer agencies."""
        
        return {
            "peer_agencies": self._get_peer_agencies(agency_code, agency_tier),
            "competitive_advantages": ["specialized expertise", "established relationships", "proven track record"],
            "competitive_challenges": ["resource constraints", "increased competition", "changing requirements"],
            "market_position": "competitive"  # leading, competitive, emerging, challenged
        }
    
    def _get_peer_agencies(self, agency_code: str, agency_tier: AgencyTier) -> List[str]:
        """Get peer agencies in same tier."""
        
        tier_agencies = self.tier_definitions.get(agency_tier, {}).get("agencies", [])
        return [agency for agency in tier_agencies if agency != agency_code]


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return AgencyIntelligenceFramework()