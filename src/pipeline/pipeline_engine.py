"""
4-Stage Processing Pipeline Engine
Orchestrates Discovery → Pre-scoring → Deep Analysis → Recommendations
"""
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from src.profiles.models import OrganizationProfile, FundingType, PipelineStage
from src.discovery.discovery_engine import discovery_engine, DiscoveryResult


class ProcessingPriority(str, Enum):
    """Processing priority levels for resource allocation"""
    LOW = "low"
    STANDARD = "standard" 
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution"""
    profile_id: str
    funding_types: List[FundingType]
    priority: ProcessingPriority = ProcessingPriority.STANDARD
    
    # Stage limits for resource allocation
    discovery_limit: int = 1000
    pre_scoring_limit: int = 200
    deep_analysis_limit: int = 50
    final_recommendations: int = 15
    
    # Quality thresholds
    min_compatibility_score: float = 0.3
    pre_scoring_threshold: float = 0.5
    deep_analysis_threshold: float = 0.7
    
    # Resource constraints
    max_processing_time_minutes: int = 30
    max_concurrent_operations: int = 5


@dataclass 
class StageResult:
    """Results from a pipeline stage"""
    stage: PipelineStage
    opportunities_in: int
    opportunities_out: int
    processing_time_seconds: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class ProcessingPipeline:
    """4-Stage opportunity processing pipeline with intelligent resource allocation"""
    
    def __init__(self):
        self.active_pipelines: Dict[str, Dict[str, Any]] = {}
    
    async def execute_pipeline(
        self,
        profile: OrganizationProfile,
        config: PipelineConfig,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Execute complete 4-stage pipeline"""
        
        pipeline_id = f"pipeline_{config.profile_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize pipeline tracking
        pipeline_state = {
            "pipeline_id": pipeline_id,
            "profile": profile,
            "config": config,
            "stage_results": [],
            "current_opportunities": [],
            "started_at": datetime.now(),
            "status": "running"
        }
        
        self.active_pipelines[pipeline_id] = pipeline_state
        
        try:
            # Stage 1: Discovery (find thousands)
            discovery_result = await self._execute_discovery_stage(
                pipeline_state, progress_callback
            )
            pipeline_state["stage_results"].append(discovery_result)
            
            if not discovery_result.success:
                return self._finalize_pipeline(pipeline_state, "failed", discovery_result.error)
            
            # Stage 2: Pre-scoring (filter to hundreds) 
            pre_scoring_result = await self._execute_pre_scoring_stage(
                pipeline_state, progress_callback
            )
            pipeline_state["stage_results"].append(pre_scoring_result)
            
            # Stage 3: Deep Analysis (analyze tens)
            deep_analysis_result = await self._execute_deep_analysis_stage(
                pipeline_state, progress_callback
            )
            pipeline_state["stage_results"].append(deep_analysis_result)
            
            # Stage 4: Recommendations (final 15-20)
            recommendations_result = await self._execute_recommendations_stage(
                pipeline_state, progress_callback
            )
            pipeline_state["stage_results"].append(recommendations_result)
            
            return self._finalize_pipeline(pipeline_state, "completed")
            
        except Exception as e:
            return self._finalize_pipeline(pipeline_state, "error", str(e))
    
    async def _execute_discovery_stage(
        self, 
        pipeline_state: Dict[str, Any],
        progress_callback: Optional[Callable]
    ) -> StageResult:
        """Stage 1: Discovery - Find initial opportunities"""
        
        start_time = datetime.now()
        config = pipeline_state["config"]
        profile = pipeline_state["profile"]
        
        if progress_callback:
            progress_callback("discovery", {"status": "starting", "stage": 1, "message": "Beginning opportunity discovery across all funding types"})
        
        try:
            # Execute multi-track discovery
            discovery_session = await discovery_engine.discover_opportunities(
                profile=profile,
                funding_types=config.funding_types,
                max_results_per_type=config.discovery_limit,
                progress_callback=lambda sid, data: progress_callback("discovery", data) if progress_callback else None
            )
            
            # Get raw results
            raw_opportunities = discovery_engine.get_session_results(discovery_session.session_id)
            
            # Store for next stage
            pipeline_state["current_opportunities"] = raw_opportunities
            pipeline_state["discovery_session_id"] = discovery_session.session_id
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if progress_callback:
                progress_callback("discovery", {
                    "status": "completed", 
                    "stage": 1, 
                    "opportunities_found": len(raw_opportunities),
                    "processing_time": processing_time
                })
            
            return StageResult(
                stage=PipelineStage.DISCOVERY,
                opportunities_in=0,
                opportunities_out=len(raw_opportunities),
                processing_time_seconds=processing_time,
                success=True,
                metadata={
                    "funding_types_searched": [ft.value for ft in config.funding_types],
                    "discovery_session_id": discovery_session.session_id,
                    "avg_compatibility_score": sum(opp.compatibility_score for opp in raw_opportunities) / len(raw_opportunities) if raw_opportunities else 0
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return StageResult(
                stage=PipelineStage.DISCOVERY,
                opportunities_in=0,
                opportunities_out=0,
                processing_time_seconds=processing_time,
                success=False,
                error=str(e)
            )
    
    async def _execute_pre_scoring_stage(
        self,
        pipeline_state: Dict[str, Any],
        progress_callback: Optional[Callable]
    ) -> StageResult:
        """Stage 2: Pre-scoring - Fast filtering of opportunities"""
        
        start_time = datetime.now()
        config = pipeline_state["config"]
        opportunities = pipeline_state["current_opportunities"]
        
        if progress_callback:
            progress_callback("pre_scoring", {"status": "starting", "stage": 2, "message": f"Pre-scoring {len(opportunities)} opportunities"})
        
        try:
            # Filter by minimum compatibility score
            qualified_opportunities = [
                opp for opp in opportunities 
                if opp.compatibility_score >= config.min_compatibility_score
            ]
            
            # Sort by compatibility score (descending)
            qualified_opportunities.sort(key=lambda x: x.compatibility_score, reverse=True)
            
            # Apply resource limits based on priority
            limit = self._calculate_pre_scoring_limit(config, len(qualified_opportunities))
            filtered_opportunities = qualified_opportunities[:limit]
            
            # Quick enhancement of top candidates
            for opp in filtered_opportunities:
                opp.external_data["pre_scoring_rank"] = qualified_opportunities.index(opp) + 1
                opp.external_data["pre_scoring_percentile"] = (len(qualified_opportunities) - qualified_opportunities.index(opp)) / len(qualified_opportunities) * 100
            
            pipeline_state["current_opportunities"] = filtered_opportunities
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if progress_callback:
                progress_callback("pre_scoring", {
                    "status": "completed",
                    "stage": 2,
                    "opportunities_filtered": len(filtered_opportunities),
                    "processing_time": processing_time
                })
            
            return StageResult(
                stage=PipelineStage.PRE_SCORING,
                opportunities_in=len(opportunities),
                opportunities_out=len(filtered_opportunities),
                processing_time_seconds=processing_time,
                success=True,
                metadata={
                    "min_compatibility_applied": config.min_compatibility_score,
                    "resource_limit_applied": limit,
                    "avg_score_after_filtering": sum(opp.compatibility_score for opp in filtered_opportunities) / len(filtered_opportunities) if filtered_opportunities else 0
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return StageResult(
                stage=PipelineStage.PRE_SCORING,
                opportunities_in=len(opportunities),
                opportunities_out=0,
                processing_time_seconds=processing_time,
                success=False,
                error=str(e)
            )
    
    async def _execute_deep_analysis_stage(
        self,
        pipeline_state: Dict[str, Any],
        progress_callback: Optional[Callable]
    ) -> StageResult:
        """Stage 3: Deep Analysis - Comprehensive research on top candidates"""
        
        start_time = datetime.now()
        config = pipeline_state["config"]
        opportunities = pipeline_state["current_opportunities"]
        
        if progress_callback:
            progress_callback("deep_analysis", {"status": "starting", "stage": 3, "message": f"Deep analysis of {len(opportunities)} top candidates"})
        
        try:
            # Select top candidates for deep analysis
            deep_analysis_limit = min(config.deep_analysis_limit, len(opportunities))
            top_candidates = opportunities[:deep_analysis_limit]
            
            # Perform deep analysis (parallel processing with concurrency limit)
            semaphore = asyncio.Semaphore(config.max_concurrent_operations)
            analysis_tasks = [
                self._analyze_single_opportunity(semaphore, opp, pipeline_state["profile"])
                for opp in top_candidates
            ]
            
            analyzed_opportunities = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Filter out failed analyses
            successful_analyses = [
                opp for opp in analyzed_opportunities 
                if not isinstance(opp, Exception)
            ]
            
            # Re-score based on deep analysis
            for opp in successful_analyses:
                opp.external_data["deep_analysis_completed"] = True
                opp.external_data["analysis_depth_score"] = self._calculate_analysis_depth_score(opp)
            
            # Sort by enhanced compatibility score
            successful_analyses.sort(key=lambda x: x.compatibility_score, reverse=True)
            
            pipeline_state["current_opportunities"] = successful_analyses
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if progress_callback:
                progress_callback("deep_analysis", {
                    "status": "completed",
                    "stage": 3, 
                    "opportunities_analyzed": len(successful_analyses),
                    "analysis_failures": len(analysis_tasks) - len(successful_analyses),
                    "processing_time": processing_time
                })
            
            return StageResult(
                stage=PipelineStage.DEEP_ANALYSIS,
                opportunities_in=len(opportunities),
                opportunities_out=len(successful_analyses),
                processing_time_seconds=processing_time,
                success=True,
                metadata={
                    "deep_analysis_limit": deep_analysis_limit,
                    "concurrent_operations": config.max_concurrent_operations,
                    "analysis_success_rate": len(successful_analyses) / len(analysis_tasks) if analysis_tasks else 0,
                    "avg_analysis_depth_score": sum(opp.external_data.get("analysis_depth_score", 0) for opp in successful_analyses) / len(successful_analyses) if successful_analyses else 0
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return StageResult(
                stage=PipelineStage.DEEP_ANALYSIS,
                opportunities_in=len(opportunities),
                opportunities_out=0,
                processing_time_seconds=processing_time,
                success=False,
                error=str(e)
            )
    
    async def _execute_recommendations_stage(
        self,
        pipeline_state: Dict[str, Any], 
        progress_callback: Optional[Callable]
    ) -> StageResult:
        """Stage 4: Recommendations - Final strategic recommendations"""
        
        start_time = datetime.now()
        config = pipeline_state["config"]
        opportunities = pipeline_state["current_opportunities"]
        
        if progress_callback:
            progress_callback("recommendations", {"status": "starting", "stage": 4, "message": f"Generating final recommendations from {len(opportunities)} analyzed opportunities"})
        
        try:
            # Generate strategic recommendations
            final_recommendations = await self._generate_strategic_recommendations(
                opportunities, pipeline_state["profile"], config
            )
            
            # Limit to final recommendation count
            final_recommendations = final_recommendations[:config.final_recommendations]
            
            # Add recommendation metadata
            for i, opp in enumerate(final_recommendations):
                opp.external_data["final_rank"] = i + 1
                opp.external_data["recommendation_tier"] = self._get_recommendation_tier(i)
                opp.external_data["strategic_value"] = self._calculate_strategic_value(opp, pipeline_state["profile"])
            
            pipeline_state["final_recommendations"] = final_recommendations
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if progress_callback:
                progress_callback("recommendations", {
                    "status": "completed",
                    "stage": 4,
                    "final_recommendations": len(final_recommendations),
                    "processing_time": processing_time
                })
            
            return StageResult(
                stage=PipelineStage.RECOMMENDATIONS,
                opportunities_in=len(opportunities),
                opportunities_out=len(final_recommendations),
                processing_time_seconds=processing_time,
                success=True,
                metadata={
                    "recommendation_algorithm": "strategic_value_ranking",
                    "final_recommendation_count": len(final_recommendations),
                    "avg_strategic_value": sum(opp.external_data.get("strategic_value", 0) for opp in final_recommendations) / len(final_recommendations) if final_recommendations else 0
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return StageResult(
                stage=PipelineStage.RECOMMENDATIONS,
                opportunities_in=len(opportunities),
                opportunities_out=0,
                processing_time_seconds=processing_time,
                success=False,
                error=str(e)
            )
    
    async def _analyze_single_opportunity(
        self,
        semaphore: asyncio.Semaphore,
        opportunity: DiscoveryResult,
        profile: OrganizationProfile
    ) -> DiscoveryResult:
        """Perform deep analysis on single opportunity"""
        
        async with semaphore:
            # Enhanced compatibility analysis
            opportunity.external_data["network_analysis"] = await self._analyze_network_connections(opportunity, profile)
            opportunity.external_data["financial_analysis"] = self._analyze_financial_capacity(opportunity)
            opportunity.external_data["strategic_fit"] = self._analyze_strategic_fit(opportunity, profile)
            opportunity.external_data["application_complexity"] = self._assess_application_complexity(opportunity)
            
            # Update compatibility score based on deep analysis
            enhanced_score = self._calculate_enhanced_compatibility(opportunity, profile)
            opportunity.compatibility_score = max(opportunity.compatibility_score, enhanced_score)
            
            return opportunity
    
    def _calculate_pre_scoring_limit(self, config: PipelineConfig, available_count: int) -> int:
        """Calculate pre-scoring limit based on priority and resources"""
        base_limit = config.pre_scoring_limit
        
        priority_multipliers = {
            ProcessingPriority.LOW: 0.5,
            ProcessingPriority.STANDARD: 1.0,
            ProcessingPriority.HIGH: 1.5,
            ProcessingPriority.URGENT: 2.0
        }
        
        adjusted_limit = int(base_limit * priority_multipliers[config.priority])
        return min(adjusted_limit, available_count)
    
    def _finalize_pipeline(self, pipeline_state: Dict[str, Any], status: str, error: Optional[str] = None) -> Dict[str, Any]:
        """Finalize pipeline execution and return results"""
        
        pipeline_state["status"] = status
        pipeline_state["completed_at"] = datetime.now()
        pipeline_state["total_processing_time"] = (
            pipeline_state["completed_at"] - pipeline_state["started_at"]
        ).total_seconds()
        
        if error:
            pipeline_state["error"] = error
        
        return {
            "pipeline_id": pipeline_state["pipeline_id"],
            "profile_id": pipeline_state["config"].profile_id,
            "status": status,
            "stage_results": pipeline_state["stage_results"],
            "final_recommendations": pipeline_state.get("final_recommendations", []),
            "total_processing_time": pipeline_state["total_processing_time"],
            "pipeline_metrics": self._calculate_pipeline_metrics(pipeline_state),
            "error": error
        }
    
    def _calculate_pipeline_metrics(self, pipeline_state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive pipeline performance metrics"""
        
        stage_results = pipeline_state["stage_results"]
        
        return {
            "total_opportunities_discovered": stage_results[0].opportunities_out if stage_results else 0,
            "final_recommendations_count": len(pipeline_state.get("final_recommendations", [])),
            "processing_efficiency": len(pipeline_state.get("final_recommendations", [])) / stage_results[0].opportunities_out if stage_results and stage_results[0].opportunities_out > 0 else 0,
            "stage_processing_times": {result.stage.value: result.processing_time_seconds for result in stage_results},
            "total_processing_time": pipeline_state.get("total_processing_time", 0),
            "success_rate": sum(1 for result in stage_results if result.success) / len(stage_results) if stage_results else 0
        }


# Helper methods (simplified for space)
    def _calculate_analysis_depth_score(self, opp: DiscoveryResult) -> float:
        return 0.8  # Placeholder
    
    async def _analyze_network_connections(self, opp: DiscoveryResult, profile: OrganizationProfile) -> Dict[str, Any]:
        return {"connections_found": 0}  # Placeholder
    
    def _analyze_financial_capacity(self, opp: DiscoveryResult) -> Dict[str, Any]:
        return {"capacity_rating": "medium"}  # Placeholder
    
    def _analyze_strategic_fit(self, opp: DiscoveryResult, profile: OrganizationProfile) -> Dict[str, Any]:
        return {"fit_score": 0.7}  # Placeholder
    
    def _assess_application_complexity(self, opp: DiscoveryResult) -> str:
        return "medium"  # Placeholder
    
    def _calculate_enhanced_compatibility(self, opp: DiscoveryResult, profile: OrganizationProfile) -> float:
        return min(opp.compatibility_score * 1.1, 1.0)  # Placeholder
    
    async def _generate_strategic_recommendations(self, opps: List[DiscoveryResult], profile: OrganizationProfile, config: PipelineConfig) -> List[DiscoveryResult]:
        # Sort by strategic value
        return sorted(opps, key=lambda x: x.compatibility_score, reverse=True)
    
    def _get_recommendation_tier(self, rank: int) -> str:
        if rank < 5: return "tier_1_priority"
        elif rank < 10: return "tier_2_strong" 
        else: return "tier_3_consider"
    
    def _calculate_strategic_value(self, opp: DiscoveryResult, profile: OrganizationProfile) -> float:
        return opp.compatibility_score * 0.9  # Placeholder


# Global pipeline engine instance
pipeline_engine = ProcessingPipeline()