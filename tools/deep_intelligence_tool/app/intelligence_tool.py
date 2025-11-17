"""
Deep Intelligence Tool
12-Factor compliant tool for comprehensive grant opportunity analysis.

Purpose: Deep analysis of ~10 selected opportunities with configurable depth
Cost: $0.75-$42.00 per opportunity depending on depth
Replaces: 6 processors (ai_heavy_deep, ai_heavy_researcher, 4 tier processors)
"""

from src.core.tool_framework.path_helper import setup_tool_paths

# Setup paths for imports
project_root = setup_tool_paths(__file__)

from typing import Optional
import logging

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext
from .intelligence_models import (
    DeepIntelligenceInput,
    DeepIntelligenceOutput,
    AnalysisDepth,
    DEPTH_FEATURES
)
from .depth_handlers import (
    QuickDepthHandler,
    StandardDepthHandler,
    EnhancedDepthHandler,
    CompleteDepthHandler
)


class DeepIntelligenceTool(BaseTool[DeepIntelligenceOutput]):
    """
    12-Factor Deep Intelligence Tool

    Factor 4: Returns structured DeepIntelligenceOutput
    Factor 6: Stateless - no persistence between runs
    Factor 10: Single responsibility - deep intelligence analysis only
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize intelligence tool.

        Args:
            config: Optional configuration
                - openai_api_key: OpenAI API key
                - default_depth: "quick", "standard", "enhanced", or "complete"
        """
        super().__init__(config)

        # Configuration
        self.openai_api_key = config.get("openai_api_key") if config else None
        self.default_depth = config.get("default_depth", "quick")

        # Initialize depth handlers
        self.handlers = {
            AnalysisDepth.QUICK: QuickDepthHandler(self.logger),
            AnalysisDepth.STANDARD: StandardDepthHandler(self.logger),
            AnalysisDepth.ENHANCED: EnhancedDepthHandler(self.logger),
            AnalysisDepth.COMPLETE: CompleteDepthHandler(self.logger)
        }

    def get_tool_name(self) -> str:
        """Tool name."""
        return "Deep Intelligence Tool"

    def get_tool_version(self) -> str:
        """Tool version."""
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        """Tool's single responsibility."""
        return "Comprehensive deep intelligence analysis of selected grant opportunities with configurable depth"

    async def _execute(
        self,
        context: ToolExecutionContext,
        intelligence_input: DeepIntelligenceInput
    ) -> DeepIntelligenceOutput:
        """
        Execute deep intelligence analysis.

        Args:
            context: Execution context
            intelligence_input: Intelligence analysis input

        Returns:
            DeepIntelligenceOutput with comprehensive analysis
        """
        self.logger.info(
            f"Starting deep intelligence analysis: {intelligence_input.opportunity_id} "
            f"at {intelligence_input.depth.value} depth"
        )

        # Get appropriate handler
        handler = self.handlers[intelligence_input.depth]

        # Execute analysis
        output = await handler.analyze(intelligence_input)

        self.logger.info(
            f"Completed {intelligence_input.depth.value} depth analysis: "
            f"score={output.overall_score:.2f}, proceed={output.proceed_recommendation}"
        )

        return output

    def get_cost_estimate(
        self,
        depth: str = "quick"
    ) -> Optional[float]:
        """
        Estimate execution cost.

        Args:
            depth: Analysis depth ("quick", "standard", "enhanced", "complete")

        Returns:
            Estimated cost in USD
        """
        depth_enum = AnalysisDepth(depth)
        return DEPTH_FEATURES[depth_enum]["cost"]

    def validate_inputs(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate tool inputs.

        Args:
            **kwargs: Tool inputs

        Returns:
            Tuple of (is_valid, error_message)
        """
        intelligence_input = kwargs.get("intelligence_input")

        if not intelligence_input:
            return False, "intelligence_input is required"

        if not isinstance(intelligence_input, DeepIntelligenceInput):
            return False, "intelligence_input must be DeepIntelligenceInput instance"

        if not intelligence_input.opportunity_id:
            return False, "opportunity_id is required"

        if not intelligence_input.organization_ein:
            return False, "organization_ein is required"

        return True, None

    def get_depth_features(self, depth: AnalysisDepth) -> dict:
        """
        Get features for a specific depth level.

        Args:
            depth: Analysis depth

        Returns:
            Dictionary of depth features
        """
        return DEPTH_FEATURES[depth]


# Convenience function for direct usage
async def analyze_opportunity(
    opportunity_id: str,
    opportunity_title: str,
    opportunity_description: str,
    funder_name: str,
    funder_type: str,
    organization_ein: str,
    organization_name: str,
    organization_mission: str,
    depth: str = "quick",
    screening_score: Optional[float] = None,
    user_notes: Optional[str] = None,
    focus_areas: Optional[list] = None,
    config: Optional[dict] = None
) -> ToolResult[DeepIntelligenceOutput]:
    """
    Analyze opportunity with the deep intelligence tool.

    Args:
        opportunity_id: Opportunity identifier
        opportunity_title: Opportunity title
        opportunity_description: Opportunity description
        funder_name: Funder name
        funder_type: Funder type (foundation, government, corporate)
        organization_ein: Organization EIN
        organization_name: Organization name
        organization_mission: Organization mission
        depth: Analysis depth ("quick", "standard", "enhanced", "complete")
        screening_score: Optional screening score from Stage 1
        user_notes: Optional user notes
        focus_areas: Optional focus areas
        config: Optional tool configuration

    Returns:
        ToolResult with DeepIntelligenceOutput
    """
    tool = DeepIntelligenceTool(config)

    intelligence_input = DeepIntelligenceInput(
        opportunity_id=opportunity_id,
        opportunity_title=opportunity_title,
        opportunity_description=opportunity_description,
        funder_name=funder_name,
        funder_type=funder_type,
        organization_ein=organization_ein,
        organization_name=organization_name,
        organization_mission=organization_mission,
        depth=AnalysisDepth(depth),
        screening_score=screening_score,
        user_notes=user_notes,
        focus_areas=focus_areas or []
    )

    return await tool.execute(intelligence_input=intelligence_input)


# Batch analysis function
async def analyze_opportunities_batch(
    opportunities: list[dict],
    organization_ein: str,
    organization_name: str,
    organization_mission: str,
    depth: str = "quick",
    config: Optional[dict] = None
) -> list[ToolResult[DeepIntelligenceOutput]]:
    """
    Analyze multiple opportunities in batch.

    Args:
        opportunities: List of opportunity dicts (id, title, description, funder, type)
        organization_ein: Organization EIN
        organization_name: Organization name
        organization_mission: Organization mission
        depth: Analysis depth
        config: Optional tool configuration

    Returns:
        List of ToolResults with DeepIntelligenceOutputs
    """
    import asyncio

    tool = DeepIntelligenceTool(config)

    # Create intelligence inputs
    inputs = []
    for opp in opportunities:
        intelligence_input = DeepIntelligenceInput(
            opportunity_id=opp["id"],
            opportunity_title=opp["title"],
            opportunity_description=opp["description"],
            funder_name=opp["funder"],
            funder_type=opp.get("funder_type", "foundation"),
            organization_ein=organization_ein,
            organization_name=organization_name,
            organization_mission=organization_mission,
            depth=AnalysisDepth(depth),
            screening_score=opp.get("screening_score")
        )
        inputs.append(intelligence_input)

    # Execute in parallel
    tasks = [tool.execute(intelligence_input=inp) for inp in inputs]
    results = await asyncio.gather(*tasks)

    return results
