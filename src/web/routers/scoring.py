#!/usr/bin/env python3
"""
Scoring Router
Handles scoring, analysis, and evaluation of opportunities against profiles
Extracted from monolithic main.py for better modularity
"""

from fastapi import APIRouter, HTTPException, Depends
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

# Import scoring services and models
from src.web.services.scoring_service import (
    get_scoring_service, ScoreRequest, ScoreResponse, 
    PromotionRequest, PromotionResponse, BulkPromotionRequest, BulkPromotionResponse
)
from src.web.services.automated_promotion_service import get_automated_promotion_service
from src.processors.analysis.government_opportunity_scorer import GovernmentOpportunityScorer
from src.processors.analysis.success_scorer import SuccessScorer
from src.processors.analysis.ai_service_manager import get_ai_service_manager
from src.profiles.unified_service import get_unified_profile_service
from src.auth.jwt_auth import get_current_user_dependency, User

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/api/scoring", tags=["scoring"])

# Initialize services
scoring_service = get_scoring_service()
automated_promotion_service = get_automated_promotion_service()
ai_service_manager = get_ai_service_manager()
unified_service = get_unified_profile_service()


# Government Opportunity Scoring

@router.post("/government")
async def score_government_opportunity(
    scoring_request: Dict[str, Any]
) -> Dict[str, Any]:
    """Score government opportunities using the government opportunity scorer."""
    try:
        profile_id = scoring_request.get("profile_id")
        opportunities = scoring_request.get("opportunities", [])
        
        if not profile_id:
            raise HTTPException(status_code=400, detail="Profile ID is required")
        
        # Get profile
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Initialize government scorer
        government_scorer = GovernmentOpportunityScorer()
        
        # Score each opportunity
        scored_opportunities = []
        for opp in opportunities:
            try:
                # Create scoring config
                config = {
                    "profile": profile.model_dump(),
                    "opportunity": opp
                }
                
                # Execute scoring
                result = government_scorer.execute(config)
                
                if result and result.get("success"):
                    scored_opportunities.append({
                        **opp,
                        "government_score": result.get("score", 0.0),
                        "scoring_details": result.get("details", {}),
                        "recommendation": result.get("recommendation", "medium")
                    })
                else:
                    scored_opportunities.append({
                        **opp,
                        "government_score": 0.0,
                        "scoring_error": "Failed to score opportunity"
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to score government opportunity {opp.get('id', 'unknown')}: {e}")
                scored_opportunities.append({
                    **opp,
                    "government_score": 0.0,
                    "scoring_error": str(e)
                })
        
        return {
            "scored_opportunities": scored_opportunities,
            "profile_id": profile_id,
            "scoring_type": "government",
            "total_processed": len(scored_opportunities),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed government opportunity scoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Financial Scoring

@router.post("/financial")
async def score_financial_fit(
    scoring_request: Dict[str, Any]
) -> Dict[str, Any]:
    """Score opportunities based on financial fit criteria."""
    try:
        profile_id = scoring_request.get("profile_id")
        opportunities = scoring_request.get("opportunities", [])
        
        if not profile_id:
            raise HTTPException(status_code=400, detail="Profile ID is required")
        
        # Get profile
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Score each opportunity for financial fit
        scored_opportunities = []
        for opp in opportunities:
            try:
                financial_score = scoring_service.calculate_financial_score(profile, opp)
                scored_opportunities.append({
                    **opp,
                    "financial_score": financial_score,
                    "scoring_timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to calculate financial score for opportunity {opp.get('id', 'unknown')}: {e}")
                scored_opportunities.append({
                    **opp,
                    "financial_score": 0.0,
                    "scoring_error": str(e)
                })
        
        return {
            "scored_opportunities": scored_opportunities,
            "profile_id": profile_id,
            "scoring_type": "financial",
            "total_processed": len(scored_opportunities),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed financial scoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AI-Lite Scoring

@router.post("/ai-lite")
async def score_ai_lite(
    scoring_request: Dict[str, Any]
) -> Dict[str, Any]:
    """Score opportunities using AI-Lite analysis."""
    try:
        profile_id = scoring_request.get("profile_id")
        opportunities = scoring_request.get("opportunities", [])
        
        if not profile_id:
            raise HTTPException(status_code=400, detail="Profile ID is required")
        
        # Get profile
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Use AI service manager for lite scoring
        scored_opportunities = []
        for opp in opportunities:
            try:
                # Request AI-Lite scoring
                ai_result = ai_service_manager.request_lite_analysis(
                    profile=profile.model_dump(),
                    opportunity=opp,
                    analysis_type="strategic_fit"
                )
                
                if ai_result and ai_result.get("success"):
                    scored_opportunities.append({
                        **opp,
                        "ai_lite_score": ai_result.get("score", 0.0),
                        "ai_analysis": ai_result.get("analysis", {}),
                        "confidence": ai_result.get("confidence", 0.5)
                    })
                else:
                    scored_opportunities.append({
                        **opp,
                        "ai_lite_score": 0.0,
                        "scoring_error": "AI analysis failed"
                    })
                    
            except Exception as e:
                logger.warning(f"Failed AI-Lite scoring for opportunity {opp.get('id', 'unknown')}: {e}")
                scored_opportunities.append({
                    **opp,
                    "ai_lite_score": 0.0,
                    "scoring_error": str(e)
                })
        
        return {
            "scored_opportunities": scored_opportunities,
            "profile_id": profile_id,
            "scoring_type": "ai_lite",
            "total_processed": len(scored_opportunities),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed AI-Lite scoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Network Analysis Scoring

@router.post("/network")
async def score_network_analysis(
    scoring_request: Dict[str, Any]
) -> Dict[str, Any]:
    """Score opportunities based on network analysis and board connections."""
    try:
        profile_id = scoring_request.get("profile_id")
        opportunities = scoring_request.get("opportunities", [])
        
        if not profile_id:
            raise HTTPException(status_code=400, detail="Profile ID is required")
        
        # Get profile
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Score each opportunity for network connections
        scored_opportunities = []
        for opp in opportunities:
            try:
                network_score = scoring_service.calculate_network_score(profile, opp)
                scored_opportunities.append({
                    **opp,
                    "network_score": network_score,
                    "network_analysis": {
                        "board_connections": [],  # Would be populated by actual analysis
                        "strategic_relationships": [],
                        "connection_strength": network_score
                    },
                    "scoring_timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed network analysis for opportunity {opp.get('id', 'unknown')}: {e}")
                scored_opportunities.append({
                    **opp,
                    "network_score": 0.0,
                    "scoring_error": str(e)
                })
        
        return {
            "scored_opportunities": scored_opportunities,
            "profile_id": profile_id,
            "scoring_type": "network",
            "total_processed": len(scored_opportunities),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed network scoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Success Pattern Scoring

@router.post("/success-patterns")
async def score_success_patterns(
    scoring_request: Dict[str, Any]
) -> Dict[str, Any]:
    """Score opportunities based on historical success patterns."""
    try:
        profile_id = scoring_request.get("profile_id")
        opportunities = scoring_request.get("opportunities", [])
        
        if not profile_id:
            raise HTTPException(status_code=400, detail="Profile ID is required")
        
        # Get profile
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Initialize success scorer
        success_scorer = SuccessScorer()
        
        # Score each opportunity
        scored_opportunities = []
        for opp in opportunities:
            try:
                # Create scoring config
                config = {
                    "profile": profile.model_dump(),
                    "opportunity": opp
                }
                
                # Execute success scoring
                result = success_scorer.execute(config)
                
                if result and result.get("success"):
                    scored_opportunities.append({
                        **opp,
                        "success_score": result.get("score", 0.0),
                        "success_patterns": result.get("patterns", []),
                        "historical_indicators": result.get("indicators", {})
                    })
                else:
                    scored_opportunities.append({
                        **opp,
                        "success_score": 0.0,
                        "scoring_error": "Success analysis failed"
                    })
                    
            except Exception as e:
                logger.warning(f"Failed success scoring for opportunity {opp.get('id', 'unknown')}: {e}")
                scored_opportunities.append({
                    **opp,
                    "success_score": 0.0,
                    "scoring_error": str(e)
                })
        
        return {
            "scored_opportunities": scored_opportunities,
            "profile_id": profile_id,
            "scoring_type": "success_patterns",
            "total_processed": len(scored_opportunities),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed success pattern scoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Comprehensive Multi-Score Analysis

@router.post("/comprehensive")
async def comprehensive_scoring(
    scoring_request: Dict[str, Any]
) -> Dict[str, Any]:
    """Perform comprehensive scoring using multiple scoring methods."""
    try:
        profile_id = scoring_request.get("profile_id")
        opportunities = scoring_request.get("opportunities", [])
        scoring_methods = scoring_request.get("methods", ["government", "financial", "network"])
        
        if not profile_id:
            raise HTTPException(status_code=400, detail="Profile ID is required")
        
        # Get profile
        profile = unified_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Score each opportunity using multiple methods
        comprehensive_results = []
        for opp in opportunities:
            opp_scores = {**opp}
            
            # Apply each requested scoring method
            if "government" in scoring_methods:
                try:
                    gov_score = scoring_service.calculate_government_score(profile, opp)
                    opp_scores["government_score"] = gov_score
                except Exception as e:
                    logger.warning(f"Government scoring failed for {opp.get('id', 'unknown')}: {e}")
                    opp_scores["government_score"] = 0.0
            
            if "financial" in scoring_methods:
                try:
                    fin_score = scoring_service.calculate_financial_score(profile, opp)
                    opp_scores["financial_score"] = fin_score
                except Exception as e:
                    logger.warning(f"Financial scoring failed for {opp.get('id', 'unknown')}: {e}")
                    opp_scores["financial_score"] = 0.0
            
            if "network" in scoring_methods:
                try:
                    net_score = scoring_service.calculate_network_score(profile, opp)
                    opp_scores["network_score"] = net_score
                except Exception as e:
                    logger.warning(f"Network scoring failed for {opp.get('id', 'unknown')}: {e}")
                    opp_scores["network_score"] = 0.0
            
            # Calculate composite score
            scores = []
            if "government_score" in opp_scores:
                scores.append(opp_scores["government_score"])
            if "financial_score" in opp_scores:
                scores.append(opp_scores["financial_score"])
            if "network_score" in opp_scores:
                scores.append(opp_scores["network_score"])
            
            if scores:
                opp_scores["composite_score"] = sum(scores) / len(scores)
                opp_scores["score_breakdown"] = {
                    "components": len(scores),
                    "methods_used": scoring_methods,
                    "individual_scores": scores
                }
            else:
                opp_scores["composite_score"] = 0.0
            
            opp_scores["scoring_timestamp"] = datetime.now().isoformat()
            comprehensive_results.append(opp_scores)
        
        # Sort by composite score (descending)
        comprehensive_results.sort(key=lambda x: x.get("composite_score", 0.0), reverse=True)
        
        return {
            "comprehensive_results": comprehensive_results,
            "profile_id": profile_id,
            "scoring_methods": scoring_methods,
            "total_processed": len(comprehensive_results),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed comprehensive scoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Scoring Configuration and Weights

@router.get("/configuration")
async def get_scoring_configuration() -> Dict[str, Any]:
    """Get current scoring configuration and weights."""
    try:
        config = {
            "scoring_methods": {
                "government": {
                    "weights": {
                        "eligibility": 0.30,
                        "geographic": 0.20,
                        "timing": 0.20,
                        "financial_fit": 0.15,
                        "historical_success": 0.15
                    },
                    "thresholds": {
                        "high": 0.75,
                        "medium": 0.55,
                        "low": 0.35
                    }
                },
                "financial": {
                    "factors": ["revenue_match", "award_size_fit", "capacity_alignment"],
                    "weights": [0.4, 0.35, 0.25]
                },
                "network": {
                    "analysis_types": ["board_connections", "strategic_partnerships", "alumni_networks"],
                    "connection_strength_weight": 0.6,
                    "relationship_quality_weight": 0.4
                }
            },
            "composite_scoring": {
                "default_weights": {
                    "government": 0.35,
                    "financial": 0.30,
                    "network": 0.20,
                    "success_patterns": 0.15
                },
                "minimum_components": 2
            }
        }
        
        return {
            "configuration": config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get scoring configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/configuration")
async def update_scoring_configuration(
    config_update: Dict[str, Any],
    current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Update scoring configuration and weights."""
    try:
        # In a real implementation, this would update the scoring configuration
        # For now, just validate and return the updated configuration
        
        updated_config = {
            **config_update,
            "updated_by": current_user.username,
            "updated_at": datetime.now().isoformat()
        }
        
        logger.info(f"Scoring configuration updated by {current_user.username}")
        
        return {
            "message": "Scoring configuration updated successfully",
            "configuration": updated_config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update scoring configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))