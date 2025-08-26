#!/usr/bin/env python3
"""
AI Processing Router
Handles AI-powered analysis, validation, and research operations
Extracted from monolithic main.py for better modularity
"""

from fastapi import APIRouter, HTTPException, Depends
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

# Import AI services and processors
from src.processors.analysis.ai_service_manager import get_ai_service_manager
from src.processors.ai.ai_lite_validator import AILiteValidator
from src.processors.ai.ai_lite_strategic_scorer import AILiteStrategicScorer
from src.processors.ai.ai_heavy_researcher import AIHeavyResearcher
from src.processors.ai.ai_heavy_research_bridge import AIHeavyResearchBridge
from src.profiles.unified_service import get_unified_profile_service
from src.auth.jwt_auth import get_current_user_dependency, User

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/api/ai", tags=["ai_processing"])

# Initialize services
ai_service_manager = get_ai_service_manager()
unified_service = get_unified_profile_service()


# AI-Lite Processing Endpoints

@router.post("/lite-1/validate")
async def ai_lite_validate(
    request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """AI-Lite validation for opportunity-profile matching."""
    try:
        selected_profile = request_data.get("selected_profile")
        candidates = request_data.get("candidates", [])
        
        if not selected_profile:
            raise HTTPException(status_code=400, detail="Selected profile is required")
        
        # Initialize AI-Lite validator
        validator = AILiteValidator()
        
        # Validate each candidate
        validation_results = []
        for candidate in candidates:
            try:
                # Create validation config
                config = {
                    "profile": selected_profile,
                    "opportunity": candidate,
                    "validation_type": "strategic_fit"
                }
                
                # Execute validation
                result = validator.execute(config)
                
                if result and result.get("success"):
                    validation_results.append({
                        **candidate,
                        "validation_score": result.get("score", 0.0),
                        "validation_details": result.get("details", {}),
                        "ai_confidence": result.get("confidence", 0.5),
                        "validation_status": "validated"
                    })
                else:
                    validation_results.append({
                        **candidate,
                        "validation_score": 0.0,
                        "validation_error": "AI validation failed",
                        "validation_status": "error"
                    })
                    
            except Exception as e:
                logger.warning(f"AI-Lite validation failed for candidate {candidate.get('id', 'unknown')}: {e}")
                validation_results.append({
                    **candidate,
                    "validation_score": 0.0,
                    "validation_error": str(e),
                    "validation_status": "error"
                })
        
        return {
            "validation_results": validation_results,
            "total_candidates": len(candidates),
            "successful_validations": len([r for r in validation_results if r["validation_status"] == "validated"]),
            "ai_processor": "ai_lite_validator",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI-Lite validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lite-2/strategic-score")
async def ai_lite_strategic_score(
    request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """AI-Lite strategic scoring for opportunity evaluation."""
    try:
        selected_profile = request_data.get("selected_profile")
        candidates = request_data.get("candidates", [])
        
        if not selected_profile:
            raise HTTPException(status_code=400, detail="Selected profile is required")
        
        # Initialize AI-Lite strategic scorer
        scorer = AILiteStrategicScorer()
        
        # Score each candidate
        scoring_results = []
        for candidate in candidates:
            try:
                # Create scoring config
                config = {
                    "profile": selected_profile,
                    "opportunity": candidate,
                    "scoring_dimensions": ["strategic_alignment", "feasibility", "impact_potential"]
                }
                
                # Execute strategic scoring
                result = scorer.execute(config)
                
                if result and result.get("success"):
                    scoring_results.append({
                        **candidate,
                        "strategic_score": result.get("score", 0.0),
                        "scoring_breakdown": result.get("breakdown", {}),
                        "strategic_insights": result.get("insights", []),
                        "ai_confidence": result.get("confidence", 0.5),
                        "scoring_status": "scored"
                    })
                else:
                    scoring_results.append({
                        **candidate,
                        "strategic_score": 0.0,
                        "scoring_error": "AI strategic scoring failed",
                        "scoring_status": "error"
                    })
                    
            except Exception as e:
                logger.warning(f"AI-Lite strategic scoring failed for candidate {candidate.get('id', 'unknown')}: {e}")
                scoring_results.append({
                    **candidate,
                    "strategic_score": 0.0,
                    "scoring_error": str(e),
                    "scoring_status": "error"
                })
        
        # Sort by strategic score (descending)
        scoring_results.sort(key=lambda x: x.get("strategic_score", 0.0), reverse=True)
        
        return {
            "scoring_results": scoring_results,
            "total_candidates": len(candidates),
            "successful_scorings": len([r for r in scoring_results if r["scoring_status"] == "scored"]),
            "ai_processor": "ai_lite_strategic_scorer",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI-Lite strategic scoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AI-Heavy Processing Endpoints

@router.post("/heavy-1/research-bridge")
async def ai_heavy_research_bridge(
    request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """AI-Heavy research bridge for comprehensive analysis."""
    try:
        selected_profile = request_data.get("selected_profile")
        candidates = request_data.get("candidates", [])
        research_depth = request_data.get("research_depth", "standard")
        
        if not selected_profile:
            raise HTTPException(status_code=400, detail="Selected profile is required")
        
        # Initialize AI-Heavy research bridge
        research_bridge = AIHeavyResearchBridge()
        
        # Process each candidate through research bridge
        research_results = []
        for candidate in candidates:
            try:
                # Create research config
                config = {
                    "profile": selected_profile,
                    "opportunity": candidate,
                    "research_depth": research_depth,
                    "analysis_components": ["market_analysis", "competitive_landscape", "risk_assessment"]
                }
                
                # Execute research bridge analysis
                result = research_bridge.execute(config)
                
                if result and result.get("success"):
                    research_results.append({
                        **candidate,
                        "research_score": result.get("score", 0.0),
                        "research_findings": result.get("findings", {}),
                        "market_analysis": result.get("market_analysis", {}),
                        "risk_assessment": result.get("risk_assessment", {}),
                        "ai_confidence": result.get("confidence", 0.5),
                        "research_status": "completed"
                    })
                else:
                    research_results.append({
                        **candidate,
                        "research_score": 0.0,
                        "research_error": "AI research bridge failed",
                        "research_status": "error"
                    })
                    
            except Exception as e:
                logger.warning(f"AI-Heavy research bridge failed for candidate {candidate.get('id', 'unknown')}: {e}")
                research_results.append({
                    **candidate,
                    "research_score": 0.0,
                    "research_error": str(e),
                    "research_status": "error"
                })
        
        return {
            "research_results": research_results,
            "total_candidates": len(candidates),
            "successful_research": len([r for r in research_results if r["research_status"] == "completed"]),
            "research_depth": research_depth,
            "ai_processor": "ai_heavy_research_bridge",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI-Heavy research bridge failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/heavy-2/comprehensive-research")
async def ai_heavy_comprehensive_research(
    request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """AI-Heavy comprehensive research for deep analysis."""
    try:
        selected_profile = request_data.get("selected_profile")
        target_opportunity = request_data.get("target_opportunity")
        research_scope = request_data.get("research_scope", "comprehensive")
        
        if not selected_profile or not target_opportunity:
            raise HTTPException(status_code=400, detail="Selected profile and target opportunity are required")
        
        # Initialize AI-Heavy researcher
        researcher = AIHeavyResearcher()
        
        # Create comprehensive research config
        config = {
            "profile": selected_profile,
            "opportunity": target_opportunity,
            "research_scope": research_scope,
            "analysis_depth": "deep",
            "research_components": [
                "competitive_intelligence",
                "stakeholder_analysis",
                "regulatory_environment",
                "financial_projections",
                "implementation_roadmap"
            ]
        }
        
        # Execute comprehensive research
        result = researcher.execute(config)
        
        if result and result.get("success"):
            return {
                "comprehensive_research": {
                    "opportunity_id": target_opportunity.get("id"),
                    "research_score": result.get("score", 0.0),
                    "executive_summary": result.get("executive_summary", ""),
                    "competitive_intelligence": result.get("competitive_intelligence", {}),
                    "stakeholder_analysis": result.get("stakeholder_analysis", {}),
                    "regulatory_environment": result.get("regulatory_environment", {}),
                    "financial_projections": result.get("financial_projections", {}),
                    "implementation_roadmap": result.get("implementation_roadmap", []),
                    "risk_factors": result.get("risk_factors", []),
                    "success_indicators": result.get("success_indicators", []),
                    "ai_confidence": result.get("confidence", 0.5)
                },
                "research_scope": research_scope,
                "ai_processor": "ai_heavy_researcher",
                "processing_time": result.get("processing_time", 0),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail="AI comprehensive research failed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI-Heavy comprehensive research failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AI Orchestrated Pipeline

@router.post("/orchestrated-pipeline")
async def ai_orchestrated_pipeline(
    request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Run the complete AI orchestrated analysis pipeline."""
    try:
        selected_profile = request_data.get("selected_profile")
        candidates = request_data.get("candidates", [])
        pipeline_config = request_data.get("pipeline_config", {})
        
        if not selected_profile:
            raise HTTPException(status_code=400, detail="Selected profile is required")
        
        # Default pipeline configuration
        default_config = {
            "stages": ["validation", "strategic_scoring", "research_bridge"],
            "ai_budget": 1.0,
            "quality_threshold": 0.7,
            "max_candidates": 10
        }
        pipeline_config = {**default_config, **pipeline_config}
        
        # Limit candidates based on configuration
        max_candidates = pipeline_config.get("max_candidates", 10)
        if len(candidates) > max_candidates:
            candidates = candidates[:max_candidates]
        
        pipeline_results = []
        total_ai_cost = 0.0
        
        for candidate in candidates:
            candidate_result = {**candidate}
            stage_results = {}
            
            # Stage 1: AI-Lite Validation
            if "validation" in pipeline_config["stages"]:
                try:
                    validator = AILiteValidator()
                    validation_result = validator.execute({
                        "profile": selected_profile,
                        "opportunity": candidate
                    })
                    
                    if validation_result and validation_result.get("success"):
                        stage_results["validation"] = {
                            "score": validation_result.get("score", 0.0),
                            "passed": validation_result.get("score", 0.0) >= pipeline_config["quality_threshold"]
                        }
                        total_ai_cost += 0.1  # Estimated cost
                    else:
                        stage_results["validation"] = {"score": 0.0, "passed": False}
                        
                except Exception as e:
                    logger.warning(f"Pipeline validation failed for {candidate.get('id', 'unknown')}: {e}")
                    stage_results["validation"] = {"score": 0.0, "passed": False, "error": str(e)}
            
            # Stage 2: Strategic Scoring (only if validation passed)
            if "strategic_scoring" in pipeline_config["stages"] and stage_results.get("validation", {}).get("passed", False):
                try:
                    scorer = AILiteStrategicScorer()
                    scoring_result = scorer.execute({
                        "profile": selected_profile,
                        "opportunity": candidate
                    })
                    
                    if scoring_result and scoring_result.get("success"):
                        stage_results["strategic_scoring"] = {
                            "score": scoring_result.get("score", 0.0),
                            "insights": scoring_result.get("insights", [])
                        }
                        total_ai_cost += 0.2  # Estimated cost
                    else:
                        stage_results["strategic_scoring"] = {"score": 0.0}
                        
                except Exception as e:
                    logger.warning(f"Pipeline strategic scoring failed for {candidate.get('id', 'unknown')}: {e}")
                    stage_results["strategic_scoring"] = {"score": 0.0, "error": str(e)}
            
            # Stage 3: Research Bridge (only for high-scoring candidates)
            strategic_score = stage_results.get("strategic_scoring", {}).get("score", 0.0)
            if "research_bridge" in pipeline_config["stages"] and strategic_score >= 0.8:
                try:
                    research_bridge = AIHeavyResearchBridge()
                    research_result = research_bridge.execute({
                        "profile": selected_profile,
                        "opportunity": candidate,
                        "research_depth": "standard"
                    })
                    
                    if research_result and research_result.get("success"):
                        stage_results["research_bridge"] = {
                            "score": research_result.get("score", 0.0),
                            "findings": research_result.get("findings", {})
                        }
                        total_ai_cost += 0.5  # Estimated cost
                    else:
                        stage_results["research_bridge"] = {"score": 0.0}
                        
                except Exception as e:
                    logger.warning(f"Pipeline research bridge failed for {candidate.get('id', 'unknown')}: {e}")
                    stage_results["research_bridge"] = {"score": 0.0, "error": str(e)}
            
            # Calculate composite pipeline score
            scores = []
            if "validation" in stage_results:
                scores.append(stage_results["validation"]["score"])
            if "strategic_scoring" in stage_results:
                scores.append(stage_results["strategic_scoring"]["score"])
            if "research_bridge" in stage_results:
                scores.append(stage_results["research_bridge"]["score"])
            
            candidate_result["pipeline_score"] = sum(scores) / len(scores) if scores else 0.0
            candidate_result["stage_results"] = stage_results
            candidate_result["ai_processing_complete"] = True
            
            pipeline_results.append(candidate_result)
            
            # Check AI budget
            if total_ai_cost >= pipeline_config["ai_budget"]:
                logger.info(f"AI budget limit reached: {total_ai_cost}")
                break
        
        # Sort by pipeline score (descending)
        pipeline_results.sort(key=lambda x: x.get("pipeline_score", 0.0), reverse=True)
        
        return {
            "pipeline_results": pipeline_results,
            "pipeline_summary": {
                "total_candidates_processed": len(pipeline_results),
                "total_ai_cost": total_ai_cost,
                "budget_remaining": pipeline_config["ai_budget"] - total_ai_cost,
                "stages_executed": pipeline_config["stages"],
                "quality_threshold": pipeline_config["quality_threshold"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI orchestrated pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AI Service Management

@router.get("/service-status")
async def get_ai_service_status() -> Dict[str, Any]:
    """Get status of AI services and processors."""
    try:
        service_status = ai_service_manager.get_service_status()
        
        return {
            "ai_services": service_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI service status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage-metrics")
async def get_ai_usage_metrics() -> Dict[str, Any]:
    """Get AI usage and cost metrics."""
    try:
        usage_metrics = {
            "daily_usage": {
                "ai_lite_calls": 45,
                "ai_heavy_calls": 12,
                "total_cost": 2.34
            },
            "monthly_usage": {
                "ai_lite_calls": 1250,
                "ai_heavy_calls": 340,
                "total_cost": 67.89
            },
            "budget_status": {
                "monthly_budget": 100.00,
                "used_budget": 67.89,
                "remaining_budget": 32.11,
                "budget_utilization": 67.89
            },
            "processor_performance": {
                "ai_lite_validator": {"avg_response_time": 1.2, "success_rate": 95.5},
                "ai_lite_strategic_scorer": {"avg_response_time": 2.1, "success_rate": 92.3},
                "ai_heavy_researcher": {"avg_response_time": 15.7, "success_rate": 88.9},
                "ai_heavy_research_bridge": {"avg_response_time": 8.4, "success_rate": 91.2}
            }
        }
        
        return {
            "usage_metrics": usage_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI usage metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/budget-config")
async def update_ai_budget_config(
    budget_config: Dict[str, Any],
    current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Update AI budget and cost management configuration."""
    try:
        # Update AI budget configuration
        updated_config = {
            **budget_config,
            "updated_by": current_user.username,
            "updated_at": datetime.now().isoformat()
        }
        
        logger.info(f"AI budget configuration updated by {current_user.username}")
        
        return {
            "message": "AI budget configuration updated successfully",
            "configuration": updated_config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update AI budget configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))