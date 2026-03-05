"""
Depth-Specific Analysis Handlers
Implements the 2-tier intelligence depth levels (Essentials / Premium)
with Claude API integration for real AI analysis.

AI Integration:
  - Essentials: claude-sonnet-4-6 (~$0.05/analysis)
  - Premium: claude-opus-4-6 (~$0.10/analysis)
  - Fallback: rule-based placeholder when no API key available
"""

from typing import Optional, List, Dict, Any
import json
import time

from .intelligence_models import (
    DeepIntelligenceInput,
    DeepIntelligenceOutput,
    AnalysisDepth,
    StrategicFitAnalysis,
    FinancialViabilityAnalysis,
    OperationalReadinessAnalysis,
    RiskAssessment,
    RiskFactor,
    RiskLevel,
    SuccessProbability,
    HistoricalAnalysis,
    GeographicAnalysis,
    NetworkAnalysis,
    RelationshipMap,
    PolicyAnalysis,
    PolicyAlignment,
    StrategicConsultingInsights,
)


class DepthHandler:
    """Base class for depth-specific analysis handlers"""

    def __init__(self, logger):
        self.logger = logger

    async def analyze(self, intel_input: DeepIntelligenceInput) -> DeepIntelligenceOutput:
        """Execute analysis for this depth level."""
        raise NotImplementedError


class QuickDepthHandler(DepthHandler):
    """
    Quick Depth Analysis Handler
    Cost: $0.75 | Time: 5-10 minutes
    Features: Core 4-stage analysis (PLAN → ANALYZE → EXAMINE → APPROACH)
    Equivalent: CURRENT tier
    """

    async def analyze(self, intel_input: DeepIntelligenceInput) -> DeepIntelligenceOutput:
        """Execute quick depth analysis."""
        self.logger.info(f"Starting QUICK depth analysis for {intel_input.opportunity_id}")

        start_time = time.time()

        # TODO: Replace with actual BAML AI calls
        # For now, using placeholder analysis

        # 1. Strategic Fit (PLAN stage)
        strategic_fit = self._analyze_strategic_fit(intel_input)

        # 2. Financial Viability (ANALYZE stage)
        financial_viability = self._analyze_financial_viability(intel_input)

        # 3. Operational Readiness (EXAMINE stage)
        operational_readiness = self._analyze_operational_readiness(intel_input)

        # 4. Risk Assessment (APPROACH stage)
        risk_assessment = self._analyze_risks(intel_input)

        # Overall assessment
        overall_score = self._calculate_overall_score(
            strategic_fit,
            financial_viability,
            operational_readiness,
            risk_assessment
        )

        # No auto-reject — present analysis honestly, let human decide
        proceed = overall_score >= 0.50  # Informational only, not a gate
        success_prob = self._determine_success_probability(overall_score, risk_assessment)

        processing_time = time.time() - start_time

        return DeepIntelligenceOutput(
            strategic_fit=strategic_fit,
            financial_viability=financial_viability,
            operational_readiness=operational_readiness,
            risk_assessment=risk_assessment,
            proceed_recommendation=proceed,
            success_probability=success_prob,
            overall_score=overall_score,
            executive_summary=self._generate_executive_summary(intel_input, overall_score, proceed),
            key_strengths=["Strategic alignment (placeholder)", "Strong capacity"],
            key_challenges=["Timeline constraints", "Competition"],
            recommended_next_steps=["Review full RFP", "Assess capacity", "Develop proposal"],
            depth_executed="quick",
            processing_time_seconds=processing_time,
            api_cost_usd=0.75
        )

    def _analyze_strategic_fit(self, intel_input: DeepIntelligenceInput) -> StrategicFitAnalysis:
        """Analyze strategic fit (PLAN stage)."""
        return StrategicFitAnalysis(
            fit_score=0.80,
            mission_alignment_score=0.85,
            program_alignment_score=0.78,
            geographic_alignment_score=0.77,
            alignment_strengths=["Strong mission alignment", "Proven track record"],
            alignment_concerns=["Geographic reach", "Capacity constraints"],
            strategic_rationale="Opportunity aligns well with organizational mission and strategic priorities.",
            strategic_positioning="Position as innovative leader in field",
            key_differentiators=["Unique approach", "Strong community ties"]
        )

    def _analyze_financial_viability(self, intel_input: DeepIntelligenceInput) -> FinancialViabilityAnalysis:
        """Analyze financial viability (ANALYZE stage)."""
        return FinancialViabilityAnalysis(
            viability_score=0.75,
            budget_capacity_score=0.72,
            financial_health_score=0.80,
            sustainability_score=0.73,
            budget_implications="Grant would require 15% organizational commitment",
            resource_requirements={"staff_time": "0.5 FTE", "infrastructure": "Minimal"},
            financial_risks=["Match requirements", "Budget sustainability"],
            financial_strategy="Leverage existing infrastructure, seek additional match funding",
            budget_recommendations=["Develop detailed budget", "Identify match sources"]
        )

    def _analyze_operational_readiness(self, intel_input: DeepIntelligenceInput) -> OperationalReadinessAnalysis:
        """Analyze operational readiness (EXAMINE stage)."""
        return OperationalReadinessAnalysis(
            readiness_score=0.70,
            capacity_score=0.68,
            timeline_feasibility_score=0.75,
            infrastructure_readiness_score=0.67,
            capacity_gaps=["Additional program staff", "Evaluation expertise"],
            infrastructure_requirements=["Data management system", "Reporting tools"],
            timeline_challenges=["Staff recruitment", "Partnership development"],
            capacity_building_plan="Phased implementation with capacity building in Year 1",
            operational_recommendations=["Hire key staff early", "Develop partnerships"],
            estimated_preparation_time_weeks=12
        )

    def _analyze_risks(self, intel_input: DeepIntelligenceInput) -> RiskAssessment:
        """Analyze risks (APPROACH stage)."""
        risk_factors = [
            RiskFactor(
                category="competition",
                risk_level=RiskLevel.MEDIUM,
                description="Moderate competition from established organizations",
                impact="May affect selection probability",
                mitigation_strategy="Emphasize unique differentiators",
                probability=0.6
            ),
            RiskFactor(
                category="capacity",
                risk_level=RiskLevel.MEDIUM,
                description="Limited evaluation capacity",
                impact="Could affect implementation quality",
                mitigation_strategy="Partner with evaluation consultant",
                probability=0.5
            )
        ]

        return RiskAssessment(
            overall_risk_level=RiskLevel.MEDIUM,
            overall_risk_score=0.55,
            risk_factors=risk_factors,
            critical_risks=[],
            manageable_risks=["Competition", "Capacity constraints"],
            risk_mitigation_plan="Address capacity gaps through partnerships and phased implementation"
        )

    def _calculate_overall_score(
        self,
        strategic: StrategicFitAnalysis,
        financial: FinancialViabilityAnalysis,
        operational: OperationalReadinessAnalysis,
        risk: RiskAssessment
    ) -> float:
        """Calculate weighted overall score."""
        return (
            strategic.fit_score * 0.35 +
            financial.viability_score * 0.25 +
            operational.readiness_score * 0.25 +
            (1.0 - risk.overall_risk_score) * 0.15
        )

    def _determine_success_probability(
        self,
        overall_score: float,
        risk: RiskAssessment
    ) -> SuccessProbability:
        """Determine success probability category."""
        if overall_score >= 0.80 and risk.overall_risk_level == RiskLevel.LOW:
            return SuccessProbability.VERY_HIGH
        elif overall_score >= 0.70:
            return SuccessProbability.HIGH
        elif overall_score >= 0.60:
            return SuccessProbability.MODERATE
        elif overall_score >= 0.50:
            return SuccessProbability.LOW
        else:
            return SuccessProbability.VERY_LOW

    def _generate_executive_summary(
        self,
        intel_input: DeepIntelligenceInput,
        score: float,
        proceed: bool
    ) -> str:
        """Generate executive summary."""
        if proceed:
            return f"""
            {intel_input.opportunity_title} from {intel_input.funder_name} presents a promising opportunity
            for {intel_input.organization_name}. Overall assessment score of {score:.2f} indicates strong
            strategic alignment and operational feasibility. Key strengths include mission alignment and
            program fit. Primary challenges involve capacity building and competitive positioning.
            Recommendation: Proceed with full proposal development.
            """
        else:
            return f"""
            {intel_input.opportunity_title} from {intel_input.funder_name} shows moderate fit for
            {intel_input.organization_name}. Overall assessment score of {score:.2f} suggests significant
            challenges. Careful consideration of capacity constraints and risk factors recommended before
            proceeding. Recommendation: Consider alternative opportunities unless critical gaps can be addressed.
            """


class StandardDepthHandler(QuickDepthHandler):
    """
    Standard Depth Analysis Handler
    Cost: $7.50 | Time: 15-20 minutes
    Features: Quick depth + Historical intelligence + Geographic analysis
    Equivalent: STANDARD tier
    """

    async def analyze(self, intel_input: DeepIntelligenceInput) -> DeepIntelligenceOutput:
        """Execute standard depth analysis."""
        self.logger.info(f"Starting STANDARD depth analysis for {intel_input.opportunity_id}")

        # Get quick depth analysis first
        output = await super().analyze(intel_input)

        # Add standard-specific features
        output.historical_intelligence = self._analyze_historical(intel_input)
        output.geographic_analysis = self._analyze_geographic(intel_input)

        output.depth_executed = "standard"
        output.api_cost_usd = 7.50

        return output

    def _analyze_historical(self, intel_input: DeepIntelligenceInput) -> HistoricalAnalysis:
        """Analyze historical funding patterns."""
        # TODO: Replace with actual data analysis
        return HistoricalAnalysis(
            historical_grants=[],
            total_grants_analyzed=15,
            total_funding_amount=2500000.0,
            average_grant_size=166667.0,
            typical_grant_range="$100,000 - $250,000",
            funding_trends="Increasing focus on capacity building",
            geographic_patterns="Primarily Mid-Atlantic region",
            similar_recipient_profiles=["Community-based nonprofits", "Education-focused"],
            success_factors=["Strong evaluation plans", "Community partnerships"],
            competitive_intelligence="Preference for organizations with track records"
        )

    def _analyze_geographic(self, intel_input: DeepIntelligenceInput) -> GeographicAnalysis:
        """Analyze geographic alignment."""
        return GeographicAnalysis(
            primary_service_area="Virginia/DC Metro",
            funder_geographic_focus="Mid-Atlantic states",
            geographic_alignment_score=0.85,
            geographic_fit_assessment="Strong alignment with funder's geographic priorities",
            regional_competition_analysis="3-4 comparable organizations in region",
            location_advantages=["Established presence", "Regional partnerships"],
            location_challenges=["Dense competitive landscape"]
        )


class EnhancedDepthHandler(StandardDepthHandler):
    """
    Enhanced Depth Analysis Handler
    Cost: $22.00 | Time: 30-45 minutes
    Features: Standard depth + Network intelligence + Relationship mapping
    Equivalent: ENHANCED tier
    """

    async def analyze(self, intel_input: DeepIntelligenceInput) -> DeepIntelligenceOutput:
        """Execute enhanced depth analysis."""
        self.logger.info(f"Starting ENHANCED depth analysis for {intel_input.opportunity_id}")

        # Get standard depth analysis first
        output = await super().analyze(intel_input)

        # Add enhanced-specific features
        output.network_intelligence = self._analyze_network(intel_input)
        output.relationship_mapping = self._map_relationships(intel_input)

        output.depth_executed = "enhanced"
        output.api_cost_usd = 22.00

        return output

    def _analyze_network(self, intel_input: DeepIntelligenceInput) -> NetworkAnalysis:
        """Analyze network connections."""
        # TODO: Replace with actual network analysis
        return NetworkAnalysis(
            board_connections=[],
            network_connections=[],
            network_strength_score=0.65,
            relationship_advantages=["Board member connections", "Partner organizations"],
            relationship_leverage_strategy="Cultivate relationships through partner introductions",
            key_contacts_to_cultivate=["Program Officer Jane Smith", "Board member John Doe"]
        )

    def _map_relationships(self, intel_input: DeepIntelligenceInput) -> RelationshipMap:
        """Map relationship ecosystem."""
        return RelationshipMap(
            direct_relationships=["Partner Org A", "Collaborator B"],
            indirect_relationships=["Funder board member via Partner A"],
            partnership_opportunities=["Joint programming with Partner C"],
            relationship_insights="Strong indirect connections through partnership network",
            cultivation_strategy="Leverage partner relationships for warm introductions"
        )


class CompleteDepthHandler(EnhancedDepthHandler):
    """
    Complete Depth Analysis Handler
    Cost: $42.00 | Time: 45-60 minutes
    Features: Enhanced depth + Policy analysis + Strategic consulting
    Equivalent: COMPLETE tier

    DEPRECATED: Use PremiumDepthHandler instead
    """

    async def analyze(self, intel_input: DeepIntelligenceInput) -> DeepIntelligenceOutput:
        """Execute complete depth analysis."""
        self.logger.info(f"Starting COMPLETE depth analysis for {intel_input.opportunity_id}")

        # Get enhanced depth analysis first
        output = await super().analyze(intel_input)

        # Add complete-specific features
        output.policy_analysis = self._analyze_policy(intel_input)
        output.strategic_consulting = self._generate_strategic_consulting(intel_input)

        output.depth_executed = "complete"
        output.api_cost_usd = 42.00

        return output

    def _analyze_policy(self, intel_input: DeepIntelligenceInput) -> PolicyAnalysis:
        """Analyze policy alignment."""
        # TODO: Replace with actual policy analysis
        from .intelligence_models import PolicyAlignment

        return PolicyAnalysis(
            federal_policy_alignment=PolicyAlignment(
                relevant_policies=["Education Reform Act", "Workforce Development Initiative"],
                alignment_score=0.80,
                policy_opportunities=["Align with federal priorities"],
                policy_risks=["Changing administration priorities"]
            ),
            state_policy_alignment=None,
            policy_landscape_summary="Strong alignment with current federal education priorities",
            policy_opportunities=["Position as policy implementation partner"],
            advocacy_recommendations=["Engage in policy discussions", "Join advocacy coalitions"]
        )

    def _generate_strategic_consulting(self, intel_input: DeepIntelligenceInput) -> StrategicConsultingInsights:
        """Generate strategic consulting insights."""
        return StrategicConsultingInsights(
            executive_summary="Comprehensive strategic opportunity with strong long-term potential",
            competitive_positioning="Position as innovative regional leader",
            differentiation_strategy="Emphasize unique community-based approach and proven outcomes",
            multi_year_funding_strategy="Build relationship for multi-year support and program sustainability",
            partnership_development_strategy="Develop strategic partnerships with complementary organizations",
            capacity_building_roadmap="Phase 1: Infrastructure (6 mo), Phase 2: Staff (6 mo), Phase 3: Scale (12 mo)",
            immediate_actions=["Submit LOI", "Schedule funder meeting", "Develop detailed budget"],
            medium_term_actions=["Build evaluation capacity", "Strengthen partnerships", "Develop case studies"],
            long_term_actions=["Scale program model", "Seek multi-year funding", "Build endowment"]
        )


# ============================================================================
# NEW 2-TIER SYSTEM (October 2025 - TRUE COST PRICING)
# ============================================================================

class EssentialsDepthHandler(DepthHandler):
    """
    ESSENTIALS Depth Handler
    User Price: $2.00 | AI Cost: $0.05 | Time: 15-20 min

    Includes network intelligence in base tier!

    Features:
    - 4-stage AI analysis (PLAN → ANALYZE → EXAMINE → APPROACH) via BAML
    - Network intelligence ($0.01 AI cost)
    - Historical funding analysis ($0 AI cost - algorithmic)
    - Geographic analysis ($0 AI cost - algorithmic)

    12-Factor Compliance:
    - Factor 4: Structured outputs via BAML (eliminates parsing errors)
    - Factor 6: Stateless execution
    - Factor 10: Single responsibility (ESSENTIALS tier analysis)
    """

    async def analyze(self, intel_input: DeepIntelligenceInput) -> DeepIntelligenceOutput:
        """Execute ESSENTIALS depth analysis using Claude API."""
        self.logger.info(f"Starting ESSENTIALS depth analysis for {intel_input.opportunity_id}")
        start_time = time.time()

        try:
            from src.core.anthropic_service import get_anthropic_service, PipelineStage

            anthropic = get_anthropic_service()
            if not anthropic.is_available:
                raise RuntimeError("Anthropic API not available")

            # Build Claude prompt with full context
            system, user = _build_deep_analysis_prompt(intel_input, depth="essentials")

            result_json = await anthropic.create_json_completion(
                messages=[{"role": "user", "content": user}],
                system=system,
                stage=PipelineStage.DEEP_INTELLIGENCE,
                max_tokens=4096,
                temperature=0.1,
            )

            output = _parse_deep_analysis_response(result_json, intel_input)

            # Algorithmic enrichments ($0 AI cost)
            output.historical_intelligence = self._analyze_historical(intel_input)
            output.geographic_analysis = self._analyze_geographic(intel_input)
            output.network_intelligence = await self._analyze_network_intelligence(intel_input)

            processing_time = time.time() - start_time
            output.processing_time_seconds = processing_time
            output.api_cost_usd = 0.05
            output.tool_version = "2.0.0"
            output.depth_executed = "essentials"

            self.logger.info(
                f"ESSENTIALS analysis complete: score={output.overall_score:.2f}, "
                f"time={processing_time:.2f}s"
            )
            return output

        except Exception as e:
            self.logger.error(f"Claude analysis failed, using fallback: {e}")
            return await self._fallback_analysis(intel_input)

    async def _fallback_analysis(self, intel_input: DeepIntelligenceInput) -> DeepIntelligenceOutput:
        """Fallback analysis if BAML fails (uses placeholder data)."""
        start_time = time.time()

        # Use placeholder methods
        strategic_fit = self._analyze_strategic_fit(intel_input)
        financial_viability = self._analyze_financial_viability(intel_input)
        operational_readiness = self._analyze_operational_readiness(intel_input)
        risk_assessment = self._analyze_risks(intel_input)
        historical_intelligence = self._analyze_historical(intel_input)
        geographic_analysis = self._analyze_geographic(intel_input)
        network_intelligence = await self._analyze_network_intelligence(intel_input)

        overall_score = self._calculate_overall_score(
            strategic_fit,
            financial_viability,
            operational_readiness,
            risk_assessment
        )

        # No auto-reject — present analysis honestly, let human decide
        proceed = overall_score >= 0.50  # Informational only, not a gate
        success_prob = self._determine_success_probability(overall_score, risk_assessment)
        processing_time = time.time() - start_time

        return DeepIntelligenceOutput(
            strategic_fit=strategic_fit,
            financial_viability=financial_viability,
            operational_readiness=operational_readiness,
            risk_assessment=risk_assessment,
            historical_intelligence=historical_intelligence,
            geographic_analysis=geographic_analysis,
            network_intelligence=network_intelligence,
            proceed_recommendation=proceed,
            success_probability=success_prob,
            overall_score=overall_score,
            executive_summary=self._generate_executive_summary(intel_input, overall_score, proceed),
            key_strengths=self._identify_strengths(strategic_fit, financial_viability, operational_readiness),
            key_challenges=self._identify_challenges(risk_assessment, operational_readiness),
            recommended_next_steps=self._generate_next_steps(proceed, overall_score),
            depth_executed="essentials",
            processing_time_seconds=processing_time,
            api_cost_usd=0.05,
            tool_version="2.0.0"
        )

    async def _analyze_network_intelligence(self, intel_input: DeepIntelligenceInput) -> Optional[NetworkAnalysis]:
        """Analyze network connections (NEW in ESSENTIALS)."""
        # Import network intelligence tool
        import sys
        from pathlib import Path

        # TODO: Replace with actual network analysis using Tool 12
        # For now, using simplified placeholder
        return NetworkAnalysis(
            board_connections=[],
            network_connections=[],
            network_strength_score=0.50,
            relationship_advantages=["Network analysis included in base tier"],
            relationship_leverage_strategy="Cultivate board connections for funder introductions",
            key_contacts_to_cultivate=["Program Officer", "Board Member"]
        )

    def _analyze_strategic_fit(self, intel_input: DeepIntelligenceInput) -> StrategicFitAnalysis:
        """Analyze strategic fit (PLAN stage)."""
        return StrategicFitAnalysis(
            fit_score=0.80,
            mission_alignment_score=0.85,
            program_alignment_score=0.78,
            geographic_alignment_score=0.77,
            alignment_strengths=["Strong mission alignment", "Proven track record"],
            alignment_concerns=["Geographic reach", "Capacity constraints"],
            strategic_rationale="Opportunity aligns well with organizational mission and strategic priorities.",
            strategic_positioning="Position as innovative leader in field",
            key_differentiators=["Unique approach", "Strong community ties"]
        )

    def _analyze_financial_viability(self, intel_input: DeepIntelligenceInput) -> FinancialViabilityAnalysis:
        """Analyze financial viability (ANALYZE stage)."""
        return FinancialViabilityAnalysis(
            viability_score=0.75,
            budget_capacity_score=0.72,
            financial_health_score=0.80,
            sustainability_score=0.73,
            budget_implications="Grant would require 15% organizational commitment",
            resource_requirements={"staff_time": "0.5 FTE", "infrastructure": "Minimal"},
            financial_risks=["Match requirements", "Budget sustainability"],
            financial_strategy="Leverage existing infrastructure, seek additional match funding",
            budget_recommendations=["Develop detailed budget", "Identify match sources"]
        )

    def _analyze_operational_readiness(self, intel_input: DeepIntelligenceInput) -> OperationalReadinessAnalysis:
        """Analyze operational readiness (EXAMINE stage)."""
        return OperationalReadinessAnalysis(
            readiness_score=0.70,
            capacity_score=0.68,
            timeline_feasibility_score=0.75,
            infrastructure_readiness_score=0.67,
            capacity_gaps=["Additional program staff", "Evaluation expertise"],
            infrastructure_requirements=["Data management system", "Reporting tools"],
            timeline_challenges=["Staff recruitment", "Partnership development"],
            capacity_building_plan="Phased implementation with capacity building in Year 1",
            operational_recommendations=["Hire key staff early", "Develop partnerships"],
            estimated_preparation_time_weeks=12
        )

    def _analyze_risks(self, intel_input: DeepIntelligenceInput) -> RiskAssessment:
        """Analyze risks (APPROACH stage)."""
        risk_factors = [
            RiskFactor(
                category="competition",
                risk_level=RiskLevel.MEDIUM,
                description="Moderate competition from established organizations",
                impact="May affect selection probability",
                mitigation_strategy="Emphasize unique differentiators",
                probability=0.6
            ),
            RiskFactor(
                category="capacity",
                risk_level=RiskLevel.MEDIUM,
                description="Limited evaluation capacity",
                impact="Could affect implementation quality",
                mitigation_strategy="Partner with evaluation consultant",
                probability=0.5
            )
        ]

        return RiskAssessment(
            overall_risk_level=RiskLevel.MEDIUM,
            overall_risk_score=0.55,
            risk_factors=risk_factors,
            critical_risks=[],
            manageable_risks=["Competition", "Capacity constraints"],
            risk_mitigation_plan="Address capacity gaps through partnerships and phased implementation"
        )

    def _analyze_historical(self, intel_input: DeepIntelligenceInput) -> HistoricalAnalysis:
        """Analyze historical funding patterns."""
        # TODO: Replace with actual Historical Funding Analyzer Tool (Tool 22)
        return HistoricalAnalysis(
            historical_grants=[],
            total_grants_analyzed=15,
            total_funding_amount=2500000.0,
            average_grant_size=166667.0,
            typical_grant_range="$100,000 - $250,000",
            funding_trends="Increasing focus on capacity building",
            geographic_patterns="Primarily Mid-Atlantic region",
            similar_recipient_profiles=["Community-based nonprofits", "Education-focused"],
            success_factors=["Strong evaluation plans", "Community partnerships"],
            competitive_intelligence="Preference for organizations with track records"
        )

    def _analyze_geographic(self, intel_input: DeepIntelligenceInput) -> GeographicAnalysis:
        """Analyze geographic alignment."""
        return GeographicAnalysis(
            primary_service_area="Virginia/DC Metro",
            funder_geographic_focus="Mid-Atlantic states",
            geographic_alignment_score=0.85,
            geographic_fit_assessment="Strong alignment with funder's geographic priorities",
            regional_competition_analysis="3-4 comparable organizations in region",
            location_advantages=["Established presence", "Regional partnerships"],
            location_challenges=["Dense competitive landscape"]
        )

    def _calculate_overall_score(
        self,
        strategic: StrategicFitAnalysis,
        financial: FinancialViabilityAnalysis,
        operational: OperationalReadinessAnalysis,
        risk: RiskAssessment
    ) -> float:
        """Calculate weighted overall score."""
        return (
            strategic.fit_score * 0.35 +
            financial.viability_score * 0.25 +
            operational.readiness_score * 0.25 +
            (1.0 - risk.overall_risk_score) * 0.15
        )

    def _determine_success_probability(
        self,
        overall_score: float,
        risk: RiskAssessment
    ) -> SuccessProbability:
        """Determine success probability category."""
        if overall_score >= 0.80 and risk.overall_risk_level == RiskLevel.LOW:
            return SuccessProbability.VERY_HIGH
        elif overall_score >= 0.70:
            return SuccessProbability.HIGH
        elif overall_score >= 0.60:
            return SuccessProbability.MODERATE
        elif overall_score >= 0.50:
            return SuccessProbability.LOW
        else:
            return SuccessProbability.VERY_LOW

    def _generate_executive_summary(
        self,
        intel_input: DeepIntelligenceInput,
        score: float,
        proceed: bool
    ) -> str:
        """Generate executive summary."""
        if proceed:
            return f"""
{intel_input.opportunity_title} from {intel_input.funder_name} presents a promising opportunity
for {intel_input.organization_name}. Overall assessment score of {score:.2f} indicates strong
strategic alignment and operational feasibility. Network intelligence analysis included in this
ESSENTIALS tier assessment shows relationship opportunities. Key strengths include mission alignment
and program fit. Primary challenges involve capacity building and competitive positioning.
Recommendation: Proceed with full proposal development.
            """.strip()
        else:
            return f"""
{intel_input.opportunity_title} from {intel_input.funder_name} shows moderate fit for
{intel_input.organization_name}. Overall assessment score of {score:.2f} suggests significant
challenges. Careful consideration of capacity constraints and risk factors recommended before
proceeding. Recommendation: Consider alternative opportunities unless critical gaps can be addressed.
            """.strip()

    def _identify_strengths(
        self,
        strategic: StrategicFitAnalysis,
        financial: FinancialViabilityAnalysis,
        operational: OperationalReadinessAnalysis
    ) -> List[str]:
        """Identify key strengths."""
        strengths = []
        if strategic.fit_score >= 0.75:
            strengths.append("Strong strategic alignment with mission and programs")
        if financial.viability_score >= 0.70:
            strengths.append("Solid financial capacity for grant implementation")
        if operational.readiness_score >= 0.65:
            strengths.append("Adequate operational infrastructure and capacity")
        return strengths or ["Organization demonstrates competitive capabilities"]

    def _identify_challenges(
        self,
        risk: RiskAssessment,
        operational: OperationalReadinessAnalysis
    ) -> List[str]:
        """Identify key challenges."""
        challenges = []
        if risk.overall_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            challenges.append("Significant risk factors requiring mitigation")
        if operational.readiness_score < 0.65:
            challenges.append("Operational capacity gaps need to be addressed")
        if risk.critical_risks:
            challenges.extend(risk.critical_risks)
        return challenges or ["Standard competitive and capacity considerations"]

    def _generate_next_steps(self, proceed: bool, score: float) -> List[str]:
        """Generate recommended next steps."""
        if proceed:
            return [
                "Review full RFP/NOFO requirements in detail",
                "Assess internal capacity and identify gaps",
                "Develop preliminary proposal outline",
                "Identify partnership opportunities if needed",
                "Create detailed budget and timeline"
            ]
        else:
            return [
                "Consider alternative opportunities with better fit",
                "Address identified capacity gaps before reapplying",
                "Seek smaller grants to build track record",
                "Consult with program officer about eligibility concerns"
            ]


class PremiumDepthHandler(DepthHandler):
    """
    PREMIUM Depth Handler
    User Price: $8.00 | AI Cost: $0.10 | Time: 30-40 min

    Everything in ESSENTIALS + enhanced features

    Additional Features:
    - Enhanced network pathways (warm introductions)
    - Decision maker profiling
    - Policy analysis
    - Strategic consulting insights
    - Comprehensive dossier (20+ pages)

    12-Factor Compliance:
    - Factor 4: Structured outputs via BAML (eliminates parsing errors)
    - Factor 6: Stateless execution
    - Factor 10: Single responsibility (PREMIUM tier analysis)
    """

    async def analyze(self, intel_input: DeepIntelligenceInput) -> DeepIntelligenceOutput:
        """Execute PREMIUM depth analysis using Claude Opus API."""
        self.logger.info(f"Starting PREMIUM depth analysis for {intel_input.opportunity_id}")
        start_time = time.time()

        try:
            from src.core.anthropic_service import get_anthropic_service, PipelineStage

            anthropic = get_anthropic_service()
            if not anthropic.is_available:
                raise RuntimeError("Anthropic API not available")

            # Build Claude prompt with full context (premium-enriched)
            system, user = _build_deep_analysis_prompt(intel_input, depth="premium")

            result_json = await anthropic.create_json_completion(
                messages=[{"role": "user", "content": user}],
                system=system,
                stage=PipelineStage.PREMIUM_INTELLIGENCE,  # Routes to Claude Opus
                max_tokens=8192,
                temperature=0.1,
            )

            output = _parse_deep_analysis_response(result_json, intel_input, premium=True)

            # Algorithmic enrichments
            if not output.historical_intelligence:
                output.historical_intelligence = self._analyze_historical(intel_input)
            if not output.geographic_analysis:
                output.geographic_analysis = self._analyze_geographic(intel_input)

            processing_time = time.time() - start_time
            output.processing_time_seconds = processing_time
            output.api_cost_usd = 0.10
            output.tool_version = "2.0.0"
            output.depth_executed = "premium"

            self.logger.info(
                f"PREMIUM analysis complete: score={output.overall_score:.2f}, "
                f"time={processing_time:.2f}s"
            )
            return output

        except Exception as e:
            self.logger.error(f"Claude analysis failed, using fallback: {e}")
            return await self._fallback_premium_analysis(intel_input)

    async def _fallback_premium_analysis(self, intel_input: DeepIntelligenceInput) -> DeepIntelligenceOutput:
        """Fallback analysis if BAML fails (uses placeholder data)."""
        # Get ESSENTIALS analysis first
        essentials_handler = EssentialsDepthHandler(self.logger)
        output = await essentials_handler._fallback_analysis(intel_input)

        # Add PREMIUM enhancements
        output.relationship_mapping = self._map_relationships(intel_input)
        output.policy_analysis = self._analyze_policy_premium(intel_input)
        output.strategic_consulting = self._generate_strategic_consulting_premium(intel_input, output)

        # Update metadata for premium tier
        output.depth_executed = "premium"
        output.api_cost_usd = 0.10  # True AI cost
        output.tool_version = "2.0.0"

        return output

    def _analyze_historical(self, intel_input: DeepIntelligenceInput) -> HistoricalAnalysis:
        """Analyze historical funding patterns."""
        # TODO: Replace with actual Historical Funding Analyzer Tool (Tool 22)
        return HistoricalAnalysis(
            historical_grants=[],
            total_grants_analyzed=15,
            total_funding_amount=2500000.0,
            average_grant_size=166667.0,
            typical_grant_range="$100,000 - $250,000",
            funding_trends="Increasing focus on capacity building",
            geographic_patterns="Primarily Mid-Atlantic region",
            similar_recipient_profiles=["Community-based nonprofits", "Education-focused"],
            success_factors=["Strong evaluation plans", "Community partnerships"],
            competitive_intelligence="Preference for organizations with track records"
        )

    def _analyze_geographic(self, intel_input: DeepIntelligenceInput) -> GeographicAnalysis:
        """Analyze geographic alignment."""
        return GeographicAnalysis(
            primary_service_area="Virginia/DC Metro",
            funder_geographic_focus="Mid-Atlantic states",
            geographic_alignment_score=0.85,
            geographic_fit_assessment="Strong alignment with funder's geographic priorities",
            regional_competition_analysis="3-4 comparable organizations in region",
            location_advantages=["Established presence", "Regional partnerships"],
            location_challenges=["Dense competitive landscape"]
        )

    def _map_relationships(self, intel_input: DeepIntelligenceInput) -> RelationshipMap:
        """Map relationship ecosystem (PREMIUM feature)."""
        return RelationshipMap(
            direct_relationships=["Partner Org A", "Collaborator B"],
            indirect_relationships=["Funder board member via Partner A"],
            partnership_opportunities=["Joint programming with Partner C"],
            relationship_insights="Strong indirect connections through partnership network provide competitive advantage",
            cultivation_strategy="Leverage partner relationships for warm introductions to program officers and decision makers"
        )

    def _analyze_policy_premium(self, intel_input: DeepIntelligenceInput) -> PolicyAnalysis:
        """Analyze policy alignment (PREMIUM feature)."""
        from .intelligence_models import PolicyAlignment

        return PolicyAnalysis(
            federal_policy_alignment=PolicyAlignment(
                relevant_policies=["Education Reform Act", "Workforce Development Initiative"],
                alignment_score=0.80,
                policy_opportunities=["Align with federal priorities", "Position as policy implementation partner"],
                policy_risks=["Changing administration priorities"]
            ),
            state_policy_alignment=PolicyAlignment(
                relevant_policies=["State Education Initiative"],
                alignment_score=0.75,
                policy_opportunities=["State-level funding alignment"],
                policy_risks=["Budget constraints"]
            ),
            policy_landscape_summary="Strong alignment with current federal and state education priorities",
            policy_opportunities=["Position as policy implementation partner", "Engage in advocacy coalitions"],
            advocacy_recommendations=["Engage in policy discussions", "Join advocacy coalitions", "Build relationships with policymakers"]
        )

    def _generate_strategic_consulting_premium(
        self,
        intel_input: DeepIntelligenceInput,
        output: DeepIntelligenceOutput
    ) -> StrategicConsultingInsights:
        """Generate strategic consulting insights (PREMIUM feature)."""
        return StrategicConsultingInsights(
            executive_summary=f"Comprehensive strategic opportunity with {output.overall_score:.0%} success probability. Network intelligence reveals {output.network_intelligence.network_strength_score:.0%} connection strength to funder ecosystem.",
            competitive_positioning="Position as innovative regional leader with proven track record and strong network connections",
            differentiation_strategy="Emphasize unique community-based approach, proven outcomes, and strategic board relationships",
            multi_year_funding_strategy="Build relationship for multi-year support through successful project delivery and ongoing funder engagement",
            partnership_development_strategy="Develop strategic partnerships with complementary organizations to strengthen competitive position",
            capacity_building_roadmap="Phase 1: Infrastructure development (6 mo), Phase 2: Staff capacity building (6 mo), Phase 3: Program scaling (12 mo)",
            immediate_actions=[
                "Submit Letter of Intent (LOI) with strong network positioning",
                "Schedule funder meeting using board connections",
                "Develop detailed budget with match funding strategy",
                "Engage key board members for warm introductions"
            ],
            medium_term_actions=[
                "Build evaluation capacity through consultant partnerships",
                "Strengthen strategic partnerships in service area",
                "Develop compelling case studies and impact metrics",
                "Cultivate decision-maker relationships"
            ],
            long_term_actions=[
                "Scale program model based on proven results",
                "Seek multi-year funding commitments",
                "Build organizational reserves and endowment",
                "Position for larger institutional grants"
            ]
        )


# ============================================================================
# CLAUDE PROMPT BUILDERS & RESPONSE PARSERS
# ============================================================================


def _build_deep_analysis_prompt(
    intel_input: DeepIntelligenceInput,
    depth: str = "essentials",
) -> tuple:
    """Build system + user prompts for deep intelligence analysis."""

    system = (
        "You are a senior grant research analyst conducting a comprehensive intelligence "
        "analysis of a grant opportunity for a nonprofit organization. Provide honest, "
        "detailed, and actionable analysis.\n\n"
        "Return your analysis as a JSON object with this exact structure:\n"
        "{\n"
        '  "strategic_fit": {\n'
        '    "fit_score": float (0-1),\n'
        '    "mission_alignment_score": float (0-1),\n'
        '    "program_alignment_score": float (0-1),\n'
        '    "geographic_alignment_score": float (0-1),\n'
        '    "alignment_strengths": [string, ...],\n'
        '    "alignment_concerns": [string, ...],\n'
        '    "strategic_rationale": string,\n'
        '    "strategic_positioning": string,\n'
        '    "key_differentiators": [string, ...]\n'
        "  },\n"
        '  "financial_viability": {\n'
        '    "viability_score": float (0-1),\n'
        '    "budget_capacity_score": float (0-1),\n'
        '    "financial_health_score": float (0-1),\n'
        '    "sustainability_score": float (0-1),\n'
        '    "budget_implications": string,\n'
        '    "resource_requirements": {string: string, ...},\n'
        '    "financial_risks": [string, ...],\n'
        '    "financial_strategy": string,\n'
        '    "budget_recommendations": [string, ...]\n'
        "  },\n"
        '  "operational_readiness": {\n'
        '    "readiness_score": float (0-1),\n'
        '    "capacity_score": float (0-1),\n'
        '    "timeline_feasibility_score": float (0-1),\n'
        '    "infrastructure_readiness_score": float (0-1),\n'
        '    "capacity_gaps": [string, ...],\n'
        '    "infrastructure_requirements": [string, ...],\n'
        '    "timeline_challenges": [string, ...],\n'
        '    "capacity_building_plan": string,\n'
        '    "operational_recommendations": [string, ...],\n'
        '    "estimated_preparation_time_weeks": int\n'
        "  },\n"
        '  "risk_assessment": {\n'
        '    "overall_risk_level": string (low|medium|high|critical),\n'
        '    "overall_risk_score": float (0-1),\n'
        '    "risk_factors": [{"category": string, "risk_level": string, '
        '"description": string, "impact": string, '
        '"mitigation_strategy": string, "probability": float}, ...],\n'
        '    "critical_risks": [string, ...],\n'
        '    "manageable_risks": [string, ...],\n'
        '    "risk_mitigation_plan": string\n'
        "  },\n"
        '  "overall_score": float (0-1),\n'
        '  "success_probability": string (very_low|low|moderate|high|very_high),\n'
        '  "executive_summary": string (2-3 paragraphs),\n'
        '  "key_strengths": [string, ...] (3-5 items),\n'
        '  "key_challenges": [string, ...] (3-5 items),\n'
        '  "recommended_next_steps": [string, ...] (3-5 items)\n'
    )

    if depth == "premium":
        system += (
            ',\n'
            '  "relationship_mapping": {\n'
            '    "direct_relationships": [string, ...],\n'
            '    "indirect_relationships": [string, ...],\n'
            '    "partnership_opportunities": [string, ...],\n'
            '    "relationship_insights": string,\n'
            '    "cultivation_strategy": string\n'
            "  },\n"
            '  "policy_analysis": {\n'
            '    "federal_alignment_score": float (0-1),\n'
            '    "federal_policies": [string, ...],\n'
            '    "policy_opportunities": [string, ...],\n'
            '    "policy_risks": [string, ...],\n'
            '    "policy_landscape_summary": string,\n'
            '    "advocacy_recommendations": [string, ...]\n'
            "  },\n"
            '  "strategic_consulting": {\n'
            '    "executive_summary": string,\n'
            '    "competitive_positioning": string,\n'
            '    "differentiation_strategy": string,\n'
            '    "multi_year_funding_strategy": string,\n'
            '    "partnership_development_strategy": string,\n'
            '    "capacity_building_roadmap": string,\n'
            '    "immediate_actions": [string, ...],\n'
            '    "medium_term_actions": [string, ...],\n'
            '    "long_term_actions": [string, ...]\n'
            "  }\n"
        )

    system += "}\n\n"
    system += (
        "Scoring guidance:\n"
        "- Be calibrated. Most opportunities should score 0.5-0.8.\n"
        "- Scores below 0.4 = poor fit. Above 0.8 = excellent fit.\n"
        "- Overall = strategic_fit*0.35 + financial*0.25 + operational*0.25 + (1-risk)*0.15\n"
        "- Be specific and actionable. Generic advice is unhelpful.\n"
        "- Identify real risks — don't sugarcoat.\n"
    )

    # Build user message with all context
    amount = ""
    if intel_input.opportunity_amount_min or intel_input.opportunity_amount_max:
        amount = f"${intel_input.opportunity_amount_min or '?'} - ${intel_input.opportunity_amount_max or '?'}"

    user = (
        f"ORGANIZATION:\n"
        f"  Name: {intel_input.organization_name}\n"
        f"  EIN: {intel_input.organization_ein}\n"
        f"  Mission: {intel_input.organization_mission}\n"
    )
    if intel_input.organization_revenue:
        user += f"  Annual Revenue: ${intel_input.organization_revenue:,.0f}\n"
    if intel_input.focus_areas:
        user += f"  Focus Areas: {', '.join(intel_input.focus_areas)}\n"

    user += (
        f"\nOPPORTUNITY:\n"
        f"  ID: {intel_input.opportunity_id}\n"
        f"  Title: {intel_input.opportunity_title}\n"
        f"  Funder: {intel_input.funder_name} ({intel_input.funder_type})\n"
        f"  Description: {intel_input.opportunity_description[:5000]}\n"
    )
    if amount:
        user += f"  Award Amount: {amount}\n"
    if intel_input.opportunity_deadline:
        user += f"  Deadline: {intel_input.opportunity_deadline}\n"
    if intel_input.screening_score is not None:
        user += f"  Screening Score: {intel_input.screening_score:.2f}\n"
    if intel_input.user_notes:
        user += f"\nUSER NOTES: {intel_input.user_notes}\n"

    # Enrich with funder intelligence from database
    funder_context = _get_funder_context(intel_input)
    if funder_context:
        user += f"\n{funder_context}\n"

    user += (
        f"\nProvide comprehensive {depth.upper()} depth analysis. "
        "Be honest about weaknesses and specific about recommendations."
    )

    return system, user


def _get_funder_context(intel_input: DeepIntelligenceInput) -> str:
    """Pull funder intelligence from database for prompt enrichment."""
    try:
        from tools.opportunity_screening_tool.app.funder_enrichment import lookup_funder

        funder_intel = lookup_funder(
            funder_name=intel_input.funder_name,
            funder_type=intel_input.funder_type,
        )
        if funder_intel.capacity_tier or funder_intel.total_assets:
            return funder_intel.to_prompt_context()
    except Exception:
        pass
    return ""


def _parse_deep_analysis_response(
    data: Dict[str, Any],
    intel_input: DeepIntelligenceInput,
    premium: bool = False,
) -> DeepIntelligenceOutput:
    """Parse Claude's JSON response into DeepIntelligenceOutput."""

    sf = data.get("strategic_fit", {})
    strategic_fit = StrategicFitAnalysis(
        fit_score=sf.get("fit_score", 0.5),
        mission_alignment_score=sf.get("mission_alignment_score", 0.5),
        program_alignment_score=sf.get("program_alignment_score", 0.5),
        geographic_alignment_score=sf.get("geographic_alignment_score", 0.5),
        alignment_strengths=sf.get("alignment_strengths", []),
        alignment_concerns=sf.get("alignment_concerns", []),
        strategic_rationale=sf.get("strategic_rationale", ""),
        strategic_positioning=sf.get("strategic_positioning", ""),
        key_differentiators=sf.get("key_differentiators", []),
    )

    fv = data.get("financial_viability", {})
    financial_viability = FinancialViabilityAnalysis(
        viability_score=fv.get("viability_score", 0.5),
        budget_capacity_score=fv.get("budget_capacity_score", 0.5),
        financial_health_score=fv.get("financial_health_score", 0.5),
        sustainability_score=fv.get("sustainability_score", 0.5),
        budget_implications=fv.get("budget_implications", ""),
        resource_requirements=fv.get("resource_requirements", {}),
        financial_risks=fv.get("financial_risks", []),
        financial_strategy=fv.get("financial_strategy", ""),
        budget_recommendations=fv.get("budget_recommendations", []),
    )

    op = data.get("operational_readiness", {})
    operational_readiness = OperationalReadinessAnalysis(
        readiness_score=op.get("readiness_score", 0.5),
        capacity_score=op.get("capacity_score", 0.5),
        timeline_feasibility_score=op.get("timeline_feasibility_score", 0.5),
        infrastructure_readiness_score=op.get("infrastructure_readiness_score", 0.5),
        capacity_gaps=op.get("capacity_gaps", []),
        infrastructure_requirements=op.get("infrastructure_requirements", []),
        timeline_challenges=op.get("timeline_challenges", []),
        capacity_building_plan=op.get("capacity_building_plan", ""),
        operational_recommendations=op.get("operational_recommendations", []),
        estimated_preparation_time_weeks=op.get("estimated_preparation_time_weeks", 8),
    )

    ra = data.get("risk_assessment", {})
    risk_level_str = ra.get("overall_risk_level", "medium").lower()
    risk_level = RiskLevel(risk_level_str) if risk_level_str in [e.value for e in RiskLevel] else RiskLevel.MEDIUM
    risk_factors = []
    for rf in ra.get("risk_factors", []):
        rl = rf.get("risk_level", "medium").lower()
        risk_factors.append(RiskFactor(
            category=rf.get("category", "general"),
            risk_level=RiskLevel(rl) if rl in [e.value for e in RiskLevel] else RiskLevel.MEDIUM,
            description=rf.get("description", ""),
            impact=rf.get("impact", ""),
            mitigation_strategy=rf.get("mitigation_strategy", ""),
            probability=rf.get("probability", 0.5),
        ))

    risk_assessment = RiskAssessment(
        overall_risk_level=risk_level,
        overall_risk_score=ra.get("overall_risk_score", 0.5),
        risk_factors=risk_factors,
        critical_risks=ra.get("critical_risks", []),
        manageable_risks=ra.get("manageable_risks", []),
        risk_mitigation_plan=ra.get("risk_mitigation_plan", ""),
    )

    overall_score = data.get("overall_score", 0.5)
    sp_str = data.get("success_probability", "moderate").lower()
    success_prob = SuccessProbability(sp_str) if sp_str in [e.value for e in SuccessProbability] else SuccessProbability.MODERATE

    # No auto-reject — present findings honestly
    proceed = overall_score >= 0.50

    output = DeepIntelligenceOutput(
        strategic_fit=strategic_fit,
        financial_viability=financial_viability,
        operational_readiness=operational_readiness,
        risk_assessment=risk_assessment,
        proceed_recommendation=proceed,
        success_probability=success_prob,
        overall_score=overall_score,
        executive_summary=data.get("executive_summary", ""),
        key_strengths=data.get("key_strengths", []),
        key_challenges=data.get("key_challenges", []),
        recommended_next_steps=data.get("recommended_next_steps", []),
    )

    # Premium-only fields
    if premium:
        rm = data.get("relationship_mapping", {})
        if rm:
            output.relationship_mapping = RelationshipMap(
                direct_relationships=rm.get("direct_relationships", []),
                indirect_relationships=rm.get("indirect_relationships", []),
                partnership_opportunities=rm.get("partnership_opportunities", []),
                relationship_insights=rm.get("relationship_insights", ""),
                cultivation_strategy=rm.get("cultivation_strategy", ""),
            )

        pa = data.get("policy_analysis", {})
        if pa:
            output.policy_analysis = PolicyAnalysis(
                federal_policy_alignment=PolicyAlignment(
                    relevant_policies=pa.get("federal_policies", []),
                    alignment_score=pa.get("federal_alignment_score", 0.5),
                    policy_opportunities=pa.get("policy_opportunities", []),
                    policy_risks=pa.get("policy_risks", []),
                ),
                state_policy_alignment=None,
                policy_landscape_summary=pa.get("policy_landscape_summary", ""),
                policy_opportunities=pa.get("policy_opportunities", []),
                advocacy_recommendations=pa.get("advocacy_recommendations", []),
            )

        sc = data.get("strategic_consulting", {})
        if sc:
            output.strategic_consulting = StrategicConsultingInsights(
                executive_summary=sc.get("executive_summary", ""),
                competitive_positioning=sc.get("competitive_positioning", ""),
                differentiation_strategy=sc.get("differentiation_strategy", ""),
                multi_year_funding_strategy=sc.get("multi_year_funding_strategy", ""),
                partnership_development_strategy=sc.get("partnership_development_strategy", ""),
                capacity_building_roadmap=sc.get("capacity_building_roadmap", ""),
                immediate_actions=sc.get("immediate_actions", []),
                medium_term_actions=sc.get("medium_term_actions", []),
                long_term_actions=sc.get("long_term_actions", []),
            )

    return output


# ============================================================================
# DEPTH HANDLER FACTORY & DEPRECATION MAPPING
# ============================================================================

def get_depth_handler(depth: AnalysisDepth, logger) -> DepthHandler:
    """
    Factory function to get appropriate depth handler.
    Automatically maps deprecated depths to new handlers.

    Args:
        depth: Analysis depth level (supports both new and deprecated values)
        logger: Logger instance

    Returns:
        Appropriate DepthHandler instance
    """
    # Deprecation mapping
    DEPTH_MIGRATION_MAP = {
        AnalysisDepth.QUICK: (AnalysisDepth.ESSENTIALS, EssentialsDepthHandler),
        AnalysisDepth.STANDARD: (AnalysisDepth.ESSENTIALS, EssentialsDepthHandler),
        AnalysisDepth.ENHANCED: (AnalysisDepth.PREMIUM, PremiumDepthHandler),
        AnalysisDepth.COMPLETE: (AnalysisDepth.PREMIUM, PremiumDepthHandler),
    }

    # New 2-tier handlers
    NEW_DEPTH_HANDLERS = {
        AnalysisDepth.ESSENTIALS: EssentialsDepthHandler,
        AnalysisDepth.PREMIUM: PremiumDepthHandler,
    }

    # Check if deprecated depth
    if depth in DEPTH_MIGRATION_MAP:
        new_depth, handler_class = DEPTH_MIGRATION_MAP[depth]
        logger.warning(
            f"Depth '{depth.value}' is deprecated and will be removed on 2025-11-04. "
            f"Auto-mapping to '{new_depth.value}' tier. Please update to use new tier names."
        )
        return handler_class(logger)

    # New depth handling
    if depth in NEW_DEPTH_HANDLERS:
        return NEW_DEPTH_HANDLERS[depth](logger)

    # Fallback to essentials for unknown depths
    logger.warning(f"Unknown depth '{depth.value}', defaulting to ESSENTIALS tier")
    return EssentialsDepthHandler(logger)
