#!/usr/bin/env python3
"""
Financial Analytics Module
Entity-independent financial analysis functions that can be reused across profiles.
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FinancialMetrics:
    """Standardized financial metrics for any organization"""
    ein: str
    organization_name: str
    revenue: Optional[float] = None
    assets: Optional[float] = None
    expenses: Optional[float] = None
    revenue_trend: Optional[float] = None  # Year-over-year change
    financial_stability_score: Optional[float] = None
    program_expense_ratio: Optional[float] = None
    asset_growth_rate: Optional[float] = None
    revenue_volatility: Optional[float] = None
    computed_at: datetime = None

    def __post_init__(self):
        if self.computed_at is None:
            self.computed_at = datetime.now()


class FinancialAnalytics:
    """
    Entity-independent financial analysis engine.
    Computes standardized financial metrics from raw data.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Financial health scoring weights (from original algorithm)
        self.weights = {
            "revenue_stability": 0.25,
            "asset_strength": 0.20,
            "program_efficiency": 0.20,
            "growth_trajectory": 0.15,
            "financial_diversity": 0.20
        }
    
    def analyze_organization_financials(self, filing_data: Dict[str, Any], 
                                      organization_name: str, 
                                      ein: str) -> FinancialMetrics:
        """
        Analyze financial data for a single organization.
        
        Args:
            filing_data: Raw filing data (990, 990-PF, etc.)
            organization_name: Organization name
            ein: Organization EIN
            
        Returns:
            FinancialMetrics object with computed analytics
        """
        try:
            metrics = FinancialMetrics(
                ein=ein,
                organization_name=organization_name
            )
            
            # Extract basic financial data
            if 'filings_with_data' in filing_data:
                filings = filing_data['filings_with_data']
                if filings:
                    metrics = self._process_filings(metrics, filings)
            elif 'filings' in filing_data:
                filings = filing_data['filings']
                if filings:
                    metrics = self._process_filings(metrics, filings)
            else:
                # Single filing data
                metrics = self._process_single_filing(metrics, filing_data)
            
            # Calculate derived metrics
            metrics.financial_stability_score = self._calculate_stability_score(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error analyzing financials for {ein}: {e}")
            return FinancialMetrics(ein=ein, organization_name=organization_name)
    
    def _process_filings(self, metrics: FinancialMetrics, filings: List[Dict[str, Any]]) -> FinancialMetrics:
        """Process multiple years of filing data"""
        if not filings:
            return metrics
        
        # Get most recent filing for primary metrics
        recent_filing = filings[0]
        metrics = self._extract_basic_metrics(metrics, recent_filing)
        
        # Calculate trends from multiple years
        if len(filings) > 1:
            metrics = self._calculate_trends(metrics, filings)
        
        return metrics
    
    def _process_single_filing(self, metrics: FinancialMetrics, filing_data: Dict[str, Any]) -> FinancialMetrics:
        """Process single filing data"""
        return self._extract_basic_metrics(metrics, filing_data)
    
    def _extract_basic_metrics(self, metrics: FinancialMetrics, filing: Dict[str, Any]) -> FinancialMetrics:
        """Extract basic financial metrics from a single filing"""
        try:
            # Revenue (various field names)
            revenue_fields = ['totrevenue', 'total_revenue', 'revenue', 'revenue_amt']
            for field in revenue_fields:
                if field in filing and filing[field]:
                    metrics.revenue = self._safe_float(filing[field])
                    break
            
            # Assets
            asset_fields = ['totassetsend', 'total_assets', 'assets', 'asset_amt']
            for field in asset_fields:
                if field in filing and filing[field]:
                    metrics.assets = self._safe_float(filing[field])
                    break
            
            # Expenses
            expense_fields = ['totfuncexpns', 'total_expenses', 'expenses', 'expense_amt']
            for field in expense_fields:
                if field in filing and filing[field]:
                    metrics.expenses = self._safe_float(filing[field])
                    break
            
            # Program expense ratio (nonprofit efficiency metric)
            if metrics.expenses and 'totprogrevs' in filing:
                program_expenses = self._safe_float(filing['totprogrevs'])
                if program_expenses:
                    metrics.program_expense_ratio = program_expenses / metrics.expenses
            
            return metrics
            
        except Exception as e:
            self.logger.debug(f"Error extracting basic metrics: {e}")
            return metrics
    
    def _calculate_trends(self, metrics: FinancialMetrics, filings: List[Dict[str, Any]]) -> FinancialMetrics:
        """Calculate financial trends from multiple years of data"""
        try:
            revenues = []
            assets_list = []
            
            for filing in filings:
                # Revenue trend
                revenue = None
                for field in ['totrevenue', 'total_revenue', 'revenue']:
                    if field in filing and filing[field]:
                        revenue = self._safe_float(filing[field])
                        break
                if revenue:
                    revenues.append(revenue)
                
                # Asset growth
                assets = None
                for field in ['totassetsend', 'total_assets', 'assets']:
                    if field in filing and filing[field]:
                        assets = self._safe_float(filing[field])
                        break
                if assets:
                    assets_list.append(assets)
            
            # Calculate year-over-year revenue change
            if len(revenues) >= 2:
                recent_revenue = revenues[0]
                prev_revenue = revenues[1]
                if prev_revenue > 0:
                    metrics.revenue_trend = (recent_revenue - prev_revenue) / prev_revenue
                
                # Calculate revenue volatility (standard deviation / mean)
                if len(revenues) >= 3:
                    revenue_array = np.array(revenues)
                    if revenue_array.mean() > 0:
                        metrics.revenue_volatility = revenue_array.std() / revenue_array.mean()
            
            # Calculate asset growth rate
            if len(assets_list) >= 2:
                recent_assets = assets_list[0]
                prev_assets = assets_list[1]
                if prev_assets > 0:
                    metrics.asset_growth_rate = (recent_assets - prev_assets) / prev_assets
            
            return metrics
            
        except Exception as e:
            self.logger.debug(f"Error calculating trends: {e}")
            return metrics
    
    def _calculate_stability_score(self, metrics: FinancialMetrics) -> Optional[float]:
        """Calculate overall financial stability score (0-1)"""
        try:
            score_components = []
            
            # Revenue stability (lower volatility = higher score)
            if metrics.revenue_volatility is not None:
                # Cap volatility at 1.0 for scoring
                capped_volatility = min(metrics.revenue_volatility, 1.0)
                revenue_stability = 1.0 - capped_volatility
                score_components.append(revenue_stability * self.weights["revenue_stability"])
            
            # Asset strength (normalized by revenue)
            if metrics.assets and metrics.revenue and metrics.revenue > 0:
                asset_ratio = metrics.assets / metrics.revenue
                # Normalize asset ratio (cap at 5x revenue)
                normalized_ratio = min(asset_ratio / 5.0, 1.0)
                score_components.append(normalized_ratio * self.weights["asset_strength"])
            
            # Program efficiency (higher program ratio = higher score)
            if metrics.program_expense_ratio is not None:
                # Cap at 1.0 for scoring
                efficiency_score = min(metrics.program_expense_ratio, 1.0)
                score_components.append(efficiency_score * self.weights["program_efficiency"])
            
            # Growth trajectory (positive growth = higher score)
            if metrics.revenue_trend is not None:
                # Normalize growth (-50% to +50% maps to 0-1)
                normalized_growth = max(0, min(1, (metrics.revenue_trend + 0.5)))
                score_components.append(normalized_growth * self.weights["growth_trajectory"])
            
            # Financial diversity (revenue vs assets balance)
            if metrics.revenue and metrics.assets and metrics.revenue > 0:
                diversity_ratio = min(metrics.revenue / (metrics.assets + 1), 1.0)
                score_components.append(diversity_ratio * self.weights["financial_diversity"])
            
            if score_components:
                # Weight the final score by how many components we have
                total_weight = sum(self.weights[key] for key in self.weights.keys()
                                 if any(key in comp_key for comp_key in 
                                       ["revenue_stability", "asset_strength", "program_efficiency", 
                                        "growth_trajectory", "financial_diversity"] 
                                       for comp_key in [key]))
                
                if total_weight > 0:
                    final_score = sum(score_components) / total_weight
                    return max(0, min(1, final_score))
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error calculating stability score: {e}")
            return None
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            if isinstance(value, str):
                # Remove common formatting
                import re
                cleaned = re.sub(r'[,$]', '', value.strip())
                if cleaned:
                    return float(cleaned)
                    
        except (ValueError, TypeError):
            pass
        
        return None
    
    def compare_organizations(self, metrics_list: List[FinancialMetrics]) -> List[FinancialMetrics]:
        """
        Compare and rank organizations by financial metrics.
        
        Args:
            metrics_list: List of FinancialMetrics to compare
            
        Returns:
            Sorted list by financial stability score (highest first)
        """
        try:
            # Filter out organizations without scores
            valid_metrics = [m for m in metrics_list if m.financial_stability_score is not None]
            
            # Sort by financial stability score (descending)
            sorted_metrics = sorted(valid_metrics, 
                                  key=lambda x: x.financial_stability_score, 
                                  reverse=True)
            
            self.logger.info(f"Ranked {len(sorted_metrics)} organizations by financial stability")
            return sorted_metrics
            
        except Exception as e:
            self.logger.error(f"Error comparing organizations: {e}")
            return metrics_list
    
    def get_peer_analysis(self, target_metrics: FinancialMetrics, 
                         peer_metrics: List[FinancialMetrics]) -> Dict[str, Any]:
        """
        Analyze how target organization compares to peers.
        
        Args:
            target_metrics: Metrics for target organization
            peer_metrics: Metrics for peer organizations
            
        Returns:
            Dictionary with peer comparison analysis
        """
        try:
            if not peer_metrics:
                return {"error": "No peer data available"}
            
            # Calculate peer statistics
            revenues = [m.revenue for m in peer_metrics if m.revenue]
            stability_scores = [m.financial_stability_score for m in peer_metrics 
                              if m.financial_stability_score is not None]
            
            analysis = {
                "peer_count": len(peer_metrics),
                "revenue_percentile": None,
                "stability_percentile": None,
                "peer_revenue_median": np.median(revenues) if revenues else None,
                "peer_stability_median": np.median(stability_scores) if stability_scores else None
            }
            
            # Calculate percentiles
            if target_metrics.revenue and revenues:
                analysis["revenue_percentile"] = (
                    len([r for r in revenues if r <= target_metrics.revenue]) / len(revenues)
                )
            
            if target_metrics.financial_stability_score and stability_scores:
                analysis["stability_percentile"] = (
                    len([s for s in stability_scores if s <= target_metrics.financial_stability_score]) / 
                    len(stability_scores)
                )
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in peer analysis: {e}")
            return {"error": str(e)}


# Global analytics instance
_financial_analytics: Optional[FinancialAnalytics] = None


def get_financial_analytics() -> FinancialAnalytics:
    """Get or create global financial analytics instance"""
    global _financial_analytics
    if _financial_analytics is None:
        _financial_analytics = FinancialAnalytics()
    return _financial_analytics