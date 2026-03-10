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

    # Inject SCREENING pipeline intelligence (web data, 990 extraction, screen scores)
    screening_section = _build_screening_context_section(intel_input.screening_context)
    if screening_section:
        user += screening_section

    user += (
        f"\nProvide comprehensive {depth.upper()} depth analysis. "
        "Be honest about weaknesses and specific about recommendations. "
        "Use the Screening Pipeline Intelligence above (if present) to calibrate your "
        "scores and surface funder-specific insights the AI already discovered."
    )

    return system, user


def _build_screening_context_section(screening_context: Dict[str, Any]) -> str:
    """
    Format SCREENING pipeline intelligence into a prompt section for Claude.
    Extracts key funder data from web_data, pdf_extraction, and screen scores.
    """
    if not screening_context:
        return ""

    lines = ["\n--- SCREENING PIPELINE INTELLIGENCE (use to calibrate analysis) ---"]

    # Web intelligence (from ② Search Website)
    web_data = screening_context.get("web_data") or {}
    gfi = web_data.get("grant_funder_intelligence") or {}
    if gfi:
        lines.append("\nWebsite Intelligence (Haiku agent, ~$0.008):")
        if gfi.get("funder_priorities"):
            priorities = gfi["funder_priorities"]
            if isinstance(priorities, list):
                priorities = "; ".join(str(p) for p in priorities[:5])
            lines.append(f"  Funder Priorities: {priorities}")
        if gfi.get("mission_statement"):
            lines.append(f"  Mission: {str(gfi['mission_statement'])[:300]}")
        if gfi.get("typical_grant_size_min") or gfi.get("typical_grant_size_max"):
            lines.append(
                f"  Typical Grant Size: ${gfi.get('typical_grant_size_min', '?')} – "
                f"${gfi.get('typical_grant_size_max', '?')}"
            )
        if gfi.get("application_status"):
            lines.append(f"  Application Status: {gfi['application_status']}")
        if gfi.get("geographic_limitations"):
            geo = gfi["geographic_limitations"]
            if isinstance(geo, list):
                geo = ", ".join(str(g) for g in geo[:5])
            lines.append(f"  Geographic Focus: {geo}")
        if gfi.get("key_program_areas"):
            areas = gfi["key_program_areas"]
            if isinstance(areas, list):
                areas = ", ".join(str(a) for a in areas[:5])
            lines.append(f"  Program Areas: {areas}")

    # 990 PDF extraction (from ③ Search 990s)
    pdf = screening_context.get("pdf_extraction") or {}
    if pdf:
        lines.append("\n990 PDF Extraction (Claude Haiku, ~$0.01):")
        if pdf.get("stated_priorities"):
            lines.append(f"  Stated Priorities: {str(pdf['stated_priorities'])[:400]}")
        if pdf.get("geographic_limitations"):
            lines.append(f"  Geographic Limitations: {str(pdf['geographic_limitations'])[:200]}")
        if pdf.get("grant_size_min") or pdf.get("grant_size_max"):
            lines.append(
                f"  Grant Size Range: ${pdf.get('grant_size_min', '?')} – "
                f"${pdf.get('grant_size_max', '?')}"
            )
        if pdf.get("program_areas"):
            areas = pdf["program_areas"]
            if isinstance(areas, list):
                areas = ", ".join(str(a) for a in areas[:5])
            lines.append(f"  Program Areas: {areas}")
        if pdf.get("leadership_names"):
            names = pdf["leadership_names"]
            if isinstance(names, list):
                names = ", ".join(str(n) for n in names[:5])
            lines.append(f"  Leadership: {names}")

    # Fast screen result (from ④ Screen Fast)
    fast = screening_context.get("fast_screen") or {}
    if fast:
        score = fast.get("overall_score")
        summary = fast.get("one_sentence_summary") or fast.get("summary", "")
        strengths = fast.get("strengths") or fast.get("key_strengths", [])
        concerns = fast.get("concerns") or fast.get("key_concerns", [])
        lines.append(f"\nFast Screen Score (Claude Haiku): {f'{score:.0%}' if score else 'N/A'}")
        if summary:
            lines.append(f"  Summary: {str(summary)[:300]}")
        if strengths:
            if isinstance(strengths, list):
                strengths = "; ".join(str(s) for s in strengths[:3])
            lines.append(f"  Strengths: {strengths}")
        if concerns:
            if isinstance(concerns, list):
                concerns = "; ".join(str(c) for c in concerns[:3])
            lines.append(f"  Concerns: {concerns}")

    # Thorough screen result (from ⑤ Screen Thorough)
    thorough = screening_context.get("thorough_screen") or {}
    if thorough:
        score = thorough.get("overall_score")
        summary = thorough.get("one_sentence_summary") or thorough.get("summary", "")
        strengths = thorough.get("strengths") or thorough.get("key_strengths", [])
        concerns = thorough.get("concerns") or thorough.get("key_concerns", [])
        lines.append(f"\nThorough Screen Score (Claude Sonnet): {f'{score:.0%}' if score else 'N/A'}")
        if summary:
            lines.append(f"  Summary: {str(summary)[:400]}")
        if strengths:
            if isinstance(strengths, list):
                strengths = "; ".join(str(s) for s in strengths[:4])
            lines.append(f"  Strengths: {strengths}")
        if concerns:
            if isinstance(concerns, list):
                concerns = "; ".join(str(c) for c in concerns[:4])
            lines.append(f"  Concerns: {concerns}")

    # Initial algorithmic score
    init = screening_context.get("initial_score") or {}
    if init and init.get("overall_score") is not None:
        lines.append(f"\nInitial Screen Score: {init['overall_score']:.0%}")
        if init.get("one_sentence_summary"):
            lines.append(f"  Summary: {init['one_sentence_summary'][:200]}")

    if len(lines) == 1:
        return ""  # Only header, nothing useful

    lines.append("--- END SCREENING INTELLIGENCE ---")
    return "\n".join(lines)


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
# PREMIUM UPGRADE HANDLER (skip re-running Essentials when already complete)
# ============================================================================


class PremiumUpgradeHandler(DepthHandler):
    """
    PREMIUM Upgrade Handler — skips Essentials re-run when already completed.

    When the frontend passes an existing Essentials result, this handler:
    1. Calls Claude with a premium-only prompt (relationship mapping, policy
       analysis, strategic consulting) — NOT re-running the 4 core stages.
    2. Merges the 3 Premium-only sections into the existing Essentials output.
    3. Returns a full DeepIntelligenceOutput with depth_executed = "premium".

    AI cost: ~$0.05 incremental (premium-only call) vs $0.10 for full Premium.
    User saves: avoids paying twice for core analysis already completed.
    """

    async def analyze(
        self,
        intel_input: DeepIntelligenceInput,
        existing_essentials: Dict[str, Any],
    ) -> DeepIntelligenceOutput:
        """Execute premium-only upgrade using the existing Essentials result."""
        self.logger.info(
            f"[PREMIUM UPGRADE] Starting upgrade for {intel_input.opportunity_id} "
            f"(reusing existing Essentials result, skipping core stages)"
        )
        start_time = time.time()

        try:
            from src.core.anthropic_service import get_anthropic_service, PipelineStage

            anthropic = get_anthropic_service()
            if not anthropic.is_available:
                raise RuntimeError("Anthropic API not available")

            system, user = _build_premium_only_prompt(intel_input, existing_essentials)

            result_json = await anthropic.create_json_completion(
                messages=[{"role": "user", "content": user}],
                system=system,
                stage=PipelineStage.PREMIUM_INTELLIGENCE,
                max_tokens=4096,
                temperature=0.1,
            )

            output = _reconstruct_from_essentials(existing_essentials, intel_input)
            _apply_premium_only_fields(output, result_json)

        except Exception as e:
            self.logger.error(
                f"[PREMIUM UPGRADE] Claude call failed, using fallback: {e}"
            )
            output = _reconstruct_from_essentials(existing_essentials, intel_input)
            _apply_premium_only_fallback(output, intel_input)

        processing_time = time.time() - start_time
        output.depth_executed = "premium"
        output.processing_time_seconds = processing_time
        output.api_cost_usd = 0.05  # incremental cost only
        output.tool_version = "2.0.0"

        self.logger.info(
            f"[PREMIUM UPGRADE] Complete for {intel_input.opportunity_id} "
            f"in {processing_time:.2f}s (incremental AI cost: $0.05)"
        )
        return output


def _build_premium_only_prompt(
    intel_input: DeepIntelligenceInput,
    existing_essentials: Dict[str, Any],
) -> tuple:
    """Build prompt that focuses ONLY on the 3 Premium-specific sections."""

    system = (
        "You are a senior grant research analyst. The client has already completed "
        "ESSENTIALS analysis (strategic fit, financial viability, operational readiness, "
        "risk assessment) for this grant opportunity. Those results are provided below.\n\n"
        "DO NOT re-run or repeat the core Essentials analysis. ONLY produce the 3 "
        "Premium-specific analyses:\n\n"
        "Return a JSON object with EXACTLY these three keys:\n"
        "{\n"
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
        "}\n\n"
        "Be specific, actionable, and build on the existing Essentials findings "
        "provided in the context below."
    )

    # Summarise existing Essentials data for context
    exec_summary = existing_essentials.get("executive_summary", "")
    key_strengths = existing_essentials.get("key_strengths", [])
    key_challenges = existing_essentials.get("key_challenges", [])
    overall_score = existing_essentials.get("overall_score", "N/A")
    success_prob = existing_essentials.get("success_probability", "N/A")

    sf = existing_essentials.get("strategic_fit", {})
    fv = existing_essentials.get("financial_viability", {})
    op = existing_essentials.get("operational_readiness", {})
    ra = existing_essentials.get("risk_assessment", {})
    ni = existing_essentials.get("network_intelligence", {})

    amount = ""
    if intel_input.opportunity_amount_min or intel_input.opportunity_amount_max:
        amount = f"${intel_input.opportunity_amount_min or '?'} – ${intel_input.opportunity_amount_max or '?'}"

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
        f"  Description: {intel_input.opportunity_description[:3000]}\n"
    )
    if amount:
        user += f"  Award Amount: {amount}\n"
    if intel_input.opportunity_deadline:
        user += f"  Deadline: {intel_input.opportunity_deadline}\n"

    user += (
        f"\n--- EXISTING ESSENTIALS ANALYSIS (DO NOT REPEAT) ---\n"
        f"Overall Score: {overall_score}\n"
        f"Success Probability: {success_prob}\n"
        f"Executive Summary: {exec_summary[:1500]}\n"
        f"Key Strengths: {', '.join(key_strengths)}\n"
        f"Key Challenges: {', '.join(key_challenges)}\n"
        f"Strategic Fit Score: {sf.get('fit_score', 'N/A')} — "
        f"Rationale: {sf.get('strategic_rationale', '')[:300]}\n"
        f"Financial Viability Score: {fv.get('viability_score', 'N/A')} — "
        f"Strategy: {fv.get('financial_strategy', '')[:200]}\n"
        f"Operational Readiness Score: {op.get('readiness_score', 'N/A')} — "
        f"Gaps: {', '.join(op.get('capacity_gaps', []))}\n"
        f"Risk Level: {ra.get('overall_risk_level', 'N/A')} — "
        f"Mitigation: {ra.get('risk_mitigation_plan', '')[:200]}\n"
    )
    if ni:
        user += (
            f"Network Strength Score: {ni.get('network_strength_score', 'N/A')}\n"
            f"Relationship Advantages: {', '.join(ni.get('relationship_advantages', []))}\n"
        )

    # Enrich with funder intelligence from database
    funder_context = _get_funder_context(intel_input)
    if funder_context:
        user += f"\n{funder_context}\n"

    # Inject SCREENING pipeline intelligence for additional context
    screening_section = _build_screening_context_section(intel_input.screening_context)
    if screening_section:
        user += screening_section

    user += (
        "\n--- YOUR TASK ---\n"
        "Using the Essentials findings above as context, produce ONLY the three "
        "Premium-specific analyses: relationship_mapping, policy_analysis, and "
        "strategic_consulting. Do not produce any other JSON keys. "
        "Use the Screening Pipeline Intelligence (if present) to add funder-specific depth."
    )

    return system, user


def _reconstruct_from_essentials(
    existing: Dict[str, Any],
    intel_input: DeepIntelligenceInput,
) -> DeepIntelligenceOutput:
    """
    Re-hydrate a DeepIntelligenceOutput from a stored Essentials dict.
    This avoids re-calling the AI for the core 4 stages.
    """
    sf_d = existing.get("strategic_fit", {})
    strategic_fit = StrategicFitAnalysis(
        fit_score=sf_d.get("fit_score", 0.5),
        mission_alignment_score=sf_d.get("mission_alignment_score", 0.5),
        program_alignment_score=sf_d.get("program_alignment_score", 0.5),
        geographic_alignment_score=sf_d.get("geographic_alignment_score", 0.5),
        alignment_strengths=sf_d.get("alignment_strengths", []),
        alignment_concerns=sf_d.get("alignment_concerns", []),
        strategic_rationale=sf_d.get("strategic_rationale", ""),
        strategic_positioning=sf_d.get("strategic_positioning", ""),
        key_differentiators=sf_d.get("key_differentiators", []),
    )

    fv_d = existing.get("financial_viability", {})
    financial_viability = FinancialViabilityAnalysis(
        viability_score=fv_d.get("viability_score", 0.5),
        budget_capacity_score=fv_d.get("budget_capacity_score", 0.5),
        financial_health_score=fv_d.get("financial_health_score", 0.5),
        sustainability_score=fv_d.get("sustainability_score", 0.5),
        budget_implications=fv_d.get("budget_implications", ""),
        resource_requirements=fv_d.get("resource_requirements", {}),
        financial_risks=fv_d.get("financial_risks", []),
        financial_strategy=fv_d.get("financial_strategy", ""),
        budget_recommendations=fv_d.get("budget_recommendations", []),
    )

    op_d = existing.get("operational_readiness", {})
    operational_readiness = OperationalReadinessAnalysis(
        readiness_score=op_d.get("readiness_score", 0.5),
        capacity_score=op_d.get("capacity_score", 0.5),
        timeline_feasibility_score=op_d.get("timeline_feasibility_score", 0.5),
        infrastructure_readiness_score=op_d.get("infrastructure_readiness_score", 0.5),
        capacity_gaps=op_d.get("capacity_gaps", []),
        infrastructure_requirements=op_d.get("infrastructure_requirements", []),
        timeline_challenges=op_d.get("timeline_challenges", []),
        capacity_building_plan=op_d.get("capacity_building_plan", ""),
        operational_recommendations=op_d.get("operational_recommendations", []),
        estimated_preparation_time_weeks=op_d.get("estimated_preparation_time_weeks", 8),
    )

    ra_d = existing.get("risk_assessment", {})
    risk_level_str = ra_d.get("overall_risk_level", "medium").lower()
    risk_level = (
        RiskLevel(risk_level_str)
        if risk_level_str in [e.value for e in RiskLevel]
        else RiskLevel.MEDIUM
    )
    risk_factors = []
    for rf in ra_d.get("risk_factors", []):
        rl = rf.get("risk_level", "medium").lower()
        risk_factors.append(
            RiskFactor(
                category=rf.get("category", "general"),
                risk_level=RiskLevel(rl) if rl in [e.value for e in RiskLevel] else RiskLevel.MEDIUM,
                description=rf.get("description", ""),
                impact=rf.get("impact", ""),
                mitigation_strategy=rf.get("mitigation_strategy", ""),
                probability=rf.get("probability", 0.5),
            )
        )
    risk_assessment = RiskAssessment(
        overall_risk_level=risk_level,
        overall_risk_score=ra_d.get("overall_risk_score", 0.5),
        risk_factors=risk_factors,
        critical_risks=ra_d.get("critical_risks", []),
        manageable_risks=ra_d.get("manageable_risks", []),
        risk_mitigation_plan=ra_d.get("risk_mitigation_plan", ""),
    )

    overall_score = existing.get("overall_score", 0.5)
    sp_str = existing.get("success_probability", "moderate").lower()
    success_prob = (
        SuccessProbability(sp_str)
        if sp_str in [e.value for e in SuccessProbability]
        else SuccessProbability.MODERATE
    )

    output = DeepIntelligenceOutput(
        strategic_fit=strategic_fit,
        financial_viability=financial_viability,
        operational_readiness=operational_readiness,
        risk_assessment=risk_assessment,
        proceed_recommendation=existing.get("proceed_recommendation", overall_score >= 0.50),
        success_probability=success_prob,
        overall_score=overall_score,
        executive_summary=existing.get("executive_summary", ""),
        key_strengths=existing.get("key_strengths", []),
        key_challenges=existing.get("key_challenges", []),
        recommended_next_steps=existing.get("recommended_next_steps", []),
    )

    # Restore optional Essentials fields if present
    ni_d = existing.get("network_intelligence")
    if ni_d:
        output.network_intelligence = NetworkAnalysis(
            board_connections=ni_d.get("board_connections", []),
            network_connections=ni_d.get("network_connections", []),
            network_strength_score=ni_d.get("network_strength_score", 0.5),
            relationship_advantages=ni_d.get("relationship_advantages", []),
            relationship_leverage_strategy=ni_d.get("relationship_leverage_strategy", ""),
            key_contacts_to_cultivate=ni_d.get("key_contacts_to_cultivate", []),
        )

    hi_d = existing.get("historical_intelligence")
    if hi_d:
        output.historical_intelligence = HistoricalAnalysis(
            historical_grants=hi_d.get("historical_grants", []),
            total_grants_analyzed=hi_d.get("total_grants_analyzed", 0),
            total_funding_amount=hi_d.get("total_funding_amount", 0.0),
            average_grant_size=hi_d.get("average_grant_size", 0.0),
            typical_grant_range=hi_d.get("typical_grant_range", ""),
            funding_trends=hi_d.get("funding_trends", ""),
            geographic_patterns=hi_d.get("geographic_patterns", ""),
            similar_recipient_profiles=hi_d.get("similar_recipient_profiles", []),
            success_factors=hi_d.get("success_factors", []),
            competitive_intelligence=hi_d.get("competitive_intelligence", ""),
        )

    ga_d = existing.get("geographic_analysis")
    if ga_d:
        output.geographic_analysis = GeographicAnalysis(
            primary_service_area=ga_d.get("primary_service_area", ""),
            funder_geographic_focus=ga_d.get("funder_geographic_focus", ""),
            geographic_alignment_score=ga_d.get("geographic_alignment_score", 0.5),
            geographic_fit_assessment=ga_d.get("geographic_fit_assessment", ""),
            regional_competition_analysis=ga_d.get("regional_competition_analysis", ""),
            location_advantages=ga_d.get("location_advantages", []),
            location_challenges=ga_d.get("location_challenges", []),
        )

    return output


def _apply_premium_only_fields(output: DeepIntelligenceOutput, data: Dict[str, Any]) -> None:
    """Overlay the 3 Premium-only fields onto a reconstructed output object."""
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


def _apply_premium_only_fallback(
    output: DeepIntelligenceOutput,
    intel_input: DeepIntelligenceInput,
) -> None:
    """Apply placeholder Premium-only fields when the AI call fails."""
    output.relationship_mapping = RelationshipMap(
        direct_relationships=["Partner Org A", "Collaborator B"],
        indirect_relationships=["Funder board member via Partner A"],
        partnership_opportunities=["Joint programming with Partner C"],
        relationship_insights="Network analysis could not be completed. Manual relationship mapping recommended.",
        cultivation_strategy="Leverage existing partner relationships for warm introductions.",
    )
    output.policy_analysis = PolicyAnalysis(
        federal_policy_alignment=PolicyAlignment(
            relevant_policies=["Relevant federal program areas"],
            alignment_score=0.6,
            policy_opportunities=["Align with federal priorities"],
            policy_risks=["Policy environment uncertainty"],
        ),
        state_policy_alignment=None,
        policy_landscape_summary="Policy analysis could not be completed. Manual review recommended.",
        policy_opportunities=["Position as policy implementation partner"],
        advocacy_recommendations=["Engage in relevant policy discussions"],
    )
    output.strategic_consulting = StrategicConsultingInsights(
        executive_summary=f"Premium upgrade for {intel_input.opportunity_title}. "
                          "Core Essentials analysis preserved. Premium-specific "
                          "insights require manual review.",
        competitive_positioning="Emphasise unique organisational strengths.",
        differentiation_strategy="Highlight proven outcomes and community partnerships.",
        multi_year_funding_strategy="Build funder relationship through consistent delivery.",
        partnership_development_strategy="Develop complementary strategic partnerships.",
        capacity_building_roadmap="Phase 1: Infrastructure (6 mo), Phase 2: Staff (6 mo), Phase 3: Scale (12 mo)",
        immediate_actions=["Submit LOI", "Schedule funder meeting", "Develop detailed budget"],
        medium_term_actions=["Build evaluation capacity", "Strengthen partnerships"],
        long_term_actions=["Scale program model", "Seek multi-year funding"],
    )


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
