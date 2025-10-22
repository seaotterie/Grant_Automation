"""
Multi-Dimensional Scorer Tool
12-Factor compliant tool for sophisticated dimensional scoring.

Purpose: Unified scoring across all workflow stages
Cost: $0.00 per score (no AI calls - algorithmic)
Replaces: discovery_scorer.py, success_scorer.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Optional, Dict, Any, List
import time
from datetime import datetime

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext

try:
    from .scorer_models import (
        ScoringInput,
        MultiDimensionalScore,
        DimensionalScore,
        ScoringMetadata,
        WorkflowStage,
        TrackType,
        EnhancedData,
        STAGE_WEIGHTS,
        FOUNDATION_WEIGHTS,
        DEFAULT_BOOST_FACTORS,
        DIMENSION_BOOST_MAP,
        MULTI_DIMENSIONAL_SCORER_COST
    )
    from .stage_scorers import (
        DiscoverStageScorer,
        PlanStageScorer,
        AnalyzeStageScorer,
        ExamineStageScorer,
        ApproachStageScorer
    )
    from .foundation_scorer import FoundationStageScorer
except ImportError:
    from scorer_models import (
        ScoringInput,
        MultiDimensionalScore,
        DimensionalScore,
        ScoringMetadata,
        WorkflowStage,
        TrackType,
        EnhancedData,
        STAGE_WEIGHTS,
        FOUNDATION_WEIGHTS,
        DEFAULT_BOOST_FACTORS,
        DIMENSION_BOOST_MAP,
        MULTI_DIMENSIONAL_SCORER_COST
    )
    from stage_scorers import (
        DiscoverStageScorer,
        PlanStageScorer,
        AnalyzeStageScorer,
        ExamineStageScorer,
        ApproachStageScorer
    )
    from foundation_scorer import FoundationStageScorer


class MultiDimensionalScorerTool(BaseTool[MultiDimensionalScore]):
    """
    12-Factor Multi-Dimensional Scorer Tool

    Factor 4: Returns structured MultiDimensionalScore
    Factor 6: Stateless - pure function scoring
    Factor 10: Single responsibility - scoring only
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize multi-dimensional scorer tool."""
        super().__init__(config)

        # Load custom configurations
        self.stage_weights = config.get("stage_weights", STAGE_WEIGHTS) if config else STAGE_WEIGHTS
        self.boost_factors = config.get("boost_factors", DEFAULT_BOOST_FACTORS) if config else DEFAULT_BOOST_FACTORS
        self.foundation_weights = config.get("foundation_weights", FOUNDATION_WEIGHTS) if config else FOUNDATION_WEIGHTS

        # Initialize stage scorers
        self.stage_scorers = {
            WorkflowStage.DISCOVER: DiscoverStageScorer(),
            WorkflowStage.PLAN: PlanStageScorer(),
            WorkflowStage.ANALYZE: AnalyzeStageScorer(),
            WorkflowStage.EXAMINE: ExamineStageScorer(),
            WorkflowStage.APPROACH: ApproachStageScorer()
        }

        # Initialize foundation scorer (track-based, not stage-based)
        self.foundation_scorer = FoundationStageScorer()

    def get_tool_name(self) -> str:
        return "Multi-Dimensional Scorer Tool"

    def get_tool_version(self) -> str:
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        return "Multi-dimensional opportunity scoring with confidence calculation"

    async def _execute(
        self,
        context: ToolExecutionContext,
        scoring_input: ScoringInput
    ) -> MultiDimensionalScore:
        """Execute multi-dimensional scoring."""
        start_time = time.time()

        self.logger.info(
            f"Starting multi-dimensional scoring: stage={scoring_input.workflow_stage.value}, "
            f"track={scoring_input.track_type.value if scoring_input.track_type else 'none'}"
        )

        # Check if using foundation track (track-based scoring)
        if scoring_input.track_type == TrackType.FOUNDATION:
            self.logger.info("Using foundation-specific scorer (990-PF composite scoring)")
            weights = self.foundation_weights
            dimensional_scores = self.foundation_scorer.calculate_dimensions(
                scoring_input.opportunity_data,
                scoring_input.organization_profile,
                weights,
                scoring_input.track_type
            )
        else:
            # Get stage-specific weights
            weights = self._get_weights(scoring_input)

            # Get stage-specific scorer
            stage_scorer = self.stage_scorers.get(scoring_input.workflow_stage)
            if not stage_scorer:
                raise ValueError(f"No scorer for stage: {scoring_input.workflow_stage}")

            # Calculate dimensional scores
            dimensional_scores = stage_scorer.calculate_dimensions(
                scoring_input.opportunity_data,
                scoring_input.organization_profile,
                weights,
                scoring_input.track_type
            )

        # Apply boost factors
        boost_factors_applied = []
        if scoring_input.enhanced_data:
            dimensional_scores, boost_factors_applied = self._apply_boost_factors(
                dimensional_scores,
                scoring_input.enhanced_data
            )

        # Calculate overall score (weighted sum)
        overall_score = sum(ds.weighted_score * (1.0 + ds.boost_factor - 1.0) for ds in dimensional_scores)

        # Calculate confidence
        confidence = self._calculate_confidence(dimensional_scores, scoring_input.enhanced_data)

        # Generate recommendations
        proceed_recommendation, key_strengths, key_concerns, recommended_actions = self._generate_recommendations(
            overall_score,
            dimensional_scores,
            scoring_input.workflow_stage
        )

        # Create metadata
        calculation_time = (time.time() - start_time) * 1000  # ms
        metadata = ScoringMetadata(
            scoring_timestamp=datetime.now().isoformat(),
            stage=scoring_input.workflow_stage.value,
            track_type=scoring_input.track_type.value if scoring_input.track_type else None,
            dimensions_count=len(dimensional_scores),
            boost_factors_count=len(boost_factors_applied),
            data_quality_average=sum(ds.data_quality for ds in dimensional_scores) / len(dimensional_scores),
            calculation_time_ms=calculation_time,
            weights_used=weights,
            boost_config_used=self.boost_factors
        )

        # Create output
        output = MultiDimensionalScore(
            overall_score=min(1.0, max(0.0, overall_score)),  # Clamp to 0-1
            confidence=confidence,
            dimensional_scores=dimensional_scores,
            stage=scoring_input.workflow_stage.value,
            track_type=scoring_input.track_type.value if scoring_input.track_type else None,
            boost_factors_applied=boost_factors_applied,
            metadata=metadata,
            proceed_recommendation=proceed_recommendation,
            key_strengths=key_strengths,
            key_concerns=key_concerns,
            recommended_actions=recommended_actions
        )

        self.logger.info(
            f"Completed scoring: overall={overall_score:.3f}, "
            f"confidence={confidence:.3f}, time={calculation_time:.2f}ms"
        )

        return output

    def _get_weights(self, scoring_input: ScoringInput) -> Dict[str, float]:
        """Get dimensional weights for the stage."""
        # Custom weights override
        if scoring_input.custom_weights:
            return scoring_input.custom_weights

        # Default stage weights
        return self.stage_weights.get(scoring_input.workflow_stage, {})

    def _apply_boost_factors(
        self,
        dimensional_scores: List[DimensionalScore],
        enhanced_data: EnhancedData
    ) -> tuple[List[DimensionalScore], List[str]]:
        """Apply boost factors based on available enhanced data."""
        boost_factors_applied = []

        for dim_score in dimensional_scores:
            # Check which boost factors apply to this dimension
            applicable_boosts = DIMENSION_BOOST_MAP.get(dim_score.dimension_name, [])

            total_boost = 1.0
            for boost_name in applicable_boosts:
                # Check if the enhanced data is available
                has_data = False
                if boost_name == "financial_data" and enhanced_data.financial_data:
                    has_data = True
                elif boost_name == "network_data" and enhanced_data.network_data:
                    has_data = True
                elif boost_name == "historical_data" and enhanced_data.historical_data:
                    has_data = True
                elif boost_name == "risk_assessment" and enhanced_data.risk_assessment:
                    has_data = True

                if has_data:
                    boost_amount = self.boost_factors.get(boost_name, 0.0)
                    total_boost += boost_amount
                    if boost_name not in boost_factors_applied:
                        boost_factors_applied.append(boost_name)

            dim_score.boost_factor = total_boost

        return dimensional_scores, boost_factors_applied

    def _calculate_confidence(
        self,
        dimensional_scores: List[DimensionalScore],
        enhanced_data: Optional[EnhancedData]
    ) -> float:
        """Calculate confidence in the overall score."""
        # Base confidence from data quality
        data_quality_avg = sum(ds.data_quality for ds in dimensional_scores) / len(dimensional_scores)

        # Boost confidence if enhanced data is available
        confidence = data_quality_avg
        if enhanced_data:
            enhancement_count = sum([
                enhanced_data.financial_data,
                enhanced_data.network_data,
                enhanced_data.historical_data,
                enhanced_data.risk_assessment
            ])
            # Each enhancement adds 5% confidence, max 20%
            confidence = min(1.0, confidence + (enhancement_count * 0.05))

        return confidence

    def _generate_recommendations(
        self,
        overall_score: float,
        dimensional_scores: List[DimensionalScore],
        stage: WorkflowStage
    ) -> tuple[bool, List[str], List[str], List[str]]:
        """Generate proceed recommendation and insights."""

        # Proceed recommendation based on stage-specific thresholds
        proceed_thresholds = {
            WorkflowStage.DISCOVER: 0.55,
            WorkflowStage.PLAN: 0.60,
            WorkflowStage.ANALYZE: 0.65,
            WorkflowStage.EXAMINE: 0.70,
            WorkflowStage.APPROACH: 0.75
        }
        proceed = overall_score >= proceed_thresholds.get(stage, 0.65)

        # Identify strengths (top 2 dimensions)
        sorted_dims = sorted(dimensional_scores, key=lambda x: x.weighted_score * x.boost_factor, reverse=True)
        key_strengths = [
            f"{dim.dimension_name.replace('_', ' ').title()}: {dim.raw_score:.0%}"
            for dim in sorted_dims[:2]
        ]

        # Identify concerns (bottom 2 dimensions if below 0.5)
        key_concerns = [
            f"{dim.dimension_name.replace('_', ' ').title()}: {dim.raw_score:.0%}"
            for dim in sorted_dims[-2:] if dim.raw_score < 0.5
        ]

        # Generate recommended actions
        recommended_actions = []
        if proceed:
            recommended_actions.append(f"Proceed to next stage - strong overall score ({overall_score:.0%})")
            if key_concerns:
                recommended_actions.append(f"Address identified concerns: {', '.join([c.split(':')[0] for c in key_concerns])}")
        else:
            recommended_actions.append(f"Review carefully - score below threshold ({overall_score:.0%})")
            recommended_actions.append("Consider additional research or skip this opportunity")

        return proceed, key_strengths, key_concerns, recommended_actions

    def get_cost_estimate(self) -> Optional[float]:
        return MULTI_DIMENSIONAL_SCORER_COST

    def validate_inputs(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate tool inputs."""
        scoring_input = kwargs.get("scoring_input")

        if not scoring_input:
            return False, "scoring_input is required"

        if not isinstance(scoring_input, ScoringInput):
            return False, "scoring_input must be ScoringInput instance"

        if not scoring_input.opportunity_data:
            return False, "opportunity_data is required"

        if not scoring_input.organization_profile:
            return False, "organization_profile is required"

        if not scoring_input.workflow_stage:
            return False, "workflow_stage is required"

        return True, None


# Convenience function
async def score_opportunity(
    opportunity_data: Dict[str, Any],
    organization_profile: Dict[str, Any],
    workflow_stage: str,
    track_type: Optional[str] = None,
    enhanced_data: Optional[Dict[str, bool]] = None,
    config: Optional[dict] = None
) -> ToolResult[MultiDimensionalScore]:
    """Score an opportunity using multi-dimensional analysis."""

    tool = MultiDimensionalScorerTool(config)

    # Convert stage string to enum
    stage_enum = WorkflowStage(workflow_stage)
    track_enum = TrackType(track_type) if track_type else None

    # Convert enhanced data dict to EnhancedData
    enhanced = None
    if enhanced_data:
        enhanced = EnhancedData(**enhanced_data)

    scoring_input = ScoringInput(
        opportunity_data=opportunity_data,
        organization_profile=organization_profile,
        workflow_stage=stage_enum,
        track_type=track_enum,
        enhanced_data=enhanced
    )

    return await tool.execute(scoring_input=scoring_input)
