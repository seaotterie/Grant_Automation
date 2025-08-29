"""
AI Service Manager - Unified processing for AI Lite and AI Heavy systems

Purpose: Coordinate between AI Lite batch analysis and AI Heavy deep research
Features:
- Request/response packet processing for both AI tiers
- Data transformation between frontend and AI processors
- Cost tracking and budget management
- Progress monitoring and status reporting
- Integration bridge between existing data models and new AI packets
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field

from .ai_lite_unified_processor import (
    AILiteUnifiedProcessor, UnifiedRequest, ComprehensiveAnalysis, UnifiedBatchResult,
    ValidationResult, StrategicValue, ActionPriority
)
from .ai_heavy_researcher import (
    AIHeavyDossierBuilder, AIHeavyRequest, AIHeavyResult,
    ResearchMetadata, ContextData, ContextProfileData, AILiteResults,
    TargetPreliminaryData, ResearchFocus, AnalysisDepth, Priority
)

logger = logging.getLogger(__name__)

# Service management models

class ProcessingStatus(BaseModel):
    """AI processing status tracking"""
    request_id: str
    processing_type: str  # "ai_lite" or "ai_heavy"
    status: str  # "pending", "processing", "completed", "failed"
    progress_percentage: float = 0.0
    start_time: datetime
    estimated_completion: Optional[datetime] = None
    cost_estimate: float = 0.0
    cost_actual: Optional[float] = None

class AIServiceManager:
    """Unified AI service management for both Lite and Heavy tiers"""
    
    def __init__(self):
        self.ai_lite_processor = AILiteUnifiedProcessor()
        self.ai_heavy_processor = AIHeavyDossierBuilder()
        self.active_requests: Dict[str, ProcessingStatus] = {}
        
        # Cost tracking
        self.total_session_cost = 0.0
        self.request_history: List[Dict[str, Any]] = []
        
    # AI LITE PROCESSING METHODS
    
    def prepare_ai_lite_request(self, frontend_data: Dict[str, Any]) -> UnifiedRequest:
        """Transform frontend opportunity data into AI Lite request packet"""
        try:
            # Extract profile context from frontend data
            profile_data = frontend_data.get("selected_profile", {})
            candidates_data = frontend_data.get("candidates", [])
            
            # Generate unified request
            batch_id = f"ai_lite_unified_{int(datetime.now().timestamp())}"
            
            # Build profile context dictionary  
            profile_context = {
                "organization_name": profile_data.get("name", "[Organization Name Missing]"),
                "mission_statement": profile_data.get("mission", "Mission not specified"),
                "focus_areas": profile_data.get("focus_areas", []),
                "ntee_codes": profile_data.get("ntee_codes", []),
                "government_criteria": profile_data.get("government_criteria", []),
                "keywords": profile_data.get("keywords", []),
                "geographic_scope": profile_data.get("geographic_scope", "National")
            }
            
            # Transform candidates data to dictionary format
            candidates = []
            for candidate in candidates_data:
                candidate_dict = {
                    "opportunity_id": candidate.get("opportunity_id", "unknown"),
                    "organization_name": candidate.get("organization_name", "Unknown"),
                    "source_type": candidate.get("source_type", "Unknown"),
                    "description": candidate.get("description", "No description available"),
                    "funding_amount": candidate.get("funding_amount"),
                    "application_deadline": candidate.get("application_deadline"),
                    "geographic_location": candidate.get("geographic_location"),
                    "current_score": candidate.get("combined_score", 0.0)
                }
                candidates.append(candidate_dict)
            
            request = UnifiedRequest(
                batch_id=batch_id,
                profile_context=profile_context,
                candidates=candidates,
                analysis_mode="comprehensive",
                cost_budget=frontend_data.get("cost_limit", 0.01),
                priority_level="standard"
            )
            
            logger.info(f"Prepared AI Lite request for {len(candidates)} candidates")
            return request
            
        except Exception as e:
            logger.error(f"Failed to prepare AI Lite request: {str(e)}")
            raise
    
    async def execute_ai_lite_analysis(self, frontend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AI Lite analysis and return formatted results"""
        try:
            # Prepare request packet
            request = self.prepare_ai_lite_request(frontend_data)
            batch_id = request.request_metadata.batch_id
            
            # Track request status
            status = ProcessingStatus(
                request_id=batch_id,
                processing_type="ai_lite",
                status="processing",
                start_time=datetime.now(),
                cost_estimate=len(request.candidates) * self.ai_lite_processor.estimated_cost_per_candidate
            )
            self.active_requests[batch_id] = status
            
            # Execute AI Lite analysis
            result = await self.ai_lite_processor.execute(request)
            
            # Update status
            status.status = "completed"
            status.cost_actual = result.batch_results.total_cost
            self.total_session_cost += result.batch_results.total_cost
            
            # Transform result back to frontend format
            frontend_result = self.format_ai_lite_result(result)
            
            # Log to history
            self.request_history.append({
                "type": "ai_lite",
                "batch_id": batch_id,
                "candidates_count": result.batch_results.processed_count,
                "cost": result.batch_results.total_cost,
                "processing_time": result.batch_results.processing_time,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"AI Lite analysis completed: {batch_id}")
            return frontend_result
            
        except Exception as e:
            logger.error(f"AI Lite analysis failed: {str(e)}")
            if batch_id in self.active_requests:
                self.active_requests[batch_id].status = "failed"
            raise
    
    def format_ai_lite_result(self, result: UnifiedBatchResult) -> Dict[str, Any]:
        """Transform AI Lite result into frontend-compatible format"""
        try:
            frontend_result = {
                "batch_id": result.batch_results.batch_id,
                "processed_count": result.batch_results.processed_count,
                "processing_time": result.batch_results.processing_time,
                "total_cost": result.batch_results.total_cost,
                "model_used": result.batch_results.model_used,
                "analysis_quality": result.batch_results.analysis_quality,
                "candidate_results": {}
            }
            
            # Transform individual candidate results
            for opportunity_id, analysis in result.candidate_analysis.items():
                frontend_result["candidate_results"][opportunity_id] = {
                    "ai_analysis": {
                        "compatibility_score": analysis.compatibility_score,
                        "strategic_value": analysis.strategic_value.value,
                        "risk_assessment": analysis.risk_assessment,
                        "priority_rank": analysis.priority_rank,
                        "funding_likelihood": analysis.funding_likelihood,
                        "strategic_rationale": analysis.strategic_rationale,
                        "action_priority": analysis.action_priority.value,
                        "confidence_level": analysis.confidence_level,
                        "analysis_timestamp": analysis.analysis_timestamp
                    },
                    "ai_lite_analyzed": True,
                    "ai_lite_processing": False
                }
            
            return frontend_result
            
        except Exception as e:
            logger.error(f"Failed to format AI Lite result: {str(e)}")
            raise
    
    # AI HEAVY PROCESSING METHODS
    
    def prepare_ai_heavy_request(self, frontend_data: Dict[str, Any]) -> AIHeavyRequest:
        """Transform frontend target data into AI Heavy request packet"""
        try:
            # Extract data from frontend
            target_data = frontend_data.get("target_opportunity", {})
            profile_data = frontend_data.get("selected_profile", {})
            ai_lite_data = frontend_data.get("ai_lite_results", {})
            
            # Generate research metadata
            research_id = f"ai_heavy_{int(datetime.now().timestamp())}"
            research_metadata = ResearchMetadata(
                research_id=research_id,
                profile_id=profile_data.get("profile_id", "unknown"),
                target_organization=target_data.get("organization_name", "Unknown"),
                analysis_depth=AnalysisDepth.COMPREHENSIVE,
                model_preference=frontend_data.get("model_preference", "gpt-5-mini"),
                cost_budget=frontend_data.get("cost_budget", 0.25),
                priority=Priority.HIGH
            )
            
            # Build context profile data
            context_profile = ContextProfileData(
                organization_name=profile_data.get("name", "[Organization Name Missing]"),
                mission_statement=profile_data.get("mission", "Mission not specified"),
                strategic_priorities=profile_data.get("strategic_priorities", []),
                leadership_team=profile_data.get("leadership_team", []),
                recent_grants=profile_data.get("recent_grants", []),
                funding_capacity=profile_data.get("funding_capacity", "$1M annually"),
                geographic_scope=profile_data.get("geographic_scope", "National")
            )
            
            # Build AI Lite results data
            ai_lite_results = AILiteResults(
                compatibility_score=ai_lite_data.get("compatibility_score", 0.7),
                strategic_value=ai_lite_data.get("strategic_value", "medium"),
                risk_assessment=ai_lite_data.get("risk_assessment", []),
                priority_rank=ai_lite_data.get("priority_rank", 1),
                funding_likelihood=ai_lite_data.get("funding_likelihood", 0.7),
                strategic_rationale=ai_lite_data.get("strategic_rationale", "Analysis pending"),
                action_priority=ai_lite_data.get("action_priority", "planned")
            )
            
            # Build target preliminary data
            target_preliminary = TargetPreliminaryData(
                organization_name=target_data.get("organization_name", "Unknown"),
                basic_info=target_data.get("description", "Organization description not available"),
                funding_capacity=target_data.get("funding_capacity", "Unknown"),
                geographic_focus=target_data.get("geographic_location", "National"),
                known_board_members=target_data.get("board_members", []),
                recent_grants_given=target_data.get("recent_grants", []),
                website_url=target_data.get("website_url"),
                annual_revenue=target_data.get("annual_revenue")
            )
            
            # Build research focus
            research_focus = ResearchFocus(
                priority_areas=frontend_data.get("research_priority_areas", ["strategic_partnership", "funding_approach", "introduction_strategy"]),
                risk_mitigation=frontend_data.get("research_risk_areas", ["competition_analysis", "capacity_assessment"]),
                intelligence_gaps=frontend_data.get("research_intelligence_gaps", ["board_connections", "funding_timeline", "application_requirements"])
            )
            
            # Assemble context data
            context_data = ContextData(
                profile_context=context_profile,
                ai_lite_results=ai_lite_results,
                target_preliminary_data=target_preliminary
            )
            
            request = AIHeavyRequest(
                request_metadata=research_metadata,
                context_data=context_data,
                research_focus=research_focus
            )
            
            logger.info(f"Prepared AI Heavy request for {target_data.get('organization_name', 'Unknown')}")
            return request
            
        except Exception as e:
            logger.error(f"Failed to prepare AI Heavy request: {str(e)}")
            raise
    
    async def execute_ai_heavy_research(self, frontend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AI Heavy research and return formatted results"""
        try:
            # Prepare request packet
            request = self.prepare_ai_heavy_request(frontend_data)
            research_id = request.request_metadata.research_id
            target_org = request.request_metadata.target_organization
            
            # Track request status
            status = ProcessingStatus(
                request_id=research_id,
                processing_type="ai_heavy",
                status="processing",
                start_time=datetime.now(),
                cost_estimate=self.ai_heavy_processor.get_cost_estimate(request.request_metadata.analysis_depth)
            )
            self.active_requests[research_id] = status
            
            # Execute AI Heavy research
            result = await self.ai_heavy_processor.execute(request)
            
            # Update status
            status.status = "completed"
            status.cost_actual = result.research_results.total_cost
            self.total_session_cost += result.research_results.total_cost
            
            # Transform result back to frontend format
            frontend_result = self.format_ai_heavy_result(result)
            
            # Log to history
            self.request_history.append({
                "type": "ai_heavy",
                "research_id": research_id,
                "target_organization": target_org,
                "cost": result.research_results.total_cost,
                "processing_time": result.research_results.processing_time,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"AI Heavy research completed: {research_id} for {target_org}")
            return frontend_result
            
        except Exception as e:
            logger.error(f"AI Heavy research failed: {str(e)}")
            if research_id in self.active_requests:
                self.active_requests[research_id].status = "failed"
            raise
    
    def format_ai_heavy_result(self, result: AIHeavyResult) -> Dict[str, Any]:
        """Transform AI Heavy result into frontend-compatible format"""
        try:
            # Convert Pydantic models to dictionaries for frontend consumption
            dossier = result.strategic_dossier
            action_plan = result.action_plan
            
            frontend_result = {
                "research_id": result.research_results.research_id,
                "target_organization": result.research_results.target_organization,
                "analysis_depth": result.research_results.analysis_depth,
                "processing_time": result.research_results.processing_time,
                "total_cost": result.research_results.total_cost,
                "confidence_level": result.research_results.confidence_level,
                
                "strategic_dossier": {
                    "partnership_assessment": {
                        "mission_alignment_score": dossier.partnership_assessment.mission_alignment_score,
                        "strategic_value": dossier.partnership_assessment.strategic_value,
                        "mutual_benefits": dossier.partnership_assessment.mutual_benefits,
                        "partnership_potential": dossier.partnership_assessment.partnership_potential,
                        "synergy_opportunities": dossier.partnership_assessment.synergy_opportunities
                    },
                    "funding_strategy": {
                        "optimal_request_amount": dossier.funding_strategy.optimal_request_amount,
                        "best_timing": dossier.funding_strategy.best_timing,
                        "target_programs": dossier.funding_strategy.target_programs,
                        "success_factors": dossier.funding_strategy.success_factors,
                        "application_requirements": dossier.funding_strategy.application_requirements
                    },
                    "competitive_analysis": {
                        "primary_competitors": dossier.competitive_analysis.primary_competitors,
                        "competitive_advantages": dossier.competitive_analysis.competitive_advantages,
                        "market_position": dossier.competitive_analysis.market_position,
                        "differentiation_strategy": dossier.competitive_analysis.differentiation_strategy,
                        "threat_assessment": dossier.competitive_analysis.threat_assessment
                    },
                    "relationship_strategy": {
                        "board_connections": dossier.relationship_strategy.board_connections,
                        "staff_approach": dossier.relationship_strategy.staff_approach,
                        "network_leverage": dossier.relationship_strategy.network_leverage,
                        "engagement_timeline": dossier.relationship_strategy.engagement_timeline
                    },
                    "financial_analysis": {
                        "funding_capacity_assessment": dossier.financial_analysis.funding_capacity_assessment,
                        "grant_size_optimization": dossier.financial_analysis.grant_size_optimization,
                        "multi_year_potential": dossier.financial_analysis.multi_year_potential,
                        "sustainability_prospects": dossier.financial_analysis.sustainability_prospects,
                        "financial_health_score": dossier.financial_analysis.financial_health_score
                    },
                    "risk_assessment": {
                        "primary_risks": dossier.risk_assessment.primary_risks,
                        "mitigation_strategies": dossier.risk_assessment.mitigation_strategies,
                        "contingency_plans": dossier.risk_assessment.contingency_plans,
                        "success_probability": dossier.risk_assessment.success_probability
                    }
                },
                
                "action_plan": {
                    "immediate_actions": [
                        {
                            "action": action.action,
                            "timeline": action.timeline,
                            "priority": action.priority,
                            "estimated_effort": action.estimated_effort,
                            "success_indicators": action.success_indicators
                        } for action in action_plan.immediate_actions
                    ],
                    "six_month_roadmap": action_plan.six_month_roadmap,
                    "success_metrics": action_plan.success_metrics,
                    "investment_recommendation": action_plan.investment_recommendation,
                    "roi_projection": action_plan.roi_projection
                },
                
                "grant_application_package": result.grant_application_package.dict() if result.grant_application_package else None,
                
                "deep_ai_analyzed": True,
                "deep_ai_processing": False,
                "deep_ai_error": False
            }
            
            return frontend_result
            
        except Exception as e:
            logger.error(f"Failed to format AI Heavy result: {str(e)}")
            raise
    
    # SERVICE MANAGEMENT METHODS
    
    def get_processing_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific AI processing request"""
        if request_id in self.active_requests:
            status = self.active_requests[request_id]
            return {
                "request_id": status.request_id,
                "processing_type": status.processing_type,
                "status": status.status,
                "progress_percentage": status.progress_percentage,
                "start_time": status.start_time.isoformat(),
                "cost_estimate": status.cost_estimate,
                "cost_actual": status.cost_actual
            }
        return None
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary with cost tracking"""
        active_count = len([s for s in self.active_requests.values() if s.status == "processing"])
        completed_count = len([s for s in self.active_requests.values() if s.status == "completed"])
        failed_count = len([s for s in self.active_requests.values() if s.status == "failed"])
        
        return {
            "total_session_cost": self.total_session_cost,
            "active_requests": active_count,
            "completed_requests": completed_count,
            "failed_requests": failed_count,
            "request_history": self.request_history,
            "processors_status": {
                "ai_lite": self.ai_lite_processor.get_status(),
                "ai_heavy": self.ai_heavy_processor.get_status()
            }
        }
    
    def get_cost_estimates(self, candidate_count: int = 1, research_count: int = 1) -> Dict[str, float]:
        """Get cost estimates for AI processing"""
        return {
            "ai_lite_batch": candidate_count * self.ai_lite_processor.estimated_cost_per_candidate,
            "ai_heavy_standard": research_count * self.ai_heavy_processor.get_cost_estimate(AnalysisDepth.STANDARD),
            "ai_heavy_comprehensive": research_count * self.ai_heavy_processor.get_cost_estimate(AnalysisDepth.COMPREHENSIVE),
            "ai_heavy_strategic": research_count * self.ai_heavy_processor.get_cost_estimate(AnalysisDepth.STRATEGIC)
        }

# Global service manager instance
_ai_service_manager: Optional[AIServiceManager] = None

def get_ai_service_manager() -> AIServiceManager:
    """Get the global AI service manager instance"""
    global _ai_service_manager
    if _ai_service_manager is None:
        _ai_service_manager = AIServiceManager()
    return _ai_service_manager

# Export service manager and key functions
__all__ = [
    "AIServiceManager",
    "ProcessingStatus", 
    "get_ai_service_manager"
]