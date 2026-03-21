#!/usr/bin/env python3
"""
AI Analysis Endpoints Router
Extracted from main.py - Enhanced AI Lite & AI Heavy Processing endpoints.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Analysis"])


def get_ai_service_manager():
    """Lazy import for AI service manager."""
    from src.processors.analysis.ai_service_manager import get_ai_service_manager as _get
    return _get()


def transform_candidate_to_target(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform candidate data from ANALYZE tab to target_opportunity format
    expected by AI Heavy researcher.
    """
    return {
        "opportunity_id": candidate.get("opportunity_id"),
        "organization_name": candidate.get("organization_name"),
        "source_type": candidate.get("source_type"),
        "funding_amount": candidate.get("funding_amount"),
        "website": candidate.get("website"),
        "ein": candidate.get("ein"),
        "ai_compatibility_score": candidate.get("ai_lite_score", 0.0),
        "ai_analysis_insights": candidate.get("ai_lite_insights", ""),
        "discovery_context": {
            "promoted_from": "ai_lite_analysis",
            "original_source": candidate.get("source_type", "unknown"),
            "promotion_timestamp": candidate.get("promotion_timestamp")
        }
    }


async def handle_batch_promotion(request: Dict[str, Any], ai_service):
    """
    Handle batch promotion of multiple candidates for AI-Heavy research.
    Transforms candidate data to individual target_opportunity format.
    """
    logger.info("Processing batch promotion for AI-Heavy research")

    candidates = request.get("candidates", [])
    if not candidates:
        raise HTTPException(status_code=400, detail="No candidates provided for batch promotion")

    selected_profile = request.get("selected_profile")
    cost_limit = request.get("cost_limit", 5.0)  # Default budget limit

    batch_results = []
    total_cost = 0.0
    successful_analyses = 0
    failed_analyses = []

    logger.info(f"Processing {len(candidates)} candidates for AI-Heavy promotion")

    for i, candidate in enumerate(candidates):
        try:
            # Transform candidate to target_opportunity format
            target_opportunity = transform_candidate_to_target(candidate)

            # Create individual research request
            single_request = {
                "target_opportunity": target_opportunity,
                "selected_profile": selected_profile,
                "ai_lite_results": candidate.get("ai_lite_insights", {}),
                "model_preference": "gpt-5-nano" if candidate.get("research_depth") == "standard" else "gpt-5-mini",
                "cost_budget": candidate.get("estimated_cost", 0.08),
                "research_priority_areas": ["funding_strategy", "competitive_analysis"],
                "research_risk_areas": ["capacity_assessment", "timeline_feasibility"],
                "research_intelligence_gaps": ["board_connections", "success_metrics"]
            }

            # Check cost budget
            if total_cost + single_request["cost_budget"] > cost_limit:
                logger.warning(f"Cost limit reached. Stopping batch processing at candidate {i+1}")
                break

            # Execute AI Heavy research for this candidate
            result = await ai_service.execute_ai_heavy_research(single_request)

            # Process successful result
            analysis_result = {
                "opportunity_id": candidate.get("opportunity_id"),
                "organization_name": candidate.get("organization_name"),
                "research_score": result.get("research_score", 0.0),
                "comprehensive_analysis": result.get("comprehensive_analysis", ""),
                "strategic_insights": result.get("strategic_insights", {}),
                "competitive_analysis": result.get("competitive_analysis", {}),
                "risk_assessment": result.get("risk_assessment", {}),
                "funding_strategy": result.get("funding_strategy", {}),
                "research_mode": candidate.get("research_depth", "standard"),
                "cost_breakdown": {
                    "total_cost": result.get("cost_breakdown", {}).get("total_cost", single_request["cost_budget"]),
                    "model_used": single_request["model_preference"]
                }
            }

            batch_results.append(analysis_result)
            total_cost += analysis_result["cost_breakdown"]["total_cost"]
            successful_analyses += 1

            logger.info(f"Completed AI-Heavy research for {candidate.get('organization_name')} (${analysis_result['cost_breakdown']['total_cost']:.4f})")

        except Exception as e:
            logger.error(f"Failed AI-Heavy research for {candidate.get('organization_name', 'Unknown')}: {str(e)}")
            failed_analyses.append({
                "candidate": candidate.get("organization_name", "Unknown"),
                "error": str(e)
            })
            continue

    logger.info(f"Batch promotion completed: {successful_analyses} successful, {len(failed_analyses)} failed, Total cost: ${total_cost:.4f}")

    return {
        "status": "success",
        "analysis_type": "ai_heavy_batch",
        "results": {
            "research_analyses": batch_results,
            "batch_summary": {
                "total_processed": len(candidates),
                "successful_analyses": successful_analyses,
                "failed_analyses": len(failed_analyses),
                "total_cost": total_cost,
                "cost_limit": cost_limit,
                "processing_time": "batch_mode"
            }
        },
        "failed_analyses": failed_analyses if failed_analyses else None,
        "total_cost": total_cost
    }


@router.post("/lite-analysis")
async def execute_ai_lite_analysis(request: Dict[str, Any]):
    """
    Execute AI Lite batch analysis using comprehensive data packets.

    Request format:
    {
        "selected_profile": {...},
        "candidates": [...],
        "model_preference": "gpt-3.5-turbo",
        "cost_limit": 0.01
    }
    """
    try:
        logger.info("Starting AI Lite batch analysis")

        # Get AI service manager
        ai_service = get_ai_service_manager()

        # Validate request data
        if not request.get("candidates"):
            raise HTTPException(status_code=400, detail="No candidates provided for analysis")

        if not request.get("selected_profile"):
            raise HTTPException(status_code=400, detail="Profile context required for AI analysis")

        # Execute AI Lite analysis
        result = await ai_service.execute_ai_lite_analysis(request)

        return {
            "status": "success",
            "analysis_type": "ai_lite",
            "result": result,
            "session_summary": ai_service.get_session_summary()
        }

    except Exception as e:
        logger.error(f"AI Lite analysis failed: {str(e)}")
        logger.error(f"AI Lite analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/deep-research")
async def execute_ai_heavy_research(request: Dict[str, Any]):
    """
    Execute AI Heavy deep research using comprehensive data packets.
    Supports both single target and batch promotion modes.

    Single Target Request format:
    {
        "target_opportunity": {...},
        "selected_profile": {...},
        "ai_lite_results": {...},
        "model_preference": "gpt-5",
        "cost_budget": 0.25,
        "research_priority_areas": [...],
        "research_risk_areas": [...],
        "research_intelligence_gaps": [...]
    }

    Batch Promotion Request format:
    {
        "candidates": [{...}, {...}],
        "selected_profile": {...},
        "research_mode": "batch_promotion",
        "cost_limit": 1.50,
        "priority": "high"
    }
    """
    try:
        logger.info("Starting AI Heavy deep research")

        # Get AI service manager
        ai_service = get_ai_service_manager()

        # Validate request data
        if not request.get("selected_profile"):
            raise HTTPException(status_code=400, detail="Profile context required for AI research")

        # Check for batch promotion mode
        if request.get("research_mode") == "batch_promotion":
            return await handle_batch_promotion(request, ai_service)

        # Original single target handling
        if not request.get("target_opportunity"):
            raise HTTPException(status_code=400, detail="Target opportunity required for deep research")

        # Execute single target AI Heavy research
        result = await ai_service.execute_ai_heavy_research(request)

        return {
            "status": "success",
            "analysis_type": "ai_heavy",
            "result": result,
            "session_summary": ai_service.get_session_summary()
        }

    except Exception as e:
        logger.error(f"AI Heavy research failed: {str(e)}")
        logger.error(f"AI Heavy research failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analysis-status/{request_id}")
async def get_ai_analysis_status(request_id: str):
    """Get status of a specific AI processing request."""
    try:
        ai_service = get_ai_service_manager()
        status = ai_service.get_processing_status(request_id)

        if not status:
            raise HTTPException(status_code=404, detail=f"Request {request_id} not found")

        return {
            "status": "success",
            "request_status": status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get AI analysis status: {str(e)}")
        logger.error(f"Internal server error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/session-summary")
async def get_ai_session_summary():
    """Get comprehensive AI session summary with cost tracking."""
    try:
        ai_service = get_ai_service_manager()
        summary = ai_service.get_session_summary()

        return {
            "status": "success",
            "session_summary": summary
        }

    except Exception as e:
        logger.error(f"Failed to get AI session summary: {str(e)}")
        logger.error(f"Internal server error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/cost-estimates")
async def get_ai_cost_estimates(candidate_count: int = 1, research_count: int = 1):
    """Get cost estimates for AI processing."""
    try:
        ai_service = get_ai_service_manager()
        estimates = ai_service.get_cost_estimates(candidate_count, research_count)

        return {
            "status": "success",
            "cost_estimates": estimates,
            "pricing_info": {
                "ai_lite_per_candidate": "$0.0001 - $0.0015",
                "ai_heavy_per_research": "$0.10 - $0.25",
                "model_tiers": {
                    "ai_lite": "GPT-3.5 Turbo (cost-optimized)",
                    "ai_heavy": "GPT-4 (premium analysis)"
                }
            }
        }

    except Exception as e:
        logger.error(f"Failed to get AI cost estimates: {str(e)}")
        logger.error(f"Internal server error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/batch-analysis")
async def execute_batch_ai_analysis(request: Dict[str, Any]):
    """
    Execute combined AI Lite + AI Heavy analysis pipeline.

    First runs AI Lite on all candidates, then runs AI Heavy on top-ranked targets.
    """
    try:
        logger.info("Starting batch AI analysis pipeline")

        # Get AI service manager
        ai_service = get_ai_service_manager()

        # Validate request data
        if not request.get("candidates"):
            raise HTTPException(status_code=400, detail="No candidates provided for batch analysis")

        if len(request.get("candidates", [])) > 200:
            raise HTTPException(status_code=400, detail="Batch size cannot exceed 200 candidates")

        if not request.get("selected_profile"):
            raise HTTPException(status_code=400, detail="Profile context required for batch analysis")

        # Step 1: Execute AI Lite analysis
        logger.info("Phase 1: AI Lite batch analysis")
        ai_lite_result = await ai_service.execute_ai_lite_analysis(request)

        # Step 2: Identify top candidates for deep research
        top_candidates_count = request.get("deep_research_count", 3)
        candidates_data = request.get("candidates", [])

        # Sort by AI Lite priority ranking and select top candidates
        if "candidate_results" in ai_lite_result:
            top_candidates = []
            for candidate in candidates_data:
                opp_id = candidate.get("opportunity_id")
                if opp_id in ai_lite_result["candidate_results"]:
                    ai_analysis = ai_lite_result["candidate_results"][opp_id]["ai_analysis"]
                    candidate["ai_lite_results"] = ai_analysis
                    top_candidates.append((candidate, ai_analysis["priority_rank"]))

            # Sort by priority rank and take top N
            top_candidates.sort(key=lambda x: x[1])
            selected_candidates = [c[0] for c in top_candidates[:top_candidates_count]]
        else:
            selected_candidates = candidates_data[:top_candidates_count]

        # Step 3: Execute AI Heavy research on top candidates
        logger.info(f"Phase 2: AI Heavy research on {len(selected_candidates)} top candidates")
        deep_research_results = []

        for candidate in selected_candidates:
            try:
                research_request = {
                    "target_opportunity": candidate,
                    "selected_profile": request["selected_profile"],
                    "ai_lite_results": candidate.get("ai_lite_results", {}),
                    "model_preference": request.get("model_preference", "gpt-5"),
                    "cost_budget": request.get("cost_budget", 0.25)
                }

                research_result = await ai_service.execute_ai_heavy_research(research_request)
                deep_research_results.append({
                    "candidate": candidate,
                    "research_result": research_result
                })

            except Exception as e:
                logger.warning(f"Deep research failed for {candidate.get('organization_name', 'Unknown')}: {str(e)}")
                deep_research_results.append({
                    "candidate": candidate,
                    "research_result": {"error": str(e)}
                })

        # Compile comprehensive results
        return {
            "status": "success",
            "analysis_type": "batch_pipeline",
            "ai_lite_result": ai_lite_result,
            "deep_research_results": deep_research_results,
            "pipeline_summary": {
                "total_candidates_analyzed": len(candidates_data),
                "deep_research_conducted": len(selected_candidates),
                "successful_deep_research": len([r for r in deep_research_results if "error" not in r["research_result"]])
            },
            "session_summary": ai_service.get_session_summary()
        }

    except Exception as e:
        logger.error(f"Batch AI analysis pipeline failed: {str(e)}")
        logger.error(f"Batch analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# SPECIALIZED AI PROCESSOR ENDPOINTS - 5-Call Architecture Integration

@router.post("/lite-1/validate")
async def execute_ai_lite_validator(request: Dict[str, Any]):
    """Execute AI-Lite Unified processor for comprehensive opportunity analysis."""
    try:
        logger.info("Starting AI-Lite Unified analysis (formerly AI-Lite-1 Validator)")

        # Import the unified processor
        from src.processors.analysis.ai_lite_unified_processor import AILiteUnifiedProcessor, UnifiedRequest

        # Validate request data
        candidates = request.get("candidates", [])
        profile = request.get("selected_profile", {})

        if not candidates:
            raise HTTPException(status_code=400, detail="No candidates provided for analysis")
        if not profile:
            raise HTTPException(status_code=400, detail="Profile context required for analysis")

        # Initialize processor
        unified_processor = AILiteUnifiedProcessor()

        # Create unified request
        unified_request = UnifiedRequest(
            batch_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            profile_context=profile,
            candidates=candidates,
            analysis_mode="validation_only",
            cost_budget=request.get("cost_limit", 0.05),
            priority_level="standard"
        )

        # Execute unified analysis
        results = await unified_processor.execute(unified_request)

        return {
            "status": "success",
            "processor": "ai_lite_unified",
            "results": results,
            "cost_estimate": "$0.0001 per candidate",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"AI-Lite-1 Validator failed: {str(e)}")
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/lite-2/strategic-score")
async def execute_ai_lite_strategic_scorer(request: Dict[str, Any]):
    """Execute AI-Lite Unified processor for comprehensive strategic analysis."""
    try:
        logger.info("Starting AI-Lite Unified analysis (formerly AI-Lite-2 Strategic Scorer)")

        # Import the unified processor
        from src.processors.analysis.ai_lite_unified_processor import AILiteUnifiedProcessor, UnifiedRequest

        # Validate request data
        qualified_candidates = request.get("qualified_candidates", [])
        profile = request.get("selected_profile", {})

        if not qualified_candidates:
            raise HTTPException(status_code=400, detail="No candidates provided for strategic analysis")
        if not profile:
            raise HTTPException(status_code=400, detail="Profile context required for strategic analysis")

        # Initialize processor
        unified_processor = AILiteUnifiedProcessor()

        # Create unified request
        unified_request = UnifiedRequest(
            batch_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            profile_context=profile,
            candidates=qualified_candidates,
            analysis_mode="strategic_only",
            cost_budget=request.get("cost_limit", 0.05),
            priority_level="standard"
        )

        # Execute strategic analysis
        results = await unified_processor.execute(unified_request)

        return {
            "status": "success",
            "processor": "ai_lite_unified_processor",
            "results": results,
            "cost_estimate": "$0.0004 per candidate",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"AI-Lite-2 Strategic Scorer failed: {str(e)}")
        logger.error(f"Strategic scoring failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/heavy-light/analyze")
async def execute_ai_heavy_light_analyzer(request: Dict[str, Any]):
    """Execute AI-Heavy Light processor for cost-effective candidate screening."""
    try:
        logger.info("Starting AI-Heavy Light analysis for ANALYZE tab")

        # Import the processor
        from src.processors.analysis.ai_heavy_light_analyzer import AIHeavyLightAnalyzer, LightAnalysisRequest

        # Validate request data
        candidates = request.get("candidates", [])
        profile = request.get("selected_profile", {})

        if not candidates:
            raise HTTPException(status_code=400, detail="No candidates provided for light analysis")
        if not profile:
            raise HTTPException(status_code=400, detail="Profile context required for analysis")

        # Initialize processor
        light_analyzer = AIHeavyLightAnalyzer()

        # Create analysis request
        analysis_request = LightAnalysisRequest(
            batch_id=f"light_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            profile_context=profile,
            candidates=candidates,
            analysis_focus=request.get("analysis_focus", "screening"),
            cost_budget=request.get("cost_budget", 0.05),
            priority_level=request.get("priority_level", "standard")
        )

        # Execute light analysis
        results = await light_analyzer.execute(analysis_request)

        return {
            "status": "success",
            "processor": "ai_heavy_light_analyzer",
            "results": results.dict(),
            "cost_estimate": f"${results.cost_per_candidate:.4f} per candidate",
            "timestamp": datetime.now().isoformat(),
            "screening_summary": results.screening_summary,
            "recommendations": results.recommendations
        }

    except Exception as e:
        logger.error(f"AI-Heavy Light analysis failed: {str(e)}")
        logger.error(f"Light analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/heavy-1/research-bridge")
async def execute_ai_heavy_research_bridge(request: Dict[str, Any]):
    """Execute AI-Heavy-1 Research Bridge for intelligence gathering and fact extraction."""
    try:
        logger.info("Starting AI-Heavy-1 Research Bridge analysis")

        # Import the specific processor
        from src.processors.analysis.ai_heavy_research_bridge import AIHeavyResearchBridge

        # Validate request data
        target_candidates = request.get("target_candidates", [])
        profile = request.get("selected_profile", {})
        lite_results = request.get("ai_lite_results", {})

        if not target_candidates:
            raise HTTPException(status_code=400, detail="No target candidates provided for research bridge")
        if not profile:
            raise HTTPException(status_code=400, detail="Profile context required for research analysis")

        # Initialize processor
        research_bridge = AIHeavyResearchBridge()

        # Execute research bridge analysis
        results = await research_bridge.execute({
            "target_candidates": target_candidates,
            "profile_context": profile,
            "ai_lite_context": lite_results,
            "research_depth": request.get("research_depth", "comprehensive"),
            "intelligence_priorities": request.get("intelligence_priorities", [])
        })

        return {
            "status": "success",
            "processor": "ai_heavy_research_bridge",
            "results": results,
            "cost_estimate": "$0.05 per candidate",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"AI-Heavy-1 Research Bridge failed: {str(e)}")
        logger.error(f"Research bridge failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/orchestrated-pipeline")
async def execute_orchestrated_analysis_pipeline(request: Dict[str, Any]):
    """Execute the complete 5-call orchestrated AI analysis pipeline."""
    try:
        logger.info("Starting orchestrated AI analysis pipeline")

        # Import the orchestrator
        from src.processors.analysis.optimized_analysis_orchestrator import OptimizedAnalysisOrchestrator

        # Validate request data
        prospects = request.get("prospects", [])
        profile = request.get("selected_profile", {})

        if not prospects:
            raise HTTPException(status_code=400, detail="No prospects provided for orchestrated analysis")
        if not profile:
            raise HTTPException(status_code=400, detail="Profile context required for orchestrated analysis")

        # Initialize orchestrator
        orchestrator = OptimizedAnalysisOrchestrator()

        # Execute complete pipeline
        results = await orchestrator.execute_complete_pipeline({
            "prospects": prospects,
            "profile_context": profile,
            "cost_budget": request.get("cost_budget", 1.0),
            "quality_threshold": request.get("quality_threshold", 0.7),
            "parallel_processing": request.get("parallel_processing", True)
        })

        return {
            "status": "success",
            "processor": "orchestrated_pipeline",
            "results": results,
            "pipeline_summary": {
                "total_prospects_input": len(prospects),
                "candidates_after_validation": results.get("validation_stats", {}).get("passed", 0),
                "qualified_after_scoring": results.get("scoring_stats", {}).get("qualified", 0),
                "targets_after_research": results.get("research_stats", {}).get("completed", 0),
                "total_cost": results.get("cost_summary", {}).get("total_cost", 0)
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Orchestrated pipeline failed: {str(e)}")
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
