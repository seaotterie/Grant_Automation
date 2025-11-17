"""
Financial Intelligence Tool
12-Factor compliant tool for comprehensive financial analysis.

Purpose: Deep financial analysis with AI-enhanced insights
Cost: $0.03 per analysis
Replaces: financial_scorer.py processor
"""

from src.core.tool_framework.path_helper import setup_tool_paths

# Setup paths for imports
project_root = setup_tool_paths(__file__)

from typing import Optional
import time
from datetime import datetime

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext
from .financial_models import (
    FinancialIntelligenceInput,
    FinancialIntelligenceOutput,
    FinancialMetrics,
    FinancialStrength,
    FinancialConcern,
    TrendAnalysis,
    GrantCapacityAssessment,
    AIFinancialInsights,
    FinancialHealthRating,
    TrendDirection,
    FINANCIAL_INTELLIGENCE_COST
)


class FinancialIntelligenceTool(BaseTool[FinancialIntelligenceOutput]):
    """
    12-Factor Financial Intelligence Tool

    Factor 4: Returns structured FinancialIntelligenceOutput
    Factor 6: Stateless - no persistence between runs
    Factor 10: Single responsibility - financial analysis only
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize financial intelligence tool.

        Args:
            config: Optional configuration
                - openai_api_key: OpenAI API key for AI insights
        """
        super().__init__(config)
        self.openai_api_key = config.get("openai_api_key") if config else None

    def get_tool_name(self) -> str:
        """Tool name."""
        return "Financial Intelligence Tool"

    def get_tool_version(self) -> str:
        """Tool version."""
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        """Tool's single responsibility."""
        return "Comprehensive financial analysis with AI-enhanced insights for nonprofits"

    async def _execute(
        self,
        context: ToolExecutionContext,
        financial_input: FinancialIntelligenceInput
    ) -> FinancialIntelligenceOutput:
        """
        Execute financial intelligence analysis.

        Args:
            context: Execution context
            financial_input: Financial intelligence input

        Returns:
            FinancialIntelligenceOutput with comprehensive analysis
        """
        start_time = time.time()

        self.logger.info(
            f"Starting financial intelligence analysis: {financial_input.organization_name} "
            f"(EIN: {financial_input.organization_ein})"
        )

        # Calculate financial metrics
        metrics = self._calculate_metrics(financial_input)

        # Assess strengths and concerns
        strengths = self._identify_strengths(financial_input, metrics)
        concerns = self._identify_concerns(financial_input, metrics)

        # Trend analysis (if historical data available)
        trends = self._analyze_trends(financial_input)

        # Grant capacity assessment
        grant_capacity = self._assess_grant_capacity(financial_input, metrics, concerns)

        # Overall health rating
        health_rating, health_score = self._calculate_health_rating(metrics, concerns, trends)

        # AI insights (placeholder - TODO: implement actual BAML call)
        ai_insights = self._generate_ai_insights(financial_input, metrics, strengths, concerns)

        # Data quality assessment
        data_quality = self._assess_data_quality(financial_input)

        processing_time = time.time() - start_time

        output = FinancialIntelligenceOutput(
            metrics=metrics,
            overall_health_rating=health_rating,
            overall_health_score=health_score,
            strengths=strengths,
            concerns=concerns,
            trends=trends,
            grant_capacity=grant_capacity,
            ai_insights=ai_insights,
            analysis_date=datetime.now().isoformat(),
            data_quality_score=data_quality,
            confidence_level=0.85,  # Placeholder
            processing_time_seconds=processing_time,
            api_cost_usd=FINANCIAL_INTELLIGENCE_COST
        )

        self.logger.info(
            f"Completed financial intelligence analysis: rating={health_rating.value}, "
            f"score={health_score:.2f}, concerns={len(concerns)}"
        )

        return output

    def _calculate_metrics(self, inp: FinancialIntelligenceInput) -> FinancialMetrics:
        """Calculate all financial metrics"""

        # Liquidity metrics
        current_ratio = inp.total_assets / max(inp.total_liabilities, 1) if inp.total_liabilities > 0 else 999.0
        months_of_expenses = (inp.net_assets / (inp.total_expenses / 12)) if inp.total_expenses > 0 else 999.0
        liquid_assets_ratio = inp.net_assets / max(inp.total_assets, 1)

        # Efficiency metrics
        program_ratio = inp.program_expenses / max(inp.total_expenses, 1)
        admin_ratio = inp.admin_expenses / max(inp.total_expenses, 1)
        fundraising_ratio = inp.fundraising_expenses / max(inp.total_expenses, 1)
        fundraising_efficiency = inp.contributions_grants / max(inp.fundraising_expenses, 1) if inp.fundraising_expenses > 0 else 999.0

        # Sustainability metrics
        revenue_growth = None
        expense_growth = None
        net_assets_growth = None

        if inp.prior_year_revenue and inp.prior_year_revenue > 0:
            revenue_growth = (inp.total_revenue - inp.prior_year_revenue) / inp.prior_year_revenue
        if inp.prior_year_expenses and inp.prior_year_expenses > 0:
            expense_growth = (inp.total_expenses - inp.prior_year_expenses) / inp.prior_year_expenses
        if inp.prior_year_net_assets and inp.prior_year_net_assets > 0:
            net_assets_growth = (inp.net_assets - inp.prior_year_net_assets) / inp.prior_year_net_assets

        operating_margin = (inp.total_revenue - inp.total_expenses) / max(inp.total_revenue, 1)

        # Diversification metrics
        revenue_sources = [
            inp.contributions_grants / max(inp.total_revenue, 1),
            inp.program_service_revenue / max(inp.total_revenue, 1),
            inp.investment_income / max(inp.total_revenue, 1),
            inp.other_revenue / max(inp.total_revenue, 1)
        ]
        largest_source = max(revenue_sources)
        # Herfindahl index for concentration (0=perfectly diversified, 1=single source)
        concentration = sum(s**2 for s in revenue_sources)

        # Capacity metrics
        asset_to_revenue = inp.total_assets / max(inp.total_revenue, 1)
        debt_to_asset = inp.total_liabilities / max(inp.total_assets, 1)

        return FinancialMetrics(
            current_ratio=current_ratio,
            months_of_expenses=months_of_expenses,
            liquid_assets_ratio=liquid_assets_ratio,
            program_expense_ratio=program_ratio,
            admin_expense_ratio=admin_ratio,
            fundraising_expense_ratio=fundraising_ratio,
            fundraising_efficiency=fundraising_efficiency,
            revenue_growth_rate=revenue_growth,
            expense_growth_rate=expense_growth,
            net_assets_growth_rate=net_assets_growth,
            operating_margin=operating_margin,
            revenue_concentration_score=concentration,
            largest_revenue_source_pct=largest_source * 100,
            asset_to_revenue_ratio=asset_to_revenue,
            debt_to_asset_ratio=debt_to_asset
        )

    def _identify_strengths(self, inp: FinancialIntelligenceInput, metrics: FinancialMetrics) -> list[FinancialStrength]:
        """Identify key financial strengths"""
        strengths = []

        # Program efficiency
        if metrics.program_expense_ratio >= 0.75:
            strengths.append(FinancialStrength(
                strength_category="Efficiency",
                description="Excellent program expense ratio demonstrating strong mission focus",
                metric_value=metrics.program_expense_ratio,
                metric_name="Program Expense Ratio",
                percentile=90.0
            ))

        # Liquidity
        if metrics.months_of_expenses >= 6:
            strengths.append(FinancialStrength(
                strength_category="Liquidity",
                description="Strong liquidity position with substantial operating reserves",
                metric_value=metrics.months_of_expenses,
                metric_name="Months of Operating Expenses",
                percentile=85.0
            ))

        # Revenue diversification
        if metrics.revenue_concentration_score < 0.5:
            strengths.append(FinancialStrength(
                strength_category="Sustainability",
                description="Well-diversified revenue streams reduce funding risk",
                metric_value=metrics.revenue_concentration_score,
                metric_name="Revenue Concentration Score",
                percentile=80.0
            ))

        # Growth
        if metrics.revenue_growth_rate and metrics.revenue_growth_rate > 0.10:
            strengths.append(FinancialStrength(
                strength_category="Growth",
                description="Strong revenue growth indicates organizational expansion",
                metric_value=metrics.revenue_growth_rate,
                metric_name="Revenue Growth Rate",
                percentile=75.0
            ))

        # Fundraising efficiency
        if metrics.fundraising_efficiency > 5.0:
            strengths.append(FinancialStrength(
                strength_category="Efficiency",
                description="Highly efficient fundraising operation generating strong ROI",
                metric_value=metrics.fundraising_efficiency,
                metric_name="Fundraising Efficiency Ratio",
                percentile=85.0
            ))

        return strengths[:5]  # Top 5 strengths

    def _identify_concerns(self, inp: FinancialIntelligenceInput, metrics: FinancialMetrics) -> list[FinancialConcern]:
        """Identify financial concerns"""
        concerns = []

        # Liquidity concerns
        if metrics.months_of_expenses < 3:
            concerns.append(FinancialConcern(
                concern_category="Liquidity",
                description="Limited operating reserves may create cash flow challenges",
                severity="high" if metrics.months_of_expenses < 1 else "medium",
                metric_value=metrics.months_of_expenses,
                metric_name="Months of Operating Expenses",
                recommendation="Build operating reserve to 3-6 months of expenses through surplus generation"
            ))

        # Program expense ratio
        if metrics.program_expense_ratio < 0.65:
            concerns.append(FinancialConcern(
                concern_category="Efficiency",
                description="Program expense ratio below best practice standards",
                severity="medium",
                metric_value=metrics.program_expense_ratio,
                metric_name="Program Expense Ratio",
                recommendation="Review overhead allocation and consider efficiency improvements"
            ))

        # Revenue concentration
        if metrics.revenue_concentration_score > 0.7:
            concerns.append(FinancialConcern(
                concern_category="Sustainability",
                description="High revenue concentration creates significant funding risk",
                severity="high",
                metric_value=metrics.revenue_concentration_score,
                metric_name="Revenue Concentration Score",
                recommendation="Diversify revenue sources to reduce dependency on single funding stream"
            ))

        # Negative trends
        if metrics.revenue_growth_rate and metrics.revenue_growth_rate < -0.10:
            concerns.append(FinancialConcern(
                concern_category="Sustainability",
                description="Declining revenue trend threatens long-term sustainability",
                severity="high",
                metric_value=metrics.revenue_growth_rate,
                metric_name="Revenue Growth Rate",
                recommendation="Develop revenue growth strategy and address underlying causes"
            ))

        # High debt
        if metrics.debt_to_asset_ratio > 0.5:
            concerns.append(FinancialConcern(
                concern_category="Risk",
                description="High debt level relative to assets increases financial risk",
                severity="medium",
                metric_value=metrics.debt_to_asset_ratio,
                metric_name="Debt to Asset Ratio",
                recommendation="Develop debt reduction plan and improve asset position"
            ))

        return concerns

    def _analyze_trends(self, inp: FinancialIntelligenceInput) -> list[TrendAnalysis]:
        """Analyze financial trends if historical data available"""
        trends = []

        if inp.prior_year_revenue and inp.prior_year_revenue > 0:
            revenue_change = (inp.total_revenue - inp.prior_year_revenue) / inp.prior_year_revenue
            direction = self._get_trend_direction(revenue_change)

            trends.append(TrendAnalysis(
                metric_name="Total Revenue",
                direction=direction,
                percentage_change=revenue_change * 100,
                interpretation=f"Revenue {'increased' if revenue_change > 0 else 'decreased'} by {abs(revenue_change * 100):.1f}% year-over-year",
                forecast="Continued growth expected if current trends persist" if revenue_change > 0 else "Revenue stabilization recommended"
            ))

        if inp.prior_year_expenses and inp.prior_year_expenses > 0:
            expense_change = (inp.total_expenses - inp.prior_year_expenses) / inp.prior_year_expenses
            direction = self._get_trend_direction(expense_change)

            trends.append(TrendAnalysis(
                metric_name="Total Expenses",
                direction=direction,
                percentage_change=expense_change * 100,
                interpretation=f"Expenses {'increased' if expense_change > 0 else 'decreased'} by {abs(expense_change * 100):.1f}% year-over-year",
                forecast="Expense management strategy needed" if expense_change > 0.15 else "Expense control appears effective"
            ))

        if inp.prior_year_net_assets and inp.prior_year_net_assets > 0:
            assets_change = (inp.net_assets - inp.prior_year_net_assets) / inp.prior_year_net_assets
            direction = self._get_trend_direction(assets_change)

            trends.append(TrendAnalysis(
                metric_name="Net Assets",
                direction=direction,
                percentage_change=assets_change * 100,
                interpretation=f"Net assets {'increased' if assets_change > 0 else 'decreased'} by {abs(assets_change * 100):.1f}% year-over-year",
                forecast="Financial position strengthening" if assets_change > 0 else "Asset preservation strategy needed"
            ))

        return trends

    def _get_trend_direction(self, change: float) -> TrendDirection:
        """Convert percentage change to trend direction"""
        if change > 0.15:
            return TrendDirection.STRONGLY_POSITIVE
        elif change > 0.05:
            return TrendDirection.POSITIVE
        elif change > -0.05:
            return TrendDirection.STABLE
        elif change > -0.15:
            return TrendDirection.NEGATIVE
        else:
            return TrendDirection.STRONGLY_NEGATIVE

    def _assess_grant_capacity(
        self,
        inp: FinancialIntelligenceInput,
        metrics: FinancialMetrics,
        concerns: list[FinancialConcern]
    ) -> GrantCapacityAssessment:
        """Assess grant management capacity"""

        # Budget capacity based on revenue and admin infrastructure
        budget_capacity_score = min(1.0, (
            metrics.program_expense_ratio * 0.4 +
            (1.0 - metrics.debt_to_asset_ratio) * 0.3 +
            min(metrics.months_of_expenses / 6, 1.0) * 0.3
        ))

        # Maximum grant size (conservative estimate)
        max_grant = inp.total_revenue * 0.5 if budget_capacity_score > 0.7 else inp.total_revenue * 0.25

        # Admin capacity concerns
        admin_concerns = []
        if metrics.admin_expense_ratio < 0.10:
            admin_concerns.append("Low administrative expense ratio may indicate insufficient management infrastructure")
        if metrics.admin_expense_ratio > 0.25:
            admin_concerns.append("High administrative expense ratio may face funder scrutiny")

        # Sustainability concerns
        sustainability_concerns = []
        if metrics.months_of_expenses < 3:
            sustainability_concerns.append("Limited operating reserves pose sustainability risk")
        if metrics.revenue_concentration_score > 0.7:
            sustainability_concerns.append("High revenue concentration creates dependency risk")

        # Match capability
        can_provide_match = metrics.months_of_expenses > 3 and metrics.operating_margin > 0
        max_match = min(25.0, metrics.months_of_expenses * 5) if can_provide_match else 0.0

        match_sources = []
        if inp.investment_income > 0:
            match_sources.append("Investment income")
        if inp.program_service_revenue > 0:
            match_sources.append("Program service revenue")
        if inp.contributions_grants > inp.total_revenue * 0.3:
            match_sources.append("Unrestricted contributions")

        # Sustainability score
        sustainability_score = min(1.0, (
            min(metrics.months_of_expenses / 6, 1.0) * 0.4 +
            (1.0 - metrics.revenue_concentration_score) * 0.3 +
            (metrics.operating_margin + 0.1) * 2.5 * 0.3
        ))

        return GrantCapacityAssessment(
            can_handle_budget=max_grant,
            budget_capacity_score=budget_capacity_score,
            budget_capacity_reasoning=f"Organization can manage grants up to ${max_grant:,.0f} based on revenue capacity and financial stability",
            admin_capacity_score=min(1.0, metrics.admin_expense_ratio / 0.15),
            admin_capacity_concerns=admin_concerns,
            sustainability_score=sustainability_score,
            sustainability_concerns=sustainability_concerns,
            can_provide_match=can_provide_match,
            max_match_percentage=max_match,
            match_source_suggestions=match_sources
        )

    def _calculate_health_rating(
        self,
        metrics: FinancialMetrics,
        concerns: list[FinancialConcern],
        trends: list[TrendAnalysis]
    ) -> tuple[FinancialHealthRating, float]:
        """Calculate overall health rating and score"""

        # Base score from metrics
        score = 0.0

        # Liquidity (25%)
        score += min(metrics.months_of_expenses / 6, 1.0) * 0.25

        # Efficiency (25%)
        score += metrics.program_expense_ratio * 0.25

        # Sustainability (25%)
        score += (1.0 - metrics.revenue_concentration_score) * 0.15
        score += (metrics.operating_margin + 0.1) * 1.25 * 0.10

        # Financial strength (25%)
        score += min(1.0 - metrics.debt_to_asset_ratio, 1.0) * 0.15
        score += min(metrics.current_ratio / 2, 1.0) * 0.10

        # Adjust for concerns
        critical_concerns = sum(1 for c in concerns if c.severity == "critical")
        high_concerns = sum(1 for c in concerns if c.severity == "high")

        score -= critical_concerns * 0.10
        score -= high_concerns * 0.05

        # Adjust for trends
        negative_trends = sum(1 for t in trends if t.direction in [TrendDirection.NEGATIVE, TrendDirection.STRONGLY_NEGATIVE])
        score -= negative_trends * 0.03

        score = max(0.0, min(1.0, score))

        # Rating based on score
        if score >= 0.80:
            rating = FinancialHealthRating.EXCELLENT
        elif score >= 0.65:
            rating = FinancialHealthRating.GOOD
        elif score >= 0.50:
            rating = FinancialHealthRating.FAIR
        elif score >= 0.35:
            rating = FinancialHealthRating.CONCERNING
        else:
            rating = FinancialHealthRating.CRITICAL

        return rating, score

    def _generate_ai_insights(
        self,
        inp: FinancialIntelligenceInput,
        metrics: FinancialMetrics,
        strengths: list[FinancialStrength],
        concerns: list[FinancialConcern]
    ) -> AIFinancialInsights:
        """Generate AI insights (placeholder)"""

        # TODO: Implement actual BAML call
        # For now, return rule-based insights

        executive_summary = f"""
{inp.organization_name} demonstrates {'strong' if metrics.program_expense_ratio > 0.75 else 'moderate'} program focus
with {metrics.program_expense_ratio * 100:.1f}% of expenses directed to programs. The organization maintains
{metrics.months_of_expenses:.1f} months of operating reserves and operates with {'diversified' if metrics.revenue_concentration_score < 0.5 else 'concentrated'}
revenue sources. {'Growth trends are positive' if metrics.revenue_growth_rate and metrics.revenue_growth_rate > 0 else 'Financial stability requires attention'}.
        """.strip()

        return AIFinancialInsights(
            executive_summary=executive_summary,
            strategic_opportunities=[s.description for s in strengths[:3]],
            strategic_risks=[c.description for c in concerns[:3]],
            competitive_advantages=[
                "Strong program efficiency" if metrics.program_expense_ratio > 0.75 else None,
                "Diversified revenue base" if metrics.revenue_concentration_score < 0.5 else None,
                "Strong liquidity position" if metrics.months_of_expenses > 6 else None
            ],
            competitive_weaknesses=[c.description for c in concerns if c.severity in ["high", "critical"]],
            financial_management_recommendations=[c.recommendation for c in concerns[:3]],
            grant_strategy_recommendations=[
                "Pursue grants aligned with current program capacity",
                "Consider multi-year grants to improve sustainability",
                "Leverage financial strengths in grant applications"
            ],
            industry_comparison="Analysis requires industry benchmarking data" if not inp.ntee_code else None,
            peer_benchmarking_insights="Peer comparison requires additional data" if not inp.ntee_code else None
        )

    def _assess_data_quality(self, inp: FinancialIntelligenceInput) -> float:
        """Assess completeness of input data"""
        fields = [
            inp.total_revenue > 0,
            inp.total_expenses > 0,
            inp.total_assets > 0,
            inp.program_expenses > 0,
            inp.admin_expenses > 0,
            inp.fundraising_expenses > 0,
            inp.prior_year_revenue is not None,
            inp.organization_mission is not None,
            inp.ntee_code is not None
        ]
        return sum(fields) / len(fields)

    def get_cost_estimate(self) -> Optional[float]:
        """Estimate execution cost."""
        return FINANCIAL_INTELLIGENCE_COST

    def validate_inputs(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate tool inputs."""
        financial_input = kwargs.get("financial_input")

        if not financial_input:
            return False, "financial_input is required"

        if not isinstance(financial_input, FinancialIntelligenceInput):
            return False, "financial_input must be FinancialIntelligenceInput instance"

        if not financial_input.organization_ein:
            return False, "organization_ein is required"

        if financial_input.total_revenue < 0:
            return False, "total_revenue must be non-negative"

        return True, None


# Convenience function for direct usage
async def analyze_financial_intelligence(
    organization_ein: str,
    organization_name: str,
    total_revenue: float,
    total_expenses: float,
    total_assets: float,
    total_liabilities: float,
    net_assets: float,
    contributions_grants: float,
    program_service_revenue: float,
    investment_income: float,
    other_revenue: float,
    program_expenses: float,
    admin_expenses: float,
    fundraising_expenses: float,
    prior_year_revenue: Optional[float] = None,
    prior_year_expenses: Optional[float] = None,
    prior_year_net_assets: Optional[float] = None,
    organization_mission: Optional[str] = None,
    ntee_code: Optional[str] = None,
    years_of_operation: Optional[int] = None,
    config: Optional[dict] = None
) -> ToolResult[FinancialIntelligenceOutput]:
    """
    Analyze financial intelligence with the financial intelligence tool.

    Returns:
        ToolResult with FinancialIntelligenceOutput
    """
    tool = FinancialIntelligenceTool(config)

    financial_input = FinancialIntelligenceInput(
        organization_ein=organization_ein,
        organization_name=organization_name,
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_assets=net_assets,
        contributions_grants=contributions_grants,
        program_service_revenue=program_service_revenue,
        investment_income=investment_income,
        other_revenue=other_revenue,
        program_expenses=program_expenses,
        admin_expenses=admin_expenses,
        fundraising_expenses=fundraising_expenses,
        prior_year_revenue=prior_year_revenue,
        prior_year_expenses=prior_year_expenses,
        prior_year_net_assets=prior_year_net_assets,
        organization_mission=organization_mission,
        ntee_code=ntee_code,
        years_of_operation=years_of_operation
    )

    return await tool.execute(financial_input=financial_input)
