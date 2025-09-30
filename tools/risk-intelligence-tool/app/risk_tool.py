"""
Risk Intelligence Tool
12-Factor compliant tool for multi-dimensional risk assessment.

Purpose: Comprehensive risk analysis with mitigation strategies
Cost: $0.02 per analysis
Replaces: risk_assessor.py processor
"""

import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Optional
import time
from datetime import datetime, timedelta

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext
from .risk_models import (
    RiskIntelligenceInput,
    RiskIntelligenceOutput,
    RiskFactor,
    RiskLevel,
    RiskCategory,
    MitigationStrategy,
    MitigationPriority,
    EligibilityRiskAssessment,
    CompetitionRiskAssessment,
    CapacityRiskAssessment,
    TimelineRiskAssessment,
    FinancialRiskAssessment,
    ComplianceRiskAssessment,
    AIRiskInsights,
    RISK_INTELLIGENCE_COST
)


class RiskIntelligenceTool(BaseTool[RiskIntelligenceOutput]):
    """
    12-Factor Risk Intelligence Tool

    Factor 4: Returns structured RiskIntelligenceOutput
    Factor 6: Stateless - no persistence between runs
    Factor 10: Single responsibility - risk analysis only
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize risk intelligence tool."""
        super().__init__(config)
        self.openai_api_key = config.get("openai_api_key") if config else None

    def get_tool_name(self) -> str:
        return "Risk Intelligence Tool"

    def get_tool_version(self) -> str:
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        return "Multi-dimensional risk assessment with mitigation strategies for grant opportunities"

    async def _execute(
        self,
        context: ToolExecutionContext,
        risk_input: RiskIntelligenceInput
    ) -> RiskIntelligenceOutput:
        """Execute risk intelligence analysis."""
        start_time = time.time()

        self.logger.info(
            f"Starting risk intelligence analysis: {risk_input.opportunity_title} "
            f"for {risk_input.organization_name}"
        )

        # Dimensional risk assessments
        eligibility = self._assess_eligibility(risk_input)
        competition = self._assess_competition(risk_input)
        capacity = self._assess_capacity(risk_input)
        timeline = self._assess_timeline(risk_input)
        financial = self._assess_financial(risk_input)
        compliance = self._assess_compliance(risk_input)

        # Aggregate risk factors
        all_risks = self._aggregate_risk_factors(
            eligibility, competition, capacity, timeline, financial, compliance
        )

        # Categorize by severity
        critical_risks = [r for r in all_risks if r.risk_level == RiskLevel.CRITICAL]
        high_risks = [r for r in all_risks if r.risk_level == RiskLevel.HIGH]
        manageable_risks = [r for r in all_risks if r.risk_level in [RiskLevel.MEDIUM, RiskLevel.LOW, RiskLevel.MINIMAL]]

        # Overall risk assessment
        overall_risk_level, overall_risk_score = self._calculate_overall_risk(all_risks)

        # Mitigation strategies
        mitigation_strategies = self._generate_mitigation_strategies(all_risks)
        immediate_actions = [s.strategy for s in mitigation_strategies if s.priority == MitigationPriority.IMMEDIATE]

        # AI insights (placeholder)
        ai_insights = self._generate_ai_insights(
            risk_input, all_risks, critical_risks, high_risks, overall_risk_level
        )

        # Proceed recommendation
        proceed = self._calculate_proceed_recommendation(overall_risk_level, critical_risks, eligibility)

        # Risk summary
        risk_summary = self._generate_risk_summary(overall_risk_level, critical_risks, high_risks)
        key_factors = self._identify_key_decision_factors(all_risks)

        processing_time = time.time() - start_time

        output = RiskIntelligenceOutput(
            overall_risk_level=overall_risk_level,
            overall_risk_score=overall_risk_score,
            proceed_recommendation=proceed,
            all_risk_factors=all_risks,
            critical_risks=critical_risks,
            high_risks=high_risks,
            manageable_risks=manageable_risks,
            eligibility_assessment=eligibility,
            competition_assessment=competition,
            capacity_assessment=capacity,
            timeline_assessment=timeline,
            financial_assessment=financial,
            compliance_assessment=compliance,
            mitigation_strategies=mitigation_strategies,
            immediate_actions=immediate_actions,
            ai_insights=ai_insights,
            risk_summary=risk_summary,
            key_decision_factors=key_factors,
            analysis_date=datetime.now().isoformat(),
            confidence_level=0.85,
            processing_time_seconds=processing_time,
            api_cost_usd=RISK_INTELLIGENCE_COST
        )

        self.logger.info(
            f"Completed risk analysis: level={overall_risk_level.value}, "
            f"critical={len(critical_risks)}, high={len(high_risks)}, proceed={proceed}"
        )

        return output

    def _assess_eligibility(self, inp: RiskIntelligenceInput) -> EligibilityRiskAssessment:
        """Assess eligibility risks"""

        # Geographic eligibility
        geo_match = True
        geo_concerns = []
        if inp.geographic_restrictions:
            # Would check organization location against restrictions
            geo_concerns.append("Geographic restrictions require verification")

        # Type eligibility
        type_match = True
        type_concerns = []
        if inp.organization_type_requirements:
            type_concerns.append("Organization type requirements require verification")

        # Budget eligibility
        budget_match = True
        budget_concerns = []
        if inp.grant_amount and inp.total_revenue:
            if inp.grant_amount > inp.total_revenue:
                budget_match = False
                budget_concerns.append("Grant amount exceeds annual revenue - may indicate size mismatch")

        # Other requirements
        other_met = True
        other_concerns = []

        # Overall score
        score = sum([geo_match, type_match, budget_match, other_met]) / 4.0

        # Risk level
        if score >= 0.9:
            risk_level = RiskLevel.MINIMAL
        elif score >= 0.75:
            risk_level = RiskLevel.LOW
        elif score >= 0.5:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH

        proceed = score >= 0.75
        reasoning = f"Eligibility score {score:.0%}. " + (
            "Organization appears to meet eligibility requirements."
            if proceed else
            "Significant eligibility concerns identified requiring resolution."
        )

        return EligibilityRiskAssessment(
            overall_eligibility_score=score,
            risk_level=risk_level,
            geographic_match=geo_match,
            geographic_concerns=geo_concerns,
            type_match=type_match,
            type_concerns=type_concerns,
            budget_match=budget_match,
            budget_concerns=budget_concerns,
            other_requirements_met=other_met,
            other_concerns=other_concerns,
            proceed_recommendation=proceed,
            recommendation_reasoning=reasoning
        )

    def _assess_competition(self, inp: RiskIntelligenceInput) -> CompetitionRiskAssessment:
        """Assess competition risks"""

        # Estimate competition level
        if inp.funder_type == "foundation" and inp.prior_grants_with_funder and inp.prior_grants_with_funder > 0:
            competition_score = 0.4  # Lower competition with prior relationship
            competition_level = RiskLevel.MEDIUM
            applicant_pool = "20-40 applicants (estimated, foundation with prior relationship)"
        elif inp.funder_type == "government":
            competition_score = 0.7  # Higher competition for government
            competition_level = RiskLevel.HIGH
            applicant_pool = "100-200 applicants (estimated, government grant)"
        else:
            competition_score = 0.5
            competition_level = RiskLevel.MEDIUM
            applicant_pool = "50-100 applicants (estimated)"

        # Competitive strengths
        strengths = []
        if inp.prior_grants_with_funder and inp.prior_grants_with_funder > 0:
            strengths.append(f"Prior relationship with funder ({inp.prior_grants_with_funder} grants)")
        if inp.program_expense_ratio and inp.program_expense_ratio > 0.75:
            strengths.append("Strong program efficiency ratio")
        if inp.years_of_operation and inp.years_of_operation > 10:
            strengths.append("Established organization with track record")

        # Competitive weaknesses
        weaknesses = []
        if not inp.has_grant_manager:
            weaknesses.append("No dedicated grant manager")
        if inp.years_of_operation and inp.years_of_operation < 3:
            weaknesses.append("Limited organizational track record")

        # Success probability
        if inp.typical_award_rate:
            success_prob = inp.typical_award_rate * (1.2 if strengths else 0.9)
        else:
            success_prob = 0.15 if not strengths else 0.25

        success_prob = min(0.9, max(0.05, success_prob))

        reasoning = f"Estimated {success_prob:.0%} success probability based on competition level and organizational competitive position."

        return CompetitionRiskAssessment(
            competition_level=competition_level,
            estimated_competition_score=competition_score,
            estimated_applicant_pool=applicant_pool,
            typical_success_rate=inp.typical_award_rate,
            organization_competitive_position="Strong" if len(strengths) >= 2 else "Moderate" if strengths else "Weak",
            competitive_strengths=strengths,
            competitive_weaknesses=weaknesses,
            estimated_success_probability=success_prob,
            success_probability_reasoning=reasoning
        )

    def _assess_capacity(self, inp: RiskIntelligenceInput) -> CapacityRiskAssessment:
        """Assess organizational capacity risks"""

        staff_adequate = True
        staff_concerns = []
        if inp.staff_count is not None and inp.staff_count < 5:
            staff_adequate = False
            staff_concerns.append("Small staff size may limit project management capacity")

        infra_adequate = True
        infra_concerns = []

        mgmt_adequate = inp.has_grant_manager if inp.has_grant_manager is not None else True
        mgmt_concerns = [] if mgmt_adequate else ["No dedicated grant manager"]

        exp_adequate = (inp.prior_grants_with_funder or 0) > 0
        exp_concerns = [] if exp_adequate else ["No prior grants with this funder"]

        critical_gaps = []
        moderate_gaps = []

        if not mgmt_adequate:
            critical_gaps.append("Grant management capacity")
        if not staff_adequate:
            moderate_gaps.append("Staffing levels")

        score = sum([staff_adequate, infra_adequate, mgmt_adequate, exp_adequate]) / 4.0

        if score >= 0.8:
            risk_level = RiskLevel.LOW
        elif score >= 0.6:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH

        return CapacityRiskAssessment(
            capacity_risk_level=risk_level,
            overall_capacity_score=score,
            staff_capacity_adequate=staff_adequate,
            staff_concerns=staff_concerns,
            infrastructure_adequate=infra_adequate,
            infrastructure_concerns=infra_concerns,
            management_capacity_adequate=mgmt_adequate,
            management_concerns=mgmt_concerns,
            grant_experience_adequate=exp_adequate,
            experience_concerns=exp_concerns,
            critical_gaps=critical_gaps,
            moderate_gaps=moderate_gaps
        )

    def _assess_timeline(self, inp: RiskIntelligenceInput) -> TimelineRiskAssessment:
        """Assess timeline risks"""

        days_until_deadline = None
        if inp.application_deadline:
            try:
                deadline = datetime.fromisoformat(inp.application_deadline.replace('Z', '+00:00'))
                days_until_deadline = (deadline - datetime.now()).days
            except:
                pass

        # Estimate application time (4-6 weeks typical)
        app_time = 35

        timeline_adequate = True
        deadline_concerns = []

        if days_until_deadline is not None:
            if days_until_deadline < app_time:
                timeline_adequate = False
                deadline_concerns.append(f"Only {days_until_deadline} days until deadline, need ~{app_time} days")
            elif days_until_deadline < app_time + 14:
                deadline_concerns.append("Tight timeline - limited time for review and revision")

        project_feasible = True
        project_concerns = []
        if inp.project_duration_months and inp.project_duration_months > 36:
            project_concerns.append("Long project duration increases execution risk")

        score = 1.0
        if not timeline_adequate:
            score = 0.3
        elif deadline_concerns:
            score = 0.6

        risk_level = RiskLevel.LOW if score > 0.7 else RiskLevel.MEDIUM if score > 0.4 else RiskLevel.HIGH

        return TimelineRiskAssessment(
            timeline_risk_level=risk_level,
            timeline_feasibility_score=score,
            days_until_deadline=days_until_deadline,
            application_time_required=app_time,
            timeline_adequate=timeline_adequate,
            deadline_concerns=deadline_concerns,
            project_timeline_feasible=project_feasible,
            project_concerns=project_concerns,
            critical_milestones=[]
        )

    def _assess_financial(self, inp: RiskIntelligenceInput) -> FinancialRiskAssessment:
        """Assess financial risks"""

        can_manage = True
        budget_concerns = []

        if inp.grant_amount and inp.total_revenue:
            if inp.grant_amount > inp.total_revenue * 0.5:
                budget_concerns.append("Grant amount exceeds 50% of annual revenue - significant management challenge")

        can_match = True
        match_concerns = []

        if inp.match_required and inp.match_percentage:
            if inp.match_percentage > 25:
                match_concerns.append(f"High match requirement ({inp.match_percentage}%) may be challenging")
            if inp.net_assets:
                match_amount = (inp.grant_amount or 0) * (inp.match_percentage / 100)
                if match_amount > inp.net_assets * 0.3:
                    can_match = False
                    match_concerns.append("Match requirement exceeds 30% of net assets")

        cash_flow_adequate = True
        cash_concerns = []

        sustainability_concerns = []

        score = sum([can_manage, can_match, cash_flow_adequate]) / 3.0
        risk_level = RiskLevel.LOW if score > 0.8 else RiskLevel.MEDIUM if score > 0.5 else RiskLevel.HIGH

        return FinancialRiskAssessment(
            financial_risk_level=risk_level,
            financial_risk_score=1.0 - score,
            can_manage_budget=can_manage,
            budget_concerns=budget_concerns,
            can_provide_match=can_match,
            match_concerns=match_concerns,
            cash_flow_adequate=cash_flow_adequate,
            cash_flow_concerns=cash_concerns,
            sustainability_concerns=sustainability_concerns
        )

    def _assess_compliance(self, inp: RiskIntelligenceInput) -> ComplianceRiskAssessment:
        """Assess compliance risks"""

        # Placeholder compliance assessment
        reg_requirements = ["Federal regulations compliance"]
        reg_concerns = []

        reporting_requirements = ["Quarterly financial reports", "Annual performance reports"]
        reporting_concerns = []

        audit_requirements = []
        audit_concerns = []

        if inp.grant_amount and inp.grant_amount > 750000:
            audit_requirements.append("Single Audit required (OMB Uniform Guidance)")

        score = 0.8  # Assume low compliance risk unless specific concerns
        risk_level = RiskLevel.LOW

        return ComplianceRiskAssessment(
            compliance_risk_level=risk_level,
            compliance_risk_score=1.0 - score,
            regulatory_requirements=reg_requirements,
            regulatory_concerns=reg_concerns,
            reporting_requirements=reporting_requirements,
            reporting_concerns=reporting_concerns,
            audit_requirements=audit_requirements,
            audit_concerns=audit_concerns
        )

    def _aggregate_risk_factors(self, *assessments) -> list[RiskFactor]:
        """Aggregate risk factors from all assessments"""
        risks = []

        eligibility, competition, capacity, timeline, financial, compliance = assessments

        # Eligibility risks
        if eligibility.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            risks.append(RiskFactor(
                category=RiskCategory.ELIGIBILITY,
                risk_level=eligibility.risk_level,
                description="Eligibility concerns may disqualify application",
                likelihood=0.7,
                impact=1.0,
                risk_score=0.7,
                evidence=eligibility.geographic_concerns + eligibility.type_concerns + eligibility.budget_concerns
            ))

        # Competition risks
        if competition.competition_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            risks.append(RiskFactor(
                category=RiskCategory.COMPETITION,
                risk_level=competition.competition_level,
                description=f"High competition ({competition.estimated_applicant_pool})",
                likelihood=0.8,
                impact=0.6,
                risk_score=0.48,
                evidence=[f"Success probability: {competition.estimated_success_probability:.0%}"]
            ))

        # Capacity risks
        for gap in capacity.critical_gaps:
            risks.append(RiskFactor(
                category=RiskCategory.CAPACITY,
                risk_level=RiskLevel.HIGH,
                description=f"Critical capacity gap: {gap}",
                likelihood=0.9,
                impact=0.8,
                risk_score=0.72,
                evidence=capacity.management_concerns + capacity.staff_concerns
            ))

        # Timeline risks
        if not timeline.timeline_adequate:
            risks.append(RiskFactor(
                category=RiskCategory.TIMELINE,
                risk_level=RiskLevel.HIGH,
                description="Insufficient time to prepare quality application",
                likelihood=0.8,
                impact=0.7,
                risk_score=0.56,
                evidence=timeline.deadline_concerns
            ))

        # Financial risks
        if not financial.can_provide_match and financial.match_concerns:
            risks.append(RiskFactor(
                category=RiskCategory.FINANCIAL,
                risk_level=RiskLevel.HIGH,
                description="Cannot meet match requirement",
                likelihood=0.9,
                impact=0.9,
                risk_score=0.81,
                evidence=financial.match_concerns
            ))

        return risks

    def _calculate_overall_risk(self, risks: list[RiskFactor]) -> tuple[RiskLevel, float]:
        """Calculate overall risk level and score"""

        if not risks:
            return RiskLevel.LOW, 0.2

        # Weight by risk scores
        avg_score = sum(r.risk_score for r in risks) / len(risks)

        # Consider critical risks
        has_critical = any(r.risk_level == RiskLevel.CRITICAL for r in risks)
        has_high = any(r.risk_level == RiskLevel.HIGH for r in risks)

        if has_critical or avg_score > 0.7:
            level = RiskLevel.CRITICAL
        elif has_high or avg_score > 0.5:
            level = RiskLevel.HIGH
        elif avg_score > 0.3:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        return level, avg_score

    def _generate_mitigation_strategies(self, risks: list[RiskFactor]) -> list[MitigationStrategy]:
        """Generate mitigation strategies for identified risks"""
        strategies = []

        for risk in risks:
            if risk.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                priority = MitigationPriority.IMMEDIATE if risk.risk_level == RiskLevel.CRITICAL else MitigationPriority.HIGH

                # Generate strategy based on category
                if risk.category == RiskCategory.CAPACITY:
                    strategies.append(MitigationStrategy(
                        risk_category=risk.category,
                        strategy="Hire or contract grant management expertise",
                        priority=priority,
                        timeline="Before application submission",
                        resources_required=["Budget for grant manager", "HR approval"],
                        success_indicators=["Grant manager in place", "Application quality improved"]
                    ))

                elif risk.category == RiskCategory.TIMELINE:
                    strategies.append(MitigationStrategy(
                        risk_category=risk.category,
                        strategy="Request deadline extension or defer to next cycle",
                        priority=priority,
                        timeline="Immediately",
                        resources_required=["Communication with funder"],
                        success_indicators=["Extended deadline secured or next cycle planned"]
                    ))

                elif risk.category == RiskCategory.FINANCIAL:
                    strategies.append(MitigationStrategy(
                        risk_category=risk.category,
                        strategy="Identify and secure match funding sources",
                        priority=priority,
                        timeline="Before application submission",
                        resources_required=["Board approval", "Fundraising effort"],
                        success_indicators=["Match commitment letters obtained"]
                    ))

        return strategies

    def _calculate_proceed_recommendation(
        self,
        overall_risk: RiskLevel,
        critical_risks: list[RiskFactor],
        eligibility: EligibilityRiskAssessment
    ) -> bool:
        """Calculate proceed recommendation"""

        # Don't proceed if critical risks or major eligibility issues
        if critical_risks or not eligibility.proceed_recommendation:
            return False

        # Don't proceed if overall risk is critical
        if overall_risk == RiskLevel.CRITICAL:
            return False

        # Proceed with caution if high risk
        return True

    def _generate_ai_insights(
        self,
        inp: RiskIntelligenceInput,
        all_risks: list[RiskFactor],
        critical: list[RiskFactor],
        high: list[RiskFactor],
        overall_level: RiskLevel
    ) -> AIRiskInsights:
        """Generate AI insights (placeholder)"""

        # TODO: Implement actual BAML call

        top_risks = [r.description for r in sorted(all_risks, key=lambda x: x.risk_score, reverse=True)[:3]]
        deal_breakers = [r.description for r in critical]

        summary = f"""
Risk analysis for {inp.opportunity_title} identifies {overall_level.value} overall risk level
with {len(critical)} critical and {len(high)} high-priority risks.
{"Proceed with caution and address critical risks before application." if overall_level in [RiskLevel.MEDIUM, RiskLevel.HIGH] else
 "Not recommended to proceed unless critical risks can be mitigated." if overall_level == RiskLevel.CRITICAL else
 "Proceed - manageable risk profile with standard mitigation strategies."}
        """.strip()

        proceed = overall_level not in [RiskLevel.CRITICAL] and len(critical) == 0

        return AIRiskInsights(
            risk_executive_summary=summary,
            top_3_risks=top_risks,
            deal_breaker_risks=deal_breakers,
            overlooked_risks=["Consider funder's funding priorities alignment", "Review past award patterns"],
            strategic_risk_factors=["Competition level", "Organizational readiness"],
            go_no_go_recommendation=proceed,
            recommendation_confidence=0.85,
            recommendation_reasoning=f"Based on {overall_level.value} risk level with {len(critical)} critical risks",
            risk_reduction_suggestions=[s.strategy for s in self._generate_mitigation_strategies(all_risks)[:3]]
        )

    def _generate_risk_summary(
        self,
        overall: RiskLevel,
        critical: list[RiskFactor],
        high: list[RiskFactor]
    ) -> str:
        """Generate concise risk summary"""

        return f"{overall.value.upper()} risk level with {len(critical)} critical and {len(high)} high risks requiring attention."

    def _identify_key_decision_factors(self, risks: list[RiskFactor]) -> list[str]:
        """Identify key factors for decision-making"""

        factors = []

        for risk in sorted(risks, key=lambda x: x.risk_score, reverse=True)[:5]:
            factors.append(f"{risk.category.value.title()}: {risk.description}")

        return factors

    def get_cost_estimate(self) -> Optional[float]:
        return RISK_INTELLIGENCE_COST

    def validate_inputs(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate tool inputs."""
        risk_input = kwargs.get("risk_input")

        if not risk_input:
            return False, "risk_input is required"

        if not isinstance(risk_input, RiskIntelligenceInput):
            return False, "risk_input must be RiskIntelligenceInput instance"

        if not risk_input.opportunity_id:
            return False, "opportunity_id is required"

        return True, None


# Convenience function
async def analyze_risk_intelligence(
    opportunity_id: str,
    opportunity_title: str,
    opportunity_description: str,
    funder_name: str,
    funder_type: str,
    organization_ein: str,
    organization_name: str,
    organization_mission: str,
    **kwargs
) -> ToolResult[RiskIntelligenceOutput]:
    """Analyze risk intelligence with the risk intelligence tool."""

    tool = RiskIntelligenceTool(kwargs.get("config"))

    risk_input = RiskIntelligenceInput(
        opportunity_id=opportunity_id,
        opportunity_title=opportunity_title,
        opportunity_description=opportunity_description,
        funder_name=funder_name,
        funder_type=funder_type,
        organization_ein=organization_ein,
        organization_name=organization_name,
        organization_mission=organization_mission,
        **{k: v for k, v in kwargs.items() if k != "config"}
    )

    return await tool.execute(risk_input=risk_input)
