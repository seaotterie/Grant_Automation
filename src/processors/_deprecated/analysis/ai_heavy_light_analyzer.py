#!/usr/bin/env python3
"""
AI-Heavy Light Analyzer - Cost-Effective Screening for ANALYZE Tab

Purpose: Intelligent screening and risk assessment before expensive deep analysis
Model: GPT-5-nano (cost-optimized)
Cost: ~$0.02-0.04 per candidate
Processing: Strategic screening to filter candidates for EXAMINE/APPROACH tabs

Key Features:
- AI Intelligence: Strategic candidate assessment and screening
- Risk Assessment: Compliance, stability, and viability analysis  
- Financial Analysis: AI-enhanced local processing of revenue trends
- Network Analysis: AI-enhanced local relationship mapping

This processor provides the "screening layer" in our cost-efficient funnel:
ANALYZE (screening) → EXAMINE (deep intelligence) → APPROACH (implementation)
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.openai_service import get_openai_service

logger = logging.getLogger(__name__)

# Light Analysis Data Models

class ViabilityLevel(str, Enum):
    """Candidate viability assessment"""
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"
    REJECT = "reject"

class RiskLevel(str, Enum):
    """Risk assessment levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class CompetitionLevel(str, Enum):
    """Competition assessment"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"

class FinancialHealth(str, Enum):
    """Financial stability assessment"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNKNOWN = "unknown"

class LightAnalysis(BaseModel):
    """Screening-level analysis result"""
    opportunity_id: str
    
    # CORE SCREENING RESULTS
    viability_level: ViabilityLevel
    overall_score: float = Field(..., ge=0.0, le=1.0)
    recommendation: str  # "proceed", "proceed_with_caution", "monitor", "reject"
    
    # AI INTELLIGENCE SCREENING
    strategic_fit: float = Field(..., ge=0.0, le=1.0)
    mission_alignment: float = Field(..., ge=0.0, le=1.0)
    opportunity_strength: float = Field(..., ge=0.0, le=1.0)
    preliminary_advantages: List[str] = Field(default_factory=list)
    preliminary_concerns: List[str] = Field(default_factory=list)
    
    # RISK ASSESSMENT
    risk_level: RiskLevel
    compliance_risk: float = Field(..., ge=0.0, le=1.0)
    stability_risk: float = Field(..., ge=0.0, le=1.0)
    capacity_risk: float = Field(..., ge=0.0, le=1.0)
    risk_factors: List[str] = Field(default_factory=list)
    risk_mitigation: List[str] = Field(default_factory=list)
    
    # FINANCIAL ANALYSIS
    financial_health: FinancialHealth
    funding_stability: float = Field(..., ge=0.0, le=1.0)
    financial_transparency: float = Field(..., ge=0.0, le=1.0)
    funding_size_match: float = Field(..., ge=0.0, le=1.0)
    financial_notes: List[str] = Field(default_factory=list)
    
    # NETWORK ANALYSIS
    relationship_potential: float = Field(..., ge=0.0, le=1.0)
    connection_strength: float = Field(..., ge=0.0, le=1.0)
    network_advantages: List[str] = Field(default_factory=list)
    introduction_pathways: List[str] = Field(default_factory=list)
    
    # COMPETITIVE INTELLIGENCE
    competition_level: CompetitionLevel
    competitive_position: float = Field(..., ge=0.0, le=1.0)
    differentiation_potential: float = Field(..., ge=0.0, le=1.0)
    competitive_advantages: List[str] = Field(default_factory=list)
    
    # METADATA
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    processing_time: float = 0.0
    cost_estimate: float = 0.0
    next_step_recommendation: str = ""
    analysis_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class LightAnalysisRequest(BaseModel):
    """Request structure for light analysis"""
    batch_id: str
    profile_context: Dict[str, Any]
    candidates: List[Dict[str, Any]]
    analysis_focus: str = "screening"  # "screening", "risk_focus", "financial_focus"
    cost_budget: float = 0.05
    priority_level: str = "standard"

class LightAnalysisBatchResult(BaseModel):
    """Batch results from light analysis"""
    batch_id: str
    processed_count: int
    processing_time: float
    total_cost: float
    cost_per_candidate: float
    analyses: Dict[str, LightAnalysis]  # opportunity_id -> analysis
    screening_summary: Dict[str, Any]
    recommendations: Dict[str, Any]

class AIHeavyLightAnalyzer(BaseProcessor):
    """AI-Heavy Light processor for cost-effective candidate screening"""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="ai_heavy_light_analyzer",
            description="AI-Heavy Light: Cost-effective screening and risk assessment for ANALYZE tab",
            version="1.0.0",
            dependencies=[],
            estimated_duration=30,
            requires_network=True,
            requires_api_key=True,
            can_run_parallel=True,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Optimized settings for cost-effective screening
        self.batch_size = 8  # Smaller batches for faster processing
        self.model = "gpt-5-nano"  # Cost-effective model
        self.max_tokens = 800  # Moderate token allocation
        self.temperature = 0.3  # Balanced for consistency and insight
        
        # Cost tracking - target $0.02-0.04 per candidate
        self.estimated_cost_per_candidate = 0.03
        self.target_processing_time = 20  # seconds per batch
        
        # Initialize OpenAI service
        self.openai_service = get_openai_service()
        
        # Performance tracking
        self.performance_metrics = {
            "screening_accuracy": 0.0,
            "cost_efficiency": 0.0,
            "processing_speed": 0.0
        }
    
    async def execute(self, request_data: LightAnalysisRequest) -> LightAnalysisBatchResult:
        """Execute light analysis screening"""
        start_time = datetime.now()
        batch_id = request_data.batch_id
        
        logger.info(f"Starting AI-Heavy Light analysis for {len(request_data.candidates)} candidates (batch: {batch_id})")
        
        try:
            # Create screening prompt
            screening_prompt = self._create_screening_prompt(request_data)
            
            # Call OpenAI API
            response = await self._call_openai_api(screening_prompt, request_data)
            
            # Parse response
            analyses = self._parse_screening_response(response, request_data)
            
            # Calculate metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            total_cost = len(request_data.candidates) * self.estimated_cost_per_candidate
            
            # Generate screening summary
            screening_summary = self._generate_screening_summary(analyses)
            recommendations = self._generate_batch_recommendations(analyses)
            
            result = LightAnalysisBatchResult(
                batch_id=batch_id,
                processed_count=len(analyses),
                processing_time=processing_time,
                total_cost=total_cost,
                cost_per_candidate=total_cost / max(len(analyses), 1),
                analyses=analyses,
                screening_summary=screening_summary,
                recommendations=recommendations
            )
            
            logger.info(f"AI-Heavy Light analysis completed: {len(analyses)} candidates processed in {processing_time:.1f}s")
            return result
            
        except Exception as e:
            logger.error(f"AI-Heavy Light analysis failed: {str(e)}")
            # Return fallback result
            return self._create_fallback_result(request_data, str(e))
    
    def _create_screening_prompt(self, request_data: LightAnalysisRequest) -> str:
        """Create comprehensive screening prompt"""
        
        profile_context = request_data.profile_context
        candidates = request_data.candidates[:self.batch_size]  # Limit batch size
        
        prompt = f"""
AI-HEAVY LIGHT ANALYZER - COST-EFFECTIVE CANDIDATE SCREENING

MISSION: Provide intelligent screening analysis to filter candidates for expensive deep analysis.
FOCUS: Strategic assessment, risk evaluation, financial health, and network potential.

ORGANIZATION PROFILE:
Organization: {profile_context.get('organization_name', 'Unknown')}
Mission: {profile_context.get('mission_statement', 'Not specified')}
Focus Areas: {', '.join(profile_context.get('focus_areas', []))}
Geographic Scope: {profile_context.get('geographic_scope', 'Unknown')}
NTEE Codes: {', '.join(profile_context.get('ntee_codes', []))}

CANDIDATES TO ANALYZE:
{json.dumps(candidates, indent=2)}

ANALYSIS FRAMEWORK:

For each candidate, provide comprehensive screening analysis with these components:

1. VIABILITY ASSESSMENT:
   - viability_level: "high", "medium", "low", "reject"
   - overall_score: 0.0-1.0 overall viability score
   - recommendation: "proceed", "proceed_with_caution", "monitor", "reject"

2. AI INTELLIGENCE SCREENING:
   - strategic_fit: 0.0-1.0 strategic alignment score
   - mission_alignment: 0.0-1.0 mission compatibility
   - opportunity_strength: 0.0-1.0 opportunity quality assessment
   - preliminary_advantages: List of strategic advantages
   - preliminary_concerns: List of concerns or challenges

3. RISK ASSESSMENT:
   - risk_level: "low", "moderate", "high", "critical"
   - compliance_risk: 0.0-1.0 regulatory/compliance risk
   - stability_risk: 0.0-1.0 organizational stability risk
   - capacity_risk: 0.0-1.0 organizational capacity risk
   - risk_factors: List of identified risk factors
   - risk_mitigation: List of risk mitigation strategies

4. FINANCIAL ANALYSIS:
   - financial_health: "excellent", "good", "fair", "poor", "unknown"
   - funding_stability: 0.0-1.0 funding source stability
   - financial_transparency: 0.0-1.0 transparency and reporting quality
   - funding_size_match: 0.0-1.0 funding amount appropriateness
   - financial_notes: List of financial observations

5. NETWORK ANALYSIS:
   - relationship_potential: 0.0-1.0 relationship building potential
   - connection_strength: 0.0-1.0 existing connection strength
   - network_advantages: List of network-based advantages
   - introduction_pathways: List of potential introduction routes

6. COMPETITIVE INTELLIGENCE:
   - competition_level: "low", "moderate", "high", "extreme"
   - competitive_position: 0.0-1.0 competitive strength
   - differentiation_potential: 0.0-1.0 differentiation opportunity
   - competitive_advantages: List of competitive advantages

7. METADATA:
   - confidence_level: 0.0-1.0 analysis confidence
   - next_step_recommendation: Specific next step recommendation

RESPONSE FORMAT (JSON only):
{{
  "candidate_1_opportunity_id": {{
    "viability_level": "high",
    "overall_score": 0.85,
    "recommendation": "proceed",
    "strategic_fit": 0.9,
    "mission_alignment": 0.85,
    "opportunity_strength": 0.8,
    "preliminary_advantages": ["Strong mission alignment", "Geographic fit", "Funding size match"],
    "preliminary_concerns": ["High competition", "Application complexity"],
    "risk_level": "moderate",
    "compliance_risk": 0.2,
    "stability_risk": 0.1,
    "capacity_risk": 0.3,
    "risk_factors": ["Competitive landscape", "Capacity requirements"],
    "risk_mitigation": ["Early application", "Partnership development"],
    "financial_health": "good",
    "funding_stability": 0.8,
    "financial_transparency": 0.9,
    "funding_size_match": 0.85,
    "financial_notes": ["Stable funding history", "Transparent reporting"],
    "relationship_potential": 0.7,
    "connection_strength": 0.5,
    "network_advantages": ["Board connections", "Regional presence"],
    "introduction_pathways": ["Board member introduction", "Regional network"],
    "competition_level": "moderate",
    "competitive_position": 0.75,
    "differentiation_potential": 0.8,
    "competitive_advantages": ["Unique approach", "Strong track record"],
    "confidence_level": 0.85,
    "next_step_recommendation": "Proceed to deep analysis with focus on competitive positioning"
  }}
}}

SCREENING OBJECTIVES:
- Identify high-potential candidates for expensive deep analysis
- Flag critical risks early to avoid wasted resources
- Assess financial viability and relationship potential
- Provide clear proceed/don't proceed recommendations
- Optimize resource allocation for maximum ROI

Focus on practical, actionable intelligence that supports strategic funding decisions.

RESPONSE (JSON only):"""
        
        return prompt
    
    async def _call_openai_api(self, prompt: str, request_data: LightAnalysisRequest) -> str:
        """Call OpenAI API for screening analysis"""
        try:
            response = await self.openai_service.create_completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            logger.info(f"AI-Heavy Light API call completed: {self.model}, ~{self.max_tokens} tokens")
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    def _parse_screening_response(self, response: str, request_data: LightAnalysisRequest) -> Dict[str, LightAnalysis]:
        """Parse and validate screening response"""
        analyses = {}
        
        try:
            # Clean and parse JSON response
            cleaned_response = self._clean_json_response(response)
            response_data = json.loads(cleaned_response)
            
            # Process each analysis
            for opportunity_id, analysis_data in response_data.items():
                try:
                    analysis = LightAnalysis(
                        opportunity_id=opportunity_id,
                        **analysis_data
                    )
                    analyses[opportunity_id] = analysis
                    
                except Exception as e:
                    logger.warning(f"Failed to parse analysis for {opportunity_id}: {str(e)}")
                    # Create fallback analysis
                    analyses[opportunity_id] = self._create_fallback_analysis(opportunity_id)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            # Create fallback analyses for all candidates
            for candidate in request_data.candidates:
                opportunity_id = candidate.get('opportunity_id', 'unknown')
                analyses[opportunity_id] = self._create_fallback_analysis(opportunity_id)
        
        return analyses
    
    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response from common formatting issues"""
        try:
            # Remove markdown formatting
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            # Clean whitespace
            response = response.strip()
            
            return response
            
        except Exception as e:
            logger.warning(f"JSON cleaning failed: {str(e)}")
            return response
    
    def _create_fallback_analysis(self, opportunity_id: str) -> LightAnalysis:
        """Create fallback analysis for error cases"""
        return LightAnalysis(
            opportunity_id=opportunity_id,
            viability_level=ViabilityLevel.LOW,
            overall_score=0.3,
            recommendation="monitor",
            strategic_fit=0.3,
            mission_alignment=0.3,
            opportunity_strength=0.3,
            preliminary_advantages=["Requires manual review"],
            preliminary_concerns=["Analysis failed - manual review needed"],
            risk_level=RiskLevel.HIGH,
            compliance_risk=0.8,
            stability_risk=0.8,
            capacity_risk=0.8,
            risk_factors=["Analysis failure"],
            risk_mitigation=["Manual review required"],
            financial_health=FinancialHealth.UNKNOWN,
            funding_stability=0.3,
            financial_transparency=0.3,
            funding_size_match=0.3,
            financial_notes=["Analysis failed"],
            relationship_potential=0.3,
            connection_strength=0.3,
            network_advantages=["Unknown"],
            introduction_pathways=["Manual research needed"],
            competition_level=CompetitionLevel.HIGH,
            competitive_position=0.3,
            differentiation_potential=0.3,
            competitive_advantages=["Unknown"],
            confidence_level=0.1,
            next_step_recommendation="Manual review and analysis required"
        )
    
    def _generate_screening_summary(self, analyses: Dict[str, LightAnalysis]) -> Dict[str, Any]:
        """Generate screening summary statistics"""
        if not analyses:
            return {"error": "No analyses to summarize"}
        
        total_count = len(analyses)
        high_viability = sum(1 for a in analyses.values() if a.viability_level == ViabilityLevel.HIGH)
        proceed_recommendations = sum(1 for a in analyses.values() if a.recommendation == "proceed")
        average_score = sum(a.overall_score for a in analyses.values()) / total_count
        
        risk_distribution = {}
        for risk_level in RiskLevel:
            risk_distribution[risk_level.value] = sum(1 for a in analyses.values() if a.risk_level == risk_level)
        
        return {
            "total_candidates": total_count,
            "high_viability_count": high_viability,
            "proceed_recommendations": proceed_recommendations,
            "average_overall_score": round(average_score, 3),
            "risk_distribution": risk_distribution,
            "top_candidates": [
                {"opportunity_id": aid, "score": a.overall_score, "recommendation": a.recommendation}
                for aid, a in sorted(analyses.items(), key=lambda x: x[1].overall_score, reverse=True)[:5]
            ]
        }
    
    def _generate_batch_recommendations(self, analyses: Dict[str, LightAnalysis]) -> Dict[str, Any]:
        """Generate batch-level recommendations"""
        if not analyses:
            return {"error": "No analyses to process"}
        
        proceed_candidates = [aid for aid, a in analyses.items() if a.recommendation == "proceed"]
        caution_candidates = [aid for aid, a in analyses.items() if a.recommendation == "proceed_with_caution"]
        monitor_candidates = [aid for aid, a in analyses.items() if a.recommendation == "monitor"]
        reject_candidates = [aid for aid, a in analyses.items() if a.recommendation == "reject"]
        
        return {
            "proceed_to_examine": {
                "candidate_ids": proceed_candidates,
                "count": len(proceed_candidates),
                "recommendation": "Proceed to EXAMINE tab for deep analysis"
            },
            "proceed_with_caution": {
                "candidate_ids": caution_candidates,
                "count": len(caution_candidates),
                "recommendation": "Consider for EXAMINE tab with additional risk assessment"
            },
            "monitor_opportunities": {
                "candidate_ids": monitor_candidates,
                "count": len(monitor_candidates),
                "recommendation": "Monitor for future consideration"
            },
            "rejected_candidates": {
                "candidate_ids": reject_candidates,
                "count": len(reject_candidates),
                "recommendation": "Do not proceed - resources better allocated elsewhere"
            },
            "resource_allocation": {
                "high_priority_count": len(proceed_candidates),
                "estimated_examine_cost": len(proceed_candidates) * 0.12,  # $0.12 per EXAMINE analysis
                "estimated_approach_cost": len(proceed_candidates) * 0.18,  # $0.18 per APPROACH analysis
                "total_downstream_cost_estimate": len(proceed_candidates) * 0.30
            }
        }
    
    def _create_fallback_result(self, request_data: LightAnalysisRequest, error_message: str) -> LightAnalysisBatchResult:
        """Create fallback result for error cases"""
        analyses = {}
        for candidate in request_data.candidates:
            opportunity_id = candidate.get('opportunity_id', 'unknown')
            analyses[opportunity_id] = self._create_fallback_analysis(opportunity_id)
        
        return LightAnalysisBatchResult(
            batch_id=request_data.batch_id,
            processed_count=len(analyses),
            processing_time=0.0,
            total_cost=0.0,
            cost_per_candidate=0.0,
            analyses=analyses,
            screening_summary={"error": f"Analysis failed: {error_message}"},
            recommendations={"error": f"Analysis failed: {error_message}"}
        )

# Convenience function for easy import
def get_ai_heavy_light_analyzer() -> AIHeavyLightAnalyzer:
    """Get AI-Heavy Light Analyzer instance"""
    return AIHeavyLightAnalyzer()