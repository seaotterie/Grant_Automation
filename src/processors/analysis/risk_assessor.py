#!/usr/bin/env python3
"""
Enhanced Risk Assessment Scoring Processor
Advanced risk analysis processor that evaluates organizational risk factors and grant readiness.

This processor:
1. Takes organizations with trend analysis from previous steps
2. Performs comprehensive risk assessment across multiple dimensions
3. Calculates weighted risk scores and stability indicators
4. Provides actionable risk management recommendations
"""

import asyncio
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from statistics import mean, median

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile


class RiskAssessorProcessor(BaseProcessor):
    """Advanced risk assessment processor for grant decision intelligence."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="risk_assessor",
            description="Comprehensive risk assessment with financial stability and grant readiness scoring",
            version="1.0.0",
            dependencies=["trend_analyzer"],
            estimated_duration=60,  # 1 minute
            requires_network=False,
            requires_api_key=False
        )
        super().__init__(metadata)
        
        # Risk assessment weights and thresholds
        self.risk_weights = {
            "financial_stability": 0.25,    # Financial health and trends
            "operational_risk": 0.20,       # Filing consistency, governance
            "sustainability_risk": 0.20,    # Long-term viability
            "compliance_risk": 0.15,        # Regulatory and filing compliance
            "capacity_risk": 0.10,          # Ability to manage grants
            "external_risk": 0.10           # Market and sector risks
        }
        
        self.risk_thresholds = {
            "low_risk": 0.75,      # 75%+ = Low risk
            "moderate_risk": 0.50, # 50-75% = Moderate risk
            "high_risk": 0.25,     # 25-50% = High risk
            # Below 25% = Very high risk
        }
        
        # Grant readiness criteria
        self.readiness_criteria = {
            "min_revenue": 25000,           # Minimum annual revenue
            "max_revenue": 10000000,        # Maximum for typical grants
            "min_program_ratio": 0.60,      # Minimum program expense ratio
            "max_admin_ratio": 0.25,        # Maximum admin expense ratio
            "min_filing_recency": 2021,     # Must have recent filing
            "min_stability_score": 0.40     # Minimum financial stability
        }
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute comprehensive risk assessment."""
        start_time = time.time()
        
        try:
            # Get organizations with trend analysis
            organizations = await self._get_trend_analyzed_organizations(config, workflow_state)
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No trend-analyzed organizations found for risk assessment"]
                )
            
            self.logger.info(f"Assessing risk for {len(organizations)} organizations")
            
            # Perform risk assessment for each organization
            risk_assessments = []
            for org in organizations:
                assessment = await self._assess_organization_risk(org)
                if assessment:
                    risk_assessments.append(assessment)
            
            # Generate portfolio-level risk insights
            portfolio_risk = self._analyze_portfolio_risk(risk_assessments)
            
            execution_time = time.time() - start_time
            
            # Prepare results
            result_data = {
                "organizations": [org.dict() for org in organizations],
                "risk_assessments": risk_assessments,
                "portfolio_analysis": portfolio_risk,
                "assessment_stats": {
                    "total_organizations": len(organizations),
                    "risk_assessments_completed": len(risk_assessments),
                    "risk_methodology": "comprehensive_weighted_assessment",
                    "assessment_dimensions": list(self.risk_weights.keys())
                }
            }
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "assessment_type": "comprehensive_risk_analysis",
                    "risk_weights": self.risk_weights,
                    "risk_thresholds": self.risk_thresholds
                }
            )
            
        except Exception as e:
            self.logger.error(f"Risk assessment failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"Risk assessment failed: {str(e)}"]
            )
    
    async def _get_trend_analyzed_organizations(self, config: ProcessorConfig, workflow_state=None) -> List[OrganizationProfile]:
        """Get organizations from trend analyzer step."""
        try:
            if workflow_state and workflow_state.has_processor_succeeded('trend_analyzer'):
                org_dicts = workflow_state.get_organizations_from_processor('trend_analyzer')
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
            
            # Fallback to financial scorer if trend analyzer not available
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
            
            self.logger.warning("No suitable organizations found for risk assessment")
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get organizations for risk assessment: {e}")
            return []
    
    async def _assess_organization_risk(self, org: OrganizationProfile) -> Optional[Dict[str, Any]]:
        """Perform comprehensive risk assessment for a single organization."""
        try:
            # Get filing data for analysis
            filings = self._get_filing_data(org)
            
            # Calculate individual risk components
            financial_risk = self._assess_financial_stability_risk(org, filings)
            operational_risk = self._assess_operational_risk(org, filings)
            sustainability_risk = self._assess_sustainability_risk(org, filings)
            compliance_risk = self._assess_compliance_risk(org, filings)
            capacity_risk = self._assess_capacity_risk(org, filings)
            external_risk = self._assess_external_risk(org)
            
            # Calculate weighted composite risk score (0-1, higher is better/lower risk)
            composite_risk_score = (
                self.risk_weights["financial_stability"] * financial_risk["score"] +
                self.risk_weights["operational_risk"] * operational_risk["score"] +
                self.risk_weights["sustainability_risk"] * sustainability_risk["score"] +
                self.risk_weights["compliance_risk"] * compliance_risk["score"] +
                self.risk_weights["capacity_risk"] * capacity_risk["score"] +
                self.risk_weights["external_risk"] * external_risk["score"]
            )
            
            # Determine risk classification
            risk_classification = self._classify_risk_level(composite_risk_score)
            
            # Calculate grant readiness score
            grant_readiness = self._calculate_grant_readiness_score(org, filings)
            
            # Generate risk-based recommendations
            recommendations = self._generate_risk_recommendations(
                org, financial_risk, operational_risk, sustainability_risk, 
                compliance_risk, capacity_risk, external_risk
            )
            
            # Prepare comprehensive assessment
            assessment = {
                "ein": org.ein,
                "name": org.name,
                "composite_risk_score": composite_risk_score,
                "risk_classification": risk_classification,
                "grant_readiness_score": grant_readiness["score"],
                "grant_readiness_level": grant_readiness["level"],
                
                # Detailed risk breakdown
                "risk_components": {
                    "financial_stability": financial_risk,
                    "operational_risk": operational_risk,
                    "sustainability_risk": sustainability_risk,
                    "compliance_risk": compliance_risk,
                    "capacity_risk": capacity_risk,
                    "external_risk": external_risk
                },
                
                # Strategic insights
                "key_risk_factors": self._identify_key_risk_factors(
                    [financial_risk, operational_risk, sustainability_risk, 
                     compliance_risk, capacity_risk, external_risk]
                ),
                "risk_mitigation_priorities": recommendations["priorities"],
                "funding_recommendations": recommendations["funding"],
                
                # Assessment metadata
                "assessment_date": datetime.now().isoformat(),
                "data_completeness": self._calculate_data_completeness(org, filings)
            }
            
            # Update organization with risk assessment data
            org.risk_assessment = assessment
            org.composite_risk_score = composite_risk_score
            org.risk_classification = risk_classification
            org.grant_readiness_level = grant_readiness["level"]
            
            return assessment
            
        except Exception as e:
            self.logger.warning(f"Failed to assess risk for {org.ein}: {e}")
            return None
    
    def _get_filing_data(self, org: OrganizationProfile) -> List[Dict[str, Any]]:
        """Extract filing data from organization."""
        if hasattr(org, 'filing_data') and org.filing_data:
            return org.filing_data.get('filings', [])
        return []
    
    def _assess_financial_stability_risk(self, org: OrganizationProfile, filings: List[Dict]) -> Dict[str, Any]:
        """Assess financial stability risk factors."""
        factors = []
        issues = []
        
        # Revenue stability (use trend analysis if available)
        if hasattr(org, 'trend_analysis') and org.trend_analysis:
            revenue_trend = org.trend_analysis.get("revenue_trend", {})
            volatility = revenue_trend.get("volatility", 1.0)
            
            if volatility < 0.2:  # Low volatility
                factors.append(0.9)
            elif volatility < 0.4:  # Moderate volatility
                factors.append(0.7)
            else:  # High volatility
                factors.append(0.3)
                issues.append("High revenue volatility")
        else:
            factors.append(0.6)  # Default if no trend data
        
        # Asset adequacy
        if org.revenue and org.assets:
            asset_ratio = org.assets / org.revenue
            if asset_ratio > 1.0:  # Assets > annual revenue
                factors.append(0.9)
            elif asset_ratio > 0.5:
                factors.append(0.7)
            else:
                factors.append(0.4)
                issues.append("Low asset-to-revenue ratio")
        
        # Program expense ratio (efficiency indicator)
        if org.program_expense_ratio:
            if org.program_expense_ratio > 0.8:
                factors.append(0.9)
            elif org.program_expense_ratio > 0.6:
                factors.append(0.7)
            else:
                factors.append(0.5)
                issues.append("Low program expense ratio")
        
        # Net asset position
        if filings:
            latest_filing = max(filings, key=lambda x: x.get("tax_prd_yr", 0))
            net_assets = self._extract_num(latest_filing, ["totnetassetend"])
            if net_assets > 0:
                factors.append(0.8)
            elif net_assets == 0:
                factors.append(0.6)
            else:
                factors.append(0.2)
                issues.append("Negative net assets")
        
        score = mean(factors) if factors else 0.5
        
        return {
            "score": score,
            "level": "low" if score > 0.75 else "moderate" if score > 0.5 else "high",
            "factors_analyzed": len(factors),
            "key_issues": issues,
            "details": {
                "asset_adequacy": factors[1] if len(factors) > 1 else None,
                "program_efficiency": factors[2] if len(factors) > 2 else None,
                "revenue_stability": factors[0] if factors else None
            }
        }
    
    def _assess_operational_risk(self, org: OrganizationProfile, filings: List[Dict]) -> Dict[str, Any]:
        """Assess operational and governance risk factors."""
        factors = []
        issues = []
        
        # Filing consistency
        if org.filing_consistency_score:
            if org.filing_consistency_score > 0.8:
                factors.append(0.9)
            elif org.filing_consistency_score > 0.6:
                factors.append(0.7)
            else:
                factors.append(0.4)
                issues.append("Inconsistent filing history")
        
        # Filing recency
        if org.most_recent_filing_year:
            years_behind = 2024 - org.most_recent_filing_year
            if years_behind <= 1:
                factors.append(0.9)
            elif years_behind <= 2:
                factors.append(0.7)
            else:
                factors.append(0.3)
                issues.append(f"Filing {years_behind} years behind")
        
        # Organization size (operational complexity)
        if org.revenue:
            if 100000 <= org.revenue <= 2000000:  # Sweet spot for operational efficiency
                factors.append(0.8)
            elif org.revenue < 50000:
                factors.append(0.6)
                issues.append("Very small organization - capacity concerns")
            elif org.revenue > 5000000:
                factors.append(0.7)  # Large orgs have different risks
            else:
                factors.append(0.7)
        
        # Board governance (if available)
        if hasattr(org, 'board_size') and org.board_size:
            if 5 <= org.board_size <= 15:  # Optimal board size
                factors.append(0.8)
            elif org.board_size < 3:
                factors.append(0.4)
                issues.append("Very small board - governance risk")
            else:
                factors.append(0.6)
        
        score = mean(factors) if factors else 0.6
        
        return {
            "score": score,
            "level": "low" if score > 0.75 else "moderate" if score > 0.5 else "high",
            "factors_analyzed": len(factors),
            "key_issues": issues,
            "details": {
                "filing_consistency": org.filing_consistency_score,
                "filing_recency_years": 2024 - org.most_recent_filing_year if org.most_recent_filing_year else None,
                "organization_size_category": self._categorize_org_size(org.revenue)
            }
        }
    
    def _assess_sustainability_risk(self, org: OrganizationProfile, filings: List[Dict]) -> Dict[str, Any]:
        """Assess long-term sustainability risk factors."""
        factors = []
        issues = []
        
        # Revenue growth trend (if available from trend analysis)
        if hasattr(org, 'trend_analysis') and org.trend_analysis:
            growth_classification = org.trend_analysis.get("growth_classification", "unknown")
            
            if growth_classification in ["accelerating", "steady_growth"]:
                factors.append(0.9)
            elif growth_classification == "stable_mature":
                factors.append(0.7)
            elif growth_classification == "declining":
                factors.append(0.4)
                issues.append("Declining revenue trend")
            else:
                factors.append(0.6)
        
        # Funding diversification (proxy through revenue size and type)
        if org.revenue:
            # Larger orgs typically have more diverse funding
            if org.revenue > 500000:
                factors.append(0.8)
            elif org.revenue > 100000:
                factors.append(0.7)
            else:
                factors.append(0.5)
                issues.append("Small size may indicate limited funding sources")
        
        # Financial reserves (assets vs expenses)
        if org.assets and filings:
            latest_filing = max(filings, key=lambda x: x.get("tax_prd_yr", 0))
            total_expenses = self._extract_num(latest_filing, ["totexpns"])
            
            if total_expenses > 0:
                months_of_reserves = (org.assets / total_expenses) * 12
                if months_of_reserves > 12:  # More than 1 year
                    factors.append(0.9)
                elif months_of_reserves > 6:  # 6-12 months
                    factors.append(0.7)
                elif months_of_reserves > 3:  # 3-6 months
                    factors.append(0.5)
                else:
                    factors.append(0.3)
                    issues.append("Low financial reserves")
        
        # Market sector stability (NTEE-based)
        sector_stability = self._assess_sector_stability(org.ntee_code)
        factors.append(sector_stability)
        
        score = mean(factors) if factors else 0.5
        
        return {
            "score": score,
            "level": "low" if score > 0.75 else "moderate" if score > 0.5 else "high",
            "factors_analyzed": len(factors),
            "key_issues": issues,
            "details": {
                "growth_trend": getattr(org, 'growth_classification', None),
                "reserve_months": self._calculate_reserve_months(org, filings),
                "sector_stability": sector_stability
            }
        }
    
    def _assess_compliance_risk(self, org: OrganizationProfile, filings: List[Dict]) -> Dict[str, Any]:
        """Assess regulatory compliance risk factors."""
        factors = []
        issues = []
        
        # Filing completeness
        complete_filings = 0
        for filing in filings:
            required_fields = ["totrevenue", "totexpns", "totassetsend"]
            if all(self._extract_num(filing, [field]) > 0 for field in required_fields):
                complete_filings += 1
        
        if filings:
            completeness_ratio = complete_filings / len(filings)
            if completeness_ratio > 0.8:
                factors.append(0.9)
            elif completeness_ratio > 0.6:
                factors.append(0.7)
            else:
                factors.append(0.4)
                issues.append("Incomplete filing data")
        
        # Regular filing pattern
        if len(filings) >= 3:
            years = sorted([f.get("tax_prd_yr") for f in filings if f.get("tax_prd_yr")])
            gaps = [years[i] - years[i-1] for i in range(1, len(years))]
            
            if all(gap <= 1 for gap in gaps):
                factors.append(0.9)
            elif most_gaps_regular := sum(1 for gap in gaps if gap <= 1) / len(gaps) > 0.7:
                factors.append(0.7)
            else:
                factors.append(0.5)
                issues.append("Irregular filing pattern")
        
        # Organization type compliance indicators
        if org.subsection_code == "1":  # Private foundation
            factors.append(0.8)  # Generally more regulated, better compliance
        else:
            factors.append(0.7)  # Public charities have different compliance burden
        
        score = mean(factors) if factors else 0.6
        
        return {
            "score": score,
            "level": "low" if score > 0.75 else "moderate" if score > 0.5 else "high",
            "factors_analyzed": len(factors),
            "key_issues": issues,
            "details": {
                "filing_completeness": complete_filings / len(filings) if filings else 0,
                "regular_filing_pattern": len(filings) >= 3,
                "organization_type": "Private Foundation" if org.subsection_code == "1" else "Public Charity"
            }
        }
    
    def _assess_capacity_risk(self, org: OrganizationProfile, filings: List[Dict]) -> Dict[str, Any]:
        """Assess organizational capacity to manage grants effectively."""
        factors = []
        issues = []
        
        # Revenue size as capacity indicator
        if org.revenue:
            if org.revenue >= 250000:  # Sufficient for dedicated staff
                factors.append(0.8)
            elif org.revenue >= 100000:  # Moderate capacity
                factors.append(0.7)
            else:
                factors.append(0.5)
                issues.append("Small size may limit grant management capacity")
        
        # Administrative capacity (admin expense ratio)
        if filings:
            latest_filing = max(filings, key=lambda x: x.get("tax_prd_yr", 0))
            total_expenses = self._extract_num(latest_filing, ["totexpns"])
            program_expenses = self._extract_num(latest_filing, ["totfuncexpns"])
            
            if total_expenses > 0:
                admin_ratio = (total_expenses - program_expenses) / total_expenses
                if 0.10 <= admin_ratio <= 0.25:  # Healthy admin expense
                    factors.append(0.8)
                elif admin_ratio < 0.10:
                    factors.append(0.6)
                    issues.append("Very low admin expenses - may lack infrastructure")
                else:
                    factors.append(0.5)
                    issues.append("High admin expenses")
        
        # Organizational maturity (years of operation proxy)
        if len(filings) >= 5:
            factors.append(0.8)  # 5+ years of filings = mature org
        elif len(filings) >= 3:
            factors.append(0.7)  # 3-4 years = established
        else:
            factors.append(0.5)  # New organization
            issues.append("Limited operational history")
        
        score = mean(factors) if factors else 0.6
        
        return {
            "score": score,
            "level": "low" if score > 0.75 else "moderate" if score > 0.5 else "high",
            "factors_analyzed": len(factors),
            "key_issues": issues,
            "details": {
                "revenue_capacity_level": self._categorize_org_size(org.revenue),
                "years_of_operation": len(filings),
                "admin_infrastructure": "adequate" if factors and factors[-2] > 0.7 else "limited"
            }
        }
    
    def _assess_external_risk(self, org: OrganizationProfile) -> Dict[str, Any]:
        """Assess external market and sector risk factors."""
        factors = []
        issues = []
        
        # Geographic risk (state-level factors)
        state_risk = self._assess_state_risk(org.state)
        factors.append(state_risk)
        
        # Sector risk based on NTEE code
        sector_risk = self._assess_sector_risk(org.ntee_code)
        factors.append(sector_risk)
        
        # Size-market fit risk
        market_fit_risk = self._assess_market_fit_risk(org)
        factors.append(market_fit_risk)
        
        score = mean(factors) if factors else 0.7
        
        return {
            "score": score,
            "level": "low" if score > 0.75 else "moderate" if score > 0.5 else "high",
            "factors_analyzed": len(factors),
            "key_issues": issues,
            "details": {
                "geographic_risk": state_risk,
                "sector_risk": sector_risk,
                "market_fit_risk": market_fit_risk
            }
        }
    
    def _extract_num(self, filing: Dict[str, Any], keys: List[str]) -> float:
        """Extract numeric value from filing data."""
        for key in keys:
            if key in filing:
                try:
                    return float(filing[key])
                except (ValueError, TypeError):
                    continue
        return 0.0
    
    def _classify_risk_level(self, score: float) -> str:
        """Classify risk level based on composite score."""
        if score >= self.risk_thresholds["low_risk"]:
            return "low"
        elif score >= self.risk_thresholds["moderate_risk"]:
            return "moderate"  
        elif score >= self.risk_thresholds["high_risk"]:
            return "high"
        else:
            return "very_high"
    
    def _calculate_grant_readiness_score(self, org: OrganizationProfile, filings: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive grant readiness score."""
        readiness_factors = []
        barriers = []
        
        # Revenue size appropriateness
        if org.revenue:
            if self.readiness_criteria["min_revenue"] <= org.revenue <= self.readiness_criteria["max_revenue"]:
                readiness_factors.append(0.2)
            else:
                readiness_factors.append(0.1)
                if org.revenue < self.readiness_criteria["min_revenue"]:
                    barriers.append("Revenue below minimum threshold")
                else:
                    barriers.append("Revenue above typical grant size")
        
        # Program expense ratio
        if org.program_expense_ratio:
            if org.program_expense_ratio >= self.readiness_criteria["min_program_ratio"]:
                readiness_factors.append(0.2)
            else:
                readiness_factors.append(0.1)
                barriers.append("Low program expense ratio")
        
        # Filing recency
        if org.most_recent_filing_year:
            if org.most_recent_filing_year >= self.readiness_criteria["min_filing_recency"]:
                readiness_factors.append(0.15)
            else:
                readiness_factors.append(0.05)
                barriers.append("Outdated filing information")
        
        # Financial stability
        if hasattr(org, 'financial_stability_score') and org.financial_stability_score:
            if org.financial_stability_score >= self.readiness_criteria["min_stability_score"]:
                readiness_factors.append(0.15)
            else:
                readiness_factors.append(0.05)
                barriers.append("Low financial stability")
        
        # Operational capacity
        if org.revenue and org.revenue >= 100000:
            readiness_factors.append(0.15)
        else:
            readiness_factors.append(0.08)
            barriers.append("Limited operational capacity")
        
        # Compliance indicators
        if len(filings) >= 3:
            readiness_factors.append(0.13)
        else:
            readiness_factors.append(0.05)
            barriers.append("Limited compliance history")
        
        total_score = sum(readiness_factors)
        
        # Determine readiness level
        if total_score >= 0.8:
            level = "excellent"
        elif total_score >= 0.65:
            level = "good"
        elif total_score >= 0.5:
            level = "fair"
        else:
            level = "poor"
        
        return {
            "score": total_score,
            "level": level,
            "barriers": barriers,
            "strengths": [
                "Appropriate revenue size" if org.revenue and self.readiness_criteria["min_revenue"] <= org.revenue <= self.readiness_criteria["max_revenue"] else None,
                "Strong program focus" if org.program_expense_ratio and org.program_expense_ratio >= 0.7 else None,
                "Recent filings" if org.most_recent_filing_year and org.most_recent_filing_year >= 2022 else None,
                "Established operations" if len(filings) >= 5 else None
            ]
        }
    
    def _categorize_org_size(self, revenue: Optional[float]) -> str:
        """Categorize organization size based on revenue."""
        if not revenue:
            return "unknown"
        elif revenue < 50000:
            return "very_small"
        elif revenue < 250000:
            return "small"
        elif revenue < 1000000:
            return "medium"
        elif revenue < 5000000:
            return "large"
        else:
            return "very_large"
    
    def _assess_sector_stability(self, ntee_code: Optional[str]) -> float:
        """Assess sector stability based on NTEE code."""
        if not ntee_code:
            return 0.6
            
        # Health and human services typically stable
        if ntee_code.startswith(('E', 'F', 'P')):
            return 0.8
        # Education generally stable
        elif ntee_code.startswith('B'):
            return 0.8
        # Arts and culture more volatile
        elif ntee_code.startswith('A'):
            return 0.6
        # Environment variable
        elif ntee_code.startswith('C'):
            return 0.7
        # Other sectors
        else:
            return 0.7
    
    def _assess_state_risk(self, state: str) -> float:
        """Assess geographic risk factors."""
        # Simplified state risk assessment
        # In reality, this would consider economic indicators, nonprofit sector health, etc.
        stable_states = ['VA', 'MD', 'CA', 'NY', 'MA', 'CT', 'NJ']
        if state in stable_states:
            return 0.8
        else:
            return 0.7
    
    def _assess_sector_risk(self, ntee_code: Optional[str]) -> float:
        """Assess sector-specific risk factors."""
        return self._assess_sector_stability(ntee_code)  # Same logic for now
    
    def _assess_market_fit_risk(self, org: OrganizationProfile) -> float:
        """Assess organization's fit within its market context."""
        # Basic assessment - could be enhanced with market data
        if org.revenue and 50000 <= org.revenue <= 2000000:
            return 0.8  # Good size for grants
        else:
            return 0.6
    
    def _calculate_reserve_months(self, org: OrganizationProfile, filings: List[Dict]) -> Optional[float]:
        """Calculate months of financial reserves."""
        if not org.assets or not filings:
            return None
            
        latest_filing = max(filings, key=lambda x: x.get("tax_prd_yr", 0))
        total_expenses = self._extract_num(latest_filing, ["totexpns"])
        
        if total_expenses > 0:
            return (org.assets / total_expenses) * 12
        return None
    
    def _calculate_data_completeness(self, org: OrganizationProfile, filings: List[Dict]) -> float:
        """Calculate completeness of available data for assessment."""
        total_fields = 10  # Key fields for assessment
        available_fields = 0
        
        if org.revenue: available_fields += 1
        if org.assets: available_fields += 1
        if org.program_expense_ratio: available_fields += 1
        if org.most_recent_filing_year: available_fields += 1
        if org.filing_consistency_score: available_fields += 1
        if filings: available_fields += 1
        if org.ntee_code: available_fields += 1
        if org.state: available_fields += 1
        if hasattr(org, 'trend_analysis'): available_fields += 1
        if len(filings) >= 3: available_fields += 1
        
        return available_fields / total_fields
    
    def _identify_key_risk_factors(self, risk_components: List[Dict]) -> List[str]:
        """Identify the most significant risk factors."""
        key_risks = []
        
        for component in risk_components:
            if component["score"] < 0.5:  # High risk components
                key_risks.extend(component["key_issues"])
        
        return list(set(key_risks))[:5]  # Top 5 unique risks
    
    def _generate_risk_recommendations(self, org: OrganizationProfile, *risk_components) -> Dict[str, List[str]]:
        """Generate risk mitigation and funding recommendations."""
        priorities = []
        funding_recs = []
        
        # Analyze each risk component for recommendations
        financial_risk, operational_risk, sustainability_risk, compliance_risk, capacity_risk, external_risk = risk_components
        
        # Financial recommendations
        if financial_risk["score"] < 0.6:
            priorities.append("Improve financial stability and reserves")
            funding_recs.append("Consider capacity building grants for financial management")
        
        # Operational recommendations
        if operational_risk["score"] < 0.6:
            priorities.append("Strengthen operational systems and compliance")
            funding_recs.append("Provide general operating support to build infrastructure")
        
        # Sustainability recommendations
        if sustainability_risk["score"] < 0.6:
            priorities.append("Develop sustainable funding strategies")
            funding_recs.append("Multi-year funding commitment to ensure stability")
        
        # Capacity recommendations
        if capacity_risk["score"] < 0.6:
            priorities.append("Build organizational capacity and systems")
            funding_recs.append("Capacity building grants before program funding")
        
        return {
            "priorities": priorities[:3],  # Top 3 priorities
            "funding": funding_recs[:3]   # Top 3 funding recommendations
        }
    
    def _analyze_portfolio_risk(self, assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze risk patterns across the entire portfolio of organizations."""
        if not assessments:
            return {}
        
        # Aggregate risk scores
        risk_scores = [a["composite_risk_score"] for a in assessments]
        risk_classifications = [a["risk_classification"] for a in assessments]
        grant_readiness_scores = [a["grant_readiness_score"] for a in assessments]
        
        # Calculate portfolio metrics
        portfolio_analysis = {
            "total_organizations": len(assessments),
            "average_risk_score": mean(risk_scores),
            "median_risk_score": median(risk_scores),
            "risk_distribution": {
                "low": sum(1 for r in risk_classifications if r == "low"),
                "moderate": sum(1 for r in risk_classifications if r == "moderate"),
                "high": sum(1 for r in risk_classifications if r == "high"),
                "very_high": sum(1 for r in risk_classifications if r == "very_high")
            },
            "average_grant_readiness": mean(grant_readiness_scores),
            
            # Portfolio recommendations
            "portfolio_health": "excellent" if mean(risk_scores) > 0.75 else
                              "good" if mean(risk_scores) > 0.6 else
                              "fair" if mean(risk_scores) > 0.45 else "concerning",
            
            "recommended_allocation": self._recommend_portfolio_allocation(risk_classifications),
            "high_priority_organizations": len([a for a in assessments if a["grant_readiness_score"] > 0.7]),
            "organizations_needing_capacity_building": len([a for a in assessments if a["composite_risk_score"] < 0.5])
        }
        
        return portfolio_analysis
    
    def _recommend_portfolio_allocation(self, risk_classifications: List[str]) -> Dict[str, str]:
        """Recommend funding allocation strategy based on portfolio risk profile."""
        total = len(risk_classifications)
        low_risk = sum(1 for r in risk_classifications if r == "low")
        moderate_risk = sum(1 for r in risk_classifications if r == "moderate")
        
        if low_risk / total > 0.6:
            return {
                "strategy": "aggressive_growth",
                "recommendation": "Focus on program expansion and impact scaling"
            }
        elif (low_risk + moderate_risk) / total > 0.7:
            return {
                "strategy": "balanced_portfolio",
                "recommendation": "Mix of program funding and capacity building"
            }
        else:
            return {
                "strategy": "capacity_focused",
                "recommendation": "Prioritize organizational development and stability"
            }
    
    def validate_inputs(self, config: ProcessorConfig) -> List[str]:
        """Validate inputs for risk assessment."""
        errors = []
        
        if not config.workflow_id:
            errors.append("Workflow ID is required")
        
        return errors


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return RiskAssessorProcessor()