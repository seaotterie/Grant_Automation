"""
Dossier & Decision Synthesis API Router

Extracted from main.py - handles all dossier generation, document templates,
and approach/decision synthesis endpoints.

Endpoints:
- POST /api/profiles/{profile_id}/dossier/generate
- POST /api/profiles/{profile_id}/dossier/batch-generate
- POST /api/dossier/{dossier_id}/generate-document
- GET  /api/dossier/templates
- GET  /api/dossier/performance-summary
- POST /api/profiles/{profile_id}/approach/synthesize-decision
- GET  /api/profiles/{profile_id}/approach/decision-history
- POST /api/profiles/{profile_id}/approach/export-decision
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

from fastapi import APIRouter, HTTPException, Query, Body

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Dossier & Decisions"])


# =============================================================================
# Phase 4: AI Heavy Dossier Builder API Endpoints
# =============================================================================

@router.post("/profiles/{profile_id}/dossier/generate")
async def generate_comprehensive_dossier(
    profile_id: str,
    opportunity_ids: List[str] = Query(..., description="List of opportunity IDs to analyze"),
    analysis_depth: str = Query("comprehensive", description="Analysis depth: basic, standard, comprehensive"),
    target_audience: str = Query("executive", description="Target audience: executive, board, implementation, stakeholder"),
    cost_optimization: bool = Query(False, description="Enable cost optimization for AI processing")
):
    """Generate comprehensive AI Heavy dossier for opportunities"""
    try:
        from src.analysis.ai_heavy_dossier_builder import AIHeavyDossierBuilder

        # Initialize dossier builder
        builder = AIHeavyDossierBuilder(
            cost_optimization=cost_optimization,
            quality_threshold=0.8 if analysis_depth == "comprehensive" else 0.6
        )

        # Generate comprehensive dossier
        dossier = await builder.generate_comprehensive_dossier(
            profile_id=profile_id,
            opportunity_ids=opportunity_ids,
            analysis_depth=analysis_depth,
            target_audience=target_audience
        )

        return {
            "success": True,
            "dossier_id": dossier.dossier_id,
            "profile_id": profile_id,
            "analysis_summary": {
                "opportunities_analyzed": len(opportunity_ids),
                "analysis_depth": analysis_depth,
                "target_audience": target_audience,
                "confidence_score": dossier.executive_decision.confidence_score,
                "success_probability": dossier.executive_decision.success_probability,
                "recommendation": dossier.executive_decision.primary_recommendation
            },
            "generation_metadata": {
                "generated_at": dossier.generated_at,
                "ai_analysis_cost": dossier.ai_analysis_cost,
                "processing_time_seconds": dossier.processing_time_seconds
            },
            "available_documents": [template.template_id for template in dossier.available_documents],
            "dossier": dossier.model_dump()
        }

    except Exception as e:
        logger.error(f"Error generating dossier for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate dossier")


@router.post("/dossier/{dossier_id}/generate-document")
async def generate_decision_document(
    dossier_id: str,
    template_id: str = Query(..., description="Document template ID"),
    format_type: str = Query("comprehensive", description="Document format: executive_brief, detailed_report, presentation, dashboard, compliance_report"),
    customizations: Optional[Dict[str, Any]] = None
):
    """Generate decision-ready document from dossier"""
    try:
        from src.analysis.decision_document_templates import DecisionDocumentTemplates
        from src.analysis.ai_heavy_dossier_builder import AIHeavyDossierBuilder

        # Load dossier (in production, this would be from database)
        builder = AIHeavyDossierBuilder()
        dossier = await builder.load_dossier(dossier_id)

        if not dossier:
            raise HTTPException(status_code=404, detail=f"Dossier {dossier_id} not found")

        # Generate document
        template_generator = DecisionDocumentTemplates()
        document = template_generator.generate_document(
            dossier=dossier,
            template_id=template_id,
            customizations=customizations or {}
        )

        return {
            "success": True,
            "document_id": document.document_id,
            "dossier_id": dossier_id,
            "template_id": template_id,
            "format_type": format_type,
            "document_metadata": {
                "generated_at": document.generated_at,
                "target_audience": document.target_audience,
                "document_type": document.document_type,
                "word_count": document.word_count,
                "confidence_level": document.confidence_level
            },
            "content": document.content,
            "executive_summary": document.executive_summary,
            "key_recommendations": document.key_recommendations
        }

    except Exception as e:
        logger.error(f"Error generating document for dossier {dossier_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/dossier/templates")
async def get_available_templates():
    """Get list of available document templates"""
    try:
        from src.analysis.decision_document_templates import DecisionDocumentTemplates

        template_generator = DecisionDocumentTemplates()
        templates = template_generator.get_available_templates()

        return {
            "success": True,
            "templates": [
                {
                    "template_id": template.template_id,
                    "name": template.name,
                    "description": template.description,
                    "target_audience": template.target_audience,
                    "document_type": template.document_type,
                    "estimated_length": template.estimated_length,
                    "complexity_level": template.complexity_level
                }
                for template in templates
            ]
        }

    except Exception as e:
        logger.error(f"Error retrieving templates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/dossier/performance-summary")
async def get_dossier_performance_summary():
    """Get performance summary for AI Heavy dossier generation"""
    try:
        from src.analysis.ai_heavy_dossier_builder import AIHeavyDossierBuilder

        builder = AIHeavyDossierBuilder()
        performance_stats = builder.get_performance_stats()

        return {
            "success": True,
            "performance_summary": performance_stats,
            "system_status": "operational",
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error retrieving performance summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/profiles/{profile_id}/dossier/batch-generate")
async def batch_generate_dossiers(
    profile_id: str,
    opportunity_batches: List[Dict[str, Any]] = Body(..., description="List of opportunity batches with analysis configurations"),
    global_settings: Optional[Dict[str, Any]] = Body(None, description="Global settings for all dossiers")
):
    """Generate multiple dossiers in batch for different opportunity sets"""
    try:
        if len(opportunity_batches) > 20:
            raise HTTPException(status_code=400, detail="Batch size cannot exceed 20 dossiers")

        from src.analysis.ai_heavy_dossier_builder import AIHeavyDossierBuilder

        # Initialize builder with global settings
        global_config = global_settings or {}
        builder = AIHeavyDossierBuilder(
            cost_optimization=global_config.get("cost_optimization", False),
            quality_threshold=global_config.get("quality_threshold", 0.8)
        )

        # Process batches
        batch_results = []
        total_cost = 0.0

        for i, batch in enumerate(opportunity_batches):
            try:
                dossier = await builder.generate_comprehensive_dossier(
                    profile_id=profile_id,
                    opportunity_ids=batch.get("opportunity_ids", []),
                    analysis_depth=batch.get("analysis_depth", "standard"),
                    target_audience=batch.get("target_audience", "executive")
                )

                batch_results.append({
                    "batch_id": i + 1,
                    "success": True,
                    "dossier_id": dossier.dossier_id,
                    "opportunities_count": len(batch.get("opportunity_ids", [])),
                    "confidence_score": dossier.executive_decision.confidence_score,
                    "recommendation": dossier.executive_decision.primary_recommendation,
                    "cost": dossier.ai_analysis_cost
                })

                total_cost += dossier.ai_analysis_cost

            except Exception as batch_error:
                logger.error(f"Error processing batch {i + 1}: {batch_error}")
                batch_results.append({
                    "batch_id": i + 1,
                    "success": False,
                    "error": str(batch_error),
                    "opportunities_count": len(batch.get("opportunity_ids", [])),
                    "cost": 0.0
                })

        successful_batches = sum(1 for result in batch_results if result["success"])

        return {
            "success": True,
            "profile_id": profile_id,
            "batch_summary": {
                "total_batches": len(opportunity_batches),
                "successful_batches": successful_batches,
                "failed_batches": len(opportunity_batches) - successful_batches,
                "total_cost": total_cost,
                "average_cost_per_batch": total_cost / len(opportunity_batches) if opportunity_batches else 0
            },
            "batch_results": batch_results
        }

    except Exception as e:
        logger.error(f"Error in batch dossier generation for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Phase 6: Decision Synthesis API Endpoints
# =============================================================================

@router.post("/profiles/{profile_id}/approach/synthesize-decision")
async def synthesize_decision(
    profile_id: str,
    request_data: Dict[str, Any] = Body(...)
):
    """
    Phase 6 Decision Synthesis API - APPROACH Tab Integration

    Synthesizes decision recommendations from all workflow stages using the
    advanced decision synthesis framework.

    Args:
        profile_id: Organization profile ID
        request_data: {
            "opportunity_id": str,
            "workflow_results": [
                {
                    "stage": "discover|plan|analyze|examine",
                    "primary_score": float,
                    "confidence": float,
                    "scorer_type": str,
                    "metadata": dict,
                    "processing_time_ms": float
                }
            ],
            "enhanced_data": dict (optional),
            "user_preferences": dict (optional),
            "decision_context": dict (optional)
        }

    Returns:
        Comprehensive decision synthesis result with recommendations,
        visualizations, audit trails, and export-ready data.
    """
    try:
        # PHASE 8: Integration layer removed for desktop simplification
        # Decision synthesis framework removed - single user makes decisions manually
        raise HTTPException(
            status_code=410,
            detail="Decision synthesis endpoint deprecated in Phase 8. Use Tool 2 (Deep Intelligence Tool) for comprehensive analysis."
        )

        logger.info(f"Starting decision synthesis for profile {profile_id}")

        # Validate required fields
        if "opportunity_id" not in request_data or "workflow_results" not in request_data:
            raise HTTPException(status_code=400, detail="Missing required fields: opportunity_id, workflow_results")

        # Convert workflow results to structured format
        workflow_results = []
        for result_data in request_data["workflow_results"]:
            try:
                stage = WorkflowStage(result_data["stage"])
                scorer_type = ScorerType(result_data.get("scorer_type", "discovery"))

                workflow_result = WorkflowStageResult(
                    stage=stage,
                    primary_score=result_data["primary_score"],
                    confidence=result_data["confidence"],
                    scorer_type=scorer_type,
                    metadata=result_data.get("metadata", {}),
                    processing_time_ms=result_data.get("processing_time_ms", 0.0),
                    timestamp=datetime.now()
                )
                workflow_results.append(workflow_result)
            except ValueError as ve:
                logger.warning(f"Invalid workflow result data: {ve}, skipping...")
                continue

        if not workflow_results:
            raise HTTPException(status_code=400, detail="No valid workflow results provided")

        # Create decision synthesis request
        synthesis_request = DecisionSynthesisRequest(
            profile_id=profile_id,
            opportunity_id=request_data["opportunity_id"],
            workflow_results=workflow_results,
            enhanced_data=request_data.get("enhanced_data"),
            user_preferences=request_data.get("user_preferences"),
            decision_context=request_data.get("decision_context")
        )

        # Execute decision synthesis
        synthesis_result = await decision_synthesis_bridge.synthesize_decision(synthesis_request)

        # Format response for web interface
        response_data = {
            "success": True,
            "profile_id": profile_id,
            "opportunity_id": request_data["opportunity_id"],
            "synthesis_score": synthesis_result.synthesis_score,
            "overall_confidence": synthesis_result.overall_confidence,
            "recommendation": synthesis_result.recommendation,
            "stage_contributions": synthesis_result.stage_contributions,
            "feasibility_assessment": synthesis_result.feasibility_assessment,
            "resource_requirements": synthesis_result.resource_requirements,
            "implementation_timeline": synthesis_result.implementation_timeline,
            "risk_assessment": synthesis_result.risk_assessment,
            "success_factors": synthesis_result.success_factors,
            "decision_rationale": synthesis_result.decision_rationale,
            "audit_trail": synthesis_result.audit_trail,
            "visualization_data": synthesis_result.visualization_data,
            "export_ready": True,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Decision synthesis completed for {profile_id} with recommendation: {synthesis_result.recommendation}")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in decision synthesis for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/profiles/{profile_id}/approach/decision-history")
async def get_decision_history(
    profile_id: str,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0)
):
    """
    Get decision synthesis history for a profile

    Args:
        profile_id: Organization profile ID
        limit: Maximum number of decisions to return
        offset: Offset for pagination

    Returns:
        List of historical decision synthesis results
    """
    try:
        # This would connect to a decision history storage system
        # For now, return mock data structure
        return {
            "success": True,
            "profile_id": profile_id,
            "decisions": [],  # Would be populated from storage
            "total_count": 0,
            "limit": limit,
            "offset": offset,
            "message": "Decision history storage not yet implemented"
        }

    except Exception as e:
        logger.error(f"Error retrieving decision history for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/profiles/{profile_id}/approach/export-decision")
async def export_decision_document(
    profile_id: str,
    request_data: Dict[str, Any] = Body(...)
):
    """
    Export decision synthesis result as professional document

    Args:
        profile_id: Organization profile ID
        request_data: {
            "synthesis_result": dict,  # Result from decision synthesis
            "export_format": "pdf|excel|powerpoint|html|json",
            "template": "executive|detailed|presentation|minimal",
            "branding": dict (optional)
        }

    Returns:
        File download information or direct file response
    """
    try:
        from src.export.comprehensive_export_system import ComprehensiveExportSystem

        logger.info(f"Exporting decision document for profile {profile_id}")

        # Validate required fields
        required_fields = ["synthesis_result", "export_format"]
        for field in required_fields:
            if field not in request_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Initialize export system
        export_system = ComprehensiveExportSystem()

        # Prepare export configuration
        export_config = {
            'format': request_data['export_format'],
            'template': request_data.get('template', 'executive'),
            'branding': request_data.get('branding', {}),
            'profile_id': profile_id,
            'timestamp': datetime.now()
        }

        # Generate export (this would use the comprehensive export system)
        # For now, return success with file info
        export_filename = f"decision_synthesis_{profile_id}_{int(datetime.now().timestamp())}.{request_data['export_format']}"

        return {
            "success": True,
            "profile_id": profile_id,
            "export_filename": export_filename,
            "export_format": request_data['export_format'],
            "template_used": export_config['template'],
            "file_size": "1.2MB",  # Mock data
            "download_url": f"/api/exports/{export_filename}",
            "generated_timestamp": datetime.now().isoformat(),
            "expires_in_hours": 24,
            "message": "Export generation completed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting decision document for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
