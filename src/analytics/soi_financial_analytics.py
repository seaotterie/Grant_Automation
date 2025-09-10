#!/usr/bin/env python3
"""
SOI Financial Analytics Module
Comprehensive financial intelligence using IRS Statistics of Income data

Provides advanced financial analysis capabilities leveraging:
- Form 990 data (671,484 records) - Large nonprofits
- Form 990-PF data (235,374 records) - Private foundations  
- Form 990-EZ data (411,235 records) - Small nonprofits
- Multi-year trend analysis (2022-2024)
- Foundation grant-making intelligence
- Financial health and capacity assessment
"""

import sqlite3
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FormType(Enum):
    """IRS form types for financial data"""
    FORM_990 = "990"        # Large nonprofits
    FORM_990PF = "990-PF"    # Private foundations
    FORM_990EZ = "990-EZ"    # Small nonprofits
    BMF_ONLY = "BMF-Only"    # BMF data only


@dataclass
class FinancialMetrics:
    """Comprehensive financial metrics from SOI data"""
    ein: str
    form_type: FormType
    tax_year: int
    
    # Core financial data
    total_revenue: int = 0
    total_expenses: int = 0
    total_assets: int = 0
    total_contributions: int = 0
    program_service_revenue: int = 0
    
    # Foundation-specific (990-PF)
    grant_distributions: int = 0
    investment_income: int = 0
    fair_market_value: int = 0
    required_distribution: int = 0
    future_grants_approved: int = 0
    
    # Calculated ratios
    efficiency_ratio: float = 0.0        # (Revenue - Expenses) / Revenue
    program_service_ratio: float = 0.0   # Program Service Revenue / Total Revenue
    payout_ratio: float = 0.0           # Grant Distributions / Total Assets (foundations)
    
    # Financial health indicators
    financial_stability_score: float = 0.0
    grant_capacity_tier: str = "Unknown"
    sustainability_score: float = 0.0


@dataclass
class TrendAnalysis:
    """Multi-year financial trend analysis"""
    ein: str
    years_analyzed: List[int]
    
    # Revenue trends
    revenue_growth_rate: float = 0.0
    revenue_stability: float = 0.0
    
    # Asset trends
    asset_growth_rate: float = 0.0
    asset_stability: float = 0.0
    
    # Foundation grant trends (990-PF only)
    giving_growth_rate: float = 0.0
    giving_consistency: float = 0.0
    
    # Overall trend score
    trend_score: float = 0.0
    trend_direction: str = "Stable"  # Growth, Decline, Stable, Volatile


class SOIFinancialAnalytics:
    """SOI Financial Intelligence Analytics Engine"""
    
    def __init__(self, database_path: str = "data/bmf_soi.db"):
        self.database_path = database_path
        
        # Financial capacity tiers
        self.foundation_tiers = {
            "Major": 1000000,      # $1M+ in grants
            "Significant": 100000,  # $100K+ in grants
            "Moderate": 10000,     # $10K+ in grants
            "Small": 1000,        # $1K+ in grants
            "Minimal": 0          # Any grants
        }
        
        self.nonprofit_tiers = {
            "Large": 10000000,     # $10M+ revenue
            "Medium": 1000000,     # $1M+ revenue
            "Small": 100000,      # $100K+ revenue
            "Emerging": 50000,    # $50K+ revenue
            "Startup": 0          # Any revenue
        }
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection to BMF/SOI database"""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_financial_metrics(self, ein: str, tax_year: Optional[int] = None) -> Optional[FinancialMetrics]:
        """Get comprehensive financial metrics for an organization"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get latest or specific year financial data
                year_filter = f"AND tax_year = {tax_year}" if tax_year else ""
                
                # Try Form 990 first (large nonprofits)
                cursor.execute(f"""
                    SELECT 
                        ein, tax_year, totrevenue, totfuncexpns, totassetsend,
                        totcntrbgfts, prgmservrevnue, grntstogovt, grnsttoindiv
                    FROM form_990 
                    WHERE ein = ? {year_filter}
                    ORDER BY tax_year DESC 
                    LIMIT 1
                """, (ein,))
                
                row = cursor.fetchone()
                if row:
                    return self._create_990_metrics(row)
                
                # Try Form 990-PF (foundations)
                cursor.execute(f"""
                    SELECT 
                        ein, tax_year, totrcptperbks as revenue, totexpnspbks as expenses,
                        totassetsend, grscontrgifts as contributions, contrpdpbks as grants_paid,
                        netinvstinc as investment_income, fairmrktvalamt as fmv,
                        distribamt as required_dist, grntapprvfut as future_grants
                    FROM form_990pf 
                    WHERE ein = ? {year_filter}
                    ORDER BY tax_year DESC 
                    LIMIT 1
                """, (ein,))
                
                row = cursor.fetchone()
                if row:
                    return self._create_990pf_metrics(row)
                
                # Try Form 990-EZ (small nonprofits)
                cursor.execute(f"""
                    SELECT 
                        ein, tax_year, totrevnue as revenue, totexpns as expenses,
                        totassetsend, totcntrbs as contributions, prgmservrev as program_revenue
                    FROM form_990ez 
                    WHERE ein = ? {year_filter}
                    ORDER BY tax_year DESC 
                    LIMIT 1
                """, (ein,))
                
                row = cursor.fetchone()
                if row:
                    return self._create_990ez_metrics(row)
                
                logger.info(f"No SOI financial data found for EIN {ein}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving financial metrics for {ein}: {e}")
            return None
    
    def get_multi_year_trends(self, ein: str, years: int = 3) -> Optional[TrendAnalysis]:
        """Analyze multi-year financial trends (2022-2024)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get multi-year data from all form types
                financial_data = []
                
                # Form 990 data
                cursor.execute("""
                    SELECT tax_year, totrevenue, totassetsend, 'Form990' as form_type
                    FROM form_990 
                    WHERE ein = ? 
                    ORDER BY tax_year DESC 
                    LIMIT ?
                """, (ein, years))
                financial_data.extend(cursor.fetchall())
                
                # Form 990-PF data
                cursor.execute("""
                    SELECT tax_year, totrcptperbks as totrevenue, totassetsend, 
                           contrpdpbks as grants_paid, 'Form990PF' as form_type
                    FROM form_990pf 
                    WHERE ein = ? 
                    ORDER BY tax_year DESC 
                    LIMIT ?
                """, (ein, years))
                financial_data.extend(cursor.fetchall())
                
                # Form 990-EZ data
                cursor.execute("""
                    SELECT tax_year, totrevnue as totrevenue, totassetsend, 'Form990EZ' as form_type
                    FROM form_990ez 
                    WHERE ein = ? 
                    ORDER BY tax_year DESC 
                    LIMIT ?
                """, (ein, years))
                financial_data.extend(cursor.fetchall())
                
                if not financial_data:
                    return None
                
                return self._calculate_trends(ein, financial_data)
                
        except Exception as e:
            logger.error(f"Error analyzing trends for {ein}: {e}")
            return None
    
    def get_foundation_intelligence(self, ein: str) -> Dict[str, Any]:
        """Get foundation-specific grant-making intelligence"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get latest 990-PF data with grant-making details
                cursor.execute("""
                    SELECT 
                        ein, tax_year, contrpdpbks, fairmrktvalamt, distribamt,
                        grntapprvfut, netinvstinc, adjnetinc,
                        totassetsend, totrcptperbks
                    FROM form_990pf 
                    WHERE ein = ? AND contrpdpbks > 0
                    ORDER BY tax_year DESC 
                    LIMIT 1
                """, (ein,))
                
                row = cursor.fetchone()
                if not row:
                    return {"foundation_status": "Not a grant-making foundation"}
                
                # Calculate foundation intelligence metrics
                grants_paid = row['contrpdpbks'] or 0
                assets_fmv = row['fairmrktvalamt'] or 0
                required_dist = row['distribamt'] or 0
                future_grants = row['grntapprvfut'] or 0
                investment_income = row['netinvstinc'] or 0
                
                # Payout ratio (key foundation metric)
                payout_ratio = grants_paid / assets_fmv if assets_fmv > 0 else 0
                
                # Grant capacity tier
                capacity_tier = "Small"
                for tier, threshold in self.foundation_tiers.items():
                    if grants_paid >= threshold:
                        capacity_tier = tier
                        break
                
                # Investment efficiency (investment income to grants ratio)
                investment_efficiency = investment_income / grants_paid if grants_paid > 0 else 0
                
                return {
                    "foundation_status": "Active grant-maker",
                    "grants_paid_latest": grants_paid,
                    "assets_fair_market_value": assets_fmv,
                    "required_distribution": required_dist,
                    "future_grants_approved": future_grants,
                    "payout_ratio": payout_ratio,
                    "capacity_tier": capacity_tier,
                    "investment_efficiency": investment_efficiency,
                    "grant_making_priority": self._calculate_grant_priority(payout_ratio, grants_paid),
                    "tax_year": row['tax_year']
                }
                
        except Exception as e:
            logger.error(f"Error analyzing foundation intelligence for {ein}: {e}")
            return {"error": str(e)}
    
    def calculate_financial_health_score(self, metrics: FinancialMetrics, trends: Optional[TrendAnalysis] = None) -> float:
        """Calculate comprehensive financial health score (0-1)"""
        score = 0.0
        
        # Efficiency component (30%)
        if metrics.efficiency_ratio > 0:
            efficiency_score = min(1.0, max(0.0, metrics.efficiency_ratio))
            score += 0.30 * efficiency_score
        
        # Program service ratio component (25%) - higher is better for nonprofits
        if metrics.form_type != FormType.FORM_990PF:  # Not applicable to foundations
            program_score = min(1.0, metrics.program_service_ratio)
            score += 0.25 * program_score
        else:
            # For foundations, use payout ratio instead
            payout_score = min(1.0, metrics.payout_ratio * 20)  # 5% payout = 1.0 score
            score += 0.25 * payout_score
        
        # Asset stability component (20%)
        if metrics.total_assets > 0:
            # Size-based stability score
            if metrics.total_assets > 10000000:  # $10M+
                stability_score = 1.0
            elif metrics.total_assets > 1000000:  # $1M+
                stability_score = 0.8
            elif metrics.total_assets > 100000:  # $100K+
                stability_score = 0.6
            else:
                stability_score = 0.4
            score += 0.20 * stability_score
        
        # Trend component (15%)
        if trends:
            trend_score = min(1.0, max(0.0, trends.trend_score))
            score += 0.15 * trend_score
        else:
            score += 0.15 * 0.5  # Neutral if no trend data
        
        # Sustainability component (10%)
        sustainability_score = self._calculate_sustainability(metrics)
        score += 0.10 * sustainability_score
        
        return min(1.0, score)
    
    def get_capacity_assessment(self, ein: str) -> Dict[str, Any]:
        """Assess organizational capacity for grant applications or giving"""
        metrics = self.get_financial_metrics(ein)
        trends = self.get_multi_year_trends(ein)
        
        if not metrics:
            return {"status": "No financial data available"}
        
        health_score = self.calculate_financial_health_score(metrics, trends)
        
        # Capacity tier based on form type and size
        if metrics.form_type == FormType.FORM_990PF:
            # Foundation grant-making capacity
            capacity_info = self.get_foundation_intelligence(ein)
            return {
                "capacity_type": "Grant-making",
                "capacity_tier": capacity_info.get("capacity_tier", "Unknown"),
                "annual_giving": metrics.grant_distributions,
                "payout_ratio": metrics.payout_ratio,
                "health_score": health_score,
                "trends": trends.trend_direction if trends else "No trend data"
            }
        else:
            # Nonprofit grant-receiving capacity
            tier = "Startup"
            for tier_name, threshold in self.nonprofit_tiers.items():
                if metrics.total_revenue >= threshold:
                    tier = tier_name
                    break
            
            return {
                "capacity_type": "Grant-receiving",
                "capacity_tier": tier,
                "annual_revenue": metrics.total_revenue,
                "program_ratio": metrics.program_service_ratio,
                "health_score": health_score,
                "trends": trends.trend_direction if trends else "No trend data"
            }
    
    def _create_990_metrics(self, row: sqlite3.Row) -> FinancialMetrics:
        """Create metrics from Form 990 data"""
        revenue = row['totrevenue'] or 0
        expenses = row['totfuncexpns'] or 0
        assets = row['totassetsend'] or 0
        contributions = row['totcntrbgfts'] or 0
        program_revenue = row['prgmservrevnue'] or 0
        
        metrics = FinancialMetrics(
            ein=row['ein'],
            form_type=FormType.FORM_990,
            tax_year=row['tax_year'],
            total_revenue=revenue,
            total_expenses=expenses,
            total_assets=assets,
            total_contributions=contributions,
            program_service_revenue=program_revenue
        )
        
        # Calculate ratios
        metrics.efficiency_ratio = (revenue - expenses) / revenue if revenue > 0 else 0
        metrics.program_service_ratio = program_revenue / revenue if revenue > 0 else 0
        metrics.sustainability_score = self._calculate_sustainability(metrics)
        
        return metrics
    
    def _create_990pf_metrics(self, row: sqlite3.Row) -> FinancialMetrics:
        """Create metrics from Form 990-PF data"""
        revenue = row['revenue'] or 0
        expenses = row['expenses'] or 0
        assets = row['totassetsend'] or 0
        contributions = row['contributions'] or 0
        grants_paid = row['grants_paid'] or 0
        investment_income = row['investment_income'] or 0
        fmv = row['fmv'] or 0
        
        metrics = FinancialMetrics(
            ein=row['ein'],
            form_type=FormType.FORM_990PF,
            tax_year=row['tax_year'],
            total_revenue=revenue,
            total_expenses=expenses,
            total_assets=assets,
            total_contributions=contributions,
            grant_distributions=grants_paid,
            investment_income=investment_income,
            fair_market_value=fmv,
            required_distribution=row.get('required_dist', 0) or 0,
            future_grants_approved=row.get('future_grants', 0) or 0
        )
        
        # Calculate foundation-specific ratios
        metrics.efficiency_ratio = (revenue - expenses) / revenue if revenue > 0 else 0
        metrics.payout_ratio = grants_paid / fmv if fmv > 0 else 0
        
        # Foundation capacity tier
        for tier, threshold in self.foundation_tiers.items():
            if grants_paid >= threshold:
                metrics.grant_capacity_tier = tier
                break
        
        metrics.sustainability_score = self._calculate_sustainability(metrics)
        return metrics
    
    def _create_990ez_metrics(self, row: sqlite3.Row) -> FinancialMetrics:
        """Create metrics from Form 990-EZ data"""
        revenue = row['revenue'] or 0
        expenses = row['expenses'] or 0
        assets = row['totassetsend'] or 0
        contributions = row['contributions'] or 0
        program_revenue = row.get('program_revenue', 0) or 0
        
        metrics = FinancialMetrics(
            ein=row['ein'],
            form_type=FormType.FORM_990EZ,
            tax_year=row['tax_year'],
            total_revenue=revenue,
            total_expenses=expenses,
            total_assets=assets,
            total_contributions=contributions,
            program_service_revenue=program_revenue
        )
        
        # Calculate ratios
        metrics.efficiency_ratio = (revenue - expenses) / revenue if revenue > 0 else 0
        metrics.program_service_ratio = program_revenue / revenue if revenue > 0 else 0
        metrics.sustainability_score = self._calculate_sustainability(metrics)
        
        return metrics
    
    def _calculate_trends(self, ein: str, financial_data: List[sqlite3.Row]) -> TrendAnalysis:
        """Calculate multi-year trend analysis"""
        if len(financial_data) < 2:
            return TrendAnalysis(ein=ein, years_analyzed=[])
        
        # Sort by year
        data = sorted(financial_data, key=lambda x: x['tax_year'])
        years = [row['tax_year'] for row in data]
        revenues = [row['totrevenue'] or 0 for row in data]
        assets = [row['totassetsend'] or 0 for row in data]
        
        # Calculate growth rates
        revenue_growth = self._calculate_growth_rate(revenues)
        asset_growth = self._calculate_growth_rate(assets)
        
        # Calculate stability (coefficient of variation)
        revenue_stability = 1 - (np.std(revenues) / np.mean(revenues)) if np.mean(revenues) > 0 else 0
        asset_stability = 1 - (np.std(assets) / np.mean(assets)) if np.mean(assets) > 0 else 0
        
        # Foundation-specific trends
        giving_growth = 0.0
        giving_consistency = 0.0
        if any(row.get('grants_paid') for row in data):
            grants = [row.get('grants_paid', 0) or 0 for row in data]
            giving_growth = self._calculate_growth_rate(grants)
            giving_consistency = 1 - (np.std(grants) / np.mean(grants)) if np.mean(grants) > 0 else 0
        
        # Overall trend score
        trend_score = (revenue_growth + asset_growth + revenue_stability + asset_stability) / 4
        
        # Trend direction
        direction = "Stable"
        if revenue_growth > 0.1:
            direction = "Growth"
        elif revenue_growth < -0.1:
            direction = "Decline"
        elif revenue_stability < 0.7:
            direction = "Volatile"
        
        return TrendAnalysis(
            ein=ein,
            years_analyzed=years,
            revenue_growth_rate=revenue_growth,
            revenue_stability=revenue_stability,
            asset_growth_rate=asset_growth,
            asset_stability=asset_stability,
            giving_growth_rate=giving_growth,
            giving_consistency=giving_consistency,
            trend_score=trend_score,
            trend_direction=direction
        )
    
    def _calculate_growth_rate(self, values: List[float]) -> float:
        """Calculate compound annual growth rate"""
        if len(values) < 2 or values[0] == 0:
            return 0.0
        
        try:
            years = len(values) - 1
            growth_rate = (values[-1] / values[0]) ** (1/years) - 1
            return max(-1.0, min(1.0, growth_rate))  # Cap at +/-100%
        except (ZeroDivisionError, ValueError):
            return 0.0
    
    def _calculate_sustainability(self, metrics: FinancialMetrics) -> float:
        """Calculate sustainability score based on financial mix"""
        if metrics.total_revenue == 0:
            return 0.0
        
        score = 0.0
        
        # Revenue diversification (program service revenue is more sustainable)
        if metrics.form_type != FormType.FORM_990PF:
            program_ratio = metrics.program_service_ratio
            contribution_ratio = metrics.total_contributions / metrics.total_revenue
            # Optimal mix: 60% program revenue, 40% contributions
            diversification_score = 1 - abs(program_ratio - 0.6) - abs(contribution_ratio - 0.4)
            score += max(0, diversification_score) * 0.5
        else:
            # Foundation sustainability based on investment income vs distributions
            if metrics.grant_distributions > 0:
                investment_ratio = metrics.investment_income / metrics.grant_distributions
                score += min(1.0, investment_ratio) * 0.5
        
        # Financial efficiency
        score += max(0, metrics.efficiency_ratio) * 0.3
        
        # Size stability factor
        if metrics.total_assets > 1000000:  # $1M+ assets
            score += 0.2
        elif metrics.total_assets > 100000:  # $100K+ assets
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_grant_priority(self, payout_ratio: float, grants_paid: int) -> str:
        """Calculate foundation grant-making priority level"""
        if payout_ratio >= 0.07:  # 7%+ payout (above legal minimum)
            if grants_paid >= 1000000:
                return "High Priority - Major Active Funder"
            elif grants_paid >= 100000:
                return "High Priority - Active Funder"
            else:
                return "Medium Priority - Regular Funder"
        elif payout_ratio >= 0.05:  # 5-7% payout (meeting legal minimum)
            if grants_paid >= 100000:
                return "Medium Priority - Compliant Funder"
            else:
                return "Low Priority - Minimal Funder"
        else:
            return "Low Priority - Below Standard Payout"


def get_soi_analytics() -> SOIFinancialAnalytics:
    """Get singleton instance of SOI financial analytics"""
    if not hasattr(get_soi_analytics, '_instance'):
        get_soi_analytics._instance = SOIFinancialAnalytics()
    return get_soi_analytics._instance
