"""
Research & AI Router
API endpoints for research capabilities, AI analysis (lite/heavy), and integrated research platform.
Extracted from main.py for better modularity.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
from datetime import datetime
import logging

from src.profiles.unified_service import get_unified_profile_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Research & AI"])

# Lazy-initialized shared services
_unified_service = None


def _get_unified_service():
    global _unified_service
    if _unified_service is None:
        _unified_service = get_unified_profile_service()
    return _unified_service


# =============================================================================
# Research Capabilities Endpoints
# =============================================================================

@router.get("/research/capabilities")
async def get_research_capabilities():
    """Get AI research capabilities for ANALYZE and EXAMINE tabs"""
    try:
        # Import research integration service
        from src.processors.analysis.research_integration_service import get_research_integration_service
        from src.processors.analysis.ai_lite_unified_processor import AILiteUnifiedProcessor
        from src.processors.analysis.ai_heavy_researcher import AIHeavyResearcher

        integration_service = get_research_integration_service()
        ai_lite = AILiteUnifiedProcessor()
        ai_heavy = AIHeavyResearcher()

        return {
            "research_integration": integration_service.get_integration_status(),
            "ai_lite_capabilities": ai_lite.get_research_capabilities(),
            "ai_heavy_capabilities": ai_heavy.get_dossier_builder_capabilities(),
            "phase_1_features": {
                "ai_lite_research_mode": "Comprehensive research reports for grant teams",
                "ai_heavy_dossier_builder": "Decision-ready dossiers with implementation roadmaps",
                "cross_system_integration": "Seamless research handoff from ANALYZE to EXAMINE",
                "evidence_based_scoring": "Research-backed scoring with supporting documentation"
            },
            "status": "Phase 1 Complete - Research capabilities fully activated"
        }
    except Exception as e:
        logger.error(f"Failed to get research capabilities: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/research/ai-lite/analyze")
async def ai_lite_research_analysis(
    opportunity_ids: List[str] = Body(...),
    profile_id: str = Body(...),
    research_mode: bool = Body(default=True)
):
    """Trigger AI-Lite research analysis for opportunities"""
    try:
        from src.processors.analysis.ai_lite_unified_processor import AILiteUnifiedProcessor, UnifiedRequest, UnifiedBatchResult

        ai_lite = AILiteUnifiedProcessor()

        # Create mock request data for demonstration
        # In production, this would pull real data from the profile and opportunity systems
        request_data = UnifiedRequest(
            batch_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            profile_context={
                "organization_name": "Sample Organization",
                "mission_statement": "Sample mission for demonstration",
                "focus_areas": ["health", "education"],
                "ntee_codes": ["A01", "B01"],
                "geographic_scope": "National"
            },
            candidates=[
                {
                    "opportunity_id": opp_id,
                    "organization_name": f"Target Organization {i+1}",
                    "source_type": "foundation",
                    "description": f"Sample opportunity description for {opp_id}",
                    "funding_amount": 100000,
                    "current_score": 0.7
                } for i, opp_id in enumerate(opportunity_ids[:3])  # Limit to 3 for demo
            ],
            analysis_mode="comprehensive" if research_mode else "validation_only",
            cost_budget=0.05,
            priority_level="high"
        )

        # Execute analysis
        results = await ai_lite.execute(request_data)

        # Convert results to JSON-serializable format
        response_data = {
            "batch_id": results.batch_results.batch_id,
            "processed_count": results.batch_results.processed_count,
            "processing_time": results.batch_results.processing_time,
            "estimated_cost": results.batch_results.total_cost,
            "research_mode_used": research_mode,
            "analysis_results": {}
        }

        for opp_id, analysis in results.candidate_analysis.items():
            result_data = {
                "compatibility_score": analysis.compatibility_score,
                "strategic_value": analysis.strategic_value.value,
                "funding_likelihood": analysis.funding_likelihood,
                "strategic_rationale": analysis.strategic_rationale,
                "action_priority": analysis.action_priority.value,
                "confidence_level": analysis.confidence_level,
                "research_mode_enabled": analysis.research_mode_enabled
            }

            # Add research components if available
            if analysis.research_report:
                result_data["research_report"] = {
                    "executive_summary": analysis.research_report.executive_summary,
                    "opportunity_overview": analysis.research_report.opportunity_overview,
                    "funding_details": analysis.research_report.funding_details,
                    "decision_factors": analysis.research_report.decision_factors
                }

            if analysis.competitive_analysis:
                result_data["competitive_analysis"] = {
                    "likely_competitors": analysis.competitive_analysis.likely_competitors,
                    "competitive_advantages": analysis.competitive_analysis.competitive_advantages,
                    "success_probability_factors": analysis.competitive_analysis.success_probability_factors
                }

            response_data["analysis_results"][opp_id] = result_data

        return response_data

    except Exception as e:
        logger.error(f"AI-Lite research analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/research/status/{profile_id}")
async def get_research_status(profile_id: str):
    """Get research status for a profile"""
    try:
        from src.processors.analysis.research_integration_service import get_research_integration_service

        integration_service = get_research_integration_service()

        return {
            "profile_id": profile_id,
            "research_integration_status": integration_service.get_integration_status(),
            "ai_lite_research_enabled": True,
            "ai_heavy_dossier_builder_enabled": True,
            "cross_system_integration_enabled": True,
            "phase_1_enhancement": "Complete",
            "available_features": [
                "AI-Lite comprehensive research reports",
                "AI-Heavy decision-ready dossiers",
                "Research evidence integration",
                "Cross-system data handoff",
                "Grant team decision support"
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get research status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/research/split-capabilities")
async def get_split_research_capabilities():
    """Get specialized research capabilities for split AI-Heavy system"""
    try:
        # Import both specialized processors
        from src.processors.analysis.ai_heavy_deep_researcher import AIHeavyDeepResearcher
        from src.processors.analysis.ai_heavy_researcher import AIHeavyDossierBuilder
        from src.processors.analysis.research_integration_service import get_research_integration_service

        deep_researcher = AIHeavyDeepResearcher()
        dossier_builder = AIHeavyDossierBuilder()
        integration_service = get_research_integration_service()

        return {
            "phase_1_5_split_architecture": {
                "examine_tab_deep_research": deep_researcher.get_deep_research_capabilities(),
                "approach_tab_dossier_builder": dossier_builder.get_approach_tab_capabilities(),
                "three_way_integration": integration_service.get_integration_status()
            },
            "workflow_architecture": {
                "analyze_tab": "AI-Lite comprehensive research and scoring",
                "examine_tab": "AI-Heavy deep research and strategic intelligence",
                "approach_tab": "AI-Heavy implementation planning and dossier building"
            },
            "data_flow": {
                "stage_1": "ANALYZE: AI-Lite research → preliminary analysis",
                "stage_2": "EXAMINE: Deep research → strategic intelligence",
                "stage_3": "APPROACH: Dossier building → implementation planning"
            },
            "cost_optimization": {
                "ai_lite_research": "$0.0008 per candidate",
                "deep_research_examine": "$0.08-0.15 per analysis",
                "dossier_builder_approach": "$0.12-0.20 per implementation plan"
            },
            "status": "Phase 1.5 Complete - AI-Heavy split architecture active"
        }
    except Exception as e:
        logger.error(f"Failed to get split research capabilities: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/research/integration-status/{opportunity_id}")
async def get_integration_status_endpoint(opportunity_id: str):
    """Get three-way integration status for an opportunity"""
    try:
        from src.processors.analysis.research_integration_service import get_research_integration_service

        integration_service = get_research_integration_service()
        integration_context = integration_service.get_complete_integration_context(opportunity_id)

        if not integration_context:
            return {
                "opportunity_id": opportunity_id,
                "integration_available": False,
                "workflow_stage": "none",
                "message": "No integration context found for this opportunity"
            }

        return {
            "opportunity_id": opportunity_id,
            "integration_available": True,
            "integration_completeness_score": integration_context.integration_completeness_score,
            "current_workflow_stage": integration_context.workflow_stage,
            "ai_lite_handoff_available": integration_context.ai_lite_handoff is not None,
            "deep_research_handoff_available": integration_context.deep_research_handoff is not None,
            "context_preservation_metadata": integration_context.context_preservation_metadata,
            "workflow_progression": {
                "analyze_completed": integration_context.ai_lite_handoff is not None,
                "examine_completed": integration_context.deep_research_handoff is not None,
                "approach_ready": integration_context.integration_completeness_score >= 0.67
            }
        }

    except Exception as e:
        logger.error(f"Failed to get integration status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Enhanced AI Analysis Endpoints
# =============================================================================

@router.post("/ai/lite-analysis")
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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/ai/deep-research")
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
        raise HTTPException(status_code=500, detail="Internal server error")


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


@router.get("/ai/analysis-status/{request_id}")
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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/ai/session-summary")
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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/ai/cost-estimates")
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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/ai/batch-analysis")
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
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Specialized AI Processor Endpoints - 5-Call Architecture Integration
# =============================================================================

@router.post("/ai/lite-1/validate")
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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/ai/lite-2/strategic-score")
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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/ai/heavy-light/analyze")
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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/ai/heavy-1/research-bridge")
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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/ai/orchestrated-pipeline")
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
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Phase 3: AI Research Platform Endpoints (Profile-scoped)
# =============================================================================

@router.post("/profiles/{profile_id}/research/analyze-integrated")
async def analyze_opportunity_integrated(profile_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform integrated scoring and research analysis for a specific opportunity"""
    try:
        # Import research integration system
        from src.analysis.research_scoring_integration import ResearchScoringIntegration
        from src.analysis.ai_research_platform import ReportFormat

        unified_service = _get_unified_service()

        opportunity_id = request_data.get('opportunity_id')
        include_research = request_data.get('include_research', True)
        report_type_str = request_data.get('report_type', 'executive_summary')

        if not opportunity_id:
            raise HTTPException(status_code=400, detail="opportunity_id required")

        # Get opportunity data
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Find the specific opportunity
        opportunity = None
        for opp in profile.opportunities:
            if opp.opportunity_id == opportunity_id:
                opportunity = opp.model_dump()
                break

        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        # Convert report type string to enum
        report_type_map = {
            'executive_summary': ReportFormat.EXECUTIVE_SUMMARY,
            'detailed_research': ReportFormat.DETAILED_RESEARCH,
            'decision_brief': ReportFormat.DECISION_BRIEF,
            'evaluation_summary': ReportFormat.EVALUATION_SUMMARY,
            'evidence_package': ReportFormat.EVIDENCE_PACKAGE
        }

        report_type = report_type_map.get(report_type_str, ReportFormat.EXECUTIVE_SUMMARY)

        # Perform integrated analysis
        async with ResearchScoringIntegration(cost_optimization=True) as integration:
            analysis = await integration.analyze_opportunity_integrated(
                opportunity, include_research, report_type
            )

        # Convert analysis to response format
        response = {
            'analysis_id': f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'opportunity_id': analysis.opportunity_id,
            'organization_name': analysis.organization_name,
            'integrated_results': {
                'integrated_score': analysis.integrated_score,
                'integrated_confidence': analysis.integrated_confidence,
                'evidence_strength': analysis.evidence_strength,
                'research_impact_factor': analysis.research_impact_factor,
                'recommended_action': analysis.recommended_action,
                'decision_confidence': analysis.decision_confidence
            },
            'scoring_results': analysis.scoring_results,
            'research_results': {
                'research_quality_score': analysis.research_quality_score,
                'research_confidence': analysis.research_confidence,
                'has_research_report': analysis.research_report is not None
            },
            'decision_support': {
                'next_steps': analysis.next_steps,
                'risk_factors': analysis.risk_factors
            },
            'performance_metrics': {
                'processing_time': analysis.processing_time,
                'cost_breakdown': analysis.cost_breakdown,
                'analysis_timestamp': analysis.analysis_timestamp.isoformat()
            }
        }

        # Add research report details if available
        if analysis.research_report:
            response['research_report'] = {
                'report_id': analysis.research_report.report_id,
                'report_type': analysis.research_report.report_type.value,
                'title': analysis.research_report.title,
                'executive_summary': analysis.research_report.executive_summary,
                'contacts_identified': len(analysis.research_report.contacts_identified),
                'evidence_facts': len(analysis.research_report.evidence_package),
                'recommendations': analysis.research_report.recommendations,
                'confidence_assessment': analysis.research_report.confidence_assessment
            }

        logger.info(f"Integrated analysis completed for {analysis.organization_name}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in integrated analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/profiles/{profile_id}/research/batch-analyze")
async def batch_analyze_opportunities(profile_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform batch integrated analysis for multiple opportunities"""
    try:
        from src.analysis.research_scoring_integration import ResearchScoringIntegration
        from src.analysis.ai_research_platform import ReportFormat

        unified_service = _get_unified_service()

        include_research = request_data.get('include_research', True)
        report_type_str = request_data.get('report_type', 'executive_summary')
        batch_size = request_data.get('batch_size')
        stage_filter = request_data.get('stage_filter', 'candidates')  # candidates, candidates+, all

        # Get profile and opportunities
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Filter opportunities based on stage
        opportunities = []
        for opp in profile.opportunities:
            stage = opp.current_stage

            if stage_filter == 'candidates' and stage not in ['pre_scoring', 'recommendations']:
                continue
            elif stage_filter == 'candidates+' and stage not in ['discovery', 'pre_scoring', 'recommendations']:
                continue
            # 'all' includes everything

            opportunities.append(opp.model_dump())

        if not opportunities:
            return {
                'batch_id': f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'message': 'No opportunities found matching filter criteria',
                'opportunities_processed': 0,
                'results': []
            }

        if len(opportunities) > 50:
            raise HTTPException(status_code=400, detail="Batch size cannot exceed 50 opportunities")

        # Convert report type
        report_type_map = {
            'executive_summary': ReportFormat.EXECUTIVE_SUMMARY,
            'detailed_research': ReportFormat.DETAILED_RESEARCH,
            'decision_brief': ReportFormat.DECISION_BRIEF,
            'evaluation_summary': ReportFormat.EVALUATION_SUMMARY,
            'evidence_package': ReportFormat.EVIDENCE_PACKAGE
        }

        report_type = report_type_map.get(report_type_str, ReportFormat.EXECUTIVE_SUMMARY)

        # Perform batch analysis
        async with ResearchScoringIntegration(cost_optimization=True) as integration:
            batch_result = await integration.batch_analyze_opportunities(
                opportunities, include_research, report_type, batch_size
            )

        # Convert results to response format
        analysis_results = []
        for analysis in batch_result.integrated_analyses:
            result = {
                'opportunity_id': analysis.opportunity_id,
                'organization_name': analysis.organization_name,
                'integrated_score': analysis.integrated_score,
                'integrated_confidence': analysis.integrated_confidence,
                'recommended_action': analysis.recommended_action,
                'decision_confidence': analysis.decision_confidence,
                'evidence_strength': analysis.evidence_strength,
                'processing_time': analysis.processing_time,
                'cost': analysis.cost_breakdown.get('total_cost', 0.0)
            }

            if analysis.research_report:
                result['research_summary'] = {
                    'quality_score': analysis.research_quality_score,
                    'contacts_found': len(analysis.research_report.contacts_identified),
                    'facts_extracted': len(analysis.research_report.evidence_package),
                    'recommendations_count': len(analysis.research_report.recommendations)
                }

            analysis_results.append(result)

        response = {
            'batch_id': batch_result.batch_id,
            'batch_summary': {
                'total_opportunities': batch_result.total_opportunities,
                'successful_analyses': batch_result.successful_analyses,
                'failed_analyses': batch_result.failed_analyses,
                'success_rate': batch_result.successful_analyses / batch_result.total_opportunities if batch_result.total_opportunities > 0 else 0,
                'total_processing_time': batch_result.total_processing_time,
                'total_cost': batch_result.total_cost,
                'average_cost_per_opportunity': batch_result.average_cost_per_opportunity,
                'average_confidence': batch_result.average_confidence,
                'quality_distribution': batch_result.quality_distribution
            },
            'analysis_results': analysis_results,
            'errors': batch_result.error_log,
            'batch_started': batch_result.batch_started.isoformat(),
            'batch_completed': batch_result.batch_completed.isoformat() if batch_result.batch_completed else None
        }

        logger.info(f"Batch analysis completed: {batch_result.successful_analyses}/{batch_result.total_opportunities} successful")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/profiles/{profile_id}/analyze/ai-lite")
async def ai_lite_profile_analysis(profile_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    AI-Lite analysis endpoint for ANALYZE tab integration

    Performs cost-effective candidate evaluation with dual-mode operation:
    - Scoring mode: Quick compatibility analysis (~$0.0001/candidate)
    - Research mode: Comprehensive research reports (~$0.0008/candidate)
    """
    try:
        logger.info(f"Starting AI-Lite analysis for profile {profile_id}")
        logger.info(f"Request data type: {type(request_data)}")

        unified_service = _get_unified_service()

        # Handle case where request_data might not be a dict
        try:
            if hasattr(request_data, 'dict'):
                request_dict = request_data.dict()
            elif hasattr(request_data, '__dict__'):
                request_dict = vars(request_data)
            elif isinstance(request_data, dict):
                request_dict = request_data
            else:
                logger.error(f"Unexpected request_data type: {type(request_data)}")
                raise HTTPException(status_code=400, detail=f"Invalid request format: {type(request_data)}")

            logger.info(f"Request dict type: {type(request_dict)}, keys: {list(request_dict.keys())}")

            # Validate request data
            candidates = request_dict.get("candidates", [])
            candidate_ids = request_dict.get("candidate_ids", [])
            analysis_type = request_dict.get("analysis_type", "compatibility_scoring")
            model_preference = request_dict.get("model_preference", "gpt-3.5-turbo")
            cost_limit = request_dict.get("cost_limit", 0.01)
            research_mode = request_dict.get("research_mode", False)

            logger.info(f"Parsed request: candidates={len(candidates)}, candidate_ids={candidate_ids}")

        except Exception as parse_error:
            logger.error(f"Failed to parse request data: {parse_error}")
            raise HTTPException(status_code=400, detail=f"Request parsing failed: {str(parse_error)}")

        # Handle both direct candidates and candidate IDs
        if not candidates and candidate_ids:
            logger.info(f"Looking for candidates with IDs: {candidate_ids}")
            # Fetch candidates by ID from the profile's opportunities
            profile_opportunities = unified_service.get_profile_opportunities(profile_id)
            logger.info(f"Profile has {len(profile_opportunities) if profile_opportunities else 0} opportunities")
            if profile_opportunities:
                candidates = []
                for i, opp in enumerate(profile_opportunities[:5]):  # Debug first 5 opportunities
                    # Handle both dictionary and object formats
                    opp_id = getattr(opp, 'id', None) or getattr(opp, 'opportunity_id', None) or (opp.get('id') if hasattr(opp, 'get') else None) or (opp.get('opportunity_id') if hasattr(opp, 'get') else None)
                    logger.info(f"Opportunity {i}: type={type(opp)}, id={opp_id}")
                    if opp_id in candidate_ids:
                        logger.info(f"Found matching candidate: {opp_id}")
                        # Convert object to dictionary format if needed
                        if hasattr(opp, 'dict'):
                            candidates.append(opp.dict())
                            logger.info(f"Converted with .dict() method")
                        elif hasattr(opp, '__dict__'):
                            candidates.append(vars(opp))
                            logger.info(f"Converted with vars()")
                        else:
                            candidates.append(opp)
                            logger.info(f"Used as-is")
                logger.info(f"Fetched {len(candidates)} candidates from {len(candidate_ids)} provided IDs")

        if not candidates:
            raise HTTPException(status_code=400, detail="No candidates provided for analysis")

        # Ensure all candidates are dictionaries
        processed_candidates = []
        for candidate in candidates:
            if hasattr(candidate, 'dict'):
                processed_candidates.append(candidate.dict())
            elif hasattr(candidate, '__dict__'):
                processed_candidates.append(vars(candidate))
            elif isinstance(candidate, dict):
                processed_candidates.append(candidate)
            else:
                logger.warning(f"Candidate type not supported: {type(candidate)}")
                continue

        logger.info(f"Processed {len(processed_candidates)} candidates for AI-Lite analysis")

        # Debug: Log candidate types and sample data
        for i, candidate in enumerate(processed_candidates[:2]):  # Log first 2 for debugging
            logger.info(f"Candidate {i}: type={type(candidate)}, keys={list(candidate.keys()) if isinstance(candidate, dict) else 'not a dict'}")

        if not processed_candidates:
            raise HTTPException(status_code=400, detail="No valid candidates after processing")

        # Get profile for context
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Legacy AI-Lite services - migrated to Tool 1 (Opportunity Screening)
        # from src.processors.analysis.ai_service_manager import get_ai_service_manager
        from src.analytics.cost_tracker import get_cost_tracker

        # ai_service = get_ai_service_manager()
        raise HTTPException(
            status_code=410,
            detail="Legacy AI-Lite endpoint deprecated. Use Tool 1 (Opportunity Screening Tool) via /api/v1/tools/opportunity-screening-tool/execute"
        )
        cost_tracker = get_cost_tracker()

        # Transform profile data for AI service compatibility
        profile_data = profile.model_dump()
        logger.info(f"Original profile geographic_scope: {profile_data.get('geographic_scope', 'NOT_FOUND')}")

        # Transform geographic_scope from dict to string
        if "geographic_scope" in profile_data:
            logger.info(f"Geographic scope type: {type(profile_data['geographic_scope'])}")
            if isinstance(profile_data["geographic_scope"], dict):
                logger.info("Transforming geographic_scope from dict to string")
                geo_scope = profile_data["geographic_scope"]
                scope_parts = []

                if geo_scope.get("nationwide", False):
                    scope_parts.append("Nationwide")
                elif geo_scope.get("international", False):
                    scope_parts.append("International")
                else:
                    # Build from states and regions
                    states = geo_scope.get("states", [])
                    regions = geo_scope.get("regions", [])

                    if states:
                        if len(states) == 1:
                            scope_parts.append(f"{states[0]} state")
                        else:
                            scope_parts.append(f"{', '.join(states)} states")

                    if regions:
                        scope_parts.append(f"{', '.join(regions)} region")

                # Default to "Local/Regional" if no specific scope defined
                profile_data["geographic_scope"] = " and ".join(scope_parts) if scope_parts else "Local/Regional"
                logger.info(f"Transformed geographic_scope to: '{profile_data['geographic_scope']}'")
            else:
                logger.info(f"Geographic scope is already a string: {profile_data['geographic_scope']}")
        else:
            logger.warning("No geographic_scope found in profile data")

        # Prepare AI-Lite request
        frontend_data = {
            "selected_profile": profile_data,
            "candidates": processed_candidates,
            "model_preference": model_preference,
            "cost_limit": cost_limit,
            "research_mode": research_mode,
            "analysis_type": analysis_type
        }

        # Check budget before processing
        from src.analytics.cost_tracker import AIService, CostCategory

        # Map model preference to AI service (GPT-5 models only)
        service_mapping = {
            "gpt-5-nano": AIService.OPENAI_GPT5_NANO,
            "gpt-5-mini": AIService.OPENAI_GPT5_MINI,
            "gpt-5": AIService.OPENAI_GPT5,
            "gpt-5-chat-latest": AIService.OPENAI_GPT5_CHAT_LATEST
        }

        service = service_mapping.get(model_preference, AIService.OPENAI_GPT5_NANO)

        # Estimate cost for all candidates
        avg_tokens = 1500 if not research_mode else 3000  # Research mode uses more tokens
        output_tokens = 300 if not research_mode else 800

        total_estimate = cost_tracker.estimate_cost(
            service=service,
            operation_type=CostCategory.AI_ANALYSIS,
            input_tokens=avg_tokens * len(processed_candidates),
            output_tokens=output_tokens * len(processed_candidates)
        )

        # Check if we can afford this operation
        can_run = True
        budget_message = "Budget validated"

        async with cost_tracker.lock:
            for budget in cost_tracker.budgets.values():
                if not budget.can_spend(total_estimate.estimated_cost_usd):
                    can_run = False
                    budget_message = f"Would exceed budget {budget.name} (${budget.remaining_budget()} remaining, ${total_estimate.estimated_cost_usd} needed)"
                    break

        if not can_run:
            return {
                "profile_id": profile_id,
                "analysis_type": "ai_lite",
                "status": "budget_exceeded",
                "message": budget_message,
                "cost_estimate": str(total_estimate.estimated_cost_usd),
                "candidates_count": len(candidates),
                "results": [],
                "budget_info": {
                    "estimated_cost": str(total_estimate.estimated_cost_usd),
                    "service": service.value,
                    "model": model_preference
                }
            }

        # Execute AI-Lite analysis
        logger.info(f"Frontend data geographic_scope: {frontend_data['selected_profile'].get('geographic_scope', 'NOT_FOUND')}")
        try:
            ai_lite_result = await ai_service.execute_ai_lite_analysis(frontend_data)

            # Format results for frontend
            analysis_results = []

            # Handle both dict and object response formats
            candidate_analyses = ai_lite_result.get("candidate_analyses", {}) if isinstance(ai_lite_result, dict) else getattr(ai_lite_result, "candidate_analyses", {})

            for candidate_id, analysis in candidate_analyses.items():
                # Handle both dict and object formats for analysis data
                if isinstance(analysis, dict):
                    result = {
                        "candidate_id": candidate_id,
                        "organization_name": analysis.get("organization_name", "Unknown"),
                        "compatibility_score": analysis.get("compatibility_score", 0.0),
                        "confidence_level": analysis.get("confidence_level", 0.0),
                        "recommendation": analysis.get("recommendation_summary", "No recommendation"),
                        "key_insights": analysis.get("key_insights", []),
                        "cost": str(analysis.get("processing_cost", 0.0)),
                        "processing_time": analysis.get("processing_time_seconds", 0.0)
                    }

                    if research_mode and "research_summary" in analysis:
                        result["research_summary"] = analysis["research_summary"]
                else:
                    result = {
                        "candidate_id": candidate_id,
                        "organization_name": getattr(analysis, "organization_name", "Unknown"),
                        "compatibility_score": getattr(analysis, "compatibility_score", 0.0),
                        "confidence_level": getattr(analysis, "confidence_level", 0.0),
                        "recommendation": getattr(analysis, "recommendation_summary", "No recommendation"),
                        "key_insights": getattr(analysis, "key_insights", []),
                        "cost": str(getattr(analysis, "processing_cost", 0.0)),
                        "processing_time": getattr(analysis, "processing_time_seconds", 0.0)
                    }

                    if research_mode and hasattr(analysis, 'research_summary'):
                        result["research_summary"] = analysis.research_summary

                analysis_results.append(result)

            # Handle both dict and object formats for ai_lite_result metadata
            if isinstance(ai_lite_result, dict):
                batch_id = ai_lite_result.get("batch_id", "unknown")
                successful_analyses = ai_lite_result.get("successful_analyses", len(analysis_results))
                failed_analyses = ai_lite_result.get("failed_analyses", 0)
                total_cost = ai_lite_result.get("total_cost", 0.0)
                average_cost = ai_lite_result.get("average_cost_per_candidate", 0.0)
                total_processing_time = ai_lite_result.get("total_processing_time", 0.0)
            else:
                batch_id = getattr(ai_lite_result, "batch_id", "unknown")
                successful_analyses = getattr(ai_lite_result, "successful_analyses", len(analysis_results))
                failed_analyses = getattr(ai_lite_result, "failed_analyses", 0)
                total_cost = getattr(ai_lite_result, "total_cost", 0.0)
                average_cost = getattr(ai_lite_result, "average_cost_per_candidate", 0.0)
                total_processing_time = getattr(ai_lite_result, "total_processing_time", 0.0)

            return {
                "profile_id": profile_id,
                "analysis_type": "ai_lite",
                "status": "completed",
                "batch_id": batch_id,
                "processing_summary": {
                    "total_candidates": len(processed_candidates),
                    "successful_analyses": successful_analyses,
                    "failed_analyses": failed_analyses,
                    "total_cost": str(total_cost),
                    "average_cost_per_candidate": str(average_cost),
                    "total_processing_time": total_processing_time,
                    "model_used": model_preference,
                    "research_mode": research_mode
                },
                "results": analysis_results,
                "cost_breakdown": {
                    "estimated_cost": str(total_estimate.estimated_cost_usd),
                    "actual_cost": str(total_cost),
                    "service": service.value,
                    "candidates_processed": len(analysis_results)
                },
                "budget_status": budget_message
            }

        except Exception as ai_error:
            logger.error(f"AI-Lite processing failed: {ai_error}")
            return {
                "profile_id": profile_id,
                "analysis_type": "ai_lite",
                "status": "processing_error",
                "message": f"AI analysis failed: {str(ai_error)}",
                "cost_estimate": str(total_estimate.estimated_cost_usd),
                "candidates_count": len(candidates),
                "results": []
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI-Lite profile analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/profiles/{profile_id}/research/decision-package/{opportunity_id}")
async def generate_decision_package(profile_id: str, opportunity_id: str) -> Dict[str, Any]:
    """Generate comprehensive decision package for grant team"""
    try:
        from src.analysis.research_scoring_integration import ResearchScoringIntegration
        from src.analysis.ai_research_platform import ReportFormat

        unified_service = _get_unified_service()

        # Get opportunity data
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        opportunity = None
        for opp in profile.opportunities:
            if opp.opportunity_id == opportunity_id:
                opportunity = opp.model_dump()
                break

        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        # Perform integrated analysis first
        async with ResearchScoringIntegration(cost_optimization=True) as integration:
            analysis = await integration.analyze_opportunity_integrated(
                opportunity, include_research=True, report_type=ReportFormat.EVALUATION_SUMMARY
            )

            # Generate decision package
            decision_package = await integration.generate_team_decision_package(analysis)

        logger.info(f"Decision package generated for {analysis.organization_name}")
        return decision_package

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating decision package: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/research/website-intelligence")
async def analyze_website_intelligence(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform website intelligence analysis"""
    try:
        from src.analysis.ai_research_platform import AIResearchPlatform

        url = request_data.get('url')
        opportunity_data = request_data.get('opportunity_data', {})

        if not url:
            raise HTTPException(status_code=400, detail="URL required")

        # Perform website analysis
        async with AIResearchPlatform(cost_optimization=True) as research_platform:
            intelligence = await research_platform.analyze_website(url, opportunity_data)

        # Convert to response format
        response = {
            'analysis_id': f"website_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'url': intelligence.url,
            'domain': intelligence.domain,
            'website_intelligence': {
                'title': intelligence.title,
                'description': intelligence.description,
                'organization_type': intelligence.organization_type,
                'quality_score': intelligence.quality_score,
                'program_areas': intelligence.program_areas,
                'funding_info': intelligence.funding_info
            },
            'contacts_identified': [
                {
                    'name': contact.name,
                    'title': contact.title,
                    'email': contact.email,
                    'phone': contact.phone,
                    'confidence': contact.confidence,
                    'source': contact.source
                }
                for contact in intelligence.contact_info
            ],
            'facts_extracted': [
                {
                    'fact': fact.fact,
                    'category': fact.category,
                    'confidence': fact.confidence,
                    'source': fact.source,
                    'date_extracted': fact.date_extracted.isoformat()
                }
                for fact in intelligence.key_facts
            ],
            'analysis_timestamp': intelligence.analysis_timestamp.isoformat()
        }

        logger.info(f"Website intelligence analysis completed for {url}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in website intelligence analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/research/performance-summary")
async def get_research_performance_summary() -> Dict[str, Any]:
    """Get research platform performance summary"""
    try:
        from src.analysis.research_scoring_integration import ResearchScoringIntegration

        # Get performance summary (this would be from a persistent service instance in production)
        async with ResearchScoringIntegration(cost_optimization=True) as integration:
            performance_summary = integration.get_performance_summary()

        # Add current timestamp
        performance_summary['retrieved_at'] = datetime.now().isoformat()

        return performance_summary

    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/research/export-results")
async def export_research_results(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Export research analysis results"""
    try:
        from src.analysis.research_scoring_integration import ResearchScoringIntegration, BatchAnalysisResult

        batch_id = request_data.get('batch_id')
        export_format = request_data.get('format', 'json')

        if not batch_id:
            raise HTTPException(status_code=400, detail="batch_id required")

        # In a full implementation, this would retrieve the actual batch result from storage
        # For now, return a mock export confirmation

        export_data = {
            'export_id': f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'batch_id': batch_id,
            'export_format': export_format,
            'exported_at': datetime.now().isoformat(),
            'status': 'completed',
            'message': f'Research results exported in {export_format} format'
        }

        logger.info(f"Research results export initiated for batch {batch_id}")
        return export_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting research results: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Legacy AI Service Manager (deprecated - module removed)
# These endpoints reference get_ai_service_manager which no longer exists.
# They are preserved for backward compatibility but will fail at runtime.
# Use Tool 1 (Opportunity Screening) and Tool 2 (Deep Intelligence) instead.
# =============================================================================

def get_ai_service_manager():
    """
    Legacy stub for deprecated AI service manager.
    The original module (src.processors.analysis.ai_service_manager) has been removed
    as part of the 12-factor tool migration.
    """
    raise ImportError(
        "get_ai_service_manager has been removed. "
        "Use Tool 1 (Opportunity Screening Tool) or Tool 2 (Deep Intelligence Tool) instead. "
        "See /api/v1/tools/ for the new tool-based API."
    )
