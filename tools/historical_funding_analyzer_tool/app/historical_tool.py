"""
Historical Funding Analyzer Tool
12-Factor compliant tool for historical funding pattern analysis.

Purpose: Analyze USASpending.gov historical data
Cost: $0.00 per analysis (no AI calls - data analysis)
Replaces: Historical analysis portions of tier processors
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Optional, Dict, Any, List
import time
from datetime import datetime
from collections import defaultdict

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext

try:
    from .historical_models import (
        HistoricalAnalysisInput,
        HistoricalAnalysis,
        FundingPattern,
        GeographicDistribution,
        TemporalTrend,
        CompetitiveInsight,
        HistoricalAnalysisMetadata,
        AWARD_SIZE_CATEGORIES,
        TREND_THRESHOLD_INCREASE,
        TREND_THRESHOLD_DECREASE,
        HISTORICAL_FUNDING_ANALYZER_COST
    )
except ImportError:
    from historical_models import (
        HistoricalAnalysisInput,
        HistoricalAnalysis,
        FundingPattern,
        GeographicDistribution,
        TemporalTrend,
        CompetitiveInsight,
        HistoricalAnalysisMetadata,
        AWARD_SIZE_CATEGORIES,
        TREND_THRESHOLD_INCREASE,
        TREND_THRESHOLD_DECREASE,
        HISTORICAL_FUNDING_ANALYZER_COST
    )


class HistoricalFundingAnalyzerTool(BaseTool[HistoricalAnalysis]):
    """
    12-Factor Historical Funding Analyzer Tool

    Factor 4: Returns structured HistoricalAnalysis
    Factor 6: Stateless - pure function analysis
    Factor 10: Single responsibility - historical analysis only
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize historical funding analyzer tool."""
        super().__init__(config)

        # Configuration
        self.default_analysis_years = config.get("default_analysis_years", 5) if config else 5

    def get_tool_name(self) -> str:
        return "Historical Funding Analyzer Tool"

    def get_tool_version(self) -> str:
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        return "Historical funding pattern analysis and trend detection"

    async def _execute(
        self,
        context: ToolExecutionContext,
        analysis_input: HistoricalAnalysisInput
    ) -> HistoricalAnalysis:
        """Execute historical funding analysis."""
        start_time = time.time()

        self.logger.info(
            f"Starting historical analysis: ein={analysis_input.organization_ein}, "
            f"awards={len(analysis_input.historical_data)}"
        )

        # Filter and prepare data
        filtered_data = self._filter_data(analysis_input)

        # Calculate summary metrics
        total_awards = len(filtered_data)
        total_funding = sum(award.get('amount', 0) for award in filtered_data)
        average_award_size = total_funding / total_awards if total_awards > 0 else 0

        # Analyze funding patterns
        funding_patterns = []
        if analysis_input.include_patterns:
            funding_patterns = self._analyze_funding_patterns(filtered_data)

        # Analyze geographic distribution
        geographic_distribution = []
        if analysis_input.include_geographic:
            geographic_distribution = self._analyze_geographic_distribution(filtered_data, total_funding)

        # Analyze temporal trends
        temporal_trends = []
        if analysis_input.include_temporal:
            temporal_trends = self._analyze_temporal_trends(filtered_data)

        # Competitive insights
        competitive_insights = []
        if analysis_input.include_competitive:
            competitive_insights = self._analyze_competitive_position(
                filtered_data,
                average_award_size,
                total_funding
            )

        # Generate key insights
        key_insights = self._generate_insights(
            funding_patterns,
            geographic_distribution,
            temporal_trends,
            total_awards,
            total_funding
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            funding_patterns,
            temporal_trends,
            average_award_size
        )

        # Create metadata
        analysis_time = (time.time() - start_time) * 1000  # ms
        date_range = self._get_date_range(filtered_data)

        metadata = HistoricalAnalysisMetadata(
            analysis_timestamp=datetime.now().isoformat(),
            years_analyzed=analysis_input.analysis_years or self.default_analysis_years,
            total_awards_analyzed=total_awards,
            date_range_start=date_range['start'],
            date_range_end=date_range['end'],
            analysis_time_ms=analysis_time,
            data_quality_score=self._calculate_data_quality(filtered_data)
        )

        # Create output
        output = HistoricalAnalysis(
            organization_ein=analysis_input.organization_ein,
            total_awards=total_awards,
            total_funding=total_funding,
            average_award_size=average_award_size,
            years_analyzed=analysis_input.analysis_years or self.default_analysis_years,
            funding_patterns=funding_patterns,
            geographic_distribution=geographic_distribution,
            temporal_trends=temporal_trends,
            competitive_insights=competitive_insights,
            metadata=metadata,
            key_insights=key_insights,
            recommendations=recommendations
        )

        self.logger.info(
            f"Completed historical analysis: awards={total_awards}, "
            f"funding=${total_funding:,.2f}, time={analysis_time:.2f}ms"
        )

        return output

    def _filter_data(self, analysis_input: HistoricalAnalysisInput) -> List[Dict[str, Any]]:
        """Filter historical data based on input parameters."""
        filtered = analysis_input.historical_data

        # Filter by award amount
        if analysis_input.min_award_amount:
            filtered = [
                award for award in filtered
                if award.get('amount', 0) >= analysis_input.min_award_amount
            ]

        # Filter by categories
        if analysis_input.award_categories:
            filtered = [
                award for award in filtered
                if award.get('category', '') in analysis_input.award_categories
            ]

        # Filter by years
        if analysis_input.analysis_years:
            current_year = datetime.now().year
            cutoff_year = current_year - analysis_input.analysis_years
            filtered = [
                award for award in filtered
                if self._extract_year(award.get('date', '')) >= cutoff_year
            ]

        return filtered

    def _analyze_funding_patterns(self, data: List[Dict[str, Any]]) -> List[FundingPattern]:
        """Analyze funding patterns in historical data."""
        patterns = []

        # Award size distribution
        size_distribution = defaultdict(list)
        for award in data:
            amount = award.get('amount', 0)
            category = self._categorize_award_size(amount)
            size_distribution[category].append(award)

        total_funding = sum(award.get('amount', 0) for award in data)

        for category, awards in size_distribution.items():
            if awards:
                category_funding = sum(a.get('amount', 0) for a in awards)
                patterns.append(FundingPattern(
                    pattern_type="award_size",
                    pattern_name=f"{category.title()} Awards",
                    description=f"Awards in the {category} category ({AWARD_SIZE_CATEGORIES[category][0]:,}-{AWARD_SIZE_CATEGORIES[category][1]:,})",
                    frequency=len(awards),
                    total_amount=category_funding,
                    percentage_of_total=(category_funding / total_funding * 100) if total_funding > 0 else 0,
                    examples=awards[:3]  # First 3 examples
                ))

        # Frequency patterns (awards per year)
        yearly_counts = defaultdict(int)
        for award in data:
            year = self._extract_year(award.get('date', ''))
            if year:
                yearly_counts[year] += 1

        if yearly_counts:
            avg_awards_per_year = sum(yearly_counts.values()) / len(yearly_counts)
            patterns.append(FundingPattern(
                pattern_type="frequency",
                pattern_name="Award Frequency",
                description=f"Average {avg_awards_per_year:.1f} awards per year",
                frequency=len(data),
                total_amount=total_funding,
                percentage_of_total=100.0,
                examples=[]
            ))

        return patterns

    def _analyze_geographic_distribution(
        self,
        data: List[Dict[str, Any]],
        total_funding: float
    ) -> List[GeographicDistribution]:
        """Analyze geographic distribution of funding."""
        state_data = defaultdict(lambda: {'awards': [], 'agencies': set()})

        for award in data:
            state = award.get('state', 'Unknown')
            state_data[state]['awards'].append(award)
            if award.get('agency'):
                state_data[state]['agencies'].add(award['agency'])

        distribution = []
        for state, info in state_data.items():
            awards = info['awards']
            state_funding = sum(a.get('amount', 0) for a in awards)

            distribution.append(GeographicDistribution(
                state=state,
                award_count=len(awards),
                total_funding=state_funding,
                percentage_of_total=(state_funding / total_funding * 100) if total_funding > 0 else 0,
                average_award_size=state_funding / len(awards) if awards else 0,
                agencies=sorted(list(info['agencies']))
            ))

        # Sort by total funding descending
        distribution.sort(key=lambda x: x.total_funding, reverse=True)

        return distribution

    def _analyze_temporal_trends(self, data: List[Dict[str, Any]]) -> List[TemporalTrend]:
        """Analyze temporal funding trends."""
        yearly_data = defaultdict(list)

        for award in data:
            year = self._extract_year(award.get('date', ''))
            if year:
                yearly_data[year].append(award)

        trends = []
        sorted_years = sorted(yearly_data.keys())

        for i, year in enumerate(sorted_years):
            awards = yearly_data[year]
            year_funding = sum(a.get('amount', 0) for a in awards)
            avg_award = year_funding / len(awards) if awards else 0

            # Calculate year-over-year change
            yoy_change = None
            trend_direction = None
            if i > 0:
                prev_year = sorted_years[i - 1]
                prev_funding = sum(a.get('amount', 0) for a in yearly_data[prev_year])
                if prev_funding > 0:
                    yoy_change = ((year_funding - prev_funding) / prev_funding) * 100

                    if yoy_change >= TREND_THRESHOLD_INCREASE * 100:
                        trend_direction = "increasing"
                    elif yoy_change <= TREND_THRESHOLD_DECREASE * 100:
                        trend_direction = "decreasing"
                    else:
                        trend_direction = "stable"

            trends.append(TemporalTrend(
                year=year,
                award_count=len(awards),
                total_funding=year_funding,
                average_award_size=avg_award,
                year_over_year_change=yoy_change,
                trend_direction=trend_direction
            ))

        return trends

    def _analyze_competitive_position(
        self,
        data: List[Dict[str, Any]],
        average_award_size: float,
        total_funding: float
    ) -> List[CompetitiveInsight]:
        """Analyze competitive position."""
        insights = []

        # Award size competitiveness
        if average_award_size > 0:
            if average_award_size >= 250000:
                insights.append(CompetitiveInsight(
                    insight_type="award_size",
                    description="Large average award size indicates strong competitive position",
                    metric_value=average_award_size,
                    comparison_to_peers="Above average",
                    recommendation="Continue pursuing large-scale opportunities"
                ))
            elif average_award_size < 50000:
                insights.append(CompetitiveInsight(
                    insight_type="award_size",
                    description="Small average award size may indicate early-stage competitiveness",
                    metric_value=average_award_size,
                    comparison_to_peers="Below average",
                    recommendation="Build track record to qualify for larger awards"
                ))

        # Funding consistency
        if len(data) >= 10:
            insights.append(CompetitiveInsight(
                insight_type="consistency",
                description="Strong award frequency demonstrates proven track record",
                metric_value=len(data),
                comparison_to_peers="Above average",
                recommendation="Leverage track record in future applications"
            ))

        return insights

    def _generate_insights(
        self,
        patterns: List[FundingPattern],
        distribution: List[GeographicDistribution],
        trends: List[TemporalTrend],
        total_awards: int,
        total_funding: float
    ) -> List[str]:
        """Generate key insights from analysis."""
        insights = []

        # Overall summary
        insights.append(
            f"Received {total_awards} awards totaling ${total_funding:,.2f} in historical funding"
        )

        # Award size insights
        if patterns:
            largest_pattern = max(patterns, key=lambda p: p.total_amount)
            insights.append(
                f"{largest_pattern.pattern_name} represents {largest_pattern.percentage_of_total:.1f}% of total funding"
            )

        # Geographic insights
        if distribution:
            top_state = distribution[0]
            insights.append(
                f"{top_state.state} is top funding state with ${top_state.total_funding:,.2f} ({top_state.percentage_of_total:.1f}%)"
            )

        # Temporal insights
        if trends and len(trends) >= 2:
            latest_trend = trends[-1]
            if latest_trend.trend_direction == "increasing":
                insights.append(
                    f"Funding trend is increasing ({latest_trend.year_over_year_change:+.1f}% year-over-year)"
                )
            elif latest_trend.trend_direction == "decreasing":
                insights.append(
                    f"Funding trend is decreasing ({latest_trend.year_over_year_change:+.1f}% year-over-year)"
                )

        return insights

    def _generate_recommendations(
        self,
        patterns: List[FundingPattern],
        trends: List[TemporalTrend],
        average_award_size: float
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        # Award size recommendations
        if average_award_size < 50000:
            recommendations.append(
                "Focus on building track record with small-to-medium grants before pursuing major awards"
            )
        elif average_award_size > 250000:
            recommendations.append(
                "Leverage proven success with large awards to pursue major funding opportunities"
            )

        # Trend recommendations
        if trends and len(trends) >= 2:
            latest_trend = trends[-1]
            if latest_trend.trend_direction == "decreasing":
                recommendations.append(
                    "Consider diversifying funding sources due to decreasing trend in historical awards"
                )
            elif latest_trend.trend_direction == "increasing":
                recommendations.append(
                    "Capitalize on positive funding momentum by applying to similar opportunities"
                )

        # Pattern recommendations
        if patterns:
            most_common_pattern = max(patterns, key=lambda p: p.frequency)
            recommendations.append(
                f"Target opportunities in the {most_common_pattern.pattern_name.lower()} range based on historical success"
            )

        return recommendations

    # Helper methods

    def _categorize_award_size(self, amount: float) -> str:
        """Categorize award by size."""
        for category, (min_amt, max_amt) in AWARD_SIZE_CATEGORIES.items():
            if min_amt <= amount < max_amt:
                return category
        return "major"

    def _extract_year(self, date_str: str) -> Optional[int]:
        """Extract year from date string."""
        if not date_str:
            return None

        try:
            # Try parsing common date formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y"]:
                try:
                    dt = datetime.strptime(str(date_str), fmt)
                    return dt.year
                except ValueError:
                    continue

            # Try extracting year directly
            year = int(str(date_str)[:4])
            if 1900 <= year <= 2100:
                return year
        except (ValueError, TypeError):
            pass

        return None

    def _get_date_range(self, data: List[Dict[str, Any]]) -> Dict[str, str]:
        """Get date range of historical data."""
        years = [self._extract_year(award.get('date', '')) for award in data]
        years = [y for y in years if y]

        if years:
            return {
                'start': str(min(years)),
                'end': str(max(years))
            }
        return {'start': 'Unknown', 'end': 'Unknown'}

    def _calculate_data_quality(self, data: List[Dict[str, Any]]) -> float:
        """Calculate data quality score."""
        if not data:
            return 0.0

        required_fields = ['amount', 'date', 'state', 'agency']
        quality_scores = []

        for award in data:
            present = sum(1 for field in required_fields if award.get(field))
            quality_scores.append(present / len(required_fields))

        return sum(quality_scores) / len(quality_scores)

    def get_cost_estimate(self) -> Optional[float]:
        return HISTORICAL_FUNDING_ANALYZER_COST

    def validate_inputs(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate tool inputs."""
        analysis_input = kwargs.get("analysis_input")

        if not analysis_input:
            return False, "analysis_input is required"

        if not isinstance(analysis_input, HistoricalAnalysisInput):
            return False, "analysis_input must be HistoricalAnalysisInput instance"

        if not analysis_input.organization_ein:
            return False, "organization_ein is required"

        if not analysis_input.historical_data:
            return False, "historical_data is required"

        return True, None


# Convenience function
async def analyze_historical_funding(
    organization_ein: str,
    historical_data: List[Dict[str, Any]],
    analysis_years: int = 5,
    include_geographic: bool = True,
    include_temporal: bool = True,
    include_patterns: bool = True,
    include_competitive: bool = False,
    config: Optional[dict] = None
) -> ToolResult[HistoricalAnalysis]:
    """Analyze historical funding data."""

    tool = HistoricalFundingAnalyzerTool(config)

    analysis_input = HistoricalAnalysisInput(
        organization_ein=organization_ein,
        historical_data=historical_data,
        analysis_years=analysis_years,
        include_geographic=include_geographic,
        include_temporal=include_temporal,
        include_patterns=include_patterns,
        include_competitive=include_competitive
    )

    return await tool.execute(analysis_input=analysis_input)
