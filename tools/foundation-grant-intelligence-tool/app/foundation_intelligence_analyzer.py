#!/usr/bin/env python3
"""
Foundation Grant Intelligence Tool - 12-Factor Agents Implementation
Human Layer Framework - Factor 4: Tools as Structured Outputs

This tool demonstrates Factor 4 by providing foundation grant intelligence
with guaranteed structured output format, eliminating foundation analysis errors.

Single Responsibility: 990-PF analysis and grant-making capacity assessment
- Grant-making profile analysis
- Payout requirement calculations
- Foundation capacity scoring
- Investment portfolio analysis
- NO API calls (handled by separate tool)
- NO XML parsing (handled by separate tool)
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
import os

# Add the project root to access existing Catalynx infrastructure
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

print("Foundation Grant Intelligence Tool initializing...")


@dataclass
class FoundationAnalysisCriteria:
    """Input criteria for foundation grant intelligence analysis following Factor 4 principles."""
    target_eins: List[str]
    years_to_analyze: int = 3
    include_investment_analysis: bool = True
    include_payout_requirements: bool = True
    include_grant_capacity_scoring: bool = True
    min_grant_amount: float = 1000.0


@dataclass
class GrantMakingProfile:
    """Grant-making profile for a foundation."""
    ein: str
    foundation_name: str
    foundation_type: str = "Private Foundation"
    total_grants_paid: float = 0.0
    number_of_grants: int = 0
    average_grant_size: float = 0.0
    largest_grant_amount: float = 0.0
    smallest_grant_amount: float = 0.0
    grant_focus_areas: List[str] = field(default_factory=list)
    geographic_focus: List[str] = field(default_factory=list)
    recurring_recipients: List[str] = field(default_factory=list)
    grant_making_consistency_score: float = 0.0


@dataclass
class PayoutAnalysis:
    """Payout requirement analysis for foundations."""
    ein: str
    foundation_name: str
    tax_year: int
    total_assets: float = 0.0
    required_payout_percentage: float = 0.05  # 5% standard requirement
    required_payout_amount: float = 0.0
    actual_grants_paid: float = 0.0
    payout_compliance_status: str = "Unknown"
    excess_payout_amount: Optional[float] = None
    payout_deficit_amount: Optional[float] = None
    administrative_expenses: float = 0.0
    investment_income: float = 0.0
    payout_ratio: float = 0.0


@dataclass
class CapacityScore:
    """Foundation capacity scoring for grant research."""
    ein: str
    foundation_name: str
    overall_capacity_score: float = 0.0
    financial_strength_score: float = 0.0
    grant_activity_score: float = 0.0
    grant_size_score: float = 0.0
    accessibility_score: float = 0.0
    alignment_likelihood_score: float = 0.0
    capacity_category: str = "Unknown"
    annual_grant_budget_estimate: float = 0.0
    recommended_ask_range: str = "$0 - $0"
    best_application_timing: str = "Unknown"
    capacity_trend: str = "Unknown"


@dataclass
class InvestmentProfile:
    """Investment portfolio analysis for foundations."""
    ein: str
    foundation_name: str
    tax_year: int
    total_investment_assets: float = 0.0
    investment_income: float = 0.0
    investment_return_rate: float = 0.0
    portfolio_growth_rate: float = 0.0
    investment_strategy_indicators: List[str] = field(default_factory=list)
    liquidity_ratio: float = 0.0
    investment_risk_profile: str = "Unknown"
    endowment_stability_score: float = 0.0


@dataclass
class FoundationExecutionMetadata:
    """Foundation intelligence execution metadata."""
    execution_time_ms: float
    foundations_analyzed: int = 0
    payout_analyses_completed: int = 0
    capacity_scores_generated: int = 0
    investment_profiles_created: int = 0
    high_value_foundations_identified: int = 0
    data_completeness_average: float = 0.0
    analysis_depth_score: float = 0.0
    trend_analysis_years: int = 0
    calculation_accuracy_score: float = 0.0


@dataclass
class FoundationQualityAssessment:
    """Quality assessment for foundation intelligence."""
    overall_analysis_quality: float
    payout_calculation_accuracy: float
    capacity_scoring_reliability: float
    investment_analysis_depth: float
    grant_pattern_detection_score: float
    foundation_classification_accuracy: float
    limitation_notes: List[str] = field(default_factory=list)


@dataclass
class FoundationIntelligenceResult:
    """Complete foundation grant intelligence result - Factor 4 structured output."""
    grant_making_profiles: List[GrantMakingProfile]
    payout_requirements: List[PayoutAnalysis]
    foundation_capacity_scores: List[CapacityScore]
    investment_analysis: List[InvestmentProfile]
    high_value_foundations: List[str]
    execution_metadata: FoundationExecutionMetadata
    quality_assessment: FoundationQualityAssessment
    tool_name: str = "Foundation Grant Intelligence Tool"
    framework_compliance: str = "Human Layer 12-Factor Agents"
    factor_4_implementation: str = "Tools as Structured Outputs - eliminates foundation analysis errors"
    foundations_processed: int = 0
    major_grant_makers: int = 0
    total_grant_capacity_estimated: float = 0.0


class FoundationIntelligenceTool:
    """
    Foundation Grant Intelligence Tool - 12-Factor Agents Implementation

    Demonstrates Factor 4: Tools as Structured Outputs
    Single Responsibility: 990-PF analysis and grant-making capacity assessment
    """

    def __init__(self):
        self.tool_name = "Foundation Grant Intelligence Tool"
        self.version = "1.0.0"

        # Standard foundation analysis parameters
        self.standard_payout_rate = 0.05  # 5% annual payout requirement
        self.major_foundation_threshold = 1000000  # $1M+ assets for major classification
        self.significant_grant_threshold = 50000   # $50K+ for significant grants

    async def execute(self, criteria: FoundationAnalysisCriteria) -> FoundationIntelligenceResult:
        """
        Execute foundation grant intelligence with guaranteed structured output.

        Factor 4 Implementation: This method ALWAYS returns a FoundationIntelligenceResult
        with structured data, eliminating any foundation analysis errors.
        """
        start_time = time.time()

        # Initialize result structure
        result = FoundationIntelligenceResult(
            grant_making_profiles=[],
            payout_requirements=[],
            foundation_capacity_scores=[],
            investment_analysis=[],
            high_value_foundations=[],
            execution_metadata=FoundationExecutionMetadata(
                execution_time_ms=0.0,
                foundations_analyzed=0
            ),
            quality_assessment=FoundationQualityAssessment(
                overall_analysis_quality=0.0,
                payout_calculation_accuracy=0.0,
                capacity_scoring_reliability=0.0,
                investment_analysis_depth=0.0,
                grant_pattern_detection_score=0.0,
                foundation_classification_accuracy=0.0
            )
        )

        try:
            print(f"Starting foundation grant intelligence analysis for {len(criteria.target_eins)} organizations")

            # Process each foundation EIN
            for ein in criteria.target_eins:
                try:
                    await self._analyze_single_foundation(ein, criteria, result)
                except Exception as e:
                    print(f"Failed to analyze foundation {ein}: {e}")

            # Calculate final metrics
            result.foundations_processed = len(criteria.target_eins)
            result.execution_metadata.foundations_analyzed = len(criteria.target_eins)
            result.execution_metadata.execution_time_ms = (time.time() - start_time) * 1000

            # Identify high-value foundations
            result.high_value_foundations = self._identify_high_value_foundations(result)
            result.execution_metadata.high_value_foundations_identified = len(result.high_value_foundations)

            # Calculate total grant capacity
            result.total_grant_capacity_estimated = sum(
                score.annual_grant_budget_estimate for score in result.foundation_capacity_scores
            )

            # Count major grant makers
            result.major_grant_makers = len([
                profile for profile in result.grant_making_profiles
                if profile.total_grants_paid >= self.significant_grant_threshold
            ])

            # Generate quality assessment
            result.quality_assessment = self._assess_quality(result)

            print(f"Foundation grant intelligence completed:")
            print(f"   Foundations analyzed: {result.foundations_processed}")
            print(f"   Grant-making profiles: {len(result.grant_making_profiles)}")
            print(f"   Payout analyses: {len(result.payout_requirements)}")
            print(f"   Capacity scores: {len(result.foundation_capacity_scores)}")
            print(f"   Investment profiles: {len(result.investment_analysis)}")
            print(f"   High-value foundations: {len(result.high_value_foundations)}")
            print(f"   Total grant capacity: ${result.total_grant_capacity_estimated:,.0f}")
            print(f"   Execution time: {result.execution_metadata.execution_time_ms:.1f}ms")

            return result

        except Exception as e:
            print(f"Critical error in foundation grant intelligence: {e}")
            # Factor 4: Even on critical error, return structured result
            result.execution_metadata.execution_time_ms = (time.time() - start_time) * 1000
            result.quality_assessment.limitation_notes.append(f"Critical error: {str(e)}")
            return result

    async def _analyze_single_foundation(
        self,
        ein: str,
        criteria: FoundationAnalysisCriteria,
        result: FoundationIntelligenceResult
    ) -> None:
        """Analyze a single foundation for grant intelligence."""

        try:
            print(f"   Analyzing foundation: {ein}")

            # For demonstration, create mock foundation data
            # In production, this would integrate with Form 990 Analysis Tool results
            foundation_data = await self._get_foundation_data(ein)

            if not foundation_data:
                print(f"   No foundation data available for {ein}")
                return

            foundation_name = foundation_data.get('name', f"Foundation {ein}")

            # Generate grant-making profile
            if criteria.include_grant_capacity_scoring:
                grant_profile = self._create_grant_making_profile(ein, foundation_name, foundation_data)
                result.grant_making_profiles.append(grant_profile)

            # Generate payout analysis
            if criteria.include_payout_requirements:
                payout_analysis = self._create_payout_analysis(ein, foundation_name, foundation_data)
                result.payout_requirements.append(payout_analysis)
                result.execution_metadata.payout_analyses_completed += 1

            # Generate capacity score
            capacity_score = self._create_capacity_score(ein, foundation_name, foundation_data)
            result.foundation_capacity_scores.append(capacity_score)
            result.execution_metadata.capacity_scores_generated += 1

            # Generate investment profile
            if criteria.include_investment_analysis:
                investment_profile = self._create_investment_profile(ein, foundation_name, foundation_data)
                result.investment_analysis.append(investment_profile)
                result.execution_metadata.investment_profiles_created += 1

        except Exception as e:
            print(f"   Error analyzing foundation {ein}: {e}")

    async def _get_foundation_data(self, ein: str) -> Optional[Dict[str, Any]]:
        """Get foundation data (mock implementation for demonstration)."""

        # Mock foundation data for testing
        if ein == "812827604":  # HEROS BRIDGE (not actually a foundation, but for testing)
            return {
                'name': 'HEROS BRIDGE',
                'total_assets': 157689,
                'total_revenue': 504030,
                'grants_paid': 0,  # Not a foundation
                'investment_income': 5000,
                'administrative_expenses': 50000,
                'form_type': '990'  # Regular 990, not 990-PF
            }

        # Mock foundation data for demonstration
        foundation_data = {
            'name': f'Foundation {ein}',
            'total_assets': 5000000,  # $5M foundation
            'total_revenue': 300000,
            'grants_paid': 250000,   # $250K in grants
            'investment_income': 200000,
            'administrative_expenses': 50000,
            'form_type': '990-PF'
        }

        return foundation_data

    def _create_grant_making_profile(self, ein: str, name: str, data: Dict[str, Any]) -> GrantMakingProfile:
        """Create grant-making profile from foundation data."""

        grants_paid = data.get('grants_paid', 0)

        # Estimate grant details (in production, would come from Schedule I data)
        number_of_grants = max(1, int(grants_paid / 25000)) if grants_paid > 0 else 0  # Estimate ~$25K avg
        average_grant_size = grants_paid / number_of_grants if number_of_grants > 0 else 0

        profile = GrantMakingProfile(
            ein=ein,
            foundation_name=name,
            foundation_type="Private Non-Operating Foundation" if data.get('form_type') == '990-PF' else "Public Charity",
            total_grants_paid=grants_paid,
            number_of_grants=number_of_grants,
            average_grant_size=average_grant_size,
            largest_grant_amount=average_grant_size * 2 if average_grant_size > 0 else 0,  # Estimate
            smallest_grant_amount=average_grant_size * 0.5 if average_grant_size > 0 else 0,  # Estimate
            grant_focus_areas=["Education", "Health", "Human Services"] if grants_paid > 0 else [],
            geographic_focus=["VA", "MD", "DC"] if grants_paid > 0 else [],
            grant_making_consistency_score=0.8 if grants_paid > 50000 else 0.3
        )

        return profile

    def _create_payout_analysis(self, ein: str, name: str, data: Dict[str, Any]) -> PayoutAnalysis:
        """Create payout requirement analysis."""

        total_assets = data.get('total_assets', 0)
        grants_paid = data.get('grants_paid', 0)
        admin_expenses = data.get('administrative_expenses', 0)
        investment_income = data.get('investment_income', 0)

        # Calculate required payout (5% of assets)
        required_payout = total_assets * self.standard_payout_rate
        payout_ratio = grants_paid / total_assets if total_assets > 0 else 0

        # Determine compliance status
        if grants_paid >= required_payout:
            compliance_status = "Compliant"
            excess_amount = grants_paid - required_payout
            deficit_amount = None
        else:
            compliance_status = "Under-Payout"
            excess_amount = None
            deficit_amount = required_payout - grants_paid

        analysis = PayoutAnalysis(
            ein=ein,
            foundation_name=name,
            tax_year=2022,  # Default year
            total_assets=total_assets,
            required_payout_percentage=self.standard_payout_rate,
            required_payout_amount=required_payout,
            actual_grants_paid=grants_paid,
            payout_compliance_status=compliance_status,
            excess_payout_amount=excess_amount,
            payout_deficit_amount=deficit_amount,
            administrative_expenses=admin_expenses,
            investment_income=investment_income,
            payout_ratio=payout_ratio
        )

        return analysis

    def _create_capacity_score(self, ein: str, name: str, data: Dict[str, Any]) -> CapacityScore:
        """Create foundation capacity score for grant research."""

        total_assets = data.get('total_assets', 0)
        grants_paid = data.get('grants_paid', 0)

        # Calculate component scores (0.0-1.0)
        financial_strength_score = min(1.0, total_assets / 10000000)  # $10M = max score
        grant_activity_score = min(1.0, grants_paid / 500000)  # $500K = max score
        grant_size_score = min(1.0, (grants_paid / max(1, int(grants_paid / 25000))) / 100000)  # $100K avg = max

        # Mock accessibility and alignment scores
        accessibility_score = 0.7  # Most foundations moderately accessible
        alignment_likelihood_score = 0.6  # Moderate alignment likelihood

        # Calculate overall capacity score
        overall_score = (
            financial_strength_score * 0.3 +
            grant_activity_score * 0.3 +
            grant_size_score * 0.2 +
            accessibility_score * 0.1 +
            alignment_likelihood_score * 0.1
        )

        # Determine capacity category
        if overall_score >= 0.8:
            capacity_category = "Major"
        elif overall_score >= 0.6:
            capacity_category = "Significant"
        elif overall_score >= 0.4:
            capacity_category = "Moderate"
        else:
            capacity_category = "Limited"

        # Estimate annual grant budget (typically 5-7% of assets)
        annual_budget_estimate = total_assets * 0.06

        # Recommend ask range based on average grant size
        avg_grant = grants_paid / max(1, int(grants_paid / 25000)) if grants_paid > 0 else 0
        if avg_grant >= 50000:
            ask_range = f"${avg_grant*0.5:,.0f} - ${avg_grant*1.5:,.0f}"
        elif avg_grant >= 10000:
            ask_range = f"${avg_grant*0.7:,.0f} - ${avg_grant*1.3:,.0f}"
        else:
            ask_range = "$5,000 - $25,000"

        score = CapacityScore(
            ein=ein,
            foundation_name=name,
            overall_capacity_score=overall_score,
            financial_strength_score=financial_strength_score,
            grant_activity_score=grant_activity_score,
            grant_size_score=grant_size_score,
            accessibility_score=accessibility_score,
            alignment_likelihood_score=alignment_likelihood_score,
            capacity_category=capacity_category,
            annual_grant_budget_estimate=annual_budget_estimate,
            recommended_ask_range=ask_range,
            best_application_timing="Fall/Winter (October-December)",
            capacity_trend="Stable"
        )

        return score

    def _create_investment_profile(self, ein: str, name: str, data: Dict[str, Any]) -> InvestmentProfile:
        """Create investment portfolio analysis."""

        total_assets = data.get('total_assets', 0)
        investment_income = data.get('investment_income', 0)

        # Calculate investment metrics
        investment_return_rate = investment_income / total_assets if total_assets > 0 else 0
        portfolio_growth_rate = 0.05  # Assume 5% growth (would be calculated from multi-year data)

        # Determine investment strategy indicators
        strategy_indicators = []
        if investment_return_rate > 0.06:
            strategy_indicators.append("Growth-oriented")
        elif investment_return_rate > 0.03:
            strategy_indicators.append("Balanced approach")
        else:
            strategy_indicators.append("Conservative strategy")

        # Determine risk profile
        if investment_return_rate > 0.08:
            risk_profile = "Aggressive"
        elif investment_return_rate > 0.04:
            risk_profile = "Moderate"
        else:
            risk_profile = "Conservative"

        profile = InvestmentProfile(
            ein=ein,
            foundation_name=name,
            tax_year=2022,
            total_investment_assets=total_assets * 0.9,  # Assume 90% invested
            investment_income=investment_income,
            investment_return_rate=investment_return_rate,
            portfolio_growth_rate=portfolio_growth_rate,
            investment_strategy_indicators=strategy_indicators,
            liquidity_ratio=0.1,  # Assume 10% liquid assets
            investment_risk_profile=risk_profile,
            endowment_stability_score=0.8  # High stability assumption
        )

        return profile

    def _identify_high_value_foundations(self, result: FoundationIntelligenceResult) -> List[str]:
        """Identify high-value foundations for grant research targeting."""

        high_value_eins = []

        for score in result.foundation_capacity_scores:
            # High-value criteria: Major or Significant capacity + good grant activity
            if (score.capacity_category in ["Major", "Significant"] and
                score.overall_capacity_score >= 0.6 and
                score.annual_grant_budget_estimate >= 100000):

                high_value_eins.append(score.ein)

        return high_value_eins

    def _assess_quality(self, result: FoundationIntelligenceResult) -> FoundationQualityAssessment:
        """Assess the quality of the foundation intelligence analysis."""

        if result.foundations_processed == 0:
            return FoundationQualityAssessment(
                overall_analysis_quality=0.0,
                payout_calculation_accuracy=0.0,
                capacity_scoring_reliability=0.0,
                investment_analysis_depth=0.0,
                grant_pattern_detection_score=0.0,
                foundation_classification_accuracy=0.0,
                limitation_notes=["No foundations processed"]
            )

        # Calculate quality metrics
        profiles_created = len(result.grant_making_profiles)
        analysis_completion_rate = profiles_created / result.foundations_processed

        # Mock quality scores (in production, would be based on data quality)
        overall_quality = 0.8 * analysis_completion_rate
        payout_accuracy = 0.9  # High accuracy for payout calculations
        capacity_reliability = 0.7  # Moderate reliability without historical data
        investment_depth = 0.6  # Limited depth without detailed portfolio data
        pattern_detection = 0.5  # Limited without Schedule I data
        classification_accuracy = 0.9  # High accuracy for foundation type classification

        limitation_notes = []
        if analysis_completion_rate < 1.0:
            limitation_notes.append(f"Analysis completed for {analysis_completion_rate:.1%} of foundations")
        if len(result.high_value_foundations) == 0:
            limitation_notes.append("No high-value foundations identified")

        return FoundationQualityAssessment(
            overall_analysis_quality=overall_quality,
            payout_calculation_accuracy=payout_accuracy,
            capacity_scoring_reliability=capacity_reliability,
            investment_analysis_depth=investment_depth,
            grant_pattern_detection_score=pattern_detection,
            foundation_classification_accuracy=classification_accuracy,
            limitation_notes=limitation_notes
        )


# Test function for foundation analysis
async def test_foundation_intelligence():
    """Test the Foundation Grant Intelligence tool."""

    print("Testing Foundation Grant Intelligence Tool")
    print("=" * 60)

    # Initialize tool
    tool = FoundationIntelligenceTool()

    # Create test criteria
    criteria = FoundationAnalysisCriteria(
        target_eins=["812827604", "123456789"],  # HEROS BRIDGE + mock foundation
        years_to_analyze=3,
        include_investment_analysis=True,
        include_payout_requirements=True,
        include_grant_capacity_scoring=True,
        min_grant_amount=1000.0
    )

    # Execute analysis
    result = await tool.execute(criteria)

    # Display results
    print("\nAnalysis Results:")
    print(f"Tool: {result.tool_name}")
    print(f"Framework: {result.framework_compliance}")
    print(f"Factor 4: {result.factor_4_implementation}")
    print(f"Foundations processed: {result.foundations_processed}")
    print(f"Major grant makers: {result.major_grant_makers}")
    print(f"Total grant capacity: ${result.total_grant_capacity_estimated:,.0f}")

    if result.grant_making_profiles:
        print(f"\nGrant-Making Profiles ({len(result.grant_making_profiles)}):")
        for profile in result.grant_making_profiles:
            print(f"  {profile.foundation_name}: ${profile.total_grants_paid:,.0f} in grants")

    if result.foundation_capacity_scores:
        print(f"\nCapacity Scores ({len(result.foundation_capacity_scores)}):")
        for score in result.foundation_capacity_scores:
            print(f"  {score.foundation_name}: {score.capacity_category} ({score.overall_capacity_score:.2f})")

    if result.high_value_foundations:
        print(f"\nHigh-Value Foundations ({len(result.high_value_foundations)}):")
        for ein in result.high_value_foundations:
            print(f"  EIN: {ein}")

    print(f"\nExecution Metadata:")
    print(f"  Execution time: {result.execution_metadata.execution_time_ms:.1f}ms")
    print(f"  Analyses completed: {result.execution_metadata.payout_analyses_completed}")
    print(f"  Capacity scores: {result.execution_metadata.capacity_scores_generated}")

    print(f"\nQuality Assessment:")
    print(f"  Overall quality: {result.quality_assessment.overall_analysis_quality:.2f}")
    print(f"  Payout accuracy: {result.quality_assessment.payout_calculation_accuracy:.2f}")
    print(f"  Capacity reliability: {result.quality_assessment.capacity_scoring_reliability:.2f}")

    return result


if __name__ == "__main__":
    asyncio.run(test_foundation_intelligence())