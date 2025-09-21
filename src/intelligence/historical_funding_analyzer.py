"""
Historical Funding Pattern Analyzer
Standard Tier Intelligence Enhancement

Leverages existing USASpending.gov integration to provide comprehensive
historical funding pattern analysis for enhanced grant opportunity intelligence.
"""

import asyncio
import statistics
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict

from src.clients.usaspending_client import USASpendingClient
from src.core.government_models import HistoricalAward, OrganizationAwardHistory
from src.core.entity_cache_manager import get_entity_cache_manager
from src.processors.data_collection.usaspending_fetch import USASpendingFetchProcessor

logger = logging.getLogger(__name__)

@dataclass
class FundingIntelligence:
    """Structured funding intelligence from historical analysis"""
    agency_name: str
    program_keywords: List[str]
    analysis_date: str
    
    # Data Summary
    total_awards: int
    total_funding: float
    fiscal_years_analyzed: List[int]
    data_completeness_score: float
    
    # Pattern Analysis
    award_size_patterns: Dict[str, Any]
    geographic_patterns: Dict[str, Any]
    recipient_patterns: Dict[str, Any] 
    temporal_patterns: Dict[str, Any]
    success_factors: Dict[str, Any]
    
    # Strategic Intelligence
    competitive_landscape: str  # "low", "medium", "high"
    market_size: str  # "small", "medium", "large"
    funding_stability: float  # 0-1 score
    optimal_award_range: Dict[str, float]
    geographic_advantages: List[str]
    timing_recommendation: str
    
    # Actionable Recommendations
    recommendations: List[str]
    confidence_score: float

class HistoricalFundingAnalyzer:
    """
    Analyzes historical funding patterns using existing USASpending integration
    to provide Standard tier intelligence enhancement.
    """
    
    def __init__(self):
        self.usaspending_client = USASpendingClient()
        self.entity_cache_manager = get_entity_cache_manager()
        self.usaspending_processor = USASpendingFetchProcessor()
        
    async def analyze_opportunity_funding_patterns(
        self, 
        agency_name: str,
        program_keywords: List[str] = None,
        fiscal_years: List[int] = None,
        max_awards: int = 500
    ) -> FundingIntelligence:
        """
        Comprehensive funding pattern analysis for a specific opportunity
        
        Args:
            agency_name: Name of the funding agency (e.g., "Department of Energy")
            program_keywords: Keywords related to the program/opportunity
            fiscal_years: Specific years to analyze (default: last 5 years)
            max_awards: Maximum awards to analyze
            
        Returns:
            Comprehensive funding intelligence report
        """
        logger.info(f"Analyzing funding patterns for {agency_name}, keywords: {program_keywords}")
        
        if fiscal_years is None:
            current_year = datetime.now().year
            fiscal_years = list(range(current_year - 4, current_year + 1))
        
        try:
            # Collect historical awards using existing client with timeout
            historical_awards = await asyncio.wait_for(
                self._collect_historical_awards(
                    agency_name, program_keywords, fiscal_years, max_awards
                ),
                timeout=30.0  # 30 second timeout to prevent hanging
            )
            
            if not historical_awards:
                return self._generate_no_data_report(agency_name, program_keywords)
            
            logger.info(f"Found {len(historical_awards)} historical awards for analysis")
            
            # Perform comprehensive pattern analysis
            patterns = await self._analyze_funding_patterns(historical_awards)
            
            # Generate strategic intelligence
            intelligence = self._generate_strategic_intelligence(patterns, historical_awards)
            
            # Create comprehensive funding intelligence report
            funding_intelligence = FundingIntelligence(
                agency_name=agency_name,
                program_keywords=program_keywords or [],
                analysis_date=datetime.now().isoformat(),
                
                # Data summary
                total_awards=len(historical_awards),
                total_funding=sum(award.award_amount for award in historical_awards),
                fiscal_years_analyzed=fiscal_years,
                data_completeness_score=self._calculate_data_completeness(historical_awards),
                
                # Pattern analysis
                award_size_patterns=patterns["award_size_patterns"],
                geographic_patterns=patterns["geographic_patterns"],
                recipient_patterns=patterns["recipient_patterns"],
                temporal_patterns=patterns["temporal_patterns"],
                success_factors=patterns["success_factors"],
                
                # Strategic intelligence
                competitive_landscape=intelligence["competitive_landscape"],
                market_size=intelligence["market_size"],
                funding_stability=intelligence["funding_stability"],
                optimal_award_range=intelligence["optimal_award_range"],
                geographic_advantages=intelligence["geographic_advantages"],
                timing_recommendation=intelligence["timing_recommendation"],
                
                # Actionable recommendations
                recommendations=intelligence["recommendations"],
                confidence_score=intelligence["confidence_score"]
            )
            
            return funding_intelligence
            
        except asyncio.TimeoutError:
            logger.warning(f"Funding pattern analysis timed out for {agency_name} - using fallback data")
            return self._generate_timeout_report(agency_name, program_keywords)
        except Exception as e:
            logger.error(f"Funding pattern analysis failed: {e}", exc_info=True)
            return self._generate_error_report(agency_name, program_keywords, str(e))
    
    async def _collect_historical_awards(
        self,
        agency_name: str,
        keywords: List[str],
        fiscal_years: List[int],
        max_awards: int
    ) -> List[Dict[str, Any]]:
        """Collect historical awards using existing USASpending client"""
        
        all_awards = []
        
        for fiscal_year in fiscal_years:
            try:
                # Use existing client to get agency awards for specific year
                year_awards = await self.usaspending_client.get_agency_awards(
                    agency_code=agency_name,
                    fiscal_year=fiscal_year,
                    award_types=["02", "03", "04", "05"],  # Grant types
                    max_results=max_awards // len(fiscal_years)  # Distribute across years
                )
                
                if year_awards:
                    # Filter by keywords if provided
                    if keywords:
                        filtered_awards = []
                        for award in year_awards:
                            award_text = f"{award.get('Award Title', '')} {award.get('Award Description', '')}".lower()
                            if any(keyword.lower() in award_text for keyword in keywords):
                                filtered_awards.append(award)
                        all_awards.extend(filtered_awards)
                    else:
                        all_awards.extend(year_awards)
                
                logger.debug(f"Collected {len(year_awards)} awards for FY{fiscal_year}")
                
            except Exception as e:
                logger.warning(f"Failed to collect awards for FY{fiscal_year}: {e}")
                continue
        
        # Deduplicate by Award ID
        unique_awards = {}
        for award in all_awards:
            award_id = award.get("Award ID")
            if award_id and award_id not in unique_awards:
                unique_awards[award_id] = award
        
        return list(unique_awards.values())
    
    async def _analyze_funding_patterns(self, awards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze funding patterns from historical awards"""
        
        return {
            "award_size_patterns": self._analyze_award_sizes(awards),
            "geographic_patterns": self._analyze_geographic_distribution(awards),
            "recipient_patterns": self._analyze_recipient_patterns(awards),
            "temporal_patterns": self._analyze_temporal_patterns(awards),
            "success_factors": self._identify_success_factors(awards)
        }
    
    def _analyze_award_sizes(self, awards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze award size distribution and patterns"""
        amounts = []
        for award in awards:
            amount = award.get("Total Award Amount") or award.get("Award Amount")
            if amount:
                try:
                    amounts.append(float(amount))
                except (ValueError, TypeError):
                    continue
        
        if not amounts:
            return {"error": "No valid award amounts found"}
        
        # Statistical analysis
        stats = {
            "count": len(amounts),
            "total": sum(amounts),
            "min": min(amounts),
            "max": max(amounts),
            "mean": statistics.mean(amounts),
            "median": statistics.median(amounts),
            "std_dev": statistics.stdev(amounts) if len(amounts) > 1 else 0
        }
        
        # Size categorization
        categories = {
            "small": len([a for a in amounts if a < 50000]),      # < $50K
            "medium": len([a for a in amounts if 50000 <= a < 250000]),  # $50K-$250K
            "large": len([a for a in amounts if 250000 <= a < 1000000]), # $250K-$1M
            "major": len([a for a in amounts if a >= 1000000])   # $1M+
        }
        
        # Percentile analysis
        percentiles = {}
        if len(amounts) >= 4:
            quartiles = statistics.quantiles(amounts, n=4)
            percentiles = {
                "p25": quartiles[0],
                "p50": statistics.median(amounts),
                "p75": quartiles[2]
            }
            if len(amounts) >= 10:
                deciles = statistics.quantiles(amounts, n=10)
                percentiles["p90"] = deciles[8]
        
        # Funding concentration analysis
        sorted_amounts = sorted(amounts, reverse=True)
        top_10_percent = max(1, len(amounts) // 10)
        concentration = {
            "top_10_percent_share": sum(sorted_amounts[:top_10_percent]) / sum(amounts) * 100,
            "top_award_share": sorted_amounts[0] / sum(amounts) * 100 if amounts else 0,
            "gini_coefficient": self._calculate_gini_coefficient(amounts)
        }
        
        return {
            "statistics": stats,
            "size_categories": categories,
            "percentiles": percentiles,
            "concentration": concentration
        }
    
    def _analyze_geographic_distribution(self, awards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze geographic distribution of awards"""
        state_counts = defaultdict(int)
        state_funding = defaultdict(float)
        
        for award in awards:
            state = award.get("Place of Performance State", "").strip().upper()
            if not state:
                state = "UNKNOWN"
            
            state_counts[state] += 1
            
            amount = award.get("Total Award Amount") or award.get("Award Amount")
            if amount:
                try:
                    state_funding[state] += float(amount)
                except (ValueError, TypeError):
                    pass
        
        # Top states analysis
        top_states_by_count = sorted(state_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_states_by_funding = sorted(state_funding.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Geographic concentration
        total_awards = sum(state_counts.values())
        total_funding = sum(state_funding.values())
        
        concentration_metrics = {}
        if total_awards > 0 and total_funding > 0:
            top_5_states_awards = sum(count for _, count in top_states_by_count[:5])
            top_5_states_funding = sum(funding for _, funding in top_states_by_funding[:5])
            
            concentration_metrics = {
                "top_5_states_award_share": top_5_states_awards / total_awards * 100,
                "top_5_states_funding_share": top_5_states_funding / total_funding * 100,
                "geographic_diversity": len(state_counts),
                "herfindahl_index": sum((count / total_awards) ** 2 for count in state_counts.values())
            }
        
        return {
            "total_states": len(state_counts),
            "top_states_by_count": dict(top_states_by_count),
            "top_states_by_funding": dict(top_states_by_funding),
            "concentration_metrics": concentration_metrics
        }
    
    def _analyze_recipient_patterns(self, awards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze recipient organization patterns"""
        recipient_counts = defaultdict(int)
        recipient_funding = defaultdict(float)
        recipient_types = {"universities": 0, "nonprofits": 0, "corporations": 0, "government": 0, "other": 0}
        
        # Keywords for organization type classification
        type_keywords = {
            "universities": ["university", "college", "institute of technology", "polytechnic", "school"],
            "nonprofits": ["foundation", "association", "society", "nonprofit", "council", "institute"],
            "corporations": ["inc", "corp", "llc", "ltd", "company", "technologies", "systems"],
            "government": ["department", "agency", "commission", "authority", "county", "city", "state"]
        }
        
        for award in awards:
            recipient = award.get("Recipient Name", "").strip()
            if not recipient:
                continue
                
            recipient_counts[recipient] += 1
            
            # Add funding amount
            amount = award.get("Total Award Amount") or award.get("Award Amount")
            if amount:
                try:
                    recipient_funding[recipient] += float(amount)
                except (ValueError, TypeError):
                    pass
            
            # Classify recipient type
            recipient_lower = recipient.lower()
            classified = False
            
            for org_type, keywords in type_keywords.items():
                if any(keyword in recipient_lower for keyword in keywords):
                    recipient_types[org_type] += 1
                    classified = True
                    break
            
            if not classified:
                recipient_types["other"] += 1
        
        # Calculate metrics
        total_recipients = len(recipient_counts)
        repeat_recipients = len([r for r, count in recipient_counts.items() if count > 1])
        
        # Top recipients
        top_by_count = sorted(recipient_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_by_funding = sorted(recipient_funding.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Type percentages
        total_awards = sum(recipient_types.values())
        type_percentages = {k: (v / total_awards * 100) for k, v in recipient_types.items()} if total_awards > 0 else {}
        
        return {
            "total_recipients": total_recipients,
            "repeat_recipients": repeat_recipients,
            "repeat_recipient_percentage": repeat_recipients / total_recipients * 100 if total_recipients > 0 else 0,
            "top_recipients_by_count": dict(top_by_count),
            "top_recipients_by_funding": dict(top_by_funding),
            "recipient_types": recipient_types,
            "type_percentages": type_percentages,
            "diversity_score": self._calculate_diversity_score(recipient_types)
        }
    
    def _analyze_temporal_patterns(self, awards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal patterns in funding"""
        yearly_data = defaultdict(lambda: {"count": 0, "funding": 0})
        
        for award in awards:
            # Try to extract year from start date or award date
            year = None
            for date_field in ["Start Date", "Award Date", "Action Date"]:
                date_str = award.get(date_field)
                if date_str:
                    try:
                        year = datetime.strptime(str(date_str)[:4], "%Y").year
                        break
                    except (ValueError, TypeError):
                        continue
            
            if not year:
                continue
                
            yearly_data[year]["count"] += 1
            
            amount = award.get("Total Award Amount") or award.get("Award Amount")
            if amount:
                try:
                    yearly_data[year]["funding"] += float(amount)
                except (ValueError, TypeError):
                    pass
        
        if not yearly_data:
            return {"error": "No temporal data available"}
        
        # Calculate trends
        years = sorted(yearly_data.keys())
        year_counts = [yearly_data[year]["count"] for year in years]
        year_funding = [yearly_data[year]["funding"] for year in years]
        
        trends = {
            "count_trend": self._calculate_trend(year_counts),
            "funding_trend": self._calculate_trend(year_funding),
            "stability_score": self._calculate_stability(year_funding),
            "yearly_breakdown": [
                {
                    "year": year,
                    "count": yearly_data[year]["count"],
                    "funding": yearly_data[year]["funding"],
                    "avg_award_size": yearly_data[year]["funding"] / yearly_data[year]["count"] if yearly_data[year]["count"] > 0 else 0
                }
                for year in years
            ]
        }
        
        return trends
    
    def _identify_success_factors(self, awards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify patterns in successful funding recipients"""
        
        # Get award amounts for analysis
        amounts = []
        for award in awards:
            amount = award.get("Total Award Amount") or award.get("Award Amount")
            if amount:
                try:
                    amounts.append((award, float(amount)))
                except (ValueError, TypeError):
                    continue
        
        if not amounts:
            return {"error": "No valid award data for success analysis"}
        
        # Sort by amount to identify high-value awards
        amounts.sort(key=lambda x: x[1], reverse=True)
        
        # Analyze top 25% of awards by value
        top_25_percent = max(1, len(amounts) // 4)
        high_value_awards = [award for award, amount in amounts[:top_25_percent]]
        
        # Extract patterns from high-value awards
        success_patterns = {
            "high_value_threshold": amounts[top_25_percent - 1][1] if top_25_percent <= len(amounts) else 0,
            "common_states": self._get_common_values([a.get("Place of Performance State", "") for a in high_value_awards]),
            "common_recipients": self._get_common_values([a.get("Recipient Name", "") for a in high_value_awards]),
            "common_agencies": self._get_common_values([a.get("Awarding Agency", "") for a in high_value_awards]),
            "average_high_value_award": sum(amount for _, amount in amounts[:top_25_percent]) / top_25_percent if top_25_percent > 0 else 0
        }
        
        return success_patterns
    
    def _generate_strategic_intelligence(self, patterns: Dict[str, Any], awards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate strategic intelligence from patterns"""
        
        # Assess competitive landscape
        recipient_patterns = patterns["recipient_patterns"]
        competitive_landscape = "medium"
        
        if recipient_patterns.get("diversity_score", 0) > 0.7:
            competitive_landscape = "low"
        elif recipient_patterns.get("repeat_recipient_percentage", 0) > 60:
            competitive_landscape = "high"
        
        # Assess market size
        total_funding = sum(float(award.get("Total Award Amount", 0) or 0) for award in awards)
        market_size = "small"
        if total_funding > 100_000_000:
            market_size = "large"
        elif total_funding > 25_000_000:
            market_size = "medium"
        
        # Calculate funding stability
        temporal_patterns = patterns["temporal_patterns"]
        funding_stability = temporal_patterns.get("stability_score", 0.5)
        
        # Determine optimal award range
        award_size_patterns = patterns["award_size_patterns"]
        percentiles = award_size_patterns.get("percentiles", {})
        optimal_award_range = {
            "min": percentiles.get("p25", 50000),
            "optimal": percentiles.get("p50", 100000),
            "max": percentiles.get("p75", 250000)
        }
        
        # Identify geographic advantages
        geographic_patterns = patterns["geographic_patterns"]
        top_states = list(geographic_patterns.get("top_states_by_funding", {}).keys())[:5]
        geographic_advantages = [f"{state}: High funding concentration" for state in top_states if state != "UNKNOWN"]
        
        # Timing recommendation
        timing_trend = temporal_patterns.get("funding_trend", "stable")
        if timing_trend == "increasing":
            timing_recommendation = "favorable"
        elif timing_trend == "decreasing":
            timing_recommendation = "urgent"
        else:
            timing_recommendation = "stable"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(patterns, {
            "competitive_landscape": competitive_landscape,
            "market_size": market_size,
            "optimal_award_range": optimal_award_range,
            "timing_recommendation": timing_recommendation
        })
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(patterns, len(awards))
        
        return {
            "competitive_landscape": competitive_landscape,
            "market_size": market_size,
            "funding_stability": funding_stability,
            "optimal_award_range": optimal_award_range,
            "geographic_advantages": geographic_advantages,
            "timing_recommendation": timing_recommendation,
            "recommendations": recommendations,
            "confidence_score": confidence_score
        }
    
    def _generate_recommendations(self, patterns: Dict[str, Any], intelligence: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Award size recommendations
        award_range = intelligence["optimal_award_range"]
        recommendations.append(
            f"Target award range: ${award_range['min']:,.0f} - ${award_range['max']:,.0f} (median: ${award_range['optimal']:,.0f})"
        )
        
        # Geographic recommendations
        geo_advantages = intelligence.get("geographic_advantages", [])
        if geo_advantages:
            recommendations.append(f"Geographic advantages in: {', '.join([g.split(':')[0] for g in geo_advantages[:3]])}")
        
        # Timing recommendations
        timing = intelligence["timing_recommendation"]
        if timing == "favorable":
            recommendations.append("Funding trend is increasing - excellent timing for applications")
        elif timing == "urgent":
            recommendations.append("Funding trend declining - submit applications urgently")
        else:
            recommendations.append("Stable funding environment - consistent opportunity available")
        
        # Competition recommendations
        competition = intelligence["competitive_landscape"]
        if competition == "low":
            recommendations.append("Low competition environment - strong success probability")
        elif competition == "high":
            recommendations.append("High competition - differentiation strategy essential")
        else:
            recommendations.append("Moderate competition - solid proposal needed for success")
        
        # Success factor recommendations
        success_factors = patterns.get("success_factors", {})
        if success_factors.get("common_states"):
            top_states = list(success_factors["common_states"].keys())[:3]
            recommendations.append(f"Higher success rates in: {', '.join(top_states)}")
        
        return recommendations
    
    # Helper methods
    def _calculate_gini_coefficient(self, values: List[float]) -> float:
        """Calculate Gini coefficient for distribution inequality"""
        if not values or len(values) < 2:
            return 0
        
        sorted_values = sorted(values)
        n = len(values)
        cumsum = sum((i + 1) * v for i, v in enumerate(sorted_values))
        return (2 * cumsum) / (n * sum(values)) - (n + 1) / n
    
    def _calculate_diversity_score(self, categories: Dict[str, int]) -> float:
        """Calculate diversity score using Shannon entropy"""
        total = sum(categories.values())
        if total == 0:
            return 0
        
        import math
        entropy = 0
        for count in categories.values():
            if count > 0:
                proportion = count / total
                entropy -= proportion * math.log(proportion)
        
        max_entropy = math.log(len(categories))
        return entropy / max_entropy if max_entropy > 0 else 0
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate overall trend direction"""
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple linear trend
        n = len(values)
        x = list(range(n))
        
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x_squared = sum(x[i] ** 2 for i in range(n))
        
        if n * sum_x_squared - sum_x ** 2 == 0:
            return "stable"
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x ** 2)
        
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_stability(self, values: List[float]) -> float:
        """Calculate stability score (0-1, higher = more stable)"""
        if len(values) < 2:
            return 1.0
        
        mean_val = statistics.mean(values)
        if mean_val == 0:
            return 0
        
        std_val = statistics.stdev(values)
        cv = std_val / mean_val  # Coefficient of variation
        
        return max(0, 1 - cv)  # Convert to stability score
    
    def _get_common_values(self, values: List[str], top_n: int = 3) -> Dict[str, int]:
        """Get most common values from a list"""
        counts = defaultdict(int)
        for value in values:
            clean_value = value.strip() if value else ""
            if clean_value:
                counts[clean_value] += 1
        
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_n])
    
    def _calculate_data_completeness(self, awards: List[Dict[str, Any]]) -> float:
        """Calculate data completeness score"""
        if not awards:
            return 0
        
        total_fields = 0
        complete_fields = 0
        
        key_fields = ["Award ID", "Recipient Name", "Total Award Amount", "Start Date", "Awarding Agency"]
        
        for award in awards:
            total_fields += len(key_fields)
            for field in key_fields:
                if award.get(field):
                    complete_fields += 1
        
        return complete_fields / total_fields if total_fields > 0 else 0
    
    def _calculate_confidence_score(self, patterns: Dict[str, Any], award_count: int) -> float:
        """Calculate analysis confidence score"""
        base_confidence = 0.5
        
        # Data volume bonus
        if award_count >= 100:
            base_confidence += 0.3
        elif award_count >= 50:
            base_confidence += 0.2
        elif award_count >= 25:
            base_confidence += 0.1
        
        # Data completeness bonus
        temporal_patterns = patterns.get("temporal_patterns", {})
        if not temporal_patterns.get("error"):
            base_confidence += 0.1
        
        # Pattern consistency bonus
        award_patterns = patterns.get("award_size_patterns", {})
        if award_patterns.get("statistics", {}).get("std_dev", 0) > 0:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _generate_no_data_report(self, agency_name: str, keywords: List[str]) -> FundingIntelligence:
        """Generate report when no data is found"""
        return FundingIntelligence(
            agency_name=agency_name,
            program_keywords=keywords or [],
            analysis_date=datetime.now().isoformat(),
            total_awards=0,
            total_funding=0.0,
            fiscal_years_analyzed=[],
            data_completeness_score=0.0,
            award_size_patterns={},
            geographic_patterns={},
            recipient_patterns={},
            temporal_patterns={},
            success_factors={},
            competitive_landscape="unknown",
            market_size="unknown",
            funding_stability=0.0,
            optimal_award_range={"min": 0, "optimal": 0, "max": 0},
            geographic_advantages=[],
            timing_recommendation="unknown",
            recommendations=[
                "No historical data found - may indicate new program",
                "Consider broadening search criteria",
                "Contact program officers for guidance"
            ],
            confidence_score=0.0
        )
    
    def _generate_error_report(self, agency_name: str, keywords: List[str], error: str) -> FundingIntelligence:
        """Generate report when analysis fails"""
        return FundingIntelligence(
            agency_name=agency_name,
            program_keywords=keywords or [],
            analysis_date=datetime.now().isoformat(),
            total_awards=0,
            total_funding=0.0,
            fiscal_years_analyzed=[],
            data_completeness_score=0.0,
            award_size_patterns={},
            geographic_patterns={},
            recipient_patterns={},
            temporal_patterns={},
            success_factors={},
            competitive_landscape="unknown",
            market_size="unknown",
            funding_stability=0.0,
            optimal_award_range={"min": 0, "optimal": 0, "max": 0},
            geographic_advantages=[],
            timing_recommendation="unknown",
            recommendations=[f"Analysis failed: {error}", "Please retry or contact support"],
            confidence_score=0.0
        )

    def _generate_timeout_report(self, agency_name: str, keywords: List[str]) -> FundingIntelligence:
        """Generate report when analysis times out"""
        return FundingIntelligence(
            agency_name=agency_name,
            program_keywords=keywords or [],
            analysis_date=datetime.now().isoformat(),
            total_awards=0,
            total_funding=0.0,
            fiscal_years_analyzed=[],
            data_completeness_score=0.0,
            award_size_patterns={},
            geographic_patterns={},
            recipient_patterns={},
            temporal_patterns={},
            success_factors={},
            competitive_landscape="unknown",
            market_size="unknown",
            funding_stability=0.0,
            optimal_award_range={"min": 0, "optimal": 0, "max": 0},
            geographic_advantages=[],
            timing_recommendation="unknown",
            recommendations=["Analysis timed out due to API delays", "Proceeding with basic analysis"],
            confidence_score=0.3  # Partial confidence for timeout case
        )

# Export main class
__all__ = ["HistoricalFundingAnalyzer", "FundingIntelligence"]