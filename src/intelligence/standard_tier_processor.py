"""
Standard Tier Intelligence Processor
Enhanced Grant Intelligence with Historical Funding Analysis

Combines existing AI analysis (Current tier) with historical funding intelligence
to provide Standard tier enhanced analysis for $7.50 cost point.
"""

import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from src.core.data_models import ProcessorResult, OrganizationProfile
from src.intelligence.historical_funding_analyzer import HistoricalFundingAnalyzer, FundingIntelligence
from src.core.entity_cache_manager import get_entity_cache_manager

logger = logging.getLogger(__name__)

@dataclass
class StandardTierResult:
    """Result structure for Standard tier analysis"""
    tier: str = "standard"
    analysis_timestamp: str = ""
    
    # Base Current tier results
    current_tier_analysis: Dict[str, Any] = None
    current_tier_cost: float = 0.0
    
    # Enhanced historical intelligence
    historical_funding_intelligence: Dict[str, Any] = None
    historical_analysis_cost: float = 0.0
    
    # Integrated insights
    enhanced_recommendations: List[str] = None
    confidence_improvement: float = 0.0
    intelligence_score: float = 0.0
    
    # Processing metadata
    total_processing_cost: float = 0.0
    processing_time_seconds: float = 0.0
    data_sources_used: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return asdict(self)

class StandardTierProcessor:
    """
    Standard Tier Intelligence Processor
    
    Enhances existing AI analysis with comprehensive historical funding intelligence
    to provide 10x value increase over Current tier while maintaining cost efficiency.
    """
    
    def __init__(self):
        self.historical_analyzer = HistoricalFundingAnalyzer()
        self.entity_cache_manager = get_entity_cache_manager()
        
        # Cost tracking
        self.estimated_api_cost = 0.94  # Based on planning estimates
        self.cost_tracker = {"current_tier": 0.0, "historical_analysis": 0.0, "integration": 0.0}
        
    async def process_opportunity(
        self,
        profile_id: str,
        opportunity_id: str,
        current_tier_analysis: Optional[Dict[str, Any]] = None
    ) -> StandardTierResult:
        """
        Process opportunity with Standard tier intelligence
        
        Args:
            profile_id: Organization profile ID
            opportunity_id: Grant opportunity ID
            current_tier_analysis: Optional pre-computed Current tier results
            
        Returns:
            Enhanced Standard tier analysis results
        """
        start_time = time.time()
        logger.info(f"Starting Standard tier processing for {profile_id} + {opportunity_id}")
        
        try:
            # Step 1: Get or run Current tier analysis
            if current_tier_analysis is None:
                current_analysis = await self._run_current_tier_analysis(profile_id, opportunity_id)
            else:
                current_analysis = current_tier_analysis
            
            # Step 2: Extract opportunity details for historical analysis
            opportunity_details = await self._extract_opportunity_details(opportunity_id)
            
            # Step 3: Run historical funding analysis
            historical_intelligence = await self._run_historical_funding_analysis(
                opportunity_details.get("agency_name", ""),
                opportunity_details.get("program_keywords", [])
            )
            
            # Step 4: Integrate analyses and generate enhanced insights
            enhanced_analysis = await self._integrate_analyses(
                current_analysis,
                historical_intelligence,
                opportunity_details
            )
            
            processing_time = time.time() - start_time
            
            # Step 5: Build comprehensive result
            result = StandardTierResult(
                analysis_timestamp=datetime.now().isoformat(),
                current_tier_analysis=current_analysis,
                current_tier_cost=self.cost_tracker["current_tier"],
                historical_funding_intelligence=historical_intelligence.__dict__ if historical_intelligence else {},
                historical_analysis_cost=self.cost_tracker["historical_analysis"],
                enhanced_recommendations=enhanced_analysis.get("recommendations", []),
                confidence_improvement=enhanced_analysis.get("confidence_improvement", 0.0),
                intelligence_score=enhanced_analysis.get("intelligence_score", 0.0),
                total_processing_cost=sum(self.cost_tracker.values()),
                processing_time_seconds=processing_time,
                data_sources_used=enhanced_analysis.get("data_sources", [])
            )
            
            logger.info(f"Standard tier processing completed in {processing_time:.2f}s, cost: ${result.total_processing_cost:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Standard tier processing failed: {e}", exc_info=True)
            # Return partial results with error information
            return StandardTierResult(
                analysis_timestamp=datetime.now().isoformat(),
                current_tier_analysis=current_tier_analysis or {},
                enhanced_recommendations=[f"Analysis partially failed: {str(e)}"],
                processing_time_seconds=time.time() - start_time,
                data_sources_used=["error"]
            )
    
    async def _run_current_tier_analysis(self, profile_id: str, opportunity_id: str) -> Dict[str, Any]:
        """Run Current tier analysis using existing system"""
        logger.debug("Running Current tier analysis")
        
        try:
            # This would integrate with the existing AI processor system
            # For now, simulate the Current tier analysis structure
            # In real implementation, this would call the existing 4-stage AI analysis
            
            self.cost_tracker["current_tier"] = 0.19  # Known cost from existing system
            
            # Simulate Current tier results structure
            # This would be replaced with actual integration to existing AI processors
            current_results = {
                "strategic_fit_score": 0.85,
                "financial_viability_score": 0.90,
                "operational_readiness_score": 0.80,
                "success_probability": 0.78,
                "risk_assessment": {
                    "competition_risk": "medium",
                    "technical_risk": "medium",
                    "timeline_risk": "low"
                },
                "implementation_roadmap": {
                    "estimated_hours": 120,
                    "timeline_weeks": 8,
                    "resource_requirements": ["project_manager", "grant_writer"]
                },
                "recommendation": "proceed",
                "confidence": 0.85
            }
            
            logger.debug("Current tier analysis completed")
            return current_results
            
        except Exception as e:
            logger.warning(f"Current tier analysis failed: {e}")
            self.cost_tracker["current_tier"] = 0.0
            return {"error": f"Current tier analysis failed: {str(e)}"}
    
    async def _extract_opportunity_details(self, opportunity_id: str) -> Dict[str, Any]:
        """Extract opportunity details for historical analysis"""
        logger.debug(f"Extracting opportunity details for {opportunity_id}")
        
        try:
            # This would integrate with existing opportunity data
            # For now, simulate based on test data structure
            
            # In real implementation, this would query the entity cache or opportunity database
            opportunity_details = {
                "agency_name": "Department of Energy",
                "agency_code": "DOE",
                "program_keywords": ["environmental", "sustainability", "energy"],
                "opportunity_type": "government_grant",
                "estimated_award_range": {"min": 50000, "max": 500000}
            }
            
            logger.debug(f"Extracted opportunity details: {opportunity_details}")
            return opportunity_details
            
        except Exception as e:
            logger.warning(f"Failed to extract opportunity details: {e}")
            return {
                "agency_name": "Unknown Agency",
                "program_keywords": [],
                "opportunity_type": "unknown"
            }
    
    async def _run_historical_funding_analysis(
        self,
        agency_name: str,
        program_keywords: List[str]
    ) -> Optional[FundingIntelligence]:
        """Run historical funding pattern analysis"""
        logger.debug(f"Running historical funding analysis for {agency_name}")
        
        try:
            self.cost_tracker["historical_analysis"] = 0.75  # Estimated cost for API calls and processing
            
            # Use the HistoricalFundingAnalyzer
            historical_intelligence = await self.historical_analyzer.analyze_opportunity_funding_patterns(
                agency_name=agency_name,
                program_keywords=program_keywords,
                fiscal_years=None,  # Use default (last 5 years)
                max_awards=200  # Reasonable limit for Standard tier
            )
            
            logger.info(f"Historical analysis found {historical_intelligence.total_awards} awards, "
                       f"${historical_intelligence.total_funding:,.0f} total funding")
            
            return historical_intelligence
            
        except Exception as e:
            logger.warning(f"Historical funding analysis failed: {e}")
            self.cost_tracker["historical_analysis"] = 0.0
            return None
    
    async def _integrate_analyses(
        self,
        current_analysis: Dict[str, Any],
        historical_intelligence: Optional[FundingIntelligence],
        opportunity_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Integrate Current tier analysis with historical intelligence"""
        logger.debug("Integrating analyses for enhanced insights")
        
        try:
            enhanced_insights = {
                "recommendations": [],
                "confidence_improvement": 0.0,
                "intelligence_score": 0.0,
                "data_sources": ["current_ai_analysis"]
            }
            
            # Base recommendations from Current tier
            current_recommendations = []
            if current_analysis.get("recommendation") == "proceed":
                current_recommendations.append("Current AI analysis recommends proceeding with this opportunity")
            
            current_confidence = current_analysis.get("confidence", 0.0)
            
            if historical_intelligence and historical_intelligence.total_awards > 0:
                enhanced_insights["data_sources"].append("usaspending_historical_data")
                
                # Historical intelligence insights
                historical_recommendations = historical_intelligence.recommendations
                
                # Award size optimization
                optimal_range = historical_intelligence.optimal_award_range
                if optimal_range["optimal"] > 0:
                    current_recommendations.append(
                        f"Historical data suggests optimal award range: ${optimal_range['min']:,.0f} - ${optimal_range['max']:,.0f}"
                    )
                
                # Geographic insights
                if historical_intelligence.geographic_advantages:
                    geo_info = historical_intelligence.geographic_advantages[0]
                    current_recommendations.append(f"Geographic advantage identified: {geo_info}")
                
                # Competition insights
                competition = historical_intelligence.competitive_landscape
                if competition == "low":
                    current_recommendations.append("Low competition environment identified - strong success probability")
                elif competition == "high":
                    current_recommendations.append("High competition detected - differentiation strategy essential")
                
                # Timing insights
                timing = historical_intelligence.timing_recommendation
                if timing == "favorable":
                    current_recommendations.append("Favorable funding timing based on historical trends")
                elif timing == "urgent":
                    current_recommendations.append("Declining funding trend - urgent application recommended")
                
                # Market size insights
                market_size = historical_intelligence.market_size
                funding_info = f"Market analysis: {market_size} funding market with ${historical_intelligence.total_funding:,.0f} in recent awards"
                current_recommendations.append(funding_info)
                
                # Calculate confidence improvement
                historical_confidence = historical_intelligence.confidence_score
                if historical_confidence > 0.5:
                    confidence_boost = min(0.15, historical_confidence * 0.2)  # Up to 15% boost
                    enhanced_insights["confidence_improvement"] = confidence_boost
                
                # Calculate intelligence score (0-1, measures enhancement value)
                intelligence_factors = [
                    historical_intelligence.total_awards / 100,  # Data volume factor
                    historical_intelligence.confidence_score,    # Data quality factor
                    len(historical_intelligence.recommendations) / 5,  # Insight richness factor
                    1.0 if historical_intelligence.total_funding > 10_000_000 else 0.5  # Market size factor
                ]
                enhanced_insights["intelligence_score"] = min(1.0, sum(intelligence_factors) / len(intelligence_factors))
                
                # Combine recommendations
                enhanced_insights["recommendations"] = current_recommendations + historical_recommendations
            else:
                # No historical data available
                enhanced_insights["recommendations"] = current_recommendations + [
                    "Limited historical funding data available for this opportunity",
                    "Consider this as potentially new or specialized program area"
                ]
                enhanced_insights["intelligence_score"] = 0.3  # Lower score due to limited enhancement
            
            # Final confidence calculation
            base_confidence = current_confidence
            confidence_improvement = enhanced_insights["confidence_improvement"]
            final_confidence = min(0.95, base_confidence + confidence_improvement)
            
            enhanced_insights["final_confidence"] = final_confidence
            enhanced_insights["base_confidence"] = base_confidence
            
            logger.info(f"Analysis integration completed. Intelligence score: {enhanced_insights['intelligence_score']:.2f}, "
                       f"Confidence improvement: {confidence_improvement:.2f}")
            
            return enhanced_insights
            
        except Exception as e:
            logger.error(f"Analysis integration failed: {e}")
            return {
                "recommendations": ["Analysis integration failed - using basic recommendations"],
                "confidence_improvement": 0.0,
                "intelligence_score": 0.0,
                "data_sources": ["error"],
                "error": str(e)
            }
    
    def calculate_value_metrics(self, result: StandardTierResult) -> Dict[str, Any]:
        """Calculate value metrics for Standard tier vs Current tier"""
        try:
            # Base metrics
            current_cost = 0.75  # Current tier price
            standard_cost = 7.50  # Standard tier price
            
            # Intelligence enhancement metrics
            intelligence_score = result.intelligence_score
            confidence_improvement = result.confidence_improvement
            
            # Data source diversity
            data_sources = len(result.data_sources_used) if result.data_sources_used else 1
            
            # Calculate value scores
            value_metrics = {
                "cost_comparison": {
                    "current_tier_cost": current_cost,
                    "standard_tier_cost": standard_cost,
                    "cost_multiplier": standard_cost / current_cost
                },
                "intelligence_enhancement": {
                    "intelligence_score": intelligence_score,
                    "confidence_improvement": confidence_improvement,
                    "data_source_diversity": data_sources,
                    "enhancement_factor": intelligence_score * 10  # 0-10 scale
                },
                "value_per_dollar": {
                    "current_tier_value": 1.0,  # Baseline
                    "standard_tier_value": 1.0 + (intelligence_score * 5),  # Up to 6x value
                    "roi_improvement": intelligence_score * 5
                },
                "decision_support_quality": {
                    "recommendation_count": len(result.enhanced_recommendations) if result.enhanced_recommendations else 0,
                    "historical_data_available": result.historical_funding_intelligence is not None,
                    "comprehensive_analysis": intelligence_score > 0.5
                }
            }
            
            return value_metrics
            
        except Exception as e:
            logger.error(f"Value metrics calculation failed: {e}")
            return {"error": "Value metrics calculation failed"}
    
    def get_cost_breakdown(self) -> Dict[str, float]:
        """Get detailed cost breakdown for Standard tier processing"""
        return {
            "current_tier_api_cost": self.cost_tracker["current_tier"],
            "historical_analysis_cost": self.cost_tracker["historical_analysis"],
            "integration_processing": self.cost_tracker.get("integration", 0.0),
            "total_api_cost": sum(self.cost_tracker.values()),
            "platform_cost": 6.56,  # Infrastructure and processing costs
            "total_standard_tier_cost": sum(self.cost_tracker.values()) + 6.56
        }

# Factory function for processor registration
def create_standard_tier_processor() -> StandardTierProcessor:
    """Factory function to create Standard tier processor"""
    return StandardTierProcessor()

# Export main class
__all__ = ["StandardTierProcessor", "StandardTierResult"]