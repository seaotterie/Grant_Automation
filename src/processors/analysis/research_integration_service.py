"""
Research Integration Service - Phase 1.5: Three-Way Cross-System Research Integration

Purpose: Orchestrate research flow across AI-Lite → Deep Research → Dossier Builder
Functionality: Bridge research findings between ANALYZE → EXAMINE → APPROACH tabs
Enhancement: Enable seamless three-way research flow across the complete grant research workflow

Phase 1.5 Enhanced Features:
- AI-Lite to Deep Research handoff (ANALYZE → EXAMINE)
- Deep Research to Dossier Builder handoff (EXAMINE → APPROACH)
- Three-way research quality assessment and validation
- Cross-system data enrichment with context preservation
- Evidence-based integration across all workflow stages
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from .ai_lite_scorer import AILiteAnalysis, ResearchReport, WebsiteIntelligence, FactExtraction, CompetitiveAnalysis
from .ai_heavy_researcher import AILiteResults, TargetPreliminaryData
from .ai_heavy_deep_researcher import (
    DeepResearchIntelligenceReport, RelationshipIntelligence, CompetitiveIntelligence,
    FinancialIntelligence, StrategicPartnershipIntelligence, MarketIntelligence, RiskIntelligence
)

logger = logging.getLogger(__name__)


class ResearchHandoffData(BaseModel):
    """Research data handoff from AI-Lite to AI-Heavy"""
    opportunity_id: str
    ai_lite_analysis: AILiteAnalysis
    research_quality_score: float = Field(ge=0.0, le=1.0, description="Quality of research data")
    handoff_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    
class DeepResearchHandoffData(BaseModel):
    """Research data handoff from Deep Research to Dossier Builder"""
    opportunity_id: str
    deep_research_report: DeepResearchIntelligenceReport
    intelligence_quality_score: float = Field(ge=0.0, le=1.0, description="Quality of intelligence data")
    handoff_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class EnhancedTargetData(BaseModel):
    """Enhanced target data with AI-Lite research integration"""
    base_target_data: TargetPreliminaryData
    ai_lite_research_enrichment: Optional[Dict[str, Any]] = None
    research_confidence_boost: float = 0.0

class ThreeWayIntegrationContext(BaseModel):
    """Complete three-way integration context across all tabs"""
    opportunity_id: str
    ai_lite_handoff: Optional[ResearchHandoffData] = None
    deep_research_handoff: Optional[DeepResearchHandoffData] = None
    integration_completeness_score: float = 0.0
    workflow_stage: str = "analyze"  # analyze -> examine -> approach
    context_preservation_metadata: Dict[str, Any] = Field(default_factory=dict)
    

class ResearchIntegrationService:
    """Service for integrating research outputs across AI processors with three-way handoff"""
    
    def __init__(self):
        self.handoff_cache: Dict[str, ResearchHandoffData] = {}
        self.deep_research_handoff_cache: Dict[str, DeepResearchHandoffData] = {}
        self.three_way_integration_cache: Dict[str, ThreeWayIntegrationContext] = {}
        self.integration_enabled = True
        self.three_way_integration_enabled = True
        
    def create_research_handoff(self, opportunity_id: str, ai_lite_analysis: AILiteAnalysis) -> ResearchHandoffData:
        """Create research handoff data from AI-Lite to AI-Heavy"""
        
        # Calculate research quality score based on available research components
        quality_score = self._calculate_research_quality_score(ai_lite_analysis)
        
        handoff_data = ResearchHandoffData(
            opportunity_id=opportunity_id,
            ai_lite_analysis=ai_lite_analysis,
            research_quality_score=quality_score
        )
        
        # Cache for potential reuse
        self.handoff_cache[opportunity_id] = handoff_data
        
        logger.info(f"Created research handoff for {opportunity_id} with quality score {quality_score:.2f}")
        
        # Initialize three-way integration context
        self._initialize_three_way_integration_context(opportunity_id, handoff_data)
        
        return handoff_data
    
    def create_deep_research_handoff(
        self, 
        opportunity_id: str, 
        deep_research_report: DeepResearchIntelligenceReport
    ) -> DeepResearchHandoffData:
        """Create research handoff data from Deep Research to Dossier Builder"""
        
        # Calculate intelligence quality score
        intelligence_quality_score = self._calculate_intelligence_quality_score(deep_research_report)
        
        handoff_data = DeepResearchHandoffData(
            opportunity_id=opportunity_id,
            deep_research_report=deep_research_report,
            intelligence_quality_score=intelligence_quality_score
        )
        
        # Cache for integration
        self.deep_research_handoff_cache[opportunity_id] = handoff_data
        
        # Update three-way integration context
        self._update_three_way_integration_context(opportunity_id, deep_research_handoff=handoff_data)
        
        logger.info(f"Created deep research handoff for {opportunity_id} with intelligence quality score {intelligence_quality_score:.2f}")
        return handoff_data
    
    def get_complete_integration_context(self, opportunity_id: str) -> Optional[ThreeWayIntegrationContext]:
        """Get complete three-way integration context for an opportunity"""
        return self.three_way_integration_cache.get(opportunity_id)
    
    def _initialize_three_way_integration_context(
        self, 
        opportunity_id: str, 
        ai_lite_handoff: ResearchHandoffData
    ):
        """Initialize three-way integration context with AI-Lite data"""
        context = ThreeWayIntegrationContext(
            opportunity_id=opportunity_id,
            ai_lite_handoff=ai_lite_handoff,
            workflow_stage="analyze",
            integration_completeness_score=0.33,  # 1/3 complete
            context_preservation_metadata={
                "ai_lite_research_quality": ai_lite_handoff.research_quality_score,
                "ai_lite_research_components": self._extract_ai_lite_components(ai_lite_handoff.ai_lite_analysis)
            }
        )
        
        self.three_way_integration_cache[opportunity_id] = context
        
    def _update_three_way_integration_context(
        self,
        opportunity_id: str,
        deep_research_handoff: Optional[DeepResearchHandoffData] = None,
        workflow_stage: Optional[str] = None
    ):
        """Update three-way integration context with new data"""
        context = self.three_way_integration_cache.get(opportunity_id)
        if not context:
            return
        
        if deep_research_handoff:
            context.deep_research_handoff = deep_research_handoff
            context.workflow_stage = "examine"
            context.integration_completeness_score = 0.67  # 2/3 complete
            context.context_preservation_metadata.update({
                "deep_research_intelligence_quality": deep_research_handoff.intelligence_quality_score,
                "deep_research_intelligence_components": self._extract_deep_research_components(deep_research_handoff.deep_research_report)
            })
        
        if workflow_stage:
            context.workflow_stage = workflow_stage
            if workflow_stage == "approach":
                context.integration_completeness_score = 1.0  # Complete
    
    def _extract_ai_lite_components(self, ai_lite_analysis: AILiteAnalysis) -> List[str]:
        """Extract available AI-Lite research components"""
        components = []
        if ai_lite_analysis.research_report:
            components.append("research_report")
        if ai_lite_analysis.website_intelligence:
            components.append("website_intelligence")
        if ai_lite_analysis.fact_extraction:
            components.append("fact_extraction")
        if ai_lite_analysis.competitive_analysis:
            components.append("competitive_analysis")
        return components
    
    def _extract_deep_research_components(self, deep_research_report: DeepResearchIntelligenceReport) -> List[str]:
        """Extract available deep research intelligence components"""
        components = []
        if deep_research_report.relationship_intelligence:
            components.append("relationship_intelligence")
        if deep_research_report.competitive_intelligence:
            components.append("competitive_intelligence")
        if deep_research_report.financial_intelligence:
            components.append("financial_intelligence")
        if deep_research_report.strategic_partnership_intelligence:
            components.append("strategic_partnership_intelligence")
        if deep_research_report.market_intelligence:
            components.append("market_intelligence")
        if deep_research_report.risk_intelligence:
            components.append("risk_intelligence")
        return components
    
    def _calculate_intelligence_quality_score(self, deep_research_report: DeepResearchIntelligenceReport) -> float:
        """Calculate intelligence quality score for deep research"""
        base_score = 0.3
        quality_score = base_score
        
        # Intelligence confidence and completeness
        quality_score += deep_research_report.intelligence_confidence_score * 0.3
        quality_score += deep_research_report.research_completeness_score * 0.2
        
        # Actionable insights bonus
        if deep_research_report.actionable_insights_count > 10:
            quality_score += 0.1
        elif deep_research_report.actionable_insights_count > 5:
            quality_score += 0.05
        
        # Intelligence component completeness
        available_components = len(self._extract_deep_research_components(deep_research_report))
        component_bonus = min(available_components * 0.02, 0.12)  # Up to 6 components
        quality_score += component_bonus
        
        return min(quality_score, 1.0)
    
    def integrate_ai_lite_research_to_ai_heavy_input(
        self, 
        opportunity_id: str, 
        ai_lite_analysis: AILiteAnalysis
    ) -> AILiteResults:
        """Convert AI-Lite analysis to AI-Heavy input format"""
        
        # Create enhanced AI-Lite results for AI-Heavy consumption
        enhanced_results = AILiteResults(
            compatibility_score=ai_lite_analysis.compatibility_score,
            strategic_value=ai_lite_analysis.strategic_value.value,
            risk_assessment=[risk for risk in ai_lite_analysis.risk_assessment],
            priority_rank=ai_lite_analysis.priority_rank,
            funding_likelihood=ai_lite_analysis.funding_likelihood,
            strategic_rationale=ai_lite_analysis.strategic_rationale,
            action_priority=ai_lite_analysis.action_priority.value
        )
        
        logger.info(f"Integrated AI-Lite research for {opportunity_id} into AI-Heavy input format")
        return enhanced_results
    
    def enrich_target_data_with_research(
        self,
        base_target_data: TargetPreliminaryData,
        ai_lite_analysis: AILiteAnalysis
    ) -> EnhancedTargetData:
        """Enrich target data with AI-Lite research findings"""
        
        enrichment_data = {}
        confidence_boost = 0.0
        
        # Extract research enrichments if available
        if ai_lite_analysis.research_mode_enabled and ai_lite_analysis.research_report:
            research = ai_lite_analysis.research_report
            enrichment_data.update({
                "research_executive_summary": research.executive_summary,
                "research_opportunity_overview": research.opportunity_overview,
                "research_funding_details": research.funding_details,
                "research_strategic_considerations": research.strategic_considerations,
                "research_decision_factors": research.decision_factors
            })
            confidence_boost += 0.2
        
        if ai_lite_analysis.website_intelligence:
            web_intel = ai_lite_analysis.website_intelligence
            enrichment_data.update({
                "website_key_contacts": web_intel.key_contacts,
                "website_application_process": web_intel.application_process_summary,
                "website_eligibility_highlights": web_intel.eligibility_highlights
            })
            confidence_boost += 0.1
        
        if ai_lite_analysis.fact_extraction:
            facts = ai_lite_analysis.fact_extraction
            enrichment_data.update({
                "facts_award_amount_range": facts.award_amount_range,
                "facts_geographic_eligibility": facts.geographic_eligibility,
                "facts_organizational_requirements": facts.organizational_requirements,
                "facts_reporting_requirements": facts.reporting_requirements
            })
            confidence_boost += 0.1
        
        if ai_lite_analysis.competitive_analysis:
            comp_analysis = ai_lite_analysis.competitive_analysis
            enrichment_data.update({
                "competitive_likely_competitors": comp_analysis.likely_competitors,
                "competitive_advantages": comp_analysis.competitive_advantages,
                "competitive_success_factors": comp_analysis.success_probability_factors
            })
            confidence_boost += 0.15
        
        enhanced_target_data = EnhancedTargetData(
            base_target_data=base_target_data,
            ai_lite_research_enrichment=enrichment_data if enrichment_data else None,
            research_confidence_boost=min(confidence_boost, 0.5)  # Cap at 0.5
        )
        
        logger.info(f"Enhanced target data with {len(enrichment_data)} research enrichments, "
                   f"confidence boost: {confidence_boost:.2f}")
        
        return enhanced_target_data
    
    def create_evidence_based_scoring_summary(self, ai_lite_analysis: AILiteAnalysis) -> Dict[str, Any]:
        """Create evidence-based scoring summary for decision support"""
        
        summary = {
            "scoring_summary": {
                "compatibility_score": ai_lite_analysis.compatibility_score,
                "funding_likelihood": ai_lite_analysis.funding_likelihood,
                "strategic_value": ai_lite_analysis.strategic_value.value,
                "confidence_level": ai_lite_analysis.confidence_level,
                "priority_rank": ai_lite_analysis.priority_rank
            },
            "risk_factors": ai_lite_analysis.risk_assessment,
            "recommended_action": ai_lite_analysis.action_priority.value,
            "strategic_rationale": ai_lite_analysis.strategic_rationale,
            "evidence_quality": "high" if ai_lite_analysis.research_mode_enabled else "standard"
        }
        
        # Add research evidence if available
        if ai_lite_analysis.research_mode_enabled:
            evidence = {}
            if ai_lite_analysis.research_report:
                evidence["executive_summary"] = ai_lite_analysis.research_report.executive_summary
                evidence["key_decision_factors"] = ai_lite_analysis.research_report.decision_factors
            
            if ai_lite_analysis.competitive_analysis:
                evidence["competitive_positioning"] = {
                    "likely_competitors": ai_lite_analysis.competitive_analysis.likely_competitors,
                    "our_advantages": ai_lite_analysis.competitive_analysis.competitive_advantages,
                    "differentiation_strategies": ai_lite_analysis.competitive_analysis.differentiation_strategies
                }
            
            if evidence:
                summary["research_evidence"] = evidence
        
        return summary
    
    def _calculate_research_quality_score(self, ai_lite_analysis: AILiteAnalysis) -> float:
        """Calculate research quality score based on available research components"""
        
        base_score = 0.3  # Base score for scoring analysis
        quality_score = base_score
        
        # Research mode enabled
        if ai_lite_analysis.research_mode_enabled:
            quality_score += 0.2
        
        # Research report quality
        if ai_lite_analysis.research_report:
            research = ai_lite_analysis.research_report
            if len(research.executive_summary) > 100:
                quality_score += 0.1
            if len(research.eligibility_analysis) > 2:
                quality_score += 0.1
            if len(research.strategic_considerations) > 1:
                quality_score += 0.1
        
        # Website intelligence quality
        if ai_lite_analysis.website_intelligence:
            web_intel = ai_lite_analysis.website_intelligence
            if len(web_intel.key_contacts) > 0:
                quality_score += 0.1
            if web_intel.application_process_summary:
                quality_score += 0.05
        
        # Fact extraction quality
        if ai_lite_analysis.fact_extraction:
            facts = ai_lite_analysis.fact_extraction
            if facts.award_amount_range:
                quality_score += 0.05
            if len(facts.organizational_requirements) > 0:
                quality_score += 0.05
        
        # Competitive analysis quality
        if ai_lite_analysis.competitive_analysis:
            comp = ai_lite_analysis.competitive_analysis
            if len(comp.likely_competitors) > 0:
                quality_score += 0.1
            if len(comp.competitive_advantages) > 0:
                quality_score += 0.05
        
        # Confidence level bonus
        confidence_bonus = ai_lite_analysis.confidence_level * 0.1
        quality_score += confidence_bonus
        
        return min(quality_score, 1.0)  # Cap at 1.0
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get integration service status with three-way integration capabilities"""
        return {
            "service_name": "research_integration_service",
            "version": "1.5.0",  # Phase 1.5 Enhancement
            "integration_enabled": self.integration_enabled,
            "three_way_integration_enabled": self.three_way_integration_enabled,
            "cached_handoffs": {
                "ai_lite_handoffs": len(self.handoff_cache),
                "deep_research_handoffs": len(self.deep_research_handoff_cache),
                "three_way_integrations": len(self.three_way_integration_cache)
            },
            "workflow_integration": {
                "analyze_to_examine": "AI-Lite → Deep Research handoff",
                "examine_to_approach": "Deep Research → Dossier Builder handoff",
                "three_way_orchestration": "Complete workflow context preservation"
            },
            "capabilities": [
                "AI-Lite to Deep Research handoff (ANALYZE → EXAMINE)",
                "Deep Research to Dossier Builder handoff (EXAMINE → APPROACH)",
                "Three-way research quality assessment and validation",
                "Cross-system data enrichment with context preservation",
                "Evidence-based integration across all workflow stages",
                "Complete integration context management"
            ],
            "status": "ready"
        }


# Global integration service instance
_integration_service_instance = None


def get_research_integration_service() -> ResearchIntegrationService:
    """Get the global research integration service instance"""
    global _integration_service_instance
    if _integration_service_instance is None:
        _integration_service_instance = ResearchIntegrationService()
    return _integration_service_instance


# Export classes and service
__all__ = [
    "ResearchIntegrationService",
    "ResearchHandoffData", 
    "DeepResearchHandoffData",
    "EnhancedTargetData",
    "ThreeWayIntegrationContext",
    "get_research_integration_service"
]