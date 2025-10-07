#!/usr/bin/env python3
"""
Multi-Year Trend Analysis Engine
Advanced analytics processor that analyzes financial performance trends across 3-5 years.

This processor:
1. Takes scored organizations from financial scorer 
2. Analyzes multi-year financial trends and growth patterns
3. Calculates trend indicators and stability metrics
4. Generates predictive insights for grant decision-making
"""

import asyncio
import time
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from statistics import mean, stdev

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile


class TrendAnalyzerProcessor(BaseProcessor):
    """Advanced multi-year trend analysis processor for strategic intelligence."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="trend_analyzer",
            description="Multi-year financial trend analysis with predictive insights",
            version="1.0.0",
            dependencies=["financial_scorer"],
            estimated_duration=90,  # 1.5 minutes
            requires_network=False,
            requires_api_key=False
        )
        super().__init__(metadata)
        
        # Trend analysis thresholds
        self.trend_thresholds = {
            "strong_growth": 0.15,     # 15%+ annual growth
            "moderate_growth": 0.05,   # 5-15% annual growth
            "stable": 0.05,            # -5% to +5% change
            "declining": -0.15,        # -15% or worse decline
            "volatility_high": 0.30,   # High volatility threshold
            "consistency_min": 3       # Minimum years for trend analysis
        }
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute multi-year trend analysis."""
        start_time = time.time()
        
        try:
            # Get scored organizations
            organizations = await self._get_scored_organizations(config, workflow_state)
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No scored organizations found for trend analysis"]
                )
            
            self.logger.info(f"Analyzing trends for {len(organizations)} organizations")
            
            # Analyze trends for each organization
            trend_results = []
            for org in organizations:
                trend_data = await self._analyze_organization_trends(org)
                if trend_data:
                    trend_results.append(trend_data)
            
            # Generate aggregate insights
            market_insights = self._generate_market_insights(trend_results)
            
            execution_time = time.time() - start_time
            
            # Prepare results
            result_data = {
                "organizations": [org.dict() for org in organizations],
                "trend_analysis": trend_results,
                "market_insights": market_insights,
                "analysis_stats": {
                    "total_organizations": len(organizations),
                    "organizations_with_trends": len(trend_results),
                    "analysis_period": "2019-2023",
                    "trend_categories": list(self.trend_thresholds.keys())
                }
            }
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "analysis_type": "multi_year_trend_analysis",
                    "trend_thresholds": self.trend_thresholds
                }
            )
            
        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"Trend analysis failed: {str(e)}"]
            )
    
    async def _get_scored_organizations(self, config: ProcessorConfig, workflow_state=None) -> List[OrganizationProfile]:
        """Get organizations from financial scorer step."""
        try:
            if workflow_state and workflow_state.has_processor_succeeded('financial_scorer'):
                org_dicts = workflow_state.get_organizations_from_processor('financial_scorer')
                if org_dicts:
                    organizations = []
                    for org_dict in org_dicts:
                        try:
                            if isinstance(org_dict, dict):
                                org = OrganizationProfile(**org_dict)
                            else:
                                org = org_dict
                            organizations.append(org)
                        except Exception as e:
                            self.logger.warning(f"Failed to parse organization data: {e}")
                            continue
                    return organizations
            
            self.logger.warning("Financial scorer not completed - no organizations for trend analysis")
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get scored organizations: {e}")
            return []
    
    async def _analyze_organization_trends(self, org: OrganizationProfile) -> Optional[Dict[str, Any]]:
        """Analyze multi-year trends for a single organization."""
        try:
            # Get filing data
            filings = self._get_filing_data(org)
            if len(filings) < 2:  # Need at least 2 years for trend
                return None
            
            # Sort by year and extract financial time series
            filings.sort(key=lambda x: x.get("tax_prd_yr", 0))
            years = [f.get("tax_prd_yr") for f in filings if f.get("tax_prd_yr")]
            
            if len(years) < 2:
                return None
            
            # Extract financial metrics over time
            revenue_series = [self._extract_num(f, ["totrevenue"]) for f in filings]
            asset_series = [self._extract_num(f, ["totassetsend", "totnetassetend"]) for f in filings]
            expense_series = [self._extract_num(f, ["totexpns"]) for f in filings]
            program_series = [self._extract_num(f, ["totfuncexpns"]) for f in filings]
            
            # Calculate trend metrics
            trend_analysis = {
                "ein": org.ein,
                "name": org.name,
                "analysis_years": years,
                "years_of_data": len(years),
                
                # Revenue trends
                "revenue_trend": self._calculate_trend_metrics(revenue_series, years, "Revenue"),
                "asset_trend": self._calculate_trend_metrics(asset_series, years, "Assets"),
                "expense_trend": self._calculate_trend_metrics(expense_series, years, "Expenses"),
                "program_trend": self._calculate_trend_metrics(program_series, years, "Program Expenses"),
                
                # Financial health trends
                "financial_stability": self._assess_financial_stability(revenue_series, asset_series, expense_series),
                "growth_classification": self._classify_growth_pattern(revenue_series),
                "risk_indicators": self._identify_risk_indicators(filings),
                
                # Predictive insights
                "grant_readiness_score": self._calculate_grant_readiness(org, revenue_series, asset_series),
                "funding_capacity_trend": self._assess_funding_capacity_trend(revenue_series, expense_series),
                
                # Recommendations
                "strategic_recommendations": self._generate_recommendations(
                    org, revenue_series, asset_series, expense_series
                )
            }
            
            # Update organization with trend data
            org.trend_analysis = trend_analysis
            org.financial_stability_score = trend_analysis["financial_stability"]["stability_score"]
            org.growth_classification = trend_analysis["growth_classification"]
            org.grant_readiness_score = trend_analysis["grant_readiness_score"]
            
            return trend_analysis
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze trends for {org.ein}: {e}")
            return None
    
    def _get_filing_data(self, org: OrganizationProfile) -> List[Dict[str, Any]]:
        """Extract filing data from organization."""
        if hasattr(org, 'filing_data') and org.filing_data:
            return org.filing_data.get('filings', [])
        return []
    
    def _extract_num(self, filing: Dict[str, Any], keys: List[str]) -> float:
        """Extract numeric value from filing data."""
        for key in keys:
            if key in filing:
                try:
                    return float(filing[key])
                except (ValueError, TypeError):
                    continue
        return 0.0
    
    def _calculate_trend_metrics(self, series: List[float], years: List[int], metric_name: str) -> Dict[str, Any]:
        """Calculate comprehensive trend metrics for a financial series."""
        # Filter out zero values for meaningful analysis
        valid_data = [(year, value) for year, value in zip(years, series) if value > 0]
        
        if len(valid_data) < 2:
            return {
                "metric": metric_name,
                "trend": "insufficient_data",
                "annual_growth_rate": 0,
                "volatility": 0,
                "trend_strength": 0
            }
        
        values = [v[1] for v in valid_data]
        data_years = [v[0] for v in valid_data]
        
        # Calculate year-over-year growth rates
        growth_rates = []
        for i in range(1, len(values)):
            if values[i-1] > 0:
                growth_rate = (values[i] - values[i-1]) / values[i-1]
                growth_rates.append(growth_rate)
        
        # Calculate trend metrics
        avg_growth = mean(growth_rates) if growth_rates else 0
        volatility = stdev(growth_rates) if len(growth_rates) > 1 else 0
        
        # Classify trend
        if avg_growth >= self.trend_thresholds["strong_growth"]:
            trend_classification = "strong_growth"
        elif avg_growth >= self.trend_thresholds["moderate_growth"]:
            trend_classification = "moderate_growth"
        elif avg_growth >= -self.trend_thresholds["stable"]:
            trend_classification = "stable"
        elif avg_growth >= self.trend_thresholds["declining"]:
            trend_classification = "moderate_decline"
        else:
            trend_classification = "strong_decline"
        
        # Calculate trend strength (consistency of direction)
        positive_years = sum(1 for gr in growth_rates if gr > 0)
        trend_strength = abs(positive_years / len(growth_rates) - 0.5) * 2 if growth_rates else 0
        
        return {
            "metric": metric_name,
            "values": values,
            "years": data_years,
            "annual_growth_rate": avg_growth,
            "volatility": volatility,
            "trend": trend_classification,
            "trend_strength": trend_strength,
            "total_growth": (values[-1] / values[0] - 1) if values[0] > 0 else 0,
            "consecutive_growth_years": self._count_consecutive_growth(growth_rates)
        }
    
    def _count_consecutive_growth(self, growth_rates: List[float]) -> int:
        """Count consecutive years of positive growth."""
        max_consecutive = 0
        current_consecutive = 0
        
        for rate in reversed(growth_rates):  # Start from most recent
            if rate > 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                break
        
        return current_consecutive  # Return current streak from most recent
    
    def _assess_financial_stability(self, revenue_series: List[float], asset_series: List[float], 
                                  expense_series: List[float]) -> Dict[str, Any]:
        """Assess overall financial stability and health."""
        # Calculate stability metrics
        revenue_cv = self._coefficient_variation(revenue_series) if revenue_series else 1.0
        asset_cv = self._coefficient_variation(asset_series) if asset_series else 1.0
        
        # Asset-to-expense ratio trend (sustainability indicator)
        sustainability_ratios = []
        for assets, expenses in zip(asset_series, expense_series):
            if expenses > 0:
                sustainability_ratios.append(assets / expenses)
        
        # Calculate stability score (0-1, higher is better)
        stability_factors = []
        
        # Lower volatility is better
        if revenue_cv < 0.3:
            stability_factors.append(0.8)
        elif revenue_cv < 0.5:
            stability_factors.append(0.6)
        else:
            stability_factors.append(0.3)
        
        # Positive sustainability trend
        if len(sustainability_ratios) > 1:
            sustainability_trend = (sustainability_ratios[-1] - sustainability_ratios[0]) / len(sustainability_ratios)
            if sustainability_trend > 0:
                stability_factors.append(0.8)
            else:
                stability_factors.append(0.4)
        
        stability_score = mean(stability_factors) if stability_factors else 0.5
        
        return {
            "stability_score": stability_score,
            "revenue_volatility": revenue_cv,
            "asset_volatility": asset_cv,
            "sustainability_ratios": sustainability_ratios,
            "financial_health": "excellent" if stability_score > 0.8 else 
                              "good" if stability_score > 0.6 else
                              "fair" if stability_score > 0.4 else "poor"
        }
    
    def _coefficient_variation(self, series: List[float]) -> float:
        """Calculate coefficient of variation (std dev / mean)."""
        valid_values = [v for v in series if v > 0]
        if len(valid_values) < 2:
            return 0.0
        
        avg = mean(valid_values)
        std = stdev(valid_values)
        return std / avg if avg > 0 else 0.0
    
    def _classify_growth_pattern(self, revenue_series: List[float]) -> str:
        """Classify overall growth pattern."""
        if len(revenue_series) < 3:
            return "insufficient_data"
        
        # Calculate recent vs historical performance
        recent_revenues = revenue_series[-2:]  # Last 2 years
        historical_revenues = revenue_series[:-2]  # Earlier years
        
        if not historical_revenues:
            return "emerging"
        
        recent_avg = mean([r for r in recent_revenues if r > 0])
        historical_avg = mean([r for r in historical_revenues if r > 0])
        
        if recent_avg > historical_avg * 1.2:
            return "accelerating"
        elif recent_avg > historical_avg * 1.05:
            return "steady_growth"
        elif recent_avg > historical_avg * 0.95:
            return "stable_mature"
        else:
            return "declining"
    
    def _identify_risk_indicators(self, filings: List[Dict[str, Any]]) -> List[str]:
        """Identify potential risk indicators from filing patterns."""
        risks = []
        
        # Check for filing gaps
        years = sorted([f.get("tax_prd_yr") for f in filings if f.get("tax_prd_yr")])
        if len(years) > 1:
            gaps = [years[i] - years[i-1] for i in range(1, len(years))]
            if any(gap > 1 for gap in gaps):
                risks.append("filing_gaps")
        
        # Check for negative net assets
        for filing in filings:
            net_assets = self._extract_num(filing, ["totnetassetend"])
            if net_assets < 0:
                risks.append("negative_net_assets")
                break
        
        # Check for very low program expense ratios
        for filing in filings:
            program_exp = self._extract_num(filing, ["totfuncexpns"])
            total_exp = self._extract_num(filing, ["totexpns"])
            if total_exp > 0 and (program_exp / total_exp) < 0.5:
                risks.append("low_program_ratio")
                break
        
        return list(set(risks))  # Remove duplicates
    
    def _calculate_grant_readiness(self, org: OrganizationProfile, revenue_series: List[float], 
                                 asset_series: List[float]) -> float:
        """Calculate how ready an organization is to receive grants."""
        readiness_factors = []
        
        # Stable or growing revenue (0-0.3 points)
        if len(revenue_series) >= 2:
            recent_growth = (revenue_series[-1] - revenue_series[0]) / len(revenue_series)
            if recent_growth >= 0:
                readiness_factors.append(0.3)
            else:
                readiness_factors.append(0.1)
        
        # Sufficient assets for operations (0-0.2 points)
        if asset_series and revenue_series:
            latest_assets = asset_series[-1]
            latest_revenue = revenue_series[-1]
            if latest_revenue > 0 and (latest_assets / latest_revenue) > 0.5:
                readiness_factors.append(0.2)
            else:
                readiness_factors.append(0.1)
        
        # Recent filings (0-0.2 points)
        if org.most_recent_filing_year and org.most_recent_filing_year >= 2022:
            readiness_factors.append(0.2)
        elif org.most_recent_filing_year and org.most_recent_filing_year >= 2020:
            readiness_factors.append(0.1)
        else:
            readiness_factors.append(0.0)
        
        # Program expense ratio (0-0.15 points)
        if org.program_expense_ratio and org.program_expense_ratio > 0.7:
            readiness_factors.append(0.15)
        elif org.program_expense_ratio and org.program_expense_ratio > 0.5:
            readiness_factors.append(0.1)
        else:
            readiness_factors.append(0.05)
        
        # Size appropriate for grants (0-0.15 points)
        if org.revenue and 50000 <= org.revenue <= 5000000:
            readiness_factors.append(0.15)
        else:
            readiness_factors.append(0.05)
        
        return sum(readiness_factors)
    
    def _assess_funding_capacity_trend(self, revenue_series: List[float], expense_series: List[float]) -> str:
        """Assess trend in organization's capacity to handle additional funding."""
        if len(revenue_series) < 2 or len(expense_series) < 2:
            return "unknown"
        
        # Calculate surplus/deficit trend
        surpluses = [rev - exp for rev, exp in zip(revenue_series, expense_series)]
        
        if len(surpluses) < 2:
            return "unknown"
        
        recent_surplus = surpluses[-1]
        surplus_trend = surpluses[-1] - surpluses[0]
        
        if recent_surplus > 0 and surplus_trend > 0:
            return "increasing_capacity"
        elif recent_surplus > 0:
            return "stable_capacity"
        elif surplus_trend > 0:
            return "improving_capacity"
        else:
            return "limited_capacity"
    
    def _generate_recommendations(self, org: OrganizationProfile, revenue_series: List[float], 
                                asset_series: List[float], expense_series: List[float]) -> List[str]:
        """Generate strategic recommendations based on trend analysis."""
        recommendations = []
        
        # Revenue trend recommendations
        if len(revenue_series) >= 2:
            revenue_growth = (revenue_series[-1] - revenue_series[0]) / revenue_series[0] if revenue_series[0] > 0 else 0
            
            if revenue_growth > 0.15:
                recommendations.append("Strong growth trajectory - excellent grant candidate")
            elif revenue_growth > 0:
                recommendations.append("Steady growth - good grant candidate with monitoring")
            else:
                recommendations.append("Declining revenue - consider capacity building grants")
        
        # Financial stability recommendations
        if org.program_expense_ratio and org.program_expense_ratio > 0.8:
            recommendations.append("High program efficiency - mission-focused organization")
        elif org.program_expense_ratio and org.program_expense_ratio < 0.6:
            recommendations.append("Consider operational efficiency improvements")
        
        # Size-based recommendations
        if org.revenue:
            if org.revenue < 100000:
                recommendations.append("Small organization - consider general operating support")
            elif org.revenue > 2000000:
                recommendations.append("Large organization - suitable for major program funding")
            else:
                recommendations.append("Mid-size organization - ideal for targeted program grants")
        
        return recommendations
    
    def _generate_market_insights(self, trend_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate aggregate market insights from all organization trends."""
        if not trend_results:
            return {}
        
        # Aggregate growth classifications
        growth_patterns = {}
        stability_scores = []
        grant_readiness_scores = []
        
        for result in trend_results:
            pattern = result.get("growth_classification", "unknown")
            growth_patterns[pattern] = growth_patterns.get(pattern, 0) + 1
            
            if "financial_stability" in result:
                stability_scores.append(result["financial_stability"]["stability_score"])
            
            if "grant_readiness_score" in result:
                grant_readiness_scores.append(result["grant_readiness_score"])
        
        # Calculate market-level insights
        market_insights = {
            "sector_growth_distribution": growth_patterns,
            "average_stability_score": mean(stability_scores) if stability_scores else 0,
            "average_grant_readiness": mean(grant_readiness_scores) if grant_readiness_scores else 0,
            "high_growth_organizations": len([r for r in trend_results 
                                           if r.get("growth_classification") in ["accelerating", "steady_growth"]]),
            "stable_organizations": len([r for r in trend_results 
                                       if r.get("growth_classification") == "stable_mature"]),
            "declining_organizations": len([r for r in trend_results 
                                         if r.get("growth_classification") == "declining"]),
            "market_health_assessment": self._assess_market_health(growth_patterns, stability_scores)
        }
        
        return market_insights
    
    def _assess_market_health(self, growth_patterns: Dict[str, int], stability_scores: List[float]) -> str:
        """Assess overall market health based on growth patterns and stability."""
        total_orgs = sum(growth_patterns.values())
        if total_orgs == 0:
            return "unknown"
        
        healthy_orgs = growth_patterns.get("accelerating", 0) + growth_patterns.get("steady_growth", 0)
        healthy_ratio = healthy_orgs / total_orgs
        avg_stability = mean(stability_scores) if stability_scores else 0
        
        if healthy_ratio > 0.6 and avg_stability > 0.7:
            return "excellent"
        elif healthy_ratio > 0.4 and avg_stability > 0.6:
            return "good"
        elif healthy_ratio > 0.3 or avg_stability > 0.5:
            return "fair"
        else:
            return "challenging"
    
    def validate_inputs(self, config: ProcessorConfig) -> List[str]:
        """Validate inputs for trend analysis."""
        errors = []
        
        if not config.workflow_id:
            errors.append("Workflow ID is required")
        
        return errors


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return TrendAnalyzerProcessor()